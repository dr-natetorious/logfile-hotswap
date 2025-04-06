"""
Discovery Coordinator for managing and executing discovery plugins.
"""
import logging
import importlib
import pkgutil
import inspect
import concurrent.futures
from typing import Dict, List, Set, Optional, Any

from shell.exceptions import DiscoveryError
from .base import DiscoveryPlugin

logger = logging.getLogger(__name__)


class DiscoveryCoordinator:
    """
    Coordinates discovery plugins to gather information about systems.
    """
    
    def __init__(self, config_store, parallel=True, max_workers=5):
        """
        Initialize the discovery coordinator.
        
        Args:
            config_store: The configuration store to update
            parallel: Whether to run discoveries in parallel (default: True)
            max_workers: Maximum number of parallel workers (default: 5)
        """
        self.config_store = config_store
        self.plugins = {}
        self.parallel = parallel
        self.max_workers = max_workers
        self._load_plugins()
    
    def _load_plugins(self):
        """
        Dynamically load all discovery plugins.
        """
        # Import the discovery package
        import discovery
        
        # Reset plugins
        self.plugins = {}
        
        # Find all modules in the discovery package
        for _, name, is_pkg in pkgutil.iter_modules(discovery.__path__):
            if not is_pkg and name != 'base' and name != 'coordinator':
                try:
                    module = importlib.import_module(f'discovery.{name}')
                    
                    # Find all classes in the module that inherit from DiscoveryPlugin
                    for _, obj in inspect.getmembers(module, inspect.isclass):
                        if (issubclass(obj, DiscoveryPlugin) and 
                            obj != DiscoveryPlugin and 
                            not inspect.isabstract(obj)):
                            plugin_instance = obj()
                            plugin_name = plugin_instance.get_name()
                            self.plugins[plugin_name] = plugin_instance
                            logger.debug(f"Loaded discovery plugin: {plugin_name}")
                except Exception as e:
                    logger.error(f"Error loading discovery plugin {name}: {e}")
        
        # Also check for plugins registered in __init__.py
        if hasattr(discovery, 'register_plugins'):
            for plugin in discovery.register_plugins():
                plugin_name = plugin.get_name()
                self.plugins[plugin_name] = plugin
                logger.debug(f"Registered discovery plugin: {plugin_name}")
        
        logger.info(f"Loaded {len(self.plugins)} discovery plugins")
    
    def get_plugins(self) -> Dict[str, DiscoveryPlugin]:
        """
        Get all loaded discovery plugins.
        
        Returns:
            Dictionary of plugin_name -> plugin_instance
        """
        return self.plugins.copy()
    
    def _resolve_dependencies(self, plugin_names: Optional[List[str]] = None) -> List[str]:
        """
        Resolve plugin dependencies and return a correctly ordered list of plugins to run.
        
        Args:
            plugin_names: Optional list of plugin names to run, or None for all plugins
            
        Returns:
            Ordered list of plugin names respecting dependencies
            
        Raises:
            DiscoveryError: If circular dependencies are detected
        """
        if plugin_names is None:
            plugins_to_run = list(self.plugins.keys())
        else:
            plugins_to_run = plugin_names
        
        # Build dependency graph
        graph = {}
        for name in plugins_to_run:
            if name not in self.plugins:
                raise DiscoveryError(f"Discovery plugin not found: {name}")
            
            plugin = self.plugins[name]
            dependencies = [dep for dep in plugin.get_dependencies() if dep in plugins_to_run]
            graph[name] = dependencies
        
        # Topological sort (Kahn's algorithm)
        result = []
        no_deps = [name for name, deps in graph.items() if not deps]
        
        while no_deps:
            name = no_deps.pop(0)
            result.append(name)
            
            # Remove this node from the graph
            for deps in graph.values():
                if name in deps:
                    deps.remove(name)
            
            # Find new nodes with no dependencies
            no_deps.extend([n for n, deps in graph.items() if not deps and n not in result and n not in no_deps])
        
        # Check for circular dependencies
        if len(result) != len(graph):
            raise DiscoveryError("Circular dependencies detected in discovery plugins")
        
        return result
    
    def run_discovery(self, plugin_names: Optional[List[str]] = None,
                     system_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Run discovery plugins.
        
        Args:
            plugin_names: Optional list of plugin names to run, or None for all plugins
            system_names: Optional list of system names to limit discovery to
            
        Returns:
            Dictionary of plugin_name -> discovery results
            
        Raises:
            DiscoveryError: If a discovery plugin fails
        """
        # Resolve dependencies
        plugins_to_run = self._resolve_dependencies(plugin_names)
        
        # Results dictionary
        results = {}
        
        if self.parallel and len(plugins_to_run) > 1:
            # Run plugins in parallel if no interdependencies
            # Group plugins by dependency level
            levels = []
            remaining = set(plugins_to_run)
            
            while remaining:
                # Find plugins that can run at this level (no dependencies left)
                current_level = set()
                for name in list(remaining):
                    deps = set(self.plugins[name].get_dependencies())
                    if not deps.intersection(remaining):
                        current_level.add(name)
                
                if not current_level:
                    # This shouldn't happen due to dependency resolution above
                    raise DiscoveryError("Unable to resolve plugin execution order")
                
                levels.append(list(current_level))
                remaining -= current_level
            
            # Run each level in parallel
            for level in levels:
                level_results = {}
                
                with concurrent.futures.ThreadPoolExecutor(max_workers=min(len(level), self.max_workers)) as executor:
                    future_to_plugin = {
                        executor.submit(self._run_single_plugin, name, system_names): name
                        for name in level
                    }
                    
                    for future in concurrent.futures.as_completed(future_to_plugin):
                        plugin_name = future_to_plugin[future]
                        try:
                            level_results[plugin_name] = future.result()
                        except Exception as e:
                            logger.error(f"Discovery plugin {plugin_name} failed: {e}")
                            raise DiscoveryError(f"Discovery plugin {plugin_name} failed: {e}")
                
                # Update results with this level's discoveries
                results.update(level_results)
        else:
            # Run plugins sequentially
            for name in plugins_to_run:
                results[name] = self._run_single_plugin(name, system_names)
        
        return results
    
    def _run_single_plugin(self, plugin_name: str, system_names: Optional[List[str]]) -> Any:
        """
        Run a single discovery plugin.
        
        Args:
            plugin_name: Name of the plugin to run
            system_names: Optional list of system names to limit discovery to
            
        Returns:
            The discovery results
            
        Raises:
            Exception: If the discovery plugin fails
        """
        plugin = self.plugins[plugin_name]
        logger.info(f"Running discovery plugin: {plugin_name}")
        
        try:
            result = plugin.discover(self.config_store, system_names)
            logger.info(f"Discovery plugin {plugin_name} completed successfully")
            return result
        except Exception as e:
            logger.error(f"Discovery plugin {plugin_name} failed: {e}")
            raise
    
    def get_available_tags(self) -> Set[str]:
        """
        Get all tags that can be added by discovery plugins.
        
        Returns:
            Set of tag names
        """
        tags = set()
        for plugin in self.plugins.values():
            tags.update(plugin.get_tags_added())
        return tags
    
    def get_available_roles(self) -> Set[str]:
        """
        Get all roles that can be added by discovery plugins.
        
        Returns:
            Set of role names
        """
        roles = set()
        for plugin in self.plugins.values():
            roles.update(plugin.get_roles_added())
        return roles