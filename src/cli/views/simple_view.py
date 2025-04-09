"""
Simple view implementation based on the original shell.
"""
import traceback
from prompt_toolkit import PromptSession
from prompt_toolkit.history import FileHistory
from prompt_toolkit.auto_suggest import AutoSuggestFromHistory
from prompt_toolkit.completion import merge_completers
from prompt_toolkit.formatted_text import HTML

from cli.views.base_view import BaseView
from cli.shell.exceptions import ShellExit
from cli.shell.update_info_node import UpdateInfoNode


class SimpleView(BaseView):
    """Simple command-line interface view based on the original shell."""
    
    def __init__(self, shell):
        """Initialize the simple view.
        
        Args:
            shell: The parent shell instance
        """
        super().__init__(shell)
        self.session = None
    
    def setup(self):
        """Set up the view components."""
        # Set up prompt session
        history_file = self.shell.config.get('history_file', '.shell_history')
        
        # Get completer from command handler
        completer = None
        if hasattr(self.shell.command_handler, 'get_completer'):
            completer = self.shell.command_handler.get_completer()
        
        self.session = PromptSession(
            history=FileHistory(history_file),
            auto_suggest=AutoSuggestFromHistory(),
            completer=completer,
            complete_in_thread=True,
            complete_while_typing=True
        )

    def create_layout(self):
        """Create the prompt_toolkit layout for this view.
        
        In SimpleView, we don't use the prompt_toolkit layout system
        since we're using PromptSession directly.
        """
        # For compatibility with BaseView
        from prompt_toolkit.layout import Layout
        from prompt_toolkit.layout.containers import Container
        
        return Layout(Container())
    
    def get_prompt_text(self):
        """Generate the prompt text based on current context."""
        # Start with basic prompt
        prompt_parts = []
        
        # Add server context if available
        if self.shell.context.get('current_server'):
            server_name = self.shell.context['current_server']
            prompt_parts.append(HTML(f"<ansired>{server_name}</ansired>"))
        else:
            prompt_parts.append(HTML("<ansigreen>shell</ansigreen>"))
        
        # Add the final prompt character
        prompt_parts.append(HTML("<ansiyellow>></ansiyellow> "))
        
        return prompt_parts
    
    def run(self):
        """Run the main view loop."""
        self.running = True
        
        # Print welcome message
        print("Welcome to Server Management Shell")
        print('Type "help" for available commands, "exit" to quit, or "view editor" to switch to the editor view')
        
        while self.running:
            try:
                # Get input from user with custom prompt
                user_input = self.session.prompt(self.get_prompt_text())
                
                # Skip empty inputs
                if not user_input.strip():
                    continue
                
                # Process the command
                self.process_command(user_input)
                
            except KeyboardInterrupt:
                # Handle Ctrl+C - reset the input buffer
                continue
            except EOFError:
                # Handle Ctrl+D - exit the shell
                self.running = False
                print("\nExiting shell. Goodbye!")
                break
            except ShellExit:
                # Command requested shell exit
                self.running = False
                print("Exiting shell. Goodbye!")
                break
            except Exception as e:
                print(f"Error: {e}")
                traceback.print_exc()
    
    def update_ui_for_command_execution(self, update_info: UpdateInfoNode) -> None:
        """Update UI after command execution.
        
        In SimpleView, we don't need to explicitly update the UI since
        output is directly printed to the console.
        
        Args:
            update_info: The update info node
        """
        pass
    
    def cleanup(self):
        """Clean up resources before exiting or switching views."""
        super().cleanup()
        # Nothing specific to clean up for simple view
