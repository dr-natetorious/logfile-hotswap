"""
Disk space discovery plugin.
"""
from typing import Dict, Any, List, Optional, Set

from .base import DiscoveryPlugin


class DiskSpaceDiscovery(DiscoveryPlugin):
    """
    Discovery plugin for disk space information.
    """
    
    def get_name(self) -> str:
        return "disk_space"
    
    def get_description(self) -> str:
        return "Discovers disk space usage on target systems"
    
    def get_dependencies(self) -> List[str]:
        # This discovery depends on mount points being discovered first
        return ["mount_points"]
    
    def get_tags_added(self) -> Set[str]:
        return {"low_disk_space", "high_disk_space"}
    
    def get_roles_added(self) -> Set[str]:
        return {"disk_cleanup_needed"}
    
    def get_properties_added(self) -> Set[str]:
        return {"disk_usage", "disk_free", "disk_total"}
    
    def discover(self, config_store, system_names: Optional[List[str]] = None) -> Dict[str, Any]:
        """
        Discover disk space information.
        
        Args:
            config_store: The configuration store to update
            system_names: Optional list of system names to limit discovery to
            
        Returns:
            Dictionary with discovery results
        """
        results = {
            "systems_checked": 0,
            "systems_updated": 0,
            "low_disk_space_found": 0
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
            # In a real implementation, this would connect to the system and check disk space
            # For now, we'll simulate some discovery
            
            try:
                # First, check if we're connected or can connect
                if not system.is_connected():
                    agent = system.connect()
                else:
                    agent = system.endpoint.agent
                
                # This would normally execute df command or similar
                # Here we'll just simulate disk usage for demonstration
                
                # Get mount points (should have been discovered by MountPointsDiscovery)
                mount_points = system.get_property("mount_points", [])
                
                disk_usage = {}
                low_space_detected = False
                
                for mount in mount_points:
                    # Simulate getting disk usage
                    total = 100  # GB
                    used = total * 0.75  # 75% used
                    free = total - used
                    
                    disk_usage[mount] = {
                        "total_gb": total,
                        "used_gb": used,
                        "free_gb": free,
                        "percent_used": used / total * 100
                    }
                    
                    # Check for low disk space
                    if used / total > 0.9:  # 90% used
                        low_space_detected = True
                
                # Update system properties
                system.add_property("disk_usage", disk_usage)
                system.add_property("disk_free", sum(info["free_gb"] for info in disk_usage.values()))
                system.add_property("disk_total", sum(info["total_gb"] for info in disk_usage.values()))
                
                # Update tags and roles based on findings
                if low_space_detected:
                    system.add_tag("low_disk_space")
                    system.add_role("disk_cleanup_needed", 
                                   "System needs disk cleanup due to low disk space")
                    results["low_disk_space_found"] += 1
                else:
                    system.add_tag("healthy_disk_space")
                
                results["systems_updated"] += 1
                
            except Exception as e:
                # Log the error but continue with other systems
                results.setdefault("errors", []).append({
                    "system": system.name,
                    "error": str(e)
                })
        
        return results