"""
Commands for running system discovery.
"""
import shlex
from typing import List, Optional
from .base import BaseCommand
from prompt_toolkit.completion import Completion
from discovery.base import DiscoveryError

class DiscoveryCommand(BaseCommand):
    """
    Commands for system discovery operations.
    """
    
    def get_command_names(self):
        return ['discover', 'discoveries']
    
    def execute(self, command_name, args_str, shell):
        if command_name == 'discover':
            return self._run_discovery(args_str, shell)
        elif command_name == 'discoveries':
            return self._list_discoveries(shell)
        
        return False
    
    def _run_discovery(self, args_str, shell):
        """Run discovery on systems."""
        args = self.parse_args(args_str)
        
        # Parse options
        plugins = []
        systems = []
        parallel = True
        
        i = 0
        while i < len(args):
            arg = args[i]
            if arg == '--plugins' or arg == '-p':
                if i + 1 < len(args):
                    plugins = args[i + 1].split(',')
                    i += 2
                else:
                    print("Error: Missing plugin names after --plugins")
                    return False
            elif arg == '--systems' or arg == '-s':
                if i + 1 < len(args):
                    systems = args[i + 1].split(',')
                    i += 2
                else:
                    print("Error: Missing system names after --systems")
                    return False
            elif arg == '--sequential' or arg == '-q':
                parallel = False
                i += 1
            else:
                print(f"Error: Unknown option: {arg}")
                print("Usage: discover [--plugins plugin1,plugin2] [--systems system1,system2] [--sequential]")
                return False
        
        # Run discovery
        try:
            # Set parallel mode if provided
            if shell.discovery_coordinator.parallel != parallel:
                shell.discovery_coordinator.parallel = parallel
            
            print(f"Running {'sequential' if not parallel else 'parallel'} discovery...")
            
            if plugins:
                print(f"Plugins: {', '.join(plugins)}")
            else:
                print("Running all available plugins")
            
            if systems:
                print(f"Systems: {', '.join(systems)}")
            else:
                print("Targeting all available systems")
            
            # Run discovery
            results = shell.discovery_coordinator.run_discovery(
                plugin_names=plugins if plugins else None,
                system_names=systems if systems else None
            )
            
            # Print results
            print("\nDiscovery Results:")
            print("=================")
            
            for plugin_name, plugin_results in results.items():
                print(f"\nPlugin: {plugin_name}")
                print("-" * (len(plugin_name) + 8))
                
                # Print key results first
                if "systems_checked" in plugin_results:
                    print(f"Systems checked: {plugin_results['systems_checked']}")
                    
                if "systems_updated" in plugin_results:
                    print(f"Systems updated: {plugin_results['systems_updated']}")
                
                # Print other results
                for key, value in plugin_results.items():
                    if key not in ["systems_checked", "systems_updated", "errors"]:
                        print(f"{key}: {value}")
                
                # Print errors if any
                if "errors" in plugin_results and plugin_results["errors"]:
                    print("\nErrors:")
                    for error in plugin_results["errors"]:
                        print(f"  {error['system']}: {error['error']}")
            
            print("\nDiscovery completed successfully")
            
            return True
        
        except DiscoveryError as e:
            print(f"Discovery error: {e}")
            return False
        except Exception as e:
            print(f"Error running discovery: {e}")
            return False
    
    def _list_discoveries(self, shell):
        """List available discovery plugins."""
        plugins = shell.discovery_coordinator.get_plugins()
        
        if not plugins:
            print("No discovery plugins available")
            return True
        
        print("\nAvailable Discovery Plugins:")
        print("===========================")
        
        for name, plugin in sorted(plugins.items()):
            print(f"\n{name}")
            print("-" * len(name))
            print(f"Description: {plugin.get_description()}")
            
            dependencies = plugin.get_dependencies()
            if dependencies:
                print(f"Dependencies: {', '.join(dependencies)}")
            
            tags = plugin.get_tags_added()
            if tags:
                print(f"Tags: {', '.join(tags)}")
            
            roles = plugin.get_roles_added()
            if roles:
                print(f"Roles: {', '.join(roles)}")
            
            properties = plugin.get_properties_added()
            if properties:
                print(f"Properties: {', '.join(properties)}")
        
        return True
    
    def get_completions(self, text):
        """
        Provide completions for discovery commands.
        """
        words = text.strip().split()
        
        if not words:
            # Complete command options
            yield Completion('--plugins', start_position=0, display='--plugins')
            yield Completion('-p', start_position=0, display='-p')
            yield Completion('--systems', start_position=0, display='--systems')
            yield Completion('-s', start_position=0, display='-s')
            yield Completion('--sequential', start_position=0, display='--sequential')
            yield Completion('-q', start_position=0, display='-q')
            return
        
        last_word = words[-1].lower()
        
        if len(words) > 1 and (words[-2] == '--plugins' or words[-2] == '-p'):
            # We're completing plugin names
            # This would be populated from actual plugins in a real implementation
            plugins = ['disk_space', 'mount_points']
            
            for plugin in plugins:
                if plugin.startswith(last_word):
                    yield Completion(
                        plugin,
                        start_position=-len(last_word),
                        display=plugin
                    )
        
        elif len(words) > 1 and (words[-2] == '--systems' or words[-2] == '-s'):
            # We're completing system names
            # This would be populated from actual systems in a real implementation
            systems = ['server1', 'server2', 'webserver', 'dbserver']
            
            for system in systems:
                if system.startswith(last_word):
                    yield Completion(
                        system,
                        start_position=-len(last_word),
                        display=system
                    )
        
        elif last_word.startswith('-'):
            # Complete command options
            options = {
                '--plugins': 'Specify which discovery plugins to run',
                '-p': 'Specify which discovery plugins to run (short form)',
                '--systems': 'Specify which systems to target',
                '-s': 'Specify which systems to target (short form)',
                '--sequential': 'Run discoveries sequentially instead of in parallel',
                '-q': 'Run discoveries sequentially (short form)'
            }
            
            for option, description in options.items():
                if option.startswith(last_word):
                    yield Completion(
                        option,
                        start_position=-len(last_word),
                        display=f"{option} - {description}"
                    )
    
    def get_help(self):
        return """
System discovery commands.

Usage:
  discover [options]    - Run discovery on target systems
    Options:
      --plugins, -p <plugins>  - Comma-separated list of discovery plugins to run
      --systems, -s <systems>  - Comma-separated list of systems to target
      --sequential, -q         - Run discoveries sequentially (not in parallel)
      
  discoveries           - List available discovery plugins

Examples:
  discover                              - Run all discoveries on all systems
  discover --plugins disk_space         - Run only disk space discovery
  discover -p disk_space,mount_points   - Run specific discoveries
  discover -s server1,server2           - Target specific systems
  discover -p disk_space -s server1 -q  - Run disk space discovery on server1 sequentially
"""