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

from app.core.environment import (Environment, FeatureContext,
                                  get_environment_info)
from app.core.exceptions import ConfigurationError

logger = logging.getLogger(__name__)


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

    is_valid: bool
    tls_status: str
    encryption_status: str
    auth_status: str
    connectivity_status: str
    warnings: List[str] = field(default_factory=list)
    errors: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    certificate_info: Optional[Dict[str, Any]] = None

    def summary(self) -> str:
        """Generate human-readable validation summary."""
        lines = ["━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━"]
        lines.append("🔒 Redis Security Validation Report")
        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")
        lines.append("")

        status_icon = "✅" if self.is_valid else "❌"
        lines.append(
            f"{status_icon} Overall Status: {'PASSED' if self.is_valid else 'FAILED'}"
        )
        lines.append("")

        lines.append("Security Components:")
        lines.append(f"  • TLS/SSL:     {self.tls_status}")
        lines.append(f"  • Encryption:  {self.encryption_status}")
        lines.append(f"  • Auth:        {self.auth_status}")
        lines.append(f"  • Connectivity: {self.connectivity_status}")

        if self.certificate_info:
            lines.append("")
            lines.append("Certificate Information:")
            for key, value in self.certificate_info.items():
                lines.append(f"  • {key}: {value}")

        if self.errors:
            lines.append("")
            lines.append("❌ Errors:")
            for error in self.errors:
                lines.append(f"  • {error}")

        if self.warnings:
            lines.append("")
            lines.append("⚠️  Warnings:")
            for warning in self.warnings:
                lines.append(f"  • {warning}")

        if self.recommendations:
            lines.append("")
            lines.append("💡 Recommendations:")
            for rec in self.recommendations:
                lines.append(f"  • {rec}")

        lines.append("━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━")

        return "\n".join(lines)


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

    def validate_production_security(
        self, redis_url: Optional[str], insecure_override: bool = False
    ) -> None:
        """
        Validate Redis security for production environments.

        This method enforces TLS encryption and authentication requirements in
        production while allowing development flexibility. It provides clear
        error messages and configuration guidance when security requirements
        are not met.

        Args:
            redis_url: Redis connection string to validate. Must not be None or empty.
            insecure_override: Explicit override to allow insecure connections
                             in production (logs prominent security warning)

        Raises:
            ConfigurationError: If redis_url is None/empty, or if production environment
                              lacks required security and no explicit override is provided

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
        # Defensive validation - fail fast with clear error message
        if not redis_url:
            raise ConfigurationError(
                "🔒 CONFIGURATION ERROR: Redis URL is required for security validation\n"
                "\n"
                "The Redis connection URL must be provided and cannot be empty.\n"
                "This typically indicates a missing or incorrectly configured environment variable.\n"
                "\n"
                "🔧 How to fix this:\n"
                "\n"
                "  1. Set the REDIS_URL environment variable:\n"
                "     export REDIS_URL='redis://localhost:6379'  # Development\n"
                "     export REDIS_URL='rediss://redis:6380'     # Production (TLS)\n"
                "\n"
                "  2. Verify environment variable is loaded:\n"
                "     echo $REDIS_URL\n"
                "\n"
                "  3. Check your .env file or environment configuration\n"
                "\n"
                "📚 Documentation:\n"
                "   • Environment variables: docs/get-started/ENVIRONMENT_VARIABLES.md\n"
                "   • Cache setup: docs/guides/infrastructure/CACHE.md\n",
                context={
                    "redis_url": redis_url,
                    "validation_type": "production_security",
                    "required_fix": "set_redis_url",
                },
            )

        env_info = get_environment_info(FeatureContext.SECURITY_ENFORCEMENT)

        # Only enforce TLS in production environments
        if env_info.environment != Environment.PRODUCTION:
            # Graduated messaging for non-production environments
            if env_info.environment == Environment.DEVELOPMENT:
                self.logger.info(
                    f"ℹ️  Development environment detected - TLS validation skipped\n"
                    f"   Security flexibility enabled for local development.\n"
                    f"   💡 Tip: Use './scripts/init-redis-tls.sh' to test with TLS locally"
                )
            else:
                self.logger.info(
                    f"ℹ️  {env_info.environment.value.title()} environment - TLS validation skipped\n"
                    f"   Using flexible security for {env_info.environment.value} environment."
                )
            return

        # Check for explicit insecure override in production
        if insecure_override:
            self.logger.warning(
                "🚨 SECURITY WARNING: Running with insecure Redis connection in production!\n"
                "\n"
                "⚠️  REDIS_INSECURE_ALLOW_PLAINTEXT=true detected\n"
                "\n"
                "This override should ONLY be used in highly secure, isolated network environments where:\n"
                "  ✓ Network traffic is encrypted at the infrastructure level (e.g., VPN, service mesh)\n"
                "  ✓ Redis access is restricted to authorized services only via firewall rules\n"
                "  ✓ Network monitoring and intrusion detection systems are in place\n"
                "  ✓ Physical network access is strictly controlled\n"
                "\n"
                "🔐 Strong Recommendation: Use TLS encryption (rediss://) for maximum security\n"
                "\n"
                "📚 Documentation: docs/guides/infrastructure/CACHE.md#security\n"
                "🛠️  Quick TLS setup: ./scripts/init-redis-tls.sh"
            )
            return

        # Validate TLS usage in production - provide detailed guidance
        if not self._is_secure_connection(redis_url):
            connection_type = (
                redis_url.split("://")[0] if "://" in redis_url else "unknown"
            )

            raise ConfigurationError(
                "🔒 SECURITY ERROR: Production environment requires secure Redis connection\n"
                "\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                f"❌ Current: Insecure connection ({connection_type}://)\n"
                "✅ Required: TLS-enabled (rediss://) or authenticated connection\n"
                "━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━\n"
                "\n"
                "🔧 How to fix this:\n"
                "\n"
                "  Option 1: Use TLS Connection (Recommended)\n"
                "  ─────────────────────────────────────────\n"
                "  1. Change REDIS_URL to use TLS scheme:\n"
                "     export REDIS_URL='rediss://your-redis-host:6380'\n"
                "\n"
                "  2. Ensure TLS certificates are configured:\n"
                "     export REDIS_TLS_CERT_PATH='/path/to/client.crt'\n"
                "     export REDIS_TLS_KEY_PATH='/path/to/client.key'\n"
                "     export REDIS_TLS_CA_PATH='/path/to/ca.crt'\n"
                "\n"
                "  Option 2: Development/Testing TLS Setup\n"
                "  ────────────────────────────────────────\n"
                "  Run the automated TLS setup script:\n"
                "     ./scripts/init-redis-tls.sh\n"
                "     docker-compose -f docker-compose.secure.yml up -d\n"
                "\n"
                "  Option 3: Secure Internal Network Override (Use with caution)\n"
                "  ──────────────────────────────────────────────────────────────\n"
                "  If your network infrastructure provides encryption:\n"
                "     export REDIS_INSECURE_ALLOW_PLAINTEXT=true\n"
                "\n"
                "  ⚠️  WARNING: Only use this in secured internal networks with:\n"
                "     • Infrastructure-level encryption (VPN/service mesh)\n"
                "     • Strict firewall rules limiting Redis access\n"
                "     • Network monitoring and intrusion detection\n"
                "\n"
                "📚 Detailed Documentation:\n"
                "   • Security guide: docs/guides/infrastructure/CACHE.md#security\n"
                "   • TLS setup: docs/guides/infrastructure/CACHE.md#tls-configuration\n"
                "   • Environment variables: docs/get-started/ENVIRONMENT_VARIABLES.md\n"
                "\n"
                "🌍 Environment Information:\n"
                f"   • Detected: {env_info.environment.value} (confidence: {env_info.confidence:.1%})\n"
                f"   • Redis URL: {redis_url}\n",
                context={
                    "redis_url": redis_url,
                    "connection_type": connection_type,
                    "environment": env_info.environment.value,
                    "confidence": env_info.confidence,
                    "validation_type": "production_security",
                    "required_fix": "tls_connection",
                    "fix_options": [
                        "tls_connection",
                        "automated_setup",
                        "insecure_override",
                    ],
                },
            )

        # Success message - provide security confirmation
        self.logger.info(
            f"✅ Redis security validation passed\n"
            f"   • Environment: {env_info.environment.value}\n"
            f"   • Connection: Secure (TLS/authenticated)\n"
            f"   • Validation: Production security requirements met"
        )

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
        if redis_url.startswith("rediss://"):
            return True

        # Redis connections with authentication are considered secure
        if redis_url.startswith("redis://") and "@" in redis_url:
            return True

        # All other connections are insecure
        return False

    def validate_tls_certificates(
        self,
        cert_path: Optional[str] = None,
        key_path: Optional[str] = None,
        ca_path: Optional[str] = None,
    ) -> Dict[str, Any]:
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
        result = {"valid": True, "errors": [], "warnings": [], "cert_info": {}}

        # Check certificate file existence
        if cert_path:
            cert_file = Path(cert_path)
            if not cert_file.exists():
                result["valid"] = False
                result["errors"].append(f"Certificate file not found: {cert_path}")
            elif not cert_file.is_file():
                result["valid"] = False
                result["errors"].append(f"Certificate path is not a file: {cert_path}")
            else:
                result["cert_info"]["cert_path"] = str(cert_file.absolute())

                # Try to read certificate expiration (requires cryptography library)
                try:
                    from cryptography import x509
                    from cryptography.hazmat.backends import default_backend

                    with open(cert_file, "rb") as f:
                        cert_data = f.read()
                        cert = x509.load_pem_x509_certificate(
                            cert_data, default_backend()
                        )

                        expiration = (
                            cert.not_valid_after_utc
                            if hasattr(cert, "not_valid_after_utc")
                            else cert.not_valid_after
                        )
                        result["cert_info"]["expires"] = expiration.isoformat()

                        # Check expiration warnings
                        days_until_expiry = (
                            expiration.replace(tzinfo=None) - datetime.utcnow()
                        ).days
                        result["cert_info"]["days_until_expiry"] = days_until_expiry

                        if days_until_expiry < 0:
                            result["valid"] = False
                            result["errors"].append(
                                f"Certificate expired {-days_until_expiry} days ago"
                            )
                        elif days_until_expiry < 30:
                            result["warnings"].append(
                                f"Certificate expires in {days_until_expiry} days - renewal recommended"
                            )
                        elif days_until_expiry < 90:
                            result["warnings"].append(
                                f"Certificate expires in {days_until_expiry} days"
                            )

                        # Get subject information
                        subject = cert.subject
                        result["cert_info"]["subject"] = subject.rfc4514_string()

                except ImportError:
                    result["warnings"].append(
                        "cryptography library not available - certificate validation limited"
                    )
                except Exception as e:
                    result["warnings"].append(f"Could not parse certificate: {str(e)}")

        # Check key file existence
        if key_path:
            key_file = Path(key_path)
            if not key_file.exists():
                result["valid"] = False
                result["errors"].append(f"Private key file not found: {key_path}")
            elif not key_file.is_file():
                result["valid"] = False
                result["errors"].append(f"Private key path is not a file: {key_path}")
            else:
                result["cert_info"]["key_path"] = str(key_file.absolute())

        # Check CA file existence
        if ca_path:
            ca_file = Path(ca_path)
            if not ca_file.exists():
                result["valid"] = False
                result["errors"].append(f"CA certificate file not found: {ca_path}")
            elif not ca_file.is_file():
                result["valid"] = False
                result["errors"].append(f"CA certificate path is not a file: {ca_path}")
            else:
                result["cert_info"]["ca_path"] = str(ca_file.absolute())

        return result

    def validate_encryption_key(
        self, encryption_key: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Validate encryption key format and strength.

        Args:
            encryption_key: Fernet encryption key to validate

        Returns:
            Dictionary with validation results

        Examples:
            result = validator.validate_encryption_key("your-fernet-key")
        """
        result = {"valid": True, "errors": [], "warnings": [], "key_info": {}}

        if not encryption_key:
            result["valid"] = False
            result["errors"].append("No encryption key provided")
            result["warnings"].append(
                "Data encryption is disabled - not recommended for production"
            )
            return result

        # Check key format (Fernet keys are 44 characters base64-encoded)
        if len(encryption_key) != 44:
            result["valid"] = False
            result["errors"].append(
                f"Invalid encryption key length: {len(encryption_key)} (expected 44 characters for Fernet key)"
            )
            return result

        # Try to validate with cryptography library
        try:
            from cryptography.fernet import Fernet

            # Attempt to create Fernet instance
            if isinstance(encryption_key, str):
                key_bytes = encryption_key.encode("utf-8")
            else:
                key_bytes = encryption_key

            fernet = Fernet(key_bytes)

            # Test encryption/decryption
            test_data = b"validation_test"
            encrypted = fernet.encrypt(test_data)
            decrypted = fernet.decrypt(encrypted)

            if decrypted != test_data:
                result["valid"] = False
                result["errors"].append(
                    "Encryption key validation failed - encrypt/decrypt test failed"
                )
            else:
                result["key_info"]["format"] = "Fernet (AES-128-CBC with HMAC)"
                result["key_info"]["length"] = "256-bit"
                result["key_info"]["status"] = "Valid and functional"

        except ImportError:
            result["valid"] = False
            result["errors"].append(
                "cryptography library not available - encryption key cannot be validated"
            )
        except Exception as e:
            result["valid"] = False
            result["errors"].append(f"Invalid encryption key: {str(e)}")

        return result

    def validate_redis_auth(
        self, redis_url: str, auth_password: Optional[str] = None
    ) -> Dict[str, Any]:
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
        result = {"valid": True, "errors": [], "warnings": [], "auth_info": {}}

        # Check if URL contains authentication
        has_auth_in_url = "@" in redis_url and "://" in redis_url

        if has_auth_in_url:
            result["auth_info"]["method"] = "URL-embedded credentials"
            result["auth_info"]["status"] = "Present"

            # Extract username/password if present
            try:
                url_parts = redis_url.split("://", 1)[1]
                if "@" in url_parts:
                    auth_part = url_parts.split("@")[0]
                    if ":" in auth_part:
                        username, password = auth_part.split(":", 1)
                        result["auth_info"]["username"] = (
                            username if username else "(default)"
                        )

                        # Check password strength
                        if len(password) < 16:
                            result["warnings"].append(
                                f"Weak password detected ({len(password)} chars) - recommend 16+ characters"
                            )
                    else:
                        result["auth_info"]["password_only"] = True
            except Exception as e:
                result["warnings"].append(
                    f"Could not parse authentication from URL: {str(e)}"
                )

        elif auth_password:
            result["auth_info"]["method"] = "Separate password configuration"
            result["auth_info"]["status"] = "Present"

            # Check password strength
            if len(auth_password) < 16:
                result["warnings"].append(
                    f"Weak password detected ({len(auth_password)} chars) - recommend 16+ characters"
                )
        else:
            env_info = get_environment_info(FeatureContext.SECURITY_ENFORCEMENT)
            if env_info.environment == Environment.PRODUCTION:
                result["valid"] = False
                result["errors"].append(
                    "No authentication configured for production environment"
                )
            else:
                result["warnings"].append(
                    "No authentication configured - acceptable for development only"
                )
            result["auth_info"]["status"] = "Missing"

        return result

    def validate_security_configuration(
        self,
        redis_url: Optional[str],
        encryption_key: Optional[str] = None,
        tls_cert_path: Optional[str] = None,
        tls_key_path: Optional[str] = None,
        tls_ca_path: Optional[str] = None,
        auth_password: Optional[str] = None,
        test_connectivity: bool = False,
    ) -> SecurityValidationResult:
        """
        Perform comprehensive security configuration validation.

        This method validates all aspects of Redis security configuration including
        TLS, encryption, authentication, and optionally connectivity testing.

        Args:
            redis_url: Redis connection URL. Must not be None or empty.
            encryption_key: Fernet encryption key
            tls_cert_path: Path to TLS client certificate
            tls_key_path: Path to TLS private key
            tls_ca_path: Path to TLS CA certificate
            auth_password: Redis authentication password
            test_connectivity: Whether to test actual Redis connectivity

        Returns:
            SecurityValidationResult with detailed validation information

        Raises:
            ConfigurationError: If redis_url is None or empty

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
        # Defensive validation - fail fast with clear error message
        if not redis_url:
            raise ConfigurationError(
                "🔒 CONFIGURATION ERROR: Redis URL is required for security validation\n"
                "\n"
                "The Redis connection URL must be provided and cannot be empty.\n"
                "\n"
                "📚 Documentation:\n"
                "   • Environment variables: docs/get-started/ENVIRONMENT_VARIABLES.md\n"
                "   • Cache setup: docs/guides/infrastructure/CACHE.md\n",
                context={
                    "redis_url": redis_url,
                    "validation_type": "security_configuration",
                    "required_fix": "set_redis_url",
                },
            )

        env_info = get_environment_info(FeatureContext.SECURITY_ENFORCEMENT)

        # Validate TLS
        tls_result = self.validate_tls_certificates(
            tls_cert_path, tls_key_path, tls_ca_path
        )
        tls_status = "✅ Valid" if tls_result["valid"] else "❌ Invalid"

        if redis_url.startswith("rediss://"):
            if not tls_result["valid"]:
                tls_status = "⚠️  TLS URL but certificate issues"
        elif redis_url.startswith("redis://"):
            if env_info.environment == Environment.PRODUCTION:
                tls_status = "❌ No TLS in production"
            else:
                tls_status = "⚠️  No TLS (dev mode)"

        # Validate encryption
        encryption_result = self.validate_encryption_key(encryption_key)
        encryption_status = "✅ Valid" if encryption_result["valid"] else "❌ Invalid"

        # Validate authentication
        auth_result = self.validate_redis_auth(redis_url, auth_password)
        auth_status = "✅ Configured" if auth_result["valid"] else "❌ Missing"

        # Connectivity status (placeholder for actual test)
        connectivity_status = (
            "⏭️  Skipped" if not test_connectivity else "⚠️  Not implemented"
        )

        # Collect all warnings and errors
        all_warnings = []
        all_errors = []
        recommendations = []

        all_warnings.extend(tls_result.get("warnings", []))
        all_warnings.extend(encryption_result.get("warnings", []))
        all_warnings.extend(auth_result.get("warnings", []))

        all_errors.extend(tls_result.get("errors", []))
        all_errors.extend(encryption_result.get("errors", []))
        all_errors.extend(auth_result.get("errors", []))

        # Generate recommendations
        if (
            not redis_url.startswith("rediss://")
            and env_info.environment == Environment.PRODUCTION
        ):
            recommendations.append("Use TLS (rediss://) for production deployments")

        if not encryption_result["valid"]:
            recommendations.append(
                "Enable encryption with REDIS_ENCRYPTION_KEY environment variable"
            )

        if not auth_result["valid"]:
            recommendations.append(
                "Configure Redis authentication with strong password"
            )

        if tls_result.get("cert_info", {}).get("days_until_expiry", 365) < 90:
            recommendations.append("Plan certificate renewal soon")

        # Determine overall validity
        is_valid = len(all_errors) == 0

        # Build certificate info
        cert_info = None
        if tls_result.get("cert_info"):
            cert_info = tls_result["cert_info"]

        return SecurityValidationResult(
            is_valid=is_valid,
            tls_status=tls_status,
            encryption_status=encryption_status,
            auth_status=auth_status,
            connectivity_status=connectivity_status,
            warnings=all_warnings,
            errors=all_errors,
            recommendations=recommendations,
            certificate_info=cert_info,
        )

    def validate_startup_security(
        self, redis_url: Optional[str], insecure_override: Optional[bool] = None
    ) -> None:
        """
        Comprehensive Redis security validation for application startup.

        This is the main entry point for startup security validation. It performs
        environment-aware security validation and provides clear feedback on
        security status.

        Args:
            redis_url: Redis connection string to validate. Must not be None or empty.
            insecure_override: Optional explicit override for insecure connections
                             If None, will be determined from environment variables

        Raises:
            ConfigurationError: If redis_url is None/empty, or if security requirements are not met

        Examples:
            # Standard startup validation
            validator.validate_startup_security("rediss://redis:6380")

            # With explicit override
            validator.validate_startup_security("redis://redis:6379", insecure_override=True)
        """
        env_info = get_environment_info(FeatureContext.SECURITY_ENFORCEMENT)

        # Determine insecure override from environment if not provided
        if insecure_override is None:
            insecure_override = (
                os.getenv("REDIS_INSECURE_ALLOW_PLAINTEXT", "false").lower() == "true"
            )

        # Log security validation attempt
        self.logger.info(
            f"🔐 Starting Redis security validation for {env_info.environment.value} environment"
        )

        # Perform environment-specific validation
        self.validate_production_security(redis_url, insecure_override)

        # Perform comprehensive validation and log report
        encryption_key = os.getenv("REDIS_ENCRYPTION_KEY")
        tls_cert_path = os.getenv("REDIS_TLS_CERT_PATH")
        tls_key_path = os.getenv("REDIS_TLS_KEY_PATH")
        tls_ca_path = os.getenv("REDIS_TLS_CA_PATH")
        auth_password = os.getenv("REDIS_PASSWORD")

        validation_result = self.validate_security_configuration(
            redis_url=redis_url,
            encryption_key=encryption_key,
            tls_cert_path=tls_cert_path,
            tls_key_path=tls_key_path,
            tls_ca_path=tls_ca_path,
            auth_password=auth_password,
            test_connectivity=False,
        )

        # Log validation summary
        self.logger.info(f"\n{validation_result.summary()}")

        # Log final security status
        security_status = (
            "SECURE" if self._is_secure_connection(redis_url) else "INSECURE"
        )
        self.logger.info(
            f"✅ Redis security validation complete: {security_status} connection in "
            f"{env_info.environment.value} environment"
        )


def validate_redis_security(
    redis_url: Optional[str], insecure_override: Optional[bool] = None
) -> None:
    """
    Convenience function for Redis security validation.

    This function provides a simple interface for startup security validation
    without requiring explicit validator instantiation.

    Args:
        redis_url: Redis connection string to validate. Must not be None or empty.
        insecure_override: Optional explicit override for insecure connections

    Raises:
        ConfigurationError: If redis_url is None/empty, or if security requirements are not met

    Examples:
        # Simple validation
        validate_redis_security("rediss://redis:6380")

        # With override
        validate_redis_security("redis://redis:6379", insecure_override=True)
    """
    validator = RedisSecurityValidator()
    validator.validate_startup_security(redis_url, insecure_override)
