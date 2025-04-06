"""
Data models for the system targeting and configuration.
"""
from enum import Enum
from typing import Dict, List, Optional, Set, Any, Union, Callable
from pydantic import BaseModel, Field

class ConnectionStatus(str, Enum):
    """Enum representing the connection status of a system."""
    DISCONNECTED = "disconnected"
    CONNECTING = "connecting"
    CONNECTED = "connected"
    ERROR = "error"


class ServerCredentials(BaseModel):
    """Model for server authentication credentials."""
    username: str
    password: Optional[str] = None
    key_path: Optional[str] = None
    use_keyring: bool = False


class RemoteAgent:
    """Class representing an active connection to a remote system."""
    
    def __init__(self, endpoint):
        self.endpoint = endpoint
        self._connection = None
    
    def execute(self, command: str) -> str:
        """
        Execute a command on the remote system.
        
        Args:
            command: The command to execute
            
        Returns:
            The command output
        """
        # This would be implemented with actual SSH/remote execution logic
        return f"Executed: {command}"
    
    def cleanup(self) -> str:
        """
        Perform cleanup operations on the remote system.
        
        Returns:
            The result of the cleanup
        """
        # This would be implemented with actual cleanup logic
        return "Cleanup completed"
    
    def disconnect(self) -> None:
        """Disconnect from the remote system."""
        self._connection = None
        self.endpoint.connection_status = ConnectionStatus.DISCONNECTED
        self.endpoint.agent = None


class ServerEndpoint(BaseModel):
    """Model for a server endpoint."""
    hostname: str
    port: int = 22
    credentials: Optional[ServerCredentials] = None
    connection_status: ConnectionStatus = ConnectionStatus.DISCONNECTED
    last_connected: Optional[str] = None
    error_message: Optional[str] = None
    
    def get_agent(self)->Optional[RemoteAgent]:
        return None
    
    def connect(self) -> RemoteAgent:
        """
        Connect to the server.
        
        Returns:
            A RemoteAgent object for interacting with the server
            
        Raises:
            Exception: If connection fails
        """
        try:
            # Update connection status
            self.connection_status = ConnectionStatus.CONNECTING
            
            # This would be implemented with actual connection logic
            # For now, we'll just create an agent
            agent = RemoteAgent(self)
            
            # Update connection status
            self.connection_status = ConnectionStatus.CONNECTED
            self.error_message = None
            self.agent = agent
            
            return agent
        except Exception as e:
            self.connection_status = ConnectionStatus.ERROR
            self.error_message = str(e)
            raise


class ConfigSetting(BaseModel):
    """Model for a configuration setting."""
    key: str
    value: Any
    description: Optional[str] = None


class Role(BaseModel):
    """Model for a system role."""
    name: str
    description: Optional[str] = None
    properties: Dict[str, Any] = Field(default_factory=dict)
    
    def add_property(self, key: str, value: Any) -> 'Role':
        """
        Add a property to the role.
        
        Args:
            key: Property key
            value: Property value
            
        Returns:
            Self for method chaining
        """
        self.properties[key] = value
        return self
    
    def get_property(self, key: str, default: Any = None) -> Any:
        """
        Get a property value.
        
        Args:
            key: Property key
            default: Default value if property doesn't exist
            
        Returns:
            The property value or default
        """
        return self.properties.get(key, default)


class ConfigSystem(BaseModel):
    """Model for a system in the configuration."""
    name: str
    description: Optional[str] = None
    local_settings: Dict[str, ConfigSetting] = Field(default_factory=dict)
    roles: Dict[str, Role] = Field(default_factory=dict)
    endpoint: ServerEndpoint
    tags: Set[str] = Field(default_factory=set)
    properties: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        validate_assignment = True
    
    def add_setting(self, key: str, value: Any, description: Optional[str] = None) -> 'ConfigSystem':
        """
        Add a setting to the system.
        
        Args:
            key: Setting key
            value: Setting value
            description: Optional description
            
        Returns:
            Self for method chaining
        """
        self.local_settings[key] = ConfigSetting(
            key=key,
            value=value,
            description=description
        )
        return self
    
    def get_setting(self, key: str, default: Any = None) -> Any:
        """
        Get a setting value.
        
        Args:
            key: Setting key
            default: Default value if setting doesn't exist
            
        Returns:
            The setting value or default
        """
        setting = self.local_settings.get(key)
        return setting.value if setting else default
    
    def remove_setting(self, key: str) -> 'ConfigSystem':
        """
        Remove a setting.
        
        Args:
            key: Setting key
            
        Returns:
            Self for method chaining
        """
        if key in self.local_settings:
            del self.local_settings[key]
        return self
    
    def add_role(self, name: str, description: Optional[str] = None) -> Role:
        """
        Add a role to the system.
        
        Args:
            name: Role name
            description: Optional description
            
        Returns:
            The created role
        """
        role = Role(name=name, description=description)
        self.roles[name] = role
        return role
    
    def remove_role(self, name: str) -> 'ConfigSystem':
        """
        Remove a role from the system.
        
        Args:
            name: Role name
            
        Returns:
            Self for method chaining
        """
        if name in self.roles:
            del self.roles[name]
        return self
    
    def has_role(self, name: str) -> bool:
        """
        Check if the system has a specific role.
        
        Args:
            name: Role name
            
        Returns:
            True if the system has the role, False otherwise
        """
        return name in self.roles
    
    def add_tag(self, tag: str) -> 'ConfigSystem':
        """
        Add a tag to the system.
        
        Args:
            tag: The tag to add
            
        Returns:
            Self for method chaining
        """
        self.tags.add(tag)
        return self
    
    def add_tags(self, tags: Set[str]) -> 'ConfigSystem':
        """
        Add multiple tags to the system.
        
        Args:
            tags: The tags to add
            
        Returns:
            Self for method chaining
        """
        self.tags.update(tags)
        return self
    
    def remove_tag(self, tag: str) -> 'ConfigSystem':
        """
        Remove a tag from the system.
        
        Args:
            tag: The tag to remove
            
        Returns:
            Self for method chaining
        """
        if tag in self.tags:
            self.tags.remove(tag)
        return self
    
    def has_tag(self, tag: str) -> bool:
        """
        Check if the system has a specific tag.
        
        Args:
            tag: The tag to check
            
        Returns:
            True if the system has the tag, False otherwise
        """
        return tag in self.tags
    
    def add_property(self, key: str, value: Any) -> 'ConfigSystem':
        """
        Add a property to the system.
        
        Args:
            key: Property key
            value: Property value
            
        Returns:
            Self for method chaining
        """
        self.properties[key] = value
        return self
    
    def get_property(self, key: str, default: Any = None) -> Any:
        """
        Get a property value.
        
        Args:
            key: Property key
            default: Default value if property doesn't exist
            
        Returns:
            The property value or default
        """
        return self.properties.get(key, default)
    
    def connect(self) -> RemoteAgent:
        """
        Connect to the system.
        
        Returns:
            A RemoteAgent for interacting with the system
        """
        return self.endpoint.connect()
    
    def is_connected(self) -> bool:
        """
        Check if the system is connected.
        
        Returns:
            True if the system is connected, False otherwise
        """
        return self.endpoint.connection_status == ConnectionStatus.CONNECTED


class ConfigStore(BaseModel):
    """Model for the entire configuration store."""
    systems: Dict[str, ConfigSystem] = Field(default_factory=dict)
    global_settings: Dict[str, ConfigSetting] = Field(default_factory=dict)
    
    class Config:
        validate_assignment = True
    
    def add_system(self, system: ConfigSystem) -> ConfigSystem:
        """
        Add a system to the store.
        
        Args:
            system: The system to add
            
        Returns:
            The added system
            
        Raises:
            ValueError: If a system with the same name already exists
        """
        if system.name in self.systems:
            raise ValueError(f"System with name '{system.name}' already exists")
        
        self.systems[system.name] = system
        return system
    
    def remove_system(self, name: str) -> bool:
        """
        Remove a system from the store.
        
        Args:
            name: The name of the system to remove
            
        Returns:
            True if the system was removed, False if it didn't exist
        """
        if name in self.systems:
            del self.systems[name]
            return True
        return False
    
    def get_system(self, name: str) -> Optional[ConfigSystem]:
        """
        Get a system by name.
        
        Args:
            name: The name of the system
            
        Returns:
            The system or None if it doesn't exist
        """
        return self.systems.get(name)
    
    def list_systems(self)->List[ConfigSystem]:
        return list(self.systems.values())

    def find_systems(self, predicate: Callable[[ConfigSystem], bool]) -> List[ConfigSystem]:
        """
        Find systems matching a predicate.
        
        Args:
            predicate: Function that takes a system and returns a boolean
            
        Returns:
            List of matching systems
        """
        return [system for system in self.systems.values() if predicate(system)]
    
    def filter_by_tags(self, tags: Set[str]) -> List[ConfigSystem]:
        """
        Filter systems by tags.
        
        Args:
            tags: Set of tags to filter by (systems must have ALL tags)
            
        Returns:
            List of matching systems
        """
        return self.find_systems(lambda system: tags.issubset(system.tags))
    
    def filter_by_role(self, role: str) -> List[ConfigSystem]:
        """
        Filter systems by role.
        
        Args:
            role: Role name that systems must have
            
        Returns:
            List of matching systems
        """
        return self.find_systems(lambda system: system.has_role(role))
    
    def filter_connected(self) -> List[ConfigSystem]:
        """
        Get all connected systems.
        
        Returns:
            List of connected systems
        """
        return self.find_systems(lambda system: system.is_connected())
    
    def add_global_setting(self, key: str, value: Any, description: Optional[str] = None) -> ConfigSetting:
        """
        Add a global setting.
        
        Args:
            key: Setting key
            value: Setting value
            description: Optional description
            
        Returns:
            The created setting
        """
        setting = ConfigSetting(key=key, value=value, description=description)
        self.global_settings[key] = setting
        return setting
    
    def get_global_setting(self, key: str, default: Any = None) -> Any:
        """
        Get a global setting value.
        
        Args:
            key: Setting key
            default: Default value if setting doesn't exist
            
        Returns:
            The setting value or default
        """
        setting = self.global_settings.get(key)
        return setting.value if setting else default
    
    def remove_global_setting(self, key: str) -> bool:
        """
        Remove a global setting.
        
        Args:
            key: Setting key
            
        Returns:
            True if the setting was removed, False if it didn't exist
        """
        if key in self.global_settings:
            del self.global_settings[key]
            return True
        return False