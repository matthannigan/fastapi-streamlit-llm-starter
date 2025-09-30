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
import subprocess
import secrets
from pathlib import Path
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


# =============================================================================
# Secure Redis Testcontainer Infrastructure (Phase 1, Deliverable 1)
# =============================================================================

@pytest.fixture(scope="session")
def test_redis_certs(tmp_path_factory):
    """
    Generate self-signed TLS certificates for secure Redis testing.

    Creates a session-scoped certificate authority and Redis server certificate
    for integration testing with TLS-enabled Redis containers.

    Yields:
        Dict containing:
            - ca_cert: Path to CA certificate
            - ca_key: Path to CA private key
            - redis_cert: Path to Redis server certificate
            - redis_key: Path to Redis server private key
            - cert_dir: Path to certificate directory

    Raises:
        RuntimeError: If certificate generation fails
        subprocess.CalledProcessError: If OpenSSL command execution fails

    Note:
        Certificates are valid for 1 day (sufficient for test sessions).
        Subject name is /CN=test.redis for consistency.
    """
    # Create temporary directory for certificates
    cert_dir = tmp_path_factory.mktemp("redis_certs")

    # Generate CA certificate and key
    ca_key = cert_dir / "ca.key"
    ca_cert = cert_dir / "ca.crt"

    try:
        # Generate CA private key (2048-bit RSA)
        subprocess.run(
            [
                "openssl", "genrsa",
                "-out", str(ca_key),
                "2048"
            ],
            check=True,
            capture_output=True,
            text=True
        )

        # Generate self-signed CA certificate (valid for 1 day)
        subprocess.run(
            [
                "openssl", "req",
                "-new", "-x509",
                "-days", "1",
                "-key", str(ca_key),
                "-out", str(ca_cert),
                "-subj", "/CN=test.redis.ca"
            ],
            check=True,
            capture_output=True,
            text=True
        )

        # Generate Redis server private key
        redis_key = cert_dir / "redis.key"
        subprocess.run(
            [
                "openssl", "genrsa",
                "-out", str(redis_key),
                "2048"
            ],
            check=True,
            capture_output=True,
            text=True
        )

        # Generate certificate signing request for Redis server
        redis_csr = cert_dir / "redis.csr"
        subprocess.run(
            [
                "openssl", "req",
                "-new",
                "-key", str(redis_key),
                "-out", str(redis_csr),
                "-subj", "/CN=test.redis"
            ],
            check=True,
            capture_output=True,
            text=True
        )

        # Sign Redis server certificate with CA (valid for 1 day)
        redis_cert = cert_dir / "redis.crt"
        subprocess.run(
            [
                "openssl", "x509",
                "-req",
                "-days", "1",
                "-in", str(redis_csr),
                "-CA", str(ca_cert),
                "-CAkey", str(ca_key),
                "-CAcreateserial",
                "-out", str(redis_cert)
            ],
            check=True,
            capture_output=True,
            text=True
        )

        # Set proper file permissions (600 for keys, 644 for certs)
        os.chmod(ca_key, 0o600)
        os.chmod(redis_key, 0o600)
        os.chmod(ca_cert, 0o644)
        os.chmod(redis_cert, 0o644)

        # Validate certificate generation succeeded
        if not ca_cert.exists() or not redis_cert.exists():
            raise RuntimeError("Certificate generation failed - certificate files not created")

        if ca_cert.stat().st_size == 0 or redis_cert.stat().st_size == 0:
            raise RuntimeError("Certificate generation failed - certificate files are empty")

        # Validate certificate chain (CA → server cert)
        verify_result = subprocess.run(
            [
                "openssl", "verify",
                "-CAfile", str(ca_cert),
                str(redis_cert)
            ],
            capture_output=True,
            text=True
        )

        if verify_result.returncode != 0 or "OK" not in verify_result.stdout:
            raise RuntimeError(
                f"Certificate validation failed: {verify_result.stdout}\n{verify_result.stderr}"
            )

        # Return certificate paths
        return {
            "ca_cert": str(ca_cert),
            "ca_key": str(ca_key),
            "redis_cert": str(redis_cert),
            "redis_key": str(redis_key),
            "cert_dir": str(cert_dir)
        }

    except subprocess.CalledProcessError as e:
        raise RuntimeError(
            f"OpenSSL command failed: {e.cmd}\n"
            f"stdout: {e.stdout}\n"
            f"stderr: {e.stderr}"
        ) from e


@pytest.fixture(scope="session")
def secure_redis_container(test_redis_certs):
    """
    TLS-enabled Redis container for secure integration testing.

    Creates a Redis container with mandatory TLS encryption and authentication,
    using self-signed certificates from test_redis_certs fixture.

    Args:
        test_redis_certs: Certificate paths from test_redis_certs fixture

    Yields:
        Dict containing:
            - url: rediss:// connection URL with password
            - password: Redis password for authentication
            - host: Container host
            - port: Container port
            - container: GenericContainer instance
            - ca_cert: Path to CA certificate

    Raises:
        TimeoutError: If container fails to start within 30 seconds
        RuntimeError: If health check fails

    Note:
        - Redis configured with TLS-only mode (--tls-port 6379 --port 0)
        - Strong password generated per session
        - Health check validates TLS connection via docker exec
        - Container automatically cleaned up after session
    """
    from testcontainers.core.container import DockerContainer
    from testcontainers.core.waiting_utils import wait_for_logs

    # Generate cryptographically secure password
    password = secrets.token_urlsafe(32)

    # Extract certificate paths
    cert_dir = test_redis_certs["cert_dir"]
    redis_cert = Path(test_redis_certs["redis_cert"]).name
    redis_key = Path(test_redis_certs["redis_key"]).name
    ca_cert = Path(test_redis_certs["ca_cert"]).name

    container = None
    try:
        # Create generic Docker container (not RedisContainer which has built-in health check)
        container = DockerContainer("redis:7-alpine")

        # Mount certificate directory
        container.with_volume_mapping(str(cert_dir), "/tls", mode="ro")

        # Expose TLS port
        container.with_exposed_ports(6379)

        # Configure TLS-only mode (disable plain port)
        # Use --tls-auth-clients no to allow TLS without requiring client certificates
        # This enables TLS encryption without mutual TLS (mTLS)
        container.with_command(
            f"redis-server "
            f"--tls-port 6379 "
            f"--port 0 "
            f"--tls-cert-file /tls/{redis_cert} "
            f"--tls-key-file /tls/{redis_key} "
            f"--tls-ca-cert-file /tls/{ca_cert} "
            f"--tls-auth-clients no "
            f"--requirepass {password}"
        )

        # Start container
        container.start()

        # Wait for Redis to be ready (look for the "Ready to accept connections" log message)
        wait_for_logs(container, "Ready to accept connections", timeout=30)

        # Custom health check using docker exec with TLS
        import time
        start_time = time.time()
        max_wait = 10  # Additional wait after logs appear

        container_id = container.get_wrapped_container().id

        while time.time() - start_time < max_wait:
            try:
                # Check if Redis is responsive via TLS
                health_check = subprocess.run(
                    [
                        "docker", "exec", container_id,
                        "redis-cli",
                        "--tls",
                        "--cert", f"/tls/{redis_cert}",
                        "--key", f"/tls/{redis_key}",
                        "--cacert", f"/tls/{ca_cert}",
                        "-a", password,
                        "ping"
                    ],
                    capture_output=True,
                    text=True,
                    timeout=5
                )

                if health_check.returncode == 0 and "PONG" in health_check.stdout:
                    break
            except (subprocess.TimeoutExpired, subprocess.CalledProcessError) as e:
                # Log but continue trying
                pass

            time.sleep(0.5)
        else:
            # Log container status for debugging
            try:
                logs = container.get_logs()
                print(f"Container logs:\n{logs[0].decode() if logs else 'No logs'}")
            except:
                pass
            raise TimeoutError(
                f"Redis container failed TLS health check within {max_wait} seconds"
            )

        # Get connection details
        host = container.get_container_host_ip()
        port = container.get_exposed_port(6379)

        # Build secure connection URL
        url = f"rediss://:{password}@{host}:{port}/0"

        yield {
            "url": url,
            "password": password,
            "host": host,
            "port": port,
            "container": container,
            "ca_cert": test_redis_certs["ca_cert"]
        }

    finally:
        # Graceful cleanup
        try:
            if container:
                container.stop()
        except Exception as e:
            # Log but don't fail on cleanup errors
            print(f"Warning: Failed to stop Redis container: {e}")


@pytest.fixture
async def secure_redis_cache(secure_redis_container, monkeypatch):
    """
    GenericRedisCache instance connected to secure TLS-enabled Redis container.

    Creates a fully configured GenericRedisCache with TLS, authentication, and
    encryption for integration testing. Uses real secure Redis container.

    Args:
        secure_redis_container: Secure Redis container fixture
        monkeypatch: Pytest fixture for environment variable manipulation

    Yields:
        GenericRedisCache: Connected cache instance with security enabled

    Raises:
        InfrastructureError: If connection to secure Redis fails
        ConfigurationError: If security configuration invalid

    Note:
        - Uses rediss:// URL with TLS encryption
        - Self-signed certificates (verify_certificates=False)
        - Encryption enabled with test encryption key
        - Automatic cleanup on teardown
    """
    from app.infrastructure.cache.redis_generic import GenericRedisCache
    from app.infrastructure.cache.security import SecurityConfig
    from app.core.exceptions import InfrastructureError
    from cryptography.fernet import Fernet

    # Set required environment variables for security configuration
    # Generate proper Fernet key for encryption
    test_encryption_key = Fernet.generate_key().decode()
    monkeypatch.setenv("REDIS_ENCRYPTION_KEY", test_encryption_key)
    monkeypatch.setenv("REDIS_PASSWORD", secure_redis_container["password"])
    # Use 'testing' environment - now properly supports TLS with self-signed certs
    monkeypatch.setenv("ENVIRONMENT", "testing")

    # Initialize cache - it will use SecurityConfig.create_for_environment()
    cache = GenericRedisCache(
        redis_url=secure_redis_container["url"],
        default_ttl=3600,
        enable_l1_cache=True,
        l1_cache_size=100,
        compression_threshold=1000
    )

    # Manually configure security manager to use our test certificates
    # The auto-generated SecurityConfig doesn't know about our custom certs
    from app.infrastructure.cache.security import SecurityConfig
    cache.security_manager.config = SecurityConfig(
        redis_auth=secure_redis_container["password"],
        use_tls=True,
        tls_ca_path=secure_redis_container["ca_cert"],
        verify_certificates=False,  # Self-signed test certificates
        connection_timeout=10,
        socket_timeout=10
    )

    # Connect to secure Redis
    connected = await cache.connect()

    if not connected:
        raise InfrastructureError(
            "Failed to connect to secure Redis container for integration testing",
            context={
                "url": secure_redis_container["url"],
                "security": "TLS + auth + encryption"
            }
        )

    try:
        yield cache
    finally:
        # Cleanup: clear cache and disconnect
        try:
            await cache.clear()
        except Exception as e:
            print(f"Warning: Failed to clear cache during teardown: {e}")


@pytest.fixture
async def cache_instances(secure_redis_cache):
    """
    List of cache instances for shared contract testing.

    Provides multiple cache implementations to test against same behavioral contract.
    Currently includes real Redis (secure container). fakeredis will be added in Phase 2.

    Args:
        secure_redis_cache: Secure Redis cache fixture

    Yields:
        List[Tuple[str, CacheInterface]]: List of (name, cache_instance) tuples

    Note:
        - "real_redis": Uses secure TLS-enabled container
        - "fake_redis": Will be added in Phase 2 with encryption patched

    Phase 2 TODO:
        Add fakeredis implementation with encryption bypassed for unit testing:
        ```python
        # ("fake_redis", fakeredis_cache_with_patched_encryption)
        ```
    """
    instances = [
        ("real_redis", secure_redis_cache)
    ]

    try:
        yield instances
    finally:
        # Cleanup all cache instances
        for name, cache in instances:
            try:
                if hasattr(cache, 'clear'):
                    await cache.clear()
            except Exception as e:
                print(f"Warning: Failed to cleanup {name} cache: {e}")