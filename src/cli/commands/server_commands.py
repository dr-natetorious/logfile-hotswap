"""
Server navigation and management commands using the declarative approach.
"""
from typing import Optional, List
from prompt_toolkit.completion import Completion
from .declarative import DeclarativeCommand, command, Parameter
from shell.exceptions import ServerConnectionError


@command(name="connect")
class ConnectCommand(DeclarativeCommand):
    """
    Connect to a server.
    """
    server_name: str = Parameter(position=0, mandatory=True, help="The server name")
    
    def execute_command(self, shell) -> bool:
        """Connect to the specified server."""
        try:
            print(f"Connecting to server: {self.server_name}")
            # Simulate connection
            shell.context['current_server'] = self.server_name
            print(f"Connected to {self.server_name}")
            return True
        except Exception as e:
            raise ServerConnectionError(f"Failed to connect to {self.server_name}: {e}")
    
    def get_completions(self, args_str):
        """Provide completions for server names."""
        # Override the base implementation to provide server name completions
        # This would be populated from actual server list in a real implementation
        servers = ['server1', 'server2', 'server3', 'production', 'staging']
        
        # If we haven't typed a full arg yet, provide completions
        if ' ' not in args_str and not args_str.endswith(' '):
            word = args_str.strip().lower()
            for server in servers:
                if server.startswith(word):
                    yield Completion(
                        server,
                        start_position=-len(word),
                        display=server
                    )


@command(name="disconnect")
class DisconnectCommand(DeclarativeCommand):
    """
    Disconnect from the current server.
    """
    
    def execute_command(self, shell) -> bool:
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


@command(name="servers")
class ListServersCommand(DeclarativeCommand):
    """
    List available servers.
    """
    
    def execute_command(self, shell) -> bool:
        """List available servers."""
        # In a real implementation, you would get this from a config or discovery
        servers = self._get_servers()
        
        print("Available servers:")
        for server in servers:
            suffix = " (connected)" if server == shell.context.get('current_server') else ""
            print(f"  {server}{suffix}")