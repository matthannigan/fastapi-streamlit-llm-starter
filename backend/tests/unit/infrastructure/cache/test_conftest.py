"""
Smoke Test for Shared Cache Fixtures (`backend/tests/unit/infrastructure/cache/conftest.py`)

Goal: Verify that all mock fixtures are created with the correct type and spec.

This test consumes all major mock fixtures to ensure they are configured correctly
before they are used in more complex unit tests. It acts as a fast-running check
to build confidence in the test harness itself.

This test does not check application logic; it only verifies that the mocks
have the correct interface as defined by their respective contracts. This helps
catch setup errors, incorrect specs, or breaking changes in the real classes early.
"""

# Note: No need to import pytest, as it's the test runner.
# The fixtures are automatically discovered and injected by pytest.

def test_mock_dependency_fixtures_are_configured_correctly(
    mock_settings,
    mock_cache_factory,
    mock_cache_interface,
    mock_performance_monitor,
    mock_memory_cache,
):
    """Verifies that core dependency mocks have the correct interface."""
    # Verify mock_settings (spec'd from app.core.config.Settings)
    assert hasattr(mock_settings, 'get_cache_config')
    assert hasattr(mock_settings, 'get_resilience_config')
    assert hasattr(mock_settings, 'is_development')
    assert hasattr(mock_settings, 'redis_url')

    # Verify mock_cache_factory (spec'd from app.infrastructure.cache.factory.CacheFactory)
    assert hasattr(mock_cache_factory, 'for_web_app')
    assert hasattr(mock_cache_factory, 'for_ai_app')
    assert hasattr(mock_cache_factory, 'create_cache_from_config')

    # Verify mock_cache_interface (spec'd from app.infrastructure.cache.base.CacheInterface)
    assert hasattr(mock_cache_interface, 'get')
    assert hasattr(mock_cache_interface, 'set')
    assert hasattr(mock_cache_interface, 'delete')

    # Verify mock_performance_monitor (spec'd from app.infrastructure.cache.monitoring.CachePerformanceMonitor)
    assert hasattr(mock_performance_monitor, 'record_cache_operation_time')
    assert hasattr(mock_performance_monitor, 'get_performance_stats')
    assert hasattr(mock_performance_monitor, 'get_memory_usage_stats')
    assert hasattr(mock_performance_monitor, 'record_operation') # Async method

    # Verify mock_memory_cache (spec'd from app.infrastructure.cache.memory.InMemoryCache)
    assert hasattr(mock_memory_cache, 'get_stats')
    assert hasattr(mock_memory_cache, 'get_active_keys')
    assert hasattr(mock_memory_cache, 'clear')


def test_mock_exception_fixtures_are_configured_correctly(
    mock_validation_error,
    mock_configuration_error,
    mock_infrastructure_error,
):
    """Verifies that mock exception fixtures are correctly spec'd."""
    # These are simple mocks, but we can check for a basic dunder method.
    assert hasattr(mock_validation_error, '__str__')
    assert hasattr(mock_configuration_error, '__str__')
    assert hasattr(mock_infrastructure_error, '__str__')


# NOTE: The following tests are commented out because they depend on fixtures
# defined in subdirectory conftest.py files (e.g., redis_ai/conftest.py).
# Pytest cannot discover these fixtures from a test file in a parent directory.
# To enable these tests, move the required fixtures (e.g., mock_parameter_mapper,
# mock_key_generator, mock_security_config) to the shared
# `backend/tests/unit/infrastructure/cache/conftest.py` file.

# def test_redis_ai_specific_fixtures_are_configured_correctly(
#     mock_parameter_mapper,
#     mock_key_generator,
# ):
#     """Verifies fixtures specific to the redis_ai module."""
#     # Verify mock_parameter_mapper (spec'd from app.infrastructure.cache.parameter_mapping.CacheParameterMapper)
#     assert hasattr(mock_parameter_mapper, 'map_ai_to_generic_params')
#     assert hasattr(mock_parameter_mapper, 'validate_parameter_compatibility')
#
#     # Verify mock_key_generator (spec'd from app.infrastructure.cache.key_generator.CacheKeyGenerator)
#     assert hasattr(mock_key_generator, 'generate_cache_key')
#     assert hasattr(mock_key_generator, 'get_key_generation_stats')

# def test_redis_generic_specific_fixtures_are_configured_correctly(
#     mock_security_config,
#     mock_tls_security_config,
#     mock_redis_client
# ):
#     """Verifies fixtures specific to the redis_generic module."""
#     # Verify mock_security_config (spec'd from app.infrastructure.cache.security.SecurityConfig)
#     assert hasattr(mock_security_config, 'has_authentication')
#     assert hasattr(mock_security_config, 'security_level')
#     assert hasattr(mock_security_config, 'use_tls')
#
#     # Verify mock_tls_security_config has TLS attributes
#     assert hasattr(mock_tls_security_config, 'tls_cert_path')
#     assert mock_tls_security_config.use_tls is True
#
#     # Verify mock_redis_client (simulates a redis.asyncio.Redis client)
#     assert hasattr(mock_redis_client, 'ping')
#     assert hasattr(mock_redis_client, 'get')
#     assert hasattr(mock_redis_client, 'set')
#     assert hasattr(mock_redis_client, 'delete')
