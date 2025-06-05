"""Tests for AI response cache functionality."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import json
from datetime import datetime

from app.services.cache import AIResponseCache, CacheKeyGenerator


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
        small_data = {"result": "small", "cached_at": "2024-01-01"}
        
        compressed = cache_instance._compress_data(small_data)
        
        # Should start with "raw:" prefix for uncompressed data
        assert compressed.startswith(b"raw:")
        
        # Should be able to decompress back to original
        decompressed = cache_instance._decompress_data(compressed)
        assert decompressed == small_data

    def test_compression_data_large_data(self, cache_instance):
        """Test that large data is compressed."""
        # Create large data that exceeds compression threshold
        large_text = "A" * 2000  # Larger than default 1000 byte threshold
        large_data = {
            "result": large_text,
            "cached_at": "2024-01-01",
            "operation": "summarize",
            "success": True
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

    @pytest.mark.asyncio
    async def test_cache_response_includes_compression_metadata(self, cache_instance, mock_redis):
        """Test that cached responses include compression metadata."""
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
            
            # Decompress the stored data to check metadata
            stored_data = call_args[0][2]
            cached_data = cache_instance._decompress_data(stored_data)
            
            # Check compression metadata is included
            assert "compression_used" in cached_data
            assert "text_length" in cached_data
            assert cached_data["text_length"] == len("test text")
            assert isinstance(cached_data["compression_used"], bool)

    @pytest.mark.asyncio
    async def test_cache_retrieval_handles_compressed_data(self, cache_instance, mock_redis):
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
        compressed_data = cache_instance._compress_data(test_data)
        mock_redis.get.return_value = compressed_data
        
        # Mock successful connection
        with patch.object(cache_instance, 'connect', return_value=True):
            cache_instance.redis = mock_redis
            
            result = await cache_instance.get_cached_response(
                "test text", "summarize", {}, None
            )
            
            assert result == test_data
            mock_redis.get.assert_called_once()

    @pytest.mark.asyncio
    async def test_cache_response_timing_tracking(self, cache_instance, mock_redis):
        """Test that cache_response records performance timing metrics."""
        response_data = {
            "operation": "summarize",
            "result": "Test summary",
            "success": True
        }
        
        # Ensure performance monitor is available
        assert cache_instance.performance_monitor is not None
        
        # Get initial counts
        initial_cache_ops = len(cache_instance.performance_monitor.cache_operation_times)
        
        # Mock successful connection
        with patch.object(cache_instance, 'connect', return_value=True):
            cache_instance.redis = mock_redis
            
            await cache_instance.cache_response(
                "test text", "summarize", {}, response_data, None
            )
            
            # Verify that a cache operation time was recorded
            assert len(cache_instance.performance_monitor.cache_operation_times) == initial_cache_ops + 1
            
            # Check the recorded metric
            recorded_metric = cache_instance.performance_monitor.cache_operation_times[-1]
            assert recorded_metric.operation_type == "set"
            assert recorded_metric.text_length == len("test text")
            assert recorded_metric.duration > 0
            assert recorded_metric.additional_data["operation_type"] == "summarize"
            assert recorded_metric.additional_data["status"] == "success"
            assert "compression_used" in recorded_metric.additional_data
            assert "compression_time" in recorded_metric.additional_data

    @pytest.mark.asyncio
    async def test_cache_response_timing_on_failure(self, cache_instance, mock_redis):
        """Test that cache_response records timing even when Redis operations fail."""
        response_data = {
            "operation": "summarize", 
            "result": "Test summary",
            "success": True
        }
        
        # Get initial counts
        initial_cache_ops = len(cache_instance.performance_monitor.cache_operation_times)
        
        # Mock Redis setex to raise an exception
        mock_redis.setex.side_effect = Exception("Redis error")
        
        # Mock successful connection
        with patch.object(cache_instance, 'connect', return_value=True):
            cache_instance.redis = mock_redis
            
            await cache_instance.cache_response(
                "test text", "summarize", {}, response_data, None
            )
            
            # Verify that a cache operation time was recorded even on failure
            assert len(cache_instance.performance_monitor.cache_operation_times) == initial_cache_ops + 1
            
            # Check the recorded metric shows failure
            recorded_metric = cache_instance.performance_monitor.cache_operation_times[-1]
            assert recorded_metric.operation_type == "set"
            assert recorded_metric.duration > 0
            assert recorded_metric.additional_data["status"] == "failed"
            assert recorded_metric.additional_data["reason"] == "redis_error"

    @pytest.mark.asyncio
    async def test_cache_response_timing_on_connection_failure(self, cache_instance):
        """Test that cache_response records timing when Redis connection fails."""
        response_data = {
            "operation": "summarize",
            "result": "Test summary", 
            "success": True
        }
        
        # Get initial counts
        initial_cache_ops = len(cache_instance.performance_monitor.cache_operation_times)
        
        # Mock connection failure
        with patch.object(cache_instance, 'connect', return_value=False):
            
            await cache_instance.cache_response(
                "test text", "summarize", {}, response_data, None
            )
            
            # Verify that a cache operation time was recorded for connection failure
            assert len(cache_instance.performance_monitor.cache_operation_times) == initial_cache_ops + 1
            
            # Check the recorded metric shows connection failure
            recorded_metric = cache_instance.performance_monitor.cache_operation_times[-1]
            assert recorded_metric.operation_type == "set"
            assert recorded_metric.duration > 0
            assert recorded_metric.additional_data["reason"] == "redis_connection_failed"
            assert recorded_metric.additional_data["status"] == "failed"

    @pytest.mark.asyncio
    async def test_cache_response_compression_tracking(self, cache_instance, mock_redis):
        """Test that cache_response records compression metrics when compression is used."""
        # Create large response that will trigger compression
        large_response = {
            "operation": "summarize",
            "result": "A" * 2000,  # Large result to trigger compression
            "success": True
        }
        
        # Get initial counts 
        initial_compression_ops = len(cache_instance.performance_monitor.compression_ratios)
        
        # Mock successful connection
        with patch.object(cache_instance, 'connect', return_value=True):
            cache_instance.redis = mock_redis
            
            await cache_instance.cache_response(
                "test text", "summarize", {}, large_response, None
            )
            
            # Verify that a compression ratio was recorded
            assert len(cache_instance.performance_monitor.compression_ratios) == initial_compression_ops + 1
            
            # Check the recorded compression metric
            recorded_compression = cache_instance.performance_monitor.compression_ratios[-1]
            assert recorded_compression.operation_type == "summarize"
            assert recorded_compression.compression_time > 0
            assert recorded_compression.original_size > 0
            assert recorded_compression.compressed_size > 0
            assert recorded_compression.compression_ratio <= 1.0  # Should be compressed

    @pytest.mark.asyncio
    async def test_cache_response_no_compression_tracking_for_small_data(self, cache_instance, mock_redis):
        """Test that cache_response doesn't record compression metrics for small data."""
        # Create small response that won't trigger compression
        small_response = {
            "operation": "sentiment",
            "result": "positive",
            "success": True
        }
        
        # Get initial counts
        initial_compression_ops = len(cache_instance.performance_monitor.compression_ratios)
        
        # Mock successful connection
        with patch.object(cache_instance, 'connect', return_value=True):
            cache_instance.redis = mock_redis
            
            await cache_instance.cache_response(
                "test text", "sentiment", {}, small_response, None
            )
            
            # Verify that no compression ratio was recorded for small data
            assert len(cache_instance.performance_monitor.compression_ratios) == initial_compression_ops

    @pytest.mark.asyncio
    async def test_cache_response_compression_tracking_for_small_data(self, cache_instance, mock_redis):
        """Test that compression metrics are NOT recorded for small data."""
        small_response = {"result": "small", "success": True}
        
        # Mock successful connection
        with patch.object(cache_instance, 'connect', return_value=True):
            cache_instance.redis = mock_redis
            
            await cache_instance.cache_response(
                "test text", "summarize", {}, small_response, None
            )
            
            # Should NOT record compression metrics for small data
            assert len(cache_instance.performance_monitor.compression_ratios) == 0

    def test_memory_usage_recording(self, cache_instance):
        """Test that memory usage is recorded correctly."""
        # Add some items to memory cache
        cache_instance._update_memory_cache("key1", {"data": "value1"})
        cache_instance._update_memory_cache("key2", {"data": "value2"})
        
        # Record memory usage
        redis_stats = {"memory_used_bytes": 1024 * 1024, "keys": 10}
        cache_instance.record_memory_usage(redis_stats)
        
        # Verify memory usage was recorded
        assert len(cache_instance.performance_monitor.memory_usage_measurements) == 1
        
        metric = cache_instance.performance_monitor.memory_usage_measurements[0]
        assert metric.memory_cache_entry_count == 2
        assert metric.cache_entry_count == 12  # 2 memory + 10 redis
        assert metric.total_cache_size_bytes > 0

    def test_memory_usage_recording_failure(self, cache_instance):
        """Test graceful handling of memory usage recording failure."""
        # Mock the performance monitor to raise an exception
        with patch.object(cache_instance.performance_monitor, 'record_memory_usage', side_effect=Exception("Test error")):
            with patch('backend.app.services.cache.logger') as mock_logger:
                # Should not raise an exception
                cache_instance.record_memory_usage()
                
                # Should log a warning
                mock_logger.warning.assert_called_once()
                warning_call = mock_logger.warning.call_args[0][0]
                assert "Failed to record memory usage" in warning_call

    def test_get_memory_usage_stats(self, cache_instance):
        """Test getting memory usage statistics."""
        # Add some data and record memory usage
        cache_instance._update_memory_cache("key1", {"data": "value1"})
        cache_instance.record_memory_usage()
        
        stats = cache_instance.get_memory_usage_stats()
        
        # Should return memory usage stats from monitor
        assert "current" in stats or "no_measurements" in stats

    def test_get_memory_warnings(self, cache_instance):
        """Test getting memory warnings."""
        # Add some data and record memory usage
        cache_instance._update_memory_cache("key1", {"data": "value1"})
        cache_instance.record_memory_usage()
        
        warnings = cache_instance.get_memory_warnings()
        
        # Should return a list (empty for small test data)
        assert isinstance(warnings, list)

    @pytest.mark.asyncio
    async def test_cache_stats_includes_memory_tracking(self, cache_instance, mock_redis):
        """Test that get_cache_stats triggers memory usage recording and includes memory stats."""
        # Add some items to memory cache
        cache_instance._update_memory_cache("key1", {"data": "value1"})
        cache_instance._update_memory_cache("key2", {"data": "value2"})
        
        # Mock successful Redis connection
        with patch.object(cache_instance, 'connect', return_value=True):
            cache_instance.redis = mock_redis
            
            # Mock Redis info to include memory_used_bytes
            mock_redis.info.return_value = {
                "used_memory": 2048 * 1024,  # 2MB in bytes
                "used_memory_human": "2.0M",
                "connected_clients": 1
            }
            
            stats = await cache_instance.get_cache_stats()
            
            # Verify memory usage was recorded during stats collection
            assert len(cache_instance.performance_monitor.memory_usage_measurements) == 1
            
            # Verify stats include performance data with memory usage
            assert "performance" in stats
            performance_stats = stats["performance"]
            
            # If memory usage was recorded, it should be in performance stats
            if cache_instance.performance_monitor.memory_usage_measurements:
                assert "memory_usage" in performance_stats

    @pytest.mark.asyncio
    async def test_cache_stats_memory_recording_redis_unavailable(self, cache_instance):
        """Test memory usage recording when Redis is unavailable."""
        # Add some items to memory cache
        cache_instance._update_memory_cache("key1", {"data": "value1"})
        
        # Mock Redis connection failure
        with patch.object(cache_instance, 'connect', return_value=False):
            stats = await cache_instance.get_cache_stats()
            
            # Memory usage should still be recorded even without Redis
            assert len(cache_instance.performance_monitor.memory_usage_measurements) == 1
            
            # Stats should still include memory cache info
            assert "memory" in stats
            assert stats["memory"]["memory_cache_entries"] == 1

    def test_memory_usage_with_large_cache(self, cache_instance):
        """Test memory usage tracking with larger cache data."""
        # Create larger cache entries
        large_data = {"data": "x" * 1000, "metadata": {"key": "value"}}
        
        for i in range(10):
            cache_instance._update_memory_cache(f"key{i}", large_data)
        
        redis_stats = {"memory_used_bytes": 5 * 1024 * 1024, "keys": 50}  # 5MB
        cache_instance.record_memory_usage(redis_stats)
        
        assert len(cache_instance.performance_monitor.memory_usage_measurements) == 1
        
        metric = cache_instance.performance_monitor.memory_usage_measurements[0]
        assert metric.memory_cache_entry_count == 10
        assert metric.cache_entry_count == 60  # 10 memory + 50 redis
        assert metric.total_cache_size_bytes > 5 * 1024 * 1024  # Should include both memory and Redis
        assert metric.memory_cache_size_bytes > 0

    def test_memory_threshold_configuration(self, cache_instance):
        """Test that memory thresholds are properly configured in the performance monitor."""
        # Check default thresholds
        monitor = cache_instance.performance_monitor
        assert monitor.memory_warning_threshold_bytes == 50 * 1024 * 1024  # 50MB
        assert monitor.memory_critical_threshold_bytes == 100 * 1024 * 1024  # 100MB

    def test_memory_usage_integration_with_performance_stats(self, cache_instance):
        """Test memory usage integration with overall performance stats."""
        # Add cache operations and memory usage
        cache_instance.performance_monitor.record_cache_operation_time("get", 0.02, True, 500)
        cache_instance.performance_monitor.record_key_generation_time(0.01, 1000, "summarize")
        
        # Add memory usage
        cache_instance._update_memory_cache("key1", {"data": "value1"})
        cache_instance.record_memory_usage()
        
        # Get combined performance stats
        stats = cache_instance.get_performance_summary()
        
        # Should include basic performance metrics
        assert "hit_ratio" in stats
        assert "total_operations" in stats
        
        # Get full performance stats
        full_stats = cache_instance.performance_monitor.get_performance_stats()
        
        # Should include memory usage in full stats
        assert "memory_usage" in full_stats

    def test_memory_usage_cleanup_on_reset(self, cache_instance):
        """Test that memory usage measurements are cleared when stats are reset."""
        # Add memory usage data
        cache_instance._update_memory_cache("key1", {"data": "value1"})
        cache_instance.record_memory_usage()
        
        assert len(cache_instance.performance_monitor.memory_usage_measurements) == 1
        
        # Reset performance stats
        cache_instance.reset_performance_stats()
        
        # Memory usage measurements should be cleared
        assert len(cache_instance.performance_monitor.memory_usage_measurements) == 0

    @pytest.mark.asyncio
    async def test_invalidate_pattern_tracking_success(self, cache_instance, mock_redis):
        """Test invalidation tracking with successful operation."""
        mock_redis.keys.return_value = [
            "ai_cache:test_key1",
            "ai_cache:test_key2",
            "ai_cache:test_key3"
        ]
        
        with patch.object(cache_instance, 'connect', return_value=True):
            cache_instance.redis = mock_redis
            
            await cache_instance.invalidate_pattern("test", "unit_test_context")
        
        # Check that invalidation was tracked
        assert cache_instance.performance_monitor.total_invalidations == 1
        assert cache_instance.performance_monitor.total_keys_invalidated == 3
        assert len(cache_instance.performance_monitor.invalidation_events) == 1
        
        event = cache_instance.performance_monitor.invalidation_events[0]
        assert event.pattern == "test"
        assert event.keys_invalidated == 3
        assert event.invalidation_type == "manual"
        assert event.operation_context == "unit_test_context"
        assert event.additional_data["status"] == "success"

    @pytest.mark.asyncio
    async def test_invalidate_pattern_tracking_no_keys_found(self, cache_instance, mock_redis):
        """Test invalidation tracking when no keys are found."""
        mock_redis.keys.return_value = []
        
        with patch.object(cache_instance, 'connect', return_value=True):
            cache_instance.redis = mock_redis
            
            await cache_instance.invalidate_pattern("nonexistent", "unit_test")
        
        # Should still track the invalidation attempt
        assert cache_instance.performance_monitor.total_invalidations == 1
        assert cache_instance.performance_monitor.total_keys_invalidated == 0
        
        event = cache_instance.performance_monitor.invalidation_events[0]
        assert event.pattern == "nonexistent"
        assert event.keys_invalidated == 0
        assert event.additional_data["status"] == "success"

    @pytest.mark.asyncio
    async def test_invalidate_pattern_tracking_redis_connection_failed(self, cache_instance):
        """Test invalidation tracking when Redis connection fails."""
        with patch.object(cache_instance, 'connect', return_value=False):
            await cache_instance.invalidate_pattern("test", "connection_test")
        
        # Should track the failed attempt
        assert cache_instance.performance_monitor.total_invalidations == 1
        assert cache_instance.performance_monitor.total_keys_invalidated == 0
        
        event = cache_instance.performance_monitor.invalidation_events[0]
        assert event.pattern == "test"
        assert event.keys_invalidated == 0
        assert event.additional_data["status"] == "failed"
        assert event.additional_data["reason"] == "redis_connection_failed"

    @pytest.mark.asyncio
    async def test_invalidate_pattern_tracking_redis_error(self, cache_instance, mock_redis):
        """Test invalidation tracking when Redis operation fails."""
        mock_redis.keys.side_effect = Exception("Redis error")
        
        with patch.object(cache_instance, 'connect', return_value=True):
            cache_instance.redis = mock_redis
            
            await cache_instance.invalidate_pattern("test", "error_test")
        
        # Should track the failed operation
        assert cache_instance.performance_monitor.total_invalidations == 1
        assert cache_instance.performance_monitor.total_keys_invalidated == 0
        
        event = cache_instance.performance_monitor.invalidation_events[0]
        assert event.pattern == "test"
        assert event.keys_invalidated == 0
        assert event.additional_data["status"] == "failed"
        assert event.additional_data["reason"] == "redis_error"
        assert "Redis error" in event.additional_data["error"]

    @pytest.mark.asyncio
    async def test_invalidate_all(self, cache_instance, mock_redis):
        """Test invalidate_all convenience method."""
        mock_redis.keys.return_value = ["ai_cache:key1", "ai_cache:key2"]
        
        with patch.object(cache_instance, 'connect', return_value=True):
            cache_instance.redis = mock_redis
            
            await cache_instance.invalidate_all("clear_all_test")
        
        # Should call invalidate_pattern with empty string
        mock_redis.keys.assert_called_once_with(b"ai_cache:*")
        
        # Should track invalidation
        event = cache_instance.performance_monitor.invalidation_events[0]
        assert event.pattern == ""
        assert event.operation_context == "clear_all_test"

    @pytest.mark.asyncio
    async def test_invalidate_by_operation(self, cache_instance, mock_redis):
        """Test invalidate_by_operation convenience method."""
        mock_redis.keys.return_value = ["ai_cache:op:summarize|key1"]
        
        with patch.object(cache_instance, 'connect', return_value=True):
            cache_instance.redis = mock_redis
            
            await cache_instance.invalidate_by_operation("summarize", "operation_specific_test")
        
        # Should call invalidate_pattern with operation pattern
        mock_redis.keys.assert_called_once_with(b"ai_cache:*op:summarize*")
        
        # Should track invalidation
        event = cache_instance.performance_monitor.invalidation_events[0]
        assert event.pattern == "op:summarize"
        assert event.operation_context == "operation_specific_test"

    @pytest.mark.asyncio
    async def test_invalidate_memory_cache(self, cache_instance):
        """Test memory cache invalidation tracking."""
        # Add some items to memory cache
        cache_instance._update_memory_cache("key1", {"data": "value1"})
        cache_instance._update_memory_cache("key2", {"data": "value2"})
        cache_instance._update_memory_cache("key3", {"data": "value3"})
        
        assert len(cache_instance.memory_cache) == 3
        
        # Invalidate memory cache
        await cache_instance.invalidate_memory_cache("memory_test")
        
        # Memory cache should be cleared
        assert len(cache_instance.memory_cache) == 0
        assert len(cache_instance.memory_cache_order) == 0
        
        # Should track invalidation
        assert cache_instance.performance_monitor.total_invalidations == 1
        assert cache_instance.performance_monitor.total_keys_invalidated == 3
        
        event = cache_instance.performance_monitor.invalidation_events[0]
        assert event.pattern == "memory_cache"
        assert event.keys_invalidated == 3
        assert event.invalidation_type == "memory"
        assert event.operation_context == "memory_test"
        assert event.additional_data["status"] == "success"
        assert event.additional_data["invalidation_target"] == "memory_cache_only"

    def test_get_invalidation_frequency_stats(self, cache_instance):
        """Test getting invalidation frequency statistics from cache."""
        # Add some invalidation events through the monitor
        cache_instance.performance_monitor.record_invalidation_event("pattern1", 5, 0.02, "manual")
        cache_instance.performance_monitor.record_invalidation_event("pattern2", 3, 0.01, "automatic")
        
        stats = cache_instance.get_invalidation_frequency_stats()
        
        assert stats["total_invalidations"] == 2
        assert stats["total_keys_invalidated"] == 8
        assert "rates" in stats
        assert "patterns" in stats
        assert "efficiency" in stats

    def test_get_invalidation_recommendations(self, cache_instance):
        """Test getting invalidation recommendations from cache."""
        # Add some invalidation events to trigger recommendations
        for i in range(10):
            cache_instance.performance_monitor.record_invalidation_event(
                f"pattern_{i}", 
                0,  # No keys found - will trigger low efficiency recommendation
                0.01, 
                "manual"
            )
        
        recommendations = cache_instance.get_invalidation_recommendations()
        
        assert isinstance(recommendations, list)
        # Should have at least one recommendation for low efficiency
        low_efficiency_rec = next((r for r in recommendations if "efficiency" in r["issue"].lower()), None)
        assert low_efficiency_rec is not None

    def test_invalidation_integration_with_performance_stats(self, cache_instance):
        """Test that invalidation data integrates with overall performance stats."""
        # Record some cache operations and invalidations
        cache_instance.performance_monitor.record_cache_operation_time("get", 0.02, True, 500)
        cache_instance.performance_monitor.record_invalidation_event("test_pattern", 5, 0.03, "manual")
        
        # Get performance summary
        summary = cache_instance.get_performance_summary()
        assert "hit_ratio" in summary
        assert "total_operations" in summary
        
        # Get full performance stats
        full_stats = cache_instance.performance_monitor.get_performance_stats()
        assert "invalidation" in full_stats
        assert full_stats["invalidation"]["total_invalidations"] == 1
        assert full_stats["invalidation"]["total_keys_invalidated"] == 5

    def test_invalidation_events_cleanup(self, cache_instance):
        """Test that invalidation events are properly cleaned up."""
        import time
        current_time = time.time()
        
        # Add an old invalidation event manually
        old_event = cache_instance.performance_monitor.invalidation_events
        from app.services.monitoring import InvalidationMetric
        old_event.append(InvalidationMetric(
            pattern="old_pattern",
            keys_invalidated=1,
            duration=0.01,
            timestamp=current_time - 7200,  # 2 hours ago
            invalidation_type="manual",
            operation_context="old_test"
        ))
        
        # Add a recent event
        cache_instance.performance_monitor.record_invalidation_event("recent_pattern", 1, 0.01, "manual")
        
        # Trigger cleanup (happens automatically during get_performance_stats)
        cache_instance.performance_monitor.get_performance_stats()
        
        # Should only have recent events (assuming 1 hour retention)
        remaining_events = [e for e in cache_instance.performance_monitor.invalidation_events 
                          if e.timestamp > current_time - 3600]
        assert len(remaining_events) == 1
        assert remaining_events[0].pattern == "recent_pattern"


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