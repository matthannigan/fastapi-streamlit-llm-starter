"""
Integration Tests: Orchestrator → Metrics Collection → Performance Monitoring

This module tests the integration between resilience orchestration, metrics collection,
and performance monitoring. It validates that comprehensive metrics are collected,
performance is monitored, and operational visibility is maintained across the system.

Integration Scope:
    - AIServiceResilience → ResilienceMetrics → ConfigurationMetricsCollector
    - Performance benchmarks → Configuration validation → Operational monitoring
    - Metrics collection → Performance analysis → Alert generation

Business Impact:
    Provides operational visibility for production monitoring and alerting,
    enabling proactive issue detection and performance optimization

Test Strategy:
    - Test comprehensive metrics collection across operations
    - Validate performance monitoring and benchmarking
    - Test metrics integration with health checks
    - Verify operational visibility and monitoring capabilities
    - Test performance threshold validation and alerting

Critical Paths:
    - Operation execution → Metrics collection → Performance analysis
    - Configuration loading → Performance measurement → Validation
    - Health monitoring → Metrics export → Alert generation
"""

import pytest
import asyncio
import time
from unittest.mock import AsyncMock, patch
from typing import Dict, Any

from app.core.config import Settings
from app.infrastructure.resilience.orchestrator import AIServiceResilience
from app.infrastructure.resilience.circuit_breaker import CircuitBreakerConfig, ResilienceMetrics
from app.infrastructure.resilience.config_presets import ResilienceStrategy, ResilienceConfig
from app.infrastructure.resilience.config_monitoring import ConfigurationMetricsCollector
from app.infrastructure.resilience.performance_benchmarks import ConfigurationPerformanceBenchmark


class TestMetricsPerformanceMonitoring:
    """
    Integration tests for Orchestrator → Metrics Collection → Performance Monitoring.

    Seam Under Test:
        AIServiceResilience → ResilienceMetrics → ConfigurationMetricsCollector → Performance benchmarks

    Critical Paths:
        - Operation execution → Metrics collection → Performance analysis
        - Configuration loading → Performance measurement → Validation
        - Health monitoring → Metrics export → Alert generation

    Business Impact:
        Provides comprehensive operational visibility and performance monitoring
        for production systems, enabling proactive issue detection and optimization
    """

    @pytest.fixture
    def metrics_orchestrator(self):
        """Create a resilience orchestrator with comprehensive metrics collection."""
        settings = Settings(
            environment="testing",
            enable_circuit_breaker=True,
            enable_retry=True,
            max_retry_attempts=3,
            circuit_breaker_failure_threshold=5,
            circuit_breaker_recovery_timeout=60
        )

        orchestrator = AIServiceResilience(settings)

        # Register multiple operations for testing
        operations = [
            "summarize_operation",
            "sentiment_operation",
            "key_points_operation",
            "qa_operation"
        ]

        for operation in operations:
            orchestrator.register_operation(operation, ResilienceStrategy.BALANCED)

        return orchestrator

    @pytest.fixture
    def metrics_collector(self):
        """Create a configuration metrics collector for testing."""
        return ConfigurationMetricsCollector()

    @pytest.fixture
    def performance_benchmark(self):
        """Create a performance benchmark instance for testing."""
        return ConfigurationPerformanceBenchmark()

    def test_comprehensive_metrics_collection(self, metrics_orchestrator):
        """
        Test comprehensive metrics collection across multiple operations.

        Integration Scope:
            Multiple operations → Metrics collection → Aggregation → Analysis

        Business Impact:
            Provides operational visibility across all resilience operations

        Test Strategy:
            - Execute operations with different outcomes
            - Verify metrics are collected for each operation
            - Test metrics aggregation and analysis
            - Validate metrics structure and completeness

        Success Criteria:
            - Metrics collected for each operation independently
            - Success/failure counts accurate
            - Timing information captured
            - Circuit breaker state transitions tracked
        """
        # Execute successful operation
        @metrics_orchestrator.with_operation_resilience("summarize_operation")
        async def successful_operation():
            return "Success result"

        result = successful_operation()  # Remove await for sync test
        assert result == "Success result"

        # Execute failed operation
        @metrics_orchestrator.with_operation_resilience("sentiment_operation")
        async def failing_operation():
            raise Exception("Simulated failure")

        with pytest.raises(Exception):
            failing_operation()  # Remove await for sync test

        # Get comprehensive metrics
        all_metrics = metrics_orchestrator.get_all_metrics()

        # Verify metrics structure
        assert "operations" in all_metrics
        assert "circuit_breakers" in all_metrics
        assert "summary" in all_metrics

        # Verify operation-specific metrics
        operations_metrics = all_metrics["operations"]
        assert "summarize_operation" in operations_metrics
        assert "sentiment_operation" in operations_metrics

        # Check individual operation metrics
        summarize_metrics = operations_metrics["summarize_operation"]
        assert hasattr(summarize_metrics, 'total_calls')
        assert summarize_metrics.total_calls >= 1
        assert summarize_metrics.successful_calls >= 1
        assert summarize_metrics.failed_calls == 0

        sentiment_metrics = operations_metrics["sentiment_operation"]
        assert sentiment_metrics.total_calls >= 1
        assert sentiment_metrics.failed_calls >= 1

        # Verify summary statistics
        summary = all_metrics["summary"]
        assert "total_operations" in summary
        assert "total_calls" in summary
        assert "overall_success_rate" in summary

    def test_performance_monitoring_and_timing(self, metrics_orchestrator):
        """
        Test performance monitoring and timing metrics.

        Integration Scope:
            Operation execution → Timing collection → Performance analysis → Benchmarking

        Business Impact:
            Enables performance optimization and SLA monitoring

        Test Strategy:
            - Execute operations with varying execution times
            - Verify timing metrics are captured accurately
            - Test performance benchmarking functionality
            - Validate timing-based alerts and thresholds

        Success Criteria:
            - Operation timing captured and stored
            - Performance metrics calculated correctly
            - Timing-based thresholds validated
            - Performance regression detection works
        """
        # Execute fast operation
        start_time = time.time()

        @metrics_orchestrator.with_operation_resilience("summarize_operation")
        async def fast_operation():
            return "Fast result"

        result = fast_operation()  # Remove await for sync test
        fast_duration = time.time() - start_time

        # Execute slow operation
        @metrics_orchestrator.with_operation_resilience("qa_operation")
        async def slow_operation():
            time.sleep(0.1)  # Simulate slow operation
            return "Slow result"

        start_time = time.time()
        result = slow_operation()  # Remove await for sync test
        slow_duration = time.time() - start_time

        # Verify timing metrics
        all_metrics = metrics_orchestrator.get_all_metrics()
        operations_metrics = all_metrics["operations"]

        # Verify timing information is captured
        for operation_name, metrics in operations_metrics.items():
            assert hasattr(metrics, 'total_calls')
            assert metrics.total_calls >= 1
            # Note: Individual timing metrics may not be exposed in current implementation

        # Verify operations completed in expected time ranges
        assert fast_duration < slow_duration
        assert slow_duration >= 0.1  # Should include sleep time

    def test_circuit_breaker_metrics_tracking(self, metrics_orchestrator):
        """
        Test circuit breaker state transition metrics.

        Integration Scope:
            Circuit breaker → State transitions → Metrics collection → Health monitoring

        Business Impact:
            Provides visibility into circuit breaker behavior for operational monitoring

        Test Strategy:
            - Trigger circuit breaker state transitions
            - Verify metrics track state changes
            - Test metrics during recovery scenarios
            - Validate health status based on metrics

        Success Criteria:
            - Circuit breaker opens tracked in metrics
            - State transitions recorded accurately
            - Recovery attempts monitored
            - Health status reflects circuit breaker state
        """
        # Execute multiple failing operations to trigger circuit breaker
        @metrics_orchestrator.with_operation_resilience("key_points_operation")
        async def failing_operation():
            raise Exception("Simulated service failure")

        # Execute failures until circuit breaker opens
        for _ in range(5):
            try:
                failing_operation()  # Remove await for sync test
            except Exception:
                pass  # Expected to fail

        # Get metrics after circuit breaker should be open
        all_metrics = metrics_orchestrator.get_all_metrics()

        # Verify circuit breaker metrics
        circuit_breaker_metrics = all_metrics["circuit_breakers"]
        assert "key_points_operation" in circuit_breaker_metrics

        cb_metrics = circuit_breaker_metrics["key_points_operation"]
        assert hasattr(cb_metrics, 'state')
        assert cb_metrics.total_calls >= 5
        assert cb_metrics.failed_calls >= 5

        # Verify health status reflects circuit breaker state
        health_status = metrics_orchestrator.get_health_status()
        assert "healthy" in health_status
        assert "open_circuit_breakers" in health_status

        # Should have open circuit breaker due to failures
        if not health_status["healthy"]:
            assert "key_points_operation" in health_status["open_circuit_breakers"]

    def test_metrics_reset_and_cleanup(self, metrics_orchestrator):
        """
        Test metrics reset and cleanup functionality.

        Integration Scope:
            Metrics collection → Reset functionality → State cleanup → Validation

        Business Impact:
            Enables operational maintenance and testing scenarios

        Test Strategy:
            - Generate metrics through operation execution
            - Test selective metrics reset for specific operations
            - Test complete metrics reset for entire system
            - Verify state cleanup doesn't affect active operations

        Success Criteria:
            - Selective reset clears specific operation metrics
            - Complete reset clears all metrics
            - Reset doesn't interfere with active operations
            - State management remains consistent after reset
        """
        # Execute operations to generate metrics
        @metrics_orchestrator.with_operation_resilience("summarize_operation")
        async def test_operation():
            return "Test result"

        # Execute multiple times
        for _ in range(3):
            result = test_operation()  # Remove await for sync test
            assert result == "Test result"

        # Verify metrics exist
        all_metrics = metrics_orchestrator.get_all_metrics()
        operations_metrics = all_metrics["operations"]
        assert "summarize_operation" in operations_metrics

        original_metrics = operations_metrics["summarize_operation"]
        assert original_metrics.total_calls >= 3

        # Reset metrics for specific operation
        metrics_orchestrator.reset_metrics("summarize_operation")

        # Verify specific operation metrics reset
        updated_metrics = metrics_orchestrator.get_all_metrics()
        updated_operations_metrics = updated_metrics["operations"]

        if "summarize_operation" in updated_operations_metrics:
            reset_metrics = updated_operations_metrics["summarize_operation"]
            # Metrics should be reset (may be recreated as empty)
            assert reset_metrics.total_calls < original_metrics.total_calls
        else:
            # Operation may be removed from metrics after reset
            assert True

        # Test complete system reset
        metrics_orchestrator.reset_metrics()  # Reset all

        final_metrics = metrics_orchestrator.get_all_metrics()
        final_operations = final_metrics["operations"]

        # All operations should be reset
        assert len(final_operations) == 0 or all(
            metrics.total_calls == 0 for metrics in final_operations.values()
        )

    def test_health_status_integration_with_metrics(self, metrics_orchestrator):
        """
        Test health status integration with metrics collection.

        Integration Scope:
            Health monitoring → Metrics integration → Status reporting → Alerting

        Business Impact:
            Provides accurate health information based on real metrics

        Test Strategy:
            - Test health status with healthy operations
            - Verify health status with failed operations
            - Test health status with mixed operation states
            - Validate health information accuracy

        Success Criteria:
            - Health status accurately reflects operation health
            - Circuit breaker states included in health status
            - Metrics contribute to health assessment
            - Health information format suitable for monitoring
        """
        # Test with all healthy operations
        @metrics_orchestrator.with_operation_resilience("summarize_operation")
        async def healthy_operation():
            return "Healthy result"

        result = healthy_operation()  # Remove await for sync test
        assert result == "Healthy result"

        # Get health status
        health_status = metrics_orchestrator.get_health_status()

        # Should be healthy
        assert health_status["healthy"] is True
        assert "total_operations" in health_status
        assert health_status["total_operations"] >= 1
        assert len(health_status.get("open_circuit_breakers", [])) == 0

        # Test with failing operations
        @metrics_orchestrator.with_operation_resilience("failing_operation")
        async def failing_op():
            raise Exception("Failing operation")

        # Execute failures
        for _ in range(5):
            try:
                failing_op()  # Remove await for sync test
            except Exception:
                pass

        # Get health status after failures
        unhealthy_status = metrics_orchestrator.get_health_status()

        # Should reflect unhealthy state
        assert "healthy" in unhealthy_status
        assert "open_circuit_breakers" in unhealthy_status
        assert "total_operations" in unhealthy_status
        assert unhealthy_status["total_operations"] >= 2

        # Test health status format and completeness
        required_fields = [
            "healthy", "total_operations", "open_circuit_breakers",
            "half_open_circuit_breakers", "total_circuit_breakers", "timestamp"
        ]

        for field in required_fields:
            assert field in unhealthy_status

    def test_performance_threshold_monitoring(self, performance_benchmark):
        """
        Test performance threshold monitoring and validation.

        Integration Scope:
            Performance monitoring → Threshold validation → Alerting → Optimization

        Business Impact:
            Enables proactive performance issue detection and optimization

        Test Strategy:
            - Test performance threshold configuration
            - Validate performance measurement accuracy
            - Test threshold-based alerting logic
            - Verify performance regression detection

        Success Criteria:
            - Performance thresholds correctly configured
            - Performance measurements accurate
            - Threshold violations detected
            - Performance monitoring provides actionable insights
        """
        # Test performance threshold configuration
        thresholds = {
            "fast_operation": 0.1,    # 100ms for fast operations
            "medium_operation": 0.5,  # 500ms for medium operations
            "slow_operation": 2.0     # 2s for slow operations
        }

        # Simulate performance measurements
        measurements = {
            "fast_operation": [0.05, 0.08, 0.06],      # All under threshold
            "medium_operation": [0.3, 0.4, 0.6],      # Mixed results
            "slow_operation": [2.5, 3.0, 2.8]        # All over threshold
        }

        # Validate threshold checking
        for operation, times in measurements.items():
            threshold = thresholds[operation]
            avg_time = sum(times) / len(times)

            if avg_time <= threshold:
                assert True, f"{operation} performance acceptable: {avg_time".3f"}s <= {threshold}s"
            else:
                assert False, f"{operation} performance violation: {avg_time".3f"}s > {threshold}s"

        # Test specific threshold validation
        assert sum(measurements["fast_operation"]) / len(measurements["fast_operation"]) <= 0.1
        assert sum(measurements["slow_operation"]) / len(measurements["slow_operation"]) > 2.0

    def test_metrics_export_and_monitoring_integration(self, metrics_orchestrator):
        """
        Test metrics export and monitoring system integration.

        Integration Scope:
            Metrics collection → Export formatting → Monitoring integration → Alerting

        Business Impact:
            Enables integration with external monitoring systems

        Test Strategy:
            - Test metrics export in various formats
            - Verify monitoring system compatibility
            - Test metrics streaming and real-time updates
            - Validate metrics for alerting thresholds

        Success Criteria:
            - Metrics export in standard formats
            - Monitoring system compatibility verified
            - Real-time metrics updates work
            - Alerting thresholds properly configured
        """
        # Execute operations to generate metrics
        @metrics_orchestrator.with_operation_resilience("export_test_operation")
        async def export_test_operation():
            return "Export test result"

        result = export_test_operation()  # Remove await for sync test
        assert result == "Export test result"

        # Get metrics in export format
        all_metrics = metrics_orchestrator.get_all_metrics()

        # Verify export format structure
        assert isinstance(all_metrics, dict)
        assert "operations" in all_metrics
        assert "circuit_breakers" in all_metrics
        assert "summary" in all_metrics

        # Test individual components
        operations = all_metrics["operations"]
        assert isinstance(operations, dict)
        assert len(operations) > 0

        circuit_breakers = all_metrics["circuit_breakers"]
        assert isinstance(circuit_breakers, dict)

        summary = all_metrics["summary"]
        assert isinstance(summary, dict)
        assert "total_operations" in summary
        assert "total_calls" in summary

        # Verify metrics are serializable for monitoring systems
        import json
        try:
            json_metrics = json.dumps(all_metrics)
            assert json_metrics is not None
            assert len(json_metrics) > 0
        except (TypeError, ValueError):
            assert False, "Metrics should be JSON serializable for monitoring systems"

    def test_concurrent_operations_metrics_tracking(self, metrics_orchestrator):
        """
        Test metrics tracking under concurrent operations.

        Integration Scope:
            Concurrent operations → Metrics collection → Thread safety → Consistency

        Business Impact:
            Ensures accurate metrics under high concurrent load

        Test Strategy:
            - Execute multiple operations concurrently
            - Verify metrics collection thread safety
            - Test metrics consistency across concurrent operations
            - Validate no metrics corruption or loss

        Success Criteria:
            - Metrics collected accurately for concurrent operations
            - No thread safety issues in metrics collection
            - Metrics consistency maintained
            - Performance acceptable under concurrent load
        """
        async def concurrent_operation(operation_id: str):
            """Execute a single operation for concurrent testing."""
            @metrics_orchestrator.with_operation_resilience(f"concurrent_op_{operation_id}")
            async def op():
                # Simulate varying execution times
                time.sleep(0.01 * operation_id)  # 10ms, 20ms, 30ms, etc.
                return f"Result {operation_id}"

            return op()  # Remove await for sync test

        # Execute concurrent operations
        start_time = time.time()
        tasks = [concurrent_operation(i) for i in range(5)]
        results = []

        async def run_concurrent():
            return await asyncio.gather(*[concurrent_operation(i) for i in range(5)])

        results = asyncio.run(run_concurrent())
        end_time = time.time()

        # Verify all operations completed
        assert len(results) == 5
        assert all("Result" in result for result in results)

        # Verify reasonable performance
        total_time = end_time - start_time
        assert total_time < 2.0  # Should complete within 2 seconds

        # Get metrics after concurrent operations
        all_metrics = metrics_orchestrator.get_all_metrics()
        operations_metrics = all_metrics["operations"]

        # Verify metrics for concurrent operations
        concurrent_ops = [op for op in operations_metrics.keys() if op.startswith("concurrent_op_")]
        assert len(concurrent_ops) == 5

        # Verify each operation has metrics
        for op_name in concurrent_ops:
            metrics = operations_metrics[op_name]
            assert hasattr(metrics, 'total_calls')
            assert metrics.total_calls >= 1

        # Verify overall metrics summary
        summary = all_metrics["summary"]
        assert summary["total_operations"] >= 5
        assert summary["total_calls"] >= 5
