---
sidebar_label: test_resilience_integration2
---

# Tests for resilience integration.

  file_path: `backend/tests/integration/test_resilience_integration2.py`
Need to combine old test_resilience_endpoints.py and test_preset_resilience_integration.py

This file currently only contains tests that were in test_preset_resilience_integration.py

Integration tests for preset-resilience service integration.

Tests the complete flow from preset selection through resilience service
configuration, including operation-specific strategies, custom overrides,
and legacy configuration compatibility.

## TestPresetResilienceService

Tests for preset resilience service integration.

### mock_settings()

```python
def mock_settings(self):
```

Mock settings for testing.

### test_operation_specific_strategy_application()

```python
def test_operation_specific_strategy_application(self, mock_settings):
```

Test that operation-specific strategies are applied correctly.

### test_preset_override_with_environment_variables()

```python
def test_preset_override_with_environment_variables(self, mock_settings):
```

Test that environment variables can override preset values.

### test_preset_configuration_inheritance()

```python
def test_preset_configuration_inheritance(self, mock_settings):
```

Test that preset configurations inherit properly.

### test_dynamic_configuration_updates()

```python
def test_dynamic_configuration_updates(self, mock_settings):
```

Test that configurations can be dynamically updated.

### test_error_handling_in_preset_loading()

```python
def test_error_handling_in_preset_loading(self, mock_settings):
```

Test error handling when preset loading fails.

### test_end_to_end_custom_override_flow()

```python
def test_end_to_end_custom_override_flow(self, mock_settings):
```

Test complete flow with custom overrides.

### test_configuration_validation()

```python
def test_configuration_validation(self, mock_settings):
```

Test that configuration values are validated.

### test_backwards_compatibility_with_legacy_config()

```python
def test_backwards_compatibility_with_legacy_config(self, mock_settings):
```

Test backwards compatibility with legacy configuration format.

### test_metrics_integration_with_presets()

```python
def test_metrics_integration_with_presets(self, mock_settings):
```

Test that metrics integrate properly with preset configurations.

### test_health_check_integration()

```python
def test_health_check_integration(self, mock_settings):
```

Test health check integration with preset service.

## mock_api_key_auth()

```python
def mock_api_key_auth():
```

Mock API key authentication to allow test API keys.
