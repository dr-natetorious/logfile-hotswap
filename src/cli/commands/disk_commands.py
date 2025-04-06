"""
Disk space analysis and cleanup commands using enhanced parameter style.
"""
from pathlib import Path
from typing import List, Optional

from prompt_toolkit.completion import Completion

from .declarative import DeclarativeCommand, command, Parameter
from shell.exceptions import DiskOperationError


@command(name="disk")
class DiskUsageCommand(DeclarativeCommand):
    """
    Show disk usage information for a path.
    """
    path: Path = Parameter(position=0, mandatory=True,default=Path("/"), help="Path to the analyze")
    human: bool = True
    
    def execute_command(self, shell) -> bool:
        """Show disk usage information."""
        # Ensure we're connected to a server
        if not shell.context.get('current_server'):
            print("Error: Not connected to any server")
            print("You must connect to a server first: connect <server_name>")
            return False
            
        server = shell.context['current_server']
        
        try:
            print(f"Disk usage for {server}:{self.path}")
            print(f"Human-readable format: {self.human}")
            
            # In a real implementation, you would get actual disk usage
            # For demonstration, we'll use mock data
            print("Filesystem      Size  Used Avail Use% Mounted on")
            print("/dev/sda1        50G   30G   20G  60% /")
            print("/dev/sdb1       100G   75G   25G  75% /data")
            return True
        except Exception as e:
            raise DiskOperationError(f"Failed to get disk usage: {e}")


@command(name="cleanup")
class CleanupCommand(DeclarativeCommand):
    """
    Clean up disk space on a specified path.
    """
    path: Path
    dry_run: bool = False
    days: int = 30
    
    def execute_command(self, shell) -> bool:
        """Clean up disk space."""
        # Ensure we're connected to a server
        if not shell.context.get('current_server'):
            print("Error: Not connected to any server")
            print("You must connect to a server first: connect <server_name>")
            return False
            
        server = shell.context['current_server']
        
        try:
            print(f"Cleaning up disk space on {server}:{self.path}")
            if self.dry_run:
                print("(Dry run mode - no files will be deleted)")
            
            print(f"Looking for files older than {self.days} days")
            
            # In a real implementation, you would clean up disk space here
            # For demonstration, we'll just print mock results
            print(f"Found 15 log files older than {self.days} days")
            print("Found 5 tmp directories not accessed in 90 days")
            
            if not self.dry_run:
                print("Deleted 500MB of old log files")
                print("Removed 2GB from unused tmp directories")
            else:
                print("Would delete approximately 2.5GB of data")
            
            return True
        except Exception as e:
            raise DiskOperationError(f"Failed to clean up disk: {e}")


@command(name="analyze")
class AnalyzeDiskCommand(DeclarativeCommand):
    """
    Analyze disk usage for potential cleanup.
    """
    path: Path
    min_size: int = 100  # Minimum size in MB to report
    depth: int = 2       # Directory depth for analysis
    all: bool = False    # Show all directories regardless of size
    
    def execute_command(self, shell) -> bool:
        """Analyze disk usage for potential cleanup."""
        # Ensure we're connected to a server
        if not shell.context.get('current_server'):
            print("Error: Not connected to any server")
            print("You must connect to a server first: connect <server_name>")
            return False
            
        server = shell.context['current_server']
        
        try:
            print(f"Analyzing disk usage on {server}:{self.path}")
            if not self.all:
                print(f"Reporting directories larger than {self.min_size}MB")
            else:
                print("Reporting all directories regardless of size")
                
            print(f"Analyzing to a depth of {self.depth} levels")
            
            # In a real implementation, you would analyze disk usage here
            # For demonstration, we'll just print mock results
            print("Top directories by size:")
            print("  /var/log         5.2GB")
            print("  /opt/application 3.7GB")
            print("  /tmp             2.1GB")
            print("\nPotential cleanup targets:")
            print("  /var/log/old     2.1GB (log files older than 30 days)")
            print("  /tmp/cache       1.5GB (cache files not accessed in 14 days)")
            
            return True
        except Exception as e:
            raise DiskOperationError(f"Failed to analyze disk: {e}")