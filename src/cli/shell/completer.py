"""
Custom command completer for the shell.
"""
import shlex
from prompt_toolkit.completion import Completer, Completion

# Import declarative command support
from commands.declarative import DeclarativeCommand


class ShellCompleter(Completer):
    """
    Custom completer for shell commands and arguments.
    Supports both traditional and declarative commands.
    """
    
    def __init__(self, commands):
        """
        Initialize the completer with available commands.
        
        Args:
            commands: Dictionary of command_name -> command_instance
        """
        self.commands = commands
        
        # Commands that might need variable completion
        self.var_sensitive_commands = [
            'echo', 'set', 'unset'
        ]
    
    def get_completions(self, document, complete_event):
        """
        Get completions for the current document.
        
        Args:
            document: The document to complete
            complete_event: The complete event
            
        Returns:
            Generator of Completion objects
        """
        text = document.text_before_cursor
        
        # Check if we're completing a command or arguments
        if ' ' in text:
            # We're completing arguments for a command
            parts = text.split(' ', 1)
            cmd = parts[0].lower()
            args = parts[1] if len(parts) > 1 else ""
            
            if cmd in self.commands:
                cmd_instance = self.commands[cmd]
                
                # Handle declarative commands
                if isinstance(cmd_instance, DeclarativeCommand):
                    yield from self._get_declarative_completions(cmd_instance, document, complete_event, args)
                else:
                    # Traditional command completion
                    if hasattr(cmd_instance, 'get_completions'):
                        for completion in cmd_instance.get_completions(args):
                            yield completion
                            
                # For variable-sensitive commands, provide variable completion
                if cmd in self.var_sensitive_commands and '$' in args:
                    yield from self._get_variable_completions(args)
        else:
            # We're completing a command name
            word = text.lower()
            
            # Complete command names
            for cmd_name in sorted(self.commands.keys()):
                if cmd_name.startswith(word):
                    cmd_instance = self.commands[cmd_name]
                    
                    # Get description for display_meta if available
                    if isinstance(cmd_instance, DeclarativeCommand):
                        display_meta = cmd_instance._command_description.split('\n')[0]
                    else:
                        display_meta = ""
                    
                    yield Completion(
                        cmd_name,
                        start_position=-len(word),
                        display=cmd_name,
                        display_meta=display_meta
                    )
    
    def _get_variable_completions(self, args):
        """
        Get completions for variable references.
        
        Args:
            args: The argument string
            
        Returns:
            Generator of Completion objects
        """
        last_dollar = args.rfind('$')
        if last_dollar >= 0:
            var_prefix = args[last_dollar+1:]
            
            # Check if we're in a ${var.prop} expression
            in_brace = last_dollar + 1 < len(args) and args[last_dollar+1:last_dollar+2] == '{'
            
            # Get variables from the shell (if available)
            # This assumes we'll have access to the shell instance, which we don't here
            # In a real implementation, you'd get this from the shell's variable_manager
            variables = {
                'servers': [],
                'paths': {},
                'cleanup_days': 0,
                'verbose': False
            }
            
            for var_name in variables.keys():
                if var_name.startswith(var_prefix):
                    completion_text = var_name
                    if in_brace:
                        # If we're in a brace expression, include the closing brace
                        completion_text += '}'
                    
                    yield Completion(
                        completion_text,
                        start_position=-len(var_prefix),
                        display=var_name
                    )
    
    def _get_declarative_completions(self, cmd_instance, document, complete_event, args_str):
        """
        Get completions for a declarative command.
        
        Args:
            cmd_instance: The command instance
            document: The document to complete
            complete_event: The complete event
            args_str: The argument string
            
        Returns:
            Generator of Completion objects
        """
        # Get parameter definitions
        param_defs = cmd_instance.__class__.get_parameter_definitions()
        
        # Parse the arguments so far
        try:
            arg_parts = shlex.split(args_str, posix=True)
        except ValueError:
            # Invalid string (like unclosed quotes)
            arg_parts = args_str.split()
        
        # Determine which argument we're completing
        arg_index = len(arg_parts)
        if not args_str.endswith(" ") and arg_parts:
            current_arg = arg_parts[-1]
            arg_index -= 1
        else:
            current_arg = ""
        
        # Separate positional and named parameters
        positional_params = sorted(
            [param for param in param_defs if param.position is not None],
            key=lambda param: param.position
        )
        
        # Check if we're completing a parameter name
        if current_arg.startswith('-'):
            # Complete parameter names
            for param_def in param_defs:
                completion = param_def.get_param_completion(current_arg)
                if completion:
                    yield completion
            return
        
        # Check if we're completing a value for a named parameter
        if arg_index > 0 and arg_parts[arg_index-1].startswith('-'):
            param_name = arg_parts[arg_index-1]
            # Find parameter definition for this name
            for param_def in param_defs:
                if param_name in param_def.all_param_names:
                    for completion in param_def.get_completions(current_arg):
                        yield completion
            return
        
        # Otherwise, we're completing a positional parameter or suggesting a named parameter
        
        # Count used positional parameters
        used_positional = 0
        for i, part in enumerate(arg_parts):
            if not part.startswith('-') and (i == 0 or not arg_parts[i-1].startswith('-')):
                used_positional += 1
        
        # If we have positional parameters available, suggest the next one
        if used_positional < len(positional_params):
            current_pos_param = positional_params[used_positional]
            
            # If we're in the middle of typing, provide completions
            if not args_str.endswith(" "):
                for completion in current_pos_param.get_completions(current_arg):
                    yield completion
            
            # Otherwise, provide a hint for what parameter is expected
            elif args_str.endswith(" ") or not arg_parts:
                yield Completion(
                    "",
                    start_position=0,
                    display=f"<{current_pos_param.name}>",
                    display_meta=f"{current_pos_param.type.__name__} (positional parameter)"
                )
        
        # Also suggest named parameters if we're not in the middle of typing
        if args_str.endswith(" ") or not arg_parts:
            for param_def in param_defs:
                # Check if parameter name has been used
                used = any(part in param_def.all_param_names for part in arg_parts)
                if not used:
                    meta = f"{param_def.type.__name__}"
                    if not param_def.mandatory:
                        meta += f" (default: {param_def.default})"
                    if param_def.help_text:
                        meta += f" - {param_def.help_text}"
                    
                    yield Completion(
                        param_def.param_name,
                        start_position=0,
                        display=param_def.param_name,
                        display_meta=meta
                    )