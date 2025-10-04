"""
Domain Service: Application Health Check API

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
from app.schemas.health import HealthResponse
from app.core.config import settings
from app.dependencies import get_health_checker
from app.infrastructure.monitoring.health import SystemHealthStatus

health_router = APIRouter(prefix='/health', tags=['Health'])


@health_router.get('', response_model=HealthResponse, summary='System Health Check', responses={200: {'description': "Successful health check. Returns 'healthy' or 'degraded' based on component status.", 'content': {'application/json': {'examples': {'healthy': {'summary': 'All components healthy', 'value': {'status': 'healthy', 'timestamp': '2025-06-28T00:06:39.130848', 'version': '1.0.0', 'ai_model_available': True, 'resilience_healthy': True, 'cache_healthy': True}}, 'degraded': {'summary': 'One or more components degraded', 'value': {'status': 'degraded', 'timestamp': '2025-06-28T00:06:39.130848', 'version': '1.0.0', 'ai_model_available': False, 'resilience_healthy': None, 'cache_healthy': True}}, 'unhealthy': {'summary': 'Example of unhealthy components (mapped to degraded in public schema)', 'value': {'status': 'degraded', 'timestamp': '2025-06-28T00:06:39.130848', 'version': '1.0.0', 'ai_model_available': False, 'resilience_healthy': False, 'cache_healthy': False}}}}}}})
async def health_check(health_checker = Depends(get_health_checker)):
    """
    System health validation endpoint with multi-component monitoring and graceful degradation.
    
    Provides enterprise-grade health monitoring for critical application components with
    sophisticated health aggregation logic. Serves as the primary health validation interface
    for load balancers, monitoring systems, and operational dashboards while maintaining
    service availability under partial system failures.
    
    Args:
        health_checker: Infrastructure health checking service providing system component
                       validation, monitoring capabilities, and health status aggregation
                       across AI models, cache systems, and resilience infrastructure
    
    Returns:
        HealthResponse: Health status response containing:
        - status: Overall system health ("healthy" or "degraded") from component aggregation
        - ai_model_available: Boolean indicating AI model configuration and accessibility
        - resilience_healthy: Optional boolean for resilience infrastructure (None if unavailable)
        - cache_healthy: Optional boolean for cache system status (None if unavailable)
        - timestamp: ISO-formatted timestamp of health check execution
        - version: API version identifier for monitoring compatibility
    
    Raises:
        HTTPException: Never raised - implements comprehensive error handling with graceful
                      degradation to ensure availability under all system conditions
    
    Behavior:
        **Component Health Validation:**
        - Validates AI model configuration and API key accessibility
        - Checks resilience infrastructure including circuit breakers and failure detection
        - Monitors cache system status with Redis connectivity and memory cache validation
        - Aggregates individual component health into overall system status
    
        **Health Status Determination:**
        - Returns "healthy" when AI model available and no critical components fail
        - Returns "degraded" when AI model unavailable or critical infrastructure fails
        - Treats optional component unavailability (None values) as non-critical
        - Implements health aggregation logic balancing availability with functionality
    
        **Graceful Degradation:**
        - Continues operation when health checker infrastructure experiences failures
        - Provides fallback validation using direct configuration checks when needed
        - Maintains endpoint availability under all system conditions including partial failures
        - Ensures monitoring systems can always assess basic application health
    
        **Monitoring Integration:**
        - Provides structured response format optimized for automated monitoring systems
        - Supports load balancer health check requirements with consistent response patterns
        - Enables operational dashboard integration with comprehensive component visibility
        - Maintains backward compatibility with existing monitoring infrastructure
    
        **Performance Optimization:**
        - Executes health checks asynchronously for optimal response times
        - Implements efficient component validation with minimal system impact
        - Provides fast health status determination suitable for high-frequency monitoring
        - Minimizes resource utilization while maintaining comprehensive validation
    
    Examples:
        >>> # Healthy system response
        >>> response = await client.get("/v1/health")
        >>> data = response.json()
        >>> assert data["status"] == "healthy"
        >>> assert data["ai_model_available"] is True
        >>> assert data["cache_healthy"] is True
        >>> assert data["resilience_healthy"] is True
    
        >>> # Degraded system with AI model issues
        >>> response = await client.get("/v1/health")
        >>> data = response.json()
        >>> assert data["status"] == "degraded"
        >>> assert data["ai_model_available"] is False
        >>> assert data["cache_healthy"] is True  # Still operational
    
        >>> # Load balancer integration
        >>> async def check_service_health():
        ...     async with aiohttp.ClientSession() as session:
        ...         async with session.get("http://api:8000/v1/health") as resp:
        ...             data = await resp.json()
        ...             return data["status"] == "healthy"
    
        >>> # Monitoring with alerting
        >>> health = await client.get("/v1/health").json()
        >>> if health["status"] == "degraded":
        ...     await send_alert(f"System degraded: {health['status']}")
        >>> if not health["ai_model_available"]:
        ...     await send_critical_alert("AI model unavailable")
    
    Note:
        Endpoint designed for high-frequency monitoring without authentication requirements.
        Implements comprehensive error handling and graceful degradation to maintain availability
        under system stress or partial infrastructure failures. Health checks create temporary
        connections automatically cleaned up to prevent resource leaks.
    """
    ...
