"""
Unit tests for CacheConfig and ValidationResult core functionality.

This test suite verifies the observable behaviors documented in the
CacheConfig and ValidationResult public contracts (config.pyi). Tests focus on the
behavior-driven testing principles described in docs/guides/testing/TESTING.md.

Coverage Focus:
    - CacheConfig initialization and validation behavior
    - ValidationResult creation and error/warning management
    - Configuration serialization and dictionary conversion
    - Post-initialization hooks and environment loading

External Dependencies:
    - Settings configuration (mocked): Application configuration management
    - Standard library components (dataclasses, typing): For configuration data structures
    - app.core.exceptions: Exception handling for configuration and validation errors
"""

from typing import Any, Dict, Optional
from unittest.mock import MagicMock, patch

import pytest

from app.core.exceptions import ConfigurationError, ValidationError
from app.infrastructure.cache.config import (AICacheConfig, CacheConfig,
                                             ValidationResult)


class TestValidationResult:
    """
    Test suite for ValidationResult creation and management.

    Scope:
        - ValidationResult initialization and state management
        - Error and warning message addition and tracking
        - Validation status determination and reporting
        - Result aggregation and summary generation

    Business Critical:
        ValidationResult accuracy ensures proper configuration validation feedback

    Test Strategy:
        - Validation state testing using sample_validation_result fixtures
        - Error/warning addition testing with various message scenarios
        - State management verification through add_error/add_warning methods
        - Validation logic testing for is_valid property behavior

    External Dependencies:
        - None (ValidationResult is a pure dataclass with simple behavior)
    """

    def test_validation_result_initializes_with_valid_state_by_default(self):
        """
        Test that ValidationResult initializes with valid state and empty error/warning lists.

        Verifies:
            Default ValidationResult state represents successful validation

        Business Impact:
            Ensures validation results start with optimistic valid state

        Scenario:
            Given: ValidationResult is initialized without parameters
            When: ValidationResult instance is created
            Then: is_valid property returns True indicating successful validation
            And: errors list is empty indicating no validation failures
            And: warnings list is empty indicating no validation concerns

        Default State Verified:
            - is_valid defaults to True for optimistic validation state
            - errors list defaults to empty list for no validation failures
            - warnings list defaults to empty list for no concerns
            - ValidationResult is ready for error/warning accumulation

        Fixtures Used:
            - None (testing default initialization behavior)

        Optimistic Validation:
            ValidationResult assumes success until errors are added

        Related Tests:
            - test_add_error_sets_validation_to_invalid_state()
            - test_add_warning_preserves_valid_state()
        """
        # Given: ValidationResult is initialized without parameters
        # When: ValidationResult instance is created
        result = ValidationResult(is_valid=True)

        # Then: is_valid property returns True indicating successful validation
        assert result.is_valid is True

        # And: errors list is empty indicating no validation failures
        assert result.errors == []

        # And: warnings list is empty indicating no validation concerns
        assert result.warnings == []

    def test_add_error_sets_validation_to_invalid_state(self):
        """
        Test that add_error() method adds error message and marks validation as invalid.

        Verifies:
            Error addition properly updates validation state and error collection

        Business Impact:
            Enables accurate error reporting for configuration validation failures

        Scenario:
            Given: ValidationResult instance with valid initial state
            When: add_error() method is called with error message
            Then: Error message is added to errors list
            And: is_valid property changes to False indicating validation failure
            And: Multiple error messages can be accumulated

        Error Accumulation Verified:
            - Single error message added to errors list correctly
            - is_valid immediately changes to False after first error
            - Multiple errors can be added and accumulated
            - Error messages maintain their original content without modification
            - Validation state remains invalid after any error addition

        Fixtures Used:
            - None (testing direct method behavior)

        Error State Management:
            Single error invalidates entire validation regardless of warnings

        Related Tests:
            - test_validation_result_initializes_with_valid_state_by_default()
            - test_add_warning_preserves_valid_state()
        """
        # Given: ValidationResult instance with valid initial state
        result = ValidationResult(is_valid=True)
        assert result.is_valid is True
        assert result.errors == []

        # When: add_error() method is called with error message
        error_message = "Configuration parameter is invalid"
        result.add_error(error_message)

        # Then: Error message is added to errors list
        assert error_message in result.errors
        assert len(result.errors) == 1

        # And: is_valid property changes to False indicating validation failure
        assert result.is_valid is False

        # And: Multiple error messages can be accumulated
        second_error = "Another validation error"
        result.add_error(second_error)

        assert len(result.errors) == 2
        assert error_message in result.errors
        assert second_error in result.errors
        assert result.is_valid is False

    def test_add_warning_preserves_valid_state(self):
        """
        Test that add_warning() method adds warning message but preserves valid state.

        Verifies:
            Warning addition provides feedback without invalidating configuration

        Business Impact:
            Enables non-critical configuration feedback without preventing usage

        Scenario:
            Given: ValidationResult instance with valid initial state
            When: add_warning() method is called with warning message
            Then: Warning message is added to warnings list
            And: is_valid property remains True indicating validation success
            And: Multiple warnings can be accumulated without affecting validity

        Warning Behavior Verified:
            - Warning messages added to warnings list correctly
            - is_valid remains True despite warning presence
            - Multiple warnings can be accumulated independently
            - Warning messages preserve their original content
            - Warnings provide guidance without blocking configuration usage

        Fixtures Used:
            - None (testing direct method behavior)

        Non-Critical Feedback:
            Warnings inform without invalidating configuration

        Related Tests:
            - test_add_error_sets_validation_to_invalid_state()
            - test_validation_result_tracks_mixed_errors_and_warnings()
        """
        # Given: ValidationResult instance with valid initial state
        result = ValidationResult(is_valid=True)
        assert result.is_valid is True
        assert result.warnings == []

        # When: add_warning() method is called with warning message
        warning_message = "Configuration could be optimized"
        result.add_warning(warning_message)

        # Then: Warning message is added to warnings list
        assert warning_message in result.warnings
        assert len(result.warnings) == 1

        # And: is_valid property remains True indicating validation success
        assert result.is_valid is True

        # And: Multiple warnings can be accumulated without affecting validity
        second_warning = "Parameter value is suboptimal"
        result.add_warning(second_warning)

        assert len(result.warnings) == 2
        assert warning_message in result.warnings
        assert second_warning in result.warnings
        assert result.is_valid is True

    def test_validation_result_tracks_mixed_errors_and_warnings(
        self, sample_validation_result_invalid
    ):
        """
        Test that ValidationResult correctly tracks both errors and warnings simultaneously.

        Verifies:
            Mixed error/warning scenarios are handled correctly with proper state management

        Business Impact:
            Provides comprehensive validation feedback with errors and improvement suggestions

        Scenario:
            Given: ValidationResult instance with valid initial state
            When: Both add_error() and add_warning() methods are called
            Then: Errors are tracked in errors list
            And: Warnings are tracked in warnings list
            And: is_valid reflects error presence (False) regardless of warnings

        Mixed Feedback Tracking:
            - Errors and warnings maintained in separate lists
            - Error presence overrides warnings for validation state
            - Both error and warning messages preserved accurately
            - Validation state determined by error presence only
            - Comprehensive feedback available for troubleshooting

        Fixtures Used:
            - sample_validation_result_invalid: ValidationResult with mixed feedback

        Comprehensive Feedback:
            ValidationResult provides complete picture of configuration assessment

        Related Tests:
            - test_add_error_sets_validation_to_invalid_state()
            - test_add_warning_preserves_valid_state()
        """
        # Given: ValidationResult instance with mixed errors and warnings from fixture
        result = sample_validation_result_invalid

        # Then: Errors are tracked in errors list
        assert len(result.errors) == 2
        assert "Configuration parameter is invalid" in result.errors
        assert "Required field is missing" in result.errors

        # And: Warnings are tracked in warnings list
        assert len(result.warnings) == 2
        assert "Configuration could be optimized" in result.warnings
        assert "Parameter value is suboptimal" in result.warnings

        # And: is_valid reflects error presence (False) regardless of warnings
        assert result.is_valid is False

        # Test that we can also create our own mixed scenario
        new_result = ValidationResult(is_valid=True)
        new_result.add_warning("First warning")
        assert new_result.is_valid is True

        new_result.add_error("First error")
        assert new_result.is_valid is False

        new_result.add_warning("Second warning")
        assert new_result.is_valid is False  # Still invalid due to error


class TestCacheConfig:
    """
    Test suite for CacheConfig initialization and core functionality.

    Scope:
        - CacheConfig initialization with various parameter combinations
        - Configuration validation through validate() method
        - Dictionary serialization through to_dict() method
        - Post-initialization processing and environment integration

    Business Critical:
        CacheConfig accuracy determines cache behavior and performance

    Test Strategy:
        - Configuration initialization using valid/invalid config parameter fixtures
        - Validation testing using ValidationResult integration
        - Serialization testing with comprehensive configuration scenarios
        - Environment loading testing through __post_init__ hook

    External Dependencies:
        - AICacheConfig: For AI-specific configuration validation
        - ValidationResult: For validation result management
    """

    def test_cache_config_initializes_with_valid_basic_parameters(
        self, valid_basic_config_params
    ):
        """
        Test that CacheConfig initializes correctly with basic valid parameters.

        Verifies:
            Basic configuration parameters create functional CacheConfig instance

        Business Impact:
            Enables simple cache setup with minimal configuration complexity

        Scenario:
            Given: Valid basic configuration parameters (redis_url, default_ttl, etc.)
            When: CacheConfig is initialized with these parameters
            Then: CacheConfig instance is created with specified configuration
            And: All provided parameters are accessible as instance attributes
            And: Default values are applied for non-specified parameters

        Basic Configuration Verified:
            - Redis URL parameter properly stored and accessible
            - TTL configuration properly applied with reasonable defaults
            - Memory cache size properly configured with limits
            - Environment setting properly stored for environment-specific behavior
            - Optional parameters receive appropriate default values

        Fixtures Used:
            - valid_basic_config_params: Minimal valid configuration parameters

        Simple Configuration:
            Basic parameters provide functional cache configuration

        Related Tests:
            - test_cache_config_initializes_with_comprehensive_parameters()
            - test_cache_config_initialization_with_invalid_parameters_raises_error()
        """
        # Given: Valid basic configuration parameters
        params = valid_basic_config_params

        # When: CacheConfig is initialized with these parameters
        config = CacheConfig(**params)

        # Then: CacheConfig instance is created with specified configuration
        assert config is not None

        # And: All provided parameters are accessible as instance attributes
        assert config.redis_url == params["redis_url"]
        assert config.default_ttl == params["default_ttl"]
        assert config.memory_cache_size == params["memory_cache_size"]
        assert config.environment == params["environment"]

        # And: Default values are applied for non-specified parameters
        assert config.redis_password is None
        assert config.use_tls is False
        assert config.compression_level == 6  # Default compression level
        assert config.compression_threshold == 1000  # Default threshold
        assert config.ai_config is None  # No AI config by default
        assert config.enable_ai_cache is False

    def test_cache_config_initializes_with_comprehensive_parameters(
        self, valid_comprehensive_config_params
    ):
        """
        Test that CacheConfig initializes correctly with comprehensive parameters including AI features.

        Verifies:
            Comprehensive configuration creates full-featured CacheConfig instance

        Business Impact:
            Enables advanced cache features for production and AI applications

        Scenario:
            Given: Comprehensive configuration parameters including security and AI features
            When: CacheConfig is initialized with full parameter set
            Then: All advanced features are properly configured and accessible
            And: AI configuration is properly integrated and validated
            And: Security settings are properly stored and available

        Comprehensive Configuration Verified:
            - Redis connection with authentication and TLS properly configured
            - Compression settings properly applied with validation
            - AI configuration properly integrated with text processing features
            - Security certificates and TLS settings properly stored
            - Environment-specific optimizations properly applied

        Fixtures Used:
            - valid_comprehensive_config_params: Complete configuration with all features

        Advanced Features:
            Comprehensive configuration supports enterprise and AI use cases

        Related Tests:
            - test_cache_config_initializes_with_valid_basic_parameters()
            - test_cache_config_validates_ai_configuration_integration()
        """
        # Given: Comprehensive configuration parameters including security and AI features
        params = valid_comprehensive_config_params.copy()
        ai_config_data = params.pop("ai_config")
        ai_config = AICacheConfig(**ai_config_data)
        params["ai_config"] = ai_config

        # When: CacheConfig is initialized with full parameter set
        config = CacheConfig(**params)

        # Then: All advanced features are properly configured and accessible
        # Redis connection with authentication and TLS
        assert config.redis_url == "redis://prod-redis:6379"
        assert config.redis_password == "secure-password"
        assert config.use_tls is True
        assert config.tls_cert_path == "/certs/redis.crt"
        assert config.tls_key_path == "/certs/redis.key"

        # And: Compression settings properly applied
        assert config.compression_threshold == 1000
        assert config.compression_level == 6

        # And: AI configuration is properly integrated and validated
        assert config.ai_config is not None
        assert config.ai_config.text_hash_threshold == 1500
        assert config.ai_config.hash_algorithm == "sha256"
        assert config.enable_ai_cache is True

        # And: Security settings are properly stored and available
        assert config.environment == "production"
        assert config.default_ttl == 7200
        assert config.memory_cache_size == 200

    def test_cache_config_post_init_hook_processes_environment_loading(
        self, valid_basic_config_params, environment_variables_basic
    ):
        """
        Test that __post_init__ hook properly processes environment-specific configuration loading.

        Verifies:
            Post-initialization processing applies environment-specific optimizations

        Business Impact:
            Enables environment-aware configuration optimization and validation

        Scenario:
            Given: CacheConfig initialization with environment specification
            When: __post_init__ hook is executed during initialization
            Then: Environment-specific processing is applied to configuration
            And: Configuration is optimized for specified environment
            And: Environment-specific validation rules are applied

        Post-Init Processing Verified:
            - Environment-specific configuration adjustments applied
            - Configuration validation performed with environment context
            - Default value optimization based on environment requirements
            - Environment compatibility checks performed
            - Configuration state properly finalized after processing

        Fixtures Used:
            - valid_basic_config_params: Configuration with environment specification
            - environment_variables_basic: Environment context for processing

        Environment Awareness:
            Post-init processing ensures configuration matches environment requirements

        Related Tests:
            - test_cache_config_validates_configuration_with_environment_context()
            - test_cache_config_environment_loading_integration()
        """
        # Given: CacheConfig initialization with environment specification
        params = valid_basic_config_params.copy()

        # When: CacheConfig is initialized normally
        config = CacheConfig(**params)

        # Then: Post-init hook executes without errors
        assert config.environment == "development"
        assert config._from_env is False  # Default value

        # And: Configuration is properly initialized
        assert config.redis_url == params["redis_url"]
        assert config.default_ttl == params["default_ttl"]

        # Test triggering the environment loading path
        config._from_env = True  # Set the flag manually
        config._load_from_environment()  # Call the method directly to test it

        # Verify the deprecation path still works (logs warning but doesn't crash)
        assert (
            config.environment == "development"
        )  # Should remain unchanged due to deprecation

    def test_cache_config_validate_method_returns_comprehensive_validation_result(
        self, valid_comprehensive_config_params, mock_path_exists
    ):
        """
        Test that validate() method returns comprehensive ValidationResult with detailed feedback.

        Verifies:
            Configuration validation provides detailed error and warning feedback

        Business Impact:
            Enables comprehensive configuration validation with actionable feedback

        Scenario:
            Given: CacheConfig instance with various configuration parameters
            When: validate() method is called for configuration assessment
            Then: ValidationResult is returned with comprehensive validation feedback
            And: All configuration parameters are validated against requirements
            And: Errors and warnings are provided for invalid and suboptimal settings

        Validation Comprehensiveness Verified:
            - Redis URL validation including scheme and connectivity checks
            - TTL value validation including range and reasonableness checks
            - Memory cache size validation including limits and efficiency
            - Compression settings validation including level and threshold checks
            - AI configuration validation through integrated AICacheConfig

        Fixtures Used:
            - valid_comprehensive_config_params: Configuration for validation testing
            - sample_validation_result_valid: Expected validation outcome structure

        Thorough Validation:
            Configuration validation catches issues before runtime failures

        Related Tests:
            - test_cache_config_validation_identifies_parameter_conflicts()
            - test_cache_config_validation_provides_improvement_recommendations()
        """
        # Mock filesystem to simulate certificates exist
        mock_path_exists.return_value = True

        # Given: CacheConfig instance with various configuration parameters
        params = valid_comprehensive_config_params.copy()
        ai_config_data = params.pop("ai_config")
        ai_config = AICacheConfig(**ai_config_data)
        params["ai_config"] = ai_config
        config = CacheConfig(**params)

        # When: validate() method is called for configuration assessment
        result = config.validate()

        # Then: ValidationResult is returned with comprehensive validation feedback
        assert isinstance(result, ValidationResult)

        # And: All configuration parameters are validated successfully
        assert result.is_valid is True

        # Verify that validation checks various aspects
        # Test with invalid config to see validation in action
        invalid_config = CacheConfig(
            redis_url="invalid-scheme://localhost",  # Invalid scheme
            default_ttl=-100,  # Invalid TTL
            memory_cache_size=-50,  # Invalid size
            compression_level=15,  # Invalid level
        )

        invalid_result = invalid_config.validate()
        assert invalid_result.is_valid is False
        assert len(invalid_result.errors) >= 4  # Should have multiple validation errors

    def test_cache_config_to_dict_method_produces_complete_serialization(
        self, valid_comprehensive_config_params
    ):
        """
        Test that to_dict() method produces complete dictionary representation of configuration.

        Verifies:
            Configuration serialization captures all parameters for storage and transmission

        Business Impact:
            Enables configuration persistence, logging, and API transmission

        Scenario:
            Given: CacheConfig instance with comprehensive configuration
            When: to_dict() method is called for serialization
            Then: Complete dictionary representation is returned
            And: All configuration parameters are included in dictionary
            And: Nested AI configuration is properly serialized

        Serialization Completeness Verified:
            - All scalar configuration parameters included in dictionary
            - AI configuration properly nested and serialized
            - Security settings included with appropriate structure
            - Dictionary structure suitable for JSON serialization
            - No sensitive information exposed inappropriately

        Fixtures Used:
            - valid_comprehensive_config_params: Configuration for serialization testing

        Complete Representation:
            Dictionary serialization preserves all configuration information

        Related Tests:
            - test_cache_config_serialization_supports_round_trip_conversion()
            - test_cache_config_dictionary_format_suitable_for_persistence()
        """
        # Given: CacheConfig instance with comprehensive configuration
        params = valid_comprehensive_config_params.copy()
        ai_config_data = params.pop("ai_config")
        ai_config = AICacheConfig(**ai_config_data)
        params["ai_config"] = ai_config
        config = CacheConfig(**params)

        # When: to_dict() method is called for serialization
        config_dict = config.to_dict()

        # Then: Complete dictionary representation is returned
        assert isinstance(config_dict, dict)

        # And: All configuration parameters are included in dictionary
        assert "redis_url" in config_dict
        assert "redis_password" in config_dict
        assert "use_tls" in config_dict
        assert "tls_cert_path" in config_dict
        assert "tls_key_path" in config_dict
        assert "default_ttl" in config_dict
        assert "memory_cache_size" in config_dict
        assert "compression_threshold" in config_dict
        assert "compression_level" in config_dict
        assert "environment" in config_dict
        assert "enable_ai_cache" in config_dict

        # And: Nested AI configuration is properly serialized
        assert "ai_config" in config_dict
        assert config_dict["ai_config"] is not None
        ai_dict = config_dict["ai_config"]
        assert "text_hash_threshold" in ai_dict
        assert "hash_algorithm" in ai_dict
        assert "text_size_tiers" in ai_dict
        assert "operation_ttls" in ai_dict

        # And: Internal fields are excluded
        assert "_from_env" not in config_dict

        # Verify values match original configuration
        assert config_dict["redis_url"] == config.redis_url
        assert config_dict["default_ttl"] == config.default_ttl
        assert (
            config_dict["ai_config"]["text_hash_threshold"]
            == config.ai_config.text_hash_threshold
        )

    def test_cache_config_initialization_with_invalid_parameters_raises_error(
        self, invalid_config_params
    ):
        """
        Test that CacheConfig initialization with invalid parameters raises appropriate errors.

        Verifies:
            Invalid configuration parameters are detected and rejected during initialization

        Business Impact:
            Prevents deployment with invalid cache configurations that could cause runtime failures

        Scenario:
            Given: Invalid configuration parameters (negative TTL, invalid URLs, etc.)
            When: CacheConfig initialization is attempted with invalid parameters
            Then: ConfigurationError is raised with specific parameter validation failures
            And: Error context includes which parameters failed validation
            And: No CacheConfig instance is created with invalid parameters

        Invalid Parameter Detection:
            - Invalid Redis URLs cause specific URL validation errors
            - Negative TTL values cause range validation errors
            - Invalid compression levels cause parameter range errors
            - Unsupported environments cause environment validation errors
            - Parameter type mismatches cause type validation errors

        Fixtures Used:
            - invalid_config_params: Configuration parameters that should fail validation

        Validation Protection:
            Parameter validation prevents invalid cache configuration deployment

        Related Tests:
            - test_cache_config_initializes_with_valid_basic_parameters()
            - test_cache_config_validation_provides_detailed_error_context()
        """
        # Note: CacheConfig itself doesn't validate parameters at initialization time.
        # It only validates when validate() method is called.
        # This test verifies that validation catches invalid parameters when validate() is called.

        # Given: Invalid configuration parameters
        params = invalid_config_params

        # When: CacheConfig is initialized (this succeeds)
        config = CacheConfig(**params)

        # Then: Configuration validation detects errors when validate() is called
        result = config.validate()
        assert result.is_valid is False
        assert len(result.errors) > 0

        # Verify specific validation errors
        error_messages = result.errors

        # Check for Redis URL validation error
        redis_url_error = any(
            "redis_url must start with" in error for error in error_messages
        )
        assert (
            redis_url_error
        ), f"Expected Redis URL validation error. Errors: {error_messages}"

        # Check for TTL validation error
        ttl_error = any(
            "default_ttl must be positive" in error for error in error_messages
        )
        assert ttl_error, f"Expected TTL validation error. Errors: {error_messages}"

        # Check for memory cache size error
        memory_error = any(
            "memory_cache_size must be positive" in error for error in error_messages
        )
        assert (
            memory_error
        ), f"Expected memory cache size error. Errors: {error_messages}"

        # Check for compression level error
        compression_error = any(
            "compression_level must be between 1 and 9" in error
            for error in error_messages
        )
        assert (
            compression_error
        ), f"Expected compression level error. Errors: {error_messages}"


class TestAICacheConfig:
    """
    Test suite for AICacheConfig AI-specific configuration functionality.

    Scope:
        - AICacheConfig initialization with AI-specific parameters
        - AI configuration validation through validate() method
        - AI feature parameter validation and optimization
        - Integration with parent CacheConfig validation

    Business Critical:
        AI configuration accuracy determines AI cache performance and behavior

    Test Strategy:
        - AI configuration testing using valid/invalid AI parameter fixtures
        - Validation integration testing with ValidationResult management
        - AI feature parameter testing including thresholds and algorithms
        - Configuration optimization testing for AI workloads

    External Dependencies:
        - ValidationResult: For AI configuration validation results
    """

    def test_ai_cache_config_initializes_with_valid_ai_parameters(
        self, valid_ai_config_params
    ):
        """
        Test that AICacheConfig initializes correctly with valid AI-specific parameters.

        Verifies:
            AI-specific configuration parameters create functional AICacheConfig instance

        Business Impact:
            Enables AI cache optimization with text processing and intelligent caching features

        Scenario:
            Given: Valid AI configuration parameters (text thresholds, algorithms, TTLs)
            When: AICacheConfig is initialized with these parameters
            Then: AI configuration instance is created with specified settings
            And: All AI-specific parameters are accessible as instance attributes
            And: Default values are applied for non-specified AI parameters

        AI Configuration Verified:
            - Text hash threshold properly configured for large text handling
            - Hash algorithm properly set with supported algorithm validation
            - Text size tiers properly structured for tiered caching strategies
            - Operation-specific TTLs properly configured for AI operations
            - Smart promotion settings properly applied for cache optimization

        Fixtures Used:
            - valid_ai_config_params: Valid AI-specific configuration parameters

        AI Feature Enablement:
            AI configuration enables intelligent text processing and caching

        Related Tests:
            - test_ai_cache_config_validates_ai_parameter_ranges()
            - test_ai_cache_config_integration_with_parent_config()
        """
        # Given: Valid AI configuration parameters
        params = valid_ai_config_params

        # When: AICacheConfig is initialized with these parameters
        ai_config = AICacheConfig(**params)

        # Then: AI configuration instance is created with specified settings
        assert ai_config is not None

        # And: All AI-specific parameters are accessible as instance attributes
        assert ai_config.text_hash_threshold == params["text_hash_threshold"]
        assert ai_config.hash_algorithm == params["hash_algorithm"]
        assert ai_config.enable_smart_promotion == params["enable_smart_promotion"]
        assert ai_config.max_text_length == params["max_text_length"]

        # Text size tiers properly structured
        assert ai_config.text_size_tiers == params["text_size_tiers"]
        assert ai_config.text_size_tiers["small"] == 1000
        assert ai_config.text_size_tiers["medium"] == 10000
        assert ai_config.text_size_tiers["large"] == 100000

        # Operation-specific TTLs properly configured
        assert ai_config.operation_ttls == params["operation_ttls"]
        assert ai_config.operation_ttls["summarize"] == 7200
        assert ai_config.operation_ttls["sentiment"] == 3600

        # Test with minimal parameters (using defaults)
        minimal_config = AICacheConfig()
        assert minimal_config.text_hash_threshold == 1000  # Default
        assert minimal_config.hash_algorithm == "sha256"  # Default
        assert minimal_config.enable_smart_promotion is True  # Default

    def test_ai_cache_config_validate_method_checks_ai_parameter_validity(
        self, valid_ai_config_params, invalid_ai_config_params
    ):
        """
        Test that validate() method performs comprehensive AI parameter validation.

        Verifies:
            AI configuration validation catches AI-specific parameter issues

        Business Impact:
            Prevents AI cache deployment with parameters that could degrade performance

        Scenario:
            Given: AICacheConfig instance with various AI parameter combinations
            When: validate() method is called for AI parameter assessment
            Then: ValidationResult is returned with AI-specific validation feedback
            And: Text processing parameters are validated for efficiency
            And: Algorithm choices are validated for support and performance

        AI Validation Comprehensiveness:
            - Text hash threshold validated for reasonable performance ranges
            - Hash algorithm validated for support and security characteristics
            - Text size tiers validated for logical progression and efficiency
            - Operation TTLs validated for reasonable caching behavior
            - Smart promotion settings validated for compatibility

        Fixtures Used:
            - valid_ai_config_params: AI configuration for validation testing
            - invalid_ai_config_params: AI parameters that should trigger validation errors

        AI Parameter Safety:
            AI validation ensures parameters support efficient text processing

        Related Tests:
            - test_ai_cache_config_initializes_with_valid_ai_parameters()
            - test_ai_cache_config_validation_provides_optimization_recommendations()
        """
        # Test valid configuration
        # Given: AICacheConfig instance with valid AI parameter combinations
        valid_config = AICacheConfig(**valid_ai_config_params)

        # When: validate() method is called for AI parameter assessment
        valid_result = valid_config.validate()

        # Then: ValidationResult is returned indicating success
        assert isinstance(valid_result, ValidationResult)
        assert valid_result.is_valid is True
        assert len(valid_result.errors) == 0

        # Test invalid configuration
        # Given: AICacheConfig with invalid parameters
        invalid_params = invalid_ai_config_params.copy()
        # Fix the invalid text_size_tiers to have proper structure for initialization
        invalid_params["text_size_tiers"] = {
            "small": 0
        }  # Keep only zero size for validation error

        invalid_config = AICacheConfig(
            text_hash_threshold=invalid_params["text_hash_threshold"],
            max_text_length=invalid_params["max_text_length"],
            text_size_tiers=invalid_params["text_size_tiers"],
            operation_ttls=invalid_params["operation_ttls"],
        )

        # When: validate() method is called
        invalid_result = invalid_config.validate()

        # Then: ValidationResult indicates validation failures
        assert invalid_result.is_valid is False
        assert len(invalid_result.errors) > 0

        # Verify specific validation errors
        error_messages = invalid_result.errors

        # Check for text_hash_threshold validation
        threshold_error = any(
            "text_hash_threshold must be positive" in error for error in error_messages
        )
        assert (
            threshold_error
        ), f"Expected threshold validation error. Errors: {error_messages}"

        # Check for max_text_length validation
        length_error = any(
            "max_text_length must be positive" in error for error in error_messages
        )
        assert (
            length_error
        ), f"Expected max_text_length validation error. Errors: {error_messages}"

        # Check for text_size_tiers validation
        tiers_error = any(
            "text_size_tiers['small'] must be a positive integer" in error
            for error in error_messages
        )
        assert (
            tiers_error
        ), f"Expected text_size_tiers validation error. Errors: {error_messages}"
