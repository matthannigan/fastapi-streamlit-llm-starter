# Resilience performance benchmarking and analysis REST API endpoints.

This module provides comprehensive REST API endpoints for performance
benchmarking, threshold management, and performance analysis of resilience
configurations and operations. It includes capabilities for running custom
benchmarks, analyzing historical performance data, and generating detailed
performance reports with recommendations.

The module implements sophisticated performance measurement and analysis
tools that help optimize resilience configurations for maximum efficiency
and reliability. All endpoints provide detailed performance insights with
actionable recommendations for system optimization.

## Endpoints

GET  /resilience/performance/benchmark: Run comprehensive performance benchmark suite
POST /resilience/performance/benchmark: Run custom performance benchmarks with specific parameters
GET  /resilience/performance/thresholds: Get performance thresholds and targets (optional auth)
GET  /resilience/performance/report: Generate detailed performance analysis report
GET  /resilience/performance/history: Retrieve historical performance data and trends

## Performance Benchmarking Features

- Comprehensive benchmark suite with multiple test scenarios
- Custom benchmark configuration with specific operations and iterations
- Performance threshold validation and compliance checking
- Historical performance tracking and trend analysis
- Detailed performance reporting with optimization recommendations

## Benchmark Operations

- Preset loading performance measurement
- Settings initialization timing analysis
- Resilience configuration loading benchmarks
- Service initialization performance testing
- Custom configuration loading efficiency analysis
- Legacy configuration compatibility performance
- Validation performance optimization testing

## Performance Metrics

- Average, minimum, and maximum execution times
- Standard deviation analysis for consistency measurement
- Memory usage tracking and peak memory consumption
- Success rate monitoring and failure analysis
- Throughput measurement and capacity planning
- Performance target compliance and threshold validation

## Benchmark Customization

- Configurable iteration counts for statistical accuracy
- Selective operation benchmarking for focused analysis
- Custom performance thresholds and target setting
- Memory tracking with peak usage analysis
- Statistical analysis with standard deviation calculation

## Dependencies

- PerformanceBenchmark: Core benchmarking engine with multiple test scenarios
- PerformanceThreshold: Configurable performance targets and limits
- BenchmarkSuite: Comprehensive benchmark orchestration and results aggregation
- Security: API key verification for most endpoints (thresholds endpoint has optional auth)

## Authentication

Most endpoints require API key authentication for secure access to
performance data. The thresholds endpoint supports optional authentication
for monitoring system compatibility.

## Example

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

## Note

Performance benchmarks provide valuable insights for optimization but
may cause temporary CPU and memory spikes during execution. Historical
data helps identify performance trends and regression issues over time.
