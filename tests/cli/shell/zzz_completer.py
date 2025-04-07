"""
Tests for the custom ShellCompleter class.
"""
import pytest
from unittest.mock import MagicMock, patch
from prompt_toolkit.document import Document
from prompt_toolkit.completion import Completion

from src.cli.shell.completer import ShellCompleter
from src.cli.commands.declarative import DeclarativeCommand


class MockTraditionalCommand:
    """Mock for a traditional (non-declarative) command."""
    
    def __init__(self, name, completions=None):
        self.name = name
        self._completions = completions or []
    
    def get_completions(self, args):
        """Return predefined completions."""
        return self._completions


class MockDeclarativeCommand(DeclarativeCommand):
    """Mock for a declarative command with parameters."""
    
    _command_name = "mock_declarative"
    _command_description = "Mock declarative command for testing"
    
    @classmethod
    def get_parameter_definitions(cls):
        """Return mock parameter definitions."""
        return cls._param_definitions


# Mock parameter definition for declarative commands
class MockParamDef:
    def __init__(self, name, position=None, param_name=None, all_param_names=None, 
                 mandatory=True, default=None, type=str, help_text=None, completions=None):
        self.name = name
        self.position = position
        self.param_name = param_name or f"--{name}"
        self.all_param_names = all_param_names or [self.param_name]
        self.mandatory = mandatory
        self.default = default
        self.type = type
        self.help_text = help_text
        self._completions = completions or []
    
    def get_param_completion(self, text):
        """Get completion for parameter name."""
        for name in self.all_param_names:
            if name.startswith(text):
                return Completion(
                    name,
                    start_position=-len(text),
                    display=name,
                    display_meta=self.help_text or ""
                )
        return None
    
    def get_completions(self, text):
        """Get completions for parameter value."""
        for completion in self._completions:
            if completion.startswith(text):
                yield Completion(
                    completion,
                    start_position=-len(text),
                    display=completion
                )


class TestShellCompleter:
    """Test suite for the ShellCompleter class."""

    @pytest.fixture
    def traditional_commands(self):
        """Fixture that returns sample traditional commands."""
        help_cmd = MockTraditionalCommand("help", [
            Completion("topic1", display="topic1", display_meta="Help topic 1"),
            Completion("topic2", display="topic2", display_meta="Help topic 2")
        ])
        
        ls_cmd = MockTraditionalCommand("ls", [
            Completion("-l", display="-l", display_meta="Long format"),
            Completion("-a", display="-a", display_meta="Show all")
        ])
        
        return {
            "help": help_cmd,
            "ls": ls_cmd,
            "exit": MockTraditionalCommand("exit")
        }
    
    @pytest.fixture
    def declarative_commands(self):
        """Fixture that returns sample declarative commands."""
        # Create parameter definitions for connect command
        connect_params = [
            MockParamDef("server", position=0, help_text="Server to connect to", 
                         completions=["server1", "server2", "production"]),
            MockParamDef("port", position=None, param_name="--port", 
                         all_param_names=["--port", "-p"], mandatory=False, 
                         default=22, type=int, help_text="Port number")
        ]
        
        # Create parameter definitions for config command
        config_params = [
            MockParamDef("option", position=0, help_text="Configuration option",
                         completions=["timeout", "retries", "verbose"]),
            MockParamDef("value", position=1, help_text="Option value"),
            MockParamDef("save", position=None, param_name="--save", 
                         mandatory=False, default=False, type=bool, 
                         help_text="Save to config file")
        ]
        
        # Create mock declarative commands
        connect_cmd = MockDeclarativeCommand()
        connect_cmd._param_definitions = connect_params
        
        config_cmd = MockDeclarativeCommand()
        config_cmd._param_definitions = config_params
        config_cmd._command_name = "config"
        config_cmd._command_description = "Configure settings"
        
        return {
            "connect": connect_cmd,
            "config": config_cmd
        }
    
    @pytest.fixture
    def completer(self, traditional_commands, declarative_commands):
        """Fixture that returns a configured ShellCompleter."""
        commands = {**traditional_commands, **declarative_commands}
        return ShellCompleter(commands)

    def test_command_name_completion(self, completer):
        """Test completion of command names."""
        # Empty input should return all commands
        document = Document("", 0)
        completions = list(completer.get_completions(document, MagicMock()))
        assert len(completions) == 5  # All commands
        
        # Partial match should return matching commands
        document = Document("c", 1)
        completions = list(completer.get_completions(document, MagicMock()))
        assert len(completions) == 2  # connect, config
        assert any(c.text == "connect" for c in completions)
        assert any(c.text == "config" for c in completions)
        
        # Exact match to a single command should return no completions for command name
        document = Document("exit", 4)
        completions = list(completer.get_completions(document, MagicMock()))
        assert len(completions) == 0  # No command name completions for exact match
    
    def test_traditional_command_arg_completion(self, completer):
        """Test completion of arguments for traditional commands."""
        # Test help command completions
        document = Document("help ", 5)
        completions = list(completer.get_completions(document, MagicMock()))
        assert len(completions) == 2  # help topics
        
        document = Document("help t", 6)
        completions = list(completer.get_completions(document, MagicMock()))
        assert len(completions) == 2  # topics starting with 't'
        
        # Test ls command completions
        document = Document("ls -", 4)
        completions = list(completer.get_completions(document, MagicMock()))
        assert len(completions) == 2  # -l and -a options
    
    def test_declarative_command_positional_completion(self, completer):
        """Test completion of positional parameters for declarative commands."""
        # Test connect command with server parameter
        document = Document("connect ", 8)
        completions = list(completer.get_completions(document, MagicMock()))
        
        # We should get server completions plus a hint completion
        server_options = ["server1", "server2", "production"]
        assert any(c.display == "<server>" for c in completions)
        
        # Test partial server name
        document = Document("connect ser", 11)
        completions = list(completer.get_completions(document, MagicMock()))
        assert len(completions) == 2  # server1, server2
        assert all(c.text in server_options for c in completions)
        
        # Test config command with multiple positional parameters
        document = Document("config timeout ", 15)
        completions = list(completer.get_completions(document, MagicMock()))
        assert any(c.display == "<value>" for c in completions)  # Second positional param
    
    def test_declarative_command_named_param_completion(self, completer):
        """Test completion of named parameters for declarative commands."""
        # Test connect command with --port parameter
        document = Document("connect --", 10)
        completions = list(completer.get_completions(document, MagicMock()))
        assert any(c.text == "--port" for c in completions)
        
        # Test partial parameter name
        document = Document("connect --p", 11)
        completions = list(completer.get_completions(document, MagicMock()))
        assert len(completions) == 1
        assert completions[0].text == "--port"
        
        # Test config command with --save parameter
        document = Document("config timeout --", 17)
        completions = list(completer.get_completions(document, MagicMock()))
        assert any(c.text == "--save" for c in completions)
    
    def test_declarative_command_named_param_value_completion(self, completer):
        """Test completion of values for named parameters."""
        # Currently not handling specific completions for named parameter values
        # This is a placeholder for when that functionality is implemented
        document = Document("connect --port ", 15)
        completions = list(completer.get_completions(document, MagicMock()))
        assert len(completions) == 0  # No completions for port values

    @patch('src.cli.shell.completer.shlex.split')
    def test_argument_parsing_error_handling(self, mock_split, completer):
        """Test handling of parsing errors for arguments."""
        # Simulate parsing error (like unclosed quotes)
        mock_split.side_effect = ValueError("Unclosed quotes")
        
        document = Document('connect "unclosed', 17)
        # This should not raise an exception
        completions = list(completer.get_completions(document, MagicMock()))
        # Will fall back to simple splitting by spaces
        assert len(completions) >= 0  # May or may not have completions based on fallback
    
    def test_variable_completion(self, completer):
        """Test completion of variable references."""
        # Test variable completion in var-sensitive command
        document = Document("echo $", 6)
        completions = list(completer.get_completions(document, MagicMock()))
        
        # Should suggest variables
        variable_names = ["servers", "paths", "cleanup_days", "verbose"]
        for var_name in variable_names:
            assert any(c.text == var_name for c in completions)
        
        # Test partial variable name
        document = Document("set $s", 6)
        completions = list(completer.get_completions(document, MagicMock()))
        assert len(completions) == 1
        assert completions[0].text == "servers"
        
        # Test variable completion in non-var-sensitive command
        document = Document("ls $", 4)
        completions = list(completer.get_completions(document, MagicMock()))
        assert len(completions) == 0  # No completions for variables in ls
    
    def test_brace_variable_completion(self, completer):
        """Test completion of variable references with braces."""
        document = Document("echo ${", 7)
        completions = list(completer.get_completions(document, MagicMock()))
        
        # Should suggest variables with closing brace
        variable_names = ["servers}", "paths}", "cleanup_days}", "verbose}"]
        for var_name in variable_names:
            assert any(c.text == var_name for c in completions)
    
    def test_mixed_commands_completion(self, completer):
        """Test that both traditional and declarative commands work together."""
        # Test that we get completions for both types
        document = Document("", 0)
        completions = list(completer.get_completions(document, MagicMock()))
        
        # Should have both traditional and declarative commands
        traditional_names = ["help", "ls", "exit"]
        declarative_names = ["connect", "config"]
        
        for name in traditional_names:
            assert any(c.text == name for c in completions)
        
        for name in declarative_names:
            assert any(c.text == name for c in completions)