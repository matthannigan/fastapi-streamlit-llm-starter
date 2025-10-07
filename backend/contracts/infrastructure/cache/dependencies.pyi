"""
FastAPI dependencies for cache infrastructure with lifecycle management.

This module provides comprehensive FastAPI dependency injection for cache services
with lifecycle management, thread-safe registry, and health monitoring. It implements
explicit cache creation patterns and supports graceful degradation with fallback.

## Classes

**CacheDependencyManager**: Core dependency manager handling cache lifecycle and registry

## Functions

- **get_settings**: Cached settings dependency for configuration access
- **get_cache_config**: Configuration builder with environment detection
- **get_cache_service**: Main cache service dependency with registry management
- **get_web_cache_service**: Web-optimized cache service dependency
- **get_ai_cache_service**: AI-optimized cache service dependency
- **get_test_cache**: Testing cache dependency with memory fallback
- **get_cache_health_status**: Comprehensive health check dependency
- **validate_cache_configuration**: Configuration validation dependency
- **cleanup_cache_registry**: Lifecycle cleanup for cache registry

## Key Features

- **Thread-Safe Registry**: Weak reference cache registry with asyncio locks
- **Explicit Factory Usage**: Uses CacheFactory for deterministic creation
- **Graceful Degradation**: Automatic fallback to InMemoryCache on Redis failures
- **Lifecycle Management**: Proper cache connection and cleanup handling
    - **Health Monitoring**: Comprehensive health checks with ping() method support
    - **Configuration Building**: Environment-aware configuration from settings
    - **Test Integration**: Specialized dependencies for testing scenarios
    - **Async Safety**: Full async/await patterns with proper error handling

Architecture:
    This module integrates with:
    - CacheFactory for explicit cache creation
    - CacheConfig and CacheConfigBuilder for configuration management
    - FastAPI dependency injection system for request-scoped cache access
    - Application settings for environment-specific configuration
    - Custom exception hierarchy for structured error handling

Examples:
    Basic cache dependency usage:
        @app.get("/api/data")
        async def get_data(cache: CacheInterface = Depends(get_cache_service)):
            cached_data  =  await cache.get("api_data")
            if cached_data:
                return cached_data

            # Fetch fresh data
            fresh_data  =  fetch_api_data()
            await cache.set("api_data", fresh_data, ttl = 300)
            return fresh_data

    AI cache dependency usage:
        @app.post("/api/ai/summarize")
        async def summarize_text(
            request: SummarizeRequest,
            ai_cache: CacheInterface = Depends(get_ai_cache_service)
        ):
            # Domain service handles caching logic (recommended pattern)
            # Use TextProcessorService for business logic, not direct cache operations
            # Direct usage shown for illustration only:
            cache_key  =  ai_cache.build_key(request.text, "summarize", request.options)
            cached_result  =  await ai_cache.get(cache_key)
            return cached_result

    Health check integration:
        @app.get("/health/cache")
        async def cache_health(
            health_status: dict = Depends(get_cache_health_status)
        ):
            return health_status

Performance Considerations:
    - Cache registry uses weak references to prevent memory leaks
    - Connection establishment is async and non-blocking
    - Fallback operations are near-instantaneous (<1ms)
    - Health checks prefer lightweight ping() over full operations
    - Registry cleanup removes dead references efficiently

Error Handling:
    - ConfigurationError: Configuration building or validation failures
    - InfrastructureError: Cache connection or infrastructure issues
    - ValidationError: Invalid configuration parameters
    - All errors include context data for debugging and monitoring

Dependencies:
    Required:
        - app.infrastructure.cache.factory.CacheFactory: Explicit cache creation
        - app.infrastructure.cache.config.CacheConfig: Configuration management
        - app.infrastructure.cache.base.CacheInterface: Cache interface contract
        - app.core.config.Settings: Application settings access
        - app.core.exceptions: Custom exception hierarchy
        - fastapi.Depends: Dependency injection framework

    Optional:
        - redis.asyncio: Redis connectivity for health checks
        - app.infrastructure.cache.monitoring: Performance monitoring
"""

import asyncio
import logging
import os
import weakref
from functools import lru_cache
from typing import Any, Dict
from fastapi import Depends, HTTPException
from app.core.config import Settings
from app.core.exceptions import ConfigurationError, InfrastructureError
from app.infrastructure.cache.base import CacheInterface
from app.infrastructure.cache.factory import CacheFactory
from app.infrastructure.cache.memory import InMemoryCache


class CacheDependencyManager:
    """
    Dependency manager for cache lifecycle and registry management.
    
    This class provides static methods for managing cache connections, registry
    operations, and lifecycle management. It ensures thread-safe access to the
    cache registry and handles connection establishment with proper error handling.
    
    Features:
        - Thread-safe cache registry using asyncio.Lock
        - Weak reference storage to prevent memory leaks
        - Automatic connection management and validation
        - Graceful degradation on connection failures
        - Comprehensive logging for debugging and monitoring
    """

    @staticmethod
    async def cleanup_registry() -> Dict[str, Any]:
        """
        Expose registry cleanup for tests expecting manager-based cleanup.
        """
        ...


@lru_cache
def get_settings() -> Settings:
    """
    Get cached application settings instance.
    
    This dependency provides access to the application settings with LRU caching
    to avoid repeated instantiation. The settings are used to build cache
    configurations and determine environment-specific behaviors.
    
    Returns:
        Settings: Cached application settings instance
    
    Examples:
        @app.get("/config")
        async def get_config(settings: Settings = Depends(get_settings)):
            return {
                "debug": settings.debug,
                "environment": settings.environment
            }
    """
    ...


async def get_cache_config(settings: Settings = Depends(get_settings)) -> Dict[str, Any]:
    """
    Build cache configuration from application settings using preset system.
    
    This dependency creates a CacheConfig instance using the preset-based approach
    with intelligent environment detection and settings integration. It replaces
    the previous CacheConfigBuilder approach with the new preset system that
    reduces 28+ environment variables to a single CACHE_PRESET variable.
    
    Preset System:
        - Loads configuration from settings.cache_preset (default: "development")
        - Supports overrides via CACHE_REDIS_URL and ENABLE_AI_CACHE environment variables
        - Supports custom JSON configuration via CACHE_CUSTOM_CONFIG
        - Provides fallback to "simple" preset on configuration errors
    
    Args:
        settings: Application settings dependency
    
    Returns:
        CacheConfig: Built and validated cache configuration from preset system
    
    Raises:
        ConfigurationError: Configuration building or validation failures
        InfrastructureError: Preset system failures
    
    Examples:
        @app.get("/cache/config")
        async def get_cache_configuration(
            config: CacheConfig = Depends(get_cache_config)
        ):
            return config.to_dict()
    """
    ...


async def get_cache_service(config: Dict[str, Any] = Depends(get_cache_config)) -> CacheInterface:
    """
    Get main cache service with explicit factory usage and registry management.
    
    This is the primary cache dependency that uses CacheFactory.create_cache_from_config()
    for explicit cache creation. It provides registry management, connection handling,
    and graceful fallback to InMemoryCache when Redis is unavailable.
    
    Args:
        config: Cache configuration dependency
    
    Returns:
        CacheInterface: Cache service instance (Redis or InMemory fallback)
    
    Raises:
        InfrastructureError: Critical cache creation failures
        ConfigurationError: Invalid configuration for cache creation
    
    Examples:
        @app.get("/api/data")
        async def get_data(cache: CacheInterface = Depends(get_cache_service)):
            # Cache will be GenericRedisCache or AIResponseCache based on config
            result  =  await cache.get("data_key")
            return result
    """
    ...


async def get_web_cache_service(config = Depends(get_cache_config)) -> CacheInterface:
    """
    Get web-optimized cache service ensuring no AI configuration.
    
    This dependency provides a cache specifically optimized for web applications
    by ensuring the configuration has no AI features enabled and using the
    appropriate factory method.
    
    Args:
        config: Cache configuration dependency
    
    Returns:
        CacheInterface: Web-optimized cache service instance
    
    Raises:
        InfrastructureError: Cache creation failures
        ConfigurationError: Invalid web cache configuration
    
    Examples:
        @app.get("/web/sessions")
        async def get_session_data(
            cache: CacheInterface = Depends(get_web_cache_service)
        ):
            # Guaranteed to be optimized for web usage patterns
            session_data  =  await cache.get("session:123")
            return session_data
    """
    ...


async def get_ai_cache_service(config = Depends(get_cache_config)) -> CacheInterface:
    """
    Get AI-optimized cache service ensuring AI configuration is present.
    
    This dependency provides a cache specifically optimized for AI applications
    by ensuring the configuration includes AI features and using the appropriate
    factory method for AI-specific optimizations.
    
    Args:
        config: Cache configuration dependency
    
    Returns:
        CacheInterface: AI-optimized cache service instance
    
    Raises:
        ConfigurationError: Missing AI configuration
        InfrastructureError: AI cache creation failures
    
    Examples:
        @app.post("/ai/summarize")
        async def summarize_text(
            request: SummarizeRequest,
            ai_cache: CacheInterface = Depends(get_ai_cache_service)
        ):
            # Standard interface usage with AI-optimized cache
            cache_key  =  ai_cache.build_key(request.text, "summarize", request.options)
            result  =  await ai_cache.get(cache_key)
            if not result:
                result  =  {"summary": "Generated summary"}  # Process with AI
                await ai_cache.set(cache_key, result, ttl = 3600)
            return result
    """
    ...


async def get_test_cache() -> CacheInterface:
    """
    Get test cache using memory-only factory method.
    
    This dependency provides a cache specifically for testing scenarios using
    CacheFactory.for_testing() with memory-only mode to ensure test isolation
    and fast execution.
    
    Returns:
        CacheInterface: Memory-based test cache instance
    
    Examples:
        @pytest.fixture
        async def test_cache():
            return await get_test_cache()
    
        async def test_cache_operations(test_cache):
            await test_cache.set("test_key", "test_value")
            assert await test_cache.get("test_key") == "test_value"
    """
    ...


async def get_test_redis_cache() -> CacheInterface:
    """
    Get Redis test cache for integration testing.
    
    This dependency provides a Redis-based test cache using CacheFactory.for_testing()
    with Redis database 15 for integration tests that require Redis functionality.
    
    Returns:
        CacheInterface: Redis-based test cache instance (or InMemory fallback)
    
    Examples:
        @pytest.mark.integration
        async def test_redis_operations():
            cache  =  await get_test_redis_cache()
            await cache.set("integration_test", {"data": "value"})
            result  =  await cache.get("integration_test")
            assert result == {"data": "value"}
    """
    ...


async def get_fallback_cache_service() -> CacheInterface:
    """
    Get fallback cache service that always returns InMemoryCache.
    
    This dependency provides a guaranteed InMemoryCache instance for scenarios
    where Redis is unavailable or for testing degraded mode behavior.
    
    Returns:
        CacheInterface: InMemoryCache instance with safe defaults
    
    Examples:
        @app.get("/fallback/data")
        async def get_fallback_data(
            cache: CacheInterface = Depends(get_fallback_cache_service)
        ):
            # Always uses InMemoryCache regardless of Redis availability
            cached_data  =  await cache.get("fallback_key")
            return cached_data or "no_data"
    """
    ...


async def validate_cache_configuration(config = Depends(get_cache_config)):
    """
    Validate cache configuration and raise HTTP errors for invalid configs.
    
    This dependency validates the cache configuration and converts validation
    errors to appropriate HTTP exceptions for API error responses.
    
    Args:
        config: Cache configuration dependency
    
    Returns:
        CacheConfig: Validated cache configuration
    
    Raises:
        HTTPException: HTTP 500 for invalid configuration
    
    Examples:
        @app.get("/config/validate")
        async def validate_config(
            config: CacheConfig = Depends(validate_cache_configuration)
        ):
            return {"status": "valid", "config": config.to_dict()}
    """
    ...


async def get_cache_service_conditional(enable_ai: bool = False, fallback_only: bool = False, settings: Settings = Depends(get_settings)) -> CacheInterface:
    """
    Get cache service based on conditional parameters.
    
    This dependency provides conditional cache selection based on runtime
    parameters, allowing for dynamic cache behavior within the same application.
    
    Args:
        enable_ai: Whether to use AI-optimized cache
        fallback_only: Whether to force fallback to InMemoryCache
        settings: Application settings dependency
    
    Returns:
        CacheInterface: Cache instance based on conditions
    
    Examples:
        @app.get("/api/data")
        async def get_conditional_data(
            enable_ai: bool  =  Query(False),
            cache: CacheInterface = Depends(
                lambda: get_cache_service_conditional(enable_ai = enable_ai)
            )
        ):
            # Cache type depends on enable_ai parameter
            return await cache.get("conditional_data")
    """
    ...


async def cleanup_cache_registry() -> Dict[str, Any]:
    """
    Clean up cache registry and disconnect active caches.
    
    This function performs comprehensive cleanup of the cache registry,
    disconnecting active caches and removing dead weak references. It's
    designed to be called during application shutdown or maintenance.
    
    Returns:
        Dict[str, Any]: Cleanup statistics and results
    
    Examples:
        @app.on_event("shutdown")
        async def shutdown_event():
            cleanup_stats  =  await cleanup_cache_registry()
            logger.info(f"Cache cleanup completed: {cleanup_stats}")
    """
    ...


async def get_cache_health_status(cache: CacheInterface = Depends(get_cache_service)) -> Dict[str, Any]:
    """
    Get comprehensive cache health status with ping() method support.
    
    This dependency performs comprehensive health checks on the cache instance,
    preferring lightweight ping() operations when available and falling back
    to full operations only when necessary.
    
    Args:
        cache: Cache service dependency
    
    Returns:
        Dict[str, Any]: Comprehensive health status information
    
    Examples:
        @app.get("/health/cache")
        async def cache_health_check(
            health: Dict[str, Any] = Depends(get_cache_health_status)
        ):
            return health
    
        @app.get("/health/detailed")
        async def detailed_health(
            cache_health: Dict[str, Any] = Depends(get_cache_health_status)
        ):
            return {
                "cache": cache_health,
                "timestamp": datetime.utcnow().isoformat()
            }
    """
    ...
