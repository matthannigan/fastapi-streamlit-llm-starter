"""
Callback Composition Examples

This module demonstrates advanced callback composition patterns for cache infrastructure,
showing how to migrate from inheritance-based hooks to flexible callback composition
patterns that support audit, performance monitoring, alerting, and custom business logic.

Examples included:
- Custom callback composition for web applications
- Audit, performance, and alerting callback examples
- Migration from inheritance hooks to callback composition
- Advanced callback chaining and composition techniques
- Integration with FastAPI dependency injection
- Testing strategies for callback-based cache implementations
"""

import asyncio
import json
import logging
import time
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Protocol, Union
from datetime import datetime
from abc import ABC, abstractmethod

from app.infrastructure.cache import (
    CacheFactory,
    CacheInterface,
    GenericRedisCache,
    AIResponseCache,
    InMemoryCache,
)


# Set up logging for examples
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


# =============================================================================
# Callback Protocols and Base Classes
# =============================================================================

class CacheCallbackProtocol(Protocol):
    """Protocol defining the interface for cache callbacks."""
    
    async def on_set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Called before setting a value in cache."""
        ...
    
    async def on_get(self, key: str, value: Any) -> Any:
        """Called after getting a value from cache (can transform the value)."""
        ...
    
    async def on_delete(self, key: str) -> None:
        """Called before deleting a value from cache."""
        ...
    
    async def on_miss(self, key: str) -> None:
        """Called when a cache miss occurs."""
        ...
    
    async def on_error(self, operation: str, key: str, error: Exception) -> None:
        """Called when a cache operation encounters an error."""
        ...


@dataclass
class CacheOperationMetrics:
    """Metrics collected for cache operations."""
    operation: str
    key: str
    timestamp: datetime
    duration_ms: float
    success: bool
    error: Optional[str] = None
    value_size: Optional[int] = None


class CallbackCompositeCache:
    """
    A cache wrapper that supports callback composition patterns.
    
    This class demonstrates how to migrate from inheritance-based hooks
    to flexible callback composition while maintaining full cache functionality.
    """
    
    def __init__(self, cache: CacheInterface, callbacks: List[CacheCallbackProtocol] = None):
        self.cache = cache
        self.callbacks = callbacks or []
        self.metrics: List[CacheOperationMetrics] = []
    
    def add_callback(self, callback: CacheCallbackProtocol) -> None:
        """Add a callback to the composition chain."""
        self.callbacks.append(callback)
    
    def remove_callback(self, callback: CacheCallbackProtocol) -> None:
        """Remove a callback from the composition chain."""
        if callback in self.callbacks:
            self.callbacks.remove(callback)
    
    async def connect(self) -> None:
        """Connect to the underlying cache."""
        await self.cache.connect()
    
    async def disconnect(self) -> None:
        """Disconnect from the underlying cache."""
        await self.cache.disconnect()
    
    async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Set a value with callback composition."""
        start_time = time.time()
        success = True
        error = None
        
        try:
            # Execute on_set callbacks
            for callback in self.callbacks:
                if hasattr(callback, 'on_set'):
                    await callback.on_set(key, value, ttl)
            
            # Perform the actual cache operation
            await self.cache.set(key, value, ttl)
            
        except Exception as e:
            success = False
            error = str(e)
            
            # Execute on_error callbacks
            for callback in self.callbacks:
                if hasattr(callback, 'on_error'):
                    await callback.on_error("set", key, e)
            
            raise
        finally:
            # Record metrics
            duration = (time.time() - start_time) * 1000
            self.metrics.append(CacheOperationMetrics(
                operation="set",
                key=key,
                timestamp=datetime.now(),
                duration_ms=duration,
                success=success,
                error=error,
                value_size=len(str(value)) if value else None
            ))
    
    async def get(self, key: str) -> Any:
        """Get a value with callback composition."""
        start_time = time.time()
        success = True
        error = None
        value = None
        
        try:
            # Perform the actual cache operation
            value = await self.cache.get(key)
            
            if value is None:
                # Execute on_miss callbacks
                for callback in self.callbacks:
                    if hasattr(callback, 'on_miss'):
                        await callback.on_miss(key)
            else:
                # Execute on_get callbacks (can transform value)
                for callback in self.callbacks:
                    if hasattr(callback, 'on_get'):
                        value = await callback.on_get(key, value) or value
            
            return value
            
        except Exception as e:
            success = False
            error = str(e)
            
            # Execute on_error callbacks
            for callback in self.callbacks:
                if hasattr(callback, 'on_error'):
                    await callback.on_error("get", key, e)
            
            raise
        finally:
            # Record metrics
            duration = (time.time() - start_time) * 1000
            self.metrics.append(CacheOperationMetrics(
                operation="get",
                key=key,
                timestamp=datetime.now(),
                duration_ms=duration,
                success=success,
                error=error,
                value_size=len(str(value)) if value else None
            ))
    
    async def delete(self, key: str) -> None:
        """Delete a value with callback composition."""
        start_time = time.time()
        success = True
        error = None
        
        try:
            # Execute on_delete callbacks
            for callback in self.callbacks:
                if hasattr(callback, 'on_delete'):
                    await callback.on_delete(key)
            
            # Perform the actual cache operation
            await self.cache.delete(key)
            
        except Exception as e:
            success = False
            error = str(e)
            
            # Execute on_error callbacks
            for callback in self.callbacks:
                if hasattr(callback, 'on_error'):
                    await callback.on_error("delete", key, e)
            
            raise
        finally:
            # Record metrics
            duration = (time.time() - start_time) * 1000
            self.metrics.append(CacheOperationMetrics(
                operation="delete",
                key=key,
                timestamp=datetime.now(),
                duration_ms=duration,
                success=success,
                error=error
            ))


# =============================================================================
# Concrete Callback Implementations
# =============================================================================

class AuditCallback:
    """Audit callback for compliance and security logging."""
    
    def __init__(self, audit_logger: Optional[logging.Logger] = None):
        self.audit_logger = audit_logger or logging.getLogger("cache.audit")
    
    async def on_set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Log cache set operations for audit trail."""
        self.audit_logger.info(
            f"AUDIT: SET operation - key='{key}', ttl={ttl}, "
            f"value_type={type(value).__name__}, timestamp={datetime.now().isoformat()}"
        )
    
    async def on_get(self, key: str, value: Any) -> Any:
        """Log cache get operations for audit trail."""
        if value is not None:
            self.audit_logger.info(
                f"AUDIT: GET operation - key='{key}', hit=True, "
                f"value_type={type(value).__name__}, timestamp={datetime.now().isoformat()}"
            )
        return value
    
    async def on_delete(self, key: str) -> None:
        """Log cache delete operations for audit trail."""
        self.audit_logger.info(
            f"AUDIT: DELETE operation - key='{key}', timestamp={datetime.now().isoformat()}"
        )
    
    async def on_miss(self, key: str) -> None:
        """Log cache misses for audit trail."""
        self.audit_logger.info(
            f"AUDIT: MISS operation - key='{key}', timestamp={datetime.now().isoformat()}"
        )
    
    async def on_error(self, operation: str, key: str, error: Exception) -> None:
        """Log cache errors for audit trail."""
        self.audit_logger.error(
            f"AUDIT: ERROR in {operation} operation - key='{key}', "
            f"error={type(error).__name__}: {error}, timestamp={datetime.now().isoformat()}"
        )


class PerformanceCallback:
    """Performance monitoring callback with alerting thresholds."""
    
    def __init__(self, slow_threshold_ms: float = 100.0):
        self.slow_threshold_ms = slow_threshold_ms
        self.operation_times: Dict[str, List[float]] = {}
        self.performance_logger = logging.getLogger("cache.performance")
    
    async def on_set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Track set operation start time."""
        self._start_timing("set", key)
    
    async def on_get(self, key: str, value: Any) -> Any:
        """Track get operation performance."""
        duration = self._end_timing("get", key)
        if duration and duration > self.slow_threshold_ms:
            self.performance_logger.warning(
                f"SLOW GET: key='{key}', duration={duration:.2f}ms (threshold: {self.slow_threshold_ms}ms)"
            )
        return value
    
    async def on_delete(self, key: str) -> None:
        """Track delete operation start time."""
        self._start_timing("delete", key)
    
    def _start_timing(self, operation: str, key: str) -> None:
        """Start timing an operation."""
        timing_key = f"{operation}:{key}"
        if not hasattr(self, '_start_times'):
            self._start_times = {}
        self._start_times[timing_key] = time.time()
    
    def _end_timing(self, operation: str, key: str) -> Optional[float]:
        """End timing an operation and return duration in milliseconds."""
        timing_key = f"{operation}:{key}"
        if not hasattr(self, '_start_times'):
            return None
        
        start_time = self._start_times.pop(timing_key, None)
        if start_time:
            duration_ms = (time.time() - start_time) * 1000
            
            # Store performance data
            if operation not in self.operation_times:
                self.operation_times[operation] = []
            self.operation_times[operation].append(duration_ms)
            
            return duration_ms
        return None
    
    def get_performance_stats(self) -> Dict[str, Dict[str, float]]:
        """Get performance statistics for all operations."""
        stats = {}
        for operation, times in self.operation_times.items():
            if times:
                stats[operation] = {
                    "count": len(times),
                    "avg_ms": sum(times) / len(times),
                    "min_ms": min(times),
                    "max_ms": max(times),
                    "p95_ms": sorted(times)[int(len(times) * 0.95)] if len(times) > 20 else max(times)
                }
        return stats


class AlertingCallback:
    """Alerting callback for critical cache events."""
    
    def __init__(self, error_threshold: int = 5, miss_rate_threshold: float = 0.8):
        self.error_threshold = error_threshold
        self.miss_rate_threshold = miss_rate_threshold
        self.error_count = 0
        self.get_count = 0
        self.miss_count = 0
        self.alert_logger = logging.getLogger("cache.alerts")
    
    async def on_get(self, key: str, value: Any) -> Any:
        """Track cache hit/miss ratio for alerting."""
        self.get_count += 1
        return value
    
    async def on_miss(self, key: str) -> None:
        """Track cache misses and alert on high miss rate."""
        self.miss_count += 1
        
        if self.get_count > 0:
            miss_rate = self.miss_count / self.get_count
            if miss_rate > self.miss_rate_threshold:
                self.alert_logger.critical(
                    f"ALERT: High cache miss rate - {miss_rate:.2%} "
                    f"(threshold: {self.miss_rate_threshold:.2%}), "
                    f"misses: {self.miss_count}, total: {self.get_count}"
                )
    
    async def on_error(self, operation: str, key: str, error: Exception) -> None:
        """Track errors and alert on threshold breach."""
        self.error_count += 1
        
        if self.error_count >= self.error_threshold:
            self.alert_logger.critical(
                f"ALERT: Cache error threshold breached - "
                f"error_count: {self.error_count} (threshold: {self.error_threshold}), "
                f"latest_error: {type(error).__name__}: {error}"
            )


class DataTransformCallback:
    """Data transformation callback for encryption, compression, or formatting."""
    
    def __init__(self, transform_keys: List[str] = None):
        self.transform_keys = transform_keys or []
    
    async def on_set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Potentially transform data before setting (placeholder)."""
        if any(pattern in key for pattern in self.transform_keys):
            logger.info(f"TRANSFORM: Preparing to transform data for key '{key}'")
    
    async def on_get(self, key: str, value: Any) -> Any:
        """Transform data after retrieval."""
        if value and any(pattern in key for pattern in self.transform_keys):
            # Example transformation: add metadata
            if isinstance(value, dict):
                transformed_value = value.copy()
                transformed_value["_cache_metadata"] = {
                    "retrieved_at": datetime.now().isoformat(),
                    "transformed": True,
                    "key": key
                }
                logger.info(f"TRANSFORM: Added metadata to value for key '{key}'")
                return transformed_value
        
        return value


class BusinessLogicCallback:
    """Custom business logic callback for application-specific behavior."""
    
    def __init__(self, user_context: Dict[str, Any] = None):
        self.user_context = user_context or {}
        self.business_logger = logging.getLogger("cache.business")
    
    async def on_set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
        """Execute business logic on cache set."""
        if "user_session" in key and isinstance(value, dict):
            user_id = value.get("user_id")
            if user_id:
                self.business_logger.info(
                    f"BUSINESS: User {user_id} session cached, activity recorded"
                )
    
    async def on_get(self, key: str, value: Any) -> Any:
        """Execute business logic on cache get."""
        if "api_response" in key and value:
            # Track API cache usage for analytics
            self.business_logger.info(
                f"BUSINESS: API response cache hit for key '{key}', "
                f"saved backend request"
            )
        
        return value
    
    async def on_miss(self, key: str) -> None:
        """Execute business logic on cache miss."""
        if "expensive_computation" in key:
            self.business_logger.warning(
                f"BUSINESS: Cache miss for expensive computation '{key}', "
                f"backend load will increase"
            )


# =============================================================================
# Example Implementations
# =============================================================================

async def example_basic_callback_composition():
    """
    Example 1: Basic Callback Composition
    
    Demonstrates setting up a cache with multiple callbacks
    for audit, performance monitoring, and alerting.
    """
    print("\n" + "="*60)
    print("Example 1: Basic Callback Composition")
    print("="*60)
    
    # Create base cache
    base_cache = CacheFactory.for_web_app(
        redis_url="redis://localhost:6379/10",
        fail_on_connection_error=False
    )
    
    # Create callbacks
    audit_callback = AuditCallback()
    performance_callback = PerformanceCallback(slow_threshold_ms=50.0)
    alerting_callback = AlertingCallback(error_threshold=3, miss_rate_threshold=0.7)
    
    # Compose cache with callbacks
    composite_cache = CallbackCompositeCache(
        cache=base_cache,
        callbacks=[audit_callback, performance_callback, alerting_callback]
    )
    
    await composite_cache.connect()
    
    print("Testing callback composition...")
    
    # Test operations that trigger various callbacks
    test_data = {
        "user_id": "user_123",
        "session_data": {"login_time": time.time(), "preferences": {"theme": "dark"}},
        "test": True
    }
    
    # SET operation (triggers audit and performance tracking)
    await composite_cache.set("user_session:123", test_data, ttl=1800)
    print("✅ SET operation completed with callbacks")
    
    # GET operation (triggers performance monitoring)
    retrieved_data = await composite_cache.get("user_session:123")
    print(f"✅ GET operation completed: {retrieved_data['user_id']}")
    
    # Cache miss (triggers alerting)
    missing_data = await composite_cache.get("nonexistent_key")
    print(f"✅ Cache miss handled: {missing_data is None}")
    
    # Check performance stats
    perf_stats = performance_callback.get_performance_stats()
    print(f"✅ Performance stats collected: {len(perf_stats)} operation types")
    
    await composite_cache.disconnect()
    print("✅ Basic callback composition example completed")


async def example_migration_from_inheritance():
    """
    Example 2: Migration from Inheritance to Callback Composition
    
    Shows before/after patterns for migrating from inheritance-based
    cache hooks to flexible callback composition.
    """
    print("\n" + "="*60)
    print("Example 2: Migration from Inheritance to Callback Composition")
    print("="*60)
    
    print("BEFORE: Inheritance-based cache hooks")
    print("# class AuditedCache(BaseCache):")
    print("#     def set(self, key, value, ttl=None):")
    print("#         self.audit_log(f'Setting {key}')")
    print("#         return super().set(key, value, ttl)")
    print()
    print("AFTER: Callback composition")
    
    # Create specialized callbacks for migration example
    class LegacyAuditCallback:
        """Migrated legacy audit functionality."""
        
        async def on_set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
            print(f"LEGACY_AUDIT: Setting key '{key}' (migrated from inheritance)")
        
        async def on_get(self, key: str, value: Any) -> Any:
            if value:
                print(f"LEGACY_AUDIT: Retrieved key '{key}' (migrated from inheritance)")
            return value
    
    class LegacyPerformanceCallback:
        """Migrated legacy performance monitoring."""
        
        async def on_set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
            print(f"LEGACY_PERF: Monitoring SET performance for '{key}'")
        
        async def on_get(self, key: str, value: Any) -> Any:
            print(f"LEGACY_PERF: Monitoring GET performance for '{key}'")
            return value
    
    # Set up migrated cache
    base_cache = CacheFactory.for_testing("memory")
    migrated_cache = CallbackCompositeCache(
        cache=base_cache,
        callbacks=[LegacyAuditCallback(), LegacyPerformanceCallback()]
    )
    
    await migrated_cache.connect()
    
    print("\nTesting migrated functionality...")
    
    # Test that old functionality works with new pattern
    legacy_data = {"migrated": True, "pattern": "callback_composition"}
    await migrated_cache.set("migration_test", legacy_data)
    retrieved = await migrated_cache.get("migration_test")
    
    print(f"✅ Migration successful: {retrieved['pattern']}")
    print("✅ Legacy functionality preserved with callback composition")
    
    await migrated_cache.disconnect()
    print("✅ Migration from inheritance example completed")


async def example_advanced_callback_chaining():
    """
    Example 3: Advanced Callback Chaining
    
    Demonstrates complex callback chains with conditional execution,
    data transformation, and error handling patterns.
    """
    print("\n" + "="*60)
    print("Example 3: Advanced Callback Chaining")
    print("="*60)
    
    # Create advanced callbacks
    transform_callback = DataTransformCallback(transform_keys=["api_response", "user_data"])
    business_callback = BusinessLogicCallback(user_context={"tenant_id": "tenant_123"})
    audit_callback = AuditCallback()
    
    # Create cache with chained callbacks
    base_cache = CacheFactory.for_ai_app(
        redis_url="redis://localhost:6379/11",
        fail_on_connection_error=False
    )
    
    chained_cache = CallbackCompositeCache(
        cache=base_cache,
        callbacks=[
            transform_callback,  # First: transform data
            business_callback,   # Second: business logic
            audit_callback,      # Third: audit logging
        ]
    )
    
    await chained_cache.connect()
    
    print("Testing advanced callback chaining...")
    
    # Test data transformation chain
    api_data = {
        "endpoint": "/api/users",
        "response": {"users": [{"id": 1, "name": "Alice"}]},
        "cached_at": time.time()
    }
    
    await chained_cache.set("api_response:users", api_data)
    transformed_data = await chained_cache.get("api_response:users")
    
    # Check if transformation was applied
    if "_cache_metadata" in transformed_data:
        print("✅ Data transformation applied in callback chain")
        print(f"✅ Metadata added: {transformed_data['_cache_metadata']['retrieved_at']}")
    
    # Test business logic chain
    user_session = {
        "user_id": "user_456",
        "session_token": "token_789",
        "login_time": time.time()
    }
    
    await chained_cache.set("user_session:456", user_session)
    session_data = await chained_cache.get("user_session:456")
    
    print(f"✅ Business logic executed for user: {session_data['user_id']}")
    
    # Dynamic callback addition
    print("\nTesting dynamic callback management...")
    
    class DynamicCallback:
        async def on_get(self, key: str, value: Any) -> Any:
            print(f"DYNAMIC: Dynamically added callback triggered for '{key}'")
            return value
    
    dynamic_callback = DynamicCallback()
    chained_cache.add_callback(dynamic_callback)
    
    # Test dynamic callback
    await chained_cache.get("api_response:users")
    print("✅ Dynamic callback addition successful")
    
    # Remove dynamic callback
    chained_cache.remove_callback(dynamic_callback)
    await chained_cache.get("user_session:456")
    print("✅ Dynamic callback removal successful")
    
    await chained_cache.disconnect()
    print("✅ Advanced callback chaining example completed")


async def example_fastapi_dependency_integration():
    """
    Example 4: FastAPI Dependency Integration
    
    Demonstrates integrating callback-composed caches with
    FastAPI dependency injection system.
    """
    print("\n" + "="*60)
    print("Example 4: FastAPI Dependency Integration")
    print("="*60)
    
    print("FastAPI dependency pattern with callback composition:")
    print()
    
    # Simulate FastAPI dependency setup
    class MockFastAPISetup:
        """Mock FastAPI application setup with callback-composed cache."""
        
        def __init__(self):
            self.cache = None
            self.callbacks = []
        
        async def create_cache_dependency(self) -> CallbackCompositeCache:
            """Factory function for FastAPI dependency injection."""
            if not self.cache:
                # Create base cache
                base_cache = CacheFactory.for_web_app(
                    redis_url="redis://localhost:6379/12",
                    fail_on_connection_error=False
                )
                
                # Create callbacks for production use
                audit = AuditCallback()
                performance = PerformanceCallback(slow_threshold_ms=100.0)
                business = BusinessLogicCallback()
                
                # Compose cache
                self.cache = CallbackCompositeCache(
                    cache=base_cache,
                    callbacks=[audit, performance, business]
                )
                
                await self.cache.connect()
                print("✅ FastAPI cache dependency created with callbacks")
            
            return self.cache
        
        async def cleanup_cache_dependency(self):
            """Cleanup function for application shutdown."""
            if self.cache:
                await self.cache.disconnect()
                print("✅ FastAPI cache dependency cleaned up")
    
    # Simulate FastAPI application
    app_setup = MockFastAPISetup()
    
    # Simulate dependency injection in route handler
    cache_service = await app_setup.create_cache_dependency()
    
    print("Simulating FastAPI route handlers...")
    
    # Simulate route: POST /api/sessions
    async def create_session_route(user_id: str):
        session_data = {
            "user_id": user_id,
            "created_at": time.time(),
            "status": "active"
        }
        await cache_service.set(f"session:{user_id}", session_data, ttl=3600)
        return {"message": "Session created", "user_id": user_id}
    
    # Simulate route: GET /api/sessions/{user_id}
    async def get_session_route(user_id: str):
        session_data = await cache_service.get(f"session:{user_id}")
        if session_data:
            return {"session": session_data, "cached": True}
        return {"message": "Session not found", "cached": False}
    
    # Test simulated routes
    print("Testing simulated FastAPI routes...")
    
    create_result = await create_session_route("user_fastapi_123")
    print(f"✅ Session created: {create_result['message']}")
    
    get_result = await get_session_route("user_fastapi_123")
    print(f"✅ Session retrieved: cached={get_result['cached']}")
    
    # Cleanup
    await app_setup.cleanup_cache_dependency()
    print("✅ FastAPI dependency integration example completed")


async def example_testing_callback_strategies():
    """
    Example 5: Testing Strategies for Callback-Based Caches
    
    Demonstrates unit testing patterns for callback composition,
    mocking strategies, and test isolation techniques.
    """
    print("\n" + "="*60)
    print("Example 5: Testing Strategies for Callback-Based Caches")
    print("="*60)
    
    print("Testing patterns for callback composition:")
    
    # Mock callback for testing
    class MockAuditCallback:
        def __init__(self):
            self.calls = {"on_set": [], "on_get": [], "on_delete": [], "on_miss": [], "on_error": []}
        
        async def on_set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
            self.calls["on_set"].append({"key": key, "value": value, "ttl": ttl})
        
        async def on_get(self, key: str, value: Any) -> Any:
            self.calls["on_get"].append({"key": key, "value": value})
            return value
        
        async def on_delete(self, key: str) -> None:
            self.calls["on_delete"].append({"key": key})
        
        async def on_miss(self, key: str) -> None:
            self.calls["on_miss"].append({"key": key})
        
        async def on_error(self, operation: str, key: str, error: Exception) -> None:
            self.calls["on_error"].append({"operation": operation, "key": key, "error": str(error)})
    
    # Test callback isolation
    print("\n1. Testing callback isolation:")
    
    test_cache = CacheFactory.for_testing("memory")
    mock_audit = MockAuditCallback()
    
    test_composite = CallbackCompositeCache(
        cache=test_cache,
        callbacks=[mock_audit]
    )
    
    await test_composite.connect()
    
    # Test SET operation
    await test_composite.set("test_key", {"test": "data"})
    assert len(mock_audit.calls["on_set"]) == 1
    assert mock_audit.calls["on_set"][0]["key"] == "test_key"
    print("✅ SET callback isolation verified")
    
    # Test GET operation
    result = await test_composite.get("test_key")
    assert len(mock_audit.calls["on_get"]) == 1
    assert result["test"] == "data"
    print("✅ GET callback isolation verified")
    
    # Test cache miss
    await test_composite.get("nonexistent_key")
    assert len(mock_audit.calls["on_miss"]) == 1
    print("✅ MISS callback isolation verified")
    
    # Test DELETE operation
    await test_composite.delete("test_key")
    assert len(mock_audit.calls["on_delete"]) == 1
    print("✅ DELETE callback isolation verified")
    
    print("\n2. Testing callback composition patterns:")
    
    # Test multiple callbacks
    class MockPerformanceCallback:
        def __init__(self):
            self.operation_count = 0
        
        async def on_set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
            self.operation_count += 1
        
        async def on_get(self, key: str, value: Any) -> Any:
            self.operation_count += 1
            return value
    
    mock_performance = MockPerformanceCallback()
    test_composite.add_callback(mock_performance)
    
    # Test that both callbacks are called
    await test_composite.set("multi_test", {"multi": True})
    
    # Verify both callbacks were triggered
    assert len(mock_audit.calls["on_set"]) == 2  # Previous + new call
    assert mock_performance.operation_count == 1
    print("✅ Multiple callback composition verified")
    
    print("\n3. Testing error handling in callbacks:")
    
    class ErrorProneCallback:
        async def on_set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
            if "error" in key:
                raise ValueError("Test error in callback")
    
    error_callback = ErrorProneCallback()
    test_composite.add_callback(error_callback)
    
    # Test error handling
    try:
        await test_composite.set("error_key", {"will": "fail"})
        assert False, "Expected error was not raised"
    except ValueError as e:
        assert "Test error in callback" in str(e)
        print("✅ Callback error handling verified")
    
    await test_composite.disconnect()
    print("✅ Testing strategies example completed")


async def run_all_callback_examples():
    """
    Run all callback composition examples in sequence.
    
    Demonstrates the complete range of callback functionality
    and composition patterns.
    """
    print("🚀 Starting Callback Composition Examples")
    print("=" * 80)
    
    examples = [
        example_basic_callback_composition,
        example_migration_from_inheritance,
        example_advanced_callback_chaining,
        example_fastapi_dependency_integration,
        example_testing_callback_strategies,
    ]
    
    results = {"successful": 0, "failed": 0, "errors": []}
    
    for i, example in enumerate(examples, 1):
        try:
            await example()
            results["successful"] += 1
        except Exception as e:
            results["failed"] += 1
            results["errors"].append(f"Example {i} ({example.__name__}): {e}")
            logger.error(f"Callback example {i} failed: {e}")
    
    # Summary
    print("\n" + "="*80)
    print("📊 CALLBACK COMPOSITION EXAMPLES SUMMARY")
    print("="*80)
    print(f"✅ Successful examples: {results['successful']}")
    print(f"❌ Failed examples: {results['failed']}")
    
    if results["errors"]:
        print("\nErrors encountered:")
        for error in results["errors"]:
            print(f"  - {error}")
    
    print(f"\n🎉 Callback examples completed! Success rate: {results['successful']}/{len(examples)}")
    
    return results


if __name__ == "__main__":
    """
    Run callback composition examples when script is executed directly.
    
    Usage:
        python callback_composition_examples.py
    """
    asyncio.run(run_all_callback_examples())