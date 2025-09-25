---
sidebar_label: conftest
---

# Test fixtures for cache presets unit tests.

  file_path: `backend/tests/unit/cache/cache_presets/conftest.py`

This module provides reusable fixtures following behavior-driven testing
principles. Fixtures focus on providing test data and mock dependencies
for testing the public contracts defined in the cache_presets.pyi file.

Fixture Categories:
    - Basic test data fixtures (environment names, preset configurations)
    - Mock dependency fixtures (ValidationResult, CacheValidator)
    - Configuration test data (preset definitions, strategy configurations)
    - Environment detection fixtures (environment variables and contexts)

Design Philosophy:
    - Fixtures represent 'happy path' successful behavior only
    - Error scenarios are configured within individual test functions
    - All fixtures use public contracts from backend/contracts/ directory
    - Stateless mocks for validation utilities (no state management needed)
    - Mock dependencies are spec'd against real classes for accuracy

## sample_environment_names()

```python
def sample_environment_names():
```

Sample environment names for testing environment detection.

Provides a variety of environment naming patterns used to test
the environment detection and recommendation functionality.

## sample_preset_names()

```python
def sample_preset_names():
```

Available preset names from the cache presets system.

Provides the standard preset names as defined in the contract
for testing preset retrieval and validation.

## sample_cache_strategy_values()

```python
def sample_cache_strategy_values():
```

Sample CacheStrategy enum values for testing strategy-based functionality.

Provides the available cache strategy values as defined in the contract
for testing strategy-based configuration and validation.

## sample_cache_config_data()

```python
def sample_cache_config_data():
```

Sample CacheConfig data for testing configuration functionality.

Provides realistic cache configuration data matching the structure
documented in the CacheConfig contract for testing configuration
creation, validation, and conversion.

## sample_secure_cache_config_data()

```python
def sample_secure_cache_config_data():
```

Sample secure CacheConfig data for testing TLS functionality.

Provides cache configuration with security features enabled
for testing secure configuration scenarios.

## sample_ai_cache_config_data()

```python
def sample_ai_cache_config_data():
```

Sample AI-optimized CacheConfig data for testing AI features.

Provides cache configuration with AI features enabled
for testing AI-specific configuration scenarios.

## sample_cache_preset_data()

```python
def sample_cache_preset_data():
```

Sample CachePreset data for testing preset functionality.

Provides realistic preset configuration data matching the structure
documented in the CachePreset contract for testing preset creation,
validation, and conversion.

## sample_ai_preset_data()

```python
def sample_ai_preset_data():
```

Sample AI-optimized CachePreset data for testing AI preset functionality.

Provides AI-specific preset configuration with AI optimizations
for testing AI-related preset scenarios.

## sample_environment_recommendation()

```python
def sample_environment_recommendation():
```

Sample EnvironmentRecommendation for testing recommendation functionality.

Provides a realistic environment recommendation result matching the
EnvironmentRecommendation contract structure.

## mock_environment_variables()

```python
def mock_environment_variables():
```

Mock environment variables for testing environment detection.

Provides a controlled set of environment variables that can be
used to test environment detection without affecting the actual
system environment.

## preset_manager_test_data()

```python
def preset_manager_test_data():
```

Test data for CachePresetManager functionality.

Provides comprehensive test data including presets, recommendations,
and validation scenarios for testing the preset manager.

## default_presets_sample()

```python
def default_presets_sample():
```

Sample DEFAULT_PRESETS data for testing strategy-based configurations.

Provides sample strategy-based preset configurations as would be
returned by get_default_presets() function for testing.

## configuration_conversion_test_data()

```python
def configuration_conversion_test_data():
```

Test data for configuration conversion functionality.

Provides before/after data for testing preset to configuration
conversion and dictionary serialization methods.
