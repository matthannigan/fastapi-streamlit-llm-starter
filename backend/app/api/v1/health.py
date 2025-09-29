"""Domain Service: Application Health Check API

📚 **EXAMPLE IMPLEMENTATION** - Replace in your project  
💡 **Demonstrates infrastructure usage patterns**  
🔄 **Expected to be modified/replaced**

This module provides a comprehensive health check endpoint for the application,
demonstrating how to build monitoring endpoints that check multiple infrastructure
components. It serves as an example for implementing domain-level health monitoring
that aggregates infrastructure service status.

## Core Components

### API Endpoints
- `GET /v1/health`: Enhanced health check with comprehensive system monitoring

### Health Check Components
The health check evaluates three main components:
- **AI Model**: Verifies Google Gemini API key configuration
- **Resilience Infrastructure**: Checks circuit breakers and failure detection
- **Cache System**: Validates Redis connectivity and cache operations

### Health Status Algorithm
- **"healthy"**: AI model available and no critical component failures
- **"degraded"**: AI model unavailable or critical components explicitly failed
- **Optional Components**: Resilience and cache can be None without affecting overall health

## Dependencies & Integration

### Infrastructure Dependencies
- `app.infrastructure.resilience.ai_resilience`: Resilience service health checking
- `app.infrastructure.cache.AIResponseCache`: Cache service connectivity testing
- `app.core.config.settings`: Configuration access for component validation

### Domain Logic
- Component health aggregation and status determination
- Graceful degradation when optional services are unavailable
- Manual cache service instantiation for health validation

## Response Structure

### Successful Health Check
```json
{
    "status": "healthy",
    "timestamp": "2025-06-28T00:06:39.130848",
    "version": "1.0.0",
    "ai_model_available": true,
    "resilience_healthy": true,
    "cache_healthy": true
}
```

### Degraded Status Example
```json
{
    "status": "degraded", 
    "ai_model_available": false,
    "resilience_healthy": null,
    "cache_healthy": true
}
```

## Usage Examples

### Health Check Request
```bash
# No authentication required
curl http://localhost:8000/v1/health
```

### Load Balancer Configuration
```yaml
health_check:
  path: /v1/health
  expected_status: 200
  expected_body_contains: '"status":"healthy"'
```

## Implementation Notes

This service demonstrates domain-level health checking that:
- Aggregates multiple infrastructure component health status
- Uses manual service instantiation for isolated health testing
- Implements graceful degradation for optional components
- Provides structured responses for monitoring systems

**Replace in your project** - Customize the health checks and status logic
based on your specific infrastructure components and monitoring requirements.

## Developer Reference

For comprehensive documentation on the health check infrastructure, including
advanced usage patterns, performance optimization, testing strategies, and
production deployment guidance, see:

**📖 `docs/guides/developer/HEALTH_CHECKS.md`**
"""

from fastapi import APIRouter, Depends
import logging

from app.schemas.health import (
    HealthResponse,
)

from app.core.config import settings
from app.dependencies import get_health_checker
from app.infrastructure.monitoring.health import SystemHealthStatus

# Create a router for health endpoints
health_router = APIRouter(prefix="/health", tags=["Health"])

logger = logging.getLogger(__name__)


@health_router.get(
    "",
    response_model=HealthResponse,
    summary="System Health Check",
    responses={
        200: {
            "description": "Successful health check. Returns 'healthy' or 'degraded' based on component status.",
            "content": {
                "application/json": {
                    "examples": {
                        "healthy": {
                            "summary": "All components healthy",
                            "value": {
                                "status": "healthy",
                                "timestamp": "2025-06-28T00:06:39.130848",
                                "version": "1.0.0",
                                "ai_model_available": True,
                                "resilience_healthy": True,
                                "cache_healthy": True
                            }
                        },
                        "degraded": {
                            "summary": "One or more components degraded",
                            "value": {
                                "status": "degraded",
                                "timestamp": "2025-06-28T00:06:39.130848",
                                "version": "1.0.0",
                                "ai_model_available": False,
                                "resilience_healthy": None,
                                "cache_healthy": True
                            }
                        },
                        "unhealthy": {
                            "summary": "Example of unhealthy components (mapped to degraded in public schema)",
                            "value": {
                                "status": "degraded",
                                "timestamp": "2025-06-28T00:06:39.130848",
                                "version": "1.0.0",
                                "ai_model_available": False,
                                "resilience_healthy": False,
                                "cache_healthy": False
                            }
                        }
                    }
                }
            }
        }
    }
)
async def health_check(health_checker = Depends(get_health_checker)):
    """
    Comprehensive system health validation endpoint with multi-component monitoring and graceful degradation.
    
    This endpoint provides enterprise-grade health monitoring capabilities for all critical application
    components, implementing sophisticated health aggregation logic and graceful degradation patterns.
    It serves as the primary health validation interface for load balancers, monitoring systems, and
    operational dashboards while maintaining service availability even under partial system failures.
    
    Args:
        health_checker: Infrastructure health checking service dependency providing comprehensive
                       system component validation, monitoring capabilities, and health status
                       aggregation across AI models, cache systems, and resilience infrastructure
    
    Returns:
        HealthResponse: Comprehensive health status response containing:
                       - status: Overall system health ("healthy" or "degraded") based on component aggregation
                       - ai_model_available: Boolean indicating AI model configuration and accessibility
                       - resilience_healthy: Optional boolean for resilience infrastructure status (None if unavailable)
                       - cache_healthy: Optional boolean for cache system operational status (None if unavailable)
                       - timestamp: ISO-formatted timestamp of health check execution
                       - version: Current API version identifier for monitoring compatibility
    
    Raises:
        HTTPException: Never raised - endpoint implements comprehensive error handling with graceful
                      degradation to ensure health check availability under all system conditions
    
    Behavior:
        **Component Health Validation:**
        - Validates AI model configuration and API key accessibility for text processing operations
        - Checks resilience infrastructure including circuit breakers and failure detection systems  
        - Monitors cache system status with Redis connectivity and memory cache operational validation
        - Aggregates individual component health into overall system status determination
        
        **Health Status Determination:**
        - Returns "healthy" when AI model is available and no critical components report explicit failures
        - Returns "degraded" when AI model is unavailable or critical infrastructure components fail
        - Treats optional component unavailability (None values) as non-critical for overall health
        - Implements sophisticated health aggregation logic balancing availability with functionality
        
        **Graceful Degradation Patterns:**
        - Continues operation even when health checker infrastructure experiences failures
        - Provides fallback health validation using direct configuration checks when needed
        - Maintains endpoint availability under all system conditions including partial failures
        - Ensures monitoring systems can always assess basic application health status
        
        **Monitoring Integration:**
        - Provides structured response format optimized for automated monitoring systems
        - Supports load balancer health check requirements with consistent response patterns  
        - Enables operational dashboard integration with comprehensive component visibility
        - Maintains backward compatibility with existing monitoring infrastructure
        
        **Performance Optimization:**
        - Executes health checks asynchronously for optimal response times
        - Implements efficient component validation with minimal system impact
        - Provides fast health status determination suitable for high-frequency monitoring
        - Minimizes resource utilization while maintaining comprehensive validation coverage
    
    Examples:
        >>> # Healthy system response with all components operational
        >>> response = await client.get("/v1/health")
        >>> assert response.status_code == 200
        >>> data = response.json()
        >>> assert data["status"] == "healthy"
        >>> assert data["ai_model_available"] is True
        >>> assert data["cache_healthy"] is True
        >>> assert data["resilience_healthy"] is True
        >>> assert "timestamp" in data and "version" in data
        
        >>> # Degraded system with AI model issues
        >>> # Response when AI model is misconfigured
        >>> response = await client.get("/v1/health")
        >>> data = response.json()
        >>> assert data["status"] == "degraded"
        >>> assert data["ai_model_available"] is False
        >>> assert data["cache_healthy"] is True  # Cache still operational
        >>> assert data["resilience_healthy"] is True  # Resilience still operational
        
        >>> # Load balancer health check integration
        >>> import aiohttp
        >>> async def load_balancer_check():
        ...     async with aiohttp.ClientSession() as session:
        ...         async with session.get("http://api:8000/v1/health") as response:
        ...             if response.status == 200:
        ...                 data = await response.json()
        ...                 return data["status"] == "healthy"
        ...             return False
        
        >>> # Monitoring system integration with alerting
        >>> async def monitoring_health_check():
        ...     try:
        ...         response = await client.get("/v1/health")
        ...         health_data = response.json()
        ...         
        ...         # Alert on degraded status
        ...         if health_data["status"] == "degraded":
        ...             await send_alert(f"System degraded: {health_data}")
        ...         
        ...         # Component-specific monitoring
        ...         if not health_data["ai_model_available"]:
        ...             await send_critical_alert("AI model unavailable")
        ...         
        ...         return health_data
        ...     except Exception as e:
        ...         await send_alert(f"Health check failed: {e}")
        ...         return None
        
        >>> # Kubernetes liveness probe configuration
        >>> # livenessProbe:
        >>> #   httpGet:
        >>> #     path: /v1/health
        >>> #     port: 8000
        >>> #   initialDelaySeconds: 30
        >>> #   periodSeconds: 10
        >>> #   successThreshold: 1
        >>> #   failureThreshold: 3
        
        >>> # Operational dashboard integration
        >>> async def dashboard_health_status():
        ...     health = await client.get("/v1/health").json()
        ...     return {
        ...         "overall": health["status"],
        ...         "ai_service": "✅" if health["ai_model_available"] else "❌",
        ...         "cache": "✅" if health["cache_healthy"] else "❌" if health["cache_healthy"] is not None else "⚠️",
        ...         "resilience": "✅" if health["resilience_healthy"] else "❌" if health["resilience_healthy"] is not None else "⚠️",
        ...         "last_check": health["timestamp"]
        ...     }
    
    Note:
        This endpoint is designed for high-frequency monitoring and does not require authentication
        to ensure monitoring systems can always assess application health. The endpoint implements
        comprehensive error handling and graceful degradation to maintain availability even under
        system stress or partial infrastructure failures. Component health checks create temporary
        connections that are automatically cleaned up to prevent resource leaks.
    """
    try:
        # Use infrastructure health checker
        system_status: SystemHealthStatus = await health_checker.check_all_components()

        # Map to existing HealthResponse format for backward compatibility
        ai_healthy = any(
            c.name == "ai_model" and c.status.value == "healthy" for c in system_status.components
        )
        cache_comp = next((c for c in system_status.components if c.name == "cache"), None)
        resilience_comp = next((c for c in system_status.components if c.name == "resilience"), None)

        cache_healthy = None if cache_comp is None else (cache_comp.status.value == "healthy")
        resilience_healthy = None if resilience_comp is None else (resilience_comp.status.value == "healthy")

        overall_status = "healthy" if system_status.overall_status.value == "healthy" else "degraded"

        return HealthResponse(
            status=overall_status,
            ai_model_available=ai_healthy,
            resilience_healthy=resilience_healthy,
            cache_healthy=cache_healthy,
        )
    except Exception as e:
        # Graceful degradation: never fail the health endpoint due to infra issues
        logger.warning(f"Health checker failed; returning degraded status: {e}")
        ai_healthy = bool(settings.gemini_api_key)
        return HealthResponse(
            status="degraded",
            ai_model_available=ai_healthy,
            resilience_healthy=None,
            cache_healthy=None,
        )
