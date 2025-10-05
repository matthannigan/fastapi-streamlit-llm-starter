"""
Integration tests for environment-aware authentication flow.

Tests the complete authentication flow from HTTP request through environment
detection, security policy enforcement, and HTTP response generation.

Seam Under Test:
    FastAPI → verify_api_key_http → EnvironmentDetector → HTTPException conversion

Critical Paths:
    - Production environment enforces API key requirements
    - Development environment allows optional authentication
    - Environment detection failure defaults to production security
"""

import pytest
from fastapi import status


class TestEnvironmentAwareAuthenticationFlow:
    """
    Integration tests for environment-aware authentication flow.
    
    Seam Under Test:
        HTTP Request → FastAPI Dependencies → Environment Detection → Security Policy → HTTP Response
        
    Critical Paths:
        - Production environment requires valid API keys with proper HTTP errors
        - Development environment allows access while preserving authentication flow
        - Environment detection failures trigger production security as fallback
    """

    def test_production_environment_requires_valid_api_key_success(
        self, production_client, auth_headers_valid
    ):
        """
        Test production environment successfully authenticates valid API keys.
        
        Integration Scope:
            Tests complete flow from HTTP request through environment detection,
            security policy enforcement, and successful authentication response.
            
        Business Impact:
            Ensures users with valid API keys can access protected resources
            in production environments.
            
        Test Strategy:
            - Set production environment with configured API key
            - Make authenticated request to auth status endpoint
            - Verify successful authentication and response content
            
        Success Criteria:
            - Returns 200 status code indicating successful authentication
            - Response includes authenticated context and key information
            - No authentication errors or warnings in response
        """
        # Act: Make authenticated request to protected endpoint
        response = production_client.get("/v1/auth/status", headers=auth_headers_valid)

        # Assert: Verify successful authentication
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert response_data["authenticated"] is True
        assert response_data["api_key_prefix"] == "test-pro..."  # Truncated key prefix
        assert "Authentication successful" in response_data["message"]

    def test_production_environment_rejects_invalid_api_key_with_proper_http_error(
        self, production_client, auth_headers_invalid
    ):
        """
        Test production environment returns proper 401 for invalid API keys.
        
        Integration Scope:
            Tests authentication failure flow including custom exception creation,
            HTTP exception conversion, and structured error response generation.
            
        Business Impact:
            Ensures unauthorized users receive clear, actionable error messages
            while protecting system security.
            
        Test Strategy:
            - Configure production environment with valid API key
            - Attempt access with invalid API key
            - Verify proper 401 response with authentication challenge
            
        Success Criteria:
            - Returns 401 Unauthorized status code
            - Includes WWW-Authenticate header for proper HTTP auth flow
            - Error response includes environment context and debugging information
            - No sensitive information exposed in error response
        """
        # Act: Attempt authentication with invalid key
        response = production_client.get("/v1/auth/status", headers=auth_headers_invalid)

        # Assert: Verify proper authentication failure response
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # Verify WWW-Authenticate header for proper HTTP authentication flow
        assert "WWW-Authenticate" in response.headers
        assert response.headers["WWW-Authenticate"] == "Bearer"

        # Verify structured error response with context
        response_data = response.json()
        assert "detail" in response_data
        assert "Invalid API key" in response_data["detail"]["message"]
        assert "environment" in response_data["detail"]["context"]
        assert response_data["detail"]["context"]["environment"] == "production"

    def test_production_environment_rejects_missing_credentials_with_auth_challenge(
        self, production_client
    ):
        """
        Test production environment requires credentials with proper authentication challenge.
        
        Integration Scope:
            Tests missing credentials handling through dependency injection,
            authentication validation, and HTTP exception conversion.
            
        Business Impact:
            Ensures production environments properly challenge unauthenticated
            requests with standard HTTP authentication flows.
            
        Test Strategy:
            - Configure production environment with API keys
            - Make request without authentication headers
            - Verify proper 401 challenge response
            
        Success Criteria:
            - Returns 401 Unauthorized for missing credentials
            - Includes proper WWW-Authenticate challenge header
            - Error message clearly indicates authentication requirement
            - Response includes environment context for debugging
        """
        # Act: Make unauthenticated request to protected endpoint
        response = production_client.get("/v1/auth/status")

        # Assert: Verify authentication challenge
        assert response.status_code == status.HTTP_401_UNAUTHORIZED
        assert "WWW-Authenticate" in response.headers

        response_data = response.json()
        assert "API key required" in response_data["detail"]["message"]
        assert response_data["detail"]["context"]["environment"] == "production"

    def test_development_environment_allows_unauthenticated_access(
        self, client, development_environment
    ):
        """
        Test development environment allows access without authentication.
        
        Integration Scope:
            Tests development mode flow through environment detection,
            security policy determination, and development mode response.
            
        Business Impact:
            Enables frictionless local development without requiring
            API key configuration while maintaining security awareness.
            
        Test Strategy:
            - Configure development environment with no API keys
            - Make unauthenticated request to protected endpoint
            - Verify successful access with development mode indicators
            
        Success Criteria:
            - Returns 200 status indicating successful access
            - Response indicates development mode operation
            - Includes appropriate warnings about development mode
            - Authentication context shows development mode status
        """
        # Act: Make unauthenticated request in development environment
        response = client.get("/v1/auth/status")

        # Assert: Verify development mode access
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert response_data["authenticated"] is True
        assert response_data["api_key_prefix"] == "developm..."
        assert "Authentication successful" in response_data["message"]

    def test_development_environment_authenticates_valid_keys_normally(
        self, development_with_keys_client
    ):
        """
        Test development environment with configured keys works normally.

        Integration Scope:
            Tests mixed development configuration where environment is development
            but API keys are configured, ensuring normal authentication flow.

        Business Impact:
            Supports development environments that choose to use authentication
            while maintaining development-appropriate behavior.

        Test Strategy:
            - Configure development environment with API key
            - Make authenticated request with valid key
            - Verify normal authentication with development context

        Success Criteria:
            - Returns 200 for valid authentication
            - Shows actual API key prefix (not "development")
            - Includes development environment context
            - Functions identically to production authentication
        """
        # Arrange: Prepare valid authentication for development environment
        auth_headers = {"Authorization": "Bearer test-dev-key"}

        # Act: Make authenticated request in development environment
        response = development_with_keys_client.get("/v1/auth/status", headers=auth_headers)

        # Assert: Verify normal authentication in development
        assert response.status_code == status.HTTP_200_OK

        response_data = response.json()
        assert response_data["authenticated"] is True
        assert response_data["api_key_prefix"] == "test-dev..."  # Real key prefix
        assert "Authentication successful" in response_data["message"]

    def test_environment_detection_failure_defaults_to_production_security(
        self, clean_environment
    ):
        """
        Test system defaults to production security when environment detection fails.

        Integration Scope:
            Tests fallback behavior when environment detection service fails,
            ensuring system defaults to secure production mode.

        Business Impact:
            Ensures system security is maintained even when environment
            detection fails, preventing accidental security bypasses.

        Test Strategy:
            - Configure environment that causes detection failure
            - Attempt unauthenticated access
            - Verify system defaults to production security requirements

        Success Criteria:
            - Requires authentication even with detection failure
            - Returns 401 for missing credentials
            - Error context indicates fallback to production security
            - System maintains secure defaults under failure conditions
        """
        # Arrange: Configure environment that may cause detection uncertainty
        clean_environment.setenv("API_KEY", "fallback-test-key")
        # Intentionally leave ENVIRONMENT undefined to test detection failure handling

        # Create client AFTER environment is configured
        from fastapi.testclient import TestClient
        from app.main import create_app
        with TestClient(create_app()) as client:
            # Act: Make unauthenticated request with uncertain environment
            response = client.get("/v1/auth/status")

            # Assert: Verify fallback to production security
            assert response.status_code == status.HTTP_401_UNAUTHORIZED

            response_data = response.json()
            assert "API key required" in response_data["detail"]["message"]
            # Should indicate production security enforcement as fallback
            context = response_data["detail"]["context"]
            assert context["credentials_provided"] is False
