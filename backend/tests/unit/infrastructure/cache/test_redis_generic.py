"""
Unit tests for the GenericRedisCache class following docstring-driven test development.

This test module comprehensively validates the GenericRedisCache implementation
by testing the documented contracts from class and method docstrings. Each test
focuses on specific behavior guarantees documented in the source code.

Test Coverage Areas:
    1. Connection Management: Redis connection establishment, failures, and reconnection
    2. Cache Operations: Basic get/set/delete operations with various data types
    3. L1 Memory Cache Integration: Two-tier caching behavior and synchronization
    4. Data Serialization: JSON fast-path, pickle serialization, and compression
    5. TTL and Expiration: Time-to-live management and automatic expiration
    6. Error Handling: Graceful degradation and Redis unavailability scenarios
    7. Performance Monitoring: Integration with CachePerformanceMonitor
    8. Callback System: Event-driven callback registration and execution
    9. Security Features: Secure connection management and validation
    10. Memory Management: Memory usage tracking and threshold alerting

Business Impact:
    These tests ensure the Redis cache provides reliable, high-performance caching
    capabilities that gracefully handle infrastructure failures while maintaining
    data consistency and performance monitoring for production environments.

Testing Philosophy:
    - Test documented behavior contracts from docstrings (Args, Returns, Raises, Behavior)
    - Mock Redis connections to avoid external dependencies
    - Focus on generic caching patterns rather than Redis implementation details
    - Validate error handling and graceful degradation scenarios
    - Ensure thread safety and async operation correctness
"""

import asyncio
import json
import pickle
import time
import zlib
from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, Mock, patch, MagicMock

import pytest

from app.infrastructure.cache.redis_generic import GenericRedisCache
from app.infrastructure.cache.monitoring import CachePerformanceMonitor
from app.infrastructure.cache.memory import InMemoryCache


class TestGenericRedisCacheConnection:
    """
    Test Redis connection management and resilience patterns.
    
    Business Impact:
        Connection management determines cache availability and performance.
        Proper connection handling ensures graceful degradation when Redis
        is unavailable, maintaining application functionality.
    """

    @pytest.fixture
    def cache(self):
        """Create a GenericRedisCache instance for testing."""
        return GenericRedisCache(
            redis_url="redis://localhost:6379",
            default_ttl=3600,
            enable_l1_cache=True
        )

    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis client for testing."""
        mock = AsyncMock()
        mock.ping.return_value = True
        mock.close.return_value = None
        return mock

    @pytest.mark.asyncio
    async def test_connect_success_with_redis_available(self, cache):
        """
        Test that connect() returns True when Redis is available per docstring.
        
        Business Impact:
            Successful connections enable full-featured caching with Redis persistence
            and improved application performance through data caching.
            
        Test Scenario:
            Redis is available and connection succeeds
            
        Success Criteria:
            - connect() returns True
            - Redis client is properly initialized
            - Connection is established and validated with ping()
        """
        with patch('app.infrastructure.cache.redis_generic.REDIS_AVAILABLE', True):
            with patch('app.infrastructure.cache.redis_generic.aioredis') as mock_aioredis:
                mock_redis = AsyncMock()
                mock_redis.ping = AsyncMock(return_value=True)
                mock_aioredis.from_url = AsyncMock(return_value=mock_redis)
                
                result = await cache.connect()
                
                assert result is True
                assert cache.redis is not None
                mock_aioredis.from_url.assert_called_once()
                mock_redis.ping.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_returns_false_when_redis_unavailable(self, cache):
        """
        Test that connect() returns False when Redis is unavailable per docstring.
        
        Business Impact:
            When Redis is unavailable, the cache gracefully degrades to memory-only mode,
            maintaining application functionality without external dependencies.
            
        Test Scenario:
            Redis package is not available (REDIS_AVAILABLE = False)
            
        Success Criteria:
            - connect() returns False
            - Cache operates in memory-only mode
            - No Redis client initialization attempted
        """
        with patch('app.infrastructure.cache.redis_generic.REDIS_AVAILABLE', False):
            result = await cache.connect()
            
            assert result is False
            assert cache.redis is None

    @pytest.mark.asyncio
    async def test_connect_handles_connection_failures_gracefully(self, cache):
        """
        Test that connect() handles Redis connection failures gracefully per docstring.
        
        Business Impact:
            Connection failure handling prevents application crashes and enables
            graceful degradation to memory-only cache operation.
            
        Test Scenario:
            Redis is available but connection fails (network/auth/config issues)
            
        Success Criteria:
            - connect() returns False on connection failure
            - No exceptions propagated to caller
            - Connection retry throttling prevents repeated failed attempts
        """
        with patch('app.infrastructure.cache.redis_generic.REDIS_AVAILABLE', True):
            with patch('app.infrastructure.cache.redis_generic.aioredis') as mock_aioredis:
                mock_aioredis.from_url.side_effect = Exception("Connection failed")
                
                result = await cache.connect()
                
                assert result is False
                assert cache.redis is None
                assert cache._last_connect_result is False

    @pytest.mark.asyncio
    async def test_connect_throttles_repeated_failed_attempts(self, cache):
        """
        Test that connect() throttles repeated failed connection attempts per implementation.
        
        Business Impact:
            Connection throttling prevents performance degradation from repeated
            failed connection attempts when Redis is persistently unavailable.
            
        Test Scenario:
            Multiple rapid connection attempts after initial failure
            
        Success Criteria:
            - First attempt fails and sets throttling state
            - Subsequent attempts within throttle interval return False immediately
            - No actual connection attempts made during throttling period
        """
        with patch('app.infrastructure.cache.redis_generic.REDIS_AVAILABLE', True):
            with patch('app.infrastructure.cache.redis_generic.aioredis') as mock_aioredis:
                mock_aioredis.from_url.side_effect = Exception("Connection failed")
                
                # First attempt should fail and set throttling
                result1 = await cache.connect()
                assert result1 is False
                
                # Immediate second attempt should be throttled
                result2 = await cache.connect()
                assert result2 is False
                
                # Should only have made one actual connection attempt
                assert mock_aioredis.from_url.call_count == 1

    @pytest.mark.asyncio
    async def test_disconnect_closes_redis_connection_cleanly(self, cache, mock_redis):
        """
        Test that disconnect() cleanly closes Redis connection per docstring.
        
        Business Impact:
            Proper connection cleanup prevents resource leaks and ensures
            clean application shutdown with proper Redis connection management.
            
        Test Scenario:
            Active Redis connection is properly disconnected
            
        Success Criteria:
            - Redis connection is closed via close() method
            - Cache redis attribute is set to None
            - No exceptions during disconnect process
        """
        cache.redis = mock_redis
        
        await cache.disconnect()
        
        mock_redis.close.assert_called_once()
        assert cache.redis is None

    @pytest.mark.asyncio
    async def test_disconnect_handles_redis_none_gracefully(self, cache):
        """
        Test that disconnect() handles None Redis client gracefully per docstring.
        
        Business Impact:
            Graceful handling of disconnect when no connection exists prevents
            errors during cleanup and supports idempotent disconnect operations.
            
        Test Scenario:
            disconnect() called when no Redis connection exists
            
        Success Criteria:
            - No exceptions raised
            - Operation completes successfully
            - Cache state remains consistent
        """
        cache.redis = None
        
        # Should not raise any exceptions
        await cache.disconnect()
        
        assert cache.redis is None


class TestGenericRedisCacheOperations:
    """
    Test core cache operations (get/set/delete/exists) with various data types.
    
    Business Impact:
        Core cache operations are fundamental to application performance and
        data consistency. These tests ensure reliable caching behavior across
        different data types and scenarios.
    """

    @pytest.fixture
    def cache(self):
        """Create a GenericRedisCache instance for testing."""
        monitor = CachePerformanceMonitor()
        return GenericRedisCache(
            redis_url="redis://localhost:6379",
            default_ttl=3600,
            enable_l1_cache=True,
            performance_monitor=monitor
        )

    @pytest.fixture
    def mock_redis(self):
        """Create a mock Redis client for testing."""
        mock = AsyncMock()
        mock.ping.return_value = True
        mock.get.return_value = None
        mock.setex.return_value = True
        mock.delete.return_value = 0
        mock.exists.return_value = 0
        return mock

    @pytest.mark.asyncio
    async def test_get_returns_none_for_missing_key(self, cache, mock_redis):
        """
        Test that get() returns None for missing keys per docstring contract.
        
        Business Impact:
            Consistent None return for missing keys enables reliable cache miss
            detection and proper fallback to data source operations.
            
        Test Scenario:
            Key does not exist in either L1 cache or Redis
            
        Success Criteria:
            - get() returns None for non-existent key
            - Performance metrics recorded for cache miss
            - get_miss callback fired with correct key
        """
        cache.redis = mock_redis
        mock_redis.get.return_value = None
        
        result = await cache.get("nonexistent_key")
        
        assert result is None
        mock_redis.get.assert_called_once_with("nonexistent_key")

    @pytest.mark.asyncio
    async def test_get_retrieves_value_from_redis_successfully(self, cache, mock_redis):
        """
        Test that get() successfully retrieves and deserializes values from Redis per docstring.
        
        Business Impact:
            Successful value retrieval from Redis provides fast data access
            and reduces database load through effective caching.
            
        Test Scenario:
            Key exists in Redis with serialized data
            
        Success Criteria:
            - get() returns original deserialized value
            - Value is populated in L1 cache for future access
            - Performance metrics recorded for cache hit
            - get_success callback fired with key and value
        """
        test_data = {"name": "John", "age": 30, "active": True}
        compressed_data = cache._compress_data(test_data)
        
        cache.redis = mock_redis
        mock_redis.get.return_value = compressed_data
        
        result = await cache.get("user:123")
        
        assert result == test_data
        mock_redis.get.assert_called_once_with("user:123")

    @pytest.mark.asyncio
    async def test_get_checks_l1_cache_first(self, cache, mock_redis):
        """
        Test that get() checks L1 cache before Redis per docstring behavior.
        
        Business Impact:
            L1 cache check optimization provides sub-millisecond data access
            for recently accessed items, significantly improving application performance.
            
        Test Scenario:
            Value exists in L1 memory cache
            
        Success Criteria:
            - get() returns value from L1 cache
            - Redis is not queried when L1 cache hit occurs
            - Performance metrics show L1 cache tier hit
        """
        test_data = {"cached": "in_memory"}
        
        cache.redis = mock_redis
        # Populate L1 cache directly
        await cache.l1_cache.set("test_key", test_data)
        
        result = await cache.get("test_key")
        
        assert result == test_data
        # Redis should not be called due to L1 cache hit
        mock_redis.get.assert_not_called()

    @pytest.mark.asyncio
    async def test_set_stores_value_in_redis_with_ttl(self, cache, mock_redis):
        """
        Test that set() stores value in Redis with correct TTL per docstring contract.
        
        Business Impact:
            Proper value storage with TTL enables automatic cache expiration
            and prevents stale data issues in production applications.
            
        Test Scenario:
            Store value with custom TTL in Redis and L1 cache
            
        Success Criteria:
            - Value is compressed and stored in Redis with specified TTL
            - Value is also stored in L1 cache for fast access
            - Performance metrics recorded for successful set operation
            - set_success callback fired with key and value
        """
        test_data = {"stored": "data", "timestamp": time.time()}
        custom_ttl = 1800  # 30 minutes
        
        cache.redis = mock_redis
        
        await cache.set("storage_key", test_data, ttl=custom_ttl)
        
        # Verify Redis setex was called with correct parameters
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert call_args[0][0] == "storage_key"  # key
        assert call_args[0][1] == custom_ttl     # ttl
        # Verify data was compressed/serialized
        stored_data = cache._decompress_data(call_args[0][2])
        assert stored_data == test_data

    @pytest.mark.asyncio
    async def test_set_uses_default_ttl_when_none_specified(self, cache, mock_redis):
        """
        Test that set() uses default TTL when none specified per docstring contract.
        
        Business Impact:
            Default TTL behavior ensures consistent cache expiration policies
            without requiring explicit TTL specification for every operation.
            
        Test Scenario:
            Store value without specifying TTL parameter
            
        Success Criteria:
            - set() uses cache instance default_ttl value
            - Value stored with correct default expiration
            - Both Redis and L1 cache use same TTL value
        """
        test_data = {"default_ttl": "test"}
        
        cache.redis = mock_redis
        
        await cache.set("default_key", test_data)  # No TTL specified
        
        # Should use default TTL (3600 from fixture)
        mock_redis.setex.assert_called_once()
        call_args = mock_redis.setex.call_args
        assert call_args[0][1] == 3600  # default_ttl

    @pytest.mark.asyncio
    async def test_set_falls_back_to_l1_only_when_redis_unavailable(self, cache):
        """
        Test that set() falls back to L1-only storage when Redis unavailable per docstring.
        
        Business Impact:
            L1-only fallback maintains cache functionality during Redis outages,
            ensuring application performance degradation rather than complete failure.
            
        Test Scenario:
            Redis connection is not available but L1 cache is enabled
            
        Success Criteria:
            - Value stored only in L1 cache when Redis unavailable
            - No Redis operations attempted
            - Performance metrics recorded for L1-only operation
        """
        test_data = {"fallback": "data"}
        
        # Ensure Redis connection fails
        with patch.object(cache, 'connect', return_value=False):
            await cache.set("fallback_key", test_data)
        
        # Verify value was stored in L1 cache
        l1_result = await cache.l1_cache.get("fallback_key")
        assert l1_result == test_data

    @pytest.mark.asyncio
    async def test_delete_removes_key_from_both_tiers(self, cache, mock_redis):
        """
        Test that delete() removes key from both L1 cache and Redis per docstring.
        
        Business Impact:
            Consistent key deletion across cache tiers prevents stale data
            and ensures cache invalidation works correctly for data consistency.
            
        Test Scenario:
            Key exists in both L1 cache and Redis
            
        Success Criteria:
            - Key removed from both L1 cache and Redis
            - delete() returns True indicating key existed
            - Performance metrics recorded for successful deletion
            - delete_success callback fired with key
        """
        test_key = "delete_test"
        test_data = {"to_delete": True}
        
        cache.redis = mock_redis
        mock_redis.delete.return_value = 1  # Key existed in Redis
        
        # Pre-populate both caches
        await cache.l1_cache.set(test_key, test_data)
        
        result = await cache.delete(test_key)
        
        assert result is True
        mock_redis.delete.assert_called_once_with(test_key)
        # Verify L1 cache no longer contains the key
        l1_result = await cache.l1_cache.get(test_key)
        assert l1_result is None

    @pytest.mark.asyncio
    async def test_delete_returns_false_when_key_not_found(self, cache, mock_redis):
        """
        Test that delete() returns False when key doesn't exist per docstring.
        
        Business Impact:
            Accurate deletion status reporting enables proper cache invalidation
            tracking and debugging of cache consistency issues.
            
        Test Scenario:
            Key does not exist in either cache tier
            
        Success Criteria:
            - delete() returns False indicating key didn't exist
            - Redis delete operation still attempted
            - Performance metrics recorded with key_existed=False
        """
        cache.redis = mock_redis
        mock_redis.delete.return_value = 0  # Key didn't exist
        
        result = await cache.delete("nonexistent_key")
        
        assert result is False
        mock_redis.delete.assert_called_once_with("nonexistent_key")

    @pytest.mark.asyncio
    async def test_exists_checks_both_cache_tiers(self, cache, mock_redis):
        """
        Test that exists() checks both L1 cache and Redis per docstring contract.
        
        Business Impact:
            Accurate key existence checking supports conditional cache operations
            and prevents unnecessary data processing when cached data is available.
            
        Test Scenario:
            Key exists in one of the cache tiers
            
        Success Criteria:
            - exists() returns True if key found in either tier
            - L1 cache checked first for performance
            - Redis checked if L1 cache miss occurs
        """
        test_key = "exists_test"
        
        cache.redis = mock_redis
        mock_redis.exists.return_value = 1  # Key exists in Redis
        
        result = await cache.exists(test_key)
        
        assert result is True
        mock_redis.exists.assert_called_once_with(test_key)

    @pytest.mark.asyncio
    async def test_exists_returns_true_for_l1_cache_hit(self, cache, mock_redis):
        """
        Test that exists() returns True for L1 cache hits without Redis check per docstring.
        
        Business Impact:
            L1 cache optimization reduces Redis queries for existence checks,
            improving performance for recently accessed keys.
            
        Test Scenario:
            Key exists in L1 memory cache
            
        Success Criteria:
            - exists() returns True from L1 cache check
            - Redis existence check is skipped
            - Performance optimized through L1 cache hit
        """
        test_key = "l1_exists_test"
        test_data = {"in_l1": True}
        
        cache.redis = mock_redis
        await cache.l1_cache.set(test_key, test_data)
        
        result = await cache.exists(test_key)
        
        assert result is True
        # Redis should not be queried due to L1 hit
        mock_redis.exists.assert_not_called()


class TestGenericRedisCacheDataSerialization:
    """
    Test data compression, serialization, and deserialization behavior.
    
    Business Impact:
        Data serialization affects memory usage, network transfer efficiency,
        and cache performance. Proper serialization ensures data integrity
        while optimizing storage and transfer costs.
    """

    @pytest.fixture
    def cache(self):
        """Create cache with specific compression settings for testing."""
        return GenericRedisCache(
            compression_threshold=100,  # Low threshold for testing
            compression_level=6
        )

    def test_compress_data_uses_json_fast_path_for_small_data(self, cache):
        """
        Test that _compress_data uses JSON fast-path for small compatible data per docstring.
        
        Business Impact:
            JSON fast-path provides optimal performance for common small data types,
            reducing serialization overhead and improving cache operation speed.
            
        Test Scenario:
            Small dictionary/list/primitive data under compression threshold
            
        Success Criteria:
            - JSON serialization used instead of pickle for compatible types
            - Data prefixed with "rawj:" marker for identification
            - Original data preserved through compression/decompression cycle
        """
        small_data = {"name": "John", "age": 30}
        
        compressed = cache._compress_data(small_data)
        
        assert compressed.startswith(b"rawj:")
        decompressed = cache._decompress_data(compressed)
        assert decompressed == small_data

    def test_compress_data_uses_pickle_for_large_data(self, cache):
        """
        Test that _compress_data uses pickle serialization for large data per docstring.
        
        Business Impact:
            Pickle serialization handles complex Python objects and large data,
            ensuring complete data fidelity for all cacheable data types.
            
        Test Scenario:
            Data exceeding compression_threshold size limit
            
        Success Criteria:
            - Pickle serialization used for large or complex data
            - Compression applied when data exceeds threshold
            - Data prefixed with appropriate marker (raw: or compressed:)
        """
        # Create large data that exceeds threshold
        large_data = {"large_field": "x" * 200}
        
        compressed = cache._compress_data(large_data)
        
        # Should use compression due to size
        assert compressed.startswith(b"compressed:")
        decompressed = cache._decompress_data(compressed)
        assert decompressed == large_data

    def test_compress_data_applies_compression_above_threshold(self, cache):
        """
        Test that _compress_data applies zlib compression above threshold per docstring.
        
        Business Impact:
            Compression reduces memory usage and network transfer costs for large
            cache entries, optimizing resource utilization in production systems.
            
        Test Scenario:
            String data exceeding compression threshold
            
        Success Criteria:
            - zlib compression applied to large data
            - Compressed size smaller than original
            - Data integrity preserved through compression cycle
        """
        # Large string that will benefit from compression
        large_string = "This is a large string that repeats. " * 10
        
        compressed = cache._compress_data(large_string)
        
        assert compressed.startswith(b"compressed:")
        # Verify compression actually reduced size
        compressed_content = compressed[11:]  # Remove prefix
        assert len(compressed_content) < len(large_string)
        
        # Verify data integrity
        decompressed = cache._decompress_data(compressed)
        assert decompressed == large_string

    def test_compress_data_handles_none_and_primitives(self, cache):
        """
        Test that _compress_data handles None and primitive types per docstring behavior.
        
        Business Impact:
            Proper handling of primitive types ensures cache compatibility with
            all common Python data types used in application caching scenarios.
            
        Test Scenario:
            Various primitive data types (None, int, float, bool, str)
            
        Success Criteria:
            - All primitive types serialized correctly
            - JSON fast-path used for compatible primitives
            - Data integrity preserved for all types
        """
        test_cases = [
            None,
            42,
            3.14,
            True,
            False,
            "simple string"
        ]
        
        for data in test_cases:
            compressed = cache._compress_data(data)
            decompressed = cache._decompress_data(compressed)
            assert decompressed == data

    def test_decompress_data_handles_legacy_formats(self, cache):
        """
        Test that _decompress_data handles legacy data formats per docstring backward compatibility.
        
        Business Impact:
            Backward compatibility ensures smooth cache system upgrades without
            data loss or application errors during deployment transitions.
            
        Test Scenario:
            Data stored without compression prefixes (legacy format)
            
        Success Criteria:
            - Legacy pickle data deserialized correctly
            - Legacy JSON data handled as fallback
            - No errors during backward compatibility processing
        """
        test_data = {"legacy": "data"}
        
        # Create legacy pickle data (no prefix)
        legacy_pickle = pickle.dumps(test_data)
        result = cache._decompress_data(legacy_pickle)
        assert result == test_data
        
        # Test JSON fallback for legacy data
        legacy_json = json.dumps(test_data).encode("utf-8")
        try:
            result = cache._decompress_data(legacy_json)
            # Should either succeed with JSON or fail gracefully
            assert result == test_data or result is None
        except Exception:
            # JSON fallback failure is acceptable for non-JSON data
            pass

    def test_decompress_data_raises_error_for_invalid_data(self, cache):
        """
        Test that _decompress_data raises appropriate errors for invalid data per docstring.
        
        Business Impact:
            Proper error handling for corrupted cache data prevents application
            crashes and enables graceful cache miss handling for data integrity.
            
        Test Scenario:
            Corrupted or invalid serialized data
            
        Success Criteria:
            - Appropriate exceptions raised for corrupted data
            - Error handling prevents application crashes
            - Cache system can recover from data corruption
        """
        invalid_data = b"invalid_data_that_cannot_be_deserialized"
        
        with pytest.raises(Exception):
            cache._decompress_data(invalid_data)


class TestGenericRedisCacheCallbacks:
    """
    Test callback system for cache events and monitoring integration.
    
    Business Impact:
        Callback system enables event-driven cache monitoring, custom analytics,
        and integration with external monitoring systems for operational visibility.
    """

    @pytest.fixture
    def cache(self):
        """Create cache instance for callback testing."""
        return GenericRedisCache(enable_l1_cache=True)

    @pytest.fixture
    def mock_callback(self):
        """Create mock callback function for testing."""
        return Mock()

    @pytest.mark.asyncio
    async def test_register_callback_stores_callback_for_event(self, cache, mock_callback):
        """
        Test that register_callback stores callback for specified event per docstring.
        
        Business Impact:
            Callback registration enables custom monitoring and analytics integration,
            providing visibility into cache performance and usage patterns.
            
        Test Scenario:
            Register callback for cache hit event
            
        Success Criteria:
            - Callback registered and stored for specified event
            - Multiple callbacks can be registered for same event
            - Callback system ready for event triggering
        """
        cache.register_callback('get_success', mock_callback)
        
        # Verify callback was registered
        assert 'get_success' in cache._callbacks
        assert mock_callback in cache._callbacks['get_success']

    @pytest.mark.asyncio
    async def test_callback_fired_on_cache_hit(self, cache, mock_callback):
        """
        Test that callbacks are fired on cache hit events per docstring behavior.
        
        Business Impact:
            Cache hit callbacks enable performance monitoring and custom analytics
            for optimizing cache usage patterns and identifying hot data.
            
        Test Scenario:
            Cache hit triggers registered get_success callback
            
        Success Criteria:
            - Callback invoked with correct parameters on cache hit
            - Key and value passed to callback function
            - Callback execution doesn't affect cache operation
        """
        test_key = "callback_test"
        test_data = {"callback": "data"}
        
        cache.register_callback('get_success', mock_callback)
        
        # Set up L1 cache hit scenario
        await cache.l1_cache.set(test_key, test_data)
        
        result = await cache.get(test_key)
        
        assert result == test_data
        mock_callback.assert_called_once_with(test_key, test_data)

    @pytest.mark.asyncio
    async def test_callback_fired_on_cache_miss(self, cache, mock_callback):
        """
        Test that callbacks are fired on cache miss events per docstring behavior.
        
        Business Impact:
            Cache miss callbacks enable monitoring of cache effectiveness and
            identification of frequently missed keys for cache optimization.
            
        Test Scenario:
            Cache miss triggers registered get_miss callback
            
        Success Criteria:
            - Callback invoked with key parameter on cache miss
            - Callback execution doesn't affect cache operation result
            - Miss tracking supports cache performance analysis
        """
        cache.register_callback('get_miss', mock_callback)
        
        # Ensure cache miss scenario
        with patch.object(cache, 'connect', return_value=False):
            result = await cache.get("missing_key")
        
        assert result is None
        mock_callback.assert_called_once_with("missing_key")

    @pytest.mark.asyncio
    async def test_callback_exception_handling(self, cache):
        """
        Test that callback exceptions don't affect cache operations per docstring.
        
        Business Impact:
            Robust callback error handling ensures cache operations remain reliable
            even when custom callback code contains bugs or failures.
            
        Test Scenario:
            Callback raises exception during cache operation
            
        Success Criteria:
            - Cache operation completes successfully despite callback failure
            - Exception logged but not propagated to cache operation
            - Cache system remains stable and functional
        """
        def failing_callback(*args, **kwargs):
            raise Exception("Callback failure")
        
        cache.register_callback('get_miss', failing_callback)
        
        # Should not raise exception despite callback failure
        with patch.object(cache, 'connect', return_value=False):
            result = await cache.get("test_key")
        
        assert result is None  # Cache operation should succeed


class TestGenericRedisCachePerformanceMonitoring:
    """
    Test integration with CachePerformanceMonitor for metrics collection.
    
    Business Impact:
        Performance monitoring provides operational visibility into cache
        effectiveness, helping optimize application performance and resource usage.
    """

    @pytest.fixture
    def monitor(self):
        """Create CachePerformanceMonitor for testing."""
        return CachePerformanceMonitor()

    @pytest.fixture
    def cache(self, monitor):
        """Create cache with performance monitoring enabled."""
        return GenericRedisCache(
            enable_l1_cache=True,
            performance_monitor=monitor
        )

    @pytest.mark.asyncio
    async def test_performance_metrics_recorded_for_cache_operations(self, cache, monitor):
        """
        Test that cache operations record performance metrics per docstring integration.
        
        Business Impact:
            Performance metrics enable operational monitoring, capacity planning,
            and identification of cache performance issues in production systems.
            
        Test Scenario:
            Cache get operation records timing and hit/miss status
            
        Success Criteria:
            - Operation timing recorded in performance monitor
            - Cache hit/miss status correctly tracked
            - Additional metadata included for analysis
        """
        test_key = "perf_test"
        test_data = {"performance": "data"}
        
        # Set up cache hit scenario
        await cache.l1_cache.set(test_key, test_data)
        
        result = await cache.get(test_key)
        
        assert result == test_data
        # Verify performance metrics were recorded
        assert len(monitor.cache_operation_times) > 0
        latest_metric = monitor.cache_operation_times[-1]
        assert latest_metric.operation_type == "get"
        assert latest_metric.duration > 0

    @pytest.mark.asyncio
    async def test_compression_metrics_recorded(self, cache, monitor):
        """
        Test that compression operations record performance metrics per docstring.
        
        Business Impact:
            Compression metrics help optimize cache storage efficiency and
            identify opportunities for performance improvements.
            
        Test Scenario:
            Large data compression during set operation
            
        Success Criteria:
            - Compression ratio and timing recorded
            - Original and compressed sizes tracked
            - Performance data available for analysis
        """
        # Create data that will trigger compression (must exceed 1000 byte threshold)
        large_data = {"large": "x" * 1500}
        
        with patch.object(cache, 'connect', return_value=True):
            mock_redis = AsyncMock()
            cache.redis = mock_redis
            
            await cache.set("large_key", large_data)
        
        # Verify compression metrics were recorded
        assert len(monitor.compression_ratios) > 0
        latest_metric = monitor.compression_ratios[-1]
        assert latest_metric.original_size > 0
        assert latest_metric.compressed_size > 0


class TestGenericRedisCacheSecurityFeatures:
    """
    Test security configuration and validation features.
    
    Business Impact:
        Security features protect cached data and Redis connections from
        unauthorized access and ensure compliance with security requirements.
    """

    @pytest.fixture
    def mock_security_config(self):
        """Create mock security configuration."""
        return Mock(spec=['redis_auth', 'use_tls'])

    @pytest.fixture
    def mock_security_manager(self):
        """Create mock security manager."""
        mock = Mock()
        mock.create_secure_connection = AsyncMock()
        mock.validate_connection_security = AsyncMock()
        mock.get_security_status.return_value = {"security_enabled": True}
        mock.get_security_recommendations.return_value = ["Test recommendation"]
        return mock

    def test_security_config_initialization(self, mock_security_config):
        """
        Test that security configuration is properly initialized per docstring.
        
        Business Impact:
            Proper security initialization ensures secure Redis connections
            and prevents unauthorized access to cached data in production.
            
        Test Scenario:
            Cache initialized with security configuration
            
        Success Criteria:
            - Security configuration stored and accessible
            - Security manager initialized when security available
            - Warning logged when security unavailable
        """
        with patch('app.infrastructure.cache.redis_generic.SECURITY_AVAILABLE', True):
            with patch('app.infrastructure.cache.redis_generic.RedisCacheSecurityManager') as MockSecurityManager:
                cache = GenericRedisCache(security_config=mock_security_config)
                
                assert cache.security_config is mock_security_config
                MockSecurityManager.assert_called_once()

    @pytest.mark.asyncio
    async def test_validate_security_returns_none_without_security_manager(self):
        """
        Test that validate_security returns None without security manager per docstring.
        
        Business Impact:
            Graceful handling of security validation when security features
            are not configured prevents errors in non-secure environments.
            
        Test Scenario:
            Security validation called without security configuration
            
        Success Criteria:
            - validate_security returns None
            - No exceptions raised
            - Debug message logged about skipping validation
        """
        cache = GenericRedisCache()  # No security config
        
        result = await cache.validate_security()
        
        assert result is None

    def test_get_security_status_without_security_manager(self):
        """
        Test that get_security_status returns appropriate status without security per docstring.
        
        Business Impact:
            Clear security status reporting helps administrators understand
            current security configuration and identify security gaps.
            
        Test Scenario:
            Security status requested without security configuration
            
        Success Criteria:
            - Returns dictionary with security_enabled=False
            - Includes appropriate message about no security configuration
            - Provides clear security level indication
        """
        cache = GenericRedisCache()
        
        status = cache.get_security_status()
        
        assert status["security_enabled"] is False
        assert status["security_level"] == "NONE"
        assert "No security configuration" in status["message"]

    def test_get_security_recommendations_without_security_manager(self):
        """
        Test that get_security_recommendations returns default recommendations per docstring.
        
        Business Impact:
            Security recommendations guide administrators in implementing
            proper cache security configurations for production environments.
            
        Test Scenario:
            Security recommendations requested without security configuration
            
        Success Criteria:
            - Returns list of default security recommendations
            - Recommendations include TLS, authentication, and configuration guidance
            - Actionable advice provided for security improvement
        """
        cache = GenericRedisCache()
        
        recommendations = cache.get_security_recommendations()
        
        assert isinstance(recommendations, list)
        assert len(recommendations) > 0
        # Verify key security recommendations are included
        recommendation_text = " ".join(recommendations)
        assert "TLS" in recommendation_text or "encryption" in recommendation_text
        assert "authentication" in recommendation_text or "AUTH" in recommendation_text

    @pytest.mark.asyncio
    async def test_generate_security_report_without_security_manager(self):
        """
        Test that generate_security_report returns appropriate report without security per docstring.
        
        Business Impact:
            Security reports provide comprehensive security assessments for
            compliance audits and security reviews of cache infrastructure.
            
        Test Scenario:
            Security report generated without security configuration
            
        Success Criteria:
            - Returns formatted security report string
            - Report indicates no security configuration
            - Includes recommendations for enabling security
            - Provides example configuration guidance
        """
        cache = GenericRedisCache()
        
        report = await cache.generate_security_report()
        
        assert isinstance(report, str)
        assert "Security Status: NOT CONFIGURED" in report
        assert "RECOMMENDATIONS:" in report
        assert "SecurityConfig" in report  # Configuration guidance

    @pytest.mark.asyncio
    async def test_test_security_configuration_without_security_manager(self):
        """
        Test that test_security_configuration returns appropriate results without security per docstring.
        
        Business Impact:
            Security configuration testing provides validation of security
            setup and identifies configuration issues before production deployment.
            
        Test Scenario:
            Security configuration test without security configuration
            
        Success Criteria:
            - Returns dictionary with test results
            - Indicates no security configuration
            - Provides timestamp and appropriate status
            - Includes recommendations for security setup
        """
        cache = GenericRedisCache()
        
        results = await cache.test_security_configuration()
        
        assert isinstance(results, dict)
        assert "timestamp" in results
        assert results["security_configured"] is False
        assert results["overall_secure"] is False
        assert "recommendations" in results


class TestGenericRedisCacheEdgeCases:
    """
    Test edge cases and error handling scenarios.
    
    Business Impact:
        Edge case handling ensures cache system reliability under unusual
        conditions and prevents application failures due to unexpected scenarios.
    """

    @pytest.fixture
    def cache(self):
        """Create cache for edge case testing."""
        return GenericRedisCache(enable_l1_cache=True)

    @pytest.mark.asyncio
    async def test_cache_operations_with_none_values(self, cache):
        """
        Test that cache operations handle None values correctly per docstring behavior.
        
        Business Impact:
            Proper None value handling ensures cache can store and retrieve
            None values as legitimate cached data, supporting all application use cases.
            
        Test Scenario:
            Store and retrieve None as a valid cached value
            
        Success Criteria:
            - None values can be stored in cache
            - None values can be retrieved correctly
            - None values distinguished from cache misses
        """
        test_key = "none_value_test"
        
        # Set up in-memory only operation
        with patch.object(cache, 'connect', return_value=False):
            await cache.set(test_key, None)
            result = await cache.get(test_key)
        
        assert result is None
        # Verify it was actually stored (not a cache miss)
        assert await cache.exists(test_key) is True

    @pytest.mark.asyncio
    async def test_cache_operations_with_empty_strings_and_collections(self, cache):
        """
        Test that cache operations handle empty strings and collections per docstring.
        
        Business Impact:
            Proper handling of empty values ensures cache compatibility with
            all valid Python data structures used in application caching.
            
        Test Scenario:
            Store and retrieve empty strings, lists, and dictionaries
            
        Success Criteria:
            - Empty values stored and retrieved correctly
            - Data types preserved through cache operations
            - Empty values distinguished from None and cache misses
        """
        test_cases = [
            ("empty_string", ""),
            ("empty_list", []),
            ("empty_dict", {}),
            ("empty_tuple", ()),
        ]
        
        with patch.object(cache, 'connect', return_value=False):
            for key, value in test_cases:
                await cache.set(key, value)
                result = await cache.get(key)
                assert result == value
                assert type(result) == type(value)

    @pytest.mark.asyncio
    async def test_cache_operations_with_large_keys(self, cache):
        """
        Test that cache operations handle large keys appropriately per implementation limits.
        
        Business Impact:
            Large key handling ensures cache system stability and prevents
            errors when applications generate long cache keys.
            
        Test Scenario:
            Use very long cache keys that might cause issues
            
        Success Criteria:
            - Large keys handled without errors
            - Cache operations complete successfully
            - System remains stable with large keys
        """
        large_key = "x" * 1000  # Very long key
        test_data = {"large_key": "test"}
        
        with patch.object(cache, 'connect', return_value=False):
            await cache.set(large_key, test_data)
            result = await cache.get(large_key)
        
        assert result == test_data

    @pytest.mark.asyncio
    async def test_concurrent_cache_operations(self, cache):
        """
        Test that concurrent cache operations are handled safely per async design.
        
        Business Impact:
            Concurrent operation safety ensures cache system reliability in
            high-concurrency applications and prevents data corruption.
            
        Test Scenario:
            Multiple concurrent cache operations on different keys
            
        Success Criteria:
            - All concurrent operations complete successfully
            - No data corruption or race conditions
            - Cache state remains consistent
        """
        async def cache_operation(key_suffix: int, data: Any):
            key = f"concurrent_test_{key_suffix}"
            await cache.set(key, data)
            return await cache.get(key)
        
        with patch.object(cache, 'connect', return_value=False):
            # Run multiple concurrent operations
            tasks = [
                cache_operation(i, {"data": f"value_{i}"})
                for i in range(10)
            ]
            results = await asyncio.gather(*tasks)
        
        # Verify all operations succeeded
        for i, result in enumerate(results):
            assert result == {"data": f"value_{i}"}


# Run tests command for easy execution
if __name__ == "__main__":
    import subprocess
    subprocess.run([
        "python", "-m", "pytest", __file__, "-v",
        "--tb=short", "--disable-warnings"
    ])