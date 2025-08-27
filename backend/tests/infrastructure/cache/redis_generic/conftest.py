"""
Test fixtures for GenericRedisCache unit tests.

This module provides reusable fixtures following behavior-driven testing
principles. Fixtures focus on providing test data and mock dependencies
for testing the public contracts defined in the redis_generic.pyi file.

Fixture Categories:
    - Basic test data fixtures (keys, values, Redis URLs, TTL values)
    - Mock dependency fixtures (InMemoryCache, CachePerformanceMonitor, SecurityConfig)
    - Configuration fixtures (various GenericRedisCache configurations)
    - Redis operation fixtures (connection states, callback systems)

Design Philosophy:
    - Fixtures represent 'happy path' successful behavior only
    - Error scenarios are configured within individual test functions
    - All fixtures use public contracts from backend/contracts/ directory
    - Stateful mocks maintain internal state for realistic behavior
    - Mock dependencies are spec'd against real classes for accuracy
"""

import pytest
import hashlib
import time
from typing import Any, Dict, List, Optional, Callable
from unittest.mock import AsyncMock, MagicMock, patch
from collections import defaultdict


@pytest.fixture
def sample_redis_url():
    """
    Standard Redis URL for testing connections.
    
    Provides a typical Redis connection URL used across multiple test scenarios
    for consistency in testing Redis connection functionality.
    """
    return "redis://localhost:6379"


@pytest.fixture
def sample_secure_redis_url():
    """
    Secure Redis URL with TLS for testing secure connections.
    
    Provides a Redis URL with TLS encryption for testing
    security-enabled cache configurations.
    """
    return "rediss://localhost:6380"


# Note: sample_cache_key fixture is now provided by the parent conftest.py


# Note: sample_cache_value fixture is now provided by the parent conftest.py


@pytest.fixture
def sample_large_value():
    """
    Large cache value for testing compression functionality.
    
    Provides a large data structure that exceeds typical compression
    thresholds to test compression behavior.
    """
    return {
        "id": 456,
        "type": "large_document",
        "content": "Large document content " * 100,  # Create large content
        "data": {
            "items": [{"id": i, "value": f"item_{i}"} for i in range(50)],
            "bulk_data": "x" * 2000  # Ensure it exceeds compression threshold
        }
    }


# Note: sample_ttl and short_ttl fixtures are now provided by the parent conftest.py


# Note: mock_memory_cache fixture is now provided by the parent conftest.py


# Note: mock_performance_monitor fixture is now provided by the parent conftest.py


@pytest.fixture
def mock_security_config():
    """
    Mock SecurityConfig for testing secure Redis connections.
    
    Provides 'happy path' mock of the SecurityConfig contract with all properties
    returning secure configuration values as documented in the public interface.
    This is a stateless mock representing basic authentication configuration.
    """
    from app.infrastructure.cache.security import SecurityConfig
    
    config = MagicMock(spec=SecurityConfig)
    
    # Mock basic security configuration per contract
    config.redis_auth = "secure_password"
    config.use_tls = False
    config.tls_cert_path = None
    config.tls_key_path = None
    config.tls_ca_path = None
    config.acl_username = None
    config.acl_password = None
    config.connection_timeout = 10
    config.max_retries = 3
    config.retry_delay = 1
    config.verify_certificates = True
    config.min_tls_version = None
    config.cipher_suites = None
    
    # Mock property methods per contract
    config.has_authentication = True
    config.security_level = "basic"
    
    return config


@pytest.fixture
def mock_tls_security_config():
    """
    Mock SecurityConfig with TLS configuration for testing encrypted connections.
    
    Provides a SecurityConfig mock with TLS encryption enabled for testing
    secure Redis connection behavior.
    """
    from app.infrastructure.cache.security import SecurityConfig
    
    config = MagicMock(spec=SecurityConfig)
    
    # Mock TLS security configuration per contract
    config.redis_auth = "secure_password"
    config.use_tls = True
    config.tls_cert_path = "/etc/ssl/certs/redis-client.crt"
    config.tls_key_path = "/etc/ssl/private/redis-client.key" 
    config.tls_ca_path = "/etc/ssl/certs/ca.crt"
    config.acl_username = "cache_user"
    config.acl_password = "acl_password"
    config.connection_timeout = 10
    config.max_retries = 3
    config.retry_delay = 1
    config.verify_certificates = True
    config.min_tls_version = "TLSv1.2"
    config.cipher_suites = ["ECDHE-RSA-AES256-GCM-SHA384"]
    
    # Mock property methods per contract
    config.has_authentication = True
    config.security_level = "enterprise"
    
    return config


@pytest.fixture
def mock_redis_client():
    """
    Mock Redis client for testing Redis operations.
    
    Provides a stateful mock Redis client that simulates Redis behavior
    including get/set operations, expiration, and connection management.
    This allows testing of Redis integration without requiring a real Redis instance.
    """
    mock_client = AsyncMock()
    
    # Create stateful internal storage for Redis simulation
    mock_client._storage = {}
    mock_client._ttl_storage = {}
    mock_client._connected = False
    
    async def mock_ping():
        if not mock_client._connected:
            raise Exception("Redis connection failed")
        return b"PONG"
    
    async def mock_get(key):
        if key in mock_client._storage:
            # Check TTL
            if key in mock_client._ttl_storage:
                if time.time() > mock_client._ttl_storage[key]:
                    del mock_client._storage[key]
                    del mock_client._ttl_storage[key]
                    return None
            return mock_client._storage[key]
        return None
    
    async def mock_set(key, value, ex=None):
        mock_client._storage[key] = value
        if ex:
            mock_client._ttl_storage[key] = time.time() + ex
        return True
    
    async def mock_delete(key):
        deleted = key in mock_client._storage
        if deleted:
            del mock_client._storage[key]
            if key in mock_client._ttl_storage:
                del mock_client._ttl_storage[key]
        return 1 if deleted else 0
    
    async def mock_exists(key):
        # Check TTL first
        if key in mock_client._ttl_storage:
            if time.time() > mock_client._ttl_storage[key]:
                del mock_client._storage[key]
                del mock_client._ttl_storage[key]
                return 0
        return 1 if key in mock_client._storage else 0
    
    def mock_close():
        mock_client._connected = False
    
    # Assign mock implementations
    mock_client.ping.side_effect = mock_ping
    mock_client.get.side_effect = mock_get
    mock_client.set.side_effect = mock_set
    mock_client.delete.side_effect = mock_delete
    mock_client.exists.side_effect = mock_exists
    mock_client.close.side_effect = mock_close
    
    # Mark as connected by default
    mock_client._connected = True
    
    return mock_client


@pytest.fixture
def default_generic_redis_config():
    """
    Default GenericRedisCache configuration for standard testing.
    
    Provides a standard configuration dictionary suitable for most test scenarios.
    This represents the 'happy path' configuration that should work reliably.
    """
    return {
        "redis_url": "redis://localhost:6379",
        "default_ttl": 3600,
        "enable_l1_cache": True,
        "l1_cache_size": 100,
        "compression_threshold": 1000,
        "compression_level": 6,
        "performance_monitor": None,
        "security_config": None
    }


@pytest.fixture
def secure_generic_redis_config(mock_security_config):
    """
    Secure GenericRedisCache configuration for security testing.
    
    Provides a configuration with security features enabled for testing
    secure Redis connections and security validation.
    """
    return {
        "redis_url": "redis://localhost:6379",
        "default_ttl": 3600,
        "enable_l1_cache": True,
        "l1_cache_size": 100,
        "compression_threshold": 1000,
        "compression_level": 6,
        "performance_monitor": None,
        "security_config": mock_security_config
    }


@pytest.fixture
def compression_redis_config():
    """
    GenericRedisCache configuration optimized for compression testing.
    
    Provides a configuration with low compression threshold and high compression level
    to facilitate testing of compression functionality.
    """
    return {
        "redis_url": "redis://localhost:6379",
        "default_ttl": 3600,
        "enable_l1_cache": True,
        "l1_cache_size": 50,
        "compression_threshold": 100,  # Low threshold for testing
        "compression_level": 9,        # High compression for testing
        "performance_monitor": None,
        "security_config": None
    }


@pytest.fixture
def no_l1_redis_config():
    """
    GenericRedisCache configuration without L1 cache for Redis-only testing.
    
    Provides a configuration with L1 cache disabled to test pure Redis
    operations without memory cache interference.
    """
    return {
        "redis_url": "redis://localhost:6379",
        "default_ttl": 3600,
        "enable_l1_cache": False,
        "l1_cache_size": 0,
        "compression_threshold": 1000,
        "compression_level": 6,
        "performance_monitor": None,
        "security_config": None
    }


@pytest.fixture
def mock_callback_registry():
    """
    Mock callback registry for testing callback system functionality.
    
    Provides a mock callback registry that simulates the callback system
    described in the GenericRedisCache contract. This is stateful to track
    registered callbacks and their invocations.
    """
    registry = {
        "callbacks": defaultdict(list),
        "call_history": []
    }
    
    def register_callback(event: str, callback: Callable):
        registry["callbacks"][event].append(callback)
    
    def trigger_callbacks(event: str, *args, **kwargs):
        for callback in registry["callbacks"][event]:
            try:
                callback(*args, **kwargs)
                registry["call_history"].append({
                    "event": event,
                    "args": args,
                    "kwargs": kwargs,
                    "timestamp": time.time()
                })
            except Exception as e:
                registry["call_history"].append({
                    "event": event,
                    "error": str(e),
                    "timestamp": time.time()
                })
    
    mock_registry = MagicMock()
    mock_registry.register = register_callback
    mock_registry.trigger = trigger_callbacks
    mock_registry.callbacks = registry["callbacks"]
    mock_registry.call_history = registry["call_history"]
    
    return mock_registry


@pytest.fixture
def sample_callback_functions():
    """
    Sample callback functions for testing the callback system.
    
    Provides a set of test callback functions that can be used to test
    the callback registration and invocation system.
    """
    callback_results = {
        "get_success_calls": [],
        "get_miss_calls": [],
        "set_success_calls": [],
        "delete_success_calls": []
    }
    
    def on_get_success(key, value):
        callback_results["get_success_calls"].append({"key": key, "value": value})
    
    def on_get_miss(key):
        callback_results["get_miss_calls"].append({"key": key})
    
    def on_set_success(key, value, ttl=None):
        callback_results["set_success_calls"].append({"key": key, "value": value, "ttl": ttl})
    
    def on_delete_success(key):
        callback_results["delete_success_calls"].append({"key": key})
    
    return {
        "callbacks": {
            "get_success": on_get_success,
            "get_miss": on_get_miss,
            "set_success": on_set_success,
            "delete_success": on_delete_success
        },
        "results": callback_results
    }


@pytest.fixture
def bulk_test_data():
    """
    Bulk test data for testing batch operations and performance.
    
    Provides a set of key-value pairs for testing bulk operations,
    L1 cache behavior, and performance characteristics.
    """
    return {
        f"bulk:key:{i}": {
            "id": i,
            "data": f"test_data_{i}",
            "timestamp": "2023-01-01T12:00:00Z",
            "metadata": {"index": i, "batch": "test"}
        }
        for i in range(20)
    }


@pytest.fixture
def compression_test_data():
    """
    Test data specifically designed for compression testing.
    
    Provides data with varying sizes and compressibility to test
    compression threshold behavior and compression ratio calculations.
    """
    return {
        # Small data (below compression threshold)
        "small:data": {"content": "small"},
        
        # Large compressible data (repetitive content)
        "large:compressible": {
            "content": "This is repetitive content. " * 100,
            "data": ["repeated_item"] * 50
        },
        
        # Large incompressible data (random-like content)
        "large:incompressible": {
            "content": hashlib.sha256(str(i).encode()).hexdigest() 
                      for i in range(100)
        }
    }