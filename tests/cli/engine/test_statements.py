"""
Tests for the statements module.

This module tests the functionality of the Statement classes and their behavior.
"""
import pytest
from unittest.mock import MagicMock, call
from typing import List, Dict, Any, Type

from engine.statements import (
    Statement,
    CommandStatement,
    SetVariableStatement,
    ForEachStatement,
    TryCatchStatement,
    CodeBlock,
    IfStatement,
    WhileStatement,
    FunctionDefinitionStatement,
    ReturnStatement,
    PipelineStatement
)


class TestExecutorFixture:
    """
    A test fixture that provides a mock executor for testing statements.
    
    This class is used as a base for statement execution tests to provide
    a consistent testing environment.
    """
    
    def setup_method(self):
        """Set up the test fixture."""
        self.executor = MagicMock()
        self.executor.execute_command.return_value = True
        self.executor.set_variable.return_value = "test_value"
        
        # Set up additional executor methods
        self.executor.execute_foreach.return_value = None
        self.executor.execute_try_catch.return_value = None
        self.executor.execute_parallel.return_value = None
        self.executor.execute_if.return_value = None
        self.executor.execute_while.return_value = None
        self.executor.register_function.return_value = None
        self.executor.execute_return.return_value = None
        self.executor.execute_pipeline.return_value = None


class TestCommandStatement(TestExecutorFixture):
    """Tests for the CommandStatement class."""
    
    @pytest.mark.parametrize("command_name,args_str,expected_result", [
        ("help", "", True),
        ("ls", "-la /tmp", True),
        ("complex", "-param1 value -flag -quoted \"test value\"", True),
    ])
    def test_execute(self, command_name, args_str, expected_result):
        """Test that execute() calls the executor's execute_command method."""
        # Arrange
        statement = CommandStatement(command_name, args_str)
        
        # Act
        result = statement.execute(self.executor)
        
        # Assert
        assert result == expected_result
        self.executor.execute_command.assert_called_once_with(command_name, args_str)


class TestSetVariableStatement(TestExecutorFixture):
    """Tests for the SetVariableStatement class."""
    
    @pytest.mark.parametrize("var_name,expression,expected_result", [
        ("x", "5", "test_value"),
        ("complex_var", "2 * 3 + len('test')", "test_value"),
        ("mylist", "[1, 2, 3]", "test_value"),
    ])
    def test_execute(self, var_name, expression, expected_result):
        """Test that execute() calls the executor's set_variable method."""
        # Arrange
        statement = SetVariableStatement(var_name, expression)
        
        # Act
        result = statement.execute(self.executor)
        
        # Assert
        assert result == expected_result
        self.executor.set_variable.assert_called_once_with(var_name, expression)


class TestForEachStatement(TestExecutorFixture):
    """Tests for the ForEachStatement class."""
    
    def test_execute_with_code_block(self):
        """Test execute() with a CodeBlock body."""
        # Arrange
        item_var = "item"
        collection_expr = "[1, 2, 3]"
        body = CodeBlock([
            CommandStatement("print", "$item")
        ])
        statement = ForEachStatement(item_var, collection_expr, body)
        
        # Act
        result = statement.execute(self.executor)
        
        # Assert
        self.executor.execute_foreach.assert_called_once_with(item_var, collection_expr, body)
    
    def test_execute_with_statement_list(self):
        """Test execute() with a list of statements that gets converted to a CodeBlock."""
        # Arrange
        item_var = "item"
        collection_expr = "[1, 2, 3]"
        body_statements = [
            CommandStatement("print", "$item")
        ]
        statement = ForEachStatement(item_var, collection_expr, body_statements)
        
        # Act
        result = statement.execute(self.executor)
        
        # Assert
        assert isinstance(statement.body, CodeBlock)
        self.executor.execute_foreach.assert_called_once()
        # Check that the first arg of the first call is the item_var
        assert self.executor.execute_foreach.call_args[0][0] == item_var


class TestTryCatchStatement(TestExecutorFixture):
    """Tests for the TryCatchStatement class."""
    
    def test_execute(self):
        """Test that execute() calls the executor's execute_try_catch method."""
        # Arrange
        try_block = CodeBlock([
            CommandStatement("risky_command", "")
        ])
        catch_block = CodeBlock([
            CommandStatement("handle_error", "")
        ])
        statement = TryCatchStatement(try_block, catch_block)
        
        # Act
        result = statement.execute(self.executor)
        
        # Assert
        self.executor.execute_try_catch.assert_called_once_with(try_block, catch_block)
    
    def test_post_init_conversion(self):
        """Test that __post_init__ converts lists to CodeBlocks."""
        # Arrange
        try_list = [CommandStatement("risky_command", "")]
        catch_list = [CommandStatement("handle_error", "")]
        
        # Act
        statement = TryCatchStatement(try_list, catch_list)
        
        # Assert
        assert isinstance(statement.try_block, CodeBlock)
        assert isinstance(statement.catch_block, CodeBlock)
        assert len(statement.try_block) == 1
        assert len(statement.catch_block) == 1


class TestCodeBlock(TestExecutorFixture):
    """Tests for the CodeBlock class."""
    
    def test_sequential_execution(self):
        """Test that execute() runs statements sequentially by default."""
        # Arrange
        cmd1 = CommandStatement("cmd1", "")
        cmd2 = CommandStatement("cmd2", "")
        block = CodeBlock([cmd1, cmd2])
        
        # Create separate mock methods for the commands
        cmd1_mock = MagicMock(return_value="result1")
        cmd2_mock = MagicMock(return_value="result2")
        cmd1.execute = cmd1_mock
        cmd2.execute = cmd2_mock
        
        # Act
        result = block.execute(self.executor)
        
        # Assert
        assert result == "result2"  # Last command's result
        cmd1_mock.assert_called_once_with(self.executor)
        cmd2_mock.assert_called_once_with(self.executor)
    
    def test_parallel_execution(self):
        """Test that execute() delegates to execute_parallel for parallel blocks."""
        # Arrange
        cmd1 = CommandStatement("cmd1", "")
        cmd2 = CommandStatement("cmd2", "")
        block = CodeBlock([cmd1, cmd2], block_type="parallel")
        
        # Act
        result = block.execute(self.executor)
        
        # Assert
        self.executor.execute_parallel.assert_called_once_with([cmd1, cmd2])
    
    def test_sequence_protocol(self):
        """Test that CodeBlock implements the Sequence protocol."""
        # Arrange
        cmd1 = CommandStatement("cmd1", "")
        cmd2 = CommandStatement("cmd2", "")
        block = CodeBlock([cmd1, cmd2])
        
        # Act & Assert
        assert len(block) == 2
        assert block[0] == cmd1
        assert block[1] == cmd2
        assert list(block) == [cmd1, cmd2]
        assert cmd1 in block
    
    def test_append_and_extend(self):
        """Test append and extend methods."""
        # Arrange
        block = CodeBlock()
        cmd1 = CommandStatement("cmd1", "")
        cmd2 = CommandStatement("cmd2", "")
        cmd3 = CommandStatement("cmd3", "")
        
        # Act
        block.append(cmd1)
        block.extend([cmd2, cmd3])
        
        # Assert
        assert len(block) == 3
        assert list(block) == [cmd1, cmd2, cmd3]
    
    def test_extend_with_code_block(self):
        """Test extending with another CodeBlock."""
        # Arrange
        block1 = CodeBlock([CommandStatement("cmd1", "")])
        block2 = CodeBlock([CommandStatement("cmd2", "")])
        
        # Act
        block1.extend(block2)
        
        # Assert
        assert len(block1) == 2
        assert block1[1].command_name == "cmd2"
    
    def test_add_operator_with_statement(self):
        """Test the + operator with a Statement."""
        # Arrange
        block = CodeBlock([CommandStatement("cmd1", "")])
        cmd2 = CommandStatement("cmd2", "")
        
        # Act
        result = block + cmd2
        
        # Assert
        assert len(result) == 2
        assert result[0].command_name == "cmd1"
        assert result[1].command_name == "cmd2"
        # Original block should be unchanged
        assert len(block) == 1
    
    def test_add_operator_with_block(self):
        """Test the + operator with another CodeBlock."""
        # Arrange
        block1 = CodeBlock([CommandStatement("cmd1", "")])
        block2 = CodeBlock([CommandStatement("cmd2", "")])
        
        # Act
        result = block1 + block2
        
        # Assert
        assert len(result) == 2
        assert result[0].command_name == "cmd1"
        assert result[1].command_name == "cmd2"
        # Original blocks should be unchanged
        assert len(block1) == 1
        assert len(block2) == 1


class TestStatementCombination:
    """Tests for combining statements."""
    
    def test_statement_addition(self):
        """Test adding two statements to create a CodeBlock."""
        # Arrange
        cmd1 = CommandStatement("cmd1", "")
        cmd2 = CommandStatement("cmd2", "")
        
        # Act
        result = cmd1 + cmd2
        
        # Assert
        assert isinstance(result, CodeBlock)
        assert len(result) == 2
        assert result[0] == cmd1
        assert result[1] == cmd2
    
    def test_radd_with_list(self):
        """Test adding a list of statements to a statement."""
        # Arrange
        cmd1 = CommandStatement("cmd1", "")
        cmd2 = CommandStatement("cmd2", "")
        cmd3 = CommandStatement("cmd3", "")
        
        # Act
        result = [cmd1, cmd2] + cmd3
        
        # Assert
        assert isinstance(result, CodeBlock)
        assert len(result) == 3
        assert result[0] == cmd1
        assert result[1] == cmd2
        assert result[2] == cmd3


class TestIfStatement(TestExecutorFixture):
    """Tests for the IfStatement class."""
    
    def test_execute(self):
        """Test that execute() calls the executor's execute_if method."""
        # Arrange
        conditions = ["x > 5", "x < 10"]
        blocks = [
            CodeBlock([CommandStatement("then_cmd", "")]),
            CodeBlock([CommandStatement("elif_cmd", "")])
        ]
        else_block = CodeBlock([CommandStatement("else_cmd", "")])
        statement = IfStatement(conditions, blocks, else_block)
        
        # Act
        result = statement.execute(self.executor)
        
        # Assert
        self.executor.execute_if.assert_called_once_with(conditions, blocks, else_block)


class TestWhileStatement(TestExecutorFixture):
    """Tests for the WhileStatement class."""
    
    def test_execute(self):
        """Test that execute() calls the executor's execute_while method."""
        # Arrange
        condition = "x < 10"
        body = CodeBlock([CommandStatement("loop_cmd", "")])
        statement = WhileStatement(condition, body)
        
        # Act
        result = statement.execute(self.executor)
        
        # Assert
        self.executor.execute_while.assert_called_once_with(condition, body)


class TestFunctionDefinitionStatement(TestExecutorFixture):
    """Tests for the FunctionDefinitionStatement class."""
    
    def test_execute(self):
        """Test that execute() calls the executor's register_function method."""
        # Arrange
        name = "test_func"
        parameters = [("param1", None), ("param2", "default")]
        body = CodeBlock([CommandStatement("func_cmd", "")])
        statement = FunctionDefinitionStatement(name, parameters, body)
        
        # Act
        result = statement.execute(self.executor)
        
        # Assert
        self.executor.register_function.assert_called_once_with(name, parameters, body)


class TestReturnStatement(TestExecutorFixture):
    """Tests for the ReturnStatement class."""
    
    def test_execute(self):
        """Test that execute() calls the executor's execute_return method."""
        # Arrange
        expression = "x + 5"
        statement = ReturnStatement(expression)
        
        # Act
        result = statement.execute(self.executor)
        
        # Assert
        self.executor.execute_return.assert_called_once_with(expression)
    
    def test_execute_no_expression(self):
        """Test execute() with no expression."""
        # Arrange
        statement = ReturnStatement()
        
        # Act
        result = statement.execute(self.executor)
        
        # Assert
        self.executor.execute_return.assert_called_once_with(None)


class TestPipelineStatement(TestExecutorFixture):
    """Tests for the PipelineStatement class."""
    
    def test_execute(self):
        """Test that execute() calls the executor's execute_pipeline method."""
        # Arrange
        commands = [
            CommandStatement("cmd1", ""),
            CommandStatement("cmd2", ""),
            CommandStatement("cmd3", "")
        ]
        statement = PipelineStatement(commands)
        
        # Act
        result = statement.execute(self.executor)
        
        # Assert
        self.executor.execute_pipeline.assert_called_once_with(commands)