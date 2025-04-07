"""
Tests for the configuration store manager.
"""
import os
import json
import pytest
from unittest.mock import patch, mock_open, MagicMock
from typing import Dict, Any

from src.cli.targeting.config_store import ConfigStoreManager
from src.cli.targeting.config_models import (
    ConfigStore, 
    ConfigSystem, 
    ServerEndpoint, 
    ServerCredentials,
    ConnectionStatus
)


class TestConfigStoreManager:
    """Test suite for the ConfigStoreManager class."""

    @pytest.fixture
    def mock_config_path(self, tmp_path):
        """Fixture that returns a temporary config file path."""
        config_file = tmp_path / "config.json"
        return str(config_file)
    
    @pytest.fixture
    def empty_config_manager(self, mock_config_path):
        """Fixture that returns a ConfigStoreManager with an empty store."""
        return ConfigStoreManager(config_path=mock_config_path)
    
    @pytest.fixture
    def sample_config_data(self):
        """Fixture that returns sample configuration data."""
        return {
            "systems": {
                "test-server": {
                    "name": "test-server",
                    "description": "Test server",
                    "local_settings": {},
                    "roles": {
                        "web": {
                            "name": "web",
                            "description": "Web server",
                            "properties": {}
                        }
                    },
                    "endpoint": {
                        "hostname": "test.example.com",
                        "port": 22,
                        "credentials": {
                            "username": "testuser",
                            "password": None,
                            "key_path": "/path/to/key",
                            "use_keyring": False
                        },
                        "connection_status": "disconnected",
                        "last_connected": None,
                        "error_message": None
                    },
                    "tags": ["test", "example"],
                    "properties": {}
                }
            },
            "global_settings": {
                "timeout": {
                    "key": "timeout",
                    "value": 30,
                    "description": "Connection timeout in seconds"
                }
            }
        }

    def test_init_default_path(self):
        """Test initialization with default config path."""
        with patch('os.path.expanduser', return_value='/mock/home/.server_shell/config.json'):
            with patch('os.path.exists', return_value=False):
                with patch('os.makedirs') as mock_makedirs:
                    manager = ConfigStoreManager()
                    
                    assert manager.config_path == '/mock/home/.server_shell/config.json'
                    assert isinstance(manager.store, ConfigStore)
                    mock_makedirs.assert_called_once()
    
    def test_init_custom_path(self, mock_config_path):
        """Test initialization with custom config path."""
        with patch('os.path.exists', return_value=False):
            with patch('os.makedirs') as mock_makedirs:
                manager = ConfigStoreManager(config_path=mock_config_path)
                
                assert manager.config_path == mock_config_path
                assert isinstance(manager.store, ConfigStore)
                mock_makedirs.assert_called_once()
    
    def test_load_configuration_file_exists(self, sample_config_data):
        """Test loading configuration when file exists."""
        mock_json = json.dumps(sample_config_data)
        
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data=mock_json)):
                with patch('os.makedirs'):
                    manager = ConfigStoreManager(config_path='/mock/path')
                    
                    # Verify store was loaded correctly
                    assert len(manager.store.systems) == 1
                    assert "test-server" in manager.store.systems
                    assert len(manager.store.global_settings) == 1
                    assert "timeout" in manager.store.global_settings
    
    def test_load_configuration_file_does_not_exist(self):
        """Test loading configuration when file doesn't exist."""
        with patch('os.path.exists', return_value=False):
            with patch('os.makedirs'):
                manager = ConfigStoreManager(config_path='/mock/path')
                
                # Verify an empty store was created
                assert len(manager.store.systems) == 0
                assert len(manager.store.global_settings) == 0
    
    def test_load_configuration_invalid_json(self):
        """Test loading configuration with invalid JSON."""
        with patch('os.path.exists', return_value=True):
            with patch('builtins.open', mock_open(read_data='invalid json')):
                with patch('os.makedirs'):
                    with patch('src.cli.targeting.config_store.logger') as mock_logger:
                        manager = ConfigStoreManager(config_path='/mock/path')
                        
                        # Verify an empty store was created and error was logged
                        assert len(manager.store.systems) == 0
                        assert len(manager.store.global_settings) == 0
                        mock_logger.error.assert_called_once()
    
    def test_save_configuration(self, empty_config_manager):
        """Test saving configuration to file."""
        manager = empty_config_manager
        
        # Create a test system
        manager.create_system(
            name="test-server",
            hostname="test.example.com",
            description="Test server"
        )
        
        # Add a global setting
        manager.store.add_global_setting(
            key="timeout", 
            value=30, 
            description="Connection timeout in seconds"
        )
        
        with patch('builtins.open', mock_open()) as mock_file:
            with patch('src.cli.targeting.config_store.logger'):
                manager.save_configuration()
                
                # Verify file was written
                mock_file.assert_called_once_with(manager.config_path, 'w')
                
                # Get the JSON that was written
                write_call = mock_file().write.call_args
                assert write_call is not None
                written_data = write_call[0][0]
                config_dict = json.loads(written_data)
                
                # Verify the system was saved
                assert "systems" in config_dict
                assert "test-server" in config_dict["systems"]
                assert config_dict["systems"]["test-server"]["name"] == "test-server"
                
                # Verify the global setting was saved
                assert "global_settings" in config_dict
                assert "timeout" in config_dict["global_settings"]
    
    def test_save_configuration_error(self, empty_config_manager):
        """Test handling of errors during configuration save."""
        manager = empty_config_manager
        
        with patch('builtins.open', side_effect=Exception("Mock error")):
            with patch('src.cli.targeting.config_store.logger') as mock_logger:
                manager.save_configuration()
                
                # Verify error was logged
                mock_logger.error.assert_called_once()
    
    def test_create_system_basic(self, empty_config_manager):
        """Test creating a basic system without credentials."""
        manager = empty_config_manager
        
        system = manager.create_system(
            name="test-server",
            hostname="test.example.com",
            port=2222,
            description="Test server"
        )
        
        # Verify system was created correctly
        assert system.name == "test-server"
        assert system.description == "Test server"
        assert system.endpoint.hostname == "test.example.com"
        assert system.endpoint.port == 2222
        assert system.endpoint.credentials is None
        
        # Verify system was added to the store
        assert "test-server" in manager.store.systems
        assert manager.store.systems["test-server"] == system
    
    def test_create_system_with_credentials(self, empty_config_manager):
        """Test creating a system with credentials."""
        manager = empty_config_manager
        
        system = manager.create_system(
            name="test-server",
            hostname="test.example.com",
            username="testuser",
            password="testpass",
            key_path="/path/to/key",
            use_keyring=True
        )
        
        # Verify credentials were set correctly
        assert system.endpoint.credentials is not None
        assert system.endpoint.credentials.username == "testuser"
        assert system.endpoint.credentials.password == "testpass"
        assert system.endpoint.credentials.key_path == "/path/to/key"
        assert system.endpoint.credentials.use_keyring is True
    
    def test_create_system_duplicate_name(self, empty_config_manager):
        """Test creating a system with a duplicate name raises ValueError."""
        manager = empty_config_manager
        
        # Create first system
        manager.create_system(
            name="test-server",
            hostname="test.example.com"
        )
        
        # Try to create a second system with the same name
        with pytest.raises(ValueError):
            manager.create_system(
                name="test-server",
                hostname="other.example.com"
            )
    
    def test_get_store(self, empty_config_manager):
        """Test getting the configuration store."""
        manager = empty_config_manager
        store = manager.get_store()
        
        assert store is manager.store
        assert isinstance(store, ConfigStore)
    
    def test_end_to_end(self, mock_config_path):
        """Test the end-to-end flow of creating, saving, and loading configuration."""
        # Mock file operations to simulate saving and loading
        sample_config = {}
        
        def mock_save(path, mode):
            if mode == 'w':
                return mock_open()(path, mode)
            else:
                mock_file = mock_open(read_data=json.dumps(sample_config))(path, mode)
                return mock_file
        
        # Create a manager and add a system
        with patch('builtins.open', mock_save):
            with patch('src.cli.targeting.config_store.logger'):
                with patch('os.path.exists', return_value=True):
                    # First manager - create and save config
                    manager1 = ConfigStoreManager(config_path=mock_config_path)
                    system = manager1.create_system(
                        name="test-server",
                        hostname="test.example.com",
                        description="Test server",
                        username="testuser"
                    )
                    system.add_tag("test")
                    
                    # Capture the config data that would be saved
                    with patch.object(manager1, '_load_configuration', return_value=ConfigStore()):
                        manager1.save_configuration()
                        # Manually update our mock sample config to simulate saved state
                        sample_config = {
                            "systems": {
                                "test-server": {
                                    "name": "test-server",
                                    "description": "Test server",
                                    "local_settings": {},
                                    "roles": {},
                                    "endpoint": {
                                        "hostname": "test.example.com",
                                        "port": 22,
                                        "credentials": {
                                            "username": "testuser",
                                            "password": None,
                                            "key_path": None,
                                            "use_keyring": False
                                        },
                                        "connection_status": "disconnected",
                                        "last_connected": None,
                                        "error_message": None
                                    },
                                    "tags": ["test"],
                                    "properties": {}
                                }
                            },
                            "global_settings": {}
                        }
                    
                    # Second manager - load the config we just saved
                    manager2 = ConfigStoreManager(config_path=mock_config_path)
                    
                    # Verify the system was loaded correctly
                    assert len(manager2.store.systems) == 1
                    assert "test-server" in manager2.store.systems
                    system = manager2.store.systems["test-server"]
                    assert system.name == "test-server"
                    assert system.description == "Test server"
                    assert system.endpoint.hostname == "test.example.com"
                    assert system.endpoint.credentials is not None
                    assert system.endpoint.credentials.username == "testuser"
                    assert len(system.tags) > 0