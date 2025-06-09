"""
JSON Schema validation for resilience configuration.

This module provides JSON Schema definitions and validation utilities
for custom resilience configuration overrides.
"""

import json
import logging
from typing import Any, Dict, List, Optional

try:
    import jsonschema
    from jsonschema import ValidationError, Draft7Validator
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False
    ValidationError = Exception
    Draft7Validator = None

logger = logging.getLogger(__name__)

# JSON Schema for resilience custom configuration
RESILIENCE_CONFIG_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Resilience Configuration Override",
    "description": "Schema for custom resilience configuration overrides",
    "type": "object",
    "properties": {
        "retry_attempts": {
            "type": "integer",
            "minimum": 1,
            "maximum": 10,
            "description": "Number of retry attempts (1-10)"
        },
        "circuit_breaker_threshold": {
            "type": "integer", 
            "minimum": 1,
            "maximum": 20,
            "description": "Circuit breaker failure threshold (1-20)"
        },
        "recovery_timeout": {
            "type": "integer",
            "minimum": 10,
            "maximum": 300,
            "description": "Circuit breaker recovery timeout in seconds (10-300)"
        },
        "default_strategy": {
            "type": "string",
            "enum": ["aggressive", "balanced", "conservative", "critical"],
            "description": "Default resilience strategy"
        },
        "operation_overrides": {
            "type": "object",
            "patternProperties": {
                "^(summarize|sentiment|key_points|questions|qa)$": {
                    "type": "string",
                    "enum": ["aggressive", "balanced", "conservative", "critical"],
                    "description": "Strategy override for specific operation"
                }
            },
            "additionalProperties": False,
            "description": "Operation-specific strategy overrides"
        },
        "exponential_multiplier": {
            "type": "number",
            "minimum": 0.1,
            "maximum": 5.0,
            "description": "Exponential backoff multiplier (0.1-5.0)"
        },
        "exponential_min": {
            "type": "number",
            "minimum": 0.5,
            "maximum": 10.0,
            "description": "Minimum exponential backoff delay in seconds (0.5-10.0)"
        },
        "exponential_max": {
            "type": "number",
            "minimum": 5.0,
            "maximum": 120.0,
            "description": "Maximum exponential backoff delay in seconds (5.0-120.0)"
        },
        "jitter_enabled": {
            "type": "boolean",
            "description": "Enable jitter in retry delays"
        },
        "jitter_max": {
            "type": "number",
            "minimum": 0.1,
            "maximum": 10.0,
            "description": "Maximum jitter value in seconds (0.1-10.0)"
        },
        "max_delay_seconds": {
            "type": "integer",
            "minimum": 5,
            "maximum": 600,
            "description": "Maximum total delay for all retries in seconds (5-600)"
        }
    },
    "additionalProperties": False,
    "anyOf": [
        {"required": ["retry_attempts"]},
        {"required": ["circuit_breaker_threshold"]},
        {"required": ["recovery_timeout"]},
        {"required": ["default_strategy"]},
        {"required": ["operation_overrides"]},
        {"required": ["exponential_multiplier"]},
        {"required": ["exponential_min"]},
        {"required": ["exponential_max"]},
        {"required": ["jitter_enabled"]},
        {"required": ["jitter_max"]},
        {"required": ["max_delay_seconds"]}
    ]
}

# Preset validation schema
PRESET_SCHEMA = {
    "$schema": "http://json-schema.org/draft-07/schema#",
    "title": "Resilience Preset",
    "description": "Schema for resilience preset definitions",
    "type": "object",
    "properties": {
        "name": {
            "type": "string",
            "minLength": 1,
            "maxLength": 50,
            "description": "Preset name"
        },
        "description": {
            "type": "string",
            "minLength": 1,
            "maxLength": 200,
            "description": "Preset description"
        },
        "retry_attempts": {
            "type": "integer",
            "minimum": 1,
            "maximum": 10,
            "description": "Number of retry attempts"
        },
        "circuit_breaker_threshold": {
            "type": "integer",
            "minimum": 1,
            "maximum": 20,
            "description": "Circuit breaker failure threshold"
        },
        "recovery_timeout": {
            "type": "integer",
            "minimum": 10,
            "maximum": 300,
            "description": "Recovery timeout in seconds"
        },
        "default_strategy": {
            "type": "string",
            "enum": ["aggressive", "balanced", "conservative", "critical"],
            "description": "Default resilience strategy"
        },
        "operation_overrides": {
            "type": "object",
            "patternProperties": {
                "^(summarize|sentiment|key_points|questions|qa)$": {
                    "type": "string",
                    "enum": ["aggressive", "balanced", "conservative", "critical"]
                }
            },
            "additionalProperties": False,
            "description": "Operation-specific strategy overrides"
        },
        "environment_contexts": {
            "type": "array",
            "items": {
                "type": "string",
                "enum": ["development", "testing", "staging", "production"]
            },
            "minItems": 1,
            "uniqueItems": True,
            "description": "Applicable environment contexts"
        }
    },
    "required": [
        "name", "description", "retry_attempts", "circuit_breaker_threshold",
        "recovery_timeout", "default_strategy", "operation_overrides", "environment_contexts"
    ],
    "additionalProperties": False
}


class ValidationResult:
    """Result of configuration validation."""
    
    def __init__(self, is_valid: bool, errors: List[str] = None, warnings: List[str] = None):
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []
    
    def __bool__(self) -> bool:
        return self.is_valid
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings
        }


class ResilienceConfigValidator:
    """Validator for resilience configuration using JSON Schema."""
    
    def __init__(self):
        """Initialize the validator."""
        self.config_validator = None
        self.preset_validator = None
        
        if JSONSCHEMA_AVAILABLE:
            self.config_validator = Draft7Validator(RESILIENCE_CONFIG_SCHEMA)
            self.preset_validator = Draft7Validator(PRESET_SCHEMA)
            logger.info("JSON Schema validation enabled")
        else:
            logger.warning("jsonschema package not available - validation will be basic")
    
    def validate_custom_config(self, config_data: Dict[str, Any]) -> ValidationResult:
        """
        Validate custom resilience configuration.
        
        Args:
            config_data: Configuration data to validate
            
        Returns:
            ValidationResult with validation status and any errors
        """
        if not JSONSCHEMA_AVAILABLE:
            return self._basic_custom_config_validation(config_data)
        
        errors = []
        warnings = []
        
        try:
            # JSON Schema validation
            schema_errors = list(self.config_validator.iter_errors(config_data))
            for error in schema_errors:
                error_path = ".".join(str(p) for p in error.absolute_path)
                if error_path:
                    error_msg = f"Field '{error_path}': {error.message}"
                else:
                    error_msg = error.message
                errors.append(error_msg)
            
            # Additional logical validations
            logical_errors, logical_warnings = self._validate_config_logic(config_data)
            errors.extend(logical_errors)
            warnings.extend(logical_warnings)
            
        except Exception as e:
            logger.error(f"Error during configuration validation: {e}")
            errors.append(f"Validation error: {str(e)}")
        
        return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)
    
    def validate_preset(self, preset_data: Dict[str, Any]) -> ValidationResult:
        """
        Validate preset configuration.
        
        Args:
            preset_data: Preset data to validate
            
        Returns:
            ValidationResult with validation status and any errors
        """
        if not JSONSCHEMA_AVAILABLE:
            return self._basic_preset_validation(preset_data)
        
        errors = []
        warnings = []
        
        try:
            # JSON Schema validation
            schema_errors = list(self.preset_validator.iter_errors(preset_data))
            for error in schema_errors:
                error_path = ".".join(str(p) for p in error.absolute_path)
                if error_path:
                    error_msg = f"Field '{error_path}': {error.message}"
                else:
                    error_msg = error.message
                errors.append(error_msg)
            
            # Additional logical validations
            logical_errors, logical_warnings = self._validate_preset_logic(preset_data)
            errors.extend(logical_errors)
            warnings.extend(logical_warnings)
            
        except Exception as e:
            logger.error(f"Error during preset validation: {e}")
            errors.append(f"Validation error: {str(e)}")
        
        return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)
    
    def validate_json_string(self, json_string: str) -> ValidationResult:
        """
        Validate JSON string for custom configuration.
        
        Args:
            json_string: JSON string to validate
            
        Returns:
            ValidationResult with validation status and any errors
        """
        try:
            config_data = json.loads(json_string)
            return self.validate_custom_config(config_data)
        except json.JSONDecodeError as e:
            return ValidationResult(
                is_valid=False,
                errors=[f"Invalid JSON: {str(e)}"]
            )
    
    def _validate_config_logic(self, config_data: Dict[str, Any]) -> tuple[List[str], List[str]]:
        """Validate configuration logical constraints."""
        errors = []
        warnings = []
        
        # Check exponential backoff bounds
        exp_min = config_data.get("exponential_min")
        exp_max = config_data.get("exponential_max")
        if exp_min is not None and exp_max is not None and exp_min >= exp_max:
            errors.append("exponential_min must be less than exponential_max")
        
        # Check retry attempts vs max delay
        retry_attempts = config_data.get("retry_attempts")
        max_delay = config_data.get("max_delay_seconds")
        if retry_attempts is not None and max_delay is not None:
            # Warn if max delay might be too short for retry attempts
            estimated_min_delay = retry_attempts * 2  # Conservative estimate
            if max_delay < estimated_min_delay:
                warnings.append(
                    f"max_delay_seconds ({max_delay}s) might be too short for "
                    f"{retry_attempts} retry attempts (estimated minimum: {estimated_min_delay}s)"
                )
        
        # Validate operation overrides
        operation_overrides = config_data.get("operation_overrides", {})
        valid_operations = {"summarize", "sentiment", "key_points", "questions", "qa"}
        for operation in operation_overrides.keys():
            if operation not in valid_operations:
                errors.append(f"Invalid operation '{operation}' in operation_overrides")
        
        return errors, warnings
    
    def _validate_preset_logic(self, preset_data: Dict[str, Any]) -> tuple[List[str], List[str]]:
        """Validate preset logical constraints."""
        errors = []
        warnings = []
        
        # Check if retry attempts make sense with circuit breaker threshold
        retry_attempts = preset_data.get("retry_attempts", 0)
        cb_threshold = preset_data.get("circuit_breaker_threshold", 0)
        
        if retry_attempts > cb_threshold:
            warnings.append(
                f"retry_attempts ({retry_attempts}) is greater than "
                f"circuit_breaker_threshold ({cb_threshold}). This may cause "
                f"the circuit breaker to open before retries are exhausted."
            )
        
        # Check environment contexts make sense
        env_contexts = preset_data.get("environment_contexts", [])
        if "production" in env_contexts and preset_data.get("default_strategy") == "aggressive":
            warnings.append(
                "Using 'aggressive' strategy for production environment may impact reliability"
            )
        
        return errors, warnings
    
    def _basic_custom_config_validation(self, config_data: Dict[str, Any]) -> ValidationResult:
        """Basic validation when jsonschema is not available."""
        errors = []
        
        # Check types and ranges for key fields
        if "retry_attempts" in config_data:
            val = config_data["retry_attempts"]
            if not isinstance(val, int) or val < 1 or val > 10:
                errors.append("retry_attempts must be an integer between 1 and 10")
        
        if "circuit_breaker_threshold" in config_data:
            val = config_data["circuit_breaker_threshold"]
            if not isinstance(val, int) or val < 1 or val > 20:
                errors.append("circuit_breaker_threshold must be an integer between 1 and 20")
        
        if "recovery_timeout" in config_data:
            val = config_data["recovery_timeout"]
            if not isinstance(val, int) or val < 10 or val > 300:
                errors.append("recovery_timeout must be an integer between 10 and 300")
        
        return ValidationResult(is_valid=len(errors) == 0, errors=errors)
    
    def _basic_preset_validation(self, preset_data: Dict[str, Any]) -> ValidationResult:
        """Basic validation when jsonschema is not available."""
        errors = []
        required_fields = ["name", "description", "retry_attempts", "circuit_breaker_threshold", 
                          "recovery_timeout", "default_strategy", "operation_overrides", "environment_contexts"]
        
        for field in required_fields:
            if field not in preset_data:
                errors.append(f"Missing required field: {field}")
        
        return ValidationResult(is_valid=len(errors) == 0, errors=errors)


# Global validator instance
config_validator = ResilienceConfigValidator()