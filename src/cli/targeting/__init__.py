"""
Targeting package for system discovery and management.

This package contains models and tools for targeting systems,
managing configuration, and discovering system properties.
"""

from .config_models import (
    ConfigStore, 
    ConfigSystem,
    ServerEndpoint,
    ConfigSetting,
    Role,
    RemoteAgent,
    ConnectionStatus
)
from .config_store import ConfigStoreManager

__all__ = [
    'ConfigStore',
    'ConfigSystem',
    'ServerEndpoint',
    'ConfigSetting',
    'Role',
    'RemoteAgent',
    'ConnectionStatus',
    'ConfigStoreManager'
]