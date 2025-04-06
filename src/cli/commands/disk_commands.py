"""
Disk space analysis and cleanup commands.
"""
from .base import BaseCommand
from shell.exceptions import DiskOperationError


class DiskCommand(BaseCommand):
    """
    Commands for disk space management and cleanup.
    """
    
    def get_command_names(self):
        return ['disk', 'cleanup', 'analyze']
    
    def execute(self, command_name, args_str, shell):
        args = self.parse_args(args_str)
        
        # Ensure we're connected to a server
        if not shell.context.get('current_server'):
            print("Error: Not connected to any server")
            print("You must connect to a server first: connect <server_name>")
            return False
        
        if command_name == 'disk':
            return self._show_disk_usage(args, shell)
        elif command_name == 'cleanup':
            return self._cleanup_disk(args, shell)
        elif command_name == 'analyze':
            return self._analyze_disk(args, shell)
        
        return False
    
    def _show_disk_usage(self, args, shell):
        """Show disk usage information."""
        server = shell.context['current_server']
        
        # Parse arguments for path
        path = args[0] if args else '/'
        
        try:
            print(f"Disk usage for {server}:{path}")
            # In a real implementation, you would get actual disk usage
            # For demonstration, we'll use mock data
            print("Filesystem      Size  Used Avail Use% Mounted on")
            print("/dev/sda1        50G   30G   20G  60% /")
            print("/dev/sdb1       100G   75G   25G  75% /data")
            return True
        except Exception as e:
            raise DiskOperationError(f"Failed to get disk usage: {e}")
    
    def _cleanup_disk(self, args, shell):
        """Clean up disk space."""
        server = shell.context['current_server']
        
        if not args:
            print("Error: Path required")
            print("Usage: cleanup <path> [--dry-run]")
            return False
        
        path = args[0]
        dry_run = '--dry-run' in args
        
        try:
            print(f"Cleaning up disk space on {server}:{path}")
            if dry_run:
                print("(Dry run mode - no files will be deleted)")
            
            # In a real implementation, you would clean up disk space here
            # For demonstration, we'll just print mock results
            print("Found 15 log files older than 30 days")
            print("Found 5 tmp directories not accessed in 90 days")
            
            if not dry_run:
                print("Deleted 500MB of old log files")
                print("Removed 2GB from unused tmp directories")
            else:
                print("Would delete approximately 2.5GB of data")
            
            return True
        except Exception as e:
            raise DiskOperationError(f"Failed to clean up disk: {e}")
    
    def _analyze_disk(self, args, shell):
        """Analyze disk usage for potential cleanup."""
        server = shell.context['current_server']
        
        if not args:
            print("Error: Path required")
            print("Usage: analyze <path>")
            return False
        
        path = args[0]
        
        try:
            print(f"Analyzing disk usage on {server}:{path}")
            
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
    
    def get_completions(self, text):
        """
        Provide path completions for disk commands.
        In a real implementation, this would use the actual filesystem.
        """
        common_paths = [
            '/', '/var', '/var/log', '/tmp', '/opt', '/home',
            '/var/log/application', '/var/cache'
        ]
        
        words = text.strip().split()
        
        if len(words) == 0 or (len(words) == 1 and not text.endswith(' ')):
            # First argument should be a path
            word = words[0] if words else ''
            for path in common_paths:
                if path.startswith(word):
                    yield Completion(
                        path,
                        start_position=-len(word),
                        display=path
                    )
        elif len(words) == 1 and text.endswith(' '):
            # For cleanup command, suggest --dry-run after the path
            yield Completion('--dry-run', start_position=0, display='--dry-run')
    
    def get_help(self):
        return """
Disk space management and cleanup commands.

Usage:
  disk <path>            - Show disk usage information for <path>
  cleanup <path> [flags] - Clean up disk space on <path>
    Flags:
      --dry-run          - Show what would be cleaned up without actually doing it
  analyze <path>         - Analyze disk usage and suggest cleanup targets

Note: You must be connected to a server to use these commands.
"""