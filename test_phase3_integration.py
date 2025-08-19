#!/usr/bin/env python3
"""
Quick integration test for Phase 3 cache components
"""
import asyncio
import sys
import os

# Add backend directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

def test_phase3_imports():
    """Test that all Phase 3 components can be imported successfully"""
    try:
        # Test Phase 3 imports
        from app.infrastructure.cache import (
            CacheFactory, CacheConfig, AICacheConfig, CacheConfigBuilder,
            EnvironmentPresets, ConfigValidationResult
        )
        
        from app.infrastructure.cache import (
            get_settings, get_cache_config, get_cache_service,
            get_web_cache_service, get_ai_cache_service, 
            get_test_cache, CacheDependencyManager
        )
        
        print("✓ All Phase 3 imports successful")
        return True
        
    except ImportError as e:
        print(f"✗ Import error: {e}")
        return False

async def test_factory_creation():
    """Test basic factory methods work"""
    try:
        from app.infrastructure.cache import CacheFactory
        
        # Create factory instance
        factory = CacheFactory()
        
        # Test memory cache creation
        test_cache = await factory.for_testing(use_memory_cache=True)
        print(f"✓ Test cache created: {type(test_cache).__name__}")
        
        # Test web app cache creation (will fallback to memory if no Redis)
        web_cache = await factory.for_web_app(redis_url=None, fail_on_connection_error=False)
        print(f"✓ Web cache created: {type(web_cache).__name__}")
        
        # Test AI app cache creation (will fallback to memory if no Redis)
        ai_cache = await factory.for_ai_app(redis_url=None, fail_on_connection_error=False)
        print(f"✓ AI cache created: {type(ai_cache).__name__}")
        
        return True
        
    except Exception as e:
        print(f"✗ Factory creation error: {e}")
        return False

def test_config_builder():
    """Test configuration builder pattern"""
    try:
        from app.infrastructure.cache import CacheConfigBuilder, EnvironmentPresets
        
        # Test builder pattern
        config = (CacheConfigBuilder()
                 .for_environment("development")
                 .with_memory_cache(100)
                 .build())
        
        print(f"✓ Config built: redis_url={config.redis_url}, memory_cache_size={config.memory_cache_size}")
        
        # Test environment presets
        dev_preset = EnvironmentPresets.development()
        print(f"✓ Development preset created")
        
        return True
        
    except Exception as e:
        print(f"✗ Config builder error: {e}")
        return False

async def test_async_operations():
    """Test basic async cache operations"""
    try:
        from app.infrastructure.cache import CacheFactory
        
        # Create factory and test cache
        factory = CacheFactory()
        cache = await factory.for_testing(use_memory_cache=True)
        
        # Test basic operations
        await cache.set("test_key", "test_value", ttl=60)
        value = await cache.get("test_key")
        
        if value == "test_value":
            print("✓ Async cache operations working")
            return True
        else:
            print(f"✗ Cache value mismatch: {value}")
            return False
            
    except Exception as e:
        print(f"✗ Async operations error: {e}")
        return False

async def main():
    """Run all integration tests"""
    print("🧪 Testing Phase 3 Cache Infrastructure Integration\n")
    
    # Sync tests
    sync_tests = [
        ("Phase 3 Imports", test_phase3_imports),
        ("Config Builder", test_config_builder),
    ]
    
    # Async tests
    async_tests = [
        ("Factory Creation", test_factory_creation),
        ("Async Operations", test_async_operations),
    ]
    
    results = []
    
    # Run sync tests
    for test_name, test_func in sync_tests:
        print(f"Testing {test_name}...")
        result = test_func()
        results.append(result)
        print()
    
    # Run async tests
    for test_name, test_func in async_tests:
        print(f"Testing {test_name}...")
        result = await test_func()
        results.append(result)
        print()
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print(f"📊 Integration Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 All Phase 3 integration tests passed!")
        return True
    else:
        print("❌ Some integration tests failed")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)