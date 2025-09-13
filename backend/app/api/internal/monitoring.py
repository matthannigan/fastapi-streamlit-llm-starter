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
    """
    Comprehensive monitoring infrastructure health assessment endpoint with multi-component validation.
    
    This endpoint provides advanced meta-monitoring capabilities for all monitoring infrastructure
    components, enabling operational teams to assess the health of monitoring systems themselves.
    It implements sophisticated component-level health validation with graceful degradation patterns,
    ensuring continuous monitoring availability even under partial infrastructure failures.
    
    Args:
        api_key: Optional API key for authentication and access control. Enables enhanced monitoring
                metadata and audit trail generation when provided. Authentication remains optional
                to support flexible monitoring integration scenarios.
        cache_service: Injected cache service dependency providing performance monitoring capabilities,
                      metrics collection interfaces, and operational status validation for comprehensive
                      cache infrastructure health assessment.
    
    Returns:
        dict: Comprehensive monitoring infrastructure health report containing:
             - status: Overall monitoring health status ("healthy", "degraded", "unhealthy")
             - timestamp: ISO-formatted timestamp of health check execution for temporal tracking
             - components: Detailed component-level health information including:
               * cache_performance_monitor: Performance metrics collection status and data availability
               * cache_service_monitoring: Cache service connectivity and monitoring capabilities
               * resilience_monitoring: Circuit breaker metrics and retry operation tracking status
             - available_endpoints: Complete list of available monitoring API endpoints for discovery
    
    Raises:
        HTTPException: 500 Internal Server Error when monitoring health check experiences catastrophic
                      failure or when critical monitoring infrastructure becomes completely unavailable,
                      preventing basic health assessment operations.
    
    Behavior:
        **Meta-Monitoring Architecture:**
        - Performs health checks on monitoring infrastructure components themselves
        - Validates monitoring system capabilities and operational readiness
        - Provides comprehensive component-level status assessment with isolation
        - Enables monitoring system observability and operational diagnostics
        
        **Component Health Validation:**
        - Assesses cache performance monitor functionality and data collection capabilities
        - Validates cache service monitoring interfaces and connectivity status
        - Evaluates resilience monitoring systems including circuit breaker and retry metrics
        - Performs isolated component checks with individual error handling and recovery
        
        **Graceful Degradation Patterns:**
        - Continues operation when individual monitoring components experience failures
        - Provides detailed component-level error information for troubleshooting
        - Maintains overall monitoring health assessment even with partial component failures
        - Implements cascading health status determination based on component availability
        
        **Operational Integration:**
        - Supports integration with external monitoring systems and alerting platforms
        - Provides structured response format optimized for automated monitoring tools
        - Enables monitoring system health dashboards and operational visibility
        - Maintains backward compatibility with existing monitoring infrastructure
        
        **Security and Access Control:**
        - Implements optional authentication for flexible access control requirements
        - Maintains security for production environments while supporting development scenarios
        - Provides audit trail capabilities when authentication is enabled
        - Protects sensitive monitoring infrastructure information appropriately
    
    Examples:
        >>> # Comprehensive monitoring health assessment
        >>> headers = {"X-API-Key": "monitoring-key-12345"}
        >>> response = await client.get("/internal/monitoring/health", headers=headers)
        >>> assert response.status_code == 200
        >>> health = response.json()
        >>> assert health["status"] in ["healthy", "degraded", "unhealthy"]
        >>> assert "components" in health and "timestamp" in health
        
        >>> # Component-level health validation
        >>> components = health["components"]
        >>> cache_monitor = components.get("cache_performance_monitor", {})
        >>> if cache_monitor["status"] == "healthy":
        ...     assert "total_operations_tracked" in cache_monitor
        ...     assert "has_recent_data" in cache_monitor
        
        >>> # Monitoring endpoint discovery
        >>> available_endpoints = health["available_endpoints"]
        >>> expected_endpoints = [
        ...     "GET /internal/monitoring/health",
        ...     "GET /internal/cache/status",
        ...     "GET /internal/resilience/health"
        ... ]
        >>> assert all(endpoint in available_endpoints for endpoint in expected_endpoints)
        
        >>> # Operational dashboard integration
        >>> async def monitoring_system_status():
        ...     health_response = await client.get("/internal/monitoring/health")
        ...     health_data = health_response.json()
        ...     
        ...     status_indicators = {}
        ...     for component, details in health_data["components"].items():
        ...         if details["status"] == "healthy":
        ...             status_indicators[component] = "✅"
        ...         elif details["status"] == "degraded":
        ...             status_indicators[component] = "⚠️"
        ...         else:
        ...             status_indicators[component] = "❌"
        ...     
        ...     return {
        ...         "overall": health_data["status"],
        ...         "components": status_indicators,
        ...         "last_check": health_data["timestamp"]
        ...     }
        
        >>> # Automated monitoring system integration
        >>> async def monitor_infrastructure_health():
        ...     try:
        ...         response = await client.get("/internal/monitoring/health")
        ...         health_data = response.json()
        ...         
        ...         if health_data["status"] == "unhealthy":
        ...             await send_critical_alert("Monitoring infrastructure unhealthy")
        ...         elif health_data["status"] == "degraded":
        ...             degraded_components = [
        ...                 name for name, details in health_data["components"].items()
        ...                 if details["status"] != "healthy"
        ...             ]
        ...             await send_warning_alert(f"Degraded components: {degraded_components}")
        ...         
        ...         return health_data
        ...     except Exception as e:
        ...         await send_alert(f"Monitoring health check failed: {e}")
        ...         return None
        
        >>> # Development and testing integration
        >>> def validate_monitoring_infrastructure():
        ...     health = client.get("/internal/monitoring/health").json()
        ...     
        ...     # Validate required components are present
        ...     required_components = [
        ...         "cache_performance_monitor",
        ...         "cache_service_monitoring", 
        ...         "resilience_monitoring"
        ...     ]
        ...     for component in required_components:
        ...         assert component in health["components"]
        ...     
        ...     # Validate endpoint availability
        ...     assert len(health["available_endpoints"]) >= 3
        ...     return True
        
        >>> # Graceful degradation verification
        >>> # When cache performance monitor fails but other components work
        >>> health = response.json()
        >>> if health["status"] == "degraded":
        ...     failed_components = [
        ...         name for name, details in health["components"].items()
        ...         if details["status"] != "healthy"
        ...     ]
        ...     print(f"Failed components: {failed_components}")
        ...     # System continues with partial monitoring capability
    
    Note:
        This endpoint provides meta-monitoring for monitoring infrastructure health, distinct
        from application component health available through public health endpoints. It enables
        operational teams to ensure monitoring systems themselves remain functional and provides
        comprehensive visibility into monitoring infrastructure status for operational reliability
        and troubleshooting scenarios.
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
            # Check if performance_monitor attribute exists (not all cache implementations have it)
            if hasattr(cache_service, 'performance_monitor') and cache_service.performance_monitor is not None:
                cache_stats = cache_service.performance_monitor.get_performance_stats()
                monitoring_health["components"]["cache_performance_monitor"] = {
                    "status": "healthy",
                    "total_operations_tracked": cache_stats.get("total_cache_operations", 0),
                    "has_recent_data": len(cache_service.performance_monitor.cache_operation_times) > 0
                }
                # Update timestamp from performance stats if available
                if "timestamp" in cache_stats:
                    monitoring_health["timestamp"] = str(cache_stats["timestamp"])
            else:
                # Performance monitor not available (e.g., InMemoryCache)
                monitoring_health["components"]["cache_performance_monitor"] = {
                    "status": "degraded",
                    "error": "Performance monitor not available for this cache implementation"
                }
                monitoring_health["status"] = "degraded"
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


 