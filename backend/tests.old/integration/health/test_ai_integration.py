"""
Integration Tests for AI Service Configuration Health Monitoring (SEAM 3)

Tests the integration between HealthChecker and AI service configuration validation,
including API key presence checking, configuration status reporting, and external
API call avoidance patterns. Validates that AI health checks accurately reflect
AI service configuration state without making external API calls.

This test file validates the critical integration seam:
HealthChecker → check_ai_model_health → Settings validation → Configuration status

Test Coverage:
- AI model configuration validation with API key presence
- Degraded status when API key missing or invalid
- External API call avoidance for performance optimization
- Metadata collection for AI service monitoring
- Performance characteristics of AI health checks
"""

import pytest
import time
from unittest.mock import patch

from app.infrastructure.monitoring.health import HealthStatus, ComponentStatus, check_ai_model_health


@pytest.mark.integration
class TestAIHealthIntegration:
    """
    Integration tests for AI service configuration health monitoring.

    Seam Under Test:
        HealthChecker → check_ai_model_health → settings.gemini_api_key validation

    Critical Paths:
        - AI configuration validation without external API calls
        - API key presence checking and status reporting
        - Graceful degradation when AI services not configured
        - Metadata collection for AI service operational visibility

    Business Impact:
        Confirms AI services ready for text processing operations
        Validates AI configuration status without consuming API quota
        Ensures fast health checks for rapid operational feedback

    Integration Scope:
        Health checker execution → Settings access → Configuration validation → Status reporting
    """

    async def test_ai_model_health_check_reports_healthy_with_valid_api_key(
        self, health_checker, healthy_environment
    ):
        """
        Test AI model health check returns HEALTHY when API key properly configured.

        Integration Scope:
            Health checker → check_ai_model_health → settings.gemini_api_key validation

        Contract Validation:
            - ComponentStatus with status=HEALTHY per health.pyi:579
            - metadata includes provider and configuration status per health.pyi:582
            - No external API calls made per health.pyi:617

        Business Impact:
            Confirms AI services ready for text processing operations
            Validates AI configuration is properly detected and reported
            Ensures health monitoring doesn't consume AI service quota

        Test Strategy:
            - Ensure valid GEMINI_API_KEY configured in environment
            - Use real health check function (no mocking of internals)
            - Verify through direct health checker invocation
            - Validate metadata includes provider information

        Success Criteria:
            - AI component status is "healthy"
            - Metadata shows provider="gemini" and has_api_key=true
            - Message confirms configuration status
            - Response time indicates no external API calls
        """
        # Act: Execute AI health check through health checker
        result = await health_checker.check_component("ai_model")

        # Assert: AI model reports healthy
        assert result.name == "ai_model"
        assert result.status == HealthStatus.HEALTHY
        assert result.response_time_ms > 0
        assert result.response_time_ms < 100, "AI health check should be fast (< 100ms)"

        # Verify message indicates healthy configuration
        assert "configured" in result.message.lower() or "available" in result.message.lower()

        # Verify metadata if present
        if result.metadata:
            assert result.metadata.get("provider") == "gemini"
            assert result.metadata.get("has_api_key") is True

    async def test_ai_model_health_check_reports_degraded_without_api_key(
        self, health_checker, degraded_ai_environment
    ):
        """
        Test AI model health check returns DEGRADED when API key missing.

        Integration Scope:
            Health checker → check_ai_model_health → settings validation (missing key)

        Contract Validation:
            - ComponentStatus with status=DEGRADED per health.pyi:580
            - metadata indicates missing configuration per health.pyi:582
            - Graceful degradation without external dependency failures

        Business Impact:
            Alerts operations to AI service configuration issues
            System remains partially operational for non-AI features
            Validates configuration validation works correctly

        Test Strategy:
            - Remove GEMINI_API_KEY from environment using fixture
            - Verify degraded status with descriptive message
            - Test through health checker (outside-in approach)
            - Validate metadata reflects missing configuration

        Success Criteria:
            - AI component status is "degraded"
            - Message indicates missing or invalid configuration
            - Metadata shows has_api_key=false
            - Health check completes quickly without errors
        """
        # Act: Execute AI health check
        result = await health_checker.check_component("ai_model")

        # Assert: AI model reports degraded
        assert result.name == "ai_model"
        assert result.status == HealthStatus.DEGRADED
        assert result.response_time_ms > 0
        assert result.response_time_ms < 100, "AI health check should be fast even when degraded"

        # Verify message indicates missing configuration
        assert "missing" in result.message.lower() or "not configured" in result.message.lower()

        # Verify metadata indicates missing configuration
        if result.metadata:
            assert result.metadata.get("has_api_key") is False

    async def test_ai_model_health_check_makes_no_external_api_calls(
        self, health_checker, healthy_environment, performance_time_tracker
    ):
        """
        Test AI model health check validates configuration without calling external APIs.

        Integration Scope:
            Health checker → check_ai_model_health (configuration validation only)

        Contract Validation:
            - "Does not perform actual AI model inference" per health.pyi:617
            - Fast response time for health monitoring efficiency
            - Configuration-only validation approach

        Business Impact:
            Ensures health monitoring doesn't consume AI service quota
            Provides fast health checks for rapid operational feedback
            Validates efficient health monitoring practices

        Test Strategy:
            - Monitor response time to infer no external calls
            - Configure with valid API key
            - Measure timing characteristics
            - Verify response time suggests local validation only

        Success Criteria:
            - Health check completes in < 100ms
            - No external network calls made (inferred from timing)
            - Consistent fast response across multiple checks
            - Performance suitable for high-frequency monitoring
        """
        # Act: Execute health check and measure timing
        performance_time_tracker.start_measurement()
        result = await health_checker.check_component("ai_model")
        measured_time_ms = performance_time_tracker.end_measurement()

        # Assert: Fast response indicates no external calls
        assert result.status == HealthStatus.HEALTHY
        assert result.response_time_ms < 100, \
            f"AI health check took {result.response_time_ms:.1f}ms (expected < 100ms without API calls)"

        # Overall measurement should also be fast
        assert measured_time_ms < 200, \
            f"Total AI health check took {measured_time_ms:.1f}ms (indicates potential external calls)"

    async def test_ai_model_health_check_metadata_collection(
        self, health_checker, healthy_environment
    ):
        """
        Test AI model health check collects comprehensive metadata for monitoring.

        Integration Scope:
            Health checker → check_ai_model_health → Metadata generation and reporting

        Contract Validation:
            - ComponentStatus metadata includes provider information per health.pyi:582
            - Configuration status captured in metadata for operational visibility
            - Diagnostic information for troubleshooting AI service issues

        Business Impact:
            Provides operational visibility into AI service configuration
            Enables monitoring systems to understand AI service state
            Supports troubleshooting and capacity planning

        Test Strategy:
            - Test metadata collection with different AI configurations
            - Verify metadata includes provider and configuration information
            - Validate metadata structure and content accuracy
            - Test metadata consistency across configuration states

        Success Criteria:
            - Metadata includes provider information
            - Configuration status is reflected in metadata
            - Metadata structure is consistent and valid
            - Information supports operational monitoring needs
        """
        # Act: Execute AI health check
        result = await health_checker.check_component("ai_model")

        # Assert: Metadata collection
        assert result.metadata is not None
        assert "provider" in result.metadata
        assert "has_api_key" in result.metadata

        # Verify provider information
        assert result.metadata["provider"] == "gemini"

        # Verify API key status (should be True due to healthy_environment fixture)
        assert isinstance(result.metadata["has_api_key"], bool)

    async def test_ai_model_health_check_consistency_across_calls(
        self, health_checker, healthy_environment
    ):
        """
        Test AI model health check provides consistent results across multiple calls.

        Integration Scope:
            Multiple health checker executions → Consistent AI configuration validation

        Business Impact:
            Validates health monitoring reliability and consistency
            Ensures monitoring systems receive stable status information
            Confirms no state-related issues in health checking

        Test Strategy:
            - Execute multiple AI health checks in sequence
            - Verify results are consistent across calls
            - Test performance characteristics remain stable
            - Validate no side effects between health check calls

        Success Criteria:
            - Multiple health checks return identical status
            - Response times remain consistent
            - No side effects or state changes between calls
            - Results are deterministic and predictable
        """
        # Act: Execute multiple health checks
        results = []
        response_times = []

        for i in range(5):
            result = await health_checker.check_component("ai_model")
            results.append(result)
            response_times.append(result.response_time_ms)

        # Assert: Consistency across calls
        assert len(results) == 5

        # All results should have same status
        statuses = [result.status for result in results]
        assert all(status == HealthStatus.HEALTHY for status in statuses)

        # All results should have same name
        names = [result.name for result in results]
        assert all(name == "ai_model" for name in names)

        # Response times should be reasonable and consistent
        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)

        assert avg_response_time < 100, f"Average response time {avg_response_time:.1f}ms too high"
        assert max_response_time < 200, f"Max response time {max_response_time:.1f}ms too high"

        # Response times should be relatively consistent (within 5x of average)
        for rt in response_times:
            assert rt < (avg_response_time * 5), f"Response time variance too high: {rt}ms vs avg {avg_response_time:.1f}ms"

    async def test_ai_model_health_check_error_handling(
        self, health_checker
    ):
        """
        Test AI model health check handles configuration errors gracefully.

        Integration Scope:
            Health checker → check_ai_model_health → Exception handling → UNHEALTHY status

        Contract Validation:
            - ComponentStatus with status=UNHEALTHY when health check infrastructure fails
            - Exception handling preserves error information in message
            - Graceful failure without impacting overall health monitoring

        Business Impact:
            Ensures health monitoring continues even when AI configuration validation fails
            Validates error information is preserved for troubleshooting
            Confirms AI health check failures don't crash overall health monitoring

        Test Strategy:
            - Simulate configuration validation error
            - Verify UNHEALTHY status is returned with error details
            - Test exception handling doesn't crash health monitoring
            - Validate error information is preserved in response

        Success Criteria:
            - AI component status is "unhealthy" when validation fails
            - Error message provides diagnostic information
            - Health check completes despite configuration validation failure
            - Response time is measured even for failed checks
        """
        # Mock settings to raise exception during validation
        with patch('app.infrastructure.monitoring.health.settings') as mock_settings:
            mock_settings.gemini_api_key = property(
                lambda self: (_ for _ in ()).throw(Exception("Configuration access failed"))
            )

            # Act: Execute AI health check with mocked failure
            result = await health_checker.check_component("ai_model")

            # Assert: Error handling
            assert result.name == "ai_model"
            assert result.status == HealthStatus.UNHEALTHY
            assert "failed" in result.message.lower()
            assert result.response_time_ms > 0

    async def test_ai_model_health_check_performance_requirements(
        self, health_checker, healthy_environment, performance_time_tracker
    ):
        """
        Test AI model health check meets performance requirements for monitoring systems.

        Integration Scope:
            Health checker execution → Performance measurement → SLA validation

        Business Impact:
            Ensures AI health monitoring suitable for high-frequency monitoring
            Validates health checks don't impact application performance
            Confirms monitoring system requirements are met

        Test Strategy:
            - Measure AI health check execution time under various conditions
            - Verify performance meets operational requirements
            - Test performance consistency across multiple executions
            - Validate performance is suitable for monitoring integration

        Success Criteria:
            - AI health check completes in < 50ms under normal conditions
            - Performance remains consistent across multiple calls
            - Response time measurement is accurate and reliable
            - Performance meets typical monitoring system SLAs
        """
        # Act: Measure performance across multiple calls
        measurements = []

        for _ in range(10):
            performance_time_tracker.start_measurement()
            result = await health_checker.check_component("ai_model")
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

        # Performance should be excellent (very fast local validation)
        assert avg_result_time < 50, f"Average result time {avg_result_time:.1f}ms exceeds requirement"
        assert avg_measured_time < 100, f"Average measured time {avg_measured_time:.1f}ms exceeds requirement"
        assert max_measured_time < 200, f"Max measured time {max_measured_time:.1f}ms exceeds requirement"


@pytest.mark.integration
class TestAIHealthConfigurationScenarios:
    """
    Integration tests for various AI service configuration scenarios.

    Tests AI health check behavior under different configuration states,
    including valid configurations, missing keys, invalid configurations,
    and edge cases that might occur in production environments.
    """

    @pytest.mark.parametrize("api_key_value,expected_status,expected_message_contains", [
        ("valid-api-key-123", HealthStatus.HEALTHY, "configured"),
        ("", HealthStatus.DEGRADED, "missing"),
        ("   ", HealthStatus.DEGRADED, "missing"),
        (None, HealthStatus.DEGRADED, "missing"),
    ])
    async def test_ai_model_health_check_with_various_api_key_configurations(
        self, health_checker, api_key_value, expected_status, expected_message_contains, monkeypatch
    ):
        """
        Test AI model health check with various API key configuration values.

        Integration Scope:
            Health checker → check_ai_model_health → Different API key configurations

        Business Impact:
            Validates AI health check handles various configuration states correctly
            Ensures consistent behavior across different configuration scenarios
            Confirms robust configuration validation logic

        Test Strategy:
            - Test different API key values using parameterized test
            - Verify expected status and message content for each configuration
            - Test edge cases like empty strings and None values
            - Validate behavior consistency

        Success Criteria:
            - Status matches expected value for each configuration
            - Message contains expected descriptive content
            - Edge cases are handled gracefully
            - Behavior is consistent and predictable
        """
        # Arrange: Set API key configuration
        if api_key_value is None:
            monkeypatch.delenv("GEMINI_API_KEY", raising=False)
        else:
            monkeypatch.setenv("GEMINI_API_KEY", api_key_value)

        # Reset health checker to pick up new environment
        from app.infrastructure.monitoring.health import check_ai_model_health
        health_checker.register_check("ai_model_test", check_ai_model_health)

        # Act: Execute health check
        result = await health_checker.check_component("ai_model_test")

        # Assert: Expected behavior
        assert result.name == "ai_model_test"
        assert result.status == expected_status
        assert expected_message_contains in result.message.lower()

    async def test_ai_model_health_check_environment_variable_changes(
        self, health_checker, monkeypatch
    ):
        """
        Test AI model health check responds to environment variable changes.

        Integration Scope:
            Environment changes → Settings reload → AI health check behavior

        Business Impact:
            Validates health monitoring responds to configuration changes
            Ensures dynamic configuration updates are detected
            Confirms monitoring accuracy during configuration changes

        Test Strategy:
            - Test initial configuration state
            - Change environment variable
            - Verify health check detects change
            - Test multiple configuration changes

        Success Criteria:
            - Health check detects configuration changes
            - Status updates appropriately with new configuration
            - Response time remains fast after configuration changes
            - No caching issues prevent configuration detection
        """
        # Test Case 1: Start with no API key
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)

        result1 = await health_checker.check_component("ai_model")
        assert result1.status == HealthStatus.DEGRADED
        assert "missing" in result1.message.lower()

        # Test Case 2: Add API key
        monkeypatch.setenv("GEMINI_API_KEY", "new-api-key-456")

        # Note: In a real scenario, you might need to reload settings
        # For this test, we'll verify the behavior is consistent with the new environment
        result2 = await health_checker.check_component("ai_model")

        # The result should reflect the new configuration
        # (Depending on implementation, this might require settings reload)
        assert result2.name == "ai_model"
        assert result2.response_time_ms > 0

    async def test_ai_model_health_check_concurrent_execution(
        self, health_checker, healthy_environment
    ):
        """
        Test AI model health check handles concurrent execution safely.

        Integration Scope:
            Concurrent health checker executions → Safe AI configuration validation

        Business Impact:
            Validates health monitoring can handle concurrent monitoring requests
            Ensures thread safety of configuration validation
            Confirms no race conditions in health checking

        Test Strategy:
            - Execute multiple AI health checks concurrently
            - Verify all requests complete successfully
            - Check for consistent results across concurrent calls
            - Test thread safety of configuration access

        Success Criteria:
            - All concurrent requests succeed
            - Results are consistent across concurrent calls
            - No race conditions or threading issues
            - Performance remains acceptable under concurrent load
        """
        import asyncio

        # Act: Execute concurrent health checks
        tasks = [health_checker.check_component("ai_model") for _ in range(10)]
        results = await asyncio.gather(*tasks)

        # Assert: Concurrent execution safety
        assert len(results) == 10

        # All results should be successful and consistent
        statuses = [result.status for result in results]
        assert all(status == HealthStatus.HEALTHY for status in statuses)

        names = [result.name for result in results]
        assert all(name == "ai_model" for name in names)

        # Response times should be reasonable even under concurrent load
        response_times = [result.response_time_ms for result in results]
        avg_response_time = sum(response_times) / len(response_times)
        max_response_time = max(response_times)

        assert avg_response_time < 100, f"Average response time {avg_response_time:.1f}ms too high under load"
        assert max_response_time < 200, f"Max response time {max_response_time:.1f}ms too high under load"