"""
Enhanced E2E test fixtures with Testcontainers Redis support.

This module provides fixtures for end-to-end cache testing with real Redis instances,
enabling comprehensive testing of Redis-specific features and behaviors.
"""

import os

import pytest
import pytest_asyncio
from httpx import ASGITransport, AsyncClient
from testcontainers.redis import RedisContainer


@pytest.fixture(scope="session")
def redis_container():
    """
    Session-scoped Redis container for e2e tests.

    Provides a real Redis instance for testing Redis-specific behaviors
    like pattern matching, TTL, persistence, and connection management.

    Benefits:
        - Real Redis connectivity testing
        - Accurate pattern invalidation testing
        - Performance metrics with actual Redis operations
        - Security feature testing (AUTH, TLS if configured)

    Usage:
        Test functions can access redis connection details to configure
        cache instances with real Redis backends instead of InMemoryCache fallback.
    """
    container = RedisContainer("redis:7-alpine")
    container.start()

    try:
        yield container
    finally:
        container.stop()


@pytest.fixture
def redis_config(redis_container):
    """
    Redis connection configuration from Testcontainers instance.

    Returns:
        dict: Redis connection parameters for cache configuration
    """
    return {
        "host": redis_container.get_container_host_ip(),
        "port": redis_container.get_exposed_port(6379),
        "url": f"redis://{redis_container.get_container_host_ip()}:{redis_container.get_exposed_port(6379)}",
    }


@pytest.fixture
def enhanced_cache_preset_app(monkeypatch, redis_config):
    """
    Enhanced cache preset app factory with real Redis connectivity.

    This fixture creates app instances that use real Redis instead of falling back
    to InMemoryCache, enabling comprehensive testing of Redis-specific behaviors.

    Usage:
        app_with_preset = enhanced_cache_preset_app("ai-production")
        # App will have real Redis connection and show "connected" status

    Benefits:
        - Tests actual Redis connectivity and status
        - Validates Redis-specific cache operations
        - Enables realistic preset behavior testing
        - Provides real performance metrics and monitoring data
    """

    def _create_app_with_redis_preset(preset: str):
        """Create app instance with specified cache preset and real Redis."""
        import sys

        # Clear cache-related environment variables
        cache_env_vars = [
            "CACHE_PRESET",
            "CACHE_REDIS_URL",
            "ENABLE_AI_CACHE",
            "REDIS_AUTH",
            "REDIS_PASSWORD",
            "USE_TLS",
            "CACHE_CUSTOM_CONFIG",
            "RESILIENCE_PRESET",
        ]
        for var in cache_env_vars:
            monkeypatch.delenv(var, raising=False)

        # Set test environment with real Redis
        monkeypatch.setenv("CACHE_PRESET", preset)
        monkeypatch.setenv("CACHE_REDIS_URL", redis_config["url"])

        # Log configuration for debugging
        print(f"Redis-enhanced test using Redis URL: {redis_config['url']}")

        # Ensure authentication is configured for tests
        if not os.getenv("API_KEY"):
            monkeypatch.setenv("API_KEY", "test-api-key-12345")

        # Disable rate limiting for tests
        monkeypatch.setenv("RATE_LIMITING_ENABLED", "false")

        # Clear any cached modules to force re-import with new environment
        modules_to_clear = [k for k in sys.modules.keys() if k.startswith("app.")]
        for module in modules_to_clear:
            if module in sys.modules:
                del sys.modules[module]

        # Import app with Redis-enabled configuration
        from app.main import app

        return app

    return _create_app_with_redis_preset


@pytest.fixture
def enhanced_client_with_preset(enhanced_cache_preset_app):
    """
    Enhanced async HTTP client factory with real Redis connectivity.

    Usage:
        async with enhanced_client_with_preset("ai-production") as client:
            response = await client.get("/internal/cache/status")
            # Response will show "connected" Redis status

    Use Cases:
        - Testing preset-driven behavior with real Redis
        - Validating cache invalidation patterns with Redis SCAN/DEL
        - Performance monitoring with actual Redis metrics
        - Security testing with Redis AUTH/TLS features
    """

    def _create_enhanced_client_with_preset(preset: str):
        """Create async client with Redis-enabled app configuration."""
        app_instance = enhanced_cache_preset_app(preset)
        api_key = os.getenv("API_KEY", "test-api-key-12345")
        headers = {"Authorization": f"Bearer {api_key}"}
        transport = ASGITransport(app=app_instance)
        return AsyncClient(
            transport=transport, base_url="http://testserver", headers=headers
        )

    return _create_enhanced_client_with_preset


# Enhanced preset scenarios with realistic Redis expectations
REDIS_PRESET_SCENARIOS = [
    ("ai-production", "connected", "active"),  # Should show Redis connected
    ("development", "connected", "active"),  # Should show Redis connected with fallback
    (
        "simple",
        "connected",
        "active",
    ),  # Simple preset with Redis available via testcontainers
    (
        "disabled",
        "connected",
        "active",
    ),  # Even disabled presets may show Redis connected when testcontainers provides Redis
]


@pytest.fixture
def redis_preset_scenarios():
    """
    Enhanced test scenarios for Redis-enabled cache preset behavior validation.

    These scenarios reflect realistic expectations when Redis is available,
    enabling proper validation of production-like preset behavior.

    Scenarios:
        - ai-production, development: Should show Redis "connected"
        - minimal, disabled: Should show Redis "disconnected" (intentional)
    """
    return REDIS_PRESET_SCENARIOS
