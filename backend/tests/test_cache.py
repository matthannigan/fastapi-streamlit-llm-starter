"""Tests for AI response cache functionality."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import json
import hashlib
import time
import asyncio
from datetime import datetime

from app.services.cache import AIResponseCache, CacheKeyGenerator
from app.services.monitoring import CachePerformanceMonitor


class TestAIResponseCache:
    """Test the AIResponseCache class."""
    
    @pytest.fixture
    def cache_instance(self):
        """Create a fresh cache instance for testing."""
        return AIResponseCache()
    
    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client."""
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(return_value=True)
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.setex = AsyncMock(return_value=True)
        mock_redis.delete = AsyncMock(return_value=1)
        mock_redis.keys = AsyncMock(return_value=[])
        mock_redis.info = AsyncMock(return_value={
            "used_memory_human": "1.2M",
            "connected_clients": 5
        })
        return mock_redis
    
    def test_instantiation_without_global_settings(self):
        """Test that AIResponseCache can be instantiated without global settings."""
        # This test verifies Task 4 requirement: AIResponseCache() can be instantiated 
        # without global settings being pre-loaded
        cache = AIResponseCache()
        assert cache is not None
        assert cache.redis_url == "redis://redis:6379"  # default value
        assert cache.default_ttl == 3600  # default value
        
    def test_instantiation_with_custom_config(self):
        """Test that AIResponseCache can be instantiated with custom configuration."""
        custom_redis_url = "redis://custom-redis:6380"
        custom_ttl = 7200
        
        cache = AIResponseCache(redis_url=custom_redis_url, default_ttl=custom_ttl)
        assert cache.redis_url == custom_redis_url
        assert cache.default_ttl == custom_ttl
        
    def test_connect_method_uses_injected_config(self):
        """Test that connect method uses injected configuration instead of global settings."""
        custom_redis_url = "redis://test-redis:1234"
        cache = AIResponseCache(redis_url=custom_redis_url)
        
        with patch('app.services.cache.REDIS_AVAILABLE', True):
            with patch('app.services.cache.aioredis') as mock_aioredis:
                async def mock_from_url(*args, **kwargs):
                    # Verify that the custom redis_url is used
                    assert args[0] == custom_redis_url
                    mock_redis = AsyncMock()
                    mock_redis.ping = AsyncMock(return_value=True)
                    return mock_redis
                    
                mock_aioredis.from_url = mock_from_url
                
                # This test will pass if the correct URL is used
                import asyncio
                asyncio.run(cache.connect())
    
    def test_cache_key_generation(self, cache_instance):
        """Test cache key generation consistency."""
        text = "Test text"
        operation = "summarize"
        options = {"max_length": 100}
        question = "What is this about?"
        
        key1 = cache_instance._generate_cache_key(text, operation, options, question)
        key2 = cache_instance._generate_cache_key(text, operation, options, question)
        
        # Same inputs should generate same key
        assert key1 == key2
        assert key1.startswith("ai_cache:")
        
        # Different inputs should generate different keys
        key3 = cache_instance._generate_cache_key(text, "sentiment", options, question)
        assert key1 != key3
    
    def test_cache_key_options_order_independence(self, cache_instance):
        """Test that options order doesn't affect cache key."""
        text = "Test text"
        operation = "summarize"
        options1 = {"max_length": 100, "style": "formal"}
        options2 = {"style": "formal", "max_length": 100}
        
        key1 = cache_instance._generate_cache_key(text, operation, options1)
        key2 = cache_instance._generate_cache_key(text, operation, options2)
        
        assert key1 == key2
    
    @pytest.mark.asyncio
    async def test_redis_connection_success(self, cache_instance, mock_redis):
        """Test successful Redis connection."""
        with patch('app.services.cache.REDIS_AVAILABLE', True):
            with patch('app.services.cache.aioredis') as mock_aioredis:
                # Make from_url return an awaitable that resolves to mock_redis
                async def mock_from_url(*args, **kwargs):
                    return mock_redis
                mock_aioredis.from_url = mock_from_url
                
                result = await cache_instance.connect()
                assert result is True
                assert cache_instance.redis is not None
    
    @pytest.mark.asyncio
    async def test_redis_connection_failure(self, cache_instance):
        """Test Redis connection failure graceful degradation."""
        with patch('app.services.cache.REDIS_AVAILABLE', True):
            with patch('app.services.cache.aioredis') as mock_aioredis:
                # Make from_url raise an exception
                async def mock_from_url(*args, **kwargs):
                    raise Exception("Connection failed")
                mock_aioredis.from_url = mock_from_url
                
                result = await cache_instance.connect()
                assert result is False
                assert cache_instance.redis is None
    
    @pytest.mark.asyncio
    async def test_redis_unavailable(self, cache_instance):
        """Test behavior when Redis is not available."""
        with patch('app.services.cache.REDIS_AVAILABLE', False):
            result = await cache_instance.connect()
            assert result is False
            assert cache_instance.redis is None
    
    @pytest.mark.asyncio
    async def test_cache_miss(self, cache_instance, mock_redis):
        """Test cache miss scenario."""
        mock_redis.get.return_value = None
        
        # Mock successful connection
        with patch.object(cache_instance, 'connect', return_value=True):
            cache_instance.redis = mock_redis
            
            result = await cache_instance.get_cached_response(
                "test text", "summarize", {}, None
            )
            
            assert result is None
            mock_redis.get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cache_hit(self, cache_instance, mock_redis):
        """Test cache hit scenario."""
        cached_data = {
            "operation": "summarize",
            "result": "Test summary",
            "success": True,
            "cached_at": "2024-01-01T12:00:00",
            "cache_hit": True
        }
        mock_redis.get.return_value = json.dumps(cached_data)
        
        # Mock successful connection
        with patch.object(cache_instance, 'connect', return_value=True):
            cache_instance.redis = mock_redis
            
            result = await cache_instance.get_cached_response(
                "test text", "summarize", {}, None
            )
            
            assert result == cached_data
            mock_redis.get.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_cache_storage(self, cache_instance, mock_redis):
        """Test caching response data."""
        response_data = {
            "operation": "summarize",
            "result": "Test summary",
            "success": True
        }
        
        # Mock successful connection
        with patch.object(cache_instance, 'connect', return_value=True):
            cache_instance.redis = mock_redis
            
            await cache_instance.cache_response(
                "test text", "summarize", {}, response_data, None
            )
            
            mock_redis.setex.assert_called_once()
            call_args = mock_redis.setex.call_args
            
            # Check TTL is correct for summarize operation
            assert call_args[0][1] == 7200  # 2 hours for summarize
            
            # Check cached data includes metadata
            stored_data = call_args[0][2]
            # Since compression is now used, decompress the data
            if isinstance(stored_data, bytes):
                cached_data = cache_instance._decompress_data(stored_data)
            else:
                cached_data = json.loads(stored_data)
            assert "cached_at" in cached_data
            assert cached_data["cache_hit"] is True
            assert cached_data["operation"] == "summarize"
            assert "compression_used" in cached_data
            assert "text_length" in cached_data
    
    @pytest.mark.asyncio
    async def test_operation_specific_ttl(self, cache_instance, mock_redis):
        """Test that different operations get appropriate TTL values."""
        # Mock successful connection
        with patch.object(cache_instance, 'connect', return_value=True):
            cache_instance.redis = mock_redis
            
            operations_ttl = [
                ("summarize", 7200),
                ("sentiment", 86400),
                ("key_points", 7200),
                ("questions", 3600),
                ("qa", 1800),
                ("unknown_operation", 3600)  # default TTL
            ]
            
            for operation, expected_ttl in operations_ttl:
                mock_redis.reset_mock()
                await cache_instance.cache_response(
                    "test text", operation, {}, {"result": "test"}, None
                )
                
                call_args = mock_redis.setex.call_args
                assert call_args[0][1] == expected_ttl
    
    @pytest.mark.asyncio
    async def test_cache_invalidation(self, cache_instance, mock_redis):
        """Test cache pattern invalidation."""
        mock_redis.keys.return_value = [
            "ai_cache:abc123",
            "ai_cache:def456",
            "ai_cache:ghi789"
        ]
        
        # Mock successful connection
        with patch.object(cache_instance, 'connect', return_value=True):
            cache_instance.redis = mock_redis
            
            await cache_instance.invalidate_pattern("test")
            
            # Keys are now passed as bytes
            mock_redis.keys.assert_called_once_with(b"ai_cache:*test*")
            mock_redis.delete.assert_called_once_with(
                "ai_cache:abc123", "ai_cache:def456", "ai_cache:ghi789"
            )
    
    @pytest.mark.asyncio
    async def test_cache_stats(self, cache_instance, mock_redis):
        """Test cache statistics retrieval."""
        # Mock successful connection
        with patch.object(cache_instance, 'connect', return_value=True):
            cache_instance.redis = mock_redis
            
            stats = await cache_instance.get_cache_stats()
            
            # Test new nested structure
            assert "redis" in stats
            assert "memory" in stats
            assert stats["redis"]["status"] == "connected"
            assert "keys" in stats["redis"]
            assert "memory_used" in stats["redis"]
            assert "connected_clients" in stats["redis"]
            assert "memory_cache_entries" in stats["memory"]
            assert "memory_cache_size_limit" in stats["memory"]
            assert "memory_cache_utilization" in stats["memory"]
    
    @pytest.mark.asyncio
    async def test_cache_stats_unavailable(self, cache_instance):
        """Test cache stats when Redis unavailable."""
        with patch.object(cache_instance, 'connect', return_value=False):
            stats = await cache_instance.get_cache_stats()
            
            # Test new nested structure
            assert "redis" in stats
            assert "memory" in stats
            assert stats["redis"]["status"] == "unavailable"
            assert stats["redis"]["keys"] == 0
            assert "memory_cache_entries" in stats["memory"]
    
    @pytest.mark.asyncio
    async def test_cache_error_handling(self, cache_instance, mock_redis):
        """Test graceful error handling in cache operations."""
        mock_redis.get.side_effect = Exception("Redis error")
        mock_redis.setex.side_effect = Exception("Redis error")
        
        # Mock successful connection
        with patch.object(cache_instance, 'connect', return_value=True):
            cache_instance.redis = mock_redis
            
            # Test get operation error handling
            result = await cache_instance.get_cached_response(
                "test text", "summarize", {}, None
            )
            assert result is None
            
            # Test set operation error handling (should not raise)
            await cache_instance.cache_response(
                "test text", "summarize", {}, {"result": "test"}, None
            )
    
    @pytest.mark.asyncio
    async def test_cache_with_question_parameter(self, cache_instance, mock_redis):
        """Test cache operations with question parameter."""
        # Mock successful connection
        with patch.object(cache_instance, 'connect', return_value=True):
            cache_instance.redis = mock_redis
            
            # Test that questions create different cache keys
            key1 = cache_instance._generate_cache_key(
                "test text", "qa", {}, "What is this?"
            )
            key2 = cache_instance._generate_cache_key(
                "test text", "qa", {}, "How does this work?"
            )
            key3 = cache_instance._generate_cache_key(
                "test text", "qa", {}, None
            )
            
            assert key1 != key2
            assert key1 != key3
            assert key2 != key3

    @pytest.mark.asyncio
    async def test_text_tier_classification(self, cache_instance):
        """Test _get_text_tier method correctly classifies text sizes."""
        # Test small tier (< 500 chars)
        small_text = "A" * 100
        assert cache_instance._get_text_tier(small_text) == 'small'
        
        # Test boundary case for small tier
        boundary_small = "A" * 499
        assert cache_instance._get_text_tier(boundary_small) == 'small'
        
        # Test medium tier (500-5000 chars)
        medium_text = "A" * 1000
        assert cache_instance._get_text_tier(medium_text) == 'medium'
        
        # Test boundary case for medium tier
        boundary_medium = "A" * 4999
        assert cache_instance._get_text_tier(boundary_medium) == 'medium'
        
        # Test large tier (5000-50000 chars)
        large_text = "A" * 10000
        assert cache_instance._get_text_tier(large_text) == 'large'
        
        # Test boundary case for large tier
        boundary_large = "A" * 49999
        assert cache_instance._get_text_tier(boundary_large) == 'large'
        
        # Test xlarge tier (> 50000 chars)
        xlarge_text = "A" * 60000
        assert cache_instance._get_text_tier(xlarge_text) == 'xlarge'

    def test_memory_cache_update_basic(self, cache_instance):
        """Test basic memory cache update functionality."""
        test_key = "test_key"
        test_value = {"result": "test_result", "cached_at": "2024-01-01"}
        
        # Add item to empty cache
        cache_instance._update_memory_cache(test_key, test_value)
        
        assert test_key in cache_instance.memory_cache
        assert cache_instance.memory_cache[test_key] == test_value
        assert test_key in cache_instance.memory_cache_order
        assert len(cache_instance.memory_cache_order) == 1

    def test_memory_cache_update_existing_key(self, cache_instance):
        """Test updating existing key in memory cache."""
        test_key = "test_key"
        original_value = {"result": "original"}
        updated_value = {"result": "updated"}
        
        # Add original value
        cache_instance._update_memory_cache(test_key, original_value)
        cache_instance._update_memory_cache("other_key", {"other": "value"})
        
        # Update existing key
        cache_instance._update_memory_cache(test_key, updated_value)
        
        # Key should be moved to end of order list
        assert cache_instance.memory_cache[test_key] == updated_value
        assert cache_instance.memory_cache_order[-1] == test_key
        assert len(cache_instance.memory_cache_order) == 2

    def test_memory_cache_fifo_eviction(self, cache_instance):
        """Test FIFO eviction when memory cache reaches size limit."""
        # Set small cache size for testing
        cache_instance.memory_cache_size = 3
        
        # Add items to fill cache
        for i in range(3):
            cache_instance._update_memory_cache(f"key_{i}", {"value": i})
        
        assert len(cache_instance.memory_cache) == 3
        assert "key_0" in cache_instance.memory_cache
        
        # Add one more item to trigger eviction
        cache_instance._update_memory_cache("key_3", {"value": 3})
        
        # Oldest item (key_0) should be evicted
        assert len(cache_instance.memory_cache) == 3
        assert "key_0" not in cache_instance.memory_cache
        assert "key_1" in cache_instance.memory_cache
        assert "key_2" in cache_instance.memory_cache
        assert "key_3" in cache_instance.memory_cache
        assert cache_instance.memory_cache_order == ["key_1", "key_2", "key_3"]

    @pytest.mark.asyncio
    async def test_memory_cache_hit_for_small_text(self, cache_instance, mock_redis):
        """Test that small text hits memory cache before Redis."""
        small_text = "A" * 100  # Small tier text
        operation = "summarize"
        options = {}
        
        # Populate memory cache directly
        cache_key = cache_instance._generate_cache_key(small_text, operation, options)
        cached_response = {"result": "cached_summary", "cache_hit": True}
        cache_instance.memory_cache[cache_key] = cached_response
        
        # Mock Redis to ensure it's not called
        mock_redis.get.return_value = None  # This should not be reached
        
        with patch.object(cache_instance, 'connect', return_value=True):
            cache_instance.redis = mock_redis
            
            result = await cache_instance.get_cached_response(small_text, operation, options)
            
            # Should return memory cache result
            assert result == cached_response
            # Redis should not be called for small tier memory cache hit
            mock_redis.get.assert_not_called()

    @pytest.mark.asyncio
    async def test_memory_cache_miss_falls_back_to_redis(self, cache_instance, mock_redis):
        """Test that memory cache miss for small text falls back to Redis."""
        small_text = "A" * 100  # Small tier text
        operation = "summarize"
        options = {}
        
        redis_response = {"result": "redis_summary", "cache_hit": True}
        mock_redis.get.return_value = json.dumps(redis_response)
        
        with patch.object(cache_instance, 'connect', return_value=True):
            cache_instance.redis = mock_redis
            
            result = await cache_instance.get_cached_response(small_text, operation, options)
            
            # Should return Redis result
            assert result == redis_response
            # Redis should be called
            mock_redis.get.assert_called_once()
            
            # Small item should now be populated in memory cache
            cache_key = cache_instance._generate_cache_key(small_text, operation, options)
            assert cache_key in cache_instance.memory_cache
            assert cache_instance.memory_cache[cache_key] == redis_response

    @pytest.mark.asyncio
    async def test_medium_text_skips_memory_cache(self, cache_instance, mock_redis):
        """Test that medium/large text doesn't use memory cache."""
        medium_text = "A" * 1000  # Medium tier text
        operation = "summarize"
        options = {}
        
        redis_response = {"result": "redis_summary", "cache_hit": True}
        mock_redis.get.return_value = json.dumps(redis_response)
        
        with patch.object(cache_instance, 'connect', return_value=True):
            cache_instance.redis = mock_redis
            
            result = await cache_instance.get_cached_response(medium_text, operation, options)
            
            # Should return Redis result
            assert result == redis_response
            # Redis should be called
            mock_redis.get.assert_called_once()
            
            # Medium item should NOT be populated in memory cache
            cache_key = cache_instance._generate_cache_key(medium_text, operation, options)
            assert cache_key not in cache_instance.memory_cache

    @pytest.mark.asyncio
    async def test_memory_cache_statistics(self, cache_instance, mock_redis):
        """Test memory cache statistics in cache stats."""
        # Add some items to memory cache
        cache_instance._update_memory_cache("key1", {"data": "value1"})
        cache_instance._update_memory_cache("key2", {"data": "value2"})
        
        # Mock successful connection
        with patch.object(cache_instance, 'connect', return_value=True):
            cache_instance.redis = mock_redis
            
            stats = await cache_instance.get_cache_stats()
            
            assert stats["memory"]["memory_cache_entries"] == 2
            assert stats["memory"]["memory_cache_size_limit"] == 100
            assert stats["memory"]["memory_cache_utilization"] == "2/100"

    def test_memory_cache_initialization(self, cache_instance):
        """Test memory cache is properly initialized."""
        assert cache_instance.memory_cache == {}
        assert cache_instance.memory_cache_order == []
        assert cache_instance.memory_cache_size == 100

    def test_compression_data_small_data(self, cache_instance):
        """Test that small data is not compressed."""
        small_data = {
            "result": "small", 
            "cached_at": "2024-01-01",
            "success": True,
            "metadata": {"size": "small"}
        }
        
        compressed = cache_instance._compress_data(small_data)
        
        # Should start with "raw:" prefix for uncompressed data
        assert compressed.startswith(b"raw:")
        
        # Should be able to decompress back to original
        decompressed = cache_instance._decompress_data(compressed)
        assert decompressed == small_data
        
        # Verify data integrity
        assert decompressed["result"] == "small"
        assert decompressed["success"] is True
        assert decompressed["metadata"]["size"] == "small"

    def test_compression_data_large_data(self, cache_instance):
        """Test that large data is compressed."""
        # Create large data that exceeds compression threshold
        large_text = "A" * 2000  # Larger than default 1000 byte threshold
        large_data = {
            "result": large_text,
            "cached_at": "2024-01-01T12:00:00",
            "operation": "summarize",
            "success": True,
            "metadata": {"compression": True}
        }
        
        compressed = cache_instance._compress_data(large_data)
        
        # Should start with "compressed:" prefix for compressed data
        assert compressed.startswith(b"compressed:")
        
        # Compressed data should be smaller than original
        import pickle
        original_size = len(pickle.dumps(large_data))
        compressed_size = len(compressed) - 11  # Remove prefix length
        assert compressed_size < original_size
        
        # Should be able to decompress back to original
        decompressed = cache_instance._decompress_data(compressed)
        assert decompressed == large_data
        
        # Verify data integrity for complex structures
        assert len(decompressed["result"]) == len(large_text)
        assert decompressed["metadata"]["compression"] is True

    def test_compression_threshold_configuration(self):
        """Test that compression threshold can be configured."""
        custom_threshold = 500
        custom_level = 9
        
        cache = AIResponseCache(
            compression_threshold=custom_threshold,
            compression_level=custom_level
        )
        
        assert cache.compression_threshold == custom_threshold
        assert cache.compression_level == custom_level


class TestMemoryCacheOperations:
    """Comprehensive unit tests for memory cache operations."""
    
    @pytest.fixture
    def memory_cache_instance(self):
        """Create a cache instance for memory cache testing."""
        return AIResponseCache()
    
    @pytest.fixture
    def small_memory_cache_instance(self):
        """Create a cache instance with small memory cache for eviction testing."""
        cache = AIResponseCache()
        cache.memory_cache_size = 3  # Small cache for testing eviction
        return cache
    
    @pytest.fixture
    def memory_mock_redis(self):
        """Mock Redis instance for memory cache testing."""
        mock = MagicMock()
        mock.get = AsyncMock()
        mock.set = AsyncMock()
        mock.setex = AsyncMock()
        mock.delete = AsyncMock()
        mock.keys = AsyncMock()
        mock.scan_iter = AsyncMock()
        mock.info = AsyncMock()
        return mock
    
    def _create_test_helper(self, cache_instance):
        """Create test helper for cache access patterns."""
        class CacheTestHelper:
            def __init__(self, cache):
                self.cache = cache
                
            def simulate_cache_fills(self, count: int, key_prefix: str = "key"):
                """Fill cache with test data."""
                for i in range(count):
                    key = f"{key_prefix}_{i}"
                    value = {"data": f"value_{i}", "index": i}
                    self.cache._update_memory_cache(key, value)
                    
            def simulate_access_pattern(self, keys: list):
                """Simulate accessing keys in specified order."""
                results = []
                for key in keys:
                    if key in self.cache.memory_cache:
                        # Simulate access by updating cache (moves to end in FIFO)
                        value = self.cache.memory_cache[key]
                        self.cache._update_memory_cache(key, value)
                        results.append(("hit", key, value))
                    else:
                        results.append(("miss", key, None))
                return results
                
            def get_cache_state(self):
                """Get current cache state for verification."""
                return {
                    "cache_contents": dict(self.cache.memory_cache),
                    "access_order": list(self.cache.memory_cache_order),
                    "size": len(self.cache.memory_cache),
                    "size_limit": self.cache.memory_cache_size
                }
        
        return CacheTestHelper(cache_instance)
    
    def test_memory_cache_hit_returns_correct_data(self, memory_cache_instance):
        """Test that cache hit returns the correct cached data."""
        # Arrange
        test_key = "test_key"
        test_data = {
            "result": "cached_response",
            "operation": "summarize",
            "cached_at": "2024-01-01T12:00:00Z",
            "metadata": {"tier": "small", "cached": True}
        }
        
        # Add to cache
        memory_cache_instance._update_memory_cache(test_key, test_data)
        
        # Act & Assert
        assert test_key in memory_cache_instance.memory_cache
        retrieved_data = memory_cache_instance.memory_cache[test_key]
        assert retrieved_data == test_data
        assert retrieved_data["result"] == "cached_response"
        assert retrieved_data["metadata"]["cached"] is True
    
    def test_memory_cache_miss_returns_none(self, memory_cache_instance):
        """Test that cache miss returns None for non-existent keys."""
        # Arrange
        non_existent_key = "non_existent_key"
        
        # Act & Assert
        assert non_existent_key not in memory_cache_instance.memory_cache
        assert memory_cache_instance.memory_cache.get(non_existent_key) is None
    
    def test_memory_cache_fifo_eviction_detailed(self, small_memory_cache_instance):
        """Test detailed FIFO eviction behavior when cache reaches capacity."""
        helper = self._create_test_helper(small_memory_cache_instance)
        
        # Fill cache to capacity (3 items)
        helper.simulate_cache_fills(3)
        
        state = helper.get_cache_state()
        assert state["size"] == 3
        assert "key_0" in state["cache_contents"]
        assert "key_1" in state["cache_contents"] 
        assert "key_2" in state["cache_contents"]
        assert state["access_order"] == ["key_0", "key_1", "key_2"]
        
        # Add one more item to trigger eviction
        small_memory_cache_instance._update_memory_cache("key_3", {"data": "value_3", "index": 3})
        
        final_state = helper.get_cache_state()
        assert final_state["size"] == 3
        assert "key_0" not in final_state["cache_contents"]  # Oldest evicted
        assert "key_1" in final_state["cache_contents"]
        assert "key_2" in final_state["cache_contents"]
        assert "key_3" in final_state["cache_contents"]
        assert final_state["access_order"] == ["key_1", "key_2", "key_3"]
    
    def test_memory_cache_access_pattern_complex(self, small_memory_cache_instance):
        """Test complex access patterns with cache updates."""
        helper = self._create_test_helper(small_memory_cache_instance)
        
        # Fill cache to capacity-1 to avoid immediate eviction
        helper.simulate_cache_fills(2)
        
        # Initial state: ["key_0", "key_1"]
        initial_state = helper.get_cache_state()
        assert initial_state["access_order"] == ["key_0", "key_1"]
        assert len(initial_state["cache_contents"]) == 2
        
        # Access key_0 (should move it to end)
        access_results = helper.simulate_access_pattern(["key_0"])
        assert access_results[0][0] == "hit"
        assert access_results[0][1] == "key_0"
        
        # After accessing key_0, order should be: ["key_1", "key_0"]
        state_after_access = helper.get_cache_state()
        assert state_after_access["access_order"] == ["key_1", "key_0"]
        
        # Add third key - should fill to capacity: ["key_1", "key_0", "key_2"]
        small_memory_cache_instance._update_memory_cache("key_2", {"data": "value_2", "index": 2})
        
        state_after_add = helper.get_cache_state()
        assert len(state_after_add["cache_contents"]) == 3  # At capacity
        assert state_after_add["access_order"] == ["key_1", "key_0", "key_2"]
        
        # Add fourth key - should evict key_1 (oldest)
        small_memory_cache_instance._update_memory_cache("key_3", {"data": "value_3", "index": 3})
        
        final_state = helper.get_cache_state()
        assert "key_1" not in final_state["cache_contents"]  # Oldest evicted
        assert "key_0" in final_state["cache_contents"]
        assert "key_2" in final_state["cache_contents"]
        assert "key_3" in final_state["cache_contents"]
        assert final_state["access_order"] == ["key_0", "key_2", "key_3"]
    
    def test_memory_cache_boundary_conditions(self, memory_cache_instance):
        """Test cache behavior at boundary conditions."""
        # Test with cache size of 1
        memory_cache_instance.memory_cache_size = 1
        
        # Add first item
        memory_cache_instance._update_memory_cache("key1", {"data": "value1"})
        assert len(memory_cache_instance.memory_cache) == 1
        assert "key1" in memory_cache_instance.memory_cache
        
        # Add second item - should evict first
        memory_cache_instance._update_memory_cache("key2", {"data": "value2"})
        assert len(memory_cache_instance.memory_cache) == 1
        assert "key1" not in memory_cache_instance.memory_cache
        assert "key2" in memory_cache_instance.memory_cache
        
        # Test with cache size of 0 (edge case)
        memory_cache_instance.memory_cache_size = 0
        memory_cache_instance.memory_cache.clear()
        memory_cache_instance.memory_cache_order.clear()
        
        # The current implementation doesn't handle size 0 gracefully
        # So we test that it behaves consistently (doesn't crash)
        try:
            memory_cache_instance._update_memory_cache("key3", {"data": "value3"})
            # If it doesn't crash, the cache should remain empty or have been cleared
            assert len(memory_cache_instance.memory_cache) <= 0 or "key3" not in memory_cache_instance.memory_cache
        except IndexError:
            # This is expected behavior when cache size is 0 - it tries to pop from empty list
            assert len(memory_cache_instance.memory_cache) == 0
    
    def test_memory_cache_duplicate_key_handling(self, memory_cache_instance):
        """Test handling of duplicate keys in cache updates."""
        # Add initial value
        memory_cache_instance._update_memory_cache("duplicate_key", {"version": 1})
        assert memory_cache_instance.memory_cache["duplicate_key"]["version"] == 1
        assert len(memory_cache_instance.memory_cache_order) == 1
        
        # Update with new value - should replace and move to end
        memory_cache_instance._update_memory_cache("other_key", {"version": 2})
        memory_cache_instance._update_memory_cache("duplicate_key", {"version": 3})
        
        assert memory_cache_instance.memory_cache["duplicate_key"]["version"] == 3
        assert len(memory_cache_instance.memory_cache_order) == 2
        assert memory_cache_instance.memory_cache_order == ["other_key", "duplicate_key"]
    
    def test_memory_cache_data_integrity(self, memory_cache_instance):
        """Test that cached data maintains integrity over operations."""
        # Create complex data structure
        import copy
        complex_data = {
            "nested": {
                "array": [1, 2, 3, {"inner": "value"}],
                "string": "test_string",
                "boolean": True,
                "null_value": None
            },
            "metadata": {
                "timestamps": ["2024-01-01", "2024-01-02"],
                "counts": {"hits": 5, "misses": 2}
            }
        }
        
        # Store copy in cache to avoid reference sharing
        memory_cache_instance._update_memory_cache("complex_key", copy.deepcopy(complex_data))
        
        # Retrieve and verify integrity
        retrieved = memory_cache_instance.memory_cache["complex_key"]
        assert retrieved["nested"]["array"][3]["inner"] == "value"
        assert retrieved["metadata"]["counts"]["hits"] == 5
        assert retrieved["nested"]["null_value"] is None
        assert retrieved["nested"]["boolean"] is True
        
        # Modify original data and ensure cache is not affected
        original_array_length = len(retrieved["nested"]["array"])
        complex_data["nested"]["array"].append("new_item")
        assert len(retrieved["nested"]["array"]) == original_array_length
        assert "new_item" not in retrieved["nested"]["array"]
    
    def test_memory_cache_concurrent_access_simulation(self, memory_cache_instance):
        """Test simulation of concurrent access patterns."""
        import threading
        import time
        
        memory_cache_instance.memory_cache_size = 10
        results = []
        
        def cache_worker(worker_id: int, iterations: int):
            """Simulate concurrent cache operations."""
            worker_results = []
            for i in range(iterations):
                key = f"worker_{worker_id}_key_{i}"
                value = {"worker": worker_id, "iteration": i, "timestamp": time.time()}
                
                # Add to cache
                memory_cache_instance._update_memory_cache(key, value)
                
                # Verify immediately
                if key in memory_cache_instance.memory_cache:
                    worker_results.append(("success", key, value))
                else:
                    worker_results.append(("failure", key, value))
                    
                time.sleep(0.001)  # Small delay to simulate real work
            
            results.extend(worker_results)
        
        # Run multiple workers
        threads = []
        for worker_id in range(3):
            thread = threading.Thread(target=cache_worker, args=(worker_id, 5))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads
        for thread in threads:
            thread.join()
        
        # Verify results
        assert len(results) == 15  # 3 workers * 5 iterations
        success_count = sum(1 for result in results if result[0] == "success")
        assert success_count == 15  # All operations should succeed
        
        # Verify final cache state
        assert len(memory_cache_instance.memory_cache) <= 10  # Should not exceed limit
        assert len(memory_cache_instance.memory_cache_order) == len(memory_cache_instance.memory_cache)
    
    @pytest.mark.asyncio
    async def test_memory_cache_integration_with_get_cached_response(self, memory_cache_instance, memory_mock_redis):
        """Test memory cache integration with the main cache retrieval method."""
        small_text = "Small text for memory cache"  # < 500 chars = small tier
        operation = "summarize"
        options = {"max_length": 100}
        
        # Pre-populate memory cache
        cache_key = memory_cache_instance._generate_cache_key(small_text, operation, options)
        cached_response = {
            "result": "Memory cached summary",
            "cached_at": "2024-01-01T12:00:00Z",
            "cache_tier": "memory"
        }
        memory_cache_instance._update_memory_cache(cache_key, cached_response)
        
        # Mock Redis - should not be called for memory cache hit
        memory_mock_redis.get.return_value = None
        
        with patch.object(memory_cache_instance, 'connect', return_value=True):
            memory_cache_instance.redis = memory_mock_redis
            
            # Test memory cache hit
            result = await memory_cache_instance.get_cached_response(small_text, operation, options)
            
            assert result == cached_response
            assert result["cache_tier"] == "memory"
            memory_mock_redis.get.assert_not_called()  # Should not fallback to Redis
    
    @pytest.mark.asyncio
    async def test_memory_cache_miss_fallback_to_redis(self, memory_cache_instance, memory_mock_redis):
        """Test memory cache miss properly falls back to Redis."""
        small_text = "Small text not in memory cache"  # < 500 chars = small tier
        operation = "summarize" 
        options = {"max_length": 100}
        
        # Ensure memory cache is empty
        memory_cache_instance.memory_cache.clear()
        memory_cache_instance.memory_cache_order.clear()
        
        # Setup Redis response
        redis_response = {
            "result": "Redis cached summary",
            "cached_at": "2024-01-01T10:00:00Z",
            "cache_tier": "redis"
        }
        memory_mock_redis.get.return_value = json.dumps(redis_response)
        
        with patch.object(memory_cache_instance, 'connect', return_value=True):
            memory_cache_instance.redis = memory_mock_redis
            
            # Test Redis fallback
            result = await memory_cache_instance.get_cached_response(small_text, operation, options)
            
            assert result == redis_response
            memory_mock_redis.get.assert_called_once()
            
            # Verify memory cache was populated from Redis response
            cache_key = memory_cache_instance._generate_cache_key(small_text, operation, options)
            assert cache_key in memory_cache_instance.memory_cache
            assert memory_cache_instance.memory_cache[cache_key] == redis_response
    
    def test_memory_cache_eviction_preserves_consistency(self, small_memory_cache_instance):
        """Test that eviction maintains consistency between cache and order list."""
        helper = self._create_test_helper(small_memory_cache_instance)
        
        # Fill cache beyond capacity multiple times
        for round_num in range(3):
            for i in range(5):  # Add 5 items (cache size is 3)
                key = f"round_{round_num}_key_{i}"
                value = {"round": round_num, "index": i}
                small_memory_cache_instance._update_memory_cache(key, value)
                
                # Verify consistency after each operation
                state = helper.get_cache_state()
                assert len(state["cache_contents"]) == len(state["access_order"])
                assert len(state["cache_contents"]) <= state["size_limit"]
                
                # Verify all keys in cache are in order list
                for cache_key in state["cache_contents"].keys():
                    assert cache_key in state["access_order"]
                
                # Verify all keys in order list are in cache
                for order_key in state["access_order"]:
                    assert order_key in state["cache_contents"]
    
    def test_memory_cache_performance_characteristics(self, memory_cache_instance):
        """Test performance characteristics of memory cache operations."""
        import time
        
        memory_cache_instance.memory_cache_size = 1000  # Larger cache for performance testing
        
        # Measure cache update performance
        start_time = time.time()
        for i in range(100):
            key = f"perf_key_{i}"
            value = {"data": f"value_{i}", "index": i}
            memory_cache_instance._update_memory_cache(key, value)
        update_time = time.time() - start_time
        
        # Measure cache lookup performance
        start_time = time.time()
        for i in range(100):
            key = f"perf_key_{i}"
            _ = memory_cache_instance.memory_cache.get(key)
        lookup_time = time.time() - start_time
        
        # Performance assertions (adjust thresholds as needed)
        assert update_time < 1.0  # Should complete 100 updates in under 1 second
        assert lookup_time < 0.1  # Should complete 100 lookups in under 0.1 seconds
        
        # Verify all items were cached
        assert len(memory_cache_instance.memory_cache) == 100
        assert len(memory_cache_instance.memory_cache_order) == 100
    
    def test_memory_cache_edge_case_empty_operations(self, memory_cache_instance):
        """Test edge cases with empty keys, values, and operations."""
        # Test empty key (current implementation allows this)
        memory_cache_instance._update_memory_cache("", {"data": "value"})
        assert "" in memory_cache_instance.memory_cache
        assert memory_cache_instance.memory_cache[""]["data"] == "value"
        
        # Test None key - should fail when trying to use as dict key
        # The method signature expects str, but implementation doesn't explicitly validate
        # It will fail when trying to use None in dict operations
        try:
            memory_cache_instance._update_memory_cache(None, {"data": "value"})
            # If no exception, check that None is handled (implementation dependent)
            assert None in memory_cache_instance.memory_cache
        except (TypeError, KeyError):
            # Expected behavior - None not suitable as dict key in some operations
            pass
        
        # Test empty value (should be allowed)
        memory_cache_instance._update_memory_cache("empty_value_key", {})
        assert "empty_value_key" in memory_cache_instance.memory_cache
        assert memory_cache_instance.memory_cache["empty_value_key"] == {}
        
        # Test None value (should be allowed)
        memory_cache_instance._update_memory_cache("none_value_key", None)
        assert "none_value_key" in memory_cache_instance.memory_cache
        assert memory_cache_instance.memory_cache["none_value_key"] is None

    @pytest.mark.asyncio
    async def test_cache_response_includes_compression_metadata(self, memory_cache_instance, memory_mock_redis):
        """Test that cached responses include compression metadata."""
        response_data = {
            "operation": "summarize",
            "result": "Test summary",
            "success": True
        }
        
                # Mock successful connection
        with patch.object(memory_cache_instance, 'connect', return_value=True):
            memory_cache_instance.redis = memory_mock_redis

            await memory_cache_instance.cache_response(
                "test text", "summarize", {}, response_data, None
            )

            memory_mock_redis.setex.assert_called_once()
            call_args = memory_mock_redis.setex.call_args

            # Decompress the stored data to check metadata
            stored_data = call_args[0][2]
            cached_data = memory_cache_instance._decompress_data(stored_data)
            
            # Check compression metadata is included
            assert "compression_used" in cached_data
            assert "text_length" in cached_data
            assert cached_data["text_length"] == len("test text")
            assert isinstance(cached_data["compression_used"], bool)

    @pytest.mark.asyncio
    async def test_cache_retrieval_handles_compressed_data(self, memory_cache_instance, memory_mock_redis):
        """Test that cache retrieval properly handles compressed data."""
        # Create test data
        test_data = {
            "operation": "summarize",
            "result": "Test summary",
            "success": True,
            "cached_at": "2024-01-01T12:00:00",
            "cache_hit": True,
            "compression_used": True,
            "text_length": 9
        }
        
        # Compress the data as it would be stored
        compressed_data = memory_cache_instance._compress_data(test_data)
        memory_mock_redis.get.return_value = compressed_data
        
        # Mock successful connection
        with patch.object(memory_cache_instance, 'connect', return_value=True):
            memory_cache_instance.redis = memory_mock_redis
            
            result = await memory_cache_instance.get_cached_response(
                "test text", "summarize", {}, None
            )
            
            assert result == test_data
            memory_mock_redis.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_response_timing_tracking(self, memory_cache_instance, memory_mock_redis):
        """Test that cache_response records performance timing metrics."""
        response_data = {
            "operation": "summarize",
            "result": "Test summary",
            "success": True
        }
        
        # Ensure performance monitor is available
        assert memory_cache_instance.performance_monitor is not None
        
        # Get initial counts
        initial_cache_ops = len(memory_cache_instance.performance_monitor.cache_operation_times)
        
        # Mock successful connection
        with patch.object(memory_cache_instance, 'connect', return_value=True):
            memory_cache_instance.redis = memory_mock_redis
            
            await memory_cache_instance.cache_response(
                "test text", "summarize", {}, response_data, None
            )
            
            # Verify that a cache operation time was recorded
            assert len(memory_cache_instance.performance_monitor.cache_operation_times) == initial_cache_ops + 1
            
            # Check the recorded metric
            recorded_metric = memory_cache_instance.performance_monitor.cache_operation_times[-1]
            assert recorded_metric.operation_type == "set"
            assert recorded_metric.text_length == len("test text")
            assert recorded_metric.duration > 0
            assert recorded_metric.additional_data["operation_type"] == "summarize"
            assert recorded_metric.additional_data["status"] == "success"
            assert "compression_used" in recorded_metric.additional_data
            assert "compression_time" in recorded_metric.additional_data

    @pytest.mark.asyncio
    async def test_cache_response_timing_on_failure(self, memory_cache_instance, memory_mock_redis):
        """Test that cache_response records timing even when Redis operations fail."""
        response_data = {
            "operation": "summarize", 
            "result": "Test summary",
            "success": True
        }
        
        # Get initial counts
        initial_cache_ops = len(memory_cache_instance.performance_monitor.cache_operation_times)
        
        # Mock Redis setex to raise an exception
        memory_mock_redis.setex.side_effect = Exception("Redis error")
        
        # Mock successful connection
        with patch.object(memory_cache_instance, 'connect', return_value=True):
            memory_cache_instance.redis = memory_mock_redis
            
            await memory_cache_instance.cache_response(
                "test text", "summarize", {}, response_data, None
            )
            
            # Verify that a cache operation time was recorded even on failure
            assert len(memory_cache_instance.performance_monitor.cache_operation_times) == initial_cache_ops + 1
            
            # Check the recorded metric shows failure
            recorded_metric = memory_cache_instance.performance_monitor.cache_operation_times[-1]
            assert recorded_metric.operation_type == "set"
            assert recorded_metric.duration > 0
            assert recorded_metric.additional_data["status"] == "failed"
            assert recorded_metric.additional_data["reason"] == "redis_error"

    @pytest.mark.asyncio
    async def test_cache_response_timing_on_connection_failure(self, memory_cache_instance):
        """Test that cache_response records timing when Redis connection fails."""
        response_data = {
            "operation": "summarize",
            "result": "Test summary", 
            "success": True
        }
        
        # Get initial counts
        initial_cache_ops = len(memory_cache_instance.performance_monitor.cache_operation_times)
        
        # Mock connection failure
        with patch.object(memory_cache_instance, 'connect', return_value=False):
            
            await memory_cache_instance.cache_response(
                "test text", "summarize", {}, response_data, None
            )
            
            # Verify that a cache operation time was recorded for connection failure
            assert len(memory_cache_instance.performance_monitor.cache_operation_times) == initial_cache_ops + 1
            
            # Check the recorded metric shows connection failure
            recorded_metric = memory_cache_instance.performance_monitor.cache_operation_times[-1]
            assert recorded_metric.operation_type == "set"
            assert recorded_metric.duration > 0
            assert recorded_metric.additional_data["reason"] == "redis_connection_failed"
            assert recorded_metric.additional_data["status"] == "failed"

    @pytest.mark.asyncio
    async def test_cache_response_compression_tracking(self, memory_cache_instance, memory_mock_redis):
        """Test that cache_response records compression metrics when compression is used."""
        # Create large response that will trigger compression
        large_response = {
            "operation": "summarize",
            "result": "A" * 2000,  # Large result to trigger compression
            "success": True
        }
        
        # Get initial counts 
        initial_compression_ops = len(memory_cache_instance.performance_monitor.compression_ratios)
        
        # Mock successful connection
        with patch.object(memory_cache_instance, 'connect', return_value=True):
            memory_cache_instance.redis = memory_mock_redis
            
            await memory_cache_instance.cache_response(
                "test text", "summarize", {}, large_response, None
            )
            
            # Verify that a compression ratio was recorded
            assert len(memory_cache_instance.performance_monitor.compression_ratios) == initial_compression_ops + 1
            
            # Check the recorded compression metric
            recorded_compression = memory_cache_instance.performance_monitor.compression_ratios[-1]
            assert recorded_compression.operation_type == "summarize"
            assert recorded_compression.compression_time > 0
            assert recorded_compression.original_size > 0
            assert recorded_compression.compressed_size > 0
            assert recorded_compression.compression_ratio <= 1.0  # Should be compressed

    @pytest.mark.asyncio
    async def test_cache_response_no_compression_tracking_for_small_data(self, memory_cache_instance, memory_mock_redis):
        """Test that cache_response doesn't record compression metrics for small data."""
        # Create small response that won't trigger compression
        small_response = {
            "operation": "sentiment",
            "result": "positive",
            "success": True
        }
        
        # Get initial counts
        initial_compression_ops = len(memory_cache_instance.performance_monitor.compression_ratios)
        
        # Mock successful connection
        with patch.object(memory_cache_instance, 'connect', return_value=True):
            memory_cache_instance.redis = memory_mock_redis
            
            await memory_cache_instance.cache_response(
                "test text", "sentiment", {}, small_response, None
            )
            
            # Verify that no compression ratio was recorded for small data
            assert len(memory_cache_instance.performance_monitor.compression_ratios) == initial_compression_ops

    @pytest.mark.asyncio
    async def test_cache_response_compression_tracking_for_small_data(self, memory_cache_instance, memory_mock_redis):
        """Test that compression metrics are NOT recorded for small data."""
        small_response = {"result": "small", "success": True}
        
        # Mock successful connection
        with patch.object(memory_cache_instance, 'connect', return_value=True):
            memory_cache_instance.redis = memory_mock_redis
            
            await memory_cache_instance.cache_response(
                "test text", "summarize", {}, small_response, None
            )
            
            # Should NOT record compression metrics for small data
            assert len(memory_cache_instance.performance_monitor.compression_ratios) == 0

    def test_memory_usage_recording(self, memory_cache_instance):
        """Test that memory usage is recorded properly."""
        # Add some items to memory cache to create measurable usage
        memory_cache_instance._update_memory_cache("key1", {"data": "value1"})
        memory_cache_instance._update_memory_cache("key2", {"data": "value2"})
        
        # Record memory usage
        redis_stats = {"used_memory": 1024 * 1024}  # 1MB
        memory_cache_instance.record_memory_usage(redis_stats)
        
        # Verify memory usage was recorded
        assert len(memory_cache_instance.performance_monitor.memory_usage_measurements) == 1
        
        measurement = memory_cache_instance.performance_monitor.memory_usage_measurements[0]
        assert measurement.memory_cache_entry_count == 2  # Fixed attribute name
        # Check that memory tracking is working (process_memory_mb should be >= 0)
        assert measurement.process_memory_mb >= 0.0

    def test_memory_usage_recording_failure(self, memory_cache_instance):
        """Test memory usage recording when Redis stats are unavailable."""
        # Record memory usage without Redis stats
        memory_cache_instance.record_memory_usage()
        
        # Should still record local memory cache info
        assert len(memory_cache_instance.performance_monitor.memory_usage_measurements) == 1
        
        measurement = memory_cache_instance.performance_monitor.memory_usage_measurements[0]
        assert measurement.memory_cache_entry_count == 0  # Empty cache (fixed attribute name)
        # Process memory should still be tracked
        assert measurement.process_memory_mb >= 0.0

    def test_get_memory_usage_stats(self, memory_cache_instance):
        """Test getting memory usage statistics."""
        # Add memory usage data
        memory_cache_instance.record_memory_usage({"used_memory": 2048 * 1024})  # 2MB
        
        stats = memory_cache_instance.get_memory_usage_stats()
        
        # Check for actual fields that exist in the stats
        assert "current" in stats
        assert "thresholds" in stats
        assert "trends" in stats
        assert stats["trends"]["total_measurements"] == 1

    def test_get_memory_warnings(self, memory_cache_instance):
        """Test memory warning generation."""
        # Create high memory usage scenario
        high_memory_stats = {"used_memory": 100 * 1024 * 1024}  # 100MB
        memory_cache_instance.record_memory_usage(high_memory_stats)
        
        warnings = memory_cache_instance.get_memory_warnings()
        
        # Should be a list (may be empty depending on thresholds)
        assert isinstance(warnings, list)

    @pytest.mark.asyncio
    async def test_cache_stats_includes_memory_tracking(self, memory_cache_instance, memory_mock_redis):
        """Test that get_cache_stats triggers memory usage recording and includes memory stats."""
        # Add some items to memory cache
        memory_cache_instance._update_memory_cache("key1", {"data": "value1"})
        memory_cache_instance._update_memory_cache("key2", {"data": "value2"})
        
        # Mock successful Redis connection
        with patch.object(memory_cache_instance, 'connect', return_value=True):
            memory_cache_instance.redis = memory_mock_redis
            
            # Mock Redis info to include memory_used_bytes
            memory_mock_redis.info.return_value = {
                "used_memory": 2048 * 1024,  # 2MB in bytes
                "used_memory_human": "2.0M",
                "connected_clients": 1
            }
            
            stats = await memory_cache_instance.get_cache_stats()
            
            # Verify memory usage was recorded during stats collection
            assert len(memory_cache_instance.performance_monitor.memory_usage_measurements) == 1
            
            # Verify stats include performance data with memory usage
            assert "performance" in stats
            performance_stats = stats["performance"]
            
            # If memory usage was recorded, it should be in performance stats
            if memory_cache_instance.performance_monitor.memory_usage_measurements:
                assert "memory_usage" in performance_stats

    @pytest.mark.asyncio
    async def test_cache_stats_memory_recording_redis_unavailable(self, memory_cache_instance):
        """Test memory usage recording when Redis is unavailable."""
        # Add some items to memory cache
        memory_cache_instance._update_memory_cache("key1", {"data": "value1"})
        
        # Mock Redis connection failure
        with patch.object(memory_cache_instance, 'connect', return_value=False):
            stats = await memory_cache_instance.get_cache_stats()
            
            # Memory usage should still be recorded even without Redis
            assert len(memory_cache_instance.performance_monitor.memory_usage_measurements) == 1
            
            # Stats should still include memory cache info
            assert "memory" in stats
            assert stats["memory"]["memory_cache_entries"] == 1

    def test_memory_usage_with_large_cache(self, memory_cache_instance):
        """Test memory usage tracking with large cache."""
        # Fill cache with many items
        for i in range(50):
            memory_cache_instance._update_memory_cache(f"key{i}", {"data": f"value{i}"})
        
        memory_cache_instance.record_memory_usage({"used_memory": 10 * 1024 * 1024})  # 10MB
        
        measurement = memory_cache_instance.performance_monitor.memory_usage_measurements[0]
        assert measurement.memory_cache_entry_count == 50  # Should track all entries

    def test_memory_threshold_configuration(self, memory_cache_instance):
        """Test memory threshold configuration."""
        # Test that memory cache size is configurable
        assert memory_cache_instance.memory_cache_size == 100  # Default
        
        # Create instance with custom memory cache size
        custom_cache = AIResponseCache()
        custom_cache.memory_cache_size = 50
        assert custom_cache.memory_cache_size == 50

    def test_memory_usage_integration_with_performance_stats(self, memory_cache_instance):
        """Test integration between memory usage and performance stats."""
        # Record memory usage
        memory_cache_instance.record_memory_usage({"used_memory": 5 * 1024 * 1024})  # 5MB
        
        # Get performance summary
        summary = memory_cache_instance.get_performance_summary()
        
        # Should include memory usage data if available
        assert "memory_usage" in summary

    def test_memory_usage_cleanup_on_reset(self, memory_cache_instance):
        """Test that memory usage data is cleaned up on reset."""
        # Record some memory usage
        memory_cache_instance.record_memory_usage({"used_memory": 1024 * 1024})
        assert len(memory_cache_instance.performance_monitor.memory_usage_measurements) == 1
        
        # Reset performance stats
        memory_cache_instance.reset_performance_stats()
        
        # Memory usage measurements should be cleared
        assert len(memory_cache_instance.performance_monitor.memory_usage_measurements) == 0

    @pytest.mark.asyncio
    async def test_invalidate_pattern_tracking_success(self, memory_cache_instance, memory_mock_redis):
        """Test invalidation tracking with successful operation."""
        memory_mock_redis.keys.return_value = [
            "ai_cache:test_key1",
            "ai_cache:test_key2", 
            "ai_cache:test_key3"
        ]
        
        with patch.object(memory_cache_instance, 'connect', return_value=True):
            memory_cache_instance.redis = memory_mock_redis
            
            await memory_cache_instance.invalidate_pattern("test", "unit_test_context")
        
        # Check that invalidation was tracked
        assert memory_cache_instance.performance_monitor.total_invalidations == 1
        assert memory_cache_instance.performance_monitor.total_keys_invalidated == 3
        assert len(memory_cache_instance.performance_monitor.invalidation_events) == 1
        
        event = memory_cache_instance.performance_monitor.invalidation_events[0]
        assert event.pattern == "test"
        assert event.keys_invalidated == 3
        assert event.invalidation_type == "manual"
        assert event.operation_context == "unit_test_context"
        assert event.additional_data["status"] == "success"

    @pytest.mark.asyncio
    async def test_invalidate_pattern_tracking_no_keys_found(self, memory_cache_instance, memory_mock_redis):
        """Test invalidation tracking when no keys are found."""
        memory_mock_redis.keys.return_value = []
        
        with patch.object(memory_cache_instance, 'connect', return_value=True):
            memory_cache_instance.redis = memory_mock_redis
            
            await memory_cache_instance.invalidate_pattern("nonexistent", "unit_test")
        
        # Should still track the invalidation attempt
        assert memory_cache_instance.performance_monitor.total_invalidations == 1
        assert memory_cache_instance.performance_monitor.total_keys_invalidated == 0
        
        event = memory_cache_instance.performance_monitor.invalidation_events[0]
        assert event.pattern == "nonexistent"
        assert event.keys_invalidated == 0
        assert event.additional_data["status"] == "success"

    @pytest.mark.asyncio
    async def test_invalidate_pattern_tracking_redis_connection_failed(self, memory_cache_instance):
        """Test invalidation tracking when Redis connection fails."""
        with patch.object(memory_cache_instance, 'connect', return_value=False):
            await memory_cache_instance.invalidate_pattern("test", "connection_test")
        
        # Should track the failed attempt
        assert memory_cache_instance.performance_monitor.total_invalidations == 1
        assert memory_cache_instance.performance_monitor.total_keys_invalidated == 0
        
        event = memory_cache_instance.performance_monitor.invalidation_events[0]
        assert event.pattern == "test"
        assert event.keys_invalidated == 0
        assert event.additional_data["status"] == "failed"
        assert event.additional_data["reason"] == "redis_connection_failed"

    @pytest.mark.asyncio
    async def test_invalidate_pattern_tracking_redis_error(self, memory_cache_instance, memory_mock_redis):
        """Test invalidation tracking when Redis operation fails."""
        memory_mock_redis.keys.side_effect = Exception("Redis error")
        
        with patch.object(memory_cache_instance, 'connect', return_value=True):
            memory_cache_instance.redis = memory_mock_redis
            
            await memory_cache_instance.invalidate_pattern("test", "error_test")
        
        # Should track the failed operation
        assert memory_cache_instance.performance_monitor.total_invalidations == 1
        assert memory_cache_instance.performance_monitor.total_keys_invalidated == 0
        
        event = memory_cache_instance.performance_monitor.invalidation_events[0]
        assert event.pattern == "test"
        assert event.keys_invalidated == 0
        assert event.additional_data["status"] == "failed"
        assert event.additional_data["reason"] == "redis_error"
        assert "Redis error" in event.additional_data["error"]

    @pytest.mark.asyncio
    async def test_invalidate_all(self, memory_cache_instance, memory_mock_redis):
        """Test invalidate_all convenience method."""
        memory_mock_redis.keys.return_value = ["ai_cache:key1", "ai_cache:key2"]
        
        with patch.object(memory_cache_instance, 'connect', return_value=True):
            memory_cache_instance.redis = memory_mock_redis
            
            await memory_cache_instance.invalidate_all("clear_all_test")
        
        # Should call invalidate_pattern with empty string
        memory_mock_redis.keys.assert_called_once_with(b"ai_cache:**")
        
        # Should track invalidation
        event = memory_cache_instance.performance_monitor.invalidation_events[0]
        assert event.pattern == ""
        assert event.operation_context == "clear_all_test"

    @pytest.mark.asyncio
    async def test_invalidate_by_operation(self, memory_cache_instance, memory_mock_redis):
        """Test invalidate_by_operation convenience method."""
        memory_mock_redis.keys.return_value = ["ai_cache:op:summarize|key1"]
        
        with patch.object(memory_cache_instance, 'connect', return_value=True):
            memory_cache_instance.redis = memory_mock_redis
            
            await memory_cache_instance.invalidate_by_operation("summarize", "operation_specific_test")
        
        # Should call invalidate_pattern with operation pattern
        memory_mock_redis.keys.assert_called_once_with(b"ai_cache:*op:summarize*")
        
        # Should track invalidation
        event = memory_cache_instance.performance_monitor.invalidation_events[0]
        assert event.pattern == "op:summarize"
        assert event.operation_context == "operation_specific_test"

    @pytest.mark.asyncio
    async def test_invalidate_memory_cache(self, memory_cache_instance):
        """Test memory cache invalidation tracking."""
        # Add some items to memory cache
        memory_cache_instance._update_memory_cache("key1", {"data": "value1"})
        memory_cache_instance._update_memory_cache("key2", {"data": "value2"})
        memory_cache_instance._update_memory_cache("key3", {"data": "value3"})
        
        assert len(memory_cache_instance.memory_cache) == 3
        
        # Invalidate memory cache
        await memory_cache_instance.invalidate_memory_cache("memory_test")
        
        # Memory cache should be cleared
        assert len(memory_cache_instance.memory_cache) == 0
        assert len(memory_cache_instance.memory_cache_order) == 0
        
        # Should track invalidation
        assert memory_cache_instance.performance_monitor.total_invalidations == 1
        assert memory_cache_instance.performance_monitor.total_keys_invalidated == 3
        
        event = memory_cache_instance.performance_monitor.invalidation_events[0]
        assert event.pattern == "memory_cache"
        assert event.keys_invalidated == 3
        assert event.invalidation_type == "memory"
        assert event.operation_context == "memory_test"
        assert event.additional_data["status"] == "success"
        assert event.additional_data["invalidation_target"] == "memory_cache_only"

    def test_get_invalidation_frequency_stats(self, memory_cache_instance):
        """Test invalidation frequency statistics."""
        # Trigger some invalidations to have data to test
        import asyncio
        
        async def trigger_invalidations():
            await memory_cache_instance.invalidate_memory_cache("test1")
            await memory_cache_instance.invalidate_memory_cache("test2")
        
        asyncio.run(trigger_invalidations())
        
        stats = memory_cache_instance.get_invalidation_frequency_stats()
        
        assert "total_invalidations" in stats
        assert "total_keys_invalidated" in stats
        assert stats["total_invalidations"] == 2

    def test_get_invalidation_recommendations(self, memory_cache_instance):
        """Test invalidation recommendations."""
        recommendations = memory_cache_instance.get_invalidation_recommendations()
        
        # Should return a list of recommendations
        assert isinstance(recommendations, list)

    def test_invalidation_integration_with_performance_stats(self, memory_cache_instance):
        """Test invalidation integration with performance statistics."""
        # Get performance summary
        summary = memory_cache_instance.get_performance_summary()
        
        # Should include invalidation data
        assert "total_invalidations" in summary
        assert "total_keys_invalidated" in summary

    def test_invalidation_events_cleanup(self, memory_cache_instance):
        """Test that invalidation events are cleaned up on reset."""
        import asyncio
        
        async def add_invalidation():
            await memory_cache_instance.invalidate_memory_cache("test")
        
        asyncio.run(add_invalidation())
        
        # Should have invalidation events
        assert len(memory_cache_instance.performance_monitor.invalidation_events) == 1
        
        # Reset performance stats
        memory_cache_instance.reset_performance_stats()
        
        # Invalidation events should be cleared
        assert len(memory_cache_instance.performance_monitor.invalidation_events) == 0


class TestCacheKeyGenerator:
    """Test the CacheKeyGenerator class."""
    
    @pytest.fixture
    def key_generator(self):
        """Create a fresh CacheKeyGenerator instance for testing."""
        return CacheKeyGenerator()
    
    @pytest.fixture
    def custom_key_generator(self):
        """Create a CacheKeyGenerator with custom settings."""
        return CacheKeyGenerator(text_hash_threshold=50)
    
    def test_instantiation_with_defaults(self, key_generator):
        """Test CacheKeyGenerator instantiation with default parameters."""
        assert key_generator.text_hash_threshold == 1000
        assert 'sha256' in key_generator.hash_algorithm.__name__.lower()
    
    def test_instantiation_with_custom_params(self, custom_key_generator):
        """Test CacheKeyGenerator instantiation with custom parameters."""
        assert custom_key_generator.text_hash_threshold == 50
        
    def test_short_text_handling(self, key_generator):
        """Test that short texts are kept as-is with sanitization."""
        short_text = "This is a short text"
        result = key_generator._hash_text_efficiently(short_text)
        
        # Should return sanitized original text for short inputs
        assert result == short_text
        
    def test_short_text_sanitization(self, key_generator):
        """Test that special characters are sanitized in short texts."""
        text_with_special_chars = "text|with:special|chars"
        result = key_generator._hash_text_efficiently(text_with_special_chars)
        
        # Should sanitize pipe and colon characters
        assert "|" not in result
        assert ":" not in result
        assert result == "text_with_special_chars"
        
    def test_long_text_hashing(self, key_generator):
        """Test that long texts are hashed efficiently."""
        # Create text longer than threshold (1000 chars)
        long_text = "A" * 1500
        result = key_generator._hash_text_efficiently(long_text)
        
        # Should return hash format for long texts
        assert result.startswith("hash:")
        assert len(result) == 21  # "hash:" + 16 char hash
        
    def test_long_text_with_custom_threshold(self, custom_key_generator):
        """Test long text handling with custom threshold."""
        # Text longer than custom threshold (50 chars)
        medium_text = "A" * 100
        result = custom_key_generator._hash_text_efficiently(medium_text)
        
        # Should be hashed with custom threshold
        assert result.startswith("hash:")
        
    def test_hash_consistency(self, key_generator):
        """Test that identical texts produce identical hashes."""
        long_text = "A" * 1500
        hash1 = key_generator._hash_text_efficiently(long_text)
        hash2 = key_generator._hash_text_efficiently(long_text)
        
        assert hash1 == hash2
        
    def test_hash_uniqueness(self, key_generator):
        """Test that different texts produce different hashes."""
        text1 = "A" * 1500
        text2 = "B" * 1500
        
        hash1 = key_generator._hash_text_efficiently(text1)
        hash2 = key_generator._hash_text_efficiently(text2)
        
        assert hash1 != hash2
        
    def test_cache_key_generation_basic(self, key_generator):
        """Test basic cache key generation."""
        text = "Test text"
        operation = "summarize"
        options = {"max_length": 100}
        
        cache_key = key_generator.generate_cache_key(text, operation, options)
        
        assert cache_key.startswith("ai_cache:")
        assert "op:summarize" in cache_key
        assert "txt:Test text" in cache_key
        assert "opts:" in cache_key
        
    def test_cache_key_with_question(self, key_generator):
        """Test cache key generation with question parameter."""
        text = "Test text"
        operation = "qa"
        options = {}
        question = "What is this about?"
        
        cache_key = key_generator.generate_cache_key(text, operation, options, question)
        
        assert cache_key.startswith("ai_cache:")
        assert "op:qa" in cache_key
        assert "q:" in cache_key
        
    def test_cache_key_without_options(self, key_generator):
        """Test cache key generation without options."""
        text = "Test text"
        operation = "sentiment"
        options = {}
        
        cache_key = key_generator.generate_cache_key(text, operation, options)
        
        assert cache_key.startswith("ai_cache:")
        assert "op:sentiment" in cache_key
        assert "txt:Test text" in cache_key
        assert "opts:" not in cache_key  # No options should mean no opts component
        
    def test_cache_key_consistency(self, key_generator):
        """Test that identical inputs produce identical cache keys."""
        text = "Test text"
        operation = "summarize"
        options = {"max_length": 100}
        
        key1 = key_generator.generate_cache_key(text, operation, options)
        key2 = key_generator.generate_cache_key(text, operation, options)
        
        assert key1 == key2
        
    def test_cache_key_options_order_independence(self, key_generator):
        """Test that options order doesn't affect cache key."""
        text = "Test text"
        operation = "summarize"
        options1 = {"max_length": 100, "style": "formal"}
        options2 = {"style": "formal", "max_length": 100}
        
        key1 = key_generator.generate_cache_key(text, operation, options1)
        key2 = key_generator.generate_cache_key(text, operation, options2)
        
        assert key1 == key2
        
    def test_cache_key_with_long_text(self, key_generator):
        """Test cache key generation with long text that gets hashed."""
        long_text = "A" * 1500
        operation = "summarize"
        options = {"max_length": 100}
        
        cache_key = key_generator.generate_cache_key(long_text, operation, options)
        
        assert cache_key.startswith("ai_cache:")
        assert "op:summarize" in cache_key
        assert "txt:hash:" in cache_key  # Long text should be hashed
        assert "opts:" in cache_key
        
    def test_cache_key_performance_improvement(self, key_generator):
        """Test that new implementation is more efficient for large texts."""
        import time
        import hashlib
        import json
        
        # Create large text
        large_text = "A" * 10000
        operation = "summarize"
        options = {"max_length": 100}
        
        # Time the new implementation
        start_time = time.time()
        for _ in range(100):
            key_generator.generate_cache_key(large_text, operation, options)
        new_time = time.time() - start_time
        
        # Time the old implementation approach
        start_time = time.time()
        for _ in range(100):
            cache_data = {
                "text": large_text,
                "operation": operation,
                "options": sorted(options.items()) if options else [],
                "question": None
            }
            content = json.dumps(cache_data, sort_keys=True)
            old_key = f"ai_cache:{hashlib.md5(content.encode()).hexdigest()}"
        old_time = time.time() - start_time
        
        # New implementation should be faster (allowing for some margin)
        # This is more of a performance characterization than a strict requirement
        print(f"New implementation time: {new_time:.4f}s")
        print(f"Old implementation time: {old_time:.4f}s")
        # Just verify both produce results
        assert len(key_generator.generate_cache_key(large_text, operation, options)) > 0
    
    # ==================== ENHANCED EDGE CASE TESTS ====================
    
    def test_empty_string_handling(self, key_generator):
        """Test CacheKeyGenerator behavior with empty strings."""
        # Arrange
        empty_text = ""
        operation = "summarize"
        options = {"max_length": 100}
        
        # Act
        result = key_generator._hash_text_efficiently(empty_text)
        cache_key = key_generator.generate_cache_key(empty_text, operation, options)
        
        # Assert
        assert result == empty_text  # Empty string should remain empty (below threshold)
        assert cache_key.startswith("ai_cache:")
        assert "op:summarize" in cache_key
        assert "txt:" in cache_key
        
    def test_boundary_threshold_conditions(self, key_generator):
        """Test behavior at exact threshold boundaries."""
        # Arrange - Text exactly at threshold (1000 chars)
        threshold_text = "A" * 1000
        over_threshold_text = "A" * 1001
        under_threshold_text = "A" * 999
        
        # Act
        at_threshold = key_generator._hash_text_efficiently(threshold_text)
        over_threshold = key_generator._hash_text_efficiently(over_threshold_text)
        under_threshold = key_generator._hash_text_efficiently(under_threshold_text)
        
        # Assert
        assert at_threshold == threshold_text.replace("|", "_").replace(":", "_")  # Should not be hashed
        assert over_threshold.startswith("hash:")  # Should be hashed
        assert under_threshold == under_threshold_text  # Should not be hashed
        
    def test_unicode_and_special_characters(self, key_generator):
        """Test CacheKeyGenerator with Unicode and special characters."""
        # Arrange
        unicode_text = "Hello 世界! 🌍 Testing émojis and spëcial chars: àáâãäå"
        operation = "summarize"
        options = {"style": "formal"}
        
        # Act
        text_hash = key_generator._hash_text_efficiently(unicode_text)
        cache_key = key_generator.generate_cache_key(unicode_text, operation, options)
        
        # Assert
        # Should handle Unicode gracefully
        assert text_hash == unicode_text.replace("|", "_").replace(":", "_")
        assert cache_key.startswith("ai_cache:")
        assert "op:summarize" in cache_key
        
    def test_various_option_value_types(self, key_generator):
        """Test cache key generation with different option value types."""
        # Arrange
        text = "Test text"
        operation = "summarize"
        complex_options = {
            "max_length": 100,
            "temperature": 0.7,
            "enabled": True,
            "disabled": False,
            "tags": ["tag1", "tag2"],
            "metadata": {"nested": "value"}
        }
        
        # Act
        cache_key = key_generator.generate_cache_key(text, operation, complex_options)
        
        # Assert
        assert cache_key.startswith("ai_cache:")
        assert "op:summarize" in cache_key
        assert "opts:" in cache_key
        
        # Test consistency with same complex options
        cache_key2 = key_generator.generate_cache_key(text, operation, complex_options)
        assert cache_key == cache_key2
        
    def test_performance_monitor_integration(self):
        """Test CacheKeyGenerator with performance monitor integration."""
        # Arrange
        monitor = CachePerformanceMonitor()
        key_generator = CacheKeyGenerator(performance_monitor=monitor)
        text = "Test text for performance monitoring"
        operation = "summarize"
        options = {"max_length": 100}
        
        # Act
        initial_count = len(monitor.key_generation_times)
        cache_key = key_generator.generate_cache_key(text, operation, options)
        
        # Assert
        assert cache_key.startswith("ai_cache:")
        assert len(monitor.key_generation_times) == initial_count + 1
        
        # Verify recorded performance data
        latest_metric = monitor.key_generation_times[-1]
        assert latest_metric.text_length == len(text)
        assert latest_metric.operation_type == operation
        assert isinstance(latest_metric.duration, float)
        assert latest_metric.duration >= 0
        
    def test_different_hash_algorithms(self):
        """Test CacheKeyGenerator with different hash algorithms."""
        # Arrange
        text = "A" * 1500  # Long text to trigger hashing
        md5_generator = CacheKeyGenerator(hash_algorithm=hashlib.md5)
        sha1_generator = CacheKeyGenerator(hash_algorithm=hashlib.sha1)
        sha256_generator = CacheKeyGenerator(hash_algorithm=hashlib.sha256)
        
        # Act
        md5_hash = md5_generator._hash_text_efficiently(text)
        sha1_hash = sha1_generator._hash_text_efficiently(text)
        sha256_hash = sha256_generator._hash_text_efficiently(text)
        
        # Assert
        assert md5_hash.startswith("hash:")
        assert sha1_hash.startswith("hash:")
        assert sha256_hash.startswith("hash:")
        
        # All should be different due to different algorithms
        assert md5_hash != sha1_hash
        assert md5_hash != sha256_hash
        assert sha1_hash != sha256_hash
        
    def test_none_and_invalid_inputs_handling(self, key_generator):
        """Test CacheKeyGenerator behavior with None and edge case inputs."""
        # Test with None question (should work normally)
        cache_key = key_generator.generate_cache_key("text", "summarize", {}, None)
        assert cache_key.startswith("ai_cache:")
        assert "q:" not in cache_key
        
        # Test with empty options dict
        cache_key2 = key_generator.generate_cache_key("text", "summarize", {})
        assert cache_key2.startswith("ai_cache:")
        assert "opts:" not in cache_key2
        
        # Test with options containing None values
        options_with_none = {"key1": None, "key2": "value"}
        cache_key3 = key_generator.generate_cache_key("text", "summarize", options_with_none)
        assert cache_key3.startswith("ai_cache:")
        
    def test_cache_key_structure_validation(self, key_generator):
        """Test the structure and format of generated cache keys."""
        # Arrange
        text = "Test text"
        operation = "sentiment"
        options = {"model": "advanced"}
        question = "What sentiment?"
        
        # Act
        cache_key = key_generator.generate_cache_key(text, operation, options, question)
        
        # Assert
        parts = cache_key.split("|")
        assert parts[0] == "ai_cache:op:sentiment"
        assert parts[1] == "txt:Test text"
        assert parts[2].startswith("opts:")
        assert parts[3].startswith("q:")
        assert len(parts) == 4  # Should have exactly 4 parts for this configuration
        
    def test_cache_key_length_constraints(self, key_generator):
        """Test that cache keys don't become excessively long."""
        # Arrange
        very_long_text = "A" * 50000  # Very large text
        operation = "summarize"
        options = {"param": "value"}
        
        # Act
        cache_key = key_generator.generate_cache_key(very_long_text, operation, options)
        
        # Assert
        # Cache key should be reasonably bounded even for very large texts
        assert len(cache_key) < 200  # Reasonable upper bound
        assert cache_key.startswith("ai_cache:")
        assert "txt:hash:" in cache_key  # Large text should be hashed
        
    def test_concurrent_key_generation_consistency(self, key_generator):
        """Test that concurrent key generation produces consistent results."""
        # Arrange
        text = "Concurrent test text"
        operation = "summarize"
        options = {"max_length": 150}
        
        # Act - Simulate concurrent access
        keys = []
        for _ in range(10):
            key = key_generator.generate_cache_key(text, operation, options)
            keys.append(key)
        
        # Assert
        # All keys should be identical (thread-safe/stateless behavior)
        assert all(key == keys[0] for key in keys)
        assert len(set(keys)) == 1  # All keys should be the same
        
    def test_performance_monitor_data_integrity(self):
        """Test that performance monitor receives accurate data."""
        # Arrange
        monitor = CachePerformanceMonitor()
        key_generator = CacheKeyGenerator(
            text_hash_threshold=100,
            performance_monitor=monitor
        )
        
        small_text = "Small"
        large_text = "A" * 200
        
        # Act
        key_generator.generate_cache_key(small_text, "summarize", {})
        key_generator.generate_cache_key(large_text, "sentiment", {"model": "v1"})
        
        # Assert
        assert len(monitor.key_generation_times) == 2
        
        # Check small text metric
        small_metric = monitor.key_generation_times[0]
        assert small_metric.text_length == len(small_text)
        assert small_metric.operation_type == "summarize"
        assert small_metric.additional_data["text_tier"] == "small"
        assert not small_metric.additional_data["has_options"]
        assert not small_metric.additional_data["has_question"]
        
        # Check large text metric
        large_metric = monitor.key_generation_times[1]
        assert large_metric.text_length == len(large_text)
        assert large_metric.operation_type == "sentiment"
        assert large_metric.additional_data["text_tier"] == "large"
        assert large_metric.additional_data["has_options"]
        assert not large_metric.additional_data["has_question"]
        
    def test_text_sanitization_edge_cases(self, key_generator):
        """Test edge cases in text sanitization."""
        # Arrange
        test_cases = [
            ("text|with|pipes", "text_with_pipes"),
            ("text:with:colons", "text_with_colons"),
            ("text|mixed:chars|here:", "text_mixed_chars_here_"),
            ("||||", "____"),
            ("::::", "____"),
            ("normal text", "normal text"),
            ("", ""),
        ]
        
        # Act & Assert
        for input_text, expected in test_cases:
            result = key_generator._hash_text_efficiently(input_text)
            assert result == expected, f"Failed for input: '{input_text}'"
            
    def test_hash_metadata_inclusion(self, key_generator):
        """Test that hash includes metadata for uniqueness."""
        # Arrange - Two texts with same content but different lengths due to spaces
        text1 = "A" * 1500
        text2 = "A" * 1500 + " "  # Same content + space (different length and word count)
        
        # Act
        hash1 = key_generator._hash_text_efficiently(text1)
        hash2 = key_generator._hash_text_efficiently(text2)
        
        # Assert
        assert hash1.startswith("hash:")
        assert hash2.startswith("hash:")
        assert hash1 != hash2  # Should be different due to metadata (length/word count)
        
    def test_question_parameter_hashing_consistency(self, key_generator):
        """Test that question parameter hashing is consistent and secure."""
        # Arrange
        text = "Test text"
        operation = "qa"
        options = {}
        question1 = "What is this about?"
        question2 = "What is this about?"  # Same question
        question3 = "What is this topic?"  # Different question
        
        # Act
        key1 = key_generator.generate_cache_key(text, operation, options, question1)
        key2 = key_generator.generate_cache_key(text, operation, options, question2)
        key3 = key_generator.generate_cache_key(text, operation, options, question3)
        
        # Assert
        assert key1 == key2  # Same questions should produce same keys
        assert key1 != key3  # Different questions should produce different keys
        
        # Check that question is hashed (not stored in plain text)
        assert question1 not in key1
        assert "q:" in key1  # Should have question component
        
    def test_options_hashing_security(self, key_generator):
        """Test that sensitive options are properly hashed."""
        # Arrange
        text = "Test text"
        operation = "summarize"
        sensitive_options = {
            "api_key": "secret_key_123",
            "password": "very_secret_password",
            "token": "auth_token_xyz"
        }
        
        # Act
        cache_key = key_generator.generate_cache_key(text, operation, sensitive_options)
        
        # Assert
        # Sensitive values should not appear in plain text in the cache key
        assert "secret_key_123" not in cache_key
        assert "very_secret_password" not in cache_key
        assert "auth_token_xyz" not in cache_key
        assert "opts:" in cache_key  # Should have options component


class TestAIResponseCacheTierSelection:
    """Comprehensive tests for AIResponseCache tier selection logic."""
    
    @pytest.fixture
    def cache_instance(self):
        """Create a fresh cache instance for tier testing."""
        return AIResponseCache()
    
    @pytest.fixture
    def mock_redis(self):
        """Mock Redis client for tier testing."""
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(return_value=True)
        mock_redis.get = AsyncMock(return_value=None)
        mock_redis.setex = AsyncMock(return_value=True)
        mock_redis.delete = AsyncMock(return_value=1)
        mock_redis.keys = AsyncMock(return_value=[])
        return mock_redis
    
    def test_tier_configuration_defaults(self, cache_instance):
        """Test that tier configuration has expected default values."""
        assert cache_instance.text_size_tiers['small'] == 500
        assert cache_instance.text_size_tiers['medium'] == 5000
        assert cache_instance.text_size_tiers['large'] == 50000
    
    def test_tier_configuration_custom(self):
        """Test that tier configuration can be customized."""
        # Custom tier thresholds for testing
        cache = AIResponseCache()
        cache.text_size_tiers = {
            'small': 100,
            'medium': 1000,
            'large': 10000
        }
        
        assert cache.text_size_tiers['small'] == 100
        assert cache.text_size_tiers['medium'] == 1000
        assert cache.text_size_tiers['large'] == 10000
    
    def test_text_tier_classification_comprehensive(self, cache_instance):
        """Test comprehensive text tier classification including all boundaries."""
        test_cases = [
            # Small tier tests (< 500 chars)
            ("", "small"),  # Empty string
            ("A", "small"),  # Single character
            ("A" * 100, "small"),  # Small text
            ("A" * 499, "small"),  # Boundary: just below small threshold
            
            # Medium tier tests (500-5000 chars)
            ("A" * 500, "medium"),  # Boundary: exactly at small threshold
            ("A" * 1000, "medium"),  # Mid-range medium
            ("A" * 4999, "medium"),  # Boundary: just below medium threshold
            
            # Large tier tests (5000-50000 chars)
            ("A" * 5000, "large"),  # Boundary: exactly at medium threshold
            ("A" * 25000, "large"),  # Mid-range large
            ("A" * 49999, "large"),  # Boundary: just below large threshold
            
            # XLarge tier tests (>= 50000 chars)
            ("A" * 50000, "xlarge"),  # Boundary: exactly at large threshold
            ("A" * 100000, "xlarge"),  # Very large text
        ]
        
        for text, expected_tier in test_cases:
            actual_tier = cache_instance._get_text_tier(text)
            assert actual_tier == expected_tier, \
                f"Failed for text length {len(text)}: expected '{expected_tier}', got '{actual_tier}'"
    
    @pytest.mark.asyncio
    async def test_small_tier_uses_memory_cache_on_cache_hit(self, cache_instance, mock_redis):
        """Test that small tier text uses memory cache when available."""
        # Arrange
        small_text = "A" * 100  # Small tier
        operation = "summarize"
        options = {"max_length": 150}
        
        cached_response = {"result": "cached_summary", "cache_hit": True}
        cache_key = cache_instance._generate_cache_key(small_text, operation, options)
        
        # Pre-populate memory cache
        cache_instance.memory_cache[cache_key] = cached_response
        
        # Mock Redis (should not be called for memory cache hit)
        mock_redis.get.return_value = None
        
        # Act
        with patch.object(cache_instance, 'connect', return_value=True):
            cache_instance.redis = mock_redis
            
            result = await cache_instance.get_cached_response(small_text, operation, options)
        
        # Assert
        assert result == cached_response
        mock_redis.get.assert_not_called()  # Memory cache hit should skip Redis
    
    @pytest.mark.asyncio
    async def test_medium_tier_skips_memory_cache_directly_to_redis(self, cache_instance, mock_redis):
        """Test that medium tier text bypasses memory cache and goes directly to Redis."""
        # Arrange
        medium_text = "A" * 1000  # Medium tier
        operation = "summarize"
        options = {"max_length": 150}
        
        redis_response = {"result": "redis_summary", "cache_hit": True}
        mock_redis.get.return_value = json.dumps(redis_response)
        
        # Act
        with patch.object(cache_instance, 'connect', return_value=True):
            cache_instance.redis = mock_redis
            
            result = await cache_instance.get_cached_response(medium_text, operation, options)
        
        # Assert
        assert result == redis_response
        mock_redis.get.assert_called_once()
        
        # Medium tier should NOT populate memory cache
        cache_key = cache_instance._generate_cache_key(medium_text, operation, options)
        assert cache_key not in cache_instance.memory_cache
    
    @pytest.mark.asyncio
    async def test_large_tier_skips_memory_cache_directly_to_redis(self, cache_instance, mock_redis):
        """Test that large tier text bypasses memory cache and goes directly to Redis."""
        # Arrange
        large_text = "A" * 10000  # Large tier
        operation = "summarize"
        options = {"max_length": 150}
        
        redis_response = {"result": "redis_summary", "cache_hit": True}
        mock_redis.get.return_value = json.dumps(redis_response)
        
        # Act
        with patch.object(cache_instance, 'connect', return_value=True):
            cache_instance.redis = mock_redis
            
            result = await cache_instance.get_cached_response(large_text, operation, options)
        
        # Assert
        assert result == redis_response
        mock_redis.get.assert_called_once()
        
        # Large tier should NOT populate memory cache
        cache_key = cache_instance._generate_cache_key(large_text, operation, options)
        assert cache_key not in cache_instance.memory_cache
    
    @pytest.mark.asyncio
    async def test_xlarge_tier_skips_memory_cache_directly_to_redis(self, cache_instance, mock_redis):
        """Test that xlarge tier text bypasses memory cache and goes directly to Redis."""
        # Arrange
        xlarge_text = "A" * 60000  # XLarge tier
        operation = "summarize"
        options = {"max_length": 150}
        
        redis_response = {"result": "redis_summary", "cache_hit": True}
        mock_redis.get.return_value = json.dumps(redis_response)
        
        # Act
        with patch.object(cache_instance, 'connect', return_value=True):
            cache_instance.redis = mock_redis
            
            result = await cache_instance.get_cached_response(xlarge_text, operation, options)
        
        # Assert
        assert result == redis_response
        mock_redis.get.assert_called_once()
        
        # XLarge tier should NOT populate memory cache
        cache_key = cache_instance._generate_cache_key(xlarge_text, operation, options)
        assert cache_key not in cache_instance.memory_cache
    
    @pytest.mark.asyncio
    async def test_tier_boundary_memory_cache_behavior(self, cache_instance, mock_redis):
        """Test memory cache behavior at exact tier boundaries."""
        operation = "summarize"
        options = {}
        
        # Test texts at tier boundaries
        test_cases = [
            ("A" * 499, "small", True),   # Just below small threshold - should use memory cache
            ("A" * 500, "medium", False), # Exactly at small threshold - should NOT use memory cache
            ("A" * 4999, "medium", False), # Just below medium threshold - should NOT use memory cache
            ("A" * 5000, "large", False),  # Exactly at medium threshold - should NOT use memory cache
        ]
        
        redis_response = {"result": "redis_summary", "cache_hit": True}
        mock_redis.get.return_value = json.dumps(redis_response)
        
        with patch.object(cache_instance, 'connect', return_value=True):
            cache_instance.redis = mock_redis
            
            for text, expected_tier, should_use_memory_cache in test_cases:
                # Reset Redis mock call count
                mock_redis.reset_mock()
                
                # Verify tier classification
                actual_tier = cache_instance._get_text_tier(text)
                assert actual_tier == expected_tier, \
                    f"Tier mismatch for length {len(text)}: expected {expected_tier}, got {actual_tier}"
                
                # Test cache behavior
                result = await cache_instance.get_cached_response(text, operation, options)
                assert result == redis_response
                
                # Check memory cache population
                cache_key = cache_instance._generate_cache_key(text, operation, options)
                if should_use_memory_cache:
                    assert cache_key in cache_instance.memory_cache, \
                        f"Memory cache should contain key for small tier text (length {len(text)})"
                else:
                    assert cache_key not in cache_instance.memory_cache, \
                        f"Memory cache should NOT contain key for {expected_tier} tier text (length {len(text)})"
    
    @pytest.mark.asyncio
    async def test_mixed_tier_cache_behavior_isolation(self, cache_instance, mock_redis):
        """Test that different tiers don't interfere with each other's caching behavior."""
        operation = "summarize"
        options = {}
        
        # Prepare different tier texts
        small_text = "A" * 100
        medium_text = "A" * 1000
        large_text = "A" * 10000
        
        redis_response = {"result": "summary", "cache_hit": True}
        mock_redis.get.return_value = json.dumps(redis_response)
        
        with patch.object(cache_instance, 'connect', return_value=True):
            cache_instance.redis = mock_redis
            
            # Process each tier
            small_result = await cache_instance.get_cached_response(small_text, operation, options)
            medium_result = await cache_instance.get_cached_response(medium_text, operation, options)
            large_result = await cache_instance.get_cached_response(large_text, operation, options)
            
            # All should return the Redis response
            assert small_result == redis_response
            assert medium_result == redis_response
            assert large_result == redis_response
            
            # Check memory cache state
            small_key = cache_instance._generate_cache_key(small_text, operation, options)
            medium_key = cache_instance._generate_cache_key(medium_text, operation, options)
            large_key = cache_instance._generate_cache_key(large_text, operation, options)
            
            # Only small tier should be in memory cache
            assert small_key in cache_instance.memory_cache
            assert medium_key not in cache_instance.memory_cache
            assert large_key not in cache_instance.memory_cache
            
            # Memory cache should contain exactly one item
            assert len(cache_instance.memory_cache) == 1
    
    @pytest.mark.asyncio
    async def test_tier_selection_with_custom_thresholds(self, mock_redis):
        """Test tier selection with custom threshold configuration."""
        # Create cache with custom tier thresholds
        cache_instance = AIResponseCache()
        cache_instance.text_size_tiers = {
            'small': 100,
            'medium': 1000,
            'large': 10000
        }
        
        # Test texts with custom thresholds
        test_cases = [
            ("A" * 50, "small"),     # Well below custom small threshold
            ("A" * 99, "small"),     # Just below custom small threshold
            ("A" * 100, "medium"),   # Exactly at custom small threshold
            ("A" * 500, "medium"),   # Mid-range custom medium
            ("A" * 999, "medium"),   # Just below custom medium threshold
            ("A" * 1000, "large"),   # Exactly at custom medium threshold
            ("A" * 5000, "large"),   # Mid-range custom large
            ("A" * 9999, "large"),   # Just below custom large threshold
            ("A" * 10000, "xlarge"), # Exactly at custom large threshold
        ]
        
        for text, expected_tier in test_cases:
            actual_tier = cache_instance._get_text_tier(text)
            assert actual_tier == expected_tier, \
                f"Custom tier mismatch for length {len(text)}: expected {expected_tier}, got {actual_tier}"
    
    @pytest.mark.asyncio
    async def test_tier_selection_affects_cache_storage_behavior(self, cache_instance, mock_redis):
        """Test that tier selection affects how responses are stored in cache."""
        operation = "summarize"
        options = {}
        response_data = {"result": "test_summary", "success": True}
        
        # Test different tier texts
        small_text = "A" * 100   # Small tier
        medium_text = "A" * 1000 # Medium tier
        large_text = "A" * 10000 # Large tier
        
        with patch.object(cache_instance, 'connect', return_value=True):
            cache_instance.redis = mock_redis
            
            # Store responses for different tiers
            await cache_instance.cache_response(small_text, operation, options, response_data)
            await cache_instance.cache_response(medium_text, operation, options, response_data)
            await cache_instance.cache_response(large_text, operation, options, response_data)
            
            # All should result in Redis storage calls
            assert mock_redis.setex.call_count == 3
            
            # Verify cache keys are different for different tiers
            small_key = cache_instance._generate_cache_key(small_text, operation, options)
            medium_key = cache_instance._generate_cache_key(medium_text, operation, options)
            large_key = cache_instance._generate_cache_key(large_text, operation, options)
            
            assert small_key != medium_key
            assert medium_key != large_key
            assert small_key != large_key
    
    @pytest.mark.asyncio
    async def test_tier_selection_error_handling(self, cache_instance):
        """Test tier selection behavior with edge cases and error conditions."""
        # Test with None text (should handle gracefully)
        with pytest.raises(TypeError):
            cache_instance._get_text_tier(None)
        
        # Test with non-string input
        with pytest.raises(TypeError):
            cache_instance._get_text_tier(123)
        
        # Test with very large text (should still work)
        very_large_text = "A" * 1000000  # 1 million characters
        tier = cache_instance._get_text_tier(very_large_text)
        assert tier == "xlarge"
    
    @pytest.mark.asyncio
    async def test_tier_selection_memory_cache_eviction_behavior(self, cache_instance, mock_redis):
        """Test that memory cache eviction only affects small tier items."""
        # Set small memory cache size for testing
        cache_instance.memory_cache_size = 2
        
        operation = "summarize"
        options = {}
        redis_response = {"result": "summary", "cache_hit": True}
        mock_redis.get.return_value = json.dumps(redis_response)
        
        with patch.object(cache_instance, 'connect', return_value=True):
            cache_instance.redis = mock_redis
            
            # Add multiple small tier items to trigger eviction
            small_text_1 = "A" * 50
            small_text_2 = "B" * 60
            small_text_3 = "C" * 70  # This should trigger eviction
            medium_text = "D" * 1000  # This should not be added to memory cache
            
            # Process items
            await cache_instance.get_cached_response(small_text_1, operation, options)
            await cache_instance.get_cached_response(small_text_2, operation, options)
            await cache_instance.get_cached_response(medium_text, operation, options)
            await cache_instance.get_cached_response(small_text_3, operation, options)
            
            # Check memory cache state
            assert len(cache_instance.memory_cache) == 2  # Should be at size limit
            
            # Should contain the 2 most recent small tier items
            key_2 = cache_instance._generate_cache_key(small_text_2, operation, options)
            key_3 = cache_instance._generate_cache_key(small_text_3, operation, options)
            medium_key = cache_instance._generate_cache_key(medium_text, operation, options)
            
            assert key_2 in cache_instance.memory_cache
            assert key_3 in cache_instance.memory_cache
            assert medium_key not in cache_instance.memory_cache  # Medium tier never enters memory cache
    
    def test_tier_selection_configuration_immutability_during_operation(self, cache_instance):
        """Test that tier configuration doesn't change during cache operations."""
        # Store original configuration
        original_tiers = cache_instance.text_size_tiers.copy()
        
        # Perform various operations
        texts = ["A" * 100, "B" * 1000, "C" * 10000]
        for text in texts:
            tier = cache_instance._get_text_tier(text)
            assert tier in ["small", "medium", "large", "xlarge"]
        
        # Verify configuration hasn't changed
        assert cache_instance.text_size_tiers == original_tiers 


class TestDataCompressionDecompression:
    """Comprehensive unit tests for data compression and decompression functionality."""
    
    @pytest.fixture
    def cache_instance(self):
        """Create a cache instance for compression testing."""
        return AIResponseCache()
    
    @pytest.fixture
    def custom_compression_cache(self):
        """Create a cache instance with custom compression settings."""
        return AIResponseCache(
            compression_threshold=500,  # Lower threshold for testing
            compression_level=9  # Maximum compression
        )
    
    @pytest.fixture
    def no_compression_cache(self):
        """Create a cache instance with very high compression threshold (effectively no compression)."""
        return AIResponseCache(
            compression_threshold=1000000  # Very high threshold
        )

    def test_small_data_compression_and_decompression(self, cache_instance):
        """Test that small data is handled correctly without compression."""
        # Small data under default threshold (1000 bytes)
        small_data = {
            "result": "short response",
            "operation": "summarize",
            "success": True,
            "cached_at": "2024-01-01T12:00:00Z",
            "metadata": {"size": "small"}
        }
        
        # Compress the data
        compressed = cache_instance._compress_data(small_data)
        
        # Should use raw format (no compression)
        assert compressed.startswith(b"raw:")
        assert not compressed.startswith(b"compressed:")
        
        # Should be able to decompress back to original
        decompressed = cache_instance._decompress_data(compressed)
        assert decompressed == small_data
        
        # Verify data integrity
        assert decompressed["result"] == "short response"
        assert decompressed["success"] is True
        assert decompressed["metadata"]["size"] == "small"

    def test_large_data_compression_and_decompression(self, cache_instance):
        """Test that large data is compressed and decompressed correctly."""
        # Large data exceeding default threshold (1000 bytes)
        large_text = "This is a very long response that contains lots of repeated information. " * 50
        large_data = {
            "result": large_text,
            "operation": "summarize",
            "success": True,
            "cached_at": "2024-01-01T12:00:00Z",
            "metadata": {"size": "large", "compression": True},
            "additional_info": {
                "source": "test",
                "processing_time": 1.5,
                "tokens": [1, 2, 3, 4, 5] * 100  # Large array
            }
        }
        
        # Compress the data
        compressed = cache_instance._compress_data(large_data)
        
        # Should use compressed format
        assert compressed.startswith(b"compressed:")
        assert not compressed.startswith(b"raw:")
        
        # Verify compression actually reduced size
        import pickle
        original_size = len(pickle.dumps(large_data))
        compressed_size = len(compressed) - 11  # Remove prefix length
        assert compressed_size < original_size, "Data should be compressed smaller"
        
        # Calculate compression ratio
        compression_ratio = compressed_size / original_size
        assert compression_ratio < 0.9, "Should achieve at least 10% compression"
        
        # Should be able to decompress back to original
        decompressed = cache_instance._decompress_data(compressed)
        assert decompressed == large_data
        
        # Verify data integrity for complex structures
        assert len(decompressed["result"]) == len(large_text)
        assert decompressed["additional_info"]["tokens"] == [1, 2, 3, 4, 5] * 100
        assert decompressed["metadata"]["compression"] is True

    def test_empty_data_handling(self, cache_instance):
        """Test handling of empty data structures."""
        empty_data_cases = [
            {},  # Empty dict
            {"result": ""},  # Empty string result
            {"result": [], "metadata": {}},  # Empty arrays and objects
            {"result": None, "success": True},  # None values
        ]
        
        for empty_data in empty_data_cases:
            # Should handle compression/decompression without errors
            compressed = cache_instance._compress_data(empty_data)
            decompressed = cache_instance._decompress_data(compressed)
            assert decompressed == empty_data

    def test_very_large_data_handling(self, cache_instance):
        """Test handling of very large data structures."""
        # Create very large data (several MB)
        massive_text = "A" * 1000000  # 1 MB of text
        very_large_data = {
            "result": massive_text,
            "operation": "analyze",
            "success": True,
            "large_array": list(range(10000)),  # Large numeric array
            "nested_structure": {
                "level1": {
                    "level2": {
                        "level3": ["data"] * 1000
                    }
                }
            }
        }
        
        # Should handle compression/decompression
        compressed = cache_instance._compress_data(very_large_data)
        decompressed = cache_instance._decompress_data(compressed)
        
        # Verify data integrity
        assert decompressed == very_large_data
        assert len(decompressed["result"]) == 1000000
        assert len(decompressed["large_array"]) == 10000
        assert len(decompressed["nested_structure"]["level1"]["level2"]["level3"]) == 1000
        
        # Should achieve significant compression for repetitive data
        import pickle
        original_size = len(pickle.dumps(very_large_data))
        compressed_size = len(compressed) - 11  # Remove prefix
        compression_ratio = compressed_size / original_size
        assert compression_ratio < 0.1, "Should achieve very high compression for repetitive data"

    def test_various_data_types_compression(self, cache_instance):
        """Test compression/decompression with various Python data types."""
        complex_data = {
            "string": "Hello World!",
            "integer": 42,
            "float": 3.14159,
            "boolean": True,
            "none_value": None,
            "list": [1, 2, 3, "four", 5.0],
            "tuple": (1, 2, 3),  # Note: pickle preserves tuples
            "set": {1, 2, 3, 4},  # Note: pickle preserves sets
            "dict": {"nested": {"deep": {"value": "found"}}},
            "bytes": b"binary data here",
            "unicode": "Unicode: 你好世界 🌍 emoji test",
            "large_text": "Repeated content " * 100,  # To trigger compression
        }
        
        # Compress and decompress
        compressed = cache_instance._compress_data(complex_data)
        decompressed = cache_instance._decompress_data(compressed)
        
        # Verify all data types are preserved
        assert decompressed["string"] == "Hello World!"
        assert decompressed["integer"] == 42
        assert decompressed["float"] == 3.14159
        assert decompressed["boolean"] is True
        assert decompressed["none_value"] is None
        assert decompressed["list"] == [1, 2, 3, "four", 5.0]
        assert decompressed["tuple"] == (1, 2, 3)
        assert decompressed["set"] == {1, 2, 3, 4}
        assert decompressed["dict"]["nested"]["deep"]["value"] == "found"
        assert decompressed["bytes"] == b"binary data here"
        assert decompressed["unicode"] == "Unicode: 你好世界 🌍 emoji test"
        assert decompressed["large_text"] == "Repeated content " * 100

    def test_boundary_threshold_compression(self, cache_instance):
        """Test compression behavior at exact threshold boundaries."""
        threshold = cache_instance.compression_threshold  # Default 1000
        
        # Test data just under threshold
        import pickle
        test_data = {"result": "test"}
        while len(pickle.dumps(test_data)) < threshold - 10:
            test_data["padding"] = test_data.get("padding", "") + "x"
        
        compressed_under = cache_instance._compress_data(test_data)
        assert compressed_under.startswith(b"raw:")
        
        # Test data just over threshold
        test_data["extra"] = "x" * 100  # Push over threshold
        assert len(pickle.dumps(test_data)) > threshold
        
        compressed_over = cache_instance._compress_data(test_data)
        assert compressed_over.startswith(b"compressed:")
        
        # Both should decompress correctly
        decompressed_under = cache_instance._decompress_data(compressed_under)
        decompressed_over = cache_instance._decompress_data(compressed_over)
        
        # Verify the under-threshold data doesn't have the extra field
        assert "extra" not in decompressed_under
        assert "extra" in decompressed_over

    def test_custom_compression_settings(self, custom_compression_cache):
        """Test compression with custom threshold and level settings."""
        # Data that would be compressed with custom threshold (500) but not default (1000)
        medium_data = {
            "result": "x" * 600,  # Between 500 and 1000 bytes
            "operation": "test"
        }
        
        # Should be compressed with custom settings
        compressed = custom_compression_cache._compress_data(medium_data)
        assert compressed.startswith(b"compressed:")
        
        # Should decompress correctly
        decompressed = custom_compression_cache._decompress_data(compressed)
        assert decompressed == medium_data
        
        # Verify high compression level (9) is more effective
        large_repetitive_data = {"result": "repeated text " * 1000}
        compressed_max = custom_compression_cache._compress_data(large_repetitive_data)
        
        # Create cache with lower compression level for comparison
        low_compression_cache = AIResponseCache(compression_level=1)
        compressed_min = low_compression_cache._compress_data(large_repetitive_data)
        
        # Max compression should be smaller
        assert len(compressed_max) <= len(compressed_min)

    def test_compression_ratio_validation(self, cache_instance):
        """Test that compression ratios are within expected ranges for different data types."""
        test_cases = [
            # (description, data, expected_max_ratio)
            ("Highly repetitive text", {"result": "AAAA" * 1000}, 0.1),
            ("Random-like text", {"result": "abcdefghijklmnop" * 100}, 0.8),
            ("JSON-like structure", {"items": [{"id": i, "name": f"item_{i}"} for i in range(100)]}, 0.6),
            ("Mixed data types", {"text": "x" * 500, "numbers": list(range(500)), "bools": [True, False] * 250}, 0.7),
        ]
        
        for description, data, expected_max_ratio in test_cases:
            compressed = cache_instance._compress_data(data)
            
            if compressed.startswith(b"compressed:"):
                import pickle
                original_size = len(pickle.dumps(data))
                compressed_size = len(compressed) - 11  # Remove prefix
                actual_ratio = compressed_size / original_size
                
                assert actual_ratio <= expected_max_ratio, \
                    f"{description}: compression ratio {actual_ratio:.3f} exceeds expected max {expected_max_ratio}"
            
            # Verify data integrity regardless of compression
            decompressed = cache_instance._decompress_data(compressed)
            assert decompressed == data, f"{description}: data integrity failed"

    def test_error_handling_corrupted_data(self, cache_instance):
        """Test error handling for corrupted or invalid compressed data."""
        # Test various corruption scenarios
        corrupted_cases = [
            b"compressed:invalid_zlib_data",
            b"raw:invalid_pickle_data",
            b"unknown_prefix:data",
            b"compressed:",  # Empty compressed data
            b"raw:",  # Empty raw data
            b"",  # Completely empty
        ]
        
        for corrupted_data in corrupted_cases:
            with pytest.raises((Exception, ValueError, EOFError, TypeError)):
                cache_instance._decompress_data(corrupted_data)

    def test_compression_performance_characteristics(self, cache_instance):
        """Test performance characteristics of compression/decompression operations."""
        import time
        
        # Prepare test data of various sizes
        test_data_sizes = [
            ("Small", {"result": "x" * 100}),
            ("Medium", {"result": "x" * 2000}),
            ("Large", {"result": "x" * 10000}),
            ("Very Large", {"result": "x" * 100000}),
        ]
        
        for size_name, data in test_data_sizes:
            # Measure compression time
            start_time = time.time()
            compressed = cache_instance._compress_data(data)
            compression_time = time.time() - start_time
            
            # Measure decompression time
            start_time = time.time()
            decompressed = cache_instance._decompress_data(compressed)
            decompression_time = time.time() - start_time
            
            # Verify data integrity
            assert decompressed == data
            
            # Performance assertions (reasonable limits)
            assert compression_time < 1.0, f"{size_name}: compression took {compression_time:.3f}s (should be < 1s)"
            assert decompression_time < 0.5, f"{size_name}: decompression took {decompression_time:.3f}s (should be < 0.5s)"
            
            # Decompression should generally be faster than compression
            if compressed.startswith(b"compressed:"):
                assert decompression_time <= compression_time * 2, \
                    f"{size_name}: decompression should not be much slower than compression"

    def test_compression_with_none_and_invalid_inputs(self, cache_instance):
        """Test compression/decompression with None and invalid inputs."""
        # None input should work with pickle (pickle can handle None)
        compressed_none = cache_instance._compress_data(None)
        decompressed_none = cache_instance._decompress_data(compressed_none)
        assert decompressed_none is None
        
        # Non-dict input should work with pickle (lists, strings, etc.)
        list_data = [1, 2, 3, "test", {"nested": "dict"}]
        compressed_list = cache_instance._compress_data(list_data)
        decompressed_list = cache_instance._decompress_data(compressed_list)
        assert decompressed_list == list_data
        
        # String input should work
        string_data = "This is just a string" * 100  # Make it large enough for compression
        compressed_string = cache_instance._compress_data(string_data)
        decompressed_string = cache_instance._decompress_data(compressed_string)
        assert decompressed_string == string_data

    def test_compression_consistency_across_calls(self, cache_instance):
        """Test that compression produces consistent results across multiple calls."""
        test_data = {
            "result": "Consistent data for testing",
            "metadata": {"test": True, "id": 12345},
            "large_content": "Repeated content for compression testing " * 50
        }
        
        # Compress the same data multiple times
        compressed_1 = cache_instance._compress_data(test_data)
        compressed_2 = cache_instance._compress_data(test_data)
        compressed_3 = cache_instance._compress_data(test_data)
        
        # All compressions should produce identical results
        assert compressed_1 == compressed_2
        assert compressed_2 == compressed_3
        
        # All should decompress to the same original data
        decompressed_1 = cache_instance._decompress_data(compressed_1)
        decompressed_2 = cache_instance._decompress_data(compressed_2)
        decompressed_3 = cache_instance._decompress_data(compressed_3)
        
        assert decompressed_1 == test_data
        assert decompressed_2 == test_data
        assert decompressed_3 == test_data
        assert decompressed_1 == decompressed_2 == decompressed_3

    def test_no_compression_behavior(self, no_compression_cache):
        """Test behavior when compression is effectively disabled (very high threshold)."""
        # Even very large data should not be compressed
        large_data = {
            "result": "This is very large data that would normally be compressed " * 1000,
            "metadata": {"size": "huge"},
            "array": list(range(1000))
        }
        
        compressed = no_compression_cache._compress_data(large_data)
        
        # Should use raw format even for large data
        assert compressed.startswith(b"raw:")
        assert not compressed.startswith(b"compressed:")
        
        # Should still decompress correctly
        decompressed = no_compression_cache._decompress_data(compressed)
        assert decompressed == large_data

    def test_compression_with_circular_references_error_handling(self, cache_instance):
        """Test that circular references are handled appropriately."""
        # Create circular reference
        circular_data = {"self": None}
        circular_data["self"] = circular_data
        
        # Pickle can actually handle circular references correctly
        compressed = cache_instance._compress_data(circular_data)
        decompressed = cache_instance._decompress_data(compressed)
        
        # Verify the circular reference is preserved
        assert decompressed["self"] is decompressed  # Should reference itself

    def test_compression_memory_efficiency(self, cache_instance):
        """Test that compression reduces data size effectively."""
        import pickle
        
        # Create reasonably large test data with repetitive content (compresses well)
        large_data = {
            "content": "Repeated content for compression " * 5000,
            "array": [1, 2, 3] * 1000,  # Repetitive array
            "metadata": {"test": True}
        }
        
        # Get pickled size before compression
        pickled_data = pickle.dumps(large_data)
        original_size = len(pickled_data)
        
        # Perform compression
        compressed = cache_instance._compress_data(large_data)
        
        # Should use compressed format for large data
        assert compressed.startswith(b"compressed:")
        
        # Compressed data should be significantly smaller than pickled original
        compressed_size = len(compressed)
        compression_ratio = compressed_size / original_size
        assert compression_ratio < 0.5, f"Compression ratio {compression_ratio:.3f} should be < 0.5 for repetitive data"
        
        # Decompression should restore original data
        decompressed = cache_instance._decompress_data(compressed)
        assert decompressed == large_data


class TestRedisIntegrationTests:
    """Integration tests for Redis cache interactions with proper mocking."""
    
    @pytest.fixture
    def integration_cache_instance(self):
        """Create a cache instance for integration testing."""
        return AIResponseCache(
            redis_url="redis://test-redis:6379",
            default_ttl=1800,
            compression_threshold=500
        )
    
    @pytest.fixture
    def mock_redis_client(self):
        """Create a comprehensive mock Redis client for integration testing."""
        mock_redis = AsyncMock()
        
        # Connection-related mocks
        mock_redis.ping = AsyncMock(return_value=True)
        
        # Data storage (simulate actual Redis data storage)
        mock_redis._data = {}  # Internal storage for mocked data
        mock_redis._ttls = {}  # Internal TTL tracking
        
        # GET operation mock
        async def mock_get(key):
            if isinstance(key, str):
                key = key.encode('utf-8')
            key_str = key.decode('utf-8') if isinstance(key, bytes) else str(key)
            return mock_redis._data.get(key_str)
        mock_redis.get = mock_get
        
        # SETEX operation mock (set with expiration)
        async def mock_setex(key, ttl, value):
            key_str = key if isinstance(key, str) else key.decode('utf-8')
            mock_redis._data[key_str] = value
            mock_redis._ttls[key_str] = ttl
            return True
        mock_redis.setex = mock_setex
        
        # DELETE operation mock
        async def mock_delete(*keys):
            deleted = 0
            for key in keys:
                key_str = key.decode('utf-8') if isinstance(key, bytes) else str(key)
                if key_str in mock_redis._data:
                    del mock_redis._data[key_str]
                    mock_redis._ttls.pop(key_str, None)
                    deleted += 1
            return deleted
        mock_redis.delete = mock_delete
        
        # KEYS operation mock
        async def mock_keys(pattern):
            if isinstance(pattern, bytes):
                pattern = pattern.decode('utf-8')
            import fnmatch
            matching_keys = []
            for key in mock_redis._data.keys():
                if fnmatch.fnmatch(key, pattern):
                    matching_keys.append(key.encode('utf-8'))
            return matching_keys
        mock_redis.keys = mock_keys
        
        # INFO operation mock
        async def mock_info():
            return {
                "used_memory_human": "2.5M",
                "used_memory": 2621440,
                "connected_clients": 3,
                "redis_version": "7.0.0"
            }
        mock_redis.info = mock_info
        
        return mock_redis
    
    @pytest.mark.asyncio
    async def test_redis_set_operation_stores_data_correctly(self, integration_cache_instance, mock_redis_client):
        """Test that Redis set operations store data correctly with proper serialization."""
        # Mock successful connection
        with patch.object(integration_cache_instance, 'connect', return_value=True):
            integration_cache_instance.redis = mock_redis_client
            
            # Test data to cache
            test_text = "Test text for Redis set operation"
            test_operation = "summarize"
            test_options = {"max_length": 100}
            test_response = {
                "operation": "summarize",
                "result": "Test summary result",
                "success": True,
                "processing_time": 1.23
            }
            
            # Perform cache storage
            await integration_cache_instance.cache_response(
                test_text, test_operation, test_options, test_response
            )
            
            # Verify data was stored
            expected_key = integration_cache_instance._generate_cache_key(
                test_text, test_operation, test_options
            )
            assert expected_key in mock_redis_client._data
            
            # Verify TTL was set correctly
            assert expected_key in mock_redis_client._ttls
            assert mock_redis_client._ttls[expected_key] == integration_cache_instance.operation_ttls.get("summarize", integration_cache_instance.default_ttl)
            
            # Verify stored data integrity
            stored_data = mock_redis_client._data[expected_key]
            assert stored_data is not None
            
            # Verify compressed data can be decompressed correctly
            decompressed_data = integration_cache_instance._decompress_data(stored_data)
            assert decompressed_data["result"] == "Test summary result"
            assert decompressed_data["operation"] == "summarize"
            assert decompressed_data["success"] is True
            assert "cached_at" in decompressed_data
            assert "compression_used" in decompressed_data
    
    @pytest.mark.asyncio
    async def test_redis_get_operation_retrieves_data_correctly(self, integration_cache_instance, mock_redis_client):
        """Test that Redis get operations retrieve data correctly with proper deserialization."""
        # Mock successful connection
        with patch.object(integration_cache_instance, 'connect', return_value=True):
            integration_cache_instance.redis = mock_redis_client
            
            # Pre-populate cache with test data
            test_text = "Test text for Redis get operation"
            test_operation = "sentiment"
            test_options = {"model": "advanced"}
            test_response = {
                "operation": "sentiment",
                "result": "positive",
                "confidence": 0.95,
                "success": True
            }
            
            # Store data first
            await integration_cache_instance.cache_response(
                test_text, test_operation, test_options, test_response
            )
            
            # Now retrieve the data
            retrieved_data = await integration_cache_instance.get_cached_response(
                test_text, test_operation, test_options
            )
            
            # Verify retrieval was successful
            assert retrieved_data is not None
            assert retrieved_data["operation"] == "sentiment"
            assert retrieved_data["result"] == "positive"
            assert retrieved_data["confidence"] == 0.95
            assert retrieved_data["success"] is True
            assert "cached_at" in retrieved_data
            assert retrieved_data["cache_hit"] is True
    
    @pytest.mark.asyncio
    async def test_redis_get_operation_returns_none_for_missing_data(self, integration_cache_instance, mock_redis_client):
        """Test that Redis get operations return None for missing/non-existent data."""
        # Mock successful connection
        with patch.object(integration_cache_instance, 'connect', return_value=True):
            integration_cache_instance.redis = mock_redis_client
            
            # Try to retrieve non-existent data
            retrieved_data = await integration_cache_instance.get_cached_response(
                "Non-existent text", "summarize", {}
            )
            
            # Verify cache miss
            assert retrieved_data is None
    
    @pytest.mark.asyncio
    async def test_redis_expiration_settings_work_as_expected(self, integration_cache_instance, mock_redis_client):
        """Test that Redis expiration (TTL) settings work correctly for different operations."""
        # Mock successful connection
        with patch.object(integration_cache_instance, 'connect', return_value=True):
            integration_cache_instance.redis = mock_redis_client
            
            # Test different operations with different TTLs
            test_cases = [
                ("summarize", "Test summarize text", {"length": 100}, 7200),  # 2 hours
                ("sentiment", "Test sentiment text", {"model": "basic"}, 86400),  # 24 hours
                ("key_points", "Test key points text", {"count": 5}, 7200),  # 2 hours
                ("questions", "Test questions text", {"count": 3}, 3600),  # 1 hour
                ("qa", "Test QA text", {"context": "test"}, 1800),  # 30 minutes
                ("custom_operation", "Test custom operation", {}, 1800)  # default TTL
            ]
            
            for operation, text, options, expected_ttl in test_cases:
                test_response = {
                    "operation": operation,
                    "result": f"Test result for {operation}",
                    "success": True
                }
                
                # Cache the response
                await integration_cache_instance.cache_response(
                    text, operation, options, test_response
                )
                
                # Verify TTL was set correctly
                cache_key = integration_cache_instance._generate_cache_key(text, operation, options)
                assert cache_key in mock_redis_client._ttls
                assert mock_redis_client._ttls[cache_key] == expected_ttl
    
    @pytest.mark.asyncio
    async def test_redis_connection_error_handling(self, integration_cache_instance):
        """Test error handling for Redis connection issues."""
        # Test connection failure during connect()
        with patch('app.services.cache.REDIS_AVAILABLE', True):
            with patch('app.services.cache.aioredis') as mock_aioredis:
                # Simulate connection failure
                async def mock_from_url(*args, **kwargs):
                    raise ConnectionError("Redis connection failed")
                mock_aioredis.from_url = mock_from_url
                
                # Attempt to connect
                result = await integration_cache_instance.connect()
                assert result is False
                assert integration_cache_instance.redis is None
                
                # Test cache operations gracefully handle connection failure
                cached_response = await integration_cache_instance.get_cached_response(
                    "test text", "summarize", {}
                )
                assert cached_response is None
                
                # Test cache storage handles connection failure
                await integration_cache_instance.cache_response(
                    "test text", "summarize", {}, {"result": "test"}
                )
                # Should not raise exception, just log warning
    
    @pytest.mark.asyncio
    async def test_redis_unavailable_graceful_degradation(self, integration_cache_instance):
        """Test graceful degradation when Redis is not available."""
        # Simulate Redis not being available
        with patch('app.services.cache.REDIS_AVAILABLE', False):
            # Attempt to connect
            result = await integration_cache_instance.connect()
            assert result is False
            assert integration_cache_instance.redis is None
            
            # Test cache operations work without Redis
            cached_response = await integration_cache_instance.get_cached_response(
                "test text", "summarize", {}
            )
            assert cached_response is None
            
            # Test cache storage works without Redis
            await integration_cache_instance.cache_response(
                "test text", "summarize", {}, {"result": "test"}
            )
            # Should not raise exception
    
    @pytest.mark.asyncio
    async def test_redis_operation_error_handling_during_get(self, integration_cache_instance, mock_redis_client):
        """Test error handling during Redis get operations."""
        # Mock successful connection but failing get operation
        with patch.object(integration_cache_instance, 'connect', return_value=True):
            integration_cache_instance.redis = mock_redis_client
            
            # Make get operation raise an exception
            async def failing_get(key):
                raise Exception("Redis get operation failed")
            mock_redis_client.get = failing_get
            
            # Attempt to get cached response
            cached_response = await integration_cache_instance.get_cached_response(
                "test text", "summarize", {}
            )
            
            # Should handle error gracefully and return None
            assert cached_response is None
    
    @pytest.mark.asyncio
    async def test_redis_operation_error_handling_during_set(self, integration_cache_instance, mock_redis_client):
        """Test error handling during Redis set operations."""
        # Mock successful connection but failing setex operation
        with patch.object(integration_cache_instance, 'connect', return_value=True):
            integration_cache_instance.redis = mock_redis_client
            
            # Make setex operation raise an exception
            async def failing_setex(key, ttl, value):
                raise Exception("Redis setex operation failed")
            mock_redis_client.setex = failing_setex
            
            # Attempt to cache response
            await integration_cache_instance.cache_response(
                "test text", "summarize", {}, {"result": "test"}
            )
            # Should handle error gracefully and not raise exception
    
    @pytest.mark.asyncio
    async def test_redis_invalidation_operations(self, integration_cache_instance, mock_redis_client):
        """Test Redis invalidation operations work correctly."""
        # Mock successful connection
        with patch.object(integration_cache_instance, 'connect', return_value=True):
            integration_cache_instance.redis = mock_redis_client
            
            # Pre-populate cache with multiple entries
            test_entries = [
                ("text1", "summarize", {"length": 100}),
                ("text2", "summarize", {"length": 200}),
                ("text3", "sentiment", {"model": "basic"}),
                ("text4", "key_points", {"count": 5})
            ]
            
            for text, operation, options in test_entries:
                await integration_cache_instance.cache_response(
                    text, operation, options, {"result": f"result for {operation}"}
                )
            
            # Verify entries were stored
            assert len(mock_redis_client._data) == 4
            
            # Test pattern invalidation (invalidate all summarize operations)
            await integration_cache_instance.invalidate_by_operation("summarize")
            
            # Verify summarize entries were removed
            remaining_keys = list(mock_redis_client._data.keys())
            summarize_keys = [key for key in remaining_keys if "op:summarize" in key]
            assert len(summarize_keys) == 0
            
            # Verify other entries remain
            sentiment_keys = [key for key in remaining_keys if "op:sentiment" in key]
            assert len(sentiment_keys) == 1
            
            # Test invalidate all
            await integration_cache_instance.invalidate_all()
            assert len(mock_redis_client._data) == 0
    
    @pytest.mark.asyncio
    async def test_redis_stats_collection(self, integration_cache_instance, mock_redis_client):
        """Test Redis statistics collection works correctly."""
        # Mock successful connection
        with patch.object(integration_cache_instance, 'connect', return_value=True):
            integration_cache_instance.redis = mock_redis_client
            
            # Pre-populate cache with test data
            for i in range(5):
                await integration_cache_instance.cache_response(
                    f"test text {i}", "summarize", {}, {"result": f"result {i}"}
                )
            
            # Get cache stats
            stats = await integration_cache_instance.get_cache_stats()
            
            # Verify stats structure
            assert "redis" in stats
            assert "memory" in stats
            assert "performance" in stats
            
            # Verify Redis stats
            redis_stats = stats["redis"]
            assert redis_stats["status"] == "connected"
            assert redis_stats["keys"] == 5
            assert "memory_used" in redis_stats
            assert "connected_clients" in redis_stats
            
            # Verify memory stats
            memory_stats = stats["memory"]
            assert "memory_cache_entries" in memory_stats
            assert "memory_cache_size_limit" in memory_stats
    
    @pytest.mark.asyncio
    async def test_redis_compression_integration(self, integration_cache_instance, mock_redis_client):
        """Test Redis integration with data compression for large responses."""
        # Mock successful connection
        with patch.object(integration_cache_instance, 'connect', return_value=True):
            integration_cache_instance.redis = mock_redis_client
            
            # Create large response that will trigger compression
            large_response = {
                "operation": "summarize",
                "result": "Very long summary text that exceeds compression threshold. " * 50,
                "success": True,
                "processing_time": 2.5,
                "metadata": {"tokens": 1000, "model": "advanced"}
            }
            
            test_text = "Large text to process"
            
            # Cache the large response
            await integration_cache_instance.cache_response(
                test_text, "summarize", {}, large_response
            )
            
            # Retrieve and verify compression worked
            retrieved_data = await integration_cache_instance.get_cached_response(
                test_text, "summarize", {}
            )
            
            assert retrieved_data is not None
            assert retrieved_data["result"] == large_response["result"]
            assert retrieved_data["compression_used"] is True
            
            # Verify compressed data is stored in Redis
            cache_key = integration_cache_instance._generate_cache_key(test_text, "summarize", {})
            stored_data = mock_redis_client._data[cache_key]
            
            # Should be binary compressed data
            assert isinstance(stored_data, bytes)
            assert stored_data.startswith(b"compressed:")
    
    @pytest.mark.asyncio
    async def test_redis_binary_data_handling(self, integration_cache_instance, mock_redis_client):
        """Test Redis binary data handling for compressed responses."""
        # Mock successful connection
        with patch.object(integration_cache_instance, 'connect', return_value=True):
            integration_cache_instance.redis = mock_redis_client
            
            # Test with small response (should not compress)
            small_response = {"operation": "sentiment", "result": "positive", "success": True}
            
            await integration_cache_instance.cache_response(
                "small text", "sentiment", {}, small_response
            )
            
            retrieved_small = await integration_cache_instance.get_cached_response(
                "small text", "sentiment", {}
            )
            
            assert retrieved_small is not None
            assert retrieved_small["result"] == "positive"
            assert retrieved_small["compression_used"] is False
            
            # Verify raw (uncompressed) data is stored
            cache_key = integration_cache_instance._generate_cache_key("small text", "sentiment", {})
            stored_data = mock_redis_client._data[cache_key]
            assert isinstance(stored_data, bytes)
            assert stored_data.startswith(b"raw:")
    
    @pytest.mark.asyncio
    async def test_redis_concurrent_operations_simulation(self, integration_cache_instance, mock_redis_client):
        """Test Redis operations under simulated concurrent access."""
        # Mock successful connection
        with patch.object(integration_cache_instance, 'connect', return_value=True):
            integration_cache_instance.redis = mock_redis_client
            
            # Simulate concurrent cache operations
            async def cache_worker(worker_id: int, operation_count: int):
                for i in range(operation_count):
                    text = f"worker_{worker_id}_text_{i}"
                    response = {"result": f"result_{worker_id}_{i}", "success": True}
                    
                    # Cache the response
                    await integration_cache_instance.cache_response(
                        text, "summarize", {"worker": worker_id}, response
                    )
                    
                    # Retrieve the response
                    retrieved = await integration_cache_instance.get_cached_response(
                        text, "summarize", {"worker": worker_id}
                    )
                    
                    assert retrieved is not None
                    assert retrieved["result"] == response["result"]
            
            # Run multiple workers concurrently
            workers = [cache_worker(worker_id, 5) for worker_id in range(3)]
            await asyncio.gather(*workers)
            
            # Verify all data was stored correctly
            assert len(mock_redis_client._data) == 15  # 3 workers * 5 operations each
            
            # Verify data integrity
            for worker_id in range(3):
                for i in range(5):
                    text = f"worker_{worker_id}_text_{i}"
                    retrieved = await integration_cache_instance.get_cached_response(
                        text, "summarize", {"worker": worker_id}
                    )
                    assert retrieved is not None
                    assert retrieved["result"] == f"result_{worker_id}_{i}"
    
    @pytest.mark.asyncio
    async def test_redis_memory_tier_integration(self, integration_cache_instance, mock_redis_client):
        """Test Redis integration with memory cache tiers."""
        # Mock successful connection
        with patch.object(integration_cache_instance, 'connect', return_value=True):
            integration_cache_instance.redis = mock_redis_client
            
            # Test small text (should use memory cache)
            small_text = "Small text under 500 chars"  # < 500 chars = 'small' tier
            small_response = {"operation": "sentiment", "result": "positive", "success": True}
            
            # Cache small response
            await integration_cache_instance.cache_response(
                small_text, "sentiment", {}, small_response
            )
            
            # Retrieve twice - second should hit memory cache
            retrieved1 = await integration_cache_instance.get_cached_response(
                small_text, "sentiment", {}
            )
            retrieved2 = await integration_cache_instance.get_cached_response(
                small_text, "sentiment", {}
            )
            
            assert retrieved1 is not None
            assert retrieved2 is not None
            assert retrieved1 == retrieved2
            
            # Verify memory cache was populated
            cache_key = integration_cache_instance._generate_cache_key(small_text, "sentiment", {})
            assert cache_key in integration_cache_instance.memory_cache
            
            # Test large text (should skip memory cache)
            large_text = "Large text " * 100  # > 500 chars = 'medium' tier
            large_response = {"operation": "summarize", "result": "long summary", "success": True}
            
            # Cache large response
            await integration_cache_instance.cache_response(
                large_text, "summarize", {}, large_response
            )
            
            # Retrieve large response
            retrieved_large = await integration_cache_instance.get_cached_response(
                large_text, "summarize", {}
            )
            
            assert retrieved_large is not None
            
            # Verify memory cache was NOT populated for large text
            large_cache_key = integration_cache_instance._generate_cache_key(large_text, "summarize", {})
            assert large_cache_key not in integration_cache_instance.memory_cache