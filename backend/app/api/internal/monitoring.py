"""Internal monitoring endpoints for system health and performance metrics.

This module provides FastAPI endpoints for monitoring various system components
including cache performance, resilience metrics, and monitoring infrastructure health.
The endpoints are designed for internal monitoring and diagnostics, requiring API key
authentication for access.

The module exposes detailed health information about:
    - Cache performance monitoring system
    - Cache service monitoring capabilities  
    - Resilience metrics collection (circuit breakers, retry operations)
    - Monitoring data availability and integrity

Routes:
    GET /monitoring/health: Comprehensive health check of all monitoring subsystems

Dependencies:
    - FastAPI for HTTP routing
    - Authentication via API key verification
    - Cache service for performance metrics
    - Resilience infrastructure for circuit breaker metrics

Example:
    To check monitoring system health:
    GET /monitoring/health
    
    Returns detailed component-level health status with timestamps and metrics.

Note:
    This module focuses specifically on monitoring infrastructure health,
    not the main application health. Use /health for overall application status.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from app.infrastructure.security.auth import optional_verify_api_key
from app.dependencies import get_cache_service
from app.infrastructure.cache import AIResponseCache
import logging
from datetime import datetime

# Create a router for monitoring endpoints
monitoring_router = APIRouter(prefix="/monitoring", tags=["monitoring"])

logger = logging.getLogger(__name__)


@monitoring_router.get("/health")
async def get_monitoring_health(
    api_key: str = Depends(optional_verify_api_key),
    cache_service: AIResponseCache = Depends(get_cache_service)
):
    """
    Get the health status of the monitoring subsystems.
    
    This endpoint specifically checks the health of monitoring infrastructure
    components, not the main application. Use /health for overall app health.
    
    Validates:
    - Cache performance monitoring system
    - Metrics collection functionality  
    - Monitoring data availability
    - Resilience metrics collection
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


 