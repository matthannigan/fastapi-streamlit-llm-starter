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
