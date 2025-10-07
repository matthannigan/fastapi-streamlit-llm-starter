"""
JSON Schema validation for resilience configuration.

This module provides JSON Schema definitions and validation utilities
for custom resilience configuration overrides.
"""

import json
import logging
import time
import threading
from typing import Any, Dict, List
from collections import defaultdict, deque

CONFIGURATION_TEMPLATES = {'fast_development': {'name': 'Fast Development', 'description': 'Optimized for development speed with minimal retries', 'config': {'retry_attempts': 1, 'circuit_breaker_threshold': 2, 'recovery_timeout': 15, 'default_strategy': 'aggressive', 'operation_overrides': {'sentiment': 'aggressive'}}}, 'robust_production': {'name': 'Robust Production', 'description': 'High reliability configuration for production workloads', 'config': {'retry_attempts': 6, 'circuit_breaker_threshold': 12, 'recovery_timeout': 180, 'default_strategy': 'conservative', 'operation_overrides': {'qa': 'critical', 'summarize': 'conservative'}}}, 'low_latency': {'name': 'Low Latency', 'description': 'Minimal latency configuration with fast failures', 'config': {'retry_attempts': 1, 'circuit_breaker_threshold': 2, 'recovery_timeout': 10, 'default_strategy': 'aggressive', 'max_delay_seconds': 5, 'exponential_multiplier': 0.5, 'exponential_min': 0.5, 'exponential_max': 5.0}}, 'high_throughput': {'name': 'High Throughput', 'description': 'Optimized for high throughput with moderate reliability', 'config': {'retry_attempts': 3, 'circuit_breaker_threshold': 8, 'recovery_timeout': 45, 'default_strategy': 'balanced', 'operation_overrides': {'sentiment': 'aggressive', 'key_points': 'balanced'}}}, 'maximum_reliability': {'name': 'Maximum Reliability', 'description': 'Maximum reliability configuration for critical operations', 'config': {'retry_attempts': 8, 'circuit_breaker_threshold': 15, 'recovery_timeout': 300, 'default_strategy': 'critical', 'operation_overrides': {'qa': 'critical', 'summarize': 'critical', 'sentiment': 'conservative', 'key_points': 'conservative', 'questions': 'conservative'}, 'exponential_multiplier': 2.0, 'exponential_min': 3.0, 'exponential_max': 60.0, 'jitter_enabled': True, 'jitter_max': 5.0}}}

SECURITY_CONFIG = {'max_config_size': 4096, 'max_string_length': 200, 'max_array_items': 20, 'max_object_properties': 50, 'max_nesting_depth': 10, 'forbidden_patterns': ['<script', 'javascript:', 'data:', 'vbscript:', 'on\\w+\\s*=', '\\.\\.\\/', '\\\\x[0-9a-fA-F]{2}', '\\\\u[0-9a-fA-F]{4}', '<%.*%>', '\\$\\{.*\\}', 'eval\\s*\\(', 'exec\\s*\\(', 'import\\s+', 'require\\s*\\(', '__.*__'], 'allowed_field_whitelist': {'retry_attempts': {'type': 'int', 'min': 1, 'max': 10}, 'circuit_breaker_threshold': {'type': 'int', 'min': 1, 'max': 20}, 'recovery_timeout': {'type': 'int', 'min': 10, 'max': 300}, 'default_strategy': {'type': 'string', 'enum': ['aggressive', 'balanced', 'conservative', 'critical']}, 'operation_overrides': {'type': 'object', 'max_properties': 10}, 'exponential_multiplier': {'type': 'float', 'min': 0.1, 'max': 5.0}, 'exponential_min': {'type': 'float', 'min': 0.5, 'max': 10.0}, 'exponential_max': {'type': 'float', 'min': 5.0, 'max': 120.0}, 'jitter_enabled': {'type': 'bool'}, 'jitter_max': {'type': 'float', 'min': 0.1, 'max': 10.0}, 'max_delay_seconds': {'type': 'int', 'min': 5, 'max': 600}}, 'rate_limiting': {'max_validations_per_minute': 60, 'max_validations_per_hour': 1000, 'validation_cooldown_seconds': 1}, 'content_filtering': {'max_unicode_codepoint': 128255, 'forbidden_unicode_categories': ['Cc', 'Cf', 'Co', 'Cs'], 'max_repeated_chars': 10}}

RESILIENCE_CONFIG_SCHEMA = {'$schema': 'http://json-schema.org/draft-07/schema#', 'title': 'Resilience Configuration Override', 'description': 'Schema for custom resilience configuration overrides', 'type': 'object', 'properties': {'retry_attempts': {'type': 'integer', 'minimum': 1, 'maximum': 10, 'description': 'Number of retry attempts (1-10)'}, 'circuit_breaker_threshold': {'type': 'integer', 'minimum': 1, 'maximum': 20, 'description': 'Circuit breaker failure threshold (1-20)'}, 'recovery_timeout': {'type': 'integer', 'minimum': 10, 'maximum': 300, 'description': 'Circuit breaker recovery timeout in seconds (10-300)'}, 'default_strategy': {'type': 'string', 'enum': ['aggressive', 'balanced', 'conservative', 'critical'], 'description': 'Default resilience strategy'}, 'operation_overrides': {'type': 'object', 'patternProperties': {'^(summarize|sentiment|key_points|questions|qa)$': {'type': 'string', 'enum': ['aggressive', 'balanced', 'conservative', 'critical'], 'description': 'Strategy override for specific operation'}}, 'additionalProperties': False, 'description': 'Operation-specific strategy overrides'}, 'exponential_multiplier': {'type': 'number', 'minimum': 0.1, 'maximum': 5.0, 'description': 'Exponential backoff multiplier (0.1-5.0)'}, 'exponential_min': {'type': 'number', 'minimum': 0.5, 'maximum': 10.0, 'description': 'Minimum exponential backoff delay in seconds (0.5-10.0)'}, 'exponential_max': {'type': 'number', 'minimum': 5.0, 'maximum': 120.0, 'description': 'Maximum exponential backoff delay in seconds (5.0-120.0)'}, 'jitter_enabled': {'type': 'boolean', 'description': 'Enable jitter in retry delays'}, 'jitter_max': {'type': 'number', 'minimum': 0.1, 'maximum': 10.0, 'description': 'Maximum jitter value in seconds (0.1-10.0)'}, 'max_delay_seconds': {'type': 'integer', 'minimum': 5, 'maximum': 600, 'description': 'Maximum total delay for all retries in seconds (5-600)'}}, 'additionalProperties': False, 'anyOf': [{'required': ['retry_attempts']}, {'required': ['circuit_breaker_threshold']}, {'required': ['recovery_timeout']}, {'required': ['default_strategy']}, {'required': ['operation_overrides']}, {'required': ['exponential_multiplier']}, {'required': ['exponential_min']}, {'required': ['exponential_max']}, {'required': ['jitter_enabled']}, {'required': ['jitter_max']}, {'required': ['max_delay_seconds']}]}

PRESET_SCHEMA = {'$schema': 'http://json-schema.org/draft-07/schema#', 'title': 'Resilience Preset', 'description': 'Schema for resilience preset definitions', 'type': 'object', 'properties': {'name': {'type': 'string', 'minLength': 1, 'maxLength': 50, 'description': 'Preset name'}, 'description': {'type': 'string', 'minLength': 1, 'maxLength': 200, 'description': 'Preset description'}, 'retry_attempts': {'type': 'integer', 'minimum': 1, 'maximum': 10, 'description': 'Number of retry attempts'}, 'circuit_breaker_threshold': {'type': 'integer', 'minimum': 1, 'maximum': 20, 'description': 'Circuit breaker failure threshold'}, 'recovery_timeout': {'type': 'integer', 'minimum': 10, 'maximum': 300, 'description': 'Recovery timeout in seconds'}, 'default_strategy': {'type': 'string', 'enum': ['aggressive', 'balanced', 'conservative', 'critical'], 'description': 'Default resilience strategy'}, 'operation_overrides': {'type': 'object', 'patternProperties': {'^(summarize|sentiment|key_points|questions|qa)$': {'type': 'string', 'enum': ['aggressive', 'balanced', 'conservative', 'critical']}}, 'additionalProperties': False, 'description': 'Operation-specific strategy overrides'}, 'environment_contexts': {'type': 'array', 'items': {'type': 'string', 'enum': ['development', 'testing', 'staging', 'production']}, 'minItems': 1, 'uniqueItems': True, 'description': 'Applicable environment contexts'}}, 'required': ['name', 'description', 'retry_attempts', 'circuit_breaker_threshold', 'recovery_timeout', 'default_strategy', 'operation_overrides', 'environment_contexts'], 'additionalProperties': False}


class ValidationRateLimiter:
    """
    Rate limiter for validation requests to prevent abuse.
    """

    def __init__(self) -> None:
        ...

    def check_rate_limit(self, identifier: str) -> tuple[bool, str]:
        """
        Check if request is within rate limits.
        
        Args:
            identifier: Client identifier (IP address, user ID, etc.)
        
        Returns:
            Tuple of (allowed, error_message)
        """
        ...

    def get_rate_limit_status(self, identifier: str) -> Dict[str, Any]:
        """
        Get current rate limit status for an identifier.
        """
        ...

    def reset(self) -> None:
        """
        Reset all rate limiting state. Used for testing.
        """
        ...


class ValidationResult:
    """
    Result of configuration validation with errors, warnings, and suggestions.
    """

    def __init__(self, is_valid: bool, errors: List[str] | None = None, warnings: List[str] | None = None, suggestions: List[str] | None = None):
        ...

    def __bool__(self) -> bool:
        ...

    def to_dict(self) -> Dict[str, Any]:
        """
        Convert to dictionary for JSON serialization.
        """
        ...


class ResilienceConfigValidator:
    """
    Comprehensive validator for resilience configuration with security checks and JSON Schema validation.
    
    Provides robust validation of custom resilience configurations and preset definitions using
    JSON Schema validation with fallback to basic validation when jsonschema is unavailable.
    Implements security controls including rate limiting, size constraints, forbidden pattern
    detection, and field whitelisting to ensure configuration safety and prevent abuse.
    
    Attributes:
        config_validator: Draft7Validator instance for resilience configuration schema validation
        preset_validator: Draft7Validator instance for preset schema validation
        rate_limiter: ValidationRateLimiter instance for preventing validation abuse
    
    Public Methods:
        validate_custom_config(): Validate custom resilience configuration objects
        validate_preset(): Validate preset configuration objects with environment contexts
        validate_json_string(): Validate JSON string configuration input
        validate_template_based_config(): Validate configuration using templates with overrides
        validate_with_security_checks(): Perform security-only validation without schema checks
        get_configuration_templates(): Retrieve available configuration templates
        suggest_template_for_config(): Recommend appropriate template based on configuration
    
    State Management:
        - Thread-safe validation operations using internal rate limiter with RLock
        - Graceful degradation when jsonschema package unavailable
        - Persistent rate limiting state across validation requests
        - Stateless validation design - no persistent configuration state
    
    Usage:
        # Basic configuration validation
        validator = ResilienceConfigValidator()
        config = {"retry_attempts": 3, "circuit_breaker_threshold": 5}
        result = validator.validate_custom_config(config)
        if result.is_valid:
            print("Configuration is valid")
        else:
            print(f"Errors: {result.errors}")
            print(f"Suggestions: {result.suggestions}")
    
        # Template-based validation with overrides
        result = validator.validate_template_based_config(
            "robust_production",
            overrides={"retry_attempts": 8}
        )
    
        # Security validation with rate limiting
        result = validator.validate_with_security_checks(
            config_data,
            client_identifier="user_123"
        )
    
        # JSON string validation
        json_config = '{"retry_attempts": 3, "circuit_breaker_threshold": 5}'
        result = validator.validate_json_string(json_config)
    """

    def __init__(self) -> None:
        """
        Initialize the resilience configuration validator with schema validators and rate limiting.
        
        Behavior:
            - Attempts to initialize JSON Schema validators for both config and preset schemas
            - Falls back to basic validation when jsonschema package unavailable
            - Creates ValidationRateLimiter instance for abuse prevention
            - Logs initialization status and validation capabilities
            - Maintains thread-safe operation through internal rate limiter
        
        Raises:
            No exceptions raised during initialization - all errors handled gracefully
            with fallback behavior and appropriate logging
        """
        ...

    def get_configuration_templates(self) -> Dict[str, Dict[str, Any]]:
        """
        Retrieve all available configuration templates for resilience configuration.
        
        Returns:
            Dictionary mapping template names to their complete configuration including:
            - name: Human-readable template name
            - description: Detailed description of template purpose and use cases
            - config: Complete resilience configuration with all settings
            Each template is optimized for specific scenarios (development, production, etc.)
        
        Behavior:
            - Returns a deep copy of template configurations to prevent modification
            - Templates include pre-configured settings for common use cases
            - All templates are pre-validated against the resilience configuration schema
            - Templates provide starting points for custom configuration development
        
        Examples:
            >>> validator = ResilienceConfigValidator()
            >>> templates = validator.get_configuration_templates()
            >>> assert len(templates) > 0
            >>> assert "robust_production" in templates
            >>>
            >>> template = templates["fast_development"]
            >>> assert "config" in template
            >>> assert "retry_attempts" in template["config"]
        """
        ...

    def get_template(self, template_name: str) -> Dict[str, Any] | None:
        """
        Retrieve a specific configuration template by name.
        
        Args:
            template_name: Name of the template to retrieve. Valid template names include:
                          "fast_development", "robust_production", "low_latency",
                          "high_throughput", "maximum_reliability"
        
        Returns:
            Complete template configuration dictionary containing name, description,
            and config fields, or None if template name not found
        
        Behavior:
            - Returns template configuration without copying for performance
            - Template configurations are read-only and should not be modified
            - Provides access to pre-validated configuration templates
            - Returns None for unknown template names
        
        Examples:
            >>> validator = ResilienceConfigValidator()
            >>> template = validator.get_template("robust_production")
            >>> assert template is not None
            >>> assert "config" in template
            >>> assert template["config"]["retry_attempts"] == 6
            >>>
            >>> # Unknown template returns None
            >>> unknown = validator.get_template("nonexistent")
            >>> assert unknown is None
        """
        ...

    def check_rate_limit(self, identifier: str) -> ValidationResult:
        """
        Validate request against rate limiting controls to prevent validation abuse.
        
        Args:
            identifier: Client identifier for rate limiting (IP address, user ID, API key, etc.)
                        Must be a unique string per client to ensure accurate rate limiting
        
        Returns:
            ValidationResult with validation status:
            - is_valid: True if request within rate limits, False if rate limited
            - errors: List containing rate limit error messages if exceeded
            - suggestions: List with suggestions for resolving rate limit issues
        
        Behavior:
            - Checks per-minute and per-hour request limits
            - Enforces minimum cooldown period between requests
            - Tracks requests separately per client identifier
            - Returns helpful error messages with remaining wait times
            - Automatically cleans up old request records to prevent memory leaks
        
        Examples:
            >>> validator = ResilienceConfigValidator()
            >>> result = validator.check_rate_limit("client_123")
            >>> assert result.is_valid
            >>>
            >>> # Multiple rapid requests may trigger rate limiting
            >>> for i in range(100):  # This would exceed typical rate limits
            ...     result = validator.check_rate_limit("rapid_client")
            ...     if not result.is_valid:
            ...         assert "Rate limit exceeded" in result.errors[0]
            ...         break
        """
        ...

    def get_rate_limit_info(self, identifier: str) -> Dict[str, Any]:
        """
        Retrieve current rate limiting status and metrics for a specific client identifier.
        
        Args:
            identifier: Client identifier (IP address, user ID, API key) for which
                        to retrieve rate limit information
        
        Returns:
            Dictionary containing current rate limit status:
            - requests_last_minute: Number of requests in the last 60 seconds
            - requests_last_hour: Total requests in the last hour
            - max_per_minute: Maximum allowed requests per minute
            - max_per_hour: Maximum allowed requests per hour
            - cooldown_remaining: Seconds until next request allowed (if rate limited)
        
        Behavior:
            - Returns real-time rate limiting metrics for the specified client
            - Provides visibility into current usage against limits
            - Includes cooldown period if client is currently rate limited
            - Thread-safe access to rate limiting state
            - Used for monitoring and client feedback on rate limiting status
        
        Examples:
            >>> validator = ResilienceConfigValidator()
            >>> info = validator.get_rate_limit_info("client_123")
            >>> assert "requests_last_minute" in info
            >>> assert "max_per_minute" in info
            >>> assert info["requests_last_minute"] <= info["max_per_minute"]
        """
        ...

    def reset_rate_limiter(self) -> None:
        """
        Reset all rate limiting state for testing and maintenance scenarios.
        
        Behavior:
            - Clears all client request history and rate limit state
            - Resets cooldown timers and request counters
            - Intended for testing environments and maintenance operations
            - Thread-safe reset operation using internal locks
            - Affects all client identifiers simultaneously
        
        Examples:
            >>> validator = ResilienceConfigValidator()
            >>> # Simulate some requests that would hit rate limits
            >>> validator.check_rate_limit("test_client")
            >>> # Reset for clean test state
            >>> validator.reset_rate_limiter()
            >>> # Now the client can make requests without rate limiting
        """
        ...

    def validate_with_security_checks(self, config_data: Any, client_identifier: str | None = None) -> ValidationResult:
        """
        Perform security-focused validation of configuration data without schema validation.
        
        Validates configuration against security controls including size limits, forbidden patterns,
        field whitelisting, and content filtering. Does not perform JSON Schema validation for
        field structure or data types, focusing exclusively on security constraints.
        
        Args:
            config_data: Configuration data to validate (typically dict or JSON-serializable object)
            client_identifier: Optional client identifier for rate limiting validation.
                              If provided, method will check rate limits before validation
        
        Returns:
            ValidationResult containing security validation results:
            - is_valid: True if configuration passes all security checks
            - errors: Security violation messages (size limits, forbidden patterns, etc.)
            - warnings: Non-critical security concerns or recommendations
            - suggestions: Specific recommendations for resolving security issues
        
        Behavior:
            - Enforces rate limiting if client identifier provided
            - Validates configuration size against maximum byte limits
            - Scans for forbidden patterns (scripts, injection attacks, etc.)
            - Validates field names and values against security whitelist
            - Checks Unicode content and character encoding issues
            - Validates object structure depth and complexity
            - Detects potential code injection and template vulnerabilities
        
        Raises:
            No exceptions raised - all validation results captured in ValidationResult
        
        Examples:
            >>> validator = ResilienceConfigValidator()
            >>> config = {"retry_attempts": 3, "circuit_breaker_threshold": 5}
            >>> result = validator.validate_with_security_checks(config)
            >>> assert result.is_valid
            >>>
            >>> # With rate limiting
            >>> result = validator.validate_with_security_checks(
            ...     config, client_identifier="user_123"
            ... )
            >>> assert result.is_valid
            >>>
            >>> # Security violation detection
            >>> dangerous_config = {"retry_attempts": "<script>alert('xss')</script>"}
            >>> result = validator.validate_with_security_checks(dangerous_config)
            >>> assert not result.is_valid
            >>> assert "forbidden pattern" in str(result.errors).lower()
        """
        ...

    def validate_template_based_config(self, template_name: str, overrides: Dict[str, Any] | None = None) -> ValidationResult:
        """
        Validate configuration based on a template with optional overrides.
        
        Args:
            template_name: Name of the template to use as base
            overrides: Optional overrides to apply to the template
        
        Returns:
            ValidationResult for the merged configuration
        """
        ...

    def suggest_template_for_config(self, config_data: Dict[str, Any]) -> str | None:
        """
        Suggest the most appropriate template for a given configuration.
        
        Args:
            config_data: Configuration to analyze
        
        Returns:
            Name of the most appropriate template or None
        """
        ...

    def validate_custom_config(self, config_data: Dict[str, Any]) -> ValidationResult:
        """
        Perform comprehensive validation of custom resilience configuration data.
        
        Validates configuration using JSON Schema validation when available, with fallback to
        basic validation when jsonschema package is unavailable. Includes both schema validation
        and logical constraint validation to ensure configuration quality and safety.
        
        Args:
            config_data: Configuration dictionary to validate containing resilience settings
                        such as retry_attempts, circuit_breaker_threshold, etc.
        
        Returns:
            ValidationResult with comprehensive validation results:
            - is_valid: True if configuration passes all validation checks
            - errors: Schema validation errors, logical constraint violations, and security issues
            - warnings: Non-critical issues and best practice recommendations
            - suggestions: Specific guidance for resolving validation problems
        
        Behavior:
            - Uses JSON Schema validation for structural validation when available
            - Falls back to basic type and range validation when jsonschema unavailable
            - Validates logical constraints (e.g., exponential_min < exponential_max)
            - Checks for potentially problematic configurations
            - Generates helpful suggestions based on validation errors
            - Handles validation exceptions gracefully with appropriate error reporting
        
        Examples:
            >>> validator = ResilienceConfigValidator()
            >>> valid_config = {"retry_attempts": 3, "circuit_breaker_threshold": 5}
            >>> result = validator.validate_custom_config(valid_config)
            >>> assert result.is_valid
            >>>
            >>> # Invalid configuration
            >>> invalid_config = {"retry_attempts": -1}
            >>> result = validator.validate_custom_config(invalid_config)
            >>> assert not result.is_valid
            >>> assert any("minimum" in error for error in result.errors)
            >>>
            >>> # Configuration with warnings
            >>> risky_config = {"retry_attempts": 10, "circuit_breaker_threshold": 1}
            >>> result = validator.validate_custom_config(risky_config)
            >>> # May be valid but include warnings about aggressive settings
            >>> assert len(result.warnings) > 0
        """
        ...

    def validate_preset(self, preset_data: Dict[str, Any]) -> ValidationResult:
        """
        Validate preset configuration.
        
        Args:
            preset_data: Preset data to validate
        
        Returns:
            ValidationResult with validation status and any errors
        """
        ...

    def validate_json_string(self, json_string: str) -> ValidationResult:
        """
        Validate JSON string containing custom resilience configuration.
        
        Parses JSON string and performs full validation of the resulting configuration
        using the same validation logic as validate_custom_config(). Provides detailed
        error reporting for both JSON parsing errors and configuration validation issues.
        
        Args:
            json_string: JSON string to parse and validate. Must contain valid JSON
                         representing a resilience configuration dictionary
        
        Returns:
            ValidationResult with parsing and validation results:
            - is_valid: True if JSON parses successfully and configuration is valid
            - errors: JSON parsing errors and/or configuration validation errors
            - warnings: Configuration warnings and best practice recommendations
            - suggestions: Guidance for fixing both JSON and configuration issues
        
        Behavior:
            - Parses JSON string using json.loads() with strict parsing
            - Validates parsed configuration using full validation pipeline
            - Returns detailed JSON parsing errors with line/column information
            - Propagates all configuration validation results to caller
            - Handles JSON parsing exceptions gracefully with helpful error messages
        
        Examples:
            >>> validator = ResilienceConfigValidator()
            >>> valid_json = '{"retry_attempts": 3, "circuit_breaker_threshold": 5}'
            >>> result = validator.validate_json_string(valid_json)
            >>> assert result.is_valid
            >>>
            >>> # Invalid JSON
            >>> invalid_json = '{"retry_attempts": 3, "circuit_breaker_threshold": }'
            >>> result = validator.validate_json_string(invalid_json)
            >>> assert not result.is_valid
            >>> assert "Invalid JSON" in result.errors[0]
            >>>
            >>> # Valid JSON but invalid configuration
            >>> bad_config_json = '{"retry_attempts": -1}'
            >>> result = validator.validate_json_string(bad_config_json)
            >>> assert not result.is_valid
            >>> assert "minimum" in result.errors[0]
        """
        ...
