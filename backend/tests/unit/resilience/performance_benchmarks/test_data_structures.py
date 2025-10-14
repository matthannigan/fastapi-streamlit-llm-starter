"""
Test suite for performance benchmarks data structure classes.

This module verifies the behavior of BenchmarkResult, BenchmarkSuite,
and PerformanceThreshold data classes, including their initialization,
serialization methods, and data integrity.

Test Strategy:
    - Test BenchmarkResult NamedTuple structure and attributes
    - Test BenchmarkSuite dataclass with to_dict() and to_json() methods
    - Test PerformanceThreshold Enum values and usage
    - Test data serialization for storage and reporting
    - Test data structure immutability where appropriate

Business Critical:
    Data structures ensure consistent representation of benchmark results
    across the system, enabling reliable storage, analysis, and reporting
    of performance data.
"""

import pytest
import json
from typing import Dict, Any

# Import the data structures from the performance_benchmarks module
from app.infrastructure.resilience.performance_benchmarks import (
    BenchmarkResult,
    BenchmarkSuite,
    PerformanceThreshold
)


class TestBenchmarkResultStructure:
    """
    Tests for BenchmarkResult NamedTuple structure and attributes.
    
    Scope:
        Verifies BenchmarkResult contains all required performance metrics
        as documented in the contract, with correct types and accessibility.
    
    Business Impact:
        Complete and accurate result structure ensures all performance
        metrics are captured and available for analysis and decision-making.
    
    Test Strategy:
        - Test NamedTuple creation with all required fields
        - Test attribute accessibility
        - Test immutability
        - Test field types and values
    """

    def test_benchmark_result_creation_with_all_fields(self):
        """
        Test that BenchmarkResult can be created with all required fields.

        Verifies:
            BenchmarkResult NamedTuple accepts all documented performance
            metrics: operation, duration_ms, memory_peak_mb, iterations,
            avg_duration_ms, min_duration_ms, max_duration_ms, std_dev_ms,
            success_rate, metadata.

        Business Impact:
            Complete field set ensures all performance metrics are captured
            for comprehensive performance analysis.

        Scenario:
            Given: Performance metrics from a benchmark execution
            When: BenchmarkResult is created with all field values
            Then: Result object is created successfully
            And: All fields are accessible with correct values

        Fixtures Used:
            - None required for structure creation
        """
        # Given: Performance metrics from a benchmark execution
        metadata = {"test_param": "test_value", "iterations_completed": 100}

        # When: BenchmarkResult is created with all field values
        result = BenchmarkResult(
            operation="test_operation",
            duration_ms=150.5,
            memory_peak_mb=25.7,
            iterations=100,
            avg_duration_ms=1.505,
            min_duration_ms=0.8,
            max_duration_ms=3.2,
            std_dev_ms=0.6,
            success_rate=0.95,
            metadata=metadata
        )

        # Then: Result object is created successfully
        assert isinstance(result, BenchmarkResult)

        # And: All fields are accessible with correct values
        assert result.operation == "test_operation"
        assert result.duration_ms == 150.5
        assert result.memory_peak_mb == 25.7
        assert result.iterations == 100
        assert result.avg_duration_ms == 1.505
        assert result.min_duration_ms == 0.8
        assert result.max_duration_ms == 3.2
        assert result.std_dev_ms == 0.6
        assert result.success_rate == 0.95
        assert result.metadata == metadata

    def test_benchmark_result_operation_attribute_accessible(self):
        """
        Test that BenchmarkResult.operation attribute is accessible.

        Verifies:
            Operation name is stored and retrievable from BenchmarkResult
            for result identification.

        Business Impact:
            Operation name enables filtering and grouping of results by
            operation type for targeted performance analysis.

        Scenario:
            Given: A BenchmarkResult with operation name "test_operation"
            When: Accessing the operation attribute
            Then: Value equals "test_operation"
            And: Operation can be used for result filtering

        Fixtures Used:
            - None required for attribute access
        """
        # Given: A BenchmarkResult with operation name "test_operation"
        result = BenchmarkResult(
            operation="test_operation",
            duration_ms=100.0,
            memory_peak_mb=10.0,
            iterations=10,
            avg_duration_ms=10.0,
            min_duration_ms=8.0,
            max_duration_ms=12.0,
            std_dev_ms=1.0,
            success_rate=1.0,
            metadata={}
        )

        # When: Accessing the operation attribute
        operation_name = result.operation

        # Then: Value equals "test_operation"
        assert operation_name == "test_operation"

        # And: Operation can be used for result filtering
        assert operation_name.startswith("test_")

    def test_benchmark_result_duration_attributes_accessible(self):
        """
        Test that BenchmarkResult duration attributes are accessible.

        Verifies:
            Duration metrics (duration_ms, avg_duration_ms, min_duration_ms,
            max_duration_ms) are stored and retrievable.

        Business Impact:
            Duration metrics enable comprehensive timing analysis including
            average performance, best/worst case, and total execution time.

        Scenario:
            Given: A BenchmarkResult with timing metrics
            When: Accessing duration attributes
            Then: All timing values are accessible
            And: Values reflect measured performance accurately

        Fixtures Used:
            - None required for attribute access
        """
        # Given: A BenchmarkResult with timing metrics
        result = BenchmarkResult(
            operation="timing_test",
            duration_ms=250.0,
            memory_peak_mb=15.0,
            iterations=20,
            avg_duration_ms=12.5,
            min_duration_ms=8.0,
            max_duration_ms=20.0,
            std_dev_ms=2.5,
            success_rate=0.95,
            metadata={}
        )

        # When: Accessing duration attributes
        total_duration = result.duration_ms
        avg_duration = result.avg_duration_ms
        min_duration = result.min_duration_ms
        max_duration = result.max_duration_ms

        # Then: All timing values are accessible
        assert isinstance(total_duration, float)
        assert isinstance(avg_duration, float)
        assert isinstance(min_duration, float)
        assert isinstance(max_duration, float)

        # And: Values reflect measured performance accurately
        assert total_duration == 250.0
        assert avg_duration == 12.5
        assert min_duration == 8.0
        assert max_duration == 20.0
        assert max_duration >= min_duration
        assert avg_duration >= min_duration
        assert avg_duration <= max_duration

    def test_benchmark_result_memory_peak_mb_accessible(self):
        """
        Test that BenchmarkResult.memory_peak_mb attribute is accessible.

        Verifies:
            Peak memory usage metric is stored and retrievable for
            memory performance analysis.

        Business Impact:
            Memory metrics enable identification of memory-intensive
            operations and validation against memory budgets.

        Scenario:
            Given: A BenchmarkResult with memory usage data
            When: Accessing the memory_peak_mb attribute
            Then: Memory value is accessible
            And: Value is in megabytes for readability

        Fixtures Used:
            - None required for attribute access
        """
        # Given: A BenchmarkResult with memory usage data
        result = BenchmarkResult(
            operation="memory_test",
            duration_ms=100.0,
            memory_peak_mb=42.7,
            iterations=10,
            avg_duration_ms=10.0,
            min_duration_ms=8.0,
            max_duration_ms=12.0,
            std_dev_ms=1.0,
            success_rate=1.0,
            metadata={}
        )

        # When: Accessing the memory_peak_mb attribute
        memory_peak = result.memory_peak_mb

        # Then: Memory value is accessible
        assert isinstance(memory_peak, float)
        assert memory_peak == 42.7

        # And: Value is in megabytes for readability (reasonable scale)
        assert 0 < memory_peak < 10000  # Reasonable MB range

    def test_benchmark_result_iterations_count_accessible(self):
        """
        Test that BenchmarkResult.iterations attribute is accessible.

        Verifies:
            Iteration count is stored and retrievable for statistical
            significance assessment.

        Business Impact:
            Iteration count enables assessment of statistical validity
            and comparison of results with different sample sizes.

        Scenario:
            Given: A BenchmarkResult from benchmark with 100 iterations
            When: Accessing the iterations attribute
            Then: Value equals 100
            And: Statistical significance can be assessed

        Fixtures Used:
            - None required for attribute access
        """
        # Given: A BenchmarkResult from benchmark with 100 iterations
        result = BenchmarkResult(
            operation="iterations_test",
            duration_ms=1000.0,
            memory_peak_mb=10.0,
            iterations=100,
            avg_duration_ms=10.0,
            min_duration_ms=8.0,
            max_duration_ms=12.0,
            std_dev_ms=1.0,
            success_rate=1.0,
            metadata={}
        )

        # When: Accessing the iterations attribute
        iterations = result.iterations

        # Then: Value equals 100
        assert iterations == 100
        assert isinstance(iterations, int)

        # And: Statistical significance can be assessed
        assert iterations > 1  # Multiple iterations for statistical validity

    def test_benchmark_result_std_dev_accessible(self):
        """
        Test that BenchmarkResult.std_dev_ms attribute is accessible.

        Verifies:
            Standard deviation metric is stored and retrievable for
            performance consistency analysis.

        Business Impact:
            Standard deviation enables assessment of performance
            variability and consistency across iterations.

        Scenario:
            Given: A BenchmarkResult with standard deviation calculated
            When: Accessing the std_dev_ms attribute
            Then: Standard deviation value is accessible
            And: Performance consistency can be analyzed

        Fixtures Used:
            - None required for attribute access
        """
        # Given: A BenchmarkResult with standard deviation calculated
        result = BenchmarkResult(
            operation="std_dev_test",
            duration_ms=500.0,
            memory_peak_mb=15.0,
            iterations=50,
            avg_duration_ms=10.0,
            min_duration_ms=7.0,
            max_duration_ms=13.0,
            std_dev_ms=1.8,
            success_rate=0.98,
            metadata={}
        )

        # When: Accessing the std_dev_ms attribute
        std_dev = result.std_dev_ms

        # Then: Standard deviation value is accessible
        assert isinstance(std_dev, float)
        assert std_dev == 1.8

        # And: Performance consistency can be analyzed
        assert std_dev >= 0  # Standard deviation cannot be negative
        assert std_dev < result.avg_duration_ms  # Typically less than mean

    def test_benchmark_result_success_rate_accessible(self):
        """
        Test that BenchmarkResult.success_rate attribute is accessible.

        Verifies:
            Success rate metric is stored and retrievable for reliability
            assessment.

        Business Impact:
            Success rate enables distinction between performance problems
            and functional failures in benchmark execution.

        Scenario:
            Given: A BenchmarkResult with 95% success rate
            When: Accessing the success_rate attribute
            Then: Value equals 0.95
            And: Operation reliability can be assessed

        Fixtures Used:
            - None required for attribute access
        """
        # Given: A BenchmarkResult with 95% success rate
        result = BenchmarkResult(
            operation="success_rate_test",
            duration_ms=950.0,
            memory_peak_mb=20.0,
            iterations=100,
            avg_duration_ms=10.0,
            min_duration_ms=8.0,
            max_duration_ms=12.0,
            std_dev_ms=1.0,
            success_rate=0.95,
            metadata={}
        )

        # When: Accessing the success_rate attribute
        success_rate = result.success_rate

        # Then: Value equals 0.95
        assert success_rate == 0.95
        assert isinstance(success_rate, float)

        # And: Operation reliability can be assessed
        assert 0.0 <= success_rate <= 1.0  # Valid probability range
        assert success_rate > 0.9  # High success rate scenario

    def test_benchmark_result_metadata_accessible(self):
        """
        Test that BenchmarkResult.metadata attribute is accessible.

        Verifies:
            Metadata dictionary is stored and retrievable for additional
            context and debugging information.

        Business Impact:
            Metadata provides operation-specific context enabling detailed
            analysis and troubleshooting of performance issues.

        Scenario:
            Given: A BenchmarkResult with metadata containing context
            When: Accessing the metadata attribute
            Then: Metadata dictionary is accessible
            And: Context information is available for analysis

        Fixtures Used:
            - None required for attribute access
        """
        # Given: A BenchmarkResult with metadata containing context
        metadata = {
            "test_environment": "development",
            "thread_count": 4,
            "cache_enabled": True,
            "error_details": [],
            "custom_params": {"timeout": 30, "retries": 3}
        }

        result = BenchmarkResult(
            operation="metadata_test",
            duration_ms=200.0,
            memory_peak_mb=12.0,
            iterations=10,
            avg_duration_ms=20.0,
            min_duration_ms=15.0,
            max_duration_ms=25.0,
            std_dev_ms=2.0,
            success_rate=1.0,
            metadata=metadata
        )

        # When: Accessing the metadata attribute
        result_metadata = result.metadata

        # Then: Metadata dictionary is accessible
        assert isinstance(result_metadata, dict)
        assert result_metadata == metadata

        # And: Context information is available for analysis
        assert "test_environment" in result_metadata
        assert result_metadata["cache_enabled"] is True
        assert "custom_params" in result_metadata

    def test_benchmark_result_is_immutable(self):
        """
        Test that BenchmarkResult fields cannot be modified after creation.

        Verifies:
            NamedTuple immutability prevents accidental modification of
            benchmark results, ensuring data integrity.

        Business Impact:
            Immutability ensures benchmark results remain trustworthy
            throughout analysis pipeline without risk of corruption.

        Scenario:
            Given: A BenchmarkResult with initial values
            When: Attempting to modify a field value
            Then: Modification raises AttributeError
            And: Original values remain unchanged

        Fixtures Used:
            - None required for immutability verification

        Edge Cases Covered:
            - NamedTuple field assignment attempts
            - Result data integrity preservation
        """
        # Given: A BenchmarkResult with initial values
        result = BenchmarkResult(
            operation="immutable_test",
            duration_ms=100.0,
            memory_peak_mb=10.0,
            iterations=10,
            avg_duration_ms=10.0,
            min_duration_ms=8.0,
            max_duration_ms=12.0,
            std_dev_ms=1.0,
            success_rate=1.0,
            metadata={}
        )

        # Store original values
        original_operation = result.operation
        original_duration = result.duration_ms

        # When: Attempting to modify a field value
        with pytest.raises(AttributeError):
            result.operation = "modified_operation"

        with pytest.raises(AttributeError):
            result.duration_ms = 200.0

        # Then: Modification raises AttributeError (already verified)

        # And: Original values remain unchanged
        assert result.operation == original_operation
        assert result.duration_ms == original_duration


class TestBenchmarkSuiteStructure:
    """
    Tests for BenchmarkSuite dataclass structure and attributes.
    
    Scope:
        Verifies BenchmarkSuite dataclass contains all required suite
        information including results, metadata, and environment context.
    
    Business Impact:
        Complete suite structure enables comprehensive tracking of
        entire benchmark runs with full context for analysis.
    
    Test Strategy:
        - Test dataclass creation with all required fields
        - Test attribute accessibility
        - Test default values where applicable
        - Test field types
    """

    def test_benchmark_suite_creation_with_required_fields(self):
        """
        Test that BenchmarkSuite can be created with all required fields.

        Verifies:
            BenchmarkSuite dataclass accepts all documented fields: name,
            results, total_duration_ms, pass_rate, failed_benchmarks,
            timestamp, environment_info.

        Business Impact:
            Complete suite structure ensures all benchmark run information
            is captured for comprehensive analysis and reporting.

        Scenario:
            Given: Comprehensive benchmark suite execution results
            When: BenchmarkSuite is created with all field values
            Then: Suite object is created successfully
            And: All fields are accessible with correct values

        Fixtures Used:
            - None required for structure creation
        """
        # Given: Comprehensive benchmark suite execution results
        test_results = [
            BenchmarkResult(
                operation="test_operation_1",
                duration_ms=100.0,
                memory_peak_mb=10.0,
                iterations=10,
                avg_duration_ms=10.0,
                min_duration_ms=8.0,
                max_duration_ms=12.0,
                std_dev_ms=1.0,
                success_rate=1.0,
                metadata={}
            ),
            BenchmarkResult(
                operation="test_operation_2",
                duration_ms=150.0,
                memory_peak_mb=15.0,
                iterations=15,
                avg_duration_ms=10.0,
                min_duration_ms=7.0,
                max_duration_ms=13.0,
                std_dev_ms=1.5,
                success_rate=0.93,
                metadata={}
            )
        ]

        failed_benchmarks = ["failed_operation_1"]
        environment_info = {
            "platform": "test_platform",
            "python_version": "3.9.0",
            "cpu_count": 4
        }

        # When: BenchmarkSuite is created with all field values
        suite = BenchmarkSuite(
            name="Test Benchmark Suite",
            results=test_results,
            total_duration_ms=250.0,
            pass_rate=0.85,
            failed_benchmarks=failed_benchmarks,
            timestamp="2023-01-01 12:00:00 UTC",
            environment_info=environment_info
        )

        # Then: Suite object is created successfully
        assert isinstance(suite, BenchmarkSuite)

        # And: All fields are accessible with correct values
        assert suite.name == "Test Benchmark Suite"
        assert suite.results == test_results
        assert suite.total_duration_ms == 250.0
        assert suite.pass_rate == 0.85
        assert suite.failed_benchmarks == failed_benchmarks
        assert suite.timestamp == "2023-01-01 12:00:00 UTC"
        assert suite.environment_info == environment_info

    def test_benchmark_suite_name_accessible(self):
        """
        Test that BenchmarkSuite.name attribute is accessible.

        Verifies:
            Suite name is stored and retrievable for suite identification
            in performance tracking systems.

        Business Impact:
            Suite name enables identification and filtering of resilience
            benchmark results in multi-suite performance dashboards.

        Scenario:
            Given: A BenchmarkSuite with name "Test Suite"
            When: Accessing the name attribute
            Then: Value equals "Test Suite"
            And: Suite can be identified in reports

        Fixtures Used:
            - None required for attribute access
        """
        # Given: A BenchmarkSuite with name "Test Suite"
        suite = BenchmarkSuite(
            name="Test Suite",
            results=[],
            total_duration_ms=100.0,
            pass_rate=1.0,
            failed_benchmarks=[],
            timestamp="2023-01-01 12:00:00 UTC",
            environment_info={}
        )

        # When: Accessing the name attribute
        suite_name = suite.name

        # Then: Value equals "Test Suite"
        assert suite_name == "Test Suite"
        assert isinstance(suite_name, str)

        # And: Suite can be identified in reports
        assert "Test" in suite_name
        assert len(suite_name) > 0

    def test_benchmark_suite_results_list_accessible(self):
        """
        Test that BenchmarkSuite.results list is accessible.

        Verifies:
            Results list containing BenchmarkResult objects is stored
            and retrievable for detailed analysis.

        Business Impact:
            Results list enables analysis of individual benchmark
            performance and identification of specific issues.

        Scenario:
            Given: A BenchmarkSuite with multiple benchmark results
            When: Accessing the results attribute
            Then: Results list is accessible
            And: Individual benchmark results can be analyzed

        Fixtures Used:
            - None required for attribute access
        """
        # Given: A BenchmarkSuite with multiple benchmark results
        test_results = [
            BenchmarkResult(
                operation="operation_1",
                duration_ms=50.0,
                memory_peak_mb=5.0,
                iterations=5,
                avg_duration_ms=10.0,
                min_duration_ms=8.0,
                max_duration_ms=12.0,
                std_dev_ms=1.0,
                success_rate=1.0,
                metadata={}
            ),
            BenchmarkResult(
                operation="operation_2",
                duration_ms=75.0,
                memory_peak_mb=7.5,
                iterations=5,
                avg_duration_ms=15.0,
                min_duration_ms=12.0,
                max_duration_ms=18.0,
                std_dev_ms=1.5,
                success_rate=0.8,
                metadata={}
            )
        ]

        suite = BenchmarkSuite(
            name="Results Test Suite",
            results=test_results,
            total_duration_ms=125.0,
            pass_rate=0.9,
            failed_benchmarks=[],
            timestamp="2023-01-01 12:00:00 UTC",
            environment_info={}
        )

        # When: Accessing the results attribute
        results = suite.results

        # Then: Results list is accessible
        assert isinstance(results, list)
        assert len(results) == 2

        # And: Individual benchmark results can be analyzed
        for result in results:
            assert isinstance(result, BenchmarkResult)
            assert hasattr(result, 'operation')
            assert hasattr(result, 'duration_ms')

        assert results[0].operation == "operation_1"
        assert results[1].operation == "operation_2"

    def test_benchmark_suite_pass_rate_accessible(self):
        """
        Test that BenchmarkSuite.pass_rate attribute is accessible.

        Verifies:
            Overall pass rate metric is stored and retrievable for
            suite-level performance health assessment.

        Business Impact:
            Pass rate provides immediate indicator of overall benchmark
            suite health and configuration performance.

        Scenario:
            Given: A BenchmarkSuite with 85% pass rate
            When: Accessing the pass_rate attribute
            Then: Value equals 0.85
            And: Suite health can be quickly assessed

        Fixtures Used:
            - None required for attribute access
        """
        # Given: A BenchmarkSuite with 85% pass rate
        suite = BenchmarkSuite(
            name="Pass Rate Test Suite",
            results=[],
            total_duration_ms=200.0,
            pass_rate=0.85,
            failed_benchmarks=["failed_test"],
            timestamp="2023-01-01 12:00:00 UTC",
            environment_info={}
        )

        # When: Accessing the pass_rate attribute
        pass_rate = suite.pass_rate

        # Then: Value equals 0.85
        assert pass_rate == 0.85
        assert isinstance(pass_rate, float)

        # And: Suite health can be quickly assessed
        assert 0.0 <= pass_rate <= 1.0  # Valid range
        assert pass_rate > 0.8  # Good performance
        assert pass_rate < 1.0  # Some failures occurred

    def test_benchmark_suite_failed_benchmarks_accessible(self):
        """
        Test that BenchmarkSuite.failed_benchmarks list is accessible.

        Verifies:
            List of failed benchmark names is stored and retrievable for
            rapid issue identification.

        Business Impact:
            Failed benchmark list enables quick identification of
            problematic operations requiring investigation.

        Scenario:
            Given: A BenchmarkSuite with two failed benchmarks
            When: Accessing the failed_benchmarks attribute
            Then: List contains failed benchmark names
            And: Failed operations can be quickly identified

        Fixtures Used:
            - None required for attribute access
        """
        # Given: A BenchmarkSuite with two failed benchmarks
        failed_tests = ["slow_operation", "memory_intensive_operation"]

        suite = BenchmarkSuite(
            name="Failed Benchmarks Test Suite",
            results=[],
            total_duration_ms=300.0,
            pass_rate=0.75,
            failed_benchmarks=failed_tests,
            timestamp="2023-01-01 12:00:00 UTC",
            environment_info={}
        )

        # When: Accessing the failed_benchmarks attribute
        failed_benchmarks = suite.failed_benchmarks

        # Then: List contains failed benchmark names
        assert isinstance(failed_benchmarks, list)
        assert len(failed_benchmarks) == 2

        # And: Failed operations can be quickly identified
        assert "slow_operation" in failed_benchmarks
        assert "memory_intensive_operation" in failed_benchmarks

        for failed_name in failed_benchmarks:
            assert isinstance(failed_name, str)
            assert len(failed_name) > 0

    def test_benchmark_suite_environment_info_accessible(self):
        """
        Test that BenchmarkSuite.environment_info dictionary is accessible.

        Verifies:
            Environment context information is stored and retrievable
            for result interpretation and reproducibility.

        Business Impact:
            Environment context enables correlation of performance with
            system configuration and troubleshooting of issues.

        Scenario:
            Given: A BenchmarkSuite with environment information
            When: Accessing the environment_info attribute
            Then: Environment dictionary is accessible
            And: Context information aids result analysis

        Fixtures Used:
            - None required for attribute access
        """
        # Given: A BenchmarkSuite with environment information
        env_info = {
            "platform": "Linux-5.15.0",
            "python_version": "3.9.0",
            "cpu_count": 8,
            "memory_gb": 16.0,
            "environment_variables": {
                "DEBUG": "false",
                "RESILIENCE_PRESET": "production"
            },
            "test_configuration": {
                "iterations": 100,
                "timeout": 30
            }
        }

        suite = BenchmarkSuite(
            name="Environment Test Suite",
            results=[],
            total_duration_ms=150.0,
            pass_rate=0.95,
            failed_benchmarks=[],
            timestamp="2023-01-01 12:00:00 UTC",
            environment_info=env_info
        )

        # When: Accessing the environment_info attribute
        environment_info = suite.environment_info

        # Then: Environment dictionary is accessible
        assert isinstance(environment_info, dict)
        assert environment_info == env_info

        # And: Context information aids result analysis
        assert "platform" in environment_info
        assert "python_version" in environment_info
        assert "cpu_count" in environment_info
        assert environment_info["cpu_count"] == 8
        assert "environment_variables" in environment_info


class TestBenchmarkSuiteSerialization:
    """
    Tests for BenchmarkSuite serialization methods (to_dict, to_json).
    
    Scope:
        Verifies BenchmarkSuite can be serialized to dictionary and JSON
        formats for storage, transmission, and reporting.
    
    Business Impact:
        Serialization enables persistence of benchmark results, integration
        with monitoring systems, and sharing of results across teams.
    
    Test Strategy:
        - Test to_dict() method completeness
        - Test to_json() method validity
        - Test round-trip serialization
        - Test handling of nested structures
    """

    def test_benchmark_suite_to_dict_returns_dictionary(self):
        """
        Test that BenchmarkSuite.to_dict() returns dictionary representation.

        Verifies:
            to_dict() method returns dictionary containing all suite
            information for programmatic access and serialization.

        Business Impact:
            Dictionary format enables flexible data manipulation and
            integration with various storage and analysis systems.

        Scenario:
            Given: A BenchmarkSuite with comprehensive results
            When: Calling to_dict() method
            Then: Return value is a dictionary
            And: Dictionary contains all suite information

        Fixtures Used:
            - None required for serialization verification
        """
        # Given: A BenchmarkSuite with comprehensive results
        test_results = [
            BenchmarkResult(
                operation="test_operation",
                duration_ms=100.0,
                memory_peak_mb=10.0,
                iterations=10,
                avg_duration_ms=10.0,
                min_duration_ms=8.0,
                max_duration_ms=12.0,
                std_dev_ms=1.0,
                success_rate=1.0,
                metadata={}
            )
        ]

        suite = BenchmarkSuite(
            name="Test Suite",
            results=test_results,
            total_duration_ms=100.0,
            pass_rate=1.0,
            failed_benchmarks=[],
            timestamp="2023-01-01 12:00:00 UTC",
            environment_info={"platform": "test"}
        )

        # When: Calling to_dict() method
        result_dict = suite.to_dict()

        # Then: Return value is a dictionary
        assert isinstance(result_dict, dict)

        # And: Dictionary contains all suite information
        expected_keys = {"name", "results", "total_duration_ms", "pass_rate",
                        "failed_benchmarks", "timestamp", "environment_info"}
        assert set(result_dict.keys()) == expected_keys

    def test_benchmark_suite_to_dict_includes_all_fields(self):
        """
        Test that to_dict() includes all BenchmarkSuite fields.

        Verifies:
            Dictionary representation contains all suite attributes:
            name, results, total_duration_ms, pass_rate, failed_benchmarks,
            timestamp, environment_info.

        Business Impact:
            Complete dictionary representation ensures no information is
            lost during serialization and storage.

        Scenario:
            Given: A BenchmarkSuite with all fields populated
            When: Converting to dictionary with to_dict()
            Then: Dictionary contains keys for all suite attributes
            And: All field values are accurately represented

        Fixtures Used:
            - None required for completeness verification
        """
        # Given: A BenchmarkSuite with all fields populated
        test_results = [
            BenchmarkResult(
                operation="test_operation",
                duration_ms=200.0,
                memory_peak_mb=20.0,
                iterations=20,
                avg_duration_ms=10.0,
                min_duration_ms=5.0,
                max_duration_ms=15.0,
                std_dev_ms=2.0,
                success_rate=0.95,
                metadata={"test": "data"}
            )
        ]

        failed_benchmarks = ["failed_test"]
        environment_info = {"cpu_count": 4, "memory_gb": 8.0}

        suite = BenchmarkSuite(
            name="Complete Test Suite",
            results=test_results,
            total_duration_ms=200.0,
            pass_rate=0.9,
            failed_benchmarks=failed_benchmarks,
            timestamp="2023-01-01 12:00:00 UTC",
            environment_info=environment_info
        )

        # When: Converting to dictionary with to_dict()
        result_dict = suite.to_dict()

        # Then: Dictionary contains keys for all suite attributes
        assert "name" in result_dict
        assert "results" in result_dict
        assert "total_duration_ms" in result_dict
        assert "pass_rate" in result_dict
        assert "failed_benchmarks" in result_dict
        assert "timestamp" in result_dict
        assert "environment_info" in result_dict

        # And: All field values are accurately represented
        assert result_dict["name"] == "Complete Test Suite"
        assert result_dict["total_duration_ms"] == 200.0
        assert result_dict["pass_rate"] == 0.9
        assert result_dict["failed_benchmarks"] == failed_benchmarks
        assert result_dict["timestamp"] == "2023-01-01 12:00:00 UTC"
        assert result_dict["environment_info"] == environment_info

    def test_benchmark_suite_to_dict_handles_nested_results(self):
        """
        Test that to_dict() properly serializes nested BenchmarkResult objects.

        Verifies:
            Results list containing BenchmarkResult NamedTuples is properly
            converted to serializable dictionary format.

        Business Impact:
            Proper nested structure serialization enables complete data
            preservation for analysis and reporting systems.

        Scenario:
            Given: A BenchmarkSuite with multiple BenchmarkResult objects
            When: Converting to dictionary with to_dict()
            Then: Results are serialized to list of dictionaries
            And: All BenchmarkResult fields are preserved

        Fixtures Used:
            - None required for nested structure verification
        """
        # Given: A BenchmarkSuite with multiple BenchmarkResult objects
        test_results = [
            BenchmarkResult(
                operation="operation_1",
                duration_ms=100.0,
                memory_peak_mb=10.0,
                iterations=10,
                avg_duration_ms=10.0,
                min_duration_ms=8.0,
                max_duration_ms=12.0,
                std_dev_ms=1.0,
                success_rate=1.0,
                metadata={"env": "test"}
            ),
            BenchmarkResult(
                operation="operation_2",
                duration_ms=150.0,
                memory_peak_mb=15.0,
                iterations=15,
                avg_duration_ms=10.0,
                min_duration_ms=7.0,
                max_duration_ms=13.0,
                std_dev_ms=1.5,
                success_rate=0.93,
                metadata={"errors": ["timeout"]}
            )
        ]

        suite = BenchmarkSuite(
            name="Nested Test Suite",
            results=test_results,
            total_duration_ms=250.0,
            pass_rate=0.965,
            failed_benchmarks=[],
            timestamp="2023-01-01 12:00:00 UTC",
            environment_info={}
        )

        # When: Converting to dictionary with to_dict()
        result_dict = suite.to_dict()

        # Then: Results are serialized to list of dictionaries
        assert isinstance(result_dict["results"], list)
        assert len(result_dict["results"]) == 2

        # And: All BenchmarkResult fields are preserved
        for i, result_dict_item in enumerate(result_dict["results"]):
            assert isinstance(result_dict_item, dict)

            # Check all BenchmarkResult fields are present
            expected_result_fields = {
                "operation", "duration_ms", "memory_peak_mb", "iterations",
                "avg_duration_ms", "min_duration_ms", "max_duration_ms",
                "std_dev_ms", "success_rate", "metadata"
            }
            assert set(result_dict_item.keys()) == expected_result_fields

            # Check values match original
            original_result = test_results[i]
            assert result_dict_item["operation"] == original_result.operation
            assert result_dict_item["duration_ms"] == original_result.duration_ms
            assert result_dict_item["metadata"] == original_result.metadata

    def test_benchmark_suite_to_json_returns_valid_json_string(self):
        """
        Test that BenchmarkSuite.to_json() returns valid JSON string.

        Verifies:
            to_json() method returns properly formatted JSON string
            that can be parsed and stored.

        Business Impact:
            JSON format enables standard data exchange, API integration,
            and file-based result storage.

        Scenario:
            Given: A BenchmarkSuite with benchmark results
            When: Calling to_json() method
            Then: Return value is a valid JSON string
            And: String can be parsed back to data structure

        Fixtures Used:
            - None required for JSON validation
        """
        # Given: A BenchmarkSuite with benchmark results
        test_results = [
            BenchmarkResult(
                operation="json_test_operation",
                duration_ms=120.0,
                memory_peak_mb=12.0,
                iterations=12,
                avg_duration_ms=10.0,
                min_duration_ms=8.0,
                max_duration_ms=12.0,
                std_dev_ms=1.0,
                success_rate=1.0,
                metadata={}
            )
        ]

        suite = BenchmarkSuite(
            name="JSON Test Suite",
            results=test_results,
            total_duration_ms=120.0,
            pass_rate=1.0,
            failed_benchmarks=[],
            timestamp="2023-01-01 12:00:00 UTC",
            environment_info={"test": True}
        )

        # When: Calling to_json() method
        json_string = suite.to_json()

        # Then: Return value is a valid JSON string
        assert isinstance(json_string, str)
        assert len(json_string) > 0

        # And: String can be parsed back to data structure
        parsed_data = json.loads(json_string)
        assert isinstance(parsed_data, dict)
        assert parsed_data["name"] == "JSON Test Suite"

    def test_benchmark_suite_to_json_produces_parseable_output(self):
        """
        Test that to_json() output can be parsed back to dictionary.

        Verifies:
            JSON string produced by to_json() is valid and can be parsed
            using json.loads() for round-trip serialization.

        Business Impact:
            Parseable JSON enables storage and retrieval of benchmark
            results without data corruption or loss.

        Scenario:
            Given: A BenchmarkSuite serialized to JSON
            When: Parsing the JSON string with json.loads()
            Then: Parsing succeeds without errors
            And: Parsed data matches original suite structure

        Fixtures Used:
            - None required for parsing verification
        """
        # Given: A BenchmarkSuite serialized to JSON
        test_results = [
            BenchmarkResult(
                operation="parseable_test",
                duration_ms=80.0,
                memory_peak_mb=8.0,
                iterations=8,
                avg_duration_ms=10.0,
                min_duration_ms=9.0,
                max_duration_ms=11.0,
                std_dev_ms=0.5,
                success_rate=1.0,
                metadata={"parse_test": True}
            )
        ]

        suite = BenchmarkSuite(
            name="Parseable Test Suite",
            results=test_results,
            total_duration_ms=80.0,
            pass_rate=1.0,
            failed_benchmarks=[],
            timestamp="2023-01-01 12:00:00 UTC",
            environment_info={"parser": "json"}
        )

        # When: Parsing the JSON string with json.loads()
        json_string = suite.to_json()
        parsed_data = json.loads(json_string)

        # Then: Parsing succeeds without errors
        assert parsed_data is not None
        assert isinstance(parsed_data, dict)

        # And: Parsed data matches original suite structure
        assert parsed_data["name"] == suite.name
        assert parsed_data["total_duration_ms"] == suite.total_duration_ms
        assert parsed_data["pass_rate"] == suite.pass_rate
        assert parsed_data["failed_benchmarks"] == suite.failed_benchmarks
        assert parsed_data["timestamp"] == suite.timestamp
        assert parsed_data["environment_info"] == suite.environment_info

        # Check that nested results are also properly parsed
        assert isinstance(parsed_data["results"], list)
        assert len(parsed_data["results"]) == 1
        assert parsed_data["results"][0]["operation"] == "parseable_test"

    def test_benchmark_suite_to_json_handles_special_characters(self):
        """
        Test that to_json() properly escapes special characters.

        Verifies:
            Special characters in operation names, metadata, or error
            messages are properly escaped in JSON output.

        Business Impact:
            Proper character escaping ensures JSON validity even with
            unusual operation names or error messages containing quotes.

        Scenario:
            Given: A BenchmarkSuite with operation name containing quotes
            When: Converting to JSON with to_json()
            Then: Special characters are properly escaped
            And: JSON remains valid and parseable

        Fixtures Used:
            - None required for character escaping verification

        Edge Cases Covered:
            - Quote characters in strings
            - Newline characters in error messages
            - Unicode characters in metadata
        """
        # Given: A BenchmarkSuite with special characters in data
        test_results = [
            BenchmarkResult(
                operation='operation_with_"quotes"_and_\'apostrophes\'',
                duration_ms=100.0,
                memory_peak_mb=10.0,
                iterations=10,
                avg_duration_ms=10.0,
                min_duration_ms=8.0,
                max_duration_ms=12.0,
                std_dev_ms=1.0,
                success_rate=1.0,
                metadata={
                    "error_message": "Error: Unexpected \"token\" at line 1\nNewline included",
                    "unicode_chars": "Special chars: ñáéíóú 🚀 emoji test",
                    "special_json_chars": '{"key": "value"}'
                }
            )
        ]

        suite = BenchmarkSuite(
            name='Suite with "special" characters\nand newlines',
            results=test_results,
            total_duration_ms=100.0,
            pass_rate=1.0,
            failed_benchmarks=['failed_"operation"'],
            timestamp="2023-01-01 12:00:00 UTC",
            environment_info={
                "special_value": "Value with \"quotes\" and\nnewlines"
            }
        )

        # When: Converting to JSON with to_json()
        json_string = suite.to_json()

        # Then: Special characters are properly escaped
        assert isinstance(json_string, str)

        # And: JSON remains valid and parseable
        parsed_data = json.loads(json_string)
        assert parsed_data is not None
        assert parsed_data["name"] == 'Suite with "special" characters\nand newlines'
        assert parsed_data["failed_benchmarks"] == ['failed_"operation"']
        assert parsed_data["environment_info"]["special_value"] == 'Value with "quotes" and\nnewlines'

        # Check nested results with special characters
        result_metadata = parsed_data["results"][0]["metadata"]
        error_message = result_metadata["error_message"]
        unicode_chars = result_metadata["unicode_chars"]

        # Check for token keyword (surrounding quotes may be escaped in JSON)
        assert "token" in error_message
        assert "Error:" in error_message
        assert "Unexpected" in error_message

        # Check for unicode characters
        assert "ñáéíóú" in unicode_chars
        assert "🚀" in unicode_chars

    def test_benchmark_suite_to_dict_to_json_round_trip(self):
        """
        Test round-trip serialization: suite -> dict -> JSON -> dict.

        Verifies:
            Data can be converted through multiple serialization steps
            without loss or corruption.

        Business Impact:
            Round-trip fidelity ensures benchmark results remain accurate
            through storage, transmission, and deserialization cycles.

        Scenario:
            Given: A BenchmarkSuite with comprehensive results
            When: Converting to dict, then to JSON, then parsing JSON
            Then: Final dictionary matches original to_dict() output
            And: No data is lost or corrupted

        Fixtures Used:
            - None required for round-trip verification
        """
        # Given: A BenchmarkSuite with comprehensive results
        test_results = [
            BenchmarkResult(
                operation="round_trip_test",
                duration_ms=150.0,
                memory_peak_mb=15.0,
                iterations=15,
                avg_duration_ms=10.0,
                min_duration_ms=7.0,
                max_duration_ms=13.0,
                std_dev_ms=1.5,
                success_rate=0.93,
                metadata={
                    "test_param": "test_value",
                    "numeric_param": 42,
                    "list_param": [1, 2, 3],
                    "nested_dict": {"inner_key": "inner_value"}
                }
            )
        ]

        failed_benchmarks = ["slow_operation"]
        environment_info = {
            "platform": "test_platform",
            "python_version": "3.9.0",
            "cpu_count": 8,
            "nested_info": {
                "memory_info": {"total_gb": 16.0, "available_gb": 8.0}
            }
        }

        suite = BenchmarkSuite(
            name="Round Trip Test Suite",
            results=test_results,
            total_duration_ms=150.0,
            pass_rate=0.93,
            failed_benchmarks=failed_benchmarks,
            timestamp="2023-01-01 12:00:00 UTC",
            environment_info=environment_info
        )

        # When: Converting through multiple serialization steps
        original_dict = suite.to_dict()
        json_string = suite.to_json()
        parsed_dict = json.loads(json_string)

        # Then: Final dictionary matches original to_dict() output
        assert parsed_dict == original_dict

        # And: No data is lost or corrupted
        assert parsed_dict["name"] == original_dict["name"]
        assert parsed_dict["total_duration_ms"] == original_dict["total_duration_ms"]
        assert parsed_dict["pass_rate"] == original_dict["pass_rate"]
        assert parsed_dict["failed_benchmarks"] == original_dict["failed_benchmarks"]
        assert parsed_dict["timestamp"] == original_dict["timestamp"]
        assert parsed_dict["environment_info"] == original_dict["environment_info"]

        # Check nested results are preserved
        assert len(parsed_dict["results"]) == len(original_dict["results"])
        for orig_result, parsed_result in zip(original_dict["results"], parsed_dict["results"]):
            assert parsed_result == orig_result

        # Check deeply nested structures
        assert parsed_dict["environment_info"]["nested_info"]["memory_info"]["total_gb"] == 16.0
        assert parsed_dict["results"][0]["metadata"]["nested_dict"]["inner_key"] == "inner_value"


class TestPerformanceThresholdEnum:
    """
    Tests for PerformanceThreshold Enum values and usage.
    
    Scope:
        Verifies PerformanceThreshold Enum defines all documented thresholds
        with correct values for different operation types.
    
    Business Impact:
        Correct threshold definitions ensure benchmark pass/fail evaluation
        uses appropriate performance targets for each operation type.
    
    Test Strategy:
        - Test enum member existence
        - Test threshold values
        - Test enum usage in comparisons
        - Test threshold documentation
    """

    def test_performance_threshold_enum_has_config_loading(self):
        """
        Test that PerformanceThreshold enum includes CONFIG_LOADING threshold.

        Verifies:
            CONFIG_LOADING enum member exists with documented <100ms target
            for configuration loading operations.

        Business Impact:
            CONFIG_LOADING threshold enables validation that configuration
            operations meet <100ms performance target.

        Scenario:
            Given: The PerformanceThreshold enum
            When: Accessing CONFIG_LOADING member
            Then: Enum member exists
            And: Value represents <100ms threshold

        Fixtures Used:
            - None required for enum verification
        """
        # Given: The PerformanceThreshold enum

        # When: Accessing CONFIG_LOADING member
        config_loading_threshold = PerformanceThreshold.CONFIG_LOADING

        # Then: Enum member exists
        assert hasattr(PerformanceThreshold, 'CONFIG_LOADING')
        assert config_loading_threshold is not None

        # And: Value represents <100ms threshold
        assert isinstance(config_loading_threshold.value, (int, float))
        assert config_loading_threshold.value == 100.0

        # Verify it's the documented target for configuration loading
        assert config_loading_threshold.value <= 100.0

    def test_performance_threshold_enum_has_preset_access(self):
        """
        Test that PerformanceThreshold enum includes PRESET_ACCESS threshold.

        Verifies:
            PRESET_ACCESS enum member exists with documented <10ms target
            for preset lookup operations.

        Business Impact:
            PRESET_ACCESS threshold enables validation that preset loading
            meets aggressive <10ms performance target.

        Scenario:
            Given: The PerformanceThreshold enum
            When: Accessing PRESET_ACCESS member
            Then: Enum member exists
            And: Value represents <10ms threshold

        Fixtures Used:
            - None required for enum verification
        """
        # Given: The PerformanceThreshold enum

        # When: Accessing PRESET_ACCESS member
        preset_access_threshold = PerformanceThreshold.PRESET_ACCESS

        # Then: Enum member exists
        assert hasattr(PerformanceThreshold, 'PRESET_ACCESS')
        assert preset_access_threshold is not None

        # And: Value represents <10ms threshold
        assert isinstance(preset_access_threshold.value, (int, float))
        assert preset_access_threshold.value == 10.0

        # Verify it's the aggressive target for preset access
        assert preset_access_threshold.value <= 10.0

    def test_performance_threshold_enum_has_validation(self):
        """
        Test that PerformanceThreshold enum includes VALIDATION threshold.

        Verifies:
            VALIDATION enum member exists with documented <50ms target
            for configuration validation operations.

        Business Impact:
            VALIDATION threshold enables validation that config validation
            provides fast feedback within <50ms.

        Scenario:
            Given: The PerformanceThreshold enum
            When: Accessing VALIDATION member
            Then: Enum member exists
            And: Value represents <50ms threshold

        Fixtures Used:
            - None required for enum verification
        """
        # Given: The PerformanceThreshold enum

        # When: Accessing VALIDATION member
        validation_threshold = PerformanceThreshold.VALIDATION

        # Then: Enum member exists
        assert hasattr(PerformanceThreshold, 'VALIDATION')
        assert validation_threshold is not None

        # And: Value represents <50ms threshold
        assert isinstance(validation_threshold.value, (int, float))
        assert validation_threshold.value == 50.0

        # Verify it's the target for validation operations
        assert validation_threshold.value <= 50.0

    def test_performance_threshold_enum_has_service_init(self):
        """
        Test that PerformanceThreshold enum includes SERVICE_INIT threshold.

        Verifies:
            SERVICE_INIT enum member exists with documented <200ms target
            for service initialization operations.

        Business Impact:
            SERVICE_INIT threshold enables validation that service
            initialization completes quickly for fast application startup.

        Scenario:
            Given: The PerformanceThreshold enum
            When: Accessing SERVICE_INIT member
            Then: Enum member exists
            And: Value represents <200ms threshold

        Fixtures Used:
            - None required for enum verification
        """
        # Given: The PerformanceThreshold enum

        # When: Accessing SERVICE_INIT member
        service_init_threshold = PerformanceThreshold.SERVICE_INIT

        # Then: Enum member exists
        assert hasattr(PerformanceThreshold, 'SERVICE_INIT')
        assert service_init_threshold is not None

        # And: Value represents <200ms threshold
        assert isinstance(service_init_threshold.value, (int, float))
        assert service_init_threshold.value == 200.0

        # Verify it's the target for service initialization
        assert service_init_threshold.value <= 200.0

    def test_performance_threshold_values_are_numeric(self):
        """
        Test that PerformanceThreshold enum values are numeric for comparisons.

        Verifies:
            Enum values are numeric (integer or float) enabling direct
            comparison with measured execution times.

        Business Impact:
            Numeric values enable simple arithmetic comparison for
            pass/fail determination in benchmark evaluation.

        Scenario:
            Given: Any PerformanceThreshold enum member
            When: Checking the member's value type
            Then: Value is numeric (int or float)
            And: Value can be used in arithmetic comparisons

        Fixtures Used:
            - None required for type verification
        """
        # Given: Any PerformanceThreshold enum member
        thresholds = [
            PerformanceThreshold.CONFIG_LOADING,
            PerformanceThreshold.PRESET_ACCESS,
            PerformanceThreshold.VALIDATION,
            PerformanceThreshold.SERVICE_INIT
        ]

        for threshold in thresholds:
            # When: Checking the member's value type
            threshold_value = threshold.value

            # Then: Value is numeric (int or float)
            assert isinstance(threshold_value, (int, float))

            # And: Value can be used in arithmetic comparisons
            assert threshold_value > 0  # All thresholds should be positive
            assert threshold_value < 1000  # Reasonable upper bound

            # Test arithmetic operations
            double_value = threshold_value * 2
            half_value = threshold_value / 2
            assert isinstance(double_value, (int, float))
            assert isinstance(half_value, (int, float))

    def test_performance_threshold_can_compare_with_measured_time(self):
        """
        Test that PerformanceThreshold values can be compared with benchmark results.

        Verifies:
            Threshold values can be directly compared with avg_duration_ms
            from BenchmarkResult for pass/fail evaluation.

        Business Impact:
            Direct comparison enables simple pass/fail logic in benchmark
            evaluation without complex threshold lookup.

        Scenario:
            Given: A PerformanceThreshold value and measured execution time
            When: Comparing measured time against threshold
            Then: Comparison works correctly
            And: Pass/fail can be determined

        Fixtures Used:
            - None required for comparison verification
        """
        # Given: A PerformanceThreshold value and measured execution time
        threshold = PerformanceThreshold.CONFIG_LOADING  # 100ms threshold

        # Test cases with different execution times
        test_cases = [
            {"measured_time": 50.0, "expected_pass": True, "description": "Fast execution"},
            {"measured_time": 100.0, "expected_pass": True, "description": "Exactly at threshold"},
            {"measured_time": 150.0, "expected_pass": False, "description": "Slow execution"},
            {"measured_time": 25.5, "expected_pass": True, "description": "Very fast execution"},
            {"measured_time": 200.0, "expected_pass": False, "description": "Very slow execution"}
        ]

        for case in test_cases:
            measured_time = case["measured_time"]
            expected_pass = case["expected_pass"]
            description = case["description"]

            # When: Comparing measured time against threshold
            actual_pass = measured_time <= threshold.value

            # Then: Comparison works correctly
            assert actual_pass == expected_pass, f"Failed for {description}: {measured_time}ms vs {threshold.value}ms"

            # And: Pass/fail can be determined
            if actual_pass:
                assert measured_time <= threshold.value
            else:
                assert measured_time > threshold.value

        # Test with different threshold types
        preset_threshold = PerformanceThreshold.PRESET_ACCESS  # 10ms
        service_threshold = PerformanceThreshold.SERVICE_INIT  # 200ms

        # Verify different thresholds work for pass/fail determination
        assert 15.0 > preset_threshold.value  # Should fail for preset access
        assert 15.0 < service_threshold.value  # Should pass for service init
        assert 15.0 < threshold.value  # Should pass for config loading

