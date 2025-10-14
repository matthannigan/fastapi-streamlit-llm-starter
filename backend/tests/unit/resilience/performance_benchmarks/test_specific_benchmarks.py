"""
Test suite for ConfigurationPerformanceBenchmark specific benchmark methods.

This module verifies the specific benchmark methods that measure performance
of individual resilience configuration operations including preset loading,
settings initialization, config loading, service initialization, and validation.

Test Strategy:
    - Test each benchmark method independently
    - Verify iteration count handling
    - Verify BenchmarkResult structure
    - Verify operation names match expectations
    - Verify performance target validation
    - Test with fake external dependencies

Business Critical:
    Each specific benchmark validates critical configuration performance targets
    (<100ms config loading, <10ms preset access, <50ms validation, <200ms service init).
    Meeting these targets ensures the system starts quickly and responds to configuration
    changes without impacting user experience.
"""

import pytest
from unittest.mock import Mock, patch, call

from app.infrastructure.resilience.performance_benchmarks import (
    ConfigurationPerformanceBenchmark,
    BenchmarkResult
)


class TestBenchmarkPresetLoading:
    """
    Tests for benchmark_preset_loading() method behavior.
    
    Scope:
        Verifies preset loading performance measurement, iteration handling,
        and target validation against <10ms PRESET_ACCESS threshold.
    
    Business Impact:
        Preset loading speed directly impacts application startup time and
        configuration reload responsiveness. <10ms target ensures minimal latency.
    
    Test Strategy:
        - Test default iteration count (100)
        - Test custom iteration counts
        - Test BenchmarkResult structure
        - Test operation naming
        - Test with fake time for deterministic timing
    """

    def test_benchmark_preset_loading_executes_with_default_iterations(self):
        """
        Test that benchmark_preset_loading executes 100 iterations by default.

        Verifies:
            Default iterations parameter of 100 is used when no custom value provided,
            matching documented contract for preset loading benchmarks.

        Business Impact:
            Sufficient iteration count (100) provides statistically significant
            preset loading performance measurements for regression detection.

        Scenario:
            Given: A benchmark instance ready to measure preset loading
            When: benchmark_preset_loading is called without iterations parameter
            Then: Benchmark executes 100 iterations for statistical significance
            And: BenchmarkResult.iterations equals 100

        Fixtures Used:
            - None required for iteration count verification
        """
        # Arrange
        benchmark = ConfigurationPerformanceBenchmark()

        # Mock measure_performance to capture the iterations parameter
        with patch.object(benchmark, 'measure_performance') as mock_measure:
            mock_measure.return_value = BenchmarkResult(
                operation="preset_loading",
                duration_ms=100.0,
                memory_peak_mb=1.0,
                iterations=100,
                avg_duration_ms=1.0,
                min_duration_ms=0.5,
                max_duration_ms=2.0,
                std_dev_ms=0.3,
                success_rate=1.0,
                metadata={}
            )

            # Act
            result = benchmark.benchmark_preset_loading()

            # Assert
            mock_measure.assert_called_once()
            call_args = mock_measure.call_args
            assert call_args[0][0] == "preset_loading"  # operation_name
            assert call_args[0][1] is not None  # operation_func
            assert call_args[0][2] == 100  # default iterations (3rd positional argument)
            assert result.iterations == 100
            assert result.operation == "preset_loading"

    def test_benchmark_preset_loading_accepts_custom_iteration_count(self):
        """
        Test that benchmark_preset_loading accepts custom iteration count.

        Verifies:
            Custom iterations parameter is respected, enabling flexible benchmark
            execution for different testing scenarios per documented Args.

        Business Impact:
            Flexible iteration counts enable quick smoke tests (low iterations)
            or thorough validation (high iterations) based on testing needs.

        Scenario:
            Given: A benchmark instance with custom iteration requirement
            When: benchmark_preset_loading is called with iterations=25
            Then: Benchmark executes exactly 25 iterations
            And: BenchmarkResult.iterations equals 25

        Fixtures Used:
            - None required for custom iteration verification
        """
        # Arrange
        benchmark = ConfigurationPerformanceBenchmark()
        custom_iterations = 25

        with patch.object(benchmark, 'measure_performance') as mock_measure:
            mock_measure.return_value = BenchmarkResult(
                operation="preset_loading",
                duration_ms=50.0,
                memory_peak_mb=1.0,
                iterations=custom_iterations,
                avg_duration_ms=2.0,
                min_duration_ms=1.0,
                max_duration_ms=4.0,
                std_dev_ms=0.5,
                success_rate=1.0,
                metadata={}
            )

            # Act
            result = benchmark.benchmark_preset_loading(iterations=custom_iterations)

            # Assert
            mock_measure.assert_called_once()
            call_args = mock_measure.call_args
            assert call_args[0][2] == custom_iterations  # custom iterations (3rd positional argument)
            assert result.iterations == custom_iterations
            assert result.operation == "preset_loading"

    def test_benchmark_preset_loading_returns_benchmark_result(self):
        """
        Test that benchmark_preset_loading returns BenchmarkResult object.

        Verifies:
            Return type is BenchmarkResult containing comprehensive preset loading
            performance metrics as documented in Returns section.

        Business Impact:
            Structured result format enables automated performance analysis,
            regression detection, and performance reporting for preset access.

        Scenario:
            Given: A benchmark instance measuring preset loading
            When: benchmark_preset_loading completes execution
            Then: Return value is a BenchmarkResult instance
            And: Result contains all required performance metrics

        Fixtures Used:
            - None required for return type verification
        """
        # Arrange
        benchmark = ConfigurationPerformanceBenchmark()

        with patch.object(benchmark, 'measure_performance') as mock_measure:
            expected_result = BenchmarkResult(
                operation="preset_loading",
                duration_ms=120.0,
                memory_peak_mb=2.5,
                iterations=100,
                avg_duration_ms=1.2,
                min_duration_ms=0.8,
                max_duration_ms=2.0,
                std_dev_ms=0.3,
                success_rate=1.0,
                metadata={"preset_simple_loaded": True, "preset_development_loaded": True}
            )
            mock_measure.return_value = expected_result

            # Act
            result = benchmark.benchmark_preset_loading()

            # Assert
            assert isinstance(result, BenchmarkResult)
            assert result.operation == "preset_loading"
            assert result.duration_ms == 120.0
            assert result.memory_peak_mb == 2.5
            assert result.iterations == 100
            assert result.avg_duration_ms == 1.2
            assert result.success_rate == 1.0
            assert isinstance(result.metadata, dict)

    def test_benchmark_preset_loading_sets_correct_operation_name(self):
        """
        Test that benchmark_preset_loading uses "preset_loading" operation name.

        Verifies:
            BenchmarkResult.operation is set to "preset_loading" for result
            identification and filtering in analysis tools.

        Business Impact:
            Consistent operation naming enables filtering and analysis of
            preset loading performance across benchmark runs.

        Scenario:
            Given: A benchmark measuring preset loading performance
            When: benchmark_preset_loading completes execution
            Then: BenchmarkResult.operation equals "preset_loading"
            And: Result can be identified in performance reports

        Fixtures Used:
            - None required for operation name verification
        """
        # Arrange
        benchmark = ConfigurationPerformanceBenchmark()

        with patch.object(benchmark, 'measure_performance') as mock_measure:
            mock_measure.return_value = BenchmarkResult(
                operation="preset_loading",
                duration_ms=100.0,
                memory_peak_mb=1.0,
                iterations=100,
                avg_duration_ms=1.0,
                min_duration_ms=0.5,
                max_duration_ms=2.0,
                std_dev_ms=0.3,
                success_rate=1.0,
                metadata={}
            )

            # Act
            result = benchmark.benchmark_preset_loading()

            # Assert
            assert result.operation == "preset_loading"
            # Verify that measure_performance was called with the correct operation name
            call_args = mock_measure.call_args
            assert call_args[0][0] == "preset_loading"

    def test_benchmark_preset_loading_measures_actual_preset_access(self, fake_time_module):
        """
        Test that benchmark_preset_loading measures real preset access operations.

        Verifies:
            Benchmark measures actual preset retrieval from PresetManager,
            not simulated operations, for realistic performance data.

        Business Impact:
            Real operation measurement ensures benchmark results reflect
            actual production performance characteristics.

        Scenario:
            Given: A fake time module providing deterministic timing
            When: benchmark_preset_loading executes preset access operations
            Then: Real preset manager retrieval operations are measured
            And: Timing data reflects actual preset access performance

        Fixtures Used:
            - fake_time_module: Provides deterministic timing without affecting measured operations
        """
        # Arrange
        benchmark = ConfigurationPerformanceBenchmark()
        fake_time_module.set_time(1000.0)  # Set deterministic start time

        # Mock the actual preset loading operation to verify it gets called
        with patch('app.infrastructure.resilience.config_presets.preset_manager') as mock_preset_manager:
            mock_preset_manager.get_preset.return_value = {"retry_attempts": 3}

            # Act
            result = benchmark.benchmark_preset_loading(iterations=5)

            # Assert
            # Verify that preset manager was called for each preset
            expected_presets = ["simple", "development", "production"]
            assert mock_preset_manager.get_preset.call_count == len(expected_presets) * 5  # 5 iterations * 3 presets

            # Verify all expected presets were accessed
            called_presets = [call[0][0] for call in mock_preset_manager.get_preset.call_args_list]
            for preset in expected_presets:
                assert preset in called_presets

            # Verify result structure
            assert result.operation == "preset_loading"
            assert result.iterations == 5


class TestBenchmarkSettingsInitialization:
    """
    Tests for benchmark_settings_initialization() method behavior.
    
    Scope:
        Verifies Settings class initialization performance measurement
        against <100ms CONFIG_LOADING threshold.
    
    Business Impact:
        Settings initialization speed impacts application startup time.
        <100ms target ensures fast application startup without user delays.
    
    Test Strategy:
        - Test default iteration count (50)
        - Test custom iteration counts
        - Test BenchmarkResult structure
        - Test operation naming
    """

    def test_benchmark_settings_initialization_executes_with_default_iterations(self):
        """
        Test that benchmark_settings_initialization executes 50 iterations by default.

        Verifies:
            Default iterations parameter of 50 is used when no custom value provided,
            matching documented contract for settings initialization benchmarks.

        Business Impact:
            50 iterations provide sufficient statistical significance while
            keeping benchmark execution time reasonable for CI/CD pipelines.

        Scenario:
            Given: A benchmark instance measuring settings initialization
            When: benchmark_settings_initialization is called without iterations parameter
            Then: Benchmark executes 50 iterations for statistical validity
            And: BenchmarkResult.iterations equals 50

        Fixtures Used:
            - None required for iteration count verification
        """
        # Arrange
        benchmark = ConfigurationPerformanceBenchmark()

        with patch.object(benchmark, 'measure_performance') as mock_measure:
            mock_measure.return_value = BenchmarkResult(
                operation="settings_initialization",
                duration_ms=200.0,
                memory_peak_mb=5.0,
                iterations=50,
                avg_duration_ms=4.0,
                min_duration_ms=3.0,
                max_duration_ms=6.0,
                std_dev_ms=0.8,
                success_rate=1.0,
                metadata={}
            )

            # Act
            result = benchmark.benchmark_settings_initialization()

            # Assert
            mock_measure.assert_called_once()
            call_args = mock_measure.call_args
            assert call_args[0][0] == "settings_initialization"  # operation_name
            assert call_args[0][2] == 50  # default iterations (3rd positional argument)
            assert result.iterations == 50
            assert result.operation == "settings_initialization"

    def test_benchmark_settings_initialization_accepts_custom_iteration_count(self):
        """
        Test that benchmark_settings_initialization accepts custom iteration count.

        Verifies:
            Custom iterations parameter enables flexible benchmark execution
            for different testing scenarios per documented Args.

        Business Impact:
            Flexible iteration counts enable quick smoke tests or thorough
            validation based on testing context and time constraints.

        Scenario:
            Given: A benchmark with custom iteration requirement
            When: benchmark_settings_initialization is called with iterations=10
            Then: Benchmark executes exactly 10 iterations
            And: BenchmarkResult.iterations equals 10

        Fixtures Used:
            - None required for custom iteration verification
        """
        # Arrange
        benchmark = ConfigurationPerformanceBenchmark()
        custom_iterations = 10

        with patch.object(benchmark, 'measure_performance') as mock_measure:
            mock_measure.return_value = BenchmarkResult(
                operation="settings_initialization",
                duration_ms=40.0,
                memory_peak_mb=2.0,
                iterations=custom_iterations,
                avg_duration_ms=4.0,
                min_duration_ms=3.0,
                max_duration_ms=6.0,
                std_dev_ms=0.8,
                success_rate=1.0,
                metadata={}
            )

            # Act
            result = benchmark.benchmark_settings_initialization(iterations=custom_iterations)

            # Assert
            mock_measure.assert_called_once()
            call_args = mock_measure.call_args
            assert call_args[0][2] == custom_iterations
            assert result.iterations == custom_iterations
            assert result.operation == "settings_initialization"

    def test_benchmark_settings_initialization_returns_benchmark_result(self):
        """
        Test that benchmark_settings_initialization returns BenchmarkResult.

        Verifies:
            Return type is BenchmarkResult containing comprehensive settings
            initialization performance metrics as documented.

        Business Impact:
            Structured result format enables automated performance analysis
            and regression detection for settings initialization performance.

        Scenario:
            Given: A benchmark measuring settings initialization
            When: benchmark_settings_initialization completes execution
            Then: Return value is a BenchmarkResult instance
            And: Result contains all required performance metrics

        Fixtures Used:
            - None required for return type verification
        """
        # Arrange
        benchmark = ConfigurationPerformanceBenchmark()

        with patch.object(benchmark, 'measure_performance') as mock_measure:
            expected_result = BenchmarkResult(
                operation="settings_initialization",
                duration_ms=180.0,
                memory_peak_mb=4.5,
                iterations=50,
                avg_duration_ms=3.6,
                min_duration_ms=2.8,
                max_duration_ms=5.2,
                std_dev_ms=0.7,
                success_rate=1.0,
                metadata={"settings_simple_initialized": True, "settings_development_initialized": True}
            )
            mock_measure.return_value = expected_result

            # Act
            result = benchmark.benchmark_settings_initialization()

            # Assert
            assert isinstance(result, BenchmarkResult)
            assert result.operation == "settings_initialization"
            assert result.duration_ms == 180.0
            assert result.memory_peak_mb == 4.5
            assert result.iterations == 50
            assert result.success_rate == 1.0

    def test_benchmark_settings_initialization_sets_correct_operation_name(self):
        """
        Test that benchmark_settings_initialization uses correct operation name.

        Verifies:
            BenchmarkResult.operation is set to "settings_initialization" for
            result identification in analysis tools.

        Business Impact:
            Consistent operation naming enables filtering and trend analysis
            of settings initialization performance.

        Scenario:
            Given: A benchmark measuring settings initialization
            When: benchmark_settings_initialization completes execution
            Then: BenchmarkResult.operation equals "settings_initialization"
            And: Result can be filtered in performance reports

        Fixtures Used:
            - None required for operation name verification
        """
        # Arrange
        benchmark = ConfigurationPerformanceBenchmark()

        with patch.object(benchmark, 'measure_performance') as mock_measure:
            mock_measure.return_value = BenchmarkResult(
                operation="settings_initialization",
                duration_ms=150.0,
                memory_peak_mb=4.0,
                iterations=50,
                avg_duration_ms=3.0,
                min_duration_ms=2.0,
                max_duration_ms=5.0,
                std_dev_ms=0.6,
                success_rate=1.0,
                metadata={}
            )

            # Act
            result = benchmark.benchmark_settings_initialization()

            # Assert
            assert result.operation == "settings_initialization"
            call_args = mock_measure.call_args
            assert call_args[0][0] == "settings_initialization"


class TestBenchmarkResilienceConfigLoading:
    """
    Tests for benchmark_resilience_config_loading() method behavior.
    
    Scope:
        Verifies resilience configuration loading performance measurement
        against <100ms CONFIG_LOADING threshold.
    
    Business Impact:
        Configuration loading speed impacts application startup and
        configuration reload operations. <100ms ensures responsive system.
    
    Test Strategy:
        - Test default iteration count (50)
        - Test BenchmarkResult structure
        - Test operation naming
        - Test realistic config loading measurement
    """

    def test_benchmark_resilience_config_loading_executes_with_default_iterations(self):
        """
        Test that benchmark_resilience_config_loading executes 50 iterations by default.

        Verifies:
            Default iterations parameter of 50 provides sufficient statistical
            significance for configuration loading benchmarks.

        Business Impact:
            Balanced iteration count provides statistical validity while
            maintaining reasonable benchmark execution time.

        Scenario:
            Given: A benchmark measuring config loading performance
            When: benchmark_resilience_config_loading is called without iterations
            Then: Benchmark executes 50 iterations
            And: BenchmarkResult.iterations equals 50

        Fixtures Used:
            - None required for iteration count verification
        """
        # Arrange
        benchmark = ConfigurationPerformanceBenchmark()

        with patch.object(benchmark, 'measure_performance') as mock_measure:
            mock_measure.return_value = BenchmarkResult(
                operation="resilience_config_loading",
                duration_ms=300.0,
                memory_peak_mb=8.0,
                iterations=50,
                avg_duration_ms=6.0,
                min_duration_ms=4.0,
                max_duration_ms=10.0,
                std_dev_ms=1.2,
                success_rate=1.0,
                metadata={}
            )

            # Act
            result = benchmark.benchmark_resilience_config_loading()

            # Assert
            mock_measure.assert_called_once()
            call_args = mock_measure.call_args
            assert call_args[0][0] == "resilience_config_loading"
            assert call_args[0][2] == 50
            assert result.iterations == 50
            assert result.operation == "resilience_config_loading"

    def test_benchmark_resilience_config_loading_returns_benchmark_result(self):
        """
        Test that benchmark_resilience_config_loading returns BenchmarkResult.

        Verifies:
            Return type is BenchmarkResult with comprehensive configuration
            loading performance metrics.

        Business Impact:
            Structured results enable automated validation that config loading
            meets <100ms performance target.

        Scenario:
            Given: A benchmark measuring resilience config loading
            When: benchmark_resilience_config_loading completes
            Then: Return value is a BenchmarkResult instance
            And: Result contains configuration loading metrics

        Fixtures Used:
            - None required for return type verification
        """
        # Arrange
        benchmark = ConfigurationPerformanceBenchmark()

        with patch.object(benchmark, 'measure_performance') as mock_measure:
            expected_result = BenchmarkResult(
                operation="resilience_config_loading",
                duration_ms=250.0,
                memory_peak_mb=7.5,
                iterations=50,
                avg_duration_ms=5.0,
                min_duration_ms=3.5,
                max_duration_ms=8.0,
                std_dev_ms=1.0,
                success_rate=1.0,
                metadata={"config_simple_loaded": True}
            )
            mock_measure.return_value = expected_result

            # Act
            result = benchmark.benchmark_resilience_config_loading()

            # Assert
            assert isinstance(result, BenchmarkResult)
            assert result.operation == "resilience_config_loading"
            assert result.iterations == 50
            assert result.success_rate == 1.0

    def test_benchmark_resilience_config_loading_sets_correct_operation_name(self):
        """
        Test that benchmark_resilience_config_loading uses correct operation name.

        Verifies:
            BenchmarkResult.operation is set to "resilience_config_loading"
            for result identification.

        Business Impact:
            Consistent operation naming enables tracking of config loading
            performance trends across releases.

        Scenario:
            Given: A benchmark measuring resilience configuration loading
            When: benchmark_resilience_config_loading completes
            Then: BenchmarkResult.operation equals "resilience_config_loading"
            And: Result can be identified in performance dashboards

        Fixtures Used:
            - None required for operation name verification
        """
        # Arrange
        benchmark = ConfigurationPerformanceBenchmark()

        with patch.object(benchmark, 'measure_performance') as mock_measure:
            mock_measure.return_value = BenchmarkResult(
                operation="resilience_config_loading",
                duration_ms=200.0,
                memory_peak_mb=6.0,
                iterations=50,
                avg_duration_ms=4.0,
                min_duration_ms=3.0,
                max_duration_ms=7.0,
                std_dev_ms=0.9,
                success_rate=1.0,
                metadata={}
            )

            # Act
            result = benchmark.benchmark_resilience_config_loading()

            # Assert
            assert result.operation == "resilience_config_loading"
            call_args = mock_measure.call_args
            assert call_args[0][0] == "resilience_config_loading"


class TestBenchmarkServiceInitialization:
    """
    Tests for benchmark_service_initialization() method behavior.
    
    Scope:
        Verifies AIServiceResilience initialization performance measurement
        against <200ms SERVICE_INIT threshold.
    
    Business Impact:
        Service initialization speed impacts application startup time.
        <200ms target ensures application ready to serve requests quickly.
    
    Test Strategy:
        - Test default iteration count (25)
        - Test BenchmarkResult structure
        - Test operation naming
        - Test service initialization measurement
    """

    def test_benchmark_service_initialization_executes_with_default_iterations(self):
        """
        Test that benchmark_service_initialization executes 25 iterations by default.

        Verifies:
            Default iterations parameter of 25 balances statistical significance
            with reasonable execution time for service initialization benchmarks.

        Business Impact:
            Lower iteration count (25) appropriate for heavier service
            initialization operations while maintaining statistical validity.

        Scenario:
            Given: A benchmark measuring service initialization
            When: benchmark_service_initialization is called without iterations
            Then: Benchmark executes 25 iterations
            And: BenchmarkResult.iterations equals 25

        Fixtures Used:
            - None required for iteration count verification
        """
        # Arrange
        benchmark = ConfigurationPerformanceBenchmark()

        with patch.object(benchmark, 'measure_performance') as mock_measure:
            mock_measure.return_value = BenchmarkResult(
                operation="service_initialization",
                duration_ms=500.0,
                memory_peak_mb=15.0,
                iterations=25,
                avg_duration_ms=20.0,
                min_duration_ms=15.0,
                max_duration_ms=30.0,
                std_dev_ms=3.5,
                success_rate=1.0,
                metadata={}
            )

            # Act
            result = benchmark.benchmark_service_initialization()

            # Assert
            mock_measure.assert_called_once()
            call_args = mock_measure.call_args
            assert call_args[0][0] == "service_initialization"
            assert call_args[0][2] == 25
            assert result.iterations == 25
            assert result.operation == "service_initialization"

    def test_benchmark_service_initialization_returns_benchmark_result(self):
        """
        Test that benchmark_service_initialization returns BenchmarkResult.

        Verifies:
            Return type is BenchmarkResult with comprehensive service
            initialization performance metrics.

        Business Impact:
            Structured results enable validation that service initialization
            meets <200ms performance target for fast startup.

        Scenario:
            Given: A benchmark measuring service initialization
            When: benchmark_service_initialization completes
            Then: Return value is a BenchmarkResult instance
            And: Result contains service initialization metrics

        Fixtures Used:
            - None required for return type verification
        """
        # Arrange
        benchmark = ConfigurationPerformanceBenchmark()

        with patch.object(benchmark, 'measure_performance') as mock_measure:
            expected_result = BenchmarkResult(
                operation="service_initialization",
                duration_ms=450.0,
                memory_peak_mb=14.0,
                iterations=25,
                avg_duration_ms=18.0,
                min_duration_ms=14.0,
                max_duration_ms=28.0,
                std_dev_ms=3.2,
                success_rate=1.0,
                metadata={"service_simple_summarize_config": True}
            )
            mock_measure.return_value = expected_result

            # Act
            result = benchmark.benchmark_service_initialization()

            # Assert
            assert isinstance(result, BenchmarkResult)
            assert result.operation == "service_initialization"
            assert result.iterations == 25
            assert result.success_rate == 1.0

    def test_benchmark_service_initialization_sets_correct_operation_name(self):
        """
        Test that benchmark_service_initialization uses correct operation name.

        Verifies:
            BenchmarkResult.operation is set to "service_initialization"
            for result identification and tracking.

        Business Impact:
            Consistent operation naming enables monitoring service
            initialization performance across deployments.

        Scenario:
            Given: A benchmark measuring AIServiceResilience initialization
            When: benchmark_service_initialization completes
            Then: BenchmarkResult.operation equals "service_initialization"
            And: Result can be tracked in performance monitoring

        Fixtures Used:
            - None required for operation name verification
        """
        # Arrange
        benchmark = ConfigurationPerformanceBenchmark()

        with patch.object(benchmark, 'measure_performance') as mock_measure:
            mock_measure.return_value = BenchmarkResult(
                operation="service_initialization",
                duration_ms=400.0,
                memory_peak_mb=12.0,
                iterations=25,
                avg_duration_ms=16.0,
                min_duration_ms=12.0,
                max_duration_ms=25.0,
                std_dev_ms=3.0,
                success_rate=1.0,
                metadata={}
            )

            # Act
            result = benchmark.benchmark_service_initialization()

            # Assert
            assert result.operation == "service_initialization"
            call_args = mock_measure.call_args
            assert call_args[0][0] == "service_initialization"


class TestBenchmarkCustomConfigLoading:
    """
    Tests for benchmark_custom_config_loading() method behavior.
    
    Scope:
        Verifies custom configuration loading performance measurement
        against <100ms CONFIG_LOADING threshold.
    
    Business Impact:
        Custom config loading speed impacts configuration flexibility.
        <100ms ensures users can apply custom configurations quickly.
    
    Test Strategy:
        - Test default iteration count (25)
        - Test BenchmarkResult structure
        - Test operation naming
    """

    def test_benchmark_custom_config_loading_executes_with_default_iterations(self):
        """
        Test that benchmark_custom_config_loading executes 25 iterations by default.

        Verifies:
            Default iterations parameter of 25 appropriate for custom
            configuration loading benchmarks.

        Business Impact:
            25 iterations provide statistical validity while keeping
            execution time reasonable for custom config scenarios.

        Scenario:
            Given: A benchmark measuring custom config loading
            When: benchmark_custom_config_loading is called without iterations
            Then: Benchmark executes 25 iterations
            And: BenchmarkResult.iterations equals 25

        Fixtures Used:
            - None required for iteration count verification
        """
        # Arrange
        benchmark = ConfigurationPerformanceBenchmark()

        with patch.object(benchmark, 'measure_performance') as mock_measure:
            mock_measure.return_value = BenchmarkResult(
                operation="custom_config_loading",
                duration_ms=400.0,
                memory_peak_mb=10.0,
                iterations=25,
                avg_duration_ms=16.0,
                min_duration_ms=12.0,
                max_duration_ms=22.0,
                std_dev_ms=2.5,
                success_rate=1.0,
                metadata={}
            )

            # Act
            result = benchmark.benchmark_custom_config_loading()

            # Assert
            mock_measure.assert_called_once()
            call_args = mock_measure.call_args
            assert call_args[0][0] == "custom_config_loading"
            assert call_args[0][2] == 25
            assert result.iterations == 25
            assert result.operation == "custom_config_loading"

    def test_benchmark_custom_config_loading_returns_benchmark_result(self):
        """
        Test that benchmark_custom_config_loading returns BenchmarkResult.

        Verifies:
            Return type is BenchmarkResult with custom configuration loading
            performance metrics.

        Business Impact:
            Structured results enable validation that custom config loading
            meets <100ms target for responsive configuration updates.

        Scenario:
            Given: A benchmark measuring custom config loading
            When: benchmark_custom_config_loading completes
            Then: Return value is a BenchmarkResult instance
            And: Result contains custom config loading metrics

        Fixtures Used:
            - None required for return type verification
        """
        # Arrange
        benchmark = ConfigurationPerformanceBenchmark()

        with patch.object(benchmark, 'measure_performance') as mock_measure:
            expected_result = BenchmarkResult(
                operation="custom_config_loading",
                duration_ms=350.0,
                memory_peak_mb=9.0,
                iterations=25,
                avg_duration_ms=14.0,
                min_duration_ms=10.0,
                max_duration_ms=20.0,
                std_dev_ms=2.2,
                success_rate=1.0,
                metadata={"custom_config_0_loaded": True}
            )
            mock_measure.return_value = expected_result

            # Act
            result = benchmark.benchmark_custom_config_loading()

            # Assert
            assert isinstance(result, BenchmarkResult)
            assert result.operation == "custom_config_loading"
            assert result.iterations == 25
            assert result.success_rate == 1.0

    def test_benchmark_custom_config_loading_sets_correct_operation_name(self):
        """
        Test that benchmark_custom_config_loading uses correct operation name.

        Verifies:
            BenchmarkResult.operation is set to "custom_config_loading"
            for result identification.

        Business Impact:
            Consistent naming enables tracking custom config loading
            performance separately from preset-based loading.

        Scenario:
            Given: A benchmark measuring custom configuration loading
            When: benchmark_custom_config_loading completes
            Then: BenchmarkResult.operation equals "custom_config_loading"
            And: Result can be distinguished from preset loading

        Fixtures Used:
            - None required for operation name verification
        """
        # Arrange
        benchmark = ConfigurationPerformanceBenchmark()

        with patch.object(benchmark, 'measure_performance') as mock_measure:
            mock_measure.return_value = BenchmarkResult(
                operation="custom_config_loading",
                duration_ms=300.0,
                memory_peak_mb=8.0,
                iterations=25,
                avg_duration_ms=12.0,
                min_duration_ms=8.0,
                max_duration_ms=18.0,
                std_dev_ms=2.0,
                success_rate=1.0,
                metadata={}
            )

            # Act
            result = benchmark.benchmark_custom_config_loading()

            # Assert
            assert result.operation == "custom_config_loading"
            call_args = mock_measure.call_args
            assert call_args[0][0] == "custom_config_loading"


class TestBenchmarkLegacyConfigLoading:
    """
    Tests for benchmark_legacy_config_loading() method behavior.
    
    Scope:
        Verifies legacy configuration loading performance measurement
        against <100ms CONFIG_LOADING threshold.
    
    Business Impact:
        Legacy config support ensures backward compatibility. <100ms target
        ensures migration path doesn't impact performance.
    
    Test Strategy:
        - Test default iteration count (25)
        - Test BenchmarkResult structure
        - Test operation naming
    """

    def test_benchmark_legacy_config_loading_executes_with_default_iterations(self):
        """
        Test that benchmark_legacy_config_loading executes 25 iterations by default.

        Verifies:
            Default iterations parameter of 25 appropriate for legacy
            configuration loading benchmarks.

        Business Impact:
            25 iterations sufficient to validate legacy config support
            meets performance targets for backward compatibility.

        Scenario:
            Given: A benchmark measuring legacy config loading
            When: benchmark_legacy_config_loading is called without iterations
            Then: Benchmark executes 25 iterations
            And: BenchmarkResult.iterations equals 25

        Fixtures Used:
            - None required for iteration count verification
        """
        # Arrange
        benchmark = ConfigurationPerformanceBenchmark()

        with patch.object(benchmark, 'measure_performance') as mock_measure:
            mock_measure.return_value = BenchmarkResult(
                operation="legacy_config_loading",
                duration_ms=450.0,
                memory_peak_mb=12.0,
                iterations=25,
                avg_duration_ms=18.0,
                min_duration_ms=14.0,
                max_duration_ms=25.0,
                std_dev_ms=3.0,
                success_rate=1.0,
                metadata={}
            )

            # Act
            result = benchmark.benchmark_legacy_config_loading()

            # Assert
            mock_measure.assert_called_once()
            call_args = mock_measure.call_args
            assert call_args[0][0] == "legacy_config_loading"
            assert call_args[0][2] == 25
            assert result.iterations == 25
            assert result.operation == "legacy_config_loading"

    def test_benchmark_legacy_config_loading_returns_benchmark_result(self):
        """
        Test that benchmark_legacy_config_loading returns BenchmarkResult.

        Verifies:
            Return type is BenchmarkResult with legacy configuration loading
            performance metrics.

        Business Impact:
            Structured results enable validation that legacy config support
            maintains <100ms performance target.

        Scenario:
            Given: A benchmark measuring legacy config loading
            When: benchmark_legacy_config_loading completes
            Then: Return value is a BenchmarkResult instance
            And: Result contains legacy config loading metrics

        Fixtures Used:
            - None required for return type verification
        """
        # Arrange
        benchmark = ConfigurationPerformanceBenchmark()

        with patch.object(benchmark, 'measure_performance') as mock_measure:
            expected_result = BenchmarkResult(
                operation="legacy_config_loading",
                duration_ms=400.0,
                memory_peak_mb=11.0,
                iterations=25,
                avg_duration_ms=16.0,
                min_duration_ms=12.0,
                max_duration_ms=23.0,
                std_dev_ms=2.8,
                success_rate=1.0,
                metadata={"legacy_config_0_loaded": True}
            )
            mock_measure.return_value = expected_result

            # Act
            result = benchmark.benchmark_legacy_config_loading()

            # Assert
            assert isinstance(result, BenchmarkResult)
            assert result.operation == "legacy_config_loading"
            assert result.iterations == 25
            assert result.success_rate == 1.0

    def test_benchmark_legacy_config_loading_sets_correct_operation_name(self):
        """
        Test that benchmark_legacy_config_loading uses correct operation name.

        Verifies:
            BenchmarkResult.operation is set to "legacy_config_loading"
            for result identification and tracking.

        Business Impact:
            Consistent naming enables monitoring legacy config performance
            to ensure backward compatibility doesn't degrade over time.

        Scenario:
            Given: A benchmark measuring legacy configuration loading
            When: benchmark_legacy_config_loading completes
            Then: BenchmarkResult.operation equals "legacy_config_loading"
            And: Result can be tracked for backward compatibility validation

        Fixtures Used:
            - None required for operation name verification
        """
        # Arrange
        benchmark = ConfigurationPerformanceBenchmark()

        with patch.object(benchmark, 'measure_performance') as mock_measure:
            mock_measure.return_value = BenchmarkResult(
                operation="legacy_config_loading",
                duration_ms=350.0,
                memory_peak_mb=10.0,
                iterations=25,
                avg_duration_ms=14.0,
                min_duration_ms=10.0,
                max_duration_ms=20.0,
                std_dev_ms=2.5,
                success_rate=1.0,
                metadata={}
            )

            # Act
            result = benchmark.benchmark_legacy_config_loading()

            # Assert
            assert result.operation == "legacy_config_loading"
            call_args = mock_measure.call_args
            assert call_args[0][0] == "legacy_config_loading"


class TestBenchmarkValidationPerformance:
    """
    Tests for benchmark_validation_performance() method behavior.
    
    Scope:
        Verifies configuration validation performance measurement against
        <50ms VALIDATION threshold.
    
    Business Impact:
        Validation speed impacts configuration change responsiveness.
        <50ms ensures fast validation feedback for configuration updates.
    
    Test Strategy:
        - Test default iteration count (50)
        - Test BenchmarkResult structure
        - Test operation naming
        - Test validation measurement
    """

    def test_benchmark_validation_performance_executes_with_default_iterations(self):
        """
        Test that benchmark_validation_performance executes 50 iterations by default.

        Verifies:
            Default iterations parameter of 50 provides sufficient statistical
            significance for validation performance benchmarks.

        Business Impact:
            50 iterations balance statistical validity with reasonable
            execution time for validation benchmarks.

        Scenario:
            Given: A benchmark measuring validation performance
            When: benchmark_validation_performance is called without iterations
            Then: Benchmark executes 50 iterations
            And: BenchmarkResult.iterations equals 50

        Fixtures Used:
            - None required for iteration count verification
        """
        # Arrange
        benchmark = ConfigurationPerformanceBenchmark()

        with patch.object(benchmark, 'measure_performance') as mock_measure:
            mock_measure.return_value = BenchmarkResult(
                operation="validation_performance",
                duration_ms=250.0,
                memory_peak_mb=6.0,
                iterations=50,
                avg_duration_ms=5.0,
                min_duration_ms=3.0,
                max_duration_ms=8.0,
                std_dev_ms=1.2,
                success_rate=1.0,
                metadata={}
            )

            # Act
            result = benchmark.benchmark_validation_performance()

            # Assert
            mock_measure.assert_called_once()
            call_args = mock_measure.call_args
            assert call_args[0][0] == "validation_performance"
            assert call_args[0][2] == 50
            assert result.iterations == 50
            assert result.operation == "validation_performance"

    def test_benchmark_validation_performance_returns_benchmark_result(self):
        """
        Test that benchmark_validation_performance returns BenchmarkResult.

        Verifies:
            Return type is BenchmarkResult with configuration validation
            performance metrics.

        Business Impact:
            Structured results enable validation that config validation
            meets <50ms target for responsive validation feedback.

        Scenario:
            Given: A benchmark measuring validation performance
            When: benchmark_validation_performance completes
            Then: Return value is a BenchmarkResult instance
            And: Result contains validation performance metrics

        Fixtures Used:
            - None required for return type verification
        """
        # Arrange
        benchmark = ConfigurationPerformanceBenchmark()

        with patch.object(benchmark, 'measure_performance') as mock_measure:
            expected_result = BenchmarkResult(
                operation="validation_performance",
                duration_ms=200.0,
                memory_peak_mb=5.0,
                iterations=50,
                avg_duration_ms=4.0,
                min_duration_ms=2.0,
                max_duration_ms=7.0,
                std_dev_ms=1.0,
                success_rate=1.0,
                metadata={"config_0_valid": True, "config_0_errors": 0}
            )
            mock_measure.return_value = expected_result

            # Act
            result = benchmark.benchmark_validation_performance()

            # Assert
            assert isinstance(result, BenchmarkResult)
            assert result.operation == "validation_performance"
            assert result.iterations == 50
            assert result.success_rate == 1.0

    def test_benchmark_validation_performance_sets_correct_operation_name(self):
        """
        Test that benchmark_validation_performance uses correct operation name.

        Verifies:
            BenchmarkResult.operation is set to "validation_performance"
            for result identification and filtering.

        Business Impact:
            Consistent naming enables tracking validation performance
            to ensure configuration changes validate quickly.

        Scenario:
            Given: A benchmark measuring configuration validation
            When: benchmark_validation_performance completes
            Then: BenchmarkResult.operation equals "validation_performance"
            And: Result can be filtered in validation performance analysis

        Fixtures Used:
            - None required for operation name verification
        """
        # Arrange
        benchmark = ConfigurationPerformanceBenchmark()

        with patch.object(benchmark, 'measure_performance') as mock_measure:
            mock_measure.return_value = BenchmarkResult(
                operation="validation_performance",
                duration_ms=180.0,
                memory_peak_mb=4.5,
                iterations=50,
                avg_duration_ms=3.6,
                min_duration_ms=2.5,
                max_duration_ms=6.5,
                std_dev_ms=0.9,
                success_rate=1.0,
                metadata={}
            )

            # Act
            result = benchmark.benchmark_validation_performance()

            # Assert
            assert result.operation == "validation_performance"
            call_args = mock_measure.call_args
            assert call_args[0][0] == "validation_performance"

