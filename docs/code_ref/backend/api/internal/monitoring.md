# Infrastructure Service: Monitoring System Health API

🏗️ **STABLE API** - Changes affect all template users
📋 **Minimum test coverage**: 90%
🔧 **Configuration-driven behavior**

This module provides comprehensive FastAPI endpoints for monitoring the health and
performance of monitoring infrastructure components. It serves as the central hub
for infrastructure observability, focusing on the health of monitoring systems
themselves rather than business logic components.

## Core Components

### API Endpoints
- `GET /internal/monitoring/health`: Comprehensive health check of all monitoring subsystems (optional auth)

### Monitoring Subsystems
The health endpoint performs checks on three critical monitoring components:

1. **Cache Performance Monitor**: Validates cache performance tracking capabilities
- Checks `cache_service.performance_monitor.get_performance_stats()`
- Monitors operation tracking and recent data availability
- Validates performance metrics collection integrity

2. **Cache Service Monitoring**: Verifies cache service health and connectivity
- Validates Redis connectivity via `cache_service.get_cache_stats()`
- Monitors memory usage tracking capabilities
- Checks cache service operational status

3. **Resilience Monitoring**: Assesses resilience metrics collection
- Imports and validates `app.infrastructure.resilience.ai_resilience`
- Checks circuit breaker metrics availability via `get_all_metrics()`
- Monitors retry operation tracking capabilities

### Health Status Algorithm
The system uses a cascading health status determination:
- **"healthy"**: All components operational with no errors
- **"degraded"**: One or more components failed but system remains functional
- **"unhealthy"**: Critical failures or complete monitoring unavailability

## Dependencies & Integration

### Infrastructure Dependencies
- `AIResponseCache`: Cache service with performance monitoring capabilities
- `app.infrastructure.resilience.ai_resilience`: Resilience metrics collection
- **Security**: Optional API key verification for access control
- **Logging**: Structured logging with warning and error context

### FastAPI Dependencies
- `get_cache_service()`: Injected cache service with monitoring capabilities
- `optional_verify_api_key()`: Optional authentication for flexible access control

### Runtime Imports
- Dynamic import of resilience infrastructure for metrics validation
- Error-safe component checking with graceful degradation

## Error Handling Patterns

### Graceful Degradation
- Individual component failures do not prevent overall health reporting
- Failed components are marked as "degraded" with error details
- System continues operating with partial monitoring capabilities

### Exception Handling
- Component-level try-catch blocks for isolated error handling
- Warning-level logging for component failures (non-critical)
- Error-level logging for catastrophic monitoring failures

### HTTP Status Codes
- `200 OK`: Successful health check (may include degraded components)
- `500 Internal Server Error`: Complete monitoring system failure

## Response Structure

### Successful Health Check
```json
{
"status": "healthy|degraded|unhealthy",
"timestamp": "2024-01-15T10:30:00.123456",
"components": {
"cache_performance_monitor": {
"status": "healthy",
"total_operations_tracked": 1250,
"has_recent_data": true
},
"cache_service_monitoring": {
"status": "healthy",
"redis_monitoring": "connected",
"memory_monitoring": "available"
},
"resilience_monitoring": {
"status": "healthy",
"circuit_breaker_tracked": true,
"retry_metrics_available": true
}
},
"available_endpoints": [
"GET /internal/monitoring/health",
"GET /internal/cache/status",
"GET /internal/cache/metrics",
"GET /internal/cache/invalidation-stats",
"GET /internal/resilience/health"
]
}
```

### Component Failure Response
```json
{
"status": "degraded",
"components": {
"cache_performance_monitor": {
"status": "degraded",
"error": "Performance metrics collection temporarily unavailable"
}
}
}
```

## Usage Examples

### Integration with FastAPI Application
```python
from app.api.internal.monitoring import monitoring_router
app.include_router(monitoring_router, prefix="/internal")
```

### Health Check Request
```bash
# With authentication
curl -H "X-API-Key: your-api-key" http://localhost:8000/internal/monitoring/health

# Without authentication (if configured)
curl http://localhost:8000/internal/monitoring/health
```

## Monitoring Architecture

### Infrastructure Focus
This module monitors the monitoring infrastructure itself, providing:
- **Meta-monitoring**: Health of monitoring systems
- **Component isolation**: Individual subsystem health tracking
- **Operational visibility**: Real-time monitoring system status

### Relationship to Other Endpoints
- **Complements** `/health` (main application health)
- **Aggregates** `/internal/cache/*` and `/internal/resilience/*` endpoints
- **Provides** centralized monitoring infrastructure status

### Security Model
- **Optional Authentication**: Flexible access control for different environments
- **Internal Access**: Designed for internal monitoring and diagnostics
- **Production Ready**: Secure monitoring for production deployments

## Module Attributes

- `monitoring_router` (APIRouter): FastAPI router with "/monitoring" prefix and "System Monitoring" tags
- `logger` (logging.Logger): Module-level logger for monitoring operations and error reporting

**Change with caution** - This infrastructure service provides stable monitoring
APIs used across the application. Ensure backward compatibility and comprehensive
testing for any modifications.
