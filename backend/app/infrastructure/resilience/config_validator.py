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

try:
    import jsonschema
    from jsonschema import ValidationError, Draft7Validator
    JSONSCHEMA_AVAILABLE = True
except ImportError:
    JSONSCHEMA_AVAILABLE = False
    ValidationError = Exception
    Draft7Validator = None

logger = logging.getLogger(__name__)

# Configuration templates for common use cases
CONFIGURATION_TEMPLATES = {
    "fast_development": {
        "name": "Fast Development",
        "description": "Optimized for development speed with minimal retries",
        "config": {
            "retry_attempts": 1,
            "circuit_breaker_threshold": 2,
            "recovery_timeout": 15,
            "default_strategy": "aggressive",
            "operation_overrides": {
                "sentiment": "aggressive"
            }
        }
    },
    "robust_production": {
        "name": "Robust Production",
        "description": "High reliability configuration for production workloads",
        "config": {
            "retry_attempts": 6,
            "circuit_breaker_threshold": 12,
            "recovery_timeout": 180,
            "default_strategy": "conservative",
            "operation_overrides": {
                "qa": "critical",
                "summarize": "conservative"
            }
        }
    },
    "low_latency": {
        "name": "Low Latency",
        "description": "Minimal latency configuration with fast failures",
        "config": {
            "retry_attempts": 1,
            "circuit_breaker_threshold": 2,
            "recovery_timeout": 10,
            "default_strategy": "aggressive",
            "max_delay_seconds": 5,
            "exponential_multiplier": 0.5,
            "exponential_min": 0.5,
            "exponential_max": 5.0
        }
    },
    "high_throughput": {
        "name": "High Throughput",
        "description": "Optimized for high throughput with moderate reliability",
        "config": {
            "retry_attempts": 3,
            "circuit_breaker_threshold": 8,
            "recovery_timeout": 45,
            "default_strategy": "balanced",
            "operation_overrides": {
                "sentiment": "aggressive",
                "key_points": "balanced"
            }
        }
    },
    "maximum_reliability": {
        "name": "Maximum Reliability",
        "description": "Maximum reliability configuration for critical operations",
        "config": {
            "retry_attempts": 8,
            "circuit_breaker_threshold": 15,
            "recovery_timeout": 300,
            "default_strategy": "critical",
            "operation_overrides": {
                "qa": "critical",
                "summarize": "critical",
                "sentiment": "conservative",
                "key_points": "conservative",
                "questions": "conservative"
            },
            "exponential_multiplier": 2.0,
            "exponential_min": 3.0,
            "exponential_max": 60.0,
            "jitter_enabled": True,
            "jitter_max": 5.0
        }
    }
}

# Security configuration
SECURITY_CONFIG = {
    "max_config_size": 4096,  # 4KB limit
    "max_string_length": 200,
    "max_array_items": 20,
    "max_object_properties": 50,
    "max_nesting_depth": 10,  # Maximum object/array nesting depth
    "forbidden_patterns": [
        r"<script",
        r"javascript:",
        r"data:",
        r"vbscript:",
        r"on\w+\s*=",  # Event handlers
        r"\.\.\/",  # Path traversal
        r"\\x[0-9a-fA-F]{2}",  # Hex encoded characters
        r"\\u[0-9a-fA-F]{4}",  # Unicode encoded characters
        r"<%.*%>",  # Template tags
        r"\$\{.*\}",  # Variable interpolation
        r"eval\s*\(",  # Eval functions
        r"exec\s*\(",  # Exec functions
        r"import\s+",  # Import statements
        r"require\s*\(",  # Require statements
        r"__.*__",  # Python dunder methods
    ],
    "allowed_field_whitelist": {
        # Configuration field whitelist with allowed value types and ranges
        "retry_attempts": {"type": "int", "min": 1, "max": 10},
        "circuit_breaker_threshold": {"type": "int", "min": 1, "max": 20},
        "recovery_timeout": {"type": "int", "min": 10, "max": 300},
        "default_strategy": {"type": "string", "enum": ["aggressive", "balanced", "conservative", "critical"]},
        "operation_overrides": {"type": "object", "max_properties": 10},
        "exponential_multiplier": {"type": "float", "min": 0.1, "max": 5.0},
        "exponential_min": {"type": "float", "min": 0.5, "max": 10.0},
        "exponential_max": {"type": "float", "min": 5.0, "max": 120.0},
        "jitter_enabled": {"type": "bool"},
        "jitter_max": {"type": "float", "min": 0.1, "max": 10.0},
        "max_delay_seconds": {"type": "int", "min": 5, "max": 600},
    },
    "rate_limiting": {
        "max_validations_per_minute": 60,  # Rate limit for validation requests
        "max_validations_per_hour": 1000,
        "validation_cooldown_seconds": 1,  # Minimum time between validations
    },
    "content_filtering": {
        "max_unicode_codepoint": 0x1F4FF,  # Block high Unicode ranges
        "forbidden_unicode_categories": ["Cc", "Cf", "Co", "Cs"],  # Control chars, format chars, etc.
        "max_repeated_chars": 10,  # Maximum consecutive identical characters
    }
}

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


class ValidationRateLimiter:
    """Rate limiter for validation requests to prevent abuse."""
    
    def __init__(self):
        self._requests = defaultdict(deque)  # IP/user -> request timestamps
        self._last_validation = {}  # IP/user -> last validation timestamp
        self._lock = threading.RLock()
    
    def check_rate_limit(self, identifier: str) -> tuple[bool, str]:
        """
        Check if request is within rate limits.
        
        Args:
            identifier: Client identifier (IP address, user ID, etc.)
            
        Returns:
            Tuple of (allowed, error_message)
        """
        with self._lock:
            current_time = time.time()
            rate_config = SECURITY_CONFIG["rate_limiting"]
            
            # Check cooldown period
            last_validation = self._last_validation.get(identifier, 0)
            cooldown = rate_config["validation_cooldown_seconds"]
            if current_time - last_validation < cooldown:
                return False, f"Rate limit: wait {cooldown - (current_time - last_validation):.1f}s before next validation"
            
            # Clean old requests (older than 1 hour)
            request_times = self._requests[identifier]
            cutoff_time = current_time - 3600  # 1 hour
            while request_times and request_times[0] < cutoff_time:
                request_times.popleft()
            
            # Check per-minute limit
            minute_cutoff = current_time - 60
            minute_requests = sum(1 for t in request_times if t > minute_cutoff)
            if minute_requests >= rate_config["max_validations_per_minute"]:
                return False, f"Rate limit exceeded: {minute_requests}/{rate_config['max_validations_per_minute']} validations per minute"
            
            # Check per-hour limit
            if len(request_times) >= rate_config["max_validations_per_hour"]:
                return False, f"Rate limit exceeded: {len(request_times)}/{rate_config['max_validations_per_hour']} validations per hour"
            
            # Record this request
            request_times.append(current_time)
            self._last_validation[identifier] = current_time
            
            return True, ""
    
    def get_rate_limit_status(self, identifier: str) -> Dict[str, Any]:
        """Get current rate limit status for an identifier."""
        with self._lock:
            current_time = time.time()
            request_times = self._requests[identifier]
            
            # Count recent requests
            minute_cutoff = current_time - 60
            minute_requests = sum(1 for t in request_times if t > minute_cutoff)
            
            return {
                "requests_last_minute": minute_requests,
                "requests_last_hour": len(request_times),
                "max_per_minute": SECURITY_CONFIG["rate_limiting"]["max_validations_per_minute"],
                "max_per_hour": SECURITY_CONFIG["rate_limiting"]["max_validations_per_hour"],
                "cooldown_remaining": max(0, SECURITY_CONFIG["rate_limiting"]["validation_cooldown_seconds"] - 
                                        (current_time - self._last_validation.get(identifier, 0)))
            }
    
    def reset(self):
        """Reset all rate limiting state. Used for testing."""
        with self._lock:
            self._requests.clear()
            self._last_validation.clear()


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
        self.rate_limiter = ValidationRateLimiter()
        
        if JSONSCHEMA_AVAILABLE:
            self.config_validator = Draft7Validator(RESILIENCE_CONFIG_SCHEMA)
            self.preset_validator = Draft7Validator(PRESET_SCHEMA)
            logger.info("JSON Schema validation enabled")
        else:
            logger.warning("jsonschema package not available - validation will be basic")
    
    def get_configuration_templates(self) -> Dict[str, Dict[str, Any]]:
        """
        Get available configuration templates.
        
        Returns:
            Dictionary of template configurations
        """
        return CONFIGURATION_TEMPLATES.copy()
    
    def get_template(self, template_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a specific configuration template.
        
        Args:
            template_name: Name of the template to retrieve
            
        Returns:
            Template configuration or None if not found
        """
        return CONFIGURATION_TEMPLATES.get(template_name)
    
    def check_rate_limit(self, identifier: str) -> ValidationResult:
        """
        Check rate limit for validation request.
        
        Args:
            identifier: Client identifier (IP, user ID, etc.)
            
        Returns:
            ValidationResult indicating if request is allowed
        """
        allowed, error_msg = self.rate_limiter.check_rate_limit(identifier)
        if not allowed:
            return ValidationResult(
                is_valid=False,
                errors=[f"Rate limit exceeded: {error_msg}"],
                suggestions=["Wait before making another validation request", "Consider batching multiple validations"]
            )
        return ValidationResult(is_valid=True)
    
    def get_rate_limit_info(self, identifier: str) -> Dict[str, Any]:
        """Get rate limit information for identifier."""
        return self.rate_limiter.get_rate_limit_status(identifier)
    
    def reset_rate_limiter(self):
        """Reset rate limiter state. Used for testing."""
        self.rate_limiter.reset()
    
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
        # Check rate limits if identifier provided
        if client_identifier:
            rate_limit_result = self.check_rate_limit(client_identifier)
            if not rate_limit_result.is_valid:
                return rate_limit_result
        
        # Perform security validation only
        if config_data is None:
            return ValidationResult(
                is_valid=False,
                errors=["Configuration must be a JSON object"],
                suggestions=["Ensure your configuration is a valid JSON object with key-value pairs"]
            )
        
        if not isinstance(config_data, dict):
            return ValidationResult(
                is_valid=False,
                errors=["Configuration must be a JSON object"],
                suggestions=["Ensure your configuration is a valid JSON object with key-value pairs"]
            )
        
        # Perform security validation
        return self._validate_security(config_data)
    
    def _validate_security(self, config_data: Any) -> ValidationResult:
        """
        Perform comprehensive security validation on configuration data.
        
        Args:
            config_data: Configuration data to validate
            
        Returns:
            ValidationResult with security validation results
        """
        import re
        import unicodedata
        
        errors = []
        warnings = []
        suggestions = []
        
        try:
            # Convert to JSON string to check size
            json_str = json.dumps(config_data)
            
            # Check size limits
            if len(json_str) > SECURITY_CONFIG["max_config_size"]:
                errors.append(f"Configuration too large: {len(json_str)} bytes (max: {SECURITY_CONFIG['max_config_size']} bytes)")
                suggestions.append("Reduce configuration size by removing unnecessary fields or simplifying values")
            
            # Check for forbidden patterns in JSON string
            for pattern in SECURITY_CONFIG["forbidden_patterns"]:
                if re.search(pattern, json_str, re.IGNORECASE):
                    errors.append(f"Configuration contains forbidden pattern matching: {pattern}")
                    suggestions.append("Remove any HTML, JavaScript, template syntax, or potentially dangerous content from configuration")
            
            # Content filtering validation
            content_errors, content_warnings = self._validate_content_filtering(json_str)
            errors.extend(content_errors)
            warnings.extend(content_warnings)
            
            # Field whitelist validation
            whitelist_errors, whitelist_suggestions = self._validate_field_whitelist(config_data)
            errors.extend(whitelist_errors)
            suggestions.extend(whitelist_suggestions)
            
            # Recursive validation of structure
            self._validate_security_recursive(config_data, "", errors, warnings, suggestions, depth=0)
            
        except Exception as e:
            errors.append(f"Security validation error: {str(e)}")
            suggestions.append("Ensure configuration contains only valid JSON with allowed field types")
        
        return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings, suggestions=suggestions)
    
    def _validate_security_recursive(self, obj: Any, path: str, errors: List[str], warnings: List[str], suggestions: List[str], depth: int = 0):
        """Recursively validate object structure for security issues."""
        # Check nesting depth
        if depth > SECURITY_CONFIG["max_nesting_depth"]:
            errors.append(f"Nesting too deep at '{path}': depth {depth} (max: {SECURITY_CONFIG['max_nesting_depth']})")
            suggestions.append(f"Reduce nesting depth by flattening the structure at '{path}'")
            return  # Stop recursing to prevent stack overflow
        
        if isinstance(obj, dict):
            if len(obj) > SECURITY_CONFIG["max_object_properties"]:
                errors.append(f"Too many properties in object at '{path}': {len(obj)} (max: {SECURITY_CONFIG['max_object_properties']})")
                suggestions.append(f"Reduce the number of properties in the object at '{path}'")
            
            for key, value in obj.items():
                # Validate key names
                if not isinstance(key, str):
                    errors.append(f"Non-string key at '{path}': {type(key).__name__}")
                    suggestions.append("All object keys must be strings")
                    continue
                
                if len(key) > SECURITY_CONFIG["max_string_length"]:
                    errors.append(f"Key name too long at '{path}': '{key}' ({len(key)} characters)")
                    suggestions.append(f"Key names must be {SECURITY_CONFIG['max_string_length']} characters or less")
                
                new_path = f"{path}.{key}" if path else key
                self._validate_security_recursive(value, new_path, errors, warnings, suggestions, depth + 1)
        
        elif isinstance(obj, list):
            if len(obj) > SECURITY_CONFIG["max_array_items"]:
                errors.append(f"Too many items in array at '{path}': {len(obj)} (max: {SECURITY_CONFIG['max_array_items']})")
                suggestions.append(f"Reduce the number of items in the array at '{path}'")
            
            for i, item in enumerate(obj):
                new_path = f"{path}[{i}]"
                self._validate_security_recursive(item, new_path, errors, warnings, suggestions, depth + 1)
        
        elif isinstance(obj, str):
            if len(obj) > SECURITY_CONFIG["max_string_length"]:
                errors.append(f"String too long at '{path}': {len(obj)} characters (max: {SECURITY_CONFIG['max_string_length']})")
                suggestions.append(f"Shorten the text at '{path}' to {SECURITY_CONFIG['max_string_length']} characters or less")
            
            # Check for repeated characters
            self._check_repeated_chars(obj, path, warnings, suggestions)
        
        elif isinstance(obj, (int, float)):
            # Check for extremely large numbers that might cause issues
            if isinstance(obj, int) and abs(obj) > 2**53:
                warnings.append(f"Very large integer at '{path}': {obj}")
                suggestions.append("Consider using smaller integer values to avoid precision issues")
            elif isinstance(obj, float) and (abs(obj) > 1e100 or (obj != 0 and abs(obj) < 1e-100)):
                warnings.append(f"Extreme float value at '{path}': {obj}")
                suggestions.append("Consider using more reasonable floating-point values")
    
    def _validate_content_filtering(self, content: str) -> tuple[List[str], List[str]]:
        """
        Validate content for forbidden Unicode characters and patterns.
        
        Args:
            content: String content to validate
            
        Returns:
            Tuple of (errors, warnings)
        """
        import unicodedata
        import re
        
        errors = []
        warnings = []
        
        # Check Unicode codepoints
        for char in content:
            codepoint = ord(char)
            if codepoint > SECURITY_CONFIG["content_filtering"]["max_unicode_codepoint"]:
                errors.append(f"High Unicode codepoint detected: U+{codepoint:04X} ('{char}')")
                continue
            
            # Check Unicode categories
            category = unicodedata.category(char)
            if category in SECURITY_CONFIG["content_filtering"]["forbidden_unicode_categories"]:
                errors.append(f"Forbidden Unicode character category '{category}': U+{codepoint:04X}")
        
        return errors, warnings
    
    def _validate_field_whitelist(self, config_data: Dict[str, Any]) -> tuple[List[str], List[str]]:
        """
        Validate configuration fields against whitelist.
        
        Args:
            config_data: Configuration dictionary to validate
            
        Returns:
            Tuple of (errors, suggestions)
        """
        errors = []
        suggestions = []
        whitelist = SECURITY_CONFIG["allowed_field_whitelist"]
        
        for field_name, field_value in config_data.items():
            if field_name not in whitelist:
                errors.append(f"Field '{field_name}' not in allowed whitelist")
                suggestions.append(f"Allowed fields: {', '.join(sorted(whitelist.keys()))}")
                continue
            
            field_spec = whitelist[field_name]
            
            # Type validation
            expected_type = field_spec["type"]
            if expected_type == "int" and not isinstance(field_value, int):
                errors.append(f"Field '{field_name}' must be an integer, got {type(field_value).__name__}")
            elif expected_type == "float" and not isinstance(field_value, (int, float)):
                errors.append(f"Field '{field_name}' must be a number, got {type(field_value).__name__}")
            elif expected_type == "string" and not isinstance(field_value, str):
                errors.append(f"Field '{field_name}' must be a string, got {type(field_value).__name__}")
            elif expected_type == "bool" and not isinstance(field_value, bool):
                errors.append(f"Field '{field_name}' must be a boolean, got {type(field_value).__name__}")
            elif expected_type == "object" and not isinstance(field_value, dict):
                errors.append(f"Field '{field_name}' must be an object, got {type(field_value).__name__}")
            
            # Range validation for numeric types
            if expected_type in ["int", "float"] and isinstance(field_value, (int, float)):
                if "min" in field_spec and field_value < field_spec["min"]:
                    errors.append(f"Field '{field_name}' value {field_value} below minimum {field_spec['min']}")
                if "max" in field_spec and field_value > field_spec["max"]:
                    errors.append(f"Field '{field_name}' value {field_value} above maximum {field_spec['max']}")
            
            # Enum validation
            if "enum" in field_spec and field_value not in field_spec["enum"]:
                errors.append(f"Field '{field_name}' value '{field_value}' not in allowed values: {field_spec['enum']}")
            
            # Object property count validation
            if expected_type == "object" and isinstance(field_value, dict):
                max_props = field_spec.get("max_properties", 50)
                if len(field_value) > max_props:
                    errors.append(f"Field '{field_name}' has too many properties: {len(field_value)} (max: {max_props})")
        
        return errors, suggestions
    
    def _check_repeated_chars(self, text: str, path: str, warnings: List[str], suggestions: List[str]):
        """Check for excessive repeated characters in text."""
        max_repeated = SECURITY_CONFIG["content_filtering"]["max_repeated_chars"]
        
        i = 0
        while i < len(text):
            char = text[i]
            count = 1
            while i + count < len(text) and text[i + count] == char:
                count += 1
            
            if count > max_repeated:
                warnings.append(f"Excessive repeated characters at '{path}': '{char}' repeated {count} times")
                suggestions.append(f"Limit repeated characters to {max_repeated} or fewer")
                break
            
            i += count
    
    def validate_template_based_config(self, template_name: str, overrides: Dict[str, Any] = None) -> ValidationResult:
        """
        Validate configuration based on a template with optional overrides.
        
        Args:
            template_name: Name of the template to use as base
            overrides: Optional overrides to apply to the template
            
        Returns:
            ValidationResult for the merged configuration
        """
        template = self.get_template(template_name)
        if not template:
            return ValidationResult(
                is_valid=False,
                errors=[f"Unknown template: {template_name}"],
                suggestions=[f"Available templates: {', '.join(CONFIGURATION_TEMPLATES.keys())}"]
            )
        
        # Start with template config
        config = template["config"].copy()
        
        # Apply overrides if provided
        if overrides:
            config.update(overrides)
        
        # Validate the merged configuration
        return self.validate_with_security_checks(config)
    
    def suggest_template_for_config(self, config_data: Dict[str, Any]) -> Optional[str]:
        """
        Suggest the most appropriate template for a given configuration.
        
        Args:
            config_data: Configuration to analyze
            
        Returns:
            Name of the most appropriate template or None
        """
        retry_attempts = config_data.get("retry_attempts", 3)
        circuit_threshold = config_data.get("circuit_breaker_threshold", 5)
        strategy = config_data.get("default_strategy", "balanced")
        
        # Score each template based on similarity
        scores = {}
        
        for template_name, template_info in CONFIGURATION_TEMPLATES.items():
            template_config = template_info["config"]
            score = 0
            
            # Score based on retry attempts
            template_retries = template_config.get("retry_attempts", 3)
            if abs(retry_attempts - template_retries) <= 1:
                score += 3
            elif abs(retry_attempts - template_retries) <= 2:
                score += 1
            
            # Score based on circuit breaker threshold
            template_threshold = template_config.get("circuit_breaker_threshold", 5)
            if abs(circuit_threshold - template_threshold) <= 2:
                score += 2
            elif abs(circuit_threshold - template_threshold) <= 5:
                score += 1
            
            # Score based on strategy
            template_strategy = template_config.get("default_strategy", "balanced")
            if strategy == template_strategy:
                score += 3
            
            scores[template_name] = score
        
        # Return template with highest score (minimum threshold of 4)
        best_template = max(scores.items(), key=lambda x: x[1])
        return best_template[0] if best_template[1] >= 4 else None
    
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
        """
        Generate helpful suggestions based on validation errors.
        
        Args:
            error: JSON Schema validation error
            error_path: Path to the field that caused the error
            
        Returns:
            List of suggestion strings
        """
        suggestions = []
        
        try:
            error_message = error.message.lower()
            schema_context = error.schema
            
            # Suggestions for common field errors
            if "retry_attempts" in error_path:
                if "minimum" in error_message or "maximum" in error_message:
                    suggestions.append("💡 Try: retry_attempts: 3 (recommended for most use cases)")
                    suggestions.append("🔧 Valid range: 1 (fast failure) to 10 (maximum persistence)")
                elif "type" in error_message:
                    suggestions.append("💡 retry_attempts must be a whole number, like: retry_attempts: 5")
            
            elif "circuit_breaker_threshold" in error_path:
                if "minimum" in error_message or "maximum" in error_message:
                    suggestions.append("💡 Try: circuit_breaker_threshold: 5 (good balance)")
                    suggestions.append("🔧 Valid range: 1 (very sensitive) to 20 (very tolerant)")
                elif "type" in error_message:
                    suggestions.append("💡 circuit_breaker_threshold must be a whole number, like: circuit_breaker_threshold: 8")
            
            elif "recovery_timeout" in error_path:
                if "minimum" in error_message or "maximum" in error_message:
                    suggestions.append("💡 Try: recovery_timeout: 60 (1 minute is often good)")
                    suggestions.append("🔧 Valid range: 10 seconds (quick) to 300 seconds (conservative)")
                elif "type" in error_message:
                    suggestions.append("💡 recovery_timeout must be a whole number in seconds, like: recovery_timeout: 120")
            
            elif "default_strategy" in error_path or "strategy" in error_path:
                if "enum" in error_message:
                    suggestions.append("💡 Valid strategies: 'aggressive' (fast), 'balanced' (recommended), 'conservative' (reliable), 'critical' (maximum)")
                    suggestions.append("🔧 Try: default_strategy: 'balanced' for most use cases")
            
            elif "operation_overrides" in error_path:
                if "additionalproperties" in error_message.replace(" ", ""):
                    suggestions.append("💡 Valid operations: summarize, sentiment, key_points, questions, qa")
                    suggestions.append("🔧 Example: operation_overrides: {\"qa\": \"critical\", \"sentiment\": \"aggressive\"}")
                elif "enum" in error_message:
                    suggestions.append("💡 Each operation strategy must be: 'aggressive', 'balanced', 'conservative', or 'critical'")
            
            elif "exponential" in error_path:
                suggestions.append("💡 Exponential backoff settings control retry timing")
                suggestions.append("🔧 Default values usually work well - consider using a preset instead")
            
            elif "jitter" in error_path:
                suggestions.append("💡 Jitter adds randomness to prevent thundering herd problems")
                suggestions.append("🔧 Boolean values: true or false, numeric values in reasonable ranges")
            
            # General suggestions based on error type
            if "type" in error_message:
                if "string" in error_message:
                    suggestions.append("📝 This field expects text in quotes, like: \"balanced\"")
                elif "integer" in error_message or "number" in error_message:
                    suggestions.append("📝 This field expects a number without quotes, like: 5")
                elif "boolean" in error_message:
                    suggestions.append("📝 This field expects true or false (without quotes)")
            
            elif "required" in error_message:
                required_fields = schema_context.get("required", [])
                if required_fields:
                    suggestions.append(f"📋 Required fields: {', '.join(required_fields)}")
                suggestions.append("💡 Check that all necessary fields are included in your configuration")
            
            elif "additional properties" in error_message.lower():
                allowed_props = list(schema_context.get("properties", {}).keys())
                if allowed_props:
                    suggestions.append(f"📋 Allowed fields: {', '.join(allowed_props)}")
                suggestions.append("🔧 Remove any fields not in the allowed list")
            
            # Contextual suggestions
            if not suggestions:
                suggestions.append("💡 Consider using a preset configuration instead of custom settings")
                suggestions.append("📖 Check the documentation for examples and valid values")
            
        except Exception as e:
            # Fallback for any errors in suggestion generation
            suggestions.append("💡 Please check the field format and try again")
            logger.debug(f"Error generating suggestions: {e}")
        
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