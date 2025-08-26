"""
FastAPI Dependency Integration with Lifecycle Management

This module provides comprehensive FastAPI dependency injection for cache services
with lifecycle management, thread-safe registry, and health monitoring. It implements
explicit cache creation patterns using CacheFactory methods and supports graceful
degradation with fallback to InMemoryCache.

Classes:
    CacheDependencyManager: Core dependency manager for cache lifecycle and registry
    
Functions:
    get_settings: Cached settings dependency for configuration access
    get_cache_config: Configuration builder with environment detection
    get_cache_service: Main cache service dependency with registry management
    get_web_cache_service: Web-optimized cache service dependency
    get_ai_cache_service: AI-optimized cache service dependency
    get_test_cache: Testing cache dependency with memory fallback
    get_test_redis_cache: Redis testing cache for integration tests
    get_fallback_cache_service: Always returns InMemoryCache for degraded mode
    validate_cache_configuration: Configuration validation dependency
    get_cache_service_conditional: Conditional cache selection based on parameters
    cleanup_cache_registry: Lifecycle cleanup for cache registry
    get_cache_health_status: Comprehensive health check dependency

Key Features:
    - **Thread-Safe Registry**: Weak reference cache registry with asyncio.Lock
    - **Explicit Factory Usage**: Uses CacheFactory.create_cache_from_config() for deterministic creation
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
            cached_data = await cache.get("api_data")
            if cached_data:
                return cached_data
            
            # Fetch fresh data
            fresh_data = fetch_api_data()
            await cache.set("api_data", fresh_data, ttl=300)
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
            cache_key = ai_cache.build_key(request.text, "summarize", request.options)
            cached_result = await ai_cache.get(cache_key)
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
from typing import Any, Dict, Optional, Union

from fastapi import Depends, HTTPException

from app.core.config import Settings
from app.core.exceptions import ConfigurationError, ValidationError, InfrastructureError
from app.infrastructure.cache.base import CacheInterface
from app.infrastructure.cache.factory import CacheFactory
from app.infrastructure.cache.memory import InMemoryCache

# Optional imports for enhanced functionality
try:
    from app.infrastructure.cache.monitoring import CachePerformanceMonitor
    MONITORING_AVAILABLE = True
except ImportError:
    MONITORING_AVAILABLE = False
    CachePerformanceMonitor = None

logger = logging.getLogger(__name__)

# Module-level cache registry with weak references to prevent memory leaks
_cache_registry: Dict[str, weakref.ReferenceType] = {}
_cache_lock = asyncio.Lock()


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
        """Expose registry cleanup for tests expecting manager-based cleanup."""
        return await cleanup_cache_registry()

    @staticmethod
    async def _ensure_cache_connected(cache: CacheInterface) -> CacheInterface:
        """
        Ensure cache is connected and ready for operations.
        
        This method checks if the cache has a connect method and calls it to
        establish or validate the connection. It handles connection failures
        gracefully and returns the cache in its current state.
        
        Args:
            cache: Cache instance to check and connect
            
        Returns:
            CacheInterface: The cache instance (connected or in degraded mode)
            
        Raises:
            InfrastructureError: Critical connection failures that should be reported
        """
        if not hasattr(cache, 'connect'):
            logger.debug(f"Cache {type(cache).__name__} does not have connect method, assuming ready")
            return cache
        
        try:
            logger.debug(f"Ensuring connection for cache {type(cache).__name__}")
            connected = await cache.connect()
            
            if connected:
                logger.debug(f"Cache {type(cache).__name__} connected successfully")
            else:
                logger.warning(f"Cache {type(cache).__name__} connection failed, operating in degraded mode")
            
            return cache
            
        except Exception as e:
            logger.error(f"Failed to connect cache {type(cache).__name__}: {e}")
            # Return cache as-is - it may still work in degraded mode
            return cache

    @staticmethod
    async def _get_or_create_cache(
        cache_key: str,
        factory_func,
        *args,
        **kwargs
    ) -> CacheInterface:
        """
        Get existing cache from registry or create new one with factory function.
        
        This method implements thread-safe cache registry access with weak references
        to prevent memory leaks. It checks the registry for existing caches and
        creates new ones using the provided factory function.
        
        Args:
            cache_key: Unique identifier for cache in registry
            factory_func: Async factory function to create cache
            *args: Positional arguments for factory function
            **kwargs: Keyword arguments for factory function
            
        Returns:
            CacheInterface: Cache instance from registry or newly created
            
        Raises:
            InfrastructureError: Cache creation failures
            ConfigurationError: Invalid factory function or parameters
        """
        async with _cache_lock:
            # Check if cache exists in registry
            if cache_key in _cache_registry:
                cache_ref = _cache_registry[cache_key]
                cache = cache_ref()
                
                if cache is not None:
                    logger.debug(f"Using existing cache from registry: {cache_key}")
                    return await CacheDependencyManager._ensure_cache_connected(cache)
                else:
                    # Clean up dead reference
                    logger.debug(f"Removing dead cache reference: {cache_key}")
                    del _cache_registry[cache_key]
            
            # Create new cache instance
            logger.info(f"Creating new cache instance: {cache_key}")
            try:
                cache = await factory_func(*args, **kwargs)
                
                # Ensure cache is connected
                cache = await CacheDependencyManager._ensure_cache_connected(cache)
                
                # Register with weak reference
                _cache_registry[cache_key] = weakref.ref(cache)
                logger.debug(f"Cache registered in registry: {cache_key}")
                
                return cache
                
            except Exception as e:
                logger.error(f"Failed to create cache {cache_key}: {e}")
                raise InfrastructureError(
                    f"Failed to create cache instance: {str(e)}",
                    context={
                        "cache_key": cache_key,
                        "factory_func": factory_func.__name__ if hasattr(factory_func, '__name__') else str(factory_func),
                        "args": args,
                        "kwargs": {k: str(v) for k, v in kwargs.items()},
                        "original_error": str(e)
                    }
                )


# ============================================================================
# Core Settings and Configuration Dependencies
# ============================================================================

@lru_cache()
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
    logger.debug("Providing cached application settings")
    return Settings()


async def get_cache_config(settings: Settings = Depends(get_settings)):
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
    try:
        logger.debug("Building cache configuration from preset system")
        
        # Use the new preset-based configuration loading from settings
        cache_config = settings.get_cache_config()
        
        logger.info(f"Cache configuration loaded successfully from preset '{settings.cache_preset}'")
        
        # Convert to the expected return type if needed
        # The settings.get_cache_config() returns the new CacheConfig from cache_presets
        # but we need to ensure compatibility with existing code expectations
        
        return cache_config
        
    except Exception as e:
        logger.error(f"Failed to build cache configuration from preset system: {e}")
        
        # Fallback to simple preset on configuration errors
        logger.warning("Falling back to 'simple' cache preset due to configuration error")
        try:
            from app.infrastructure.cache.cache_presets import cache_preset_manager
            fallback_preset = cache_preset_manager.get_preset("simple")
            fallback_config = fallback_preset.to_cache_config()
            logger.info("Using fallback 'simple' cache configuration")
            return fallback_config
            
        except Exception as fallback_error:
            logger.error(f"Fallback cache configuration also failed: {fallback_error}")
            raise ConfigurationError(
                f"Failed to build cache configuration and fallback failed: {str(e)}",
                context={
                    "original_error": str(e),
                    "fallback_error": str(fallback_error),
                    "cache_preset": getattr(settings, 'cache_preset', 'unknown'),
                    "preset_system": "cache_presets"
                }
            )


# ============================================================================
# Main Cache Service Dependencies
# ============================================================================

async def get_cache_service(config = Depends(get_cache_config)) -> CacheInterface:
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
            result = await cache.get("data_key")
            return result
    """
    try:
        logger.debug("Getting main cache service with explicit factory usage")
        
        # Create cache key for registry
        config_dict = config.to_dict()
        cache_key = f"main_cache_{hash(str(sorted(config_dict.items())))}"
        
        # Use factory for explicit cache creation
        factory = CacheFactory()
        
        async def create_cache():
            logger.info("Creating cache using CacheFactory.create_cache_from_config()")
            return await factory.create_cache_from_config(
                config_dict,
                fail_on_connection_error=False  # Enable graceful degradation
            )
        
        cache = await CacheDependencyManager._get_or_create_cache(
            cache_key=cache_key,
            factory_func=create_cache
        )
        
        logger.info(f"Main cache service ready: {type(cache).__name__}")
        return cache
        
    except Exception as e:
        logger.error(f"Failed to get main cache service: {e}")
        
        # Fallback to InMemoryCache for graceful degradation
        logger.warning("Falling back to InMemoryCache for main cache service")
        return InMemoryCache(
            default_ttl=1800,  # 30 minutes
            max_size=100
        )


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
            session_data = await cache.get("session:123")
            return session_data
    """
    try:
        logger.debug("Getting web-optimized cache service")
        
        # Ensure no AI configuration for web cache
        config_dict = config.to_dict()
        if 'ai_config' in config_dict:
            config_dict = {k: v for k, v in config_dict.items() if k != 'ai_config'}
            logger.debug("Removed AI configuration for web cache service")
        
        cache_key = f"web_cache_{hash(str(sorted(config_dict.items())))}"
        
        factory = CacheFactory()
        
        async def create_web_cache():
            logger.info("Creating web cache using CacheFactory.create_cache_from_config()")
            return await factory.create_cache_from_config(
                config_dict,
                fail_on_connection_error=False
            )
        
        cache = await CacheDependencyManager._get_or_create_cache(
            cache_key=cache_key,
            factory_func=create_web_cache
        )
        
        logger.info(f"Web cache service ready: {type(cache).__name__}")
        return cache
        
    except Exception as e:
        logger.error(f"Failed to get web cache service: {e}")
        
        # Fallback to InMemoryCache optimized for web usage
        logger.warning("Falling back to InMemoryCache for web cache service")
        return InMemoryCache(
            default_ttl=1800,  # 30 minutes for web sessions
            max_size=200       # Larger cache for web usage
        )


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
            cache_key = ai_cache.build_key(request.text, "summarize", request.options)
            result = await ai_cache.get(cache_key)
            if not result:
                result = {"summary": "Generated summary"}  # Process with AI
                await ai_cache.set(cache_key, result, ttl=3600)
            return result
    """
    try:
        logger.debug("Getting AI-optimized cache service")
        
        config_dict = config.to_dict()
        
        # Ensure AI configuration is present
        if 'ai_config' not in config_dict:
            logger.warning("No AI configuration found, adding default AI features")
            # Add minimal AI configuration
            config_dict['ai_config'] = {
                'text_hash_threshold': 500,
                'operation_ttls': {},
                'text_size_tiers': {'small': 1000, 'medium': 5000, 'large': 20000},
                'enable_smart_promotion': True,
                'max_text_length': 100000,
                'hash_algorithm': 'sha256'
            }
        
        cache_key = f"ai_cache_{hash(str(sorted(config_dict.items())))}"
        
        factory = CacheFactory()
        
        async def create_ai_cache():
            logger.info("Creating AI cache using CacheFactory.create_cache_from_config()")
            return await factory.create_cache_from_config(
                config_dict,
                fail_on_connection_error=False
            )
        
        cache = await CacheDependencyManager._get_or_create_cache(
            cache_key=cache_key,
            factory_func=create_ai_cache
        )
        
        logger.info(f"AI cache service ready: {type(cache).__name__}")
        return cache
        
    except Exception as e:
        logger.error(f"Failed to get AI cache service: {e}")
        
        # Fallback to InMemoryCache optimized for AI usage
        logger.warning("Falling back to InMemoryCache for AI cache service")
        return InMemoryCache(
            default_ttl=300,   # 5 minutes for AI operations
            max_size=50        # Smaller cache for AI operations
        )


# ============================================================================
# Testing Dependencies
# ============================================================================

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
    logger.debug("Creating memory-only test cache")
    
    factory = CacheFactory()
    cache = await factory.for_testing(use_memory_cache=True)
    
    logger.info(f"Test cache ready: {type(cache).__name__}")
    return cache


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
            cache = await get_test_redis_cache()
            await cache.set("integration_test", {"data": "value"})
            result = await cache.get("integration_test")
            assert result == {"data": "value"}
    """
    logger.debug("Creating Redis test cache for integration testing")
    
    try:
        factory = CacheFactory()
        
        # Use environment variable for test Redis URL or default
        test_redis_url = os.environ.get('TEST_REDIS_URL', 'redis://localhost:6379/15')
        
        cache = await factory.for_testing(
            redis_url=test_redis_url,
            use_memory_cache=False,
            fail_on_connection_error=False
        )
        
        logger.info(f"Test Redis cache ready: {type(cache).__name__}")
        return cache
        
    except Exception as e:
        logger.warning(f"Failed to create Redis test cache, falling back to memory: {e}")
        return await get_test_cache()


# ============================================================================
# Utility Dependencies
# ============================================================================

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
            cached_data = await cache.get("fallback_key")
            return cached_data or "no_data"
    """
    logger.debug("Creating fallback cache service (InMemoryCache)")
    
    cache = InMemoryCache(
        default_ttl=1800,  # 30 minutes
        max_size=100       # Conservative memory usage
    )
    
    logger.info("Fallback cache service ready: InMemoryCache")
    return cache


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
    try:
        logger.debug("Validating cache configuration")
        
        # Run validation if available
        if hasattr(config, 'validate'):
            validation_result = config.validate()
            
            if not validation_result.is_valid:
                logger.error(f"Cache configuration validation failed: {validation_result.errors}")
                raise HTTPException(
                    status_code=500,
                    detail={
                        "error": "Invalid cache configuration",
                        "validation_errors": validation_result.errors,
                        "warnings": validation_result.warnings if hasattr(validation_result, 'warnings') else []
                    }
                )
            
            # Log warnings if present
            if hasattr(validation_result, 'warnings') and validation_result.warnings:
                logger.warning(f"Cache configuration warnings: {validation_result.warnings}")
        
        logger.debug("Cache configuration validation passed")
        return config
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Configuration validation error: {e}")
        raise HTTPException(
            status_code=500,
            detail={
                "error": "Configuration validation failed",
                "message": str(e)
            }
        )


async def get_cache_service_conditional(
    enable_ai: bool = False,
    fallback_only: bool = False,
    settings: Settings = Depends(get_settings)
) -> CacheInterface:
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
            enable_ai: bool = Query(False),
            cache: CacheInterface = Depends(
                lambda: get_cache_service_conditional(enable_ai=enable_ai)
            )
        ):
            # Cache type depends on enable_ai parameter
            return await cache.get("conditional_data")
    """
    try:
        logger.debug(f"Getting conditional cache service: ai={enable_ai}, fallback={fallback_only}")
        
        if fallback_only:
            logger.info("Conditional cache: using fallback cache")
            return await get_fallback_cache_service()
        
        # Build configuration for conditional cache
        config = await get_cache_config(settings)
        
        if enable_ai:
            logger.info("Conditional cache: using AI cache service")
            return await get_ai_cache_service(config)
        else:
            logger.info("Conditional cache: using web cache service")
            return await get_web_cache_service(config)
            
    except Exception as e:
        logger.error(f"Failed to get conditional cache service: {e}")
        logger.warning("Falling back to InMemoryCache for conditional service")
        return await get_fallback_cache_service()


# ============================================================================
# Lifecycle Management
# ============================================================================

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
            cleanup_stats = await cleanup_cache_registry()
            logger.info(f"Cache cleanup completed: {cleanup_stats}")
    """
    cleanup_stats = {
        "total_entries": 0,
        "active_caches": 0,
        "dead_references": 0,
        "disconnected_caches": 0,
        "errors": []
    }
    
    try:
        logger.info("Starting cache registry cleanup")
        
        async with _cache_lock:
            cleanup_stats["total_entries"] = len(_cache_registry)
            
            # Process each cache in registry
            dead_keys = []
            for cache_key, cache_ref in _cache_registry.items():
                cache = cache_ref()
                
                if cache is None:
                    # Dead reference
                    dead_keys.append(cache_key)
                    cleanup_stats["dead_references"] += 1
                    logger.debug(f"Found dead cache reference: {cache_key}")
                else:
                    # Active cache
                    cleanup_stats["active_caches"] += 1
                    
                    # Try to disconnect if cache has disconnect method
                    if hasattr(cache, 'disconnect'):
                        try:
                            await cache.disconnect()
                            cleanup_stats["disconnected_caches"] += 1
                            logger.debug(f"Disconnected cache: {cache_key}")
                        except Exception as e:
                            error_msg = f"Failed to disconnect cache {cache_key}: {str(e)}"
                            cleanup_stats["errors"].append(error_msg)
                            logger.error(error_msg)
            
            # Remove dead references
            for key in dead_keys:
                del _cache_registry[key]
            
            # Clear registry
            _cache_registry.clear()
            
        logger.info(f"Cache registry cleanup completed: {cleanup_stats}")
        return cleanup_stats
        
    except Exception as e:
        error_msg = f"Cache registry cleanup failed: {str(e)}"
        cleanup_stats["errors"].append(error_msg)
        logger.error(error_msg)
        return cleanup_stats


# ============================================================================
# Health Check Dependencies
# ============================================================================

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
    health_status = {
        "cache_type": type(cache).__name__,
        "status": "unknown",
        "ping_available": False,
        "ping_success": False,
        "operation_test": False,
        "errors": [],
        "warnings": [],
        "statistics": {}
    }
    
    try:
        logger.debug(f"Performing health check on cache: {type(cache).__name__}")
        
        # Check for ping() method availability (preferred for health checks)
        if hasattr(cache, 'ping'):
            health_status["ping_available"] = True
            logger.debug("Using ping() method for health check")
            
            try:
                ping_result = await cache.ping()
                health_status["ping_success"] = ping_result
                
                if ping_result:
                    health_status["status"] = "healthy"
                    logger.debug("Cache ping successful")
                else:
                    health_status["status"] = "degraded"
                    health_status["warnings"].append("Cache ping failed but cache may still be operational")
                    logger.warning("Cache ping failed")
                    
            except Exception as e:
                health_status["ping_success"] = False
                health_status["status"] = "degraded"
                health_status["errors"].append(f"Ping operation failed: {str(e)}")
                logger.warning(f"Cache ping operation failed: {e}")
        
        # Fall back to operation test only if ping() is not available
        if not health_status["ping_available"]:
            logger.debug("Ping not available, performing operation test")
            
            try:
                # Lightweight operation test
                test_key = f"health_check_{asyncio.get_event_loop().time()}"
                test_value = "health_check_value"
                
                # Test set operation
                await cache.set(test_key, test_value, ttl=60)
                
                # Test get operation
                retrieved_value = await cache.get(test_key)
                
                if retrieved_value == test_value:
                    health_status["operation_test"] = True
                    health_status["status"] = "healthy"
                    logger.debug("Cache operation test successful")
                else:
                    health_status["status"] = "degraded"
                    health_status["warnings"].append("Cache operation test failed - data integrity issue")
                    logger.warning("Cache operation test failed: data mismatch")
                
                # Clean up test data
                try:
                    await cache.delete(test_key)
                except Exception as cleanup_error:
                    health_status["warnings"].append(f"Failed to clean up test data: {str(cleanup_error)}")
                    logger.warning(f"Failed to clean up health check test data: {cleanup_error}")
                    
            except Exception as e:
                health_status["status"] = "unhealthy"
                health_status["errors"].append(f"Operation test failed: {str(e)}")
                logger.error(f"Cache operation test failed: {e}")
        
        # Add cache statistics if available
        if hasattr(cache, 'get_stats'):
            try:
                stats = await cache.get_stats()
                health_status["statistics"] = stats
                logger.debug("Added cache statistics to health status")
            except Exception as e:
                health_status["warnings"].append(f"Failed to get cache statistics: {str(e)}")
                logger.warning(f"Failed to get cache statistics: {e}")
        
        # Final status determination
        if health_status["status"] == "unknown":
            if health_status.get("ping_success") or health_status.get("operation_test"):
                health_status["status"] = "healthy"
            else:
                health_status["status"] = "unhealthy"
        
        logger.info(f"Cache health check completed: {health_status['status']}")
        return health_status
        
    except Exception as e:
        logger.error(f"Cache health check failed: {e}")
        health_status["status"] = "error"
        health_status["errors"].append(f"Health check failed: {str(e)}")
        return health_status