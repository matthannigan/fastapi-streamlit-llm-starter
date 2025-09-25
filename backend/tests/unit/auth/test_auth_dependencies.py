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
from unittest.mock import patch
from fastapi import HTTPException, status
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
    """Helper context manager to properly mock auth configuration."""
    with patch('app.infrastructure.security.auth.settings', fake_settings):
        with patch('app.infrastructure.security.auth.api_key_auth.api_keys', api_keys_set):
            if auth_config_patch:
                with patch('app.infrastructure.security.auth.auth_config', auth_config_patch):
                    if mock_env_detection:
                        with patch('app.infrastructure.security.auth.get_environment_info', mock_env_detection):
                            yield
                    else:
                        yield
            elif mock_env_detection:
                with patch('app.infrastructure.security.auth.get_environment_info', mock_env_detection):
                    yield
            else:
                yield


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
    async def test_verify_api_key_succeeds_with_valid_credentials(self, fake_settings_with_primary_key, valid_http_bearer_credentials, mock_environment_detection):
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
            - valid_http_bearer_credentials: Mock credentials with valid API key.
            - mock_environment_detection: Environment detection for context.
        """
        # Given: APIKeyAuth is configured with known valid API keys
        # And: Valid Bearer credentials are provided in request
        # Configure the mock credentials to match the configured key
        valid_http_bearer_credentials.credentials = "test-primary-key-123"

        # When: verify_api_key dependency is called
        with mock_auth_config(fake_settings_with_primary_key, {"test-primary-key-123"}):
            result = await verify_api_key(valid_http_bearer_credentials)

        # Then: The API key string is returned successfully
        assert result == "test-primary-key-123"

    @pytest.mark.asyncio
    async def test_verify_api_key_raises_authentication_error_for_invalid_key(self, fake_settings_with_primary_key, invalid_http_bearer_credentials, mock_environment_detection):
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
            - invalid_http_bearer_credentials: Mock credentials with invalid API key.
            - mock_environment_detection: Environment detection for error context.
        """
        # Given: APIKeyAuth is configured with known valid API keys
        # And: Invalid Bearer credentials are provided in request
        # invalid_http_bearer_credentials fixture provides this

        # When: verify_api_key dependency is called
        # Then: AuthenticationError is raised with detailed context
        with mock_auth_config(fake_settings_with_primary_key, {"test-primary-key-123"}):
            with pytest.raises(AuthenticationError) as exc_info:
                await verify_api_key(invalid_http_bearer_credentials)

            # Verify error contains appropriate context
            error_msg = str(exc_info.value)
            assert "Invalid API key" in error_msg
            assert exc_info.value.context is not None

    @pytest.mark.asyncio
    async def test_verify_api_key_raises_authentication_error_for_missing_credentials(self, fake_settings_with_primary_key, mock_environment_detection):
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
            - mock_environment_detection: Environment detection for context.
        """
        # Given: APIKeyAuth is configured with API keys (not development mode)
        # And: No Authorization header or credentials are provided

        # When: verify_api_key dependency is called
        # Then: AuthenticationError is raised indicating missing credentials
        with mock_auth_config(fake_settings_with_primary_key, {"test-primary-key-123"}, mock_environment_detection):
            with pytest.raises(AuthenticationError) as exc_info:
                await verify_api_key(None)  # No credentials provided

                # Verify error message contains appropriate guidance
                error_msg = str(exc_info.value)
                assert "API key required" in error_msg
                assert exc_info.value.context is not None
                assert exc_info.value.context["credentials_provided"] is False

    @pytest.mark.asyncio
    async def test_verify_api_key_allows_development_mode_access(self, fake_settings, mock_environment_detection):
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
            - mock_environment_detection: Returns development environment.
        """
        # Given: No API keys are configured (development mode)
        # fake_settings fixture provides empty settings by default
        # And: No credentials are provided in request

        # When: verify_api_key dependency is called
        with mock_auth_config(fake_settings, set()):
            result = await verify_api_key(None)  # No credentials provided

        # Then: "development" string is returned allowing access
        assert result == "development"

    @pytest.mark.asyncio
    async def test_verify_api_key_includes_environment_context_in_errors(self, fake_settings_with_primary_key, invalid_http_bearer_credentials, mock_environment_detection):
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
            - invalid_http_bearer_credentials: Invalid credentials for error trigger.
            - mock_environment_detection: Environment details for error context.
        """
        # Given: APIKeyAuth configuration and environment detection available
        # When: verify_api_key fails with invalid or missing credentials
        # Then: AuthenticationError context includes environment details
        with mock_auth_config(fake_settings_with_primary_key, {"test-primary-key-123"}, mock_environment_detection):
            with pytest.raises(AuthenticationError) as exc_info:
                await verify_api_key(invalid_http_bearer_credentials)

                # Verify environment context is included
                assert exc_info.value.context is not None
                context = exc_info.value.context
                assert "environment" in context
                assert "confidence" in context
                assert "auth_method" in context
                assert context["credentials_provided"] is True

    @pytest.mark.asyncio
    async def test_verify_api_key_handles_environment_detection_failure(self, fake_settings_with_primary_key, valid_http_bearer_credentials):
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
            - valid_http_bearer_credentials: Valid credentials for success case.
            - mock_environment_detection: Configured to raise exceptions.
        """
        # Given: Environment detection service raises exceptions
        # Configure the mock credentials to match the configured key
        valid_http_bearer_credentials.credentials = "test-primary-key-123"

        def failing_env_detection(*args, **kwargs):
            raise Exception("Environment detection failed")

        # When: verify_api_key is called with valid credentials
        # Then: Authentication logic continues with fallback context
        with mock_auth_config(fake_settings_with_primary_key, {"test-primary-key-123"}):
            with patch('app.infrastructure.security.auth.get_environment_info', side_effect=failing_env_detection):
                # Should still succeed with valid credentials despite env detection failure
                result = await verify_api_key(valid_http_bearer_credentials)
                assert result == "test-primary-key-123"

        # Test with invalid credentials - should still fail gracefully
        with mock_auth_config(fake_settings_with_primary_key, {"test-primary-key-123"}):
            with patch('app.infrastructure.security.auth.get_environment_info', side_effect=failing_env_detection):
                invalid_credentials = valid_http_bearer_credentials
                invalid_credentials.credentials = "invalid-key"

                with pytest.raises(AuthenticationError) as exc_info:
                    await verify_api_key(invalid_credentials)

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
    async def test_verify_api_key_with_metadata_returns_api_key_and_metadata(self, fake_settings_with_primary_key, valid_http_bearer_credentials, mock_environment_detection):
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

        with mock_auth_config(fake_settings_with_primary_key, {"test-primary-key-123"}, mock_environment_detection, mock_auth_config_obj):
            with patch('app.infrastructure.security.auth.api_key_auth.config', mock_auth_config_obj):
                result = await verify_api_key_with_metadata(valid_http_bearer_credentials)

        # Then: Dictionary containing 'api_key' and metadata fields is returned
        assert isinstance(result, dict)
        assert "api_key" in result
        assert result["api_key"] == "test-primary-key-123"
        assert "api_key_type" in result  # Basic metadata always present when features enabled

    @pytest.mark.asyncio
    async def test_verify_api_key_with_metadata_includes_user_tracking_data(self, fake_settings_with_primary_key, valid_http_bearer_credentials, mock_environment_detection):
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

        with mock_auth_config(fake_settings_with_primary_key, {"test-primary-key-123"}, mock_environment_detection, mock_auth_config_obj):
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
                    result = await verify_api_key_with_metadata(valid_http_bearer_credentials)

        # Then: Returned metadata includes key_type and permissions information
        assert "key_type" in result
        assert "permissions" in result
        assert result["key_type"] == "primary"  # Based on primary key metadata
        assert isinstance(result["permissions"], list)

    @pytest.mark.asyncio
    async def test_verify_api_key_with_metadata_includes_request_logging_data(self, fake_settings_with_primary_key, valid_http_bearer_credentials, mock_environment_detection):
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

        with mock_auth_config(fake_settings_with_primary_key, {"test-primary-key-123"}, mock_environment_detection, mock_auth_config_obj):
            # Also need to mock the api_key_auth config to enable request logging
            with patch('app.infrastructure.security.auth.api_key_auth.config', mock_auth_config_obj):
                # When: verify_api_key_with_metadata is called with valid credentials
                result = await verify_api_key_with_metadata(valid_http_bearer_credentials)

        # Then: Returned metadata includes timestamp, endpoint, and method information
        assert "timestamp" in result
        assert "endpoint" in result
        assert "method" in result

    @pytest.mark.asyncio
    async def test_verify_api_key_with_metadata_delegates_authentication_to_base(self, fake_settings_with_primary_key, invalid_http_bearer_credentials, mock_environment_detection):
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
            - invalid_http_bearer_credentials: Invalid credentials for error case.
        """
        # Given: Configuration that would cause verify_api_key to fail
        # When: verify_api_key_with_metadata is called with same parameters
        # Then: The same AuthenticationError is raised by delegation
        with mock_auth_config(fake_settings_with_primary_key, {"test-primary-key-123"}, mock_environment_detection):
            with pytest.raises(AuthenticationError) as exc_info:
                await verify_api_key_with_metadata(invalid_http_bearer_credentials)

                # Verify the same error type and message as basic dependency
                error_msg = str(exc_info.value)
                assert "Invalid API key" in error_msg
                assert exc_info.value.context is not None

    @pytest.mark.asyncio
    async def test_verify_api_key_with_metadata_minimal_when_features_disabled(self, fake_settings_with_primary_key, valid_http_bearer_credentials, mock_environment_detection):
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
            - valid_http_bearer_credentials: Valid credentials for authentication.
        """
        # Given: AuthConfig with user tracking and request logging disabled (default)
        valid_http_bearer_credentials.credentials = "test-primary-key-123"

        # When: verify_api_key_with_metadata is called with valid credentials
        from unittest.mock import Mock
        mock_auth_config_obj = Mock()
        mock_auth_config_obj.enable_user_tracking = False
        mock_auth_config_obj.enable_request_logging = False

        with mock_auth_config(fake_settings_with_primary_key, {"test-primary-key-123"}, mock_environment_detection, mock_auth_config_obj):
            with patch('app.infrastructure.security.auth.api_key_auth.config', mock_auth_config_obj):
                result = await verify_api_key_with_metadata(valid_http_bearer_credentials)

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
    async def test_optional_verify_api_key_returns_none_for_missing_credentials(self, fake_settings_with_primary_key, mock_environment_detection):
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
        """
        # Given: No Authorization header or credentials are provided
        # When: optional_verify_api_key dependency is called
        with mock_auth_config(fake_settings_with_primary_key, {"test-primary-key-123"}, mock_environment_detection):
            result = await optional_verify_api_key(None)

        # Then: None is returned without raising any exceptions
        assert result is None

    @pytest.mark.asyncio
    async def test_optional_verify_api_key_returns_key_for_valid_credentials(self, fake_settings_with_primary_key, valid_http_bearer_credentials, mock_environment_detection):
        """
        Test that optional_verify_api_key returns API key for valid credentials.

        Verifies:
            Valid credentials are authenticated successfully when provided.

        Business Impact:
            Enables enhanced functionality for authenticated users while
            maintaining access for unauthenticated requests.

        Scenario:
            Given: Valid Bearer credentials are provided in request.
            When: optional_verify_api_key dependency is called.
            Then: The validated API key string is returned.

        Fixtures Used:
            - fake_settings_with_primary_key: Settings with valid API key.
            - valid_http_bearer_credentials: Valid credentials for authentication.
        """
        # Given: Valid Bearer credentials are provided in request
        valid_http_bearer_credentials.credentials = "test-primary-key-123"

        # When: optional_verify_api_key dependency is called
        with mock_auth_config(fake_settings_with_primary_key, {"test-primary-key-123"}, mock_environment_detection):
            result = await optional_verify_api_key(valid_http_bearer_credentials)

        # Then: The validated API key string is returned
        assert result == "test-primary-key-123"

    @pytest.mark.asyncio
    async def test_optional_verify_api_key_raises_error_for_invalid_credentials(self, fake_settings_with_primary_key, invalid_http_bearer_credentials, mock_environment_detection):
        """
        Test that optional_verify_api_key raises error for invalid credentials.

        Verifies:
            Invalid credentials are properly rejected when authentication is attempted.

        Business Impact:
            Prevents authentication bypass with invalid credentials and
            maintains security when credentials are explicitly provided.

        Scenario:
            Given: Invalid Bearer credentials are provided in request.
            When: optional_verify_api_key dependency is called.
            Then: AuthenticationError is raised for invalid credentials.

        Fixtures Used:
            - fake_settings_with_primary_key: Settings with valid API key.
            - invalid_http_bearer_credentials: Invalid credentials for error case.
        """
        # Given: Invalid Bearer credentials are provided in request
        # When: optional_verify_api_key dependency is called
        # Then: AuthenticationError is raised for invalid credentials
        with mock_auth_config(fake_settings_with_primary_key, {"test-primary-key-123"}, mock_environment_detection):
            with pytest.raises(AuthenticationError) as exc_info:
                await optional_verify_api_key(invalid_http_bearer_credentials)

                # Verify error contains appropriate context
                error_msg = str(exc_info.value)
                assert "Invalid API key" in error_msg
                assert exc_info.value.context is not None

    @pytest.mark.asyncio
    async def test_optional_verify_api_key_handles_development_mode(self, fake_settings, mock_environment_detection):
        """
        Test that optional_verify_api_key handles development mode appropriately.

        Verifies:
            Development mode behavior is consistent with base authentication.

        Business Impact:
            Ensures optional authentication works correctly in development
            environments without requiring API key configuration.

        Scenario:
            Given: No API keys configured (development mode).
            And: No credentials are provided in request.
            When: optional_verify_api_key dependency is called.
            Then: "development" string is returned for development access.

        Fixtures Used:
            - fake_settings: Empty settings for development mode.
            - mock_environment_detection: Development environment configuration.
        """
        # Given: No API keys configured (development mode)
        # And: No credentials are provided in request
        # When: optional_verify_api_key dependency is called
        with mock_auth_config(fake_settings, set(), mock_environment_detection):
            result = await optional_verify_api_key(None)

        # Then: None is returned (consistent with optional behavior)
        # In development mode, optional_verify_api_key returns None when no credentials provided
        # This is different from required verify_api_key which returns "development"
        assert result is None


class TestVerifyApiKeyHttpDependency:
    """
    Test suite for verify_api_key_http HTTP exception wrapper dependency.

    Scope:
        - HTTPException conversion for FastAPI middleware compatibility
        - Error response structure and HTTP status codes
        - WWW-Authenticate header inclusion
        - Context preservation in HTTP error responses

    Business Critical:
        verify_api_key_http is the recommended dependency for production use
        as it provides proper HTTP responses and avoids middleware conflicts.

    Test Strategy:
        - Test successful authentication delegation
        - Test HTTPException conversion from AuthenticationError
        - Test HTTP response structure and headers
        - Test error context preservation in HTTP responses
    """

    @pytest.mark.asyncio
    async def test_verify_api_key_http_returns_key_for_valid_authentication(self, fake_settings_with_primary_key, valid_http_bearer_credentials, mock_environment_detection):
        """
        Test that verify_api_key_http returns API key for successful authentication.

        Verifies:
            Valid authentication is handled identically to base dependency.

        Business Impact:
            Ensures HTTP wrapper maintains consistent authentication behavior
            while providing improved HTTP response handling.

        Scenario:
            Given: APIKeyAuth configured with valid API keys.
            And: Valid Bearer credentials are provided.
            When: verify_api_key_http dependency is called.
            Then: The validated API key string is returned.

        Fixtures Used:
            - fake_settings_with_primary_key: Settings with valid API key.
            - valid_http_bearer_credentials: Valid credentials for authentication.
        """
        # Given: APIKeyAuth configured with valid API keys
        # And: Valid Bearer credentials are provided
        valid_http_bearer_credentials.credentials = "test-primary-key-123"

        # When: verify_api_key_http dependency is called
        with mock_auth_config(fake_settings_with_primary_key, {"test-primary-key-123"}, mock_environment_detection):
            result = await verify_api_key_http(valid_http_bearer_credentials)

        # Then: The validated API key string is returned
        assert result == "test-primary-key-123"

    @pytest.mark.asyncio
    async def test_verify_api_key_http_converts_authentication_error_to_http_exception(self, fake_settings_with_primary_key, invalid_http_bearer_credentials, mock_environment_detection):
        """
        Test that verify_api_key_http converts AuthenticationError to HTTPException.

        Verifies:
            Custom authentication exceptions are converted to proper HTTP responses.

        Business Impact:
            Ensures proper HTTP error responses for API clients and prevents
            middleware conflicts in FastAPI applications.

        Scenario:
            Given: Configuration that causes verify_api_key to raise AuthenticationError.
            When: verify_api_key_http dependency is called.
            Then: HTTPException with 401 status is raised instead.

        Fixtures Used:
            - fake_settings_with_primary_key: Settings for authentication context.
            - invalid_http_bearer_credentials: Invalid credentials for error case.
        """
        # Given: Configuration that causes verify_api_key to raise AuthenticationError
        # When: verify_api_key_http dependency is called
        # Then: HTTPException with 401 status is raised instead
        with mock_auth_config(fake_settings_with_primary_key, {"test-primary-key-123"}, mock_environment_detection):
            with pytest.raises(HTTPException) as exc_info:
                await verify_api_key_http(invalid_http_bearer_credentials)

                # Verify it's converted to proper HTTP exception
                assert exc_info.value.status_code == 401
                assert exc_info.value.detail is not None
                assert isinstance(exc_info.value.detail, dict)
                assert "message" in exc_info.value.detail
                assert "Invalid API key" in exc_info.value.detail["message"]

    @pytest.mark.asyncio
    async def test_verify_api_key_http_includes_www_authenticate_header(self, fake_settings_with_primary_key, invalid_http_bearer_credentials, mock_environment_detection):
        """
        Test that verify_api_key_http includes WWW-Authenticate header in HTTP errors.

        Verifies:
            HTTP authentication errors include proper WWW-Authenticate header.

        Business Impact:
            Provides standards-compliant HTTP authentication responses that
            guide API clients on proper authentication methods.

        Scenario:
            Given: Authentication failure that triggers HTTPException.
            When: verify_api_key_http raises the HTTP exception.
            Then: Headers include WWW-Authenticate with Bearer scheme.

        Fixtures Used:
            - fake_settings_with_primary_key: Settings for authentication context.
            - invalid_http_bearer_credentials: Invalid credentials for error case.
        """
        # Given: Authentication failure that triggers HTTPException
        # When: verify_api_key_http raises the HTTP exception
        # Then: Headers include WWW-Authenticate with Bearer scheme
        with mock_auth_config(fake_settings_with_primary_key, {"test-primary-key-123"}, mock_environment_detection):
            with pytest.raises(HTTPException) as exc_info:
                await verify_api_key_http(invalid_http_bearer_credentials)

                # Verify WWW-Authenticate header is included
                assert exc_info.value.headers is not None
                assert "WWW-Authenticate" in exc_info.value.headers
                assert exc_info.value.headers["WWW-Authenticate"] == "Bearer"

    @pytest.mark.asyncio
    async def test_verify_api_key_http_preserves_error_context_in_http_response(self, fake_settings_with_primary_key, invalid_http_bearer_credentials, mock_environment_detection):
        """
        Test that verify_api_key_http preserves original error context in HTTP response.

        Verifies:
            HTTP error responses maintain detailed context for debugging.

        Business Impact:
            Enables troubleshooting of authentication issues while providing
            proper HTTP response structure for API clients.

        Scenario:
            Given: AuthenticationError with detailed context information.
            When: verify_api_key_http converts error to HTTPException.
            Then: HTTP response detail includes original message and context.

        Fixtures Used:
            - fake_settings_with_primary_key: Settings for authentication context.
            - invalid_http_bearer_credentials: Invalid credentials for error case.
            - mock_environment_detection: Environment context for error details.
        """
        # Given: AuthenticationError with detailed context information
        # When: verify_api_key_http converts error to HTTPException
        # Then: HTTP response detail includes original message and context
        with mock_auth_config(fake_settings_with_primary_key, {"test-primary-key-123"}, mock_environment_detection):
            with pytest.raises(HTTPException) as exc_info:
                await verify_api_key_http(invalid_http_bearer_credentials)

                # Verify original context is preserved
                assert "context" in exc_info.value.detail
                context = exc_info.value.detail["context"]
                assert "auth_method" in context
                assert "environment" in context
                assert "credentials_provided" in context
                assert context["credentials_provided"] is True

    @pytest.mark.asyncio
    async def test_verify_api_key_http_returns_401_status_for_authentication_failures(self, fake_settings_with_primary_key, invalid_http_bearer_credentials, mock_environment_detection):
        """
        Test that verify_api_key_http returns 401 Unauthorized for authentication failures.

        Verifies:
            Authentication failures result in proper HTTP 401 status codes.

        Business Impact:
            Ensures API clients receive standards-compliant HTTP status codes
            for authentication failures enabling proper error handling.

        Scenario:
            Given: Any authentication failure scenario.
            When: verify_api_key_http converts AuthenticationError to HTTPException.
            Then: HTTPException has status_code 401 (HTTP_401_UNAUTHORIZED).

        Fixtures Used:
            - fake_settings_with_primary_key: Settings for authentication context.
            - invalid_http_bearer_credentials: Invalid credentials for error case.
        """
        # Given: Any authentication failure scenario
        # When: verify_api_key_http converts AuthenticationError to HTTPException
        # Then: HTTPException has status_code 401 (HTTP_401_UNAUTHORIZED)
        with mock_auth_config(fake_settings_with_primary_key, {"test-primary-key-123"}, mock_environment_detection):
            with pytest.raises(HTTPException) as exc_info:
                await verify_api_key_http(invalid_http_bearer_credentials)

            # Verify status code is 401
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED
            assert exc_info.value.status_code == 401

        # Test with missing credentials scenario too
        with mock_auth_config(fake_settings_with_primary_key, {"test-primary-key-123"}, mock_environment_detection):
            with pytest.raises(HTTPException) as exc_info:
                await verify_api_key_http(None)  # Missing credentials

            # Verify status code is 401 for missing credentials too
            assert exc_info.value.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.asyncio
    async def test_verify_api_key_http_handles_development_mode_consistently(self, fake_settings, mock_environment_detection):
        """
        Test that verify_api_key_http handles development mode consistently with base dependency.

        Verifies:
            Development mode behavior is preserved through HTTP wrapper.

        Business Impact:
            Ensures development experience remains consistent across dependency
            variants while maintaining HTTP compatibility benefits.

        Scenario:
            Given: Development mode configuration (no API keys).
            When: verify_api_key_http is called without credentials.
            Then: "development" string is returned without HTTP exceptions.

        Fixtures Used:
            - fake_settings: Empty settings for development mode.
            - mock_environment_detection: Development environment configuration.
        """
        # Given: Development mode configuration (no API keys)
        # When: verify_api_key_http is called without credentials
        with mock_auth_config(fake_settings, set(), mock_environment_detection):
            result = await verify_api_key_http(None)

        # Then: "development" string is returned without HTTP exceptions
        assert result == "development"


class TestAuthenticationDependencyEdgeCases:
    """
    Test suite for edge cases and boundary conditions in authentication dependencies.

    Scope:
        - Error handling resilience across all dependencies
        - Concurrent access patterns and thread safety
        - Resource cleanup and exception safety
        - Integration consistency between dependency variants

    Business Critical:
        Robust edge case handling ensures authentication system reliability
        under adverse conditions and maintains security guarantees.

    Test Strategy:
        - Test dependencies with corrupted or malformed input
        - Test behavior during system resource constraints
        - Test integration consistency across dependency variants
        - Test graceful degradation scenarios
    """

    @pytest.mark.asyncio
    async def test_dependencies_handle_malformed_bearer_credentials(self, fake_settings_with_primary_key, mock_http_bearer_credentials, mock_environment_detection):
        """
        Test that dependencies handle malformed Bearer token format gracefully.

        Verifies:
            Malformed Authorization headers are processed safely.

        Business Impact:
            Prevents authentication system failures due to malformed client
            requests and maintains security under attack conditions.

        Scenario:
            Given: Authorization header with malformed Bearer token format.
            When: Any authentication dependency is called.
            Then: Appropriate authentication failure is returned safely.

        Fixtures Used:
            - fake_settings_with_primary_key: Settings for authentication context.
            - mock_http_bearer_credentials: Configured with malformed data.
        """
        # Given: Authorization header with malformed Bearer token format
        # Test various malformed credentials
        malformed_credentials = [
            "",  # Empty string
            " ",  # Whitespace only
            "\n\t",  # Special characters
            "malformed-no-prefix",  # No 'sk-' prefix
        ]

        with mock_auth_config(fake_settings_with_primary_key, {"test-primary-key-123"}, mock_environment_detection):
            for malformed_cred in malformed_credentials:
                mock_http_bearer_credentials.credentials = malformed_cred

                # When: Any authentication dependency is called
                # Then: Appropriate authentication failure is returned safely
                with pytest.raises(AuthenticationError):
                    await verify_api_key(mock_http_bearer_credentials)

                # Test HTTP variant too
                with pytest.raises(HTTPException):
                    await verify_api_key_http(mock_http_bearer_credentials)

    @pytest.mark.asyncio
    async def test_dependencies_maintain_consistent_behavior_across_variants(self, fake_settings_with_primary_key, valid_http_bearer_credentials, invalid_http_bearer_credentials, mock_environment_detection):
        """
        Test that all dependency variants maintain consistent authentication logic.

        Verifies:
            Authentication decisions are consistent across dependency implementations.

        Business Impact:
            Ensures predictable authentication behavior regardless of dependency
            choice and prevents security policy divergence.

        Scenario:
            Given: Identical authentication scenarios across dependencies.
            When: Each dependency variant is tested with same inputs.
            Then: Authentication success/failure decisions are consistent.

        Fixtures Used:
            - fake_settings_with_primary_key: Settings for consistent testing.
            - valid_http_bearer_credentials: Valid credentials for success case.
            - invalid_http_bearer_credentials: Invalid credentials for failure case.
        """
        # Given: Identical authentication scenarios across dependencies
        valid_http_bearer_credentials.credentials = "test-primary-key-123"

        with mock_auth_config(fake_settings_with_primary_key, {"test-primary-key-123"}, mock_environment_detection):
            # Test valid credentials - all should succeed
            basic_result = await verify_api_key(valid_http_bearer_credentials)
            http_result = await verify_api_key_http(valid_http_bearer_credentials)
            optional_result = await optional_verify_api_key(valid_http_bearer_credentials)
            metadata_result = await verify_api_key_with_metadata(valid_http_bearer_credentials)

            # All should return the same API key for valid credentials
            assert basic_result == "test-primary-key-123"
            assert http_result == "test-primary-key-123"
            assert optional_result == "test-primary-key-123"
            assert metadata_result["api_key"] == "test-primary-key-123"

            # Test invalid credentials - all should fail consistently
            # Reset invalid credentials to ensure they're actually invalid
            invalid_http_bearer_credentials.credentials = "invalid-test-key"

            with pytest.raises(AuthenticationError):
                await verify_api_key(invalid_http_bearer_credentials)

            # Reset credentials for each test to ensure they're invalid
            invalid_http_bearer_credentials.credentials = "invalid-test-key"
            with pytest.raises(HTTPException):
                await verify_api_key_http(invalid_http_bearer_credentials)

            invalid_http_bearer_credentials.credentials = "invalid-test-key"
            with pytest.raises(AuthenticationError):
                await optional_verify_api_key(invalid_http_bearer_credentials)

            invalid_http_bearer_credentials.credentials = "invalid-test-key"
            with pytest.raises(AuthenticationError):
                await verify_api_key_with_metadata(invalid_http_bearer_credentials)

    @pytest.mark.asyncio
    async def test_dependencies_handle_concurrent_access_safely(self, fake_settings_with_primary_key, valid_http_bearer_credentials, mock_environment_detection):
        """
        Test that dependencies handle concurrent authentication requests safely.

        Verifies:
            Authentication dependencies are thread-safe for concurrent requests.

        Business Impact:
            Ensures authentication system stability under high load and
            prevents race conditions in production environments.

        Scenario:
            Given: Multiple concurrent authentication requests.
            When: Dependencies are called simultaneously from different threads.
            Then: All requests are processed correctly without interference.

        Fixtures Used:
            - fake_settings_with_primary_key: Settings for concurrent testing.
            - valid_http_bearer_credentials: Valid credentials for concurrent requests.
        """
        import asyncio
        from unittest.mock import Mock

        # Given: Multiple concurrent authentication requests
        valid_http_bearer_credentials.credentials = "test-primary-key-123"

        # Create multiple credential objects to simulate concurrent requests
        credential_mocks = []
        for i in range(10):
            mock_cred = Mock()
            mock_cred.credentials = "test-primary-key-123"
            credential_mocks.append(mock_cred)

        with mock_auth_config(fake_settings_with_primary_key, {"test-primary-key-123"}, mock_environment_detection):
            # When: Dependencies are called simultaneously
            tasks = [
                verify_api_key(cred) for cred in credential_mocks
            ]

            # Then: All requests are processed correctly without interference
            results = await asyncio.gather(*tasks)

            # Verify all results are correct
            assert len(results) == 10
            for result in results:
                assert result == "test-primary-key-123"

    @pytest.mark.asyncio
    async def test_dependencies_preserve_security_during_error_conditions(self, fake_settings_with_primary_key, mock_environment_detection):
        """
        Test that dependencies maintain security guarantees during error conditions.

        Verifies:
            Authentication security is preserved even when errors occur.

        Business Impact:
            Ensures authentication system fails securely and doesn't accidentally
            grant access during error conditions or system stress.

        Scenario:
            Given: Various error conditions (memory pressure, service failures).
            When: Authentication dependencies encounter these conditions.
            Then: Security is preserved with fail-safe behavior.

        Fixtures Used:
            - fake_settings_with_primary_key: Settings for security testing.
            - mock_environment_detection: Configured to simulate various conditions.
        """
        from unittest.mock import Mock

        # Simulate various error conditions
        error_conditions = [
            Exception("Memory error"),
            RuntimeError("Service unavailable"),
            KeyError("Configuration missing"),
            ValueError("Invalid state"),
        ]

        # Create test credentials
        test_credentials = Mock()
        test_credentials.credentials = "potentially-valid-key"

        for error in error_conditions:
            # Given: Various error conditions
            def failing_env_detection(*args, **kwargs):
                raise error

            with mock_auth_config(fake_settings_with_primary_key, {"test-primary-key-123"}):
                with patch('app.infrastructure.security.auth.get_environment_info', side_effect=failing_env_detection):
                    # When: Authentication dependencies encounter these conditions
                    # Then: Security is preserved with fail-safe behavior

                    # Should fail securely - invalid key should still be rejected
                    with pytest.raises((AuthenticationError, Exception)):
                        await verify_api_key(test_credentials)

                    # HTTP variant should also fail securely
                    with pytest.raises((HTTPException, Exception)):
                        await verify_api_key_http(test_credentials)

        # Test with valid credentials and environment failure
        # Should succeed despite environment detection failure
        test_credentials.credentials = "test-primary-key-123"

        def failing_env_detection(*args, **kwargs):
            raise Exception("Environment detection failed")

        with mock_auth_config(fake_settings_with_primary_key, {"test-primary-key-123"}):
            with patch('app.infrastructure.security.auth.get_environment_info', side_effect=failing_env_detection):
                # Valid key should still work despite environment detection failure
                result = await verify_api_key(test_credentials)
                assert result == "test-primary-key-123"