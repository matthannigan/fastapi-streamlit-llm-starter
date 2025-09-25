---
sidebar_label: conftest
---

# Environment Integration Test Fixtures

  file_path: `backend/tests.new/integration/environment/conftest.py`

This module provides fixtures for environment detection integration testing, including
environment isolation, configuration management, and integration with infrastructure
components like security, cache, and resilience systems.

## clean_environment()

```python
def clean_environment():
```

Ensure clean environment variables for each test.

This fixture provides complete environment isolation by backing up the
original environment, clearing all environment variables that could affect
environment detection, and restoring the original environment after the test.

This is critical for environment detection integration tests as environment
variables are global state that can cause test interference.

Use Cases:
    - Testing environment detection in controlled conditions
    - Verifying environment-specific behavior
    - Ensuring test isolation between different environment scenarios

Cleanup:
    Original environment is completely restored after test completion

## development_environment()

```python
def development_environment(clean_environment):
```

Set up development environment for integration testing.

Configures the environment to simulate a development deployment with
typical development environment variables and system indicators.

Configuration:
    - ENVIRONMENT=development (highest precedence)
    - No API keys configured
    - Development-specific system indicators

Use Cases:
    - Testing development-specific behavior
    - Verifying relaxed security in development
    - Testing cache optimization for development

## production_environment()

```python
def production_environment(clean_environment):
```

Set up production environment for integration testing.

Configures the environment to simulate a production deployment with
production environment variables and security requirements.

Configuration:
    - ENVIRONMENT=production (highest precedence)
    - API keys configured and required
    - Production-specific system indicators
    - Security enforcement enabled

Use Cases:
    - Testing production security enforcement
    - Verifying API key requirements
    - Testing production-specific resilience settings

## staging_environment()

```python
def staging_environment(clean_environment):
```

Set up staging environment for integration testing.

Configures the environment to simulate a staging deployment with
staging environment variables and balanced security.

Configuration:
    - ENVIRONMENT=staging
    - API keys configured
    - Staging-specific system indicators

Use Cases:
    - Testing staging-specific behavior
    - Verifying pre-production configurations
    - Testing integration with staging systems

## testing_environment()

```python
def testing_environment(clean_environment):
```

Set up testing environment for integration testing.

Configures the environment to simulate a CI/CD testing environment.

Configuration:
    - ENVIRONMENT=testing
    - Minimal security requirements
    - Testing-specific optimizations

Use Cases:
    - Testing CI/CD pipeline behavior
    - Verifying automated test configurations
    - Testing environment detection in test scenarios

## environment_with_hostname()

```python
def environment_with_hostname(clean_environment):
```

Set up environment with hostname-based detection.

Configures environment variables and hostname to test hostname pattern
matching in environment detection.

Use Cases:
    - Testing hostname-based environment detection
    - Verifying containerized deployment detection
    - Testing pattern-based environment classification

## environment_with_system_indicators()

```python
def environment_with_system_indicators(clean_environment):
```

Set up environment with system indicator files.

Creates temporary files that serve as system indicators for environment
detection (e.g., .env, .git, docker-compose files).

Use Cases:
    - Testing file-based environment detection
    - Verifying development environment indicators
    - Testing system-level environment detection

## ai_enabled_environment()

```python
def ai_enabled_environment(clean_environment):
```

Set up environment with AI features enabled.

Configures environment for testing AI-specific feature contexts and
environment detection overrides.

Configuration:
    - ENABLE_AI_CACHE=true
    - AI-specific feature context testing
    - Cache optimization for AI workloads

Use Cases:
    - Testing AI feature context detection
    - Verifying AI-specific environment overrides
    - Testing AI-optimized cache settings

## security_enforcement_environment()

```python
def security_enforcement_environment(clean_environment):
```

Set up environment with security enforcement enabled.

Configures environment for testing security-specific feature contexts
and production overrides.

Configuration:
    - ENFORCE_AUTH=true
    - Security enforcement feature context
    - Production security requirements

Use Cases:
    - Testing security context overrides
    - Verifying security enforcement behavior
    - Testing production security requirements

## mock_environment_detector()

```python
def mock_environment_detector():
```

Mock environment detector for controlled testing.

Provides a mock that can be configured to return specific environment
information for testing component integration without real environment
detection logic.

Use Cases:
    - Testing components that depend on environment detection
    - Isolating component behavior from environment detection logic
    - Testing error scenarios in environment detection

## mock_production_environment_detector()

```python
def mock_production_environment_detector(mock_environment_detector):
```

Mock environment detector configured for production environment.

Pre-configured mock that returns production environment with high
confidence for testing production-specific behavior.

Use Cases:
    - Testing production security enforcement
    - Verifying production cache settings
    - Testing production resilience configurations

## mock_environment_detection_failure()

```python
def mock_environment_detection_failure():
```

Mock environment detector that fails.

Configured to raise exceptions to test error handling and fallback
behavior in components that depend on environment detection.

Use Cases:
    - Testing error handling in environment detection
    - Verifying fallback behavior when detection fails
    - Testing resilience of dependent components

## custom_detection_config()

```python
def custom_detection_config():
```

Custom detection configuration for testing.

Provides a DetectionConfig instance with custom patterns and settings
for testing specialized deployment scenarios.

Use Cases:
    - Testing custom environment detection patterns
    - Verifying custom environment variable precedence
    - Testing specialized deployment configurations

## environment_detector_with_config()

```python
def environment_detector_with_config(custom_detection_config):
```

Environment detector with custom configuration.

Provides an EnvironmentDetector instance with custom configuration
for testing specialized detection scenarios.

Use Cases:
    - Testing custom pattern matching
    - Verifying custom environment variable precedence
    - Testing feature-specific overrides

## prod_with_ai_features()

```python
def prod_with_ai_features(clean_environment):
```

Production environment with AI features enabled.

## dev_with_security_enforcement()

```python
def dev_with_security_enforcement(clean_environment):
```

Development environment with security enforcement enabled.

## unknown_environment()

```python
def unknown_environment(clean_environment):
```

Environment with no clear indicators for fallback testing.
