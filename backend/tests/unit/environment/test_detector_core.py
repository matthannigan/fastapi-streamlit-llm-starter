"""
Tests for core EnvironmentDetector functionality.

Tests the primary detection methods including initialization, basic environment
detection, and summary reporting. Covers signal collection, confidence scoring,
fallback behavior, and debugging capabilities.
"""

from unittest.mock import patch

from app.core.environment import (
    Environment,
    FeatureContext,
    EnvironmentInfo,
    DetectionConfig,
    EnvironmentDetector,
)


class TestEnvironmentDetectorInitialization:
    """
    Test suite for EnvironmentDetector initialization and configuration.

    Scope:
        - EnvironmentDetector creation with default and custom configuration
        - Configuration validation and initialization behavior

    Business Critical:
        EnvironmentDetector initialization establishes detection behavior
        for all subsequent environment classification throughout the application
    """

    def test_environment_detector_initializes_with_default_config(self):
        """
        Test that EnvironmentDetector initializes successfully with default configuration.

        Verifies:
            EnvironmentDetector can be created without configuration parameters.

        Business Impact:
            Ensures environment detection works immediately without setup requirements.

        Scenario:
            Given: No configuration parameters
            When: Creating EnvironmentDetector instance
            Then: Detector initializes with default DetectionConfig and empty signal cache

        Fixtures Used:
            - None (testing initialization behavior only)
        """
        # Given: No configuration parameters

        # When: Creating EnvironmentDetector instance
        detector = EnvironmentDetector()

        # Then: Detector initializes with default DetectionConfig and empty signal cache
        assert detector.config is not None
        assert isinstance(detector.config, DetectionConfig)
        assert hasattr(detector, "_signal_cache")
        assert isinstance(detector._signal_cache, dict)
        assert len(detector._signal_cache) == 0

    def test_environment_detector_initializes_with_custom_config(self, custom_detection_config):
        """
        Test that EnvironmentDetector accepts custom DetectionConfig.

        Verifies:
            Custom configuration is stored and used for detection behavior.

        Business Impact:
            Enables specialized deployment scenarios with customized detection logic.

        Scenario:
            Given: Custom DetectionConfig instance with modified patterns
            When: Creating EnvironmentDetector with custom config
            Then: Detector stores custom configuration for subsequent detection operations

        Fixtures Used:
            - custom_detection_config: DetectionConfig with modified patterns and precedence
        """
        # Given: Custom DetectionConfig instance with modified patterns

        # When: Creating EnvironmentDetector with custom config
        detector = EnvironmentDetector(custom_detection_config)

        # Then: Detector stores custom configuration for subsequent detection operations
        assert detector.config is custom_detection_config
        assert detector.config.env_var_precedence == custom_detection_config.env_var_precedence
        assert detector.config.development_patterns == custom_detection_config.development_patterns
        assert detector.config.feature_contexts == custom_detection_config.feature_contexts

    def test_environment_detector_creates_signal_cache(self):
        """
        Test that EnvironmentDetector initializes signal cache for performance.

        Verifies:
            Signal cache is created during initialization for performance optimization.

        Business Impact:
            Ensures repeated detection calls can benefit from caching optimization.

        Scenario:
            Given: EnvironmentDetector initialization
            When: Checking internal state after creation
            Then: Signal cache is initialized as empty dictionary

        Fixtures Used:
            - None (testing initialization state only)
        """
        # Given: EnvironmentDetector initialization

        # When: Checking internal state after creation
        detector = EnvironmentDetector()

        # Then: Signal cache is initialized as empty dictionary
        assert hasattr(detector, "_signal_cache")
        assert isinstance(detector._signal_cache, dict)
        assert len(detector._signal_cache) == 0

    def test_environment_detector_logs_initialization(self, mock_logger):
        """
        Test that EnvironmentDetector logs initialization for monitoring.

        Verifies:
            Initialization events are logged for debugging and monitoring purposes.

        Business Impact:
            Enables tracking of detector creation in production environments.

        Scenario:
            Given: Logger configuration for EnvironmentDetector
            When: Creating EnvironmentDetector instance
            Then: Initialization message is logged with appropriate level

        Fixtures Used:
            - mock_logger: Mocked logger to capture initialization messages
        """
        # Given: Logger configuration for EnvironmentDetector
        # (provided by mock_logger fixture)

        # When: Creating EnvironmentDetector instance
        detector = EnvironmentDetector()

        # Then: Initialization message is logged with appropriate level
        mock_logger.info.assert_called_once_with("Initialized EnvironmentDetector")


class TestEnvironmentDetectorBasicDetection:
    """
    Test suite for basic environment detection without feature contexts.

    Scope:
        - detect_environment() method with default feature context
        - Environment signal collection and confidence scoring
        - Fallback detection when no signals are found

    Business Critical:
        Basic environment detection is used throughout infrastructure services
        for configuration selection and must provide reliable results
    """

    def test_detect_environment_returns_environment_info(self, environment_detector):
        """
        Test that detect_environment returns complete EnvironmentInfo result.

        Verifies:
            detect_environment() returns EnvironmentInfo with all required fields populated.

        Business Impact:
            Ensures all infrastructure services receive complete detection information.

        Scenario:
            Given: EnvironmentDetector instance with default configuration
            When: Calling detect_environment() without parameters
            Then: Returns EnvironmentInfo with environment, confidence, reasoning, and detected_by

        Fixtures Used:
            - environment_detector: EnvironmentDetector with default configuration
        """
        # Given: EnvironmentDetector instance with default configuration
        # (provided by environment_detector fixture)

        # When: Calling detect_environment() without parameters
        result = environment_detector.detect_environment()

        # Then: Returns EnvironmentInfo with environment, confidence, reasoning, and detected_by
        assert isinstance(result, EnvironmentInfo)
        assert isinstance(result.environment, Environment)
        assert isinstance(result.confidence, float)
        assert isinstance(result.reasoning, str)
        assert isinstance(result.detected_by, str)
        assert isinstance(result.feature_context, FeatureContext)
        assert isinstance(result.additional_signals, list)
        assert isinstance(result.metadata, dict)

        # Verify required fields are populated
        assert result.environment is not None
        assert result.confidence is not None
        assert result.reasoning != ""
        assert result.detected_by != ""

    def test_detect_environment_with_explicit_feature_context(self, environment_detector):
        """
        Test that detect_environment accepts feature context parameter.

        Verifies:
            detect_environment() can be called with specific FeatureContext values.

        Business Impact:
            Enables feature-aware detection from primary detection method.

        Scenario:
            Given: EnvironmentDetector instance
            When: Calling detect_environment() with specific FeatureContext
            Then: Returns EnvironmentInfo with feature_context field set to specified context

        Fixtures Used:
            - environment_detector: EnvironmentDetector with default configuration
        """
        # Given: EnvironmentDetector instance
        # (provided by environment_detector fixture)

        # When: Calling detect_environment() with specific FeatureContext
        test_context = FeatureContext.AI_ENABLED
        result = environment_detector.detect_environment(test_context)

        # Then: Returns EnvironmentInfo with feature_context field set to specified context
        assert isinstance(result, EnvironmentInfo)
        assert result.feature_context == test_context

    def test_detect_environment_confidence_within_valid_range(self, environment_detector, mock_environment_conditions):
        """
        Test that detect_environment returns confidence scores in valid range.

        Verifies:
            Confidence scores are always between 0.0 and 1.0 inclusive.

        Business Impact:
            Ensures confidence scores provide meaningful reliability assessment.

        Scenario:
            Given: EnvironmentDetector with various environment conditions
            When: Calling detect_environment() under different scenarios
            Then: All returned confidence scores are between 0.0 and 1.0

        Fixtures Used:
            - environment_detector: EnvironmentDetector with default configuration
            - mock_environment_conditions: Various environment variable and system configurations
        """
        # Given: EnvironmentDetector with various environment conditions
        # Test various environment conditions from fixture
        test_scenarios = [
            mock_environment_conditions["production_explicit"],
            mock_environment_conditions["development_explicit"],
            mock_environment_conditions["node_env_prod"],
            mock_environment_conditions["mixed_signals"]
        ]

        for env_vars in test_scenarios:
            with patch.dict("os.environ", env_vars, clear=True):
                # When: Calling detect_environment() under different scenarios
                result = environment_detector.detect_environment()

                # Then: All returned confidence scores are between 0.0 and 1.0
                assert 0.0 <= result.confidence <= 1.0, f"Confidence {result.confidence} out of range for {env_vars}"

    def test_detect_environment_fallback_when_no_signals(self, environment_detector, clean_environment):
        """
        Test that detect_environment provides fallback when no environment signals found.

        Verifies:
            Detection returns development environment as fallback with appropriate confidence.

        Business Impact:
            Ensures system continues operating even when environment cannot be determined.

        Scenario:
            Given: EnvironmentDetector in environment with no detection signals
            When: Calling detect_environment()
            Then: Returns DEVELOPMENT environment with confidence around 0.5 and fallback reasoning

        Fixtures Used:
            - environment_detector: EnvironmentDetector with default configuration
            - clean_environment: Environment with no detection signals available
        """
        # Given: EnvironmentDetector in environment with no detection signals
        # (clean_environment fixture provides this context)

        # When: Calling detect_environment()
        result = environment_detector.detect_environment()

        # Then: Returns DEVELOPMENT environment with confidence around 0.5 and fallback reasoning
        assert result.environment == Environment.DEVELOPMENT
        assert result.confidence == 0.5
        assert "fallback" in result.reasoning.lower() or "no environment signals" in result.reasoning.lower()
        assert result.detected_by == "fallback"

    def test_detect_environment_includes_reasoning(self, environment_detector):
        """
        Test that detect_environment provides human-readable reasoning.

        Verifies:
            Detection results include clear explanation of how environment was determined.

        Business Impact:
            Enables debugging and validation of environment detection decisions.

        Scenario:
            Given: EnvironmentDetector with identifiable environment signals
            When: Calling detect_environment()
            Then: Returns EnvironmentInfo with reasoning field explaining detection logic

        Fixtures Used:
            - environment_detector: EnvironmentDetector with default configuration
            - mock_environment_signal: Known environment condition for predictable detection
        """
        # Given: EnvironmentDetector with identifiable environment signals
        with patch.dict("os.environ", {"ENVIRONMENT": "production"}, clear=True):
            # When: Calling detect_environment()
            result = environment_detector.detect_environment()

            # Then: Returns EnvironmentInfo with reasoning field explaining detection logic
            assert isinstance(result.reasoning, str)
            assert len(result.reasoning) > 0
            assert "environment" in result.reasoning.lower() or "production" in result.reasoning.lower()
            # Reasoning should be human-readable and explain the detection
            assert result.reasoning != ""

    def test_detect_environment_includes_detected_by_source(self, environment_detector):
        """
        Test that detect_environment identifies primary detection mechanism.

        Verifies:
            Detection results include detected_by field identifying signal source.

        Business Impact:
            Enables analysis of detection reliability and signal source effectiveness.

        Scenario:
            Given: EnvironmentDetector with known environment signal
            When: Calling detect_environment()
            Then: Returns EnvironmentInfo with detected_by field identifying signal source

        Fixtures Used:
            - environment_detector: EnvironmentDetector with default configuration
            - mock_primary_signal: Known environment signal with identifiable source
        """
        # Given: EnvironmentDetector with known environment signal
        with patch.dict("os.environ", {"ENVIRONMENT": "development"}, clear=True):
            # When: Calling detect_environment()
            result = environment_detector.detect_environment()

            # Then: Returns EnvironmentInfo with detected_by field identifying signal source
            assert isinstance(result.detected_by, str)
            assert len(result.detected_by) > 0
            # Should identify the primary signal source
            assert result.detected_by == "ENVIRONMENT"


class TestEnvironmentDetectorSummaryReporting:
    """
    Test suite for environment detection summary and debugging capabilities.

    Scope:
        - get_environment_summary() method comprehensive reporting
        - Signal collection and formatting for analysis
        - Debugging information for low-confidence detection

    Business Critical:
        Detection summary enables debugging and monitoring of environment
        classification in production systems for reliability assurance
    """

    def test_get_environment_summary_returns_complete_structure(self, environment_detector):
        """
        Test that get_environment_summary returns comprehensive detection information.

        Verifies:
            Summary includes all documented fields for complete detection analysis.

        Business Impact:
            Enables comprehensive debugging and monitoring of detection behavior.

        Scenario:
            Given: EnvironmentDetector with detectable environment signals
            When: Calling get_environment_summary()
            Then: Returns dictionary with detected_environment, confidence, reasoning,
                  detected_by, all_signals, and metadata

        Fixtures Used:
            - environment_detector: EnvironmentDetector with default configuration
            - mock_environment_signals: Environment with multiple detection signals
        """
        # Given: EnvironmentDetector with detectable environment signals
        with patch.dict("os.environ", {"ENVIRONMENT": "production"}, clear=True):
            # When: Calling get_environment_summary()
            summary = environment_detector.get_environment_summary()

            # Then: Returns dictionary with all required fields
            assert isinstance(summary, dict)

            # Verify all required fields are present
            required_fields = ["detected_environment", "confidence", "reasoning", "detected_by", "all_signals", "metadata"]
            for field in required_fields:
                assert field in summary, f"Missing required field: {field}"

            # Verify field types
            assert isinstance(summary["detected_environment"], str)
            assert isinstance(summary["confidence"], float)
            assert isinstance(summary["reasoning"], str)
            assert isinstance(summary["detected_by"], str)
            assert isinstance(summary["all_signals"], list)
            assert isinstance(summary["metadata"], dict)

    def test_get_environment_summary_formats_signals_for_analysis(self, environment_detector):
        """
        Test that get_environment_summary formats signals for human analysis.

        Verifies:
            All collected signals are formatted with source, value, confidence, and reasoning.

        Business Impact:
            Enables detailed analysis of detection logic and signal effectiveness.

        Scenario:
            Given: EnvironmentDetector with multiple environment signals
            When: Calling get_environment_summary()
            Then: all_signals list contains formatted signal information for analysis

        Fixtures Used:
            - environment_detector: EnvironmentDetector with default configuration
            - mock_multiple_signals: Environment with various types of detection signals
        """
        # Given: EnvironmentDetector with multiple environment signals
        with patch.dict("os.environ", {"ENVIRONMENT": "production", "NODE_ENV": "production"}, clear=True):
            # When: Calling get_environment_summary()
            summary = environment_detector.get_environment_summary()

            # Then: all_signals list contains formatted signal information for analysis
            signals = summary["all_signals"]
            assert isinstance(signals, list)

            if signals:  # If signals were detected
                for signal in signals:
                    assert isinstance(signal, dict)
                    # Verify signal has required format fields
                    required_signal_fields = ["source", "value", "environment", "confidence", "reasoning"]
                    for field in required_signal_fields:
                        assert field in signal, f"Signal missing field: {field}"

                    # Verify field types
                    assert isinstance(signal["source"], str)
                    assert isinstance(signal["value"], str)
                    assert isinstance(signal["environment"], str)
                    assert isinstance(signal["confidence"], float)
                    assert isinstance(signal["reasoning"], str)

    def test_get_environment_summary_includes_confidence_details(self, environment_detector):
        """
        Test that get_environment_summary includes detailed confidence information.

        Verifies:
            Summary provides confidence score and explanation of confidence calculation.

        Business Impact:
            Enables assessment of detection reliability in production environments.

        Scenario:
            Given: EnvironmentDetector with varying confidence signals
            When: Calling get_environment_summary()
            Then: Returns confidence score and reasoning explaining confidence assessment

        Fixtures Used:
            - environment_detector: EnvironmentDetector with default configuration
            - mock_confidence_scenarios: Environment conditions producing different confidence levels
        """
        # Given: EnvironmentDetector with varying confidence signals
        test_scenarios = [
            {"ENVIRONMENT": "production"},  # High confidence
            {"NODE_ENV": "development"},    # Medium confidence
            {}                              # Low confidence (fallback)
        ]

        for env_vars in test_scenarios:
            with patch.dict("os.environ", env_vars, clear=True):
                # When: Calling get_environment_summary()
                summary = environment_detector.get_environment_summary()

                # Then: Returns confidence score and reasoning explaining confidence assessment
                assert "confidence" in summary
                assert isinstance(summary["confidence"], float)
                assert 0.0 <= summary["confidence"] <= 1.0

                assert "reasoning" in summary
                assert isinstance(summary["reasoning"], str)
                assert len(summary["reasoning"]) > 0

    def test_get_environment_summary_preserves_signal_confidence_scores(self, environment_detector):
        """
        Test that get_environment_summary preserves original signal confidence scores.

        Verifies:
            Individual signal confidence scores are maintained in summary output.

        Business Impact:
            Enables analysis of signal reliability and detection accuracy.

        Scenario:
            Given: EnvironmentDetector with signals having known confidence scores
            When: Calling get_environment_summary()
            Then: all_signals preserve original confidence values for each signal

        Fixtures Used:
            - environment_detector: EnvironmentDetector with default configuration
            - mock_known_confidence_signals: Environment signals with predetermined confidence scores
        """
        # Given: EnvironmentDetector with signals having known confidence scores
        with patch.dict("os.environ", {"ENVIRONMENT": "production"}, clear=True):
            # When: Calling get_environment_summary()
            summary = environment_detector.get_environment_summary()

            # Then: all_signals preserve original confidence values for each signal
            signals = summary["all_signals"]
            if signals:  # If signals were detected
                for signal in signals:
                    assert "confidence" in signal
                    assert isinstance(signal["confidence"], float)
                    assert 0.0 <= signal["confidence"] <= 1.0

                    # Confidence should be preserved from original signal
                    # High confidence for ENVIRONMENT variable should be around 0.95
                    if signal["source"] == "ENVIRONMENT":
                        assert signal["confidence"] >= 0.90

    def test_get_environment_summary_uses_default_context(self, environment_detector):
        """
        Test that get_environment_summary uses DEFAULT feature context for detection.

        Verifies:
            Summary generation uses standard detection without feature-specific overrides.

        Business Impact:
            Ensures summary represents baseline detection behavior for general analysis.

        Scenario:
            Given: EnvironmentDetector instance
            When: Calling get_environment_summary()
            Then: Uses FeatureContext.DEFAULT for environment detection

        Fixtures Used:
            - environment_detector: EnvironmentDetector with default configuration
        """
        # Given: EnvironmentDetector instance
        # (provided by environment_detector fixture)

        # When: Calling get_environment_summary()
        summary = environment_detector.get_environment_summary()

        # Then: Uses FeatureContext.DEFAULT for environment detection
        # We can verify this by checking that no feature-specific metadata is present
        metadata = summary.get("metadata", {})

        # Default context should not have feature-specific keys
        feature_specific_keys = ["ai_prefix", "enable_ai_cache_enabled", "enforce_auth_enabled"]
        for key in feature_specific_keys:
            assert key not in metadata, f"Found feature-specific key '{key}' in default context summary"

        # Verify this is behaving like default context by comparing with explicit call
        default_env_info = environment_detector.detect_environment(FeatureContext.DEFAULT)
        assert summary["detected_environment"] == default_env_info.environment.value
        assert summary["confidence"] == default_env_info.confidence
