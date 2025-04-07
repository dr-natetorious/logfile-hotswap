"""
Tests for the prompt_toolkit integration in the shell.
"""
import os
import tempfile
import pytest
from unittest.mock import patch, MagicMock, call

from prompt_toolkit.history import FileHistory
from prompt_toolkit.completion import Completion
from prompt_toolkit.document import Document
from prompt_toolkit.formatted_text import FormattedText

from src.cli.shell.shell import ServerShell
from src.cli.shell.completer import ShellCompleter

class TestPromptToolkitIntegration:
    """Test suite for prompt_toolkit integration."""

    @pytest.fixture
    def temp_history_file(self):
        """Fixture that creates a temporary history file."""
        fd, path = tempfile.mkstemp()
        try:
            os.close(fd)
            yield path
        finally:
            os.unlink(path)

    @pytest.fixture
    def mock_command_handler(self):
        """Fixture for a mocked CommandHandler with sample commands."""
        with patch('src.cli.shell.shell.CommandHandler') as mock:
            handler = mock.return_value
            # Define some sample commands for testing completion
            commands = {
                'help': MagicMock(description="Show help"),
                'exit': MagicMock(description="Exit the shell"),
                'connect': MagicMock(description="Connect to a server"),
                'list': MagicMock(description="List available servers")
            }
            handler.get_commands.return_value = commands
            yield handler

    @pytest.fixture
    def shell_with_history(self, temp_history_file, mock_command_handler):
        """Fixture that returns a shell with a real history file."""
        with patch('src.cli.shell.shell.VariableManager'), \
             patch('src.cli.shell.shell.ConfigStoreManager'), \
             patch('src.cli.shell.shell.DiscoveryCoordinator'):
            
            config = {'history_file': temp_history_file}
            shell = ServerShell(config=config)
            
            # Replace the session with a mock to avoid terminal interaction
            shell.session = MagicMock()
            
            yield shell

    def test_history_file_creation(self, temp_history_file):
        """Test that a history file is created when the shell is initialized."""
        with patch('src.cli.shell.shell.CommandHandler'), \
             patch('src.cli.shell.shell.VariableManager'), \
             patch('src.cli.shell.shell.ConfigStoreManager'), \
             patch('src.cli.shell.shell.DiscoveryCoordinator'), \
             patch('src.cli.shell.shell.PromptSession') as mock_session:
            
            config = {'history_file': temp_history_file}
            shell = ServerShell(config=config)
            
            # Verify FileHistory was created with the correct path
            mock_session.assert_called_once()
            call_kwargs = mock_session.call_args[1]
            assert 'history' in call_kwargs
            assert isinstance(call_kwargs['history'], FileHistory)
            assert call_kwargs['history'].filename == temp_history_file

    def test_auto_suggest_configuration(self):
        """Test that AutoSuggestFromHistory is configured correctly."""
        with patch('src.cli.shell.shell.CommandHandler'), \
             patch('src.cli.shell.shell.VariableManager'), \
             patch('src.cli.shell.shell.ConfigStoreManager'), \
             patch('src.cli.shell.shell.DiscoveryCoordinator'), \
             patch('src.cli.shell.shell.PromptSession') as mock_session, \
             patch('src.cli.shell.shell.AutoSuggestFromHistory') as mock_auto_suggest:
            
            shell = ServerShell()
            
            # Verify AutoSuggestFromHistory was created and used
            mock_auto_suggest.assert_called_once()
            mock_session.assert_called_once()
            call_kwargs = mock_session.call_args[1]
            assert 'auto_suggest' in call_kwargs
            assert call_kwargs['auto_suggest'] is mock_auto_suggest.return_value

    def test_completer_initialization(self, mock_command_handler):
        """Test that the ShellCompleter is initialized with commands."""
        with patch('src.cli.shell.shell.VariableManager'), \
             patch('src.cli.shell.shell.ConfigStoreManager'), \
             patch('src.cli.shell.shell.DiscoveryCoordinator'), \
             patch('src.cli.shell.shell.PromptSession') as mock_session, \
             patch('src.cli.shell.shell.ShellCompleter') as mock_completer_class:
            
            shell = ServerShell()
            
            # Verify ShellCompleter was created with commands
            mock_completer_class.assert_called_once_with(mock_command_handler.get_commands.return_value)
            
            # Verify PromptSession was created with the completer
            mock_session.assert_called_once()
            call_kwargs = mock_session.call_args[1]
            assert 'completer' in call_kwargs
            assert call_kwargs['completer'] is mock_completer_class.return_value

    def test_shell_completer_completion(self):
        """Test that the ShellCompleter provides correct completions."""
        # Create a sample command dict
        commands = {
            'help': MagicMock(description="Show help"),
            'exit': MagicMock(description="Exit the shell"),
            'connect': MagicMock(description="Connect to a server"),
            'list': MagicMock(description="List available servers")
        }
        
        # Create a ShellCompleter with the commands
        completer = ShellCompleter(commands)
        
        # Test completion for an empty string (should offer all commands)
        completions = list(completer.get_completions(Document("", 0), MagicMock()))
        assert len(completions) == 4
        assert all(isinstance(c, Completion) for c in completions)
        completion_texts = [c.text for c in completions]
        assert 'help' in completion_texts
        assert 'exit' in completion_texts
        assert 'connect' in completion_texts
        assert 'list' in completion_texts
        
        # Test partial completion (should offer matching commands)
        completions = list(completer.get_completions(Document("co", 2), MagicMock()))
        assert len(completions) == 1
        assert completions[0].text == 'connect'
        
        # Test no completions for non-matching prefix
        completions = list(completer.get_completions(Document("xyz", 3), MagicMock()))
        assert len(completions) == 0

    def test_prompt_session_usage(self, shell_with_history):
        """Test that the PromptSession is used correctly in the run loop."""
        shell = shell_with_history
        
        # Setup the prompt method to return a command and then trigger exit
        shell.session.prompt.side_effect = [
            "test command",
            EOFError()
        ]
        
        # Mock process_command to avoid actually processing commands
        shell.process_command = MagicMock()
        
        # Run the shell
        shell.run()
        
        # Verify prompt was called with the correct prompt text
        shell.session.prompt.assert_any_call("shell> ")
        
        # Verify process_command was called with the input
        shell.process_command.assert_called_once_with("test command")

    def test_prompt_with_server_context(self, shell_with_history):
        """Test that the prompt includes server context when available."""
        shell = shell_with_history
        shell.context['current_server'] = 'test-server'
        
        # Setup the prompt method to return a command and then trigger exit
        shell.session.prompt.side_effect = [
            "test command",
            EOFError()
        ]
        
        # Mock process_command to avoid actually processing commands
        shell.process_command = MagicMock()
        
        # Run the shell
        shell.run()
        
        # Verify prompt was called with the server-specific prompt text
        shell.session.prompt.assert_any_call("test-server> ")


class TestPromptToolkitIntegrationWithApp:
    """
    Test suite for more advanced prompt_toolkit integration using Application.
    
    These tests require more setup but provide better validation of the
    actual prompt_toolkit behavior.
    """

    @pytest.mark.skip(reason="These tests require a more complex setup and are provided as examples")
    def test_with_prompt_toolkit_app(self):
        """
        Example of how to test with a full prompt_toolkit Application.
        
        This would require additional setup to create a test environment that
        can simulate key presses and capture output.
        """
        # Implementation would go here
        pass


# Additional testing utilities that could be useful for prompt_toolkit testing

def create_pipe_input():
    """
    Create a PipeInput that can be used to simulate user input.
    
    This requires prompt_toolkit's testing utilities.
    
    Returns:
        A PipeInput object for sending input to prompt_toolkit
    """
    from prompt_toolkit.input.defaults import create_pipe_input
    pipe_input = create_pipe_input()
    return pipe_input

def get_app_output(app):
    """
    Get the output from a prompt_toolkit Application.
    
    Args:
        app: The prompt_toolkit Application
        
    Returns:
        The rendered output as text
    """
    from prompt_toolkit.output import DummyOutput
    output = DummyOutput()
    app.output = output
    app.run()
    return output.data