"""
Enhanced configuration management with builder pattern and environment presets.

This module provides comprehensive cache configuration management using a fluent
builder pattern. It supports environment variable loading, validation, AI-specific
configurations, and preset configurations for different deployment environments.

## Classes

- **ValidationResult**: Validation results with detailed errors and warnings
- **CacheConfig**: Main configuration dataclass with comprehensive cache settings
- **AICacheConfig**: AI-specific configuration extensions
- **CacheConfigBuilder**: Builder pattern for flexible configuration construction
- **EnvironmentPresets**: Pre-configured settings for common environments

## Key Features

- **Builder Pattern**: Fluent interface for readable configuration construction
- **Environment Loading**: Automatic detection and loading from environment variables
- **Validation**: Comprehensive validation with detailed error reporting
- **AI Extensions**: Specialized settings for AI workloads and text processing
- **Environment Presets**: Pre-tested configurations for dev/test/prod environments
- **File Operations**: JSON serialization for configuration persistence

## Usage

```python
# Environment-based configuration
config = CacheConfigBuilder().for_environment("development").build()

# AI application configuration
config = (CacheConfigBuilder()
    .for_environment("production")
        ...     .with_redis("redis://prod:6379")
        ...     .with_ai_features(text_hash_threshold=2000)
        ...     .build())

    Environment-based configuration:
        >>> config = CacheConfigBuilder().from_environment().build()

    File-based configuration:
        >>> config = CacheConfigBuilder().from_file("cache_config.json").build()
"""

import hashlib
import json
import logging
from dataclasses import dataclass, field, asdict
from pathlib import Path
from typing import Any, Dict, List, Optional, Union

from app.core.exceptions import ConfigurationError, ValidationError

logger = logging.getLogger(__name__)


# ============================================================================
# Core Configuration Classes
# ============================================================================

@dataclass
class ValidationResult:
    """
    Result of configuration validation containing validation status and details.

    Attributes:
        is_valid: Whether the configuration passed validation
        errors: List of error messages that prevent successful operation
        warnings: List of warning messages for non-critical issues
    """
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

    def add_error(self, message: str) -> None:
        """Add an error message and mark validation as invalid."""
        self.errors.append(message)
        self.is_valid = False

    def add_warning(self, message: str) -> None:
        """Add a warning message."""
        self.warnings.append(message)


@dataclass
class AICacheConfig:
    """
    AI-specific cache configuration settings.

    This configuration extends the basic cache with AI-specific features like
    text hashing, operation-specific TTLs, and intelligent caching strategies.

    Attributes:
        text_hash_threshold: Text length threshold for enabling hashing (default: 1000)
        hash_algorithm: Hash algorithm to use for text content (default: "sha256")
        text_size_tiers: Size tiers for different caching strategies
        operation_ttls: TTL values for specific AI operations
        enable_smart_promotion: Whether to enable smart cache promotion (default: True)
        max_text_length: Maximum text length to cache (default: 100000)
    """
    text_hash_threshold: int = 1000
    hash_algorithm: str = "sha256"
    text_size_tiers: Dict[str, int] = field(default_factory=lambda: {
        "small": 1000,
        "medium": 10000,
        "large": 100000
    })
    operation_ttls: Dict[str, int] = field(default_factory=lambda: {
        "summarize": 7200,  # 2 hours
        "sentiment": 3600,  # 1 hour
        "key_points": 5400,  # 1.5 hours
        "questions": 4800,  # 1.33 hours
        "qa": 3600         # 1 hour
    })
    enable_smart_promotion: bool = True
    max_text_length: int = 100000

    def validate(self) -> ValidationResult:
        """
        Validate AI configuration settings.

        Returns:
            ValidationResult with any errors or warnings found
        """
        result = ValidationResult(is_valid=True)

        # Validate text_hash_threshold
        if self.text_hash_threshold <= 0:
            result.add_error("text_hash_threshold must be positive")

        # Validate text_size_tiers
        for tier_name, size in self.text_size_tiers.items():
            if not isinstance(size, int) or size <= 0:
                result.add_error(f"text_size_tiers['{tier_name}'] must be a positive integer")

        # Check tier progression (should be ascending)
        tier_values = list(self.text_size_tiers.values())
        if tier_values != sorted(tier_values):
            result.add_warning("text_size_tiers values should be in ascending order")

        # Validate operation_ttls
        for operation, ttl in self.operation_ttls.items():
            if not isinstance(ttl, int) or ttl <= 0:
                result.add_error(f"operation_ttls['{operation}'] must be a positive integer")
            elif ttl > 604800:  # 1 week
                result.add_warning(f"operation_ttls['{operation}'] is very long (>1 week)")

        # Validate hash_algorithm
        try:
            hashlib.new(self.hash_algorithm)
        except ValueError:
            result.add_error(f"hash_algorithm '{self.hash_algorithm}' is not supported")

        # Validate max_text_length
        if self.max_text_length <= 0:
            result.add_error("max_text_length must be positive")

        return result


@dataclass
class CacheConfig:
    """
    Comprehensive cache configuration with all settings.

    This is the main configuration class that contains all cache settings including
    Redis connection, security, performance, and optional AI-specific configuration.

    Attributes:
        redis_url: Redis connection URL (optional, falls back to memory cache)
        redis_password: Redis password for authentication
        use_tls: Enable TLS for Redis connections
        tls_cert_path: Path to TLS certificate file
        tls_key_path: Path to TLS private key file
        default_ttl: Default time-to-live in seconds
        memory_cache_size: Maximum size of memory cache
        compression_threshold: Size threshold for enabling compression
        compression_level: Compression level (1-9)
        environment: Environment name (development, testing, production)
        ai_config: Optional AI-specific configuration
    """
    # Redis configuration
    redis_url: Optional[str] = None
    redis_password: Optional[str] = None
    use_tls: bool = False
    tls_cert_path: Optional[str] = None
    tls_key_path: Optional[str] = None

    # Cache configuration
    default_ttl: int = 3600  # 1 hour
    memory_cache_size: int = 100
    compression_threshold: int = 1000
    compression_level: int = 6

    # Environment configuration
    environment: str = "development"

    # AI-specific configuration
    ai_config: Optional[AICacheConfig] = None
    enable_ai_cache: bool = False

    # Internal flags
    _from_env: bool = field(default=False, init=False)

    def __post_init__(self):
        """Post-initialization hook for environment loading."""
        if self._from_env:
            self._load_from_environment()

    def _load_from_environment(self) -> None:
        """
        Load configuration from environment variables (DEPRECATED).

        This method is deprecated in favor of the preset-based configuration system.
        Individual CACHE_* environment variables are no longer supported.

        Use CACHE_PRESET environment variable with preset-based configuration instead.
        """
        logger.warning(
            "Individual CACHE_* environment variable loading is deprecated. "
            "Use CACHE_PRESET with preset-based configuration instead."
        )
        # No-op - preset system should be used instead

    def _load_ai_config_from_environment(self) -> None:
        """
        Load AI-specific configuration from environment variables (DEPRECATED).

        This method is deprecated in favor of the preset-based configuration system.
        Individual CACHE_* environment variables are no longer supported.

        Use CACHE_PRESET environment variable with preset-based configuration instead.
        """
        logger.warning(
            "Individual AI CACHE_* environment variable loading is deprecated. "
            "Use CACHE_PRESET with preset-based configuration instead."
        )
        # No-op - preset system should be used instead

    @staticmethod
    def _parse_bool(value: str) -> bool:
        """Parse string value to boolean."""
        return value.lower() in ('true', '1', 'yes', 'on')

    def validate(self) -> ValidationResult:
        """
        Validate the configuration settings.

        Returns:
            ValidationResult with any errors or warnings found
        """
        result = ValidationResult(is_valid=True)

        # Validate Redis URL format
        if self.redis_url and not (
            self.redis_url.startswith('redis://') or
            self.redis_url.startswith('rediss://')
        ):
            result.add_error("redis_url must start with 'redis://' or 'rediss://'")

        # Validate TTL values
        if self.default_ttl <= 0:
            result.add_error("default_ttl must be positive")

        # Validate memory cache size
        if self.memory_cache_size <= 0:
            result.add_error("memory_cache_size must be positive")

        # Validate compression settings
        if self.compression_level < 1 or self.compression_level > 9:
            result.add_error("compression_level must be between 1 and 9")

        if self.compression_threshold < 0:
            result.add_error("compression_threshold must be non-negative")

        # Validate TLS configuration
        if self.use_tls:
            if self.tls_cert_path and not Path(self.tls_cert_path).exists():
                if self.environment == "production":
                    result.add_error(f"TLS certificate file not found: {self.tls_cert_path}")
                else:
                    result.add_warning(f"TLS certificate file not found: {self.tls_cert_path}")

            if self.tls_key_path and not Path(self.tls_key_path).exists():
                if self.environment == "production":
                    result.add_error(f"TLS key file not found: {self.tls_key_path}")
                else:
                    result.add_warning(f"TLS key file not found: {self.tls_key_path}")

        # Validate AI configuration if present
        if self.ai_config:
            ai_result = self.ai_config.validate()
            result.errors.extend(ai_result.errors)
            result.warnings.extend(ai_result.warnings)
            if not ai_result.is_valid:
                result.is_valid = False

        return result

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.

        Returns:
            Dictionary representation of the configuration
        """
        config_dict = asdict(self)
        # Remove internal fields
        config_dict.pop('_from_env', None)
        return config_dict


# ============================================================================
# Builder Pattern Implementation
# ============================================================================

class CacheConfigBuilder:
    """
    Builder for constructing CacheConfig instances with a fluent interface.

    This builder provides a flexible way to construct cache configurations
    using method chaining and supports loading from environment variables,
    files, and preset configurations.

    Example:
        >>> config = (CacheConfigBuilder()
        ...     .for_environment("production")
        ...     .with_redis("redis://prod:6379")
        ...     .with_compression(threshold=2000, level=6)
        ...     .with_ai_features(text_hash_threshold=1500)
        ...     .build())
    """

    def __init__(self):
        """Initialize the builder with an empty configuration."""
        self._config = CacheConfig()

    def for_environment(self, environment: str) -> 'CacheConfigBuilder':
        """
        Set configuration for a specific environment.

        Args:
            environment: Environment name (development, testing, production)

        Returns:
            Self for method chaining

        Raises:
            ValidationError: If environment is not supported
        """
        valid_environments = {'development', 'testing', 'production'}
        if environment not in valid_environments:
            raise ValidationError(
                f"Invalid environment: {environment}. Must be one of {valid_environments}",
                context={"provided_environment": environment, "valid_environments": list(valid_environments)}
            )

        self._config.environment = environment

        # Set environment-specific defaults
        if environment == "development":
            self._config.default_ttl = 1800  # 30 minutes
            self._config.memory_cache_size = 50
            self._config.compression_threshold = 2000
            self._config.compression_level = 4
        elif environment == "testing":
            self._config.default_ttl = 60  # 1 minute
            self._config.memory_cache_size = 25
            self._config.compression_threshold = 1000
            self._config.compression_level = 1
        elif environment == "production":
            self._config.default_ttl = 7200  # 2 hours
            self._config.memory_cache_size = 200
            self._config.compression_threshold = 1000
            self._config.compression_level = 6

        logger.debug(f"Set environment to {environment} with defaults")
        return self

    def with_redis(self, redis_url: str, password: Optional[str] = None,
                   use_tls: bool = False) -> 'CacheConfigBuilder':
        """
        Configure Redis connection settings.

        Args:
            redis_url: Redis connection URL
            password: Redis password (optional)
            use_tls: Enable TLS for connection

        Returns:
            Self for method chaining
        """
        self._config.redis_url = redis_url
        self._config.redis_password = password
        self._config.use_tls = use_tls
        return self

    def with_security(self, tls_cert_path: Optional[str] = None,
                      tls_key_path: Optional[str] = None) -> 'CacheConfigBuilder':
        """
        Configure TLS security settings.

        Args:
            tls_cert_path: Path to TLS certificate file
            tls_key_path: Path to TLS private key file

        Returns:
            Self for method chaining
        """
        self._config.tls_cert_path = tls_cert_path
        self._config.tls_key_path = tls_key_path

        # Auto-enable TLS if certificates are provided
        if tls_cert_path or tls_key_path:
            self._config.use_tls = True

        return self

    def with_compression(self, threshold: int = 1000,
                         level: int = 6) -> 'CacheConfigBuilder':
        """
        Configure compression settings.

        Args:
            threshold: Size threshold for enabling compression
            level: Compression level (1-9)

        Returns:
            Self for method chaining
        """
        self._config.compression_threshold = threshold
        self._config.compression_level = level
        return self

    def with_memory_cache(self, size: int) -> 'CacheConfigBuilder':
        """
        Configure memory cache settings.

        Args:
            size: Maximum size of memory cache

        Returns:
            Self for method chaining
        """
        self._config.memory_cache_size = size
        return self

    def with_ai_features(self, **ai_options) -> 'CacheConfigBuilder':
        """
        Enable and configure AI-specific features.

        Args:
            **ai_options: AI configuration options (text_hash_threshold,
                         hash_algorithm, operation_ttls, etc.)

        Returns:
            Self for method chaining

        Raises:
            ValidationError: If unknown AI configuration options are provided
        """
        if self._config.ai_config is None:
            self._config.ai_config = AICacheConfig()

        # Validate known AI configuration options
        valid_ai_options = {
            'text_hash_threshold', 'hash_algorithm', 'text_size_tiers',
            'operation_ttls', 'enable_smart_promotion', 'max_text_length'
        }

        unknown_options = set(ai_options.keys()) - valid_ai_options
        if unknown_options:
            raise ValidationError(
                f"Unknown AI configuration options: {unknown_options}",
                context={"unknown_options": list(unknown_options), "valid_options": list(valid_ai_options)}
            )

        # Update AI configuration
        for option, value in ai_options.items():
            setattr(self._config.ai_config, option, value)

        return self

    def from_file(self, file_path: str | Path) -> 'CacheConfigBuilder':
        """
        Load configuration from a JSON file.

        Args:
            file_path: Path to JSON configuration file

        Returns:
            Self for method chaining

        Raises:
            ConfigurationError: If file cannot be read or parsed
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise ConfigurationError(
                f"Configuration file not found: {file_path}",
                context={"file_path": str(file_path)}
            )

        try:
            with open(file_path, 'r') as f:
                config_data = json.load(f)

            # Apply configuration data
            for key, value in config_data.items():
                if key == 'ai_config':
                    # Handle AI config specially
                    if value:
                        if self._config.ai_config is None:
                            self._config.ai_config = AICacheConfig()

                        for ai_key, ai_value in value.items():
                            if hasattr(self._config.ai_config, ai_key):
                                setattr(self._config.ai_config, ai_key, ai_value)
                elif hasattr(self._config, key) and not key.startswith('_'):
                    setattr(self._config, key, value)

            logger.info(f"Loaded configuration from {file_path}")

        except json.JSONDecodeError as e:
            raise ConfigurationError(
                f"Invalid JSON in configuration file: {e}",
                context={"file_path": str(file_path), "json_error": str(e)}
            )
        except Exception as e:
            raise ConfigurationError(
                f"Failed to load configuration from file: {e}",
                context={"file_path": str(file_path), "error_type": type(e).__name__}
            )

        return self

    def from_environment(self) -> 'CacheConfigBuilder':
        """
        Load configuration from environment variables.

        Returns:
            Self for method chaining
        """
        self._config._from_env = True
        self._config._load_from_environment()
        return self

    def validate(self) -> ValidationResult:
        """
        Validate the current configuration.

        Returns:
            ValidationResult with any errors or warnings found
        """
        return self._config.validate()

    def build(self) -> CacheConfig:
        """
        Build and validate the final configuration.

        Returns:
            Validated CacheConfig instance

        Raises:
            ValidationError: If configuration validation fails
        """
        validation_result = self.validate()

        if not validation_result.is_valid:
            error_msg = "Configuration validation failed: " + "; ".join(validation_result.errors)
            raise ValidationError(
                error_msg,
                context={"errors": validation_result.errors, "warnings": validation_result.warnings}
            )

        # Log warnings if present
        for warning in validation_result.warnings:
            logger.warning(f"Configuration warning: {warning}")

        return self._config

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert current configuration to dictionary.

        Returns:
            Dictionary representation of the configuration
        """
        return self._config.to_dict()

    def save_to_file(self, file_path: str | Path,
                     create_dirs: bool = True) -> None:
        """
        Save current configuration to a JSON file.

        Args:
            file_path: Path to save configuration file
            create_dirs: Whether to create parent directories if they don't exist

        Raises:
            ConfigurationError: If file cannot be written
        """
        file_path = Path(file_path)

        if create_dirs:
            file_path.parent.mkdir(parents=True, exist_ok=True)

        try:
            config_dict = self.to_dict()
            with open(file_path, 'w') as f:
                json.dump(config_dict, f, indent=2)

            logger.info(f"Saved configuration to {file_path}")

        except Exception as e:
            raise ConfigurationError(
                f"Failed to save configuration to file: {e}",
                context={"file_path": str(file_path), "error_type": type(e).__name__}
            )


# ============================================================================
# Environment Presets
# ============================================================================

class EnvironmentPresets:
    """
    Pre-configured cache settings for different environments using the new preset system.

    This class provides static methods that return pre-configured CacheConfig
    instances from the new cache preset system, replacing the CacheConfigBuilder approach
    with the simplified preset-based configuration system.

    **Migration Note**: This class now uses the new cache preset system from
    `app.infrastructure.cache.cache_presets` which reduces 28+ environment variables
    to a single CACHE_PRESET configuration.
    """

    @staticmethod
    def disabled():
        """
        Cache completely disabled, no Redis connection, memory-only fallback.

        Returns:
            CacheConfig with no caching
        """
        from app.infrastructure.cache.cache_presets import cache_preset_manager
        preset = cache_preset_manager.get_preset("disabled")
        return preset.to_cache_config()

    @staticmethod
    def minimal():
        """
        Ultra-lightweight caching for resource-constrained environments.

        Returns:
            CacheConfig optimized for minimal caching
        """
        from app.infrastructure.cache.cache_presets import cache_preset_manager
        preset = cache_preset_manager.get_preset("minimal")
        return preset.to_cache_config()

    @staticmethod
    def simple():
        """
        Simple cache preset with balanced caching and typical expiration.

        Returns:
            CacheConfig suitable for most use cases
        """
        from app.infrastructure.cache.cache_presets import cache_preset_manager
        preset = cache_preset_manager.get_preset("simple")
        return preset.to_cache_config()

    @staticmethod
    def development():
        """
        Development environment preset with balanced performance and debugging.

        Returns:
            CacheConfig optimized for development from the new preset system
        """
        from app.infrastructure.cache.cache_presets import cache_preset_manager
        preset = cache_preset_manager.get_preset("development")
        return preset.to_cache_config()

    @staticmethod
    def testing():
        """
        Testing environment preset with minimal caching and fast expiration.

        Returns:
            CacheConfig optimized for testing from the new preset system

        Note: Uses 'development' preset as base since it's optimized for fast feedback
        """
        from app.infrastructure.cache.cache_presets import cache_preset_manager
        preset = cache_preset_manager.get_preset("development")
        return preset.to_cache_config()

    @staticmethod
    def production():
        """
        Production environment preset with optimized performance and security.

        Returns:
            CacheConfig optimized for production from the new preset system
        """
        from app.infrastructure.cache.cache_presets import cache_preset_manager
        preset = cache_preset_manager.get_preset("production")
        return preset.to_cache_config()

    @staticmethod
    def ai_development():
        """
        AI development preset with AI features and development-friendly settings.

        Returns:
            CacheConfig optimized for AI development from the new preset system
        """
        from app.infrastructure.cache.cache_presets import cache_preset_manager
        preset = cache_preset_manager.get_preset("ai-development")
        return preset.to_cache_config()

    @staticmethod
    def ai_production():
        """
        AI production preset with AI features and production-optimized settings.

        Returns:
            CacheConfig optimized for AI production workloads from the new preset system
        """
        from app.infrastructure.cache.cache_presets import cache_preset_manager
        preset = cache_preset_manager.get_preset("ai-production")
        return preset.to_cache_config()

    @staticmethod
    def get_preset_names() -> list:
        """
        Get list of all available preset names.

        Returns:
            List of preset names available in the system
        """
        from app.infrastructure.cache.cache_presets import cache_preset_manager
        return cache_preset_manager.list_presets()

    @staticmethod
    def get_preset_details(preset_name: str) -> dict:
        """
        Get detailed information about a specific preset.

        Args:
            preset_name: Name of the preset to get details for

        Returns:
            Dictionary with preset configuration details
        """
        from app.infrastructure.cache.cache_presets import cache_preset_manager
        return cache_preset_manager.get_preset_details(preset_name)

    @staticmethod
    def recommend_preset(environment: Optional[str] = None) -> str:
        """
        Recommend appropriate preset for given environment.

        Args:
            environment: Environment name (optional, auto-detects if None)

        Returns:
            Recommended preset name
        """
        from app.infrastructure.cache.cache_presets import cache_preset_manager
        return cache_preset_manager.recommend_preset(environment)
