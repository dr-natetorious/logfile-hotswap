"""
Views package for the CLI application.

This package provides different views for the application UI.
Views define the layout and interaction model for the application.
"""
from .view_registry import ViewRegistry, register_view, default_registry
from .base_view import BaseView
from .simple_view import SimpleView
from .editor_view import EditorView

# Register views with the default registry
register_view("simple", default=True)(SimpleView)
register_view("editor")(EditorView)


def get_default_registry():
    """Get the default view registry.
    
    Returns:
        ViewRegistry: The default view registry
    """
    return default_registry


def create_registry():
    """Create a new view registry.
    
    Returns:
        ViewRegistry: A new view registry instance
    """
    return ViewRegistry()

__all__ = [
    'BaseView',
    'SimpleView',
    'EditorView',
    'ViewRegistry',
    'register_view',
    'default_registry',
    'get_default_registry',
    'create_registry'
]