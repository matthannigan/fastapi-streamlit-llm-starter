"""Health Check Schema Definitions

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

from typing import Optional
from pydantic import BaseModel, Field, field_serializer
from datetime import datetime

class HealthResponse(BaseModel):
    """
    System health check response model.
    
    Provides comprehensive health information about the application and its dependencies,
    including AI model availability, resilience patterns status, and cache system health.
    
    Attributes:
        status (str): Overall system health status ("healthy", "degraded", "unhealthy").
        timestamp (datetime): When the health check was performed.
        version (str): Application version for deployment tracking.
        ai_model_available (bool): Whether AI models are accessible and functional.
        resilience_healthy (bool, optional): Health status of resilience patterns.
        cache_healthy (bool, optional): Health status of caching system.
    
    Example:
        ```json
        {
            "status": "healthy",
            "timestamp": "2025-01-12T10:30:45.123456",
            "version": "1.0.0",
            "ai_model_available": true,
            "resilience_healthy": true,
            "cache_healthy": true
        }
        ```
    """
    status: str = Field(default="healthy", description="Overall system health status")
    timestamp: datetime = Field(default_factory=datetime.now, description="Health check timestamp")
    version: str = Field(default="1.0.0", description="Application version")
    ai_model_available: bool = Field(default=True, description="AI model accessibility status")
    resilience_healthy: Optional[bool] = Field(default=None, description="Resilience patterns health")
    cache_healthy: Optional[bool] = Field(default=None, description="Cache system health")

    @field_serializer('timestamp')
    def serialize_timestamp(self, dt: datetime, _info):
        """Serialize datetime to ISO format string."""
        return dt.isoformat()
