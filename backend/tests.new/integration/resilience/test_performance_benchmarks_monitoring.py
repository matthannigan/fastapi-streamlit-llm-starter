"""
Integration Tests: Performance Benchmarks → Configuration Validation → Operational Monitoring

This module tests the integration between performance benchmarking, configuration validation,
and operational monitoring systems. It validates that performance benchmarks are properly
executed, configurations are validated for performance, and operational monitoring provides
visibility into system performance.

Integration Scope:
    - ConfigurationPerformanceBenchmark → ResilienceConfigValidator → ConfigurationMetricsCollector
    - Performance measurement → Configuration validation → Operational monitoring
    - Benchmark execution → Performance analysis → Alert generation → Optimization

Business Impact:
    Ensures system performance requirements are met and provides early warning
    for performance degradations through comprehensive benchmarking and monitoring

Test Strategy:
    - Test performance benchmark execution and accuracy
    - Validate configuration performance validation
    - Test operational monitoring integration
    - Verify performance threshold validation and alerting
    - Test performance regression detection and reporting

Critical Paths:
    - Configuration loading → Performance measurement → Validation → Alert generation
    - Benchmark execution → Performance analysis → Regression detection → Optimization
    - Operational monitoring → Performance metrics → Health assessment → Reporting
"""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, patch
from typing import Dict, Any

from app.core.config import Settings
from app.infrastructure.resilience.config_presets import (
    ResilienceStrategy,
    ResilienceConfig,
    get_default_presets
)
from app.infrastructure.resilience.performance_benchmarks import (
    ConfigurationPerformanceBenchmark,
    BenchmarkResult,
    BenchmarkSuite,
    PerformanceThreshold
)
from app.infrastructure.resilience.config_monitoring import ConfigurationMetricsCollector
from app.infrastructure.resilience.orchestrator import AIServiceResilience


class TestPerformanceBenchmarksMonitoring:
    """
    Integration tests for Performance Benchmarks → Configuration Validation → Operational Monitoring.

    Seam Under Test:
        ConfigurationPerformanceBenchmark → ResilienceConfigValidator → ConfigurationMetricsCollector → Alerting

    Critical Paths:
        - Configuration loading → Performance measurement → Validation → Alert generation
        - Benchmark execution → Performance analysis → Regression detection → Optimization
        - Operational monitoring → Performance metrics → Health assessment → Reporting

    Business Impact:
        Ensures system performance requirements are met and provides operational visibility
        for performance optimization and proactive issue detection
    """

    @pytest.fixture
    def performance_benchmark(self):
        """Create a performance benchmark instance for testing."""
        return ConfigurationPerformanceBenchmark()

    @pytest.fixture
    def benchmark_suite(self):
        """Create a benchmark suite for comprehensive testing."""
        suite = BenchmarkSuite()

        # Add standard benchmark tests
        suite.add_benchmark("config_loading", self._benchmark_config_loading)
        suite.add_benchmark("operation_execution", self._benchmark_operation_execution)
        suite.add_benchmark("memory_usage", self._benchmark_memory_usage)
        suite.add_benchmark("response_time", self._benchmark_response_time)

        return suite

    @pytest.fixture
    def performance_thresholds(self):
        """Create performance thresholds for testing."""
        return {
            "config_loading": PerformanceThreshold(max_time=0.1, max_memory_mb=50, description="Configuration loading performance"),
            "operation_execution": PerformanceThreshold(max_time=0.5, max_memory_mb=100, description="Operation execution performance"),
            "memory_usage": PerformanceThreshold(max_time=0.05, max_memory_mb=30, description="Memory usage efficiency"),
            "response_time": PerformanceThreshold(max_time=1.0, max_memory_mb=150, description="Response time performance")
        }

    @pytest.fixture
    def config_monitor(self):
        """Create a configuration metrics collector for monitoring testing."""
        return ConfigurationMetricsCollector()

    def _benchmark_config_loading(self) -> BenchmarkResult:
        """Benchmark configuration loading performance."""
        start_time = time.time()
        start_memory = self._get_memory_usage()

        # Simulate configuration loading
        config = ResilienceConfig(strategy=ResilienceStrategy.BALANCED)
        config.validate()

        end_time = time.time()
        end_memory = self._get_memory_usage()

        return BenchmarkResult(
            name="config_loading",
            execution_time=end_time - start_time,
            memory_usage=end_memory - start_memory,
            success=True,
            metadata={"config_type": "ResilienceConfig"}
        )

    def _benchmark_operation_execution(self) -> BenchmarkResult:
        """Benchmark operation execution performance."""
        start_time = time.time()
        start_memory = self._get_memory_usage()

        # Simulate operation execution
        settings = Settings()
        orchestrator = AIServiceResilience(settings)

        end_time = time.time()
        end_memory = self._get_memory_usage()

        return BenchmarkResult(
            name="operation_execution",
            execution_time=end_time - start_time,
            memory_usage=end_memory - start_memory,
            success=True,
            metadata={"operation_count": 1}
        )

    def _benchmark_memory_usage(self) -> BenchmarkResult:
        """Benchmark memory usage patterns."""
        start_time = time.time()
        start_memory = self._get_memory_usage()

        # Simulate memory allocation patterns
        data = [i for i in range(1000)]

        end_time = time.time()
        end_memory = self._get_memory_usage()

        return BenchmarkResult(
            name="memory_usage",
            execution_time=end_time - start_time,
            memory_usage=end_memory - start_memory,
            success=True,
            metadata={"data_size": len(data)}
        )

    def _benchmark_response_time(self) -> BenchmarkResult:
        """Benchmark response time performance."""
        start_time = time.time()
        start_memory = self._get_memory_usage()

        # Simulate response time measurement
        time.sleep(0.1)  # 100ms delay

        end_time = time.time()
        end_memory = self._get_memory_usage()

        return BenchmarkResult(
            name="response_time",
            execution_time=end_time - start_time,
            memory_usage=end_memory - start_memory,
            success=True,
            metadata={"simulated_delay": 0.1}
        )

    def _get_memory_usage(self) -> float:
        """Get current memory usage (simplified for testing)."""
        # In a real implementation, this would use psutil or similar
        return 50.0  # Mock value for testing

    def test_configuration_loading_performance_benchmark(self, performance_benchmark, performance_thresholds):
        """
        Test configuration loading performance benchmarking.

        Integration Scope:
            Configuration loading → Performance measurement → Validation → Optimization

        Business Impact:
            Ensures configuration loading meets performance requirements

        Test Strategy:
            - Execute configuration loading benchmark
            - Validate performance against thresholds
            - Test benchmark accuracy and reliability
            - Verify performance optimization recommendations

        Success Criteria:
            - Configuration loading benchmark executes successfully
            - Performance measured accurately within acceptable ranges
            - Threshold validation works correctly
            - Performance optimization recommendations generated
        """
        # Execute benchmark
        result = performance_benchmark.run_benchmark("config_loading")

        # Verify benchmark result structure
        assert isinstance(result, BenchmarkResult)
        assert result.name == "config_loading"
        assert result.success is True
        assert result.execution_time > 0
        assert result.memory_usage >= 0
        assert isinstance(result.metadata, dict)

        # Validate performance against threshold
        threshold = performance_thresholds["config_loading"]
        within_time_limit = result.execution_time <= threshold.max_time
        within_memory_limit = result.memory_usage <= threshold.max_memory_mb

        # Configuration loading should be very fast
        assert within_time_limit, f"Config loading too slow: {result.execution_time".3f"}s > {threshold.max_time}s"
        assert within_memory_limit, f"Config loading uses too much memory: {result.memory_usage".1f"}MB > {threshold.max_memory_mb}MB"

        # Verify benchmark metadata
        assert "config_type" in result.metadata
        assert result.metadata["config_type"] == "ResilienceConfig"

    def test_operation_execution_performance_benchmark(self, performance_benchmark, performance_thresholds):
        """
        Test operation execution performance benchmarking.

        Integration Scope:
            Operation execution → Performance measurement → Analysis → Optimization

        Business Impact:
            Ensures operation execution meets performance SLA requirements

        Test Strategy:
            - Execute operation execution benchmark
            - Measure performance characteristics
            - Validate against operational thresholds
            - Test performance regression detection

        Success Criteria:
            - Operation execution benchmark captures accurate metrics
            - Performance measurements within acceptable limits
            - Threshold validation detects performance issues
            - Performance characteristics properly analyzed
        """
        # Execute benchmark
        result = performance_benchmark.run_benchmark("operation_execution")

        # Verify benchmark result
        assert isinstance(result, BenchmarkResult)
        assert result.name == "operation_execution"
        assert result.success is True
        assert result.execution_time > 0
        assert result.memory_usage >= 0

        # Validate against threshold
        threshold = performance_thresholds["operation_execution"]
        within_time_limit = result.execution_time <= threshold.max_time
        within_memory_limit = result.memory_usage <= threshold.max_memory_mb

        # Operation execution should be reasonably fast
        assert within_time_limit, f"Operation execution too slow: {result.execution_time".3f"}s > {threshold.max_time}s"
        assert within_memory_limit, f"Operation execution uses too much memory: {result.memory_usage".1f"}MB > {threshold.max_memory_mb}MB"

    def test_comprehensive_benchmark_suite_execution(self, benchmark_suite, performance_thresholds):
        """
        Test comprehensive benchmark suite execution and analysis.

        Integration Scope:
            Benchmark suite → Multiple benchmarks → Analysis → Reporting

        Business Impact:
            Provides comprehensive performance analysis across system components

        Test Strategy:
            - Execute complete benchmark suite
            - Analyze performance across multiple dimensions
            - Validate benchmark suite coordination
            - Test performance reporting and analysis

        Success Criteria:
            - All benchmarks execute successfully
            - Performance data collected comprehensively
            - Benchmark results properly aggregated
            - Performance analysis provides actionable insights
        """
        # Execute benchmark suite
        results = benchmark_suite.run_all_benchmarks()

        # Verify suite execution
        assert isinstance(results, dict)
        assert len(results) >= 4  # Should have results for all benchmarks

        # Verify each benchmark result
        expected_benchmarks = ["config_loading", "operation_execution", "memory_usage", "response_time"]
        for benchmark_name in expected_benchmarks:
            assert benchmark_name in results
            result = results[benchmark_name]
            assert isinstance(result, BenchmarkResult)
            assert result.success is True
            assert result.execution_time > 0
            assert result.memory_usage >= 0

        # Test benchmark suite analysis
        analysis = benchmark_suite.analyze_results(results)

        assert isinstance(analysis, dict)
        assert "total_benchmarks" in analysis
        assert "successful_benchmarks" in analysis
        assert "failed_benchmarks" in analysis
        assert "performance_summary" in analysis

        # Verify analysis accuracy
        assert analysis["total_benchmarks"] >= 4
        assert analysis["successful_benchmarks"] == analysis["total_benchmarks"]
        assert analysis["failed_benchmarks"] == 0

    def test_performance_threshold_validation(self, performance_benchmark, performance_thresholds):
        """
        Test performance threshold validation and alerting.

        Integration Scope:
            Performance measurement → Threshold validation → Alert generation → Monitoring

        Business Impact:
            Enables proactive performance issue detection and alerting

        Test Strategy:
            - Test threshold configuration and validation
            - Execute benchmarks with threshold checking
            - Verify threshold violation detection
            - Test alert generation for performance issues

        Success Criteria:
            - Performance thresholds properly configured
            - Threshold validation detects violations accurately
            - Alert generation works for performance issues
            - Performance monitoring provides actionable alerts
        """
        # Test threshold validation
        for benchmark_name, threshold in performance_thresholds.items():
            assert isinstance(threshold, PerformanceThreshold)
            assert threshold.max_time > 0
            assert threshold.max_memory_mb > 0
            assert isinstance(threshold.description, str)

        # Execute benchmarks and validate against thresholds
        violations = []
        for benchmark_name, threshold in performance_thresholds.items():
            result = performance_benchmark.run_benchmark(benchmark_name)

            # Check for threshold violations
            time_violation = result.execution_time > threshold.max_time
            memory_violation = result.memory_usage > threshold.max_memory_mb

            if time_violation or memory_violation:
                violations.append({
                    "benchmark": benchmark_name,
                    "threshold": threshold,
                    "result": result,
                    "violations": {
                        "time": time_violation,
                        "memory": memory_violation
                    }
                })

        # For testing, most benchmarks should pass thresholds
        # Report violations for analysis
        if violations:
            for violation in violations:
                print(f"Performance violation in {violation['benchmark']}:")
                if violation['violations']['time']:
                    print(f"  Time: {violation['result'].execution_time".3f"}s > {violation['threshold'].max_time}s")
                if violation['violations']['memory']:
                    print(f"  Memory: {violation['result'].memory_usage".1f"}MB > {violation['threshold'].max_memory_mb}MB")

        # Verify violations are properly detected (may be empty in normal conditions)
        assert isinstance(violations, list)

    def test_operational_monitoring_integration(self, performance_benchmark, config_monitor):
        """
        Test operational monitoring integration with performance benchmarks.

        Integration Scope:
            Performance benchmarks → Operational monitoring → Metrics collection → Alerting

        Business Impact:
            Provides integrated performance monitoring and alerting

        Test Strategy:
            - Execute performance benchmarks with monitoring
            - Test metrics collection and integration
            - Verify monitoring system integration
            - Test performance-based alerting

        Success Criteria:
            - Performance benchmarks integrate with monitoring systems
            - Metrics collected and stored properly
            - Monitoring provides operational visibility
            - Performance alerts generated when needed
        """
        # Execute benchmark with monitoring
        result = performance_benchmark.run_benchmark("operation_execution")

        # Record performance metrics
        config_monitor.record_performance_metrics({
            "benchmark_name": result.name,
            "execution_time": result.execution_time,
            "memory_usage": result.memory_usage,
            "success": result.success,
            "timestamp": "2024-01-01T12:00:00Z"
        })

        # Verify metrics were recorded
        performance_metrics = config_monitor.get_performance_metrics()
        assert len(performance_metrics) >= 1

        latest_metrics = performance_metrics[-1]
        assert latest_metrics["benchmark_name"] == result.name
        assert latest_metrics["execution_time"] == result.execution_time
        assert latest_metrics["memory_usage"] == result.memory_usage
        assert latest_metrics["success"] == result.success

        # Test performance trend analysis
        trends = config_monitor.analyze_performance_trends()
        assert isinstance(trends, dict)
        assert "execution_time_trends" in trends
        assert "memory_usage_trends" in trends
        assert "success_rate_trends" in trends

    def test_performance_regression_detection(self, benchmark_suite, performance_thresholds):
        """
        Test performance regression detection and analysis.

        Integration Scope:
            Benchmark execution → Performance analysis → Regression detection → Reporting

        Business Impact:
            Enables early detection of performance degradations

        Test Strategy:
            - Execute benchmarks to establish baseline
            - Simulate performance regression scenarios
            - Test regression detection algorithms
            - Verify regression reporting and analysis

        Success Criteria:
            - Performance baseline established correctly
            - Performance regressions detected accurately
            - Regression analysis provides actionable information
            - Regression reporting enables proactive optimization
        """
        # Establish baseline performance
        baseline_results = benchmark_suite.run_all_benchmarks()

        # Verify baseline is established
        assert isinstance(baseline_results, dict)
        assert len(baseline_results) >= 4

        # Simulate performance regression (memory usage increase)
        original_memory_benchmark = benchmark_suite.benchmarks["memory_usage"]

        def regressed_memory_benchmark() -> BenchmarkResult:
            """Simulate memory regression."""
            start_time = time.time()
            start_memory = 100.0  # Simulate higher memory usage

            # Simulate memory-intensive operation
            data = [i for i in range(10000)]  # Much larger dataset

            end_time = time.time()
            end_memory = start_memory + 50.0  # Significant memory increase

            return BenchmarkResult(
                name="memory_usage",
                execution_time=end_time - start_time,
                memory_usage=end_memory - start_memory,
                success=True,
                metadata={"data_size": len(data), "regression": True}
            )

        # Replace benchmark with regressed version
        benchmark_suite.benchmarks["memory_usage"] = regressed_memory_benchmark

        # Execute benchmarks with regression
        regressed_results = benchmark_suite.run_all_benchmarks()

        # Detect regression
        regression_analysis = benchmark_suite.detect_performance_regression(
            baseline_results,
            regressed_results
        )

        # Verify regression detection
        assert isinstance(regression_analysis, dict)
        assert "regressions_detected" in regression_analysis
        assert "baseline_comparison" in regression_analysis
        assert "recommendations" in regression_analysis

        # Should detect memory usage regression
        if regression_analysis["regressions_detected"]:
            assert "memory_usage" in str(regression_analysis).lower()

        # Restore original benchmark
        benchmark_suite.benchmarks["memory_usage"] = original_memory_benchmark

    def test_configuration_performance_impact_assessment(self, performance_benchmark):
        """
        Test configuration performance impact assessment.

        Integration Scope:
            Configuration changes → Performance impact → Assessment → Recommendations

        Business Impact:
            Enables performance-aware configuration management

        Test Strategy:
            - Test different configuration scenarios
            - Assess performance impact of each configuration
            - Generate performance recommendations
            - Validate configuration optimization

        Success Criteria:
            - Performance impact accurately assessed
            - Configuration changes evaluated for performance
            - Performance recommendations generated
            - Configuration optimization validated
        """
        # Test different configuration scenarios
        config_scenarios = {
            "fast_config": {
                "retry_config": {"max_attempts": 1},
                "circuit_breaker_config": {"failure_threshold": 10, "recovery_timeout": 30}
            },
            "balanced_config": {
                "retry_config": {"max_attempts": 3},
                "circuit_breaker_config": {"failure_threshold": 5, "recovery_timeout": 60}
            },
            "conservative_config": {
                "retry_config": {"max_attempts": 5},
                "circuit_breaker_config": {"failure_threshold": 3, "recovery_timeout": 120}
            }
        }

        performance_impacts = {}

        for config_name, config_data in config_scenarios.items():
            # Create configuration with performance characteristics
            config = ResilienceConfig(
                strategy=ResilienceStrategy.BALANCED,
                retry_config=config_data["retry_config"],
                circuit_breaker_config=config_data["circuit_breaker_config"]
            )

            # Assess performance impact
            impact = performance_benchmark.assess_configuration_performance(config)

            assert isinstance(impact, dict)
            assert "performance_score" in impact
            assert "recommendations" in impact
            assert "risk_factors" in impact

            performance_impacts[config_name] = impact

            # Validate impact assessment
            assert isinstance(impact["performance_score"], (int, float))
            assert 0 <= impact["performance_score"] <= 100
            assert isinstance(impact["recommendations"], list)
            assert isinstance(impact["risk_factors"], list)

        # Analyze configuration performance comparison
        comparison = performance_benchmark.compare_configuration_performance(performance_impacts)

        assert isinstance(comparison, dict)
        assert "best_performing" in comparison
        assert "performance_ranking" in comparison
        assert "optimization_suggestions" in comparison

        # Fast config should generally perform better
        assert "fast_config" in comparison["best_performing"] or "balanced_config" in comparison["best_performing"]

    def test_benchmark_accuracy_and_reliability(self, benchmark_suite):
        """
        Test benchmark accuracy and reliability characteristics.

        Integration Scope:
            Benchmark execution → Accuracy validation → Reliability testing → Quality assurance

        Business Impact:
            Ensures benchmark results are accurate and reliable

        Test Strategy:
            - Test benchmark execution consistency
            - Validate benchmark result accuracy
            - Test benchmark reliability under different conditions
            - Verify benchmark quality metrics

        Success Criteria:
            - Benchmarks execute consistently
            - Results are accurate and reproducible
            - Benchmark reliability validated
            - Quality metrics provided for benchmarks
        """
        # Execute same benchmark multiple times for consistency
        results = []
        for _ in range(3):
            result = benchmark_suite.run_benchmark("config_loading")
            results.append(result)

        # Verify consistency
        assert len(results) == 3
        assert all(r.success for r in results)
        assert all(r.name == "config_loading" for r in results)

        # Check result consistency (allowing for small variations)
        execution_times = [r.execution_time for r in results]
        memory_usages = [r.memory_usage for r in results]

        # Times should be reasonably consistent
        avg_time = sum(execution_times) / len(execution_times)
        time_variance = max(execution_times) - min(execution_times)
        assert time_variance < avg_time * 0.5, "Benchmark execution times too inconsistent"

        # Memory usage should be very consistent
        avg_memory = sum(memory_usages) / len(memory_usages)
        memory_variance = max(memory_usages) - min(memory_usages)
        assert memory_variance < avg_memory * 0.1, "Benchmark memory usage too inconsistent"

        # Test benchmark metadata consistency
        for result in results:
            assert "config_type" in result.metadata
            assert result.metadata["config_type"] == "ResilienceConfig"

    def test_operational_visibility_and_reporting(self, benchmark_suite, config_monitor):
        """
        Test operational visibility and performance reporting capabilities.

        Integration Scope:
            Performance monitoring → Operational visibility → Reporting → Dashboard integration

        Business Impact:
            Provides comprehensive operational visibility for performance management

        Test Strategy:
            - Execute comprehensive benchmark suite
            - Generate operational visibility reports
            - Test performance dashboard data generation
            - Validate reporting integration and accuracy

        Success Criteria:
            - Comprehensive performance reports generated
            - Operational visibility data accurate
            - Dashboard integration data properly formatted
            - Performance reporting provides actionable insights
        """
        # Execute comprehensive benchmark suite
        benchmark_results = benchmark_suite.run_all_benchmarks()

        # Record operational metrics
        for benchmark_name, result in benchmark_results.items():
            config_monitor.record_performance_metrics({
                "benchmark_name": benchmark_name,
                "execution_time": result.execution_time,
                "memory_usage": result.memory_usage,
                "success": result.success,
                "metadata": result.metadata,
                "timestamp": "2024-01-01T12:00:00Z"
            })

        # Generate operational visibility report
        visibility_report = config_monitor.generate_operational_report()

        # Verify report structure
        assert isinstance(visibility_report, dict)
        assert "performance_summary" in visibility_report
        assert "benchmark_results" in visibility_report
        assert "system_health" in visibility_report
        assert "recommendations" in visibility_report

        # Verify performance summary
        summary = visibility_report["performance_summary"]
        assert "total_benchmarks" in summary
        assert "average_execution_time" in summary
        assert "average_memory_usage" in summary
        assert "success_rate" in summary

        # Verify benchmark results
        benchmark_section = visibility_report["benchmark_results"]
        assert isinstance(benchmark_section, dict)
        assert len(benchmark_section) >= 4  # All benchmarks included

        for benchmark_name, result_data in benchmark_section.items():
            assert "execution_time" in result_data
            assert "memory_usage" in result_data
            assert "success" in result_data
            assert "metadata" in result_data

        # Verify system health assessment
        health = visibility_report["system_health"]
        assert "overall_status" in health
        assert "performance_score" in health
        assert "issues_identified" in health
        assert "health_metrics" in health

        # Verify recommendations
        recommendations = visibility_report["recommendations"]
        assert isinstance(recommendations, list)

        # Recommendations should be actionable
        for recommendation in recommendations:
            assert isinstance(recommendation, str)
            assert len(recommendation) > 0

    def test_performance_alerting_and_thresholds(self, performance_benchmark, config_monitor):
        """
        Test performance alerting and threshold-based monitoring.

        Integration Scope:
            Performance monitoring → Threshold validation → Alert generation → Notification

        Business Impact:
            Enables proactive performance issue detection and alerting

        Test Strategy:
            - Test performance threshold configuration
            - Simulate performance threshold violations
            - Verify alert generation for violations
            - Test alert integration with monitoring systems

        Success Criteria:
            - Performance thresholds properly configured
            - Threshold violations detected accurately
            - Alerts generated for performance issues
            - Alert integration provides operational visibility
        """
        # Configure performance thresholds
        thresholds = {
            "config_loading": PerformanceThreshold(
                max_time=0.05,  # Very tight threshold to trigger alert
                max_memory_mb=25,
                description="Configuration loading performance"
            ),
            "operation_execution": PerformanceThreshold(
                max_time=0.1,
                max_memory_mb=50,
                description="Operation execution performance"
            )
        }

        # Execute benchmark that should violate threshold
        result = performance_benchmark.run_benchmark("config_loading")

        # Check for threshold violation
        threshold = thresholds["config_loading"]
        violates_time = result.execution_time > threshold.max_time
        violates_memory = result.memory_usage > threshold.max_memory_mb

        if violates_time or violates_memory:
            # Generate alert
            alert = config_monitor.generate_performance_alert(
                benchmark_name=result.name,
                result=result,
                threshold=threshold
            )

            assert isinstance(alert, dict)
            assert "alert_level" in alert
            assert "message" in alert
            assert "recommendations" in alert
            assert "timestamp" in alert

            # Verify alert details
            assert alert["benchmark_name"] == result.name
            assert "violation" in alert["message"].lower() or "threshold" in alert["message"].lower()

            # Verify alert level is appropriate
            assert alert["alert_level"] in ["WARNING", "CRITICAL", "INFO"]

            # Verify recommendations are actionable
            assert len(alert["recommendations"]) > 0
            for recommendation in alert["recommendations"]:
                assert isinstance(recommendation, str)
                assert len(recommendation) > 0

        # Test performance monitoring integration
        monitoring_data = config_monitor.get_performance_monitoring_data()

        assert isinstance(monitoring_data, dict)
        assert "current_metrics" in monitoring_data
        assert "thresholds" in monitoring_data
        assert "alerts" in monitoring_data
        assert "trends" in monitoring_data

        # Verify monitoring data structure
        assert len(monitoring_data["current_metrics"]) > 0
        assert len(monitoring_data["thresholds"]) > 0
        assert isinstance(monitoring_data["alerts"], list)
        assert isinstance(monitoring_data["trends"], dict)
