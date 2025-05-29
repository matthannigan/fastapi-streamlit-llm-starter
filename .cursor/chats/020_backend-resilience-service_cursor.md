# Adding Resilience Monitoring API Endpoints
_Exported on 5/29/2025 at 11:19:26 EDT from Cursor (0.50.7)_

---

**User**

"""
Additional API endpoints for resilience monitoring and management.
Add these endpoints to your main.py file.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, Optional
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
            "timestamp": "2024-01-01T12:00:00Z",  # You can use datetime.now().isoformat()
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


# Instructions for integrating these endpoints into main.py:
"""
To integrate these resilience endpoints into your main FastAPI application,
add the following to your backend/app/main.py file:

1. Import the router:
   from app.resilience_endpoints import resilience_router

2. Include the router in your app:
   app.include_router(resilience_router)

3. Update the health check endpoint to include resilience status:

@app.get("/health", response_model=HealthResponse)
async def health_check():
    \"\"\"Enhanced health check endpoint with resilience status.\"\"\"
    from app.services.resilience import ai_resilience
    
    ai_healthy = bool(settings.gemini_api_key)
    resilience_healthy = ai_resilience.is_healthy()
    
    return HealthResponse(
        status="healthy" if ai_healthy and resilience_healthy else "degraded",
        ai_model_available=ai_healthy,
        resilience_healthy=resilience_healthy
    )

4. Add resilience status to your HealthResponse model in shared/models.py:

class HealthResponse(BaseModel):
    \"\"\"Health check response model.\"\"\"
    status: str = "healthy"
    timestamp: datetime = Field(default_factory=datetime.now)
    version: str = "1.0.0"
    ai_model_available: bool = True
    resilience_healthy: Optional[bool] = None
"""

---

**Cursor**

To integrate the additional API endpoints for resilience monitoring and management into your FastAPI application, follow these steps:

1. **Create a new file for the resilience endpoints** (if it doesn't already exist) in your project structure, for example, `backend/app/resilience_endpoints.py`.

2. **Add the resilience endpoints code** to the new file. Here’s the complete code to include:

```python
# backend/app/resilience_endpoints.py

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, Optional
from app.auth import verify_api_key, optional_verify_api_key
from app.services.resilience import ai_resilience
from app.services.text_processor import text_processor

# Create a router for resilience endpoints
resilience_router = APIRouter(prefix="/resilience", tags=["resilience"])

@resilience_router.get("/health")
async def get_resilience_health(api_key: str = Depends(optional_verify_api_key)):
    """Get the health status of the resilience service."""
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
    """Get detailed metrics for all resilience operations."""
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
    """Get metrics for a specific operation."""
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
    """Reset metrics for a specific operation or all operations."""
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
    """Get the status of all circuit breakers."""
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
    """Get detailed information about a specific circuit breaker."""
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
    """Reset a specific circuit breaker to closed state."""
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
    """Get current resilience configuration."""
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
    """Get a dashboard view of resilience status."""
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
            "timestamp": "2024-01-01T12:00:00Z",  # You can use datetime.now().isoformat()
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
```

3. **Update your `main.py` file** to include the new router. Add the following lines:

```python
# backend/app/main.py

from app.resilience_endpoints import resilience_router  # Add this import

# Include the router in your FastAPI app
app.include_router(resilience_router)
```

4. **Update the health check endpoint** in `main.py` to include resilience status. Modify the existing health check function as follows:

```python
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Enhanced health check endpoint with resilience status."""
    from app.services.resilience import ai_resilience
    
    ai_healthy = bool(settings.gemini_api_key)
    resilience_healthy = ai_resilience.is_healthy()
    
    return HealthResponse(
        status="healthy" if ai_healthy and resilience_healthy else "degraded",
        ai_model_available=ai_healthy,
        resilience_healthy=resilience_healthy
    )
```

5. **Update the `HealthResponse` model** in `shared/models.py` to include the new field for resilience health:

```python
class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = "healthy"
    timestamp: datetime = Field(default_factory=datetime.now)
    version: str = "1.0.0"
    ai_model_available: bool = True
    resilience_healthy: Optional[bool] = None  # Add this line
```

### Summary of Changes
- Created a new file for resilience endpoints.
- Added resilience monitoring endpoints to the new file.
- Updated `main.py` to include the resilience router and modified the health check endpoint.
- Updated the `HealthResponse` model to include resilience health status.

These changes will enhance your FastAPI application with resilience monitoring capabilities. If you need further assistance or modifications, feel free to ask!

```python
# backend/app/resilience_endpoints.py

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, Optional
from app.auth import verify_api_key, optional_verify_api_key
from app.services.resilience import ai_resilience
from app.services.text_processor import text_processor

# Create a router for resilience endpoints
resilience_router = APIRouter(prefix="/resilience", tags=["resilience"])

@resilience_router.get("/health")
async def get_resilience_health(api_key: str = Depends(optional_verify_api_key)):
    """Get the health status of the resilience service."""
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
    """Get detailed metrics for all resilience operations."""
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
    """Get metrics for a specific operation."""
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
    """Reset metrics for a specific operation or all operations."""
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
    """Get the status of all circuit breakers."""
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
    """Get detailed information about a specific circuit breaker."""
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
    """Reset a specific circuit breaker to closed state."""
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
    """Get current resilience configuration."""
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
    """Get a dashboard view of resilience status."""
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
            "timestamp": "2024-01-01T12:00:00Z",  # You can use datetime.now().isoformat()
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
```

```python
# backend/app/main.py

from app.resilience_endpoints import resilience_router  # Add this import

# Include the router in your FastAPI app
app.include_router(resilience_router)
```

```python
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Enhanced health check endpoint with resilience status."""
    from app.services.resilience import ai_resilience
    
    ai_healthy = bool(settings.gemini_api_key)
    resilience_healthy = ai_resilience.is_healthy()
    
    return HealthResponse(
        status="healthy" if ai_healthy and resilience_healthy else "degraded",
        ai_model_available=ai_healthy,
        resilience_healthy=resilience_healthy
    )
```

```python
class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = "healthy"
    timestamp: datetime = Field(default_factory=datetime.now)
    version: str = "1.0.0"
    ai_model_available: bool = True
    resilience_healthy: Optional[bool] = None  # Add this line
```

---

**User**

Make the changes

---

**Cursor**

I'll make the necessary changes to integrate the resilience monitoring endpoints into your FastAPI application.

```python
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
```

Now I'll update the main.py file to include the resilience router and modify the health check endpoint:

```python
"""Main FastAPI application."""

import sys
import os
# Add the root directory to Python path so we can import shared modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__)))))

import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI, HTTPException, status, Depends
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from shared.models import (
    TextProcessingRequest,
    TextProcessingResponse,
    ErrorResponse,
    HealthResponse,
    BatchTextProcessingRequest,
    BatchTextProcessingResponse
)
from app.config import settings
from app.services.text_processor import text_processor
from app.auth import verify_api_key, optional_verify_api_key
from app.services.cache import ai_cache
from app.resilience_endpoints import resilience_router

// ... existing code ...

# Create FastAPI app
app = FastAPI(
    title="AI Text Processor API",
    description="API for processing text using AI models",
    version="1.0.0",
    lifespan=lifespan
)

# Add CORS middleware
# Note: mypy has issues with FastAPI's add_middleware and CORSMiddleware
# This is a known issue and the code works correctly at runtime
app.add_middleware(
    CORSMiddleware,  # type: ignore[arg-type]
    allow_origins=settings.allowed_origins,  # type: ignore[call-arg]
    allow_credentials=True,  # type: ignore[call-arg]
    allow_methods=["*"],  # type: ignore[call-arg]
    allow_headers=["*"],  # type: ignore[call-arg]
)

# Include the resilience router
app.include_router(resilience_router)

// ... existing code ...

@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Enhanced health check endpoint with resilience status."""
    try:
        from app.services.resilience import ai_resilience
        
        ai_healthy = bool(settings.gemini_api_key)
        resilience_healthy = ai_resilience.is_healthy()
        
        return HealthResponse(
            status="healthy" if ai_healthy and resilience_healthy else "degraded",
            ai_model_available=ai_healthy,
            resilience_healthy=resilience_healthy
        )
    except Exception:
        # Fallback if resilience service is not available
        return HealthResponse(
            ai_model_available=bool(settings.gemini_api_key),
            resilience_healthy=None
        )

// ... existing code ...
```

Now I need to update the HealthResponse model in the shared/models.py file to include the resilience_healthy field:

```python
class HealthResponse(BaseModel):
    """Health check response model."""
    status: str = "healthy"
    timestamp: datetime = Field(default_factory=datetime.now)
    version: str = "1.0.0"
    ai_model_available: bool = True
    resilience_healthy: Optional[bool] = None
```

Perfect! I've successfully made all the necessary changes to integrate the resilience monitoring endpoints into your FastAPI application. Here's a summary of what was implemented:

## Changes Made:

### 1. Created `backend/app/resilience_endpoints.py`
- Added a comprehensive set of resilience monitoring endpoints
- Includes health checks, metrics, circuit breaker management, configuration viewing, and dashboard functionality
- All endpoints are properly authenticated and include error handling

### 2. Updated `backend/app/main.py`
- Added import for the resilience router
- Included the resilience router in the FastAPI app
- Enhanced the health check endpoint to include resilience status with fallback handling

### 3. Updated `shared/models.py`
- Added `resilience_healthy` field to the `HealthResponse` model

## New Endpoints Available:

- **`GET /resilience/health`** - Get resilience service health status
- **`GET /resilience/metrics`** - Get detailed metrics for all operations
- **`GET /resilience/metrics/{operation_name}`** - Get metrics for specific operation
- **`POST /resilience/metrics/reset`** - Reset metrics
- **`GET /resilience/circuit-breakers`** - Get all circuit breaker statuses
- **`GET /resilience/circuit-breakers/{breaker_name}`** - Get specific circuit breaker details
- **`POST /resilience/circuit-breakers/{breaker_name}/reset`** - Reset a circuit breaker
- **`GET /resilience/config`** - Get resilience configuration
- **`GET /resilience/dashboard`** - Get dashboard view with summary statistics

## Features:

- **Authentication**: Most endpoints require API key authentication
- **Error Handling**: Comprehensive error handling with appropriate HTTP status codes
- **Monitoring**: Real-time metrics and health status monitoring
- **Management**: Ability to reset metrics and circuit breakers
- **Dashboard**: Summary view suitable for monitoring dashboards

The implementation is now complete and your FastAPI application has been enhanced with robust resilience monitoring and management capabilities!

---

**User**

I want to update `text_processor.py` to `text_processor_resilience.py` but I don't want to lose the `# noqa:` comments I've added. Can you update the resilence file with the old comments where appropriate?

---

**Cursor**

I'll update the `text_processor_resilience.py` file to include the `# noqa:` comments from the original `text_processor.py` file where appropriate.

```python
"""Text processing service with resilience integration."""

import sys
import os
# Add the root directory to Python path so we can import shared modules
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))))

import time
import asyncio
from typing import Dict, Any, List
import logging
from pydantic_ai import Agent

from shared.models import (
    ProcessingOperation,
    TextProcessingRequest,
    TextProcessingResponse,
    SentimentResult,
    BatchTextProcessingRequest,
    BatchTextProcessingResponse,
    BatchProcessingItem,
    ProcessingStatus
)
from app.config import settings
from app.services.cache import ai_cache
from app.services.resilience import (
    ai_resilience,
    ResilienceStrategy,
    with_balanced_resilience,
    with_aggressive_resilience,
    with_conservative_resilience,
    ServiceUnavailableError,
    TransientAIError
)

logger = logging.getLogger(__name__)


class TextProcessorService:
    """Service for processing text using AI models with resilience patterns."""
    
    def __init__(self):
        """Initialize the text processor with AI agent and resilience."""
        if not settings.gemini_api_key:
            raise ValueError("GEMINI_API_KEY environment variable is required")
            
        self.agent = Agent(
            model=settings.ai_model,
            system_prompt="You are a helpful AI assistant specialized in text analysis.",
        )
        
        # Configure resilience strategies for different operations
        self._configure_resilience_strategies()
    
    def _configure_resilience_strategies(self):
        """Configure resilience strategies based on settings."""
        self.resilience_strategies = {
            ProcessingOperation.SUMMARIZE: settings.summarize_resilience_strategy,
            ProcessingOperation.SENTIMENT: settings.sentiment_resilience_strategy,
            ProcessingOperation.KEY_POINTS: settings.key_points_resilience_strategy,
            ProcessingOperation.QUESTIONS: settings.questions_resilience_strategy,
            ProcessingOperation.QA: settings.qa_resilience_strategy,
        }
        
        logger.info(f"Configured resilience strategies: {self.resilience_strategies}")
    
    async def _get_fallback_response(self, operation: ProcessingOperation, text: str, question: str = None) -> str:
        """
        Provide fallback responses when AI service is unavailable.
        
        This method returns cached responses or generates simple fallback messages
        when the circuit breaker is open or retries are exhausted.
        """
        logger.warning(f"Providing fallback response for {operation}")
        
        # Try to get cached response first
        operation_value = operation.value if hasattr(operation, 'value') else operation
        cached_response = await ai_cache.get_cached_response(text, operation_value, {}, question)
        
        if cached_response:
            logger.info(f"Using cached fallback for {operation}")
            return cached_response
        
        # Generate simple fallback responses
        fallback_responses = {
            ProcessingOperation.SUMMARIZE: "Service temporarily unavailable. Please try again later for text summarization.",
            ProcessingOperation.SENTIMENT: None,  # Will use neutral sentiment
            ProcessingOperation.KEY_POINTS: ["Service temporarily unavailable", "Please try again later"],
            ProcessingOperation.QUESTIONS: ["What is the main topic of this text?", "Can you provide more details?"],
            ProcessingOperation.QA: "I'm sorry, I cannot answer your question right now. The service is temporarily unavailable. Please try again later."
        }
        
        return fallback_responses.get(operation, "Service temporarily unavailable. Please try again later.")
    
    async def _get_fallback_sentiment(self) -> SentimentResult:
        """Provide fallback sentiment when AI service is unavailable."""
        return SentimentResult(
            sentiment="neutral",
            confidence=0.0,
            explanation="Unable to analyze sentiment - service temporarily unavailable"
        )
    
    async def process_text(self, request: TextProcessingRequest) -> TextProcessingResponse:
        """Process text with caching and resilience support."""
        # Check cache first
        operation_value = request.operation.value if hasattr(request.operation, 'value') else request.operation
        cached_response = await ai_cache.get_cached_response(
            request.text, 
            operation_value, 
            request.options or {}, 
            request.question
        )
        
        if cached_response:
            logger.info(f"Cache hit for operation: {request.operation}")
            return TextProcessingResponse(**cached_response)
        
        # Process normally if no cache hit
        start_time = time.time()
        
        try:
            logger.info(f"Processing text with operation: {request.operation}")
            
            # Validate operation first to provide better error messages
            if request.operation not in [op.value for op in ProcessingOperation]:
                raise ValueError(f"Unsupported operation: {request.operation}")
            
            # Create response with timing metadata
            processing_time = time.time() - start_time
            response = TextProcessingResponse(
                operation=request.operation,
                processing_time=processing_time,
                metadata={"word_count": len(request.text.split())}
            )
            
            # Route to specific processing method with resilience
            try:
                if request.operation == ProcessingOperation.SUMMARIZE:
                    response.result = await self._summarize_text_with_resilience(request.text, request.options)
                elif request.operation == ProcessingOperation.SENTIMENT:
                    response.sentiment = await self._analyze_sentiment_with_resilience(request.text)
                elif request.operation == ProcessingOperation.KEY_POINTS:
                    response.key_points = await self._extract_key_points_with_resilience(request.text, request.options)
                elif request.operation == ProcessingOperation.QUESTIONS:
                    response.questions = await self._generate_questions_with_resilience(request.text, request.options)
                elif request.operation == ProcessingOperation.QA:
                    response.result = await self._answer_question_with_resilience(request.text, request.question)
                else:
                    raise ValueError(f"Unsupported operation: {request.operation}")
            
            except ServiceUnavailableError:
                # Handle circuit breaker open - provide fallback
                if request.operation == ProcessingOperation.SENTIMENT:
                    response.sentiment = await self._get_fallback_sentiment()
                elif request.operation == ProcessingOperation.KEY_POINTS:
                    response.key_points = await self._get_fallback_response(request.operation, request.text)
                elif request.operation == ProcessingOperation.QUESTIONS:
                    response.questions = await self._get_fallback_response(request.operation, request.text)
                else:
                    response.result = await self._get_fallback_response(request.operation, request.text, request.question)
                
                # Mark as degraded service
                response.metadata["service_status"] = "degraded"
                response.metadata["fallback_used"] = True
            
            # Cache the successful response (even fallback responses)
            await ai_cache.cache_response(
                request.text,
                operation_value,
                request.options or {},
                response.model_dump(),
                request.question
            )
                
            processing_time = time.time() - start_time
            response.processing_time = processing_time
            logger.info(f"Processing completed in {processing_time:.2f}s")  # noqa: E231
            return response
            
        except Exception as e:
            logger.error(f"Error processing text: {str(e)}")
            raise
    
    @ai_resilience.with_resilience("summarize_text", strategy=ResilienceStrategy.BALANCED)
    async def _summarize_text_with_resilience(self, text: str, options: Dict[str, Any]) -> str:
        """Summarize text with resilience patterns."""
        return await self._summarize_text(text, options)
    
    @ai_resilience.with_resilience("analyze_sentiment", strategy=ResilienceStrategy.AGGRESSIVE)
    async def _analyze_sentiment_with_resilience(self, text: str) -> SentimentResult:
        """Analyze sentiment with resilience patterns."""
        return await self._analyze_sentiment(text)
    
    @ai_resilience.with_resilience("extract_key_points", strategy=ResilienceStrategy.BALANCED)
    async def _extract_key_points_with_resilience(self, text: str, options: Dict[str, Any]) -> List[str]:
        """Extract key points with resilience patterns."""
        return await self._extract_key_points(text, options)
    
    @ai_resilience.with_resilience("generate_questions", strategy=ResilienceStrategy.BALANCED)
    async def _generate_questions_with_resilience(self, text: str, options: Dict[str, Any]) -> List[str]:
        """Generate questions with resilience patterns."""
        return await self._generate_questions(text, options)
    
    @ai_resilience.with_resilience("answer_question", strategy=ResilienceStrategy.CONSERVATIVE)
    async def _answer_question_with_resilience(self, text: str, question: str) -> str:
        """Answer question with resilience patterns."""
        return await self._answer_question(text, question)
    
    async def _summarize_text(self, text: str, options: Dict[str, Any]) -> str:
        """Summarize the provided text."""
        max_length = options.get("max_length", 100)
        
        prompt = f"""
        Please provide a concise summary of the following text in approximately {max_length} words:
        
        Text: {text}
        
        Summary:
        """  # noqa: E231,E221
        
        try:
            result = await self.agent.run(prompt)
            return result.data.strip()
        except Exception as e:
            logger.error(f"AI agent error in summarization: {e}")
            # Convert to our custom exception for proper retry handling
            raise TransientAIError(f"Failed to summarize text: {str(e)}")
    
    async def _analyze_sentiment(self, text: str) -> SentimentResult:
        """Analyze sentiment of the provided text."""
        prompt = f"""
        Analyze the sentiment of the following text. Respond with a JSON object containing:
        - sentiment: "positive", "negative", or "neutral"
        - confidence: a number between 0.0 and 1.0
        - explanation: a brief explanation of the sentiment
        
        Text: {text}
        
        Response (JSON only):
        """  # noqa: E231,E221
        
        try:
            result = await self.agent.run(prompt)
            
            # Parse the JSON response
            import json
            try:
                sentiment_data = json.loads(result.data.strip())
                return SentimentResult(**sentiment_data)
            except (json.JSONDecodeError, ValueError) as e:
                logger.warning(f"Failed to parse sentiment JSON: {e}")
                # Fallback response
                return SentimentResult(
                    sentiment="neutral",
                    confidence=0.5,
                    explanation="Unable to analyze sentiment accurately"
                )
        except Exception as e:
            logger.error(f"AI agent error in sentiment analysis: {e}")
            raise TransientAIError(f"Failed to analyze sentiment: {str(e)}")
    
    async def _extract_key_points(self, text: str, options: Dict[str, Any]) -> List[str]:
        """Extract key points from the text."""
        max_points = options.get("max_points", 5)
        
        prompt = f"""
        Extract the {max_points} most important key points from the following text.
        Return each point as a separate line starting with a dash (-).
        
        Text: {text}
        
        Key Points:
        """  # noqa: E231,E221
        
        try:
            result = await self.agent.run(prompt)
            
            # Parse the response into a list
            points = []
            for line in result.data.strip().split('\n'):
                line = line.strip()
                if line.startswith('-'):
                    points.append(line[1:].strip())
                elif line and not line.startswith('Key Points:'):
                    points.append(line)
            
            return points[:max_points]
        except Exception as e:
            logger.error(f"AI agent error in key points extraction: {e}")
            raise TransientAIError(f"Failed to extract key points: {str(e)}")
    
    async def _generate_questions(self, text: str, options: Dict[str, Any]) -> List[str]:
        """Generate questions about the text."""
        num_questions = options.get("num_questions", 5)
        
        prompt = f"""
        Generate {num_questions} thoughtful questions about the following text.
        These questions should help someone better understand or think more deeply about the content.
        Return each question on a separate line.
        
        Text: {text}
        
        Questions:
        """  # noqa: E231,E221
        
        try:
            result = await self.agent.run(prompt)
            
            # Parse questions into a list
            questions = []
            for line in result.data.strip().split('\n'):
                line = line.strip()
                if line and not line.startswith('Questions:'):
                    # Remove numbering if present
                    if line[0].isdigit() and '.' in line[:5]:
                        line = line.split('.', 1)[1].strip()
                    questions.append(line)
            
            return questions[:num_questions]
        except Exception as e:
            logger.error(f"AI agent error in question generation: {e}")
            raise TransientAIError(f"Failed to generate questions: {str(e)}")
    
    async def _answer_question(self, text: str, question: str) -> str:
        """Answer a question about the text."""
        if not question:
            raise ValueError("Question is required for Q&A operation")
        
        prompt = f"""
        Based on the following text, please answer this question:
        
        Question: {question}
        
        Text: {text}
        
        Answer:
        """  # noqa: E231,E221
        
        try:
            result = await self.agent.run(prompt)
            return result.data.strip()
        except Exception as e:
            logger.error(f"AI agent error in question answering: {e}")
            raise TransientAIError(f"Failed to answer question: {str(e)}")

    async def process_batch(self, batch_request: BatchTextProcessingRequest) -> BatchTextProcessingResponse:
        """Process a batch of text processing requests concurrently with resilience."""
        start_time = time.time()
        total_requests = len(batch_request.requests)
        batch_id = batch_request.batch_id or f"batch_{int(time.time())}"

        logger.info(f"Processing batch of {total_requests} requests for batch_id: {batch_id}")

        semaphore = asyncio.Semaphore(settings.BATCH_AI_CONCURRENCY_LIMIT)
        tasks = []

        async def _process_single_request_in_batch(index: int, item_request: TextProcessingRequest) -> BatchProcessingItem:
            """Helper function to process a single request within the batch with resilience."""
            async with semaphore:
                try:
                    # Ensure the operation is valid before processing
                    if not hasattr(ProcessingOperation, item_request.operation.upper()):
                        raise ValueError(f"Unsupported operation: {item_request.operation}")
                    
                    # Create a new TextProcessingRequest object
                    current_request = TextProcessingRequest(
                        text=item_request.text,
                        operation=ProcessingOperation[item_request.operation.upper()],
                        options=item_request.options,
                        question=item_request.question
                    )
                    
                    # Process with resilience (this will use the resilience decorators)
                    response = await self.process_text(current_request)
                    return BatchProcessingItem(request_index=index, status=ProcessingStatus.COMPLETED, response=response)
                    
                except ServiceUnavailableError as e:
                    logger.warning(f"Batch item {index} (batch_id: {batch_id}) degraded service: {str(e)}")
                    # For circuit breaker open, we might want to return a partial success
                    # depending on business requirements
                    return BatchProcessingItem(request_index=index, status=ProcessingStatus.FAILED, error=str(e))
                    
                except Exception as e:
                    logger.error(f"Batch item {index} (batch_id: {batch_id}) failed: {str(e)}")
                    return BatchProcessingItem(request_index=index, status=ProcessingStatus.FAILED, error=str(e))

        for i, request_item in enumerate(batch_request.requests):
            task = _process_single_request_in_batch(i, request_item)
            tasks.append(task)

        results: List[BatchProcessingItem] = await asyncio.gather(*tasks, return_exceptions=False)

        completed_count = sum(1 for r in results if r.status == ProcessingStatus.COMPLETED)
        failed_count = total_requests - completed_count
        total_time = time.time() - start_time

        logger.info(f"Batch (batch_id: {batch_id}) completed. Successful: {completed_count}/{total_requests}. Time: {total_time:.2f}s")  # noqa: E231

        return BatchTextProcessingResponse(
            batch_id=batch_id,
            total_requests=total_requests,
            completed=completed_count,
            failed=failed_count,
            results=results,
            total_processing_time=total_time
        )
    
    def get_resilience_health(self) -> Dict[str, Any]:
        """Get resilience health status for this service."""
        return ai_resilience.get_health_status()
    
    def get_resilience_metrics(self) -> Dict[str, Any]:
        """Get resilience metrics for this service."""
        return ai_resilience.get_all_metrics()


# Global service instance
text_processor = TextProcessorService()
```

Let me check what the current content looks like and make the specific changes needed:

Now let me read the specific sections that need the `# noqa:` comments:

Now let me read the rest of the file to see the batch processing section:

Now I can see exactly where the `# noqa:` comments need to be added. Let me make the specific edits:

```python
            processing_time = time.time() - start_time
            response.processing_time = processing_time
            logger.info(f"Processing completed in {processing_time:.2f}s")  # noqa: E231
            return response
```

```python
        prompt = f"""
        Please provide a concise summary of the following text in approximately {max_length} words:
        
        Text: {text}
        
        Summary:
        """  # noqa: E231,E221
```

```python
        prompt = f"""
        Analyze the sentiment of the following text. Respond with a JSON object containing:
        - sentiment: "positive", "negative", or "neutral"
        - confidence: a number between 0.0 and 1.0
        - explanation: a brief explanation of the sentiment
        
        Text: {text}
        
        Response (JSON only):
        """  # noqa: E231,E221
```

```python
        prompt = f"""
        Extract the {max_points} most important key points from the following text.
        Return each point as a separate line starting with a dash (-).
        
        Text: {text}
        
        Key Points:
        """  # noqa: E231,E221
```

```python
        prompt = f"""
        Generate {num_questions} thoughtful questions about the following text.
        These questions should help someone better understand or think more deeply about the content.
        Return each question on a separate line.
        
        Text: {text}
        
        Questions:
        """  # noqa: E231,E221
```

```python
        prompt = f"""
        Based on the following text, please answer this question:
        
        Question: {question}
        
        Text: {text}
        
        Answer:
        """  # noqa: E231,E221
```

```python
        logger.info(f"Batch (batch_id: {batch_id}) completed. Successful: {completed_count}/{total_requests}. Time: {total_time:.2f}s")  # noqa: E231
```

Perfect! I've successfully updated the `text_processor_resilience.py` file to include all the `# noqa:` comments from the original `text_processor.py` file. Here's a summary of the changes made:

## Changes Made

1. **Line 177**: Added `# noqa: E231` to the processing completion log message
2. **Line 219**: Added `# noqa: E231,E221` to the summarize text prompt f-string
3. **Line 239**: Added `# noqa: E231,E221` to the sentiment analysis prompt f-string  
4. **Line 269**: Added `# noqa: E231,E221` to the key points extraction prompt f-string
5. **Line 301**: Added `# noqa: E231,E221` to the question generation prompt f-string
6. **Line 333**: Added `# noqa: E231,E221` to the Q&A prompt f-string
7. **Line 405**: Added `# noqa: E231` to the batch processing completion log message

These `# noqa:` comments suppress specific linting warnings:
- `E231`: Missing whitespace after ':'
- `E221`: Multiple spaces before operator

The comments are placed exactly where they were needed in the original file, maintaining the same code quality standards while preserving the resilience functionality. Now you can use the resilience-enabled version without losing the linting suppressions you had carefully added to handle the f-string formatting in the prompts.

