# Internal monitoring endpoints for system health and performance metrics.

This module provides FastAPI endpoints for monitoring various system components
including cache performance, resilience metrics, and monitoring infrastructure health.
The endpoints are designed for internal monitoring and diagnostics, requiring API key
authentication for access.

The module serves as the central hub for monitoring infrastructure health checks,
providing detailed insights into:
- Cache performance monitoring system status and metrics
- Cache service monitoring capabilities and Redis connectivity
- Resilience metrics collection (circuit breakers, retry operations)
- Monitoring data availability and integrity validation
- Component-level health status with operational metadata

This monitoring system is specifically designed for infrastructure observability
and should not be confused with main application health endpoints. It focuses
on the health of monitoring systems themselves rather than business logic components.

## Classes

None: This module contains only router definitions and endpoint functions.

## Functions

get_monitoring_health: Comprehensive health check of all monitoring subsystems.

## Routes

GET /internal/monitoring/health: Returns detailed health status of monitoring infrastructure.

## Dependencies

FastAPI: Web framework for HTTP routing and dependency injection.
Authentication: API key verification for secure access to monitoring data.
Cache Service: Performance metrics and health status from cache infrastructure.
Resilience Infrastructure: Circuit breaker and retry operation metrics.

## Typical Usage Example

The monitoring endpoints are automatically registered when the module is imported
and included in the main FastAPI application:

```python
from app.api.internal.monitoring import monitoring_router
app.include_router(monitoring_router, prefix="/internal")
```

To check monitoring system health:
```bash
curl -H "X-API-Key: your-api-key" http://localhost:8000/internal/monitoring/health
```

Returns comprehensive monitoring health report with component-level status.

## Security

All endpoints require optional API key authentication via the X-API-Key header.
This allows for flexible access control in different deployment environments
while maintaining security for production monitoring.

## Note

This module focuses exclusively on monitoring infrastructure health,
not main application health. Use the `/health` endpoint for overall
application status and readiness checks.

## Attributes

monitoring_router (APIRouter): FastAPI router instance configured with
"/monitoring" prefix and "monitoring" tags for endpoint organization.
logger (logging.Logger): Module-level logger for monitoring operations
and error reporting.
