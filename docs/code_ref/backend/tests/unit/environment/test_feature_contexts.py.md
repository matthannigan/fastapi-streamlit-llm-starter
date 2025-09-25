---
sidebar_label: test_feature_contexts
---

# Tests for feature-specific environment detection.

  file_path: `backend/tests/unit/environment/test_feature_contexts.py`

Tests the detect_with_context method with various FeatureContext values including
AI, security, cache, and resilience contexts. Covers feature-specific overrides,
metadata generation, and signal preservation.

## TestEnvironmentDetectorFeatureContexts

Test suite for feature-specific environment detection.

Scope:
    - detect_with_context() method with various FeatureContext values
    - Feature-specific environment variable handling and overrides
    - Metadata generation for configuration hints

Business Critical:
    Feature contexts enable specialized detection for AI, security, cache,
    and resilience systems that may require different environment logic

### test_detect_with_context_default_context_behavior()

```python
def test_detect_with_context_default_context_behavior(self, environment_detector):
```

Test that detect_with_context with DEFAULT context matches basic detection.

Verifies:
    DEFAULT feature context produces same results as standard detection.

Business Impact:
    Ensures consistent behavior between detection methods for standard cases.

Scenario:
    Given: EnvironmentDetector instance
    When: Calling detect_with_context(FeatureContext.DEFAULT)
    Then: Returns same result as detect_environment() with no feature context

Fixtures Used:
    - environment_detector: EnvironmentDetector with default configuration

### test_detect_with_context_ai_enabled_feature_detection()

```python
def test_detect_with_context_ai_enabled_feature_detection(self, environment_detector, mock_ai_environment_vars):
```

Test that AI_ENABLED context applies AI-specific detection logic.

Verifies:
    AI_ENABLED context checks ENABLE_AI_CACHE variable and adds metadata.

Business Impact:
    Enables AI services to receive AI-optimized environment configuration.

Scenario:
    Given: EnvironmentDetector with AI-specific environment variables
    When: Calling detect_with_context(FeatureContext.AI_ENABLED)
    Then: Returns EnvironmentInfo with AI-specific metadata and signal consideration

Fixtures Used:
    - environment_detector: EnvironmentDetector with default configuration
    - mock_ai_environment_vars: Environment with ENABLE_AI_CACHE and related variables

### test_detect_with_context_security_enforcement_override()

```python
def test_detect_with_context_security_enforcement_override(self, environment_detector, mock_security_enforcement_vars):
```

Test that SECURITY_ENFORCEMENT context can override environment to production.

Verifies:
    Security enforcement can force production environment for security features.

Business Impact:
    Ensures security features receive production-level configuration when required.

Scenario:
    Given: EnvironmentDetector with ENFORCE_AUTH=true environment variable
    When: Calling detect_with_context(FeatureContext.SECURITY_ENFORCEMENT)
    Then: May return PRODUCTION environment even in development context

Fixtures Used:
    - environment_detector: EnvironmentDetector with default configuration
    - mock_security_enforcement_vars: Environment with ENFORCE_AUTH=true

### test_detect_with_context_cache_optimization_context()

```python
def test_detect_with_context_cache_optimization_context(self, environment_detector, mock_cache_environment_vars):
```

Test that CACHE_OPTIMIZATION context applies cache-specific detection logic.

Verifies:
    Cache optimization context provides cache-specific environment assessment.

Business Impact:
    Enables cache services to receive optimized configuration recommendations.

Scenario:
    Given: EnvironmentDetector with cache-related environment variables
    When: Calling detect_with_context(FeatureContext.CACHE_OPTIMIZATION)
    Then: Returns EnvironmentInfo with cache-specific metadata and recommendations

Fixtures Used:
    - environment_detector: EnvironmentDetector with default configuration
    - mock_cache_environment_vars: Environment with cache-related configuration

### test_detect_with_context_resilience_strategy_context()

```python
def test_detect_with_context_resilience_strategy_context(self, environment_detector, mock_resilience_environment_vars):
```

Test that RESILIENCE_STRATEGY context applies resilience-specific detection logic.

Verifies:
    Resilience strategy context provides resilience-specific environment assessment.

Business Impact:
    Enables resilience services to receive strategy-appropriate configuration.

Scenario:
    Given: EnvironmentDetector with resilience-related environment variables
    When: Calling detect_with_context(FeatureContext.RESILIENCE_STRATEGY)
    Then: Returns EnvironmentInfo with resilience-specific metadata and recommendations

Fixtures Used:
    - environment_detector: EnvironmentDetector with default configuration
    - mock_resilience_environment_vars: Environment with resilience configuration

### test_detect_with_context_adds_feature_specific_metadata()

```python
def test_detect_with_context_adds_feature_specific_metadata(self, environment_detector, mock_feature_environment_vars):
```

Test that feature contexts add relevant metadata to detection results.

Verifies:
    Feature-specific contexts enrich EnvironmentInfo with configuration hints.

Business Impact:
    Enables infrastructure services to access feature-specific configuration guidance.

Scenario:
    Given: EnvironmentDetector with feature-specific environment variables
    When: Calling detect_with_context() with various FeatureContext values
    Then: Returns EnvironmentInfo with metadata containing feature-specific hints

Fixtures Used:
    - environment_detector: EnvironmentDetector with default configuration
    - mock_feature_environment_vars: Environment with various feature-specific variables

### test_detect_with_context_preserves_base_signals()

```python
def test_detect_with_context_preserves_base_signals(self, environment_detector, mock_security_enforcement_vars):
```

Test that feature contexts preserve base environment signals.

Verifies:
    Feature-specific detection includes both base and feature-specific signals.

Business Impact:
    Ensures feature detection maintains comprehensive signal collection.

Scenario:
    Given: EnvironmentDetector with both base and feature-specific signals
    When: Calling detect_with_context() with specific feature context
    Then: Returns EnvironmentInfo with additional_signals including both types

Fixtures Used:
    - environment_detector: EnvironmentDetector with default configuration
    - mock_mixed_environment_signals: Environment with base and feature-specific signals
