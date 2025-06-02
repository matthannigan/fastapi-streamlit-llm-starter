"""Tests for AI response cache functionality."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import json
from datetime import datetime

from app.services.cache import AIResponseCache


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
            cached_data = json.loads(call_args[0][2])
            assert "cached_at" in cached_data
            assert cached_data["cache_hit"] is True
            assert cached_data["operation"] == "summarize"
    
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
            
            mock_redis.keys.assert_called_once_with("ai_cache:*test*")
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
            
            assert stats["status"] == "connected"
            assert "keys" in stats
            assert "memory_used" in stats
            assert "connected_clients" in stats
    
    @pytest.mark.asyncio
    async def test_cache_stats_unavailable(self, cache_instance):
        """Test cache stats when Redis unavailable."""
        with patch.object(cache_instance, 'connect', return_value=False):
            stats = await cache_instance.get_cache_stats()
            
            assert stats["status"] == "unavailable"
            assert stats["keys"] == 0
    
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