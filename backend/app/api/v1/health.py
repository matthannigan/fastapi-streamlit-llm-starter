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

from fastapi import APIRouter
import logging

from app.schemas.health import (
    HealthResponse,
)

from app.core.config import settings

# Create a router for health endpoints
health_router = APIRouter(prefix="/health", tags=["Health"])

logger = logging.getLogger(__name__)


@health_router.get("", response_model=HealthResponse)
async def health_check():
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
    ai_healthy = bool(settings.gemini_api_key)
    resilience_healthy = None
    cache_healthy = None
    
    # Check resilience health
    try:
        from app.infrastructure.resilience import ai_resilience
        resilience_healthy = ai_resilience.is_healthy()
    except Exception:
        logger.warning("Resilience service is not available")
        resilience_healthy = None
    
    # Check cache health
    try:
        from app.infrastructure.cache import AIResponseCache
        
        # Create cache service instance manually (not using dependency injection)
        cache_service = AIResponseCache(
            redis_url=settings.redis_url,
            default_ttl=settings.cache_default_ttl,
            text_hash_threshold=settings.cache_text_hash_threshold,
            compression_threshold=settings.cache_compression_threshold,
            compression_level=settings.cache_compression_level,
            text_size_tiers=settings.cache_text_size_tiers,
            memory_cache_size=settings.cache_memory_cache_size
        )
        
        # Try to connect and get stats
        await cache_service.connect()
        cache_stats = await cache_service.get_cache_stats()
        
        # Determine cache health based on status indicators
        cache_healthy = (
            cache_stats.get("redis", {}).get("status") != "error" and
            cache_stats.get("memory", {}).get("status") != "unavailable" and
            cache_stats.get("performance", {}).get("status") != "unavailable" and
            "error" not in cache_stats
        )
                
    except Exception as e:
        logger.warning(f"Cache service is not available: {e}")
        cache_healthy = None
    
    # Overall health determination
    # Consider healthy if AI is available and no critical components are explicitly unhealthy
    # Allow for optional components (resilience, cache) to be None without affecting overall health
    overall_healthy = ai_healthy and (
        resilience_healthy is not False and cache_healthy is not False
    )
    
    return HealthResponse(
        status="healthy" if overall_healthy else "degraded",
        ai_model_available=ai_healthy,
        resilience_healthy=resilience_healthy,
        cache_healthy=cache_healthy
    )
