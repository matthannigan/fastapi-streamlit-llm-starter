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

import hashlib
import json
import ssl
from typing import Any
from unittest.mock import patch

import pytest

from app.infrastructure.cache.security import SecurityConfig


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
            "bulk_data": "x" * 2000,  # Ensure it exceeds compression threshold
        },
    }


# Note: sample_ttl and short_ttl fixtures are now provided by the parent conftest.py


@pytest.fixture
def fake_redis_client():
    """
    Fake Redis client for testing Redis operations.

    Provides a fakeredis instance that behaves like a real Redis server,
    including proper Redis operations, data types, expiration, and error handling.
    This provides more realistic testing than mocks while not requiring a real Redis instance.
    """
    import fakeredis.aioredis

    class ExtendedFakeRedis(fakeredis.aioredis.FakeRedis):
        """Extended FakeRedis with additional commands needed for testing."""

        async def info(self, section=None):
            """Mock implementation of Redis INFO command."""
            return {
                "redis_version": "6.2.0",
                "redis_git_sha1": "00000000",
                "redis_git_dirty": "0",
                "redis_build_id": "test",
                "redis_mode": "standalone",
                "os": "Linux 4.9.0-7-amd64 x86_64",
                "arch_bits": "64",
                "multiplexing_api": "epoll",
                "gcc_version": "6.3.0",
                "process_id": "1",
                "run_id": "test-run-id",
                "tcp_port": "6379",
                "uptime_in_seconds": "1000",
                "uptime_in_days": "0",
                "hz": "10",
                "configured_hz": "10",
                "lru_clock": "12345",
                "executable": "/usr/local/bin/redis-server",
                "config_file": "",
                "connected_clients": "1",
                "client_recent_max_input_buffer": "2",
                "client_recent_max_output_buffer": "0",
                "blocked_clients": "0",
                "used_memory": "1000000",
                "used_memory_human": "976.56K",
                "used_memory_rss": "2000000",
                "used_memory_rss_human": "1.91M",
                "used_memory_peak": "1500000",
                "used_memory_peak_human": "1.43M",
                "total_system_memory": "8000000000",
                "total_system_memory_human": "7.45G",
                "used_memory_lua": "37888",
                "used_memory_lua_human": "37.00K",
                "maxmemory": "0",
                "maxmemory_human": "0B",
                "maxmemory_policy": "noeviction",
                "mem_fragmentation_ratio": "2.00",
                "mem_allocator": "jemalloc-4.0.3",
                "loading": "0",
                "rdb_changes_since_last_save": "0",
                "rdb_bgsave_in_progress": "0",
                "rdb_last_save_time": "1234567890",
                "rdb_last_bgsave_status": "ok",
                "rdb_last_bgsave_time_sec": "0",
                "rdb_current_bgsave_time_sec": "-1",
                "aof_enabled": "0",
                "aof_rewrite_in_progress": "0",
                "aof_rewrite_scheduled": "0",
                "aof_last_rewrite_time_sec": "-1",
                "aof_current_rewrite_time_sec": "-1",
                "total_connections_received": "1",
                "total_commands_processed": "1",
                "instantaneous_ops_per_sec": "0",
                "total_net_input_bytes": "14",
                "total_net_output_bytes": "0",
                "instantaneous_input_kbps": "0.00",
                "instantaneous_output_kbps": "0.00",
                "rejected_connections": "0",
                "sync_full": "0",
                "sync_partial_ok": "0",
                "sync_partial_err": "0",
                "expired_keys": "0",
                "evicted_keys": "0",
                "keyspace_hits": "0",
                "keyspace_misses": "0",
                "pubsub_channels": "0",
                "pubsub_patterns": "0",
                "latest_fork_usec": "0",
                "migrate_cached_sockets": "0",
                "role": "master",
                "connected_slaves": "0",
                "master_repl_offset": "0",
                "repl_backlog_active": "0",
                "repl_backlog_size": "1048576",
                "repl_backlog_first_byte_offset": "0",
                "repl_backlog_histlen": "0",
            }

    # Create extended fakeredis instance that behaves like real Redis
    fake_redis = ExtendedFakeRedis(decode_responses=False)

    return fake_redis


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
        "security_config": None,
    }


@pytest.fixture
def secure_generic_redis_config(mock_path_exists):
    """
    Secure GenericRedisCache configuration for security testing.

    Provides a configuration with security features enabled for testing
    secure Redis connections and security validation.

    Creates the security configuration on-demand to ensure mock_path_exists
    is active during SecurityConfig creation.
    """
    # Create SecurityConfig with mocked certificate paths (mock_path_exists handles file existence)
    secure_config = SecurityConfig(
        redis_auth="secure_password",
        use_tls=True,
        tls_cert_path="/etc/ssl/certs/redis-client.crt",
        tls_key_path="/etc/ssl/private/redis-client.key",
        tls_ca_path="/etc/ssl/certs/ca.crt",
        acl_username="cache_user",
        acl_password="acl_password",
        connection_timeout=10,
        max_retries=3,
        retry_delay=1,
        verify_certificates=True,
        min_tls_version=ssl.TLSVersion.TLSv1_2.value,  # type: ignore
        cipher_suites=["ECDHE-RSA-AES256-GCM-SHA384"],
    )

    return {
        "redis_url": "redis://localhost:6379",
        "default_ttl": 3600,
        "enable_l1_cache": True,
        "l1_cache_size": 100,
        "compression_threshold": 1000,
        "compression_level": 6,
        "performance_monitor": None,
        "security_config": secure_config,
    }


@pytest.fixture
def mock_path_exists():
    """
    Fixture that mocks pathlib.Path.exists for certificate file validation.

    Uses autospec=True to ensure the mock's signature matches the real
    method, which is crucial for using side_effect correctly. The default
    return_value is True for "happy path" tests.

    Note: This fixture is now redundant since it's already defined in parent conftest,
    but kept here for clarity in the redis_generic test module context.
    """
    with patch("pathlib.Path.exists", autospec=True) as mock_patch:
        mock_patch.return_value = True
        yield mock_patch


@pytest.fixture
def mock_ssl_context():
    """
    Fixture that mocks SSL certificate loading operations for security testing.

    Mocks ssl.SSLContext.load_cert_chain and ssl.SSLContext.load_verify_locations
    to prevent actual file system access during testing. Essential for security
    tests that require TLS configuration without real certificate files.
    """
    with patch("ssl.SSLContext.load_cert_chain") as mock_load_cert, patch(
        "ssl.SSLContext.load_verify_locations"
    ) as mock_load_verify:
        # Mock successful certificate loading
        mock_load_cert.return_value = None
        mock_load_verify.return_value = None
        yield {
            "load_cert_chain": mock_load_cert,
            "load_verify_locations": mock_load_verify,
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
        "compression_level": 9,  # High compression for testing
        "performance_monitor": None,
        "security_config": None,
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
        "security_config": None,
    }


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
        "delete_success_calls": [],
    }

    def on_get_success(key, value):
        callback_results["get_success_calls"].append({"key": key, "value": value})

    def on_get_miss(key):
        callback_results["get_miss_calls"].append({"key": key})

    def on_set_success(key, value, ttl=None):
        callback_results["set_success_calls"].append(
            {"key": key, "value": value, "ttl": ttl}
        )

    def on_delete_success(key):
        callback_results["delete_success_calls"].append({"key": key})

    return {
        "callbacks": {
            "get_success": on_get_success,
            "get_miss": on_get_miss,
            "set_success": on_set_success,
            "delete_success": on_delete_success,
        },
        "results": callback_results,
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
            "metadata": {"index": i, "batch": "test"},
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
            "data": ["repeated_item"] * 50,
        },
        # Large incompressible data (random-like content)
        "large:incompressible": {
            "content": hashlib.sha256(str(i).encode()).hexdigest() for i in range(100)
        },
    }


@pytest.fixture
def secure_fakeredis_cache(default_generic_redis_config, fake_redis_client):
    """
    Provides a GenericRedisCache instance backed by FakeRedis with encryption bypassed.

    This fixture creates a cache instance that uses FakeRedis for storage but patches
    out the encryption layer to allow unit testing of cache logic without encryption
    complexity. The encryption/decryption methods are replaced with simple JSON
    encoding/decoding.

    This is the recommended fixture for unit tests focused on cache behavior
    (compression, TTL, data handling, connection management) where encryption
    would add unnecessary complexity.

    Use Cases:
        - Testing cache operations without encryption overhead
        - Testing compression functionality in isolation
        - Testing TTL behavior and expiration
        - Testing connection management and state

    NOT recommended for:
        - Integration tests (use secure_redis_cache with real TLS)
        - Security validation tests (use real encryption)
        - End-to-end tests (use full security stack)

    Returns:
        GenericRedisCache: Cache instance with FakeRedis backend and patched encryption
    """
    from unittest.mock import patch

    from app.infrastructure.cache.redis_generic import GenericRedisCache

    # Create cache instance with default config
    cache = GenericRedisCache(**default_generic_redis_config)

    # Replace Redis client with FakeRedis
    cache.redis = fake_redis_client
    cache._redis_connected = True

    # Patch serialization methods to bypass encryption
    def mock_serialize(value: Any) -> bytes:
        """Simple JSON serialization without encryption."""
        return json.dumps(value).encode("utf-8")

    def mock_deserialize(value: bytes) -> Any:
        """Simple JSON deserialization without decryption."""
        return json.loads(value.decode("utf-8"))

    # Apply patches using context managers
    with patch.object(
        cache, "_serialize_value", side_effect=mock_serialize
    ), patch.object(cache, "_deserialize_value", side_effect=mock_deserialize):
        yield cache
