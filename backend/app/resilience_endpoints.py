"""
Additional API endpoints for resilience monitoring and management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, Optional
from datetime import datetime
from app.auth import verify_api_key, optional_verify_api_key
from app.services.resilience import ai_resilience
from app.services.text_processor import text_processor

# Create a router for resilience endpoints
resilience_router = APIRouter(prefix="/resilience", tags=["resilience"])

@resilience_router.get("/health")
async def get_resilience_health(api_key: str = Depends(optional_verify_api_key)):
    """
    Get the health status of the resilience service.
    
    Returns information about circuit breaker states and overall health.
    """
    try:
        health_status = ai_resilience.get_health_status()
        return {
            "resilience_health": health_status,
            "service_health": text_processor.get_resilience_health(),
            "overall_healthy": health_status["healthy"]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get resilience health: {str(e)}"
        )

@resilience_router.get("/metrics")
async def get_resilience_metrics(api_key: str = Depends(verify_api_key)):
    """
    Get detailed metrics for all resilience operations.
    
    Requires authentication. Returns comprehensive metrics including:
    - Operation success/failure rates
    - Retry attempt counts
    - Circuit breaker state transitions
    """
    try:
        return ai_resilience.get_all_metrics()
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get resilience metrics: {str(e)}"
        )

@resilience_router.get("/metrics/{operation_name}")
async def get_operation_metrics(
    operation_name: str,
    api_key: str = Depends(verify_api_key)
):
    """
    Get metrics for a specific operation.
    
    Args:
        operation_name: Name of the operation (e.g., 'summarize_text', 'analyze_sentiment')
    """
    try:
        metrics = ai_resilience.get_metrics(operation_name)
        return {
            "operation": operation_name,
            "metrics": metrics.to_dict()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get metrics for operation {operation_name}: {str(e)}"
        )

@resilience_router.post("/metrics/reset")
async def reset_resilience_metrics(
    operation_name: Optional[str] = None,
    api_key: str = Depends(verify_api_key)
):
    """
    Reset metrics for a specific operation or all operations.
    
    Args:
        operation_name: Optional operation name. If not provided, resets all metrics.
    """
    try:
        ai_resilience.reset_metrics(operation_name)
        return {
            "message": f"Metrics reset for {operation_name or 'all operations'}",
            "operation": operation_name
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset metrics: {str(e)}"
        )

@resilience_router.get("/circuit-breakers")
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

@resilience_router.get("/circuit-breakers/{breaker_name}")
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
            "state": breaker.current_state,
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

@resilience_router.post("/circuit-breakers/{breaker_name}/reset")
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
        breaker._last_failure_time = None
        breaker._state = 'closed'
        
        return {
            "message": f"Circuit breaker '{breaker_name}' has been reset",
            "name": breaker_name,
            "new_state": breaker.current_state
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset circuit breaker: {str(e)}"
        )

@resilience_router.get("/config")
async def get_resilience_config(api_key: str = Depends(verify_api_key)):
    """
    Get current resilience configuration.
    
    Returns the configuration for all resilience strategies.
    """
    try:
        config_data = {}
        for strategy, config in ai_resilience.configs.items():
            config_data[strategy.value] = {
                "strategy": config.strategy.value,
                "retry_config": {
                    "max_attempts": config.retry_config.max_attempts,
                    "max_delay_seconds": config.retry_config.max_delay_seconds,
                    "exponential_multiplier": config.retry_config.exponential_multiplier,
                    "exponential_min": config.retry_config.exponential_min,
                    "exponential_max": config.retry_config.exponential_max,
                    "jitter": config.retry_config.jitter,
                    "jitter_max": config.retry_config.jitter_max
                },
                "circuit_breaker_config": {
                    "failure_threshold": config.circuit_breaker_config.failure_threshold,
                    "recovery_timeout": config.circuit_breaker_config.recovery_timeout,
                    "half_open_max_calls": config.circuit_breaker_config.half_open_max_calls
                },
                "enable_circuit_breaker": config.enable_circuit_breaker,
                "enable_retry": config.enable_retry
            }
        
        return {
            "strategies": config_data,
            "operation_strategies": text_processor.resilience_strategies
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get resilience config: {str(e)}"
        )

@resilience_router.get("/dashboard")
async def get_resilience_dashboard(api_key: str = Depends(optional_verify_api_key)):
    """
    Get a dashboard view of resilience status.
    
    Returns a summary suitable for monitoring dashboards.
    """
    try:
        health_status = ai_resilience.get_health_status()
        all_metrics = ai_resilience.get_all_metrics()
        
        # Calculate summary statistics
        total_calls = sum(
            metrics.get("total_calls", 0) 
            for metrics in all_metrics.get("operations", {}).values()
        )
        total_successes = sum(
            metrics.get("successful_calls", 0) 
            for metrics in all_metrics.get("operations", {}).values()
        )
        total_failures = sum(
            metrics.get("failed_calls", 0) 
            for metrics in all_metrics.get("operations", {}).values()
        )
        total_retries = sum(
            metrics.get("retry_attempts", 0) 
            for metrics in all_metrics.get("operations", {}).values()
        )
        
        overall_success_rate = (total_successes / total_calls * 100) if total_calls > 0 else 0
        
        return {
            "timestamp": datetime.now().isoformat(),
            "health": {
                "overall_healthy": health_status["healthy"],
                "open_circuit_breakers": len(health_status["open_circuit_breakers"]),
                "half_open_circuit_breakers": len(health_status["half_open_circuit_breakers"]),
                "total_circuit_breakers": health_status["total_circuit_breakers"]
            },
            "performance": {
                "total_calls": total_calls,
                "successful_calls": total_successes,
                "failed_calls": total_failures,
                "retry_attempts": total_retries,
                "success_rate": round(overall_success_rate, 2)
            },
            "operations": list(all_metrics.get("operations", {}).keys()),
            "alerts": [
                f"Circuit breaker open: {name}" 
                for name in health_status["open_circuit_breakers"]
            ] + [
                f"High failure rate detected" 
                if overall_success_rate < 80 and total_calls > 10 else None
            ],
            "summary": all_metrics.get("summary", {})
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get resilience dashboard: {str(e)}"
        ) 