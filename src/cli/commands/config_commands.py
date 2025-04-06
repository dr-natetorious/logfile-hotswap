"""
Commands for managing configuration files using the declarative approach.
"""
import os
from pathlib import Path
from typing import Optional

from .declarative import DeclarativeCommand, command

@command(name="config")
class ConfigCommand(DeclarativeCommand):
    """
    Show current configuration path.
    """
    
    def execute_command(self, shell) -> bool:
        """Show current configuration path."""
        print(f"Current configuration path: {shell.config_store_manager.config_path}")
        return True

@command(name="load-config")
class LoadConfigCommand(DeclarativeCommand):
    """
    Load configuration from a file.
    """
    config_path: Path
    
    def execute_command(self, shell) -> bool:
        """Load configuration from a file."""
        # Check if file exists
        if not self.config_path.exists():
            print(f"Error: Config file not found: {self.config_path}")
            return False
        
        try:
            # Update config path
            shell.config_store_manager.config_path = str(self.config_path)
            
            # Load the configuration
            shell.config_store = shell.config_store_manager._load_configuration()
            
            # Update the discovery coordinator to use the new config store
            shell.discovery_coordinator.config_store = shell.config_store
            
            print(f"Configuration loaded from: {self.config_path}")
            print(f"Systems: {len(shell.config_store.systems)}")
            print(f"Global settings: {len(shell.config_store.global_settings)}")
            
            return True
        except Exception as e:
            print(f"Error loading configuration: {e}")
            return False


@command(name="save-config")
class SaveConfigCommand(DeclarativeCommand):
    """
    Save configuration to a file.
    """
    config_path: Optional[Path] = None
    
    def execute_command(self, shell) -> bool:
        """Save configuration to a file."""
        if self.config_path:
            # Save to specified path
            original_path = shell.config_store_manager.config_path
            shell.config_store_manager.config_path = str(self.config_path)
            
            try:
                # Save configuration
                shell.config_store_manager.save_configuration()
                print(f"Configuration saved to: {self.config_path}")
                return True
            except Exception as e:
                print(f"Error saving configuration: {e}")
                # Restore original path on error
                shell.config_store_manager.config_path = original_path
                return False
        else:
            # Save to current path
            try:
                shell.config_store_manager.save_configuration()
                print(f"Configuration saved to: {shell.config_store_manager.config_path}")
                return True
            except Exception as e:
                print(f"Error saving configuration: {e}")
                return False