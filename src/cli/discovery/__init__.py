"""
Discovery package for system discovery mechanisms.

This package contains plugins and tools for discovering
information about target systems.
"""

from .base import DiscoveryPlugin
from .coordinator import DiscoveryCoordinator
from .disk_space import DiskSpaceDiscovery
from .mount_points import MountPointsDiscovery

__all__ = [
    'DiscoveryPlugin',
    'DiscoveryCoordinator',
    'DiskSpaceDiscovery',
    'MountPointsDiscovery'
]

# This function can be used to manually register discovery plugins
def register_plugins():
    """
    Register discovery plugins manually.
    Useful for adding plugins that are not automatically discovered.
    
    Returns:
        List of plugin instances
    """
    return [
        DiskSpaceDiscovery(),
        MountPointsDiscovery()
    ]