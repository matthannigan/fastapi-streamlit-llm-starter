---
sidebar_label: health
---

# Health Check Infrastructure Module

  file_path: `backend/app/infrastructure/monitoring/health.py`

Async-first, standardized health checking for system components with timeouts,
graceful degradation, and response time measurement. Used by API endpoints and
external monitoring systems.

## HealthCheckError

Base exception for health check operations with contextual error information.

Provides the foundation for health check error handling, enabling specific error
classification and appropriate response strategies for monitoring system failures.

Usage:
    >>> try:
    ...     await health_checker.check_component("database")
    ... except HealthCheckError as e:
    ...     logger.error(f"Health check failed: {e}")

## HealthCheckTimeoutError

Exception raised when health check operations exceed configured timeout limits.

Indicates that a component health check took longer than the allowed time,
suggesting potential system performance issues or component unavailability.

Behavior:
    - Inherits from HealthCheckError for consistent exception hierarchy
    - Automatically raised by timeout mechanisms in health check execution
    - Includes timing context for debugging performance issues
    
Usage:
    >>> try:
    ...     status = await health_checker.check_component("slow_service")
    ... except HealthCheckTimeoutError:
    ...     # Handle timeout with degraded response
    ...     status = ComponentStatus("slow_service", HealthStatus.DEGRADED, "Timeout")

## HealthStatus

## ComponentStatus

## SystemHealthStatus

## HealthChecker

### __init__()

```python
def __init__(self, default_timeout_ms: int = 2000, per_component_timeouts_ms: Optional[Dict[str, int]] = None, retry_count: int = 1, backoff_base_seconds: float = 0.1) -> None:
```

### register_check()

```python
def register_check(self, name: str, check_func: HealthCheckFunc) -> None:
```

### check_component()

```python
async def check_component(self, name: str) -> ComponentStatus:
```

### check_all_components()

```python
async def check_all_components(self) -> SystemHealthStatus:
```

## check_ai_model_health()

```python
async def check_ai_model_health() -> ComponentStatus:
```

## check_cache_health()

```python
async def check_cache_health() -> ComponentStatus:
```

Check cache system health and operational status.

⚠️ PERFORMANCE ISSUE: This function currently creates a new AIResponseCache 
instance on every health check call, which is extremely inefficient and wasteful.
This causes redundant connection setup, memory allocation, and resource usage.

REQUIRED FIX: Update to accept cache service as parameter for dependency injection:

async def check_cache_health(cache_service: AIResponseCache) -> ComponentStatus:
    '''Reuse singleton cache service for optimal performance.'''
    stats = await cache_service.get_cache_stats()  # Reuses existing connections
    
Then update registration in get_health_checker():
checker.register_check("cache", lambda: check_cache_health(cache_service))

This will eliminate redundant instantiation and significantly improve performance
under frequent monitoring scenarios.

Returns:
    ComponentStatus with cache connectivity and operational status

## check_resilience_health()

```python
async def check_resilience_health() -> ComponentStatus:
```

## check_database_health()

```python
async def check_database_health() -> ComponentStatus:
```

⚠️ PLACEHOLDER DATABASE HEALTH CHECK - Always returns healthy!

This function is NOT a functional health check. It always returns HEALTHY
regardless of actual database state. This could mislead operators about
system health.

Replace with actual database connectivity validation for production:

async def check_database_health() -> ComponentStatus:
    name = "database"
    start = time.perf_counter()
    try:
        async with get_database_connection() as conn:
            await conn.execute("SELECT 1")  # Test connectivity
        return ComponentStatus(
            name=name, status=HealthStatus.HEALTHY,
            message="Database connection successful",
            response_time_ms=(time.perf_counter() - start) * 1000.0
        )
    except Exception as e:
        return ComponentStatus(
            name=name, status=HealthStatus.UNHEALTHY,
            message=f"Database connection failed: {e}",
            response_time_ms=(time.perf_counter() - start) * 1000.0
        )

Returns:
    ComponentStatus: Always HEALTHY with "Not implemented" message
