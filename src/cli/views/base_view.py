"""
Base View class that defines the interface for all views.
"""
from abc import ABC, abstractmethod
from typing import Dict, List, Any, Optional, Type, Callable, TYPE_CHECKING
import asyncio

from prompt_toolkit.application import Application
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.containers import Container
from prompt_toolkit.styles import Style, merge_styles
from prompt_toolkit.formatted_text import HTML
from prompt_toolkit.filters import Condition

from controls.base import BaseControl
from cli.shell.update_info_node import UpdateInfoNode

if TYPE_CHECKING:
    from cli.shell.shell import ServerShell
    from cli.shell.pipeline import Pipeline


class BaseView(ABC):
    """Base class for all views in the application."""
    
    def __init__(self, shell: 'ServerShell'):
        """Initialize the view with a reference to the shell.
        
        Args:
            shell: The parent shell that owns this view
        """
        self.shell = shell
        self.running = False
        self.app = None
        
        # Controls registry
        self.controls: Dict[str, BaseControl] = {}
        
        # Current update info node (for displaying command output)
        self.current_update_info: Optional[UpdateInfoNode] = None
        
        # Key bindings
        self.kb = KeyBindings()
        self._register_default_key_bindings()
        
        # View-specific configuration
        self.config: Dict[str, Any] = {}
        
        # Event handlers
        self._event_handlers: Dict[str, List[Callable]] = {}
    
    def _register_default_key_bindings(self) -> None:
        """Register default key bindings for the view."""
        @self.kb.add('c-q')
        def _(event):
            """Quit the application."""
            self.stop()
            event.app.exit()
        
        @self.kb.add('c-s')
        def _(event):
            """Switch between views."""
            # Get the next view in the registry
            views = self.shell.view_manager.get_available_views()
            current_index = views.index(self.shell.view_manager.current_view) if self.shell.view_manager.current_view in views else 0
            next_index = (current_index + 1) % len(views)
            next_view = views[next_index]
            
            if self.shell.view_manager.switch_to(next_view):
                self.stop()
                event.app.exit()
    
    def register_control(self, name: str, control_class: Type[BaseControl], *args, **kwargs) -> BaseControl:
        """Register a control with the view.
        
        Args:
            name: The name of the control
            control_class: The control class to instantiate
            args, kwargs: Additional arguments to pass to the control constructor
            
        Returns:
            BaseControl: The created control instance
        """
        control = control_class(self, *args, **kwargs)
        control.id = name
        self.controls[name] = control
        return control
    
    def get_control(self, name: str) -> Optional[BaseControl]:
        """Get a control by name.
        
        Args:
            name: The name of the control
            
        Returns:
            Optional[BaseControl]: The control instance or None if not found
        """
        return self.controls.get(name)
    
    @abstractmethod
    def create_layout(self) -> Layout:
        """Create the prompt_toolkit layout for this view.
        
        Returns:
            Layout: The prompt_toolkit layout
        """
        pass
    
    def create_style(self) -> Style:
        """Create the prompt_toolkit style for this view.
        
        Returns:
            Style: The prompt_toolkit style
        """
        return Style.from_dict({
            # Base styles
            'output': '#ffffff',
            'input': '#ffffff',
            'status': '#ffffff bg:#333333',
            
            # Command input styles
            'command.prompt': '#ffcc00',
            'command.input': '#ffffff',
            
            # Toolbox styles
            'toolbox.header': 'bold #ffffff',
            'toolbox.category': 'bold #88ff88',
            'toolbox.command': '#88ff88',
            'toolbox.description': '#aaaaaa',
            'toolbox.variable.name': '#ffff88',
            'toolbox.variable.type': '#888888',
            'toolbox.variable.equals': '#ffffff',
            'toolbox.variable.value': '#aaaaff',
            
            # Tab styles
            'tab': '#888888',
            'tab.selected': 'bold #ffffff',
            
            # Status bar styles
            'status.key': 'bg:#555555 #ffffff',
            'status.server': 'bg:#007700 #ffffff',
            'status.view': 'bg:#000077 #ffffff',
            
            # Update info styles
            'update_info.command': 'bold #ffffff',
            'update_info.status.running': '#ffff00',
            'update_info.status.completed': '#00ff00',
            'update_info.status.failed': '#ff0000',
            'update_info.status.cancelled': '#888888',
            'update_info.time': '#888888',
            'update_info.log.debug': '#888888',
            'update_info.log.info': '#ffffff',
            'update_info.log.warning': '#ffff00',
            'update_info.log.error': '#ff0000',
            'update_info.log.critical': 'bg:#ff0000 #ffffff',
            
            # Completions menu
            'completion-menu': 'bg:#333333 #ffffff',
            'completion-menu.completion': 'bg:#333333 #ffffff',
            'completion-menu.completion.current': 'bg:#666666 #ffffff',
            'completion-menu.meta.completion': 'bg:#444444 #aaaaaa',
            'completion-menu.meta.completion.current': 'bg:#666666 #ffffff',
        })
    
    def setup(self) -> None:
        """Set up the view components and configuration."""
        # Set up pipeline event handlers
        self.shell.pipeline.register_event_handler('view_switched', 
                                                 lambda view_name: self.stop())
        
        # Create prompt_toolkit application
        layout = self.create_layout()
        style = self.create_style()
        
        self.app = Application(
            layout=layout,
            key_bindings=self.kb,
            full_screen=True,
            mouse_support=True,
            style=style
        )
    
    def run(self) -> None:
        """Run the view's main loop."""
        self.running = True
        
        if not self.app:
            self.setup()
        
        try:
            # Run the application
            self.app.run()
        finally:
            self.cleanup()
    
    async def run_async(self) -> None:
        """Run the view asynchronously."""
        self.running = True
        
        if not self.app:
            self.setup()
        
        try:
            # Run the application
            await self.app.run_async()
        finally:
            self.cleanup()
    
    def process_command(self, command_str: str) -> UpdateInfoNode:
        """Process a command string.
        
        Args:
            command_str: The command string to process
            
        Returns:
            UpdateInfoNode: The update info node for the command execution
        """
        # Execute the command using the pipeline
        result = self.shell.pipeline.execute(command_str)
        
        # Update the current update info node
        self.current_update_info = result
        
        # Update UI
        self.update_ui_for_command_execution(result)
        
        return result
    
    def update_ui_for_command_execution(self, update_info: UpdateInfoNode) -> None:
        """Update UI after command execution.
        
        Args:
            update_info: The update info node
        """
        # Default implementation does nothing
        # Override in subclasses to update specific controls
        pass
    
    def cleanup(self) -> None:
        """Clean up resources before exiting or switching views."""
        # Trigger cleanup event
        self.trigger_event('cleanup', self)
    
    def stop(self) -> None:
        """Stop the view's execution."""
        self.running = False
        
        # Trigger stop event
        self.trigger_event('stop', self)
    
    def get_prompt_text(self) -> str:
        """Generate the prompt text based on current context.
        
        Returns:
            str: The prompt text
        """
        if self.shell.context.get('current_server'):
            return f"{self.shell.context['current_server']}> "
        return "shell> "
    
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