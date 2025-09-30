"""
Redis security validation for application startup.

This module provides fail-fast Redis security validation that ensures secure
connections are mandatory in production environments while allowing flexibility
in development contexts.

## Security Philosophy

This implementation follows a security-first approach where:
- Production environments MUST use TLS encryption and authentication
- Development environments are encouraged but not required to use TLS
- Explicit insecure overrides are available with prominent warnings
- Application fails immediately if security requirements aren't met

## Usage

```python
from app.core.startup.redis_security import RedisSecurityValidator

# Initialize validator
validator = RedisSecurityValidator()

# Validate Redis security configuration
validator.validate_production_security(
    redis_url="rediss://redis:6380",
    insecure_override=False
)

# Comprehensive configuration validation
validation_report = validator.validate_security_configuration(
    redis_url="rediss://redis:6380",
    encryption_key="your-fernet-key",
    tls_cert_path="/path/to/cert.pem"
)
print(validation_report.summary())
```
"""

import logging
import os
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from app.core.environment import Environment, FeatureContext, get_environment_info
from app.core.exceptions import ConfigurationError


@dataclass
class SecurityValidationResult:
    """
    Results from comprehensive security configuration validation.
    
    Attributes:
        is_valid: Overall validation status
        tls_status: TLS configuration validation status
        encryption_status: Encryption key validation status
        auth_status: Authentication configuration status
        connectivity_status: Redis connectivity test status
        warnings: List of security warnings
        errors: List of validation errors
        recommendations: Security improvement recommendations
        certificate_info: TLS certificate information if available
    """

    def summary(self) -> str:
        """
        Generate human-readable validation summary.
        """
        ...


class RedisSecurityValidator:
    """
    Validates Redis security configuration at application startup.
    
    This validator enforces security-first Redis connections with environment-aware
    requirements. Production environments must use secure connections while
    development environments have flexibility with explicit override support.
    
    The validator integrates with the existing environment detection system to
    provide appropriate security levels for different deployment contexts.
    """

    def __init__(self):
        """
        Initialize the Redis security validator.
        """
        ...

    def validate_production_security(self, redis_url: str, insecure_override: bool = False) -> None:
        """
        Validate Redis security for production environments.
        
        This method enforces TLS encryption and authentication requirements in
        production while allowing development flexibility. It provides clear
        error messages and configuration guidance when security requirements
        are not met.
        
        Args:
            redis_url: Redis connection string to validate
            insecure_override: Explicit override to allow insecure connections
                             in production (logs prominent security warning)
        
        Raises:
            ConfigurationError: If production environment lacks required security
                              and no explicit override is provided
        
        Examples:
            # Production validation (must be secure)
            validator.validate_production_security("rediss://redis:6380")
        
            # Development validation (flexible)
            validator.validate_production_security("redis://localhost:6379")
        
            # Production with override (warning logged)
            validator.validate_production_security(
                "redis://internal:6379",
                insecure_override=True
            )
        """
        ...

    def validate_tls_certificates(self, cert_path: Optional[str] = None, key_path: Optional[str] = None, ca_path: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate TLS certificate files and their properties.
        
        Args:
            cert_path: Path to client certificate file
            key_path: Path to private key file
            ca_path: Path to CA certificate file
        
        Returns:
            Dictionary with validation results and certificate info
        
        Examples:
            result = validator.validate_tls_certificates(
                cert_path="/path/to/cert.pem",
                key_path="/path/to/key.pem",
                ca_path="/path/to/ca.pem"
            )
        """
        ...

    def validate_encryption_key(self, encryption_key: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate encryption key format and strength.
        
        Args:
            encryption_key: Fernet encryption key to validate
        
        Returns:
            Dictionary with validation results
        
        Examples:
            result = validator.validate_encryption_key("your-fernet-key")
        """
        ...

    def validate_redis_auth(self, redis_url: str, auth_password: Optional[str] = None) -> Dict[str, Any]:
        """
        Validate Redis authentication configuration.
        
        Args:
            redis_url: Redis connection URL
            auth_password: Redis AUTH password (if not in URL)
        
        Returns:
            Dictionary with validation results
        
        Examples:
            result = validator.validate_redis_auth("redis://user:pass@localhost:6379")
        """
        ...

    def validate_security_configuration(self, redis_url: str, encryption_key: Optional[str] = None, tls_cert_path: Optional[str] = None, tls_key_path: Optional[str] = None, tls_ca_path: Optional[str] = None, auth_password: Optional[str] = None, test_connectivity: bool = False) -> SecurityValidationResult:
        """
        Perform comprehensive security configuration validation.
        
        This method validates all aspects of Redis security configuration including
        TLS, encryption, authentication, and optionally connectivity testing.
        
        Args:
            redis_url: Redis connection URL
            encryption_key: Fernet encryption key
            tls_cert_path: Path to TLS client certificate
            tls_key_path: Path to TLS private key
            tls_ca_path: Path to TLS CA certificate
            auth_password: Redis authentication password
            test_connectivity: Whether to test actual Redis connectivity
        
        Returns:
            SecurityValidationResult with detailed validation information
        
        Examples:
            # Full validation
            result = validator.validate_security_configuration(
                redis_url="rediss://redis:6380",
                encryption_key=os.getenv("REDIS_ENCRYPTION_KEY"),
                tls_cert_path="/path/to/cert.pem",
                test_connectivity=True
            )
            print(result.summary())
        """
        ...

    def validate_startup_security(self, redis_url: str, insecure_override: Optional[bool] = None) -> None:
        """
        Comprehensive Redis security validation for application startup.
        
        This is the main entry point for startup security validation. It performs
        environment-aware security validation and provides clear feedback on
        security status.
        
        Args:
            redis_url: Redis connection string to validate
            insecure_override: Optional explicit override for insecure connections
                             If None, will be determined from environment variables
        
        Raises:
            ConfigurationError: If security requirements are not met
        
        Examples:
            # Standard startup validation
            validator.validate_startup_security("rediss://redis:6380")
        
            # With explicit override
            validator.validate_startup_security("redis://redis:6379", insecure_override=True)
        """
        ...


def validate_redis_security(redis_url: str, insecure_override: Optional[bool] = None) -> None:
    """
    Convenience function for Redis security validation.
    
    This function provides a simple interface for startup security validation
    without requiring explicit validator instantiation.
    
    Args:
        redis_url: Redis connection string to validate
        insecure_override: Optional explicit override for insecure connections
    
    Raises:
        ConfigurationError: If security requirements are not met
    
    Examples:
        # Simple validation
        validate_redis_security("rediss://redis:6380")
    
        # With override
        validate_redis_security("redis://redis:6379", insecure_override=True)
    """
    ...
