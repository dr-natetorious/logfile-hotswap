import pytest
import typing as t
from collections.abc import Mapping
from src.cli.shell.variable_manager import VariableManager

class TestVariableManager:
    """Test suite for the VariableManager class."""

    def test_initialization(self):
        """Test that the VariableManager initializes with default variables."""
        vm = VariableManager()
        variables = vm.list_variables()
        
        # Check default variables
        assert 'servers' in variables
        assert 'paths' in variables
        assert 'cleanup_days' in variables
        assert 'verbose' in variables
        
        # Check default values
        assert isinstance(variables['servers'], list)
        assert isinstance(variables['paths'], dict)
        assert variables['cleanup_days'] == 30
        assert variables['verbose'] is False

    def test_get_existing_variable(self):
        """Test getting an existing variable."""
        vm = VariableManager()
        servers = vm.get('servers')
        assert servers == ['server1', 'server2', 'production', 'staging']

    def test_get_nonexistent_variable(self):
        """Test getting a nonexistent variable returns the default."""
        vm = VariableManager()
        value = vm.get('nonexistent', 'default_value')
        assert value == 'default_value'

    def test_get_with_type_hint(self):
        """Test getting a variable with type conversion."""
        vm = VariableManager()
        # Set cleanup_days to a string
        vm.set('cleanup_days', '"30"')
        
        # Get with type hint
        days = vm.get('cleanup_days', type_hint=int)
        assert days == 30
        assert isinstance(days, int)

    def test_set_simple_value(self):
        """Test setting a simple value."""
        vm = VariableManager()
        vm.set('test_var', "'hello'")
        value = vm.get('test_var')
        assert value == 'hello'

    def test_set_complex_value(self):
        """Test setting a value from a complex expression."""
        vm = VariableManager()
        vm.set('max_port', 'max([8080, 8081, 8082])')
        value = vm.get('max_port')
        assert value == 8082

    def test_set_with_type_hint(self):
        """Test setting a value with type validation."""
        vm = VariableManager()
        vm.set('port_str', '"8080"', type_hint=int)
        value = vm.get('port_str')
        assert value == 8080
        assert isinstance(value, int)

    def test_set_with_invalid_type(self):
        """Test setting a value that can't be converted to the specified type."""
        vm = VariableManager()
        with pytest.raises(ValueError):
            vm.set('invalid_int', '"not_an_int"', type_hint=int)

    def test_evaluate_expression_simple(self):
        """Test evaluating a simple expression."""
        vm = VariableManager()
        result = vm.evaluate_expression('2 + 2')
        assert result == 4

    def test_evaluate_expression_with_variables(self):
        """Test evaluating an expression that uses existing variables."""
        vm = VariableManager()
        vm.set('x', '10')
        vm.set('y', '20')
        result = vm.evaluate_expression('x + y')
        assert result == 30

    def test_evaluate_expression_with_functions(self):
        """Test evaluating an expression with allowed functions."""
        vm = VariableManager()
        vm.set('numbers', '[1, 2, 3, 4, 5]')
        result = vm.evaluate_expression('sum(numbers)')
        assert result == 15

    def test_evaluate_invalid_expression(self):
        """Test evaluating an invalid expression raises SyntaxError."""
        vm = VariableManager()
        with pytest.raises(SyntaxError):
            vm.evaluate_expression('2 +')

    def test_evaluate_expression_exception(self):
        """Test evaluating an expression that raises an exception."""
        vm = VariableManager()
        with pytest.raises(ValueError):
            vm.evaluate_expression('1 / 0')  # Division by zero

    def test_delete_existing_variable(self):
        """Test deleting an existing variable."""
        vm = VariableManager()
        assert vm.delete('servers') is True
        assert 'servers' not in vm.list_variables()

    def test_delete_nonexistent_variable(self):
        """Test deleting a nonexistent variable returns False."""
        vm = VariableManager()
        assert vm.delete('nonexistent') is False

    def test_list_variables(self):
        """Test listing all variables."""
        vm = VariableManager()
        vm.set('new_var', '"test"')
        variables = vm.list_variables()
        
        assert 'servers' in variables
        assert 'paths' in variables
        assert 'new_var' in variables
        assert variables['new_var'] == 'test'

    def test_expand_simple_variable(self):
        """Test expanding a simple variable reference."""
        vm = VariableManager()
        vm.set('name', '"John"')
        expanded = vm.expand_variables('Hello, $name!')
        assert expanded == 'Hello, John!'

    def test_expand_complex_variable(self):
        """Test expanding a complex variable reference."""
        vm = VariableManager()
        expanded = vm.expand_variables('Log path: ${paths["log"]}')
        assert expanded == 'Log path: /var/log'

    def test_expand_expression(self):
        """Test expanding an expression."""
        vm = VariableManager()
        vm.set('numbers', '[1, 2, 3, 4, 5]')
        expanded = vm.expand_variables('Sum: ${sum(numbers)}')
        assert expanded == 'Sum: 15'

    def test_expand_nonexistent_variable(self):
        """Test expanding a nonexistent variable leaves it unchanged."""
        vm = VariableManager()
        expanded = vm.expand_variables('Missing: $nonexistent')
        assert expanded == 'Missing: $nonexistent'

    def test_expand_nested_variables(self):
        """Test expanding nested variable references."""
        vm = VariableManager()
        vm.set('key', '"log"')
        expanded = vm.expand_variables('Nested: ${paths[key]}')
        assert expanded == 'Nested: /var/log'

    def test_get_typed_existing(self):
        """Test get_typed for an existing variable."""
        vm = VariableManager()
        vm.set('port_str', '"8080"')
        port = vm.get_typed('port_str', int)
        assert port == 8080
        assert isinstance(port, int)

    def test_get_typed_default(self):
        """Test get_typed with a default value."""
        vm = VariableManager()
        port = vm.get_typed('nonexistent', int, default=8000)
        assert port == 8000
        assert isinstance(port, int)

    def test_get_typed_conversion_error(self):
        """Test get_typed when the conversion fails."""
        vm = VariableManager()
        vm.set('invalid', '"not_a_number"')
        with pytest.raises(ValueError):
            vm.get_typed('invalid', int)

    def test_safe_eval_context(self):
        """Test that the safe eval context contains only allowed functions."""
        vm = VariableManager()
        context = vm._create_safe_eval_context()
        
        # Check that only safe functions are available
        builtins = context['__builtins__']
        assert 'int' in builtins
        assert 'float' in builtins
        assert 'open' not in builtins
        assert 'exec' not in builtins
        assert '__import__' not in builtins