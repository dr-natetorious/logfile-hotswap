
"""
Centralized type conversion utility leveraging typing module functions.
"""
import os
import ast
import json
import typing
from pathlib import Path

class TypeConverter:
    """
    A type converter that uses typing module functions for type handling.
    """
    
    @classmethod
    def convert(
        cls, 
        value: typing.Any, 
        expected_type: typing.Type
    ) -> typing.Any:
        """
        Convert a value to the expected type.
        
        :param value: Input value to convert
        :param expected_type: Expected type hint
        :return: Converted value
        """
        # Handle None values
        if value is None:
            return None
        
        # Convert to string if not already a string
        value_str = str(value)
        
        # Unwrap Optional and Union types
        origin_type = typing.get_origin(expected_type)
        type_args = typing.get_args(expected_type)
        
        # Handle Optional and Union types
        if origin_type is typing.Union:
            # Remove NoneType from Union
            type_args = [arg for arg in type_args if arg is not type(None)]
            
            # If only one type remains after removing NoneType
            if len(type_args) == 1:
                expected_type = type_args[0]
                origin_type = typing.get_origin(expected_type)
            else:
                # Try converting to each type in the Union
                for type_arg in type_args:
                    try:
                        return cls._convert_single_type(value_str, type_arg)
                    except (ValueError, TypeError):
                        continue
                
                # If no conversion worked, raise an error
                raise ValueError(f"Cannot convert '{value_str}' to any of {type_args}")
        
        # Handle container types
        if origin_type in (list, typing.List, tuple, typing.Tuple, dict, typing.Dict, typing.Mapping):
            return cls._convert_container_type(value_str, expected_type)
        
        # Convert the value
        return cls._convert_single_type(value_str, expected_type)
    
    @classmethod
    def _convert_single_type(cls, value_str: str, expected_type: typing.Type) -> typing.Any:
        """
        Convert a single value to a specific type.
        
        :param value_str: Input string value
        :param expected_type: Expected type
        :return: Converted value
        """
        # Special handling for specific types
        if expected_type == Path:
            return Path(os.path.expanduser(value_str))
        
        if expected_type == bool:
            # Flexible boolean conversion
            value_str_lower = value_str.lower()
            if value_str_lower in ('yes', 'true', 't', 'y', '1'):
                return True
            if value_str_lower in ('no', 'false', 'f', 'n', '0'):
                return False
            raise ValueError(f"Cannot convert '{value_str}' to boolean")
        
        if expected_type == str:
            return value_str
        
        # Generic type conversion
        try:
            return expected_type(value_str)
        except Exception as e:
            raise ValueError(f"Cannot convert '{value_str}' to {expected_type.__name__}: {e}")
    
    @classmethod
    def _convert_container_type(
        cls, 
        value_str: str, 
        expected_type: typing.Type
    ) -> typing.Any:
        """
        Convert a string value to a container type.
        
        :param value_str: Input string value
        :param expected_type: Expected container type
        :return: Converted container
        """
        def _parse_json(value_str: str) -> typing.Any:
            """Parse value as JSON."""
            return json.loads(value_str)
        
        def _parse_python_literal(value_str: str) -> typing.Any:
            """Parse value using ast.literal_eval."""
            return ast.literal_eval(value_str)
        
        def _parse_csv(value_str: str) -> typing.List[str]:
            """Parse value as CSV."""
            return [item.strip() for item in str(value_str).split(',')]
        
        origin_type = typing.get_origin(expected_type)
        type_args = typing.get_args(expected_type)
        
        # Try multiple parsing methods
        parsing_methods = [
            _parse_json,
            _parse_python_literal,
            _parse_csv
        ]
        
        for parser in parsing_methods:
            try:
                parsed_value = parser(value_str)
                
                # If no type arguments, return as-is
                if not type_args:
                    return parsed_value
                
                # Convert each element to the specified type
                if origin_type in (list, typing.List):
                    elem_type = type_args[0] if type_args else str
                    return [cls.convert(item, elem_type) for item in parsed_value]
                
                if origin_type in (tuple, typing.Tuple):
                    elem_types = type_args if type_args else [str] * len(parsed_value)
                    return tuple(
                        cls.convert(item, elem_type)
                        for item, elem_type in zip(parsed_value, elem_types)
                    )
                
                if origin_type in (dict, typing.Dict, typing.Mapping):
                    key_type, value_type = type_args if len(type_args) == 2 else (str, typing.Any)
                    return {
                        cls.convert(k, key_type): cls.convert(v, value_type)
                        for k, v in parsed_value.items()
                    }
                
            except (ValueError, TypeError):
                continue
        
        raise ValueError(f"Cannot convert '{value_str}' to {origin_type.__name__}")