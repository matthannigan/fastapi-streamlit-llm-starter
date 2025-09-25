"""
Integration tests for AI model health monitoring.

These tests verify the integration between HealthChecker and AI service connectivity,
ensuring proper monitoring of AI model availability, API key validation,
and response validation patterns.

HIGH PRIORITY - Core business functionality monitoring
"""

import pytest
from unittest.mock import Mock, patch

from app.infrastructure.monitoring.health import (
    HealthChecker,
    HealthStatus,
    ComponentStatus,
    check_ai_model_health,
)
from app.core.config import Settings


class TestAIModelHealthIntegration:
    """
    Integration tests for AI model health monitoring.

    Seam Under Test:
        HealthChecker → AI Service → Model connectivity → Response validation

    Critical Path:
        Health check registration → AI service connectivity →
        Model validation → Health status determination

    Business Impact:
        Ensures AI model availability and prevents failed requests
        due to model unavailability, maintaining core business functionality.

    Test Strategy:
        - Test AI service connectivity validation
        - Verify API key presence and validation
        - Confirm proper health status determination
        - Test both healthy and degraded AI service scenarios
        - Validate response time measurement and metadata

    Success Criteria:
        - AI health checks detect service availability correctly
        - API key validation works as expected
        - System reports appropriate status based on AI service state
        - Response times are reasonable for frequent monitoring
        - Metadata provides actionable insights for operators
    """

    def test_ai_model_health_integration_with_valid_api_key(
        self, health_checker, settings_with_gemini_key
    ):
        """
        Test AI model health monitoring with valid Gemini API key.

        Integration Scope:
            HealthChecker → Settings validation → API key verification

        Business Impact:
            Verifies that AI model health monitoring correctly reports
            healthy status when API credentials are properly configured,
            ensuring operators know when AI services are ready for use.

        Test Strategy:
            - Mock settings with valid Gemini API key
            - Register AI model health check with health checker
            - Execute health check and validate healthy status
            - Verify API key metadata is captured correctly

        Success Criteria:
            - Health check returns HEALTHY status with valid API key
            - API key presence is correctly detected and reported
            - Metadata includes provider and API key status
            - Response time is reasonable for monitoring frequency
        """
        with patch('app.infrastructure.monitoring.health.settings', settings_with_gemini_key):
            health_checker.register_check("ai_model", check_ai_model_health)

            result = await health_checker.check_component("ai_model")

            # Verify healthy AI model monitoring
            assert result.name == "ai_model"
            assert result.status == HealthStatus.HEALTHY
            assert "configured" in result.message.lower()
            assert result.response_time_ms > 0
            assert result.response_time_ms < 50  # Should be very fast

            # Verify comprehensive metadata
            assert result.metadata is not None
            assert result.metadata["provider"] == "gemini"
            assert result.metadata["has_api_key"] is True

    def test_ai_model_health_integration_with_missing_api_key(
        self, health_checker, settings_without_gemini_key
    ):
        """
        Test AI model health monitoring with missing API key.

        Integration Scope:
            HealthChecker → Settings validation → Missing credentials detection

        Business Impact:
            Ensures AI model health monitoring correctly detects and reports
            when API credentials are missing, enabling operators to identify
            configuration issues before they impact user requests.

        Test Strategy:
            - Mock settings with missing/empty Gemini API key
            - Register AI model health check with health checker
            - Execute health check and validate degraded status
            - Verify missing API key is properly detected and reported

        Success Criteria:
            - Health check returns DEGRADED status without API key
            - Clear indication of missing API key in message
            - Metadata accurately reflects missing credentials
            - Response time remains reasonable despite degraded state
        """
        with patch('app.infrastructure.monitoring.health.settings', settings_without_gemini_key):
            health_checker.register_check("ai_model", check_ai_model_health)

            result = await health_checker.check_component("ai_model")

            # Verify degraded AI model monitoring
            assert result.name == "ai_model"
            assert result.status == HealthStatus.DEGRADED
            assert "missing" in result.message.lower() or "empty" in result.message.lower()
            assert result.response_time_ms > 0

            # Verify metadata indicates missing API key
            assert result.metadata is not None
            assert result.metadata["provider"] == "gemini"
            assert result.metadata["has_api_key"] is False

    def test_ai_model_health_integration_with_api_key_validation(
        self, health_checker, settings_with_gemini_key
    ):
        """
        Test AI model health monitoring with API key validation logic.

        Integration Scope:
            HealthChecker → Settings → API key format validation

        Business Impact:
            Ensures AI model health monitoring validates API key format
            and structure, providing early detection of configuration
            issues that could cause AI service failures.

        Test Strategy:
            - Mock settings with various API key formats
            - Register AI model health check with health checker
            - Execute health check and validate format validation
            - Verify proper handling of different API key states

        Success Criteria:
            - API key validation works correctly for different formats
            - Health status reflects actual API key usability
            - Metadata provides detailed API key information
            - Response time includes validation overhead
        """
        # Test with various API key lengths and formats
        test_cases = [
            ("test-key-123", True, "Valid format API key"),
            ("", False, "Empty API key"),
            ("x", False, "Too short API key"),
            ("valid-gemini-api-key-123456789", True, "Long valid API key"),
        ]

        with patch('app.infrastructure.monitoring.health.settings') as mock_settings:
            for api_key, expected_has_key, description in test_cases:
                mock_settings.gemini_api_key = api_key
                health_checker.register_check("ai_model", check_ai_model_health)

                result = await health_checker.check_component("ai_model")

                # Verify API key validation
                assert result.name == "ai_model"
                assert result.metadata is not None
                assert result.metadata["has_api_key"] == expected_has_key

                if expected_has_key:
                    assert result.status == HealthStatus.HEALTHY
                    assert "configured" in result.message.lower()
                else:
                    assert result.status == HealthStatus.DEGRADED
                    assert "missing" in result.message.lower() or "empty" in result.message.lower()

    def test_ai_model_health_integration_with_provider_metadata(
        self, health_checker, settings_with_gemini_key
    ):
        """
        Test AI model health monitoring provider metadata collection.

        Integration Scope:
            HealthChecker → Settings → Provider information gathering

        Business Impact:
            Ensures AI model health monitoring collects comprehensive
            provider information for operational visibility and
            troubleshooting capabilities.

        Test Strategy:
            - Mock settings with valid API key
            - Register AI model health check with health checker
            - Execute health check and validate metadata collection
            - Verify provider-specific information is captured

        Success Criteria:
            - Provider information is correctly identified and reported
            - Metadata includes all relevant provider details
            - Health status reflects provider configuration state
            - Response time includes metadata collection overhead
        """
        with patch('app.infrastructure.monitoring.health.settings', settings_with_gemini_key):
            health_checker.register_check("ai_model", check_ai_model_health)

            result = await health_checker.check_component("ai_model")

            # Verify comprehensive provider metadata
            assert result.name == "ai_model"
            assert result.status == HealthStatus.HEALTHY
            assert result.metadata is not None

            # Verify provider-specific metadata
            assert result.metadata["provider"] == "gemini"
            assert result.metadata["has_api_key"] is True
            assert isinstance(result.metadata["provider"], str)
            assert len(result.metadata["provider"]) > 0

    def test_ai_model_health_integration_with_exception_handling(
        self, health_checker
    ):
        """
        Test AI model health monitoring with exception handling.

        Integration Scope:
            HealthChecker → Settings access → Exception handling

        Business Impact:
            Ensures AI model health monitoring remains operational even
            when configuration access fails, providing visibility into
            configuration-related issues without crashing monitoring.

        Test Strategy:
            - Mock settings access to raise exceptions
            - Register AI model health check with health checker
            - Execute health check and validate error handling
            - Verify graceful degradation with configuration failures

        Success Criteria:
            - Health check returns UNHEALTHY status when settings fail
            - Clear error message indicates the nature of the failure
            - Response time is reasonable despite configuration failure
            - System continues operating despite configuration issues
        """
        # Mock settings access failure
        with patch('app.infrastructure.monitoring.health.settings', side_effect=Exception("Settings access failed")):
            health_checker.register_check("ai_model", check_ai_model_health)

            result = await health_checker.check_component("ai_model")

            # Verify graceful handling of settings failure
            assert result.name == "ai_model"
            assert result.status == HealthStatus.UNHEALTHY
            assert "failed" in result.message.lower()
            assert "Exception" in result.message or "failed" in result.message
            assert result.response_time_ms > 0

    def test_ai_model_health_integration_performance_characteristics(
        self, health_checker, settings_with_gemini_key
    ):
        """
        Test AI model health monitoring performance characteristics.

        Integration Scope:
            HealthChecker → Settings validation → Performance monitoring

        Business Impact:
            Ensures AI model health checks don't become a performance
            bottleneck when monitoring systems scale, maintaining
            operational visibility without impacting system performance.

        Test Strategy:
            - Mock settings with valid configuration
            - Register AI model health check with health checker
            - Execute multiple health checks to measure performance
            - Verify response time remains consistent under repeated calls

        Success Criteria:
            - Health check completes within performance requirements
            - Response times remain consistent across multiple calls
            - Performance doesn't degrade with repeated monitoring
            - System remains responsive during frequent health checks
        """
        with patch('app.infrastructure.monitoring.health.settings', settings_with_gemini_key):
            health_checker.register_check("ai_model", check_ai_model_health)

            # Execute multiple health checks to test performance consistency
            results = []
            for i in range(10):
                result = await health_checker.check_component("ai_model")
                results.append(result)

            # Verify consistent performance characteristics
            for result in results:
                assert result.name == "ai_model"
                assert result.status == HealthStatus.HEALTHY
                assert result.response_time_ms > 0
                assert result.response_time_ms < 100  # Should be consistently fast

            # Verify response times are reasonably consistent
            response_times = [r.response_time_ms for r in results]
            avg_response_time = sum(response_times) / len(response_times)
            max_response_time = max(response_times)
            min_response_time = min(response_times)

            # Allow for some variance but ensure consistency
            assert max_response_time - min_response_time < 50  # Less than 50ms variance
            assert avg_response_time < 75  # Average under 75ms

    def test_ai_model_health_integration_with_different_providers(
        self, health_checker
    ):
        """
        Test AI model health monitoring with different AI providers.

        Integration Scope:
            HealthChecker → Settings → Multi-provider support validation

        Business Impact:
            Ensures AI model health monitoring works correctly with
            different AI provider configurations, supporting multi-provider
            deployments and provider switching capabilities.

        Test Strategy:
            - Mock settings with different provider configurations
            - Register AI model health check with health checker
            - Execute health checks and validate provider-specific behavior
            - Verify proper handling of provider-specific settings

        Success Criteria:
            - Provider detection works correctly
            - Health status reflects provider configuration state
            - Metadata includes accurate provider information
            - Response time remains consistent across providers
        """
        # Test cases for different provider scenarios
        test_cases = [
            {
                "gemini_key": "test-gemini-key-123",
                "expected_provider": "gemini",
                "expected_has_key": True,
                "expected_status": HealthStatus.HEALTHY
            },
            {
                "gemini_key": "",
                "expected_provider": "gemini",
                "expected_has_key": False,
                "expected_status": HealthStatus.DEGRADED
            },
            {
                "gemini_key": "   ",  # Whitespace only
                "expected_provider": "gemini",
                "expected_has_key": False,
                "expected_status": HealthStatus.DEGRADED
            }
        ]

        with patch('app.infrastructure.monitoring.health.settings') as mock_settings:
            for case in test_cases:
                mock_settings.gemini_api_key = case["gemini_key"]
                health_checker.register_check("ai_model", check_ai_model_health)

                result = await health_checker.check_component("ai_model")

                # Verify provider-specific behavior
                assert result.name == "ai_model"
                assert result.status == case["expected_status"]
                assert result.metadata is not None
                assert result.metadata["provider"] == case["expected_provider"]
                assert result.metadata["has_api_key"] == case["expected_has_key"]
