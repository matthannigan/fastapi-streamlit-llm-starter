---
sidebar_label: test_validation_schemas
---

# Unit tests for JSON schema validation system.

  file_path: `backend/tests/infrastructure/resilience/test_validation_schemas.py`

Tests validation of custom resilience configurations and presets.

## TestValidationResult

Test ValidationResult class.

### test_validation_result_creation()

```python
def test_validation_result_creation(self):
```

Test creating validation results.

### test_validation_result_with_errors()

```python
def test_validation_result_with_errors(self):
```

Test validation result with errors.

### test_validation_result_to_dict()

```python
def test_validation_result_to_dict(self):
```

Test converting validation result to dictionary.

## TestResilienceConfigValidator

Test resilience configuration validator.

### test_validator_initialization()

```python
def test_validator_initialization(self):
```

Test validator initialization.

### test_valid_custom_config()

```python
def test_valid_custom_config(self):
```

Test validation of valid custom configuration.

### test_custom_config_with_all_fields()

```python
def test_custom_config_with_all_fields(self):
```

Test validation with all possible fields.

### test_invalid_retry_attempts()

```python
def test_invalid_retry_attempts(self):
```

Test validation with invalid retry attempts.

### test_invalid_circuit_breaker_threshold()

```python
def test_invalid_circuit_breaker_threshold(self):
```

Test validation with invalid circuit breaker threshold.

### test_invalid_recovery_timeout()

```python
def test_invalid_recovery_timeout(self):
```

Test validation with invalid recovery timeout.

### test_invalid_strategy()

```python
def test_invalid_strategy(self):
```

Test validation with invalid strategy.

### test_invalid_operation_overrides()

```python
def test_invalid_operation_overrides(self):
```

Test validation with invalid operation overrides.

### test_logical_validation_exponential_bounds()

```python
def test_logical_validation_exponential_bounds(self):
```

Test logical validation for exponential bounds.

### test_warning_for_retry_delay_mismatch()

```python
def test_warning_for_retry_delay_mismatch(self):
```

Test warning for potential retry/delay mismatch.

### test_validate_json_string_valid()

```python
def test_validate_json_string_valid(self):
```

Test validating valid JSON string.

### test_validate_json_string_invalid_json()

```python
def test_validate_json_string_invalid_json(self):
```

Test validating invalid JSON string.

### test_empty_config_validation()

```python
def test_empty_config_validation(self):
```

Test validation of empty configuration.

## TestPresetValidation

Test preset validation.

### test_valid_preset()

```python
def test_valid_preset(self):
```

Test validation of valid preset.

### test_preset_missing_required_fields()

```python
def test_preset_missing_required_fields(self):
```

Test preset validation with missing required fields.

### test_preset_logical_validation_warnings()

```python
def test_preset_logical_validation_warnings(self):
```

Test preset logical validation warnings.

## TestConfigValidatorIntegration

Test integration with Settings and PresetManager.

### test_settings_validate_custom_config()

```python
def test_settings_validate_custom_config(self):
```

Test Settings.validate_custom_config method.

### test_settings_validate_invalid_custom_config()

```python
def test_settings_validate_invalid_custom_config(self):
```

Test Settings validation with invalid custom config.

### test_settings_validate_external_json()

```python
def test_settings_validate_external_json(self):
```

Test Settings validation with external JSON string.

## TestValidationWithoutJsonSchema

Test validation behavior when jsonschema is not available.

### test_basic_validation_fallback()

```python
def test_basic_validation_fallback(self):
```

Test that basic validation works when jsonschema is unavailable.

### test_basic_preset_validation_fallback()

```python
def test_basic_preset_validation_fallback(self):
```

Test basic preset validation fallback.

## TestValidationSchemas

Test the JSON schema definitions themselves.

### test_resilience_config_schema_structure()

```python
def test_resilience_config_schema_structure(self):
```

Test that the resilience config schema is well-formed.

### test_preset_schema_structure()

```python
def test_preset_schema_structure(self):
```

Test that the preset schema is well-formed.
