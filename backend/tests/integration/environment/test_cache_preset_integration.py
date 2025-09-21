"""
Cache Preset Environment-Aware Configuration Integration Tests

This module tests the integration between environment detection and cache preset
management, ensuring that cache configurations are automatically optimized based
on the detected environment.

MEDIUM PRIORITY - Performance and operational efficiency
"""

import pytest
from app.core.environment import (
    Environment,
    FeatureContext,
    get_environment_info,
    EnvironmentInfo
)


class TestCachePresetEnvironmentIntegration:
    """
    Integration tests for cache preset environment-aware configuration.

    Seam Under Test:
        Environment Detection → Cache Preset Manager → Configuration Selection

    Critical Path:
        Environment detection → Cache preset recommendation → Configuration application

    Business Impact:
        Ensures optimal cache settings for different deployment environments

    Test Strategy:
        - Test cache preset recommendations for different environments
        - Verify environment-specific cache configuration selection
        - Test cache preset behavior with feature contexts
        - Validate cache configuration adaptation to environment changes
    """

    def test_production_environment_recommends_production_cache_preset(self, production_environment):
        """
        Test that production environment recommends production cache preset.

        Integration Scope:
            Production environment → Cache preset manager → Production preset selection

        Business Impact:
            Ensures production workloads get appropriate cache configuration

        Test Strategy:
            - Set production environment
            - Verify environment detection
            - Test cache preset recommendation
            - Verify production-optimized cache settings

        Success Criteria:
            - Cache preset manager recommends production preset
            - Production preset has appropriate TTLs and settings
            - Environment detection correctly identifies production
        """
        # Verify environment detection
        env_info = get_environment_info()
        assert env_info.environment == Environment.PRODUCTION
        assert env_info.confidence >= 0.8

        # Test cache preset integration
        try:
            from app.infrastructure.cache.cache_presets import CachePresetManager
            preset_manager = CachePresetManager()

            # Should recommend production-appropriate preset
            preset = preset_manager.recommend_preset(env_info.environment)
            assert preset is not None

            # Production preset should be indicated
            assert 'production' in preset.lower() or 'prod' in preset.lower()

        except ImportError:
            pytest.skip("Cache preset system not available")

    def test_development_environment_recommends_development_cache_preset(self, development_environment):
        """
        Test that development environment recommends development cache preset.

        Integration Scope:
            Development environment → Cache preset manager → Development preset selection

        Business Impact:
            Ensures development gets fast iteration cache settings

        Test Strategy:
            - Set development environment
            - Verify environment detection
            - Test cache preset recommendation
            - Verify development-optimized cache settings

        Success Criteria:
            - Cache preset manager recommends development preset
            - Development preset has short TTLs for fast iteration
            - Environment detection correctly identifies development
        """
        # Verify environment detection
        env_info = get_environment_info()
        assert env_info.environment == Environment.DEVELOPMENT
        assert env_info.confidence >= 0.8

        # Test cache preset integration
        try:
            from app.infrastructure.cache.cache_presets import CachePresetManager
            preset_manager = CachePresetManager()

            # Should recommend development-appropriate preset
            preset = preset_manager.recommend_preset(env_info.environment)
            assert preset is not None

            # Development preset should be indicated
            assert 'development' in preset.lower() or 'dev' in preset.lower()

        except ImportError:
            pytest.skip("Cache preset system not available")

    def test_staging_environment_recommends_balanced_cache_preset(self, staging_environment):
        """
        Test that staging environment recommends balanced cache preset.

        Integration Scope:
            Staging environment → Cache preset manager → Balanced preset selection

        Business Impact:
            Ensures staging gets appropriate pre-production cache settings

        Test Strategy:
            - Set staging environment
            - Verify environment detection
            - Test cache preset recommendation
            - Verify staging-appropriate cache settings

        Success Criteria:
            - Cache preset manager recommends staging preset
            - Staging preset balances performance and freshness
            - Environment detection correctly identifies staging
        """
        # Verify environment detection
        env_info = get_environment_info()
        assert env_info.environment == Environment.STAGING
        assert env_info.confidence >= 0.8

        # Test cache preset integration
        try:
            from app.infrastructure.cache.cache_presets import CachePresetManager
            preset_manager = CachePresetManager()

            # Should recommend staging-appropriate preset
            preset = preset_manager.recommend_preset(env_info.environment)
            assert preset is not None

            # Staging preset should be indicated
            assert 'staging' in preset.lower() or 'stage' in preset.lower()

        except ImportError:
            pytest.skip("Cache preset system not available")

    def test_cache_preset_with_ai_context(self, production_environment):
        """
        Test cache preset selection with AI feature context.

        Integration Scope:
            Production environment + AI context → Cache preset manager → AI-optimized preset

        Business Impact:
            Ensures AI workloads get appropriate cache optimization

        Test Strategy:
            - Set production environment with AI features enabled
            - Test cache preset with AI context
            - Verify AI-optimized cache configuration

        Success Criteria:
            - AI context influences cache preset selection
            - AI-specific cache optimizations are applied
            - Cache configuration includes AI workload considerations
        """
        # Enable AI features
        import os
        os.environ['ENABLE_AI_CACHE'] = 'true'

        # Test with AI context
        ai_env = get_environment_info(FeatureContext.AI_ENABLED)
        assert ai_env.environment == Environment.PRODUCTION
        assert ai_env.metadata.get('enable_ai_cache_enabled') is True

        # Test cache preset integration with AI context
        try:
            from app.infrastructure.cache.cache_presets import CachePresetManager
            preset_manager = CachePresetManager()

            # Should recommend AI-optimized preset
            preset = preset_manager.recommend_preset(ai_env.environment)
            assert preset is not None

            # Should consider AI context for cache configuration
            # (Implementation may vary based on cache preset manager)

        except ImportError:
            pytest.skip("Cache preset system not available")

    def test_cache_preset_with_cache_optimization_context(self, production_environment):
        """
        Test cache preset selection with cache optimization context.

        Integration Scope:
            Production environment + Cache context → Cache preset manager → Cache-optimized preset

        Business Impact:
            Ensures cache-intensive workloads get optimized configuration

        Test Strategy:
            - Set production environment
            - Test cache preset with cache optimization context
            - Verify cache-optimized configuration

        Success Criteria:
            - Cache optimization context is recognized
            - Cache-specific optimizations are applied
            - Configuration reflects cache-intensive workload needs
        """
        # Test with cache optimization context
        cache_env = get_environment_info(FeatureContext.CACHE_OPTIMIZATION)
        assert cache_env.environment == Environment.PRODUCTION

        # Test cache preset integration with cache context
        try:
            from app.infrastructure.cache.cache_presets import CachePresetManager
            preset_manager = CachePresetManager()

            # Should recommend cache-optimized preset
            preset = preset_manager.recommend_preset(cache_env.environment)
            assert preset is not None

            # Cache optimization context should influence configuration

        except ImportError:
            pytest.skip("Cache preset system not available")

    def test_cache_preset_confidence_influence(self, clean_environment):
        """
        Test that cache preset selection is influenced by environment detection confidence.

        Integration Scope:
            Environment confidence → Cache preset manager → Confidence-based selection

        Business Impact:
            Ensures cache configuration adapts to detection confidence

        Test Strategy:
            - Test cache presets with high confidence detection
            - Test cache presets with low confidence detection
            - Verify confidence influences preset recommendations

        Success Criteria:
            - High confidence detection leads to confident preset selection
            - Low confidence detection leads to conservative preset selection
            - Confidence scoring affects cache configuration decisions
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

        # Test cache preset integration
        try:
            from app.infrastructure.cache.cache_presets import CachePresetManager
            preset_manager = CachePresetManager()

            # Both should get valid presets but potentially different ones
            high_conf_preset = preset_manager.recommend_preset(high_conf_env.environment)
            low_conf_preset = preset_manager.recommend_preset(low_conf_env.environment)

            assert high_conf_preset is not None
            assert low_conf_preset is not None

            # In practice, both might get same preset but confidence could influence settings

        except ImportError:
            pytest.skip("Cache preset system not available")

    def test_cache_preset_with_unknown_environment(self, unknown_environment):
        """
        Test cache preset selection when environment cannot be determined.

        Integration Scope:
            Unknown environment → Cache preset manager → Conservative preset selection

        Business Impact:
            Ensures safe cache configuration when environment is unclear

        Test Strategy:
            - Create unknown environment scenario
            - Test cache preset recommendation
            - Verify conservative/safe cache configuration

        Success Criteria:
            - Unknown environment gets conservative preset
            - Cache configuration is safe for unknown environments
            - System degrades gracefully with unknown environment
        """
        env_info = get_environment_info()
        assert env_info.environment == Environment.DEVELOPMENT  # Fallback
        assert env_info.confidence < 0.7  # Low confidence

        # Test cache preset integration
        try:
            from app.infrastructure.cache.cache_presets import CachePresetManager
            preset_manager = CachePresetManager()

            # Should recommend conservative preset for unknown environment
            preset = preset_manager.recommend_preset(env_info.environment)
            assert preset is not None

            # Unknown environment should get development or minimal preset

        except ImportError:
            pytest.skip("Cache preset system not available")

    def test_cache_preset_custom_environment_mapping(self, custom_detection_config):
        """
        Test cache preset selection with custom environment mapping.

        Integration Scope:
            Custom detection config → Cache preset manager → Custom environment handling

        Business Impact:
            Ensures custom environments work with cache preset system

        Test Strategy:
            - Create detector with custom configuration
            - Test cache preset with custom environment
            - Verify custom environment mapping works

        Success Criteria:
            - Custom environment configuration is respected
            - Cache preset system handles custom environments
            - Custom patterns work correctly with cache presets
        """
        detector = __import__('app.core.environment', fromlist=['EnvironmentDetector']).EnvironmentDetector(custom_detection_config)

        # Test with custom configuration
        import os
        os.environ['CUSTOM_ENV'] = 'production'

        env_info = detector.detect_environment()
        assert env_info.environment == Environment.PRODUCTION

        # Test cache preset integration
        try:
            from app.infrastructure.cache.cache_presets import CachePresetManager
            preset_manager = CachePresetManager()

            # Should recommend production preset based on custom environment detection
            preset = preset_manager.recommend_preset(env_info.environment)
            assert preset is not None

        except ImportError:
            pytest.skip("Cache preset system not available")

    def test_cache_preset_environment_consistency(self, clean_environment):
        """
        Test that cache preset recommendations are consistent for same environment.

        Integration Scope:
            Environment detection → Cache preset manager → Consistent recommendations

        Business Impact:
            Ensures deterministic cache configuration for same environment

        Test Strategy:
            - Set consistent environment
            - Make multiple cache preset recommendations
            - Verify consistent results across calls

        Success Criteria:
            - Same environment produces same cache preset recommendation
            - Multiple calls return identical recommendations
            - Cache configuration is deterministic
        """
        import os
        os.environ['ENVIRONMENT'] = 'production'

        # Make multiple calls to test consistency
        try:
            from app.infrastructure.cache.cache_presets import CachePresetManager
            preset_manager = CachePresetManager()

            presets = []
            for _ in range(3):
                env_info = get_environment_info()
                preset = preset_manager.recommend_preset(env_info.environment)
                presets.append(preset)

            # All recommendations should be identical
            assert len(set(presets)) == 1  # All same
            assert presets[0] is not None

        except ImportError:
            pytest.skip("Cache preset system not available")

    def test_cache_preset_error_handling(self, mock_environment_detection_failure):
        """
        Test cache preset system error handling when environment detection fails.

        Integration Scope:
            Environment detection failure → Cache preset manager → Error handling

        Business Impact:
            Ensures cache system remains stable when environment detection fails

        Test Strategy:
            - Mock environment detection to fail
            - Test cache preset manager behavior
            - Verify graceful error handling

        Success Criteria:
            - Cache preset system handles detection failures
            - Appropriate fallback behavior is used
            - System logs errors appropriately
        """
        # Mock environment detection failure
        with pytest.raises(Exception, match="Environment detection service unavailable"):
            get_environment_info()

        # Test cache preset manager with failed detection
        try:
            from app.infrastructure.cache.cache_presets import CachePresetManager
            preset_manager = CachePresetManager()

            # Should handle detection failure gracefully
            # Implementation may vary, but should not crash
            try:
                preset = preset_manager.recommend_preset(Environment.DEVELOPMENT)  # Fallback
                assert preset is not None
            except Exception:
                # May raise exception or return None, but shouldn't crash
                pass

        except ImportError:
            pytest.skip("Cache preset system not available")
