"""
Custom command completer for the shell.
"""
import shlex
from prompt_toolkit.completion import Completer, Completion

# Import declarative command support if available
try:
    from commands.declarative import DeclarativeCommand
    DECLARATIVE_AVAILABLE = True
except ImportError:
    DECLARATIVE_AVAILABLE = False


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
                
                # Handle declarative commands differently
                if DECLARATIVE_AVAILABLE and isinstance(cmd_instance, DeclarativeCommand):
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
                    if DECLARATIVE_AVAILABLE and isinstance(cmd_instance, DeclarativeCommand):
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
        # Get argument definitions
        arg_defs = cmd_instance.__class__.get_argument_definitions()
        
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
        
        # Get argument at this position
        if arg_index < len(arg_defs):
            arg_def = arg_defs[arg_index]
            
            # Show argument type in completions
            meta = f"{arg_def.type.__name__}"
            if arg_def.required:
                meta += " (required)"
            else:
                meta += f" (default: {arg_def.default})"
            
            # If it has completions, provide them
            if arg_def.completer:
                for completion in arg_def.completer.get_completions(document, complete_event):
                    # Enhance with argument information
                    yield Completion(
                        completion.text,
                        start_position=completion.start_position,
                        display=completion.display or completion.text,
                        display_meta=meta
                    )
            # Otherwise, just show what argument is expected
            elif current_arg == "":
                # Provide a hint about what argument is expected
                yield Completion(
                    "",
                    start_position=0,
                    display=f"<{arg_def.name}>",
                    display_meta=meta
                )
        else:
            # All arguments provided - check if there are any more optional args
            remaining_args = [
                arg for i, arg in enumerate(arg_defs) 
                if i >= arg_index and not arg.required
            ]
            
            if remaining_args:
                # Show what optional args are available
                for arg in remaining_args:
                    yield Completion(
                        "",
                        start_position=0,
                        display=f"[{arg.name}]",
                        display_meta=f"{arg.type.__name__} (optional)"
                    )