"""
Tests for the exit command implementation.
"""
import pytest
from unittest.mock import MagicMock

from src.cli.commands.exit_command import ExitCommand
from src.cli.commands.declarative import CommandRegistry


@pytest.fixture
def shell_mock():
    """Create a mock shell for testing."""
    return MagicMock()


class TestExitCommand:
    """Test the ExitCommand class."""
    
    @pytest.mark.parametrize("cmd_name", ["exit", "quit", "bye"])
    def test_command_registration(self, cmd_name):
        """Test that the command and its aliases are properly registered."""
        assert CommandRegistry.get_command(cmd_name) == ExitCommand
    
    def test_get_command_names(self):
        """Test that get_command_names returns the primary command and all aliases."""
        expected_names = ["exit", "quit", "bye"]
        command_names = ExitCommand.get_command_names()
        
        assert sorted(command_names) == sorted(expected_names)
        assert len(command_names) == len(expected_names)
    
    @pytest.mark.parametrize("arg_str, expected_exitcode", [
        ("", 0),                    # Default value
        ("42", 42),                 # Positional parameter
        ("-exitcode 123", 123),     # Named parameter
    ])
    def test_initialization(self, arg_str, expected_exitcode):
        """Test ExitCommand initialization with various parameters."""
        cmd = ExitCommand.parse(arg_str)
        assert cmd.exitcode == expected_exitcode
    
    @pytest.mark.parametrize("exitcode", [0, 42, 99])
    def test_execute_command(self, shell_mock, exitcode):
        """Test that execute_command calls shell.exit_shell with the correct exit code."""
        cmd = ExitCommand.parse(str(exitcode))
        cmd.execute_command(shell_mock)
        shell_mock.exit_shell.assert_called_once_with(exitcode)
    
    def test_parse_invalid_exitcode(self):
        """Test that parsing fails with invalid exit code."""
        with pytest.raises(ValueError):
            ExitCommand.parse("not_an_integer")
    
    def test_help_text(self):
        """Test that the help text is generated correctly."""
        cmd = ExitCommand()
        help_text = cmd.get_help()
        
        # Check that help text contains key information
        expected_content = ["Exit the shell application", "exitcode", "Process exit code"]
        for content in expected_content:
            assert content in help_text
    
    def test_full_workflow(self, shell_mock):
        """Test the complete workflow from parse to execute."""
        test_exitcode = 99
        
        # Create a command instance through parse
        cmd = ExitCommand.parse(str(test_exitcode))
        
        # Verify parsing and execute
        assert cmd.exitcode == test_exitcode
        cmd.execute_command(shell_mock)
        
        # Verify shell.exit_shell was called with the correct exit code
        shell_mock.exit_shell.assert_called_once_with(test_exitcode)