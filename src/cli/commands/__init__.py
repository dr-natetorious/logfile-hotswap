"""
Commands package initialization.
This module makes all command modules available and can register additional commands.
"""
# Import command classes for easy access
from .help_command import HelpCommand
from .exit_command import ExitCommand
from .server_commands import ServerCommand
from .disk_commands import DiskCommand
from .variable_commands import VariableCommand

# This function can be used to manually register commands
def register_commands():
    """
    Register commands manually.
    Useful for adding commands that are not automatically discovered.
    
    Returns:
        Dictionary of command_name -> command_instance
    """
    commands = {}
    
    # Register basic commands
    commands_to_register = [
        HelpCommand(),
        ExitCommand(),
        ServerCommand(),
        DiskCommand(),
        VariableCommand()
    ]
    
    for cmd in commands_to_register:
        for name in cmd.get_command_names():
            commands[name] = cmd
            
    return commands