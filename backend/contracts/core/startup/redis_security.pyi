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
```
"""

import logging
from typing import Optional
from app.core.environment import get_environment_info, Environment, FeatureContext
from app.core.exceptions import ConfigurationError


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
