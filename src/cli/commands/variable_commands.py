"""
Commands for managing shell variables using the declarative approach.
"""
import re
from typing import Optional, List, Dict, Any
from prompt_toolkit.completion import Completion
from .declarative import DeclarativeCommand, command

@command(name="set")
class SetVariableCommand(DeclarativeCommand):
    """
    Set a variable to a value from a Python expression.
    """
    name: str
    expression: str
    
    def execute_command(self, shell) -> bool:
        """Set a variable to a value."""
        try:
            value = shell.variable_manager.set(self.name, self.expression)
            print(f"Set {self.name} = {value!r}")
            return True
        except (SyntaxError, ValueError) as e:
            print(f"Error: {e}")
            return False


@command(name="unset")
class UnsetVariableCommand(DeclarativeCommand):
    """
    Delete a variable.
    """
    name: str
    
    def execute_command(self, shell) -> bool:
        """Delete a variable."""
        if shell.variable_manager.delete(self.name):
            print(f"Deleted variable: {self.name}")
            return True
        else:
            print(f"Variable not found: {self.name}")
            return False


@command(name="vars")
class ListVariablesCommand(DeclarativeCommand):
    """
    List all variables and their values.
    """
    verbose: bool = False
    
    def execute_command(self, shell) -> bool:
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
    text: Optional[str] = None
    no_newline: bool = False
    
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
    expression: str
    
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


# This function helps with get_completions for variable-related commands
def get_variable_completions(text: str, shell) -> List[str]:
    """
    Get completions for variable names.
    """
    if not shell or not hasattr(shell, 'variable_manager'):
        # Fallback for testing
        return ['servers', 'paths', 'cleanup_days', 'verbose']
    
    # Get actual variables from the shell
    variables = shell.variable_manager.list_variables()
    return list(variables.keys())
    

# Custom implementation for get_completions to handle variable completions
def get_var_completions(self, text: str) -> List[Dict]:
    """
    Custom completion handler for variable commands.
    """
    # This would be populated from actual variables in the shell
    # We'll implement a basic version here with the same completions as the original
    completions = []
    for var_name in ['servers', 'paths', 'cleanup_days', 'verbose']:
        if var_name.startswith(text):
            completions.append(Completion(var_name, start_position=-len(text), display=var_name))
    return completions

# Add custom completions to the command classes
SetVariableCommand.get_completions = get_var_completions
UnsetVariableCommand.get_completions = get_var_completions