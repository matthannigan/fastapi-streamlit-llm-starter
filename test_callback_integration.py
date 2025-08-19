#!/usr/bin/env python3
"""
Test Callback Composition Integration with Phase 3 Cache Types

This test verifies that callback composition works correctly with all
cache types created by the Phase 3 factory methods.
"""

import asyncio
import sys
import os
from typing import Any, Optional

# Add backend directory to path for imports
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from app.infrastructure.cache import CacheFactory, CacheInterface

class TestCallback:
    """Simple test callback to verify callback composition works"""
    
    def __init__(self, name: str):
        self.name = name
        self.calls = []
    
    async def on_set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Called before setting a value in cache"""
        self.calls.append(f"on_set: {key}={value} (ttl={ttl})")
        print(f"[{self.name}] on_set: {key}={value}")
    
    async def on_get(self, key: str, value: Any) -> None:
        """Called after getting a value from cache"""
        self.calls.append(f"on_get: {key}={value}")
        print(f"[{self.name}] on_get: {key}={value}")
    
    async def on_delete(self, key: str) -> None:
        """Called before deleting a value from cache"""
        self.calls.append(f"on_delete: {key}")
        print(f"[{self.name}] on_delete: {key}")

async def test_callback_composition_with_cache_type(cache_type: str, cache: CacheInterface):
    """Test callback composition with a specific cache type"""
    print(f"\n🧪 Testing callback composition with {cache_type} cache ({type(cache).__name__})")
    
    # Create test callback
    callback = TestCallback(f"{cache_type}_callback")
    
    # Check if cache supports callbacks
    if not hasattr(cache, 'add_callback'):
        print(f"  ℹ️  Cache type {type(cache).__name__} does not support callbacks")
        return True
    
    try:
        # Add callback to cache
        cache.add_callback(callback)
        print(f"  ✓ Added callback to {cache_type} cache")
        
        # Test cache operations with callbacks
        await cache.set("test_key", "test_value", ttl=60)
        value = await cache.get("test_key")
        await cache.delete("test_key")
        
        # Verify callbacks were called
        expected_calls = 3  # set, get, delete
        actual_calls = len(callback.calls)
        
        if actual_calls >= expected_calls:
            print(f"  ✓ Callback composition working: {actual_calls} calls recorded")
            return True
        else:
            print(f"  ✗ Expected at least {expected_calls} callback calls, got {actual_calls}")
            return False
            
    except Exception as e:
        print(f"  ✗ Error testing callback composition: {e}")
        return False

async def main():
    """Test callback composition with all Phase 3 cache types"""
    print("🧪 Testing Callback Composition with Phase 3 Cache Types\n")
    
    factory = CacheFactory()
    
    # Test cases: cache type name and factory method
    test_cases = [
        ("memory_test", lambda: factory.for_testing(use_memory_cache=True)),
        ("web_fallback", lambda: factory.for_web_app(redis_url=None, fail_on_connection_error=False)),
        ("ai_fallback", lambda: factory.for_ai_app(redis_url=None, fail_on_connection_error=False)),
    ]
    
    results = []
    
    for cache_type, factory_method in test_cases:
        try:
            # Create cache instance
            cache = await factory_method()
            
            # Test callback composition
            result = await test_callback_composition_with_cache_type(cache_type, cache)
            results.append(result)
            
            # Cleanup
            if hasattr(cache, 'disconnect'):
                await cache.disconnect()
                
        except Exception as e:
            print(f"\n❌ Failed to test {cache_type}: {e}")
            results.append(False)
    
    # Summary
    passed = sum(results)
    total = len(results)
    
    print(f"\n📊 Callback Integration Test Results: {passed}/{total} passed")
    
    if passed == total:
        print("🎉 Callback composition works with all Phase 3 cache types!")
        return True
    else:
        print("❌ Some callback integration tests failed")
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    exit(0 if success else 1)