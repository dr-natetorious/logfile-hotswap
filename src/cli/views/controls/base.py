"""
Base Control class for creating reusable UI components.
"""
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, Callable, List, TYPE_CHECKING
from prompt_toolkit.filters import Condition

if TYPE_CHECKING:
    from prompt_toolkit.layout.containers import Container
    from cli.shell.shell import ServerShell
    from cli.views.base_view import BaseView


class BaseControl(ABC):
    """Base class for all UI controls.
    
    Controls are reusable UI components that can be composed into views.
    Each control creates and manages a prompt_toolkit container.
    """
    
    def __init__(self, parent_view: 'BaseView'):
        """Initialize the control.
        
        Args:
            parent_view: The parent view that owns this control
        """
        self.parent_view = parent_view
        self._shell = parent_view.shell
        self._container = None
        self._visible = True
        self._id = None
        
        # Control state
        self.state: Dict[str, Any] = {}
        
        # Event handlers
        self._event_handlers: Dict[str, List[Callable]] = {}
    
    @property
    def shell(self) -> 'ServerShell':
        """Get the shell instance."""
        return self._shell
    
    @property
    def id(self) -> Optional[str]:
        """Get the control ID."""
        return self._id
    
    @id.setter
    def id(self, value: str):
        """Set the control ID."""
        self._id = value
    
    @property
    def visible(self) -> bool:
        """Get the control visibility."""
        return self._visible
    
    @visible.setter
    def visible(self, value: bool):
        """Set the control visibility."""
        self._visible = value
        self.trigger_event('visibility_changed', self._visible)
    
    @abstractmethod
    def create_container(self) -> 'Container':
        """Create and return the prompt_toolkit container for this control.
        
        Returns:
            Container: The prompt_toolkit container for this control
        """
        pass
    
    def get_container(self) -> 'Container':
        """Get the prompt_toolkit container for this control.
        
        Returns:
            Container: The prompt_toolkit container
        """
        if self._container is None:
            self._container = self.create_container()
        return self._container
    
    def get_visibility_condition(self) -> Condition:
        """Get a condition that determines if this control is visible.
        
        Returns:
            Condition: A prompt_toolkit condition for visibility
        """
        return Condition(lambda: self.visible)
    
    def update(self) -> None:
        """Update the control's content."""
        self.trigger_event('update', self)
    
    def register_event_handler(self, event_name: str, handler: Callable) -> None:
        """Register an event handler.
        
        Args:
            event_name: Name of the event
            handler: Handler function
        """
        if event_name not in self._event_handlers:
            self._event_handlers[event_name] = []
        self._event_handlers[event_name].append(handler)
    
    def unregister_event_handler(self, event_name: str, handler: Callable) -> None:
        """Unregister an event handler.
        
        Args:
            event_name: Name of the event
            handler: Handler function to remove
        """
        if event_name in self._event_handlers:
            if handler in self._event_handlers[event_name]:
                self._event_handlers[event_name].remove(handler)
    
    def trigger_event(self, event_name: str, *args, **kwargs) -> None:
        """Trigger an event.
        
        Args:
            event_name: Name of the event
            args, kwargs: Arguments to pass to handlers
        """
        if event_name in self._event_handlers:
            for handler in self._event_handlers[event_name]:
                handler(*args, **kwargs)
    
    def show(self) -> None:
        """Show the control."""
        self.visible = True
    
    def hide(self) -> None:
        """Hide the control."""
        self.visible = False
    
    def toggle_visibility(self) -> None:
        """Toggle the control's visibility."""
        self.visible = not self.visible
        
    def cleanup(self) -> None:
        """Clean up resources when control is no longer needed."""
        pass