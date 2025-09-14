---
sidebar_label: conftest
---

# Fixtures for environment detection test suite.

  file_path: `backend/tests/core/environment/conftest.py`

This module provides test fixtures for testing the unified environment detection
service. All fixtures focus on external dependencies and test data setup without
exposing internal implementation details of the environment detection module.

Fixture Categories:
    - Basic Configuration: Default and custom DetectionConfig instances
    - Environment Detectors: Pre-configured EnvironmentDetector instances
    - Environment Mocking: Simulated environment variables and system conditions
    - System Mocking: File system, hostname, and system indicator simulation
    - Signal Scenarios: Various combinations of detection signals for testing
    - Error Conditions: Simulated failure scenarios for resilience testing

## custom_detection_config()

```python
def custom_detection_config():
```

Provides DetectionConfig with modified patterns and precedence for testing.

Use Cases:
    - Testing custom environment variable precedence
    - Testing specialized deployment naming patterns
    - Testing feature-specific configuration overrides

Configuration:
    - Custom env_var_precedence with organization-specific variables
    - Modified pattern lists for specialized deployments
    - Feature context overrides for testing scenarios

## custom_precedence_config()

```python
def custom_precedence_config():
```

Provides DetectionConfig with custom environment variable precedence only.

Use Cases:
    - Testing precedence ordering behavior
    - Testing organization-specific variable priorities

## custom_patterns_config()

```python
def custom_patterns_config():
```

Provides DetectionConfig with custom hostname patterns for specialized deployments.

Use Cases:
    - Testing custom hostname pattern matching
    - Testing organization-specific naming conventions

## custom_feature_config()

```python
def custom_feature_config():
```

Provides DetectionConfig with custom feature context configuration.

Use Cases:
    - Testing custom feature-specific detection logic
    - Testing organization-specific feature variables

## custom_indicators_config()

```python
def custom_indicators_config():
```

Provides DetectionConfig with custom system indicators.

Use Cases:
    - Testing custom development/production indicators
    - Testing organization-specific deployment markers

## invalid_patterns_config()

```python
def invalid_patterns_config():
```

Provides DetectionConfig with invalid regex patterns for error testing.

Use Cases:
    - Testing configuration validation
    - Testing error handling for malformed patterns

## environment_detector()

```python
def environment_detector():
```

Provides EnvironmentDetector instance with default configuration.

Use Cases:
    - Standard environment detection testing
    - Baseline behavior validation
    - General functionality testing

## clean_environment()

```python
def clean_environment():
```

Provides clean environment with no detection signals available.

Use Cases:
    - Testing fallback detection behavior
    - Testing behavior when no environment signals are found

Environment State:
    - No environment variables set
    - No system indicators present
    - No hostname patterns available

## mock_environment_conditions()

```python
def mock_environment_conditions():
```

Provides various environment variable configurations for testing.

Use Cases:
    - Testing different environment variable combinations
    - Testing confidence scoring with various signal strengths

Returns:
    Dictionary with different environment scenarios

## mock_multiple_env_vars()

```python
def mock_multiple_env_vars():
```

Provides environment with multiple conflicting environment variables.

Use Cases:
    - Testing environment variable precedence
    - Testing conflict resolution logic

## mock_common_env_values()

```python
def mock_common_env_values():
```

Provides environment variables with common naming conventions.

Use Cases:
    - Testing mapping of common values to Environment enums
    - Testing compatibility with standard naming

## mock_custom_env_vars()

```python
def mock_custom_env_vars():
```

Provides environment variables matching custom precedence configuration.

Use Cases:
    - Testing custom environment variable precedence
    - Testing organization-specific variables

## mock_ai_environment_vars()

```python
def mock_ai_environment_vars():
```

Provides environment variables for AI-specific feature detection.

Use Cases:
    - Testing AI_ENABLED feature context behavior
    - Testing AI-specific metadata generation

## mock_security_enforcement_vars()

```python
def mock_security_enforcement_vars():
```

Provides environment variables for security enforcement testing.

Use Cases:
    - Testing SECURITY_ENFORCEMENT context overrides
    - Testing security-driven environment classification

## mock_cache_environment_vars()

```python
def mock_cache_environment_vars():
```

Provides environment variables for cache optimization testing.

Use Cases:
    - Testing CACHE_OPTIMIZATION feature context
    - Testing cache-specific configuration hints

## mock_resilience_environment_vars()

```python
def mock_resilience_environment_vars():
```

Provides environment variables for resilience strategy testing.

Use Cases:
    - Testing RESILIENCE_STRATEGY feature context
    - Testing resilience-specific metadata generation

## mock_feature_environment_vars()

```python
def mock_feature_environment_vars():
```

Provides comprehensive feature-specific environment variables.

Use Cases:
    - Testing multiple feature contexts together
    - Testing feature-specific metadata collection

## mock_custom_feature_vars()

```python
def mock_custom_feature_vars():
```

Provides environment variables matching custom feature configuration.

Use Cases:
    - Testing custom feature context configuration
    - Testing organization-specific feature variables

## mock_debug_flags()

```python
def mock_debug_flags():
```

Provides various DEBUG flag configurations for testing.

Use Cases:
    - Testing system indicator detection
    - Testing debug flag influence on environment classification

## mock_file_system()

```python
def mock_file_system():
```

Provides mocked file system with various indicator files.

Use Cases:
    - Testing file-based system indicator detection
    - Testing development/production file presence logic

## mock_custom_indicators()

```python
def mock_custom_indicators():
```

Provides environment/filesystem with custom system indicators.

Use Cases:
    - Testing custom system indicator detection
    - Testing organization-specific deployment markers

## mock_hostname_patterns()

```python
def mock_hostname_patterns():
```

Provides various hostname patterns for testing pattern matching.

Use Cases:
    - Testing hostname pattern recognition
    - Testing containerized deployment detection

## mock_custom_hostname()

```python
def mock_custom_hostname():
```

Provides hostname matching custom pattern configuration.

Use Cases:
    - Testing custom hostname pattern matching
    - Testing organization-specific naming conventions

## mock_problematic_hostname()

```python
def mock_problematic_hostname():
```

Provides hostname values that could trigger regex issues.

Use Cases:
    - Testing regex error handling
    - Testing edge cases in pattern matching

## mock_environment_signal()

```python
def mock_environment_signal():
```

Provides known environment signal for predictable detection testing.

Use Cases:
    - Testing detection reasoning and source identification
    - Testing signal processing logic

## mock_primary_signal()

```python
def mock_primary_signal():
```

Provides primary environment signal with identifiable source.

Use Cases:
    - Testing detected_by field population
    - Testing primary signal identification

## mock_environment_signals()

```python
def mock_environment_signals():
```

Provides multiple environment signals for comprehensive testing.

Use Cases:
    - Testing signal collection and summary generation
    - Testing multiple signal processing

## mock_multiple_signals()

```python
def mock_multiple_signals():
```

Provides various types of detection signals for analysis testing.

Use Cases:
    - Testing signal formatting and analysis
    - Testing comprehensive signal collection

## mock_mixed_signal_sources()

```python
def mock_mixed_signal_sources():
```

Provides signals from various sources with different reliability levels.

Use Cases:
    - Testing signal confidence scoring
    - Testing source reliability assessment

## mock_conflicting_signals()

```python
def mock_conflicting_signals():
```

Provides contradictory high-confidence signals for conflict testing.

Use Cases:
    - Testing signal conflict resolution
    - Testing confidence reduction logic

## mock_agreeing_signals()

```python
def mock_agreeing_signals():
```

Provides multiple signals indicating the same environment.

Use Cases:
    - Testing confidence boosting logic
    - Testing signal agreement assessment

## mock_mixed_environment_signals()

```python
def mock_mixed_environment_signals():
```

Provides combination of base and feature-specific signals.

Use Cases:
    - Testing feature context signal preservation
    - Testing comprehensive signal collection

## mock_confidence_scenarios()

```python
def mock_confidence_scenarios():
```

Provides environment conditions producing different confidence levels.

Use Cases:
    - Testing confidence threshold logic
    - Testing environment check function behavior

## mock_known_confidence_signals()

```python
def mock_known_confidence_signals():
```

Provides environment signals with predetermined confidence scores.

Use Cases:
    - Testing confidence score preservation
    - Testing signal confidence analysis

## mock_cacheable_signals()

```python
def mock_cacheable_signals():
```

Provides stable environment signals suitable for caching testing.

Use Cases:
    - Testing signal caching performance
    - Testing repeated detection optimization

## thread_pool()

```python
def thread_pool():
```

Provides thread pool for concurrent testing.

Use Cases:
    - Testing thread safety
    - Testing concurrent detection calls

## mock_global_detector()

```python
def mock_global_detector():
```

Provides mocked global environment detector instance.

Use Cases:
    - Testing module-level convenience functions
    - Testing global detector consistency

## mock_feature_detection_results()

```python
def mock_feature_detection_results():
```

Provides detection results for various feature contexts.

Use Cases:
    - Testing feature context support in convenience functions
    - Testing feature-specific detection consistency

## mock_file_system_errors()

```python
def mock_file_system_errors():
```

Provides file system that raises errors on access attempts.

Use Cases:
    - Testing file system error handling
    - Testing graceful degradation

## mock_env_access_errors()

```python
def mock_env_access_errors():
```

Provides environment that raises errors on variable access.

Use Cases:
    - Testing environment variable access error handling
    - Testing detection resilience

## mock_error_conditions()

```python
def mock_error_conditions():
```

Provides environment conditions designed to trigger specific errors.

Use Cases:
    - Testing error message quality
    - Testing error condition handling

## mock_partial_failure_conditions()

```python
def mock_partial_failure_conditions():
```

Provides environment with some detection mechanisms failing.

Use Cases:
    - Testing partial functionality maintenance
    - Testing detection resilience

## mock_logger()

```python
def mock_logger():
```

Provides mocked logger to capture initialization and detection messages.

Use Cases:
    - Testing logging behavior
    - Validating log message content and levels
