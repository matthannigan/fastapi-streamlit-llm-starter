"""
Comprehensive unit tests for cache configuration validation system.

This module tests all cache validation components following docstring-driven
test development methodology. Tests verify documented contracts in Args, Returns,
Raises, and Behavior sections, focusing on WHAT should happen rather than HOW
it's implemented.

Test Classes:
    - TestValidationSeverity: Enumeration values for message severity classification
    - TestValidationMessage: Single validation message structure with context
    - TestValidationResult: Validation result container with message management
    - TestCacheValidator: Comprehensive validation system with schema and template support
    - TestCacheValidatorIntegration: Integration testing between validator components

Coverage Requirements:
    >90% coverage for infrastructure modules per project standards
    
Testing Philosophy:
    - Test WHAT should happen per docstring contracts
    - Focus on behavior verification, not implementation details
    - Mock only external dependencies (logging, JSON schema validation)
    - Test edge cases and error conditions documented in docstrings
    - Validate comprehensive validation scenarios and template system
"""

import json
import pytest
from unittest.mock import patch, MagicMock
from dataclasses import asdict

from app.infrastructure.cache.cache_validator import (
    ValidationSeverity,
    ValidationMessage,
    ValidationResult,
    CacheValidator,
    cache_validator
)


class TestValidationSeverity:
    """Test validation severity enumeration per docstring contracts."""
    
    def test_validation_severity_values(self):
        """
        Test ValidationSeverity enum values per docstring.
        
        Verifies:
            ValidationSeverity provides ERROR, WARNING, INFO levels as documented
            
        Business Impact:
            Ensures validation system can properly categorize message severity
            
        Scenario:
            Given: ValidationSeverity enum
            When: Accessing enum values
            Then: All documented severity levels are available
        """
        assert ValidationSeverity.ERROR == "error"
        assert ValidationSeverity.WARNING == "warning" 
        assert ValidationSeverity.INFO == "info"
    
    def test_validation_severity_string_behavior(self):
        """
        Test ValidationSeverity string enumeration behavior per docstring.
        
        Verifies:
            ValidationSeverity inherits from str for direct string usage
            
        Business Impact:
            Allows severity values to be used directly as strings in validation logic
            
        Scenario:
            Given: ValidationSeverity enum values
            When: Used as strings
            Then: String operations work correctly
        """
        assert isinstance(ValidationSeverity.ERROR, str)
        assert ValidationSeverity.WARNING.upper() == "WARNING"
        # ValidationSeverity should behave like a string enum
        assert ValidationSeverity.INFO == "info"
        assert ValidationSeverity.ERROR.startswith("err")


class TestValidationMessage:
    """Test validation message structure per docstring contracts."""
    
    def test_validation_message_initialization(self):
        """
        Test ValidationMessage initialization per docstring.
        
        Verifies:
            ValidationMessage can be created with severity, message, field_path, and context
            
        Business Impact:
            Ensures validation messages contain all necessary information for debugging
            
        Scenario:
            Given: ValidationMessage with all fields
            When: Object is created
            Then: All attributes are accessible and correctly stored
        """
        context = {"expected": "string", "actual": "int"}
        message = ValidationMessage(
            severity=ValidationSeverity.ERROR,
            message="Invalid field type",
            field_path="config.timeout",
            context=context
        )
        
        assert message.severity == ValidationSeverity.ERROR
        assert message.message == "Invalid field type"
        assert message.field_path == "config.timeout"
        assert message.context == context
    
    def test_validation_message_defaults(self):
        """
        Test ValidationMessage default values per docstring.
        
        Verifies:
            ValidationMessage uses empty defaults for field_path and context
            
        Business Impact:
            Simplifies message creation when field path and context aren't needed
            
        Scenario:
            Given: ValidationMessage with only required fields
            When: Object is created
            Then: Optional fields use documented defaults
        """
        message = ValidationMessage(
            severity=ValidationSeverity.WARNING,
            message="Configuration warning"
        )
        
        assert message.field_path == ""
        assert message.context == {}


class TestValidationResult:
    """Test validation result functionality per docstring contracts."""
    
    def test_validation_result_initialization_valid(self):
        """
        Test ValidationResult initialization with valid status per docstring.
        
        Verifies:
            ValidationResult correctly initializes with valid state and attributes
            
        Business Impact:
            Ensures validation results properly represent successful validation
            
        Scenario:
            Given: ValidationResult with valid status
            When: Object is created
            Then: is_valid is True and attributes are set correctly
        """
        result = ValidationResult(
            is_valid=True,
            validation_type="preset",
            schema_version="2.0"
        )
        
        assert result.is_valid is True
        assert result.validation_type == "preset"
        assert result.schema_version == "2.0"
        assert result.messages == []
    
    def test_validation_result_defaults(self):
        """
        Test ValidationResult default values per docstring.
        
        Verifies:
            ValidationResult uses documented defaults for validation_type and schema_version
            
        Business Impact:
            Simplifies result creation with sensible defaults
            
        Scenario:
            Given: ValidationResult with minimal parameters
            When: Object is created with defaults
            Then: Default values match docstring specifications
        """
        result = ValidationResult(is_valid=False)
        
        assert result.validation_type == "unknown"
        assert result.schema_version == "1.0"
        assert result.messages == []
    
    def test_errors_property(self):
        """
        Test errors property returns error messages per docstring.
        
        Verifies:
            errors property returns list of error messages only
            
        Business Impact:
            Allows callers to easily access critical validation failures
            
        Scenario:
            Given: ValidationResult with mixed message severities
            When: Accessing errors property
            Then: Only error messages are returned
        """
        result = ValidationResult(is_valid=False)
        result.add_error("Critical error")
        result.add_warning("Minor issue")
        result.add_info("Information only")
        
        errors = result.errors
        assert len(errors) == 1
        assert errors[0] == "Critical error"
    
    def test_warnings_property(self):
        """
        Test warnings property returns warning messages per docstring.
        
        Verifies:
            warnings property returns list of warning messages only
            
        Business Impact:
            Allows callers to identify non-critical issues that should be addressed
            
        Scenario:
            Given: ValidationResult with mixed message severities
            When: Accessing warnings property
            Then: Only warning messages are returned
        """
        result = ValidationResult(is_valid=True)
        result.add_error("Critical error")
        result.add_warning("Minor issue")
        result.add_info("Information only")
        
        warnings = result.warnings
        assert len(warnings) == 1
        assert warnings[0] == "Minor issue"
    
    def test_info_property(self):
        """
        Test info property returns info messages per docstring.
        
        Verifies:
            info property returns list of info messages only
            
        Business Impact:
            Allows callers to access informational validation messages
            
        Scenario:
            Given: ValidationResult with mixed message severities
            When: Accessing info property
            Then: Only info messages are returned
        """
        result = ValidationResult(is_valid=True)
        result.add_error("Critical error")
        result.add_warning("Minor issue")
        result.add_info("Information only")
        
        info = result.info
        assert len(info) == 1
        assert info[0] == "Information only"
    
    def test_add_error_marks_invalid(self):
        """
        Test add_error marks validation as invalid per docstring.
        
        Verifies:
            Adding error message sets is_valid to False as documented
            
        Business Impact:
            Ensures validation failures are properly marked to prevent invalid config usage
            
        Scenario:
            Given: ValidationResult initially valid
            When: Error is added via add_error
            Then: is_valid becomes False and error is stored
        """
        result = ValidationResult(is_valid=True)
        result.add_error("Configuration error", "field.path", {"detail": "value"})
        
        assert result.is_valid is False
        assert len(result.messages) == 1
        assert result.messages[0].severity == ValidationSeverity.ERROR
        assert result.messages[0].message == "Configuration error"
        assert result.messages[0].field_path == "field.path"
        assert result.messages[0].context == {"detail": "value"}
    
    def test_add_warning_preserves_validity(self):
        """
        Test add_warning preserves validation status per docstring.
        
        Verifies:
            Adding warning message doesn't change is_valid status
            
        Business Impact:
            Allows warnings to be recorded without failing validation
            
        Scenario:
            Given: ValidationResult with valid status
            When: Warning is added via add_warning
            Then: is_valid status is preserved and warning is stored
        """
        result = ValidationResult(is_valid=True)
        result.add_warning("Configuration warning", "field.path")
        
        assert result.is_valid is True
        assert len(result.messages) == 1
        assert result.messages[0].severity == ValidationSeverity.WARNING
        assert result.messages[0].message == "Configuration warning"
    
    def test_add_info_preserves_validity(self):
        """
        Test add_info preserves validation status per docstring.
        
        Verifies:
            Adding info message doesn't change is_valid status
            
        Business Impact:
            Allows informational messages without affecting validation outcome
            
        Scenario:
            Given: ValidationResult with valid status
            When: Info is added via add_info
            Then: is_valid status is preserved and info is stored
        """
        result = ValidationResult(is_valid=True)
        result.add_info("Configuration info")
        
        assert result.is_valid is True
        assert len(result.messages) == 1
        assert result.messages[0].severity == ValidationSeverity.INFO


class TestCacheValidator:
    """Test cache validator functionality per docstring contracts."""
    
    @pytest.fixture
    def validator(self):
        """Create CacheValidator instance for testing."""
        return CacheValidator()
    
    def test_cache_validator_initialization(self, validator):
        """
        Test CacheValidator initialization per docstring.
        
        Verifies:
            CacheValidator initializes with schemas, templates, and cache as documented
            
        Business Impact:
            Ensures validator has all necessary components for comprehensive validation
            
        Scenario:
            Given: CacheValidator initialization
            When: Validator is created
            Then: Schemas, templates, and cache are properly initialized
        """
        assert hasattr(validator, 'schemas')
        assert hasattr(validator, 'templates')
        assert hasattr(validator, '_validation_cache')
        assert isinstance(validator.schemas, dict)
        assert isinstance(validator.templates, dict)
        assert isinstance(validator._validation_cache, dict)
    
    def test_validate_preset_valid_configuration(self, validator):
        """
        Test validate_preset with valid preset configuration per docstring.
        
        Verifies:
            Valid preset configuration returns successful validation result
            
        Business Impact:
            Ensures valid presets are properly accepted by the validation system
            
        Scenario:
            Given: Complete valid preset configuration
            When: validate_preset is called
            Then: ValidationResult is valid with no errors
        """
        valid_preset = {
            "name": "test_preset",
            "description": "Test preset configuration",
            "strategy": "balanced",
            "default_ttl": 3600,
            "max_connections": 10,
            "connection_timeout": 5,
            "memory_cache_size": 100,
            "compression_threshold": 1000,
            "compression_level": 6,
            "enable_ai_cache": False,
            "enable_monitoring": True,
            "log_level": "INFO",
            "environment_contexts": ["development", "testing"]
        }
        
        result = validator.validate_preset(valid_preset)
        
        assert result.is_valid is True
        assert result.validation_type == "preset"
        assert len(result.errors) == 0
    
    def test_validate_preset_missing_required_fields(self, validator):
        """
        Test validate_preset with missing required fields per docstring.
        
        Verifies:
            Missing required fields generate validation errors as documented
            
        Business Impact:
            Prevents incomplete preset configurations from being used
            
        Scenario:
            Given: Preset configuration missing required fields
            When: validate_preset is called
            Then: ValidationResult is invalid with specific field errors
        """
        incomplete_preset = {
            "name": "incomplete",
            "description": "Missing required fields"
        }
        
        result = validator.validate_preset(incomplete_preset)
        
        assert result.is_valid is False
        assert len(result.errors) > 0
        # Check that specific required fields are mentioned in errors
        error_text = " ".join(result.errors)
        assert "strategy" in error_text
        assert "default_ttl" in error_text
    
    def test_validate_preset_invalid_field_values(self, validator):
        """
        Test validate_preset with invalid field values per docstring.
        
        Verifies:
            Invalid field values generate appropriate validation errors
            
        Business Impact:
            Prevents misconfigured presets that could cause runtime issues
            
        Scenario:
            Given: Preset configuration with invalid field values
            When: validate_preset is called
            Then: ValidationResult contains specific validation errors
        """
        invalid_preset = {
            "name": "invalid_preset",
            "description": "Preset with invalid values",
            "strategy": "balanced",
            "default_ttl": 30,  # Too low (min 60)
            "max_connections": 150,  # Too high (max 100)
            "connection_timeout": 5,
            "memory_cache_size": 100,
            "compression_threshold": 1000,
            "compression_level": 15,  # Too high (max 9)
            "enable_ai_cache": False,
            "enable_monitoring": True,
            "log_level": "INFO",
            "environment_contexts": ["development"]
        }
        
        result = validator.validate_preset(invalid_preset)
        
        assert result.is_valid is False
        error_text = " ".join(result.errors)
        assert "default_ttl" in error_text
        assert "max_connections" in error_text
        assert "compression_level" in error_text
    
    def test_validate_preset_ai_cache_enabled(self, validator):
        """
        Test validate_preset with AI cache enabled per docstring.
        
        Verifies:
            AI cache validation is triggered when enable_ai_cache is True
            
        Business Impact:
            Ensures AI-specific configurations are properly validated
            
        Scenario:
            Given: Preset with AI cache enabled and optimizations
            When: validate_preset is called
            Then: AI optimizations are validated according to constraints
        """
        ai_preset = {
            "name": "ai_preset",
            "description": "AI-enabled preset",
            "strategy": "ai_optimized",
            "default_ttl": 3600,
            "max_connections": 10,
            "connection_timeout": 5,
            "memory_cache_size": 100,
            "compression_threshold": 1000,
            "compression_level": 6,
            "enable_ai_cache": True,
            "ai_optimizations": {
                "text_hash_threshold": 500,
                "operation_ttls": {"summarize": 1800, "sentiment": 900}
            },
            "enable_monitoring": True,
            "log_level": "INFO",
            "environment_contexts": ["production"]
        }
        
        result = validator.validate_preset(ai_preset)
        
        assert result.is_valid is True
    
    def test_validate_preset_invalid_ai_optimizations(self, validator):
        """
        Test validate_preset with invalid AI optimizations per docstring.
        
        Verifies:
            Invalid AI optimization values generate validation errors
            
        Business Impact:
            Prevents AI cache misconfiguration that could cause performance issues
            
        Scenario:
            Given: Preset with invalid AI optimization values
            When: validate_preset is called
            Then: Specific AI validation errors are generated
        """
        invalid_ai_preset = {
            "name": "invalid_ai",
            "description": "Invalid AI preset",
            "strategy": "ai_optimized",
            "default_ttl": 3600,
            "max_connections": 10,
            "connection_timeout": 5,
            "memory_cache_size": 100,
            "compression_threshold": 1000,
            "compression_level": 6,
            "enable_ai_cache": True,
            "ai_optimizations": {
                "text_hash_threshold": 50,  # Too low (min 100)
                "operation_ttls": {"summarize": 30}  # Too low (min 60)
            },
            "enable_monitoring": True,
            "log_level": "INFO",
            "environment_contexts": ["production"]
        }
        
        result = validator.validate_preset(invalid_ai_preset)
        
        assert result.is_valid is False
        error_text = " ".join(result.errors)
        assert "text_hash_threshold" in error_text
        assert "operation_ttls" in error_text
    
    def test_validate_configuration_valid(self, validator):
        """
        Test validate_configuration with valid configuration per docstring.
        
        Verifies:
            Valid complete configuration returns successful validation result
            
        Business Impact:
            Ensures valid cache configurations are properly accepted
            
        Scenario:
            Given: Complete valid cache configuration
            When: validate_configuration is called
            Then: ValidationResult is valid with no errors
        """
        valid_config = {
            "strategy": "balanced",
            "redis_url": "redis://localhost:6379",
            "default_ttl": 3600,
            "max_connections": 10,
            "enable_ai_cache": False
        }
        
        result = validator.validate_configuration(valid_config)
        
        assert result.is_valid is True
        assert result.validation_type == "configuration"
    
    def test_validate_configuration_missing_strategy(self, validator):
        """
        Test validate_configuration with missing strategy per docstring.
        
        Verifies:
            Missing required strategy field generates validation error
            
        Business Impact:
            Prevents configuration usage without essential strategy specification
            
        Scenario:
            Given: Configuration missing required strategy field
            When: validate_configuration is called
            Then: ValidationResult contains strategy error
        """
        config_without_strategy = {
            "redis_url": "redis://localhost:6379",
            "default_ttl": 3600
        }
        
        result = validator.validate_configuration(config_without_strategy)
        
        assert result.is_valid is False
        assert "strategy" in " ".join(result.errors)
    
    def test_validate_configuration_invalid_redis_url(self, validator):
        """
        Test validate_configuration with invalid Redis URL per docstring.
        
        Verifies:
            Invalid Redis URL format generates validation error
            
        Business Impact:
            Prevents Redis connection failures due to malformed URLs
            
        Scenario:
            Given: Configuration with invalid Redis URL format
            When: validate_configuration is called
            Then: ValidationResult contains Redis URL error
        """
        config_invalid_redis = {
            "strategy": "balanced",
            "redis_url": "invalid://localhost:6379",  # Invalid scheme
            "default_ttl": 3600
        }
        
        result = validator.validate_configuration(config_invalid_redis)
        
        assert result.is_valid is False
        error_text = " ".join(result.errors)
        assert "Invalid Redis URL format" in error_text
    
    def test_validate_custom_overrides_valid(self, validator):
        """
        Test validate_custom_overrides with valid overrides per docstring.
        
        Verifies:
            Valid custom overrides return successful validation result
            
        Business Impact:
            Ensures custom configuration overrides are properly validated
            
        Scenario:
            Given: Valid custom override dictionary
            When: validate_custom_overrides is called
            Then: ValidationResult is valid with recognized keys
        """
        valid_overrides = {
            "redis_url": "redis://localhost:6379",
            "default_ttl": 7200,
            "max_connections": 15,
            "enable_ai_cache": True
        }
        
        result = validator.validate_custom_overrides(valid_overrides)
        
        assert result.is_valid is True
        assert result.validation_type == "custom_overrides"
    
    def test_validate_custom_overrides_unknown_keys(self, validator):
        """
        Test validate_custom_overrides with unknown keys per docstring.
        
        Verifies:
            Unknown override keys generate warnings as documented
            
        Business Impact:
            Alerts users to potentially misnamed or unsupported override keys
            
        Scenario:
            Given: Custom overrides with unknown keys
            When: validate_custom_overrides is called
            Then: ValidationResult contains warnings for unknown keys
        """
        overrides_unknown_keys = {
            "redis_url": "redis://localhost:6379",
            "unknown_setting": "value",
            "another_unknown": 42
        }
        
        result = validator.validate_custom_overrides(overrides_unknown_keys)
        
        assert result.is_valid is True  # Warnings don't make invalid
        assert len(result.warnings) >= 2
        warning_text = " ".join(result.warnings)
        assert "unknown_setting" in warning_text
        assert "another_unknown" in warning_text
    
    def test_validate_custom_overrides_invalid_types(self, validator):
        """
        Test validate_custom_overrides with invalid value types per docstring.
        
        Verifies:
            Invalid override value types generate validation errors
            
        Business Impact:
            Prevents type-related runtime errors from invalid overrides
            
        Scenario:
            Given: Custom overrides with incorrect value types
            When: validate_custom_overrides is called
            Then: ValidationResult contains type validation errors
        """
        invalid_type_overrides = {
            "default_ttl": "3600",  # Should be int
            "max_connections": 15.5,  # Should be int
            "enable_ai_cache": "true"  # Should be bool
        }
        
        result = validator.validate_custom_overrides(invalid_type_overrides)
        
        assert result.is_valid is False
        error_text = " ".join(result.errors)
        assert "default_ttl" in error_text
        assert "max_connections" in error_text
        assert "enable_ai_cache" in error_text
    
    def test_get_template_valid_name(self, validator):
        """
        Test get_template with valid template name per docstring.
        
        Verifies:
            Valid template name returns copy of template configuration
            
        Business Impact:
            Provides access to predefined configuration templates for common use cases
            
        Scenario:
            Given: Valid template name
            When: get_template is called
            Then: Template configuration copy is returned
        """
        template = validator.get_template("fast_development")
        
        assert isinstance(template, dict)
        assert "strategy" in template
        assert "default_ttl" in template
        # Verify it's a copy, not reference
        template["modified"] = "test"
        original = validator.get_template("fast_development")
        assert "modified" not in original
    
    def test_get_template_invalid_name(self, validator):
        """
        Test get_template with invalid template name per docstring.
        
        Verifies:
            Invalid template name raises ValueError as documented
            
        Business Impact:
            Prevents silent failures when requesting non-existent templates
            
        Scenario:
            Given: Invalid template name
            When: get_template is called
            Then: ValueError is raised with available template list
        """
        with pytest.raises(ValueError) as exc_info:
            validator.get_template("nonexistent_template")
        
        error_message = str(exc_info.value)
        assert "nonexistent_template" in error_message
        assert "Available:" in error_message
    
    def test_list_templates(self, validator):
        """
        Test list_templates returns available template names per docstring.
        
        Verifies:
            list_templates returns list of available template names
            
        Business Impact:
            Allows callers to discover available configuration templates
            
        Scenario:
            Given: CacheValidator with loaded templates
            When: list_templates is called
            Then: List of template names is returned
        """
        templates = validator.list_templates()
        
        assert isinstance(templates, list)
        assert len(templates) > 0
        assert "fast_development" in templates
        assert "robust_production" in templates
        assert "ai_optimized" in templates
    
    def test_compare_configurations_identical(self, validator):
        """
        Test compare_configurations with identical configurations per docstring.
        
        Verifies:
            Identical configurations show no differences
            
        Business Impact:
            Enables configuration comparison for change tracking and analysis
            
        Scenario:
            Given: Two identical configuration dictionaries
            When: compare_configurations is called
            Then: Comparison shows only identical keys
        """
        config = {"strategy": "balanced", "ttl": 3600}
        
        result = validator.compare_configurations(config, config)
        
        assert result["added_keys"] == []
        assert result["removed_keys"] == []
        assert result["changed_values"] == []
        assert len(result["identical_keys"]) == 2
    
    def test_compare_configurations_differences(self, validator):
        """
        Test compare_configurations with different configurations per docstring.
        
        Verifies:
            Different configurations show added, removed, and changed keys
            
        Business Impact:
            Provides detailed configuration change analysis for validation and auditing
            
        Scenario:
            Given: Two different configuration dictionaries
            When: compare_configurations is called
            Then: All difference categories are properly identified
        """
        config1 = {"strategy": "fast", "ttl": 1800, "removed_key": "value"}
        config2 = {"strategy": "balanced", "ttl": 3600, "added_key": "new_value"}
        
        result = validator.compare_configurations(config1, config2)
        
        assert "added_key" in result["added_keys"]
        assert "removed_key" in result["removed_keys"]
        assert len(result["changed_values"]) == 2  # strategy and ttl changed
        assert result["identical_keys"] == []


class TestCacheValidatorIntegration:
    """Test cache validator integration and edge cases per docstring contracts."""
    
    def test_preset_validation_with_consistency_warnings(self):
        """
        Test preset validation generates consistency warnings per docstring.
        
        Verifies:
            Preset consistency checks generate appropriate warnings
            
        Business Impact:
            Helps identify configuration combinations that may cause performance issues
            
        Scenario:
            Given: Preset configuration with consistency issues
            When: validate_preset is called
            Then: Consistency warnings are generated
        """
        validator = CacheValidator()
        inconsistent_preset = {
            "name": "inconsistent",
            "description": "Preset with consistency issues",
            "strategy": "balanced",
            "default_ttl": 7200,  # Long TTL
            "max_connections": 10,
            "connection_timeout": 5,
            "memory_cache_size": 50,  # Small cache with long TTL
            "compression_threshold": 1000,
            "compression_level": 6,
            "enable_ai_cache": True,  # AI enabled
            "ai_optimizations": {},  # But no optimizations
            "enable_monitoring": True,
            "log_level": "INFO",
            "environment_contexts": ["production"]
        }
        
        result = validator.validate_preset(inconsistent_preset)
        
        assert result.is_valid is True  # Valid but with warnings
        # Check for consistency warnings or info messages
        all_messages = " ".join(result.warnings + result.info)
        assert ("evictions" in all_messages or 
                "cache" in all_messages or 
                "AI" in all_messages or 
                len(result.warnings) > 0 or 
                len(result.info) > 0)
    
    def test_environment_context_validation(self):
        """
        Test environment context validation per docstring.
        
        Verifies:
            Environment contexts are validated against known values
            
        Business Impact:
            Ensures environment detection works with standard context names
            
        Scenario:
            Given: Preset with unknown environment contexts
            When: validate_preset is called
            Then: Warnings are generated for unknown contexts
        """
        validator = CacheValidator()
        preset_unknown_context = {
            "name": "unknown_env",
            "description": "Preset with unknown environment",
            "strategy": "balanced",
            "default_ttl": 3600,
            "max_connections": 10,
            "connection_timeout": 5,
            "memory_cache_size": 100,
            "compression_threshold": 1000,
            "compression_level": 6,
            "enable_ai_cache": False,
            "enable_monitoring": True,
            "log_level": "INFO",
            "environment_contexts": ["unknown_environment", "custom_env"]
        }
        
        result = validator.validate_preset(preset_unknown_context)
        
        assert result.is_valid is True  # Valid but with warnings
        warning_text = " ".join(result.warnings)
        assert "unknown_environment" in warning_text
        assert "custom_env" in warning_text
    
    def test_security_validation_warnings(self):
        """
        Test security validation generates appropriate warnings per docstring.
        
        Verifies:
            Security configuration issues generate warnings
            
        Business Impact:
            Alerts users to potential security risks in cache configuration
            
        Scenario:
            Given: Configuration with security concerns
            When: validate_configuration is called
            Then: Security warnings are generated
        """
        validator = CacheValidator()
        insecure_config = {
            "strategy": "balanced",
            "redis_url": "redis://localhost:6379",
            "redis_password": "secret123",
            "use_tls": False,  # Password without TLS
            "default_ttl": 3600
        }
        
        result = validator.validate_configuration(insecure_config)
        
        assert result.is_valid is True  # Valid but insecure
        warning_text = " ".join(result.warnings)
        assert "password" in warning_text and "TLS" in warning_text
    
    def test_performance_validation_warnings(self):
        """
        Test performance validation generates warnings per docstring.
        
        Verifies:
            Performance configuration issues generate warnings
            
        Business Impact:
            Helps identify configurations that may cause performance problems
            
        Scenario:
            Given: Configuration with performance concerns
            When: validate_configuration is called
            Then: Performance warnings are generated
        """
        validator = CacheValidator()
        perf_config = {
            "strategy": "balanced",
            "redis_url": "redis://localhost:6379",
            "max_connections": 75,  # High connection count
            "connection_timeout": 2,  # Low timeout
            "default_ttl": 3600
        }
        
        result = validator.validate_configuration(perf_config)
        
        warning_text = " ".join(result.warnings)
        assert ("connection" in warning_text and "timeout" in warning_text) or len(result.warnings) > 0
    
    @patch('app.infrastructure.cache.cache_validator.logger')
    def test_validator_initialization_logging(self, mock_logger):
        """
        Test validator initialization includes logging per docstring.
        
        Verifies:
            CacheValidator logs initialization with schemas and templates
            
        Business Impact:
            Provides audit trail for validator setup and configuration
            
        Scenario:
            Given: CacheValidator initialization
            When: Validator is created
            Then: Initialization is logged with component details
        """
        CacheValidator()
        
        mock_logger.info.assert_called_once()
        call_args = mock_logger.info.call_args[0][0]
        assert "Initialized CacheValidator" in call_args
        assert "schemas" in call_args
        assert "templates" in call_args


class TestGlobalCacheValidator:
    """Test global cache validator instance per docstring contracts."""
    
    def test_global_cache_validator_instance(self):
        """
        Test global cache_validator instance availability per docstring.
        
        Verifies:
            Global cache_validator instance is available and functional
            
        Business Impact:
            Provides convenient access to validation functionality across application
            
        Scenario:
            Given: Global cache_validator import
            When: Using cache_validator instance
            Then: Instance is functional CacheValidator
        """
        assert cache_validator is not None
        assert isinstance(cache_validator, CacheValidator)
        assert hasattr(cache_validator, 'validate_preset')
        assert hasattr(cache_validator, 'validate_configuration')
        assert hasattr(cache_validator, 'get_template')
    
    def test_global_validator_functionality(self):
        """
        Test global validator provides full functionality per docstring.
        
        Verifies:
            Global cache_validator instance provides complete validation capabilities
            
        Business Impact:
            Ensures global instance can be used for all validation needs
            
        Scenario:
            Given: Global cache_validator instance
            When: Using validation methods
            Then: All methods function correctly
        """
        # Test basic functionality
        templates = cache_validator.list_templates()
        assert isinstance(templates, list)
        assert len(templates) > 0
        
        # Test template retrieval
        template = cache_validator.get_template("fast_development")
        assert isinstance(template, dict)
        
        # Test validation
        result = cache_validator.validate_custom_overrides({"default_ttl": 3600})
        assert isinstance(result, ValidationResult)
        assert result.is_valid is True