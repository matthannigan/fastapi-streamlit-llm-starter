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
from dataclasses import asdict, dataclass, field
from pathlib import Path
from typing import Any, Dict, List
from app.core.exceptions import ConfigurationError, ValidationError


@dataclass
class ValidationResult:
    """
    Result of configuration validation containing validation status and details.
    
    Attributes:
        is_valid: Whether the configuration passed validation
        errors: List of error messages that prevent successful operation
        warnings: List of warning messages for non-critical issues
    """

    def add_error(self, message: str) -> None:
        """
        Add an error message and mark validation as invalid.
        """
        ...

    def add_warning(self, message: str) -> None:
        """
        Add a warning message.
        """
        ...


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

    def validate(self) -> ValidationResult:
        """
        Validate AI configuration settings.
        
        Returns:
            ValidationResult with any errors or warnings found
        """
        ...


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

    def __post_init__(self):
        """
        Post-initialization hook for environment loading.
        """
        ...

    def validate(self) -> ValidationResult:
        """
        Validate the configuration settings.
        
        Returns:
            ValidationResult with any errors or warnings found
        """
        ...

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert configuration to dictionary.
        
        Returns:
            Dictionary representation of the configuration
        """
        ...


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
        """
        Initialize the builder with an empty configuration.
        """
        ...

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
        ...

    def with_redis(self, redis_url: str, password: str | None = None, use_tls: bool = False) -> 'CacheConfigBuilder':
        """
        Configure Redis connection settings.
        
        Args:
            redis_url: Redis connection URL
            password: Redis password (optional)
            use_tls: Enable TLS for connection
        
        Returns:
            Self for method chaining
        """
        ...

    def with_security(self, tls_cert_path: str | None = None, tls_key_path: str | None = None) -> 'CacheConfigBuilder':
        """
        Configure TLS security settings.
        
        Args:
            tls_cert_path: Path to TLS certificate file
            tls_key_path: Path to TLS private key file
        
        Returns:
            Self for method chaining
        """
        ...

    def with_compression(self, threshold: int = 1000, level: int = 6) -> 'CacheConfigBuilder':
        """
        Configure compression settings.
        
        Args:
            threshold: Size threshold for enabling compression
            level: Compression level (1-9)
        
        Returns:
            Self for method chaining
        """
        ...

    def with_memory_cache(self, size: int) -> 'CacheConfigBuilder':
        """
        Configure memory cache settings.
        
        Args:
            size: Maximum size of memory cache
        
        Returns:
            Self for method chaining
        """
        ...

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
        ...

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
        ...

    def from_environment(self) -> 'CacheConfigBuilder':
        """
        Load configuration from environment variables.
        
        Returns:
            Self for method chaining
        """
        ...

    def validate(self) -> ValidationResult:
        """
        Validate the current configuration.
        
        Returns:
            ValidationResult with any errors or warnings found
        """
        ...

    def build(self) -> CacheConfig:
        """
        Build and validate the final configuration.
        
        Returns:
            Validated CacheConfig instance
        
        Raises:
            ValidationError: If configuration validation fails
        """
        ...

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert current configuration to dictionary.
        
        Returns:
            Dictionary representation of the configuration
        """
        ...

    def save_to_file(self, file_path: str | Path, create_dirs: bool = True) -> None:
        """
        Save current configuration to a JSON file.
        
        Args:
            file_path: Path to save configuration file
            create_dirs: Whether to create parent directories if they don't exist
        
        Raises:
            ConfigurationError: If file cannot be written
        """
        ...


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
        ...

    @staticmethod
    def minimal():
        """
        Ultra-lightweight caching for resource-constrained environments.
        
        Returns:
            CacheConfig optimized for minimal caching
        """
        ...

    @staticmethod
    def simple():
        """
        Simple cache preset with balanced caching and typical expiration.
        
        Returns:
            CacheConfig suitable for most use cases
        """
        ...

    @staticmethod
    def development():
        """
        Development environment preset with balanced performance and debugging.
        
        Returns:
            CacheConfig optimized for development from the new preset system
        """
        ...

    @staticmethod
    def testing():
        """
        Testing environment preset with minimal caching and fast expiration.
        
        Returns:
            CacheConfig optimized for testing from the new preset system
        
        Note: Uses 'development' preset as base since it's optimized for fast feedback
        """
        ...

    @staticmethod
    def production():
        """
        Production environment preset with optimized performance and security.
        
        Returns:
            CacheConfig optimized for production from the new preset system
        """
        ...

    @staticmethod
    def ai_development():
        """
        AI development preset with AI features and development-friendly settings.
        
        Returns:
            CacheConfig optimized for AI development from the new preset system
        """
        ...

    @staticmethod
    def ai_production():
        """
        AI production preset with AI features and production-optimized settings.
        
        Returns:
            CacheConfig optimized for AI production workloads from the new preset system
        """
        ...

    @staticmethod
    def get_preset_names() -> list:
        """
        Get list of all available preset names.
        
        Returns:
            List of preset names available in the system
        """
        ...

    @staticmethod
    def get_preset_details(preset_name: str) -> dict:
        """
        Get detailed information about a specific preset.
        
        Args:
            preset_name: Name of the preset to get details for
        
        Returns:
            Dictionary with preset configuration details
        """
        ...

    @staticmethod
    def recommend_preset(environment: str | None = None) -> str:
        """
        Recommend appropriate preset for given environment.
        
        Args:
            environment: Environment name (optional, auto-detects if None)
        
        Returns:
            Recommended preset name
        """
        ...
