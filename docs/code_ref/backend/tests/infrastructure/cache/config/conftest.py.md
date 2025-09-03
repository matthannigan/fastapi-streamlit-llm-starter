---
sidebar_label: conftest
---

# Test fixtures for config module unit tests.

  file_path: `backend/tests/infrastructure/cache/config/conftest.py`

This module provides reusable fixtures specific to cache configuration testing,
focused on providing real configuration instances and test data following
behavior-driven testing principles.

Fixture Categories:
    - Configuration parameter fixtures (basic, comprehensive, invalid)
    - ValidationResult fixtures (valid and invalid states)
    - AI configuration fixtures (valid and invalid AI parameters)
    - Environment variable fixtures for testing environment loading

## valid_basic_config_params()

```python
def valid_basic_config_params():
```

Valid basic configuration parameters for minimal CacheConfig testing.

## valid_comprehensive_config_params()

```python
def valid_comprehensive_config_params():
```

Valid comprehensive configuration parameters including all features.

## invalid_config_params()

```python
def invalid_config_params():
```

Invalid configuration parameters that should trigger validation errors.

## sample_validation_result_valid()

```python
def sample_validation_result_valid():
```

ValidationResult instance representing successful validation.

## sample_validation_result_invalid()

```python
def sample_validation_result_invalid():
```

ValidationResult instance with mixed errors and warnings.

## valid_ai_config_params()

```python
def valid_ai_config_params():
```

Valid AI-specific configuration parameters.

## invalid_ai_config_params()

```python
def invalid_ai_config_params():
```

Invalid AI configuration parameters for testing validation errors.

## builder_with_basic_config()

```python
def builder_with_basic_config():
```

CacheConfigBuilder with basic configuration for accumulation testing.

## builder_with_comprehensive_config()

```python
def builder_with_comprehensive_config(tmp_path):
```

CacheConfigBuilder with comprehensive configuration for build testing.

## sample_config_file_content()

```python
def sample_config_file_content():
```

Sample configuration file content for testing file loading.

## temp_config_file()

```python
def temp_config_file(tmp_path, sample_config_file_content):
```

Temporary configuration file for testing file operations.

## invalid_config_file()

```python
def invalid_config_file(tmp_path):
```

Invalid JSON configuration file for testing error handling.

## environment_variables_basic()

```python
def environment_variables_basic():
```

Basic environment variables for testing environment loading.

## environment_variables_comprehensive()

```python
def environment_variables_comprehensive():
```

Comprehensive environment variables including all features.
