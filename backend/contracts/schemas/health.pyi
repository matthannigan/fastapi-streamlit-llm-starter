"""
Health Check Schema Definitions

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
"""

from pydantic import BaseModel, Field, field_serializer, FieldSerializationInfo
from datetime import datetime


class HealthResponse(BaseModel):
    """
    System health check response model for monitoring and operational visibility.
    
    Provides detailed health information about the application and critical dependencies,
    enabling load balancers, monitoring systems, and operational dashboards to make
    informed decisions about service availability and deployment readiness.
    
    Attributes:
        status: Overall system health status - "healthy" (all operational), "degraded"
               (partial functionality), or "unhealthy" (critical failures)
        timestamp: UTC timestamp when health check was performed, enabling frequency
                  analysis and stale check detection
        version: Application version string for deployment tracking, rollback decisions,
                and version-specific health correlation analysis
        ai_model_available: Boolean indicating AI model accessibility and functionality,
                          critical for text processing operations and service availability
        resilience_healthy: Optional health status of resilience patterns including
                          circuit breakers, retry mechanisms, and failure recovery systems
        cache_healthy: Optional health status of caching infrastructure including
                      Redis connectivity, memory cache, and cache performance
    
    State Management:
        - Immutable health snapshot through Pydantic model behavior
        - Thread-safe for concurrent health check operations
        - Automatic timestamp generation for accurate health timing
        - Consistent JSON serialization for monitoring system integration
        - Structured data format supporting health trend analysis and correlation
    
    Behavior:
        - Generates timestamp at health check execution time automatically
        - Serializes timestamp to ISO 8601 format for JSON compatibility
        - Provides sensible defaults for optional health indicators
        - Integrates with FastAPI's automatic OpenAPI documentation generation
        - Supports health check aggregation across multiple service instances
        - Enables health status correlation with performance metrics and alerting
    
    Examples:
        >>> # Basic healthy system
        >>> health = HealthResponse(
        ...     status="healthy",
        ...     ai_model_available=True,
        ...     version="1.0.0"
        ... )
        >>> assert health.status == "healthy"
        >>> assert health.ai_model_available is True
    
        >>> # Degraded system with cache issues
        >>> degraded = HealthResponse(
        ...     status="degraded",
        ...     ai_model_available=True,
        ...     resilience_healthy=True,
        ...     cache_healthy=False,  # Cache down but service functional
        ...     version="1.0.0"
        ... )
        >>> assert degraded.status == "degraded"
        >>> assert degraded.cache_healthy is False
    
        >>> # Complete system health
        >>> complete = HealthResponse(
        ...     status="healthy",
        ...     ai_model_available=True,
        ...     resilience_healthy=True,
        ...     cache_healthy=True,
        ...     version="1.2.3"
        ... )
        >>> json_data = complete.model_dump_json()
        >>> assert "timestamp" in json_data
    
        >>> # Load balancer health check
        >>> def service_healthy(response_data: dict) -> bool:
        ...     return (
        ...         response_data.get("status") == "healthy" and
        ...         response_data.get("ai_model_available") is True
        ...     )
    
        >>> # Monitoring system integration
        >>> health_data = health.model_dump()
        >>> alerts = []
        >>> if health_data["status"] == "degraded":
        ...     alerts.append("System degraded")
        >>> if not health_data.get("ai_model_available"):
        ...     alerts.append("AI model unavailable")
        
    """

    @field_serializer('timestamp')
    def serialize_timestamp(self, dt: datetime, _info: FieldSerializationInfo) -> str:
        """
        Serialize datetime to ISO 8601 format string for JSON compatibility.
        
        Converts Python datetime objects to standardized ISO 8601 format strings,
        ensuring consistent timestamp representation across different systems
        and monitoring platforms. Enables proper JSON serialization and
        timezone-aware timestamp handling.
        
        Args:
            dt: Python datetime object to serialize
            _info: Pydantic serialization context (unused)
        
        Returns:
            ISO 8601 formatted timestamp string (e.g., "2025-01-15T10:30:45.123456")
        """
        ...
