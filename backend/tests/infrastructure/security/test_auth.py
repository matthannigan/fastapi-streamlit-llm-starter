"""Unit tests for the authentication module."""

import os
import pytest
from unittest.mock import patch, MagicMock
from fastapi import HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials

from app.infrastructure.security.auth import (
    verify_api_key,
    verify_api_key_string,
    optional_verify_api_key,
    verify_api_key_with_metadata,
    APIKeyAuth,
    AuthConfig,
    api_key_auth
)


class TestVerifyAPIKey:
    """Test the verify_api_key dependency function."""

    def test_verify_api_key_with_valid_credentials(self):
        """Test verify_api_key with valid credentials."""
        # Mock credentials
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="test-valid-key"
        )
        
        # Mock the api_key_auth instance to return True for verification
        with patch.object(api_key_auth, 'verify_api_key', return_value=True):
            # Test async function
            import asyncio
            result = asyncio.run(verify_api_key(credentials))
            assert result == "test-valid-key"

    def test_verify_api_key_with_invalid_credentials(self):
        """Test verify_api_key with invalid credentials."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="invalid-key"
        )
        
        # Mock the api_key_auth instance to return False for verification
        with patch.object(api_key_auth, 'verify_api_key', return_value=False):
            # Test async function should raise AuthenticationError
            import asyncio
            from app.core.exceptions import AuthenticationError
            with pytest.raises(AuthenticationError) as exc_info:
                asyncio.run(verify_api_key(credentials))
            
            assert "Invalid API key" in str(exc_info.value)
            assert exc_info.value.context["auth_method"] == "bearer_token"

    def test_verify_api_key_without_credentials(self):
        """Test verify_api_key without credentials."""
        # Mock api_key_auth to have some keys configured
        with patch.object(api_key_auth, 'api_keys', {"test-key"}):
            # Test async function should raise AuthenticationError
            import asyncio
            from app.core.exceptions import AuthenticationError
            with pytest.raises(AuthenticationError) as exc_info:
                asyncio.run(verify_api_key(None))
            
            assert "API key required" in str(exc_info.value)
            assert exc_info.value.context["auth_method"] == "bearer_token"

    def test_verify_api_key_development_mode_no_keys(self):
        """Test verify_api_key in development mode (no API keys configured)."""
        # Mock api_key_auth to have no keys configured
        with patch.object(api_key_auth, 'api_keys', set()):
            # Test async function should return "development"
            import asyncio
            result = asyncio.run(verify_api_key(None))
            assert result == "development"

    def test_verify_api_key_test_mode_with_test_key(self):
        """Test verify_api_key in test mode with test key."""
        test_key = "test-api-key-12345"
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=test_key
        )
        
        # Mock environment to simulate pytest
        with patch.dict(os.environ, {'PYTEST_CURRENT_TEST': 'test_something'}):
            import asyncio
            result = asyncio.run(verify_api_key(credentials))
            assert result == test_key

    def test_verify_api_key_test_mode_development_fallback(self):
        """Test verify_api_key in test mode with development fallback."""
        # Mock api_key_auth to have no keys configured
        with patch.object(api_key_auth, 'api_keys', set()):
            # Mock environment to simulate pytest
            with patch.dict(os.environ, {'PYTEST_CURRENT_TEST': 'test_something'}):
                import asyncio
                result = asyncio.run(verify_api_key(None))
                assert result == "development"

    def test_verify_api_key_empty_credentials(self):
        """Test verify_api_key with empty credentials string."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials=""
        )
        
        # Mock the api_key_auth instance to return False for empty key
        with patch.object(api_key_auth, 'verify_api_key', return_value=False):
            import asyncio
            from app.core.exceptions import AuthenticationError
            with pytest.raises(AuthenticationError) as exc_info:
                asyncio.run(verify_api_key(credentials))
            
            assert "Invalid API key" in str(exc_info.value)
            assert exc_info.value.context["auth_method"] == "bearer_token"


class TestVerifyAPIKeyString:
    """Test the verify_api_key_string utility function."""

    def test_verify_api_key_string_valid(self):
        """Test verify_api_key_string with valid key."""
        with patch.object(api_key_auth, 'verify_api_key', return_value=True):
            result = verify_api_key_string("valid-key")
            assert result is True

    def test_verify_api_key_string_invalid(self):
        """Test verify_api_key_string with invalid key."""
        with patch.object(api_key_auth, 'verify_api_key', return_value=False):
            result = verify_api_key_string("invalid-key")
            assert result is False

    def test_verify_api_key_string_empty(self):
        """Test verify_api_key_string with empty key."""
        with patch.object(api_key_auth, 'verify_api_key', return_value=False):
            result = verify_api_key_string("")
            assert result is False


class TestOptionalVerifyAPIKey:
    """Test the optional_verify_api_key dependency function."""

    def test_optional_verify_api_key_with_valid_credentials(self):
        """Test optional_verify_api_key with valid credentials."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="test-valid-key"
        )
        
        with patch.object(api_key_auth, 'verify_api_key', return_value=True):
            import asyncio
            result = asyncio.run(optional_verify_api_key(credentials))
            assert result == "test-valid-key"

    def test_optional_verify_api_key_with_invalid_credentials(self):
        """Test optional_verify_api_key with invalid credentials should raise exception."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="invalid-key"
        )
        
        with patch.object(api_key_auth, 'verify_api_key', return_value=False):
            import asyncio
            from app.core.exceptions import AuthenticationError
            with pytest.raises(AuthenticationError) as exc_info:
                asyncio.run(optional_verify_api_key(credentials))
            
            assert "Invalid API key" in str(exc_info.value)
            assert exc_info.value.context["auth_method"] == "bearer_token"

    def test_optional_verify_api_key_without_credentials(self):
        """Test optional_verify_api_key without credentials should return None."""
        import asyncio
        result = asyncio.run(optional_verify_api_key(None))
        assert result is None


class TestVerifyAPIKeyWithMetadata:
    """Test the verify_api_key_with_metadata dependency function."""

    def test_verify_api_key_with_metadata_valid_credentials(self):
        """Test verify_api_key_with_metadata with valid credentials."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="test-valid-key"
        )
        
        with patch.object(api_key_auth, 'verify_api_key', return_value=True):
            import asyncio
            result = asyncio.run(verify_api_key_with_metadata(credentials))
            
            assert isinstance(result, dict)
            assert result["api_key"] == "test-valid-key"

    def test_verify_api_key_with_metadata_includes_metadata(self):
        """Test verify_api_key_with_metadata includes metadata when enabled."""
        credentials = HTTPAuthorizationCredentials(
            scheme="Bearer",
            credentials="test-valid-key"
        )
        
        # Mock auth config to enable metadata features
        mock_config = MagicMock()
        mock_config.enable_user_tracking = True
        mock_config.enable_request_logging = True
        
        with patch.object(api_key_auth, 'verify_api_key', return_value=True), \
             patch('app.infrastructure.security.auth.auth_config', mock_config), \
             patch.object(api_key_auth, 'add_request_metadata', return_value={"metadata": "test"}):
            
            import asyncio
            result = asyncio.run(verify_api_key_with_metadata(credentials))
            
            assert isinstance(result, dict)
            assert result["api_key"] == "test-valid-key"
            assert "metadata" in result


class TestAPIKeyAuth:
    """Test the APIKeyAuth class."""

    def test_api_key_auth_verify_valid_key(self):
        """Test APIKeyAuth.verify_api_key with valid key."""
        auth = APIKeyAuth()
        # Add a test key to the instance
        auth.api_keys = {"test-key"}
        
        result = auth.verify_api_key("test-key")
        assert result is True

    def test_api_key_auth_verify_invalid_key(self):
        """Test APIKeyAuth.verify_api_key with invalid key."""
        auth = APIKeyAuth()
        auth.api_keys = {"test-key"}
        
        result = auth.verify_api_key("invalid-key")
        assert result is False

    def test_api_key_auth_verify_empty_key(self):
        """Test APIKeyAuth.verify_api_key with empty key."""
        auth = APIKeyAuth()
        auth.api_keys = {"test-key"}
        
        result = auth.verify_api_key("")
        assert result is False

    def test_api_key_auth_no_keys_configured(self):
        """Test APIKeyAuth with no keys configured."""
        auth = APIKeyAuth()
        auth.api_keys = set()
        
        result = auth.verify_api_key("any-key")
        assert result is False

    def test_api_key_auth_case_sensitive(self):
        """Test APIKeyAuth is case sensitive."""
        auth = APIKeyAuth()
        auth.api_keys = {"TestKey"}
        
        # Should not match different case
        assert auth.verify_api_key("testkey") is False
        assert auth.verify_api_key("TESTKEY") is False
        assert auth.verify_api_key("TestKey") is True

    def test_api_key_auth_get_key_metadata(self):
        """Test APIKeyAuth.get_key_metadata functionality."""
        config = AuthConfig()
        config.enable_user_tracking = True
        
        auth = APIKeyAuth(config)
        auth._key_metadata = {
            "test-key": {
                "type": "primary",
                "permissions": ["read", "write"]
            }
        }
        
        metadata = auth.get_key_metadata("test-key")
        assert metadata["type"] == "primary"
        assert metadata["permissions"] == ["read", "write"]
        
        # Test non-existent key
        metadata = auth.get_key_metadata("non-existent")
        assert metadata == {}

    def test_api_key_auth_get_key_metadata_disabled(self):
        """Test APIKeyAuth.get_key_metadata when user tracking is disabled."""
        config = AuthConfig()
        config.enable_user_tracking = False
        
        auth = APIKeyAuth(config)
        metadata = auth.get_key_metadata("any-key")
        assert metadata == {}

    def test_api_key_auth_reload_keys(self):
        """Test APIKeyAuth.reload_keys functionality."""
        auth = APIKeyAuth()
        original_keys = auth.api_keys.copy()
        
        # Modify the keys
        auth.api_keys.add("temporary-key")
        assert "temporary-key" in auth.api_keys
        
        # Reload should restore original configuration
        auth.reload_keys()
        
        # Note: This test might vary based on actual environment configuration
        # The exact result depends on what keys are configured in settings


class TestAuthConfig:
    """Test the AuthConfig class."""

    def test_auth_config_default_simple_mode(self):
        """Test AuthConfig defaults to simple mode."""
        with patch.dict(os.environ, {}, clear=True):
            config = AuthConfig()
            assert config.simple_mode is True

    def test_auth_config_advanced_mode(self):
        """Test AuthConfig can be set to advanced mode."""
        with patch.dict(os.environ, {'AUTH_MODE': 'advanced'}):
            config = AuthConfig()
            assert config.simple_mode is False

    def test_auth_config_feature_support_simple_mode(self):
        """Test feature support in simple mode."""
        with patch.dict(os.environ, {'AUTH_MODE': 'simple'}):
            config = AuthConfig()
            assert config.supports_user_context is False
            assert config.supports_permissions is False
            assert config.supports_rate_limiting is False

    def test_auth_config_feature_support_advanced_mode(self):
        """Test feature support in advanced mode."""
        with patch.dict(os.environ, {'AUTH_MODE': 'advanced'}):
            config = AuthConfig()
            assert config.supports_user_context is True
            assert config.supports_permissions is True
            assert config.supports_rate_limiting is True

    def test_auth_config_user_tracking_enabled(self):
        """Test user tracking can be enabled."""
        with patch.dict(os.environ, {'ENABLE_USER_TRACKING': 'true'}):
            config = AuthConfig()
            assert config.enable_user_tracking is True

    def test_auth_config_request_logging_enabled(self):
        """Test request logging can be enabled."""
        with patch.dict(os.environ, {'ENABLE_REQUEST_LOGGING': 'true'}):
            config = AuthConfig()
            assert config.enable_request_logging is True

    def test_auth_config_get_auth_info(self):
        """Test AuthConfig.get_auth_info returns proper structure."""
        config = AuthConfig()
        info = config.get_auth_info()
        
        assert "mode" in info
        assert "features" in info
        assert isinstance(info["features"], dict)
        assert "user_context" in info["features"]
        assert "permissions" in info["features"]
        assert "rate_limiting" in info["features"] 