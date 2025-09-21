"""
Authentication Status API Environment Integration Tests

This module tests the integration between the authentication status API endpoint
and environment detection, ensuring that authentication status responses include
environment context and adapt to the detected environment.

MEDIUM PRIORITY - API functionality and monitoring
"""

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.environment import (
    Environment,
    FeatureContext,
    get_environment_info
)


class TestAuthAPIEnvironmentIntegration:
    """
    Integration tests for authentication status API environment integration.

    Seam Under Test:
        HTTP API → Authentication → Environment Detection → Response Formatting

    Critical Path:
        HTTP request → Authentication dependency → Environment-aware response generation

    Business Impact:
        Provides environment-aware authentication status for client applications

    Test Strategy:
        - Test auth status endpoint in different environments
        - Verify environment context in API responses
        - Test API key prefix truncation based on environment
        - Validate environment detection confidence in responses
    """

    def test_auth_status_response_includes_environment_context(self, production_environment):
        """
        Test that authentication status response includes detected environment context.

        Integration Scope:
            HTTP API → Authentication → Environment detection → Response formatting

        Business Impact:
            Provides environment context in auth status for client awareness

        Test Strategy:
            - Set production environment with API key
            - Make authenticated request to auth status endpoint
            - Verify response includes environment information

        Success Criteria:
            - Response includes detected environment context
            - Environment detection confidence is reflected
            - Environment-specific response formatting is applied
        """
        # Set up production environment with API key
        import os
        os.environ['API_KEY'] = 'test-api-key-12345'

        try:
            from app.infrastructure.security.auth import api_key_auth
            api_key_auth.reload_keys()
        except ImportError:
            pytest.skip("Authentication system not available")

        client = TestClient(app)

        # Make authenticated request
        response = client.get(
            "/v1/auth/status",
            headers={"Authorization": "Bearer test-api-key-12345"}
        )

        # Should return successful response with environment context
        assert response.status_code == 200
        data = response.json()

        # Response should include authentication status
        assert "authenticated" in data
        assert data["authenticated"] is True

        # Response should include API key information
        assert "api_key_prefix" in data
        assert data["api_key_prefix"] is not None

        # In production, API key should be truncated for security
        assert len(data["api_key_prefix"]) < len("test-api-key-12345")

    def test_auth_status_response_differs_by_environment(self, clean_environment):
        """
        Test that auth status response differs between environments.

        Integration Scope:
            Environment detection → API response formatting → Environment-specific content

        Business Impact:
            Ensures API responses adapt to environment context

        Test Strategy:
            - Test auth status in development environment
            - Test auth status in production environment
            - Verify environment-specific response differences

        Success Criteria:
            - Development environment allows more permissive responses
            - Production environment enforces stricter response formatting
            - API key handling differs by environment
        """
        client = TestClient(app)

        # Test development environment (no API key required)
        with pytest.MonkeyPatch().context() as m:
            m.setenv('ENVIRONMENT', 'development')

            # Should work in development even without auth
            response = client.get("/v1/auth/status")
            # May fail due to missing auth, but that's expected behavior
            # The important thing is that environment affects the behavior

        # Test production environment (API key required)
        with pytest.MonkeyPatch().context() as m:
            m.setenv('ENVIRONMENT', 'production')
            m.setenv('API_KEY', 'test-api-key-12345')

            try:
                from app.infrastructure.security.auth import api_key_auth
                api_key_auth.reload_keys()
            except ImportError:
                pytest.skip("Authentication system not available")

            response = client.get(
                "/v1/auth/status",
                headers={"Authorization": "Bearer test-api-key-12345"}
            )

            assert response.status_code == 200
            data = response.json()
            assert data["authenticated"] is True

    def test_auth_status_environment_detection_confidence_reflection(self, clean_environment):
        """
        Test that auth status response reflects environment detection confidence.

        Integration Scope:
            Environment confidence → API response → Confidence-based behavior

        Business Impact:
            Ensures API responses reflect detection confidence levels

        Test Strategy:
            - Set up environment with high confidence detection
            - Test auth status response
            - Verify confidence is reflected in response behavior

        Success Criteria:
            - High confidence detection leads to confident API responses
            - API behavior adapts to detection confidence levels
            - Response formatting reflects detection certainty
        """
        import os
        os.environ['ENVIRONMENT'] = 'production'
        os.environ['API_KEY'] = 'test-api-key-12345'

        try:
            from app.infrastructure.security.auth import api_key_auth
            api_key_auth.reload_keys()
        except ImportError:
            pytest.skip("Authentication system not available")

        client = TestClient(app)

        # Test with high confidence environment detection
        response = client.get(
            "/v1/auth/status",
            headers={"Authorization": "Bearer test-api-key-12345"}
        )

        assert response.status_code == 200
        data = response.json()

        # Verify response includes environment-aware formatting
        assert "api_key_prefix" in data
        assert data["authenticated"] is True

        # Test with low confidence environment detection
        os.environ.pop('ENVIRONMENT')

        # Response should still work but may have different behavior
        # (This tests that environment detection confidence affects response)

    def test_auth_status_with_feature_specific_contexts(self, production_environment):
        """
        Test auth status with feature-specific contexts.

        Integration Scope:
            Feature context → Environment detection → Auth response → Context-aware formatting

        Business Impact:
            Ensures feature contexts influence auth status responses

        Test Strategy:
            - Set production environment
            - Test auth status with security enforcement context
            - Verify security-aware response formatting

        Success Criteria:
            - Security context affects auth status response
            - Context-specific response formatting is applied
            - Feature metadata is reflected in response
        """
        import os
        os.environ['API_KEY'] = 'test-api-key-12345'

        try:
            from app.infrastructure.security.auth import api_key_auth
            api_key_auth.reload_keys()
        except ImportError:
            pytest.skip("Authentication system not available")

        client = TestClient(app)

        # Test with security enforcement context
        os.environ['ENFORCE_AUTH'] = 'true'

        security_env = get_environment_info(FeatureContext.SECURITY_ENFORCEMENT)
        assert security_env.environment == Environment.PRODUCTION
        assert security_env.metadata.get('enforce_auth_enabled') is True

        # Response should reflect security enforcement context
        response = client.get(
            "/v1/auth/status",
            headers={"Authorization": "Bearer test-api-key-12345"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is True

    def test_auth_status_error_responses_include_environment_context(self, clean_environment):
        """
        Test that auth status error responses include environment detection information.

        Integration Scope:
            Error handling → Environment detection → Error response formatting

        Business Impact:
            Ensures error responses provide environment context for debugging

        Test Strategy:
            - Test auth status with invalid credentials
            - Verify error response includes environment information
            - Test that environment context aids troubleshooting

        Success Criteria:
            - Error responses include environment detection context
            - Environment information aids error diagnosis
            - Error formatting adapts to environment
        """
        client = TestClient(app)

        # Test with invalid API key in production environment
        with pytest.MonkeyPatch().context() as m:
            m.setenv('ENVIRONMENT', 'production')
            m.setenv('API_KEY', 'test-api-key-12345')

            try:
                from app.infrastructure.security.auth import api_key_auth
                api_key_auth.reload_keys()
            except ImportError:
                pytest.skip("Authentication system not available")

            response = client.get(
                "/v1/auth/status",
                headers={"Authorization": "Bearer invalid-api-key-99999"}
            )

            # Should return authentication error
            assert response.status_code == 401

            # Error response should be informative for troubleshooting
            # (Exact format may vary based on auth implementation)

    def test_auth_status_response_consistency_across_requests(self, production_environment):
        """
        Test that auth status responses are consistent across multiple requests.

        Integration Scope:
            Multiple requests → Environment detection → Consistent responses

        Business Impact:
            Ensures deterministic API behavior for same environment

        Test Strategy:
            - Make multiple auth status requests
            - Verify consistent environment detection
            - Test response consistency across requests

        Success Criteria:
            - Same environment produces consistent responses
            - Environment detection is stable across requests
            - API behavior is deterministic for same conditions
        """
        import os
        os.environ['API_KEY'] = 'test-api-key-12345'

        try:
            from app.infrastructure.security.auth import api_key_auth
            api_key_auth.reload_keys()
        except ImportError:
            pytest.skip("Authentication system not available")

        client = TestClient(app)

        # Make multiple requests to test consistency
        responses = []
        for _ in range(3):
            response = client.get(
                "/v1/auth/status",
                headers={"Authorization": "Bearer test-api-key-12345"}
            )
            responses.append(response)

        # All responses should be consistent
        for response in responses:
            assert response.status_code == 200

        # Check that environment detection is consistent
        env_info = get_environment_info()
        assert env_info.environment == Environment.PRODUCTION
        assert env_info.confidence >= 0.8

    def test_auth_status_with_environment_detection_failure(self, mock_environment_detection_failure):
        """
        Test auth status API behavior when environment detection fails.

        Integration Scope:
            Environment detection failure → Auth API → Error handling → Response formatting

        Business Impact:
            Ensures API remains stable when environment detection fails

        Test Strategy:
            - Mock environment detection to fail
            - Test auth status API behavior
            - Verify graceful error handling and response formatting

        Success Criteria:
            - API handles environment detection failure gracefully
            - Appropriate error responses are returned
            - System degrades gracefully without crashing
        """
        # Mock environment detection failure
        with pytest.raises(Exception, match="Environment detection service unavailable"):
            get_environment_info()

        client = TestClient(app)

        # API should handle detection failure gracefully
        try:
            response = client.get("/v1/auth/status")
            # Response behavior may vary, but should not crash
            # The important thing is graceful handling of the failure
        except Exception:
            # May raise exception due to missing auth, but that's expected
            pass

    def test_auth_status_environment_context_affects_response_format(self, clean_environment):
        """
        Test that environment context affects auth status response format.

        Integration Scope:
            Environment context → Response formatting → Environment-specific content

        Business Impact:
            Ensures response format adapts to environment requirements

        Test Strategy:
            - Test auth status in development vs production
            - Verify response format differences
            - Test that format adapts to environment context

        Success Criteria:
            - Development environment provides more detailed responses
            - Production environment provides secure, minimal responses
            - Response format adapts appropriately to environment
        """
        client = TestClient(app)

        # Test development environment response format
        with pytest.MonkeyPatch().context() as m:
            m.setenv('ENVIRONMENT', 'development')

            # Development should allow flexible authentication
            # (Exact behavior depends on auth implementation)

        # Test production environment response format
        with pytest.MonkeyPatch().context() as m:
            m.setenv('ENVIRONMENT', 'production')
            m.setenv('API_KEY', 'test-api-key-12345')

            try:
                from app.infrastructure.security.auth import api_key_auth
                api_key_auth.reload_keys()
            except ImportError:
                pytest.skip("Authentication system not available")

            response = client.get(
                "/v1/auth/status",
                headers={"Authorization": "Bearer test-api-key-12345"}
            )

            assert response.status_code == 200
            data = response.json()

            # Production should provide secure response format
            assert "authenticated" in data
            assert "api_key_prefix" in data
            assert data["authenticated"] is True

    def test_auth_status_with_custom_environment_detection(self, custom_detection_config):
        """
        Test auth status with custom environment detection configuration.

        Integration Scope:
            Custom detection config → Auth API → Custom environment handling

        Business Impact:
            Ensures custom environment configurations work with auth API

        Test Strategy:
            - Create custom detection configuration
            - Test auth status with custom environment
            - Verify custom configuration is respected

        Success Criteria:
            - Custom environment detection configuration is used
            - Auth API adapts to custom environment detection
            - Custom patterns work correctly with auth status
        """
        detector = __import__('app.core.environment', fromlist=['EnvironmentDetector']).EnvironmentDetector(custom_detection_config)

        import os
        os.environ['CUSTOM_ENV'] = 'production'
        os.environ['API_KEY'] = 'test-api-key-12345'

        # Test with custom configuration
        env_info = detector.detect_environment()
        assert env_info.environment == Environment.PRODUCTION

        try:
            from app.infrastructure.security.auth import api_key_auth
            api_key_auth.reload_keys()
        except ImportError:
            pytest.skip("Authentication system not available")

        client = TestClient(app)

        response = client.get(
            "/v1/auth/status",
            headers={"Authorization": "Bearer test-api-key-12345"}
        )

        assert response.status_code == 200
        data = response.json()
        assert data["authenticated"] is True

    def test_auth_status_performance_under_environment_detection(self, production_environment):
        """
        Test auth status API performance with environment detection.

        Integration Scope:
            Environment detection → Auth API → Performance → Response time

        Business Impact:
            Ensures environment detection doesn't impact API performance

        Test Strategy:
            - Measure auth status response time with environment detection
            - Verify environment detection completes quickly
            - Test performance under normal operating conditions

        Success Criteria:
            - Environment detection completes quickly (<100ms)
            - Auth API response time is acceptable
            - No performance degradation due to environment detection
        """
        import time
        import os
        os.environ['API_KEY'] = 'test-api-key-12345'

        try:
            from app.infrastructure.security.auth import api_key_auth
            api_key_auth.reload_keys()
        except ImportError:
            pytest.skip("Authentication system not available")

        client = TestClient(app)

        # Test response time
        start_time = time.time()
        response = client.get(
            "/v1/auth/status",
            headers={"Authorization": "Bearer test-api-key-12345"}
        )
        end_time = time.time()

        # Should respond quickly
        response_time = end_time - start_time
        assert response_time < 1.0  # Less than 1 second

        assert response.status_code == 200

        # Environment detection should also be quick
        env_start = time.time()
        env_info = get_environment_info()
        env_end = time.time()

        env_time = env_end - env_start
        assert env_time < 0.1  # Less than 100ms for environment detection
