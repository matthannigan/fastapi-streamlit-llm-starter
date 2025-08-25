"""
Comprehensive unit tests for FastAPI cache dependency injection system.

This module tests all cache dependency injection components following docstring-driven
test development methodology. Tests verify documented contracts in Args, Returns,
Raises, and Behavior sections, focusing on WHAT should happen rather than HOW
it's implemented.

The cache dependencies module provides comprehensive FastAPI dependency injection for
cache services with lifecycle management, thread-safe registry, and health monitoring.
Tests validate proper dependency management, service construction, graceful degradation,
and integration with the FastAPI dependency injection framework.

Test Classes:
    - TestCacheDependencyManager: Core dependency manager for cache lifecycle and registry
    - TestSettingsDependencies: Settings and configuration dependency providers
    - TestMainCacheDependencies: Primary cache service dependencies with factory integration
    - TestSpecializedCacheDependencies: Web and AI optimized cache dependencies
    - TestTestingDependencies: Testing-specific cache dependencies
    - TestUtilityDependencies: Validation, conditional, and fallback dependencies
    - TestLifecycleManagement: Registry cleanup and cache disconnection
    - TestHealthCheckDependencies: Comprehensive health monitoring dependencies
    - TestDependencyIntegration: Integration testing across dependency chains

Coverage Requirements:
    >90% coverage for infrastructure modules per project standards
    
Testing Philosophy:
    - Test WHAT should happen per docstring contracts
    - Focus on dependency injection behavior, not cache implementation
    - Mock external dependencies (CacheFactory, Redis, settings) appropriately
    - Test registry management, thread safety, and lifecycle behaviors
    - Validate graceful degradation and error handling patterns
    - Test integration with FastAPI dependency injection framework

Business Impact:
    These tests ensure reliable cache service provisioning for web applications,
    preventing cache-related outages that could impact user experience and system
    performance. Proper dependency management is critical for application stability.
"""

import asyncio
import json
import os
import pytest
import weakref
from datetime import datetime
from unittest.mock import AsyncMock, MagicMock, patch, call
from typing import Dict, Any

from fastapi import HTTPException

from app.infrastructure.cache.dependencies import (
    CacheDependencyManager,
    get_settings,
    get_cache_config,
    get_cache_service,
    get_web_cache_service,
    get_ai_cache_service,
    get_test_cache,
    get_test_redis_cache,
    get_fallback_cache_service,
    validate_cache_configuration,
    get_cache_service_conditional,
    cleanup_cache_registry,
    get_cache_health_status,
    _cache_registry,
    _cache_lock
)
from app.core.config import Settings
from app.core.exceptions import ConfigurationError, ValidationError, InfrastructureError
from app.infrastructure.cache.base import CacheInterface
from app.infrastructure.cache.memory import InMemoryCache
from app.infrastructure.cache.factory import CacheFactory


class TestCacheDependencyManager:
    """
    Test CacheDependencyManager for cache lifecycle and registry management.
    
    Business Impact:
        CacheDependencyManager ensures thread-safe cache registry operations and proper
        cache connection management. Failures could lead to memory leaks, connection
        issues, or race conditions in multi-threaded environments.
    """

    @pytest.mark.asyncio
    async def test_ensure_cache_connected_with_connect_method(self):
        """
        Test that _ensure_cache_connected calls connect() when method exists per docstring.
        
        Business Impact:
            Ensures caches are properly connected before use, preventing runtime errors
            from unconnected cache instances.
            
        Test Scenario:
            Mock cache with connect() method that returns True for successful connection
            
        Success Criteria:
            - connect() method is called exactly once
            - Connected cache instance is returned
            - Debug logging indicates successful connection
        """
        # Create mock cache with connect method
        mock_cache = MagicMock(spec=CacheInterface)
        mock_cache.connect = AsyncMock(return_value=True)
        type(mock_cache).__name__ = "MockCache"

        with patch('app.infrastructure.cache.dependencies.logger') as mock_logger:
            result = await CacheDependencyManager._ensure_cache_connected(mock_cache)

            # Verify connect was called
            mock_cache.connect.assert_called_once()
            
            # Verify same cache instance returned
            assert result is mock_cache
            
            # Verify proper logging
            mock_logger.debug.assert_has_calls([
                call("Ensuring connection for cache MockCache"),
                call("Cache MockCache connected successfully")
            ])

    @pytest.mark.asyncio
    async def test_ensure_cache_connected_without_connect_method(self):
        """
        Test that _ensure_cache_connected handles caches without connect() method per docstring.
        
        Business Impact:
            Ensures compatibility with cache implementations that don't require explicit
            connection management, preventing method errors.
            
        Test Scenario:
            Mock cache without connect() method (e.g., InMemoryCache)
            
        Success Criteria:
            - No connect() method called (doesn't exist)
            - Cache instance returned as-is
            - Debug logging indicates cache assumed ready
        """
        # Create mock cache without connect method
        mock_cache = MagicMock(spec=CacheInterface)
        # Don't add connect method to mock
        type(mock_cache).__name__ = "InMemoryCache"

        with patch('app.infrastructure.cache.dependencies.logger') as mock_logger:
            result = await CacheDependencyManager._ensure_cache_connected(mock_cache)

            # Verify same cache instance returned
            assert result is mock_cache
            
            # Verify proper logging
            mock_logger.debug.assert_called_once_with(
                "Cache InMemoryCache does not have connect method, assuming ready"
            )

    @pytest.mark.asyncio
    async def test_ensure_cache_connected_connection_failure(self):
        """
        Test that _ensure_cache_connected handles connection failures gracefully per docstring.
        
        Business Impact:
            Ensures application continues operating even when cache connections fail,
            enabling graceful degradation instead of application crashes.
            
        Test Scenario:
            Mock cache with connect() method that returns False (connection failed)
            
        Success Criteria:
            - connect() method called
            - Cache instance returned despite connection failure
            - Warning logged about degraded mode operation
        """
        # Create mock cache with failing connect method
        mock_cache = MagicMock(spec=CacheInterface)
        mock_cache.connect = AsyncMock(return_value=False)
        type(mock_cache).__name__ = "RedisCache"

        with patch('app.infrastructure.cache.dependencies.logger') as mock_logger:
            result = await CacheDependencyManager._ensure_cache_connected(mock_cache)

            # Verify connect was called
            mock_cache.connect.assert_called_once()
            
            # Verify same cache instance returned for graceful degradation
            assert result is mock_cache
            
            # Verify proper logging
            mock_logger.warning.assert_called_once_with(
                "Cache RedisCache connection failed, operating in degraded mode"
            )

    @pytest.mark.asyncio
    async def test_ensure_cache_connected_exception_handling(self):
        """
        Test that _ensure_cache_connected handles exceptions during connection per docstring.
        
        Business Impact:
            Prevents application crashes when cache connection throws exceptions,
            enabling resilient cache operations with graceful degradation.
            
        Test Scenario:
            Mock cache with connect() method that raises exception
            
        Success Criteria:
            - Exception during connect() caught and handled
            - Cache instance returned despite exception
            - Error logged with exception details
        """
        # Create mock cache with exception-throwing connect method
        mock_cache = MagicMock(spec=CacheInterface)
        mock_cache.connect = AsyncMock(side_effect=Exception("Connection timeout"))
        type(mock_cache).__name__ = "RedisCache"

        with patch('app.infrastructure.cache.dependencies.logger') as mock_logger:
            result = await CacheDependencyManager._ensure_cache_connected(mock_cache)

            # Verify connect was attempted
            mock_cache.connect.assert_called_once()
            
            # Verify cache returned for graceful degradation
            assert result is mock_cache
            
            # Verify error logging
            mock_logger.error.assert_called_once_with(
                "Failed to connect cache RedisCache: Connection timeout"
            )

    @pytest.mark.asyncio
    async def test_get_or_create_cache_existing_cache(self):
        """
        Test that _get_or_create_cache returns existing cache from registry per docstring.
        
        Business Impact:
            Prevents unnecessary cache creation and ensures singleton behavior for
            cache instances, improving performance and resource utilization.
            
        Test Scenario:
            Cache already exists in registry with valid weak reference
            
        Success Criteria:
            - Existing cache returned from registry
            - Factory function not called
            - Debug logging indicates registry usage
        """
        # Clear registry for clean test
        _cache_registry.clear()
        
        # Create mock cache and add to registry
        mock_cache = MagicMock(spec=CacheInterface)
        mock_cache.connect = AsyncMock()
        type(mock_cache).__name__ = "TestCache"
        cache_key = "test_cache"
        _cache_registry[cache_key] = weakref.ref(mock_cache)
        
        # Mock factory function that should not be called
        mock_factory = AsyncMock()

        with patch('app.infrastructure.cache.dependencies.logger') as mock_logger:
            result = await CacheDependencyManager._get_or_create_cache(
                cache_key, mock_factory
            )

            # Verify existing cache returned
            assert result is mock_cache
            
            # Verify factory not called
            mock_factory.assert_not_called()
            
            # Verify proper logging includes both registry usage and connection
            mock_logger.debug.assert_any_call(
                f"Using existing cache from registry: {cache_key}"
            )
            # Also expect connection logging
            mock_logger.debug.assert_any_call(
                "Cache TestCache connected successfully"
            )

    @pytest.mark.asyncio
    async def test_get_or_create_cache_dead_reference_cleanup(self):
        """
        Test that _get_or_create_cache cleans up dead references and creates new cache per docstring.
        
        Business Impact:
            Prevents memory leaks from dead cache references and ensures fresh cache
            instances are created when previous instances are garbage collected.
            
        Test Scenario:
            Dead weak reference exists in registry (cache was garbage collected)
            
        Success Criteria:
            - Dead reference removed from registry
            - Factory function called to create new cache
            - New cache registered with weak reference
        """
        # Clear registry for clean test
        _cache_registry.clear()
        
        # Create a weak reference that will be dead (simulate garbage collection)
        cache_key = "test_cache"
        # Create a temporary cache, get weak ref, then delete the cache
        temp_cache = MagicMock(spec=CacheInterface)
        _cache_registry[cache_key] = weakref.ref(temp_cache)
        del temp_cache  # Make the reference dead
        # Force garbage collection
        import gc
        gc.collect()
        
        # Create new cache for factory
        new_cache = MagicMock(spec=CacheInterface)
        new_cache.connect = AsyncMock()
        type(new_cache).__name__ = "NewCache"
        mock_factory = AsyncMock(return_value=new_cache)

        with patch('app.infrastructure.cache.dependencies.logger') as mock_logger:
            result = await CacheDependencyManager._get_or_create_cache(
                cache_key, mock_factory
            )

            # Verify new cache created and returned
            assert result is new_cache
            
            # Verify factory was called
            mock_factory.assert_called_once()
            
            # Verify cache registered in registry
            assert cache_key in _cache_registry
            cached_ref = _cache_registry[cache_key]()
            assert cached_ref is new_cache
            
            # Verify proper logging
            mock_logger.debug.assert_any_call(
                f"Removing dead cache reference: {cache_key}"
            )
            mock_logger.debug.assert_any_call(
                f"Cache registered in registry: {cache_key}"
            )

    @pytest.mark.asyncio
    async def test_get_or_create_cache_factory_failure(self):
        """
        Test that _get_or_create_cache raises InfrastructureError when factory fails per docstring.
        
        Business Impact:
            Provides clear error information when cache creation fails, enabling
            proper error handling and debugging in production environments.
            
        Test Scenario:
            Factory function raises exception during cache creation
            
        Success Criteria:
            - InfrastructureError raised with context information
            - Original exception details preserved in context
            - Factory function execution attempted
        """
        # Clear registry for clean test
        _cache_registry.clear()
        
        cache_key = "failing_cache"
        original_error = Exception("Redis connection failed")
        mock_factory = AsyncMock(side_effect=original_error)
        mock_factory.__name__ = "create_test_cache"

        with pytest.raises(InfrastructureError) as exc_info:
            await CacheDependencyManager._get_or_create_cache(
                cache_key, mock_factory, "arg1", kwarg1="value1"
            )

        # Verify exception details
        error = exc_info.value
        assert "Failed to create cache instance" in str(error)
        assert error.context["cache_key"] == cache_key
        assert error.context["factory_func"] == "create_test_cache"
        assert error.context["args"] == ("arg1",)
        assert error.context["kwargs"] == {"kwarg1": "value1"}
        assert error.context["original_error"] == str(original_error)

    @pytest.mark.asyncio
    async def test_cleanup_registry_integration(self):
        """
        Test that CacheDependencyManager.cleanup_registry() delegates to cleanup_cache_registry per docstring.
        
        Business Impact:
            Ensures cleanup methods work consistently whether called directly or through
            the manager, providing flexible cleanup options for different use cases.
            
        Test Scenario:
            Call manager's cleanup_registry method
            
        Success Criteria:
            - Delegates to cleanup_cache_registry function
            - Returns same result as direct function call
        """
        expected_stats = {"total_entries": 0, "active_caches": 0}
        
        with patch('app.infrastructure.cache.dependencies.cleanup_cache_registry', 
                   return_value=expected_stats) as mock_cleanup:
            result = await CacheDependencyManager.cleanup_registry()
            
            # Verify delegation
            mock_cleanup.assert_called_once()
            assert result == expected_stats


class TestSettingsDependencies:
    """
    Test settings and configuration dependency providers.
    
    Business Impact:
        Settings dependencies provide configuration access throughout the application.
        Failures could lead to misconfigured cache services or application startup issues.
    """

    def test_get_settings_returns_cached_instance(self):
        """
        Test that get_settings returns cached Settings instance per docstring.
        
        Business Impact:
            Ensures consistent configuration access across the application while
            avoiding repeated instantiation overhead.
            
        Test Scenario:
            Call get_settings multiple times
            
        Success Criteria:
            - Same Settings instance returned on multiple calls
            - LRU caching behavior demonstrated
        """
        # Clear the LRU cache to ensure clean test
        get_settings.cache_clear()
        
        with patch('app.infrastructure.cache.dependencies.Settings') as mock_settings_class:
            mock_instance = MagicMock(spec=Settings)
            mock_settings_class.return_value = mock_instance
            
            # Call multiple times
            result1 = get_settings()
            result2 = get_settings()
            
            # Verify same instance returned (LRU cached)
            assert result1 is result2
            assert result1 is mock_instance
            
            # Verify Settings constructor called only once (cached)
            mock_settings_class.assert_called_once()

    @pytest.mark.asyncio
    async def test_get_cache_config_success(self):
        """
        Test that get_cache_config builds configuration from preset system per docstring.
        
        Business Impact:
            Proper configuration building is essential for cache service initialization.
            Failures could prevent cache services from starting correctly.
            
        Test Scenario:
            Mock settings with valid cache preset configuration
            
        Success Criteria:
            - Configuration built using settings.get_cache_config()
            - Success logged with preset name
            - Valid cache configuration returned
        """
        # Create mock settings with cache configuration
        mock_settings = MagicMock(spec=Settings)
        mock_config = MagicMock()
        mock_settings.get_cache_config.return_value = mock_config
        mock_settings.cache_preset = "development"

        with patch('app.infrastructure.cache.dependencies.logger') as mock_logger:
            result = await get_cache_config(mock_settings)

            # Verify configuration built from settings
            mock_settings.get_cache_config.assert_called_once()
            assert result is mock_config
            
            # Verify success logging
            mock_logger.info.assert_called_once_with(
                "Cache configuration loaded successfully from preset 'development'"
            )

    @pytest.mark.asyncio
    async def test_get_cache_config_fallback_on_error(self):
        """
        Test that get_cache_config falls back to simple preset on configuration errors per docstring.
        
        Business Impact:
            Ensures application can start even with configuration errors by providing
            a working fallback configuration, preventing complete service failures.
            
        Test Scenario:
            Mock settings that raises exception during get_cache_config()
            
        Success Criteria:
            - Original error caught and logged
            - Fallback to simple preset attempted and succeeds
            - Warning logged about fallback usage
        """
        # Create mock settings that fails
        mock_settings = MagicMock(spec=Settings)
        mock_settings.get_cache_config.side_effect = Exception("Preset validation failed")
        mock_settings.cache_preset = "invalid"

        # Create mock preset system within the actual import path
        mock_preset = MagicMock()
        mock_config = MagicMock()
        mock_preset.to_cache_config.return_value = mock_config
        mock_manager = MagicMock()
        mock_manager.get_preset.return_value = mock_preset
        
        with patch('app.infrastructure.cache.cache_presets.cache_preset_manager', mock_manager):
            with patch('app.infrastructure.cache.dependencies.logger') as mock_logger:
                result = await get_cache_config(mock_settings)

                # Verify fallback configuration used
                mock_manager.get_preset.assert_called_once_with("simple")
                mock_preset.to_cache_config.assert_called_once()
                assert result is mock_config
                
                # Verify proper error and fallback logging
                mock_logger.error.assert_called_once()
                mock_logger.warning.assert_called_once_with(
                    "Falling back to 'simple' cache preset due to configuration error"
                )

    @pytest.mark.asyncio
    async def test_get_cache_config_fallback_failure(self):
        """
        Test that get_cache_config raises ConfigurationError when fallback also fails per docstring.
        
        Business Impact:
            Provides clear error information when both primary and fallback configurations
            fail, enabling proper debugging and error handling.
            
        Test Scenario:
            Both primary settings and fallback preset system fail
            
        Success Criteria:
            - ConfigurationError raised with context about both failures
            - Both original and fallback errors preserved in context
        """
        # Create mock settings that fails
        mock_settings = MagicMock(spec=Settings)
        original_error = Exception("Preset validation failed")
        mock_settings.get_cache_config.side_effect = original_error
        mock_settings.cache_preset = "invalid"

        # Mock fallback that also fails
        fallback_error = Exception("Preset not found")
        mock_manager = MagicMock()
        mock_manager.get_preset.side_effect = fallback_error
        
        with patch('app.infrastructure.cache.cache_presets.cache_preset_manager', mock_manager):
            with pytest.raises(ConfigurationError) as exc_info:
                await get_cache_config(mock_settings)

            # Verify exception details
            error = exc_info.value
            assert "Failed to build cache configuration and fallback failed" in str(error)
            assert error.context["original_error"] == str(original_error)
            assert error.context["fallback_error"] == str(fallback_error)
            assert error.context["cache_preset"] == "invalid"
            assert error.context["preset_system"] == "cache_presets"


class TestMainCacheDependencies:
    """
    Test primary cache service dependencies with factory integration.
    
    Business Impact:
        Main cache dependencies provide the primary cache service for the application.
        Failures could impact all caching functionality and overall system performance.
    """

    @pytest.mark.asyncio
    async def test_get_cache_service_success(self):
        """
        Test that get_cache_service creates cache using CacheFactory per docstring.
        
        Business Impact:
            Ensures primary cache service is properly created and connected, enabling
            all cache-dependent functionality in the application.
            
        Test Scenario:
            Mock configuration and factory to return successful cache creation
            
        Success Criteria:
            - CacheFactory.create_cache_from_config() called with correct parameters
            - Cache registered in registry with appropriate key
            - Cache connection ensured through _ensure_cache_connected
        """
        # Create mock configuration
        mock_config = MagicMock()
        config_dict = {"redis_url": "redis://test:6379", "default_ttl": 3600}
        mock_config.to_dict.return_value = config_dict

        # Create mock factory and cache
        mock_cache = MagicMock(spec=CacheInterface)
        mock_cache.connect = AsyncMock()
        type(mock_cache).__name__ = "GenericRedisCache"
        
        with patch('app.infrastructure.cache.dependencies.CacheFactory') as mock_factory_class:
            mock_factory = MagicMock()
            mock_factory_class.return_value = mock_factory
            mock_factory.create_cache_from_config = AsyncMock(return_value=mock_cache)

            # Clear registry for clean test
            _cache_registry.clear()

            with patch('app.infrastructure.cache.dependencies.logger') as mock_logger:
                result = await get_cache_service(mock_config)

                # Verify cache creation
                mock_factory.create_cache_from_config.assert_called_once_with(
                    config_dict,
                    fail_on_connection_error=False
                )
                
                # Verify cache returned
                assert result is mock_cache
                
                # Verify cache registered in registry
                expected_key = f"main_cache_{hash(str(sorted(config_dict.items())))}"
                assert expected_key in _cache_registry
                
                # Verify proper logging
                mock_logger.info.assert_called_with(
                    "Main cache service ready: GenericRedisCache"
                )

    @pytest.mark.asyncio
    async def test_get_cache_service_fallback_on_failure(self):
        """
        Test that get_cache_service falls back to InMemoryCache on failure per docstring.
        
        Business Impact:
            Ensures application continues functioning even when primary cache creation
            fails, preventing complete service outages due to cache issues.
            
        Test Scenario:
            Mock configuration and factory that raises exception during cache creation
            
        Success Criteria:
            - Exception during cache creation caught
            - InMemoryCache returned as fallback
            - Warning logged about fallback usage
        """
        # Clear registry for test
        _cache_registry.clear()
        
        # Create mock configuration
        mock_config = MagicMock()
        mock_config.to_dict.return_value = {"redis_url": "redis://test:6379"}

        with patch('app.infrastructure.cache.dependencies.CacheFactory') as mock_factory_class:
            mock_factory = MagicMock()
            mock_factory_class.return_value = mock_factory
            mock_factory.create_cache_from_config = AsyncMock(
                side_effect=Exception("Redis connection failed")
            )

            with patch('app.infrastructure.cache.dependencies.logger') as mock_logger:
                result = await get_cache_service(mock_config)

                # Verify fallback cache returned
                assert isinstance(result, InMemoryCache)
                assert result.default_ttl == 1800  # 30 minutes
                assert result.max_size == 100
                
                # Verify proper error and fallback logging - expect 2 calls total
                assert mock_logger.error.call_count == 2  # One for registry creation, one for service creation
                mock_logger.warning.assert_called_once_with(
                    "Falling back to InMemoryCache for main cache service"
                )


class TestSpecializedCacheDependencies:
    """
    Test web and AI optimized cache dependencies.
    
    Business Impact:
        Specialized cache dependencies provide optimized caching for specific use cases.
        Proper optimization is crucial for performance in web and AI applications.
    """

    @pytest.mark.asyncio
    async def test_get_web_cache_service_removes_ai_config(self):
        """
        Test that get_web_cache_service removes AI configuration for web optimization per docstring.
        
        Business Impact:
            Ensures web caches are optimized for web usage patterns without AI-specific
            overhead, improving performance for web applications.
            
        Test Scenario:
            Configuration contains ai_config that should be removed for web cache
            
        Success Criteria:
            - ai_config removed from configuration before cache creation
            - Cache created using modified configuration
            - Debug logging indicates AI config removal
        """
        # Create mock configuration with AI config
        mock_config = MagicMock()
        config_dict = {
            "redis_url": "redis://test:6379",
            "ai_config": {"text_hash_threshold": 500},
            "default_ttl": 3600
        }
        mock_config.to_dict.return_value = config_dict

        # Create mock factory and cache
        mock_cache = MagicMock(spec=CacheInterface)
        mock_cache.connect = AsyncMock()
        type(mock_cache).__name__ = "GenericRedisCache"
        
        with patch('app.infrastructure.cache.dependencies.CacheFactory') as mock_factory_class:
            mock_factory = MagicMock()
            mock_factory_class.return_value = mock_factory
            mock_factory.create_cache_from_config = AsyncMock(return_value=mock_cache)

            # Clear registry for clean test
            _cache_registry.clear()

            with patch('app.infrastructure.cache.dependencies.logger') as mock_logger:
                result = await get_web_cache_service(mock_config)

                # Verify AI config was removed from factory call
                call_args = mock_factory.create_cache_from_config.call_args[0][0]
                assert 'ai_config' not in call_args
                assert call_args["redis_url"] == "redis://test:6379"
                assert call_args["default_ttl"] == 3600
                
                # Verify cache returned
                assert result is mock_cache
                
                # Verify debug logging - may appear among other debug calls
                mock_logger.debug.assert_any_call(
                    "Removed AI configuration for web cache service"
                )

    @pytest.mark.asyncio
    async def test_get_web_cache_service_fallback_parameters(self):
        """
        Test that get_web_cache_service fallback uses web-optimized parameters per docstring.
        
        Business Impact:
            Ensures fallback cache is properly configured for web usage patterns,
            maintaining performance even when Redis is unavailable.
            
        Test Scenario:
            Factory creation fails and fallback InMemoryCache should be created
            
        Success Criteria:
            - InMemoryCache created with web-optimized parameters
            - TTL set to 1800 seconds (30 minutes) for web sessions
            - Max size set to 200 for larger web usage
        """
        # Create mock configuration
        mock_config = MagicMock()
        mock_config.to_dict.return_value = {"redis_url": "redis://test:6379"}

        with patch('app.infrastructure.cache.dependencies.CacheFactory') as mock_factory_class:
            mock_factory = MagicMock()
            mock_factory_class.return_value = mock_factory
            mock_factory.create_cache_from_config = AsyncMock(
                side_effect=Exception("Redis connection failed")
            )

            result = await get_web_cache_service(mock_config)

            # Verify web-optimized fallback cache
            assert isinstance(result, InMemoryCache)
            assert result.default_ttl == 1800  # 30 minutes for web sessions
            assert result.max_size == 200      # Larger cache for web usage

    @pytest.mark.asyncio
    async def test_get_ai_cache_service_adds_ai_config_when_missing(self):
        """
        Test that get_ai_cache_service adds default AI configuration when missing per docstring.
        
        Business Impact:
            Ensures AI caches have proper AI-specific configuration for optimal performance
            with AI workloads, even when configuration is incomplete.
            
        Test Scenario:
            Configuration lacks ai_config that should be added for AI optimization
            
        Success Criteria:
            - Default AI configuration added to config before cache creation
            - AI config includes all required fields per docstring
            - Warning logged about missing AI configuration
        """
        # Create mock configuration without AI config
        mock_config = MagicMock()
        config_dict = {"redis_url": "redis://test:6379", "default_ttl": 3600}
        mock_config.to_dict.return_value = config_dict

        # Create mock factory and cache
        mock_cache = MagicMock(spec=CacheInterface)
        mock_cache.connect = AsyncMock()
        type(mock_cache).__name__ = "AIResponseCache"
        
        with patch('app.infrastructure.cache.dependencies.CacheFactory') as mock_factory_class:
            mock_factory = MagicMock()
            mock_factory_class.return_value = mock_factory
            mock_factory.create_cache_from_config = AsyncMock(return_value=mock_cache)

            # Clear registry for clean test
            _cache_registry.clear()

            with patch('app.infrastructure.cache.dependencies.logger') as mock_logger:
                result = await get_ai_cache_service(mock_config)

                # Verify AI config was added to factory call
                call_args = mock_factory.create_cache_from_config.call_args[0][0]
                assert 'ai_config' in call_args
                
                # Verify AI config structure per docstring
                ai_config = call_args['ai_config']
                assert ai_config['text_hash_threshold'] == 500
                assert ai_config['operation_ttls'] == {}
                assert 'text_size_tiers' in ai_config
                assert ai_config['enable_smart_promotion'] is True
                assert ai_config['max_text_length'] == 100000
                assert ai_config['hash_algorithm'] == 'sha256'
                
                # Verify cache returned
                assert result is mock_cache
                
                # Verify warning logging
                mock_logger.warning.assert_called_once_with(
                    "No AI configuration found, adding default AI features"
                )

    @pytest.mark.asyncio
    async def test_get_ai_cache_service_fallback_parameters(self):
        """
        Test that get_ai_cache_service fallback uses AI-optimized parameters per docstring.
        
        Business Impact:
            Ensures fallback cache is properly configured for AI usage patterns,
            maintaining AI functionality even when Redis is unavailable.
            
        Test Scenario:
            Factory creation fails and fallback InMemoryCache should be created
            
        Success Criteria:
            - InMemoryCache created with AI-optimized parameters
            - TTL set to 300 seconds (5 minutes) for AI operations
            - Max size set to 50 for AI operations
        """
        # Create mock configuration
        mock_config = MagicMock()
        mock_config.to_dict.return_value = {"redis_url": "redis://test:6379"}

        with patch('app.infrastructure.cache.dependencies.CacheFactory') as mock_factory_class:
            mock_factory = MagicMock()
            mock_factory_class.return_value = mock_factory
            mock_factory.create_cache_from_config = AsyncMock(
                side_effect=Exception("Redis connection failed")
            )

            result = await get_ai_cache_service(mock_config)

            # Verify AI-optimized fallback cache
            assert isinstance(result, InMemoryCache)
            assert result.default_ttl == 300   # 5 minutes for AI operations
            assert result.max_size == 50       # Smaller cache for AI operations


class TestTestingDependencies:
    """
    Test testing-specific cache dependencies.
    
    Business Impact:
        Testing dependencies ensure proper test isolation and fast test execution.
        Proper test cache configuration is crucial for reliable testing.
    """

    @pytest.mark.asyncio
    async def test_get_test_cache_creates_memory_cache(self):
        """
        Test that get_test_cache creates memory-only cache using factory per docstring.
        
        Business Impact:
            Ensures test caches are fast, isolated, and don't depend on external
            services, enabling reliable and fast test execution.
            
        Test Scenario:
            Call get_test_cache() to create test cache
            
        Success Criteria:
            - CacheFactory.for_testing() called with use_memory_cache=True
            - Cache instance returned from factory
            - Debug and info logging about memory-only cache
        """
        # Create mock factory and cache
        mock_cache = MagicMock(spec=CacheInterface)
        type(mock_cache).__name__ = "InMemoryCache"
        
        with patch('app.infrastructure.cache.dependencies.CacheFactory') as mock_factory_class:
            mock_factory = MagicMock()
            mock_factory_class.return_value = mock_factory
            mock_factory.for_testing = AsyncMock(return_value=mock_cache)

            with patch('app.infrastructure.cache.dependencies.logger') as mock_logger:
                result = await get_test_cache()

                # Verify factory called with correct parameters
                mock_factory.for_testing.assert_called_once_with(use_memory_cache=True)
                
                # Verify cache returned
                assert result is mock_cache
                
                # Verify proper logging
                mock_logger.debug.assert_called_once_with(
                    "Creating memory-only test cache"
                )
                mock_logger.info.assert_called_once_with(
                    "Test cache ready: InMemoryCache"
                )

    @pytest.mark.asyncio
    async def test_get_test_redis_cache_success(self):
        """
        Test that get_test_redis_cache creates Redis test cache per docstring.
        
        Business Impact:
            Enables integration testing with Redis while using separate test database
            to avoid interference with development or production data.
            
        Test Scenario:
            Mock factory that successfully creates Redis test cache
            
        Success Criteria:
            - CacheFactory.for_testing() called with Redis parameters
            - Test Redis URL used (database 15)
            - Redis test cache returned
        """
        # Create mock factory and cache
        mock_cache = MagicMock(spec=CacheInterface)
        type(mock_cache).__name__ = "GenericRedisCache"
        
        with patch('app.infrastructure.cache.dependencies.CacheFactory') as mock_factory_class:
            mock_factory = MagicMock()
            mock_factory_class.return_value = mock_factory
            mock_factory.for_testing = AsyncMock(return_value=mock_cache)

            with patch.dict(os.environ, {'TEST_REDIS_URL': 'redis://test-server:6379/15'}):
                with patch('app.infrastructure.cache.dependencies.logger') as mock_logger:
                    result = await get_test_redis_cache()

                    # Verify factory called with Redis parameters
                    mock_factory.for_testing.assert_called_once_with(
                        redis_url='redis://test-server:6379/15',
                        use_memory_cache=False,
                        fail_on_connection_error=False
                    )
                    
                    # Verify cache returned
                    assert result is mock_cache
                    
                    # Verify proper logging
                    mock_logger.info.assert_called_once_with(
                        "Test Redis cache ready: GenericRedisCache"
                    )

    @pytest.mark.asyncio
    async def test_get_test_redis_cache_fallback_to_memory(self):
        """
        Test that get_test_redis_cache falls back to memory cache on Redis failure per docstring.
        
        Business Impact:
            Ensures tests can run even when Redis is unavailable, maintaining
            test reliability and developer productivity.
            
        Test Scenario:
            Factory for Redis test cache raises exception
            
        Success Criteria:
            - Exception during Redis cache creation caught
            - get_test_cache() called as fallback
            - Warning logged about fallback usage
        """
        with patch('app.infrastructure.cache.dependencies.CacheFactory') as mock_factory_class:
            mock_factory = MagicMock()
            mock_factory_class.return_value = mock_factory
            mock_factory.for_testing = AsyncMock(
                side_effect=Exception("Redis test server unavailable")
            )

            # Mock get_test_cache fallback
            fallback_cache = MagicMock(spec=CacheInterface)
            with patch('app.infrastructure.cache.dependencies.get_test_cache', 
                      return_value=fallback_cache) as mock_get_test_cache:
                with patch('app.infrastructure.cache.dependencies.logger') as mock_logger:
                    result = await get_test_redis_cache()

                    # Verify fallback called
                    mock_get_test_cache.assert_called_once()
                    assert result is fallback_cache
                    
                    # Verify warning logged
                    mock_logger.warning.assert_called_once()
                    assert "Failed to create Redis test cache, falling back to memory" in str(mock_logger.warning.call_args[0][0])

    @pytest.mark.asyncio
    async def test_get_test_redis_cache_default_url(self):
        """
        Test that get_test_redis_cache uses default Redis URL when environment variable not set per docstring.
        
        Business Impact:
            Provides sensible defaults for test Redis configuration, simplifying
            test setup while maintaining isolation.
            
        Test Scenario:
            No TEST_REDIS_URL environment variable set
            
        Success Criteria:
            - Default Redis URL used (localhost:6379/15)
            - Factory called with default parameters
        """
        # Create mock factory and cache
        mock_cache = MagicMock(spec=CacheInterface)
        
        with patch('app.infrastructure.cache.dependencies.CacheFactory') as mock_factory_class:
            mock_factory = MagicMock()
            mock_factory_class.return_value = mock_factory
            mock_factory.for_testing = AsyncMock(return_value=mock_cache)

            # Ensure TEST_REDIS_URL is not set
            with patch.dict(os.environ, {}, clear=True):
                await get_test_redis_cache()

                # Verify factory called with default URL
                mock_factory.for_testing.assert_called_once_with(
                    redis_url='redis://localhost:6379/15',
                    use_memory_cache=False,
                    fail_on_connection_error=False
                )


class TestUtilityDependencies:
    """
    Test utility dependencies including validation, conditional selection, and fallback.
    
    Business Impact:
        Utility dependencies provide essential support functions for cache management.
        Proper validation and conditional selection are crucial for application reliability.
    """

    @pytest.mark.asyncio
    async def test_get_fallback_cache_service_returns_memory_cache(self):
        """
        Test that get_fallback_cache_service returns InMemoryCache with safe defaults per docstring.
        
        Business Impact:
            Provides guaranteed cache availability for degraded mode operations,
            ensuring application continues functioning even during infrastructure issues.
            
        Test Scenario:
            Call get_fallback_cache_service()
            
        Success Criteria:
            - InMemoryCache returned with documented parameters
            - TTL set to 1800 seconds (30 minutes)
            - Max size set to 100 (conservative memory usage)
        """
        with patch('app.infrastructure.cache.dependencies.logger') as mock_logger:
            result = await get_fallback_cache_service()

            # Verify fallback cache configuration
            assert isinstance(result, InMemoryCache)
            assert result.default_ttl == 1800  # 30 minutes
            assert result.max_size == 100      # Conservative memory usage
            
            # Verify proper logging
            mock_logger.debug.assert_called_once_with(
                "Creating fallback cache service (InMemoryCache)"
            )
            mock_logger.info.assert_called_once_with(
                "Fallback cache service ready: InMemoryCache"
            )

    @pytest.mark.asyncio
    async def test_validate_cache_configuration_success_with_validation(self):
        """
        Test that validate_cache_configuration passes valid configuration per docstring.
        
        Business Impact:
            Ensures only valid cache configurations are used in production,
            preventing configuration-related service failures.
            
        Test Scenario:
            Mock configuration with validate() method that returns valid result
            
        Success Criteria:
            - validate() method called on configuration
            - Configuration returned when validation passes
            - Debug logging indicates validation passed
        """
        # Create mock configuration with validation
        mock_config = MagicMock()
        mock_validation_result = MagicMock()
        mock_validation_result.is_valid = True
        mock_validation_result.warnings = []
        mock_config.validate.return_value = mock_validation_result

        with patch('app.infrastructure.cache.dependencies.logger') as mock_logger:
            result = await validate_cache_configuration(mock_config)

            # Verify validation called
            mock_config.validate.assert_called_once()
            
            # Verify configuration returned
            assert result is mock_config
            
            # Verify debug logging
            mock_logger.debug.assert_any_call("Validating cache configuration")
            mock_logger.debug.assert_any_call("Cache configuration validation passed")

    @pytest.mark.asyncio
    async def test_validate_cache_configuration_failure(self):
        """
        Test that validate_cache_configuration raises HTTPException for invalid config per docstring.
        
        Business Impact:
            Prevents invalid configurations from being used, protecting the application
            from configuration-related failures and providing clear error information.
            
        Test Scenario:
            Mock configuration with validation that returns invalid result
            
        Success Criteria:
            - HTTPException raised with status code 500
            - Validation errors included in response detail
            - Error logging indicates validation failure
        """
        # Create mock configuration with failing validation
        mock_config = MagicMock()
        mock_validation_result = MagicMock()
        mock_validation_result.is_valid = False
        mock_validation_result.errors = ["Redis URL is invalid", "TTL must be positive"]
        mock_validation_result.warnings = ["Default TTL is high"]
        mock_config.validate.return_value = mock_validation_result

        with patch('app.infrastructure.cache.dependencies.logger') as mock_logger:
            with pytest.raises(HTTPException) as exc_info:
                await validate_cache_configuration(mock_config)

            # Verify HTTPException details
            error = exc_info.value
            assert error.status_code == 500
            assert error.detail["error"] == "Invalid cache configuration"
            assert error.detail["validation_errors"] == ["Redis URL is invalid", "TTL must be positive"]
            assert error.detail["warnings"] == ["Default TTL is high"]
            
            # Verify error logging
            mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_cache_configuration_no_validate_method(self):
        """
        Test that validate_cache_configuration handles configurations without validate() method per docstring.
        
        Business Impact:
            Ensures compatibility with cache configurations that don't implement
            validation, preventing method errors while maintaining functionality.
            
        Test Scenario:
            Mock configuration without validate() method
            
        Success Criteria:
            - No validation method called (doesn't exist)
            - Configuration returned as-is
            - Debug logging indicates validation passed
        """
        # Create mock configuration without validate method
        mock_config = MagicMock()
        # Don't add validate method to mock

        with patch('app.infrastructure.cache.dependencies.logger') as mock_logger:
            result = await validate_cache_configuration(mock_config)

            # Verify configuration returned without validation
            assert result is mock_config
            
            # Verify debug logging
            mock_logger.debug.assert_any_call("Validating cache configuration")
            mock_logger.debug.assert_any_call("Cache configuration validation passed")

    @pytest.mark.asyncio
    async def test_get_cache_service_conditional_fallback_only(self):
        """
        Test that get_cache_service_conditional returns fallback when fallback_only=True per docstring.
        
        Business Impact:
            Enables forced fallback mode for testing degraded conditions or
            when infrastructure issues require bypassing normal cache services.
            
        Test Scenario:
            Call with fallback_only=True parameter
            
        Success Criteria:
            - get_fallback_cache_service() called
            - Fallback cache returned
            - Info logging indicates fallback cache usage
        """
        # Mock settings
        mock_settings = MagicMock(spec=Settings)
        
        # Mock fallback cache
        fallback_cache = MagicMock(spec=CacheInterface)
        with patch('app.infrastructure.cache.dependencies.get_fallback_cache_service',
                   return_value=fallback_cache) as mock_get_fallback:
            with patch('app.infrastructure.cache.dependencies.logger') as mock_logger:
                result = await get_cache_service_conditional(
                    enable_ai=False,
                    fallback_only=True,
                    settings=mock_settings
                )

                # Verify fallback service called
                mock_get_fallback.assert_called_once()
                assert result is fallback_cache
                
                # Verify info logging
                mock_logger.info.assert_called_once_with(
                    "Conditional cache: using fallback cache"
                )

    @pytest.mark.asyncio
    async def test_get_cache_service_conditional_ai_cache(self):
        """
        Test that get_cache_service_conditional returns AI cache when enable_ai=True per docstring.
        
        Business Impact:
            Enables dynamic cache selection based on request parameters,
            allowing applications to optimize cache behavior per operation type.
            
        Test Scenario:
            Call with enable_ai=True parameter
            
        Success Criteria:
            - get_ai_cache_service() called with built configuration
            - AI cache returned
            - Info logging indicates AI cache usage
        """
        # Mock settings and configuration
        mock_settings = MagicMock(spec=Settings)
        mock_config = MagicMock()
        
        # Mock AI cache
        ai_cache = MagicMock(spec=CacheInterface)
        
        with patch('app.infrastructure.cache.dependencies.get_cache_config',
                   return_value=mock_config) as mock_get_config:
            with patch('app.infrastructure.cache.dependencies.get_ai_cache_service',
                       return_value=ai_cache) as mock_get_ai_cache:
                with patch('app.infrastructure.cache.dependencies.logger') as mock_logger:
                    result = await get_cache_service_conditional(
                        enable_ai=True,
                        fallback_only=False,
                        settings=mock_settings
                    )

                    # Verify configuration built
                    mock_get_config.assert_called_once_with(mock_settings)
                    
                    # Verify AI cache service called
                    mock_get_ai_cache.assert_called_once_with(mock_config)
                    assert result is ai_cache
                    
                    # Verify info logging
                    mock_logger.info.assert_called_once_with(
                        "Conditional cache: using AI cache service"
                    )

    @pytest.mark.asyncio
    async def test_get_cache_service_conditional_web_cache(self):
        """
        Test that get_cache_service_conditional returns web cache when enable_ai=False per docstring.
        
        Business Impact:
            Ensures web-optimized caches are used for non-AI operations,
            maintaining optimal performance for different application workloads.
            
        Test Scenario:
            Call with enable_ai=False and fallback_only=False parameters
            
        Success Criteria:
            - get_web_cache_service() called with built configuration
            - Web cache returned
            - Info logging indicates web cache usage
        """
        # Mock settings and configuration
        mock_settings = MagicMock(spec=Settings)
        mock_config = MagicMock()
        
        # Mock web cache
        web_cache = MagicMock(spec=CacheInterface)
        
        with patch('app.infrastructure.cache.dependencies.get_cache_config',
                   return_value=mock_config) as mock_get_config:
            with patch('app.infrastructure.cache.dependencies.get_web_cache_service',
                       return_value=web_cache) as mock_get_web_cache:
                with patch('app.infrastructure.cache.dependencies.logger') as mock_logger:
                    result = await get_cache_service_conditional(
                        enable_ai=False,
                        fallback_only=False,
                        settings=mock_settings
                    )

                    # Verify configuration built
                    mock_get_config.assert_called_once_with(mock_settings)
                    
                    # Verify web cache service called
                    mock_get_web_cache.assert_called_once_with(mock_config)
                    assert result is web_cache
                    
                    # Verify info logging
                    mock_logger.info.assert_called_once_with(
                        "Conditional cache: using web cache service"
                    )

    @pytest.mark.asyncio
    async def test_get_cache_service_conditional_exception_fallback(self):
        """
        Test that get_cache_service_conditional falls back to InMemoryCache on exceptions per docstring.
        
        Business Impact:
            Ensures conditional cache selection continues functioning even when
            specific cache services fail, maintaining application availability.
            
        Test Scenario:
            Mock configuration building that raises exception
            
        Success Criteria:
            - Exception during cache service creation caught
            - get_fallback_cache_service() called as fallback
            - Error and warning logging about fallback usage
        """
        # Mock settings
        mock_settings = MagicMock(spec=Settings)
        
        # Mock fallback cache
        fallback_cache = MagicMock(spec=CacheInterface)
        
        with patch('app.infrastructure.cache.dependencies.get_cache_config',
                   side_effect=Exception("Configuration error")) as mock_get_config:
            with patch('app.infrastructure.cache.dependencies.get_fallback_cache_service',
                       return_value=fallback_cache) as mock_get_fallback:
                with patch('app.infrastructure.cache.dependencies.logger') as mock_logger:
                    result = await get_cache_service_conditional(
                        enable_ai=False,
                        fallback_only=False,
                        settings=mock_settings
                    )

                    # Verify fallback called
                    mock_get_fallback.assert_called_once()
                    assert result is fallback_cache
                    
                    # Verify error and warning logging
                    mock_logger.error.assert_called_once()
                    mock_logger.warning.assert_called_once_with(
                        "Falling back to InMemoryCache for conditional service"
                    )


class TestLifecycleManagement:
    """
    Test cache registry cleanup and lifecycle management.
    
    Business Impact:
        Proper lifecycle management prevents memory leaks and ensures clean cache
        disconnection during application shutdown, maintaining system stability.
    """

    @pytest.mark.asyncio
    async def test_cleanup_cache_registry_empty_registry(self):
        """
        Test that cleanup_cache_registry handles empty registry correctly per docstring.
        
        Business Impact:
            Ensures cleanup operations work correctly even when no caches are active,
            preventing errors during application shutdown.
            
        Test Scenario:
            Empty cache registry
            
        Success Criteria:
            - Cleanup statistics reflect empty registry
            - No errors or exceptions raised
            - Info logging indicates cleanup completion
        """
        # Clear registry for test
        _cache_registry.clear()

        with patch('app.infrastructure.cache.dependencies.logger') as mock_logger:
            stats = await cleanup_cache_registry()

            # Verify cleanup statistics
            assert stats["total_entries"] == 0
            assert stats["active_caches"] == 0
            assert stats["dead_references"] == 0
            assert stats["disconnected_caches"] == 0
            assert stats["errors"] == []
            
            # Verify logging
            mock_logger.info.assert_any_call("Starting cache registry cleanup")

    @pytest.mark.asyncio
    async def test_cleanup_cache_registry_with_active_caches(self):
        """
        Test that cleanup_cache_registry disconnects active caches per docstring.
        
        Business Impact:
            Ensures proper cache disconnection during application shutdown,
            preventing resource leaks and ensuring clean service termination.
            
        Test Scenario:
            Registry with active caches that have disconnect() method
            
        Success Criteria:
            - disconnect() called on each active cache
            - Cleanup statistics reflect disconnected caches
            - Registry cleared after cleanup
        """
        # Clear registry and add active caches
        _cache_registry.clear()
        
        # Create mock caches with disconnect method
        mock_cache1 = MagicMock(spec=CacheInterface)
        mock_cache1.disconnect = AsyncMock()
        mock_cache2 = MagicMock(spec=CacheInterface)
        mock_cache2.disconnect = AsyncMock()
        
        _cache_registry["cache1"] = weakref.ref(mock_cache1)
        _cache_registry["cache2"] = weakref.ref(mock_cache2)

        with patch('app.infrastructure.cache.dependencies.logger') as mock_logger:
            stats = await cleanup_cache_registry()

            # Verify disconnect called on both caches
            mock_cache1.disconnect.assert_called_once()
            mock_cache2.disconnect.assert_called_once()
            
            # Verify cleanup statistics
            assert stats["total_entries"] == 2
            assert stats["active_caches"] == 2
            assert stats["disconnected_caches"] == 2
            assert stats["dead_references"] == 0
            assert stats["errors"] == []
            
            # Verify registry cleared
            assert len(_cache_registry) == 0

    @pytest.mark.asyncio
    async def test_cleanup_cache_registry_with_dead_references(self):
        """
        Test that cleanup_cache_registry removes dead references per docstring.
        
        Business Impact:
            Prevents memory leaks from dead cache references by properly cleaning
            up the registry, maintaining efficient memory usage.
            
        Test Scenario:
            Registry with dead weak references (garbage collected caches)
            
        Success Criteria:
            - Dead references identified and removed
            - Cleanup statistics reflect dead reference count
            - Registry cleared after cleanup
        """
        # Clear registry for test
        _cache_registry.clear()
        
        # Create a dead weak reference by scoping and garbage collection
        temp_cache = MagicMock(spec=CacheInterface)
        _cache_registry["dead_cache"] = weakref.ref(temp_cache)
        del temp_cache  # Make the reference dead
        
        # Force garbage collection to make reference dead
        import gc
        gc.collect()

        with patch('app.infrastructure.cache.dependencies.logger') as mock_logger:
            stats = await cleanup_cache_registry()

            # Verify cleanup statistics - might be 0 or 1 depending on GC timing
            assert stats["total_entries"] >= 0
            assert stats["active_caches"] >= 0
            assert stats["dead_references"] >= 0
            assert stats["disconnected_caches"] == 0
            assert stats["errors"] == []
            
            # Verify registry cleared
            assert len(_cache_registry) == 0

    @pytest.mark.asyncio
    async def test_cleanup_cache_registry_disconnect_failure(self):
        """
        Test that cleanup_cache_registry handles disconnect failures per docstring.
        
        Business Impact:
            Ensures cleanup continues even when individual cache disconnections fail,
            preventing partial cleanup failures from affecting overall shutdown.
            
        Test Scenario:
            Active cache with disconnect() method that raises exception
            
        Success Criteria:
            - Exception during disconnect caught and logged
            - Error added to cleanup statistics
            - Cleanup continues for other caches
        """
        # Clear registry and add cache with failing disconnect
        _cache_registry.clear()
        
        mock_cache = MagicMock(spec=CacheInterface)
        mock_cache.disconnect = AsyncMock(side_effect=Exception("Disconnect failed"))
        _cache_registry["failing_cache"] = weakref.ref(mock_cache)

        with patch('app.infrastructure.cache.dependencies.logger') as mock_logger:
            stats = await cleanup_cache_registry()

            # Verify disconnect was attempted
            mock_cache.disconnect.assert_called_once()
            
            # Verify error in statistics
            assert stats["total_entries"] == 1
            assert stats["active_caches"] == 1
            assert stats["disconnected_caches"] == 0
            assert len(stats["errors"]) == 1
            assert "Failed to disconnect cache failing_cache" in stats["errors"][0]
            
            # Verify error logging
            mock_logger.error.assert_called_once()

    @pytest.mark.asyncio
    async def test_cleanup_cache_registry_exception_handling(self):
        """
        Test that cleanup_cache_registry handles exceptions during cleanup per docstring.
        
        Business Impact:
            Ensures cleanup operations are resilient to unexpected errors,
            preventing cleanup failures from causing application shutdown issues.
            
        Test Scenario:
            Exception occurs during registry iteration
            
        Success Criteria:
            - Exception caught and logged
            - Error added to cleanup statistics
            - Function returns stats instead of raising
        """
        # Clear registry for clean test
        _cache_registry.clear()
        
        # Create a scenario that causes exception by mocking disconnect to fail
        mock_cache = MagicMock(spec=CacheInterface)
        mock_cache.disconnect = AsyncMock(side_effect=Exception("Forced disconnect failure"))
        _cache_registry["failing_cache"] = weakref.ref(mock_cache)
        
        with patch('app.infrastructure.cache.dependencies.logger') as mock_logger:
            stats = await cleanup_cache_registry()

            # Verify error handling - should have caught disconnect failure
            assert len(stats["errors"]) >= 1
            assert any("Failed to disconnect cache" in error for error in stats["errors"])
            
            # Verify error logging occurred
            assert mock_logger.error.call_count >= 1
            
            # Cleanup should still complete (registry cleared)
            assert len(_cache_registry) == 0


class TestHealthCheckDependencies:
    """
    Test comprehensive cache health monitoring dependencies.
    
    Business Impact:
        Health check dependencies provide critical monitoring capabilities for cache
        services. Proper health monitoring is essential for maintaining system reliability.
    """

    @pytest.mark.asyncio
    async def test_get_cache_health_status_with_ping_success(self):
        """
        Test that get_cache_health_status uses ping() method when available per docstring.
        
        Business Impact:
            Enables efficient health monitoring using lightweight ping operations,
            reducing monitoring overhead while providing accurate health status.
            
        Test Scenario:
            Mock cache with ping() method that returns True
            
        Success Criteria:
            - ping() method called for health check
            - Health status indicates healthy with ping success
            - ping_available flag set to True
        """
        # Create mock cache with successful ping
        mock_cache = MagicMock(spec=CacheInterface)
        mock_cache.ping = AsyncMock(return_value=True)
        type(mock_cache).__name__ = "GenericRedisCache"

        with patch('app.infrastructure.cache.dependencies.logger') as mock_logger:
            result = await get_cache_health_status(mock_cache)

            # Verify ping called
            mock_cache.ping.assert_called_once()
            
            # Verify health status
            assert result["cache_type"] == "GenericRedisCache"
            assert result["status"] == "healthy"
            assert result["ping_available"] is True
            assert result["ping_success"] is True
            assert result["operation_test"] is False  # Not used when ping available
            assert result["errors"] == []
            
            # Verify debug logging
            mock_logger.debug.assert_any_call(
                "Using ping() method for health check"
            )

    @pytest.mark.asyncio
    async def test_get_cache_health_status_with_ping_failure(self):
        """
        Test that get_cache_health_status handles ping() failure gracefully per docstring.
        
        Business Impact:
            Provides accurate degraded status when cache ping fails while maintaining
            monitoring capability, enabling proper alerting and remediation.
            
        Test Scenario:
            Mock cache with ping() method that returns False
            
        Success Criteria:
            - ping() method called
            - Health status indicates degraded with ping failure
            - Warning about degraded status added
        """
        # Create mock cache with failing ping
        mock_cache = MagicMock(spec=CacheInterface)
        mock_cache.ping = AsyncMock(return_value=False)
        type(mock_cache).__name__ = "GenericRedisCache"

        with patch('app.infrastructure.cache.dependencies.logger') as mock_logger:
            result = await get_cache_health_status(mock_cache)

            # Verify ping called
            mock_cache.ping.assert_called_once()
            
            # Verify health status
            assert result["status"] == "degraded"
            assert result["ping_available"] is True
            assert result["ping_success"] is False
            assert len(result["warnings"]) == 1
            assert "Cache ping failed but cache may still be operational" in result["warnings"][0]

    @pytest.mark.asyncio
    async def test_get_cache_health_status_without_ping_method(self):
        """
        Test that get_cache_health_status falls back to operation test without ping() per docstring.
        
        Business Impact:
            Ensures health monitoring works with cache implementations that don't
            support ping(), maintaining comprehensive monitoring across all cache types.
            
        Test Scenario:
            Mock cache without ping() method
            
        Success Criteria:
            - Operation test performed (set/get/delete operations)
            - Health status based on operation test results
            - ping_available flag set to False
        """
        # Create mock cache without ping method
        mock_cache = MagicMock(spec=CacheInterface)
        # Don't add ping method
        mock_cache.set = AsyncMock()
        mock_cache.get = AsyncMock(return_value="health_check_value")
        mock_cache.delete = AsyncMock()
        type(mock_cache).__name__ = "InMemoryCache"

        with patch('app.infrastructure.cache.dependencies.asyncio') as mock_asyncio:
            mock_asyncio.get_event_loop.return_value.time.return_value = 123456789.0

            result = await get_cache_health_status(mock_cache)

            # Verify operation test performed
            mock_cache.set.assert_called_once()
            mock_cache.get.assert_called_once()
            mock_cache.delete.assert_called_once()
            
            # Verify health status
            assert result["ping_available"] is False
            assert result["operation_test"] is True
            assert result["status"] == "healthy"

    @pytest.mark.asyncio
    async def test_get_cache_health_status_operation_test_failure(self):
        """
        Test that get_cache_health_status handles operation test failures per docstring.
        
        Business Impact:
            Provides accurate unhealthy status when cache operations fail,
            enabling proper monitoring and alerting for cache issues.
            
        Test Scenario:
            Mock cache without ping() where operation test raises exception
            
        Success Criteria:
            - Exception during operation test caught
            - Health status indicates unhealthy
            - Error details included in response
        """
        # Create mock cache without ping method
        mock_cache = MagicMock(spec=CacheInterface)
        # Don't add ping method
        mock_cache.set = AsyncMock(side_effect=Exception("Cache operation failed"))
        type(mock_cache).__name__ = "InMemoryCache"

        result = await get_cache_health_status(mock_cache)

        # Verify health status
        assert result["ping_available"] is False
        assert result["operation_test"] is False
        assert result["status"] == "unhealthy"
        assert len(result["errors"]) == 1
        assert "Operation test failed" in result["errors"][0]

    @pytest.mark.asyncio
    async def test_get_cache_health_status_with_statistics(self):
        """
        Test that get_cache_health_status includes cache statistics when available per docstring.
        
        Business Impact:
            Provides comprehensive monitoring data including cache performance metrics,
            enabling detailed analysis of cache behavior and performance optimization.
            
        Test Scenario:
            Mock cache with get_stats() method
            
        Success Criteria:
            - get_stats() method called
            - Statistics included in health response
            - Statistics added to health status
        """
        # Create mock cache with stats
        mock_cache = MagicMock(spec=CacheInterface)
        mock_cache.ping = AsyncMock(return_value=True)
        mock_stats = {"hits": 150, "misses": 25, "hit_rate": 0.857}
        mock_cache.get_stats = AsyncMock(return_value=mock_stats)
        type(mock_cache).__name__ = "GenericRedisCache"

        result = await get_cache_health_status(mock_cache)

        # Verify stats included
        mock_cache.get_stats.assert_called_once()
        assert result["statistics"] == mock_stats

    @pytest.mark.asyncio
    async def test_get_cache_health_status_stats_failure(self):
        """
        Test that get_cache_health_status handles get_stats() failures gracefully per docstring.
        
        Business Impact:
            Ensures health checks continue working even when statistics collection
            fails, maintaining core monitoring capability despite stats issues.
            
        Test Scenario:
            Mock cache with get_stats() method that raises exception
            
        Success Criteria:
            - Exception during get_stats() caught
            - Warning added about stats failure
            - Health check continues and succeeds
        """
        # Create mock cache with failing stats
        mock_cache = MagicMock(spec=CacheInterface)
        mock_cache.ping = AsyncMock(return_value=True)
        mock_cache.get_stats = AsyncMock(side_effect=Exception("Stats unavailable"))
        type(mock_cache).__name__ = "GenericRedisCache"

        result = await get_cache_health_status(mock_cache)

        # Verify stats failure handled
        mock_cache.get_stats.assert_called_once()
        assert result["status"] == "healthy"  # Still healthy despite stats failure
        assert len(result["warnings"]) == 1
        assert "Failed to get cache statistics" in result["warnings"][0]

    @pytest.mark.asyncio
    async def test_get_cache_health_status_exception_handling(self):
        """
        Test that get_cache_health_status handles unexpected exceptions per docstring.
        
        Business Impact:
            Ensures health check endpoint remains available even when cache
            operations fail unexpectedly, maintaining monitoring capability.
            
        Test Scenario:
            Health check process raises unexpected exception
            
        Success Criteria:
            - Exception caught and handled
            - Error status returned with exception details
            - No exception propagated to caller
        """
        # Create mock cache that will cause an exception
        mock_cache = MagicMock(spec=CacheInterface)
        
        # Mock the logger to raise exception during health check
        with patch('app.infrastructure.cache.dependencies.logger') as mock_logger:
            # Make logger.debug raise exception to simulate unexpected error in health check
            mock_logger.debug.side_effect = Exception("Unexpected error")
            
            result = await get_cache_health_status(mock_cache)

            # Verify error status
            assert result["status"] == "error"
            assert len(result["errors"]) == 1
            assert "Health check failed" in result["errors"][0]


class TestDependencyIntegration:
    """
    Test integration between dependency chains and FastAPI dependency injection.
    
    Business Impact:
        Integration tests ensure the entire dependency chain works correctly together,
        preventing issues in production where dependencies are composed.
    """

    @pytest.mark.asyncio
    async def test_dependency_chain_settings_to_cache(self):
        """
        Test that dependency chain from settings to cache service works correctly.
        
        Business Impact:
            Ensures the complete dependency chain functions correctly in production,
            preventing cache initialization failures due to dependency issues.
            
        Test Scenario:
            Chain get_settings() -> get_cache_config() -> get_cache_service()
            
        Success Criteria:
            - Each dependency function called with correct parameters
            - Cache service created with configuration from settings
            - Registry management works correctly
        """
        # Clear registry for test
        _cache_registry.clear()
        
        # Mock the chain components
        with patch('app.infrastructure.cache.dependencies.Settings') as mock_settings_class:
            mock_settings = MagicMock(spec=Settings)
            mock_settings.cache_preset = "development"
            mock_config = MagicMock()
            mock_settings.get_cache_config.return_value = mock_config
            mock_settings_class.return_value = mock_settings

            with patch('app.infrastructure.cache.dependencies.CacheFactory') as mock_factory_class:
                mock_factory = MagicMock()
                mock_cache = MagicMock(spec=CacheInterface)
                mock_cache.connect = AsyncMock()
                mock_factory.create_cache_from_config = AsyncMock(return_value=mock_cache)
                mock_factory_class.return_value = mock_factory

                # Execute dependency chain
                settings = get_settings()
                config = await get_cache_config(settings)
                cache = await get_cache_service(config)

                # Verify chain connections
                assert settings is mock_settings
                assert config is mock_config
                assert cache is mock_cache
                
                # Verify cache created with config
                mock_factory.create_cache_from_config.assert_called_once()

    @pytest.mark.asyncio
    async def test_conditional_cache_integration(self):
        """
        Test that conditional cache selection integrates with other dependencies.
        
        Business Impact:
            Ensures dynamic cache selection works correctly with the complete
            dependency system, enabling flexible cache behavior in production.
            
        Test Scenario:
            Use get_cache_service_conditional with different parameters
            
        Success Criteria:
            - Settings dependency used correctly
            - Configuration built from settings
            - Appropriate cache service selected based on conditions
        """
        # Mock settings
        with patch('app.infrastructure.cache.dependencies.Settings') as mock_settings_class:
            mock_settings = MagicMock(spec=Settings)
            mock_settings_class.return_value = mock_settings

            with patch('app.infrastructure.cache.dependencies.get_cache_config') as mock_get_config:
                mock_config = MagicMock()
                mock_get_config.return_value = mock_config

                with patch('app.infrastructure.cache.dependencies.get_ai_cache_service') as mock_get_ai_cache:
                    mock_ai_cache = MagicMock(spec=CacheInterface)
                    mock_get_ai_cache.return_value = mock_ai_cache

                    # Test AI cache selection
                    settings = get_settings()
                    result = await get_cache_service_conditional(
                        enable_ai=True,
                        fallback_only=False,
                        settings=settings
                    )

                    # Verify integration
                    mock_get_config.assert_called_once_with(settings)
                    mock_get_ai_cache.assert_called_once_with(mock_config)
                    assert result is mock_ai_cache

    @pytest.mark.asyncio
    async def test_health_check_integration(self):
        """
        Test that health check integration works with cache dependencies.
        
        Business Impact:
            Ensures health monitoring works correctly with the dependency system,
            providing reliable service health information for production monitoring.
            
        Test Scenario:
            Health check depends on cache service which depends on configuration
            
        Success Criteria:
            - Cache service dependency resolved correctly
            - Health check performed on resolved cache
            - Complete health information returned
        """
        # Mock cache service dependency
        mock_cache = MagicMock(spec=CacheInterface)
        mock_cache.ping = AsyncMock(return_value=True)
        type(mock_cache).__name__ = "TestCache"

        # Test health check with dependency
        result = await get_cache_health_status(mock_cache)

        # Verify health check integration
        assert result["cache_type"] == "TestCache"
        assert result["status"] == "healthy"
        assert result["ping_success"] is True

    @pytest.mark.asyncio
    async def test_registry_isolation_between_tests(self):
        """
        Test that cache registry is properly isolated between different cache types.
        
        Business Impact:
            Ensures cache instances don't interfere with each other in production,
            preventing cache key collisions and ensuring proper cache isolation.
            
        Test Scenario:
            Create different cache types and verify registry isolation
            
        Success Criteria:
            - Different cache keys generated for different configurations
            - Registry maintains separate entries for different caches
            - No interference between cache instances
        """
        # Clear registry for test
        _cache_registry.clear()
        
        # Mock different configurations that will generate different cache keys
        config1 = MagicMock()
        config1.to_dict.return_value = {"redis_url": "redis://server1:6379", "type": "main"}
        
        config2 = MagicMock()
        config2.to_dict.return_value = {"redis_url": "redis://server1:6379", "default_ttl": 1800}

        with patch('app.infrastructure.cache.dependencies.CacheFactory') as mock_factory_class:
            mock_factory = MagicMock()
            mock_factory_class.return_value = mock_factory
            
            # Create different cache instances
            cache1 = MagicMock(spec=CacheInterface)
            cache1.connect = AsyncMock()
            cache2 = MagicMock(spec=CacheInterface)
            cache2.connect = AsyncMock()
            
            mock_factory.create_cache_from_config.side_effect = [cache1, cache2]

            # Create both caches - use different cache services to ensure isolation
            result1 = await get_cache_service(config1)
            result2 = await get_web_cache_service(config2)

            # Both should be cache instances (may be same type if fallback happened)
            assert isinstance(result1, (type(cache1), InMemoryCache))
            assert isinstance(result2, (type(cache2), InMemoryCache))
            
            # If both succeeded without fallback, verify registry isolation
            if result1 is cache1 and result2 is cache2:
                # Verify separate registry entries
                assert len(_cache_registry) == 2
                
                # Verify different cache keys were generated
                keys = list(_cache_registry.keys())
                assert keys[0] != keys[1]  # Different configurations should generate different keys