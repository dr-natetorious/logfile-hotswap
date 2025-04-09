"""
Tests for the update_info_node module.
"""
import pytest
import time
from typing import Dict, Any
from src.cli.shell.update_info_node import UpdateInfoNode, LogLevel, LogEntry, ErrorInfo

class TestLogEntry:
    """Tests for the LogEntry class."""
    
    def test_log_entry_initialization(self):
        """Test creating a log entry."""
        # Test with default log level
        log_entry = LogEntry("Test message")
        assert log_entry.message == "Test message"
        assert log_entry.level == LogLevel.INFO
        assert isinstance(log_entry.timestamp, float)
        
        # Test with specific log level
        log_entry = LogEntry("Error message", LogLevel.ERROR)
        assert log_entry.message == "Error message"
        assert log_entry.level == LogLevel.ERROR
    
    def test_log_entry_representation(self):
        """Test the string representation of log entries."""
        log_entry = LogEntry("Debug message", LogLevel.DEBUG)
        assert str(log_entry) == "[DEBUG] Debug message"
        
        log_entry = LogEntry("Warning", LogLevel.WARNING)
        assert str(log_entry) == "[WARNING] Warning"


class TestErrorInfo:
    """Tests for the ErrorInfo class."""
    
    def test_error_info_initialization(self):
        """Test creating error info."""
        # Test with minimal parameters
        error_info = ErrorInfo("ValueError", "Invalid value")
        assert error_info.error_type == "ValueError"
        assert error_info.message == "Invalid value"
        assert error_info.traceback is None
        
        # Test with traceback
        error_info = ErrorInfo("RuntimeError", "Unexpected error", "Traceback info here")
        assert error_info.error_type == "RuntimeError"
        assert error_info.message == "Unexpected error"
        assert error_info.traceback == "Traceback info here"
    
    def test_error_info_representation(self):
        """Test the string representation of error info."""
        error_info = ErrorInfo("TypeError", "Expected int, got str")
        assert str(error_info) == "TypeError: Expected int, got str"


class TestUpdateInfoNode:
    """Tests for the UpdateInfoNode class."""
    
    def test_node_initialization(self):
        """Test creating an update info node."""
        # Test with minimal parameters
        node = UpdateInfoNode()
        assert node.command is None
        assert node.parent is None
        assert node.node_id is not None
        assert isinstance(node.node_id, str)
        assert len(node.node_id) > 0
        assert node.logs == []
        assert node.output == {}
        assert node.error is None
        assert node.status == "pending"
        assert isinstance(node.start_time, float)
        assert node.end_time is None
        assert node.child_nodes == []
        
        # Test with command and parent
        parent = UpdateInfoNode()
        node = UpdateInfoNode("test command", parent)
        assert node.command == "test command"
        assert node.parent == parent
        
        # Test with custom node ID
        node = UpdateInfoNode(node_id="custom-id")
        assert node.node_id == "custom-id"
    
    def test_add_log(self):
        """Test adding log entries."""
        node = UpdateInfoNode()
        
        # Add a log with default level
        node.add_log("Info message")
        assert len(node.logs) == 1
        assert node.logs[0].message == "Info message"
        assert node.logs[0].level == LogLevel.INFO
        
        # Add a log with specific level
        node.add_log("Warning message", LogLevel.WARNING)
        assert len(node.logs) == 2
        assert node.logs[1].message == "Warning message"
        assert node.logs[1].level == LogLevel.WARNING
    
    def test_add_output(self):
        """Test adding output values."""
        node = UpdateInfoNode()
        
        # Add simple output
        node.add_output("result", 42)
        assert node.output == {"result": 42}
        
        # Add another output
        node.add_output("text", "Hello")
        assert node.output == {"result": 42, "text": "Hello"}
        
        # Override an existing output
        node.add_output("result", "new value")
        assert node.output == {"result": "new value", "text": "Hello"}
    
    def test_set_error(self):
        """Test setting error information."""
        node = UpdateInfoNode()
        
        # Set an error
        node.set_error("ValueError", "Invalid input")
        assert node.error is not None
        assert node.error.error_type == "ValueError"
        assert node.error.message == "Invalid input"
        assert node.error.traceback is None
        assert node.status == "failed"
        
        # Set an error with traceback
        node.set_error("RuntimeError", "Unexpected error", "Traceback here")
        assert node.error.error_type == "RuntimeError"
        assert node.error.message == "Unexpected error"
        assert node.error.traceback == "Traceback here"
    
    def test_create_child_node(self):
        """Test creating child nodes."""
        parent = UpdateInfoNode("parent command")
        
        # Create a child node
        child = parent.create_child_node("child command")
        assert child.command == "child command"
        assert child.parent == parent
        assert child in parent.child_nodes
        assert len(parent.child_nodes) == 1
        
        # Create another child node
        another_child = parent.create_child_node("another child")
        assert another_child.command == "another child"
        assert another_child.parent == parent
        assert another_child in parent.child_nodes
        assert len(parent.child_nodes) == 2
    
    def test_node_status_management(self):
        """Test node status management."""
        node = UpdateInfoNode()
        assert node.status == "pending"
        
        # Start the node
        node.start()
        assert node.status == "running"
        
        # Complete with success
        node.complete(True)
        assert node.status == "completed"
        assert node.end_time is not None
        
        # Create another node and complete with failure
        node = UpdateInfoNode()
        node.start()
        node.complete(False)
        assert node.status == "failed"
        
        # Create another node and cancel
        node = UpdateInfoNode()
        node.start()
        node.cancel()
        assert node.status == "cancelled"
    
    def test_get_execution_time(self):
        """Test getting execution time."""
        node = UpdateInfoNode()
        
        # Execution time for running node
        start_time = time.time()
        node.start_time = start_time
        time.sleep(0.01)  # Small delay
        exec_time = node.get_execution_time()
        assert exec_time > 0
        assert exec_time < 1.0  # Should be a small value
        
        # Execution time for completed node
        node.start_time = start_time
        node.end_time = start_time + 0.5
        assert node.get_execution_time() == 0.5
    
    def test_to_dict(self):
        """Test converting a node to a dictionary."""
        node = UpdateInfoNode("test command")
        node.add_log("Log message")
        node.add_output("result", 42)
        child = node.create_child_node("child command")
        
        # Test with children
        node_dict = node.to_dict()
        assert node_dict["command"] == "test command"
        assert node_dict["status"] == "pending"
        assert "start_time" in node_dict
        assert "execution_time" in node_dict
        assert len(node_dict["logs"]) == 1
        assert node_dict["logs"][0]["message"] == "Log message"
        assert node_dict["output"] == {"result": 42}
        assert node_dict["error"] is None
        assert len(node_dict["child_nodes"]) == 1
        assert node_dict["child_nodes"][0]["command"] == "child command"
        
        # Test without children
        node_dict = node.to_dict(include_children=False)
        assert "child_nodes" not in node_dict
    
    def test_get_all_logs(self):
        """Test getting all logs including from child nodes."""
        parent = UpdateInfoNode("parent")
        parent.add_log("Parent log")
        
        child1 = parent.create_child_node("child1")
        child1.add_log("Child 1 log")
        
        child2 = parent.create_child_node("child2")
        child2.add_log("Child 2 log")
        
        grandchild = child1.create_child_node("grandchild")
        grandchild.add_log("Grandchild log")
        
        # Get all logs
        all_logs = parent.get_all_logs()
        assert len(all_logs) == 4
        
        # Check log messages (order may vary)
        log_messages = {log[1].message for log in all_logs}
        assert log_messages == {"Parent log", "Child 1 log", "Child 2 log", "Grandchild log"}
        
        # Check node IDs are included
        assert all(isinstance(log[0], str) for log in all_logs)
    
    def test_find_node_by_id(self):
        """Test finding a node by its ID."""
        parent = UpdateInfoNode("parent")
        child1 = parent.create_child_node("child1")
        child2 = parent.create_child_node("child2")
        grandchild = child1.create_child_node("grandchild")
        
        # Find existing nodes
        assert parent.find_node_by_id(parent.node_id) == parent
        assert parent.find_node_by_id(child1.node_id) == child1
        assert parent.find_node_by_id(child2.node_id) == child2
        assert parent.find_node_by_id(grandchild.node_id) == grandchild
        
        # Find from different starting points
        assert child1.find_node_by_id(grandchild.node_id) == grandchild
        assert child1.find_node_by_id(child2.node_id) is None
        
        # Find non-existent node
        assert parent.find_node_by_id("non-existent") is None