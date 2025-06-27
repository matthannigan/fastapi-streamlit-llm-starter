"""
Monitoring endpoints for cache performance metrics and system monitoring.

This module provides endpoints for exposing cache performance statistics
and other monitoring-related functionality.
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
            resilience_stats = ai_resilience.get_stats()
            monitoring_health["components"]["resilience_monitoring"] = {
                "status": "healthy",
                "circuit_breaker_tracked": "failures" in resilience_stats,
                "retry_metrics_available": "retries" in resilience_stats
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


 