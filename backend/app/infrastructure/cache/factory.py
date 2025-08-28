"""
Factory for explicit cache instantiation with environment-optimized defaults.

This module provides a comprehensive factory system for creating cache instances
with explicit configuration and deterministic behavior. It offers clear factory
methods for different use cases, eliminating ambiguity in cache selection.

## Classes

**CacheFactory**: Main factory class providing explicit cache creation methods
for web applications, AI applications, testing environments, and configuration-based
instantiation.

## Key Features

- **Explicit Creation**: Clear, deterministic factory methods for specific use cases
- **Environment Defaults**: Pre-configured settings optimized for different environments
- **Configuration Support**: Flexible creation from configuration objects
- **Graceful Fallback**: Automatic fallback to InMemoryCache when Redis unavailable
- **Input Validation**: Comprehensive validation with detailed error messages
- **Type Safety**: Full type annotations for IDE support

## Factory Methods

- `for_web_app()`: Web applications with balanced performance settings
- `for_ai_app()`: AI applications with optimized storage and compression
- `for_testing()`: Testing environments with short TTLs and test databases
- `create_cache_from_config()`: Flexible configuration-based creation

## Usage

```python
factory = CacheFactory()

# Web application cache
cache = await factory.for_web_app(redis_url="redis://localhost:6379")
await cache.set("session:123", {"user_id": 456})

# AI application cache
ai_cache = await factory.for_ai_app(
    redis_url="redis://ai-cache:6379",
    default_ttl=7200
)

# Configuration-based creation
config = {
    "redis_url": "redis://production:6379",
    "default_ttl": 3600,
    "compression_threshold": 2000
}
cache = await factory.create_cache_from_config(config)
    providing optimized defaults for different application types.

Performance Considerations:
    - Factory methods execute in <10ms for typical configurations
    - Redis connection validation adds 5-50ms depending on network latency
    - Fallback to InMemoryCache is instantaneous (<1ms)
    - All factory methods are async to support connection validation

Error Handling:
    - ConfigurationError: Invalid parameters or configuration conflicts
    - ValidationError: Input validation failures with specific field information
    - InfrastructureError: Redis connection or infrastructure issues
    - All errors include context data for debugging and monitoring

Dependencies:
    Required:
        - app.infrastructure.cache.base.CacheInterface: Cache interface contract
        - app.infrastructure.cache.redis_generic.GenericRedisCache: Generic Redis cache
        - app.infrastructure.cache.redis_ai.AIResponseCache: AI-specialized cache
        - app.infrastructure.cache.memory.InMemoryCache: Memory fallback cache
        - app.core.exceptions: Custom exception hierarchy

    Optional:
        - redis.asyncio: Redis connectivity (graceful degradation if unavailable)
        - app.infrastructure.cache.monitoring.CachePerformanceMonitor: Performance tracking
"""

import logging
from typing import Any, Dict, Optional, TYPE_CHECKING

from app.core.exceptions import ConfigurationError, ValidationError, InfrastructureError
from app.infrastructure.cache.base import CacheInterface
from app.infrastructure.cache.redis_generic import GenericRedisCache
from app.infrastructure.cache.redis_ai import AIResponseCache
from app.infrastructure.cache.memory import InMemoryCache

# Optional performance monitoring
try:
    from app.infrastructure.cache.monitoring import CachePerformanceMonitor
    MONITORING_AVAILABLE = True
except ImportError:
    MONITORING_AVAILABLE = False
    CachePerformanceMonitor = None

# Type checking imports
if TYPE_CHECKING:
    pass

logger = logging.getLogger(__name__)


class CacheFactory:
    """
    Factory class for explicit cache instantiation with environment-optimized defaults.

    This factory provides deterministic cache creation for different use cases,
    replacing auto-detection patterns with explicit configuration. Each factory
    method returns a fully configured cache instance optimized for specific
    application types and environments.

    Factory Methods:
        - for_web_app(): Web application cache with balanced performance
        - for_ai_app(): AI application cache with enhanced storage and compression
        - for_testing(): Testing cache with short TTLs and test database support
        - create_cache_from_config(): Configuration-driven cache creation

    Error Handling:
        All factory methods include comprehensive error handling with fallback
        to InMemoryCache when Redis is unavailable. Errors are logged with
        context information for debugging and monitoring.

    Example:
        >>> factory = CacheFactory()
        >>> cache = await factory.for_web_app(redis_url="redis://localhost:6379")
        >>> isinstance(cache, GenericRedisCache)
        True
    """

    def __init__(self):
        """Initialize the CacheFactory with default configuration."""
        self._performance_monitor = None
        if MONITORING_AVAILABLE:
            self._performance_monitor = CachePerformanceMonitor()

        logger.info("CacheFactory initialized")

    def _validate_factory_inputs(
        self,
        redis_url: Optional[str] = None,
        default_ttl: Optional[int] = None,
        fail_on_connection_error: bool = False,
        **kwargs
    ) -> None:
        """
        Validate common factory method inputs with comprehensive error checking.

        This method performs validation of the most common parameters used across
        factory methods to ensure consistent validation behavior and clear error
        messages for invalid configurations.

        Args:
            redis_url: Redis connection URL to validate
            default_ttl: Time-to-live value to validate
            fail_on_connection_error: Whether to fail on connection errors
            **kwargs: Additional parameters for extensibility

        Raises:
            ValidationError: When required parameters are missing or invalid
            ConfigurationError: When parameter combinations are incompatible

        Examples:
            >>> factory = CacheFactory()
            >>> factory._validate_factory_inputs(
            ...     redis_url="redis://localhost:6379",
            ...     default_ttl=3600
            ... )  # No error raised

            >>> factory._validate_factory_inputs(
            ...     redis_url="invalid-url",
            ...     default_ttl=-100
            ... )  # Raises ValidationError
        """
        errors = []

        # Validate redis_url format
        if redis_url is not None:
            if not isinstance(redis_url, str):
                errors.append("redis_url must be a string")
            elif not redis_url.strip():
                errors.append("redis_url cannot be empty")
            elif not (redis_url.startswith("redis://") or redis_url.startswith("rediss://")):
                errors.append("redis_url must start with 'redis://' or 'rediss://'")
            else:
                # Basic URL validation
                try:
                    # Remove protocol and check for basic host:port format
                    url_part = redis_url.split("://", 1)[1]
                    if not url_part or url_part == "/":
                        errors.append("redis_url must include host information")
                except (IndexError, ValueError):
                    errors.append("redis_url format is invalid")

        # Validate default_ttl
        if default_ttl is not None:
            if not isinstance(default_ttl, int):
                errors.append("default_ttl must be an integer")
            elif default_ttl < 0:
                errors.append("default_ttl must be non-negative (0 means no expiration)")
            elif default_ttl > 86400 * 365:  # 1 year in seconds
                errors.append("default_ttl must not exceed 365 days (31,536,000 seconds)")

        # Validate fail_on_connection_error
        if not isinstance(fail_on_connection_error, bool):
            errors.append("fail_on_connection_error must be a boolean")

        # Validate additional parameters
        for key, value in kwargs.items():
            if key == "enable_l1_cache" and not isinstance(value, bool):
                errors.append("enable_l1_cache must be a boolean")
            elif key == "l1_cache_size" and (not isinstance(value, int) or value <= 0):
                errors.append("l1_cache_size must be a positive integer")
            elif key == "compression_threshold" and (not isinstance(value, int) or value < 0):
                errors.append("compression_threshold must be a non-negative integer")
            elif key == "compression_level" and (not isinstance(value, int) or not 1 <= value <= 9):
                errors.append("compression_level must be an integer between 1 and 9")

        if errors:
            error_context = {
                "validation_errors": errors,
                "redis_url": redis_url,
                "default_ttl": default_ttl,
                "fail_on_connection_error": fail_on_connection_error,
                "additional_params": list(kwargs.keys())
            }
            raise ValidationError(
                f"Factory input validation failed: {'; '.join(errors)}",
                context=error_context
            )

        logger.debug(f"Factory input validation passed for {len(kwargs) + 3} parameters")

    async def for_web_app(
        self,
        redis_url: str = "redis://redis:6379",
        default_ttl: int = 1800,  # 30 minutes
        enable_l1_cache: bool = True,
        l1_cache_size: int = 200,
        compression_threshold: int = 2000,
        compression_level: int = 6,
        fail_on_connection_error: bool = False,
        **kwargs
    ) -> CacheInterface:
        """
        Create a cache optimized for web applications with balanced performance.

        This factory method creates a GenericRedisCache configured with defaults
        optimized for typical web application caching patterns. It provides
        balanced performance between memory usage and cache hit rates, with
        moderate TTLs suitable for session data, API responses, and page caching.

        Web Application Optimizations:
            - 30-minute default TTL for reasonable session/data freshness
            - L1 memory cache enabled for fastest access to frequently used data
            - 200-item L1 cache size for good memory usage vs. hit rate balance
            - 2KB compression threshold to optimize network and storage
            - Moderate compression level (6) for balanced speed vs. compression ratio
            - Graceful Redis fallback for high availability

        Args:
            redis_url: Redis server URL (default: "redis://redis:6379")
            default_ttl: Default time-to-live in seconds (default: 1800/30min)
            enable_l1_cache: Enable in-memory L1 cache (default: True)
            l1_cache_size: Maximum L1 cache entries (default: 200)
            compression_threshold: Compress data above this size in bytes (default: 2000)
            compression_level: Zlib compression level 1-9 (default: 6)
            fail_on_connection_error: Raise error if Redis unavailable (default: False)
            **kwargs: Additional parameters passed to GenericRedisCache

        Returns:
            CacheInterface: Configured cache instance (GenericRedisCache or InMemoryCache fallback)

        Raises:
            ValidationError: Invalid parameter values or combinations
            ConfigurationError: Configuration conflicts or missing requirements
            InfrastructureError: Redis connection failed and fail_on_connection_error=True

        Examples:
            Basic web application cache:
                >>> factory = CacheFactory()
                >>> cache = await factory.for_web_app()
                >>> await cache.set("session:abc123", {"user_id": 456})

            Production web cache with custom Redis:
                >>> cache = await factory.for_web_app(
                ...     redis_url="redis://production:6379",
                ...     default_ttl=3600,  # 1 hour
                ...     fail_on_connection_error=True
                ... )

            High-performance web cache:
                >>> cache = await factory.for_web_app(
                ...     l1_cache_size=500,
                ...     compression_threshold=5000,
                ...     compression_level=9
                ... )
        """
        # Validate inputs
        self._validate_factory_inputs(
            redis_url=redis_url,
            default_ttl=default_ttl,
            fail_on_connection_error=fail_on_connection_error,
            enable_l1_cache=enable_l1_cache,
            l1_cache_size=l1_cache_size,
            compression_threshold=compression_threshold,
            compression_level=compression_level
        )

        logger.info(f"Creating web application cache with redis_url={redis_url}, ttl={default_ttl}s")

        try:
            # Create GenericRedisCache with web-optimized defaults
            cache = GenericRedisCache(
                redis_url=redis_url,
                default_ttl=default_ttl,
                enable_l1_cache=enable_l1_cache,
                l1_cache_size=l1_cache_size,
                compression_threshold=compression_threshold,
                compression_level=compression_level,
                performance_monitor=self._performance_monitor,
                **kwargs
            )

            # Test Redis connection
            connected = await cache.connect()

            if not connected:
                if fail_on_connection_error:
                    raise InfrastructureError(
                        "Redis connection failed for web application cache",
                        context={
                            "redis_url": redis_url,
                            "cache_type": "web_app",
                            "fail_on_connection_error": True
                        }
                    )
                else:
                    # Fall back to InMemoryCache
                    logger.warning("Redis connection failed, falling back to InMemoryCache")
                    return InMemoryCache(
                        default_ttl=default_ttl,
                        max_size=l1_cache_size
                    )

            logger.info(f"Web application cache created successfully (Redis connected: {connected})")
            return cache

        except Exception as e:
            if isinstance(e, (ValidationError, ConfigurationError, InfrastructureError)):
                raise

            logger.error(f"Failed to create web application cache: {e}")
            if fail_on_connection_error:
                raise InfrastructureError(
                    f"Failed to create web application cache: {str(e)}",
                    context={
                        "redis_url": redis_url,
                        "cache_type": "web_app",
                        "original_error": str(e)
                    }
                )

            # Fall back to InMemoryCache on any error
            logger.info("Falling back to InMemoryCache due to cache creation error")
            return InMemoryCache(
                default_ttl=default_ttl,
                max_size=l1_cache_size
            )

    async def for_ai_app(
        self,
        redis_url: str = "redis://redis:6379",
        default_ttl: int = 3600,  # 1 hour
        enable_l1_cache: bool = True,
        l1_cache_size: int = 100,
        compression_threshold: int = 1000,
        compression_level: int = 6,
        text_hash_threshold: int = 500,
        memory_cache_size: Optional[int] = None,
        operation_ttls: Optional[Dict[str, int]] = None,
        fail_on_connection_error: bool = False,
        **kwargs
    ) -> CacheInterface:
        """
        Create a cache optimized for AI applications with enhanced storage and compression.

        This factory method creates an AIResponseCache configured with defaults
        optimized for AI workloads. It provides enhanced compression for large AI
        responses, operation-specific TTLs, intelligent key generation, and
        performance optimizations for typical AI usage patterns.

        AI Application Optimizations:
            - 1-hour default TTL for reasonable AI response freshness
            - Lower compression threshold (1KB) for better storage efficiency
            - 100-item L1 cache for frequently accessed AI responses
            - Text hashing threshold for intelligent key generation
            - Operation-specific TTLs for different AI operations
            - Enhanced monitoring for AI-specific metrics

        Args:
            redis_url: Redis server URL (default: "redis://redis:6379")
            default_ttl: Default time-to-live in seconds (default: 3600/1hr)
            enable_l1_cache: Enable in-memory L1 cache (default: True)
            l1_cache_size: Maximum L1 cache entries (default: 100)
            compression_threshold: Compress data above this size in bytes (default: 1000)
            compression_level: Zlib compression level 1-9 (default: 6)
            text_hash_threshold: Hash text above this length for keys (default: 500)
            memory_cache_size: Override l1_cache_size if provided
            operation_ttls: Custom TTLs per AI operation type
            fail_on_connection_error: Raise error if Redis unavailable (default: False)
            **kwargs: Additional parameters passed to AIResponseCache

        Returns:
            CacheInterface: Configured AIResponseCache or InMemoryCache fallback

        Raises:
            ValidationError: Invalid parameter values or combinations
            ConfigurationError: Configuration conflicts or missing requirements
            InfrastructureError: Redis connection failed and fail_on_connection_error=True

        Examples:
            Basic AI application cache:
                >>> factory = CacheFactory()
                >>> cache = await factory.for_ai_app()
                >>> # Use standard interface for caching
                >>> cache_key = cache.build_key("Document to analyze...", "summarize", {"max_length": 100})
                >>> await cache.set(cache_key, {"summary": "Brief summary"}, ttl=3600)

            Production AI cache with custom settings:
                >>> cache = await factory.for_ai_app(
                ...     redis_url="redis://ai-production:6379",
                ...     default_ttl=7200,  # 2 hours
                ...     operation_ttls={
                ...         "summarize": 1800,  # 30 minutes
                ...         "sentiment": 3600,  # 1 hour
                ...         "translate": 7200   # 2 hours
                ...     }
                ... )

            High-compression AI cache:
                >>> cache = await factory.for_ai_app(
                ...     compression_threshold=500,
                ...     compression_level=9,
                ...     text_hash_threshold=200
                ... )
        """
        # Validate inputs with AI-specific parameters
        self._validate_factory_inputs(
            redis_url=redis_url,
            default_ttl=default_ttl,
            fail_on_connection_error=fail_on_connection_error,
            enable_l1_cache=enable_l1_cache,
            l1_cache_size=l1_cache_size,
            compression_threshold=compression_threshold,
            compression_level=compression_level
        )

        # Additional AI-specific validation
        ai_errors = []
        if text_hash_threshold is not None and (not isinstance(text_hash_threshold, int) or text_hash_threshold < 0):
            ai_errors.append("text_hash_threshold must be a non-negative integer")

        if memory_cache_size is not None and (not isinstance(memory_cache_size, int) or memory_cache_size <= 0):
            ai_errors.append("memory_cache_size must be a positive integer")

        if operation_ttls is not None:
            if not isinstance(operation_ttls, dict):
                ai_errors.append("operation_ttls must be a dictionary")
            else:
                for op, ttl in operation_ttls.items():
                    if not isinstance(op, str) or not op.strip():
                        ai_errors.append("operation_ttls keys must be non-empty strings")
                    if not isinstance(ttl, int) or ttl < 0:
                        ai_errors.append(f"operation_ttls['{op}'] must be a non-negative integer")

        if ai_errors:
            raise ValidationError(
                f"AI application cache validation failed: {'; '.join(ai_errors)}",
                context={
                    "validation_errors": ai_errors,
                    "text_hash_threshold": text_hash_threshold,
                    "memory_cache_size": memory_cache_size,
                    "operation_ttls": operation_ttls
                }
            )

        logger.info(f"Creating AI application cache with redis_url={redis_url}, ttl={default_ttl}s")

        try:
            # Use memory_cache_size if provided, otherwise use l1_cache_size
            effective_cache_size = memory_cache_size if memory_cache_size is not None else l1_cache_size

            # Create AIResponseCache with AI-optimized defaults
            cache = AIResponseCache(
                redis_url=redis_url,
                default_ttl=default_ttl,
                memory_cache_size=effective_cache_size,
                compression_threshold=compression_threshold,
                compression_level=compression_level,
                text_hash_threshold=text_hash_threshold,
                operation_ttls=operation_ttls or {},
                performance_monitor=self._performance_monitor,
                **kwargs
            )

            # Test Redis connection
            connected = await cache.connect()

            if not connected:
                if fail_on_connection_error:
                    raise InfrastructureError(
                        "Redis connection failed for AI application cache",
                        context={
                            "redis_url": redis_url,
                            "cache_type": "ai_app",
                            "fail_on_connection_error": True
                        }
                    )
                else:
                    # Fall back to InMemoryCache
                    logger.warning("Redis connection failed, falling back to InMemoryCache")
                    return InMemoryCache(
                        default_ttl=default_ttl,
                        max_size=effective_cache_size
                    )

            logger.info(f"AI application cache created successfully (Redis connected: {connected})")
            return cache

        except Exception as e:
            if isinstance(e, (ValidationError, ConfigurationError, InfrastructureError)):
                raise

            logger.error(f"Failed to create AI application cache: {e}")
            if fail_on_connection_error:
                raise InfrastructureError(
                    f"Failed to create AI application cache: {str(e)}",
                    context={
                        "redis_url": redis_url,
                        "cache_type": "ai_app",
                        "original_error": str(e)
                    }
                )

            # Fall back to InMemoryCache on any error
            logger.info("Falling back to InMemoryCache due to cache creation error")
            effective_cache_size = memory_cache_size if memory_cache_size is not None else l1_cache_size
            return InMemoryCache(
                default_ttl=default_ttl,
                max_size=effective_cache_size
            )

    async def for_testing(
        self,
        redis_url: str = "redis://redis:6379/15",  # Test database 15
        default_ttl: int = 60,  # 1 minute
        enable_l1_cache: bool = False,
        l1_cache_size: int = 50,
        compression_threshold: int = 1000,
        compression_level: int = 1,  # Fast compression for tests
        fail_on_connection_error: bool = False,
        use_memory_cache: bool = False,
        **kwargs
    ) -> CacheInterface:
        """
        Create a cache optimized for testing environments with short TTLs and fast operations.

        This factory method creates a cache configured for testing scenarios with
        short TTLs, minimal memory usage, fast operations, and support for Redis
        test databases. It can also return a pure InMemoryCache for isolated testing.

        Testing Optimizations:
            - 1-minute default TTL for quick test data expiration
            - Redis database 15 by default for test isolation
            - L1 cache disabled to simplify testing behavior
            - Fast compression (level 1) for minimal test overhead
            - Small cache sizes for minimal memory usage
            - Option to use InMemoryCache for isolated tests

        Args:
            redis_url: Redis server URL with test DB (default: "redis://redis:6379/15")
            default_ttl: Default time-to-live in seconds (default: 60/1min)
            enable_l1_cache: Enable in-memory L1 cache (default: False)
            l1_cache_size: Maximum L1 cache entries (default: 50)
            compression_threshold: Compress data above this size in bytes (default: 1000)
            compression_level: Zlib compression level 1-9 (default: 1)
            fail_on_connection_error: Raise error if Redis unavailable (default: False)
            use_memory_cache: Force InMemoryCache usage (default: False)
            **kwargs: Additional parameters passed to cache implementation

        Returns:
            CacheInterface: Configured cache instance optimized for testing

        Raises:
            ValidationError: Invalid parameter values or combinations
            ConfigurationError: Configuration conflicts or missing requirements
            InfrastructureError: Redis connection failed and fail_on_connection_error=True

        Examples:
            Basic testing cache:
                >>> factory = CacheFactory()
                >>> cache = await factory.for_testing()
                >>> await cache.set("test_key", "test_value")

            Memory-only testing cache:
                >>> cache = await factory.for_testing(use_memory_cache=True)
                >>> # Guaranteed to be InMemoryCache

            Custom test database:
                >>> cache = await factory.for_testing(
                ...     redis_url="redis://test-server:6379/10",
                ...     default_ttl=30  # 30 seconds
                ... )

            Strict testing with connection requirements:
                >>> cache = await factory.for_testing(
                ...     fail_on_connection_error=True,
                ...     enable_l1_cache=True
                ... )
        """
        # Validate inputs
        self._validate_factory_inputs(
            redis_url=redis_url,
            default_ttl=default_ttl,
            fail_on_connection_error=fail_on_connection_error,
            enable_l1_cache=enable_l1_cache,
            l1_cache_size=l1_cache_size,
            compression_threshold=compression_threshold,
            compression_level=compression_level
        )

        # Validate use_memory_cache
        if not isinstance(use_memory_cache, bool):
            raise ValidationError(
                "use_memory_cache must be a boolean",
                context={"use_memory_cache": use_memory_cache}
            )

        logger.info(f"Creating testing cache with redis_url={redis_url}, ttl={default_ttl}s, memory_only={use_memory_cache}")

        # Return InMemoryCache if explicitly requested
        if use_memory_cache:
            logger.info("Creating InMemoryCache for testing (memory_only=True)")
            return InMemoryCache(
                default_ttl=default_ttl,
                max_size=l1_cache_size
            )

        try:
            # Create GenericRedisCache with testing-optimized defaults
            cache = GenericRedisCache(
                redis_url=redis_url,
                default_ttl=default_ttl,
                enable_l1_cache=enable_l1_cache,
                l1_cache_size=l1_cache_size,
                compression_threshold=compression_threshold,
                compression_level=compression_level,
                performance_monitor=self._performance_monitor,
                **kwargs
            )

            # Test Redis connection
            connected = await cache.connect()

            if not connected:
                if fail_on_connection_error:
                    raise InfrastructureError(
                        "Redis connection failed for testing cache",
                        context={
                            "redis_url": redis_url,
                            "cache_type": "testing",
                            "fail_on_connection_error": True
                        }
                    )
                else:
                    # Fall back to InMemoryCache
                    logger.warning("Redis connection failed, falling back to InMemoryCache for testing")
                    return InMemoryCache(
                        default_ttl=default_ttl,
                        max_size=l1_cache_size
                    )

            logger.info(f"Testing cache created successfully (Redis connected: {connected})")
            return cache

        except Exception as e:
            if isinstance(e, (ValidationError, ConfigurationError, InfrastructureError)):
                raise

            logger.error(f"Failed to create testing cache: {e}")
            if fail_on_connection_error:
                raise InfrastructureError(
                    f"Failed to create testing cache: {str(e)}",
                    context={
                        "redis_url": redis_url,
                        "cache_type": "testing",
                        "original_error": str(e)
                    }
                )

            # Fall back to InMemoryCache on any error
            logger.info("Falling back to InMemoryCache due to cache creation error")
            return InMemoryCache(
                default_ttl=default_ttl,
                max_size=l1_cache_size
            )

    async def create_cache_from_config(
        self,
        config: Dict[str, Any],
        fail_on_connection_error: bool = False
    ) -> CacheInterface:
        """
        Create a cache instance from a configuration dictionary with flexible parameter support.

        This factory method provides maximum flexibility by accepting a configuration
        dictionary and automatically determining the appropriate cache type based on
        the provided parameters. It supports both GenericRedisCache and AIResponseCache
        configurations with automatic parameter mapping and validation.

        Configuration Detection:
            - If AI-specific parameters are present (text_hash_threshold, operation_ttls),
              creates an AIResponseCache
            - Otherwise, creates a GenericRedisCache
            - Automatically handles parameter mapping and validation
            - Provides comprehensive error messages for invalid configurations

        Args:
            config: Configuration dictionary with cache parameters
            fail_on_connection_error: Raise error if Redis unavailable (default: False)

        Required Configuration Keys:
            - redis_url (str): Redis server URL

        Optional Configuration Keys:
            Common parameters:
                - default_ttl (int): Default time-to-live in seconds
                - enable_l1_cache (bool): Enable in-memory L1 cache
                - l1_cache_size (int): Maximum L1 cache entries
                - compression_threshold (int): Compress data above this size
                - compression_level (int): Zlib compression level 1-9

            AI-specific parameters (triggers AIResponseCache):
                - text_hash_threshold (int): Hash text above this length
                - operation_ttls (Dict[str, int]): Custom TTLs per operation
                - memory_cache_size (int): Override l1_cache_size

        Returns:
            CacheInterface: Configured cache instance based on configuration

        Raises:
            ValidationError: Invalid configuration parameters or missing required keys
            ConfigurationError: Configuration conflicts or incompatible parameters
            InfrastructureError: Redis connection failed and fail_on_connection_error=True

        Examples:
            Basic Redis cache configuration:
                >>> config = {
                ...     "redis_url": "redis://localhost:6379",
                ...     "default_ttl": 3600,
                ...     "enable_l1_cache": True,
                ...     "compression_threshold": 2000
                ... }
                >>> cache = await factory.create_cache_from_config(config)
                >>> isinstance(cache, GenericRedisCache)
                True

            AI cache configuration:
                >>> config = {
                ...     "redis_url": "redis://ai-cache:6379",
                ...     "default_ttl": 7200,
                ...     "text_hash_threshold": 500,
                ...     "operation_ttls": {"summarize": 1800, "sentiment": 3600}
                ... }
                >>> cache = await factory.create_cache_from_config(config)
                >>> isinstance(cache, AIResponseCache)
                True

            Production configuration with strict error handling:
                >>> config = {
                ...     "redis_url": "redis://production:6379",
                ...     "default_ttl": 3600,
                ...     "compression_level": 9,
                ...     "enable_l1_cache": True,
                ...     "l1_cache_size": 500
                ... }
                >>> cache = await factory.create_cache_from_config(
                ...     config,
                ...     fail_on_connection_error=True
                ... )
        """
        # Validate config parameter
        if not isinstance(config, dict):
            raise ValidationError(
                "config must be a dictionary",
                context={"config_type": type(config).__name__}
            )

        if not config:
            raise ValidationError(
                "config dictionary cannot be empty",
                context={"config": config}
            )

        # Validate required parameters
        if "redis_url" not in config:
            raise ValidationError(
                "redis_url is required in config",
                context={"config_keys": list(config.keys())}
            )

        logger.info(f"Creating cache from configuration with {len(config)} parameters")

        # Extract and validate common parameters
        redis_url = config["redis_url"]
        default_ttl = config.get("default_ttl", 3600)
        enable_l1_cache = config.get("enable_l1_cache", True)
        l1_cache_size = config.get("l1_cache_size", 100)
        compression_threshold = config.get("compression_threshold", 1000)
        compression_level = config.get("compression_level", 6)

        # Detect AI-specific parameters to determine cache type
        ai_specific_params = {
            "text_hash_threshold", "operation_ttls", "memory_cache_size"
        }
        has_ai_params = any(param in config for param in ai_specific_params)

        try:
            if has_ai_params:
                # Create AIResponseCache
                logger.info("Configuration contains AI parameters, creating AIResponseCache")

                text_hash_threshold = config.get("text_hash_threshold", 500)
                operation_ttls = config.get("operation_ttls", {})
                memory_cache_size = config.get("memory_cache_size")

                # Filter out AI-specific params from kwargs
                kwargs = {k: v for k, v in config.items()
                          if k not in ai_specific_params and k not in {
                              "redis_url", "default_ttl", "enable_l1_cache",
                              "l1_cache_size", "compression_threshold", "compression_level"
                          }}

                return await self.for_ai_app(
                    redis_url=redis_url,
                    default_ttl=default_ttl,
                    enable_l1_cache=enable_l1_cache,
                    l1_cache_size=l1_cache_size,
                    compression_threshold=compression_threshold,
                    compression_level=compression_level,
                    text_hash_threshold=text_hash_threshold,
                    memory_cache_size=memory_cache_size,
                    operation_ttls=operation_ttls,
                    fail_on_connection_error=fail_on_connection_error,
                    **kwargs
                )
            else:
                # Create GenericRedisCache
                logger.info("Configuration contains generic parameters, creating GenericRedisCache")

                # Filter out known params from kwargs
                kwargs = {k: v for k, v in config.items()
                          if k not in {
                              "redis_url", "default_ttl", "enable_l1_cache",
                              "l1_cache_size", "compression_threshold", "compression_level"
                          }}

                return await self.for_web_app(
                    redis_url=redis_url,
                    default_ttl=default_ttl,
                    enable_l1_cache=enable_l1_cache,
                    l1_cache_size=l1_cache_size,
                    compression_threshold=compression_threshold,
                    compression_level=compression_level,
                    fail_on_connection_error=fail_on_connection_error,
                    **kwargs
                )

        except Exception as e:
            if isinstance(e, (ValidationError, ConfigurationError, InfrastructureError)):
                raise

            logger.error(f"Failed to create cache from configuration: {e}")
            raise ConfigurationError(
                f"Failed to create cache from configuration: {str(e)}",
                context={
                    "config": config,
                    "has_ai_params": has_ai_params,
                    "fail_on_connection_error": fail_on_connection_error,
                    "original_error": str(e)
                }
            )
