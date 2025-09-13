---
sidebar_label: health
---

# Health Check Schema Definitions

  file_path: `backend/app/schemas/health.py`

This module defines Pydantic models for system health monitoring and status reporting.
The health schemas provide standardized response formats for health check endpoints,
enabling consistent monitoring across the application infrastructure.

## Models

**HealthResponse**: Comprehensive health status response including system components,
service availability, and performance indicators for monitoring and alerting systems.

## Usage

```python
from app.schemas.health import HealthResponse

# Create health response
health = HealthResponse(
    status="healthy",
    ai_model_available=True,
    resilience_healthy=True,
    cache_healthy=True
)
```

## Integration

This schema is used by health check endpoints to provide standardized status
information for load balancers, monitoring systems, and operational dashboards.

## HealthResponse

Comprehensive system health check response model for monitoring and operational visibility.

This model provides detailed health information about the application and all its critical
dependencies, enabling load balancers, monitoring systems, and operational dashboards to
make informed decisions about service availability and deployment readiness.

Attributes:
    status: Overall system health status indicator with three possible states:
           "healthy" (all systems operational), "degraded" (partial functionality),
           "unhealthy" (critical systems failing)
    timestamp: UTC timestamp when the health check was performed, enabling
              health check frequency analysis and stale check detection
    version: Application version string for deployment tracking, rollback decisions,
            and version-specific health correlation analysis
    ai_model_available: Boolean indicator of AI model accessibility and functionality,
                      critical for text processing operations and service availability
    resilience_healthy: Optional health status of resilience patterns including
                      circuit breakers, retry mechanisms, and failure recovery systems
    cache_healthy: Optional health status of caching infrastructure including
                  Redis connectivity, memory cache, and cache performance

State Management:
    - Immutable health snapshot (Pydantic model behavior)
    - Thread-safe for concurrent health check operations
    - Automatic timestamp generation for accurate health timing
    - Consistent JSON serialization for monitoring system integration
    - Structured data format for health trend analysis
    
Behavior:
    - Generates timestamp at health check execution time
    - Serializes timestamp to ISO 8601 format for JSON compatibility
    - Provides default values for optional health indicators
    - Integrates with FastAPI's automatic OpenAPI documentation
    - Supports health check aggregation across multiple service instances
    - Enables health status correlation with performance metrics
    
Examples:
    >>> # Basic healthy system status
    >>> healthy_status = HealthResponse(
    ...     status="healthy",
    ...     ai_model_available=True,
    ...     version="1.0.0"
    ... )
    >>> assert healthy_status.status == "healthy"
    >>> assert healthy_status.ai_model_available is True
    
    >>> # Degraded system with partial functionality
    >>> degraded_status = HealthResponse(
    ...     status="degraded",
    ...     ai_model_available=True,
    ...     resilience_healthy=True,
    ...     cache_healthy=False,  # Cache unavailable but service functional
    ...     version="1.0.0"
    ... )
    >>> assert degraded_status.status == "degraded"
    >>> assert degraded_status.cache_healthy is False
    
    >>> # Comprehensive health check with all components
    >>> comprehensive_health = HealthResponse(
    ...     status="healthy",
    ...     ai_model_available=True,
    ...     resilience_healthy=True,
    ...     cache_healthy=True,
    ...     version="1.2.3"
    ... )
    >>> health_json = comprehensive_health.model_dump_json()
    >>> assert "timestamp" in health_json
    
    >>> # Unhealthy system requiring attention
    >>> unhealthy_status = HealthResponse(
    ...     status="unhealthy",
    ...     ai_model_available=False,  # Critical AI service down
    ...     resilience_healthy=False,
    ...     cache_healthy=True,
    ...     version="1.0.0"
    ... )
    >>> assert unhealthy_status.status == "unhealthy"
    >>> assert unhealthy_status.ai_model_available is False

### serialize_timestamp()

```python
def serialize_timestamp(self, dt: datetime, _info):
```

Serialize datetime to ISO format string.
