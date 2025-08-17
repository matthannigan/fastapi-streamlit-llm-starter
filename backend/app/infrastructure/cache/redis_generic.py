"""[REFACTORED] Generic Redis cache implementation providing flexible caching capabilities.

This module implements a generic Redis-backed cache that can handle various data
types and caching patterns. It extends the base cache interface with Redis-specific
functionality while maintaining compatibility with the standard cache contract.

Classes:
    GenericRedisCache: A flexible Redis cache implementation that supports
                      multiple data types, custom serialization, and advanced
                      Redis features like expiration, atomic operations, and
                      pipeline operations.

Key Features:
    - Generic data type support with automatic serialization/deserialization
    - TTL (Time To Live) management with Redis native expiration
    - Pipeline operations for batch processing
    - Atomic operations using Redis transactions
    - Connection pooling and failover support
    - Metrics and monitoring integration

Example:
    ```python
    >>> cache = GenericRedisCache(redis_url="redis://localhost:6379")
    >>> await cache.set("user:123", {"name": "John", "age": 30}, ttl=3600)
    >>> user_data = await cache.get("user:123")
    >>> await cache.delete("user:123")
    ```

Note:
    This is a Phase-1 scaffolding stub. Implementation will be added in
    subsequent phases of the cache refactoring project.
"""


import logging
import pickle
import time
import zlib
from collections import defaultdict
from typing import Any, Callable, Dict, List, Optional, TYPE_CHECKING

try:
    from redis import asyncio as aioredis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    aioredis = None

if TYPE_CHECKING:  # pragma: no cover - typing-only imports
    from redis.asyncio import Redis as RedisClient

from app.infrastructure.cache.base import CacheInterface
from app.infrastructure.cache.memory import InMemoryCache
from app.infrastructure.cache.monitoring import CachePerformanceMonitor

# Optional security imports for production environments
try:
    from app.infrastructure.cache.security import (
        SecurityConfig,
        RedisCacheSecurityManager,
        create_security_config_from_env
    )
    SECURITY_AVAILABLE = True
except ImportError:
    SECURITY_AVAILABLE = False

logger = logging.getLogger(__name__)


class GenericRedisCache(CacheInterface):
    """Generic Redis cache with L1 memory tier, compression, and monitoring.

    ### Overview
    This class provides a generic Redis-backed cache with an optional L1 in-memory
    cache for improved performance. It supports automatic data compression,
    comprehensive performance monitoring, and an extensible callback system.

    ### Parameters
    - `redis_url` (str): URL for the Redis server.
    - `default_ttl` (int): Default time-to-live for cache entries in seconds.
    - `enable_l1_cache` (bool): If True, use an in-memory L1 cache.
    - `l1_cache_size` (int): Maximum number of items in the L1 cache.
    - `compression_threshold` (int): Data size in bytes above which to compress.
    - `compression_level` (int): Zlib compression level (1-9).
    - `performance_monitor` (CachePerformanceMonitor): Instance for tracking metrics.

    ### Returns
    A `GenericRedisCache` instance.

    ### Examples
    ```python
    monitor = CachePerformanceMonitor()
    cache = GenericRedisCache(
        redis_url="redis://localhost:6379",
        default_ttl=3600,
        enable_l1_cache=True,
        performance_monitor=monitor
    )
    await cache.connect()
    await cache.set("my_key", {"data": "value"})
    result = await cache.get("my_key")
    print(result)
    # Output: {'data': 'value'}
    ```
    """

    def __init__(
        self,
        redis_url: str = "redis://redis:6379",
        default_ttl: int = 3600,
        enable_l1_cache: bool = True,
        l1_cache_size: int = 100,
        compression_threshold: int = 1000,
        compression_level: int = 6,
        performance_monitor: Optional[CachePerformanceMonitor] = None,
        security_config: Optional["SecurityConfig"] = None,
    ):
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self.enable_l1_cache = enable_l1_cache
        self.compression_threshold = compression_threshold
        self.compression_level = compression_level
        self.redis: Optional["RedisClient"] = None

        self.l1_cache: Optional[InMemoryCache] = None
        if self.enable_l1_cache:
            self.l1_cache = InMemoryCache(
                default_ttl=default_ttl, max_size=l1_cache_size
            )

        self.performance_monitor = performance_monitor or CachePerformanceMonitor()
        self._callbacks: Dict[str, List[Callable]] = defaultdict(list)
        
        # Security configuration
        self.security_config = security_config
        self.security_manager = None
        if security_config and SECURITY_AVAILABLE:
            self.security_manager = RedisCacheSecurityManager(
                config=security_config,
                performance_monitor=self.performance_monitor
            )
        elif security_config and not SECURITY_AVAILABLE:
            logger.warning(
                "Security configuration provided but security module not available. "
                "Operating without security features."
            )

    def _fire_callback(self, event: str, *args, **kwargs):
        """Fires all registered callbacks for a given event."""
        for callback in self._callbacks.get(event, []):
            try:
                callback(*args, **kwargs)
            except Exception as e:
                logger.warning(f"Callback for event '{event}' failed: {e}")

    def register_callback(self, event: str, callback: Callable):
        """Register a callback for cache events.

        ### Overview
        Registers a callback function to be executed when specific cache events
        occur. Supported events: get_success, get_miss, set_success, delete_success.

        ### Parameters
        - `event` (str): The event name to register for.
        - `callback` (Callable): The callback function to execute.

        ### Examples
        ```python
        def on_cache_hit(key, value):
            print(f"Cache hit for key: {key}")

        cache.register_callback('get_success', on_cache_hit)
        ```
        """
        self._callbacks[event].append(callback)

    def _compress_data(self, data: Any) -> bytes:
        """Compress/serialize data efficiently, with JSON fast-path for small payloads.

        ### Overview
        Serializes data with pickle and compresses it using zlib if the data
        size exceeds the configured compression threshold.

        ### Parameters
        - `data` (Any): The data to compress.

        ### Returns
        Compressed bytes with appropriate prefix marking compression status.

        ### Examples
        ```python
        compressed = cache._compress_data({"large": "data"})
        ```
        """
        # JSON fast-path for common small payloads (dict/list/primitives)
        try:
            if isinstance(data, (dict, list, str, int, float, bool)) or data is None:
                json_bytes = json.dumps(data, separators=(",", ":")).encode("utf-8")
                if len(json_bytes) <= self.compression_threshold:
                    return b"rawj:" + json_bytes
        except Exception:
            # Fallback to pickle path on any serialization error
            pass

        pickled_data = pickle.dumps(data)

        # Use the size of original content as the decision signal. For strings/bytes,
        # this better reflects user intent around thresholds used in tests.
        try:
            original_size = len(data) if isinstance(data, (str, bytes, bytearray)) else len(pickled_data)
        except Exception:
            original_size = len(pickled_data)

        if original_size > self.compression_threshold:
            compressed = zlib.compress(pickled_data, self.compression_level)
            logger.debug(
                f"Compressed data: {len(pickled_data)} -> {len(compressed)} bytes"
            )
            return b"compressed:" + compressed

        return b"raw:" + pickled_data

    def _decompress_data(self, data: bytes) -> Any:
        """Decompress/deserialize data that was serialized by _compress_data.

        ### Overview
        Decompresses data if it was compressed, then deserializes using pickle.

        ### Parameters
        - `data` (bytes): The compressed bytes to decompress.

        ### Returns
        The original deserialized data.

        ### Examples
        ```python
        original_data = cache._decompress_data(compressed_bytes)
        ```
        """
        if data.startswith(b"compressed:"):
            compressed_data = data[11:]
            pickled_data = zlib.decompress(compressed_data)
            return pickle.loads(pickled_data)
        if data.startswith(b"raw:"):
            pickled_data = data[4:]
            return pickle.loads(pickled_data)
        if data.startswith(b"rawj:"):
            json_bytes = data[5:]
            return json.loads(json_bytes.decode("utf-8"))
        # Backward compatibility: attempt pickle if no prefix
        try:
            return pickle.loads(data)
        except Exception:
            # As a last resort, try JSON
            try:
                return json.loads(data.decode("utf-8"))
            except Exception:
                raise

    async def connect(self) -> bool:
        """Initialize Redis connection with security features and graceful degradation.

        ### Overview
        Attempts to establish a connection to Redis. If a security manager is configured,
        it uses secure connection features including authentication, TLS encryption, and
        security validation. If Redis is unavailable or the connection fails, the cache
        operates in memory-only mode.

        ### Returns
        True if connected to Redis successfully, False otherwise.

        ### Examples
        ```python
        # Basic connection
        cache = GenericRedisCache()
        connected = await cache.connect()
        if not connected:
            print("Using memory-only mode")
        
        # Secure connection
        security_config = SecurityConfig(redis_auth="password", use_tls=True)
        cache = GenericRedisCache(security_config=security_config)
        connected = await cache.connect()
        ```
        """
        if not REDIS_AVAILABLE:
            logger.warning("Redis not available - operating in memory-only mode")
            return False

        if not self.redis:
            try:
                # Use security manager for secure connections if available
                if self.security_manager:
                    self.redis = await self.security_manager.create_secure_connection(self.redis_url)
                    logger.info(f"Secure Redis connection established at {self.redis_url}")
                    return True
                else:
                    # Fall back to basic connection
                    assert aioredis is not None  # Type checker hint
                    self.redis = await aioredis.from_url(
                        self.redis_url,
                        decode_responses=False,  # Handle binary data
                        socket_connect_timeout=5,
                        socket_timeout=5,
                    )
                    assert self.redis is not None
                    await self.redis.ping()
                    logger.info(f"Basic Redis connection established at {self.redis_url}")
                    return True
            except Exception as e:
                logger.warning(f"Redis connection failed: {e} - using memory-only mode")
                self.redis = None
                return False
        return True

    async def disconnect(self):
        """Disconnect from Redis server.

        ### Overview
        Cleanly closes the Redis connection. This is a no-op if Redis
        is not available or not connected.

        ### Examples
        ```python
        await cache.disconnect()
        ```
        """
        if self.redis:
            try:
                await self.redis.close()
                logger.info("Disconnected from Redis")
            except Exception as e:
                logger.warning(f"Error disconnecting from Redis: {e}")
            finally:
                self.redis = None

    async def get(self, key: str) -> Any:
        """Get a value from the cache with L1 cache check first.

        ### Overview
        Attempts to retrieve a cached value, first from the L1 memory cache
        (if enabled), then from Redis. Includes performance monitoring and
        callback notifications.

        ### Parameters
        - `key` (str): The cache key to retrieve.

        ### Returns
        The cached value if found, None otherwise.

        ### Examples
        ```python
        value = await cache.get("user:123")
        if value:
            print(f"Found: {value}")
        else:
            print("Cache miss")
        ```
        """
        start_time = time.time()

        # Check L1 cache first
        if self.l1_cache:
            l1_value = await self.l1_cache.get(key)
            if l1_value is not None:
                duration = time.time() - start_time
                self.performance_monitor.record_cache_operation_time(
                    operation="get",
                    duration=duration,
                    cache_hit=True,
                    additional_data={"cache_tier": "l1"},
                )
                self._fire_callback("get_success", key, l1_value)
                logger.debug(f"L1 cache hit for key: {key}")
                return l1_value

        # Check Redis
        if not await self.connect():
            duration = time.time() - start_time
            self.performance_monitor.record_cache_operation_time(
                operation="get",
                duration=duration,
                cache_hit=False,
                additional_data={
                    "cache_tier": "redis_unavailable",
                    "reason": "connection_failed",
                },
            )
            self._fire_callback("get_miss", key)
            return None

        try:
            assert self.redis is not None
            cached_data = await self.redis.get(key)
            duration = time.time() - start_time

            if cached_data:
                # Decompress and deserialize
                value = self._decompress_data(cached_data)

                # Populate L1 cache
                if self.l1_cache:
                    await self.l1_cache.set(key, value)

                self.performance_monitor.record_cache_operation_time(
                    operation="get",
                    duration=duration,
                    cache_hit=True,
                    additional_data={"cache_tier": "redis"},
                )
                self._fire_callback("get_success", key, value)
                logger.debug(f"Redis cache hit for key: {key}")
                return value
            else:
                self.performance_monitor.record_cache_operation_time(
                    operation="get",
                    duration=duration,
                    cache_hit=False,
                    additional_data={"cache_tier": "redis", "reason": "key_not_found"},
                )
                self._fire_callback("get_miss", key)
                logger.debug(f"Cache miss for key: {key}")
                return None

        except Exception as e:
            duration = time.time() - start_time
            self.performance_monitor.record_cache_operation_time(
                operation="get",
                duration=duration,
                cache_hit=False,
                additional_data={
                    "cache_tier": "redis",
                    "reason": "error",
                    "error": str(e),
                },
            )
            logger.warning(f"Cache get error for key {key}: {e}")
            self._fire_callback("get_miss", key)
            return None

    async def set(self, key: str, value: Any, ttl: Optional[int] = None):
        """Set a value in the cache with optional TTL.

        ### Overview
        Stores a value in both the L1 memory cache (if enabled) and Redis.
        Automatically compresses large values and records performance metrics.

        ### Parameters
        - `key` (str): The cache key.
        - `value` (Any): The value to cache.
        - `ttl` (Optional[int]): Time-to-live in seconds. Uses default if None.

        ### Examples
        ```python
        await cache.set("user:123", {"name": "John"}, ttl=3600)
        await cache.set("temp_data", "value")  # Uses default TTL
        ```
        """
        start_time = time.time()
        effective_ttl = ttl or self.default_ttl

        # Store in L1 cache first
        if self.l1_cache:
            await self.l1_cache.set(key, value, ttl=effective_ttl)

        # Store in Redis
        if not await self.connect():
            duration = time.time() - start_time
            self.performance_monitor.record_cache_operation_time(
                operation="set",
                duration=duration,
                cache_hit=False,
                additional_data={"reason": "redis_unavailable"},
            )
            logger.debug(f"Set key {key} in L1 cache only (Redis unavailable)")
            return

        try:
            # Compress and serialize
            compression_start = time.time()
            cache_data = self._compress_data(value)
            compression_time = time.time() - compression_start

            # Record compression metrics if compression was used
            original_size = len(str(value))
            if len(cache_data) < original_size:  # Compression occurred
                self.performance_monitor.record_compression_ratio(
                    original_size=original_size,
                    compressed_size=len(cache_data),
                    compression_time=compression_time,
                )

            assert self.redis is not None
            await self.redis.setex(key, effective_ttl, cache_data)

            duration = time.time() - start_time
            self.performance_monitor.record_cache_operation_time(
                operation="set",
                duration=duration,
                cache_hit=True,  # Successful set
                additional_data={
                    "ttl": effective_ttl,
                    "data_size": len(cache_data),
                    "compression_time": compression_time,
                },
            )
            self._fire_callback("set_success", key, value)
            logger.debug(f"Set cache key {key} with TTL {effective_ttl}s")

        except Exception as e:
            duration = time.time() - start_time
            self.performance_monitor.record_cache_operation_time(
                operation="set",
                duration=duration,
                cache_hit=False,
                additional_data={"error": str(e)},
            )
            logger.warning(f"Cache set error for key {key}: {e}")

    async def delete(self, key: str) -> bool:
        """Delete a key from both L1 cache and Redis.

        ### Overview
        Removes a key from both cache tiers and records the operation.

        ### Parameters
        - `key` (str): The cache key to delete.

        ### Returns
        True if the key existed and was deleted, False otherwise.

        ### Examples
        ```python
        deleted = await cache.delete("user:123")
        if deleted:
            print("Key deleted successfully")
        ```
        """
        start_time = time.time()
        existed = False

        # Delete from L1 cache
        if self.l1_cache:
            l1_existed = await self.l1_cache.exists(key)
            if l1_existed:
                await self.l1_cache.delete(key)
                existed = True

        # Delete from Redis
        if await self.connect():
            try:
                assert self.redis is not None
                result = await self.redis.delete(key)
                if result > 0:
                    existed = True
            except Exception as e:
                logger.warning(f"Cache delete error for key {key}: {e}")

        duration = time.time() - start_time
        self.performance_monitor.record_cache_operation_time(
            operation="delete",
            duration=duration,
            cache_hit=existed,
            additional_data={"key_existed": existed},
        )

        if existed:
            self._fire_callback("delete_success", key)
            logger.debug(f"Deleted cache key {key}")
        else:
            logger.debug(f"Cache key {key} did not exist")

        return existed

    async def exists(self, key: str) -> bool:
        """Check if a key exists in either cache tier.

        ### Overview
        Checks for key existence in L1 cache first, then Redis.

        ### Parameters
        - `key` (str): The cache key to check.

        ### Returns
        True if the key exists, False otherwise.

        ### Examples
        ```python
        if await cache.exists("user:123"):
            print("Key exists")
        ```
        """
        # Check L1 cache first
        if self.l1_cache:
            if await self.l1_cache.exists(key):
                return True

        # Check Redis
        if await self.connect():
            try:
                assert self.redis is not None
                result = await self.redis.exists(key)
                return result > 0
            except Exception as e:
                logger.warning(f"Cache exists error for key {key}: {e}")

        return False
    
    async def validate_security(self):
        """Validate Redis connection security if security manager is available.
        
        ### Overview
        Performs comprehensive security validation of the Redis connection
        including authentication, encryption, and certificate checks.
        
        ### Returns
        SecurityValidationResult if security manager is available, None otherwise.
        
        ### Examples
        ```python
        cache = GenericRedisCache(security_config=security_config)
        await cache.connect()
        validation = await cache.validate_security()
        if validation and not validation.is_secure:
            print(f"Security issues: {validation.vulnerabilities}")
        ```
        """
        if not self.security_manager or not self.redis:
            logger.debug("Security validation skipped - no security manager or Redis connection")
            return None
        
        return await self.security_manager.validate_connection_security(self.redis)
    
    def get_security_status(self) -> Dict[str, Any]:
        """Get current security configuration and status.
        
        ### Overview
        Returns information about the current security configuration,
        connection status, and any recent security validations.
        
        ### Returns
        Dictionary containing security status information.
        
        ### Examples
        ```python
        cache = GenericRedisCache(security_config=security_config)
        status = cache.get_security_status()
        print(f"Security level: {status['security_level']}")
        ```
        """
        if not self.security_manager:
            return {
                "security_enabled": False,
                "security_level": "NONE",
                "message": "No security configuration provided"
            }
        
        return self.security_manager.get_security_status()
    
    def get_security_recommendations(self) -> List[str]:
        """Get security recommendations for the current configuration.
        
        ### Overview
        Returns a list of security recommendations based on the current
        configuration and any security validations performed.
        
        ### Returns
        List of security recommendations.
        
        ### Examples
        ```python
        cache = GenericRedisCache(security_config=security_config)
        recommendations = cache.get_security_recommendations()
        for rec in recommendations:
            print(f"💡 {rec}")
        ```
        """
        if not self.security_manager:
            return [
                "🔐 Configure Redis security with SecurityConfig",
                "🔒 Enable TLS encryption for production environments", 
                "🚨 Set up authentication (AUTH or ACL)"
            ]
        
        return self.security_manager.get_security_recommendations()
    
    async def generate_security_report(self) -> str:
        """Generate comprehensive security assessment report.
        
        ### Overview
        Creates a detailed security report including configuration status,
        validation results, vulnerabilities, and recommendations.
        
        ### Returns
        Formatted security report string.
        
        ### Examples
        ```python
        cache = GenericRedisCache(security_config=security_config)
        await cache.connect()
        await cache.validate_security()
        report = await cache.generate_security_report()
        print(report)
        ```
        """
        if not self.security_manager:
            return (
                "REDIS CACHE SECURITY REPORT\n"
                "============================\n\n"
                "❌ Security Status: NOT CONFIGURED\n"
                "Security Level: NONE\n\n"
                "RECOMMENDATIONS:\n"
                "1. 🔐 Configure SecurityConfig with authentication\n"
                "2. 🔒 Enable TLS encryption\n"
                "3. 🚨 Set up Redis ACL or AUTH password\n\n"
                "To enable security, pass a SecurityConfig to GenericRedisCache:\n"
                "  config = SecurityConfig(redis_auth='password', use_tls=True)\n"
                "  cache = GenericRedisCache(security_config=config)\n"
            )
        
        # Validate security if connected
        if self.redis:
            await self.security_manager.validate_connection_security(self.redis)
        
        return self.security_manager.generate_security_report()
    
    async def test_security_configuration(self) -> Dict[str, Any]:
        """Test the security configuration comprehensively.
        
        ### Overview
        Performs comprehensive testing of the security configuration
        including connection tests, authentication validation, and encryption checks.
        
        ### Returns
        Dictionary with detailed test results.
        
        ### Examples
        ```python
        cache = GenericRedisCache(security_config=security_config)
        results = await cache.test_security_configuration()
        print(f"Overall secure: {results['overall_secure']}")
        if results['errors']:
            for error in results['errors']:
                print(f"❌ {error}")
        ```
        """
        if not self.security_manager:
            return {
                "timestamp": time.time(),
                "security_configured": False,
                "overall_secure": False,
                "message": "No security configuration provided",
                "recommendations": self.get_security_recommendations()
            }
        
        return await self.security_manager.test_security_configuration(self.redis_url)
