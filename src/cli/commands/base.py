"""
Base command class for all shell commands.
"""
import abc
import shlex

class BaseCommand(abc.ABC):
    """
    Abstract base class for all shell commands.
    """
    
    @abc.abstractmethod
    def get_command_names(self):
        """
        Return a list of command names that this class handles.
        A command might have multiple aliases.
        """
        pass
    
    @abc.abstractmethod
    def execute(self, command_name, args_str, shell):
        """
        Execute the command.
        
        Args:
            command_name: The name of the command being executed
            args_str: The arguments as a string
            shell: The shell instance
            
        Returns:
            True if the command executed successfully, False otherwise
        """
        pass
    
    def get_help(self):
        """
        Return help text for this command.
        """
        return "No help available for this command."
    
    def parse_args(self, args_str):
        """
        Parse command arguments string into a list of arguments.
        Handles quoted arguments properly.
        """
        if not args_str:
            return []
        return shlex.split(args_str)