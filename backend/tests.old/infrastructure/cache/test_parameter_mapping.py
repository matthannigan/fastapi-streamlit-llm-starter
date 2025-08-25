"""
Comprehensive unit tests for cache parameter mapping functionality.

These tests ensure the parameter mapping module correctly separates AI-specific
parameters from generic Redis parameters, validates compatibility, and provides
accurate validation results for the cache inheritance refactoring.

Test Categories:
    - ValidationResult dataclass functionality
    - CacheParameterMapper initialization and configuration
    - Parameter mapping from AI to generic parameters
    - Parameter validation and compatibility checking
    - Error handling and edge cases
    - Integration scenarios for cache inheritance

Coverage Requirements:
    - >95% test coverage for new parameter mapping code
    - All parameter validation rules tested
    - All error conditions and edge cases covered
    - Integration with existing cache infrastructure verified
"""

import pytest
from typing import Any, Dict
from unittest.mock import Mock, patch

from app.core.exceptions import ValidationError, ConfigurationError
from app.infrastructure.cache.parameter_mapping import (
    ValidationResult,
    CacheParameterMapper
)


class TestValidationResult:
    """Test cases for ValidationResult dataclass functionality."""
    
    def test_validation_result_initialization(self):
        """Test ValidationResult initializes with correct defaults."""
        result = ValidationResult()
        
        assert result.is_valid is True
        assert result.errors == []
        assert result.warnings == []
        assert result.recommendations == []
        assert result.parameter_conflicts == {}
        assert result.ai_specific_params == set()
        assert result.generic_params == set()
        assert result.context == {}
    
    def test_validation_result_custom_initialization(self):
        """Test ValidationResult with custom initial values."""
        result = ValidationResult(
            is_valid=False,
            errors=["Initial error"],
            warnings=["Initial warning"],
            recommendations=["Initial recommendation"]
        )
        
        assert result.is_valid is False
        assert "Initial error" in result.errors
        assert "Initial warning" in result.warnings
        assert "Initial recommendation" in result.recommendations
    
    def test_add_error_marks_invalid(self):
        """Test that adding an error marks the result as invalid."""
        result = ValidationResult()
        assert result.is_valid is True
        
        result.add_error("Test error")
        
        assert result.is_valid is False
        assert "Test error" in result.errors
    
    def test_add_warning_preserves_validity(self):
        """Test that adding a warning preserves validity if no errors."""
        result = ValidationResult()
        assert result.is_valid is True
        
        result.add_warning("Test warning")
        
        assert result.is_valid is True
        assert "Test warning" in result.warnings
    
    def test_add_recommendation(self):
        """Test adding recommendations to validation result."""
        result = ValidationResult()
        
        result.add_recommendation("Test recommendation")
        
        assert "Test recommendation" in result.recommendations
    
    def test_add_conflict_creates_error(self):
        """Test that adding a conflict creates an error and marks invalid."""
        result = ValidationResult()
        assert result.is_valid is True
        
        result.add_conflict("test_param", "Test conflict description")
        
        assert result.is_valid is False
        assert result.parameter_conflicts["test_param"] == "Test conflict description"
        assert any("test_param" in error for error in result.errors)


class TestCacheParameterMapperInitialization:
    """Test cases for CacheParameterMapper initialization and configuration."""
    
    def test_mapper_initialization(self):
        """Test that CacheParameterMapper initializes correctly."""
        mapper = CacheParameterMapper()
        
        # Check that parameter sets are properly initialized
        assert len(mapper._generic_parameters) > 0
        assert len(mapper._ai_specific_parameters) > 0
        assert isinstance(mapper._parameter_mappings, dict)
        assert isinstance(mapper._parameter_validators, dict)
    
    def test_generic_parameters_defined(self):
        """Test that all expected generic parameters are defined."""
        mapper = CacheParameterMapper()
        
        expected_generic = {
            'redis_url', 'default_ttl', 'enable_l1_cache', 'l1_cache_size',
            'compression_threshold', 'compression_level', 'performance_monitor',
            'security_config'
        }
        
        assert expected_generic.issubset(mapper._generic_parameters)
    
    def test_ai_specific_parameters_defined(self):
        """Test that all expected AI-specific parameters are defined."""
        mapper = CacheParameterMapper()
        
        expected_ai_specific = {
            'text_hash_threshold', 'hash_algorithm', 'text_size_tiers',
            'operation_ttls'
        }
        
        assert expected_ai_specific.issubset(mapper._ai_specific_parameters)
    
    def test_parameter_mappings_defined(self):
        """Test that parameter mappings are correctly defined."""
        mapper = CacheParameterMapper()
        
        # Should map memory_cache_size to l1_cache_size
        assert mapper._parameter_mappings.get('memory_cache_size') == 'l1_cache_size'
    
    def test_parameter_validators_coverage(self):
        """Test that parameter validators cover all known parameters."""
        mapper = CacheParameterMapper()
        
        # Key parameters should have validators
        expected_validated_params = {
            'redis_url', 'default_ttl', 'l1_cache_size', 'memory_cache_size',
            'compression_threshold', 'compression_level', 'text_hash_threshold',
            'text_size_tiers', 'operation_ttls'
        }
        
        assert expected_validated_params.issubset(set(mapper._parameter_validators.keys()))


class TestParameterMapping:
    """Test cases for parameter mapping from AI to generic parameters."""
    
    def test_map_generic_parameters_direct(self):
        """Test mapping of direct generic parameters."""
        mapper = CacheParameterMapper()
        ai_params = {
            'redis_url': 'redis://localhost:6379',
            'default_ttl': 3600,
            'compression_threshold': 1000
        }
        
        generic_params, ai_specific_params = mapper.map_ai_to_generic_params(ai_params)
        
        assert generic_params == ai_params
        assert ai_specific_params == {}
    
    def test_map_ai_specific_parameters(self):
        """Test mapping of AI-specific parameters."""
        mapper = CacheParameterMapper()
        ai_params = {
            'text_hash_threshold': 1000,
            'hash_algorithm': 'sha256',
            'operation_ttls': {'summarize': 7200}
        }
        
        generic_params, ai_specific_params = mapper.map_ai_to_generic_params(ai_params)
        
        assert generic_params == {}
        assert ai_specific_params == ai_params
    
    def test_map_mixed_parameters(self):
        """Test mapping of mixed generic and AI-specific parameters."""
        mapper = CacheParameterMapper()
        ai_params = {
            'redis_url': 'redis://localhost:6379',
            'compression_threshold': 1000,
            'text_hash_threshold': 500,
            'operation_ttls': {'summarize': 7200}
        }
        
        generic_params, ai_specific_params = mapper.map_ai_to_generic_params(ai_params)
        
        expected_generic = {
            'redis_url': 'redis://localhost:6379',
            'compression_threshold': 1000
        }
        expected_ai_specific = {
            'text_hash_threshold': 500,
            'operation_ttls': {'summarize': 7200}
        }
        
        assert generic_params == expected_generic
        assert ai_specific_params == expected_ai_specific
    
    def test_map_memory_cache_size_to_l1_cache_size(self):
        """Test mapping of memory_cache_size to l1_cache_size."""
        mapper = CacheParameterMapper()
        ai_params = {
            'memory_cache_size': 200,
            'redis_url': 'redis://localhost:6379'
        }
        
        generic_params, ai_specific_params = mapper.map_ai_to_generic_params(ai_params)
        
        assert generic_params['l1_cache_size'] == 200
        assert generic_params['enable_l1_cache'] is True  # Auto-enabled
        assert 'memory_cache_size' not in generic_params
        assert ai_specific_params == {}
    
    def test_map_auto_enable_l1_cache(self):
        """Test that L1 cache is auto-enabled when l1_cache_size is provided."""
        mapper = CacheParameterMapper()
        ai_params = {
            'l1_cache_size': 150,
            'redis_url': 'redis://localhost:6379'
        }
        
        generic_params, ai_specific_params = mapper.map_ai_to_generic_params(ai_params)
        
        assert generic_params['l1_cache_size'] == 150
        assert generic_params['enable_l1_cache'] is True  # Auto-enabled
        assert generic_params['redis_url'] == 'redis://localhost:6379'
    
    def test_map_unknown_parameters_as_ai_specific(self):
        """Test that unknown parameters are treated as AI-specific."""
        mapper = CacheParameterMapper()
        ai_params = {
            'unknown_parameter': 'some_value',
            'another_unknown': 42
        }
        
        generic_params, ai_specific_params = mapper.map_ai_to_generic_params(ai_params)
        
        assert generic_params == {}
        assert ai_specific_params == ai_params
    
    def test_map_empty_parameters(self):
        """Test mapping with empty parameter dictionary."""
        mapper = CacheParameterMapper()
        ai_params = {}
        
        generic_params, ai_specific_params = mapper.map_ai_to_generic_params(ai_params)
        
        assert generic_params == {}
        assert ai_specific_params == {}
    
    @patch('app.infrastructure.cache.parameter_mapping.logger')
    def test_map_parameters_exception_handling(self, mock_logger):
        """Test exception handling in parameter mapping."""
        mapper = CacheParameterMapper()
        
        # Create a mock that raises an exception during dict.items()
        class FailingDict:
            def keys(self):
                return ['bad_param']
            
            def items(self):
                raise ValueError("Simulated failure")
        
        ai_params = FailingDict()
        
        # This should raise a ConfigurationError wrapping the original exception
        with pytest.raises(ConfigurationError, match="Failed to map AI parameters"):
            mapper.map_ai_to_generic_params(ai_params)


class TestParameterValidation:
    """Test cases for parameter validation and compatibility checking."""
    
    def test_validate_valid_parameters(self):
        """Test validation of valid parameters."""
        mapper = CacheParameterMapper()
        ai_params = {
            'redis_url': 'redis://localhost:6379',
            'default_ttl': 3600,
            'memory_cache_size': 100,
            'text_hash_threshold': 1000
        }
        
        result = mapper.validate_parameter_compatibility(ai_params)
        
        assert result.is_valid is True
        assert len(result.errors) == 0
        assert len(result.ai_specific_params) > 0
        assert len(result.generic_params) > 0
    
    def test_validate_invalid_types(self):
        """Test validation of parameters with invalid types."""
        mapper = CacheParameterMapper()
        ai_params = {
            'default_ttl': 'not_an_integer',
            'memory_cache_size': 'not_an_integer',
            'enable_l1_cache': 'not_a_boolean'
        }
        
        result = mapper.validate_parameter_compatibility(ai_params)
        
        assert result.is_valid is False
        assert len(result.errors) >= 3
        assert any('must be int' in error for error in result.errors)
        assert any('must be bool' in error for error in result.errors)
    
    def test_validate_out_of_range_values(self):
        """Test validation of parameters with out-of-range values."""
        mapper = CacheParameterMapper()
        ai_params = {
            'default_ttl': -1,  # Must be >= 1
            'memory_cache_size': 0,  # Must be >= 1
            'compression_level': 15,  # Must be <= 9
            'text_hash_threshold': -100  # Must be >= 1
        }
        
        result = mapper.validate_parameter_compatibility(ai_params)
        
        assert result.is_valid is False
        assert len(result.errors) >= 4
        assert any('must be >= 1' in error for error in result.errors)
        assert any('must be <= 9' in error for error in result.errors)
    
    def test_validate_redis_url_format(self):
        """Test validation of Redis URL format."""
        mapper = CacheParameterMapper()
        
        # Valid URLs
        valid_urls = [
            'redis://localhost:6379',
            'rediss://secure-redis:6380',
            'unix:///tmp/redis.sock'
        ]
        
        for url in valid_urls:
            ai_params = {'redis_url': url}
            result = mapper.validate_parameter_compatibility(ai_params)
            assert result.is_valid is True, f"URL {url} should be valid"
        
        # Invalid URLs
        invalid_urls = [
            'http://localhost:6379',
            'localhost:6379',
            'invalid_url'
        ]
        
        for url in invalid_urls:
            ai_params = {'redis_url': url}
            result = mapper.validate_parameter_compatibility(ai_params)
            assert result.is_valid is False, f"URL {url} should be invalid"
            assert any('valid Redis URL' in error for error in result.errors)
    
    def test_validate_text_size_tiers(self):
        """Test validation of text size tiers configuration."""
        mapper = CacheParameterMapper()
        
        # Valid text size tiers
        valid_tiers = {
            'small': 100,
            'medium': 1000,
            'large': 10000
        }
        ai_params = {'text_size_tiers': valid_tiers}
        result = mapper.validate_parameter_compatibility(ai_params)
        assert result.is_valid is True
        
        # Missing required tier
        invalid_tiers = {
            'small': 100,
            'large': 10000  # Missing 'medium'
        }
        ai_params = {'text_size_tiers': invalid_tiers}
        result = mapper.validate_parameter_compatibility(ai_params)
        assert result.is_valid is False
        assert any('missing required tiers' in error for error in result.errors)
        
        # Invalid tier ordering
        invalid_order_tiers = {
            'small': 1000,
            'medium': 100,  # Wrong order: should be > small
            'large': 10000
        }
        ai_params = {'text_size_tiers': invalid_order_tiers}
        result = mapper.validate_parameter_compatibility(ai_params)
        assert result.is_valid is False
        assert any('must be ordered' in error for error in result.errors)
    
    def test_validate_operation_ttls(self):
        """Test validation of operation TTL configuration."""
        mapper = CacheParameterMapper()
        
        # Valid operation TTLs
        valid_ttls = {
            'summarize': 7200,
            'sentiment': 86400,
            'qa': 1800
        }
        ai_params = {'operation_ttls': valid_ttls}
        result = mapper.validate_parameter_compatibility(ai_params)
        assert result.is_valid is True
        
        # Invalid TTL values
        invalid_ttls = {
            'summarize': -100,  # Negative
            'sentiment': 'not_an_integer',  # Wrong type
            'qa': 86400 * 400  # Very large (should warn)
        }
        ai_params = {'operation_ttls': invalid_ttls}
        result = mapper.validate_parameter_compatibility(ai_params)
        assert result.is_valid is False
        assert len(result.errors) >= 2  # Negative and wrong type
        assert len(result.warnings) >= 1  # Very large value
    
    def test_validate_parameter_conflicts(self):
        """Test detection of parameter conflicts."""
        mapper = CacheParameterMapper()
        
        # Conflict: memory_cache_size and l1_cache_size with different values
        ai_params = {
            'memory_cache_size': 100,
            'l1_cache_size': 200
        }
        
        result = mapper.validate_parameter_compatibility(ai_params)
        
        assert result.is_valid is False
        assert 'memory_cache_size' in result.parameter_conflicts
        assert any('conflicts with l1_cache_size' in error for error in result.errors)
    
    def test_validate_l1_cache_consistency(self):
        """Test L1 cache configuration consistency checks."""
        mapper = CacheParameterMapper()
        
        # Warning: L1 cache disabled but size specified
        ai_params = {
            'enable_l1_cache': False,
            'l1_cache_size': 100
        }
        
        result = mapper.validate_parameter_compatibility(ai_params)
        
        assert result.is_valid is True  # Just a warning, not an error
        assert len(result.warnings) >= 1
        assert any('L1 cache is disabled' in warning for warning in result.warnings)
    
    def test_validate_compression_consistency(self):
        """Test compression configuration consistency checks."""
        mapper = CacheParameterMapper()
        
        # Warning: compression disabled but high compression level
        ai_params = {
            'compression_threshold': 0,  # Compression disabled
            'compression_level': 9  # High compression level
        }
        
        result = mapper.validate_parameter_compatibility(ai_params)
        
        assert result.is_valid is True  # Just a warning, not an error
        assert len(result.warnings) >= 1
        assert any('compression_level' in warning for warning in result.warnings)
    
    def test_validate_with_recommendations(self):
        """Test that appropriate recommendations are generated."""
        mapper = CacheParameterMapper()
        ai_params = {
            'memory_cache_size': 100,  # Should recommend l1_cache_size
            'compression_threshold': 20000,  # Should recommend lower value
            'compression_level': 9,  # Should recommend lower level
            'text_hash_threshold': 500  # Different from compression_threshold
        }
        
        result = mapper.validate_parameter_compatibility(ai_params)
        
        # Check that we have the expected number of recommendations
        assert len(result.recommendations) >= 3
        
        # Should recommend using l1_cache_size instead of memory_cache_size
        assert any('l1_cache_size' in rec for rec in result.recommendations)
        
        # Should recommend lower compression threshold
        assert any('compression threshold' in rec.lower() for rec in result.recommendations)
        
        # Should recommend lower compression level
        assert any('compression level' in rec.lower() for rec in result.recommendations)
    
    def test_validate_empty_parameters(self):
        """Test validation with empty parameter dictionary."""
        mapper = CacheParameterMapper()
        ai_params = {}
        
        result = mapper.validate_parameter_compatibility(ai_params)
        
        assert result.is_valid is True
        assert len(result.errors) == 0
        assert result.context['total_parameters'] == 0
    
    @patch('app.infrastructure.cache.parameter_mapping.logger')
    def test_validate_exception_handling(self, mock_logger):
        """Test exception handling in parameter validation."""
        mapper = CacheParameterMapper()
        
        # Mock a validation method to raise an exception
        original_validate = mapper._validate_single_parameter
        
        def failing_validate(*args, **kwargs):
            raise ValueError("Simulated validation failure")
        
        mapper._validate_single_parameter = failing_validate
        
        ai_params = {'redis_url': 'redis://localhost:6379'}
        result = mapper.validate_parameter_compatibility(ai_params)
        
        assert result.is_valid is False
        assert any('validation failed with exception' in error for error in result.errors)
        assert 'validation_exception' in result.context


class TestParameterMapperUtilities:
    """Test cases for utility methods and parameter information."""
    
    def test_get_parameter_info(self):
        """Test getting comprehensive parameter information."""
        mapper = CacheParameterMapper()
        
        info = mapper.get_parameter_info()
        
        assert 'generic_parameters' in info
        assert 'ai_specific_parameters' in info
        assert 'parameter_mappings' in info
        assert 'parameter_conflicts' in info
        assert 'validation_rules' in info
        assert 'total_parameters' in info
        
        # Verify structure
        assert isinstance(info['generic_parameters'], list)
        assert isinstance(info['ai_specific_parameters'], list)
        assert isinstance(info['parameter_mappings'], dict)
        assert isinstance(info['validation_rules'], dict)
        assert isinstance(info['total_parameters'], int)
        
        # Verify content
        assert 'redis_url' in info['generic_parameters']
        assert 'text_hash_threshold' in info['ai_specific_parameters']
        assert info['parameter_mappings'].get('memory_cache_size') == 'l1_cache_size'
    
    def test_get_parameter_info_sorted(self):
        """Test that parameter lists are sorted for consistency."""
        mapper = CacheParameterMapper()
        
        info = mapper.get_parameter_info()
        
        # Lists should be sorted
        assert info['generic_parameters'] == sorted(info['generic_parameters'])
        assert info['ai_specific_parameters'] == sorted(info['ai_specific_parameters'])
    
    def test_parameter_classification_completeness(self):
        """Test that all parameters are classified correctly."""
        mapper = CacheParameterMapper()
        
        info = mapper.get_parameter_info()
        generic_set = set(info['generic_parameters'])
        ai_specific_set = set(info['ai_specific_parameters'])
        
        # Sets should not overlap
        assert generic_set.isdisjoint(ai_specific_set)
        
        # All validation rules should be for classified parameters or mapped parameters
        validated_params = set(info['validation_rules'].keys())
        mapped_params = set(info['parameter_mappings'].keys())
        classified_params = generic_set | ai_specific_set | mapped_params
        
        # All validated parameters should be classified
        unclassified_params = validated_params - classified_params
        assert len(unclassified_params) == 0, f"Unclassified validated parameters: {unclassified_params}"


class TestIntegrationScenarios:
    """Test integration scenarios for cache inheritance."""
    
    def test_ai_response_cache_parameter_mapping(self):
        """Test parameter mapping for typical AIResponseCache initialization."""
        mapper = CacheParameterMapper()
        
        # Typical AIResponseCache parameters
        ai_params = {
            'redis_url': 'redis://localhost:6379',
            'default_ttl': 3600,
            'text_hash_threshold': 1000,
            'compression_threshold': 1000,
            'compression_level': 6,
            'text_size_tiers': {
                'small': 500,
                'medium': 5000,
                'large': 50000
            },
            'memory_cache_size': 100,
            'operation_ttls': {
                'summarize': 7200,
                'sentiment': 86400,
                'key_points': 7200,
                'questions': 3600,
                'qa': 1800
            }
        }
        
        # Test mapping
        generic_params, ai_specific_params = mapper.map_ai_to_generic_params(ai_params)
        
        # Verify generic parameters for GenericRedisCache
        assert 'redis_url' in generic_params
        assert 'default_ttl' in generic_params
        assert 'compression_threshold' in generic_params
        assert 'compression_level' in generic_params
        assert 'l1_cache_size' in generic_params
        assert 'enable_l1_cache' in generic_params
        assert generic_params['l1_cache_size'] == 100
        assert generic_params['enable_l1_cache'] is True
        
        # Verify AI-specific parameters
        assert 'text_hash_threshold' in ai_specific_params
        assert 'text_size_tiers' in ai_specific_params
        assert 'operation_ttls' in ai_specific_params
        
        # Test validation
        result = mapper.validate_parameter_compatibility(ai_params)
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_generic_redis_cache_parameter_compatibility(self):
        """Test that GenericRedisCache parameters work correctly."""
        mapper = CacheParameterMapper()
        
        # Typical GenericRedisCache parameters
        generic_cache_params = {
            'redis_url': 'redis://localhost:6379',
            'default_ttl': 7200,
            'enable_l1_cache': True,
            'l1_cache_size': 200,
            'compression_threshold': 2000,
            'compression_level': 8
        }
        
        # Test mapping
        generic_params, ai_specific_params = mapper.map_ai_to_generic_params(generic_cache_params)
        
        # All should be generic parameters
        assert generic_params == generic_cache_params
        assert ai_specific_params == {}
        
        # Test validation
        result = mapper.validate_parameter_compatibility(generic_cache_params)
        assert result.is_valid is True
        assert len(result.generic_params) == len(generic_cache_params)
        assert len(result.ai_specific_params) == 0
    
    def test_mixed_parameter_inheritance_scenario(self):
        """Test mixed parameters for inheritance scenario."""
        mapper = CacheParameterMapper()
        
        # Mixed parameters: some from parent, some AI-specific
        mixed_params = {
            # From GenericRedisCache (parent)
            'redis_url': 'redis://production:6379',
            'enable_l1_cache': True,
            'compression_threshold': 1500,
            
            # AI-specific (child)
            'text_hash_threshold': 800,
            'operation_ttls': {'summarize': 10800},
            
            # Mapped parameter
            'memory_cache_size': 150
        }
        
        # Test mapping
        generic_params, ai_specific_params = mapper.map_ai_to_generic_params(mixed_params)
        
        # Verify correct separation
        expected_generic = {
            'redis_url': 'redis://production:6379',
            'enable_l1_cache': True,
            'compression_threshold': 1500,
            'l1_cache_size': 150  # Mapped from memory_cache_size
        }
        expected_ai_specific = {
            'text_hash_threshold': 800,
            'operation_ttls': {'summarize': 10800}
        }
        
        assert generic_params == expected_generic
        assert ai_specific_params == expected_ai_specific
        
        # Test validation
        result = mapper.validate_parameter_compatibility(mixed_params)
        assert result.is_valid is True
    
    def test_backward_compatibility_scenario(self):
        """Test backward compatibility with existing AIResponseCache usage."""
        mapper = CacheParameterMapper()
        
        # Legacy AIResponseCache parameters that should still work
        legacy_params = {
            'redis_url': 'redis://legacy:6379',
            'default_ttl': 3600,
            'text_hash_threshold': 1000,
            'memory_cache_size': 100,  # Legacy parameter name
            'compression_threshold': 1000,
            'compression_level': 6
        }
        
        # Test mapping preserves functionality
        generic_params, ai_specific_params = mapper.map_ai_to_generic_params(legacy_params)
        
        # Should map memory_cache_size to l1_cache_size
        assert 'l1_cache_size' in generic_params
        assert 'memory_cache_size' not in generic_params
        assert generic_params['l1_cache_size'] == 100
        
        # Should include AI-specific parameters
        assert 'text_hash_threshold' in ai_specific_params
        
        # Should validate successfully
        result = mapper.validate_parameter_compatibility(legacy_params)
        assert result.is_valid is True
        
        # Should recommend using l1_cache_size
        assert any('l1_cache_size' in rec for rec in result.recommendations)


@pytest.fixture
def sample_ai_params():
    """Fixture providing sample AI cache parameters for testing."""
    return {
        'redis_url': 'redis://localhost:6379',
        'default_ttl': 3600,
        'text_hash_threshold': 1000,
        'compression_threshold': 1000,
        'memory_cache_size': 100
    }


@pytest.fixture
def mapper():
    """Fixture providing a CacheParameterMapper instance."""
    return CacheParameterMapper()


def test_parameter_mapping_module_imports():
    """Test that all expected classes and functions can be imported."""
    from app.infrastructure.cache.parameter_mapping import (
        ValidationResult,
        CacheParameterMapper
    )
    
    # Verify classes can be instantiated
    result = ValidationResult()
    mapper = CacheParameterMapper()
    
    assert isinstance(result, ValidationResult)
    assert isinstance(mapper, CacheParameterMapper)


if __name__ == '__main__':
    pytest.main([__file__])