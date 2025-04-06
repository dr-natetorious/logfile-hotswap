"""
Server navigation and management commands.
"""
from prompt_toolkit.completion import Completion
from .base import BaseCommand
from shell.exceptions import ServerConnectionError


class ServerCommand(BaseCommand):
    """
    Commands for server management and navigation.
    """
    
    def get_command_names(self):
        return ['connect', 'disconnect', 'servers', 'current']
    
    def execute(self, command_name, args_str, shell):
        args = self.parse_args(args_str)
        
        if command_name == 'connect':
            return self._connect_server(args, shell)
        elif command_name == 'disconnect':
            return self._disconnect_server(shell)
        elif command_name == 'servers':
            return self._list_servers(shell)
        elif command_name == 'current':
            return self._show_current_server(shell)
        
        return False
    
    def _connect_server(self, args, shell):
        """Connect to a server."""
        if not args:
            print("Error: Server name required")
            print("Usage: connect <server_name>")
            return False
        
        server_name = args[0]
        
        # In a real implementation, you would connect to the server here
        # For now, we'll just update the context
        try:
            print(f"Connecting to server: {server_name}")
            # Simulate connection
            shell.context['current_server'] = server_name
            print(f"Connected to {server_name}")
            return True
        except Exception as e:
            raise ServerConnectionError(f"Failed to connect to {server_name}: {e}")
    
    def _disconnect_server(self, shell):
        """Disconnect from the current server."""
        if not shell.context.get('current_server'):
            print("Not connected to any server")
            return False
        
        server_name = shell.context['current_server']
        print(f"Disconnecting from {server_name}")
        
        # In a real implementation, you would disconnect here
        shell.context['current_server'] = None
        print(f"Disconnected from {server_name}")
        return True
    
    def _list_servers(self, shell):
        """List available servers."""
        # In a real implementation, you would get this from a config or discovery
        servers = ['server1', 'server2', 'server3', 'production', 'staging']
        
        print("Available servers:")
        for server in servers:
            suffix = " (connected)" if server == shell.context.get('current_server') else ""
            print(f"  {server}{suffix}")
        
        return True
    
    def _show_current_server(self, shell):
        """Show the current server."""
        server = shell.context.get('current_server')
        if server:
            print(f"Currently connected to: {server}")
        else:
            print("Not connected to any server")
        
        return True
    
    def get_completions(self, text):
        """Provide completions for server commands."""
        # This would be populated from actual server list in a real implementation
        servers = ['server1', 'server2', 'server3', 'production', 'staging']
        
        word = text.strip().lower()
        for server in servers:
            if server.startswith(word):
                yield Completion(
                    server,
                    start_position=-len(word),
                    display=server
                )
    
    def get_help(self):
        return """
Server management and navigation commands.

Usage:
  connect <server>  - Connect to a server
  disconnect        - Disconnect from the current server
  servers           - List available servers
  current           - Show the currently connected server
"""