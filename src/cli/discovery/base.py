"""
Base class for discovery plugins.
"""
import abc
from typing import Dict, Any, List, Optional, Set


class DiscoveryPlugin(abc.ABC):
    """
    Abstract base class for all discovery plugins.
    """
    
    @abc.abstractmethod
    def get_name(self) -> str:
        """
        Returns the name of the discovery plugin.
        
        Returns:
            The plugin name
        """
        pass
    
    @abc.abstractmethod
    def get_description(self) -> str:
        """
        Returns a description of what the discovery plugin does.
        
        Returns:
            The plugin description
        """
        pass
    
    def get_dependencies(self) -> List[str]:
        """
        Returns a list of other discovery plugins that must run before this one.
        
        Returns:
            List of plugin names this plugin depends on
        """
        return []
    
    @abc.abstractmethod
    def discover(self, config_store, system_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Run the discovery process.
        
        Args:
            config_store: The configuration store to update
            system_names: Optional list of system names to limit discovery to
                         or None to discover all systems
        
        Returns:
            A dictionary with discovery results information
        """
        pass
    
    def get_tags_added(self) -> Set[str]:
        """
        Returns the set of tags this discovery plugin might add to systems.
        
        Returns:
            Set of tag names
        """
        return set()
    
    def get_roles_added(self) -> Set[str]:
        """
        Returns the set of roles this discovery plugin might add to systems.
        
        Returns:
            Set of role names
        """
        return set()
    
    def get_properties_added(self) -> Set[str]:
        """
        Returns the set of property names this discovery plugin might add to systems.
        
        Returns:
            Set of property names
        """
        return set()