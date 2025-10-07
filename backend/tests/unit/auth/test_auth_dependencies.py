"""
Test suite for FastAPI authentication dependency functions.

Tests the authentication dependencies that provide FastAPI integration
for API key validation, including standard dependencies that raise custom
exceptions and HTTP wrapper dependencies for middleware compatibility.

Test Coverage:
    - verify_api_key dependency behavior
    - verify_api_key_with_metadata enhanced dependency
    - optional_verify_api_key conditional authentication
    - verify_api_key_http HTTP exception wrapper
    - Development mode and production authentication flows
"""

import pytest
from unittest.mock import patch, Mock
from fastapi import HTTPException, status, Request
from fastapi.security import HTTPAuthorizationCredentials
from contextlib import contextmanager
from app.infrastructure.security.auth import (
    verify_api_key,
    verify_api_key_with_metadata,
    optional_verify_api_key,
    verify_api_key_http
)
from app.core.exceptions import AuthenticationError


@contextmanager
def mock_auth_config(fake_settings, api_keys_set, mock_env_detection=None, auth_config_patch=None):
    """
    Helper context manager to properly mock auth configuration.

    This context manager patches multiple auth-related dependencies to enable
    isolated testing of authentication logic without requiring full FastAPI
    dependency injection or actual Settings instances.

    Args:
        fake_settings: FakeSettings instance to use for authentication configuration
        api_keys_set: Set of valid API keys for authentication
        mock_env_detection: Optional mock for environment detection (get_environment_info)
        auth_config_patch: Optional mock for auth_config object

    Yields:
        FakeSettings: The fake_settings instance for use in dependency function calls
    """
    # Mock get_settings dependency to return our fake settings
    def mock_get_settings():
        return fake_settings

    with patch('app.infrastructure.security.auth.settings', fake_settings):
        with patch('app.dependencies.get_settings', mock_get_settings):
            with patch('app.infrastructure.security.auth.api_key_auth.api_keys', api_keys_set):
                if auth_config_patch:
                    with patch('app.infrastructure.security.auth.auth_config', auth_config_patch):
                        if mock_env_detection:
                            with patch('app.infrastructure.security.auth.get_environment_info', mock_env_detection):
                                yield fake_settings
                        else:
                            yield fake_settings
                elif mock_env_detection:
                    with patch('app.infrastructure.security.auth.get_environment_info', mock_env_detection):
                        yield fake_settings
                else:
                    yield fake_settings


class TestVerifyApiKeyDependency:
    """
    Test suite for verify_api_key FastAPI dependency function.

    Scope:
        - Authentication success and failure flows
        - Development mode behavior without API keys
        - Production security enforcement
        - Error context and environment integration
        - Custom exception raising with detailed context

    Business Critical:
        verify_api_key is the primary authentication dependency that protects
        application endpoints and determines access control throughout the system.

    Test Strategy:
        - Test successful authentication with valid credentials
        - Test authentication failure with invalid credentials
        - Test missing credentials handling
        - Test development mode bypass behavior
        - Test error context inclusion and environment awareness
    """

    @pytest.mark.asyncio
    async def test_verify_api_key_succeeds_with_valid_credentials(self, fake_settings_with_primary_key, mock_request_with_bearer_token, valid_http_bearer_credentials, mock_environment_detection):
        """
        Test that verify_api_key returns API key for valid Bearer credentials.

        Verifies:
            Valid API key authentication succeeds and returns the key value.

        Business Impact:
            Ensures legitimate users with valid API keys can successfully
            authenticate and access protected application endpoints.

        Scenario:
            Given: APIKeyAuth is configured with known valid API keys.
            And: Valid Bearer credentials are provided in request.
            When: verify_api_key dependency is called.
            Then: The API key string is returned successfully.

        Fixtures Used:
            - fake_settings_with_primary_key: Settings with valid API key configured.
            - mock_request_with_bearer_token: Mock request with Bearer token.
            - valid_http_bearer_credentials: Mock credentials with valid API key.
            - mock_environment_detection: Environment detection for context.
        """
        # Given: APIKeyAuth is configured with known valid API keys
        # And: Valid Bearer credentials are provided in request
        # Configure the mock credentials to match the configured key
        valid_http_bearer_credentials.credentials = "test-primary-key-123"

        # When: verify_api_key dependency is called
        with mock_auth_config(fake_settings_with_primary_key, {"test-primary-key-123"}) as settings:
            result = await verify_api_key(mock_request_with_bearer_token, valid_http_bearer_credentials, settings)

        # Then: The API key string is returned successfully
        assert result == "test-primary-key-123"

    @pytest.mark.asyncio
    async def test_verify_api_key_succeeds_with_x_api_key(self, fake_settings_with_primary_key, mock_request_with_x_api_key, mock_environment_detection):
        """
        Test that verify_api_key returns API key for valid X-API-Key header.

        Verifies:
            X-API-Key authentication succeeds and returns the key value.

        Business Impact:
            Ensures API key authentication works with both Bearer and X-API-Key headers.
        """
        # When: verify_api_key dependency is called with X-API-Key header
        with mock_auth_config(fake_settings_with_primary_key, {"test-primary-key-123"}) as settings:
            result = await verify_api_key(mock_request_with_x_api_key, None, settings)

        # Then: The API key string is returned successfully
        assert result == "test-primary-key-123"

    @pytest.mark.asyncio
    async def test_verify_api_key_raises_authentication_error_for_invalid_key(self, fake_settings_with_primary_key, mock_request_with_invalid_bearer, invalid_http_bearer_credentials, mock_environment_detection):
        """
        Test that verify_api_key raises AuthenticationError for invalid keys.

        Verifies:
            Invalid API keys are rejected with appropriate error context.

        Business Impact:
            Prevents unauthorized access by properly rejecting invalid credentials
            and providing clear error information for troubleshooting.

        Scenario:
            Given: APIKeyAuth is configured with known valid API keys.
            And: Invalid Bearer credentials are provided in request.
            When: verify_api_key dependency is called.
            Then: AuthenticationError is raised with detailed context.

        Fixtures Used:
            - fake_settings_with_primary_key: Settings with valid API key configured.
            - mock_request_with_invalid_bearer: Mock request with invalid Bearer token.
            - invalid_http_bearer_credentials: Mock credentials with invalid API key.
            - mock_environment_detection: Environment detection for error context.
        """
        # Given: APIKeyAuth is configured with known valid API keys
        # And: Invalid Bearer credentials are provided in request

        # When: verify_api_key dependency is called
        # Then: AuthenticationError is raised with detailed context
        with mock_auth_config(fake_settings_with_primary_key, {"test-primary-key-123"}) as settings:
            with pytest.raises(AuthenticationError) as exc_info:
                await verify_api_key(mock_request_with_invalid_bearer, invalid_http_bearer_credentials, settings)

            # Verify error contains appropriate context
            error_msg = str(exc_info.value)
            assert "Invalid API key" in error_msg
            assert exc_info.value.context is not None

    @pytest.mark.asyncio
    async def test_verify_api_key_raises_authentication_error_for_missing_credentials(self, fake_settings_with_primary_key, mock_request, mock_environment_detection):
        """
        Test that verify_api_key raises AuthenticationError when credentials are missing.

        Verifies:
            Missing Authorization header is properly detected and rejected.

        Business Impact:
            Ensures protected endpoints require authentication and provide
            clear guidance when credentials are not provided.

        Scenario:
            Given: APIKeyAuth is configured with API keys (not development mode).
            And: No Authorization header or credentials are provided.
            When: verify_api_key dependency is called.
            Then: AuthenticationError is raised indicating missing credentials.

        Fixtures Used:
            - fake_settings_with_primary_key: Settings requiring authentication.
            - mock_request: Mock request without authentication headers.
            - mock_environment_detection: Environment detection for context.
        """
        # Given: APIKeyAuth is configured with API keys (not development mode)
        # And: No Authorization header or credentials are provided

        # When: verify_api_key dependency is called
        # Then: AuthenticationError is raised indicating missing credentials
        with mock_auth_config(fake_settings_with_primary_key, {"test-primary-key-123"}, mock_environment_detection) as settings:
            with pytest.raises(AuthenticationError) as exc_info:
                await verify_api_key(mock_request, None, settings)  # No credentials provided

            # Verify error message contains appropriate guidance
            error_msg = str(exc_info.value)
            assert "API key required" in error_msg
            assert exc_info.value.context is not None
            assert exc_info.value.context["credentials_provided"] is False

    @pytest.mark.asyncio
    async def test_verify_api_key_allows_development_mode_access(self, fake_settings, mock_request, mock_environment_detection):
        """
        Test that verify_api_key allows access in development mode without keys.

        Verifies:
            Development mode bypasses authentication when no keys are configured.

        Business Impact:
            Enables local development without authentication complexity while
            maintaining security in production environments.

        Scenario:
            Given: No API keys are configured (development mode).
            And: No credentials are provided in request.
            When: verify_api_key dependency is called.
            Then: "development" string is returned allowing access.

        Fixtures Used:
            - fake_settings: Empty settings for development mode.
            - mock_request: Mock request without authentication.
            - mock_environment_detection: Returns development environment.
        """
        # Given: No API keys are configured (development mode)
        # fake_settings fixture provides empty settings by default
        # And: No credentials are provided in request

        # When: verify_api_key dependency is called
        with mock_auth_config(fake_settings, set()) as settings:
            result = await verify_api_key(mock_request, None, settings)  # No credentials provided

        # Then: "development" string is returned allowing access
        assert result == "development"

    @pytest.mark.asyncio
    async def test_verify_api_key_includes_environment_context_in_errors(self, fake_settings_with_primary_key, mock_request_with_invalid_bearer, invalid_http_bearer_credentials, mock_environment_detection):
        """
        Test that verify_api_key includes environment detection context in errors.

        Verifies:
            Authentication errors include environment information for debugging.

        Business Impact:
            Provides operational context for troubleshooting authentication
            issues across different deployment environments.

        Scenario:
            Given: APIKeyAuth configuration and environment detection available.
            When: verify_api_key fails with invalid or missing credentials.
            Then: AuthenticationError context includes environment details.

        Fixtures Used:
            - fake_settings_with_primary_key: Settings for authentication context.
            - mock_request_with_invalid_bearer: Request with invalid Bearer token.
            - invalid_http_bearer_credentials: Invalid credentials for error trigger.
            - mock_environment_detection: Environment details for error context.
        """
        # Given: APIKeyAuth configuration and environment detection available
        # When: verify_api_key fails with invalid or missing credentials
        # Then: AuthenticationError context includes environment details
        with mock_auth_config(fake_settings_with_primary_key, {"test-primary-key-123"}, mock_environment_detection) as settings:
            with pytest.raises(AuthenticationError) as exc_info:
                await verify_api_key(mock_request_with_invalid_bearer, invalid_http_bearer_credentials, settings)

            # Verify environment context is included
            assert exc_info.value.context is not None
            context = exc_info.value.context
            assert "environment" in context
            assert "confidence" in context
            assert "auth_method" in context
            assert context["credentials_provided"] is True

    @pytest.mark.asyncio
    async def test_verify_api_key_handles_environment_detection_failure(self, fake_settings_with_primary_key, mock_request_with_bearer_token, valid_http_bearer_credentials):
        """
        Test that verify_api_key handles environment detection service failures.

        Verifies:
            Authentication continues to work when environment detection fails.

        Business Impact:
            Ensures authentication system resilience and prevents failures
            due to environment detection service issues.

        Scenario:
            Given: Environment detection service raises exceptions.
            When: verify_api_key is called with valid or invalid credentials.
            Then: Authentication logic continues with fallback context.

        Fixtures Used:
            - fake_settings_with_primary_key: Settings for authentication.
            - mock_request_with_bearer_token: Request with valid Bearer token.
            - valid_http_bearer_credentials: Valid credentials for success case.
        """
        # Given: Environment detection service raises exceptions
        # Configure the mock credentials to match the configured key
        valid_http_bearer_credentials.credentials = "test-primary-key-123"

        def failing_env_detection(*args, **kwargs):
            raise Exception("Environment detection failed")

        # When: verify_api_key is called with valid credentials
        # Then: Authentication logic continues with fallback context
        with mock_auth_config(fake_settings_with_primary_key, {"test-primary-key-123"}) as settings:
            with patch('app.infrastructure.security.auth.get_environment_info', side_effect=failing_env_detection):
                # Should still succeed with valid credentials despite env detection failure
                result = await verify_api_key(mock_request_with_bearer_token, valid_http_bearer_credentials, settings)
                assert result == "test-primary-key-123"

        # Test with invalid credentials - should still fail gracefully
        invalid_request = Mock(spec=Request)
        invalid_request.headers = Mock()
        invalid_request.headers.get = Mock(return_value="invalid-key")
        invalid_credentials = Mock(spec=HTTPAuthorizationCredentials)
        invalid_credentials.credentials = "invalid-key"

        with mock_auth_config(fake_settings_with_primary_key, {"test-primary-key-123"}) as settings:
            with patch('app.infrastructure.security.auth.get_environment_info', side_effect=failing_env_detection):
                with pytest.raises(AuthenticationError) as exc_info:
                    await verify_api_key(invalid_request, invalid_credentials, settings)

                # Should still provide some context even with env detection failure
                assert exc_info.value.context is not None
                assert "auth_method" in exc_info.value.context


class TestVerifyApiKeyWithMetadataDependency:
    """
    Test suite for verify_api_key_with_metadata enhanced dependency function.

    Scope:
        - Enhanced authentication with metadata inclusion
        - User tracking and request logging integration
        - Metadata structure and content validation
        - Feature flag integration and conditional behavior

    Business Critical:
        verify_api_key_with_metadata enables advanced authentication features
        required for enterprise deployments with detailed audit requirements.

    Test Strategy:
        - Test successful authentication with metadata return
        - Test metadata structure and content
        - Test feature flag integration effects
        - Test delegation to base verify_api_key function
    """

    @pytest.mark.asyncio
    async def test_verify_api_key_with_metadata_returns_api_key_and_metadata(self, fake_settings_with_primary_key, mock_request_with_bearer_token, valid_http_bearer_credentials, mock_environment_detection):
        """
        Test that verify_api_key_with_metadata returns dictionary with key and metadata.

        Verifies:
            Enhanced dependency returns structured data including API key and metadata.

        Business Impact:
            Enables advanced authentication workflows that require detailed
            context and metadata for audit trails and user tracking.

        Scenario:
            Given: APIKeyAuth with metadata features enabled.
            And: Valid Bearer credentials are provided.
            When: verify_api_key_with_metadata dependency is called.
            Then: Dictionary containing 'api_key' and metadata fields is returned.

        Fixtures Used:
            - fake_settings_with_primary_key: Settings with valid API key.
            - mock_request_with_bearer_token: Request with Bearer token.
            - valid_http_bearer_credentials: Valid credentials for authentication.
            - monkeypatch: To enable user tracking and request logging features.
        """
        # Given: Valid Bearer credentials are provided
        valid_http_bearer_credentials.credentials = "test-primary-key-123"

        # When: verify_api_key_with_metadata dependency is called
        # Mock auth_config to enable at least basic metadata
        from unittest.mock import Mock
        mock_auth_config_obj = Mock()
        mock_auth_config_obj.enable_user_tracking = True  # Enable to get metadata
        mock_auth_config_obj.enable_request_logging = False

        with mock_auth_config(fake_settings_with_primary_key, {"test-primary-key-123"}, mock_environment_detection, mock_auth_config_obj) as settings:
            with patch('app.infrastructure.security.auth.api_key_auth.config', mock_auth_config_obj):
                result = await verify_api_key_with_metadata(mock_request_with_bearer_token, valid_http_bearer_credentials, settings)

        # Then: Dictionary containing 'api_key' and metadata fields is returned
        assert isinstance(result, dict)
        assert "api_key" in result
        assert result["api_key"] == "test-primary-key-123"
        assert "api_key_type" in result  # Basic metadata always present when features enabled

    @pytest.mark.asyncio
    async def test_verify_api_key_with_metadata_includes_user_tracking_data(self, fake_settings_with_primary_key, mock_request_with_bearer_token, valid_http_bearer_credentials, mock_environment_detection):
        """
        Test that metadata includes user tracking data when feature is enabled.

        Verifies:
            User tracking features enhance metadata with key type and permissions.

        Business Impact:
            Provides detailed user context for enterprise authentication
            requiring role-based access control and audit compliance.

        Scenario:
            Given: User tracking is enabled in AuthConfig.
            And: APIKeyAuth has metadata configured for keys.
            When: verify_api_key_with_metadata is called with valid credentials.
            Then: Returned metadata includes key_type and permissions information.

        Fixtures Used:
            - fake_settings_with_primary_key: Settings with API key and metadata.
            - mock_request_with_bearer_token: Request with Bearer token.
            - valid_http_bearer_credentials: Valid credentials for authentication.
            - monkeypatch: To enable user tracking features.
        """
        # Given: User tracking is enabled in AuthConfig
        valid_http_bearer_credentials.credentials = "test-primary-key-123"

        # Enable user tracking
        from unittest.mock import Mock
        mock_auth_config_obj = Mock()
        mock_auth_config_obj.enable_user_tracking = True
        mock_auth_config_obj.enable_request_logging = False

        with mock_auth_config(fake_settings_with_primary_key, {"test-primary-key-123"}, mock_environment_detection, mock_auth_config_obj) as settings:
            # Also need to mock the api_key_auth config to enable user tracking
            # And provide metadata for the key
            key_metadata = {
                "test-primary-key-123": {
                    "type": "primary",
                    "created_at": "system",
                    "permissions": ["read", "write"]
                }
            }
            with patch('app.infrastructure.security.auth.api_key_auth.config', mock_auth_config_obj):
                with patch('app.infrastructure.security.auth.api_key_auth._key_metadata', key_metadata):
                    # When: verify_api_key_with_metadata is called with valid credentials
                    result = await verify_api_key_with_metadata(mock_request_with_bearer_token, valid_http_bearer_credentials, settings)

        # Then: Returned metadata includes key_type and permissions information
        assert "key_type" in result
        assert "permissions" in result
        assert result["key_type"] == "primary"  # Based on primary key metadata
        assert isinstance(result["permissions"], list)

    @pytest.mark.asyncio
    async def test_verify_api_key_with_metadata_includes_request_logging_data(self, fake_settings_with_primary_key, mock_request_with_bearer_token, valid_http_bearer_credentials, mock_environment_detection):
        """
        Test that metadata includes request logging data when feature is enabled.

        Verifies:
            Request logging features enhance metadata with request details.

        Business Impact:
            Enables detailed request monitoring and audit trails for
            operational visibility and compliance requirements.

        Scenario:
            Given: Request logging is enabled in AuthConfig.
            When: verify_api_key_with_metadata is called with valid credentials.
            Then: Returned metadata includes timestamp, endpoint, and method information.

        Fixtures Used:
            - fake_settings_with_primary_key: Settings with valid API key.
            - mock_request_with_bearer_token: Request with Bearer token.
            - valid_http_bearer_credentials: Valid credentials for authentication.
            - monkeypatch: To enable request logging features.
        """
        # Given: Request logging is enabled in AuthConfig
        valid_http_bearer_credentials.credentials = "test-primary-key-123"

        # Enable request logging
        from unittest.mock import Mock
        mock_auth_config_obj = Mock()
        mock_auth_config_obj.enable_user_tracking = False
        mock_auth_config_obj.enable_request_logging = True

        with mock_auth_config(fake_settings_with_primary_key, {"test-primary-key-123"}, mock_environment_detection, mock_auth_config_obj) as settings:
            # Also need to mock the api_key_auth config to enable request logging
            with patch('app.infrastructure.security.auth.api_key_auth.config', mock_auth_config_obj):
                # When: verify_api_key_with_metadata is called with valid credentials
                result = await verify_api_key_with_metadata(mock_request_with_bearer_token, valid_http_bearer_credentials, settings)

        # Then: Returned metadata includes timestamp, endpoint, and method information
        assert "timestamp" in result
        assert "endpoint" in result
        assert "method" in result

    @pytest.mark.asyncio
    async def test_verify_api_key_with_metadata_delegates_authentication_to_base(self, fake_settings_with_primary_key, mock_request_with_invalid_bearer, invalid_http_bearer_credentials, mock_environment_detection):
        """
        Test that verify_api_key_with_metadata delegates authentication to verify_api_key.

        Verifies:
            Authentication logic is consistent between basic and enhanced dependencies.

        Business Impact:
            Ensures authentication behavior remains consistent across dependency
            variants and prevents security policy divergence.

        Scenario:
            Given: Configuration that would cause verify_api_key to fail.
            When: verify_api_key_with_metadata is called with same parameters.
            Then: The same AuthenticationError is raised by delegation.

        Fixtures Used:
            - fake_settings_with_primary_key: Settings for authentication.
            - mock_request_with_invalid_bearer: Request with invalid Bearer token.
            - invalid_http_bearer_credentials: Invalid credentials for error case.
        """
        # Given: Configuration that would cause verify_api_key to fail
        # When: verify_api_key_with_metadata is called with same parameters
        # Then: The same AuthenticationError is raised by delegation
        with mock_auth_config(fake_settings_with_primary_key, {"test-primary-key-123"}, mock_environment_detection) as settings:
            with pytest.raises(AuthenticationError) as exc_info:
                await verify_api_key_with_metadata(mock_request_with_invalid_bearer, invalid_http_bearer_credentials, settings)

            # Verify the same error type and message as basic dependency
            error_msg = str(exc_info.value)
            assert "Invalid API key" in error_msg
            assert exc_info.value.context is not None

    @pytest.mark.asyncio
    async def test_verify_api_key_with_metadata_minimal_when_features_disabled(self, fake_settings_with_primary_key, mock_request_with_bearer_token, valid_http_bearer_credentials, mock_environment_detection):
        """
        Test that metadata is minimal when advanced features are disabled.

        Verifies:
            Simple mode maintains minimal metadata without advanced features.

        Business Impact:
            Ensures simple authentication mode remains lightweight and doesn't
            accidentally expose advanced features or metadata.

        Scenario:
            Given: AuthConfig with user tracking and request logging disabled.
            When: verify_api_key_with_metadata is called with valid credentials.
            Then: Returned metadata contains only basic api_key_type information.

        Fixtures Used:
            - fake_settings_with_primary_key: Settings with API key configured.
            - mock_request_with_bearer_token: Request with Bearer token.
            - valid_http_bearer_credentials: Valid credentials for authentication.
        """
        # Given: AuthConfig with user tracking and request logging disabled (default)
        valid_http_bearer_credentials.credentials = "test-primary-key-123"

        # When: verify_api_key_with_metadata is called with valid credentials
        from unittest.mock import Mock
        mock_auth_config_obj = Mock()
        mock_auth_config_obj.enable_user_tracking = False
        mock_auth_config_obj.enable_request_logging = False

        with mock_auth_config(fake_settings_with_primary_key, {"test-primary-key-123"}, mock_environment_detection, mock_auth_config_obj) as settings:
            with patch('app.infrastructure.security.auth.api_key_auth.config', mock_auth_config_obj):
                result = await verify_api_key_with_metadata(mock_request_with_bearer_token, valid_http_bearer_credentials, settings)

        # Then: Returned metadata is minimal when advanced features are disabled
        assert "api_key" in result
        # When both features are disabled, no additional metadata is added
        assert len(result) == 1  # Only api_key field

        # Verify advanced features are not present
        assert "api_key_type" not in result  # Only present when features enabled
        assert "key_type" not in result  # User tracking feature
        assert "permissions" not in result  # User tracking feature
        assert "timestamp" not in result  # Request logging feature
        assert "endpoint" not in result  # Request logging feature
        assert "method" not in result  # Request logging feature


class TestOptionalVerifyApiKeyDependency:
    """
    Test suite for optional_verify_api_key conditional authentication dependency.

    Scope:
        - Optional authentication behavior for flexible endpoints
        - Missing credentials handling without errors
        - Valid credentials validation when provided
        - Integration with base authentication logic

    Business Critical:
        optional_verify_api_key enables flexible endpoint protection where
        authentication enhances functionality but isn't strictly required.

    Test Strategy:
        - Test None return for missing credentials
        - Test successful authentication when credentials provided
        - Test authentication failure delegation
        - Test consistency with base authentication behavior
    """

    @pytest.mark.asyncio
    async def test_optional_verify_api_key_returns_none_for_missing_credentials(self, fake_settings_with_primary_key, mock_request, mock_environment_detection):
        """
        Test that optional_verify_api_key returns None when no credentials provided.

        Verifies:
            Missing credentials are handled gracefully without raising errors.

        Business Impact:
            Enables flexible endpoint access where authentication is optional
            but can enhance functionality when provided.

        Scenario:
            Given: No Authorization header or credentials are provided.
            When: optional_verify_api_key dependency is called.
            Then: None is returned without raising any exceptions.

        Fixtures Used:
            - fake_settings_with_primary_key: Settings for authentication context.
            - mock_request: Request without authentication headers.
        """
        # Given: No Authorization header or credentials are provided
        # When: optional_verify_api_key dependency is called
        with mock_auth_config(fake_settings_with_primary_key, {"test-primary-key-123"}, mock_environment_detection) as settings:
            result = await optional_verify_api_key(mock_request, None, settings)

        # Then: None is returned without raising any exceptions
        assert result is None

    @pytest.mark.asyncio
    async def test_optional_verify_api_key_returns_key_for_valid_credentials(self, fake_settings_with_primary_key, mock_request_with_bearer_token, valid_http_bearer_credentials, mock_environment_detection):
        """
        Test that optional_verify_api_key returns API key for valid credentials.

        Verifies:
            Valid credentials are authenticated successfully when provided.

        Business Impact:
            Enables enhanced functionality for authenticated users while
            maintaining accessibility for anonymous users.

        Scenario:
            Given: APIKeyAuth configured with valid keys.
            And: Valid Bearer credentials are provided.
            When: optional_verify_api_key dependency is called.
            Then: The validated API key is returned.

        Fixtures Used:
            - fake_settings_with_primary_key: Settings with valid API key.
            - mock_request_with_bearer_token: Request with Bearer token.
            - valid_http_bearer_credentials: Valid credentials for authentication.
        """
        # Given: APIKeyAuth configured with valid keys
        # And: Valid Bearer credentials are provided
        valid_http_bearer_credentials.credentials = "test-primary-key-123"

        # When: optional_verify_api_key dependency is called
        with mock_auth_config(fake_settings_with_primary_key, {"test-primary-key-123"}) as settings:
            result = await optional_verify_api_key(mock_request_with_bearer_token, valid_http_bearer_credentials, settings)

        # Then: The validated API key is returned
        assert result == "test-primary-key-123"

    @pytest.mark.asyncio
    async def test_optional_verify_api_key_raises_error_for_invalid_credentials(self, fake_settings_with_primary_key, mock_request_with_invalid_bearer, invalid_http_bearer_credentials, mock_environment_detection):
        """
        Test that optional_verify_api_key raises error for invalid credentials.

        Verifies:
            Invalid credentials are rejected when provided, not silently ignored.

        Business Impact:
            Prevents security bypass attempts by ensuring invalid credentials
            are properly rejected rather than treated as anonymous access.

        Scenario:
            Given: APIKeyAuth configured with valid keys.
            And: Invalid Bearer credentials are provided.
            When: optional_verify_api_key dependency is called.
            Then: AuthenticationError is raised for invalid key.

        Fixtures Used:
            - fake_settings_with_primary_key: Settings with valid API key.
            - mock_request_with_invalid_bearer: Request with invalid Bearer token.
            - invalid_http_bearer_credentials: Invalid credentials for testing.
        """
        # Given: APIKeyAuth configured with valid keys
        # And: Invalid Bearer credentials are provided

        # When: optional_verify_api_key dependency is called
        # Then: AuthenticationError is raised for invalid key
        with mock_auth_config(fake_settings_with_primary_key, {"test-primary-key-123"}) as settings:
            with pytest.raises(AuthenticationError) as exc_info:
                await optional_verify_api_key(mock_request_with_invalid_bearer, invalid_http_bearer_credentials, settings)

            # Verify appropriate error for invalid credentials
            error_msg = str(exc_info.value)
            assert "Invalid API key" in error_msg

    @pytest.mark.asyncio
    async def test_optional_verify_api_key_handles_development_mode(self, fake_settings, mock_request, mock_environment_detection):
        """
        Test that optional_verify_api_key handles development mode correctly.

        Verifies:
            Development mode is handled properly with optional authentication.

        Business Impact:
            Enables consistent behavior in development environments with
            optional authentication endpoints.

        Scenario:
            Given: No API keys configured (development mode).
            When: optional_verify_api_key is called without credentials.
            Then: None is returned (not "development" string).

        Fixtures Used:
            - fake_settings: Empty settings for development mode.
            - mock_request: Request without authentication.
        """
        # Given: No API keys configured (development mode)
        # When: optional_verify_api_key is called without credentials
        with mock_auth_config(fake_settings, set()) as settings:
            result = await optional_verify_api_key(mock_request, None, settings)

        # Then: None is returned (consistent with "no credentials provided" behavior)
        assert result is None


class TestVerifyApiKeyHttpDependency:
    """
    Test suite for verify_api_key_http HTTP exception wrapper dependency.

    Scope:
        - HTTPException conversion for middleware compatibility
        - 401 status code and WWW-Authenticate header handling
        - Error context preservation in HTTP responses
        - Delegation to base authentication logic

    Business Critical:
        verify_api_key_http provides proper HTTP error responses and avoids
        middleware conflicts in complex FastAPI applications.

    Test Strategy:
        - Test successful authentication pass-through
        - Test AuthenticationError to HTTPException conversion
        - Test HTTP status codes and headers
        - Test error context preservation
    """

    @pytest.mark.asyncio
    async def test_verify_api_key_http_returns_key_for_valid_authentication(self, fake_settings_with_primary_key, mock_request_with_bearer_token, valid_http_bearer_credentials):
        """
        Test that verify_api_key_http returns API key for valid authentication.

        Verifies:
            Successful authentication passes through without modification.

        Business Impact:
            Ensures HTTP wrapper doesn't interfere with successful authentication
            and maintains compatibility with existing endpoints.

        Scenario:
            Given: Valid API key credentials are provided.
            When: verify_api_key_http dependency is called.
            Then: The validated API key is returned normally.

        Fixtures Used:
            - fake_settings_with_primary_key: Settings with valid API key.
            - mock_request_with_bearer_token: Request with Bearer token.
            - valid_http_bearer_credentials: Valid credentials for authentication.
        """
        # Given: Valid API key credentials are provided
        valid_http_bearer_credentials.credentials = "test-primary-key-123"

        # When: verify_api_key_http dependency is called
        with mock_auth_config(fake_settings_with_primary_key, {"test-primary-key-123"}) as settings:
            result = await verify_api_key_http(mock_request_with_bearer_token, valid_http_bearer_credentials, settings)

        # Then: The validated API key is returned normally
        assert result == "test-primary-key-123"

    @pytest.mark.asyncio
    async def test_verify_api_key_http_converts_authentication_error_to_http_exception(self, fake_settings_with_primary_key, mock_request_with_invalid_bearer, invalid_http_bearer_credentials):
        """
        Test that verify_api_key_http converts AuthenticationError to HTTPException.

        Verifies:
            Custom exceptions are converted to HTTP exceptions for middleware.

        Business Impact:
            Prevents middleware conflicts and ensures proper HTTP error responses
            in production FastAPI applications.

        Scenario:
            Given: Invalid API key credentials are provided.
            When: verify_api_key_http dependency is called.
            Then: HTTPException with 401 status is raised.

        Fixtures Used:
            - fake_settings_with_primary_key: Settings for authentication.
            - mock_request_with_invalid_bearer: Request with invalid Bearer token.
            - invalid_http_bearer_credentials: Invalid credentials for testing.
        """
        # Given: Invalid API key credentials are provided
        # When: verify_api_key_http dependency is called
        # Then: HTTPException with 401 status is raised
        with mock_auth_config(fake_settings_with_primary_key, {"test-primary-key-123"}) as settings:
            with pytest.raises(HTTPException) as exc_info:
                await verify_api_key_http(mock_request_with_invalid_bearer, invalid_http_bearer_credentials, settings)

            # Verify HTTP exception properties
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert exc_info.value.headers["WWW-Authenticate"] == "Bearer"

    @pytest.mark.asyncio
    async def test_verify_api_key_http_includes_www_authenticate_header(self, fake_settings_with_primary_key, mock_request, mock_environment_detection):
        """
        Test that verify_api_key_http includes WWW-Authenticate header in errors.

        Verifies:
            Proper HTTP authentication flow with required headers.

        Business Impact:
            Ensures compliance with HTTP authentication standards and proper
            client behavior for authentication challenges.

        Scenario:
            Given: No credentials are provided (authentication required).
            When: verify_api_key_http dependency is called.
            Then: HTTPException includes WWW-Authenticate: Bearer header.

        Fixtures Used:
            - fake_settings_with_primary_key: Settings requiring authentication.
            - mock_request: Request without authentication.
        """
        # Given: No credentials are provided (authentication required)
        # When: verify_api_key_http dependency is called
        # Then: HTTPException includes WWW-Authenticate: Bearer header
        with mock_auth_config(fake_settings_with_primary_key, {"test-primary-key-123"}, mock_environment_detection) as settings:
            with pytest.raises(HTTPException) as exc_info:
                await verify_api_key_http(mock_request, None, settings)

            # Verify WWW-Authenticate header is present
            assert "WWW-Authenticate" in exc_info.value.headers
            assert exc_info.value.headers["WWW-Authenticate"] == "Bearer"

    @pytest.mark.asyncio
    async def test_verify_api_key_http_returns_401_status_for_authentication_failures(self, fake_settings_with_primary_key, mock_request_with_invalid_bearer, invalid_http_bearer_credentials):
        """
        Test that verify_api_key_http returns 401 Unauthorized status.

        Verifies:
            Standard HTTP status code for authentication failures.

        Business Impact:
            Ensures API clients receive standard HTTP status codes for proper
            error handling and retry logic.

        Scenario:
            Given: Invalid authentication credentials.
            When: verify_api_key_http dependency is called.
            Then: HTTPException with 401 Unauthorized status is raised.

        Fixtures Used:
            - fake_settings_with_primary_key: Settings for authentication.
            - mock_request_with_invalid_bearer: Request with invalid Bearer token.
            - invalid_http_bearer_credentials: Invalid credentials for testing.
        """
        # Given: Invalid authentication credentials
        # When: verify_api_key_http dependency is called
        # Then: HTTPException with 401 Unauthorized status is raised
        with mock_auth_config(fake_settings_with_primary_key, {"test-primary-key-123"}) as settings:
            with pytest.raises(HTTPException) as exc_info:
                await verify_api_key_http(mock_request_with_invalid_bearer, invalid_http_bearer_credentials, settings)

            # Verify 401 status code
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert exc_info.value.status_code == 401

    @pytest.mark.asyncio
    async def test_verify_api_key_http_preserves_error_context_in_http_response(self, fake_settings_with_primary_key, mock_request_with_invalid_bearer, invalid_http_bearer_credentials, mock_environment_detection):
        """
        Test that verify_api_key_http preserves error context in HTTP response.

        Verifies:
            Original error context is preserved for debugging and monitoring.

        Business Impact:
            Maintains operational visibility and debugging capabilities while
            providing proper HTTP error responses.

        Scenario:
            Given: Authentication failure with environment context.
            When: verify_api_key_http converts error to HTTPException.
            Then: Original error message and context are preserved in detail.

        Fixtures Used:
            - fake_settings_with_primary_key: Settings for authentication.
            - mock_request_with_invalid_bearer: Request with invalid Bearer token.
            - invalid_http_bearer_credentials: Invalid credentials for testing.
            - mock_environment_detection: Environment context for errors.
        """
        # Given: Authentication failure with environment context
        # When: verify_api_key_http converts error to HTTPException
        # Then: Original error message and context are preserved in detail
        with mock_auth_config(fake_settings_with_primary_key, {"test-primary-key-123"}, mock_environment_detection) as settings:
            with pytest.raises(HTTPException) as exc_info:
                await verify_api_key_http(mock_request_with_invalid_bearer, invalid_http_bearer_credentials, settings)

            # Verify error detail structure
            detail = exc_info.value.detail
            assert isinstance(detail, dict)
            assert "message" in detail
            assert "context" in detail
            assert "Invalid API key" in detail["message"]
            assert detail["context"] is not None

    @pytest.mark.asyncio
    async def test_verify_api_key_http_handles_development_mode_consistently(self, fake_settings, mock_request):
        """
        Test that verify_api_key_http handles development mode like base dependency.

        Verifies:
            Development mode behavior is consistent across dependency variants.

        Business Impact:
            Ensures consistent development experience regardless of which
            authentication dependency variant is used.

        Scenario:
            Given: No API keys configured (development mode).
            When: verify_api_key_http is called without credentials.
            Then: "development" string is returned (no HTTPException).

        Fixtures Used:
            - fake_settings: Empty settings for development mode.
            - mock_request: Request without authentication.
        """
        # Given: No API keys configured (development mode)
        # When: verify_api_key_http is called without credentials
        with mock_auth_config(fake_settings, set()) as settings:
            result = await verify_api_key_http(mock_request, None, settings)

        # Then: "development" string is returned (no HTTPException)
        assert result == "development"


class TestAuthenticationDependencyEdgeCases:
    """
    Test suite for edge cases and error conditions in authentication dependencies.

    Scope:
        - Malformed credentials handling
        - Concurrent access patterns
        - Error consistency across dependency variants
        - Security preservation during error conditions

    Business Critical:
        Edge case handling ensures security and stability in unexpected
        situations and prevents authentication bypass vulnerabilities.

    Test Strategy:
        - Test malformed authentication data handling
        - Test thread safety and concurrent access
        - Test error consistency across variants
        - Test security preservation in error states
    """

    @pytest.mark.asyncio
    async def test_dependencies_handle_malformed_bearer_credentials(self, fake_settings_with_primary_key):
        """
        Test that dependencies handle malformed Bearer token formats.

        Verifies:
            Malformed authentication data doesn't cause unexpected failures.

        Business Impact:
            Prevents authentication bypass or service disruption from
            malformed or malicious authentication attempts.

        Scenario:
            Given: Malformed Bearer credentials (empty, None, non-string).
            When: Authentication dependencies are called.
            Then: Appropriate errors are raised without crashes.

        Fixtures Used:
            - fake_settings_with_primary_key: Settings for authentication.
        """
        # Test with empty string credentials
        empty_creds = Mock(spec=HTTPAuthorizationCredentials)
        empty_creds.credentials = ""
        
        empty_request = Mock(spec=Request)
        empty_request.headers = Mock()
        empty_request.headers.get = Mock(return_value=None)

        with mock_auth_config(fake_settings_with_primary_key, {"test-primary-key-123"}) as settings:
            with pytest.raises(AuthenticationError):
                await verify_api_key(empty_request, empty_creds, settings)

        # Test with None credentials object but headers present
        none_request = Mock(spec=Request)
        none_request.headers = Mock()
        none_request.headers.get = Mock(return_value=None)

        with mock_auth_config(fake_settings_with_primary_key, {"test-primary-key-123"}) as settings:
            with pytest.raises(AuthenticationError):
                await verify_api_key(none_request, None, settings)

    @pytest.mark.asyncio
    async def test_dependencies_maintain_consistent_behavior_across_variants(self, fake_settings_with_primary_key, mock_request_with_bearer_token, valid_http_bearer_credentials):
        """
        Test that all dependency variants maintain consistent authentication behavior.

        Verifies:
            Authentication logic is consistent across all dependency variants.

        Business Impact:
            Ensures security policies are uniformly enforced regardless of
            which dependency variant is used in endpoints.

        Scenario:
            Given: Same valid credentials and configuration.
            When: Different dependency variants are called.
            Then: All return the same successful authentication result.

        Fixtures Used:
            - fake_settings_with_primary_key: Settings for authentication.
            - mock_request_with_bearer_token: Request with Bearer token.
            - valid_http_bearer_credentials: Valid credentials for testing.
        """
        # Configure credentials
        valid_http_bearer_credentials.credentials = "test-primary-key-123"

        with mock_auth_config(fake_settings_with_primary_key, {"test-primary-key-123"}) as settings:
            # Test basic verify_api_key
            result1 = await verify_api_key(mock_request_with_bearer_token, valid_http_bearer_credentials, settings)
            
            # Test HTTP wrapper variant
            result2 = await verify_api_key_http(mock_request_with_bearer_token, valid_http_bearer_credentials, settings)
            
            # Test optional variant
            result3 = await optional_verify_api_key(mock_request_with_bearer_token, valid_http_bearer_credentials, settings)
            
            # Test metadata variant
            result4 = await verify_api_key_with_metadata(mock_request_with_bearer_token, valid_http_bearer_credentials, settings)

        # All should authenticate successfully
        assert result1 == "test-primary-key-123"
        assert result2 == "test-primary-key-123"
        assert result3 == "test-primary-key-123"
        assert result4["api_key"] == "test-primary-key-123"

    @pytest.mark.asyncio
    async def test_dependencies_preserve_security_during_error_conditions(self, fake_settings_with_primary_key):
        """
        Test that security is preserved even during error conditions.

        Verifies:
            Authentication remains secure during exceptional conditions.

        Business Impact:
            Prevents security degradation or bypass opportunities during
            error conditions or system failures.

        Scenario:
            Given: Various error conditions (env detection failure, etc.).
            When: Authentication is attempted.
            Then: Security is preserved (no unauthorized access).

        Fixtures Used:
            - fake_settings_with_primary_key: Settings for authentication.
        """
        def failing_env_detection(*args, **kwargs):
            raise Exception("Environment detection failed")

        # Create request with invalid credentials
        invalid_request = Mock(spec=Request)
        invalid_request.headers = Mock()
        invalid_request.headers.get = Mock(return_value="wrong-key")
        
        invalid_creds = Mock(spec=HTTPAuthorizationCredentials)
        invalid_creds.credentials = "wrong-key"

        # Even with environment detection failure, invalid keys should be rejected
        with mock_auth_config(fake_settings_with_primary_key, {"test-primary-key-123"}) as settings:
            with patch('app.infrastructure.security.auth.get_environment_info', side_effect=failing_env_detection):
                with pytest.raises(AuthenticationError):
                    await verify_api_key(invalid_request, invalid_creds, settings)

        # No credentials should also be rejected when keys are configured
        no_creds_request = Mock(spec=Request)
        no_creds_request.headers = Mock()
        no_creds_request.headers.get = Mock(return_value=None)

        with mock_auth_config(fake_settings_with_primary_key, {"test-primary-key-123"}) as settings:
            with patch('app.infrastructure.security.auth.get_environment_info', side_effect=failing_env_detection):
                with pytest.raises(AuthenticationError):
                    await verify_api_key(no_creds_request, None, settings)

    @pytest.mark.asyncio
    async def test_dependencies_handle_concurrent_access_safely(self, fake_settings_with_primary_key):
        """
        Test that dependencies handle concurrent access patterns safely.

        Verifies:
            Thread safety and concurrent request handling.

        Business Impact:
            Ensures authentication system stability under high concurrent load
            and prevents race conditions or state corruption.

        Scenario:
            Given: Multiple concurrent authentication attempts.
            When: Dependencies are called simultaneously.
            Then: Each request is handled independently and correctly.

        Fixtures Used:
            - fake_settings_with_primary_key: Settings for authentication.
        """
        import asyncio

        # Create multiple requests with different credentials
        valid_request = Mock(spec=Request)
        valid_request.headers = Mock()
        valid_request.headers.get = Mock(return_value="test-primary-key-123")
        
        valid_creds = Mock(spec=HTTPAuthorizationCredentials)
        valid_creds.credentials = "test-primary-key-123"

        invalid_request = Mock(spec=Request)
        invalid_request.headers = Mock()
        invalid_request.headers.get = Mock(return_value="invalid-key")
        
        invalid_creds = Mock(spec=HTTPAuthorizationCredentials)
        invalid_creds.credentials = "invalid-key"

        async def valid_auth():
            with mock_auth_config(fake_settings_with_primary_key, {"test-primary-key-123"}) as settings:
                return await verify_api_key(valid_request, valid_creds, settings)

        async def invalid_auth():
            with mock_auth_config(fake_settings_with_primary_key, {"test-primary-key-123"}) as settings:
                try:
                    await verify_api_key(invalid_request, invalid_creds, settings)
                    return "should_not_succeed"
                except AuthenticationError:
                    return "failed_as_expected"

        # Run multiple concurrent authentication attempts
        results = await asyncio.gather(
            valid_auth(),
            invalid_auth(),
            valid_auth(),
            invalid_auth(),
            valid_auth()
        )

        # Verify each request was handled correctly
        assert results[0] == "test-primary-key-123"  # Valid auth
        assert results[1] == "failed_as_expected"     # Invalid auth
        assert results[2] == "test-primary-key-123"  # Valid auth
        assert results[3] == "failed_as_expected"     # Invalid auth
        assert results[4] == "test-primary-key-123"  # Valid auth