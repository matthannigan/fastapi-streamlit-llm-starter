"""
JSON Schema validation for resilience configuration.

This module provides JSON Schema definitions and validation utilities
for custom resilience configuration overrides.
"""

import json
import logging
import time
import threading
from typing import Any, Dict, List, Optional
from collections import defaultdict, deque

CONFIGURATION_TEMPLATES = {'fast_development': {'name': 'Fast Development', 'description': 'Optimized for development speed with minimal retries', 'config': {'retry_attempts': 1, 'circuit_breaker_threshold': 2, 'recovery_timeout': 15, 'default_strategy': 'aggressive', 'operation_overrides': {'sentiment': 'aggressive'}}}, 'robust_production': {'name': 'Robust Production', 'description': 'High reliability configuration for production workloads', 'config': {'retry_attempts': 6, 'circuit_breaker_threshold': 12, 'recovery_timeout': 180, 'default_strategy': 'conservative', 'operation_overrides': {'qa': 'critical', 'summarize': 'conservative'}}}, 'low_latency': {'name': 'Low Latency', 'description': 'Minimal latency configuration with fast failures', 'config': {'retry_attempts': 1, 'circuit_breaker_threshold': 2, 'recovery_timeout': 10, 'default_strategy': 'aggressive', 'max_delay_seconds': 5, 'exponential_multiplier': 0.5, 'exponential_min': 0.5, 'exponential_max': 5.0}}, 'high_throughput': {'name': 'High Throughput', 'description': 'Optimized for high throughput with moderate reliability', 'config': {'retry_attempts': 3, 'circuit_breaker_threshold': 8, 'recovery_timeout': 45, 'default_strategy': 'balanced', 'operation_overrides': {'sentiment': 'aggressive', 'key_points': 'balanced'}}}, 'maximum_reliability': {'name': 'Maximum Reliability', 'description': 'Maximum reliability configuration for critical operations', 'config': {'retry_attempts': 8, 'circuit_breaker_threshold': 15, 'recovery_timeout': 300, 'default_strategy': 'critical', 'operation_overrides': {'qa': 'critical', 'summarize': 'critical', 'sentiment': 'conservative', 'key_points': 'conservative', 'questions': 'conservative'}, 'exponential_multiplier': 2.0, 'exponential_min': 3.0, 'exponential_max': 60.0, 'jitter_enabled': True, 'jitter_max': 5.0}}}

SECURITY_CONFIG = {'max_config_size': 4096, 'max_string_length': 200, 'max_array_items': 20, 'max_object_properties': 50, 'max_nesting_depth': 10, 'forbidden_patterns': ['<script', 'javascript:', 'data:', 'vbscript:', 'on\\w+\\s*=', '\\.\\.\\/', '\\\\x[0-9a-fA-F]{2}', '\\\\u[0-9a-fA-F]{4}', '<%.*%>', '\\$\\{.*\\}', 'eval\\s*\\(', 'exec\\s*\\(', 'import\\s+', 'require\\s*\\(', '__.*__'], 'allowed_field_whitelist': {'retry_attempts': {'type': 'int', 'min': 1, 'max': 10}, 'circuit_breaker_threshold': {'type': 'int', 'min': 1, 'max': 20}, 'recovery_timeout': {'type': 'int', 'min': 10, 'max': 300}, 'default_strategy': {'type': 'string', 'enum': ['aggressive', 'balanced', 'conservative', 'critical']}, 'operation_overrides': {'type': 'object', 'max_properties': 10}, 'exponential_multiplier': {'type': 'float', 'min': 0.1, 'max': 5.0}, 'exponential_min': {'type': 'float', 'min': 0.5, 'max': 10.0}, 'exponential_max': {'type': 'float', 'min': 5.0, 'max': 120.0}, 'jitter_enabled': {'type': 'bool'}, 'jitter_max': {'type': 'float', 'min': 0.1, 'max': 10.0}, 'max_delay_seconds': {'type': 'int', 'min': 5, 'max': 600}}, 'rate_limiting': {'max_validations_per_minute': 60, 'max_validations_per_hour': 1000, 'validation_cooldown_seconds': 1}, 'content_filtering': {'max_unicode_codepoint': 128255, 'forbidden_unicode_categories': ['Cc', 'Cf', 'Co', 'Cs'], 'max_repeated_chars': 10}}

RESILIENCE_CONFIG_SCHEMA = {'$schema': 'http://json-schema.org/draft-07/schema#', 'title': 'Resilience Configuration Override', 'description': 'Schema for custom resilience configuration overrides', 'type': 'object', 'properties': {'retry_attempts': {'type': 'integer', 'minimum': 1, 'maximum': 10, 'description': 'Number of retry attempts (1-10)'}, 'circuit_breaker_threshold': {'type': 'integer', 'minimum': 1, 'maximum': 20, 'description': 'Circuit breaker failure threshold (1-20)'}, 'recovery_timeout': {'type': 'integer', 'minimum': 10, 'maximum': 300, 'description': 'Circuit breaker recovery timeout in seconds (10-300)'}, 'default_strategy': {'type': 'string', 'enum': ['aggressive', 'balanced', 'conservative', 'critical'], 'description': 'Default resilience strategy'}, 'operation_overrides': {'type': 'object', 'patternProperties': {'^(summarize|sentiment|key_points|questions|qa)$': {'type': 'string', 'enum': ['aggressive', 'balanced', 'conservative', 'critical'], 'description': 'Strategy override for specific operation'}}, 'additionalProperties': False, 'description': 'Operation-specific strategy overrides'}, 'exponential_multiplier': {'type': 'number', 'minimum': 0.1, 'maximum': 5.0, 'description': 'Exponential backoff multiplier (0.1-5.0)'}, 'exponential_min': {'type': 'number', 'minimum': 0.5, 'maximum': 10.0, 'description': 'Minimum exponential backoff delay in seconds (0.5-10.0)'}, 'exponential_max': {'type': 'number', 'minimum': 5.0, 'maximum': 120.0, 'description': 'Maximum exponential backoff delay in seconds (5.0-120.0)'}, 'jitter_enabled': {'type': 'boolean', 'description': 'Enable jitter in retry delays'}, 'jitter_max': {'type': 'number', 'minimum': 0.1, 'maximum': 10.0, 'description': 'Maximum jitter value in seconds (0.1-10.0)'}, 'max_delay_seconds': {'type': 'integer', 'minimum': 5, 'maximum': 600, 'description': 'Maximum total delay for all retries in seconds (5-600)'}}, 'additionalProperties': False, 'anyOf': [{'required': ['retry_attempts']}, {'required': ['circuit_breaker_threshold']}, {'required': ['recovery_timeout']}, {'required': ['default_strategy']}, {'required': ['operation_overrides']}, {'required': ['exponential_multiplier']}, {'required': ['exponential_min']}, {'required': ['exponential_max']}, {'required': ['jitter_enabled']}, {'required': ['jitter_max']}, {'required': ['max_delay_seconds']}]}

PRESET_SCHEMA = {'$schema': 'http://json-schema.org/draft-07/schema#', 'title': 'Resilience Preset', 'description': 'Schema for resilience preset definitions', 'type': 'object', 'properties': {'name': {'type': 'string', 'minLength': 1, 'maxLength': 50, 'description': 'Preset name'}, 'description': {'type': 'string', 'minLength': 1, 'maxLength': 200, 'description': 'Preset description'}, 'retry_attempts': {'type': 'integer', 'minimum': 1, 'maximum': 10, 'description': 'Number of retry attempts'}, 'circuit_breaker_threshold': {'type': 'integer', 'minimum': 1, 'maximum': 20, 'description': 'Circuit breaker failure threshold'}, 'recovery_timeout': {'type': 'integer', 'minimum': 10, 'maximum': 300, 'description': 'Recovery timeout in seconds'}, 'default_strategy': {'type': 'string', 'enum': ['aggressive', 'balanced', 'conservative', 'critical'], 'description': 'Default resilience strategy'}, 'operation_overrides': {'type': 'object', 'patternProperties': {'^(summarize|sentiment|key_points|questions|qa)$': {'type': 'string', 'enum': ['aggressive', 'balanced', 'conservative', 'critical']}}, 'additionalProperties': False, 'description': 'Operation-specific strategy overrides'}, 'environment_contexts': {'type': 'array', 'items': {'type': 'string', 'enum': ['development', 'testing', 'staging', 'production']}, 'minItems': 1, 'uniqueItems': True, 'description': 'Applicable environment contexts'}}, 'required': ['name', 'description', 'retry_attempts', 'circuit_breaker_threshold', 'recovery_timeout', 'default_strategy', 'operation_overrides', 'environment_contexts'], 'additionalProperties': False}


class ValidationRateLimiter:
    """
    Rate limiter for validation requests to prevent abuse.
    """

    def __init__(self):
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

    def reset(self):
        """
        Reset all rate limiting state. Used for testing.
        """
        ...


class ValidationResult:
    """
    Result of configuration validation with errors, warnings, and suggestions.
    """

    def __init__(self, is_valid: bool, errors: Optional[List[str]] = None, warnings: Optional[List[str]] = None, suggestions: Optional[List[str]] = None):
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
    Validator for resilience configuration using JSON Schema.
    """

    def __init__(self):
        """
        Initialize the validator.
        """
        ...

    def get_configuration_templates(self) -> Dict[str, Dict[str, Any]]:
        """
        Get available configuration templates.
        
        Returns:
            Dictionary of template configurations
        """
        ...

    def get_template(self, template_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific configuration template.
        
        Args:
            template_name: Name of the template to retrieve
            
        Returns:
            Template configuration or None if not found
        """
        ...

    def check_rate_limit(self, identifier: str) -> ValidationResult:
        """
        Check rate limit for validation request.
        
        Args:
            identifier: Client identifier (IP, user ID, etc.)
            
        Returns:
            ValidationResult indicating if request is allowed
        """
        ...

    def get_rate_limit_info(self, identifier: str) -> Dict[str, Any]:
        """
        Get rate limit information for identifier.
        """
        ...

    def reset_rate_limiter(self):
        """
        Reset rate limiter state. Used for testing.
        """
        ...

    def validate_with_security_checks(self, config_data: Any, client_identifier: Optional[str] = None) -> ValidationResult:
        """
        Validate configuration with enhanced security checks only.
        
        This method focuses on security validation (size limits, forbidden patterns,
        field whitelisting, etc.) and does not perform full schema validation.
        
        Args:
            config_data: Configuration data to validate
            client_identifier: Optional client identifier for rate limiting
            
        Returns:
            ValidationResult with security validation only
        """
        ...

    def validate_template_based_config(self, template_name: str, overrides: Optional[Dict[str, Any]] = None) -> ValidationResult:
        """
        Validate configuration based on a template with optional overrides.
        
        Args:
            template_name: Name of the template to use as base
            overrides: Optional overrides to apply to the template
            
        Returns:
            ValidationResult for the merged configuration
        """
        ...

    def suggest_template_for_config(self, config_data: Dict[str, Any]) -> Optional[str]:
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
        Validate custom resilience configuration.
        
        Args:
            config_data: Configuration data to validate
            
        Returns:
            ValidationResult with validation status and any errors
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
        Validate JSON string for custom configuration.
        
        Args:
            json_string: JSON string to validate
            
        Returns:
            ValidationResult with validation status and any errors
        """
        ...
