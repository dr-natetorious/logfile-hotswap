"""
Enhanced declarative command system with PowerShell-inspired parameters.
"""
import abc
import os
import inspect
import shlex
import re
from typing import get_type_hints, ClassVar, Dict, List, Any, Optional, Type, Union, Set, Tuple
from pathlib import Path
from dataclasses import dataclass, field

from prompt_toolkit.completion import Completion, PathCompleter, WordCompleter

# Import BaseCommand for compatibility
from .base import BaseCommand
from utils.type_converter import TypeConverter

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


class Parameter:
    """
    Parameter metadata class to use in class variable annotations.
    
    Example:
        class MyCommand(DeclarativeCommand):
            name: str = Parameter(position=0, help="Name parameter")
            verbose: bool = Parameter(False, help="Verbose mode")
    """
    def __init__(self, default:Any=None, position:int=None, mandatory:bool=False, help:str=None, 
                 aliases:List[str]=None, validation=None):
        self.default = default
        self.position = position
        self.mandatory = mandatory
        self.help = help
        self.aliases = aliases or []
        self.validation = validation
    
    def __repr__(self):
        return f"Parameter(default={self.default!r}, position={self.position}, help={self.help!r})"


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


class ParameterDefinition:
    """Represents a command parameter with type information and metadata."""
    
    def __init__(
        self, 
        name: str, 
        type_hint: Type, 
        param_obj: Optional[Any] = None,
        variable_manager: Optional[Any] = None
    ):
        """
        Initialize a parameter definition.
        
        Args:
            name: The name of the parameter
            type_hint: The expected type of the parameter
            param_obj: Additional parameter metadata or default value
            variable_manager: Optional variable manager for expression evaluation
        """
        self.name = name
        self.type = type_hint
        self.variable_manager = variable_manager
        
        # Extract metadata from Parameter object if available
        if isinstance(param_obj, Parameter):
            self.default = param_obj.default
            self.position = param_obj.position
            self.help_text = param_obj.help or ""
            self.aliases = param_obj.aliases
            
            # Determine if mandatory based on provided metadata or default
            if param_obj.mandatory is not None:
                self.mandatory = param_obj.mandatory
            else:
                self.mandatory = self.default is None
        else:
            # Default values if no Parameter object
            self.default = param_obj
            self.position = None
            self.help_text = ""
            self.aliases = []
            self.mandatory = self.default is None
        
        # Parameter name with hyphen prefix (PowerShell style)
        self.param_name = f"-{name}"
        
        # Parameter aliases with hyphen prefix
        self.param_aliases = [f"-{alias}" for alias in self.aliases]
        
        # All parameter names (primary + aliases)
        self.all_param_names = [self.param_name] + self.param_aliases
        
        # Set appropriate completer based on type
        self.completer = None
        self._setup_completer()
    
    def _setup_completer(self):
        """Set up an appropriate completer based on the parameter type."""
        from prompt_toolkit.completion import PathCompleter, WordCompleter
        
        # Check for Path or Optional[Path]
        origin = getattr(self.type, "__origin__", None)
        args = getattr(self.type, "__args__", [])
        
        if (self.type == Path or 
            (origin is Union and Path in args)):
            self.completer = PathCompleter()
        elif self.type == bool:
            self.completer = WordCompleter([
                'true', 'false', 'yes', 'no', '1', '0'
            ])
    
    def convert_value(self, value_str: Optional[str]) -> Any:
        """
        Convert string value to the correct type.
        
        Args:
            value_str: The string value to convert
        
        Returns:
            The converted value
        
        Raises:
            ValueError: If conversion fails
        """
        # Handle empty or None values
        if value_str is None or value_str == '':
            # Return default if available
            if self.default is not None:
                return self.default
            
            # Raise error if mandatory
            if self.mandatory:
                raise ValueError(f"Parameter '{self.name}' is mandatory")
            
            return None
        
        # Special handling for boolean flags
        if self.type == bool and not value_str:
            return True
        
        # Prepare variable expansion and expression evaluation contexts
        variable_expander = (
            self.variable_manager.expand_variables 
            if self.variable_manager else None
        )
        expression_evaluator = (
            self.variable_manager.evaluate_expression 
            if self.variable_manager else None
        )
        
        try:
            # Use TypeConverter with optional variable expansion
            return TypeConverter.convert(
                value_str, 
                self.type,                 
            )
        except ValueError as e:
            raise ValueError(
                f"Cannot convert '{value_str}' to {self.type.__name__} "
                f"for parameter '{self.name}': {e}"
            )
    
    def get_completions(self, text: str) -> List[Any]:
        """Get completions for this parameter's value."""
        if self.completer:
            return list(self.completer.get_completions(text, 0))
        return []
    
    def get_param_completion(self, text: str) -> Optional[Any]:
        """Get completion for the parameter name."""
        from prompt_toolkit.completion import Completion
        
        # Check if the text matches the parameter name or any aliases
        matching_params = [p for p in self.all_param_names if p.startswith(text)]
        if matching_params:
            param_name = matching_params[0]  # Use the first matching parameter name
            
            # Construct metadata
            meta = f"{self.type.__name__}"
            if not self.mandatory:
                meta += f" (default: {self.default})"
            if self.help_text:
                meta += f" - {self.help_text}"
            
            return Completion(
                param_name,
                start_position=-len(text),
                display=param_name,
                display_meta=meta
            )
        return None


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
    def get_parameter_definitions(cls) -> List[ParameterDefinition]:
        """
        Get the parameter definitions from class annotations and Parameter objects.
        """
        param_defs = []
        type_hints = get_type_hints(cls)
        
        # Process all class attributes with type annotations
        positional_index = 0
        
        for name, type_hint in type_hints.items():
            # Skip internal attributes
            if name.startswith('_'):
                continue
                
            # Get the attribute value (Parameter object or default value)
            attr_value = getattr(cls, name, None)
            
            # Create parameter definition
            param_def = ParameterDefinition(
                name=name,
                type_hint=type_hint,
                param_obj=attr_value
            )
            
            # If position isn't explicitly set but parameter is mandatory,
            # assign a position in declaration order
            if param_def.position is None and param_def.mandatory:
                param_def.position = positional_index
                positional_index += 1
            
            param_defs.append(param_def)
        
        # Sort by position for consistent processing
        param_defs.sort(key=lambda param: param.position if param.position is not None else 999)
        
        return param_defs
    
    @classmethod
    def parse(cls, args_str: str) -> 'DeclarativeCommand':
        """
        Parse arguments and create a command instance.
        Supports both positional parameters and -parameter value syntax.
        """
        instance = cls()
        param_defs = cls.get_parameter_definitions()
        
        # Create maps for faster lookup
        param_map = {}
        for param in param_defs:
            for name in param.all_param_names:
                param_map[name] = param
        
        # Get positional parameters in order
        positional_params = sorted(
            [param for param in param_defs if param.position is not None],
            key=lambda param: param.position
        )
        
        # Parse arguments, handling quoted strings
        if not args_str:
            args = []
        else:
            try:
                args = shlex.split(args_str)
            except ValueError as e:
                # Handle unclosed quotes
                raise ValueError(f"Error parsing arguments: {e}")
        
        # Track which parameters have been provided
        provided_params = set()
        
        # First pass: handle named parameters (-name value)
        i = 0
        while i < len(args):
            arg = args[i]
            
            # Check if this is a parameter name
            if arg.startswith('-'):
                param_name = arg
                if param_name in param_map:
                    param_def = param_map[param_name]
                    name = param_def.name
                    provided_params.add(name)
                    
                    # Check if there's a value following
                    if i+1 < len(args) and not args[i+1].startswith('-'):
                        # This is a parameter with a value
                        value_str = args[i+1]
                        i += 2  # Skip both param name and value
                    else:
                        # This is a flag parameter without a value
                        value_str = ""
                        i += 1  # Skip only param name
                    
                    try:
                        value = param_def.convert_value(value_str)
                        setattr(instance, name, value)
                    except ValueError as e:
                        raise ValueError(f"Error: {e}")
                else:
                    raise ValueError(f"Unknown parameter: {param_name}")
            else:
                # This is a positional parameter or a value for a parameter
                i += 1
        
        # Second pass: handle remaining positional parameters
        positional_values = [arg for arg in args if not arg.startswith('-') and 
                           not (args.index(arg) > 0 and args[args.index(arg)-1].startswith('-') and 
                                args[args.index(arg)-1] in param_map)]
        
        for i, value_str in enumerate(positional_values):
            if i < len(positional_params):
                param_def = positional_params[i]
                name = param_def.name
                if name not in provided_params:  # Skip if already provided as named parameter
                    provided_params.add(name)
                    try:
                        value = param_def.convert_value(value_str)
                        setattr(instance, name, value)
                    except ValueError as e:
                        raise ValueError(f"Error: {e}")
            # Ignore extra positional parameters for now
        
        # Set default values for parameters that weren't provided
        for param_def in param_defs:
            if param_def.name not in provided_params:
                if param_def.mandatory:
                    raise ValueError(f"Missing required parameter: {param_def.name}")
                setattr(instance, param_def.name, param_def.default)
        
        return instance
    
    def execute(self, command_name, args_str, shell) -> bool:
        """
        Execute method compatible with BaseCommand interface.
        This delegates to the execute_command method.
        """
        try:
            # Parse arguments and create a properly initialized instance
            instance = self.__class__.parse(args_str)
            
            # Call execute_command on the initialized instance
            return instance.execute_command(shell)
        except ValueError as e:
            print(f"Error: {e}")
            return False
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
        
        # First add positional parameters
        param_defs = sorted(
            self.__class__.get_parameter_definitions(),
            key=lambda x: (x.position is None, x.position or 0)
        )
        
        # Add positional parameters first
        positional_params = [param for param in param_defs if param.position is not None]
        for param_def in positional_params:
            usage += f" <{param_def.name}>"
        
        # Then add optional parameters
        optional_params = [param for param in param_defs if param.position is None]
        if optional_params:
            usage += " [options]"
        
        # Build detailed parameter help
        param_help = ""
        if param_defs:
            # Positional parameters section
            if positional_params:
                param_help += "\nPositional Parameters:\n"
                for param_def in positional_params:
                    param_help += f"  {param_def.name}: {param_def.type.__name__}"
                    if param_def.help_text:
                        param_help += f" - {param_def.help_text}"
                    param_help += "\n"
            
            # Options section
            if optional_params:
                param_help += "\nParameters:\n"
                for param_def in optional_params:
                    param_names = [param_def.param_name] + param_def.param_aliases
                    param_help += f"  {', '.join(param_names)} <{param_def.type.__name__}>"
                    if not param_def.mandatory:
                        param_help += f" (default: {param_def.default})"
                    if param_def.help_text:
                        param_help += f" - {param_def.help_text}"
                    param_help += "\n"
        
        return f"{help_text}\n\n{usage}\n{param_help}"
    
    def get_completions(self, args_str):
        """
        Get completions for command parameters.
        Override of BaseCommand.get_completions().
        """
        completions = []
        
        # Get parameter definitions
        param_defs = self.__class__.get_parameter_definitions()
        
        # Separate positional and named parameters
        positional_params = sorted(
            [param for param in param_defs if param.position is not None],
            key=lambda param: param.position
        )
        named_params = [param for param in param_defs if param.position is None]
        
        # Parse current arguments
        try:
            args = shlex.split(args_str) if args_str else []
        except ValueError:
            # Handle unclosed quotes
            args = args_str.split()
        
        # Check if we're in the middle of typing a parameter name or value
        completing_param = False
        current_param = None
        current_text = ""
        
        if args and args_str and not args_str.endswith(' '):
            # We're completing the last argument
            current_text = args[-1]
            if current_text.startswith('-'):
                completing_param = True
            else:
                # We might be completing a value for a parameter
                if len(args) >= 2 and args[-2].startswith('-'):
                    param_name = args[-2]
                    # Find the parameter definition for this parameter name
                    for param_def in param_defs:
                        if param_name in param_def.all_param_names:
                            current_param = param_def
                            break
        
        # Get parameters that have been provided
        provided_params = set()
        positional_used = 0
        
        for i, arg in enumerate(args):
            if arg.startswith('-'):
                for param_def in param_defs:
                    if arg in param_def.all_param_names:
                        provided_params.add(param_def.name)
                        break
            elif i == 0 or not args[i-1].startswith('-') or args[i-1] not in [p for pd in param_defs for p in pd.all_param_names]:
                # Count positional parameters
                positional_used += 1
        
        if completing_param:
            # Complete parameter names
            for param_def in param_defs:
                completion = param_def.get_param_completion(current_text)
                if completion and param_def.name not in provided_params:
                    completions.append(completion)
        elif current_param:
            # Complete value for current parameter
            for completion in current_param.get_completions(current_text):
                completions.append(completion)
        else:
            # Suggest positional parameters or parameter names
            if positional_used < len(positional_params):
                # We're completing a positional parameter
                current_pos_param = positional_params[positional_used]
                for completion in current_pos_param.get_completions(current_text or ""):
                    completions.append(completion)
                
                # Also suggest a hint for the expected parameter
                if not current_text and (not args or args_str.endswith(" ")):
                    completions.append(Completion(
                        "",
                        start_position=0,
                        display=f"<{current_pos_param.name}>",
                        display_meta=f"{current_pos_param.type.__name__} (positional)"
                    ))
            
            # Also suggest parameter names
            if args_str.endswith(" ") or not args:
                for param_def in param_defs:
                    if param_def.name not in provided_params:
                        meta = f"{param_def.type.__name__}"
                        if not param_def.mandatory:
                            meta += f" (default: {param_def.default})"
                        
                        # Suggest primary parameter name
                        completions.append(Completion(
                            param_def.param_name,
                            start_position=0,
                            display=param_def.param_name,
                            display_meta=meta
                        ))
        
        return completions