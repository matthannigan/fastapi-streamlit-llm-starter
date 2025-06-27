"""Resilience circuit breaker management and monitoring REST API endpoints.

This module provides REST API endpoints for monitoring and managing circuit
breakers within the resilience infrastructure. Circuit breakers are critical
components that protect services from cascading failures by detecting and
isolating failing operations, providing real-time status monitoring and
administrative control capabilities.

The module implements comprehensive circuit breaker management with real-time
status monitoring, detailed state analysis, and administrative reset
capabilities. All endpoints provide extensive information about circuit
breaker health and operational status.

Endpoints:
    GET /resilience/circuit-breakers: Get status of all circuit breakers
    GET /resilience/circuit-breakers/{breaker_name}: Get detailed information for specific breaker
    POST /resilience/circuit-breakers/{breaker_name}/reset: Reset circuit breaker to closed state

Circuit Breaker Management Features:
    - Real-time circuit breaker status monitoring
    - Detailed state analysis (open, closed, half-open)
    - Failure count tracking and threshold management
    - Last failure time monitoring and analysis
    - Administrative reset capabilities for operational control
    - Comprehensive metrics collection and reporting

Circuit Breaker States:
    - Closed: Normal operation, requests pass through
    - Open: Failure threshold exceeded, requests blocked
    - Half-Open: Testing phase, limited requests allowed
    - State transition monitoring and logging
    - Automatic state management based on configured thresholds

Monitoring Capabilities:
    - Current failure counts and success rates
    - Last failure timestamps and error patterns
    - Recovery timeout configuration and status
    - Threshold configuration and compliance monitoring
    - Historical metrics and trend analysis
    - Performance impact assessment

Administrative Operations:
    - Manual circuit breaker reset for emergency recovery
    - State manipulation for testing and maintenance
    - Configuration validation and compliance checking
    - Operational control for service maintenance
    - Emergency override capabilities for critical situations

Dependencies:
    - AIResilienceOrchestrator: Core circuit breaker management and orchestration
    - CircuitBreaker: Individual circuit breaker instances with state management
    - Metrics: Circuit breaker performance and operational metrics
    - Security: API key verification for all circuit breaker endpoints

Authentication:
    All circuit breaker endpoints require API key authentication to ensure
    secure access to critical infrastructure components and prevent
    unauthorized manipulation of circuit breaker states.

Example:
    Get all circuit breaker statuses:
        GET /api/internal/resilience/circuit-breakers
        
    Get specific circuit breaker details:
        GET /api/internal/resilience/circuit-breakers/text_processing_service
        
    Reset a circuit breaker:
        POST /api/internal/resilience/circuit-breakers/text_processing_service/reset

Note:
    Circuit breakers are critical safety components that protect against
    cascading failures. Manual resets should be used carefully and only
    when the underlying issues have been resolved to prevent immediate
    re-opening of the circuit breaker.
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

@router.get("/circuit-breakers")
async def get_circuit_breaker_status(api_key: str = Depends(verify_api_key)):
    """
    Get the status of all circuit breakers.
    
    Returns detailed information about each circuit breaker including:
    - Current state (open, closed, half-open)
    - Failure counts
    - Last failure times
    """
    try:
        all_metrics = ai_resilience.get_all_metrics()
        return all_metrics.get("circuit_breakers", {})
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get circuit breaker status: {str(e)}"
        )

@router.get("/circuit-breakers/{breaker_name}")
async def get_circuit_breaker_details(
    breaker_name: str,
    api_key: str = Depends(verify_api_key)
):
    """
    Get detailed information about a specific circuit breaker.
    
    Args:
        breaker_name: Name of the circuit breaker
    """
    try:
        if breaker_name not in ai_resilience.circuit_breakers:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Circuit breaker '{breaker_name}' not found"
            )
        
        breaker = ai_resilience.circuit_breakers[breaker_name]
        return {
            "name": breaker_name,
            "state": breaker.state,
            "failure_count": breaker.failure_count,
            "failure_threshold": breaker.failure_threshold,
            "recovery_timeout": breaker.recovery_timeout,
            "last_failure_time": breaker.last_failure_time,
            "metrics": breaker.metrics.to_dict() if hasattr(breaker, 'metrics') else {}
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get circuit breaker details: {str(e)}"
        )

@router.post("/circuit-breakers/{breaker_name}/reset")
async def reset_circuit_breaker(
    breaker_name: str,
    api_key: str = Depends(verify_api_key)
):
    """
    Reset a specific circuit breaker to closed state.
    
    Args:
        breaker_name: Name of the circuit breaker to reset
    """
    try:
        if breaker_name not in ai_resilience.circuit_breakers:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail=f"Circuit breaker '{breaker_name}' not found"
            )
        
        breaker = ai_resilience.circuit_breakers[breaker_name]
        # Reset the circuit breaker
        breaker._failure_count = 0
        breaker._last_failure = None
        breaker._state = 'closed'
        # Also reset the enhanced circuit breaker's last_failure_time
        breaker.last_failure_time = None
        
        return {
            "message": f"Circuit breaker '{breaker_name}' has been reset",
            "name": breaker_name,
            "new_state": breaker.state
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset circuit breaker: {str(e)}"
        )
