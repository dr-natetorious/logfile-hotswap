"""
Variable manager for storing and evaluating shell variables.
"""
import re
import ast
import builtins
import typing as t
from collections.abc import Mapping


class VariableManager:
    """
    Manages variables for the shell, including setting, getting, and evaluating expressions.
    """
    
    def __init__(self):
        """Initialize the variable manager with default variables."""
        self._variables = {}
        self._initialize_defaults()
    
    def _initialize_defaults(self):
        """Set up default variables."""
        # You can add any default variables here
        self._variables = {
            'servers': ['server1', 'server2', 'production', 'staging'],
            'paths': {
                'log': '/var/log',
                'temp': '/tmp',
                'home': '/home'
            },
            'cleanup_days': 30,
            'verbose': False
        }
    
    def get(self, name: str, default=None) -> t.Any:
        """
        Get a variable by name.
        
        Args:
            name: The variable name
            default: The default value if the variable doesn't exist
            
        Returns:
            The variable value or default
        """
        return self._variables.get(name, default)
    
    def set(self, name: str, value_expr: str) -> t.Any:
        """
        Set a variable to the result of evaluating a Python expression.
        
        Args:
            name: The variable name
            value_expr: A Python expression to evaluate
            
        Returns:
            The evaluated value
        
        Raises:
            SyntaxError: If the expression is invalid
            ValueError: If the evaluation fails
        """
        # Create a safe evaluation environment
        eval_globals = {
            '__builtins__': {
                name: getattr(builtins, name) for name in 
                ['dict', 'list', 'tuple', 'set', 'int', 'float', 'str', 'bool', 'True', 'False', 'None']
            }
        }
        
        # Add existing variables to the evaluation context
        eval_locals = self._variables.copy()
        
        try:
            # Parse the expression first to catch syntax errors
            ast.parse(value_expr)
            
            # Evaluate the expression in the restricted environment
            value = eval(value_expr, eval_globals, eval_locals)
            
            # Store the result
            self._variables[name] = value
            
            return value
        except SyntaxError as e:
            raise SyntaxError(f"Invalid expression: {e}")
        except Exception as e:
            raise ValueError(f"Failed to evaluate expression: {e}")
    
    def delete(self, name: str) -> bool:
        """
        Delete a variable.
        
        Args:
            name: The variable name
            
        Returns:
            True if the variable was deleted, False if it didn't exist
        """
        if name in self._variables:
            del self._variables[name]
            return True
        return False
    
    def list_variables(self) -> t.Dict[str, t.Any]:
        """
        Get all variables.
        
        Returns:
            A dictionary of all variables
        """
        return self._variables.copy()
    
    def expand_variables(self, text: str) -> str:
        """
        Expand variable references in text.
        
        Supports:
        - $VarName
        - ${VarName}
        - ${VarName.property} for nested access
        
        Args:
            text: The text containing variable references
            
        Returns:
            The text with variables expanded
        """
        # Handle ${var.property} syntax for nested access
        def replace_nested(match):
            expr = match.group(1)
            
            # Handle nested properties with dot notation
            if '.' in expr:
                parts = expr.split('.')
                var_name = parts[0]
                var_value = self.get(var_name)
                
                if var_value is None:
                    return f"${{{expr}}}"  # Return original if variable doesn't exist
                
                # Navigate the nested properties
                for prop in parts[1:]:
                    if isinstance(var_value, Mapping) and prop in var_value:
                        var_value = var_value[prop]
                    elif hasattr(var_value, prop):
                        var_value = getattr(var_value, prop)
                    elif isinstance(var_value, (list, tuple)) and prop.isdigit():
                        index = int(prop)
                        if 0 <= index < len(var_value):
                            var_value = var_value[index]
                        else:
                            return f"${{{expr}}}"  # Return original if index out of range
                    else:
                        return f"${{{expr}}}"  # Return original if property doesn't exist
                
                return str(var_value)
            else:
                # Simple variable
                var_value = self.get(expr)
                return str(var_value) if var_value is not None else f"${{{expr}}}"
        
        # Replace ${var.prop} pattern
        text = re.sub(r'\${([^}]+)}', replace_nested, text)
        
        # Handle $VarName syntax for simple variables
        def replace_simple(match):
            var_name = match.group(1)
            var_value = self.get(var_name)
            return str(var_value) if var_value is not None else f"${var_name}"
        
        # Replace $var pattern (but not if preceded by \ and not followed by {)
        text = re.sub(r'(?<!\\)\$([a-zA-Z_][a-zA-Z0-9_]*)(?!\{)', replace_simple, text)
        
        return text