"""
Core shell implementation for the server management tool.
"""
import sys
import traceback
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory

from .command_handler import CommandHandler
from .completer import ShellCompleter
from .exceptions import ShellExit
from .variable_manager import VariableManager
from targeting.config_store import ConfigStoreManager
from discovery.coordinator import DiscoveryCoordinator


class ServerShell:
    """Main shell class that handles the REPL loop."""
    
    def __init__(self, config=None):
        """Initialize the shell with configuration."""
        self.config = config or {}
        self.running = False
        self.command_handler = CommandHandler()
        
        # Initialize the variable manager
        self.variable_manager = VariableManager()
        
        # Initialize the config store manager and store
        self.config_store_manager = ConfigStoreManager(
            config_path=self.config.get('config_path')
        )
        self.config_store = self.config_store_manager.get_store()
        
        # Initialize the discovery coordinator
        self.discovery_coordinator = DiscoveryCoordinator(
            self.config_store,
            parallel=self.config.get('parallel_discovery', True),
            max_workers=self.config.get('discovery_workers', 5)
        )
        
        # Set up prompt session
        self.session = PromptSession(
            history=FileHistory(self.config.get('history_file', '.shell_history')),
            auto_suggest=AutoSuggestFromHistory(),
            completer=ShellCompleter(self.command_handler.get_commands())
        )
        
        # Current context (e.g., which server we're connected to)
        self.context = {
            'current_server': None,
        }

    def get_prompt_text(self):
        """Generate the prompt text based on current context."""
        if self.context.get('current_server'):
            return f"{self.context['current_server']}> "
        return "shell> "
    
    def run(self):
        """Run the main shell loop."""
        self.running = True
        
        # Print welcome message
        print("Welcome to Server Management Shell")
        print('Type "help" for available commands or "exit" to quit')
        
        while self.running:
            try:
                # Get input from user with custom prompt
                user_input = self.session.prompt(self.get_prompt_text())
                
                # Skip empty inputs
                if not user_input.strip():
                    continue
                
                # Process the command
                self.process_command(user_input)
                
            except KeyboardInterrupt:
                # Handle Ctrl+C - reset the input buffer
                continue
            except EOFError:
                # Handle Ctrl+D - exit the shell
                self.running = False
                print("\nExiting shell. Goodbye!")
                break
            except ShellExit:
                # Command requested shell exit
                self.running = False
                print("Exiting shell. Goodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")
                traceback.print_exc()
    
    def process_command(self, user_input):
        """Process a command string."""
        # Expand variables in the command input
        expanded_input = self.variable_manager.expand_variables(user_input)
        
        # Split the command and arguments
        cmd_parts = expanded_input.strip().split(maxsplit=1)
        cmd_name = cmd_parts[0].lower()
        cmd_args = cmd_parts[1] if len(cmd_parts) > 1 else ""
        
        self.command_handler.execute_command(cmd_name, cmd_args, self)

    def exit_shell(exitcode:int=0)->None:
        # Raise ShellExit exception to signal the shell to exit
        raise ShellExit(exitcode)