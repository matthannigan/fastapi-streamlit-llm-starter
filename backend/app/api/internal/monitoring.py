"""Internal monitoring endpoints for system health and performance metrics.

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

Classes:
    None: This module contains only router definitions and endpoint functions.

Functions:
    get_monitoring_health: Comprehensive health check of all monitoring subsystems.

Routes:
    GET /monitoring/health: Returns detailed health status of monitoring infrastructure.

Dependencies:
    FastAPI: Web framework for HTTP routing and dependency injection.
    Authentication: API key verification for secure access to monitoring data.
    Cache Service: Performance metrics and health status from cache infrastructure.
    Resilience Infrastructure: Circuit breaker and retry operation metrics.

Typical Usage Example:
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

Security:
    All endpoints require optional API key authentication via the X-API-Key header.
    This allows for flexible access control in different deployment environments
    while maintaining security for production monitoring.

Note:
    This module focuses exclusively on monitoring infrastructure health,
    not main application health. Use the `/health` endpoint for overall 
    application status and readiness checks.

Attributes:
    monitoring_router (APIRouter): FastAPI router instance configured with
        "/monitoring" prefix and "monitoring" tags for endpoint organization.
    logger (logging.Logger): Module-level logger for monitoring operations
        and error reporting.
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
                "GET /monitoring/health",
                "GET /cache/status",
                "GET /cache/metrics", 
                "GET /cache/invalidation-stats",
                "GET /resilience/health"
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
        use the `/health` endpoint instead.
        
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
            "GET /monitoring/health",
            "GET /cache/status", 
            "GET /cache/metrics",
            "GET /cache/invalidation-stats",
            "GET /resilience/health"
        ]
        
        return monitoring_health
        
    except Exception as e:
        logger.error(f"Monitoring health check failed: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get monitoring health: {str(e)}"
        )


 