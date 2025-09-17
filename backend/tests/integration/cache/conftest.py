"""
Test fixtures for cache integration tests.

This module provides reusable fixtures for cache integration testing,
focusing on cross-component behavior and service interactions.

Fixtures are imported from the main cache conftest.py to maintain consistency
and avoid duplication while enabling integration test isolation.
"""

import pytest
import tempfile
import json
import os
from unittest.mock import AsyncMock, MagicMock
from typing import Dict, Any, Optional


# =============================================================================
# Settings Fixtures (imported from main conftest.py)
# =============================================================================

@pytest.fixture
def test_settings():
    """
    Real Settings instance with test configuration for testing actual configuration behavior.

    Provides a Settings instance loaded from test configuration, enabling tests
    to verify actual configuration loading, validation, and environment detection
    instead of using hardcoded mock values.

    This fixture represents behavior-driven testing where we test the actual
    Settings class functionality rather than mocking its behavior.
    """
    from app.core.config import Settings

    # Create test configuration with realistic values
    test_config = {
        "gemini_api_key": "test-gemini-api-key-12345",
        "ai_model": "gemini-2.0-flash-exp",
        "ai_temperature": 0.7,
        "host": "0.0.0.0",
        "port": 8000,
        "api_key": "test-api-key-12345",
        "additional_api_keys": "key1,key2,key3",
        "debug": False,
        "log_level": "INFO",
        "cache_preset": "development",
        "resilience_preset": "simple",
        "health_check_timeout_ms": 2000
    }

    # Create temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(test_config, f, indent=2)
        config_file = f.name

    try:
        # Create Settings instance with test config
        # Override environment variables to ensure test isolation
        test_env = {
            "GEMINI_API_KEY": "test-gemini-api-key-12345",
            "API_KEY": "test-api-key-12345",
            "CACHE_PRESET": "development",
            "RESILIENCE_PRESET": "simple"
        }

        # Temporarily set test environment variables
        original_env = {}
        for key, value in test_env.items():
            original_env[key] = os.environ.get(key)
            os.environ[key] = value

        # Create real Settings instance
        settings = Settings()

        # Restore original environment
        for key, original_value in original_env.items():
            if original_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original_value

        return settings

    finally:
        # Clean up temporary config file
        os.unlink(config_file)


@pytest.fixture
def development_settings():
    """
    Real Settings instance configured for development environment testing.

    Provides Settings with development preset for testing development-specific behavior.
    """
    import os

    # Set development environment variables
    test_env = {
        "GEMINI_API_KEY": "test-dev-api-key",
        "API_KEY": "test-dev-api-key",
        "CACHE_PRESET": "development",
        "RESILIENCE_PRESET": "development",
        "DEBUG": "true"
    }

    original_env = {}
    for key, value in test_env.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value

    try:
        from app.core.config import Settings
        settings = Settings()
        yield settings
    finally:
        # Restore environment
        for key, original_value in original_env.items():
            if original_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original_value


@pytest.fixture
def production_settings():
    """
    Real Settings instance configured for production environment testing.

    Provides Settings with production preset for testing production-specific behavior.
    """
    import os

    # Set production environment variables
    test_env = {
        "GEMINI_API_KEY": "test-prod-api-key",
        "API_KEY": "test-prod-api-key",
        "CACHE_PRESET": "production",
        "RESILIENCE_PRESET": "production",
        "DEBUG": "false"
    }

    original_env = {}
    for key, value in test_env.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value

    try:
        from app.core.config import Settings
        settings = Settings()
        yield settings
    finally:
        # Restore environment
        for key, original_value in original_env.items():
            if original_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original_value


# =============================================================================
# Factory Fixtures (imported from main conftest.py)
# =============================================================================

@pytest.fixture
async def real_cache_factory():
    """
    Real CacheFactory instance for testing factory behavior.

    Provides an actual CacheFactory instance to test real factory logic,
    parameter mapping, and cache creation behavior rather than mocking
    the factory's internal operations.

    This enables behavior-driven testing of the factory's actual logic.
    """
    from app.infrastructure.cache.factory import CacheFactory
    return CacheFactory()


@pytest.fixture
async def factory_memory_cache(real_cache_factory):
    """
    Cache created via real factory using memory cache for testing.

    Creates a cache through the real factory using memory cache option,
    enabling testing of factory integration while avoiding Redis dependencies.
    """
    cache = await real_cache_factory.for_testing(use_memory_cache=True)
    yield cache
    await cache.clear()


@pytest.fixture
async def factory_web_cache(real_cache_factory):
    """
    Cache created via real factory for web application testing.

    Creates a cache through the real factory for web application use case,
    with graceful fallback to memory cache if Redis is unavailable.
    """
    cache = await real_cache_factory.for_web_app(fail_on_connection_error=False)
    yield cache
    if hasattr(cache, 'clear'):
        await cache.clear()


@pytest.fixture
async def factory_ai_cache(real_cache_factory):
    """
    Cache created via real factory for AI application testing.

    Creates a cache through the real factory for AI application use case,
    with graceful fallback to memory cache if Redis is unavailable.
    """
    cache = await real_cache_factory.for_ai_app(fail_on_connection_error=False)
    yield cache
    if hasattr(cache, 'clear'):
        await cache.clear()


# =============================================================================
# Basic Test Data Fixtures (imported from main conftest.py)
# =============================================================================

@pytest.fixture
def sample_cache_key():
    """
    Standard cache key for basic testing scenarios.

    Provides a typical cache key string used across multiple test scenarios
    for consistency in testing cache interfaces.
    """
    return "test:key:123"


@pytest.fixture
def sample_cache_value():
    """
    Standard cache value for basic testing scenarios.

    Provides a typical cache value (dictionary) that represents common
    data structures cached in production applications.
    """
    return {
        "user_id": 123,
        "name": "John Doe",
        "email": "john@example.com",
        "preferences": {
            "theme": "dark",
            "language": "en"
        },
        "created_at": "2023-01-01T12:00:00Z"
    }


@pytest.fixture
def sample_ttl():
    """
    Standard TTL value for testing time-to-live functionality.

    Provides a reasonable TTL value (in seconds) for testing
    cache expiration behavior.
    """
    return 3600  # 1 hour


@pytest.fixture
def default_memory_cache():
    """
    InMemoryCache instance with default configuration for standard testing.

    Provides a fresh InMemoryCache instance with default settings
    suitable for most test scenarios. This represents the 'happy path'
    configuration that should work reliably.

    Configuration:
        - default_ttl: 3600 seconds (1 hour)
        - max_size: 1000 entries
    """
    from app.infrastructure.cache.memory import InMemoryCache
    return InMemoryCache()