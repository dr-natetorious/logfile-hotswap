"""
Exit command implementation.
"""
from .base import BaseCommand
from shell.exceptions import ShellExit


class ExitCommand(BaseCommand):
    """
    Exits the shell.
    """
    
    def get_command_names(self):
        return ['exit', 'quit', 'bye']
    
    def execute(self, command_name, args_str, shell):
        # Raise ShellExit exception to signal the shell to exit
        raise ShellExit()
    
    def get_help(self):
        return """
Exit the shell application.

Usage:
  exit  - Exit the shell
  quit  - Same as exit
  bye   - Same as exit
"""