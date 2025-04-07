"""
Configuration store manager for loading and saving targeting configuration.
"""
import os
import json
import logging
from typing import Optional, List, Dict, Any, Set
from datetime import datetime

from .config_models import (
    ConfigStore,
    ConfigSystem,
    ServerEndpoint,
    ServerCredentials,
    Role
)

logger = logging.getLogger(__name__)

class ConfigStoreManager:
    """
    Manages loading and saving of the configuration store.
    """
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the configuration store manager.
        
        Args:
            config_path: Path to the configuration file
        """
        self.config_path = config_path or os.path.expanduser("~/.server_shell/config.json")
        self.store = self._load_configuration()
    
    def _load_configuration(self) -> ConfigStore:
        """
        Load configuration from file.
        
        Returns:
            The loaded ConfigStore or a new one if loading fails
        """
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        
        if os.path.exists(self.config_path):
            try:
                with open(self.config_path, 'r') as f:
                    config_data = json.load(f)
                
                # Use Pydantic's parse_obj method to create the ConfigStore
                store = ConfigStore.parse_obj(config_data)
                logger.info(f"Loaded configuration with {len(store.systems)} systems")
                return store
            except Exception as e:
                logger.error(f"Error loading configuration: {e}")
        
        # Return a new store if loading fails or file doesn't exist
        return ConfigStore()
    
    def save_configuration(self) -> None:
        """Save configuration to file."""
        os.makedirs(os.path.dirname(self.config_path), exist_ok=True)
        
        try:
            # Convert to dict and save as JSON
            config_data = self.store.model_dump_json()#exclude={'systems': {'__all__': {'endpoint': {'agent'}}}})
            
            with open(self.config_path, 'w') as f:
                f.write(config_data)
            
            logger.info(f"Saved configuration with {len(self.store.systems)} systems")
        except Exception as e:
            logger.error(f"Error saving configuration: {e}")
    
    def create_system(self, name: str, hostname: str, port: int = 22, 
                     description: Optional[str] = None,
                     username: Optional[str] = None,
                     password: Optional[str] = None,
                     key_path: Optional[str] = None,
                     use_keyring: bool = False) -> ConfigSystem:
        """
        Create and add a new system to the store.
        
        Args:
            name: System name
            hostname: Server hostname
            port: Server port
            description: Optional system description
            username: Optional username for credentials
            password: Optional password for credentials
            key_path: Optional SSH key path for credentials
            use_keyring: Whether to use the system keyring for credentials
            
        Returns:
            The created system
            
        Raises:
            ValueError: If a system with the same name already exists
        """
        # Create credentials if any credential info is provided
        credentials = None
        if username:
            credentials = ServerCredentials(
                username=username,
                password=password,
                key_path=key_path,
                use_keyring=use_keyring
            )
        
        # Create the endpoint
        endpoint = ServerEndpoint(
            hostname=hostname,
            port=port,
            credentials=credentials
        )
        
        # Create the system
        system = ConfigSystem(
            name=name,
            description=description,
            endpoint=endpoint
        )
        
        # Add to the store
        try:
            self.store.add_system(system)
            return system
        except ValueError as e:
            raise
    
    def get_store(self) -> ConfigStore:
        """
        Get the configuration store.
        
        Returns:
            The configuration store
        """
        return self.store