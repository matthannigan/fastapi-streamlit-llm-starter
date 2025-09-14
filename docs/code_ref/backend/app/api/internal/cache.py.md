---
sidebar_label: cache
---

# Infrastructure Service: Cache Management REST API

  file_path: `backend/app/api/internal/cache.py`

🏗️ **STABLE API** - Changes affect all template users  
📋 **Minimum test coverage**: 90%  
🔧 **Configuration-driven behavior**

This module provides comprehensive REST API endpoints for managing and monitoring
the AI response cache infrastructure. It serves as the primary interface for cache
operations, performance monitoring, and administrative functions in the FastAPI
application.

## Core Components

### API Endpoints
- `GET  /internal/cache/status`: Cache status and basic statistics (optional auth)
- `POST /internal/cache/invalidate`: Pattern-based cache invalidation (requires auth)
- `GET  /internal/cache/invalidation-stats`: Invalidation frequency statistics (optional auth)
- `GET  /internal/cache/invalidation-recommendations`: Optimization recommendations (optional auth)
- `GET  /internal/cache/metrics`: Comprehensive performance metrics (optional auth)

### Pydantic Response Models
- `CacheKeyGenerationStats`: Key generation timing and text length metrics
- `CacheOperationTypeStats`: Operation-specific performance statistics
- `CacheOperationStats`: Overall cache operation performance with type breakdown
- `CompressionStats`: Compression efficiency and storage savings metrics
- `CachePerformanceResponse`: Complete performance metrics with validation

### Security Model
- **Optional Authentication**: Status, stats, and metrics endpoints (degraded access without auth)
- **Required Authentication**: Invalidation operations (full API key required)
- **Authentication Types**: Primary API key or additional API keys via `verify_api_key`/`optional_verify_api_key`

## Performance Metrics

### Key Generation Analytics
- Timing statistics (avg, median, min, max durations)
- Text length analysis (average and maximum lengths processed)
- Slow operation detection and counting

### Cache Operation Performance
- Performance breakdown by operation type (get, set, delete)
- Duration statistics with percentile analysis
- Slow operation identification and tracking

### Compression Analytics
- Compression ratio statistics (average, median, best, worst)
- Compression timing performance
- Storage savings analysis (bytes processed, saved, percentage)

### System Monitoring
- Memory usage and threshold monitoring
- Hit/miss rate analysis and trending
- Invalidation pattern analysis and recommendations

## Dependencies & Integration

### Infrastructure Dependencies
- `AIResponseCache`: Core cache service providing operations and statistics
- `CachePerformanceMonitor`: Performance metrics collection and computation
- **Security**: API key verification with multiple authentication modes
- **Logging**: Structured logging with error context and request tracing

### FastAPI Dependencies
- `get_cache_service()`: Injected cache service with performance monitoring
- `get_performance_monitor()`: Extracted performance monitor from cache service
- `verify_api_key()`: Required authentication for destructive operations
- `optional_verify_api_key()`: Optional authentication for read operations

## Error Handling Patterns

### Graceful Degradation
- Status endpoints return error information instead of raising exceptions
- Statistics endpoints return empty data structures on failure
- Performance metrics include detailed error context and HTTP status codes

### HTTP Status Codes
- `200 OK`: Successful operations with valid data
- `500 Internal Server Error`: Performance monitor failures, computation errors
- `503 Service Unavailable`: Temporarily disabled monitoring capabilities

### Error Response Validation
- Pydantic model validation for all response structures
- Comprehensive error examples in OpenAPI documentation
- Structured error messages with context and troubleshooting information

## Usage Examples

### Cache Status Monitoring
```python
# GET /internal/cache/status
{
    "redis": {"status": "connected", "memory_usage": "2.5MB"},
    "memory": {"status": "normal", "entries": 1250},
    "performance": {"status": "optimal", "hit_rate": 85.2}
}
```

### Performance Metrics Collection
```python
# GET /internal/cache/metrics
{
    "timestamp": "2024-01-15T10:30:00.123456",
    "cache_hit_rate": 85.5,
    "key_generation": {
        "total_operations": 75,
        "avg_duration": 0.002,
        "slow_operations": 2
    },
    "compression": {
        "avg_compression_ratio": 0.65,
        "total_bytes_saved": 183500,
        "overall_savings_percent": 35.0
    }
}
```

### Cache Invalidation
```python
# POST /internal/cache/invalidate?pattern=user:123:*
{"message": "Cache invalidated for pattern: user:123:*"}
```

## Performance Considerations

### On-Demand Computation
- Performance metrics are computed on-demand to ensure current data
- Statistics calculation may cause brief CPU spikes during computation
- Metrics collection includes memory usage and timing analysis

### Data Retention
- Metrics are collected over configurable retention periods (default: 1 hour)
- Automatic cleanup prevents memory accumulation
- Historical data available for trend analysis and optimization

### Monitoring Impact
- Performance monitoring designed for minimal overhead
- Optional monitoring can be disabled for high-throughput scenarios
- Metrics collection optimized for production environments

**Change with caution** - This infrastructure service provides stable APIs used
across the application. Ensure backward compatibility and comprehensive testing
for any modifications.

## CacheKeyGenerationStats

Statistics for cache key generation operations.

## CacheOperationTypeStats

Statistics for a specific cache operation type.

## CacheOperationStats

Statistics for cache operations.

## CompressionStats

Statistics for compression operations.

## CachePerformanceResponse

Comprehensive cache performance metrics response.

## get_performance_monitor()

```python
async def get_performance_monitor(cache_service: AIResponseCache = Depends(get_cache_service)) -> CachePerformanceMonitor:
```

Get the cache performance monitor from the cache service.

FastAPI dependency function that extracts the performance monitor component
from the injected cache service. This monitor provides access to cache
performance metrics, statistics computation, and monitoring capabilities.

Args:
    cache_service (AIResponseCache): Injected cache service dependency
        containing the performance monitor component.

Returns:
    CachePerformanceMonitor: The performance monitor instance for collecting
        and computing cache performance statistics and metrics.

Raises:
    InfrastructureError: If the cache service does not have a performance_monitor
        attribute or if the monitor is not properly initialized, indicating
        that performance monitoring is not available for this cache implementation.

Example:
    Used as a FastAPI dependency:
    >>> @router.get("/metrics")
    >>> async def endpoint(monitor: CachePerformanceMonitor = Depends(get_performance_monitor)):
    ...     return monitor.get_performance_stats()

## get_performance_monitor_http()

```python
async def get_performance_monitor_http(cache_service: AIResponseCache = Depends(get_cache_service)) -> CachePerformanceMonitor:
```

HTTP-aware dependency wrapper that converts InfrastructureError to HTTPException.

This wrapper catches InfrastructureError exceptions from get_performance_monitor and
converts them to HTTPException which FastAPI handles gracefully, avoiding middleware
conflicts and providing proper HTTP status codes for performance monitor availability.

Args:
    cache_service (AIResponseCache): Injected cache service dependency
        containing the performance monitor component.

Returns:
    CachePerformanceMonitor: The performance monitor instance when available.

Raises:
    HTTPException: 500 Internal Server Error when performance monitor is not available
        for the current cache implementation, with detailed error information.

Example:
    Used as a FastAPI dependency:
    >>> @router.get("/metrics")
    >>> async def endpoint(monitor: CachePerformanceMonitor = Depends(get_performance_monitor_http)):
    ...     return monitor.get_performance_stats()

## get_cache_status()

```python
async def get_cache_status(cache_service: AIResponseCache = Depends(get_cache_service), api_key: str = Depends(optional_verify_api_key)):
```

Comprehensive cache infrastructure status endpoint with multi-layer health assessment and performance metrics.

This endpoint provides detailed operational visibility into all cache infrastructure components,
including Redis connectivity status, memory usage patterns, and performance characteristics.
It serves as the primary cache health validation interface for operational monitoring, enabling
infrastructure teams to assess cache system health and performance optimization opportunities.

Args:
    cache_service: Injected cache service dependency providing comprehensive cache operations,
                  statistics collection, and health monitoring capabilities for both Redis
                  and memory-based caching layers
    api_key: Optional API key for authentication and enhanced access control. Enables detailed
            statistics access and operational audit trail generation when provided while
            maintaining flexible access patterns for monitoring integration

Returns:
    dict: Comprehensive cache infrastructure status containing:
         - redis: Redis backend status including connection state, memory utilization, and operational metrics
         - memory: In-memory cache status with entry counts, capacity utilization, and performance indicators
         - performance: Cache performance metrics including hit rates, response times, and efficiency statistics
         - error: Detailed error information when cache status retrieval experiences failures

Behavior:
    **Multi-Layer Status Assessment:**
    - Evaluates Redis backend connectivity and operational status with connection validation
    - Assesses in-memory cache layer performance and capacity utilization patterns
    - Provides comprehensive performance metrics collection and analysis capabilities
    - Implements graceful error handling with detailed diagnostic information
    
    **Performance Monitoring Integration:**
    - Collects real-time cache performance metrics including hit rates and response times
    - Provides capacity utilization analysis for both Redis and memory-based cache layers
    - Enables performance trend analysis and optimization opportunity identification
    - Supports operational monitoring and alerting integration for cache infrastructure
    
    **Operational Visibility:**
    - Provides detailed cache layer status for infrastructure monitoring and diagnostics
    - Enables cache performance optimization through comprehensive metrics exposure
    - Supports troubleshooting and operational analysis with detailed status information
    - Facilitates capacity planning and performance tuning through usage statistics
    
    **Error Resilience and Recovery:**
    - Implements comprehensive error handling without endpoint failure propagation
    - Provides detailed error information for troubleshooting and diagnosis
    - Maintains operational visibility even when cache components experience issues
    - Enables graceful degradation with partial status information availability

Examples:
    >>> # Comprehensive cache status retrieval
    >>> headers = {"X-API-Key": "cache-admin-key"}
    >>> response = await client.get("/internal/cache/status", headers=headers)
    >>> assert response.status_code == 200
    >>> status = response.json()
    >>> 
    >>> # Redis backend status validation
    >>> redis_status = status.get("redis", {})
    >>> if redis_status.get("status") == "connected":
    ...     print(f"Redis memory usage: {redis_status.get('memory_usage')}")
    ...     assert "memory_usage" in redis_status
    
    >>> # Memory cache layer assessment
    >>> memory_status = status.get("memory", {})
    >>> if memory_status.get("status") == "normal":
    ...     entry_count = memory_status.get("entries", 0)
    ...     print(f"Memory cache entries: {entry_count}")
    
    >>> # Performance metrics evaluation
    >>> performance = status.get("performance", {})
    >>> if "hit_rate" in performance:
    ...     hit_rate = performance["hit_rate"]
    ...     if hit_rate < 70.0:
    ...         print("Cache hit rate below optimal threshold")
    
    >>> # Operational monitoring integration
    >>> async def monitor_cache_health():
    ...     status_response = await client.get("/internal/cache/status")
    ...     cache_status = status_response.json()
    ...     
    ...     health_indicators = []
    ...     if cache_status.get("redis", {}).get("status") != "connected":
    ...         health_indicators.append("redis_disconnected")
    ...     
    ...     memory_status = cache_status.get("memory", {}).get("status")
    ...     if memory_status not in ["normal", "optimal"]:
    ...         health_indicators.append("memory_pressure")
    ...     
    ...     performance = cache_status.get("performance", {})
    ...     hit_rate = performance.get("hit_rate", 0)
    ...     if hit_rate < 60.0:
    ...         health_indicators.append("low_hit_rate")
    ...     
    ...     return {
    ...         "healthy": len(health_indicators) == 0,
    ...         "issues": health_indicators,
    ...         "status_data": cache_status
    ...     }
    
    >>> # Error handling verification
    >>> # When cache service experiences issues
    >>> error_response = await client.get("/internal/cache/status")
    >>> if "error" in error_response.json():
    ...     error_info = error_response.json()["error"]
    ...     print(f"Cache status error: {error_info}")
    ...     # Status remains available with error information
    
    >>> # Capacity planning analysis
    >>> def analyze_cache_capacity(status_data):
    ...     redis_info = status_data.get("redis", {})
    ...     memory_info = status_data.get("memory", {})
    ...     
    ...     capacity_analysis = {
    ...         "redis_utilization": redis_info.get("memory_usage", "unknown"),
    ...         "memory_entries": memory_info.get("entries", 0),
    ...         "performance_trend": status_data.get("performance", {})
    ...     }
    ...     
    ...     # Identify capacity optimization opportunities
    ...     if memory_info.get("entries", 0) > 10000:
    ...         capacity_analysis["recommendation"] = "consider_memory_optimization"
    ...     
    ...     return capacity_analysis
    
    >>> # Infrastructure dashboard integration
    >>> async def cache_dashboard_data():
    ...     status = await client.get("/internal/cache/status").json()
    ...     return {
    ...         "redis_health": "🟢" if status.get("redis", {}).get("status") == "connected" else "🔴",
    ...         "memory_health": "🟢" if status.get("memory", {}).get("status") == "normal" else "🟡",
    ...         "hit_rate": f"{status.get('performance', {}).get('hit_rate', 0):.1f}%",
    ...         "last_updated": datetime.now().isoformat()
    ...     }

Note:
    This endpoint provides comprehensive cache infrastructure monitoring capabilities and
    implements robust error handling to ensure status visibility remains available even
    under cache system stress. It serves as the foundation for cache performance optimization,
    capacity planning, and operational monitoring integration while maintaining security
    through optional authentication for enhanced operational access control.

## invalidate_cache()

```python
async def invalidate_cache(pattern: str = Query(default='', description='Pattern to match for cache invalidation'), operation_context: str = Query(default='api_endpoint', description='Context for the invalidation operation'), cache_service: AIResponseCache = Depends(get_cache_service), api_key: str = Depends(verify_api_key_http)):
```

Invalidate cache entries matching the specified pattern.

Removes cache entries that match the provided pattern from the cache storage.
This operation is useful for clearing stale or outdated cache data, forcing
fresh data retrieval on subsequent requests. An empty pattern will invalidate
all cache entries.

Args:
    pattern (str, optional): Glob-style pattern to match cache keys for
        invalidation. Defaults to empty string which matches all entries.
        Examples: "user:*", "api:v1:*", "text:processing:*".
    operation_context (str, optional): Context identifier for tracking
        the source of invalidation operations. Defaults to "api_endpoint".
        Used for monitoring and auditing cache invalidation patterns.
    cache_service (AIResponseCache): Injected cache service dependency
        for performing cache invalidation operations.
    api_key (str): Required API key for authentication. Must be valid
        to perform cache invalidation operations.

Returns:
    Dict[str, str]: Confirmation message containing:
        - message: Success or failure message with pattern details

Raises:
    AuthenticationError: May raise authentication errors if API key is invalid.
        Cache operation errors are handled gracefully and returned in
        the response message rather than raising exceptions.

Example:
    >>> # POST /internal/cache/invalidate?pattern=user:123:*
    >>> {"message": "Cache invalidated for pattern: user:123:*"}

    >>> # POST /internal/cache/invalidate (invalidate all)
    >>> {"message": "Cache invalidated for pattern: "}

## get_invalidation_stats()

```python
async def get_invalidation_stats(cache_service: AIResponseCache = Depends(get_cache_service), api_key: str = Depends(optional_verify_api_key)):
```

Get cache invalidation frequency and pattern statistics.

Retrieves comprehensive statistics about cache invalidation operations
including frequency analysis, pattern identification, and performance
metrics. This data helps understand cache usage patterns and optimize
invalidation strategies.

Args:
    cache_service (AIResponseCache): Injected cache service dependency
        for accessing invalidation statistics and metrics.
    api_key (str, optional): Optional API key for authentication. If provided,
        must be valid for access to detailed invalidation statistics.

Returns:
    Dict[str, Any]: Invalidation statistics including:
        - frequency: Invalidation frequency by time period
        - patterns: Most common invalidation patterns
        - performance: Timing statistics for invalidation operations
        - trends: Temporal trends in invalidation behavior
        Empty dict returned if statistics are unavailable or on error.

Raises:
    None: This endpoint does not raise exceptions but returns empty
        statistics if data retrieval fails.

Example:
    >>> # GET /internal/cache/invalidation-stats
    >>> {
    ...     "frequency": {"hourly": 45, "daily": 1080},
    ...     "patterns": {"user:*": 0.35, "api:*": 0.28, "": 0.15},
    ...     "performance": {"avg_duration": 0.025, "max_duration": 0.156}
    ... }

## get_invalidation_recommendations()

```python
async def get_invalidation_recommendations(cache_service: AIResponseCache = Depends(get_cache_service), api_key: str = Depends(optional_verify_api_key)):
```

Get optimization recommendations based on cache invalidation patterns.

Analyzes cache invalidation patterns and usage statistics to provide
actionable recommendations for improving cache efficiency. Recommendations
may include pattern optimization, timing adjustments, and configuration
changes to reduce unnecessary invalidations.

Args:
    cache_service (AIResponseCache): Injected cache service dependency
        for accessing invalidation data and generating recommendations.
    api_key (str, optional): Optional API key for authentication. If provided,
        must be valid for access to invalidation recommendations.

Returns:
    Dict[str, List[str]]: Response containing:
        - recommendations: List of optimization suggestions based on
          analysis of invalidation patterns, frequency, and performance.
          Empty list returned if analysis fails or no recommendations available.

Raises:
    None: This endpoint does not raise exceptions but returns empty
        recommendations list if analysis fails.

Example:
    >>> # GET /internal/cache/invalidation-recommendations
    >>> {
    ...     "recommendations": [
    ...         "Consider using more specific patterns instead of wildcard invalidations",
    ...         "High frequency of user:* invalidations suggests reviewing user data caching strategy",
    ...         "Batch invalidation operations during low-traffic periods for better performance"
    ...     ]
    ... }

## get_cache_performance_metrics()

```python
async def get_cache_performance_metrics(api_key: str = Depends(optional_verify_api_key), performance_monitor: CachePerformanceMonitor = Depends(get_performance_monitor_http)) -> CachePerformanceResponse:
```

Get comprehensive cache performance metrics and statistics.

Retrieves detailed performance statistics from the cache system including
key generation metrics, cache operation performance, compression statistics,
memory usage information, and invalidation analytics. This endpoint provides
deep insights into cache efficiency and performance characteristics over the
configured retention period.

The metrics are collected over the configured retention period (default: 1 hour)
and are computed on-demand, which may cause brief CPU spikes during statistics
calculation. All metrics are automatically cleaned up to maintain system performance.

Args:
    api_key (str, optional): Optional API key for authentication. If provided,
        must be valid for access to detailed performance metrics.
    performance_monitor (CachePerformanceMonitor): Injected performance monitor
        dependency for accessing cache performance data and statistics computation.

Returns:
    CachePerformanceResponse: Comprehensive performance metrics including:
        - timestamp: When metrics were collected (ISO format string)
        - retention_hours: Data retention period in hours
        - cache_hit_rate: Cache hit rate percentage
        - total_cache_operations: Total cache operations performed
        - cache_hits: Number of successful cache hits
        - cache_misses: Number of cache misses
        - key_generation: Key generation timing and text length statistics
        - cache_operations: Cache operation performance by type (get, set, delete)
        - compression: Compression efficiency and storage savings metrics
        - memory_usage: Cache memory utilization and entry counts
        - invalidation: Cache invalidation frequency and patterns

Raises:
    InfrastructureError:
        - When performance monitor is unavailable, cache service errors occur,
          statistics computation fails, or response validation fails.
    ConfigurationError:
        - When cache monitoring is temporarily disabled or performance monitor
          methods are not available.

Example:
    >>> # GET /internal/cache/metrics
    >>> {
    ...     "timestamp": "2024-01-15T10:30:00.123456",
    ...     "retention_hours": 1,
    ...     "cache_hit_rate": 85.5,
    ...     "total_cache_operations": 150,
    ...     "cache_hits": 128,
    ...     "cache_misses": 22,
    ...     "key_generation": {
    ...         "total_operations": 75,
    ...         "avg_duration": 0.002,
    ...         "avg_text_length": 1250,
    ...         "slow_operations": 2
    ...     },
    ...     "cache_operations": {
    ...         "total_operations": 150,
    ...         "avg_duration": 0.0045,
    ...         "slow_operations": 5,
    ...         "by_operation_type": {
    ...             "get": {"count": 100, "avg_duration": 0.003},
    ...             "set": {"count": 50, "avg_duration": 0.007}
    ...         }
    ...     },
    ...     "compression": {
    ...         "total_operations": 25,
    ...         "avg_compression_ratio": 0.65,
    ...         "total_bytes_saved": 183500,
    ...         "overall_savings_percent": 35.0
    ...     }
    ... }

Note:
    This endpoint may take longer to respond when computing statistics for
    large datasets. Memory usage reporting includes process-level metrics.
    Statistics computation may cause brief CPU spikes during calculation.
