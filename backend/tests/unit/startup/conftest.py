"""
Test fixtures for startup module unit tests.

This module provides reusable fixtures for testing the startup module following
behavior-driven testing principles. Fixtures provide test doubles (Fakes and Mocks)
for external dependencies while keeping internal startup components real.

Fixture Categories:
    - Environment detection fixtures (Mock)
    - TLS certificate fixtures (Fake filesystem + real Path objects)
    - Encryption key fixtures (test data)
    - Redis URL fixtures (test data)
    - Logger fixtures (Mock at I/O boundary)

Design Philosophy:
    - Prefer Fakes over Mocks for stateful behavior
    - Mock only at system boundaries (logging, environment variables, filesystem)
    - Fixtures represent 'happy path' behavior by default
    - Error scenarios configured within individual tests
"""

import pytest
from pathlib import Path
from typing import Any, Dict, Optional
from unittest.mock import Mock, MagicMock, patch
from datetime import datetime, timedelta

# Real imports from the same application (not mocked)
from app.core.exceptions import ConfigurationError
from app.core.environment import Environment, FeatureContext


# =============================================================================
# Fake Environment Info Implementation (Preferred over Mock)
# =============================================================================


class FakeEnvironmentInfo:
    """
    Fake environment information for testing environment-aware behavior.

    Provides a lightweight implementation that simulates the EnvironmentInfo
    contract returned by get_environment_info() without complex initialization.

    Behavior:
        - Configurable environment type (development, staging, production)
        - Configurable confidence level (0.0-1.0)
        - Configurable reasoning string
        - Stateless - immutable after creation
        - Matches EnvironmentInfo interface exactly

    Usage:
        fake_env = FakeEnvironmentInfo(
            environment=Environment.PRODUCTION,
            confidence=0.95,
            reasoning="Production indicators detected"
        )
        assert fake_env.environment == Environment.PRODUCTION

    Note:
        This Fake is preferred over mocking get_environment_info() because
        it provides realistic, stateful behavior that matches the real
        EnvironmentInfo contract.
    """

    def __init__(
        self,
        environment: Environment = Environment.DEVELOPMENT,
        confidence: float = 0.90,
        reasoning: str = "Test environment detection",
    ):
        """
        Initialize fake environment info.

        Args:
            environment: Environment type to simulate
            confidence: Detection confidence level (0.0-1.0)
            reasoning: Human-readable reasoning for detection
        """
        self.environment = environment
        self.confidence = confidence
        self.reasoning = reasoning


# =============================================================================
# Environment Detection Fixtures
# =============================================================================


@pytest.fixture
def mock_get_environment_info():
    """
    Mock for get_environment_info function with development default.

    Provides a spec'd mock that returns FakeEnvironmentInfo for development
    environment by default. Tests can customize the return value for different
    environment scenarios.

    Default Behavior:
        Returns FakeEnvironmentInfo with:
        - environment: Environment.DEVELOPMENT
        - confidence: 0.90
        - reasoning: "Development environment detected for testing"

    Use Cases:
        - Testing development mode behavior
        - Testing environment-specific validation
        - Testing security enforcement based on environment

    Test Customization:
        def test_production_security(mock_get_environment_info):
            # Configure for production environment
            mock_get_environment_info.return_value = FakeEnvironmentInfo(
                environment=Environment.PRODUCTION,
                confidence=0.95,
                reasoning="Production deployment detected"
            )
            # Test will see production environment

    Note:
        This is a proper system boundary mock - environment detection
        involves system introspection and should be mocked for testing.
    """
    mock = Mock()
    mock.return_value = FakeEnvironmentInfo(
        environment=Environment.DEVELOPMENT,
        confidence=0.90,
        reasoning="Development environment detected for testing",
    )
    return mock


@pytest.fixture
def fake_development_environment():
    """
    Pre-configured FakeEnvironmentInfo for development environment.

    Provides environment info representing a development environment
    with typical confidence level and reasoning.

    Returns:
        FakeEnvironmentInfo configured for development

    Use Cases:
        - Testing development mode security flexibility
        - Testing development-specific messaging
        - Testing TLS validation skipping in development
    """
    return FakeEnvironmentInfo(
        environment=Environment.DEVELOPMENT,
        confidence=0.90,
        reasoning="Development environment - local machine detected",
    )


@pytest.fixture
def fake_staging_environment():
    """
    Pre-configured FakeEnvironmentInfo for staging environment.

    Provides environment info representing a staging environment
    with typical confidence level and reasoning.

    Returns:
        FakeEnvironmentInfo configured for staging

    Use Cases:
        - Testing staging mode security requirements
        - Testing staging-specific messaging
        - Testing intermediate security enforcement
    """
    return FakeEnvironmentInfo(
        environment=Environment.STAGING,
        confidence=0.88,
        reasoning="Staging environment indicators found",
    )


@pytest.fixture
def fake_production_environment():
    """
    Pre-configured FakeEnvironmentInfo for production environment.

    Provides environment info representing a production environment
    with high confidence level and reasoning.

    Returns:
        FakeEnvironmentInfo configured for production

    Use Cases:
        - Testing production security enforcement
        - Testing mandatory TLS requirements
        - Testing production error messages
    """
    return FakeEnvironmentInfo(
        environment=Environment.PRODUCTION,
        confidence=0.95,
        reasoning="Production deployment detected - strict security enforced",
    )


# =============================================================================
# Redis URL Fixtures (Test Data)
# =============================================================================


@pytest.fixture
def secure_redis_url_tls():
    """
    Secure Redis URL using TLS encryption (rediss://).

    Returns:
        Redis URL string with TLS scheme

    Use Cases:
        - Testing secure connection validation
        - Testing TLS URL recognition
        - Testing production security compliance
    """
    return "rediss://redis.production.example.com:6380"


@pytest.fixture
def secure_redis_url_auth():
    """
    Secure Redis URL using authentication (redis:// with credentials).

    Returns:
        Redis URL string with embedded authentication

    Use Cases:
        - Testing authenticated connection validation
        - Testing credential parsing from URL
        - Testing alternative secure connection method
    """
    return "redis://user:strongpassword123456@redis.example.com:6379"


@pytest.fixture
def insecure_redis_url():
    """
    Insecure Redis URL without TLS or authentication.

    Returns:
        Redis URL string without security

    Use Cases:
        - Testing insecure connection detection
        - Testing production security enforcement
        - Testing ConfigurationError raising
    """
    return "redis://redis.internal.example.com:6379"


@pytest.fixture
def local_redis_url():
    """
    Local development Redis URL.

    Returns:
        Redis URL string for localhost

    Use Cases:
        - Testing development mode flexibility
        - Testing local development scenarios
        - Testing environment-specific validation
    """
    return "redis://localhost:6379"


@pytest.fixture
def redis_url_with_weak_password():
    """
    Redis URL with weak authentication password.

    Returns:
        Redis URL with short password

    Use Cases:
        - Testing password strength validation
        - Testing warning generation for weak passwords
        - Testing security recommendations
    """
    return "redis://user:weak@redis.example.com:6379"


@pytest.fixture
def malformed_redis_url():
    """
    Malformed Redis URL for error testing.

    Returns:
        Invalid Redis URL string

    Use Cases:
        - Testing URL parsing error handling
        - Testing validation robustness
        - Testing error message clarity
    """
    return "not-a-valid-url"


# =============================================================================
# TLS Certificate Fixtures (Fake Filesystem)
# =============================================================================


@pytest.fixture
def mock_cert_path_exists(tmp_path):
    """
    Creates temporary certificate files for testing TLS validation.

    Provides real Path objects pointing to temporary files that exist,
    enabling testing of certificate file validation without requiring
    actual production certificates.

    Returns:
        Dictionary with Path objects for cert, key, and CA files

    Behavior:
        - Creates temporary certificate files with realistic names
        - Files exist but contain placeholder content
        - Paths are cleaned up automatically after test

    Use Cases:
        - Testing certificate file existence validation
        - Testing certificate path resolution
        - Testing TLS configuration validation

    Example:
        def test_certificate_validation(mock_cert_path_exists):
            result = validator.validate_tls_certificates(
                cert_path=str(mock_cert_path_exists["cert"]),
                key_path=str(mock_cert_path_exists["key"]),
                ca_path=str(mock_cert_path_exists["ca"])
            )
            assert result["valid"] is True
    """
    cert_file = tmp_path / "client.crt"
    key_file = tmp_path / "client.key"
    ca_file = tmp_path / "ca.crt"

    # Create placeholder certificate files
    cert_file.write_text("-----BEGIN CERTIFICATE-----\nplaceholder\n-----END CERTIFICATE-----")
    key_file.write_text("-----BEGIN PRIVATE KEY-----\nplaceholder\n-----END PRIVATE KEY-----")
    ca_file.write_text("-----BEGIN CERTIFICATE-----\nplaceholder\n-----END CERTIFICATE-----")

    return {"cert": cert_file, "key": key_file, "ca": ca_file}


@pytest.fixture
def mock_cert_paths_missing():
    """
    Provides non-existent certificate paths for testing error handling.

    Returns:
        Dictionary with Path objects that don't exist

    Use Cases:
        - Testing missing certificate file detection
        - Testing error messages for missing files
        - Testing validation failure scenarios

    Example:
        def test_missing_certificates(mock_cert_paths_missing):
            result = validator.validate_tls_certificates(
                cert_path=str(mock_cert_paths_missing["cert"])
            )
            assert result["valid"] is False
            assert "not found" in result["errors"][0]
    """
    return {
        "cert": Path("/nonexistent/path/to/cert.pem"),
        "key": Path("/nonexistent/path/to/key.pem"),
        "ca": Path("/nonexistent/path/to/ca.pem"),
    }


@pytest.fixture
def mock_x509_certificate():
    """
    Mock x509 certificate for testing certificate parsing.

    Provides a mock certificate with configurable expiration dates
    and subject information for testing certificate validation logic.

    Default Behavior:
        - Certificate expires in 365 days (1 year)
        - Subject: CN=redis.example.com
        - Valid for testing expiration logic

    Use Cases:
        - Testing certificate expiration validation
        - Testing expiration warning generation
        - Testing certificate info extraction

    Test Customization:
        def test_expired_certificate(mock_x509_certificate):
            # Configure for expired certificate
            mock_x509_certificate.not_valid_after = datetime.utcnow() - timedelta(days=30)
            # Test will see expired certificate

    Note:
        This mocks cryptography.x509 certificate parsing, which is
        a system boundary (filesystem + parsing library).
    """
    mock_cert = MagicMock()

    # Set expiration to 365 days from now
    future_date = datetime.utcnow() + timedelta(days=365)
    mock_cert.not_valid_after = future_date
    mock_cert.not_valid_after_utc = future_date

    # Set subject information
    mock_subject = MagicMock()
    mock_subject.rfc4514_string.return_value = "CN=redis.example.com,O=TestOrg,C=US"
    mock_cert.subject = mock_subject

    return mock_cert


@pytest.fixture
def mock_expiring_certificate(mock_x509_certificate):
    """
    Pre-configured mock certificate expiring soon (30 days).

    Provides a certificate that will trigger expiration warnings
    for testing warning generation logic.

    Returns:
        Mock certificate expiring in 30 days

    Use Cases:
        - Testing expiration warning generation
        - Testing certificate renewal recommendations
        - Testing warning thresholds
    """
    near_future = datetime.utcnow() + timedelta(days=30)
    mock_x509_certificate.not_valid_after = near_future
    mock_x509_certificate.not_valid_after_utc = near_future
    return mock_x509_certificate


@pytest.fixture
def mock_expired_certificate(mock_x509_certificate):
    """
    Pre-configured mock certificate that has expired.

    Provides an expired certificate for testing error handling
    and validation failure scenarios.

    Returns:
        Mock certificate expired 30 days ago

    Use Cases:
        - Testing expired certificate detection
        - Testing validation failure for expired certs
        - Testing error message generation
    """
    past_date = datetime.utcnow() - timedelta(days=30)
    mock_x509_certificate.not_valid_after = past_date
    mock_x509_certificate.not_valid_after_utc = past_date
    return mock_x509_certificate


# =============================================================================
# Encryption Key Fixtures (Test Data)
# =============================================================================


@pytest.fixture
def valid_fernet_key():
    """
    Valid Fernet encryption key for testing encryption validation.

    Returns:
        44-character base64-encoded Fernet key

    Use Cases:
        - Testing encryption key validation
        - Testing key format verification
        - Testing encryption functionality

    Note:
        This is a real Fernet key generated for testing only.
        Do NOT use in production.
    """
    try:
        from cryptography.fernet import Fernet

        return Fernet.generate_key().decode()
    except ImportError:
        # Fallback if cryptography not available
        return "dGVzdC1rZXktMzItYnl0ZXMtbG9uZyEhISEhISEhISEhIQ=="


@pytest.fixture
def invalid_fernet_key_short():
    """
    Invalid encryption key (too short) for testing error handling.

    Returns:
        String that's too short to be a valid Fernet key

    Use Cases:
        - Testing key length validation
        - Testing validation error messages
        - Testing ConfigurationError raising
    """
    return "too-short-key"


@pytest.fixture
def invalid_fernet_key_format():
    """
    Invalid encryption key (wrong format) for testing error handling.

    Returns:
        44-character string that isn't valid base64

    Use Cases:
        - Testing key format validation
        - Testing base64 decoding errors
        - Testing error message clarity
    """
    return "!" * 44  # 44 chars but invalid base64


@pytest.fixture
def empty_encryption_key():
    """
    None encryption key for testing disabled encryption.

    Returns:
        None

    Use Cases:
        - Testing missing encryption key handling
        - Testing warning generation
        - Testing development mode flexibility
    """
    return None


# =============================================================================
# Real Validator Instances
# =============================================================================


@pytest.fixture
def redis_security_validator():
    """
    Real RedisSecurityValidator instance for testing validator behavior.

    Provides an actual validator instance to test real validation logic
    rather than mocking the validator's internal operations.

    Returns:
        RedisSecurityValidator instance

    Use Cases:
        - Testing validator initialization
        - Testing validation methods
        - Testing integration of validation logic

    Example:
        def test_validator_initialization(redis_security_validator):
            assert redis_security_validator is not None
            assert hasattr(redis_security_validator, 'logger')
    """
    from app.core.startup.redis_security import RedisSecurityValidator

    return RedisSecurityValidator()


# =============================================================================
# Mock Logger Fixtures (System Boundary)
# =============================================================================


@pytest.fixture
def mock_logger():
    """
    Mock logger for testing logging behavior.

    Provides a spec'd mock logger that simulates logging.Logger
    for testing log message generation without actual I/O.

    Default Behavior:
        - All log methods available (info, warning, error, debug)
        - No actual logging output (mocked)

    Use Cases:
        - Testing info messages for security status
        - Testing warning messages for insecure configurations
        - Testing error logging for validation failures

    Test Customization:
        def test_validator_logs_warning(mock_logger, monkeypatch):
            monkeypatch.setattr('app.core.startup.redis_security.logger', mock_logger)
            validator = RedisSecurityValidator()
            validator.validate_production_security(
                "redis://localhost:6379",
                insecure_override=True
            )
            mock_logger.warning.assert_called()

    Note:
        This is a proper system boundary mock - logger performs I/O
        and should not be tested as part of security validation unit tests.
    """
    mock = MagicMock()
    mock.info = Mock()
    mock.warning = Mock()
    mock.error = Mock()
    mock.debug = Mock()
    return mock


# =============================================================================
# Environment Variable Mocking Fixtures (System Boundary)
# =============================================================================


@pytest.fixture
def mock_secure_redis_env(monkeypatch):
    """
    Mock environment variables for secure Redis configuration.

    Sets up environment variables representing a secure production
    Redis configuration with TLS and encryption.

    Environment Variables Set:
        - REDIS_URL: rediss://redis:6380 (TLS)
        - REDIS_ENCRYPTION_KEY: valid Fernet key
        - REDIS_TLS_CERT_PATH: /etc/ssl/redis/client.crt
        - REDIS_TLS_KEY_PATH: /etc/ssl/redis/client.key
        - REDIS_TLS_CA_PATH: /etc/ssl/redis/ca.crt
        - REDIS_PASSWORD: strong_password_123456

    Use Cases:
        - Testing secure configuration reading
        - Testing environment variable integration
        - Testing comprehensive security validation

    Example:
        def test_secure_environment(mock_secure_redis_env, redis_security_validator):
            redis_url = os.getenv("REDIS_URL")
            validator.validate_startup_security(redis_url)
            # Should pass validation
    """
    monkeypatch.setenv("REDIS_URL", "rediss://redis:6380")
    monkeypatch.setenv(
        "REDIS_ENCRYPTION_KEY", "dGVzdC1rZXktMzItYnl0ZXMtbG9uZyEhISEhISEhISEhIQ=="
    )
    monkeypatch.setenv("REDIS_TLS_CERT_PATH", "/etc/ssl/redis/client.crt")
    monkeypatch.setenv("REDIS_TLS_KEY_PATH", "/etc/ssl/redis/client.key")
    monkeypatch.setenv("REDIS_TLS_CA_PATH", "/etc/ssl/redis/ca.crt")
    monkeypatch.setenv("REDIS_PASSWORD", "strong_password_123456")
    monkeypatch.setenv("REDIS_INSECURE_ALLOW_PLAINTEXT", "false")


@pytest.fixture
def mock_insecure_redis_env(monkeypatch):
    """
    Mock environment variables for insecure Redis configuration.

    Sets up environment variables representing an insecure Redis
    configuration without TLS or encryption.

    Environment Variables Set:
        - REDIS_URL: redis://localhost:6379 (no TLS)
        - REDIS_INSECURE_ALLOW_PLAINTEXT: false (no override)

    Use Cases:
        - Testing insecure configuration detection
        - Testing production security enforcement
        - Testing error message generation

    Example:
        def test_insecure_environment(mock_insecure_redis_env, redis_security_validator):
            redis_url = os.getenv("REDIS_URL")
            with pytest.raises(ConfigurationError):
                validator.validate_startup_security(redis_url)
    """
    monkeypatch.setenv("REDIS_URL", "redis://localhost:6379")
    monkeypatch.setenv("REDIS_INSECURE_ALLOW_PLAINTEXT", "false")


@pytest.fixture
def mock_insecure_override_env(monkeypatch):
    """
    Mock environment variables with insecure override enabled.

    Sets up environment variables with explicit override allowing
    insecure connections in production.

    Environment Variables Set:
        - REDIS_URL: redis://redis:6379 (no TLS)
        - REDIS_INSECURE_ALLOW_PLAINTEXT: true (override enabled)

    Use Cases:
        - Testing insecure override behavior
        - Testing warning generation for overrides
        - Testing production security bypass

    Example:
        def test_insecure_override(mock_insecure_override_env, redis_security_validator):
            redis_url = os.getenv("REDIS_URL")
            # Should pass with warning
            validator.validate_startup_security(redis_url)
    """
    monkeypatch.setenv("REDIS_URL", "redis://redis:6379")
    monkeypatch.setenv("REDIS_INSECURE_ALLOW_PLAINTEXT", "true")


# =============================================================================
# Cryptography Library Availability Fixtures
# =============================================================================


@pytest.fixture
def mock_cryptography_unavailable(monkeypatch):
    """
    Mock cryptography library unavailability for testing graceful degradation.

    Patches cryptography imports to simulate missing library for testing
    behavior when cryptography is not installed.

    Use Cases:
        - Testing validation without cryptography library
        - Testing warning messages for missing dependencies
        - Testing graceful degradation

    Example:
        def test_validation_without_cryptography(mock_cryptography_unavailable):
            result = validator.validate_encryption_key("test-key")
            assert not result["valid"]
            assert "library not available" in result["errors"][0]
    """
    # Mock ImportError when trying to import cryptography
    def mock_import_error(*args, **kwargs):
        if "cryptography" in str(args):
            raise ImportError("cryptography library not available")
        return None

    monkeypatch.setattr("builtins.__import__", mock_import_error, raising=False)


# =============================================================================
# SecurityValidationResult Fixtures
# =============================================================================


@pytest.fixture
def sample_valid_security_result():
    """
    Sample SecurityValidationResult representing valid security configuration.

    Provides a complete validation result for testing result handling
    and summary generation.

    Returns:
        SecurityValidationResult with all checks passed

    Use Cases:
        - Testing result summary formatting
        - Testing valid configuration reporting
        - Testing success scenarios
    """
    from app.core.startup.redis_security import SecurityValidationResult

    return SecurityValidationResult(
        is_valid=True,
        tls_status="✅ Valid",
        encryption_status="✅ Valid",
        auth_status="✅ Configured",
        connectivity_status="⏭️  Skipped",
        warnings=[],
        errors=[],
        recommendations=[],
        certificate_info={
            "cert_path": "/etc/ssl/redis/client.crt",
            "expires": "2025-12-31T23:59:59",
            "days_until_expiry": 365,
            "subject": "CN=redis.example.com,O=TestOrg,C=US",
        },
    )


@pytest.fixture
def sample_invalid_security_result():
    """
    Sample SecurityValidationResult representing invalid security configuration.

    Provides a validation result with errors for testing error handling
    and reporting.

    Returns:
        SecurityValidationResult with multiple failures

    Use Cases:
        - Testing error summary formatting
        - Testing failure scenario reporting
        - Testing recommendation generation
    """
    from app.core.startup.redis_security import SecurityValidationResult

    return SecurityValidationResult(
        is_valid=False,
        tls_status="❌ No TLS in production",
        encryption_status="❌ Invalid",
        auth_status="❌ Missing",
        connectivity_status="⏭️  Skipped",
        warnings=[
            "No TLS configured for production environment",
            "Encryption key validation failed",
        ],
        errors=[
            "Production requires TLS (rediss://) connections",
            "No authentication configured for production environment",
            "Invalid encryption key length: 12 (expected 44 characters)",
        ],
        recommendations=[
            "Use TLS (rediss://) for production deployments",
            "Enable encryption with REDIS_ENCRYPTION_KEY environment variable",
            "Configure Redis authentication with strong password",
        ],
        certificate_info=None,
    )
