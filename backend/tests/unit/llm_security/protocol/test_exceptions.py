"""
Test suite for security service exception hierarchy.

This module tests the exception classes that define error conditions and failure
modes for security scanning operations. Tests verify exception inheritance,
error context preservation, and proper exception chaining for debugging.

Test Strategy:
    - Verify exception inheritance hierarchy
    - Test exception initialization with message and context
    - Validate error chaining via original_error parameter
    - Test scanner_name context preservation
    - Verify string representation and error messages
"""

import pytest
from app.infrastructure.security.llm.protocol import (
    SecurityServiceError,
    ScannerInitializationError,
    ScannerTimeoutError,
    ScannerConfigurationError
)


class TestSecurityServiceError:
    """
    Test suite for SecurityServiceError base exception.
    
    Scope:
        - Base exception initialization
        - Message preservation
        - Scanner name context
        - Original error chaining
        - Exception hierarchy foundation
        
    Business Critical:
        Base exception provides foundation for error handling and debugging
        across all security service failure scenarios.
        
    Test Coverage:
        - Initialization with various parameter combinations
        - Error context preservation
        - Exception chaining support
        - String representation
    """
    
    def test_security_service_error_initialization_with_message_only(self):
        """
        Test that SecurityServiceError can be created with just error message.

        Verifies:
            Exception initializes with message parameter alone, with
            optional fields defaulting to None per contract

        Business Impact:
            Enables simple error creation for basic failure scenarios
            without additional context overhead

        Scenario:
            Given: Error message describing the security service failure
            When: Creating SecurityServiceError(message)
            Then: Exception is created successfully
            And: Message is accessible via str(error)
            And: scanner_name and original_error are None

        Fixtures Used:
            None - Direct exception testing
        """
        # Given: Error message describing the security service failure
        error_message = "Security service is temporarily unavailable"

        # When: Creating SecurityServiceError(message)
        error = SecurityServiceError(error_message)

        # Then: Exception is created successfully
        assert error is not None

        # And: Message is accessible via str(error)
        assert str(error) == error_message

        # And: scanner_name and original_error are None
        assert error.scanner_name is None
        assert error.original_error is None
    
    def test_security_service_error_initialization_with_scanner_name(self):
        """
        Test that SecurityServiceError accepts scanner_name for context.

        Verifies:
            Scanner identification is preserved for targeted troubleshooting
            per documented contract

        Business Impact:
            Enables quick identification of which scanner failed in
            multi-scanner security infrastructure

        Scenario:
            Given: Error message and scanner name
            When: Creating SecurityServiceError(message, scanner_name="prompt_guard")
            Then: scanner_name attribute equals "prompt_guard"
            And: Scanner context is preserved for debugging

        Fixtures Used:
            None - Direct exception testing
        """
        # Given: Error message and scanner name
        error_message = "Scanner connection failed"
        scanner_name = "prompt_guard"

        # When: Creating SecurityServiceError(message, scanner_name="prompt_guard")
        error = SecurityServiceError(error_message, scanner_name=scanner_name)

        # Then: scanner_name attribute equals "prompt_guard"
        assert error.scanner_name == scanner_name

        # And: Scanner context is preserved for debugging
        assert str(error) == error_message
        assert error.original_error is None
    
    def test_security_service_error_initialization_with_original_error(self):
        """
        Test that SecurityServiceError accepts original_error for exception chaining.

        Verifies:
            Original exception is preserved for root cause analysis per
            documented exception chaining support

        Business Impact:
            Preserves complete error chain for debugging complex failure
            scenarios across system boundaries

        Scenario:
            Given: Error message and original exception (e.g., ConnectionError)
            When: Creating SecurityServiceError(message, original_error=original)
            Then: original_error attribute contains original exception
            And: Full error chain is available for analysis

        Fixtures Used:
            None - Direct exception testing
        """
        # Given: Error message and original exception (e.g., ConnectionError)
        error_message = "Network connectivity issue"
        original_error = ConnectionError("Failed to connect to scanner service")

        # When: Creating SecurityServiceError(message, original_error=original)
        error = SecurityServiceError(error_message, original_error=original_error)

        # Then: original_error attribute contains original exception
        assert error.original_error is original_error
        assert isinstance(error.original_error, ConnectionError)

        # And: Full error chain is available for analysis
        assert str(error) == error_message
        assert error.scanner_name is None
    
    def test_security_service_error_initialization_with_all_parameters(self):
        """
        Test that SecurityServiceError accepts all parameters simultaneously.

        Verifies:
            Complete error context can be captured in single exception
            per comprehensive error handling design

        Business Impact:
            Supports detailed error reporting with complete context for
            production incident investigation

        Scenario:
            Given: Error message, scanner name, and original error
            When: Creating SecurityServiceError with all parameters
            Then: All context is preserved and accessible
            And: Error provides complete debugging information

        Fixtures Used:
            None - Direct exception testing
        """
        # Given: Error message, scanner name, and original error
        error_message = "Scanner configuration validation failed"
        scanner_name = "injection_detector"
        original_error = ValueError("Invalid threshold value: 1.5")

        # When: Creating SecurityServiceError with all parameters
        error = SecurityServiceError(
            error_message,
            scanner_name=scanner_name,
            original_error=original_error
        )

        # Then: All context is preserved and accessible
        assert str(error) == error_message
        assert error.scanner_name == scanner_name
        assert error.original_error is original_error

        # And: Error provides complete debugging information
        assert isinstance(error.original_error, ValueError)

    def test_security_service_error_inherits_from_exception(self):
        """
        Test that SecurityServiceError inherits from base Exception class.

        Verifies:
            Exception is part of standard Python exception hierarchy per
            Python exception handling conventions

        Business Impact:
            Ensures exception can be caught with standard except clauses
            and follows Python error handling patterns

        Scenario:
            Given: SecurityServiceError class
            When: Checking inheritance chain
            Then: SecurityServiceError is subclass of Exception
            And: Standard exception handling works correctly

        Fixtures Used:
            None - Direct exception testing
        """
        # Given: SecurityServiceError class
        # When: Checking inheritance chain
        # Then: SecurityServiceError is subclass of Exception
        assert issubclass(SecurityServiceError, Exception)

        # And: Standard exception handling works correctly
        try:
            raise SecurityServiceError("Test error")
        except Exception as e:
            assert isinstance(e, SecurityServiceError)
            assert str(e) == "Test error"

    def test_security_service_error_string_representation_includes_message(self):
        """
        Test that str(SecurityServiceError) returns the error message.

        Verifies:
            String conversion produces human-readable error description
            per exception convention

        Business Impact:
            Enables clear error messages in logs and user-facing error
            responses without additional formatting

        Scenario:
            Given: SecurityServiceError with specific message
            When: Converting to string via str(error)
            Then: String representation contains original message
            And: Message is clear and actionable

        Fixtures Used:
            None - Direct exception testing
        """
        # Given: SecurityServiceError with specific message
        error_message = "API rate limit exceeded. Please retry later."

        # When: Converting to string via str(error)
        error = SecurityServiceError(error_message)
        string_repr = str(error)

        # Then: String representation contains original message
        assert string_repr == error_message

        # And: Message is clear and actionable
        assert "rate limit" in string_repr.lower()
        assert "retry" in string_repr.lower()

    def test_security_service_error_can_be_raised_and_caught(self):
        """
        Test that SecurityServiceError can be raised and caught normally.

        Verifies:
            Exception follows standard Python raise/except patterns per
            exception protocol

        Business Impact:
            Ensures exception integrates properly with Python error
            handling infrastructure

        Scenario:
            Given: Code that raises SecurityServiceError
            When: Raising and catching the exception
            Then: Exception is caught successfully in except clause
            And: Error context is accessible in exception handler

        Fixtures Used:
            None - Direct exception testing
        """
        # Given: Code that raises SecurityServiceError
        error_message = "Scanner initialization failed"
        scanner_name = "pii_detector"

        # When: Raising and catching the exception
        caught_exception = None
        try:
            raise SecurityServiceError(error_message, scanner_name=scanner_name)
        except SecurityServiceError as e:
            caught_exception = e

        # Then: Exception is caught successfully in except clause
        assert caught_exception is not None
        assert isinstance(caught_exception, SecurityServiceError)

        # And: Error context is accessible in exception handler
        assert str(caught_exception) == error_message
        assert caught_exception.scanner_name == scanner_name

    def test_security_service_error_supports_exception_chaining(self):
        """
        Test that SecurityServiceError supports 'raise from' exception chaining.

        Verifies:
            Exception chaining preserves full error context per Python 3
            exception chaining protocol

        Business Impact:
            Maintains complete error history for debugging complex
            multi-layer failures

        Scenario:
            Given: Original exception and SecurityServiceError
            When: Raising SecurityServiceError from original exception
            Then: __cause__ attribute preserves original exception
            And: Full traceback chain is available

        Fixtures Used:
            None - Direct exception testing
        """
        # Given: Original exception and SecurityServiceError
        original_error = ConnectionError("Database connection timeout")
        error_message = "Failed to initialize scanner database"

        # When: Raising SecurityServiceError from original exception
        caught_exception = None
        try:
            try:
                # Simulate the original failure
                raise original_error
            except ConnectionError as e:
                # Chain the security service error
                raise SecurityServiceError(error_message, original_error=e) from e
        except SecurityServiceError as e:
            caught_exception = e

        # Then: __cause__ attribute preserves original exception
        assert caught_exception is not None
        assert caught_exception.__cause__ is original_error
        assert isinstance(caught_exception.__cause__, ConnectionError)

        # And: Full traceback chain is available
        assert caught_exception.original_error is original_error
        assert str(caught_exception) == error_message


class TestScannerInitializationError:
    """
    Test suite for ScannerInitializationError exception.
    
    Scope:
        - Initialization error specific attributes
        - Inheritance from SecurityServiceError
        - Scanner initialization failure scenarios
        - Configuration and dependency error contexts
        
    Business Critical:
        Initialization errors prevent security service startup failures
        by providing clear diagnostics for configuration issues.
        
    Test Coverage:
        - Exception creation and inheritance
        - Context preservation for initialization failures
        - Diagnostic information for troubleshooting
    """
    
    def test_scanner_initialization_error_inherits_from_security_service_error(self):
        """
        Test that ScannerInitializationError inherits from SecurityServiceError.

        Verifies:
            Exception hierarchy enables catching by base class per
            documented inheritance chain

        Business Impact:
            Allows both specific (initialization) and general (service)
            error handling in client code

        Scenario:
            Given: ScannerInitializationError class
            When: Checking inheritance
            Then: Exception is subclass of SecurityServiceError
            And: Can be caught by base class exception handler

        Fixtures Used:
            None - Direct exception testing
        """
        # Given: ScannerInitializationError class
        # When: Checking inheritance
        # Then: Exception is subclass of SecurityServiceError
        assert issubclass(ScannerInitializationError, SecurityServiceError)

        # And: Can be caught by base class exception handler
        try:
            raise ScannerInitializationError("Test init error")
        except SecurityServiceError as e:
            assert isinstance(e, ScannerInitializationError)
            assert str(e) == "Test init error"

    def test_scanner_initialization_error_can_be_created_with_scanner_name(self):
        """
        Test that ScannerInitializationError accepts scanner_name for failed scanner identification.

        Verifies:
            Failed scanner is identifiable in initialization errors per
            troubleshooting requirements

        Business Impact:
            Enables quick identification of which scanner failed to
            initialize in multi-scanner deployments

        Scenario:
            Given: Initialization error message and scanner name
            When: Creating ScannerInitializationError
            Then: scanner_name is preserved for debugging
            And: Error clearly identifies problematic scanner

        Fixtures Used:
            None - Direct exception testing
        """
        # Given: Initialization error message and scanner name
        error_message = "Invalid API key format"
        scanner_name = "prompt_injection_scanner"

        # When: Creating ScannerInitializationError
        error = ScannerInitializationError(error_message, scanner_name=scanner_name)

        # Then: scanner_name is preserved for debugging
        assert error.scanner_name == scanner_name

        # And: Error clearly identifies problematic scanner
        assert str(error) == error_message
        assert error.original_error is None

    def test_scanner_initialization_error_preserves_original_cause(self):
        """
        Test that ScannerInitializationError preserves original initialization failure.

        Verifies:
            Root cause exceptions (ImportError, ValueError, etc.) are
            chained for complete diagnostics

        Business Impact:
            Provides complete error context for resolving configuration,
            dependency, or permission issues

        Scenario:
            Given: Original exception (e.g., ImportError for missing library)
            When: Creating ScannerInitializationError with original_error
            Then: Original exception is accessible for root cause analysis
            And: Complete error chain aids troubleshooting

        Fixtures Used:
            None - Direct exception testing
        """
        # Given: Original exception (e.g., ImportError for missing library)
        error_message = "Scanner dependencies not found"
        scanner_name = "pii_detector"
        original_error = ImportError("No module named 'transformers'")

        # When: Creating ScannerInitializationError with original_error
        error = ScannerInitializationError(
            error_message,
            scanner_name=scanner_name,
            original_error=original_error
        )

        # Then: Original exception is accessible for root cause analysis
        assert error.original_error is original_error
        assert isinstance(error.original_error, ImportError)

        # And: Complete error chain aids troubleshooting
        assert error.scanner_name == scanner_name
        assert str(error) == error_message

    def test_scanner_initialization_error_indicates_initialization_failure_context(self):
        """
        Test that ScannerInitializationError clearly indicates initialization failure.

        Verifies:
            Error message and type clearly communicate initialization
            failure vs. runtime operational failures

        Business Impact:
            Prevents confusion between startup configuration issues and
            runtime operational failures

        Scenario:
            Given: ScannerInitializationError with descriptive message
            When: Examining error type and message
            Then: Failure is clearly identified as initialization issue
            And: Appropriate remediation (config fix, dependency install) is implied

        Fixtures Used:
            None - Direct exception testing
        """
        # Given: ScannerInitializationError with descriptive message
        error_message = "API key authentication failed during scanner startup"

        # When: Creating ScannerInitializationError
        error = ScannerInitializationError(error_message)

        # Then: Failure is clearly identified as initialization issue
        assert isinstance(error, ScannerInitializationError)
        assert "authentication failed" in str(error).lower()

        # And: Appropriate remediation (config fix, dependency install) is implied
        # The exception type itself indicates initialization vs runtime failure
        assert issubclass(ScannerInitializationError, SecurityServiceError)

        # Can be caught specifically for initialization failures
        caught_as_init_error = False
        caught_as_service_error = False
        try:
            raise error
        except ScannerInitializationError:
            caught_as_init_error = True
        except SecurityServiceError:
            caught_as_service_error = True

        assert caught_as_init_error
        assert not caught_as_service_error


class TestScannerTimeoutError:
    """
    Test suite for ScannerTimeoutError exception.
    
    Scope:
        - Timeout error specific attributes
        - Inheritance from SecurityServiceError
        - Scanner timeout failure scenarios
        - Performance degradation indication
        
    Business Critical:
        Timeout errors enable performance monitoring and prevent resource
        exhaustion from hung scanner operations.
        
    Test Coverage:
        - Exception creation for timeout scenarios
        - Scanner identification in timeout contexts
        - Timeout vs. other error differentiation
    """
    
    def test_scanner_timeout_error_inherits_from_security_service_error(self):
        """
        Test that ScannerTimeoutError inherits from SecurityServiceError.

        Verifies:
            Exception hierarchy enables unified error handling per
            documented inheritance structure

        Business Impact:
            Allows catching timeout-specific errors or all security
            errors via base class

        Scenario:
            Given: ScannerTimeoutError class
            When: Checking inheritance chain
            Then: Exception is subclass of SecurityServiceError
            And: Participates in exception hierarchy properly

        Fixtures Used:
            None - Direct exception testing
        """
        # Given: ScannerTimeoutError class
        # When: Checking inheritance chain
        # Then: Exception is subclass of SecurityServiceError
        assert issubclass(ScannerTimeoutError, SecurityServiceError)

        # And: Participates in exception hierarchy properly
        try:
            raise ScannerTimeoutError("Test timeout")
        except SecurityServiceError as e:
            assert isinstance(e, ScannerTimeoutError)
            assert str(e) == "Test timeout"

    def test_scanner_timeout_error_can_be_created_with_timeout_details(self):
        """
        Test that ScannerTimeoutError accepts timeout duration and scanner context.

        Verifies:
            Timeout exceptions capture which scanner timed out and
            provide duration context per monitoring requirements

        Business Impact:
            Enables performance monitoring and alerting for slow or
            hung scanners requiring optimization

        Scenario:
            Given: Timeout error message indicating duration limit
            When: Creating ScannerTimeoutError with scanner name
            Then: Timeout context is preserved for performance analysis
            And: Scanner can be identified for targeted optimization

        Fixtures Used:
            None - Direct exception testing
        """
        # Given: Timeout error message indicating duration limit
        error_message = "Scan exceeded 30 second limit"
        scanner_name = "prompt_injection_detector"

        # When: Creating ScannerTimeoutError with scanner name
        error = ScannerTimeoutError(error_message, scanner_name=scanner_name)

        # Then: Timeout context is preserved for performance analysis
        assert error.scanner_name == scanner_name
        assert "30 second" in str(error)

        # And: Scanner can be identified for targeted optimization
        assert error.original_error is None
        assert isinstance(error, ScannerTimeoutError)

    def test_scanner_timeout_error_preserves_original_timeout_exception(self):
        """
        Test that ScannerTimeoutError can chain asyncio.TimeoutError or other timeout causes.

        Verifies:
            Original timeout exceptions are preserved for debugging per
            exception chaining requirements

        Business Impact:
            Maintains complete error context for investigating timeout
            root causes (network, CPU, blocking operations)

        Scenario:
            Given: Original timeout exception (asyncio.TimeoutError)
            When: Creating ScannerTimeoutError with original_error
            Then: Timeout cause is preserved in exception chain
            And: Full context is available for performance debugging

        Fixtures Used:
            None - Direct exception testing
        """
        import asyncio

        # Given: Original timeout exception (asyncio.TimeoutError)
        error_message = "External security service timeout"
        scanner_name = "content_safety_scanner"
        original_error = asyncio.TimeoutError("Operation timed out")

        # When: Creating ScannerTimeoutError with original_error
        error = ScannerTimeoutError(
            error_message,
            scanner_name=scanner_name,
            original_error=original_error
        )

        # Then: Timeout cause is preserved in exception chain
        assert error.original_error is original_error
        assert isinstance(error.original_error, asyncio.TimeoutError)

        # And: Full context is available for performance debugging
        assert error.scanner_name == scanner_name
        assert str(error) == error_message

    def test_scanner_timeout_error_indicates_performance_issue(self):
        """
        Test that ScannerTimeoutError clearly communicates performance degradation.

        Verifies:
            Error type and message indicate timeout vs. other failure
            types for appropriate handling

        Business Impact:
            Enables distinct handling of timeouts (retry, skip, alert)
            vs. permanent failures (block, error)

        Scenario:
            Given: ScannerTimeoutError with timeout duration in message
            When: Examining error for performance context
            Then: Timeout is clearly distinguished from other failures
            And: Appropriate retry or scaling strategies are indicated

        Fixtures Used:
            None - Direct exception testing
        """
        # Given: ScannerTimeoutError with timeout duration in message
        error_message = "Input validation exceeded 10 second timeout"
        scanner_name = "input_validator"

        # When: Creating ScannerTimeoutError
        error = ScannerTimeoutError(error_message, scanner_name=scanner_name)

        # Then: Timeout is clearly distinguished from other failures
        assert isinstance(error, ScannerTimeoutError)
        assert "timeout" in str(error).lower()
        assert "10 second" in str(error)

        # And: Appropriate retry or scaling strategies are indicated
        # The exception type itself indicates performance vs configuration issue
        assert issubclass(ScannerTimeoutError, SecurityServiceError)

        # Can be handled differently than configuration errors
        timeout_caught = False
        config_caught = False
        service_caught = False

        try:
            raise error
        except ScannerTimeoutError:
            timeout_caught = True
        except ScannerConfigurationError:
            config_caught = True
        except SecurityServiceError:
            service_caught = True

        assert timeout_caught
        assert not config_caught
        assert not service_caught


class TestScannerConfigurationError:
    """
    Test suite for ScannerConfigurationError exception.
    
    Scope:
        - Configuration error specific attributes
        - Inheritance from SecurityServiceError
        - Scanner configuration validation failures
        - Configuration fix guidance
        
    Business Critical:
        Configuration errors prevent invalid scanner deployments by
        catching configuration issues early with clear remediation guidance.
        
    Test Coverage:
        - Exception creation for configuration failures
        - Invalid parameter identification
        - Configuration validation contexts
    """
    
    def test_scanner_configuration_error_inherits_from_security_service_error(self):
        """
        Test that ScannerConfigurationError inherits from SecurityServiceError.

        Verifies:
            Exception hierarchy enables configuration-specific and general
            error handling per inheritance design

        Business Impact:
            Supports both targeted configuration error handling and
            catch-all security error handling

        Scenario:
            Given: ScannerConfigurationError class
            When: Checking inheritance
            Then: Exception is subclass of SecurityServiceError
            And: Fits into exception hierarchy correctly

        Fixtures Used:
            None - Direct exception testing
        """
        # Given: ScannerConfigurationError class
        # When: Checking inheritance
        # Then: Exception is subclass of SecurityServiceError
        assert issubclass(ScannerConfigurationError, SecurityServiceError)

        # And: Fits into exception hierarchy correctly
        try:
            raise ScannerConfigurationError("Test config error")
        except SecurityServiceError as e:
            assert isinstance(e, ScannerConfigurationError)
            assert str(e) == "Test config error"

    def test_scanner_configuration_error_can_indicate_invalid_parameters(self):
        """
        Test that ScannerConfigurationError can describe specific invalid configuration.

        Verifies:
            Error messages identify which configuration parameter is
            invalid per troubleshooting requirements

        Business Impact:
            Reduces debugging time by clearly identifying misconfigured
            parameters requiring correction

        Scenario:
            Given: Configuration error describing invalid threshold value
            When: Creating ScannerConfigurationError with detailed message
            Then: Invalid parameter and valid range are identified
            And: Remediation guidance is clear from error message

        Fixtures Used:
            None - Direct exception testing
        """
        # Given: Configuration error describing invalid threshold value
        error_message = "Security threshold must be between 0.0 and 1.0"
        scanner_name = "content_safety_scanner"

        # When: Creating ScannerConfigurationError with detailed message
        error = ScannerConfigurationError(error_message, scanner_name=scanner_name)

        # Then: Invalid parameter and valid range are identified
        assert "threshold" in str(error).lower()
        assert "0.0" in str(error)
        assert "1.0" in str(error)

        # And: Remediation guidance is clear from error message
        assert error.scanner_name == scanner_name
        assert error.original_error is None

    def test_scanner_configuration_error_preserves_validation_failure_context(self):
        """
        Test that ScannerConfigurationError can chain original validation exceptions.

        Verifies:
            Original validation errors (ValueError, TypeError) are preserved
            for complete diagnostic information

        Business Impact:
            Provides full context for resolving configuration schema
            violations and type mismatches

        Scenario:
            Given: Original validation exception (ValueError for out-of-range value)
            When: Creating ScannerConfigurationError with original_error
            Then: Validation context is preserved in exception chain
            And: Complete error information aids configuration correction

        Fixtures Used:
            None - Direct exception testing
        """
        # Given: Original validation exception (ValueError for out-of-range value)
        error_message = "Invalid scanner parameters detected"
        scanner_name = "threat_detection_scanner"
        original_error = ValueError("Invalid confidence threshold: 1.5")

        # When: Creating ScannerConfigurationError with original_error
        error = ScannerConfigurationError(
            error_message,
            scanner_name=scanner_name,
            original_error=original_error
        )

        # Then: Validation context is preserved in exception chain
        assert error.original_error is original_error
        assert isinstance(error.original_error, ValueError)

        # And: Complete error information aids configuration correction
        assert error.scanner_name == scanner_name
        assert str(error) == error_message

    def test_scanner_configuration_error_differentiates_from_runtime_errors(self):
        """
        Test that ScannerConfigurationError clearly indicates configuration vs. runtime issues.

        Verifies:
            Configuration errors are distinguished from operational
            failures for appropriate remediation

        Business Impact:
            Prevents wasted effort troubleshooting runtime when
            configuration correction is needed

        Scenario:
            Given: ScannerConfigurationError for invalid threshold
            When: Examining error type and message
            Then: Configuration issue is clear vs. runtime operational failure
            And: Configuration file/parameter correction is indicated

        Fixtures Used:
            None - Direct exception testing
        """
        # Given: ScannerConfigurationError for invalid threshold
        error_message = "Threat threshold must be between 0.0 and 1.0, got 1.5"
        scanner_name = "threat_detector"

        # When: Creating ScannerConfigurationError
        error = ScannerConfigurationError(error_message, scanner_name=scanner_name)

        # Then: Configuration issue is clear vs. runtime operational failure
        assert isinstance(error, ScannerConfigurationError)
        assert "threshold" in str(error).lower()
        assert "1.5" in str(error)

        # And: Configuration file/parameter correction is indicated
        # The exception type itself indicates configuration vs runtime
        assert issubclass(ScannerConfigurationError, SecurityServiceError)

        # Can be handled differently than timeout errors
        config_caught = False
        timeout_caught = False
        service_caught = False

        try:
            raise error
        except ScannerConfigurationError:
            config_caught = True
        except ScannerTimeoutError:
            timeout_caught = True
        except SecurityServiceError:
            service_caught = True

        assert config_caught
        assert not timeout_caught
        assert not service_caught


class TestExceptionHierarchy:
    """
    Test suite for complete security service exception hierarchy.
    
    Scope:
        - Overall exception inheritance structure
        - Exception hierarchy completeness
        - Catch-all exception handling patterns
        - Exception type differentiation
        
    Business Critical:
        Proper exception hierarchy enables robust error handling with
        both specific and general exception catching strategies.
        
    Test Coverage:
        - Complete inheritance relationships
        - Base class catch-all behavior
        - Specific exception filtering
        - Exception type identification
    """
    
    def test_all_specific_errors_inherit_from_security_service_error(self):
        """
        Test that all specific security exceptions inherit from SecurityServiceError.

        Verifies:
            Complete exception hierarchy has single root base class per
            error handling design

        Business Impact:
            Enables catching all security-related errors with single
            except clause when needed

        Scenario:
            Given: All security exception classes
            When: Checking inheritance relationships
            Then: All specific errors are subclasses of SecurityServiceError
            And: Single base class catch handles all security errors

        Fixtures Used:
            None - Direct exception testing
        """
        # Given: All security exception classes
        specific_exceptions = [
            ScannerInitializationError,
            ScannerTimeoutError,
            ScannerConfigurationError
        ]

        # When: Checking inheritance relationships
        # Then: All specific errors are subclasses of SecurityServiceError
        for exception_class in specific_exceptions:
            assert issubclass(exception_class, SecurityServiceError)

        # And: Single base class catch handles all security errors
        for exception_class in specific_exceptions:
            try:
                raise exception_class("Test error")
            except SecurityServiceError as e:
                assert isinstance(e, exception_class)

    def test_security_service_error_catch_all_pattern_works(self):
        """
        Test that catching SecurityServiceError catches all specific exception types.

        Verifies:
            Base class exception handling captures all security errors
            per catch-all design pattern

        Business Impact:
            Simplifies error handling when specific error type doesn't
            matter, reducing code complexity

        Scenario:
            Given: Code raising various specific security exceptions
            When: Catching with 'except SecurityServiceError'
            Then: All security exceptions are caught by base class handler
            And: Specific error types can still be identified if needed

        Fixtures Used:
            None - Direct exception testing
        """
        # Given: Code raising various specific security exceptions
        exception_types = [
            (ScannerInitializationError, "Init failed"),
            (ScannerTimeoutError, "Timeout occurred"),
            (ScannerConfigurationError, "Config invalid")
        ]

        for exception_class, message in exception_types:
            # When: Catching with 'except SecurityServiceError'
            caught_exception = None
            try:
                raise exception_class(message, scanner_name="test_scanner")
            except SecurityServiceError as e:
                caught_exception = e

            # Then: All security exceptions are caught by base class handler
            assert caught_exception is not None
            assert isinstance(caught_exception, SecurityServiceError)

            # And: Specific error types can still be identified if needed
            assert isinstance(caught_exception, exception_class)
            assert str(caught_exception) == message

    def test_specific_exception_types_can_be_caught_individually(self):
        """
        Test that specific exception types can be caught before base class.

        Verifies:
            Exception hierarchy supports targeted exception handling per
            Python exception handling rules

        Business Impact:
            Enables different handling strategies for different failure
            types (retry timeouts, log config errors, etc.)

        Scenario:
            Given: Code with multiple except clauses for different error types
            When: Raising specific exception types
            Then: Most specific matching except clause catches each error
            And: Base class catch-all works as fallback

        Fixtures Used:
            None - Direct exception testing

        Edge Cases Covered:
            - ScannerTimeoutError caught before SecurityServiceError
            - ScannerConfigurationError caught specifically
            - ScannerInitializationError handled distinctly
        """
        # Test ScannerTimeoutError caught before SecurityServiceError
        timeout_caught_specifically = False
        timeout_caught_generally = False

        try:
            raise ScannerTimeoutError("Timeout error", scanner_name="scanner1")
        except ScannerTimeoutError:
            timeout_caught_specifically = True
        except SecurityServiceError:
            timeout_caught_generally = True

        assert timeout_caught_specifically
        assert not timeout_caught_generally

        # Test ScannerConfigurationError caught specifically
        config_caught_specifically = False
        config_caught_generally = False

        try:
            raise ScannerConfigurationError("Config error", scanner_name="scanner2")
        except ScannerConfigurationError:
            config_caught_specifically = True
        except SecurityServiceError:
            config_caught_generally = True

        assert config_caught_specifically
        assert not config_caught_generally

        # Test ScannerInitializationError handled distinctly
        init_caught_specifically = False
        init_caught_generally = False

        try:
            raise ScannerInitializationError("Init error", scanner_name="scanner3")
        except ScannerInitializationError:
            init_caught_specifically = True
        except SecurityServiceError:
            init_caught_generally = True

        assert init_caught_specifically
        assert not init_caught_generally

        # Test base class catch-all works as fallback for unknown error types
        # (if there were other exception types in the hierarchy)
        fallback_caught = False
        try:
            raise ScannerTimeoutError("Will be caught by base")
        except (ScannerInitializationError, ScannerConfigurationError):
            pass  # Won't catch
        except SecurityServiceError:
            fallback_caught = True

        assert fallback_caught

    def test_exception_hierarchy_enables_error_type_identification(self):
        """
        Test that exception types can be identified using isinstance checks.

        Verifies:
            Error type checking works correctly with inheritance hierarchy
            per Python type checking patterns

        Business Impact:
            Enables conditional error handling based on error type without
            requiring specific except clauses

        Scenario:
            Given: Caught SecurityServiceError exception
            When: Checking type with isinstance()
            Then: Specific error types are identifiable
            And: Base class type check returns True for all security errors

        Fixtures Used:
            None - Direct exception testing
        """
        # Create various specific exceptions
        exceptions = [
            ScannerInitializationError("Init error", scanner_name="scanner1"),
            ScannerTimeoutError("Timeout error", scanner_name="scanner2"),
            ScannerConfigurationError("Config error", scanner_name="scanner3")
        ]

        # Test each exception can be identified correctly
        for error in exceptions:
            # Given: Caught SecurityServiceError exception
            assert isinstance(error, SecurityServiceError)

            # When: Checking type with isinstance()
            # Then: Specific error types are identifiable
            if isinstance(error, ScannerInitializationError):
                assert isinstance(error, ScannerInitializationError)
                assert "Init error" in str(error)
            elif isinstance(error, ScannerTimeoutError):
                assert isinstance(error, ScannerTimeoutError)
                assert "Timeout error" in str(error)
            elif isinstance(error, ScannerConfigurationError):
                assert isinstance(error, ScannerConfigurationError)
                assert "Config error" in str(error)

            # And: Base class type check returns True for all security errors
            assert isinstance(error, SecurityServiceError)
            assert isinstance(error, Exception)

        # Test specific type checking scenarios
        timeout_error = ScannerTimeoutError("Test timeout")
        config_error = ScannerConfigurationError("Test config")

        # Positive checks
        assert isinstance(timeout_error, ScannerTimeoutError)
        assert isinstance(timeout_error, SecurityServiceError)
        assert isinstance(config_error, ScannerConfigurationError)
        assert isinstance(config_error, SecurityServiceError)

        # Negative checks
        assert not isinstance(timeout_error, ScannerConfigurationError)
        assert not isinstance(timeout_error, ScannerInitializationError)
        assert not isinstance(config_error, ScannerTimeoutError)
        assert not isinstance(config_error, ScannerInitializationError)

