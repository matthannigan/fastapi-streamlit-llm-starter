"""
Common mock objects for testing.

This module contains mock implementations and helper utilities
for creating test doubles across the test suite.
"""
from unittest.mock import MagicMock, AsyncMock
import pytest


class MockAIClient:
    """Mock AI client for testing."""
    
    def __init__(self):
        self.generate_text = AsyncMock(return_value="Mock generated text")
        self.is_available = MagicMock(return_value=True)


class MockCacheClient:
    """Mock cache client for testing."""
    
    def __init__(self):
        self._data = {}
        
    async def get(self, key):
        return self._data.get(key)
        
    async def set(self, key, value, ttl=None):
        self._data[key] = value
        
    async def delete(self, key):
        self._data.pop(key, None)
        
    async def clear(self):
        self._data.clear()


class MockAuthenticator:
    """Mock authenticator for testing."""
    
    def __init__(self):
        self.verify_token = AsyncMock(return_value={"user_id": "test_user"})
        self.create_token = MagicMock(return_value="mock_token")


@pytest.fixture
def mock_ai_client():
    """Fixture providing a mock AI client."""
    return MockAIClient()


@pytest.fixture
def mock_cache_client():
    """Fixture providing a mock cache client."""
    return MockCacheClient()


@pytest.fixture
def mock_authenticator():
    """Fixture providing a mock authenticator."""
    return MockAuthenticator() 