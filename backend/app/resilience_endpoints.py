"""
Additional API endpoints for resilience monitoring and management.
"""

from fastapi import APIRouter, Depends, HTTPException, status
from typing import Dict, Any, Optional, List
from datetime import datetime
from pydantic import BaseModel
from app.auth import verify_api_key, optional_verify_api_key
from app.services.resilience import ai_resilience
from app.services.text_processor import TextProcessorService
from app.dependencies import get_text_processor
from app.performance_benchmarks import performance_benchmark
from app.validation_schemas import config_validator


class BenchmarkRunRequest(BaseModel):
    """Request model for running performance benchmarks."""
    iterations: int = 50
    include_slow: bool = False
    operations: Optional[List[str]] = None  # Specific operations to benchmark


class ValidationRequest(BaseModel):
    """Request model for configuration validation."""
    configuration: Dict[str, Any]

# Create a router for resilience endpoints
resilience_router = APIRouter(prefix="/resilience", tags=["resilience"])

@resilience_router.get("/health")
async def get_resilience_health(
    api_key: str = Depends(optional_verify_api_key),
    text_processor: TextProcessorService = Depends(get_text_processor)
):
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
            "new_state": breaker.state
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to reset circuit breaker: {str(e)}"
        )

@resilience_router.get("/config")
async def get_resilience_config(
    api_key: str = Depends(verify_api_key),
    text_processor: TextProcessorService = Depends(get_text_processor)
):
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


# Configuration Monitoring Endpoints

@resilience_router.get("/monitoring/usage-statistics")
async def get_configuration_usage_statistics(
    time_window_hours: int = 24,
    api_key: str = Depends(verify_api_key)
):
    """
    Get configuration usage statistics.
    
    Args:
        time_window_hours: Time window for statistics (default: 24 hours)
    
    Returns:
        Configuration usage statistics and trends
    """
    try:
        from app.config_monitoring import config_metrics_collector
        
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


@resilience_router.get("/monitoring/preset-trends/{preset_name}")
async def get_preset_usage_trend(
    preset_name: str,
    hours: int = 24,
    api_key: str = Depends(verify_api_key)
):
    """
    Get usage trend for a specific preset.
    
    Args:
        preset_name: Name of the preset to analyze
        hours: Number of hours to analyze (default: 24)
    
    Returns:
        Hourly usage trend data for the preset
    """
    try:
        from app.config_monitoring import config_metrics_collector
        
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


@resilience_router.get("/monitoring/performance-metrics")
async def get_configuration_performance_metrics(
    hours: int = 24,
    api_key: str = Depends(verify_api_key)
):
    """
    Get configuration performance metrics.
    
    Args:
        hours: Number of hours to analyze (default: 24)
    
    Returns:
        Performance metrics for configuration operations
    """
    try:
        from app.config_monitoring import config_metrics_collector
        
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


@resilience_router.get("/monitoring/alerts")
async def get_configuration_alerts(
    max_alerts: int = 50,
    level: Optional[str] = None,
    api_key: str = Depends(verify_api_key)
):
    """
    Get active configuration alerts.
    
    Args:
        max_alerts: Maximum number of alerts to return (default: 50)
        level: Filter by alert level (info, warning, error, critical)
    
    Returns:
        List of active configuration alerts
    """
    try:
        from app.config_monitoring import config_metrics_collector
        
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


@resilience_router.get("/monitoring/session/{session_id}")
async def get_session_configuration_metrics(
    session_id: str,
    api_key: str = Depends(verify_api_key)
):
    """
    Get configuration metrics for a specific session.
    
    Args:
        session_id: Session identifier
    
    Returns:
        Configuration metrics for the session
    """
    try:
        from app.config_monitoring import config_metrics_collector
        
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


@resilience_router.get("/monitoring/export")
async def export_configuration_metrics(
    format: str = "json",
    time_window_hours: Optional[int] = None,
    api_key: str = Depends(verify_api_key)
):
    """
    Export configuration metrics data.
    
    Args:
        format: Export format ('json' or 'csv')
        time_window_hours: Time window for export (None for all data)
    
    Returns:
        Exported metrics data
    """
    try:
        from app.config_monitoring import config_metrics_collector
        
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


@resilience_router.post("/monitoring/cleanup")
async def cleanup_old_metrics(
    hours: int = 24,
    api_key: str = Depends(verify_api_key)
):
    """
    Cleanup old configuration metrics.
    
    Args:
        hours: Remove metrics older than this many hours
    
    Returns:
        Cleanup summary
    """
    try:
        from app.config_monitoring import config_metrics_collector
        
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


# Performance Benchmarking Endpoints

@resilience_router.get("/performance/benchmark")
async def run_performance_benchmark(
    iterations: int = 50,
    include_slow: bool = False,
    api_key: str = Depends(verify_api_key)
):
    """
    Run comprehensive performance benchmark suite.
    
    Args:
        iterations: Number of iterations for each benchmark (default: 50)
        include_slow: Include slow benchmarks that take longer to run (default: False)
    
    Returns:
        Complete benchmark suite results with performance metrics
    """
    try:
        # Reset previous results
        performance_benchmark.results = []
        
        # Run comprehensive benchmark
        suite = performance_benchmark.run_comprehensive_benchmark()
        
        return {
            "benchmark_suite": suite.to_dict(),
            "summary": {
                "total_benchmarks": len(suite.results),
                "pass_rate": suite.pass_rate,
                "total_duration_ms": suite.total_duration_ms,
                "failed_benchmarks": suite.failed_benchmarks,
                "performance_target_met": suite.pass_rate >= 0.8  # 80% pass rate
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run performance benchmark: {str(e)}"
        )


@resilience_router.post("/performance/benchmark")
async def run_custom_performance_benchmark(
    request: BenchmarkRunRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Run custom performance benchmark with specific parameters.
    
    Args:
        request: Custom benchmark configuration
    
    Returns:
        Custom benchmark results
    """
    try:
        # Reset previous results
        performance_benchmark.results = []
        
        benchmark_methods = {
            "preset_loading": performance_benchmark.benchmark_preset_loading,
            "settings_initialization": performance_benchmark.benchmark_settings_initialization,
            "resilience_config_loading": performance_benchmark.benchmark_resilience_config_loading,
            "service_initialization": performance_benchmark.benchmark_service_initialization,
            "custom_config_loading": performance_benchmark.benchmark_custom_config_loading,
            "legacy_config_loading": performance_benchmark.benchmark_legacy_config_loading,
            "validation_performance": performance_benchmark.benchmark_validation_performance
        }
        
        # Run specific benchmarks if requested
        if request.operations:
            results = []
            for operation in request.operations:
                if operation in benchmark_methods:
                    result = benchmark_methods[operation](iterations=request.iterations)
                    results.append(result)
                else:
                    raise HTTPException(
                        status_code=status.HTTP_400_BAD_REQUEST,
                        detail=f"Unknown benchmark operation: {operation}"
                    )
        else:
            # Run all benchmarks
            suite = performance_benchmark.run_comprehensive_benchmark()
            results = suite.results
        
        # Calculate overall performance metrics
        total_duration = sum(result.duration_ms for result in results)
        avg_duration = sum(result.avg_duration_ms for result in results) / len(results) if results else 0
        success_rate = sum(result.success_rate for result in results) / len(results) if results else 0
        
        return {
            "results": [
                {
                    "operation": result.operation,
                    "avg_duration_ms": result.avg_duration_ms,
                    "min_duration_ms": result.min_duration_ms,
                    "max_duration_ms": result.max_duration_ms,
                    "std_dev_ms": result.std_dev_ms,
                    "memory_peak_mb": result.memory_peak_mb,
                    "success_rate": result.success_rate,
                    "iterations": result.iterations,
                    "metadata": result.metadata
                }
                for result in results
            ],
            "summary": {
                "total_benchmarks": len(results),
                "total_duration_ms": total_duration,
                "avg_duration_ms": avg_duration,
                "overall_success_rate": success_rate,
                "performance_target_met": avg_duration < 100.0  # <100ms target
            }
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to run custom benchmark: {str(e)}"
        )


@resilience_router.get("/performance/thresholds")
async def get_performance_thresholds(api_key: str = Depends(optional_verify_api_key)):
    """
    Get performance thresholds for different operations.
    
    Returns:
        Performance thresholds and targets for configuration operations
    """
    try:
        from app.performance_benchmarks import PerformanceThreshold
        
        return {
            "thresholds": {
                "config_loading_ms": PerformanceThreshold.CONFIG_LOADING.value,
                "preset_access_ms": PerformanceThreshold.PRESET_ACCESS.value,
                "validation_ms": PerformanceThreshold.VALIDATION.value,
                "service_initialization_ms": PerformanceThreshold.SERVICE_INIT.value
            },
            "targets": {
                "primary_target": "Configuration loading under 100ms",
                "secondary_targets": [
                    "Preset access under 10ms",
                    "Validation under 50ms",
                    "Service initialization under 200ms"
                ]
            },
            "measurement_info": {
                "default_iterations": 50,
                "memory_tracking": "Peak memory usage in MB",
                "timing_precision": "Microsecond precision with perf_counter"
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get performance thresholds: {str(e)}"
        )


@resilience_router.get("/performance/report")
async def get_performance_report(
    format: str = "json",
    api_key: str = Depends(verify_api_key)
):
    """
    Get detailed performance report.
    
    Args:
        format: Report format ('json' or 'text')
    
    Returns:
        Detailed performance report with analysis and recommendations
    """
    try:
        # Run quick benchmark if no recent results
        if not performance_benchmark.results:
            suite = performance_benchmark.run_comprehensive_benchmark()
        else:
            # Create suite from current results
            from app.performance_benchmarks import BenchmarkSuite
            import time
            suite = BenchmarkSuite(
                name="Current Performance Results",
                results=performance_benchmark.results,
                total_duration_ms=sum(r.duration_ms for r in performance_benchmark.results),
                pass_rate=len(performance_benchmark._check_performance_thresholds()) / len(performance_benchmark.results),
                failed_benchmarks=[],
                timestamp=time.strftime("%Y-%m-%d %H:%M:%S UTC", time.gmtime()),
                environment_info=performance_benchmark._collect_environment_info()
            )
        
        if format.lower() == "text":
            # Return text report
            report_text = performance_benchmark.generate_performance_report(suite)
            return {
                "format": "text",
                "report": report_text,
                "timestamp": suite.timestamp
            }
        else:
            # Return JSON report
            return {
                "format": "json",
                "suite": suite.to_dict(),
                "analysis": {
                    "performance_summary": {
                        "avg_config_loading_ms": next(
                            (r.avg_duration_ms for r in suite.results if r.operation == "resilience_config_loading"),
                            None
                        ),
                        "avg_preset_loading_ms": next(
                            (r.avg_duration_ms for r in suite.results if r.operation == "preset_loading"),
                            None
                        ),
                        "target_met": suite.pass_rate >= 0.8
                    },
                    "recommendations": [
                        "Configuration loading meets <100ms target" if suite.pass_rate >= 0.8 
                        else "Consider optimizing configuration loading performance",
                        "Memory usage is efficient" if all(r.memory_peak_mb < 50 for r in suite.results) 
                        else "Review memory usage in configuration operations"
                    ]
                }
            }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to generate performance report: {str(e)}"
        )


@resilience_router.get("/performance/history")
async def get_performance_history(
    limit: int = 10,
    api_key: str = Depends(verify_api_key)
):
    """
    Get performance benchmark history and trends.
    
    Args:
        limit: Maximum number of historical records to return
    
    Returns:
        Historical performance data and trend analysis
    """
    try:
        # Note: In a real implementation, this would query a database
        # For now, return placeholder data showing the expected format
        
        return {
            "message": "Performance history tracking not yet implemented",
            "note": "This endpoint will provide historical performance data and trend analysis",
            "expected_features": [
                "Historical benchmark results",
                "Performance trend analysis",
                "Regression detection",
                "Performance baseline comparison"
            ],
            "current_results": [
                {
                    "operation": result.operation,
                    "avg_duration_ms": result.avg_duration_ms,
                    "timestamp": "current"
                }
                for result in performance_benchmark.results[-limit:]
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get performance history: {str(e)}"
        )


# Security Validation Endpoints

@resilience_router.post("/validate/security")
async def validate_configuration_security(
    request: ValidationRequest,
    client_ip: str = "unknown",
    api_key: str = Depends(verify_api_key)
):
    """
    Validate configuration with enhanced security checks.
    
    Args:
        request: Configuration validation request
        client_ip: Client IP address for rate limiting
    
    Returns:
        Comprehensive security validation results
    """
    try:
        # Use client IP as identifier for rate limiting
        result = config_validator.validate_with_security_checks(
            request.configuration, 
            client_identifier=client_ip
        )
        
        return {
            "is_valid": result.is_valid,
            "errors": result.errors,
            "warnings": result.warnings,
            "suggestions": result.suggestions,
            "security_info": {
                "size_bytes": len(str(request.configuration)),
                "max_size_bytes": 4096,
                "field_count": len(request.configuration) if isinstance(request.configuration, dict) else 0,
                "validation_timestamp": datetime.now().isoformat()
            }
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate configuration security: {str(e)}"
        )


@resilience_router.get("/validate/rate-limit-status")
async def get_validation_rate_limit_status(
    client_ip: str = "unknown",
    api_key: str = Depends(verify_api_key)
):
    """
    Get current rate limit status for validation requests.
    
    Args:
        client_ip: Client IP address
    
    Returns:
        Current rate limit status and quotas
    """
    try:
        status_info = config_validator.get_rate_limit_info(client_ip)
        
        return {
            "client_identifier": client_ip,
            "current_status": status_info,
            "limits": {
                "max_validations_per_minute": 60,
                "max_validations_per_hour": 1000,
                "cooldown_seconds": 1
            },
            "check_timestamp": datetime.now().isoformat()
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get rate limit status: {str(e)}"
        )


@resilience_router.get("/validate/security-config")
async def get_security_configuration(
    api_key: str = Depends(verify_api_key)
):
    """
    Get current security validation configuration and limits.
    
    Returns:
        Security validation configuration details
    """
    try:
        from app.validation_schemas import SECURITY_CONFIG
        
        return {
            "security_limits": {
                "max_config_size_bytes": SECURITY_CONFIG["max_config_size"],
                "max_string_length": SECURITY_CONFIG["max_string_length"],
                "max_array_items": SECURITY_CONFIG["max_array_items"],
                "max_object_properties": SECURITY_CONFIG["max_object_properties"],
                "max_nesting_depth": SECURITY_CONFIG["max_nesting_depth"]
            },
            "rate_limiting": SECURITY_CONFIG["rate_limiting"],
            "content_filtering": SECURITY_CONFIG["content_filtering"],
            "allowed_fields": list(SECURITY_CONFIG["allowed_field_whitelist"].keys()),
            "forbidden_pattern_count": len(SECURITY_CONFIG["forbidden_patterns"]),
            "validation_features": [
                "Size limits",
                "Field whitelisting", 
                "Content filtering",
                "Rate limiting",
                "Unicode validation",
                "Nesting depth limits",
                "Pattern detection"
            ]
        }
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get security configuration: {str(e)}"
        )


@resilience_router.post("/validate/field-whitelist")
async def validate_against_field_whitelist(
    request: ValidationRequest,
    api_key: str = Depends(verify_api_key)
):
    """
    Validate configuration specifically against field whitelist.
    
    Args:
        request: Configuration validation request
    
    Returns:
        Field whitelist validation results
    """
    try:
        if not isinstance(request.configuration, dict):
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Configuration must be a JSON object for field validation"
            )
        
        # Perform only field whitelist validation
        errors, suggestions = config_validator._validate_field_whitelist(request.configuration)
        
        from app.validation_schemas import SECURITY_CONFIG
        whitelist = SECURITY_CONFIG["allowed_field_whitelist"]
        
        field_analysis = {}
        for field_name, field_value in request.configuration.items():
            if field_name in whitelist:
                field_spec = whitelist[field_name]
                field_analysis[field_name] = {
                    "allowed": True,
                    "type": field_spec["type"],
                    "constraints": {k: v for k, v in field_spec.items() if k != "type"},
                    "current_value": field_value,
                    "current_type": type(field_value).__name__
                }
            else:
                field_analysis[field_name] = {
                    "allowed": False,
                    "current_value": field_value,
                    "current_type": type(field_value).__name__
                }
        
        return {
            "is_valid": len(errors) == 0,
            "errors": errors,
            "suggestions": suggestions,
            "field_analysis": field_analysis,
            "allowed_fields": list(whitelist.keys()),
            "validation_timestamp": datetime.now().isoformat()
        }
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to validate field whitelist: {str(e)}"
        ) 