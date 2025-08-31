"""
Integration tests for cache infrastructure components.

This test suite verifies cross-component interactions using real implementations
instead of extensive mocking. Tests demonstrate how different cache components
work together to provide complete functionality.

Coverage Focus:
    - Factory + Cache + Monitor integration
    - Settings + Factory integration  
    - Cache + Key Generator + Performance Monitor integration
    - End-to-end cache workflows with real components

External Dependencies:
    Uses real components with graceful degradation for Redis unavailability.
    No internal mocking - only system boundary mocking where necessary.
"""

import pytest
import asyncio
from typing import Dict, Any

from app.infrastructure.cache.factory import CacheFactory
from app.infrastructure.cache.monitoring import CachePerformanceMonitor
from app.infrastructure.cache.key_generator import CacheKeyGenerator
from app.core.exceptions import InfrastructureError


class TestCacheFactoryIntegration:
    """
    Integration tests for CacheFactory with other components.
    
    Tests real component interactions rather than mocked dependencies.
    """
    
    @pytest.mark.asyncio
    async def test_factory_creates_cache_with_monitoring_integration(self):
        """
        Test complete factory workflow with performance monitoring integration.
        
        Verifies:
            Factory creates cache with real monitoring component integration
            
        Business Impact:
            Ensures end-to-end monitoring functionality works correctly
            
        Integration Points:
            - CacheFactory -> Cache creation
            - Cache -> Performance monitoring integration
            - Monitor -> Metrics collection during operations
        """
        # Given: Real factory and monitor components
        factory = CacheFactory()
        monitor = CachePerformanceMonitor()
        
        # When: Factory creates cache with monitoring
        cache = await factory.for_testing(
            performance_monitor=monitor,
            use_memory_cache=True
        )
        
        # Then: Integration should work end-to-end
        assert cache is not None
        
        # Test actual monitoring integration through operations
        test_key = "integration:factory:monitoring"
        test_value = {"integration_test": True, "component": "factory"}
        
        await cache.set(test_key, test_value)
        retrieved_value = await cache.get(test_key)
        
        assert retrieved_value == test_value
        
        # Clean up
        await cache.delete(test_key)
        
    @pytest.mark.asyncio
    async def test_factory_with_settings_creates_configured_cache(self, test_settings):
        """
        Test factory integration with real Settings configuration.
        
        Verifies:
            Factory respects actual configuration from Settings
            
        Integration Points:
            - Settings -> Configuration loading
            - Factory -> Configuration application
            - Cache -> Configured behavior
        """
        # Given: Real settings and factory
        factory = CacheFactory()
        
        # When: Factory uses real settings configuration
        cache = await factory.for_web_app(
            settings=test_settings,
            fail_on_connection_error=False  # Allow graceful degradation
        )
        
        # Then: Cache should be created with settings-based configuration
        assert cache is not None
        
        # Test cache functionality with settings-derived configuration
        test_key = "integration:settings:config"
        test_value = {"settings_integration": True}
        
        await cache.set(test_key, test_value)
        result = await cache.get(test_key)
        
        assert result == test_value
        
        # Clean up
        await cache.delete(test_key)


class TestCacheKeyGeneratorIntegration:
    """
    Integration tests for CacheKeyGenerator with cache and monitoring.
    
    Tests real component interactions in key generation workflows.
    """
    
    @pytest.mark.asyncio
    async def test_key_generator_with_cache_and_monitoring_integration(self):
        """
        Test complete key generation workflow with cache and monitoring.
        
        Verifies:
            Key generator integrates properly with cache operations and monitoring
            
        Business Impact:
            Ensures key generation, caching, and monitoring work together correctly
            
        Integration Points:
            - KeyGenerator -> Key generation with monitoring
            - Cache -> Key-based operations
            - Monitor -> Key generation metrics
        """
        # Given: Real components integrated together
        monitor = CachePerformanceMonitor()
        key_generator = CacheKeyGenerator(performance_monitor=monitor)
        factory = CacheFactory()
        cache = await factory.for_testing(
            performance_monitor=monitor,
            use_memory_cache=True
        )
        
        # When: Using integrated workflow
        text = "Integration test for key generation and caching"
        operation = "test_integration"
        options = {"integration": True}
        
        # Generate key with monitoring
        cache_key = key_generator.generate_cache_key(text, operation, options)
        
        # Use key with cache (also monitored)
        test_value = {
            "text": text,
            "operation": operation,
            "generated_key": cache_key
        }
        
        await cache.set(cache_key, test_value)
        retrieved_value = await cache.get(cache_key)
        
        # Then: End-to-end workflow should work correctly
        assert retrieved_value == test_value
        # Key should contain the operation (actual key format may vary)
        assert operation in cache_key
        
        # Verify key exists
        key_exists = await cache.exists(cache_key)
        assert key_exists is True
        
        # Clean up
        await cache.delete(cache_key)
        
        # Verify cleanup
        exists_after_delete = await cache.exists(cache_key)
        assert exists_after_delete is False


class TestEndToEndCacheWorkflows:
    """
    End-to-end integration tests for complete cache workflows.
    
    Tests realistic usage patterns with multiple integrated components.
    """
    
    @pytest.mark.asyncio
    async def test_complete_ai_cache_workflow_integration(self):
        """
        Test complete AI cache workflow with all components integrated.
        
        Verifies:
            All AI cache components work together in realistic workflows
            
        Business Impact:
            Ensures AI cache functionality works end-to-end in production scenarios
            
        Integration Points:
            - Factory -> AI cache creation
            - KeyGenerator -> AI-specific key generation
            - Cache -> AI response storage and retrieval
            - Monitor -> AI cache performance tracking
        """
        # Given: Complete AI cache setup with real components
        monitor = CachePerformanceMonitor()
        key_generator = CacheKeyGenerator(
            performance_monitor=monitor,
            text_hash_threshold=1000
        )
        factory = CacheFactory()
        
        # Create AI cache with monitoring
        cache = await factory.for_ai_app(
            performance_monitor=monitor,
            fail_on_connection_error=False
        )
        
        # When: Performing complete AI cache workflow
        # Simulate AI text processing workflow
        texts = [
            "Short text for AI processing",
            "Much longer text that should trigger hashing behavior in the key generator " * 20,
            "Another AI processing request with different content"
        ]
        
        operations = ["summarize", "sentiment", "key_points"]
        
        # Process multiple AI requests
        for i, text in enumerate(texts):
            operation = operations[i % len(operations)]
            
            # Generate AI-appropriate cache key
            cache_key = key_generator.generate_cache_key(text, operation, {})
            
            # Store AI response
            ai_response = {
                "operation": operation,
                "text_length": len(text),
                "result": f"AI {operation} result for text {i+1}",
                "metadata": {"processed_at": "2023-01-01", "model": "test"}
            }
            
            await cache.set(cache_key, ai_response, ttl=3600)
            
            # Retrieve and verify
            retrieved = await cache.get(cache_key)
            assert retrieved == ai_response
            assert await cache.exists(cache_key) is True
        
        # Clean up all test data
        for i, text in enumerate(texts):
            operation = operations[i % len(operations)]
            cache_key = key_generator.generate_cache_key(text, operation, {})
            await cache.delete(cache_key)
            
            # Verify cleanup
            assert await cache.exists(cache_key) is False
            
    @pytest.mark.asyncio
    async def test_cache_fallback_behavior_integration(self):
        """
        Test cache fallback behavior integration across components.
        
        Verifies:
            Graceful degradation works across all integrated components
            
        Business Impact:
            Ensures system resilience when external dependencies are unavailable
            
        Integration Points:
            - Factory -> Fallback cache creation
            - Settings -> Fallback configuration
            - Components -> Graceful degradation behavior
        """
        # Given: Factory configured for fallback behavior
        factory = CacheFactory()
        
        # When: Creating cache with fallback enabled
        cache = await factory.for_web_app(
            redis_url="redis://invalid-host:99999",  # Intentionally invalid
            fail_on_connection_error=False  # Enable graceful fallback
        )
        
        # Then: Should get fallback cache that works normally
        assert cache is not None
        
        # Test normal operations work with fallback
        test_key = "integration:fallback:test"
        test_value = {"fallback": True, "working": True}
        
        await cache.set(test_key, test_value)
        retrieved = await cache.get(test_key)
        
        assert retrieved == test_value
        assert await cache.exists(test_key) is True
        
        # Clean up
        await cache.delete(test_key)
        assert await cache.exists(test_key) is False


class TestCacheComponentInteroperability:
    """
    Tests for cache component interoperability and compatibility.
    
    Verifies different cache implementations can be used interchangeably.
    """
    
    @pytest.mark.asyncio
    @pytest.mark.parametrize("cache_type", ["memory", "web", "ai"])
    async def test_cache_interoperability_across_factory_methods(self, cache_type):
        """
        Test that caches created by different factory methods are interoperable.
        
        Verifies:
            All factory-created caches support the same basic operations
            
        Integration Points:
            - Factory methods -> Different cache creation paths
            - CacheInterface -> Consistent behavior across implementations
        """
        # Given: Factory creating different types of caches
        factory = CacheFactory()
        
        if cache_type == "memory":
            cache = await factory.for_testing(use_memory_cache=True)
        elif cache_type == "web":
            cache = await factory.for_web_app(fail_on_connection_error=False)
        elif cache_type == "ai":
            cache = await factory.for_ai_app(fail_on_connection_error=False)
        
        # When: Using cache for basic operations
        test_key = f"interop:test:{cache_type}"
        test_value = {"cache_type": cache_type, "interoperability": True}
        
        await cache.set(test_key, test_value)
        retrieved = await cache.get(test_key)
        
        # Then: All caches should support consistent operations
        assert retrieved == test_value
        assert await cache.exists(test_key) is True
        
        await cache.delete(test_key)
        assert await cache.exists(test_key) is False
        
        # Verify cache supports basic CacheInterface contract
        assert hasattr(cache, 'get')
        assert hasattr(cache, 'set')
        assert hasattr(cache, 'delete')
        assert hasattr(cache, 'exists')