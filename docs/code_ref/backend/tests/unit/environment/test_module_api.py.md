---
sidebar_label: test_module_api
---

# Tests for module-level environment detection API.

  file_path: `backend/tests/unit/environment/test_module_api.py`

Tests the convenience functions get_environment_info, is_production_environment,
and is_development_environment. Covers global detector usage, confidence thresholds,
and feature context support.

## TestModuleLevelConvenienceFunctions

Test suite for module-level convenience functions.

Scope:
    - get_environment_info() function behavior and global detector usage
    - is_production_environment() and is_development_environment() functions
    - Confidence threshold validation and decision logic

Business Critical:
    Module-level functions provide simple API for environment detection
    throughout infrastructure services and must maintain consistency

### test_get_environment_info_returns_complete_detection_result()

```python
def test_get_environment_info_returns_complete_detection_result(self, mock_global_detector):
```

Test that get_environment_info returns complete EnvironmentInfo.

Verifies:
    Module-level function returns same structure as EnvironmentDetector methods.

Business Impact:
    Provides consistent API for environment detection across the application.

Scenario:
    Given: Module-level get_environment_info function
    When: Calling function with default parameters
    Then: Returns EnvironmentInfo with all required fields populated

Fixtures Used:
    - mock_global_detector: Mocked global environment detector instance

### test_get_environment_info_supports_feature_contexts()

```python
def test_get_environment_info_supports_feature_contexts(self, mock_global_detector):
```

Test that get_environment_info accepts feature context parameters.

Verifies:
    Module-level function supports feature-specific detection.

Business Impact:
    Enables feature-aware detection without creating detector instances.

Scenario:
    Given: Module-level get_environment_info function
    When: Calling function with specific FeatureContext
    Then: Returns EnvironmentInfo with feature-specific detection results

Fixtures Used:
    - mock_global_detector: Mocked global environment detector instance

### test_get_environment_info_validates_feature_context_parameter()

```python
def test_get_environment_info_validates_feature_context_parameter(self):
```

Test that get_environment_info validates feature context parameter.

Verifies:
    Invalid FeatureContext values raise AttributeError as actual behavior.

Business Impact:
    Prevents invalid feature context usage throughout the application.

Scenario:
    Given: Module-level get_environment_info function
    When: Calling function with invalid feature context parameter
    Then: Raises AttributeError due to missing 'value' attribute

Fixtures Used:
    - None (testing parameter validation only)

### test_is_production_environment_uses_confidence_threshold()

```python
def test_is_production_environment_uses_confidence_threshold(self, mock_global_detector):
```

Test that is_production_environment applies documented confidence threshold.

Verifies:
    Function returns True only when confidence > 0.60 and environment is PRODUCTION.

Business Impact:
    Prevents false positive production configuration due to low confidence detection.

Scenario:
    Given: Various environment detection scenarios with different confidence levels
    When: Calling is_production_environment()
    Then: Returns True only for PRODUCTION environment with confidence > 0.60

Fixtures Used:
    - mock_global_detector: Mocked global environment detector instance

### test_is_development_environment_uses_confidence_threshold()

```python
def test_is_development_environment_uses_confidence_threshold(self, mock_global_detector):
```

Test that is_development_environment applies documented confidence threshold.

Verifies:
    Function returns True only when confidence > 0.60 and environment is DEVELOPMENT.

Business Impact:
    Prevents false positive development configuration due to low confidence detection.

Scenario:
    Given: Various environment detection scenarios with different confidence levels
    When: Calling is_development_environment()
    Then: Returns True only for DEVELOPMENT environment with confidence > 0.60

Fixtures Used:
    - mock_global_detector: Mocked global environment detector instance

### test_production_and_development_functions_support_feature_contexts()

```python
def test_production_and_development_functions_support_feature_contexts(self, mock_global_detector, mock_feature_detection_results):
```

Test that environment check functions accept feature context parameters.

Verifies:
    Both is_production_environment and is_development_environment support feature contexts.

Business Impact:
    Enables feature-aware environment checking for specialized infrastructure needs.

Scenario:
    Given: Module-level environment check functions
    When: Calling functions with various FeatureContext parameters
    Then: Functions use feature-specific detection for environment determination

Fixtures Used:
    - mock_feature_detection_results: Detection results for various feature contexts

### test_environment_check_functions_use_same_detection_logic()

```python
def test_environment_check_functions_use_same_detection_logic(self, mock_global_detector):
```

Test that environment check functions use consistent detection logic.

Verifies:
    is_production_environment and is_development_environment use get_environment_info.

Business Impact:
    Ensures consistent detection behavior across all module-level functions.

Scenario:
    Given: Module-level environment check functions
    When: Calling functions under identical conditions
    Then: Functions use same underlying detection logic with consistent results

Fixtures Used:
    - mock_global_detector: Mocked global environment detector for consistency testing
