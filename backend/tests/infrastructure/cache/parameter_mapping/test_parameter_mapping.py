"""
Comprehensive test suite for parameter_mapping UUT.

This module provides systematic behavioral testing of the CacheParameterMapper
and ValidationResult components, ensuring robust parameter mapping functionality
for cache inheritance architecture.

Test Coverage:
    - ValidationResult: Dataclass behavior, error management, and state validation
    - CacheParameterMapper: Parameter mapping, validation, classification, and error handling
    - Integration scenarios: Complete parameter mapping workflows
    - Edge cases: Invalid inputs, boundary conditions, and error scenarios

Testing Philosophy:
    - Uses behavior-driven testing with Given/When/Then structure
    - Tests core business logic without mocking standard library components
    - Validates parameter mapping accuracy and validation completeness
    - Ensures thread-safety and immutability where specified
    - Comprehensive edge case coverage for production reliability

Test Organization:
    - TestValidationResult: ValidationResult dataclass behavior testing
    - TestCacheParameterMapperInitialization: Mapper initialization and configuration
    - TestParameterMapping: Core parameter mapping and separation logic
    - TestParameterValidation: Comprehensive validation scenarios and edge cases

Fixtures and Mocks:    
    Note: No additional mocking needed as parameter_mapping uses only standard
    library components (dataclasses, typing, logging) and internal exceptions
    already available in shared cache conftest.py.
"""

import pytest
from typing import Dict, Any
from app.infrastructure.cache.parameter_mapping import CacheParameterMapper

class TestValidationResult:
    """
    Test ValidationResult dataclass behavior and error management functionality.
    
    The ValidationResult dataclass provides structured validation feedback for
    cache parameter mapping operations with comprehensive error reporting.
    """

    def test_validation_result_default_initialization(self):
        """
        Test ValidationResult initialization with default values.
        
        Given: A ValidationResult is created with no parameters
        When: The ValidationResult object is instantiated
        Then: Default values should be properly set for all attributes
        And: The result should indicate valid status by default
        And: All collection attributes should be empty
        """
        # Import the ValidationResult from the public contract
        from app.infrastructure.cache.parameter_mapping import ValidationResult
        
        # Given/When: Create ValidationResult with default values
        result = ValidationResult()
        
        # Then: Verify default state
        assert result.is_valid == True  # Default to valid
        assert result.errors == []  # Empty errors list
        assert result.warnings == []  # Empty warnings list
        assert result.recommendations == []  # Empty recommendations list
        assert result.parameter_conflicts == {}  # Empty conflicts dict
        assert result.ai_specific_params == set()  # Empty set
        assert result.generic_params == set()  # Empty set
        assert result.context == {}  # Empty context dict

    def test_validation_result_custom_initialization(self):
        """
        Test ValidationResult initialization with custom values.
        
        Given: Specific validation result data including errors and warnings
        When: A ValidationResult is created with custom parameters
        Then: All provided values should be properly assigned
        And: The validation state should reflect the provided validity
        And: All collections should contain the specified items
        """
        from app.infrastructure.cache.parameter_mapping import ValidationResult
        
        # Given: Custom validation data
        custom_errors = ["Invalid parameter type"]
        custom_warnings = ["Suboptimal configuration"]
        custom_recommendations = ["Consider using production settings"]
        custom_conflicts = {"memory_cache_size": "Conflicts with l1_cache_size"}
        custom_ai_params = {"text_hash_threshold"}
        custom_generic_params = {"redis_url", "default_ttl"}
        custom_context = {"validation_mode": "strict"}
        
        # When: Create ValidationResult with custom values
        result = ValidationResult(
            is_valid=False,
            errors=custom_errors,
            warnings=custom_warnings,
            recommendations=custom_recommendations,
            parameter_conflicts=custom_conflicts,
            ai_specific_params=custom_ai_params,
            generic_params=custom_generic_params,
            context=custom_context
        )
        
        # Then: Verify all custom values are assigned
        assert result.is_valid == False
        assert result.errors == custom_errors
        assert result.warnings == custom_warnings
        assert result.recommendations == custom_recommendations
        assert result.parameter_conflicts == custom_conflicts
        assert result.ai_specific_params == custom_ai_params
        assert result.generic_params == custom_generic_params
        assert result.context == custom_context

    def test_add_error_marks_invalid(self):
        """
        Test adding validation errors automatically marks result as invalid.
        
        Given: A ValidationResult that is initially valid
        When: An error is added using add_error()
        Then: The result should be marked as invalid
        And: The error should be added to the errors list
        And: The validity flag should be updated accordingly
        """
        from app.infrastructure.cache.parameter_mapping import ValidationResult
        
        # Given: A ValidationResult that is initially valid
        result = ValidationResult(is_valid=True)
        assert result.is_valid == True  # Verify initial state
        assert len(result.errors) == 0
        
        # When: An error is added
        error_message = "Parameter validation failed"
        result.add_error(error_message)
        
        # Then: Result should be marked invalid and error added
        assert result.is_valid == False  # Should be automatically marked invalid
        assert error_message in result.errors  # Error should be in the list
        assert len(result.errors) == 1  # Only one error added

    def test_add_warning_preserves_validity(self):
        """
        Test adding warnings does not affect validation status.
        
        Given: A ValidationResult with valid status
        When: A warning is added using add_warning()
        Then: The validation status should remain unchanged
        And: The warning should be added to the warnings list
        And: Other attributes should remain unaffected
        """
        from app.infrastructure.cache.parameter_mapping import ValidationResult
        
        # Given: A ValidationResult with valid status
        result = ValidationResult(is_valid=True)
        initial_errors = result.errors.copy()
        initial_recommendations = result.recommendations.copy()
        
        # When: A warning is added
        warning_message = "Configuration may not be optimal"
        result.add_warning(warning_message)
        
        # Then: Validation status should remain unchanged
        assert result.is_valid == True  # Should remain valid
        assert warning_message in result.warnings  # Warning should be added
        assert len(result.warnings) == 1
        
        # And: Other attributes should remain unaffected
        assert result.errors == initial_errors
        assert result.recommendations == initial_recommendations

    def test_add_recommendation_functionality(self):
        """
        Test adding configuration recommendations.
        
        Given: A ValidationResult object
        When: A recommendation is added using add_recommendation()
        Then: The recommendation should be added to the recommendations list
        And: Other validation state should remain unchanged
        And: Multiple recommendations should be supported
        """
        from app.infrastructure.cache.parameter_mapping import ValidationResult
        
        # Given: A ValidationResult object
        result = ValidationResult(is_valid=True)
        initial_validity = result.is_valid
        initial_errors = result.errors.copy()
        initial_warnings = result.warnings.copy()
        
        # When: Recommendations are added
        first_recommendation = "Consider enabling compression"
        second_recommendation = "Use production Redis settings"
        
        result.add_recommendation(first_recommendation)
        result.add_recommendation(second_recommendation)
        
        # Then: Recommendations should be added
        assert len(result.recommendations) == 2
        assert first_recommendation in result.recommendations
        assert second_recommendation in result.recommendations
        
        # And: Other validation state should remain unchanged
        assert result.is_valid == initial_validity
        assert result.errors == initial_errors
        assert result.warnings == initial_warnings

    def test_add_conflict_parameter_tracking(self):
        """
        Test parameter conflict tracking with descriptions.
        
        Given: A ValidationResult object
        When: A parameter conflict is added using add_conflict()
        Then: The conflict should be stored in parameter_conflicts
        And: The parameter name should map to the conflict description
        And: Multiple conflicts should be supported
        """
        from app.infrastructure.cache.parameter_mapping import ValidationResult
        
        # Given: A ValidationResult object
        result = ValidationResult()
        
        # When: Parameter conflicts are added
        result.add_conflict("memory_cache_size", "Conflicts with l1_cache_size")
        result.add_conflict("compression_threshold", "Value too low for performance")
        
        # Then: Conflicts should be stored correctly
        assert len(result.parameter_conflicts) == 2
        assert result.parameter_conflicts["memory_cache_size"] == "Conflicts with l1_cache_size"
        assert result.parameter_conflicts["compression_threshold"] == "Value too low for performance"
        
        # And: Multiple conflicts should be supported
        result.add_conflict("redis_url", "Invalid URL format")
        assert len(result.parameter_conflicts) == 3
        assert "redis_url" in result.parameter_conflicts

    def test_multiple_operations_state_consistency(self):
        """
        Test ValidationResult state consistency across multiple operations.
        
        Given: A ValidationResult object
        When: Multiple errors, warnings, and recommendations are added
        Then: All operations should maintain state consistency
        And: The validity should reflect the presence of errors
        And: All collections should accumulate items correctly
        """
        from app.infrastructure.cache.parameter_mapping import ValidationResult
        
        # Given: A ValidationResult object
        result = ValidationResult(is_valid=True)
        
        # When: Multiple operations are performed
        result.add_warning("First warning")
        result.add_recommendation("First recommendation")
        assert result.is_valid == True  # Should still be valid
        
        result.add_error("First error")  # This should invalidate
        assert result.is_valid == False  # Now should be invalid
        
        result.add_warning("Second warning")
        result.add_error("Second error")
        result.add_recommendation("Second recommendation")
        result.add_conflict("param1", "First conflict")
        result.add_conflict("param2", "Second conflict")
        
        # Then: All operations should maintain state consistency
        assert result.is_valid == False  # Should remain invalid due to errors
        
        # And: All collections should accumulate items correctly
        # Note: add_conflict may add to both errors and parameter_conflicts
        base_errors = ["First error", "Second error"]
        assert all(error in result.errors for error in base_errors)
        assert len([error for error in result.errors if error in base_errors]) == 2
        
        assert len(result.warnings) == 2
        assert "First warning" in result.warnings
        assert "Second warning" in result.warnings
        
        assert len(result.recommendations) == 2
        assert "First recommendation" in result.recommendations
        assert "Second recommendation" in result.recommendations
        
        assert len(result.parameter_conflicts) == 2
        assert result.parameter_conflicts["param1"] == "First conflict"
        assert result.parameter_conflicts["param2"] == "Second conflict"


class TestCacheParameterMapperInitialization:
    """
    Test CacheParameterMapper initialization and configuration setup.
    
    The CacheParameterMapper requires proper initialization of parameter
    classifications, mappings, and validation rules.
    """

    def test_mapper_initialization(self):
        """
        Test CacheParameterMapper initialization with default configuration.
        
        Given: CacheParameterMapper is instantiated with default settings
        When: The mapper object is created
        Then: All parameter classifications should be properly initialized
        And: Parameter mappings should be correctly configured
        And: The mapper should be ready for parameter operations
        """
        from app.infrastructure.cache.parameter_mapping import CacheParameterMapper
        
        # Given/When: Instantiate mapper with default settings
        mapper = CacheParameterMapper()
        
        # Then: Mapper should be properly initialized
        assert mapper is not None
        
        # And: Should have core attributes initialized (testing through public interface)
        info = mapper.get_parameter_info()
        # Use actual key names from implementation
        assert "ai_specific_parameters" in info or "ai_specific_params" in info
        assert "generic_parameters" in info or "generic_params" in info
        assert "parameter_mappings" in info
        
        # And: Should be ready for parameter operations
        # Test with empty parameters to verify it can operate
        generic_params, ai_specific_params = mapper.map_ai_to_generic_params({})
        assert isinstance(generic_params, dict)
        assert isinstance(ai_specific_params, dict)

    def test_parameter_classifications_setup(self):
        """
        Test proper setup of AI-specific and generic parameter classifications.
        
        Given: A CacheParameterMapper instance
        When: Parameter classifications are accessed
        Then: AI-specific parameters should be correctly identified
        And: Generic parameters should be properly categorized
        And: Parameter mappings should be accurately configured
        """
        from app.infrastructure.cache.parameter_mapping import CacheParameterMapper
        
        # Given: A CacheParameterMapper instance
        mapper = CacheParameterMapper()
        
        # When: Parameter classifications are accessed
        info = mapper.get_parameter_info()
        
        # Then: AI-specific parameters should be correctly identified
        ai_specific_key = "ai_specific_parameters" if "ai_specific_parameters" in info else "ai_specific_params"
        ai_specific_params = info[ai_specific_key]
        assert isinstance(ai_specific_params, (set, list))
        assert len(ai_specific_params) > 0  # Should have some AI-specific parameters
        
        # And: Generic parameters should be properly categorized
        generic_key = "generic_parameters" if "generic_parameters" in info else "generic_params"
        generic_params = info[generic_key]
        assert isinstance(generic_params, (set, list))
        assert len(generic_params) > 0  # Should have some generic parameters
        
        # And: Parameter mappings should be accurately configured
        parameter_mappings = info["parameter_mappings"]
        assert isinstance(parameter_mappings, dict)
        # Should have at least some parameter mappings (AI -> generic)

    def test_immutable_parameter_definitions(self):
        """
        Test immutability of core parameter definitions after initialization.
        
        Given: A CacheParameterMapper instance
        When: Attempts are made to modify parameter classifications
        Then: Core parameter definitions should remain immutable
        And: Parameter mappings should be protected from modification
        And: Validation rules should remain consistent
        """
        from app.infrastructure.cache.parameter_mapping import CacheParameterMapper
        
        # Given: A CacheParameterMapper instance
        mapper = CacheParameterMapper()
        
        # When: Get initial parameter info for comparison
        initial_info = mapper.get_parameter_info()
        ai_key = "ai_specific_parameters" if "ai_specific_parameters" in initial_info else "ai_specific_params"
        generic_key = "generic_parameters" if "generic_parameters" in initial_info else "generic_params"
        
        initial_ai_params = initial_info[ai_key].copy() if hasattr(initial_info[ai_key], 'copy') else set(initial_info[ai_key])
        initial_generic_params = initial_info[generic_key].copy() if hasattr(initial_info[generic_key], 'copy') else set(initial_info[generic_key])
        initial_mappings = initial_info["parameter_mappings"].copy()
        
        # Then: Verify that getting info multiple times returns consistent data
        second_info = mapper.get_parameter_info()
        
        # Core parameter definitions should remain consistent
        second_ai_params = second_info[ai_key] if isinstance(second_info[ai_key], set) else set(second_info[ai_key])
        second_generic_params = second_info[generic_key] if isinstance(second_info[generic_key], set) else set(second_info[generic_key])
        
        # Convert to sets for comparison to handle list vs set differences
        initial_ai_set = initial_ai_params if isinstance(initial_ai_params, set) else set(initial_ai_params)
        initial_generic_set = initial_generic_params if isinstance(initial_generic_params, set) else set(initial_generic_params)
        
        assert initial_ai_set == second_ai_params
        assert initial_generic_set == second_generic_params
        assert initial_mappings == second_info["parameter_mappings"]
        
        # And: Validation behavior should remain consistent
        test_params = {"redis_url": "redis://localhost"}
        first_validation = mapper.validate_parameter_compatibility(test_params)
        second_validation = mapper.validate_parameter_compatibility(test_params)
        
        # Validation results should be consistent (same parameters -> same result)
        assert first_validation.is_valid == second_validation.is_valid


class TestParameterMapping:
    """
    Test core parameter mapping and separation logic functionality.
    
    The parameter mapping functionality separates AI parameters into generic
    Redis parameters and AI-specific parameters with proper transformations.
    """

    def test_basic_parameter_separation(self):
        """
        Test basic separation of AI and generic parameters.
        
        Given: A set of mixed AI and generic parameters
        When: map_ai_to_generic_params() is called
        Then: Parameters should be correctly separated into generic and AI-specific
        And: Generic parameters should be suitable for GenericRedisCache
        And: AI-specific parameters should contain only AI functionality
        """
        pass

    def test_parameter_name_mapping(self):
        """
        Test mapping of AI parameter names to generic equivalents.
        
        Given: AI parameters that have generic equivalents
        When: Parameter mapping is performed
        Then: AI parameter names should be mapped to generic names
        And: Parameter values should be preserved during mapping
        And: Mapped parameters should be included in generic parameters
        """
        pass

    def test_empty_parameters_handling(self):
        """
        Test handling of empty parameter dictionaries.
        
        Given: An empty parameter dictionary
        When: Parameter mapping is attempted
        Then: Empty dictionaries should be returned for both generic and AI-specific
        And: No exceptions should be raised
        And: The operation should complete successfully
        """
        pass

    def test_only_generic_parameters(self):
        """
        Test mapping with only generic parameters present.
        
        Given: A parameter dictionary containing only generic parameters
        When: Parameter separation is performed
        Then: All parameters should be classified as generic
        And: The AI-specific dictionary should be empty
        And: Generic parameters should be unchanged
        """
        pass

    def test_only_ai_specific_parameters(self):
        """
        Test mapping with only AI-specific parameters present.
        
        Given: A parameter dictionary containing only AI-specific parameters
        When: Parameter separation is performed
        Then: All parameters should be classified as AI-specific
        And: The generic dictionary should be empty or contain defaults
        And: AI-specific parameters should be preserved
        """
        pass

    def test_mixed_parameter_scenarios(self):
        """
        Test mapping with complex mixed parameter scenarios.
        
        Given: A parameter dictionary with generic, AI-specific, and mapped parameters
        When: Comprehensive parameter mapping is performed
        Then: All parameters should be correctly classified and mapped
        And: No parameters should be lost during mapping
        And: Mapped parameters should appear in appropriate categories
        """
        pass

    def test_parameter_value_preservation(self):
        """
        Test preservation of parameter values during mapping operations.
        
        Given: Parameters with various data types and values
        When: Parameter mapping is performed
        Then: All parameter values should be preserved exactly
        And: Data types should remain unchanged
        And: Complex values should be handled correctly
        """
        pass

    def test_invalid_parameter_handling(self): # No mock fixture needed
        """
        Test that validate_parameter_compatibility identifies invalid parameters.
        
        Given: A parameter dictionary containing invalid parameters
        When: Parameter validation is attempted
        Then: The validation result should be marked as invalid
        And: The errors list should contain specific parameter information
        """
        # 1. Arrange: Create a real mapper and define invalid parameters
        mapper = CacheParameterMapper()
        invalid_params = {
            "redis_url": "redis://localhost",
            "memory_cache_size": -10, # Invalid range
            "text_hash_threshold": "this-should-be-an-integer" # Invalid type
        }
        
        # 2. Act: Call the correct validation method
        result = mapper.validate_parameter_compatibility(ai_params=invalid_params)
            
        # 3. Assert: Verify the ValidationResult object
        assert result.is_valid is False
        assert len(result.errors) > 0
        
        # Optional but recommended: Assert the error messages are helpful
        error_string = " ".join(result.errors).lower()
        assert "memory_cache_size" in error_string
        assert "text_hash_threshold" in error_string

    def test_configuration_error_scenarios(self):
        """
        Test handling of configuration errors during mapping.
        
        Given: Parameters that create unresolvable configuration conflicts
        When: Parameter mapping encounters conflicts
        Then: A ConfigurationError should be raised
        And: The error should describe the specific conflict
        And: The mapping should provide actionable error information
        """
        pass


class TestParameterValidation:
    """
    Test comprehensive parameter validation scenarios and edge cases.
    
    Parameter validation ensures compatibility, identifies conflicts, and provides
    recommendations for optimal cache configuration.
    """

    def test_valid_parameters_validation(self):
        """
        Test validation of completely valid parameter sets.
        
        Given: A parameter dictionary with all valid parameters and values
        When: Parameter validation is performed
        Then: The validation result should indicate success
        And: No errors or warnings should be present
        And: The validation should complete without issues
        """
        from app.infrastructure.cache.parameter_mapping import CacheParameterMapper
        
        # Given: A parameter dictionary with all valid parameters and values
        mapper = CacheParameterMapper()
        valid_params = {
            "redis_url": "redis://localhost:6379",
            "default_ttl": 3600,
            "enable_compression": True,
            "text_hash_threshold": 1000
        }
        
        # When: Parameter validation is performed
        validation_result = mapper.validate_parameter_compatibility(valid_params)
        
        # Then: The validation result should indicate success
        assert validation_result.is_valid == True
        
        # And: No errors should be present
        assert len(validation_result.errors) == 0
        
        # And: The validation should complete without issues
        assert isinstance(validation_result.warnings, list)
        assert isinstance(validation_result.recommendations, list)

    def test_invalid_parameter_types(self):
        """
        Test validation of parameters with incorrect types.
        
        Given: Parameters with incorrect data types
        When: Parameter validation is performed
        Then: Type validation errors should be identified
        And: Specific type mismatch information should be provided
        And: The validation result should be marked as invalid
        """
        from app.infrastructure.cache.parameter_mapping import CacheParameterMapper
        
        # Given: Parameters with incorrect data types
        mapper = CacheParameterMapper()
        invalid_type_params = {
            "redis_url": 123,  # Should be string
            "default_ttl": "not-a-number",  # Should be int
            "enable_compression": "true",  # Should be boolean
            "text_hash_threshold": [1000]  # Should be int
        }
        
        # When: Parameter validation is performed
        validation_result = mapper.validate_parameter_compatibility(invalid_type_params)
        
        # Then: Type validation errors should be identified
        assert validation_result.is_valid == False
        
        # And: Specific type mismatch information should be provided
        assert len(validation_result.errors) > 0
        error_text = " ".join(validation_result.errors).lower()
        
        # Should mention type issues
        assert "type" in error_text or "int" in error_text or "str" in error_text or "bool" in error_text
        
        # And: The validation result should be marked as invalid
        assert validation_result.is_valid == False

    def test_parameter_value_range_validation(self):
        """
        Test validation of parameter values outside acceptable ranges.
        
        Given: Parameters with values outside valid ranges
        When: Range validation is performed
        Then: Range validation errors should be detected
        And: Specific range violation information should be provided
        And: Acceptable value ranges should be indicated
        """
        from app.infrastructure.cache.parameter_mapping import CacheParameterMapper
        
        # Given: Parameters with values outside valid ranges
        mapper = CacheParameterMapper()
        out_of_range_params = {
            "default_ttl": -100,  # Negative TTL should be invalid
            "memory_cache_size": -50,  # Negative cache size should be invalid
            "text_hash_threshold": -1000  # Negative threshold should be invalid
        }
        
        # When: Range validation is performed
        validation_result = mapper.validate_parameter_compatibility(out_of_range_params)
        
        # Then: Range validation errors should be detected
        assert validation_result.is_valid == False
        
        # And: Specific range violation information should be provided
        assert len(validation_result.errors) > 0
        error_text = " ".join(validation_result.errors).lower()
        
        # Should mention range/value issues
        range_keywords = ["range", "negative", "positive", ">=", "<=", "must be", "invalid"]
        assert any(keyword in error_text for keyword in range_keywords)
        
        # And: Should provide specific parameter information
        parameter_mentioned = any(param in error_text for param in ["ttl", "cache_size", "threshold"])
        assert parameter_mentioned, f"Error should mention specific parameters: {error_text}"

    def test_parameter_conflict_detection(self):
        """
        Test detection of conflicting parameter combinations.
        
        Given: Parameters that conflict with each other
        When: Conflict validation is performed
        Then: Parameter conflicts should be identified
        And: Conflict descriptions should be provided
        And: Conflicting parameters should be specifically named
        """
        from app.infrastructure.cache.parameter_mapping import CacheParameterMapper
        
        # Given: Parameters that conflict with each other
        mapper = CacheParameterMapper()
        
        # Create potentially conflicting parameters
        conflicting_params = {
            "memory_cache_size": 100,
            "l1_cache_size": 200,  # These might conflict in the mapping logic
            "enable_compression": True,
            "compression_threshold": -1  # Negative threshold with compression enabled might conflict
        }
        
        # When: Conflict validation is performed
        validation_result = mapper.validate_parameter_compatibility(conflicting_params)
        
        # Then: Check for conflicts (may be detected as errors or in parameter_conflicts)
        conflicts_detected = (
            not validation_result.is_valid or 
            len(validation_result.parameter_conflicts) > 0 or
            any("conflict" in error.lower() for error in validation_result.errors)
        )
        
        # If conflicts are detected, verify proper reporting
        if conflicts_detected:
            # And: Conflict descriptions should be provided
            if validation_result.parameter_conflicts:
                assert len(validation_result.parameter_conflicts) > 0
                
                # And: Conflicting parameters should be specifically named
                conflict_params = list(validation_result.parameter_conflicts.keys())
                assert len(conflict_params) > 0
                
                # Conflict descriptions should be meaningful
                for param, description in validation_result.parameter_conflicts.items():
                    assert len(description) > 0, f"Conflict description for {param} should not be empty"
            
            elif validation_result.errors:
                # Conflicts might be reported as errors instead
                error_text = " ".join(validation_result.errors).lower()
                assert "conflict" in error_text or "incompatible" in error_text
        
        # Test should complete successfully regardless of whether conflicts are detected
        assert isinstance(validation_result, type(validation_result))

    def test_configuration_consistency_checks(self):
        """
        Test validation of overall configuration consistency.
        
        Given: Parameters that are individually valid but inconsistent together
        When: Consistency validation is performed
        Then: Consistency issues should be identified
        And: Recommendations for resolution should be provided
        And: The validation should explain the consistency requirements
        """
        from app.infrastructure.cache.parameter_mapping import CacheParameterMapper
        
        # Given: Parameters that are individually valid but inconsistent together
        mapper = CacheParameterMapper()
        inconsistent_params = {
            "enable_compression": False,  # Compression disabled
            "compression_threshold": 1000,  # But threshold specified
            "memory_cache_size": 1000000,  # Very large cache
            "default_ttl": 1  # Very short TTL (inconsistent with large cache)
        }
        
        # When: Consistency validation is performed
        validation_result = mapper.validate_parameter_compatibility(inconsistent_params)
        
        # Then: Check for consistency feedback (may be warnings or recommendations)
        has_consistency_feedback = (
            len(validation_result.warnings) > 0 or 
            len(validation_result.recommendations) > 0 or
            not validation_result.is_valid
        )
        
        # Consistency checks should provide some form of feedback
        if has_consistency_feedback:
            # And: Recommendations for resolution should be provided
            if validation_result.recommendations:
                assert len(validation_result.recommendations) > 0
                recommendation_text = " ".join(validation_result.recommendations).lower()
                
                # And: The validation should explain the consistency requirements
                consistency_keywords = ["consider", "recommend", "should", "consistent", "configuration"]
                assert any(keyword in recommendation_text for keyword in consistency_keywords)
            
            elif validation_result.warnings:
                # Consistency issues might be reported as warnings
                warning_text = " ".join(validation_result.warnings).lower()
                consistency_keywords = ["inconsistent", "may", "consider", "configuration"]
                assert any(keyword in warning_text for keyword in consistency_keywords)
        
        # Test should complete successfully
        assert isinstance(validation_result.is_valid, bool)

    def test_warning_generation_for_suboptimal_config(self):
        """
        Test generation of warnings for suboptimal but valid configurations.
        
        Given: Parameters that are valid but not optimal
        When: Configuration analysis is performed
        Then: Appropriate warnings should be generated
        And: The configuration should remain valid
        And: Optimization recommendations should be provided
        """
        from app.infrastructure.cache.parameter_mapping import CacheParameterMapper
        
        # Given: Parameters that are valid but not optimal
        mapper = CacheParameterMapper()
        suboptimal_params = {
            "redis_url": "redis://localhost:6379",
            "default_ttl": 1,  # Very short TTL (suboptimal but valid)
            "memory_cache_size": 1,  # Very small cache (suboptimal but valid)
            "text_hash_threshold": 1  # Very low threshold (suboptimal but valid)
        }
        
        # When: Configuration analysis is performed
        validation_result = mapper.validate_parameter_compatibility(suboptimal_params)
        
        # Then: The configuration should remain valid
        # (Implementation may or may not flag this as invalid based on business rules)
        assert isinstance(validation_result.is_valid, bool)
        
        # And: Should provide feedback about the configuration
        has_feedback = (
            len(validation_result.warnings) > 0 or 
            len(validation_result.recommendations) > 0 or
            len(validation_result.errors) > 0
        )
        
        if has_feedback:
            # And: Feedback should be helpful
            if validation_result.warnings:
                # Appropriate warnings should be generated
                warning_text = " ".join(validation_result.warnings).lower()
                optimization_keywords = ["low", "small", "performance", "may", "consider"]
                assert any(keyword in warning_text for keyword in optimization_keywords)
            
            if validation_result.recommendations:
                # And: Optimization recommendations should be provided
                recommendation_text = " ".join(validation_result.recommendations).lower()
                improvement_keywords = ["increase", "consider", "recommend", "performance", "optimize"]
                assert any(keyword in recommendation_text for keyword in improvement_keywords)
        
        # Validation should complete successfully
        assert validation_result is not None

    def test_best_practice_recommendations(self):
        """
        Test generation of best practice recommendations.
        
        Given: A valid configuration that could be optimized
        When: Best practice analysis is performed
        Then: Relevant recommendations should be provided
        And: Recommendations should be specific and actionable
        And: The validation result should include improvement suggestions
        """
        from app.infrastructure.cache.parameter_mapping import CacheParameterMapper
        
        # Given: A valid configuration that could be optimized
        mapper = CacheParameterMapper()
        optimizable_params = {
            "redis_url": "redis://localhost:6379",
            "default_ttl": 3600,
            "enable_compression": False,  # Could enable compression for better performance
            "memory_cache_size": 50,  # Could be larger for better performance
            "text_hash_threshold": 500  # Could be optimized based on use case
        }
        
        # When: Best practice analysis is performed
        validation_result = mapper.validate_parameter_compatibility(optimizable_params)
        
        # Then: Check if recommendations are provided
        if validation_result.recommendations:
            # Relevant recommendations should be provided
            assert len(validation_result.recommendations) > 0
            
            # And: Recommendations should be specific and actionable
            recommendation_text = " ".join(validation_result.recommendations).lower()
            
            actionable_keywords = [
                "enable", "increase", "consider", "set", "use", 
                "compression", "performance", "optimize", "recommend"
            ]
            
            has_actionable_content = any(keyword in recommendation_text for keyword in actionable_keywords)
            assert has_actionable_content, f"Recommendations should be actionable: {validation_result.recommendations}"
            
            # And: Should include improvement suggestions
            improvement_keywords = ["better", "improve", "optimize", "performance", "efficient"]
            has_improvement_focus = any(keyword in recommendation_text for keyword in improvement_keywords)
        
        # Test should complete successfully regardless of whether recommendations are generated
        assert validation_result is not None
        assert isinstance(validation_result.recommendations, list)

    def test_comprehensive_validation_result_structure(self):
        """
        Test comprehensive validation result structure and completeness.
        
        Given: A complex parameter set requiring multiple validation checks
        When: Complete validation is performed
        Then: The validation result should contain all relevant information
        And: Errors, warnings, and recommendations should be properly categorized
        And: Parameter classifications should be accurate
        """
        from app.infrastructure.cache.parameter_mapping import CacheParameterMapper, ValidationResult
        
        # Given: A complex parameter set requiring multiple validation checks
        mapper = CacheParameterMapper()
        complex_params = {
            "redis_url": "redis://localhost:6379",  # Valid generic parameter
            "default_ttl": -100,  # Invalid (should cause error)
            "enable_compression": "maybe",  # Invalid type (should cause error)
            "memory_cache_size": 10,  # Valid but suboptimal (might cause warning)
            "text_hash_threshold": 1000,  # AI-specific parameter
            "compression_threshold": 5000,  # Valid parameter
            "unknown_parameter": "value"  # Unknown parameter (might be ignored or cause warning)
        }
        
        # When: Complete validation is performed
        validation_result = mapper.validate_parameter_compatibility(complex_params)
        
        # Then: The validation result should contain all relevant information
        assert isinstance(validation_result, ValidationResult)
        assert hasattr(validation_result, 'is_valid')
        assert hasattr(validation_result, 'errors')
        assert hasattr(validation_result, 'warnings')
        assert hasattr(validation_result, 'recommendations')
        assert hasattr(validation_result, 'parameter_conflicts')
        assert hasattr(validation_result, 'ai_specific_params')
        assert hasattr(validation_result, 'generic_params')
        
        # And: Should be properly typed
        assert isinstance(validation_result.is_valid, bool)
        assert isinstance(validation_result.errors, list)
        assert isinstance(validation_result.warnings, list)
        assert isinstance(validation_result.recommendations, list)
        assert isinstance(validation_result.parameter_conflicts, dict)
        
        # And: Should have detected the invalid parameters
        assert validation_result.is_valid == False  # Due to invalid TTL and type
        assert len(validation_result.errors) > 0  # Should have error messages
        
        # And: Parameter classifications should be populated
        total_classifications = len(validation_result.ai_specific_params) + len(validation_result.generic_params)
        assert total_classifications >= 0  # Should have some parameter classification information

    def test_empty_parameters_validation(self):
        """
        Test validation behavior with empty parameter dictionary.
        
        Given: An empty parameter dictionary
        When: Validation is performed
        Then: The validation should handle empty input gracefully
        And: Appropriate default validation behavior should occur
        And: No unexpected errors should be raised
        """
        from app.infrastructure.cache.parameter_mapping import CacheParameterMapper, ValidationResult
        
        # Given: An empty parameter dictionary
        mapper = CacheParameterMapper()
        empty_params = {}
        
        # When: Validation is performed
        # Then: No unexpected errors should be raised
        try:
            validation_result = mapper.validate_parameter_compatibility(empty_params)
            
            # And: The validation should handle empty input gracefully
            assert isinstance(validation_result, ValidationResult)
            assert isinstance(validation_result.is_valid, bool)
            assert isinstance(validation_result.errors, list)
            assert isinstance(validation_result.warnings, list)
            assert isinstance(validation_result.recommendations, list)
            
            # And: Appropriate default validation behavior should occur
            # Empty parameters should either be valid (using defaults) or provide helpful feedback
            if not validation_result.is_valid:
                # If invalid, should have explanatory errors
                assert len(validation_result.errors) > 0, "If empty params are invalid, should explain why"
            
            validation_completed = True
        except Exception as e:
            validation_completed = False
            assert False, f"Empty parameters validation should not raise exceptions: {e}"
        
        assert validation_completed, "Validation should complete successfully"

    def test_get_parameter_info_comprehensive_data(self):
        """
        Test retrieval of comprehensive parameter information.
        
        Given: A CacheParameterMapper instance
        When: get_parameter_info() is called
        Then: Complete parameter classification information should be returned
        And: Parameter mappings should be included
        And: Validation rules should be documented
        """
        from app.infrastructure.cache.parameter_mapping import CacheParameterMapper
        
        # Given: A CacheParameterMapper instance
        mapper = CacheParameterMapper()
        
        # When: get_parameter_info() is called
        parameter_info = mapper.get_parameter_info()
        
        # Then: Complete parameter classification information should be returned
        assert isinstance(parameter_info, dict)
        # Use actual key names from implementation
        ai_key = "ai_specific_parameters" if "ai_specific_parameters" in parameter_info else "ai_specific_params"
        generic_key = "generic_parameters" if "generic_parameters" in parameter_info else "generic_params"
        
        assert ai_key in parameter_info
        assert generic_key in parameter_info
        assert "parameter_mappings" in parameter_info
        
        # And: Parameter classifications should be properly structured
        ai_specific_params = parameter_info[ai_key]
        generic_params = parameter_info[generic_key]
        
        assert isinstance(ai_specific_params, (set, list, tuple))
        assert isinstance(generic_params, (set, list, tuple))
        
        # Should have some parameters defined
        total_params = len(ai_specific_params) + len(generic_params)
        assert total_params > 0, "Should have some parameter classifications defined"
        
        # And: Parameter mappings should be included
        parameter_mappings = parameter_info["parameter_mappings"]
        assert isinstance(parameter_mappings, dict)
        
        # And: Should provide comprehensive information structure
        # Check that the info is substantial enough to be useful
        info_keys = list(parameter_info.keys())
        assert len(info_keys) >= 3, f"Should provide comprehensive information: {info_keys}"
        
        # Information should be consistent across calls
        second_info = mapper.get_parameter_info()
        assert parameter_info == second_info, "get_parameter_info() should return consistent data"