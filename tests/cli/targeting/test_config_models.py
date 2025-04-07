import pytest
import json
from typing import Dict, Set, List, Optional, Any
from pydantic import ValidationError
from src.cli.targeting.config_models import (
    ConnectionStatus,
    ServerCredentials,
    RemoteAgent,
    ServerEndpoint,
    ConfigSetting,
    Role,
    ConfigSystem,
    ConfigStore
)

class TestConnectionStatus:
    """Test suite for the ConnectionStatus enum."""

    def test_enum_values(self):
        """Test that the ConnectionStatus enum has the expected values."""
        assert ConnectionStatus.DISCONNECTED == "disconnected"
        assert ConnectionStatus.CONNECTING == "connecting"
        assert ConnectionStatus.CONNECTED == "connected"
        assert ConnectionStatus.ERROR == "error"


class TestServerCredentials:
    """Test suite for the ServerCredentials model."""

    def test_initialization(self):
        """Test initialization with valid data."""
        creds = ServerCredentials(username="admin")
        assert creds.username == "admin"
        assert creds.password is None
        assert creds.key_path is None
        assert creds.use_keyring is False

    def test_initialization_with_all_fields(self):
        """Test initialization with all fields."""
        creds = ServerCredentials(
            username="admin",
            password="secret",
            key_path="/path/to/key",
            use_keyring=True
        )
        assert creds.username == "admin"
        assert creds.password == "secret"
        assert creds.key_path == "/path/to/key"
        assert creds.use_keyring is True

    def test_missing_username(self):
        """Test that initialization fails without a username."""
        with pytest.raises(ValidationError):
            ServerCredentials()

    def test_serialization(self):
        """Test JSON serialization and deserialization."""
        creds = ServerCredentials(
            username="admin",
            password="secret",
            key_path="/path/to/key",
            use_keyring=True
        )
        
        # Serialize to JSON
        json_str = creds.model_dump_json()
        
        # Deserialize from JSON
        creds_from_json = ServerCredentials.model_validate_json(json_str)
        
        # Check equality
        assert creds.username == creds_from_json.username
        assert creds.password == creds_from_json.password
        assert creds.key_path == creds_from_json.key_path
        assert creds.use_keyring == creds_from_json.use_keyring


class TestServerEndpoint:
    """Test suite for the ServerEndpoint model."""

    def test_initialization(self):
        """Test initialization with valid data."""
        endpoint = ServerEndpoint(hostname="server1.example.com")
        assert endpoint.hostname == "server1.example.com"
        assert endpoint.port == 22  # Default port
        assert endpoint.credentials is None
        assert endpoint.connection_status == ConnectionStatus.DISCONNECTED
        assert endpoint.last_connected is None
        assert endpoint.error_message is None

    def test_initialization_with_all_fields(self):
        """Test initialization with all fields."""
        creds = ServerCredentials(username="admin", password="secret")
        endpoint = ServerEndpoint(
            hostname="server1.example.com",
            port=2222,
            credentials=creds,
            connection_status=ConnectionStatus.ERROR,
            last_connected="2023-01-01T12:00:00Z",
            error_message="Connection failed"
        )
        
        assert endpoint.hostname == "server1.example.com"
        assert endpoint.port == 2222
        assert endpoint.credentials == creds
        assert endpoint.connection_status == ConnectionStatus.ERROR
        assert endpoint.last_connected == "2023-01-01T12:00:00Z"
        assert endpoint.error_message == "Connection failed"

    def test_missing_hostname(self):
        """Test that initialization fails without a hostname."""
        with pytest.raises(ValidationError):
            ServerEndpoint()

    def test_connection_methods(self):
        """Test the connection-related methods."""
        endpoint = ServerEndpoint(hostname="server1.example.com")
        
        # Test initial state
        assert endpoint.get_agent() is None
        
        # Test connect and status update
        agent = endpoint.connect()
        assert endpoint.connection_status == ConnectionStatus.CONNECTED
        assert endpoint.get_agent() is not None
        assert agent == endpoint.get_agent()
        
        # Test disconnect
        agent.disconnect()
        assert endpoint.connection_status == ConnectionStatus.DISCONNECTED
        assert endpoint.get_agent() is None

    def test_serialization(self):
        """Test JSON serialization and deserialization."""
        creds = ServerCredentials(username="admin", password="secret")
        endpoint = ServerEndpoint(
            hostname="server1.example.com",
            port=2222,
            credentials=creds,
            connection_status=ConnectionStatus.DISCONNECTED,
            last_connected="2023-01-01T12:00:00Z",
            error_message=None
        )
        
        # Serialize to JSON
        json_str = endpoint.model_dump_json()
        
        # Deserialize from JSON
        endpoint_from_json = ServerEndpoint.model_validate_json(json_str)
        
        # Check equality
        assert endpoint.hostname == endpoint_from_json.hostname
        assert endpoint.port == endpoint_from_json.port
        assert endpoint.connection_status == endpoint_from_json.connection_status
        assert endpoint.last_connected == endpoint_from_json.last_connected
        
        # Check nested object
        assert endpoint_from_json.credentials is not None
        assert endpoint.credentials.username == endpoint_from_json.credentials.username
        assert endpoint.credentials.password == endpoint_from_json.credentials.password


class TestRemoteAgent:
    """Test suite for the RemoteAgent class."""

    def test_initialization(self):
        """Test initialization with a ServerEndpoint."""
        endpoint = ServerEndpoint(hostname="server1.example.com")
        agent = RemoteAgent(endpoint)
        
        assert agent.endpoint == endpoint
        assert agent._connection is None

    def test_execute(self):
        """Test the execute method."""
        endpoint = ServerEndpoint(hostname="server1.example.com")
        agent = RemoteAgent(endpoint)
        
        result = agent.execute("ls -la")
        assert result == "Executed: ls -la"

    def test_cleanup(self):
        """Test the cleanup method."""
        endpoint = ServerEndpoint(hostname="server1.example.com")
        agent = RemoteAgent(endpoint)
        
        result = agent.cleanup()
        assert result == "Cleanup completed"

    def test_disconnect(self):
        """Test the disconnect method updates the endpoint status."""
        endpoint = ServerEndpoint(hostname="server1.example.com")
        agent = endpoint.connect()
        
        # Before disconnect
        assert endpoint.connection_status == ConnectionStatus.CONNECTED
        
        # Disconnect
        agent.disconnect()
        
        # After disconnect
        assert endpoint.connection_status == ConnectionStatus.DISCONNECTED
        assert endpoint.agent is None


class TestConfigSetting:
    """Test suite for the ConfigSetting model."""

    def test_initialization(self):
        """Test initialization with valid data."""
        setting = ConfigSetting(key="timeout", value=30)
        assert setting.key == "timeout"
        assert setting.value == 30
        assert setting.description is None

    def test_initialization_with_description(self):
        """Test initialization with a description."""
        setting = ConfigSetting(
            key="timeout",
            value=30,
            description="Connection timeout in seconds"
        )
        assert setting.key == "timeout"
        assert setting.value == 30
        assert setting.description == "Connection timeout in seconds"

    def test_missing_required_fields(self):
        """Test that initialization fails without required fields."""
        with pytest.raises(ValidationError):
            ConfigSetting(value=30)
            
        with pytest.raises(ValidationError):
            ConfigSetting(key="timeout")

    def test_serialization(self):
        """Test JSON serialization and deserialization."""
        setting = ConfigSetting(
            key="timeout",
            value=30,
            description="Connection timeout in seconds"
        )
        
        # Serialize to JSON
        json_str = setting.model_dump_json()
        
        # Deserialize from JSON
        setting_from_json = ConfigSetting.model_validate_json(json_str)
        
        # Check equality
        assert setting.key == setting_from_json.key
        assert setting.value == setting_from_json.value
        assert setting.description == setting_from_json.description

    def test_complex_value_serialization(self):
        """Test serialization with complex values."""
        # Test with a list
        setting_list = ConfigSetting(key="ports", value=[80, 443, 8080])
        json_list = setting_list.model_dump_json()
        setting_list_from_json = ConfigSetting.model_validate_json(json_list)
        assert setting_list.value == setting_list_from_json.value
        
        # Test with a dict
        setting_dict = ConfigSetting(key="config", value={"debug": True, "env": "prod"})
        json_dict = setting_dict.model_dump_json()
        setting_dict_from_json = ConfigSetting.model_validate_json(json_dict)
        assert setting_dict.value == setting_dict_from_json.value


class TestRole:
    """Test suite for the Role model."""

    def test_initialization(self):
        """Test initialization with valid data."""
        role = Role(name="web_server")
        assert role.name == "web_server"
        assert role.description is None
        assert role.properties == {}

    def test_initialization_with_all_fields(self):
        """Test initialization with all fields."""
        role = Role(
            name="web_server",
            description="Web server role",
            properties={"port": 80, "ssl": True}
        )
        
        assert role.name == "web_server"
        assert role.description == "Web server role"
        assert role.properties == {"port": 80, "ssl": True}

    def test_missing_name(self):
        """Test that initialization fails without a name."""
        with pytest.raises(ValidationError):
            Role()

    def test_add_property(self):
        """Test adding a property."""
        role = Role(name="web_server")
        
        # Add a property
        role.add_property("port", 80)
        assert role.properties["port"] == 80
        
        # Method should be chainable
        role.add_property("ssl", True).add_property("workers", 4)
        assert role.properties["ssl"] is True
        assert role.properties["workers"] == 4

    def test_get_property(self):
        """Test getting a property."""
        role = Role(
            name="web_server",
            properties={"port": 80, "ssl": True}
        )
        
        # Get existing property
        assert role.get_property("port") == 80
        assert role.get_property("ssl") is True
        
        # Get non-existent property
        assert role.get_property("workers") is None
        assert role.get_property("workers", 4) == 4  # With default

    def test_serialization(self):
        """Test JSON serialization and deserialization."""
        role = Role(
            name="web_server",
            description="Web server role",
            properties={"port": 80, "ssl": True}
        )
        
        # Serialize to JSON
        json_str = role.model_dump_json()
        
        # Deserialize from JSON
        role_from_json = Role.model_validate_json(json_str)
        
        # Check equality
        assert role.name == role_from_json.name
        assert role.description == role_from_json.description
        assert role.properties == role_from_json.properties


class TestConfigSystem:
    """Test suite for the ConfigSystem model."""

    @pytest.fixture
    def system(self):
        """Create a sample system for testing."""
        endpoint = ServerEndpoint(hostname="server1.example.com")
        
        return ConfigSystem(
            name="web1",
            description="Web server 1",
            endpoint=endpoint
        )

    def test_initialization(self, system):
        """Test initialization with valid data."""
        assert system.name == "web1"
        assert system.description == "Web server 1"
        assert system.local_settings == {}
        assert system.roles == {}
        assert system.tags == set()
        assert system.properties == {}
        assert isinstance(system.endpoint, ServerEndpoint)
        assert system.endpoint.hostname == "server1.example.com"

    def test_missing_required_fields(self):
        """Test that initialization fails without required fields."""
        # Missing name
        with pytest.raises(ValidationError):
            ConfigSystem(endpoint=ServerEndpoint(hostname="server1.example.com"))
            
        # Missing endpoint
        with pytest.raises(ValidationError):
            ConfigSystem(name="web1")

    def test_settings_management(self, system):
        """Test adding, getting, and removing settings."""
        # Add a setting
        system.add_setting("timeout", 30, "Connection timeout in seconds")
        assert "timeout" in system.local_settings
        assert system.local_settings["timeout"].value == 30
        
        # Get a setting
        assert system.get_setting("timeout") == 30
        assert system.get_setting("nonexistent") is None
        assert system.get_setting("nonexistent", 60) == 60
        
        # Remove a setting
        system.remove_setting("timeout")
        assert "timeout" not in system.local_settings
        
        # Method chaining
        system.add_setting("timeout", 30).add_setting("retries", 3)
        assert system.get_setting("timeout") == 30
        assert system.get_setting("retries") == 3

    def test_role_management(self, system):
        """Test adding, checking, and removing roles."""
        # Add a role
        role = system.add_role("web_server", "Web server role")
        assert "web_server" in system.roles
        assert role.name == "web_server"
        assert role.description == "Web server role"
        
        # Check if role exists
        assert system.has_role("web_server") is True
        assert system.has_role("db_server") is False
        
        # Remove a role
        system.remove_role("web_server")
        assert "web_server" not in system.roles
        assert system.has_role("web_server") is False

    def test_tag_management(self, system):
        """Test adding, checking, and removing tags."""
        # Add tags
        system.add_tag("production")
        assert "production" in system.tags
        
        # Add multiple tags
        system.add_tags({"critical", "high-availability"})
        assert "critical" in system.tags
        assert "high-availability" in system.tags
        
        # Check if tag exists
        assert system.has_tag("production") is True
        assert system.has_tag("development") is False
        
        # Remove a tag
        system.remove_tag("production")
        assert "production" not in system.tags
        
        # Method chaining
        system.add_tag("tier1").add_tag("frontend")
        assert "tier1" in system.tags
        assert "frontend" in system.tags

    def test_property_management(self, system):
        """Test adding and getting properties."""
        # Add properties
        system.add_property("region", "us-west")
        assert system.properties["region"] == "us-west"
        
        # Get properties
        assert system.get_property("region") == "us-west"
        assert system.get_property("nonexistent") is None
        assert system.get_property("nonexistent", "default") == "default"
        
        # Method chaining
        system.add_property("zone", "a").add_property("priority", 1)
        assert system.get_property("zone") == "a"
        assert system.get_property("priority") == 1

    def test_connection_methods(self, system):
        """Test connection methods."""
        # Initially not connected
        assert system.is_connected() is False
        
        # Connect
        agent = system.connect()
        assert system.is_connected() is True
        
        # Disconnect
        agent.disconnect()
        assert system.is_connected() is False

    def test_serialization(self, system):
        """Test JSON serialization and deserialization."""
        # Add some data to make it interesting
        system.add_setting("timeout", 30, "Connection timeout")
        system.add_role("web_server", "Web server role")
        system.add_tags({"production", "critical"})
        system.add_property("region", "us-west")
        
        # Serialize to JSON
        json_str = system.model_dump_json()
        
        # Deserialize from JSON
        system_from_json = ConfigSystem.model_validate_json(json_str)
        
        # Check equality of basic fields
        assert system.name == system_from_json.name
        assert system.description == system_from_json.description
        
        # Check nested objects
        assert "timeout" in system_from_json.local_settings
        assert system_from_json.local_settings["timeout"].value == 30
        
        assert "web_server" in system_from_json.roles
        assert system_from_json.roles["web_server"].description == "Web server role"
        
        # Check sets
        assert "production" in system_from_json.tags
        assert "critical" in system_from_json.tags
        
        # Check properties
        assert system_from_json.get_property("region") == "us-west"
        
        # Check endpoint
        assert system_from_json.endpoint.hostname == system.endpoint.hostname


class TestConfigStore:
    """Test suite for the ConfigStore model."""

    @pytest.fixture
    def store(self):
        """Create a sample store for testing."""
        return ConfigStore()

    @pytest.fixture
    def system1(self):
        """Create a sample system for testing."""
        endpoint = ServerEndpoint(hostname="web1.example.com")
        system = ConfigSystem(
            name="web1",
            description="Web server 1",
            endpoint=endpoint
        )
        system.add_tag("production")
        system.add_role("web_server")
        return system

    @pytest.fixture
    def system2(self):
        """Create another sample system for testing."""
        endpoint = ServerEndpoint(hostname="db1.example.com")
        system = ConfigSystem(
            name="db1",
            description="Database server 1",
            endpoint=endpoint
        )
        system.add_tag("production")
        system.add_tag("critical")
        system.add_role("db_server")
        return system

    def test_initialization(self, store):
        """Test initialization of an empty store."""
        assert store.systems == {}
        assert store.global_settings == {}

    def test_system_management(self, store, system1, system2):
        """Test adding, getting, and removing systems."""
        # Add systems
        added_system1 = store.add_system(system1)
        assert added_system1 == system1
        assert "web1" in store.systems
        
        added_system2 = store.add_system(system2)
        assert added_system2 == system2
        assert "db1" in store.systems
        
        # Get system
        retrieved_system = store.get_system("web1")
        assert retrieved_system == system1
        assert store.get_system("nonexistent") is None
        
        # Get all systems
        all_systems = store.list_systems()
        assert len(all_systems) == 2
        assert system1 in all_systems
        assert system2 in all_systems
        
        # Remove system
        assert store.remove_system("web1") is True
        assert "web1" not in store.systems
        assert store.remove_system("nonexistent") is False

    def test_duplicate_system_name(self, store, system1):
        """Test that adding a system with a duplicate name raises an error."""
        store.add_system(system1)
        
        duplicate_system = ConfigSystem(
            name="web1",  # Same name as system1
            endpoint=ServerEndpoint(hostname="duplicate.example.com")
        )
        
        with pytest.raises(ValueError):
            store.add_system(duplicate_system)

    def test_system_filtering(self, store, system1, system2):
        """Test filtering systems by various criteria."""
        store.add_system(system1)
        store.add_system(system2)
        
        # Filter by tag (both systems have 'production' tag)
        production_systems = store.filter_by_tags({"production"})
        assert len(production_systems) == 2
        assert system1 in production_systems
        assert system2 in production_systems
        
        # Filter by multiple tags (only system2 has both tags)
        critical_production_systems = store.filter_by_tags({"production", "critical"})
        assert len(critical_production_systems) == 1
        assert system2 in critical_production_systems
        
        # Filter by role
        web_servers = store.filter_by_role("web_server")
        assert len(web_servers) == 1
        assert system1 in web_servers
        
        db_servers = store.filter_by_role("db_server")
        assert len(db_servers) == 1
        assert system2 in db_servers
        
        # Filter by connection status
        connected_systems = store.filter_connected()
        assert len(connected_systems) == 0  # None are connected
        
        # Connect a system and filter again
        system1.connect()
        connected_systems = store.filter_connected()
        assert len(connected_systems) == 1
        assert system1 in connected_systems

    def test_custom_predicates(self, store, system1, system2):
        """Test finding systems with custom predicates."""
        store.add_system(system1)
        store.add_system(system2)
        
        # Find systems with "web" in the name
        web_systems = store.find_systems(lambda s: "web" in s.name.lower())
        assert len(web_systems) == 1
        assert system1 in web_systems
        
        # Find systems with "server" in the description
        server_systems = store.find_systems(lambda s: "server" in s.description.lower())
        assert len(server_systems) == 2
        
        # Find systems with specific hostname pattern
        example_systems = store.find_systems(lambda s: "example.com" in s.endpoint.hostname)
        assert len(example_systems) == 2

    def test_global_settings_management(self, store):
        """Test adding, getting, and removing global settings."""
        # Add global setting
        setting = store.add_global_setting("log_level", "INFO", "Global logging level")
        assert "log_level" in store.global_settings
        assert setting.key == "log_level"
        assert setting.value == "INFO"
        
        # Get global setting
        assert store.get_global_setting("log_level") == "INFO"
        assert store.get_global_setting("nonexistent") is None
        assert store.get_global_setting("nonexistent", "DEFAULT") == "DEFAULT"
        
        # Remove global setting
        assert store.remove_global_setting("log_level") is True
        assert "log_level" not in store.global_settings
        assert store.remove_global_setting("nonexistent") is False

    def test_serialization(self, store, system1, system2):
        """Test JSON serialization and deserialization."""
        # Add systems and settings
        store.add_system(system1)
        store.add_system(system2)
        store.add_global_setting("log_level", "INFO", "Global logging level")
        
        # Serialize to JSON
        json_str = store.model_dump_json()
        
        # Deserialize from JSON
        store_from_json = ConfigStore.model_validate_json(json_str)
        
        # Check systems
        assert len(store_from_json.systems) == 2
        assert "web1" in store_from_json.systems
        assert "db1" in store_from_json.systems
        
        # Check global settings
        assert "log_level" in store_from_json.global_settings
        assert store_from_json.global_settings["log_level"].value == "INFO"
        
        # Deeper check of a system
        web1 = store_from_json.systems["web1"]
        assert web1.name == "web1"
        assert web1.description == "Web server 1"
        assert "production" in web1.tags
        assert "web_server" in web1.roles


def test_integration_full_config():
    """Integration test for a complete configuration workflow."""
    # Create a config store
    store = ConfigStore()
    
    # Add global settings
    store.add_global_setting("organization", "Example Corp")
    store.add_global_setting("contact", "admin@example.com")
    
    # Create systems
    web_endpoint = ServerEndpoint(
        hostname="web.example.com",
        credentials=ServerCredentials(username="webadmin", password="secret")
    )
    
    web_system = ConfigSystem(
        name="web_server",
        description="Main web server",
        endpoint=web_endpoint
    )
    web_system.add_tag("production")
    web_system.add_tag("internet-facing")
    web_system.add_role("web_server", "Serves web content")
    web_system.add_setting("worker_processes", 4, "Number of worker processes")
    
    db_endpoint = ServerEndpoint(
        hostname="db.example.com",
        credentials=ServerCredentials(username="dbadmin", key_path="/keys/db.pem")
    )
    
    db_system = ConfigSystem(
        name="db_server",
        description="Main database server",
        endpoint=db_endpoint
    )
    db_system.add_tag("production")
    db_system.add_tag("critical")
    db_system.add_role("db_server", "Stores application data")
    db_system.add_setting("max_connections", 100, "Maximum number of connections")
    
    # Add systems to store
    store.add_system(web_system)
    store.add_system(db_system)
    
    # Serialize the entire config
    json_str = store.model_dump_json()
    
    # Deserialize from JSON
    store_from_json = ConfigStore.model_validate_json(json_str)
    
    # Verify everything came back correctly
    assert store.global_settings.keys() == store_from_json.global_settings.keys()
    assert store.systems.keys() == store_from_json.systems.keys()
    
    # Check global settings
    assert store_from_json.get_global_setting("organization") == "Example Corp"
    
    # Check systems
    web_from_json = store_from_json.get_system("web_server")
    assert web_from_json.description == "Main web server"
    assert "production" in web_from_json.tags
    assert "internet-facing" in web_from_json.tags
    assert web_from_json.has_role("web_server")
    assert web_from_json.get_setting("worker_processes") == 4
    
    # Check nested objects (credentials)
    assert web_from_json.endpoint.credentials.username == "webadmin"
    assert web_from_json.endpoint.credentials.password == "secret"
    
    db_from_json = store_from_json.get_system("db_server")
    assert "critical" in db_from_json.tags
    assert db_from_json.get_setting("max_connections") == 100
    assert db_from_json.endpoint.credentials.key_path == "/keys/db.pem"