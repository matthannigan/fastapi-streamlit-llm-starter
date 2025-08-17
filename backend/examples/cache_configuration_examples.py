"""
AIResponseCache Configuration Examples

This script provides practical examples of how to configure and use the AIResponseCache
with different settings for various use cases. It demonstrates:

1. Basic cache setup and usage
2. Custom configuration for different environments
3. Performance monitoring and optimization
4. Cache invalidation patterns
5. Graceful degradation scenarios
6. Memory vs Redis caching strategies

Each example is self-contained and can be run independently to understand
specific caching patterns and their trade-offs.
"""

import asyncio
import logging
import time
from typing import Dict, Any, List
from datetime import datetime

from app.infrastructure.cache import (
    AIResponseCache,
    AIResponseCacheConfig,
    GenericRedisCache,
    InMemoryCache,
    CachePerformanceMonitor,
    CacheParameterMapper,
    REDIS_AVAILABLE
)

# Setup logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


class CacheConfigurationExamples:
    """
    Comprehensive examples of AIResponseCache configurations for different scenarios.
    """
    
    def __init__(self):
        self.caches = {}
        self.performance_monitors = {}
    
    async def example_1_basic_cache_setup(self):
        """
        Example 1: Basic cache setup with default configuration using AIResponseCacheConfig.
        
        This demonstrates the new Phase 2 configuration approach with validation.
        Good for development and simple use cases.
        """
        logger.info("\n🔧 Example 1: Basic Cache Setup (Phase 2 - Configuration-Based)")
        logger.info("=" * 50)
        
        # Create configuration with defaults
        config = AIResponseCacheConfig()
        
        # Validate configuration before use
        validation_result = config.validate()
        if not validation_result.is_valid:
            logger.error(f"❌ Configuration validation failed: {validation_result.errors}")
            return None
        
        logger.info("✅ Configuration validation passed")
        
        # Create cache using configuration object
        cache = AIResponseCache(config)
        
        # Try to connect (will gracefully degrade if Redis unavailable)
        connected = await cache.connect()
        
        if connected:
            logger.info("✅ Connected to Redis with default settings")
        else:
            logger.info("⚠️  Using memory-only mode (Redis unavailable)")
        
        # Basic usage example
        test_text = "This is a simple test document for caching demonstration."
        
        # Cache a response
        sample_response = {
            "summary": "This is a test document about caching.",
            "confidence": 0.95,
            "model": "example-model",
            "timestamp": datetime.now().isoformat()
        }
        
        await cache.cache_response(
            text=test_text,
            operation="summarize",
            options={"max_length": 100},
            response=sample_response
        )
        
        logger.info("💾 Cached sample response")
        
        # Retrieve the cached response
        cached_result = await cache.get_cached_response(
            text=test_text,
            operation="summarize",
            options={"max_length": 100}
        )
        
        if cached_result:
            logger.info("⚡ Successfully retrieved cached response")
            logger.info(f"   Summary: {cached_result['summary']}")
        else:
            logger.warning("❌ Failed to retrieve cached response")
        
        self.caches['basic'] = cache
        return cache
    
    async def example_2_development_optimized_cache(self):
        """
        Example 2: Development-optimized cache configuration using AIResponseCacheConfig.
        
        Demonstrates Phase 2 configuration approach with development-specific settings.
        Optimized for fast development cycles with quick feedback.
        """
        logger.info("\n🛠️  Example 2: Development-Optimized Cache (Phase 2 - Config-Based)")
        logger.info("=" * 50)
        
        # Create performance monitor for development
        dev_monitor = CachePerformanceMonitor(
            retention_hours=1,  # Keep metrics for 1 hour only
            memory_warning_threshold_bytes=10 * 1024 * 1024,  # 10MB warning
            memory_critical_threshold_bytes=25 * 1024 * 1024,  # 25MB critical
        )
        
        # Development cache configuration using AIResponseCacheConfig
        dev_config = AIResponseCacheConfig(
            redis_url="redis://localhost:6379",
            default_ttl=300,  # 5 minutes - short for development
            text_hash_threshold=200,  # Hash smaller texts for testing
            compression_threshold=500,  # Compress smaller responses for testing
            compression_level=1,  # Fast compression for development
            memory_cache_size=50,  # Smaller memory cache for development
            text_size_tiers={
                'small': 100,
                'medium': 1000,
                'large': 10000,
            },
            performance_monitor=dev_monitor
        )
        
        # Validate development configuration
        validation_result = dev_config.validate()
        if not validation_result.is_valid:
            logger.error(f"❌ Development config validation failed: {validation_result.errors}")
            return None
        
        logger.info("✅ Development configuration validated")
        
        # Create cache using configuration
        dev_cache = AIResponseCache(dev_config)
        
        await dev_cache.connect()
        
        # Test with different text sizes to see tier behavior
        test_cases = [
            ("Small text for testing", "sentiment"),
            ("Medium text " * 50, "key_points"),
            ("Large text " * 200, "analyze")
        ]
        
        logger.info("Testing different text size tiers:")
        
        for text, operation in test_cases:
            # Determine tier
            tier = dev_cache._get_text_tier(text)
            
            # Create mock response
            response = {
                "result": f"Mock {operation} result",
                "text_length": len(text),
                "tier": tier,
                "timestamp": datetime.now().isoformat()
            }
            
            # Cache and retrieve
            start_time = time.time()
            await dev_cache.cache_response(text, operation, {}, response)
            cache_time = time.time() - start_time
            
            start_time = time.time()
            cached = await dev_cache.get_cached_response(text, operation, {})
            retrieve_time = time.time() - start_time
            
            logger.info(f"   {tier.upper()} tier - Cache: {cache_time:.3f}s, Retrieve: {retrieve_time:.3f}s")
        
        self.caches['development'] = dev_cache
        self.performance_monitors['development'] = dev_monitor
        return dev_cache
    
    async def example_3_generic_redis_cache(self):
        """
        Example 3: GenericRedisCache - The inheritance base (NEW in Phase 2).
        
        Demonstrates the new GenericRedisCache that serves as the base for AIResponseCache.
        Perfect for general-purpose applications that need Redis caching without AI features.
        """
        logger.info("\n🔧 Example 3: GenericRedisCache (Phase 2 - Inheritance Base)")
        logger.info("=" * 50)
        
        # Create a generic Redis cache for non-AI applications
        generic_cache = GenericRedisCache(
            redis_url="redis://localhost:6379",
            default_ttl=1800,                   # 30 minutes
            enable_l1_cache=True,               # Enable memory tier
            l1_cache_size=100,                  # 100 items in memory
            compression_threshold=2000,         # Compress data > 2KB
            compression_level=6                 # Balanced compression
        )
        
        # Connect to Redis
        connected = await generic_cache.connect()
        
        if connected:
            logger.info("✅ GenericRedisCache connected to Redis")
        else:
            logger.info("⚠️  GenericRedisCache using memory-only mode")
        
        # Test generic cache operations (not AI-specific)
        test_data = {
            "user:profile:123": {"name": "John Doe", "email": "john@example.com", "role": "admin"},
            "session:abc456": {"user_id": 123, "created_at": "2024-01-15T10:30:00Z"},
            "config:feature_flags": {"new_ui": True, "beta_features": False},
            "api:weather:nyc": {"temperature": 22, "humidity": 65, "conditions": "sunny"}
        }
        
        logger.info("Testing GenericRedisCache with various data types:")
        
        # Store data with different TTLs
        for key, value in test_data.items():
            if "config" in key:
                ttl = 3600  # Config data - 1 hour
            elif "session" in key:
                ttl = 1800  # Session data - 30 minutes  
            else:
                ttl = 7200  # Other data - 2 hours
                
            await generic_cache.set(key, value, ttl=ttl)
            logger.info(f"   📦 Stored {key} (TTL: {ttl}s)")
        
        # Retrieve and verify data
        retrieved_count = 0
        for key in test_data.keys():
            cached_value = await generic_cache.get(key)
            if cached_value:
                retrieved_count += 1
                logger.info(f"   ✅ Retrieved {key}")
        
        logger.info(f"   📊 Successfully retrieved {retrieved_count}/{len(test_data)} items")
        
        # Test additional GenericRedisCache features
        logger.info("\nTesting GenericRedisCache advanced features:")
        
        # Pattern operations
        config_keys = await generic_cache.get_keys("config:*")
        logger.info(f"   🔍 Found {len(config_keys)} config keys: {config_keys}")
        
        # Check existence and TTL
        exists = await generic_cache.exists("user:profile:123")
        ttl = await generic_cache.get_ttl("user:profile:123")
        logger.info(f"   ⏰ user:profile:123 exists: {exists}, TTL: {ttl}s")
        
        # Memory cache statistics  
        if hasattr(generic_cache, 'get_memory_usage'):
            memory_stats = generic_cache.get_memory_usage()
            logger.info(f"   💾 Memory cache: {memory_stats.get('memory_cache_entries', 0)} entries")
        
        # Demonstrate that this is the base class for AIResponseCache
        logger.info(f"\n🏗️  Architecture: AIResponseCache inherits from {type(generic_cache).__name__}")
        logger.info("   • AIResponseCache gets all GenericRedisCache features")
        logger.info("   • Plus AI-specific optimizations (key generation, text tiers, etc.)")
        
        self.caches['generic'] = generic_cache
        return generic_cache
    
    async def example_4_production_optimized_cache(self):
        """
        Example 3: Production-optimized cache configuration.
        
        Optimized for high performance and reliability in production.
        Uses higher compression, longer TTLs, and more aggressive caching.
        """
        logger.info("\n🚀 Example 3: Production-Optimized Cache")
        logger.info("=" * 50)
        
        # Production performance monitor with higher thresholds
        prod_monitor = CachePerformanceMonitor(
            retention_hours=24,  # Keep metrics for 24 hours
            memory_warning_threshold_bytes=100 * 1024 * 1024,  # 100MB warning
            memory_critical_threshold_bytes=250 * 1024 * 1024,  # 250MB critical
        )
        
        # Set custom performance thresholds after initialization
        prod_monitor.key_generation_threshold = 0.1  # 100ms threshold
        prod_monitor.cache_operation_threshold = 0.2  # 200ms threshold
        
        # Production cache configuration
        prod_cache = AIResponseCache(
            redis_url="redis://localhost:6379",
            default_ttl=7200,  # 2 hours default
            text_hash_threshold=1000,  # Standard threshold
            compression_threshold=2000,  # Compress larger responses
            compression_level=9,  # Maximum compression for production
            memory_cache_size=200,  # Larger memory cache
            text_size_tiers={
                'small': 500,
                'medium': 5000,
                'large': 50000,
            },
            performance_monitor=prod_monitor
        )
        
        await prod_cache.connect()
        
        # Override operation-specific TTLs for production
        prod_cache.operation_ttls.update({
            "summarize": 14400,  # 4 hours - summaries are stable
            "sentiment": 86400,  # 24 hours - sentiment rarely changes
            "key_points": 7200,  # 2 hours
            "questions": 3600,   # 1 hour
            "qa": 1800,         # 30 minutes - context-dependent
            "analyze": 10800,   # 3 hours - analysis is fairly stable
        })
        
        logger.info("✅ Production cache configured with:")
        logger.info(f"   • Default TTL: {prod_cache.default_ttl}s")
        logger.info(f"   • Compression level: {prod_cache.compression_level}")
        logger.info(f"   • Memory cache size: {prod_cache.memory_cache_size}")
        logger.info(f"   • Custom operation TTLs: {len(prod_cache.operation_ttls)} operations")
        
        # Test production caching with a larger dataset
        await self._test_production_workload(prod_cache)
        
        self.caches['production'] = prod_cache
        self.performance_monitors['production'] = prod_monitor
        return prod_cache
    
    async def example_5_memory_only_fallback(self):
        """
        Example 5: Memory-only cache for scenarios without Redis.
        
        Demonstrates graceful degradation when Redis is unavailable.
        Uses InMemoryCache as a complete fallback solution.
        """
        logger.info("\n💾 Example 4: Memory-Only Fallback Cache")
        logger.info("=" * 50)
        
        # InMemoryCache as a fallback
        memory_cache = InMemoryCache(
            default_ttl=1800,  # 30 minutes
            max_size=300       # Reasonable size for memory-only operation
        )
        
        logger.info("✅ Memory-only cache initialized")
        logger.info(f"   • Max size: {memory_cache.max_size} entries")
        logger.info(f"   • Default TTL: {memory_cache.default_ttl}s")
        
        # Test memory cache operations
        test_data = [
            {"key": f"test_key_{i}", "value": f"test_value_{i}"} 
            for i in range(10)
        ]
        
        # Set values
        for item in test_data:
            await memory_cache.set(item["key"], item["value"])
        
        # Get values
        retrieved_count = 0
        for item in test_data:
            value = await memory_cache.get(item["key"])
            if value == item["value"]:
                retrieved_count += 1
        
        logger.info(f"   • Successfully stored and retrieved {retrieved_count}/{len(test_data)} items")
        
        # Show memory cache statistics
        stats = memory_cache.get_stats()
        logger.info(f"   • Active entries: {stats['active_entries']}")
        logger.info(f"   • Cache utilization: {stats['utilization_percent']:.1f}%")
        
        self.caches['memory_only'] = memory_cache
        return memory_cache
    
    async def example_6_cache_invalidation_patterns(self):
        """
        Example 6: Cache invalidation and management patterns.
        
        Demonstrates different approaches to cache invalidation and maintenance.
        """
        logger.info("\n🗑️  Example 6: Cache Invalidation Patterns")
        logger.info("=" * 50)
        
        # Use the production cache for this example
        cache = self.caches.get('production') or await self.example_4_production_optimized_cache()
        
        # Populate cache with test data
        test_documents = [
            ("Document about AI technology", "summarize"),
            ("Document about AI technology", "sentiment"),
            ("Different document about machine learning", "summarize"),
            ("User feedback: Great service!", "sentiment"),
            ("User feedback: Poor experience", "sentiment"),
        ]
        
        # Cache all documents
        for i, (text, operation) in enumerate(test_documents):
            response = {
                "result": f"Mock {operation} result for document {i+1}",
                "cached_at": datetime.now().isoformat()
            }
            await cache.cache_response(text, operation, {}, response)
        
        logger.info(f"📦 Cached {len(test_documents)} test documents")
        
        # Pattern 1: Invalidate by operation type
        logger.info("\n1. Invalidating all 'sentiment' operations...")
        try:
            await cache.invalidate_by_operation("sentiment", operation_context="model_update")
            logger.info("   ✅ Sentiment operations invalidated")
        except Exception as e:
            logger.warning(f"   ⚠️  Invalidation failed: {e}")
        
        # Pattern 2: Pattern-based invalidation
        logger.info("\n2. Pattern-based invalidation...")
        try:
            await cache.invalidate_pattern("*AI technology*", operation_context="content_update")
            logger.info("   ✅ AI technology documents invalidated")
        except Exception as e:
            logger.warning(f"   ⚠️  Pattern invalidation failed: {e}")
        
        # Pattern 3: Check what's still cached
        logger.info("\n3. Checking remaining cached items...")
        remaining_count = 0
        for text, operation in test_documents:
            cached = await cache.get_cached_response(text, operation, {})
            if cached:
                remaining_count += 1
        
        logger.info(f"   📊 {remaining_count}/{len(test_documents)} items still cached after invalidation")
    
    async def example_7_performance_monitoring(self):
        """
        Example 7: Performance monitoring and optimization.
        
        Demonstrates how to use performance monitoring to optimize cache configuration.
        """
        logger.info("\n📊 Example 7: Performance Monitoring")
        logger.info("=" * 50)
        
        # Use the development cache with its monitor
        cache = self.caches.get('development')
        monitor = self.performance_monitors.get('development')
        
        if not cache or not monitor:
            logger.warning("⚠️  Development cache not available, creating new one...")
            cache = await self.example_2_development_optimized_cache()
            monitor = self.performance_monitors['development']
        
        # Generate some cache activity for monitoring
        logger.info("Generating cache activity for monitoring...")
        
        test_scenarios = [
            ("Quick test", "sentiment", 0.01),  # Fast operation
            ("Medium length test document " * 20, "summarize", 0.05),  # Medium operation
            ("Long test document " * 100, "analyze", 0.1),  # Slow operation
        ]
        
        for text, operation, simulated_processing_time in test_scenarios:
            # Simulate processing time
            await asyncio.sleep(simulated_processing_time)
            
            response = {
                "result": f"Result for {operation}",
                "processing_time": simulated_processing_time
            }
            
            # Cache the response (this will be monitored)
            await cache.cache_response(text, operation, {}, response)
            
            # Retrieve the response (this will also be monitored)
            await cache.get_cached_response(text, operation, {})
        
        # Display comprehensive performance statistics
        logger.info("\n📈 Performance Statistics:")
        
        # Get cache hit ratio
        hit_ratio = cache.get_cache_hit_ratio()
        logger.info(f"   Hit Ratio: {hit_ratio:.1f}%")
        
        # Get performance summary
        try:
            summary = cache.get_performance_summary()
            logger.info(f"   Average Cache Operation Time: {summary.get('recent_avg_cache_operation_time', 0):.3f}s")
            logger.info(f"   Average Key Generation Time: {summary.get('recent_avg_key_generation_time', 0):.3f}s")
        except Exception as e:
            logger.warning(f"   Could not get performance summary: {e}")
        
        # Check for memory warnings
        warnings = cache.get_memory_warnings()
        if warnings:
            logger.info("\n⚠️  Memory Warnings:")
            for warning in warnings:
                logger.warning(f"   {warning['severity'].upper()}: {warning['message']}")
        else:
            logger.info("   ✅ No memory warnings detected")
        
        # Get detailed performance stats
        try:
            stats = await cache.get_cache_stats()
            perf_stats = stats.get('performance', {})
            logger.info(f"   Total Operations: {perf_stats.get('total_operations', 0)}")
            logger.info(f"   Cache Hits: {perf_stats.get('cache_hits', 0)}")
            logger.info(f"   Cache Misses: {perf_stats.get('cache_misses', 0)}")
        except Exception as e:
            logger.warning(f"   Could not get detailed stats: {e}")
    
    async def _test_production_workload(self, cache: AIResponseCache):
        """Helper method to simulate production workload."""
        
        logger.info("🔄 Testing production workload simulation...")
        
        # Simulate various operations with different characteristics
        operations = [
            ("summarize", "Document summarization task", {"max_length": 200}),
            ("sentiment", "Customer feedback analysis", {"include_confidence": True}),
            ("key_points", "Meeting notes extraction", {"max_points": 5}),
            ("qa", "Question answering task", {"context_window": 1000}),
        ]
        
        # Run multiple iterations to test performance
        for i in range(5):
            for operation, description, options in operations:
                text = f"{description} - iteration {i+1}. " + "Sample content. " * 50
                
                response = {
                    "result": f"Mock {operation} result for iteration {i+1}",
                    "options_used": options,
                    "timestamp": datetime.now().isoformat(),
                    "iteration": i+1
                }
                
                # Cache the response
                await cache.cache_response(text, operation, options, response)
                
                # Simulate cache hits by retrieving some of the responses
                if i > 0:  # Start retrieving from second iteration
                    await cache.get_cached_response(text, operation, options)
        
        logger.info("   ✅ Production workload simulation complete")
    
    async def run_all_examples(self):
        """Run all cache configuration examples in sequence."""
        logger.info("🚀 Running All Cache Configuration Examples")
        logger.info("=" * 60)
        
        try:
            # Run examples in logical order
            await self.example_1_basic_cache_setup()
            await self.example_2_development_optimized_cache()
            await self.example_3_generic_redis_cache()
            await self.example_4_production_optimized_cache()
            await self.example_5_memory_only_fallback()
            await self.example_6_cache_invalidation_patterns()
            await self.example_7_performance_monitoring()
            
            logger.info("\n🎉 All Cache Configuration Examples Complete!")
            logger.info("=" * 60)
            
            # Summary of what was demonstrated
            logger.info("\n📋 Summary of Examples:")
            logger.info("✅ Basic cache setup with AIResponseCacheConfig validation")
            logger.info("✅ Development-optimized configuration with Phase 2 patterns")
            logger.info("✅ GenericRedisCache - inheritance base demonstration")
            logger.info("✅ Production-optimized AIResponseCache configuration")
            logger.info("✅ Memory-only fallback scenarios")
            logger.info("✅ Cache invalidation patterns")
            logger.info("✅ Performance monitoring and optimization")
            
            logger.info(f"\n💾 Created {len(self.caches)} cache instances")
            logger.info(f"📊 Configured {len(self.performance_monitors)} performance monitors")
            
        except Exception as e:
            logger.error(f"❌ Examples failed with error: {e}")
            raise
        finally:
            await self._cleanup_caches()
    
    async def _cleanup_caches(self):
        """Clean up all cache connections."""
        logger.info("\n🧹 Cleaning up cache connections...")
        
        for name, cache in self.caches.items():
            if hasattr(cache, 'redis') and cache.redis:
                try:
                    await cache.redis.close()
                    logger.info(f"   ✅ Closed {name} cache connection")
                except Exception as e:
                    logger.warning(f"   ⚠️  Error closing {name} cache: {e}")
        
        logger.info("   ✅ Cleanup complete")


# Main execution function
async def run_cache_examples():
    """
    Run the cache configuration examples.
    
    This function demonstrates various AIResponseCache configurations
    and usage patterns suitable for different environments and requirements.
    """
    examples = CacheConfigurationExamples()
    await examples.run_all_examples()


if __name__ == "__main__":
    """
    Run the cache configuration examples.
    
    Usage:
        python backend/app/examples/cache_configuration_examples.py
    
    Prerequisites:
        - Redis server running (optional - examples will demonstrate graceful degradation)
        - Dependencies installed from requirements.txt
    
    This script demonstrates practical caching patterns and is safe to run
    without modifying any persistent application data.
    """
    print("💾 Starting AIResponseCache Configuration Examples")
    print("=" * 60)
    print("This script demonstrates different cache configurations and patterns.")
    print("Redis connection is optional - examples will show graceful degradation.")
    print("=" * 60)
    
    # Check Redis availability and inform user
    if REDIS_AVAILABLE:
        print("✅ Redis client library available")
    else:
        print("⚠️  Redis client library not available - will use memory-only examples")
    
    print("\nStarting examples...\n")
    
    # Run the examples
    asyncio.run(run_cache_examples()) 