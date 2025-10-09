"""
Security Service Factory

This module provides a factory for creating and configuring security service instances.
It supports multiple service implementations, environment-based configuration, and
dependency injection for testing and flexibility.

## Factory Pattern Overview

The factory pattern enables:
- **Service Abstraction**: Create services without knowing implementation details
- **Configuration Management**: Centralized configuration loading and validation
- **Environment Support**: Environment-based service selection and configuration
- **Testability**: Easy mocking and dependency injection for testing
- **Extensibility**: Simple addition of new service implementations

## Supported Service Modes

### Local Mode
Custom security scanning implementation using:
- **Transformers**: ML models for text classification and analysis
- **Presidio**: PII detection and anonymization
- **SpaCy**: Advanced NLP processing
- **Async Processing**: Non-blocking operations

### SaaS Mode (Future)
Cloud-based security service integration:
- **API Integration**: Third-party security service APIs
- **Managed Infrastructure**: No local ML models required
- **Scalability**: Cloud-based scaling and reliability
- **Compliance**: Managed compliance and updates

## Configuration Loading

The factory supports multiple configuration sources:
- **Environment Variables**: Runtime configuration via environment
- **Configuration Files**: JSON/YAML configuration files
- **Predefined Presets**: Built-in configuration presets
- **Programmatic Configuration**: Direct configuration objects

## Usage Examples

### Basic Factory Usage
```python
from app.infrastructure.security.llm import create_security_service

# Create security service with default configuration
security_service = create_security_service(mode="local")

# Use the service
result = await security_service.validate_input("User input text")
```

### Configuration-based Factory Usage
```python
from app.infrastructure.security.llm import create_security_service
from app.infrastructure.security.llm.config import SecurityConfig, PresetName

# Create custom configuration
config = SecurityConfig.create_from_preset(PresetName.STRICT)

# Create service with custom configuration
security_service = create_security_service(
    mode="local",
    config=config
)
```

### Environment-based Configuration
```python
import os
from app.infrastructure.security.llm import create_security_service

# Set environment variables
os.environ["SECURITY_MODE"] = "local"
os.environ["SECURITY_PRESET"] = "production"
os.environ["SECURITY_MAX_CONCURRENT_SCANS"] = "15"

# Factory automatically picks up environment configuration
security_service = create_security_service()
```

### FastAPI Integration
```python
from fastapi import Depends
from app.infrastructure.security.llm import get_security_service

@app.post("/chat")
async def chat(
    message: str,
    security_service: SecurityService = Depends(get_security_service)
):
    # Security service is automatically injected
    result = await security_service.validate_input(message)
    if not result.is_safe:
        raise HTTPException(status_code=400, detail="Security violation")

    # Process with AI...
    return {"response": "AI response"}
```
"""

import os
import logging
from typing import Any, Dict

from app.core.exceptions import ConfigurationError, InfrastructureError
from app.infrastructure.security.llm.config import (
    PresetName,
    SecurityConfig,
)
from app.infrastructure.security.llm.protocol import SecurityService


class SecurityServiceFactory:
    """
    Factory for creating and managing security service instances with comprehensive configuration support.

    This factory provides centralized creation and lifecycle management of security service
    implementations, supporting multiple operational modes, configuration sources, and
    caching strategies for production deployments.

    Attributes:
        _service_cache: Class-level cache storing configured service instances by cache key
        _default_config: Cached default configuration for performance optimization

    Public Methods:
        create_service(): Create a security service with specified configuration
        clear_cache(): Clear all cached service instances
        get_cache_stats(): Get statistics about cached services

    State Management:
        - Maintains class-level service cache for instance reuse
        - Thread-safe service creation and caching
        - Automatic cache key generation based on configuration parameters
        - Supports service isolation through unique cache keys

    Usage:
        # Basic service creation with default configuration
        factory = SecurityServiceFactory()
        service = factory.create_service(mode="local")
        result = await service.validate_input("User input text")

        # Advanced configuration with custom settings
        config = SecurityConfig.create_from_preset(PresetName.STRICT)
        service = factory.create_service(
            mode="local",
            config=config,
            cache_key="strict_security_service"
        )

        # Cache management
        stats = factory.get_cache_stats()
        factory.clear_cache()
    """

    _service_cache: Dict[str, SecurityService] = {}
    _default_config: SecurityConfig | None = None

    @classmethod
    def create_service(
        cls,
        mode: str = "local",
        config: SecurityConfig | None = None,
        environment_overrides: Dict[str, Any] | None = None,
        cache_key: str | None = None,
    ) -> SecurityService:
        """
        Create a security service instance with specified configuration and caching.

        This method creates security service instances supporting multiple operational modes,
        configuration sources, and caching strategies. It handles configuration validation,
        environment variable integration, and service instance caching for performance
        optimization in production environments.

        Args:
            mode: Service mode, one of ["local", "saas"] (default: "local")
                  - "local": Local ML-based security scanning
                  - "saas": Cloud-based security service (future implementation)
            config: Optional SecurityConfig object with detailed settings. If None,
                   creates default configuration from environment variables
            environment_overrides: Optional dictionary of environment variable overrides
                                  for runtime configuration adjustments
            cache_key: Optional cache key for service instance reuse. If None,
                      generates deterministic key based on configuration parameters

        Returns:
            Configured SecurityService instance ready for input validation and scanning

        Raises:
            ConfigurationError: If configuration is invalid, incomplete, or contains
                               contradictory settings
            InfrastructureError: If service creation fails due to missing dependencies,
                                 model loading errors, or system resource issues

        Behavior:
            - Generates deterministic cache key if not provided for consistent caching
            - Returns cached service instance if available with matching configuration
            - Loads and validates configuration from provided config, environment, or defaults
            - Applies environment variable overrides for runtime customization
            - Creates service instance based on specified mode with proper error handling
            - Caches service instance for subsequent reuse with same configuration
            - Validates final configuration to ensure at least one scanner is enabled

        Examples:
            >>> # Basic local service with default configuration
            >>> service = SecurityServiceFactory.create_service(mode="local")
            >>> result = await service.validate_input("Test input text")
            >>> assert hasattr(result, 'is_safe')

            >>> # Service with custom configuration
            >>> config = SecurityConfig.create_from_preset(PresetName.STRICT)
            >>> service = SecurityServiceFactory.create_service(
            ...     mode="local",
            ...     config=config,
            ...     cache_key="strict_service"
            ... )
            >>> result = await service.validate_input("Another test")

            >>> # Service with environment overrides
            >>> overrides = {"toxicity_threshold": 0.8, "enable_caching": "true"}
            >>> service = SecurityServiceFactory.create_service(
            ...     mode="local",
            ...     environment_overrides=overrides
            ... )

            >>> # Error handling for invalid configuration
            >>> with pytest.raises(ConfigurationError):
            ...     # Empty config with no environment variables
            ...     SecurityServiceFactory.create_service(
            ...         mode="local",
            ...         config=SecurityConfig()  # No scanners enabled
            ...     )
        """
        # Generate cache key if not provided
        if cache_key is None:
            cache_key = cls._generate_cache_key(mode, config, environment_overrides)

        # Check cache first
        if cache_key in cls._service_cache:
            return cls._service_cache[cache_key]

        # Load configuration
        service_config = cls._load_configuration(config, environment_overrides)

        # Create service based on mode
        service = cls._create_service_instance(mode, service_config)

        # Cache the service
        cls._service_cache[cache_key] = service

        return service

    @classmethod
    def _load_configuration(
        cls,
        config: SecurityConfig | None = None,
        environment_overrides: Dict[str, Any] | None = None,
    ) -> SecurityConfig:
        """
        Load and validate security service configuration from multiple sources.

        This method consolidates configuration from provided objects, environment variables,
        and default values, then validates the resulting configuration for completeness
        and consistency before returning a ready-to-use SecurityConfig object.

        Args:
            config: Optional SecurityConfig object with predefined settings. If None,
                   creates default configuration from environment variables or presets
            environment_overrides: Optional dictionary of environment variable name-value
                                  pairs to override configuration settings at runtime

        Returns:
            Validated SecurityConfig object with all settings resolved and checked for
            consistency, ready for service instantiation

        Raises:
            ConfigurationError: If configuration is invalid, incomplete, or contains
                               contradictory settings that prevent service creation

        Behavior:
            - Uses provided config object directly if specified, skipping default creation
            - Creates default configuration from environment variables if no config provided
            - Applies environment variable overrides for runtime customization
            - Merges configuration settings with override values taking precedence
            - Validates final configuration for required fields and value constraints
            - Ensures configuration consistency before returning to service creation

        Examples:
            >>> # Configuration with environment overrides
            >>> config = SecurityConfig.create_from_preset(PresetName.BALANCED)
            >>> overrides = {"toxicity_threshold": 0.8, "max_concurrent_scans": 10}
            >>> final_config = SecurityServiceFactory._load_configuration(config, overrides)
            >>> assert final_config.scanners.toxicity.threshold == 0.8
            >>> assert final_config.performance.max_concurrent_scans == 10

            >>> # Default configuration creation
            >>> default_config = SecurityServiceFactory._load_configuration()
            >>> assert hasattr(default_config, 'scanners')
            >>> assert hasattr(default_config, 'performance')

            >>> # Error handling for invalid configuration
            >>> with pytest.raises(ConfigurationError):
            ...     # This would fail validation with no scanners enabled
            ...     invalid_config = SecurityConfig()  # Assuming empty config
            ...     SecurityServiceFactory._load_configuration(invalid_config)
        """
        # Start with provided config or create default
        if config is not None:
            service_config = config
        else:
            service_config = cls._create_default_configuration()

        # Apply environment overrides
        env_overrides = environment_overrides or cls._load_environment_overrides()
        if env_overrides:
            service_config = service_config.merge_with_environment_overrides(env_overrides)

        # Validate configuration
        cls._validate_configuration(service_config)

        return service_config

    @classmethod
    def _create_default_configuration(cls) -> SecurityConfig:
        """
        Create default security service configuration from environment variables.

        This method constructs a SecurityConfig object by reading environment variables
        for preset selection, environment context, and debug settings. It provides
        sensible defaults and graceful fallback behavior for missing or invalid
        environment variable values.

        Returns:
            SecurityConfig object initialized with environment-based settings and
            appropriate defaults for production deployment

        Behavior:
            - Reads SECURITY_PRESET environment variable, defaults to "balanced" if invalid
            - Reads ENVIRONMENT variable, defaults to "development" for context
            - Reads SECURITY_DEBUG variable, enables debug mode if set to true/1/yes
            - Creates configuration using preset-based initialization
            - Applies debug mode setting to the final configuration
            - Logs warnings for invalid environment variable values

        Examples:
            >>> # With environment variables set
            >>> os.environ["SECURITY_PRESET"] = "strict"
            >>> os.environ["ENVIRONMENT"] = "production"
            >>> os.environ["SECURITY_DEBUG"] = "false"
            >>> config = SecurityServiceFactory._create_default_configuration()
            >>> # Returns config with strict preset and production settings

            >>> # With invalid preset (falls back to balanced)
            >>> os.environ["SECURITY_PRESET"] = "invalid_preset"
            >>> config = SecurityServiceFactory._create_default_configuration()
            >>> # Logs warning and uses balanced preset

            >>> # With no environment variables (all defaults)
            >>> for key in ["SECURITY_PRESET", "ENVIRONMENT", "SECURITY_DEBUG"]:
            ...     os.environ.pop(key, None)
            >>> config = SecurityServiceFactory._create_default_configuration()
            >>> # Returns config with balanced preset and development environment
        """
        # Determine preset from environment
        preset_name = os.getenv("SECURITY_PRESET", "balanced").lower()

        try:
            preset = PresetName(preset_name)
        except ValueError:
            # Fall back to balanced preset if invalid preset specified
            preset = PresetName.BALANCED
            logging.warning(
                f"Invalid SECURITY_PRESET '{preset_name}', using 'balanced' preset"
            )

        # Determine environment
        environment = os.getenv("ENVIRONMENT", "development").lower()

        # Create configuration from preset
        config = SecurityConfig.create_from_preset(preset, environment)

        # Apply debug mode if specified
        debug_mode = os.getenv("SECURITY_DEBUG", "false").lower() in ("true", "1", "yes")
        config.debug_mode = debug_mode

        return config

    @classmethod
    def _load_environment_overrides(cls) -> Dict[str, Any]:
        """
        Load configuration overrides from security-related environment variables.

        This method scans the environment for SECURITY_* prefixed variables and converts
        them to configuration override values with appropriate type conversion and
        validation. It supports various data types and provides graceful error handling
        for invalid values.

        Returns:
            Dictionary mapping configuration property names to override values extracted
            from environment variables, ready for merging with base configuration

        Behavior:
            - Scans for SECURITY_MODE, SECURITY_PRESET, and SECURITY_DEBUG variables
            - Converts SECURITY_MAX_CONCURRENT_SCANS to integer with validation
            - Converts SECURITY_CACHE_TTL to integer with error handling
            - Validates SECURITY_TOXICITY_THRESHOLD as float between 0.0 and 1.0
            - Preserves SECURITY_PII_ACTION, SECURITY_LOG_LEVEL as string values
            - Logs warnings for invalid or unparsable environment variable values
            - Returns empty dictionary if no relevant environment variables found

        Examples:
            >>> # With environment variables set
            >>> os.environ["SECURITY_MODE"] = "local"
            >>> os.environ["SECURITY_MAX_CONCURRENT_SCANS"] = "15"
            >>> os.environ["SECURITY_TOXICITY_THRESHOLD"] = "0.8"
            >>> overrides = SecurityServiceFactory._load_environment_overrides()
            >>> assert overrides["security_mode"] == "local"
            >>> assert overrides["max_concurrent_scans"] == 15
            >>> assert overrides["toxicity_threshold"] == 0.8

            >>> # With invalid numeric values (logs warnings, ignores invalid)
            >>> os.environ["SECURITY_MAX_CONCURRENT_SCANS"] = "invalid"
            >>> os.environ["SECURITY_TOXICITY_THRESHOLD"] = "2.0"  # Out of range
            >>> overrides = SecurityServiceFactory._load_environment_overrides()
            >>> # Logs warnings and excludes these invalid values

            >>> # With no security environment variables
            >>> for key in list(os.environ.keys()):
            ...     if key.startswith("SECURITY_"):
            ...         del os.environ[key]
            >>> overrides = SecurityServiceFactory._load_environment_overrides()
            >>> assert overrides == {}
        """
        overrides: Dict[str, Any] = {}

        # Security service configuration
        if "SECURITY_MODE" in os.environ:
            overrides["security_mode"] = os.environ["SECURITY_MODE"]

        if "SECURITY_PRESET" in os.environ:
            overrides["security_preset"] = os.environ["SECURITY_PRESET"]

        if "SECURITY_DEBUG" in os.environ:
            overrides["security_debug"] = os.environ["SECURITY_DEBUG"]

        # Performance settings
        if "SECURITY_MAX_CONCURRENT_SCANS" in os.environ:
            try:
                overrides["max_concurrent_scans"] = int(os.environ["SECURITY_MAX_CONCURRENT_SCANS"])
            except ValueError:
                logging.warning("Invalid SECURITY_MAX_CONCURRENT_SCANS value, ignoring")

        if "SECURITY_ENABLE_CACHING" in os.environ:
            overrides["enable_caching"] = os.environ["SECURITY_ENABLE_CACHING"]

        if "SECURITY_CACHE_TTL" in os.environ:
            try:
                overrides["cache_ttl_seconds"] = int(os.environ["SECURITY_CACHE_TTL"])
            except ValueError:
                logging.warning("Invalid SECURITY_CACHE_TTL value, ignoring")

        # Scanner-specific settings
        if "SECURITY_TOXICITY_THRESHOLD" in os.environ:
            try:
                threshold = float(os.environ["SECURITY_TOXICITY_THRESHOLD"])
                if 0.0 <= threshold <= 1.0:
                    overrides["toxicity_threshold"] = threshold
                else:
                    logging.warning("Invalid SECURITY_TOXICITY_THRESHOLD value, ignoring")
            except ValueError:
                logging.warning("Invalid SECURITY_TOXICITY_THRESHOLD value, ignoring")

        if "SECURITY_PII_ACTION" in os.environ:
            overrides["pii_action"] = os.environ["SECURITY_PII_ACTION"]

        # Logging settings
        if "SECURITY_LOG_LEVEL" in os.environ:
            overrides["log_level"] = os.environ["SECURITY_LOG_LEVEL"]

        if "SECURITY_INCLUDE_SCANNED_TEXT" in os.environ:
            overrides["include_scanned_text"] = os.environ["SECURITY_INCLUDE_SCANNED_TEXT"]

        return overrides

    @classmethod
    def _create_service_instance(cls, mode: str, config: SecurityConfig) -> SecurityService:
        """
        Create a security service instance based on the specified operational mode.

        This method instantiates the appropriate security service implementation
        based on the provided mode, handling all necessary initialization and
        error scenarios with comprehensive exception handling and logging.

        Args:
            mode: Service mode, one of ["local", "saas"]. Determines which implementation
                  to instantiate for security scanning and validation
            config: Validated SecurityConfig object containing all settings required
                    for service initialization and operation

        Returns:
            Fully initialized SecurityService instance ready to perform input
            validation and security scanning operations

        Raises:
            InfrastructureError: If service creation fails due to missing dependencies,
                                 model loading errors, system resource constraints,
                                 or initialization failures
            NotImplementedError: If the specified mode is not yet implemented

        Behavior:
            - Instantiates LocalLLMSecurityScanner for "local" mode with ML models
            - Raises NotImplementedError for "saas" mode (future implementation)
            - Raises ConfigurationError for unknown or unsupported modes
            - Wraps and re-raises initialization failures as InfrastructureError
            - Preserves original exception context for debugging
            - Handles import errors and other system-level failures gracefully

        Examples:
            >>> # Local service creation
            >>> config = SecurityConfig.create_from_preset(PresetName.BALANCED)
            >>> service = SecurityServiceFactory._create_service_instance("local", config)
            >>> assert hasattr(service, 'validate_input')
            >>> assert service.__class__.__name__ == 'LocalLLMSecurityScanner'

            >>> # SaaS mode (not yet implemented)
            >>> with pytest.raises(NotImplementedError):
            ...     SecurityServiceFactory._create_service_instance("saas", config)

            >>> # Invalid mode
            >>> with pytest.raises(ConfigurationError):
            ...     SecurityServiceFactory._create_service_instance("invalid", config)

            >>> # Infrastructure error for missing dependencies
            >>> # This would happen if required ML models or libraries are unavailable
            >>> with pytest.raises(InfrastructureError):
            ...     # Assuming missing dependencies
            ...     SecurityServiceFactory._create_service_instance("local", config)
        """
        try:
            if mode == "local":
                from app.infrastructure.security.llm.scanners.local_scanner import (
                    LocalLLMSecurityScanner,
                )
                # Pass the configuration directly - scanner will handle YAML loading if needed
                return LocalLLMSecurityScanner(config=config)

            if mode == "saas":
                # Future: SaaS implementation
                raise NotImplementedError("SaaS mode is not yet implemented")

            raise ConfigurationError(f"Unknown security service mode: {mode}")

        except Exception as e:
            if isinstance(e, (ConfigurationError, InfrastructureError)):
                raise

            raise InfrastructureError(
                f"Failed to create security service with mode '{mode}': {e!s}",
                context={"original_error": str(e)},
            ) from e

    @classmethod
    def _validate_configuration(cls, config: SecurityConfig) -> None:
        """
        Validate security service configuration for completeness and consistency.

        This method performs comprehensive validation of the security configuration
        to ensure it meets minimum requirements for service operation and contains
        valid settings for all configured scanners and performance parameters.

        Args:
            config: SecurityConfig object to validate for operational readiness

        Raises:
            ConfigurationError: If configuration is invalid, incomplete, or contains
                               settings that would prevent proper service operation

        Behavior:
            - Verifies at least one security scanner is enabled in the configuration
            - Validates performance settings (max_concurrent_scans >= 1)
            - Validates memory allocation (max_memory_mb >= 512)
            - Logs configuration summary in debug mode for troubleshooting
            - Provides detailed error messages for specific validation failures
            - Checks scanner-specific configuration consistency

        Examples:
            >>> # Valid configuration passes validation
            >>> config = SecurityConfig.create_from_preset(PresetName.BALANCED)
            >>> SecurityServiceFactory._validate_configuration(config)  # No exception

            >>> # Configuration with no scanners enabled fails
            >>> config = SecurityConfig()  # Assuming empty config with no scanners
            >>> with pytest.raises(ConfigurationError) as exc_info:
            ...     SecurityServiceFactory._validate_configuration(config)
            >>> assert "at least one security scanner" in str(exc_info.value).lower()

            >>> # Invalid performance settings fail validation
            >>> config = SecurityConfig.create_from_preset(PresetName.BALANCED)
            >>> config.performance.max_concurrent_scans = 0
            >>> with pytest.raises(ConfigurationError) as exc_info:
            ...     SecurityServiceFactory._validate_configuration(config)
            >>> assert "max_concurrent_scans must be at least 1" in str(exc_info.value)

            >>> # Insufficient memory allocation fails validation
            >>> config = SecurityConfig.create_from_preset(PresetName.BALANCED)
            >>> config.performance.max_memory_mb = 256
            >>> with pytest.raises(ConfigurationError) as exc_info:
            ...     SecurityServiceFactory._validate_configuration(config)
            >>> assert "max_memory_mb must be at least 512" in str(exc_info.value)
        """
        # Check if at least one scanner is enabled
        enabled_scanners = config.get_enabled_scanners()
        if not enabled_scanners:
            raise ConfigurationError(
                "At least one security scanner must be enabled. "
                "Check your configuration or SECURITY_PRESET setting."
            )

        # Validate performance settings
        if config.performance.max_concurrent_scans < 1:
            raise ConfigurationError("max_concurrent_scans must be at least 1")

        if config.performance.max_memory_mb < 512:
            raise ConfigurationError("max_memory_mb must be at least 512")

        # Log configuration summary in debug mode
        if config.debug_mode:
            logging.info(
                f"Security service configured with {len(enabled_scanners)} enabled scanners: "
                f"{[scanner.value for scanner in enabled_scanners]}"
            )
            logging.info(f"Performance settings: {config.performance.dict()}")

    @classmethod
    def _generate_cache_key(
        cls,
        mode: str,
        config: SecurityConfig | None,
        environment_overrides: Dict[str, Any] | None,
    ) -> str:
        """
        Generate a deterministic cache key for the service configuration.

        This method creates a unique, reproducible cache key based on the service
        mode, configuration object, and environment overrides. The key ensures that
        identical configurations produce the same cache key while different
        configurations produce distinct keys.

        Args:
            mode: Service mode string used as part of cache key generation
            config: SecurityConfig object to include in cache key computation
            environment_overrides: Dictionary of environment variable overrides
                                   to include in cache key generation

        Returns:
            String cache key in format "security_service_{mode}_{hash}" suitable for
            use as dictionary key in service cache

        Behavior:
            - Converts configuration object to dictionary representation if provided
            - Creates deterministic JSON representation with sorted keys
            - Generates MD5 hash of complete configuration for compact key
            - Includes mode name in cache key for easy identification
            - Handles None values gracefully in cache key generation
            - Ensures reproducible keys for identical configurations

        Examples:
            >>> # Same configuration produces same cache key
            >>> config = SecurityConfig.create_from_preset(PresetName.BALANCED)
            >>> key1 = SecurityServiceFactory._generate_cache_key("local", config, {})
            >>> key2 = SecurityServiceFactory._generate_cache_key("local", config, {})
            >>> assert key1 == key2

            >>> # Different configurations produce different cache keys
            >>> config1 = SecurityConfig.create_from_preset(PresetName.BALANCED)
            >>> config2 = SecurityConfig.create_from_preset(PresetName.STRICT)
            >>> key1 = SecurityServiceFactory._generate_cache_key("local", config1, {})
            >>> key2 = SecurityServiceFactory._generate_cache_key("local", config2, {})
            >>> assert key1 != key2

            >>> # Environment overrides affect cache key
            >>> overrides1 = {"toxicity_threshold": 0.5}
            >>> overrides2 = {"toxicity_threshold": 0.8}
            >>> key1 = SecurityServiceFactory._generate_cache_key("local", config1, overrides1)
            >>> key2 = SecurityServiceFactory._generate_cache_key("local", config1, overrides2)
            >>> assert key1 != key2

            >>> # Cache key format validation
            >>> key = SecurityServiceFactory._generate_cache_key("local", config, {})
            >>> assert key.startswith("security_service_local_")
            >>> assert len(key) > len("security_service_local_")  # Has hash component
        """
        import hashlib
        import json

        # Create a deterministic representation of the configuration
        cache_data = {
            "mode": mode,
            "config": config.to_dict() if config else None,
            "overrides": environment_overrides or {},
        }

        cache_json = json.dumps(cache_data, sort_keys=True)
        cache_hash = hashlib.md5(cache_json.encode()).hexdigest()

        return f"security_service_{mode}_{cache_hash}"

    @classmethod
    def clear_cache(cls) -> None:
        """
        Clear all cached security service instances.

        This method removes all service instances from the factory cache, forcing
        subsequent service creation calls to instantiate new services. Useful for
        testing, configuration updates, or memory management.

        Behavior:
            - Removes all entries from the class-level service cache
            - Resets cache to empty state for fresh service instantiation
            - Does not affect currently running service instances
            - Thread-safe operation for concurrent access scenarios

        Examples:
            >>> # Cache with services
            >>> service1 = SecurityServiceFactory.create_service(mode="local")
            >>> stats_before = SecurityServiceFactory.get_cache_stats()
            >>> assert stats_before["cached_services"] > 0

            >>> # Clear cache
            >>> SecurityServiceFactory.clear_cache()
            >>> stats_after = SecurityServiceFactory.get_cache_stats()
            >>> assert stats_after["cached_services"] == 0

            >>> # Subsequent service creation creates new instances
            >>> service2 = SecurityServiceFactory.create_service(mode="local")
            >>> assert service2 is not service1  # Different instances
        """
        cls._service_cache.clear()

    @classmethod
    def get_cache_stats(cls) -> Dict[str, Any]:
        """
        Get statistics about the current service cache state.

        This method returns diagnostic information about the factory cache,
        including the number of cached services and their cache keys. Useful
        for monitoring, debugging, and performance optimization.

        Returns:
            Dictionary containing cache statistics:
            - cached_services: int, number of services currently cached
            - cache_keys: List[str], list of cache keys for cached services

        Behavior:
            - Returns snapshot of current cache state
            - Provides diagnostic information for monitoring
            - Lists all active cache keys for debugging
            - Returns empty cache statistics when no services are cached

        Examples:
            >>> # Empty cache statistics
            >>> SecurityServiceFactory.clear_cache()
            >>> stats = SecurityServiceFactory.get_cache_stats()
            >>> assert stats["cached_services"] == 0
            >>> assert stats["cache_keys"] == []

            >>> # Cache with multiple services
            >>> service1 = SecurityServiceFactory.create_service(mode="local")
            >>> service2 = SecurityServiceFactory.create_service(
            ...     mode="local",
            ...     cache_key="custom_service"
            ... )
            >>> stats = SecurityServiceFactory.get_cache_stats()
            >>> assert stats["cached_services"] == 2
            >>> assert len(stats["cache_keys"]) == 2
            >>> assert "custom_service" in stats["cache_keys"]

            >>> # Cache monitoring
            >>> stats = SecurityServiceFactory.get_cache_stats()
            >>> print(f"Cached services: {stats['cached_services']}")
            >>> print(f"Cache keys: {', '.join(stats['cache_keys'])}")
        """
        return {
            "cached_services": len(cls._service_cache),
            "cache_keys": list(cls._service_cache.keys()),
        }


# Global factory instance for convenience
_factory = SecurityServiceFactory()


def create_security_service(
    mode: str = "local",
    config: SecurityConfig | None = None,
    environment_overrides: Dict[str, Any] | None = None,
    cache_key: str | None = None,
) -> SecurityService:
    """
    Create a security service instance using the global factory.

    This is a convenience function that provides a simple interface for creating
    security service instances without directly managing the SecurityServiceFactory.
    It uses a shared global factory instance for efficient resource management.

    Args:
        mode: Service mode, one of ["local", "saas"] (default: "local")
              - "local": Local ML-based security scanning
              - "saas": Cloud-based security service (future implementation)
        config: Optional SecurityConfig object with detailed settings. If None,
               creates default configuration from environment variables
        environment_overrides: Optional dictionary of environment variable overrides
                              for runtime configuration adjustments
        cache_key: Optional cache key for service instance reuse. If None,
                  generates deterministic key based on configuration parameters

    Returns:
        Configured SecurityService instance ready for input validation and scanning

    Raises:
        ConfigurationError: If configuration is invalid, incomplete, or contains
                           contradictory settings
        InfrastructureError: If service creation fails due to missing dependencies,
                             model loading errors, or system resource issues

    Behavior:
            - Delegates to global SecurityServiceFactory instance for service creation
            - Provides same caching and configuration management as factory methods
            - Maintains shared cache state across multiple function calls
            - Handles all validation and error scenarios automatically
            - Returns cached service when identical configuration is requested

    Examples:
            >>> # Basic service creation with default configuration
            >>> service = create_security_service(mode="local")
            >>> result = await service.validate_input("Test input text")
            >>> assert hasattr(result, 'is_safe')

            >>> # Service with custom configuration
            >>> config = SecurityConfig.create_from_preset(PresetName.STRICT)
            >>> service = create_security_service(
            ...     mode="local",
            ...     config=config,
            ...     cache_key="strict_service"
            ... )
            >>> result = await service.validate_input("Another test")

            >>> # Service with environment overrides
            >>> overrides = {"toxicity_threshold": 0.8, "enable_caching": "true"}
            >>> service = create_security_service(
            ...     mode="local",
            ...     environment_overrides=overrides
            ... )

            >>> # Error handling for invalid configuration
            >>> with pytest.raises(ConfigurationError):
            ...     # Invalid configuration would raise exception
            ...     create_security_service(mode="invalid_mode")
    """
    return _factory.create_service(mode, config, environment_overrides, cache_key)


def get_security_service() -> SecurityService:
    """
    Get a security service instance for FastAPI dependency injection.

    This function creates a security service using environment-based configuration,
    making it ideal for FastAPI dependency injection scenarios where services
    should be automatically configured based on runtime environment.

    Returns:
        Configured SecurityService instance ready for input validation and scanning

    Behavior:
        - Reads SECURITY_MODE environment variable to determine service type
        - Defaults to "local" mode if SECURITY_MODE is not specified
        - Creates service using create_security_service with environment configuration
        - Returns cached service if available for improved performance
        - Automatically handles all configuration loading and validation

    Examples:
            >>> # FastAPI dependency injection usage
            >>> from fastapi import Depends
            >>> from app.infrastructure.security.llm import get_security_service
            >>>
            >>> @app.post("/chat")
            >>> async def chat(
            ...     message: str,
            ...     security_service: SecurityService = Depends(get_security_service)
            ... ):
            ...     result = await security_service.validate_input(message)
            ...     if not result.is_safe:
            ...         raise HTTPException(status_code=400, detail="Security violation")
            ...     return {"response": "AI response"}

            >>> # Environment-based configuration
            >>> # Set SECURITY_MODE=local in environment
            >>> service = get_security_service()
            >>> assert hasattr(service, 'validate_input')

            >>> # With different mode in environment
            >>> os.environ["SECURITY_MODE"] = "local"
            >>> service = get_security_service()
            >>> # Service uses "local" mode from environment

            >>> # FastAPI with custom dependencies
            >>> @app.get("/health")
            >>> async def health_check(
            ...     security_service: SecurityService = Depends(get_security_service)
            ... ):
            ...     return {"status": "healthy", "security": "active"}
    """
    # Determine mode from environment
    mode = os.getenv("SECURITY_MODE", "local").lower()
    return create_security_service(mode=mode)


def create_security_service_from_preset(
    preset: PresetName | str,
    mode: str = "local",
    environment: str = "development",
) -> SecurityService:
    """
    Create a security service instance from a predefined configuration preset.

    This function provides a simplified interface for creating security services
    using named configuration presets, making it easy to get started with common
    security configurations without managing detailed settings.

    Args:
        preset: Configuration preset name, either PresetName enum or string
               (balanced, strict, permissive, development, production)
        mode: Service mode, one of ["local", "saas"] (default: "local")
              - "local": Local ML-based security scanning
              - "saas": Cloud-based security service (future implementation)
        environment: Environment context for configuration preset settings
                    (development, production, testing, staging)

    Returns:
        Configured SecurityService instance initialized with the specified preset

    Raises:
        ConfigurationError: If the specified preset name is invalid or unsupported

    Behavior:
        - Converts string preset names to PresetName enum values
        - Creates SecurityConfig from preset using SecurityConfig.create_from_preset()
        - Delegates to create_security_service() for service instantiation
        - Handles preset validation and error scenarios automatically
        - Applies environment-specific settings based on environment parameter

    Examples:
            >>> # Using enum preset
            >>> from app.infrastructure.security.llm.config import PresetName
            >>> service = create_security_service_from_preset(
            ...     PresetName.STRICT,
            ...     mode="local",
            ...     environment="production"
            ... )
            >>> result = await service.validate_input("Test input")
            >>> assert hasattr(result, 'is_safe')

            >>> # Using string preset name
            >>> service = create_security_service_from_preset("balanced")
            >>> assert hasattr(service, 'validate_input')

            >>> # Different environments
            >>> dev_service = create_security_service_from_preset(
            ...     PresetName.STRICT,
            ...     environment="development"
            ... )
            >>> prod_service = create_security_service_from_preset(
            ...     PresetName.STRICT,
            ...     environment="production"
            ... )
            >>> # Services have different settings based on environment

            >>> # Error handling for invalid preset
            >>> with pytest.raises(ConfigurationError) as exc_info:
            ...     create_security_service_from_preset("invalid_preset")
            >>> assert "invalid preset" in str(exc_info.value).lower()

            >>> # Quick production setup
            >>> service = create_security_service_from_preset(
            ...     PresetName.PRODUCTION,
            ...     environment="production"
            ... )
            >>> # Service is ready for production use
    """
    if isinstance(preset, str):
        try:
            preset = PresetName(preset.lower())
        except ValueError:
            raise ConfigurationError(f"Invalid preset: {preset}")

    config = SecurityConfig.create_from_preset(preset, environment)
    return create_security_service(mode=mode, config=config)


def create_security_service_from_yaml(
    config_path: str | None = None,
    environment: str | None = None,
    mode: str = "local",
    cache_key: str | None = None,
) -> SecurityService:
    """
    Create a security service instance from YAML configuration files.

    This function provides file-based configuration management for security services,
    allowing detailed configuration through YAML files with environment-specific
    overrides. Ideal for production deployments with complex configuration requirements.

    Args:
        config_path: Path to configuration directory containing YAML files
                    (default: "config/security" relative to current working directory)
        environment: Environment name for configuration selection (development, production,
                    testing). If None, reads from SECURITY_ENVIRONMENT environment variable
                    or defaults to "development"
        mode: Service mode, one of ["local", "saas"] (default: "local")
              - "local": Local ML-based security scanning
              - "saas": Cloud-based security service (future implementation)
        cache_key: Optional cache key for service instance reuse. If None,
                  generates deterministic key based on configuration parameters

    Returns:
        Configured SecurityService instance initialized from YAML configuration

    Raises:
        ConfigurationError: If YAML configuration files are missing, malformed,
                           contain invalid settings, or fail validation
        InfrastructureError: If service creation fails due to missing dependencies,
                             model loading errors, or system resource issues

    Behavior:
        - Directly instantiates LocalLLMSecurityScanner with YAML configuration support
        - Handles configuration file discovery and loading automatically
        - Applies environment-specific configuration overrides
        - Validates configuration consistency and completeness
        - Handles both core ConfigurationError and config_loader.ConfigurationError
        - Provides detailed error messages with file paths and suggestions when possible
        - Supports flexible configuration directory structures

    Examples:
            >>> # Load from default path with current environment
            >>> service = create_security_service_from_yaml()
            >>> result = await service.validate_input("Test input")
            >>> assert hasattr(result, 'is_safe')

            >>> # Load from custom path with specific environment
            >>> service = create_security_service_from_yaml(
            ...     config_path="custom/security",
            ...     environment="production"
            ... )
            >>> # Service loaded from custom/security/production.yaml

            >>> # Environment variable based configuration
            >>> os.environ["SECURITY_ENVIRONMENT"] = "staging"
            >>> service = create_security_service_from_yaml(
            ...     config_path="config/security"
            ... )
            >>> # Service loaded from config/security/staging.yaml

            >>> # With custom cache key for reuse
            >>> service = create_security_service_from_yaml(
            ...     config_path="prod/security",
            ...     environment="production",
            ...     cache_key="prod_security_service"
            ... )

            >>> # Error handling for missing configuration
            >>> with pytest.raises(ConfigurationError) as exc_info:
            ...     create_security_service_from_yaml(
            ...         config_path="nonexistent/path",
            ...         environment="production"
            ...     )
            >>> assert "configuration" in str(exc_info.value).lower()

            >>> # Production deployment pattern
            >>> service = create_security_service_from_yaml(
            ...     config_path="/app/config/security",
            ...     environment=os.getenv("DEPLOYMENT_ENV", "production"),
            ...     cache_key=f"security_service_{os.getenv('DEPLOYMENT_ENV', 'production')}"
            ... )
            >>> # Service ready for production with proper configuration
    """
    try:
        from app.infrastructure.security.llm.scanners.local_scanner import LocalLLMSecurityScanner

        # Create scanner with YAML configuration
        return LocalLLMSecurityScanner(
            config_path=config_path,
            environment=environment
        )

    except Exception as e:
        # Handle both app.core.exceptions.ConfigurationError and config_loader.ConfigurationError
        if isinstance(e, InfrastructureError):
            raise
        if isinstance(e, ConfigurationError) or (hasattr(e, "__class__") and e.__class__.__name__ == "ConfigurationError"):
            # Convert config_loader.ConfigurationError to app.core.exceptions.ConfigurationError
            from app.core.exceptions import ConfigurationError as CoreConfigurationError
            if isinstance(e, ConfigurationError):
                raise
            # Convert the config_loader ConfigurationError to core ConfigurationError
            suggestion = getattr(e, "suggestion", None)
            file_path = getattr(e, "file_path", None)

            # Get the base message without the suggestion (remove the suggestion part from str(e))
            base_message = str(e)
            if suggestion and f"\nSuggestion: {suggestion}" in base_message:
                base_message = base_message.replace(f"\nSuggestion: {suggestion}", "").strip()

            raise CoreConfigurationError(base_message, {"file_path": file_path, "suggestion": suggestion}) from e

        raise InfrastructureError(
            f"Failed to create security service from YAML configuration: {e!s}"
        ) from e
