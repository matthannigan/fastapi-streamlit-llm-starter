"""
Pydantic model for health check.
"""

from typing import Optional
from pydantic import BaseModel, Field, field_serializer
from datetime import datetime

class HealthResponse(BaseModel):
    """Health check response model2."""
    status: str = "healthy"
    timestamp: datetime = Field(default_factory=datetime.now)
    version: str = "1.0.0"
    ai_model_available: bool = True
    resilience_healthy: Optional[bool] = None
    cache_healthy: Optional[bool] = None

    @field_serializer('timestamp')
    def serialize_timestamp(self, dt: datetime, _info):
        """Serialize datetime to ISO format string."""
        return dt.isoformat()
