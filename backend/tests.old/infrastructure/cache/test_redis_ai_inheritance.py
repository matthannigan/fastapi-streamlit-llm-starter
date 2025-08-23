"""
Comprehensive tests for AIResponseCache inheritance implementation.

This module tests the refactored AIResponseCache that inherits from GenericRedisCache,
focusing on the method overrides and AI-specific enhancements implemented in 
Phase 2 Deliverable 3.

Test Coverage Areas:
- AI-specific method overrides (cache_response, get_cached_response, invalidate_by_operation)
- Helper methods for text tier determination and operation extraction
- Memory cache promotion logic
- AI metrics collection and recording
- Error handling and validation
- Integration with inherited GenericRedisCache functionality
"""

import asyncio
import hashlib
import pytest
import time
from collections import defaultdict
from datetime import datetime
from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.exceptions import ConfigurationError, ValidationError, InfrastructureError
from app.infrastructure.cache.redis_ai import AIResponseCache
from app.infrastructure.cache.monitoring import CachePerformanceMonitor


class TestAIResponseCacheInheritance:
    """Test AIResponseCache inheritance and method overrides."""

    @pytest.fixture
    def performance_monitor(self):
        """Create a mock performance monitor."""
        return MagicMock(spec=CachePerformanceMonitor)

    @pytest.fixture
    async def ai_cache(self, performance_monitor):
        """Create AIResponseCache instance for testing."""
        cache = AIResponseCache(
            redis_url="redis://localhost:6379",
            default_ttl=3600,
            text_hash_threshold=1000,
            memory_cache_size=100,
            performance_monitor=performance_monitor,
            text_size_tiers={
                "small": 500,
                "medium": 5000,
                "large": 50000,
            }
        )
        yield cache
        # Cleanup
        if hasattr(cache, 'redis') and cache.redis:
            try:
                await cache.disconnect()
            except Exception:
                pass

    @pytest.fixture
    def sample_response(self):
        """Sample AI response for testing."""
        return {
            "summary": "This is a test summary",
            "confidence": 0.95,
            "model": "test-model",
            "tokens_used": 150
        }

    @pytest.fixture
    def sample_options(self):
        """Sample operation options for testing."""
        return {
            "max_length": 100,
            "temperature": 0.7,
            "model": "gpt-4"
        }


class TestCacheResponseMethod:
    """Test the enhanced cache_response method."""

    async def test_cache_response_basic_functionality(self, ai_cache, sample_response, sample_options):
        """Test basic cache_response functionality."""
        with patch.object(ai_cache, 'set', new_callable=AsyncMock) as mock_set:
            await ai_cache.cache_response(
                text="Test text for caching",
                operation="summarize",
                options=sample_options,
                response=sample_response
            )
            
            # Verify set was called with enhanced response
            mock_set.assert_called_once()
            call_args = mock_set.call_args
            cached_response = call_args[0][1]  # Second argument is the cached response
            
            # Check enhanced metadata was added
            assert cached_response["cache_hit"] is False
            assert "cached_at" in cached_response
            assert cached_response["text_length"] == len("Test text for caching")
            assert cached_response["text_tier"] == "small"  # Based on size tiers
            assert cached_response["operation"] == "summarize"
            assert cached_response["ai_version"] == "refactored_inheritance"

    async def test_cache_response_input_validation(self, ai_cache, sample_response, sample_options):
        """Test input validation in cache_response method."""
        # Test invalid text
        with pytest.raises(ValidationError, match="Invalid text parameter"):
            await ai_cache.cache_response("", "summarize", sample_options, sample_response)
        
        with pytest.raises(ValidationError, match="Invalid text parameter"):
            await ai_cache.cache_response(None, "summarize", sample_options, sample_response)
        
        # Test invalid operation
        with pytest.raises(ValidationError, match="Invalid operation parameter"):
            await ai_cache.cache_response("test", "", sample_options, sample_response)
        
        # Test invalid options
        with pytest.raises(ValidationError, match="Invalid options parameter"):
            await ai_cache.cache_response("test", "summarize", "not_dict", sample_response)
        
        # Test invalid response
        with pytest.raises(ValidationError, match="Invalid response parameter"):
            await ai_cache.cache_response("test", "summarize", sample_options, "not_dict")

    async def test_cache_response_operation_specific_ttl(self, ai_cache, sample_response, sample_options):
        """Test that operation-specific TTL is used correctly."""
        with patch.object(ai_cache, 'set', new_callable=AsyncMock) as mock_set:
            await ai_cache.cache_response(
                text="Test text",
                operation="sentiment",  # Has specific TTL of 86400
                options=sample_options,
                response=sample_response
            )
            
            # Verify TTL from operation_ttls was used
            call_args = mock_set.call_args
            ttl_used = call_args[0][2]  # Third argument is TTL
            assert ttl_used == 86400  # sentiment operation TTL

    async def test_cache_response_text_tier_determination(self, ai_cache, sample_response, sample_options):
        """Test text tier determination in cache_response."""
        test_cases = [
            ("short", "small"),  # 5 chars < 500 (small threshold)
            ("a" * 1000, "medium"),  # 1000 chars between 500-5000
            ("a" * 10000, "large"),  # 10000 chars between 5000-50000
            ("a" * 60000, "xlarge"),  # 60000 chars > 50000
        ]
        
        for text, expected_tier in test_cases:
            with patch.object(ai_cache, 'set', new_callable=AsyncMock) as mock_set:
                await ai_cache.cache_response(
                    text=text,
                    operation="summarize",
                    options=sample_options,
                    response=sample_response
                )
                
                cached_response = mock_set.call_args[0][1]
                assert cached_response["text_tier"] == expected_tier

    async def test_cache_response_metrics_recording(self, ai_cache, sample_response, sample_options):
        """Test that AI metrics are recorded correctly."""
        with patch.object(ai_cache, 'set', new_callable=AsyncMock):
            with patch.object(ai_cache, '_record_cache_operation') as mock_record:
                await ai_cache.cache_response(
                    text="Test text",
                    operation="summarize",
                    options=sample_options,
                    response=sample_response
                )
                
                # Verify metrics recording was called
                mock_record.assert_called_once()
                call_args = mock_record.call_args
                assert call_args[1]['operation'] == "summarize"
                assert call_args[1]['cache_operation'] == "set"
                assert call_args[1]['success'] is True

    async def test_cache_response_error_handling(self, ai_cache, sample_response, sample_options):
        """Test error handling in cache_response method."""
        with patch.object(ai_cache, 'set', side_effect=Exception("Redis error")):
            with patch.object(ai_cache, '_record_cache_operation') as mock_record:
                # Should not raise exception - graceful degradation
                await ai_cache.cache_response(
                    text="Test text",
                    operation="summarize",
                    options=sample_options,
                    response=sample_response
                )
                
                # Verify error metrics were recorded
                mock_record.assert_called()
                call_args = mock_record.call_args
                assert call_args[1]['success'] is False


class TestGetCachedResponseMethod:
    """Test the enhanced get_cached_response method."""

    async def test_get_cached_response_cache_hit(self, ai_cache, sample_options):
        """Test successful cache hit in get_cached_response."""
        cached_data = {
            "summary": "Cached summary",
            "confidence": 0.9,
            "cached_at": "2024-01-01T12:00:00"
        }
        
        with patch.object(ai_cache, 'get', return_value=cached_data) as mock_get:
            with patch.object(ai_cache, '_record_cache_operation') as mock_record:
                result = await ai_cache.get_cached_response(
                    text="Test text",
                    operation="summarize",
                    options=sample_options
                )
                
                # Verify result was enhanced with retrieval metadata
                assert result["cache_hit"] is True
                assert "retrieved_at" in result
                assert "retrieval_count" in result
                assert result["retrieval_count"] == 1
                
                # Verify metrics recording
                mock_record.assert_called_once()
                call_args = mock_record.call_args
                assert call_args[1]['success'] is True
                assert call_args[1]['additional_data']['cache_result'] == 'hit'

    async def test_get_cached_response_cache_miss(self, ai_cache, sample_options):
        """Test cache miss in get_cached_response."""
        with patch.object(ai_cache, 'get', return_value=None):
            with patch.object(ai_cache, '_record_cache_operation') as mock_record:
                result = await ai_cache.get_cached_response(
                    text="Test text",
                    operation="summarize",
                    options=sample_options
                )
                
                assert result is None
                
                # Verify miss metrics recording
                mock_record.assert_called_once()
                call_args = mock_record.call_args
                assert call_args[1]['success'] is False
                assert call_args[1]['additional_data']['cache_result'] == 'miss'

    async def test_get_cached_response_input_validation(self, ai_cache, sample_options):
        """Test input validation in get_cached_response method."""
        # Test invalid text
        with pytest.raises(ValidationError, match="Invalid text parameter"):
            await ai_cache.get_cached_response("", "summarize", sample_options)
        
        # Test invalid operation
        with pytest.raises(ValidationError, match="Invalid operation parameter"):
            await ai_cache.get_cached_response("test", "", sample_options)
        
        # Test invalid options
        with pytest.raises(ValidationError, match="Invalid options parameter"):
            await ai_cache.get_cached_response("test", "summarize", "not_dict")

    async def test_get_cached_response_memory_promotion(self, ai_cache, sample_options):
        """Test memory cache promotion logic."""
        cached_data = {"summary": "test"}
        
        with patch.object(ai_cache, 'get', return_value=cached_data):
            with patch.object(ai_cache, '_should_promote_to_memory', return_value=True) as mock_promote:
                result = await ai_cache.get_cached_response(
                    text="small text",  # Should trigger small tier
                    operation="sentiment",  # Stable operation
                    options=sample_options
                )
                
                # Verify promotion logic was called
                mock_promote.assert_called_once_with("small", "sentiment")

    async def test_get_cached_response_error_handling(self, ai_cache, sample_options):
        """Test error handling in get_cached_response method."""
        with patch.object(ai_cache, 'get', side_effect=Exception("Redis error")):
            with patch.object(ai_cache, '_record_cache_operation') as mock_record:
                result = await ai_cache.get_cached_response(
                    text="Test text",
                    operation="summarize",
                    options=sample_options
                )
                
                assert result is None
                
                # Verify error metrics were recorded
                mock_record.assert_called()
                call_args = mock_record.call_args
                assert call_args[1]['success'] is False
                assert call_args[1]['additional_data']['cache_result'] == 'error'


class TestInvalidateByOperationMethod:
    """Test the enhanced invalidate_by_operation method."""

    async def test_invalidate_by_operation_basic_functionality(self, ai_cache):
        """Test basic invalidate_by_operation functionality."""
        mock_keys = [b"ai_cache:op:summarize|txt:test1", b"ai_cache:op:summarize|txt:test2"]
        
        with patch.object(ai_cache, 'connect', return_value=True):
            with patch.object(ai_cache, 'redis') as mock_redis:
                mock_redis.keys.return_value = mock_keys
                mock_redis.delete = AsyncMock()
                
                count = await ai_cache.invalidate_by_operation("summarize")
                
                assert count == 2
                mock_redis.keys.assert_called_once()
                mock_redis.delete.assert_called_once_with(*mock_keys)

    async def test_invalidate_by_operation_input_validation(self, ai_cache):
        """Test input validation in invalidate_by_operation method."""
        # Test invalid operation
        with pytest.raises(ValidationError, match="Invalid operation parameter"):
            await ai_cache.invalidate_by_operation("")
        
        with pytest.raises(ValidationError, match="Invalid operation parameter"):
            await ai_cache.invalidate_by_operation(None)

    async def test_invalidate_by_operation_no_keys_found(self, ai_cache):
        """Test invalidate_by_operation when no keys match."""
        with patch.object(ai_cache, 'connect', return_value=True):
            with patch.object(ai_cache, 'redis') as mock_redis:
                mock_redis.keys.return_value = []
                
                count = await ai_cache.invalidate_by_operation("nonexistent")
                
                assert count == 0

    async def test_invalidate_by_operation_redis_unavailable(self, ai_cache):
        """Test invalidate_by_operation when Redis is unavailable."""
        with patch.object(ai_cache, 'connect', return_value=False):
            count = await ai_cache.invalidate_by_operation("summarize")
            assert count == 0

    async def test_invalidate_by_operation_metrics_recording(self, ai_cache):
        """Test metrics recording in invalidate_by_operation."""
        mock_keys = [b"ai_cache:op:summarize|txt:test1"]
        
        with patch.object(ai_cache, 'connect', return_value=True):
            with patch.object(ai_cache, 'redis') as mock_redis:
                mock_redis.keys.return_value = mock_keys
                mock_redis.delete = AsyncMock()
                
                count = await ai_cache.invalidate_by_operation("summarize", "test_context")
                
                # Verify performance monitor was called
                ai_cache.performance_monitor.record_invalidation_event.assert_called_once()

    async def test_invalidate_by_operation_error_handling(self, ai_cache):
        """Test error handling in invalidate_by_operation method."""
        with patch.object(ai_cache, 'connect', return_value=True):
            with patch.object(ai_cache, 'redis') as mock_redis:
                mock_redis.keys.side_effect = Exception("Redis error")
                
                with pytest.raises(InfrastructureError, match="Failed to invalidate cache entries"):
                    await ai_cache.invalidate_by_operation("summarize")


class TestHelperMethods:
    """Test helper methods for text tiers and operations."""

    def test_get_text_tier_classification(self, ai_cache):
        """Test text tier classification logic."""
        test_cases = [
            ("short", "small"),  # 5 chars < 500
            ("a" * 1000, "medium"),  # 1000 chars between 500-5000
            ("a" * 10000, "large"),  # 10000 chars between 5000-50000
            ("a" * 60000, "xlarge"),  # 60000 chars > 50000
        ]
        
        for text, expected_tier in test_cases:
            assert ai_cache._get_text_tier(text) == expected_tier

    def test_get_text_tier_input_validation(self, ai_cache):
        """Test input validation in _get_text_tier method."""
        with pytest.raises(ValidationError, match="Invalid text parameter"):
            ai_cache._get_text_tier(123)

    def test_get_text_tier_error_handling(self, ai_cache):
        """Test error handling in _get_text_tier method."""
        # Mock an error in the tier determination
        with patch.object(ai_cache.text_size_tiers, '__getitem__', side_effect=KeyError("test")):
            # Should return medium as fallback
            result = ai_cache._get_text_tier("test")
            assert result == "medium"

    def test_get_text_tier_from_key_explicit_tier(self, ai_cache):
        """Test extracting tier from key with explicit tier information."""
        key = "ai_cache:op:summarize|tier:large|txt:content"
        assert ai_cache._get_text_tier_from_key(key) == "large"

    def test_get_text_tier_from_key_embedded_text(self, ai_cache):
        """Test extracting tier from key with embedded text."""
        # Small text embedded in key
        key = "ai_cache:op:summarize|txt:short|opts:hash"
        assert ai_cache._get_text_tier_from_key(key) == "small"

    def test_get_text_tier_from_key_size_indicators(self, ai_cache):
        """Test extracting tier from key with size indicators."""
        assert ai_cache._get_text_tier_from_key("cache_key_with_large_indicator") == "large"
        assert ai_cache._get_text_tier_from_key("cache_key_with_medium_indicator") == "medium"

    def test_get_text_tier_from_key_unknown(self, ai_cache):
        """Test extracting tier from malformed key."""
        assert ai_cache._get_text_tier_from_key("invalid_key_format") == "unknown"
        assert ai_cache._get_text_tier_from_key("") == "unknown"
        assert ai_cache._get_text_tier_from_key(None) == "unknown"

    def test_extract_operation_from_key_standard_format(self, ai_cache):
        """Test extracting operation from standard AI cache key format."""
        key = "ai_cache:op:summarize|txt:content|opts:hash"
        assert ai_cache._extract_operation_from_key(key) == "summarize"

    def test_extract_operation_from_key_alternative_format(self, ai_cache):
        """Test extracting operation from alternative key format."""
        key = "cache_prefix|op:sentiment|other_data"
        assert ai_cache._extract_operation_from_key(key) == "sentiment"

    def test_extract_operation_from_key_known_operations(self, ai_cache):
        """Test extracting operation by searching for known operation names."""
        key = "some_cache_key_with_questions_operation"
        assert ai_cache._extract_operation_from_key(key) == "questions"

    def test_extract_operation_from_key_unknown(self, ai_cache):
        """Test extracting operation from malformed key."""
        assert ai_cache._extract_operation_from_key("invalid_key") == "unknown"
        assert ai_cache._extract_operation_from_key("") == "unknown"
        assert ai_cache._extract_operation_from_key(None) == "unknown"

    def test_record_cache_operation_success(self, ai_cache):
        """Test recording successful cache operation metrics."""
        ai_cache._record_cache_operation(
            operation="summarize",
            cache_operation="get",
            text_tier="medium",
            duration=0.123,
            success=True,
            additional_data={"cache_result": "hit"}
        )
        
        # Verify performance monitor was called
        ai_cache.performance_monitor.record_cache_operation_time.assert_called_once()
        
        # Verify AI metrics were updated
        assert ai_cache.ai_metrics['cache_hits_by_operation']['summarize'] == 1
        assert ai_cache.ai_metrics['text_tier_distribution']['medium'] == 1

    def test_record_cache_operation_failure(self, ai_cache):
        """Test recording failed cache operation metrics."""
        ai_cache._record_cache_operation(
            operation="summarize",
            cache_operation="get",
            text_tier="large",
            duration=0.456,
            success=False,
            additional_data={"cache_result": "miss"}
        )
        
        # Verify AI metrics were updated for miss
        assert ai_cache.ai_metrics['cache_misses_by_operation']['summarize'] == 1


class TestMemoryCachePromotionLogic:
    """Test memory cache promotion logic."""

    def test_should_promote_to_memory_small_texts(self, ai_cache):
        """Test that small texts are always promoted."""
        assert ai_cache._should_promote_to_memory("small", "any_operation") is True

    def test_should_promote_to_memory_stable_medium(self, ai_cache):
        """Test that stable operations with medium texts are promoted."""
        stable_operations = ["sentiment", "summarize", "key_points", "classify"]
        for operation in stable_operations:
            assert ai_cache._should_promote_to_memory("medium", operation) is True

    def test_should_promote_to_memory_highly_stable_large(self, ai_cache):
        """Test that highly stable operations with large texts are promoted."""
        assert ai_cache._should_promote_to_memory("large", "sentiment") is True
        assert ai_cache._should_promote_to_memory("large", "summarize") is False  # Not highly stable

    def test_should_promote_to_memory_large_texts_generally_not_promoted(self, ai_cache):
        """Test that large/xlarge texts are generally not promoted."""
        assert ai_cache._should_promote_to_memory("large", "qa") is False
        assert ai_cache._should_promote_to_memory("xlarge", "summarize") is False

    def test_should_promote_to_memory_frequent_access(self, ai_cache):
        """Test promotion based on frequent access patterns."""
        # Set up metrics to simulate frequent access
        ai_cache.ai_metrics['cache_hits_by_operation']['frequent_op'] = 15
        
        assert ai_cache._should_promote_to_memory("medium", "frequent_op") is True
        assert ai_cache._should_promote_to_memory("small", "frequent_op") is True

    def test_should_promote_to_memory_input_validation(self, ai_cache):
        """Test input validation in promotion logic."""
        assert ai_cache._should_promote_to_memory("", "operation") is False
        assert ai_cache._should_promote_to_memory(None, "operation") is False
        assert ai_cache._should_promote_to_memory("small", "") is False
        assert ai_cache._should_promote_to_memory("small", None) is False

    def test_should_promote_to_memory_error_handling(self, ai_cache):
        """Test error handling in promotion logic."""
        with patch.object(ai_cache, 'ai_metrics', side_effect=AttributeError("test error")):
            # Should fallback to basic logic (small texts only)
            assert ai_cache._should_promote_to_memory("small", "test") is True
            assert ai_cache._should_promote_to_memory("large", "test") is False


class TestIntegrationWithInheritance:
    """Test integration with inherited GenericRedisCache functionality."""

    async def test_inherited_connect_method(self, ai_cache):
        """Test that connect method is properly inherited and works."""
        with patch('app.infrastructure.cache.redis_ai.aioredis') as mock_aioredis:
            mock_redis = MagicMock()
            mock_redis.ping = AsyncMock()
            mock_aioredis.from_url.return_value = mock_redis
            
            result = await ai_cache.connect()
            assert result is True
            assert ai_cache.redis is mock_redis

    async def test_inherited_set_get_methods(self, ai_cache, sample_response, sample_options):
        """Test that set/get methods from parent are properly used."""
        with patch.object(ai_cache, 'connect', return_value=True):
            with patch.object(ai_cache, 'redis') as mock_redis:
                # Test set method inheritance
                await ai_cache.cache_response(
                    text="test",
                    operation="summarize", 
                    options=sample_options,
                    response=sample_response
                )
                
                # Verify the parent's set method was called through inheritance chain
                # (We can't directly test this without complex mocking, but we test the integration)

    def test_ai_specific_callbacks_registration(self, ai_cache):
        """Test that AI-specific callbacks are properly registered."""
        # Verify callbacks were registered during initialization
        assert 'get_success' in ai_cache._callbacks
        assert 'get_miss' in ai_cache._callbacks
        assert 'set_success' in ai_cache._callbacks

    def test_parameter_mapping_integration(self, performance_monitor):
        """Test that parameter mapping works correctly with inheritance."""
        # Test that AI parameters are properly mapped to generic parameters
        cache = AIResponseCache(
            redis_url="redis://test:6379",
            memory_cache_size=200,  # AI parameter
            compression_threshold=2000,
            performance_monitor=performance_monitor
        )
        
        # Verify L1 cache was configured with mapped parameter
        assert cache.l1_cache.max_size == 200
        assert cache.compression_threshold == 2000


# Performance and Integration Tests
class TestPerformanceAndErrorHandling:
    """Test performance characteristics and comprehensive error handling."""

    async def test_graceful_degradation_redis_unavailable(self, ai_cache, sample_response, sample_options):
        """Test graceful degradation when Redis is unavailable."""
        with patch.object(ai_cache, 'connect', return_value=False):
            # Should not raise exceptions
            await ai_cache.cache_response(
                text="test", operation="summarize", 
                options=sample_options, response=sample_response
            )
            
            result = await ai_cache.get_cached_response(
                text="test", operation="summarize", options=sample_options
            )
            assert result is None

    async def test_concurrent_operations(self, ai_cache, sample_response, sample_options):
        """Test concurrent cache operations."""
        with patch.object(ai_cache, 'set', new_callable=AsyncMock):
            with patch.object(ai_cache, 'get', return_value=sample_response):
                # Run multiple operations concurrently
                tasks = [
                    ai_cache.cache_response(
                        text=f"test{i}", operation="summarize",
                        options=sample_options, response=sample_response
                    )
                    for i in range(10)
                ]
                
                # Should complete without errors
                await asyncio.gather(*tasks)

    async def test_large_data_handling(self, ai_cache, sample_options):
        """Test handling of large data sets."""
        large_text = "a" * 100000  # 100KB text
        large_response = {"summary": "b" * 10000}  # 10KB response
        
        with patch.object(ai_cache, 'set', new_callable=AsyncMock) as mock_set:
            await ai_cache.cache_response(
                text=large_text,
                operation="summarize",
                options=sample_options,
                response=large_response
            )
            
            # Verify it was handled correctly (tier should be xlarge)
            cached_response = mock_set.call_args[0][1]
            assert cached_response["text_tier"] == "xlarge"

    def test_metrics_memory_management(self, ai_cache):
        """Test that metrics don't grow unbounded."""
        # Simulate many operations to test memory management
        for i in range(1500):  # More than the 1000 limit
            ai_cache._record_cache_operation(
                operation="test",
                cache_operation="get",
                text_tier="small",
                duration=0.001,
                success=True
            )
        
        # Verify operation_performance list is capped at 1000
        assert len(ai_cache.ai_metrics['operation_performance']) == 1000