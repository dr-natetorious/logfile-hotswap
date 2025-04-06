"""
Command handler for the shell.
"""
from importlib import import_module
import pkgutil
import inspect

# Import the base command
from commands.base import BaseCommand

# Import declarative command support
try:
    from commands.declarative import DeclarativeCommand, CommandRegistry
    DECLARATIVE_AVAILABLE = True
except ImportError:
    DECLARATIVE_AVAILABLE = False


class CommandHandler:
    """
    Handles command registration, discovery, and execution.
    Supports both traditional BaseCommand classes and DeclarativeCommand classes.
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
            if not is_pkg and name not in ['base', 'declarative']:  # Skip base/infrastructure modules
                module = import_module(f'commands.{name}')
                
                # Find all classes in the module that inherit from BaseCommand
                for _, obj in inspect.getmembers(module, inspect.isclass):
                    if (issubclass(obj, BaseCommand) and 
                    obj != BaseCommand and 
                    not inspect.isabstract(obj)):
                        cmd_instance = obj()
                        for cmd_name in cmd_instance.get_command_names():
                            self.commands[cmd_name] = cmd_instance
        
        # Register declarative commands if available
        if DECLARATIVE_AVAILABLE:
            for name, cmd_class in CommandRegistry.get_all_commands().items():
                # Create an instance
                cmd_instance = cmd_class()
                self.commands[name] = cmd_instance
        
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
            cmd = self.commands[command_name]
            
            # Handle declarative commands differently
            if DECLARATIVE_AVAILABLE and isinstance(cmd, DeclarativeCommand):
                try:
                    # Create a properly-configured instance from the args
                    cmd_class = cmd.__class__
                    instance = cmd_class.parse(args)
                    
                    # Execute the instance
                    return instance.execute_command(shell)
                except ValueError as e:
                    # Show usage if we get a value error
                    print(f"Error: {e}")
                    print(f"\n{cmd.get_help()}")
                    return False
            else:
                # Execute traditional command
                return cmd.execute(command_name, args, shell)
        else:
            print(f"Unknown command: {command_name}")
            print('Type "help" for a list of available commands')
            return False