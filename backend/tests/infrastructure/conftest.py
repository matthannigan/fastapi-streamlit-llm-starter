"""
Infrastructure-specific fixtures for testing.
"""
import pytest


@pytest.fixture
def mock_infrastructure_config():
    """Mock configuration for infrastructure components."""
    return {
        "cache_enabled": True,
        "resilience_enabled": True,
        "monitoring_enabled": True
    }
