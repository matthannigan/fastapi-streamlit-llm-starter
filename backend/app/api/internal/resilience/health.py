"""

### health.py (3 endpoints)
- GET  /resilience/health - get_resilience_health
- GET  /resilience/metrics - get_resilience_metrics  
- GET  /resilience/dashboard - get_resilience_dashboard

"""

import json
import logging
import os

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, List, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from app.config import Settings, settings
from app.infrastructure.security.auth import verify_api_key, optional_verify_api_key
from app.infrastructure.resilience.orchestrator import ai_resilience
from app.services.text_processor import TextProcessorService
from app.api.v1.deps import get_text_processor
from app.infrastructure.resilience.presets import preset_manager, PresetManager
from app.infrastructure.resilience.performance_benchmarks import performance_benchmark
from app.infrastructure.resilience.config_validator import config_validator, ValidationResult


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/resilience", tags=["resilience"])

@router.get("/health")
async def get_resilience_health():
    """
    Get resilience service health status.
    
    Returns:
        Health status with circuit breaker information
    """
    try:
        health_status = ai_resilience.get_health_status()
        is_healthy = ai_resilience.is_healthy()
        
        return {
            "healthy": is_healthy,
            "status": "healthy" if is_healthy else "degraded",
            "details": health_status
        }
        
    except Exception as e:
        logger.error(f"Error getting health status: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get health status: {str(e)}")

class ResilienceMetricsResponse(BaseModel):
    """Resilience service metrics response."""
    operations: Dict[str, Dict[str, Any]]
    circuit_breakers: Dict[str, Dict[str, Any]]
    summary: Dict[str, Any]

@router.get("/metrics", response_model=ResilienceMetricsResponse)
async def get_resilience_metrics(
    api_key: str = Depends(verify_api_key)
    ) -> ResilienceMetricsResponse:
    """
    Get current resilience service metrics.
    
    Returns:
        Comprehensive metrics about resilience operations and circuit breakers
    """
    try:
        metrics = ai_resilience.get_all_metrics()
        return ResilienceMetricsResponse(**metrics)
        
    except Exception as e:
        logger.error(f"Error getting resilience metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get resilience metrics: {str(e)}"
        )