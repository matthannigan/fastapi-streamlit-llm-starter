---
sidebar_label: test_dependencies
---

# Tests for FastAPI cache dependency integration with preset system.

  file_path: `backend/tests.old/infrastructure/cache/test_dependencies.py`

This module tests the cache dependency injection system with the new preset-based
configuration approach, ensuring all preset configurations work correctly with
FastAPI dependencies and override systems.

Test Categories:
    - Preset-based configuration loading tests
    - Environment variable validation and error handling 
    - Override precedence tests (Custom Config > Environment Variables > Preset Defaults)
    - Invalid preset handling with descriptive error messages
    - Fallback behavior when CACHE_PRESET not specified
    - Configuration validation after loading

Key Dependencies Under Test:
    - get_cache_config(): Main configuration dependency using preset system
    - get_cache_service(): Cache service creation with preset configurations
    - Settings integration with preset system
    - Override handling via CACHE_REDIS_URL, ENABLE_AI_CACHE, CACHE_CUSTOM_CONFIG

## TestCacheConfigDependency

Test cache configuration dependency with preset system.

### test_get_cache_config_with_all_presets()

```python
async def test_get_cache_config_with_all_presets(self, monkeypatch):
```

Test get_cache_config() with all available preset values.

### test_cache_preset_environment_variable_validation()

```python
async def test_cache_preset_environment_variable_validation(self, monkeypatch):
```

Test CACHE_PRESET environment variable validation and error handling.

### test_preset_with_override_combinations()

```python
async def test_preset_with_override_combinations(self, monkeypatch):
```

Test preset + override combinations (CACHE_REDIS_URL, ENABLE_AI_CACHE, CACHE_CUSTOM_CONFIG).

### test_override_precedence()

```python
async def test_override_precedence(self, monkeypatch):
```

Test override precedence: Custom Config > Environment Variables > Preset Defaults.

### test_invalid_preset_names_with_descriptive_errors()

```python
async def test_invalid_preset_names_with_descriptive_errors(self, monkeypatch):
```

Test invalid preset names with descriptive error messages.

### test_fallback_to_development_preset_when_not_specified()

```python
async def test_fallback_to_development_preset_when_not_specified(self, monkeypatch):
```

Test fallback to 'development' preset when CACHE_PRESET not specified.

### test_preset_configuration_validation_after_loading()

```python
async def test_preset_configuration_validation_after_loading(self, monkeypatch):
```

Test preset configuration validation after loading.

## TestCacheServiceDependency

Test cache service dependency with preset system.

### test_get_cache_service_with_preset_configs()

```python
async def test_get_cache_service_with_preset_configs(self, monkeypatch):
```

Test get_cache_service() creation with different preset configurations.

### test_cache_service_fallback_with_invalid_preset()

```python
async def test_cache_service_fallback_with_invalid_preset(self, monkeypatch):
```

Test cache service creation with fallback when preset is invalid.

## TestFastAPIIntegration

Test FastAPI integration with preset-based cache dependencies.

### test_fastapi_app_with_preset_cache_dependency()

```python
def test_fastapi_app_with_preset_cache_dependency(self, monkeypatch):
```

Test FastAPI application using preset-based cache dependency.

## TestCacheDependencyManager

Test CacheDependencyManager with preset system.

### test_dependency_manager_with_preset_configs()

```python
async def test_dependency_manager_with_preset_configs(self, monkeypatch):
```

Test CacheDependencyManager integration with preset configurations.

### test_manager_cleanup_with_preset_caches()

```python
async def test_manager_cleanup_with_preset_caches(self):
```

Test manager cleanup functionality with preset-based caches.

## TestPresetSystemIntegration

Test integration between preset system and dependency injection.

### test_all_presets_produce_valid_dependencies()

```python
async def test_all_presets_produce_valid_dependencies(self, monkeypatch):
```

Test that all available presets produce valid cache dependencies.

### test_preset_system_performance()

```python
async def test_preset_system_performance(self, monkeypatch):
```

Test that preset-based configuration loading performs acceptably.
