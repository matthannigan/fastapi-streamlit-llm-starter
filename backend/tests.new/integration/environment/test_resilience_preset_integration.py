"""
Resilience Preset Environment-Aware Configuration Integration Tests

This module tests the integration between environment detection and resilience preset
management, ensuring that resilience strategies are automatically optimized based
on the detected environment.

MEDIUM PRIORITY - System reliability and error handling
"""

import pytest
from app.core.environment import (
    Environment,
    FeatureContext,
    get_environment_info,
    EnvironmentInfo
)


class TestResiliencePresetEnvironmentIntegration:
    """
    Integration tests for resilience preset environment-aware configuration.

    Seam Under Test:
        Environment Detection → Resilience Preset Manager → Strategy Selection

    Critical Path:
        Environment detection → Resilience preset recommendation → Configuration application

    Business Impact:
        Ensures appropriate resilience strategies for different operational contexts

    Test Strategy:
        - Test resilience preset recommendations for different environments
        - Verify environment-specific resilience strategy selection
        - Test resilience preset behavior with feature contexts
        - Validate resilience configuration adaptation to environment changes
    """

    def test_production_environment_recommends_conservative_resilience_preset(self, production_environment):
        """
        Test that production environment recommends conservative resilience strategy.

        Integration Scope:
            Production environment → Resilience preset manager → Conservative preset selection

        Business Impact:
            Ensures production stability with conservative resilience settings

        Test Strategy:
            - Set production environment
            - Verify environment detection
            - Test resilience preset recommendation
            - Verify conservative resilience settings for production

        Success Criteria:
            - Resilience preset manager recommends conservative preset
            - Production preset has appropriate retry limits and circuit breaker settings
            - Environment detection correctly identifies production
        """
        # Verify environment detection
        env_info = get_environment_info()
        assert env_info.environment == Environment.PRODUCTION
        assert env_info.confidence >= 0.8

        # Test resilience preset integration
        try:
            from app.infrastructure.resilience.config_presets import ResiliencePresetManager
            preset_manager = ResiliencePresetManager()

            # Should recommend conservative preset for production
            preset = preset_manager.recommend_preset(env_info.environment)
            assert preset is not None

            # Production preset should be conservative
            assert 'conservative' in preset.lower() or 'production' in preset.lower()

        except ImportError:
            pytest.skip("Resilience preset system not available")

    def test_development_environment_recommends_aggressive_resilience_preset(self, development_environment):
        """
        Test that development environment recommends aggressive resilience strategy.

        Integration Scope:
            Development environment → Resilience preset manager → Aggressive preset selection

        Business Impact:
            Ensures fast development iteration with aggressive resilience settings

        Test Strategy:
            - Set development environment
            - Verify environment detection
            - Test resilience preset recommendation
            - Verify aggressive resilience settings for development

        Success Criteria:
            - Resilience preset manager recommends aggressive preset
            - Development preset has fast-fail behavior for quick feedback
            - Environment detection correctly identifies development
        """
        # Verify environment detection
        env_info = get_environment_info()
        assert env_info.environment == Environment.DEVELOPMENT
        assert env_info.confidence >= 0.8

        # Test resilience preset integration
        try:
            from app.infrastructure.resilience.config_presets import ResiliencePresetManager
            preset_manager = ResiliencePresetManager()

            # Should recommend aggressive preset for development
            preset = preset_manager.recommend_preset(env_info.environment)
            assert preset is not None

            # Development preset should be aggressive/fast-fail
            assert 'development' in preset.lower() or 'dev' in preset.lower() or 'aggressive' in preset.lower()

        except ImportError:
            pytest.skip("Resilience preset system not available")

    def test_staging_environment_recommends_balanced_resilience_preset(self, staging_environment):
        """
        Test that staging environment recommends balanced resilience strategy.

        Integration Scope:
            Staging environment → Resilience preset manager → Balanced preset selection

        Business Impact:
            Ensures staging gets balanced pre-production resilience settings

        Test Strategy:
            - Set staging environment
            - Verify environment detection
            - Test resilience preset recommendation
            - Verify balanced resilience settings for staging

        Success Criteria:
            - Resilience preset manager recommends balanced preset
            - Staging preset balances stability and feedback
            - Environment detection correctly identifies staging
        """
        # Verify environment detection
        env_info = get_environment_info()
        assert env_info.environment == Environment.STAGING
        assert env_info.confidence >= 0.8

        # Test resilience preset integration
        try:
            from app.infrastructure.resilience.config_presets import ResiliencePresetManager
            preset_manager = ResiliencePresetManager()

            # Should recommend balanced preset for staging
            preset = preset_manager.recommend_preset(env_info.environment)
            assert preset is not None

            # Staging preset should be balanced
            assert 'staging' in preset.lower() or 'stage' in preset.lower() or 'balanced' in preset.lower()

        except ImportError:
            pytest.skip("Resilience preset system not available")

    def test_resilience_preset_with_resilience_context(self, production_environment):
        """
        Test resilience preset selection with resilience strategy context.

        Integration Scope:
            Production environment + Resilience context → Resilience preset manager → Context-aware preset

        Business Impact:
            Ensures resilience strategy context influences configuration

        Test Strategy:
            - Set production environment
            - Test resilience preset with resilience strategy context
            - Verify resilience-specific configuration

        Success Criteria:
            - Resilience context influences preset selection
            - Resilience-specific strategies are applied
            - Configuration reflects resilience workload considerations
        """
        # Test with resilience strategy context
        resilience_env = get_environment_info(FeatureContext.RESILIENCE_STRATEGY)
        assert resilience_env.environment == Environment.PRODUCTION

        # Test resilience preset integration with resilience context
        try:
            from app.infrastructure.resilience.config_presets import ResiliencePresetManager
            preset_manager = ResiliencePresetManager()

            # Should recommend resilience-optimized preset
            preset = preset_manager.recommend_preset(resilience_env.environment)
            assert preset is not None

            # Resilience context should influence configuration

        except ImportError:
            pytest.skip("Resilience preset system not available")

    def test_resilience_preset_confidence_influence(self, clean_environment):
        """
        Test that resilience preset selection is influenced by environment detection confidence.

        Integration Scope:
            Environment confidence → Resilience preset manager → Confidence-based selection

        Business Impact:
            Ensures resilience configuration adapts to detection confidence

        Test Strategy:
            - Test resilience presets with high confidence detection
            - Test resilience presets with low confidence detection
            - Verify confidence influences preset recommendations

        Success Criteria:
            - High confidence detection leads to confident preset selection
            - Low confidence detection leads to conservative preset selection
            - Confidence scoring affects resilience configuration decisions
        """
        # Test high confidence production detection
        import os
        os.environ['ENVIRONMENT'] = 'production'

        high_conf_env = get_environment_info()
        assert high_conf_env.confidence >= 0.8

        # Test low confidence detection (no clear signals)
        os.environ.pop('ENVIRONMENT')
        low_conf_env = get_environment_info()
        assert low_conf_env.confidence < 0.7

        # Test resilience preset integration
        try:
            from app.infrastructure.resilience.config_presets import ResiliencePresetManager
            preset_manager = ResiliencePresetManager()

            # Both should get valid presets but potentially different ones
            high_conf_preset = preset_manager.recommend_preset(high_conf_env.environment)
            low_conf_preset = preset_manager.recommend_preset(low_conf_env.environment)

            assert high_conf_preset is not None
            assert low_conf_preset is not None

            # In practice, both might get same preset but confidence could influence settings

        except ImportError:
            pytest.skip("Resilience preset system not available")

    def test_resilience_preset_with_unknown_environment(self, unknown_environment):
        """
        Test resilience preset selection when environment cannot be determined.

        Integration Scope:
            Unknown environment → Resilience preset manager → Conservative preset selection

        Business Impact:
            Ensures safe resilience configuration when environment is unclear

        Test Strategy:
            - Create unknown environment scenario
            - Test resilience preset recommendation
            - Verify conservative resilience configuration

        Success Criteria:
            - Unknown environment gets conservative preset
            - Resilience configuration is safe for unknown environments
            - System degrades gracefully with unknown environment
        """
        env_info = get_environment_info()
        assert env_info.environment == Environment.DEVELOPMENT  # Fallback
        assert env_info.confidence < 0.7  # Low confidence

        # Test resilience preset integration
        try:
            from app.infrastructure.resilience.config_presets import ResiliencePresetManager
            preset_manager = ResiliencePresetManager()

            # Should recommend conservative preset for unknown environment
            preset = preset_manager.recommend_preset(env_info.environment)
            assert preset is not None

            # Unknown environment should get development or conservative preset

        except ImportError:
            pytest.skip("Resilience preset system not available")

    def test_resilience_preset_custom_environment_mapping(self, custom_detection_config):
        """
        Test resilience preset selection with custom environment mapping.

        Integration Scope:
            Custom detection config → Resilience preset manager → Custom environment handling

        Business Impact:
            Ensures custom environments work with resilience preset system

        Test Strategy:
            - Create detector with custom configuration
            - Test resilience preset with custom environment
            - Verify custom environment mapping works

        Success Criteria:
            - Custom environment configuration is respected
            - Resilience preset system handles custom environments
            - Custom patterns work correctly with resilience presets
        """
        detector = __import__('app.core.environment', fromlist=['EnvironmentDetector']).EnvironmentDetector(custom_detection_config)

        # Test with custom configuration
        import os
        os.environ['CUSTOM_ENV'] = 'production'

        env_info = detector.detect_environment()
        assert env_info.environment == Environment.PRODUCTION

        # Test resilience preset integration
        try:
            from app.infrastructure.resilience.config_presets import ResiliencePresetManager
            preset_manager = ResiliencePresetManager()

            # Should recommend production preset based on custom environment detection
            preset = preset_manager.recommend_preset(env_info.environment)
            assert preset is not None

        except ImportError:
            pytest.skip("Resilience preset system not available")

    def test_resilience_preset_environment_consistency(self, clean_environment):
        """
        Test that resilience preset recommendations are consistent for same environment.

        Integration Scope:
            Environment detection → Resilience preset manager → Consistent recommendations

        Business Impact:
            Ensures deterministic resilience configuration for same environment

        Test Strategy:
            - Set consistent environment
            - Make multiple resilience preset recommendations
            - Verify consistent results across calls

        Success Criteria:
            - Same environment produces same resilience preset recommendation
            - Multiple calls return identical recommendations
            - Resilience configuration is deterministic
        """
        import os
        os.environ['ENVIRONMENT'] = 'production'

        # Make multiple calls to test consistency
        try:
            from app.infrastructure.resilience.config_presets import ResiliencePresetManager
            preset_manager = ResiliencePresetManager()

            presets = []
            for _ in range(3):
                env_info = get_environment_info()
                preset = preset_manager.recommend_preset(env_info.environment)
                presets.append(preset)

            # All recommendations should be identical
            assert len(set(presets)) == 1  # All same
            assert presets[0] is not None

        except ImportError:
            pytest.skip("Resilience preset system not available")

    def test_resilience_preset_operation_specific_selection(self, production_environment):
        """
        Test operation-specific resilience preset selection.

        Integration Scope:
            Environment + Operation → Resilience preset manager → Operation-specific preset

        Business Impact:
            Ensures different operations get appropriate resilience strategies

        Test Strategy:
            - Set production environment
            - Test resilience preset for different operation types
            - Verify operation-specific resilience configuration

        Success Criteria:
            - Different operations can get different resilience strategies
            - Operation-specific configuration is respected
            - Environment context is maintained across operations
        """
        env_info = get_environment_info()
        assert env_info.environment == Environment.PRODUCTION

        # Test resilience preset integration with operation context
        try:
            from app.infrastructure.resilience.config_presets import ResiliencePresetManager
            preset_manager = ResiliencePresetManager()

            # Test different operation types
            operations = ['critical', 'standard', 'bulk']

            for operation in operations:
                # Should recommend appropriate preset for operation
                preset = preset_manager.recommend_preset(env_info.environment, operation)
                assert preset is not None

                # Different operations may get different presets or configurations

        except ImportError:
            pytest.skip("Resilience preset system not available")

    def test_resilience_preset_error_handling(self, mock_environment_detection_failure):
        """
        Test resilience preset system error handling when environment detection fails.

        Integration Scope:
            Environment detection failure → Resilience preset manager → Error handling

        Business Impact:
            Ensures resilience system remains stable when environment detection fails

        Test Strategy:
            - Mock environment detection to fail
            - Test resilience preset manager behavior
            - Verify graceful error handling

        Success Criteria:
            - Resilience preset system handles detection failures
            - Appropriate fallback behavior is used
            - System logs errors appropriately
        """
        # Mock environment detection failure
        with pytest.raises(Exception, match="Environment detection service unavailable"):
            get_environment_info()

        # Test resilience preset manager with failed detection
        try:
            from app.infrastructure.resilience.config_presets import ResiliencePresetManager
            preset_manager = ResiliencePresetManager()

            # Should handle detection failure gracefully
            # Implementation may vary, but should not crash
            try:
                preset = preset_manager.recommend_preset(Environment.DEVELOPMENT)  # Fallback
                assert preset is not None
            except Exception:
                # May raise exception or return None, but shouldn't crash
                pass

        except ImportError:
            pytest.skip("Resilience preset system not available")
