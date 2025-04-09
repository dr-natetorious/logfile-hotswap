"""
Tests for the declarative command system.
"""
import pytest
from unittest.mock import MagicMock, patch
from typing import Optional, List, Union, Type, Any, Dict, ClassVar
from pathlib import Path

from src.cli.commands.declarative import (
    command,
    Parameter,
    CommandRegistry,
    ParameterDefinition,
    DeclarativeCommand
)


# Test command classes for reuse across tests
@command(name="test-cmd", description="Test command for unit testing")
class TestCommand(DeclarativeCommand):
    """Test command for unit testing."""
    
    # Define parameters with different configurations
    name: str = Parameter(position=0, mandatory=True, help="Name parameter")
    count: int = Parameter(42, help="Count parameter")
    verbose: bool = Parameter(False, help="Verbose mode", aliases=["v"])
    tags: List[str] = Parameter([], help="List of tags")
    config_path: Optional[Path] = Parameter(None, help="Path to config file")
    
    def execute_command(self, shell) -> bool:
        """Execute the command."""
        self.executed = True
        self.shell = shell
        return True


@command()
class MinimalCommand(DeclarativeCommand):
    """A minimal command with defaults."""
    
    value: str = Parameter(position=0, mandatory=True)
    
    def execute_command(self, shell) -> bool:
        """Execute the command."""
        return True


@command(name="param_test")
class ParametersTestCommand(DeclarativeCommand):
    """Command with various parameter types."""
    req_pos: str = Parameter(position=0, mandatory=True, help="Required positional")
    opt_pos: str = Parameter("default", position=1, help="Optional positional")
    flag: bool = Parameter(False, help="Boolean flag")
    str_param: str = Parameter("default_str", help="String parameter")
    int_param: int = Parameter(42, help="Integer parameter")
    
    def execute_command(self, shell) -> bool:
        return True


@command()
class AliasTestCommand(DeclarativeCommand):
    """Command to test parameter aliases."""
    verbose: bool = Parameter(False, help="Verbose flag", aliases=["v"])
    output: str = Parameter("stdout", help="Output destination", 
                           aliases=["o", "out"])
    
    def execute_command(self, shell) -> bool:
        return True


class FailingCommand(DeclarativeCommand):
    """A command that is not decorated with @command."""
    
    def execute_command(self, shell) -> bool:
        """Execute the command."""
        return True


# Create fixtures for commonly used objects
@pytest.fixture
def shell_mock():
    """Create a mock shell object."""
    return MagicMock()


# Group tests by component being tested
class TestCommandDecorator:
    """Test the @command decorator functionality."""
    
    @pytest.mark.parametrize("command_class, expected_name", [
        (TestCommand, "test-cmd"),
        (MinimalCommand, "minimal"),
        (ParametersTestCommand, "param_test"),
        (AliasTestCommand, "aliastest")
    ])
    def test_command_name_registration(self, command_class, expected_name):
        """Test command name registration through the decorator."""
        assert command_class._command_name == expected_name
        assert expected_name in CommandRegistry.get_all_commands()
        assert CommandRegistry.get_command(expected_name) == command_class
    
    @pytest.mark.parametrize("command_class, expected_description", [
        (TestCommand, "Test command for unit testing"),
        (MinimalCommand, "A minimal command with defaults."),
        (ParametersTestCommand, "Command with various parameter types."),
    ])
    def test_command_description(self, command_class, expected_description):
        """Test command description from decorator or docstring."""
        assert command_class._command_description == expected_description


class TestParameter:
    """Test the Parameter class."""
    
    def test_parameter_initialization_with_all_args(self):
        """Test Parameter initialization with all arguments."""
        param = Parameter(
            default="default",
            position=1,
            mandatory=True,
            help="Help text",
            aliases=["a", "alias"],
            validation=lambda x: x
        )
        
        assert param.default == "default"
        assert param.position == 1
        assert param.mandatory is True
        assert param.help == "Help text"
        assert param.aliases == ["a", "alias"]
        assert param.validation is not None
    
    def test_parameter_default_values(self):
        """Test Parameter initialization with default values."""
        param = Parameter()
        
        assert param.default is None
        assert param.position is None
        assert param.mandatory is False
        assert param.help is None
        assert param.aliases == []
        assert param.validation is None


class TestCommandRegistry:
    """Test the CommandRegistry class."""
    
    def test_register_command(self):
        """Test registering a command."""
        # TestCommand is already registered by the @command decorator
        assert "test-cmd" in CommandRegistry.get_all_commands()
    
    def test_get_command(self):
        """Test getting a command by name."""
        cmd_class = CommandRegistry.get_command("test-cmd")
        assert cmd_class == TestCommand
    
    def test_get_nonexistent_command(self):
        """Test getting a command that doesn't exist."""
        cmd_class = CommandRegistry.get_command("nonexistent")
        assert cmd_class is None
    
    def test_get_all_commands(self):
        """Test getting all commands."""
        commands = CommandRegistry.get_all_commands()
        assert isinstance(commands, dict)
        assert "test-cmd" in commands
        assert "minimal" in commands
        assert "param_test" in commands


class TestParameterDefinition:
    """Test the ParameterDefinition class."""
    
    def test_initialization_with_parameter_object(self):
        """Test ParameterDefinition initialization with Parameter object."""
        param_obj = Parameter(
            default="default",
            position=1,
            mandatory=True,
            help="Help text",
            aliases=["a"]
        )
        
        param_def = ParameterDefinition(
            name="test",
            type_hint=str,
            param_obj=param_obj
        )
        
        assert param_def.name == "test"
        assert param_def.type == str
        assert param_def.default == "default"
        assert param_def.position == 1
        assert param_def.help_text == "Help text"
        assert param_def.aliases == ["a"]
        assert param_def.param_name == "-test"
        assert param_def.param_aliases == ["-a"]
        assert param_def.all_param_names == ["-test", "-a"]
    
    def test_initialization_with_default_value(self):
        """Test ParameterDefinition initialization with a default value instead of Parameter."""
        param_def = ParameterDefinition(
            name="test",
            type_hint=str,
            param_obj="default"
        )
        
        assert param_def.name == "test"
        assert param_def.type == str
        assert param_def.default == "default"
        assert param_def.position is None
        assert param_def.help_text == ""
        assert param_def.aliases == []
        assert param_def.mandatory is False
    
    @pytest.mark.parametrize("name, type_hint, expected_completer", [
        ("path", Path, True),
        ("opt_path", Optional[Path], True),
        ("flag", bool, True),
        ("text", str, False)
    ])
    def test_setup_completer(self, name, type_hint, expected_completer):
        """Test the _setup_completer method with different types."""
        param_def = ParameterDefinition(
            name=name,
            type_hint=type_hint,
            param_obj=None
        )
        
        if expected_completer:
            assert param_def.completer is not None
        else:
            assert param_def.completer is None
    
    @pytest.mark.parametrize("type_hint, value_str, expected_value", [
        (str, "hello", "hello"),
        (int, "42", 42),
        (bool, "true", True),
        (bool, "false", False),
        (bool, "yes", True),
        (bool, "no", False),
        (List[str], "a,b,c", ["a", "b", "c"])
    ])
    def test_convert_value(self, type_hint, value_str, expected_value):
        """Test the convert_value method with different types."""
        param_def = ParameterDefinition(
            name="test",
            type_hint=type_hint,
            param_obj=None
        )
        
        assert param_def.convert_value(value_str) == expected_value
    
    def test_convert_value_with_default(self):
        """Test convert_value returns default for None or empty string."""
        param = ParameterDefinition(
            name="test",
            type_hint=str,
            param_obj=Parameter(default="default")
        )
        
        assert param.convert_value(None) == "default"
        assert param.convert_value("") == "default"
    
    def test_convert_value_mandatory(self):
        """Test convert_value raises error for mandatory parameter with no value."""
        param = ParameterDefinition(
            name="test",
            type_hint=str,
            param_obj=Parameter(mandatory=True)
        )
        
        with pytest.raises(ValueError, match="Parameter 'test' is mandatory"):
            param.convert_value(None)
    
    def test_convert_value_error(self):
        """Test convert_value raises error for invalid conversion."""
        param = ParameterDefinition(
            name="count",
            type_hint=int,
            param_obj=None
        )
        
        with pytest.raises(ValueError):
            param.convert_value("not_an_int")
    
    def test_get_param_completion(self):
        """Test the get_param_completion method."""
        param = ParameterDefinition(
            name="verbose",
            type_hint=bool,
            param_obj=Parameter(False, help="Verbose mode", aliases=["v"])
        )
        
        # Test completion for the primary parameter name
        completion = param.get_param_completion("-v")
        assert completion is not None
        assert completion.text == "-verbose"
        
        # Test completion for an alias
        completion = param.get_param_completion("-verb")
        assert completion is not None
        assert completion.text == "-verbose"
        
        # Test no completion for non-matching text
        completion = param.get_param_completion("-x")
        assert completion is None


class TestDeclarativeCommand:
    """Test the DeclarativeCommand class."""
    
    def test_get_command_names(self):
        """Test the get_command_names method."""
        assert TestCommand.get_command_names() == ["test-cmd"]
        assert MinimalCommand.get_command_names() == ["minimal"]
    
    def test_get_parameter_definitions(self):
        """Test the get_parameter_definitions method."""
        param_defs = TestCommand.get_parameter_definitions()
        
        assert len(param_defs) == 5
        
        # Check that the mandatory positional parameter comes first
        assert param_defs[0].name == "name"
        assert param_defs[0].position == 0
        assert param_defs[0].mandatory is True
        
        # Find the verbose parameter and check its properties
        verbose_param = next(p for p in param_defs if p.name == "verbose")
        assert verbose_param.type == bool
        assert verbose_param.default is False
        assert verbose_param.param_aliases == ["-v"]
    
    @pytest.mark.parametrize("args_str, expected_attrs", [
        # Basic positional args
        ("test_name", {"name": "test_name", "count": 42, "verbose": False}),
        
        # Named args
        ("-name test_name -count 10 -verbose", {"name": "test_name", "count": 10, "verbose": True}),
        
        # Mixed args
        ("test_name -count 10", {"name": "test_name", "count": 10, "verbose": False}),
        
        # Using aliases
        ("test_name -v", {"name": "test_name", "count": 42, "verbose": True}),
        
        # With quoted arguments
        ("'test name with spaces'", {"name": "test name with spaces", "count": 42}),
        
        # With complex types
        ("test_name -tags a,b,c", {"name": "test_name", "tags": ["a", "b", "c"]}),
    ])
    def test_parse_args(self, args_str, expected_attrs):
        """Test parsing arguments with various formats."""
        cmd = TestCommand.parse(args_str)
        
        # Check each expected attribute
        for attr_name, expected_value in expected_attrs.items():
            assert getattr(cmd, attr_name) == expected_value
    
    def test_parse_errors(self):
        """Test parsing errors."""
        # Unknown parameter
        with pytest.raises(ValueError, match="Unknown parameter"):
            TestCommand.parse("-invalid value")
        
        # Missing mandatory parameter
        with pytest.raises(ValueError, match="Missing required parameter"):
            TestCommand.parse("-count 10")
        
        # Invalid type conversion
        with pytest.raises(ValueError, match="Cannot convert"):
            TestCommand.parse("test_name -count not_an_int")
    
    def test_execute(self, shell_mock):
        """Test the execute method."""
        cmd = TestCommand()
        
        with patch.object(TestCommand, 'parse', return_value=cmd):
            result = cmd.execute("test-cmd", "test_name", shell_mock)
            
            assert result is True
            assert hasattr(cmd, 'executed')
            assert cmd.shell is shell_mock
    
    def test_execute_error(self, shell_mock):
        """Test the execute method with an error."""
        cmd = TestCommand()
        
        with patch.object(TestCommand, 'parse', side_effect=ValueError("Test error")):
            with patch('builtins.print') as mock_print:
                result = cmd.execute("test-cmd", "invalid", shell_mock)
                
                assert result is False
                mock_print.assert_called_with("Error: Test error")
    
    def test_execute_unknown_exception(self, shell_mock):
        """Test the execute method with an unknown exception."""
        cmd = TestCommand()
        
        with patch.object(TestCommand, 'parse', side_effect=Exception("Unknown error")):
            with patch('builtins.print') as mock_print:
                result = cmd.execute("test-cmd", "invalid", shell_mock)
                
                assert result is False
                mock_print.assert_called_with("Error executing command: Unknown error")
    
    @pytest.mark.parametrize("command_class, expected_sections", [
        (TestCommand, ["Test command for unit testing", "Usage: test-cmd <name>", "Positional Parameters:", "Parameters:"]),
        (MinimalCommand, ["A minimal command with defaults.", "Usage: minimal <value>", "Positional Parameters:"]),
        (ParametersTestCommand, ["Command with various parameter types", "Usage: param_test <req_pos>", "Positional Parameters:", "Parameters:"])
    ])
    def test_get_help(self, command_class, expected_sections):
        """Test the get_help method for various commands."""
        cmd = command_class()
        help_text = cmd.get_help()
        
        # Check that each expected section appears in the help text
        for section in expected_sections:
            assert section in help_text
    
    def test_get_completions_empty(self):
        """Test get_completions with empty input."""
        cmd = TestCommand()
        completions = cmd.get_completions("")
        
        # Should suggest parameters and a hint for the positional parameter
        assert len(completions) > 0
        
        # Find the positional parameter hint
        from prompt_toolkit.formatted_text import FormattedText
        formatted_text:List[FormattedText] = [x for x in [c.display for c in completions]]
        suggestions:List[str] = [x[0][1] for x in formatted_text]

        for value in ['<name>','-name','-count','-verbose','-tags','-config_path']:
            assert value in suggestions, f'Missing {value} in suggestions'
    
    def test_get_completions_partial_param(self):
        """Test get_completions with partial parameter name."""
        cmd = TestCommand()
        
        # Test partial parameter name
        completions = cmd.get_completions("-ve")
        assert len(completions) == 1
        assert completions[0].text == "-verbose"
        
        # Test no completions
        completions = cmd.get_completions("-xyz")
        assert len(completions) == 0
    
    def test_get_completions_for_param_value(self):
        """Test get_completions for parameter values."""
        cmd = TestCommand()
        
        # For boolean parameters, should suggest true/false values
        completions = cmd.get_completions("-verbose ")
        assert len(completions) > 0
        
        # For path parameters, should use path completer
        completions = cmd.get_completions("-config_path ")
        assert len(completions) > 0


class TestCompleteWorkflow:
    """Test the complete workflow of command parsing and execution."""
    
    def test_parse_and_execute(self, shell_mock):
        """Test parsing arguments and executing the command."""
        # Create the command directly through parse
        cmd = TestCommand.parse("test_value -count 99 -verbose")
        
        # Execute the command
        result = cmd.execute_command(shell_mock)
        
        # Verify the result and attributes
        assert result is True
        assert cmd.name == "test_value"
        assert cmd.count == 99
        assert cmd.verbose is True
        assert cmd.executed
        assert cmd.shell is shell_mock
    
    @pytest.mark.parametrize("args_str, expected_output", [
        ("required -flag", "flag: True"),
        ("required optional -str_param custom", "str_param: custom"),
        ("required -int_param 99", "int_param: 99")
    ])
    def test_command_output(self, args_str, expected_output, shell_mock):
        """Test command parsing and output."""
        # Create a test command that prints its parameters
        @command(name="print_test")
        class PrintTestCommand(ParametersTestCommand):
            def execute_command(self, shell):
                for param_name in dir(self):
                    if not param_name.startswith('_') and param_name not in ('execute', 'execute_command'):
                        print(f"{param_name}: {getattr(self, param_name)}")
                return True
        
        # Create the command and execute it
        cmd = PrintTestCommand.parse(args_str)
        
        with patch('builtins.print') as mock_print:
            result = cmd.execute_command(shell_mock)
            
            # Check that the expected output was printed
            assert result is True
            for call in mock_print.call_args_list:
                if expected_output in call.args[0]:
                    break
            else:
                pytest.fail(f"Expected output '{expected_output}' not found in printed output")