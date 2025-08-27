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


# Note: mock_generic_redis_cache fixture is now provided by the parent conftest.py


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
    
    def mock_build_key(text, operation, options):
        """Mock build_key method using simplified key generation logic."""
        # Simplified mock key generation - for realistic testing, use CacheKeyGenerator
        text_part = text[:50] + ("..." if len(text) > 50 else "")
        options_str = str(sorted(options.items())) if options else ""
        options_hash = str(hash(options_str))[-8:] if options_str else "00000000"
        
        key = f"ai_cache:op:{operation}|txt:{text_part}|opts:{options_hash}"
        
        # Handle embedded question for Q&A operations
        if options and "question" in options:
            question_hash = str(hash(options["question"]))[-8:]
            key += f"|q:{question_hash}"
            
        return key
    
    # Assign mock implementations
    mock_cache.get.side_effect = mock_get
    mock_cache.set.side_effect = mock_set
    mock_cache.delete.side_effect = mock_delete
    mock_cache.build_key.side_effect = mock_build_key
    
    # Note: Removed is_connected and close methods as they are not part of the AIResponseCache contract
    
    return mock_cache