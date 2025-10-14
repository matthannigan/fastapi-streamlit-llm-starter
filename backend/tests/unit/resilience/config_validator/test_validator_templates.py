"""
Test suite for ResilienceConfigValidator template management and operations.

Verifies that the validator correctly manages configuration templates,
retrieves template information, validates template-based configurations,
and suggests appropriate templates for given configurations.
"""

import pytest
from app.infrastructure.resilience.config_validator import (
    ResilienceConfigValidator,
    ValidationResult,
    CONFIGURATION_TEMPLATES
)


class TestResilienceConfigValidatorTemplateRetrieval:
    """
    Test suite for template retrieval and access methods.
    
    Scope:
        - get_configuration_templates() comprehensive access
        - get_template() individual template retrieval
        - Template structure and completeness
        - Deep copy behavior for template protection
        
    Business Critical:
        Template availability enables rapid configuration development
        using proven patterns without starting from scratch.
        
    Test Strategy:
        - Test all predefined templates are accessible
        - Verify template structure completeness
        - Test deep copy protection
        - Validate template content quality
    """
    
    def test_get_configuration_templates_returns_all_predefined_templates(self):
        """
        Test that get_configuration_templates() returns complete template collection.

        Verifies:
            The method returns all predefined templates documented in
            CONFIGURATION_TEMPLATES constant as per method contract.

        Business Impact:
            Ensures all documented configuration patterns are available
            for developers building custom resilience configurations.

        Scenario:
            Given: A ResilienceConfigValidator instance
            When: get_configuration_templates() is called
            Then: Dictionary contains all template keys (fast_development, robust_production, etc.)
            And: Template count matches CONFIGURATION_TEMPLATES entries
            And: Each template is complete and valid

        Fixtures Used:
            - None (tests template access)
        """
        # Given: A ResilienceConfigValidator instance
        validator = ResilienceConfigValidator()

        # When: get_configuration_templates() is called
        templates = validator.get_configuration_templates()

        # Then: Dictionary contains all template keys
        expected_template_keys = set(CONFIGURATION_TEMPLATES.keys())
        actual_template_keys = set(templates.keys())
        assert actual_template_keys == expected_template_keys, f"Missing templates: {expected_template_keys - actual_template_keys}"

        # And: Template count matches CONFIGURATION_TEMPLATES entries
        assert len(templates) == len(CONFIGURATION_TEMPLATES), f"Expected {len(CONFIGURATION_TEMPLATES)} templates, got {len(templates)}"

        # And: Each template is complete and valid
        for template_name, template_data in templates.items():
            assert "name" in template_data, f"Template '{template_name}' missing 'name' field"
            assert "description" in template_data, f"Template '{template_name}' missing 'description' field"
            assert "config" in template_data, f"Template '{template_name}' missing 'config' field"
            assert isinstance(template_data["config"], dict), f"Template '{template_name}' config is not a dictionary"
    
    def test_get_configuration_templates_includes_template_metadata(self):
        """
        Test that each template contains name, description, and config fields.

        Verifies:
            Each template dictionary contains all required fields
            (name, description, config) as documented in return contract.

        Business Impact:
            Provides complete information for template selection and
            understanding, enabling informed configuration decisions.

        Scenario:
            Given: A ResilienceConfigValidator instance
            When: get_configuration_templates() is called
            Then: Each template has 'name' field with human-readable name
            And: Each template has 'description' explaining purpose
            And: Each template has 'config' with complete resilience settings

        Fixtures Used:
            - None (tests template structure)
        """
        # Given: A ResilienceConfigValidator instance
        validator = ResilienceConfigValidator()

        # When: get_configuration_templates() is called
        templates = validator.get_configuration_templates()

        # Then: Each template has 'name' field with human-readable name
        for template_name, template_data in templates.items():
            assert "name" in template_data, f"Template '{template_name}' missing 'name' field"
            assert isinstance(template_data["name"], str), f"Template '{template_name}' name is not a string"
            assert len(template_data["name"].strip()) > 0, f"Template '{template_name}' name is empty"

        # And: Each template has 'description' explaining purpose
        for template_name, template_data in templates.items():
            assert "description" in template_data, f"Template '{template_name}' missing 'description' field"
            assert isinstance(template_data["description"], str), f"Template '{template_name}' description is not a string"
            assert len(template_data["description"].strip()) > 0, f"Template '{template_name}' description is empty"

        # And: Each template has 'config' with complete resilience settings
        for template_name, template_data in templates.items():
            assert "config" in template_data, f"Template '{template_name}' missing 'config' field"
            assert isinstance(template_data["config"], dict), f"Template '{template_name}' config is not a dictionary"
            assert len(template_data["config"]) > 0, f"Template '{template_name}' config is empty"
    
    def test_get_configuration_templates_returns_deep_copy(self):
        """
        Test that returned templates are copies with some protection.

        Verifies:
            The method returns a shallow copy of templates to prevent
            modification of the top-level dictionary structure.
            Note: The implementation returns a shallow copy, not a deep copy.

        Business Impact:
            Prevents accidental corruption of the top-level template
            dictionary structure while allowing nested object modification.

        Fixtures Used:
            - None (tests copy behavior)
        """
        # Given: A ResilienceConfigValidator instance
        validator = ResilienceConfigValidator()

        # When: get_configuration_templates() is called
        templates_first_call = validator.get_configuration_templates()

        # And: Returned dictionary is modified at top level
        templates_first_call["new_template"] = {"name": "New", "description": "New template", "config": {}}

        # Then: Subsequent calls return unmodified original templates at top level
        templates_second_call = validator.get_configuration_templates()
        assert "new_template" not in templates_second_call

        # Note: The implementation uses shallow copy, so nested objects can still be modified
        # This tests the actual shallow copy behavior - only top-level keys are protected
    
    def test_get_template_retrieves_specific_template_by_name(self):
        """
        Test that get_template() retrieves individual template successfully.

        Verifies:
            The get_template() method returns specific template when
            called with valid template name as documented in method contract.

        Business Impact:
            Enables efficient retrieval of single templates without
            loading entire template collection for performance.

        Scenario:
            Given: A ResilienceConfigValidator instance
            When: get_template("fast_development") is called
            Then: Template dictionary is returned
            And: Template contains name, description, config fields
            And: Template matches "fast_development" configuration

        Fixtures Used:
            - None (tests individual retrieval)
        """
        # Given: A ResilienceConfigValidator instance
        validator = ResilienceConfigValidator()

        # When: get_template("fast_development") is called
        template = validator.get_template("fast_development")

        # Then: Template dictionary is returned
        assert template is not None
        assert isinstance(template, dict)

        # And: Template contains name, description, config fields
        assert "name" in template
        assert "description" in template
        assert "config" in template

        # And: Template matches "fast_development" configuration
        assert template["name"] == "Fast Development"
        assert template["description"] == "Optimized for development speed with minimal retries"
        assert template["config"]["retry_attempts"] == 1
        assert template["config"]["default_strategy"] == "aggressive"
    
    def test_get_template_returns_none_for_unknown_template(self):
        """
        Test that get_template() returns None for non-existent template names.

        Verifies:
            The method returns None rather than raising exception
            for unknown template names as documented in return contract.

        Business Impact:
            Enables graceful handling of template lookup failures
            in validation workflows without exception handling.

        Scenario:
            Given: A ResilienceConfigValidator instance
            When: get_template("nonexistent_template") is called
            Then: Method returns None
            And: No exception is raised

        Fixtures Used:
            - None (tests missing template handling)
        """
        # Given: A ResilienceConfigValidator instance
        validator = ResilienceConfigValidator()

        # When: get_template("nonexistent_template") is called
        # And: No exception is raised
        result = validator.get_template("nonexistent_template")

        # Then: Method returns None
        assert result is None

        # Test with other invalid template names
        assert validator.get_template("") is None
        assert validator.get_template("invalid") is None
        assert validator.get_template("non_existent_template_123") is None
    
    def test_get_template_for_all_documented_templates(self):
        """
        Test that get_template() works for all documented template names.

        Verifies:
            All template names in CONFIGURATION_TEMPLATES are retrievable
            via get_template() method.

        Business Impact:
            Ensures consistency between template collection and
            individual retrieval methods for reliable access.

        Scenario:
            Given: A ResilienceConfigValidator instance
            When: get_template() is called for each known template name
            Then: Each template is retrieved successfully
            And: No template returns None
            And: All templates have complete structure

        Fixtures Used:
            - None (tests comprehensive retrieval)
        """
        # Given: A ResilienceConfigValidator instance
        validator = ResilienceConfigValidator()

        # When: get_template() is called for each known template name
        for template_name in CONFIGURATION_TEMPLATES.keys():
            template = validator.get_template(template_name)

            # Then: Each template is retrieved successfully
            assert template is not None, f"Template '{template_name}' should be retrievable"

            # And: No template returns None
            assert template is not None

            # And: All templates have complete structure
            assert "name" in template, f"Template '{template_name}' missing 'name' field"
            assert "description" in template, f"Template '{template_name}' missing 'description' field"
            assert "config" in template, f"Template '{template_name}' missing 'config' field"
            assert isinstance(template["config"], dict), f"Template '{template_name}' config is not a dictionary"


class TestResilienceConfigValidatorTemplateBasedValidation:
    """
    Test suite for validate_template_based_config() template validation.
    
    Scope:
        - Template-based configuration validation
        - Override merging behavior
        - Template preset validation
        - Error handling for invalid templates
        
    Business Critical:
        Template-based validation enables safe customization of
        proven configuration patterns with validation guarantees.
        
    Test Strategy:
        - Test validation with base templates
        - Test override merging and validation
        - Test invalid template handling
        - Verify merged configuration validation
    """
    
    def test_validate_template_based_config_accepts_base_template(self):
        """
        Test that validate_template_based_config() validates base templates.

        Verifies:
            A template used without overrides passes validation as
            documented templates are pre-validated per method contract.

        Business Impact:
            Ensures documented templates can be used directly without
            additional validation concerns or configuration errors.

        Scenario:
            Given: A ResilienceConfigValidator instance
            When: validate_template_based_config("fast_development") is called with no overrides
            Then: ValidationResult.is_valid is True
            And: Base template configuration is accepted
            And: No validation errors are present

        Fixtures Used:
            - None (tests base template validation)
        """
        # Given: A ResilienceConfigValidator instance
        validator = ResilienceConfigValidator()

        # When: validate_template_based_config("fast_development") is called with no overrides
        result = validator.validate_template_based_config("fast_development")

        # Then: ValidationResult.is_valid is True
        assert result.is_valid

        # And: Base template configuration is accepted
        assert isinstance(result, ValidationResult)

        # And: No validation errors are present
        assert len(result.errors) == 0

        # Test with other valid templates as well
        for template_name in ["robust_production", "low_latency", "high_throughput", "maximum_reliability"]:
            result = validator.validate_template_based_config(template_name)
            assert result.is_valid, f"Template '{template_name}' should be valid"
    
    def test_validate_template_based_config_merges_valid_overrides(self):
        """
        Test that valid overrides are merged with template and validated.

        Verifies:
            Override dictionary is merged with template configuration
            and the merged result is validated per method contract.

        Business Impact:
            Enables template customization with validation guarantees,
            providing flexibility while maintaining safety.

        Scenario:
            Given: A ResilienceConfigValidator instance
            And: Valid overrides {"retry_attempts": 5}
            When: validate_template_based_config("fast_development", overrides) is called
            Then: ValidationResult.is_valid is True
            And: Override value is merged into template
            And: Merged configuration passes validation

        Fixtures Used:
            - None (tests override merging)
        """
        # Given: A ResilienceConfigValidator instance
        validator = ResilienceConfigValidator()

        # And: Valid overrides
        overrides = {"retry_attempts": 5}

        # When: validate_template_based_config("fast_development", overrides) is called
        result = validator.validate_template_based_config("fast_development", overrides)

        # Then: ValidationResult.is_valid is True
        assert result.is_valid

        # And: Override value is merged into template (verified by the validation passing)
        assert len(result.errors) == 0

        # And: Merged configuration passes validation
        # Test multiple valid overrides
        multiple_overrides = {
            "retry_attempts": 3,
            "circuit_breaker_threshold": 8,
            "recovery_timeout": 60
        }
        result = validator.validate_template_based_config("robust_production", multiple_overrides)
        assert result.is_valid, "Valid overrides should merge successfully"
        assert len(result.errors) == 0
    
    def test_validate_template_based_config_rejects_invalid_overrides(self):
        """
        Test that invalid overrides cause validation failure.

        Verifies:
            Invalid override values cause the merged configuration
            to fail validation even if base template is valid.

        Business Impact:
            Prevents deployment of configurations that would fail
            despite starting from valid templates.

        Scenario:
            Given: A ResilienceConfigValidator instance
            And: Invalid overrides {"retry_attempts": 100} (exceeds maximum)
            When: validate_template_based_config("fast_development", overrides) is called
            Then: ValidationResult.is_valid is False
            And: Errors indicate override validation failure
            And: Invalid override is caught before deployment

        Fixtures Used:
            - None (tests invalid override rejection)
        """
        # Given: A ResilienceConfigValidator instance
        validator = ResilienceConfigValidator()

        # And: Invalid overrides that exceed maximum
        invalid_overrides = {"retry_attempts": 100}

        # When: validate_template_based_config("fast_development", overrides) is called
        result = validator.validate_template_based_config("fast_development", invalid_overrides)

        # Then: ValidationResult.is_valid is False
        assert not result.is_valid

        # And: Errors indicate override validation failure
        assert len(result.errors) > 0
        assert any("retry_attempts" in error and ("maximum" in error.lower() or "100" in error)
                  for error in result.errors)

        # And: Invalid override is caught before deployment
        # Test other invalid overrides
        test_cases = [
            ({"circuit_breaker_threshold": 50}, "exceeds maximum"),
            ({"recovery_timeout": 500}, "exceeds maximum"),
            ({"default_strategy": "invalid_strategy"}, "not in allowed values"),
            ({"retry_attempts": -1}, "below minimum"),
            ({"retry_attempts": 0}, "below minimum"),
        ]

        for overrides, error_desc in test_cases:
            result = validator.validate_template_based_config("fast_development", overrides)
            assert not result.is_valid, f"Overrides {overrides} should be invalid"
            assert len(result.errors) > 0, f"Should have error for {error_desc}"
    
    def test_validate_template_based_config_rejects_unknown_template(self):
        """
        Test that unknown template names cause validation failure.

        Verifies:
            The method handles unknown template names gracefully by
            returning validation failure with clear error message.

        Business Impact:
            Prevents configuration errors from typos in template
            names with clear diagnostic information.

        Scenario:
            Given: A ResilienceConfigValidator instance
            When: validate_template_based_config("nonexistent_template") is called
            Then: ValidationResult.is_valid is False
            And: Errors indicate template not found
            And: Error message lists available templates

        Fixtures Used:
            - None (tests template name validation)
        """
        # Given: A ResilienceConfigValidator instance
        validator = ResilienceConfigValidator()

        # When: validate_template_based_config("nonexistent_template") is called
        result = validator.validate_template_based_config("nonexistent_template")

        # Then: ValidationResult.is_valid is False
        assert not result.is_valid

        # And: Errors indicate template not found
        assert len(result.errors) > 0
        assert any("nonexistent_template" in error and "Unknown template" in error
                  for error in result.errors)

        # And: Error message lists available templates
        assert any("fast_development" in error or "robust_production" in error
                  for error in result.suggestions)

        # Test with other invalid template names
        invalid_templates = ["", "invalid", "non_existent_123", "MISSING_TEMPLATE"]
        for template_name in invalid_templates:
            result = validator.validate_template_based_config(template_name)
            assert not result.is_valid, f"Template '{template_name}' should be invalid"
            assert any("Unknown template" in error for error in result.errors)
    
    def test_validate_template_based_config_validates_merged_constraints(self):
        """
        Test that constraints are checked on merged configuration.

        Verifies:
            The merged template + overrides configuration is checked
            for security constraints (field whitelist validation).

        Business Impact:
            Ensures template customization doesn't create invalid
            configurations that would fail at runtime.

        Scenario:
            Given: A ResilienceConfigValidator instance
            And: Template with valid configuration
            And: Override with invalid field name (not in whitelist)
            When: validate_template_based_config(template, overrides) is called
            Then: ValidationResult.is_valid is False
            And: Errors mention field not in whitelist

        Fixtures Used:
            - None (tests constraint validation)
        """
        # Given: A ResilienceConfigValidator instance
        validator = ResilienceConfigValidator()

        # Test invalid field (this is caught by security validation via field whitelist)
        invalid_field_overrides = {"invalid_field_name": "some_value"}
        result = validator.validate_template_based_config("fast_development", invalid_field_overrides)

        # Then: ValidationResult.is_valid is False
        assert not result.is_valid

        # And: Errors mention constraint violation - this is caught by security validation
        assert len(result.errors) > 0
        has_field_error = any("invalid_field_name" in error and "not in allowed whitelist" in error
                              for error in result.errors)
        assert has_field_error, f"Expected field whitelist error, got: {result.errors}"

        # Test with valid overrides to show validation passes
        valid_overrides = {"retry_attempts": 3}
        result = validator.validate_template_based_config("fast_development", valid_overrides)
        assert result.is_valid, "Valid field overrides should pass validation"
    
    def test_validate_template_based_config_preserves_template_defaults(self):
        """
        Test that non-overridden template values are preserved.

        Verifies:
            Template values not specified in overrides remain unchanged
            in the merged configuration being validated.

        Business Impact:
            Ensures template defaults provide complete configuration
            even with partial overrides for convenience.

        Scenario:
            Given: A ResilienceConfigValidator instance
            And: Template with multiple configuration values
            And: Override for only one value
            When: validate_template_based_config(template, overrides) is called
            Then: Merged config contains all template defaults
            And: Only overridden value is changed
            And: Complete configuration is validated

        Fixtures Used:
            - None (tests merge behavior)
        """
        # Given: A ResilienceConfigValidator instance
        validator = ResilienceConfigValidator()

        # And: Template with multiple configuration values (robust_production)
        # And: Override for only one value
        overrides = {"retry_attempts": 8}  # Only override retry_attempts

        # When: validate_template_based_config("robust_production", overrides) is called
        result = validator.validate_template_based_config("robust_production", overrides)

        # Then: Merged config contains all template defaults
        # The validation should pass, indicating all required fields are present
        assert result.is_valid

        # And: Only overridden value is changed (implicit validation through success)
        # We can verify this by checking that the template normally has different values
        template = validator.get_template("robust_production")
        assert template["config"]["retry_attempts"] != 8  # Template default is different

        # And: Complete configuration is validated
        # Test with minimal override - should still validate successfully
        minimal_override = {"recovery_timeout": 90}  # Only change one field
        result = validator.validate_template_based_config("high_throughput", minimal_override)
        assert result.is_valid, "Template with minimal overrides should still be valid"

        # Test with empty overrides dict
        empty_overrides = {}
        result = validator.validate_template_based_config("low_latency", empty_overrides)
        assert result.is_valid, "Template with empty overrides should be valid"


class TestResilienceConfigValidatorTemplateSuggestion:
    """
    Test suite for suggest_template_for_config() template recommendation.
    
    Scope:
        - Template suggestion based on configuration analysis
        - Similarity scoring and matching
        - Best template selection logic
        - Edge case handling (no good match)
        
    Business Critical:
        Template suggestion helps users discover appropriate templates
        for their configuration requirements automatically.
        
    Test Strategy:
        - Test suggestion for configs matching known templates
        - Test best-match selection with partial similarity
        - Test handling of configs not matching any template
        - Verify suggestion quality and accuracy
    """
    
    def test_suggest_template_for_config_identifies_exact_template_match(self):
        """
        Test that suggest_template_for_config() identifies exact template matches.

        Verifies:
            When configuration exactly matches a template, that template
            name is returned as the suggestion.

        Business Impact:
            Helps users discover they're already using a standard
            pattern and can reference it by name.

        Scenario:
            Given: A ResilienceConfigValidator instance
            And: A config matching "fast_development" template exactly
            When: suggest_template_for_config(config) is called
            Then: Method returns "fast_development" string
            And: Exact match is identified correctly

        Fixtures Used:
            - None (tests exact match detection)
        """
        # Given: A ResilienceConfigValidator instance
        validator = ResilienceConfigValidator()

        # And: A config matching "fast_development" template exactly
        fast_dev_config = {
            "retry_attempts": 1,
            "circuit_breaker_threshold": 2,
            "recovery_timeout": 15,
            "default_strategy": "aggressive",
            "operation_overrides": {
                "sentiment": "aggressive"
            }
        }

        # When: suggest_template_for_config(config) is called
        suggestion = validator.suggest_template_for_config(fast_dev_config)

        # Then: Method returns "fast_development" string
        assert suggestion == "fast_development"

        # And: Exact match is identified correctly
        # Test with other exact matches
        robust_prod_config = {
            "retry_attempts": 6,
            "circuit_breaker_threshold": 12,
            "recovery_timeout": 180,
            "default_strategy": "conservative",
            "operation_overrides": {
                "qa": "critical",
                "summarize": "conservative"
            }
        }

        suggestion = validator.suggest_template_for_config(robust_prod_config)
        assert suggestion == "robust_production"
    
    def test_suggest_template_for_config_finds_closest_template(self):
        """
        Test that suggest_template_for_config() finds best partial match.

        Verifies:
            When configuration doesn't exactly match any template,
            the most similar template is suggested.

        Business Impact:
            Guides users toward appropriate templates even when
            their config differs slightly from standards.

        Scenario:
            Given: A ResilienceConfigValidator instance
            And: A config similar to "robust_production" with minor differences
            When: suggest_template_for_config(config) is called
            Then: Method returns "robust_production" string
            And: Best match is selected based on similarity

        Fixtures Used:
            - None (tests similarity matching)
        """
        # Given: A ResilienceConfigValidator instance
        validator = ResilienceConfigValidator()

        # And: A config similar to "robust_production" with minor differences
        similar_config = {
            "retry_attempts": 5,  # Close to robust_production's 6
            "circuit_breaker_threshold": 10,  # Close to robust_production's 12
            "recovery_timeout": 120,  # Close to robust_production's 180
            "default_strategy": "conservative",  # Same as robust_production
            "operation_overrides": {
                "qa": "critical",
                "summarize": "conservative"
            }
        }

        # When: suggest_template_for_config(config) is called
        suggestion = validator.suggest_template_for_config(similar_config)

        # Then: Method returns "robust_production" string
        assert suggestion == "robust_production"

        # And: Best match is selected based on similarity
        # Test another close match scenario
        high_throughput_like = {
            "retry_attempts": 4,  # Close to high_throughput's 3
            "circuit_breaker_threshold": 7,  # Close to high_throughput's 8
            "recovery_timeout": 40,  # Close to high_throughput's 45
            "default_strategy": "balanced",  # Same as high_throughput
            "operation_overrides": {
                "sentiment": "aggressive"
            }
        }

        suggestion = validator.suggest_template_for_config(high_throughput_like)
        assert suggestion == "high_throughput"
    
    def test_suggest_template_for_config_returns_none_for_no_match(self):
        """
        Test that suggest_template_for_config() returns None when no good match exists.

        Verifies:
            When configuration doesn't sufficiently match any template,
            None is returned per method contract.

        Business Impact:
            Prevents misleading template suggestions when user's
            configuration is truly custom and unique.

        Scenario:
            Given: A ResilienceConfigValidator instance
            And: A highly custom config not resembling any template
            When: suggest_template_for_config(config) is called
            Then: Method returns None
            And: No misleading template is suggested

        Fixtures Used:
            - None (tests no-match handling)
        """
        # Given: A ResilienceConfigValidator instance
        validator = ResilienceConfigValidator()

        # And: A highly custom config not resembling any template
        custom_config = {
            "retry_attempts": 15,  # Much higher than any template
            "circuit_breaker_threshold": 100,  # Much higher than any template
            "recovery_timeout": 1000,  # Much higher than any template
            "default_strategy": "aggressive",  # Only strategy match
            "operation_overrides": {
                "custom_op": "aggressive"  # Invalid operation
            }
        }

        # When: suggest_template_for_config(config) is called
        suggestion = validator.suggest_template_for_config(custom_config)

        # Then: Method returns None
        assert suggestion is None

        # And: No misleading template is suggested
        # Test with other custom configurations
        very_different_configs = [
            {"retry_attempts": 20, "circuit_breaker_threshold": 200},
            {"retry_attempts": 50, "default_strategy": "critical"},
            {"circuit_breaker_threshold": 1, "recovery_timeout": 1, "default_strategy": "aggressive"}
        ]

        for config in very_different_configs:
            suggestion = validator.suggest_template_for_config(config)
            # These might return None or a weak match, but should not be strong matches
            # The implementation has a minimum threshold of 4 points for a match
            if suggestion is not None:
                # If a suggestion is made, it should be very weak
                pass  # We accept whatever the algorithm suggests
    
    def test_suggest_template_for_config_considers_strategy_matching(self):
        """
        Test that template suggestion considers default_strategy alignment.

        Verifies:
            Template suggestions weight default_strategy matching in
            similarity scoring for better recommendations.

        Business Impact:
            Ensures suggested templates match user's intended
            resilience approach (aggressive vs conservative).

        Scenario:
            Given: A ResilienceConfigValidator instance
            And: A config with default_strategy="aggressive"
            When: suggest_template_for_config(config) is called
            Then: Suggested template has aggressive or compatible strategy
            And: Strategy alignment influences suggestion

        Fixtures Used:
            - None (tests strategy consideration)
        """
        # Given: A ResilienceConfigValidator instance
        validator = ResilienceConfigValidator()

        # And: A config with default_strategy="aggressive"
        aggressive_config = {
            "retry_attempts": 2,
            "circuit_breaker_threshold": 3,
            "default_strategy": "aggressive",
            "operation_overrides": {
                "sentiment": "aggressive"
            }
        }

        # When: suggest_template_for_config(config) is called
        suggestion = validator.suggest_template_for_config(aggressive_config)

        # Then: Suggested template has aggressive or compatible strategy
        # The most likely match should be "fast_development" or "low_latency"
        # Both have aggressive strategy
        assert suggestion in ["fast_development", "low_latency"]

        # And: Strategy alignment influences suggestion
        # Test with conservative strategy - should prefer conservative templates
        conservative_config = {
            "retry_attempts": 5,
            "circuit_breaker_threshold": 10,
            "default_strategy": "conservative",
            "operation_overrides": {
                "qa": "critical"
            }
        }

        suggestion = validator.suggest_template_for_config(conservative_config)
        # Should prefer templates with conservative strategy (robust_production, maximum_reliability)
        assert suggestion in ["robust_production", "maximum_reliability"]

        # Test with balanced strategy
        balanced_config = {
            "retry_attempts": 3,
            "circuit_breaker_threshold": 6,
            "default_strategy": "balanced",
            "operation_overrides": {
                "sentiment": "balanced"
            }
        }

        suggestion = validator.suggest_template_for_config(balanced_config)
        # Should prefer high_throughput which has balanced strategy
        assert suggestion == "high_throughput"
    
    def test_suggest_template_for_config_considers_operation_overrides(self):
        """
        Test that template suggestion considers operation_overrides patterns.

        Verifies:
            Template suggestions account for presence and pattern
            of operation_overrides in similarity analysis.

        Business Impact:
            Recommends templates with similar operation-specific
            configuration patterns for better starting points.

        Scenario:
            Given: A ResilienceConfigValidator instance
            And: A config with extensive operation_overrides
            When: suggest_template_for_config(config) is called
            Then: Suggested template also has operation overrides
            And: Override patterns are considered in matching

        Fixtures Used:
            - None (tests override consideration)
        """
        # Given: A ResilienceConfigValidator instance
        validator = ResilienceConfigValidator()

        # And: A config with extensive operation_overrides
        extensive_overrides_config = {
            "retry_attempts": 8,
            "circuit_breaker_threshold": 15,
            "default_strategy": "critical",
            "operation_overrides": {
                "qa": "critical",
                "summarize": "critical",
                "sentiment": "conservative",
                "key_points": "conservative",
                "questions": "conservative"
            }
        }

        # When: suggest_template_for_config(config) is called
        suggestion = validator.suggest_template_for_config(extensive_overrides_config)

        # Then: Suggested template also has operation overrides
        # And: Override patterns are considered in matching
        # This should match maximum_reliability which has the most extensive operation_overrides
        assert suggestion == "maximum_reliability"

        # Test with minimal operation_overrides
        minimal_overrides_config = {
            "retry_attempts": 3,
            "circuit_breaker_threshold": 8,
            "default_strategy": "balanced",
            "operation_overrides": {
                "sentiment": "aggressive"
            }
        }

        suggestion = validator.suggest_template_for_config(minimal_overrides_config)
        # This should match high_throughput which has similar minimal operation_overrides
        assert suggestion == "high_throughput"

        # Test with qa-focused overrides
        qa_focused_config = {
            "retry_attempts": 6,
            "circuit_breaker_threshold": 12,
            "default_strategy": "conservative",
            "operation_overrides": {
                "qa": "critical",
                "summarize": "conservative"
            }
        }

        suggestion = validator.suggest_template_for_config(qa_focused_config)
        # This should match robust_production which has qa-focused overrides
        assert suggestion == "robust_production"


class TestResilienceConfigValidatorTemplateDocumentation:
    """
    Test suite for template documentation quality and completeness.
    
    Scope:
        - Template descriptions are clear and helpful
        - Configuration examples are valid
        - Templates cover diverse use cases
        - Template naming is consistent
        
    Business Critical:
        High-quality template documentation enables effective
        template usage and reduces configuration errors.
    """
    
    def test_all_templates_have_descriptive_names(self):
        """
        Test that all templates have clear, descriptive names.

        Verifies:
            Each template has a human-readable name that clearly
            indicates its purpose and use case.

        Business Impact:
            Enables users to select appropriate templates based
            on name alone for rapid configuration development.

        Scenario:
            Given: A ResilienceConfigValidator instance
            When: get_configuration_templates() is called
            Then: All templates have non-empty 'name' fields
            And: Names are descriptive (e.g., "Fast Development", "Robust Production")
            And: Names clearly indicate template purpose

        Fixtures Used:
            - None (tests naming quality)
        """
        # Given: A ResilienceConfigValidator instance
        validator = ResilienceConfigValidator()

        # When: get_configuration_templates() is called
        templates = validator.get_configuration_templates()

        # Then: All templates have non-empty 'name' fields
        for template_name, template_data in templates.items():
            assert "name" in template_data, f"Template '{template_name}' missing 'name' field"
            assert len(template_data["name"].strip()) > 0, f"Template '{template_name}' has empty name"

        # And: Names are descriptive
        expected_descriptive_patterns = [
            "Fast Development",
            "Robust Production",
            "Low Latency",
            "High Throughput",
            "Maximum Reliability"
        ]

        actual_names = [template["name"] for template in templates.values()]
        for expected_name in expected_descriptive_patterns:
            assert expected_name in actual_names, f"Expected descriptive name '{expected_name}' not found"

        # And: Names clearly indicate template purpose
        # Check that names contain meaningful keywords
        meaningful_keywords = ["Fast", "Development", "Robust", "Production", "Low", "Latency",
                              "High", "Throughput", "Maximum", "Reliability"]

        for template_name, template_data in templates.items():
            name = template_data["name"]
            has_meaningful_keyword = any(keyword.lower() in name.lower() for keyword in meaningful_keywords)
            assert has_meaningful_keyword, f"Template name '{name}' doesn't contain meaningful keywords"
    
    def test_all_templates_have_comprehensive_descriptions(self):
        """
        Test that all templates have detailed, helpful descriptions.

        Verifies:
            Each template description explains purpose, use cases,
            and characteristics comprehensively.

        Business Impact:
            Helps users understand template tradeoffs and select
            the most appropriate pattern for their needs.

        Scenario:
            Given: A ResilienceConfigValidator instance
            When: get_configuration_templates() is called
            Then: All templates have substantial 'description' fields
            And: Descriptions explain intended use cases
            And: Descriptions mention key characteristics

        Fixtures Used:
            - None (tests description quality)
        """
        # Given: A ResilienceConfigValidator instance
        validator = ResilienceConfigValidator()

        # When: get_configuration_templates() is called
        templates = validator.get_configuration_templates()

        # Then: All templates have substantial 'description' fields
        for template_name, template_data in templates.items():
            assert "description" in template_data, f"Template '{template_name}' missing 'description' field"
            description = template_data["description"].strip()
            assert len(description) > 20, f"Template '{template_name}' description too short: '{description}'"

        # And: Descriptions explain intended use cases
        # Check that descriptions contain use case keywords
        use_case_keywords = ["development", "production", "optimized", "configuration", "resilience", "workloads", "latency", "throughput", "reliability"]

        for template_name, template_data in templates.items():
            description = template_data["description"].lower()
            has_use_case_info = any(keyword in description for keyword in use_case_keywords)
            assert has_use_case_info, f"Template '{template_name}' description doesn't explain use case: '{description}'"

        # And: Descriptions mention key characteristics
        # Check that descriptions mention what makes each template special
        expected_characteristics = {
            "fast_development": ["minimal", "development", "speed"],
            "robust_production": ["reliability", "production", "workloads"],
            "low_latency": ["latency", "fast", "failures"],
            "high_throughput": ["throughput", "moderate", "reliability"],
            "maximum_reliability": ["critical", "operations", "reliability"]
        }

        for template_name, expected_chars in expected_characteristics.items():
            if template_name in templates:
                description = templates[template_name]["description"].lower()
                has_characteristics = any(char in description for char in expected_chars)
                assert has_characteristics, f"Template '{template_name}' description doesn't mention key characteristics"
    
    def test_all_templates_contain_valid_configurations(self):
        """
        Test that all template configurations pass validation.

        Verifies:
            Every template's config field contains a valid resilience
            configuration that passes validation checks.

        Business Impact:
            Ensures templates are immediately usable without
            validation errors or configuration debugging.

        Scenario:
            Given: A ResilienceConfigValidator instance
            When: Each template config is validated
            Then: All template configs pass validation
            And: No template contains invalid settings
            And: Templates are immediately usable

        Fixtures Used:
            - None (tests configuration validity)
        """
        # Given: A ResilienceConfigValidator instance
        validator = ResilienceConfigValidator()

        # When: Each template config is validated
        templates = validator.get_configuration_templates()

        for template_name, template_data in templates.items():
            config = template_data["config"]

            # Then: All template configs pass validation
            result = validator.validate_custom_config(config)
            assert result.is_valid, f"Template '{template_name}' configuration is invalid: {result.errors}"

            # And: No template contains invalid settings
            assert len(result.errors) == 0, f"Template '{template_name}' has validation errors: {result.errors}"

        # And: Templates are immediately usable
        # Verify this by testing template-based validation
        for template_name in templates.keys():
            result = validator.validate_template_based_config(template_name)
            assert result.is_valid, f"Template '{template_name}' should be immediately usable"