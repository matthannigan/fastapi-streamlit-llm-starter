---
sidebar_label: config_validator
---

# JSON Schema validation for resilience configuration.

  file_path: `backend/app/infrastructure/resilience/config_validator.py`

This module provides JSON Schema definitions and validation utilities
for custom resilience configuration overrides.

## ValidationRateLimiter

Rate limiter for validation requests to prevent abuse.

### __init__()

```python
def __init__(self):
```

### check_rate_limit()

```python
def check_rate_limit(self, identifier: str) -> tuple[bool, str]:
```

Check if request is within rate limits.

Args:
    identifier: Client identifier (IP address, user ID, etc.)
    
Returns:
    Tuple of (allowed, error_message)

### get_rate_limit_status()

```python
def get_rate_limit_status(self, identifier: str) -> Dict[str, Any]:
```

Get current rate limit status for an identifier.

### reset()

```python
def reset(self):
```

Reset all rate limiting state. Used for testing.

## ValidationResult

Result of configuration validation with errors, warnings, and suggestions.

### __init__()

```python
def __init__(self, is_valid: bool, errors: Optional[List[str]] = None, warnings: Optional[List[str]] = None, suggestions: Optional[List[str]] = None):
```

### __bool__()

```python
def __bool__(self) -> bool:
```

### to_dict()

```python
def to_dict(self) -> Dict[str, Any]:
```

Convert to dictionary for JSON serialization.

## ResilienceConfigValidator

Validator for resilience configuration using JSON Schema.

### __init__()

```python
def __init__(self):
```

Initialize the validator.

### get_configuration_templates()

```python
def get_configuration_templates(self) -> Dict[str, Dict[str, Any]]:
```

Get available configuration templates.

Returns:
    Dictionary of template configurations

### get_template()

```python
def get_template(self, template_name: str) -> Optional[Dict[str, Any]]:
```

Get a specific configuration template.

Args:
    template_name: Name of the template to retrieve
    
Returns:
    Template configuration or None if not found

### check_rate_limit()

```python
def check_rate_limit(self, identifier: str) -> ValidationResult:
```

Check rate limit for validation request.

Args:
    identifier: Client identifier (IP, user ID, etc.)
    
Returns:
    ValidationResult indicating if request is allowed

### get_rate_limit_info()

```python
def get_rate_limit_info(self, identifier: str) -> Dict[str, Any]:
```

Get rate limit information for identifier.

### reset_rate_limiter()

```python
def reset_rate_limiter(self):
```

Reset rate limiter state. Used for testing.

### validate_with_security_checks()

```python
def validate_with_security_checks(self, config_data: Any, client_identifier: Optional[str] = None) -> ValidationResult:
```

Validate configuration with enhanced security checks only.

This method focuses on security validation (size limits, forbidden patterns,
field whitelisting, etc.) and does not perform full schema validation.

Args:
    config_data: Configuration data to validate
    client_identifier: Optional client identifier for rate limiting
    
Returns:
    ValidationResult with security validation only

### validate_template_based_config()

```python
def validate_template_based_config(self, template_name: str, overrides: Optional[Dict[str, Any]] = None) -> ValidationResult:
```

Validate configuration based on a template with optional overrides.

Args:
    template_name: Name of the template to use as base
    overrides: Optional overrides to apply to the template
    
Returns:
    ValidationResult for the merged configuration

### suggest_template_for_config()

```python
def suggest_template_for_config(self, config_data: Dict[str, Any]) -> Optional[str]:
```

Suggest the most appropriate template for a given configuration.

Args:
    config_data: Configuration to analyze
    
Returns:
    Name of the most appropriate template or None

### validate_custom_config()

```python
def validate_custom_config(self, config_data: Dict[str, Any]) -> ValidationResult:
```

Validate custom resilience configuration.

Args:
    config_data: Configuration data to validate
    
Returns:
    ValidationResult with validation status and any errors

### validate_preset()

```python
def validate_preset(self, preset_data: Dict[str, Any]) -> ValidationResult:
```

Validate preset configuration.

Args:
    preset_data: Preset data to validate
    
Returns:
    ValidationResult with validation status and any errors

### validate_json_string()

```python
def validate_json_string(self, json_string: str) -> ValidationResult:
```

Validate JSON string for custom configuration.

Args:
    json_string: JSON string to validate
    
Returns:
    ValidationResult with validation status and any errors
