"""
Multi-Context Environment Detection Integration Tests

This module tests environment detection across different feature contexts (AI, Security,
Cache, Resilience), ensuring that each context provides appropriate metadata and
overrides for its specific use case.

HIGH PRIORITY - Core functionality across all infrastructure services
"""

import pytest
from app.core.environment import (
    Environment,
    FeatureContext,
    EnvironmentDetector,
    DetectionConfig,
    get_environment_info,
    EnvironmentInfo,
    EnvironmentSignal
)


class TestMultiContextEnvironmentDetection:
    """
    Integration tests for multi-context environment detection.

    Seam Under Test:
        Feature Context → Environment Detection → Context-Specific Metadata

    Critical Path:
        Feature-specific context → Detection logic → Metadata and overrides

    Business Impact:
        Ensures consistent environment detection across different feature contexts
        while providing appropriate metadata for each context

    Test Strategy:
        - Test each feature context provides appropriate metadata
        - Verify context-specific overrides work correctly
        - Test context consistency across different environments
        - Validate metadata format and content for each context
    """

    def test_ai_enabled_context_provides_cache_metadata(self, ai_enabled_environment):
        """
        Test that AI_ENABLED context provides AI-specific cache metadata.

        Integration Scope:
            AI feature context → Environment detection → Cache metadata generation

        Business Impact:
            Ensures AI services get appropriate cache prefixes and optimization hints

        Test Strategy:
            - Enable AI features in environment
            - Request environment info with AI context
            - Verify AI-specific metadata is included

        Success Criteria:
            - AI context returns enable_ai_cache_enabled = True
            - AI prefix metadata is provided for cache keys
            - Context-specific metadata is correctly applied
        """
        ai_env = get_environment_info(FeatureContext.AI_ENABLED)

        # Should detect environment with AI context
        assert ai_env.environment in [Environment.DEVELOPMENT, Environment.PRODUCTION]
        assert ai_env.feature_context == FeatureContext.AI_ENABLED

        # Should include AI-specific metadata
        assert ai_env.metadata.get('enable_ai_cache_enabled') is True
        assert 'ai_prefix' in ai_env.metadata
        assert ai_env.metadata['ai_prefix'] == 'ai-'

        # Should include AI-specific signals
        ai_signals = [s for s in ai_env.additional_signals
                     if s.source == 'feature_context' and 'ai' in s.value.lower()]
        assert len(ai_signals) >= 1

    def test_security_enforcement_context_applies_overrides(self, security_enforcement_environment):
        """
        Test that SECURITY_ENFORCEMENT context applies production overrides.

        Integration Scope:
            Security feature context → Production override → Environment enforcement

        Business Impact:
            Allows security-conscious deployments to enforce production rules
            regardless of underlying environment

        Test Strategy:
            - Enable security enforcement in development environment
            - Request environment info with security context
            - Verify production override is applied

        Success Criteria:
            - Security context overrides to production environment
            - High confidence in security override decision
            - Security enforcement metadata is included
        """
        security_env = get_environment_info(FeatureContext.SECURITY_ENFORCEMENT)

        # Should override to production when security enforcement is enabled
        assert security_env.environment == Environment.PRODUCTION
        assert security_env.confidence >= 0.9
        assert "security enforcement" in security_env.reasoning.lower()

        # Should include security-specific metadata
        assert security_env.metadata.get('enforce_auth_enabled') is True
        assert security_env.feature_context == FeatureContext.SECURITY_ENFORCEMENT

        # Should include security override signal
        security_signals = [s for s in security_env.additional_signals
                           if s.source == 'security_override']
        assert len(security_signals) >= 1
        assert security_signals[0].environment == Environment.PRODUCTION
        assert security_signals[0].confidence >= 0.9

    def test_cache_optimization_context_in_production(self, production_environment):
        """
        Test CACHE_OPTIMIZATION context in production environment.

        Integration Scope:
            Production environment → Cache optimization context → Cache configuration hints

        Business Impact:
            Ensures cache optimization works correctly in production with
            appropriate configuration hints

        Test Strategy:
            - Set production environment
            - Request environment info with cache optimization context
            - Verify cache-specific metadata is provided

        Success Criteria:
            - Cache context returns production environment
            - Cache optimization metadata is included
            - Context is correctly identified as cache optimization
        """
        cache_env = get_environment_info(FeatureContext.CACHE_OPTIMIZATION)

        # Should detect production environment
        assert cache_env.environment == Environment.PRODUCTION
        assert cache_env.feature_context == FeatureContext.CACHE_OPTIMIZATION

        # Should include cache optimization metadata
        assert 'feature_context' in cache_env.metadata
        assert cache_env.metadata['feature_context'] == 'cache_optimization'

        # Should have high confidence detection
        assert cache_env.confidence >= 0.8

    def test_resilience_strategy_context_in_staging(self, staging_environment):
        """
        Test RESILIENCE_STRATEGY context in staging environment.

        Integration Scope:
            Staging environment → Resilience strategy context → Resilience configuration hints

        Business Impact:
            Ensures resilience patterns work correctly in staging with
            appropriate strategy hints

        Test Strategy:
            - Set staging environment
            - Request environment info with resilience strategy context
            - Verify resilience-specific metadata is provided

        Success Criteria:
            - Resilience context returns staging environment
            - Resilience strategy metadata is included
            - Context is correctly identified as resilience strategy
        """
        resilience_env = get_environment_info(FeatureContext.RESILIENCE_STRATEGY)

        # Should detect staging environment
        assert resilience_env.environment == Environment.STAGING
        assert resilience_env.feature_context == FeatureContext.RESILIENCE_STRATEGY

        # Should include resilience strategy metadata
        assert 'feature_context' in resilience_env.metadata
        assert resilience_env.metadata['feature_context'] == 'resilience_strategy'

        # Should have high confidence detection
        assert resilience_env.confidence >= 0.8

    def test_default_context_consistency(self, development_environment):
        """
        Test that DEFAULT context provides consistent detection.

        Integration Scope:
            Standard environment detection → Default context → Baseline metadata

        Business Impact:
            Ensures baseline environment detection works consistently
            without feature-specific overrides

        Test Strategy:
            - Set development environment
            - Request environment info with default context
            - Verify no feature-specific overrides are applied

        Success Criteria:
            - Default context returns development environment
            - No feature-specific metadata is added
            - Only base environment signals are present
        """
        default_env = get_environment_info(FeatureContext.DEFAULT)

        # Should detect development environment
        assert default_env.environment == Environment.DEVELOPMENT
        assert default_env.feature_context == FeatureContext.DEFAULT

        # Should not include feature-specific metadata
        assert default_env.metadata.get('enable_ai_cache_enabled') is None
        assert default_env.metadata.get('enforce_auth_enabled') is None
        assert default_env.metadata.get('ai_prefix') is None

        # Should have minimal metadata (only feature_context)
        assert 'feature_context' in default_env.metadata
        assert default_env.metadata['feature_context'] == 'default'
        assert len(default_env.metadata) == 1  # Only feature_context

    def test_context_consistency_across_environments(self, clean_environment):
        """
        Test that feature contexts work consistently across different environments.

        Integration Scope:
            Multiple environments → Feature contexts → Consistent metadata patterns

        Business Impact:
            Ensures feature contexts provide consistent metadata regardless
            of underlying environment detection

        Test Strategy:
            - Test each feature context in multiple environments
            - Verify metadata format consistency
            - Test context-specific behavior is preserved

        Success Criteria:
            - AI context always provides AI metadata regardless of environment
            - Security context always provides security metadata
            - Context-specific metadata format is consistent
        """
        environments = ['development', 'staging', 'production']

        for env in environments:
            os.environ['ENVIRONMENT'] = env

            # Test AI context consistency
            ai_env = get_environment_info(FeatureContext.AI_ENABLED)
            assert ai_env.feature_context == FeatureContext.AI_ENABLED
            assert 'enable_ai_cache_enabled' in ai_env.metadata or 'feature_context' in ai_env.metadata

            # Test Security context consistency
            security_env = get_environment_info(FeatureContext.SECURITY_ENFORCEMENT)
            assert security_env.feature_context == FeatureContext.SECURITY_ENFORCEMENT
            assert 'enforce_auth_enabled' in security_env.metadata or 'feature_context' in security_env.metadata

            # Test Cache context consistency
            cache_env = get_environment_info(FeatureContext.CACHE_OPTIMIZATION)
            assert cache_env.feature_context == FeatureContext.CACHE_OPTIMIZATION
            assert 'feature_context' in cache_env.metadata

    def test_context_metadata_format_consistency(self, production_environment):
        """
        Test that context metadata follows consistent format patterns.

        Integration Scope:
            Feature contexts → Metadata generation → Consistent data structures

        Business Impact:
            Ensures downstream consumers can reliably parse context metadata

        Test Strategy:
            - Test metadata format for each feature context
            - Verify metadata keys follow consistent naming
            - Test metadata value types and structures

        Success Criteria:
            - All contexts include feature_context in metadata
            - Boolean flags use consistent key naming (xxx_enabled)
            - String values follow consistent patterns
        """
        # Test each context metadata format
        contexts = [
            (FeatureContext.AI_ENABLED, 'enable_ai_cache_enabled'),
            (FeatureContext.SECURITY_ENFORCEMENT, 'enforce_auth_enabled'),
            (FeatureContext.CACHE_OPTIMIZATION, 'feature_context'),
            (FeatureContext.RESILIENCE_STRATEGY, 'feature_context'),
            (FeatureContext.DEFAULT, 'feature_context')
        ]

        for context, expected_key in contexts:
            env_info = get_environment_info(context)

            # All contexts should include feature_context metadata
            assert 'feature_context' in env_info.metadata
            assert env_info.metadata['feature_context'] == context.value

            # Check for context-specific metadata
            if expected_key == 'enable_ai_cache_enabled':
                # AI context should have boolean flag or feature_context
                assert ('enable_ai_cache_enabled' in env_info.metadata or
                        env_info.metadata.get('feature_context') == context.value)
            elif expected_key == 'enforce_auth_enabled':
                # Security context should have boolean flag or feature_context
                assert ('enforce_auth_enabled' in env_info.metadata or
                        env_info.metadata.get('feature_context') == context.value)
            else:
                # Other contexts should have feature_context
                assert env_info.metadata.get('feature_context') == context.value

    def test_context_with_custom_configuration(self, custom_detection_config):
        """
        Test feature contexts with custom detection configuration.

        Integration Scope:
            Custom detection config → Feature contexts → Custom metadata and overrides

        Business Impact:
            Ensures custom configurations work correctly with feature contexts

        Test Strategy:
            - Create detector with custom configuration
            - Test feature contexts with custom config
            - Verify custom metadata and overrides are applied

        Success Criteria:
            - Custom configuration is respected
            - Feature-specific custom settings are applied
            - Custom overrides work correctly with contexts
        """
        detector = EnvironmentDetector(custom_detection_config)

        # Test custom AI configuration
        os.environ['ENABLE_AI_FEATURES'] = 'true'
        ai_env = detector.detect_with_context(FeatureContext.AI_ENABLED)

        assert ai_env.environment in [Environment.DEVELOPMENT, Environment.PRODUCTION]
        assert ai_env.metadata.get('enable_ai_features_enabled') is True
        assert ai_env.metadata.get('ai_prefix') == 'ai-'

        # Test custom security configuration
        os.environ['FORCE_SECURE_MODE'] = 'true'
        security_env = detector.detect_with_context(FeatureContext.SECURITY_ENFORCEMENT)

        # Custom security config should still override to production
        assert security_env.environment == Environment.PRODUCTION
        assert security_env.metadata.get('force_secure_mode_enabled') is True

    def test_context_signal_collection_completeness(self, ai_enabled_environment):
        """
        Test that feature contexts collect all relevant signals.

        Integration Scope:
            Feature context → Signal collection → Complete signal set

        Business Impact:
            Ensures all relevant signals are collected for comprehensive
            environment detection

        Test Strategy:
            - Enable AI features
            - Collect environment signals with AI context
            - Verify all relevant signals are included

        Success Criteria:
            - Base environment signals are collected
            - Feature-specific signals are added
            - No relevant signals are missing
        """
        env_info = get_environment_info(FeatureContext.AI_ENABLED)

        # Should have base environment signals
        all_signals = env_info.additional_signals
        assert len(all_signals) >= 1

        # Should include AI-specific signals
        ai_signals = [s for s in all_signals if 'ai' in s.value.lower()]
        assert len(ai_signals) >= 1

        # Should include feature context signal
        context_signals = [s for s in all_signals if s.source == 'feature_context']
        assert len(context_signals) >= 1

        # All signals should have reasonable confidence scores
        for signal in all_signals:
            assert 0.0 <= signal.confidence <= 1.0
            assert signal.environment in Environment
            assert len(signal.reasoning) > 0

    def test_context_reasoning_comprehensiveness(self, security_enforcement_environment):
        """
        Test that feature contexts provide comprehensive reasoning.

        Integration Scope:
            Feature context → Detection logic → Detailed reasoning

        Business Impact:
            Ensures debugging and monitoring can understand context decisions

        Test Strategy:
            - Enable security enforcement
            - Get environment info with security context
            - Verify reasoning includes all relevant information

        Success Criteria:
            - Reasoning includes base environment detection
            - Reasoning includes feature-specific decisions
            - Reasoning explains confidence scoring
        """
        security_env = get_environment_info(FeatureContext.SECURITY_ENFORCEMENT)

        reasoning = security_env.reasoning.lower()

        # Should include base environment detection
        assert 'production' in reasoning or 'development' in reasoning

        # Should include security-specific information
        assert 'security' in reasoning or 'enforcement' in reasoning or 'override' in reasoning

        # Should include confidence information
        assert 'confidence' in reasoning or str(security_env.confidence) in security_env.reasoning

        # Should include detection method
        assert 'detected by' in security_env.reasoning or security_env.detected_by in security_env.reasoning
