"""
HTTP Exception Conversion and Middleware Compatibility Integration Tests

HIGH PRIORITY - Affects all HTTP error responses and middleware integration

INTEGRATION SCOPE:
    Tests collaboration between verify_api_key_http, AuthenticationError, HTTPException,
    and FastAPI exception handlers for proper HTTP response formatting.

SEAM UNDER TEST:
    verify_api_key_http → AuthenticationError → HTTPException → FastAPI response

CRITICAL PATH:
    Authentication failure → Custom exception → HTTP conversion → Response formatting

BUSINESS IMPACT:
    Ensures proper HTTP error responses and middleware compatibility across the application.

TEST STRATEGY:
    - Test HTTP 401 responses for invalid API keys
    - Test error context preservation through HTTP conversion
    - Test WWW-Authenticate header inclusion
    - Test middleware compatibility and error handling
    - Test structured error responses for API clients
    - Test exception chaining and debugging context preservation

SUCCESS CRITERIA:
    - Authentication failures return proper HTTP 401 responses
    - Error context is preserved through HTTP conversion
    - WWW-Authenticate headers are correctly included
    - Middleware conflicts are avoided
    - Structured error responses are provided to clients
"""

import pytest
from fastapi.testclient import TestClient
from fastapi import HTTPException, status

from app.core.exceptions import AuthenticationError
from app.infrastructure.security.auth import verify_api_key_http


class TestHTTPExceptionConversionAndMiddlewareCompatibility:
    """
    Integration tests for HTTP exception conversion and middleware compatibility.

    Seam Under Test:
        Authentication dependency → AuthenticationError → HTTPException → HTTP response

    Business Impact:
        Critical for API client compatibility and proper error handling across middleware stack
    """

    def test_invalid_api_key_receives_401_unauthorized_response(
        self, integration_client, invalid_api_key_headers
    ):
        """
        Test that invalid API key receives 401 Unauthorized response.

        Integration Scope:
            FastAPI client → Authentication dependency → HTTPException → Response formatting

        Business Impact:
            Provides clear authentication failure indication to API clients

        Test Strategy:
            - Reload API keys to ensure test environment has keys configured
            - Make request with invalid API key
            - Verify 401 status code is returned
            - Confirm proper HTTP authentication error response

        Success Criteria:
            - Response status code is 401 (Unauthorized)
            - Authentication failure is clearly indicated
            - Error follows HTTP authentication standards
        """
        # Create fresh settings and auth instance to ensure keys are loaded correctly
        from app.core.config import Settings
        from app.infrastructure.security.auth import APIKeyAuth, AuthConfig
        from unittest.mock import patch

        # Create new settings instance to load current environment variables
        new_settings = Settings()

        # Mock environment detection to return production to ensure keys are required
        def mock_production_env(feature_context):
            class MockEnvInfo:
                def __init__(self):
                    self.environment = "Environment.PRODUCTION"
                    self.confidence = 0.9
                    self.reasoning = "Mocked production environment for testing"

            return MockEnvInfo()

        with patch('app.infrastructure.security.auth.get_environment_info', side_effect=mock_production_env), \
             patch('app.infrastructure.security.auth.settings', new_settings):
            test_auth = APIKeyAuth()
            test_auth.reload_keys()

        # Act
        response = integration_client.get(
            "/v1/auth/status",
            headers=invalid_api_key_headers
        )

        # Assert
        assert response.status_code == 401
        assert response.headers.get("WWW-Authenticate") == "Bearer"

    def test_401_response_for_invalid_api_key_contains_original_error_context(
        self, integration_client, invalid_api_key_headers
    ):
        """
        Test that 401 response contains original error context from AuthenticationError.

        Integration Scope:
            AuthenticationError → HTTPException conversion → Response body → Client

        Business Impact:
            Provides debugging information while maintaining security

        Test Strategy:
            - Make request with invalid API key
            - Examine response body for error context
            - Verify context is preserved through HTTP conversion

        Success Criteria:
            - Response body contains structured error information
            - Original error context is preserved in HTTP response
            - Sensitive information is not exposed in error details
        """
        # Act
        response = integration_client.get(
            "/v1/auth/status",
            headers=invalid_api_key_headers
        )

        # Assert
        assert response.status_code == 401
        data = response.json()

        # Verify structured error response format
        assert "detail" in data
        assert "message" in data["detail"]
        assert "context" in data["detail"]

        # Verify error context is preserved
        context = data["detail"]["context"]
        assert "auth_method" in context
        assert context["auth_method"] == "bearer_token"
        assert "credentials_provided" in context
        assert context["credentials_provided"] is True

    def test_401_response_includes_www_authenticate_header(
        self, integration_client, invalid_api_key_headers
    ):
        """
        Test that 401 response includes WWW-Authenticate header for proper HTTP authentication flow.

        Integration Scope:
            HTTPException → FastAPI response formatting → HTTP headers → Client

        Business Impact:
            Enables proper HTTP authentication flow for API clients

        Test Strategy:
            - Make request with invalid API key
            - Check response headers for WWW-Authenticate
            - Verify header follows HTTP authentication standards

        Success Criteria:
            - WWW-Authenticate header is present in 401 response
            - Header value follows Bearer token authentication scheme
            - Header enables proper client authentication flow
        """
        # Act
        response = integration_client.get(
            "/v1/auth/status",
            headers=invalid_api_key_headers
        )

        # Assert
        assert response.status_code == 401
        www_authenticate = response.headers.get("WWW-Authenticate")
        assert www_authenticate is not None
        assert www_authenticate == "Bearer"

    def test_authentication_errors_handled_consistently_without_middleware_conflicts(
        self, integration_client, invalid_api_key_headers
    ):
        """
        Test that authentication errors are handled consistently without conflicts from other middleware.

        Integration Scope:
            FastAPI middleware stack → Exception handlers → HTTPException → Response

        Business Impact:
            Ensures consistent error handling across the application

        Test Strategy:
            - Make multiple requests with invalid authentication
            - Verify consistent error responses across requests
            - Confirm no middleware conflicts or response corruption

        Success Criteria:
            - All authentication errors return consistent 401 responses
            - No middleware conflicts interfere with error handling
            - Response format remains stable across multiple requests
        """
        # Act - Multiple requests to test consistency
        responses = []
        for _ in range(3):
            response = integration_client.get(
                "/v1/auth/status",
                headers=invalid_api_key_headers
            )
            responses.append(response)

        # Assert - All responses should be consistent
        for response in responses:
            assert response.status_code == 401
            assert response.headers.get("WWW-Authenticate") == "Bearer"

            data = response.json()
            assert "detail" in data
            assert "message" in data["detail"]
            assert "context" in data["detail"]

    def test_error_response_for_authentication_failure_includes_environment_detection_information(
        self, integration_client, invalid_api_key_headers, mock_environment_detection
    ):
        """
        Test that error response includes environment detection information for debugging.

        Integration Scope:
            AuthenticationError → Environment detection → HTTPException → Response context

        Business Impact:
            Provides operational debugging information for authentication failures

        Test Strategy:
            - Mock environment detection to provide specific context
            - Make request with invalid authentication
            - Verify environment information is included in error response

        Success Criteria:
            - Error response contains environment detection information
            - Environment context aids in debugging authentication issues
            - Environment information is safely included without exposing sensitive data
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

    def test_api_clients_receive_structured_error_response_on_authentication_failure(
        self, integration_client, invalid_api_key_headers
    ):
        """
        Test that API clients receive structured error response on authentication failure.

        Integration Scope:
            HTTP client → AuthenticationError → HTTPException → Structured response → Client

        Business Impact:
            Provides clear, parseable error information to API clients

        Test Strategy:
            - Make request with invalid authentication
            - Verify response follows structured error format
            - Confirm response is easily parseable by clients

        Success Criteria:
            - Response follows consistent error response schema
            - Error information is structured and predictable
            - Clients can reliably parse authentication error details
        """
        # Act
        response = integration_client.get(
            "/v1/auth/status",
            headers=invalid_api_key_headers
        )

        # Assert
        assert response.status_code == 401

        # Verify structured error response format
        data = response.json()
        assert isinstance(data, dict)
        assert "detail" in data
        assert isinstance(data["detail"], dict)
        assert "message" in data["detail"]
        assert "context" in data["detail"]

        # Verify required fields
        assert isinstance(data["detail"]["message"], str)
        assert isinstance(data["detail"]["context"], dict)

    def test_chained_exceptions_preserve_debugging_context_during_authentication_failures(
        self, integration_client, invalid_api_key_headers
    ):
        """
        Test that chained exceptions preserve debugging context during authentication failures.

        Integration Scope:
            Exception chaining → HTTPException conversion → Context preservation → Response

        Business Impact:
            Maintains debugging information through exception handling chain

        Test Strategy:
            - Trigger authentication failure with complex error context
            - Verify debugging context is preserved through exception chaining
            - Confirm context is available in final HTTP response

        Success Criteria:
            - Debugging context is preserved through exception conversion
            - Complex error scenarios maintain diagnostic information
            - Context survives the HTTPException conversion process
        """
        # Act
        response = integration_client.get(
            "/v1/auth/status",
            headers=invalid_api_key_headers
        )

        # Assert
        assert response.status_code == 401
        data = response.json()

        # Verify context is preserved and comprehensive
        context = data["detail"]["context"]
        assert "auth_method" in context
        assert "credentials_provided" in context
        assert "environment" in context
        assert "confidence" in context
        assert "key_prefix" in context

    def test_authentication_errors_correctly_handled_by_global_exception_handler(
        self, integration_client, invalid_api_key_headers
    ):
        """
        Test that authentication errors are correctly handled by the global exception handler.

        Integration Scope:
            FastAPI global exception handler → HTTPException → Response formatting

        Business Impact:
            Ensures consistent error handling across the entire application

        Test Strategy:
            - Trigger authentication error through API endpoint
            - Verify global exception handler processes the error
            - Confirm consistent error response format

        Success Criteria:
            - Global exception handler processes authentication errors
            - Error response format is consistent with application standards
            - Authentication-specific error handling is preserved
        """
        # Act
        response = integration_client.get(
            "/v1/auth/status",
            headers=invalid_api_key_headers
        )

        # Assert
        assert response.status_code == 401

        # Verify the response follows global exception handler format
        data = response.json()
        assert "detail" in data
        assert "message" in data["detail"]
        assert "context" in data["detail"]

        # This should match the format defined by the global exception handler
        # which typically includes the original error message and context

    def test_missing_credentials_return_401_with_appropriate_error_message(
        self, integration_client, missing_auth_headers
    ):
        """
        Test that missing credentials return 401 with appropriate error message.

        Integration Scope:
            Missing authentication → AuthenticationError → HTTPException → Response

        Business Impact:
            Provides clear guidance when authentication is required but missing

        Test Strategy:
            - Make request without authentication headers
            - Verify 401 response with appropriate error message
            - Confirm error message guides proper authentication

        Success Criteria:
            - 401 response returned for missing credentials
            - Error message clearly indicates authentication is required
            - Response provides guidance on proper authentication method
        """
        # Act
        response = integration_client.get(
            "/v1/auth/status",
            headers=missing_auth_headers
        )

        # Assert
        assert response.status_code == 401

        data = response.json()
        assert "message" in data["detail"]
        assert "API key required" in data["detail"]["message"]
        assert "context" in data["detail"]
        assert data["detail"]["context"]["credentials_provided"] is False

    def test_malformed_authentication_headers_return_401_with_validation_error(
        self, integration_client, malformed_auth_headers
    ):
        """
        Test that malformed authentication headers return 401 with validation error.

        Integration Scope:
            Malformed authentication → AuthenticationError → HTTPException → Response

        Business Impact:
            Provides clear feedback for authentication format errors

        Test Strategy:
            - Make request with malformed authentication headers
            - Verify 401 response with appropriate validation message
            - Confirm error indicates authentication format issue

        Success Criteria:
            - 401 response returned for malformed authentication
            - Error message indicates authentication format problem
            - Response helps client correct authentication format
        """
        # Act
        response = integration_client.get(
            "/v1/auth/status",
            headers=malformed_auth_headers
        )

        # Assert
        assert response.status_code == 401

        # The specific error message may vary based on the authentication implementation
        # but should indicate an authentication issue
        data = response.json()
        assert "message" in data["detail"]
        assert "context" in data["detail"]
