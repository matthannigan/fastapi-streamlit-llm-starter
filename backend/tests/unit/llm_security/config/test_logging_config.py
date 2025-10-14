"""
Test suite for LoggingConfig Pydantic model.

Tests verify LoggingConfig initialization and logging settings according to
the public contract defined in config.pyi.
"""

import pytest
from pydantic import ValidationError
from app.infrastructure.security.llm.config import LoggingConfig


class TestLoggingConfigInitialization:
    """Test LoggingConfig model instantiation and defaults."""

    def test_logging_config_initialization_with_defaults(self):
        """
        Test that LoggingConfig initializes with sensible default logging settings.

        Verifies:
            LoggingConfig provides default values for all logging settings per
            contract's Attributes section defaults.

        Business Impact:
            Enables quick logging configuration without specifying all parameters
            for standard operational scenarios.

        Scenario:
            Given: No parameters provided to LoggingConfig.
            When: LoggingConfig instance is created.
            Then: All fields have sensible defaults for logging and auditing.

        Fixtures Used:
            None - tests default initialization.
        """
        # Given: No parameters provided to LoggingConfig
        # When: LoggingConfig instance is created
        config = LoggingConfig()

        # Then: All fields have sensible defaults for logging and auditing
        assert config.enable_scan_logging is True
        assert config.enable_violation_logging is True
        assert config.enable_performance_logging is True
        assert config.log_level == "INFO"
        assert config.log_format == "json"
        assert config.include_scanned_text is False
        assert config.sanitize_pii_in_logs is True
        assert config.log_retention_days == 30

    def test_logging_config_with_scan_logging_enabled(self):
        """
        Test that LoggingConfig accepts scan logging configuration.

        Verifies:
            LoggingConfig stores enable_scan_logging for audit trail management
            per contract's Attributes section.

        Business Impact:
            Enables comprehensive audit trails of all security scan operations for
            compliance and troubleshooting.

        Scenario:
            Given: enable_scan_logging=True.
            When: LoggingConfig is created with scan logging enabled.
            Then: Scan logging setting is stored for audit configuration.

        Fixtures Used:
            None - tests scan logging configuration.
        """
        # Given: enable_scan_logging=True
        # When: LoggingConfig is created with scan logging enabled
        config = LoggingConfig(enable_scan_logging=True)

        # Then: Scan logging setting is stored for audit configuration
        assert config.enable_scan_logging is True
        # Verify other defaults remain unchanged
        assert config.enable_violation_logging is True
        assert config.enable_performance_logging is True

    def test_logging_config_with_violation_logging_enabled(self):
        """
        Test that LoggingConfig accepts violation logging configuration.

        Verifies:
            LoggingConfig stores enable_violation_logging for security event tracking
            per contract's Attributes section.

        Business Impact:
            Enables detailed logging of security violations for incident response
            and analysis.

        Scenario:
            Given: enable_violation_logging=True.
            When: LoggingConfig is created with violation logging enabled.
            Then: Violation logging setting is stored for security tracking.

        Fixtures Used:
            None - tests violation logging configuration.
        """
        # Given: enable_violation_logging=True
        # When: LoggingConfig is created with violation logging enabled
        config = LoggingConfig(enable_violation_logging=True)

        # Then: Violation logging setting is stored for security tracking
        assert config.enable_violation_logging is True
        # Verify other defaults remain unchanged
        assert config.enable_scan_logging is True
        assert config.enable_performance_logging is True

    def test_logging_config_with_performance_logging_enabled(self):
        """
        Test that LoggingConfig accepts performance logging configuration.

        Verifies:
            LoggingConfig stores enable_performance_logging for metrics tracking
            per contract's Attributes section.

        Business Impact:
            Enables performance monitoring through detailed timing and resource
            usage logging.

        Scenario:
            Given: enable_performance_logging=True.
            When: LoggingConfig is created with performance logging enabled.
            Then: Performance logging setting is stored for monitoring.

        Fixtures Used:
            None - tests performance logging configuration.
        """
        # Given: enable_performance_logging=True
        # When: LoggingConfig is created with performance logging enabled
        config = LoggingConfig(enable_performance_logging=True)

        # Then: Performance logging setting is stored for monitoring
        assert config.enable_performance_logging is True
        # Verify other defaults remain unchanged
        assert config.enable_scan_logging is True
        assert config.enable_violation_logging is True

    def test_logging_config_with_log_level_configuration(self):
        """
        Test that LoggingConfig accepts log level configuration.

        Verifies:
            LoggingConfig stores log_level for controlling verbosity per contract's
            Attributes section.

        Business Impact:
            Enables appropriate log verbosity control for different environments
            and debugging scenarios.

        Scenario:
            Given: log_level="DEBUG".
            When: LoggingConfig is created with log level.
            Then: Log level is stored for verbosity control.

        Fixtures Used:
            None - tests log level configuration.
        """
        # Given: log_level="DEBUG"
        # When: LoggingConfig is created with log level
        config = LoggingConfig(log_level="DEBUG")

        # Then: Log level is stored for verbosity control
        assert config.log_level == "DEBUG"
        # Verify other defaults remain unchanged
        assert config.enable_scan_logging is True
        assert config.log_format == "json"

    def test_logging_config_with_json_format(self):
        """
        Test that LoggingConfig accepts JSON log format configuration.

        Verifies:
            LoggingConfig stores log_format for structured logging per contract's
            Attributes section.

        Business Impact:
            Enables structured logging for integration with log aggregation and
            analysis systems.

        Scenario:
            Given: log_format="json".
            When: LoggingConfig is created with JSON format.
            Then: Log format is stored for structured output.

        Fixtures Used:
            None - tests log format configuration.
        """
        # Given: log_format="json"
        # When: LoggingConfig is created with JSON format
        config = LoggingConfig(log_format="json")

        # Then: Log format is stored for structured output
        assert config.log_format == "json"
        # Verify other defaults remain unchanged
        assert config.enable_scan_logging is True
        assert config.log_level == "INFO"

    def test_logging_config_with_scanned_text_inclusion(self):
        """
        Test that LoggingConfig accepts scanned text inclusion configuration.

        Verifies:
            LoggingConfig stores include_scanned_text for content logging per
            contract's Attributes section.

        Business Impact:
            Enables debugging by including actual scanned content in logs when
            appropriate for non-sensitive data.

        Scenario:
            Given: include_scanned_text=True.
            When: LoggingConfig is created with text inclusion enabled.
            Then: Text inclusion setting is stored for debug logging.

        Fixtures Used:
            None - tests text inclusion configuration.
        """
        # Given: include_scanned_text=True
        # When: LoggingConfig is created with text inclusion enabled
        config = LoggingConfig(include_scanned_text=True)

        # Then: Text inclusion setting is stored for debug logging
        assert config.include_scanned_text is True
        # Verify other defaults remain unchanged
        assert config.enable_scan_logging is True
        assert config.sanitize_pii_in_logs is True

    def test_logging_config_with_pii_sanitization(self):
        """
        Test that LoggingConfig accepts PII sanitization configuration.

        Verifies:
            LoggingConfig stores sanitize_pii_in_logs for privacy protection per
            contract's Attributes section.

        Business Impact:
            Enables privacy protection by automatically detecting and masking PII
            in log content for compliance.

        Scenario:
            Given: sanitize_pii_in_logs=True.
            When: LoggingConfig is created with PII sanitization enabled.
            Then: PII sanitization setting is stored for privacy protection.

        Fixtures Used:
            None - tests PII sanitization configuration.
        """
        # Given: sanitize_pii_in_logs=True
        # When: LoggingConfig is created with PII sanitization enabled
        config = LoggingConfig(sanitize_pii_in_logs=True)

        # Then: PII sanitization setting is stored for privacy protection
        assert config.sanitize_pii_in_logs is True
        # Verify other defaults remain unchanged
        assert config.enable_scan_logging is True
        assert config.include_scanned_text is False

    def test_logging_config_with_log_retention_days(self):
        """
        Test that LoggingConfig accepts log retention period configuration.

        Verifies:
            LoggingConfig stores log_retention_days for retention policy per
            contract's Attributes section.

        Business Impact:
            Enables log retention policy enforcement for compliance and storage
            management.

        Scenario:
            Given: log_retention_days=90.
            When: LoggingConfig is created with retention period.
            Then: Retention period is stored for log lifecycle management.

        Fixtures Used:
            None - tests retention configuration.
        """
        # Given: log_retention_days=90
        # When: LoggingConfig is created with retention period
        config = LoggingConfig(log_retention_days=90)

        # Then: Retention period is stored for log lifecycle management
        assert config.log_retention_days == 90
        # Verify other defaults remain unchanged
        assert config.enable_scan_logging is True
        assert config.log_level == "INFO"

    def test_logging_config_validates_invalid_log_level(self):
        """
        Test that LoggingConfig validates log_level against allowed values.

        Verifies:
            LoggingConfig raises ValidationError for invalid log levels per
            contract's validation rules.

        Business Impact:
            Prevents configuration errors that could cause logging failures
            by ensuring only valid log levels are accepted.

        Scenario:
            Given: Invalid log_level="INVALID".
            When: LoggingConfig is created with invalid log level.
            Then: ValidationError is raised with appropriate message.

        Fixtures Used:
            None - tests validation behavior.
        """
        # Given: Invalid log_level="INVALID"
        # When: LoggingConfig is created with invalid log level
        # Then: ValidationError is raised with appropriate message
        with pytest.raises(ValidationError) as exc_info:
            LoggingConfig(log_level="INVALID")

        # Verify error mentions log_level validation
        assert "log_level" in str(exc_info.value)

    def test_logging_config_validates_invalid_log_format(self):
        """
        Test that LoggingConfig validates log_format against allowed values.

        Verifies:
            LoggingConfig raises ValidationError for invalid log formats per
            contract's validation rules.

        Business Impact:
            Prevents configuration errors that could cause logging failures
            by ensuring only supported log formats are accepted.

        Scenario:
            Given: Invalid log_format="xml".
            When: LoggingConfig is created with invalid log format.
            Then: ValidationError is raised with appropriate message.

        Fixtures Used:
            None - tests validation behavior.
        """
        # Given: Invalid log_format="xml"
        # When: LoggingConfig is created with invalid log format
        # Then: ValidationError is raised with appropriate message
        with pytest.raises(ValidationError) as exc_info:
            LoggingConfig(log_format="xml")

        # Verify error mentions log_format validation
        assert "log_format" in str(exc_info.value)

    def test_logging_config_validates_retention_days_bounds(self):
        """
        Test that LoggingConfig validates log_retention_days within allowed range.

        Verifies:
            LoggingConfig raises ValidationError for retention days outside 1-365 range
            per contract's validation rules.

        Business Impact:
            Prevents configuration errors that could cause storage issues
            by ensuring retention periods are within reasonable bounds.

        Scenario:
            Given: Invalid log_retention_days values (0 and 366).
            When: LoggingConfig is created with invalid retention days.
            Then: ValidationError is raised for out-of-bounds values.

        Fixtures Used:
            None - tests validation behavior.
        """
        # Test lower bound violation
        # Given: Invalid log_retention_days=0
        # When: LoggingConfig is created with invalid retention days
        # Then: ValidationError is raised
        with pytest.raises(ValidationError) as exc_info:
            LoggingConfig(log_retention_days=0)

        # Verify error mentions log_retention_days validation
        assert "log_retention_days" in str(exc_info.value)

        # Test upper bound violation
        # Given: Invalid log_retention_days=366
        # When: LoggingConfig is created with invalid retention days
        # Then: ValidationError is raised
        with pytest.raises(ValidationError) as exc_info:
            LoggingConfig(log_retention_days=366)

        # Verify error mentions log_retention_days validation
        assert "log_retention_days" in str(exc_info.value)


class TestLoggingConfigUsagePatterns:
    """Test LoggingConfig usage in typical scenarios."""

    def test_logging_config_for_production_with_privacy(self):
        """
        Test LoggingConfig configuration for production with privacy protection.

        Verifies:
            LoggingConfig supports production logging with privacy controls per
            contract's Usage example for production.

        Business Impact:
            Enables comprehensive production logging while protecting sensitive
            data through PII sanitization.

        Scenario:
            Given: Production logging settings with privacy controls.
            When: LoggingConfig is created for production deployment.
            Then: Configuration supports production logging with privacy protection.

        Fixtures Used:
            None - tests production logging pattern.
        """
        # Given: Production logging settings with privacy controls
        production_settings = {
            "enable_scan_logging": True,
            "enable_violation_logging": True,
            "include_scanned_text": False,  # Privacy-first
            "sanitize_pii_in_logs": True,
            "log_level": "INFO",
            "log_format": "json",
            "log_retention_days": 90
        }

        # When: LoggingConfig is created for production deployment
        config = LoggingConfig(**production_settings)

        # Then: Configuration supports production logging with privacy protection
        assert config.enable_scan_logging is True
        assert config.enable_violation_logging is True
        assert config.include_scanned_text is False  # Privacy protection
        assert config.sanitize_pii_in_logs is True  # PII sanitization
        assert config.log_level == "INFO"
        assert config.log_format == "json"  # Structured logging
        assert config.log_retention_days == 90  # Retention policy

    def test_logging_config_for_development_with_debugging(self):
        """
        Test LoggingConfig configuration for development with detailed debugging.

        Verifies:
            LoggingConfig supports development logging with verbose output per
            contract's Usage example for development.

        Business Impact:
            Enables comprehensive debugging through detailed logging including
            scanned text content.

        Scenario:
            Given: Development logging settings with debug verbosity.
            When: LoggingConfig is created for development environment.
            Then: Configuration supports development debugging requirements.

        Fixtures Used:
            None - tests development logging pattern.
        """
        # Given: Development logging settings with debug verbosity
        development_settings = {
            "enable_performance_logging": True,
            "include_scanned_text": True,  # For debugging
            "log_level": "DEBUG",
            "log_format": "text",
            "log_retention_days": 7
        }

        # When: LoggingConfig is created for development environment
        config = LoggingConfig(**development_settings)

        # Then: Configuration supports development debugging requirements
        assert config.enable_performance_logging is True  # Performance metrics
        assert config.include_scanned_text is True  # Debug content
        assert config.log_level == "DEBUG"  # Verbose logging
        assert config.log_format == "text"  # Readable format
        assert config.log_retention_days == 7  # Short retention
        # Verify other defaults for development
        assert config.enable_scan_logging is True
        assert config.enable_violation_logging is True
        assert config.sanitize_pii_in_logs is True  # Still protect privacy

    def test_logging_config_for_minimal_privacy_sensitive(self):
        """
        Test LoggingConfig configuration for minimal logging in privacy-sensitive environments.

        Verifies:
            LoggingConfig supports minimal logging configuration per contract's
            Usage example for privacy-sensitive scenarios.

        Business Impact:
            Enables essential logging while minimizing data retention for
            privacy-critical deployments.

        Scenario:
            Given: Minimal logging settings with maximum privacy controls.
            When: LoggingConfig is created for privacy-sensitive environment.
            Then: Configuration supports minimal logging with privacy protection.

        Fixtures Used:
            None - tests privacy-sensitive logging pattern.
        """
        # Given: Minimal logging settings with maximum privacy controls
        minimal_settings = {
            "enable_violation_logging": True,  # Keep violations only
            "enable_scan_logging": False,
            "enable_performance_logging": False,
            "sanitize_pii_in_logs": True,
            "log_level": "WARNING",
            "include_scanned_text": False,
            "log_retention_days": 30
        }

        # When: LoggingConfig is created for privacy-sensitive environment
        config = LoggingConfig(**minimal_settings)

        # Then: Configuration supports minimal logging with privacy protection
        assert config.enable_violation_logging is True  # Only essential logs
        assert config.enable_scan_logging is False  # No audit trail
        assert config.enable_performance_logging is False  # No metrics
        assert config.sanitize_pii_in_logs is True  # Maximum privacy
        assert config.log_level == "WARNING"  # Minimal verbosity
        assert config.include_scanned_text is False  # No content logging
        assert config.log_retention_days == 30  # Limited retention