"""
Integration tests for the exit command with the command handler.
"""
import pytest
from unittest.mock import MagicMock

from src.cli.commands.exit_command import ExitCommand
from src.cli.shell.command_handler import CommandHandler


class TestExitCommandIntegration:
    """Test the ExitCommand integration with the command handler."""
    
    @pytest.fixture
    def command_handler_setup(self):
        """Create a CommandHandler with a mock shell."""
        shell_mock = MagicMock()
        handler = CommandHandler()
        return handler, shell_mock
    
    @pytest.mark.parametrize("cmd_name", ["exit", "quit", "bye"])
    def test_execute_with_command_names(self, command_handler_setup, cmd_name):
        """Test executing the command using its primary name and aliases."""
        handler, shell_mock = command_handler_setup
        
        # Execute the command
        handler.execute_command(cmd_name, "", shell_mock)
        
        # Verify that shell.exit_shell was called with default exit code
        shell_mock.exit_shell.assert_called_once_with(0)
    
    @pytest.mark.parametrize("cmd_str, expected_code", [
        ("exit 42", 42),
        ("quit 1", 1),
        ("bye 255", 255),
        ("exit -exitcode 99", 99)
    ])
    def test_execute_with_exitcode(self, command_handler_setup, cmd_str, expected_code):
        """Test executing the command with various exit codes."""
        handler, shell_mock = command_handler_setup
        
        # Execute the command
        name, args = cmd_str.split(' ', maxsplit=1)
        handler.execute_command(name, args, shell_mock)
        
        # Verify that shell.exit_shell was called with the correct exit code
        shell_mock.exit_shell.assert_called_once_with(expected_code)
    
    # @pytest.mark.parametrize("prefix, expected_cmd", [
    #     ("ex", "exit"),
    #     ("qu", "quit"),
    #     ("by", "bye")
    # ])
    # def test_command_completion(self, command_handler_setup, prefix, expected_cmd):
    #     """Test command completion for the exit command and its aliases."""
    #     handler, _ = command_handler_setup
        
    #     # Get completions for the command prefix
    #     completions = handler.get_completions(prefix)
        
    #     # Should suggest the expected command
    #     assert any(c.text == expected_cmd for c in completions), f"Expected '{expected_cmd}' in completions for prefix '{prefix}'"