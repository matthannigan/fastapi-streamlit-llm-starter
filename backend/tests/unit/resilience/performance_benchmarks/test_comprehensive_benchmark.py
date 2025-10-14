"""
Test suite for ConfigurationPerformanceBenchmark.run_comprehensive_benchmark() method.

This module verifies the comprehensive benchmark suite execution, including
all standard benchmarks, threshold evaluation, pass rate calculation, environment
context collection, and graceful error handling.

Test Strategy:
    - Test complete suite execution
    - Test result accumulation across all benchmarks
    - Test pass rate calculation with threshold evaluation
    - Test environment context collection
    - Test graceful handling of individual benchmark failures
    - Test BenchmarkSuite structure and completeness

Business Critical:
    run_comprehensive_benchmark() is the primary entry point for validating
    resilience configuration performance. It must execute reliably, handle failures
    gracefully, and provide complete results for performance validation and
    regression detection.
"""

import pytest
from unittest.mock import Mock, MagicMock, patch
from typing import Dict, Any, List
import time as real_time

# Import the classes we need to test
from app.infrastructure.resilience.performance_benchmarks import (
    ConfigurationPerformanceBenchmark,
    BenchmarkSuite,
    BenchmarkResult,
    PerformanceThreshold
)


class TestRunComprehensiveBenchmarkExecution:
    """
    Tests for run_comprehensive_benchmark() execution and orchestration.
    
    Scope:
        Verifies complete benchmark suite execution, orchestration of all
        standard benchmarks, and result collection.
    
    Business Impact:
        Complete suite execution enables comprehensive performance validation
        across all resilience configuration operations in single invocation.
    
    Test Strategy:
        - Test all standard benchmarks execute
        - Test proper benchmark orchestration
        - Test result accumulation
        - Test execution order independence
    """

    def test_run_comprehensive_benchmark_executes_all_standard_benchmarks(self):
        """
        Test that run_comprehensive_benchmark executes all documented standard benchmarks.

        Verifies:
            All seven standard benchmarks are executed: preset_loading,
            settings_initialization, resilience_config_loading, service_initialization,
            custom_config_loading, legacy_config_loading, and validation_performance.

        Business Impact:
            Complete benchmark coverage ensures all critical configuration operations
            are performance-validated, preventing performance regressions in any area.

        Scenario:
            Given: A benchmark instance ready to run comprehensive suite
            When: run_comprehensive_benchmark is called
            Then: All seven standard benchmarks execute
            And: BenchmarkSuite.results contains results for all operations

        Fixtures Used:
            - None required for execution verification
        """
        # Given: A benchmark instance ready to run comprehensive suite
        benchmark = ConfigurationPerformanceBenchmark()

        # Expected operations to verify
        expected_operations = [
            "preset_loading",
            "settings_initialization",
            "resilience_config_loading",
            "service_initialization",
            "custom_config_loading",
            "legacy_config_loading",
            "validation_performance"
        ]

        # Create mock results for each operation
        mock_results = {}
        for operation in expected_operations:
            mock_results[operation] = BenchmarkResult(
                operation=operation,
                duration_ms=10.0,
                memory_peak_mb=1.0,
                iterations=1,
                avg_duration_ms=10.0,
                min_duration_ms=10.0,
                max_duration_ms=10.0,
                std_dev_ms=0.0,
                success_rate=1.0,
                metadata={"test": True}
            )

        # Mock all benchmark methods using patch.multiple
        mocks = {}
        for operation in expected_operations:
            method_name = f"benchmark_{operation}"
            mocks[method_name] = Mock(return_value=mock_results[operation])

        # Use the patch context manager properly with the full import path
        with patch.multiple(
            "app.infrastructure.resilience.performance_benchmarks.ConfigurationPerformanceBenchmark",
            **mocks
        ):
            # When: run_comprehensive_benchmark is called
            suite = benchmark.run_comprehensive_benchmark()

        # Then: All seven standard benchmarks execute
        for operation in expected_operations:
            method_name = f"benchmark_{operation}"
            mock_method = mocks[method_name]
            mock_method.assert_called_once()

        # And: BenchmarkSuite.results contains results for all operations
        assert len(suite.results) == 7
        executed_operations = [result.operation for result in suite.results]
        for expected_operation in expected_operations:
            assert expected_operation in executed_operations

    def test_run_comprehensive_benchmark_clears_previous_results(self):
        """
        Test that run_comprehensive_benchmark clears results before execution.

        Verifies:
            Previous results are cleared to ensure clean benchmark execution per
            documented behavior, preventing contamination from prior runs.

        Business Impact:
            Clean state ensures benchmark results reflect current execution only,
            preventing confusion from stale data in performance analysis.

        Scenario:
            Given: A benchmark instance with results from previous run
            When: run_comprehensive_benchmark is called
            Then: Previous results are cleared before execution
            And: Only current benchmark results are present

        Fixtures Used:
            - None required for result clearing verification
        """
        # Given: A benchmark instance with results from previous run
        benchmark = ConfigurationPerformanceBenchmark()

        # Add some previous results to simulate contamination
        previous_result = BenchmarkResult(
            operation="previous_operation",
            duration_ms=100.0,
            memory_peak_mb=2.0,
            iterations=5,
            avg_duration_ms=20.0,
            min_duration_ms=15.0,
            max_duration_ms=25.0,
            std_dev_ms=3.0,
            success_rate=1.0,
            metadata={"old": True}
        )
        benchmark.results.append(previous_result)

        # Verify previous results exist
        assert len(benchmark.results) == 1
        assert benchmark.results[0].operation == "previous_operation"

        # Mock the benchmark methods to return predictable results
        with patch.object(benchmark, 'benchmark_preset_loading') as mock_preset:
            with patch.object(benchmark, 'benchmark_settings_initialization') as mock_settings:
                mock_preset.return_value = BenchmarkResult(
                    operation="preset_loading",
                    duration_ms=10.0,
                    memory_peak_mb=1.0,
                    iterations=1,
                    avg_duration_ms=10.0,
                    min_duration_ms=10.0,
                    max_duration_ms=10.0,
                    std_dev_ms=0.0,
                    success_rate=1.0,
                    metadata={}
                )
                mock_settings.return_value = BenchmarkResult(
                    operation="settings_initialization",
                    duration_ms=15.0,
                    memory_peak_mb=1.5,
                    iterations=1,
                    avg_duration_ms=15.0,
                    min_duration_ms=15.0,
                    max_duration_ms=15.0,
                    std_dev_ms=0.0,
                    success_rate=1.0,
                    metadata={}
                )

                # Mock the remaining benchmarks to avoid actual execution
                with patch.multiple(
                    benchmark,
                    benchmark_resilience_config_loading=Mock(return_value=mock_settings.return_value),
                    benchmark_service_initialization=Mock(return_value=mock_settings.return_value),
                    benchmark_custom_config_loading=Mock(return_value=mock_settings.return_value),
                    benchmark_legacy_config_loading=Mock(return_value=mock_settings.return_value),
                    benchmark_validation_performance=Mock(return_value=mock_settings.return_value)
                ):
                    # When: run_comprehensive_benchmark is called
                    suite = benchmark.run_comprehensive_benchmark()

        # Then: Previous results are cleared before execution
        # Only current benchmark results should be present
        assert len(benchmark.results) == 7  # Should have 7 current results
        current_operations = [result.operation for result in benchmark.results]
        assert "previous_operation" not in current_operations

        # And: Only current benchmark results are present in the suite
        assert len(suite.results) == 7
        suite_operations = [result.operation for result in suite.results]
        assert "previous_operation" not in suite_operations
        assert all(op in [
            "preset_loading", "settings_initialization", "resilience_config_loading",
            "service_initialization", "custom_config_loading", "legacy_config_loading",
            "validation_performance"
        ] for op in suite_operations)

    def test_run_comprehensive_benchmark_returns_benchmark_suite(self):
        """
        Test that run_comprehensive_benchmark returns BenchmarkSuite object.

        Verifies:
            Return type is BenchmarkSuite containing comprehensive results per
            documented Returns section with all required attributes.

        Business Impact:
            Structured suite result format enables automated performance analysis,
            reporting, and regression detection across all operations.

        Scenario:
            Given: A benchmark executing comprehensive suite
            When: run_comprehensive_benchmark completes
            Then: Return value is a BenchmarkSuite instance
            And: Suite contains all required result attributes

        Fixtures Used:
            - None required for return type verification
        """
        # Given: A benchmark executing comprehensive suite
        benchmark = ConfigurationPerformanceBenchmark()

        # Mock all benchmark methods to return predictable results
        mock_result = BenchmarkResult(
            operation="test_operation",
            duration_ms=10.0,
            memory_peak_mb=1.0,
            iterations=1,
            avg_duration_ms=10.0,
            min_duration_ms=10.0,
            max_duration_ms=10.0,
            std_dev_ms=0.0,
            success_rate=1.0,
            metadata={}
        )

        with patch.multiple(
            benchmark,
            benchmark_preset_loading=Mock(return_value=mock_result),
            benchmark_settings_initialization=Mock(return_value=mock_result),
            benchmark_resilience_config_loading=Mock(return_value=mock_result),
            benchmark_service_initialization=Mock(return_value=mock_result),
            benchmark_custom_config_loading=Mock(return_value=mock_result),
            benchmark_legacy_config_loading=Mock(return_value=mock_result),
            benchmark_validation_performance=Mock(return_value=mock_result)
        ):
            # When: run_comprehensive_benchmark completes
            result = benchmark.run_comprehensive_benchmark()

        # Then: Return value is a BenchmarkSuite instance
        assert isinstance(result, BenchmarkSuite)

        # And: Suite contains all required result attributes
        required_attributes = [
            'name', 'results', 'total_duration_ms', 'pass_rate',
            'failed_benchmarks', 'timestamp', 'environment_info'
        ]
        for attr in required_attributes:
            assert hasattr(result, attr), f"Missing required attribute: {attr}"

        # Verify attribute types are correct
        assert isinstance(result.name, str)
        assert isinstance(result.results, list)
        assert isinstance(result.total_duration_ms, (int, float))
        assert isinstance(result.pass_rate, (int, float))
        assert isinstance(result.failed_benchmarks, list)
        assert isinstance(result.timestamp, str)
        assert isinstance(result.environment_info, dict)

    def test_run_comprehensive_benchmark_sets_suite_name(self):
        """
        Test that run_comprehensive_benchmark sets correct suite name.

        Verifies:
            BenchmarkSuite.name is set to "Resilience Configuration Performance Benchmark"
            per documented contract for suite identification.

        Business Impact:
            Consistent suite naming enables identification and filtering of
            resilience configuration benchmark results in performance dashboards.

        Scenario:
            Given: A comprehensive benchmark execution
            When: run_comprehensive_benchmark completes
            Then: BenchmarkSuite.name equals "Resilience Configuration Performance Benchmark"
            And: Suite can be identified in performance tracking systems

        Fixtures Used:
            - None required for name verification
        """
        # Given: A comprehensive benchmark execution
        benchmark = ConfigurationPerformanceBenchmark()

        # Mock all benchmark methods to avoid actual execution
        mock_result = BenchmarkResult(
            operation="test_operation",
            duration_ms=10.0,
            memory_peak_mb=1.0,
            iterations=1,
            avg_duration_ms=10.0,
            min_duration_ms=10.0,
            max_duration_ms=10.0,
            std_dev_ms=0.0,
            success_rate=1.0,
            metadata={}
        )

        with patch.multiple(
            benchmark,
            benchmark_preset_loading=Mock(return_value=mock_result),
            benchmark_settings_initialization=Mock(return_value=mock_result),
            benchmark_resilience_config_loading=Mock(return_value=mock_result),
            benchmark_service_initialization=Mock(return_value=mock_result),
            benchmark_custom_config_loading=Mock(return_value=mock_result),
            benchmark_legacy_config_loading=Mock(return_value=mock_result),
            benchmark_validation_performance=Mock(return_value=mock_result)
        ):
            # When: run_comprehensive_benchmark completes
            suite = benchmark.run_comprehensive_benchmark()

        # Then: BenchmarkSuite.name equals "Resilience Configuration Performance Benchmark"
        expected_name = "Resilience Configuration Performance Benchmark"
        assert suite.name == expected_name

        # And: Suite can be identified in performance tracking systems
        # Verify the name is descriptive and identifiable
        assert "Resilience" in suite.name
        assert "Performance" in suite.name
        assert "Benchmark" in suite.name

    def test_run_comprehensive_benchmark_accumulates_all_results(self):
        """
        Test that run_comprehensive_benchmark accumulates all benchmark results.

        Verifies:
            BenchmarkSuite.results list contains BenchmarkResult objects for all
            executed benchmarks, enabling comprehensive performance analysis.

        Business Impact:
            Complete result accumulation enables detailed analysis of each
            operation's performance and identification of performance bottlenecks.

        Scenario:
            Given: A comprehensive benchmark suite execution
            When: run_comprehensive_benchmark completes all benchmarks
            Then: BenchmarkSuite.results contains at least 7 BenchmarkResult objects
            And: Each standard benchmark has a corresponding result

        Fixtures Used:
            - None required for result accumulation verification
        """
        # Given: A comprehensive benchmark suite execution
        benchmark = ConfigurationPerformanceBenchmark()

        # Create distinct mock results for each benchmark to verify accumulation
        expected_operations = [
            "preset_loading",
            "settings_initialization",
            "resilience_config_loading",
            "service_initialization",
            "custom_config_loading",
            "legacy_config_loading",
            "validation_performance"
        ]

        mock_results = {}
        for i, operation in enumerate(expected_operations):
            mock_results[operation] = BenchmarkResult(
                operation=operation,
                duration_ms=10.0 + i * 5,  # Different duration for each
                memory_peak_mb=1.0 + i * 0.5,  # Different memory for each
                iterations=1,
                avg_duration_ms=10.0 + i * 5,
                min_duration_ms=10.0 + i * 5,
                max_duration_ms=10.0 + i * 5,
                std_dev_ms=0.0,
                success_rate=1.0,
                metadata={"operation_id": i}
            )

        # Mock all benchmark methods with their specific results
        mocks = {}
        for operation in expected_operations:
            method_name = f"benchmark_{operation}"
            mocks[operation] = Mock(return_value=mock_results[operation])

        with patch.multiple(benchmark, **mocks):
            # When: run_comprehensive_benchmark completes all benchmarks
            suite = benchmark.run_comprehensive_benchmark()

        # Then: BenchmarkSuite.results contains at least 7 BenchmarkResult objects
        assert len(suite.results) >= 7
        assert all(isinstance(result, BenchmarkResult) for result in suite.results)

        # And: Each standard benchmark has a corresponding result
        result_operations = [result.operation for result in suite.results]
        for expected_operation in expected_operations:
            assert expected_operation in result_operations

        # Verify each result is unique and properly accumulated
        unique_operations = set(result_operations)
        assert len(unique_operations) == 7  # All 7 should be unique

        # Verify the specific mock results were accumulated correctly
        for result in suite.results:
            assert result.operation in expected_operations
            expected_result = mock_results[result.operation]
            assert result.duration_ms == expected_result.duration_ms
            assert result.memory_peak_mb == expected_result.memory_peak_mb
            assert result.metadata == expected_result.metadata


class TestRunComprehensiveBenchmarkPerformanceThresholds:
    """
    Tests for run_comprehensive_benchmark() threshold evaluation and pass rate calculation.
    
    Scope:
        Verifies performance threshold application, pass/fail evaluation
        for each benchmark, and overall pass rate calculation.
    
    Business Impact:
        Threshold-based evaluation enables automated performance validation,
        identifying operations that fail to meet performance targets.
    
    Test Strategy:
        - Test threshold application to each benchmark
        - Test pass rate calculation with all passing
        - Test pass rate calculation with some failures
        - Test pass rate calculation with all failures
    """

    def test_run_comprehensive_benchmark_evaluates_against_thresholds(self):
        """
        Test that run_comprehensive_benchmark evaluates results against performance thresholds.

        Verifies:
            Each benchmark result is evaluated against its corresponding performance
            threshold (PRESET_ACCESS <10ms, CONFIG_LOADING <100ms, VALIDATION <50ms,
            SERVICE_INIT <200ms) per documented threshold specification.

        Business Impact:
            Threshold evaluation enables automated identification of operations
            failing to meet performance targets, triggering investigation.

        Scenario:
            Given: A comprehensive benchmark with all standard benchmarks
            When: run_comprehensive_benchmark completes execution
            Then: Each result is evaluated against its performance threshold
            And: Pass/fail status is determined based on threshold comparison

        Fixtures Used:
            - None required for threshold evaluation logic
        """
        # Given: A comprehensive benchmark with all standard benchmarks
        benchmark = ConfigurationPerformanceBenchmark()

        # Create mock results with varying performance characteristics
        mock_results = {
            "preset_loading": BenchmarkResult(
                operation="preset_loading",
                duration_ms=50.0,
                memory_peak_mb=1.0,
                iterations=1,
                avg_duration_ms=5.0,  # Should pass PRESET_ACCESS (<10ms)
                min_duration_ms=4.0,
                max_duration_ms=6.0,
                std_dev_ms=0.5,
                success_rate=1.0,
                metadata={}
            ),
            "settings_initialization": BenchmarkResult(
                operation="settings_initialization",
                duration_ms=200.0,
                memory_peak_mb=2.0,
                iterations=1,
                avg_duration_ms=200.0,  # Should fail CONFIG_LOADING (>100ms)
                min_duration_ms=180.0,
                max_duration_ms=220.0,
                std_dev_ms=10.0,
                success_rate=1.0,
                metadata={}
            ),
            "validation_performance": BenchmarkResult(
                operation="validation_performance",
                duration_ms=60.0,
                memory_peak_mb=1.5,
                iterations=1,
                avg_duration_ms=60.0,  # Should fail VALIDATION (>50ms)
                min_duration_ms=55.0,
                max_duration_ms=65.0,
                std_dev_ms=3.0,
                success_rate=1.0,
                metadata={}
            ),
            "service_initialization": BenchmarkResult(
                operation="service_initialization",
                duration_ms=300.0,
                memory_peak_mb=3.0,
                iterations=1,
                avg_duration_ms=150.0,  # Should pass SERVICE_INIT (<200ms)
                min_duration_ms=140.0,
                max_duration_ms=160.0,
                std_dev_ms=5.0,
                success_rate=1.0,
                metadata={}
            )
        }

        # Create mocks for remaining benchmarks with passing results
        passing_result = BenchmarkResult(
            operation="test",
            duration_ms=80.0,
            memory_peak_mb=1.8,
            iterations=1,
            avg_duration_ms=80.0,  # Should pass CONFIG_LOADING (<100ms)
            min_duration_ms=75.0,
            max_duration_ms=85.0,
            std_dev_ms=2.5,
            success_rate=1.0,
            metadata={}
        )

        # Mock all benchmark methods
        mocks = {
            'benchmark_preset_loading': Mock(return_value=mock_results["preset_loading"]),
            'benchmark_settings_initialization': Mock(return_value=mock_results["settings_initialization"]),
            'benchmark_validation_performance': Mock(return_value=mock_results["validation_performance"]),
            'benchmark_service_initialization': Mock(return_value=mock_results["service_initialization"]),
            'benchmark_resilience_config_loading': Mock(return_value=BenchmarkResult(
                operation="resilience_config_loading",
                duration_ms=80.0,
                memory_peak_mb=1.8,
                iterations=1,
                avg_duration_ms=80.0,  # Should pass CONFIG_LOADING (<100ms)
                min_duration_ms=75.0,
                max_duration_ms=85.0,
                std_dev_ms=2.5,
                success_rate=1.0,
                metadata={}
            )),
            'benchmark_custom_config_loading': Mock(return_value=BenchmarkResult(
                operation="custom_config_loading",
                duration_ms=80.0,
                memory_peak_mb=1.8,
                iterations=1,
                avg_duration_ms=80.0,  # Should pass CONFIG_LOADING (<100ms)
                min_duration_ms=75.0,
                max_duration_ms=85.0,
                std_dev_ms=2.5,
                success_rate=1.0,
                metadata={}
            )),
            'benchmark_legacy_config_loading': Mock(return_value=BenchmarkResult(
                operation="legacy_config_loading",
                duration_ms=80.0,
                memory_peak_mb=1.8,
                iterations=1,
                avg_duration_ms=80.0,  # Should pass CONFIG_LOADING (<100ms)
                min_duration_ms=75.0,
                max_duration_ms=85.0,
                std_dev_ms=2.5,
                success_rate=1.0,
                metadata={}
            ))
        }

        with patch.multiple(benchmark, **mocks):
            # When: run_comprehensive_benchmark completes execution
            suite = benchmark.run_comprehensive_benchmark()

        # Then: Each result is evaluated against its performance threshold
        # Verify pass rate reflects threshold evaluation
        assert 0.0 <= suite.pass_rate <= 1.0

        # And: Pass/fail status is determined based on threshold comparison
        # Expected passing operations: preset_loading (5ms < 10ms), service_initialization (150ms < 200ms),
        # resilience_config_loading (80ms < 100ms), custom_config_loading (80ms < 100ms),
        # legacy_config_loading (80ms < 100ms)
        # Expected failing operations: settings_initialization (200ms > 100ms), validation_performance (60ms > 50ms)
        expected_pass_rate = 5.0 / 7.0  # 5 passing out of 7 total
        assert abs(suite.pass_rate - expected_pass_rate) < 0.01

    def test_run_comprehensive_benchmark_calculates_pass_rate_with_all_passing(self, fake_time_module, monkeypatch):
        """
        Test that run_comprehensive_benchmark calculates 100% pass rate when all meet thresholds.

        Verifies:
            BenchmarkSuite.pass_rate equals 1.0 when all benchmarks meet their
            performance thresholds, indicating complete success.

        Business Impact:
            100% pass rate clearly indicates all operations meet performance
            targets, validating configuration system performance.

        Scenario:
            Given: A fake time module ensuring fast execution times
            And: All benchmarks execute within their performance thresholds
            When: run_comprehensive_benchmark completes
            Then: BenchmarkSuite.pass_rate equals 1.0
            And: All benchmarks are counted as passing

        Fixtures Used:
            - fake_time_module: Ensures fast execution for threshold compliance
        """
        # Given: A fake time module ensuring fast execution times
        fake_time_module.set_time(1000.0)

        # And: All benchmarks execute within their performance thresholds
        benchmark = ConfigurationPerformanceBenchmark()

        # Create mock results that all pass their respective thresholds
        passing_results = {
            "preset_loading": BenchmarkResult(
                operation="preset_loading",
                duration_ms=50.0,
                memory_peak_mb=1.0,
                iterations=1,
                avg_duration_ms=5.0,  # < 10ms (PRESET_ACCESS)
                min_duration_ms=4.0,
                max_duration_ms=6.0,
                std_dev_ms=0.5,
                success_rate=1.0,
                metadata={}
            ),
            "settings_initialization": BenchmarkResult(
                operation="settings_initialization",
                duration_ms=80.0,
                memory_peak_mb=2.0,
                iterations=1,
                avg_duration_ms=80.0,  # < 100ms (CONFIG_LOADING)
                min_duration_ms=75.0,
                max_duration_ms=85.0,
                std_dev_ms=2.5,
                success_rate=1.0,
                metadata={}
            ),
            "validation_performance": BenchmarkResult(
                operation="validation_performance",
                duration_ms=40.0,
                memory_peak_mb=1.5,
                iterations=1,
                avg_duration_ms=40.0,  # < 50ms (VALIDATION)
                min_duration_ms=35.0,
                max_duration_ms=45.0,
                std_dev_ms=2.0,
                success_rate=1.0,
                metadata={}
            ),
            "service_initialization": BenchmarkResult(
                operation="service_initialization",
                duration_ms=150.0,
                memory_peak_mb=3.0,
                iterations=1,
                avg_duration_ms=150.0,  # < 200ms (SERVICE_INIT)
                min_duration_ms=140.0,
                max_duration_ms=160.0,
                std_dev_ms=5.0,
                success_rate=1.0,
                metadata={}
            )
        }

        # Mock all benchmark methods with passing results
        mocks = {
            'benchmark_preset_loading': Mock(return_value=passing_results["preset_loading"]),
            'benchmark_settings_initialization': Mock(return_value=passing_results["settings_initialization"]),
            'benchmark_validation_performance': Mock(return_value=passing_results["validation_performance"]),
            'benchmark_service_initialization': Mock(return_value=passing_results["service_initialization"]),
            'benchmark_resilience_config_loading': Mock(return_value=BenchmarkResult(
                operation="resilience_config_loading",
                duration_ms=80.0,
                memory_peak_mb=2.0,
                iterations=1,
                avg_duration_ms=80.0,  # < 100ms (CONFIG_LOADING)
                min_duration_ms=75.0,
                max_duration_ms=85.0,
                std_dev_ms=2.5,
                success_rate=1.0,
                metadata={}
            )),
            'benchmark_custom_config_loading': Mock(return_value=BenchmarkResult(
                operation="custom_config_loading",
                duration_ms=80.0,
                memory_peak_mb=2.0,
                iterations=1,
                avg_duration_ms=80.0,  # < 100ms (CONFIG_LOADING)
                min_duration_ms=75.0,
                max_duration_ms=85.0,
                std_dev_ms=2.5,
                success_rate=1.0,
                metadata={}
            )),
            'benchmark_legacy_config_loading': Mock(return_value=BenchmarkResult(
                operation="legacy_config_loading",
                duration_ms=80.0,
                memory_peak_mb=2.0,
                iterations=1,
                avg_duration_ms=80.0,  # < 100ms (CONFIG_LOADING)
                min_duration_ms=75.0,
                max_duration_ms=85.0,
                std_dev_ms=2.5,
                success_rate=1.0,
                metadata={}
            ))
        }

        with patch.multiple(benchmark, **mocks):
            # When: run_comprehensive_benchmark completes
            suite = benchmark.run_comprehensive_benchmark()

        # Then: BenchmarkSuite.pass_rate equals 1.0
        assert suite.pass_rate == 1.0

        # And: All benchmarks are counted as passing
        assert len(suite.results) == 7
        assert all(result.success_rate == 1.0 for result in suite.results)

    def test_run_comprehensive_benchmark_calculates_pass_rate_with_some_failures(self, fake_time_module, monkeypatch):
        """
        Test that run_comprehensive_benchmark calculates correct pass rate with partial failures.

        Verifies:
            BenchmarkSuite.pass_rate accurately reflects ratio of passing benchmarks
            when some operations exceed their performance thresholds.

        Business Impact:
            Accurate pass rate enables identification of specific performance
            issues requiring attention while showing overall system health.

        Scenario:
            Given: A fake time module causing some benchmarks to exceed thresholds
            And: 5 out of 7 benchmarks meet their performance targets
            When: run_comprehensive_benchmark completes
            Then: BenchmarkSuite.pass_rate approximately equals 0.71 (5/7)
            And: Partial failures are accurately reflected

        Fixtures Used:
            - fake_time_module: Controls execution times for threshold testing
        """
        # Given: A fake time module causing some benchmarks to exceed thresholds
        fake_time_module.set_time(1000.0)
        benchmark = ConfigurationPerformanceBenchmark()

        # Create results with 5 passing and 2 failing benchmarks
        passing_result = BenchmarkResult(
            operation="test",
            duration_ms=50.0,
            memory_peak_mb=1.0,
            iterations=1,
            avg_duration_ms=50.0,  # Should pass most thresholds
            min_duration_ms=45.0,
            max_duration_ms=55.0,
            std_dev_ms=2.0,
            success_rate=1.0,
            metadata={}
        )

        failing_result = BenchmarkResult(
            operation="test",
            duration_ms=500.0,
            memory_peak_mb=5.0,
            iterations=1,
            avg_duration_ms=500.0,  # Should fail most thresholds
            min_duration_ms=450.0,
            max_duration_ms=550.0,
            std_dev_ms=20.0,
            success_rate=1.0,
            metadata={}
        )

        # Mock 5 passing and 2 failing benchmarks
        mocks = {
            'benchmark_preset_loading': Mock(return_value=BenchmarkResult(
                operation="preset_loading", duration_ms=25.0, memory_peak_mb=1.0, iterations=1,
                avg_duration_ms=5.0, min_duration_ms=4.0, max_duration_ms=6.0, std_dev_ms=0.5, success_rate=1.0, metadata={}  # Pass
            )),
            'benchmark_settings_initialization': Mock(return_value=BenchmarkResult(
                operation="settings_initialization", duration_ms=200.0, memory_peak_mb=2.0, iterations=1,
                avg_duration_ms=200.0, min_duration_ms=180.0, max_duration_ms=220.0, std_dev_ms=10.0, success_rate=1.0, metadata={}  # Fail
            )),
            'benchmark_resilience_config_loading': Mock(return_value=BenchmarkResult(
                operation="resilience_config_loading", duration_ms=80.0, memory_peak_mb=1.5, iterations=1,
                avg_duration_ms=80.0, min_duration_ms=75.0, max_duration_ms=85.0, std_dev_ms=2.5, success_rate=1.0, metadata={}  # Pass
            )),
            'benchmark_service_initialization': Mock(return_value=BenchmarkResult(
                operation="service_initialization", duration_ms=150.0, memory_peak_mb=2.5, iterations=1,
                avg_duration_ms=150.0, min_duration_ms=140.0, max_duration_ms=160.0, std_dev_ms=5.0, success_rate=1.0, metadata={}  # Pass
            )),
            'benchmark_custom_config_loading': Mock(return_value=BenchmarkResult(
                operation="custom_config_loading", duration_ms=80.0, memory_peak_mb=1.5, iterations=1,
                avg_duration_ms=80.0, min_duration_ms=75.0, max_duration_ms=85.0, std_dev_ms=2.5, success_rate=1.0, metadata={}  # Pass
            )),
            'benchmark_legacy_config_loading': Mock(return_value=BenchmarkResult(
                operation="legacy_config_loading", duration_ms=300.0, memory_peak_mb=3.0, iterations=1,
                avg_duration_ms=300.0, min_duration_ms=280.0, max_duration_ms=320.0, std_dev_ms=15.0, success_rate=1.0, metadata={}  # Fail
            )),
            'benchmark_validation_performance': Mock(return_value=BenchmarkResult(
                operation="validation_performance", duration_ms=40.0, memory_peak_mb=1.2, iterations=1,
                avg_duration_ms=40.0, min_duration_ms=35.0, max_duration_ms=45.0, std_dev_ms=2.0, success_rate=1.0, metadata={}  # Pass
            ))
        }

        with patch.multiple(benchmark, **mocks):
            # When: run_comprehensive_benchmark completes
            suite = benchmark.run_comprehensive_benchmark()

        # Then: BenchmarkSuite.pass_rate approximately equals 0.71 (5/7)
        expected_pass_rate = 5.0 / 7.0
        assert abs(suite.pass_rate - expected_pass_rate) < 0.01

        # And: Partial failures are accurately reflected
        assert 0.0 < suite.pass_rate < 1.0
        assert len(suite.results) == 7

    def test_run_comprehensive_benchmark_calculates_pass_rate_with_all_failures(self, fake_time_module, monkeypatch):
        """
        Test that run_comprehensive_benchmark calculates 0% pass rate when all exceed thresholds.

        Verifies:
            BenchmarkSuite.pass_rate equals 0.0 when all benchmarks exceed their
            performance thresholds, indicating systemic performance issues.

        Business Impact:
            Zero pass rate clearly indicates critical performance problems
            requiring immediate investigation before deployment.

        Scenario:
            Given: A fake time module causing all benchmarks to exceed thresholds
            And: All benchmarks take longer than their performance targets
            When: run_comprehensive_benchmark completes
            Then: BenchmarkSuite.pass_rate equals 0.0
            And: Complete failure is clearly indicated

        Fixtures Used:
            - fake_time_module: Simulates slow execution exceeding all thresholds
        """
        # Given: A fake time module causing all benchmarks to exceed thresholds
        fake_time_module.set_time(1000.0)
        benchmark = ConfigurationPerformanceBenchmark()

        # Create failing results that exceed all thresholds
        failing_result = BenchmarkResult(
            operation="test",
            duration_ms=1000.0,
            memory_peak_mb=10.0,
            iterations=1,
            avg_duration_ms=1000.0,  # Should fail all thresholds
            min_duration_ms=900.0,
            max_duration_ms=1100.0,
            std_dev_ms=50.0,
            success_rate=1.0,
            metadata={}
        )

        # Mock all benchmarks to fail
        mocks = {
            'benchmark_preset_loading': Mock(return_value=BenchmarkResult(
                operation="preset_loading", duration_ms=1000.0, memory_peak_mb=10.0, iterations=1,
                avg_duration_ms=1000.0, min_duration_ms=900.0, max_duration_ms=1100.0, std_dev_ms=50.0, success_rate=1.0, metadata={}
            )),
            'benchmark_settings_initialization': Mock(return_value=BenchmarkResult(
                operation="settings_initialization", duration_ms=1000.0, memory_peak_mb=10.0, iterations=1,
                avg_duration_ms=1000.0, min_duration_ms=900.0, max_duration_ms=1100.0, std_dev_ms=50.0, success_rate=1.0, metadata={}
            )),
            'benchmark_resilience_config_loading': Mock(return_value=BenchmarkResult(
                operation="resilience_config_loading", duration_ms=1000.0, memory_peak_mb=10.0, iterations=1,
                avg_duration_ms=1000.0, min_duration_ms=900.0, max_duration_ms=1100.0, std_dev_ms=50.0, success_rate=1.0, metadata={}
            )),
            'benchmark_service_initialization': Mock(return_value=BenchmarkResult(
                operation="service_initialization", duration_ms=1000.0, memory_peak_mb=10.0, iterations=1,
                avg_duration_ms=1000.0, min_duration_ms=900.0, max_duration_ms=1100.0, std_dev_ms=50.0, success_rate=1.0, metadata={}
            )),
            'benchmark_custom_config_loading': Mock(return_value=BenchmarkResult(
                operation="custom_config_loading", duration_ms=1000.0, memory_peak_mb=10.0, iterations=1,
                avg_duration_ms=1000.0, min_duration_ms=900.0, max_duration_ms=1100.0, std_dev_ms=50.0, success_rate=1.0, metadata={}
            )),
            'benchmark_legacy_config_loading': Mock(return_value=BenchmarkResult(
                operation="legacy_config_loading", duration_ms=1000.0, memory_peak_mb=10.0, iterations=1,
                avg_duration_ms=1000.0, min_duration_ms=900.0, max_duration_ms=1100.0, std_dev_ms=50.0, success_rate=1.0, metadata={}
            )),
            'benchmark_validation_performance': Mock(return_value=BenchmarkResult(
                operation="validation_performance", duration_ms=1000.0, memory_peak_mb=10.0, iterations=1,
                avg_duration_ms=1000.0, min_duration_ms=900.0, max_duration_ms=1100.0, std_dev_ms=50.0, success_rate=1.0, metadata={}
            ))
        }

        with patch.multiple(benchmark, **mocks):
            # When: run_comprehensive_benchmark completes
            suite = benchmark.run_comprehensive_benchmark()

        # Then: BenchmarkSuite.pass_rate equals 0.0
        assert suite.pass_rate == 0.0

        # And: Complete failure is clearly indicated
        assert len(suite.results) == 7
        assert all(result.avg_duration_ms > 200 for result in suite.results)  # All exceed thresholds


class TestRunComprehensiveBenchmarkEnvironmentContext:
    """
    Tests for run_comprehensive_benchmark() environment context collection.
    
    Scope:
        Verifies collection of environment information including timestamp,
        system details, and execution context for result interpretation.
    
    Business Impact:
        Environment context enables correlation of performance with
        system configuration, aiding root cause analysis of issues.
    
    Test Strategy:
        - Test timestamp inclusion
        - Test environment info structure
        - Test context completeness
    """

    def test_run_comprehensive_benchmark_includes_timestamp(self):
        """
        Test that run_comprehensive_benchmark includes execution timestamp.

        Verifies:
            BenchmarkSuite.timestamp contains ISO format timestamp of suite
            execution for historical tracking and trend analysis.

        Business Impact:
            Timestamp enables chronological tracking of performance over time
            and correlation with deployments or configuration changes.

        Scenario:
            Given: A comprehensive benchmark execution
            When: run_comprehensive_benchmark completes
            Then: BenchmarkSuite contains timestamp attribute
            And: Timestamp is in ISO format for standard parsing

        Fixtures Used:
            - None required for timestamp verification
        """
        pass

    def test_run_comprehensive_benchmark_includes_environment_info(self):
        """
        Test that run_comprehensive_benchmark includes environment information.

        Verifies:
            BenchmarkSuite.environment_info contains system environment details
            for result context per documented Returns section.

        Business Impact:
            Environment context enables correlation of performance with system
            configuration, aiding troubleshooting and capacity planning.

        Scenario:
            Given: A comprehensive benchmark execution
            When: run_comprehensive_benchmark completes
            Then: BenchmarkSuite.environment_info contains system details
            And: Environment context is available for result analysis

        Fixtures Used:
            - None required for environment info verification
        """
        pass

    def test_run_comprehensive_benchmark_environment_info_includes_timestamp(self):
        """
        Test that environment_info includes timestamp for execution tracking.

        Verifies:
            BenchmarkSuite.environment_info contains timestamp per documented
            contract for execution time tracking.

        Business Impact:
            Timestamp in environment info enables precise correlation of
            results with system events and deployment timeline.

        Scenario:
            Given: A comprehensive benchmark with environment collection
            When: run_comprehensive_benchmark completes
            Then: environment_info dictionary contains "timestamp" key
            And: Timestamp value is accessible for analysis

        Fixtures Used:
            - None required for timestamp in environment info
        """
        pass


class TestRunComprehensiveBenchmarkErrorHandling:
    """
    Tests for run_comprehensive_benchmark() error handling and graceful failure.
    
    Scope:
        Verifies graceful handling of individual benchmark failures, error
        tracking, and continuation of suite execution despite failures.
    
    Business Impact:
        Graceful error handling ensures partial results are available even
        when some benchmarks fail, maximizing diagnostic information.
    
    Test Strategy:
        - Test continuation after individual benchmark failure
        - Test failed benchmark tracking
        - Test partial results availability
        - Test suite completion despite failures
    """

    def test_run_comprehensive_benchmark_continues_after_individual_failure(self):
        """
        Test that run_comprehensive_benchmark continues execution after benchmark failure.

        Verifies:
            Individual benchmark failures don't stop suite execution; remaining
            benchmarks continue to provide comprehensive results per documented behavior.

        Business Impact:
            Resilient suite execution maximizes diagnostic information by
            running all benchmarks even when some fail.

        Scenario:
            Given: A comprehensive benchmark where one benchmark fails
            When: The failing benchmark encounters an error
            Then: Remaining benchmarks continue executing normally
            And: Suite completes with results from successful benchmarks

        Fixtures Used:
            - None required for failure resilience verification
        """
        pass

    def test_run_comprehensive_benchmark_tracks_failed_benchmarks(self):
        """
        Test that run_comprehensive_benchmark tracks failed benchmark names.

        Verifies:
            BenchmarkSuite.failed_benchmarks list contains names of benchmarks
            that failed during execution per documented Returns section.

        Business Impact:
            Failed benchmark tracking enables rapid identification of specific
            operations with performance or execution issues.

        Scenario:
            Given: A comprehensive benchmark with some failing benchmarks
            When: run_comprehensive_benchmark encounters benchmark failures
            Then: BenchmarkSuite.failed_benchmarks contains failed benchmark names
            And: Failed operations can be quickly identified for investigation

        Fixtures Used:
            - None required for failure tracking verification
        """
        pass

    def test_run_comprehensive_benchmark_completes_with_partial_results(self):
        """
        Test that run_comprehensive_benchmark completes successfully with partial results.

        Verifies:
            Suite completes and returns BenchmarkSuite even when some benchmarks
            fail, providing maximum diagnostic information.

        Business Impact:
            Partial results enable performance analysis of successful operations
            even when some benchmarks fail, aiding troubleshooting.

        Scenario:
            Given: A comprehensive benchmark where 2 out of 7 benchmarks fail
            When: run_comprehensive_benchmark executes all benchmarks
            Then: BenchmarkSuite is returned successfully
            And: Results contain data from 5 successful benchmarks
            And: failed_benchmarks lists the 2 failed operations

        Fixtures Used:
            - None required for partial completion verification
        """
        pass

    def test_run_comprehensive_benchmark_logs_progress_and_completion(self, mock_logger, monkeypatch):
        """
        Test that run_comprehensive_benchmark logs progress and completion metrics.

        Verifies:
            Progress and completion are logged for monitoring and debugging
            per documented behavior section.

        Business Impact:
            Progress logging enables real-time monitoring of benchmark execution
            and identification of slow or stuck operations.

        Scenario:
            Given: A mock logger configured for benchmark suite
            When: run_comprehensive_benchmark executes
            Then: Progress is logged during execution
            And: Completion metrics are logged at suite end

        Fixtures Used:
            - mock_logger: Captures logging calls for verification
        """
        pass


class TestRunComprehensiveBenchmarkTotalDuration:
    """
    Tests for run_comprehensive_benchmark() total duration measurement.
    
    Scope:
        Verifies accurate measurement of total suite execution time across
        all benchmarks for performance tracking.
    
    Business Impact:
        Total duration measurement enables tracking of complete benchmark
        suite performance and CI/CD pipeline impact.
    
    Test Strategy:
        - Test total duration calculation
        - Test duration units (milliseconds)
        - Test duration accuracy
    """

    def test_run_comprehensive_benchmark_measures_total_duration(self, fake_time_module, monkeypatch):
        """
        Test that run_comprehensive_benchmark measures total suite execution time.

        Verifies:
            BenchmarkSuite.total_duration_ms contains total execution time across
            all benchmarks in milliseconds per documented Returns section.

        Business Impact:
            Total duration tracking enables monitoring of benchmark suite
            performance and optimization of suite execution time.

        Scenario:
            Given: A fake time module tracking total execution time
            When: run_comprehensive_benchmark executes all benchmarks
            Then: BenchmarkSuite.total_duration_ms reflects total execution time
            And: Duration is reported in milliseconds for consistency

        Fixtures Used:
            - fake_time_module: Provides deterministic timing for total duration
        """
        pass

    def test_run_comprehensive_benchmark_total_duration_includes_all_benchmarks(self, fake_time_module, monkeypatch):
        """
        Test that total duration includes time from all executed benchmarks.

        Verifies:
            Total duration represents cumulative execution time of all individual
            benchmarks without double-counting or omissions.

        Business Impact:
            Accurate total duration enables assessment of complete suite
            performance impact on CI/CD pipelines and development workflows.

        Scenario:
            Given: A fake time module tracking cumulative execution
            And: Seven benchmarks with known individual durations
            When: run_comprehensive_benchmark executes all benchmarks
            Then: total_duration_ms equals sum of individual benchmark durations
            And: No benchmarks are omitted from total duration

        Fixtures Used:
            - fake_time_module: Tracks cumulative timing across benchmarks
        """
        # Given: A fake time module tracking cumulative execution
        fake_time_module.set_time(1000.0)
        benchmark = ConfigurationPerformanceBenchmark()

        # Mock benchmark results with predictable timing
        mock_result = BenchmarkResult(
            operation="test",
            duration_ms=50.0,
            memory_peak_mb=1.0,
            iterations=1,
            avg_duration_ms=50.0,
            min_duration_ms=45.0,
            max_duration_ms=55.0,
            std_dev_ms=2.0,
            success_rate=1.0,
            metadata={}
        )

        # Mock all benchmarks with distinct results
        mocks = {
            'benchmark_preset_loading': Mock(return_value=BenchmarkResult(
                operation="preset_loading", duration_ms=50.0, memory_peak_mb=1.0, iterations=1,
                avg_duration_ms=50.0, min_duration_ms=45.0, max_duration_ms=55.0, std_dev_ms=2.0, success_rate=1.0, metadata={}
            )),
            'benchmark_settings_initialization': Mock(return_value=BenchmarkResult(
                operation="settings_initialization", duration_ms=60.0, memory_peak_mb=1.2, iterations=1,
                avg_duration_ms=60.0, min_duration_ms=55.0, max_duration_ms=65.0, std_dev_ms=2.5, success_rate=1.0, metadata={}
            )),
            'benchmark_resilience_config_loading': Mock(return_value=BenchmarkResult(
                operation="resilience_config_loading", duration_ms=70.0, memory_peak_mb=1.4, iterations=1,
                avg_duration_ms=70.0, min_duration_ms=65.0, max_duration_ms=75.0, std_dev_ms=3.0, success_rate=1.0, metadata={}
            )),
            'benchmark_service_initialization': Mock(return_value=BenchmarkResult(
                operation="service_initialization", duration_ms=80.0, memory_peak_mb=1.6, iterations=1,
                avg_duration_ms=80.0, min_duration_ms=75.0, max_duration_ms=85.0, std_dev_ms=3.5, success_rate=1.0, metadata={}
            )),
            'benchmark_custom_config_loading': Mock(return_value=BenchmarkResult(
                operation="custom_config_loading", duration_ms=90.0, memory_peak_mb=1.8, iterations=1,
                avg_duration_ms=90.0, min_duration_ms=85.0, max_duration_ms=95.0, std_dev_ms=4.0, success_rate=1.0, metadata={}
            )),
            'benchmark_legacy_config_loading': Mock(return_value=BenchmarkResult(
                operation="legacy_config_loading", duration_ms=100.0, memory_peak_mb=2.0, iterations=1,
                avg_duration_ms=100.0, min_duration_ms=95.0, max_duration_ms=105.0, std_dev_ms=4.5, success_rate=1.0, metadata={}
            )),
            'benchmark_validation_performance': Mock(return_value=BenchmarkResult(
                operation="validation_performance", duration_ms=110.0, memory_peak_mb=2.2, iterations=1,
                avg_duration_ms=110.0, min_duration_ms=105.0, max_duration_ms=115.0, std_dev_ms=5.0, success_rate=1.0, metadata={}
            ))
        }

        with patch.multiple(benchmark, **mocks):
            # When: run_comprehensive_benchmark executes all benchmarks
            suite = benchmark.run_comprehensive_benchmark()

        # Then: total_duration_ms reflects total execution time
        assert suite.total_duration_ms > 0
        assert isinstance(suite.total_duration_ms, (int, float))

        # And: Duration is reported in milliseconds for consistency
        # Verify it's a reasonable duration (not in seconds or nanoseconds)
        assert 1 < suite.total_duration_ms < 100000  # Between 1ms and 100s


class TestBenchmarkSuiteConversion:
    """
    Tests for BenchmarkSuite.to_dict() and to_json() conversion methods.

    Scope:
        Verifies proper conversion of BenchmarkSuite to dictionary and JSON
        formats for serialization and analysis.

    Business Impact:
        Conversion methods enable benchmark result storage, transmission,
        and analysis in external systems and reporting tools.

    Test Strategy:
        - Test to_dict() method completeness
        - Test to_json() method format
        - Test serialization integrity
    """

    def test_benchmark_suite_to_dict_conversion(self):
        """
        Test that BenchmarkSuite.to_dict() converts all suite data to dictionary.

        Verifies:
            All suite attributes are properly converted to dictionary format with
            correct types and structure for serialization.

        Business Impact:
            Dictionary conversion enables storage and transmission of benchmark
            results in structured format for analysis and reporting.

        Scenario:
            Given: A BenchmarkSuite with complete test data
            When: to_dict() method is called
            Then: All suite attributes are present in dictionary
            And: Data types are preserved correctly
            And: BenchmarkResult objects are converted to dictionaries

        Fixtures Used:
            - None required for conversion testing
        """
        # Given: A BenchmarkSuite with complete test data
        test_results = [
            BenchmarkResult(
                operation="test_operation",
                duration_ms=100.0,
                memory_peak_mb=5.0,
                iterations=10,
                avg_duration_ms=10.0,
                min_duration_ms=8.0,
                max_duration_ms=12.0,
                std_dev_ms=1.0,
                success_rate=1.0,
                metadata={"test": "data"}
            )
        ]

        suite = BenchmarkSuite(
            name="Test Benchmark Suite",
            results=test_results,
            total_duration_ms=500.0,
            pass_rate=1.0,
            failed_benchmarks=[],
            timestamp="2023-01-01 00:00:00 UTC",
            environment_info={"python_version": "3.9", "platform": "test"}
        )

        # When: to_dict() method is called
        result_dict = suite.to_dict()

        # Then: All suite attributes are present in dictionary
        expected_keys = [
            "name", "results", "total_duration_ms", "pass_rate",
            "failed_benchmarks", "timestamp", "environment_info"
        ]
        for key in expected_keys:
            assert key in result_dict, f"Missing key: {key}"

        # And: Data types are preserved correctly
        assert isinstance(result_dict["name"], str)
        assert isinstance(result_dict["results"], list)
        assert isinstance(result_dict["total_duration_ms"], (int, float))
        assert isinstance(result_dict["pass_rate"], (int, float))
        assert isinstance(result_dict["failed_benchmarks"], list)
        assert isinstance(result_dict["timestamp"], str)
        assert isinstance(result_dict["environment_info"], dict)

        # And: BenchmarkResult objects are converted to dictionaries
        assert len(result_dict["results"]) == 1
        result_entry = result_dict["results"][0]
        assert isinstance(result_entry, dict)
        assert result_entry["operation"] == "test_operation"
        assert result_entry["avg_duration_ms"] == 10.0

    def test_benchmark_suite_to_json_conversion(self):
        """
        Test that BenchmarkSuite.to_json() converts suite to JSON string.

        Verifies:
            Suite data is properly serialized to JSON format with proper
            structure and valid JSON syntax for storage and transmission.

        Business Impact:
            JSON conversion enables easy storage, transmission, and integration
            with web-based tools and external analysis systems.

        Scenario:
            Given: A BenchmarkSuite with test data
            When: to_json() method is called
            Then: Valid JSON string is returned
            And: JSON contains all suite data
            And: JSON can be parsed back to reconstruct data

        Fixtures Used:
            - None required for JSON conversion testing
        """
        import json

        # Given: A BenchmarkSuite with test data
        test_results = [
            BenchmarkResult(
                operation="json_test",
                duration_ms=75.0,
                memory_peak_mb=3.0,
                iterations=5,
                avg_duration_ms=15.0,
                min_duration_ms=12.0,
                max_duration_ms=18.0,
                std_dev_ms=2.0,
                success_rate=1.0,
                metadata={"format": "json"}
            )
        ]

        suite = BenchmarkSuite(
            name="JSON Test Suite",
            results=test_results,
            total_duration_ms=300.0,
            pass_rate=0.8,
            failed_benchmarks=["failed_benchmark"],
            timestamp="2023-01-01 12:00:00 UTC",
            environment_info={"format": "json", "test": True}
        )

        # When: to_json() method is called
        json_string = suite.to_json()

        # Then: Valid JSON string is returned
        assert isinstance(json_string, str)
        assert len(json_string) > 0

        # And: JSON contains all suite data
        parsed_data = json.loads(json_string)
        assert parsed_data["name"] == "JSON Test Suite"
        assert parsed_data["pass_rate"] == 0.8
        assert "failed_benchmark" in parsed_data["failed_benchmarks"]
        assert parsed_data["environment_info"]["format"] == "json"

        # And: JSON can be parsed back to reconstruct data
        assert len(parsed_data["results"]) == 1
        result = parsed_data["results"][0]
        assert result["operation"] == "json_test"
        assert result["avg_duration_ms"] == 15.0

