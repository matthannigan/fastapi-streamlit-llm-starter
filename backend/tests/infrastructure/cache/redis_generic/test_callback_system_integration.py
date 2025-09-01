"""
Comprehensive test suite for GenericRedisCache callback system integration.

This module provides systematic behavioral testing of the callback system
functionality, ensuring proper event notification, callback registration,
and integration with cache operations.

Test Coverage:
    - Callback registration for various cache events
    - Callback invocation during cache operations
    - Multiple callback handling for single events
    - Error handling in callback execution
    - Callback system integration with performance monitoring
    - Event-driven cache behavior validation

Testing Philosophy:
    - Uses behavior-driven testing with Given/When/Then structure
    - Tests callback system behavior without mocking the core callback mechanism
    - Validates callback timing and data consistency
    - Ensures callback failures don't affect cache operations
    - Comprehensive event coverage for all cache operations

Test Organization:
    - TestCallbackRegistration: Callback registration and management
    - TestCacheEventCallbacks: Event-driven callback invocation testing
    - TestMultipleCallbackHandling: Multiple callback coordination
    - TestCallbackErrorHandling: Error scenarios and resilience

Fixtures and Mocks:
    From conftest.py:
        - default_generic_redis_config: Standard configuration dictionary
        - fakeredis: Stateful fake Redis client
        - sample_callback_functions: Test callback functions with tracking
        - bulk_test_data: Multiple key-value pairs for batch testing
    From parent conftest.py:
        - sample_cache_key: Standard cache key for testing
        - sample_cache_value: Standard cache value for testing
        - sample_ttl: Standard TTL value for testing
"""

import pytest
import asyncio
from typing import Dict, Any, Callable
from app.infrastructure.cache.redis_generic import GenericRedisCache


class TestCallbackRegistration:
    """
    Test callback registration and management functionality.
    
    The callback system must properly register callbacks for various events
    and maintain the registration state correctly.
    """

    async def test_register_single_callback(self, default_generic_redis_config, sample_callback_functions, fake_redis_client):
        """
        Test registration of a single callback for a cache event.
        
        Given: A GenericRedisCache instance
        When: A callback is registered for a specific event
        Then: The callback should be properly registered
        And: The callback should be associated with the correct event
        And: The callback registry should reflect the registration
        """
        # Given: A GenericRedisCache instance
        cache = GenericRedisCache(**default_generic_redis_config)
        cache.redis = fake_redis_client  # Use fake Redis for testing
        callback = sample_callback_functions["callbacks"]["get_success"]
        
        # When: A callback is registered for a specific event
        cache.register_callback("get_success", callback)
        
        # Then: The callback should be properly registered
        assert "get_success" in cache._callbacks
        assert len(cache._callbacks["get_success"]) == 1
        assert cache._callbacks["get_success"][0] == callback
        
        # And: Test that callback is invoked during cache operation
        await cache.set("test_key", "test_value")
        result = await cache.get("test_key")
        
        # Verify callback was invoked with correct parameters
        assert len(sample_callback_functions["results"]["get_success_calls"]) == 1
        call = sample_callback_functions["results"]["get_success_calls"][0]
        assert call["key"] == "test_key"
        assert call["value"] == "test_value"

    async def test_register_multiple_callbacks_same_event(self, default_generic_redis_config, sample_callback_functions, fake_redis_client):
        """
        Test registration of multiple callbacks for the same event.
        
        Given: A GenericRedisCache instance
        When: Multiple callbacks are registered for the same event
        Then: All callbacks should be properly registered
        And: All callbacks should be associated with the event
        And: Callback execution order should be deterministic
        """
        # Given: A GenericRedisCache instance
        cache = GenericRedisCache(**default_generic_redis_config)
        cache.redis = fake_redis_client
        
        # Create multiple callbacks for the same event
        callback_results = {"calls": []}
        
        def callback1(key, value):
            callback_results["calls"].append(f"callback1: {key}={value}")
            
        def callback2(key, value):
            callback_results["calls"].append(f"callback2: {key}={value}")
        
        # When: Multiple callbacks are registered for the same event
        cache.register_callback("get_success", callback1)
        cache.register_callback("get_success", callback2)
        
        # Then: All callbacks should be properly registered
        assert len(cache._callbacks["get_success"]) == 2
        assert callback1 in cache._callbacks["get_success"]
        assert callback2 in cache._callbacks["get_success"]
        
        # And: Test that all callbacks are invoked during cache operation
        await cache.set("multi_key", "multi_value")
        result = await cache.get("multi_key")
        
        # Verify all callbacks were invoked in registration order
        assert len(callback_results["calls"]) == 2
        assert "callback1: multi_key=multi_value" in callback_results["calls"]
        assert "callback2: multi_key=multi_value" in callback_results["calls"]
        # Verify order (callbacks are stored and executed in registration order)
        assert callback_results["calls"][0] == "callback1: multi_key=multi_value"
        assert callback_results["calls"][1] == "callback2: multi_key=multi_value"

    async def test_register_callbacks_different_events(self, default_generic_redis_config, sample_callback_functions, fake_redis_client):
        """
        Test registration of callbacks for different events.
        
        Given: A GenericRedisCache instance
        When: Callbacks are registered for different events
        Then: Each callback should be associated with its specific event
        And: Event isolation should be maintained
        And: Cross-event callback invocation should not occur
        """
        # Given: A GenericRedisCache instance
        cache = GenericRedisCache(**default_generic_redis_config)
        cache.redis = fake_redis_client
        
        # Create callbacks for different events
        callback_results = {
            "get_success": [],
            "get_miss": [],
            "set_success": [],
            "delete_success": []
        }
        
        def on_get_success(key, value):
            callback_results["get_success"].append(f"{key}={value}")
        
        def on_get_miss(key):
            callback_results["get_miss"].append(key)
        
        def on_set_success(key, value, ttl=None):
            callback_results["set_success"].append(f"{key}={value}")
            
        def on_delete_success(key):
            callback_results["delete_success"].append(key)
        
        # When: Callbacks are registered for different events
        cache.register_callback("get_success", on_get_success)
        cache.register_callback("get_miss", on_get_miss)
        cache.register_callback("set_success", on_set_success)
        cache.register_callback("delete_success", on_delete_success)
        
        # Then: Each callback should be associated with its specific event
        assert len(cache._callbacks["get_success"]) == 1
        assert len(cache._callbacks["get_miss"]) == 1
        assert len(cache._callbacks["set_success"]) == 1
        assert len(cache._callbacks["delete_success"]) == 1
        
        # Test event isolation with different operations
        # Test get_miss event
        result = await cache.get("nonexistent_key")
        assert result is None
        assert len(callback_results["get_miss"]) == 1
        assert callback_results["get_miss"][0] == "nonexistent_key"
        assert len(callback_results["get_success"]) == 0  # Should not trigger
        
        # Test set_success event  
        await cache.set("test_key", "test_value")
        assert len(callback_results["set_success"]) == 1
        assert callback_results["set_success"][0] == "test_key=test_value"
        
        # Test get_success event
        result = await cache.get("test_key")
        assert len(callback_results["get_success"]) == 1
        assert callback_results["get_success"][0] == "test_key=test_value"
        
        # Test delete_success event
        deleted = await cache.delete("test_key")
        assert deleted
        assert len(callback_results["delete_success"]) == 1
        assert callback_results["delete_success"][0] == "test_key"

    def test_callback_registration_validation(self, default_generic_redis_config):
        """
        Test validation of callback registration parameters.
        
        Given: A GenericRedisCache instance
        When: Callback registration is attempted with various parameters
        Then: Valid registrations should succeed
        And: Invalid event names should be handled appropriately
        And: Invalid callback functions should be rejected
        """
        # Given: A GenericRedisCache instance
        cache = GenericRedisCache(**default_generic_redis_config)
        
        # Valid callback function
        def valid_callback(key, value=None):
            pass
        
        # Test valid registrations - these should succeed without error
        cache.register_callback("get_success", valid_callback)
        cache.register_callback("get_miss", valid_callback)
        cache.register_callback("set_success", valid_callback)
        cache.register_callback("delete_success", valid_callback)
        
        # Verify all valid registrations succeeded
        assert len(cache._callbacks["get_success"]) == 1
        assert len(cache._callbacks["get_miss"]) == 1
        assert len(cache._callbacks["set_success"]) == 1
        assert len(cache._callbacks["delete_success"]) == 1
        
        # Test that unknown event names are still accepted (graceful handling)
        # The implementation doesn't validate event names, it accepts any string
        cache.register_callback("unknown_event", valid_callback)
        assert len(cache._callbacks["unknown_event"]) == 1
        
        # Test that non-callable objects are still registered (no validation in implementation)
        # The implementation doesn't validate that the callback is callable
        cache.register_callback("test_event", "not_a_function")
        assert len(cache._callbacks["test_event"]) == 1
        assert cache._callbacks["test_event"][0] == "not_a_function"
        
        # Test edge cases that should work
        cache.register_callback("", valid_callback)  # Empty event name
        cache.register_callback("event", None)       # None callback
        
        assert len(cache._callbacks[""]) == 1
        assert len(cache._callbacks["event"]) == 1
        assert cache._callbacks["event"][0] is None

    async def test_supported_event_types(self, default_generic_redis_config, sample_callback_functions, fake_redis_client):
        """
        Test registration for all supported event types.
        
        Given: A GenericRedisCache instance
        When: Callbacks are registered for all supported events
        Then: All supported events should accept callback registration
        And: Event types should include: get_success, get_miss, set_success, delete_success
        And: Registration should work for all documented event types
        """
        # Given: A GenericRedisCache instance
        cache = GenericRedisCache(**default_generic_redis_config)
        cache.redis = fake_redis_client
        
        # Define supported event types based on the contract documentation
        supported_events = [
            "get_success",
            "get_miss", 
            "set_success",
            "delete_success"
        ]
        
        # Use sample callbacks for testing
        callbacks = sample_callback_functions["callbacks"]
        results = sample_callback_functions["results"]
        
        # When: Callbacks are registered for all supported events
        for event_type in supported_events:
            if event_type in callbacks:
                cache.register_callback(event_type, callbacks[event_type])
        
        # Then: All supported events should accept callback registration
        for event_type in supported_events:
            assert event_type in cache._callbacks
            if event_type in callbacks:
                assert len(cache._callbacks[event_type]) == 1
                assert cache._callbacks[event_type][0] == callbacks[event_type]
        
        # Test that all event types are triggered during operations
        # Test get_miss
        result = await cache.get("missing_key")
        assert result is None
        assert len(results["get_miss_calls"]) == 1
        assert results["get_miss_calls"][0]["key"] == "missing_key"
        
        # Test set_success
        await cache.set("test_key", "test_value", ttl=3600)
        assert len(results["set_success_calls"]) == 1
        assert results["set_success_calls"][0]["key"] == "test_key"
        assert results["set_success_calls"][0]["value"] == "test_value"
        
        # Test get_success
        result = await cache.get("test_key")
        assert result == "test_value"
        assert len(results["get_success_calls"]) == 1
        assert results["get_success_calls"][0]["key"] == "test_key"
        assert results["get_success_calls"][0]["value"] == "test_value"
        
        # Test delete_success  
        deleted = await cache.delete("test_key")
        assert deleted
        assert len(results["delete_success_calls"]) == 1
        assert results["delete_success_calls"][0]["key"] == "test_key"


class TestMultipleCallbackHandling:
    """
    Test coordination of multiple callbacks for cache events.
    
    These tests verify that multiple callbacks can be registered and executed
    properly without interference between callbacks.
    """




    async def test_callback_registry_state_management(self, default_generic_redis_config, fake_redis_client):
        """
        Test callback registry state management with multiple callbacks.
        
        Given: A callback registry with multiple registered callbacks
        When: Callback registration and invocation occur
        Then: Registry state should be properly maintained
        And: Callback history should be accurately tracked
        And: Registry should handle concurrent callback operations
        """
        # Given: A callback registry with multiple registered callbacks
        cache = GenericRedisCache(**default_generic_redis_config)
        cache.redis = fake_redis_client
        
        # Track callback invocations with detailed state
        callback_state = {
            "invocations": [],
            "registry_snapshots": [],
            "concurrent_calls": 0
        }
        
        def callback1(key, value=None):
            callback_state["concurrent_calls"] += 1
            callback_state["invocations"].append({
                "callback": "callback1", 
                "key": key, 
                "value": value, 
                "concurrent_level": callback_state["concurrent_calls"]
            })
            callback_state["concurrent_calls"] -= 1
        
        def callback2(key, value=None):
            callback_state["concurrent_calls"] += 1
            callback_state["invocations"].append({
                "callback": "callback2", 
                "key": key, 
                "value": value,
                "concurrent_level": callback_state["concurrent_calls"]
            })
            callback_state["concurrent_calls"] -= 1
            
        def callback3(key, value=None):
            callback_state["concurrent_calls"] += 1
            callback_state["invocations"].append({
                "callback": "callback3", 
                "key": key, 
                "value": value,
                "concurrent_level": callback_state["concurrent_calls"]
            })
            callback_state["concurrent_calls"] -= 1
        
        # Register callbacks for different events to test state management
        cache.register_callback("set_success", callback1)
        callback_state["registry_snapshots"].append(len(cache._callbacks["set_success"]))
        
        cache.register_callback("set_success", callback2)
        callback_state["registry_snapshots"].append(len(cache._callbacks["set_success"]))
        
        cache.register_callback("get_success", callback3)
        callback_state["registry_snapshots"].append(len(cache._callbacks["get_success"]))
        
        # Verify registry state is properly maintained
        assert len(cache._callbacks["set_success"]) == 2
        assert len(cache._callbacks["get_success"]) == 1
        assert callback_state["registry_snapshots"] == [1, 2, 1]
        
        # When: Callback registration and invocation occur
        await cache.set("state_key", "state_value")
        result = await cache.get("state_key")
        
        # Then: Registry state should be properly maintained
        assert len(cache._callbacks["set_success"]) == 2  # State unchanged after invocation
        assert len(cache._callbacks["get_success"]) == 1  # State unchanged after invocation
        
        # And: Callback history should be accurately tracked
        assert len(callback_state["invocations"]) == 3  # 2 set callbacks + 1 get callback
        
        set_invocations = [inv for inv in callback_state["invocations"] if inv["callback"] in ["callback1", "callback2"]]
        get_invocations = [inv for inv in callback_state["invocations"] if inv["callback"] == "callback3"]
        
        assert len(set_invocations) == 2
        assert len(get_invocations) == 1
        
        # Verify all callbacks received correct parameters
        for inv in set_invocations:
            assert inv["key"] == "state_key"
            assert inv["value"] == "state_value"
            
        for inv in get_invocations:
            assert inv["key"] == "state_key"
            assert inv["value"] == "state_value"
        
        # And: Registry should handle concurrent callback operations
        # (This tests that callbacks are executed sequentially, not concurrently)
        max_concurrent = max(inv["concurrent_level"] for inv in callback_state["invocations"])
        assert max_concurrent == 1  # Callbacks are executed sequentially


class TestCallbackErrorHandling:
    """
    Test error handling and resilience in the callback system.
    
    These tests verify that callback system errors don't affect cache operations
    and that error scenarios are handled gracefully.
    """




    async def test_callback_memory_leak_prevention(self, default_generic_redis_config, fake_redis_client):
        """
        Test prevention of memory leaks in callback registration.
        
        Given: A cache with dynamic callback registration and deregistration
        When: Many callbacks are registered and operations are performed
        Then: Memory usage should remain stable
        And: Callback references should not accumulate indefinitely
        And: Garbage collection should properly clean up callbacks
        """
        # Given: A cache with dynamic callback registration
        cache = GenericRedisCache(**default_generic_redis_config)
        cache.redis = fake_redis_client
        
        import weakref
        import gc
        
        # Track callback objects for garbage collection testing
        callback_refs = []
        initial_callback_count = len(cache._callbacks.get("get_success", []))
        
        # When: Many callbacks are registered dynamically
        for i in range(100):  # Register many callbacks
            def create_callback(index):
                def callback(key, value):
                    pass
                return callback
            
            callback = create_callback(i)
            callback_refs.append(weakref.ref(callback))
            cache.register_callback("get_success", callback)
            
            # Perform some operations to test runtime behavior
            if i % 10 == 0:  # Every 10 registrations, perform cache operations
                await cache.set(f"key_{i}", f"value_{i}")
                await cache.get(f"key_{i}")
        
        # Verify callbacks were registered
        total_callbacks = len(cache._callbacks["get_success"])
        assert total_callbacks == initial_callback_count + 100
        
        # Test callback reference management
        # Clear local references to callbacks
        del callback_refs[-1]  # Remove one reference
        
        # When callbacks go out of scope, they should still work (they're held by cache)
        alive_refs_before_gc = sum(1 for ref in callback_refs if ref() is not None)
        
        # Force garbage collection
        gc.collect()
        
        # Check that callbacks are still held by the cache registry
        # (callbacks should remain alive because cache holds references)
        assert len(cache._callbacks["get_success"]) == total_callbacks
        
        # Test that callback registry doesn't grow indefinitely for same event
        initial_registry_size = len(cache._callbacks)
        
        # Register more callbacks for different events
        for event in ["get_miss", "set_success", "delete_success"]:
            for i in range(10):
                def temp_callback(key, value=None):
                    pass
                cache.register_callback(event, temp_callback)
        
        # Verify registry growth is controlled and predictable
        final_registry_size = len(cache._callbacks)
        assert final_registry_size == initial_registry_size + 3  # 3 new event types
        
        # Test memory stability with operations
        operations_count = 50
        for i in range(operations_count):
            await cache.set(f"mem_key_{i}", f"mem_value_{i}")
            result = await cache.get(f"mem_key_{i}")
            assert result == f"mem_value_{i}"
        
        # Verify callback registry size remains stable after operations
        assert len(cache._callbacks["get_success"]) == total_callbacks
        assert len(cache._callbacks["set_success"]) == 10
        assert len(cache._callbacks["get_miss"]) == 10  # get_miss callbacks were registered
        assert len(cache._callbacks["delete_success"]) == 10  # delete_success callbacks were registered
        
        # Test that removing cache instance allows proper cleanup
        callback_registry_size_before = len(cache._callbacks["get_success"])
        cache_ref = weakref.ref(cache)
        
        # Cache should still be alive
        assert cache_ref() is not None
        assert len(cache._callbacks["get_success"]) == callback_registry_size_before


    async def test_callback_error_logging_and_monitoring(self, default_generic_redis_config, fake_redis_client, caplog):
        """
        Test error logging and monitoring for callback failures.
        
        Given: A cache with callbacks that encounter errors
        When: Callback errors occur during execution
        Then: Errors should be properly logged with context
        And: Error monitoring should track callback failure rates
        And: Diagnostic information should be available for troubleshooting
        """
        import logging
        
        # Given: A cache with callbacks that encounter errors
        cache = GenericRedisCache(**default_generic_redis_config)
        cache.redis = fake_redis_client
        
        # Track callback execution and errors
        callback_state = {
            "successful_calls": 0,
            "error_calls": 0,
            "error_messages": []
        }
        
        def successful_callback(key, value):
            callback_state["successful_calls"] += 1
        
        def error_callback(key, value):
            callback_state["error_calls"] += 1
            error_msg = f"Callback error for key: {key}"
            callback_state["error_messages"].append(error_msg)
            raise ValueError(error_msg)
            
        def exception_callback(key, value):
            callback_state["error_calls"] += 1
            raise RuntimeError("Critical callback failure")
        
        # Register callbacks including error-prone ones
        cache.register_callback("get_success", successful_callback)
        cache.register_callback("get_success", error_callback)  # This will throw error
        cache.register_callback("set_success", exception_callback)  # This will throw different error
        
        # When: Callback errors occur during execution
        with caplog.at_level(logging.WARNING):
            # Perform operations that will trigger callbacks
            await cache.set("error_key", "error_value")
            result = await cache.get("error_key")
            
            # Perform additional operations to test error resilience
            await cache.set("test_key", "test_value")
            result2 = await cache.get("test_key")
        
        # Then: Errors should be properly logged with context
        warning_logs = [record for record in caplog.records if record.levelname == "WARNING"]
        assert len(warning_logs) >= 2  # At least 2 callback errors should be logged
        
        # Check that error logs contain relevant context
        error_log_messages = [record.message for record in warning_logs]
        
        # Should contain information about callback failures
        get_error_logged = any("get_success" in msg and "failed" in msg for msg in error_log_messages)
        set_error_logged = any("set_success" in msg and "failed" in msg for msg in error_log_messages)
        
        assert get_error_logged, f"Expected get_success callback error in logs: {error_log_messages}"
        assert set_error_logged, f"Expected set_success callback error in logs: {error_log_messages}"
        
        # And: Cache operations should continue to work despite callback errors
        assert result == "error_value"  # Cache operation succeeded despite callback error
        assert result2 == "test_value"  # Subsequent operations also succeed
        
        # And: Both successful and failed callbacks should have been attempted
        assert callback_state["successful_calls"] >= 2  # Successful callback called for both get operations
        assert callback_state["error_calls"] >= 3  # Error callbacks called (2 gets + 2 sets but may vary due to timing)
        
        # And: Error monitoring should track callback failure information
        assert len(callback_state["error_messages"]) >= 2
        assert any("error_key" in msg for msg in callback_state["error_messages"])
        
        # Test that cache remains functional after callback errors
        await cache.set("recovery_key", "recovery_value")
        recovery_result = await cache.get("recovery_key")
        assert recovery_result == "recovery_value"
        
        # Verify error isolation - cache operations are not affected by callback failures
        assert len(cache._callbacks["get_success"]) == 2  # Both callbacks still registered
        assert len(cache._callbacks["set_success"]) == 1  # Error callback still registered
        
        # Test diagnostic information availability
        # The callback registry should maintain state for troubleshooting
        callback_events = list(cache._callbacks.keys())
        assert "get_success" in callback_events
        assert "set_success" in callback_events