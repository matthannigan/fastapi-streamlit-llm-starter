"""
Test suite for ResilienceConfigValidator custom configuration validation.

Verifies that the validator correctly validates custom resilience configurations
against JSON schema and logical constraints.
"""

import pytest
from app.infrastructure.resilience.config_validator import (
    ResilienceConfigValidator,
    ValidationResult
)


class TestResilienceConfigValidatorCustomConfig:
    """
    Test suite for validate_custom_config() method behavior.
    
    Scope:
        - Valid configuration acceptance
        - Invalid configuration rejection
        - Boundary value validation
        - Logical constraint checking
        - ValidationResult structure
        
    Business Critical:
        Accurate custom configuration validation ensures only safe,
        well-formed configurations are accepted in production.
        
    Test Strategy:
        - Test valid minimal configuration
        - Test all optional parameters
        - Test boundary conditions
        - Test invalid configurations
        - Verify ValidationResult structure
    """
    
    def test_validate_custom_config_accepts_minimal_valid_config(self):
        """
        Test that validate_custom_config() accepts minimal valid configuration.

        Verifies:
            A configuration with only retry_attempts is accepted as valid
            per the anyOf schema constraint documented in RESILIENCE_CONFIG_SCHEMA.

        Business Impact:
            Enables simple configuration overrides without requiring
            specification of all possible parameters.

        Scenario:
            Given: A ResilienceConfigValidator instance
            And: A config dictionary with only {"retry_attempts": 3}
            When: validate_custom_config(config) is called
            Then: ValidationResult.is_valid is True
            And: No validation errors are present
            And: Minimal configuration is accepted

        Fixtures Used:
            - None (tests validation logic)
        """
        # Given: A ResilienceConfigValidator instance
        validator = ResilienceConfigValidator()

        # And: A config dictionary with only {"retry_attempts": 3}
        config = {"retry_attempts": 3}

        # When: validate_custom_config(config) is called
        result = validator.validate_custom_config(config)

        # Then: ValidationResult.is_valid is True
        assert result.is_valid is True

        # And: No validation errors are present
        assert len(result.errors) == 0

        # And: Minimal configuration is accepted
        assert isinstance(result, ValidationResult)
    
    def test_validate_custom_config_accepts_complete_valid_config(self):
        """
        Test that validate_custom_config() accepts complete configuration.

        Verifies:
            A configuration with all valid optional parameters is
            accepted by the validation logic.

        Business Impact:
            Ensures comprehensive custom configurations can be validated
            for advanced resilience tuning requirements.

        Scenario:
            Given: A ResilienceConfigValidator instance
            And: A complete config with all parameters (retry_attempts, circuit_breaker_threshold, etc.)
            When: validate_custom_config(config) is called
            Then: ValidationResult.is_valid is True
            And: All parameters are validated correctly

        Fixtures Used:
            - None (tests comprehensive validation)
        """
        # Given: A ResilienceConfigValidator instance
        validator = ResilienceConfigValidator()

        # And: A complete config with all parameters
        config = {
            "retry_attempts": 3,
            "circuit_breaker_threshold": 5,
            "recovery_timeout": 60,
            "default_strategy": "balanced",
            "operation_overrides": {
                "qa": "critical",
                "sentiment": "aggressive"
            },
            "exponential_multiplier": 1.5,
            "exponential_min": 1.0,
            "exponential_max": 30.0,
            "jitter_enabled": True,
            "jitter_max": 2.0,
            "max_delay_seconds": 120
        }

        # When: validate_custom_config(config) is called
        result = validator.validate_custom_config(config)

        # Then: ValidationResult.is_valid is True
        assert result.is_valid is True

        # And: All parameters are validated correctly
        assert len(result.errors) == 0
        assert isinstance(result, ValidationResult)
    
    def test_validate_custom_config_rejects_retry_attempts_below_minimum(self):
        """
        Test that retry_attempts below minimum (1) is rejected.

        Verifies:
            The validator rejects configurations with retry_attempts < 1
            as documented in schema minimum constraint.

        Business Impact:
            Prevents invalid retry configurations that would cause
            runtime errors or unexpected behavior.

        Scenario:
            Given: A ResilienceConfigValidator instance
            And: A config with {"retry_attempts": 0}
            When: validate_custom_config(config) is called
            Then: ValidationResult.is_valid is False
            And: Errors contain message about minimum constraint

        Fixtures Used:
            - None (tests minimum boundary)
        """
        # Given: A ResilienceConfigValidator instance
        validator = ResilienceConfigValidator()

        # And: A config with {"retry_attempts": 0}
        config = {"retry_attempts": 0}

        # When: validate_custom_config(config) is called
        result = validator.validate_custom_config(config)

        # Then: ValidationResult.is_valid is False
        assert result.is_valid is False

        # And: Errors contain message about minimum constraint
        assert len(result.errors) > 0
        assert any("minimum" in error.lower() or "retry_attempts" in error.lower() for error in result.errors)
    
    def test_validate_custom_config_rejects_retry_attempts_above_maximum(self):
        """
        Test that retry_attempts above maximum (10) is rejected.

        Verifies:
            The validator rejects configurations with retry_attempts > 10
            as documented in schema maximum constraint.

        Business Impact:
            Prevents excessive retry configurations that could cause
            unacceptable latency or resource consumption.

        Scenario:
            Given: A ResilienceConfigValidator instance
            And: A config with {"retry_attempts": 20}
            When: validate_custom_config(config) is called
            Then: ValidationResult.is_valid is False
            And: Errors contain message about maximum constraint

        Fixtures Used:
            - None (tests maximum boundary)
        """
        # Given: A ResilienceConfigValidator instance
        validator = ResilienceConfigValidator()

        # And: A config with {"retry_attempts": 20}
        config = {"retry_attempts": 20}

        # When: validate_custom_config(config) is called
        result = validator.validate_custom_config(config)

        # Then: ValidationResult.is_valid is False
        assert result.is_valid is False

        # And: Errors contain message about maximum constraint
        assert len(result.errors) > 0
        assert any("maximum" in error.lower() or "retry_attempts" in error.lower() for error in result.errors)
    
    def test_validate_custom_config_rejects_invalid_strategy_value(self):
        """
        Test that invalid default_strategy value is rejected.

        Verifies:
            The validator rejects configurations with default_strategy
            values not in the enum (aggressive, balanced, conservative, critical).

        Business Impact:
            Prevents runtime errors from invalid strategy references
            that could cause configuration system failures.

        Scenario:
            Given: A ResilienceConfigValidator instance
            And: A config with {"default_strategy": "invalid_value"}
            When: validate_custom_config(config) is called
            Then: ValidationResult.is_valid is False
            And: Errors mention invalid enum value

        Fixtures Used:
            - None (tests enum validation)
        """
        # Given: A ResilienceConfigValidator instance
        validator = ResilienceConfigValidator()

        # And: A config with {"default_strategy": "invalid_value"}
        config = {"default_strategy": "invalid_value"}

        # When: validate_custom_config(config) is called
        result = validator.validate_custom_config(config)

        # Then: ValidationResult.is_valid is False
        assert result.is_valid is False

        # And: Errors mention invalid enum value
        assert len(result.errors) > 0
        assert any("enum" in error.lower() or "invalid_value" in error.lower() or "default_strategy" in error.lower() for error in result.errors)
    
    def test_validate_custom_config_validates_operation_overrides_structure(self):
        """
        Test that operation_overrides structure is validated.

        Verifies:
            The validator checks that operation_overrides keys match
            valid operation names and values are valid strategies.

        Business Impact:
            Ensures operation-specific configurations use valid
            operation names and strategy values.

        Scenario:
            Given: A ResilienceConfigValidator instance
            And: A config with operation_overrides containing invalid operation
            When: validate_custom_config(config) is called
            Then: ValidationResult.is_valid is False
            And: Errors indicate invalid operation name or strategy

        Fixtures Used:
            - None (tests nested structure validation)
        """
        # Given: A ResilienceConfigValidator instance
        validator = ResilienceConfigValidator()

        # And: A config with operation_overrides containing invalid operation
        config = {
            "retry_attempts": 3,
            "operation_overrides": {
                "invalid_operation": "aggressive",  # Invalid operation name
                "sentiment": "invalid_strategy"     # Invalid strategy value
            }
        }

        # When: validate_custom_config(config) is called
        result = validator.validate_custom_config(config)

        # Then: ValidationResult.is_valid is False
        assert result.is_valid is False

        # And: Errors indicate invalid operation name or strategy
        assert len(result.errors) > 0
        error_text = " ".join(result.errors).lower()
        # Should catch either the invalid operation name or invalid strategy value
        assert "invalid_operation" in error_text or "invalid_strategy" in error_text or "enum" in error_text
    
    def test_validate_custom_config_checks_exponential_min_max_relationship(self):
        """
        Test that exponential_min < exponential_max logical constraint is checked.

        Verifies:
            The validator checks logical constraints beyond schema validation,
            such as exponential_min being less than exponential_max.

        Business Impact:
            Prevents illogical retry timing configurations that would
            cause invalid backoff behavior or runtime errors.

        Scenario:
            Given: A ResilienceConfigValidator instance
            And: A config with exponential_min=10.0 and exponential_max=5.0
            When: validate_custom_config(config) is called
            Then: ValidationResult.is_valid is False
            And: Warnings or errors mention logical constraint violation

        Fixtures Used:
            - None (tests logical constraint checking)
        """
        # Given: A ResilienceConfigValidator instance
        validator = ResilienceConfigValidator()

        # And: A config with exponential_min=10.0 and exponential_max=5.0
        config = {
            "retry_attempts": 3,
            "exponential_min": 10.0,
            "exponential_max": 5.0
        }

        # When: validate_custom_config(config) is called
        result = validator.validate_custom_config(config)

        # Then: ValidationResult.is_valid is False
        assert result.is_valid is False

        # And: Warnings or errors mention logical constraint violation
        assert len(result.errors) > 0
        error_text = " ".join(result.errors).lower()
        assert "exponential_min" in error_text and "exponential_max" in error_text
    
    def test_validate_custom_config_generates_helpful_suggestions(self):
        """
        Test that ValidationResult includes helpful suggestions for errors.

        Verifies:
            When validation fails, the suggestions field contains
            actionable guidance for fixing the configuration.

        Business Impact:
            Improves developer experience by providing clear guidance
            for resolving validation errors quickly.

        Scenario:
            Given: A ResilienceConfigValidator instance
            And: An invalid config (e.g., retry_attempts too high)
            When: validate_custom_config(config) is called
            Then: ValidationResult.suggestions is non-empty
            And: Suggestions mention valid ranges or correction steps

        Fixtures Used:
            - None (tests suggestion generation)
        """
        # Given: A ResilienceConfigValidator instance
        validator = ResilienceConfigValidator()

        # And: An invalid config (retry_attempts too high)
        config = {"retry_attempts": 50}  # Exceeds maximum of 10

        # When: validate_custom_config(config) is called
        result = validator.validate_custom_config(config)

        # Then: ValidationResult.suggestions is non-empty
        assert len(result.suggestions) > 0

        # And: Suggestions mention valid ranges or correction steps
        suggestions_text = " ".join(result.suggestions).lower()
        assert any(keyword in suggestions_text for keyword in ["range", "valid", "try", "retry_attempts", "10", "1"])
        assert result.is_valid is False
    
    def test_validate_custom_config_returns_warnings_for_risky_configs(self):
        """
        Test that ValidationResult includes warnings for potentially problematic configs.

        Verifies:
            Valid but potentially problematic configurations generate
            warnings in the ValidationResult.warnings field.

        Business Impact:
            Alerts operators to configurations that may cause issues
            without blocking deployment, enabling informed decisions.

        Scenario:
            Given: A ResilienceConfigValidator instance
            And: A config with extreme but valid values (e.g., retry_attempts=10, circuit_breaker_threshold=1)
            When: validate_custom_config(config) is called
            Then: ValidationResult.is_valid is True
            And: ValidationResult.warnings contains advisory messages

        Fixtures Used:
            - None (tests warning generation)
        """
        # Given: A ResilienceConfigValidator instance
        validator = ResilienceConfigValidator()

        # And: A config with extreme but valid values
        config = {
            "retry_attempts": 10,  # Maximum valid value
            "circuit_breaker_threshold": 1  # Very low threshold
        }

        # When: validate_custom_config(config) is called
        result = validator.validate_custom_config(config)

        # Then: ValidationResult.is_valid is True
        assert result.is_valid is True

        # And: ValidationResult.warnings contains advisory messages
        assert len(result.warnings) > 0
        warnings_text = " ".join(result.warnings).lower()
        assert any(keyword in warnings_text for keyword in ["high", "low", "circuit", "retry", "frequent", "latency"])


class TestResilienceConfigValidatorFallbackValidation:
    """
    Test suite for basic validation fallback when jsonschema unavailable.
    
    Scope:
        - Basic type checking validation
        - Range validation without schema
        - Enum value validation
        - Error message quality in fallback mode
        
    Business Critical:
        Fallback validation maintains core safety even when
        advanced schema validation is unavailable.
    """
    
    def test_validate_custom_config_fallback_validates_types(self, monkeypatch):
        """
        Test that fallback validation checks basic types.

        Verifies:
            Without jsonschema, the validator performs basic type
            checking for configuration values.

        Business Impact:
            Maintains minimum validation quality in environments
            without jsonschema dependency.

        Scenario:
            Given: A ResilienceConfigValidator without jsonschema
            And: A config with retry_attempts="not_a_number"
            When: validate_custom_config(config) is called
            Then: ValidationResult.is_valid is False
            And: Errors indicate type mismatch

        Fixtures Used:
            - monkeypatch: Simulates missing jsonschema
        """
        # Given: A ResilienceConfigValidator without jsonschema
        monkeypatch.setattr("app.infrastructure.resilience.config_validator.JSONSCHEMA_AVAILABLE", False)
        validator = ResilienceConfigValidator()

        # And: A config with retry_attempts="not_a_number"
        config = {"retry_attempts": "not_a_number"}

        # When: validate_custom_config(config) is called
        result = validator.validate_custom_config(config)

        # Then: ValidationResult.is_valid is False
        assert result.is_valid is False

        # And: Errors indicate type mismatch
        assert len(result.errors) > 0
        error_text = " ".join(result.errors).lower()
        assert "integer" in error_text or "type" in error_text
    
    def test_validate_custom_config_fallback_validates_ranges(self, monkeypatch):
        """
        Test that fallback validation checks numeric ranges.

        Verifies:
            Without jsonschema, the validator performs basic range
            checking for numeric configuration values.

        Business Impact:
            Prevents dangerous configurations even without
            full schema validation capabilities.

        Scenario:
            Given: A ResilienceConfigValidator without jsonschema
            And: A config with retry_attempts=100 (exceeds maximum)
            When: validate_custom_config(config) is called
            Then: ValidationResult.is_valid is False
            And: Errors mention exceeding valid range

        Fixtures Used:
            - monkeypatch: Simulates missing jsonschema
        """
        # Given: A ResilienceConfigValidator without jsonschema
        monkeypatch.setattr("app.infrastructure.resilience.config_validator.JSONSCHEMA_AVAILABLE", False)
        validator = ResilienceConfigValidator()

        # And: A config with retry_attempts=100 (exceeds maximum)
        config = {"retry_attempts": 100}

        # When: validate_custom_config(config) is called
        result = validator.validate_custom_config(config)

        # Then: ValidationResult.is_valid is False
        assert result.is_valid is False

        # And: Errors mention exceeding valid range
        assert len(result.errors) > 0
        error_text = " ".join(result.errors).lower()
        assert "retry_attempts" in error_text and ("between" in error_text or "1" in error_text or "10" in error_text)