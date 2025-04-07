import pytest
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Union, Any, Mapping, Set, get_args, get_origin

from src.cli.utils.type_converter import TypeConverter


def is_valid_type(value, expected_type):
    """Check if a value meets the expected type requirements, handling Union types properly."""
    # Handle None with Optional types
    if value is None:
        return type(None) in get_args(expected_type) if get_origin(expected_type) is Union else False
    
    # Handle Union types
    if get_origin(expected_type) is Union:
        # Check if value satisfies any of the Union type arguments
        type_args = get_args(expected_type)
        return any(is_valid_type(value, arg) for arg in type_args)
    
    # Handle container types
    if get_origin(expected_type) in (list, List):
        if not isinstance(value, list):
            return False
        # Empty list is valid for any List type
        if not value:
            return True
        # Check each element against the element type
        elem_type = get_args(expected_type)[0] if get_args(expected_type) else Any
        return all(is_valid_type(item, elem_type) for item in value)
    
    if get_origin(expected_type) in (tuple, Tuple):
        if not isinstance(value, tuple):
            return False
        # Get tuple element types
        elem_types = get_args(expected_type)
        # Handle empty tuples
        if not elem_types:
            return True
        # Handle variable-length tuples (Tuple[int, ...])
        if len(elem_types) == 2 and elem_types[1] is Ellipsis:
            return all(is_valid_type(item, elem_types[0]) for item in value)
        # Check each element against its expected type
        if len(value) != len(elem_types):
            return False
        return all(is_valid_type(item, elem_type) for item, elem_type in zip(value, elem_types))
    
    if get_origin(expected_type) in (dict, Dict, Mapping):
        if not isinstance(value, dict):
            return False
        # Empty dict is valid for any Dict type
        if not value:
            return True
        # Get key and value types
        key_type, val_type = get_args(expected_type) if len(get_args(expected_type)) == 2 else (Any, Any)
        # Check each key and value against their expected types
        return all(is_valid_type(k, key_type) and is_valid_type(v, val_type) for k, v in value.items())
    
    # Handle Path special case
    if expected_type is Path:
        return isinstance(value, Path)
    
    # Handle primitive types
    return isinstance(value, expected_type)


def assert_valid_conversion(value_str, expected_type):
    """Assert that converting value_str to expected_type produces a valid result."""
    result = TypeConverter.convert(value_str, expected_type)
    assert is_valid_type(result, expected_type), \
        f"Converted value {result} does not match expected type {expected_type}"
    return result


def test_type_converter_primitive_types():
    """Test conversion of primitive types."""
    # Test string conversion
    assert TypeConverter.convert("hello", str) == "hello"
    
    # Test integer conversion
    assert TypeConverter.convert("42", int) == 42
    
    # Test float conversion
    assert TypeConverter.convert("3.14", float) == 3.14
    
    # Test conversion from non-string input
    assert TypeConverter.convert(42, str) == "42"
    assert TypeConverter.convert(3.14, str) == "3.14"


def test_type_converter_boolean():
    """Test boolean conversions."""
    # Test various true values
    true_values = ['true', 'True', 'yes', 'y', '1', 't', 'YES', 'Y', 'T']
    for val in true_values:
        assert TypeConverter.convert(val, bool) is True
    
    # Test various false values
    false_values = ['false', 'False', 'no', 'n', '0', 'f', 'NO', 'N', 'F']
    for val in false_values:
        assert TypeConverter.convert(val, bool) is False
    
    # Test invalid boolean conversion
    with pytest.raises(ValueError):
        TypeConverter.convert("invalid", bool)
    
    with pytest.raises(ValueError):
        TypeConverter.convert("maybe", bool)
    
    # Test boolean conversion from non-string input
    assert TypeConverter.convert(1, bool) is True
    assert TypeConverter.convert(0, bool) is False


def test_type_converter_path():
    """Test Path type conversion."""
    # Test path conversion
    assert TypeConverter.convert("~/test", Path) == Path.home() / "test"
    assert TypeConverter.convert("/absolute/path", Path) == Path("/absolute/path")
    assert TypeConverter.convert("./relative/path", Path) == Path("./relative/path")
    assert TypeConverter.convert("../parent/path", Path) == Path("../parent/path")


def test_type_converter_list():
    """Test list conversions."""
    # JSON list
    assert TypeConverter.convert("[1, 2, 3]", List[int]) == [1, 2, 3]
    
    # Python literal list
    assert TypeConverter.convert("[1, 2, 3]", List[int]) == [1, 2, 3]
    
    # CSV list
    assert TypeConverter.convert("1, 2, 3", List[int]) == [1, 2, 3]
    assert TypeConverter.convert("1,2,3", List[int]) == [1, 2, 3]
    
    # Empty list
    assert TypeConverter.convert("[]", List[int]) == []
    assert TypeConverter.convert("", List[str]) == []
    
    # List with nested types
    assert TypeConverter.convert("[[1, 2], [3, 4]]", List[List[int]]) == [[1, 2], [3, 4]]
    
    # List with whitespace in CSV format
    assert TypeConverter.convert(" 1 , 2 , 3 ", List[int]) == [1, 2, 3]


def test_type_converter_list_with_union():
    """Test list conversions with Union types."""
    # Given a List[Union[int, str]], we might get any permutation of types
    # Option 1: Use the flexible validation approach
    result = assert_valid_conversion("[1, 2, 3]", List[Union[int, str]])
    assert len(result) == 3
    
    result = assert_valid_conversion("['1', '2', '3']", List[Union[int, str]])
    assert len(result) == 3
    
    result = assert_valid_conversion("[1, '2', 3]", List[Union[int, str]])
    assert len(result) == 3
    
    # Option 2: Check types directly
    result = TypeConverter.convert("[1, 2, 3]", List[Union[int, str]])
    assert isinstance(result, list)
    assert len(result) == 3
    assert all(isinstance(x, (int, str)) for x in result)
    
    result = TypeConverter.convert("['1', '2', '3']", List[Union[int, str]])
    assert isinstance(result, list)
    assert len(result) == 3
    assert all(isinstance(x, (int, str)) for x in result)
    
    result = TypeConverter.convert("[1, '2', 3]", List[Union[int, str]])
    assert isinstance(result, list)
    assert len(result) == 3
    assert all(isinstance(x, (int, str)) for x in result)
    
    # List with mixed types
    result = TypeConverter.convert("[1, '2', 3.0]", List[Union[int, str, float]])
    assert isinstance(result, list)
    assert len(result) == 3
    assert all(isinstance(x, (int, str, float)) for x in result)
    
    # List with boolean and numeric types
    result = TypeConverter.convert("[1, true, 3]", List[Union[int, bool]])
    assert isinstance(result, list)
    assert len(result) == 3
    assert all(isinstance(x, (int, bool)) for x in result)


def test_type_converter_dict():
    """Test dictionary conversions."""
    # JSON dict
    assert TypeConverter.convert('{"a": 1, "b": 2}', Dict[str, int]) == {"a": 1, "b": 2}
    
    # Python literal dict
    assert TypeConverter.convert("{'a': 1, 'b': 2}", Dict[str, int]) == {"a": 1, "b": 2}
    
    # Empty dict
    assert TypeConverter.convert("{}", Dict[str, int]) == {}
    
    # Nested dict
    assert TypeConverter.convert('{"a": {"b": 1, "c": 2}}', Dict[str, Dict[str, int]]) == {
        "a": {"b": 1, "c": 2}
    }
    
    # Dict with lists
    assert TypeConverter.convert('{"a": [1, 2], "b": [3, 4]}', Dict[str, List[int]]) == {
        "a": [1, 2],
        "b": [3, 4],
    }


def test_type_converter_dict_with_union():
    """Test dictionary conversions with Union types."""
    # Dict with Union values - Flexible validation
    result = assert_valid_conversion(
        '{"a": 1, "b": "2", "c": 3.0}', 
        Dict[str, Union[int, str, float]]
    )
    assert set(result.keys()) == {"a", "b", "c"}
    
    # Direct type checking
    result = TypeConverter.convert(
        '{"a": 1, "b": "2", "c": 3.0}', 
        Dict[str, Union[int, str, float]]
    )
    assert isinstance(result, dict)
    assert set(result.keys()) == {"a", "b", "c"}
    assert isinstance(result["a"], (int, str, float))
    assert isinstance(result["b"], (int, str, float))
    assert isinstance(result["c"], (int, str, float))


def test_type_converter_tuple():
    """Test tuple conversions."""
    # JSON tuple (as list)
    assert TypeConverter.convert('[1, "two", 3.0]', Tuple[int, str, float]) == (1, "two", 3.0)
    
    # Python literal tuple
    assert TypeConverter.convert('(1, "two", 3.0)', Tuple[int, str, float]) == (1, "two", 3.0)
    
    # CSV to tuple
    assert TypeConverter.convert("1, two, 3.0", Tuple[int, str, float]) == (1, "two", 3.0)
    
    # Variadic tuple (Tuple[int, ...])
    result = TypeConverter.convert("[1, 2, 3, 4, 5]", Tuple[int, ...])
    assert isinstance(result, tuple)
    assert len(result) == 5
    assert all(isinstance(x, int) for x in result)
    
    # Error on wrong number of elements
    with pytest.raises(ValueError):
        TypeConverter.convert("[1, 2]", Tuple[int, int, int])
    
    with pytest.raises(ValueError):
        TypeConverter.convert("[1, 2, 3, 4]", Tuple[int, int, int])


def test_type_converter_tuple_with_union():
    """Test tuple conversions with Union types."""
    # Tuple with Union types - Flexible validation
    result = assert_valid_conversion(
        '[1, "2", true]',
        Tuple[Union[int, float], Union[int, str], Union[bool, int]]
    )
    assert isinstance(result, tuple)
    assert len(result) == 3
    
    # Direct type checking
    result = TypeConverter.convert(
        '[1, "2", true]',
        Tuple[Union[int, float], Union[int, str], Union[bool, int]]
    )
    assert isinstance(result, tuple)
    assert len(result) == 3
    assert isinstance(result[0], (int, float))
    assert isinstance(result[1], (int, str))
    assert isinstance(result[2], (bool, int))


def test_type_converter_optional():
    """Test Optional type conversions."""
    # Optional int
    assert TypeConverter.convert(None, Optional[int]) is None
    assert TypeConverter.convert("42", Optional[int]) == 42
    
    # Optional list
    assert TypeConverter.convert(None, Optional[List[int]]) is None
    assert TypeConverter.convert("[1, 2, 3]", Optional[List[int]]) == [1, 2, 3]
    
    # Optional dict
    assert TypeConverter.convert(None, Optional[Dict[str, int]]) is None
    assert TypeConverter.convert('{"a": 1}', Optional[Dict[str, int]]) == {"a": 1}
    
    # Optional str
    assert TypeConverter.convert(None, Optional[str]) is None
    assert TypeConverter.convert("", Optional[str]) == ""
    
    # Optional with error handling
    with pytest.raises(ValueError):
        TypeConverter.convert("not-a-number", Optional[int])


def test_type_converter_union():
    """Test Union type conversions."""
    # Union of int and str - Flexible validation
    int_result = assert_valid_conversion("42", Union[int, str])
    str_result = assert_valid_conversion("hello", Union[int, str])
    
    # Direct type checking
    int_result = TypeConverter.convert("42", Union[int, str])
    assert isinstance(int_result, (int, str))
    
    str_result = TypeConverter.convert("hello", Union[int, str])
    assert isinstance(str_result, (int, str))
    
    # Union of int, float, and bool
    result1 = assert_valid_conversion("42", Union[int, float, bool])
    result2 = assert_valid_conversion("3.14", Union[int, float, bool])
    result3 = assert_valid_conversion("true", Union[int, float, bool])
    
    # Direct type checking
    result1 = TypeConverter.convert("42", Union[int, float, bool])
    assert isinstance(result1, (int, float, bool))
    
    result2 = TypeConverter.convert("3.14", Union[int, float, bool])
    assert isinstance(result2, (int, float, bool))
    
    result3 = TypeConverter.convert("true", Union[int, float, bool])
    assert isinstance(result3, (int, float, bool))
    
    # Union with optional
    assert TypeConverter.convert(None, Union[int, None]) is None
    int_or_none = TypeConverter.convert("42", Union[int, None])
    assert isinstance(int_or_none, (int, type(None)))
    
    # Union in containers
    result = assert_valid_conversion(
        '{"a": 1, "b": "hello"}', 
        Dict[str, Union[int, str]]
    )
    assert "a" in result and "b" in result
    
    # Failed Union conversion
    with pytest.raises(ValueError):
        TypeConverter.convert("not-a-number-or-path", Union[int, bool])


def test_type_converter_error_cases():
    """Test error cases for type conversion."""
    # Invalid conversion
    with pytest.raises(ValueError):
        TypeConverter.convert("not a number", int)
    
    with pytest.raises(ValueError):
        TypeConverter.convert("invalid", bool)
    
    with pytest.raises(ValueError):
        TypeConverter.convert("not-a-list", List[int])
    
    with pytest.raises(ValueError):
        TypeConverter.convert("not-a-dict", Dict[str, int])
    
    # Test container with wrong element type
    with pytest.raises(ValueError):
        TypeConverter.convert("[1, 2, 'a']", List[int])


def test_type_converter_none():
    """Test None value handling."""
    assert TypeConverter.convert(None, int) is None
    assert TypeConverter.convert(None, str) is None
    assert TypeConverter.convert(None, List[int]) is None
    assert TypeConverter.convert(None, Dict[str, int]) is None
    assert TypeConverter.convert(None, Tuple[int, str]) is None
    assert TypeConverter.convert(None, Path) is None
    assert TypeConverter.convert(None, bool) is None


def test_type_converter_complex_cases():
    """Test complex type conversions."""
    # Nested containers - Flexible validation
    result = assert_valid_conversion(
        '{"users": [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]}',
        Dict[str, List[Dict[str, Union[str, int]]]]
    )
    # Verify structure
    assert "users" in result
    assert isinstance(result["users"], list)
    assert len(result["users"]) == 2
    assert all("name" in user and "age" in user for user in result["users"])
    
    # Direct type checking
    result = TypeConverter.convert(
        '{"users": [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]}',
        Dict[str, List[Dict[str, Union[str, int]]]]
    )
    assert isinstance(result, dict)
    assert "users" in result
    assert isinstance(result["users"], list)
    assert len(result["users"]) == 2
    assert all("name" in user and "age" in user for user in result["users"])
    assert all(isinstance(user["name"], (str, int)) for user in result["users"])
    assert all(isinstance(user["age"], (str, int)) for user in result["users"])
    
    # List of Optional
    result = assert_valid_conversion(
        '[1, null, 3]',
        List[Optional[int]]
    )
    assert len(result) == 3
    assert result[0] == 1
    assert result[1] is None
    assert result[2] == 3


def test_type_converter_mapping():
    """Test Mapping type conversions."""
    # Mapping instead of Dict
    result = TypeConverter.convert(
        '{"a": 1, "b": 2}', 
        Mapping[str, int]
    )
    assert isinstance(result, dict)
    assert result == {"a": 1, "b": 2}
    
    # Nested Mapping
    result = TypeConverter.convert(
        '{"a": {"b": 1}}',
        Mapping[str, Mapping[str, int]]
    )
    assert isinstance(result, dict)
    assert isinstance(result["a"], dict)
    assert result == {"a": {"b": 1}}