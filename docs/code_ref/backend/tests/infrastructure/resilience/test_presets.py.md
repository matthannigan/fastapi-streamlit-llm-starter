---
sidebar_label: test_presets
---

# Unit tests for resilience preset system.

  file_path: `backend/tests/infrastructure/resilience/test_presets.py`

Tests preset loading, validation, conversion, and integration with Settings class.

## TestResiliencePreset

Test ResiliencePreset data model.

### test_preset_creation()

```python
def test_preset_creation(self):
```

Test creating a resilience preset.

### test_preset_to_dict()

```python
def test_preset_to_dict(self):
```

Test converting preset to dictionary.

### test_preset_to_resilience_config()

```python
def test_preset_to_resilience_config(self):
```

Test converting preset to ResilienceConfig.

## TestPresetManager

Test PresetManager functionality.

### test_preset_manager_initialization()

```python
def test_preset_manager_initialization(self):
```

Test preset manager initialization.

### test_get_preset_valid()

```python
def test_get_preset_valid(self):
```

Test getting a valid preset.

### test_get_preset_invalid()

```python
def test_get_preset_invalid(self):
```

Test getting an invalid preset raises ValueError.

### test_list_presets()

```python
def test_list_presets(self):
```

Test listing all preset names.

### test_get_preset_details()

```python
def test_get_preset_details(self):
```

Test getting detailed preset information.

### test_validate_preset_valid()

```python
def test_validate_preset_valid(self):
```

Test validating a valid preset.

### test_validate_preset_invalid_retry_attempts()

```python
def test_validate_preset_invalid_retry_attempts(self):
```

Test validating preset with invalid retry attempts.

### test_validate_preset_invalid_circuit_breaker_threshold()

```python
def test_validate_preset_invalid_circuit_breaker_threshold(self):
```

Test validating preset with invalid circuit breaker threshold.

### test_validate_preset_invalid_recovery_timeout()

```python
def test_validate_preset_invalid_recovery_timeout(self):
```

Test validating preset with invalid recovery timeout.

### test_recommend_preset()

```python
def test_recommend_preset(self, environment, expected):
```

Test preset recommendations for different environments.

### test_get_all_presets_summary()

```python
def test_get_all_presets_summary(self):
```

Test getting summary of all presets.

## TestPresetDefinitions

Test the predefined presets match specifications.

### test_simple_preset_specification()

```python
def test_simple_preset_specification(self):
```

Test simple preset matches PRD specification.

### test_development_preset_specification()

```python
def test_development_preset_specification(self):
```

Test development preset matches PRD specification.

### test_production_preset_specification()

```python
def test_production_preset_specification(self):
```

Test production preset matches PRD specification.

## TestSettingsIntegration

Test Settings class integration with preset system.

### test_default_resilience_preset()

```python
def test_default_resilience_preset(self):
```

Test default resilience preset setting.

### test_resilience_preset_validation_valid()

```python
def test_resilience_preset_validation_valid(self):
```

Test valid resilience preset passes validation.

### test_resilience_preset_validation_invalid()

```python
def test_resilience_preset_validation_invalid(self):
```

Test invalid resilience preset fails validation with flexible error handling.

### test_has_legacy_resilience_config_false()

```python
def test_has_legacy_resilience_config_false(self):
```

Test detecting no legacy config when using presets.

### test_has_legacy_resilience_config_true_env_vars()

```python
def test_has_legacy_resilience_config_true_env_vars(self):
```

Test detecting legacy config from environment variables.

### test_has_legacy_resilience_config_true_modified_defaults()

```python
def test_has_legacy_resilience_config_true_modified_defaults(self):
```

Test detecting legacy config from modified default values.

### test_get_resilience_config_preset()

```python
def test_get_resilience_config_preset(self):
```

Test getting resilience config from preset.

### test_get_resilience_config_legacy()

```python
def test_get_resilience_config_legacy(self):
```

Test getting resilience config from legacy settings.

### test_get_resilience_config_with_custom_overrides()

```python
def test_get_resilience_config_with_custom_overrides(self):
```

Test getting resilience config with custom JSON overrides.

### test_get_resilience_config_invalid_custom_json()

```python
def test_get_resilience_config_invalid_custom_json(self):
```

Test handling invalid JSON in custom config.

### test_get_resilience_config_fallback_on_error()

```python
def test_get_resilience_config_fallback_on_error(self):
```

Test fallback to simple preset on error.

### test_get_operation_strategy()

```python
def test_get_operation_strategy(self, operation, expected_legacy, expected_preset):
```

Test getting operation-specific strategies with flexible assertion.

### test_get_operation_strategy_fallback()

```python
def test_get_operation_strategy_fallback(self):
```

Test operation strategy fallback on error.

## TestGlobalPresetManager

Test the global preset manager instance.

### test_global_preset_manager_available()

```python
def test_global_preset_manager_available(self):
```

Test global preset manager is available.

### test_global_preset_manager_functionality()

```python
def test_global_preset_manager_functionality(self):
```

Test global preset manager functionality.
