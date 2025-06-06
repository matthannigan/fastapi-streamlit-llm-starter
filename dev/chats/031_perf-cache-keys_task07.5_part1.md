# Implement integration tests for Redis cache
_Exported on 6/5/2025 at 22:50:37 EDT from Cursor (1.0.0)_

---

**User**

Execute Task 7.5: Implement Integration Tests for Redis Cache Interactions

---

**Cursor**

I'll help you implement integration tests for Redis cache interactions. Let me first examine the current test structure and Redis implementation to understand what needs to be tested.

Now let me check if there are any existing Redis integration tests and examine the cache service implementation:

Now let me look at the existing Redis connection and operation methods:

Let me read the cache_response method and other Redis operations:

Let me look at the invalidation methods to understand all Redis operations:

Now I have a comprehensive understanding of the Redis operations that need integration testing. Let me implement the integration tests for Redis cache interactions as specified in Task 7.5:

```python
# ... existing code ...

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
```

Now let me run the tests to verify they work correctly:

I need to add the missing asyncio import. Let me fix that:

```python
"""Tests for AI response cache functionality."""

import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import json
import hashlib
import time
from datetime import datetime

from app.services.cache import AIResponseCache, CacheKeyGenerator
from app.services.monitoring import CachePerformanceMonitor

->

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
```

Now let me run the tests again:

Perfect! All 14 Redis integration tests are now passing. Let me also run a broader test to make sure I didn't break any existing tests:

Excellent! All 144 tests are passing, including the 14 new Redis integration tests. Now let me update the task documentation to reflect the completion:

Now let me mark the subtask as complete:

Perfect! Now let me check the overall task status to see if Task 7 is complete:

Great! All subtasks are complete. Now I should mark the overall task as completed:

Perfect! Task 7 has been completed successfully. Let me provide a summary of what was accomplished:

## Task 7.5: Implement Integration Tests for Redis Cache Interactions - **COMPLETED** ✅

I have successfully executed Task 7.5 and implemented comprehensive integration tests for Redis cache interactions. Here's what was accomplished:

### **Implementation Summary:**

**✅ Created `TestRedisIntegrationTests` class with 14 comprehensive integration tests**
- All tests pass successfully
- Comprehensive coverage of all Redis cache interactions
- Proper mocking to avoid external dependencies

### **Key Test Coverage Areas:**

#### **1. Core Redis Operations**
- **`test_redis_set_operation_stores_data_correctly`** - Verifies Redis setex operations store data with proper serialization and TTL
- **`test_redis_get_operation_retrieves_data_correctly`** - Verifies Redis get operations retrieve and deserialize data correctly  
- **`test_redis_get_operation_returns_none_for_missing_data`** - Verifies cache miss behavior returns None

#### **2. TTL/Expiration Settings**
- **`test_redis_expiration_settings_work_as_expected`** - Comprehensive TTL testing for all operation types:
  - summarize: 7200s (2 hours)
  - sentiment: 86400s (24 hours) 
  - key_points: 7200s (2 hours)
  - questions: 3600s (1 hour)
  - qa: 1800s (30 minutes)
  - custom operations: 1800s (default)

#### **3. Error Handling & Connection Issues**
- **`test_redis_connection_error_handling`** - Connection failure graceful degradation
- **`test_redis_unavailable_graceful_degradation`** - When Redis unavailable
- **`test_redis_operation_error_handling_during_get`** - Redis get operation failures
- **`test_redis_operation_error_handling_during_set`** - Redis setex operation failures

#### **4. Advanced Integration Features**
- **`test_redis_invalidation_operations`** - Pattern-based invalidation (invalidate_by_operation, invalidate_all)
- **`test_redis_stats_collection`** - Cache statistics collection (keys count, memory usage, connection status)
- **`test_redis_compression_integration`** - Redis integration with data compression for large responses
- **`test_redis_binary_data_handling`** - Binary data handling for compressed and raw data
- **`test_redis_concurrent_operations_simulation`** - Concurrent access (3 workers × 5 operations each)
- **`test_redis_memory_tier_integration`** - Multi-tier cache behavior (memory cache for small texts, Redis for large)

### **Technical Achievements:**

#### **Comprehensive Mock Redis Client**
- Simulates actual Redis data storage with `_data` and `_ttls` dictionaries
- Implements all major Redis operations: GET, SETEX, DELETE, KEYS, INFO, PING
- Handles binary/string key conversions appropriately
- Supports pattern matching for invalidation operations
- Provides realistic Redis info statistics

#### **Integration Quality**
- ✅ Proper mocking avoids external Redis dependencies in unit tests
- ✅ Full integration with existing cache compression/decompression system
- ✅ Comprehensive error handling validation
- ✅ Multi-tier cache behavior validation
- ✅ Concurrent operation safety verification
- ✅ TTL and expiration setting validation for all operation types
- ✅ Binary data handling for compressed responses
- ✅ Pattern-based cache invalidation testing

### **Test Results:**
- **All 14 Redis integration tests: PASSED** ✅
- **All 144 total cache tests: PASSED** ✅
- No regressions in existing functionality

### **Task Completion:**
Task 7 (Unit Tests for New Caching Logic) is now **COMPLETE** with all 5 subtasks finished:
1. ✅ Unit Tests for CacheKeyGenerator 
2. ✅ Unit Tests for AIResponseCache Tier Selection
3. ✅ Unit Tests for Memory Cache Operations  
4. ✅ Unit Tests for Data Compression/Decompression
5. ✅ **Integration Tests for Redis Cache Interactions**

The caching system now has comprehensive test coverage ensuring reliability, performance, and proper error handling across all Redis interactions.

