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


@health_router.get("", response_model=HealthResponse)
async def health_check(health_checker = Depends(get_health_checker)):
    """Enhanced health check endpoint with comprehensive system monitoring.
    
    Performs health checks on all critical application components including AI model
    configuration, resilience infrastructure, and cache system status. This endpoint
    provides a comprehensive view of system health and can be used for monitoring,
    load balancer health checks, and operational dashboards.
    
    The health check evaluates three main components:
    
    - **AI Model**: Verifies that the Google Gemini API key is properly configured
      and available for text processing operations.
    - **Resilience Infrastructure**: Checks the operational status of circuit breakers,
      failure detection mechanisms, and resilience orchestration services.
    - **Cache System**: Validates Redis connectivity, memory cache operations, and
      overall cache service availability with graceful degradation support.
    
    The overall system status is determined as "healthy" when the AI model is available
    and no critical components report explicit failures. Optional components (resilience
    and cache services) may be unavailable (None) without affecting overall system
    health, as the application can continue operating with reduced functionality.
    
    Returns:
        HealthResponse: A comprehensive health status response containing:
            - status (str): Overall system health status, either "healthy" or "degraded"
            - ai_model_available (bool): Whether the AI model is properly configured
            - resilience_healthy (Optional[bool]): Resilience infrastructure status,
              None if service is unavailable
            - cache_healthy (Optional[bool]): Cache system operational status,
              None if service is unavailable  
            - timestamp (datetime): When the health check was performed (ISO format)
            - version (str): Current API version identifier
    
    Raises:
        Exception: Internal errors are caught and handled gracefully. Component
            failures result in None values rather than endpoint failures, ensuring
            the health check remains available even when subsystems are down.
    
    Example:
        >>> # GET /health
        >>> {
        ...   "status": "healthy",
        ...   "timestamp": "2025-06-28T00:06:39.130848",
        ...   "version": "1.0.0",
        ...   "ai_model_available": true,
        ...   "resilience_healthy": true,
        ...   "cache_healthy": true
        ... }
        
    Note:
        This endpoint does not require authentication and should be used by monitoring
        systems, load balancers, and operational tools. Cache health checks create
        temporary connections that are automatically cleaned up.
    """
    # Use infrastructure health checker
    system_status: SystemHealthStatus = await health_checker.check_all_components()

    # Map to existing HealthResponse format for backward compatibility
    ai_healthy = any(c.name == "ai_model" and c.status.value == "healthy" for c in system_status.components)
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
