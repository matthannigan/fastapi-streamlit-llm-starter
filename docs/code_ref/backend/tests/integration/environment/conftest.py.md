---
sidebar_label: conftest
---

# Environment Integration Test Fixtures

  file_path: `backend/tests/integration/environment/conftest.py`

This module provides fixtures for environment detection integration testing, including
environment isolation, configuration management, module reloading utilities, and
integration with infrastructure components like security, cache, and resilience systems.

## clean_environment()

```python
def clean_environment():
```

Provides a clean environment for testing by backing up and restoring os.environ.

This fixture ensures test isolation by:
1. Backing up the current environment variables
2. Clearing variables that affect environment detection
3. Restoring the original environment after the test

Use this fixture in ALL environment detection tests to prevent test pollution.

Business Impact:
    Critical for test reliability and preventing test interference
    
Use Cases:
    - Testing environment detection in controlled conditions
    - Verifying environment-specific behavior
    - Ensuring test isolation between different environment scenarios
    
Cleanup:
    Original environment is completely restored after test completion

## reload_environment_module()

```python
def reload_environment_module():
```

Utility fixture for reloading the environment module after changes.

This fixture provides a function to reload the environment module
to pick up environment variable changes during testing.

Business Impact:
    Ensures environment variable changes are reflected in module state
    
Use Cases:
    - Testing environment changes mid-application
    - Verifying module initialization behavior
    - Testing service adaptation to environment changes

## development_environment()

```python
def development_environment(clean_environment, reload_environment_module):
```

Configures environment variables for a development environment.

This fixture:
1. Sets ENVIRONMENT=development
2. Sets development-specific indicators
3. Reloads environment module to pick up changes

Business Impact:
    Enables testing of development-specific behaviors and configurations
    
Use Cases:
    - Testing development-specific behavior
    - Verifying relaxed security in development
    - Testing cache optimization for development

## production_environment()

```python
def production_environment(clean_environment, reload_environment_module):
```

Configures environment variables for a production environment.

This fixture:
1. Sets ENVIRONMENT=production
2. Sets API keys for production security
3. Reloads environment module to pick up changes

Business Impact:
    Enables testing of production security enforcement and configurations
    
Use Cases:
    - Testing production security enforcement
    - Verifying API key requirements
    - Testing production-specific resilience settings

## staging_environment()

```python
def staging_environment(clean_environment, reload_environment_module):
```

Configures environment variables for a staging environment.

Business Impact:
    Enables testing of staging-specific configurations and behaviors
    
Use Cases:
    - Testing staging-specific behavior
    - Verifying pre-production configurations
    - Testing integration with staging systems

## testing_environment()

```python
def testing_environment(clean_environment, reload_environment_module):
```

Configures environment variables for a testing environment.

Business Impact:
    Enables testing of CI/CD pipeline behaviors
    
Use Cases:
    - Testing CI/CD pipeline behavior
    - Verifying automated test configurations
    - Testing environment detection in test scenarios

## ai_enabled_environment()

```python
def ai_enabled_environment(clean_environment, reload_environment_module):
```

Set up environment with AI features enabled.

Business Impact:
    Enables testing of AI-specific feature contexts and optimizations
    
Configuration:
    - ENABLE_AI_CACHE=true
    - AI-specific feature context testing
    - Cache optimization for AI workloads

## security_enforcement_environment()

```python
def security_enforcement_environment(clean_environment, reload_environment_module):
```

Set up environment with security enforcement enabled.

Business Impact:
    Enables testing of security context overrides and enforcement
    
Configuration:
    - ENFORCE_AUTH=true
    - Security enforcement feature context
    - Production security requirements

## conflicting_signals_environment()

```python
def conflicting_signals_environment(clean_environment, reload_environment_module):
```

Set up environment with conflicting signals for fallback testing.

Business Impact:
    Tests system reliability when environment detection is uncertain
    
Configuration:
    - Conflicting environment indicators
    - Tests fallback behavior
    - Tests confidence scoring with conflicts

## unknown_environment()

```python
def unknown_environment(clean_environment, reload_environment_module):
```

Environment with no clear indicators for fallback testing.

Business Impact:
    Tests system behavior when environment cannot be determined
    
Use Cases:
    - Testing fallback behavior
    - Verifying safe defaults
    - Testing low confidence detection

## custom_detection_config()

```python
def custom_detection_config():
```

Custom detection configuration for testing specialized scenarios.

Business Impact:
    Enables testing of deployment flexibility and custom patterns
    
Use Cases:
    - Testing custom environment detection patterns
    - Verifying custom environment variable precedence
    - Testing specialized deployment configurations

## environment_detector_with_config()

```python
def environment_detector_with_config(custom_detection_config):
```

Environment detector with custom configuration.

Business Impact:
    Enables testing of custom detection logic and specialized scenarios
    
Use Cases:
    - Testing custom pattern matching
    - Verifying custom environment variable precedence
    - Testing feature-specific overrides

## mock_system_indicators()

```python
def mock_system_indicators(tmp_path, monkeypatch):
```

Mock system indicators for testing file-based detection.

Business Impact:
    Enables testing of system-level environment detection
    
Use Cases:
    - Testing file-based environment detection
    - Verifying development environment indicators
    - Testing system-level environment detection

## prod_with_ai_features()

```python
def prod_with_ai_features(clean_environment, reload_environment_module):
```

Production environment with AI features enabled.

## dev_with_security_enforcement()

```python
def dev_with_security_enforcement(clean_environment, reload_environment_module):
```

Development environment with security enforcement enabled.

## test_client()

```python
def test_client():
```

Test client for API endpoint testing.

Business Impact:
    Enables testing of API behavior under different environment configurations
    
Use Cases:
    - Testing authentication behavior
    - Verifying API response differences by environment
    - Testing environment-aware API functionality

## test_database()

```python
def test_database():
```

Test database for integration testing.

Business Impact:
    Provides database access for testing environment-driven database configurations
    
Use Cases:
    - Testing database connection behavior
    - Verifying environment-specific database settings
    - Testing data persistence across environment changes

## performance_monitor()

```python
def performance_monitor():
```

Performance monitoring for testing environment detection speed.

Business Impact:
    Ensures environment detection meets performance SLAs
    
Use Cases:
    - Testing detection speed under load
    - Verifying caching performance
    - Testing concurrent detection performance
