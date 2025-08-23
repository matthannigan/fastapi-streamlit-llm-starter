"""
Comprehensive unit tests for cache configuration system.

This module tests the cache configuration components following docstring-driven
test development methodology. Tests verify documented contracts in Args, Returns,
Raises, and Behavior sections.

Test Classes:
    - TestValidationResult: Error and warning management functionality
    - TestAICacheConfig: AI-specific configuration validation
    - TestCacheConfig: Core configuration validation and environment loading
    - TestCacheConfigBuilder: Builder pattern implementation and fluent interface
    - TestEnvironmentPresets: Preset system integration with cache_presets module

Coverage Requirements:
    >90% coverage for infrastructure modules per project standards
    
Testing Philosophy:
    - Test WHAT should happen per docstring contracts
    - Focus on behavior verification, not implementation details
    - Mock only external dependencies (file system, environment, cache_presets)
    - Test edge cases and error conditions documented in docstrings
"""

import hashlib
import json
import os
import pytest
import tempfile
from pathlib import Path
from unittest.mock import patch, mock_open, MagicMock

from app.infrastructure.cache.config import (
    ValidationResult,
    AICacheConfig,
    CacheConfig,
    CacheConfigBuilder,
    EnvironmentPresets
)
from app.core.exceptions import ConfigurationError, ValidationError


class TestValidationResult:
    """Test validation result functionality per docstring contracts."""
    
    def test_validation_result_initialization_valid(self):
        """
        Test ValidationResult initialization with valid status.
        
        Verifies:
            ValidationResult can be created with valid status and empty error/warning lists
            
        Business Impact:
            Ensures validation system can represent successful validation states
            
        Scenario:
            Given: ValidationResult initialized with is_valid=True
            When: Object is created
            Then: Object has correct state with empty error and warning lists
        """
        result = ValidationResult(is_valid=True)
        
        assert result.is_valid is True
        assert result.errors == []
        assert result.warnings == []
    
    def test_validation_result_initialization_invalid(self):
        """
        Test ValidationResult initialization with invalid status.
        
        Verifies:
            ValidationResult can be created with invalid status and populated lists
            
        Business Impact:
            Ensures validation system can represent failed validation states with details
            
        Scenario:
            Given: ValidationResult initialized with is_valid=False and error list
            When: Object is created
            Then: Object maintains provided state
        """
        errors = ["error1", "error2"]
        warnings = ["warning1"]
        result = ValidationResult(is_valid=False, errors=errors, warnings=warnings)
        
        assert result.is_valid is False
        assert result.errors == errors
        assert result.warnings == warnings
    
    def test_add_error_marks_invalid(self):
        """
        Test that add_error method marks validation as invalid per docstring.
        
        Verifies:
            Adding error message sets is_valid to False and appends to errors list
            
        Business Impact:
            Prevents invalid configurations from being accepted as valid
            
        Scenario:
            Given: Valid ValidationResult
            When: Error is added via add_error method
            Then: is_valid becomes False and error appears in errors list
        """
        result = ValidationResult(is_valid=True)
        error_message = "test error"
        
        result.add_error(error_message)
        
        assert result.is_valid is False
        assert error_message in result.errors
        assert len(result.errors) == 1
    
    def test_add_warning_preserves_validity(self):
        """
        Test that add_warning method preserves validation status per docstring.
        
        Verifies:
            Adding warning message does not change is_valid status
            
        Business Impact:
            Allows configuration warnings without preventing system operation
            
        Scenario:
            Given: Valid ValidationResult
            When: Warning is added via add_warning method
            Then: is_valid remains unchanged and warning appears in warnings list
        """
        result = ValidationResult(is_valid=True)
        warning_message = "test warning"
        
        result.add_warning(warning_message)
        
        assert result.is_valid is True
        assert warning_message in result.warnings
        assert len(result.warnings) == 1
    
    def test_multiple_errors_and_warnings(self):
        """
        Test handling of multiple errors and warnings per docstring behavior.
        
        Verifies:
            Multiple errors and warnings can be accumulated correctly
            
        Business Impact:
            Enables comprehensive validation reporting with all issues identified
            
        Scenario:
            Given: ValidationResult
            When: Multiple errors and warnings are added
            Then: All messages are preserved and validity reflects errors
        """
        result = ValidationResult(is_valid=True)
        
        result.add_error("error1")
        result.add_error("error2")
        result.add_warning("warning1")
        result.add_warning("warning2")
        
        assert result.is_valid is False
        assert len(result.errors) == 2
        assert len(result.warnings) == 2
        assert "error1" in result.errors
        assert "error2" in result.errors
        assert "warning1" in result.warnings
        assert "warning2" in result.warnings


class TestAICacheConfig:
    """Test AI-specific cache configuration per docstring contracts."""
    
    def test_ai_cache_config_default_initialization(self):
        """
        Test AICacheConfig initialization with default values per docstring.
        
        Verifies:
            Default values match those documented in docstring Attributes section
            
        Business Impact:
            Ensures consistent AI cache behavior across deployments without explicit configuration
            
        Scenario:
            Given: AICacheConfig created with no parameters
            When: Object is initialized
            Then: All attributes match documented default values
        """
        config = AICacheConfig()
        
        # Test default values per docstring
        assert config.text_hash_threshold == 1000
        assert config.hash_algorithm == "sha256"
        assert config.enable_smart_promotion is True
        assert config.max_text_length == 100000
        
        # Test default text_size_tiers per docstring
        expected_tiers = {"small": 1000, "medium": 10000, "large": 100000}
        assert config.text_size_tiers == expected_tiers
        
        # Test default operation_ttls per docstring
        expected_ttls = {
            "summarize": 7200,  # 2 hours
            "sentiment": 3600,  # 1 hour
            "key_points": 5400, # 1.5 hours
            "questions": 4800,  # 1.33 hours
            "qa": 3600         # 1 hour
        }
        assert config.operation_ttls == expected_ttls
    
    def test_validate_success_with_valid_configuration(self):
        """
        Test validation success with valid AI configuration per docstring contract.
        
        Verifies:
            Valid configuration passes validation and returns valid result
            
        Business Impact:
            Allows properly configured AI cache systems to operate without validation errors
            
        Scenario:
            Given: AICacheConfig with all valid settings
            When: validate() is called
            Then: ValidationResult shows success with no errors
        """
        config = AICacheConfig(
            text_hash_threshold=500,
            hash_algorithm="sha256",
            text_size_tiers={"small": 100, "medium": 1000, "large": 10000},
            operation_ttls={"test_op": 3600},
            max_text_length=50000
        )
        
        result = config.validate()
        
        assert result.is_valid is True
        assert len(result.errors) == 0
    
    def test_validate_text_hash_threshold_boundary_errors(self):
        """
        Test validation of text_hash_threshold boundaries per docstring behavior.
        
        Verifies:
            text_hash_threshold must be positive as documented
            
        Business Impact:
            Prevents invalid threshold configurations that could break text hashing
            
        Scenario:
            Given: AICacheConfig with zero or negative text_hash_threshold
            When: validate() is called
            Then: ValidationResult contains error about threshold requirement
        """
        # Test zero threshold
        config = AICacheConfig(text_hash_threshold=0)
        result = config.validate()
        
        assert result.is_valid is False
        assert any("text_hash_threshold must be positive" in error for error in result.errors)
        
        # Test negative threshold
        config = AICacheConfig(text_hash_threshold=-100)
        result = config.validate()
        
        assert result.is_valid is False
        assert any("text_hash_threshold must be positive" in error for error in result.errors)
    
    def test_validate_text_size_tiers_errors(self):
        """
        Test validation of text_size_tiers per docstring validation rules.
        
        Verifies:
            text_size_tiers values must be positive integers as documented
            
        Business Impact:
            Prevents invalid tier configurations that could break size-based caching logic
            
        Scenario:
            Given: AICacheConfig with invalid text_size_tiers values
            When: validate() is called
            Then: ValidationResult contains specific tier validation errors
        """
        # Test negative tier value
        config = AICacheConfig(text_size_tiers={"small": -100, "medium": 1000})
        result = config.validate()
        
        assert result.is_valid is False
        assert any("text_size_tiers['small'] must be a positive integer" in error for error in result.errors)
        
        # Test zero tier value
        config = AICacheConfig(text_size_tiers={"medium": 0})
        result = config.validate()
        
        assert result.is_valid is False
        assert any("text_size_tiers['medium'] must be a positive integer" in error for error in result.errors)
        
        # Test non-integer tier value
        config = AICacheConfig(text_size_tiers={"large": "invalid"})  # type: ignore[arg-type]
        result = config.validate()
        
        assert result.is_valid is False
        assert any("text_size_tiers['large'] must be a positive integer" in error for error in result.errors)
    
    def test_validate_text_size_tiers_ordering_warning(self):
        """
        Test validation warning for text_size_tiers ordering per docstring behavior.
        
        Verifies:
            Non-ascending tier values generate warnings as documented
            
        Business Impact:
            Alerts administrators to potentially confusing tier configurations
            
        Scenario:
            Given: AICacheConfig with descending text_size_tiers values
            When: validate() is called
            Then: ValidationResult contains warning about tier ordering
        """
        config = AICacheConfig(text_size_tiers={"small": 10000, "medium": 1000, "large": 100})
        result = config.validate()
        
        # Should be valid but have warnings
        assert result.is_valid is True
        assert any("text_size_tiers values should be in ascending order" in warning for warning in result.warnings)
    
    def test_validate_operation_ttls_errors(self):
        """
        Test validation of operation_ttls per docstring validation rules.
        
        Verifies:
            operation_ttls values must be positive integers as documented
            
        Business Impact:
            Prevents invalid TTL configurations that could break cache expiration
            
        Scenario:
            Given: AICacheConfig with invalid operation_ttls values
            When: validate() is called
            Then: ValidationResult contains specific TTL validation errors
        """
        # Test negative TTL
        config = AICacheConfig(operation_ttls={"test_op": -100})
        result = config.validate()
        
        assert result.is_valid is False
        assert any("operation_ttls['test_op'] must be a positive integer" in error for error in result.errors)
        
        # Test zero TTL
        config = AICacheConfig(operation_ttls={"test_op": 0})
        result = config.validate()
        
        assert result.is_valid is False
        assert any("operation_ttls['test_op'] must be a positive integer" in error for error in result.errors)
        
        # Test non-integer TTL
        config = AICacheConfig(operation_ttls={"test_op": "invalid"})  # type: ignore[arg-type]
        result = config.validate()
        
        assert result.is_valid is False
        assert any("operation_ttls['test_op'] must be a positive integer" in error for error in result.errors)
    
    def test_validate_operation_ttls_long_warning(self):
        """
        Test validation warning for very long operation_ttls per docstring behavior.
        
        Verifies:
            TTL values longer than 1 week generate warnings as documented
            
        Business Impact:
            Alerts administrators to potentially excessive cache durations
            
        Scenario:
            Given: AICacheConfig with TTL longer than 1 week (604800 seconds)
            When: validate() is called
            Then: ValidationResult contains warning about long TTL
        """
        long_ttl = 604801  # 1 week + 1 second
        config = AICacheConfig(operation_ttls={"test_op": long_ttl})
        result = config.validate()
        
        # Should be valid but have warnings
        assert result.is_valid is True
        assert any("operation_ttls['test_op'] is very long (>1 week)" in warning for warning in result.warnings)
    
    def test_validate_hash_algorithm_error(self):
        """
        Test validation of hash_algorithm per docstring validation rules.
        
        Verifies:
            Invalid hash algorithms generate errors as documented
            
        Business Impact:
            Prevents system failures due to unsupported hash algorithms
            
        Scenario:
            Given: AICacheConfig with unsupported hash algorithm
            When: validate() is called
            Then: ValidationResult contains hash algorithm error
        """
        config = AICacheConfig(hash_algorithm="invalid_hash")
        result = config.validate()
        
        assert result.is_valid is False
        assert any("hash_algorithm 'invalid_hash' is not supported" in error for error in result.errors)
    
    def test_validate_hash_algorithm_success(self):
        """
        Test validation of supported hash algorithms per docstring behavior.
        
        Verifies:
            Supported hash algorithms pass validation
            
        Business Impact:
            Ensures properly configured hash algorithms work correctly
            
        Scenario:
            Given: AICacheConfig with supported hash algorithms
            When: validate() is called
            Then: ValidationResult shows success
        """
        # Test common supported algorithms
        for algorithm in ["sha256", "sha1", "md5", "sha512"]:
            config = AICacheConfig(hash_algorithm=algorithm)
            result = config.validate()
            
            assert result.is_valid is True, f"Algorithm {algorithm} should be supported"
    
    def test_validate_max_text_length_error(self):
        """
        Test validation of max_text_length per docstring validation rules.
        
        Verifies:
            max_text_length must be positive as documented
            
        Business Impact:
            Prevents invalid text length limits that could break text processing
            
        Scenario:
            Given: AICacheConfig with zero or negative max_text_length
            When: validate() is called
            Then: ValidationResult contains error about text length requirement
        """
        # Test zero length
        config = AICacheConfig(max_text_length=0)
        result = config.validate()
        
        assert result.is_valid is False
        assert any("max_text_length must be positive" in error for error in result.errors)
        
        # Test negative length
        config = AICacheConfig(max_text_length=-1000)
        result = config.validate()
        
        assert result.is_valid is False
        assert any("max_text_length must be positive" in error for error in result.errors)


class TestCacheConfig:
    """Test core cache configuration per docstring contracts."""
    
    def test_cache_config_default_initialization(self):
        """
        Test CacheConfig initialization with default values per docstring.
        
        Verifies:
            Default values match those documented in docstring Attributes section
            
        Business Impact:
            Ensures consistent cache behavior across deployments without explicit configuration
            
        Scenario:
            Given: CacheConfig created with no parameters
            When: Object is initialized
            Then: All attributes match documented default values
        """
        config = CacheConfig()
        
        # Test core defaults per docstring
        assert config.redis_url is None
        assert config.redis_password is None
        assert config.use_tls is False
        assert config.tls_cert_path is None
        assert config.tls_key_path is None
        assert config.default_ttl == 3600  # 1 hour
        assert config.memory_cache_size == 100
        assert config.compression_threshold == 1000
        assert config.compression_level == 6
        assert config.environment == "development"
        assert config.ai_config is None
        assert config.enable_ai_cache is False
    
    def test_validate_redis_url_format_errors(self):
        """
        Test validation of Redis URL format per docstring validation rules.
        
        Verifies:
            Redis URL must start with 'redis://' or 'rediss://' as documented
            
        Business Impact:
            Prevents connection failures due to malformed Redis URLs
            
        Scenario:
            Given: CacheConfig with invalid Redis URL format
            When: validate() is called
            Then: ValidationResult contains specific URL format error
        """
        # Test invalid URL format
        config = CacheConfig(redis_url="http://localhost:6379")
        result = config.validate()
        
        assert result.is_valid is False
        assert any("redis_url must start with 'redis://' or 'rediss://'" in error for error in result.errors)
        
        # Test completely invalid URL
        config = CacheConfig(redis_url="invalid-url")
        result = config.validate()
        
        assert result.is_valid is False
        assert any("redis_url must start with 'redis://' or 'rediss://'" in error for error in result.errors)
    
    def test_validate_redis_url_format_success(self):
        """
        Test validation of valid Redis URL formats per docstring behavior.
        
        Verifies:
            Valid Redis URL formats pass validation
            
        Business Impact:
            Ensures properly formatted Redis URLs are accepted
            
        Scenario:
            Given: CacheConfig with valid Redis URL formats
            When: validate() is called
            Then: ValidationResult shows success for URL validation
        """
        # Test standard redis:// URL
        config = CacheConfig(redis_url="redis://localhost:6379")
        result = config.validate()
        
        assert result.is_valid is True
        
        # Test secure rediss:// URL
        config = CacheConfig(redis_url="rediss://secure-redis:6380")
        result = config.validate()
        
        assert result.is_valid is True
    
    def test_validate_ttl_positive_requirement(self):
        """
        Test validation of default_ttl positive requirement per docstring.
        
        Verifies:
            default_ttl must be positive as documented
            
        Business Impact:
            Prevents invalid TTL configurations that could break cache expiration
            
        Scenario:
            Given: CacheConfig with zero or negative default_ttl
            When: validate() is called
            Then: ValidationResult contains TTL requirement error
        """
        # Test zero TTL
        config = CacheConfig(default_ttl=0)
        result = config.validate()
        
        assert result.is_valid is False
        assert any("default_ttl must be positive" in error for error in result.errors)
        
        # Test negative TTL
        config = CacheConfig(default_ttl=-100)
        result = config.validate()
        
        assert result.is_valid is False
        assert any("default_ttl must be positive" in error for error in result.errors)
    
    def test_validate_memory_cache_size_positive_requirement(self):
        """
        Test validation of memory_cache_size positive requirement per docstring.
        
        Verifies:
            memory_cache_size must be positive as documented
            
        Business Impact:
            Prevents invalid cache size configurations that could break memory caching
            
        Scenario:
            Given: CacheConfig with zero or negative memory_cache_size
            When: validate() is called
            Then: ValidationResult contains cache size requirement error
        """
        # Test zero cache size
        config = CacheConfig(memory_cache_size=0)
        result = config.validate()
        
        assert result.is_valid is False
        assert any("memory_cache_size must be positive" in error for error in result.errors)
        
        # Test negative cache size
        config = CacheConfig(memory_cache_size=-50)
        result = config.validate()
        
        assert result.is_valid is False
        assert any("memory_cache_size must be positive" in error for error in result.errors)
    
    def test_validate_compression_level_range(self):
        """
        Test validation of compression_level range per docstring validation rules.
        
        Verifies:
            compression_level must be between 1 and 9 as documented
            
        Business Impact:
            Prevents invalid compression configurations that could cause system errors
            
        Scenario:
            Given: CacheConfig with compression_level outside valid range
            When: validate() is called
            Then: ValidationResult contains compression level range error
        """
        # Test below minimum
        config = CacheConfig(compression_level=0)
        result = config.validate()
        
        assert result.is_valid is False
        assert any("compression_level must be between 1 and 9" in error for error in result.errors)
        
        # Test above maximum
        config = CacheConfig(compression_level=10)
        result = config.validate()
        
        assert result.is_valid is False
        assert any("compression_level must be between 1 and 9" in error for error in result.errors)
        
        # Test valid range boundaries
        for level in [1, 9]:
            config = CacheConfig(compression_level=level)
            result = config.validate()
            assert result.is_valid is True, f"Compression level {level} should be valid"
    
    def test_validate_compression_threshold_non_negative(self):
        """
        Test validation of compression_threshold non-negative requirement per docstring.
        
        Verifies:
            compression_threshold must be non-negative as documented
            
        Business Impact:
            Prevents invalid threshold configurations that could break compression logic
            
        Scenario:
            Given: CacheConfig with negative compression_threshold
            When: validate() is called
            Then: ValidationResult contains threshold requirement error
        """
        config = CacheConfig(compression_threshold=-100)
        result = config.validate()
        
        assert result.is_valid is False
        assert any("compression_threshold must be non-negative" in error for error in result.errors)
        
        # Test zero is acceptable
        config = CacheConfig(compression_threshold=0)
        result = config.validate()
        assert result.is_valid is True
    
    @patch('pathlib.Path.exists')
    def test_validate_tls_certificate_file_production_error(self, mock_exists):
        """
        Test TLS certificate file validation in production environment per docstring.
        
        Verifies:
            Missing TLS certificate files generate errors in production as documented
            
        Business Impact:
            Prevents production deployments with missing security certificates
            
        Scenario:
            Given: Production CacheConfig with TLS enabled but missing certificate file
            When: validate() is called
            Then: ValidationResult contains certificate file error
        """
        mock_exists.return_value = False
        config = CacheConfig(
            environment="production",
            use_tls=True,
            tls_cert_path="/path/to/missing/cert.pem"
        )
        
        result = config.validate()
        
        assert result.is_valid is False
        assert any("TLS certificate file not found: /path/to/missing/cert.pem" in error for error in result.errors)
    
    @patch('pathlib.Path.exists')
    def test_validate_tls_certificate_file_development_warning(self, mock_exists):
        """
        Test TLS certificate file validation in development environment per docstring.
        
        Verifies:
            Missing TLS certificate files generate warnings in non-production as documented
            
        Business Impact:
            Allows development work to continue with TLS configuration warnings
            
        Scenario:
            Given: Development CacheConfig with TLS enabled but missing certificate file
            When: validate() is called
            Then: ValidationResult contains certificate file warning but is still valid
        """
        mock_exists.return_value = False
        config = CacheConfig(
            environment="development",
            use_tls=True,
            tls_cert_path="/path/to/missing/cert.pem"
        )
        
        result = config.validate()
        
        assert result.is_valid is True
        assert any("TLS certificate file not found: /path/to/missing/cert.pem" in warning for warning in result.warnings)
    
    @patch('pathlib.Path.exists')
    def test_validate_tls_key_file_validation(self, mock_exists):
        """
        Test TLS key file validation per docstring validation rules.
        
        Verifies:
            Missing TLS key files are validated according to environment as documented
            
        Business Impact:
            Ensures TLS key file validation matches certificate file validation
            
        Scenario:
            Given: CacheConfig with TLS enabled but missing key file
            When: validate() is called
            Then: ValidationResult handles key file validation per environment
        """
        mock_exists.return_value = False
        
        # Test production - should error
        config = CacheConfig(
            environment="production",
            use_tls=True,
            tls_key_path="/path/to/missing/key.pem"
        )
        result = config.validate()
        assert result.is_valid is False
        assert any("TLS key file not found: /path/to/missing/key.pem" in error for error in result.errors)
        
        # Test development - should warn
        config = CacheConfig(
            environment="development",
            use_tls=True,
            tls_key_path="/path/to/missing/key.pem"
        )
        result = config.validate()
        assert result.is_valid is True
        assert any("TLS key file not found: /path/to/missing/key.pem" in warning for warning in result.warnings)
    
    def test_validate_ai_config_integration(self):
        """
        Test validation of AI configuration integration per docstring behavior.
        
        Verifies:
            AI configuration validation is integrated into overall validation as documented
            
        Business Impact:
            Ensures AI cache features are properly validated within main configuration
            
        Scenario:
            Given: CacheConfig with invalid AI configuration
            When: validate() is called
            Then: ValidationResult includes AI validation errors
        """
        # Create config with invalid AI settings
        ai_config = AICacheConfig(text_hash_threshold=-100)  # Invalid
        config = CacheConfig(ai_config=ai_config)
        
        result = config.validate()
        
        assert result.is_valid is False
        assert any("text_hash_threshold must be positive" in error for error in result.errors)
    
    def test_to_dict_removes_internal_fields(self):
        """
        Test to_dict removes internal fields per docstring contract.
        
        Verifies:
            Internal fields like _from_env are excluded from dictionary representation
            
        Business Impact:
            Ensures serialized configuration doesn't contain internal implementation details
            
        Scenario:
            Given: CacheConfig with internal field set
            When: to_dict() is called
            Then: Dictionary does not contain internal fields
        """
        config = CacheConfig()
        config._from_env = True
        
        config_dict = config.to_dict()
        
        assert "_from_env" not in config_dict
        assert "default_ttl" in config_dict  # Verify regular fields are present
        assert "environment" in config_dict
    
    @patch.dict(os.environ, {
        "CACHE_REDIS_URL": "redis://test:6379",
        "CACHE_DEFAULT_TTL": "1800",
        "CACHE_USE_TLS": "true",
        "CACHE_ENVIRONMENT": "testing"
    }, clear=False)
    def test_load_from_environment_success(self):
        """
        Test successful environment variable loading per docstring behavior.
        
        Verifies:
            Environment variables are loaded and converted correctly as documented
            
        Business Impact:
            Enables configuration through environment variables for deployment flexibility
            
        Scenario:
            Given: Valid environment variables set
            When: Configuration loads from environment
            Then: Configuration values reflect environment variable values
        """
        config = CacheConfig()
        config._from_env = True
        config._load_from_environment()
        
        assert config.redis_url == "redis://test:6379"
        assert config.default_ttl == 1800
        assert config.use_tls is True
        assert config.environment == "testing"
    
    @patch.dict(os.environ, {
        "CACHE_DEFAULT_TTL": "invalid_number"
    }, clear=False)
    def test_load_from_environment_conversion_error(self):
        """
        Test environment loading with type conversion error per docstring.
        
        Verifies:
            Invalid environment values raise ConfigurationError as documented
            
        Business Impact:
            Prevents system startup with invalid environment configuration
            
        Scenario:
            Given: Environment variable with invalid value for expected type
            When: Configuration attempts to load from environment
            Then: ConfigurationError is raised with descriptive message
        """
        with pytest.raises(ConfigurationError) as exc_info:
            config = CacheConfig()
            config._from_env = True
            config._load_from_environment()
        
        assert "Invalid value for CACHE_DEFAULT_TTL" in str(exc_info.value)
    
    @patch.dict(os.environ, {
        "CACHE_ENABLE_AI_FEATURES": "true",
        "CACHE_TEXT_HASH_THRESHOLD": "2000"
    }, clear=False)
    def test_load_ai_config_from_environment(self):
        """
        Test loading AI configuration from environment variables per docstring.
        
        Verifies:
            AI configuration is loaded when AI features are enabled as documented
            
        Business Impact:
            Enables AI cache feature configuration through environment variables
            
        Scenario:
            Given: AI features enabled via environment and AI configuration variables set
            When: Configuration loads from environment
            Then: AI configuration is created and populated with environment values
        """
        config = CacheConfig()
        config._from_env = True
        config._load_from_environment()
        
        assert config.ai_config is not None
        assert config.ai_config.text_hash_threshold == 2000
    
    @patch.dict(os.environ, {
        "CACHE_ENABLE_AI_FEATURES": "true",
        "CACHE_OPERATION_TTLS": '{"custom_op": 1800, "test_op": 900}'
    }, clear=False)
    def test_load_operation_ttls_from_json(self):
        """
        Test loading operation TTLs from JSON environment variable per docstring.
        
        Verifies:
            Operation TTLs can be loaded from JSON string as documented
            
        Business Impact:
            Enables flexible operation-specific TTL configuration
            
        Scenario:
            Given: Valid JSON string in CACHE_OPERATION_TTLS environment variable
            When: Configuration loads AI features from environment
            Then: Operation TTLs are parsed and applied to AI configuration
        """
        config = CacheConfig()
        config._from_env = True
        config._load_from_environment()
        
        assert config.ai_config is not None
        assert config.ai_config.operation_ttls["custom_op"] == 1800
        assert config.ai_config.operation_ttls["test_op"] == 900
    
    @patch.dict(os.environ, {
        "CACHE_ENABLE_AI_FEATURES": "true",
        "CACHE_OPERATION_TTLS": 'invalid json'
    }, clear=False)
    def test_load_operation_ttls_invalid_json(self):
        """
        Test handling of invalid JSON in operation TTLs per docstring error handling.
        
        Verifies:
            Invalid JSON in CACHE_OPERATION_TTLS raises ConfigurationError as documented
            
        Business Impact:
            Prevents system startup with malformed operation TTL configuration
            
        Scenario:
            Given: Invalid JSON string in CACHE_OPERATION_TTLS environment variable
            When: Configuration attempts to load AI features from environment
            Then: ConfigurationError is raised with JSON parsing error details
        """
        with pytest.raises(ConfigurationError) as exc_info:
            config = CacheConfig()
            config._from_env = True
            config._load_from_environment()
        
        assert "Invalid JSON in CACHE_OPERATION_TTLS" in str(exc_info.value)
    
    def test_parse_bool_method(self):
        """
        Test _parse_bool method per docstring behavior.
        
        Verifies:
            Boolean parsing works for documented values
            
        Business Impact:
            Ensures consistent boolean interpretation across configuration
            
        Scenario:
            Given: Various string representations of boolean values
            When: _parse_bool is called
            Then: Correct boolean values are returned
        """
        # Test true values
        for true_val in ['true', '1', 'yes', 'on', 'TRUE', 'True', 'YES', 'On']:
            assert CacheConfig._parse_bool(true_val) is True, f"'{true_val}' should parse as True"
        
        # Test false values
        for false_val in ['false', '0', 'no', 'off', '', 'invalid']:
            assert CacheConfig._parse_bool(false_val) is False, f"'{false_val}' should parse as False"


class TestCacheConfigBuilder:
    """Test cache configuration builder pattern per docstring contracts."""
    
    def test_builder_initialization(self):
        """
        Test CacheConfigBuilder initialization per docstring.
        
        Verifies:
            Builder initializes with empty configuration as documented
            
        Business Impact:
            Ensures builder starts with clean state for configuration construction
            
        Scenario:
            Given: CacheConfigBuilder is created
            When: Builder is initialized
            Then: Internal configuration is empty CacheConfig with defaults
        """
        builder = CacheConfigBuilder()
        
        assert builder._config is not None
        assert isinstance(builder._config, CacheConfig)
        assert builder._config.environment == "development"  # Default value
    
    def test_for_environment_valid_environments(self):
        """
        Test for_environment method with valid environments per docstring.
        
        Verifies:
            Valid environment names are accepted and environment-specific defaults applied
            
        Business Impact:
            Enables environment-specific configuration with appropriate defaults
            
        Scenario:
            Given: CacheConfigBuilder instance
            When: for_environment is called with valid environment name
            Then: Environment is set and appropriate defaults are applied
        """
        builder = CacheConfigBuilder()
        
        # Test development environment
        result = builder.for_environment("development")
        assert result is builder  # Fluent interface
        assert builder._config.environment == "development"
        assert builder._config.default_ttl == 1800  # 30 minutes
        assert builder._config.memory_cache_size == 50
        
        # Test production environment
        builder = CacheConfigBuilder()
        result = builder.for_environment("production")
        assert result is builder
        assert builder._config.environment == "production"
        assert builder._config.default_ttl == 7200  # 2 hours
        assert builder._config.memory_cache_size == 200
        
        # Test testing environment
        builder = CacheConfigBuilder()
        result = builder.for_environment("testing")
        assert result is builder
        assert builder._config.environment == "testing"
        assert builder._config.default_ttl == 60  # 1 minute
        assert builder._config.memory_cache_size == 25
    
    def test_for_environment_invalid_environment_error(self):
        """
        Test for_environment method with invalid environment per docstring.
        
        Verifies:
            Invalid environment names raise ValidationError as documented
            
        Business Impact:
            Prevents configuration with unsupported environment settings
            
        Scenario:
            Given: CacheConfigBuilder instance
            When: for_environment is called with invalid environment name
            Then: ValidationError is raised with supported environments list
        """
        builder = CacheConfigBuilder()
        
        with pytest.raises(ValidationError) as exc_info:
            builder.for_environment("invalid_env")
        
        assert "Invalid environment: invalid_env" in str(exc_info.value)
        assert "development" in str(exc_info.value)
        assert "testing" in str(exc_info.value)
        assert "production" in str(exc_info.value)
    
    def test_with_redis_configuration(self):
        """
        Test with_redis method per docstring contract.
        
        Verifies:
            Redis connection settings are configured correctly as documented
            
        Business Impact:
            Enables flexible Redis connection configuration through builder
            
        Scenario:
            Given: CacheConfigBuilder instance
            When: with_redis is called with connection parameters
            Then: Redis configuration is set and builder supports method chaining
        """
        builder = CacheConfigBuilder()
        
        result = builder.with_redis(
            redis_url="redis://localhost:6379",
            password="secret",
            use_tls=True
        )
        
        assert result is builder  # Fluent interface
        assert builder._config.redis_url == "redis://localhost:6379"
        assert builder._config.redis_password == "secret"
        assert builder._config.use_tls is True
    
    def test_with_security_configuration(self):
        """
        Test with_security method per docstring contract.
        
        Verifies:
            TLS security settings are configured correctly as documented
            
        Business Impact:
            Enables secure TLS configuration through builder pattern
            
        Scenario:
            Given: CacheConfigBuilder instance
            When: with_security is called with TLS parameters
            Then: TLS configuration is set and TLS is auto-enabled
        """
        builder = CacheConfigBuilder()
        
        result = builder.with_security(
            tls_cert_path="/path/to/cert.pem",
            tls_key_path="/path/to/key.pem"
        )
        
        assert result is builder  # Fluent interface
        assert builder._config.tls_cert_path == "/path/to/cert.pem"
        assert builder._config.tls_key_path == "/path/to/key.pem"
        assert builder._config.use_tls is True  # Auto-enabled per docstring
    
    def test_with_compression_configuration(self):
        """
        Test with_compression method per docstring contract.
        
        Verifies:
            Compression settings are configured correctly as documented
            
        Business Impact:
            Enables compression configuration optimization through builder
            
        Scenario:
            Given: CacheConfigBuilder instance
            When: with_compression is called with compression parameters
            Then: Compression configuration is set correctly
        """
        builder = CacheConfigBuilder()
        
        result = builder.with_compression(threshold=2000, level=8)
        
        assert result is builder  # Fluent interface
        assert builder._config.compression_threshold == 2000
        assert builder._config.compression_level == 8
    
    def test_with_memory_cache_configuration(self):
        """
        Test with_memory_cache method per docstring contract.
        
        Verifies:
            Memory cache size is configured correctly as documented
            
        Business Impact:
            Enables memory cache optimization through builder pattern
            
        Scenario:
            Given: CacheConfigBuilder instance
            When: with_memory_cache is called with size parameter
            Then: Memory cache size is set correctly
        """
        builder = CacheConfigBuilder()
        
        result = builder.with_memory_cache(size=500)
        
        assert result is builder  # Fluent interface
        assert builder._config.memory_cache_size == 500
    
    def test_with_ai_features_valid_options(self):
        """
        Test with_ai_features method with valid options per docstring.
        
        Verifies:
            AI features are enabled and configured correctly as documented
            
        Business Impact:
            Enables AI-specific cache optimization through builder pattern
            
        Scenario:
            Given: CacheConfigBuilder instance
            When: with_ai_features is called with valid AI options
            Then: AI configuration is created and options are applied
        """
        builder = CacheConfigBuilder()
        
        result = builder.with_ai_features(
            text_hash_threshold=2000,
            hash_algorithm="sha512",
            max_text_length=50000
        )
        
        assert result is builder  # Fluent interface
        assert builder._config.ai_config is not None
        assert builder._config.ai_config.text_hash_threshold == 2000
        assert builder._config.ai_config.hash_algorithm == "sha512"
        assert builder._config.ai_config.max_text_length == 50000
    
    def test_with_ai_features_invalid_options_error(self):
        """
        Test with_ai_features method with invalid options per docstring.
        
        Verifies:
            Unknown AI configuration options raise ValidationError as documented
            
        Business Impact:
            Prevents configuration with invalid AI feature settings
            
        Scenario:
            Given: CacheConfigBuilder instance
            When: with_ai_features is called with unknown options
            Then: ValidationError is raised with unknown options details
        """
        builder = CacheConfigBuilder()
        
        with pytest.raises(ValidationError) as exc_info:
            builder.with_ai_features(unknown_option="value", invalid_setting=123)
        
        assert "Unknown AI configuration options:" in str(exc_info.value)
        assert "unknown_option" in str(exc_info.value)
        assert "invalid_setting" in str(exc_info.value)
    
    def test_from_file_success(self):
        """
        Test from_file method with valid JSON file per docstring.
        
        Verifies:
            Configuration is loaded successfully from JSON file as documented
            
        Business Impact:
            Enables file-based configuration for complex deployment scenarios
            
        Scenario:
            Given: Valid JSON configuration file exists
            When: from_file is called with file path
            Then: Configuration is loaded from file and applied to builder
        """
        config_data = {
            "redis_url": "redis://file-config:6379",
            "default_ttl": 1200,
            "compression_level": 5,
            "ai_config": {
                "text_hash_threshold": 1500,
                "hash_algorithm": "sha256"
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            json.dump(config_data, temp_file)
            temp_file_path = temp_file.name
        
        try:
            builder = CacheConfigBuilder()
            result = builder.from_file(temp_file_path)
            
            assert result is builder  # Fluent interface
            assert builder._config.redis_url == "redis://file-config:6379"
            assert builder._config.default_ttl == 1200
            assert builder._config.compression_level == 5
            assert builder._config.ai_config is not None
            assert builder._config.ai_config.text_hash_threshold == 1500
        finally:
            Path(temp_file_path).unlink()
    
    def test_from_file_not_found_error(self):
        """
        Test from_file method with missing file per docstring error handling.
        
        Verifies:
            Missing configuration file raises ConfigurationError as documented
            
        Business Impact:
            Prevents system startup with missing configuration files
            
        Scenario:
            Given: Configuration file does not exist
            When: from_file is called with non-existent file path
            Then: ConfigurationError is raised with file path details
        """
        builder = CacheConfigBuilder()
        
        with pytest.raises(ConfigurationError) as exc_info:
            builder.from_file("/path/to/nonexistent/file.json")
        
        assert "Configuration file not found:" in str(exc_info.value)
    
    def test_from_file_invalid_json_error(self):
        """
        Test from_file method with invalid JSON per docstring error handling.
        
        Verifies:
            Invalid JSON in configuration file raises ConfigurationError as documented
            
        Business Impact:
            Prevents system startup with malformed configuration files
            
        Scenario:
            Given: Configuration file contains invalid JSON
            When: from_file is called with malformed file
            Then: ConfigurationError is raised with JSON parsing error details
        """
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            temp_file.write("invalid json content")
            temp_file_path = temp_file.name
        
        try:
            builder = CacheConfigBuilder()
            
            with pytest.raises(ConfigurationError) as exc_info:
                builder.from_file(temp_file_path)
            
            assert "Invalid JSON in configuration file:" in str(exc_info.value)
        finally:
            Path(temp_file_path).unlink()
    
    @patch.dict(os.environ, {
        "CACHE_REDIS_URL": "redis://env:6379",
        "CACHE_DEFAULT_TTL": "2400"
    }, clear=False)
    def test_from_environment_success(self):
        """
        Test from_environment method per docstring contract.
        
        Verifies:
            Environment variables are loaded successfully as documented
            
        Business Impact:
            Enables environment-based configuration for deployment flexibility
            
        Scenario:
            Given: Valid cache configuration environment variables are set
            When: from_environment is called
            Then: Configuration values are loaded from environment
        """
        builder = CacheConfigBuilder()
        result = builder.from_environment()
        
        assert result is builder  # Fluent interface
        assert builder._config.redis_url == "redis://env:6379"
        assert builder._config.default_ttl == 2400
    
    def test_validate_delegates_to_config(self):
        """
        Test validate method delegates to configuration per docstring.
        
        Verifies:
            Builder validation delegates to underlying configuration as documented
            
        Business Impact:
            Ensures consistent validation behavior across configuration and builder
            
        Scenario:
            Given: CacheConfigBuilder with invalid configuration
            When: validate is called
            Then: ValidationResult reflects configuration validation
        """
        builder = CacheConfigBuilder()
        builder._config.default_ttl = -100  # Invalid
        
        result = builder.validate()
        
        assert result.is_valid is False
        assert any("default_ttl must be positive" in error for error in result.errors)
    
    def test_build_success_with_valid_config(self):
        """
        Test build method success with valid configuration per docstring.
        
        Verifies:
            Valid configuration builds successfully and returns CacheConfig as documented
            
        Business Impact:
            Enables successful configuration construction for system operation
            
        Scenario:
            Given: CacheConfigBuilder with valid configuration
            When: build is called
            Then: CacheConfig instance is returned
        """
        builder = CacheConfigBuilder()
        builder.for_environment("development")
        
        config = builder.build()
        
        assert isinstance(config, CacheConfig)
        assert config.environment == "development"
    
    def test_build_validation_failure_error(self):
        """
        Test build method with validation failure per docstring error handling.
        
        Verifies:
            Invalid configuration raises ValidationError on build as documented
            
        Business Impact:
            Prevents system startup with invalid configuration
            
        Scenario:
            Given: CacheConfigBuilder with invalid configuration
            When: build is called
            Then: ValidationError is raised with validation details
        """
        builder = CacheConfigBuilder()
        builder._config.default_ttl = -100  # Invalid
        
        with pytest.raises(ValidationError) as exc_info:
            builder.build()
        
        assert "Configuration validation failed:" in str(exc_info.value)
        assert "default_ttl must be positive" in str(exc_info.value)
    
    def test_to_dict_delegates_to_config(self):
        """
        Test to_dict method delegates to configuration per docstring.
        
        Verifies:
            Builder to_dict delegates to underlying configuration as documented
            
        Business Impact:
            Ensures consistent serialization behavior across configuration and builder
            
        Scenario:
            Given: CacheConfigBuilder with configuration
            When: to_dict is called
            Then: Dictionary representation matches configuration to_dict
        """
        builder = CacheConfigBuilder()
        builder.for_environment("testing")
        
        builder_dict = builder.to_dict()
        config_dict = builder._config.to_dict()
        
        assert builder_dict == config_dict
        assert "environment" in builder_dict
        assert builder_dict["environment"] == "testing"
    
    def test_save_to_file_success(self):
        """
        Test save_to_file method success per docstring contract.
        
        Verifies:
            Configuration is saved successfully to JSON file as documented
            
        Business Impact:
            Enables configuration persistence for deployment and backup
            
        Scenario:
            Given: CacheConfigBuilder with configuration
            When: save_to_file is called with valid path
            Then: Configuration is written to JSON file
        """
        builder = CacheConfigBuilder()
        builder.for_environment("production").with_redis("redis://save-test:6379")
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as temp_file:
            temp_file_path = temp_file.name
        
        try:
            builder.save_to_file(temp_file_path)
            
            # Verify file was written correctly
            with open(temp_file_path, 'r') as f:
                saved_config = json.load(f)
            
            assert saved_config["environment"] == "production"
            assert saved_config["redis_url"] == "redis://save-test:6379"
        finally:
            Path(temp_file_path).unlink()
    
    def test_save_to_file_creates_directories(self):
        """
        Test save_to_file creates parent directories per docstring behavior.
        
        Verifies:
            Parent directories are created when create_dirs=True as documented
            
        Business Impact:
            Enables configuration saving to new directory structures
            
        Scenario:
            Given: CacheConfigBuilder with configuration and non-existent directory path
            When: save_to_file is called with create_dirs=True
            Then: Parent directories are created and file is saved
        """
        builder = CacheConfigBuilder()
        builder.for_environment("testing")
        
        with tempfile.TemporaryDirectory() as temp_dir:
            nested_path = Path(temp_dir) / "config" / "cache" / "test.json"
            
            builder.save_to_file(nested_path, create_dirs=True)
            
            assert nested_path.exists()
            assert nested_path.parent.exists()
    
    def test_method_chaining_fluent_interface(self):
        """
        Test method chaining fluent interface per docstring contract.
        
        Verifies:
            All builder methods return self for fluent interface as documented
            
        Business Impact:
            Enables readable configuration construction through method chaining
            
        Scenario:
            Given: CacheConfigBuilder instance
            When: Multiple configuration methods are chained
            Then: All methods return builder instance enabling fluent syntax
        """
        builder = CacheConfigBuilder()
        
        # Test complete fluent interface chain
        result = (builder
                 .for_environment("production")
                 .with_redis("redis://chain:6379", password="secret", use_tls=True)
                 .with_security(tls_cert_path="/cert.pem", tls_key_path="/key.pem")
                 .with_compression(threshold=1500, level=7)
                 .with_memory_cache(size=300)
                 .with_ai_features(text_hash_threshold=2500, max_text_length=75000))
        
        # Verify fluent interface returns builder
        assert result is builder
        
        # Verify all configurations were applied
        assert builder._config.environment == "production"
        assert builder._config.redis_url == "redis://chain:6379"
        assert builder._config.redis_password == "secret"
        assert builder._config.use_tls is True
        assert builder._config.tls_cert_path == "/cert.pem"
        assert builder._config.compression_threshold == 1500
        assert builder._config.memory_cache_size == 300
        assert builder._config.ai_config.text_hash_threshold == 2500


class TestEnvironmentPresets:
    """Test environment presets integration per docstring contracts."""
    
    @patch('app.infrastructure.cache.cache_presets.cache_preset_manager')
    def test_disabled_preset(self, mock_preset_manager):
        """
        Test disabled preset per docstring contract.
        
        Verifies:
            disabled() returns configuration for completely disabled cache as documented
            
        Business Impact:
            Enables cache-disabled deployments for minimal resource environments
            
        Scenario:
            Given: disabled() method is called
            When: Cache preset system provides disabled preset
            Then: Configuration for disabled cache is returned
        """
        mock_preset = MagicMock()
        mock_config = CacheConfig(redis_url=None, memory_cache_size=0)
        mock_preset.to_cache_config.return_value = mock_config
        mock_preset_manager.get_preset.return_value = mock_preset
        
        result = EnvironmentPresets.disabled()
        
        mock_preset_manager.get_preset.assert_called_once_with("disabled")
        mock_preset.to_cache_config.assert_called_once()
        assert result is mock_config
    
    @patch('app.infrastructure.cache.cache_presets.cache_preset_manager')
    def test_minimal_preset(self, mock_preset_manager):
        """
        Test minimal preset per docstring contract.
        
        Verifies:
            minimal() returns ultra-lightweight configuration as documented
            
        Business Impact:
            Enables minimal caching for resource-constrained environments
            
        Scenario:
            Given: minimal() method is called
            When: Cache preset system provides minimal preset
            Then: Ultra-lightweight cache configuration is returned
        """
        mock_preset = MagicMock()
        mock_config = CacheConfig(memory_cache_size=10, default_ttl=300)
        mock_preset.to_cache_config.return_value = mock_config
        mock_preset_manager.get_preset.return_value = mock_preset
        
        result = EnvironmentPresets.minimal()
        
        mock_preset_manager.get_preset.assert_called_once_with("minimal")
        assert result is mock_config
    
    @patch('app.infrastructure.cache.cache_presets.cache_preset_manager')
    def test_simple_preset(self, mock_preset_manager):
        """
        Test simple preset per docstring contract.
        
        Verifies:
            simple() returns balanced configuration for most use cases as documented
            
        Business Impact:
            Enables standard caching suitable for typical applications
            
        Scenario:
            Given: simple() method is called
            When: Cache preset system provides simple preset
            Then: Balanced cache configuration is returned
        """
        mock_preset = MagicMock()
        mock_config = CacheConfig(memory_cache_size=100, default_ttl=3600)
        mock_preset.to_cache_config.return_value = mock_config
        mock_preset_manager.get_preset.return_value = mock_preset
        
        result = EnvironmentPresets.simple()
        
        mock_preset_manager.get_preset.assert_called_once_with("simple")
        assert result is mock_config
    
    @patch('app.infrastructure.cache.cache_presets.cache_preset_manager')
    def test_development_preset(self, mock_preset_manager):
        """
        Test development preset per docstring contract.
        
        Verifies:
            development() returns configuration optimized for development as documented
            
        Business Impact:
            Enables development-friendly caching with balanced performance and debugging
            
        Scenario:
            Given: development() method is called
            When: Cache preset system provides development preset
            Then: Development-optimized cache configuration is returned
        """
        mock_preset = MagicMock()
        mock_config = CacheConfig(environment="development", default_ttl=1800)
        mock_preset.to_cache_config.return_value = mock_config
        mock_preset_manager.get_preset.return_value = mock_preset
        
        result = EnvironmentPresets.development()
        
        mock_preset_manager.get_preset.assert_called_once_with("development")
        assert result is mock_config
    
    @patch('app.infrastructure.cache.cache_presets.cache_preset_manager')
    def test_testing_preset_uses_development(self, mock_preset_manager):
        """
        Test testing preset uses development base per docstring note.
        
        Verifies:
            testing() uses development preset as base for fast feedback as documented
            
        Business Impact:
            Enables test-friendly caching with minimal TTLs and fast expiration
            
        Scenario:
            Given: testing() method is called
            When: Cache preset system provides development preset (per docstring note)
            Then: Development-based configuration optimized for testing is returned
        """
        mock_preset = MagicMock()
        mock_config = CacheConfig(environment="development", default_ttl=60)
        mock_preset.to_cache_config.return_value = mock_config
        mock_preset_manager.get_preset.return_value = mock_preset
        
        result = EnvironmentPresets.testing()
        
        # Per docstring: Uses 'development' preset as base for fast feedback
        mock_preset_manager.get_preset.assert_called_once_with("development")
        assert result is mock_config
    
    @patch('app.infrastructure.cache.cache_presets.cache_preset_manager')
    def test_production_preset(self, mock_preset_manager):
        """
        Test production preset per docstring contract.
        
        Verifies:
            production() returns configuration optimized for production as documented
            
        Business Impact:
            Enables production-grade caching with optimized performance and security
            
        Scenario:
            Given: production() method is called
            When: Cache preset system provides production preset
            Then: Production-optimized cache configuration is returned
        """
        mock_preset = MagicMock()
        mock_config = CacheConfig(environment="production", default_ttl=7200, use_tls=True)
        mock_preset.to_cache_config.return_value = mock_config
        mock_preset_manager.get_preset.return_value = mock_preset
        
        result = EnvironmentPresets.production()
        
        mock_preset_manager.get_preset.assert_called_once_with("production")
        assert result is mock_config
    
    @patch('app.infrastructure.cache.cache_presets.cache_preset_manager')
    def test_ai_development_preset(self, mock_preset_manager):
        """
        Test AI development preset per docstring contract.
        
        Verifies:
            ai_development() returns AI-optimized development configuration as documented
            
        Business Impact:
            Enables AI cache features in development with appropriate settings
            
        Scenario:
            Given: ai_development() method is called
            When: Cache preset system provides ai-development preset
            Then: AI development-optimized cache configuration is returned
        """
        mock_preset = MagicMock()
        ai_config = AICacheConfig(text_hash_threshold=1000)
        mock_config = CacheConfig(ai_config=ai_config, enable_ai_cache=True)
        mock_preset.to_cache_config.return_value = mock_config
        mock_preset_manager.get_preset.return_value = mock_preset
        
        result = EnvironmentPresets.ai_development()
        
        mock_preset_manager.get_preset.assert_called_once_with("ai-development")
        assert result is mock_config
    
    @patch('app.infrastructure.cache.cache_presets.cache_preset_manager')
    def test_ai_production_preset(self, mock_preset_manager):
        """
        Test AI production preset per docstring contract.
        
        Verifies:
            ai_production() returns AI-optimized production configuration as documented
            
        Business Impact:
            Enables AI cache features in production with optimized settings
            
        Scenario:
            Given: ai_production() method is called
            When: Cache preset system provides ai-production preset
            Then: AI production-optimized cache configuration is returned
        """
        mock_preset = MagicMock()
        ai_config = AICacheConfig(text_hash_threshold=2000, enable_smart_promotion=True)
        mock_config = CacheConfig(ai_config=ai_config, enable_ai_cache=True, use_tls=True)
        mock_preset.to_cache_config.return_value = mock_config
        mock_preset_manager.get_preset.return_value = mock_preset
        
        result = EnvironmentPresets.ai_production()
        
        mock_preset_manager.get_preset.assert_called_once_with("ai-production")
        assert result is mock_config
    
    @patch('app.infrastructure.cache.cache_presets.cache_preset_manager')
    def test_get_preset_names(self, mock_preset_manager):
        """
        Test get_preset_names method per docstring contract.
        
        Verifies:
            get_preset_names() returns list of available preset names as documented
            
        Business Impact:
            Enables discovery of available cache presets for configuration
            
        Scenario:
            Given: get_preset_names() method is called
            When: Cache preset system provides preset list
            Then: List of preset names is returned
        """
        expected_presets = ["disabled", "minimal", "simple", "development", "production"]
        mock_preset_manager.list_presets.return_value = expected_presets
        
        result = EnvironmentPresets.get_preset_names()
        
        mock_preset_manager.list_presets.assert_called_once()
        assert result == expected_presets
    
    @patch('app.infrastructure.cache.cache_presets.cache_preset_manager')
    def test_get_preset_details(self, mock_preset_manager):
        """
        Test get_preset_details method per docstring contract.
        
        Verifies:
            get_preset_details() returns detailed preset information as documented
            
        Business Impact:
            Enables detailed inspection of preset configurations for decision making
            
        Scenario:
            Given: get_preset_details() method is called with preset name
            When: Cache preset system provides preset details
            Then: Dictionary with preset configuration details is returned
        """
        expected_details = {
            "name": "production",
            "description": "Production-optimized configuration",
            "settings": {"default_ttl": 7200, "memory_cache_size": 200}
        }
        mock_preset_manager.get_preset_details.return_value = expected_details
        
        result = EnvironmentPresets.get_preset_details("production")
        
        mock_preset_manager.get_preset_details.assert_called_once_with("production")
        assert result == expected_details
    
    @patch('app.infrastructure.cache.cache_presets.cache_preset_manager')
    def test_recommend_preset_with_environment(self, mock_preset_manager):
        """
        Test recommend_preset method with explicit environment per docstring.
        
        Verifies:
            recommend_preset() returns appropriate preset for given environment as documented
            
        Business Impact:
            Enables intelligent preset selection based on deployment environment
            
        Scenario:
            Given: recommend_preset() method is called with environment name
            When: Cache preset system provides recommendation
            Then: Recommended preset name is returned
        """
        mock_preset_manager.recommend_preset.return_value = "production"
        
        result = EnvironmentPresets.recommend_preset("production")
        
        mock_preset_manager.recommend_preset.assert_called_once_with("production")
        assert result == "production"
    
    @patch('app.infrastructure.cache.cache_presets.cache_preset_manager')
    def test_recommend_preset_auto_detect(self, mock_preset_manager):
        """
        Test recommend_preset method with auto-detection per docstring.
        
        Verifies:
            recommend_preset() auto-detects environment when None provided as documented
            
        Business Impact:
            Enables automatic preset selection based on current environment
            
        Scenario:
            Given: recommend_preset() method is called with None environment
            When: Cache preset system auto-detects and provides recommendation
            Then: Recommended preset name based on auto-detection is returned
        """
        mock_preset_manager.recommend_preset.return_value = "development"
        
        result = EnvironmentPresets.recommend_preset(None)
        
        mock_preset_manager.recommend_preset.assert_called_once_with(None)
        assert result == "development"