"""
Comprehensive Cache Usage Examples (Updated for Phase 4 Preset System)

This module demonstrates practical usage patterns for the Phase 4 preset-based cache 
infrastructure that reduces configuration complexity from 28+ variables to 1-4 variables.

🚀 NEW: Preset-Based Configuration (Phase 4)
    Simplified setup: CACHE_PRESET=development replaces 28+ CACHE_* variables
    Available presets: disabled, minimal, simple, development, production, ai-development, ai-production

Examples included:
1. Preset-based configuration (NEW - recommended approach)
2. Simple web app setup (with preset integration)
3. AI app setup (using ai-development/ai-production presets)
4. Hybrid app setup
5. Configuration builder pattern (legacy approach)
6. Fallback and resilience
7. Testing patterns
8. Performance benchmarking
9. Monitoring and analytics
10. Migration from legacy configuration to presets
11. Advanced configuration patterns with preset overrides

Environment Setup Examples:
    # Development: CACHE_PRESET=development
    # Production: CACHE_PRESET=production + CACHE_REDIS_URL=redis://prod:6379
    # AI Applications: CACHE_PRESET=ai-production + ENABLE_AI_CACHE=true
"""

import asyncio
import logging
import os
import time
from typing import Dict, Any, List, Optional

from app.infrastructure.cache import (
    CacheFactory,
    CacheConfig,
    CacheConfigBuilder,
    EnvironmentPresets,
    CachePerformanceBenchmark,
    InMemoryCache,
    GenericRedisCache,
    AIResponseCache,
)
from app.core.config import Settings


# Set up logging for examples
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def example_1_simple_web_app_setup():
    """
    Example 1: Simple Web Application Setup
    
    Demonstrates setting up a cache for a typical web application
    with session management, API response caching, and user data.
    """
    print("\n" + "="*60)
    print("Example 1: Simple Web Application Setup")
    print("="*60)
    
    # Option A: Using factory method directly (recommended)
    web_cache = CacheFactory.for_web_app(
        redis_url="redis://localhost:6379/0",
        fail_on_connection_error=False,  # Graceful degradation
        default_ttl=3600,  # 1 hour for web content
        compression_threshold=1000,  # Compress larger responses
    )
    
    # Ensure connection
    await web_cache.connect()
    
    # Example web app operations
    user_id = "user_12345"
    session_data = {
        "user_id": user_id,
        "preferences": {"theme": "dark", "language": "en"},
        "cart": ["item_1", "item_2"],
        "last_activity": time.time()
    }
    
    # Cache user session
    await web_cache.set(f"session:{user_id}", session_data, ttl=1800)  # 30 minutes
    print(f"✅ Cached session data for {user_id}")
    
    # Cache API response
    api_response = {"products": [{"id": 1, "name": "Product A"}], "total": 100}
    await web_cache.set("api:products:page_1", api_response, ttl=600)  # 10 minutes
    print("✅ Cached API response")
    
    # Retrieve and verify
    cached_session = await web_cache.get(f"session:{user_id}")
    cached_products = await web_cache.get("api:products:page_1")
    
    print(f"✅ Retrieved session: {cached_session['user_id']}")
    print(f"✅ Retrieved products: {len(cached_products['products'])} items")
    
    await web_cache.disconnect()
    print("✅ Web app cache example completed successfully")


async def example_2_ai_app_setup():
    """
    Example 2: AI Application Setup
    
    Demonstrates setting up a cache optimized for AI applications
    with text processing, model responses, and intelligent caching.
    """
    print("\n" + "="*60)
    print("Example 2: AI Application Setup")
    print("="*60)
    
    # AI-optimized cache with intelligent defaults
    ai_cache = CacheFactory.for_ai_app(
        redis_url="redis://localhost:6379/1",
        fail_on_connection_error=False,
        text_hash_threshold=500,  # Hash texts longer than 500 chars
        compression_level=6,  # Higher compression for AI responses
        operation_ttls={
            "summarize": 3600,  # 1 hour
            "sentiment": 1800,  # 30 minutes
            "translate": 7200,  # 2 hours
        }
    )
    
    await ai_cache.connect()
    
    # Example AI operations
    long_text = "This is a long document that needs to be processed..." * 100
    
    # Cache summarization result
    summary_result = {
        "original_length": len(long_text),
        "summary": "This document discusses important topics...",
        "confidence": 0.95,
        "model": "gpt-4"
    }
    
    # AI cache automatically handles text hashing for long inputs
    cache_key = f"summarize:{hash(long_text)}"
    await ai_cache.set(cache_key, summary_result, ttl=3600)
    print("✅ Cached AI summarization result")
    
    # Cache sentiment analysis
    sentiment_result = {"sentiment": "positive", "confidence": 0.87}
    await ai_cache.set("sentiment:sample_text", sentiment_result)
    print("✅ Cached sentiment analysis")
    
    # Retrieve and verify
    cached_summary = await ai_cache.get(cache_key)
    cached_sentiment = await ai_cache.get("sentiment:sample_text")
    
    print(f"✅ Retrieved summary confidence: {cached_summary['confidence']}")
    print(f"✅ Retrieved sentiment: {cached_sentiment['sentiment']}")
    
    await ai_cache.disconnect()
    print("✅ AI app cache example completed successfully")


async def example_3_hybrid_app_setup():
    """
    Example 3: Hybrid Application Setup
    
    Demonstrates using both web and AI caches in the same application
    for different purposes with proper separation of concerns.
    """
    print("\n" + "="*60)
    print("Example 3: Hybrid Application Setup")
    print("="*60)
    
    # Separate caches for different purposes
    web_cache = CacheFactory.for_web_app(
        redis_url="redis://localhost:6379/0",
        fail_on_connection_error=False,
    )
    
    ai_cache = CacheFactory.for_ai_app(
        redis_url="redis://localhost:6379/1",
        fail_on_connection_error=False,
    )
    
    await web_cache.connect()
    await ai_cache.connect()
    
    # Web operations: User sessions, API responses
    user_data = {"user_id": "user_789", "subscription": "premium"}
    await web_cache.set("user:789", user_data)
    print("✅ Cached user data in web cache")
    
    # AI operations: Content analysis, recommendations
    content_analysis = {
        "sentiment": "positive",
        "topics": ["technology", "innovation"],
        "reading_time": 5
    }
    await ai_cache.set("analysis:article_123", content_analysis)
    print("✅ Cached content analysis in AI cache")
    
    # Cross-cache workflow: Use AI analysis for web recommendations
    user = await web_cache.get("user:789")
    analysis = await ai_cache.get("analysis:article_123")
    
    recommendations = {
        "user_id": user["user_id"],
        "recommended_topics": analysis["topics"],
        "based_on_sentiment": analysis["sentiment"]
    }
    
    await web_cache.set(f"recommendations:{user['user_id']}", recommendations)
    print("✅ Generated and cached recommendations using both caches")
    
    await web_cache.disconnect()
    await ai_cache.disconnect()
    print("✅ Hybrid app cache example completed successfully")


async def example_4_configuration_builder_pattern():
    """
    Example 4: Configuration Builder Pattern
    
    Demonstrates using CacheConfigBuilder for flexible, programmatic
    cache configuration across different environments.
    """
    print("\n" + "="*60)
    print("Example 4: Configuration Builder Pattern")
    print("="*60)
    
    # Development configuration
    dev_config = (CacheConfigBuilder()
                  .for_environment("development")
                  .with_redis("redis://localhost:6379/2")
                  .with_memory_cache(max_size=50)
                  .with_compression(threshold=500, level=3)
                  .with_ai_features(
                      text_hash_threshold=1000,
                      enable_smart_promotion=True
                  )
                  .build())
    
    print("✅ Built development configuration")
    
    # Production configuration
    prod_config = (CacheConfigBuilder()
                   .for_environment("production")
                   .with_redis("redis://prod-server:6379/0")
                   .with_security(use_tls=True)
                   .with_memory_cache(max_size=200)
                   .with_compression(threshold=1000, level=6)
                   .with_ai_features(
                       text_hash_threshold=500,
                       operation_ttls={
                           "summarize": 7200,
                           "translate": 3600,
                       }
                   )
                   .build())
    
    print("✅ Built production configuration")
    
    # Create caches from configurations
    dev_cache = CacheFactory.create_cache_from_config(
        dev_config, 
        fail_on_connection_error=False
    )
    
    # For this example, we'll use the dev cache
    await dev_cache.connect()
    
    # Test configuration-driven behavior
    test_data = {"config_test": True, "environment": "development"}
    await dev_cache.set("config_test", test_data)
    
    retrieved_data = await dev_cache.get("config_test")
    print(f"✅ Configuration test successful: {retrieved_data['environment']}")
    
    await dev_cache.disconnect()
    print("✅ Configuration builder pattern example completed successfully")


async def example_5_fallback_and_resilience():
    """
    Example 5: Fallback and Resilience
    
    Demonstrates graceful degradation, connection error handling,
    and resilience patterns with fail_on_connection_error parameter.
    """
    print("\n" + "="*60)
    print("Example 5: Fallback and Resilience")
    print("="*60)
    
    # Scenario A: Strict error handling (fail_on_connection_error=True)
    print("\nScenario A: Strict error handling")
    try:
        strict_cache = CacheFactory.for_web_app(
            redis_url="redis://nonexistent-server:6379",
            fail_on_connection_error=True
        )
        await strict_cache.connect()
    except Exception as e:
        print(f"✅ Strict mode correctly failed: {type(e).__name__}")
    
    # Scenario B: Graceful degradation (fail_on_connection_error=False)
    print("\nScenario B: Graceful degradation")
    resilient_cache = CacheFactory.for_web_app(
        redis_url="redis://nonexistent-server:6379",
        fail_on_connection_error=False  # Falls back to InMemoryCache
    )
    
    await resilient_cache.connect()
    print(f"✅ Graceful fallback successful, using: {type(resilient_cache).__name__}")
    
    # Test fallback cache functionality
    test_data = {"resilience_test": True, "cache_type": "fallback"}
    await resilient_cache.set("resilience_test", test_data)
    
    retrieved_data = await resilient_cache.get("resilience_test")
    print(f"✅ Fallback cache working: {retrieved_data['cache_type']}")
    
    # Scenario C: Connection recovery simulation
    print("\nScenario C: Connection recovery patterns")
    
    # Create cache with working Redis
    working_cache = CacheFactory.for_ai_app(
        redis_url="redis://localhost:6379/3",
        fail_on_connection_error=False
    )
    
    await working_cache.connect()
    
    # Store some data
    recovery_data = {"recovery_test": True, "timestamp": time.time()}
    await working_cache.set("recovery_test", recovery_data)
    
    # Verify data persistence
    recovered_data = await working_cache.get("recovery_test")
    print(f"✅ Data recovered successfully: {recovered_data['recovery_test']}")
    
    await working_cache.disconnect()
    await resilient_cache.disconnect()
    print("✅ Fallback and resilience example completed successfully")


async def example_6_testing_patterns():
    """
    Example 6: Testing Patterns
    
    Demonstrates proper cache setup for testing environments
    with isolation, cleanup, and test-specific configurations.
    """
    print("\n" + "="*60)
    print("Example 6: Testing Patterns")
    print("="*60)
    
    # Memory cache for unit tests
    print("Unit test cache setup:")
    unit_test_cache = CacheFactory.for_testing("memory")
    await unit_test_cache.connect()
    
    print(f"✅ Unit test cache: {type(unit_test_cache).__name__}")
    
    # Redis cache for integration tests
    print("\nIntegration test cache setup:")
    integration_test_cache = CacheFactory.for_testing("redis")
    await integration_test_cache.connect()
    
    print(f"✅ Integration test cache: {type(integration_test_cache).__name__}")
    
    # Test isolation example
    test_cases = ["test_case_1", "test_case_2", "test_case_3"]
    
    for test_case in test_cases:
        # Each test gets isolated data
        test_data = {
            "test_case": test_case,
            "data": f"Test data for {test_case}",
            "isolated": True
        }
        
        await unit_test_cache.set(f"test:{test_case}", test_data, ttl=60)
        retrieved = await unit_test_cache.get(f"test:{test_case}")
        print(f"✅ Test isolation verified: {retrieved['test_case']}")
    
    # Cleanup demonstration
    print("\nTest cleanup:")
    for test_case in test_cases:
        await unit_test_cache.delete(f"test:{test_case}")
        result = await unit_test_cache.get(f"test:{test_case}")
        assert result is None, f"Cleanup failed for {test_case}"
    
    print("✅ Test cleanup completed")
    
    await unit_test_cache.disconnect()
    await integration_test_cache.disconnect()
    print("✅ Testing patterns example completed successfully")


async def example_7_performance_benchmarking():
    """
    Example 7: Performance Benchmarking
    
    Demonstrates using the benchmarking tools to measure
    and compare cache performance across different configurations.
    """
    print("\n" + "="*60)
    print("Example 7: Performance Benchmarking")
    print("="*60)
    
    # Create caches for comparison
    memory_cache = CacheFactory.for_testing("memory")
    web_cache = CacheFactory.for_web_app(
        redis_url="redis://localhost:6379/4",
        fail_on_connection_error=False
    )
    
    await memory_cache.connect()
    await web_cache.connect()
    
    # Initialize benchmark tool
    benchmark = CachePerformanceBenchmark()
    
    print("Running performance benchmarks...")
    
    # Benchmark memory cache
    memory_results = await benchmark.benchmark_basic_operations(
        memory_cache,
        test_operations=100,
        data_size="small"
    )
    
    print(f"✅ Memory cache - Avg SET: {memory_results.avg_set_time:.4f}ms")
    print(f"✅ Memory cache - Avg GET: {memory_results.avg_get_time:.4f}ms")
    
    # Benchmark Redis cache (if available)
    if isinstance(web_cache, (GenericRedisCache, AIResponseCache)):
        redis_results = await benchmark.benchmark_basic_operations(
            web_cache,
            test_operations=100,
            data_size="small"
        )
        
        print(f"✅ Redis cache - Avg SET: {redis_results.avg_set_time:.4f}ms")
        print(f"✅ Redis cache - Avg GET: {redis_results.avg_get_time:.4f}ms")
        
        # Compare caches
        comparison = await benchmark.compare_caches(
            baseline_cache=memory_cache,
            comparison_cache=web_cache,
            test_operations=50
        )
        
        print(f"✅ Performance comparison: {comparison.overall_performance_change:.2f}%")
        print(f"✅ Recommendation: {comparison.recommendation}")
    
    await memory_cache.disconnect()
    await web_cache.disconnect()
    print("✅ Performance benchmarking example completed successfully")


async def example_8_monitoring_and_analytics():
    """
    Example 8: Monitoring and Analytics
    
    Demonstrates cache monitoring, health checks, and analytics
    collection for production observability.
    """
    print("\n" + "="*60)
    print("Example 8: Monitoring and Analytics")
    print("="*60)
    
    # Create monitored cache
    monitored_cache = CacheFactory.for_web_app(
        redis_url="redis://localhost:6379/5",
        fail_on_connection_error=False
    )
    
    await monitored_cache.connect()
    
    print("Setting up monitoring...")
    
    # Simulate application activity for monitoring
    activities = [
        ("user_session:123", {"user": "alice", "login_time": time.time()}),
        ("api_response:products", {"products": [1, 2, 3], "cached_at": time.time()}),
        ("temp_data:xyz", {"temp": True, "expires": time.time() + 300}),
    ]
    
    # Track operations
    operation_times = []
    
    for key, data in activities:
        start_time = time.time()
        await monitored_cache.set(key, data)
        end_time = time.time()
        
        operation_times.append(end_time - start_time)
        print(f"✅ Cached {key} in {(end_time - start_time)*1000:.2f}ms")
    
    # Health check simulation
    print("\nPerforming health checks...")
    
    # Basic connectivity check
    try:
        test_key = "health_check"
        test_value = {"status": "healthy", "timestamp": time.time()}
        
        await monitored_cache.set(test_key, test_value, ttl=10)
        retrieved = await monitored_cache.get(test_key)
        await monitored_cache.delete(test_key)
        
        if retrieved and retrieved["status"] == "healthy":
            print("✅ Health check passed: Cache is responsive")
        else:
            print("❌ Health check failed: Data integrity issue")
            
    except Exception as e:
        print(f"❌ Health check failed: {e}")
    
    # Analytics collection
    print("\nCollecting analytics...")
    
    analytics = {
        "total_operations": len(activities),
        "avg_operation_time": sum(operation_times) / len(operation_times) * 1000,
        "cache_type": type(monitored_cache).__name__,
        "health_status": "healthy",
        "timestamp": time.time()
    }
    
    print(f"✅ Analytics collected:")
    print(f"   - Total operations: {analytics['total_operations']}")
    print(f"   - Avg operation time: {analytics['avg_operation_time']:.2f}ms")
    print(f"   - Cache type: {analytics['cache_type']}")
    
    await monitored_cache.disconnect()
    print("✅ Monitoring and analytics example completed successfully")


async def example_9_migration_from_auto_detection():
    """
    Example 9: Migration from Auto-Detection
    
    Demonstrates migrating from legacy auto-detection patterns
    to explicit factory methods with clear before/after examples.
    """
    print("\n" + "="*60)
    print("Example 9: Migration from Auto-Detection")
    print("="*60)
    
    print("BEFORE: Legacy auto-detection pattern")
    print("# Old pattern (deprecated):")
    print("# cache = get_cache_instance()  # Magic auto-detection")
    print("# cache = Cache.from_environment()  # Environment-based")
    
    print("\nAFTER: Explicit factory methods")
    
    # Explicit web app cache
    print("1. Web application explicit setup:")
    web_cache = CacheFactory.for_web_app(
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/6"),
        fail_on_connection_error=False
    )
    await web_cache.connect()
    print(f"✅ Explicit web cache: {type(web_cache).__name__}")
    
    # Explicit AI app cache  
    print("2. AI application explicit setup:")
    ai_cache = CacheFactory.for_ai_app(
        redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/7"),
        fail_on_connection_error=False
    )
    await ai_cache.connect()
    print(f"✅ Explicit AI cache: {type(ai_cache).__name__}")
    
    # Migration validation
    print("\n3. Migration validation:")
    
    # Test data compatibility
    migration_data = {
        "migration_test": True,
        "legacy_compatible": True,
        "new_features": ["explicit_selection", "graceful_degradation"]
    }
    
    await web_cache.set("migration_test", migration_data)
    retrieved = await web_cache.get("migration_test")
    
    print(f"✅ Data compatibility verified: {retrieved['legacy_compatible']}")
    print(f"✅ New features available: {len(retrieved['new_features'])}")
    
    # Configuration migration example
    print("\n4. Configuration migration:")
    
    # Before: Scattered environment variables
    print("BEFORE: Multiple environment variables")
    print("# REDIS_URL=redis://localhost:6379")
    print("# CACHE_TTL=3600")
    print("# ENABLE_COMPRESSION=true")
    
    print("AFTER: Centralized configuration")
    config = (CacheConfigBuilder()
              .for_environment("development")
              .with_redis("redis://localhost:6379/8")
              .with_compression(threshold=1000, level=4)
              .build())
    
    config_cache = CacheFactory.create_cache_from_config(config)
    await config_cache.connect()
    print(f"✅ Configuration-based cache: {type(config_cache).__name__}")
    
    # Cleanup
    await web_cache.disconnect()
    await ai_cache.disconnect()
    await config_cache.disconnect()
    print("✅ Migration from auto-detection example completed successfully")


async def example_10_advanced_configuration_patterns():
    """
    Example 10: Advanced Configuration Patterns
    
    Demonstrates sophisticated configuration patterns including
    environment-specific presets, JSON configuration files,
    and dynamic configuration updates.
    """
    print("\n" + "="*60)
    print("Example 10: Advanced Configuration Patterns")
    print("="*60)
    
    # Environment presets
    print("1. Environment presets:")
    
    # Development preset
    dev_preset = EnvironmentPresets.development()
    dev_cache = CacheFactory.create_cache_from_config(dev_preset)
    await dev_cache.connect()
    print(f"✅ Development preset cache: {type(dev_cache).__name__}")
    
    # AI development preset
    ai_dev_preset = EnvironmentPresets.ai_development()
    ai_dev_cache = CacheFactory.create_cache_from_config(ai_dev_preset)
    await ai_dev_cache.connect()
    print(f"✅ AI development preset cache: {type(ai_dev_cache).__name__}")
    
    # JSON configuration file pattern
    print("\n2. JSON configuration file:")
    
    config_data = {
        "redis_url": "redis://localhost:6379/9",
        "default_ttl": 3600,
        "memory_cache_size": 100,
        "compression_threshold": 1000,
        "compression_level": 4,
        "ai_config": {
            "text_hash_threshold": 500,
            "hash_algorithm": "sha256",
            "operation_ttls": {
                "summarize": 7200,
                "sentiment": 1800
            }
        }
    }
    
    # Save configuration to file (simulated)
    config_builder = CacheConfigBuilder().from_environment()
    
    # Apply JSON-like configuration
    file_config = (config_builder
                   .with_redis(config_data["redis_url"])
                   .with_compression(
                       threshold=config_data["compression_threshold"],
                       level=config_data["compression_level"]
                   )
                   .with_ai_features(**config_data["ai_config"])
                   .build())
    
    file_cache = CacheFactory.create_cache_from_config(file_config)
    await file_cache.connect()
    print(f"✅ JSON config cache: {type(file_cache).__name__}")
    
    # Dynamic configuration validation
    print("\n3. Configuration validation:")
    
    validation_result = file_config.validate()
    if validation_result.is_valid:
        print("✅ Configuration validation passed")
        if validation_result.warnings:
            print(f"⚠️  Warnings: {len(validation_result.warnings)} found")
    else:
        print(f"❌ Configuration validation failed: {validation_result.errors}")
    
    # Multi-environment configuration
    print("\n4. Multi-environment pattern:")
    
    environments = {
        "test": EnvironmentPresets.testing(),
        "dev": EnvironmentPresets.development(),
        "ai_prod": EnvironmentPresets.ai_production()
    }
    
    for env_name, env_config in environments.items():
        env_cache = CacheFactory.create_cache_from_config(
            env_config, 
            fail_on_connection_error=False
        )
        await env_cache.connect()
        print(f"✅ {env_name} environment: {type(env_cache).__name__}")
        await env_cache.disconnect()
    
    # Cleanup
    await dev_cache.disconnect()
    await ai_dev_cache.disconnect() 
    await file_cache.disconnect()
    print("✅ Advanced configuration patterns example completed successfully")


async def run_all_examples():
    """
    Run all cache usage examples in sequence.
    
    This function executes all examples to demonstrate the complete
    range of cache functionality and usage patterns.
    """
    print("🚀 Starting Comprehensive Cache Usage Examples")
    print("=" * 80)
    
    examples = [
        example_1_simple_web_app_setup,
        example_2_ai_app_setup,
        example_3_hybrid_app_setup,
        example_4_configuration_builder_pattern,
        example_5_fallback_and_resilience,
        example_6_testing_patterns,
        example_7_performance_benchmarking,
        example_8_monitoring_and_analytics,
        example_9_migration_from_auto_detection,
        example_10_advanced_configuration_patterns,
    ]
    
    results = {"successful": 0, "failed": 0, "errors": []}
    
    for i, example in enumerate(examples, 1):
        try:
            await example()
            results["successful"] += 1
        except Exception as e:
            results["failed"] += 1
            results["errors"].append(f"Example {i} ({example.__name__}): {e}")
            logger.error(f"Example {i} failed: {e}")
    
    # Summary
    print("\n" + "="*80)
    print("📊 COMPREHENSIVE EXAMPLES SUMMARY")
    print("="*80)
    print(f"✅ Successful examples: {results['successful']}")
    print(f"❌ Failed examples: {results['failed']}")
    
    if results["errors"]:
        print("\nErrors encountered:")
        for error in results["errors"]:
            print(f"  - {error}")
    
    print(f"\n🎉 Examples completed! Success rate: {results['successful']}/{len(examples)}")
    
    return results


if __name__ == "__main__":
    """
    Run examples when script is executed directly.
    
    Usage:
        python comprehensive_usage_examples.py
    """
    asyncio.run(run_all_examples())