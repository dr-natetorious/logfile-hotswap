"""
Commands for managing systems in the configuration store.
"""
import shlex
import json
from typing import List, Optional, Dict, Any, Set
from .base import BaseCommand
from prompt_toolkit.completion import Completion
from shell.exceptions import ServerNotFoundError, ServerAlreadyExistsError, ServerConnectionError


class SystemCommand(BaseCommand):
    """
    Commands for system management operations.
    """
    
    def get_command_names(self):
        return ['systems', 'add-system', 'remove-system', 'find-systems', 'show-system']
    
    def execute(self, command_name, args_str, shell):
        if command_name == 'systems':
            return self._list_systems(args_str, shell)
        elif command_name == 'add-system':
            return self._add_system(args_str, shell)
        elif command_name == 'remove-system':
            return self._remove_system(args_str, shell)
        elif command_name == 'find-systems':
            return self._find_systems(args_str, shell)
        elif command_name == 'show-system':
            return self._show_system(args_str, shell)
        
        return False
    
    def _list_systems(self, args_str, shell):
        """List all systems."""
        args = self.parse_args(args_str)
        
        # Get all systems
        systems = shell.config_store.systems.values()
        
        if not systems:
            print("No systems configured")
            return True
        
        # Display systems
        print("\nConfigured systems:")
        print("=================")
        
        for system in sorted(systems, key=lambda s: s.name):
            status = system.endpoint.connection_status.value
            tags = ", ".join(system.tags) if system.tags else "none"
            roles = ", ".join(system.roles.keys()) if system.roles else "none"
            
            print(f"\n{system.name} ({status})")
            print(f"  Hostname: {system.endpoint.hostname}:{system.endpoint.port}")
            if system.description:
                print(f"  Description: {system.description}")
            print(f"  Tags: {tags}")
            print(f"  Roles: {roles}")
        
        return True
    
    def _add_system(self, args_str, shell):
        """Add a new system."""
        args = self.parse_args(args_str)
        
        if len(args) < 2:
            print("Error: Missing required arguments")
            print("Usage: add-system <name> <hostname> [port] [description]")
            return False
        
        name = args[0]
        hostname = args[1]
        port = int(args[2]) if len(args) > 2 and args[2].isdigit() else 22
        description = args[3] if len(args) > 3 else None
        
        try:
            # Create the system
            system = shell.config_store_manager.create_system(
                name=name,
                hostname=hostname,
                port=port,
                description=description
            )
            
            print(f"System '{name}' added successfully")
            print(f"Hostname: {hostname}:{port}")
            if description:
                print(f"Description: {description}")
            
            return True
        
        except ServerAlreadyExistsError:
            print(f"Error: System '{name}' already exists")
            return False
        except Exception as e:
            print(f"Error adding system: {e}")
            return False
    
    def _remove_system(self, args_str, shell):
        """Remove a system."""
        args = self.parse_args(args_str)
        
        if not args:
            print("Error: System name required")
            print("Usage: remove-system <name>")
            return False
        
        name = args[0]
        
        try:
            # Check if the system exists
            if name not in shell.config_store.systems:
                print(f"Error: System '{name}' not found")
                return False
            
            # Remove the system
            if shell.config_store.remove_system(name):
                print(f"System '{name}' removed successfully")
                
                return True
            else:
                print(f"Error removing system '{name}'")
                return False
        
        except Exception as e:
            print(f"Error removing system: {e}")
            return False
    
    def _find_systems(self, args_str, shell):
        """Find systems by tags and/or roles."""
        args = self.parse_args(args_str)
        
        # Parse options
        tags = set()
        roles = set()
        
        i = 0
        while i < len(args):
            arg = args[i]
            if arg == '--tags' or arg == '-t':
                if i + 1 < len(args):
                    tags.update(args[i + 1].split(','))
                    i += 2
                else:
                    print("Error: Missing tag names after --tags")
                    return False
            elif arg == '--roles' or arg == '-r':
                if i + 1 < len(args):
                    roles.update(args[i + 1].split(','))
                    i += 2
                else:
                    print("Error: Missing role names after --roles")
                    return False
            else:
                print(f"Error: Unknown option: {arg}")
                print("Usage: find-systems [--tags tag1,tag2] [--roles role1,role2]")
                return False
        
        # If no filters provided, show usage
        if not tags and not roles:
            print("Error: No search criteria provided")
            print("Usage: find-systems [--tags tag1,tag2] [--roles role1,role2]")
            return False
        
        # Find matching systems
        matching_systems = []
        
        for system in shell.config_store.systems.values():
            # Check tags
            if tags and not tags.issubset(system.tags):
                continue
            
            # Check roles
            if roles and not all(role in system.roles for role in roles):
                continue
            
            matching_systems.append(system)
        
        # Display results
        if not matching_systems:
            print("No matching systems found")
            return True
        
        print(f"\nFound {len(matching_systems)} matching systems:")
        print("==============================")
        
        for system in sorted(matching_systems, key=lambda s: s.name):
            status = system.endpoint.connection_status.value
            sys_tags = ", ".join(system.tags) if system.tags else "none"
            sys_roles = ", ".join(system.roles.keys()) if system.roles else "none"
            
            print(f"\n{system.name} ({status})")
            print(f"  Hostname: {system.endpoint.hostname}:{system.endpoint.port}")
            if system.description:
                print(f"  Description: {system.description}")
            print(f"  Tags: {sys_tags}")
            print(f"  Roles: {sys_roles}")
        
        return True
    
    def _show_system(self, args_str, shell):
        """Show detailed information about a system."""
        args = self.parse_args(args_str)
        
        if not args:
            print("Error: System name required")
            print("Usage: show-system <name>")
            return False
        
        name = args[0]
        
        try:
            # Get the system
            system = shell.config_store.get_system(name)
            
            if not system:
                print(f"Error: System '{name}' not found")
                return False
            
            # Display system details
            print(f"\nSystem: {system.name}")
            print("=" * (len(system.name) + 8))
            
            print(f"Hostname: {system.endpoint.hostname}:{system.endpoint.port}")
            print(f"Status: {system.endpoint.connection_status.value}")
            
            if system.description:
                print(f"Description: {system.description}")
            
            # Tags
            print(f"\nTags: {', '.join(system.tags) if system.tags else 'none'}")
            
            # Roles
            if system.roles:
                print("\nRoles:")
                for role_name, role in system.roles.items():
                    print(f"  {role_name}")
                    if role.description:
                        print(f"    Description: {role.description}")
                    if role.properties:
                        print(f"    Properties: {json.dumps(role.properties, indent=6)}")
            else:
                print("\nRoles: none")
            
            # Settings
            if system.local_settings:
                print("\nSettings:")
                for key, setting in system.local_settings.items():
                    print(f"  {key}: {setting.value}")
                    if setting.description:
                        print(f"    Description: {setting.description}")
            else:
                print("\nSettings: none")
            
            # Properties
            if system.properties:
                print("\nProperties:")
                for key, value in system.properties.items():
                    if isinstance(value, (dict, list)):
                        print(f"  {key}: {json.dumps(value, indent=4)}")
                    else:
                        print(f"  {key}: {value}")
            else:
                print("\nProperties: none")
            
            return True
        
        except Exception as e:
            print(f"Error showing system: {e}")
            return False
    
    def get_completions(self, text):
        """
        Provide completions for system commands.
        """
        words = text.strip().split()
        
        if not words:
            return
        
        last_word = words[-1].lower()
        
        # TODO: Implement completions for system names, tags, roles, etc.
        # This would need access to the shell instance to get the real data
    
    def get_help(self):
        return """
System management commands.

Usage:
  systems              - List all configured systems
  
  add-system <name> <hostname> [port] [description]
                       - Add a new system to the configuration
                       
  remove-system <name> - Remove a system from the configuration
  
  find-systems [options]
                       - Find systems matching criteria
    Options:
      --tags, -t <tags>   - Comma-separated list of tags to match (all must match)
      --roles, -r <roles> - Comma-separated list of roles to match (all must match)
      
  show-system <name>   - Show detailed information about a system

Examples:
  systems
  add-system webserver web01.example.com 22 "Web server"
  remove-system oldserver
  find-systems --tags production,web --roles web_server
  show-system dbserver
"""