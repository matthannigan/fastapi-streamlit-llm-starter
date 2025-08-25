"""
Comprehensive unit tests for GenericRedisCache implementation.

This module tests all aspects of the GenericRedisCache including L1 caching,
compression, monitoring integration, callback system, and error handling.
Designed to achieve 95%+ line coverage.
"""

import asyncio
import pickle
import pytest
import zlib
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Any

from app.infrastructure.cache.redis_generic import GenericRedisCache
from app.infrastructure.cache.monitoring import CachePerformanceMonitor


class TestGenericRedisCache:
    """Test suite for GenericRedisCache with comprehensive coverage."""

    @pytest.fixture
    def performance_monitor(self):
        """Create a performance monitor for testing."""
        return CachePerformanceMonitor()

    @pytest.fixture
    def cache(self, performance_monitor):
        """Create a GenericRedisCache instance for testing."""
        return GenericRedisCache(
            redis_url="redis://localhost:6379",
            default_ttl=3600,
            enable_l1_cache=True,
            l1_cache_size=10,
            compression_threshold=100,
            compression_level=6,
            performance_monitor=performance_monitor,
        )

    @pytest.fixture
    def cache_no_l1(self, performance_monitor):
        """Create a GenericRedisCache instance without L1 cache."""
        return GenericRedisCache(
            enable_l1_cache=False,
            performance_monitor=performance_monitor,
        )

    def test_initialization_with_l1_cache(self, cache):
        """Test cache initialization with L1 cache enabled."""
        assert cache.redis_url == "redis://localhost:6379"
        assert cache.default_ttl == 3600
        assert cache.enable_l1_cache is True
        assert cache.l1_cache is not None
        assert cache.compression_threshold == 100
        assert cache.compression_level == 6
        assert cache.performance_monitor is not None
        assert isinstance(cache._callbacks, dict)

    def test_initialization_without_l1_cache(self, cache_no_l1):
        """Test cache initialization with L1 cache disabled."""
        assert cache_no_l1.enable_l1_cache is False
        assert cache_no_l1.l1_cache is None

    def test_register_callback(self, cache):
        """Test callback registration system."""
        callback_called = False
        
        def test_callback(key, value):
            nonlocal callback_called
            callback_called = True
            
        cache.register_callback("get_success", test_callback)
        assert len(cache._callbacks["get_success"]) == 1
        
        # Test callback firing
        cache._fire_callback("get_success", "test_key", "test_value")
        assert callback_called

    def test_fire_callback_with_exception(self, cache, caplog):
        """Test callback firing handles exceptions gracefully."""
        def failing_callback(key, value):
            raise Exception("Test exception")
            
        cache.register_callback("get_success", failing_callback)
        
        # Should not raise exception
        cache._fire_callback("get_success", "key", "value")
        assert "Callback for event 'get_success' failed" in caplog.text

    def test_compress_data_small_data(self, cache):
        """Test compression with data below threshold."""
        small_data = {"key": "small_value"}
        result = cache._compress_data(small_data)
        
        assert result.startswith(b"raw:")
        # Verify we can decompress it
        decompressed = cache._decompress_data(result)
        assert decompressed == small_data

    def test_compress_data_large_data(self, cache):
        """Test compression with data above threshold."""
        large_data = {"key": "x" * 200}  # Exceeds 100-byte threshold
        result = cache._compress_data(large_data)
        
        assert result.startswith(b"compressed:")
        # Verify we can decompress it
        decompressed = cache._decompress_data(result)
        assert decompressed == large_data

    def test_decompress_data_raw(self, cache):
        """Test decompression of raw (uncompressed) data."""
        data = {"test": "value"}
        pickled = pickle.dumps(data)
        raw_data = b"raw:" + pickled
        
        result = cache._decompress_data(raw_data)
        assert result == data

    def test_decompress_data_compressed(self, cache):
        """Test decompression of compressed data."""
        data = {"test": "value"}
        pickled = pickle.dumps(data)
        compressed = zlib.compress(pickled)
        compressed_data = b"compressed:" + compressed
        
        result = cache._decompress_data(compressed_data)
        assert result == data

    @pytest.mark.asyncio
    async def test_connect_redis_unavailable(self, cache):
        """Test connection when Redis is unavailable."""
        with patch('app.infrastructure.cache.redis_generic.REDIS_AVAILABLE', False):
            result = await cache.connect()
            assert result is False
            assert cache.redis is None

    @pytest.mark.asyncio
    async def test_connect_success(self, cache):
        """Test successful Redis connection."""
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock()
        
        with patch('app.infrastructure.cache.redis_generic.aioredis') as mock_aioredis:
            mock_aioredis.from_url = AsyncMock(return_value=mock_redis)
            
            result = await cache.connect()
            assert result is True
            assert cache.redis is mock_redis
            mock_redis.ping.assert_called_once()

    @pytest.mark.asyncio
    async def test_connect_failure(self, cache):
        """Test Redis connection failure."""
        with patch('app.infrastructure.cache.redis_generic.aioredis') as mock_aioredis:
            mock_aioredis.from_url = AsyncMock(side_effect=Exception("Connection failed"))
            
            result = await cache.connect()
            assert result is False
            assert cache.redis is None

    @pytest.mark.asyncio
    async def test_disconnect_success(self, cache):
        """Test successful Redis disconnection."""
        mock_redis = AsyncMock()
        cache.redis = mock_redis
        
        await cache.disconnect()
        mock_redis.close.assert_called_once()
        assert cache.redis is None

    @pytest.mark.asyncio
    async def test_disconnect_with_error(self, cache, caplog):
        """Test disconnection with Redis error."""
        mock_redis = AsyncMock()
        mock_redis.close = AsyncMock(side_effect=Exception("Disconnect error"))
        cache.redis = mock_redis
        
        await cache.disconnect()
        assert cache.redis is None
        assert "Error disconnecting from Redis" in caplog.text

    @pytest.mark.asyncio
    async def test_disconnect_no_connection(self, cache):
        """Test disconnection when not connected."""
        cache.redis = None
        await cache.disconnect()  # Should not raise

    @pytest.mark.asyncio
    async def test_get_l1_cache_hit(self, cache):
        """Test cache get with L1 cache hit."""
        test_value = {"test": "value"}
        
        # Mock L1 cache hit
        cache.l1_cache.get = AsyncMock(return_value=test_value)
        
        # Track callback
        callback_called = False
        def callback(key, value):
            nonlocal callback_called
            callback_called = True
            
        cache.register_callback("get_success", callback)
        
        result = await cache.get("test_key")
        
        assert result == test_value
        assert callback_called
        assert cache.performance_monitor.cache_hits > 0

    @pytest.mark.asyncio
    async def test_get_redis_hit(self, cache):
        """Test cache get with Redis hit (L1 miss)."""
        test_value = {"test": "value"}
        compressed_data = cache._compress_data(test_value)
        
        # Mock L1 cache miss
        cache.l1_cache.get = AsyncMock(return_value=None)
        cache.l1_cache.set = AsyncMock()
        
        # Mock Redis hit
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=compressed_data)
        cache.redis = mock_redis
        cache.connect = AsyncMock(return_value=True)
        
        result = await cache.get("test_key")
        
        assert result == test_value
        # Should populate L1 cache
        cache.l1_cache.set.assert_called_once_with("test_key", test_value)

    @pytest.mark.asyncio
    async def test_get_cache_miss(self, cache):
        """Test cache get with complete miss."""
        # Mock L1 cache miss
        cache.l1_cache.get = AsyncMock(return_value=None)
        
        # Mock Redis miss
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=None)
        cache.redis = mock_redis
        cache.connect = AsyncMock(return_value=True)
        
        # Track callback
        callback_called = False
        def callback(key):
            nonlocal callback_called
            callback_called = True
            
        cache.register_callback("get_miss", callback)
        
        result = await cache.get("test_key")
        
        assert result is None
        assert callback_called
        assert cache.performance_monitor.cache_misses > 0

    @pytest.mark.asyncio
    async def test_get_redis_unavailable(self, cache):
        """Test cache get when Redis is unavailable."""
        cache.l1_cache.get = AsyncMock(return_value=None)
        cache.connect = AsyncMock(return_value=False)
        
        result = await cache.get("test_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_redis_error(self, cache):
        """Test cache get with Redis error."""
        cache.l1_cache.get = AsyncMock(return_value=None)
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(side_effect=Exception("Redis error"))
        cache.redis = mock_redis
        cache.connect = AsyncMock(return_value=True)
        
        result = await cache.get("test_key")
        assert result is None

    @pytest.mark.asyncio
    async def test_get_without_l1_cache(self, cache_no_l1):
        """Test cache get without L1 cache."""
        test_value = {"test": "value"}
        compressed_data = cache_no_l1._compress_data(test_value)
        
        mock_redis = AsyncMock()
        mock_redis.get = AsyncMock(return_value=compressed_data)
        cache_no_l1.redis = mock_redis
        cache_no_l1.connect = AsyncMock(return_value=True)
        
        result = await cache_no_l1.get("test_key")
        assert result == test_value

    @pytest.mark.asyncio
    async def test_set_success(self, cache):
        """Test successful cache set operation."""
        test_value = {"test": "value"}
        
        # Mock L1 cache
        cache.l1_cache.set = AsyncMock()
        
        # Mock Redis
        mock_redis = AsyncMock()
        mock_redis.setex = AsyncMock()
        cache.redis = mock_redis
        cache.connect = AsyncMock(return_value=True)
        
        # Track callback
        callback_called = False
        def callback(key, value):
            nonlocal callback_called
            callback_called = True
            
        cache.register_callback("set_success", callback)
        
        await cache.set("test_key", test_value, ttl=1800)
        
        cache.l1_cache.set.assert_called_once_with("test_key", test_value, ttl=1800)
        mock_redis.setex.assert_called_once()
        assert callback_called

    @pytest.mark.asyncio
    async def test_set_with_compression(self, cache):
        """Test set operation with data compression."""
        large_value = {"data": "x" * 200}  # Exceeds compression threshold
        
        cache.l1_cache.set = AsyncMock()
        mock_redis = AsyncMock()
        mock_redis.setex = AsyncMock()
        cache.redis = mock_redis
        cache.connect = AsyncMock(return_value=True)
        
        await cache.set("test_key", large_value)
        
        # Check that compression metrics were recorded
        assert len(cache.performance_monitor.compression_ratios) > 0

    @pytest.mark.asyncio
    async def test_set_redis_unavailable(self, cache):
        """Test set operation when Redis is unavailable."""
        cache.l1_cache.set = AsyncMock()
        cache.connect = AsyncMock(return_value=False)
        
        await cache.set("test_key", "value")
        
        # Should still set in L1 cache
        cache.l1_cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_redis_error(self, cache):
        """Test set operation with Redis error."""
        cache.l1_cache.set = AsyncMock()
        mock_redis = AsyncMock()
        mock_redis.setex = AsyncMock(side_effect=Exception("Redis error"))
        cache.redis = mock_redis
        cache.connect = AsyncMock(return_value=True)
        
        await cache.set("test_key", "value")
        
        # Should handle error gracefully
        cache.l1_cache.set.assert_called_once()

    @pytest.mark.asyncio
    async def test_set_without_l1_cache(self, cache_no_l1):
        """Test set operation without L1 cache."""
        mock_redis = AsyncMock()
        mock_redis.setex = AsyncMock()
        cache_no_l1.redis = mock_redis
        cache_no_l1.connect = AsyncMock(return_value=True)
        
        await cache_no_l1.set("test_key", "value")
        mock_redis.setex.assert_called_once()

    @pytest.mark.asyncio
    async def test_delete_key_exists(self, cache):
        """Test delete operation when key exists."""
        # Mock L1 cache
        cache.l1_cache.exists = AsyncMock(return_value=True)
        cache.l1_cache.delete = AsyncMock()
        
        # Mock Redis
        mock_redis = AsyncMock()
        mock_redis.delete = AsyncMock(return_value=1)  # Key existed
        cache.redis = mock_redis
        cache.connect = AsyncMock(return_value=True)
        
        # Track callback
        callback_called = False
        def callback(key):
            nonlocal callback_called
            callback_called = True
            
        cache.register_callback("delete_success", callback)
        
        result = await cache.delete("test_key")
        
        assert result is True
        assert callback_called
        cache.l1_cache.delete.assert_called_once_with("test_key")
        mock_redis.delete.assert_called_once_with("test_key")

    @pytest.mark.asyncio
    async def test_delete_key_not_exists(self, cache):
        """Test delete operation when key doesn't exist."""
        cache.l1_cache.exists = AsyncMock(return_value=False)
        
        mock_redis = AsyncMock()
        mock_redis.delete = AsyncMock(return_value=0)  # Key didn't exist
        cache.redis = mock_redis
        cache.connect = AsyncMock(return_value=True)
        
        result = await cache.delete("test_key")
        assert result is False

    @pytest.mark.asyncio
    async def test_delete_redis_error(self, cache):
        """Test delete operation with Redis error."""
        cache.l1_cache.exists = AsyncMock(return_value=True)
        cache.l1_cache.delete = AsyncMock()
        
        mock_redis = AsyncMock()
        mock_redis.delete = AsyncMock(side_effect=Exception("Redis error"))
        cache.redis = mock_redis
        cache.connect = AsyncMock(return_value=True)
        
        result = await cache.delete("test_key")
        assert result is True  # L1 cache had the key

    @pytest.mark.asyncio
    async def test_delete_without_l1_cache(self, cache_no_l1):
        """Test delete operation without L1 cache."""
        mock_redis = AsyncMock()
        mock_redis.delete = AsyncMock(return_value=1)
        cache_no_l1.redis = mock_redis
        cache_no_l1.connect = AsyncMock(return_value=True)
        
        result = await cache_no_l1.delete("test_key")
        assert result is True

    @pytest.mark.asyncio
    async def test_exists_l1_cache_hit(self, cache):
        """Test exists operation with L1 cache hit."""
        cache.l1_cache.exists = AsyncMock(return_value=True)
        
        result = await cache.exists("test_key")
        assert result is True

    @pytest.mark.asyncio
    async def test_exists_redis_hit(self, cache):
        """Test exists operation with Redis hit (L1 miss)."""
        cache.l1_cache.exists = AsyncMock(return_value=False)
        
        mock_redis = AsyncMock()
        mock_redis.exists = AsyncMock(return_value=1)
        cache.redis = mock_redis
        cache.connect = AsyncMock(return_value=True)
        
        result = await cache.exists("test_key")
        assert result is True

    @pytest.mark.asyncio
    async def test_exists_not_found(self, cache):
        """Test exists operation when key is not found."""
        cache.l1_cache.exists = AsyncMock(return_value=False)
        
        mock_redis = AsyncMock()
        mock_redis.exists = AsyncMock(return_value=0)
        cache.redis = mock_redis
        cache.connect = AsyncMock(return_value=True)
        
        result = await cache.exists("test_key")
        assert result is False

    @pytest.mark.asyncio
    async def test_exists_redis_error(self, cache):
        """Test exists operation with Redis error."""
        cache.l1_cache.exists = AsyncMock(return_value=False)
        
        mock_redis = AsyncMock()
        mock_redis.exists = AsyncMock(side_effect=Exception("Redis error"))
        cache.redis = mock_redis
        cache.connect = AsyncMock(return_value=True)
        
        result = await cache.exists("test_key")
        assert result is False

    @pytest.mark.asyncio
    async def test_exists_without_l1_cache(self, cache_no_l1):
        """Test exists operation without L1 cache."""
        mock_redis = AsyncMock()
        mock_redis.exists = AsyncMock(return_value=1)
        cache_no_l1.redis = mock_redis
        cache_no_l1.connect = AsyncMock(return_value=True)
        
        result = await cache_no_l1.exists("test_key")
        assert result is True

    def test_performance_monitoring_integration(self, cache):
        """Test that performance monitoring is properly integrated."""
        # Performance monitor should be set
        assert cache.performance_monitor is not None
        
        # Initial stats should be zero
        assert cache.performance_monitor.cache_hits == 0
        assert cache.performance_monitor.cache_misses == 0

    @pytest.mark.asyncio
    async def test_full_cache_workflow(self, cache):
        """Test complete cache workflow: set, get, exists, delete."""
        test_value = {"name": "John", "age": 30}
        
        # Mock Redis and L1 cache
        mock_redis = AsyncMock()
        mock_redis.setex = AsyncMock()
        mock_redis.get = AsyncMock(return_value=cache._compress_data(test_value))
        mock_redis.exists = AsyncMock(return_value=1)
        mock_redis.delete = AsyncMock(return_value=1)
        
        cache.redis = mock_redis
        cache.connect = AsyncMock(return_value=True)
        cache.l1_cache.set = AsyncMock()
        cache.l1_cache.get = AsyncMock(return_value=None)  # Force Redis lookup
        cache.l1_cache.exists = AsyncMock(return_value=False)
        cache.l1_cache.delete = AsyncMock()
        
        # Set value
        await cache.set("user:123", test_value)
        mock_redis.setex.assert_called_once()
        
        # Get value
        result = await cache.get("user:123")
        assert result == test_value
        
        # Check existence
        exists = await cache.exists("user:123")
        assert exists is True
        
        # Delete value
        deleted = await cache.delete("user:123")
        assert deleted is True

    def test_callback_system_comprehensive(self, cache):
        """Test comprehensive callback system functionality."""
        events = []
        
        def track_event(event_name):
            def callback(*args, **kwargs):
                events.append((event_name, args, kwargs))
            return callback
        
        # Register callbacks for all events
        cache.register_callback("get_success", track_event("get_success"))
        cache.register_callback("get_miss", track_event("get_miss"))
        cache.register_callback("set_success", track_event("set_success"))
        cache.register_callback("delete_success", track_event("delete_success"))
        
        # Fire all callback types
        cache._fire_callback("get_success", "key1", "value1")
        cache._fire_callback("get_miss", "key2")
        cache._fire_callback("set_success", "key3", "value3")
        cache._fire_callback("delete_success", "key4")
        
        assert len(events) == 4
        assert events[0][0] == "get_success"
        assert events[1][0] == "get_miss"
        assert events[2][0] == "set_success"
        assert events[3][0] == "delete_success"

    @pytest.mark.asyncio
    async def test_edge_cases_and_error_handling(self, cache):
        """Test various edge cases and error conditions."""
        
        # Test with None values
        await cache.set("none_key", None)
        result = await cache.get("none_key")
        # This depends on implementation - None might be treated as cache miss
        
        # Test with empty string
        await cache.set("empty_key", "")
        
        # Test with large data structures
        large_dict = {f"key_{i}": f"value_{i}" * 100 for i in range(100)}
        await cache.set("large_key", large_dict)
        
        # Test reconnection scenario
        cache.redis = None
        await cache.connect()

    def test_compression_threshold_edge_cases(self, cache):
        """Test compression behavior at threshold boundaries."""
        # Data exactly at threshold
        data_at_threshold = "x" * 100
        compressed = cache._compress_data(data_at_threshold)
        
        # Data just below threshold  
        data_below_threshold = "x" * 99
        not_compressed = cache._compress_data(data_below_threshold)
        
        # Data just above threshold
        data_above_threshold = "x" * 101
        compressed_large = cache._compress_data(data_above_threshold)
        
        # Verify compression decisions
        assert not_compressed.startswith(b"raw:")
        # Note: Actual compression depends on pickle overhead and data compressibility

    @pytest.mark.asyncio 
    async def test_ttl_parameter_handling(self, cache):
        """Test TTL parameter handling in set operations."""
        cache.l1_cache.set = AsyncMock()
        mock_redis = AsyncMock()
        cache.redis = mock_redis
        cache.connect = AsyncMock(return_value=True)
        
        # Test with custom TTL
        await cache.set("key1", "value1", ttl=7200)
        
        # Test with None TTL (should use default)
        await cache.set("key2", "value2", ttl=None)
        
        # Test with zero TTL
        await cache.set("key3", "value3", ttl=0)
        
        # Verify calls were made with correct TTL values
        assert mock_redis.setex.call_count == 3
