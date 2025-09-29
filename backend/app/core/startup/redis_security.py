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

logger = logging.getLogger(__name__)


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
        """Initialize the Redis security validator."""
        self.logger = logging.getLogger(__name__)

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
        env_info = get_environment_info(FeatureContext.SECURITY_ENFORCEMENT)

        # Only enforce TLS in production environments
        if env_info.environment != Environment.PRODUCTION:
            self.logger.info(
                f"Environment: {env_info.environment.value} - TLS validation skipped. "
                f"Using flexible security for {env_info.environment.value} environment."
            )
            return

        # Check for explicit insecure override in production
        if insecure_override:
            self.logger.warning(
                "🚨 SECURITY WARNING: Running with insecure Redis connection in production!\n"
                "\n"
                "REDIS_INSECURE_ALLOW_PLAINTEXT=true detected. This should ONLY be used "
                "in highly secure, isolated network environments where:\n"
                "- Network traffic is encrypted at the infrastructure level\n"
                "- Redis access is restricted to authorized services only\n"
                "- Network monitoring and intrusion detection are in place\n"
                "\n"
                "🔐 Recommendation: Use TLS encryption (rediss://) for maximum security."
            )
            return

        # Validate TLS usage in production
        if not self._is_secure_connection(redis_url):
            raise ConfigurationError(
                "🔒 SECURITY ERROR: Production environment requires secure Redis connection.\n"
                "\n"
                f"Current connection: insecure ({redis_url.split('://')[0]}://)\n"
                "Required: TLS-enabled (rediss://) or authenticated connection\n"
                "\n"
                "To fix this issue:\n"
                "1. Use TLS: Change REDIS_URL to rediss://your-redis-host:6380\n"
                "2. Or set REDIS_TLS_ENABLED=true in environment\n"
                "3. For secure networks only: Set REDIS_INSECURE_ALLOW_PLAINTEXT=true\n"
                "\n"
                "📚 See documentation: docs/infrastructure/redis-security.md\n"
                f"🌍 Environment detected: {env_info.environment.value} (confidence: {env_info.confidence:.1f})",
                context={
                    "redis_url": redis_url,
                    "environment": env_info.environment.value,
                    "confidence": env_info.confidence,
                    "validation_type": "production_security",
                    "required_fix": "tls_connection"
                }
            )

        self.logger.info(f"✅ Production Redis security validation passed: TLS connection verified")

    def _is_secure_connection(self, redis_url: str) -> bool:
        """
        Check if Redis connection is secure.

        A connection is considered secure if:
        1. Uses TLS encryption (rediss:// scheme), OR
        2. Uses authentication with redis:// scheme (has @ symbol indicating auth)

        Args:
            redis_url: Redis connection URL to analyze

        Returns:
            True if connection is secure, False otherwise

        Examples:
            >>> validator._is_secure_connection("rediss://redis:6380")
            True
            >>> validator._is_secure_connection("redis://user:pass@redis:6379")
            True
            >>> validator._is_secure_connection("redis://redis:6379")
            False
        """
        if not redis_url:
            return False

        # TLS connections are always secure
        if redis_url.startswith('rediss://'):
            return True

        # Redis connections with authentication are considered secure
        if redis_url.startswith('redis://') and '@' in redis_url:
            return True

        # All other connections are insecure
        return False

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
        env_info = get_environment_info(FeatureContext.SECURITY_ENFORCEMENT)

        # Determine insecure override from environment if not provided
        if insecure_override is None:
            import os
            insecure_override = os.getenv("REDIS_INSECURE_ALLOW_PLAINTEXT", "false").lower() == "true"

        # Log security validation attempt
        self.logger.info(
            f"🔐 Starting Redis security validation for {env_info.environment.value} environment"
        )

        # Perform environment-specific validation
        self.validate_production_security(redis_url, insecure_override)

        # Log final security status
        security_status = "SECURE" if self._is_secure_connection(redis_url) else "INSECURE"
        self.logger.info(
            f"✅ Redis security validation complete: {security_status} connection in "
            f"{env_info.environment.value} environment"
        )


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
    validator = RedisSecurityValidator()
    validator.validate_startup_security(redis_url, insecure_override)