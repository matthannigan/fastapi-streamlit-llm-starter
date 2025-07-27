"""Infrastructure Service: Monitoring System Health API

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
"""

from fastapi import APIRouter, Depends, HTTPException, status
from app.infrastructure.security.auth import optional_verify_api_key
from app.dependencies import get_cache_service
from app.infrastructure.cache import AIResponseCache
import logging
from datetime import datetime

# Create a router for monitoring endpoints
monitoring_router = APIRouter(prefix="/monitoring", tags=["System Monitoring"])

logger = logging.getLogger(__name__)


@monitoring_router.get("/health")
async def get_monitoring_health(
    api_key: str = Depends(optional_verify_api_key),
    cache_service: AIResponseCache = Depends(get_cache_service)
):
    """Get comprehensive health status of all monitoring subsystems.
    
    This endpoint performs health checks on monitoring infrastructure components
    including cache performance monitoring, metrics collection, and resilience
    systems. It provides detailed component-level status information for
    operational monitoring and diagnostics.
    
    Args:
        api_key (str): Optional API key for authentication. Obtained via dependency
            injection from optional_verify_api_key function.
        cache_service (AIResponseCache): Cache service instance for monitoring
            cache performance metrics. Obtained via dependency injection.
    
    Returns:
        dict: Comprehensive monitoring health report containing:
            - status (str): Overall health status ("healthy", "degraded", "unhealthy")
            - timestamp (str): ISO formatted timestamp of the health check
            - components (dict): Detailed status of each monitoring component:
                - cache_performance_monitor: Cache performance tracking status
                - cache_service_monitoring: Cache service health and capabilities
                - resilience_monitoring: Circuit breaker and retry metrics status
            - available_endpoints (list): List of available monitoring endpoints
    
    Raises:
        HTTPException: 500 Internal Server Error if the monitoring health check
            fails catastrophically or if critical monitoring components are
            completely unavailable.
    
    Examples:
        Successful response:
        ```json
        {
            "status": "healthy",
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
        
        Degraded response (partial failures):
        ```json
        {
            "status": "degraded",
            "timestamp": "2024-01-15T10:30:00.123456",
            "components": {
                "cache_performance_monitor": {
                    "status": "degraded",
                    "error": "Performance metrics collection temporarily unavailable"
                }
            }
        }
        ```
    
    Note:
        This endpoint specifically monitors the health of monitoring infrastructure,
        not the main application components. For overall application health,
        use the versioned public `/health` endpoint instead.
        
        The endpoint uses optional API key authentication, making it accessible
        for internal monitoring while maintaining security for production
        environments.
    """
    try:
        # Initialize with default timestamp
        monitoring_health = {
            "status": "healthy",
            "timestamp": datetime.now().isoformat(),
            "components": {}
        }
        
        # Check cache performance monitoring
        try:
            cache_stats = cache_service.performance_monitor.get_performance_stats()
            monitoring_health["components"]["cache_performance_monitor"] = {
                "status": "healthy",
                "total_operations_tracked": cache_stats.get("total_cache_operations", 0),
                "has_recent_data": len(cache_service.performance_monitor.cache_operation_times) > 0
            }
            # Update timestamp from performance stats if available
            if "timestamp" in cache_stats:
                monitoring_health["timestamp"] = str(cache_stats["timestamp"])
        except Exception as e:
            logger.warning(f"Cache performance monitor check failed: {e}")
            monitoring_health["components"]["cache_performance_monitor"] = {
                "status": "degraded",
                "error": str(e)
            }
            monitoring_health["status"] = "degraded"
        
        # Check cache service monitoring capabilities
        try:
            cache_service_stats = await cache_service.get_cache_stats()
            monitoring_health["components"]["cache_service_monitoring"] = {
                "status": "healthy",
                "redis_monitoring": cache_service_stats.get("redis", {}).get("status", "unknown"),
                "memory_monitoring": "available" if "memory" in cache_service_stats else "unavailable"
            }
        except Exception as e:
            logger.warning(f"Cache service monitoring check failed: {e}")
            monitoring_health["components"]["cache_service_monitoring"] = {
                "status": "degraded", 
                "error": str(e)
            }
            monitoring_health["status"] = "degraded"
        
        # Check resilience metrics collection
        try:
            from app.infrastructure.resilience import ai_resilience
            resilience_stats = ai_resilience.get_all_metrics()
            monitoring_health["components"]["resilience_monitoring"] = {
                "status": "healthy",
                "circuit_breaker_tracked": len(resilience_stats.get("circuit_breakers", {})) > 0,
                "retry_metrics_available": len(resilience_stats.get("operations", {})) > 0
            }
        except Exception as e:
            logger.warning(f"Resilience monitoring check failed: {e}")
            monitoring_health["components"]["resilience_monitoring"] = {
                "status": "degraded",
                "error": str(e)
            }
            monitoring_health["status"] = "degraded"
        
        # Add available monitoring endpoints
        monitoring_health["available_endpoints"] = [
            "GET /internal/monitoring/health",
            "GET /internal/cache/status", 
            "GET /internal/cache/metrics",
            "GET /internal/cache/invalidation-stats",
            "GET /internal/resilience/health"
        ]
        
        return monitoring_health
        
    except Exception as e:
        logger.error(f"Monitoring health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get monitoring health: {str(e)}"
        )


 