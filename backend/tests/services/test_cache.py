import pytest
import asyncio
import time
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime

from app.services.cache import AIResponseCache, CacheKeyGenerator
from app.services.monitoring import CachePerformanceMonitor


class TestCacheHitRatioTracking:
    """Test cache hit ratio tracking functionality."""
    
    @pytest.fixture
    def performance_monitor(self):
        """Create a CachePerformanceMonitor instance for testing."""
        return CachePerformanceMonitor(retention_hours=1, max_measurements=100)
    
    @pytest.fixture
    def cache_service(self, performance_monitor):
        """Create an AIResponseCache with performance monitoring."""
        return AIResponseCache(
            redis_url="redis://localhost:6379",
            default_ttl=3600,
            performance_monitor=performance_monitor
        )
    
    def test_cache_hit_ratio_initialization(self, cache_service):
        """Test that cache hit ratio starts at 0%."""
        assert cache_service.get_cache_hit_ratio() == 0.0
        assert cache_service.performance_monitor.cache_hits == 0
        assert cache_service.performance_monitor.cache_misses == 0
        assert cache_service.performance_monitor.total_operations == 0
    
    @pytest.mark.asyncio
    async def test_cache_miss_tracking(self, cache_service):
        """Test that cache misses are properly tracked."""
        # Mock Redis to return None (cache miss)
        with patch.object(cache_service, 'connect', return_value=True):
            with patch.object(cache_service, 'redis', create=True) as mock_redis:
                mock_redis.get = AsyncMock(return_value=None)
                
                # Perform cache operation that should miss
                result = await cache_service.get_cached_response(
                    text="Test text for cache miss",
                    operation="summarize",
                    options={"max_length": 100}
                )
                
                # Verify result is None and miss is tracked
                assert result is None
                assert cache_service.performance_monitor.cache_misses == 1
                assert cache_service.performance_monitor.cache_hits == 0
                assert cache_service.performance_monitor.total_operations == 1
                assert cache_service.get_cache_hit_ratio() == 0.0
    
    @pytest.mark.asyncio
    async def test_redis_cache_hit_tracking(self, cache_service):
        """Test that Redis cache hits are properly tracked."""
        # Mock cached response
        cached_response = {
            "operation": "summarize",
            "result": "Test summary",
            "cached_at": datetime.now().isoformat(),
            "cache_hit": True
        }
        
        with patch.object(cache_service, 'connect', return_value=True):
            with patch.object(cache_service, 'redis', create=True) as mock_redis:
                # Mock Redis to return cached data
                mock_redis.get = AsyncMock(return_value=b'{"operation": "summarize", "result": "Test summary", "cached_at": "2024-01-01T12:00:00", "cache_hit": true}')
                
                result = await cache_service.get_cached_response(
                    text="Test text for cache hit",
                    operation="summarize",
                    options={"max_length": 100}
                )
                
                # Verify cache hit is tracked
                assert result is not None
                assert cache_service.performance_monitor.cache_hits == 1
                assert cache_service.performance_monitor.cache_misses == 0
                assert cache_service.performance_monitor.total_operations == 1
                assert cache_service.get_cache_hit_ratio() == 100.0
    
    @pytest.mark.asyncio
    async def test_memory_cache_hit_tracking(self, cache_service):
        """Test that memory cache hits are properly tracked."""
        # Add item to memory cache
        cache_key = "ai_cache:op:summarize|txt:short_text"
        cached_response = {
            "operation": "summarize",
            "result": "Test summary",
            "cached_at": datetime.now().isoformat(),
            "cache_hit": True
        }
        cache_service.memory_cache[cache_key] = cached_response
        
        # Mock _generate_cache_key to return our known key
        with patch.object(cache_service, '_generate_cache_key', return_value=cache_key):
            result = await cache_service.get_cached_response(
                text="short_text",  # Small text to trigger memory cache
                operation="summarize",
                options={}
            )
            
            # Verify memory cache hit is tracked
            assert result is not None
            assert cache_service.performance_monitor.cache_hits == 1
            assert cache_service.performance_monitor.cache_misses == 0
            assert cache_service.performance_monitor.total_operations == 1
            assert cache_service.get_cache_hit_ratio() == 100.0
    
    @pytest.mark.asyncio
    async def test_mixed_cache_operations_hit_ratio(self, cache_service):
        """Test hit ratio calculation with mixed hits and misses."""
        with patch.object(cache_service, 'connect', return_value=True):
            with patch.object(cache_service, 'redis', create=True) as mock_redis:
                # Perform multiple operations: 2 hits, 3 misses
                
                # Miss 1
                mock_redis.get = AsyncMock(return_value=None)
                await cache_service.get_cached_response("text1", "summarize", {})
                
                # Hit 1
                mock_redis.get = AsyncMock(return_value=b'{"result": "cached"}')
                await cache_service.get_cached_response("text2", "summarize", {})
                
                # Miss 2
                mock_redis.get = AsyncMock(return_value=None)
                await cache_service.get_cached_response("text3", "sentiment", {})
                
                # Hit 2
                mock_redis.get = AsyncMock(return_value=b'{"result": "cached"}')
                await cache_service.get_cached_response("text4", "key_points", {})
                
                # Miss 3
                mock_redis.get = AsyncMock(return_value=None)
                await cache_service.get_cached_response("text5", "questions", {})
                
                # Verify hit ratio: 2 hits out of 5 operations = 40%
                assert cache_service.performance_monitor.cache_hits == 2
                assert cache_service.performance_monitor.cache_misses == 3
                assert cache_service.performance_monitor.total_operations == 5
                assert cache_service.get_cache_hit_ratio() == 40.0
    
    def test_key_generation_timing_tracking(self, cache_service):
        """Test that key generation timing is tracked."""
        # Generate a cache key which should trigger timing measurement
        test_text = "This is a test text for key generation timing"
        key = cache_service._generate_cache_key(
            text=test_text,
            operation="summarize",
            options={"max_length": 100},
            question=None
        )
        
        # Verify key generation time was recorded
        assert len(cache_service.performance_monitor.key_generation_times) == 1
        
        timing_record = cache_service.performance_monitor.key_generation_times[0]
        assert timing_record.duration > 0
        assert timing_record.text_length == len(test_text)  # Use actual length of the test text
        assert timing_record.operation_type == "summarize"
        assert timing_record.additional_data["has_options"] is True
        assert timing_record.additional_data["has_question"] is False
    
    @pytest.mark.asyncio
    async def test_redis_connection_failure_tracking(self, cache_service):
        """Test that Redis connection failures are tracked as misses."""
        with patch.object(cache_service, 'connect', return_value=False):
            result = await cache_service.get_cached_response(
                text="Test text",
                operation="summarize", 
                options={}
            )
            
            # Verify connection failure is tracked as a miss
            assert result is None
            assert cache_service.performance_monitor.cache_hits == 0
            assert cache_service.performance_monitor.cache_misses == 1
            assert cache_service.performance_monitor.total_operations == 1
            assert cache_service.get_cache_hit_ratio() == 0.0
    
    @pytest.mark.asyncio
    async def test_redis_error_tracking(self, cache_service):
        """Test that Redis errors are tracked as misses with error details."""
        with patch.object(cache_service, 'connect', return_value=True):
            with patch.object(cache_service, 'redis', create=True) as mock_redis:
                # Make Redis raise an exception
                mock_redis.get = AsyncMock(side_effect=Exception("Redis error"))
                
                result = await cache_service.get_cached_response(
                    text="Test text",
                    operation="summarize",
                    options={}
                )
                
                # Verify error is tracked as a miss
                assert result is None
                assert cache_service.performance_monitor.cache_hits == 0
                assert cache_service.performance_monitor.cache_misses == 1
                assert cache_service.get_cache_hit_ratio() == 0.0
                
                # Check that error details are recorded
                operation_record = cache_service.performance_monitor.cache_operation_times[0]
                assert operation_record.additional_data["reason"] == "redis_error"
                assert "Redis error" in operation_record.additional_data["error"]
    
    def test_performance_summary(self, cache_service):
        """Test the performance summary method."""
        # Add some mock data
        cache_service.performance_monitor.cache_hits = 7
        cache_service.performance_monitor.cache_misses = 3
        cache_service.performance_monitor.total_operations = 10
        
        summary = cache_service.get_performance_summary()
        
        assert summary["hit_ratio"] == 70.0
        assert summary["total_operations"] == 10
        assert summary["cache_hits"] == 7
        assert summary["cache_misses"] == 3
        assert "recent_avg_key_generation_time" in summary
        assert "recent_avg_cache_operation_time" in summary
    
    def test_performance_stats_reset(self, cache_service):
        """Test that performance statistics can be reset."""
        # Add some data first
        cache_service.performance_monitor.cache_hits = 5
        cache_service.performance_monitor.cache_misses = 2
        cache_service.performance_monitor.total_operations = 7
        
        # Reset stats
        cache_service.reset_performance_stats()
        
        # Verify everything is reset
        assert cache_service.performance_monitor.cache_hits == 0
        assert cache_service.performance_monitor.cache_misses == 0
        assert cache_service.performance_monitor.total_operations == 0
        assert cache_service.get_cache_hit_ratio() == 0.0
    
    @pytest.mark.asyncio
    async def test_cache_stats_includes_performance(self, cache_service):
        """Test that get_cache_stats includes performance metrics."""
        # Add some performance data
        cache_service.performance_monitor.cache_hits = 3
        cache_service.performance_monitor.cache_misses = 1
        cache_service.performance_monitor.total_operations = 4  # Set total operations to match hits + misses
        
        with patch.object(cache_service, 'connect', return_value=False):
            stats = await cache_service.get_cache_stats()
            
            # Verify performance stats are included
            assert "performance" in stats
            assert stats["performance"]["cache_hit_rate"] == 75.0
            assert stats["performance"]["total_cache_operations"] == 4
            assert stats["performance"]["cache_hits"] == 3
            assert stats["performance"]["cache_misses"] == 1 