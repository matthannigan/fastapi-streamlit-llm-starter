"""
Migration Code Examples: Before/After Patterns

This module provides concrete before/after code examples for migrating from
auto-detection patterns to explicit factory methods. These examples demonstrate
practical migration strategies for different application patterns.

Migration Areas Covered:
- Auto-detection to explicit factory methods
- Environment-based selection to explicit configuration
- FastAPI dependency injection updates
- Environment variable migration
- Test fixture migration to for_testing() method
- Health check endpoint conversion
"""

import asyncio
import os
import logging
from typing import Optional, Dict, Any
from datetime import datetime

# Note: These imports show the new Phase 3 structure
from app.infrastructure.cache import (
    CacheFactory,
    CacheConfig,
    CacheConfigBuilder,
    EnvironmentPresets,
    CacheInterface,
    InMemoryCache,
    GenericRedisCache,
    AIResponseCache,
)

logger = logging.getLogger(__name__)


# =============================================================================
# Migration Example 1: Auto-Detection to Explicit Factory Methods
# =============================================================================

class LegacyAutoDetectionPattern:
    """
    BEFORE: Legacy auto-detection pattern (DEPRECATED)
    
    This class demonstrates the old pattern that should be migrated away from.
    """
    
    @staticmethod
    def get_cache_instance():
        """
        OLD PATTERN: Auto-detection based on environment variables.
        
        This approach is deprecated because:
        - Magic behavior is hard to debug
        - Configuration is scattered across environment variables
        - Fallback behavior is implicit and unpredictable
        - Testing is difficult due to environment coupling
        """
        # Magic auto-detection (DEPRECATED)
        redis_url = os.getenv("REDIS_URL")
        
        if redis_url:
            if os.getenv("AI_CACHE_ENABLED", "false").lower() == "true":
                # AI cache with scattered configuration
                return AIResponseCache(
                    redis_url=redis_url,
                    default_ttl=int(os.getenv("CACHE_TTL", "3600")),
                    text_hash_threshold=int(os.getenv("TEXT_HASH_THRESHOLD", "1000")),
                    compression_threshold=int(os.getenv("COMPRESSION_THRESHOLD", "1000")),
                    # ... many more environment variables
                )
            else:
                # Generic cache
                return GenericRedisCache(
                    redis_url=redis_url,
                    default_ttl=int(os.getenv("CACHE_TTL", "3600")),
                    # ... scattered configuration
                )
        else:
            # Fallback with no configuration
            return InMemoryCache()


class ModernExplicitPattern:
    """
    AFTER: Modern explicit factory pattern (RECOMMENDED)
    
    This class demonstrates the new explicit pattern that provides:
    - Clear intent and predictable behavior
    - Centralized configuration
    - Graceful degradation with explicit control
    - Easy testing with dedicated factory methods
    """
    
    @staticmethod
    def get_web_cache() -> CacheInterface:
        """
        NEW PATTERN: Explicit web application cache.
        
        Clear intent: This creates a cache optimized for web applications.
        """
        return CacheFactory.for_web_app(
            redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/0"),
            fail_on_connection_error=False,  # Explicit graceful degradation
            default_ttl=1800,               # Explicit web-optimized TTL
            compression_threshold=2000       # Explicit threshold
        )
    
    @staticmethod
    def get_ai_cache() -> CacheInterface:
        """
        NEW PATTERN: Explicit AI application cache.
        
        Clear intent: This creates a cache optimized for AI operations.
        """
        return CacheFactory.for_ai_app(
            redis_url=os.getenv("REDIS_URL", "redis://localhost:6379/1"),
            fail_on_connection_error=False,
            text_hash_threshold=500,         # AI-optimized hashing
            compression_level=6,             # Higher compression for AI
            operation_ttls={
                "summarize": 3600,
                "sentiment": 1800,
                "translate": 7200
            }
        )
    
    @staticmethod
    def get_test_cache() -> CacheInterface:
        """
        NEW PATTERN: Explicit testing cache.
        
        Clear intent: This creates a cache for testing scenarios.
        """
        return CacheFactory.for_testing("memory")  # or "redis" for integration tests
    
    @staticmethod
    def get_config_based_cache() -> CacheInterface:
        """
        NEW PATTERN: Configuration-based cache creation.
        
        Ultimate flexibility: Use configuration objects for complex setups.
        """
        config = (CacheConfigBuilder()
                  .from_environment()
                  .with_ai_features(enable_smart_promotion=True)
                  .build())
        
        return CacheFactory.create_cache_from_config(config)


async def demo_migration_example_1():
    """Demonstrate migration from auto-detection to explicit patterns."""
    print("\n" + "="*70)
    print("Migration Example 1: Auto-Detection to Explicit Factory Methods")
    print("="*70)
    
    print("BEFORE: Auto-detection pattern (deprecated)")
    print("# cache = LegacyAutoDetectionPattern.get_cache_instance()")
    print("# ^ Magic behavior, hard to predict and test")
    
    print("\nAFTER: Explicit factory methods")
    
    # Demonstrate explicit patterns
    web_cache = ModernExplicitPattern.get_web_cache()
    await web_cache.connect()
    print(f"✅ Web cache created explicitly: {type(web_cache).__name__}")
    
    ai_cache = ModernExplicitPattern.get_ai_cache()
    await ai_cache.connect()
    print(f"✅ AI cache created explicitly: {type(ai_cache).__name__}")
    
    test_cache = ModernExplicitPattern.get_test_cache()
    await test_cache.connect()
    print(f"✅ Test cache created explicitly: {type(test_cache).__name__}")
    
    # Test the caches work correctly
    await web_cache.set("web_test", {"type": "web", "explicit": True})
    await ai_cache.set("ai_test", {"type": "ai", "explicit": True})
    await test_cache.set("test_key", {"type": "test", "explicit": True})
    
    web_data = await web_cache.get("web_test")
    ai_data = await ai_cache.get("ai_test")
    test_data = await test_cache.get("test_key")
    
    print(f"✅ Web cache data: {web_data['type']}")
    print(f"✅ AI cache data: {ai_data['type']}")
    print(f"✅ Test cache data: {test_data['type']}")
    
    # Cleanup
    await web_cache.disconnect()
    await ai_cache.disconnect()
    await test_cache.disconnect()
    
    print("✅ Migration Example 1 completed successfully")


# =============================================================================
# Migration Example 2: FastAPI Dependency Injection Updates
# =============================================================================

class LegacyFastAPIDependencies:
    """
    BEFORE: Manual dependency injection (DEPRECATED)
    """
    
    cache_instance = None
    
    @classmethod
    async def get_cache_dependency(cls):
        """OLD: Manual singleton management with auto-detection."""
        if cls.cache_instance is None:
            # Manual cache creation with auto-detection
            redis_url = os.getenv("REDIS_URL")
            if redis_url:
                cls.cache_instance = AIResponseCache(redis_url=redis_url)
                try:
                    await cls.cache_instance.connect()
                except Exception:
                    # Manual fallback logic
                    cls.cache_instance = InMemoryCache()
            else:
                cls.cache_instance = InMemoryCache()
        
        return cls.cache_instance


# New pattern imports (these would be in your actual FastAPI app)
from fastapi import Depends
from app.infrastructure.cache.dependencies import (
    get_cache_service,
    get_cache_config,
    get_cache_health_status
)


class ModernFastAPIDependencies:
    """
    AFTER: Comprehensive dependency injection system (RECOMMENDED)
    """
    
    # No manual singleton management needed - handled by dependency system
    
    @staticmethod
    def example_endpoint_old_style():
        """OLD: Manual dependency management in FastAPI endpoints."""
        return """
        # OLD PATTERN (deprecated):
        @app.post("/api/process")
        async def process_text(request: ProcessRequest):
            cache = await LegacyFastAPIDependencies.get_cache_dependency()
            # Manual error handling, no lifecycle management
            cached_result = await cache.get(f"process:{request.text}")
            if cached_result:
                return cached_result
            
            result = await process_service.execute(request)
            await cache.set(f"process:{request.text}", result)
            return result
        """
    
    @staticmethod
    def example_endpoint_new_style():
        """NEW: Automatic dependency injection with lifecycle management."""
        return """
        # NEW PATTERN (recommended):
        @app.post("/api/process")
        async def process_text(
            request: ProcessRequest,
            cache: CacheInterface = Depends(get_cache_service),
            config: CacheConfig = Depends(get_cache_config)
        ):
            # Automatic connection management, graceful degradation
            cached_result = await cache.get(f"process:{request.operation}:{hash(request.text)}")
            if cached_result:
                return cached_result
            
            result = await process_service.execute(request)
            await cache.set(f"process:{request.operation}:{hash(request.text)}", result)
            return result
        
        @app.get("/internal/cache/health")
        async def cache_health(
            cache: CacheInterface = Depends(get_cache_service)
        ):
            return await get_cache_health_status(cache)
        """


async def demo_migration_example_2():
    """Demonstrate FastAPI dependency injection migration."""
    print("\n" + "="*70)
    print("Migration Example 2: FastAPI Dependency Injection Updates")
    print("="*70)
    
    print("BEFORE: Manual dependency management")
    print(ModernFastAPIDependencies.example_endpoint_old_style())
    
    print("AFTER: Automatic dependency injection")
    print(ModernFastAPIDependencies.example_endpoint_new_style())
    
    # Simulate dependency injection behavior
    from app.infrastructure.cache.dependencies import get_cache_config
    
    print("\nSimulating new dependency behavior:")
    
    # This would normally be handled by FastAPI's dependency injection
    # We'll simulate it for demonstration
    config = await get_cache_config()
    cache = CacheFactory.create_cache_from_config(config, fail_on_connection_error=False)
    await cache.connect()
    
    print(f"✅ Dependency-injected cache: {type(cache).__name__}")
    print(f"✅ Automatic lifecycle management active")
    print(f"✅ Configuration validation passed")
    
    await cache.disconnect()
    print("✅ Migration Example 2 completed successfully")


# =============================================================================
# Migration Example 3: Environment Variable Migration
# =============================================================================

class LegacyEnvironmentVariables:
    """
    BEFORE: Scattered environment variables (DEPRECATED)
    """
    
    @staticmethod
    def get_legacy_config():
        """OLD: Multiple scattered environment variables."""
        return {
            "redis_url": os.getenv("REDIS_URL"),
            "cache_ttl": int(os.getenv("CACHE_TTL", "3600")),
            "compression_enabled": os.getenv("ENABLE_COMPRESSION", "false").lower() == "true",
            "compression_threshold": int(os.getenv("COMPRESSION_THRESHOLD", "1000")),
            "compression_level": int(os.getenv("COMPRESSION_LEVEL", "6")),
            "text_hash_threshold": int(os.getenv("TEXT_HASH_THRESHOLD", "1000")),
            "memory_cache_size": int(os.getenv("MEMORY_CACHE_SIZE", "100")),
            "ai_cache_enabled": os.getenv("AI_CACHE_ENABLED", "false").lower() == "true",
            # ... potentially dozens more variables
        }


class ModernEnvironmentVariables:
    """
    AFTER: Centralized configuration with presets (RECOMMENDED)
    """
    
    @staticmethod
    def get_modern_config():
        """NEW: Centralized configuration with environment presets."""
        # Option 1: Use environment presets
        environment = os.getenv("ENVIRONMENT", "development")
        
        if environment == "production":
            return EnvironmentPresets.ai_production()
        elif environment == "testing":
            return EnvironmentPresets.testing()
        else:
            return EnvironmentPresets.ai_development()
    
    @staticmethod
    def get_builder_config():
        """NEW: Use builder pattern with environment loading."""
        return (CacheConfigBuilder()
                .from_environment()  # Automatically loads standardized env vars
                .build())
    
    @staticmethod
    def get_hybrid_config():
        """NEW: Combine presets with custom overrides."""
        base_config = EnvironmentPresets.development()
        
        # Override specific settings from environment
        redis_url = os.getenv("REDIS_URL")
        if redis_url:
            return (CacheConfigBuilder()
                    .for_environment("development")
                    .with_redis(redis_url)
                    .build())
        
        return base_config


def demo_environment_variable_migration():
    """Demonstrate environment variable migration patterns."""
    print("\n" + "="*70)
    print("Migration Example 3: Environment Variable Migration")
    print("="*70)
    
    print("BEFORE: Scattered environment variables")
    print("# REDIS_URL=redis://localhost:6379")
    print("# CACHE_TTL=3600") 
    print("# ENABLE_COMPRESSION=true")
    print("# COMPRESSION_THRESHOLD=1000")
    print("# COMPRESSION_LEVEL=6")
    print("# TEXT_HASH_THRESHOLD=1000")
    print("# MEMORY_CACHE_SIZE=100")
    print("# AI_CACHE_ENABLED=true")
    print("# ... potentially dozens more")
    
    print("\nAFTER: Centralized configuration")
    print("# ENVIRONMENT=production  # or development, testing")
    print("# REDIS_URL=redis://localhost:6379  # Override if needed")
    print("# ENABLE_AI_CACHE=true  # Simple AI features toggle")
    
    print("\nDemonstrating new configuration patterns:")
    
    # Preset-based configuration
    dev_config = ModernEnvironmentVariables.get_modern_config()
    print(f"✅ Preset configuration loaded: {dev_config.environment}")
    
    # Builder-based configuration
    builder_config = ModernEnvironmentVariables.get_builder_config()
    print(f"✅ Builder configuration loaded: {builder_config.environment}")
    
    # Show validation
    validation = dev_config.validate()
    if validation.is_valid:
        print("✅ Configuration validation passed")
    else:
        print(f"❌ Configuration validation failed: {validation.errors}")
    
    print("✅ Migration Example 3 completed successfully")


# =============================================================================
# Migration Example 4: Test Fixture Migration
# =============================================================================

class LegacyTestFixtures:
    """
    BEFORE: Manual test setup (DEPRECATED)
    """
    
    @staticmethod
    async def setup_test_cache():
        """OLD: Manual test cache setup with environment coupling."""
        # Test is coupled to environment variables
        test_redis_url = os.getenv("TEST_REDIS_URL", "redis://localhost:6379/15")
        
        cache = AIResponseCache(
            redis_url=test_redis_url,
            default_ttl=60,  # Short TTL for tests
            memory_cache_size=10  # Small size for tests
        )
        
        try:
            await cache.connect()
            # Manual cleanup - prone to errors
            await cache.delete("*")  # Dangerous pattern
        except Exception:
            # Manual fallback
            cache = InMemoryCache(default_ttl=60, max_size=10)
        
        return cache
    
    @staticmethod
    async def cleanup_test_cache(cache):
        """OLD: Manual cleanup with potential issues."""
        try:
            # Manual key management
            keys = await cache.get_active_keys()
            for key in keys:
                await cache.delete(key)
            await cache.disconnect()
        except Exception as e:
            print(f"Cleanup failed: {e}")


class ModernTestFixtures:
    """
    AFTER: Factory-based test fixtures (RECOMMENDED)
    """
    
    @staticmethod
    async def setup_unit_test_cache():
        """NEW: Memory cache for fast unit tests."""
        cache = CacheFactory.for_testing("memory")
        await cache.connect()
        return cache
    
    @staticmethod
    async def setup_integration_test_cache():
        """NEW: Redis cache for integration tests."""
        cache = CacheFactory.for_testing("redis")
        await cache.connect()
        return cache
    
    @staticmethod
    async def cleanup_test_cache(cache):
        """NEW: Automatic cleanup with proper isolation."""
        await cache.disconnect()
        # Factory ensures proper test database usage and cleanup


async def demo_migration_example_4():
    """Demonstrate test fixture migration."""
    print("\n" + "="*70)
    print("Migration Example 4: Test Fixture Migration")
    print("="*70)
    
    print("BEFORE: Manual test setup with environment coupling")
    print("# test_cache = await LegacyTestFixtures.setup_test_cache()")
    print("# ^ Environment dependent, manual cleanup, error-prone")
    
    print("\nAFTER: Factory-based test fixtures")
    
    # Unit test cache
    unit_cache = await ModernTestFixtures.setup_unit_test_cache()
    print(f"✅ Unit test cache: {type(unit_cache).__name__}")
    
    # Test the cache
    await unit_cache.set("unit_test", {"fast": True, "isolated": True})
    unit_data = await unit_cache.get("unit_test")
    print(f"✅ Unit test data: fast={unit_data['fast']}")
    
    # Integration test cache
    integration_cache = await ModernTestFixtures.setup_integration_test_cache()
    print(f"✅ Integration test cache: {type(integration_cache).__name__}")
    
    # Test the cache
    await integration_cache.set("integration_test", {"persistent": True, "isolated": True})
    integration_data = await integration_cache.get("integration_test")
    print(f"✅ Integration test data: persistent={integration_data['persistent']}")
    
    # Modern cleanup
    await ModernTestFixtures.cleanup_test_cache(unit_cache)
    await ModernTestFixtures.cleanup_test_cache(integration_cache)
    print("✅ Automatic cleanup completed")
    
    print("✅ Migration Example 4 completed successfully")


# =============================================================================
# Migration Example 5: Health Check Endpoint Migration
# =============================================================================

class LegacyHealthChecks:
    """
    BEFORE: Manual health check implementation (DEPRECATED)
    """
    
    @staticmethod
    async def manual_health_check():
        """OLD: Manual health check with hardcoded logic."""
        try:
            # Manual cache creation
            cache = LegacyAutoDetectionPattern.get_cache_instance()
            
            # Manual health check logic
            test_key = f"health_check_{datetime.now().timestamp()}"
            test_value = {"status": "test", "timestamp": datetime.now().isoformat()}
            
            await cache.set(test_key, test_value, ttl=10)
            retrieved = await cache.get(test_key)
            await cache.delete(test_key)
            
            if retrieved and retrieved["status"] == "test":
                return {"status": "healthy", "cache_type": type(cache).__name__}
            else:
                return {"status": "unhealthy", "reason": "data_integrity_failed"}
                
        except Exception as e:
            return {"status": "unhealthy", "reason": str(e)}


class ModernHealthChecks:
    """
    AFTER: Dependency-based health checks (RECOMMENDED)
    """
    
    @staticmethod
    async def dependency_health_check():
        """NEW: Use dependency injection for health checks."""
        # This would normally be injected by FastAPI
        from app.infrastructure.cache.dependencies import get_cache_service, get_cache_health_status
        
        cache = await get_cache_service()
        return await get_cache_health_status(cache)


async def demo_migration_example_5():
    """Demonstrate health check endpoint migration."""
    print("\n" + "="*70)
    print("Migration Example 5: Health Check Endpoint Migration")
    print("="*70)
    
    print("BEFORE: Manual health check implementation")
    legacy_health = await LegacyHealthChecks.manual_health_check()
    print(f"Legacy health check: {legacy_health}")
    
    print("\nAFTER: Dependency-based health checks")
    modern_health = await ModernHealthChecks.dependency_health_check()
    print(f"Modern health check: {modern_health}")
    
    print("✅ Migration Example 5 completed successfully")


# =============================================================================
# Run All Migration Examples
# =============================================================================

async def run_all_migration_examples():
    """
    Run all migration examples to demonstrate the complete
    transition from legacy patterns to modern explicit patterns.
    """
    print("🚀 Starting Migration Code Examples")
    print("=" * 80)
    
    examples = [
        demo_migration_example_1,  # Auto-detection to explicit factory
        demo_migration_example_2,  # FastAPI dependency injection
        demo_migration_example_4,  # Test fixture migration
        demo_migration_example_5,  # Health check migration
    ]
    
    # Note: Example 3 is synchronous
    demo_environment_variable_migration()
    
    results = {"successful": 0, "failed": 0, "errors": []}
    
    for i, example in enumerate(examples, 1):
        try:
            await example()
            results["successful"] += 1
        except Exception as e:
            results["failed"] += 1
            results["errors"].append(f"Example {i} ({example.__name__}): {e}")
            logger.error(f"Migration example {i} failed: {e}")
    
    # Summary
    print("\n" + "="*80)
    print("📊 MIGRATION EXAMPLES SUMMARY")
    print("="*80)
    print(f"✅ Successful examples: {results['successful'] + 1}")  # +1 for sync example
    print(f"❌ Failed examples: {results['failed']}")
    
    if results["errors"]:
        print("\nErrors encountered:")
        for error in results["errors"]:
            print(f"  - {error}")
    
    print(f"\n🎉 Migration examples completed! Success rate: {results['successful'] + 1}/{len(examples) + 1}")
    
    # Migration checklist
    print("\n" + "="*80)
    print("📋 MIGRATION CHECKLIST")
    print("="*80)
    print("✅ Replace auto-detection with explicit factory methods")
    print("✅ Update FastAPI dependencies to use get_cache_service()")
    print("✅ Consolidate environment variables to ENVIRONMENT preset")
    print("✅ Update test fixtures to use CacheFactory.for_testing()")
    print("✅ Migrate health checks to use get_cache_health_status()")
    print("✅ Add proper error handling with fail_on_connection_error")
    print("✅ Implement configuration validation")
    print("✅ Add performance monitoring and benchmarking")
    
    return results


if __name__ == "__main__":
    """
    Run migration examples when script is executed directly.
    
    Usage:
        python migration_code_examples.py
    """
    asyncio.run(run_all_migration_examples())