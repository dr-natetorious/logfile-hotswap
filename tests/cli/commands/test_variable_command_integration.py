"""
Integration tests for variable commands with the actual VariableManager.
"""
import pytest
from unittest.mock import MagicMock, patch
import io
import sys

from src.cli.commands.variable_commands import (
    SetVariableCommand,
    UnsetVariableCommand,
    ListVariablesCommand,
    EchoCommand
)
from src.cli.shell.variable_manager import VariableManager


class TestVariableCommandsIntegration:
    @pytest.fixture
    def shell_with_var_manager(self):
        """Create a shell mock with a real VariableManager."""
        shell_mock = MagicMock()
        shell_mock.variable_manager = VariableManager()
        return shell_mock
    
    @pytest.fixture
    def capture_stdout(self):
        """Fixture to capture stdout."""
        old_stdout = sys.stdout
        new_stdout = io.StringIO()
        sys.stdout = new_stdout
        yield new_stdout
        sys.stdout = old_stdout
    
    def test_set_and_echo_variable(self, shell_with_var_manager, capture_stdout):
        """Test setting a variable and echoing it."""
        # Set a variable
        set_cmd = SetVariableCommand.parse("test_var 'Hello, World!'")
        result = set_cmd.execute_command(shell_with_var_manager)
        
        assert result is True
        stdout = capture_stdout.getvalue()
        assert "Set test_var" in stdout
        assert "Hello, World" in stdout

        # Clear the captured output
        capture_stdout.truncate(0)
        capture_stdout.seek(0)
        
        # Echo the variable
        echo_cmd = EchoCommand.parse("'Value: $test_var'")
        result = echo_cmd.execute_command(shell_with_var_manager)
        
        assert result is True
        stdout = capture_stdout.getvalue()
        assert "Value: Hello, World!" in stdout
    
    def test_set_and_unset_variable(self, shell_with_var_manager, capture_stdout):
        """Test setting and then unsetting a variable."""
        # Set a variable
        set_cmd = SetVariableCommand.parse("temp_var '123'")
        result = set_cmd.execute_command(shell_with_var_manager)
        
        assert result is True
        
        # Clear the captured output
        capture_stdout.truncate(0)
        capture_stdout.seek(0)
        
        # List variables to verify it was set
        list_cmd = ListVariablesCommand.parse("")
        result = list_cmd.execute_command(shell_with_var_manager)
        
        assert result is True
        stdout = capture_stdout.getvalue()
        assert "temp_var = 123" in stdout
        
        # Clear the captured output
        capture_stdout.truncate(0)
        capture_stdout.seek(0)
        
        # Unset the variable
        unset_cmd = UnsetVariableCommand.parse("temp_var")
        result = unset_cmd.execute_command(shell_with_var_manager)
        
        assert result is True
        stdout = capture_stdout.getvalue()
        assert "Deleted variable: temp_var" in stdout
        
        # Clear the captured output
        capture_stdout.truncate(0)
        capture_stdout.seek(0)
        
        # List variables to verify it was removed
        list_cmd = ListVariablesCommand.parse("")
        result = list_cmd.execute_command(shell_with_var_manager)
        
        assert result is True
        stdout = capture_stdout.getvalue()
        assert "temp_var" not in stdout
    
    def test_complex_expression_evaluation(self, shell_with_var_manager, capture_stdout):
        """Test setting variables with complex expressions."""
        # Set a variable with a list expression
        set_cmd = SetVariableCommand.parse("numbers '[1, 2, 3, 4, 5]'")
        result = set_cmd.execute_command(shell_with_var_manager)
        assert result is True
        
        # Clear the captured output
        capture_stdout.truncate(0)
        capture_stdout.seek(0)
        
        # Set a variable that uses the first variable in an expression
        set_cmd = SetVariableCommand.parse("sum_result 'sum(numbers)'")
        result = set_cmd.execute_command(shell_with_var_manager)
        assert result is True
        
        # Clear the captured output
        capture_stdout.truncate(0)
        capture_stdout.seek(0)
        
        # Echo the result using variable expansion with complex expression
        echo_cmd = EchoCommand.parse("'Sum of numbers: ${sum_result}'")
        result = echo_cmd.execute_command(shell_with_var_manager)
        
        assert result is True
        stdout = capture_stdout.getvalue()
        assert "Sum of numbers: 15" in stdout
    
    def test_variable_list_verbose(self, shell_with_var_manager, capture_stdout):
        """Test listing variables in verbose mode."""
        # Set different types of variables
        shell_with_var_manager.variable_manager.set("str_var", "'test'")
        shell_with_var_manager.variable_manager.set("int_var", "42")
        shell_with_var_manager.variable_manager.set("list_var", "[1, 2, 3]")
        shell_with_var_manager.variable_manager.set("dict_var", "{'a': 1, 'b': 2}")
        
        # Clear the captured output
        capture_stdout.truncate(0)
        capture_stdout.seek(0)
        
        # List variables with verbose flag
        list_cmd = ListVariablesCommand.parse("-verbose")
        result = list_cmd.execute_command(shell_with_var_manager)
        
        assert result is True
        stdout = capture_stdout.getvalue()
        
        # Verify type information is included
        assert "str_var (str) = test" in stdout
        assert "int_var (int) = 42" in stdout
        assert "list_var (list) =" in stdout
        assert "dict_var (dict) =" in stdout
    
    def test_echo_no_newline(self, shell_with_var_manager):
        """Test that echo command respects no_newline flag."""
        with patch('builtins.print') as mock_print:
            echo_cmd = EchoCommand.parse("'Hello' -n")
            result = echo_cmd.execute_command(shell_with_var_manager)
            
            assert result is True
            mock_print.assert_called_once_with("Hello", end="")
    
    def test_error_handling(self, shell_with_var_manager, capture_stdout):
        """Test error handling in variable commands."""
        # Try to set a variable with an invalid expression
        set_cmd = SetVariableCommand.parse("error_var '[1, 2,'")
        result = set_cmd.execute_command(shell_with_var_manager)
        
        assert result is False
        stdout = capture_stdout.getvalue()
        assert "Error:" in stdout