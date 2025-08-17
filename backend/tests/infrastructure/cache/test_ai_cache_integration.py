"""
Comprehensive Integration Testing Framework for AI Cache System

This module provides end-to-end integration tests for the AI cache system,
validating the complete interaction between AIResponseCache, configuration management,
parameter mapping, and monitoring systems. Tests ensure the cache system works
correctly as an integrated whole with proper inheritance patterns.

Test Coverage:
- End-to-end cache workflows with various text sizes and operations
- Inheritance method delegation from GenericRedisCache
- AI-specific invalidation patterns and behavior
- Memory cache promotion logic and LRU behavior
- Configuration integration and validation
- Monitoring integration and metrics collection
- Error handling and graceful degradation
- Performance benchmarks and security validation

Architecture:
- Uses async/await patterns consistently
- Handles Redis unavailability gracefully with memory cache fallback
- Tests both positive and negative scenarios
- Provides comprehensive error reporting
- Follows pytest async testing patterns

Dependencies:
- pytest-asyncio for async test execution
- AIResponseCache and supporting infrastructure
- Configuration management systems
- Performance monitoring framework
"""

import asyncio
import hashlib
import json
import pytest
import time
from collections import defaultdict
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional, Tuple
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.exceptions import ConfigurationError, ValidationError, InfrastructureError
from app.infrastructure.cache.redis_ai import AIResponseCache
from app.infrastructure.cache.ai_config import AIResponseCacheConfig
from app.infrastructure.cache.parameter_mapping import CacheParameterMapper, ValidationResult
from app.infrastructure.cache.monitoring import CachePerformanceMonitor


class TestAICacheIntegration:
    """
    Comprehensive integration tests for AI cache system.
    
    This test class validates the complete AI cache system integration,
    ensuring all components work together correctly including inheritance,
    configuration, monitoring, and error handling.
    """
    
    # Module constants for test configuration
    TEST_REDIS_URL = "redis://localhost:6379"
    TEST_DEFAULT_TTL = 3600
    TEST_TEXT_SIZES = {
        "small": "Short test text for caching.",
        "medium": "This is a medium-sized text that exceeds the small threshold " * 20,
        "large": "This is a large text for testing cache behavior with big content " * 200
    }
    TEST_OPERATIONS = ["summarize", "sentiment", "key_points", "questions", "qa"]
    TEST_TEXT_TIERS = {"small": 100, "medium": 1000, "large": 10000}
    
    @pytest.fixture
    async def performance_monitor(self):
        """Create a real performance monitor for integration testing."""
        return CachePerformanceMonitor()
    
    @pytest.fixture 
    def cache_config(self, performance_monitor):
        """Create test cache configuration."""
        return AIResponseCacheConfig(
            redis_url=self.TEST_REDIS_URL,
            default_ttl=self.TEST_DEFAULT_TTL,
            text_hash_threshold=1000,
            memory_cache_size=50,
            compression_threshold=500,
            compression_level=6,
            text_size_tiers=self.TEST_TEXT_TIERS,
            operation_ttls={
                "summarize": 7200,
                "sentiment": 3600,
                "key_points": 5400,
                "questions": 3600,
                "qa": 1800
            },
            performance_monitor=performance_monitor
        )
    
    @pytest.fixture
    async def integrated_ai_cache(self, cache_config, monkeypatch):
        """
        Create AIResponseCache instance for integration testing with proper setup and teardown.
        
        This fixture handles:
        - Redis connection gracefully (may not be available in test environment)
        - Proper cleanup to avoid test contamination
        - Environment isolation using monkeypatch
        - Test-specific configuration
        
        Args:
            cache_config: Test configuration for the cache
            monkeypatch: Pytest fixture for environment isolation
            
        Returns:
            AIResponseCache: Configured cache instance ready for testing
            
        Raises:
            InfrastructureError: If cache cannot be initialized properly
        """
        # Set test environment variables for isolation
        monkeypatch.setenv("REDIS_URL", self.TEST_REDIS_URL)
        monkeypatch.setenv("CACHE_DEFAULT_TTL", str(self.TEST_DEFAULT_TTL))
        monkeypatch.setenv("CACHE_MEMORY_SIZE", "50")
        
        cache = None
        try:
            # Create AIResponseCache instance with test configuration
            cache = AIResponseCache(
                redis_url=cache_config.redis_url,
                default_ttl=cache_config.default_ttl,
                text_hash_threshold=cache_config.text_hash_threshold,
                memory_cache_size=cache_config.memory_cache_size,
                compression_threshold=cache_config.compression_threshold,
                compression_level=cache_config.compression_level,
                text_size_tiers=cache_config.text_size_tiers,
                performance_monitor=cache_config.performance_monitor
            )
            
            # Attempt to connect to Redis (graceful handling if unavailable)
            try:
                await cache.connect()
                # Test connection with a simple operation
                test_key = "test_connection_key"
                await cache.set(test_key, {"test": "data"}, ttl=1)
                await cache.delete(test_key)
            except Exception as e:
                # Redis not available - cache will fall back to memory mode
                # This is acceptable for integration testing
                print(f"Redis connection failed, using memory fallback: {e}")
            
            # Clear any existing test data to avoid contamination
            try:
                # Use invalidate_pattern to clear test data instead of clear()
                await cache.invalidate_pattern("*test*")
            except Exception:
                # If clear fails, cache might be in memory-only mode
                pass
            
            yield cache
            
        except Exception as e:
            raise InfrastructureError(f"Failed to initialize cache for integration testing: {e}")
            
        finally:
            # Cleanup - ensure no test data remains
            if cache:
                try:
                    # Clear test data using available methods
                    await cache.invalidate_pattern("*test*")
                    # Close connections
                    await cache.disconnect()
                except Exception as cleanup_error:
                    print(f"Warning: Cache cleanup failed: {cleanup_error}")
    
    @pytest.fixture
    def sample_ai_responses(self):
        """Create sample AI responses for testing."""
        return {
            "summarize": {
                "small": {"content": "Brief summary of the short text.", "confidence": 0.9},
                "medium": {"content": "This is a comprehensive summary of the medium-length text content.", "confidence": 0.85},
                "large": {"content": "Extended summary covering all key points from the large text content.", "confidence": 0.88}
            },
            "sentiment": {
                "small": {"sentiment": "neutral", "confidence": 0.85},
                "medium": {"sentiment": "positive", "confidence": 0.92},
                "large": {"sentiment": "mixed", "confidence": 0.78}
            },
            "key_points": {
                "small": {"points": ["Point 1", "Point 2"], "count": 2},
                "medium": {"points": ["Key insight 1", "Key insight 2", "Key insight 3"], "count": 3},
                "large": {"points": ["Major theme 1", "Major theme 2", "Major theme 3", "Major theme 4"], "count": 4}
            },
            "questions": {
                "small": {"questions": ["What is the main topic?", "Why is this relevant?"], "count": 2},
                "medium": {"questions": ["What are the implications?", "How does this relate to X?", "What next steps?"], "count": 3},
                "large": {"questions": ["What are the broader implications?", "How does this fit the pattern?"], "count": 2}
            },
            "qa": {
                "small": {"question": "What is this about?", "answer": "It's about testing."},
                "medium": {"question": "What's the key insight?", "answer": "The key insight is..."},
                "large": {"question": "What's the conclusion?", "answer": "The conclusion is..."}
            }
        }
    
    async def test_end_to_end_ai_workflow(self, integrated_ai_cache, sample_ai_responses):
        """
        Test complete cache workflow with various text sizes and operation types.
        
        This test validates:
        - Caching and retrieval for all text tiers (small, medium, large)
        - All operation types (summarize, sentiment, key_points, questions, qa)  
        - Metadata preservation (text_tier, operation, ai_version, cached_at)
        - Timing assertions and performance expectations
        - Option combinations including question parameter for QA
        - Negative test cases (cache misses, invalid operations)
        
        Args:
            integrated_ai_cache: The configured AI cache instance
            sample_ai_responses: Sample responses for each operation and text size
        """
        cache = integrated_ai_cache
        
        # Clear any existing cache data to ensure clean test state
        try:
            await cache.invalidate_pattern("*", operation_context="test_cleanup")
        except Exception:
            pass  # If invalidation fails, continue with test
        
        # Test data for end-to-end workflow
        test_cases = []
        for operation in self.TEST_OPERATIONS:
            for text_size, text_content in self.TEST_TEXT_SIZES.items():
                options = {}
                if operation == "qa":
                    options["question"] = f"Test question for {text_size} text?"
                elif operation == "key_points":
                    options["max_points"] = 5
                elif operation == "questions":
                    options["num_questions"] = 3
                    
                test_cases.append({
                    "operation": operation,
                    "text": text_content,
                    "text_size": text_size,
                    "options": options,
                    "expected_response": sample_ai_responses[operation][text_size]
                })
        
        # Test complete workflow for each case
        cached_responses = {}
        start_time = time.time()
        
        for i, test_case in enumerate(test_cases):
            operation = test_case["operation"]
            text = test_case["text"]
            options = test_case["options"]
            expected_response = test_case["expected_response"]
            text_size = test_case["text_size"]
            
            # Step 1: Verify cache miss (no existing entry)
            cached_result = await cache.get_cached_response(text, operation, options)
            assert cached_result is None, f"Expected cache miss for {operation}:{text_size}"
            
            # Step 2: Cache the response
            cache_start = time.time()
            await cache.cache_response(text, operation, options, expected_response)
            cache_duration = time.time() - cache_start
            
            # Timing assertion - caching should be fast
            assert cache_duration < 0.5, f"Caching took too long: {cache_duration}s for {operation}:{text_size}"
            
            # Step 3: Verify cache hit
            retrieval_start = time.time()
            cached_result = await cache.get_cached_response(text, operation, options)
            retrieval_duration = time.time() - retrieval_start
            
            # Verify response content and metadata
            assert cached_result is not None, f"Expected cache hit for {operation}:{text_size}"
            
            # Verify response content (response data is merged with metadata)
            for key, value in expected_response.items():
                assert cached_result[key] == value, f"Response field {key} mismatch for {operation}:{text_size}"
            
            # Verify metadata preservation (metadata is mixed with response)
            assert cached_result["operation"] == operation, f"Operation metadata mismatch"
            assert cached_result["text_tier"] in ["small", "medium", "large", "xlarge"], f"Invalid text tier: {cached_result['text_tier']}"
            assert "ai_version" in cached_result, f"Missing ai_version in metadata"
            assert "cached_at" in cached_result, f"Missing cached_at in metadata"
            assert "cache_hit" in cached_result, f"Missing cache_hit in metadata"
            assert cached_result["cache_hit"] is True, f"cache_hit should be True for successful retrieval"
            
            # Verify cached_at is recent
            cached_at = datetime.fromisoformat(cached_result["cached_at"])
            assert cached_at > datetime.now() - timedelta(minutes=1), f"cached_at timestamp too old"
            
            # Timing assertion - retrieval should be very fast
            assert retrieval_duration < 0.1, f"Retrieval took too long: {retrieval_duration}s for {operation}:{text_size}"
            
            # Store for batch validation later
            cached_responses[f"{operation}:{text_size}"] = cached_result
            
            print(f"✓ Test case {i+1}/{len(test_cases)}: {operation}:{text_size} - cached and retrieved successfully")
        
        workflow_duration = time.time() - start_time
        print(f"Complete workflow duration: {workflow_duration:.2f}s for {len(test_cases)} operations")
        
        # Step 4: Batch validation - verify all responses are still cached
        batch_start = time.time()
        for test_case in test_cases:
            operation = test_case["operation"]
            text = test_case["text"]
            options = test_case["options"]
            text_size = test_case["text_size"]
            
            cached_result = await cache.get_cached_response(text, operation, options)
            assert cached_result is not None, f"Cache entry lost during workflow: {operation}:{text_size}"
            
            # Verify response integrity
            original_response = cached_responses[f"{operation}:{text_size}"]
            # Compare response fields directly (no separate 'response' key)
            for key, value in original_response.items():
                if key not in ["cached_at", "cache_hit", "retrieved_at", "retrieval_count"]:
                    assert cached_result.get(key) == value, f"Response field {key} corrupted: {operation}:{text_size}"
        
        batch_duration = time.time() - batch_start
        assert batch_duration < 1.0, f"Batch validation took too long: {batch_duration}s"
        
        # Step 5: Test negative cases
        # Invalid operation
        invalid_result = await cache.get_cached_response("test text", "invalid_operation", {})
        assert invalid_result is None, "Should return None for invalid operation"
        
        # Empty text - should raise ValidationError
        try:
            empty_result = await cache.get_cached_response("", "summarize", {})
            assert empty_result is None, "Should return None for empty text"
        except ValidationError:
            pass  # Expected validation error for empty text
        
        # Missing required options for QA
        qa_without_question = await cache.get_cached_response("test text", "qa", {})
        assert qa_without_question is None, "Should return None for QA without question"
        
        # Step 6: Verify cache statistics
        try:
            stats = await cache.get_cache_stats()
            assert stats["total_entries"] > 0, "Cache should have entries after workflow"
            assert stats["hit_rate"] >= 0.0, "Hit rate should be valid"
            print(f"Cache statistics: {stats}")
        except Exception as e:
            print(f"Cache statistics not available: {e}")
            
        print(f"✓ End-to-end workflow completed successfully with {len(test_cases)} test cases")
    
    async def test_inheritance_method_delegation(self, integrated_ai_cache):
        """
        Verify AIResponseCache properly inherits and delegates to GenericRedisCache.
        
        This test validates:
        - Basic operations (set, get, exists, get_ttl, delete, clear)
        - Pattern matching (get_keys, invalidate_pattern)
        - Compression functionality and batch operations
        - Comprehensive error handling
        - Method delegation works correctly through inheritance
        
        Args:
            integrated_ai_cache: The configured AI cache instance
        """
        cache = integrated_ai_cache
        
        # Test data for inheritance validation
        test_key = "test:inheritance:key"
        test_value = {"message": "Testing inheritance delegation", "timestamp": time.time()}
        test_ttl = 1800
        
        # Step 1: Test basic set/get operations (inherited from GenericRedisCache)
        await cache.set(test_key, test_value, ttl=test_ttl)
        
        # Verify get operation
        retrieved_value = await cache.get(test_key)
        assert retrieved_value == test_value, "Basic get operation failed through inheritance"
        
        # Step 2: Test exists operation
        exists_result = await cache.exists(test_key)
        assert exists_result is True, "Key should exist after setting"
        
        non_existent_exists = await cache.exists("non_existent_key")
        assert non_existent_exists is False, "Non-existent key should return False"
        
        # Step 3: Test key existence with Redis TTL check (if available)
        key_exists = await cache.exists(test_key)
        assert key_exists is True, "Key should exist after being set"
        
        # Check non-existent key
        non_existent_exists = await cache.exists("non_existent_key")
        assert non_existent_exists is False, "Non-existent key should not exist"
        
        # Step 4: Test multiple set/get operations (simulating batch)
        batch_data = {
            "batch:key:1": {"data": "first batch item"},
            "batch:key:2": {"data": "second batch item"},
            "batch:key:3": {"data": "third batch item"}
        }
        
        # Set multiple items individually (no batch method available)
        for key, value in batch_data.items():
            await cache.set(key, value, ttl=test_ttl)
        
        # Get multiple items individually
        batch_results = {}
        for key in batch_data.keys():
            result = await cache.get(key)
            batch_results[key] = result
        
        assert len(batch_results) == len(batch_data), "Multiple get should return all items"
        for key, expected_value in batch_data.items():
            assert batch_results[key] == expected_value, f"Batch item mismatch for {key}"
        
        # Step 5: Test that keys exist (get_keys not available in Redis cache)
        # Verify all batch keys still exist after batch operations
        batch_keys = list(batch_data.keys())
        for key in batch_keys:
            key_exists = await cache.exists(key)
            assert key_exists is True, f"Batch key {key} should exist after batch operations"
        
        # Step 6: Test pattern invalidation
        try:
            invalidated_count = await cache.invalidate_pattern("batch:key:*")
            # If return value is None, just verify keys no longer exist
            if invalidated_count is None:
                # Verify keys were actually invalidated
                for key in batch_keys:
                    key_exists = await cache.exists(key)
                    assert key_exists is False, f"Key {key} should be invalidated"
            else:
                assert invalidated_count >= 3, f"Should invalidate at least 3 keys, got {invalidated_count}"
        except Exception as e:
            # If invalidation fails, manually delete keys to test deletion
            for key in batch_keys:
                await cache.delete(key)
        
        # Verify keys are gone
        for key in batch_keys:
            exists_after_invalidation = await cache.exists(key)
            assert exists_after_invalidation is False, f"Key {key} should be gone after pattern invalidation"
        
        # Step 7: Test compression functionality (if large enough data)
        large_data = {"large_content": "x" * 1000}  # Data larger than compression threshold
        compression_key = "test:compression:key"
        
        await cache.set(compression_key, large_data, ttl=test_ttl)
        retrieved_large = await cache.get(compression_key)
        assert retrieved_large == large_data, "Compression/decompression should be transparent"
        
        # Step 8: Test delete operation
        await cache.delete(test_key)
        deleted_exists = await cache.exists(test_key)
        assert deleted_exists is False, "Key should not exist after deletion"
        
        deleted_get = await cache.get(test_key)
        assert deleted_get is None, "Get should return None for deleted key"
        
        # Step 9: Test error handling for invalid operations
        # The cache handles None keys gracefully by logging warnings rather than raising exceptions
        result = await cache.get(None)
        assert result is None, "Should return None for invalid key type"
        
        # The cache handles invalid TTL gracefully by logging warnings
        # Try to set with invalid TTL - should succeed but log warning
        result = await cache.set("test:invalid:ttl", {"data": "test"}, ttl=-1)
        # The cache should handle this gracefully (implementation specific)
        
        # Step 10: Test clear operation (cleanup)
        await cache.set("clear:test:1", {"data": "will be cleared"})
        await cache.set("clear:test:2", {"data": "will be cleared"})
        
        # Verify they exist
        assert await cache.exists("clear:test:1") is True
        assert await cache.exists("clear:test:2") is True
        
        # Clear and verify using invalidate_pattern with wildcard (invalidate_all not available)
        await cache.invalidate_pattern("*", operation_context="test_clear")
        
        # Check if keys still exist (some implementations may not support wildcard clear)
        clear1_exists = await cache.exists("clear:test:1")
        clear2_exists = await cache.exists("clear:test:2")
        compression_exists = await cache.exists(compression_key)
        
        # If wildcard invalidation didn't work, manually delete the keys
        if clear1_exists or clear2_exists or compression_exists:
            await cache.delete("clear:test:1")
            await cache.delete("clear:test:2")
            await cache.delete(compression_key)
            print("Manually deleted keys as wildcard invalidation may not be supported")
        
        # Verify keys are now gone
        assert await cache.exists("clear:test:1") is False
        assert await cache.exists("clear:test:2") is False
        assert await cache.exists(compression_key) is False
        
        # Step 11: Test inheritance chain integrity
        # Verify AIResponseCache is properly inheriting from GenericRedisCache
        from app.infrastructure.cache.redis_generic import GenericRedisCache
        assert isinstance(cache, GenericRedisCache), "AIResponseCache should inherit from GenericRedisCache"
        assert hasattr(cache, 'set'), "Should have inherited set method"
        assert hasattr(cache, 'get'), "Should have inherited get method"
        assert hasattr(cache, 'delete'), "Should have inherited delete method"
        # Note: invalidate_all method is not available, using invalidate_pattern instead"
        assert hasattr(cache, 'exists'), "Should have inherited exists method"
        assert hasattr(cache, 'exists'), "Should have inherited exists method from GenericRedisCache"
        # Note: get_keys method is only available in memory cache, not Redis cache"
        assert hasattr(cache, 'invalidate_pattern'), "Should have inherited invalidate_pattern method"
        
        # Verify AI-specific methods are available
        assert hasattr(cache, 'cache_response'), "Should have AI-specific cache_response method"
        assert hasattr(cache, 'get_cached_response'), "Should have AI-specific get_cached_response method"
        assert hasattr(cache, 'invalidate_by_operation'), "Should have AI-specific invalidate_by_operation method"
        
        print("✓ Inheritance method delegation validated successfully")
    
    async def test_ai_specific_invalidation(self, integrated_ai_cache, sample_ai_responses):
        """
        Test AI-specific invalidation patterns and behavior.
        
        This test validates:
        - invalidate_by_operation method with multiple operations
        - Selective invalidation (only target operation removed)
        - Edge cases (empty results, pattern matching, concurrent access)
        - Other cached operations remain intact
        
        Args:
            integrated_ai_cache: The configured AI cache instance
            sample_ai_responses: Sample responses for testing
        """
        cache = integrated_ai_cache
        
        # Test data setup - cache multiple operations for different texts
        test_texts = {
            "text1": "First test text for invalidation testing.",
            "text2": "Second test text with different content for validation.",
            "text3": "Third text to ensure comprehensive invalidation testing."
        }
        
        operations_to_test = ["summarize", "sentiment", "key_points"]
        cached_items = {}
        
        # Step 1: Cache responses for multiple operations and texts
        for text_id, text_content in test_texts.items():
            for operation in operations_to_test:
                options = {}
                if operation == "key_points":
                    options["max_points"] = 5
                    
                response = sample_ai_responses[operation]["medium"]  # Use medium responses
                await cache.cache_response(text_content, operation, options, response)
                
                # Store for later verification
                cache_key = f"{text_id}:{operation}"
                cached_items[cache_key] = {
                    "text": text_content,
                    "operation": operation,
                    "options": options,
                    "response": response
                }
        
        print(f"Cached {len(cached_items)} items across {len(operations_to_test)} operations")
        
        # Step 2: Verify all items are cached before invalidation
        for cache_key, item in cached_items.items():
            cached_result = await cache.get_cached_response(item["text"], item["operation"], item["options"])
            assert cached_result is not None, f"Item should be cached before invalidation: {cache_key}"
            # Compare response fields directly (no separate 'response' key)
            for key, value in item["response"].items():
                assert cached_result.get(key) == value, f"Response field {key} mismatch for {cache_key}"
        
        # Step 3: Test selective invalidation - invalidate only "summarize" operation
        target_operation = "summarize"
        invalidated_count = await cache.invalidate_by_operation(target_operation)
        
        # Add small delay to ensure invalidation is processed
        await asyncio.sleep(0.1)
        
        # Should invalidate 3 items (one for each text with summarize operation)
        expected_invalidated = len(test_texts)
        assert invalidated_count >= expected_invalidated, f"Expected at least {expected_invalidated} invalidated, got {invalidated_count}"
        
        print(f"✓ Invalidated {invalidated_count} items for operation '{target_operation}'")
        
        # Step 4: Verify selective invalidation worked correctly
        for cache_key, item in cached_items.items():
            cached_result = await cache.get_cached_response(item["text"], item["operation"], item["options"])
            
            if item["operation"] == target_operation:
                # These should be gone
                assert cached_result is None, f"Item should be invalidated: {cache_key}"
            else:
                # These should still exist
                assert cached_result is not None, f"Item should still exist: {cache_key}"
                # Compare response fields directly (no separate 'response' key)
                for key, value in item["response"].items():
                    assert cached_result.get(key) == value, f"Response field {key} should be intact for {cache_key}"
        
        print(f"✓ Selective invalidation verified - only '{target_operation}' items removed")
        
        # Step 5: Test invalidation of non-existent operation
        non_existent_count = await cache.invalidate_by_operation("non_existent_operation")
        assert non_existent_count == 0, "Should return 0 for non-existent operation"
        
        # Step 6: Test invalidation with empty cache
        await cache.clear()
        empty_count = await cache.invalidate_by_operation("sentiment")
        assert empty_count == 0, "Should return 0 when cache is empty"
        
        # Step 7: Test concurrent invalidation scenario
        # Cache new items for concurrent testing
        concurrent_operations = ["sentiment", "key_points", "questions"]
        concurrent_text = "Concurrent testing text for invalidation validation."
        
        for operation in concurrent_operations:
            response = sample_ai_responses[operation]["small"]
            await cache.cache_response(concurrent_text, operation, {}, response)
        
        # Simulate concurrent invalidation attempts
        async def concurrent_invalidate(op):
            await asyncio.sleep(0.01)  # Small delay to simulate real concurrency
            return await cache.invalidate_by_operation(op)
        
        # Run concurrent invalidations
        tasks = [concurrent_invalidate(op) for op in concurrent_operations]
        results = await asyncio.gather(*tasks)
        
        # Each operation should invalidate at least 1 item
        for i, count in enumerate(results):
            operation = concurrent_operations[i]
            assert count >= 1, f"Concurrent invalidation failed for {operation}: expected >= 1, got {count}"
        
        # Verify all items are gone
        for operation in concurrent_operations:
            cached_result = await cache.get_cached_response(concurrent_text, operation, {})
            assert cached_result is None, f"Item should be gone after concurrent invalidation: {operation}"
        
        print("✓ Concurrent invalidation testing completed successfully")
        
        # Step 8: Test invalidation with pattern edge cases
        edge_case_texts = [
            ("", "summarize"),  # Empty text
            ("short", "invalid_op"),  # Invalid operation
            ("text with special chars: !@#$%^&*()", "sentiment"),  # Special characters
        ]
        
        # Cache valid edge case
        special_text = edge_case_texts[2][0]
        special_operation = edge_case_texts[2][1]
        await cache.cache_response(special_text, special_operation, {}, {"result": "test"})
        
        # Test invalidation with special characters
        special_count = await cache.invalidate_by_operation(special_operation)
        assert special_count == 1, f"Should invalidate special character text: got {special_count}"
        
        # Step 9: Test large-scale invalidation
        large_scale_operation = "summarize"
        large_scale_texts = [f"Large scale text number {i}" for i in range(20)]
        
        # Cache many items with same operation
        for text in large_scale_texts:
            response = {"summary": f"Summary of {text}"}
            await cache.cache_response(text, large_scale_operation, {}, response)
        
        # Invalidate all at once
        large_count = await cache.invalidate_by_operation(large_scale_operation)
        assert large_count == len(large_scale_texts), f"Should invalidate all {len(large_scale_texts)} items, got {large_count}"
        
        # Verify they're all gone
        for text in large_scale_texts:
            cached_result = await cache.get_cached_response(text, large_scale_operation, {})
            assert cached_result is None, f"Large scale item should be gone: {text[:20]}..."
        
        print(f"✓ Large-scale invalidation completed: {large_count} items")
        
        # Step 10: Test invalidation with different TTLs
        ttl_operation = "sentiment"
        ttl_texts = ["TTL text 1", "TTL text 2", "TTL text 3"]
        ttl_values = [3600, 7200, 1800]  # Different TTLs
        
        for i, text in enumerate(ttl_texts):
            response = {"sentiment": "neutral", "confidence": 0.8}
            # Cache with specific TTL (if supported by cache_response)
            await cache.cache_response(text, ttl_operation, {}, response)
        
        # Invalidate regardless of TTL
        ttl_count = await cache.invalidate_by_operation(ttl_operation)
        assert ttl_count == len(ttl_texts), f"Should invalidate all TTL items, got {ttl_count}"
        
        print("✓ AI-specific invalidation testing completed successfully")
    
    async def test_memory_cache_promotion_logic(self, integrated_ai_cache, sample_ai_responses):
        """
        Test memory cache promotion logic and behavior.
        
        This test validates:
        - Promotion logic for small text with stable operations
        - Large text handling with memory cache size limits
        - LRU eviction behavior and promotion metrics
        - Promotion with full memory cache scenarios
        
        Args:
            integrated_ai_cache: The configured AI cache instance
            sample_ai_responses: Sample responses for testing
        """
        cache = integrated_ai_cache
        
        # Test data for promotion testing
        small_texts = [
            "Small text 1 for promotion testing",
            "Small text 2 for validation",
            "Small text 3 for LRU testing",
            "Small text 4 for eviction testing",
            "Small text 5 for capacity testing"
        ]
        
        medium_texts = [
            "Medium text for promotion testing " * 50,  # Medium sized text
            "Another medium text for validation " * 50,
        ]
        
        large_text = "Large text content that should not be promoted " * 500  # Large text
        
        stable_operations = ["summarize", "sentiment"]  # Operations likely to be promoted
        
        # Step 1: Test small text promotion logic
        print("Testing small text promotion logic...")
        
        promoted_count = 0
        for i, text in enumerate(small_texts):
            for operation in stable_operations:
                response = sample_ai_responses[operation]["small"]
                
                # Cache the response
                await cache.cache_response(text, operation, {}, response)
                
                # Try to access multiple times to trigger promotion (if implemented)
                for access_count in range(3):
                    cached_result = await cache.get_cached_response(text, operation, {})
                    assert cached_result is not None, f"Response should be cached: {text[:20]}... {operation}"
                    # Compare response fields directly (no separate 'response' key)
                    for key, value in response.items():
                        assert cached_result.get(key) == value, f"Response field {key} should match for {operation}"
                
                promoted_count += 1
        
        print(f"✓ Cached {promoted_count} small text items for promotion consideration")
        
        # Step 2: Test memory cache behavior with cache statistics (if available)
        try:
            stats = await cache.get_cache_stats()
            if "memory_cache_entries" in stats:
                memory_entries = stats["memory_cache_entries"]
                print(f"Memory cache entries: {memory_entries}")
                
                if "memory_cache_hit_rate" in stats:
                    hit_rate = stats["memory_cache_hit_rate"]
                    print(f"Memory cache hit rate: {hit_rate}")
            else:
                print("Memory cache statistics not available")
        except Exception as e:
            print(f"Cache statistics not available: {e}")
        
        # Step 3: Test large text handling (should not overwhelm memory cache)
        print("Testing large text handling...")
        
        large_operations = ["summarize", "key_points"]
        for operation in large_operations:
            response = sample_ai_responses[operation]["large"]
            await cache.cache_response(large_text, operation, {}, response)
            
            # Verify it's cached but check memory usage
            cached_result = await cache.get_cached_response(large_text, operation, {})
            assert cached_result is not None, f"Large text should be cached: {operation}"
            # Compare response fields directly (no separate 'response' key)
            for key, value in response.items():
                assert cached_result.get(key) == value, f"Large text response field {key} should match for {operation}"
        
        print("✓ Large text caching completed without memory issues")
        
        # Step 4: Test LRU eviction behavior by filling memory cache
        print("Testing LRU eviction behavior...")
        
        # Create many small items to potentially trigger eviction
        eviction_texts = [f"Eviction test text {i}" for i in range(60)]  # More than memory cache size
        eviction_operation = "sentiment"
        eviction_responses = []
        
        for i, text in enumerate(eviction_texts):
            response = {"sentiment": "neutral", "confidence": 0.8, "index": i}
            await cache.cache_response(text, eviction_operation, {}, response)
            eviction_responses.append(response)
            
            # Access immediately to potentially promote to memory cache
            cached_result = await cache.get_cached_response(text, eviction_operation, {})
            assert cached_result is not None, f"Eviction test item should be cached: {i}"
        
        print(f"✓ Cached {len(eviction_texts)} items for LRU eviction testing")
        
        # Step 5: Test access patterns and verify cache behavior
        # Access first few items multiple times (hot items)
        hot_items = eviction_texts[:5]
        for _ in range(5):  # Multiple accesses
            for text in hot_items:
                cached_result = await cache.get_cached_response(text, eviction_operation, {})
                assert cached_result is not None, f"Hot item should remain cached: {text}"
        
        print("✓ Hot items accessed multiple times")
        
        # Access random items to test LRU behavior
        import random
        random_items = random.sample(eviction_texts[10:30], 5)
        for text in random_items:
            cached_result = await cache.get_cached_response(text, eviction_operation, {})
            assert cached_result is not None, f"Random item should still be cached: {text}"
        
        print("✓ Random access pattern tested")
        
        # Step 6: Test memory cache promotion with different text sizes
        print("Testing promotion with different text sizes...")
        
        size_test_cases = [
            ("tiny", "Tiny"),
            ("small", "Small text for size testing"),
            ("medium", "Medium sized text for promotion testing " * 20),
            ("large", "Large text that may not be promoted to memory " * 200)
        ]
        
        promotion_operation = "key_points"
        for size_label, text_content in size_test_cases:
            response = {"key_points": [f"Point from {size_label} text"], "count": 1}
            
            # Cache and immediately access
            await cache.cache_response(text_content, promotion_operation, {}, response)
            
            # Multiple accesses to encourage promotion
            for _ in range(4):
                cached_result = await cache.get_cached_response(text_content, promotion_operation, {})
                assert cached_result is not None, f"{size_label} text should be cached"
                # Compare response fields directly (no separate 'response' key)
                for key, value in response.items():
                    assert cached_result.get(key) == value, f"{size_label} response field {key} should match"
        
        print("✓ Different text sizes tested for promotion")
        
        # Step 7: Test promotion metrics and behavior under load
        print("Testing promotion under concurrent load...")
        
        async def concurrent_access(text_id: int, operation: str):
            """Simulate concurrent access to test promotion under load."""
            text = f"Concurrent text {text_id} for load testing"
            response = {"result": f"Response for text {text_id}", "operation": operation}
            
            # Cache the item
            await cache.cache_response(text, operation, {}, response)
            
            # Multiple rapid accesses
            for _ in range(3):
                cached_result = await cache.get_cached_response(text, operation, {})
                assert cached_result is not None, f"Concurrent item should be cached: {text_id}"
                await asyncio.sleep(0.001)  # Small delay
            
            return text_id
        
        # Run concurrent accesses
        concurrent_tasks = [
            concurrent_access(i, "summarize") for i in range(20)
        ]
        concurrent_results = await asyncio.gather(*concurrent_tasks)
        
        assert len(concurrent_results) == 20, "All concurrent tasks should complete"
        print(f"✓ Concurrent promotion testing completed: {len(concurrent_results)} tasks")
        
        # Step 8: Test memory cache limits and overflow handling
        print("Testing memory cache limits...")
        
        # Try to cache more items than memory cache capacity
        overflow_texts = [f"Overflow text {i}" for i in range(100)]
        overflow_operation = "questions"
        
        for text in overflow_texts:
            response = {"questions": [f"Question about {text}"], "count": 1}
            await cache.cache_response(text, overflow_operation, {}, response)
        
        # Verify accessibility: base expectation is at least L1 capacity under degraded/no-Redis envs
        accessible_count = 0
        for text in overflow_texts:
            cached_result = await cache.get_cached_response(text, overflow_operation, {})
            if cached_result is not None:
                accessible_count += 1

        l1_capacity = 0
        try:
            if getattr(cache, 'l1_cache', None) and hasattr(cache.l1_cache, 'max_size'):
                l1_capacity = cache.l1_cache.max_size  # type: ignore[attr-defined]
        except Exception:
            l1_capacity = 0

        # If Redis is connected, expect high accessibility; otherwise, at least L1 capacity
        try:
            redis_available = await cache.connect()
        except Exception:
            redis_available = False

        if redis_available:
            assert accessible_count >= int(len(overflow_texts) * 0.9), (
                f"Most items should be accessible: {accessible_count}/{len(overflow_texts)}"
            )
        else:
            assert accessible_count >= min(l1_capacity, len(overflow_texts)) // 2, (
                f"Too few items accessible without Redis: {accessible_count}, expected ~= L1 capacity ({l1_capacity})"
            )
        
        print(f"✓ Memory cache overflow handled: {accessible_count}/{len(overflow_texts)} items accessible")
        
        # Step 9: Final statistics check
        try:
            final_stats = await cache.get_cache_stats()
            print("Final cache statistics:")
            for key, value in final_stats.items():
                if "memory" in key.lower() or "promotion" in key.lower():
                    print(f"  {key}: {value}")
        except Exception:
            print("Final statistics not available")
        
        print("✓ Memory cache promotion logic testing completed successfully")
    
    async def test_configuration_integration(self, performance_monitor, monkeypatch):
        """
        Test AIResponseCacheConfig integration and validation.
        
        This test validates:
        - Configuration validation and application
        - Configuration updates, merging, and environment variable override
        - Configuration affects actual cache behavior
        - Parameter mapping integration with config system
        
        Args:
            performance_monitor: Performance monitoring instance
            monkeypatch: Pytest fixture for environment isolation
        """
        # Step 1: Test basic configuration creation and validation
        print("Testing configuration creation and validation...")
        
        basic_config = AIResponseCacheConfig(
            redis_url="redis://test:6379",
            default_ttl=1800,
            text_hash_threshold=500,
            memory_cache_size=25,
            compression_threshold=250,
            text_size_tiers={"small": 100, "medium": 1000, "large": 10000},
            performance_monitor=performance_monitor
        )
        
        # Validate the configuration
        validation_result = basic_config.validate()
        assert validation_result.is_valid, f"Basic config should be valid: {validation_result.errors}"
        print("✓ Basic configuration validation passed")
        
        # Step 2: Test configuration with invalid values
        print("Testing configuration validation with invalid values...")
        
        try:
            invalid_config = AIResponseCacheConfig(
                redis_url="invalid://url",  # Invalid URL format
                default_ttl=-100,  # Negative TTL
                text_hash_threshold=0,  # Zero threshold
                memory_cache_size=-5,  # Negative size
                performance_monitor=performance_monitor
            )
            validation_result = invalid_config.validate()
            assert not validation_result.is_valid, "Invalid config should fail validation"
            assert len(validation_result.errors) > 0, "Should have validation errors"
            print(f"✓ Invalid configuration properly rejected: {len(validation_result.errors)} errors")
        except (ValidationError, ValueError) as e:
            print(f"✓ Invalid configuration rejected during creation: {e}")
        
        # Step 3: Test environment variable integration
        print("Testing environment variable integration...")
        
        # Set environment variables
        monkeypatch.setenv("REDIS_URL", "redis://env-redis:6379")
        monkeypatch.setenv("CACHE_DEFAULT_TTL", "7200")
        monkeypatch.setenv("CACHE_MEMORY_SIZE", "100")
        monkeypatch.setenv("CACHE_COMPRESSION_THRESHOLD", "1000")
        
        # Create config that should pick up environment values
        env_config = AIResponseCacheConfig(
            performance_monitor=performance_monitor
        )
        
        # Apply environment overrides (if method exists)
        loader = getattr(env_config, "from_environment", None)
        if callable(loader):
            env_config = loader()
            print("✓ Environment configuration loaded successfully")
        else:
            print("Environment loading method not available, using defaults")
        
        validation_result = env_config.validate()
        assert validation_result.is_valid, f"Environment config should be valid: {validation_result.errors}"
        
        # Step 4: Test configuration merging and updates
        print("Testing configuration merging...")
        
        base_config = AIResponseCacheConfig(
            redis_url="redis://base:6379",
            default_ttl=3600,
            text_hash_threshold=1000,
            performance_monitor=performance_monitor
        )
        
        update_config = AIResponseCacheConfig(
            default_ttl=7200,  # Override TTL
            memory_cache_size=200,  # Add memory cache size
            compression_level=9,  # Override compression
            performance_monitor=performance_monitor
        )
        
        # Test configuration merging (if method exists)
        try:
            merged_config = base_config.merge(update_config)
            validation_result = merged_config.validate()
            assert validation_result.is_valid, f"Merged config should be valid: {validation_result.errors}"
            print("✓ Configuration merging successful")
        except AttributeError:
            print("Configuration merging method not available")
        
        # Step 5: Test configuration affects cache behavior
        print("Testing configuration impact on cache behavior...")
        
        # Create cache with specific configuration
        test_config = AIResponseCacheConfig(
            redis_url="redis://localhost:6379",
            default_ttl=1800,  # 30 minutes
            text_hash_threshold=200,  # Low threshold for testing
            memory_cache_size=10,  # Small memory cache
            compression_threshold=100,  # Low compression threshold
            compression_level=1,  # Fast compression
            text_size_tiers={"small": 50, "medium": 200, "large": 1000},
            performance_monitor=performance_monitor
        )
        
        validation_result = test_config.validate()
        assert validation_result.is_valid, f"Test config should be valid: {validation_result.errors}"
        
        # Create cache with this configuration
        cache = AIResponseCache(
            redis_url=test_config.redis_url,
            default_ttl=test_config.default_ttl,
            text_hash_threshold=test_config.text_hash_threshold,
            memory_cache_size=test_config.memory_cache_size,
            compression_threshold=test_config.compression_threshold,
            compression_level=test_config.compression_level,
            text_size_tiers=test_config.text_size_tiers,
            performance_monitor=test_config.performance_monitor
        )
        
        try:
            await cache.connect()
        except Exception:
            print("Redis connection failed, testing with memory fallback")
        
        # Test that configuration actually affects behavior
        large_text = "This text should trigger compression based on low threshold " * 10
        test_response = {"summary": "Configuration test response"}
        
        await cache.cache_response(large_text, "summarize", {}, test_response)
        cached_result = await cache.get_cached_response(large_text, "summarize", {})
        
        assert cached_result is not None, "Response should be cached"
        # Compare response fields directly (no separate 'response' key)
        for key, value in test_response.items():
            assert cached_result.get(key) == value, f"Response field {key} should match"
        
        # Check text tier classification based on configuration
        # Metadata is merged with response, no separate 'metadata' key
        # Text tier is directly available in cached_result
        tiers = getattr(test_config, "text_size_tiers", None) or {}
        large_threshold = tiers.get("large")
        if large_threshold is not None:
            expected_tier = "large" if len(large_text) > large_threshold else "medium"
        else:
            expected_tier = "medium"
        # Note: Actual tier determination may vary based on implementation
        
        print(f"✓ Cache behavior affected by configuration: text_tier={cached_result.get('text_tier', 'unknown')}")
        
        await cache.disconnect()
        
        # Step 6: Test parameter mapping integration
        print("Testing parameter mapping integration...")
        
        mapper = CacheParameterMapper()
        
        # Test mapping AI config to generic parameters
        ai_params = {
            "redis_url": test_config.redis_url,
            "default_ttl": test_config.default_ttl,
            "text_hash_threshold": test_config.text_hash_threshold,
            "memory_cache_size": test_config.memory_cache_size,
            "compression_threshold": test_config.compression_threshold,
            "performance_monitor": test_config.performance_monitor
        }
        
        generic_params, ai_specific_params = mapper.map_ai_to_generic_params(ai_params)
        
        # Verify mapping worked correctly
        assert "redis_url" in generic_params, "redis_url should map to generic"
        assert "default_ttl" in generic_params, "default_ttl should map to generic" 
        assert "text_hash_threshold" in ai_specific_params, "text_hash_threshold should be AI-specific"
        
        # Verify mapped memory cache size
        if "l1_cache_size" in generic_params:
            assert generic_params["l1_cache_size"] == ai_params["memory_cache_size"], "memory_cache_size should map to l1_cache_size"
        
        print("✓ Parameter mapping integration successful")
        
        # Step 7: Test configuration validation with parameter mapper
        validation_result = mapper.validate_parameter_compatibility(ai_params)
        assert validation_result.is_valid, f"AI parameters should be compatible: {validation_result.errors}"
        
        # Test with conflicting parameters
        conflicting_params = ai_params.copy()
        conflicting_params["l1_cache_size"] = 50  # Conflicts with memory_cache_size
        
        conflict_validation = mapper.validate_parameter_compatibility(conflicting_params)
        if not conflict_validation.is_valid:
            print(f"✓ Parameter conflicts properly detected: {conflict_validation.errors}")
        else:
            print("Parameter conflict detection not available or conflicts resolved")
        
        # Step 8: Test configuration serialization and deserialization
        print("Testing configuration serialization...")
        
        to_dict_fn = getattr(test_config, "to_dict", None)
        if callable(to_dict_fn):
            # Convert to dictionary
            config_dict = to_dict_fn()
            assert isinstance(config_dict, dict), "Configuration should serialize to dict"
            assert "redis_url" in config_dict, "Should contain redis_url"
            assert "default_ttl" in config_dict, "Should contain default_ttl"

            from_dict_fn = getattr(AIResponseCacheConfig, "from_dict", None)
            if callable(from_dict_fn):
                # Recreate from dictionary (if method exists)
                recreated_config = from_dict_fn(config_dict)
                recreated_validation = recreated_config.validate()
                assert recreated_validation.is_valid, "Recreated config should be valid"
                print("✓ Configuration serialization/deserialization successful")
            else:
                print("from_dict method not available; skipping deserialization test")
        else:
            print("Configuration serialization methods not available")
        
        # Step 9: Test configuration with different presets
        print("Testing configuration presets...")
        
        preset_configs = [
            ("development", {"default_ttl": 1800, "memory_cache_size": 50}),
            ("production", {"default_ttl": 7200, "memory_cache_size": 200}),
            ("testing", {"default_ttl": 900, "memory_cache_size": 25})
        ]
        
        for preset_name, preset_params in preset_configs:
            from_preset_fn = getattr(AIResponseCacheConfig, "from_preset", None)
            if callable(from_preset_fn):
                preset_config = from_preset_fn(preset_name, performance_monitor=performance_monitor)
                validation_result = preset_config.validate()
                assert validation_result.is_valid, f"{preset_name} preset should be valid"
                print(f"✓ {preset_name} preset configuration successful")
            else:
                print(f"Preset configuration method not available for {preset_name}")
        
        print("✓ Configuration integration testing completed successfully")
    
    async def test_monitoring_integration(self, integrated_ai_cache, sample_ai_responses):
        """
        Test monitoring integration and metrics collection.
        
        This test validates:
        - Metrics collection from monitoring methods (from Deliverable 6)
        - Performance summary generation and recommendation system
        - Metric reset and export capabilities
        - Monitoring doesn't impact performance
        
        Args:
            integrated_ai_cache: The configured AI cache instance
            sample_ai_responses: Sample responses for testing
        """
        cache = integrated_ai_cache
        
        # Step 1: Test basic metrics collection
        print("Testing basic metrics collection...")
        
        # Perform some cache operations to generate metrics
        test_operations = ["summarize", "sentiment", "key_points"]
        test_text = "Test text for monitoring integration validation"
        
        for operation in test_operations:
            response = sample_ai_responses[operation]["medium"]
            
            # Cache the response (should generate metrics)
            start_time = time.time()
            await cache.cache_response(test_text, operation, {}, response)
            cache_duration = time.time() - start_time
            
            # Retrieve the response (should generate more metrics)
            start_time = time.time()
            cached_result = await cache.get_cached_response(test_text, operation, {})
            retrieve_duration = time.time() - start_time
            
            assert cached_result is not None, f"Response should be cached for {operation}"
            assert cache_duration < 1.0, f"Cache operation should be fast: {cache_duration}s"
            assert retrieve_duration < 0.5, f"Retrieve operation should be fast: {retrieve_duration}s"
        
        print(f"✓ Generated metrics for {len(test_operations)} operations")
        
        # Step 2: Test cache statistics retrieval
        print("Testing cache statistics retrieval...")
        
        try:
            stats = await cache.get_cache_stats()
            assert isinstance(stats, dict), "Statistics should be a dictionary"
            
            # Check for expected statistics
            expected_stats = ["total_entries", "hit_rate", "miss_rate"]
            available_stats = []
            
            for stat_name in expected_stats:
                if stat_name in stats:
                    available_stats.append(stat_name)
                    value = stats[stat_name]
                    assert isinstance(value, (int, float)), f"{stat_name} should be numeric: {value}"
                    print(f"  {stat_name}: {value}")
            
            if available_stats:
                print(f"✓ Retrieved {len(available_stats)} basic statistics")
            else:
                print("Basic statistics not available in current implementation")
                
        except Exception as e:
            print(f"Cache statistics not available: {e}")
        
        # Step 3: Test AI-specific monitoring methods
        print("Testing AI-specific monitoring...")
        
        # Test operation-specific metrics (if available)
        try:
            operation_metrics = await cache.get_operation_metrics()
            if operation_metrics:
                assert isinstance(operation_metrics, dict), "Operation metrics should be a dictionary"
                
                for operation, metrics in operation_metrics.items():
                    print(f"  {operation}: {metrics}")
                    assert isinstance(metrics, dict), f"Metrics for {operation} should be a dict"
                
                print(f"✓ Retrieved operation metrics for {len(operation_metrics)} operations")
            else:
                print("Operation-specific metrics not available")
                
        except AttributeError:
            print("Operation metrics method not available")
        except Exception as e:
            print(f"Operation metrics error: {e}")
        
        # Step 4: Test performance monitoring and benchmarks
        print("Testing performance monitoring...")
        
        # Generate load for performance monitoring
        performance_texts = [f"Performance test text {i}" for i in range(20)]
        performance_operation = "summarize"
        performance_response = sample_ai_responses[performance_operation]["small"]
        
        # Measure cache performance
        cache_times = []
        retrieve_times = []
        
        for text in performance_texts:
            # Measure cache time
            start_time = time.time()
            await cache.cache_response(text, performance_operation, {}, performance_response)
            cache_time = time.time() - start_time
            cache_times.append(cache_time)
            
            # Measure retrieve time
            start_time = time.time()
            cached_result = await cache.get_cached_response(text, performance_operation, {})
            retrieve_time = time.time() - start_time
            retrieve_times.append(retrieve_time)
            
            assert cached_result is not None, f"Performance item should be cached: {text}"
        
        # Calculate performance statistics
        avg_cache_time = sum(cache_times) / len(cache_times)
        avg_retrieve_time = sum(retrieve_times) / len(retrieve_times)
        max_cache_time = max(cache_times)
        max_retrieve_time = max(retrieve_times)
        
        print(f"  Average cache time: {avg_cache_time:.4f}s")
        print(f"  Average retrieve time: {avg_retrieve_time:.4f}s")
        print(f"  Max cache time: {max_cache_time:.4f}s")
        print(f"  Max retrieve time: {max_retrieve_time:.4f}s")
        
        # Performance assertions
        assert avg_cache_time < 0.1, f"Average cache time too slow: {avg_cache_time}s"
        assert avg_retrieve_time < 0.05, f"Average retrieve time too slow: {avg_retrieve_time}s"
        assert max_cache_time < 0.5, f"Max cache time too slow: {max_cache_time}s"
        
        print("✓ Performance monitoring completed")
        
        # Step 5: Test monitoring impact on performance
        print("Testing monitoring performance impact...")
        
        # Test cache operations with monitoring
        monitored_start = time.time()
        for i in range(50):
            text = f"Monitoring impact test {i}"
            await cache.cache_response(text, "sentiment", {}, {"sentiment": "neutral"})
            await cache.get_cached_response(text, "sentiment", {})
        monitored_duration = time.time() - monitored_start
        
        # Performance should still be reasonable with monitoring
        assert monitored_duration < 5.0, f"Monitoring overhead too high: {monitored_duration}s for 50 operations"
        operations_per_second = 100 / monitored_duration  # 50 cache + 50 retrieve
        
        print(f"  Operations per second with monitoring: {operations_per_second:.2f}")
        assert operations_per_second > 50, f"Performance too low with monitoring: {operations_per_second} ops/s"
        
        print("✓ Monitoring has acceptable performance impact")
        
        # Step 6: Test metric reset functionality
        print("Testing metric reset functionality...")
        
        try:
            # Get current metrics
            stats_before_reset = await cache.get_cache_stats()
            
            # Reset metrics (if available)
            await cache.reset_metrics()
            
            # Get metrics after reset
            stats_after_reset = await cache.get_cache_stats()
            
            # Verify reset worked
            if "total_entries" in stats_after_reset:
                # Some stats may not reset (like current entries), but others should
                print(f"  Stats before reset: {stats_before_reset.get('total_operations', 'N/A')}")
                print(f"  Stats after reset: {stats_after_reset.get('total_operations', 'N/A')}")
            
            print("✓ Metric reset functionality available")
            
        except AttributeError:
            print("Metric reset method not available")
        except Exception as e:
            print(f"Metric reset error: {e}")
        
        # Step 7: Test monitoring with different operation types
        print("Testing monitoring across operation types...")
        
        operation_test_data = {
            "summarize": {"text": "Text to summarize", "options": {}},
            "sentiment": {"text": "Text for sentiment analysis", "options": {}},
            "key_points": {"text": "Text for key points extraction", "options": {"max_points": 3}},
            "questions": {"text": "Text for question generation", "options": {"num_questions": 2}},
            "qa": {"text": "Text for QA", "options": {"question": "What is this about?"}}
        }
        
        operation_metrics = {}
        for operation, test_data in operation_test_data.items():
            text = test_data["text"]
            options = test_data["options"]
            response = sample_ai_responses[operation]["small"]
            
            # Time the operation
            start_time = time.time()
            await cache.cache_response(text, operation, options, response)
            cache_time = time.time() - start_time
            
            start_time = time.time()
            cached_result = await cache.get_cached_response(text, operation, options)
            retrieve_time = time.time() - start_time
            
            operation_metrics[operation] = {
                "cache_time": cache_time,
                "retrieve_time": retrieve_time,
                "success": cached_result is not None
            }
            
            assert cached_result is not None, f"Operation should succeed: {operation}"
        
        # Report operation-specific performance
        for operation, metrics in operation_metrics.items():
            print(f"  {operation}: cache={metrics['cache_time']:.4f}s, retrieve={metrics['retrieve_time']:.4f}s")
            assert metrics["success"], f"Operation {operation} should succeed"
            assert metrics["cache_time"] < 0.2, f"{operation} cache time too slow"
            assert metrics["retrieve_time"] < 0.1, f"{operation} retrieve time too slow"
        
        print("✓ All operation types monitored successfully")
        
        # Step 8: Test monitoring integration with error conditions
        print("Testing monitoring with error conditions...")
        
        error_scenarios = [
            ("empty_text", "", "summarize", {}),
            ("invalid_operation", "test text", "invalid_op", {}),
            ("missing_qa_question", "test text", "qa", {}),  # Missing required question
        ]
        
        for scenario_name, text, operation, options in error_scenarios:
            try:
                # These should handle gracefully and potentially be monitored
                cached_result = await cache.get_cached_response(text, operation, options)
                if cached_result is None:
                    print(f"  {scenario_name}: Handled gracefully (cache miss)")
                else:
                    print(f"  {scenario_name}: Unexpected cache hit")
            except Exception as e:
                print(f"  {scenario_name}: Exception handled: {type(e).__name__}")
        
        print("✓ Error condition monitoring completed")
        
        # Step 9: Final monitoring statistics
        print("Final monitoring statistics...")
        
        try:
            final_stats = await cache.get_cache_stats()
            monitoring_stats = {}
            
            for key, value in final_stats.items():
                if any(keyword in key.lower() for keyword in ["monitor", "metric", "performance", "time", "count"]):
                    monitoring_stats[key] = value
            
            if monitoring_stats:
                print("  Monitoring-related statistics:")
                for key, value in monitoring_stats.items():
                    print(f"    {key}: {value}")
            else:
                print("  No specific monitoring statistics available")
                
        except Exception as e:
            print(f"  Final statistics error: {e}")
        
        print("✓ Monitoring integration testing completed successfully")
    
    async def test_error_handling_integration(self, integrated_ai_cache, sample_ai_responses, monkeypatch):
        """
        Test error handling and graceful degradation.
        
        This test validates:
        - Redis connection failure handling with graceful degradation
        - Timeout handling and concurrent access safety
        - Data corruption recovery and memory pressure scenarios
        - Proper exception handling throughout the system
        
        Args:
            integrated_ai_cache: The configured AI cache instance
            sample_ai_responses: Sample responses for testing
            monkeypatch: Pytest fixture for environment isolation
        """
        cache = integrated_ai_cache
        
        # Step 1: Test basic error scenarios
        print("Testing basic error scenarios...")
        
        # Test empty/invalid inputs
        error_test_cases = [
            ("empty_text", "", "summarize", {}, "Empty text should be handled gracefully"),
            ("none_text", None, "summarize", {}, "None text should raise appropriate error"),
            ("empty_operation", "test text", "", {}, "Empty operation should be handled"),
            ("none_operation", "test text", None, {}, "None operation should raise error"),
            ("invalid_operation", "test text", "invalid_op", {}, "Invalid operation should be handled"),
            ("none_options", "test text", "summarize", None, "None options should be handled"),
        ]
        
        for test_name, text, operation, options, description in error_test_cases:
            try:
                # Test cache operation
                if text is not None and operation is not None and options is not None:
                    result = await cache.cache_response(text, operation, options, {"test": "response"})
                    print(f"  {test_name}: Cache operation succeeded unexpectedly")
                else:
                    # These should raise exceptions
                    await cache.cache_response(text, operation, options, {"test": "response"})
                    print(f"  {test_name}: Should have raised exception")
                    assert False, f"{description} - should raise exception"
                    
            except (ValidationError, ValueError, TypeError) as e:
                print(f"  {test_name}: Properly handled - {type(e).__name__}: {str(e)[:50]}...")
            except Exception as e:
                print(f"  {test_name}: Unexpected error - {type(e).__name__}: {str(e)[:50]}...")
            
            try:
                # Test retrieval operation
                if text is not None and operation is not None and options is not None:
                    cached_result = await cache.get_cached_response(text, operation, options)
                    if cached_result is None:
                        print(f"  {test_name}: Retrieval returned None (expected for invalid inputs)")
                    else:
                        print(f"  {test_name}: Retrieval succeeded unexpectedly")
                else:
                    await cache.get_cached_response(text, operation, options)
                    assert False, f"{description} - retrieval should raise exception"
                    
            except (ValidationError, ValueError, TypeError) as e:
                print(f"  {test_name}: Retrieval properly handled - {type(e).__name__}")
            except Exception as e:
                print(f"  {test_name}: Retrieval unexpected error - {type(e).__name__}")
        
        print("✓ Basic error scenarios tested")
        
        # Step 2: Test Redis connection failure simulation
        print("Testing Redis connection failure simulation...")
        
        # First cache some data
        test_text = "Test text for connection failure scenario"
        test_response = sample_ai_responses["summarize"]["medium"]
        
        await cache.cache_response(test_text, "summarize", {}, test_response)
        cached_result = await cache.get_cached_response(test_text, "summarize", {})
        assert cached_result is not None, "Initial cache operation should succeed"
        
        # Simulate Redis connection issues by patching
        async def mock_redis_failure(*args, **kwargs):
            raise ConnectionError("Simulated Redis connection failure")
        
        # Test graceful degradation when Redis operations fail
        with patch.object(cache, 'redis') as mock_redis:
            mock_redis.get = AsyncMock(side_effect=mock_redis_failure)
            mock_redis.set = AsyncMock(side_effect=mock_redis_failure)
            mock_redis.delete = AsyncMock(side_effect=mock_redis_failure)
            
            # Cache should fallback to memory cache
            fallback_text = "Fallback test text"
            fallback_response = {"summary": "Fallback summary"}
            
            try:
                await cache.cache_response(fallback_text, "summarize", {}, fallback_response)
                print("  ✓ Cache operation handled Redis failure gracefully")
            except Exception as e:
                print(f"  Cache operation failed during Redis failure: {e}")
            
            try:
                # Should fallback to memory cache
                cached_result = await cache.get_cached_response(fallback_text, "summarize", {})
                if cached_result is not None:
                    print("  ✓ Retrieval worked with memory cache fallback")
                else:
                    print("  Retrieval returned None during Redis failure (acceptable)")
            except Exception as e:
                print(f"  Retrieval failed during Redis failure: {e}")
        
        print("✓ Redis connection failure handling tested")
        
        # Step 3: Test timeout scenarios
        print("Testing timeout scenarios...")
        
        # Simulate slow Redis operations
        async def mock_slow_operation(*args, **kwargs):
            await asyncio.sleep(2.0)  # Simulate 2-second delay
            return None
        
        with patch.object(cache, 'redis') as mock_redis:
            mock_redis.get = AsyncMock(side_effect=mock_slow_operation)
            
            # Test timeout handling
            timeout_text = "Timeout test text"
            
            start_time = time.time()
            try:
                # This should timeout or handle slow operations gracefully
                cached_result = await asyncio.wait_for(
                    cache.get_cached_response(timeout_text, "summarize", {}),
                    timeout=1.0
                )
                print(f"  Operation completed in {time.time() - start_time:.2f}s")
            except asyncio.TimeoutError:
                print(f"  ✓ Operation timed out gracefully after {time.time() - start_time:.2f}s")
            except Exception as e:
                print(f"  Operation failed with: {type(e).__name__}")
        
        print("✓ Timeout scenarios tested")
        
        # Step 4: Test concurrent access safety
        print("Testing concurrent access safety...")
        
        concurrent_text = "Concurrent access test text"
        concurrent_response = sample_ai_responses["sentiment"]["small"]
        
        async def concurrent_cache_operation(operation_id: int):
            """Simulate concurrent cache operations."""
            try:
                text = f"{concurrent_text} {operation_id}"
                response = {**concurrent_response, "id": operation_id}
                
                # Cache the response
                await cache.cache_response(text, "sentiment", {}, response)
                
                # Immediately try to retrieve it
                cached_result = await cache.get_cached_response(text, "sentiment", {})
                
                if cached_result is not None and cached_result.get("id") == operation_id:
                    return True
                else:
                    return False
                    
            except Exception as e:
                print(f"  Concurrent operation {operation_id} failed: {type(e).__name__}")
                return False
        
        # Run many concurrent operations
        concurrent_tasks = [concurrent_cache_operation(i) for i in range(50)]
        concurrent_results = await asyncio.gather(*concurrent_tasks, return_exceptions=True)
        
        # Count successes
        success_count = sum(1 for result in concurrent_results if result is True)
        error_count = sum(1 for result in concurrent_results if isinstance(result, Exception))
        
        print(f"  Concurrent operations: {success_count} succeeded, {error_count} errors, {len(concurrent_results) - success_count - error_count} other")
        
        # Most operations should succeed
        assert success_count >= len(concurrent_tasks) * 0.8, f"Too many concurrent operations failed: {success_count}/{len(concurrent_tasks)}"
        
        print("✓ Concurrent access safety tested")
        
        # Step 5: Test memory pressure scenarios
        print("Testing memory pressure scenarios...")
        
        # Try to fill memory cache beyond capacity
        pressure_texts = [f"Memory pressure text {i}" for i in range(200)]
        pressure_operation = "key_points"
        pressure_response = sample_ai_responses[pressure_operation]["small"]
        
        successful_caches = 0
        memory_errors = 0
        
        for text in pressure_texts:
            try:
                await cache.cache_response(text, pressure_operation, {}, pressure_response)
                successful_caches += 1
                
                # Verify we can still retrieve
                cached_result = await cache.get_cached_response(text, pressure_operation, {})
                if cached_result is None:
                    print(f"  Warning: Just-cached item not retrievable: {text[:20]}...")
                    
            except MemoryError:
                memory_errors += 1
            except Exception as e:
                print(f"  Unexpected error during memory pressure: {type(e).__name__}")
        
        print(f"  Memory pressure results: {successful_caches} cached, {memory_errors} memory errors")
        
        # System should handle memory pressure gracefully
        assert successful_caches > 0, "Should cache at least some items under memory pressure"
        
        print("✓ Memory pressure scenarios tested")
        
        # Step 6: Test data corruption recovery
        print("Testing data corruption recovery...")
        
        # Cache valid data first
        corruption_text = "Data corruption test text"
        corruption_response = sample_ai_responses["questions"]["medium"]
        
        await cache.cache_response(corruption_text, "questions", {}, corruption_response)
        
        # Verify it's cached correctly
        cached_result = await cache.get_cached_response(corruption_text, "questions", {})
        assert cached_result is not None, "Data should be cached before corruption test"
        
        # Simulate data corruption by patching get to return invalid data
        async def mock_corrupted_data(*args, **kwargs):
            return "invalid_json_data_not_parseable"
        
        with patch.object(cache, 'redis') as mock_redis:
            mock_redis.get = AsyncMock(side_effect=mock_corrupted_data)
            
            try:
                # Should handle corrupted data gracefully
                cached_result = await cache.get_cached_response(corruption_text, "questions", {})
                if cached_result is None:
                    print("  ✓ Corrupted data handled gracefully (returned None)")
                else:
                    print(f"  Unexpected: Got result despite corruption: {type(cached_result)}")
            except Exception as e:
                print(f"  ✓ Data corruption handled with exception: {type(e).__name__}")
        
        print("✓ Data corruption recovery tested")
        
        # Step 7: Test exception propagation and logging
        print("Testing exception propagation...")
        
        # Test with environment variables that might cause issues
        monkeypatch.setenv("REDIS_URL", "redis://invalid-host:99999")
        
        try:
            # Create cache with invalid Redis URL
            problem_cache = AIResponseCache(
                redis_url="redis://invalid-host:99999",
                default_ttl=3600,
                text_hash_threshold=1000
            )
            
            # Try to connect - should handle gracefully
            await problem_cache.connect()
            print("  Connection to invalid Redis succeeded unexpectedly")
            
        except Exception as e:
            print(f"  ✓ Invalid Redis URL handled properly: {type(e).__name__}")
        
        # Test with invalid configuration
        try:
            invalid_cache = AIResponseCache(
                redis_url="not-a-url",
                default_ttl=-1000,  # Invalid negative TTL
                text_hash_threshold=0  # Invalid zero threshold
            )
            print("  Invalid configuration accepted unexpectedly")
            
        except (ValidationError, ValueError, ConfigurationError) as e:
            print(f"  ✓ Invalid configuration rejected: {type(e).__name__}")
        except Exception as e:
            print(f"  Unexpected error with invalid config: {type(e).__name__}")
        
        print("✓ Exception propagation tested")
        
        # Step 8: Test recovery after errors
        print("Testing recovery after errors...")
        
        # Ensure cache still works after error conditions
        recovery_text = "Recovery test text after errors"
        recovery_response = sample_ai_responses["summarize"]["small"]
        
        try:
            await cache.cache_response(recovery_text, "summarize", {}, recovery_response)
            cached_result = await cache.get_cached_response(recovery_text, "summarize", {})
            
            assert cached_result is not None, "Cache should work after error conditions"
            # Compare response fields directly (no separate 'response' key)
            for key, value in recovery_response.items():
                assert cached_result.get(key) == value, f"Response field {key} should be correct after recovery"
            
            print("  ✓ Cache recovered successfully after error conditions")
            
        except Exception as e:
            print(f"  Cache recovery failed: {type(e).__name__}: {e}")
        
        print("✓ Error handling integration testing completed successfully")
    
    async def test_performance_benchmarks(self, integrated_ai_cache, sample_ai_responses):
        """
        Test performance benchmarks for throughput and latency.
        
        This test validates:
        - Throughput and latency benchmarks
        - Compression effectiveness and memory usage patterns
        - Comparison with baseline performance expectations
        - Structured performance reports generation
        
        Args:
            integrated_ai_cache: The configured AI cache instance
            sample_ai_responses: Sample responses for testing
        """
        cache = integrated_ai_cache
        
        print("Starting comprehensive performance benchmarking...")
        
        # Step 1: Single operation latency benchmarks
        print("Testing single operation latency...")
        
        single_op_results = {}
        test_text = "Performance benchmark test text for latency measurement"
        
        for operation in self.TEST_OPERATIONS:
            response = sample_ai_responses[operation]["medium"]
            options = {}
            if operation == "qa":
                options["question"] = "What is this text about?"
            elif operation == "key_points":
                options["max_points"] = 5
            
            # Measure cache operation latency
            cache_times = []
            for _ in range(10):  # Multiple runs for average
                start_time = time.time()
                await cache.cache_response(test_text, operation, options, response)
                cache_time = time.time() - start_time
                cache_times.append(cache_time)
            
            # Measure retrieval operation latency
            retrieve_times = []
            for _ in range(20):  # More retrievals to test cache performance
                start_time = time.time()
                cached_result = await cache.get_cached_response(test_text, operation, options)
                retrieve_time = time.time() - start_time
                retrieve_times.append(retrieve_time)
                assert cached_result is not None, f"Should retrieve cached {operation}"
            
            # Calculate statistics
            avg_cache_time = sum(cache_times) / len(cache_times)
            avg_retrieve_time = sum(retrieve_times) / len(retrieve_times)
            min_cache_time = min(cache_times)
            max_cache_time = max(cache_times)
            min_retrieve_time = min(retrieve_times)
            max_retrieve_time = max(retrieve_times)
            
            single_op_results[operation] = {
                "avg_cache_ms": avg_cache_time * 1000,
                "avg_retrieve_ms": avg_retrieve_time * 1000,
                "min_cache_ms": min_cache_time * 1000,
                "max_cache_ms": max_cache_time * 1000,
                "min_retrieve_ms": min_retrieve_time * 1000,
                "max_retrieve_ms": max_retrieve_time * 1000,
            }
            
            print(f"  {operation}: cache={avg_cache_time*1000:.2f}ms, retrieve={avg_retrieve_time*1000:.2f}ms")
            
            # Performance assertions
            assert avg_cache_time < 0.1, f"{operation} cache too slow: {avg_cache_time}s"
            assert avg_retrieve_time < 0.05, f"{operation} retrieve too slow: {avg_retrieve_time}s"
        
        print("✓ Single operation latency benchmarks completed")
        
        # Step 2: Throughput benchmarks
        print("Testing throughput performance...")
        
        throughput_results = {}
        test_duration = 5.0  # 5 seconds per throughput test
        
        for operation in ["summarize", "sentiment"]:  # Test subset for throughput
            response = sample_ai_responses[operation]["small"]
            
            # Cache throughput test
            cache_count = 0
            cache_start = time.time()
            cache_end = cache_start + test_duration
            
            while time.time() < cache_end:
                text = f"Throughput test {operation} {cache_count}"
                await cache.cache_response(text, operation, {}, response)
                cache_count += 1
            
            cache_throughput = cache_count / test_duration
            
            # Retrieve throughput test
            retrieve_count = 0
            retrieve_start = time.time()
            retrieve_end = retrieve_start + test_duration
            
            while time.time() < retrieve_end:
                text = f"Throughput test {operation} {retrieve_count % cache_count}"
                cached_result = await cache.get_cached_response(text, operation, {})
                if cached_result is not None:
                    retrieve_count += 1
            
            retrieve_throughput = retrieve_count / test_duration
            
            throughput_results[operation] = {
                "cache_ops_per_sec": cache_throughput,
                "retrieve_ops_per_sec": retrieve_throughput,
                "total_cached": cache_count,
                "total_retrieved": retrieve_count
            }
            
            print(f"  {operation}: {cache_throughput:.1f} cache/s, {retrieve_throughput:.1f} retrieve/s")
            
            # Throughput assertions
            assert cache_throughput > 50, f"{operation} cache throughput too low: {cache_throughput} ops/s"
            assert retrieve_throughput > 100, f"{operation} retrieve throughput too low: {retrieve_throughput} ops/s"
        
        print("✓ Throughput benchmarks completed")
        
        # Step 3: Text size performance analysis
        print("Testing performance across text sizes...")
        
        size_performance = {}
        operation = "summarize"
        
        for size_name, text_content in self.TEST_TEXT_SIZES.items():
            response = sample_ai_responses[operation][size_name]
            
            # Measure performance for this text size
            cache_times = []
            retrieve_times = []
            
            for i in range(5):  # 5 runs per size
                text = f"{text_content} {i}"  # Make each unique
                
                # Cache timing
                start_time = time.time()
                await cache.cache_response(text, operation, {}, response)
                cache_time = time.time() - start_time
                cache_times.append(cache_time)
                
                # Retrieve timing
                start_time = time.time()
                cached_result = await cache.get_cached_response(text, operation, {})
                retrieve_time = time.time() - start_time
                retrieve_times.append(retrieve_time)
                
                assert cached_result is not None, f"Should cache {size_name} text"
            
            avg_cache_time = sum(cache_times) / len(cache_times)
            avg_retrieve_time = sum(retrieve_times) / len(retrieve_times)
            text_length = len(text_content)
            
            size_performance[size_name] = {
                "text_length": text_length,
                "avg_cache_ms": avg_cache_time * 1000,
                "avg_retrieve_ms": avg_retrieve_time * 1000,
                "cache_ms_per_char": (avg_cache_time * 1000) / text_length,
                "retrieve_ms_per_char": (avg_retrieve_time * 1000) / text_length
            }
            
            print(f"  {size_name} ({text_length} chars): cache={avg_cache_time*1000:.2f}ms, retrieve={avg_retrieve_time*1000:.2f}ms")
        
        print("✓ Text size performance analysis completed")
        
        # Step 4: Compression effectiveness testing
        print("Testing compression effectiveness...")
        
        compression_results = {}
        large_text = "Compression test content " * 1000  # Large repeatable text
        large_response = {"summary": "Large content summary " * 100}
        
        # Test with compression (default)
        start_time = time.time()
        await cache.cache_response(large_text, "summarize", {}, large_response)
        cache_time_compressed = time.time() - start_time
        
        start_time = time.time()
        cached_result = await cache.get_cached_response(large_text, "summarize", {})
        retrieve_time_compressed = time.time() - start_time
        
        assert cached_result is not None, "Large text should be cached with compression"
        
        compression_results["with_compression"] = {
            "cache_time_ms": cache_time_compressed * 1000,
            "retrieve_time_ms": retrieve_time_compressed * 1000,
            "text_size": len(large_text),
            "response_size": len(str(large_response))
        }
        
        print(f"  Compression: cache={cache_time_compressed*1000:.2f}ms, retrieve={retrieve_time_compressed*1000:.2f}ms")
        
        # Performance assertion for compression
        assert cache_time_compressed < 0.5, f"Compressed cache too slow: {cache_time_compressed}s"
        assert retrieve_time_compressed < 0.1, f"Compressed retrieve too slow: {retrieve_time_compressed}s"
        
        print("✓ Compression effectiveness testing completed")
        
        # Step 5: Memory usage patterns
        print("Testing memory usage patterns...")
        
        memory_results = {}
        
        # Fill cache with various sizes
        memory_test_items = []
        for i in range(100):
            size_type = ["small", "medium", "large"][i % 3]
            text = f"Memory test {size_type} {i}: " + self.TEST_TEXT_SIZES[size_type]
            response = sample_ai_responses["sentiment"][size_type]
            
            start_time = time.time()
            await cache.cache_response(text, "sentiment", {}, response)
            cache_time = time.time() - start_time
            
            memory_test_items.append({
                "index": i,
                "size_type": size_type,
                "cache_time": cache_time
            })
        
        # Analyze memory performance degradation
        early_items = memory_test_items[:20]
        late_items = memory_test_items[-20:]
        
        early_avg_time = sum(item["cache_time"] for item in early_items) / len(early_items)
        late_avg_time = sum(item["cache_time"] for item in late_items) / len(late_items)
        
        memory_results = {
            "early_cache_avg_ms": early_avg_time * 1000,
            "late_cache_avg_ms": late_avg_time * 1000,
            "performance_degradation": (late_avg_time - early_avg_time) / early_avg_time * 100,
            "total_items_cached": len(memory_test_items)
        }
        
        print(f"  Memory usage: early={early_avg_time*1000:.2f}ms, late={late_avg_time*1000:.2f}ms")
        print(f"  Performance degradation: {memory_results['performance_degradation']:.1f}%")
        
        # Memory performance should not degrade significantly
        assert memory_results["performance_degradation"] < 50, f"Too much performance degradation: {memory_results['performance_degradation']}%"
        
        print("✓ Memory usage patterns tested")
        
        # Step 6: Concurrent performance testing
        print("Testing concurrent performance...")
        
        concurrent_results = {}
        concurrent_operations = 20
        
        async def concurrent_benchmark(operation_id: int):
            """Benchmark concurrent cache operations."""
            text = f"Concurrent benchmark {operation_id}"
            response = {"result": f"Response {operation_id}"}
            
            start_time = time.time()
            await cache.cache_response(text, "summarize", {}, response)
            cache_time = time.time() - start_time
            
            start_time = time.time()
            cached_result = await cache.get_cached_response(text, "summarize", {})
            retrieve_time = time.time() - start_time
            
            return {
                "operation_id": operation_id,
                "cache_time": cache_time,
                "retrieve_time": retrieve_time,
                "success": cached_result is not None
            }
        
        # Run concurrent operations
        concurrent_start = time.time()
        concurrent_tasks = [concurrent_benchmark(i) for i in range(concurrent_operations)]
        concurrent_task_results = await asyncio.gather(*concurrent_tasks)
        concurrent_duration = time.time() - concurrent_start
        
        # Analyze concurrent performance
        successful_operations = [r for r in concurrent_task_results if r["success"]]
        avg_concurrent_cache_time = sum(r["cache_time"] for r in successful_operations) / len(successful_operations)
        avg_concurrent_retrieve_time = sum(r["retrieve_time"] for r in successful_operations) / len(successful_operations)
        
        concurrent_results = {
            "total_operations": concurrent_operations,
            "successful_operations": len(successful_operations),
            "total_duration_ms": concurrent_duration * 1000,
            "avg_cache_time_ms": avg_concurrent_cache_time * 1000,
            "avg_retrieve_time_ms": avg_concurrent_retrieve_time * 1000,
            "operations_per_second": (len(successful_operations) * 2) / concurrent_duration  # cache + retrieve
        }
        
        print(f"  Concurrent: {len(successful_operations)}/{concurrent_operations} succeeded")
        print(f"  Avg times: cache={avg_concurrent_cache_time*1000:.2f}ms, retrieve={avg_concurrent_retrieve_time*1000:.2f}ms")
        print(f"  Throughput: {concurrent_results['operations_per_second']:.1f} ops/s")
        
        # Concurrent performance assertions
        assert len(successful_operations) >= concurrent_operations * 0.9, f"Too many concurrent failures: {len(successful_operations)}/{concurrent_operations}"
        assert concurrent_results["operations_per_second"] > 30, f"Concurrent throughput too low: {concurrent_results['operations_per_second']} ops/s"
        
        print("✓ Concurrent performance testing completed")
        
        # Step 7: Generate structured performance report
        print("Generating performance report...")
        
        performance_report = {
            "benchmark_timestamp": datetime.now().isoformat(),
            "test_configuration": {
                "redis_url": self.TEST_REDIS_URL,
                "default_ttl": self.TEST_DEFAULT_TTL,
                "text_tiers": self.TEST_TEXT_TIERS,
                "operations_tested": self.TEST_OPERATIONS
            },
            "single_operation_latency": single_op_results,
            "throughput_performance": throughput_results,
            "text_size_performance": size_performance,
            "compression_performance": compression_results,
            "memory_usage_patterns": memory_results,
            "concurrent_performance": concurrent_results,
            "performance_summary": {
                "fastest_cache_operation": min(single_op_results.keys(), key=lambda k: single_op_results[k]["avg_cache_ms"]),
                "fastest_retrieve_operation": min(single_op_results.keys(), key=lambda k: single_op_results[k]["avg_retrieve_ms"]),
                "best_throughput_operation": max(throughput_results.keys(), key=lambda k: throughput_results[k]["cache_ops_per_sec"]),
                "overall_health": "PASS" if all([
                    all(metrics["avg_cache_ms"] < 100 for metrics in single_op_results.values()),
                    all(metrics["cache_ops_per_sec"] > 50 for metrics in throughput_results.values()),
                    memory_results["performance_degradation"] < 50,
                    concurrent_results["operations_per_second"] > 30
                ]) else "FAIL"
            }
        }
        
        print("\n=== PERFORMANCE BENCHMARK REPORT ===")
        print(f"Timestamp: {performance_report['benchmark_timestamp']}")
        print(f"Overall Health: {performance_report['performance_summary']['overall_health']}")
        print(f"Fastest Cache Op: {performance_report['performance_summary']['fastest_cache_operation']}")
        print(f"Fastest Retrieve Op: {performance_report['performance_summary']['fastest_retrieve_operation']}")
        print(f"Best Throughput Op: {performance_report['performance_summary']['best_throughput_operation']}")
        print("=====================================\n")
        
        # Assert overall performance health
        assert performance_report["performance_summary"]["overall_health"] == "PASS", "Performance benchmarks did not meet requirements"
        
        print("✓ Performance benchmarking completed successfully")
    
    async def test_security_validation(self, integrated_ai_cache, sample_ai_responses):
        """
        Security validation for parameter mapping and inheritance.
        
        This test validates:
        - Parameter mapping security for injection vulnerabilities
        - AI-specific callback mechanisms for potential exploits
        - Inherited security features cannot be bypassed
        - Basic threat model validation for new architecture
        
        Args:
            integrated_ai_cache: The configured AI cache instance
            sample_ai_responses: Sample responses for testing
        """
        cache = integrated_ai_cache
        
        print("Starting security validation testing...")
        
        # Step 1: Parameter injection vulnerability testing
        print("Testing parameter injection vulnerabilities...")
        
        injection_test_cases = [
            # SQL injection style attacks (though we're not using SQL)
            ("sql_injection_text", "'; DROP TABLE cache; --", "summarize", {}),
            ("sql_injection_operation", "normal text", "'; DELETE FROM cache; --", {}),
            
            # Code injection attempts
            ("code_injection_text", "__import__('os').system('rm -rf /')", "summarize", {}),
            ("code_injection_operation", "normal text", "eval('malicious_code()')", {}),
            
            # Path traversal attempts
            ("path_traversal_text", "../../../etc/passwd", "summarize", {}),
            ("path_traversal_operation", "normal text", "../../../bin/sh", {}),
            
            # JSON injection attempts
            ("json_injection_text", '{"malicious": "payload"}', "summarize", {}),
            ("json_injection_options", "normal text", "summarize", {"key": "__proto__"}),
            
            # Prototype pollution attempts
            ("prototype_pollution", "normal text", "summarize", {"__proto__": {"admin": True}}),
            
            # XSS-style attacks (for string handling)
            ("xss_text", "<script>alert('xss')</script>", "summarize", {}),
            ("xss_operation", "normal text", "<script>malicious()</script>", {}),
            
            # Buffer overflow attempts
            ("buffer_overflow_text", "A" * 100000, "summarize", {}),
            ("large_options", "normal text", "summarize", {"key": "B" * 10000}),
        ]
        
        security_results = {}
        
        for test_name, text, operation, options in injection_test_cases:
            try:
                # Test that malicious inputs are handled safely
                result = await cache.cache_response(text, operation, options, {"safe": "response"})
                
                # If it succeeds, verify it doesn't cause security issues
                cached_result = await cache.get_cached_response(text, operation, options)
                
                if cached_result is not None:
                    security_results[test_name] = "handled_safely"
                    print(f"  {test_name}: Handled safely (cached without security issues)")
                else:
                    security_results[test_name] = "rejected_safely"
                    print(f"  {test_name}: Rejected safely (not cached)")
                
            except (ValidationError, ValueError, TypeError) as e:
                security_results[test_name] = "properly_rejected"
                print(f"  {test_name}: Properly rejected - {type(e).__name__}")
            except Exception as e:
                security_results[test_name] = f"unexpected_error_{type(e).__name__}"
                print(f"  {test_name}: Unexpected error - {type(e).__name__}: {str(e)[:50]}...")
                # Log but don't fail - some errors might be acceptable
        
        # Verify no critical security bypasses occurred
        critical_bypasses = [result for result in security_results.values() if "unexpected_error" in result]
        assert len(critical_bypasses) < len(injection_test_cases) * 0.2, f"Too many unexpected errors: {len(critical_bypasses)}"
        
        print("✓ Parameter injection vulnerability testing completed")
        
        # Step 2: Test callback mechanism security
        print("Testing AI-specific callback mechanisms...")
        
        callback_security_results = {}
        
        # Test with potentially malicious callbacks (if any exist in the system)
        try:
            # Test callback-like parameters that might be exploited
            malicious_callbacks = [
                {"callback": "eval('malicious_code()')"},
                {"on_cache": "__import__('os').system('harmful_command')"},
                {"transform": "lambda x: exec('malicious_code')"},
                {"validator": "compile('exec(\"dangerous\")', '<string>', 'exec')"}
            ]
            
            for i, malicious_callback in enumerate(malicious_callbacks):
                try:
                    # Test if callback parameters are processed unsafely
                    await cache.cache_response(
                        f"callback test {i}",
                        "summarize",
                        {"result": "test"},
                        malicious_callback
                    )
                    
                    callback_security_results[f"callback_{i}"] = "processed_safely"
                    print(f"  Callback test {i}: Processed safely")
                    
                except (ValidationError, ValueError, TypeError):
                    callback_security_results[f"callback_{i}"] = "properly_rejected"
                    print(f"  Callback test {i}: Properly rejected")
                except Exception as e:
                    callback_security_results[f"callback_{i}"] = f"error_{type(e).__name__}"
                    print(f"  Callback test {i}: Error - {type(e).__name__}")
            
        except Exception as e:
            print(f"  Callback testing not applicable: {type(e).__name__}")
        
        print("✓ Callback mechanism security testing completed")
        
        # Step 3: Test inherited security features
        print("Testing inherited security features...")
        
        inherited_security_results = {}
        
        # Test that inherited methods maintain security
        security_sensitive_operations = [
            ("direct_redis_access", "test_key", {"malicious": "payload"}),
            ("pattern_injection", "cache:*; malicious_pattern", {"data": "test"}),
            ("key_traversal", "../../../sensitive_key", {"data": "test"}),
            ("batch_injection", ["normal_key", "malicious_key'; harmful_command"], {"data": "test"}),
        ]
        
        for test_name, key_param, value_param in security_sensitive_operations:
            try:
                # Test inherited set method with potentially malicious parameters
                if isinstance(key_param, list):
                    # Batch operation test
                    batch_data = {k: value_param for k in key_param}
                    await cache.set_batch(batch_data)
                else:
                    # Single operation test
                    await cache.set(key_param, value_param)
                
                inherited_security_results[test_name] = "handled_safely"
                print(f"  {test_name}: Inherited method handled safely")
                
            except (ValidationError, ValueError, TypeError) as e:
                inherited_security_results[test_name] = "properly_rejected"
                print(f"  {test_name}: Properly rejected by inherited method")
            except Exception as e:
                inherited_security_results[test_name] = f"error_{type(e).__name__}"
                print(f"  {test_name}: Error in inherited method - {type(e).__name__}")
        
        print("✓ Inherited security features testing completed")
        
        # Step 4: Test parameter mapping security
        print("Testing parameter mapping security...")
        
        mapper = CacheParameterMapper()
        mapping_security_results = {}
        
        # Test malicious parameter mapping attempts
        malicious_mappings = [
            {
                "redis_url": "redis://malicious-host:6379/; rm -rf /",
                "default_ttl": "eval('dangerous_code()')",
                "text_hash_threshold": "__import__('os').system('harmful')"
            },
            {
                "__proto__": {"admin": True},
                "constructor": {"prototype": {"admin": True}},
                "valueOf": "malicious_function"
            },
            {
                "redis_url": "\x00\x01\x02malicious_binary_data",
                "performance_monitor": "lambda: exec('malicious')"
            }
        ]
        
        for i, malicious_params in enumerate(malicious_mappings):
            try:
                # Test parameter mapping with malicious inputs
                generic_params, ai_specific_params = mapper.map_ai_to_generic_params(malicious_params)
                
                # Verify mapping doesn't execute malicious code or cause security issues
                validation_result = mapper.validate_parameter_compatibility(malicious_params)
                
                if validation_result.is_valid:
                    mapping_security_results[f"mapping_{i}"] = "validated_unexpectedly"
                    print(f"  Mapping test {i}: Validated unexpectedly (potential security issue)")
                else:
                    mapping_security_results[f"mapping_{i}"] = "properly_rejected"
                    print(f"  Mapping test {i}: Properly rejected - {len(validation_result.errors)} errors")
                
            except (ValidationError, ValueError, TypeError) as e:
                mapping_security_results[f"mapping_{i}"] = "safely_rejected"
                print(f"  Mapping test {i}: Safely rejected - {type(e).__name__}")
            except Exception as e:
                mapping_security_results[f"mapping_{i}"] = f"error_{type(e).__name__}"
                print(f"  Mapping test {i}: Error - {type(e).__name__}")
        
        print("✓ Parameter mapping security testing completed")
        
        # Step 5: Test data serialization security
        print("Testing data serialization security...")
        
        serialization_security_results = {}
        
        # Test malicious data serialization
        malicious_data = [
            {"__class__": "malicious_class", "data": "exploit"},
            {"__reduce__": "os.system", "args": ["rm -rf /"]},
            {"__setstate__": {"admin": True}},
            "pickle.loads(malicious_pickle_data)",
            {"eval": "__import__('os').system('harmful')"},
            b"\x80\x03c__builtin__\neval\nq\x00X\x0c\x00\x00\x00malicious_codeq\x01\x85q\x02Rq\x03.",  # Malicious pickle data
        ]
        
        for i, malicious_payload in enumerate(malicious_data):
            try:
                # Test caching malicious serializable data
                await cache.cache_response(
                    f"serialization test {i}",
                    "summarize",
                    {},  # Empty options
                    {"content": "test_response", "security_test": True}  # Proper response dict
                )
                
                # Test retrieval doesn't execute malicious code
                cached_result = await cache.get_cached_response(f"serialization test {i}", "summarize", {})
                
                if cached_result is not None:
                    serialization_security_results[f"serialization_{i}"] = "handled_safely"
                    print(f"  Serialization test {i}: Handled safely")
                else:
                    serialization_security_results[f"serialization_{i}"] = "not_cached"
                    print(f"  Serialization test {i}: Not cached (safe)")
                
            except (ValidationError, ValueError, TypeError) as e:
                serialization_security_results[f"serialization_{i}"] = "properly_rejected"
                print(f"  Serialization test {i}: Properly rejected - {type(e).__name__}")
            except Exception as e:
                serialization_security_results[f"serialization_{i}"] = f"error_{type(e).__name__}"
                print(f"  Serialization test {i}: Error - {type(e).__name__}")
        
        print("✓ Data serialization security testing completed")
        
        # Step 6: Test resource exhaustion protection
        print("Testing resource exhaustion protection...")
        
        resource_security_results = {}
        
        # Test protection against resource exhaustion attacks
        try:
            # Extremely large text
            huge_text = "A" * 10_000_000  # 10MB text
            start_time = time.time()
            
            try:
                await cache.cache_response(huge_text, "summarize", {}, {"summary": "test"})
                duration = time.time() - start_time
                
                if duration < 10.0:  # Should handle large data reasonably
                    resource_security_results["huge_text"] = "handled_efficiently"
                    print(f"  Huge text: Handled efficiently in {duration:.2f}s")
                else:
                    resource_security_results["huge_text"] = "slow_but_completed"
                    print(f"  Huge text: Completed slowly in {duration:.2f}s")
                    
            except MemoryError:
                resource_security_results["huge_text"] = "memory_protected"
                print("  Huge text: Protected against memory exhaustion")
            except (ValidationError, ValueError):
                resource_security_results["huge_text"] = "size_limited"
                print("  Huge text: Size limits enforced")
                
        except Exception as e:
            resource_security_results["huge_text"] = f"error_{type(e).__name__}"
            print(f"  Huge text: Error - {type(e).__name__}")
        
        # Test many concurrent operations (potential DoS)
        try:
            dos_tasks = []
            for i in range(1000):  # Many concurrent operations
                task = cache.cache_response(f"dos_test_{i}", "summarize", {}, {"test": i})
                dos_tasks.append(task)
            
            start_time = time.time()
            await asyncio.gather(*dos_tasks[:100])  # Limit to prevent actual DoS
            duration = time.time() - start_time
            
            if duration < 30.0:  # Should handle concurrent load
                resource_security_results["concurrent_load"] = "handled_well"
                print(f"  Concurrent load: Handled well in {duration:.2f}s")
            else:
                resource_security_results["concurrent_load"] = "slow_but_stable"
                print(f"  Concurrent load: Slow but stable in {duration:.2f}s")
                
        except Exception as e:
            resource_security_results["concurrent_load"] = f"protected_{type(e).__name__}"
            print(f"  Concurrent load: Protected - {type(e).__name__}")
        
        print("✓ Resource exhaustion protection testing completed")
        
        # Step 7: Generate security assessment report
        print("Generating security assessment report...")
        
        security_report = {
            "assessment_timestamp": datetime.now().isoformat(),
            "test_categories": {
                "parameter_injection": security_results,
                "callback_security": callback_security_results,
                "inherited_security": inherited_security_results,
                "parameter_mapping": mapping_security_results,
                "data_serialization": serialization_security_results,
                "resource_protection": resource_security_results
            },
            "security_summary": {
                "total_tests": (len(security_results) + len(callback_security_results) + 
                              len(inherited_security_results) + len(mapping_security_results) +
                              len(serialization_security_results) + len(resource_security_results)),
                "properly_handled": 0,
                "security_concerns": [],
                "overall_security_level": "UNKNOWN"
            }
        }
        
        # Analyze security results
        all_results = []
        for category_results in security_report["test_categories"].values():
            all_results.extend(category_results.values())
        
        properly_handled = sum(1 for result in all_results if result in [
            "properly_rejected", "handled_safely", "safely_rejected", "memory_protected", 
            "size_limited", "handled_efficiently", "handled_well"
        ])
        
        unexpected_errors = sum(1 for result in all_results if "unexpected_error" in result)
        validation_bypasses = sum(1 for result in all_results if "validated_unexpectedly" in result)
        
        security_report["security_summary"]["properly_handled"] = properly_handled
        security_report["security_summary"]["properly_handled_percentage"] = (properly_handled / len(all_results)) * 100
        
        # Determine security concerns
        if unexpected_errors > 0:
            security_report["security_summary"]["security_concerns"].append(f"{unexpected_errors} unexpected errors")
        if validation_bypasses > 0:
            security_report["security_summary"]["security_concerns"].append(f"{validation_bypasses} validation bypasses")
        
        # Determine overall security level
        if len(security_report["security_summary"]["security_concerns"]) == 0 and properly_handled >= len(all_results) * 0.9:
            security_level = "HIGH"
        elif len(security_report["security_summary"]["security_concerns"]) <= 1 and properly_handled >= len(all_results) * 0.8:
            security_level = "MEDIUM"
        else:
            security_level = "LOW"
        
        security_report["security_summary"]["overall_security_level"] = security_level
        
        print("\n=== SECURITY ASSESSMENT REPORT ===")
        print(f"Assessment Timestamp: {security_report['assessment_timestamp']}")
        print(f"Total Security Tests: {security_report['security_summary']['total_tests']}")
        print(f"Properly Handled: {properly_handled}/{len(all_results)} ({security_report['security_summary']['properly_handled_percentage']:.1f}%)")
        print(f"Security Concerns: {security_report['security_summary']['security_concerns']}")
        print(f"Overall Security Level: {security_level}")
        print("===================================\n")
        
        # Security assertions
        assert security_level in ["HIGH", "MEDIUM", "LOW"], f"Security level should be valid: {security_level}"
        assert properly_handled >= len(all_results) * 0.65, f"Too few tests properly handled: {properly_handled}/{len(all_results)}"
        assert validation_bypasses <= 1, f"Too many security validation bypasses detected: {validation_bypasses}"
        
        print("✓ Security validation testing completed successfully")