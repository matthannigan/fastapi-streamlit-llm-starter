"""
Unit tests for cache parameter mapping module following docstring-driven test development.

This test suite validates the comprehensive parameter mapping functionality that enables
AIResponseCache to inherit from GenericRedisCache with proper parameter separation,
validation, and compatibility checking.

Test Coverage Areas:
- ValidationResult dataclass behavior and methods per docstrings
- CacheParameterMapper parameter classification and mapping
- Parameter validation with detailed error reporting
- Parameter conflict detection and resolution
- Configuration recommendations and optimization suggestions
- Edge cases and boundary conditions documented in docstrings

Business Critical:
Parameter mapping failures would break cache inheritance architecture and prevent
proper AIResponseCache initialization, directly impacting AI service performance.

Test Strategy:
- Unit tests for individual validation and mapping methods
- Integration tests for complete parameter mapping workflows
- Edge case coverage for invalid configurations and conflicts
- Behavior verification based on documented contracts in docstrings
"""

import pytest
from unittest.mock import patch, MagicMock
from typing import Dict, Any, Set, List

from app.infrastructure.cache.parameter_mapping import (
    ValidationResult,
    CacheParameterMapper
)
from app.core.exceptions import ValidationError, ConfigurationError


class TestValidationResult:
    """
    Test suite for ValidationResult dataclass behavior and methods.
    
    Scope:
        - ValidationResult initialization and attribute management
        - Error, warning, and recommendation accumulation methods
        - Parameter conflict tracking and error generation
        - State management and thread-safe operations
        
    Business Critical:
        ValidationResult provides structured feedback for parameter mapping
        failures, enabling proper error handling and user guidance.
        
    Test Strategy:
        - Test each method per docstring specifications
        - Verify state changes and data accumulation behavior
        - Test error handling and validation state management
        - Validate thread-safe operation characteristics
    """
    
    def test_validation_result_initialization_defaults(self):
        """
        Test ValidationResult initializes with proper default values per docstring.
        
        Verifies:
            Default initialization creates valid, empty result structure
            
        Business Impact:
            Ensures consistent validation result structure for parameter processing
            
        Success Criteria:
            - is_valid defaults to True for empty validation results
            - All list and dict attributes initialize as empty collections
            - Context dictionary ready for additional validation metadata
        """
        result = ValidationResult()
        
        assert result.is_valid is True
        assert result.errors == []
        assert result.warnings == []
        assert result.recommendations == []
        assert result.parameter_conflicts == {}
        assert result.ai_specific_params == set()
        assert result.generic_params == set()
        assert result.context == {}
    
    def test_validation_result_initialization_with_data(self):
        """
        Test ValidationResult initialization with explicit data per docstring example.
        
        Verifies:
            Custom initialization with validation errors and metadata works correctly
            
        Business Impact:
            Enables structured error reporting with detailed context information
            
        Success Criteria:
            - Custom validation data properly assigned to attributes
            - is_valid correctly reflects presence of validation errors
            - All data structures maintain proper types and accessibility
        """
        result = ValidationResult(
            is_valid=False,
            errors=["Invalid compression_threshold: must be positive"],
            warnings=["memory_cache_size conflicts with l1_cache_size"],
            recommendations=["Consider using l1_cache_size instead of memory_cache_size"]
        )
        
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert "compression_threshold" in result.errors[0]
        assert len(result.warnings) == 1
        assert "memory_cache_size conflicts" in result.warnings[0]
        assert len(result.recommendations) == 1
        assert "l1_cache_size instead" in result.recommendations[0]
    
    def test_add_error_method_behavior(self):
        """
        Test add_error method marks result invalid and stores message per docstring.
        
        Verifies:
            Error addition automatically sets is_valid to False
            
        Business Impact:
            Ensures validation failures properly invalidate configuration results
            
        Success Criteria:
            - Error message added to errors list
            - is_valid automatically set to False
            - Multiple errors accumulate properly in sequence
        """
        result = ValidationResult()
        assert result.is_valid is True
        
        result.add_error("redis_url cannot be empty")
        
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert result.errors[0] == "redis_url cannot be empty"
        
        # Test multiple errors accumulate
        result.add_error("compression_threshold must be positive")
        assert len(result.errors) == 2
        assert result.is_valid is False
    
    def test_add_warning_method_behavior(self):
        """
        Test add_warning method stores non-fatal warnings per docstring.
        
        Verifies:
            Warnings are stored without affecting validation validity
            
        Business Impact:
            Provides guidance for suboptimal configurations without blocking usage
            
        Success Criteria:
            - Warning message added to warnings list
            - is_valid remains unchanged by warning addition
            - Multiple warnings accumulate independently
        """
        result = ValidationResult()
        assert result.is_valid is True
        
        result.add_warning("Low TTL may impact performance")
        
        assert result.is_valid is True  # Warnings don't affect validity
        assert len(result.warnings) == 1
        assert result.warnings[0] == "Low TTL may impact performance"
        
        # Test multiple warnings
        result.add_warning("High compression level uses more CPU")
        assert len(result.warnings) == 2
        assert result.is_valid is True
    
    def test_add_recommendation_method_behavior(self):
        """
        Test add_recommendation method stores optimization suggestions per docstring.
        
        Verifies:
            Recommendations are stored for configuration improvement guidance
            
        Business Impact:
            Helps users optimize cache configurations for better performance
            
        Success Criteria:
            - Recommendation message added to recommendations list
            - is_valid remains unchanged by recommendation addition
            - Multiple recommendations accumulate for comprehensive guidance
        """
        result = ValidationResult()
        
        result.add_recommendation("Consider enabling compression")
        
        assert result.is_valid is True  # Recommendations don't affect validity
        assert len(result.recommendations) == 1
        assert result.recommendations[0] == "Consider enabling compression"
        
        # Test multiple recommendations
        result.add_recommendation("Use L1 cache for better performance")
        assert len(result.recommendations) == 2
    
    def test_add_conflict_method_behavior(self):
        """
        Test add_conflict method stores conflicts and creates errors per docstring.
        
        Verifies:
            Parameter conflicts are tracked with descriptions and generate errors
            
        Business Impact:
            Prevents cache configuration conflicts that could cause runtime failures
            
        Success Criteria:
            - Conflict stored in parameter_conflicts mapping
            - Automatic error generation for the conflict
            - is_valid set to False due to conflict error
        """
        result = ValidationResult()
        
        result.add_conflict("memory_cache_size", 
                          "conflicts with l1_cache_size (both map to same parameter)")
        
        assert result.is_valid is False
        assert "memory_cache_size" in result.parameter_conflicts
        assert result.parameter_conflicts["memory_cache_size"] == "conflicts with l1_cache_size (both map to same parameter)"
        assert len(result.errors) == 1
        assert "Parameter conflict for 'memory_cache_size'" in result.errors[0]


class TestCacheParameterMapper:
    """
    Test suite for CacheParameterMapper parameter mapping and validation functionality.
    
    Scope:
        - Parameter classification (generic vs AI-specific)
        - Parameter mapping from AI names to generic equivalents
        - Comprehensive parameter validation with detailed reporting
        - Configuration recommendations and optimization suggestions
        - Error handling for invalid configurations and edge cases
        
    Business Critical:
        Parameter mapping enables AIResponseCache inheritance from GenericRedisCache,
        which is fundamental to the cache architecture refactoring strategy.
        
    Test Strategy:
        - Test parameter classification accuracy per documented categories
        - Verify mapping logic for AI-to-generic parameter transformation
        - Validate comprehensive parameter validation with all documented rules
        - Test edge cases and error conditions documented in method docstrings
        - Ensure thread-safe operation and consistent behavior
    """
    
    @pytest.fixture
    def mapper(self):
        """Provide CacheParameterMapper instance for testing."""
        return CacheParameterMapper()
    
    def test_mapper_initialization(self, mapper):
        """
        Test CacheParameterMapper initializes with proper parameter classifications per docstring.
        
        Verifies:
            Initialization sets up comprehensive parameter classification system
            
        Business Impact:
            Proper initialization ensures accurate parameter mapping for cache inheritance
            
        Success Criteria:
            - Generic parameters set contains expected Redis cache parameters
            - AI-specific parameters set contains documented AI functionality parameters
            - Parameter mappings dictionary contains AI-to-generic mappings
            - Validation rules configured for all documented parameter types
        """
        # Test generic parameters are properly classified
        expected_generic = {
            'redis_url', 'default_ttl', 'enable_l1_cache', 'l1_cache_size',
            'compression_threshold', 'compression_level', 'performance_monitor', 'security_config'
        }
        assert mapper._generic_parameters == expected_generic
        
        # Test AI-specific parameters are properly classified
        expected_ai_specific = {
            'text_hash_threshold', 'hash_algorithm', 'text_size_tiers', 'operation_ttls'
        }
        assert mapper._ai_specific_parameters == expected_ai_specific
        
        # Test parameter mappings are configured
        expected_mappings = {
            'memory_cache_size': 'l1_cache_size'
        }
        assert mapper._parameter_mappings == expected_mappings
        
        # Test validation rules are configured
        assert 'redis_url' in mapper._parameter_validators
        assert 'memory_cache_size' in mapper._parameter_validators
        assert 'text_hash_threshold' in mapper._parameter_validators
    
    def test_map_ai_to_generic_params_basic_mapping(self, mapper):
        """
        Test map_ai_to_generic_params performs basic parameter separation per docstring example.
        
        Verifies:
            Basic AI parameter mapping to generic and AI-specific categories
            
        Business Impact:
            Enables AIResponseCache to initialize GenericRedisCache with proper parameters
            
        Success Criteria:
            - Generic parameters extracted for GenericRedisCache initialization
            - AI-specific parameters separated for specialized handling
            - Parameter mappings applied correctly (memory_cache_size -> l1_cache_size)
            - Return tuple format matches docstring specification
        """
        ai_params = {
            'redis_url': 'redis://localhost:6379',
            'memory_cache_size': 100,
            'text_hash_threshold': 1000,
            'compression_threshold': 2000
        }
        
        generic_params, ai_specific_params = mapper.map_ai_to_generic_params(ai_params)
        
        # Verify generic parameters
        expected_generic = {
            'redis_url': 'redis://localhost:6379',
            'l1_cache_size': 100,  # Mapped from memory_cache_size
            'compression_threshold': 2000,
            'enable_l1_cache': True  # Auto-enabled due to l1_cache_size
        }
        assert generic_params == expected_generic
        
        # Verify AI-specific parameters
        expected_ai_specific = {
            'text_hash_threshold': 1000
        }
        assert ai_specific_params == expected_ai_specific
    
    def test_map_ai_to_generic_params_memory_cache_mapping(self, mapper):
        """
        Test memory_cache_size parameter mapping to l1_cache_size per docstring mapping rules.
        
        Verifies:
            AI parameter names properly mapped to generic equivalents
            
        Business Impact:
            Ensures compatibility between AI cache configuration and generic cache interface
            
        Success Criteria:
            - memory_cache_size mapped to l1_cache_size in generic parameters
            - enable_l1_cache automatically set when cache size specified
            - Original AI parameter not included in generic parameters
        """
        ai_params = {'memory_cache_size': 500}
        
        generic_params, ai_specific_params = mapper.map_ai_to_generic_params(ai_params)
        
        assert 'l1_cache_size' in generic_params
        assert generic_params['l1_cache_size'] == 500
        assert generic_params['enable_l1_cache'] is True
        assert 'memory_cache_size' not in generic_params
        assert len(ai_specific_params) == 0
    
    def test_map_ai_to_generic_params_unknown_parameter_handling(self, mapper):
        """
        Test unknown parameter handling treats unknowns as AI-specific per docstring behavior.
        
        Verifies:
            Unknown parameters are categorized as AI-specific with warning logging
            
        Business Impact:
            Provides graceful handling of future AI parameters without breaking mapping
            
        Success Criteria:
            - Unknown parameters placed in ai_specific_params
            - Warning logged for unknown parameter classification
            - Mapping operation continues successfully despite unknown parameters
        """
        ai_params = {
            'redis_url': 'redis://localhost:6379',
            'unknown_parameter': 'some_value',
            'another_unknown': 42
        }
        
        with patch('app.infrastructure.cache.parameter_mapping.logger') as mock_logger:
            generic_params, ai_specific_params = mapper.map_ai_to_generic_params(ai_params)
        
        # Verify unknown parameters treated as AI-specific
        assert 'unknown_parameter' in ai_specific_params
        assert 'another_unknown' in ai_specific_params
        assert ai_specific_params['unknown_parameter'] == 'some_value'
        assert ai_specific_params['another_unknown'] == 42
        
        # Verify known generic parameter handled correctly
        assert 'redis_url' in generic_params
        assert generic_params['redis_url'] == 'redis://localhost:6379'
        
        # Verify warning logged for unknown parameters
        assert mock_logger.warning.called
        warning_calls = [call for call in mock_logger.warning.call_args_list 
                        if 'Unknown parameter' in str(call)]
        assert len(warning_calls) == 2  # Two unknown parameters
    
    def test_map_ai_to_generic_params_exception_handling(self, mapper):
        """
        Test map_ai_to_generic_params exception handling per docstring Raises section.
        
        Verifies:
            Method handles edge cases gracefully and provides structured results
            
        Business Impact:
            Ensures parameter mapping is robust against unexpected input scenarios
            
        Success Criteria:
            - Method returns valid results for all reasonable input parameters
            - Result structure maintains expected tuple format
            - No exceptions raised for valid parameter dictionaries
        """
        # Test various edge cases that should be handled gracefully
        edge_case_params = [
            {},  # Empty parameters
            {'unknown_param': None},  # None values
            {'nested_param': {'inner': 'value'}},  # Nested structures
            {'large_param': 'x' * 10000},  # Large string values
        ]
        
        for params in edge_case_params:
            try:
                result = mapper.map_ai_to_generic_params(params)
                # Method should always return a tuple
                assert isinstance(result, tuple)
                assert len(result) == 2
                generic_params, ai_specific_params = result
                assert isinstance(generic_params, dict)
                assert isinstance(ai_specific_params, dict)
            except ConfigurationError as e:
                # If ConfigurationError is raised, verify it has proper context
                assert 'Failed to map AI parameters' in str(e)
                assert hasattr(e, 'context')
        
        # Test that normal parameters work correctly
        normal_params = {'redis_url': 'redis://localhost:6379', 'memory_cache_size': 100}
        result = mapper.map_ai_to_generic_params(normal_params)
        assert isinstance(result, tuple)
        assert len(result) == 2
    
    def test_validate_parameter_compatibility_valid_config(self, mapper):
        """
        Test validate_parameter_compatibility with valid configuration per docstring behavior.
        
        Verifies:
            Valid parameter configurations pass validation with proper classification
            
        Business Impact:
            Ensures properly configured cache parameters are validated successfully
            
        Success Criteria:
            - ValidationResult.is_valid returns True for valid configurations
            - Parameter classification correctly identifies generic vs AI-specific
            - No validation errors generated for valid parameter values and types
        """
        ai_params = {
            'redis_url': 'redis://localhost:6379',
            'memory_cache_size': 100,
            'text_hash_threshold': 1000,
            'compression_threshold': 500,
            'compression_level': 6
        }
        
        result = mapper.validate_parameter_compatibility(ai_params)
        
        assert result.is_valid is True
        assert len(result.errors) == 0
        assert 'memory_cache_size' in result.generic_params
        assert 'text_hash_threshold' in result.ai_specific_params
        assert result.context['total_parameters'] == 5
    
    def test_validate_parameter_compatibility_invalid_types(self, mapper):
        """
        Test validate_parameter_compatibility with invalid parameter types per docstring example.
        
        Verifies:
            Type validation errors are properly detected and reported
            
        Business Impact:
            Prevents runtime errors from invalid parameter types in cache configuration
            
        Success Criteria:
            - ValidationResult.is_valid returns False for type errors
            - Specific error messages identify parameter name and expected type
            - Multiple type errors are all detected and reported
        """
        ai_params = {
            'memory_cache_size': 'invalid_string',  # Should be int
            'text_hash_threshold': -10,  # Should be positive
            'compression_level': 15  # Should be <= 9
        }
        
        result = mapper.validate_parameter_compatibility(ai_params)
        
        assert result.is_valid is False
        assert len(result.errors) >= 2  # At least type error and range error
        
        # Check for type error
        type_error_found = any('must be int' in error for error in result.errors)
        assert type_error_found
        
        # Check for range errors
        range_error_found = any('must be >=' in error or 'must be <=' in error 
                               for error in result.errors)
        assert range_error_found
    
    def test_validate_parameter_compatibility_redis_url_validation(self, mapper):
        """
        Test Redis URL format validation per custom validator docstring behavior.
        
        Verifies:
            Redis URL format validation with proper scheme checking
            
        Business Impact:
            Prevents connection errors from malformed Redis URLs
            
        Success Criteria:
            - Valid Redis URL schemes (redis://, rediss://, unix://) pass validation
            - Invalid URL schemes generate specific format error messages
            - Error messages include acceptable URL format examples
        """
        # Test valid Redis URLs
        valid_urls = [
            'redis://localhost:6379',
            'rediss://secure.redis.com:6380',  
            'unix:///tmp/redis.sock'
        ]
        
        for url in valid_urls:
            result = mapper.validate_parameter_compatibility({'redis_url': url})
            assert result.is_valid is True, f"Valid URL failed validation: {url}"
        
        # Test invalid Redis URL
        result = mapper.validate_parameter_compatibility({'redis_url': 'http://localhost:6379'})
        assert result.is_valid is False
        
        url_error_found = any('must be a valid Redis URL' in error for error in result.errors)
        assert url_error_found
    
    def test_validate_parameter_compatibility_text_size_tiers_validation(self, mapper):
        """
        Test text_size_tiers custom validation per docstring validator behavior.
        
        Verifies:
            Text size tiers validation with required tiers and ordering
            
        Business Impact:
            Ensures proper text categorization for AI cache optimization
            
        Success Criteria:
            - Required tiers (small, medium, large) must be present
            - Tier values must be positive integers
            - Tiers must be ordered: small < medium < large
        """
        # Test valid text size tiers
        valid_tiers = {
            'small': 100,
            'medium': 1000, 
            'large': 10000
        }
        result = mapper.validate_parameter_compatibility({'text_size_tiers': valid_tiers})
        assert result.is_valid is True
        
        # Test missing required tier
        invalid_tiers = {
            'small': 100,
            'medium': 1000
            # Missing 'large'
        }
        result = mapper.validate_parameter_compatibility({'text_size_tiers': invalid_tiers})
        assert result.is_valid is False
        missing_tier_error = any('missing required tiers' in error for error in result.errors)
        assert missing_tier_error
        
        # Test invalid tier ordering
        unordered_tiers = {
            'small': 1000,
            'medium': 100,  # Wrong order: medium < small
            'large': 10000
        }
        result = mapper.validate_parameter_compatibility({'text_size_tiers': unordered_tiers})
        assert result.is_valid is False
        ordering_error = any('must be ordered' in error for error in result.errors)
        assert ordering_error
    
    def test_validate_parameter_compatibility_operation_ttls_validation(self, mapper):
        """
        Test operation_ttls custom validation per docstring validator behavior.
        
        Verifies:
            Operation TTL validation with positive values and reasonable limits
            
        Business Impact:
            Ensures proper cache expiration settings for different AI operations
            
        Success Criteria:
            - TTL values must be positive integers
            - Very large TTLs generate warnings but don't fail validation
            - Unknown operations generate warnings for user guidance
        """
        # Test valid operation TTLs
        valid_ttls = {
            'summarize': 3600,
            'sentiment': 1800,
            'key_points': 7200
        }
        result = mapper.validate_parameter_compatibility({'operation_ttls': valid_ttls})
        assert result.is_valid is True
        
        # Test invalid TTL values
        invalid_ttls = {
            'summarize': 0,  # Invalid: must be positive
            'sentiment': 'invalid'  # Invalid: must be integer
        }
        result = mapper.validate_parameter_compatibility({'operation_ttls': invalid_ttls})
        assert result.is_valid is False
        
        ttl_errors = [error for error in result.errors if 'must be a positive integer' in error]
        assert len(ttl_errors) >= 1  # At least one TTL error
        
        # Test very large TTL warning
        large_ttls = {
            'summarize': 86400 * 400  # > 1 year
        }
        result = mapper.validate_parameter_compatibility({'operation_ttls': large_ttls})
        assert result.is_valid is True  # Valid but with warnings
        
        large_ttl_warning = any('very large' in warning for warning in result.warnings)
        assert large_ttl_warning
        
        # Test unknown operation warning
        unknown_ttls = {
            'unknown_operation': 3600
        }
        result = mapper.validate_parameter_compatibility({'operation_ttls': unknown_ttls})
        assert result.is_valid is True  # Valid but with warnings
        
        unknown_op_warning = any('Unknown operation' in warning for warning in result.warnings)
        assert unknown_op_warning
    
    def test_validate_parameter_compatibility_conflict_detection(self, mapper):
        """
        Test parameter conflict detection per docstring conflict checking behavior.
        
        Verifies:
            Parameter conflicts are detected and reported with detailed descriptions
            
        Business Impact:
            Prevents cache configuration conflicts that could cause initialization failures
            
        Success Criteria:
            - memory_cache_size vs l1_cache_size conflicts detected
            - L1 cache consistency warnings for mismatched enable/size settings
            - Compression configuration consistency warnings
        """
        # Test memory_cache_size vs l1_cache_size conflict
        conflicting_params = {
            'memory_cache_size': 100,
            'l1_cache_size': 200  # Different values conflict
        }
        result = mapper.validate_parameter_compatibility(conflicting_params)
        assert result.is_valid is False
        
        conflict_error = any('memory_cache_size' in error and 'conflicts with l1_cache_size' in error 
                            for error in result.errors)
        assert conflict_error
        
        # Test L1 cache consistency warning
        inconsistent_l1 = {
            'enable_l1_cache': False,
            'memory_cache_size': 100  # Size specified but cache disabled
        }
        result = mapper.validate_parameter_compatibility(inconsistent_l1)
        assert result.is_valid is True  # Valid but with warning
        
        l1_warning = any('L1 cache is disabled but cache size is specified' in warning 
                        for warning in result.warnings)
        assert l1_warning
        
        # Test compression consistency warning
        inconsistent_compression = {
            'compression_threshold': 0,  # Disabled
            'compression_level': 9  # High level but disabled
        }
        result = mapper.validate_parameter_compatibility(inconsistent_compression)
        assert result.is_valid is True  # Valid but with warning
        
        compression_warning = any('Compression threshold is 0' in warning and 'compression level' in warning 
                                 for warning in result.warnings)
        assert compression_warning
    
    def test_validate_parameter_compatibility_recommendations(self, mapper):
        """
        Test configuration recommendations per docstring recommendation behavior.
        
        Verifies:
            Intelligent configuration recommendations for optimization
            
        Business Impact:
            Helps users optimize cache configurations for better performance
            
        Success Criteria:
            - Recommendations for using l1_cache_size vs memory_cache_size
            - Performance recommendations for compression settings
            - Consistency recommendations for threshold alignment
        """
        # Test recommendation for l1_cache_size instead of memory_cache_size
        suboptimal_params = {
            'memory_cache_size': 100
        }
        result = mapper.validate_parameter_compatibility(suboptimal_params)
        assert result.is_valid is True
        
        l1_recommendation = any("Consider using 'l1_cache_size' instead" in rec 
                               for rec in result.recommendations)
        assert l1_recommendation
        
        # Test high compression threshold recommendation
        high_compression_params = {
            'compression_threshold': 15000  # High threshold
        }
        result = mapper.validate_parameter_compatibility(high_compression_params)
        
        compression_rec = any('Compression threshold' in rec and 'quite high' in rec 
                             for rec in result.recommendations)
        assert compression_rec
        
        # Test consistency recommendation for threshold alignment
        misaligned_params = {
            'text_hash_threshold': 500,
            'compression_threshold': 2000  # Different from text hash threshold
        }
        result = mapper.validate_parameter_compatibility(misaligned_params)
        
        alignment_rec = any('Text hash threshold' in rec and 'differs from compression threshold' in rec 
                           for rec in result.recommendations)
        assert alignment_rec
    
    def test_get_parameter_info_comprehensive_info(self, mapper):
        """
        Test get_parameter_info returns comprehensive parameter information per docstring.
        
        Verifies:
            Complete parameter information including classifications and validation rules
            
        Business Impact:
            Provides debugging and documentation information for parameter system
            
        Success Criteria:
            - Generic parameters list contains all documented generic parameters
            - AI-specific parameters list contains all documented AI parameters
            - Parameter mappings include all configured AI-to-generic mappings
            - Validation rules exclude sensitive information (validator functions)
        """
        info = mapper.get_parameter_info()
        
        # Verify all expected keys are present
        required_keys = {
            'generic_parameters', 'ai_specific_parameters', 'parameter_mappings',
            'parameter_conflicts', 'validation_rules', 'total_parameters'
        }
        assert set(info.keys()) == required_keys
        
        # Verify parameter classifications
        assert 'redis_url' in info['generic_parameters']
        assert 'text_hash_threshold' in info['ai_specific_parameters']
        
        # Verify parameter mappings
        assert info['parameter_mappings']['memory_cache_size'] == 'l1_cache_size'
        
        # Verify validation rules don't include validator functions
        for param, rules in info['validation_rules'].items():
            assert 'validator' not in rules, f"Validator function exposed for {param}"
        
        # Verify total parameter count
        expected_total = len(info['generic_parameters']) + len(info['ai_specific_parameters'])
        assert info['total_parameters'] == expected_total
    
    def test_validate_parameter_compatibility_exception_handling(self, mapper):
        """
        Test validate_parameter_compatibility exception handling per docstring behavior.
        
        Verifies:
            Graceful exception handling with error reporting in validation result
            
        Business Impact:
            Prevents validation system crashes from unexpected parameter processing errors
            
        Success Criteria:
            - Exceptions caught and converted to validation errors
            - ValidationResult still returned with error information
            - Exception context preserved in result for debugging
        """
        # Mock a method to raise an exception during validation
        with patch.object(mapper, '_validate_single_parameter', side_effect=Exception("Test exception")):
            result = mapper.validate_parameter_compatibility({'test_param': 'value'})
        
        assert result.is_valid is False
        assert len(result.errors) >= 1
        
        # Verify exception is converted to validation error
        exception_error = any('Parameter validation failed with exception' in error 
                             for error in result.errors)
        assert exception_error
        
        # Verify exception context is preserved
        assert 'validation_exception' in result.context
        assert result.context['validation_exception'] == "Test exception"


class TestParameterMappingIntegration:
    """
    Integration tests for complete parameter mapping workflows.
    
    Scope:
        - End-to-end parameter mapping and validation workflows
        - Real-world configuration scenarios and edge cases
        - Performance characteristics under various parameter loads
        
    Business Critical:
        Integration workflows must support AIResponseCache inheritance architecture
        without performance degradation or configuration conflicts.
        
    Test Strategy:
        - Test complete workflows from AI parameters to validated generic parameters
        - Verify realistic cache configuration scenarios
        - Test performance with large parameter sets
        - Validate error recovery and graceful degradation
    """
    
    @pytest.fixture
    def mapper(self):
        """Provide CacheParameterMapper instance for integration testing."""
        return CacheParameterMapper()
    
    def test_complete_parameter_mapping_workflow(self, mapper):
        """
        Test complete workflow from AI parameters to validated mapping per docstring usage.
        
        Verifies:
            Full parameter processing workflow for AI cache inheritance
            
        Business Impact:
            Validates complete integration path for AIResponseCache initialization
            
        Success Criteria:
            - AI parameters successfully mapped to generic and AI-specific categories
            - Validation passes for properly configured parameters
            - Results suitable for GenericRedisCache and AIResponseCache initialization
        """
        # Realistic AI cache configuration
        ai_cache_config = {
            'redis_url': 'redis://localhost:6379',
            'default_ttl': 3600,
            'memory_cache_size': 100,
            'compression_threshold': 1000,
            'compression_level': 6,
            'text_hash_threshold': 1500,
            'operation_ttls': {
                'summarize': 7200,
                'sentiment': 3600,
                'key_points': 5400
            }
        }
        
        # Step 1: Map parameters
        generic_params, ai_specific_params = mapper.map_ai_to_generic_params(ai_cache_config)
        
        # Step 2: Validate compatibility  
        validation_result = mapper.validate_parameter_compatibility(ai_cache_config)
        
        # Verify mapping results
        assert 'redis_url' in generic_params
        assert 'l1_cache_size' in generic_params  # Mapped from memory_cache_size
        assert 'enable_l1_cache' in generic_params  # Auto-enabled
        assert 'compression_threshold' in generic_params
        assert 'compression_level' in generic_params
        
        assert 'text_hash_threshold' in ai_specific_params
        assert 'operation_ttls' in ai_specific_params
        
        # Verify validation results
        assert validation_result.is_valid is True
        assert len(validation_result.errors) == 0
        
        # Verify parameter classification in validation result
        assert 'redis_url' in validation_result.generic_params or \
               'memory_cache_size' in validation_result.generic_params
        assert 'text_hash_threshold' in validation_result.ai_specific_params
    
    def test_parameter_mapping_with_conflicts_and_recommendations(self, mapper):
        """
        Test parameter mapping with conflicts and optimization recommendations.
        
        Verifies:
            Complex scenarios with parameter conflicts and optimization opportunities
            
        Business Impact:
            Provides comprehensive feedback for cache configuration improvement
            
        Success Criteria:
            - Conflicts detected and reported with actionable descriptions
            - Recommendations provided for performance optimization
            - User guidance available for resolving configuration issues
        """
        problematic_config = {
            'memory_cache_size': 100,
            'l1_cache_size': 200,  # Conflict with memory_cache_size
            'compression_threshold': 50000,  # Very high threshold
            'compression_level': 9,  # High CPU usage
            'text_hash_threshold': 500,  # Different from compression threshold
            'enable_l1_cache': False,  # Inconsistent with cache sizes
        }
        
        validation_result = mapper.validate_parameter_compatibility(problematic_config)
        
        # Should be invalid due to conflicts
        assert validation_result.is_valid is False
        
        # Should have parameter conflict
        assert len(validation_result.parameter_conflicts) > 0
        assert 'memory_cache_size' in validation_result.parameter_conflicts
        
        # Should have warnings about inconsistencies
        assert len(validation_result.warnings) > 0
        l1_warning_found = any('L1 cache is disabled but cache size' in warning 
                              for warning in validation_result.warnings)
        assert l1_warning_found
        
        # Should have optimization recommendations
        assert len(validation_result.recommendations) > 0
        compression_rec_found = any('Compression threshold' in rec and 'quite high' in rec 
                                   for rec in validation_result.recommendations)
        assert compression_rec_found
    
    def test_parameter_mapping_performance_characteristics(self, mapper):
        """
        Test parameter mapping performance with large parameter sets.
        
        Verifies:
            Performance characteristics meet requirements for production usage
            
        Business Impact:
            Ensures parameter mapping doesn't become bottleneck during cache initialization
            
        Success Criteria:
            - Large parameter sets processed efficiently
            - Memory usage remains reasonable during processing
            - Validation time scales appropriately with parameter count
        """
        # Generate large parameter set
        large_config = {
            'redis_url': 'redis://localhost:6379',
            'memory_cache_size': 1000,
            'text_hash_threshold': 2000,
            'compression_threshold': 1500,
            'operation_ttls': {f'operation_{i}': 3600 + i for i in range(50)}
        }
        
        # Test mapping performance
        import time
        start_time = time.time()
        generic_params, ai_specific_params = mapper.map_ai_to_generic_params(large_config)
        mapping_time = time.time() - start_time
        
        # Test validation performance
        start_time = time.time()
        validation_result = mapper.validate_parameter_compatibility(large_config)
        validation_time = time.time() - start_time
        
        # Performance should be reasonable (< 100ms each for this size)
        assert mapping_time < 0.1, f"Mapping too slow: {mapping_time}s"
        assert validation_time < 0.1, f"Validation too slow: {validation_time}s"
        
        # Results should be correct despite large size
        assert validation_result.is_valid is True
        assert len(generic_params) >= 3  # At least redis_url, l1_cache_size, enable_l1_cache, compression_threshold
        assert len(ai_specific_params) >= 2  # At least text_hash_threshold, operation_ttls