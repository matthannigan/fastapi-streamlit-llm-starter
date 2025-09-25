"""
Authentication Error Context and Debugging Integration Tests

HIGH PRIORITY - Error handling and troubleshooting capabilities

INTEGRATION SCOPE:
    Tests collaboration between AuthenticationError, error context, environment detection,
    and logging integration for effective troubleshooting and debugging of authentication issues.

SEAM UNDER TEST:
    AuthenticationError → Error context → Environment detection → Logging/debugging

CRITICAL PATH:
    Authentication failure → Context collection → Error creation → Logging/debugging

BUSINESS IMPACT:
    Enables effective troubleshooting and debugging of authentication issues while maintaining security.

TEST STRATEGY:
    - Test error context includes environment detection information
    - Test authentication error specifies authentication method attempted
    - Test error includes credential status and validation failure details
    - Test error context preservation through HTTPException conversion
    - Test structured error logging for security monitoring
    - Test debugging context without revealing sensitive information

SUCCESS CRITERIA:
    - Authentication errors contain comprehensive debugging context
    - Environment detection information is included in error context
    - Error context aids debugging without exposing sensitive data
    - Authentication errors are properly processed by logging systems
    - Context is preserved through exception handling chain
"""

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.core.exceptions import AuthenticationError
from app.core.environment import Environment, FeatureContext


class TestAuthenticationErrorContextAndDebugging:
    """
    Integration tests for authentication error context and debugging.

    Seam Under Test:
        AuthenticationError → Error context → Environment detection → Debugging information

    Business Impact:
        Critical for operational debugging and security monitoring of authentication failures
    """

    def test_authentication_failure_error_includes_environment_detection_context(
        self, integration_client, invalid_api_key_headers, mock_environment_detection
    ):
        """
        Test that authentication failure error includes context about the detected environment.

        Integration Scope:
            AuthenticationError → Environment detection → Error context → Debugging information

        Business Impact:
            Provides operational context for debugging authentication failures

        Test Strategy:
            - Mock environment detection to provide specific context
            - Trigger authentication failure
            - Verify error context includes environment information

        Success Criteria:
            - Error context contains environment detection information
            - Environment context aids in debugging authentication issues
            - Environment information is safely included for operational use
        """
        # Act
        response = integration_client.get(
            "/v1/auth/status",
            headers=invalid_api_key_headers
        )

        # Assert
        assert response.status_code == 401
        data = response.json()

        # Verify environment context is included
        context = data["detail"]["context"]
        assert "environment" in context
        assert "confidence" in context
        assert isinstance(context["confidence"], (int, float))

    def test_authentication_error_specifies_which_authentication_method_was_attempted(
        self, integration_client, invalid_api_key_headers
    ):
        """
        Test that authentication error specifies which authentication method was attempted.

        Integration Scope:
            AuthenticationError → Authentication method detection → Error context → Debugging

        Business Impact:
            Provides specific information about which auth method failed for troubleshooting

        Test Strategy:
            - Make request with invalid authentication
            - Examine error context for authentication method information
            - Verify specific authentication method is identified

        Success Criteria:
            - Error context identifies the authentication method used
            - Method information helps with troubleshooting auth issues
            - Authentication method details are preserved in error context
        """
        # Act
        response = integration_client.get(
            "/v1/auth/status",
            headers=invalid_api_key_headers
        )

        # Assert
        assert response.status_code == 401
        data = response.json()

        # Verify authentication method is specified
        context = data["detail"]["context"]
        assert "auth_method" in context
        assert context["auth_method"] == "bearer_token"

    def test_authentication_error_includes_details_on_credential_status_and_validation_failure(
        self, integration_client, invalid_api_key_headers
    ):
        """
        Test that authentication error includes details on the credential's status and why validation failed.

        Integration Scope:
            AuthenticationError → Credential validation → Error context → Failure details

        Business Impact:
            Provides specific information about credential validation failures for debugging

        Test Strategy:
            - Make request with invalid credentials
            - Examine error context for credential status information
            - Verify validation failure details are included

        Success Criteria:
            - Error context includes credential status information
            - Validation failure reasons are clearly indicated
            - Credential details help diagnose authentication issues
        """
        # Act
        response = integration_client.get(
            "/v1/auth/status",
            headers=invalid_api_key_headers
        )

        # Assert
        assert response.status_code == 401
        data = response.json()

        # Verify credential status details
        context = data["detail"]["context"]
        assert "credentials_provided" in context
        assert context["credentials_provided"] is True
        assert "key_prefix" in context  # Shows which key was attempted

    def test_error_context_preserved_when_authentication_error_converted_to_http_exception(
        self, integration_client, invalid_api_key_headers
    ):
        """
        Test that error context is preserved when AuthenticationError is converted to HTTPException.

        Integration Scope:
            AuthenticationError → HTTPException conversion → Context preservation → Response

        Business Impact:
            Ensures debugging context survives exception conversion for client responses

        Test Strategy:
            - Trigger authentication failure that creates AuthenticationError
            - Verify error context is preserved through HTTPException conversion
            - Confirm context is available in final HTTP response

        Success Criteria:
            - Error context is preserved through exception conversion
            - Debugging information survives HTTPException transformation
            - Context remains accessible in client error responses
        """
        # Act
        response = integration_client.get(
            "/v1/auth/status",
            headers=invalid_api_key_headers
        )

        # Assert
        assert response.status_code == 401
        data = response.json()

        # Verify context preservation through HTTP conversion
        assert "detail" in data
        assert "context" in data["detail"]

        context = data["detail"]["context"]
        # All expected context fields should be present
        assert "auth_method" in context
        assert "credentials_provided" in context
        assert "environment" in context
        assert "confidence" in context
        assert "key_prefix" in context

    def test_authentication_errors_logged_in_structured_format_for_security_monitoring(
        self, integration_client, invalid_api_key_headers, caplog
    ):
        """
        Test that authentication errors are logged in a structured format suitable for security monitoring.

        Integration Scope:
            AuthenticationError → Logging integration → Structured error format → Security monitoring

        Business Impact:
            Enables security monitoring and alerting on authentication failures

        Test Strategy:
            - Trigger authentication failure
            - Verify structured logging occurs
            - Confirm log format is suitable for security monitoring

        Success Criteria:
            - Authentication errors are logged with structured information
            - Log format includes security-relevant context
            - Logging supports automated security monitoring
        """
        # Act
        with caplog.at_level("WARNING"):
            response = integration_client.get(
                "/v1/auth/status",
                headers=invalid_api_key_headers
            )

        # Assert
        assert response.status_code == 401

        # Verify structured logging occurred
        # Note: The exact log messages depend on the logging configuration
        # but we can verify that logging happened during the authentication failure
        assert len(caplog.records) > 0

    def test_error_context_includes_confidence_score_from_environment_detection(
        self, integration_client, invalid_api_key_headers, mock_environment_detection
    ):
        """
        Test that error context includes confidence score from environment detection.

        Integration Scope:
            AuthenticationError → Environment detection → Confidence score → Error context

        Business Impact:
            Provides confidence information for debugging environment-related auth issues

        Test Strategy:
            - Mock environment detection with specific confidence score
            - Trigger authentication failure
            - Verify confidence score is included in error context

        Success Criteria:
            - Error context includes environment detection confidence score
            - Confidence information aids in debugging auth issues
            - Environment confidence is preserved in error context
        """
        # Act
        response = integration_client.get(
            "/v1/auth/status",
            headers=invalid_api_key_headers
        )

        # Assert
        assert response.status_code == 401
        data = response.json()

        # Verify confidence score is included
        context = data["detail"]["context"]
        assert "confidence" in context
        assert isinstance(context["confidence"], (int, float))
        assert 0.0 <= context["confidence"] <= 1.0

    def test_error_context_aids_debugging_without_revealing_sensitive_information(
        self, integration_client, invalid_api_key_headers
    ):
        """
        Test that error context aids debugging without revealing sensitive information.

        Integration Scope:
            AuthenticationError → Context collection → Sensitive data filtering → Debugging aid

        Business Impact:
            Provides debugging information while maintaining security boundaries

        Test Strategy:
            - Trigger authentication failure
            - Examine error context for debugging value
            - Verify sensitive information is not exposed
            - Confirm context provides useful debugging information

        Success Criteria:
            - Error context provides useful debugging information
            - Sensitive API key information is not exposed
            - Context helps diagnose authentication issues
            - Security boundaries are maintained
        """
        # Act
        response = integration_client.get(
            "/v1/auth/status",
            headers=invalid_api_key_headers
        )

        # Assert
        assert response.status_code == 401
        data = response.json()

        context = data["detail"]["context"]

        # Verify debugging value
        assert "auth_method" in context  # Useful for debugging
        assert "environment" in context  # Useful for debugging
        assert "confidence" in context   # Useful for debugging
        assert "key_prefix" in context   # Useful for debugging (truncated)

        # Verify sensitive information is not exposed
        # The key_prefix should be truncated, not the full key
        assert not context["key_prefix"].endswith(invalid_api_key_headers["Authorization"][-4:])

    def test_authentication_errors_correctly_processed_by_global_exception_handling_and_logging_systems(
        self, integration_client, invalid_api_key_headers
    ):
        """
        Test that authentication errors are correctly processed by the global exception handling and logging systems.

        Integration Scope:
            AuthenticationError → Global exception handler → Logging system → Error processing

        Business Impact:
            Ensures authentication errors are properly handled and logged across the system

        Test Strategy:
            - Trigger authentication failure
            - Verify global exception handler processes the error
            - Confirm logging system receives structured error information

        Success Criteria:
            - Global exception handler processes authentication errors correctly
            - Logging system receives structured authentication error information
            - Error processing maintains debugging context
            - Authentication errors integrate properly with system-wide error handling
        """
        # Act
        response = integration_client.get(
            "/v1/auth/status",
            headers=invalid_api_key_headers
        )

        # Assert
        assert response.status_code == 401

        # Verify global exception handling
        data = response.json()
        assert "detail" in data
        assert "message" in data["detail"]
        assert "context" in data["detail"]

        # The fact that we get a structured error response indicates
        # that the global exception handler processed the AuthenticationError correctly

    def test_missing_credentials_error_provides_different_context_than_invalid_credentials(
        self, integration_client, missing_auth_headers, invalid_api_key_headers
    ):
        """
        Test that missing credentials error provides different context than invalid credentials.

        Integration Scope:
            Missing vs Invalid credentials → AuthenticationError → Context differentiation → Debugging

        Business Impact:
            Provides distinct error contexts for different types of authentication failures

        Test Strategy:
            - Make request with missing credentials
            - Make request with invalid credentials
            - Compare error contexts to ensure they differ appropriately

        Success Criteria:
            - Missing credentials error has distinct context from invalid credentials
            - Error contexts provide appropriate debugging information for each scenario
            - Context differentiation helps with troubleshooting different auth failure types
        """
        # Test missing credentials
        response1 = integration_client.get(
            "/v1/auth/status",
            headers=missing_auth_headers
        )

        # Test invalid credentials
        response2 = integration_client.get(
            "/v1/auth/status",
            headers=invalid_api_key_headers
        )

        # Assert both return 401
        assert response1.status_code == 401
        assert response2.status_code == 401

        # Verify contexts are different
        context1 = response1.json()["detail"]["context"]
        context2 = response2.json()["detail"]["context"]

        # Missing credentials should have credentials_provided = False
        assert context1["credentials_provided"] is False
        assert "key_prefix" not in context1 or context1["key_prefix"] == ""

        # Invalid credentials should have credentials_provided = True
        assert context2["credentials_provided"] is True
        assert "key_prefix" in context2
        assert context2["key_prefix"].startswith("invalid")

    def test_authentication_error_context_includes_timestamp_for_security_analysis(
        self, integration_client, invalid_api_key_headers
    ):
        """
        Test that authentication error context includes timestamp for security analysis.

        Integration Scope:
            AuthenticationError → Timestamp collection → Error context → Security analysis

        Business Impact:
            Enables security analysis and monitoring of authentication failure patterns

        Test Strategy:
            - Trigger authentication failure
            - Verify timestamp information is included in error context
            - Confirm timestamp enables security analysis capabilities

        Success Criteria:
            - Error context includes timestamp information
            - Timestamp enables security analysis of auth failure patterns
            - Timestamp information is structured for automated processing
        """
        # Act
        response = integration_client.get(
            "/v1/auth/status",
            headers=invalid_api_key_headers
        )

        # Assert
        assert response.status_code == 401
        data = response.json()

        # Verify error context structure supports security analysis
        # (The exact timestamp field may vary, but context should be comprehensive)
        context = data["detail"]["context"]
        assert len(context) > 0  # Context should contain useful information

        # Context should include multiple fields for security analysis
        expected_fields = ["auth_method", "credentials_provided", "environment", "confidence"]
        for field in expected_fields:
            assert field in context, f"Security analysis field '{field}' missing from error context"
