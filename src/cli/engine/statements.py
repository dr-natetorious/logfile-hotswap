"""
Statement definitions for the shell scripting engine.

This module defines the base Statement class and its various implementations
that can be executed by the command executor.
"""
import abc
import ast
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any, Type, Union, ClassVar, Set, Tuple, Sequence, Iterator

# Type aliases for common types
StatementOrBlock = Union[List['Statement'], 'CodeBlock']

class Statement(abc.ABC):
    """
    Abstract base class for all executable statements in the shell.
    
    A statement represents a unit of execution that can be processed
    by the command executor.
    """
    
    @abc.abstractmethod
    def execute(self, executor) -> Any:
        """
        Execute the statement within the context of the given executor.
        
        Args:
            executor: The command executor managing the execution context
            
        Returns:
            Result of the statement execution
        """
        pass
    
    def __add__(self, other):
        """
        Allow Statement + Statement to create a CodeBlock.
        
        Args:
            other: Another statement to combine with this one
            
        Returns:
            A CodeBlock containing both statements
        """
        if isinstance(other, Statement):
            return CodeBlock([self, other])
        return NotImplemented
    
    def __radd__(self, other):
        """
        Allow list + Statement operations by converting the list to a CodeBlock.
        
        Args:
            other: Likely a list of statements
            
        Returns:
            A CodeBlock containing the statements
        """
        if isinstance(other, list) and all(isinstance(item, Statement) for item in other):
            return CodeBlock(other + [self])
        return NotImplemented


@dataclass
class CommandStatement(Statement):
    """
    Represents a command statement to be executed.
    Wraps a BaseCommand instance with its parsed arguments.
    """
    command_name: str
    args_str: str = ""
    
    def execute(self, executor) -> bool:
        """
        Execute the command using the executor's command handler.
        """
        return executor.execute_command(self.command_name, self.args_str)


@dataclass
class SetVariableStatement(Statement):
    """
    Represents a variable assignment statement.
    Format: $variable = expression
    """
    variable_name: str
    expression: str
    
    def execute(self, executor) -> Any:
        """
        Set the variable using the executor's variable manager.
        """
        return executor.set_variable(self.variable_name, self.expression)


@dataclass
class ForEachStatement(Statement):
    """
    Represents a foreach loop statement.
    Format: foreach $item in $collection:
        # indented statements
    """
    item_var: str
    collection_expr: str
    body: StatementOrBlock
    
    def __post_init__(self):
        """Convert body to CodeBlock if it's a list."""
        if isinstance(self.body, list):
            self.body = CodeBlock(self.body)
    
    def execute(self, executor) -> Any:
        """
        Execute the foreach loop using the executor's variable manager.
        """
        return executor.execute_foreach(self.item_var, self.collection_expr, self.body)


@dataclass
class ParallelBlock(Statement):
    """
    Represents a block of statements to be executed in parallel.
    
    Format: parallel [$collection [as $item] [restricted by $policy]]:
        # indented statements
    """
    body: StatementOrBlock  # The statements to execute in parallel
    collection_expr: Optional[str] = None  # Optional collection to iterate over
    item_var: Optional[str] = None  # Optional variable name for current item
    policy_expr: Optional[str] = None  # Optional restriction policy
    max_concurrent: int = 10  # Maximum concurrent executions
    
    def __post_init__(self):
        """Convert body to CodeBlock if it's a list."""
        if isinstance(self.body, list):
            self.body = CodeBlock(self.body)
    
    def execute(self, executor) -> Any:
        """
        Execute statements in parallel, with optional iteration.
        """
        if self.collection_expr:
            # Parallel foreach mode
            return executor.execute_parallel_foreach(
                self.item_var or "_item",  # Use default name if not specified
                self.collection_expr,
                self.body,
                self.policy_expr,
                self.max_concurrent
            )
        else:
            # Simple parallel block mode
            return executor.execute_parallel_block(
                self.body,
                self.max_concurrent
            )


@dataclass
class RemoteBlockStatement(Statement):
    """
    Represents a block of statements to be executed on one or more remote systems.
    
    Format: remote $system|$systems [as $target]:
               # indented statements to execute remotely
    """
    system_expr: str  # Expression to evaluate to one or more systems
    body: StatementOrBlock
    target_var: Optional[str] = None  # Optional variable name to reference the current system
    
    def __post_init__(self):
        """Convert body to CodeBlock if it's a list."""
        if isinstance(self.body, list):
            self.body = CodeBlock(self.body)
    
    def execute(self, executor) -> Any:
        """
        Execute statements on remote system(s).
        """
        return executor.execute_remote_block(
            self.system_expr,
            self.body,
            self.target_var
        )


@dataclass
class TryCatchStatement(Statement):
    """
    Represents a try-catch-finally block for error handling.
    Format: 
    try:
        # indented statements
    catch:
        # indented statements with access to $error
    finally:
        # indented statements always executed]
    """
    try_block: StatementOrBlock
    catch_block: StatementOrBlock
    finally_block: Optional[StatementOrBlock] = None
    
    def __post_init__(self):
        """Convert blocks to CodeBlock if they're lists."""
        if isinstance(self.try_block, list):
            self.try_block = CodeBlock(self.try_block)
        if isinstance(self.catch_block, list):
            self.catch_block = CodeBlock(self.catch_block)
        if self.finally_block is not None and isinstance(self.finally_block, list):
            self.finally_block = CodeBlock(self.finally_block)
    
    def execute(self, executor) -> Any:
        """
        Execute the try-catch-finally block using the executor.
        """
        return executor.execute_try_catch(
            self.try_block, 
            self.catch_block,
            self.finally_block
        )


@dataclass
class BreakStatement(Statement):
    """
    Represents a break statement to exit a loop.
    
    Format: break
    """
    def execute(self, executor) -> Any:
        """
        Break out of the current loop.
        """
        return executor.execute_break()


@dataclass
class ContinueStatement(Statement):
    """
    Represents a continue statement to skip to the next iteration.
    
    Format: continue
    """
    def execute(self, executor) -> Any:
        """
        Skip to the next iteration of the current loop.
        """
        return executor.execute_continue()


@dataclass
class CodeBlock(Statement, Sequence[Statement]):
    """
    Represents a block of statements.
    Can have a type (e.g., 'parallel', 'sequential') and metadata.
    
    Format: 
    type:
        # indented statements
    
    CodeBlock implements the Sequence protocol, so it can be used like a list.
    """
    statements: List[Statement] = field(default_factory=list)
    block_type: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def execute(self, executor) -> Any:
        """
        Execute all statements in the block sequentially or according to block_type.
        """
        if self.block_type == 'parallel':
            return executor.execute_parallel(self.statements)
        else:
            # Default to sequential execution
            result = None
            for statement in self.statements:
                result = statement.execute(executor)
            return result
    
    # Sequence protocol implementation
    def __getitem__(self, index) -> Union[Statement, List[Statement]]:
        """Get statement at index or slice the block."""
        return self.statements[index]
    
    def __len__(self) -> int:
        """Get the number of statements in the block."""
        return len(self.statements)
    
    def __iter__(self) -> Iterator[Statement]:
        """Iterate through the statements."""
        return iter(self.statements)
    
    def __add__(self, other):
        """
        Allow CodeBlock + Statement or CodeBlock + CodeBlock operations.
        
        Args:
            other: A Statement or CodeBlock to append
            
        Returns:
            A new CodeBlock with all statements
        """
        if isinstance(other, Statement):
            if isinstance(other, CodeBlock):
                return CodeBlock(self.statements + other.statements, self.block_type, dict(self.metadata))
            else:
                return CodeBlock(self.statements + [other], self.block_type, dict(self.metadata))
        return NotImplemented
    
    def __radd__(self, other):
        """
        Allow Statement + CodeBlock operations.
        
        Args:
            other: Likely a Statement or list of statements
            
        Returns:
            A new CodeBlock with all statements
        """
        if isinstance(other, Statement) and not isinstance(other, CodeBlock):
            return CodeBlock([other] + self.statements, self.block_type, dict(self.metadata))
        if isinstance(other, list) and all(isinstance(item, Statement) for item in other):
            return CodeBlock(other + self.statements, self.block_type, dict(self.metadata))
        return NotImplemented
    
    def append(self, statement: Statement) -> None:
        """
        Append a statement to the block.
        
        Args:
            statement: The statement to append
        """
        self.statements.append(statement)
    
    def extend(self, statements: Union[List[Statement], 'CodeBlock']) -> None:
        """
        Extend the block with more statements.
        
        Args:
            statements: A list of statements or another CodeBlock to add
        """
        if isinstance(statements, CodeBlock):
            self.statements.extend(statements.statements)
        else:
            self.statements.extend(statements)


@dataclass
class IfStatement(Statement):
    """
    Represents an if-elif-else conditional statement.
    
    Format:
    if $condition:
        # indented statements
    elseif $condition:
        # indented statements
    else:
        # indented statements
    """
    conditions: List[str]
    blocks: List[CodeBlock]
    else_block: Optional['CodeBlock'] = None
    
    def execute(self, executor) -> Any:
        """
        Execute the if statement using the executor.
        """
        return executor.execute_if(self.conditions, self.blocks, self.else_block)


@dataclass
class WhileStatement(Statement):
    """
    Represents a while loop statement.
    
    Format:
    while $condition:
        # indented statements
    """
    condition: str
    body: StatementOrBlock
    
    def __post_init__(self):
        """Convert body to CodeBlock if it's a list."""
        if isinstance(self.body, list):
            self.body = CodeBlock(self.body)
    
    def execute(self, executor) -> Any:
        """
        Execute the while loop using the executor.
        """
        return executor.execute_while(self.condition, self.body)


@dataclass
class FunctionDefinitionStatement(Statement):
    """
    Represents a function definition statement.
    
    Format:
    function|def name($param1, $param2=default):
        # indented statements
    """
    name: str
    parameters: List[Tuple[str, Optional[str]]]  # (name, default) pairs
    body: StatementOrBlock
    
    def __post_init__(self):
        """Convert body to CodeBlock if it's a list."""
        if isinstance(self.body, list):
            self.body = CodeBlock(self.body)
    
    def execute(self, executor) -> Any:
        """
        Register the function with the executor.
        """
        return executor.register_function(self.name, self.parameters, self.body)


@dataclass
class ReturnStatement(Statement):
    """
    Represents a return statement.
    
    Format:
    return $expression
    """
    expression: Optional[str] = None
    
    def execute(self, executor) -> Any:
        """
        Return a value from a function.
        """
        return executor.execute_return(self.expression)


@dataclass
class PipelineStatement(Statement):
    """
    Represents a pipeline of commands.
    
    Format:
    command1 | command2 | command3
    """
    commands: List[CommandStatement]
    
    def execute(self, executor) -> Any:
        """
        Execute a pipeline of commands.
        """
        return executor.execute_pipeline(self.commands)