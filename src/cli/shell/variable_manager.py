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
        # Create a safe evaluation environment with allowed built-ins
        eval_globals = {
            '__builtins__': {
                'int': int, 'float': float, 'str': str, 'bool': bool,
                'list': list, 'dict': dict, 'tuple': tuple, 'set': set,
                'len': len, 'min': min, 'max': max, 'sum': sum,
                'True': True, 'False': False, 'None': None,
                'sorted': sorted, 'range': range, 'enumerate': enumerate,
                'zip': zip, 'round': round, 'abs': abs, 'all': all, 'any': any
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
    
    def execute(self, expr: str) -> t.Any:
        """
        Execute a Python expression and return the result.
        
        Args:
            expr: A Python expression to evaluate
            
        Returns:
            The result of the expression
            
        Raises:
            SyntaxError: If the expression is invalid
            ValueError: If the evaluation fails
        """
        # Similar to set() but doesn't store the result
        eval_globals = {
            '__builtins__': {
                'int': int, 'float': float, 'str': str, 'bool': bool,
                'list': list, 'dict': dict, 'tuple': tuple, 'set': set,
                'len': len, 'min': min, 'max': max, 'sum': sum,
                'True': True, 'False': False, 'None': None,
                'sorted': sorted, 'range': range, 'enumerate': enumerate,
                'zip': zip, 'round': round, 'abs': abs, 'all': all, 'any': any
            }
        }
        
        # Add existing variables to the evaluation context
        eval_locals = self._variables.copy()
        
        try:
            # Parse the expression first to catch syntax errors
            ast.parse(expr)
            
            # Evaluate the expression in the restricted environment
            result = eval(expr, eval_globals, eval_locals)
            return result
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
        - ${VarName.property}
        - ${VarName.method()}
        - ${function(VarName)}
        
        Args:
            text: The text containing variable references
            
        Returns:
            The text with variables expanded
        """
        # Handle complex expressions like ${len(var)}, ${var.append(4)}, etc.
        def replace_complex(match):
            expr = match.group(1)
            
            try:
                # Directly evaluate the expression using execute()
                result = self.execute(expr)
                return str(result)
            except Exception as e:
                # If the expression fails, return the original text
                return f"${{{expr}}}"
        
        # First replace ${expr} with results of evaluating expr
        text = re.sub(r'\${([^}]+)}', replace_complex, text)
        
        # Handle $VarName syntax for simple variables
        def replace_simple(match):
            var_name = match.group(1)
            var_value = self.get(var_name)
            return str(var_value) if var_value is not None else f"${var_name}"
        
        # Replace $var pattern (but not if preceded by \ and not followed by {)
        text = re.sub(r'(?<!\\)\$([a-zA-Z_][a-zA-Z0-9_]*)(?!\{)', replace_simple, text)
        
        return text