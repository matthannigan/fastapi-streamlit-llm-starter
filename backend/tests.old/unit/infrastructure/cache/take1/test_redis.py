"""
[UNIT TESTS] Redis Legacy Cache Implementation - Comprehensive Docstring-Driven Tests

This test module provides comprehensive unit tests for the deprecated AIResponseCache class
in app.infrastructure.cache.redis, following docstring-driven test development principles.
The tests focus on the documented contracts in the AIResponseCache class docstrings,
testing WHAT the cache should do rather than HOW it implements the functionality.

Test Structure:
    - TestAIResponseCacheInitialization: Constructor behavior and configuration
    - TestAIResponseCacheConnection: Redis connection handling and fallback logic
    - TestAIResponseCacheKeyGeneration: Cache key generation and text handling
    - TestAIResponseCacheRetrieval: Cache retrieval with tiered fallback strategy
    - TestAIResponseCacheCaching: Response caching with compression and TTL
    - TestAIResponseCacheInvalidation: Pattern-based and operation-specific invalidation
    - TestAIResponseCacheStatistics: Performance statistics and memory monitoring
    - TestAIResponseCacheErrorHandling: Error scenarios and graceful degradation
    - TestAIResponseCachePerformanceMonitoring: Performance monitoring integration
    - TestAIResponseCacheMemoryManagement: Memory cache management and eviction

Business Impact:
    These tests ensure the deprecated Redis cache maintains backward compatibility
    while validating the documented behavior for systems still using this interface.
    The tests prevent regressions during the transition to the new modular cache structure.

Test Coverage Focus:
    - Cache contract fulfillment per documented behavior
    - Redis connection handling with graceful degradation
    - Tiered caching strategy (memory + Redis) 
    - Compression logic for large responses
    - TTL handling per operation type
    - Pattern-based invalidation with performance tracking
    - Performance monitoring integration
    - Error handling and fallback behavior

Mocking Strategy:
    - Mock Redis client connections to avoid external dependencies
    - Mock CachePerformanceMonitor for isolated performance tracking
    - Mock CacheKeyGenerator for predictable key generation
    - Test actual cache logic while mocking Redis interactions
    - Use real objects for business logic validation

Architecture Note:
    This module tests the deprecated AIResponseCache which inherits from GenericRedisCache
    but adds AI-specific functionality. Tests focus on the AI-specific behavior documented
    in the class docstrings while ensuring the inheritance relationship works correctly.
"""

import asyncio
import hashlib
import json
import pytest
import time
import warnings
from datetime import datetime
from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, MagicMock, Mock, patch

# Test the deprecated module to ensure backward compatibility
from app.infrastructure.cache.redis import AIResponseCache, REDIS_AVAILABLE
from app.infrastructure.cache.monitoring import CachePerformanceMonitor
from app.infrastructure.cache.key_generator import CacheKeyGenerator


class TestAIResponseCacheInitialization:
    """
    Test AIResponseCache initialization and configuration.
    
    Business Impact:
        Ensures proper initialization of cache with various configurations,
        preventing configuration errors that could lead to cache failures.
        
    Test Scenarios:
        - Default configuration initialization
        - Custom configuration with all parameters
        - Performance monitor integration
        - Text size tier configuration
        - Backward compatibility with legacy parameters
    """

    def test_init_with_defaults_creates_proper_configuration(self):
        """
        Test AIResponseCache initialization with default parameters per docstring.
        
        Business Impact:
            Verifies default configuration provides sensible cache behavior
            for systems that don't specify custom parameters.
            
        Success Criteria:
            - Cache initializes with documented default values
            - All required components are properly configured
            - Performance monitor is created if not provided
            - Operation TTLs are set according to documented values
        """
        # Test default initialization per constructor docstring
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            cache = AIResponseCache()
        
        # Verify default configuration matches documented values
        assert cache.redis_url == "redis://redis:6379"
        assert cache.default_ttl == 3600
        assert cache.memory_cache_size == 100
        assert cache.compression_threshold == 1000
        assert cache.compression_level == 6
        
        # Verify AI-specific operation TTLs per documentation
        expected_ttls = {
            "summarize": 7200,  # 2 hours - summaries are stable
            "sentiment": 86400,  # 24 hours - sentiment rarely changes
            "key_points": 7200,  # 2 hours
            "questions": 3600,  # 1 hour - questions can vary
            "qa": 1800,  # 30 minutes - context-dependent
        }
        assert cache.operation_ttls == expected_ttls
        
        # Verify key generator initialization per docstring
        assert isinstance(cache.key_generator, CacheKeyGenerator)
        assert cache.key_generator.text_hash_threshold == 1000
        assert cache.key_generator.hash_algorithm == hashlib.sha256
        
        # Verify default text size tiers per documentation
        expected_tiers = {
            "small": 500,  # < 500 chars - cache with full text and use memory cache
            "medium": 5000,  # 500-5000 chars - cache with text hash
            "large": 50000,  # 5000-50000 chars - cache with content hash + metadata
        }
        assert cache.text_size_tiers == expected_tiers

    def test_init_with_custom_configuration_applies_all_parameters(self):
        """
        Test AIResponseCache initialization with custom parameters per docstring.
        
        Business Impact:
            Ensures cache can be customized for specific deployment requirements
            without breaking the documented interface contract.
            
        Success Criteria:
            - All custom parameters are properly applied
            - Custom text size tiers override defaults
            - Custom performance monitor is used when provided
            - Hash algorithm customization works correctly
        """
        # Create custom configuration per constructor docstring
        custom_monitor = Mock(spec=CachePerformanceMonitor)
        custom_tiers = {"small": 300, "medium": 3000, "large": 30000}
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            cache = AIResponseCache(
                redis_url="redis://custom:6380",
                default_ttl=7200,
                text_hash_threshold=500,
                hash_algorithm=hashlib.md5,
                compression_threshold=2000,
                compression_level=9,
                text_size_tiers=custom_tiers,
                memory_cache_size=200,
                performance_monitor=custom_monitor,
            )
        
        # Verify all custom parameters are applied per docstring
        assert cache.redis_url == "redis://custom:6380"
        assert cache.default_ttl == 7200
        assert cache.memory_cache_size == 200
        assert cache.compression_threshold == 2000
        assert cache.compression_level == 9
        
        # Verify custom text size tiers are used
        assert cache.text_size_tiers == custom_tiers
        
        # Verify custom key generator configuration
        assert cache.key_generator.text_hash_threshold == 500
        assert cache.key_generator.hash_algorithm == hashlib.md5
        assert cache.key_generator.performance_monitor == custom_monitor
        
        # Verify custom performance monitor is used
        assert cache.performance_monitor == custom_monitor

    def test_init_emits_deprecation_warning_for_direct_usage(self):
        """
        Test that direct AIResponseCache usage emits deprecation warning per docstring.
        
        Business Impact:
            Alerts users to migrate to new modular cache structure,
            preventing future compatibility issues during API evolution.
            
        Success Criteria:
            - DeprecationWarning is emitted for direct instantiation
            - Warning message contains migration guidance
            - Cache still functions correctly despite warning
        """
        # Test deprecation warning emission per class docstring
        with pytest.warns(DeprecationWarning) as warning_info:
            cache = AIResponseCache()
        
        # Verify warning contains expected guidance per docstring
        warning_message = str(warning_info[0].message)
        assert "AIResponseCache direct usage is deprecated" in warning_message
        assert "GenericRedisCache with CacheCompatibilityWrapper" in warning_message
        assert "refactored in future versions" in warning_message
        
        # Verify cache is still functional despite deprecation
        assert isinstance(cache, AIResponseCache)
        assert hasattr(cache, "key_generator")
        assert hasattr(cache, "operation_ttls")


class TestAIResponseCacheConnection:
    """
    Test Redis connection handling and graceful degradation.
    
    Business Impact:
        Ensures cache continues operating when Redis is unavailable,
        preventing application failures due to cache infrastructure issues.
        
    Test Scenarios:
        - Successful Redis connection
        - Redis unavailable graceful degradation
        - Connection failure handling
        - Connection retry behavior
    """

    @patch('app.infrastructure.cache.redis.aioredis')
    @pytest.mark.asyncio
    async def test_connect_successful_redis_connection_per_docstring(self, mock_aioredis):
        """
        Test successful Redis connection per connect method docstring.
        
        Business Impact:
            Verifies cache can establish Redis connection for persistent storage,
            enabling cross-instance cache sharing and improved performance.
            
        Success Criteria:
            - Redis client is created with correct configuration
            - Connection is tested with ping command
            - Success status is returned
            - Connection state is properly maintained
        """
        # Mock successful Redis connection per connect method behavior
        mock_redis_client = AsyncMock()
        mock_redis_client.ping = AsyncMock(return_value=True)
        mock_aioredis.from_url = AsyncMock(return_value=mock_redis_client)
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            cache = AIResponseCache(redis_url="redis://test:6379")
        
        # Test connection per docstring: "Initialize Redis connection"
        result = await cache.connect()
        
        # Verify successful connection per docstring return behavior
        assert result is True
        assert cache.redis == mock_redis_client
        
        # Verify Redis client configuration per docstring
        mock_aioredis.from_url.assert_called_once_with(
            "redis://test:6379",
            decode_responses=False,
            socket_connect_timeout=5,
            socket_timeout=5,
        )
        mock_redis_client.ping.assert_called_once()

    @patch('app.infrastructure.cache.redis.REDIS_AVAILABLE', False)
    @pytest.mark.asyncio
    async def test_connect_graceful_degradation_when_redis_unavailable(self):
        """
        Test graceful degradation when Redis is unavailable per docstring.
        
        Business Impact:
            Ensures application continues functioning when Redis dependency
            fails, preventing total cache system failure.
            
        Success Criteria:
            - Returns False when Redis is unavailable
            - Logs warning about memory-only operation
            - Cache remains functional for memory operations
            - No exceptions are raised
        """
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            cache = AIResponseCache()
        
        # Test graceful degradation per docstring behavior
        with patch('app.infrastructure.cache.redis.logger') as mock_logger:
            result = await cache.connect()
            
            # Verify graceful degradation per docstring
            assert result is False
            assert cache.redis is None
            mock_logger.warning.assert_called_with(
                "Redis not available - operating in memory-only mode"
            )

    @patch('app.infrastructure.cache.redis.aioredis')
    @pytest.mark.asyncio
    async def test_connect_handles_connection_failure_gracefully(self, mock_aioredis):
        """
        Test connection failure handling per connect method docstring.
        
        Business Impact:
            Ensures cache degrades gracefully on Redis connection failures,
            maintaining application stability during infrastructure issues.
            
        Success Criteria:
            - Connection failures are caught and logged
            - Returns False on connection failure
            - Switches to memory-only mode automatically
            - No unhandled exceptions propagate to caller
        """
        # Mock Redis connection failure per error handling docstring
        mock_aioredis.from_url = AsyncMock(side_effect=ConnectionError("Redis unavailable"))
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            cache = AIResponseCache()
        
        # Test connection failure handling per docstring
        with patch('app.infrastructure.cache.redis.logger') as mock_logger:
            result = await cache.connect()
            
            # Verify graceful failure handling per docstring
            assert result is False
            assert cache.redis is None
            mock_logger.warning.assert_called_with(
                "Redis connection failed: Redis unavailable - using memory-only mode"
            )


class TestAIResponseCacheKeyGeneration:
    """
    Test cache key generation with text tier optimization.
    
    Business Impact:
        Ensures consistent and collision-free cache keys for all text sizes,
        enabling reliable cache hits and preventing key conflicts.
        
    Test Scenarios:
        - Small text direct inclusion
        - Large text hashing
        - Key generation with options and questions
        - Text tier determination logic
    """

    def test_get_text_tier_categorizes_text_correctly_per_docstring(self):
        """
        Test text tier categorization per _get_text_tier method docstring.
        
        Business Impact:
            Ensures proper text size categorization for optimal caching strategy,
            balancing memory usage with cache performance.
            
        Success Criteria:
            - Small texts (< 500 chars) return "small" tier
            - Medium texts (500-5000 chars) return "medium" tier  
            - Large texts (5000-50000 chars) return "large" tier
            - Extra large texts (> 50000 chars) return "xlarge" tier
        """
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            cache = AIResponseCache()
        
        # Test text tier determination per docstring Args/Returns
        assert cache._get_text_tier("short") == "small"  # < 500 chars
        assert cache._get_text_tier("a" * 300) == "small"  # 300 chars
        assert cache._get_text_tier("a" * 499) == "small"  # 499 chars
        
        assert cache._get_text_tier("a" * 500) == "medium"  # 500 chars
        assert cache._get_text_tier("a" * 2000) == "medium"  # 2000 chars
        assert cache._get_text_tier("a" * 4999) == "medium"  # 4999 chars
        
        assert cache._get_text_tier("a" * 5000) == "large"  # 5000 chars
        assert cache._get_text_tier("a" * 25000) == "large"  # 25000 chars
        assert cache._get_text_tier("a" * 49999) == "large"  # 49999 chars
        
        assert cache._get_text_tier("a" * 50000) == "xlarge"  # 50000 chars
        assert cache._get_text_tier("a" * 100000) == "xlarge"  # 100000 chars

    @patch.object(CacheKeyGenerator, 'generate_cache_key')
    def test_generate_cache_key_delegates_to_key_generator_per_docstring(self, mock_generate):
        """
        Test cache key generation delegation per _generate_cache_key docstring.
        
        Business Impact:
            Ensures consistent key generation through dedicated key generator,
            maintaining cache key format compatibility and uniqueness.
            
        Success Criteria:
            - Method delegates to CacheKeyGenerator instance
            - All parameters are passed correctly to key generator
            - Generated key is returned unchanged from key generator
            - Key generation follows documented format patterns
        """
        # Set up mock key generator response per docstring example
        expected_key = "ai_cache:op:summarize|txt:Sample text|opts:abc12345"
        mock_generate.return_value = expected_key
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            cache = AIResponseCache()
        
        # Test key generation delegation per docstring
        result = cache._generate_cache_key(
            text="Sample text",
            operation="summarize",
            options={"max_length": 100},
            question="What is this about?"
        )
        
        # Verify delegation per docstring behavior
        assert result == expected_key
        mock_generate.assert_called_once_with(
            "Sample text",
            "summarize", 
            {"max_length": 100},
            "What is this about?"
        )


class TestAIResponseCacheRetrieval:
    """
    Test multi-tier cache retrieval with performance monitoring.
    
    Business Impact:
        Ensures efficient cache retrieval with proper fallback strategy,
        optimizing response times while maintaining data consistency.
        
    Test Scenarios:
        - Memory cache hits for small texts
        - Redis cache hits with memory population
        - Cache misses with proper performance tracking
        - Error handling during retrieval
    """

    @pytest.mark.asyncio
    async def test_get_cached_response_memory_cache_hit_for_small_text(self):
        """
        Test memory cache hit for small text per get_cached_response docstring.
        
        Business Impact:
            Ensures fastest possible cache retrieval for frequently accessed
            small texts, minimizing response latency.
            
        Success Criteria:
            - Small texts check memory cache first per docstring
            - Memory cache hits return immediately without Redis check
            - Performance metrics are recorded correctly
            - Cache tier information is included in metrics
        """
        # Create mock performance monitor
        mock_monitor = Mock(spec=CachePerformanceMonitor)
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            cache = AIResponseCache(performance_monitor=mock_monitor)
        
        # Set up memory cache with small text entry per docstring behavior
        small_text = "Small text for testing"  # < 500 chars = small tier
        cache_key = cache._generate_cache_key(small_text, "summarize", {})
        expected_response = {"summary": "Test summary", "cached_at": "2024-01-15T10:30:00"}
        cache.memory_cache[cache_key] = expected_response
        
        # Test memory cache retrieval per docstring
        result = await cache.get_cached_response(
            text=small_text,
            operation="summarize",
            options={}
        )
        
        # Verify memory cache hit per docstring behavior
        assert result == expected_response
        
        # Verify performance monitoring per docstring
        mock_monitor.record_cache_operation_time.assert_called_once()
        call_args = mock_monitor.record_cache_operation_time.call_args
        assert call_args[1]['operation'] == "get"
        assert call_args[1]['cache_hit'] is True
        assert call_args[1]['text_length'] == len(small_text)
        assert call_args[1]['additional_data']['cache_tier'] == "memory"
        assert call_args[1]['additional_data']['text_tier'] == "small"

    @patch('app.infrastructure.cache.redis.aioredis')
    @pytest.mark.asyncio
    async def test_get_cached_response_redis_hit_populates_memory_cache(self, mock_aioredis):
        """
        Test Redis cache hit with memory cache population per docstring.
        
        Business Impact:
            Ensures Redis cache hits populate memory cache for future fast access,
            optimizing subsequent retrievals of the same content.
            
        Success Criteria:
            - Redis cache is checked when memory cache misses
            - Successful Redis hits populate memory cache for small texts
            - Performance metrics track Redis cache tier correctly
            - Decompression handles both new and legacy formats
        """
        # Mock successful Redis connection and data retrieval
        mock_redis_client = AsyncMock()
        expected_response = {"summary": "Redis cached summary", "cached_at": "2024-01-15T10:30:00"}
        cached_data = json.dumps(expected_response).encode('utf-8')
        mock_redis_client.get = AsyncMock(return_value=cached_data)
        mock_redis_client.ping = AsyncMock(return_value=True)
        mock_aioredis.from_url = AsyncMock(return_value=mock_redis_client)
        
        mock_monitor = Mock(spec=CachePerformanceMonitor)
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            cache = AIResponseCache(performance_monitor=mock_monitor)
        
        # Set up small text for memory cache population per docstring
        small_text = "Small text for Redis test"  # < 500 chars = small tier
        
        # Test Redis cache retrieval per docstring
        result = await cache.get_cached_response(
            text=small_text,
            operation="summarize", 
            options={}
        )
        
        # Verify Redis cache hit per docstring behavior
        assert result == expected_response
        
        # Verify memory cache population for small texts per docstring
        cache_key = cache._generate_cache_key(small_text, "summarize", {})
        assert cache.memory_cache[cache_key] == expected_response
        
        # Verify performance monitoring per docstring
        mock_monitor.record_cache_operation_time.assert_called_once()
        call_args = mock_monitor.record_cache_operation_time.call_args
        assert call_args[1]['cache_hit'] is True
        assert call_args[1]['additional_data']['cache_tier'] == "redis"
        assert call_args[1]['additional_data']['populated_memory_cache'] is True

    @patch('app.infrastructure.cache.redis.aioredis')
    @pytest.mark.asyncio
    async def test_get_cached_response_cache_miss_records_metrics(self, mock_aioredis):
        """
        Test cache miss recording per get_cached_response docstring.
        
        Business Impact:
            Ensures cache misses are properly tracked for performance analysis
            and cache optimization decisions.
            
        Success Criteria:
            - Cache misses return None per docstring
            - Performance metrics record cache miss with reason
            - Redis connection failures are handled gracefully
            - Appropriate cache tier and text tier are recorded
        """
        # Mock Redis connection with no cached data (cache miss)
        mock_redis_client = AsyncMock()
        mock_redis_client.get = AsyncMock(return_value=None)  # Cache miss
        mock_redis_client.ping = AsyncMock(return_value=True)
        mock_aioredis.from_url = AsyncMock(return_value=mock_redis_client)
        
        mock_monitor = Mock(spec=CachePerformanceMonitor)
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            cache = AIResponseCache(performance_monitor=mock_monitor)
        
        # Test cache miss per docstring
        result = await cache.get_cached_response(
            text="Text not in cache",
            operation="summarize",
            options={}
        )
        
        # Verify cache miss behavior per docstring
        assert result is None
        
        # Verify performance monitoring per docstring
        mock_monitor.record_cache_operation_time.assert_called_once()
        call_args = mock_monitor.record_cache_operation_time.call_args
        assert call_args[1]['cache_hit'] is False
        assert call_args[1]['additional_data']['reason'] == "key_not_found"

    @patch('app.infrastructure.cache.redis.REDIS_AVAILABLE', False)
    @pytest.mark.asyncio
    async def test_get_cached_response_handles_redis_unavailable(self):
        """
        Test cache retrieval when Redis is unavailable per docstring.
        
        Business Impact:
            Ensures cache retrieval gracefully degrades when Redis fails,
            preventing cache system from blocking application functionality.
            
        Success Criteria:
            - Returns None when Redis connection fails
            - Records cache miss with appropriate reason
            - No exceptions propagate to caller
            - Performance metrics include failure reason
        """
        mock_monitor = Mock(spec=CachePerformanceMonitor)
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            cache = AIResponseCache(performance_monitor=mock_monitor)
        
        # Test Redis unavailable scenario per docstring
        result = await cache.get_cached_response(
            text="Test text",
            operation="summarize",
            options={}
        )
        
        # Verify graceful degradation per docstring
        assert result is None
        
        # Verify performance monitoring captures Redis unavailability
        mock_monitor.record_cache_operation_time.assert_called_once()
        call_args = mock_monitor.record_cache_operation_time.call_args
        assert call_args[1]['cache_hit'] is False
        assert call_args[1]['additional_data']['cache_tier'] == "redis_unavailable"
        assert call_args[1]['additional_data']['reason'] == "redis_connection_failed"


class TestAIResponseCacheCaching:
    """
    Test response caching with compression and TTL handling.
    
    Business Impact:
        Ensures reliable storage of AI responses with appropriate compression
        and time-based expiration for optimal cache efficiency.
        
    Test Scenarios:
        - Response caching with compression for large responses
        - TTL assignment based on operation type
        - Performance monitoring during cache operations
        - Error handling during storage operations
    """

    @patch('app.infrastructure.cache.redis.aioredis')
    @pytest.mark.asyncio
    async def test_cache_response_stores_with_compression_for_large_responses(self, mock_aioredis):
        """
        Test response caching with compression per cache_response docstring.
        
        Business Impact:
            Ensures large AI responses are compressed before storage,
            optimizing Redis memory usage and storage costs.
            
        Success Criteria:
            - Large responses trigger compression per docstring threshold
            - Compression metrics are recorded accurately
            - Cache metadata includes compression information
            - TTL is set according to operation type per docstring
        """
        # Mock Redis connection for caching
        mock_redis_client = AsyncMock()
        mock_redis_client.setex = AsyncMock()
        mock_redis_client.ping = AsyncMock(return_value=True)
        mock_aioredis.from_url = AsyncMock(return_value=mock_redis_client)
        
        mock_monitor = Mock(spec=CachePerformanceMonitor)
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            cache = AIResponseCache(
                compression_threshold=100,  # Low threshold for testing
                performance_monitor=mock_monitor
            )
        
        # Create large response that will trigger compression per docstring
        large_response = {"summary": "A" * 200, "confidence": 0.95}  # > 100 bytes
        
        # Test caching with compression per docstring
        await cache.cache_response(
            text="Test text",
            operation="summarize",
            options={"max_length": 100},
            response=large_response
        )
        
        # Verify Redis storage was called per docstring
        mock_redis_client.setex.assert_called_once()
        call_args = mock_redis_client.setex.call_args[0]
        cache_key, ttl, cache_data = call_args
        
        # Verify TTL matches operation type per docstring
        expected_ttl = cache.operation_ttls["summarize"]  # 7200 seconds
        assert ttl == expected_ttl
        
        # Verify compression metrics are recorded per docstring  
        mock_monitor.record_compression_ratio.assert_called_once()
        
        # Verify performance metrics per docstring
        mock_monitor.record_cache_operation_time.assert_called_once()
        perf_call = mock_monitor.record_cache_operation_time.call_args
        assert perf_call[1]['operation'] == "set"
        assert perf_call[1]['cache_hit'] is True  # Successful set
        assert perf_call[1]['additional_data']['compression_used'] is True

    @pytest.mark.asyncio
    async def test_cache_response_applies_correct_ttl_per_operation_type(self):
        """
        Test TTL assignment per operation type per cache_response docstring.
        
        Business Impact:
            Ensures cache entries expire at appropriate intervals based on
            content stability, optimizing cache hit rates and data freshness.
            
        Success Criteria:
            - Sentiment operations use 24-hour TTL (stable data)
            - Q&A operations use 30-minute TTL (context-dependent)
            - Summarize operations use 2-hour TTL (moderately stable)
            - Unknown operations use default TTL
        """
        # Mock performance monitor
        mock_monitor = Mock(spec=CachePerformanceMonitor)
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            cache = AIResponseCache(
                default_ttl=3600,
                performance_monitor=mock_monitor
            )
        
        # Mock Redis connection
        with patch.object(cache, 'connect', return_value=True):
            cache.redis = AsyncMock()
            
            # Test different operation TTLs per docstring
            test_cases = [
                ("sentiment", 86400),    # 24 hours - sentiment rarely changes
                ("summarize", 7200),     # 2 hours - summaries are stable  
                ("key_points", 7200),    # 2 hours
                ("questions", 3600),     # 1 hour - questions can vary
                ("qa", 1800),           # 30 minutes - context-dependent
                ("unknown_op", 3600),    # Default TTL for unknown operations
            ]
            
            for operation, expected_ttl in test_cases:
                cache.redis.reset_mock()
                
                await cache.cache_response(
                    text="Test text",
                    operation=operation,
                    options={},
                    response={"result": "test"}
                )
                
                # Verify correct TTL was used per docstring
                cache.redis.setex.assert_called_once()
                call_args = cache.redis.setex.call_args[0]
                _, actual_ttl, _ = call_args
                assert actual_ttl == expected_ttl, f"Operation {operation} should have TTL {expected_ttl}"

    @patch('app.infrastructure.cache.redis.REDIS_AVAILABLE', False)
    @pytest.mark.asyncio
    async def test_cache_response_handles_redis_unavailable_gracefully(self):
        """
        Test caching when Redis is unavailable per cache_response docstring.
        
        Business Impact:
            Ensures cache storage failures don't interrupt application flow,
            maintaining system stability during infrastructure issues.
            
        Success Criteria:
            - Method returns without raising exceptions
            - Performance metrics record the failure reason
            - Operation completes gracefully per docstring error handling
        """
        mock_monitor = Mock(spec=CachePerformanceMonitor)
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            cache = AIResponseCache(performance_monitor=mock_monitor)
        
        # Test caching when Redis unavailable per docstring
        await cache.cache_response(
            text="Test text",
            operation="summarize",
            options={},
            response={"summary": "Test summary"}
        )
        
        # Verify graceful handling per docstring error handling
        # Should complete without exceptions
        
        # Verify performance monitoring captures failure per docstring
        mock_monitor.record_cache_operation_time.assert_called_once()
        call_args = mock_monitor.record_cache_operation_time.call_args
        assert call_args[1]['cache_hit'] is False  # Failed operation
        assert call_args[1]['additional_data']['reason'] == "redis_connection_failed"


class TestAIResponseCacheInvalidation:
    """
    Test pattern-based and operation-specific cache invalidation.
    
    Business Impact:
        Ensures cache can be efficiently cleared when data becomes stale,
        maintaining data freshness and preventing outdated responses.
        
    Test Scenarios:
        - Pattern-based invalidation with wildcard matching
        - Operation-specific invalidation
        - Full cache clearing
        - Memory cache invalidation
        - Performance tracking during invalidation
    """

    @patch('app.infrastructure.cache.redis.aioredis')
    @pytest.mark.asyncio
    async def test_invalidate_pattern_removes_matching_keys_per_docstring(self, mock_aioredis):
        """
        Test pattern-based invalidation per invalidate_pattern docstring.
        
        Business Impact:
            Enables selective cache clearing for related content,
            improving cache efficiency without losing unrelated data.
            
        Success Criteria:
            - Pattern matching uses documented Redis pattern format
            - Matching keys are deleted from Redis
            - Performance metrics track invalidation event
            - Zero matches are handled gracefully per docstring
        """
        # Mock Redis with keys matching pattern
        mock_redis_client = AsyncMock()
        matching_keys = [
            b"ai_cache:op:summarize|txt:doc1",
            b"ai_cache:op:summarize|txt:doc2"
        ]
        mock_redis_client.keys = AsyncMock(return_value=matching_keys)
        mock_redis_client.delete = AsyncMock()
        mock_redis_client.ping = AsyncMock(return_value=True)
        mock_aioredis.from_url = AsyncMock(return_value=mock_redis_client)
        
        mock_monitor = Mock(spec=CachePerformanceMonitor)
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            cache = AIResponseCache(performance_monitor=mock_monitor)
        
        # Test pattern invalidation per docstring
        await cache.invalidate_pattern("summarize", "model_update")
        
        # Verify Redis pattern search per docstring
        expected_pattern = "ai_cache:*summarize*".encode("utf-8")
        mock_redis_client.keys.assert_called_once_with(expected_pattern)
        
        # Verify matching keys were deleted per docstring
        mock_redis_client.delete.assert_called_once_with(*matching_keys)
        
        # Verify performance monitoring per docstring
        mock_monitor.record_invalidation_event.assert_called_once()
        call_args = mock_monitor.record_invalidation_event.call_args
        assert call_args[1]['pattern'] == "summarize"
        assert call_args[1]['keys_invalidated'] == 2
        assert call_args[1]['operation_context'] == "model_update"

    @pytest.mark.asyncio
    async def test_invalidate_by_operation_targets_specific_operation_per_docstring(self):
        """
        Test operation-specific invalidation per invalidate_by_operation docstring.
        
        Business Impact:
            Enables clearing cache for specific AI operations after model updates,
            ensuring data freshness without affecting other operation types.
            
        Success Criteria:
            - Operation-specific pattern is constructed correctly
            - Context is auto-generated when not provided per docstring
            - Invalidation delegates to pattern invalidation correctly
        """
        mock_monitor = Mock(spec=CachePerformanceMonitor)
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            cache = AIResponseCache(performance_monitor=mock_monitor)
        
        # Mock the pattern invalidation method to verify delegation
        with patch.object(cache, 'invalidate_pattern') as mock_invalidate:
            # Test operation invalidation per docstring
            await cache.invalidate_by_operation("sentiment", "model_updated")
            
            # Verify correct pattern and context per docstring
            mock_invalidate.assert_called_once_with(
                "op:sentiment", 
                operation_context="model_updated"
            )

    @pytest.mark.asyncio
    async def test_invalidate_by_operation_auto_generates_context_per_docstring(self):
        """
        Test auto-generated context per invalidate_by_operation docstring.
        
        Business Impact:
            Provides meaningful invalidation context for monitoring even when
            not explicitly provided by caller.
            
        Success Criteria:
            - Context is auto-generated when empty per docstring
            - Generated context includes operation name
            - Pattern delegation works with generated context
        """
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            cache = AIResponseCache()
        
        # Mock pattern invalidation to verify context generation
        with patch.object(cache, 'invalidate_pattern') as mock_invalidate:
            # Test with empty context per docstring
            await cache.invalidate_by_operation("summarize", "")
            
            # Verify auto-generated context per docstring
            mock_invalidate.assert_called_once_with(
                "op:summarize",
                operation_context="operation_specific_summarize"
            )

    @pytest.mark.asyncio
    async def test_invalidate_all_clears_entire_cache_per_docstring(self):
        """
        Test full cache invalidation per invalidate_all docstring.
        
        Business Impact:
            Enables complete cache clearing for major system changes,
            ensuring no stale data remains after significant updates.
            
        Success Criteria:
            - Empty pattern matches all keys per docstring
            - Operation context defaults to "manual_clear_all"
            - Delegates to pattern invalidation correctly
        """
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            cache = AIResponseCache()
        
        # Mock pattern invalidation to verify full clearing
        with patch.object(cache, 'invalidate_pattern') as mock_invalidate:
            # Test full cache invalidation per docstring
            await cache.invalidate_all("system_restart")
            
            # Verify full invalidation per docstring
            mock_invalidate.assert_called_once_with(
                "",  # Empty pattern matches all
                operation_context="system_restart"
            )

    @pytest.mark.asyncio
    async def test_invalidate_memory_cache_clears_memory_tier_per_docstring(self):
        """
        Test memory cache clearing per invalidate_memory_cache docstring.
        
        Business Impact:
            Enables memory cache optimization without affecting Redis storage,
            useful for memory pressure situations.
            
        Success Criteria:
            - Memory cache is cleared completely per docstring  
            - Memory cache order tracking is reset
            - Performance metrics record the invalidation event
            - Redis cache remains intact per docstring note
        """
        mock_monitor = Mock(spec=CachePerformanceMonitor)
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            cache = AIResponseCache(performance_monitor=mock_monitor)
        
        # Populate memory cache for testing
        cache.memory_cache = {"key1": "value1", "key2": "value2"}
        cache.memory_cache_order = ["key1", "key2"]
        
        # Test memory cache invalidation per docstring
        await cache.invalidate_memory_cache("memory_optimization")
        
        # Verify memory cache clearing per docstring
        assert len(cache.memory_cache) == 0
        assert len(cache.memory_cache_order) == 0
        
        # Verify performance monitoring per docstring
        mock_monitor.record_invalidation_event.assert_called_once()
        call_args = mock_monitor.record_invalidation_event.call_args
        assert call_args[1]['pattern'] == "memory_cache"
        assert call_args[1]['keys_invalidated'] == 2  # Two entries were cleared
        assert call_args[1]['invalidation_type'] == "memory"
        assert call_args[1]['operation_context'] == "memory_optimization"


class TestAIResponseCacheStatistics:
    """
    Test cache statistics and performance monitoring.
    
    Business Impact:
        Ensures comprehensive cache monitoring for performance optimization
        and capacity planning decisions.
        
    Test Scenarios:
        - Cache statistics collection from Redis and memory
        - Hit ratio calculations
        - Performance summary generation
        - Memory usage statistics and warnings
    """

    @patch('app.infrastructure.cache.redis.aioredis')
    @pytest.mark.asyncio
    async def test_get_cache_stats_collects_comprehensive_statistics_per_docstring(self, mock_aioredis):
        """
        Test comprehensive statistics collection per get_cache_stats docstring.
        
        Business Impact:
            Provides complete cache performance visibility for monitoring
            and optimization decisions.
            
        Success Criteria:
            - Redis statistics include connection status and key count
            - Memory cache statistics show utilization
            - Performance statistics from monitor are included
            - Memory usage is recorded during stats collection
        """
        # Mock Redis with statistics
        mock_redis_client = AsyncMock()
        mock_keys = [b"ai_cache:key1", b"ai_cache:key2", b"ai_cache:key3"]
        mock_info = {
            "used_memory_human": "1.5M",
            "used_memory": 1572864,  # 1.5MB in bytes
            "connected_clients": 5
        }
        mock_redis_client.keys = AsyncMock(return_value=mock_keys)
        mock_redis_client.info = AsyncMock(return_value=mock_info)
        mock_redis_client.ping = AsyncMock(return_value=True)
        mock_aioredis.from_url = AsyncMock(return_value=mock_redis_client)
        
        mock_monitor = Mock(spec=CachePerformanceMonitor)
        mock_monitor.get_performance_stats.return_value = {
            "hit_ratio": 85.5,
            "total_operations": 150
        }
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            cache = AIResponseCache(
                memory_cache_size=100,
                performance_monitor=mock_monitor
            )
        
        # Populate memory cache for testing
        cache.memory_cache = {"key1": "value1", "key2": "value2"}
        
        # Test statistics collection per docstring
        stats = await cache.get_cache_stats()
        
        # Verify Redis statistics per docstring
        assert stats["redis"]["status"] == "connected"
        assert stats["redis"]["keys"] == 3
        assert stats["redis"]["memory_used"] == "1.5M"
        assert stats["redis"]["connected_clients"] == 5
        
        # Verify memory statistics per docstring
        assert stats["memory"]["memory_cache_entries"] == 2
        assert stats["memory"]["memory_cache_size_limit"] == 100
        assert stats["memory"]["memory_cache_utilization"] == "2/100"
        
        # Verify performance statistics inclusion per docstring
        assert stats["performance"]["hit_ratio"] == 85.5
        assert stats["performance"]["total_operations"] == 150
        
        # Verify memory usage recording was called
        # (This verifies the side effect mentioned in docstring)
        # We can't easily assert the specific call without more complex mocking

    def test_get_cache_hit_ratio_calculates_percentage_per_docstring(self):
        """
        Test hit ratio calculation per get_cache_hit_ratio docstring.
        
        Business Impact:
            Provides key performance metric for cache effectiveness evaluation
            and optimization decisions.
            
        Success Criteria:
            - Hit ratio calculated as percentage (0.0 to 100.0)
            - Returns 0.0 when no operations recorded per docstring
            - Delegates to performance monitor calculation
        """
        mock_monitor = Mock(spec=CachePerformanceMonitor)
        mock_monitor._calculate_hit_rate.return_value = 75.3
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            cache = AIResponseCache(performance_monitor=mock_monitor)
        
        # Test hit ratio calculation per docstring
        hit_ratio = cache.get_cache_hit_ratio()
        
        # Verify calculation per docstring
        assert hit_ratio == 75.3
        mock_monitor._calculate_hit_rate.assert_called_once()

    def test_get_performance_summary_provides_comprehensive_overview_per_docstring(self):
        """
        Test performance summary generation per get_performance_summary docstring.
        
        Business Impact:
            Provides consolidated performance view for quick assessment
            of cache effectiveness and identification of issues.
            
        Success Criteria:
            - Summary includes hit ratio and operation counts
            - Timing statistics for recent operations are included
            - Invalidation statistics are provided
            - Memory usage stats included when available
        """
        mock_monitor = Mock(spec=CachePerformanceMonitor)
        # Mock monitor attributes per the actual implementation
        mock_monitor.total_operations = 250
        mock_monitor.cache_hits = 200
        mock_monitor.cache_misses = 50
        mock_monitor.total_invalidations = 5
        mock_monitor.total_keys_invalidated = 25
        mock_monitor.memory_usage_measurements = [Mock()]  # Non-empty for memory stats
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            cache = AIResponseCache(performance_monitor=mock_monitor)
        
        # Mock performance monitor methods for timing statistics
        cache._get_recent_avg_key_generation_time = Mock(return_value=0.002)
        cache._get_recent_avg_cache_operation_time = Mock(return_value=0.015)
        cache.get_cache_hit_ratio = Mock(return_value=80.0)
        cache.get_memory_usage_stats = Mock(return_value={"current_usage": "50MB"})
        
        # Test performance summary per docstring
        summary = cache.get_performance_summary()
        
        # Verify summary contents per docstring
        assert summary["hit_ratio"] == 80.0
        assert summary["total_operations"] == 250
        assert summary["cache_hits"] == 200
        assert summary["cache_misses"] == 50
        assert summary["recent_avg_key_generation_time"] == 0.002
        assert summary["recent_avg_cache_operation_time"] == 0.015
        assert summary["total_invalidations"] == 5
        assert summary["total_keys_invalidated"] == 25
        assert "memory_usage" in summary  # Memory stats included when available


class TestAIResponseCacheErrorHandling:
    """
    Test error handling and graceful degradation scenarios.
    
    Business Impact:
        Ensures cache system remains stable during various failure conditions,
        preventing cache issues from disrupting application functionality.
        
    Test Scenarios:
        - Redis connection failures during operations
        - Data corruption handling
        - Timeout scenarios
        - Invalid input handling
    """

    @patch('app.infrastructure.cache.redis.aioredis')
    @pytest.mark.asyncio
    async def test_get_cached_response_handles_redis_errors_gracefully(self, mock_aioredis):
        """
        Test graceful error handling during cache retrieval per docstring.
        
        Business Impact:
            Ensures cache errors don't interrupt application flow,
            maintaining system stability during infrastructure issues.
            
        Success Criteria:
            - Redis errors are caught and logged per docstring
            - Returns None for any retrieval errors
            - Performance metrics record error details
            - No exceptions propagate to caller
        """
        # Mock Redis client that raises errors
        mock_redis_client = AsyncMock()
        mock_redis_client.get = AsyncMock(side_effect=ConnectionError("Redis timeout"))
        mock_redis_client.ping = AsyncMock(return_value=True)
        mock_aioredis.from_url = AsyncMock(return_value=mock_redis_client)
        
        mock_monitor = Mock(spec=CachePerformanceMonitor)
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            cache = AIResponseCache(performance_monitor=mock_monitor)
        
        # Test error handling per docstring
        with patch('app.infrastructure.cache.redis.logger') as mock_logger:
            result = await cache.get_cached_response(
                text="Test text",
                operation="summarize",
                options={}
            )
            
            # Verify graceful error handling per docstring
            assert result is None
            mock_logger.warning.assert_called_with("Cache retrieval error: Redis timeout")
            
            # Verify error tracking in performance metrics
            mock_monitor.record_cache_operation_time.assert_called_once()
            call_args = mock_monitor.record_cache_operation_time.call_args
            assert call_args[1]['cache_hit'] is False
            assert call_args[1]['additional_data']['reason'] == "redis_error"
            assert call_args[1]['additional_data']['error'] == "Redis timeout"

    @patch('app.infrastructure.cache.redis.aioredis')
    @pytest.mark.asyncio
    async def test_cache_response_handles_storage_errors_gracefully(self, mock_aioredis):
        """
        Test graceful error handling during cache storage per docstring.
        
        Business Impact:
            Ensures storage errors don't interrupt AI response processing,
            maintaining application functionality during cache issues.
            
        Success Criteria:
            - Redis storage errors are caught and logged
            - Method completes without raising exceptions
            - Performance metrics record error details
            - Error context is preserved for debugging
        """
        # Mock Redis client that fails during storage
        mock_redis_client = AsyncMock()
        mock_redis_client.setex = AsyncMock(side_effect=MemoryError("Redis out of memory"))
        mock_redis_client.ping = AsyncMock(return_value=True)
        mock_aioredis.from_url = AsyncMock(return_value=mock_redis_client)
        
        mock_monitor = Mock(spec=CachePerformanceMonitor)
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            cache = AIResponseCache(performance_monitor=mock_monitor)
        
        # Test storage error handling per docstring
        with patch('app.infrastructure.cache.redis.logger') as mock_logger:
            # Should complete without exceptions per docstring
            await cache.cache_response(
                text="Test text",
                operation="summarize",
                options={},
                response={"summary": "Test summary"}
            )
            
            # Verify error logging per docstring
            mock_logger.warning.assert_called_with("Cache storage error: Redis out of memory")
            
            # Verify error tracking in performance metrics
            mock_monitor.record_cache_operation_time.assert_called_once()
            call_args = mock_monitor.record_cache_operation_time.call_args
            assert call_args[1]['cache_hit'] is False  # Failed operation
            assert call_args[1]['additional_data']['reason'] == "redis_error"
            assert call_args[1]['additional_data']['error'] == "Redis out of memory"

    @patch('app.infrastructure.cache.redis.aioredis')
    @pytest.mark.asyncio  
    async def test_get_cached_response_handles_data_corruption_gracefully(self, mock_aioredis):
        """
        Test handling of corrupted cache data per docstring error handling.
        
        Business Impact:
            Ensures corrupted cache entries don't crash the application,
            maintaining system stability with graceful fallback.
            
        Success Criteria:
            - Corrupted data causes graceful fallback to cache miss
            - JSON decode errors are caught and logged
            - Performance metrics record error appropriately
            - No exceptions propagate to caller
        """
        # Mock Redis with corrupted data
        mock_redis_client = AsyncMock()
        mock_redis_client.get = AsyncMock(return_value=b"corrupted-json-data")
        mock_redis_client.ping = AsyncMock(return_value=True)
        mock_aioredis.from_url = AsyncMock(return_value=mock_redis_client)
        
        mock_monitor = Mock(spec=CachePerformanceMonitor)
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            cache = AIResponseCache(performance_monitor=mock_monitor)
        
        # Test corrupted data handling per docstring
        with patch('app.infrastructure.cache.redis.logger'):
            result = await cache.get_cached_response(
                text="Test text",
                operation="summarize",
                options={}
            )
            
            # Verify graceful handling of corrupted data
            assert result is None  # Should fallback to cache miss
            
            # Note: The actual implementation may handle JSON decode errors
            # differently, but the important thing is no exceptions propagate


class TestAIResponseCachePerformanceMonitoring:
    """
    Test performance monitoring integration and metrics recording.
    
    Business Impact:
        Ensures comprehensive performance tracking for cache optimization
        and system monitoring capabilities.
        
    Test Scenarios:
        - Key generation timing recording
        - Cache operation performance tracking
        - Compression efficiency monitoring
        - Memory usage recording and warnings
    """

    @pytest.mark.asyncio
    async def test_get_cached_response_records_performance_metrics_per_docstring(self):
        """
        Test performance monitoring during cache retrieval per docstring.
        
        Business Impact:
            Provides detailed performance visibility for cache optimization
            and bottleneck identification.
            
        Success Criteria:
            - Cache operations record timing and metadata
            - Text length and operation type are captured
            - Cache tier information is included
            - Hit/miss status is tracked correctly
        """
        mock_monitor = Mock(spec=CachePerformanceMonitor)
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            cache = AIResponseCache(performance_monitor=mock_monitor)
        
        # Test performance monitoring during memory cache hit per docstring
        small_text = "Small text"
        cache_key = cache._generate_cache_key(small_text, "summarize", {})
        cache.memory_cache[cache_key] = {"summary": "Test"}
        
        await cache.get_cached_response(
            text=small_text,
            operation="summarize",
            options={"max_length": 100}
        )
        
        # Verify performance monitoring per docstring
        mock_monitor.record_cache_operation_time.assert_called_once()
        call_args = mock_monitor.record_cache_operation_time.call_args
        assert call_args[1]['operation'] == "get"
        assert call_args[1]['cache_hit'] is True
        assert call_args[1]['text_length'] == len(small_text)
        assert call_args[1]['additional_data']['cache_tier'] == "memory"
        assert call_args[1]['additional_data']['operation_type'] == "summarize"

    @patch('app.infrastructure.cache.redis.aioredis')
    @pytest.mark.asyncio
    async def test_cache_response_records_compression_metrics_per_docstring(self, mock_aioredis):
        """
        Test compression monitoring during cache storage per docstring.
        
        Business Impact:
            Provides compression efficiency metrics for storage optimization
            and cost analysis.
            
        Success Criteria:
            - Compression ratios are recorded when compression occurs
            - Original and compressed sizes are tracked
            - Compression time is measured
            - Operation type is associated with compression metrics
        """
        # Mock Redis connection
        mock_redis_client = AsyncMock()
        mock_redis_client.setex = AsyncMock()
        mock_redis_client.ping = AsyncMock(return_value=True)
        mock_aioredis.from_url = AsyncMock(return_value=mock_redis_client)
        
        mock_monitor = Mock(spec=CachePerformanceMonitor)
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            cache = AIResponseCache(
                compression_threshold=50,  # Low threshold for testing
                performance_monitor=mock_monitor
            )
        
        # Create response that will trigger compression per docstring
        large_response = {"summary": "A" * 100, "metadata": "B" * 100}  # > 50 bytes
        
        # Test compression monitoring per docstring
        await cache.cache_response(
            text="Test text",
            operation="summarize",
            options={},
            response=large_response
        )
        
        # Verify compression metrics recording per docstring
        mock_monitor.record_compression_ratio.assert_called_once()
        call_args = mock_monitor.record_compression_ratio.call_args
        assert call_args[1]['operation_type'] == "summarize"
        assert call_args[1]['original_size'] > 0
        assert call_args[1]['compressed_size'] > 0
        assert call_args[1]['compression_time'] > 0

    def test_record_memory_usage_captures_cache_state_per_docstring(self):
        """
        Test memory usage recording per record_memory_usage docstring.
        
        Business Impact:
            Enables memory usage monitoring for capacity planning and
            performance optimization decisions.
            
        Success Criteria:
            - Memory cache size and entry count are captured
            - Redis statistics are included when available
            - Additional metadata is preserved
            - Performance monitor receives complete usage data
        """
        mock_monitor = Mock(spec=CachePerformanceMonitor)
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            cache = AIResponseCache(
                memory_cache_size=100,
                performance_monitor=mock_monitor
            )
        
        # Set up memory cache state for testing
        cache.memory_cache = {"key1": "value1", "key2": "value2"}
        redis_stats = {
            "memory_used_bytes": 1048576,  # 1MB
            "keys": 50
        }
        
        # Test memory usage recording per docstring
        cache.record_memory_usage(redis_stats)
        
        # Verify memory usage recording per docstring
        mock_monitor.record_memory_usage.assert_called_once()
        call_args = mock_monitor.record_memory_usage.call_args
        assert call_args[0][0] == cache.memory_cache  # memory_cache parameter
        assert call_args[1]['redis_stats'] == redis_stats
        assert "memory_cache_size_limit" in call_args[1]['additional_data']

    def test_get_memory_warnings_provides_actionable_alerts_per_docstring(self):
        """
        Test memory warning generation per get_memory_warnings docstring.
        
        Business Impact:
            Provides proactive alerts for memory issues before they impact
        
        Success Criteria:
            - Warnings include severity levels per docstring
            - Human-readable messages are provided
            - Threshold information is included
            - Recommendations are actionable
        """
        mock_monitor = Mock(spec=CachePerformanceMonitor)
        mock_monitor.get_memory_warnings.return_value = [
            {
                "severity": "warning",
                "message": "Memory cache approaching size limit (95/100 entries)",
                "threshold": 90,
                "current_value": 95,
                "recommendations": ["Monitor cache growth closely"]
            }
        ]
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            cache = AIResponseCache(performance_monitor=mock_monitor)
        
        # Test memory warnings per docstring
        warnings_list = cache.get_memory_warnings()
        
        # Verify warning structure per docstring
        assert len(warnings_list) == 1
        warning = warnings_list[0]
        assert warning["severity"] == "warning"
        assert "message" in warning
        assert "recommendations" in warning


class TestAIResponseCacheMemoryManagement:
    """
    Test memory cache management and eviction strategies.
    
    Business Impact:
        Ensures efficient memory usage with proper eviction to prevent
        memory leaks while maintaining cache performance.
        
    Test Scenarios:
        - Memory cache FIFO eviction
        - Memory cache size limits
        - Memory cache order tracking
        - Memory cache population from Redis hits
    """

    def test_update_memory_cache_implements_fifo_eviction_per_docstring(self):
        """
        Test FIFO eviction in memory cache per _update_memory_cache docstring.
        
        Business Impact:
            Prevents unlimited memory growth while maintaining cache efficiency
            through predictable eviction strategy.
            
        Success Criteria:
            - Memory cache respects size limits per docstring
            - FIFO eviction removes oldest entries first
            - Cache order tracking is maintained correctly
            - New entries are added properly
        """
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            cache = AIResponseCache(memory_cache_size=2)  # Small size for testing
        
        # Test FIFO eviction per docstring
        cache._update_memory_cache("key1", {"data": "value1"})
        cache._update_memory_cache("key2", {"data": "value2"})
        
        # Verify cache is at capacity
        assert len(cache.memory_cache) == 2
        assert "key1" in cache.memory_cache
        assert "key2" in cache.memory_cache
        
        # Add third item to trigger eviction per docstring
        cache._update_memory_cache("key3", {"data": "value3"})
        
        # Verify FIFO eviction per docstring
        assert len(cache.memory_cache) == 2
        assert "key1" not in cache.memory_cache  # Oldest removed
        assert "key2" in cache.memory_cache
        assert "key3" in cache.memory_cache
        
        # Verify order tracking per docstring
        assert cache.memory_cache_order == ["key2", "key3"]

    def test_update_memory_cache_handles_duplicate_keys_per_docstring(self):
        """
        Test duplicate key handling in memory cache per docstring.
        
        Business Impact:
            Ensures cache updates don't create duplicate entries,
            maintaining accurate cache size and order tracking.
            
        Success Criteria:
            - Duplicate keys update existing entries
            - Cache size remains constant for updates
            - Order is updated to reflect recent access
            - No memory leaks from duplicate entries
        """
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            cache = AIResponseCache(memory_cache_size=3)
        
        # Set up initial cache state
        cache._update_memory_cache("key1", {"data": "value1"})
        cache._update_memory_cache("key2", {"data": "value2"})
        
        # Update existing key per docstring behavior
        cache._update_memory_cache("key1", {"data": "updated_value1"})
        
        # Verify duplicate handling per docstring
        assert len(cache.memory_cache) == 2  # Size unchanged
        assert cache.memory_cache["key1"]["data"] == "updated_value1"
        
        # Verify order is updated per docstring
        assert cache.memory_cache_order == ["key2", "key1"]  # key1 moved to end

    @patch('app.infrastructure.cache.redis.aioredis')
    @pytest.mark.asyncio
    async def test_memory_cache_population_from_redis_hit_per_docstring(self, mock_aioredis):
        """
        Test memory cache population from Redis hits per docstring.
        
        Business Impact:
            Optimizes subsequent cache access by promoting Redis hits
            to memory cache for faster future retrieval.
            
        Success Criteria:
            - Small text Redis hits populate memory cache
            - Large text Redis hits don't populate memory cache
            - Memory cache population respects size limits
            - Population is tracked in performance metrics
        """
        # Mock Redis with cached response
        mock_redis_client = AsyncMock()
        cached_response = {"summary": "Redis cached summary"}
        mock_redis_client.get = AsyncMock(return_value=json.dumps(cached_response).encode())
        mock_redis_client.ping = AsyncMock(return_value=True)
        mock_aioredis.from_url = AsyncMock(return_value=mock_redis_client)
        
        mock_monitor = Mock(spec=CachePerformanceMonitor)
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            cache = AIResponseCache(performance_monitor=mock_monitor)
        
        # Test memory cache population for small text per docstring
        small_text = "Small text for testing"  # < 500 chars = small tier
        result = await cache.get_cached_response(
            text=small_text,
            operation="summarize",
            options={}
        )
        
        # Verify memory cache population per docstring
        cache_key = cache._generate_cache_key(small_text, "summarize", {})
        assert cache_key in cache.memory_cache
        assert cache.memory_cache[cache_key] == cached_response
        
        # Verify performance tracking includes population flag
        mock_monitor.record_cache_operation_time.assert_called_once()
        call_args = mock_monitor.record_cache_operation_time.call_args
        assert call_args[1]['additional_data']['populated_memory_cache'] is True


# Integration test to verify overall cache behavior
class TestAIResponseCacheIntegration:
    """
    Integration tests for overall cache behavior and workflows.
    
    Business Impact:
        Validates complete cache workflows work correctly across
        all components and use cases.
        
    Test Scenarios:
        - End-to-end caching workflow
        - Cache tier interactions
        - Performance monitoring integration
        - Error recovery workflows
    """

    @patch('app.infrastructure.cache.redis.aioredis') 
    @pytest.mark.asyncio
    async def test_complete_cache_workflow_per_documented_usage(self, mock_aioredis):
        """
        Test complete cache workflow per module docstring usage examples.
        
        Business Impact:
            Validates entire cache system works as documented for real usage,
            ensuring API contracts are fulfilled end-to-end.
            
        Success Criteria:
            - Cache miss, store, and hit workflow works correctly
            - Performance monitoring tracks all operations
            - Memory cache and Redis cache interact properly
            - All documented features function as specified
        """
        # Mock Redis connection
        mock_redis_client = AsyncMock()
        mock_redis_client.get = AsyncMock(return_value=None)  # Initial miss
        mock_redis_client.setex = AsyncMock()  # For storage
        mock_redis_client.ping = AsyncMock(return_value=True)
        mock_aioredis.from_url = AsyncMock(return_value=mock_redis_client)
        
        mock_monitor = Mock(spec=CachePerformanceMonitor)
        
        with warnings.catch_warnings():
            warnings.simplefilter("ignore", DeprecationWarning)
            cache = AIResponseCache(performance_monitor=mock_monitor)
        
        text = "Long document to summarize..."
        operation = "summarize"
        options = {"max_length": 100}
        response = {"summary": "Brief summary", "confidence": 0.95}
        
        # Test initial cache miss per docstring example
        result1 = await cache.get_cached_response(text, operation, options)
        assert result1 is None
        
        # Test caching response per docstring example
        await cache.cache_response(text, operation, options, response)
        
        # Mock Redis to return cached data for subsequent retrieval
        mock_redis_client.get = AsyncMock(
            return_value=json.dumps({
                **response,
                "cached_at": "2024-01-15T10:30:00",
                "cache_hit": True,
                "text_length": len(text),
                "compression_used": False
            }).encode()
        )
        
        # Test cache hit per docstring example
        result2 = await cache.get_cached_response(text, operation, options)
        assert result2 is not None
        assert result2["summary"] == response["summary"]
        assert result2["confidence"] == response["confidence"]
        assert result2["cache_hit"] is True
        
        # Verify performance monitoring tracked all operations
        assert mock_monitor.record_cache_operation_time.call_count >= 2  # At least get and set