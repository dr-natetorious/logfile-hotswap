"""
Shell module for the server management tool.
Contains the core shell implementation, command handler, and related utilities.
"""

from .shell import ServerShell
from .command_handler import CommandHandler
from .completer import ShellCompleter
from .exceptions import ShellException, ShellExit, CommandError