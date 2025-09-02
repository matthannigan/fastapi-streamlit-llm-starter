---
sidebar_label: test_factory
---

# Tests for CacheFactory explicit cache instantiation with preset system integration.

  file_path: `backend/tests.old/infrastructure/cache/test_factory.py`

This module provides comprehensive testing for the CacheFactory class that enables
explicit cache instantiation with deterministic behavior and environment-optimized
defaults. Tests cover all factory methods, validation logic, error handling, preset
integration, and fallback behavior.

Test Categories:
    - Factory Initialization Tests
    - Input Validation Tests
    - Web Application Cache Factory Tests
    - AI Application Cache Factory Tests  
    - Testing Cache Factory Tests
    - Configuration-Based Cache Factory Tests
    - Preset-Based Cache Factory Tests (NEW)
    - Error Handling and Fallback Tests
    - Performance and Integration Tests

## TestCacheFactoryInitialization

Test factory initialization and basic setup.

### test_factory_initialization_success()

```python
def test_factory_initialization_success(self):
```

Test successful factory initialization.

### test_factory_initialization_without_monitoring()

```python
def test_factory_initialization_without_monitoring(self):
```

Test factory works when monitoring is not available.

## TestFactoryInputValidation

Test the _validate_factory_inputs method.

### test_validate_factory_inputs_success()

```python
def test_validate_factory_inputs_success(self):
```

Test successful validation with valid inputs.

### test_validate_factory_inputs_redis_url_errors()

```python
def test_validate_factory_inputs_redis_url_errors(self):
```

Test validation errors for redis_url parameter.

### test_validate_factory_inputs_ttl_errors()

```python
def test_validate_factory_inputs_ttl_errors(self):
```

Test validation errors for default_ttl parameter.

### test_validate_factory_inputs_boolean_errors()

```python
def test_validate_factory_inputs_boolean_errors(self):
```

Test validation errors for boolean parameters.

### test_validate_factory_inputs_additional_params_errors()

```python
def test_validate_factory_inputs_additional_params_errors(self):
```

Test validation errors for additional parameters.

## TestWebAppCacheFactory

Test the for_web_app factory method.

### test_for_web_app_success_with_memory_fallback()

```python
async def test_for_web_app_success_with_memory_fallback(self):
```

Test successful web app cache creation with memory fallback.

### test_for_web_app_custom_parameters()

```python
async def test_for_web_app_custom_parameters(self):
```

Test web app cache with custom parameters.

### test_for_web_app_validation_error()

```python
async def test_for_web_app_validation_error(self):
```

Test web app cache creation with validation errors.

### test_for_web_app_connection_error_strict()

```python
async def test_for_web_app_connection_error_strict(self):
```

Test web app cache with fail_on_connection_error=True.

## TestAIAppCacheFactory

Test the for_ai_app factory method.

### test_for_ai_app_success_with_memory_fallback()

```python
async def test_for_ai_app_success_with_memory_fallback(self):
```

Test successful AI app cache creation with memory fallback.

### test_for_ai_app_custom_parameters()

```python
async def test_for_ai_app_custom_parameters(self):
```

Test AI app cache with custom parameters.

### test_for_ai_app_ai_specific_validation_errors()

```python
async def test_for_ai_app_ai_specific_validation_errors(self):
```

Test AI app cache creation with AI-specific validation errors.

### test_for_ai_app_operation_ttls_validation()

```python
async def test_for_ai_app_operation_ttls_validation(self):
```

Test operation_ttls parameter validation.

### test_for_ai_app_connection_error_strict()

```python
async def test_for_ai_app_connection_error_strict(self):
```

Test AI app cache with fail_on_connection_error=True.

## TestTestingCacheFactory

Test the for_testing factory method.

### test_for_testing_memory_cache_forced()

```python
async def test_for_testing_memory_cache_forced(self):
```

Test testing cache with forced memory cache usage.

### test_for_testing_redis_fallback()

```python
async def test_for_testing_redis_fallback(self):
```

Test testing cache with Redis fallback to memory.

### test_for_testing_custom_parameters()

```python
async def test_for_testing_custom_parameters(self):
```

Test testing cache with custom parameters.

### test_for_testing_validation_errors()

```python
async def test_for_testing_validation_errors(self):
```

Test testing cache with validation errors.

### test_for_testing_connection_error_strict()

```python
async def test_for_testing_connection_error_strict(self):
```

Test testing cache with fail_on_connection_error=True.

## TestConfigurationBasedCacheFactory

Test the create_cache_from_config factory method.

### test_create_cache_from_config_generic_cache()

```python
async def test_create_cache_from_config_generic_cache(self):
```

Test creating generic cache from configuration.

### test_create_cache_from_config_ai_cache()

```python
async def test_create_cache_from_config_ai_cache(self):
```

Test creating AI cache from configuration with AI parameters.

### test_create_cache_from_config_validation_errors()

```python
async def test_create_cache_from_config_validation_errors(self):
```

Test configuration validation errors.

### test_create_cache_from_config_ai_detection()

```python
async def test_create_cache_from_config_ai_detection(self):
```

Test automatic AI cache detection based on parameters.

### test_create_cache_from_config_connection_error_strict()

```python
async def test_create_cache_from_config_connection_error_strict(self):
```

Test configuration-based cache with fail_on_connection_error=True.

## TestFactoryErrorHandlingAndFallback

Test comprehensive error handling and fallback behavior.

### test_factory_graceful_fallback_on_import_errors()

```python
async def test_factory_graceful_fallback_on_import_errors(self):
```

Test factory behavior when cache imports fail.

### test_factory_handles_unexpected_exceptions()

```python
async def test_factory_handles_unexpected_exceptions(self):
```

Test factory handles unexpected exceptions gracefully.

### test_factory_preserves_context_in_errors()

```python
async def test_factory_preserves_context_in_errors(self):
```

Test that factory errors include proper context information.

## TestFactoryIntegration

Test factory integration with actual cache operations.

### test_factory_created_cache_basic_operations()

```python
async def test_factory_created_cache_basic_operations(self):
```

Test that factory-created caches support basic operations.

### test_factory_respects_ttl_settings()

```python
async def test_factory_respects_ttl_settings(self):
```

Test that factory-created caches respect TTL settings.

### test_factory_performance_monitoring_integration()

```python
async def test_factory_performance_monitoring_integration(self):
```

Test that factory integrates performance monitoring when available.

## TestFactoryPerformance

Test factory performance characteristics.

### test_factory_creation_performance()

```python
async def test_factory_creation_performance(self):
```

Test that factory cache creation is reasonably fast.

### test_factory_multiple_cache_creation()

```python
async def test_factory_multiple_cache_creation(self):
```

Test creating multiple caches from the same factory.

## TestPresetBasedFactoryMethods

Test preset integration with factory methods.

### test_for_web_app_with_preset_configuration()

```python
async def test_for_web_app_with_preset_configuration(self, monkeypatch):
```

Test for_web_app() with preset configurations.

### test_for_ai_app_with_preset_configuration()

```python
async def test_for_ai_app_with_preset_configuration(self, monkeypatch):
```

Test for_ai_app() with preset configurations.

### test_for_testing_with_preset_configuration()

```python
async def test_for_testing_with_preset_configuration(self, monkeypatch):
```

Test for_testing() with preset configurations.

### test_create_cache_from_config_with_preset()

```python
async def test_create_cache_from_config_with_preset(self, monkeypatch):
```

Test create_cache_from_config() with preset-based configurations.

## TestFactoryWithPresetOverrides

Test factory methods with preset configurations and parameter overrides.

### test_preset_with_parameter_overrides()

```python
async def test_preset_with_parameter_overrides(self, monkeypatch):
```

Test preset + override parameter combinations in factory methods.

### test_ai_preset_with_ai_parameter_overrides()

```python
async def test_ai_preset_with_ai_parameter_overrides(self, monkeypatch):
```

Test AI preset with AI-specific parameter overrides.

### test_multiple_preset_overrides()

```python
async def test_multiple_preset_overrides(self, monkeypatch):
```

Test multiple parameter overrides with preset base configuration.

## TestFactoryPresetFallbackBehavior

Test fallback behavior when preset loading fails.

### test_fallback_with_invalid_preset()

```python
async def test_fallback_with_invalid_preset(self, monkeypatch):
```

Test factory fallback behavior when preset loading fails.

### test_fallback_with_corrupted_preset_environment()

```python
async def test_fallback_with_corrupted_preset_environment(self, monkeypatch):
```

Test factory behavior with corrupted preset environment.

## TestPresetConfigurationEquivalence

Test behavior equivalence between preset and manual configuration.

### test_preset_vs_manual_configuration_equivalence()

```python
async def test_preset_vs_manual_configuration_equivalence(self, monkeypatch):
```

Test that preset configuration produces equivalent behavior to manual configuration.

### test_ai_preset_vs_manual_ai_configuration_equivalence()

```python
async def test_ai_preset_vs_manual_ai_configuration_equivalence(self, monkeypatch):
```

Test AI preset configuration equivalence with manual AI configuration.
