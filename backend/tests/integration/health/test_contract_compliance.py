"""
Health Check Contract Compliance Integration Tests

This module contains contract-based integration tests that validate all health check functions
follow the ComponentStatus contract defined in health.pyi. These tests ensure consistent
health monitoring interface across all components and verify metadata provides actionable
diagnostic information for operations teams.

Test Coverage:
- C.1: Health Check Function Contract Compliance
- C.2: Health Check Metadata Contract
"""

import pytest
from app.infrastructure.monitoring.health import (
    check_ai_model_health,
    check_cache_health,
    check_resilience_health,
    HealthStatus,
    ComponentStatus,
)


class TestHealthCheckContractCompliance:
    """
    Integration tests for health monitoring system contract compliance.

    Seam Under Test:
        Individual health check functions → ComponentStatus contract compliance

    Critical Paths:
        - All health check functions return valid ComponentStatus per contract
        - Health check metadata contains diagnostic information when present

    Business Impact:
        Ensures consistent health monitoring interface across all infrastructure components,
        enabling reliable operational monitoring and alerting systems. Contract compliance
        guarantees that health monitoring infrastructure behaves predictably across
        different component types and implementations.
    """

    @pytest.mark.integration
    @pytest.mark.parametrize("health_check_func,component_name", [
        (check_ai_model_health, "ai_model"),
        (check_cache_health, "cache"),
        (check_resilience_health, "resilience"),
    ])
    async def test_all_health_checks_follow_component_status_contract(
        self, health_check_func, component_name
    ):
        """
        Test all health check functions return valid ComponentStatus per contract.

        Integration Scope:
            Individual health check functions → ComponentStatus contract validation
            Tests all built-in health check functions for structural contract compliance

        Business Impact:
            Ensures consistent health monitoring interface across all components,
            enabling reliable operational monitoring and preventing health check
            infrastructure failures that could mask system issues.

        Test Strategy:
            - Execute each health check function directly (no mocking)
            - Verify ComponentStatus structure matches health.pyi contract
            - Validate all required fields have correct types and values
            - Ensure response time measurement is working correctly

        Success Criteria:
            - All health check functions return ComponentStatus objects
            - name field matches expected component identifier
            - status is valid HealthStatus enum value (HEALTHY/DEGRADED/UNHEALTHY)
            - message is non-empty string for troubleshooting
            - response_time_ms is non-negative float
            - No health check crashes or returns invalid data
        """
        # Act: Execute health check function
        status = await health_check_func()

        # Assert: Contract compliance - name field
        assert status.name == component_name, (
            f"Component name mismatch for {health_check_func.__name__}: "
            f"expected '{component_name}', got '{status.name}'"
        )

        # Assert: Contract compliance - status field type and value
        assert isinstance(status.status, HealthStatus), (
            f"Invalid status type for {component_name}: "
            f"expected HealthStatus enum, got {type(status.status)}"
        )
        assert status.status in [
            HealthStatus.HEALTHY,
            HealthStatus.DEGRADED,
            HealthStatus.UNHEALTHY
        ], (
            f"Invalid status value for {component_name}: "
            f"{status.status} is not a valid HealthStatus enum value"
        )

        # Assert: Contract compliance - message field
        assert isinstance(status.message, str), (
            f"Message must be string for {component_name}: "
            f"got {type(status.message)}"
        )
        assert len(status.message) > 0, (
            f"Message must not be empty for {component_name}: "
            f"empty message provides no diagnostic value"
        )

        # Assert: Contract compliance - response_time_ms field
        assert isinstance(status.response_time_ms, (int, float)), (
            f"Invalid response_time type for {component_name}: "
            f"expected int or float, got {type(status.response_time_ms)}"
        )
        assert status.response_time_ms >= 0, (
            f"Response time must be non-negative for {component_name}: "
            f"got {status.response_time_ms}ms"
        )

        # Assert: Contract compliance - metadata field type (optional)
        assert status.metadata is None or isinstance(status.metadata, dict), (
            f"Metadata must be None or dict for {component_name}: "
            f"got {type(status.metadata)}"
        )

    @pytest.mark.integration
    async def test_health_checks_with_metadata_include_diagnostic_information(self):
        """
        Test health checks that provide metadata include useful diagnostic information.

        Integration Scope:
            Health check functions → ComponentStatus.metadata diagnostic validation
            Tests that metadata, when present, provides actionable operational information

        Business Impact:
            Enables detailed diagnostics for operations teams during incidents.
            Metadata containing circuit breaker states, cache backend information,
            and AI configuration status helps troubleshoot issues quickly and
            make informed operational decisions.

        Test Strategy:
            - Execute all health check functions and examine metadata
            - Validate metadata structure when present
            - Verify metadata contains actionable diagnostic information
            - Test both present and absent metadata scenarios

        Success Criteria:
            - Metadata is either None or a dictionary
            - Metadata keys are strings with descriptive names
            - Metadata values provide actionable diagnostic information
            - AI model health metadata includes provider and configuration status
            - Resilience health metadata includes circuit breaker information
        """
        # Test AI model health metadata
        ai_status = await check_ai_model_health()

        if ai_status.metadata is not None:
            assert isinstance(ai_status.metadata, dict), (
                "AI model health metadata must be dict when present"
            )

            # Verify expected metadata keys for AI model health
            has_provider = "provider" in ai_status.metadata
            has_api_key = "has_api_key" in ai_status.metadata

            assert has_provider or has_api_key, (
                f"AI model health metadata should include diagnostic information. "
                f"Current keys: {list(ai_status.metadata.keys())}. "
                f"Expected at least 'provider' or 'has_api_key' for operational diagnostics."
            )

            # Verify metadata values are useful for diagnostics
            if "provider" in ai_status.metadata:
                assert isinstance(ai_status.metadata["provider"], str), (
                    "AI provider metadata should be string for operational clarity"
                )
                assert len(ai_status.metadata["provider"]) > 0, (
                    "AI provider metadata should not be empty"
                )

            if "has_api_key" in ai_status.metadata:
                assert isinstance(ai_status.metadata["has_api_key"], bool), (
                    "AI API key status should be boolean for clear operational state"
                )

        # Test resilience health metadata
        resilience_status = await check_resilience_health()

        if resilience_status.metadata is not None:
            assert isinstance(resilience_status.metadata, dict), (
                "Resilience health metadata must be dict when present"
            )

            # Verify expected metadata keys for resilience health
            has_total_breakers = "total_circuit_breakers" in resilience_status.metadata
            has_open_breakers = "open_circuit_breakers" in resilience_status.metadata
            has_half_open_breakers = "half_open_circuit_breakers" in resilience_status.metadata

            assert has_total_breakers or has_open_breakers or has_half_open_breakers, (
                f"Resilience health metadata should include circuit breaker information. "
                f"Current keys: {list(resilience_status.metadata.keys())}. "
                f"Expected at least one of: 'total_circuit_breakers', "
                f"'open_circuit_breakers', 'half_open_circuit_breakers'"
            )

            # Verify metadata values are useful for operational diagnostics
            if "total_circuit_breakers" in resilience_status.metadata:
                assert isinstance(resilience_status.metadata["total_circuit_breakers"], int), (
                    "Total circuit breakers should be integer for monitoring"
                )
                assert resilience_status.metadata["total_circuit_breakers"] >= 0, (
                    "Total circuit breakers should be non-negative"
                )

            if "open_circuit_breakers" in resilience_status.metadata:
                assert isinstance(resilience_status.metadata["open_circuit_breakers"], list), (
                    "Open circuit breakers should be list of breaker names"
                )
                # All items in list should be strings
                for breaker_name in resilience_status.metadata["open_circuit_breakers"]:
                    assert isinstance(breaker_name, str), (
                        f"Circuit breaker name should be string: {breaker_name}"
                    )

            if "half_open_circuit_breakers" in resilience_status.metadata:
                assert isinstance(resilience_status.metadata["half_open_circuit_breakers"], list), (
                    "Half-open circuit breakers should be list of breaker names"
                )
                # All items in list should be strings
                for breaker_name in resilience_status.metadata["half_open_circuit_breakers"]:
                    assert isinstance(breaker_name, str), (
                        f"Circuit breaker name should be string: {breaker_name}"
                    )

        # Test cache health metadata (may be None in some configurations)
        cache_status = await check_cache_health()

        # Cache health check may not provide metadata in all configurations
        # This is acceptable as metadata is optional per contract
        if cache_status.metadata is not None:
            assert isinstance(cache_status.metadata, dict), (
                "Cache health metadata must be dict when present"
            )

            # Cache metadata may vary based on backend (Redis vs memory)
            # We only verify structure compliance, not specific content
            for key, value in cache_status.metadata.items():
                assert isinstance(key, str), (
                    f"Cache metadata key should be string: {key}"
                )
                # Values can be various types (str, int, bool, dict) for cache diagnostics
                assert isinstance(value, (str, int, bool, float, list, dict)), (
                    f"Cache metadata value should be serializable: {key}={value} ({type(value)})"
                )

    @pytest.mark.integration
    async def test_all_health_checks_measure_response_times_accurately(self):
        """
        Test all health check functions measure and report response times accurately.

        Integration Scope:
            Health check functions → ComponentStatus.response_time_ms measurement validation
            Ensures timing information is available for performance monitoring

        Business Impact:
            Response time measurement enables performance monitoring and alerting
            for health check infrastructure itself. Slow health checks can indicate
            system performance issues that may impact overall application responsiveness.

        Test Strategy:
            - Execute all health check functions
            - Verify response_time_ms is greater than 0
            - Ensure response times are reasonable (not extremely slow)
            - Validate response times are float values for precision

        Success Criteria:
            - All health checks report positive response times (> 0ms)
            - Response times are measured with microsecond precision (simple checks may be <0.01ms)
            - Response times are properly typed as float
            - No health check exceeds reasonable timeout (10000ms indicates performance issue)
        """
        health_checks = [
            (check_ai_model_health, "ai_model"),
            (check_cache_health, "cache"),
            (check_resilience_health, "resilience"),
        ]

        for health_check_func, component_name in health_checks:
            # Act: Execute health check function
            status = await health_check_func()

            # Assert: Response time measurement
            assert status.response_time_ms > 0.0, (
                f"Response time for {component_name} should be > 0ms: "
                f"got {status.response_time_ms}ms (indicates timing not measured)"
            )

            # Response times should be reasonable (not extremely slow in normal operation)
            # Note: Simple configuration checks can legitimately complete in microseconds,
            # so we only verify upper bound to catch performance issues
            assert status.response_time_ms < 10000.0, (
                f"Response time for {component_name} is unexpectedly slow: "
                f"{status.response_time_ms}ms (may indicate performance issue)"
            )

            # Verify float precision for monitoring
            assert isinstance(status.response_time_ms, float), (
                f"Response time should be float for precision: "
                f"{component_name} has {type(status.response_time_ms)}"
            )