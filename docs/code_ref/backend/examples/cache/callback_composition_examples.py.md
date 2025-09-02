---
sidebar_label: callback_composition_examples
---

# Callback Composition Examples

  file_path: `backend/examples/cache/callback_composition_examples.py`

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

## CacheCallbackProtocol

Protocol defining the interface for cache callbacks.

### on_set()

```python
async def on_set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
```

Called before setting a value in cache.

### on_get()

```python
async def on_get(self, key: str, value: Any) -> Any:
```

Called after getting a value from cache (can transform the value).

### on_delete()

```python
async def on_delete(self, key: str) -> None:
```

Called before deleting a value from cache.

### on_miss()

```python
async def on_miss(self, key: str) -> None:
```

Called when a cache miss occurs.

### on_error()

```python
async def on_error(self, operation: str, key: str, error: Exception) -> None:
```

Called when a cache operation encounters an error.

## CacheOperationMetrics

Metrics collected for cache operations.

## CallbackCompositeCache

A cache wrapper that supports callback composition patterns.

This class demonstrates how to migrate from inheritance-based hooks
to flexible callback composition while maintaining full cache functionality.

### __init__()

```python
def __init__(self, cache: CacheInterface, callbacks: List[CacheCallbackProtocol] = None):
```

### add_callback()

```python
def add_callback(self, callback: CacheCallbackProtocol) -> None:
```

Add a callback to the composition chain.

### remove_callback()

```python
def remove_callback(self, callback: CacheCallbackProtocol) -> None:
```

Remove a callback from the composition chain.

### connect()

```python
async def connect(self) -> None:
```

Connect to the underlying cache.

### disconnect()

```python
async def disconnect(self) -> None:
```

Disconnect from the underlying cache.

### set()

```python
async def set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
```

Set a value with callback composition.

### get()

```python
async def get(self, key: str) -> Any:
```

Get a value with callback composition.

### delete()

```python
async def delete(self, key: str) -> None:
```

Delete a value with callback composition.

## AuditCallback

Audit callback for compliance and security logging.

### __init__()

```python
def __init__(self, audit_logger: Optional[logging.Logger] = None):
```

### on_set()

```python
async def on_set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
```

Log cache set operations for audit trail.

### on_get()

```python
async def on_get(self, key: str, value: Any) -> Any:
```

Log cache get operations for audit trail.

### on_delete()

```python
async def on_delete(self, key: str) -> None:
```

Log cache delete operations for audit trail.

### on_miss()

```python
async def on_miss(self, key: str) -> None:
```

Log cache misses for audit trail.

### on_error()

```python
async def on_error(self, operation: str, key: str, error: Exception) -> None:
```

Log cache errors for audit trail.

## PerformanceCallback

Performance monitoring callback with alerting thresholds.

### __init__()

```python
def __init__(self, slow_threshold_ms: float = 100.0):
```

### on_set()

```python
async def on_set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
```

Track set operation start time.

### on_get()

```python
async def on_get(self, key: str, value: Any) -> Any:
```

Track get operation performance.

### on_delete()

```python
async def on_delete(self, key: str) -> None:
```

Track delete operation start time.

### get_performance_stats()

```python
def get_performance_stats(self) -> Dict[str, Dict[str, float]]:
```

Get performance statistics for all operations.

## AlertingCallback

Alerting callback for critical cache events.

### __init__()

```python
def __init__(self, error_threshold: int = 5, miss_rate_threshold: float = 0.8):
```

### on_get()

```python
async def on_get(self, key: str, value: Any) -> Any:
```

Track cache hit/miss ratio for alerting.

### on_miss()

```python
async def on_miss(self, key: str) -> None:
```

Track cache misses and alert on high miss rate.

### on_error()

```python
async def on_error(self, operation: str, key: str, error: Exception) -> None:
```

Track errors and alert on threshold breach.

## DataTransformCallback

Data transformation callback for encryption, compression, or formatting.

### __init__()

```python
def __init__(self, transform_keys: List[str] = None):
```

### on_set()

```python
async def on_set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
```

Potentially transform data before setting (placeholder).

### on_get()

```python
async def on_get(self, key: str, value: Any) -> Any:
```

Transform data after retrieval.

## BusinessLogicCallback

Custom business logic callback for application-specific behavior.

### __init__()

```python
def __init__(self, user_context: Dict[str, Any] = None):
```

### on_set()

```python
async def on_set(self, key: str, value: Any, ttl: Optional[int] = None) -> None:
```

Execute business logic on cache set.

### on_get()

```python
async def on_get(self, key: str, value: Any) -> Any:
```

Execute business logic on cache get.

### on_miss()

```python
async def on_miss(self, key: str) -> None:
```

Execute business logic on cache miss.

## example_basic_callback_composition()

```python
async def example_basic_callback_composition():
```

Example 1: Basic Callback Composition

Demonstrates setting up a cache with multiple callbacks
for audit, performance monitoring, and alerting.

## example_migration_from_inheritance()

```python
async def example_migration_from_inheritance():
```

Example 2: Migration from Inheritance to Callback Composition

Shows before/after patterns for migrating from inheritance-based
cache hooks to flexible callback composition.

## example_advanced_callback_chaining()

```python
async def example_advanced_callback_chaining():
```

Example 3: Advanced Callback Chaining

Demonstrates complex callback chains with conditional execution,
data transformation, and error handling patterns.

## example_fastapi_dependency_integration()

```python
async def example_fastapi_dependency_integration():
```

Example 4: FastAPI Dependency Integration

Demonstrates integrating callback-composed caches with
FastAPI dependency injection system.

## example_testing_callback_strategies()

```python
async def example_testing_callback_strategies():
```

Example 5: Testing Strategies for Callback-Based Caches

Demonstrates unit testing patterns for callback composition,
mocking strategies, and test isolation techniques.

## run_all_callback_examples()

```python
async def run_all_callback_examples():
```

Run all callback composition examples in sequence.

Demonstrates the complete range of callback functionality
and composition patterns.
