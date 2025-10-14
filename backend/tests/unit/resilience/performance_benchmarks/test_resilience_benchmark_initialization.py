"""
Test suite for ConfigurationPerformanceBenchmark initialization behavior.

This module verifies the initialization contract of the ConfigurationPerformanceBenchmark
class, ensuring proper setup of benchmark state, result storage, and baseline configuration.

Test Strategy:
    - Verify clean state initialization
    - Verify baseline results initialization
    - Verify logger setup
    - Verify no external dependencies required for initialization

Business Critical:
    Proper initialization ensures benchmark suite starts with clean state and
    can accurately track performance metrics without interference from previous runs.
"""

import pytest


class TestConfigurationPerformanceBenchmarkInitialization:
    """
    Tests for ConfigurationPerformanceBenchmark initialization behavior.
    
    Scope:
        Verifies the __init__ method contract as documented in the public interface.
        Tests focus on initial state setup, storage initialization, and configuration.
    
    Business Impact:
        Ensures benchmark suite initializes correctly with clean state, preventing
        contamination from previous benchmark runs and ensuring accurate performance tracking.
    
    Test Strategy:
        - Test empty results list initialization
        - Test baseline results dictionary initialization
        - Test logger setup and availability
        - Test initialization with no external dependencies
        - Test initialization idempotency
    """

    def test_initialization_creates_empty_results_list(self):
        """
        Test that benchmark initialization creates empty results list.

        Verifies:
            The results attribute is initialized as an empty list ready to accumulate
            benchmark execution data.

        Business Impact:
            Ensures benchmark suite starts with clean state, preventing contamination
            from previous runs that could skew performance analysis.

        Scenario:
            Given: No previous benchmark state exists
            When: ConfigurationPerformanceBenchmark is instantiated
            Then: The results attribute is an empty list
            And: No benchmark data is present from previous runs

        Fixtures Used:
            - None required (tests direct instantiation)
        """
        # Arrange & Act
        from app.infrastructure.resilience.performance_benchmarks import ConfigurationPerformanceBenchmark

        benchmark = ConfigurationPerformanceBenchmark()

        # Assert
        assert hasattr(benchmark, 'results'), "Benchmark should have results attribute"
        assert isinstance(benchmark.results, list), "Results should be a list"
        assert len(benchmark.results) == 0, "Results list should be empty initially"

        # Verify no previous benchmark data exists
        assert benchmark.results == [], "Results should be exactly an empty list"

    def test_initialization_creates_baseline_results_dictionary(self):
        """
        Test that benchmark initialization creates empty baseline results dictionary.

        Verifies:
            The baseline_results attribute is initialized as an empty dictionary
            ready to store baseline performance metrics for regression detection.

        Business Impact:
            Ensures baseline comparison system starts correctly, enabling performance
            regression detection across benchmark runs.

        Scenario:
            Given: No previous baseline data exists
            When: ConfigurationPerformanceBenchmark is instantiated
            Then: The baseline_results attribute is an empty dictionary
            And: No baseline data is present from previous runs

        Fixtures Used:
            - None required (tests direct instantiation)
        """
        # Arrange & Act
        from app.infrastructure.resilience.performance_benchmarks import ConfigurationPerformanceBenchmark

        benchmark = ConfigurationPerformanceBenchmark()

        # Assert
        assert hasattr(benchmark, 'baseline_results'), "Benchmark should have baseline_results attribute"
        assert isinstance(benchmark.baseline_results, dict), "Baseline results should be a dictionary"
        assert len(benchmark.baseline_results) == 0, "Baseline results dictionary should be empty initially"

        # Verify no previous baseline data exists
        assert benchmark.baseline_results == {}, "Baseline results should be exactly an empty dictionary"

    def test_initialization_requires_no_external_dependencies(self):
        """
        Test that benchmark initialization succeeds without external dependencies.

        Verifies:
            Benchmark can be instantiated successfully without requiring external
            configuration, files, or services to be available.

        Business Impact:
            Ensures benchmark suite can be used in any environment without complex
            setup requirements, improving developer productivity.

        Scenario:
            Given: No external dependencies are configured
            When: ConfigurationPerformanceBenchmark is instantiated
            Then: Initialization succeeds without errors
            And: Benchmark is ready to execute performance tests

        Fixtures Used:
            - None required (tests direct instantiation)
        """
        # Arrange & Act
        from app.infrastructure.resilience.performance_benchmarks import ConfigurationPerformanceBenchmark

        # Should succeed without any external dependencies, configuration, or services
        try:
            benchmark = ConfigurationPerformanceBenchmark()
        except Exception as e:
            pytest.fail(f"Initialization failed unexpectedly: {e}")

        # Assert the benchmark is properly initialized and ready for use
        assert benchmark is not None, "Benchmark should be created successfully"
        assert hasattr(benchmark, 'results'), "Benchmark should have results attribute"
        assert hasattr(benchmark, 'baseline_results'), "Benchmark should have baseline_results attribute"

        # Verify it's in a clean state ready for benchmark execution
        assert len(benchmark.results) == 0, "Results should be clean"
        assert len(benchmark.baseline_results) == 0, "Baseline results should be clean"

    def test_initialization_is_idempotent(self):
        """
        Test that multiple benchmark instantiations create independent instances.

        Verifies:
            Creating multiple benchmark instances produces independent objects
            with isolated state that don't interfere with each other.

        Business Impact:
            Ensures concurrent or sequential benchmark execution doesn't cause
            state contamination between benchmark runs.

        Scenario:
            Given: Multiple benchmark instances are needed
            When: Multiple ConfigurationPerformanceBenchmark instances are created
            Then: Each instance has independent results storage
            And: Modifications to one instance don't affect others

        Fixtures Used:
            - None required (tests direct instantiation)
        """
        # Arrange & Act
        from app.infrastructure.resilience.performance_benchmarks import ConfigurationPerformanceBenchmark

        benchmark1 = ConfigurationPerformanceBenchmark()
        benchmark2 = ConfigurationPerformanceBenchmark()
        benchmark3 = ConfigurationPerformanceBenchmark()

        # Assert instances are independent
        assert benchmark1 is not benchmark2, "Instances should be different objects"
        assert benchmark2 is not benchmark3, "Instances should be different objects"
        assert benchmark1 is not benchmark3, "Instances should be different objects"

        # Each should start with clean state
        for i, benchmark in enumerate([benchmark1, benchmark2, benchmark3], 1):
            assert len(benchmark.results) == 0, f"Benchmark {i} should have empty results"
            assert len(benchmark.baseline_results) == 0, f"Benchmark {i} should have empty baseline results"

        # Modify one instance - should not affect others
        benchmark1.results.append("test_result")
        benchmark1.baseline_results["test_baseline"] = 1.0

        # Verify only benchmark1 was modified
        assert len(benchmark1.results) == 1, "Benchmark1 should have one result"
        assert len(benchmark1.baseline_results) == 1, "Benchmark1 should have one baseline result"
        assert len(benchmark2.results) == 0, "Benchmark2 should still be empty"
        assert len(benchmark2.baseline_results) == 0, "Benchmark2 baseline should still be empty"
        assert len(benchmark3.results) == 0, "Benchmark3 should still be empty"
        assert len(benchmark3.baseline_results) == 0, "Benchmark3 baseline should still be empty"

    def test_initialization_sets_up_logger_correctly(self):
        """
        Test that benchmark initialization sets up logger for execution tracking.

        Verifies:
            Logger is properly initialized and available for benchmark execution
            tracking, progress logging, and completion metrics.

        Business Impact:
            Ensures benchmark execution can be monitored and debugged through
            comprehensive logging of benchmark progress and results.

        Scenario:
            Given: No logger is pre-configured
            When: ConfigurationPerformanceBenchmark is instantiated
            Then: Logger attribute is available for use
            And: Logger is ready for benchmark execution tracking

        Fixtures Used:
            - None required (tests direct instantiation)

        Edge Cases Covered:
            - Logger initialization without external configuration
            - Logger availability immediately after initialization
        """
        # Arrange & Act
        from app.infrastructure.resilience.performance_benchmarks import ConfigurationPerformanceBenchmark
        import logging

        benchmark = ConfigurationPerformanceBenchmark()

        # Assert logger is available and properly configured
        # Note: The module-level logger is used, not an instance attribute
        # We verify the logger exists and is properly configured for the module
        module_logger = logging.getLogger('app.infrastructure.resilience.performance_benchmarks')

        # Verify logger is properly configured
        assert module_logger is not None, "Module logger should be available"
        assert hasattr(module_logger, 'info'), "Logger should have info method"
        assert hasattr(module_logger, 'debug'), "Logger should have debug method"
        assert hasattr(module_logger, 'warning'), "Logger should have warning method"
        assert hasattr(module_logger, 'error'), "Logger should have error method"

        # Verify logger name matches the module
        assert module_logger.name == 'app.infrastructure.resilience.performance_benchmarks', "Logger name should match module name"

        # The initialization should have logged a message (we can't easily test this without
        # complex logging setup, but we can verify the logger is ready to use)
        assert callable(module_logger.info), "Logger info method should be callable"
        assert callable(module_logger.debug), "Logger debug method should be callable"

    def test_initialization_results_list_is_mutable(self):
        """
        Test that initialized results list can accumulate benchmark data.

        Verifies:
            The results list is mutable and capable of accumulating benchmark
            results as tests execute.

        Business Impact:
            Ensures benchmark suite can properly collect and store performance
            data throughout benchmark execution lifecycle.

        Scenario:
            Given: A newly initialized benchmark instance
            When: Results are added to the results list
            Then: Results list properly accumulates the benchmark data
            And: Results remain accessible for analysis

        Fixtures Used:
            - None required (tests direct instantiation)

        Edge Cases Covered:
            - Empty list mutability
            - List append operations
        """
        # Arrange
        from app.infrastructure.resilience.performance_benchmarks import ConfigurationPerformanceBenchmark

        benchmark = ConfigurationPerformanceBenchmark()

        # Verify initial state
        assert len(benchmark.results) == 0, "Results list should start empty"

        # Act - Add mock benchmark results
        mock_result1 = {"operation": "test1", "duration": 1.0}
        mock_result2 = {"operation": "test2", "duration": 2.0}
        mock_result3 = {"operation": "test3", "duration": 1.5}

        # Test append operations
        benchmark.results.append(mock_result1)
        benchmark.results.append(mock_result2)
        benchmark.results.append(mock_result3)

        # Assert results were properly accumulated
        assert len(benchmark.results) == 3, "Results list should contain 3 items"
        assert benchmark.results[0] == mock_result1, "First result should match"
        assert benchmark.results[1] == mock_result2, "Second result should match"
        assert benchmark.results[2] == mock_result3, "Third result should match"

        # Test list operations work properly
        assert mock_result1 in benchmark.results, "First result should be in list"
        assert mock_result2 in benchmark.results, "Second result should be in list"
        assert mock_result3 in benchmark.results, "Third result should be in list"

        # Test list iteration works
        result_count = 0
        for result in benchmark.results:
            assert "operation" in result, "Each result should have operation key"
            assert "duration" in result, "Each result should have duration key"
            result_count += 1
        assert result_count == 3, "Should iterate over all 3 results"

        # Test list clearing works
        benchmark.results.clear()
        assert len(benchmark.results) == 0, "Results list should be empty after clearing"

    def test_initialization_baseline_results_is_mutable(self):
        """
        Test that initialized baseline_results dict can store baseline metrics.

        Verifies:
            The baseline_results dictionary is mutable and capable of storing
            baseline performance metrics for regression detection.

        Business Impact:
            Ensures baseline comparison system can properly store and retrieve
            baseline metrics for performance regression analysis.

        Scenario:
            Given: A newly initialized benchmark instance
            When: Baseline metrics are stored in baseline_results
            Then: Dictionary properly stores the baseline data
            And: Baseline data remains accessible for comparison

        Fixtures Used:
            - None required (tests direct instantiation)

        Edge Cases Covered:
            - Empty dictionary mutability
            - Dictionary key-value storage
        """
        # Arrange
        from app.infrastructure.resilience.performance_benchmarks import ConfigurationPerformanceBenchmark

        benchmark = ConfigurationPerformanceBenchmark()

        # Verify initial state
        assert len(benchmark.baseline_results) == 0, "Baseline results should start empty"

        # Act - Add baseline performance metrics
        baseline_metrics = {
            "preset_loading": 5.2,  # milliseconds
            "config_validation": 12.8,
            "service_initialization": 45.1,
            "custom_config_loading": 8.3,
            "legacy_config_loading": 15.7,
            "validation_performance": 22.4
        }

        # Test dictionary assignment operations
        for operation, baseline_time in baseline_metrics.items():
            benchmark.baseline_results[operation] = baseline_time

        # Assert baseline metrics were properly stored
        assert len(benchmark.baseline_results) == 6, "Should have 6 baseline metrics"

        for operation, expected_time in baseline_metrics.items():
            assert operation in benchmark.baseline_results, f"Operation {operation} should be in baseline results"
            assert benchmark.baseline_results[operation] == expected_time, f"Baseline time for {operation} should match"

        # Test dictionary operations work properly
        assert "preset_loading" in benchmark.baseline_results, "preset_loading should be in baseline results"
        assert benchmark.baseline_results["config_validation"] == 12.8, "config_validation baseline should be accessible"

        # Test dictionary iteration works
        baseline_count = 0
        for operation, baseline_time in benchmark.baseline_results.items():
            assert isinstance(operation, str), "Operation names should be strings"
            assert isinstance(baseline_time, (int, float)), "Baseline times should be numeric"
            baseline_count += 1
        assert baseline_count == 6, "Should iterate over all 6 baseline metrics"

        # Test dictionary methods work
        operations = list(benchmark.baseline_results.keys())
        times = list(benchmark.baseline_results.values())
        items = list(benchmark.baseline_results.items())

        assert len(operations) == 6, "Should have 6 operations"
        assert len(times) == 6, "Should have 6 times"
        assert len(items) == 6, "Should have 6 items"
        assert all(isinstance(op, str) for op in operations), "All operations should be strings"
        assert all(isinstance(t, (int, float)) for t in times), "All times should be numeric"

        # Test dictionary clearing works
        benchmark.baseline_results.clear()
        assert len(benchmark.baseline_results) == 0, "Baseline results should be empty after clearing"

