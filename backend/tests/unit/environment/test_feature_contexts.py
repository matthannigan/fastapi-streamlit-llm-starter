"""
Tests for feature-specific environment detection.

Tests the detect_with_context method with various FeatureContext values including
AI, security, cache, and resilience contexts. Covers feature-specific overrides,
metadata generation, and signal preservation.
"""

import pytest
import os
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


class TestEnvironmentDetectorFeatureContexts:
    """
    Test suite for feature-specific environment detection.

    Scope:
        - detect_with_context() method with various FeatureContext values
        - Feature-specific environment variable handling and overrides
        - Metadata generation for configuration hints

    Business Critical:
        Feature contexts enable specialized detection for AI, security, cache,
        and resilience systems that may require different environment logic
    """

    def test_detect_with_context_default_context_behavior(self, environment_detector):
        """
        Test that detect_with_context with DEFAULT context matches basic detection.

        Verifies:
            DEFAULT feature context produces same results as standard detection.

        Business Impact:
            Ensures consistent behavior between detection methods for standard cases.

        Scenario:
            Given: EnvironmentDetector instance
            When: Calling detect_with_context(FeatureContext.DEFAULT)
            Then: Returns same result as detect_environment() with no feature context

        Fixtures Used:
            - environment_detector: EnvironmentDetector with default configuration
        """
        # Given: EnvironmentDetector instance
        detector = environment_detector

        # When: Calling both detection methods
        default_result = detector.detect_with_context(FeatureContext.DEFAULT)
        basic_result = detector.detect_environment()

        # Then: Returns same result as detect_environment() with no feature context
        assert default_result.environment == basic_result.environment
        assert default_result.confidence == basic_result.confidence
        assert default_result.reasoning == basic_result.reasoning
        assert default_result.detected_by == basic_result.detected_by
        assert default_result.feature_context == FeatureContext.DEFAULT
        assert basic_result.feature_context == FeatureContext.DEFAULT
        assert default_result.additional_signals == basic_result.additional_signals
        assert default_result.metadata == basic_result.metadata

    def test_detect_with_context_ai_enabled_feature_detection(self, environment_detector, mock_ai_environment_vars):
        """
        Test that AI_ENABLED context applies AI-specific detection logic.

        Verifies:
            AI_ENABLED context checks ENABLE_AI_CACHE variable and adds metadata.

        Business Impact:
            Enables AI services to receive AI-optimized environment configuration.

        Scenario:
            Given: EnvironmentDetector with AI-specific environment variables
            When: Calling detect_with_context(FeatureContext.AI_ENABLED)
            Then: Returns EnvironmentInfo with AI-specific metadata and signal consideration

        Fixtures Used:
            - environment_detector: EnvironmentDetector with default configuration
            - mock_ai_environment_vars: Environment with ENABLE_AI_CACHE and related variables
        """
        # Given: EnvironmentDetector with AI-specific environment variables
        detector = environment_detector

        with patch.dict(os.environ, mock_ai_environment_vars):
            # When: Calling detect_with_context(FeatureContext.AI_ENABLED)
            ai_result = detector.detect_with_context(FeatureContext.AI_ENABLED)

            # Then: Returns EnvironmentInfo with AI-specific metadata and signal consideration
            assert ai_result.feature_context == FeatureContext.AI_ENABLED
            assert ai_result.environment == Environment.DEVELOPMENT  # From fixture
            assert ai_result.confidence > 0.0

            # Verify AI-specific metadata is added
            assert 'feature_context' in ai_result.metadata
            assert ai_result.metadata['feature_context'] == 'ai_enabled'
            assert 'enable_ai_cache_enabled' in ai_result.metadata
            assert ai_result.metadata['enable_ai_cache_enabled'] is True
            assert 'ai_prefix' in ai_result.metadata
            assert ai_result.metadata['ai_prefix'] == 'ai-'

    def test_detect_with_context_security_enforcement_override(self, environment_detector, mock_security_enforcement_vars):
        """
        Test that SECURITY_ENFORCEMENT context can override environment to production.

        Verifies:
            Security enforcement can force production environment for security features.

        Business Impact:
            Ensures security features receive production-level configuration when required.

        Scenario:
            Given: EnvironmentDetector with ENFORCE_AUTH=true environment variable
            When: Calling detect_with_context(FeatureContext.SECURITY_ENFORCEMENT)
            Then: May return PRODUCTION environment even in development context

        Fixtures Used:
            - environment_detector: EnvironmentDetector with default configuration
            - mock_security_enforcement_vars: Environment with ENFORCE_AUTH=true
        """
        # Given: EnvironmentDetector with ENFORCE_AUTH=true environment variable
        detector = environment_detector

        with patch.dict(os.environ, mock_security_enforcement_vars):
            # When: Calling detect_with_context(FeatureContext.SECURITY_ENFORCEMENT)
            security_result = detector.detect_with_context(FeatureContext.SECURITY_ENFORCEMENT)

            # Then: May return PRODUCTION environment even in development context
            assert security_result.feature_context == FeatureContext.SECURITY_ENFORCEMENT
            # The base environment is still development (from ENVIRONMENT=development in fixture)
            # but security override signal is available in additional_signals
            assert security_result.environment == Environment.DEVELOPMENT
            assert security_result.confidence > 0.0

            # Verify security-specific metadata is added
            assert 'feature_context' in security_result.metadata
            assert security_result.metadata['feature_context'] == 'security_enforcement'
            assert 'enforce_auth_enabled' in security_result.metadata
            assert security_result.metadata['enforce_auth_enabled'] is True

            # Verify additional security override signal was created
            security_signals = [s for s in security_result.additional_signals
                              if s.source == 'security_override']
            assert len(security_signals) == 1
            assert security_signals[0].environment == Environment.PRODUCTION
            assert security_signals[0].confidence == 0.90
            assert 'Security enforcement enabled' in security_signals[0].reasoning

    def test_detect_with_context_cache_optimization_context(self, environment_detector, mock_cache_environment_vars):
        """
        Test that CACHE_OPTIMIZATION context applies cache-specific detection logic.

        Verifies:
            Cache optimization context provides cache-specific environment assessment.

        Business Impact:
            Enables cache services to receive optimized configuration recommendations.

        Scenario:
            Given: EnvironmentDetector with cache-related environment variables
            When: Calling detect_with_context(FeatureContext.CACHE_OPTIMIZATION)
            Then: Returns EnvironmentInfo with cache-specific metadata and recommendations

        Fixtures Used:
            - environment_detector: EnvironmentDetector with default configuration
            - mock_cache_environment_vars: Environment with cache-related configuration
        """
        # Given: EnvironmentDetector with cache-related environment variables
        detector = environment_detector

        with patch.dict(os.environ, mock_cache_environment_vars):
            # When: Calling detect_with_context(FeatureContext.CACHE_OPTIMIZATION)
            cache_result = detector.detect_with_context(FeatureContext.CACHE_OPTIMIZATION)

            # Then: Returns EnvironmentInfo with cache-specific metadata and recommendations
            assert cache_result.feature_context == FeatureContext.CACHE_OPTIMIZATION
            assert cache_result.environment == Environment.PRODUCTION  # From fixture
            assert cache_result.confidence > 0.0

            # Verify cache-specific metadata is added
            assert 'feature_context' in cache_result.metadata
            assert cache_result.metadata['feature_context'] == 'cache_optimization'

            # Cache optimization context doesn't have special environment variables configured by default
            # but still provides feature context identification

    def test_detect_with_context_resilience_strategy_context(self, environment_detector, mock_resilience_environment_vars):
        """
        Test that RESILIENCE_STRATEGY context applies resilience-specific detection logic.

        Verifies:
            Resilience strategy context provides resilience-specific environment assessment.

        Business Impact:
            Enables resilience services to receive strategy-appropriate configuration.

        Scenario:
            Given: EnvironmentDetector with resilience-related environment variables
            When: Calling detect_with_context(FeatureContext.RESILIENCE_STRATEGY)
            Then: Returns EnvironmentInfo with resilience-specific metadata and recommendations

        Fixtures Used:
            - environment_detector: EnvironmentDetector with default configuration
            - mock_resilience_environment_vars: Environment with resilience configuration
        """
        # Given: EnvironmentDetector with resilience-related environment variables
        detector = environment_detector

        with patch.dict(os.environ, mock_resilience_environment_vars):
            # When: Calling detect_with_context(FeatureContext.RESILIENCE_STRATEGY)
            resilience_result = detector.detect_with_context(FeatureContext.RESILIENCE_STRATEGY)

            # Then: Returns EnvironmentInfo with resilience-specific metadata and recommendations
            assert resilience_result.feature_context == FeatureContext.RESILIENCE_STRATEGY
            assert resilience_result.environment == Environment.PRODUCTION  # From fixture
            assert resilience_result.confidence > 0.0

            # Verify resilience-specific metadata is added
            assert 'feature_context' in resilience_result.metadata
            assert resilience_result.metadata['feature_context'] == 'resilience_strategy'

            # Resilience strategy context doesn't have special environment variables configured by default
            # but still provides feature context identification

    def test_detect_with_context_adds_feature_specific_metadata(self, environment_detector, mock_feature_environment_vars):
        """
        Test that feature contexts add relevant metadata to detection results.

        Verifies:
            Feature-specific contexts enrich EnvironmentInfo with configuration hints.

        Business Impact:
            Enables infrastructure services to access feature-specific configuration guidance.

        Scenario:
            Given: EnvironmentDetector with feature-specific environment variables
            When: Calling detect_with_context() with various FeatureContext values
            Then: Returns EnvironmentInfo with metadata containing feature-specific hints

        Fixtures Used:
            - environment_detector: EnvironmentDetector with default configuration
            - mock_feature_environment_vars: Environment with various feature-specific variables
        """
        # Given: EnvironmentDetector with feature-specific environment variables
        detector = environment_detector

        with patch.dict(os.environ, mock_feature_environment_vars):
            # When: Calling detect_with_context() with various FeatureContext values

            # Test AI_ENABLED context
            ai_result = detector.detect_with_context(FeatureContext.AI_ENABLED)

            # Test SECURITY_ENFORCEMENT context
            security_result = detector.detect_with_context(FeatureContext.SECURITY_ENFORCEMENT)

            # Test CACHE_OPTIMIZATION context
            cache_result = detector.detect_with_context(FeatureContext.CACHE_OPTIMIZATION)

            # Test RESILIENCE_STRATEGY context
            resilience_result = detector.detect_with_context(FeatureContext.RESILIENCE_STRATEGY)

            # Then: Returns EnvironmentInfo with metadata containing feature-specific hints

            # AI metadata
            assert ai_result.metadata['feature_context'] == 'ai_enabled'
            assert 'enable_ai_cache_enabled' in ai_result.metadata
            assert 'ai_prefix' in ai_result.metadata
            assert ai_result.metadata['ai_prefix'] == 'ai-'

            # Security metadata
            assert security_result.metadata['feature_context'] == 'security_enforcement'
            assert 'enforce_auth_enabled' in security_result.metadata

            # Cache metadata
            assert cache_result.metadata['feature_context'] == 'cache_optimization'

            # Resilience metadata
            assert resilience_result.metadata['feature_context'] == 'resilience_strategy'

            # Verify each context has distinct metadata
            contexts = [ai_result, security_result, cache_result, resilience_result]
            feature_contexts = [result.metadata['feature_context'] for result in contexts]
            assert len(set(feature_contexts)) == 4  # All unique

    def test_detect_with_context_preserves_base_signals(self, environment_detector, mock_security_enforcement_vars):
        """
        Test that feature contexts preserve base environment signals.

        Verifies:
            Feature-specific detection includes both base and feature-specific signals.

        Business Impact:
            Ensures feature detection maintains comprehensive signal collection.

        Scenario:
            Given: EnvironmentDetector with both base and feature-specific signals
            When: Calling detect_with_context() with specific feature context
            Then: Returns EnvironmentInfo with additional_signals including both types

        Fixtures Used:
            - environment_detector: EnvironmentDetector with default configuration
            - mock_mixed_environment_signals: Environment with base and feature-specific signals
        """
        # Given: EnvironmentDetector with both base and feature-specific signals
        detector = environment_detector

        with patch.dict(os.environ, mock_security_enforcement_vars):
            # When: Calling detect_with_context() with specific feature context
            security_result = detector.detect_with_context(FeatureContext.SECURITY_ENFORCEMENT)
            default_result = detector.detect_with_context(FeatureContext.DEFAULT)

            # Then: Returns EnvironmentInfo with additional_signals including both types

            # Base signals should be present in both results
            base_signal_sources = {signal.source for signal in default_result.additional_signals}
            security_signal_sources = {signal.source for signal in security_result.additional_signals}

            # Security context should include all base signals plus additional feature-specific ones
            assert base_signal_sources.issubset(security_signal_sources)

            # Security context should have additional security override signal
            security_overrides = [s for s in security_result.additional_signals
                                if s.source == 'security_override']
            assert len(security_overrides) == 1

            # Base signals are preserved - check for common signal types
            base_env_signals = [s for s in default_result.additional_signals
                              if s.source == 'ENVIRONMENT']
            security_env_signals = [s for s in security_result.additional_signals
                                  if s.source == 'ENVIRONMENT']

            # Environment signals should be preserved in both contexts
            if base_env_signals:
                assert len(security_env_signals) == len(base_env_signals)
                assert security_env_signals[0].value == base_env_signals[0].value
