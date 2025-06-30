"""Resilience performance benchmarking and analysis REST API endpoints.

This module provides comprehensive REST API endpoints for performance
benchmarking, threshold management, and performance analysis of resilience
configurations and operations. It includes capabilities for running custom
benchmarks, analyzing historical performance data, and generating detailed
performance reports with recommendations.

The module implements sophisticated performance measurement and analysis
tools that help optimize resilience configurations for maximum efficiency
and reliability. All endpoints provide detailed performance insights with
actionable recommendations for system optimization.

Endpoints:
    GET  /resilience/performance/benchmark: Run comprehensive performance benchmark suite
    POST /resilience/performance/benchmark: Run custom performance benchmarks with specific parameters
    GET  /resilience/performance/thresholds: Get performance thresholds and targets (optional auth)
    GET  /resilience/performance/report: Generate detailed performance analysis report
    GET  /resilience/performance/history: Retrieve historical performance data and trends

Performance Benchmarking Features:
    - Comprehensive benchmark suite with multiple test scenarios
    - Custom benchmark configuration with specific operations and iterations
    - Performance threshold validation and compliance checking
    - Historical performance tracking and trend analysis
    - Detailed performance reporting with optimization recommendations

Benchmark Operations:
    - Preset loading performance measurement
    - Settings initialization timing analysis
    - Resilience configuration loading benchmarks
    - Service initialization performance testing
    - Custom configuration loading efficiency analysis
    - Legacy configuration compatibility performance
    - Validation performance optimization testing

Performance Metrics:
    - Average, minimum, and maximum execution times
    - Standard deviation analysis for consistency measurement
    - Memory usage tracking and peak memory consumption
    - Success rate monitoring and failure analysis
    - Throughput measurement and capacity planning
    - Performance target compliance and threshold validation

Benchmark Customization:
    - Configurable iteration counts for statistical accuracy
    - Selective operation benchmarking for focused analysis
    - Custom performance thresholds and target setting
    - Memory tracking with peak usage analysis
    - Statistical analysis with standard deviation calculation

Dependencies:
    - PerformanceBenchmark: Core benchmarking engine with multiple test scenarios
    - PerformanceThreshold: Configurable performance targets and limits
    - BenchmarkSuite: Comprehensive benchmark orchestration and results aggregation
    - Security: API key verification for most endpoints (thresholds endpoint has optional auth)

Authentication:
    Most endpoints require API key authentication for secure access to
    performance data. The thresholds endpoint supports optional authentication
    for monitoring system compatibility.

Example:
    Run comprehensive benchmark suite:
        GET /api/internal/resilience/performance/benchmark?iterations=100
        
    Run custom benchmarks for specific operations:
        POST /api/internal/resilience/performance/benchmark
        {
            "iterations": 50,
            "operations": ["preset_loading", "validation_performance"],
            "include_slow": false
        }
        
    Get performance thresholds:
        GET /api/internal/resilience/performance/thresholds

Note:
    Performance benchmarks provide valuable insights for optimization but
    may cause temporary CPU and memory spikes during execution. Historical
    data helps identify performance trends and regression issues over time.
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

from app.api.internal.resilience.models import BenchmarkRunRequest


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/resilience/performance", tags=["resilience-performance"])

@router.get("/benchmark")
async def run_performance_benchmark(
    iterations: int = 50,
    include_slow: bool = False,
    api_key: str = Depends(verify_api_key)
):
    """Run comprehensive performance benchmark suite for resilience configuration operations.

    This endpoint executes a complete performance benchmark suite covering all
    key resilience operations, providing detailed performance metrics, success
    rates, and health assessments for monitoring and optimization purposes.
    
    Args:
        iterations: Number of iterations for each benchmark operation (default: 50)
        include_slow: Include slow/intensive benchmarks that take longer (default: False)
        api_key: API key for authentication (injected via dependency)
        
    Returns:
        Dict[str, Any]: Comprehensive benchmark results containing:
            - benchmark_suite: Complete suite results with detailed metrics
            - summary: Performance summary including:
                - total_benchmarks: Number of benchmark operations executed
                - pass_rate: Overall pass rate (0.0-1.0) for performance targets
                - total_duration_ms: Total execution time for all benchmarks
                - failed_benchmarks: List of failed benchmark operations
                - performance_target_met: Boolean indicating 80% pass rate threshold
                
    Raises:
        HTTPException: 500 Internal Server Error if benchmark execution fails
        
    Example:
        >>> response = await run_performance_benchmark(iterations=100)
        >>> {
        ...     "benchmark_suite": {...},
        ...     "summary": {
        ...         "total_benchmarks": 7,
        ...         "pass_rate": 0.857,
        ...         "total_duration_ms": 2850,
        ...         "failed_benchmarks": [],
        ...         "performance_target_met": True
        ...     }
        ... }
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


@router.post("/benchmark")
async def run_custom_performance_benchmark(
    request: BenchmarkRunRequest,
    api_key: str = Depends(verify_api_key)
):
    """Run custom performance benchmarks with specific operations and parameters.

    This endpoint allows selective execution of performance benchmarks with
    custom parameters, providing flexibility for targeted performance analysis
    and optimization of specific resilience operations.
    
    Args:
        request: Custom benchmark configuration containing:
                - iterations: Number of iterations per benchmark
                - operations: Optional list of specific operations to benchmark
                - include_slow: Whether to include intensive benchmarks
        api_key: API key for authentication (injected via dependency)
        
    Returns:
        Dict[str, Any]: Custom benchmark results containing:
            - results: List of individual benchmark results with:
                - operation: Benchmark operation name
                - avg_duration_ms: Average execution time
                - min_duration_ms: Minimum execution time
                - max_duration_ms: Maximum execution time
                - std_dev_ms: Standard deviation of execution times
                - memory_peak_mb: Peak memory usage in megabytes
                - success_rate: Operation success rate (0.0-1.0)
                - iterations: Number of iterations executed
                - metadata: Additional benchmark metadata
            - summary: Overall benchmark summary with performance analysis
                
    Raises:
        HTTPException: 400 Bad Request if unknown operation specified
        HTTPException: 500 Internal Server Error if benchmark execution fails
        
    Example:
        >>> request = BenchmarkRunRequest(
        ...     iterations=25,
        ...     operations=["preset_loading", "validation_performance"]
        ... )
        >>> response = await run_custom_performance_benchmark(request)
        >>> {
        ...     "results": [
        ...         {
        ...             "operation": "preset_loading",
        ...             "avg_duration_ms": 8.5,
        ...             "success_rate": 1.0
        ...         }
        ...     ],
        ...     "summary": {...}
        ... }
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


@router.get("/thresholds")
async def get_performance_thresholds(api_key: str = Depends(optional_verify_api_key)):
    """Get performance thresholds and targets for resilience configuration operations.

    This endpoint provides comprehensive information about performance thresholds,
    targets, and measurement standards used for benchmarking and monitoring
    resilience configuration operations.
    
    Args:
        api_key: Optional API key for authentication (injected via dependency)
        
    Returns:
        Dict[str, Any]: Performance threshold information containing:
            - thresholds: Performance thresholds in milliseconds for:
                - config_loading_ms: Configuration loading threshold
                - preset_access_ms: Preset access threshold
                - validation_ms: Configuration validation threshold
                - service_initialization_ms: Service initialization threshold
            - targets: Performance targets and objectives including:
                - primary_target: Main performance target description
                - secondary_targets: List of secondary performance objectives
            - measurement_info: Measurement methodology including:
                - default_iterations: Default iteration count for benchmarks
                - memory_tracking: Memory measurement description
                - timing_precision: Timing measurement precision details
                
    Raises:
        HTTPException: 500 Internal Server Error if threshold retrieval fails
        
    Note:
        This endpoint supports optional authentication for monitoring system
        compatibility and can be accessed without authentication.
        
    Example:
        >>> response = await get_performance_thresholds()
        >>> {
        ...     "thresholds": {
        ...         "config_loading_ms": 100,
        ...         "preset_access_ms": 10,
        ...         "validation_ms": 50
        ...     },
        ...     "targets": {
        ...         "primary_target": "Configuration loading under 100ms"
        ...     },
        ...     "measurement_info": {...}
        ... }
    """
    try:
        from app.infrastructure.resilience.performance_benchmarks import PerformanceThreshold
        
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


@router.get("/report")
async def get_performance_report(
    format: str = "json",
    api_key: str = Depends(verify_api_key)
):
    """Generate comprehensive performance analysis report with recommendations.

    This endpoint provides detailed performance reports in multiple formats,
    including benchmark analysis, performance assessments, and actionable
    recommendations for optimizing resilience configuration operations.
    
    Args:
        format: Report output format specification ("json" or "text")
        api_key: API key for authentication (injected via dependency)
        
    Returns:
        Dict[str, Any]: Performance report containing:
            - format: Requested report format
            - report or suite: Report content (text format) or structured data (json format)
            - timestamp: Report generation timestamp
            - analysis: Performance analysis including:
                - performance_summary: Key performance metrics
                - avg_config_loading_ms: Average configuration loading time
                - avg_preset_loading_ms: Average preset loading time
                - target_met: Boolean indicating performance targets met
                - recommendations: List of optimization recommendations
                
    Raises:
        HTTPException: 500 Internal Server Error if report generation fails
        
    Example:
        >>> response = await get_performance_report("json")
        >>> {
        ...     "format": "json",
        ...     "suite": {...},
        ...     "analysis": {
        ...         "performance_summary": {
        ...             "avg_config_loading_ms": 85.2,
        ...             "target_met": True
        ...         },
        ...         "recommendations": [
        ...             "Configuration loading meets <100ms target",
        ...             "Memory usage is efficient"
        ...         ]
        ...     }
        ... }
    """
    try:
        # Run quick benchmark if no recent results
        if not performance_benchmark.results:
            suite = performance_benchmark.run_comprehensive_benchmark()
        else:
            # Create suite from current results
            from app.infrastructure.resilience.performance_benchmarks import BenchmarkSuite
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


@router.get("/history")
async def get_performance_history(
    limit: int = 10,
    api_key: str = Depends(verify_api_key)
):
    """Get historical performance benchmark data and trend analysis.

    This endpoint provides access to historical performance benchmark results
    and trend analysis for tracking performance changes over time, identifying
    regressions, and monitoring performance improvements.
    
    Args:
        limit: Maximum number of historical records to return (default: 10)
        api_key: API key for authentication (injected via dependency)
        
    Returns:
        Dict[str, Any]: Historical performance data containing:
            - message: Current implementation status message
            - note: Information about planned functionality
            - expected_features: List of planned features including:
                - Historical benchmark results storage
                - Performance trend analysis capabilities
                - Regression detection algorithms
                - Performance baseline comparison tools
            - current_results: Current benchmark results for reference
            
    Raises:
        HTTPException: 500 Internal Server Error if history retrieval fails
        
    Note:
        This endpoint is currently under development. Future implementation
        will provide comprehensive historical tracking and trend analysis
        for performance benchmarks with regression detection capabilities.
        
    Example:
        >>> response = await get_performance_history(limit=5)
        >>> {
        ...     "message": "Performance history tracking not yet implemented",
        ...     "expected_features": [
        ...         "Historical benchmark results",
        ...         "Performance trend analysis",
        ...         "Regression detection"
        ...     ],
        ...     "current_results": [...]
        ... }
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

