"""
Infrastructure-specific fixtures for testing.

This module provides shared fixtures used across multiple test modules including
encryption, startup, and other infrastructure components.

Fixture Categories:
    - Settings fixtures (test_settings, development_settings, production_settings)
    - Encryption key fixtures (valid_fernet_key, invalid keys, empty key)
    - Mock logger fixtures (mock_logger)
    - Cryptography availability fixtures (mock_cryptography_unavailable)
"""
import pytest
from unittest.mock import patch, Mock, MagicMock
import hashlib
from typing import Dict, Any, Optional


@pytest.fixture
def mock_infrastructure_config():
    """Mock configuration for infrastructure components."""
    return {
        "cache_enabled": True,
        "resilience_enabled": True,
        "monitoring_enabled": True
    }

# =============================================================================
# Mock Settings Fixtures
# =============================================================================

@pytest.fixture
def test_settings():
    """
    Real Settings instance with test configuration for testing actual configuration behavior.
    
    Provides a Settings instance loaded from test configuration, enabling tests
    to verify actual configuration loading, validation, and environment detection
    instead of using hardcoded mock values.
    
    This fixture represents behavior-driven testing where we test the actual
    Settings class functionality rather than mocking its behavior.
    """
    import tempfile
    import json
    import os
    from app.core.config import Settings
    
    # Create test configuration with realistic values
    test_config = {
        "gemini_api_key": "test-gemini-api-key-12345",
        "ai_model": "gemini-2.0-flash-exp", 
        "ai_temperature": 0.7,
        "host": "0.0.0.0",
        "port": 8000,
        "api_key": "test-api-key-12345",
        "additional_api_keys": "key1,key2,key3",
        "debug": False,
        "log_level": "INFO",
        "cache_preset": "development",
        "resilience_preset": "simple",
        "health_check_timeout_ms": 2000
    }
    
    # Create temporary config file
    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        json.dump(test_config, f, indent=2)
        config_file = f.name
    
    try:
        # Create Settings instance with test config
        # Override environment variables to ensure test isolation
        test_env = {
            "GEMINI_API_KEY": "test-gemini-api-key-12345",
            "API_KEY": "test-api-key-12345",
            "CACHE_PRESET": "development",
            "RESILIENCE_PRESET": "simple"
        }
        
        # Temporarily set test environment variables
        original_env = {}
        for key, value in test_env.items():
            original_env[key] = os.environ.get(key)
            os.environ[key] = value
        
        # Create real Settings instance
        settings = Settings()
        
        # Restore original environment
        for key, original_value in original_env.items():
            if original_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original_value
        
        return settings
        
    finally:
        # Clean up temporary config file
        os.unlink(config_file)


@pytest.fixture
def development_settings():
    """
    Real Settings instance configured for development environment testing.
    
    Provides Settings with development preset for testing development-specific behavior.
    """
    import os
    
    # Set development environment variables
    test_env = {
        "GEMINI_API_KEY": "test-dev-api-key",
        "API_KEY": "test-dev-api-key", 
        "CACHE_PRESET": "development",
        "RESILIENCE_PRESET": "development",
        "DEBUG": "true"
    }
    
    original_env = {}
    for key, value in test_env.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value
        
    try:
        from app.core.config import Settings
        settings = Settings()
        yield settings
    finally:
        # Restore environment
        for key, original_value in original_env.items():
            if original_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original_value


@pytest.fixture
def production_settings():
    """
    Real Settings instance configured for production environment testing.

    Provides Settings with production preset for testing production-specific behavior.
    """
    import os

    # Set production environment variables
    test_env = {
        "GEMINI_API_KEY": "test-prod-api-key",
        "API_KEY": "test-prod-api-key",
        "CACHE_PRESET": "production",
        "RESILIENCE_PRESET": "production",
        "DEBUG": "false"
    }

    original_env = {}
    for key, value in test_env.items():
        original_env[key] = os.environ.get(key)
        os.environ[key] = value

    try:
        from app.core.config import Settings
        settings = Settings()
        yield settings
    finally:
        # Restore environment
        for key, original_value in original_env.items():
            if original_value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = original_value


# =============================================================================
# Shared Encryption Key Fixtures (Used by encryption and startup modules)
# =============================================================================


@pytest.fixture
def valid_fernet_key():
    """
    Valid Fernet encryption key for testing encryption functionality.

    Provides a properly formatted base64-encoded Fernet key (44 characters)
    that can be used across any module testing encryption behavior.

    Returns:
        Base64-encoded Fernet key as string

    Use Cases:
        - Testing encryption initialization (cache encryption module)
        - Testing encryption key validation (startup security module)
        - Testing encryption/decryption operations
        - Cross-module encryption testing

    Example:
        def test_encryption_with_valid_key(valid_fernet_key):
            encryption = EncryptedCacheLayer(encryption_key=valid_fernet_key)
            assert encryption.is_enabled is True

    Note:
        This is a real Fernet key generated for testing only.
        Do NOT use in production.
    """
    try:
        from cryptography.fernet import Fernet
        return Fernet.generate_key().decode()
    except ImportError:
        # Fallback to static test key if cryptography not available
        return "dGVzdC1rZXktMzItYnl0ZXMtbG9uZyEhISEhISEhISEhIQ=="


@pytest.fixture
def invalid_fernet_key_short():
    """
    Invalid encryption key (too short) for testing error handling.

    Provides a key that's too short to be a valid Fernet key (< 44 chars)
    for testing key length validation across modules.

    Returns:
        String that's too short to be a valid Fernet key

    Use Cases:
        - Testing key length validation in encryption module
        - Testing key validation in startup security module
        - Testing ConfigurationError raising
        - Testing error messages for invalid keys

    Example:
        def test_rejects_short_key(invalid_fernet_key_short):
            with pytest.raises(ConfigurationError):
                EncryptedCacheLayer(encryption_key=invalid_fernet_key_short)
    """
    return "too-short-key"


@pytest.fixture
def invalid_fernet_key_format():
    """
    Invalid encryption key (wrong format) for testing base64 validation.

    Provides a 44-character string that isn't valid base64 encoding
    for testing format validation logic.

    Returns:
        44-character string that isn't valid base64

    Use Cases:
        - Testing key format validation
        - Testing base64 decoding errors
        - Testing error message clarity
        - Cross-module format validation testing

    Example:
        def test_rejects_invalid_format(invalid_fernet_key_format):
            with pytest.raises(ConfigurationError):
                validator.validate_encryption_key(invalid_fernet_key_format)
    """
    return "!" * 44  # 44 chars but invalid base64


@pytest.fixture
def empty_encryption_key():
    """
    None encryption key for testing disabled encryption scenarios.

    Returns None to simulate missing or disabled encryption configuration
    for testing graceful degradation and warning generation.

    Returns:
        None (no encryption key)

    Use Cases:
        - Testing disabled encryption behavior in cache module
        - Testing missing encryption key handling in startup module
        - Testing warning message generation
        - Testing development mode flexibility

    Example:
        def test_encryption_disabled_without_key(empty_encryption_key):
            encryption = EncryptedCacheLayer(encryption_key=empty_encryption_key)
            assert encryption.is_enabled is False
    """
    return None


# =============================================================================
# Shared Mock Logger Fixture (System Boundary)
# =============================================================================


@pytest.fixture
def mock_logger():
    """
    Mock logger for testing logging behavior across all modules.

    Provides a spec'd mock logger that simulates logging.Logger
    for testing log message generation without actual I/O. Used by
    encryption, startup, and other infrastructure modules.

    Default Behavior:
        - All log methods available (info, warning, error, debug)
        - No actual logging output (mocked)
        - Can be configured per-test for specific scenarios

    Use Cases:
        - Testing log messages in cache encryption module
        - Testing log messages in startup validation module
        - Testing warning/error logging across infrastructure
        - Any module needing to test logging behavior

    Test Customization:
        def test_logs_warning(mock_logger, monkeypatch):
            monkeypatch.setattr('app.some.module.logger', mock_logger)
            # Test code that logs
            mock_logger.warning.assert_called()

    Example:
        def test_encryption_logs_warning(mock_logger, monkeypatch):
            monkeypatch.setattr('app.infrastructure.cache.encryption.logger', mock_logger)
            encryption = EncryptedCacheLayer(encryption_key=None)
            mock_logger.warning.assert_called()

    Note:
        This is a proper system boundary mock - logger performs I/O
        and should not be tested as part of unit tests. Mocking at
        this boundary is appropriate for all modules.
    """
    mock = MagicMock()
    mock.info = Mock()
    mock.warning = Mock()
    mock.error = Mock()
    mock.debug = Mock()
    return mock


# =============================================================================
# Shared Cryptography Library Availability Fixture
# =============================================================================


@pytest.fixture
def mock_cryptography_unavailable(monkeypatch):
    """
    ⚠️ DEPRECATED: Do not use this fixture for new unit tests.

    This fixture attempts to mock cryptography library unavailability but has
    fundamental limitations at the unit test level. It is kept for backwards
    compatibility but should NOT be used for new tests.

    ❌ Why This Fixture Should NOT Be Used for Unit Tests:

    1. **Import-Time Loading Issue**: Cryptography is imported at module load
       time, before test fixtures run. The fixture cannot prevent imports that
       have already occurred.

    2. **Limited Effectiveness**: sys.modules patching doesn't prevent the
       cryptography library from being available when modules import it during
       test collection.

    3. **Test Isolation**: Proper testing of missing library scenarios requires
       an environment where cryptography is actually not installed.

    ✅ Recommended Approach - Integration Tests:

    For testing missing cryptography library scenarios, use integration tests
    with an actual environment where cryptography is not installed:

        # See: tests/integration/startup/TEST_PLAN_cryptography_unavailable.md
        # Use Docker, virtualenv, or tox to create environment without cryptography

    Previous Use Cases (Now Migrated to Integration Tests):
        ❌ Testing encryption initialization without cryptography
        ❌ Testing startup validation without cryptography
        ❌ Testing graceful failure modes and error messages
        ❌ Testing warning messages for missing dependencies

    Migration Guide:
        All tests using this fixture have been marked as skipped with references
        to the integration test plan at:
        tests/integration/startup/TEST_PLAN_cryptography_unavailable.md

    Implementation Note:
        This fixture uses sys.modules patching which is safer than patching
        builtins.__import__ (avoids pytest internal errors), but still cannot
        properly simulate missing libraries at unit test level.

    Status:
        - DEPRECATED for unit tests
        - Kept for backwards compatibility only
        - See integration test plan for proper implementation approach
    """
    import sys

    # Store original cryptography modules if they exist
    original_cryptography = sys.modules.get('cryptography')
    original_fernet = sys.modules.get('cryptography.fernet')

    # Remove cryptography modules from sys.modules to simulate unavailability
    if 'cryptography' in sys.modules:
        del sys.modules['cryptography']
    if 'cryptography.fernet' in sys.modules:
        del sys.modules['cryptography.fernet']

    # Patch the encryption module's Fernet import to raise ImportError
    def mock_fernet_import():
        raise ImportError("No module named 'cryptography'")

    # This will cause imports of cryptography to fail
    monkeypatch.setitem(sys.modules, 'cryptography.fernet', None)

    yield

    # Restore original state after test
    if original_cryptography is not None:
        sys.modules['cryptography'] = original_cryptography
    elif 'cryptography' in sys.modules:
        del sys.modules['cryptography']

    if original_fernet is not None:
        sys.modules['cryptography.fernet'] = original_fernet
    elif 'cryptography.fernet' in sys.modules:
        del sys.modules['cryptography.fernet']
