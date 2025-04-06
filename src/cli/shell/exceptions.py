"""
Custom exceptions for the shell application.
"""

class ShellException(Exception):
    """Base exception for all shell-related exceptions."""
    pass


class ShellExit(ShellException):
    """Exception to signal shell exit."""
    pass


class CommandError(ShellException):
    """Exception for command execution errors."""
    pass


class ServerConnectionError(ShellException):
    """Exception for server connection errors."""
    pass


class ServerNotFoundError(ShellException):
    """Exception for when a server is not found."""
    pass


class ServerAlreadyExistsError(ShellException):
    """Exception for when a server with the same name already exists."""
    pass


class ServerNotConnectedError(ServerConnectionError):
    """Exception for when a server is not connected."""
    pass


class DiskOperationError(ShellException):
    """Exception for disk operation errors."""
    pass


class DiscoveryError(ShellException):
    """Exception for discovery-related errors."""
    pass