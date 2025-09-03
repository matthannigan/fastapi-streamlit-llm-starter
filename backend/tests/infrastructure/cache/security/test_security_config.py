"""
Unit tests for SecurityConfig initialization and validation behavior.

This test suite verifies the observable behaviors documented in the
SecurityConfig public contract (security.pyi). Tests focus on the
behavior-driven testing principles described in docs/guides/testing/TESTING.md.

Coverage Focus:
    - SecurityConfig initialization and parameter validation
    - Security level assessment and configuration validation
    - Certificate path validation and TLS configuration
    - Authentication configuration validation and security properties

External Dependencies:
    All external dependencies are mocked using fixtures from conftest.py following
    the documented public contracts to ensure accurate behavior simulation.
"""

import pytest
import ssl
from pathlib import Path
from unittest.mock import MagicMock, patch
from typing import Any, Dict, Optional

from app.infrastructure.cache.security import SecurityConfig, create_security_config_from_env
from app.core.exceptions import ConfigurationError


class TestSecurityConfigInitialization:
    """
    Test suite for SecurityConfig initialization and configuration validation.
    
    Scope:
        - Constructor parameter validation and security configuration setup
        - Default parameter application and security baseline establishment
        - Configuration validation and error handling for invalid security settings
        - Security level assessment based on configured authentication and encryption
        
    Business Critical:
        Security configuration failures can expose Redis connections to unauthorized access
        
    Test Strategy:
        - Parameter validation testing using invalid_security_config_params
        - Security level assessment using various configuration combinations
        - Certificate path validation using mock_file_system_operations
        - Authentication configuration testing with valid/invalid credentials
        
    External Dependencies:
        - ssl: For TLS version and cipher suite validation
        - pathlib: For certificate file path validation (mocked)
    """

    def test_init_with_basic_auth_creates_minimal_secure_configuration(self):
        """
        Test that SecurityConfig with basic AUTH creates minimal but secure configuration.
        
        Verifies:
            Basic AUTH password authentication provides baseline security configuration
            
        Business Impact:
            Enables secure Redis connections with minimal configuration complexity
            
        Scenario:
            Given: SecurityConfig initialized with redis_auth password only
            When: Configuration validation occurs during initialization
            Then: Configuration is accepted as providing basic security
            And: has_authentication property returns True
            And: security_level reflects "basic" authentication level
            
        Basic Security Configuration Verified:
            - redis_auth parameter enables password authentication
            - Authentication is properly detected by has_authentication property
            - Security level assessment reflects basic authentication present
            - TLS configuration defaults are applied appropriately
            - Connection parameters receive reasonable timeout defaults
            
        Fixtures Used:
            - valid_security_config_basic_auth: Minimal AUTH-based configuration
            
        Baseline Security:
            Basic AUTH provides minimal acceptable security for development environments
            
        Related Tests:
            - test_init_with_full_tls_creates_comprehensive_secure_configuration()
            - test_has_authentication_property_detects_auth_methods()
        """
        # Given: SecurityConfig initialized with redis_auth password only
        redis_password = "test-password-123"
        config = SecurityConfig(redis_auth=redis_password)
        
        # Then: Configuration is accepted as providing basic security
        assert config.redis_auth == redis_password
        assert config.use_tls is False  # TLS defaults to False
        assert config.acl_username is None
        assert config.acl_password is None
        
        # And: has_authentication property returns True
        assert config.has_authentication is True
        
        # And: security_level reflects basic authentication level
        assert config.security_level == "MEDIUM"  # AUTH without TLS = MEDIUM
        
        # And: Connection parameters receive reasonable timeout defaults
        assert config.connection_timeout == 30
        assert config.socket_timeout == 30
        assert config.max_retries == 3
        assert config.retry_delay == 1.0

    @patch('pathlib.Path.exists')
    def test_init_with_full_tls_creates_comprehensive_secure_configuration(self, mock_path_exists):
        """
        Test that SecurityConfig with full TLS creates comprehensive secure configuration.
        
        Verifies:
            Complete TLS configuration with certificates provides maximum security
            
        Business Impact:
            Enables production-grade security with encryption and certificate authentication
            
        Scenario:
            Given: SecurityConfig with TLS encryption, certificates, and ACL authentication
            When: Configuration validation occurs during initialization
            Then: All security features are properly configured and validated
            And: has_authentication returns True for multiple auth methods
            And: security_level reflects "comprehensive" or "enterprise" level
            
        Comprehensive Security Verified:
            - TLS encryption properly configured with certificate paths
            - ACL username/password authentication configured alongside AUTH fallback
            - Certificate verification settings properly applied
            - TLS version and cipher suite constraints properly set
            - Connection timeouts and retry logic configured for secure connections
            
        Fixtures Used:
            - valid_security_config_full_tls: Complete TLS configuration
            - mock_file_system_operations: Certificate path validation mocking
            
        Enterprise Security:
            Full TLS configuration meets enterprise security requirements
            
        Related Tests:
            - test_init_with_basic_auth_creates_minimal_secure_configuration()
            - test_security_level_property_reflects_configuration_strength()
        """
        # Mock certificate files exist
        mock_path_exists.return_value = True
        
        # Given: SecurityConfig with TLS encryption, certificates, and ACL authentication
        config = SecurityConfig(
            redis_auth="fallback-password",
            use_tls=True,
            tls_cert_path="/etc/ssl/redis-client.crt",
            tls_key_path="/etc/ssl/redis-client.key",
            tls_ca_path="/etc/ssl/ca.crt",
            acl_username="cache_user",
            acl_password="secure-password",
            verify_certificates=True,
            min_tls_version=ssl.TLSVersion.TLSv1_3.value,
            cipher_suites=["ECDHE+AESGCM", "ECDHE+CHACHA20"]
        )
        
        # Then: All security features are properly configured
        assert config.use_tls is True
        assert config.tls_cert_path == "/etc/ssl/redis-client.crt"
        assert config.tls_key_path == "/etc/ssl/redis-client.key"
        assert config.tls_ca_path == "/etc/ssl/ca.crt"
        assert config.verify_certificates is True
        assert config.min_tls_version == ssl.TLSVersion.TLSv1_3.value
        assert config.cipher_suites == ["ECDHE+AESGCM", "ECDHE+CHACHA20"]
        
        # And: has_authentication returns True for multiple auth methods
        assert config.has_authentication is True
        assert config.redis_auth == "fallback-password"
        assert config.acl_username == "cache_user"
        assert config.acl_password == "secure-password"
        
        # And: security_level reflects comprehensive level
        assert config.security_level == "HIGH"  # TLS + AUTH + certificate verification = HIGH

    @patch('pathlib.Path.exists')
    def test_init_with_invalid_parameters_raises_configuration_error(self, mock_path_exists):
        """
        Test that invalid security parameters raise ConfigurationError with detailed context.
        
        Verifies:
            Security parameter validation prevents insecure or invalid configurations
            
        Business Impact:
            Prevents deployment of Redis connections with security misconfigurations
            
        Scenario:
            Given: SecurityConfig with invalid or contradictory security parameters
            When: Configuration validation occurs during initialization
            Then: ConfigurationError is raised with specific validation failures
            And: Error context includes which security parameters are invalid
            And: Error message provides guidance for correct security configuration
            
        Invalid Configuration Scenarios:
            - Empty redis_auth password when authentication required
            - TLS enabled but certificate paths non-existent or inaccessible
            - Certificate verification enabled but CA certificate path missing
            - Invalid connection timeout or retry configuration values
            - Contradictory security settings (e.g., ACL without username)
            
        Fixtures Used:
            - invalid_security_config_params: Configuration parameters that should fail
            - mock_file_system_operations: Certificate path validation for failures
            
        Security Validation:
            Configuration errors prevent insecure Redis connections
            
        Related Tests:
            - test_certificate_path_validation_prevents_invalid_configurations()
            - test_post_init_validation_catches_configuration_conflicts()
        """
        # Test: TLS enabled but certificate file doesn't exist
        mock_path_exists.return_value = False
        
        with pytest.raises(ConfigurationError) as exc_info:
            SecurityConfig(
                use_tls=True,
                tls_cert_path="/nonexistent/cert.pem"
            )
        
        # Focus on exception type and context, not specific message text
        assert isinstance(exc_info.value, ConfigurationError)
        assert hasattr(exc_info.value, 'context')
        assert ('cert_path' in exc_info.value.context or 
                'tls_cert' in str(exc_info.value).lower() or
                'certificate' in str(exc_info.value).lower())
        
        # Test: ACL username without password
        with pytest.raises(ConfigurationError) as exc_info:
            SecurityConfig(
                acl_username="user"
                # Missing acl_password
            )
        
        assert "ACL password is required" in str(exc_info.value)
        assert exc_info.value.context["validation_type"] == "acl_config"
        
        # Test: Invalid connection timeout
        with pytest.raises(ConfigurationError) as exc_info:
            SecurityConfig(connection_timeout=-1)
        
        assert "Connection timeout must be positive" in str(exc_info.value)
        assert exc_info.value.context["validation_type"] == "timeout"
        
        # Test: Invalid max_retries
        with pytest.raises(ConfigurationError) as exc_info:
            SecurityConfig(max_retries=-5)
        
        assert "Max retries cannot be negative" in str(exc_info.value)
        assert exc_info.value.context["validation_type"] == "retry_config"

    @pytest.mark.no_parallel
    def test_post_init_raises_error_for_missing_key_file(self, mock_path_exists):
        """
        Test that __post_init__ validation raises a ConfigurationError if the
        TLS key file is missing when the cert file is present.
        """
        # Arrange: This function now correctly accepts a single Path object.
        def path_exists_side_effect(path_obj):
            if str(path_obj) == "/etc/ssl/cert.pem":
                return True
            if str(path_obj) == "/etc/ssl/key.pem":
                return False
            return True

        mock_path_exists.side_effect = path_exists_side_effect

        # Act & Assert
        with pytest.raises(ConfigurationError) as exc_info:
            SecurityConfig(
                use_tls=True,
                tls_cert_path="/etc/ssl/cert.pem",
                tls_key_path="/etc/ssl/key.pem"
            )
        
        assert "TLS key file not found" in str(exc_info.value)
        assert "key_path" in exc_info.value.context

    @pytest.mark.no_parallel
    def test_post_init_raises_error_for_missing_ca_file(self, mock_path_exists):
        """
        Test that __post_init__ validation raises a ConfigurationError if the
        TLS CA file is missing when certificate verification is enabled.
        """
        # Arrange: This function's signature is now correct.
        def path_exists_side_effect(path_obj):
            if str(path_obj) == "/etc/ssl/ca.pem":
                return False
            return True

        mock_path_exists.side_effect = path_exists_side_effect

        # Act & Assert
        with pytest.raises(ConfigurationError) as exc_info:
            SecurityConfig(
                use_tls=True,
                verify_certificates=True,
                tls_ca_path="/etc/ssl/ca.pem"
            )
        
        assert "TLS CA file not found" in str(exc_info.value)
        assert "ca_path" in exc_info.value.context

    def test_init_raises_error_for_invalid_retry_delay(self):
        """
        Test that __init__ validation raises a ConfigurationError for an
        invalid retry_delay value.
        """
        # Act & Assert
        with pytest.raises(ConfigurationError) as exc_info:
            SecurityConfig(retry_delay=-0.5)
        
        # Assert
        assert "Retry delay cannot be negative" in str(exc_info.value)
        assert exc_info.value.context["validation_type"] == "retry_config"

    def test_has_authentication_property_detects_auth_methods(self):
        """
        Test that has_authentication property correctly identifies configured authentication.
        
        Verifies:
            Authentication detection accurately identifies various auth method configurations
            
        Business Impact:
            Enables accurate security status assessment for monitoring and validation
            
        Scenario:
            Given: SecurityConfig instances with various authentication configurations
            When: has_authentication property is accessed
            Then: Property accurately returns True when any authentication is configured
            And: Property returns False only when no authentication methods are present
            And: Detection works for AUTH passwords, ACL credentials, and combinations
            
        Authentication Method Detection:
            - redis_auth password authentication detected as authentication present
            - ACL username/password combination detected as authentication present
            - Both AUTH and ACL configured detected as authentication present
            - No authentication methods configured detected as no authentication
            - Empty or None authentication values detected as no authentication
            
        Fixtures Used:
            - valid_security_config_basic_auth: AUTH-based authentication
            - valid_security_config_full_tls: Multiple authentication methods
            - insecure_config_no_auth: No authentication configured
            
        Accurate Detection:
            Authentication presence is accurately detected across all configuration types
            
        Related Tests:
            - test_security_level_property_reflects_configuration_strength()
            - test_authentication_configuration_validation()
        """
        # Test: redis_auth password authentication detected
        config_auth = SecurityConfig(redis_auth="password123")
        assert config_auth.has_authentication is True
        
        # Test: ACL username/password combination detected
        config_acl = SecurityConfig(acl_username="user", acl_password="password")
        assert config_acl.has_authentication is True
        
        # Test: Both AUTH and ACL configured detected
        config_both = SecurityConfig(
            redis_auth="auth_password",
            acl_username="user",
            acl_password="acl_password"
        )
        assert config_both.has_authentication is True
        
        # Test: No authentication methods configured
        config_none = SecurityConfig()
        assert config_none.has_authentication is False
        
        # Test: Empty authentication values detected as no authentication
        config_empty_auth = SecurityConfig(redis_auth="")
        assert config_empty_auth.has_authentication is False
        
        config_empty_acl = SecurityConfig(acl_username="", acl_password="")
        assert config_empty_acl.has_authentication is False
        
        # Test: None authentication values detected as no authentication
        config_none_auth = SecurityConfig(redis_auth=None)
        assert config_none_auth.has_authentication is False
        
        # Test: Partial ACL configuration (username only) detected as no authentication
        # This should raise ConfigurationError during init, but let's test the property logic
        config_partial = SecurityConfig()
        config_partial.acl_username = "user"
        config_partial.acl_password = None
        assert config_partial.has_authentication is False

    @patch('pathlib.Path.exists')
    def test_security_level_property_reflects_configuration_strength(self, mock_path_exists):
        """
        Test that security_level property provides meaningful assessment of configuration strength.
        
        Verifies:
            Security level assessment accurately categorizes configuration security strength
            
        Business Impact:
            Enables security posture assessment and compliance validation
            
        Scenario:
            Given: SecurityConfig instances with varying levels of security configuration
            When: security_level property is accessed
            Then: Property returns descriptive security level matching configuration
            And: Security levels accurately reflect authentication and encryption presence
            And: Security assessment helps identify configuration improvement opportunities
            
        Security Level Categories:
            - "insecure": No authentication or encryption configured
            - "basic": Basic authentication (AUTH password) without encryption
            - "standard": Authentication with TLS encryption enabled
            - "comprehensive": Multiple auth methods with TLS and certificate verification
            - "enterprise": Full security with ACL, TLS, certificates, and hardened settings
            
        Fixtures Used:
            - insecure_config_no_auth: Expected to return "insecure" level
            - valid_security_config_basic_auth: Expected to return "basic" level  
            - valid_security_config_full_tls: Expected to return "comprehensive" level
            
        Meaningful Assessment:
            Security level descriptions provide actionable security posture information
            
        Related Tests:
            - test_has_authentication_property_detects_auth_methods()
            - test_security_configuration_provides_improvement_recommendations()
        """
        # Test: LOW level - No authentication or encryption configured
        config_insecure = SecurityConfig()
        assert config_insecure.security_level == "LOW"
        
        # Test: MEDIUM level - Basic authentication without encryption
        config_basic_auth = SecurityConfig(redis_auth="password123")
        assert config_basic_auth.security_level == "MEDIUM"
        
        # Test: MEDIUM level - TLS without authentication
        mock_path_exists.return_value = True
        config_tls_only = SecurityConfig(use_tls=True)
        assert config_tls_only.security_level == "MEDIUM"
        
        # Test: HIGH level - Authentication with TLS encryption enabled
        config_standard = SecurityConfig(
            redis_auth="password123",
            use_tls=True,
            verify_certificates=True
        )
        assert config_standard.security_level == "HIGH"
        
        # Test: HIGH level - Multiple auth methods with TLS and certificate verification
        config_comprehensive = SecurityConfig(
            redis_auth="fallback_password",
            use_tls=True,
            tls_cert_path="/etc/ssl/cert.pem",
            acl_username="user",
            acl_password="password",
            verify_certificates=True
        )
        assert config_comprehensive.security_level == "HIGH"
        
        # Test: MEDIUM level - TLS without certificate verification
        config_tls_no_verify = SecurityConfig(
            redis_auth="password123",
            use_tls=True,
            verify_certificates=False
        )
        assert config_tls_no_verify.security_level == "MEDIUM"

    @patch('pathlib.Path.exists')
    def test_certificate_path_validation_prevents_invalid_configurations(self, mock_path_exists):
        """
        Test that certificate path validation prevents TLS configuration with invalid paths.
        
        Verifies:
            Certificate file validation ensures TLS configuration uses accessible certificates
            
        Business Impact:
            Prevents TLS connection failures due to missing or inaccessible certificate files
            
        Scenario:
            Given: SecurityConfig with TLS enabled and various certificate path configurations
            When: Certificate path validation occurs during configuration
            Then: Invalid or inaccessible certificate paths cause configuration errors
            And: Valid, accessible certificate paths are accepted for TLS configuration
            And: Certificate path validation includes file existence and readability checks
            
        Certificate Path Validation:
            - Non-existent certificate files cause configuration validation errors
            - Directory paths instead of files cause validation errors
            - Inaccessible certificate files (permissions) cause validation errors
            - Valid, readable certificate files pass validation
            - Relative certificate paths are resolved and validated appropriately
            
        Fixtures Used:
            - valid_security_config_full_tls: Valid certificate paths
            - sample_certificate_paths: Various path scenarios for validation
            - mock_file_system_operations: File system operation mocking
            
        TLS Reliability:
            Certificate validation ensures TLS connections can be established successfully
            
        Related Tests:
            - test_tls_configuration_requires_certificate_files()
            - test_certificate_verification_configuration_validation()
        """
        # Test: Valid certificate paths are accepted
        mock_path_exists.return_value = True
        
        config_valid = SecurityConfig(
            use_tls=True,
            tls_cert_path="/etc/ssl/valid-cert.pem",
            tls_key_path="/etc/ssl/valid-key.pem",
            tls_ca_path="/etc/ssl/valid-ca.pem"
        )
        
        assert config_valid.use_tls is True
        assert config_valid.tls_cert_path == "/etc/ssl/valid-cert.pem"
        assert config_valid.tls_key_path == "/etc/ssl/valid-key.pem"
        assert config_valid.tls_ca_path == "/etc/ssl/valid-ca.pem"
        
        # Test: Non-existent certificate file causes error
        mock_path_exists.return_value = False
        
        with pytest.raises(ConfigurationError) as exc_info:
            SecurityConfig(
                use_tls=True,
                tls_cert_path="/nonexistent/cert.pem"
            )
        
        # Focus on exception type and behavior, not specific message text
        assert isinstance(exc_info.value, ConfigurationError)
        # Should indicate certificate-related error
        assert ('certificate' in str(exc_info.value).lower() or 
                'cert' in str(exc_info.value).lower() or
                'tls' in str(exc_info.value).lower())
        
        # Test: Non-existent key file causes error
        mock_path_exists.reset_mock()
        mock_path_exists.return_value = False
        
        with pytest.raises(ConfigurationError) as exc_info:
            SecurityConfig(
                use_tls=True,
                tls_cert_path="/etc/ssl/cert.pem",
                tls_key_path="/nonexistent/key.pem"
            )
        
        # Focus on exception type and behavior, not specific message text
        assert isinstance(exc_info.value, ConfigurationError)
        assert ('key' in str(exc_info.value).lower() or 'tls' in str(exc_info.value).lower())
        
        # Test: Non-existent CA file causes error
        mock_path_exists.reset_mock()
        mock_path_exists.return_value = False
        
        with pytest.raises(ConfigurationError) as exc_info:
            SecurityConfig(
                use_tls=True,
                tls_ca_path="/nonexistent/ca.pem"
            )
        
        assert "TLS CA file not found" in str(exc_info.value)
        
        # Test: TLS disabled doesn't require certificate paths
        mock_path_exists.return_value = False
        config_no_tls = SecurityConfig(use_tls=False)
        assert config_no_tls.use_tls is False


class TestSecurityConfigEnvironmentCreation:
    """
    Test suite for SecurityConfig creation from environment variables.
    
    Scope:
        - create_security_config_from_env() function behavior and environment parsing
        - Environment variable validation and type conversion
        - Default value application when environment variables not present
        - Security configuration assembly from environment variable sources
        
    Business Critical:
        Environment-based configuration enables secure containerized deployment
        
    Test Strategy:
        - Environment variable parsing using environment_variables_secure/insecure
        - Type conversion testing for boolean and numeric environment values
        - Missing environment variable handling with appropriate defaults
        - Security configuration validation from environment sources
        
    External Dependencies:
        - os.environ: Environment variable access (mocked for testing)
    """

    @patch.dict('os.environ', {
        'REDIS_AUTH': 'secure-password-123',
        'REDIS_USE_TLS': 'true',
        'REDIS_TLS_CERT_PATH': '/etc/ssl/redis.crt',
        'REDIS_TLS_KEY_PATH': '/etc/ssl/redis.key',
        'REDIS_TLS_CA_PATH': '/etc/ssl/ca.crt',
        'REDIS_ACL_USERNAME': 'redis_user',
        'REDIS_ACL_PASSWORD': 'acl_password_123',
        'REDIS_VERIFY_CERTIFICATES': 'true',
        'REDIS_CONNECTION_TIMEOUT': '45',
        'REDIS_MAX_RETRIES': '5',
        'REDIS_RETRY_DELAY': '2.0'
    })
    @patch('pathlib.Path.exists')
    def test_create_from_env_builds_secure_config_from_environment(self, mock_path_exists):
        """
        Test that create_security_config_from_env creates secure configuration from environment.
        
        Verifies:
            Environment variables are properly parsed into SecurityConfig with security features
            
        Business Impact:
            Enables secure Redis configuration in containerized and cloud environments
            
        Scenario:
            Given: Environment variables containing comprehensive security configuration
            When: create_security_config_from_env() function is called
            Then: SecurityConfig is created with security features from environment
            And: Authentication credentials are properly extracted from environment
            And: TLS configuration is properly assembled from environment variables
            
        Environment Configuration Assembly:
            - REDIS_AUTH extracted as redis_auth password parameter
            - REDIS_USE_TLS parsed as boolean for TLS enabling
            - Certificate paths extracted from REDIS_TLS_* environment variables
            - ACL credentials extracted from REDIS_ACL_* environment variables
            - Connection parameters extracted with appropriate type conversion
            
        Fixtures Used:
            - environment_variables_secure: Complete secure environment configuration
            - mock_file_system_operations: Certificate path validation in environment
            
        Container Security:
            Environment-based configuration supports secure containerized deployment
            
        Related Tests:
            - test_create_from_env_returns_none_when_no_security_variables()
            - test_create_from_env_handles_invalid_environment_values()
        """
        # Mock certificate files exist
        mock_path_exists.return_value = True
        
        # When: create_security_config_from_env() function is called
        config = create_security_config_from_env()
        
        # Then: SecurityConfig is created with security features from environment
        assert config is not None
        
        # And: Authentication credentials are properly extracted from environment
        assert config.redis_auth == "secure-password-123"
        assert config.acl_username == "redis_user"
        assert config.acl_password == "acl_password_123"
        
        # And: TLS configuration is properly assembled from environment variables
        assert config.use_tls is True
        assert config.tls_cert_path == "/etc/ssl/redis.crt"
        assert config.tls_key_path == "/etc/ssl/redis.key"
        assert config.tls_ca_path == "/etc/ssl/ca.crt"
        assert config.verify_certificates is True
        
        # And: Connection parameters extracted with appropriate type conversion
        assert config.connection_timeout == 45
        assert config.max_retries == 5
        assert config.retry_delay == 2.0
        
        # Verify security properties
        assert config.has_authentication is True
        assert config.security_level == "HIGH"

    @patch.dict('os.environ', {}, clear=True)
    def test_create_from_env_returns_none_when_no_security_variables(self):
        """
        Test that create_security_config_from_env returns None when no security variables present.
        
        Verifies:
            Function gracefully handles environment without security configuration
            
        Business Impact:
            Allows application startup without security when no environment configuration present
            
        Scenario:
            Given: Environment without Redis security configuration variables
            When: create_security_config_from_env() function is called
            Then: None is returned indicating no security configuration available
            And: No exceptions are raised for missing security environment
            And: Function provides clear indication that security setup is required
            
        No Configuration Handling:
            - Missing REDIS_AUTH environment variable handled gracefully
            - Missing TLS configuration variables handled appropriately
            - Missing ACL configuration variables handled without errors
            - Empty environment returns None without creating invalid configuration
            
        Fixtures Used:
            - Empty environment or environment_variables_insecure (minimal config)
            
        Graceful Degradation:
            Missing security configuration allows application to handle security appropriately
            
        Related Tests:
            - test_create_from_env_builds_secure_config_from_environment()
            - test_insecure_environment_provides_appropriate_warnings()
        """
        # Given: Environment without Redis security configuration variables
        # (Cleared by patch.dict)
        
        # When: create_security_config_from_env() function is called
        config = create_security_config_from_env()
        
        # Then: None is returned indicating no security configuration available
        assert config is None
        
        # Test with non-security environment variables present
        with patch.dict('os.environ', {'OTHER_VAR': 'value', 'PATH': '/usr/bin'}):
            config = create_security_config_from_env()
            assert config is None

    @patch('pathlib.Path.exists')
    def test_create_from_env_handles_invalid_environment_values(self, mock_path_exists):
        """
        Test that create_security_config_from_env handles invalid environment variable values.
        
        Verifies:
            Invalid environment values are handled gracefully with appropriate error reporting
            
        Business Impact:
            Prevents application startup with invalid security configuration from environment
            
        Scenario:
            Given: Environment variables with invalid values for security configuration
            When: create_security_config_from_env() function is called
            Then: Invalid values cause appropriate configuration errors or warnings
            And: Type conversion errors are handled gracefully with clear error messages
            And: Security implications of invalid values are communicated clearly
            
        Invalid Environment Value Handling:
            - Invalid boolean values for REDIS_USE_TLS handled with clear errors
            - Invalid numeric values for timeouts converted appropriately or rejected
            - Invalid certificate paths detected and reported during environment parsing
            - Contradictory environment variable combinations detected and reported
            
        Fixtures Used:
            - Mock environment with invalid configuration values
            - mock_file_system_operations: For certificate path validation failures
            
        Robust Environment Parsing:
            Invalid environment configuration prevents insecure application startup
            
        Related Tests:
            - test_environment_type_conversion_validation()
            - test_environment_security_validation_integration()
        """
        # Test: Invalid numeric timeout value causes ValueError during int conversion
        with patch.dict('os.environ', {
            'REDIS_AUTH': 'password',
            'REDIS_CONNECTION_TIMEOUT': 'invalid_number'
        }):
            with pytest.raises(ValueError):
                create_security_config_from_env()
        
        # Test: Invalid certificate paths cause ConfigurationError
        mock_path_exists.return_value = False
        
        with patch.dict('os.environ', {
            'REDIS_AUTH': 'password',
            'REDIS_USE_TLS': 'true',
            'REDIS_TLS_CERT_PATH': '/invalid/cert.pem'
        }):
            with pytest.raises(ConfigurationError) as exc_info:
                create_security_config_from_env()
            
            assert "TLS certificate file not found" in str(exc_info.value)
        
        # Test: ACL username without password causes ConfigurationError
        with patch.dict('os.environ', {
            'REDIS_ACL_USERNAME': 'user'
            # Missing REDIS_ACL_PASSWORD
        }):
            with pytest.raises(ConfigurationError) as exc_info:
                create_security_config_from_env()
            
            assert "ACL password is required" in str(exc_info.value)
        
        # Test: Boolean values are properly converted (both true/false work)
        mock_path_exists.return_value = True
        
        with patch.dict('os.environ', {
            'REDIS_AUTH': 'password',
            'REDIS_USE_TLS': 'false',
            'REDIS_VERIFY_CERTIFICATES': 'false'
        }):
            config = create_security_config_from_env()
            assert config.use_tls is False  # type: ignore
            assert config.verify_certificates is False  # type: ignore
        
        with patch.dict('os.environ', {
            'REDIS_AUTH': 'password',
            'REDIS_USE_TLS': 'TRUE',
            'REDIS_VERIFY_CERTIFICATES': 'True'
        }):
            config = create_security_config_from_env()
            assert config.use_tls is True  # type: ignore
            assert config.verify_certificates is True  # type: ignore   
