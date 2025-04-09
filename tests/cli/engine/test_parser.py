"""
Tests for the parser module.

This module tests the tokenization and parsing functionality of the shell scripting language.
"""
import pytest
from typing import List, Dict, Any, Type, Tuple

from engine.parser import (
    TokenType,
    Token,
    Lexer,
    Parser,
    parse_script,
    parse_line
)
from engine.statements import (
    CommandStatement,
    SetVariableStatement,
    ForEachStatement,
    CodeBlock,
    TryCatchStatement
)


class TestLexer:
    """Tests for the Lexer class."""
    
    @pytest.mark.parametrize("input_text,expected_token_types", [
        (
            "command",
            [TokenType.COMMAND]
        ),
        (
            "command -flag",
            [TokenType.COMMAND, TokenType.PARAMETER]
        ),
        (
            "$variable = 123",
            [TokenType.VARIABLE, TokenType.ASSIGNMENT, TokenType.NUMBER]
        ),
        (
            'command "string value"',
            [TokenType.COMMAND, TokenType.STRING]
        ),
        (
            "command # comment",
            [TokenType.COMMAND, TokenType.COMMENT]  # Comment should be recognized
        ),
        (
            "foreach:",  # Using a keyword
            [TokenType.KEYWORD, TokenType.COLON]
        ),
    ])
    def test_tokenize_basic(self, input_text, expected_token_types):
        """Test basic tokenization of different inputs."""
        # Arrange
        lexer = Lexer(input_text)
        
        # Act
        tokens = lexer.tokenize()
        
        # Filter out EOF for easier comparison
        tokens = [t for t in tokens if t.type != TokenType.EOF]
        
        # Assert
        assert len(tokens) == len(expected_token_types)
        for i, expected_type in enumerate(expected_token_types):
            assert tokens[i].type == expected_type, f"Token {i} should be {expected_type.name} but was {tokens[i].type.name}"
    
    def test_tokenize_indentation(self):
        """Test handling of indentation."""
        # Arrange
        input_text = """foreach:
    command1
    command2
other_command"""
        
        # Act
        lexer = Lexer(input_text)
        tokens = lexer.tokenize()
        
        # Extract just the token types for easier comparison
        token_types = [token.type for token in tokens if token.type != TokenType.EOF]
        
        # Assert
        expected_types = [
            TokenType.KEYWORD,
            TokenType.COLON,
            TokenType.NEWLINE,
            TokenType.INDENT,
            TokenType.COMMAND,
            TokenType.NEWLINE,
            TokenType.COMMAND,
            TokenType.NEWLINE,
            TokenType.DEDENT,
            TokenType.COMMAND
        ]
        assert token_types == expected_types
    
    def test_tokenize_complex_indentation(self):
        """Test handling of complex indentation patterns."""
        # Arrange
        input_text = """if $condition:
    command1
    if $nested:
        nested_command
    command2
command3"""
        
        # Act
        lexer = Lexer(input_text)
        tokens = lexer.tokenize()
        
        # Extract just the token types for easier comparison
        token_types = [token.type for token in tokens if token.type != TokenType.EOF]
        
        # Assert
        expected_types = [
            TokenType.KEYWORD,  # if
            TokenType.VARIABLE,  # $condition
            TokenType.COLON,
            TokenType.NEWLINE,
            TokenType.INDENT,
            TokenType.COMMAND,  # command1
            TokenType.NEWLINE,
            TokenType.KEYWORD,  # if
            TokenType.VARIABLE,  # $nested
            TokenType.COLON,
            TokenType.NEWLINE,
            TokenType.INDENT,
            TokenType.COMMAND,  # nested_command
            TokenType.NEWLINE,
            TokenType.DEDENT,
            TokenType.COMMAND,  # command2
            TokenType.NEWLINE,
            TokenType.DEDENT,
            TokenType.COMMAND,  # command3
        ]
        assert token_types == expected_types
    
    def test_tokenize_string_literals(self):
        """Test tokenization of string literals with escape sequences."""
        # Arrange
        input_text = 'command "string with \\"quotes\\"" \'another string\''
        
        # Act
        lexer = Lexer(input_text)
        tokens = lexer.tokenize()
        
        # Filter out EOF
        tokens = [t for t in tokens if t.type != TokenType.EOF]
        
        # Assert
        assert len(tokens) == 3
        assert tokens[0].type == TokenType.COMMAND
        assert tokens[1].type == TokenType.STRING
        assert tokens[2].type == TokenType.STRING
        
        # Check that escape sequences were processed correctly
        assert tokens[1].value == 'string with "quotes"'
    
    def test_tokenize_expression(self):
        """Test tokenization of expressions with operators."""
        # Arrange
        input_text = '$result = 2 * (3 + 4)'
        
        # Act
        lexer = Lexer(input_text)
        tokens = lexer.tokenize()
        
        # Extract token types for comparison
        token_types = [token.type for token in tokens if token.type != TokenType.EOF]
        
        # Assert
        expected_types = [
            TokenType.VARIABLE,      # $result
            TokenType.ASSIGNMENT,    # =
            TokenType.NUMBER,        # 2
            TokenType.OPERATOR,      # *
            TokenType.LEFT_PAREN,    # (
            TokenType.NUMBER,        # 3
            TokenType.OPERATOR,      # +
            TokenType.NUMBER,        # 4
            TokenType.RIGHT_PAREN    # )
        ]
        assert token_types == expected_types
    
    def test_tokenize_comment_line(self):
        """Test tokenization of a line with just a comment."""
        # Arrange
        input_text = "# This is a comment"
        
        # Act
        lexer = Lexer(input_text)
        tokens = lexer.tokenize()
        
        # Filter out EOF
        tokens = [t for t in tokens if t.type != TokenType.EOF]
        
        # Assert
        assert len(tokens) == 1
        assert tokens[0].type == TokenType.COMMENT
        assert tokens[0].value == "# This is a comment"
    
    def test_invalid_syntax(self):
        """Test that invalid syntax raises an error."""
        # Arrange
        input_text = "command @invalid"
        
        # Act & Assert
        with pytest.raises(ValueError) as excinfo:
            lexer = Lexer(input_text)
            tokens = lexer.tokenize()
        
        assert "Invalid syntax" in str(excinfo.value)


class TestParser:
    """Tests for the Parser class."""
    
    def test_parse_command(self):
        """Test parsing a simple command."""
        # Arrange
        input_text = "command -param value"
        
        # Act
        result = parse_line(input_text)
        
        # Assert
        assert isinstance(result, CommandStatement)
        assert result.command_name == "command"
        assert result.args_str == "-param value"
    
    def test_parse_variable_assignment(self):
        """Test parsing a variable assignment."""
        # Arrange
        input_text = "$variable = 123"
        
        # Act
        result = parse_line(input_text)
        
        # Assert
        assert isinstance(result, SetVariableStatement)
        assert result.variable_name == "variable"
        assert result.expression == "123"
    
    def test_parse_indented_block(self):
        """Test parsing an indented block with a keyword introducer."""
        # Arrange
        input_text = """parallel:
    command1 -param1
    command2 -param2"""
        
        # Act
        result = parse_script(input_text)
        
        # Assert
        assert isinstance(result, CodeBlock)
        assert len(result) == 1  # One block statement
        
        block = result[0]
        assert isinstance(block, CodeBlock)
        assert block.block_type == "parallel"
        assert len(block) == 2  # Two commands in the block
        
        assert isinstance(block[0], CommandStatement)
        assert block[0].command_name == "command1"
        assert block[0].args_str == "-param1"
        
        assert isinstance(block[1], CommandStatement)
        assert block[1].command_name == "command2"
        assert block[1].args_str == "-param2"
    
    def test_parse_foreach(self):
        """Test parsing a foreach loop."""
        # Arrange
        input_text = """foreach $item in [1, 2, 3]:
    process -item $item
    log -message "Processed $item" """
        
        # Act
        result = parse_script(input_text)
        
        # Assert
        assert isinstance(result, CodeBlock)
        assert len(result) == 1
        
        foreach_stmt = result[0]
        assert isinstance(foreach_stmt, ForEachStatement)
        assert foreach_stmt.item_var == "item"
        assert foreach_stmt.collection_expr == "[1, 2, 3]"
        assert isinstance(foreach_stmt.body, CodeBlock)
        assert len(foreach_stmt.body) == 2
    
    def test_parse_try_catch(self):
        """Test parsing a try-catch block."""
        # Arrange
        input_text = """try:
    risky_command
catch:
    handle_error"""
        
        # Act
        result = parse_script(input_text)
        
        # Assert
        assert isinstance(result, CodeBlock)
        assert len(result) == 1
        
        try_catch = result[0]
        assert isinstance(try_catch, TryCatchStatement)
        assert isinstance(try_catch.try_block, CodeBlock)
        assert isinstance(try_catch.catch_block, CodeBlock)
        assert len(try_catch.try_block) == 1
        assert len(try_catch.catch_block) == 1
    
    def test_parse_multiple_statements(self):
        """Test parsing multiple statements in sequence."""
        # Arrange
        input_text = """command1
$var = 123
command2 -param value"""
        
        # Act
        result = parse_script(input_text)
        
        # Assert
        assert isinstance(result, CodeBlock)
        assert len(result) == 3
        
        assert isinstance(result[0], CommandStatement)
        assert result[0].command_name == "command1"
        
        assert isinstance(result[1], SetVariableStatement)
        assert result[1].variable_name == "var"
        
        assert isinstance(result[2], CommandStatement)
        assert result[2].command_name == "command2"
    
    def test_parse_nested_blocks(self):
        """Test parsing nested blocks."""
        # Arrange
        input_text = """parallel:
    command1
    foreach $item in $items:
        process -item $item
    command2"""
        
        # Act
        result = parse_script(input_text)
        
        # Assert
        assert isinstance(result, CodeBlock)
        assert len(result) == 1
        
        parallel_block = result[0]
        assert isinstance(parallel_block, CodeBlock)
        assert parallel_block.block_type == "parallel"
        assert len(parallel_block) == 3
        
        # Second item should be a foreach
        foreach_stmt = parallel_block[1]
        assert isinstance(foreach_stmt, ForEachStatement)
        assert foreach_stmt.item_var == "item"
        assert foreach_stmt.collection_expr == "$items"
    
    def test_parse_quoted_arguments(self):
        """Test parsing commands with quoted arguments."""
        # Arrange
        input_text = 'command -param "value with spaces" -flag'
        
        # Act
        result = parse_line(input_text)
        
        # Assert
        assert isinstance(result, CommandStatement)
        assert result.command_name == "command"
        assert '-param "value with spaces" -flag' in result.args_str
    
    def test_parse_comments_in_code(self):
        """Test parsing code with comments."""
        # Arrange
        input_text = """command1 # This command does something
command2 # Another comment"""
        
        # Act
        result = parse_script(input_text)
        
        # Assert
        assert isinstance(result, CodeBlock)
        assert len(result) == 2
        assert isinstance(result[0], CommandStatement)
        assert result[0].command_name == "command1"
        assert isinstance(result[1], CommandStatement)
        assert result[1].command_name == "command2"


class TestIntegrationScenarios:
    """Integration tests for more complex parsing scenarios."""
    
    def test_real_world_script(self):
        """Test parsing a realistic script with multiple constructs."""
        # Arrange
        script = """# Initialize variables
$hosts = ["server1", "server2", "server3"]
$timeout = 30

# Main processing block
parallel:
    foreach $host in $hosts:
        try:
            connect-host -name $host -timeout $timeout
            run-command -host $host -cmd "uptime"
        catch:
            log-error -message "Failed to connect to $host"
    
    # Monitor overall progress
    monitor-progress -hosts $hosts

# Final status report
generate-report -title "Connection Results"
"""
        
        # Act
        result = parse_script(script)
        
        # Assert
        assert isinstance(result, CodeBlock)
        # Should have 4 top-level statements: 2 variable assignments, 1 parallel block, 1 command
        assert len(result) == 4
        
        # Check variable assignments
        assert isinstance(result[0], SetVariableStatement)
        assert result[0].variable_name == "hosts"
        
        assert isinstance(result[1], SetVariableStatement)
        assert result[1].variable_name == "timeout"
        
        # Check parallel block
        parallel_block = result[2]
        assert isinstance(parallel_block, CodeBlock)
        assert parallel_block.block_type == "parallel"
        assert len(parallel_block) == 2  # foreach and monitor-progress
        
        # Check foreach in parallel block
        foreach_stmt = parallel_block[0]
        assert isinstance(foreach_stmt, ForEachStatement)
        assert foreach_stmt.item_var == "host"
        assert isinstance(foreach_stmt.body, CodeBlock)
        
        # Check try-catch in foreach
        try_catch = foreach_stmt.body[0]
        assert isinstance(try_catch, TryCatchStatement)
        
        # Check final command
        assert isinstance(result[3], CommandStatement)
        assert result[3].command_name == "generate-report"
    
    def test_script_with_expressions(self):
        """Test parsing a script with complex expressions."""
        # Arrange
        script = """$result = 2 * (3 + 4) # Calculate a value
$array = [1, 2, 3, 4, 5]
$filtered = $array.filter(x => x > 2)  # PowerShell-like syntax

process -value $result -items $filtered
"""
        
        # Act
        result = parse_script(script)
        
        # Assert
        assert isinstance(result, CodeBlock)
        assert len(result) == 4
        
        # Check expressions in variable assignments
        assert isinstance(result[0], SetVariableStatement)
        assert result[0].variable_name == "result"
        assert "2 * (3 + 4)" in result[0].expression
        
        assert isinstance(result[1], SetVariableStatement)
        assert result[1].variable_name == "array"
        assert "[1, 2, 3, 4, 5]" in result[1].expression
        
        assert isinstance(result[2], SetVariableStatement)
        assert result[2].variable_name == "filtered"
        
        # Check command with variables
        assert isinstance(result[3], CommandStatement)
        assert result[3].command_name == "process"
        assert "-value $result -items $filtered" in result[3].args_str