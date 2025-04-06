"""
Commands for managing systems in the configuration store.
"""
import json
from typing import List, Optional, Dict, Any, Set
from pathlib import Path

from .declarative import DeclarativeCommand, command, Parameter

from shell.exceptions import ServerNotFoundError, ServerAlreadyExistsError, ServerConnectionError


@command(name="systems")
class ListSystemsCommand(DeclarativeCommand):
    """
    List all configured systems.
    """
    
    def execute_command(self, shell) -> bool:
        """List all systems."""
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


@command(name="add-system")
class AddSystemCommand(DeclarativeCommand):
    """
    Add a new system to the configuration.
    """
    hostname: str = Parameter(position=0, mandatory=True, help="The server name")
    name: str = Parameter(position=1, mandatory=False, help="Optional friendly label")
    port: int = 22
    description: Optional[str] = None
    
    def execute_command(self, shell) -> bool:
        """Add a new system."""
        try:
            # Create the system
            system = shell.config_store_manager.create_system(
                name=self.name,
                hostname=self.hostname,
                port=self.port,
                description=self.description
            )
            
            print(f"System '{self.name}' added successfully")
            print(f"Hostname: {self.hostname}:{self.port}")
            if self.description:
                print(f"Description: {self.description}")
            
            return True
        
        except ServerAlreadyExistsError:
            print(f"Error: System '{self.name}' already exists")
            return False
        except Exception as e:
            print(f"Error adding system: {e}")
            return False


@command(name="remove-system")
class RemoveSystemCommand(DeclarativeCommand):
    """
    Remove a system from the configuration.
    """
    name: str = Parameter(position=0, mandatory=True, help="The server name") 
    
    def execute_command(self, shell) -> bool:
        """Remove a system."""
        try:
            # Check if the system exists
            if self.name not in shell.config_store.systems:
                print(f"Error: System '{self.name}' not found")
                return False
            
            # Remove the system
            if shell.config_store.remove_system(self.name):
                print(f"System '{self.name}' removed successfully")
                return True
            else:
                print(f"Error removing system '{self.name}'")
                return False
        
        except Exception as e:
            print(f"Error removing system: {e}")
            return False


@command(name="find-systems")
class FindSystemsCommand(DeclarativeCommand):
    """
    Find systems matching criteria.
    """
    tags: Optional[List[str]] = None  # Comma-separated list of tags
    roles: Optional[List[str]] = None  # Comma-separated list of roles
    
    def execute_command(self, shell) -> bool:
        """Find systems by tags and/or roles."""
        # Parse tags and roles into sets
        tag_set = set(self.tags.split(',')) if self.tags else set()
        role_set = set(self.roles.split(',')) if self.roles else set()
        
        # If no filters provided, show usage
        if not tag_set and not role_set:
            print("Error: No search criteria provided")
            print("Usage: find-systems --tags=tag1,tag2 --roles=role1,role2")
            return False
        
        # Find matching systems
        matching_systems = []
        
        for system in shell.config_store.systems.values():
            # Check tags
            if tag_set and not tag_set.issubset(system.tags):
                continue
            
            # Check roles
            if role_set and not all(role in system.roles for role in role_set):
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


@command(name="show-system")
class ShowSystemCommand(DeclarativeCommand):
    """
    Show detailed information about a system.
    """
    name: str
    
    def execute_command(self, shell) -> bool:
        """Show detailed information about a system."""
        try:
            # Get the system
            system = shell.config_store.get_system(self.name)
            
            if not system:
                print(f"Error: System '{self.name}' not found")
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