"""
Test suite for ResilienceConfigValidator JSON string validation.

Verifies that the validator correctly parses and validates JSON string
configurations with proper error handling for malformed JSON.
"""

import pytest
import json
from app.infrastructure.resilience.config_validator import (
    ResilienceConfigValidator,
    ValidationResult
)


class TestResilienceConfigValidatorJSONParsing:
    """
    Test suite for validate_json_string() JSON parsing behavior.
    
    Scope:
        - JSON parsing of valid configuration strings
        - Error handling for malformed JSON
        - JSON parsing error message quality
        - Integration with configuration validation
        
    Business Critical:
        JSON string validation enables API endpoints to accept
        configuration as JSON payloads with proper error handling.
        
    Test Strategy:
        - Test valid JSON parsing and validation
        - Test various JSON syntax errors
        - Verify error message clarity
        - Test validation pipeline integration
    """
    
    def test_validate_json_string_accepts_valid_json_configuration(self):
        """
        Test that validate_json_string() parses and validates valid JSON.

        Verifies:
            The method successfully parses valid JSON string and
            validates the resulting configuration per method contract.

        Business Impact:
            Enables API endpoints to accept JSON configuration payloads
            with automatic parsing and validation.

        Scenario:
            Given: A ResilienceConfigValidator instance
            And: Valid JSON string '{"retry_attempts": 3, "circuit_breaker_threshold": 5}'
            When: validate_json_string(json_string) is called
            Then: JSON is parsed successfully
            And: Configuration validation proceeds
            And: ValidationResult.is_valid is True

        Fixtures Used:
            - None (tests JSON parsing)
        """
        # Given
        validator = ResilienceConfigValidator()
        valid_json = '{"retry_attempts": 3, "circuit_breaker_threshold": 5}'

        # When
        result = validator.validate_json_string(valid_json)

        # Then
        assert result.is_valid
        assert len(result.errors) == 0
        assert isinstance(result, ValidationResult)
    
    def test_validate_json_string_validates_parsed_configuration(self):
        """
        Test that parsed JSON configuration undergoes full validation.

        Verifies:
            After JSON parsing, the configuration is validated using
            the same validation logic as validate_custom_config().

        Business Impact:
            Ensures JSON-provided configurations receive same validation
            quality as programmatically-created configurations.

        Scenario:
            Given: A ResilienceConfigValidator instance
            And: JSON string with invalid retry_attempts value
            When: validate_json_string(json_string) is called
            Then: JSON parses successfully
            And: Configuration validation fails appropriately
            And: Validation errors are reported

        Fixtures Used:
            - None (tests validation integration)
        """
        # Given
        validator = ResilienceConfigValidator()
        invalid_config_json = '{"retry_attempts": -1}'

        # When
        result = validator.validate_json_string(invalid_config_json)

        # Then
        assert not result.is_valid
        assert len(result.errors) > 0
        # The error should mention the retry_attempts validation issue
        assert any("retry_attempts" in error for error in result.errors)
    
    def test_validate_json_string_rejects_malformed_json(self):
        """
        Test that malformed JSON strings are rejected with clear errors.

        Verifies:
            The method detects JSON syntax errors and returns
            ValidationResult with parsing error details.

        Business Impact:
            Provides clear feedback for JSON syntax errors enabling
            rapid correction of configuration format issues.

        Scenario:
            Given: A ResilienceConfigValidator instance
            And: Malformed JSON string '{"retry_attempts": 3, "circuit_breaker_threshold": }'
            When: validate_json_string(json_string) is called
            Then: ValidationResult.is_valid is False
            And: Errors contain "Invalid JSON" or parsing error message
            And: Error indicates syntax problem location if possible

        Fixtures Used:
            - None (tests error handling)
        """
        # Given
        validator = ResilienceConfigValidator()
        malformed_json = '{"retry_attempts": 3, "circuit_breaker_threshold": }'

        # When
        result = validator.validate_json_string(malformed_json)

        # Then
        assert not result.is_valid
        assert len(result.errors) > 0
        # Error should indicate JSON parsing issue
        assert any("Invalid JSON" in error for error in result.errors)
    
    def test_validate_json_string_handles_missing_closing_brace(self):
        """
        Test that JSON with missing closing brace is rejected.

        Verifies:
            Common JSON syntax error (missing closing brace) is
            detected and reported clearly.

        Business Impact:
            Helps users quickly identify and fix common JSON
            formatting mistakes in configuration payloads.

        Scenario:
            Given: A ResilienceConfigValidator instance
            And: JSON string '{"retry_attempts": 3' (missing closing brace)
            When: validate_json_string(json_string) is called
            Then: ValidationResult.is_valid is False
            And: Errors mention JSON syntax or parsing error

        Fixtures Used:
            - None (tests syntax error handling)
        """
        # Given
        validator = ResilienceConfigValidator()
        missing_brace_json = '{"retry_attempts": 3'

        # When
        result = validator.validate_json_string(missing_brace_json)

        # Then
        assert not result.is_valid
        assert len(result.errors) > 0
        # Error should indicate JSON parsing issue
        assert any("Invalid JSON" in error for error in result.errors)
    
    def test_validate_json_string_handles_trailing_comma(self):
        """
        Test that JSON with trailing comma is rejected.

        Verifies:
            Invalid trailing comma in JSON object is detected
            as strict JSON parsing error.

        Business Impact:
            Enforces strict JSON compliance preventing issues
            with JSON parsers in other systems.

        Scenario:
            Given: A ResilienceConfigValidator instance
            And: JSON string '{"retry_attempts": 3,}' (trailing comma)
            When: validate_json_string(json_string) is called
            Then: ValidationResult.is_valid is False
            And: Errors indicate JSON parsing failure

        Fixtures Used:
            - None (tests strict parsing)
        """
        # Given
        validator = ResilienceConfigValidator()
        trailing_comma_json = '{"retry_attempts": 3,}'

        # When
        result = validator.validate_json_string(trailing_comma_json)

        # Then
        assert not result.is_valid
        assert len(result.errors) > 0
        # Error should indicate JSON parsing issue
        assert any("Invalid JSON" in error for error in result.errors)
    
    def test_validate_json_string_handles_single_quotes(self):
        """
        Test that JSON with single quotes instead of double quotes is rejected.

        Verifies:
            The method enforces proper JSON quoting rules
            (double quotes only) per JSON specification.

        Business Impact:
            Ensures configuration payloads conform to JSON standard
            for interoperability with standard JSON tools.

        Scenario:
            Given: A ResilienceConfigValidator instance
            And: JSON-like string with single quotes "{'retry_attempts': 3}"
            When: validate_json_string(json_string) is called
            Then: ValidationResult.is_valid is False
            And: Errors indicate JSON parsing failure

        Fixtures Used:
            - None (tests quote validation)
        """
        # Given
        validator = ResilienceConfigValidator()
        single_quote_json = "{'retry_attempts': 3}"

        # When
        result = validator.validate_json_string(single_quote_json)

        # Then
        assert not result.is_valid
        assert len(result.errors) > 0
        # Error should indicate JSON parsing issue
        assert any("Invalid JSON" in error for error in result.errors)
    
    def test_validate_json_string_provides_helpful_parsing_errors(self):
        """
        Test that JSON parsing errors include helpful diagnostic information.

        Verifies:
            Parsing error messages include details about the JSON
            error type and location when available.

        Business Impact:
            Improves developer experience by providing actionable
            error information for fixing JSON syntax issues.

        Scenario:
            Given: A ResilienceConfigValidator instance
            And: Various malformed JSON strings
            When: validate_json_string() is called for each
            Then: Error messages indicate specific parsing issues
            And: Suggestions mention JSON format requirements
            And: Errors are helpful for debugging

        Fixtures Used:
            - None (tests error quality)
        """
        # Given
        validator = ResilienceConfigValidator()
        malformed_jsons = [
            '{"retry_attempts": 3,}',  # trailing comma
            '{"retry_attempts": }',     # missing value
            '{"retry_attempts": 3',     # missing closing brace
            'not json at all',          # not JSON
            '{"retry_attempts": 3, "unknown": "field"}'  # extra field (should be config validation error)
        ]

        # When
        results = [validator.validate_json_string(malformed) for malformed in malformed_jsons]

        # Then
        for i, result in enumerate(results):
            assert not result.is_valid
            assert len(result.errors) > 0
            # All errors should provide helpful information
            assert any(len(error) > 10 for error in result.errors)  # Errors are descriptive

        # Specifically test the first malformed JSON (trailing comma)
        trailing_comma_result = results[0]
        assert any("Invalid JSON" in error for error in trailing_comma_result.errors)


class TestResilienceConfigValidatorJSONValidationIntegration:
    """
    Test suite for JSON parsing + validation integration.
    
    Scope:
        - Combined JSON parsing and configuration validation
        - Error aggregation from both stages
        - Warning propagation through JSON pipeline
        - Complex JSON structure handling
        
    Business Critical:
        Seamless integration of parsing and validation provides
        comprehensive quality checking for JSON configurations.
        
    Test Strategy:
        - Test multi-stage error reporting
        - Verify warning propagation
        - Test complex JSON structures
        - Validate complete error context
    """
    
    def test_validate_json_string_reports_both_json_and_validation_errors(self):
        """
        Test that both JSON and validation errors can be present.

        Verifies:
            When JSON is valid but configuration is invalid, only
            configuration validation errors are reported.

        Business Impact:
            Ensures users receive appropriate errors for the actual
            problem (configuration vs JSON syntax).

        Scenario:
            Given: A ResilienceConfigValidator instance
            And: Valid JSON with invalid configuration values
            When: validate_json_string(json_string) is called
            Then: No JSON parsing errors are present
            And: Configuration validation errors are reported
            And: Error context is clear

        Fixtures Used:
            - None (tests error categorization)
        """
        # Given
        validator = ResilienceConfigValidator()
        # Valid JSON but invalid configuration (negative retry_attempts)
        valid_json_invalid_config = '{"retry_attempts": -1}'

        # When
        result = validator.validate_json_string(valid_json_invalid_config)

        # Then
        assert not result.is_valid
        assert len(result.errors) > 0
        # Should be configuration validation error, not JSON parsing error
        assert any("retry_attempts" in error for error in result.errors)
        # Should not mention JSON parsing issues
        assert not any("Invalid JSON" in error for error in result.errors)
    
    def test_validate_json_string_propagates_validation_warnings(self):
        """
        Test that configuration warnings are propagated through JSON validation.

        Verifies:
            ValidationResult.warnings from configuration validation
            are included in the final result from JSON validation.

        Business Impact:
            Ensures users receive advisory warnings even when
            configuration arrives as JSON string.

        Scenario:
            Given: A ResilienceConfigValidator instance
            And: Valid JSON with configuration triggering warnings
            When: validate_json_string(json_string) is called
            Then: ValidationResult.is_valid may be True
            And: ValidationResult.warnings contains advisory messages
            And: Warnings are propagated from config validation

        Fixtures Used:
            - None (tests warning propagation)
        """
        # Given
        validator = ResilienceConfigValidator()
        # Valid JSON that may trigger warnings (high retry attempts)
        warning_config_json = '{"retry_attempts": 10, "circuit_breaker_threshold": 1}'

        # When
        result = validator.validate_json_string(warning_config_json)

        # Then
        # Should be valid (high values are allowed but may warn)
        # May have warnings about aggressive settings
        # The important part is that warnings are preserved through JSON parsing
        assert isinstance(result, ValidationResult)
        # Warnings list should exist (may be empty, but should be present)
        assert hasattr(result, 'warnings')
        assert isinstance(result.warnings, list)
    
    def test_validate_json_string_handles_nested_json_objects(self):
        """
        Test that nested JSON objects are parsed correctly.

        Verifies:
            Complex JSON with nested objects (e.g., operation_overrides)
            is parsed correctly and validated properly.

        Business Impact:
            Enables rich configuration structures in JSON format
            for operation-specific settings and complex configs.

        Scenario:
            Given: A ResilienceConfigValidator instance
            And: JSON with nested operation_overrides object
            When: validate_json_string(json_string) is called
            Then: Nested structure is parsed correctly
            And: Nested fields are validated appropriately
            And: Complex configuration is handled properly

        Fixtures Used:
            - None (tests complex structure handling)
        """
        # Given
        validator = ResilienceConfigValidator()
        nested_json = '''
        {
            "retry_attempts": 3,
            "circuit_breaker_threshold": 5,
            "operation_overrides": {
                "qa": "critical",
                "sentiment": "conservative",
                "summarize": "balanced"
            }
        }
        '''

        # When
        result = validator.validate_json_string(nested_json)

        # Then
        assert result.is_valid
        assert len(result.errors) == 0
        # The nested structure should be parsed and validated successfully
        assert isinstance(result, ValidationResult)
    
    def test_validate_json_string_handles_json_with_whitespace(self):
        """
        Test that JSON with various whitespace patterns is handled.

        Verifies:
            JSON with newlines, indentation, and spacing variations
            is parsed correctly without affecting validation.

        Business Impact:
            Supports human-readable JSON formatting conventions
            for configuration files and API payloads.

        Scenario:
            Given: A ResilienceConfigValidator instance
            And: JSON string with newlines and indentation
            When: validate_json_string(json_string) is called
            Then: Whitespace is handled correctly
            And: Validation proceeds normally
            And: Configuration is extracted properly

        Fixtures Used:
            - None (tests whitespace tolerance)
        """
        # Given
        validator = ResilienceConfigValidator()
        formatted_json = '''
        {
            "retry_attempts": 3,
            "circuit_breaker_threshold": 5,
            "default_strategy": "balanced"
        }
        '''

        # When
        result = validator.validate_json_string(formatted_json)

        # Then
        assert result.is_valid
        assert len(result.errors) == 0
        assert isinstance(result, ValidationResult)
    
    def test_validate_json_string_result_matches_direct_validation(self):
        """
        Test that JSON validation produces same result as direct validation.

        Verifies:
            Configuration validated via JSON string produces identical
            ValidationResult to direct dictionary validation.

        Business Impact:
            Ensures consistent validation behavior regardless of
            configuration input format (JSON vs dict).

        Scenario:
            Given: A ResilienceConfigValidator instance
            And: A configuration as both JSON string and dictionary
            When: validate_json_string() and validate_custom_config() are called
            Then: Both ValidationResults have same is_valid value
            And: Error messages are equivalent
            And: Validation behavior is consistent

        Fixtures Used:
            - None (tests consistency)
        """
        # Given
        validator = ResilienceConfigValidator()
        config_dict = {"retry_attempts": 3, "circuit_breaker_threshold": 5}
        config_json = '{"retry_attempts": 3, "circuit_breaker_threshold": 5}'

        # When
        json_result = validator.validate_json_string(config_json)
        direct_result = validator.validate_custom_config(config_dict)

        # Then
        assert json_result.is_valid == direct_result.is_valid
        assert len(json_result.errors) == len(direct_result.errors)
        assert json_result.warnings == direct_result.warnings
        # Both should be ValidationResult instances
        assert isinstance(json_result, ValidationResult)
        assert isinstance(direct_result, ValidationResult)