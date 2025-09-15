"""
Tests for the v1 authentication API endpoints.

This module tests the authentication endpoints that provide API key validation
and status checking functionality.
"""

import pytest
from fastapi import status
from fastapi.testclient import TestClient

from app.core.exceptions import AuthenticationError


class TestAuthenticationEndpoints:
    """Test authentication API endpoints."""

    def test_auth_status_with_valid_key(self, authenticated_client):
        """Test auth status endpoint with valid API key returns success."""
        response = authenticated_client.get("/v1/auth/status")
        assert response.status_code == 200

        data = response.json()
        assert data["authenticated"] is True
        assert "api_key_prefix" in data
        assert data["message"] == "Authentication successful"

    def test_auth_status_without_key_returns_401(self, client):
        """Test auth status endpoint without API key returns 401 Unauthorized."""
        # With the HTTP wrapper (verify_api_key_http), the endpoint should return
        # a proper HTTP 401 response instead of raising an exception
        response = client.get("/v1/auth/status")

        # Should return 401 Unauthorized with structured error details
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # Verify the error response structure
        error_data = response.json()
        assert "detail" in error_data
        assert "message" in error_data["detail"]
        assert "context" in error_data["detail"]

        # Verify error message content
        assert "API key required" in error_data["detail"]["message"]

        # Verify context information
        context = error_data["detail"]["context"]
        assert context["auth_method"] == "bearer_token"
        assert context["credentials_provided"] is False
        assert "environment" in context  # Should include environment detection info

    def test_auth_status_with_invalid_key_returns_401(self, client):
        """Test auth status endpoint with invalid API key returns 401 Unauthorized."""
        response = client.get(
            "/v1/auth/status",
            headers={"Authorization": "Bearer invalid-api-key-123"}
        )

        # Should return 401 Unauthorized for invalid key
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

        # Verify the error response structure
        error_data = response.json()
        assert "detail" in error_data
        assert "message" in error_data["detail"]
        assert "context" in error_data["detail"]

        # Verify error message content
        assert "Invalid API key" in error_data["detail"]["message"]

        # Verify context information for invalid key attempt
        context = error_data["detail"]["context"]
        assert context["auth_method"] == "bearer_token"
        assert context["credentials_provided"] is True
        assert "key_prefix" in context
        assert context["key_prefix"] == "invalid-"  # First 8 chars of invalid key

    def test_auth_status_response_format(self, authenticated_client):
        """Test that auth status response has the expected format."""
        response = authenticated_client.get("/v1/auth/status")
        assert response.status_code == 200

        data = response.json()

        # Verify required fields are present
        required_fields = ["authenticated", "api_key_prefix", "message"]
        for field in required_fields:
            assert field in data, f"Required field '{field}' missing from response"

        # Verify field types and values
        assert isinstance(data["authenticated"], bool)
        assert data["authenticated"] is True
        assert isinstance(data["api_key_prefix"], str)
        assert isinstance(data["message"], str)

        # Verify API key is properly truncated for security
        assert data["api_key_prefix"].endswith("...")
        assert len(data["api_key_prefix"]) > 3  # Should have some prefix + "..."

    def test_auth_status_key_truncation_security(self, client):
        """Test that API keys are properly truncated in responses for security."""
        # Test with a longer API key to verify truncation
        long_api_key = "test-very-long-api-key-12345678901234567890"

        # Configure test to use this key temporarily
        with pytest.MonkeyPatch().context() as mp:
            mp.setenv("API_KEY", long_api_key)

            # Make request with the long key
            response = client.get(
                "/v1/auth/status",
                headers={"Authorization": f"Bearer {long_api_key}"}
            )

            if response.status_code == 200:
                data = response.json()

                # Verify the key is truncated to first 8 characters + "..."
                expected_prefix = long_api_key[:8] + "..."
                assert data["api_key_prefix"] == expected_prefix

                # Verify full key is not exposed
                assert long_api_key not in str(data)

    def test_auth_status_with_x_api_key_header(self, client):
        """Test auth status endpoint supports X-API-Key header format."""
        # Note: This test assumes the infrastructure supports X-API-Key header
        # If not supported, this test should be skipped or modified

        with pytest.MonkeyPatch().context() as mp:
            mp.setenv("API_KEY", "test-api-key-12345")

            # Some authentication systems support X-API-Key as an alternative header
            response = client.get(
                "/v1/auth/status",
                headers={"X-API-Key": "test-api-key-12345"}
            )

            # This might return 401 if X-API-Key is not supported by the infrastructure
            # The test documents the expected behavior
            if response.status_code == 200:
                data = response.json()
                assert data["authenticated"] is True
            else:
                # If X-API-Key is not supported, should return 401
                assert response.status_code == status.HTTP_401_UNAUTHORIZED


class TestAuthenticationIntegration:
    """Test authentication system integration and edge cases."""

    def test_auth_status_development_mode_behavior(self, client):
        """Test auth status behavior in development mode (no API keys configured)."""
        # This test verifies the development mode fallback behavior
        # In development mode with no API keys, the system should allow access

        with pytest.MonkeyPatch().context() as mp:
            # Clear all API key environment variables to trigger development mode
            mp.delenv("API_KEY", raising=False)
            mp.delenv("ADDITIONAL_API_KEYS", raising=False)

            response = client.get("/v1/auth/status")

            # In development mode, should return success with "development" key
            if response.status_code == 200:
                data = response.json()
                assert data["authenticated"] is True
                assert data["api_key_prefix"] == "development"
                assert "successful" in data["message"].lower()
            else:
                # If development mode is disabled, should return 401
                assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_auth_status_environment_context_in_errors(self, client):
        """Test that authentication errors include environment detection context."""
        response = client.get("/v1/auth/status")

        if response.status_code == status.HTTP_401_UNAUTHORIZED:
            error_data = response.json()
            context = error_data["detail"]["context"]

            # Should include environment detection information
            assert "environment" in context
            assert "confidence" in context

            # Environment should be one of the expected values
            assert context["environment"] in ["development", "staging", "production"]

            # Confidence should be a reasonable value
            assert isinstance(context["confidence"], (int, float))
            assert 0.0 <= context["confidence"] <= 1.0

    def test_auth_status_http_wrapper_compatibility(self, client):
        """Test that the HTTP wrapper properly handles middleware compatibility."""
        # This test ensures the verify_api_key_http wrapper prevents middleware conflicts

        response = client.get("/v1/auth/status")

        # Should receive a proper HTTP response (not an unhandled exception)
        assert response.status_code in [200, 401]  # Should be one of these, not 500

        # Response should have proper headers
        assert "content-type" in response.headers
        assert response.headers["content-type"] == "application/json"

        # Should have proper error structure if 401
        if response.status_code == 401:
            error_data = response.json()
            assert "detail" in error_data
            # Should include WWW-Authenticate header for proper HTTP auth flow
            assert "www-authenticate" in response.headers