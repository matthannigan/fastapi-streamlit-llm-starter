"""
Unit tests for ValidationResult behavior.

This test suite verifies the observable behaviors documented in the
ValidationResult dataclass public contract (cache_validator.pyi). Tests focus on the
behavior-driven testing principles described in docs/guides/testing/TESTING.md.

Coverage Focus:
    - Infrastructure service (>90% test coverage requirement)
    - Validation result container behavior
    - Message categorization and management
    - Validation status determination logic

External Dependencies:
    All external dependencies are mocked using fixtures from conftest.py following
    the documented public contracts to ensure accurate behavior simulation.
"""

import pytest
from unittest.mock import MagicMock
from dataclasses import dataclass, field
from typing import Dict, List, Optional, Any

from app.infrastructure.cache.cache_validator import ValidationResult, ValidationMessage, ValidationSeverity


class TestValidationResultInitialization:
    """
    Test suite for ValidationResult initialization and basic behavior.
    
    Scope:
        - ValidationResult dataclass initialization
        - Initial validation state management
        - Basic message container functionality
        - Validation metadata assignment
        
    Business Critical:
        ValidationResult provides structured validation feedback for cache configuration systems
        
    Test Strategy:
        - Unit tests for ValidationResult initialization with various parameters
        - Initial state verification and default value testing
        - Message container initialization and structure verification
        - Metadata assignment and tracking functionality
        
    External Dependencies:
        - ValidationMessage and ValidationSeverity (real): Message structure components
        - dataclasses module (real): Dataclass functionality
    """

    def test_validation_result_initializes_with_default_valid_state(self):
        """
        Test that ValidationResult initializes with default valid state.
        
        Verifies:
            Default initialization assumes valid configuration until proven otherwise
            
        Business Impact:
            Enables optimistic validation with explicit error collection
            
        Scenario:
            Given: ValidationResult initialization without specific parameters
            When: ValidationResult instance is created with defaults
            Then: is_valid is True by default (optimistic validation)
            And: messages list is empty initially
            And: validation_type is set appropriately
            And: schema_version is configured for validation context
            
        Default State Verification:
            - is_valid defaults to True for optimistic validation
            - messages list is initialized empty
            - validation_type can be specified or defaults appropriately
            - schema_version tracks validation framework version
            
        Fixtures Used:
            - None (testing default initialization directly)
            
        Optimistic Validation Verified:
            ValidationResult assumes validity until errors are explicitly added
            
        Related Tests:
            - test_validation_result_becomes_invalid_when_errors_added()
            - test_validation_result_maintains_validity_with_warnings_only()
        """
        # Given: ValidationResult initialization without specific parameters
        result = ValidationResult(is_valid=True)
        
        # When: ValidationResult instance is created with defaults
        # Then: Verify default state per docstring
        assert result.is_valid is True  # optimistic validation
        assert len(result.messages) == 0  # empty initially
        assert hasattr(result, 'validation_type')  # metadata present
        assert hasattr(result, 'schema_version')   # metadata present
        assert result.validation_type == "unknown"  # default validation type
        assert result.schema_version == "1.0"  # default schema version

    def test_validation_result_accepts_validation_metadata(self):
        """
        Test that ValidationResult accepts validation metadata for context tracking.
        
        Verifies:
            Validation metadata provides context for validation operations
            
        Business Impact:
            Enables validation result tracking and debugging with comprehensive context
            
        Scenario:
            Given: ValidationResult initialization with validation metadata
            When: ValidationResult is created with validation_type and schema_version
            Then: Metadata is properly stored and accessible
            And: validation_type describes the type of validation performed
            And: schema_version tracks the validation schema used
            And: Metadata supports validation result interpretation
            
        Metadata Management Verified:
            - validation_type describes validation context (preset, configuration, overrides)
            - schema_version tracks validation framework version
            - Metadata is preserved throughout validation result lifecycle
            - Context information supports debugging and result interpretation
            
        Fixtures Used:
            - None (testing metadata assignment directly)
            
        Context Tracking Verified:
            Validation metadata enables comprehensive validation result interpretation
            
        Related Tests:
            - test_validation_result_metadata_supports_result_interpretation()
            - test_validation_metadata_enables_debugging_context()
        """
        # Given: ValidationResult initialization with validation metadata
        validation_type = "preset"
        schema_version = "2.1"
        
        # When: ValidationResult is created with validation_type and schema_version
        result = ValidationResult(
            is_valid=True,
            validation_type=validation_type,
            schema_version=schema_version
        )
        
        # Then: Metadata is properly stored and accessible
        assert result.validation_type == validation_type  # describes validation context
        assert result.schema_version == schema_version    # tracks schema version
        assert result.is_valid is True  # initial state maintained
        assert len(result.messages) == 0  # messages initialized empty
        
        # And: Metadata supports validation result interpretation
        assert isinstance(result.validation_type, str)
        assert isinstance(result.schema_version, str)


class TestValidationResultMessageManagement:
    """
    Test suite for ValidationResult message management functionality.
    
    Scope:
        - Message addition and categorization (errors, warnings, info)
        - Message retrieval and filtering by severity
        - Validation state management based on message content
        - Message context and field path tracking
        
    Business Critical:
        Message management enables detailed validation feedback for configuration debugging
        
    Test Strategy:
        - Unit tests for add_error(), add_warning(), add_info() methods
        - Message categorization and retrieval testing
        - Validation state change testing based on message addition
        - Message context and field path verification
        
    External Dependencies:
        - ValidationMessage dataclass (real): Individual message structure
        - ValidationSeverity enum (real): Message severity categorization
    """

    def test_validation_result_add_error_marks_result_invalid(self):
        """
        Test that add_error() marks ValidationResult as invalid.
        
        Verifies:
            Adding error messages changes validation state to invalid
            
        Business Impact:
            Ensures validation failures are properly reflected in overall validation state
            
        Scenario:
            Given: ValidationResult with initially valid state
            When: add_error() is called with error message
            Then: is_valid becomes False
            And: Error message is added to messages list
            And: Error is categorized with ERROR severity
            And: Validation result reflects failure state
            
        Error State Management Verified:
            - Single error changes is_valid to False
            - Multiple errors maintain is_valid as False
            - Error messages are properly categorized
            - Validation state reflects presence of errors
            
        Fixtures Used:
            - None (testing error addition behavior directly)
            
        Validation Failure Detection Verified:
            Error addition properly indicates validation failure
            
        Related Tests:
            - test_validation_result_add_warning_maintains_valid_state()
            - test_validation_result_errors_property_returns_error_messages()
        """
        # Given: ValidationResult with initially valid state
        result = ValidationResult(is_valid=True)
        assert result.is_valid is True  # initially valid
        
        # When: add_error() is called with error message
        error_message = "Configuration validation failed"
        result.add_error(error_message)
        
        # Then: is_valid becomes False
        assert result.is_valid is False
        
        # And: Error message is added to messages list
        assert len(result.messages) == 1
        
        # And: Error is categorized with ERROR severity
        error_msg = result.messages[0]
        assert error_msg.severity == ValidationSeverity.ERROR
        assert error_msg.message == error_message
        
        # Verify multiple errors maintain invalid state
        result.add_error("Second error")
        assert result.is_valid is False
        assert len(result.messages) == 2

    def test_validation_result_add_warning_maintains_valid_state(self):
        """
        Test that add_warning() maintains valid state while adding warning messages.
        
        Verifies:
            Warning messages provide feedback without invalidating configuration
            
        Business Impact:
            Enables configuration improvement suggestions without blocking deployment
            
        Scenario:
            Given: ValidationResult with valid state
            When: add_warning() is called with warning message
            Then: is_valid remains True
            And: Warning message is added to messages list
            And: Warning is categorized with WARNING severity
            And: Validation result indicates warnings present but configuration valid
            
        Warning State Management Verified:
            - Warnings do not change is_valid to False
            - Warning messages are properly categorized
            - Valid configurations with warnings are deployment-ready
            - Multiple warnings maintain valid state
            
        Fixtures Used:
            - None (testing warning addition behavior directly)
            
        Configuration Improvement Feedback Verified:
            Warnings provide feedback without preventing valid configuration deployment
            
        Related Tests:
            - test_validation_result_warnings_property_returns_warning_messages()
            - test_validation_result_combines_errors_and_warnings_appropriately()
        """
        # Given: ValidationResult with valid state
        result = ValidationResult(is_valid=True)
        assert result.is_valid is True
        
        # When: add_warning() is called with warning message
        warning_message = "Configuration could be optimized"
        result.add_warning(warning_message)
        
        # Then: is_valid remains True
        assert result.is_valid is True  # warnings don't invalidate
        
        # And: Warning message is added to messages list
        assert len(result.messages) == 1
        
        # And: Warning is categorized with WARNING severity
        warning_msg = result.messages[0]
        assert warning_msg.severity == ValidationSeverity.WARNING
        assert warning_msg.message == warning_message
        
        # Verify multiple warnings maintain valid state
        result.add_warning("Another optimization suggestion")
        assert result.is_valid is True  # multiple warnings still valid
        assert len(result.messages) == 2

    def test_validation_result_add_info_provides_informational_feedback(self):
        """
        Test that add_info() provides informational feedback without affecting validation state.
        
        Verifies:
            Informational messages provide context without impacting validation outcomes
            
        Business Impact:
            Enables rich validation feedback including helpful information and recommendations
            
        Scenario:
            Given: ValidationResult in any validation state
            When: add_info() is called with informational message
            Then: is_valid state is unchanged
            And: Info message is added to messages list
            And: Info is categorized with INFO severity
            And: Informational content supplements validation results
            
        Informational Feedback Verified:
            - Info messages do not affect is_valid state
            - Informational messages are properly categorized
            - Info content provides helpful context
            - Multiple info messages accumulate properly
            
        Fixtures Used:
            - None (testing info addition behavior directly)
            
        Rich Validation Feedback Verified:
            Informational messages enhance validation results without affecting validation state
            
        Related Tests:
            - test_validation_result_info_property_returns_info_messages()
            - test_validation_result_message_categorization_works_correctly()
        """
        # Given: ValidationResult in valid state
        result = ValidationResult(is_valid=True)
        original_state = result.is_valid
        
        # When: add_info() is called with informational message
        info_message = "Configuration loaded successfully"
        result.add_info(info_message)
        
        # Then: is_valid state is unchanged
        assert result.is_valid == original_state  # state unchanged
        
        # And: Info message is added to messages list
        assert len(result.messages) == 1
        
        # And: Info is categorized with INFO severity
        info_msg = result.messages[0]
        assert info_msg.severity == ValidationSeverity.INFO
        assert info_msg.message == info_message
        
        # Test with invalid state to ensure info doesn't change it
        result.add_error("Test error")
        assert result.is_valid is False
        result.add_info("Additional context")
        assert result.is_valid is False  # info doesn't change invalid state
        assert len(result.messages) == 3  # all messages present

    def test_validation_result_message_methods_accept_field_path_and_context(self):
        """
        Test that message addition methods accept field_path and context parameters.
        
        Verifies:
            Message methods support detailed error context for debugging
            
        Business Impact:
            Enables precise identification of validation issues for rapid resolution
            
        Scenario:
            Given: ValidationResult ready for message addition
            When: Message methods are called with field_path and context parameters
            Then: Messages include field path information for error location
            And: Context dictionary provides additional debugging information
            And: Field paths enable precise error identification
            And: Context supports comprehensive error analysis
            
        Message Context Verified:
            - field_path parameter specifies exact field location of validation issue
            - context dictionary provides additional debugging information
            - Message context enables rapid issue identification and resolution
            - Context information is preserved in ValidationMessage instances
            
        Fixtures Used:
            - None (testing message context parameters directly)
            
        Error Location Precision Verified:
            Message context enables precise identification of configuration validation issues
            
        Related Tests:
            - test_validation_result_messages_preserve_context_information()
            - test_field_path_information_enables_precise_error_identification()
        """
        # Given: ValidationResult ready for message addition
        result = ValidationResult(is_valid=True)
        
        # Test context data
        field_path = "cache.redis.connection_timeout"
        context = {"expected_range": "1-300 seconds", "actual_value": 0, "preset": "production"}
        
        # When: Message methods are called with field_path and context parameters
        result.add_error("Invalid connection timeout", field_path=field_path, context=context)
        result.add_warning("Suboptimal configuration", field_path="cache.ttl", context={"suggestion": "increase TTL"})
        result.add_info("Configuration loaded", field_path="cache", context={"source": "preset"})
        
        # Then: Messages include field path information and context
        assert len(result.messages) == 3
        
        # Verify error message context
        error_msg = result.messages[0]
        assert error_msg.field_path == field_path
        assert error_msg.context == context
        assert error_msg.severity == ValidationSeverity.ERROR
        
        # Verify warning message context
        warning_msg = result.messages[1]
        assert warning_msg.field_path == "cache.ttl"
        assert warning_msg.context["suggestion"] == "increase TTL"
        assert warning_msg.severity == ValidationSeverity.WARNING
        
        # Verify info message context
        info_msg = result.messages[2]
        assert info_msg.field_path == "cache"
        assert info_msg.context["source"] == "preset"
        assert info_msg.severity == ValidationSeverity.INFO


class TestValidationResultMessageRetrieval:
    """
    Test suite for ValidationResult message retrieval and filtering functionality.
    
    Scope:
        - Message retrieval by severity category (errors, warnings, info)
        - Message filtering and categorization properties
        - Message content access and formatting
        - Comprehensive message list access
        
    Business Critical:
        Message retrieval enables targeted validation feedback processing
        
    Test Strategy:
        - Unit tests for errors, warnings, info property accessors
        - Message categorization accuracy verification
        - Message content preservation and formatting testing
        - Comprehensive message access functionality
        
    External Dependencies:
        - ValidationMessage instances (real): Message content and metadata
        - Message filtering logic (internal): Category-based message selection
    """

    def test_validation_result_errors_property_returns_error_messages_only(self):
        """
        Test that errors property returns only error messages.
        
        Verifies:
            Error message filtering provides focused error feedback
            
        Business Impact:
            Enables error-focused validation feedback for critical issue resolution
            
        Scenario:
            Given: ValidationResult with mixed message types (errors, warnings, info)
            When: errors property is accessed
            Then: Only error messages are returned
            And: Warning and info messages are excluded
            And: Error messages maintain their content and context
            And: Error list order is consistent with addition order
            
        Error Filtering Verified:
            - errors property returns only ERROR severity messages
            - Non-error messages are excluded from error list
            - Error message content and context are preserved
            - Error list maintains consistent ordering
            
        Fixtures Used:
            - None (testing message filtering directly)
            
        Error-Focused Feedback Verified:
            Error property provides focused feedback for critical validation issues
            
        Related Tests:
            - test_validation_result_warnings_property_returns_warning_messages_only()
            - test_validation_result_info_property_returns_info_messages_only()
        """
        # Given: ValidationResult with mixed message types
        result = ValidationResult(is_valid=True)
        
        # Add mixed message types
        result.add_error("First error")
        result.add_warning("First warning")
        result.add_error("Second error")
        result.add_info("First info")
        result.add_warning("Second warning")
        
        # When: errors property is accessed
        error_messages = result.errors
        
        # Then: Only error messages are returned
        assert len(error_messages) == 2
        assert "First error" in error_messages
        assert "Second error" in error_messages
        
        # And: Warning and info messages are excluded
        assert "First warning" not in error_messages
        assert "Second warning" not in error_messages
        assert "First info" not in error_messages
        
        # And: Error list order is consistent with addition order
        assert error_messages[0] == "First error"
        assert error_messages[1] == "Second error"
        
        # Verify return type is List[str]
        assert isinstance(error_messages, list)
        assert all(isinstance(msg, str) for msg in error_messages)

    def test_validation_result_warnings_property_returns_warning_messages_only(self):
        """
        Test that warnings property returns only warning messages.
        
        Verifies:
            Warning message filtering provides focused improvement suggestions
            
        Business Impact:
            Enables warning-focused feedback for configuration optimization
            
        Scenario:
            Given: ValidationResult with mixed message types
            When: warnings property is accessed
            Then: Only warning messages are returned
            And: Error and info messages are excluded
            And: Warning messages maintain their content and context
            And: Warning list supports configuration improvement workflows
            
        Warning Filtering Verified:
            - warnings property returns only WARNING severity messages
            - Non-warning messages are excluded from warning list
            - Warning message content and context are preserved
            - Warning list enables configuration improvement focus
            
        Fixtures Used:
            - None (testing warning filtering directly)
            
        Improvement-Focused Feedback Verified:
            Warning property provides focused feedback for configuration optimization
            
        Related Tests:
            - test_validation_result_errors_property_returns_error_messages_only()
            - test_validation_result_info_property_returns_info_messages_only()
        """
        # Given: ValidationResult with mixed message types
        result = ValidationResult(is_valid=True)
        
        # Add mixed message types
        result.add_warning("First warning")
        result.add_error("First error")
        result.add_warning("Second warning")
        result.add_info("First info")
        result.add_error("Second error")
        
        # When: warnings property is accessed
        warning_messages = result.warnings
        
        # Then: Only warning messages are returned
        assert len(warning_messages) == 2
        assert "First warning" in warning_messages
        assert "Second warning" in warning_messages
        
        # And: Error and info messages are excluded
        assert "First error" not in warning_messages
        assert "Second error" not in warning_messages
        assert "First info" not in warning_messages
        
        # And: Warning list order is consistent with addition order
        assert warning_messages[0] == "First warning"
        assert warning_messages[1] == "Second warning"
        
        # Verify return type is List[str]
        assert isinstance(warning_messages, list)
        assert all(isinstance(msg, str) for msg in warning_messages)

    def test_validation_result_info_property_returns_info_messages_only(self):
        """
        Test that info property returns only informational messages.
        
        Verifies:
            Info message filtering provides focused contextual information
            
        Business Impact:
            Enables access to helpful information without noise from errors/warnings
            
        Scenario:
            Given: ValidationResult with mixed message types
            When: info property is accessed
            Then: Only info messages are returned
            And: Error and warning messages are excluded
            And: Info messages maintain their content and context
            And: Info list provides helpful context and recommendations
            
        Info Filtering Verified:
            - info property returns only INFO severity messages
            - Non-info messages are excluded from info list
            - Info message content and context are preserved
            - Info list provides helpful contextual information
            
        Fixtures Used:
            - None (testing info filtering directly)
            
        Contextual Information Access Verified:
            Info property provides focused access to helpful validation context
            
        Related Tests:
            - test_validation_result_comprehensive_message_access_includes_all_types()
            - test_message_filtering_maintains_content_integrity()
        """
        # Given: ValidationResult with mixed message types
        result = ValidationResult(is_valid=True)
        
        # Add mixed message types
        result.add_info("First info")
        result.add_error("First error")
        result.add_info("Second info")
        result.add_warning("First warning")
        result.add_error("Second error")
        
        # When: info property is accessed
        info_messages = result.info
        
        # Then: Only info messages are returned
        assert len(info_messages) == 2
        assert "First info" in info_messages
        assert "Second info" in info_messages
        
        # And: Error and warning messages are excluded
        assert "First error" not in info_messages
        assert "Second error" not in info_messages
        assert "First warning" not in info_messages
        
        # And: Info list order is consistent with addition order
        assert info_messages[0] == "First info"
        assert info_messages[1] == "Second info"
        
        # Verify return type is List[str]
        assert isinstance(info_messages, list)
        assert all(isinstance(msg, str) for msg in info_messages)

    def test_validation_result_message_properties_return_string_lists(self):
        """
        Test that message properties return string lists for easy consumption.
        
        Verifies:
            Message property interfaces provide simple string-based access
            
        Business Impact:
            Enables simple validation result processing without complex message object handling
            
        Scenario:
            Given: ValidationResult with various ValidationMessage instances
            When: Message properties (errors, warnings, info) are accessed
            Then: String lists are returned containing message text
            And: Message objects are converted to string format
            And: String format preserves essential message content
            And: String lists are suitable for display and logging
            
        String Interface Verified:
            - errors property returns List[str] with error message text
            - warnings property returns List[str] with warning message text
            - info property returns List[str] with info message text
            - String conversion preserves essential message content
            
        Fixtures Used:
            - None (testing string interface directly)
            
        Simple Interface Verified:
            String-based message access enables simple validation result processing
            
        Related Tests:
            - test_message_string_conversion_preserves_essential_content()
            - test_string_message_lists_support_display_and_logging()
        """
        # Given: ValidationResult with various ValidationMessage instances
        result = ValidationResult(is_valid=True)
        
        # Add messages with different context complexity
        result.add_error("Critical validation error", field_path="config.redis", context={"type": "connection"})
        result.add_warning("Performance warning", context={"suggestion": "optimize"})
        result.add_info("Configuration info", field_path="cache")
        
        # When: Message properties are accessed
        errors = result.errors
        warnings = result.warnings
        info = result.info
        
        # Then: String lists are returned
        assert isinstance(errors, list)
        assert isinstance(warnings, list)
        assert isinstance(info, list)
        
        # And: All elements are strings
        assert all(isinstance(msg, str) for msg in errors)
        assert all(isinstance(msg, str) for msg in warnings)
        assert all(isinstance(msg, str) for msg in info)
        
        # And: String format preserves essential message content
        assert "Critical validation error" in errors
        assert "Performance warning" in warnings
        assert "Configuration info" in info
        
        # Verify counts match expected
        assert len(errors) == 1
        assert len(warnings) == 1
        assert len(info) == 1


class TestValidationResultStateManagement:
    """
    Test suite for ValidationResult validation state management.
    
    Scope:
        - Validation state determination logic based on message content
        - State transitions during message addition
        - State consistency across different message combinations
        - State-based validation result interpretation
        
    Business Critical:
        Validation state management drives configuration deployment decisions
        
    Test Strategy:
        - Unit tests for is_valid state determination with various message combinations
        - State transition testing during message addition sequences
        - State consistency verification across complex validation scenarios
        - State-based decision support functionality
        
    External Dependencies:
        - Message severity impact logic (internal): State determination rules
        - Configuration deployment logic (conceptual): State-based decision making
    """

    def test_validation_result_is_valid_reflects_error_presence(self):
        """
        Test that is_valid property accurately reflects presence or absence of errors.
        
        Verifies:
            Validation state determination is based on error presence
            
        Business Impact:
            Enables reliable deployment decisions based on validation state
            
        Scenario:
            Given: ValidationResult with various message combinations
            When: is_valid property is checked
            Then: is_valid is False when any errors are present
            And: is_valid is True when only warnings and info messages are present
            And: is_valid is True when no messages are present
            And: State reflects error impact on configuration validity
            
        Error-Based State Determination Verified:
            - Any error messages make is_valid False
            - Warnings and info messages do not affect is_valid
            - Empty validation results are valid by default
            - State determination is consistent across message combinations
            
        Fixtures Used:
            - None (testing state determination logic directly)
            
        Deployment Decision Support Verified:
            is_valid property provides reliable deployment decision support
            
        Related Tests:
            - test_validation_result_state_consistency_across_message_combinations()
            - test_validation_state_transitions_during_message_addition()
        """
        # Test empty validation result
        result = ValidationResult(is_valid=True)
        assert result.is_valid is True  # valid when no messages
        
        # Test with only warnings and info
        result.add_warning("Configuration warning")
        result.add_info("Configuration info")
        assert result.is_valid is True  # warnings/info don't affect validity
        
        # Test with single error
        result.add_error("Configuration error")
        assert result.is_valid is False  # any error makes invalid
        
        # Test new result with mixed messages but no errors
        result_no_errors = ValidationResult(is_valid=True)
        result_no_errors.add_warning("Warning 1")
        result_no_errors.add_warning("Warning 2")
        result_no_errors.add_info("Info 1")
        result_no_errors.add_info("Info 2")
        assert result_no_errors.is_valid is True  # still valid without errors
        
        # Test with errors present alongside warnings/info
        result_with_errors = ValidationResult(is_valid=True)
        result_with_errors.add_warning("Warning")
        result_with_errors.add_info("Info")
        result_with_errors.add_error("Error")
        assert result_with_errors.is_valid is False  # error makes invalid regardless

    def test_validation_result_maintains_state_consistency_during_message_addition(self):
        """
        Test that ValidationResult maintains state consistency during message addition sequences.
        
        Verifies:
            Validation state remains consistent as messages are added incrementally
            
        Business Impact:
            Ensures reliable validation state throughout incremental validation processes
            
        Scenario:
            Given: ValidationResult undergoing incremental message addition
            When: Messages are added in various sequences
            Then: Validation state remains consistent at each step
            And: State transitions are predictable and reliable
            And: Final state accurately reflects all validation messages
            And: State determination is order-independent for same message sets
            
        State Consistency Verified:
            - State remains consistent throughout message addition process
            - State transitions are predictable (valid->invalid when errors added)
            - Final state is determined by message content, not addition order
            - State determination is reliable across different addition sequences
            
        Fixtures Used:
            - None (testing incremental state management directly)
            
        Incremental Validation Reliability Verified:
            State management supports reliable incremental validation processes
            
        Related Tests:
            - test_validation_result_state_is_order_independent()
            - test_complex_validation_scenarios_maintain_state_accuracy()
        """
        # Given: ValidationResult undergoing incremental message addition
        result = ValidationResult(is_valid=True)
        
        # Test sequence 1: warnings -> info -> error
        assert result.is_valid is True  # start valid
        
        result.add_warning("First warning")
        assert result.is_valid is True  # still valid after warning
        assert len(result.messages) == 1
        
        result.add_info("Configuration info")
        assert result.is_valid is True  # still valid after info
        assert len(result.messages) == 2
        
        result.add_error("Configuration error")
        assert result.is_valid is False  # becomes invalid after error
        assert len(result.messages) == 3
        
        # Test order independence with another result
        result2 = ValidationResult(is_valid=True)
        
        # Same messages, different order: error -> warning -> info
        result2.add_error("Configuration error")
        assert result2.is_valid is False  # immediately invalid
        
        result2.add_warning("First warning")
        assert result2.is_valid is False  # remains invalid
        
        result2.add_info("Configuration info")
        assert result2.is_valid is False  # remains invalid
        
        # Both results have same final state despite different addition order
        assert len(result.messages) == len(result2.messages)
        assert result.is_valid == result2.is_valid

    def test_validation_result_supports_validation_workflow_decisions(self):
        """
        Test that ValidationResult supports validation workflow and deployment decisions.
        
        Verifies:
            Validation results provide sufficient information for workflow decisions
            
        Business Impact:
            Enables automated validation workflows and deployment pipeline integration
            
        Scenario:
            Given: ValidationResult with comprehensive validation information
            When: Validation workflow decisions need to be made
            Then: is_valid property supports go/no-go deployment decisions
            And: Message categories support different workflow responses
            And: Validation metadata supports workflow context
            And: Result structure enables automated decision making
            
        Workflow Decision Support Verified:
            - is_valid enables binary deployment decisions
            - Message categories enable nuanced workflow responses
            - Validation metadata provides workflow context
            - Result structure supports automated processing
            
        Fixtures Used:
            - None (testing workflow integration support directly)
            
        Deployment Pipeline Integration Verified:
            ValidationResult structure supports automated validation workflow integration
            
        Related Tests:
            - test_validation_result_enables_automated_deployment_decisions()
            - test_validation_metadata_supports_workflow_context()
        """
        # Given: ValidationResult with comprehensive validation information
        result = ValidationResult(
            is_valid=True,
            validation_type="configuration",
            schema_version="2.0"
        )
        
        # Add comprehensive validation messages
        result.add_error("Critical: Missing required field", field_path="redis.url")
        result.add_warning("Performance: TTL too low", field_path="cache.ttl", context={"current": 60, "recommended": 300})
        result.add_info("Loaded preset successfully", context={"preset": "production"})
        
        # When: Validation workflow decisions need to be made
        
        # Then: is_valid property supports go/no-go deployment decisions
        deployment_decision = "DEPLOY" if result.is_valid else "BLOCK"
        assert deployment_decision == "BLOCK"  # errors block deployment
        
        # And: Message categories support different workflow responses
        error_count = len(result.errors)
        warning_count = len(result.warnings)
        info_count = len(result.info)
        
        # Workflow logic examples
        requires_immediate_attention = error_count > 0
        has_optimization_opportunities = warning_count > 0
        has_helpful_context = info_count > 0
        
        assert requires_immediate_attention is True
        assert has_optimization_opportunities is True
        assert has_helpful_context is True
        
        # And: Validation metadata provides workflow context
        assert result.validation_type == "configuration"  # context for workflow type
        assert result.schema_version == "2.0"  # schema compatibility info
        
        # And: Result structure enables automated decision making
        workflow_summary = {
            "deployment_allowed": result.is_valid,
            "critical_issues": error_count,
            "improvement_suggestions": warning_count,
            "context_messages": info_count,
            "validation_context": result.validation_type
        }
        
        assert workflow_summary["deployment_allowed"] is False
        assert workflow_summary["critical_issues"] == 1
        assert workflow_summary["improvement_suggestions"] == 1
        assert workflow_summary["context_messages"] == 1