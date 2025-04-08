"""
Commands for managing shell variables using the Parameter class approach.
"""
import re
from typing import Optional, List, Dict, Any, TYPE_CHECKING
from .declarative import DeclarativeCommand, command, Parameter

if TYPE_CHECKING:
    from shell.shell import ServerShell

@command(name="set")
class SetVariableCommand(DeclarativeCommand):
    """
    Set a variable to a value from a Python expression.
    """
    name: str = Parameter(position=0, mandatory=True, help="Name of the variable to set")
    expression: str = Parameter(position=1, mandatory=True, help="Python expression to evaluate")
    
    def execute_command(self, shell:'ServerShell') -> bool:
        """Set a variable to a value."""
        try:
            value = shell.variable_manager.set(self.name, self.expression)
            print(f"Set {self.name} = {value}")
            return True
        except (SyntaxError, ValueError) as e:
            print(f"Error: {e}")
            return False

@command(name="unset")
class UnsetVariableCommand(DeclarativeCommand):
    """
    Delete a variable.
    """
    name: str = Parameter(position=0, help="Name of the variable to delete")
    
    def execute_command(self, shell:'ServerShell') -> bool:
        """Delete a variable."""
        if shell.variable_manager.delete(self.name):
            print(f"Deleted variable: {self.name}")
            return True
        else:
            print(f"Variable not found: {self.name}")
            return True


@command(name="vars")
class ListVariablesCommand(DeclarativeCommand):
    """
    List all variables and their values.
    """
    verbose: bool = Parameter(False, help="Show detailed type information", aliases=["v", "detailed"])
    
    def execute_command(self, shell:'ServerShell') -> bool:
        """List all variables and their values."""
        variables = shell.variable_manager.list_variables()
        
        if not variables:
            print("No variables defined")
            return True
        
        print("Variables:")
        for name, value in sorted(variables.items()):
            # Format the output based on the variable type
            if self.verbose:
                # Show type information in verbose mode
                type_info = type(value).__name__
                if isinstance(value, (list, dict, tuple, set)):
                    print(f"  {name} ({type_info}) = {value!r}")
                else:
                    print(f"  {name} ({type_info}) = {value}")
            else:
                # Normal output
                if isinstance(value, (list, dict, tuple, set)):
                    print(f"  {name} = {value!r}")
                else:
                    print(f"  {name} = {value}")
        
        return True

@command(name="echo")
class EchoCommand(DeclarativeCommand):
    """
    Echo text with variable expansion.
    Variables can be referenced with $name or ${name}.
    Nested properties with ${name.property}.
    """
    text: Optional[str] = Parameter(None, position=0, mandatory=False, 
                                    help="Text to echo with variable expansion")
    no_newline: bool = Parameter(False, help="Suppress trailing newline", aliases=["n"])
    
    def execute_command(self, shell) -> bool:
        """Echo text with variable expansion."""
        if self.text is None:
            print(end="" if self.no_newline else "\n")
            return True
        
        # Expand variables in the text
        expanded_text = shell.variable_manager.expand_variables(self.text)
        
        # Print with or without a newline
        if self.no_newline:
            print(expanded_text, end="")
        else:
            print(expanded_text)
            
        return True


@command(name="expr")
class ExprCommand(DeclarativeCommand):
    """
    Execute a Python expression with variable expansion.
    """
    expression: str = Parameter(position=0, help="Python expression to evaluate")
    
    def execute_command(self, shell) -> bool:
        """Execute a Python expression."""
        try:
            result = shell.variable_manager.execute(self.expression)
            if result is not None:
                print(repr(result))
            return True
        except (SyntaxError, ValueError) as e:
            print(f"Error: {e}")
            return False