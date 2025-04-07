"""
Variable manager for storing and evaluating shell variables.
"""
import re
import ast
import typing as t
from collections.abc import Mapping
from utils.type_converter import TypeConverter

class VariableManager:
    """
    Manages variables for the shell, including setting, getting, and evaluating expressions.
    """
    
    def __init__(self):
        """Initialize the variable manager with default variables."""
        self._variables: t.Dict[str, t.Any] = {}
        self._initialize_defaults()
    
    def _initialize_defaults(self):
        """Set up default variables."""
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
    
    def _create_safe_eval_context(self) -> t.Dict[str, t.Any]:
        """
        Create a safe evaluation environment with allowed built-ins.
        
        Returns:
            A dictionary of safe global variables for evaluation
        """
        return {
            '__builtins__': {
                'int': int, 'float': float, 'str': str, 'bool': bool,
                'list': list, 'dict': dict, 'tuple': tuple, 'set': set,
                'len': len, 'min': min, 'max': max, 'sum': sum,
                'True': True, 'False': False, 'None': None,
                'sorted': sorted, 'range': range, 'enumerate': enumerate,
                'zip': zip, 'round': round, 'abs': abs, 'all': all, 'any': any
            }
        }
    
    def get(self, name: str, default: t.Any = None, type_hint: t.Optional[t.Type] = None) -> t.Any:
        """
        Get a variable by name, with optional type conversion.
        
        Args:
            name: The variable name
            default: The default value if the variable doesn't exist
            type_hint: Optional type to convert the value to
            
        Returns:
            The variable value, optionally converted to the specified type
        """
        value = self._variables.get(name, default)
        
        # Apply type conversion if type_hint is provided
        if type_hint is not None:
            try:
                return TypeConverter.convert(value, type_hint)
            except ValueError:
                # If conversion fails, return the original value
                return value
        
        return value
    
    def set(
        self, 
        name: str, 
        value_expr: str, 
        type_hint: t.Optional[t.Type] = None
    ) -> t.Any:
        """
        Set a variable to the result of evaluating a Python expression.
        
        Args:
            name: The variable name
            value_expr: A Python expression to evaluate
            type_hint: Optional type to validate the result against
            
        Returns:
            The evaluated value
        
        Raises:
            SyntaxError: If the expression is invalid
            ValueError: If the evaluation fails or type validation fails
        """
        # First, evaluate the expression
        value = self.evaluate_expression(value_expr)
        
        # If type_hint is provided, validate the value
        if type_hint is not None:
            try:
                # Attempt to convert/validate the value
                value = TypeConverter.convert(value, type_hint)
            except ValueError as e:
                # If direct conversion fails, try some fallback strategies
                if isinstance(value, str):
                    try:
                        # Try converting the string directly
                        converted_value = TypeConverter.convert(value, type_hint)
                        value = converted_value
                    except ValueError:
                        # If all conversion attempts fail, raise the original error
                        raise ValueError(f"Cannot convert value to {type_hint.__name__}: {e}")
                else:
                    # If not a string and conversion fails, raise the error
                    raise ValueError(f"Cannot convert value to {type_hint.__name__}: {e}")
        
        # Store the result
        self._variables[name] = value        
        return value
    
    def evaluate_expression(self, expr: str) -> t.Any:
        """
        Evaluate a Python expression and return the result.
        
        Args:
            expr: A Python expression to evaluate
            
        Returns:
            The result of the expression
            
        Raises:
            SyntaxError: If the expression is invalid
            ValueError: If the evaluation fails
        """
        # Create a safe evaluation environment
        eval_globals = self._create_safe_eval_context()
        
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
                # Directly evaluate the expression
                result = self.evaluate_expression(expr)
                return str(result)
            except Exception:
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
    
    def get_typed(self, name: str, type_hint: t.Type, default: t.Any = None) -> t.Any:
        """
        Get a variable with specific type conversion.
        
        Args:
            name: The variable name
            type_hint: The type to convert the value to
            default: The default value if the variable doesn't exist
            
        Returns:
            The variable value converted to the specified type
        """
        value = self.get(name, default)
        return TypeConverter.convert(value, type_hint)

# Example usage
def example():
    # Create a variable manager
    vm = VariableManager()
    
    # Set variables using evaluation
    vm.set('ports', '[8080, 8081, 8082]')
    vm.set('debug', 'True')
    
    # Evaluate expressions
    max_port = vm.evaluate_expression('max(ports)')
    
    # Get variables with type conversion
    ports = vm.get_typed('ports', t.List[int])
    is_debug = vm.get_typed('debug', bool)
    
    print(f"Ports: {ports}")
    print(f"Max Port: {max_port}")
    print(f"Debug mode: {is_debug}")
    
    # Expand variables in a string
    expanded = vm.expand_variables('Server is running on port ${ports[0]}')
    print(f"Expanded: {expanded}")

if __name__ == '__main__':
    example()