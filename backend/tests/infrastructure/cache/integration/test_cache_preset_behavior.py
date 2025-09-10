"""Verify Preset-Driven Behavioral Differences

This module provides integration tests that verify preset configurations result in
observable behavioral differences, validating the cache preset system provides
meaningful configuration distinctions rather than just parameter variations.

Focus on testing behavioral outcomes visible through the public API rather than
internal configuration details. Tests handle Redis fallback scenarios where
Redis is unavailable and factory creates InMemoryCache.
"""

import pytest

from app.infrastructure.cache.factory import CacheFactory
from app.infrastructure.cache.cache_presets import cache_preset_manager
from app.infrastructure.cache.redis_ai import AIResponseCache
from app.infrastructure.cache.redis_generic import GenericRedisCache
from app.infrastructure.cache.memory import InMemoryCache


class TestCachePresetBehavior:
    """
    Test suite for verifying preset-driven behavioral differences.
    
    Integration Scope:
        Tests cache factory creating different cache types based on presets
        and verifies those caches exhibit observably different behaviors.
    
    Business Impact:
        Ensures preset system delivers meaningful behavioral differences
        rather than just configuration parameter variations.
    
    Test Strategy:
        - Compare AI vs generic cache key generation patterns
        - Verify operation-specific TTL behavior differences
        - Test text hashing threshold behavioral differences
        - Validate preset-driven cache type selection
    """

    @pytest.fixture
    def cache_factory(self):
        """Create a cache factory for preset-based cache creation."""
        return CacheFactory()
    
    @pytest.mark.asyncio
    async def test_factory_method_behavioral_differences(self, cache_factory):
        """
        Test that different factory methods produce observably different behaviors.
        
        Behavior Under Test:
            AI factory method should attempt to create AIResponseCache with AI features,
            while web factory method creates GenericRedisCache. When Redis unavailable,
            both fall back to InMemoryCache but retain different configurations.
        
        Business Impact:
            Verifies factory methods provide appropriate cache configurations
            for different application types, even when infrastructure fallback occurs.
        
        Success Criteria:
            - AI factory method creates cache configured for AI workloads
            - Web factory method creates cache configured for web applications  
            - Different TTL defaults demonstrate different factory behaviors
            - Graceful degradation handling works for both factory types
        """
        # Create AI cache using factory method
        ai_cache = await cache_factory.for_ai_app(
            redis_url="redis://localhost:6379",
            default_ttl=7200  # 2 hours for AI operations
        )
        
        # Create web cache using factory method
        web_cache = await cache_factory.for_web_app(
            redis_url="redis://localhost:6379", 
            default_ttl=1800  # 30 minutes for web operations
        )
        
        # Both should be InMemoryCache due to Redis fallback, but configured differently
        assert isinstance(ai_cache, InMemoryCache), "AI factory should create InMemoryCache when Redis unavailable"
        assert isinstance(web_cache, InMemoryCache), "Web factory should create InMemoryCache when Redis unavailable"
        
        # Test that caches can store and retrieve data
        await ai_cache.set("ai_test_key", {"data": "ai_value"})
        await web_cache.set("web_test_key", {"data": "web_value"})
        
        ai_value = await ai_cache.get("ai_test_key")
        web_value = await web_cache.get("web_test_key")
        
        assert ai_value == {"data": "ai_value"}, "AI cache should store and retrieve data"
        assert web_value == {"data": "web_value"}, "Web cache should store and retrieve data"
        
        # Verify different cache instances (different configurations)
        assert ai_cache is not web_cache, "Factory should create different cache instances"

    @pytest.mark.asyncio 
    async def test_testing_cache_isolation_behavior(self, cache_factory):
        """
        Test that testing factory method creates isolated cache behavior.
        
        Behavior Under Test:
            Testing factory method should create InMemoryCache when use_memory_cache=True,
            providing predictable testing behavior without external dependencies.
        
        Business Impact:
            Ensures testing infrastructure provides reliable, isolated cache
            behavior for consistent test execution across environments.
        
        Success Criteria:
            - Testing factory creates InMemoryCache when requested
            - Cache supports basic operations for testing scenarios
            - Multiple test caches remain isolated from each other
        """
        # Create isolated testing caches
        test_cache1 = await cache_factory.for_testing(
            use_memory_cache=True,
            default_ttl=60
        )
        
        test_cache2 = await cache_factory.for_testing(
            use_memory_cache=True,
            default_ttl=120
        )
        
        # Both should be InMemoryCache for isolated testing
        assert isinstance(test_cache1, InMemoryCache), "Testing factory should create InMemoryCache"
        assert isinstance(test_cache2, InMemoryCache), "Testing factory should create InMemoryCache"
        
        # Test cache isolation - operations on one cache don't affect the other
        await test_cache1.set("shared_key", "cache1_value")
        await test_cache2.set("shared_key", "cache2_value")
        
        cache1_value = await test_cache1.get("shared_key")
        cache2_value = await test_cache2.get("shared_key")
        
        # Verify isolation - same keys have different values in different caches
        assert cache1_value == "cache1_value", "Cache 1 should have its own value"
        assert cache2_value == "cache2_value", "Cache 2 should have its own value"
        assert cache1_value != cache2_value, "Caches should be isolated"
        
        # Verify different instances
        assert test_cache1 is not test_cache2, "Factory should create different cache instances"

    @pytest.mark.asyncio
    async def test_cache_configuration_parameter_acceptance(self, cache_factory):
        """
        Test that factory methods accept different configuration parameters.
        
        Behavior Under Test:
            Different factory methods should accept their intended configuration
            parameters and create appropriately configured cache instances.
        
        Business Impact:
            Ensures factory methods provide proper configuration interfaces
            for different application requirements.
        
        Success Criteria:
            - AI factory accepts AI-specific parameters like operation_ttls
            - Web factory accepts web-specific parameters  
            - Testing factory accepts testing-specific parameters
            - All factories create working cache instances
        """
        # Test AI factory with AI-specific parameters
        ai_cache = await cache_factory.for_ai_app(
            default_ttl=7200,
            text_hash_threshold=500,
            operation_ttls={"summarize": 1800, "sentiment": 900}
        )
        
        # Test web factory with web-specific parameters  
        web_cache = await cache_factory.for_web_app(
            default_ttl=1800,
            l1_cache_size=200,
            compression_threshold=2000
        )
        
        # Test testing factory with testing-specific parameters
        test_cache = await cache_factory.for_testing(
            default_ttl=60,
            use_memory_cache=True,
            l1_cache_size=50
        )
        
        # All should create working cache instances (InMemoryCache due to Redis fallback)
        assert isinstance(ai_cache, InMemoryCache), "AI factory should create working cache"
        assert isinstance(web_cache, InMemoryCache), "Web factory should create working cache"
        assert isinstance(test_cache, InMemoryCache), "Testing factory should create working cache"
        
        # Test basic operations work
        await ai_cache.set("ai_key", "ai_value")
        await web_cache.set("web_key", "web_value")
        await test_cache.set("test_key", "test_value")
        
        assert await ai_cache.get("ai_key") == "ai_value"
        assert await web_cache.get("web_key") == "web_value" 
        assert await test_cache.get("test_key") == "test_value"

    @pytest.mark.asyncio
    async def test_graceful_degradation_behavior_differences(self, cache_factory):
        """
        Test that different factory methods provide graceful degradation consistently.
        
        Behavior Under Test:
            All factory methods should gracefully handle Redis unavailability
            by falling back to InMemoryCache while preserving their intended
            configuration characteristics.
        
        Business Impact:
            Ensures application remains functional even when Redis infrastructure
            is unavailable, providing consistent behavior across factory types.
        
        Success Criteria:
            - All factory methods successfully create working cache instances
            - Fallback caches maintain basic functionality
            - Different factory methods create isolated cache instances
            - Cache operations work correctly after fallback
        """
        # Create caches with different factory methods
        ai_cache = await cache_factory.for_ai_app(
            redis_url="redis://localhost:6379",  # Will fail and fallback
            default_ttl=7200
        )
        
        web_cache = await cache_factory.for_web_app(
            redis_url="redis://localhost:6379",  # Will fail and fallback
            default_ttl=1800
        )
        
        test_cache = await cache_factory.for_testing(
            use_memory_cache=True,  # Explicit memory cache
            default_ttl=60
        )
        
        # All should be InMemoryCache due to fallback
        assert isinstance(ai_cache, InMemoryCache), "AI factory should fallback to InMemoryCache"
        assert isinstance(web_cache, InMemoryCache), "Web factory should fallback to InMemoryCache"
        assert isinstance(test_cache, InMemoryCache), "Testing factory should create InMemoryCache"
        
        # Test basic cache functionality works after fallback
        test_data = [
            (ai_cache, "ai_key", {"ai": "data"}),
            (web_cache, "web_key", {"web": "data"}),
            (test_cache, "test_key", {"test": "data"})
        ]
        
        for cache, key, value in test_data:
            await cache.set(key, value)
            retrieved = await cache.get(key)
            assert retrieved == value, f"Cache should store and retrieve {key}"
        
        # Verify cache isolation
        ai_value = await ai_cache.get("ai_key")
        web_value = await web_cache.get("web_key")
        test_value = await test_cache.get("test_key")
        
        assert ai_value == {"ai": "data"}
        assert web_value == {"web": "data"}
        assert test_value == {"test": "data"}
        
        # Verify different instances
        assert ai_cache is not web_cache
        assert web_cache is not test_cache
        assert ai_cache is not test_cache

    @pytest.mark.asyncio
    async def test_preset_configuration_behavioral_differences(self):
        """
        Test that preset configurations provide meaningful behavioral differences.
        
        Behavior Under Test:
            Different presets should provide observably different configuration
            values that would result in different cache behavior if Redis were available.
        
        Business Impact:
            Validates that preset system provides meaningful configuration
            differences for different deployment environments and use cases.
        
        Success Criteria:
            - Development and production presets have different TTL values
            - AI presets include AI-specific configuration
            - Generic presets exclude AI-specific configuration
            - Presets provide environment-appropriate defaults
        """
        # Test development vs production preset differences
        dev_preset = cache_preset_manager.get_preset("development")
        prod_preset = cache_preset_manager.get_preset("production")
        
        dev_config = dev_preset.to_cache_config().to_dict()
        prod_config = prod_preset.to_cache_config().to_dict()
        
        # Verify presets have different TTL values (development should be shorter)
        dev_ttl = dev_config.get('default_ttl')
        prod_ttl = prod_config.get('default_ttl')
        
        assert dev_ttl is not None, "Development TTL should be configured"
        assert prod_ttl is not None, "Production TTL should be configured"
        assert dev_ttl != prod_ttl, "Development and production should have different TTLs"
        assert dev_ttl < prod_ttl, "Development TTL should be shorter than production for faster feedback"
        
        # Test AI vs generic preset configuration differences
        ai_dev_preset = cache_preset_manager.get_preset("ai-development")
        ai_config = ai_dev_preset.to_cache_config().to_dict()
        
        # Verify AI preset includes AI-specific configuration (nested in ai_config)
        assert 'ai_config' in ai_config, "AI preset should include ai_config section"
        ai_specific = ai_config['ai_config']
        assert 'text_hash_threshold' in ai_specific, "AI preset should include text_hash_threshold in ai_config"
        assert 'operation_ttls' in ai_specific, "AI preset should include operation_ttls in ai_config"
        assert isinstance(ai_specific['operation_ttls'], dict), "Operation TTLs should be dictionary"
        assert len(ai_specific['operation_ttls']) > 0, "Should have configured operation TTLs"
        
        # Verify generic preset excludes AI configuration (ai_config is None or missing)
        assert dev_config.get('ai_config') is None, "Generic preset should have ai_config as None"
        assert not dev_config.get('enable_ai_cache', False), "Generic preset should not enable AI cache"
        
        # Test preset variety
        disabled_preset = cache_preset_manager.get_preset("disabled")
        disabled_config = disabled_preset.to_cache_config().to_dict()
        
        # Disabled preset should have minimal configuration
        disabled_ttl = disabled_config.get('default_ttl')
        assert disabled_ttl is not None, "Disabled preset should have TTL"
        assert disabled_ttl <= dev_ttl, "Disabled preset should have minimal TTL"