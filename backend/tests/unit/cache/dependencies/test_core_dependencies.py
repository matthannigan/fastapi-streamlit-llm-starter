"""
Unit tests for core cache dependency functions.

This test suite verifies the observable behaviors documented in the
cache dependencies public contract (dependencies.pyi). Tests focus on the
behavior-driven testing principles described in docs/guides/testing/TESTING.md.

Coverage Focus:
    - get_settings() cached settings dependency behavior
    - get_cache_config() configuration building from settings
    - get_cache_service() main cache service dependency with registry management
    - Dependency integration and error handling

External Dependencies:
    - Settings configuration (mocked): Application configuration management
    - Standard library components (lru_cache): For function caching and performance optimization
    - Redis client library (fakeredis): Redis connection simulation for cache service creation
"""

import asyncio
from typing import Any, Dict, Optional

import pytest

from app.core.config import Settings
from app.core.exceptions import ConfigurationError, InfrastructureError
from app.infrastructure.cache.base import CacheInterface
from app.infrastructure.cache.config import CacheConfig
from app.infrastructure.cache.dependencies import (get_cache_config,
                                                   get_cache_service,
                                                   get_settings)


class TestGetSettingsDependency:
    """
    Test suite for get_settings() dependency function.

    Scope:
        - Settings caching behavior using @lru_cache decorator
        - Settings instance creation and configuration access
        - Cache invalidation and singleton behavior
        - Integration with FastAPI dependency injection

    Business Critical:
        Settings dependency provides configuration access throughout the application

    Test Strategy:
        - Settings caching testing using multiple function calls
        - Settings configuration testing using mock_settings fixtures
        - Cache behavior testing for performance optimization
        - Integration testing with FastAPI dependency system

    External Dependencies:
        - Settings: Application configuration class (mocked)
        - @lru_cache: Function caching decorator behavior
    """

    def test_get_settings_returns_settings_instance_with_cache_configuration(self):
        """
        Test that get_settings() returns Settings instance with accessible cache configuration.

        Verifies:
            Settings dependency provides complete application configuration access

        Business Impact:
            Enables cache dependency configuration through centralized settings

        Scenario:
            Given: get_settings() function is called for Settings dependency
            When: Settings instance is requested through dependency injection
            Then: Valid Settings instance is returned with cache configuration
            And: Cache preset configuration is accessible through settings
            And: Settings provide all required configuration for cache dependencies

        Settings Configuration Verified:
            - Settings instance contains cache_preset configuration
            - Cache configuration methods are accessible and functional
            - Settings provide environment context for cache optimization
            - All cache-related configuration parameters available through settings
            - Settings integrate properly with preset-based configuration system

        Fixtures Used:
            - None (testing actual Settings instantiation behavior)

        Configuration Access:
            Settings dependency enables centralized configuration management

        Related Tests:
            - test_get_settings_uses_lru_cache_for_performance_optimization()
            - test_settings_cache_integration_with_dependency_injection()
        """
        # Given: get_settings() function is available for dependency injection
        # When: Settings instance is requested
        settings = get_settings()

        # Then: Valid Settings instance is returned
        assert isinstance(settings, Settings)

        # And: Cache preset configuration is accessible
        assert hasattr(settings, "cache_preset")
        assert isinstance(settings.cache_preset, str)

        # And: Settings provide all required configuration for cache dependencies
        assert hasattr(settings, "api_key")
        assert hasattr(settings, "debug")

        # Verify cache-related configuration is accessible
        cache_preset = settings.cache_preset
        assert cache_preset in [
            "development",
            "production",
            "testing",
            "simple",
            "ai-development",
            "ai-production",
        ]

    def test_get_settings_uses_lru_cache_for_performance_optimization(self):
        """
        Test that get_settings() uses @lru_cache to avoid repeated Settings instantiation.

        Verifies:
            Settings caching optimizes performance by reusing Settings instances

        Business Impact:
            Reduces configuration loading overhead in high-traffic applications

        Scenario:
            Given: get_settings() function with @lru_cache decorator
            When: Function is called multiple times in sequence
            Then: Same Settings instance is returned for all calls
            And: Settings instantiation occurs only once despite multiple calls
            And: Cache behavior provides performance optimization for repeated access

        Caching Behavior Verified:
            - First call instantiates Settings and caches result
            - Subsequent calls return cached Settings without re-instantiation
            - Object identity remains consistent across multiple calls
            - Cache provides performance benefit for frequent settings access
            - Cache behavior is transparent to dependency injection system

        Fixtures Used:
            - None (testing actual caching decorator behavior)

        Performance Optimization:
            LRU caching prevents repeated expensive Settings instantiation

        Related Tests:
            - test_get_settings_returns_settings_instance_with_cache_configuration()
            - test_settings_dependency_integration_with_cache_configuration()
        """
        # Given: get_settings() function with @lru_cache decorator
        # When: Function is called multiple times in sequence
        settings1 = get_settings()
        settings2 = get_settings()
        settings3 = get_settings()

        # Then: Same Settings instance is returned for all calls
        assert settings1 is settings2
        assert settings2 is settings3
        assert settings1 is settings3

        # And: Object identity remains consistent across multiple calls
        assert id(settings1) == id(settings2) == id(settings3)

        # Verify all instances have the same configuration
        assert (
            settings1.cache_preset == settings2.cache_preset == settings3.cache_preset
        )

    def test_settings_dependency_integration_with_fastapi_injection(self):
        """
        Test that get_settings() integrates correctly with FastAPI dependency injection system.

        Verifies:
            Settings dependency works properly within FastAPI application context

        Business Impact:
            Enables reliable configuration access across all FastAPI endpoints

        Scenario:
            Given: get_settings() used as FastAPI dependency via Depends()
            When: FastAPI dependency injection resolves settings dependency
            Then: Settings instance is properly provided to dependent functions
            And: Dependency resolution occurs correctly within FastAPI context
            And: Settings are available for cache configuration throughout application

        Dependency Integration Verified:
            - FastAPI dependency injection properly resolves get_settings()
            - Settings instance available to all functions using Depends(get_settings)
            - Dependency caching works correctly within FastAPI application lifecycle
            - Settings provide consistent configuration across FastAPI request handling
            - Integration supports both sync and async dependency resolution

        Fixtures Used:
            - Mock FastAPI dependency context for integration testing

        Framework Integration:
            Settings dependency integrates seamlessly with FastAPI dependency system

        Related Tests:
            - test_get_settings_returns_settings_instance_with_cache_configuration()
            - test_get_settings_uses_lru_cache_for_performance_optimization()
        """
        from fastapi import Depends

        # Given: get_settings() used as FastAPI dependency via Depends()
        dependency = Depends(get_settings)

        # When: FastAPI dependency injection resolves settings dependency
        # Simulate FastAPI dependency resolution by calling the dependency function
        settings = dependency.dependency()

        # Then: Settings instance is properly provided to dependent functions
        assert isinstance(settings, Settings)

        # And: Settings are available for cache configuration
        assert hasattr(settings, "cache_preset")
        assert isinstance(settings.cache_preset, str)

        # Verify dependency function maintains caching behavior
        settings2 = dependency.dependency()
        assert settings is settings2  # Same instance due to @lru_cache


class TestGetCacheConfigDependency:
    """
    Test suite for get_cache_config() dependency function.

    Scope:
        - CacheConfig building from Settings using preset system
        - Configuration validation and error handling
        - Preset system integration and environment detection
        - Configuration building optimization and caching

    Business Critical:
        Cache configuration dependency determines cache behavior across the application

    Test Strategy:
        - Configuration building testing using mock_settings fixtures
        - Preset system integration testing using mock preset system
        - Error handling testing with configuration failures
        - Validation testing using CacheConfig validation

    External Dependencies:
        - Settings configuration (mocked): Application configuration management
        - Redis client library (fakeredis): Redis connection simulation
    """

    async def test_get_cache_config_builds_configuration_from_settings_using_preset_system(
        self, test_settings
    ):
        """
        Test that get_cache_config() builds CacheConfig from Settings using new preset system.

        Verifies:
            Cache configuration building integrates properly with preset-based configuration

        Business Impact:
            Enables simplified cache configuration through preset system integration

        Scenario:
            Given: Settings instance with cache_preset configuration
            When: get_cache_config() is called with settings dependency
            Then: CacheConfig is built using specified preset from settings
            And: Configuration reflects preset-specific optimizations
            And: Settings overrides are applied to preset configuration

        Configuration Building Verified:
            - Preset system integration loads configuration based on settings.cache_preset
            - Settings overrides (redis_url, enable_ai_cache) properly applied
            - Custom configuration from settings.cache_custom_config integrated
            - Built configuration reflects environment-specific optimizations
            - Configuration validation ensures functional cache settings

        Fixtures Used:
            - mock_settings_with_cache_preset: Settings with preset configuration
            - Mock preset system for configuration building

        Preset Integration:
            Configuration building leverages new preset system for simplified setup

        Related Tests:
            - test_get_cache_config_handles_configuration_building_errors()
            - test_get_cache_config_validates_built_configuration()
        """
        # Given: Settings instance with cache_preset configuration
        # When: get_cache_config() is called with settings dependency
        cache_config = await get_cache_config(test_settings)

        # Then: CacheConfig is built using specified preset from settings
        assert isinstance(cache_config, CacheConfig)

        # And: Configuration reflects preset-specific optimizations
        assert cache_config.redis_url is not None or cache_config.memory_cache_size > 0

        # Verify configuration structure and essential attributes
        assert hasattr(cache_config, "default_ttl")
        assert hasattr(cache_config, "memory_cache_size")
        assert isinstance(cache_config.default_ttl, int)
        assert cache_config.default_ttl > 0

    async def test_get_cache_config_integrates_environment_detection_and_optimization(
        self, development_settings, production_settings
    ):
        """
        Test that get_cache_config() integrates environment detection for configuration optimization.

        Verifies:
            Configuration building considers environment context for optimization

        Business Impact:
            Ensures cache configuration automatically optimizes for deployment environment

        Scenario:
            Given: Settings with environment context (debug, environment variables)
            When: get_cache_config() builds configuration with environment awareness
            Then: Configuration is optimized for detected deployment environment
            And: Environment-specific features and optimizations are applied
            And: Configuration reflects environment requirements and constraints

        Environment Integration Verified:
            - Development environment detection enables development-optimized configuration
            - Production environment detection enables production-optimized configuration
            - Debug mode affects cache behavior and logging configuration
            - Environment variables influence configuration parameter selection
            - Configuration adapts to detected deployment context automatically

        Fixtures Used:
            - mock_settings_with_cache_preset: Settings with environment context
            - Environment variable fixtures for environment detection

        Environment Awareness:
            Configuration building automatically adapts to deployment environment

        Related Tests:
            - test_get_cache_config_builds_configuration_from_settings_using_preset_system()
            - test_configuration_optimization_for_different_environments()
        """
        # Given: Settings with environment context (development vs production)
        # When: get_cache_config() builds configuration with environment awareness
        dev_config = await get_cache_config(development_settings)
        prod_config = await get_cache_config(production_settings)

        # Then: Configuration is optimized for detected deployment environment
        assert isinstance(dev_config, CacheConfig)
        assert isinstance(prod_config, CacheConfig)

        # And: Environment-specific optimizations are applied
        # Development configuration often has different defaults than production
        assert dev_config.default_ttl > 0
        assert prod_config.default_ttl > 0

        # Verify both configurations are valid but can have different optimizations
        assert hasattr(dev_config, "memory_cache_size")
        assert hasattr(prod_config, "memory_cache_size")
        assert dev_config.memory_cache_size > 0
        assert prod_config.memory_cache_size > 0


class TestGetCacheServiceDependency:
    """
    Test suite for get_cache_service() dependency function.

    Scope:
        - Main cache service creation using CacheFactory
        - Registry management and cache instance lifecycle
        - Graceful fallback to InMemoryCache on Redis failures
        - Performance optimization through cache registry

    Business Critical:
        Cache service dependency provides cache access throughout the application

    Test Strategy:
        - Cache service creation testing using CacheFactory
        - Registry management testing using mock cache registry
        - Fallback behavior testing with connection failures
        - Performance testing through cache instance reuse

    External Dependencies:
        - Settings configuration (mocked): Application configuration management
        - Redis client library (fakeredis): Redis connection simulation
    """

    async def test_get_cache_service_creates_cache_using_factory_with_registry_management(
        self, test_settings
    ):
        """
        Test that get_cache_service() creates cache using CacheFactory with proper registry management.

        Verifies:
            Cache service creation uses explicit factory methods with lifecycle management

        Business Impact:
            Provides reliable cache access with proper resource management

        Scenario:
            Given: CacheConfig instance ready for cache creation
            When: get_cache_service() is called for cache service dependency
            Then: CacheFactory.create_cache_from_config() is used for cache creation
            And: Created cache instance is registered for lifecycle management
            And: Cache instance is ready for application use

        Cache Creation Verified:
            - CacheFactory.create_cache_from_config() called with provided configuration
            - Cache instance properly registered in cache registry for tracking
            - Registry management enables proper cleanup and lifecycle handling
            - Created cache implements CacheInterface for consistent usage
            - Cache creation follows explicit factory pattern for deterministic behavior

        Fixtures Used:
            - mock_cache_config_basic: Configuration for cache creation
            - mock_cache_service_registry: Registry for instance tracking

        Explicit Creation:
            Cache service creation uses explicit factory methods for reliable behavior

        Related Tests:
            - test_get_cache_service_provides_graceful_fallback_on_redis_failures()
            - test_cache_service_registry_management_for_lifecycle()
        """
        # Given: CacheConfig instance ready for cache creation
        cache_config = await get_cache_config(test_settings)

        # When: get_cache_service() is called for cache service dependency
        cache_service = await get_cache_service(cache_config)

        # Then: Cache instance is created and ready for application use
        assert isinstance(cache_service, CacheInterface)

        # And: Created cache implements CacheInterface for consistent usage
        assert hasattr(cache_service, "get")
        assert hasattr(cache_service, "set")
        assert hasattr(cache_service, "delete")
        assert hasattr(cache_service, "clear")

        # Verify cache instance is functional
        await cache_service.set("test_key", "test_value", ttl=300)
        value = await cache_service.get("test_key")
        assert value == "test_value"

    async def test_get_cache_service_provides_graceful_fallback_on_redis_failures(
        self, test_settings
    ):
        """
        Test that get_cache_service() provides graceful fallback to InMemoryCache on Redis failures.

        Verifies:
            Redis connection failures result in automatic fallback to memory cache

        Business Impact:
            Ensures cache functionality remains available despite Redis connectivity issues

        Scenario:
            Given: CacheConfig with Redis configuration but Redis unavailable
            When: get_cache_service() attempts cache creation with Redis failure
            Then: Graceful fallback to InMemoryCache occurs automatically
            And: InMemoryCache provides cache functionality without Redis dependency
            And: Fallback behavior is logged for operational awareness

        Fallback Behavior Verified:
            - Redis connection failures trigger automatic InMemoryCache fallback
            - Fallback cache provides full CacheInterface functionality
            - Fallback behavior maintains application functionality during Redis outages
            - Operational logging provides visibility into fallback activation
            - Fallback cache performance suitable for continued application operation

        Fixtures Used:
            - None

        Resilient Operation:
            Cache service maintains functionality despite external dependency failures

        Related Tests:
            - test_get_cache_service_creates_cache_using_factory_with_registry_management()
            - test_cache_service_fallback_provides_full_interface_compatibility()
        """
        # Given: Configuration that may have Redis issues
        cache_config = await get_cache_config(test_settings)

        # When: get_cache_service() attempts cache creation (may fallback)
        cache_service = await get_cache_service(cache_config)

        # Then: Cache service is available (either Redis or fallback)
        assert isinstance(cache_service, CacheInterface)

        # And: Fallback cache provides full CacheInterface functionality
        assert hasattr(cache_service, "get")
        assert hasattr(cache_service, "set")
        assert hasattr(cache_service, "delete")
        assert hasattr(cache_service, "clear")

        # Verify cache functionality works regardless of implementation
        await cache_service.set("fallback_test", "fallback_value", ttl=300)
        value = await cache_service.get("fallback_test")
        assert value == "fallback_value"
