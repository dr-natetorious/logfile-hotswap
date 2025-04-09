"""
Toolbox pane control for displaying available commands.
"""
from typing import Dict, List, Any, Optional, Callable, TYPE_CHECKING, Tuple
import time

from prompt_toolkit.application.current import get_app
from prompt_toolkit.key_binding import KeyBindings
from prompt_toolkit.layout.containers import HSplit, VSplit, Window, Container, ScrollablePane
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.layout.dimension import Dimension
from prompt_toolkit.widgets import Frame, Box, Label
from prompt_toolkit.mouse_events import MouseEvent, MouseEventType
from prompt_toolkit.formatted_text import merge_formatted_text

from .base import BaseControl

if TYPE_CHECKING:
    from .base import BaseView
    from cli.shell.shell import ServerShell

class ToolboxPane(BaseControl):
    """Toolbox pane for displaying available commands."""
    
    def __init__(self, parent_view: 'BaseView'):
        """Initialize the toolbox pane.
        
        Args:
            parent_view: The parent view
        """
        super().__init__(parent_view)
        
        # Set up state
        self.state.update({
            'selected_command': None,
            'command_groups': {},
            'filter_text': '',
            'refresh_time': 0
        })
        
        # Set up key bindings
        self.kb = KeyBindings()
        
        @self.kb.add('up')
        def _(event):
            self._select_previous_command()
            get_app().invalidate()
        
        @self.kb.add('down')
        def _(event):
            self._select_next_command()
            get_app().invalidate()
        
        @self.kb.add('enter')
        def _(event):
            self._execute_selected_command()
        
        # Initialize command list
        self._update_command_list()
    
    def _update_command_list(self) -> None:
        """Update the list of available commands."""
        commands = sorted(self.shell.command_handler.get_commands().keys())
        
        # Group commands by module/category
        command_groups: Dict[str, List[Dict[str, Any]]] = {}
        
        for cmd_name in commands:
            cmd_obj = self.shell.command_handler.get_commands()[cmd_name]
            
            # Extract module name from the command class
            module_name = cmd_obj.__class__.__module__.split('.')[-1]
            if module_name == 'commands':
                module_name = 'general'
                
            # Convert snake_case to Title Case
            category = ' '.join(word.capitalize() for word in module_name.replace('_commands', '').split('_'))
            
            if category not in command_groups:
                command_groups[category] = []
            
            # Get the first line of the command's docstring as a short description
            doc = cmd_obj.__doc__ or ""
            short_desc = doc.strip().split('\n')[0].strip() if doc else "No description"
            
            command_groups[category].append({
                'name': cmd_name,
                'description': short_desc,
                'category': category
            })
        
        # Sort commands within each group
        for category in command_groups:
            command_groups[category].sort(key=lambda cmd: cmd['name'])
        
        # Update state
        self.state['command_groups'] = command_groups
        self.state['refresh_time'] = time.time()
        
        # Set initial selection if none exists
        if self.state['selected_command'] is None and command_groups:
            first_category = sorted(command_groups.keys())[0]
            if command_groups[first_category]:
                self.state['selected_command'] = command_groups[first_category][0]['name']
    
    def _get_all_commands(self) -> List[Dict[str, Any]]:
        """Get a flat list of all commands.
        
        Returns:
            List[Dict[str, Any]]: List of command info dictionaries
        """
        all_commands = []
        for category, commands in self.state['command_groups'].items():
            all_commands.extend(commands)
        return sorted(all_commands, key=lambda cmd: cmd['name'])
    
    def _select_next_command(self) -> None:
        """Select the next command in the list."""
        commands = self._get_all_commands()
        if not commands:
            return
            
        current = self.state['selected_command']
        if current is None:
            # Select the first command
            self.state['selected_command'] = commands[0]['name']
            return
            
        # Find the current command index
        current_index = next((i for i, cmd in enumerate(commands) if cmd['name'] == current), -1)
        
        # Select the next command
        if current_index >= 0 and current_index < len(commands) - 1:
            self.state['selected_command'] = commands[current_index + 1]['name']
    
    def _select_previous_command(self) -> None:
        """Select the previous command in the list."""
        commands = self._get_all_commands()
        if not commands:
            return
            
        current = self.state['selected_command']
        if current is None:
            # Select the last command
            self.state['selected_command'] = commands[-1]['name']
            return
            
        # Find the current command index
        current_index = next((i for i, cmd in enumerate(commands) if cmd['name'] == current), -1)
        
        # Select the previous command
        if current_index > 0:
            self.state['selected_command'] = commands[current_index - 1]['name']
    
    def _execute_selected_command(self) -> None:
        """Execute the currently selected command."""
        if self.state['selected_command']:
            # Insert the command into the command input
            command_input = self.parent_view.get_control("command_input")
            if command_input:
                # Set the text in the command input
                command_input.set_text(self.state['selected_command'] + " ")
                # Focus the command input
                command_input.focus()
    
    def _handle_mouse_event(self, mouse_event: MouseEvent) -> None:
        """Handle mouse events for command selection.
        
        Args:
            mouse_event: The mouse event
        """
        if mouse_event.event_type == MouseEventType.MOUSE_UP:
            # Get the row where the click occurred
            commands = self._get_all_commands()
            if not commands:
                return
                
            # Calculate which command was clicked based on position
            # This is a simplified approach - in a real implementation
            # you would need to consider scrolling position
            row = mouse_event.position.y
            
            # Find which command is at this row
            for i, cmd in enumerate(commands):
                if i == row:
                    # Select this command
                    self.state['selected_command'] = cmd['name']
                    get_app().invalidate()
                    break
            
        elif mouse_event.event_type == MouseEventType.DOUBLE_CLICK:
            # Execute on double click
            self._execute_selected_command()
    
    def update(self) -> None:
        """Update the toolbox content."""
        self._update_command_list()
        super().update()
    
    def create_container(self) -> Container:
        """Create the toolbox container.
        
        Returns:
            Container: The toolbox container
        """
        def get_formatted_commands():
            """Generate formatted text for commands display."""
            result = []
            
            # Add title
            result.append(('class:toolbox.title', "Available Commands\n\n"))
            
            # Add each category
            for category in sorted(self.state['command_groups'].keys()):
                commands = self.state['command_groups'][category]
                
                # Skip empty categories
                if not commands:
                    continue
                
                # Add category header
                result.append(('class:toolbox.category', f"{category}\n"))
                
                # Add each command
                for cmd in commands:
                    # Check if selected
                    style = 'class:toolbox.command.selected' if cmd['name'] == self.state['selected_command'] else 'class:toolbox.command'
                    
                    # Add command
                    result.append((style, f"  {cmd['name']}\n"))
            
            return result
        
        # Create command list control
        command_list = FormattedTextControl(
            get_formatted_commands,
            focusable=True,
            key_bindings=self.kb,
            mouse_handler=self._handle_mouse_event
        )
        
        # Wrap in a scrollable container
        return Frame(
            title="Commands",
            body=ScrollablePane(
                Window(
                    content=command_list,
                    wrap_lines=False,
                    width=Dimension(preferred=30)
                )
            )
        )