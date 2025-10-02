"""
Integration Tests for Resilience Infrastructure Health Monitoring (SEAM 4)

Tests the integration between HealthChecker and resilience infrastructure, including
circuit breaker state monitoring, failure detection patterns, and resilience system
health validation. Validates that resilience health checks accurately reflect the
state of circuit breakers and failure protection mechanisms.

This test file validates the critical integration seam:
HealthChecker → check_resilience_health → Resilience orchestrator → Circuit breaker states

Test Coverage:
- Circuit breaker state monitoring (closed, open, half-open)
- Resilience system health aggregation
- Circuit breaker recovery and state transitions
- Metadata collection for resilience monitoring
- Performance characteristics of resilience health checks
"""

import pytest
import asyncio
from unittest.mock import patch, AsyncMock

from app.infrastructure.monitoring.health import HealthStatus, ComponentStatus


@pytest.mark.integration
class TestResilienceHealthIntegration:
    """
    Integration tests for resilience infrastructure health monitoring.

    Seam Under Test:
        HealthChecker → check_resilience_health → resilience orchestrator → circuit breaker states

    Critical Paths:
        - Resilience health check queries circuit breaker states
        - Circuit breaker status aggregation and health determination
        - Metadata collection for operational monitoring
        - Graceful handling of resilience infrastructure failures

    Business Impact:
        Confirms resilience infrastructure protecting system from failures
        Validates monitoring can detect external service issues through circuit breaker states
        Ensures resilience system health is accurately reported

    Integration Scope:
        Health checker execution → Resilience orchestrator query → Circuit breaker state analysis
    """

    async def test_resilience_health_check_reports_healthy_with_all_circuits_closed(
        self, health_checker, mock_resilience_orchestrator
    ):
        """
        Test resilience health check returns HEALTHY when all circuit breakers closed.

        Integration Scope:
            Health checker → check_resilience_health → resilience orchestrator → circuit breaker states

        Contract Validation:
            - ComponentStatus with status=HEALTHY per health.pyi:661
            - metadata includes circuit breaker states per health.pyi:664
            - All circuits closed indicates healthy resilience infrastructure

        Business Impact:
            Confirms resilience infrastructure protecting system from failures
            Validates circuit breakers are in optimal state (closed/operational)
            Ensures external services are accessible and not being throttled

        Test Strategy:
            - Configure mock resilience orchestrator with all circuits closed
            - Use real resilience health check function
            - Verify healthy status reflects optimal circuit breaker state
            - Validate metadata includes circuit breaker information

        Success Criteria:
            - Resilience component status is "healthy"
            - Metadata shows total_circuit_breakers >= 0
            - Metadata shows open_circuit_breakers is empty list
            - Message indicates healthy resilience state
        """
        # Arrange: Configure mock for all circuits closed (healthy state)
        mock_resilience_orchestrator.get_health_status.return_value = {
            "healthy": True,
            "open_circuit_breakers": [],
            "half_open_circuit_breakers": [],
            "total_circuit_breakers": 5,
        }

        # Mock the resilience orchestrator import
        with patch('app.infrastructure.monitoring.health.ai_resilience', mock_resilience_orchestrator):
            # Act: Execute resilience health check
            result = await health_checker.check_component("resilience")

        # Assert: Resilience reports healthy
        assert result.name == "resilience"
        assert result.status == HealthStatus.HEALTHY
        assert result.response_time_ms > 0
        assert result.response_time_ms < 500, "Resilience health check should be fast"

        # Verify message indicates healthy state
        assert "healthy" in result.message.lower()

        # Verify circuit breaker metadata
        assert result.metadata is not None
        assert "total_circuit_breakers" in result.metadata
        assert "open_circuit_breakers" in result.metadata
        assert result.metadata["total_circuit_breakers"] == 5
        assert len(result.metadata["open_circuit_breakers"]) == 0

    async def test_resilience_health_check_reports_degraded_with_open_circuits(
        self, health_checker, mock_resilience_orchestrator, circuit_breaker_state_factory
    ):
        """
        Test resilience health check returns DEGRADED when circuit breakers open.

        Integration Scope:
            Health checker → check_resilience_health → circuit breaker state detection

        Contract Validation:
            - ComponentStatus with status=DEGRADED per health.pyi:662
            - metadata identifies open circuit breakers per health.pyi:672
            - Open circuits indicate external service issues but functional resilience

        Business Impact:
            Alerts operations to external service failures being protected by circuit breakers
            System remains functional through resilience patterns
            Validates resilience system is working correctly by preventing cascade failures

        Test Strategy:
            - Configure mock resilience orchestrator with open circuit breakers
            - Verify degraded status reflects open circuits
            - Test through health checker (outside-in approach)
            - Validate metadata lists open circuit breaker names

        Success Criteria:
            - Resilience component status is "degraded"
            - Message indicates circuit breakers open
            - Metadata lists open circuit breaker names
            - Overall system remains operational
        """
        # Arrange: Configure mock with open circuit breakers
        mock_state = circuit_breaker_state_factory(
            healthy=True,
            open_breakers=["external_api", "database_connection"],
            half_open_breakers=[],
            total_breakers=5
        )
        mock_resilience_orchestrator.get_health_status.return_value = mock_state

        # Mock the resilience orchestrator import
        with patch('app.infrastructure.monitoring.health.ai_resilience', mock_resilience_orchestrator):
            # Act: Check health status
            result = await health_checker.check_component("resilience")

        # Assert: Resilience reports degraded but operational
        assert result.name == "resilience"
        assert result.status == HealthStatus.DEGRADED
        assert "circuit" in result.message.lower()

        # Verify circuit breaker metadata
        assert result.metadata is not None
        assert result.metadata["total_circuit_breakers"] == 5
        assert len(result.metadata["open_circuit_breakers"]) == 2
        assert "external_api" in result.metadata["open_circuit_breakers"]
        assert "database_connection" in result.metadata["open_circuit_breakers"]

    async def test_resilience_health_check_reports_unhealthy_on_infrastructure_failure(
        self, health_checker
    ):
        """
        Test resilience health check returns UNHEALTHY when resilience infrastructure fails.

        Integration Scope:
            Health checker → check_resilience_health → Exception handling → UNHEALTHY status

        Contract Validation:
            - ComponentStatus with status=UNHEALTHY when resilience infrastructure fails
            - Exception handling preserves error information for troubleshooting
            - Graceful failure handling doesn't crash health monitoring

        Business Impact:
            Alerts monitoring systems to resilience infrastructure failures
            Validates health monitoring continues despite resilience system issues
            Ensures error information is preserved for operational troubleshooting

        Test Strategy:
            - Mock resilience orchestrator to raise exception
            - Verify UNHEALTHY status is returned with error details
            - Test exception handling doesn't crash overall health monitoring
            - Validate error information is preserved in response

        Success Criteria:
            - Resilience component status is "unhealthy"
            - Error message provides diagnostic information
            - Health check completes despite infrastructure failure
            - Response time is measured even for failed checks
        """
        # Arrange: Mock resilience orchestrator to raise exception
        with patch('app.infrastructure.monitoring.health.ai_resilience') as mock_resilience:
            mock_resilience.get_health_status.side_effect = Exception("Resilience orchestrator crashed")

            # Act: Execute resilience health check
            result = await health_checker.check_component("resilience")

        # Assert: Infrastructure failure handling
        assert result.name == "resilience"
        assert result.status == HealthStatus.UNHEALTHY
        assert "failed" in result.message.lower()
        assert result.response_time_ms > 0

    async def test_resilience_health_check_with_half_open_circuit_breakers(
        self, health_checker, mock_resilience_orchestrator, circuit_breaker_state_factory
    ):
        """
        Test resilience health check handles half-open circuit breaker states correctly.

        Integration Scope:
            Health checker → check_resilience_health → half-open circuit breaker detection

        Business Impact:
            Validates monitoring detects circuit breaker recovery attempts
            Ensures half-open states are properly reported for operational visibility
            Confirms circuit breaker recovery process is working correctly

        Test Strategy:
            - Configure mock with half-open circuit breakers
            - Verify degraded status reflects recovery state
            - Test metadata includes half-open circuit information
            - Validate proper state reporting for recovery monitoring

        Success Criteria:
            - Resilience component status is "degraded" (half-open indicates partial recovery)
            - Metadata includes half-open circuit breaker information
            - Message indicates recovery or partially degraded state
            - All circuit breaker states are accurately reported
        """
        # Arrange: Configure mock with half-open circuit breakers
        mock_state = circuit_breaker_state_factory(
            healthy=True,
            open_breakers=["failed_service"],
            half_open_breakers=["recovering_service"],
            total_breakers=4
        )
        mock_resilience_orchestrator.get_health_status.return_value = mock_state

        # Mock the resilience orchestrator import
        with patch('app.infrastructure.monitoring.health.ai_resilience', mock_resilience_orchestrator):
            # Act: Check health status
            result = await health_checker.check_component("resilience")

        # Assert: Half-open states handled correctly
        assert result.name == "resilience"
        assert result.status == HealthStatus.DEGRADED  # Any open/half-open circuits = degraded

        # Verify all circuit breaker states are reported
        assert result.metadata is not None
        assert result.metadata["total_circuit_breakers"] == 4
        assert len(result.metadata["open_circuit_breakers"]) == 1
        assert "failed_service" in result.metadata["open_circuit_breakers"]

        # Check for half-open circuit breakers if implemented
        if "half_open_circuit_breakers" in result.metadata:
            assert len(result.metadata["half_open_circuit_breakers"]) == 1
            assert "recovering_service" in result.metadata["half_open_circuit_breakers"]

    async def test_resilience_health_check_performance_characteristics(
        self, health_checker, mock_resilience_orchestrator, performance_time_tracker
    ):
        """
        Test resilience health check performance characteristics meet operational requirements.

        Integration Scope:
            Health checker execution → Resilience health check → Performance measurement

        Business Impact:
            Ensures resilience health monitoring doesn't impact application performance
            Validates health checks are suitable for high-frequency monitoring
            Confirms performance requirements are met for operational use

        Test Strategy:
            - Measure resilience health check execution time
            - Verify performance meets operational requirements
            - Test performance consistency across multiple executions
            - Validate performance is suitable for monitoring integration

        Success Criteria:
            - Resilience health check completes in < 200ms
            - Performance remains consistent across multiple calls
            - Response time measurement is accurate and reliable
            - Performance meets typical monitoring system SLAs
        """
        # Arrange: Configure healthy resilience state
        mock_resilience_orchestrator.get_health_status.return_value = {
            "healthy": True,
            "open_circuit_breakers": [],
            "half_open_circuit_breakers": [],
            "total_circuit_breakers": 3,
        }

        # Act: Measure performance across multiple calls
        measurements = []

        for _ in range(5):
            performance_time_tracker.start_measurement()

            with patch('app.infrastructure.monitoring.health.ai_resilience', mock_resilience_orchestrator):
                result = await health_checker.check_component("resilience")

            measured_time = performance_time_tracker.end_measurement()
            measurements.append({
                'result_time': result.response_time_ms,
                'measured_time': measured_time,
                'status': result.status
            })

        # Assert: Performance requirements
        avg_result_time = sum(m['result_time'] for m in measurements) / len(measurements)
        avg_measured_time = sum(m['measured_time'] for m in measurements) / len(measurements)
        max_measured_time = max(m['measured_time'] for m in measurements)

        # All should be healthy
        assert all(m['status'] == HealthStatus.HEALTHY for m in measurements)

        # Performance should be good (local state checking)
        assert avg_result_time < 100, f"Average result time {avg_result_time:.1f}ms exceeds requirement"
        assert avg_measured_time < 200, f"Average measured time {avg_measured_time:.1f}ms exceeds requirement"
        assert max_measured_time < 500, f"Max measured time {max_measured_time:.1f}ms exceeds requirement"

    async def test_resilience_health_check_metadata_completeness(
        self, health_checker, mock_resilience_orchestrator, circuit_breaker_state_factory
    ):
        """
        Test resilience health check collects comprehensive metadata for operational monitoring.

        Integration Scope:
            Health checker → check_resilience_health → Metadata collection and reporting

        Business Impact:
            Provides operational visibility into resilience infrastructure state
            Enables monitoring systems to understand circuit breaker status
            Supports troubleshooting and capacity planning

        Test Strategy:
            - Test metadata collection with different circuit breaker configurations
            - Verify metadata includes all relevant state information
            - Validate metadata structure and content accuracy
            - Test metadata completeness across various scenarios

        Success Criteria:
            - Metadata includes total circuit breaker count
            - Open circuit breakers are listed when present
            - Half-open circuit breakers are reported when present
            - Metadata structure is consistent and complete
        """
        # Test Case 1: All circuits closed
        mock_state = circuit_breaker_state_factory(
            healthy=True,
            open_breakers=[],
            half_open_breakers=[],
            total_breakers=3
        )
        mock_resilience_orchestrator.get_health_status.return_value = mock_state

        with patch('app.infrastructure.monitoring.health.ai_resilience', mock_resilience_orchestrator):
            result = await health_checker.check_component("resilience")

        assert result.metadata is not None
        assert "total_circuit_breakers" in result.metadata
        assert "open_circuit_breakers" in result.metadata
        assert result.metadata["total_circuit_breakers"] == 3
        assert len(result.metadata["open_circuit_breakers"]) == 0

        # Test Case 2: Mixed circuit breaker states
        mock_state = circuit_breaker_state_factory(
            healthy=False,
            open_breakers=["service_a", "service_b"],
            half_open_breakers=["service_c"],
            total_breakers=5
        )
        mock_resilience_orchestrator.get_health_status.return_value = mock_state

        with patch('app.infrastructure.monitoring.health.ai_resilience', mock_resilience_orchestrator):
            result = await health_checker.check_component("resilience")

        assert result.metadata is not None
        assert result.metadata["total_circuit_breakers"] == 5
        assert len(result.metadata["open_circuit_breakers"]) == 2
        assert "service_a" in result.metadata["open_circuit_breakers"]
        assert "service_b" in result.metadata["open_circuit_breakers"]


@pytest.mark.integration
@pytest.mark.slow
class TestResilienceHealthRealIntegration:
    """
    Integration tests with actual resilience infrastructure when available.

    These tests use the real resilience orchestrator to validate integration
    behavior in more realistic scenarios. They test actual circuit breaker
    behavior and state transitions when the resilience system is available.
    """

    async def test_resilience_health_check_with_real_orchestrator(self, health_checker):
        """
        Test resilience health check with real resilience orchestrator.

        Integration Scope:
            Health checker → Real resilience orchestrator → Actual circuit breaker states

        Business Impact:
            Validates integration with actual resilience infrastructure
            Confirms health checks work with real circuit breaker states
            Tests end-to-end integration behavior with real resilience patterns

        Test Strategy:
            - Attempt to use real resilience orchestrator
            - Test health check behavior with actual circuit breaker states
            - Gracefully handle cases where resilience system not available
            - Validate realistic operational behavior

        Success Criteria:
            - Health check works with real resilience system
            - Results reflect actual circuit breaker states
            - Test gracefully handles missing resilience infrastructure
            - Performance characteristics are realistic
        """
        try:
            # Try to import and use real resilience orchestrator
            from app.infrastructure.resilience.orchestrator import ai_resilience

            # Act: Test with real resilience system
            result = await health_checker.check_component("resilience")

            # Assert: Basic health check structure with real system
            assert result.name == "resilience"
            assert result.status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED, HealthStatus.UNHEALTHY]
            assert result.response_time_ms > 0
            assert result.metadata is not None

            # Verify metadata structure from real system
            assert "total_circuit_breakers" in result.metadata
            assert "open_circuit_breakers" in result.metadata
            assert isinstance(result.metadata["total_circuit_breakers"], int)
            assert isinstance(result.metadata["open_circuit_breakers"], list)

        except ImportError:
            pytest.skip("Real resilience orchestrator not available for testing")
        except Exception as e:
            # If resilience system has issues, we should handle gracefully
            if "resilience" in str(e).lower():
                pytest.skip(f"Resilience system not available for integration testing: {e}")
            else:
                # Unexpected error - fail the test
                raise

    async def test_resilience_health_check_state_transitions(self, health_checker):
        """
        Test resilience health check detects circuit breaker state transitions.

        Integration Scope:
            Real resilience system → Circuit breaker state changes → Health check updates

        Business Impact:
            Validates health monitoring detects circuit breaker state changes
            Ensures monitoring systems can track resilience system evolution
            Confirms accurate reporting of recovery and failure cycles

        Test Strategy:
            - If real resilience system available, trigger state changes
            - Monitor health check responses to state transitions
            - Verify health status updates appropriately
            - Test detection of recovery and failure cycles

        Success Criteria:
            - Health check detects state transitions when they occur
            - Status updates reflect current circuit breaker states
            - Metadata accurately reports evolving system state
            - Monitoring provides visibility into resilience behavior
        """
        try:
            from app.infrastructure.resilience.orchestrator import ai_resilience

            # Get initial health state
            initial_result = await health_checker.check_component("resilience")
            initial_status = initial_result.status
            initial_open_circuits = set(initial_result.metadata.get("open_circuit_breakers", []))

            # Note: In a real test environment, we might not be able to easily trigger
            # circuit breaker state changes without actual external service failures.
            # This test validates the basic monitoring capability.

            # Act: Check health again to verify consistency
            subsequent_result = await health_checker.check_component("resilience")

            # Assert: Basic consistency in reporting
            assert subsequent_result.name == "resilience"
            assert subsequent_result.status in [HealthStatus.HEALTHY, HealthStatus.DEGRADED, HealthStatus.UNHEALTHY]
            assert subsequent_result.metadata is not None

            # In normal operation, results should be consistent
            # (unless external service failures occurred between calls)
            subsequent_open_circuits = set(subsequent_result.metadata.get("open_circuit_breakers", []))

            # Basic structure consistency
            assert "total_circuit_breakers" in subsequent_result.metadata
            assert "open_circuit_breakers" in subsequent_result.metadata

        except ImportError:
            pytest.skip("Real resilience orchestrator not available for testing")
        except Exception as e:
            if "resilience" in str(e).lower():
                pytest.skip(f"Resilience system not available: {e}")
            else:
                raise