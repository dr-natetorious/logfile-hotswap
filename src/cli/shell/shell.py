"""
Core shell implementation for the server management tool.
"""
import sys
import traceback
from typing import Dict, Any, Optional

from .command_handler import CommandHandler
from .completer import ShellCompleter
from .exceptions import ShellExit
from .variable_manager import VariableManager
from .view_manager import ViewManager
from .pipeline import Pipeline
from .update_info_node import UpdateInfoNode

from ..views import default_registry as view_registry
from targeting.config_store import ConfigStoreManager
from discovery.coordinator import DiscoveryCoordinator


class ServerShell:
    """Main shell class that handles the REPL loop."""
    
    def __init__(self, config=None):
        """Initialize the shell with configuration."""
        self.config = config or {}
        self.running = False
        
        # Initialize components
        self.command_handler = CommandHandler()
        self.variable_manager = VariableManager()
        
        # Initialize the config store manager and store
        self.config_store_manager = ConfigStoreManager(
            config_path=self.config.get('config_path')
        )
        self.config_store = self.config_store_manager.get_store()
        
        # Initialize the discovery coordinator
        self.discovery_coordinator = DiscoveryCoordinator(
            self.config_store,
            parallel=self.config.get('parallel_discovery', True),
            max_workers=self.config.get('discovery_workers', 5)
        )
        
        # Create the pipeline for command execution
        self.pipeline = Pipeline(self)
        
        # Initialize the view manager with the view registry
        self.view_manager = ViewManager(
            self, 
            view_registry,
            default_view=self.config.get('default_view', 'simple')
        )
        
        # Current context (e.g., which server we're connected to)
        self.context = {
            'current_server': None,
        }
    
    def run(self):
        """Run the shell using the view system."""
        self.running = True
        
        # Start the view manager with the default view
        try:
            self.view_manager.start()
        except KeyboardInterrupt:
            print("\nInterrupted. Exiting shell.")
        except ShellExit as e:
            # Clean exit requested by command
            exit_code = getattr(e, 'code', 0)
            print(f"Exiting shell with code {exit_code}.")
            sys.exit(exit_code)
        except Exception as e:
            print(f"Error: {e}")
            traceback.print_exc()
        finally:
            self.running = False
            print("Exiting shell. Goodbye!")
    
    def exit_shell(self, exitcode=0):
        """Exit the shell.
        
        Args:
            exitcode: The exit code to return
        """
        # Raise ShellExit exception to signal the shell to exit
        raise ShellExit(exitcode)