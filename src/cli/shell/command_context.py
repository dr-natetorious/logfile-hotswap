"""
Command Context for passing context to commands during execution.

This module provides a context object that is passed to commands during execution,
containing references to the shell state and services needed by commands.
"""
from typing import Dict, List, Any, Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from cli.shell.shell import ServerShell
    from cli.shell.variable_manager import VariableManager
    from cli.shell.update_info_node import UpdateInfoNode


class CommandContext:
    """Context passed to commands during execution."""
    
    def __init__(
        self,
        shell: 'ServerShell',
        update_info: 'UpdateInfoNode',
        command_name: str,
        args_str: str
    ):
        """Initialize the command context.
        
        Args:
            shell: The shell instance
            update_info: The update info node for this command
            command_name: The name of the command being executed
            args_str: The arguments string
        """
        self.shell = shell
        self.update_info = update_info
        self.command_name = command_name
        self.args_str = args_str
        
        # Store some commonly used shell services as properties
        self._variable_manager = shell.variable_manager
        self._config_store = shell.config_store
        self._discovery_coordinator = shell.discovery_coordinator
    
    @property
    def variable_manager(self) -> 'VariableManager':
        """Get the variable manager.
        
        Returns:
            VariableManager: The variable manager
        """
        return self._variable_manager
    
    @property
    def config_store(self) -> Any:
        """Get the config store.
        
        Returns:
            Any: The config store
        """
        return self._config_store
    
    @property
    def discovery_coordinator(self) -> Any:
        """Get the discovery coordinator.
        
        Returns:
            Any: The discovery coordinator
        """
        return self._discovery_coordinator
    
    def log_debug(self, message: str) -> None:
        """Log a debug message.
        
        Args:
            message: The message to log
        """
        from cli.shell.update_info_node import LogLevel
        self.update_info.add_log(message, LogLevel.DEBUG)
    
    def log_info(self, message: str) -> None:
        """Log an info message.
        
        Args:
            message: The message to log
        """
        from cli.shell.update_info_node import LogLevel
        self.update_info.add_log(message, LogLevel.INFO)
    
    def log_warning(self, message: str) -> None:
        """Log a warning message.
        
        Args:
            message: The message to log
        """
        from cli.shell.update_info_node import LogLevel
        self.update_info.add_log(message, LogLevel.WARNING)
    
    def log_error(self, message: str) -> None:
        """Log an error message.
        
        Args:
            message: The message to log
        """
        from cli.shell.update_info_node import LogLevel
        self.update_info.add_log(message, LogLevel.ERROR)
    
    def add_output(self, key: str, value: Any) -> None:
        """Add output to the update info node.
        
        Args:
            key: Output identifier
            value: Output value
        """
        self.update_info.add_output(key, value)
    
    def set_error(self, error_type: str, message: str, traceback: Optional[str] = None) -> None:
        """Set error information.
        
        Args:
            error_type: Type of the error
            message: Error message
            traceback: Optional traceback
        """
        self.update_info.set_error(error_type, message, traceback)
    
    def create_child_context(self, command_name: str, args_str: str) -> 'CommandContext':
        """Create a child context for a subcommand.
        
        Args:
            command_name: The name of the subcommand
            args_str: The arguments string for the subcommand
            
        Returns:
            CommandContext: The newly created child context
        """
        child_node = self.update_info.create_child_node(f"{command_name} {args_str}")
        return CommandContext(self.shell, child_node, command_name, args_str)
