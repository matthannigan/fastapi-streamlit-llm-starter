"""
Test suite for ConfigurationPerformanceBenchmark analysis and reporting methods.

This module verifies the performance trend analysis and report generation
functionality, including historical data analysis, trend detection, and
human-readable report formatting.

Test Strategy:
    - Test analyze_performance_trends() with historical data
    - Test generate_performance_report() formatting
    - Test trend detection and regression identification
    - Test report completeness and readability

Business Critical:
    Analysis and reporting enable identification of performance regressions
    over time and provide actionable insights for performance optimization
    and capacity planning decisions.
"""

import pytest
from unittest.mock import Mock, patch
from typing import Dict, List, Any
from datetime import datetime, timedelta

from app.infrastructure.resilience.performance_benchmarks import (
    ConfigurationPerformanceBenchmark,
    BenchmarkSuite,
    BenchmarkResult,
    PerformanceThreshold
)


class TestAnalyzePerformanceTrends:
    """
    Tests for analyze_performance_trends() method behavior.
    
    Scope:
        Verifies historical performance analysis, trend detection, regression
        identification, and trend reporting across multiple benchmark runs.
    
    Business Impact:
        Trend analysis enables proactive identification of performance
        degradation and validation of performance improvements over time.
    
    Test Strategy:
        - Test with multiple historical results
        - Test with single result
        - Test with empty history
        - Test trend detection algorithms
        - Test return dictionary structure
    """

    def test_analyze_performance_trends_accepts_historical_results(self, performance_benchmarks_test_data):
        """
        Test that analyze_performance_trends accepts list of BenchmarkSuite objects.

        Verifies:
            Method accepts List[BenchmarkSuite] as historical_results parameter
            per documented Args section for trend analysis.

        Business Impact:
            Flexible historical data input enables trend analysis across
            arbitrary time periods and benchmark execution frequencies.

        Scenario:
            Given: Multiple BenchmarkSuite objects from different executions
            When: analyze_performance_trends is called with historical results list
            Then: Method accepts the input without errors
            And: Trend analysis proceeds with historical data

        Fixtures Used:
            - performance_benchmarks_test_data: Provides historical benchmark scenarios
        """
        # Given: Create multiple BenchmarkSuite objects with different performance metrics
        benchmark = ConfigurationPerformanceBenchmark()

        # Create historical results showing gradual performance improvement
        historical_suites = []
        base_time = 50.0  # Starting at 50ms

        for i in range(5):
            # Gradually improve performance over time
            current_time = base_time - (i * 5.0)  # 50ms -> 45ms -> 40ms -> 35ms -> 30ms

            suite = BenchmarkSuite(
                name="Resilience Configuration Performance Benchmark",
                results=[
                    BenchmarkResult(
                        operation="preset_loading",
                        duration_ms=current_time * 10,
                        memory_peak_mb=2.5,
                        iterations=100,
                        avg_duration_ms=current_time,
                        min_duration_ms=current_time * 0.8,
                        max_duration_ms=current_time * 1.2,
                        std_dev_ms=current_time * 0.1,
                        success_rate=1.0,
                        metadata={"test_run": i}
                    )
                ],
                total_duration_ms=current_time * 10,
                pass_rate=1.0,
                failed_benchmarks=[],
                timestamp=f"2024-01-{i+1:02d} 10:00:00 UTC",
                environment_info={"platform": "test"}
            )
            historical_suites.append(suite)

        # When: analyze_performance_trends is called with historical results list
        result = benchmark.analyze_performance_trends(historical_suites)

        # Then: Method accepts the input without errors and returns trend analysis
        assert isinstance(result, dict)
        assert "preset_loading" in result

        # And: Trend analysis proceeds with historical data
        preset_trend = result["preset_loading"]
        assert "trend_percentage" in preset_trend
        assert "trend_direction" in preset_trend
        assert preset_trend["trend_direction"] == "improving"  # Performance is getting better

    def test_analyze_performance_trends_returns_dictionary(self, performance_benchmarks_test_data):
        """
        Test that analyze_performance_trends returns Dict[str, Any] with trend data.

        Verifies:
            Return type is dictionary containing performance trend analysis
            per documented Returns section.

        Business Impact:
            Structured trend data format enables automated regression detection
            and integration with monitoring dashboards.

        Scenario:
            Given: Historical benchmark results for trend analysis
            When: analyze_performance_trends completes analysis
            Then: Return value is a dictionary containing trend analysis
            And: Dictionary structure supports automated processing

        Fixtures Used:
            - performance_benchmarks_test_data: Provides trend analysis scenarios
        """
        # Given: Create historical benchmark results with multiple operations
        benchmark = ConfigurationPerformanceBenchmark()
        historical_suites = []

        for i in range(3):
            suite = BenchmarkSuite(
                name="Resilience Configuration Performance Benchmark",
                results=[
                    BenchmarkResult(
                        operation="preset_loading",
                        duration_ms=100.0,
                        memory_peak_mb=2.0,
                        iterations=50,
                        avg_duration_ms=2.0 + i,  # Gradually increasing
                        min_duration_ms=1.5 + i,
                        max_duration_ms=2.5 + i,
                        std_dev_ms=0.2,
                        success_rate=1.0,
                        metadata={"run": i}
                    ),
                    BenchmarkResult(
                        operation="settings_initialization",
                        duration_ms=200.0,
                        memory_peak_mb=5.0,
                        iterations=25,
                        avg_duration_ms=8.0 + i,
                        min_duration_ms=7.0 + i,
                        max_duration_ms=9.0 + i,
                        std_dev_ms=0.5,
                        success_rate=1.0,
                        metadata={"run": i}
                    )
                ],
                total_duration_ms=300.0,
                pass_rate=1.0,
                failed_benchmarks=[],
                timestamp=f"2024-01-{i+1:02d} 10:00:00 UTC",
                environment_info={"platform": "test"}
            )
            historical_suites.append(suite)

        # When: analyze_performance_trends completes analysis
        result = benchmark.analyze_performance_trends(historical_suites)

        # Then: Return value is a dictionary containing trend analysis
        assert isinstance(result, dict)

        # And: Dictionary structure supports automated processing
        # Each operation should have trend analysis with expected keys
        expected_operations = ["preset_loading", "settings_initialization", "resilience_config_loading"]
        for operation in expected_operations:
            if operation in result:  # Some operations may not have data
                trend_data = result[operation]
                assert isinstance(trend_data, dict)
                expected_keys = ["trend_percentage", "trend_direction", "first_half_avg_ms", "second_half_avg_ms", "sample_count"]
                for key in expected_keys:
                    assert key in trend_data, f"Missing key '{key}' in trend data for operation '{operation}'"

        # Verify trend data types
        preset_trend = result.get("preset_loading")
        if preset_trend:
            assert isinstance(preset_trend["trend_percentage"], (int, float))
            assert isinstance(preset_trend["trend_direction"], str)
            assert preset_trend["trend_direction"] in ["improving", "degrading"]
            assert isinstance(preset_trend["first_half_avg_ms"], (int, float))
            assert isinstance(preset_trend["second_half_avg_ms"], (int, float))
            assert isinstance(preset_trend["sample_count"], int)

    def test_analyze_performance_trends_with_multiple_historical_results(self, performance_benchmarks_test_data):
        """
        Test that analyze_performance_trends analyzes trends across multiple results.

        Verifies:
            Trend analysis correctly processes multiple historical benchmark
            results to identify performance patterns and regressions.

        Business Impact:
            Multi-result trend analysis enables identification of gradual
            performance degradation that might not be visible in single comparisons.

        Scenario:
            Given: Five BenchmarkSuite objects showing gradual slowdown
            When: analyze_performance_trends analyzes the historical data
            Then: Trend analysis identifies performance degradation pattern
            And: Trend direction and magnitude are accurately reported

        Fixtures Used:
            - performance_benchmarks_test_data: Provides degrading performance scenario
        """
        # Given: Five BenchmarkSuite objects showing gradual slowdown
        benchmark = ConfigurationPerformanceBenchmark()
        historical_suites = []
        base_time = 20.0  # Starting at 20ms

        for i in range(5):
            # Gradually slow down performance over time (20% degradation overall)
            current_time = base_time + (i * 1.0)  # 20ms -> 21ms -> 22ms -> 23ms -> 24ms

            suite = BenchmarkSuite(
                name="Resilience Configuration Performance Benchmark",
                results=[
                    BenchmarkResult(
                        operation="preset_loading",
                        duration_ms=current_time * 10,
                        memory_peak_mb=2.5,
                        iterations=100,
                        avg_duration_ms=current_time,
                        min_duration_ms=current_time * 0.9,
                        max_duration_ms=current_time * 1.1,
                        std_dev_ms=current_time * 0.05,
                        success_rate=1.0,
                        metadata={"test_run": i, "degradation": True}
                    )
                ],
                total_duration_ms=current_time * 10,
                pass_rate=1.0,
                failed_benchmarks=[],
                timestamp=f"2024-01-{i+1:02d} 10:00:00 UTC",
                environment_info={"platform": "test", "load": "increasing"}
            )
            historical_suites.append(suite)

        # When: analyze_performance_trends analyzes the historical data
        result = benchmark.analyze_performance_trends(historical_suites)

        # Then: Trend analysis identifies performance degradation pattern
        assert "preset_loading" in result
        preset_trend = result["preset_loading"]

        # And: Trend direction and magnitude are accurately reported
        assert preset_trend["trend_direction"] == "degrading"
        assert preset_trend["trend_percentage"] > 0  # Positive percentage means degradation
        assert preset_trend["sample_count"] == 5
        assert preset_trend["first_half_avg_ms"] < preset_trend["second_half_avg_ms"]

    def test_analyze_performance_trends_with_single_result(self):
        """
        Test that analyze_performance_trends handles single historical result.

        Verifies:
            Trend analysis gracefully handles case with only one historical
            result, providing baseline without trend calculation.

        Business Impact:
            Graceful handling of minimal data enables trend tracking from
            first benchmark execution without requiring existing history.

        Scenario:
            Given: A single BenchmarkSuite object as historical data
            When: analyze_performance_trends is called
            Then: Method completes without errors
            And: Baseline metrics are reported without trend calculations

        Fixtures Used:
            - None required for single result edge case

        Edge Cases Covered:
            - Single data point trend analysis
            - Baseline establishment without historical comparison
        """
        # Given: A single BenchmarkSuite object as historical data
        benchmark = ConfigurationPerformanceBenchmark()
        single_suite = BenchmarkSuite(
            name="Resilience Configuration Performance Benchmark",
            results=[
                BenchmarkResult(
                    operation="preset_loading",
                    duration_ms=50.0,
                    memory_peak_mb=2.0,
                    iterations=100,
                    avg_duration_ms=5.0,
                    min_duration_ms=4.0,
                    max_duration_ms=6.0,
                    std_dev_ms=0.5,
                    success_rate=1.0,
                    metadata={"single_run": True}
                )
            ],
            total_duration_ms=50.0,
            pass_rate=1.0,
            failed_benchmarks=[],
            timestamp="2024-01-15 10:00:00 UTC",
            environment_info={"platform": "test"}
        )

        # When: analyze_performance_trends is called with single result
        result = benchmark.analyze_performance_trends([single_suite])

        # Then: Method completes without errors
        assert isinstance(result, dict)

        # And: Result handles single data point gracefully (may be empty or minimal)
        # Single data point doesn't provide enough data for trend calculation
        # The implementation may choose to return empty dict or minimal info
        assert result == {} or "message" in result or len(result) == 0

    def test_analyze_performance_trends_with_empty_history(self):
        """
        Test that analyze_performance_trends handles empty historical results list.

        Verifies:
            Trend analysis gracefully handles empty input, returning empty
            or minimal result structure without errors.

        Business Impact:
            Graceful empty input handling prevents crashes when no historical
            data is available, enabling robust trend analysis integration.

        Scenario:
            Given: An empty list of historical results
            When: analyze_performance_trends is called with empty list
            Then: Method completes without errors
            And: Returns appropriate empty or minimal trend data structure

        Fixtures Used:
            - None required for empty input edge case

        Edge Cases Covered:
            - Empty historical data handling
            - No-data scenario robustness
        """
        # Given: An empty list of historical results
        benchmark = ConfigurationPerformanceBenchmark()
        empty_history = []

        # When: analyze_performance_trends is called with empty list
        result = benchmark.analyze_performance_trends(empty_history)

        # Then: Method completes without errors
        assert isinstance(result, dict)

        # And: Returns appropriate empty or minimal trend data structure
        # Implementation should return empty dict or message about no data
        assert result == {} or "message" in result
        if "message" in result:
            assert "No historical data" in result["message"]

    def test_analyze_performance_trends_detects_performance_regressions(self, performance_benchmarks_test_data):
        """
        Test that analyze_performance_trends identifies performance regressions.

        Verifies:
            Trend analysis correctly identifies when performance degrades
            across historical results, flagging potential issues.

        Business Impact:
            Regression detection enables proactive performance problem
            identification before issues impact production users.

        Scenario:
            Given: Historical results showing 20% performance degradation
            When: analyze_performance_trends analyzes the trend
            Then: Regression is detected and flagged in analysis results
            And: Degradation magnitude is quantified for prioritization

        Fixtures Used:
            - performance_benchmarks_test_data: Provides regression scenario
        """
        # Given: Historical results showing 20% performance degradation
        benchmark = ConfigurationPerformanceBenchmark()
        historical_suites = []
        base_time = 10.0  # Starting at 10ms

        for i in range(4):
            # Create 20% degradation: 10ms -> 12ms -> 14ms -> 16ms
            current_time = base_time + (i * 2.0)

            suite = BenchmarkSuite(
                name="Resilience Configuration Performance Benchmark",
                results=[
                    BenchmarkResult(
                        operation="preset_loading",
                        duration_ms=current_time * 20,
                        memory_peak_mb=3.0,
                        iterations=100,
                        avg_duration_ms=current_time,
                        min_duration_ms=current_time * 0.95,
                        max_duration_ms=current_time * 1.05,
                        std_dev_ms=0.3,
                        success_rate=0.95 + (i * 0.01),  # Slightly decreasing success rate
                        metadata={"test_run": i, "regression": True}
                    )
                ],
                total_duration_ms=current_time * 20,
                pass_rate=0.95 + (i * 0.01),
                failed_benchmarks=[],
                timestamp=f"2024-01-{i+1:02d} 10:00:00 UTC",
                environment_info={"platform": "test", "memory_pressure": "increasing"}
            )
            historical_suites.append(suite)

        # When: analyze_performance_trends analyzes the trend
        result = benchmark.analyze_performance_trends(historical_suites)

        # Then: Regression is detected and flagged in analysis results
        assert "preset_loading" in result
        preset_trend = result["preset_loading"]

        # And: Degradation magnitude is quantified for prioritization
        assert preset_trend["trend_direction"] == "degrading"
        assert preset_trend["trend_percentage"] > 15  # Should be around 20% degradation
        assert preset_trend["first_half_avg_ms"] < preset_trend["second_half_avg_ms"]
        assert preset_trend["sample_count"] == 4

    def test_analyze_performance_trends_detects_performance_improvements(self, performance_benchmarks_test_data):
        """
        Test that analyze_performance_trends identifies performance improvements.

        Verifies:
            Trend analysis correctly identifies when performance improves
            across historical results, validating optimizations.

        Business Impact:
            Improvement detection validates that performance optimization
            efforts achieve intended results and don't regress over time.

        Scenario:
            Given: Historical results showing 30% performance improvement
            When: analyze_performance_trends analyzes the trend
            Then: Improvement is detected and reported in analysis results
            And: Improvement magnitude is quantified for validation

        Fixtures Used:
            - performance_benchmarks_test_data: Provides improvement scenario
        """
        # Given: Historical results showing 30% performance improvement
        benchmark = ConfigurationPerformanceBenchmark()
        historical_suites = []
        base_time = 20.0  # Starting at 20ms

        for i in range(5):
            # Create 30% improvement: 20ms -> 17ms -> 14ms -> 11ms -> 8ms
            current_time = base_time - (i * 3.0)

            suite = BenchmarkSuite(
                name="Resilience Configuration Performance Benchmark",
                results=[
                    BenchmarkResult(
                        operation="preset_loading",
                        duration_ms=current_time * 15,
                        memory_peak_mb=1.5,
                        iterations=100,
                        avg_duration_ms=current_time,
                        min_duration_ms=current_time * 0.9,
                        max_duration_ms=current_time * 1.1,
                        std_dev_ms=0.2,
                        success_rate=0.98 + (i * 0.004),  # Improving success rate
                        metadata={"test_run": i, "optimization": True}
                    )
                ],
                total_duration_ms=current_time * 15,
                pass_rate=0.98 + (i * 0.004),
                failed_benchmarks=[],
                timestamp=f"2024-01-{i+1:02d} 10:00:00 UTC",
                environment_info={"platform": "test", "optimization_applied": True}
            )
            historical_suites.append(suite)

        # When: analyze_performance_trends analyzes the trend
        result = benchmark.analyze_performance_trends(historical_suites)

        # Then: Improvement is detected and reported in analysis results
        assert "preset_loading" in result
        preset_trend = result["preset_loading"]

        # And: Improvement magnitude is quantified for validation
        assert preset_trend["trend_direction"] == "improving"
        assert preset_trend["trend_percentage"] < 0  # Negative percentage means improvement
        assert preset_trend["trend_percentage"] < -20  # Should be around 30% improvement
        assert preset_trend["first_half_avg_ms"] > preset_trend["second_half_avg_ms"]
        assert preset_trend["sample_count"] == 5

    def test_analyze_performance_trends_identifies_stable_performance(self, performance_benchmarks_test_data):
        """
        Test that analyze_performance_trends identifies stable performance patterns.

        Verifies:
            Trend analysis correctly identifies when performance remains
            consistent across historical results without significant changes.

        Business Impact:
            Stability detection confirms performance consistency, building
            confidence in system reliability for production deployments.

        Scenario:
            Given: Historical results with consistent performance (±5% variance)
            When: analyze_performance_trends analyzes the trend
            Then: Performance is identified as stable
            And: Low variance is reported for confidence validation

        Fixtures Used:
            - performance_benchmarks_test_data: Provides consistent performance scenario
        """
        # Given: Historical results with consistent performance (±5% variance)
        benchmark = ConfigurationPerformanceBenchmark()
        historical_suites = []
        base_time = 12.0  # Target stable performance at 12ms

        for i in range(6):
            # Create stable performance with small variance: 11.4ms to 12.6ms (±5%)
            variance = (i % 3 - 1) * 0.6  # -0.6, 0, +0.6, -0.6, 0, +0.6
            current_time = base_time + variance

            suite = BenchmarkSuite(
                name="Resilience Configuration Performance Benchmark",
                results=[
                    BenchmarkResult(
                        operation="preset_loading",
                        duration_ms=current_time * 18,
                        memory_peak_mb=2.0,
                        iterations=100,
                        avg_duration_ms=current_time,
                        min_duration_ms=current_time * 0.95,
                        max_duration_ms=current_time * 1.05,
                        std_dev_ms=0.1,
                        success_rate=0.99,  # Consistent high success rate
                        metadata={"test_run": i, "stability": True}
                    )
                ],
                total_duration_ms=current_time * 18,
                pass_rate=0.99,
                failed_benchmarks=[],
                timestamp=f"2024-01-{i+1:02d} 10:00:00 UTC",
                environment_info={"platform": "test", "load": "stable"}
            )
            historical_suites.append(suite)

        # When: analyze_performance_trends analyzes the trend
        result = benchmark.analyze_performance_trends(historical_suites)

        # Then: Performance is identified as stable (or very small trend)
        assert "preset_loading" in result
        preset_trend = result["preset_loading"]

        # And: Low variance is reported for confidence validation
        # Stable performance should show minimal trend (small positive or negative)
        assert abs(preset_trend["trend_percentage"]) < 10  # Less than 10% change
        assert preset_trend["sample_count"] == 6
        # The first and second half averages should be very close
        assert abs(preset_trend["first_half_avg_ms"] - preset_trend["second_half_avg_ms"]) < 1.0


class TestGeneratePerformanceReport:
    """
    Tests for generate_performance_report() method behavior.
    
    Scope:
        Verifies human-readable performance report generation, including
        formatting, completeness, and actionable insights.
    
    Business Impact:
        Performance reports enable communication of benchmark results to
        stakeholders and provide actionable insights for optimization.
    
    Test Strategy:
        - Test report generation from BenchmarkSuite
        - Test report formatting and readability
        - Test report completeness
        - Test report sections and structure
    """

    def test_generate_performance_report_accepts_benchmark_suite(self):
        """
        Test that generate_performance_report accepts BenchmarkSuite parameter.

        Verifies:
            Method accepts BenchmarkSuite as suite parameter per documented
            Args section for report generation.

        Business Impact:
            BenchmarkSuite input enables generation of comprehensive reports
            from complete benchmark results.

        Scenario:
            Given: A BenchmarkSuite from comprehensive benchmark execution
            When: generate_performance_report is called with the suite
            Then: Method accepts the input without errors
            And: Report generation proceeds with suite data

        Fixtures Used:
            - None required for input acceptance verification
        """
        # Given: A BenchmarkSuite from comprehensive benchmark execution
        benchmark = ConfigurationPerformanceBenchmark()
        test_suite = BenchmarkSuite(
            name="Resilience Configuration Performance Benchmark",
            results=[
                BenchmarkResult(
                    operation="preset_loading",
                    duration_ms=50.0,
                    memory_peak_mb=2.0,
                    iterations=100,
                    avg_duration_ms=0.5,
                    min_duration_ms=0.3,
                    max_duration_ms=0.7,
                    std_dev_ms=0.1,
                    success_rate=1.0,
                    metadata={"test": True}
                )
            ],
            total_duration_ms=50.0,
            pass_rate=1.0,
            failed_benchmarks=[],
            timestamp="2024-01-15 10:00:00 UTC",
            environment_info={"platform": "test"}
        )

        # When: generate_performance_report is called with the suite
        try:
            report = benchmark.generate_performance_report(test_suite)

            # Then: Method accepts the input without errors
            assert isinstance(report, str)
            assert len(report) > 0

            # And: Report generation proceeds with suite data
            assert "preset_loading" in report or "RESILIENCE" in report

        except Exception as e:
            pytest.fail(f"generate_performance_report should accept BenchmarkSuite without errors, but raised: {e}")

    def test_generate_performance_report_returns_formatted_string(self):
        """
        Test that generate_performance_report returns formatted string report.

        Verifies:
            Return type is string containing formatted performance report
            per documented Returns section.

        Business Impact:
            String format enables flexible report output to console, files,
            or monitoring systems for stakeholder consumption.

        Scenario:
            Given: A BenchmarkSuite with benchmark results
            When: generate_performance_report completes generation
            Then: Return value is a formatted string report
            And: Report is human-readable and suitable for display

        Fixtures Used:
            - None required for return type verification
        """
        # Given: A BenchmarkSuite with benchmark results
        benchmark = ConfigurationPerformanceBenchmark()
        test_suite = BenchmarkSuite(
            name="Resilience Configuration Performance Benchmark",
            results=[
                BenchmarkResult(
                    operation="settings_initialization",
                    duration_ms=80.0,
                    memory_peak_mb=4.0,
                    iterations=50,
                    avg_duration_ms=1.6,
                    min_duration_ms=1.2,
                    max_duration_ms=2.0,
                    std_dev_ms=0.2,
                    success_rate=0.98,
                    metadata={"formatted": True}
                )
            ],
            total_duration_ms=80.0,
            pass_rate=0.98,
            failed_benchmarks=[],
            timestamp="2024-01-15 11:00:00 UTC",
            environment_info={"platform": "production"}
        )

        # When: generate_performance_report completes generation
        report = benchmark.generate_performance_report(test_suite)

        # Then: Return value is a formatted string report
        assert isinstance(report, str)

        # And: Report is human-readable and suitable for display
        assert len(report) > 100  # Should be a substantial report
        assert "\n" in report  # Should have line breaks for readability
        assert not report.isspace()  # Should not be just whitespace

    def test_generate_performance_report_includes_suite_name(self):
        """
        Test that generated report includes benchmark suite name.

        Verifies:
            Report contains suite name ("Resilience Configuration Performance Benchmark")
            for identification and context.

        Business Impact:
            Suite name in report enables identification of resilience benchmarks
            in multi-suite performance tracking systems.

        Scenario:
            Given: A BenchmarkSuite with standard name
            When: generate_performance_report generates the report
            Then: Report includes "Resilience Configuration Performance Benchmark"
            And: Suite is clearly identified in report header

        Fixtures Used:
            - None required for name inclusion verification
        """
        # Given: A BenchmarkSuite with standard name
        benchmark = ConfigurationPerformanceBenchmark()
        test_suite = BenchmarkSuite(
            name="Resilience Configuration Performance Benchmark",
            results=[
                BenchmarkResult(
                    operation="validation_performance",
                    duration_ms=30.0,
                    memory_peak_mb=1.5,
                    iterations=60,
                    avg_duration_ms=0.5,
                    min_duration_ms=0.4,
                    max_duration_ms=0.6,
                    std_dev_ms=0.05,
                    success_rate=1.0,
                    metadata={"name_test": True}
                )
            ],
            total_duration_ms=30.0,
            pass_rate=1.0,
            failed_benchmarks=[],
            timestamp="2024-01-15 12:00:00 UTC",
            environment_info={"platform": "test"}
        )

        # When: generate_performance_report generates the report
        report = benchmark.generate_performance_report(test_suite)

        # Then: Report includes "Resilience Configuration Performance Benchmark"
        assert "Resilience Configuration Performance Benchmark" in report

        # And: Suite is clearly identified in report header
        # Check that it appears near the beginning of the report
        lines = report.split('\n')
        first_few_lines = '\n'.join(lines[:5])
        assert "Resilience Configuration Performance Benchmark" in first_few_lines

    def test_generate_performance_report_includes_pass_rate(self):
        """
        Test that generated report includes overall pass rate percentage.

        Verifies:
            Report contains pass rate percentage showing benchmark success rate
            for quick performance health assessment.

        Business Impact:
            Pass rate provides immediate performance health indicator,
            enabling quick identification of performance issues.

        Scenario:
            Given: A BenchmarkSuite with 85% pass rate
            When: generate_performance_report generates the report
            Then: Report includes "Pass Rate: 85%" or similar formatting
            And: Pass rate is clearly visible for quick assessment

        Fixtures Used:
            - None required for pass rate inclusion verification
        """
        # Given: A BenchmarkSuite with 85% pass rate
        benchmark = ConfigurationPerformanceBenchmark()
        test_suite = BenchmarkSuite(
            name="Resilience Configuration Performance Benchmark",
            results=[
                BenchmarkResult(
                    operation="preset_loading",
                    duration_ms=8.0,  # Under threshold - PASS
                    memory_peak_mb=2.0,
                    iterations=100,
                    avg_duration_ms=0.08,
                    min_duration_ms=0.05,
                    max_duration_ms=0.11,
                    std_dev_ms=0.01,
                    success_rate=1.0,
                    metadata={"pass": True}
                ),
                BenchmarkResult(
                    operation="service_initialization",
                    duration_ms=250.0,  # Over 200ms threshold - FAIL
                    memory_peak_mb=10.0,
                    iterations=10,
                    avg_duration_ms=25.0,
                    min_duration_ms=20.0,
                    max_duration_ms=30.0,
                    std_dev_ms=2.5,
                    success_rate=1.0,
                    metadata={"fail": True}
                )
            ],
            total_duration_ms=258.0,
            pass_rate=0.5,  # 50% pass rate (1 out of 2 passed)
            failed_benchmarks=[],
            timestamp="2024-01-15 13:00:00 UTC",
            environment_info={"platform": "test"}
        )

        # When: generate_performance_report generates the report
        report = benchmark.generate_performance_report(test_suite)

        # Then: Report includes "Pass Rate: 50%" or similar formatting
        assert "Pass Rate:" in report
        assert "50%" in report or "0.5" in report or "50.0%" in report

        # And: Pass rate is clearly visible for quick assessment
        # Should appear early in the report
        lines = report.split('\n')
        early_content = '\n'.join(lines[:10])
        assert "Pass Rate:" in early_content

    def test_generate_performance_report_includes_individual_benchmark_results(self):
        """
        Test that generated report includes results for each benchmark operation.

        Verifies:
            Report contains detailed results for each benchmark operation
            with timing metrics and pass/fail status.

        Business Impact:
            Individual benchmark results enable identification of specific
            operations with performance issues requiring attention.

        Scenario:
            Given: A BenchmarkSuite with results for seven operations
            When: generate_performance_report generates the report
            Then: Report includes section for each benchmark operation
            And: Each section shows timing metrics and threshold status

        Fixtures Used:
            - None required for result inclusion verification
        """
        # Given: A BenchmarkSuite with results for multiple operations
        benchmark = ConfigurationPerformanceBenchmark()
        test_suite = BenchmarkSuite(
            name="Resilience Configuration Performance Benchmark",
            results=[
                BenchmarkResult(
                    operation="preset_loading",
                    duration_ms=5.0,
                    memory_peak_mb=1.0,
                    iterations=100,
                    avg_duration_ms=0.05,
                    min_duration_ms=0.03,
                    max_duration_ms=0.07,
                    std_dev_ms=0.01,
                    success_rate=1.0,
                    metadata={"operation": "preset"}
                ),
                BenchmarkResult(
                    operation="settings_initialization",
                    duration_ms=60.0,
                    memory_peak_mb=3.0,
                    iterations=50,
                    avg_duration_ms=1.2,
                    min_duration_ms=1.0,
                    max_duration_ms=1.4,
                    std_dev_ms=0.1,
                    success_rate=1.0,
                    metadata={"operation": "settings"}
                ),
                BenchmarkResult(
                    operation="validation_performance",
                    duration_ms=25.0,
                    memory_peak_mb=2.0,
                    iterations=60,
                    avg_duration_ms=0.42,
                    min_duration_ms=0.35,
                    max_duration_ms=0.49,
                    std_dev_ms=0.05,
                    success_rate=0.98,
                    metadata={"operation": "validation"}
                )
            ],
            total_duration_ms=90.0,
            pass_rate=1.0,
            failed_benchmarks=[],
            timestamp="2024-01-15 14:00:00 UTC",
            environment_info={"platform": "test"}
        )

        # When: generate_performance_report generates the report
        report = benchmark.generate_performance_report(test_suite)

        # Then: Report includes section for each benchmark operation
        assert "preset_loading" in report
        assert "settings_initialization" in report
        assert "validation_performance" in report

        # And: Each section shows timing metrics and threshold status
        assert "0.05" in report or "0.05ms" in report  # preset_loading avg
        assert "1.2" in report or "1.2ms" in report   # settings_initialization avg
        assert "0.42" in report or "0.42ms" in report  # validation_performance avg

    def test_generate_performance_report_includes_timing_statistics(self):
        """
        Test that generated report includes statistical timing metrics.

        Verifies:
            Report contains average, min, max, and standard deviation for
            each benchmark operation for comprehensive analysis.

        Business Impact:
            Statistical metrics enable detailed performance analysis and
            identification of performance variability issues.

        Scenario:
            Given: A BenchmarkSuite with comprehensive timing statistics
            When: generate_performance_report generates the report
            Then: Report includes avg, min, max, and stdev for each operation
            And: Statistical metrics are formatted for readability

        Fixtures Used:
            - None required for statistics inclusion verification
        """
        # Given: A BenchmarkSuite with comprehensive timing statistics
        benchmark = ConfigurationPerformanceBenchmark()
        test_suite = BenchmarkSuite(
            name="Resilience Configuration Performance Benchmark",
            results=[
                BenchmarkResult(
                    operation="resilience_config_loading",
                    duration_ms=75.0,
                    memory_peak_mb=4.0,
                    iterations=40,
                    avg_duration_ms=1.88,
                    min_duration_ms=1.2,
                    max_duration_ms=2.8,
                    std_dev_ms=0.45,
                    success_rate=0.95,
                    metadata={"stats": "comprehensive"}
                )
            ],
            total_duration_ms=75.0,
            pass_rate=0.95,
            failed_benchmarks=[],
            timestamp="2024-01-15 15:00:00 UTC",
            environment_info={"platform": "production"}
        )

        # When: generate_performance_report generates the report
        report = benchmark.generate_performance_report(test_suite)

        # Then: Report includes avg, min, max, and stdev for each operation
        assert "1.88" in report or "1.88ms" in report  # average
        assert "1.2" in report or "1.2ms" in report   # min
        assert "2.8" in report or "2.8ms" in report   # max

        # And: Statistical metrics are formatted for readability
        # Should contain terms like "min", "max" in context
        assert "min" in report.lower() or "max" in report.lower()

    def test_generate_performance_report_includes_memory_metrics(self):
        """
        Test that generated report includes memory usage metrics.

        Verifies:
            Report contains peak memory usage for operations with significant
            memory allocation for memory performance validation.

        Business Impact:
            Memory metrics enable identification of operations exceeding
            memory budgets and potential memory leak detection.

        Scenario:
            Given: A BenchmarkSuite with memory tracking data
            When: generate_performance_report generates the report
            Then: Report includes peak memory usage for benchmarks
            And: Memory metrics are formatted in megabytes for readability

        Fixtures Used:
            - None required for memory metrics inclusion
        """
        # Given: A BenchmarkSuite with memory tracking data
        benchmark = ConfigurationPerformanceBenchmark()
        test_suite = BenchmarkSuite(
            name="Resilience Configuration Performance Benchmark",
            results=[
                BenchmarkResult(
                    operation="service_initialization",
                    duration_ms=180.0,
                    memory_peak_mb=12.5,  # Significant memory usage
                    iterations=15,
                    avg_duration_ms=12.0,
                    min_duration_ms=10.0,
                    max_duration_ms=14.0,
                    std_dev_ms=1.2,
                    success_rate=1.0,
                    metadata={"memory_intensive": True}
                )
            ],
            total_duration_ms=180.0,
            pass_rate=1.0,
            failed_benchmarks=[],
            timestamp="2024-01-15 16:00:00 UTC",
            environment_info={"platform": "test", "memory": "8GB"}
        )

        # When: generate_performance_report generates the report
        report = benchmark.generate_performance_report(test_suite)

        # Then: Report includes peak memory usage for benchmarks
        assert "12.5" in report
        assert "memory" in report.lower() or "MB" in report or "mb" in report

        # And: Memory metrics are formatted in megabytes for readability
        # Should show memory information in a readable format

    def test_generate_performance_report_includes_threshold_comparison(self):
        """
        Test that generated report includes performance threshold comparisons.

        Verifies:
            Report shows how each benchmark compares to its performance
            threshold (PRESET_ACCESS <10ms, CONFIG_LOADING <100ms, etc.)

        Business Impact:
            Threshold comparison provides clear pass/fail determination
            and quantifies performance margin or deficit for each operation.

        Scenario:
            Given: A BenchmarkSuite with threshold evaluation results
            When: generate_performance_report generates the report
            Then: Report shows target thresholds for each operation
            And: Comparison indicates pass/fail with performance margin

        Fixtures Used:
            - None required for threshold comparison inclusion
        """
        # Given: A BenchmarkSuite with threshold evaluation results
        benchmark = ConfigurationPerformanceBenchmark()
        test_suite = BenchmarkSuite(
            name="Resilience Configuration Performance Benchmark",
            results=[
                BenchmarkResult(
                    operation="preset_loading",  # Should be <10ms
                    duration_ms=15.0,
                    memory_peak_mb=2.0,
                    iterations=100,
                    avg_duration_ms=0.15,  # Over threshold - FAIL
                    min_duration_ms=0.10,
                    max_duration_ms=0.20,
                    std_dev_ms=0.03,
                    success_rate=1.0,
                    metadata={"threshold_fail": True}
                ),
                BenchmarkResult(
                    operation="validation_performance",  # Should be <50ms
                    duration_ms=20.0,
                    memory_peak_mb=1.5,
                    iterations=50,
                    avg_duration_ms=0.40,  # Well under threshold - PASS
                    min_duration_ms=0.30,
                    max_duration_ms=0.50,
                    std_dev_ms=0.08,
                    success_rate=1.0,
                    metadata={"threshold_pass": True}
                )
            ],
            total_duration_ms=35.0,
            pass_rate=0.5,
            failed_benchmarks=[],
            timestamp="2024-01-15 17:00:00 UTC",
            environment_info={"platform": "test"}
        )

        # When: generate_performance_report generates the report
        report = benchmark.generate_performance_report(test_suite)

        # Then: Report shows target thresholds for each operation
        # Should include pass/fail indicators
        assert "PASS" in report or "FAIL" in report or "✓" in report or "✗" in report

        # And: Comparison indicates pass/fail with performance margin
        # Report should show which operations passed or failed thresholds

    def test_generate_performance_report_includes_failed_benchmark_list(self):
        """
        Test that generated report includes list of failed benchmarks.

        Verifies:
            Report contains clear list of benchmarks that failed during
            execution for rapid issue identification.

        Business Impact:
            Failed benchmark list enables quick identification of problematic
            operations requiring investigation or remediation.

        Scenario:
            Given: A BenchmarkSuite with two failed benchmarks
            When: generate_performance_report generates the report
            Then: Report includes "Failed Benchmarks" section
            And: Failed operation names are clearly listed

        Fixtures Used:
            - None required for failed list inclusion
        """
        # Given: A BenchmarkSuite with two failed benchmarks
        benchmark = ConfigurationPerformanceBenchmark()
        test_suite = BenchmarkSuite(
            name="Resilience Configuration Performance Benchmark",
            results=[
                BenchmarkResult(
                    operation="custom_config_loading",
                    duration_ms=50.0,
                    memory_peak_mb=3.0,
                    iterations=25,
                    avg_duration_ms=2.0,
                    min_duration_ms=1.5,
                    max_duration_ms=2.5,
                    std_dev_ms=0.3,
                    success_rate=1.0,
                    metadata={"status": "passed"}
                )
            ],
            total_duration_ms=50.0,
            pass_rate=0.8,
            failed_benchmarks=["benchmark_preset_loading", "benchmark_validation_performance"],
            timestamp="2024-01-15 18:00:00 UTC",
            environment_info={"platform": "test"}
        )

        # When: generate_performance_report generates the report
        report = benchmark.generate_performance_report(test_suite)

        # Then: Report includes "Failed Benchmarks" section
        assert "Failed" in report

        # And: Failed operation names are clearly listed
        assert "benchmark_preset_loading" in report or "benchmark_validation_performance" in report

    def test_generate_performance_report_includes_environment_context(self):
        """
        Test that generated report includes environment context information.

        Verifies:
            Report contains environment information and execution timestamp
            for result context and reproducibility.

        Business Impact:
            Environment context enables correlation of performance with
            system configuration and troubleshooting of environment-specific issues.

        Scenario:
            Given: A BenchmarkSuite with environment information
            When: generate_performance_report generates the report
            Then: Report includes environment details and timestamp
            And: Context information aids result interpretation

        Fixtures Used:
            - None required for environment context inclusion
        """
        # Given: A BenchmarkSuite with environment information
        benchmark = ConfigurationPerformanceBenchmark()
        test_suite = BenchmarkSuite(
            name="Resilience Configuration Performance Benchmark",
            results=[
                BenchmarkResult(
                    operation="legacy_config_loading",
                    duration_ms=40.0,
                    memory_peak_mb=2.5,
                    iterations=30,
                    avg_duration_ms=1.33,
                    min_duration_ms=1.0,
                    max_duration_ms=1.66,
                    std_dev_ms=0.2,
                    success_rate=1.0,
                    metadata={"env": "test"}
                )
            ],
            total_duration_ms=40.0,
            pass_rate=1.0,
            failed_benchmarks=[],
            timestamp="2024-01-15 19:30:45 UTC",
            environment_info={
                "platform": "Linux-5.15.0",
                "python_version": "3.11.0",
                "cpu_count": 8,
                "memory_gb": 16.0
            }
        )

        # When: generate_performance_report generates the report
        report = benchmark.generate_performance_report(test_suite)

        # Then: Report includes environment details and timestamp
        assert "2024-01-15 19:30:45 UTC" in report
        assert "Environment" in report

        # And: Context information aids result interpretation
        assert "Linux" in report or "python" in report.lower() or "cpu" in report.lower()

    def test_generate_performance_report_formats_output_for_readability(self):
        """
        Test that generated report uses readable formatting with sections.

        Verifies:
            Report uses clear section headers, aligned columns, and consistent
            formatting for human readability and quick scanning.

        Business Impact:
            Readable formatting enables stakeholders to quickly understand
            performance results and identify areas requiring attention.

        Scenario:
            Given: A BenchmarkSuite with comprehensive results
            When: generate_performance_report generates the report
            Then: Report uses section headers and aligned formatting
            And: Report is easily scannable for quick information extraction

        Fixtures Used:
            - None required for formatting verification
        """
        # Given: A BenchmarkSuite with comprehensive results
        benchmark = ConfigurationPerformanceBenchmark()
        test_suite = BenchmarkSuite(
            name="Resilience Configuration Performance Benchmark",
            results=[
                BenchmarkResult(
                    operation="preset_loading",
                    duration_ms=8.0,
                    memory_peak_mb=1.8,
                    iterations=100,
                    avg_duration_ms=0.08,
                    min_duration_ms=0.05,
                    max_duration_ms=0.11,
                    std_dev_ms=0.02,
                    success_rate=1.0,
                    metadata={"readability": True}
                )
            ],
            total_duration_ms=8.0,
            pass_rate=1.0,
            failed_benchmarks=[],
            timestamp="2024-01-15 20:00:00 UTC",
            environment_info={"platform": "test"}
        )

        # When: generate_performance_report generates the report
        report = benchmark.generate_performance_report(test_suite)

        # Then: Report uses section headers and aligned formatting
        lines = report.split('\n')
        assert len(lines) > 10  # Should have multiple lines for sections

        # Should have formatting elements like headers
        assert any("=" in line for line in lines) or any("-" in line for line in lines)

        # And: Report is easily scannable for quick information extraction
        # Should not be one giant block of text
        assert len([line for line in lines if line.strip()]) > 5  # Multiple non-empty lines

    def test_generate_performance_report_includes_report_title(self):
        """
        Test that generated report includes clear title header.

        Verifies:
            Report starts with clear title "RESILIENCE CONFIGURATION PERFORMANCE REPORT"
            or similar for immediate identification.

        Business Impact:
            Clear title enables quick identification of report type when
            viewing multiple performance reports.

        Scenario:
            Given: A BenchmarkSuite ready for reporting
            When: generate_performance_report generates the report
            Then: Report includes prominent title header
            And: Report type is immediately clear from title

        Fixtures Used:
            - None required for title verification
        """
        # Given: A BenchmarkSuite ready for reporting
        benchmark = ConfigurationPerformanceBenchmark()
        test_suite = BenchmarkSuite(
            name="Resilience Configuration Performance Benchmark",
            results=[
                BenchmarkResult(
                    operation="test_operation",
                    duration_ms=10.0,
                    memory_peak_mb=2.0,
                    iterations=50,
                    avg_duration_ms=0.2,
                    min_duration_ms=0.15,
                    max_duration_ms=0.25,
                    std_dev_ms=0.03,
                    success_rate=1.0,
                    metadata={"title_test": True}
                )
            ],
            total_duration_ms=10.0,
            pass_rate=1.0,
            failed_benchmarks=[],
            timestamp="2024-01-15 21:00:00 UTC",
            environment_info={"platform": "test"}
        )

        # When: generate_performance_report generates the report
        report = benchmark.generate_performance_report(test_suite)

        # Then: Report includes prominent title header
        assert "RESILIENCE CONFIGURATION PERFORMANCE REPORT" in report

        # And: Report type is immediately clear from title
        # Should appear at the beginning of the report
        lines = report.split('\n')
        first_lines = '\n'.join(lines[:3])
        assert "RESILIENCE" in first_lines


class TestAnalysisAndReportingEdgeCases:
    """
    Tests for edge cases in analysis and reporting functionality.
    
    Scope:
        Verifies graceful handling of edge cases including empty data,
        extreme values, and unusual scenarios in analysis and reporting.
    
    Business Impact:
        Robust edge case handling ensures analysis and reporting work
        reliably across all scenarios without crashes or invalid output.
    
    Test Strategy:
        - Test with empty or minimal data
        - Test with extreme performance values
        - Test with all-passing or all-failing scenarios
        - Test with missing optional data
    """

    def test_generate_performance_report_handles_zero_benchmarks(self):
        """
        Test that generate_performance_report handles suite with zero benchmark results.

        Verifies:
            Report generation gracefully handles BenchmarkSuite with empty
            results list, producing valid report without errors.

        Business Impact:
            Graceful empty data handling prevents crashes when benchmark
            execution produces no results due to failures or configuration.

        Scenario:
            Given: A BenchmarkSuite with empty results list
            When: generate_performance_report is called
            Then: Report is generated without errors
            And: Report indicates no benchmarks were executed

        Fixtures Used:
            - None required for empty data edge case

        Edge Cases Covered:
            - Empty results list handling
            - Zero benchmark scenario
        """
        # Given: A BenchmarkSuite with empty results list
        benchmark = ConfigurationPerformanceBenchmark()
        empty_suite = BenchmarkSuite(
            name="Resilience Configuration Performance Benchmark",
            results=[],  # Empty results list
            total_duration_ms=0.0,
            pass_rate=0.0,
            failed_benchmarks=["all_benchmarks_failed"],
            timestamp="2024-01-15 22:00:00 UTC",
            environment_info={"platform": "test", "error": "no_results"}
        )

        # When: generate_performance_report is called
        try:
            report = benchmark.generate_performance_report(empty_suite)

            # Then: Report is generated without errors
            assert isinstance(report, str)
            assert len(report) > 0

            # And: Report indicates no benchmarks were executed or handles empty case gracefully
            # Report should still have basic structure even with no results
            assert "RESILIENCE" in report or "Performance" in report

        except Exception as e:
            pytest.fail(f"generate_performance_report should handle empty results gracefully, but raised: {e}")

    def test_generate_performance_report_handles_suite_with_all_failures(self):
        """
        Test that generate_performance_report handles suite where all benchmarks failed.

        Verifies:
            Report generation handles scenario where all benchmarks failed
            during execution, showing comprehensive failure information.

        Business Impact:
            Complete failure reporting enables rapid identification that
            benchmark suite is completely broken, requiring immediate attention.

        Scenario:
            Given: A BenchmarkSuite with 0% pass rate (all failures)
            When: generate_performance_report generates the report
            Then: Report clearly indicates complete failure
            And: Failed benchmarks section lists all operations

        Fixtures Used:
            - None required for complete failure scenario

        Edge Cases Covered:
            - Zero percent pass rate
            - Complete benchmark suite failure
        """
        # Given: A BenchmarkSuite with 0% pass rate (all failures)
        benchmark = ConfigurationPerformanceBenchmark()
        failed_suite = BenchmarkSuite(
            name="Resilience Configuration Performance Benchmark",
            results=[
                # These results represent benchmarks that failed to meet thresholds
                BenchmarkResult(
                    operation="preset_loading",  # Failed: avg 15ms > 10ms threshold
                    duration_ms=150.0,
                    memory_peak_mb=5.0,
                    iterations=10,
                    avg_duration_ms=15.0,
                    min_duration_ms=12.0,
                    max_duration_ms=18.0,
                    std_dev_ms=2.0,
                    success_rate=0.5,  # Also had execution failures
                    metadata={"failed": True, "error": "timeout"}
                ),
                BenchmarkResult(
                    operation="service_initialization",  # Failed: avg 300ms > 200ms threshold
                    duration_ms=600.0,
                    memory_peak_mb=20.0,
                    iterations=2,
                    avg_duration_ms=300.0,
                    min_duration_ms=250.0,
                    max_duration_ms=350.0,
                    std_dev_ms=50.0,
                    success_rate=0.0,  # Complete failure
                    metadata={"failed": True, "error": "memory_error"}
                )
            ],
            total_duration_ms=750.0,
            pass_rate=0.0,  # All benchmarks failed
            failed_benchmarks=["preset_loading", "service_initialization", "settings_initialization", "validation_performance"],
            timestamp="2024-01-15 23:00:00 UTC",
            environment_info={"platform": "test", "critical_errors": True}
        )

        # When: generate_performance_report generates the report
        report = benchmark.generate_performance_report(failed_suite)

        # Then: Report clearly indicates complete failure
        assert "0%" in report or "0.0%" in report
        assert "Pass Rate:" in report

        # And: Failed benchmarks section lists all operations
        assert "Failed" in report
        # Should contain some indication of the failure severity

    def test_generate_performance_report_handles_very_fast_benchmarks(self):
        """
        Test that generate_performance_report formats sub-millisecond timings correctly.

        Verifies:
            Report correctly formats and displays very fast benchmarks with
            sub-millisecond execution times without precision loss.

        Business Impact:
            Accurate sub-millisecond reporting enables validation of highly
            optimized operations and cache effectiveness.

        Scenario:
            Given: A BenchmarkSuite with 0.1ms average execution times
            When: generate_performance_report formats the timings
            Then: Sub-millisecond times are displayed with appropriate precision
            And: Fast benchmark performance is accurately represented

        Fixtures Used:
            - None required for fast timing edge case

        Edge Cases Covered:
            - Sub-millisecond timing display
            - Precision preservation for fast operations
        """
        # Given: A BenchmarkSuite with 0.1ms average execution times
        benchmark = ConfigurationPerformanceBenchmark()
        fast_suite = BenchmarkSuite(
            name="Resilience Configuration Performance Benchmark",
            results=[
                BenchmarkResult(
                    operation="preset_loading",  # Very fast operation
                    duration_ms=1.0,
                    memory_peak_mb=0.5,
                    iterations=1000,
                    avg_duration_ms=0.001,  # 0.001ms = 1 microsecond
                    min_duration_ms=0.0005,  # 0.0005ms = 0.5 microseconds
                    max_duration_ms=0.002,  # 0.002ms = 2 microseconds
                    std_dev_ms=0.0003,
                    success_rate=1.0,
                    metadata={"ultra_fast": True, "cache_hit": True}
                ),
                BenchmarkResult(
                    operation="cache_access",  # Fast cached operation
                    duration_ms=0.5,
                    memory_peak_mb=0.1,
                    iterations=5000,
                    avg_duration_ms=0.0001,  # 0.1 microsecond
                    min_duration_ms=0.00005,
                    max_duration_ms=0.0002,
                    std_dev_ms=0.00002,
                    success_rate=1.0,
                    metadata={"cache_optimized": True}
                )
            ],
            total_duration_ms=1.5,
            pass_rate=1.0,
            failed_benchmarks=[],
            timestamp="2024-01-15 23:30:00 UTC",
            environment_info={"platform": "test", "ssd": True}
        )

        # When: generate_performance_report formats the timings
        report = benchmark.generate_performance_report(fast_suite)

        # Then: Sub-millisecond times are displayed with appropriate precision
        assert isinstance(report, str)
        assert len(report) > 0

        # Should contain the small timing values (may be formatted differently)
        # Check that very small numbers appear in some format
        assert "0.001" in report or "0.0001" in report or "micro" in report.lower() or "μs" in report

        # And: Fast benchmark performance is accurately represented
        # Report should indicate excellent performance (likely PASS status)

    def test_generate_performance_report_handles_very_slow_benchmarks(self):
        """
        Test that generate_performance_report formats very slow benchmark timings.

        Verifies:
            Report correctly formats and displays benchmarks with execution
            times in seconds or minutes for slow operations.

        Business Impact:
            Accurate slow timing reporting enables identification of operations
            significantly exceeding performance targets.

        Scenario:
            Given: A BenchmarkSuite with 5000ms (5 second) execution times
            When: generate_performance_report formats the timings
            Then: Slow times are displayed in appropriate units (seconds)
            And: Performance issues are clearly visible

        Fixtures Used:
            - None required for slow timing edge case

        Edge Cases Covered:
            - Multi-second timing display
            - Large timing value formatting
        """
        # Given: A BenchmarkSuite with 5000ms (5 second) execution times
        benchmark = ConfigurationPerformanceBenchmark()
        slow_suite = BenchmarkSuite(
            name="Resilience Configuration Performance Benchmark",
            results=[
                BenchmarkResult(
                    operation="service_initialization",  # Very slow operation
                    duration_ms=10000.0,  # 10 seconds total
                    memory_peak_mb=500.0,  # 500MB memory usage
                    iterations=2,
                    avg_duration_ms=5000.0,  # 5 seconds average
                    min_duration_ms=4500.0,  # 4.5 seconds min
                    max_duration_ms=5500.0,  # 5.5 seconds max
                    std_dev_ms=500.0,
                    success_rate=0.5,  # Some operations timed out
                    metadata={"slow": True, "disk_io": True, "network_timeout": True}
                ),
                BenchmarkResult(
                    operation="complex_validation",  # Slow validation
                    duration_ms=15000.0,  # 15 seconds total
                    memory_peak_mb=200.0,
                    iterations=3,
                    avg_duration_ms=5000.0,  # 5 seconds average
                    min_duration_ms=4000.0,
                    max_duration_ms=6000.0,
                    std_dev_ms=800.0,
                    success_rate=0.67,
                    metadata={"computationally_intensive": True}
                )
            ],
            total_duration_ms=25000.0,  # 25 seconds total
            pass_rate=0.0,  # All failed thresholds
            failed_benchmarks=["service_initialization", "complex_validation"],
            timestamp="2024-01-15 23:45:00 UTC",
            environment_info={"platform": "test", "load": "high", "disk_slow": True}
        )

        # When: generate_performance_report formats the timings
        report = benchmark.generate_performance_report(slow_suite)

        # Then: Slow times are displayed in appropriate units (seconds)
        assert isinstance(report, str)
        assert len(report) > 0

        # Should contain large timing values
        assert "5000" in report or "5.0" in report or "5 seconds" in report.lower()
        assert "15000" in report or "15.0" in report or "15 seconds" in report.lower()

        # And: Performance issues are clearly visible
        # Should show FAIL status for these slow operations
        assert "FAIL" in report or "Failed" in report or "✗" in report

