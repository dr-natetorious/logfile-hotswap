"""
Exit command implementation with alias support.
"""
from typing import List, ClassVar
from .declarative import DeclarativeCommand, Parameter, command, CommandRegistry

@command(name="exit")
class ExitCommand(DeclarativeCommand):
    """
    Exit the shell application.
    """
    # Class variable to store aliases
    _aliases: ClassVar[List[str]] = ["quit", "bye"]

    exitcode:int = Parameter(0,position=0,help="Process exit code")
    
    def execute_command(self, shell) -> bool:
        shell.exit_shell(self.exitcode)