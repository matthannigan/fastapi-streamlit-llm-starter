"""
Fixtures for startup integration tests.

This module provides shared fixtures for testing Redis security validation
and application startup integration. All fixtures follow the monkeypatch
pattern for environment variable manipulation to ensure proper test isolation.
"""

import pytest
from cryptography.fernet import Fernet


@pytest.fixture
def production_environment(monkeypatch):
    """
    Configure production environment for security testing.

    Sets production environment indicators using monkeypatch for automatic
    cleanup. This fixture provides a realistic production context for testing
    security enforcement.

    Usage:
        def test_production_security(production_environment):
            # Test runs with production environment configured
            validator = RedisSecurityValidator()
            # Production security rules will be enforced

    Environment Variables Set:
        - ENVIRONMENT=production
        - RAILWAY_ENVIRONMENT=production
        - PRODUCTION=true

    Critical:
        Uses monkeypatch.setenv() for automatic cleanup - never use os.environ[]
    """
    monkeypatch.setenv("ENVIRONMENT", "production")
    monkeypatch.setenv("RAILWAY_ENVIRONMENT", "production")
    monkeypatch.setenv("PRODUCTION", "true")


@pytest.fixture
def development_environment(monkeypatch):
    """
    Configure development environment for flexible security testing.

    Sets development environment indicators and removes production flags.
    This fixture enables testing of developer-friendly flexible security rules.

    Usage:
        def test_development_flexibility(development_environment):
            # Test runs with development environment configured
            validator = RedisSecurityValidator()
            # Flexible security rules apply

    Environment Variables:
        - ENVIRONMENT=development
        - Removes: RAILWAY_ENVIRONMENT, PRODUCTION

    Critical:
        Uses monkeypatch for automatic cleanup
    """
    monkeypatch.setenv("ENVIRONMENT", "development")
    monkeypatch.delenv("RAILWAY_ENVIRONMENT", raising=False)
    monkeypatch.delenv("PRODUCTION", raising=False)


@pytest.fixture
def testing_environment(monkeypatch):
    """
    Configure testing environment for CI/CD and integration tests.

    Sets testing environment which behaves similarly to development but
    with explicit testing context.

    Usage:
        def test_ci_security(testing_environment):
            # Test runs with testing environment configured

    Environment Variables:
        - ENVIRONMENT=testing
        - Removes: RAILWAY_ENVIRONMENT, PRODUCTION

    Critical:
        Uses monkeypatch for automatic cleanup
    """
    monkeypatch.setenv("ENVIRONMENT", "testing")
    monkeypatch.delenv("RAILWAY_ENVIRONMENT", raising=False)
    monkeypatch.delenv("PRODUCTION", raising=False)


@pytest.fixture
def valid_fernet_key():
    """
    Generate valid Fernet encryption key for testing.

    Returns:
        str: Valid 44-character base64-encoded Fernet key

    Usage:
        def test_encryption(valid_fernet_key):
            validator = RedisSecurityValidator()
            result = validator.validate_encryption_key(valid_fernet_key)
            assert result["valid"] is True

    Note:
        Each call generates a new key - don't use for persistence testing
    """
    return Fernet.generate_key().decode("utf-8")


@pytest.fixture
def test_certificates(tmp_path):
    """
    Create temporary test certificate files for TLS validation.

    Creates realistic certificate and key files in temporary directory
    for testing certificate validation logic.

    Args:
        tmp_path: pytest temporary directory fixture

    Returns:
        dict: Paths to certificate files
            - cert_path: Client certificate path
            - key_path: Private key path
            - ca_path: CA certificate path

    Usage:
        def test_certificate_validation(test_certificates):
            validator = RedisSecurityValidator()
            result = validator.validate_tls_certificates(
                cert_path=test_certificates["cert_path"],
                key_path=test_certificates["key_path"]
            )

    Note:
        Certificates are minimal PEM format for testing - not production-ready
    """
    # Create client certificate file
    cert_file = tmp_path / "test_cert.pem"
    cert_file.write_text(
        "-----BEGIN CERTIFICATE-----\n"
        "MIICmzCCAYMCAgPoMA0GCSqGSIb3DQEBBQUAMBQxEjAQBgNVBAMTCWxvY2FsaG9z\n"
        "dAAeFw0yNDAxMDEwMDAwMDBaFw0yNTAxMDEwMDAwMDBaMBQxEjAQBgNVBAMTCWxv\n"
        "Y2FsaG9zdDCCASIwDQYJKoZIhvcNAQEBBQADggEPADCCAQoCggEBALtUlNS31Szx\n"
        "wqPy8yWsE9yV4H9em+tZ2oe+RhTjlJPJ+08JY9k7asdfalIc9nWEwuRCcBD5Rz73\n"
        "2bQDlfbVjRYfXCLUPnRGCZaWHLxMrLQTaBB0WEJcsFQ9oZXxEJKXSqEVzC3ZlUYB\n"
        "-----END CERTIFICATE-----"
    )

    # Create private key file
    key_file = tmp_path / "test_key.pem"
    key_file.write_text(
        "-----BEGIN PRIVATE KEY-----\n"
        "MIIEvQIBADANBgkqhkiG9w0BAQEFAASCBKcwggSjAgEAAoIBAQC7VJTUt9Us8cKj\n"
        "8vMlrBPcleB/XpvrWdqHvkYU45STyftPCWPZO2rHX2pSHPZ1hMLkQnAQ+Uc+99m0\n"
        "A5X21Y0WH1wi1D50RgmWlhy8TKy0E2gQdFhCXLBUPaGV8RCSl0qhFcwt2ZVGAQ==\n"
        "-----END PRIVATE KEY-----"
    )

    # Create CA certificate file
    ca_file = tmp_path / "test_ca.pem"
    ca_file.write_text(
        "-----BEGIN CERTIFICATE-----\n"
        "MIICmzCCAYMCAgPoMA0GCSqGSIb3DQEBBQUAMBQxEjAQBgNVBAMTCWxvY2FsaG9z\n"
        "dAAeFw0yNDAxMDEwMDAwMDBaFw0yNTAxMDEwMDAwMDBaMBQxEjAQBgNVBAMTCWxv\n"
        "-----END CERTIFICATE-----"
    )

    return {
        "cert_path": str(cert_file),
        "key_path": str(key_file),
        "ca_path": str(ca_file),
    }


@pytest.fixture
def secure_redis_urls():
    """
    Provide collection of secure Redis URL examples.

    Returns:
        dict: Various secure URL formats for testing
            - tls: rediss:// URL
            - tls_with_auth: rediss:// with credentials
            - auth: redis:// with authentication

    Usage:
        def test_secure_urls(secure_redis_urls):
            for name, url in secure_redis_urls.items():
                validator.validate_production_security(url)
                # All should pass in production
    """
    return {
        "tls": "rediss://redis:6380",
        "tls_with_auth": "rediss://user:password@redis:6380",
        "auth": "redis://user:password@redis:6379",
    }


@pytest.fixture
def insecure_redis_urls():
    """
    Provide collection of insecure Redis URL examples.

    Returns:
        dict: Various insecure URL formats for testing
            - basic: Simple redis:// without auth
            - localhost: Local redis without security
            - custom_port: Non-standard port without security

    Usage:
        def test_insecure_urls_in_production(insecure_redis_urls, production_environment):
            for name, url in insecure_redis_urls.items():
                with pytest.raises(ConfigurationError):
                    validator.validate_production_security(url)
    """
    return {
        "basic": "redis://redis:6379",
        "localhost": "redis://localhost:6379",
        "custom_port": "redis://redis:6380",
    }


@pytest.fixture
def redis_security_config(monkeypatch, valid_fernet_key, test_certificates):
    """
    Complete Redis security configuration for comprehensive testing.

    Provides a fully configured Redis security setup with TLS certificates,
    encryption key, and authentication. Useful for testing complete security
    validation flows.

    Args:
        monkeypatch: pytest monkeypatch fixture
        valid_fernet_key: Valid encryption key fixture
        test_certificates: Certificate files fixture

    Returns:
        dict: Complete security configuration
            - redis_url: Secure Redis URL
            - encryption_key: Fernet key
            - cert_path: TLS certificate path
            - key_path: TLS key path
            - ca_path: CA certificate path

    Usage:
        def test_comprehensive_security(redis_security_config):
            validator = RedisSecurityValidator()
            result = validator.validate_security_configuration(**redis_security_config)
            assert result.is_valid

    Note:
        Sets environment variables via monkeypatch for automatic cleanup
    """
    config = {
        "redis_url": "rediss://user:strongpassword123456@redis:6380",
        "encryption_key": valid_fernet_key,
        "tls_cert_path": test_certificates["cert_path"],
        "tls_key_path": test_certificates["key_path"],
        "tls_ca_path": test_certificates["ca_path"],
    }

    # Set corresponding environment variables for realistic testing
    monkeypatch.setenv("REDIS_URL", config["redis_url"])
    monkeypatch.setenv("REDIS_ENCRYPTION_KEY", config["encryption_key"])
    monkeypatch.setenv("REDIS_TLS_CERT_PATH", config["tls_cert_path"])
    monkeypatch.setenv("REDIS_TLS_KEY_PATH", config["tls_key_path"])
    monkeypatch.setenv("REDIS_TLS_CA_PATH", config["tls_ca_path"])

    return config


@pytest.fixture
def redis_security_validator():
    """
    Real RedisSecurityValidator instance for integration testing.

    Provides an actual validator instance to test real validation logic
    and integration with cryptography library. This is not a mock - it's
    the real component being tested.

    Returns:
        RedisSecurityValidator instance

    Scope:
        Function-scoped to ensure test isolation - each test gets a fresh
        validator instance with no shared state.

    Use Cases:
        - Testing validate_encryption_key() integration with cryptography
        - Testing validate_tls_certificates() file operations
        - Testing validate_redis_auth() URL parsing
        - Testing comprehensive validation workflows

    Example:
        def test_encryption_validation(redis_security_validator):
            result = redis_security_validator.validate_encryption_key(key)
            assert result["valid"] is True
    """
    from app.core.startup.redis_security import RedisSecurityValidator

    return RedisSecurityValidator()
