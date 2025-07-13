"""Resilience configuration monitoring and analytics REST API endpoints.

This module provides comprehensive REST API endpoints for monitoring resilience
configuration usage, performance metrics, alerts, and analytics. It includes
capabilities for tracking configuration usage patterns, analyzing performance
trends, managing alerts, and exporting monitoring data for external analysis.

The module implements sophisticated monitoring and analytics tools that provide
operational visibility into resilience system behavior, configuration usage
patterns, and performance characteristics across different time windows and
operational contexts.

Endpoints:
    GET /resilience/monitoring/usage-statistics: Configuration usage statistics and trends
    GET /resilience/monitoring/preset-trends/{preset_name}: Usage trends for specific presets
    GET /resilience/monitoring/performance-metrics: Performance metrics analysis
    GET /resilience/monitoring/alerts: Active configuration alerts and notifications
    GET /resilience/monitoring/session/{session_id}: Session-specific configuration metrics
    GET /resilience/monitoring/export: Export monitoring data in various formats
    POST /resilience/monitoring/cleanup: Clean up old metrics and monitoring data

Monitoring Features:
    - Real-time configuration usage tracking and analysis
    - Preset usage trends with time-series data
    - Performance metrics collection and aggregation
    - Alert management and notification systems
    - Session-based metrics tracking and analysis
    - Data export capabilities for external analysis

Usage Analytics:
    - Total configuration loads and access patterns
    - Preset usage frequency and popularity analysis
    - Error rate monitoring and threshold alerting
    - Load time performance tracking and optimization
    - Custom vs. legacy configuration adoption rates
    - Environment-specific usage pattern analysis

Performance Monitoring:
    - Average and percentile load time analysis
    - Error count tracking and trend analysis
    - Performance threshold compliance monitoring
    - P95 response time tracking for SLA compliance
    - Memory usage monitoring and optimization
    - Throughput analysis and capacity planning

Alert Management:
    - Multi-level alert system (info, warning, error, critical)
    - Configurable alert thresholds and triggers
    - Alert categorization and priority management
    - Real-time alert status monitoring
    - Alert history and trend analysis
    - Automated alert cleanup and management

Data Export and Cleanup:
    - Multiple export formats (JSON, CSV, etc.)
    - Configurable time window selection
    - Automated data cleanup and retention management
    - Session-based data export capabilities
    - Performance-optimized bulk data operations

Dependencies:
    - ConfigMetricsCollector: Core monitoring and metrics collection engine
    - ConfigMonitoring: Real-time monitoring and alert management
    - Analytics: Advanced analytics and trend analysis capabilities
    - Security: API key verification for all monitoring endpoints

Authentication:
    All monitoring endpoints require API key authentication to ensure
    secure access to operational data and prevent unauthorized monitoring.

Example:
    Get usage statistics for last 24 hours:
        GET /api/internal/resilience/monitoring/usage-statistics?time_window_hours=24
        
    Get performance metrics:
        GET /api/internal/resilience/monitoring/performance-metrics?hours=48
        
    Export monitoring data:
        GET /api/internal/resilience/monitoring/export?format=json&time_window_hours=168

Note:
    Monitoring data provides valuable operational insights but may include
    sensitive configuration information. Regular cleanup helps maintain
    system performance and data retention compliance.
"""

import json
import logging
import os

from fastapi import APIRouter, Depends, HTTPException, status, Query
from typing import Dict, List, Any, Optional
from datetime import datetime
from pydantic import BaseModel, Field

from app.core.config import Settings, settings
from app.infrastructure.security.auth import verify_api_key, optional_verify_api_key
from app.infrastructure.resilience.orchestrator import ai_resilience
from app.services.text_processor import TextProcessorService
from app.api.v1.deps import get_text_processor
from app.infrastructure.resilience.config_presets import preset_manager, PresetManager
from app.infrastructure.resilience.performance_benchmarks import performance_benchmark
from app.infrastructure.resilience.config_validator import config_validator, ValidationResult


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/resilience/monitoring", tags=["Resilience Monitoring"])

@router.get("/usage-statistics")
async def get_configuration_usage_statistics(
    time_window_hours: int = 24,
    api_key: str = Depends(verify_api_key)
):
    """Get comprehensive configuration usage statistics and trends.

    This endpoint provides detailed analytics on resilience configuration usage
    patterns, including preset adoption rates, error statistics, and performance
    metrics over a specified time window.
    
    Args:
        time_window_hours: Time window for statistics collection in hours (default: 24)
        api_key: API key for authentication (injected via dependency)
        
    Returns:
        Dict[str, Any]: Usage statistics containing:
            - time_window_hours: Requested time window
            - statistics: Core usage metrics including:
                - total_loads: Total configuration loads
                - preset_usage_count: Count of preset usage
                - error_rate: Configuration error rate
                - avg_load_time_ms: Average load time in milliseconds
                - most_used_preset: Most frequently used preset
                - least_used_preset: Least frequently used preset
                - custom_config_usage_rate: Rate of custom configuration usage
                - legacy_config_usage_rate: Rate of legacy configuration usage
            - summary: Health and performance summary including:
                - healthy: Boolean indicating healthy error rate (<5%)
                - performance_good: Boolean indicating good performance (<100ms)
                - preset_adoption: Rate of non-legacy configuration usage
            
    Raises:
        HTTPException: 500 Internal Server Error if statistics retrieval fails
        
    Example:
        >>> response = await get_configuration_usage_statistics(48)
        >>> {
        ...     "time_window_hours": 48,
        ...     "statistics": {
        ...         "total_loads": 1250,
        ...         "error_rate": 0.02,
        ...         "avg_load_time_ms": 85.5,
        ...         "most_used_preset": "production"
        ...     },
        ...     "summary": {
        ...         "healthy": True,
        ...         "performance_good": True,
        ...         "preset_adoption": 0.95
        ...     }
        ... }
    """
    try:
        from app.infrastructure.resilience.config_monitoring import config_metrics_collector
        
        stats = config_metrics_collector.get_usage_statistics(time_window_hours)
        
        return {
            "time_window_hours": time_window_hours,
            "statistics": {
                "total_loads": stats.total_loads,
                "preset_usage_count": stats.preset_usage_count,
                "error_rate": stats.error_rate,
                "avg_load_time_ms": stats.avg_load_time_ms,
                "most_used_preset": stats.most_used_preset,
                "least_used_preset": stats.least_used_preset,
                "custom_config_usage_rate": stats.custom_config_usage_rate,
                "legacy_config_usage_rate": stats.legacy_config_usage_rate
            },
            "summary": {
                "healthy": stats.error_rate < 0.05,  # Less than 5% error rate
                "performance_good": stats.avg_load_time_ms < 100.0,  # Less than 100ms
                "preset_adoption": 1.0 - stats.legacy_config_usage_rate  # Non-legacy usage
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get configuration usage statistics: {str(e)}"
        )


@router.get("/preset-trends/{preset_name}")
async def get_preset_usage_trend(
    preset_name: str,
    hours: int = 24,
    api_key: str = Depends(verify_api_key)
):
    """Get detailed usage trend analysis for a specific resilience preset.

    This endpoint provides time-series analysis of preset usage patterns,
    including hourly usage statistics, trend analysis, and comprehensive
    usage metrics for monitoring preset adoption and performance patterns.
    
    Args:
        preset_name: Name of the specific preset to analyze usage trends for
        hours: Number of hours to analyze for trend data (default: 24)
        api_key: API key for authentication (injected via dependency)
        
    Returns:
        Dict[str, Any]: Preset usage trend analysis containing:
            - preset_name: Name of the analyzed preset
            - time_window_hours: Analysis time window in hours
            - trend_data: List of hourly usage data points with timestamps
            - summary: Usage statistics including:
                - total_usage: Total usage count across time window
                - peak_usage: Maximum usage in any single hour
                - avg_hourly_usage: Average usage per hour
                
    Raises:
        HTTPException: 500 Internal Server Error if trend analysis fails
        
    Example:
        >>> response = await get_preset_usage_trend("production", 48)
        >>> {
        ...     "preset_name": "production",
        ...     "time_window_hours": 48,
        ...     "trend_data": [
        ...         {"hour": "2023-12-01T10:00:00Z", "usage_count": 25},
        ...         {"hour": "2023-12-01T11:00:00Z", "usage_count": 32}
        ...     ],
        ...     "summary": {
        ...         "total_usage": 1250,
        ...         "peak_usage": 45,
        ...         "avg_hourly_usage": 26.0
        ...     }
        ... }
    """
    try:
        from app.infrastructure.resilience.config_monitoring import config_metrics_collector
        
        trend_data = config_metrics_collector.get_preset_usage_trend(preset_name, hours)
        
        return {
            "preset_name": preset_name,
            "time_window_hours": hours,
            "trend_data": trend_data,
            "summary": {
                "total_usage": sum(point['usage_count'] for point in trend_data),
                "peak_usage": max(point['usage_count'] for point in trend_data) if trend_data else 0,
                "avg_hourly_usage": sum(point['usage_count'] for point in trend_data) / max(len(trend_data), 1)
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get preset usage trend: {str(e)}"
        )


@router.get("/performance-metrics")
async def get_configuration_performance_metrics(
    hours: int = 24,
    api_key: str = Depends(verify_api_key)
):
    """Get comprehensive performance metrics for resilience configuration operations.

    This endpoint provides detailed performance analysis of configuration operations,
    including load times, error rates, and performance health assessments with
    threshold-based evaluation for monitoring and alerting purposes.
    
    Args:
        hours: Number of hours to analyze for performance metrics (default: 24)
        api_key: API key for authentication (injected via dependency)
        
    Returns:
        Dict[str, Any]: Performance metrics analysis containing:
            - time_window_hours: Analysis time window in hours
            - performance_metrics: Detailed performance data including:
                - avg_load_time_ms: Average load time in milliseconds
                - error_count: Total number of errors
                - total_samples: Total number of operations sampled
                - p95_load_time_ms: 95th percentile load time
            - health_check: Performance health assessment including:
                - performance_good: Boolean indicating load times under 100ms
                - error_rate_acceptable: Boolean indicating error rate under 5%
                - p95_within_threshold: Boolean indicating P95 under 200ms
                
    Raises:
        HTTPException: 500 Internal Server Error if performance metrics retrieval fails
        
    Example:
        >>> response = await get_configuration_performance_metrics(24)
        >>> {
        ...     "time_window_hours": 24,
        ...     "performance_metrics": {
        ...         "avg_load_time_ms": 85.5,
        ...         "error_count": 12,
        ...         "total_samples": 1500,
        ...         "p95_load_time_ms": 180.2
        ...     },
        ...     "health_check": {
        ...         "performance_good": True,
        ...         "error_rate_acceptable": True,
        ...         "p95_within_threshold": True
        ...     }
        ... }
    """
    try:
        from app.infrastructure.resilience.config_monitoring import config_metrics_collector
        
        metrics = config_metrics_collector.get_performance_metrics(hours)
        
        return {
            "time_window_hours": hours,
            "performance_metrics": metrics,
            "health_check": {
                "performance_good": metrics['avg_load_time_ms'] < 100.0,
                "error_rate_acceptable": metrics['error_count'] / max(metrics['total_samples'], 1) < 0.05,
                "p95_within_threshold": metrics['p95_load_time_ms'] < 200.0
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get configuration performance metrics: {str(e)}"
        )


@router.get("/alerts")
async def get_configuration_alerts(
    max_alerts: int = 50,
    level: Optional[str] = None,
    api_key: str = Depends(verify_api_key)
):
    """Get active configuration alerts and notifications for monitoring systems.

    This endpoint provides comprehensive alert information including active alerts,
    alert categorization by severity level, and summary statistics for monitoring
    dashboards and notification systems.
    
    Args:
        max_alerts: Maximum number of alerts to return (default: 50)
        level: Optional filter by alert level ("info", "warning", "error", "critical")
        api_key: API key for authentication (injected via dependency)
        
    Returns:
        Dict[str, Any]: Active alerts information containing:
            - alerts: List of active alert objects with details
            - summary: Alert statistics including:
                - total_alerts: Total number of active alerts
                - alert_counts: Count by level (info, warning, error, critical)
                - has_critical: Boolean indicating presence of critical alerts
                - has_errors: Boolean indicating presence of error alerts
                
    Raises:
        HTTPException: 500 Internal Server Error if alert retrieval fails
        
    Example:
        >>> response = await get_configuration_alerts(max_alerts=25, level="error")
        >>> {
        ...     "alerts": [
        ...         {
        ...             "level": "error",
        ...             "message": "High failure rate detected",
        ...             "timestamp": "2023-12-01T10:30:00Z"
        ...         }
        ...     ],
        ...     "summary": {
        ...         "total_alerts": 8,
        ...         "alert_counts": {"info": 2, "warning": 5, "error": 1, "critical": 0},
        ...         "has_critical": False,
        ...         "has_errors": True
        ...     }
        ... }
    """
    try:
        from app.infrastructure.resilience.config_monitoring import config_metrics_collector
        
        alerts = config_metrics_collector.get_active_alerts(max_alerts)
        
        # Filter by level if specified
        if level:
            alerts = [alert for alert in alerts if alert['level'] == level.lower()]
        
        # Categorize alerts
        alert_counts = {"info": 0, "warning": 0, "error": 0, "critical": 0}
        for alert in alerts:
            alert_counts[alert['level']] += 1
        
        return {
            "alerts": alerts,
            "summary": {
                "total_alerts": len(alerts),
                "alert_counts": alert_counts,
                "has_critical": alert_counts['critical'] > 0,
                "has_errors": alert_counts['error'] > 0
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get configuration alerts: {str(e)}"
        )


@router.get("/session/{session_id}")
async def get_session_configuration_metrics(
    session_id: str,
    api_key: str = Depends(verify_api_key)
):
    """Get comprehensive configuration metrics for a specific user session.

    This endpoint provides detailed session-specific metrics including preset usage,
    error tracking, performance data, and operational statistics for session-based
    monitoring and analysis of configuration behavior patterns.
    
    Args:
        session_id: Unique session identifier to retrieve metrics for
        api_key: API key for authentication (injected via dependency)
        
    Returns:
        Dict[str, Any]: Session configuration metrics containing:
            - session_id: Session identifier
            - metrics: List of session-specific metric records
            - summary: Session statistics including:
                - total_operations: Total configuration operations in session
                - preset_usage: Dictionary of preset usage counts
                - error_count: Number of configuration errors
                - error_rate: Calculated error rate (0.0-1.0)
                - avg_load_time_ms: Average configuration load time
                
    Raises:
        HTTPException: 500 Internal Server Error if session metrics retrieval fails
        
    Example:
        >>> response = await get_session_configuration_metrics("session_abc123")
        >>> {
        ...     "session_id": "session_abc123",
        ...     "metrics": [...],
        ...     "summary": {
        ...         "total_operations": 45,
        ...         "preset_usage": {"production": 30, "development": 15},
        ...         "error_count": 2,
        ...         "error_rate": 0.044,
        ...         "avg_load_time_ms": 95.3
        ...     }
        ... }
    """
    try:
        from app.infrastructure.resilience.config_monitoring import config_metrics_collector
        
        session_metrics = config_metrics_collector.get_session_metrics(session_id)
        
        # Calculate session statistics
        preset_usage = {}
        total_operations = len(session_metrics)
        error_count = 0
        load_times = []
        
        for metric in session_metrics:
            if metric['metric_type'] == 'preset_usage':
                preset_name = metric['preset_name']
                preset_usage[preset_name] = preset_usage.get(preset_name, 0) + 1
            elif metric['metric_type'] == 'config_error':
                error_count += 1
            elif metric['metric_type'] == 'config_load':
                load_times.append(metric['value'])
        
        return {
            "session_id": session_id,
            "metrics": session_metrics,
            "summary": {
                "total_operations": total_operations,
                "preset_usage": preset_usage,
                "error_count": error_count,
                "error_rate": error_count / max(total_operations, 1),
                "avg_load_time_ms": sum(load_times) / max(len(load_times), 1)
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get session configuration metrics: {str(e)}"
        )


@router.get("/export")
async def export_configuration_metrics(
    format: str = "json",
    time_window_hours: Optional[int] = None,
    api_key: str = Depends(verify_api_key)
):
    """Export configuration metrics data in multiple formats for external analysis.

    This endpoint provides data export capabilities for configuration metrics,
    supporting multiple output formats and configurable time windows for
    integration with external monitoring and analytics systems.
    
    Args:
        format: Export format specification ("json" or "csv")
        time_window_hours: Optional time window in hours for data export.
                          If None, exports all available data
        api_key: API key for authentication (injected via dependency)
        
    Returns:
        Dict[str, Any]: Export response containing:
            - format: Requested export format
            - time_window_hours: Time window used for export
            - data: Exported metrics data in the requested format
            - export_timestamp: Timestamp of the export operation
            
    Raises:
        HTTPException: 400 Bad Request if format is not supported
        HTTPException: 500 Internal Server Error if export operation fails
        
    Example:
        >>> response = await export_configuration_metrics("json", 24)
        >>> {
        ...     "format": "json",
        ...     "time_window_hours": 24,
        ...     "data": [...],
        ...     "export_timestamp": "2023-12-01T10:30:00Z"
        ... }
    """
    try:
        from app.infrastructure.resilience.config_monitoring import config_metrics_collector
        
        if format.lower() not in ['json', 'csv']:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Format must be 'json' or 'csv'"
            )
        
        exported_data = config_metrics_collector.export_metrics(format, time_window_hours)
        
        return {
            "format": format,
            "time_window_hours": time_window_hours,
            "data": exported_data,
            "export_timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        # Re-raise HTTP exceptions (like the 400 error above)
        raise
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to export configuration metrics: {str(e)}"
        )


@router.post("/cleanup")
async def cleanup_old_metrics(
    hours: int = 24,
    api_key: str = Depends(verify_api_key)
):
    """Clean up old configuration metrics and alerts to manage storage and performance.

    This endpoint removes metrics and alerts older than the specified threshold
    to maintain system performance and implement data retention policies. Provides
    detailed cleanup statistics for monitoring and auditing purposes.
    
    Args:
        hours: Time threshold in hours - remove metrics older than this (default: 24)
        api_key: API key for authentication (injected via dependency)
        
    Returns:
        Dict[str, Any]: Cleanup operation results containing:
            - cleanup_threshold_hours: Time threshold used for cleanup
            - metrics_removed: Number of metric records removed
            - alerts_removed: Number of alert records removed
            - metrics_remaining: Number of metric records remaining
            - alerts_remaining: Number of alert records remaining
            - cleanup_timestamp: Timestamp of the cleanup operation
            
    Raises:
        HTTPException: 500 Internal Server Error if cleanup operation fails
        
    Example:
        >>> response = await cleanup_old_metrics(48)
        >>> {
        ...     "cleanup_threshold_hours": 48,
        ...     "metrics_removed": 1250,
        ...     "alerts_removed": 45,
        ...     "metrics_remaining": 850,
        ...     "alerts_remaining": 12,
        ...     "cleanup_timestamp": "2023-12-01T10:30:00Z"
        ... }
    """
    try:
        from app.infrastructure.resilience.config_monitoring import config_metrics_collector
        
        # Get counts before cleanup
        total_metrics_before = len(config_metrics_collector.metrics)
        total_alerts_before = len(config_metrics_collector.alerts)
        
        config_metrics_collector.clear_old_metrics(hours)
        
        # Get counts after cleanup
        total_metrics_after = len(config_metrics_collector.metrics)
        total_alerts_after = len(config_metrics_collector.alerts)
        
        return {
            "cleanup_threshold_hours": hours,
            "metrics_removed": total_metrics_before - total_metrics_after,
            "alerts_removed": total_alerts_before - total_alerts_after,
            "metrics_remaining": total_metrics_after,
            "alerts_remaining": total_alerts_after,
            "cleanup_timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to cleanup old metrics: {str(e)}"
        )
