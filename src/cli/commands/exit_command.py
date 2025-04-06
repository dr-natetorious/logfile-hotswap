"""
Exit command implementation with alias support.
"""
from typing import List, ClassVar
from .declarative import DeclarativeCommand, command, CommandRegistry
from shell.exceptions import ShellExit

@command(name="exit")
class ExitCommand(DeclarativeCommand):
    """
    Exit the shell application.
    """
    # Class variable to store aliases
    aliases: ClassVar[List[str]] = ["quit", "bye"]
    
    def __init__(self):
        super().__init__()
        # Register aliases during initialization
        self._register_aliases()
    
    def _register_aliases(self):
        """Register all aliases as commands that point to this class."""
        for alias in self.aliases:
            CommandRegistry._commands[alias] = self.__class__
    
    @classmethod
    def get_command_names(cls):
        """Return all command names including aliases."""
        return [cls._command_name] + cls.aliases
    
    def execute_command(self, shell) -> bool:
        # Raise ShellExit exception to signal the shell to exit
        raise ShellExit()