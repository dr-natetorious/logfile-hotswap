"""
Tests for the BaseCommand class.
"""
import pytest
from unittest.mock import MagicMock

from src.cli.commands.base import BaseCommand

class ConcreteCommand(BaseCommand):
    """Concrete implementation of BaseCommand for testing."""
    
    def get_command_names(self):
        """Return command names for this command."""
        return ["test", "test-alias"]
    
    def execute(self, command_name, args_str, shell):
        """Execute the command."""
        self.last_executed = {
            "command_name": command_name,
            "args_str": args_str,
            "shell": shell
        }
        return True
    
    def get_help(self):
        """Return custom help text."""
        return "Test command help text."

class FailingCommand(BaseCommand):
    """Implementation that fails on execute for testing error handling."""
    
    def get_command_names(self):
        """Return command names for this command."""
        return ["fail"]
    
    def execute(self, command_name, args_str, shell):
        """Execute the command and return False to indicate failure."""
        return False

class TestBaseCommand:
    """Test suite for the BaseCommand class."""
    
    def test_abstract_methods(self):
        """Test that BaseCommand cannot be instantiated directly."""
        with pytest.raises(TypeError):
            BaseCommand()
    
    def test_concrete_instantiation(self):
        """Test that a concrete subclass can be instantiated."""
        cmd = ConcreteCommand()
        assert isinstance(cmd, BaseCommand)
    
    def test_get_command_names(self):
        """Test the get_command_names method."""
        cmd = ConcreteCommand()
        names = cmd.get_command_names()
        assert names == ["test", "test-alias"]
        assert "test" in names
        assert "test-alias" in names
    
    def test_execute(self):
        """Test the execute method."""
        cmd = ConcreteCommand()
        shell = MagicMock()
        
        result = cmd.execute("test", "--flag value", shell)
        
        assert result is True
        assert cmd.last_executed["command_name"] == "test"
        assert cmd.last_executed["args_str"] == "--flag value"
        assert cmd.last_executed["shell"] is shell
    
    def test_execute_failure(self):
        """Test execute method that returns False."""
        cmd = FailingCommand()
        shell = MagicMock()
        
        result = cmd.execute("fail", "", shell)
        
        assert result is False
    
    def test_default_help(self):
        """Test the default help text."""
        # Create a minimal implementation that doesn't override get_help
        class MinimalCommand(BaseCommand):
            def get_command_names(self):
                return ["minimal"]
            
            def execute(self, command_name, args_str, shell):
                return True
        
        cmd = MinimalCommand()
        help_text = cmd.get_help()
        
        assert help_text == "No help available for this command."
    
    def test_custom_help(self):
        """Test overridden help text."""
        cmd = ConcreteCommand()
        help_text = cmd.get_help()
        
        assert help_text == "Test command help text."
    
    def test_parse_args_empty(self):
        """Test parsing empty arguments."""
        cmd = ConcreteCommand()
        
        assert cmd.parse_args("") == []
        assert cmd.parse_args(None) == []
    
    def test_parse_args_simple(self):
        """Test parsing simple arguments."""
        cmd = ConcreteCommand()
        
        args = cmd.parse_args("arg1 arg2 arg3")
        
        assert args == ["arg1", "arg2", "arg3"]
    
    def test_parse_args_with_quotes(self):
        """Test parsing arguments with quotes."""
        cmd = ConcreteCommand()
        
        args = cmd.parse_args('arg1 "argument with spaces" arg3')
        
        assert len(args) == 3
        assert args[0] == "arg1"
        assert args[1] == "argument with spaces"
        assert args[2] == "arg3"
    
    def test_parse_args_with_mixed_quotes(self):
        """Test parsing arguments with mixed quotes."""
        cmd = ConcreteCommand()
        
        args = cmd.parse_args("arg1 'single quoted' \"double quoted\"")
        
        assert len(args) == 3
        assert args[0] == "arg1"
        assert args[1] == "single quoted"
        assert args[2] == "double quoted"
    
    def test_parse_args_with_escaped_characters(self):
        """Test parsing arguments with escaped characters."""
        cmd = ConcreteCommand()
        
        args = cmd.parse_args(r'arg1 escaped\"quote arg3')
        
        assert len(args) == 3
        assert args[0] == "arg1"
        assert args[1] == 'escaped"quote'
        assert args[2] == "arg3"


class TestBaseCommandInheritance:
    """Test suite for ensuring correct inheritance usage."""
    
    def test_must_implement_get_command_names(self):
        """Test that subclasses must implement get_command_names."""
        class MissingGetCommandNames(BaseCommand):
            def execute(self, command_name, args_str, shell):
                return True
                
        with pytest.raises(TypeError):
            MissingGetCommandNames()
    
    def test_must_implement_execute(self):
        """Test that subclasses must implement execute."""
        class MissingExecute(BaseCommand):
            def get_command_names(self):
                return ["missing_execute"]
                
        with pytest.raises(TypeError):
            MissingExecute()