"""
Test suite for ScannerConfig Pydantic model.

Tests verify ScannerConfig initialization, validation, and methods according to
the public contract defined in config.pyi.
"""

import pytest

# Import the actual implementation and exceptions
from app.infrastructure.security.llm.config import ScannerConfig, ViolationAction
from pydantic import ValidationError


class TestScannerConfigInitialization:
    """Test ScannerConfig model instantiation and defaults."""

    def test_scanner_config_initialization_with_defaults(self):
        """
        Test that ScannerConfig initializes with sensible default values.

        Verifies:
            ScannerConfig provides default values for all fields per contract's
            Attributes section with defaults.

        Business Impact:
            Enables quick scanner configuration without specifying all parameters
            for rapid deployment.

        Scenario:
            Given: No parameters provided to ScannerConfig.
            When: ScannerConfig instance is created.
            Then: All fields have sensible defaults (enabled=True, threshold=0.7, etc.).

        Fixtures Used:
            None - tests default initialization.
        """
        # When: ScannerConfig instance is created with no parameters
        config = ScannerConfig()

        # Then: All fields have sensible defaults
        assert config.enabled is True
        assert config.threshold == 0.7
        assert config.action == ViolationAction.BLOCK
        assert config.model_name is None
        assert config.model_params == {}
        assert config.scan_timeout == 30
        assert config.enabled_violation_types == []
        assert config.metadata == {}

    def test_scanner_config_initialization_with_custom_values(self, violation_action):
        """
        Test that ScannerConfig accepts custom values for all fields.

        Verifies:
            ScannerConfig.__init__() accepts all documented parameters and stores
            them correctly per contract's Attributes section.

        Business Impact:
            Enables complete scanner customization for specific security requirements
            and operational constraints.

        Scenario:
            Given: Custom values for enabled, threshold, action, model_name, etc.
            When: ScannerConfig is instantiated with all parameters.
            Then: Instance stores all custom values correctly.

        Fixtures Used:
            - violation_action: Fixture providing MockViolationAction instance.
        """
        # Given: Custom values for all fields
        custom_params = {
            "enabled": False,
            "threshold": 0.85,
            "action": violation_action.WARN,
            "model_name": "custom-test-model-v1",
            "model_params": {"language": "en", "context_window": 1024},
            "scan_timeout": 120,
            "enabled_violation_types": ["harassment", "hate_speech"],
            "metadata": {"version": "1.0", "region": "us-east-1"}
        }

        # When: ScannerConfig is instantiated with custom parameters
        config = ScannerConfig(**custom_params)

        # Then: Instance stores all custom values correctly
        assert config.enabled is False
        assert config.threshold == 0.85
        assert config.action == violation_action.WARN
        assert config.model_name == "custom-test-model-v1"
        assert config.model_params == {"language": "en", "context_window": 1024}
        assert config.scan_timeout == 120
        assert config.enabled_violation_types == ["harassment", "hate_speech"]
        assert config.metadata == {"version": "1.0", "region": "us-east-1"}

    def test_scanner_config_with_model_configuration(self):
        """
        Test that ScannerConfig accepts model name and parameters for custom models.

        Verifies:
            ScannerConfig stores model_name and model_params for ML model selection
            per contract's Attributes section.

        Business Impact:
            Enables custom model selection and parameter tuning for advanced
            security scanning scenarios.

        Scenario:
            Given: model_name="custom-toxicity-v2" and model_params dictionary.
            When: ScannerConfig is created with model configuration.
            Then: Model name and parameters are stored for scanner use.

        Fixtures Used:
            None - tests model configuration storage.
        """
        # Given: model_name and model_params for custom model
        model_name = "custom-toxicity-v2"
        model_params = {
            "language": "en",
            "context_window": 512,
            "threshold_adjustment": 0.1,
            "specialized_detection": True
        }

        # When: ScannerConfig is created with model configuration
        config = ScannerConfig(
            model_name=model_name,
            model_params=model_params
        )

        # Then: Model name and parameters are stored correctly
        assert config.model_name == model_name
        assert config.model_params == model_params

    def test_scanner_config_with_enabled_violation_types(self):
        """
        Test that ScannerConfig accepts list of enabled violation types.

        Verifies:
            ScannerConfig stores enabled_violation_types list for fine-grained
            control per contract's Attributes section.

        Business Impact:
            Enables selective violation detection where scanners only check
            specific violation categories.

        Scenario:
            Given: enabled_violation_types=["harassment", "hate_speech"].
            When: ScannerConfig is created with violation type list.
            Then: List is stored for violation type filtering.

        Fixtures Used:
            None - tests violation type list storage.
        """
        # Given: List of specific violation types
        violation_types = ["harassment", "hate_speech", "violence"]

        # When: ScannerConfig is created with violation type list
        config = ScannerConfig(enabled_violation_types=violation_types)

        # Then: List is stored for violation type filtering
        assert config.enabled_violation_types == violation_types

    def test_scanner_config_with_metadata(self):
        """
        Test that ScannerConfig accepts additional metadata dictionary.

        Verifies:
            ScannerConfig stores metadata dictionary for operational data per
            contract's Attributes section.

        Business Impact:
            Enables storing scanner-specific operational metadata without
            modifying core configuration structure.

        Scenario:
            Given: metadata={"version": "1.0", "region": "us-east-1"}.
            When: ScannerConfig is created with metadata.
            Then: Metadata dictionary is stored for scanner use.

        Fixtures Used:
            None - tests metadata storage.
        """
        # Given: Metadata dictionary with operational data
        metadata = {
            "version": "1.0",
            "region": "us-east-1",
            "deployment": "production",
            "last_updated": "2024-01-15T10:30:00Z"
        }

        # When: ScannerConfig is created with metadata
        config = ScannerConfig(metadata=metadata)

        # Then: Metadata dictionary is stored for scanner use
        assert config.metadata == metadata


class TestScannerConfigValidation:
    """Test ScannerConfig Pydantic validation rules."""

    def test_scanner_config_validates_threshold_range_minimum(self):
        """
        Test that ScannerConfig validates threshold minimum boundary (0.0).

        Verifies:
            validate_threshold() raises ValidationError when threshold < 0.0 per
            contract's Raises section.

        Business Impact:
            Prevents invalid threshold configuration that could cause detection
            errors or unexpected scanner behavior.

        Scenario:
            Given: threshold=-0.1 (below minimum).
            When: ScannerConfig instantiation is attempted.
            Then: ValidationError is raised indicating threshold outside valid range.

        Fixtures Used:
            None - tests validation with invalid input.
        """
        # Given: threshold below minimum (0.0)
        invalid_threshold = -0.1

        # When: ScannerConfig instantiation is attempted
        # Then: ValidationError is raised indicating threshold outside valid range
        with pytest.raises(ValidationError) as exc_info:
            ScannerConfig(threshold=invalid_threshold)

        # Verify the error message indicates threshold validation failed
        error_message = str(exc_info.value)
        assert "Input should be greater than or equal to 0" in error_message
        assert "threshold" in error_message

    def test_scanner_config_validates_threshold_range_maximum(self):
        """
        Test that ScannerConfig validates threshold maximum boundary (1.0).

        Verifies:
            validate_threshold() raises ValidationError when threshold > 1.0 per
            contract's Raises section.

        Business Impact:
            Prevents invalid threshold configuration that could cause mathematical
            errors in detection algorithms.

        Scenario:
            Given: threshold=1.5 (above maximum).
            When: ScannerConfig instantiation is attempted.
            Then: ValidationError is raised indicating threshold outside valid range.

        Fixtures Used:
            None - tests validation with invalid input.
        """
        # Given: threshold above maximum (1.0)
        invalid_threshold = 1.5

        # When: ScannerConfig instantiation is attempted
        # Then: ValidationError is raised indicating threshold outside valid range
        with pytest.raises(ValidationError) as exc_info:
            ScannerConfig(threshold=invalid_threshold)

        # Verify the error message indicates threshold validation failed
        error_message = str(exc_info.value)
        assert "Input should be less than or equal to 1" in error_message
        assert "threshold" in error_message

    def test_scanner_config_accepts_threshold_at_boundaries(self):
        """
        Test that ScannerConfig accepts threshold values at valid boundaries.

        Verifies:
            validate_threshold() accepts 0.0 and 1.0 as valid boundary values
            per contract's Behavior section.

        Business Impact:
            Enables extreme threshold configurations (all detection or no detection)
            for special security scenarios.

        Scenario:
            Given: threshold=0.0 and threshold=1.0 (valid boundaries).
            When: ScannerConfig is instantiated with boundary values.
            Then: Configuration is created successfully without validation errors.

        Fixtures Used:
            None - tests boundary value acceptance.
        """
        # Given: threshold at valid boundaries
        lower_boundary = 0.0
        upper_boundary = 1.0

        # When: ScannerConfig is instantiated with boundary values
        # Then: Configuration is created successfully without validation errors
        config_lower = ScannerConfig(threshold=lower_boundary)
        config_upper = ScannerConfig(threshold=upper_boundary)

        # Verify the configurations are created with correct values
        assert config_lower.threshold == lower_boundary
        assert config_upper.threshold == upper_boundary

    def test_scanner_config_validates_scan_timeout_minimum(self):
        """
        Test that ScannerConfig validates scan timeout minimum boundary (1 second).

        Verifies:
            validate_scan_timeout() raises ValidationError when timeout < 1 per
            contract's Raises section.

        Business Impact:
            Prevents excessively short timeouts that could cause false negatives
            in security scanning.

        Scenario:
            Given: scan_timeout=0 (below minimum).
            When: ScannerConfig instantiation is attempted.
            Then: ValidationError is raised indicating timeout below operational minimum.

        Fixtures Used:
            None - tests validation with invalid input.
        """
        # Given: scan_timeout below minimum (1 second)
        invalid_timeout = 0

        # When: ScannerConfig instantiation is attempted
        # Then: ValidationError is raised indicating timeout below operational minimum
        with pytest.raises(ValidationError) as exc_info:
            ScannerConfig(scan_timeout=invalid_timeout)

        # Verify the error message indicates timeout validation failed
        error_message = str(exc_info.value)
        assert "Input should be greater than or equal to 1" in error_message
        assert "scan_timeout" in error_message

    def test_scanner_config_validates_scan_timeout_maximum(self):
        """
        Test that ScannerConfig validates scan timeout maximum boundary (5 minutes).

        Verifies:
            validate_scan_timeout() raises ValidationError when timeout > 300 per
            contract's Raises section.

        Business Impact:
            Prevents excessively long timeouts that could impact system performance
            and responsiveness.

        Scenario:
            Given: scan_timeout=400 (above maximum 300 seconds).
            When: ScannerConfig instantiation is attempted.
            Then: ValidationError is raised indicating timeout exceeds operational limit.

        Fixtures Used:
            None - tests validation with invalid input.
        """
        # Given: scan_timeout above maximum (300 seconds)
        invalid_timeout = 400

        # When: ScannerConfig instantiation is attempted
        # Then: ValidationError is raised indicating timeout exceeds operational limit
        with pytest.raises(ValidationError) as exc_info:
            ScannerConfig(scan_timeout=invalid_timeout)

        # Verify the error message indicates timeout validation failed
        error_message = str(exc_info.value)
        assert "Input should be less than or equal to 300" in error_message
        assert "scan_timeout" in error_message


class TestScannerConfigMethods:
    """Test ScannerConfig public methods."""

    def test_get_effective_threshold_returns_configured_value(self):
        """
        Test that get_effective_threshold() returns the configured threshold value.

        Verifies:
            get_effective_threshold() returns threshold attribute per contract's
            Returns section.

        Business Impact:
            Provides clear API for accessing effective threshold used by scanner
            for detection decisions.

        Scenario:
            Given: ScannerConfig with threshold=0.75.
            When: get_effective_threshold() is called.
            Then: Returns 0.75 as the effective detection threshold.

        Fixtures Used:
            None - tests threshold accessor method.
        """
        # Given: ScannerConfig with specific threshold
        threshold_value = 0.75
        config = ScannerConfig(threshold=threshold_value)

        # When: get_effective_threshold() is called
        effective_threshold = config.get_effective_threshold()

        # Then: Returns the configured threshold value
        assert effective_threshold == threshold_value

    def test_is_violation_type_enabled_returns_true_when_list_empty(self):
        """
        Test that is_violation_type_enabled() returns True for all types when list empty.

        Verifies:
            is_violation_type_enabled() returns True for any violation type when
            enabled_violation_types is empty per contract's Behavior section.

        Business Impact:
            Enables all violation detection by default without explicit configuration
            of each violation type.

        Scenario:
            Given: ScannerConfig with enabled_violation_types=[].
            When: is_violation_type_enabled("harassment") is called.
            Then: Returns True indicating all violation types are enabled.

        Fixtures Used:
            None - tests default violation type enabling.
        """
        # Given: ScannerConfig with empty enabled_violation_types list
        config = ScannerConfig(enabled_violation_types=[])

        # When: is_violation_type_enabled() is called with various violation types
        # Then: Returns True for all violation types (all enabled by default)
        assert config.is_violation_type_enabled("harassment") is True
        assert config.is_violation_type_enabled("hate_speech") is True
        assert config.is_violation_type_enabled("violence") is True
        assert config.is_violation_type_enabled("any_violation_type") is True

    def test_is_violation_type_enabled_returns_true_for_listed_types(self):
        """
        Test that is_violation_type_enabled() returns True for explicitly listed types.

        Verifies:
            is_violation_type_enabled() returns True only for types in
            enabled_violation_types list per contract's Behavior section.

        Business Impact:
            Enables selective violation detection for focused security scanning
            without processing unnecessary violation categories.

        Scenario:
            Given: ScannerConfig with enabled_violation_types=["harassment"].
            When: is_violation_type_enabled("harassment") is called.
            Then: Returns True for listed violation type.

        Fixtures Used:
            None - tests explicit violation type enabling.
        """
        # Given: ScannerConfig with specific violation types enabled
        enabled_types = ["harassment", "hate_speech"]
        config = ScannerConfig(enabled_violation_types=enabled_types)

        # When: is_violation_type_enabled() is called for listed types
        # Then: Returns True for explicitly listed violation types
        assert config.is_violation_type_enabled("harassment") is True
        assert config.is_violation_type_enabled("hate_speech") is True

    def test_is_violation_type_enabled_returns_false_for_unlisted_types(self):
        """
        Test that is_violation_type_enabled() returns False for types not in list.

        Verifies:
            is_violation_type_enabled() returns False when violation type not in
            enabled_violation_types list per contract's Examples section.

        Business Impact:
            Prevents unnecessary violation processing for disabled violation
            categories, optimizing scanner performance.

        Scenario:
            Given: ScannerConfig with enabled_violation_types=["harassment"].
            When: is_violation_type_enabled("hate_speech") is called.
            Then: Returns False for unlisted violation type.

        Fixtures Used:
            None - tests violation type filtering.
        """
        # Given: ScannerConfig with specific violation types enabled
        enabled_types = ["harassment", "hate_speech"]
        config = ScannerConfig(enabled_violation_types=enabled_types)

        # When: is_violation_type_enabled() is called for unlisted types
        # Then: Returns False for violation types not in the list
        assert config.is_violation_type_enabled("violence") is False
        assert config.is_violation_type_enabled("spam") is False
        assert config.is_violation_type_enabled("any_other_type") is False

    def test_is_violation_type_enabled_is_case_sensitive(self):
        """
        Test that is_violation_type_enabled() performs case-sensitive matching.

        Verifies:
            is_violation_type_enabled() uses case-sensitive string matching per
            contract's Behavior section.

        Business Impact:
            Ensures consistent violation type naming across configuration and
            code for reliable filtering.

        Scenario:
            Given: ScannerConfig with enabled_violation_types=["harassment"].
            When: is_violation_type_enabled("Harassment") is called (different case).
            Then: Returns False due to case mismatch.

        Fixtures Used:
            None - tests case sensitivity.
        """
        # Given: ScannerConfig with lowercase violation types enabled
        enabled_types = ["harassment", "hate_speech"]
        config = ScannerConfig(enabled_violation_types=enabled_types)

        # When: is_violation_type_enabled() is called with different cases
        # Then: Returns False due to case-sensitive matching
        assert config.is_violation_type_enabled("Harassment") is False  # Different case
        assert config.is_violation_type_enabled("HARASSMENT") is False  # Different case
        assert config.is_violation_type_enabled("hate_speech") is True   # Exact match
        assert config.is_violation_type_enabled("HATE_SPEECH") is False  # Different case