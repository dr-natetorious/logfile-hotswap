"""
Mount points discovery plugin.
"""
from typing import Dict, Any, List, Optional, Set

from .base import DiscoveryPlugin


class MountPointsDiscovery(DiscoveryPlugin):
    """
    Discovery plugin for system mount points.
    """
    
    def get_name(self) -> str:
        return "mount_points"
    
    def get_description(self) -> str:
        return "Discovers mount points on target systems"
    
    def get_dependencies(self) -> List[str]:
        # This discovery has no dependencies
        return []
    
    def get_tags_added(self) -> Set[str]:
        return {"has_nfs", "has_local_storage"}
    
    def get_roles_added(self) -> Set[str]:
        return {"storage_server"}
    
    def get_properties_added(self) -> Set[str]:
        return {"mount_points", "nfs_mounts", "local_mounts"}
    
    def discover(self, config_store, system_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Discover mount points.
        
        Args:
            config_store: The configuration store to update
            system_names: Optional list of system names to limit discovery to
            
        Returns:
            Dictionary with discovery results
        """
        results = {
            "systems_checked": 0,
            "systems_updated": 0,
            "total_mounts_found": 0
        }
        
        # Get systems to check
        systems = []
        if system_names:
            # Only check specified systems
            for name in system_names:
                system = config_store.get_system(name)
                if system:
                    systems.append(system)
        else:
            # Check all systems
            systems = config_store.list_systems()
        
        results["systems_checked"] = len(systems)
        
        # Check each system
        for system in systems:
            # In a real implementation, this would connect to the system and check mount points
            # For now, we'll simulate some discovery
            
            try:
                # First, check if we're connected or can connect
                if not system.is_connected():
                    agent = system.connect()
                else:
                    agent = system.endpoint.agent
                
                # This would normally execute mount or df command
                # Here we'll just simulate mount points for demonstration
                
                # Simulate different mount points by system name
                if "web" in system.name.lower():
                    mount_points = ["/", "/var", "/var/www", "/var/log"]
                    nfs_mounts = []
                elif "db" in system.name.lower():
                    mount_points = ["/", "/var", "/var/lib/mysql", "/backup"]
                    nfs_mounts = ["/backup"]
                elif "storage" in system.name.lower():
                    mount_points = ["/", "/var", "/mnt/data1", "/mnt/data2", "/mnt/data3"]
                    nfs_mounts = []
                else:
                    mount_points = ["/", "/var", "/home"]
                    nfs_mounts = []
                
                local_mounts = [m for m in mount_points if m not in nfs_mounts]
                
                # Update system properties
                system.add_property("mount_points", mount_points)
                system.add_property("nfs_mounts", nfs_mounts)
                system.add_property("local_mounts", local_mounts)
                
                # Update tags and roles based on findings
                if nfs_mounts:
                    system.add_tag("has_nfs")
                
                system.add_tag("has_local_storage")
                
                if "storage" in system.name.lower() or len(mount_points) > 4:
                    system.add_role("storage_server", 
                                   "System acts as a storage server with multiple mount points")
                
                results["systems_updated"] += 1
                results["total_mounts_found"] += len(mount_points)
                
            except Exception as e:
                # Log the error but continue with other systems
                results.setdefault("errors", []).append({
                    "system": system.name,
                    "error": str(e)
                })
        
        return results
