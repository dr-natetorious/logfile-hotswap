"""
Editor view implementation with multiple panes.
"""
import asyncio
from typing import Dict, Any, Optional, List, Callable

from prompt_toolkit.application.current import get_app
from prompt_toolkit.layout import Layout
from prompt_toolkit.layout.containers import (
    HSplit, VSplit, Window, WindowAlign, FloatContainer, Float, ConditionalContainer, Container
)
from prompt_toolkit.layout.controls import FormattedTextControl
from prompt_toolkit.formatted_text import HTML, merge_formatted_text
from prompt_toolkit.layout.dimension import D
from prompt_toolkit.filters import Condition
from prompt_toolkit.key_binding import KeyBindings

from cli.views.base_view import BaseView
from cli.views.controls.command_input import CommandInput
from cli.views.controls.output_pane import OutputPane
from cli.views.controls.toolbox_pane import ToolboxPane
from cli.views.controls.status_bar import StatusBar
from cli.shell.update_info_node import UpdateInfoNode, LogLevel


class EditorView(BaseView):
    """Advanced editor-like view with multiple panes."""
    
    def __init__(self, shell):
        """Initialize the editor view.
        
        Args:
            shell: The parent shell instance
        """
        super().__init__(shell)
        
        # View state
        self.toolbox_visible = True
        
        # Register controls
        self.register_control("command_input", CommandInput, 
                             on_command=self._on_command_submitted)
        self.register_control("output_pane", OutputPane)
        self.register_control("toolbox_pane", ToolboxPane)
        self.register_control("status_bar", StatusBar)
        
        # Additional key bindings
        self._register_additional_key_bindings()
    
    def _register_additional_key_bindings(self):
        """Register additional key bindings for the editor view."""
        # Toggle toolbox visibility
        @self.kb.add('c-t')
        def _(event):
            self.toolbox_visible = not self.toolbox_visible
            # Update the app
            get_app().invalidate()
    
    def _on_command_submitted(self, command_str: str) -> None:
        """Handle command submission from the input control.
        
        Args:
            command_str: The command string to process
        """
        # Process the command
        update_info = self.process_command(command_str)
        
        # Focus the command input again
        command_input = self.get_control("command_input")
        if command_input:
            command_input.focus()
    
    def create_layout(self) -> Layout:
        """Create the prompt_toolkit layout for this view.
        
        Returns:
            Layout: The prompt_toolkit layout
        """
        # Get control containers
        command_input = self.get_control("command_input")
        output_pane = self.get_control("output_pane")
        toolbox_pane = self.get_control("toolbox_pane")
        status_bar = self.get_control("status_bar")
        
        # Create the layout
        toolbox_container = ConditionalContainer(
            content=toolbox_pane.get_container(),
            filter=Condition(lambda: self.toolbox_visible)
        )
        
        main_container = VSplit([
            # Left side - toolbox (conditional)
            ConditionalContainer(
                content=toolbox_container,
                filter=Condition(lambda: self.toolbox_visible)
            ),
            # Right side - command/output
            HSplit([
                # Command input at the top
                command_input.get_container(),
                # Output pane at the bottom
                output_pane.get_container(),
            ])
        ])
        
        # Root container with status bar
        root_container = HSplit([
            main_container,
            status_bar.get_container()
        ])
        
        return Layout(root_container)
    
    def update_ui_for_command_execution(self, update_info: UpdateInfoNode) -> None:
        """Update UI after command execution.
        
        Args:
            update_info: The update info node
        """
        # Update toolbox (especially variables)
        toolbox_pane = self.get_control("toolbox_pane")
        if toolbox_pane:
            toolbox_pane.update()
        
        # Update status bar
        status_bar = self.get_control("status_bar")
        if status_bar:
            status_bar.update()
    
    def setup(self) -> None:
        """Set up the view components and configuration."""
        super().setup()
        
        # Welcome message in output pane
        output_pane = self.get_control("output_pane")
        if output_pane:
            output_pane.write("Welcome to Server Management Shell - Editor View\n")
            output_pane.write('Type "help" for available commands, "exit" to quit, or "view simple" to switch to the simple view\n')
            output_pane.write('Press Ctrl+T to toggle the toolbox, use the tabs to switch toolbox views\n\n')
        
        # Set initial focus to command input
        command_input = self.get_control("command_input")
        if command_input:
            self.app.layout.focus(command_input.get_container())
    
    def get_prompt_text(self) -> str:
        """Generate the prompt text based on current context.
        
        Returns:
            str: The prompt text
        """
        if self.shell.context.get('current_server'):
            return f"{self.shell.context['current_server']}> "
        return "shell> "
    
    def cleanup(self) -> None:
        """Clean up resources before exiting or switching views."""
        super().cleanup()
        
        # Clean up each control
        for control in self.controls.values():
            if hasattr(control, 'cleanup'):
                control.cleanup()
