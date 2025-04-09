"""
Tests for the update_info.py module.

These tests validate the functionality of the UpdateInfoNode class and related classes
that track command execution state.
"""
import pytest
import time
import logging
import uuid
from dataclasses import asdict
from typing import List, Dict, Any, Optional

from src.cli.shell.update_info import (
    UpdateInfoNode, 
    LogEntry, 
    ErrorInfo,
    LOG_DEBUG,
    LOG_INFO, 
    LOG_WARNING, 
    LOG_ERROR,
    LOG_CRITICAL
)

class TestLogEntry:
    @pytest.mark.parametrize("message,level,expected_level_name", [
        ("Test debug message", LOG_DEBUG, "DEBUG"),
        ("Test info message", LOG_INFO, "INFO"),
        ("Test warning message", LOG_WARNING, "WARNING"),
        ("Test error message", LOG_ERROR, "ERROR"),
        ("Test critical message", LOG_CRITICAL, "CRITICAL"),
    ])
    def test_log_entry_creation(self, message, level, expected_level_name):
        """Test creation of log entries with different levels."""
        log = LogEntry(message=message, level=level)
        
        assert log.message == message
        assert log.level == level
        assert expected_level_name in str(log)
        assert log.timestamp is not None
        
    def test_log_entry_default_level(self):
        """Test that log entries default to INFO level."""
        log = LogEntry(message="Default level test")
        assert log.level == LOG_INFO

    def test_log_entry_timestamp(self):
        """Test that timestamp is set correctly."""
        before = time.time()
        log = LogEntry(message="Timestamp test")
        after = time.time()
        
        assert before <= log.timestamp <= after


class TestErrorInfo:
    def test_error_info_creation(self):
        """Test creation of error info."""
        error = ErrorInfo(
            error_type="ValueError",
            message="Invalid value",
            traceback="Traceback (most recent call last):\n  File..."
        )
        
        assert error.error_type == "ValueError"
        assert error.message == "Invalid value"
        assert error.traceback is not None
        assert "ValueError: Invalid value" in str(error)
        
    def test_error_info_no_traceback(self):
        """Test error info without traceback."""
        error = ErrorInfo(
            error_type="KeyError",
            message="Key not found"
        )
        
        assert error.traceback is None


class TestUpdateInfoNode:
    def test_node_creation(self):
        """Test creating a node with defaults."""
        node = UpdateInfoNode(command="test-command")
        
        assert node.command == "test-command"
        assert node.parent is None
        assert isinstance(node.node_id, str)
        assert node.status == "pending"
        assert node.logs == []
        assert node.child_nodes == []
        assert node.output == {}
        assert node.error is None
        assert node.start_time is not None
        assert node.end_time is None
        
    def test_node_with_custom_id(self):
        """Test creating a node with a custom ID."""
        custom_id = str(uuid.uuid4())
        node = UpdateInfoNode(command="test", node_id=custom_id)
        
        assert node.node_id == custom_id
        
    def test_node_state_transitions(self):
        """Test node state transitions."""
        node = UpdateInfoNode(command="test")
        assert node.status == "pending"
        
        # Start the node
        node.start()
        assert node.status == "running"
        
        # Complete the node successfully
        node.complete(success=True)
        assert node.status == "completed"
        assert node.end_time is not None
        
        # Create a new node for failure case
        fail_node = UpdateInfoNode(command="failing-test")
        fail_node.start()
        fail_node.complete(success=False)
        assert fail_node.status == "failed"
        
        # Create a new node for cancellation case
        cancel_node = UpdateInfoNode(command="cancel-test")
        cancel_node.start()
        cancel_node.cancel()
        assert cancel_node.status == "cancelled"
        
    def test_execution_time(self):
        """Test execution time calculation."""
        node = UpdateInfoNode(command="timing-test")
        node.start()
        
        # For running node (end_time is None)
        time.sleep(0.01)  # Small delay
        running_time = node.get_execution_time()
        assert running_time > 0
        
        # For completed node (end_time is set)
        time.sleep(0.01)  # Small delay
        node.complete()
        completed_time = node.get_execution_time()
        
        assert completed_time > 0
        assert completed_time <= running_time + 0.1  # Allow for small timing differences
        
    def test_add_log(self):
        """Test adding logs to a node."""
        node = UpdateInfoNode(command="logging-test")
        
        # Add logs with different levels
        node.add_log("Debug message", LOG_DEBUG)
        node.add_log("Info message")  # Default level
        node.add_log("Warning message", LOG_WARNING)
        node.add_log("Error message", LOG_ERROR)
        
        assert len(node.logs) == 4
        assert node.logs[0].message == "Debug message"
        assert node.logs[0].level == LOG_DEBUG
        assert node.logs[1].level == LOG_INFO  # Default level
        assert node.logs[2].message == "Warning message"
        assert node.logs[3].message == "Error message"
        
    def test_add_output(self):
        """Test adding output values to a node."""
        node = UpdateInfoNode(command="output-test")
        
        # Add various output types
        node.add_output("string_value", "test")
        node.add_output("int_value", 123)
        node.add_output("list_value", [1, 2, 3])
        node.add_output("dict_value", {"key": "value"})
        
        assert node.output["string_value"] == "test"
        assert node.output["int_value"] == 123
        assert node.output["list_value"] == [1, 2, 3]
        assert node.output["dict_value"] == {"key": "value"}
        
    def test_set_error(self):
        """Test setting error info for a node."""
        node = UpdateInfoNode(command="error-test")
        
        # Set error
        node.set_error(
            error_type="RuntimeError",
            message="Something went wrong",
            traceback="Traceback..."
        )
        
        assert node.error is not None
        assert node.error.error_type == "RuntimeError"
        assert node.error.message == "Something went wrong"
        assert node.error.traceback == "Traceback..."
        assert node.status == "failed"  # Status should be set to failed
        
    def test_child_nodes(self):
        """Test creating and managing child nodes."""
        parent = UpdateInfoNode(command="parent-command")
        
        # Create children
        child1 = parent.create_child_node(command="child1")
        child2 = parent.create_child_node(command="child2")
        
        # Create grandchild
        grandchild = child1.create_child_node(command="grandchild")
        
        # Check parent-child relationships
        assert len(parent.child_nodes) == 2
        assert child1.parent == parent
        assert child2.parent == parent
        assert grandchild.parent == child1
        
        # Check commands are set correctly
        assert parent.child_nodes[0].command == "child1"
        assert parent.child_nodes[1].command == "child2"
        assert parent.child_nodes[0].child_nodes[0].command == "grandchild"
        
    def test_to_dict(self):
        """Test converting node to dictionary."""
        # Create a test hierarchy
        root = UpdateInfoNode(command="root")
        root.add_log("Root log")
        root.add_output("root_output", "value")
        
        child = root.create_child_node(command="child")
        child.add_log("Child log")
        
        # Convert to dict with children
        result = root.to_dict(include_children=True)
        
        # Check structure
        assert result["command"] == "root"
        assert result["status"] == "pending"
        assert len(result["logs"]) == 1
        assert result["logs"][0]["message"] == "Root log"
        assert result["output"]["root_output"] == "value"
        assert "parent" not in result  # Should not include parent (circular reference)
        assert len(result["child_nodes"]) == 1
        assert result["child_nodes"][0]["command"] == "child"
        assert "execution_time" in result
        
        # Convert to dict without children
        result_no_children = root.to_dict(include_children=False)
        assert "child_nodes" not in result_no_children
        
    def test_get_all_logs(self):
        """Test getting all logs from node hierarchy."""
        root = UpdateInfoNode(command="root", node_id="root-id")
        root.add_log("Root log 1")
        root.add_log("Root log 2")
        
        child1 = root.create_child_node(command="child1")
        child1.node_id = "child1-id"  # Set explicit ID for testing
        child1.add_log("Child1 log")
        
        child2 = root.create_child_node(command="child2")
        child2.node_id = "child2-id"
        child2.add_log("Child2 log")
        
        grandchild = child1.create_child_node(command="grandchild")
        grandchild.node_id = "grandchild-id"
        grandchild.add_log("Grandchild log")
        
        # Get all logs
        all_logs = root.get_all_logs()
        
        # Check structure
        assert len(all_logs) == 5  # Total 5 logs in the hierarchy
        
        # Check node associations
        node_ids = [node_id for node_id, _ in all_logs]
        assert "root-id" in node_ids
        assert "child1-id" in node_ids
        assert "child2-id" in node_ids
        assert "grandchild-id" in node_ids
        
        # Check messages from each node are present
        messages = [log.message for _, log in all_logs]
        assert "Root log 1" in messages
        assert "Root log 2" in messages
        assert "Child1 log" in messages
        assert "Child2 log" in messages
        assert "Grandchild log" in messages
        
    def test_find_node_by_id(self):
        """Test finding nodes by ID in a hierarchy."""
        root = UpdateInfoNode(command="root")
        child1 = root.create_child_node(command="child1")
        child2 = root.create_child_node(command="child2")
        grandchild1 = child1.create_child_node(command="grandchild1")
        
        # Store node IDs
        root_id = root.node_id
        child1_id = child1.node_id
        child2_id = child2.node_id
        grandchild1_id = grandchild1.node_id
        
        # Find nodes by ID
        assert root.find_node_by_id(root_id) == root
        assert root.find_node_by_id(child1_id) == child1
        assert root.find_node_by_id(child2_id) == child2
        assert root.find_node_by_id(grandchild1_id) == grandchild1
        
        # Search from middle of tree
        assert child1.find_node_by_id(root_id) is None  # Can't find parent
        assert child1.find_node_by_id(child1_id) == child1  # Can find self
        assert child1.find_node_by_id(grandchild1_id) == grandchild1  # Can find child
        assert child1.find_node_by_id(child2_id) is None  # Can't find sibling
        
        # Non-existent ID
        assert root.find_node_by_id("non-existent-id") is None
        
    def test_edge_cases(self):
        """Test various edge cases."""
        # Empty command
        node = UpdateInfoNode()
        assert node.command is None
        
        # Complete without start
        node = UpdateInfoNode(command="no-start")
        node.complete()
        assert node.status == "completed"
        
        # Cancel without start
        node = UpdateInfoNode(command="no-start-cancel")
        node.cancel()
        assert node.status == "cancelled"
        
        # To dict with circular reference - this should now work without recursion error
        parent = UpdateInfoNode(command="parent")
        child = parent.create_child_node(command="child")
        parent_dict = parent.to_dict()
        assert parent_dict["command"] == "parent"
        assert len(parent_dict["child_nodes"]) == 1
        
        child_dict = child.to_dict()
        assert child_dict["command"] == "child"
        assert "parent" not in child_dict  # Shouldn't include parent reference
        
        # Test handling a node with error
        error_node = UpdateInfoNode(command="error-node")
        error_node.set_error("TestError", "Test error message")
        error_dict = error_node.to_dict()
        assert error_dict["error"]["error_type"] == "TestError"
        assert error_dict["error"]["message"] == "Test error message"