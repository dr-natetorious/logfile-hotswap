"""
Declarative command system.

This module provides a more maintainable way to create commands using Python type annotations
to define command parameters.
"""
import abc
import os
import inspect
import shlex
from typing import get_type_hints, ClassVar, Dict, List, Any, Optional, Type, Union
from pathlib import Path
from dataclasses import dataclass, field

from prompt_toolkit.completion import Completion, PathCompleter, WordCompleter

# Import BaseCommand for compatibility
from .base import BaseCommand


def command(name=None, description=None):
    """
    Decorator for command classes.
    """
    def decorator(cls):
        # Store the command name and description as class variables
        cls._command_name = name or cls.__name__.lower().replace('command', '')
        cls._command_description = description or cls.__doc__ or "No description available"
        
        # Register the command for discovery
        CommandRegistry.register_command(cls)
        
        return cls
    
    return decorator


class CommandRegistry:
    """
    Registry for all command classes.
    """
    _commands: Dict[str, Type['DeclarativeCommand']] = {}
    
    @classmethod
    def register_command(cls, command_class: Type['DeclarativeCommand']):
        """Register a command class."""
        name = command_class._command_name
        cls._commands[name] = command_class
    
    @classmethod
    def get_command(cls, name: str) -> Optional[Type['DeclarativeCommand']]:
        """Get a command class by name."""
        return cls._commands.get(name)
    
    @classmethod
    def get_all_commands(cls) -> Dict[str, Type['DeclarativeCommand']]:
        """Get all registered command classes."""
        return cls._commands


class ArgumentDefinition:
    """Represents a command argument with type information."""
    
    def __init__(self, name: str, type_hint: Type, required: bool = True, 
                 help_text: str = "", default=None):
        self.name = name
        self.type = type_hint
        self.required = required
        self.help_text = help_text
        self.default = default
        
        # Set appropriate completer based on type
        self.completer = None
        if self.type == Path or getattr(self.type, "__origin__", None) == Union and Path in getattr(self.type, "__args__", []):
            self.completer = PathCompleter()
        elif self.type == bool:
            self.completer = WordCompleter(['true', 'false', 'yes', 'no', '1', '0'])
    
    def convert_value(self, value_str: str) -> Any:
        """Convert string value to the correct type."""
        try:
            if self.type == Path:
                return Path(os.path.expanduser(value_str))
            elif self.type == bool:
                return value_str.lower() in ('yes', 'true', 't', 'y', '1')
            else:
                return self.type(value_str)
        except ValueError as e:
            raise ValueError(f"Cannot convert '{value_str}' to {self.type.__name__} for argument '{self.name}': {e}")
    
    def get_completions(self, text: str) -> List[Completion]:
        """Get completions for this argument."""
        if self.completer:
            return list(self.completer.get_completions(text, 0))
        return []


class DeclarativeCommand(BaseCommand):
    """
    Base class for declarative commands.
    
    Class attributes define the command parameters.
    Inherits from BaseCommand for compatibility with existing code.
    """
    # Class variables to store command metadata
    _command_name: ClassVar[str]
    _command_description: ClassVar[str]
    
    @classmethod
    def get_command_names(cls):
        """
        Return all command names handled by this class.
        For compatibility with original BaseCommand interface.
        """
        return [cls._command_name]
    
    @classmethod
    def get_argument_definitions(cls) -> List[ArgumentDefinition]:
        """
        Get the argument definitions from class annotations.
        """
        arg_defs = []
        type_hints = get_type_hints(cls)
        
        # Process all class attributes with type annotations
        for name, type_hint in type_hints.items():
            # Skip internal attributes
            if name.startswith('_'):
                continue
                
            # Check if this attribute has a default value
            default_value = getattr(cls, name, None)
            has_default = hasattr(cls, name)
            
            # Create argument definition
            arg_defs.append(ArgumentDefinition(
                name=name,
                type_hint=type_hint,
                required=not has_default,
                default=default_value if has_default else None,
                help_text=f"Default: {default_value}" if has_default else ""
            ))
        
        return arg_defs
    
    @classmethod
    def parse(cls, args_str: str) -> 'DeclarativeCommand':
        """
        Parse arguments and create a command instance.
        """
        instance = cls()
        
        # Get argument definitions
        arg_defs = cls.get_argument_definitions()
        
        # Parse arguments
        args = shlex.split(args_str) if args_str else []
        
        # Bind arguments to instance attributes
        for i, arg_def in enumerate(arg_defs):
            if i < len(args):
                # Convert and set value
                try:
                    value = arg_def.convert_value(args[i])
                    setattr(instance, arg_def.name, value)
                except ValueError as e:
                    raise ValueError(f"Error: {e}")
            elif arg_def.required:
                raise ValueError(f"Missing required argument: {arg_def.name}")
            else:
                # Set default value
                setattr(instance, arg_def.name, arg_def.default)
        
        return instance
    
    def execute(self, command_name, args_str, shell) -> bool:
        """
        Execute method compatible with BaseCommand interface.
        This delegates to the execute_command method.
        """
        try:
            # For single-command classes, we can just call execute_command
            # For multi-command classes, override this method to dispatch
            return self.execute_command(shell)
        except Exception as e:
            print(f"Error executing command: {e}")
            return False
    
    @abc.abstractmethod
    def execute_command(self, shell) -> bool:
        """
        Execute the command. Override this in derived classes.
        """
        raise NotImplementedError("Command must implement execute_command method")
    
    def get_help(self):
        """
        Get help text for this command.
        Override of BaseCommand.get_help().
        """
        help_text = self._command_description
        
        # Build usage string
        usage = f"Usage: {self._command_name}"
        
        arg_defs = self.__class__.get_argument_definitions()
        for arg_def in arg_defs:
            if arg_def.required:
                usage += f" <{arg_def.name}>"
            else:
                usage += f" [{arg_def.name}]"
        
        # Build arguments help
        args_help = ""
        if arg_defs:
            args_help = "\nArguments:\n"
            for arg_def in arg_defs:
                arg_help = f"  {arg_def.name}: {arg_def.type.__name__}"
                if not arg_def.required:
                    arg_help += f" (default: {arg_def.default})"
                if arg_def.help_text:
                    arg_help += f" - {arg_def.help_text}"
                args_help += arg_help + "\n"
        
        return f"{help_text}\n\n{usage}\n{args_help}"
    
    def get_completions(self, args_str):
        """
        Get completions for command arguments.
        Override of BaseCommand.get_completions().
        """
        # Parse arguments
        try:
            args = shlex.split(args_str)
        except ValueError:
            # Invalid string (like unclosed quotes)
            args = args_str.split()
        
        # Get argument definitions
        arg_defs = self.__class__.get_argument_definitions()
        
        # Determine which argument we're completing
        arg_index = len(args)
        if not args_str.endswith(" ") and args:
            arg_index -= 1
            current_arg = args[-1]
        else:
            current_arg = ""
        
        # Get completions for this argument
        if arg_index < len(arg_defs):
            arg_def = arg_defs[arg_index]
            completions = []
            
            if arg_def.completer:
                # If it has a dedicated completer, use it
                for completion in arg_def.completer.get_completions(current_arg, 0):
                    completions.append(completion)
            
            return completions
        
        return []