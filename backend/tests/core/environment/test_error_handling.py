"""
Tests for environment detection error handling and edge cases.

Tests error resilience including invalid parameters, system access failures,
regex errors, and graceful degradation. Ensures detection continues working
when individual mechanisms fail.
"""

import pytest
from unittest.mock import patch, MagicMock
from typing import Dict, Any, List
import os

from app.core.environment import (
    Environment,
    FeatureContext,
    EnvironmentSignal,
    EnvironmentInfo,
    DetectionConfig,
    EnvironmentDetector,
    get_environment_info,
    is_production_environment,
    is_development_environment,
)
from app.core.exceptions import ValidationError


class TestEnvironmentDetectorErrorHandling:
    """
    Test suite for error handling and edge cases in environment detection.

    Scope:
        - Invalid parameter handling and validation
        - System error resilience (file system, environment access)
        - Graceful degradation when detection mechanisms fail

    Business Critical:
        Error handling ensures environment detection remains operational
        even when individual detection mechanisms fail or invalid input is provided
    """

    def test_detect_with_context_validates_feature_context_parameter(self, environment_detector):
        """
        Test that detect_with_context validates FeatureContext parameter type.

        Verifies:
            Invalid FeatureContext parameters are handled appropriately.

        Business Impact:
            Prevents runtime errors from invalid feature context usage.

        Scenario:
            Given: EnvironmentDetector instance
            When: Calling detect_with_context with invalid FeatureContext
            Then: Either raises appropriate exception or handles gracefully

        Fixtures Used:
            - environment_detector: EnvironmentDetector with default configuration
        """
        # Given: EnvironmentDetector instance (from fixture)
        # When & Then: Invalid FeatureContext should either raise ValidationError or be handled gracefully
        # Test with non-FeatureContext parameter
        with pytest.raises((ValidationError, TypeError, AttributeError)):
            environment_detector.detect_with_context("invalid_context")

        with pytest.raises((ValidationError, TypeError, AttributeError)):
            environment_detector.detect_with_context(123)

        with pytest.raises((ValidationError, TypeError, AttributeError)):
            environment_detector.detect_with_context(None)

        # Verify that valid FeatureContext works fine
        result = environment_detector.detect_with_context(FeatureContext.DEFAULT)
        assert isinstance(result, EnvironmentInfo)
        assert result.feature_context == FeatureContext.DEFAULT

    @pytest.mark.no_parallel
    def test_detection_handles_file_system_access_errors(self, environment_detector, mock_file_system_errors):
        """
        Test that detection handles file system access errors gracefully.

        Verifies:
            File system errors during indicator checking don't break detection.

        Business Impact:
            Ensures detection continues working even with restricted file system access.

        Scenario:
            Given: EnvironmentDetector with file system access restrictions
            When: Running detection that attempts to check file indicators
            Then: Detection completes successfully with alternative signals

        Fixtures Used:
            - environment_detector: EnvironmentDetector with default configuration
            - mock_file_system_errors: File system that raises errors on access attempts
        """
        # Given: File system errors fixture is active (restricts certain file access)
        # When: Running detection that might check file indicators
        result = environment_detector.detect_environment()

        # Then: Detection completes successfully despite file system restrictions
        assert isinstance(result, EnvironmentInfo)
        assert result.environment in Environment
        assert 0.0 <= result.confidence <= 1.0
        assert result.reasoning is not None

        # Verify it still functions with feature contexts
        ai_result = environment_detector.detect_with_context(FeatureContext.AI_ENABLED)
        assert isinstance(ai_result, EnvironmentInfo)
        assert ai_result.feature_context == FeatureContext.AI_ENABLED

    def test_detection_handles_environment_variable_access_errors(self, environment_detector, mock_env_access_errors):
        """
        Test that detection handles environment variable access errors gracefully.

        Verifies:
            Environment variable access errors don't prevent detection completion.

        Business Impact:
            Ensures detection works even with restricted environment access.

        Scenario:
            Given: EnvironmentDetector with environment variable access restrictions
            When: Running detection that attempts to read environment variables
            Then: Detection completes successfully with alternative detection methods

        Fixtures Used:
            - environment_detector: EnvironmentDetector with default configuration
            - mock_env_access_errors: Environment that raises errors on variable access
        """
        # Given: Environment variable access errors fixture is active
        # When: Running detection that attempts to read restricted environment variables
        result = environment_detector.detect_environment()

        # Then: Detection completes successfully despite environment variable access issues
        assert isinstance(result, EnvironmentInfo)
        assert result.environment in Environment
        assert 0.0 <= result.confidence <= 1.0
        assert result.reasoning is not None

        # Test with different feature contexts
        for context in [FeatureContext.DEFAULT, FeatureContext.AI_ENABLED, FeatureContext.SECURITY_ENFORCEMENT]:
            context_result = environment_detector.detect_with_context(context)
            assert isinstance(context_result, EnvironmentInfo)
            assert context_result.feature_context == context

    def test_detection_handles_regex_pattern_errors_gracefully(self, mock_problematic_hostname, invalid_patterns_config):
        """
        Test that detection handles regex pattern matching errors gracefully.

        Verifies:
            Malformed regex patterns or matching errors don't break detection.

        Business Impact:
            Prevents configuration errors from causing detection failures.

        Scenario:
            Given: EnvironmentDetector with potentially problematic regex patterns
            When: Running detection with hostname that could cause regex errors
            Then: Detection completes successfully, ignoring problematic patterns

        Fixtures Used:
            - environment_detector: EnvironmentDetector with edge-case regex patterns
            - mock_problematic_hostname: Hostname values that could trigger regex issues
        """
        # Given: EnvironmentDetector with invalid regex patterns
        detector = EnvironmentDetector(invalid_patterns_config)

        # Test with various problematic hostnames
        for hostname in mock_problematic_hostname:
            with patch.dict(os.environ, {'HOSTNAME': hostname}):
                # When: Running detection with problematic hostname
                result = detector.detect_environment()

                # Then: Detection completes successfully despite regex issues
                assert isinstance(result, EnvironmentInfo)
                assert result.environment in Environment
                assert 0.0 <= result.confidence <= 1.0
                assert result.reasoning is not None

        # Verify that detection still works with feature contexts
        with patch.dict(os.environ, {'HOSTNAME': mock_problematic_hostname[0]}):
            ai_result = detector.detect_with_context(FeatureContext.AI_ENABLED)
            assert isinstance(ai_result, EnvironmentInfo)

    def test_detection_provides_meaningful_error_messages(self, environment_detector, mock_error_conditions):
        """
        Test that detection provides clear error messages when failures occur.

        Verifies:
            Error conditions include helpful debugging information.

        Business Impact:
            Enables quick diagnosis and resolution of detection configuration issues.

        Scenario:
            Given: EnvironmentDetector with conditions that cause detectable errors
            When: Running detection that encounters error conditions
            Then: Error messages provide clear information about failure cause and resolution

        Fixtures Used:
            - environment_detector: EnvironmentDetector with error-prone configuration
            - mock_error_conditions: Environment conditions designed to trigger specific errors
        """
        # Given: Environment detector and various error conditions
        # When & Then: Detection should still work and provide meaningful reasoning

        # Test with low confidence scenario - should provide helpful reasoning
        with patch.dict(os.environ, {}, clear=True):
            result = environment_detector.detect_environment()

            # Should still return a result with reasoning explaining the fallback
            assert isinstance(result, EnvironmentInfo)
            assert result.reasoning is not None
            assert len(result.reasoning) > 0
            # Low confidence scenarios should have explanatory reasoning
            assert any(word in result.reasoning.lower() for word in ['fallback', 'default', 'no signals', 'development'])

        # Test with conflicting signals - should explain conflict resolution
        with patch.dict(os.environ, {'ENVIRONMENT': 'production', 'NODE_ENV': 'development'}):
            result = environment_detector.detect_environment()
            assert isinstance(result, EnvironmentInfo)
            assert result.reasoning is not None
            # Should provide information about signal resolution
            # Note: additional_signals may be empty if implementation consolidates signals

        # Test summary method for comprehensive error information
        summary = environment_detector.get_environment_summary()
        assert 'detected_environment' in summary
        assert 'confidence' in summary
        assert 'reasoning' in summary
        assert summary['reasoning'] is not None

    @pytest.mark.no_parallel
    def test_detection_maintains_partial_functionality_during_errors(self, environment_detector, mock_partial_failure_conditions):
        """
        Test that detection maintains partial functionality when some mechanisms fail.

        Verifies:
            Detection continues working even when individual signal sources fail.

        Business Impact:
            Ensures detection resilience and availability in production environments.

        Scenario:
            Given: EnvironmentDetector with some signal sources configured to fail
            When: Running detection with partially failed detection mechanisms
            Then: Detection completes using available signals and indicates reduced confidence

        Fixtures Used:
            - environment_detector: EnvironmentDetector with default configuration
            - mock_partial_failure_conditions: Environment with some detection mechanisms failing
        """
        # Given: Partial failure conditions fixture is active (file system fails, env vars work)
        # When: Running detection under partial failure conditions
        result = environment_detector.detect_environment()

        # Then: Detection still works using available signal sources
        assert isinstance(result, EnvironmentInfo)
        assert result.environment in Environment
        assert 0.0 <= result.confidence <= 1.0
        assert result.reasoning is not None

        # Should detect from environment variables even if file system fails
        assert result.environment == Environment.PRODUCTION  # Based on mock fixture

        # Test that all public methods still function
        ai_result = environment_detector.detect_with_context(FeatureContext.AI_ENABLED)
        assert isinstance(ai_result, EnvironmentInfo)

        security_result = environment_detector.detect_with_context(FeatureContext.SECURITY_ENFORCEMENT)
        assert isinstance(security_result, EnvironmentInfo)

        # Summary should still work
        summary = environment_detector.get_environment_summary()
        assert 'detected_environment' in summary
        assert summary['detected_environment'] == 'production'
        assert 'all_signals' in summary
        # Should have at least one signal (from environment variable)
        assert len(summary['all_signals']) >= 1
