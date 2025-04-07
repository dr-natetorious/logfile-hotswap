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
        
        if hasattr(origin_type,'__name__') and origin_type.__name__ == 'Mapping':
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
        
        # Handle Mapping and similar abstract types
        if expected_type in (typing.Mapping, typing.Dict) or typing.get_origin(expected_type) in (typing.Mapping, typing.Dict):
            # For Mapping types, use dict as the concrete implementation
            try:
                return cls._convert_container_type(value_str, 
                        typing.Dict[typing.get_args(expected_type)[0], typing.get_args(expected_type)[1]] 
                        if typing.get_args(expected_type) else typing.Dict)
            except Exception as e:
                raise ValueError(f"Cannot convert '{value_str}' to mapping/dictionary: {e}")
        
        # Generic type conversion
        try:
            return expected_type(value_str)
        except Exception as e:
            raise ValueError(f"Cannot convert '{value_str}' to {getattr(expected_type, '__name__', str(expected_type))}: {e}")
    
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
        # Handle empty string specially for lists
        origin_type = typing.get_origin(expected_type)
        if value_str == "" and origin_type in (list, typing.List):
            return []
        
        def _parse_json(value_str: str) -> typing.Any:
            """Parse value as JSON."""
            return json.loads(value_str)
        
        def _parse_python_literal(value_str: str) -> typing.Any:
            """Parse value using ast.literal_eval."""
            return ast.literal_eval(value_str)
        
        def _parse_csv(value_str: str) -> typing.List[str]:
            """Parse value as CSV."""
            return [item.strip() for item in str(value_str).split(',')]
        
        type_args = typing.get_args(expected_type)
        
        # Normalize container type
        # Convert abstract types like Mapping to concrete types like dict
        if origin_type in (typing.Mapping, typing.MutableMapping, typing.Collection):
            origin_type = dict

        elif hasattr(origin_type,'__name__') and origin_type.__name__ == 'Mapping':
            origin_type = dict
        
        # Try multiple parsing methods
        parsing_methods = [
            _parse_json,
            _parse_python_literal,
            _parse_csv
        ]
        
        for parser in parsing_methods:
            try:
                parsed_value = parser(value_str)
                
                # Validate the parsed value matches the expected container type
                # List expected but got dict or vice versa
                if origin_type in (list, typing.List) and not isinstance(parsed_value, (list, tuple)):
                    continue
                if origin_type in (dict, typing.Dict) and not isinstance(parsed_value, dict):
                    continue
                if origin_type in (tuple, typing.Tuple) and not isinstance(parsed_value, (list, tuple)):
                    continue
                
                # If no type arguments, return as-is
                if not type_args:
                    if origin_type in (tuple, typing.Tuple) and isinstance(parsed_value, list):
                        return tuple(parsed_value)
                    return parsed_value
                
                # Convert each element to the specified type
                if origin_type in (list, typing.List):
                    # Get the element type from type_args
                    elem_type = type_args[0] if type_args else str
                    
                    # If the element type is a Union, we need special handling for order sensitivity
                    elem_origin = typing.get_origin(elem_type)
                    if elem_origin is typing.Union:
                        # For each element, try each type in the Union
                        result = []
                        for item in parsed_value:
                            # First, if it's already the correct type, no need to convert
                            item_union_types = typing.get_args(elem_type)
                            if isinstance(item, tuple(t for t in item_union_types if isinstance(t, type))):
                                result.append(item)
                            else:
                                # Otherwise, convert using our normal conversion logic
                                result.append(cls.convert(item, elem_type))
                        return result
                    else:
                        # Normal list handling
                        return [cls.convert(item, elem_type) for item in parsed_value]
                
                if origin_type in (tuple, typing.Tuple):
                    # Check for variadic tuple (Tuple[int, ...])
                    if len(type_args) == 2 and type_args[1] is Ellipsis:
                        return tuple(cls.convert(item, type_args[0]) for item in parsed_value)
                    
                    # Ensure the number of elements matches
                    if len(parsed_value) != len(type_args):
                        raise ValueError(f"Expected {len(type_args)} elements, got {len(parsed_value)}")
                    
                    # Convert each element to its corresponding type
                    return tuple(
                        cls.convert(item, elem_type)
                        for item, elem_type in zip(parsed_value, type_args)
                    )
                
                if origin_type in (dict, typing.Dict):
                    # Ensure we have a dictionary
                    if not isinstance(parsed_value, dict):
                        raise ValueError(f"Expected a dictionary, got {type(parsed_value).__name__}")
                    
                    key_type, value_type = type_args if len(type_args) == 2 else (str, typing.Any)
                    
                    # Handle Union value types with order sensitivity
                    value_origin = typing.get_origin(value_type)
                    if value_origin is typing.Union:
                        result = {}
                        for k, v in parsed_value.items():
                            # Convert the key
                            converted_key = cls.convert(k, key_type)
                            
                            # For the value, if it's already a correct type, keep it
                            value_union_types = typing.get_args(value_type)
                            if isinstance(v, tuple(t for t in value_union_types if isinstance(t, type))):
                                result[converted_key] = v
                            else:
                                # Otherwise convert using normal Union conversion
                                result[converted_key] = cls.convert(v, value_type)
                        return result
                    else:
                        # Normal dict handling
                        return {
                            cls.convert(k, key_type): cls.convert(v, value_type)
                            for k, v in parsed_value.items()
                        }
                
            except (ValueError, TypeError, json.JSONDecodeError, SyntaxError) as e:
                continue
        
        raise ValueError(f"Cannot convert '{value_str}' to {getattr(origin_type, '__name__', str(origin_type))}")