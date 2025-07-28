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
