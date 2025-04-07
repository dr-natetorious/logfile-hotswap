"""
Tests for the declarative command system.
"""
import pytest
from unittest.mock import MagicMock, patch
from typing import Optional, List, Union
from pathlib import Path

from src.cli.commands.declarative import (
    command,
    Parameter,
    CommandRegistry,
    ParameterDefinition,
    DeclarativeCommand
)


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


class FailingCommand(DeclarativeCommand):
    """A command that is not decorated with @command."""
    
    def execute_command(self, shell) -> bool:
        """Execute the command."""
        return True


class TestCommandDecorator:
    """Test the @command decorator functionality."""
    
    def test_command_decorator_with_name(self):
        """Test the command decorator with explicit name."""
        assert TestCommand._command_name == "test-cmd"
        assert "test-cmd" in CommandRegistry.get_all_commands()
        assert CommandRegistry.get_command("test-cmd") == TestCommand
    
    def test_command_decorator_with_default_name(self):
        """Test the command decorator with default name."""
        assert MinimalCommand._command_name == "minimal"
        assert "minimal" in CommandRegistry.get_all_commands()
        assert CommandRegistry.get_command("minimal") == MinimalCommand
    
    def test_command_decorator_with_description(self):
        """Test the command decorator with explicit description."""
        assert TestCommand._command_description == "Test command for unit testing"
    
    def test_command_decorator_with_default_description(self):
        """Test the command decorator with default description."""
        assert MinimalCommand._command_description == "A minimal command with defaults."


class TestParameter:
    """Test the Parameter class."""
    
    def test_parameter_initialization(self):
        """Test Parameter initialization with various options."""
        # Test with all parameters specified
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


class TestParameterDefinition:
    """Test the ParameterDefinition class."""
    
    def test_initialization(self):
        """Test ParameterDefinition initialization."""
        # Create a Parameter object
        param_obj = Parameter(
            default="default",
            position=1,
            mandatory=True,
            help="Help text",
            aliases=["a"]
        )
        
        # Create a ParameterDefinition with the Parameter object
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
    
    def test_setup_completer(self):
        """Test the _setup_completer method."""
        # Test with Path type
        path_param = ParameterDefinition(
            name="path",
            type_hint=Path,
            param_obj=None
        )
        assert path_param.completer is not None
        
        # Test with Optional[Path] type
        optional_path_param = ParameterDefinition(
            name="opt_path",
            type_hint=Optional[Path],
            param_obj=None
        )
        assert optional_path_param.completer is not None
        
        # Test with bool type
        bool_param = ParameterDefinition(
            name="flag",
            type_hint=bool,
            param_obj=False
        )
        assert bool_param.completer is not None
        
        # Test with str type (should not have a specific completer)
        str_param = ParameterDefinition(
            name="text",
            type_hint=str,
            param_obj=None
        )
        assert str_param.completer is None
    
    def test_convert_value(self):
        """Test the convert_value method."""
        # String parameter
        str_param = ParameterDefinition(
            name="text",
            type_hint=str,
            param_obj=None
        )
        assert str_param.convert_value("hello") == "hello"
        
        # Integer parameter
        int_param = ParameterDefinition(
            name="count",
            type_hint=int,
            param_obj=0
        )
        assert int_param.convert_value("42") == 42
        
        # Boolean parameter
        bool_param = ParameterDefinition(
            name="flag",
            type_hint=bool,
            param_obj=False
        )
        assert bool_param.convert_value("true") is True
        #assert bool_param.convert_value("") is True  # Empty string for flags becomes True
        
        # List parameter
        list_param = ParameterDefinition(
            name="tags",
            type_hint=List[str],
            param_obj=[]
        )
        assert list_param.convert_value("a,b,c") == ["a", "b", "c"]
    
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
    
    def test_parse_positional_args(self):
        """Test parsing positional arguments."""
        cmd = TestCommand.parse("test_name")
        
        assert cmd.name == "test_name"
        assert cmd.count == 42  # Default value
        assert cmd.verbose is False  # Default value
        assert cmd.tags == []  # Default value
        assert cmd.config_path is None  # Default value
    
    def test_parse_named_args(self):
        """Test parsing named arguments."""
        cmd = TestCommand.parse("-name test_name -count 10 -verbose -tags a,b,c")
        
        assert cmd.name == "test_name"
        assert cmd.count == 10
        assert cmd.verbose is True
        assert cmd.tags == ["a", "b", "c"]
        assert cmd.config_path is None  # Default value
    
    def test_parse_mixed_args(self):
        """Test parsing mixed positional and named arguments."""
        cmd = TestCommand.parse("test_name -count 10")
        
        assert cmd.name == "test_name"
        assert cmd.count == 10
        assert cmd.verbose is False  # Default value
    
    def test_parse_with_aliases(self):
        """Test parsing arguments with aliases."""
        cmd = TestCommand.parse("test_name -v")
        
        assert cmd.name == "test_name"
        assert cmd.verbose is True
    
    def test_parse_quoted_args(self):
        """Test parsing arguments with quotes."""
        cmd = TestCommand.parse('test_name -count 10 -tags "a,b with space,c"')
        
        assert cmd.name == "test_name"
        assert cmd.count == 10
        assert cmd.tags == ["a", "b with space", "c"]
    
    def test_parse_invalid_args(self):
        """Test parsing invalid arguments."""
        with pytest.raises(ValueError, match="Unknown parameter"):
            TestCommand.parse("-invalid value")
    
    def test_parse_missing_mandatory(self):
        """Test parsing with missing mandatory parameter."""
        with pytest.raises(ValueError, match="Missing required parameter"):
            TestCommand.parse("-count 10")
    
    def test_parse_invalid_type(self):
        """Test parsing with invalid type conversion."""
        with pytest.raises(ValueError, match="Cannot convert"):
            TestCommand.parse("test_name -count not_an_int")
    
    def test_execute(self):
        """Test the execute method."""
        cmd = TestCommand()
        shell = MagicMock()
        
        with patch.object(TestCommand, 'parse', return_value=cmd):
            result = cmd.execute("test-cmd", "test_name", shell)
            
            assert result is True
            assert hasattr(cmd, 'executed')
            assert cmd.shell is shell
    
    def test_execute_error(self):
        """Test the execute method with an error."""
        cmd = TestCommand()
        shell = MagicMock()
        
        with patch.object(TestCommand, 'parse', side_effect=ValueError("Test error")):
            with patch('builtins.print') as mock_print:
                result = cmd.execute("test-cmd", "invalid", shell)
                
                assert result is False
                mock_print.assert_called_with("Error: Test error")
    
    def test_get_help(self):
        """Test the get_help method."""
        cmd = TestCommand()
        help_text = cmd.get_help()
        
        # Check that help text contains key elements
        assert "Test command for unit testing" in help_text
        assert "Usage: test-cmd <name>" in help_text
        assert "Positional Parameters:" in help_text
        assert "Parameters:" in help_text
        assert "-verbose, -v <bool>" in help_text
        assert "-count <int>" in help_text
    
    def test_minimal_help(self):
        """Test the get_help method for a minimal command."""
        cmd = MinimalCommand()
        help_text = cmd.get_help()
        
        assert "A minimal command with defaults." in help_text
        assert "Usage: minimal <value>" in help_text
    
    def test_get_completions(self):
        """Test the get_completions method."""
        cmd = TestCommand()
        
        # Test empty input (should suggest all parameters)
        completions = cmd.get_completions("")
        assert len(completions) > 0
        
        # Test partial parameter name
        completions = cmd.get_completions("-ve")
        assert len(completions) == 1
        assert completions[0].text == "-verbose"
        
        # Test no completions
        completions = cmd.get_completions("-xyz")
        assert len(completions) == 0