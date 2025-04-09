"""
Update Information Node for tracking command execution state.

This module provides a structured way to represent the execution state of commands
in a hierarchical manner, allowing for easy display and navigation of command outputs.
"""
from typing import Dict, List, Any, Optional, Tuple, Union
from dataclasses import dataclass, field, asdict
import logging
import time
import uuid

# Python logging module has constants but not a LogLevel enum
# Define helper names for clarity
LOG_DEBUG = logging.DEBUG
LOG_INFO = logging.INFO
LOG_WARNING = logging.WARNING
LOG_ERROR = logging.ERROR
LOG_CRITICAL = logging.CRITICAL


@dataclass
class LogEntry:
    """A log entry with timestamp, level, and message."""
    message: str
    level: int = logging.INFO
    timestamp: float = field(default_factory=time.time)
    
    def __repr__(self) -> str:
        """Get string representation."""
        return f"[{logging.getLevelName(self.level)}] {self.message}"


@dataclass
class ErrorInfo:
    """Information about an error that occurred during command execution."""
    error_type: str
    message: str
    traceback: Optional[str] = None
    
    def __repr__(self) -> str:
        """Get string representation."""
        return f"{self.error_type}: {self.message}"


@dataclass
class UpdateInfoNode:
    """
    A node in the update information tree.
    
    Each node represents a command or a subcommand execution, and contains
    logs, output, errors, and child nodes.
    """
    command: Optional[str] = None
    parent: Optional['UpdateInfoNode'] = None
    node_id: str = field(default_factory=lambda: str(uuid.uuid4()))
    child_nodes: List['UpdateInfoNode'] = field(default_factory=list)
    logs: List[LogEntry] = field(default_factory=list)
    output: Dict[str, Any] = field(default_factory=dict)
    error: Optional[ErrorInfo] = None
    start_time: float = field(default_factory=time.time)
    end_time: Optional[float] = None
    status: str = "pending"  # pending, running, completed, failed, cancelled
    
    def add_log(self, message: str, level: int = logging.INFO) -> None:
        """Add a log entry.
        
        Args:
            message: The log message
            level: The log level (use standard logging module levels)
        """
        self.logs.append(LogEntry(message=message, level=level))
    
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
        # Create a dict manually to avoid recursion issues with asdict()
        node_dict = {
            "node_id": self.node_id,
            "command": self.command,
            "status": self.status,
            "start_time": self.start_time,
            "end_time": self.end_time,
            "execution_time": self.get_execution_time(),
            "logs": [
                {
                    "level": logging.getLevelName(log.level),
                    "message": log.message,
                    "timestamp": log.timestamp
                } for log in self.logs
            ],
            "output": self.output.copy(),  # Create copy to avoid mutation
            "error": None if self.error is None else {
                "error_type": self.error.error_type,
                "message": self.error.message,
                "traceback": self.error.traceback
            }
        }
        
        # Handle child nodes based on parameter
        if include_children:
            node_dict["child_nodes"] = [child.to_dict(include_children) for child in self.child_nodes]
        
        return node_dict
    
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