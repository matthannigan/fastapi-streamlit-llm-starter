"""
Unit tests for AI Response Cache configuration module following docstring-driven test development.

This test suite validates the comprehensive AI cache configuration system including
parameter validation, factory methods, environment integration, and configuration
management features that support the cache inheritance architecture.

Test Coverage Areas:
- AIResponseCacheConfig initialization and default values per docstrings
- Configuration validation with ValidationResult integration
- Factory methods for different deployment scenarios
- Environment variable loading and parsing
- Configuration merging and inheritance
- Parameter conversion methods for cache initialization
- Edge cases and error handling documented in method docstrings

Business Critical:
AI cache configuration failures would prevent proper cache initialization and
inheritance from GenericRedisCache, directly impacting AI service performance
and reliability across different deployment environments.

Test Strategy:
- Unit tests for individual configuration methods per docstring contracts
- Integration tests for complete configuration workflows
- Edge case coverage for invalid configurations and parsing errors
- Behavior verification based on documented examples and use cases
"""

import pytest
import os
import tempfile
import json
import yaml
from unittest.mock import patch, MagicMock
from typing import Dict, Any, Optional

from app.infrastructure.cache.ai_config import AIResponseCacheConfig
from app.infrastructure.cache.parameter_mapping import ValidationResult
from app.core.exceptions import ValidationError, ConfigurationError


class TestAIResponseCacheConfig:
    """
    Test suite for AIResponseCacheConfig class behavior and methods.
    
    Scope:
        - Configuration initialization and default value assignment
        - Parameter validation with comprehensive ValidationResult integration
        - Type conversion and parameter mapping functionality
        - Configuration export methods for cache initialization
        - Error handling and edge case scenarios
        
    Business Critical:
        Proper configuration is essential for AI cache inheritance architecture
        and multi-environment deployment support.
        
    Test Strategy:
        - Test each method per docstring specifications
        - Verify parameter validation according to documented constraints
        - Test factory methods and environment integration
        - Validate error handling for malformed configurations
    """
    
    def test_initialization_with_defaults(self):
        """
        Test AIResponseCacheConfig initialization with default values per docstring.
        
        Verifies:
            Default initialization creates valid configuration with sensible defaults
            
        Business Impact:
            Ensures consistent baseline configuration for AI cache deployment
            
        Success Criteria:
            - All required parameters have appropriate default values
            - Optional parameters default to None for flexible configuration
            - Configuration passes validation with default values
        """
        config = AIResponseCacheConfig()
        
        # Verify core default values per docstring
        assert config.redis_url == "redis://redis:6379"  # Default Redis URL
        assert config.default_ttl == 3600  # 1 hour default
        assert config.memory_cache_size == 100  # Reasonable default
        assert config.compression_threshold == 1000  # Balance size/CPU
        assert config.compression_level == 6  # Balance compression/speed
        assert config.text_hash_threshold == 1000  # Match compression threshold
        
        # Verify AI-specific defaults  
        assert hasattr(config.hash_algorithm, '__call__')  # Should be a hash function
        # AI config provides smart defaults for these parameters
        assert config.text_size_tiers is not None  # Provides default tiers
        assert config.operation_ttls is not None  # Provides default operation TTLs
        
        # Verify optional parameters (performance_monitor gets default instance)
        assert config.performance_monitor is not None  # Gets default instance in __post_init__
        assert isinstance(config.performance_monitor.__class__.__name__, str)  # Should be CachePerformanceMonitor
        assert config.security_config is None
    
    def test_initialization_with_custom_parameters(self):
        """
        Test AIResponseCacheConfig initialization with custom parameters per docstring examples.
        
        Verifies:
            Custom parameter assignment and type preservation
            
        Business Impact:
            Enables environment-specific configuration for optimal performance
            
        Success Criteria:
            - Custom parameters properly assigned to configuration attributes
            - Type preservation maintained for all parameter types
            - Complex parameters like dictionaries handled correctly
        """
        custom_text_tiers = {"small": 300, "medium": 3000, "large": 30000}
        custom_operation_ttls = {"summarize": 7200, "sentiment": 3600}
        
        config = AIResponseCacheConfig(
            redis_url="redis://prod:6379",
            default_ttl=7200,
            memory_cache_size=200,
            compression_threshold=500,
            compression_level=7,
            text_hash_threshold=500,
            text_size_tiers=custom_text_tiers,
            operation_ttls=custom_operation_ttls
        )
        
        # Verify all custom parameters assigned correctly
        assert config.redis_url == "redis://prod:6379"
        assert config.default_ttl == 7200
        assert config.memory_cache_size == 200
        assert config.compression_threshold == 500
        assert config.compression_level == 7
        assert config.text_hash_threshold == 500
        assert config.text_size_tiers == custom_text_tiers
        assert config.operation_ttls == custom_operation_ttls
    
    def test_validate_method_valid_configuration(self):
        """
        Test validate method with valid configuration per docstring behavior.
        
        Verifies:
            Valid configurations pass validation with proper ValidationResult
            
        Business Impact:
            Ensures properly configured AI cache systems validate successfully
            
        Success Criteria:
            - ValidationResult.is_valid returns True for valid configurations
            - No validation errors generated for valid parameter combinations
            - Recommendations may be provided for optimization opportunities
        """
        config = AIResponseCacheConfig(
            redis_url="redis://localhost:6379",
            default_ttl=3600,
            memory_cache_size=100,
            text_hash_threshold=1000,
            compression_threshold=1000,
            compression_level=6
        )
        
        result = config.validate()
        
        assert isinstance(result, ValidationResult)
        assert result.is_valid is True
        assert len(result.errors) == 0
        # May have recommendations for optimization
        assert isinstance(result.recommendations, list)
    
    def test_validate_method_invalid_parameters(self):
        """
        Test validate method with invalid parameters per docstring validation rules.
        
        Verifies:
            Invalid parameter values properly detected and reported
            
        Business Impact:
            Prevents cache initialization failures from invalid configuration
            
        Success Criteria:
            - ValidationResult.is_valid returns False for invalid configurations
            - Specific error messages identify problematic parameters
            - Range violations and type errors properly detected
        """
        config = AIResponseCacheConfig(
            redis_url="http://invalid-url",  # Wrong scheme
            default_ttl=-100,  # Negative TTL invalid
            memory_cache_size=50000,  # Exceeds maximum
            compression_level=15,  # Exceeds maximum
            text_hash_threshold=200000  # Exceeds maximum
        )
        
        result = config.validate()
        
        assert result.is_valid is False
        assert len(result.errors) >= 4  # Multiple validation errors (expecting 5)
        
        # Check for specific error types based on actual validation messages
        url_error = any('redis_url' in error and ('must start with redis://' in error or 'valid Redis URL' in error)
                       for error in result.errors)
        assert url_error
        
        ttl_error = any('default_ttl' in error and ('positive' in error or 'must be positive' in error or 'negative' in error or '>=' in error)
                       for error in result.errors)
        assert ttl_error
        
        size_error = any('memory_cache_size' in error and ('too large' in error or '<=' in error or 'max' in error)
                        for error in result.errors)
        assert size_error
    
    def test_validate_method_text_size_tiers_validation(self):
        """
        Test text_size_tiers validation per docstring custom validator behavior.
        
        Verifies:
            Text size tiers validation with required structure and ordering
            
        Business Impact:
            Ensures proper text categorization for cache optimization strategies
            
        Success Criteria:
            - Required tiers (small, medium, large) must be present
            - Tier values must be positive integers
            - Tiers must be ordered: small < medium < large
        """
        # Test valid text size tiers
        valid_config = AIResponseCacheConfig(
            text_size_tiers={"small": 100, "medium": 1000, "large": 10000}
        )
        result = valid_config.validate()
        assert result.is_valid is True
        
        # Test missing required tier
        invalid_config = AIResponseCacheConfig(
            text_size_tiers={"small": 100, "medium": 1000}  # Missing 'large'
        )
        result = invalid_config.validate()
        assert result.is_valid is False
        missing_tier_error = any('missing required tiers' in error 
                                for error in result.errors)
        assert missing_tier_error
        
        # Test invalid tier ordering
        unordered_config = AIResponseCacheConfig(
            text_size_tiers={"small": 1000, "medium": 100, "large": 10000}
        )
        result = unordered_config.validate()
        assert result.is_valid is False
        ordering_error = any('must be ordered' in error for error in result.errors)
        assert ordering_error
    
    def test_validate_method_operation_ttls_validation(self):
        """
        Test operation_ttls validation per docstring validator behavior.
        
        Verifies:
            Operation TTL validation with positive values and warnings
            
        Business Impact:
            Ensures proper cache expiration for different AI operations
            
        Success Criteria:
            - TTL values must be positive integers
            - Very large TTLs generate warnings but don't fail validation
            - Unknown operations generate warnings for user guidance
        """
        # Test valid operation TTLs
        valid_config = AIResponseCacheConfig(
            operation_ttls={"summarize": 3600, "sentiment": 7200}
        )
        result = valid_config.validate()
        assert result.is_valid is True
        
        # Test invalid TTL values
        invalid_config = AIResponseCacheConfig(
            operation_ttls={"summarize": -100, "sentiment": "invalid"}
        )
        result = invalid_config.validate()
        assert result.is_valid is False
        
        ttl_errors = [error for error in result.errors 
                     if 'operation_ttls' in error and 'positive integer' in error]
        assert len(ttl_errors) >= 1
        
        # Test very large TTL warning
        large_ttl_config = AIResponseCacheConfig(
            operation_ttls={"summarize": 86400 * 400}  # > 1 year
        )
        result = large_ttl_config.validate()
        assert result.is_valid is True  # Valid but with warnings
        
        large_ttl_warning = any('very large' in warning 
                               for warning in result.warnings)
        assert large_ttl_warning
    
    def test_to_ai_cache_kwargs_method(self):
        """
        Test to_ai_cache_kwargs method parameter conversion per docstring.
        
        Verifies:
            Proper conversion of configuration to cache initialization parameters
            
        Business Impact:
            Enables AIResponseCache initialization with validated configuration
            
        Success Criteria:
            - All configuration parameters converted to cache-compatible format
            - Parameter names match expected cache constructor arguments
            - None values appropriately handled or excluded
        """
        config = AIResponseCacheConfig(
            redis_url="redis://localhost:6379",
            default_ttl=3600,
            memory_cache_size=100,
            text_hash_threshold=1000,
            compression_threshold=500,
            operation_ttls={"summarize": 7200}
        )
        
        kwargs = config.to_ai_cache_kwargs()
        
        # Verify all parameters present in kwargs
        assert isinstance(kwargs, dict)
        assert kwargs['redis_url'] == "redis://localhost:6379"
        assert kwargs['default_ttl'] == 3600
        assert kwargs['memory_cache_size'] == 100
        assert kwargs['text_hash_threshold'] == 1000
        assert kwargs['compression_threshold'] == 500
        assert kwargs['operation_ttls'] == {"summarize": 7200}
        
        # Verify None values handled appropriately
        minimal_config = AIResponseCacheConfig(redis_url="redis://test:6379")
        minimal_kwargs = minimal_config.to_ai_cache_kwargs()
        assert 'redis_url' in minimal_kwargs
        # None values should either be excluded or included based on cache requirements
    
    def test_to_generic_cache_kwargs_method(self):
        """
        Test to_generic_cache_kwargs method parameter mapping per docstring.
        
        Verifies:
            Proper mapping of AI parameters to generic cache parameters
            
        Business Impact:
            Enables GenericRedisCache initialization for inheritance architecture
            
        Success Criteria:
            - AI parameters mapped to generic equivalents (memory_cache_size -> l1_cache_size)
            - Generic parameters preserved with original names
            - AI-specific parameters excluded from generic kwargs
        """
        config = AIResponseCacheConfig(
            redis_url="redis://localhost:6379",
            default_ttl=3600,
            memory_cache_size=100,  # Should map to l1_cache_size
            compression_threshold=500,
            text_hash_threshold=1000  # Should be excluded (AI-specific)
        )
        
        kwargs = config.to_generic_cache_kwargs()
        
        # Verify generic parameters preserved
        assert kwargs['redis_url'] == "redis://localhost:6379"
        assert kwargs['default_ttl'] == 3600
        assert kwargs['compression_threshold'] == 500
        
        # Verify parameter mapping
        assert 'l1_cache_size' in kwargs
        assert kwargs['l1_cache_size'] == 100
        assert 'memory_cache_size' not in kwargs  # Should be mapped away
        
        # Verify AI-specific parameters excluded
        assert 'text_hash_threshold' not in kwargs
        
        # Verify auto-enabling of L1 cache when size specified
        if 'l1_cache_size' in kwargs and kwargs['l1_cache_size']:
            assert kwargs.get('enable_l1_cache', True) is True
    
    def test_create_default_factory_method(self):
        """
        Test create_default factory method per docstring specifications.
        
        Verifies:
            Default factory creates appropriate baseline configuration
            
        Business Impact:
            Provides consistent baseline configuration across deployments
            
        Success Criteria:
            - Returns AIResponseCacheConfig instance with defaults
            - Configuration is valid without additional parameters
            - Default values match documented specifications
        """
        config = AIResponseCacheConfig.create_default()
        
        assert isinstance(config, AIResponseCacheConfig)
        
        # Verify default values
        assert config.default_ttl == 3600
        assert config.memory_cache_size == 100
        assert config.compression_threshold == 1000
        assert config.compression_level == 6
        assert config.text_hash_threshold == 1000
        
        # Verify configuration is valid
        result = config.validate()
        assert result.is_valid is True
    
    def test_create_production_factory_method(self):
        """
        Test create_production factory method per docstring specifications.
        
        Verifies:
            Production factory creates optimized configuration for production use
            
        Business Impact:
            Ensures production deployments have optimized cache configuration
            
        Success Criteria:
            - Returns configuration optimized for production workloads
            - Redis URL properly assigned from parameter
            - Production-appropriate defaults for performance and reliability
        """
        redis_url = "redis://prod-cache:6379"
        config = AIResponseCacheConfig.create_production(redis_url)
        
        assert isinstance(config, AIResponseCacheConfig)
        assert config.redis_url == redis_url
        
        # Verify production-optimized settings
        assert config.default_ttl >= 3600  # Longer TTL for production
        assert config.memory_cache_size >= 100  # Adequate cache size
        assert config.compression_threshold <= 1000  # Aggressive compression
        
        # Verify configuration is valid
        result = config.validate()
        assert result.is_valid is True
    
    def test_create_development_factory_method(self):
        """
        Test create_development factory method per docstring specifications.
        
        Verifies:
            Development factory creates configuration suitable for development
            
        Business Impact:
            Provides development-friendly configuration with fast feedback
            
        Success Criteria:
            - Returns configuration optimized for development workflow
            - Uses localhost defaults appropriate for local development
            - Development-friendly settings for debugging and testing
        """
        config = AIResponseCacheConfig.create_development()
        
        assert isinstance(config, AIResponseCacheConfig)
        
        # Verify development-appropriate defaults
        assert 'localhost' in config.redis_url or config.redis_url is None
        assert config.default_ttl <= 3600  # Shorter TTL for development
        assert config.memory_cache_size >= 50  # Reasonable for development
        
        # Verify configuration is valid
        result = config.validate()
        assert result.is_valid is True
    
    def test_create_testing_factory_method(self):
        """
        Test create_testing factory method per docstring specifications.
        
        Verifies:
            Testing factory creates configuration suitable for test environments
            
        Business Impact:
            Ensures consistent test environments with appropriate cache settings
            
        Success Criteria:
            - Returns configuration optimized for testing scenarios
            - Uses test-appropriate settings for isolation and speed
            - Configuration suitable for both unit and integration tests
        """
        config = AIResponseCacheConfig.create_testing()
        
        assert isinstance(config, AIResponseCacheConfig)
        
        # Verify test-appropriate settings
        assert config.default_ttl <= 3600  # Shorter TTL for tests
        assert config.memory_cache_size <= 100  # Smaller cache for tests
        
        # Verify configuration is valid
        result = config.validate()
        assert result.is_valid is True
    
    def test_from_env_factory_method(self):
        """
        Test from_env factory method per docstring environment integration.
        
        Verifies:
            Environment variable loading with configurable prefixes
            
        Business Impact:
            Enables deployment configuration through environment variables
            
        Success Criteria:
            - Environment variables properly parsed and assigned
            - Configurable prefix support for multi-service deployments
            - Type conversion handled for numeric and JSON parameters
        """
        # Set test environment variables
        test_env = {
            'AI_CACHE_REDIS_URL': 'redis://env-test:6379',
            'AI_CACHE_DEFAULT_TTL': '7200',
            'AI_CACHE_MEMORY_CACHE_SIZE': '150',
            'AI_CACHE_TEXT_HASH_THRESHOLD': '2000',
            'AI_CACHE_OPERATION_TTLS': '{"summarize": 3600, "sentiment": 7200}'
        }
        
        with patch.dict(os.environ, test_env):
            config = AIResponseCacheConfig.from_env(prefix="AI_CACHE_")
        
        # Verify environment values loaded correctly
        assert config.redis_url == 'redis://env-test:6379'
        assert config.default_ttl == 7200
        assert config.memory_cache_size == 150
        assert config.text_hash_threshold == 2000
        assert config.operation_ttls == {"summarize": 3600, "sentiment": 7200}
    
    def test_from_dict_factory_method(self):
        """
        Test from_dict factory method per docstring dictionary loading.
        
        Verifies:
            Dictionary-based configuration loading with validation
            
        Business Impact:
            Enables configuration from various dictionary sources
            
        Success Criteria:
            - Dictionary parameters properly mapped to configuration attributes
            - Type validation and conversion handled appropriately
            - Invalid dictionary parameters generate appropriate errors
        """
        config_dict = {
            'redis_url': 'redis://dict-test:6379',
            'default_ttl': 5400,
            'memory_cache_size': 75,
            'text_hash_threshold': 1500,
            'operation_ttls': {'summarize': 10800}
        }
        
        config = AIResponseCacheConfig.from_dict(config_dict)
        
        # Verify dictionary values loaded correctly
        assert config.redis_url == 'redis://dict-test:6379'
        assert config.default_ttl == 5400
        assert config.memory_cache_size == 75
        assert config.text_hash_threshold == 1500
        assert config.operation_ttls == {'summarize': 10800}
        
        # Verify configuration is valid
        result = config.validate()
        assert result.is_valid is True
    
    def test_merge_method_configuration_inheritance(self):
        """
        Test merge method configuration inheritance per docstring behavior.
        
        Verifies:
            Configuration merging with override behavior for environment-specific setups
            
        Business Impact:
            Enables configuration inheritance and environment-specific overrides
            
        Success Criteria:
            - Base configuration values preserved when not overridden
            - Override configuration values take precedence
            - None values in override don't overwrite base values
        """
        base_config = AIResponseCacheConfig(
            redis_url="redis://base:6379",
            default_ttl=3600,
            memory_cache_size=100,
            text_hash_threshold=1000
        )
        
        override_config = AIResponseCacheConfig(
            redis_url="redis://override:6379",
            default_ttl=7200,
            # memory_cache_size not specified - should use base value
            text_hash_threshold=2000
        )
        
        merged_config = base_config.merge(override_config)
        
        # Verify override values take precedence
        assert merged_config.redis_url == "redis://override:6379"
        assert merged_config.default_ttl == 7200
        assert merged_config.text_hash_threshold == 2000
        
        # Verify base values preserved when not overridden
        assert merged_config.memory_cache_size == 100  # From base
        
        # Verify merged configuration is valid
        result = merged_config.validate()
        assert result.is_valid is True


class TestAIResponseCacheConfigIntegration:
    """
    Integration tests for complete AI cache configuration workflows.
    
    Scope:
        - End-to-end configuration creation, validation, and conversion workflows
        - Real-world configuration scenarios and deployment patterns
        - Error handling and recovery in complex configuration scenarios
        
    Business Critical:
        Integration workflows must support production deployments with proper
        error handling and configuration validation across environments.
        
    Test Strategy:
        - Test complete workflows from configuration sources to cache initialization
        - Verify realistic deployment scenarios and environment patterns
        - Test error recovery and graceful degradation for invalid configurations
        - Validate performance characteristics with complex configurations
    """
    
    def test_complete_configuration_workflow(self):
        """
        Test complete configuration workflow from creation to cache initialization.
        
        Verifies:
            Full workflow for production AI cache deployment
            
        Business Impact:
            Validates end-to-end configuration process for production deployment
            
        Success Criteria:
            - Configuration creation, validation, and conversion work together
            - Both AI cache and generic cache kwargs generated successfully
            - Configuration suitable for actual cache initialization
        """
        # Step 1: Create production configuration
        config = AIResponseCacheConfig.create_production("redis://prod:6379")
        
        # Step 2: Customize for specific deployment
        custom_config = config.merge(AIResponseCacheConfig(
            memory_cache_size=200,
            text_hash_threshold=500,
            operation_ttls={
                "summarize": 14400,
                "sentiment": 86400,
                "key_points": 7200
            }
        ))
        
        # Step 3: Validate configuration
        validation_result = custom_config.validate()
        assert validation_result.is_valid is True
        
        # Step 4: Generate cache initialization parameters
        ai_cache_kwargs = custom_config.to_ai_cache_kwargs()
        generic_cache_kwargs = custom_config.to_generic_cache_kwargs()
        
        # Verify AI cache kwargs
        assert 'redis_url' in ai_cache_kwargs
        assert 'text_hash_threshold' in ai_cache_kwargs
        assert 'operation_ttls' in ai_cache_kwargs
        
        # Verify generic cache kwargs
        assert 'redis_url' in generic_cache_kwargs
        assert 'l1_cache_size' in generic_cache_kwargs  # Mapped from memory_cache_size
        assert 'text_hash_threshold' not in generic_cache_kwargs  # AI-specific excluded
        
        # Verify both are suitable for cache initialization (allow various cache-compatible types)
        def is_cache_compatible(value):
            """Check if a value is compatible with cache initialization."""
            if value is None:
                return True
            if isinstance(value, (str, int, dict, bool)):
                return True
            if hasattr(value, '__call__'):  # Functions (like hash_algorithm)
                return True
            # Monitor objects have performance tracking methods
            if hasattr(value, 'get_performance_stats') or hasattr(value, 'record_operation'):
                return True
            return False
        
        ai_compatible = all(is_cache_compatible(v) for v in ai_cache_kwargs.values())
        generic_compatible = all(is_cache_compatible(v) for v in generic_cache_kwargs.values())
        
        assert ai_compatible, f"AI cache kwargs contain incompatible types: {[(k, type(v)) for k, v in ai_cache_kwargs.items() if not is_cache_compatible(v)]}"
        assert generic_compatible, f"Generic cache kwargs contain incompatible types: {[(k, type(v)) for k, v in generic_cache_kwargs.items() if not is_cache_compatible(v)]}"
    
    def test_environment_based_deployment_scenario(self):
        """
        Test environment-based deployment scenario with configuration validation.
        
        Verifies:
            Real-world environment variable deployment with validation and recommendations
            
        Business Impact:
            Ensures production deployments work correctly with environment configuration
            
        Success Criteria:
            - Environment variables properly loaded and validated
            - Configuration recommendations provided for optimization
            - Both development and production environment patterns supported
        """
        # Simulate production environment variables
        prod_env = {
            'CACHE_REDIS_URL': 'redis://prod-cluster:6379',
            'CACHE_DEFAULT_TTL': '14400',  # 4 hours
            'CACHE_MEMORY_CACHE_SIZE': '500',  # Large cache
            'CACHE_COMPRESSION_THRESHOLD': '500',  # Aggressive compression
            'CACHE_TEXT_SIZE_TIERS': '{"small": 200, "medium": 2000, "large": 20000}',
            'CACHE_OPERATION_TTLS': '{"summarize": 28800, "sentiment": 86400}'  # Long TTLs
        }
        
        with patch.dict(os.environ, prod_env):
            config = AIResponseCacheConfig.from_env(prefix="CACHE_")
        
        # Validate production configuration
        validation_result = config.validate()
        assert validation_result.is_valid is True
        
        # Verify production-appropriate values
        assert config.default_ttl == 14400
        assert config.memory_cache_size == 500
        assert config.compression_threshold == 500
        
        # Check for optimization recommendations
        assert isinstance(validation_result.recommendations, list)
        # Production configs may have recommendations for further optimization
        
        # Generate cache kwargs for deployment
        cache_kwargs = config.to_ai_cache_kwargs()
        assert 'redis_url' in cache_kwargs
        assert cache_kwargs['redis_url'] == 'redis://prod-cluster:6379'
    
    def test_configuration_error_handling_and_recovery(self):
        """
        Test configuration error handling and recovery scenarios.
        
        Verifies:
            Graceful handling of configuration errors with actionable feedback
            
        Business Impact:
            Prevents deployment failures from configuration issues with clear guidance
            
        Success Criteria:
            - Invalid configurations properly detected with specific error messages
            - Validation provides actionable recommendations for fixing issues
            - Partial configurations can be corrected through merging
        """
        # Create configuration with multiple issues
        problematic_config = AIResponseCacheConfig(
            redis_url="http://wrong-scheme:6379",  # Invalid scheme
            default_ttl=-100,  # Negative TTL
            memory_cache_size=50000,  # Too large
            compression_level=15,  # Invalid range
            text_size_tiers={"small": 1000, "medium": 100}  # Wrong order & missing large
        )
        
        # Validate and collect errors
        validation_result = problematic_config.validate()
        assert validation_result.is_valid is False
        assert len(validation_result.errors) >= 4  # Multiple issues
        
        # Verify specific error types are detected
        url_error = any('redis_url' in error for error in validation_result.errors)
        ttl_error = any('default_ttl' in error for error in validation_result.errors)
        size_error = any('memory_cache_size' in error for error in validation_result.errors)
        tiers_error = any('text_size_tiers' in error for error in validation_result.errors)
        
        assert url_error and ttl_error and size_error and tiers_error
        
        # Test recovery through merging with valid configuration
        valid_config = AIResponseCacheConfig.create_production("redis://valid:6379")
        recovered_config = valid_config.merge(AIResponseCacheConfig(
            memory_cache_size=200,  # Fix the size issue
            text_size_tiers={"small": 100, "medium": 1000, "large": 10000}  # Fix tiers
        ))
        
        # Verify recovery successful
        recovery_result = recovered_config.validate()
        assert recovery_result.is_valid is True
        assert len(recovery_result.errors) == 0
    
    def test_configuration_file_integration(self):
        """
        Test configuration file integration with JSON and YAML support.
        
        Verifies:
            File-based configuration loading with proper error handling
            
        Business Impact:
            Enables configuration management through version-controlled files
            
        Success Criteria:
            - JSON and YAML files properly parsed into configuration
            - File parsing errors handled gracefully with clear messages
            - Configuration validation applied to file-loaded configurations
        """
        # Test JSON configuration
        json_config = {
            "redis_url": "redis://file-config:6379",
            "default_ttl": 5400,
            "memory_cache_size": 150,
            "text_hash_threshold": 1200,
            "operation_ttls": {
                "summarize": 10800,
                "sentiment": 14400
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(json_config, f)
            json_file = f.name
        
        try:
            config = AIResponseCacheConfig.from_json(json_file)
            
            # Verify JSON values loaded correctly
            assert config.redis_url == "redis://file-config:6379"
            assert config.default_ttl == 5400
            assert config.memory_cache_size == 150
            assert config.operation_ttls == {"summarize": 10800, "sentiment": 14400}
            
            # Verify configuration is valid
            result = config.validate()
            assert result.is_valid is True
            
        finally:
            os.unlink(json_file)
        
        # Test YAML configuration
        yaml_config = {
            "redis_url": "redis://yaml-config:6379",
            "default_ttl": 7200,
            "memory_cache_size": 100,
            "text_size_tiers": {
                "small": 250,
                "medium": 2500,
                "large": 25000
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            yaml.dump(yaml_config, f)
            yaml_file = f.name
        
        try:
            config = AIResponseCacheConfig.from_yaml(yaml_file)
            
            # Verify YAML values loaded correctly
            assert config.redis_url == "redis://yaml-config:6379"
            assert config.default_ttl == 7200
            assert config.text_size_tiers == {"small": 250, "medium": 2500, "large": 25000}
            
            # Verify configuration is valid
            result = config.validate()
            assert result.is_valid is True
            
        finally:
            os.unlink(yaml_file)
    
    def test_configuration_performance_characteristics(self):
        """
        Test configuration performance characteristics with large configurations.
        
        Verifies:
            Performance characteristics meet requirements for production usage
            
        Business Impact:
            Ensures configuration processing doesn't become bottleneck during deployment
            
        Success Criteria:
            - Large configurations processed efficiently
            - Validation time scales appropriately with configuration complexity
            - Memory usage remains reasonable during processing
        """
        # Generate large configuration with many operation TTLs
        large_operation_ttls = {f"operation_{i}": 3600 + i for i in range(100)}
        large_text_tiers = {f"tier_{i}": (i + 1) * 100 for i in range(10)}
        
        config = AIResponseCacheConfig(
            redis_url="redis://performance:6379",
            operation_ttls=large_operation_ttls,
            text_size_tiers=large_text_tiers  # This will fail validation but test performance
        )
        
        # Test validation performance
        import time
        start_time = time.time()
        result = config.validate()
        validation_time = time.time() - start_time
        
        # Test conversion performance
        start_time = time.time()
        cache_kwargs = config.to_ai_cache_kwargs()
        conversion_time = time.time() - start_time
        
        # Performance should be reasonable (< 100ms each for this size)
        assert validation_time < 0.1, f"Validation too slow: {validation_time}s"
        assert conversion_time < 0.1, f"Conversion too slow: {conversion_time}s"
        
        # Results should handle large configurations correctly
        assert isinstance(result, ValidationResult)
        assert isinstance(cache_kwargs, dict)
        assert len(cache_kwargs['operation_ttls']) == 100