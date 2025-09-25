---
sidebar_label: test_env_recommendations
---

# Unit tests for environment-aware preset recommendations.

  file_path: `backend/tests.old/unit/infrastructure/resilience/test_env_recommendations.py`

Tests the enhanced environment detection and recommendation functionality
added in Phase 3 of the resilience configuration simplification project.

## TestEnvironmentRecommendations

Test environment-aware preset recommendations.

### test_exact_environment_matches()

```python
def test_exact_environment_matches(self):
```

Test exact environment name matches with high confidence.

### test_pattern_matching_development()

```python
def test_pattern_matching_development(self):
```

Test pattern matching for development-like environments.

### test_pattern_matching_production()

```python
def test_pattern_matching_production(self):
```

Test pattern matching for production-like environments.

### test_pattern_matching_staging()

```python
def test_pattern_matching_staging(self):
```

Test pattern matching for staging environments maps to production preset.

### test_unknown_environment_fallback()

```python
def test_unknown_environment_fallback(self):
```

Test fallback behavior for unknown environment patterns.

### test_auto_detection_from_environment_variables()

```python
def test_auto_detection_from_environment_variables(self, mock_getenv):
```

Test auto-detection from common environment variables.

### test_auto_detection_development_indicators()

```python
def test_auto_detection_development_indicators(self, mock_getenv):
```

Test auto-detection using development indicators.

### test_auto_detection_production_indicators()

```python
def test_auto_detection_production_indicators(self, mock_exists, mock_getenv):
```

Test auto-detection using production indicators.

### test_auto_detection_fallback_to_simple()

```python
def test_auto_detection_fallback_to_simple(self, mock_exists, mock_getenv):
```

Test auto-detection fallback when no clear indicators found.

### test_recommendation_structure()

```python
def test_recommendation_structure(self):
```

Test that recommendation structure contains all required fields.

### test_legacy_recommend_preset_method()

```python
def test_legacy_recommend_preset_method(self):
```

Test that legacy recommend_preset method still works.

### test_case_insensitive_environment_matching()

```python
def test_case_insensitive_environment_matching(self):
```

Test that environment matching is case insensitive.

### test_whitespace_handling()

```python
def test_whitespace_handling(self):
```

Test that environment names with whitespace are handled correctly.

### test_environment_variable_priority()

```python
def test_environment_variable_priority(self):
```

Test that explicit environment variables take priority over indicators.

## TestEnvironmentRecommendationIntegration

Integration tests for environment recommendation system.

### test_recommendation_affects_preset_loading()

```python
def test_recommendation_affects_preset_loading(self):
```

Test that recommendations work with actual preset loading.

### test_all_recommendations_return_valid_presets()

```python
def test_all_recommendations_return_valid_presets(self):
```

Test that all possible recommendations return valid preset names.

### test_confidence_scoring_consistency()

```python
def test_confidence_scoring_consistency(self):
```

Test that confidence scoring is consistent and logical.
