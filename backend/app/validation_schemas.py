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
    """Result of configuration validation with errors, warnings, and suggestions."""
    
    def __init__(self, is_valid: bool, errors: List[str] = None, warnings: List[str] = None, suggestions: List[str] = None):
        self.is_valid = is_valid
        self.errors = errors or []
        self.warnings = warnings or []
        self.suggestions = suggestions or []
    
    def __bool__(self) -> bool:
        return self.is_valid
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization."""
        return {
            "is_valid": self.is_valid,
            "errors": self.errors,
            "warnings": self.warnings,
            "suggestions": self.suggestions
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
        suggestions = []
        
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
                
                # Add suggestions for common errors
                suggestions.extend(self._generate_error_suggestions(error, error_path))
            
            # Additional logical validations
            logical_errors, logical_warnings, logical_suggestions = self._validate_config_logic(config_data)
            errors.extend(logical_errors)
            warnings.extend(logical_warnings)
            suggestions.extend(logical_suggestions)
            
        except Exception as e:
            logger.error(f"Error during configuration validation: {e}")
            errors.append(f"Validation error: {str(e)}")
        
        return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings, suggestions=suggestions)
    
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
        suggestions = []
        
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
                
                # Add suggestions for common errors
                suggestions.extend(self._generate_error_suggestions(error, error_path))
            
            # Additional logical validations
            logical_errors, logical_warnings, logical_suggestions = self._validate_preset_logic(preset_data)
            errors.extend(logical_errors)
            warnings.extend(logical_warnings)
            suggestions.extend(logical_suggestions)
            
        except Exception as e:
            logger.error(f"Error during preset validation: {e}")
            errors.append(f"Validation error: {str(e)}")
        
        return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings, suggestions=suggestions)
    
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
    
    def _validate_config_logic(self, config_data: Dict[str, Any]) -> tuple[List[str], List[str], List[str]]:
        """Validate configuration logical constraints."""
        errors = []
        warnings = []
        suggestions = []
        
        # Check exponential backoff bounds
        exp_min = config_data.get("exponential_min")
        exp_max = config_data.get("exponential_max")
        if exp_min is not None and exp_max is not None and exp_min >= exp_max:
            errors.append("exponential_min must be less than exponential_max")
            suggestions.append(f"Try setting exponential_min to {exp_max / 2:.1f} and exponential_max to {exp_max * 2:.1f}")
        
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
                suggestions.append(f"Consider increasing max_delay_seconds to at least {estimated_min_delay}s")
        
        # Validate operation overrides
        operation_overrides = config_data.get("operation_overrides", {})
        valid_operations = {"summarize", "sentiment", "key_points", "questions", "qa"}
        for operation in operation_overrides.keys():
            if operation not in valid_operations:
                errors.append(f"Invalid operation '{operation}' in operation_overrides")
                suggestions.append(f"Valid operations are: {', '.join(sorted(valid_operations))}")
        
        # Check for potentially problematic configurations
        circuit_threshold = config_data.get("circuit_breaker_threshold")
        if circuit_threshold is not None and circuit_threshold < 3:
            warnings.append("Very low circuit breaker threshold may cause frequent circuit opening")
            suggestions.append("Consider using threshold >= 3 for better stability")
        
        if retry_attempts is not None and retry_attempts > 7:
            warnings.append("High retry attempts may increase latency significantly")
            suggestions.append("Consider using a preset like 'production' for balanced retry behavior")
        
        return errors, warnings, suggestions
    
    def _validate_preset_logic(self, preset_data: Dict[str, Any]) -> tuple[List[str], List[str], List[str]]:
        """Validate preset logical constraints."""
        errors = []
        warnings = []
        suggestions = []
        
        # Check if retry attempts make sense with circuit breaker threshold
        retry_attempts = preset_data.get("retry_attempts", 0)
        cb_threshold = preset_data.get("circuit_breaker_threshold", 0)
        
        if retry_attempts > cb_threshold:
            warnings.append(
                f"retry_attempts ({retry_attempts}) is greater than "
                f"circuit_breaker_threshold ({cb_threshold}). This may cause "
                f"the circuit breaker to open before retries are exhausted."
            )
            suggestions.append(f"Consider setting circuit_breaker_threshold to at least {retry_attempts + 2}")
        
        # Check environment contexts make sense
        env_contexts = preset_data.get("environment_contexts", [])
        if "production" in env_contexts and preset_data.get("default_strategy") == "aggressive":
            warnings.append(
                "Using 'aggressive' strategy for production environment may impact reliability"
            )
            suggestions.append("Consider using 'balanced' or 'conservative' strategy for production")
        
        # Check for development environments with conservative strategy
        if ("development" in env_contexts and 
            preset_data.get("default_strategy") == "conservative" and
            retry_attempts > 3):
            warnings.append("Conservative strategy with high retry attempts may slow development feedback")
            suggestions.append("Consider using 'development' preset or 'aggressive' strategy for faster feedback")
        
        return errors, warnings, suggestions
    
    def _generate_error_suggestions(self, error, error_path: str) -> List[str]:
        """Generate actionable suggestions based on validation errors."""
        suggestions = []
        
        error_msg = error.message.lower()
        
        # Type validation errors
        if "is not of type" in error_msg:
            if "integer" in error_msg:
                suggestions.append(f"Field '{error_path}' must be a whole number (integer)")
            elif "number" in error_msg:
                suggestions.append(f"Field '{error_path}' must be a number")
            elif "string" in error_msg:
                suggestions.append(f"Field '{error_path}' must be text (string)")
            elif "boolean" in error_msg:
                suggestions.append(f"Field '{error_path}' must be true or false")
        
        # Range validation errors
        elif "is less than the minimum" in error_msg or "is greater than the maximum" in error_msg:
            if "retry_attempts" in error_path:
                suggestions.append("retry_attempts must be between 1 and 10. Try values like 2 (fast), 3 (balanced), or 5 (robust)")
            elif "circuit_breaker_threshold" in error_path:
                suggestions.append("circuit_breaker_threshold must be between 1 and 20. Try values like 3 (sensitive), 5 (balanced), or 10 (tolerant)")
            elif "recovery_timeout" in error_path:
                suggestions.append("recovery_timeout must be between 10 and 300 seconds. Try 30s (fast recovery), 60s (balanced), or 120s (stable)")
        
        # Enum validation errors
        elif "is not one of" in error_msg:
            if "strategy" in error_path:
                suggestions.append("Strategy must be one of: 'aggressive' (fast, less reliable), 'balanced' (moderate), 'conservative' (slow, reliable), 'critical' (maximum reliability)")
            elif "operation" in error_path:
                suggestions.append("Valid operations are: summarize, sentiment, key_points, questions, qa")
        
        # Missing required field errors
        elif "is a required property" in error_msg:
            suggestions.append(f"Add the missing required field '{error_path}' to your configuration")
        
        # Additional properties errors
        elif "additional properties are not allowed" in error_msg:
            suggestions.append("Remove any unknown configuration fields. Check the documentation for valid field names")
        
        return suggestions
    
    def _basic_custom_config_validation(self, config_data: Dict[str, Any]) -> ValidationResult:
        """Basic validation when jsonschema is not available."""
        errors = []
        suggestions = []
        
        # Check types and ranges for key fields
        if "retry_attempts" in config_data:
            val = config_data["retry_attempts"]
            if not isinstance(val, int) or val < 1 or val > 10:
                errors.append("retry_attempts must be an integer between 1 and 10")
                suggestions.append("Try values like 2 (fast), 3 (balanced), or 5 (robust)")
        
        if "circuit_breaker_threshold" in config_data:
            val = config_data["circuit_breaker_threshold"]
            if not isinstance(val, int) or val < 1 or val > 20:
                errors.append("circuit_breaker_threshold must be an integer between 1 and 20")
                suggestions.append("Try values like 3 (sensitive), 5 (balanced), or 10 (tolerant)")
        
        if "recovery_timeout" in config_data:
            val = config_data["recovery_timeout"]
            if not isinstance(val, int) or val < 10 or val > 300:
                errors.append("recovery_timeout must be an integer between 10 and 300")
                suggestions.append("Try 30s (fast recovery), 60s (balanced), or 120s (stable)")
        
        return ValidationResult(is_valid=len(errors) == 0, errors=errors, suggestions=suggestions)
    
    def _basic_preset_validation(self, preset_data: Dict[str, Any]) -> ValidationResult:
        """Basic validation when jsonschema is not available."""
        errors = []
        suggestions = []
        required_fields = ["name", "description", "retry_attempts", "circuit_breaker_threshold", 
                          "recovery_timeout", "default_strategy", "operation_overrides", "environment_contexts"]
        
        for field in required_fields:
            if field not in preset_data:
                errors.append(f"Missing required field: {field}")
        
        if errors:
            suggestions.append("Preset requires all fields: name, description, retry_attempts, circuit_breaker_threshold, recovery_timeout, default_strategy, operation_overrides, environment_contexts")
        
        return ValidationResult(is_valid=len(errors) == 0, errors=errors, suggestions=suggestions)


# Global validator instance
config_validator = ResilienceConfigValidator()