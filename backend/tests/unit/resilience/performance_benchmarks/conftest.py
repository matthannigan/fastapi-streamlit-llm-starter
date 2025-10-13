"""
Performance benchmarks module test fixtures providing external dependency isolation.

Provides Fakes and Mocks for external dependencies following the philosophy of
creating realistic test doubles that enable behavior-driven testing while isolating
the performance benchmarks component from systems outside its boundary.

External Dependencies Handled:
    - time: Standard library time module (fake implementation)
    - tracemalloc: Standard library memory tracing (fake implementation)
    - statistics: Standard library statistics module (fake implementation)
    - logging: Standard library logging system (mocked)
"""

import pytest
from unittest.mock import Mock, MagicMock
from typing import Dict, List, Any, Optional, Tuple
from dataclasses import dataclass, field
from contextlib import contextmanager
import time as real_time


@dataclass
class FakeMemorySnapshot:
    """Fake memory snapshot for testing memory tracking behavior."""
    current: int
    peak: int
    timestamp: float
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class FakePerformanceMetrics:
    """Fake performance metrics for testing benchmark calculations."""
    operation_name: str
    execution_time: float
    memory_delta: int
    cpu_usage: float
    success: bool
    error_message: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None


# Note: fake_time_module and mock_logger have been moved to the shared
# resilience/conftest.py file to eliminate duplication across modules


@pytest.fixture
def fake_tracemalloc_module():
    """
    Fake tracemalloc module implementation for deterministic memory testing.

    Provides a controllable memory tracing implementation that allows tests to
    simulate memory allocation patterns without actually tracking real memory.
    This enables deterministic testing of memory leak detection, memory usage
    monitoring, and memory-based performance metrics.

    State Management:
        - Memory tracking can be enabled/disabled programmatically
        - Memory snapshots provide configurable allocation data
        - Simulates realistic memory allocation patterns
        - Maintains tracemalloc interface compatibility

    Public Methods:
        start(): Enable memory tracking simulation
        stop(): Disable memory tracking simulation
        take_snapshot(): Create fake memory snapshot with configurable data
        get_traced_memory(): Return current and peak memory usage
        is_tracing(): Check if memory tracking is enabled

    Configuration Methods:
        set_memory_usage(current, peak): Configure memory usage values
        add_allocation(size, count): Simulate memory allocation
        configure_snapshot(snapshot_data): Set up snapshot with specific allocations

    Use Cases:
        - Testing memory leak detection without actual memory allocation
        - Testing memory usage monitoring and alerting
        - Testing memory-based performance metrics calculation
        - Testing memory cleanup and garbage collection behavior

    Test Customization:
        def test_memory_leak_detection(fake_tracemalloc_module):
            # Configure memory usage for test
            fake_tracemalloc_module.set_memory_usage(current=1000, peak=1500)

            # Create snapshot with allocation data
            fake_tracemalloc_module.configure_snapshot({
                "total": 1500,
                "allocations": [
                    {"size": 500, "count": 10},
                    {"size": 200, "count": 5}
                ]
            })

    Example:
        def test_performance_benchmark_memory_tracking(fake_tracemalloc_module, monkeypatch):
            from app.infrastructure.resilience.performance_benchmarks import PerformanceBenchmarker

            # Replace tracemalloc with our fake
            monkeypatch.setattr('app.infrastructure.resilience.performance_benchmarks.tracemalloc', fake_tracemalloc_module)

            benchmarker = PerformanceBenchmarker()

            # Start memory tracking
            fake_tracemalloc_module.start()

            # Simulate memory allocation
            fake_tracemalloc_module.add_allocation(size=1024, count=10)

            # Create snapshot for benchmark
            snapshot = fake_tracemalloc_module.take_snapshot()

            metrics = benchmarker.measure_memory_usage("test_operation")

            # Verify memory was tracked correctly
            assert metrics.memory_delta == 10240

    Default Behavior:
        - Memory tracking starts disabled
        - Memory usage defaults to 0 current, 0 peak
        - Snapshots return configurable allocation data
        - All operations are deterministic and instant

    Memory Units:
        - Memory sizes are in bytes for consistency with real tracemalloc
        - Supports both current and peak memory tracking
        - Provides realistic allocation pattern simulation

    Snapshot Structure:
        - Total memory usage
        - Allocation counts by size
        - Traceback information for allocation sources
        - Memory allocation patterns over time

    Note:
        This fake enables testing of memory-dependent performance logic
        without requiring actual memory allocation or causing test flakiness.
    """

    class FakeTracemallocModule:
        def __init__(self):
            self._tracing_enabled = False
            self._current_memory = 0
            self._peak_memory = 0
            self._snapshot_counter = 0
            self._allocation_history = []

        def start(self) -> None:
            """Start memory tracking simulation."""
            self._tracing_enabled = True
            self._current_memory = 0
            self._peak_memory = 0
            self._allocation_history.clear()

        def stop(self) -> None:
            """Stop memory tracking simulation."""
            self._tracing_enabled = False

        def is_tracing(self) -> bool:
            """Check if memory tracking is currently enabled."""
            return self._tracing_enabled

        def take_snapshot(self):
            """Create fake memory snapshot with current allocation data."""
            if not self._tracing_enabled:
                raise RuntimeError("tracemalloc is not tracing")

            self._snapshot_counter += 1
            return FakeMemorySnapshot(
                current=self._current_memory,
                peak=self._peak_memory,
                timestamp=real_time.time(),
                metadata={
                    "snapshot_id": self._snapshot_counter,
                    "allocation_count": len(self._allocation_history),
                    "total_allocations": sum(alloc["size"] * alloc["count"] for alloc in self._allocation_history)
                }
            )

        def get_traced_memory(self) -> Tuple[int, int]:
            """Return current and peak memory usage as (current, peak)."""
            if not self._tracing_enabled:
                raise RuntimeError("tracemalloc is not tracing")
            return self._current_memory, self._peak_memory

        def reset_peak(self) -> None:
            """Reset peak memory usage to current usage."""
            if not self._tracing_enabled:
                raise RuntimeError("tracemalloc is not tracing")
            self._peak_memory = self._current_memory

        def set_memory_usage(self, current: int, peak: Optional[int] = None) -> None:
            """Configure memory usage values for testing."""
            if self._tracing_enabled:
                self._current_memory = max(0, current)
                if peak is not None:
                    self._peak_memory = max(self._peak_memory, peak)
                else:
                    self._peak_memory = max(self._peak_memory, current)

        def add_allocation(self, size: int, count: int = 1, location: str = "test_location") -> None:
            """Simulate memory allocation for testing."""
            if self._tracing_enabled and size > 0 and count > 0:
                allocation_size = size * count
                self._current_memory += allocation_size
                self._peak_memory = max(self._peak_memory, self._current_memory)

                self._allocation_history.append({
                    "size": size,
                    "count": count,
                    "total": allocation_size,
                    "location": location,
                    "timestamp": real_time.time()
                })

        def simulate_deallocation(self, size: int, count: int = 1) -> None:
            """Simulate memory deallocation for testing."""
            if self._tracing_enabled and size > 0 and count > 0:
                deallocation_size = size * count
                self._current_memory = max(0, self._current_memory - deallocation_size)

        def configure_snapshot(self, snapshot_data: Dict[str, Any]) -> None:
            """Configure next snapshot with specific data."""
            self._next_snapshot_data = snapshot_data

        def get_allocation_stats(self) -> Dict[str, Any]:
            """Get statistics about current allocation patterns."""
            if not self._tracing_enabled:
                return {}

            total_allocations = sum(alloc["total"] for alloc in self._allocation_history)
            avg_allocation_size = (
                total_allocations / len(self._allocation_history)
                if self._allocation_history else 0
            )

            return {
                "total_allocations": total_allocations,
                "allocation_count": len(self._allocation_history),
                "avg_allocation_size": avg_allocation_size,
                "current_memory": self._current_memory,
                "peak_memory": self._peak_memory,
                "memory_efficiency": self._current_memory / self._peak_memory if self._peak_memory > 0 else 1.0
            }

    return FakeTracemallocModule()


@pytest.fixture
def fake_statistics_module():
    """
    Fake statistics module implementation for deterministic statistical testing.

    Provides a controllable statistics implementation that allows tests to
    configure statistical calculation results without relying on actual
    statistical computations. This enables deterministic testing of performance
    metrics calculations, benchmark aggregations, and statistical analysis.

    Default Behavior:
        - Configurable statistical function results
        - Supports common statistical operations (mean, median, stdev, etc.)
        - Realistic interface matching statistics module
        - Deterministic results for consistent testing

    Statistical Functions:
        - mean(data): Returns configured mean value
        - median(data): Returns configured median value
        - stdev(data): Returns configured standard deviation
        - variance(data): Returns configured variance
        - min(data): Returns configured minimum value
        - max(data): Returns configured maximum value

    Configuration Methods:
        set_calculation_result(func_name, result): Configure function result
        set_statistical_profile(data_points): Configure complete statistical profile
        reset_calculations(): Reset all configured values to defaults

    Use Cases:
        - Testing performance metrics aggregation
        - Testing benchmark statistical analysis
        - Testing percentile calculations and distributions
        - Testing statistical performance monitoring

    Test Customization:
        def test_performance_statistics(fake_statistics_module):
            # Configure statistical results for test scenario
            fake_statistics_module.set_statistical_profile({
                "mean": 1.5,
                "median": 1.2,
                "stdev": 0.8,
                "min": 0.5,
                "max": 3.0
            })

    Example:
        def test_benchmark_statistical_analysis(fake_statistics_module, monkeypatch):
            from app.infrastructure.resilience.performance_benchmarks import PerformanceBenchmarker

            # Replace statistics module with our fake
            monkeypatch.setattr('app.infrastructure.resilience.performance_benchmarks.statistics', fake_statistics_module)

            benchmarker = PerformanceBenchmarker()

            # Configure statistical profile for test data
            fake_statistics_module.set_statistical_profile({
                "mean": 2.1,
                "median": 1.9,
                "stdev": 0.6,
                "p95": 3.5,
                "p99": 4.2
            })

            # Test statistical analysis of performance data
            performance_data = [1.0, 2.0, 1.5, 3.0, 2.5]
            stats = benchmarker.calculate_statistics(performance_data)

            # Verify configured statistical values were used
            assert stats.mean == 2.1
            assert stats.median == 1.9

    Default Statistical Profile:
        - mean: 1.0 (average performance)
        - median: 1.0 (median performance)
        - stdev: 0.5 (standard deviation)
        - variance: 0.25 (variance)
        - min: 0.1 (minimum performance)
        - max: 5.0 (maximum performance)

    Percentile Support:
        - p50 (median): 50th percentile
        - p90: 90th percentile
        - p95: 95th percentile
        - p99: 99th percentile

    Statistical Validity:
        - Ensures configured values maintain statistical consistency
        - Validates that min ≤ median ≤ max relationships
        - Provides realistic statistical distributions

    Note:
        This fake enables testing of statistical performance analysis without
        relying on actual statistical computations, making tests faster and
        more deterministic.
    """

    class FakeStatisticsModule:
        def __init__(self):
            self._results = {
                "mean": 1.0,
                "median": 1.0,
                "stdev": 0.5,
                "variance": 0.25,
                "min": 0.1,
                "max": 5.0,
                "sum": 10.0,
                "count": 10,
                "p50": 1.0,
                "p90": 2.5,
                "p95": 3.0,
                "p99": 4.0
            }

        def mean(self, data):
            """Return configured mean value."""
            return self._results["mean"]

        def median(self, data):
            """Return configured median value."""
            return self._results["median"]

        def stdev(self, data):
            """Return configured standard deviation."""
            return self._results["stdev"]

        def variance(self, data):
            """Return configured variance."""
            return self._results["variance"]

        def min(self, data):
            """Return configured minimum value."""
            return self._results["min"]

        def max(self, data):
            """Return configured maximum value."""
            return self._results["max"]

        def sum(self, data):
            """Return configured sum value."""
            return self._results["sum"]

        def fmean(self, data):
            """Return configured floating-point mean value."""
            return float(self._results["mean"])

        def median_low(self, data):
            """Return configured low median value."""
            return self._results["median"] * 0.9

        def median_high(self, data):
            """Return configured high median value."""
            return self._results["median"] * 1.1

        def quantiles(self, data, n=4):
            """Return configured quantile values."""
            base_value = self._results["median"]
            return [base_value * (i + 1) / n for i in range(n - 1)]

        def percentile(self, data, p):
            """Return configured percentile value."""
            percentile_map = {
                50: "p50",
                90: "p90",
                95: "p95",
                99: "p99"
            }
            key = percentile_map.get(int(p), "p50")
            return self._results[key]

        def set_calculation_result(self, func_name: str, result: float) -> None:
            """Configure specific statistical function result."""
            self._results[func_name] = result

        def set_statistical_profile(self, profile: Dict[str, float]) -> None:
            """Configure complete statistical profile."""
            for key, value in profile.items():
                if key in self._results:
                    self._results[key] = value

        def reset_calculations(self) -> None:
            """Reset all statistical calculations to defaults."""
            self._results.update({
                "mean": 1.0,
                "median": 1.0,
                "stdev": 0.5,
                "variance": 0.25,
                "min": 0.1,
                "max": 5.0,
                "sum": 10.0,
                "count": 10,
                "p50": 1.0,
                "p90": 2.5,
                "p95": 3.0,
                "p99": 4.0
            })

        def validate_consistency(self) -> bool:
            """Validate statistical consistency of configured values."""
            values = self._results
            return (
                values["min"] <= values["median"] <= values["max"] and
                values["stdev"] >= 0 and
                values["variance"] >= 0 and
                values["mean"] >= values["min"] and
                values["mean"] <= values["max"]
            )

    return FakeStatisticsModule()




@pytest.fixture
def performance_benchmarks_test_data():
    """
    Standardized test data for performance benchmarks behavior testing.

    Provides consistent test scenarios and data structures for performance
    benchmarks testing across different test modules. Ensures test consistency
    and reduces duplication in performance testing implementations.

    Data Structure:
        - operation_scenarios: Different operation types and their expected performance
        - performance_thresholds: Performance limits and alerting thresholds
        - benchmark_scenarios: Complete benchmark test scenarios
        - memory_scenarios: Memory usage and allocation patterns
        - statistical_scenarios: Statistical analysis test cases

    Use Cases:
        - Standardizing performance benchmark test inputs across test modules
        - Providing consistent performance scenario coverage
        - Testing different performance threshold combinations
        - Reducing test code duplication while ensuring thorough coverage

    Example:
        def test_benchmark_with_various_scenarios(performance_benchmarks_test_data):
            for scenario in performance_benchmarks_test_data['operation_scenarios']:
                # Test benchmark behavior with each operation type
                result = benchmarker.measure_operation(scenario['operation'], scenario['function'])
                assert result.execution_time <= scenario['max_time']
    """
    return {
        "operation_scenarios": [
            {
                "name": "fast_operation",
                "operation": "cache_get",
                "expected_time": 0.01,
                "max_time": 0.05,
                "memory_usage": 100,
                "expected_success_rate": 0.99,
                "expected_alert_level": "none",
                "description": "Fast cache retrieval operation with high success rate"
            },
            {
                "name": "medium_operation",
                "operation": "ai_inference",
                "expected_time": 1.0,
                "max_time": 2.0,
                "memory_usage": 5000,
                "expected_success_rate": 0.95,
                "expected_alert_level": "none",
                "description": "AI model inference operation with moderate success rate"
            },
            {
                "name": "slow_operation",
                "operation": "batch_processing",
                "expected_time": 5.0,
                "max_time": 10.0,
                "memory_usage": 50000,
                "expected_success_rate": 0.90,
                "expected_alert_level": "warning",
                "description": "Batch processing operation with potential performance warnings"
            },
            {
                "name": "network_operation",
                "operation": "external_api_call",
                "expected_time": 2.0,
                "max_time": 5.0,
                "memory_usage": 1000,
                "expected_success_rate": 0.85,
                "expected_alert_level": "info",
                "description": "External API call operation with variable performance"
            }
        ],
        "performance_thresholds": [
            {
                "name": "strict_thresholds",
                "max_execution_time": 1.0,
                "max_memory_usage": 1000,
                "min_success_rate": 0.99,
                "description": "Strict performance requirements for critical operations"
            },
            {
                "name": "normal_thresholds",
                "max_execution_time": 5.0,
                "max_memory_usage": 10000,
                "min_success_rate": 0.95,
                "description": "Normal performance requirements for standard operations"
            },
            {
                "name": "lenient_thresholds",
                "max_execution_time": 30.0,
                "max_memory_usage": 100000,
                "min_success_rate": 0.90,
                "description": "Lenient requirements for background operations"
            }
        ],
        "benchmark_scenarios": [
            {
                "name": "single_operation_benchmark",
                "operation_count": 1,
                "concurrent": False,
                "expected_duration": 1.0,
                "expected_success_rate": 1.0,
                "expected_behavior": "linear_scaling",
                "description": "Benchmark single operation execution with perfect success rate"
            },
            {
                "name": "sequential_benchmark",
                "operation_count": 100,
                "concurrent": False,
                "expected_duration": 100.0,
                "expected_success_rate": 0.99,
                "expected_behavior": "linear_scaling",
                "description": "Benchmark sequential operation execution with linear time complexity"
            },
            {
                "name": "concurrent_benchmark",
                "operation_count": 50,
                "concurrent": True,
                "expected_duration": 10.0,
                "expected_success_rate": 0.95,
                "expected_behavior": "parallel_speedup",
                "description": "Benchmark concurrent operation execution with parallel speedup"
            },
            {
                "name": "stress_test_benchmark",
                "operation_count": 1000,
                "concurrent": True,
                "expected_duration": 60.0,
                "expected_success_rate": 0.90,
                "expected_behavior": "resource_contention",
                "description": "Stress test with high concurrent load showing resource contention"
            }
        ],
        "memory_scenarios": [
            {
                "name": "memory_efficient",
                "initial_memory": 1000,
                "peak_memory": 2000,
                "final_memory": 1100,
                "allocation_pattern": "minimal",
                "description": "Memory efficient operation with minimal allocations"
            },
            {
                "name": "memory_intensive",
                "initial_memory": 1000,
                "peak_memory": 50000,
                "final_memory": 2000,
                "allocation_pattern": "burst",
                "description": "Memory intensive operation with burst allocations"
            },
            {
                "name": "memory_leak_simulation",
                "initial_memory": 1000,
                "peak_memory": 10000,
                "final_memory": 9500,
                "allocation_pattern": "growing",
                "description": "Simulated memory leak pattern for testing"
            }
        ],
        "statistical_scenarios": [
            {
                "name": "consistent_performance",
                "data_points": [1.0, 1.1, 0.9, 1.2, 1.0],
                "expected_mean": 1.04,
                "expected_stdev": 0.11,
                "description": "Consistent performance with low variance"
            },
            {
                "name": "variable_performance",
                "data_points": [0.5, 2.0, 1.5, 3.0, 0.8],
                "expected_mean": 1.56,
                "expected_stdev": 0.91,
                "description": "Variable performance with high variance"
            },
            {
                "name": "degrading_performance",
                "data_points": [1.0, 1.5, 2.0, 2.8, 3.5],
                "expected_mean": 2.16,
                "expected_stdev": 0.96,
                "description": "Performance degradation over time"
            }
        ],
        "alert_scenarios": [
            {
                "name": "performance_alert",
                "trigger_condition": "execution_time > threshold",
                "threshold": 5.0,
                "measured_value": 7.5,
                "severity": "warning",
                "description": "Performance alert for slow execution"
            },
            {
                "name": "memory_alert",
                "trigger_condition": "memory_usage > threshold",
                "threshold": 10000,
                "measured_value": 15000,
                "severity": "critical",
                "description": "Memory alert for high usage"
            },
            {
                "name": "error_rate_alert",
                "trigger_condition": "error_rate > threshold",
                "threshold": 0.1,
                "measured_value": 0.15,
                "severity": "warning",
                "description": "Error rate alert for degraded reliability"
            }
        ]
    }


@pytest.fixture
def mock_performance_collector():
    """
    Mock performance metrics collector for integration testing.

    Provides a mock metrics collector that simulates performance data
    collection and aggregation. This enables testing of performance
    benchmarking logic without requiring actual metrics collection systems.

    Mock Components:
        - MockMetricsCollector: Simulates metrics collection and storage
        - MockAggregator: Simulates statistical aggregation of metrics
        - MockAlerting: Simulates performance alert generation
        - MockReporting: Simulates performance report generation

    Use Cases:
        - Testing performance metrics collection accuracy
        - Testing statistical aggregation of performance data
        - Testing performance alert generation logic
        - Testing performance report generation

    Example:
        def test_performance_metrics_collection(mock_performance_collector):
            collector = mock_performance_collector["metrics_collector"]

            # Simulate performance data collection
            collector.record_metric("execution_time", 1.5)
            collector.record_metric("memory_usage", 1000)

            # Verify metrics were recorded
            collector.get_metrics.assert_called_with("execution_time")
    """
    # Mock metrics collector
    mock_metrics_collector = MagicMock()
    mock_metrics_collector.record_metric = Mock(return_value=True)
    mock_metrics_collector.record_timing = Mock(return_value=True)
    mock_metrics_collector.record_memory = Mock(return_value=True)
    mock_metrics_collector.get_metrics = Mock(return_value={"execution_time": 1.5})
    mock_metrics_collector.get_aggregated_metrics = Mock(return_value={
        "avg_execution_time": 1.2,
        "max_memory_usage": 5000,
        "total_operations": 100
    })
    mock_metrics_collector.reset_metrics = Mock(return_value=True)

    # Mock statistical aggregator
    mock_aggregator = MagicMock()
    mock_aggregator.aggregate_data = Mock(return_value={
        "mean": 1.5,
        "median": 1.2,
        "p95": 3.0,
        "stdev": 0.8
    })
    mock_aggregator.calculate_percentiles = Mock(return_value={
        "p50": 1.0, "p90": 2.5, "p95": 3.0, "p99": 4.0
    })

    # Mock alerting system
    mock_alerting = MagicMock()
    mock_alerting.check_thresholds = Mock(return_value=[])
    mock_alerting.generate_alert = Mock(return_value={
        "type": "performance",
        "severity": "warning",
        "message": "Execution time exceeded threshold"
    })
    mock_alerting.active_alerts = Mock(return_value=[])

    # Mock reporting system
    mock_reporting = MagicMock()
    mock_reporting.generate_report = Mock(return_value={
        "summary": {"total_operations": 100, "success_rate": 0.95},
        "performance_metrics": {"avg_time": 1.2, "max_memory": 5000},
        "recommendations": ["Optimize cache usage", "Increase timeout values"]
    })
    mock_reporting.export_metrics = Mock(return_value="metrics.json")

    return {
        "metrics_collector": mock_metrics_collector,
        "aggregator": mock_aggregator,
        "alerting": mock_alerting,
        "reporting": mock_reporting
    }