"""
Commands for managing shell variables.
"""
import re
from .base import BaseCommand
from prompt_toolkit.completion import Completion


class VariableCommand(BaseCommand):
    """
    Commands for setting, getting, and listing variables.
    """
    
    def get_command_names(self):
        return ['set', 'unset', 'vars', 'echo', 'expr']
    
    def execute(self, command_name, args_str, shell):
        if command_name == 'set':
            return self._set_variable(args_str, shell)
        elif command_name == 'unset':
            return self._unset_variable(args_str, shell)
        elif command_name == 'vars':
            return self._list_variables(shell)
        elif command_name == 'echo':
            return self._echo_with_vars(args_str, shell)
        elif command_name == 'expr':
            return self._execute_expr(args_str, shell)
        
        return False
    
    def _set_variable(self, args_str, shell):
        """Set a variable to a value."""
        # Skip leading/trailing whitespace
        args_str = args_str.strip()
        
        # Check for assignment pattern
        match = re.match(r'^([a-zA-Z_][a-zA-Z0-9_]*)\s+(.+)$', args_str)
        
        if not match:
            print("Error: Invalid variable assignment")
            print("Usage: set variable_name expression")
            print("Example: set servers ['server1', 'server2']")
            return False
        
        var_name, value_expr = match.groups()
        
        try:
            value = shell.variable_manager.set(var_name, value_expr)
            print(f"Set {var_name} = {value!r}")
            return True
        except (SyntaxError, ValueError) as e:
            print(f"Error: {e}")
            return False
    
    def _unset_variable(self, args_str, shell):
        """Delete a variable."""
        var_name = args_str.strip()
        
        if not var_name:
            print("Error: Variable name required")
            print("Usage: unset variable_name")
            return False
        
        if shell.variable_manager.delete(var_name):
            print(f"Deleted variable: {var_name}")
            return True
        else:
            print(f"Variable not found: {var_name}")
            return False
    
    def _list_variables(self, shell):
        """List all variables and their values."""
        variables = shell.variable_manager.list_variables()
        
        if not variables:
            print("No variables defined")
            return True
        
        print("Variables:")
        for name, value in sorted(variables.items()):
            # Format the output based on the variable type
            if isinstance(value, (list, dict, tuple, set)):
                print(f"  {name} = {value!r}")
            else:
                print(f"  {name} = {value}")
        
        return True
    
    def _echo_with_vars(self, args_str, shell):
        """Echo text with variable expansion."""
        if not args_str:
            print()
            return True
        
        # Expand variables in the text
        expanded_text = shell.variable_manager.expand_variables(args_str)
        print(expanded_text)
        return True
        
    def _execute_expr(self, expr_str, shell):
        """Execute a Python expression."""
        if not expr_str.strip():
            print("Error: Expression required")
            print("Usage: expr <python_expression>")
            return False
            
        try:
            result = shell.variable_manager.execute(expr_str)
            if result is not None:
                print(repr(result))
            return True
        except (SyntaxError, ValueError) as e:
            print(f"Error: {e}")
            return False
    
    def get_completions(self, text):
        """
        Provide completions for variable commands.
        This would be populated from actual variables in the shell.
        """
        # This method would need to access the shell's variable_manager
        # We'll implement a basic version here
        yield Completion('servers', start_position=0, display='servers')
        yield Completion('paths', start_position=0, display='paths')
        yield Completion('cleanup_days', start_position=0, display='cleanup_days')
        yield Completion('verbose', start_position=0, display='verbose')
    
    def get_help(self):
        return """
Variable management commands.

Usage:
  set <name> <expression>   - Set a variable to the result of a Python expression
                              Example: set servers ['server1', 'server2']
                              Example: set paths {"log": "/var/log", "temp": "/tmp"}
                              
  unset <name>              - Delete a variable
  
  vars                      - List all variables and their values
  
  echo <text>               - Print text with variable expansion
                              Variables can be referenced with $name or ${name}
                              Nested properties with ${name.property}
                              Example: echo Server: $servers[0]
                              Example: echo Log path: ${paths.log}

Note: Variable expressions are evaluated as Python code with limited builtins.
"""