"""
Command handler for the shell.
"""
from importlib import import_module
import pkgutil
import inspect

# Import the base command
from commands.base import BaseCommand


class CommandHandler:
    """
    Handles command registration, discovery, and execution.
    """
    
    def __init__(self):
        self.commands = {}
        self._load_commands()
    
    def _load_commands(self):
        """
        Dynamically load all command modules and register commands.
        """
        # Import the commands package
        import commands
        
        # Find all modules in the commands package
        for _, name, is_pkg in pkgutil.iter_modules(commands.__path__):
            if not is_pkg and name != 'base':  # Skip base.py and packages
                module = import_module(f'commands.{name}')
                
                # Find all classes in the module that inherit from BaseCommand
                for _, obj in inspect.getmembers(module, inspect.isclass):
                    if issubclass(obj, BaseCommand) and obj != BaseCommand:
                        cmd_instance = obj()
                        for cmd_name in cmd_instance.get_command_names():
                            self.commands[cmd_name] = cmd_instance
        
        # Also register commands from the __init__.py if it has a register_commands function
        if hasattr(commands, 'register_commands'):
            for name, cmd in commands.register_commands().items():
                self.commands[name] = cmd
    
    def register_command(self, command_instance):
        """
        Register a command instance.
        """
        for cmd_name in command_instance.get_command_names():
            self.commands[cmd_name] = command_instance
    
    def get_commands(self):
        """
        Get all registered commands.
        """
        return self.commands
    
    def execute(self, command_name, args, shell):
        """
        Execute a command by name.
        
        Args:
            command_name: The name of the command to execute
            args: The arguments string for the command
            shell: The shell instance
        """
        if command_name in self.commands:
            return self.commands[command_name].execute(command_name, args, shell)
        else:
            print(f"Unknown command: {command_name}")
            print('Type "help" for a list of available commands')
            return False