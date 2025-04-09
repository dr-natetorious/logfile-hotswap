"""
Manages different views and transitions between them.
"""
from typing import Dict, List, Any, Optional, Type, Callable, TYPE_CHECKING
import traceback

if TYPE_CHECKING:
    from cli.views.base_view import BaseView
    from cli.shell.shell import ServerShell
    from cli.views.view_registry import ViewRegistry


class ViewManager:
    """Manages different views and handles transitions between them."""
    
    def __init__(self, 
                 shell: 'ServerShell', 
                 view_registry: 'ViewRegistry',
                 default_view: Optional[str] = None):
        """Initialize the view manager.
        
        Args:
            shell: The parent shell instance
            view_registry: The view registry to use for view class lookup
            default_view: The default view to start with, or None to use the registry's default
        """
        self.shell = shell
        self.view_registry = view_registry
        self.instances: Dict[str, 'BaseView'] = {}
        self.current_view: Optional[str] = None
        self.default_view = default_view or view_registry.get_default_view_name() or "simple"
        self.view_history: List[str] = []
    
    def get_available_views(self) -> List[str]:
        """Get the names of all registered views.
        
        Returns:
            List[str]: List of view names
        """
        return self.view_registry.get_available_views()
    
    def switch_to(self, view_name: str) -> bool:
        """Switch to a different view.
        
        Args:
            view_name: The name of the view to switch to
        
        Returns:
            bool: True if switch was successful, False otherwise
        """
        if view_name not in self.view_registry.get_available_views():
            print(f"Error: View '{view_name}' not found")
            return False
        
        # Don't switch if we're already in the requested view
        if self.current_view == view_name:
            return True
        
        # Clean up current view if it exists
        if self.current_view and self.current_view in self.instances:
            try:
                self.instances[self.current_view].cleanup()
            except Exception as e:
                print(f"Warning: Error cleaning up view '{self.current_view}': {e}")
                traceback.print_exc()
        
        # Track view history
        if self.current_view:
            self.view_history.append(self.current_view)
            
            # Limit history size
            if len(self.view_history) > 10:
                self.view_history.pop(0)
        
        # Create the view instance if it doesn't exist
        if view_name not in self.instances:
            view_class = self.view_registry.get_view_class(view_name)
            if not view_class:
                print(f"Error: View class for '{view_name}' not found")
                return False
                
            try:
                self.instances[view_name] = view_class(self.shell)
                
                # Set up the view
                self.instances[view_name].setup()
            except Exception as e:
                print(f"Error: Failed to initialize view '{view_name}': {e}")
                traceback.print_exc()
                return False
        
        self.current_view = view_name
        return True
    
    def get_current_view(self) -> Optional['BaseView']:
        """Get the current view instance.
        
        Returns:
            Optional[BaseView]: The current view instance or None if no view is active
        """
        if not self.current_view or self.current_view not in self.instances:
            return None
        return self.instances[self.current_view]
    
    def go_back(self) -> bool:
        """Go back to the previous view.
        
        Returns:
            bool: True if successfully switched to a previous view, False otherwise
        """
        if not self.view_history:
            return False
            
        previous_view = self.view_history.pop()
        return self.switch_to(previous_view)
    
    def start(self) -> None:
        """Start the default view."""
        available_views = self.get_available_views()
        if not available_views:
            raise ValueError("No views registered")
        
        if self.default_view not in available_views:
            self.default_view = available_views[0]
        
        if not self.switch_to(self.default_view):
            raise ValueError(f"Failed to start default view '{self.default_view}'")
        
        # Run the current view
        view = self.get_current_view()
        if view:
            view.run()