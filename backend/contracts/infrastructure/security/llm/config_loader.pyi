"""
Security Configuration Loader

This module provides comprehensive YAML-based configuration loading for security scanners.
It supports environment-specific overrides, environment variable interpolation, and
comprehensive validation with Pydantic models.

## Features

### Configuration Loading
- **YAML Parsing**: Load configuration from YAML files with full syntax validation
- **Environment Overrides**: Support for environment-specific configuration overrides
- **Variable Interpolation**: Support for environment variable interpolation in YAML
- **File Validation**: Comprehensive validation of configuration structure and values

### Configuration Merging
- **Base Configuration**: Load base configuration from scanners.yaml
- **Environment Overrides**: Merge environment-specific overrides (dev.yaml, prod.yaml, test.yaml)
- **Environment Variables**: Apply environment variable overrides with highest precedence
- **Deep Merging**: Proper deep merging of nested configuration structures

### Validation & Error Handling
- **Pydantic Validation**: Use Pydantic models for type-safe validation
- **Schema Validation**: Validate configuration against expected schema
- **Clear Error Messages**: Provide helpful error messages with suggestions
- **Validation Caching**: Cache validation results for performance

### Performance Features
- **Configuration Caching**: Cache loaded configuration to avoid repeated file I/O
- **Hot Reload**: Support for hot reload in development environments
- **Lazy Loading**: Load configuration only when needed
- **Memory Efficient**: Efficient memory usage with proper cleanup

## Usage

### Basic Usage
```python
from app.infrastructure.security.llm.config_loader import load_security_config

# Load configuration for current environment
config = load_security_config()

# Load configuration for specific environment
config = load_security_config(environment="production")
```

### Advanced Usage
```python
from app.infrastructure.security.llm.config_loader import SecurityConfigLoader

# Create loader with custom configuration path
loader = SecurityConfigLoader(
    config_path="custom/path/to/security/config",
    environment="staging"
)

# Load configuration with hot reload support
config = loader.load_config(enable_hot_reload=True)
```

### Environment Variable Overrides
```bash
# Override configuration with environment variables
SECURITY_PRESET=production
SECURITY_DEBUG=false
SECURITY_CACHE_ENABLED=true
SECURITY_MAX_CONCURRENT_SCANS=20
```

## Configuration Precedence

Configuration is applied in the following order (highest precedence last):
1. Base configuration (scanners.yaml)
2. Environment-specific overrides (dev.yaml, prod.yaml, test.yaml)
3. Environment variable overrides
4. Runtime overrides (if provided)

## File Structure

```
config/security/
├── scanners.yaml    # Base scanner configuration
├── dev.yaml        # Development environment overrides
├── prod.yaml       # Production environment overrides
└── test.yaml       # Testing environment overrides
```

## Environment Variables

The following environment variables are supported for configuration:
- `SECURITY_ENVIRONMENT`: Environment name (development, production, testing)
- `SECURITY_CONFIG_PATH`: Custom path to configuration directory
- `SECURITY_PRESET`: Configuration preset name
- `SECURITY_DEBUG`: Enable debug mode
- `SECURITY_CACHE_ENABLED`: Enable configuration caching
- `SECURITY_HOT_RELOAD`: Enable hot reload for development
"""

import os
import re
import time
from pathlib import Path
from typing import Any, Dict, Callable
import yaml
from pydantic import ValidationError
from .config import SecurityConfig


class ConfigurationError(Exception):
    """
    Exception raised for configuration-related errors with helpful context and suggestions.
    
    This custom exception provides enhanced error reporting for configuration issues,
    including file path context and actionable suggestions for resolution.
    
    Attributes:
        message: The base error message describing the configuration issue
        suggestion: Optional suggestion for resolving the configuration error
        file_path: Optional path to the configuration file where the error occurred
    
    Usage:
        >>> # Basic usage
        >>> raise ConfigurationError("Invalid YAML syntax")
    
        >>> # With suggestion
        >>> raise ConfigurationError(
        ...     "Missing required field: api_key",
        ...     suggestion="Add api_key to your configuration file"
        ... )
    
        >>> # With file context
        >>> raise ConfigurationError(
        ...     "Invalid port number",
        ...     suggestion="Port must be between 1-65535",
        ...     file_path="/path/to/config.yaml"
        ... )
    """

    def __init__(self, message: str, suggestion: str | None = None, file_path: str | None = None):
        """
        Initialize configuration error with context and optional suggestion.
        
        Args:
            message: Description of the configuration error
            suggestion: Optional suggestion for resolving the error
            file_path: Optional path to the configuration file where error occurred
        """
        ...

    def __str__(self) -> str:
        """
        Format error message with file context and suggestions.
        
        Returns:
            Formatted error message including file path and suggestion when available
        """
        ...


class SecurityConfigLoader:
    """
    Security configuration loader with YAML support, environment overrides, and validation.
    
    This class provides comprehensive configuration loading for security scanners,
    supporting YAML-based configuration files, environment-specific overrides,
    environment variable interpolation, Pydantic validation, and performance caching.
    
    Attributes:
        config_path: Path to the configuration directory containing YAML files
        environment: Current environment name (development, production, testing)
        cache_enabled: Whether configuration caching is enabled for performance
        cache_ttl: Cache time-to-live in seconds for cached configurations
        debug_mode: Whether debug mode is enabled for verbose logging
    
    Public Methods:
        load_config(): Load and validate security configuration with all overrides
        clear_cache(): Clear the internal configuration cache
        get_cache_info(): Get information about cache status and configuration
    
    State Management:
        - Maintains internal cache dictionary for loaded configurations
        - Tracks file modification times for cache invalidation
        - Thread-safe for read operations, write operations should be synchronized
        - Cache entries include timestamps and file modification metadata
        - Automatic cache invalidation when source files are modified
    
    Usage:
        # Basic usage with default configuration path
        loader = SecurityConfigLoader()
        config = loader.load_config()
    
        # Custom configuration and environment
        loader = SecurityConfigLoader(
            config_path="custom/security/config",
            environment="staging",
            cache_enabled=True,
            cache_ttl=600
        )
        config = loader.load_config()
    
        # Environment-specific loading
        prod_config = loader.load_config(environment="production")
        test_config = loader.load_config(environment="testing")
    
        # Cache management
        loader.clear_cache()  # Force reload next time
        cache_info = loader.get_cache_info()
        print(f"Cache enabled: {cache_info['cache_enabled']}")
    
        # Error handling
        try:
            config = loader.load_config()
        except ConfigurationError as e:
            print(f"Configuration error: {e}")
            if e.suggestion:
                print(f"Suggestion: {e.suggestion}")
    """

    def __init__(self, config_path: str | Path | None = None, environment: str | None = None, cache_enabled: bool = True, cache_ttl: int = 300, debug_mode: bool | None = None):
        """
        Initialize the security configuration loader with customizable settings.
        
        Creates a new configuration loader instance with support for custom paths,
        environment-specific loading, caching, and debug output.
        
        Args:
            config_path: Path to configuration directory containing YAML files.
                        Accepts string or Path objects. If None, uses SECURITY_CONFIG_PATH
                        environment variable or defaults to "config/security"
            environment: Environment name for loading environment-specific overrides.
                        If None, uses SECURITY_ENVIRONMENT environment variable or defaults to "development"
            cache_enabled: Whether to enable configuration caching for performance.
                          Can be disabled by SECURITY_CACHE_ENABLED environment variable
            cache_ttl: Cache time-to-live in seconds. Must be positive integer.
                      Configuration is refreshed after this period or when files are modified
            debug_mode: Enable debug mode for verbose logging and output.
                       If None, uses SECURITY_DEBUG environment variable (true/1/yes = enabled)
        
        Raises:
            ConfigurationError: If configuration directory does not exist or is inaccessible
        
        Behavior:
            - Resolves relative paths against current working directory
            - Validates configuration directory exists during initialization
            - Initializes internal cache and tracking structures
            - Reads environment variables for default values
            - Sets up debug logging if enabled
            - Prepares file modification tracking for cache invalidation
        
        Examples:
            >>> # Default initialization
            >>> loader = SecurityConfigLoader()
            >>> print(f"Config path: {loader.config_path}")
            >>> print(f"Environment: {loader.environment}")
        
            >>> # Custom configuration
            >>> loader = SecurityConfigLoader(
            ...     config_path="/etc/security/config",
            ...     environment="production",
            ...     cache_ttl=600
            ... )
        
            >>> # Development mode with debugging
            >>> loader = SecurityConfigLoader(
            ...     debug_mode=True,
            ...     cache_enabled=False  # Disable cache for development
            ... )
        
            >>> # Error handling for missing directory
            >>> try:
            ...     loader = SecurityConfigLoader(config_path="/nonexistent/path")
            ... except ConfigurationError as e:
            ...     print(f"Configuration error: {e}")
            ...     print(f"Suggestion: {e.suggestion}")
        """
        ...

    def load_config(self, environment: str | None = None, enable_hot_reload: bool = False, cache_bust: bool = False) -> SecurityConfig:
        """
        Load and validate security configuration with all overrides applied.
        
        This is the primary method for loading security configuration. It handles
        the complete configuration pipeline: base configuration loading, environment
        overrides, environment variable interpolation, validation, and caching.
        
        Args:
            environment: Override environment for this load operation.
                        If None, uses the instance's environment setting.
                        Common values: "development", "production", "testing"
            enable_hot_reload: Enable hot reload monitoring for development environments.
                              Only effective when environment is "development".
                              Currently provides logging about hot reload status
            cache_bust: Force cache refresh and reload all configuration from disk.
                       Ignores existing cached entries and rebuilds cache with fresh data
        
        Returns:
            SecurityConfig: Fully validated configuration object containing:
                           - Scanner configurations with thresholds and settings
                           - Performance settings (caching, concurrency limits)
                           - Logging configuration
                           - Environment-specific overrides already applied
                           - All values validated against Pydantic schemas
        
        Raises:
            ConfigurationError: If any configuration step fails:
                               - Base configuration file missing or invalid YAML
                               - Environment override file has syntax errors
                               - Required fields missing from configuration
                               - Invalid values outside allowed ranges
                               - Pydantic validation errors
        
        Behavior:
            - Checks cache first unless cache_bust is True
            - Loads base configuration from scanners.yaml with environment variable interpolation
            - Applies environment-specific overrides from {environment}.yaml if present
            - Applies environment variable overrides with highest precedence
            - Deep merges all configuration levels with proper precedence
            - Validates final configuration against Pydantic SecurityConfig model
            - Performs additional business logic validation (scanner names, thresholds)
            - Caches validated configuration if caching is enabled
            - Sets up hot reload monitoring if requested and in development
            - Returns configuration ready for use by security scanners
        
        Examples:
            >>> # Load configuration for default environment
            >>> loader = SecurityConfigLoader()
            >>> config = loader.load_config()
            >>> print(f"Environment: {config.environment}")
            >>> enabled_scanners = config.get_enabled_scanners()
            >>> print(f"Enabled scanners: {len(enabled_scanners)}")
        
            >>> # Load specific environment configuration
            >>> prod_config = loader.load_config(environment="production")
            >>> test_config = loader.load_config(environment="testing")
        
            >>> # Force reload from disk (cache bypass)
            >>> fresh_config = loader.load_config(cache_bust=True)
        
            >>> # Enable hot reload for development
            >>> dev_config = loader.load_config(
            ...     environment="development",
            ...     enable_hot_reload=True
            ... )
        
            >>> # Error handling for invalid configuration
            >>> try:
            ...     config = loader.load_config(environment="invalid")
            ... except ConfigurationError as e:
            ...     print(f"Configuration error: {e}")
            ...     if e.suggestion:
            ...         print(f"Suggestion: {e.suggestion}")
        """
        ...

    def clear_cache(self) -> None:
        """
        Clear configuration cache.
        """
        ...

    def get_cache_info(self) -> Dict[str, Any]:
        """
        Get information about configuration cache.
        """
        ...


def get_config_loader() -> SecurityConfigLoader:
    """
    Get or create global SecurityConfigLoader instance with singleton pattern.
    
    This function provides access to a shared configuration loader instance
    that can be reused across the application for consistent configuration loading.
    
    Returns:
        SecurityConfigLoader: Global configuration loader instance with:
                            - Default configuration path and environment settings
                            - Caching enabled for performance
                            - Initialized and ready to load configurations
    
    Behavior:
            - Creates new SecurityConfigLoader instance on first call
            - Reuses existing instance on subsequent calls (singleton pattern)
            - Uses default settings (config_path from SECURITY_CONFIG_PATH or "config/security")
            - Maintains global state for configuration caching and efficiency
            - Provides consistent configuration loading across application modules
    
    Usage:
        >>> # Get global loader instance
        >>> loader = get_config_loader()
        >>> config = loader.load_config()
        >>>
        >>> # Multiple calls return same instance
        >>> loader2 = get_config_loader()
        >>> assert loader is loader2  # Same instance
        >>>
        >>> # Use for consistent configuration loading
        >>> from app.infrastructure.security.llm.config_loader import get_config_loader
        >>> loader = get_config_loader()
        >>> production_config = loader.load_config(environment="production")
        >>> test_config = loader.load_config(environment="testing")
    
    Thread Safety:
        - Thread-safe for read operations after initialization
        - Multiple threads can safely use the same loader instance
        - Configuration loading is thread-safe due to immutable cache entries
    """
    ...


def load_security_config(environment: str | None = None, config_path: str | None = None, enable_hot_reload: bool = False, cache_bust: bool = False) -> SecurityConfig:
    """
    Load security configuration with sensible defaults and automatic loader management.
    
    This is the main entry point for loading security configuration. It handles all
    the complexity of loading, merging, validation, and loader instantiation automatically.
    
    Args:
        environment: Environment name for loading specific overrides.
                    If None, uses SECURITY_ENVIRONMENT environment variable or "development"
                    Common values: "development", "production", "testing", "staging"
        config_path: Custom configuration directory path containing YAML files.
                    If None, uses SECURITY_CONFIG_PATH environment variable or "config/security"
                    Must contain scanners.yaml and optional {environment}.yaml files
        enable_hot_reload: Enable hot reload monitoring for development environments.
                          Only effective when environment is "development".
                          Provides logging about configuration file changes
        cache_bust: Force cache refresh and reload all configuration from disk.
                   Ignores existing cached entries and rebuilds cache with fresh data
    
    Returns:
        SecurityConfig: Fully validated and ready-to-use configuration containing:
                       - All scanner configurations with thresholds and settings
                       - Performance settings (caching, concurrency limits)
                       - Logging configuration
                       - Environment-specific overrides applied
                       - All values validated against business rules
    
    Raises:
        ConfigurationError: If configuration loading fails:
                           - Configuration directory doesn't exist
                           - Required scanners.yaml file missing or invalid
                           - Environment override files have syntax errors
                           - Required fields missing from configuration
                           - Invalid values outside allowed ranges
                           - Pydantic validation errors
    
    Behavior:
            - Creates new SecurityConfigLoader if custom settings provided
            - Reuses global loader instance for default settings (efficiency)
            - Automatically handles environment variable detection
            - Applies full configuration pipeline: base → env overrides → env vars → validation
            - Returns configuration ready for immediate use by security scanners
            - Maintains caching for performance unless cache_bust is True
    
    Examples:
        >>> # Basic usage with default settings
        >>> config = load_security_config()
        >>> print(f"Environment: {config.environment}")
        >>> enabled_scanners = config.get_enabled_scanners()
        >>> print(f"Enabled scanners: {len(enabled_scanners)}")
    
        >>> # Load specific environment configuration
        >>> prod_config = load_security_config(environment="production")
        >>> test_config = load_security_config(environment="testing")
    
        >>> # Custom configuration path
        >>> config = load_security_config(
        ...     config_path="/etc/security/config",
        ...     environment="staging"
        ... )
    
        >>> # Force reload from disk (cache bypass)
        >>> fresh_config = load_security_config(cache_bust=True)
    
        >>> # Development mode with hot reload
        >>> dev_config = load_security_config(
        ...     environment="development",
        ...     enable_hot_reload=True
        ... )
    
        >>> # Error handling for configuration issues
        >>> try:
        ...     config = load_security_config(environment="invalid")
        ... except ConfigurationError as e:
        ...     print(f"Configuration error: {e}")
        ...     if e.suggestion:
        ...         print(f"Suggestion: {e.suggestion}")
    
    Environment Variables:
        - SECURITY_ENVIRONMENT: Default environment name if not specified
        - SECURITY_CONFIG_PATH: Default configuration directory if not specified
        - SECURITY_DEBUG: Enable debug output (true/1/yes)
        - SECURITY_CACHE_ENABLED: Enable configuration caching (true/1/yes)
    """
    ...


def reload_security_config(environment: str | None = None, config_path: str | None = None) -> SecurityConfig:
    """
    Force reload security configuration by bypassing all caches.
    
    This function ensures configuration is freshly loaded from disk, ignoring any
    cached entries. Useful when configuration files have been modified or when
    testing configuration changes.
    
    Args:
        environment: Environment name for loading specific overrides.
                    If None, uses SECURITY_ENVIRONMENT environment variable or "development"
                    Common values: "development", "production", "testing", "staging"
        config_path: Custom configuration directory path containing YAML files.
                    If None, uses SECURITY_CONFIG_PATH environment variable or "config/security"
                    Must contain scanners.yaml and optional {environment}.yaml files
    
    Returns:
        SecurityConfig: Freshly loaded configuration containing:
                       - All scanner configurations with thresholds and settings
                       - Performance settings (caching, concurrency limits)
                       - Logging configuration
                       - Environment-specific overrides applied
                       - Latest values from disk (cache bypassed)
    
    Raises:
        ConfigurationError: If configuration loading fails:
                           - Configuration directory doesn't exist
                           - Required scanners.yaml file missing or invalid
                           - Environment override files have syntax errors
                           - Required fields missing from configuration
                           - Invalid values outside allowed ranges
                           - Pydantic validation errors
    
    Behavior:
            - Calls load_security_config with cache_bust=True to force fresh load
            - Bypasses all existing cache entries regardless of TTL or file modification times
            - Creates new SecurityConfigLoader if custom settings provided
            - Rebuilds cache with fresh configuration data
            - Returns configuration that reflects current state of all files
            - Useful for configuration changes during development or runtime updates
    
    Examples:
        >>> # Force reload with default settings
        >>> config = reload_security_config()
        >>> print(f"Freshly loaded configuration: {config.environment}")
    
        >>> # Reload specific environment configuration
        >>> prod_config = reload_security_config(environment="production")
        >>> test_config = reload_security_config(environment="testing")
    
        >>> # Reload from custom configuration path
        >>> config = reload_security_config(
        ...     config_path="/etc/security/config",
        ...     environment="staging"
        ... )
    
        >>> # Use after modifying configuration files
        >>> # Modify config/security/scanners.yaml...
        >>> config = reload_security_config()  # Gets latest changes
    
        >>> # Error handling for configuration issues
        >>> try:
        ...     config = reload_security_config(environment="invalid")
        ... except ConfigurationError as e:
        ...     print(f"Configuration reload failed: {e}")
        ...     if e.suggestion:
        ...         print(f"Suggestion: {e.suggestion}")
    
    Use Cases:
        - Development: Refresh configuration after editing YAML files
        - Runtime updates: Apply configuration changes without restarting application
        - Testing: Ensure clean state for test isolation
        - Troubleshooting: Verify configuration loading works with fresh data
    
    Performance Considerations:
        - Forces complete reload of all configuration files
        - Rebuilds cache from scratch (more expensive than regular load)
        - Should be used when cache invalidation is needed
        - Regular load_security_config() preferred for normal operation
    """
    ...
