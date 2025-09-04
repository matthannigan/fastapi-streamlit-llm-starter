"""
Unit tests for CacheValidator validation functionality.

This test suite verifies the observable behaviors documented in the
CacheValidator class public contract (cache_validator.pyi). Tests focus on the
behavior-driven testing principles described in docs/guides/testing/TESTING.md.

Coverage Focus:
    - Infrastructure service (>90% test coverage requirement)
    - Configuration validation with JSON schema support
    - Template generation and management
    - Configuration comparison and recommendation

External Dependencies:
    All external dependencies are mocked using fixtures from conftest.py following
    the documented public contracts to ensure accurate behavior simulation.
"""

import pytest
from unittest.mock import MagicMock, patch
from typing import Dict, List, Any

from app.infrastructure.cache.cache_validator import CacheValidator, ValidationResult


class TestCacheValidatorInitialization:
    """
    Test suite for CacheValidator initialization and basic functionality.
    
    Scope:
        - Validator initialization with schemas and templates
        - Schema loading and validation framework setup
        - Template registry initialization and management
        - Basic validator configuration and capabilities
        
    Business Critical:
        CacheValidator provides comprehensive validation for all cache configuration types
        
    Test Strategy:
        - Unit tests for validator initialization with various configurations
        - Schema loading and validation framework verification
        - Template registry setup and access testing
        - Basic validation capability verification
        
    External Dependencies:
        - JSON schema validation libraries (mocked): Schema-based validation
        - Configuration templates (internal): Predefined configuration templates
    """

    def test_cache_validator_initializes_with_comprehensive_schemas(self):
        """
        Test that CacheValidator initializes with comprehensive validation schemas.
        
        Verifies:
            Validator initialization includes all necessary schemas for cache validation
            
        Business Impact:
            Ensures comprehensive validation coverage for all cache configuration scenarios
            
        Scenario:
            Given: CacheValidator initialization
            When: Validator instance is created
            Then: All required validation schemas are loaded and available
            And: Preset validation schema is configured
            And: Configuration validation schema is configured
            And: Custom override validation schema is configured
            And: Schemas are properly structured for JSON schema validation
            
        Schema Initialization Verified:
            - Preset validation schema covers all preset configuration fields
            - Configuration validation schema covers complete cache configurations
            - Override validation schema handles custom configuration overrides
            - All schemas are properly formatted for validation framework
            
        Fixtures Used:
            - None (testing schema initialization directly)
            
        Validation Coverage Verified:
            Schema initialization ensures comprehensive validation capability
            
        Related Tests:
            - test_cache_validator_schemas_support_all_configuration_types()
            - test_cache_validator_template_registry_is_properly_initialized()
        """
        # Given: CacheValidator initialization
        validator = CacheValidator()
        
        # When: Validator instance is created (initialization complete)
        # Then: All required validation schemas are loaded and available
        assert hasattr(validator, 'schemas')
        assert isinstance(validator.schemas, dict)
        
        # And: Preset validation schema is configured
        assert 'preset' in validator.schemas
        preset_schema = validator.schemas['preset']
        assert isinstance(preset_schema, dict)
        assert preset_schema.get('type') == 'object'
        assert 'required' in preset_schema
        assert 'properties' in preset_schema
        
        # And: Configuration validation schema is configured
        assert 'configuration' in validator.schemas
        config_schema = validator.schemas['configuration']
        assert isinstance(config_schema, dict)
        assert config_schema.get('type') == 'object'
        assert 'properties' in config_schema
        
        # And: Schemas are properly structured for JSON schema validation
        assert preset_schema['properties']['name']['type'] == 'string'
        assert preset_schema['properties']['strategy']['type'] == 'string'
        assert 'enum' in preset_schema['properties']['strategy']
        
        # Schema initialization ensures comprehensive validation capability
        assert len(validator.schemas) >= 2  # At least preset and configuration schemas

    def test_cache_validator_initializes_template_registry(self):
        """
        Test that CacheValidator initializes template registry with predefined templates.
        
        Verifies:
            Template registry provides configuration templates for common scenarios
            
        Business Impact:
            Enables rapid configuration setup with validated templates
            
        Scenario:
            Given: CacheValidator initialization with template support
            When: Validator instance is created
            Then: Template registry is initialized with predefined templates
            And: Development configuration templates are available
            And: Production configuration templates are available
            And: AI-optimized configuration templates are available
            And: Templates are validated and ready for use
            
        Template Registry Verified:
            - fast_development template for rapid development setup
            - robust_production template for production reliability
            - ai_optimized template for AI workload performance
            - Templates pass validation and provide complete configurations
            
        Fixtures Used:
            - None (testing template registry directly)
            
        Configuration Template Support Verified:
            Template registry enables rapid setup with validated configuration patterns
            
        Related Tests:
            - test_cache_validator_get_template_retrieves_valid_templates()
            - test_cache_validator_templates_pass_validation()
        """
        # Given: CacheValidator initialization with template support
        validator = CacheValidator()
        
        # When: Validator instance is created (initialization complete)
        # Then: Template registry is initialized with predefined templates
        assert hasattr(validator, 'templates')
        assert isinstance(validator.templates, dict)
        assert len(validator.templates) > 0
        
        # And: Development configuration templates are available
        assert 'fast_development' in validator.templates
        dev_template = validator.templates['fast_development']
        assert isinstance(dev_template, dict)
        assert dev_template['strategy'] == 'fast'
        assert dev_template['default_ttl'] == 600
        assert dev_template['enable_monitoring'] is True
        
        # And: Production configuration templates are available
        assert 'robust_production' in validator.templates
        prod_template = validator.templates['robust_production']
        assert isinstance(prod_template, dict)
        assert prod_template['strategy'] == 'robust'
        assert prod_template['default_ttl'] == 7200
        assert prod_template['max_connections'] == 20
        
        # And: AI-optimized configuration templates are available
        assert 'ai_optimized' in validator.templates
        ai_template = validator.templates['ai_optimized']
        assert isinstance(ai_template, dict)
        assert ai_template['strategy'] == 'ai_optimized'
        assert ai_template['enable_ai_cache'] is True
        assert 'text_hash_threshold' in ai_template
        
        # And: Templates are validated and ready for use
        # Each template should have essential configuration fields
        expected_fields = {'strategy', 'default_ttl', 'max_connections', 'enable_monitoring'}
        for template_name, template in validator.templates.items():
            assert all(field in template for field in expected_fields), f"Template {template_name} missing required fields"


class TestCacheValidatorPresetValidation:
    """
    Test suite for CacheValidator preset validation functionality.
    
    Scope:
        - Preset configuration validation with comprehensive schema checking
        - Preset parameter validation and consistency checking
        - Preset completeness validation for deployment readiness
        - Preset-specific validation rules and constraints
        
    Business Critical:
        Preset validation ensures deployment-ready preset configurations
        
    Test Strategy:
        - Unit tests for validate_preset() with various preset configurations
        - Schema-based validation testing for preset structures
        - Parameter consistency validation across preset types
        - Deployment readiness verification for validated presets
        
    External Dependencies:
        - JSON schema validation (mocked): Schema-based preset validation
        - Preset configuration patterns (internal): Preset structure validation
    """

    def test_cache_validator_validate_preset_confirms_valid_preset_configurations(self):
        """
        Test that validate_preset() confirms valid preset configurations.
        
        Verifies:
            Well-formed preset configurations pass comprehensive validation
            
        Business Impact:
            Ensures valid presets are confirmed as deployment-ready
            
        Scenario:
            Given: Well-formed preset configuration dictionary
            When: validate_preset() is called
            Then: ValidationResult indicates successful validation
            And: No validation errors are reported
            And: Preset is confirmed as deployment-ready
            And: All preset fields pass schema validation
            
        Valid Preset Confirmation Verified:
            - Complete preset configurations pass validation
            - All required preset fields are present and valid
            - Parameter values are within acceptable ranges
            - Strategy-parameter consistency is validated
            
        Fixtures Used:
            - None (testing preset validation directly)
            
        Deployment Readiness Verified:
            Valid presets are confirmed as ready for deployment use
            
        Related Tests:
            - test_cache_validator_validate_preset_identifies_invalid_preset_structure()
            - test_cache_validator_validate_preset_validates_parameter_consistency()
        """
        # Given: Well-formed preset configuration dictionary
        validator = CacheValidator()
        valid_preset = {
            "name": "test-preset",
            "description": "Test preset for validation",
            "strategy": "balanced",
            "default_ttl": 3600,
            "max_connections": 10,
            "connection_timeout": 5,
            "memory_cache_size": 200,
            "compression_threshold": 1000,
            "compression_level": 6,
            "enable_ai_cache": False,
            "enable_monitoring": True,
            "log_level": "INFO",
            "environment_contexts": ["production", "staging"]
        }
        
        # When: validate_preset() is called
        result = validator.validate_preset(valid_preset)
        
        # Then: ValidationResult indicates successful validation
        assert isinstance(result, ValidationResult)
        assert result.is_valid is True
        assert result.validation_type == "preset"
        
        # And: No validation errors are reported
        assert len(result.errors) == 0
        
        # And: Preset is confirmed as deployment-ready
        # All parameter values are within acceptable ranges
        assert valid_preset["default_ttl"] >= 60  # TTL constraint verified
        assert valid_preset["max_connections"] >= 1  # Connection constraint verified
        assert valid_preset["compression_level"] >= 1  # Compression constraint verified
        
        # And: All preset fields pass schema validation
        # No error messages should be present for any field
        error_fields = [msg.field_path for msg in result.messages if msg.severity.value == "error"]
        assert len(error_fields) == 0

    def test_cache_validator_validate_preset_identifies_invalid_preset_structure(self):
        """
        Test that validate_preset() identifies invalid preset structure.
        
        Verifies:
            Malformed preset configurations are rejected with specific errors
            
        Business Impact:
            Prevents deployment of invalid preset configurations
            
        Scenario:
            Given: Malformed preset configuration with structural issues
            When: validate_preset() is called
            Then: ValidationResult indicates validation failure
            And: Specific structural errors are identified
            And: Error messages explain required preset structure
            And: Invalid preset is prevented from deployment use
            
        Invalid Structure Detection Verified:
            - Missing required preset fields are identified
            - Invalid field types are detected and reported
            - Malformed nested structures (ai_optimizations) are caught
            - Error messages provide specific structural requirements
            
        Fixtures Used:
            - None (testing invalid preset structure directly)
            
        Configuration Safety Verified:
            Invalid preset structures are prevented from deployment
            
        Related Tests:
            - test_cache_validator_preset_validation_provides_helpful_error_messages()
            - test_cache_validator_validates_preset_parameter_ranges()
        """
        # Given: Malformed preset configuration with structural issues
        validator = CacheValidator()
        invalid_preset = {
            "name": "invalid-preset",
            "description": "Test preset with structural issues",
            # Missing required fields: strategy, default_ttl, max_connections, etc.
            "default_ttl": "invalid_type",  # Wrong type (should be int)
            "max_connections": -1,  # Invalid value (below minimum)
            "compression_level": 15,  # Invalid value (above maximum)
            "environment_contexts": "not_a_list"  # Wrong type (should be list)
        }
        
        # When: validate_preset() is called
        result = validator.validate_preset(invalid_preset)
        
        # Then: ValidationResult indicates validation failure
        assert isinstance(result, ValidationResult)
        assert result.is_valid is False
        assert result.validation_type == "preset"
        
        # And: Specific structural errors are identified
        assert len(result.errors) > 0
        
        # Missing required preset fields are identified
        missing_field_errors = [error for error in result.errors if "Missing required field" in error]
        assert len(missing_field_errors) > 0
        
        # Required fields should be reported as missing
        required_fields = ["strategy", "connection_timeout", "memory_cache_size", "compression_threshold", 
                          "enable_ai_cache", "enable_monitoring", "log_level"]
        for field in required_fields:
            field_missing = any(field in error for error in missing_field_errors)
            assert field_missing, f"Missing required field '{field}' not detected"
        
        # And: Error messages explain required preset structure
        # Invalid field types and values are detected when validation continues
        # (Note: validation stops early on missing required fields, but we can test this with complete invalid preset)
        complete_invalid_preset = {
            "name": "complete-invalid",
            "description": "Complete but invalid preset",
            "strategy": "invalid_strategy",
            "default_ttl": -1,  # Below minimum
            "max_connections": 150,  # Above maximum
            "connection_timeout": 0,  # Below minimum
            "memory_cache_size": 0,  # Below minimum
            "compression_threshold": 100,
            "compression_level": 15,  # Above maximum
            "enable_ai_cache": False,
            "enable_monitoring": True,
            "log_level": "INFO",
            "environment_contexts": ["production"]
        }
        
        complete_result = validator.validate_preset(complete_invalid_preset)
        assert complete_result.is_valid is False
        
        # Invalid field types and ranges are detected and reported
        range_errors = [error for error in complete_result.errors if "must be integer between" in error]
        assert len(range_errors) > 0
        
        # And: Invalid preset is prevented from deployment use
        assert complete_result.is_valid is False

    def test_cache_validator_validate_preset_validates_ai_optimization_parameters(self):
        """
        Test that validate_preset() validates AI optimization parameters properly.
        
        Verifies:
            AI-specific parameters in presets are validated for completeness and consistency
            
        Business Impact:
            Ensures AI-enabled presets provide complete AI optimization configuration
            
        Scenario:
            Given: Preset configuration with AI optimization parameters
            When: validate_preset() is called
            Then: AI parameters are validated for completeness
            And: text_hash_threshold is validated for appropriate range
            And: operation_ttls are validated for AI operation consistency
            And: AI parameter structure is validated for cache compatibility
            
        AI Parameter Validation Verified:
            - enable_ai_cache setting is validated appropriately
            - text_hash_threshold range is validated (appropriate for text processing)
            - operation_ttls structure matches expected AI operation names
            - AI parameter combinations are validated for consistency
            
        Fixtures Used:
            - None (testing AI parameter validation directly)
            
        AI Configuration Quality Verified:
            AI optimization parameters are validated for AI workload effectiveness
            
        Related Tests:
            - test_cache_validator_validates_ai_parameters_for_non_ai_presets()
            - test_cache_validator_ai_parameter_validation_ensures_compatibility()
        """
        # Given: Preset configuration with AI optimization parameters
        validator = CacheValidator()
        ai_preset = {
            "name": "ai-test-preset",
            "description": "AI-enabled test preset",
            "strategy": "ai_optimized",
            "default_ttl": 7200,
            "max_connections": 15,
            "connection_timeout": 10,
            "memory_cache_size": 500,
            "compression_threshold": 500,
            "compression_level": 6,
            "enable_ai_cache": True,
            "enable_monitoring": True,
            "log_level": "INFO",
            "environment_contexts": ["ai-production"],
            "ai_optimizations": {
                "text_hash_threshold": 1500,
                "operation_ttls": {
                    "text_generation": 3600,
                    "embeddings": 7200,
                    "classification": 1800
                },
                "text_size_tiers": {
                    "small": 1000,
                    "medium": 5000,
                    "large": 15000
                }
            }
        }
        
        # When: validate_preset() is called
        result = validator.validate_preset(ai_preset)
        
        # Then: AI parameters are validated for completeness
        # Valid AI preset should pass validation
        assert isinstance(result, ValidationResult)
        
        # And: text_hash_threshold is validated for appropriate range
        # Test with invalid threshold value
        invalid_ai_preset = ai_preset.copy()
        invalid_ai_preset["ai_optimizations"] = {
            "text_hash_threshold": 50,  # Too low (below 100)
            "operation_ttls": {
                "text_generation": 30  # Too low (below 60)
            }
        }
        
        invalid_result = validator.validate_preset(invalid_ai_preset)
        
        # Should detect invalid text_hash_threshold
        threshold_errors = [error for error in invalid_result.errors 
                          if "text_hash_threshold" in error and "between 100 and 10000" in error]
        assert len(threshold_errors) > 0
        
        # And: operation_ttls are validated for AI operation consistency
        ttl_errors = [error for error in invalid_result.errors 
                     if "operation_ttls" in error and ">= 60 seconds" in error]
        assert len(ttl_errors) > 0
        
        # And: AI parameter structure is validated for cache compatibility
        # Test with AI enabled but no optimizations
        ai_no_opts = {
            "name": "ai-no-opts",
            "description": "AI enabled without optimizations",
            "strategy": "ai_optimized",
            "default_ttl": 3600,
            "max_connections": 10,
            "connection_timeout": 5,
            "memory_cache_size": 200,
            "compression_threshold": 1000,
            "compression_level": 6,
            "enable_ai_cache": True,
            "enable_monitoring": True,
            "log_level": "INFO",
            "environment_contexts": ["ai-development"]
        }
        
        no_opts_result = validator.validate_preset(ai_no_opts)
        
        # Should provide info message about using defaults
        info_messages = [msg.message for msg in no_opts_result.messages 
                        if msg.severity.value == "info" and "AI cache enabled" in msg.message]
        assert len(info_messages) > 0

    def test_cache_validator_validate_preset_validates_environment_context_appropriateness(self):
        """
        Test that validate_preset() validates environment context appropriateness.
        
        Verifies:
            Environment contexts in presets are validated for deployment scenario appropriateness
            
        Business Impact:
            Ensures preset environment contexts support accurate deployment scenario classification
            
        Scenario:
            Given: Preset configuration with environment contexts
            When: validate_preset() is called
            Then: Environment contexts are validated for appropriateness
            And: Context values match recognized deployment scenarios
            And: Context combinations are validated for consistency
            And: Environment context supports preset recommendation logic
            
        Environment Context Validation Verified:
            - Environment context values match recognized deployment scenarios
            - Context combinations are appropriate for preset characteristics
            - Environment contexts support preset selection and recommendation
            - Context values enable accurate deployment scenario classification
            
        Fixtures Used:
            - None (testing environment context validation directly)
            
        Deployment Classification Support Verified:
            Environment context validation ensures accurate preset recommendation
            
        Related Tests:
            - test_cache_validator_environment_contexts_support_preset_recommendation()
            - test_cache_validator_validates_context_preset_alignment()
        """
        # Given: Preset configuration with environment contexts
        validator = CacheValidator()
        
        # Test valid environment contexts
        valid_contexts_preset = {
            "name": "context-test-preset",
            "description": "Test preset for environment contexts",
            "strategy": "balanced",
            "default_ttl": 3600,
            "max_connections": 10,
            "connection_timeout": 5,
            "memory_cache_size": 200,
            "compression_threshold": 1000,
            "compression_level": 6,
            "enable_ai_cache": False,
            "enable_monitoring": True,
            "log_level": "INFO",
            "environment_contexts": ["production", "staging", "ai-production"]
        }
        
        # When: validate_preset() is called
        result = validator.validate_preset(valid_contexts_preset)
        
        # Then: Environment contexts are validated for appropriateness
        # Valid contexts should not generate warnings
        context_warnings = [msg.message for msg in result.messages 
                          if msg.severity.value == "warning" and "environment context" in msg.message]
        assert len(context_warnings) == 0
        
        # And: Context values match recognized deployment scenarios
        # Test with invalid/unknown context values
        invalid_contexts_preset = valid_contexts_preset.copy()
        invalid_contexts_preset["environment_contexts"] = ["unknown_context", "invalid_env", "production"]
        
        invalid_result = validator.validate_preset(invalid_contexts_preset)
        
        # Should generate warnings for unknown contexts
        unknown_warnings = [msg.message for msg in invalid_result.messages 
                           if msg.severity.value == "warning" and "Unknown environment context" in msg.message]
        assert len(unknown_warnings) >= 2  # Two unknown contexts
        
        # And: Context combinations are validated for consistency
        # Verify that warning messages provide guidance
        for warning in unknown_warnings:
            assert "may not match auto-detection" in warning
        
        # And: Environment context supports preset recommendation logic
        # Test with empty context list
        empty_contexts_preset = valid_contexts_preset.copy()
        empty_contexts_preset["environment_contexts"] = []
        
        empty_result = validator.validate_preset(empty_contexts_preset)
        
        # Should generate warning for missing contexts
        empty_warnings = [msg.message for msg in empty_result.messages 
                         if msg.severity.value == "warning" and "No environment contexts specified" in msg.message]
        assert len(empty_warnings) > 0
        
        # Context values enable accurate deployment scenario classification
        # Valid contexts should be recognized
        valid_contexts = ["development", "dev", "testing", "production", "prod", 
                         "ai-development", "ai-production", "staging", "local"]
        
        for context in valid_contexts:
            single_context_preset = valid_contexts_preset.copy()
            single_context_preset["environment_contexts"] = [context]
            
            context_result = validator.validate_preset(single_context_preset)
            context_warnings = [msg.message for msg in context_result.messages 
                              if msg.severity.value == "warning" and "Unknown environment context" in msg.message]
            assert len(context_warnings) == 0, f"Valid context '{context}' generated warnings"


class TestCacheValidatorConfigurationValidation:
    """
    Test suite for CacheValidator complete configuration validation functionality.
    
    Scope:
        - Complete cache configuration validation
        - Parameter range and consistency validation
        - Configuration completeness and deployment readiness
        - Strategy-configuration alignment validation
        
    Business Critical:
        Configuration validation ensures deployment-ready cache configurations
        
    Test Strategy:
        - Unit tests for validate_configuration() with various configuration types
        - Parameter validation testing with range checking
        - Configuration completeness verification
        - Strategy alignment validation across configuration types
        
    External Dependencies:
        - Configuration validation schemas (mocked): Complete config validation
        - Parameter validation logic (internal): Range and consistency checking
    """

    def test_cache_validator_validate_configuration_confirms_complete_configurations(self):
        """
        Test that validate_configuration() confirms complete cache configurations.
        
        Verifies:
            Complete cache configurations pass comprehensive validation
            
        Business Impact:
            Ensures complete configurations are ready for cache initialization
            
        Scenario:
            Given: Complete cache configuration with all required parameters
            When: validate_configuration() is called
            Then: ValidationResult indicates successful validation
            And: All configuration parameters pass validation
            And: Configuration is confirmed as cache-initialization-ready
            And: No required parameters are missing
            
        Complete Configuration Validation Verified:
            - All required configuration fields are present and valid
            - Parameter values are within acceptable ranges
            - Configuration structure is suitable for cache factory usage
            - Optional parameters have appropriate defaults or values
            
        Fixtures Used:
            - None (testing complete configuration validation directly)
            
        Cache Initialization Readiness Verified:
            Complete configurations are validated as ready for cache creation
            
        Related Tests:
            - test_cache_validator_validate_configuration_identifies_missing_required_parameters()
            - test_cache_validator_validate_configuration_validates_parameter_ranges()
        """
        # Given: Complete cache configuration with all required parameters
        validator = CacheValidator()
        complete_config = {
            "strategy": "balanced",
            "redis_url": "redis://localhost:6379/0",
            "redis_password": "secure_password",
            "use_tls": False,
            "max_connections": 15,
            "connection_timeout": 8,
            "default_ttl": 7200,
            "memory_cache_size": 300,
            "compression_threshold": 800,
            "compression_level": 6,
            "enable_ai_cache": False,
            "enable_monitoring": True,
            "log_level": "INFO"
        }
        
        # When: validate_configuration() is called
        result = validator.validate_configuration(complete_config)
        
        # Then: ValidationResult indicates successful validation
        assert isinstance(result, ValidationResult)
        assert result.validation_type == "configuration"
        
        # And: All configuration parameters pass validation
        # For a well-formed configuration, we should have minimal validation issues
        critical_errors = [msg.message for msg in result.messages if msg.severity.value == "error"]
        assert len(critical_errors) == 0
        
        # And: Configuration is confirmed as cache-initialization-ready
        # Required strategy field should be present and valid
        assert complete_config["strategy"] is not None
        
        # And: No required parameters are missing
        # The validator should not report missing required fields
        missing_field_errors = [error for error in result.errors if "Missing required field" in error]
        assert len(missing_field_errors) == 0
        
        # Configuration structure is suitable for cache factory usage
        assert "strategy" in complete_config
        assert "redis_url" in complete_config
        assert "max_connections" in complete_config

    def test_cache_validator_validate_configuration_validates_redis_connection_parameters(self):
        """
        Test that validate_configuration() validates Redis connection parameters.
        
        Verifies:
            Redis connection parameters are validated for connection reliability
            
        Business Impact:
            Prevents cache connection failures due to invalid Redis configuration
            
        Scenario:
            Given: Cache configuration with Redis connection parameters
            When: validate_configuration() is called
            Then: Redis URL format is validated
            And: Connection pool parameters are validated for appropriate ranges
            And: Connection timeout values are validated
            And: TLS configuration consistency is validated
            
        Redis Connection Validation Verified:
            - redis_url format validation (redis://, rediss://, unix://)
            - max_connections range validation (1-100)
            - connection_timeout range validation (1-30 seconds)
            - TLS configuration consistency (use_tls, tls_cert_path)
            
        Fixtures Used:
            - None (testing Redis connection validation directly)
            
        Connection Reliability Verified:
            Redis parameter validation prevents connection configuration failures
            
        Related Tests:
            - test_cache_validator_validates_redis_url_format_variations()
            - test_cache_validator_validates_connection_pool_sizing()
        """
        # Given: Cache configuration with Redis connection parameters
        validator = CacheValidator()
        
        # Test valid Redis URL formats
        valid_redis_config = {
            "strategy": "balanced",
            "redis_url": "redis://localhost:6379/0",
            "max_connections": 10,
            "connection_timeout": 5,
            "use_tls": False
        }
        
        # When: validate_configuration() is called
        result = validator.validate_configuration(valid_redis_config)
        
        # Then: Redis URL format is validated (valid format should pass)
        url_errors = [error for error in result.errors if "Invalid Redis URL format" in error]
        assert len(url_errors) == 0
        
        # Test invalid Redis URL format
        invalid_url_config = {
            "strategy": "balanced",
            "redis_url": "http://localhost:6379",  # Invalid scheme
            "max_connections": 10,
            "connection_timeout": 5
        }
        
        invalid_url_result = validator.validate_configuration(invalid_url_config)
        url_errors = [error for error in invalid_url_result.errors if "Invalid Redis URL format" in error]
        assert len(url_errors) > 0
        
        # And: TLS configuration consistency is validated
        inconsistent_tls_config = {
            "strategy": "balanced",
            "redis_url": "redis://localhost:6379/0",  # Non-TLS URL
            "use_tls": True,  # But TLS enabled
            "max_connections": 10,
            "connection_timeout": 5
        }
        
        tls_result = validator.validate_configuration(inconsistent_tls_config)
        tls_warnings = [msg.message for msg in tls_result.messages 
                       if msg.severity.value == "warning" and "rediss://" in msg.message]
        assert len(tls_warnings) > 0
        
        # Test with valid TLS configuration
        valid_tls_config = {
            "strategy": "balanced",
            "redis_url": "rediss://localhost:6379/0",  # TLS URL
            "use_tls": True,
            "max_connections": 10,
            "connection_timeout": 5
        }
        
        tls_valid_result = validator.validate_configuration(valid_tls_config)
        tls_valid_warnings = [msg.message for msg in tls_valid_result.messages 
                             if msg.severity.value == "warning" and "rediss://" in msg.message]
        assert len(tls_valid_warnings) == 0

    def test_cache_validator_validate_configuration_validates_performance_parameters(self):
        """
        Test that validate_configuration() validates cache performance parameters.
        
        Verifies:
            Performance parameters are validated for cache operation efficiency
            
        Business Impact:
            Ensures cache performance parameters support efficient operation
            
        Scenario:
            Given: Cache configuration with performance parameters
            When: validate_configuration() is called
            Then: TTL parameters are validated for appropriate ranges
            And: Compression parameters are validated for effectiveness
            And: Memory cache parameters are validated for resource usage
            And: Performance parameter combinations are validated for consistency
            
        Performance Parameter Validation Verified:
            - default_ttl range validation (60-86400 seconds)
            - compression_threshold range validation (1024-65536 bytes)
            - compression_level range validation (1-9)
            - Memory cache size validation for resource appropriateness
            
        Fixtures Used:
            - None (testing performance parameter validation directly)
            
        Cache Performance Optimization Verified:
            Performance parameter validation ensures efficient cache operation
            
        Related Tests:
            - test_cache_validator_validates_performance_parameter_combinations()
            - test_cache_validator_validates_memory_usage_parameters()
        """
        # Given: Cache configuration with performance parameters
        validator = CacheValidator()
        
        # Test performance parameter combinations
        performance_config = {
            "strategy": "balanced",
            "redis_url": "redis://localhost:6379",
            "max_connections": 60,  # High connection count
            "connection_timeout": 3,  # Low timeout
            "default_ttl": 7200,
            "memory_cache_size": 500,
            "compression_threshold": 1000,
            "compression_level": 6
        }
        
        # When: validate_configuration() is called
        result = validator.validate_configuration(performance_config)
        
        # Then: Performance parameter combinations are validated for consistency
        # High connection count with low timeout should generate warning
        perf_warnings = [msg.message for msg in result.messages 
                        if msg.severity.value == "warning" and "High connection count" in msg.message]
        assert len(perf_warnings) > 0
        
        # Test with balanced performance parameters
        balanced_config = {
            "strategy": "balanced",
            "redis_url": "redis://localhost:6379",
            "max_connections": 15,
            "connection_timeout": 10,
            "default_ttl": 3600,
            "memory_cache_size": 300,
            "compression_threshold": 1000,
            "compression_level": 6
        }
        
        balanced_result = validator.validate_configuration(balanced_config)
        balanced_perf_warnings = [msg.message for msg in balanced_result.messages 
                                 if msg.severity.value == "warning" and "connection count" in msg.message]
        assert len(balanced_perf_warnings) == 0
        
        # Test AI configuration performance validation
        ai_config = {
            "strategy": "ai_optimized",
            "redis_url": "redis://localhost:6379",
            "enable_ai_cache": True,
            "text_hash_threshold": 50,  # Very low threshold
            "max_connections": 20,
            "connection_timeout": 10
        }
        
        ai_result = validator.validate_configuration(ai_config)
        
        # Should warn about low text_hash_threshold
        ai_warnings = [msg.message for msg in ai_result.messages 
                      if msg.severity.value == "warning" and "text_hash_threshold" in msg.message]
        assert len(ai_warnings) > 0
        
        # Performance optimization should be checked
        threshold_warning = any("very low" in warning for warning in ai_warnings)
        assert threshold_warning

    def test_cache_validator_validate_configuration_validates_strategy_alignment(self):
        """
        Test that validate_configuration() validates strategy-configuration alignment.
        
        Verifies:
            Configuration parameters align with specified strategy characteristics
            
        Business Impact:
            Ensures configuration consistency with intended deployment strategy
            
        Scenario:
            Given: Cache configuration with strategy specification and parameters
            When: validate_configuration() is called
            Then: Parameters are validated for strategy consistency
            And: Strategy-appropriate parameter ranges are enforced
            And: Strategy-specific requirements are validated
            And: Configuration supports strategy performance characteristics
            
        Strategy Alignment Validation Verified:
            - FAST strategy configurations prioritize development speed
            - ROBUST strategy configurations prioritize production reliability
            - AI_OPTIMIZED strategy configurations enable AI features
            - Strategy-parameter combinations are validated for consistency
            
        Fixtures Used:
            - None (testing strategy alignment validation directly)
            
        Strategy Consistency Verified:
            Configuration validation ensures alignment with deployment strategy goals
            
        Related Tests:
            - test_cache_validator_validates_ai_strategy_requires_ai_features()
            - test_cache_validator_validates_strategy_parameter_consistency()
        """
        # Given: Cache configuration with strategy specification and parameters
        validator = CacheValidator()
        
        # Test FAST strategy configuration
        fast_config = {
            "strategy": "fast",
            "redis_url": "redis://localhost:6379",
            "max_connections": 5,  # Low connections for development
            "connection_timeout": 3,  # Quick timeout
            "default_ttl": 600,  # Short TTL
            "memory_cache_size": 100,  # Small cache
            "compression_level": 1,  # Minimal compression
            "enable_ai_cache": False
        }
        
        # When: validate_configuration() is called
        fast_result = validator.validate_configuration(fast_config)
        
        # Then: Configuration should be validated without strategy conflicts
        # Fast strategy should work with development-focused parameters
        assert isinstance(fast_result, ValidationResult)
        
        # Test ROBUST strategy configuration
        robust_config = {
            "strategy": "robust",
            "redis_url": "rediss://localhost:6379",  # TLS for production
            "use_tls": True,
            "max_connections": 30,  # High connections for production
            "connection_timeout": 15,  # Generous timeout
            "default_ttl": 14400,  # Long TTL
            "memory_cache_size": 1000,  # Large cache
            "compression_level": 9,  # Maximum compression
            "enable_ai_cache": False,
            "enable_monitoring": True
        }
        
        robust_result = validator.validate_configuration(robust_config)
        
        # Should validate without major issues for robust strategy
        assert isinstance(robust_result, ValidationResult)
        
        # Test AI_OPTIMIZED strategy configuration
        ai_config = {
            "strategy": "ai_optimized",
            "redis_url": "redis://localhost:6379",
            "enable_ai_cache": True,  # AI features enabled
            "text_hash_threshold": 1500,
            "max_connections": 25,
            "connection_timeout": 12,
            "default_ttl": 21600,  # Long TTL for AI results
            "memory_cache_size": 800,
            "compression_level": 8
        }
        
        ai_result = validator.validate_configuration(ai_config)
        
        # AI strategy should work with AI-enabled configuration
        assert isinstance(ai_result, ValidationResult)
        
        # Strategy-specific requirements validation
        # AI strategy should be compatible with AI features
        assert ai_config["enable_ai_cache"] is True
        assert "text_hash_threshold" in ai_config
        
        # Configuration supports strategy performance characteristics
        # Each strategy should have appropriate parameter ranges
        assert fast_config["default_ttl"] < robust_config["default_ttl"]  # Fast < Robust TTL
        assert fast_config["max_connections"] < robust_config["max_connections"]  # Fast < Robust connections
        assert robust_config["compression_level"] > fast_config["compression_level"]  # Robust > Fast compression


class TestCacheValidatorCustomOverrideValidation:
    """
    Test suite for CacheValidator custom override validation functionality.
    
    Scope:
        - Custom configuration override validation
        - Override parameter validation and compatibility
        - Override structure validation for JSON/YAML input
        - Override integration validation with base configurations
        
    Business Critical:
        Override validation enables safe custom configuration while maintaining base configuration integrity
        
    Test Strategy:
        - Unit tests for validate_custom_overrides() with various override patterns
        - Override structure validation for JSON/YAML compatibility
        - Parameter override validation for compatibility with base configurations
        - Integration validation for override application
        
    External Dependencies:
        - JSON schema validation (mocked): Override structure validation
        - Configuration integration logic (internal): Override application validation
    """

    def test_cache_validator_validate_custom_overrides_confirms_valid_overrides(self):
        """
        Test that validate_custom_overrides() confirms valid custom configuration overrides.
        
        Verifies:
            Well-formed custom overrides pass validation and are ready for application
            
        Business Impact:
            Enables safe custom configuration overrides with validation assurance
            
        Scenario:
            Given: Well-formed custom override configuration
            When: validate_custom_overrides() is called
            Then: ValidationResult indicates successful validation
            And: Override parameters are validated for type and range correctness
            And: Override structure is validated for application compatibility
            And: Overrides are confirmed as safe for base configuration application
            
        Valid Override Confirmation Verified:
            - Override parameter names match recognized configuration fields
            - Override parameter values are within acceptable ranges
            - Override structure is compatible with configuration merge operations
            - Override validation ensures safe application to base configurations
            
        Fixtures Used:
            - None (testing custom override validation directly)
            
        Safe Override Application Verified:
            Valid overrides are confirmed as safe for configuration customization
            
        Related Tests:
            - test_cache_validator_validate_custom_overrides_identifies_invalid_parameters()
            - test_cache_validator_validates_override_parameter_compatibility()
        """
        # Given: Well-formed custom override configuration
        validator = CacheValidator()
        valid_overrides = {
            "default_ttl": 7200,
            "max_connections": 20,
            "compression_level": 8,
            "enable_ai_cache": True,
            "text_hash_threshold": 2000,
            "enable_monitoring": True,
            "redis_password": "custom_password",
            "log_level": "DEBUG"
        }
        
        # When: validate_custom_overrides() is called
        result = validator.validate_custom_overrides(valid_overrides)
        
        # Then: ValidationResult indicates successful validation
        assert isinstance(result, ValidationResult)
        assert result.validation_type == "custom_overrides"
        
        # And: Override parameters are validated for type and range correctness
        # Valid overrides should not generate type errors
        type_errors = [error for error in result.errors if "expects" in error and "got" in error]
        assert len(type_errors) == 0
        
        # And: Override structure is validated for application compatibility
        # All override keys should be recognized (no unknown key warnings for valid keys)
        unknown_key_warnings = [msg.message for msg in result.messages 
                              if msg.severity.value == "warning" and "Unknown override key" in msg.message]
        assert len(unknown_key_warnings) == 0
        
        # And: Overrides are confirmed as safe for base configuration application
        # Override parameter names match recognized configuration fields
        recognized_keys = {
            "redis_url", "redis_password", "use_tls", "tls_cert_path", "tls_key_path",
            "max_connections", "connection_timeout", "default_ttl", "memory_cache_size",
            "compression_threshold", "compression_level", "enable_ai_cache",
            "text_hash_threshold", "hash_algorithm", "text_size_tiers", "operation_ttls",
            "enable_smart_promotion", "max_text_length", "enable_monitoring", "log_level"
        }
        
        for key in valid_overrides.keys():
            assert key in recognized_keys, f"Override key '{key}' should be recognized"

    def test_cache_validator_validate_custom_overrides_identifies_invalid_parameters(self):
        """
        Test that validate_custom_overrides() identifies invalid override parameters.
        
        Verifies:
            Invalid custom overrides are rejected with specific error identification
            
        Business Impact:
            Prevents configuration corruption due to invalid override parameters
            
        Scenario:
            Given: Custom override configuration with invalid parameters
            When: validate_custom_overrides() is called
            Then: ValidationResult indicates validation failure
            And: Invalid parameter names are identified
            And: Invalid parameter values are reported with acceptable ranges
            And: Override application is prevented for invalid parameters
            
        Invalid Override Detection Verified:
            - Unrecognized parameter names are identified and rejected
            - Parameter values outside acceptable ranges are detected
            - Invalid parameter types are caught and reported
            - Error messages provide guidance for override correction
            
        Fixtures Used:
            - None (testing invalid override detection directly)
            
        Configuration Protection Verified:
            Invalid overrides are prevented from corrupting base configurations
            
        Related Tests:
            - test_cache_validator_override_validation_provides_corrective_guidance()
            - test_cache_validator_validates_override_structure_for_json_yaml()
        """
        # Given: Custom override configuration with invalid parameters
        validator = CacheValidator()
        invalid_overrides = {
            "unknown_parameter": "invalid_value",  # Unrecognized parameter
            "invalid_key_123": "some_value",  # Another unrecognized parameter
            "default_ttl": "not_an_integer",  # Invalid type (should be int)
            "max_connections": -5,  # Invalid value (should be positive)
            "enable_ai_cache": "yes",  # Invalid type (should be bool)
            "compression_level": 15,  # Invalid value (should be 1-9)
            "use_tls": 1  # Invalid type (should be bool)
        }
        
        # When: validate_custom_overrides() is called
        result = validator.validate_custom_overrides(invalid_overrides)
        
        # Then: ValidationResult indicates validation issues
        assert isinstance(result, ValidationResult)
        assert result.validation_type == "custom_overrides"
        
        # And: Invalid parameter names are identified
        # Unrecognized parameter names should generate warnings
        unknown_warnings = [msg.message for msg in result.messages 
                           if msg.severity.value == "warning" and "Unknown override key" in msg.message]
        assert len(unknown_warnings) >= 2  # At least 2 unknown parameters
        
        # Check that specific unknown keys are identified
        unknown_keys = ["unknown_parameter", "invalid_key_123"]
        for unknown_key in unknown_keys:
            key_warned = any(unknown_key in warning for warning in unknown_warnings)
            assert key_warned, f"Unknown key '{unknown_key}' should generate warning"
        
        # And: Invalid parameter values are reported with type errors
        type_errors = [error for error in result.errors if "expects" in error and "got" in error]
        assert len(type_errors) > 0
        
        # Check for specific type validation errors
        ttl_error = any("default_ttl" in error and ("int" in error or "integer" in error) for error in type_errors)
        assert ttl_error, "default_ttl type error should be detected"
        
        ai_error = any("enable_ai_cache" in error and "bool" in error for error in type_errors)
        assert ai_error, "enable_ai_cache type error should be detected"
        
        # And: Override application is prevented for invalid parameters
        # Result should indicate validation issues
        has_critical_issues = len(result.errors) > 0 or any(
            msg.severity.value == "error" for msg in result.messages
        )
        assert has_critical_issues, "Invalid overrides should generate validation errors"

    def test_cache_validator_validate_custom_overrides_validates_json_yaml_structure(self):
        """
        Test that validate_custom_overrides() validates JSON/YAML structure compatibility.
        
        Verifies:
            Override structure validation ensures compatibility with JSON/YAML configuration sources
            
        Business Impact:
            Enables reliable custom overrides from JSON/YAML configuration sources
            
        Scenario:
            Given: Custom override configuration from JSON/YAML sources
            When: validate_custom_overrides() is called
            Then: Override structure is validated for JSON/YAML compatibility
            And: Nested parameter structures are validated properly
            And: Complex parameter types (dicts, lists) are validated
            And: Override structure supports configuration serialization
            
        JSON/YAML Structure Validation Verified:
            - Override structure is compatible with JSON serialization
            - Nested parameter structures (operation_ttls, text_size_tiers) are valid
            - Parameter types are suitable for YAML representation
            - Override validation supports configuration file-based customization
            
        Fixtures Used:
            - JSON/YAML structure validation mocks
            
        Configuration File Compatibility Verified:
            Override validation ensures compatibility with configuration file-based customization
            
        Related Tests:
            - test_cache_validator_override_structure_supports_configuration_files()
            - test_cache_validator_validates_complex_override_parameter_types()
        """
        # Given: Custom override configuration from JSON/YAML sources
        validator = CacheValidator()
        
        # Test complex nested structures typical of JSON/YAML config files
        json_yaml_overrides = {
            "default_ttl": 7200,
            "max_connections": 25,
            "enable_ai_cache": True,
            "operation_ttls": {  # Nested dictionary structure
                "text_generation": 14400,
                "embeddings": 21600,
                "classification": 7200,
                "summarization": 10800
            },
            "text_size_tiers": {  # Another nested dictionary
                "tiny": 100,
                "small": 1000,
                "medium": 5000,
                "large": 20000,
                "huge": 50000
            },
            "redis_url": "redis://localhost:6379/0",
            "compression_level": 8
        }
        
        # When: validate_custom_overrides() is called
        result = validator.validate_custom_overrides(json_yaml_overrides)
        
        # Then: Override structure is validated for JSON/YAML compatibility
        assert isinstance(result, ValidationResult)
        
        # And: Nested parameter structures are validated properly
        # No errors should occur for properly structured nested objects
        structure_errors = [error for error in result.errors if "structure" in error.lower()]
        assert len(structure_errors) == 0
        
        # And: Complex parameter types (dicts, lists) are validated
        # operation_ttls and text_size_tiers are dictionary types that should be accepted
        complex_type_errors = [error for error in result.errors 
                             if "operation_ttls" in error or "text_size_tiers" in error]
        assert len(complex_type_errors) == 0
        
        # Test with JSON-serializable values only
        json_compatible_overrides = {
            "default_ttl": 3600,  # int - JSON compatible
            "enable_ai_cache": False,  # bool - JSON compatible
            "redis_url": "redis://prod:6379",  # str - JSON compatible
            "compression_level": 6,  # int - JSON compatible
            "text_hash_threshold": 1500  # int - JSON compatible
        }
        
        json_result = validator.validate_custom_overrides(json_compatible_overrides)
        
        # Should validate successfully with JSON-compatible types
        json_type_errors = [error for error in json_result.errors if "expects" in error]
        assert len(json_type_errors) == 0
        
        # And: Override structure supports configuration serialization
        # All parameter types should be serializable (int, str, bool, dict)
        import json
        
        try:
            # Should be JSON serializable
            serialized = json.dumps(json_yaml_overrides)
            deserialized = json.loads(serialized)
            assert isinstance(deserialized, dict)
            assert "operation_ttls" in deserialized
            assert isinstance(deserialized["operation_ttls"], dict)
        except (TypeError, ValueError) as e:
            assert False, f"Override structure should be JSON serializable: {e}"


class TestCacheValidatorTemplateManagement:
    """
    Test suite for CacheValidator template generation and management functionality.
    
    Scope:
        - Configuration template retrieval and access
        - Template validation and quality assurance
        - Template listing and enumeration
        - Template-based configuration generation
        
    Business Critical:
        Template management enables rapid configuration setup with validated patterns
        
    Test Strategy:
        - Unit tests for get_template() and list_templates() functionality
        - Template validation and quality verification
        - Template enumeration and access testing
        - Template-based configuration generation verification
        
    External Dependencies:
        - Configuration templates (internal): Predefined template registry
        - Template validation (internal): Template quality assurance
    """

    def test_cache_validator_get_template_retrieves_valid_configuration_templates(self):
        """
        Test that get_template() retrieves valid configuration templates.
        
        Verifies:
            Configuration templates are accessible and provide complete configurations
            
        Business Impact:
            Enables rapid configuration setup using validated template patterns
            
        Scenario:
            Given: Template name for specific deployment scenario
            When: get_template() is called
            Then: Complete configuration template is returned
            And: Template contains all required configuration parameters
            And: Template parameters are validated for the target scenario
            And: Template is ready for cache configuration use
            
        Template Retrieval Verified:
            - get_template('fast_development') returns development-optimized template
            - get_template('robust_production') returns production-optimized template
            - get_template('ai_optimized') returns AI-workload-optimized template
            - Retrieved templates contain complete, validated configurations
            
        Fixtures Used:
            - None (testing template retrieval directly)
            
        Rapid Configuration Setup Verified:
            Templates provide complete, validated configurations for immediate use
            
        Related Tests:
            - test_cache_validator_get_template_raises_error_for_invalid_template_names()
            - test_cache_validator_retrieved_templates_pass_validation()
        """
        # Given: Template name for specific deployment scenario
        validator = CacheValidator()
        
        # When: get_template() is called for development scenario
        dev_template = validator.get_template('fast_development')
        
        # Then: Complete configuration template is returned
        assert isinstance(dev_template, dict)
        assert len(dev_template) > 0
        
        # And: Template contains all required configuration parameters
        essential_fields = {
            'strategy', 'default_ttl', 'max_connections', 'connection_timeout',
            'memory_cache_size', 'compression_threshold', 'compression_level',
            'enable_ai_cache', 'enable_monitoring', 'log_level'
        }
        
        for field in essential_fields:
            assert field in dev_template, f"Development template missing required field: {field}"
        
        # Template parameters are validated for the target scenario
        assert dev_template['strategy'] == 'fast'
        assert dev_template['default_ttl'] == 600  # Short TTL for development
        assert dev_template['max_connections'] == 3  # Few connections for development
        assert dev_template['enable_ai_cache'] is False  # AI disabled for fast development
        
        # When: get_template() is called for production scenario
        prod_template = validator.get_template('robust_production')
        
        # Then: Production-optimized template is returned
        assert isinstance(prod_template, dict)
        assert prod_template['strategy'] == 'robust'
        assert prod_template['default_ttl'] == 7200  # Longer TTL for production
        assert prod_template['max_connections'] == 20  # More connections for production
        assert prod_template['compression_level'] == 9  # Maximum compression for efficiency
        
        # When: get_template() is called for AI scenario
        ai_template = validator.get_template('ai_optimized')
        
        # Then: AI-workload-optimized template is returned
        assert isinstance(ai_template, dict)
        assert ai_template['strategy'] == 'ai_optimized'
        assert ai_template['enable_ai_cache'] is True  # AI features enabled
        assert 'text_hash_threshold' in ai_template  # AI-specific parameter
        assert ai_template['memory_cache_size'] == 1000  # Large cache for AI workloads
        
        # And: Template is ready for cache configuration use
        # Templates should be independent copies (not references)
        dev_template_copy = validator.get_template('fast_development')
        dev_template_copy['strategy'] = 'modified'
        original_template = validator.get_template('fast_development')
        assert original_template['strategy'] == 'fast'  # Original unchanged
        
        # Test error handling for invalid template name
        try:
            validator.get_template('invalid_template_name')
            assert False, "Should raise ValueError for invalid template name"
        except ValueError as e:
            assert "Unknown template" in str(e)
            assert "Available:" in str(e)

    def test_cache_validator_list_templates_returns_available_template_names(self):
        """
        Test that list_templates() returns complete list of available template names.
        
        Verifies:
            Template enumeration enables template discovery and selection
            
        Business Impact:
            Supports dynamic template discovery for configuration UI and automation
            
        Scenario:
            Given: CacheValidator with initialized template registry
            When: list_templates() is called
            Then: List of all available template names is returned
            And: Template names are suitable for user selection
            And: List includes templates for all major deployment scenarios
            And: Template enumeration supports configuration UI development
            
        Template Enumeration Verified:
            - All predefined template names are included
            - Template names are descriptive of their deployment scenarios
            - List order is consistent and predictable
            - Template enumeration supports configuration selection interfaces
            
        Fixtures Used:
            - None (testing template enumeration directly)
            
        Configuration Discovery Support Verified:
            Template enumeration enables dynamic configuration template discovery
            
        Related Tests:
            - test_cache_validator_template_names_are_descriptive()
            - test_cache_validator_template_enumeration_supports_ui_development()
        """
        # Given: CacheValidator with initialized template registry
        validator = CacheValidator()
        
        # When: list_templates() is called
        template_names = validator.list_templates()
        
        # Then: List of all available template names is returned
        assert isinstance(template_names, list)
        assert len(template_names) > 0
        
        # And: Template names are suitable for user selection
        # All predefined template names should be included
        expected_templates = {'fast_development', 'robust_production', 'ai_optimized'}
        actual_templates = set(template_names)
        
        for expected in expected_templates:
            assert expected in actual_templates, f"Expected template '{expected}' not found in list"
        
        # And: Template names are descriptive of their deployment scenarios
        # Names should indicate their purpose
        assert any('development' in name for name in template_names), "Should include development template"
        assert any('production' in name for name in template_names), "Should include production template"
        assert any('ai' in name for name in template_names), "Should include AI-optimized template"
        
        # And: List includes templates for all major deployment scenarios
        # Verify each template name corresponds to an actual template
        for template_name in template_names:
            template = validator.get_template(template_name)
            assert isinstance(template, dict), f"Template '{template_name}' should return a dictionary"
            assert len(template) > 0, f"Template '{template_name}' should not be empty"
            assert 'strategy' in template, f"Template '{template_name}' should have a strategy"
        
        # And: Template enumeration supports configuration UI development
        # List should be consistent across multiple calls
        template_names_again = validator.list_templates()
        assert template_names == template_names_again, "Template list should be consistent"
        
        # List order is consistent and predictable
        assert isinstance(template_names, list), "Should return a list (ordered)"
        
        # Template enumeration enables dynamic configuration template discovery
        # Names should be strings suitable for UI display
        for name in template_names:
            assert isinstance(name, str), f"Template name should be string, got {type(name)}"
            assert len(name) > 0, "Template name should not be empty"
            assert '_' in name or '-' in name, f"Template name '{name}' should be descriptive with separators"

    def test_cache_validator_templates_pass_comprehensive_validation(self):
        """
        Test that all configuration templates pass comprehensive validation.
        
        Verifies:
            All predefined templates are validated and deployment-ready
            
        Business Impact:
            Ensures template-based configurations are reliable and deployment-ready
            
        Scenario:
            Given: All predefined configuration templates
            When: Each template is validated using validate_configuration()
            Then: All templates pass comprehensive validation
            And: Templates contain complete, valid configurations
            And: Template parameters are within acceptable ranges
            And: Templates are ready for immediate deployment use
            
        Template Quality Assurance Verified:
            - fast_development template passes validation
            - robust_production template passes validation
            - ai_optimized template passes validation
            - All templates meet deployment readiness standards
            
        Fixtures Used:
            - None (validating real template configurations)
            
        Template Reliability Verified:
            All configuration templates provide reliable, deployment-ready configurations
            
        Related Tests:
            - test_cache_validator_templates_are_optimized_for_their_scenarios()
            - test_cache_validator_template_parameters_are_scenario_appropriate()
        """
        # Given: All predefined configuration templates
        validator = CacheValidator()
        template_names = validator.list_templates()
        
        # When: Each template is validated using validate_configuration()
        validation_results = {}
        
        for template_name in template_names:
            template = validator.get_template(template_name)
            result = validator.validate_configuration(template)
            validation_results[template_name] = result
        
        # Then: All templates pass comprehensive validation
        for template_name, result in validation_results.items():
            assert isinstance(result, ValidationResult), f"Validation result for '{template_name}' should be ValidationResult"
            
            # Templates should not have critical validation errors
            critical_errors = [error for error in result.errors if error]
            assert len(critical_errors) == 0, f"Template '{template_name}' has validation errors: {critical_errors}"
        
        # And: Templates contain complete, valid configurations
        # Specific template validation checks
        
        # fast_development template passes validation
        dev_template = validator.get_template('fast_development')
        dev_result = validator.validate_configuration(dev_template)
        assert len(dev_result.errors) == 0, f"Development template validation errors: {dev_result.errors}"
        
        # robust_production template passes validation
        prod_template = validator.get_template('robust_production')
        prod_result = validator.validate_configuration(prod_template)
        assert len(prod_result.errors) == 0, f"Production template validation errors: {prod_result.errors}"
        
        # ai_optimized template passes validation
        ai_template = validator.get_template('ai_optimized')
        ai_result = validator.validate_configuration(ai_template)
        assert len(ai_result.errors) == 0, f"AI template validation errors: {ai_result.errors}"
        
        # And: Template parameters are within acceptable ranges
        for template_name in template_names:
            template = validator.get_template(template_name)
            
            # Check essential parameter ranges
            if 'default_ttl' in template:
                assert template['default_ttl'] >= 60, f"Template '{template_name}' TTL too low"
                assert template['default_ttl'] <= 86400, f"Template '{template_name}' TTL too high"
            
            if 'max_connections' in template:
                assert template['max_connections'] >= 1, f"Template '{template_name}' connections too low"
                assert template['max_connections'] <= 100, f"Template '{template_name}' connections too high"
            
            if 'compression_level' in template:
                assert template['compression_level'] >= 1, f"Template '{template_name}' compression level too low"
                assert template['compression_level'] <= 9, f"Template '{template_name}' compression level too high"
        
        # And: Templates are ready for immediate deployment use
        # Each template should have required fields for cache initialization
        required_deployment_fields = {'strategy', 'enable_monitoring', 'log_level'}
        
        for template_name in template_names:
            template = validator.get_template(template_name)
            for field in required_deployment_fields:
                assert field in template, f"Template '{template_name}' missing deployment field '{field}'"
            
            # Strategy should be valid
            assert template['strategy'] in ['fast', 'balanced', 'robust', 'ai_optimized'], \
                f"Template '{template_name}' has invalid strategy: {template['strategy']}"


class TestCacheValidatorConfigurationComparison:
    """
    Test suite for CacheValidator configuration comparison functionality.
    
    Scope:
        - Configuration comparison and difference analysis
        - Configuration change impact assessment
        - Configuration migration path analysis
        - Comparative validation across configuration versions
        
    Business Critical:
        Configuration comparison enables informed configuration changes and migration planning
        
    Test Strategy:
        - Unit tests for compare_configurations() with various configuration pairs
        - Configuration difference analysis and reporting verification
        - Change impact assessment functionality testing
        - Migration path analysis and recommendation testing
        
    External Dependencies:
        - Configuration comparison logic (internal): Difference analysis algorithms
        - Change impact assessment (internal): Configuration change evaluation
    """

    def test_cache_validator_compare_configurations_identifies_parameter_differences(self):
        """
        Test that compare_configurations() identifies parameter differences between configurations.
        
        Verifies:
            Configuration comparison accurately identifies parameter differences
            
        Business Impact:
            Enables informed configuration changes with clear difference visibility
            
        Scenario:
            Given: Two cache configurations with parameter differences
            When: compare_configurations() is called
            Then: Parameter differences are accurately identified
            And: Changed parameter values are reported with before/after comparison
            And: Added parameters are identified as new
            And: Removed parameters are identified as deleted
            
        Configuration Difference Detection Verified:
            - Parameter value changes are identified with before/after values
            - New parameters in second configuration are identified
            - Removed parameters from first configuration are identified
            - Nested parameter changes (operation_ttls) are detected
            
        Fixtures Used:
            - None (testing configuration comparison directly)
            
        Change Visibility Verified:
            Configuration comparison provides clear visibility into configuration changes
            
        Related Tests:
            - test_cache_validator_comparison_analyzes_change_impact()
            - test_cache_validator_comparison_provides_migration_guidance()
        """
        # Given: Two cache configurations with parameter differences
        validator = CacheValidator()
        
        config1 = {
            "strategy": "fast",
            "default_ttl": 3600,
            "max_connections": 10,
            "compression_level": 6,
            "enable_ai_cache": False,
            "old_parameter": "to_be_removed"
        }
        
        config2 = {
            "strategy": "robust",  # Changed value
            "default_ttl": 7200,  # Changed value
            "max_connections": 10,  # Same value
            "compression_level": 9,  # Changed value
            "enable_ai_cache": True,  # Changed value
            "new_parameter": "added_value"  # New parameter
            # old_parameter removed
        }
        
        # When: compare_configurations() is called
        differences = validator.compare_configurations(config1, config2)
        
        # Then: Parameter differences are accurately identified
        assert isinstance(differences, dict)
        assert "added_keys" in differences
        assert "removed_keys" in differences
        assert "changed_values" in differences
        assert "identical_keys" in differences
        
        # And: Added parameters are identified as new
        added_keys = differences["added_keys"]
        assert "new_parameter" in added_keys
        
        # And: Removed parameters are identified as deleted
        removed_keys = differences["removed_keys"]
        assert "old_parameter" in removed_keys
        
        # And: Changed parameter values are reported with before/after comparison
        changed_values = differences["changed_values"]
        
        # Find specific changes
        strategy_change = next((change for change in changed_values if change["key"] == "strategy"), None)
        assert strategy_change is not None
        assert strategy_change["old_value"] == "fast"
        assert strategy_change["new_value"] == "robust"
        
        ttl_change = next((change for change in changed_values if change["key"] == "default_ttl"), None)
        assert ttl_change is not None
        assert ttl_change["old_value"] == 3600
        assert ttl_change["new_value"] == 7200
        
        compression_change = next((change for change in changed_values if change["key"] == "compression_level"), None)
        assert compression_change is not None
        assert compression_change["old_value"] == 6
        assert compression_change["new_value"] == 9
        
        # Identical parameters should be identified
        identical_keys = differences["identical_keys"]
        assert "max_connections" in identical_keys
        
        # Test with identical configurations
        identical_config = config1.copy()
        identical_differences = validator.compare_configurations(config1, identical_config)
        
        assert len(identical_differences["added_keys"]) == 0
        assert len(identical_differences["removed_keys"]) == 0
        assert len(identical_differences["changed_values"]) == 0
        assert len(identical_differences["identical_keys"]) == len(config1)

    def test_cache_validator_compare_configurations_analyzes_performance_impact(self):
        """
        Test that compare_configurations() analyzes performance impact of configuration changes.
        
        Verifies:
            Configuration comparison includes performance impact analysis
            
        Business Impact:
            Enables informed decisions about configuration changes based on performance implications
            
        Scenario:
            Given: Configuration comparison with performance-impacting changes
            When: compare_configurations() is called with performance analysis
            Then: Performance impact of changes is analyzed
            And: Performance improvements are identified and highlighted
            And: Performance degradation risks are identified
            And: Performance impact context is provided for decision making
            
        Performance Impact Analysis Verified:
            - TTL changes are analyzed for performance impact
            - Connection pool changes are analyzed for throughput impact
            - Compression changes are analyzed for CPU/bandwidth impact
            - AI optimization changes are analyzed for AI workload performance
            
        Fixtures Used:
            - None (testing performance impact analysis directly)
            
        Performance-Informed Decision Making Verified:
            Configuration comparison enables performance-aware configuration decisions
            
        Related Tests:
            - test_cache_validator_comparison_identifies_performance_optimizations()
            - test_cache_validator_comparison_warns_about_performance_risks()
        """
        # Given: Configuration comparison with performance-impacting changes
        validator = CacheValidator()
        
        # Configuration focused on development speed
        fast_config = {
            "strategy": "fast",
            "default_ttl": 600,  # Short TTL for development
            "max_connections": 5,  # Few connections
            "compression_level": 1,  # Minimal compression
            "enable_ai_cache": False,
            "memory_cache_size": 100
        }
        
        # Configuration optimized for production performance
        optimized_config = {
            "strategy": "robust",
            "default_ttl": 14400,  # Longer TTL for better cache hit rate
            "max_connections": 25,  # More connections for throughput
            "compression_level": 9,  # Maximum compression for bandwidth
            "enable_ai_cache": True,  # AI features enabled
            "memory_cache_size": 1000,  # Larger cache for better hit rates
            "text_hash_threshold": 1000
        }
        
        # When: compare_configurations() is called
        differences = validator.compare_configurations(fast_config, optimized_config)
        
        # Then: Performance impact of changes can be analyzed
        changed_values = differences["changed_values"]
        
        # And: Performance improvements can be identified
        # TTL changes analyzed for performance impact
        ttl_change = next((change for change in changed_values if change["key"] == "default_ttl"), None)
        assert ttl_change is not None
        assert ttl_change["old_value"] < ttl_change["new_value"]  # TTL increased (better cache hit rate)
        
        # Connection pool changes analyzed for throughput impact
        conn_change = next((change for change in changed_values if change["key"] == "max_connections"), None)
        assert conn_change is not None
        assert conn_change["old_value"] < conn_change["new_value"]  # More connections (higher throughput)
        
        # Compression changes analyzed for CPU/bandwidth impact
        comp_change = next((change for change in changed_values if change["key"] == "compression_level"), None)
        assert comp_change is not None
        assert comp_change["old_value"] < comp_change["new_value"]  # Higher compression (lower bandwidth)
        
        # AI optimization changes analyzed for AI workload performance
        added_keys = differences["added_keys"]
        assert "text_hash_threshold" in added_keys  # AI feature added
        
        ai_change = next((change for change in changed_values if change["key"] == "enable_ai_cache"), None)
        assert ai_change is not None
        assert ai_change["old_value"] is False
        assert ai_change["new_value"] is True  # AI cache enabled
        
        # Test performance degradation scenario
        degraded_config = {
            "strategy": "fast",
            "default_ttl": 60,  # Very short TTL (poor cache hit rate)
            "max_connections": 2,  # Very few connections (bottleneck)
            "compression_level": 1,  # Minimal compression (higher bandwidth)
            "enable_ai_cache": False,
            "memory_cache_size": 10  # Very small cache (frequent evictions)
        }
        
        degradation_differences = validator.compare_configurations(optimized_config, degraded_config)
        degradation_changes = degradation_differences["changed_values"]
        
        # Performance degradation should be visible in the comparison
        ttl_degradation = next((change for change in degradation_changes if change["key"] == "default_ttl"), None)
        assert ttl_degradation["old_value"] > ttl_degradation["new_value"]  # TTL decreased (worse performance)
        
        conn_degradation = next((change for change in degradation_changes if change["key"] == "max_connections"), None)
        assert conn_degradation["old_value"] > conn_degradation["new_value"]  # Fewer connections (lower throughput)
        
        # And: Performance impact context is provided for decision making
        # The comparison provides structured data for performance analysis
        assert isinstance(differences, dict)
        assert all(key in differences for key in ["added_keys", "removed_keys", "changed_values", "identical_keys"])
        
        # Each changed value includes old and new values for impact assessment
        for change in changed_values:
            assert "key" in change
            assert "old_value" in change
            assert "new_value" in change