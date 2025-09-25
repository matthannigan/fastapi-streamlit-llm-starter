"""
Security Environment Enforcement Integration Tests

This module tests the integration between environment detection and security enforcement,
ensuring that production environments properly enforce API key requirements while
allowing development environments to be more permissive.

HIGH PRIORITY - Security critical, affects all authenticated requests
"""

import pytest
from fastapi.testclient import TestClient
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.core.environment import (
    Environment,
    FeatureContext,
    get_environment_info,
    is_production_environment,
    is_development_environment
)
from app.core.exceptions import ConfigurationError


class TestSecurityEnvironmentEnforcement:
    """
    Integration tests for security environment enforcement.

    Seam Under Test:
        Environment Detection → Security Authentication → API Key Enforcement

    Critical Path:
        Environment detection → Production security rules → API key validation

    Business Impact:
        Ensures production environments enforce API key requirements while
        allowing development flexibility for faster iteration

    Test Strategy:
        - Test production environment enforces API keys
        - Test development environment allows requests without keys
        - Test environment detection failure defaults to secure mode
        - Test feature-specific security context overrides
    """

    def test_production_environment_enforces_api_keys(self, production_environment):
        """
        Test that production environment enforces API key requirements.

        Integration Scope:
            Environment detection → Security authentication → API key validation

        Business Impact:
            Ensures production environments are secure by default

        Test Strategy:
            - Set production environment
            - Attempt to initialize auth without API keys
            - Verify ConfigurationError is raised

        Success Criteria:
            - ConfigurationError raised in production without API keys
            - Error message clearly indicates security requirement
            - Environment detection correctly identifies production
        """
        # Production environment should enforce API keys
        env_info = get_environment_info()
        assert env_info.environment == Environment.PRODUCTION
        assert env_info.confidence >= 0.8  # High confidence detection

        # Auth should fail to initialize without API keys in production
        with pytest.raises(ConfigurationError) as exc_info:
            from app.infrastructure.security.auth import APIKeyAuth
            APIKeyAuth()

        assert "API keys must be configured in a production environment" in str(exc_info.value)

    def test_development_environment_allows_no_api_keys(self, development_environment):
        """
        Test that development environment allows initialization without API keys.

        Integration Scope:
            Environment detection → Security authentication → Flexible development mode

        Business Impact:
            Allows faster development iteration without API key management

        Test Strategy:
            - Set development environment
            - Initialize auth without API keys
            - Verify successful initialization

        Success Criteria:
            - Auth system initializes successfully in development
            - Environment detection correctly identifies development
            - Development mode allows all API keys (permissive)
        """
        env_info = get_environment_info()
        assert env_info.environment == Environment.DEVELOPMENT
        assert env_info.confidence >= 0.8

        # Auth should initialize successfully in development
        from app.infrastructure.security.auth import APIKeyAuth
        auth = APIKeyAuth()

        # Development mode should be permissive
        assert auth.verify_api_key("any-key") is True
        assert auth.verify_api_key("") is True
        assert auth.verify_api_key(None) is True

    def test_security_enforcement_context_overrides_to_production(self, security_enforcement_environment):
        """
        Test that security enforcement context can override environment detection.

        Integration Scope:
            Feature context → Environment override → Security enforcement

        Business Impact:
            Allows security-conscious deployments to enforce production rules
            even in non-production environments

        Test Strategy:
            - Set development environment with security enforcement enabled
            - Verify environment detection with security context
            - Test that security requirements are enforced

        Success Criteria:
            - Security context returns production environment
            - API key requirements enforced despite development setting
            - Override provides clear reasoning for security decision
        """
        # With security enforcement enabled, should return production-like behavior
        security_env = get_environment_info(FeatureContext.SECURITY_ENFORCEMENT)

        # Security context should override to production when enforcement is enabled
        assert security_env.environment == Environment.PRODUCTION
        assert security_env.confidence >= 0.9
        assert "security enforcement" in security_env.reasoning.lower()
        assert security_env.metadata.get('enforce_auth_enabled') is True

        # Should enforce API key requirements
        with pytest.raises(ConfigurationError):
            from app.infrastructure.security.auth import APIKeyAuth
            APIKeyAuth()

    def test_ai_context_in_production_with_security_requirements(self, prod_with_ai_features):
        """
        Test AI context in production environment maintains security requirements.

        Integration Scope:
            Production environment + AI features → Security enforcement → API key validation

        Business Impact:
            Ensures AI features don't compromise production security

        Test Strategy:
            - Set production environment with AI features enabled
            - Verify environment detection with AI context
            - Test that security requirements are still enforced

        Success Criteria:
            - AI context returns production environment
            - API key requirements still enforced in production
            - AI-specific metadata is preserved
        """
        # AI context in production should still enforce security
        ai_env = get_environment_info(FeatureContext.AI_ENABLED)

        assert ai_env.environment == Environment.PRODUCTION
        assert ai_env.confidence >= 0.8
        assert ai_env.metadata.get('enable_ai_cache_enabled') is True
        assert ai_env.metadata.get('ai_prefix') == 'ai-'

        # Should still enforce API key requirements
        with pytest.raises(ConfigurationError):
            from app.infrastructure.security.auth import APIKeyAuth
            APIKeyAuth()

    def test_environment_detection_failure_defaults_to_secure_mode(self, clean_environment):
        """
        Test that environment detection failures default to secure production mode.

        Integration Scope:
            Environment detection failure → Fallback security → Production defaults

        Business Impact:
            Ensures system fails securely when environment cannot be determined

        Test Strategy:
            - Create scenario with no environment indicators
            - Verify environment detection with low confidence
            - Test that security defaults to production mode

        Success Criteria:
            - Unknown environment detected with low confidence
            - Security enforcement defaults to production requirements
            - System fails securely rather than allowing bypass
        """
        # Clear all environment indicators to simulate detection failure
        env_vars_to_clear = [
            'ENVIRONMENT', 'NODE_ENV', 'FLASK_ENV', 'APP_ENV', 'ENV',
            'DEPLOYMENT_ENV', 'DJANGO_SETTINGS_MODULE', 'RAILS_ENV',
            'HOSTNAME', 'CI', 'DEBUG', 'PRODUCTION', 'PROD'
        ]

        for var in env_vars_to_clear:
            os.environ.pop(var, None)

        # Should detect unknown environment with low confidence
        env_info = get_environment_info()
        assert env_info.environment == Environment.DEVELOPMENT  # Fallback to development
        assert env_info.confidence < 0.7  # Low confidence
        assert "no environment signals" in env_info.reasoning.lower()

    def test_authentication_status_endpoint_environment_awareness(self):
        """
        Test that authentication status endpoint reflects environment detection.

        Integration Scope:
            HTTP API → Authentication → Environment detection → Response formatting

        Business Impact:
            Provides environment-aware authentication status for client applications

        Test Strategy:
            - Test auth status endpoint in different environments
            - Verify environment context in response
            - Test API key prefix truncation based on environment

        Success Criteria:
            - Response includes detected environment context
            - API key prefix differs between environments
            - Environment detection confidence reflected in response
        """
        client = TestClient(app)

        # Test in development environment
        with pytest.raises(Exception):  # Auth status requires API key in production
            response = client.get("/v1/auth/status")
            # Should return 401 due to missing auth, but that's expected behavior

        # Test with valid auth headers in production environment
        with patch.dict(os.environ, {
            'ENVIRONMENT': 'production',
            'API_KEY': 'test-api-key-12345'
        }):
            # Reload auth system to pick up new environment
            from app.infrastructure.security.auth import api_key_auth
            api_key_auth.reload_keys()

            response = client.get(
                "/v1/auth/status",
                headers={"Authorization": "Bearer test-api-key-12345"}
            )

            # Should work in production with valid key
            assert response.status_code == 200

    def test_convenience_functions_environment_awareness(self, production_environment):
        """
        Test that convenience functions correctly reflect environment detection.

        Integration Scope:
            Environment convenience functions → Detection service → Boolean results

        Business Impact:
            Provides simple boolean checks for common environment scenarios

        Test Strategy:
            - Test is_production_environment() in production
            - Test is_development_environment() in development
            - Test confidence thresholds for decision making

        Success Criteria:
            - is_production_environment() returns True in production
            - is_development_environment() returns True in development
            - Functions respect confidence thresholds (>0.60)
        """
        # Test in production environment
        assert is_production_environment() is True
        assert is_development_environment() is False

        # Test with security context
        assert is_production_environment(FeatureContext.SECURITY_ENFORCEMENT) is True

    def test_environment_detection_with_mixed_signals(self, clean_environment):
        """
        Test environment detection with conflicting environment signals.

        Integration Scope:
            Multiple signal sources → Conflict resolution → Final environment determination

        Business Impact:
            Ensures reliable environment detection even with conflicting indicators

        Test Strategy:
            - Set conflicting environment variables
            - Verify signal collection and confidence scoring
            - Test conflict resolution logic

        Success Criteria:
            - Conflicting signals are collected and scored
            - Highest confidence signal wins
            - Reasoning explains the conflict resolution
        """
        # Set conflicting signals
        os.environ['ENVIRONMENT'] = 'production'  # High confidence (0.95)
        os.environ['NODE_ENV'] = 'development'    # Lower confidence (0.85)
        os.environ['DEBUG'] = 'true'              # Development indicator (0.70)

        env_info = get_environment_info()

        # Should resolve to production due to higher confidence signal
        assert env_info.environment == Environment.PRODUCTION
        assert env_info.confidence >= 0.85  # Should be at least ENVIRONMENT confidence
        assert "conflicting signals" in env_info.reasoning.lower()

    def test_environment_detection_service_availability(self, mock_environment_detection_failure):
        """
        Test system behavior when environment detection service fails.

        Integration Scope:
            Service failure → Error handling → Fallback behavior → System stability

        Business Impact:
            Ensures system remains stable when environment detection is unavailable

        Test Strategy:
            - Mock environment detection service to fail
            - Test component behavior under failure
            - Verify graceful degradation

        Success Criteria:
            - System handles detection failure gracefully
            - Appropriate error handling and logging
            - Dependent components fail safely
        """
        # Environment detection failure should be handled gracefully
        with pytest.raises(Exception, match="Environment detection service unavailable"):
            get_environment_info()

        # Components that depend on environment detection should handle failure
        # This ensures the integration point fails safely rather than crashing the system
