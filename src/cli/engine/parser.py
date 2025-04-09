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
    EXPRESSION = auto()        # Expression
    INDENT = auto()            # Indentation increase
    DEDENT = auto()            # Indentation decrease
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
            
            # Delimiters and operators
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
            
            # Whitespace
            (r'[ \t]+', lambda m: Token(TokenType.WHITESPACE, m.group(0), self.line, self.column)),
            
            # Newline (for indentation processing)
            (r'\n', self._newline_token),
            
            # Identifiers and keywords
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
        value = ast.literal_eval(full_str)
        return Token(TokenType.STRING, value, self.line, self.column)
    
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
            # Skip empty lines or comment-only lines
            if not line.strip() or line.strip().startswith('#'):
                self.line += 1
                continue
            
            # Process indentation
            indent_tokens = self._process_indentation(line)
            result.extend(indent_tokens)
            
            # Tokenize the rest of the line
            pos = len(line) - len(line.lstrip())  # Skip the indentation
            self.column = pos + 1  # 1-based column indexing
            
            while pos < len(line):
                # Try to match a token pattern
                matched = False
                
                for pattern, token_func in self.patterns:
                    regex = re.compile(pattern)
                    match = regex.match(line[pos:])
                    
                    if match:
                        token = token_func(match)
                        if token.type != TokenType.WHITESPACE:  # Skip whitespace in the result
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
        self.tokens = tokens
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
                block.append(stmt)
        
        return block
    
    def _parse_statement(self) -> Statement:
        """
        Parse a single statement.
        
        Returns:
            A Statement object
        
        Raises:
            ValueError: If the statement cannot be parsed
        """
        # Check for variable assignment: $name = expr
        if self._peek() and self._peek().type == TokenType.VARIABLE:
            var_token = self._advance()
            
            # Skip optional whitespace
            self._match(TokenType.WHITESPACE)
            
            # Check for assignment operator
            if self._match(TokenType.ASSIGNMENT):
                # Parse the expression on the right
                expr = self._parse_expression()
                return SetVariableStatement(var_token.value, expr)
        
        # Check for block with introducer: keyword:
        if self._peek() and self._peek().type in (TokenType.KEYWORD, TokenType.COMMAND):
            keyword_token = self._advance()
            
            # Check for colon after keyword
            if self._match(TokenType.COLON):
                # Parse indented block
                return self._parse_indented_block(keyword_token.value)
        
        # Check for foreach statement: foreach $item in $collection
        if self._peek() and self._peek().type == TokenType.KEYWORD and self._peek().value == 'foreach':
            self._advance()  # Consume 'foreach'
            
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
            
            # Get indented block
            body = self._parse_indented_block(None)
            
            return ForEachStatement(var_token.value, collection_expr, body)
            
        # Check for try-catch statement
        if self._peek() and self._peek().type == TokenType.KEYWORD and self._peek().value == 'try':
            self._advance()  # Consume 'try'
            
            # Skip whitespace and colon
            self._match(TokenType.WHITESPACE)
            self._expect(TokenType.COLON)
            
            # Parse try block
            try_block = self._parse_indented_block(None)
            
            # Find catch block
            if self._peek() and self._peek().type == TokenType.KEYWORD and self._peek().value == 'catch':
                self._advance()  # Consume 'catch'
                
                # Skip whitespace and colon
                self._match(TokenType.WHITESPACE)
                self._expect(TokenType.COLON)
                
                # Parse catch block
                catch_block = self._parse_indented_block(None)
                
                return TryCatchStatement(try_block, catch_block)
            else:
                raise ValueError("Expected 'catch' block after 'try'")
        
        # Default to a command statement
        return self._parse_command_statement()
    
    def _parse_indented_block(self, block_type: Optional[str]) -> CodeBlock:
        """
        Parse an indented block of statements.
        
        Args:
            block_type: Optional block type identifier (e.g., 'parallel')
            
        Returns:
            A CodeBlock containing the parsed statements
        """
        # Create a code block with the specified type
        block = CodeBlock()
        if block_type:
            # Add metadata to the block if needed
            block.block_type = block_type
        
        # Expect a newline
        self._expect(TokenType.NEWLINE)
        
        # Expect an indent
        self._expect(TokenType.INDENT)
        
        # Parse statements until we hit a dedent
        while self._peek() and self._peek().type != TokenType.DEDENT:
            # Skip newlines between statements
            while self._match(TokenType.NEWLINE):
                pass
                
            # Parse the next statement if we haven't reached the end of the block
            if self._peek() and self._peek().type != TokenType.DEDENT:
                stmt = self._parse_statement()
                block.append(stmt)
        
        # Consume the dedent
        self._expect(TokenType.DEDENT)
        
        return block
    
    def _parse_command_statement(self) -> CommandStatement:
        """
        Parse a command statement.
        
        Returns:
            A CommandStatement object
        """
        # Get the command name
        cmd_token = self._expect(TokenType.COMMAND)
        cmd_name = cmd_token.value
        
        # Collect all the remaining tokens for the command arguments
        args = []
        while self._peek() and self._peek().type not in (TokenType.NEWLINE, TokenType.EOF):
            args.append(self._advance().value)
        
        # Join arguments with spaces
        args_str = ' '.join(str(arg) for arg in args)
        
        return CommandStatement(cmd_name, args_str)
    
    def _parse_expression(self) -> str:
        """
        Parse an expression.
        
        Currently simplistic: just collects tokens until newline/EOF.
        
        Returns:
            The expression as a string
        """
        tokens = []
        while self._peek() and self._peek().type not in (TokenType.NEWLINE, TokenType.EOF):
            tokens.append(self._advance().value)
        
        # Join all tokens to form the expression
        return ' '.join(str(token) for token in tokens)


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