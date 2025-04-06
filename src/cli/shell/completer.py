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