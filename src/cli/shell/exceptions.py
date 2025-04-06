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


class DiskOperationError(ShellException):
    """Exception for disk operation errors."""
    pass