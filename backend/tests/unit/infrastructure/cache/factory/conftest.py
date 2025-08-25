"""
Test fixtures for factory module unit tests.

This module provides reusable fixtures specific to cache factory testing.
All fixtures provide 'happy path' behavior based on public contracts from 
backend/contracts/ directory.

Fixtures:
    - mock_generic_redis_cache: Mock GenericRedisCache for testing factory creation
    - mock_ai_response_cache: Mock AIResponseCache for testing factory creation
    
Note: Exception fixtures and other common mocks are available in the shared
cache conftest.py file.
"""

import pytest
from unittest.mock import AsyncMock, MagicMock


@pytest.fixture
def mock_generic_redis_cache():
    """
    Mock GenericRedisCache for testing factory cache creation behavior.
    
    Provides 'happy path' mock of the GenericRedisCache contract with all methods
    returning successful cache operation behavior as documented in the public interface.
    This is a stateful mock that maintains an internal dictionary for realistic
    cache behavior where set values can be retrieved later.
    Uses spec to ensure mock accuracy against the real class.
    """
    from app.infrastructure.cache.redis_generic import GenericRedisCache
    
    mock_cache = AsyncMock(spec=GenericRedisCache)
    
    # Create stateful internal storage
    mock_cache._internal_storage = {}
    
    async def mock_get(key):
        return mock_cache._internal_storage.get(key)
    
    async def mock_set(key, value, ttl=None):
        mock_cache._internal_storage[key] = value
        
    async def mock_delete(key):
        if key in mock_cache._internal_storage:
            del mock_cache._internal_storage[key]
            return True
        return False
    
    # Assign mock implementations
    mock_cache.get.side_effect = mock_get
    mock_cache.set.side_effect = mock_set
    mock_cache.delete.side_effect = mock_delete
    
    # Mock factory-relevant methods
    mock_cache.is_connected.return_value = True
    mock_cache.close = AsyncMock()
    
    return mock_cache


@pytest.fixture
def mock_ai_response_cache():
    """
    Mock AIResponseCache for testing factory cache creation behavior.
    
    Provides 'happy path' mock of the AIResponseCache contract with all methods
    returning successful AI cache operation behavior as documented in the public interface.
    This is a stateful mock that maintains an internal dictionary for realistic
    cache behavior where set values can be retrieved later.
    Uses spec to ensure mock accuracy against the real class.
    """
    from app.infrastructure.cache.redis_ai import AIResponseCache
    
    mock_cache = AsyncMock(spec=AIResponseCache)
    
    # Create stateful internal storage
    mock_cache._internal_storage = {}
    
    async def mock_get(key):
        return mock_cache._internal_storage.get(key)
    
    async def mock_set(key, value, ttl=None):
        mock_cache._internal_storage[key] = value
        
    async def mock_delete(key):
        if key in mock_cache._internal_storage:
            del mock_cache._internal_storage[key]
            return True
        return False
    
    async def mock_cache_response(text, operation, options, response, ttl=None):
        key = f"ai_cache:{operation}:{text[:50]}"
        mock_cache._internal_storage[key] = response
        return key
    
    async def mock_get_cached_response(text, operation, options):
        key = f"ai_cache:{operation}:{text[:50]}"
        return mock_cache._internal_storage.get(key)
    
    # Assign mock implementations
    mock_cache.get.side_effect = mock_get
    mock_cache.set.side_effect = mock_set
    mock_cache.delete.side_effect = mock_delete
    mock_cache.cache_response.side_effect = mock_cache_response
    mock_cache.get_cached_response.side_effect = mock_get_cached_response
    
    # Mock factory-relevant methods
    mock_cache.is_connected.return_value = True
    mock_cache.close = AsyncMock()
    
    return mock_cache