"""
Update Information Node for tracking command execution state.

This module provides a structured way to represent the execution state of commands
in a hierarchical manner, allowing for easy display and navigation of command outputs.
"""
from typing import Dict, List, Any, Optional, Tuple, Union
from enum import Enum
import time
import uuid


class LogLevel(Enum):
    """Log level for log entries."""
    DEBUG = 0
    INFO = 1
    WARNING = 2
    ERROR = 3
    CRITICAL = 4

class LogEntry:
    """A log entry with timestamp, level, and message."""
    
    def __init__(self, message: str, level: LogLevel = LogLevel.INFO):
        """Initialize a log entry.
        
        Args:
            message: The log message
            level: The log level
        """
        self.timestamp = time.time()
        self.level = level
        self.message = message
    
    def __repr__(self) -> str:
        """Get string representation."""
        return f"[{self.level.name}] {self.message}"


class ErrorInfo:
    """Information about an error that occurred during command execution."""
    
    def __init__(
        self, 
        error_type: str, 
        message: str, 
        traceback: Optional[str] = None
    ):
        """Initialize error information.
        
        Args:
            error_type: Type of the error
            message: Error message
            traceback: Optional traceback
        """
        self.error_type = error_type
        self.message = message
        self.traceback = traceback
    
    def __repr__(self) -> str:
        """Get string representation."""
        return f"{self.error_type}: {self.message}"


class UpdateInfoNode:
    """
    A node in the update information tree.
    
    Each node represents a command or a subcommand execution, and contains
    logs, output, errors, and child nodes.
    """
    
    def __init__(
        self, 
        command: Optional[str] = None, 
        parent: Optional['UpdateInfoNode'] = None,
        node_id: Optional[str] = None
    ):
        """Initialize an update information node.
        
        Args:
            command: The command associated with this node
            parent: Parent node, if any
            node_id: Optional node ID, generated if not provided
        """
        self.node_id = node_id or str(uuid.uuid4())
        self.command = command
        self.parent = parent
        self.child_nodes: List[UpdateInfoNode] = []
        self.logs: List[LogEntry] = []
        self.output: Dict[str, Any] = {}
        self.error: Optional[ErrorInfo] = None
        self.start_time = time.time()
        self.end_time: Optional[float] = None
        self.status = "pending"  # pending, running, completed, failed, cancelled
    
    def add_log(self, message: str, level: LogLevel = LogLevel.INFO) -> None:
        """Add a log entry.
        
        Args:
            message: The log message
            level: The log level
        """
        self.logs.append(LogEntry(message, level))
    
    def add_output(self, key: str, value: Any) -> None:
        """Add an output value.
        
        Args:
            key: Output identifier
            value: Output value
        """
        self.output[key] = value
    
    def set_error(self, error_type: str, message: str, traceback: Optional[str] = None) -> None:
        """Set error information.
        
        Args:
            error_type: Type of the error
            message: Error message
            traceback: Optional traceback
        """
        self.error = ErrorInfo(error_type, message, traceback)
        self.status = "failed"
    
    def create_child_node(self, command: Optional[str] = None) -> 'UpdateInfoNode':
        """Create a child node.
        
        Args:
            command: The command associated with the child node
            
        Returns:
            UpdateInfoNode: The newly created child node
        """
        child = UpdateInfoNode(command, parent=self)
        self.child_nodes.append(child)
        return child
    
    def start(self) -> None:
        """Mark the node as running."""
        self.start_time = time.time()
        self.status = "running"
    
    def complete(self, success: bool = True) -> None:
        """Mark the node as completed.
        
        Args:
            success: Whether the command completed successfully
        """
        self.end_time = time.time()
        self.status = "completed" if success else "failed"
    
    def cancel(self) -> None:
        """Mark the node as cancelled."""
        self.end_time = time.time()
        self.status = "cancelled"
    
    def get_execution_time(self) -> float:
        """Get the execution time in seconds.
        
        Returns:
            float: Execution time in seconds
        """
        if self.end_time is None:
            return time.time() - self.start_time
        return self.end_time - self.start_time
    
    def to_dict(self, include_children: bool = True) -> Dict[str, Any]:
        """Convert the node to a dictionary.
        
        Args:
            include_children: Whether to include child nodes
            
        Returns:
            Dict[str, Any]: Dictionary representation of the node
        """
        result = {
            "node_id": self.node_id,
            "command": self.command,
            "status": self.status,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "execution_time": self.get_execution_time(),
            "logs": [{"level": log.level.name, "message": log.message, "timestamp": log.timestamp} for log in self.logs],
            "output": self.output,
            "error": None if self.error is None else {
                "error_type": self.error.error_type,
                "message": self.error.message,
                "traceback": self.error.traceback
            }
        }
        
        if include_children:
            result["child_nodes"] = [child.to_dict(include_children) for child in self.child_nodes]
        
        return result
    
    def get_all_logs(self) -> List[Tuple[str, LogEntry]]:
        """Get all logs including from child nodes.
        
        Returns:
            List[Tuple[str, LogEntry]]: List of (node_id, log_entry) tuples
        """
        result = [(self.node_id, log) for log in self.logs]
        
        for child in self.child_nodes:
            result.extend(child.get_all_logs())
        
        return result
    
    def find_node_by_id(self, node_id: str) -> Optional['UpdateInfoNode']:
        """Find a node by its ID.
        
        Args:
            node_id: The node ID to find
            
        Returns:
            Optional[UpdateInfoNode]: The found node or None
        """
        if self.node_id == node_id:
            return self
        
        for child in self.child_nodes:
            found = child.find_node_by_id(node_id)
            if found:
                return found
        
        return None
