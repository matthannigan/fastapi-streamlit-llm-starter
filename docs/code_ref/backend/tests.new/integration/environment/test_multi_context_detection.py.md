---
sidebar_label: test_multi_context_detection
---

# Multi-Context Environment Detection Integration Tests

  file_path: `backend/tests.new/integration/environment/test_multi_context_detection.py`

This module tests environment detection across different feature contexts (AI, Security,
Cache, Resilience), ensuring that each context provides appropriate metadata and
overrides for its specific use case.

HIGH PRIORITY - Core functionality across all infrastructure services

## TestMultiContextEnvironmentDetection

Integration tests for multi-context environment detection.

Seam Under Test:
    Feature Context → Environment Detection → Context-Specific Metadata

Critical Path:
    Feature-specific context → Detection logic → Metadata and overrides

Business Impact:
    Ensures consistent environment detection across different feature contexts
    while providing appropriate metadata for each context

Test Strategy:
    - Test each feature context provides appropriate metadata
    - Verify context-specific overrides work correctly
    - Test context consistency across different environments
    - Validate metadata format and content for each context

### test_ai_enabled_context_provides_cache_metadata()

```python
def test_ai_enabled_context_provides_cache_metadata(self, ai_enabled_environment):
```

Test that AI_ENABLED context provides AI-specific cache metadata.

Integration Scope:
    AI feature context → Environment detection → Cache metadata generation

Business Impact:
    Ensures AI services get appropriate cache prefixes and optimization hints

Test Strategy:
    - Enable AI features in environment
    - Request environment info with AI context
    - Verify AI-specific metadata is included

Success Criteria:
    - AI context returns enable_ai_cache_enabled = True
    - AI prefix metadata is provided for cache keys
    - Context-specific metadata is correctly applied

### test_security_enforcement_context_applies_overrides()

```python
def test_security_enforcement_context_applies_overrides(self, security_enforcement_environment):
```

Test that SECURITY_ENFORCEMENT context applies production overrides.

Integration Scope:
    Security feature context → Production override → Environment enforcement

Business Impact:
    Allows security-conscious deployments to enforce production rules
    regardless of underlying environment

Test Strategy:
    - Enable security enforcement in development environment
    - Request environment info with security context
    - Verify production override is applied

Success Criteria:
    - Security context overrides to production environment
    - High confidence in security override decision
    - Security enforcement metadata is included

### test_cache_optimization_context_in_production()

```python
def test_cache_optimization_context_in_production(self, production_environment):
```

Test CACHE_OPTIMIZATION context in production environment.

Integration Scope:
    Production environment → Cache optimization context → Cache configuration hints

Business Impact:
    Ensures cache optimization works correctly in production with
    appropriate configuration hints

Test Strategy:
    - Set production environment
    - Request environment info with cache optimization context
    - Verify cache-specific metadata is provided

Success Criteria:
    - Cache context returns production environment
    - Cache optimization metadata is included
    - Context is correctly identified as cache optimization

### test_resilience_strategy_context_in_staging()

```python
def test_resilience_strategy_context_in_staging(self, staging_environment):
```

Test RESILIENCE_STRATEGY context in staging environment.

Integration Scope:
    Staging environment → Resilience strategy context → Resilience configuration hints

Business Impact:
    Ensures resilience patterns work correctly in staging with
    appropriate strategy hints

Test Strategy:
    - Set staging environment
    - Request environment info with resilience strategy context
    - Verify resilience-specific metadata is provided

Success Criteria:
    - Resilience context returns staging environment
    - Resilience strategy metadata is included
    - Context is correctly identified as resilience strategy

### test_default_context_consistency()

```python
def test_default_context_consistency(self, development_environment):
```

Test that DEFAULT context provides consistent detection.

Integration Scope:
    Standard environment detection → Default context → Baseline metadata

Business Impact:
    Ensures baseline environment detection works consistently
    without feature-specific overrides

Test Strategy:
    - Set development environment
    - Request environment info with default context
    - Verify no feature-specific overrides are applied

Success Criteria:
    - Default context returns development environment
    - No feature-specific metadata is added
    - Only base environment signals are present

### test_context_consistency_across_environments()

```python
def test_context_consistency_across_environments(self, clean_environment):
```

Test that feature contexts work consistently across different environments.

Integration Scope:
    Multiple environments → Feature contexts → Consistent metadata patterns

Business Impact:
    Ensures feature contexts provide consistent metadata regardless
    of underlying environment detection

Test Strategy:
    - Test each feature context in multiple environments
    - Verify metadata format consistency
    - Test context-specific behavior is preserved

Success Criteria:
    - AI context always provides AI metadata regardless of environment
    - Security context always provides security metadata
    - Context-specific metadata format is consistent

### test_context_metadata_format_consistency()

```python
def test_context_metadata_format_consistency(self, production_environment):
```

Test that context metadata follows consistent format patterns.

Integration Scope:
    Feature contexts → Metadata generation → Consistent data structures

Business Impact:
    Ensures downstream consumers can reliably parse context metadata

Test Strategy:
    - Test metadata format for each feature context
    - Verify metadata keys follow consistent naming
    - Test metadata value types and structures

Success Criteria:
    - All contexts include feature_context in metadata
    - Boolean flags use consistent key naming (xxx_enabled)
    - String values follow consistent patterns

### test_context_with_custom_configuration()

```python
def test_context_with_custom_configuration(self, custom_detection_config):
```

Test feature contexts with custom detection configuration.

Integration Scope:
    Custom detection config → Feature contexts → Custom metadata and overrides

Business Impact:
    Ensures custom configurations work correctly with feature contexts

Test Strategy:
    - Create detector with custom configuration
    - Test feature contexts with custom config
    - Verify custom metadata and overrides are applied

Success Criteria:
    - Custom configuration is respected
    - Feature-specific custom settings are applied
    - Custom overrides work correctly with contexts

### test_context_signal_collection_completeness()

```python
def test_context_signal_collection_completeness(self, ai_enabled_environment):
```

Test that feature contexts collect all relevant signals.

Integration Scope:
    Feature context → Signal collection → Complete signal set

Business Impact:
    Ensures all relevant signals are collected for comprehensive
    environment detection

Test Strategy:
    - Enable AI features
    - Collect environment signals with AI context
    - Verify all relevant signals are included

Success Criteria:
    - Base environment signals are collected
    - Feature-specific signals are added
    - No relevant signals are missing

### test_context_reasoning_comprehensiveness()

```python
def test_context_reasoning_comprehensiveness(self, security_enforcement_environment):
```

Test that feature contexts provide comprehensive reasoning.

Integration Scope:
    Feature context → Detection logic → Detailed reasoning

Business Impact:
    Ensures debugging and monitoring can understand context decisions

Test Strategy:
    - Enable security enforcement
    - Get environment info with security context
    - Verify reasoning includes all relevant information

Success Criteria:
    - Reasoning includes base environment detection
    - Reasoning includes feature-specific decisions
    - Reasoning explains confidence scoring
