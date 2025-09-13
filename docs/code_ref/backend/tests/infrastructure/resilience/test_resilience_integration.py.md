---
sidebar_label: test_resilience_integration
---

# Comprehensive tests for the resilience service integration.

  file_path: `backend/tests/infrastructure/resilience/test_resilience_integration.py`

Note: Some tests in this file assume domain-specific operations (summarize, sentiment, etc.)
are registered. In practice, these operations would be registered by domain services
like TextProcessorService during initialization.

## TestResilienceIntegration

Test resilience service integration with settings.

### test_resilience_service_with_preset_config()

```python
def test_resilience_service_with_preset_config(self):
```

Test resilience service initialization with preset configuration.

### test_operation_specific_configuration()

```python
def test_operation_specific_configuration(self):
```

Test that operations get their specific configurations with flexible validation.

### test_operation_resilience_decorator()

```python
def test_operation_resilience_decorator(self):
```

Test the operation-specific resilience decorator.

### test_fallback_to_balanced_strategy()

```python
def test_fallback_to_balanced_strategy(self):
```

Test fallback behavior when invalid strategy is encountered.

### test_legacy_configuration_integration()

```python
def test_legacy_configuration_integration(self):
```

Test that legacy configuration still works with resilience service.

### test_resilience_service_health_check()

```python
def test_resilience_service_health_check(self):
```

Test resilience service health check functionality.

### test_operation_config_caching()

```python
def test_operation_config_caching(self):
```

Test that operation configurations are properly cached with flexible validation.

### test_preset_operation_strategy_mapping()

```python
def test_preset_operation_strategy_mapping(self, preset, operation, expected_strategy):
```

Test that preset-operation strategy mappings work correctly with flexible validation.

### test_custom_config_override_integration()

```python
def test_custom_config_override_integration(self):
```

Test that custom JSON configuration overrides work with resilience service.

### test_resilience_metrics_integration()

```python
def test_resilience_metrics_integration(self):
```

Test that resilience metrics work with preset system.

## TestResilienceConvenienceDecorators

Test the convenience decorator functions.

### test_with_operation_resilience_decorator()

```python
def test_with_operation_resilience_decorator(self):
```

Test the with_operation_resilience decorator.

### test_strategy_specific_decorators()

```python
def test_strategy_specific_decorators(self):
```

Test strategy-specific decorators.
