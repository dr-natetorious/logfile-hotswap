"""
Commands for managing configuration files.
"""
import os
import shlex
from .base import BaseCommand
from prompt_toolkit.completion import Completion


class ConfigCommand(BaseCommand):
    """
    Commands for loading and saving configuration files.
    """
    
    def get_command_names(self):
        return ['config', 'load-config', 'save-config']
    
    def execute(self, command_name, args_str, shell):
        if command_name == 'config':
            return self._show_config(args_str, shell)
        elif command_name == 'load-config':
            return self._load_config(args_str, shell)
        elif command_name == 'save-config':
            return self._save_config(args_str, shell)
        
        return False
    
    def _show_config(self, args_str, shell):
        """Show current configuration path."""
        print(f"Current configuration path: {shell.config_store_manager.config_path}")
        return True
    
    def _load_config(self, args_str, shell):
        """Load configuration from a file."""
        args = self.parse_args(args_str)
        
        if not args:
            print("Error: Config file path required")
            print("Usage: load-config <path>")
            return False
        
        config_path = os.path.expanduser(args[0])
        
        # Check if file exists
        if not os.path.exists(config_path):
            print(f"Error: Config file not found: {config_path}")
            return False
        
        try:
            # Update config path
            shell.config_store_manager.config_path = config_path
            
            # Load the configuration
            shell.config_store = shell.config_store_manager._load_configuration()
            
            # Update the discovery coordinator to use the new config store
            shell.discovery_coordinator.config_store = shell.config_store
            
            print(f"Configuration loaded from: {config_path}")
            print(f"Systems: {len(shell.config_store.systems)}")
            print(f"Global settings: {len(shell.config_store.global_settings)}")
            
            return True
        except Exception as e:
            print(f"Error loading configuration: {e}")
            return False
    
    def _save_config(self, args_str, shell):
        """Save configuration to a file."""
        args = self.parse_args(args_str)
        
        if args:
            # Save to specified path
            config_path = os.path.expanduser(args[0])
            
            # Update config path
            original_path = shell.config_store_manager.config_path
            shell.config_store_manager.config_path = config_path
            
            try:
                # Save configuration
                shell.config_store_manager.save_configuration()
                print(f"Configuration saved to: {config_path}")
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
    
    def get_completions(self, text):
        """
        Provide completions for config commands.
        """
        if text.startswith("./") or text.startswith("/") or text.startswith("~"):
            # Path completion
            # This would be improved with actual path completion in a real implementation
            return
    
    def get_help(self):
        return """
Configuration file management commands.

Usage:
  config              - Show current configuration path
  
  load-config <path>  - Load configuration from a file
                        This replaces the current configuration with the loaded one
                        
  save-config [path]  - Save configuration to a file
                        If path is not specified, saves to the current config path

Examples:
  config
  load-config ~/.server_shell/production.json
  save-config ~/.server_shell/backup.json
  save-config
"""