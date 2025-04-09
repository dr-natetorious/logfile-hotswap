"""
View registry for registering and managing view classes.

This module provides a centralized registry for view classes, making it
easy to define and register views.
"""
from typing import Dict, Type, List, Optional, Any, ClassVar, TYPE_CHECKING
import threading

if TYPE_CHECKING:
    from cli.views.base_view import BaseView


class ViewRegistry:
    """Registry for view classes using the singleton pattern."""
    
    # Singleton instance
    _instance: ClassVar[Optional['ViewRegistry']] = None
    _lock = threading.Lock()
    
    def __new__(cls):
        """Create or return the singleton instance."""
        with cls._lock:
            if cls._instance is None:
                cls._instance = super(ViewRegistry, cls).__new__(cls)
                # Initialize instance attributes
                cls._instance._views = {}
                cls._instance._default_view = None
            return cls._instance
    
    def __init__(self):
        """Initialize the registry if needed.
        
        This is called every time the class is instantiated, but since we're using
        the singleton pattern, we only need to initialize once.
        """
        # The initialization is done in __new__, so we don't need to do anything here
        pass
    
    def register(self, name: str, view_class: Type['BaseView'], default: bool = False) -> None:
        """Register a view class.
        
        Args:
            name: The name of the view
            view_class: The view class to register
            default: Whether this view should be the default
        """
        self._views[name] = view_class
        
        if default or self._default_view is None:
            self._default_view = name
    
    def get_view_class(self, name: str) -> Optional[Type['BaseView']]:
        """Get a view class by name.
        
        Args:
            name: The name of the view
            
        Returns:
            Optional[Type[BaseView]]: The view class or None if not found
        """
        return self._views.get(name)
    
    def get_default_view_name(self) -> Optional[str]:
        """Get the name of the default view.
        
        Returns:
            Optional[str]: The name of the default view or None if no views are registered
        """
        return self._default_view
    
    def get_available_views(self) -> List[str]:
        """Get a list of all registered view names.
        
        Returns:
            List[str]: The list of view names
        """
        return list(self._views.keys())
    
    def get_all_views(self) -> Dict[str, Type['BaseView']]:
        """Get all registered views.
        
        Returns:
            Dict[str, Type[BaseView]]: Dictionary of view names to view classes
        """
        return self._views.copy()  # Return a copy to prevent external modification


# Create a default registry instance
default_registry = ViewRegistry()


# Decorator for registering views
def register_view(name: str, default: bool = False, registry: Optional[ViewRegistry] = None):
    """Decorator for registering a view class.
    
    Args:
        name: The name of the view
        default: Whether this view should be the default
        registry: Optional registry to use, defaults to the default registry
        
    Returns:
        Function: The decorator function
    """
    registry = registry or default_registry
    
    def decorator(cls):
        registry.register(name, cls, default)
        return cls
    return decorator