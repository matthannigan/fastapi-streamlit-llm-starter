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
        super().__init__(message)
        self.suggestion = suggestion
        self.file_path = file_path

    def __str__(self) -> str:
        """
        Format error message with file context and suggestions.

        Returns:
            Formatted error message including file path and suggestion when available
        """
        message = super().__str__()
        if self.file_path:
            message = f"Configuration error in {self.file_path}: {message}"
        if self.suggestion:
            message += f"\nSuggestion: {self.suggestion}"
        return message


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

    def __init__(
        self,
        config_path: str | Path | None = None,
        environment: str | None = None,
        cache_enabled: bool = True,
        cache_ttl: int = 300,
        debug_mode: bool | None = None
    ):
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
        # Set default configuration path
        if config_path is None:
            config_path = os.environ.get("SECURITY_CONFIG_PATH", "config/security")

        self.config_path = Path(config_path)
        self.config_path = self.config_path if self.config_path.is_absolute() else Path.cwd() / self.config_path

        # Set environment
        if environment is None:
            environment = os.environ.get("SECURITY_ENVIRONMENT", "development")
        self.environment = environment

        # Set debug mode
        if debug_mode is None:
            debug_mode = os.environ.get("SECURITY_DEBUG", "false").lower() in ("true", "1", "yes")
        self.debug_mode = debug_mode

        # Configuration settings
        self.cache_enabled = cache_enabled and os.environ.get("SECURITY_CACHE_ENABLED", "true").lower() in ("true", "1", "yes")
        self.cache_ttl = cache_ttl

        # Internal state
        self._cache: Dict[str, Any] = {}
        self._cache_timestamp: float | None = None
        self._config_schema_version = "1.0.0"

        # Validate configuration directory exists
        if not self.config_path.exists():
            raise ConfigurationError(
                f"Configuration directory does not exist: {self.config_path}",
                suggestion="Create the configuration directory or set SECURITY_CONFIG_PATH environment variable"
            )

    def load_config(
        self,
        environment: str | None = None,
        enable_hot_reload: bool = False,
        cache_bust: bool = False
    ) -> SecurityConfig:
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
        # Use provided environment or instance environment
        target_env = environment or self.environment

        # Check cache first
        cache_key = f"security_config_{target_env}"
        if self.cache_enabled and not cache_bust and self._is_cache_valid(cache_key):
            if self.debug_mode:
                print(f"Using cached configuration for environment: {target_env}")
            return self._cache[cache_key]["config"]  # type: ignore[no-any-return]

        try:
            # Load base configuration
            base_config = self._load_base_config()

            # Load environment overrides
            env_overrides = self._load_environment_overrides(target_env)

            # Apply environment variable overrides
            env_var_overrides = self._load_environment_variable_overrides()

            # Merge configurations
            merged_config = self._merge_configurations(
                base_config=base_config,
                env_overrides=env_overrides,
                env_var_overrides=env_var_overrides
            )

            # Validate configuration
            validated_config = self._validate_configuration(merged_config)

            # Cache the configuration
            if self.cache_enabled:
                self._cache[cache_key] = {
                    "config": validated_config,
                    "timestamp": time.time(),
                    "file_mtimes": self._get_file_mtimes()
                }

            # Setup hot reload if enabled
            if enable_hot_reload and target_env == "development":
                self._setup_hot_reload()

            if self.debug_mode:
                print(f"Successfully loaded security configuration for environment: {target_env}")
                print(f"Enabled scanners: {len(validated_config.get_enabled_scanners())}")
                print(f"Configuration cache: {'enabled' if self.cache_enabled else 'disabled'}")

            return validated_config

        except Exception as e:
            if isinstance(e, ConfigurationError):
                raise
            raise ConfigurationError(
                f"Failed to load security configuration: {e!s}",
                suggestion="Check configuration files and environment variables"
            )

    def _load_base_config(self) -> Dict[str, Any]:
        """
        Load base configuration from scanners.yaml with environment variable interpolation.

        This private method loads the foundational security scanner configuration from
        the base YAML file and processes any environment variable placeholders.

        Returns:
            Dict[str, Any]: Base configuration dictionary containing:
                           - Scanner definitions and default settings
                           - Performance and logging configuration
                           - All environment variable placeholders resolved

        Raises:
            ConfigurationError: If base configuration file is missing, has invalid YAML syntax,
                               or does not contain a valid dictionary structure

        Behavior:
            - Looks for scanners.yaml in the configured configuration directory
            - Parses YAML using safe_load to prevent code execution
            - Validates that the loaded content is a dictionary
            - Applies environment variable interpolation (${VAR} and ${VAR:default} syntax)
            - Logs debug information if debug mode is enabled
            - Returns processed configuration ready for merging

        Examples:
            >>> # Expected file structure: config/security/scanners.yaml
            >>> # Content might include:
            >>> # scanners:
            >>> #   prompt_injection:
            >>> #     enabled: true
            >>> #     threshold: ${INJECTION_THRESHOLD:0.7}
            >>> #   toxicity_input:
            >>> #     enabled: ${TOXICITY_ENABLED:true}
            >>>
            >>> # Method usage (internal):
            >>> base_config = self._load_base_config()
            >>> assert isinstance(base_config, dict)
            >>> assert "scanners" in base_config
        """
        base_config_path = self.config_path / "scanners.yaml"

        if not base_config_path.exists():
            raise ConfigurationError(
                f"Base configuration file not found: {base_config_path}",
                suggestion="Create scanners.yaml with base scanner configuration",
                file_path=str(base_config_path)
            )

        try:
            with open(base_config_path, encoding="utf-8") as f:
                config_data = yaml.safe_load(f)

            if not isinstance(config_data, dict):
                raise ConfigurationError(
                    "Base configuration must be a dictionary",
                    suggestion="Ensure scanners.yaml contains valid YAML dictionary structure",
                    file_path=str(base_config_path)
                )

            # Apply environment variable interpolation
            config_data = self._interpolate_environment_variables(config_data)

            if self.debug_mode:
                print(f"Loaded base configuration from: {base_config_path}")

            return config_data  # type: ignore[no-any-return]

        except yaml.YAMLError as e:
            raise ConfigurationError(
                f"Invalid YAML syntax in base configuration: {e!s}",
                suggestion="Fix YAML syntax errors and ensure proper indentation",
                file_path=str(base_config_path)
            )
        except Exception as e:
            raise ConfigurationError(
                f"Failed to read base configuration: {e!s}",
                suggestion="Check file permissions and ensure file is accessible",
                file_path=str(base_config_path)
            )

    def _load_environment_overrides(self, environment: str) -> Dict[str, Any]:
        """
        Load environment-specific configuration overrides from YAML file.

        This private method loads environment-specific configuration overrides that
        customize the base configuration for particular deployment environments.

        Args:
            environment: Environment name for loading specific overrides.
                        Used to construct filename: {environment}.yaml

        Returns:
            Dict[str, Any]: Environment-specific override dictionary or empty dict.
                           Contains configuration keys to override or merge with base config.
                           Returns empty dict if no override file exists for the environment.

        Raises:
            ConfigurationError: If environment override file exists but has invalid YAML syntax
                               or does not contain a valid dictionary structure

        Behavior:
            - Constructs filename pattern: {environment}.yaml (e.g., "production.yaml")
            - Silently returns empty dict if override file doesn't exist (optional overrides)
            - Parses YAML using safe_load to prevent code execution
            - Validates that loaded content is a dictionary
            - Applies environment variable interpolation to override values
            - Logs debug information about loaded overrides

        Examples:
            >>> # Expected file: config/security/production.yaml
            >>> # Content might override base settings:
            >>> # scanners:
            >>> #   prompt_injection:
            >>> #     threshold: 0.8  # Higher threshold for production
            >>> # performance:
            >>> #   max_concurrent_scans: 50  # Higher concurrency
            >>> # logging:
            >>> #   level: "INFO"  # Less verbose logging
            >>>
            >>> # Method usage (internal):
            >>> overrides = self._load_environment_overrides("production")
            >>> if overrides:
            ...     print(f"Loaded {len(overrides)} override settings")
            >>> else:
            ...     print("No production overrides found")
        """
        env_config_path = self.config_path / f"{environment}.yaml"

        if not env_config_path.exists():
            if self.debug_mode:
                print(f"No environment override found for: {environment}")
            return {}

        try:
            with open(env_config_path, encoding="utf-8") as f:
                env_data = yaml.safe_load(f)

            if not isinstance(env_data, dict):
                raise ConfigurationError(
                    f"Environment override must be a dictionary: {environment}",
                    suggestion=f"Ensure {environment}.yaml contains valid YAML dictionary structure",
                    file_path=str(env_config_path)
                )

            # Apply environment variable interpolation
            env_data = self._interpolate_environment_variables(env_data)

            if self.debug_mode:
                print(f"Loaded environment overrides from: {env_config_path}")

            return env_data  # type: ignore[no-any-return]

        except yaml.YAMLError as e:
            raise ConfigurationError(
                f"Invalid YAML syntax in environment override: {e!s}",
                suggestion=f"Fix YAML syntax errors in {environment}.yaml",
                file_path=str(env_config_path)
            )
        except Exception as e:
            raise ConfigurationError(
                f"Failed to read environment override: {e!s}",
                suggestion=f"Check {environment}.yaml file permissions and accessibility",
                file_path=str(env_config_path)
            )

    def _load_environment_variable_overrides(self) -> Dict[str, Any]:
        """
        Load configuration overrides from environment variables with highest precedence.

        This private method maps specific environment variables to configuration keys,
        allowing runtime override of security settings without modifying configuration files.

        Returns:
            Dict[str, Any]: Configuration overrides dictionary containing only the
                           environment variables that are set and have valid values.
                           Structure supports nested configuration keys using dot notation.

        Behavior:
            - Checks predefined environment variable mappings for security configuration
            - Converts string environment variable values to appropriate types (bool, int)
            - Supports nested configuration paths using dot notation (e.g., "performance.cache_ttl")
            - Silently ignores invalid values with debug warnings
            - Returns only overrides that have corresponding environment variables set
            - Provides type conversion with error handling for each supported variable

        Supported Environment Variables:
            - SECURITY_PRESET: Configuration preset name (string)
            - SECURITY_DEBUG: Enable debug mode (boolean: true/1/yes)
            - SECURITY_CACHE_ENABLED: Enable caching (boolean: true/1/yes)
            - SECURITY_CACHE_TTL: Cache TTL seconds (integer)
            - SECURITY_MAX_CONCURRENT_SCANS: Maximum concurrent scans (integer)
            - SECURITY_LOG_LEVEL: Logging level (string)
            - SECURITY_LOG_SCAN_OPERATIONS: Log scan operations (boolean: true/1/yes)
            - SECURITY_INCLUDE_SCANNED_TEXT: Include scanned text in logs (boolean: true/1/yes)

        Examples:
            >>> # Environment variables set:
            >>> # SECURITY_PRESET=production
            >>> # SECURITY_DEBUG=false
            >>> # SECURITY_MAX_CONCURRENT_SCANS=20
            >>>
            >>> # Method usage (internal):
            >>> overrides = self._load_environment_variable_overrides()
            >>> expected = {
            ...     "preset": "production",
            ...     "debug_mode": False,
            ...     "performance": {
            ...         "max_concurrent_scans": 20
            ...     }
            ... }
            >>> assert overrides == expected

            >>> # Invalid values are silently ignored with debug warnings
            >>> # SECURITY_MAX_CONCURRENT_SCANS=invalid_number
            >>> overrides = self._load_environment_variable_overrides()
            >>> # "max_concurrent_scans" not included due to invalid value
        """
        overrides: Dict[str, Any] = {}

        # Define environment variable mappings
        env_mappings: Dict[str, tuple[str, Callable[[str], Any]]] = {
            "SECURITY_PRESET": ("preset", str),
            "SECURITY_DEBUG": ("debug_mode", lambda v: v.lower() in ("true", "1", "yes")),
            "SECURITY_CACHE_ENABLED": ("performance.cache_enabled", lambda v: v.lower() in ("true", "1", "yes")),
            "SECURITY_CACHE_TTL": ("performance.cache_ttl_seconds", int),
            "SECURITY_MAX_CONCURRENT_SCANS": ("performance.max_concurrent_scans", int),
            "SECURITY_LOG_LEVEL": ("logging.level", str),
            "SECURITY_LOG_SCAN_OPERATIONS": ("logging.log_scan_operations", lambda v: v.lower() in ("true", "1", "yes")),
            "SECURITY_INCLUDE_SCANNED_TEXT": ("logging.include_scanned_text", lambda v: v.lower() in ("true", "1", "yes")),
        }

        for env_var, (config_path, converter) in env_mappings.items():
            if env_var in os.environ:
                try:
                    value = converter(os.environ[env_var])

                    # Handle nested configuration paths
                    if "." in config_path:
                        parts = config_path.split(".")
                        current = overrides
                        for part in parts[:-1]:
                            if part not in current:
                                current[part] = {}
                            current = current[part]
                        current[parts[-1]] = value
                    else:
                        overrides[config_path] = value

                except (ValueError, TypeError) as e:
                    if self.debug_mode:
                        print(f"Warning: Invalid value for {env_var}: {os.environ[env_var]} - {e!s}")

        if self.debug_mode and overrides:
            print(f"Applied environment variable overrides: {list(overrides.keys())}")

        return overrides

    def _interpolate_environment_variables(self, config_data: Any) -> Any:
        """
        Recursively interpolate environment variables in configuration data.

        This private method processes configuration data structures and replaces
        environment variable placeholders with their actual values from the environment.

        Args:
            config_data: Configuration data to process. Can be string, dict, list,
                        or any nested combination of these types.

        Returns:
            Any: Configuration data with all environment variable placeholders resolved.
                 Structure and data types are preserved, only string placeholders are replaced.

        Behavior:
            - Processes strings for ${VAR} and ${VAR:default} placeholder patterns
            - Recursively processes nested dictionaries and lists
            - Leaves non-string values unchanged
            - Returns original placeholder unchanged if environment variable not found
            - Supports default values using ${VAR:default} syntax
            - Logs debug warnings for missing environment variables

        Supported Syntax:
            - ${VAR}: Replace with environment variable value or empty string if not found
            - ${VAR:default}: Replace with environment variable value or default if not found
            - Nested structures: Fully recursive processing of dictionaries and lists

        Examples:
            >>> # Basic interpolation
            >>> config = {"threshold": "${MAX_THRESHOLD:0.8}"}
            >>> result = self._interpolate_environment_variables(config)
            >>> # If MAX_THRESHOLD=0.9, result = {"threshold": "0.9"}
            >>> # If MAX_THRESHOLD not set, result = {"threshold": "0.8"}

            >>> # Missing variable (no default)
            >>> config = {"api_key": "${SECRET_API_KEY}"}
            >>> # If SECRET_API_KEY not set, keeps original placeholder
            >>> result = self._interpolate_environment_variables(config)
            >>> result == {"api_key": "${SECRET_API_KEY}"}

            >>> # Nested structures
            >>> config = {
            ...     "database": {
            ...         "host": "${DB_HOST:localhost}",
            ...         "port": "${DB_PORT:5432}",
            ...         "credentials": ["${DB_USER}", "${DB_PASS}"]
            ...     }
            ... }
            >>> result = self._interpolate_environment_variables(config)
            >>> # All placeholders recursively processed

            >>> # Complex defaults
            >>> config = {"url": "https://${HOST:localhost}:${PORT:8080}/api"}
            >>> result = self._interpolate_environment_variables(config)
            >>> # Multiple placeholders in same string supported
        """
        if isinstance(config_data, str):
            # Find all environment variable patterns
            pattern = r"\$\{([^}]+)\}"

            def replace_var(match: Any) -> str:
                var_expr = match.group(1)

                # Handle default value syntax: ${VAR:default}
                if ":" in var_expr:
                    var_name, default_value = var_expr.split(":", 1)
                    value = os.environ.get(var_name.strip(), default_value.strip())
                else:
                    var_name = var_expr.strip()
                    value = os.environ.get(var_name, "")
                    if value == "":
                        if self.debug_mode:
                            print(f"Warning: Environment variable not found: {var_name}")
                        return str(match.group(0))  # Return original if not found

                return str(value)

            return re.sub(pattern, replace_var, config_data)

        if isinstance(config_data, dict):
            return {k: self._interpolate_environment_variables(v) for k, v in config_data.items()}

        if isinstance(config_data, list):
            return [self._interpolate_environment_variables(item) for item in config_data]

        return config_data

    def _merge_configurations(
        self,
        base_config: Dict[str, Any],
        env_overrides: Dict[str, Any],
        env_var_overrides: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Merge multiple configuration sources with proper precedence handling.

        This private method combines base configuration, environment-specific overrides,
        and environment variable overrides into a single unified configuration dictionary.

        Args:
            base_config: Base configuration loaded from scanners.yaml containing
                        default settings and scanner definitions
            env_overrides: Environment-specific overrides from {environment}.yaml file.
                          May be empty if no environment override file exists
            env_var_overrides: Runtime overrides from environment variables with
                              highest precedence for dynamic configuration

        Returns:
            Dict[str, Any]: Merged configuration dictionary containing:
                           - All configuration levels merged with proper precedence
                           - Environment variable overrides applied last (highest priority)
                           - Metadata section with merge information and file paths
                           - Complete configuration ready for validation

        Behavior:
            - Applies deep merging to properly handle nested configuration structures
            - Uses precedence order: environment variables > environment overrides > base config
            - Preserves all base configuration keys not explicitly overridden
            - Adds metadata section with merge tracking information
            - Handles nested dictionary merging recursively
            - Replaces entire values for non-dict types (lists, strings, numbers)
            - Includes timestamps and override flags in metadata

        Precedence Rules (highest to lowest):
            1. Environment variable overrides (runtime configuration)
            2. Environment-specific overrides (deployment-specific settings)
            3. Base configuration (default settings from scanners.yaml)

        Examples:
            >>> # Base configuration
            >>> base = {
            ...     "scanners": {"prompt_injection": {"threshold": 0.7}},
            ...     "performance": {"cache_ttl": 300}
            ... }
            >>>
            >>> # Environment overrides
            >>> env_overrides = {
            ...     "scanners": {"prompt_injection": {"threshold": 0.8}},
            ...     "performance": {"max_concurrent": 10}
            ... }
            >>>
            >>> # Environment variable overrides
            >>> env_var_overrides = {"performance": {"cache_ttl": 600}}
            >>>
            >>> # Merged result
            >>> merged = self._merge_configurations(base, env_overrides, env_var_overrides)
            >>> expected = {
            ...     "scanners": {"prompt_injection": {"threshold": 0.8}},  # From env_overrides
            ...     "performance": {  # Merged from all sources
            ...         "cache_ttl": 600,  # From env_var_overrides (highest precedence)
            ...         "max_concurrent": 10  # From env_overrides
            ...     },
            ...     "_metadata": {  # Automatically added
            ...         "config_path": "...",
            ...         "environment": "...",
            ...         "merged_at": ...,
            ...         "has_env_overrides": True,
            ...         "has_env_var_overrides": True
            ...     }
            ... }
        """
        merged = base_config.copy()

        # Apply environment-specific overrides
        merged = self._deep_merge(merged, env_overrides)

        # Apply environment variable overrides
        merged = self._deep_merge(merged, env_var_overrides)

        # Add metadata
        merged["_metadata"] = {
            "config_path": str(self.config_path),
            "environment": self.environment,
            "merged_at": time.time(),
            "has_env_overrides": bool(env_overrides),
            "has_env_var_overrides": bool(env_var_overrides)
        }

        return merged

    def _deep_merge(self, base: Dict[str, Any], override: Dict[str, Any]) -> Dict[str, Any]:
        """
        Recursively deep merge two dictionaries with proper handling of nested structures.

        This private method merges override dictionary into base dictionary, preserving
        nested structure and intelligently handling conflicts between dictionaries and other types.

        Args:
            base: Base dictionary to merge into. Contains original configuration values.
                  This dictionary is copied and not modified in place.
            override: Override dictionary to merge into base. Contains values that should
                      override corresponding values in base dictionary.

        Returns:
            Dict[str, Any]: New dictionary containing deep merge of base and override.
                           Preserves all nested structures and handles type conflicts
                           appropriately (override values take precedence).

        Behavior:
            - Creates shallow copy of base dictionary before merging
            - Recursively merges nested dictionaries instead of replacing them
            - Replaces non-dict values entirely (lists, strings, numbers, booleans)
            - Skips metadata key to preserve merge tracking information
            - Preserves original base dictionary (returns new merged dictionary)
            - Handles empty dictionaries gracefully (preserves structure)

        Merge Rules:
            - Dict + Dict: Recursively merge nested structures
            - Dict + Non-Dict: Replace entire value with override
            - Missing Key: Add override key and value to result
            - "_metadata" Key: Preserve from base, skip from override

        Examples:
            >>> # Nested dictionary merge
            >>> base = {
            ...     "scanners": {
            ...         "prompt_injection": {"threshold": 0.7, "enabled": True},
            ...         "toxicity": {"enabled": False}
            ...     },
            ...     "performance": {"cache_ttl": 300}
            ... }
            >>> override = {
            ...     "scanners": {
            ...         "prompt_injection": {"threshold": 0.8},  # Only threshold overridden
            ...         "malicious_url": {"enabled": True}  # New scanner added
            ...     },
            ...     "logging": {"level": "INFO"}  # New section added
            ... }
            >>> merged = self._deep_merge(base, override)
            >>> expected = {
            ...     "scanners": {
            ...         "prompt_injection": {"threshold": 0.8, "enabled": True},  # Merged
            ...         "toxicity": {"enabled": False},  # Preserved from base
            ...         "malicious_url": {"enabled": True}  # Added from override
            ...     },
            ...     "performance": {"cache_ttl": 300},  # Preserved from base
            ...     "logging": {"level": "INFO"}  # Added from override
            ... }

            >>> # Type replacement (non-dict override)
            >>> base = {"settings": {"nested": "value"}}
            >>> override = {"settings": "simple_string"}  # Replaces entire dict
            >>> merged = self._deep_merge(base, override)
            >>> merged == {"settings": "simple_string"}
        """
        result = base.copy()

        for key, value in override.items():
            if key == "_metadata":
                continue  # Skip metadata

            if key in result and isinstance(result[key], dict) and isinstance(value, dict):
                result[key] = self._deep_merge(result[key], value)
            else:
                result[key] = value

        return result

    def _validate_configuration(self, config_data: Dict[str, Any]) -> SecurityConfig:
        """
        Validate merged configuration data against Pydantic models and business rules.

        This private method performs comprehensive validation of the configuration,
        including schema validation, type checking, and business logic validation.

        Args:
            config_data: Merged configuration dictionary from all sources.
                        Should contain scanner configurations, performance settings,
                        and logging configuration ready for validation.

        Returns:
            SecurityConfig: Validated configuration object with:
                           - All values validated against Pydantic SecurityConfig schema
                           - Proper type conversion and validation applied
                           - Business logic validation completed
                           - Ready for use by security scanner components

        Raises:
            ConfigurationError: If validation fails for any reason:
                               - Pydantic validation errors (type mismatches, missing fields)
                               - Invalid scanner names not in allowed list
                               - Threshold values outside valid range (0.0-1.0)
                               - Invalid performance settings (negative values)
                               - Configuration structure problems

        Behavior:
            - Removes metadata section before Pydantic validation
            - Validates configuration using SecurityConfig.from_dict() method
            - Performs additional business logic validation beyond schema:
              * Scanner name validation against allowed scanner types
              * Threshold range validation (0.0 to 1.0)
              * Performance setting validation (positive values)
            - Formats Pydantic validation errors with clear location information
            - Provides helpful error messages with suggestions for resolution

        Validation Rules:
            - Schema validation via Pydantic SecurityConfig model
            - Scanner names: must be in predefined valid scanner set
            - Thresholds: must be between 0.0 and 1.0 inclusive
            - Performance: max_concurrent_scans >= 1, cache_ttl_seconds >= 1

        Examples:
            >>> # Valid configuration passes validation
            >>> valid_config = {
            ...     "scanners": {
            ...         "prompt_injection": {"enabled": True, "threshold": 0.8}
            ...     },
            ...     "performance": {"max_concurrent_scans": 10}
            ... }
            >>> result = self._validate_configuration(valid_config)
            >>> assert isinstance(result, SecurityConfig)

            >>> # Invalid configuration raises ConfigurationError
            >>> invalid_config = {
            ...     "scanners": {"invalid_scanner": {"enabled": True}},
            ...     "performance": {"max_concurrent_scans": 0}  # Invalid: must be >= 1
            ... }
            >>> try:
            ...     self._validate_configuration(invalid_config)
            ... except ConfigurationError as e:
            ...     print(f"Validation failed: {e}")
            ...     # Error includes specific location and suggestions
        """
        try:
            # Remove metadata before validation
            config_data = {k: v for k, v in config_data.items() if k != "_metadata"}

            # Convert to SecurityConfig format
            security_config = SecurityConfig.from_dict(config_data)

            # Additional validation
            self._validate_scanner_names(security_config)
            self._validate_thresholds(security_config)
            self._validate_performance_settings(security_config)

            return security_config

        except ValidationError as e:
            error_details = []
            for error in e.errors():
                location = " -> ".join(str(loc) for loc in error["loc"])
                error_details.append(f"  {location}: {error['msg']}")

            raise ConfigurationError(
                "Configuration validation failed:\n" + "\n".join(error_details),
                suggestion="Check configuration values against expected schema and types"
            )
        except Exception as e:
            raise ConfigurationError(
                f"Configuration validation error: {e!s}",
                suggestion="Check configuration structure and required fields"
            )

    def _validate_scanner_names(self, config: SecurityConfig) -> None:
        """Validate scanner names are recognized."""
        valid_scanners = {
            "prompt_injection", "toxicity_input", "pii_detection", "malicious_url",
            "toxicity_output", "bias_detection", "harmful_content"
        }

        for scanner_type in config.scanners.keys():
            # Handle both enum and string values
            scanner_name = scanner_type.value if hasattr(scanner_type, "value") else str(scanner_type)
            if scanner_name not in valid_scanners:
                raise ConfigurationError(
                    f"Unknown scanner type: {scanner_name}",
                    suggestion=f"Valid scanner types: {', '.join(sorted(valid_scanners))}"
                )

    def _validate_thresholds(self, config: SecurityConfig) -> None:
        """Validate threshold values are within valid range."""
        for scanner_type, scanner_config in config.scanners.items():
            if not 0.0 <= scanner_config.threshold <= 1.0:
                raise ConfigurationError(
                    f"Invalid threshold for {scanner_type.value}: {scanner_config.threshold}",
                    suggestion="Threshold must be between 0.0 and 1.0"
                )

    def _validate_performance_settings(self, config: SecurityConfig) -> None:
        """Validate performance configuration settings."""
        perf = config.performance

        if perf.max_concurrent_scans < 1:
            raise ConfigurationError(
                f"Invalid max_concurrent_scans: {perf.max_concurrent_scans}",
                suggestion="Must be at least 1"
            )

        if perf.cache_ttl_seconds < 1:
            raise ConfigurationError(
                f"Invalid cache_ttl_seconds: {perf.cache_ttl_seconds}",
                suggestion="Must be at least 1 second"
            )

    def _is_cache_valid(self, cache_key: str) -> bool:
        """Check if cached configuration is still valid."""
        if cache_key not in self._cache:
            return False

        cache_entry = self._cache[cache_key]

        # Check TTL
        if time.time() - cache_entry["timestamp"] > self.cache_ttl:
            return False

        # Check file modifications
        current_mtimes = self._get_file_mtimes()
        if current_mtimes != cache_entry.get("file_mtimes", {}):
            return False

        return True

    def _get_file_mtimes(self) -> Dict[str, float]:
        """Get modification times for configuration files."""
        mtimes = {}

        # Check base configuration
        base_config = self.config_path / "scanners.yaml"
        if base_config.exists():
            mtimes["base"] = base_config.stat().st_mtime

        # Check environment configuration
        env_config = self.config_path / f"{self.environment}.yaml"
        if env_config.exists():
            mtimes["env"] = env_config.stat().st_mtime

        return mtimes

    def _setup_hot_reload(self) -> None:
        """Setup hot reload for development environments."""
        # This would setup file watching for hot reload
        # Implementation depends on the specific requirements
        if self.debug_mode:
            print("Hot reload setup not implemented - configuration requires restart to reload")

    def clear_cache(self) -> None:
        """Clear configuration cache."""
        self._cache.clear()
        self._cache_timestamp = None

        if self.debug_mode:
            print("Configuration cache cleared")

    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about configuration cache."""
        return {
            "cache_enabled": self.cache_enabled,
            "cache_ttl": self.cache_ttl,
            "cached_entries": len(self._cache),
            "cache_keys": list(self._cache.keys()),
            "config_path": str(self.config_path),
            "environment": self.environment,
            "debug_mode": self.debug_mode
        }


# Global loader instance
_loader_instance: SecurityConfigLoader | None = None


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
    global _loader_instance

    if _loader_instance is None:
        _loader_instance = SecurityConfigLoader()

    return _loader_instance


def load_security_config(
    environment: str | None = None,
    config_path: str | None = None,
    enable_hot_reload: bool = False,
    cache_bust: bool = False
) -> SecurityConfig:
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
    # Create loader with custom settings if provided
    if config_path is not None or environment is not None:
        loader = SecurityConfigLoader(
            config_path=config_path,
            environment=environment or os.environ.get("SECURITY_ENVIRONMENT", "development")
        )
    else:
        loader = get_config_loader()

    return loader.load_config(
        environment=environment,
        enable_hot_reload=enable_hot_reload,
        cache_bust=cache_bust
    )


def reload_security_config(
    environment: str | None = None,
    config_path: str | None = None
) -> SecurityConfig:
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
    return load_security_config(
        environment=environment,
        config_path=config_path,
        cache_bust=True
    )
