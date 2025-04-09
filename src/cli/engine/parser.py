"""
Parser for the shell scripting language.

This module provides the tokenization and parsing functionality
to convert shell script text into executable Statement objects.
"""
import re
import ast
import shlex
from enum import Enum, auto
from dataclasses import dataclass, field
from typing import List, Dict, Any, Optional, Union, Tuple, Iterable, Iterator

from .statements import (
    Statement, 
    CommandStatement, 
    SetVariableStatement, 
    ForEachStatement, 
    TryCatchStatement, 
    CodeBlock
)


class TokenType(Enum):
    """Token types for the lexical analyzer."""
    COMMAND = auto()           # Command name
    PARAMETER = auto()         # Command parameter (starts with -)
    VARIABLE = auto()          # Variable reference ($name)
    ASSIGNMENT = auto()        # Assignment operator (=)
    STRING = auto()            # String literal
    NUMBER = auto()            # Numeric literal
    WHITESPACE = auto()        # Whitespace
    NEWLINE = auto()           # Newline
    COLON = auto()             # Colon (:)
    SEMICOLON = auto()         # Semicolon (;)
    PIPE = auto()              # Pipe (|)
    LEFT_BRACKET = auto()      # Left bracket ([)
    RIGHT_BRACKET = auto()     # Right bracket (])
    LEFT_PAREN = auto()        # Left parenthesis (()
    RIGHT_PAREN = auto()       # Right parenthesis ())
    COMMA = auto()             # Comma (,)
    DOT = auto()               # Dot (.)
    KEYWORD = auto()           # Language keyword
    IDENTIFIER = auto()        # Identifier
    OPERATOR = auto()          # Operator like +, -, *, /, etc.
    INDENT = auto()            # Indentation increase
    DEDENT = auto()            # Indentation decrease
    COMMENT = auto()           # Comment (# ...)
    EOF = auto()               # End of file/input


@dataclass
class Token:
    """Represents a token in the script language."""
    type: TokenType
    value: str
    line: int
    column: int
    
    def __str__(self) -> str:
        return f"{self.type.name}({repr(self.value)}) at line {self.line}, col {self.column}"


class Lexer:
    """
    Lexical analyzer that converts script text into tokens.
    
    This lexer is indentation-aware, similar to Python, and converts
    indentation changes into INDENT and DEDENT tokens.
    """
    
    # Language keywords
    KEYWORDS = {
        'foreach', 'in', 'if', 'else', 'elseif', 'try', 'catch', 'finally',
        'while', 'for', 'parallel', 'function', 'return', 'break', 'continue'
    }

    # Operators
    OPERATORS = {'+', '-', '*', '/', '%', '==', '!=', '<', '>', '<=', '>=', '&&', '||', '!'}
    
    def __init__(self, text: str):
        """
        Initialize the lexer with input text.
        
        Args:
            text: The script text to tokenize
        """
        self.text = text
        self.pos = 0
        self.line = 1
        self.column = 1
        self.tokens = []
        self.indent_stack = [0]  # Stack of indentation levels
        
        # Regular expressions for token patterns
        self.patterns = [
            # Variable assignment or reference
            (r'\$([a-zA-Z_][a-zA-Z0-9_]*)', self._variable_token),
            
            # Command parameter (e.g., -name)
            (r'-([a-zA-Z][a-zA-Z0-9_]*)', lambda m: Token(TokenType.PARAMETER, m.group(0), self.line, self.column)),
            
            # String literals
            (r'"([^"\\]*(\\.[^"\\]*)*)"', self._string_token),
            (r"'([^'\\]*(\\.[^'\\]*)*)'", self._string_token),
            
            # Numbers
            (r'\d+\.\d+', lambda m: Token(TokenType.NUMBER, float(m.group(0)), self.line, self.column)),
            (r'\d+', lambda m: Token(TokenType.NUMBER, int(m.group(0)), self.line, self.column)),
            
            # Comments - capture the whole comment
            (r'#[^\n]*', lambda m: Token(TokenType.COMMENT, m.group(0), self.line, self.column)),
            
            # Operators and delimiters
            (r'=', lambda m: Token(TokenType.ASSIGNMENT, '=', self.line, self.column)),
            (r':', lambda m: Token(TokenType.COLON, ':', self.line, self.column)),
            (r';', lambda m: Token(TokenType.SEMICOLON, ';', self.line, self.column)),
            (r'\|', lambda m: Token(TokenType.PIPE, '|', self.line, self.column)),
            (r'\[', lambda m: Token(TokenType.LEFT_BRACKET, '[', self.line, self.column)),
            (r'\]', lambda m: Token(TokenType.RIGHT_BRACKET, ']', self.line, self.column)),
            (r'\(', lambda m: Token(TokenType.LEFT_PAREN, '(', self.line, self.column)),
            (r'\)', lambda m: Token(TokenType.RIGHT_PAREN, ')', self.line, self.column)),
            (r',', lambda m: Token(TokenType.COMMA, ',', self.line, self.column)),
            (r'\.', lambda m: Token(TokenType.DOT, '.', self.line, self.column)),
            
            # Operators
            (r'[+\-*/%<>=!&|]+', self._operator_token),
            
            # Whitespace
            (r'[ \t]+', lambda m: Token(TokenType.WHITESPACE, m.group(0), self.line, self.column)),
            
            # Newline (for indentation processing)
            (r'\n', self._newline_token),
            
            # Identifiers and keywords (must be last to not override others)
            (r'[a-zA-Z_][a-zA-Z0-9_\-]*', self._identifier_or_keyword_token),
        ]
    
    def _variable_token(self, match):
        """Create a variable token."""
        var_name = match.group(1)
        return Token(TokenType.VARIABLE, var_name, self.line, self.column)
    
    def _string_token(self, match):
        """Create a string literal token."""
        # Extract the string including quotes
        full_str = match.group(0)
        # Process the string value (remove quotes and handle escapes)
        try:
            value = ast.literal_eval(full_str)
        except (SyntaxError, ValueError):
            # Fallback if ast.literal_eval fails
            value = full_str[1:-1].replace('\\"', '"').replace("\\'", "'")
        return Token(TokenType.STRING, value, self.line, self.column)
    
    def _operator_token(self, match):
        """Create an operator token."""
        op = match.group(0)
        return Token(TokenType.OPERATOR, op, self.line, self.column)
    
    def _newline_token(self, match):
        """Handle newline and process indentation on the next line."""
        self.line += 1
        self.column = 1
        return Token(TokenType.NEWLINE, '\n', self.line-1, self.column)
    
    def _identifier_or_keyword_token(self, match):
        """Determine if an identifier is a keyword or command/identifier."""
        value = match.group(0)
        if value in self.KEYWORDS:
            return Token(TokenType.KEYWORD, value, self.line, self.column)
        else:
            # First word on a line after whitespace/start is treated as a command
            if (not self.tokens or 
                self.tokens[-1].type in (TokenType.NEWLINE, TokenType.INDENT) or
                (len(self.tokens) >= 2 and 
                 self.tokens[-1].type == TokenType.WHITESPACE and 
                 self.tokens[-2].type in (TokenType.NEWLINE, TokenType.INDENT))):
                return Token(TokenType.COMMAND, value, self.line, self.column)
            else:
                return Token(TokenType.IDENTIFIER, value, self.line, self.column)
    
    def _process_indentation(self, line: str) -> List[Token]:
        """
        Process indentation at the start of a line.
        
        Args:
            line: The current line text
            
        Returns:
            List of INDENT/DEDENT tokens to insert
        """
        # Count spaces at the beginning of the line
        indent_size = len(line) - len(line.lstrip())
        current_indent = self.indent_stack[-1]
        
        if indent_size > current_indent:
            # Indentation increased
            self.indent_stack.append(indent_size)
            return [Token(TokenType.INDENT, ' ' * indent_size, self.line, 1)]
        elif indent_size < current_indent:
            # Indentation decreased, may need multiple DEDENT tokens
            tokens = []
            while indent_size < self.indent_stack[-1]:
                self.indent_stack.pop()
                tokens.append(Token(TokenType.DEDENT, '', self.line, 1))
                
                # If we dedent to a level not previously seen, it's an error
                if indent_size > self.indent_stack[-1]:
                    raise ValueError(f"Invalid dedent at line {self.line}")
            
            return tokens
        
        # Same indentation level
        return []
    
    def tokenize(self) -> List[Token]:
        """
        Tokenize the input text.
        
        Returns:
            List of Token objects
        
        Raises:
            ValueError: If there's a lexical error in the input
        """
        # Split the input into lines for indentation processing
        lines = self.text.splitlines(True)  # Keep the newlines
        result = []
        
        for i, line in enumerate(lines):
            # Skip empty lines
            if not line.strip():
                self.line += 1
                continue
                
            # Handle comments for the entire line
            if line.strip().startswith('#'):
                # Add a comment token but don't process further
                result.append(Token(TokenType.COMMENT, line.strip(), self.line, 1))
                self.line += 1
                continue
            
            # Process indentation
            indent_tokens = self._process_indentation(line)
            result.extend(indent_tokens)
            
            # Tokenize the rest of the line
            pos = len(line) - len(line.lstrip())  # Skip the indentation
            self.column = pos + 1  # 1-based column indexing
            
            while pos < len(line):
                # Skip if we've reached a comment
                if pos < len(line) and line[pos] == '#':
                    # Add a comment token
                    comment = line[pos:].rstrip('\n')
                    result.append(Token(TokenType.COMMENT, comment, self.line, self.column))
                    break
                
                # Try to match a token pattern
                matched = False
                
                for pattern, token_func in self.patterns:
                    regex = re.compile(pattern)
                    match = regex.match(line[pos:])
                    
                    if match:
                        token = token_func(match)
                        
                        # Store all tokens for context, but filter whitespace from final result
                        self.tokens.append(token)
                        if token.type != TokenType.WHITESPACE:
                            result.append(token)
                        
                        # Update position and column
                        advance = match.end()
                        pos += advance
                        self.column += advance
                        matched = True
                        break
                
                if not matched:
                    # No pattern matched, this is an error
                    raise ValueError(f"Invalid syntax at line {self.line}, column {self.column}: '{line[pos]}'")
            
            self.line += 1
            self.column = 1
        
        # Make sure the last line has a newline for consistent processing
        if lines and not lines[-1].endswith('\n'):
            result.append(Token(TokenType.NEWLINE, '\n', self.line - 1, self.column))
        
        # Add any remaining DEDENT tokens at the end
        while len(self.indent_stack) > 1:
            self.indent_stack.pop()
            result.append(Token(TokenType.DEDENT, '', self.line, 1))
        
        # Add EOF token
        result.append(Token(TokenType.EOF, '', self.line, 1))
        
        return result


class Parser:
    """
    Parser that converts tokens into Statement objects.
    
    This parser uses recursive descent to parse the token stream.
    """
    
    def __init__(self, tokens: List[Token]):
        """
        Initialize the parser with tokens.
        
        Args:
            tokens: List of tokens from the lexer
        """
        # Filter out comments from the token stream
        self.tokens = [token for token in tokens if token.type != TokenType.COMMENT]
        self.pos = 0
    
    def _peek(self) -> Optional[Token]:
        """Get the current token without advancing."""
        if self.pos < len(self.tokens):
            return self.tokens[self.pos]
        return None
    
    def _advance(self) -> Optional[Token]:
        """Get the current token and advance to the next one."""
        token = self._peek()
        if token:
            self.pos += 1
        return token
    
    def _match(self, token_type: TokenType) -> Optional[Token]:
        """
        Match and consume a token of the specified type.
        
        Args:
            token_type: The expected token type
            
        Returns:
            The matched token or None if no match
        """
        token = self._peek()
        if token and token.type == token_type:
            return self._advance()
        return None
    
    def _match_any(self, token_types: List[TokenType]) -> Optional[Token]:
        """
        Match and consume a token of any of the specified types.
        
        Args:
            token_types: List of acceptable token types
            
        Returns:
            The matched token or None if no match
        """
        token = self._peek()
        if token and token.type in token_types:
            return self._advance()
        return None
    
    def _expect(self, token_type: TokenType) -> Token:
        """
        Expect a token of the specified type, raising an error if not found.
        
        Args:
            token_type: The expected token type
            
        Returns:
            The matched token
            
        Raises:
            ValueError: If the expected token is not found
        """
        token = self._match(token_type)
        if not token:
            peek = self._peek()
            peek_info = f"{peek.type.name}({repr(peek.value)})" if peek else "EOF"
            raise ValueError(f"Expected {token_type.name}, got {peek_info} at line {peek.line if peek else 'end'}")
        return token
    
    def parse(self) -> CodeBlock:
        """
        Parse the token stream into a CodeBlock containing all statements.
        
        Returns:
            A CodeBlock containing all parsed statements
        """
        # Start with an empty code block
        block = CodeBlock()
        
        # Parse statements until EOF
        while self._peek() and self._peek().type != TokenType.EOF:
            # Skip newlines between statements
            while self._match(TokenType.NEWLINE):
                pass
                
            # Check if we have another statement
            if self._peek() and self._peek().type != TokenType.EOF:
                stmt = self._parse_statement()
                if stmt:  # Only add non-None statements
                    block.append(stmt)
        
        return block
    
    def _parse_statement(self) -> Optional[Statement]:
        """
        Parse a single statement.
        
        Returns:
            A Statement object or None if no valid statement was found
        
        Raises:
            ValueError: If the statement cannot be parsed
        """
        if not self._peek():
            return None
            
        # Handle variable assignment: $name = expr
        if self._peek().type == TokenType.VARIABLE:
            var_token = self._advance()
            
            # Skip optional whitespace
            self._match(TokenType.WHITESPACE)
            
            # Check for assignment operator
            if self._match(TokenType.ASSIGNMENT):
                # Parse the expression on the right
                expr = self._parse_expression()
                return SetVariableStatement(var_token.value, expr)
        
        # Handle blocks with introducer: keyword:
        if self._peek().type == TokenType.KEYWORD:
            keyword_token = self._advance()
            
            # Check if this is a foreach statement
            if keyword_token.value == 'foreach':
                return self._parse_foreach_statement()
                
            # Check if this is a try statement
            if keyword_token.value == 'try':
                return self._parse_try_catch_statement()
                
            # Check for colon after keyword
            if self._match(TokenType.COLON):
                # Parse indented block
                return self._parse_indented_block(keyword_token.value)
        
        # Check for blocks with command introducer: command:
        if self._peek().type == TokenType.COMMAND:
            cmd_token = self._advance()
            
            # Check for colon
            if self._match(TokenType.COLON):
                # Parse indented block with command as type
                return self._parse_indented_block(cmd_token.value)
            
            # Otherwise it's a regular command
            self.pos -= 1  # Back up to reprocess the command token
        
        # Parse command statement (may return None if no command found)
        cmd_stmt = self._parse_command_statement()
        if cmd_stmt:
            return cmd_stmt
            
        # Skip any unexpected tokens to avoid infinite loops
        if self._peek() and self._peek().type not in (TokenType.NEWLINE, TokenType.DEDENT, TokenType.EOF):
            # Log the skipped token for debugging
            token = self._advance()
            print(f"Warning: Skipping unexpected token {token.type.name}({repr(token.value)}) at line {token.line}")
            
        # No valid statement found
        return None
    
    def _parse_foreach_statement(self) -> ForEachStatement:
        """
        Parse a foreach statement.
        
        Format: foreach $item in collection_expr:
                    # indented block
                    
        Returns:
            A ForEachStatement object
        """
        # We've already consumed the 'foreach' keyword
        
        # Skip whitespace and get variable
        self._match(TokenType.WHITESPACE)
        var_token = self._expect(TokenType.VARIABLE)
        
        # Skip whitespace and get 'in' keyword
        self._match(TokenType.WHITESPACE)
        in_token = self._expect(TokenType.KEYWORD)
        if in_token.value != 'in':
            raise ValueError(f"Expected 'in' keyword, got '{in_token.value}' at line {in_token.line}")
        
        # Skip whitespace and get collection expression
        self._match(TokenType.WHITESPACE)
        collection_expr = self._parse_expression()
        
        # Expect colon
        self._expect(TokenType.COLON)
        
        # Get indented block
        body = self._parse_indented_block(None)
        
        return ForEachStatement(var_token.value, collection_expr, body)
    
    def _parse_try_catch_statement(self) -> TryCatchStatement:
        """
        Parse a try-catch statement.
        
        Format: try:
                    # indented try block
                catch:
                    # indented catch block
                    
        Returns:
            A TryCatchStatement object
        """
        # We've already consumed the 'try' keyword
        
        # Expect colon
        self._expect(TokenType.COLON)
        
        # Parse try block
        try_block = self._parse_indented_block(None)
        
        # Expect 'catch' keyword
        self._expect(TokenType.KEYWORD)  # Should be 'catch'
        
        # Expect colon
        self._expect(TokenType.COLON)
        
        # Parse catch block
        catch_block = self._parse_indented_block(None)
        
        return TryCatchStatement(try_block, catch_block)
    
    def _parse_indented_block(self, block_type: Optional[str]) -> CodeBlock:
        """
        Parse an indented block of statements.
        
        Args:
            block_type: Optional block type identifier (e.g., 'parallel')
            
        Returns:
            A CodeBlock containing the parsed statements
        """
        # Create a code block with the specified type
        block = CodeBlock(block_type=block_type)
        
        # Expect a newline
        self._expect(TokenType.NEWLINE)
        
        # Expect an indent
        self._expect(TokenType.INDENT)
        
        # Parse statements until we hit a dedent or EOF
        max_iterations = 1000  # Safety measure to prevent infinite loops
        iteration_count = 0
        
        while self._peek() and self._peek().type not in (TokenType.DEDENT, TokenType.EOF):
            iteration_count += 1
            if iteration_count > max_iterations:
                raise ValueError(f"Potential infinite loop detected in _parse_indented_block. Current token: {self._peek()}")
                
            # Skip newlines between statements
            while self._match(TokenType.NEWLINE):
                pass
                
            # Parse the next statement if we haven't reached the end of the block
            if self._peek() and self._peek().type not in (TokenType.DEDENT, TokenType.EOF):
                stmt = self._parse_statement()
                if stmt:  # Only add non-None statements
                    block.append(stmt)
                else:
                    # No valid statement found, but we're still in the block
                    # Skip to the next line to avoid infinite loops
                    while self._peek() and self._peek().type not in (TokenType.NEWLINE, TokenType.DEDENT, TokenType.EOF):
                        token = self._advance()
                        print(f"Warning: Skipping unexpected token in block: {token.type.name}({repr(token.value)}) at line {token.line}")
                    
                    # Make sure we advance past the newline
                    self._match(TokenType.NEWLINE)
        
        # Consume the dedent if present, otherwise we're at EOF
        if self._peek() and self._peek().type == TokenType.DEDENT:
            self._advance()  # Consume the DEDENT
        
        return block
    
    def _parse_command_statement(self) -> Optional[CommandStatement]:
        """
        Parse a command statement.
        
        Format: command arg1 arg2 ...
        
        Returns:
            A CommandStatement object or None if no command found
        """
        # Check if there's a command token at current position
        if self._peek() and self._peek().type == TokenType.COMMAND:
            # Get the command name
            cmd_token = self._advance()
            cmd_name = cmd_token.value
            
            # Collect all tokens for the command arguments until newline/EOF
            arg_tokens = []
            while self._peek() and self._peek().type not in (TokenType.NEWLINE, TokenType.EOF):
                arg_tokens.append(self._advance())
            
            # Convert tokens to argument string
            args_str = self._tokens_to_arg_string(arg_tokens)
            
            return CommandStatement(cmd_name, args_str)
        
        # Special case: we might be starting with a parameter without a command
        # This would be an error case, but we need to handle it to avoid infinite loops
        elif self._peek() and self._peek().type == TokenType.PARAMETER:
            # Skip this parameter token to avoid infinite loops
            param_token = self._advance()
            
            # Consume the rest of the line
            while self._peek() and self._peek().type not in (TokenType.NEWLINE, TokenType.EOF):
                self._advance()
                
            # Report the error by raising an exception
            raise ValueError(f"Parameter '{param_token.value}' without a command at line {param_token.line}")
            
        # No command found
        return None
    
    def _tokens_to_arg_string(self, tokens: List[Token]) -> str:
        """
        Convert a list of tokens to a command argument string.
        
        Args:
            tokens: List of tokens representing the arguments
            
        Returns:
            Argument string suitable for the CommandStatement
        """
        parts = []
        for token in tokens:
            if token.type == TokenType.STRING:
                # Re-quote strings
                parts.append(f'"{token.value}"')
            elif token.type == TokenType.VARIABLE:
                # Re-add $ prefix
                parts.append(f'${token.value}')
            else:
                parts.append(str(token.value))
        
        return ' '.join(parts)
    
    def _parse_expression(self) -> str:
        """
        Parse an expression until newline, colon, or EOF.
        
        Returns:
            The expression as a string
        """
        expr_tokens = []
        
        # Collect tokens until newline, colon, or EOF
        while (self._peek() and 
               self._peek().type not in (TokenType.NEWLINE, TokenType.COLON, TokenType.EOF)):
            expr_tokens.append(self._advance())
        
        # Convert tokens to expression string
        return self._tokens_to_expression(expr_tokens)
    
    def _tokens_to_expression(self, tokens: List[Token]) -> str:
        """
        Convert a list of tokens to an expression string.
        
        Args:
            tokens: List of tokens representing the expression
            
        Returns:
            Expression string
        """
        parts = []
        for token in tokens:
            if token.type == TokenType.STRING:
                # Format as a proper Python string
                parts.append(repr(token.value))
            elif token.type == TokenType.VARIABLE:
                # Re-add $ prefix
                parts.append(f'${token.value}')
            else:
                parts.append(str(token.value))
        
        return ' '.join(parts)


def parse_script(script_text: str) -> CodeBlock:
    """
    Parse a script string into a CodeBlock.
    
    Args:
        script_text: The script text to parse
        
    Returns:
        A CodeBlock containing all the statements in the script
        
    Raises:
        ValueError: If there's a syntax error in the script
    """
    lexer = Lexer(script_text)
    tokens = lexer.tokenize()
    parser = Parser(tokens)
    return parser.parse()


def parse_line(line: str) -> Statement:
    """
    Parse a single line of input into a Statement.
    
    Args:
        line: The line to parse
        
    Returns:
        A Statement object representing the parsed line
        
    Raises:
        ValueError: If the line cannot be parsed into a valid statement
    """
    block = parse_script(line)
    
    # If the block contains exactly one statement, return it
    if len(block) == 1:
        return block[0]
    
    # Otherwise, return the block itself
    return block