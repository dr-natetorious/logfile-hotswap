import pytest
from pathlib import Path
from typing import List, Dict, Tuple, Optional, Union, Any, Mapping, Set

from src.cli.utils.type_converter import TypeConverter


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
    
    # List with mixed types
    assert TypeConverter.convert("[1, '2', 3.0]", List[Union[int, str, float]]) == [1, '2', 3.0]
    
    # Empty list
    assert TypeConverter.convert("[]", List[int]) == []
    assert TypeConverter.convert("", List[str]) == [""]
    
    # List with nested types
    assert TypeConverter.convert("[[1, 2], [3, 4]]", List[List[int]]) == [[1, 2], [3, 4]]
    
    # List with whitespace in CSV format
    assert TypeConverter.convert(" 1 , 2 , 3 ", List[int]) == [1, 2, 3]
    

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
    
    # Dict with mixed value types
    assert TypeConverter.convert(
        '{"a": 1, "b": "string", "c": 3.14}', 
        Dict[str, Union[int, str, float]]
    ) == {"a": 1, "b": "string", "c": 3.14}


def test_type_converter_tuple():
    """Test tuple conversions."""
    # JSON tuple (as list)
    assert TypeConverter.convert('[1, "two", 3.0]', Tuple[int, str, float]) == (1, "two", 3.0)
    
    # Python literal tuple
    assert TypeConverter.convert('(1, "two", 3.0)', Tuple[int, str, float]) == (1, "two", 3.0)
    
    # CSV to tuple
    assert TypeConverter.convert("1, two, 3.0", Tuple[int, str, float]) == (1, "two", 3.0)
    
    # Error on wrong number of elements
    with pytest.raises(ValueError):
        TypeConverter.convert("[1, 2]", Tuple[int, int, int])
    
    with pytest.raises(ValueError):
        TypeConverter.convert("[1, 2, 3, 4]", Tuple[int, int, int])


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
    # Union of int and str
    assert TypeConverter.convert("42", Union[int, str]) == 42
    assert TypeConverter.convert("hello", Union[int, str]) == "hello"
    
    # Union of int, float, and bool
    assert TypeConverter.convert("42", Union[int, float, bool]) == 42
    assert TypeConverter.convert("3.14", Union[int, float, bool]) == 3.14
    assert TypeConverter.convert("true", Union[int, float, bool]) is True
    
    # Union with optional
    assert TypeConverter.convert(None, Union[int, None]) is None
    assert TypeConverter.convert("42", Union[int, None]) == 42
    
    # Union in containers
    assert TypeConverter.convert(
        '{"a": 1, "b": "hello"}', 
        Dict[str, Union[int, str]]
    ) == {"a": 1, "b": "hello"}
    
    # Failed Union conversion
    with pytest.raises(ValueError):
        TypeConverter.convert("not-a-number-or-path", Union[int, Path])


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
    # Nested containers
    assert TypeConverter.convert(
        '{"users": [{"name": "Alice", "age": 30}, {"name": "Bob", "age": 25}]}',
        Dict[str, List[Dict[str, Union[str, int]]]]
    ) == {
        "users": [
            {"name": "Alice", "age": 30},
            {"name": "Bob", "age": 25}
        ]
    }
    
    # Tuple with Union types
    assert TypeConverter.convert(
        '[1, "two", 3.0, true]',
        Tuple[int, str, float, bool]
    ) == (1, "two", 3.0, True)
    
    # List of Optional
    assert TypeConverter.convert(
        '[1, null, 3]',
        List[Optional[int]]
    ) == [1, None, 3]


def test_type_converter_mapping():
    """Test Mapping type conversions."""
    # Mapping instead of Dict
    assert TypeConverter.convert(
        '{"a": 1, "b": 2}', 
        Mapping[str, int]
    ) == {"a": 1, "b": 2}
    
    # Nested Mapping
    assert TypeConverter.convert(
        '{"a": {"b": 1}}',
        Mapping[str, Mapping[str, int]]
    ) == {"a": {"b": 1}}