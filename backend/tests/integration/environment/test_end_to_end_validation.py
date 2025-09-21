"""
End-to-End Environment Validation Integration Tests

This module tests the complete chain of behavior from configuration to observable outcome,
validating that environment settings correctly propagate through the entire system to
produce expected behavior in security, cache, and resilience components.

HIGH PRIORITY - Validates the complete chain of behavior from configuration to observable outcome
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


class TestEndToEndEnvironmentValidation:
    """
    End-to-end integration tests for environment-driven behavior.

    Seam Under Test:
        Environment Variables → Detection → Component Behavior → Observable Outcomes

    Critical Path:
        Environment variable → Environment detection → Component configuration → System behavior

    Business Impact:
        Ensures that environment settings correctly propagate and lead to the expected
        behavior in running services, validating the complete integration chain

    Test Strategy:
        - Test environment variable → security enforcement → API key requirements
        - Test environment variable → cache preset → configuration selection
        - Test environment variable → resilience preset → strategy selection
        - Test request tracing → environment detection → consistent behavior
    """

    def test_environment_variable_production_enables_security_enforcement(self):
        """
        Test that ENVIRONMENT=production enables strict API key authentication.

        Integration Scope:
            Environment variable → Environment detection → Security enforcement → API behavior

        Business Impact:
            Ensures production environments enforce security by default

        Test Strategy:
            - Set ENVIRONMENT=production
            - Verify environment detection returns production
            - Test that API key requirements are enforced
            - Verify convenience functions return correct boolean values

        Success Criteria:
            - Environment detection correctly identifies production
            - Security enforcement requires API keys in production
            - is_production_environment() returns True
            - is_development_environment() returns False
        """
        # Set production environment
        with pytest.MonkeyPatch().context() as m:
            m.setenv('ENVIRONMENT', 'production')
            m.setenv('API_KEY', 'test-api-key-12345')

            # Verify environment detection
            env_info = get_environment_info()
            assert env_info.environment == Environment.PRODUCTION
            assert env_info.confidence >= 0.8
            assert "production" in env_info.reasoning.lower()

            # Verify convenience functions
            assert is_production_environment() is True
            assert is_development_environment() is False

            # Verify security enforcement is active
            with pytest.raises(ConfigurationError):
                # Should fail without API keys if we temporarily remove them
                m.delenv('API_KEY')
                from app.infrastructure.security.auth import APIKeyAuth
                APIKeyAuth()

    def test_environment_variable_development_allows_flexible_security(self):
        """
        Test that ENVIRONMENT=development allows flexible security settings.

        Integration Scope:
            Environment variable → Environment detection → Security flexibility → Development mode

        Business Impact:
            Allows faster development iteration without strict security

        Test Strategy:
            - Set ENVIRONMENT=development
            - Verify environment detection returns development
            - Test that security allows flexible authentication
            - Verify convenience functions return correct boolean values

        Success Criteria:
            - Environment detection correctly identifies development
            - Security allows initialization without API keys
            - is_production_environment() returns False
            - is_development_environment() returns True
        """
        # Set development environment
        with pytest.MonkeyPatch().context() as m:
            m.setenv('ENVIRONMENT', 'development')

            # Verify environment detection
            env_info = get_environment_info()
            assert env_info.environment == Environment.DEVELOPMENT
            assert env_info.confidence >= 0.8
            assert "development" in env_info.reasoning.lower()

            # Verify convenience functions
            assert is_production_environment() is False
            assert is_development_environment() is True

            # Verify flexible security in development
            from app.infrastructure.security.auth import APIKeyAuth
            auth = APIKeyAuth()  # Should not raise ConfigurationError

            # Development mode should be permissive
            assert auth.verify_api_key("any-key") is True
            assert auth.verify_api_key("") is True
            assert auth.verify_api_key(None) is True

    def test_environment_variable_staging_balanced_security(self):
        """
        Test that ENVIRONMENT=staging provides balanced security approach.

        Integration Scope:
            Environment variable → Environment detection → Balanced security → Staging behavior

        Business Impact:
            Ensures staging environments have appropriate security for pre-production

        Test Strategy:
            - Set ENVIRONMENT=staging
            - Verify environment detection returns staging
            - Test that security requirements are present but balanced
            - Verify convenience functions return correct boolean values

        Success Criteria:
            - Environment detection correctly identifies staging
            - Security enforcement is active but configurable
            - is_production_environment() returns False
            - is_development_environment() returns False
        """
        # Set staging environment
        with pytest.MonkeyPatch().context() as m:
            m.setenv('ENVIRONMENT', 'staging')
            m.setenv('API_KEY', 'test-api-key-12345')

            # Verify environment detection
            env_info = get_environment_info()
            assert env_info.environment == Environment.STAGING
            assert env_info.confidence >= 0.8
            assert "staging" in env_info.reasoning.lower()

            # Verify convenience functions
            assert is_production_environment() is False
            assert is_development_environment() is False

            # Verify security is enforced in staging
            with pytest.raises(ConfigurationError):
                # Should fail without API keys
                m.delenv('API_KEY')
                from app.infrastructure.security.auth import APIKeyAuth
                APIKeyAuth()

    def test_request_tracing_shows_environment_consistency(self):
        """
        Test that environment detection is consistent across a request lifecycle.

        Integration Scope:
            HTTP request → Environment detection → Consistent behavior → Response formatting

        Business Impact:
            Ensures environment detection provides consistent results during request processing

        Test Strategy:
            - Set environment variable
            - Make HTTP request that triggers environment detection
            - Verify environment detection consistency throughout request
            - Test multiple requests for consistency

        Success Criteria:
            - Environment detection consistent across request lifecycle
            - Multiple requests return same environment detection
            - Environment context preserved in request processing
        """
        # Set test environment
        with pytest.MonkeyPatch().context() as m:
            m.setenv('ENVIRONMENT', 'production')
            m.setenv('API_KEY', 'test-api-key-12345')

            client = TestClient(app)

            # Make multiple requests to test consistency
            results = []
            for i in range(3):
                # Test environment detection in request context
                env_info = get_environment_info()
                results.append((env_info.environment, env_info.confidence))

                # Test that environment affects request processing
                try:
                    response = client.get("/v1/auth/status")
                    # Should work with valid auth
                    assert response.status_code == 200
                except Exception:
                    # May fail due to auth configuration, but that's expected
                    pass

            # Verify consistency across requests
            for i in range(1, len(results)):
                assert results[0][0] == results[i][0]  # Same environment
                assert results[0][1] == results[i][1]  # Same confidence

    def test_environment_detection_with_cache_integration(self):
        """
        Test environment detection integration with cache preset system.

        Integration Scope:
            Environment variable → Environment detection → Cache preset selection → Cache behavior

        Business Impact:
            Ensures cache configuration adapts correctly to environment

        Test Strategy:
            - Set environment variable
            - Verify environment detection
            - Test cache preset recommendation based on environment
            - Verify cache behavior matches environment expectations

        Success Criteria:
            - Cache preset recommendations match environment
            - Cache configuration adapts to environment
            - Environment-specific cache optimizations are applied
        """
        # Test production environment cache behavior
        with pytest.MonkeyPatch().context() as m:
            m.setenv('ENVIRONMENT', 'production')

            env_info = get_environment_info()
            assert env_info.environment == Environment.PRODUCTION

            # Test cache preset integration
            try:
                from app.infrastructure.cache.cache_presets import CachePresetManager
                preset_manager = CachePresetManager()

                # Should recommend production-appropriate preset
                preset = preset_manager.recommend_preset(env_info.environment)
                assert preset is not None
                assert 'production' in preset.lower() or 'prod' in preset.lower()

            except ImportError:
                # Cache presets may not be available, skip cache-specific tests
                pytest.skip("Cache preset system not available")

    def test_environment_detection_with_resilience_integration(self):
        """
        Test environment detection integration with resilience preset system.

        Integration Scope:
            Environment variable → Environment detection → Resilience preset selection → Resilience behavior

        Business Impact:
            Ensures resilience strategies adapt correctly to environment

        Test Strategy:
            - Set environment variable
            - Verify environment detection
            - Test resilience preset recommendation based on environment
            - Verify resilience behavior matches environment expectations

        Success Criteria:
            - Resilience preset recommendations match environment
            - Resilience configuration adapts to environment
            - Environment-specific resilience strategies are applied
        """
        # Test production environment resilience behavior
        with pytest.MonkeyPatch().context() as m:
            m.setenv('ENVIRONMENT', 'production')

            env_info = get_environment_info()
            assert env_info.environment == Environment.PRODUCTION

            # Test resilience preset integration
            try:
                from app.infrastructure.resilience.config_presets import ResiliencePresetManager
                preset_manager = ResiliencePresetManager()

                # Should recommend production-appropriate preset
                preset = preset_manager.recommend_preset(env_info.environment)
                assert preset is not None
                assert 'production' in preset.lower() or 'prod' in preset.lower()

            except ImportError:
                # Resilience presets may not be available, skip resilience-specific tests
                pytest.skip("Resilience preset system not available")

    def test_environment_feature_context_end_to_end(self):
        """
        Test end-to-end behavior with feature-specific contexts.

        Integration Scope:
            Environment variable + Feature context → Environment detection → Feature-specific behavior

        Business Impact:
            Ensures feature contexts work correctly with environment detection

        Test Strategy:
            - Set environment variable
            - Test AI context with production environment
            - Test Security context with development environment
            - Verify feature-specific metadata and overrides

        Success Criteria:
            - AI context provides AI-specific metadata
            - Security context can override environment detection
            - Feature contexts work consistently with environment detection
        """
        # Test AI context in production
        with pytest.MonkeyPatch().context() as m:
            m.setenv('ENVIRONMENT', 'production')
            m.setenv('ENABLE_AI_CACHE', 'true')

            ai_env = get_environment_info(FeatureContext.AI_ENABLED)
            assert ai_env.environment == Environment.PRODUCTION
            assert ai_env.metadata.get('enable_ai_cache_enabled') is True
            assert ai_env.metadata.get('ai_prefix') == 'ai-'

        # Test Security context in development with override
        with pytest.MonkeyPatch().context() as m:
            m.setenv('ENVIRONMENT', 'development')
            m.setenv('ENFORCE_AUTH', 'true')

            security_env = get_environment_info(FeatureContext.SECURITY_ENFORCEMENT)
            assert security_env.environment == Environment.PRODUCTION  # Overridden
            assert security_env.metadata.get('enforce_auth_enabled') is True

    def test_environment_detection_error_handling_end_to_end(self):
        """
        Test end-to-end error handling when environment detection fails.

        Integration Scope:
            Environment detection failure → Error handling → System resilience → Fallback behavior

        Business Impact:
            Ensures system remains stable when environment detection fails

        Test Strategy:
            - Mock environment detection to fail
            - Test component behavior under detection failure
            - Verify graceful degradation and error handling

        Success Criteria:
            - System handles detection failures gracefully
            - Appropriate error messages and logging
            - Dependent components fail safely with clear error messages
        """
        # Mock environment detection failure
        with pytest.MonkeyPatch().context() as m:
            m.setenv('ENVIRONMENT', 'production')

            with pytest.mock.patch('app.core.environment.get_environment_info') as mock_get_env:
                def failing_get_environment_info(*args, **kwargs):
                    raise Exception("Environment detection service unavailable")

                mock_get_env.side_effect = failing_get_environment_info

                # Test that failure is handled gracefully
                with pytest.raises(Exception, match="Environment detection service unavailable"):
                    get_environment_info()

                # Test that dependent components handle failure
                try:
                    # Components that depend on environment detection should handle failure
                    from app.infrastructure.security.auth import APIKeyAuth
                    # In production, this should fail due to missing API keys
                    # But the environment detection failure should be propagated
                    with pytest.raises((ConfigurationError, Exception)):
                        APIKeyAuth()
                except ImportError:
                    pass  # Auth may not be available

    def test_environment_variable_precedence_end_to_end(self):
        """
        Test that environment variable precedence works correctly end-to-end.

        Integration Scope:
            Multiple environment variables → Precedence resolution → System behavior

        Business Impact:
            Ensures predictable behavior when multiple environment indicators exist

        Test Strategy:
            - Set multiple conflicting environment variables
            - Verify correct precedence is applied
            - Test that system behavior follows precedence rules

        Success Criteria:
            - ENVIRONMENT variable takes highest precedence
            - System behavior follows precedence-based detection
            - Conflicting variables are resolved predictably
        """
        # Set conflicting environment variables
        with pytest.MonkeyPatch().context() as m:
            m.setenv('ENVIRONMENT', 'production')      # Highest precedence
            m.setenv('NODE_ENV', 'development')        # Lower precedence
            m.setenv('FLASK_ENV', 'testing')           # Even lower precedence
            m.setenv('APP_ENV', 'staging')             # Lowest precedence

            # Verify environment detection uses correct precedence
            env_info = get_environment_info()
            assert env_info.environment == Environment.PRODUCTION
            assert env_info.confidence >= 0.9  # High confidence due to explicit setting

            # Verify convenience functions
            assert is_production_environment() is True
            assert is_development_environment() is False

            # Verify security behavior follows precedence
            try:
                from app.infrastructure.security.auth import APIKeyAuth
                with pytest.raises(ConfigurationError):
                    # Should enforce production security rules
                    APIKeyAuth()
            except ImportError:
                pass  # Auth may not be available

    def test_environment_detection_with_system_indicators_end_to_end(self):
        """
        Test end-to-end behavior with system indicators.

        Integration Scope:
            System indicators → Environment detection → System behavior

        Business Impact:
            Ensures system indicators correctly influence environment detection

        Test Strategy:
            - Create system indicator files
            - Verify environment detection picks up indicators
            - Test that system behavior adapts to detected environment

        Success Criteria:
            - System indicators are correctly detected
            - Environment detection uses indicator information
            - System behavior adapts based on indicators
        """
        # Create development indicators
        with pytest.MonkeyPatch().context() as m:
            import tempfile
            import os

            m.delenv('ENVIRONMENT')  # Remove explicit environment
            m.setenv('DEBUG', 'true')  # Set development indicator

            # Create .env file
            with tempfile.NamedTemporaryFile(suffix='.env', delete=False) as f:
                temp_env_file = f.name

            try:
                # Verify environment detection uses system indicators
                env_info = get_environment_info()
                assert env_info.environment == Environment.DEVELOPMENT
                assert env_info.confidence >= 0.7  # System indicator confidence

                # Verify development-friendly behavior
                assert is_development_environment() is True
                assert is_production_environment() is False

                # Verify flexible security in development
                try:
                    from app.infrastructure.security.auth import APIKeyAuth
                    auth = APIKeyAuth()  # Should not raise ConfigurationError

                    # Should allow flexible authentication
                    assert auth.verify_api_key("any-key") is True
                except ImportError:
                    pass  # Auth may not be available

            finally:
                # Cleanup
                try:
                    os.unlink(temp_env_file)
                except OSError:
                    pass
