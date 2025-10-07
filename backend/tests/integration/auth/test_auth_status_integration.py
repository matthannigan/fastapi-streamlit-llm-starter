"""
Integration tests for authentication status API endpoint integration.

Tests the /v1/auth/status endpoint as a comprehensive demonstration of
authentication system integration with environment context and response formatting.

Seam Under Test:
    /v1/auth/status → verify_api_key_http → Authentication System → Environment Context → Response

Critical Paths:
    - Status endpoint demonstrates complete authentication integration
    - Error responses show proper HTTP exception handling integration
    - Response format varies appropriately based on environment context
"""

from fastapi import status


class TestAuthStatusIntegration:
    """
    Integration tests for authentication status API endpoint.

    Seam Under Test:
        HTTP Request → /v1/auth/status Endpoint → Authentication Dependencies → Response Generation

    Critical Paths:
        - Status endpoint serves as comprehensive authentication system demonstration
        - Response format and content varies appropriately by environment and auth state
        - Error handling demonstrates proper HTTP exception conversion and context preservation
    """

    def test_auth_status_endpoint_demonstrates_complete_integration_success(
        self, production_client
    ):
        """
        Test /v1/auth/status demonstrates complete authentication integration.

        Integration Scope:
            Tests entire authentication stack through single endpoint including
            dependency injection, authentication validation, environment detection,
            and structured response generation.

        Business Impact:
            Provides comprehensive authentication validation endpoint for
            monitoring, debugging, and API client verification.

        Test Strategy:
            - Configure production environment with valid API key
            - Call status endpoint with valid authentication
            - Verify complete response includes all integration components

        Success Criteria:
            - Returns 200 with complete authentication status information
            - Response includes truncated API key prefix for verification
            - Environment context properly integrated into response
            - Authentication metadata demonstrates system integration
        """
        # Arrange: Prepare valid authentication for status check
        auth_headers = {"Authorization": "Bearer test-production-key"}

        # Act: Request authentication status
        response = production_client.get("/v1/auth/status", headers=auth_headers)

        # Assert: Verify complete integration demonstration
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()

        # Verify authentication integration
        assert response_data["authenticated"] is True
        assert response_data["api_key_prefix"] == "test-pro..."
        assert "Authentication successful" in response_data["message"]

    def test_auth_status_error_responses_demonstrate_http_exception_integration(
        self, production_client
    ):
        """
        Test /v1/auth/status error handling demonstrates HTTP exception integration.

        Integration Scope:
            Tests authentication failure handling through custom exception
            generation, HTTP conversion, and structured error response formatting.

        Business Impact:
            Ensures API clients receive consistent, actionable error responses
            with sufficient context for debugging authentication issues.

        Test Strategy:
            - Attempt status check with invalid authentication
            - Verify proper 401 response with structured error format
            - Ensure error context preservation and HTTP compliance

        Success Criteria:
            - Returns 401 Unauthorized with proper HTTP headers
            - Error response includes structured detail and context
            - WWW-Authenticate header present for HTTP compliance
            - Error context includes debugging information without exposing secrets
        """
        # Arrange: Prepare invalid authentication
        invalid_headers = {"Authorization": "Bearer invalid-status-key"}

        # Act: Attempt status check with invalid authentication
        response = production_client.get("/v1/auth/status", headers=invalid_headers)

        # Assert: Verify HTTP exception integration
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "WWW-Authenticate" in response.headers

        response_data = response.json()

        # Verify structured error format
        assert "detail" in response_data
        detail = response_data["detail"]
        assert "message" in detail
        assert "context" in detail
        assert "Invalid API key" in detail["message"]

        # Verify error context includes integration information
        context = detail["context"]
        assert context["auth_method"] == "bearer_token"
        assert context["environment"] == "production"
        assert context["credentials_provided"] is True

    def test_auth_status_missing_credentials_shows_proper_authentication_challenge(
        self, production_client
    ):
        """
        Test /v1/auth/status returns proper authentication challenge for missing credentials.

        Integration Scope:
            Tests missing credentials handling through dependency injection,
            security policy enforcement, and HTTP challenge response generation.

        Business Impact:
            Ensures unauthenticated requests receive proper HTTP authentication
            challenge with clear guidance for required authentication.

        Test Strategy:
            - Make status request without authentication headers
            - Verify proper 401 challenge response with WWW-Authenticate header
            - Ensure error message clearly indicates authentication requirement

        Success Criteria:
            - Returns 401 with WWW-Authenticate challenge header
            - Error message clearly indicates authentication requirement
            - Response context indicates missing credentials (not invalid)
            - HTTP response complies with authentication challenge standards
        """
        # Act: Request status without authentication
        response = production_client.get("/v1/auth/status")

        # Assert: Verify authentication challenge
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert response.headers["WWW-Authenticate"] == "Bearer"

        response_data = response.json()
        detail = response_data["detail"]
        assert "API key required" in detail["message"]

        context = detail["context"]
        assert context["credentials_provided"] is False
        assert context["environment"] == "production"

    def test_auth_status_environment_context_integration_production_vs_development(
        self, development_client
    ):
        """
        Test status endpoint responses vary correctly between environments.

        Integration Scope:
            Tests environment detection integration with response formatting,
            ensuring status responses appropriately reflect deployment context.

        Business Impact:
            Provides environment-aware status reporting for monitoring
            and debugging across different deployment environments.

        Test Strategy:
            - Request status in development environment without keys
            - Verify development-specific response format and warnings
            - Ensure environment context properly integrated

        Success Criteria:
            - Development environment returns appropriate status information
            - Response includes development mode indicators and warnings
            - Environment context correctly identifies development deployment
            - Response format appropriate for development vs production
        """
        # Act: Request status in development environment (no auth required)
        response = development_client.get("/v1/auth/status")

        # Assert: Verify development environment integration
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert response_data["authenticated"] is True
        assert response_data["api_key_prefix"] == "developm..."
        assert "Authentication successful" in response_data["message"]

    def test_auth_status_response_format_consistency_across_authentication_methods(
        self, production_client
    ):
        """
        Test status response format consistent regardless of authentication method.

        Integration Scope:
            Tests response formatting consistency across different authentication
            header types (Bearer vs X-API-Key) and validation methods.

        Business Impact:
            Ensures consistent API client experience regardless of
            authentication method preference or requirements.

        Test Strategy:
            - Test status endpoint with Bearer token authentication
            - Test same endpoint with X-API-Key header authentication
            - Verify response format consistency between methods

        Success Criteria:
            - Response structure identical between authentication methods
            - Key prefix and authentication status consistent
            - Only auth_method field differs between response types
            - No functional differences in endpoint behavior
        """
        # Test Bearer token authentication
        bearer_headers = {"Authorization": "Bearer test-production-key"}
        bearer_response = production_client.get("/v1/auth/status", headers=bearer_headers)

        # Test X-API-Key authentication
        api_key_headers = {"X-API-Key": "test-production-key"}
        api_key_response = production_client.get("/v1/auth/status", headers=api_key_headers)

        # Assert: Verify consistent response format
        assert bearer_response.status_code == status.HTTP_200_OK
        assert api_key_response.status_code == status.HTTP_200_OK

        bearer_data = bearer_response.json()
        api_key_data = api_key_response.json()

        # Verify consistent core response structure
        assert bearer_data["authenticated"] == api_key_data["authenticated"]
        assert bearer_data["api_key_prefix"] == api_key_data["api_key_prefix"]
        assert bearer_data["message"] == api_key_data["message"]

    def test_auth_status_secure_key_prefix_truncation(
        self, multiple_api_keys_client
    ):
        """
        Test status endpoint securely truncates API key prefixes in responses.

        Integration Scope:
            Tests secure response formatting that includes enough key information
            for verification while preventing key exposure or reconstruction.

        Business Impact:
            Balances debugging utility with security by providing key
            identification without exposing sensitive authentication credentials.

        Test Strategy:
            - Test status endpoint with various API keys of different lengths
            - Verify consistent truncation length and security
            - Ensure truncated prefixes provide useful identification

        Success Criteria:
            - Key prefixes consistently truncated to safe length (8 chars)
            - Truncation prevents key reconstruction or exposure
            - Prefixes provide sufficient information for key identification
            - Truncation consistent across all configured keys
        """
        # Test primary key truncation
        primary_headers = {"Authorization": "Bearer primary-key-12345"}
        response = multiple_api_keys_client.get("/v1/auth/status", headers=primary_headers)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["api_key_prefix"] == "primary-..."
        assert len(response_data["api_key_prefix"]) == 11  # 8 chars + "..."

        # Test secondary key truncation
        secondary_headers = {"Authorization": "Bearer secondary-key-67890"}
        response = multiple_api_keys_client.get("/v1/auth/status", headers=secondary_headers)

        assert response.status_code == status.HTTP_200_OK
        response_data = response.json()
        assert response_data["api_key_prefix"] == "secondar..."
        assert len(response_data["api_key_prefix"]) == 11  # 8 chars + "..."
