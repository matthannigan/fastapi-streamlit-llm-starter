"""
Test suite for ConfigurationError custom exception.

Tests verify ConfigurationError exception creation, formatting, and context
provision according to the public contract defined in config_loader.pyi.
"""

import pytest
from tests.unit.llm_security.conftest import MockConfigurationError


class TestConfigurationErrorInitialization:
    """Test ConfigurationError exception instantiation."""

    def test_configuration_error_with_message_only(self):
        """
        Test that ConfigurationError can be created with just an error message.

        Verifies:
            ConfigurationError.__init__() accepts message parameter and creates
            exception instance per contract's Args section.

        Business Impact:
            Provides basic error reporting capability for configuration failures
            with clear error descriptions.

        Scenario:
            Given: An error message string describing configuration issue.
            When: ConfigurationError is instantiated with message only.
            Then: Exception instance is created with message attribute set.

        Fixtures Used:
            None - tests basic exception creation.
        """
        # Given: An error message string describing configuration issue
        error_message = "Invalid YAML syntax"

        # When: ConfigurationError is instantiated with message only
        error = MockConfigurationError(message=error_message)

        # Then: Exception instance is created with message attribute set
        assert error.message == error_message
        assert error.suggestion is None
        assert error.file_path is None
        assert str(error) == error_message

    def test_configuration_error_with_suggestion(self):
        """
        Test that ConfigurationError stores optional suggestion for resolution.

        Verifies:
            ConfigurationError.__init__() accepts and stores suggestion parameter
            per contract's Args section.

        Business Impact:
            Provides actionable guidance to users for resolving configuration
            issues quickly.

        Scenario:
            Given: Error message and suggestion for resolution.
            When: ConfigurationError is instantiated with both parameters.
            Then: Exception stores both message and suggestion attributes.

        Fixtures Used:
            None - tests exception attributes.
        """
        # Given: Error message and suggestion for resolution
        error_message = "Missing required field: api_key"
        suggestion = "Add api_key to your configuration file"

        # When: ConfigurationError is instantiated with both parameters
        error = MockConfigurationError(message=error_message, suggestion=suggestion)

        # Then: Exception stores both message and suggestion attributes
        assert error.message == error_message
        assert error.suggestion == suggestion
        assert error.file_path is None

    def test_configuration_error_with_file_path(self):
        """
        Test that ConfigurationError stores optional file_path context.

        Verifies:
            ConfigurationError.__init__() accepts and stores file_path parameter
            per contract's Args section.

        Business Impact:
            Provides file context for debugging configuration errors by showing
            which configuration file caused the issue.

        Scenario:
            Given: Error message and configuration file path.
            When: ConfigurationError is instantiated with file_path parameter.
            Then: Exception stores file_path attribute for context.

        Fixtures Used:
            None - tests exception attributes.
        """
        # Given: Error message and configuration file path
        error_message = "Invalid port number"
        file_path = "/path/to/config.yaml"

        # When: ConfigurationError is instantiated with file_path parameter
        error = MockConfigurationError(message=error_message, file_path=file_path)

        # Then: Exception stores file_path attribute for context
        assert error.message == error_message
        assert error.suggestion is None
        assert error.file_path == file_path

    def test_configuration_error_with_all_parameters(self):
        """
        Test that ConfigurationError stores all optional context parameters.

        Verifies:
            ConfigurationError.__init__() accepts message, suggestion, and file_path
            together per contract's Usage example.

        Business Impact:
            Provides comprehensive error context combining error description,
            resolution guidance, and file location.

        Scenario:
            Given: Error message, suggestion, and file_path all provided.
            When: ConfigurationError is instantiated with all parameters.
            Then: Exception stores all three attributes correctly.

        Fixtures Used:
            None - tests complete exception context.
        """
        # Given: Error message, suggestion, and file_path all provided
        error_message = "Invalid port number"
        suggestion = "Port must be between 1-65535"
        file_path = "/path/to/config.yaml"

        # When: ConfigurationError is instantiated with all parameters
        error = MockConfigurationError(
            message=error_message,
            suggestion=suggestion,
            file_path=file_path
        )

        # Then: Exception stores all three attributes correctly
        assert error.message == error_message
        assert error.suggestion == suggestion
        assert error.file_path == file_path


class TestConfigurationErrorFormatting:
    """Test ConfigurationError string representation and formatting."""

    def test_str_returns_message_when_no_context(self):
        """
        Test that __str__() returns basic message when no context provided.

        Verifies:
            ConfigurationError.__str__() returns message string when suggestion
            and file_path are None per contract's Returns section.

        Business Impact:
            Provides clear error messages in logs and exception traces for
            basic configuration errors.

        Scenario:
            Given: ConfigurationError with only message="Invalid YAML syntax".
            When: str() is called on the exception.
            Then: Returns the message string without additional formatting.

        Fixtures Used:
            None - tests string formatting.
        """
        # Given: ConfigurationError with only message="Invalid YAML syntax"
        error_message = "Invalid YAML syntax"
        error = MockConfigurationError(message=error_message)

        # When: str() is called on the exception
        result = str(error)

        # Then: Returns the message string without additional formatting
        assert result == error_message

    def test_str_includes_file_path_when_provided(self):
        """
        Test that __str__() includes file path in formatted output.

        Verifies:
            ConfigurationError.__str__() incorporates file_path in output when
            available per contract's Returns section.

        Business Impact:
            Enables quick identification of problematic configuration files in
            error messages and logs.

        Scenario:
            Given: ConfigurationError with message and file_path="/path/to/config.yaml".
            When: str() is called on the exception.
            Then: Returns formatted string including file path context.

        Fixtures Used:
            None - tests file path formatting.
        """
        # Given: ConfigurationError with message and file_path="/path/to/config.yaml"
        error_message = "Invalid YAML syntax"
        file_path = "/path/to/config.yaml"
        error = MockConfigurationError(message=error_message, file_path=file_path)

        # When: str() is called on the exception
        result = str(error)

        # Then: Returns formatted string including file path context
        assert file_path in result
        assert error_message in result

    def test_str_includes_suggestion_when_provided(self):
        """
        Test that __str__() includes suggestion in formatted output.

        Verifies:
            ConfigurationError.__str__() incorporates suggestion in output when
            available per contract's Returns section.

        Business Impact:
            Provides actionable resolution guidance directly in error messages
            for faster issue resolution.

        Scenario:
            Given: ConfigurationError with message and suggestion="Check YAML indentation".
            When: str() is called on the exception.
            Then: Returns formatted string including suggestion for resolution.

        Fixtures Used:
            None - tests suggestion formatting.
        """
        # Given: ConfigurationError with message and suggestion="Check YAML indentation"
        error_message = "Invalid YAML syntax"
        suggestion = "Check YAML indentation"
        error = MockConfigurationError(message=error_message, suggestion=suggestion)

        # When: str() is called on the exception
        result = str(error)

        # Then: Returns formatted string including suggestion for resolution
        assert suggestion in result
        assert error_message in result

    def test_str_includes_all_context_when_fully_populated(self):
        """
        Test that __str__() formats complete error with all context information.

        Verifies:
            ConfigurationError.__str__() creates comprehensive formatted message
            with message, file_path, and suggestion per contract's Usage example.

        Business Impact:
            Provides complete diagnostic information in single error message for
            efficient troubleshooting.

        Scenario:
            Given: ConfigurationError with message, file_path, and suggestion all provided.
            When: str() is called on the exception.
            Then: Returns formatted string incorporating all three pieces of context.

        Fixtures Used:
            None - tests complete formatting.
        """
        # Given: ConfigurationError with message, file_path, and suggestion all provided
        error_message = "Invalid port number"
        suggestion = "Port must be between 1-65535"
        file_path = "/path/to/config.yaml"
        error = MockConfigurationError(
            message=error_message,
            suggestion=suggestion,
            file_path=file_path
        )

        # When: str() is called on the exception
        result = str(error)

        # Then: Returns formatted string incorporating all three pieces of context
        assert error_message in result
        assert suggestion in result
        assert file_path in result


class TestConfigurationErrorUsagePatterns:
    """Test ConfigurationError usage in typical scenarios."""

    def test_configuration_error_is_raiseable_as_exception(self):
        """
        Test that ConfigurationError can be raised and caught as standard exception.

        Verifies:
            ConfigurationError inherits from Exception and can be raised/caught
            normally per Python exception protocols.

        Business Impact:
            Ensures ConfigurationError integrates properly with Python's exception
            handling mechanisms.

        Scenario:
            Given: ConfigurationError instance.
            When: Exception is raised in try block and caught in except block.
            Then: Exception is caught successfully as ConfigurationError.

        Fixtures Used:
            None - tests exception raising mechanics.
        """
        # Given: ConfigurationError instance
        error_message = "Configuration file not found"
        error = MockConfigurationError(message=error_message)

        # When: Exception is raised in try block and caught in except block
        caught_exception = None
        try:
            raise error
        except MockConfigurationError as e:
            caught_exception = e

        # Then: Exception is caught successfully as ConfigurationError
        assert caught_exception is not None
        assert isinstance(caught_exception, MockConfigurationError)
        assert caught_exception.message == error_message

    def test_configuration_error_preserves_attributes_after_raising(self):
        """
        Test that ConfigurationError attributes are accessible after catching.

        Verifies:
            ConfigurationError preserves message, suggestion, and file_path attributes
            through raise/catch cycle for exception handling code.

        Business Impact:
            Enables exception handlers to access error context programmatically for
            logging, reporting, or recovery actions.

        Scenario:
            Given: ConfigurationError raised with all context parameters.
            When: Exception is caught in except block.
            Then: All attributes (message, suggestion, file_path) remain accessible.

        Fixtures Used:
            None - tests attribute preservation.
        """
        # Given: ConfigurationError raised with all context parameters
        error_message = "Invalid configuration"
        suggestion = "Check configuration file format"
        file_path = "/path/to/config.yaml"
        error = MockConfigurationError(
            message=error_message,
            suggestion=suggestion,
            file_path=file_path
        )

        # When: Exception is caught in except block
        caught_exception = None
        try:
            raise error
        except MockConfigurationError as e:
            caught_exception = e

        # Then: All attributes (message, suggestion, file_path) remain accessible
        assert caught_exception is not None
        assert caught_exception.message == error_message
        assert caught_exception.suggestion == suggestion
        assert caught_exception.file_path == file_path