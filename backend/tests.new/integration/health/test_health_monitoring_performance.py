"""
Integration tests for health monitoring performance and metrics.

These tests verify the integration between health monitoring system
performance characteristics and metrics collection, ensuring health
monitoring doesn't become a performance bottleneck while providing
valuable operational metrics.

MEDIUM PRIORITY - System performance optimization
"""

import pytest
import time
import asyncio
from unittest.mock import patch

from app.infrastructure.monitoring.health import (
    HealthChecker,
    HealthStatus,
    ComponentStatus,
)


class TestHealthMonitoringPerformanceMetrics:
    """
    Integration tests for health monitoring performance and metrics.

    Seam Under Test:
        HealthChecker → Performance measurement → Response time tracking → Metrics collection

    Critical Path:
        Health check execution → Performance measurement → Metrics collection →
        Performance analysis → Optimization

    Business Impact:
        Ensures health monitoring doesn't become a performance bottleneck
        while providing valuable metrics, maintaining operational visibility
        without impacting system performance.

    Test Strategy:
        - Test health check performance characteristics
        - Verify response time measurement and tracking
        - Test metrics collection and aggregation
        - Validate performance under various load conditions
        - Test performance optimization and efficiency

    Success Criteria:
        - Health check response times are reasonable for monitoring frequency
        - Performance measurement is accurate and consistent
        - Metrics collection doesn't impact performance significantly
        - System remains responsive during health monitoring
        - Performance characteristics support operational requirements
    """

    def test_health_check_individual_component_performance_characteristics(
        self, health_checker
    ):
        """
        Test individual component health check performance characteristics.

        Integration Scope:
            HealthChecker → Component health check → Performance measurement → Timing validation

        Business Impact:
            Ensures individual health checks complete within performance
            requirements, maintaining monitoring system responsiveness
            and preventing monitoring delays.

        Test Strategy:
            - Execute individual component health checks
            - Measure and validate response time characteristics
            - Verify performance meets operational requirements
            - Confirm timing accuracy and consistency

        Success Criteria:
            - Individual health checks complete within expected time
            - Response time measurement is accurate
            - Performance is consistent across multiple calls
            - Timing characteristics support monitoring frequency
        """
        # Register different types of health checks
        async def fast_check():
            return ComponentStatus("fast", HealthStatus.HEALTHY, "Fast component")

        async def medium_check():
            await asyncio.sleep(0.05)  # 50ms delay
            return ComponentStatus("medium", HealthStatus.HEALTHY, "Medium component")

        async def measured_check():
            start_time = time.time()
            await asyncio.sleep(0.1)   # 100ms delay
            end_time = time.time()
            measured_time = (end_time - start_time) * 1000
            return ComponentStatus("measured", HealthStatus.HEALTHY, f"Measured {measured_time:.1f}ms")

        health_checker.register_check("fast", fast_check)
        health_checker.register_check("medium", medium_check)
        health_checker.register_check("measured", measured_check)

        # Test fast component performance
        start_time = time.time()
        fast_result = await health_checker.check_component("fast")
        fast_time = time.time() - start_time

        # Test medium component performance
        start_time = time.time()
        medium_result = await health_checker.check_component("medium")
        medium_time = time.time() - start_time

        # Test measured component performance
        start_time = time.time()
        measured_result = await health_checker.check_component("measured")
        measured_time = time.time() - start_time

        # Verify performance characteristics
        assert fast_result.name == "fast"
        assert fast_result.status == HealthStatus.HEALTHY
        assert fast_time < 0.05  # Fast check should be very quick

        assert medium_result.name == "medium"
        assert medium_result.status == HealthStatus.HEALTHY
        assert 0.04 < medium_time < 0.15  # Should include the 50ms delay + overhead

        assert measured_result.name == "measured"
        assert measured_result.status == HealthStatus.HEALTHY
        assert 0.09 < measured_time < 0.2   # Should include the 100ms delay + overhead

    def test_health_check_system_wide_performance_aggregation(
        self, health_checker
    ):
        """
        Test system-wide health check performance aggregation.

        Integration Scope:
            HealthChecker → System health check → Performance aggregation → Timing analysis

        Business Impact:
            Ensures comprehensive system health checks complete within
            reasonable time limits, maintaining monitoring system
            efficiency during full system assessments.

        Test Strategy:
            - Execute comprehensive system health check
            - Measure total system health check time
            - Verify performance meets system-wide requirements
            - Confirm aggregation doesn't cause excessive delays

        Success Criteria:
            - System health check completes within performance limits
            - Performance scales appropriately with component count
            - Response time characteristics support operational needs
            - Aggregation maintains reasonable performance overhead
        """
        # Register multiple components
        async def component_check(component_id):
            await asyncio.sleep(0.01)  # Small delay for each component
            return ComponentStatus(f"comp_{component_id}", HealthStatus.HEALTHY, f"Component {component_id}")

        for i in range(5):
            health_checker.register_check(f"component_{i}", lambda i=i: component_check(i))

        # Execute system-wide health check
        start_time = time.time()
        system_health = await health_checker.check_all_components()
        total_time = time.time() - start_time

        # Verify system-wide performance
        assert isinstance(system_health.overall_status, HealthStatus)
        assert system_health.overall_status == HealthStatus.HEALTHY
        assert len(system_health.components) == 5
        assert total_time < 1.0  # Should complete within 1 second for 5 components

        # Verify individual component timing
        for component in system_health.components:
            assert component.status == HealthStatus.HEALTHY
            assert component.response_time_ms > 0
            assert component.response_time_ms < 200  # Individual checks should be fast

    def test_health_check_performance_under_failure_conditions(
        self, health_checker
    ):
        """
        Test health check performance under various failure conditions.

        Integration Scope:
            HealthChecker → Failure conditions → Performance monitoring → Resilience validation

        Business Impact:
            Ensures health monitoring performance remains acceptable even
            during component failures, maintaining monitoring visibility
            when the system is experiencing issues.

        Test Strategy:
            - Execute health checks under various failure scenarios
            - Measure performance impact of different failure types
            - Verify performance characteristics during failures
            - Confirm system remains responsive despite failures

        Success Criteria:
            - Performance remains acceptable during failures
            - Different failure types don't cause excessive delays
            - Response time characteristics are predictable
            - System maintains performance even under stress
        """
        # Register components with different failure characteristics
        async def fast_failure():
            raise Exception("Fast failure")

        async def slow_failure():
            await asyncio.sleep(0.2)  # 200ms delay before failure
            raise Exception("Slow failure")

        async def timeout_failure():
            await asyncio.sleep(1)     # Would timeout but fail first
            raise Exception("Timeout failure")

        health_checker.register_check("fast_fail", fast_failure)
        health_checker.register_check("slow_fail", slow_failure)
        health_checker.register_check("timeout_fail", timeout_failure)

        # Test performance under different failure conditions
        start_time = time.time()
        results = []
        for component_name in ["fast_fail", "slow_fail", "timeout_fail"]:
            component_start = time.time()
            result = await health_checker.check_component(component_name)
            component_time = time.time() - component_start
            results.append((result, component_time))

        total_time = time.time() - start_time

        # Verify performance under failure conditions
        assert total_time < 2.0  # Should complete within 2 seconds despite failures

        # Verify individual failure characteristics
        for result, component_time in results:
            assert result.status in [HealthStatus.DEGRADED, HealthStatus.UNHEALTHY]
            assert component_time > 0
            assert component_time < 0.5  # Each should be reasonably fast

    def test_health_check_performance_metrics_collection_efficiency(
        self, health_checker
    ):
        """
        Test health check performance metrics collection efficiency.

        Integration Scope:
            HealthChecker → Performance metrics → Collection efficiency → Metrics overhead

        Business Impact:
            Ensures performance metrics collection doesn't significantly
            impact health check response times, maintaining monitoring
            efficiency while providing valuable performance data.

        Test Strategy:
            - Execute health checks with and without metrics collection
            - Measure performance overhead of metrics collection
            - Verify metrics collection efficiency
            - Confirm metrics don't cause excessive performance impact

        Success Criteria:
            - Metrics collection adds minimal performance overhead
            - Response time impact is reasonable and acceptable
            - Metrics collection works efficiently
            - Performance characteristics remain good with metrics
        """
        # Create health check with detailed performance measurement
        async def metrics_check():
            check_start = time.time()

            # Simulate some work
            await asyncio.sleep(0.05)

            check_end = time.time()
            check_duration = (check_end - check_start) * 1000

            return ComponentStatus(
                "metrics",
                HealthStatus.HEALTHY,
                f"Metrics check completed in {check_duration:.2f}ms"
            )

        health_checker.register_check("metrics", metrics_check)

        # Execute multiple times to measure consistency
        execution_times = []
        for i in range(10):
            start_time = time.time()
            result = await health_checker.check_component("metrics")
            end_time = time.time()

            execution_times.append((end_time - start_time) * 1000)
            assert result.status == HealthStatus.HEALTHY

        # Verify metrics collection efficiency
        avg_execution_time = sum(execution_times) / len(execution_times)
        max_execution_time = max(execution_times)
        min_execution_time = min(execution_times)

        # Metrics collection should add minimal overhead
        assert avg_execution_time < 100  # Average under 100ms
        assert max_execution_time < 200  # Max under 200ms
        assert max_execution_time - min_execution_time < 50  # Low variance

    def test_health_check_performance_scaling_with_component_count(
        self
    ):
        """
        Test health check performance scaling with increasing component count.

        Integration Scope:
            HealthChecker → Component scaling → Performance scaling → Scalability validation

        Business Impact:
            Ensures health monitoring performance scales appropriately
            as component count increases, maintaining monitoring
            capabilities as the system grows.

        Test Strategy:
            - Test with increasing numbers of components
            - Measure performance scaling characteristics
            - Verify performance remains acceptable at scale
            - Confirm system can handle realistic component counts

        Success Criteria:
            - Performance scales reasonably with component count
            - Response times don't grow excessively with scale
            - System handles realistic monitoring scenarios
            - Performance characteristics support operational scaling
        """
        # Test with different component counts
        test_scenarios = [
            {"component_count": 1, "description": "Single component"},
            {"component_count": 5, "description": "Few components"},
            {"component_count": 10, "description": "Many components"},
        ]

        for scenario in test_scenarios:
            # Create health checker for this scenario
            checker = HealthChecker(default_timeout_ms=2000)

            # Register components
            async def generic_check(component_id):
                await asyncio.sleep(0.01)  # Small delay per component
                return ComponentStatus(f"comp_{component_id}", HealthStatus.HEALTHY, f"Component {component_id}")

            for i in range(scenario["component_count"]):
                checker.register_check(f"component_{i}", lambda i=i: generic_check(i))

            # Execute system health check
            start_time = time.time()
            system_health = await checker.check_all_components()
            total_time = time.time() - start_time

            # Verify performance scaling
            assert len(system_health.components) == scenario["component_count"]
            assert system_health.overall_status == HealthStatus.HEALTHY

            # Performance should scale roughly linearly with component count
            expected_max_time = scenario["component_count"] * 0.05  # 50ms per component
            assert total_time < expected_max_time, f"Performance degraded for {scenario['description']}"

    def test_health_check_performance_under_concurrent_load(
        self, health_checker
    ):
        """
        Test health check performance under concurrent load conditions.

        Integration Scope:
            HealthChecker → Concurrent execution → Performance monitoring → Load handling

        Business Impact:
            Ensures health monitoring can handle concurrent health check
            requests efficiently, maintaining performance during
            peak monitoring periods.

        Test Strategy:
            - Execute multiple concurrent health check requests
            - Measure performance under concurrent load
            - Verify system handles concurrent requests efficiently
            - Confirm performance characteristics under load

        Success Criteria:
            - Concurrent requests are handled efficiently
            - Performance doesn't degrade excessively under load
            - Response times remain acceptable for concurrent scenarios
            - System maintains stability under concurrent load
        """
        # Register health check that can handle concurrent execution
        async def concurrent_safe_check():
            # Simulate work that can run concurrently
            await asyncio.sleep(0.05)
            return ComponentStatus("concurrent", HealthStatus.HEALTHY, "Concurrent safe")

        health_checker.register_check("concurrent", concurrent_safe_check)

        # Execute concurrent health checks
        start_time = time.time()

        # Create multiple concurrent tasks
        tasks = []
        for i in range(5):
            task = health_checker.check_component("concurrent")
            tasks.append(task)

        # Wait for all to complete
        results = await asyncio.gather(*tasks)
        total_time = time.time() - start_time

        # Verify concurrent performance
        assert len(results) == 5
        assert total_time < 1.0  # All concurrent requests should complete quickly

        for result in results:
            assert result.name == "concurrent"
            assert result.status == HealthStatus.HEALTHY

    def test_health_check_performance_optimization_and_efficiency(
        self, health_checker
    ):
        """
        Test health check performance optimization and efficiency measures.

        Integration Scope:
            HealthChecker → Performance optimization → Efficiency measurement → Optimization validation

        Business Impact:
            Ensures health monitoring system is optimized for performance
            and efficiency, providing fast and lightweight monitoring
            capabilities without unnecessary overhead.

        Test Strategy:
            - Test performance optimization measures
            - Verify efficiency of health check execution
            - Measure optimization effectiveness
            - Confirm performance meets optimization goals

        Success Criteria:
            - Performance optimizations are effective
            - Efficiency measures work as intended
            - Response times meet optimization targets
            - System performance is optimized for monitoring use cases
        """
        # Create optimized health check
        async def optimized_check():
            # Minimal work for maximum efficiency
            return ComponentStatus("optimized", HealthStatus.HEALTHY, "Optimized performance")

        health_checker.register_check("optimized", optimized_check)

        # Test optimized performance
        start_time = time.time()
        result = await health_checker.check_component("optimized")
        optimized_time = time.time() - start_time

        # Test less optimized version for comparison
        async def less_optimized_check():
            # More work that could be optimized
            data = list(range(100))  # Unnecessary work
            await asyncio.sleep(0.001)  # Small delay
            return ComponentStatus("less_optimized", HealthStatus.HEALTHY, f"Less optimized: {len(data)} items")

        health_checker.register_check("less_optimized", less_optimized_check)

        start_time = time.time()
        result2 = await health_checker.check_component("less_optimized")
        less_optimized_time = time.time() - start_time

        # Verify optimization effectiveness
        assert result.name == "optimized"
        assert result.status == HealthStatus.HEALTHY
        assert result2.name == "less_optimized"
        assert result2.status == HealthStatus.HEALTHY

        # Optimized version should be faster
        assert optimized_time < less_optimized_time
        assert optimized_time < 0.01  # Optimized should be very fast
        assert less_optimized_time < 0.05  # Less optimized should still be reasonable

    def test_health_check_performance_monitoring_and_reporting(
        self, health_checker
    ):
        """
        Test health check performance monitoring and reporting capabilities.

        Integration Scope:
            HealthChecker → Performance monitoring → Reporting → Metrics analysis

        Business Impact:
            Ensures health monitoring provides comprehensive performance
            monitoring and reporting, enabling operators to track
            monitoring system performance over time.

        Test Strategy:
            - Execute health checks with performance monitoring
            - Verify performance data collection and reporting
            - Test performance metrics analysis capabilities
            - Confirm monitoring system self-awareness

        Success Criteria:
            - Performance data is collected and available
            - Performance metrics are accurate and useful
            - Performance reporting provides operational insights
            - Monitoring system has performance self-awareness
        """
        # Create health check with performance self-monitoring
        async def performance_monitored_check():
            check_start = time.time()

            # Simulate monitored work
            await asyncio.sleep(0.02)  # 20ms of work

            check_end = time.time()
            check_duration = (check_end - check_start) * 1000

            # Return performance information in result
            return ComponentStatus(
                "performance_monitored",
                HealthStatus.HEALTHY,
                f"Performance monitored: {check_duration:.2f}ms execution time"
            )

        health_checker.register_check("performance_monitored", performance_monitored_check)

        # Execute with performance monitoring
        start_time = time.time()
        result = await health_checker.check_component("performance_monitored")
        monitoring_time = time.time() - start_time

        # Verify performance monitoring and reporting
        assert result.name == "performance_monitored"
        assert result.status == HealthStatus.HEALTHY
        assert "Performance monitored" in result.message
        assert "ms execution time" in result.message

        # Verify performance data accuracy
        execution_time_match = result.message.split("ms execution time")[0].split()[-1]
        execution_time = float(execution_time_match)
        assert 15 < execution_time < 30  # Should be close to our 20ms work

        # Total monitoring time should include execution time plus overhead
        assert monitoring_time > execution_time / 1000  # Convert to seconds for comparison
        assert monitoring_time < execution_time / 1000 + 0.1  # Should not have excessive overhead

    def test_health_check_performance_characteristics_summary(
        self, health_checker
    ):
        """
        Test comprehensive health check performance characteristics summary.

        Integration Scope:
            HealthChecker → Performance characteristics → Summary validation → Performance overview

        Business Impact:
            Ensures comprehensive understanding of health monitoring
            performance characteristics, providing operators with
            complete performance visibility and optimization insights.

        Test Strategy:
            - Test various performance scenarios
            - Validate performance characteristics across scenarios
            - Provide comprehensive performance summary
            - Confirm performance meets operational requirements

        Success Criteria:
            - Performance characteristics are well understood
            - All performance scenarios meet requirements
            - Performance summary provides actionable insights
            - System performance supports operational monitoring needs
        """
        # Test comprehensive performance scenarios
        performance_scenarios = {
            "individual_fast": 0.01,    # 10ms target
            "individual_medium": 0.05,  # 50ms target
            "system_small": 0.1,        # 100ms target for small system
            "system_large": 0.5,        # 500ms target for large system
            "concurrent": 0.2,          # 200ms target for concurrent
        }

        # Execute comprehensive performance testing
        results = {}

        # Test individual component performance
        async def fast_check():
            return ComponentStatus("fast", HealthStatus.HEALTHY, "Fast")

        async def medium_check():
            await asyncio.sleep(0.02)
            return ComponentStatus("medium", HealthStatus.HEALTHY, "Medium")

        health_checker.register_check("fast", fast_check)
        health_checker.register_check("medium", medium_check)

        # Test individual performance
        start_time = time.time()
        fast_result = await health_checker.check_component("fast")
        fast_time = time.time() - start_time
        results["individual_fast"] = fast_time

        start_time = time.time()
        medium_result = await health_checker.check_component("medium")
        medium_time = time.time() - start_time
        results["individual_medium"] = medium_time

        # Test system performance
        start_time = time.time()
        system_health = await health_checker.check_all_components()
        system_time = time.time() - start_time
        results["system_small"] = system_time

        # Add more components for larger system test
        for i in range(8):  # Total 10 components
            async def component_check(i):
                await asyncio.sleep(0.01)
                return ComponentStatus(f"comp_{i}", HealthStatus.HEALTHY, f"Component {i}")
            health_checker.register_check(f"comp_{i}", lambda i=i: component_check(i))

        start_time = time.time()
        large_system_health = await health_checker.check_all_components()
        large_system_time = time.time() - start_time
        results["system_large"] = large_system_time

        # Test concurrent performance
        tasks = [health_checker.check_component("fast") for _ in range(3)]
        start_time = time.time()
        concurrent_results = await asyncio.gather(*tasks)
        concurrent_time = time.time() - start_time
        results["concurrent"] = concurrent_time

        # Verify comprehensive performance characteristics
        assert fast_time < performance_scenarios["individual_fast"] + 0.01
        assert medium_time < performance_scenarios["individual_medium"] + 0.02
        assert system_time < performance_scenarios["system_small"] + 0.05
        assert large_system_time < performance_scenarios["system_large"] + 0.2
        assert concurrent_time < performance_scenarios["concurrent"] + 0.05

        # Verify all results are valid
        assert fast_result.status == HealthStatus.HEALTHY
        assert medium_result.status == HealthStatus.HEALTHY
        assert len(system_health.components) == 2
        assert len(large_system_health.components) == 10
        assert len(concurrent_results) == 3

        # Verify performance meets operational requirements
        assert all(time_val < max_time + 0.05 for time_val, max_time in zip(results.values(), performance_scenarios.values()))
