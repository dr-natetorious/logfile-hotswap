"""
Tests for variable commands using the declarative command system.
"""
import pytest
from unittest.mock import MagicMock, patch
from typing import Dict, Any

from src.cli.commands.variable_commands import (
    SetVariableCommand,
    UnsetVariableCommand,
    ListVariablesCommand,
    EchoCommand
)


class TestSetVariableCommand:
    def test_initialization(self):
        """Test that a SetVariableCommand can be initialized with parameters."""
        cmd = SetVariableCommand.parse("myvar 'test value'")
        assert cmd.name == "myvar"
        assert cmd.expression == "test value"

    def test_execute_command_success(self):
        """Test that SetVariableCommand sets a variable successfully."""
        # Setup
        shell_mock = MagicMock()
        shell_mock.variable_manager.set.return_value = "test value"
        
        # Create command
        cmd = SetVariableCommand.parse("myvar 'test value'")
        
        # Execute
        result = cmd.execute_command(shell_mock)
        
        # Verify
        assert result is True
        shell_mock.variable_manager.set.assert_called_once_with("myvar", "test value")

    def test_execute_command_error(self):
        """Test that SetVariableCommand handles errors properly."""
        # Setup
        shell_mock = MagicMock()
        shell_mock.variable_manager.set.side_effect = ValueError("Invalid expression")
        
        # Create command
        cmd = SetVariableCommand.parse("myvar 'invalid [value'")
        
        # Execute with captured stdout
        with patch('builtins.print') as mock_print:
            result = cmd.execute_command(shell_mock)
        
        # Verify
        assert result is False
        mock_print.assert_called_once_with("Error: Invalid expression")


class TestUnsetVariableCommand:
    def test_initialization(self):
        """Test that an UnsetVariableCommand can be initialized with parameters."""
        cmd = UnsetVariableCommand.parse("myvar")
        assert cmd.name == "myvar"

    def test_execute_command_variable_exists(self):
        """Test that UnsetVariableCommand deletes a variable that exists."""
        # Setup
        shell_mock = MagicMock()
        shell_mock.variable_manager.delete.return_value = True
        
        # Create command
        cmd = UnsetVariableCommand.parse("myvar")
        
        # Execute with captured stdout
        with patch('builtins.print') as mock_print:
            result = cmd.execute_command(shell_mock)
        
        # Verify
        assert result is True
        shell_mock.variable_manager.delete.assert_called_once_with("myvar")
        mock_print.assert_called_once_with("Deleted variable: myvar")

    def test_execute_command_variable_not_found(self):
        """Test that UnsetVariableCommand handles variables that don't exist."""
        # Setup
        shell_mock = MagicMock()
        shell_mock.variable_manager.delete.return_value = False
        
        # Create command
        cmd = UnsetVariableCommand.parse("nonexistent")
        
        # Execute with captured stdout
        with patch('builtins.print') as mock_print:
            result = cmd.execute_command(shell_mock)
        
        # Verify
        assert result is False  # Command should still succeed even if variable not found
        shell_mock.variable_manager.delete.assert_called_once_with("nonexistent")
        mock_print.assert_called_once_with("Variable not found: nonexistent")


class TestListVariablesCommand:
    def test_initialization_default(self):
        """Test that a ListVariablesCommand can be initialized with default parameters."""
        cmd = ListVariablesCommand.parse("")
        assert cmd.verbose is False

    def test_initialization_verbose(self):
        """Test that a ListVariablesCommand can be initialized with verbose flag."""
        cmd = ListVariablesCommand.parse("-verbose")
        assert cmd.verbose is True
        
        # Test with short alias
        cmd = ListVariablesCommand.parse("-v")
        assert cmd.verbose is True

    @pytest.mark.parametrize("variables, verbose, expected_output", [
        # Empty variables
        ({}, False, ["No variables defined"]),
        # Normal mode with different types
        (
            {"str_var": "value", "int_var": 123, "list_var": [1, 2, 3]}, 
            False, 
            ["Variables:", "  int_var = 123", "  list_var = [1, 2, 3]", "  str_var = value"]
        ),
        # Verbose mode with type information
        (
            {"str_var": "value", "int_var": 123, "list_var": [1, 2, 3]}, 
            True, 
            ["Variables:", "  int_var (int) = 123", "  list_var (list) = [1, 2, 3]", "  str_var (str) = value"]
        ),
    ])
    def test_execute_command(self, variables, verbose, expected_output):
        """Test ListVariablesCommand with different variable sets and verbose settings."""
        # Setup
        shell_mock = MagicMock()
        shell_mock.variable_manager.list_variables.return_value = variables
        
        # Create command
        cmd = ListVariablesCommand()
        cmd.verbose = verbose
        
        # Execute with captured stdout
        with patch('builtins.print') as mock_print:
            result = cmd.execute_command(shell_mock)
        
        # Verify
        assert result is True
        
        # Check that each expected line was printed
        for line in expected_output:
            mock_print.assert_any_call(line)
        
        # Verify number of print calls matches expected output
        assert mock_print.call_count == len(expected_output)


class TestEchoCommand:
    def test_initialization(self):
        """Test that an EchoCommand can be initialized with parameters."""
        cmd = EchoCommand.parse("'Hello, world!'")
        assert cmd.text == "Hello, world!"
        assert cmd.no_newline is False
        
        cmd = EchoCommand.parse("'Hello' -no_newline")
        assert cmd.text == "Hello"
        assert cmd.no_newline is True
        
        # Test with short alias
        cmd = EchoCommand.parse("'Hello' -n")
        assert cmd.text == "Hello"
        assert cmd.no_newline is True

    def test_execute_command_with_text(self):
        """Test that EchoCommand prints text with variable expansion."""
        # Setup
        shell_mock = MagicMock()
        shell_mock.variable_manager.expand_variables.return_value = "Hello, expanded world!"
        
        # Create command
        cmd = EchoCommand.parse("'Hello, $name!'")
        
        # Execute with captured stdout
        with patch('builtins.print') as mock_print:
            result = cmd.execute_command(shell_mock)
        
        # Verify
        assert result is True
        shell_mock.variable_manager.expand_variables.assert_called_once_with("Hello, $name!")
        mock_print.assert_called_once_with("Hello, expanded world!")

    def test_execute_command_without_text(self):
        """Test that EchoCommand handles empty text."""
        # Setup
        shell_mock = MagicMock()
        
        # Create command
        cmd = EchoCommand.parse("")
        cmd.text = None  # Ensure text is None
        
        # Execute with captured stdout
        with patch('builtins.print') as mock_print:
            result = cmd.execute_command(shell_mock)
        
        # Verify
        assert result is True
        mock_print.assert_called_once_with(end="\n")  # Default empty print with newline

    def test_execute_command_no_newline(self):
        """Test that EchoCommand respects the no_newline flag."""
        # Setup
        shell_mock = MagicMock()
        shell_mock.variable_manager.expand_variables.return_value = "No newline"
        
        # Create command
        cmd = EchoCommand.parse("'No newline' -n")
        
        # Execute with captured stdout
        with patch('builtins.print') as mock_print:
            result = cmd.execute_command(shell_mock)
        
        # Verify
        assert result is True
        mock_print.assert_called_once_with("No newline", end="")