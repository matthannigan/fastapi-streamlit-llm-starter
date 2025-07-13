"""Resilience service health monitoring and metrics REST API endpoints.

This module provides comprehensive FastAPI endpoints for monitoring and managing
the AI resilience service's health, configuration, and performance metrics. It
serves as the primary interface for internal monitoring, diagnostics, and
operational visibility into the resilience infrastructure.

The module implements endpoints for real-time health checks, configuration
retrieval, metrics collection, and dashboard-style monitoring views. All
endpoints support both legacy and modern resilience configurations with
automatic detection and appropriate response formatting.

Endpoints:
    GET  /resilience/health: Get service health status and circuit breaker states
    GET  /resilience/config: Retrieve current resilience configuration and strategies
    GET  /resilience/metrics: Get comprehensive resilience metrics for all operations
    GET  /resilience/metrics/{operation_name}: Get metrics for a specific operation
    POST /resilience/metrics/reset: Reset metrics for specific or all operations
    GET  /resilience/dashboard: Get dashboard-style summary for monitoring systems

Configuration Management:
    - Automatic detection of legacy vs. modern configuration formats
    - Environment variable override support for presets and custom configs
    - Operation-specific strategy retrieval with fallback handling
    - JSON parsing and validation for custom configuration overrides

Health Monitoring:
    - Circuit breaker state tracking (open, closed, half-open)
    - Overall service health assessment
    - Operation-level health status reporting
    - Real-time degradation detection

Performance Metrics:
    - Success/failure rates by operation
    - Retry attempt tracking and analysis
    - Circuit breaker activation statistics
    - Response time and throughput metrics
    - Historical trend data for performance analysis

Dependencies:
    - AIResilienceOrchestrator: Core resilience service for operations
    - Settings: Configuration management and environment integration
    - Security: API key verification for protected endpoints
    - Pydantic Models: Structured response validation and documentation

Authentication:
    Most endpoints require API key authentication via the verify_api_key
    dependency. Some monitoring endpoints support optional authentication
    for flexibility in different deployment scenarios.

Example:
    To check overall resilience service health:
        GET /api/internal/resilience/health
        
    To get comprehensive metrics for monitoring:
        GET /api/internal/resilience/dashboard
        
    To reset metrics for a specific operation:
        POST /api/internal/resilience/metrics/reset?operation_name=summarize

Note:
    This module automatically handles both legacy and modern resilience
    configurations, ensuring backward compatibility while supporting
    new features. Metrics are computed in real-time and may include
    brief processing delays for comprehensive statistics.
"""

import json
import logging
import os

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Optional
from datetime import datetime

from app.core.config import Settings, settings
from app.infrastructure.security.auth import verify_api_key, optional_verify_api_key
from app.infrastructure.resilience.orchestrator import ai_resilience

from app.api.internal.resilience.models import CurrentConfigResponse, ResilienceMetricsResponse

logger = logging.getLogger(__name__)

main_router = APIRouter(prefix="/resilience", tags=["Resilience Core"])
config_router = APIRouter(prefix="/resilience/config", tags=["Resilience Configuration"])

def get_settings() -> Settings:
    """Get the global settings instance."""
    return settings


@main_router.get("/health")
async def get_resilience_health():
    """Get resilience service health status and circuit breaker information.

    This endpoint provides comprehensive health monitoring for the AI resilience
    service, including overall health status and detailed circuit breaker states.
    
    Returns:
        Dict[str, Any]: A dictionary containing:
            - healthy (bool): Overall service health status
            - status (str): Human-readable status ("healthy" or "degraded")
            - details (Dict): Detailed health information including circuit breaker states
            
    Raises:
        HTTPException: 500 Internal Server Error if health status retrieval fails
        
    Example:
        >>> response = await get_resilience_health()
        >>> {
        ...     "healthy": True,
        ...     "status": "healthy",
        ...     "details": {
        ...         "circuit_breakers": {...},
        ...         "overall_health": "operational"
        ...     }
        ... }
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


@config_router.get("/", response_model=CurrentConfigResponse)
async def get_current_config(
    app_settings: Settings = Depends(get_settings),
    api_key: str = Depends(verify_api_key)
) -> CurrentConfigResponse:
    """Get the current resilience configuration with preset information and operation strategies.

    This endpoint retrieves the complete current resilience configuration, including
    preset information, operation-specific strategies, and any custom overrides.
    Automatically detects legacy vs. modern configuration formats.
    
    Args:
        app_settings: Application settings dependency for configuration access
        api_key: API key for authentication (injected via dependency)
        
    Returns:
        CurrentConfigResponse: Complete configuration response containing:
            - Current resilience configuration parameters
            - Preset name and operation strategies
            - Custom configuration overrides
            - Available strategies mapping
            
    Raises:
        HTTPException: 500 Internal Server Error if configuration retrieval fails
        
    Example:
        >>> response = await get_current_config()
        >>> CurrentConfigResponse(
        ...     preset_name="production",
        ...     config={...},
        ...     operation_strategies={...}
        ... )
    """
    try:
        # Clear cache to ensure fresh results when environment variables change during testing
        app_settings._clear_legacy_config_cache()
        
        # Get current resilience configuration
        resilience_config = app_settings.get_resilience_config()
        is_legacy = app_settings._has_legacy_resilience_config()
        
        # Get preset name with environment variable precedence
        if is_legacy:
            preset_name = "legacy"
        else:
            # Check environment variable first, then fall back to settings field
            preset_name = os.getenv("RESILIENCE_PRESET", app_settings.resilience_preset)
        
        # Get operation-specific strategies
        # Use registered operations from settings if available, fall back to common operations
        try:
            operations = app_settings.get_registered_operations()
        except Exception:
            # Fallback to common operations for compatibility
            operations = ["summarize", "sentiment", "key_points", "questions", "qa"]
        
        operation_strategies = {}
        for op in operations:
            try:
                operation_strategies[op] = app_settings.get_operation_strategy(op)
            except (AttributeError, KeyError):
                # Skip operations that don't have a strategy defined
                logger.debug(f"No strategy found for operation: {op}")
                continue
        
        # Parse custom overrides if present
        custom_overrides = None
        env_custom_config = os.getenv("RESILIENCE_CUSTOM_CONFIG")
        custom_config_json = env_custom_config if env_custom_config else app_settings.resilience_custom_config
        
        if custom_config_json:
            try:
                custom_overrides = json.loads(custom_config_json)
            except json.JSONDecodeError:
                logger.warning("Invalid JSON in resilience_custom_config")
        
        # Convert resilience config to dictionary
        config_dict = {
            "strategy": resilience_config.strategy.value,
            "retry_config": {
                "max_attempts": resilience_config.retry_config.max_attempts,
                "max_delay_seconds": resilience_config.retry_config.max_delay_seconds,
                "exponential_multiplier": resilience_config.retry_config.exponential_multiplier,
                "exponential_min": resilience_config.retry_config.exponential_min,
                "exponential_max": resilience_config.retry_config.exponential_max,
                "jitter": resilience_config.retry_config.jitter,
                "jitter_max": resilience_config.retry_config.jitter_max,
            },
            "circuit_breaker_config": {
                "failure_threshold": resilience_config.circuit_breaker_config.failure_threshold,
                "recovery_timeout": resilience_config.circuit_breaker_config.recovery_timeout,
                "half_open_max_calls": resilience_config.circuit_breaker_config.half_open_max_calls,
            },
            "enable_circuit_breaker": resilience_config.enable_circuit_breaker,
            "enable_retry": resilience_config.enable_retry,
        }
        
        # Add complete strategies mapping for backward compatibility
        strategies_dict = {}
        for strategy, config in ai_resilience.configurations.items():
            strategies_dict[strategy.value] = {
                "strategy": config.strategy.value,
                "retry_config": {
                    "max_attempts": config.retry_config.max_attempts,
                    "max_delay_seconds": config.retry_config.max_delay_seconds,
                    "exponential_multiplier": config.retry_config.exponential_multiplier,
                    "exponential_min": config.retry_config.exponential_min,
                    "exponential_max": config.retry_config.exponential_max,
                    "jitter": config.retry_config.jitter,
                    "jitter_max": config.retry_config.jitter_max,
                },
                "circuit_breaker_config": {
                    "failure_threshold": config.circuit_breaker_config.failure_threshold,
                    "recovery_timeout": config.circuit_breaker_config.recovery_timeout,
                    "half_open_max_calls": config.circuit_breaker_config.half_open_max_calls,
                },
                "enable_circuit_breaker": config.enable_circuit_breaker,
                "enable_retry": config.enable_retry,
            }
        
        return CurrentConfigResponse(
            preset_name=preset_name,
            is_legacy_config=is_legacy,
            configuration=config_dict,
            operation_strategies=operation_strategies,
            custom_overrides=custom_overrides,
            strategies=strategies_dict  # Add strategies mapping for backward compatibility
        )
        
    except Exception as e:
        logger.error(f"Error getting current configuration: {e}")
        raise HTTPException(status_code=500, detail=f"Failed to get current configuration: {str(e)}")


@main_router.get("/metrics", response_model=ResilienceMetricsResponse)
async def get_resilience_metrics(
    api_key: str = Depends(verify_api_key)
) -> ResilienceMetricsResponse:
    """Get comprehensive resilience metrics for all operations.

    This endpoint provides detailed metrics covering all resilience operations,
    including success rates, retry statistics, and circuit breaker performance.
    
    Args:
        api_key: API key for authentication (injected via dependency)
        
    Returns:
        ResilienceMetricsResponse: Comprehensive metrics response containing:
            - Success/failure rates for all operations
            - Retry attempt statistics and patterns
            - Circuit breaker activation data
            - Performance metrics and response times
            
    Raises:
        HTTPException: 500 Internal Server Error if metrics retrieval fails
        
    Example:
        >>> response = await get_resilience_metrics()
        >>> ResilienceMetricsResponse(
        ...     total_operations=1500,
        ...     success_rate=0.95,
        ...     operations={...}
        ... )
    """
    try:
        metrics = ai_resilience.get_all_metrics()
        return ResilienceMetricsResponse(**metrics)

    except Exception as e:
        logger.error(f"Error getting resilience metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to get resilience metrics: {str(e)}"
        )


@main_router.get("/metrics/{operation_name}")
async def get_operation_metrics(
    operation_name: str,
    api_key: str = Depends(verify_api_key)
):
    """Get detailed metrics for a specific resilience operation.

    This endpoint provides comprehensive metrics for a single operation,
    including performance statistics, error rates, and retry patterns.
    
    Args:
        operation_name: Name of the specific operation to retrieve metrics for
                       (e.g., 'summarize_text', 'analyze_sentiment')
        api_key: API key for authentication (injected via dependency)
        
    Returns:
        Dict[str, Any]: Operation-specific metrics containing:
            - operation: Operation name
            - metrics: Dictionary with detailed metrics including:
                - Success/failure counts and rates
                - Retry attempt statistics
                - Circuit breaker state and activations
                - Response time percentiles
                - Error patterns and trends
            
    Raises:
        HTTPException: 500 Internal Server Error if metrics retrieval fails
        
    Example:
        >>> response = await get_operation_metrics("summarize")
        >>> {
        ...     "operation": "summarize",
        ...     "metrics": {
        ...         "total_calls": 250,
        ...         "success_rate": 0.96,
        ...         "avg_response_time_ms": 1250
        ...     }
        ... }
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


@main_router.post("/metrics/reset")
async def reset_resilience_metrics(
    operation_name: Optional[str] = Query(None, description="Operation name to reset (if None, resets all)"),
    api_key: str = Depends(verify_api_key)
):
    """Reset resilience metrics for a specific operation or all operations.

    This endpoint clears stored metrics data, useful for testing or after
    configuration changes. Can target a specific operation or reset all metrics.
    
    Args:
        operation_name: Optional name of specific operation to reset.
                       If None, resets metrics for all operations
        api_key: API key for authentication (injected via dependency)
        
    Returns:
        Dict[str, str]: Reset confirmation containing:
            - message: Human-readable confirmation message indicating
                      which operations were reset
            
    Raises:
        HTTPException: 500 Internal Server Error if reset operation fails
        
    Example:
        >>> response = await reset_resilience_metrics("summarize")
        >>> {"message": "Reset metrics for operation: summarize"}
        >>> 
        >>> response = await reset_resilience_metrics()
        >>> {"message": "Reset all resilience metrics"}
    """
    try:
        ai_resilience.reset_metrics(operation_name)
        
        if operation_name:
            message = f"Reset metrics for operation: {operation_name}"
        else:
            message = "Reset all resilience metrics"
            
        logger.info(message)
        return {"message": message}
        
    except Exception as e:
        logger.error(f"Error resetting metrics: {e}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset metrics: {str(e)}"
        )


@main_router.get("/dashboard")
async def get_resilience_dashboard(api_key: str = Depends(optional_verify_api_key)):
    """Get comprehensive resilience dashboard data for monitoring systems.

    This endpoint provides a dashboard-style summary of resilience status,
    including health indicators, metrics summaries, and operational insights
    suitable for monitoring dashboards and operational visibility.
    
    Args:
        api_key: Optional API key for authentication (injected via dependency)
        
    Returns:
        Dict[str, Any]: Dashboard data containing:
            - timestamp: Current timestamp in ISO format
            - health: Service health summary including:
                - overall_healthy: Boolean overall health status
                - open_circuit_breakers: Count of open circuit breakers
                - half_open_circuit_breakers: Count of half-open circuit breakers
                - total_circuit_breakers: Total circuit breaker count
            - performance: Performance metrics including:
                - total_calls, successful_calls, failed_calls
                - retry_attempts: Total retry attempts across all operations
                - success_rate: Overall success rate percentage
            - operations: List of available operation names
            - alerts: List of current alerts and warnings
            - summary: Additional summary metrics
            
    Raises:
        HTTPException: 500 Internal Server Error if dashboard data retrieval fails
        
    Note:
        This endpoint supports optional authentication for flexibility in
        monitoring system integration scenarios.
        
    Example:
        >>> response = await get_resilience_dashboard()
        >>> {
        ...     "timestamp": "2023-12-01T10:30:00Z",
        ...     "health": {
        ...         "overall_healthy": True,
        ...         "open_circuit_breakers": 0
        ...     },
        ...     "performance": {
        ...         "total_calls": 1500,
        ...         "success_rate": 95.2
        ...     },
        ...     "alerts": []
        ... }
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
