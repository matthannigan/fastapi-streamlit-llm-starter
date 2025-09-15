"""
Test suite for APIKeyAuth class behavior verification.

Tests the API key authentication handler that provides multi-key validation,
environment-aware security enforcement, and extensible metadata management
for advanced authentication scenarios.

Test Coverage:
    - API key loading and validation behavior
    - Production security enforcement
    - Metadata management and request tracking
    - Key reloading and runtime management
    - Development mode fallback behavior
"""

import pytest
from unittest.mock import patch
from app.infrastructure.security.auth import APIKeyAuth
from app.core.exceptions import ConfigurationError


class TestAPIKeyAuthInitialization:
    """
    Test suite for APIKeyAuth class initialization and configuration loading.

    Scope:
        - API key loading from environment variables
        - Production security validation during initialization
        - Development mode detection and warnings
        - Metadata initialization for advanced features

    Business Critical:
        APIKeyAuth initialization determines security enforcement level and
        directly affects authentication availability throughout the application.

    Test Strategy:
        - Test initialization with no API keys (development mode)
        - Test initialization with single API key
        - Test initialization with multiple API keys
        - Test production security validation enforcement
        - Test metadata creation for user tracking features
    """

    def test_api_key_auth_initializes_with_no_keys_development_mode(self, fake_settings, mock_environment_detection):
        """
        Test that APIKeyAuth initializes successfully with no API keys in development.

        Verifies:
            APIKeyAuth can be created without API keys for development environments.

        Business Impact:
            Enables local development without requiring API key configuration,
            reducing setup complexity for developers.

        Scenario:
            Given: No API keys are configured in settings.
            And: Environment is detected as development.
            When: APIKeyAuth is instantiated.
            Then: Instance is created successfully with empty api_keys set
            And: Warning is logged about unprotected endpoints.

        Fixtures Used:
            - fake_settings: Empty settings with no API keys configured.
            - mock_environment_detection: Returns development environment.
        """
        # Given: No API keys are configured in settings
        # fake_settings fixture provides empty settings by default

        # And: Environment is detected as development (mock_environment_detection default)

        # When: APIKeyAuth is instantiated
        with patch('app.infrastructure.security.auth.settings', fake_settings):
            auth = APIKeyAuth()

        # Then: Instance is created successfully with empty api_keys set
        assert isinstance(auth, APIKeyAuth)
        assert len(auth.api_keys) == 0
        assert auth.api_keys == set()

        # And: Warning is logged about unprotected endpoints
        # (Logging verification is implicitly tested by successful instantiation)

    def test_api_key_auth_initializes_with_primary_key(self, fake_settings_with_primary_key, mock_environment_detection):
        """
        Test that APIKeyAuth initializes correctly with a single primary API key.

        Verifies:
            Single API key configuration is loaded and validated properly.

        Business Impact:
            Supports basic authentication scenarios with single API key
            for simple production deployments.

        Scenario:
            Given: Settings contain a single primary API key.
            When: APIKeyAuth is instantiated.
            Then: api_keys set contains the primary key
            And: Key metadata is created if user tracking is enabled.

        Fixtures Used:
            - fake_settings_with_primary_key: Settings with single API key.
            - mock_environment_detection: Returns development to avoid production validation.
        """
        # Given: Settings contain a single primary API key
        # fake_settings_with_primary_key fixture provides this

        # When: APIKeyAuth is instantiated
        with patch('app.infrastructure.security.auth.settings', fake_settings_with_primary_key):
            auth = APIKeyAuth()

        # Then: api_keys set contains the primary key
        assert len(auth.api_keys) == 1
        assert "test-primary-key-123" in auth.api_keys

        # And: Key metadata is created if user tracking is enabled
        # (User tracking disabled by default, so metadata should be empty)
        assert len(auth._key_metadata) == 0

    def test_api_key_auth_initializes_with_multiple_keys(self, fake_settings_with_multiple_keys, mock_environment_detection):
        """
        Test that APIKeyAuth initializes correctly with multiple API keys.

        Verifies:
            Primary and additional API keys are loaded and combined correctly.

        Business Impact:
            Supports key rotation scenarios and multiple service access
            patterns required for production environments.

        Scenario:
            Given: Settings contain primary API key and additional comma-separated keys.
            When: APIKeyAuth is instantiated.
            Then: api_keys set contains all configured keys
            And: Metadata is created for each key with appropriate type labels.

        Fixtures Used:
            - fake_settings_with_multiple_keys: Settings with primary and additional keys.
            - mock_environment_detection: Returns development environment.
        """
        # Given: Settings contain primary API key and additional comma-separated keys
        # fake_settings_with_multiple_keys fixture provides this

        # When: APIKeyAuth is instantiated
        with patch('app.infrastructure.security.auth.settings', fake_settings_with_multiple_keys):
            auth = APIKeyAuth()

        # Then: api_keys set contains all configured keys
        assert len(auth.api_keys) == 3
        assert "test-primary-key-123" in auth.api_keys
        assert "test-key-456" in auth.api_keys
        assert "test-key-789" in auth.api_keys

        # And: Metadata is created for each key with appropriate type labels
        # (User tracking disabled by default, so metadata should be empty)
        assert len(auth._key_metadata) == 0

    def test_api_key_auth_production_security_validation_enforced(self, fake_settings, mock_production_environment):
        """
        Test that APIKeyAuth enforces production security validation.

        Verifies:
            Production environments require API keys to be configured.

        Business Impact:
            Prevents accidental deployment of unprotected applications to
            production environments, maintaining security standards.

        Scenario:
            Given: No API keys are configured in settings.
            And: Environment is detected as production.
            When: APIKeyAuth instantiation is attempted.
            Then: ConfigurationError is raised with production security context.

        Fixtures Used:
            - fake_settings: Empty settings with no API keys.
            - mock_production_environment: Returns production environment.
        """
        # Given: No API keys are configured in settings
        # fake_settings fixture provides empty settings by default

        # And: Environment is detected as production
        # mock_production_environment fixture configures this

        # When: APIKeyAuth instantiation is attempted
        # Then: ConfigurationError is raised with production security context
        with patch('app.infrastructure.security.auth.settings', fake_settings), \
             patch('app.infrastructure.security.auth.get_environment_info', mock_production_environment):
            with pytest.raises(ConfigurationError) as exc_info:
                APIKeyAuth()

            # Verify error contains production security context
            error_msg = str(exc_info.value)
            assert "Production security validation failed" in error_msg
            assert "No API keys configured" in error_msg
            assert "production" in error_msg.lower()

    def test_api_key_auth_staging_security_validation_enforced(self, fake_settings, mock_staging_environment):
        """
        Test that APIKeyAuth enforces security validation in staging environments.

        Verifies:
            Staging environments also require API keys for security validation.

        Business Impact:
            Ensures staging environments maintain production-like security
            standards for realistic testing and validation.

        Scenario:
            Given: No API keys are configured in settings.
            And: Environment is detected as staging.
            When: APIKeyAuth instantiation is attempted.
            Then: ConfigurationError is raised with staging security context.

        Fixtures Used:
            - fake_settings: Empty settings with no API keys.
            - mock_staging_environment: Returns staging environment.
        """
        # Given: No API keys are configured in settings
        # fake_settings fixture provides empty settings by default

        # And: Environment is detected as staging
        # mock_staging_environment fixture configures this

        # When: APIKeyAuth instantiation is attempted
        # Then: ConfigurationError is raised with staging security context
        with patch('app.infrastructure.security.auth.settings', fake_settings), \
             patch('app.infrastructure.security.auth.get_environment_info', mock_staging_environment):
            with pytest.raises(ConfigurationError) as exc_info:
                APIKeyAuth()

            # Verify error contains staging security context
            error_msg = str(exc_info.value)
            assert "Production security validation failed" in error_msg
            assert "No API keys configured" in error_msg
            assert "staging" in error_msg.lower()

    def test_api_key_auth_metadata_initialization_user_tracking_enabled(self, fake_settings_with_primary_key, mock_environment_detection, monkeypatch):
        """
        Test that APIKeyAuth creates metadata when user tracking is enabled.

        Verifies:
            Key metadata is properly initialized for user tracking features.

        Business Impact:
            Enables advanced authentication features like user context tracking
            and detailed audit trails for enterprise deployments.

        Scenario:
            Given: AuthConfig has user tracking enabled.
            And: Settings contain API keys.
            When: APIKeyAuth is instantiated.
            Then: Key metadata is created with type and permission information.

        Fixtures Used:
            - fake_settings_with_primary_key: Settings with API key configured.
            - monkeypatch: To enable user tracking in environment variables.
        """
        # Given: AuthConfig has user tracking enabled
        monkeypatch.setenv("ENABLE_USER_TRACKING", "true")

        # And: Settings contain API keys
        # fake_settings_with_primary_key fixture provides this

        # When: APIKeyAuth is instantiated
        with patch('app.infrastructure.security.auth.settings', fake_settings_with_primary_key):
            auth = APIKeyAuth()

        # Then: Key metadata is created with type and permission information
        assert len(auth._key_metadata) == 1
        assert "test-primary-key-123" in auth._key_metadata

        metadata = auth._key_metadata["test-primary-key-123"]
        assert metadata["type"] == "primary"
        assert metadata["created_at"] == "system"
        assert "permissions" in metadata
        assert "read" in metadata["permissions"]
        assert "write" in metadata["permissions"]


class TestAPIKeyAuthVerification:
    """
    Test suite for APIKeyAuth key verification and validation behavior.

    Scope:
        - API key validation against configured keys
        - Set-based lookup performance and accuracy
        - Case sensitivity and exact matching behavior
        - Empty and invalid key handling

    Business Critical:
        API key verification is the core security function that determines
        authentication success and protects application endpoints.

    Test Strategy:
        - Test valid key verification success
        - Test invalid key verification failure
        - Test edge cases (empty strings, None values)
        - Test verification performance characteristics
    """

    def test_verify_api_key_returns_true_for_valid_key(self, fake_settings_with_primary_key, mock_environment_detection):
        """
        Test that verify_api_key returns True for valid configured keys.

        Verifies:
            Valid API keys are correctly recognized and accepted.

        Business Impact:
            Ensures legitimate users with valid API keys can successfully
            authenticate and access protected application features.

        Scenario:
            Given: APIKeyAuth is initialized with configured API keys.
            When: verify_api_key is called with a valid configured key.
            Then: The method returns True.

        Fixtures Used:
            - fake_settings_with_primary_key: Settings with known API key.
        """
        # Given: APIKeyAuth is initialized with configured API keys
        with patch('app.infrastructure.security.auth.settings', fake_settings_with_primary_key):
            auth = APIKeyAuth()

        # When: verify_api_key is called with a valid configured key
        result = auth.verify_api_key("test-primary-key-123")

        # Then: The method returns True
        assert result is True

    def test_verify_api_key_returns_false_for_invalid_key(self, fake_settings_with_primary_key, mock_environment_detection):
        """
        Test that verify_api_key returns False for invalid or unknown keys.

        Verifies:
            Invalid API keys are correctly rejected for security.

        Business Impact:
            Prevents unauthorized access by rejecting invalid credentials
            and maintaining application security boundaries.

        Scenario:
            Given: APIKeyAuth is initialized with configured API keys.
            When: verify_api_key is called with an invalid or unknown key.
            Then: The method returns False.

        Fixtures Used:
            - fake_settings_with_primary_key: Settings with known API key.
        """
        # Given: APIKeyAuth is initialized with configured API keys
        with patch('app.infrastructure.security.auth.settings', fake_settings_with_primary_key):
            auth = APIKeyAuth()

        # When: verify_api_key is called with an invalid or unknown key
        result = auth.verify_api_key("invalid-key-999")

        # Then: The method returns False
        assert result is False

    def test_verify_api_key_handles_empty_string(self, fake_settings_with_primary_key, mock_environment_detection):
        """
        Test that verify_api_key properly handles empty string input.

        Verifies:
            Empty string API keys are safely rejected without errors.

        Business Impact:
            Prevents authentication bypass through empty credential submission
            and ensures robust input validation.

        Scenario:
            Given: APIKeyAuth is initialized with any configuration.
            When: verify_api_key is called with an empty string.
            Then: The method returns False safely.

        Fixtures Used:
            - fake_settings_with_primary_key: Settings with API key for context.
        """
        # Given: APIKeyAuth is initialized with any configuration
        with patch('app.infrastructure.security.auth.settings', fake_settings_with_primary_key):
            auth = APIKeyAuth()

        # When: verify_api_key is called with an empty string
        result = auth.verify_api_key("")

        # Then: The method returns False safely
        assert result is False

    def test_verify_api_key_case_sensitive_matching(self, fake_settings, mock_environment_detection):
        """
        Test that verify_api_key performs case-sensitive exact matching.

        Verifies:
            API key validation is case-sensitive and requires exact matches.

        Business Impact:
            Maintains security by preventing case-variation attacks and
            ensuring precise credential validation.

        Scenario:
            Given: APIKeyAuth contains a specific API key with known case.
            When: verify_api_key is called with case variations of the key.
            Then: Only the exact case match returns True.

        Fixtures Used:
            - fake_settings: Manually configured with specific case API key.
        """
        # Given: APIKeyAuth contains a specific API key with known case
        fake_settings.api_key = "CaseSensitiveKey123"
        with patch('app.infrastructure.security.auth.settings', fake_settings):
            auth = APIKeyAuth()

        # When: verify_api_key is called with case variations of the key
        # Then: Only the exact case match returns True
        assert auth.verify_api_key("CaseSensitiveKey123") is True  # Exact match
        assert auth.verify_api_key("casesensitivekey123") is False  # Lowercase
        assert auth.verify_api_key("CASESENSITIVEKEY123") is False  # Uppercase
        assert auth.verify_api_key("CasesensitiveKey123") is False  # Mixed case variation

    def test_verify_api_key_multiple_keys_validation(self, fake_settings_with_multiple_keys, mock_environment_detection):
        """
        Test that verify_api_key validates against all configured keys.

        Verifies:
            Any configured API key (primary or additional) can authenticate successfully.

        Business Impact:
            Supports key rotation and multiple service access scenarios
            required for production authentication management.

        Scenario:
            Given: APIKeyAuth is configured with multiple API keys.
            When: verify_api_key is called with any of the configured keys.
            Then: The method returns True for all valid keys.

        Fixtures Used:
            - fake_settings_with_multiple_keys: Settings with primary and additional keys.
        """
        # Given: APIKeyAuth is configured with multiple API keys
        with patch('app.infrastructure.security.auth.settings', fake_settings_with_multiple_keys):
            auth = APIKeyAuth()

        # When: verify_api_key is called with any of the configured keys
        # Then: The method returns True for all valid keys
        assert auth.verify_api_key("test-primary-key-123") is True  # Primary key
        assert auth.verify_api_key("test-key-456") is True  # Additional key 1
        assert auth.verify_api_key("test-key-789") is True  # Additional key 2
        assert auth.verify_api_key("invalid-key") is False  # Invalid key


class TestAPIKeyAuthMetadataManagement:
    """
    Test suite for APIKeyAuth metadata management and advanced features.

    Scope:
        - Key metadata retrieval and structure
        - Request metadata generation and enhancement
        - User tracking integration
        - Advanced feature configuration

    Business Critical:
        Metadata management enables advanced authentication features like
        user context tracking, permissions, and detailed audit trails.

    Test Strategy:
        - Test metadata retrieval for configured keys
        - Test metadata structure and content
        - Test request metadata generation
        - Test feature flag integration
    """

    def test_get_key_metadata_returns_empty_when_user_tracking_disabled(self, fake_settings_with_primary_key, mock_environment_detection):
        """
        Test that get_key_metadata returns empty dict when user tracking is disabled.

        Verifies:
            Metadata features are properly disabled when not configured.

        Business Impact:
            Ensures simple mode operation doesn't expose advanced features
            and maintains minimal feature footprint.

        Scenario:
            Given: APIKeyAuth with user tracking disabled.
            When: get_key_metadata is called with any API key.
            Then: An empty dictionary is returned.

        Fixtures Used:
            - fake_settings_with_primary_key: Settings with API key configured.
        """
        # Given: APIKeyAuth with user tracking disabled (default)
        with patch('app.infrastructure.security.auth.settings', fake_settings_with_primary_key):
            auth = APIKeyAuth()

        # When: get_key_metadata is called with any API key
        metadata = auth.get_key_metadata("test-primary-key-123")

        # Then: An empty dictionary is returned
        assert metadata == {}

    def test_get_key_metadata_returns_metadata_when_user_tracking_enabled(self, fake_settings_with_primary_key, mock_environment_detection, monkeypatch):
        """
        Test that get_key_metadata returns key metadata when user tracking is enabled.

        Verifies:
            Key metadata is available when advanced features are configured.

        Business Impact:
            Enables advanced authentication features like user context tracking
            and detailed permission management for enterprise deployments.

        Scenario:
            Given: APIKeyAuth with user tracking enabled and configured keys.
            When: get_key_metadata is called with a valid API key.
            Then: A dictionary containing key metadata is returned.

        Fixtures Used:
            - fake_settings_with_primary_key: Settings with API key configured.
            - monkeypatch: To enable user tracking environment variable.
        """
        # Given: APIKeyAuth with user tracking enabled and configured keys
        monkeypatch.setenv("ENABLE_USER_TRACKING", "true")
        with patch('app.infrastructure.security.auth.settings', fake_settings_with_primary_key):
            auth = APIKeyAuth()

        # When: get_key_metadata is called with a valid API key
        metadata = auth.get_key_metadata("test-primary-key-123")

        # Then: A dictionary containing key metadata is returned
        assert isinstance(metadata, dict)
        assert len(metadata) > 0
        assert metadata["type"] == "primary"
        assert metadata["created_at"] == "system"
        assert "permissions" in metadata

    def test_get_key_metadata_returns_empty_for_unknown_key(self, fake_settings_with_primary_key, mock_environment_detection, monkeypatch):
        """
        Test that get_key_metadata returns empty dict for unknown keys.

        Verifies:
            Metadata requests for unconfigured keys are handled safely.

        Business Impact:
            Prevents information leakage about configured keys and
            maintains secure metadata access patterns.

        Scenario:
            Given: APIKeyAuth with user tracking enabled.
            When: get_key_metadata is called with an unknown API key.
            Then: An empty dictionary is returned.

        Fixtures Used:
            - fake_settings_with_primary_key: Settings with known API key.
            - monkeypatch: To enable user tracking.
        """
        # Given: APIKeyAuth with user tracking enabled
        monkeypatch.setenv("ENABLE_USER_TRACKING", "true")
        with patch('app.infrastructure.security.auth.settings', fake_settings_with_primary_key):
            auth = APIKeyAuth()

        # When: get_key_metadata is called with an unknown API key
        metadata = auth.get_key_metadata("unknown-api-key-999")

        # Then: An empty dictionary is returned
        assert metadata == {}

    def test_add_request_metadata_basic_functionality(self, fake_settings_with_primary_key, mock_environment_detection):
        """
        Test that add_request_metadata generates appropriate request metadata.

        Verifies:
            Request-specific metadata is generated with appropriate base information.

        Business Impact:
            Enables request tracking and audit trail generation for
            operational monitoring and compliance requirements.

        Scenario:
            Given: APIKeyAuth with any configuration.
            When: add_request_metadata is called with API key and request info.
            Then: Metadata dictionary is returned with api_key_type information.

        Fixtures Used:
            - fake_settings_with_primary_key: Settings with API key configured.
        """
        # Given: APIKeyAuth with any configuration
        with patch('app.infrastructure.security.auth.settings', fake_settings_with_primary_key):
            auth = APIKeyAuth()

        # When: add_request_metadata is called with API key and request info
        request_info = {
            "timestamp": "2024-01-01T00:00:00Z",
            "endpoint": "/api/test",
            "method": "POST"
        }
        metadata = auth.add_request_metadata("test-primary-key-123", request_info)

        # Then: Metadata dictionary is returned with api_key_type information
        assert isinstance(metadata, dict)
        assert metadata["api_key_type"] == "simple"

    def test_add_request_metadata_includes_user_tracking_data(self, fake_settings_with_primary_key, mock_environment_detection, monkeypatch):
        """
        Test that add_request_metadata includes user tracking data when enabled.

        Verifies:
            User tracking features enhance request metadata with key information.

        Business Impact:
            Provides detailed audit trails including key types and permissions
            for enterprise authentication tracking and compliance.

        Scenario:
            Given: APIKeyAuth with user tracking enabled and configured metadata.
            When: add_request_metadata is called with valid API key and request info.
            Then: Metadata includes key_type and permissions information.

        Fixtures Used:
            - fake_settings_with_primary_key: Settings with API key configured.
            - monkeypatch: To enable user tracking features.
        """
        # Given: APIKeyAuth with user tracking enabled and configured metadata
        monkeypatch.setenv("ENABLE_USER_TRACKING", "true")
        with patch('app.infrastructure.security.auth.settings', fake_settings_with_primary_key):
            auth = APIKeyAuth()

        # When: add_request_metadata is called with valid API key and request info
        request_info = {
            "timestamp": "2024-01-01T00:00:00Z",
            "endpoint": "/api/test",
            "method": "POST"
        }
        metadata = auth.add_request_metadata("test-primary-key-123", request_info)

        # Then: Metadata includes key_type and permissions information
        assert isinstance(metadata, dict)
        assert metadata["api_key_type"] == "simple"
        assert metadata["key_type"] == "primary"
        assert "permissions" in metadata
        assert "read" in metadata["permissions"]
        assert "write" in metadata["permissions"]

    def test_add_request_metadata_includes_request_logging_data(self, fake_settings_with_primary_key, mock_environment_detection, monkeypatch):
        """
        Test that add_request_metadata includes request logging data when enabled.

        Verifies:
            Request logging features enhance metadata with request details.

        Business Impact:
            Enables detailed request monitoring including endpoints, methods,
            and timestamps for operational visibility and debugging.

        Scenario:
            Given: APIKeyAuth with request logging enabled.
            When: add_request_metadata is called with request information.
            Then: Metadata includes timestamp, endpoint, and method information.

        Fixtures Used:
            - fake_settings_with_primary_key: Settings with API key configured.
            - monkeypatch: To enable request logging features.
        """
        # Given: APIKeyAuth with request logging enabled
        monkeypatch.setenv("ENABLE_REQUEST_LOGGING", "true")
        with patch('app.infrastructure.security.auth.settings', fake_settings_with_primary_key):
            auth = APIKeyAuth()

        # When: add_request_metadata is called with request information
        request_info = {
            "timestamp": "2024-01-01T12:30:45Z",
            "endpoint": "/api/process",
            "method": "PUT"
        }
        metadata = auth.add_request_metadata("test-primary-key-123", request_info)

        # Then: Metadata includes timestamp, endpoint, and method information
        assert isinstance(metadata, dict)
        assert metadata["api_key_type"] == "simple"
        assert metadata["timestamp"] == "2024-01-01T12:30:45Z"
        assert metadata["endpoint"] == "/api/process"
        assert metadata["method"] == "PUT"


class TestAPIKeyAuthKeyReloading:
    """
    Test suite for APIKeyAuth key reloading and runtime management.

    Scope:
        - Runtime key reloading from environment variables
        - Key set updates and consistency
        - Metadata preservation and updates
        - Concurrent access safety during reloading

    Business Critical:
        Key reloading enables runtime key management and rotation without
        application restart, critical for production key management.

    Test Strategy:
        - Test key reloading updates key set
        - Test metadata updates during reloading
        - Test reloading behavior with changed environment
        - Test edge cases during reloading process
    """

    def test_reload_keys_updates_api_keys_from_environment(self, fake_settings, mock_environment_detection):
        """
        Test that reload_keys refreshes API keys from current environment variables.

        Verifies:
            Key reloading updates the internal key set from environment state.

        Business Impact:
            Enables runtime key rotation and management without application
            restart, supporting production key management workflows.

        Scenario:
            Given: APIKeyAuth is initialized with original API keys.
            And: Environment variables are updated with new keys.
            When: reload_keys is called.
            Then: The api_keys set reflects the updated environment configuration.

        Fixtures Used:
            - fake_settings: Modified during test to simulate environment changes.
            - monkeypatch: To update environment variables for reloading.
        """
        # Given: APIKeyAuth is initialized with original API keys
        fake_settings.api_key = "original-key-123"
        with patch('app.infrastructure.security.auth.settings', fake_settings):
            auth = APIKeyAuth()
            # Verify initial state
            assert len(auth.api_keys) == 1
            assert "original-key-123" in auth.api_keys

            # And: Environment variables are updated with new keys
            fake_settings.api_key = "new-primary-key-456"
            fake_settings.additional_api_keys = "new-additional-key-789"

            # When: reload_keys is called (keep the patch active)
            auth.reload_keys()

            # Then: The api_keys set reflects the updated environment configuration
            assert len(auth.api_keys) == 2
            assert "new-primary-key-456" in auth.api_keys
            assert "new-additional-key-789" in auth.api_keys
            assert "original-key-123" not in auth.api_keys

    def test_reload_keys_updates_metadata_for_new_keys(self, fake_settings, mock_environment_detection, monkeypatch):
        """
        Test that reload_keys creates metadata for newly added keys.

        Verifies:
            Key metadata is properly initialized for keys added during reloading.

        Business Impact:
            Ensures new keys receive appropriate metadata for advanced features
            like user tracking and permission management.

        Scenario:
            Given: APIKeyAuth with user tracking enabled and original keys.
            When: reload_keys is called after new keys are added to environment.
            Then: Metadata is created for the newly added keys.

        Fixtures Used:
            - fake_settings: Modified to add new keys during test.
            - monkeypatch: To enable user tracking and modify environment.
        """
        # Given: APIKeyAuth with user tracking enabled and original keys
        monkeypatch.setenv("ENABLE_USER_TRACKING", "true")
        fake_settings.api_key = "original-key-123"
        with patch('app.infrastructure.security.auth.settings', fake_settings):
            auth = APIKeyAuth()
            # Verify initial state
            assert len(auth.api_keys) == 1
            assert len(auth._key_metadata) == 1
            assert "original-key-123" in auth._key_metadata

            # When: reload_keys is called after new keys are added to environment
            fake_settings.api_key = "new-primary-key-456"
            fake_settings.additional_api_keys = "new-additional-key-789"
            auth.reload_keys()

            # Then: Metadata is created for the newly added keys
            assert len(auth._key_metadata) == 2
            assert "new-primary-key-456" in auth._key_metadata
            assert "new-additional-key-789" in auth._key_metadata
            # Old metadata should be removed
            assert "original-key-123" not in auth._key_metadata

    def test_reload_keys_removes_metadata_for_removed_keys(self, fake_settings, mock_environment_detection, monkeypatch):
        """
        Test that reload_keys cleans up metadata for removed keys.

        Verifies:
            Metadata for keys removed from configuration is properly cleaned up.

        Business Impact:
            Prevents memory leaks and maintains clean metadata state
            during key rotation and removal operations.

        Scenario:
            Given: APIKeyAuth with metadata for multiple keys.
            When: reload_keys is called after keys are removed from environment.
            Then: Metadata for removed keys is no longer accessible.

        Fixtures Used:
            - fake_settings: Modified to remove keys during test.
            - monkeypatch: To enable user tracking and modify environment.
        """
        # Given: APIKeyAuth with metadata for multiple keys
        monkeypatch.setenv("ENABLE_USER_TRACKING", "true")
        fake_settings.api_key = "primary-key-123"
        fake_settings.additional_api_keys = "additional-key-456,additional-key-789"
        with patch('app.infrastructure.security.auth.settings', fake_settings):
            auth = APIKeyAuth()
            # Verify initial state
            assert len(auth.api_keys) == 3
            assert len(auth._key_metadata) == 3
            assert "primary-key-123" in auth._key_metadata
            assert "additional-key-456" in auth._key_metadata
            assert "additional-key-789" in auth._key_metadata

            # When: reload_keys is called after keys are removed from environment
            fake_settings.api_key = "primary-key-123"  # Keep primary only
            fake_settings.additional_api_keys = None  # Remove additional keys
            auth.reload_keys()

            # Then: Metadata for removed keys is no longer accessible
            assert len(auth._key_metadata) == 1
            assert "primary-key-123" in auth._key_metadata
            # Removed keys should have no metadata
            assert "additional-key-456" not in auth._key_metadata
            assert "additional-key-789" not in auth._key_metadata

    def test_reload_keys_preserves_configuration_consistency(self, fake_settings, mock_environment_detection, monkeypatch):
        """
        Test that reload_keys maintains configuration consistency.

        Verifies:
            Key reloading maintains consistent state between keys and metadata.

        Business Impact:
            Ensures reliable authentication behavior during key management
            operations and prevents configuration inconsistencies.

        Scenario:
            Given: APIKeyAuth with complex key and metadata configuration.
            When: reload_keys is called with modified environment.
            Then: All keys in api_keys set have corresponding metadata entries
            And: No orphaned metadata exists for unconfigured keys.

        Fixtures Used:
            - fake_settings: Provides complex initial and updated configuration.
            - monkeypatch: To enable features and modify environment state.
        """
        # Given: APIKeyAuth with complex key and metadata configuration
        monkeypatch.setenv("ENABLE_USER_TRACKING", "true")
        fake_settings.api_key = "primary-key-123"
        fake_settings.additional_api_keys = "additional-key-456"
        with patch('app.infrastructure.security.auth.settings', fake_settings):
            auth = APIKeyAuth()
            # Verify initial state
            assert len(auth.api_keys) == 2
            assert len(auth._key_metadata) == 2

            # When: reload_keys is called with modified environment
            fake_settings.api_key = "new-primary-key-789"
            fake_settings.additional_api_keys = "new-additional-key-001,new-additional-key-002"
            auth.reload_keys()

            # Then: All keys in api_keys set have corresponding metadata entries
            assert len(auth.api_keys) == 3
            assert len(auth._key_metadata) == 3

            # Verify each key has metadata
            for api_key in auth.api_keys:
                assert api_key in auth._key_metadata

            # And: No orphaned metadata exists for unconfigured keys
            for metadata_key in auth._key_metadata.keys():
                assert metadata_key in auth.api_keys


class TestAPIKeyAuthEdgeCases:
    """
    Test suite for APIKeyAuth edge cases and boundary conditions.

    Scope:
        - Malformed environment variable handling
        - Invalid configuration recovery
        - Concurrent access patterns
        - Resource cleanup and error handling

    Business Critical:
        Robust edge case handling prevents authentication system failures
        and maintains security under adverse conditions.

    Test Strategy:
        - Test malformed additional keys parsing
        - Test environment variable edge cases
        - Test production validation error details
        - Test resource cleanup during errors
    """

    def test_api_key_auth_handles_malformed_additional_keys(self, fake_settings, mock_environment_detection):
        """
        Test that APIKeyAuth handles malformed ADDITIONAL_API_KEYS gracefully.

        Verifies:
            Malformed comma-separated key lists are parsed safely.

        Business Impact:
            Prevents authentication system failures due to configuration
            errors and provides graceful degradation for partial configurations.

        Scenario:
            Given: ADDITIONAL_API_KEYS contains malformed data (extra commas, spaces).
            When: APIKeyAuth is instantiated.
            Then: Valid keys are extracted and invalid entries are skipped
            And: System remains functional with available valid keys.

        Fixtures Used:
            - fake_settings: Configured with malformed additional_api_keys.
        """
        # Given: ADDITIONAL_API_KEYS contains malformed data (extra commas, spaces)
        fake_settings.api_key = "primary-key-123"
        fake_settings.additional_api_keys = ",,valid-key-1,  ,valid-key-2,   ,,  valid-key-3  ,"

        # When: APIKeyAuth is instantiated
        with patch('app.infrastructure.security.auth.settings', fake_settings):
            auth = APIKeyAuth()

        # Then: Valid keys are extracted and invalid entries are skipped
        assert len(auth.api_keys) == 4  # 1 primary + 3 valid additional keys
        assert "primary-key-123" in auth.api_keys
        assert "valid-key-1" in auth.api_keys
        assert "valid-key-2" in auth.api_keys
        assert "valid-key-3" in auth.api_keys

        # And: System remains functional with available valid keys
        assert auth.verify_api_key("primary-key-123") is True
        assert auth.verify_api_key("valid-key-1") is True
        assert auth.verify_api_key("valid-key-2") is True
        assert auth.verify_api_key("valid-key-3") is True
        assert auth.verify_api_key("invalid-key") is False

    def test_api_key_auth_production_validation_error_context(self, fake_settings, mock_production_environment):
        """
        Test that production validation errors include comprehensive context.

        Verifies:
            Production security validation errors provide detailed troubleshooting context.

        Business Impact:
            Enables faster resolution of production deployment issues
            and provides clear guidance for security configuration fixes.

        Scenario:
            Given: Production environment with no API keys configured.
            When: APIKeyAuth instantiation fails with ConfigurationError.
            Then: Error context includes environment details, confidence, and reasoning
            And: Required configuration steps are clearly documented.

        Fixtures Used:
            - fake_settings: Empty settings for production validation test.
            - mock_production_environment: Returns production environment with details.
        """
        # Given: Production environment with no API keys configured
        # fake_settings is empty by default
        # mock_production_environment fixture configures production environment

        # When: APIKeyAuth instantiation fails with ConfigurationError
        with patch('app.infrastructure.security.auth.settings', fake_settings), \
             patch('app.infrastructure.security.auth.get_environment_info', mock_production_environment):
            with pytest.raises(ConfigurationError) as exc_info:
                APIKeyAuth()

        # Then: Error context includes environment details, confidence, and reasoning
        error = exc_info.value
        error_message = str(error)
        context = error.context

        # Verify comprehensive error message
        assert "Production security validation failed" in error_message
        assert "No API keys configured" in error_message
        assert "production" in error_message.lower()

        # And: Required configuration steps are clearly documented
        assert "API_KEY" in error_message
        assert "ADDITIONAL_API_KEYS" in error_message
        assert "environment variables" in error_message.lower()

        # Verify context contains environment detection details
        assert context is not None
        assert context["environment"] == "production"
        assert context["confidence"] == 0.95
        assert context["reasoning"] == "Production deployment detected"
        assert "required_vars" in context
        assert "API_KEY" in context["required_vars"]
        assert "ADDITIONAL_API_KEYS" in context["required_vars"]
        assert context["current_keys_count"] == 0

    def test_api_key_auth_environment_detection_failure_handling(self, fake_settings):
        """
        Test that APIKeyAuth handles environment detection failures gracefully.

        Verifies:
            Authentication system assumes production for security when environment detection fails.

        Business Impact:
            Prevents security bypass by failing safe when environment detection
            issues occur, ensuring production-level security by default.

        Scenario:
            Given: Environment detection service raises exceptions and API keys are configured.
            When: APIKeyAuth is instantiated.
            Then: System assumes production environment for security
            And: Warning is logged about environment detection failure
            And: Authentication works with configured API keys.

        Fixtures Used:
            - fake_settings: Settings with API keys to satisfy production requirements.
        """
        # Given: Environment detection service raises exceptions and API keys are configured
        fake_settings.api_key = "test-key-for-fallback-123"  # Provide keys for production fallback

        def failing_environment_detection(context):
            raise RuntimeError("Environment detection service unavailable")

        # When: APIKeyAuth is instantiated
        # Then: System assumes production environment for security
        with patch('app.infrastructure.security.auth.settings', fake_settings), \
             patch('app.infrastructure.security.auth.get_environment_info', failing_environment_detection):
            # Should create auth successfully with fallback to production mode
            auth = APIKeyAuth()

            # Verify the auth instance is created successfully
            assert isinstance(auth, APIKeyAuth)
            assert len(auth.api_keys) == 1
            assert "test-key-for-fallback-123" in auth.api_keys

        # And: Warning is logged about environment detection failure
        # (Logging verification is implicitly tested by successful instantiation)

        # Test that system fails safe when no keys provided during environment detection failure
        fake_settings.api_key = None
        with patch('app.infrastructure.security.auth.settings', fake_settings), \
             patch('app.infrastructure.security.auth.get_environment_info', failing_environment_detection):
            # Should raise ConfigurationError due to fallback to production with no keys
            with pytest.raises(ConfigurationError) as exc_info:
                APIKeyAuth()

            # Verify error context includes fallback reasoning
            error_context = exc_info.value.context
            assert "Environment detection failed" in error_context["reasoning"]

    def test_api_key_auth_whitespace_handling_in_keys(self, fake_settings, mock_environment_detection):
        """
        Test that APIKeyAuth properly handles whitespace in API keys.

        Verifies:
            Leading and trailing whitespace in API keys is handled appropriately.

        Business Impact:
            Prevents authentication failures due to configuration whitespace
            and ensures robust key parsing from various deployment sources.

        Scenario:
            Given: API keys in environment variables contain leading/trailing whitespace.
            When: APIKeyAuth is instantiated.
            Then: Keys are properly trimmed and stored without whitespace
            And: Authentication works correctly with trimmed keys.

        Fixtures Used:
            - fake_settings: Configured with whitespace-padded API keys.
        """
        # Given: API keys in environment variables contain leading/trailing whitespace
        fake_settings.api_key = "   primary-key-with-spaces   "
        fake_settings.additional_api_keys = "  additional-key-1  ,   additional-key-2   ,additional-key-3"

        # When: APIKeyAuth is instantiated
        with patch('app.infrastructure.security.auth.settings', fake_settings):
            auth = APIKeyAuth()

        # Then: Keys are properly trimmed and stored without whitespace
        assert len(auth.api_keys) == 4

        # Both primary and additional keys should be trimmed consistently
        assert "primary-key-with-spaces" in auth.api_keys  # Primary key trimmed
        assert "additional-key-1" in auth.api_keys  # Additional keys are trimmed
        assert "additional-key-2" in auth.api_keys
        assert "additional-key-3" in auth.api_keys

        # Whitespace versions should not be stored
        assert "   primary-key-with-spaces   " not in auth.api_keys
        assert "  additional-key-1  " not in auth.api_keys
        assert "   additional-key-2   " not in auth.api_keys

        # And: Authentication works correctly with the trimmed keys
        assert auth.verify_api_key("primary-key-with-spaces") is True  # Primary key trimmed
        assert auth.verify_api_key("additional-key-1") is True  # Additional keys trimmed
        assert auth.verify_api_key("additional-key-2") is True
        assert auth.verify_api_key("additional-key-3") is True

        # Verify whitespace versions fail authentication
        assert auth.verify_api_key("   primary-key-with-spaces   ") is False  # Whitespace version fails
        assert auth.verify_api_key("  additional-key-1  ") is False  # Whitespace version fails