# Cache infrastructure REST API endpoints.

This module provides comprehensive REST API endpoints for managing and monitoring
the AI response cache infrastructure. It includes endpoints for cache status
monitoring, cache invalidation, performance metrics collection, and cache
optimization recommendations.

The module defines Pydantic models for structured cache performance data and
implements robust error handling with appropriate HTTP status codes. All
endpoints support optional API key authentication for security.

## Endpoints

GET  /cache/status: Retrieve current cache status and basic statistics
POST /cache/invalidate: Invalidate cache entries matching a pattern
GET  /cache/invalidation-stats: Get cache invalidation frequency statistics
GET  /cache/invalidation-recommendations: Get optimization recommendations
GET  /cache/metrics: Get comprehensive cache performance metrics

## Performance Metrics

- Key generation timing and text length statistics
- Cache operation performance by type (get, set, delete)
- Compression efficiency and storage savings metrics
- Memory usage and invalidation pattern analysis
- Hit/miss rates and slow operation identification

## Dependencies

- AIResponseCache: Core cache service for operations
- CachePerformanceMonitor: Performance metrics collection
- Security: API key verification for protected endpoints

## Example

To get comprehensive cache metrics:
GET /api/internal/cache/metrics

To invalidate all cache entries:
POST /api/internal/cache/invalidate?pattern=

## Note

Cache performance metrics are computed on-demand and may cause brief
CPU spikes during statistics calculation. Metrics are automatically
cleaned up based on the configured retention period.
