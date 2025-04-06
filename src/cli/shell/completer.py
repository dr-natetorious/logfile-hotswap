"""
Custom command completer for the shell.
"""
from prompt_toolkit.completion import Completer, Completion

class ShellCompleter(Completer):
    """
    Custom completer for shell commands and arguments.
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
            cmd, args = text.split(' ', 1)
            cmd = cmd.lower()
            
            if cmd in self.commands:
                # If the command implements get_completions method, use it
                cmd_instance = self.commands[cmd]
                if hasattr(cmd_instance, 'get_completions'):
                    for completion in cmd_instance.get_completions(args):
                        yield completion
                        
                # For variable-sensitive commands, check if we're completing a variable reference
                if cmd in self.var_sensitive_commands and '$' in args:
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
        else:
            # We're completing a command name
            word = text.lower()
            
            # Complete command names
            for cmd_name in sorted(self.commands.keys()):
                if cmd_name.startswith(word):
                    yield Completion(
                        cmd_name,
                        start_position=-len(word),
                        display=cmd_name
                    )