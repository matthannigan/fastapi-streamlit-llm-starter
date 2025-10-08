#!/usr/bin/env python3
"""
Generate Secure Environment Configuration Script

This script generates environment-specific secure Redis configurations with:
- Environment-appropriate security settings (development, staging, production)
- Secure password and encryption key generation
- Configuration validation and strength checking
- Environment file creation with proper formatting

Usage:
    python scripts/generate-secure-env.py [options]

Options:
    --environment ENV    Target environment: development, staging, production (default: development)
    --output FILE        Output file path (default: .env.secure)
    --validate-only      Only validate existing configuration without generating
    --force              Overwrite existing file without confirmation
    --help               Show this help message

Examples:
    python scripts/generate-secure-env.py
    python scripts/generate-secure-env.py --environment production --output .env.production
    python scripts/generate-secure-env.py --validate-only --output .env
"""

import argparse
import os
import secrets
import string
import sys
from datetime import datetime, UTC
from enum import Enum
from pathlib import Path
from typing import Dict, Optional, Tuple

try:
    from cryptography.fernet import Fernet
    CRYPTOGRAPHY_AVAILABLE = True
except ImportError:
    print("Warning: cryptography library not available", file=sys.stderr)
    print("Install with: pip install cryptography", file=sys.stderr)
    CRYPTOGRAPHY_AVAILABLE = False


class Environment(Enum):
    """Supported environment types."""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"


class SecurityLevel:
    """Security configuration levels for different environments."""

    def __init__(self, environment: Environment):
        self.environment = environment
        self._configure()

    def _configure(self):
        """Configure security parameters based on environment."""
        if self.environment == Environment.PRODUCTION:
            self.password_length = 48
            self.min_password_entropy = 256
            self.certificate_validation = True
            self.tls_version = "1.3"
            self.description = "Production-grade security"
        elif self.environment == Environment.STAGING:
            self.password_length = 32
            self.min_password_entropy = 192
            self.certificate_validation = True
            self.tls_version = "1.2"
            self.description = "Staging security (production-like)"
        else:  # DEVELOPMENT
            self.password_length = 24
            self.min_password_entropy = 128
            self.certificate_validation = False
            self.tls_version = "1.2"
            self.description = "Development security"

    @property
    def cache_preset(self) -> str:
        """Get appropriate cache preset for environment."""
        if self.environment == Environment.PRODUCTION:
            return "ai-production"
        elif self.environment == Environment.STAGING:
            return "ai-staging"
        return "ai-development"

    @property
    def resilience_preset(self) -> str:
        """Get appropriate resilience preset for environment."""
        return self.environment.value

    @property
    def log_level(self) -> str:
        """Get appropriate log level for environment."""
        if self.environment == Environment.PRODUCTION:
            return "WARNING"
        elif self.environment == Environment.STAGING:
            return "INFO"
        return "DEBUG"


class SecurePasswordGenerator:
    """Generate cryptographically secure passwords."""

    # Character sets for password generation
    LOWERCASE = string.ascii_lowercase
    UPPERCASE = string.ascii_uppercase
    DIGITS = string.digits
    SPECIAL = "!@#$%^&*-_=+"

    @classmethod
    def generate(cls, length: int = 32, include_special: bool = True) -> str:
        """
        Generate a cryptographically secure random password.

        Args:
            length: Password length (default: 32)
            include_special: Include special characters (default: True)

        Returns:
            Secure random password string
        """
        # Build character set
        chars = cls.LOWERCASE + cls.UPPERCASE + cls.DIGITS
        if include_special:
            chars += cls.SPECIAL

        # Ensure minimum complexity (at least one of each character type)
        password = [
            secrets.choice(cls.LOWERCASE),
            secrets.choice(cls.UPPERCASE),
            secrets.choice(cls.DIGITS),
        ]

        if include_special:
            password.append(secrets.choice(cls.SPECIAL))

        # Fill remaining length
        password.extend(secrets.choice(chars) for _ in range(length - len(password)))

        # Shuffle to randomize positions
        secrets.SystemRandom().shuffle(password)

        return ''.join(password)

    @classmethod
    def calculate_entropy(cls, password: str) -> float:
        """
        Calculate password entropy in bits.

        Args:
            password: Password to analyze

        Returns:
            Entropy in bits
        """
        charset_size = 0

        if any(c in cls.LOWERCASE for c in password):
            charset_size += len(cls.LOWERCASE)
        if any(c in cls.UPPERCASE for c in password):
            charset_size += len(cls.UPPERCASE)
        if any(c in cls.DIGITS for c in password):
            charset_size += len(cls.DIGITS)
        if any(c in cls.SPECIAL for c in password):
            charset_size += len(cls.SPECIAL)

        import math
        return len(password) * math.log2(charset_size) if charset_size > 0 else 0

    @classmethod
    def validate_strength(cls, password: str, min_length: int = 16, min_entropy: int = 128) -> Tuple[bool, str]:
        """
        Validate password strength.

        Args:
            password: Password to validate
            min_length: Minimum password length
            min_entropy: Minimum entropy in bits

        Returns:
            Tuple of (is_valid, message)
        """
        if len(password) < min_length:
            return False, f"Password too short (minimum {min_length} characters)"

        entropy = cls.calculate_entropy(password)
        if entropy < min_entropy:
            return False, f"Password entropy too low ({entropy:.1f} bits, minimum {min_entropy} bits)"

        has_lower = any(c in cls.LOWERCASE for c in password)
        has_upper = any(c in cls.UPPERCASE for c in password)
        has_digit = any(c in cls.DIGITS for c in password)

        if not (has_lower and has_upper and has_digit):
            return False, "Password must contain lowercase, uppercase, and digits"

        return True, f"Password strength: {entropy:.1f} bits entropy"


class EncryptionKeyGenerator:
    """Generate and validate Fernet encryption keys."""

    @staticmethod
    def generate() -> str:
        """
        Generate a Fernet encryption key.

        Returns:
            Base64-encoded Fernet key
        """
        if not CRYPTOGRAPHY_AVAILABLE:
            # Fallback to basic base64 encoding
            import base64
            return base64.urlsafe_b64encode(os.urandom(32)).decode()

        return Fernet.generate_key().decode()

    @staticmethod
    def validate(key: str) -> Tuple[bool, str]:
        """
        Validate a Fernet encryption key.

        Args:
            key: Encryption key to validate

        Returns:
            Tuple of (is_valid, message)
        """
        if not CRYPTOGRAPHY_AVAILABLE:
            return True, "Validation skipped (cryptography library not available)"

        try:
            Fernet(key.encode())
            return True, "Encryption key is valid"
        except Exception as e:
            return False, f"Invalid encryption key: {str(e)}"


class EnvironmentConfigGenerator:
    """Generate environment configuration files."""

    def __init__(self, environment: Environment, output_file: Path):
        self.environment = environment
        self.output_file = output_file
        self.security = SecurityLevel(environment)

    def generate(self, force: bool = False) -> bool:
        """
        Generate environment configuration file.

        Args:
            force: Overwrite existing file without confirmation

        Returns:
            True if successful, False otherwise
        """
        # Check if file exists
        if self.output_file.exists() and not force:
            response = input(f"File {self.output_file} already exists. Overwrite? [y/N]: ")
            if response.lower() != 'y':
                print("❌ Generation cancelled")
                return False

            # Create backup
            backup_file = self.output_file.with_suffix(
                f".backup.{datetime.now().strftime('%Y%m%d_%H%M%S')}"
            )
            self.output_file.rename(backup_file)
            print(f"✅ Backup created: {backup_file}")

        # Generate secure credentials
        redis_password = SecurePasswordGenerator.generate(
            length=self.security.password_length,
            include_special=True
        )
        encryption_key = EncryptionKeyGenerator.generate()
        api_key = SecurePasswordGenerator.generate(length=32)

        # Get project root
        project_root = Path(__file__).parent.parent
        cert_dir = project_root / "certs"

        # Generate configuration content
        config_content = self._generate_config_content(
            redis_password=redis_password,
            encryption_key=encryption_key,
            api_key=api_key,
            cert_dir=cert_dir
        )

        # Write configuration file
        try:
            self.output_file.write_text(config_content)
            self.output_file.chmod(0o600)  # Read/write for owner only
            print(f"✅ Configuration generated: {self.output_file}")
            print(f"   Environment: {self.environment.value}")
            print(f"   Security Level: {self.security.description}")
            return True
        except Exception as e:
            print(f"❌ Failed to write configuration: {e}", file=sys.stderr)
            return False

    def _generate_config_content(
        self,
        redis_password: str,
        encryption_key: str,
        api_key: str,
        cert_dir: Path
    ) -> str:
        """Generate configuration file content."""
        return f"""# Secure Redis Environment Configuration
# Generated: {datetime.now(UTC).strftime('%Y-%m-%d %H:%M:%S UTC')}
# Environment: {self.environment.value}
# Security Level: {self.security.description}
#
# IMPORTANT: This file contains sensitive credentials
# - Do not commit to version control
# - Keep file permissions restrictive (600)
# - Rotate credentials regularly

# Redis Connection Settings
REDIS_URL=rediss://localhost:6380
REDIS_PASSWORD={redis_password}
REDIS_TLS_ENABLED=true
REDIS_TLS_CERT_PATH={cert_dir}/redis.crt
REDIS_TLS_KEY_PATH={cert_dir}/redis.key
REDIS_TLS_CA_PATH={cert_dir}/ca.crt
REDIS_VERIFY_CERTIFICATES={'true' if self.security.certificate_validation else 'false'}

# Data Encryption Settings
REDIS_ENCRYPTION_KEY={encryption_key}

# Application Settings
NODE_ENV={self.environment.value}
API_KEY={api_key}

# Cache Configuration
CACHE_PRESET={self.security.cache_preset}

# Resilience Configuration
RESILIENCE_PRESET={self.security.resilience_preset}

# Security Settings
CORS_ALLOWED_ORIGINS=http://localhost:3000,http://localhost:8501,http://localhost:8000
LOG_LEVEL={self.security.log_level}

# Docker Configuration
COMPOSE_PROJECT_NAME=secure_redis_stack_{self.environment.value}
"""


class ConfigurationValidator:
    """Validate existing configuration files."""

    def __init__(self, config_file: Path):
        self.config_file = config_file
        self.config: Dict[str, str] = {}
        self.errors: list = []
        self.warnings: list = []

    def validate(self) -> bool:
        """
        Validate configuration file.

        Returns:
            True if valid, False otherwise
        """
        if not self.config_file.exists():
            self.errors.append(f"Configuration file not found: {self.config_file}")
            return False

        # Load configuration
        self._load_config()

        # Validate required fields
        self._validate_required_fields()

        # Validate security settings
        self._validate_security_settings()

        # Validate file permissions
        self._validate_file_permissions()

        # Print results
        self._print_validation_results()

        return len(self.errors) == 0

    def _load_config(self):
        """Load configuration from file."""
        try:
            with open(self.config_file, 'r') as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        if '=' in line:
                            key, value = line.split('=', 1)
                            self.config[key.strip()] = value.strip()
        except Exception as e:
            self.errors.append(f"Failed to load configuration: {e}")

    def _validate_required_fields(self):
        """Validate required configuration fields."""
        required_fields = [
            'REDIS_URL',
            'REDIS_PASSWORD',
            'REDIS_ENCRYPTION_KEY',
            'REDIS_TLS_ENABLED',
        ]

        for field in required_fields:
            if field not in self.config:
                self.errors.append(f"Missing required field: {field}")

    def _validate_security_settings(self):
        """Validate security-related settings."""
        # Validate Redis URL
        redis_url = self.config.get('REDIS_URL', '')
        if not redis_url.startswith('rediss://'):
            self.errors.append("REDIS_URL must use TLS (rediss://)")

        # Validate password strength
        redis_password = self.config.get('REDIS_PASSWORD', '')
        if redis_password:
            is_valid, message = SecurePasswordGenerator.validate_strength(
                redis_password,
                min_length=16,
                min_entropy=128
            )
            if not is_valid:
                self.errors.append(f"Redis password: {message}")
            elif "entropy" in message:
                self.warnings.append(f"Redis password: {message}")

        # Validate encryption key
        encryption_key = self.config.get('REDIS_ENCRYPTION_KEY', '')
        if encryption_key:
            is_valid, message = EncryptionKeyGenerator.validate(encryption_key)
            if not is_valid:
                self.errors.append(f"Encryption key: {message}")

        # Validate TLS settings
        tls_enabled = self.config.get('REDIS_TLS_ENABLED', '').lower()
        if tls_enabled != 'true':
            self.errors.append("REDIS_TLS_ENABLED must be 'true'")

        # Check certificate paths
        cert_paths = [
            'REDIS_TLS_CERT_PATH',
            'REDIS_TLS_KEY_PATH',
            'REDIS_TLS_CA_PATH',
        ]
        for path_key in cert_paths:
            cert_path = self.config.get(path_key, '')
            if cert_path:
                if not Path(cert_path).exists():
                    self.warnings.append(f"{path_key}: File not found: {cert_path}")

    def _validate_file_permissions(self):
        """Validate configuration file permissions."""
        try:
            stat_info = self.config_file.stat()
            mode = stat_info.st_mode & 0o777

            if mode != 0o600:
                self.warnings.append(
                    f"File permissions are {oct(mode)} (should be 0600 for security)"
                )
        except Exception as e:
            self.warnings.append(f"Could not check file permissions: {e}")

    def _print_validation_results(self):
        """Print validation results."""
        print(f"\n🔍 Configuration Validation: {self.config_file}")
        print("=" * 60)

        if self.errors:
            print("\n❌ Errors:")
            for error in self.errors:
                print(f"   • {error}")

        if self.warnings:
            print("\n⚠️  Warnings:")
            for warning in self.warnings:
                print(f"   • {warning}")

        if not self.errors and not self.warnings:
            print("\n✅ Configuration is valid!")
        elif not self.errors:
            print("\n✅ Configuration is valid (with warnings)")
        else:
            print("\n❌ Configuration validation failed")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Generate secure environment configuration for Redis",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__
    )

    parser.add_argument(
        '--environment',
        type=str,
        choices=[e.value for e in Environment],
        default='development',
        help='Target environment (default: development)'
    )

    parser.add_argument(
        '--output',
        type=Path,
        default=Path('.env.secure'),
        help='Output file path (default: .env.secure)'
    )

    parser.add_argument(
        '--validate-only',
        action='store_true',
        help='Only validate existing configuration without generating'
    )

    parser.add_argument(
        '--force',
        action='store_true',
        help='Overwrite existing file without confirmation'
    )

    args = parser.parse_args()

    print("🔐 Secure Environment Configuration Generator")
    print("=" * 60)

    if args.validate_only:
        # Validate existing configuration
        validator = ConfigurationValidator(args.output)
        success = validator.validate()
        sys.exit(0 if success else 1)
    else:
        # Generate new configuration
        environment = Environment(args.environment)
        generator = EnvironmentConfigGenerator(environment, args.output)
        success = generator.generate(force=args.force)
        sys.exit(0 if success else 1)


if __name__ == '__main__':
    main()