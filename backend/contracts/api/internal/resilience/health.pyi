"""
Infrastructure Service: Resilience Health Monitoring API

🏗️ **STABLE API** - Changes affect all template users
📋 **Minimum test coverage**: 90%
🔧 **Configuration-driven behavior**

This module provides comprehensive FastAPI endpoints for monitoring and managing
the AI resilience service's health, configuration, and performance metrics. It
serves as the primary interface for internal monitoring, diagnostics, and
operational visibility into the resilience infrastructure.

The module implements endpoints for real-time health checks, configuration
retrieval, metrics collection, and dashboard-style monitoring views. All
endpoints support both legacy and modern resilience configurations with
automatic detection and appropriate response formatting.

Endpoints:
    GET  /internal/resilience/health: Get service health status and circuit breaker states
    GET  /internal/resilience/config: Retrieve current resilience configuration and strategies
    GET  /internal/resilience/metrics: Get comprehensive resilience metrics for all operations
    GET  /internal/resilience/metrics/{operation_name}: Get metrics for a specific operation
    POST /internal/resilience/metrics/reset: Reset metrics for specific or all operations
    GET  /internal/resilience/dashboard: Get dashboard-style summary for monitoring systems

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
        GET /internal/resilience/health

    To get comprehensive metrics for monitoring:
        GET /internal/resilience/dashboard

    To reset metrics for a specific operation:
        POST /internal/resilience/metrics/reset?operation_name=summarize

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
from typing import Dict, Any
from datetime import datetime
from app.core.config import Settings, settings
from app.infrastructure.security.auth import verify_api_key, optional_verify_api_key
from app.infrastructure.resilience.orchestrator import ai_resilience
from app.api.internal.resilience.models import CurrentConfigResponse, ResilienceMetricsResponse

main_router = APIRouter(prefix='/resilience', tags=['Resilience Core'])

config_router = APIRouter(prefix='/resilience/config', tags=['Resilience Configuration'])


def get_settings() -> Settings:
    """
    Get the global settings instance.
    """
    ...


@main_router.get('/health')
async def get_resilience_health() -> Dict[str, Any]:
    """
    Comprehensive resilience infrastructure health assessment endpoint with circuit breaker monitoring.
    
    This endpoint provides real-time health validation for the complete AI resilience infrastructure,
    including circuit breaker states, failure detection systems, and overall service operational status.
    It serves as the primary health validation interface for resilience monitoring systems, enabling
    operational teams to assess resilience system effectiveness and identify degradation patterns.
    
    Returns:
        dict: Comprehensive resilience health assessment containing:
             - healthy: Boolean indicating overall resilience system operational health status
             - status: Human-readable status indicator ("healthy" or "degraded") for monitoring integration
             - details: Detailed health breakdown including circuit breaker states, failure patterns,
                       and operational metrics for comprehensive system health visibility
    
    Raises:
        HTTPException: 500 Internal Server Error when resilience health assessment fails due to
                      infrastructure issues or when critical resilience components become unavailable,
                      preventing basic health status determination.
    
    Behavior:
        **Resilience Health Assessment:**
        - Evaluates overall resilience infrastructure operational status and system health
        - Validates circuit breaker states and failure detection mechanism effectiveness
        - Assesses resilience pattern performance and system degradation indicators
        - Provides real-time operational health status for monitoring and alerting systems
    
        **Circuit Breaker Monitoring:**
        - Reports current states of all registered circuit breakers (open, closed, half-open)
        - Provides circuit breaker effectiveness metrics and failure threshold monitoring
        - Includes circuit breaker activation history and recovery pattern analysis
        - Enables circuit breaker performance optimization and threshold adjustment
    
        **System Health Determination:**
        - Aggregates individual component health into overall system status assessment
        - Applies sophisticated health determination logic based on circuit breaker states
        - Provides degradation detection with detailed failure pattern analysis
        - Maintains health status consistency for reliable monitoring integration
    
        **Operational Integration:**
        - Structures health data for integration with monitoring and alerting platforms
        - Provides detailed diagnostic information for troubleshooting and analysis
        - Enables resilience system performance optimization through health visibility
        - Supports operational dashboards and health monitoring workflow integration
    
    Examples:
        >>> # Comprehensive resilience health assessment
        >>> response = await client.get("/internal/resilience/health")
        >>> assert response.status_code == 200
        >>> health = response.json()
        >>> assert "healthy" in health and "status" in health
        >>>
        >>> # Circuit breaker health validation
        >>> if health["healthy"]:
        ...     print("Resilience system operational")
        ...     circuit_breakers = health["details"].get("circuit_breakers", {})
        ...     for breaker_name, breaker_status in circuit_breakers.items():
        ...         if breaker_status.get("state") == "open":
        ...             print(f"Circuit breaker {breaker_name} is open - degraded service")
    
        >>> # Operational monitoring integration
        >>> async def monitor_resilience_health():
        ...     health_response = await client.get("/internal/resilience/health")
        ...     resilience_health = health_response.json()
        ...
        ...     alerts = []
        ...     if not resilience_health["healthy"]:
        ...         alerts.append("resilience_system_degraded")
        ...
        ...     # Check individual circuit breakers
        ...     cb_details = resilience_health["details"].get("circuit_breakers", {})
        ...     for cb_name, cb_info in cb_details.items():
        ...         if cb_info.get("state") == "open":
        ...             alerts.append(f"circuit_breaker_open_{cb_name}")
        ...
        ...     return {
        ...         "healthy": resilience_health["healthy"],
        ...         "alerts": alerts,
        ...         "status": resilience_health["status"]
        ...     }
    
        >>> # Dashboard integration for operational visibility
        >>> def prepare_resilience_dashboard(health_data):
        ...     cb_states = health_data["details"].get("circuit_breakers", {})
        ...     cb_summary = {}
        ...     for name, info in cb_states.items():
        ...         state = info.get("state", "unknown")
        ...         cb_summary[name] = {
        ...             "status": "🟢" if state == "closed" else "🔴" if state == "open" else "🟡",
        ...             "state": state
        ...         }
        ...
        ...     return {
        ...         "overall_health": health_data["status"],
        ...         "circuit_breakers": cb_summary,
        ...         "system_operational": health_data["healthy"]
        ...     }
    
        >>> # Automated alerting integration
        >>> async def check_resilience_alerts():
        ...     try:
        ...         health = await client.get("/internal/resilience/health").json()
        ...         if health["status"] == "degraded":
        ...             await send_alert("Resilience system degraded",
        ...                            details=health["details"])
        ...         return health["healthy"]
        ...     except Exception as e:
        ...         await send_critical_alert(f"Resilience health check failed: {e}")
        ...         return False
    
    Note:
        This endpoint provides comprehensive resilience infrastructure health monitoring and is
        designed for integration with operational monitoring systems, alerting platforms, and
        resilience performance dashboards. It enables proactive detection of resilience system
        degradation and supports optimization of resilience patterns through detailed health
        visibility and circuit breaker performance analysis.
    """
    ...


@config_router.get('', response_model=CurrentConfigResponse)
async def get_current_config(app_settings: Settings = Depends(get_settings), api_key: str = Depends(verify_api_key)) -> CurrentConfigResponse:
    """
    Get the current resilience configuration with preset information and operation strategies.
    
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
    ...


@main_router.get('/metrics', response_model=ResilienceMetricsResponse)
async def get_resilience_metrics(api_key: str = Depends(verify_api_key)) -> ResilienceMetricsResponse:
    """
    Get comprehensive resilience metrics for all operations.
    
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
    ...


@main_router.get('/metrics/{operation_name}')
async def get_operation_metrics(operation_name: str, api_key: str = Depends(verify_api_key)) -> Dict[str, Any]:
    """
    Get detailed metrics for a specific resilience operation.
    
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
    ...


@main_router.post('/metrics/reset')
async def reset_resilience_metrics(operation_name: str | None = Query(None, description='Operation name to reset (if None, resets all)'), api_key: str = Depends(verify_api_key)) -> Dict[str, Any]:
    """
    Reset resilience metrics for a specific operation or all operations.
    
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
    ...


@main_router.get('/dashboard')
async def get_resilience_dashboard(api_key: str = Depends(optional_verify_api_key)) -> Dict[str, Any]:
    """
    Get comprehensive resilience dashboard data for monitoring systems.
    
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
    ...
