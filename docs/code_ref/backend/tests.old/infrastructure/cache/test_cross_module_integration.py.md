---
sidebar_label: test_cross_module_integration
---

# Cross-Module Integration Testing for Cache Infrastructure

  file_path: `backend/tests.old/infrastructure/cache/test_cross_module_integration.py`

This module provides integration tests that validate the interaction between
cache infrastructure components using actual API signatures.

Test Coverage:
- AI Cache integration with correct method signatures
- Parameter mapping with actual method names
- Configuration integration
- Cross-module dependency resolution
- Preset system integration with cache infrastructure

## TestCrossModuleIntegration

Integration tests for cache infrastructure components.

### performance_monitor()

```python
async def performance_monitor(self):
```

Create a performance monitor for testing.

### integrated_cache_system()

```python
async def integrated_cache_system(self, performance_monitor, monkeypatch):
```

Create an integrated cache system with all components.

### test_ai_cache_basic_integration()

```python
async def test_ai_cache_basic_integration(self, integrated_cache_system):
```

Test basic AI cache operations with correct API signatures.

### test_parameter_mapping_integration()

```python
async def test_parameter_mapping_integration(self, integrated_cache_system):
```

Test parameter mapping with correct method names.

### test_key_generator_integration()

```python
async def test_key_generator_integration(self, integrated_cache_system):
```

Test key generator with correct method names.

### test_monitoring_integration()

```python
async def test_monitoring_integration(self, integrated_cache_system):
```

Test monitoring integration across components.

### test_security_integration()

```python
async def test_security_integration(self, integrated_cache_system):
```

Test security integration across components.

### test_configuration_integration()

```python
async def test_configuration_integration(self, integrated_cache_system, monkeypatch):
```

Test configuration integration.

### test_error_propagation_integration()

```python
async def test_error_propagation_integration(self, integrated_cache_system):
```

Test that errors are properly propagated across components.

### preset_integrated_cache_system()

```python
async def preset_integrated_cache_system(self, performance_monitor, monkeypatch):
```

Create an integrated cache system using preset configuration.

### test_preset_configuration_integration()

```python
async def test_preset_configuration_integration(self, preset_integrated_cache_system):
```

Test integration with preset-based configuration.

### test_preset_override_integration()

```python
async def test_preset_override_integration(self, performance_monitor, monkeypatch):
```

Test integration with preset configuration and custom overrides.

### test_cross_preset_compatibility()

```python
async def test_cross_preset_compatibility(self, performance_monitor, monkeypatch):
```

Test cross-module compatibility with different preset configurations.
