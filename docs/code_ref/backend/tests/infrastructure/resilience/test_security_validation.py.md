---
sidebar_label: test_security_validation
---

# Unit tests for security validation features.

  file_path: `backend/tests/infrastructure/resilience/test_security_validation.py`

Tests enhanced security validation including rate limiting, field whitelisting,
content filtering, and other security measures for configuration validation.

## TestValidationRateLimiter

Test the ValidationRateLimiter class.

### rate_limiter()

```python
def rate_limiter(self):
```

Create a fresh rate limiter for testing.

### test_rate_limiter_initialization()

```python
def test_rate_limiter_initialization(self, rate_limiter):
```

Test rate limiter initializes correctly.

### test_rate_limit_allows_first_request()

```python
def test_rate_limit_allows_first_request(self, rate_limiter):
```

Test that first request is always allowed.

### test_rate_limit_cooldown_enforcement()

```python
def test_rate_limit_cooldown_enforcement(self, rate_limiter):
```

Test cooldown period is enforced.

### test_rate_limit_per_minute_enforcement()

```python
def test_rate_limit_per_minute_enforcement(self, rate_limiter):
```

Test per-minute rate limit enforcement.

### test_rate_limit_per_hour_enforcement()

```python
def test_rate_limit_per_hour_enforcement(self, rate_limiter):
```

Test per-hour rate limit enforcement.

### test_rate_limit_status_reporting()

```python
def test_rate_limit_status_reporting(self, rate_limiter):
```

Test rate limit status reporting.

### test_old_request_cleanup()

```python
def test_old_request_cleanup(self, rate_limiter):
```

Test that old requests are cleaned up properly.

## TestSecurityValidation

Test enhanced security validation features.

### validator()

```python
def validator(self):
```

Create a fresh validator for testing.

### test_security_config_structure()

```python
def test_security_config_structure(self):
```

Test that security configuration has expected structure.

### test_config_size_validation()

```python
def test_config_size_validation(self, validator):
```

Test configuration size limit validation.

### test_forbidden_pattern_detection()

```python
def test_forbidden_pattern_detection(self, validator):
```

Test detection of forbidden patterns.

### test_field_whitelist_validation()

```python
def test_field_whitelist_validation(self, validator):
```

Test field whitelist validation.

### test_nesting_depth_validation()

```python
def test_nesting_depth_validation(self, validator):
```

Test nesting depth limit validation.

### test_string_length_validation()

```python
def test_string_length_validation(self, validator):
```

Test string length limit validation.

### test_object_properties_limit()

```python
def test_object_properties_limit(self, validator):
```

Test object properties count limit.

### test_array_items_limit()

```python
def test_array_items_limit(self, validator):
```

Test array items count limit.

### test_unicode_validation()

```python
def test_unicode_validation(self, validator):
```

Test Unicode character validation.

### test_repeated_characters_detection()

```python
def test_repeated_characters_detection(self, validator):
```

Test detection of excessive repeated characters.

### test_field_type_validation()

```python
def test_field_type_validation(self, validator):
```

Test field type validation against whitelist.

### test_field_range_validation()

```python
def test_field_range_validation(self, validator):
```

Test field range validation.

### test_enum_validation()

```python
def test_enum_validation(self, validator):
```

Test enum value validation.

### test_rate_limit_integration()

```python
def test_rate_limit_integration(self, validator):
```

Test rate limiting integration with validation.

### test_comprehensive_security_validation()

```python
def test_comprehensive_security_validation(self, validator):
```

Test comprehensive security validation with multiple issues.

## TestSecurityValidationEndpoints

Test security validation API endpoints.

### test_security_validation_endpoint_structure()

```python
def test_security_validation_endpoint_structure(self):
```

Test that security validation endpoints have correct structure.

### test_security_config_structure_endpoint()

```python
def test_security_config_structure_endpoint(self):
```

Test security configuration endpoint returns expected structure.

## TestGlobalSecurityValidator

Test the global security validator instance.

### test_global_validator_available()

```python
def test_global_validator_available(self):
```

Test that global validator instance is available.

### test_global_validator_functionality()

```python
def test_global_validator_functionality(self):
```

Test that global validator works correctly.

## TestSecurityValidationPerformance

Test performance characteristics of security validation.

### validator()

```python
def validator(self):
```

Create a fresh validator for testing.

### test_validation_performance()

```python
def test_validation_performance(self, validator):
```

Test that security validation completes in reasonable time.

### test_large_config_validation_performance()

```python
def test_large_config_validation_performance(self, validator):
```

Test performance with larger configurations.
