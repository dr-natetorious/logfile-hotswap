"""
Pipeline for executing commands with a structured execution context.

This module provides a pipeline for executing commands with proper context
and tracking execution state using UpdateInfoNode hierarchy.
"""
import traceback
from typing import List, Dict, Any, Optional, Tuple, Union, Callable, Type, TYPE_CHECKING
import shlex

from .update_info_node import UpdateInfoNode, LogLevel
from .command_context import CommandContext
from .exceptions import ShellExit

if TYPE_CHECKING:
    from .shell import ServerShell
    from cli.commands.base import BaseCommand


class Pipeline:
    """Pipeline for executing commands."""
    
    def __init__(self, shell: 'ServerShell'):
        """Initialize the pipeline.
        
        Args:
            shell: The shell instance
        """
        self.shell = shell
        self.root_node = UpdateInfoNode("root")
        self.current_node = self.root_node
        
        # Event handlers
        self._event_handlers = {}
    
    def parse_command(self, command_str: str) -> List[Tuple[str, str]]:
        """Parse a command string into command name and arguments pairs.
        
        Args:
            command_str: The command string to parse
            
        Returns:
            List[Tuple[str, str]]: List of (command_name, args_str) tuples
        """
        # Handle empty commands
        if not command_str or not command_str.strip():
            return []
        
        # Expand variables in the command
        expanded_input = self.shell.variable_manager.expand_variables(command_str)
        
        # Handle pipeline commands (not implemented yet, but prepared for)
        # For now, we just parse a single command
        commands = []
        
        # Split the command and arguments
        cmd_parts = expanded_input.strip().split(maxsplit=1)
        cmd_name = cmd_parts[0].lower()
        cmd_args = cmd_parts[1] if len(cmd_parts) > 1 else ""
        
        commands.append((cmd_name, cmd_args))
        return commands
    
    def get_command_instance(self, command_name: str) -> Optional['BaseCommand']:
        """Get a command instance by name.
        
        Args:
            command_name: The name of the command
            
        Returns:
            Optional[BaseCommand]: The command instance or None if not found
        """
        if command_name in self.shell.command_handler.get_commands():
            return self.shell.command_handler.get_commands()[command_name]
        return None
    
    def execute(self, command_str: str) -> UpdateInfoNode:
        """Execute a command string.
        
        Args:
            command_str: The command string to execute
            
        Returns:
            UpdateInfoNode: The root update info node for the execution
        """
        # Create a new root node for this execution
        self.root_node = UpdateInfoNode(command_str)
        self.current_node = self.root_node
        
        try:
            # Parse the command
            commands = self.parse_command(command_str)
            
            if not commands:
                self.root_node.add_log("Empty command, nothing to execute", LogLevel.INFO)
                self.root_node.complete(True)
                return self.root_node
            
            # Check for view switching command
            if self._handle_view_command(command_str):
                self.root_node.complete(True)
                return self.root_node
            
            # Execute each command in the pipeline
            for cmd_name, cmd_args in commands:
                # Get the command instance
                cmd_instance = self.get_command_instance(cmd_name)
                
                if cmd_instance is None:
                    self.root_node.add_log(f"Unknown command: {cmd_name}", LogLevel.ERROR)
                    self.root_node.add_log("Type 'help' for a list of available commands", LogLevel.INFO)
                    self.root_node.complete(False)
                    return self.root_node
                
                # Create a node for this command
                cmd_node = self.root_node.create_child_node(f"{cmd_name} {cmd_args}")
                self.current_node = cmd_node
                
                # Start the execution
                cmd_node.start()
                
                try:
                    # Create a context for the command
                    context = CommandContext(self.shell, cmd_node, cmd_name, cmd_args)
                    
                    # Execute the command
                    result = cmd_instance.execute(cmd_name, cmd_args, self.shell)
                    
                    # Mark the command as completed
                    cmd_node.complete(result)
                    
                except ShellExit as e:
                    # Command requested exit
                    cmd_node.add_log("Command requested shell exit", LogLevel.INFO)
                    cmd_node.complete(True)
                    # Re-raise to signal shell exit
                    raise
                except Exception as e:
                    # Command execution failed
                    error_msg = str(e)
                    error_tb = traceback.format_exc()
                    cmd_node.set_error(type(e).__name__, error_msg, error_tb)
                    print(f"Error executing command: {error_msg}")
                    print(error_tb)
                    return self.root_node
            
            # All commands completed successfully
            self.root_node.complete(True)
            
        except ShellExit:
            # Re-raise ShellExit
            raise
        except Exception as e:
            # Pipeline execution failed
            error_msg = str(e)
            error_tb = traceback.format_exc()
            self.root_node.set_error(type(e).__name__, error_msg, error_tb)
            print(f"Error in pipeline: {error_msg}")
            print(error_tb)
        
        return self.root_node
    
    def _handle_view_command(self, command_str: str) -> bool:
        """Handle view-specific commands.
        
        Args:
            command_str: The command string to process
            
        Returns:
            bool: True if a view command was handled, False otherwise
        """
        # Split the command and arguments
        cmd_parts = command_str.strip().split(maxsplit=1)
        cmd_name = cmd_parts[0].lower()
        
        # Handle view switching command
        if cmd_name == "view" and len(cmd_parts) > 1:
            view_name = cmd_parts[1].strip().lower()
            
            # Validate view name
            if view_name not in self.shell.view_manager.get_available_views():
                print(f"Error: Unknown view '{view_name}'")
                print(f"Available views: {', '.join(self.shell.view_manager.get_available_views())}")
                self.root_node.add_log(f"Unknown view: {view_name}", LogLevel.ERROR)
                return True
                
            # Switch to the specified view
            if view_name != self.shell.view_manager.current_view:
                if self.shell.view_manager.switch_to(view_name):
                    self.root_node.add_log(f"Switching to view: {view_name}", LogLevel.INFO)
                    self.trigger_event('view_switched', view_name)
                    return True
            return True
        
        # Not a view command
        return False
    
    def get_last_execution(self) -> UpdateInfoNode:
        """Get the root node of the last execution.
        
        Returns:
            UpdateInfoNode: The root node
        """
        return self.root_node
    
    def register_event_handler(self, event_name: str, handler: Callable) -> None:
        """Register an event handler.
        
        Args:
            event_name: Name of the event
            handler: Handler function
        """
        self._event_handlers[event_name] = handler
    
    def trigger_event(self, event_name: str, *args, **kwargs) -> None:
        """Trigger an event.
        
        Args:
            event_name: Name of the event
            args, kwargs: Arguments to pass to the handler
        """
        if event_name in self._event_handlers:
            self._event_handlers[event_name](*args, **kwargs)