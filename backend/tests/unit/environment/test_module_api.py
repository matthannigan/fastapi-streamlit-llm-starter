"""
Tests for module-level environment detection API.

Tests the convenience functions get_environment_info, is_production_environment,
and is_development_environment. Covers global detector usage, confidence thresholds,
and feature context support.
"""

import pytest
from unittest.mock import patch, MagicMock
from typing import Dict, Any, List

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


class TestModuleLevelConvenienceFunctions:
    """
    Test suite for module-level convenience functions.

    Scope:
        - get_environment_info() function behavior and global detector usage
        - is_production_environment() and is_development_environment() functions
        - Confidence threshold validation and decision logic

    Business Critical:
        Module-level functions provide simple API for environment detection
        throughout infrastructure services and must maintain consistency
    """

    def test_get_environment_info_returns_complete_detection_result(self, mock_global_detector):
        """
        Test that get_environment_info returns complete EnvironmentInfo.

        Verifies:
            Module-level function returns same structure as EnvironmentDetector methods.

        Business Impact:
            Provides consistent API for environment detection across the application.

        Scenario:
            Given: Module-level get_environment_info function
            When: Calling function with default parameters
            Then: Returns EnvironmentInfo with all required fields populated

        Fixtures Used:
            - mock_global_detector: Mocked global environment detector instance
        """
        # Given: Module-level get_environment_info function is available
        # Configure the mock to return a complete EnvironmentInfo
        expected_env_info = EnvironmentInfo(
            environment=Environment.PRODUCTION,
            confidence=0.85,
            reasoning="Mock production detection",
            detected_by="mock_env_var",
            feature_context=FeatureContext.DEFAULT,
            additional_signals=[
                EnvironmentSignal(
                    source="ENVIRONMENT",
                    value="production",
                    environment=Environment.PRODUCTION,
                    confidence=0.85,
                    reasoning="Mock environment variable"
                )
            ],
            metadata={"test_key": "test_value"}
        )
        mock_global_detector.detect_with_context.return_value = expected_env_info

        # When: Calling function with default parameters
        result = get_environment_info()

        # Then: Returns EnvironmentInfo with all required fields populated
        assert isinstance(result, EnvironmentInfo)
        assert result.environment == Environment.PRODUCTION
        assert result.confidence == 0.85
        assert result.reasoning == "Mock production detection"
        assert result.detected_by == "mock_env_var"
        assert result.feature_context == FeatureContext.DEFAULT
        assert len(result.additional_signals) == 1
        assert "test_key" in result.metadata

        # Verify the global detector was called with default context
        mock_global_detector.detect_with_context.assert_called_once_with(FeatureContext.DEFAULT)

    def test_get_environment_info_supports_feature_contexts(self, mock_global_detector):
        """
        Test that get_environment_info accepts feature context parameters.

        Verifies:
            Module-level function supports feature-specific detection.

        Business Impact:
            Enables feature-aware detection without creating detector instances.

        Scenario:
            Given: Module-level get_environment_info function
            When: Calling function with specific FeatureContext
            Then: Returns EnvironmentInfo with feature-specific detection results

        Fixtures Used:
            - mock_global_detector: Mocked global environment detector instance
        """
        # Given: Module-level get_environment_info function is available
        # Configure the mock to return AI-specific detection results
        ai_env_info = EnvironmentInfo(
            environment=Environment.DEVELOPMENT,
            confidence=0.90,
            reasoning="AI-aware development detection",
            detected_by="ai_env_var",
            feature_context=FeatureContext.AI_ENABLED,
            additional_signals=[],
            metadata={"ai_prefix": "ai-", "enable_ai_cache": True}
        )
        mock_global_detector.detect_with_context.return_value = ai_env_info

        # When: Calling function with specific FeatureContext
        result = get_environment_info(FeatureContext.AI_ENABLED)

        # Then: Returns EnvironmentInfo with feature-specific detection results
        assert result.feature_context == FeatureContext.AI_ENABLED
        assert result.metadata.get("ai_prefix") == "ai-"
        assert "enable_ai_cache" in result.metadata

        # Verify the global detector was called with the AI context
        mock_global_detector.detect_with_context.assert_called_once_with(FeatureContext.AI_ENABLED)

    def test_get_environment_info_validates_feature_context_parameter(self):
        """
        Test that get_environment_info validates feature context parameter.

        Verifies:
            Invalid FeatureContext values raise AttributeError as actual behavior.

        Business Impact:
            Prevents invalid feature context usage throughout the application.

        Scenario:
            Given: Module-level get_environment_info function
            When: Calling function with invalid feature context parameter
            Then: Raises AttributeError due to missing 'value' attribute

        Fixtures Used:
            - None (testing parameter validation only)
        """
        # Given: Module-level get_environment_info function is available
        # When: Calling function with invalid feature context parameter
        # Then: Raises AttributeError due to missing 'value' attribute on non-enum

        # Test with invalid string value that's not a FeatureContext
        # The actual implementation tries to access .value attribute, causing AttributeError
        with pytest.raises(AttributeError, match="'str' object has no attribute 'value'"):
            get_environment_info("invalid_context")  # type: ignore

        # Test with integer (invalid type) - also lacks 'value' attribute
        with pytest.raises(AttributeError, match="'int' object has no attribute 'value'"):
            get_environment_info(123)  # type: ignore

        # Test with None - also lacks 'value' attribute
        with pytest.raises(AttributeError, match="'NoneType' object has no attribute 'value'"):
            get_environment_info(None)  # type: ignore

    def test_is_production_environment_uses_confidence_threshold(self, mock_global_detector):
        """
        Test that is_production_environment applies documented confidence threshold.

        Verifies:
            Function returns True only when confidence > 0.60 and environment is PRODUCTION.

        Business Impact:
            Prevents false positive production configuration due to low confidence detection.

        Scenario:
            Given: Various environment detection scenarios with different confidence levels
            When: Calling is_production_environment()
            Then: Returns True only for PRODUCTION environment with confidence > 0.60

        Fixtures Used:
            - mock_global_detector: Mocked global environment detector instance
        """
        # Test scenarios: (environment, confidence, expected_result)
        test_scenarios = [
            # High confidence production - should return True
            (Environment.PRODUCTION, 0.95, True),
            (Environment.PRODUCTION, 0.70, True),
            (Environment.PRODUCTION, 0.61, True),
            # Low confidence production - should return False (threshold is > 0.60)
            (Environment.PRODUCTION, 0.60, False),
            (Environment.PRODUCTION, 0.50, False),
            (Environment.PRODUCTION, 0.30, False),
            # Non-production environments with high confidence - should return False
            (Environment.DEVELOPMENT, 0.95, False),
            (Environment.STAGING, 0.85, False),
            (Environment.TESTING, 0.75, False),
            (Environment.UNKNOWN, 0.65, False)
        ]

        for environment, confidence, expected_result in test_scenarios:
            # Given: Environment detection scenario with specific confidence level
            env_info = EnvironmentInfo(
                environment=environment,
                confidence=confidence,
                reasoning=f"Mock {environment.value} detection",
                detected_by="mock_source",
                feature_context=FeatureContext.DEFAULT,
                additional_signals=[],
                metadata={}
            )
            mock_global_detector.detect_with_context.return_value = env_info

            # When: Calling is_production_environment()
            result = is_production_environment()

            # Then: Returns True only for PRODUCTION environment with confidence > 0.60
            assert result == expected_result, (
                f"Expected {expected_result} for {environment.value} with confidence {confidence}, got {result}"
            )

            # Verify the function uses default feature context
            mock_global_detector.detect_with_context.assert_called_with(FeatureContext.DEFAULT)
            mock_global_detector.reset_mock()

    def test_is_development_environment_uses_confidence_threshold(self, mock_global_detector):
        """
        Test that is_development_environment applies documented confidence threshold.

        Verifies:
            Function returns True only when confidence > 0.60 and environment is DEVELOPMENT.

        Business Impact:
            Prevents false positive development configuration due to low confidence detection.

        Scenario:
            Given: Various environment detection scenarios with different confidence levels
            When: Calling is_development_environment()
            Then: Returns True only for DEVELOPMENT environment with confidence > 0.60

        Fixtures Used:
            - mock_global_detector: Mocked global environment detector instance
        """
        # Test scenarios: (environment, confidence, expected_result)
        test_scenarios = [
            # High confidence development - should return True
            (Environment.DEVELOPMENT, 0.95, True),
            (Environment.DEVELOPMENT, 0.70, True),
            (Environment.DEVELOPMENT, 0.61, True),
            # Low confidence development - should return False (threshold is > 0.60)
            (Environment.DEVELOPMENT, 0.60, False),
            (Environment.DEVELOPMENT, 0.50, False),
            (Environment.DEVELOPMENT, 0.30, False),
            # Non-development environments with high confidence - should return False
            (Environment.PRODUCTION, 0.95, False),
            (Environment.STAGING, 0.85, False),
            (Environment.TESTING, 0.75, False),
            (Environment.UNKNOWN, 0.65, False)
        ]

        for environment, confidence, expected_result in test_scenarios:
            # Given: Environment detection scenario with specific confidence level
            env_info = EnvironmentInfo(
                environment=environment,
                confidence=confidence,
                reasoning=f"Mock {environment.value} detection",
                detected_by="mock_source",
                feature_context=FeatureContext.DEFAULT,
                additional_signals=[],
                metadata={}
            )
            mock_global_detector.detect_with_context.return_value = env_info

            # When: Calling is_development_environment()
            result = is_development_environment()

            # Then: Returns True only for DEVELOPMENT environment with confidence > 0.60
            assert result == expected_result, (
                f"Expected {expected_result} for {environment.value} with confidence {confidence}, got {result}"
            )

            # Verify the function uses default feature context
            mock_global_detector.detect_with_context.assert_called_with(FeatureContext.DEFAULT)
            mock_global_detector.reset_mock()

    def test_production_and_development_functions_support_feature_contexts(self, mock_global_detector, mock_feature_detection_results):
        """
        Test that environment check functions accept feature context parameters.

        Verifies:
            Both is_production_environment and is_development_environment support feature contexts.

        Business Impact:
            Enables feature-aware environment checking for specialized infrastructure needs.

        Scenario:
            Given: Module-level environment check functions
            When: Calling functions with various FeatureContext parameters
            Then: Functions use feature-specific detection for environment determination

        Fixtures Used:
            - mock_feature_detection_results: Detection results for various feature contexts
        """
        # Test is_production_environment with different feature contexts
        feature_contexts = [
            FeatureContext.DEFAULT,
            FeatureContext.AI_ENABLED,
            FeatureContext.SECURITY_ENFORCEMENT,
            FeatureContext.CACHE_OPTIMIZATION
        ]

        for feature_context in feature_contexts:
            # Given: Feature-specific detection result
            if feature_context in mock_feature_detection_results:
                env_info = mock_feature_detection_results[feature_context]
            else:
                # Create a default result for contexts not in fixture
                env_info = EnvironmentInfo(
                    environment=Environment.PRODUCTION,
                    confidence=0.85,
                    reasoning=f"Mock {feature_context.value} detection",
                    detected_by="mock_source",
                    feature_context=feature_context,
                    additional_signals=[],
                    metadata={}
                )

            mock_global_detector.detect_with_context.return_value = env_info

            # When: Calling is_production_environment with feature context
            prod_result = is_production_environment(feature_context)

            # Then: Function uses feature-specific detection
            expected_prod = (env_info.environment == Environment.PRODUCTION and env_info.confidence > 0.60)
            assert prod_result == expected_prod
            mock_global_detector.detect_with_context.assert_called_with(feature_context)

            # When: Calling is_development_environment with feature context
            mock_global_detector.reset_mock()
            mock_global_detector.detect_with_context.return_value = env_info
            dev_result = is_development_environment(feature_context)

            # Then: Function uses feature-specific detection
            expected_dev = (env_info.environment == Environment.DEVELOPMENT and env_info.confidence > 0.60)
            assert dev_result == expected_dev
            mock_global_detector.detect_with_context.assert_called_with(feature_context)

            mock_global_detector.reset_mock()

        # Test specific scenario where SECURITY_ENFORCEMENT overrides to production
        security_env_info = mock_feature_detection_results[FeatureContext.SECURITY_ENFORCEMENT]
        mock_global_detector.detect_with_context.return_value = security_env_info

        # Security enforcement should return production with high confidence
        assert is_production_environment(FeatureContext.SECURITY_ENFORCEMENT) == True
        assert is_development_environment(FeatureContext.SECURITY_ENFORCEMENT) == False

    def test_environment_check_functions_use_same_detection_logic(self, mock_global_detector):
        """
        Test that environment check functions use consistent detection logic.

        Verifies:
            is_production_environment and is_development_environment use get_environment_info.

        Business Impact:
            Ensures consistent detection behavior across all module-level functions.

        Scenario:
            Given: Module-level environment check functions
            When: Calling functions under identical conditions
            Then: Functions use same underlying detection logic with consistent results

        Fixtures Used:
            - mock_global_detector: Mocked global environment detector for consistency testing
        """
        # Given: Mock detector returns consistent detection result
        env_info = EnvironmentInfo(
            environment=Environment.PRODUCTION,
            confidence=0.85,
            reasoning="Consistent detection result",
            detected_by="env_var",
            feature_context=FeatureContext.DEFAULT,
            additional_signals=[
                EnvironmentSignal(
                    source="ENVIRONMENT",
                    value="production",
                    environment=Environment.PRODUCTION,
                    confidence=0.85,
                    reasoning="Environment variable"
                )
            ],
            metadata={"consistency_test": True}
        )
        mock_global_detector.detect_with_context.return_value = env_info

        # When: Calling all module-level functions under identical conditions
        info_result = get_environment_info()
        prod_result = is_production_environment()
        dev_result = is_development_environment()

        # Then: All functions use the same underlying detection logic
        # All functions should have called the global detector with DEFAULT context
        assert mock_global_detector.detect_with_context.call_count == 3
        for call in mock_global_detector.detect_with_context.call_args_list:
            assert call[0][0] == FeatureContext.DEFAULT

        # get_environment_info should return the complete EnvironmentInfo
        assert info_result == env_info
        assert info_result.confidence == 0.85
        assert info_result.environment == Environment.PRODUCTION

        # is_production_environment should apply confidence threshold logic
        # confidence 0.85 > 0.60 and environment is PRODUCTION, so True
        assert prod_result == True

        # is_development_environment should apply confidence threshold logic
        # environment is PRODUCTION (not DEVELOPMENT), so False
        assert dev_result == False

        # Test with development environment to verify consistency
        mock_global_detector.reset_mock()
        dev_env_info = EnvironmentInfo(
            environment=Environment.DEVELOPMENT,
            confidence=0.75,
            reasoning="Development detection result",
            detected_by="env_var",
            feature_context=FeatureContext.DEFAULT,
            additional_signals=[],
            metadata={}
        )
        mock_global_detector.detect_with_context.return_value = dev_env_info

        # When: Calling functions again with development environment
        dev_info_result = get_environment_info()
        dev_prod_result = is_production_environment()
        dev_dev_result = is_development_environment()

        # Then: Results are consistent with the underlying detection
        assert dev_info_result.environment == Environment.DEVELOPMENT
        assert dev_prod_result == False  # Not production
        assert dev_dev_result == True   # Development with confidence 0.75 > 0.60
