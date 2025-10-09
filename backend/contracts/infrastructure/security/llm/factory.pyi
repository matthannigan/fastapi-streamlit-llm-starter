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
from app.infrastructure.security.llm.config import PresetName, SecurityConfig
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

    @classmethod
    def create_service(cls, mode: str = 'local', config: SecurityConfig | None = None, environment_overrides: Dict[str, Any] | None = None, cache_key: str | None = None) -> SecurityService:
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
        ...

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
        ...

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
        ...


def create_security_service(mode: str = 'local', config: SecurityConfig | None = None, environment_overrides: Dict[str, Any] | None = None, cache_key: str | None = None) -> SecurityService:
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
    ...


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
    ...


def create_security_service_from_preset(preset: PresetName | str, mode: str = 'local', environment: str = 'development') -> SecurityService:
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
    ...


def create_security_service_from_yaml(config_path: str | None = None, environment: str | None = None, mode: str = 'local', cache_key: str | None = None) -> SecurityService:
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
    ...
