"""
Unit tests for environment-aware preset recommendations.

Tests the enhanced environment detection and recommendation functionality
added in Phase 3 of the resilience configuration simplification project.
"""

import pytest
import os
from unittest.mock import patch, MagicMock

from app.infrastructure.resilience.presets import PresetManager, EnvironmentRecommendation


class TestEnvironmentRecommendations:
    """Test environment-aware preset recommendations."""
    
    def test_exact_environment_matches(self):
        """Test exact environment name matches with high confidence."""
        manager = PresetManager()
        
        test_cases = [
            ("development", "development", 0.95),
            ("dev", "development", 0.90),
            ("testing", "development", 0.85),
            ("test", "development", 0.85),
            ("staging", "production", 0.90),
            ("stage", "production", 0.85),
            ("production", "production", 0.95),
            ("prod", "production", 0.90),
            ("live", "production", 0.85),
        ]
        
        for env_name, expected_preset, min_confidence in test_cases:
            recommendation = manager.recommend_preset_with_details(env_name)
            
            assert recommendation.preset_name == expected_preset
            assert recommendation.confidence >= min_confidence
            assert recommendation.environment_detected == env_name
            assert len(recommendation.reasoning) > 0
    
    def test_pattern_matching_development(self):
        """Test pattern matching for development-like environments."""
        manager = PresetManager()
        
        dev_patterns = [
            "dev-feature-branch",
            "local-development",
            "test-environment",
            "sandbox-testing",
            "demo-app"
        ]
        
        for env_name in dev_patterns:
            recommendation = manager.recommend_preset_with_details(env_name)
            
            assert recommendation.preset_name == "development"
            assert recommendation.confidence >= 0.70
            assert "development pattern" in recommendation.reasoning.lower()
    
    def test_pattern_matching_production(self):
        """Test pattern matching for production-like environments."""
        manager = PresetManager()
        
        prod_patterns = [
            "prod-east-1",
            "live-api",
            "release-v2",
            "stable-main",
            "master-branch"
        ]
        
        for env_name in prod_patterns:
            recommendation = manager.recommend_preset_with_details(env_name)
            
            assert recommendation.preset_name == "production"
            assert recommendation.confidence >= 0.70
            assert "production pattern" in recommendation.reasoning.lower()
    
    def test_pattern_matching_staging(self):
        """Test pattern matching for staging environments maps to production preset."""
        manager = PresetManager()
        
        staging_patterns = [
            "staging-env",
            "pre-prod",
            "preprod-testing",
            "uat-environment",
            "integration-tests"
        ]
        
        for env_name in staging_patterns:
            recommendation = manager.recommend_preset_with_details(env_name)
            
            assert recommendation.preset_name == "production"
            assert recommendation.confidence >= 0.70
            assert "staging pattern" in recommendation.reasoning.lower()
    
    def test_unknown_environment_fallback(self):
        """Test fallback behavior for unknown environment patterns."""
        manager = PresetManager()
        
        unknown_envs = [
            "weird-env-name",
            "custom123",
            "xyz"
        ]
        
        for env_name in unknown_envs:
            recommendation = manager.recommend_preset_with_details(env_name)
            
            assert recommendation.preset_name == "simple"
            assert recommendation.confidence <= 0.50
            assert "unknown" in recommendation.reasoning.lower() or "defaulting" in recommendation.reasoning.lower()
    
    @patch('os.getenv')
    def test_auto_detection_from_environment_variables(self, mock_getenv):
        """Test auto-detection from common environment variables."""
        manager = PresetManager()
        
        # Test NODE_ENV detection
        mock_getenv.side_effect = lambda var, default='': {
            'NODE_ENV': 'production',
            'ENV': None,
            'ENVIRONMENT': None,
            'DEBUG': None,
            'HOST': None
        }.get(var, default)
        
        recommendation = manager.recommend_preset_with_details(None)
        
        assert recommendation.preset_name == "production"
        assert recommendation.confidence >= 0.85
        assert "auto-detected" in recommendation.environment_detected.lower()
    
    @patch('os.getenv')
    def test_auto_detection_development_indicators(self, mock_getenv):
        """Test auto-detection using development indicators."""
        manager = PresetManager()
        
        # Mock development indicators
        mock_getenv.side_effect = lambda var, default='': {
            'DEBUG': 'true',
            'HOST': 'localhost',
            'NODE_ENV': None,
            'ENV': None
        }.get(var, default)
        
        with patch('os.path.exists') as mock_exists:
            mock_exists.side_effect = lambda path: path == '.env'
            
            recommendation = manager.recommend_preset_with_details(None)
            
            assert recommendation.preset_name == "development"
            assert recommendation.confidence >= 0.70
            assert "development indicators detected" in recommendation.reasoning.lower()
    
    @patch('os.getenv')
    @patch('os.path.exists')
    def test_auto_detection_production_indicators(self, mock_exists, mock_getenv):
        """Test auto-detection using production indicators."""
        manager = PresetManager()
        
        # Mock production indicators
        mock_getenv.side_effect = lambda var, default='': {
            'DEBUG': 'false',
            'PRODUCTION': 'true',
            'DATABASE_URL': 'postgres://production-db:5432/app',
            'NODE_ENV': None
        }.get(var, default)
        
        # Mock file existence to avoid dev indicators
        mock_exists.return_value = False
        
        recommendation = manager.recommend_preset_with_details(None)
        
        assert recommendation.preset_name == "production"
        assert recommendation.confidence >= 0.70
        assert "production indicators detected" in recommendation.reasoning.lower()
    
    @patch('os.getenv')
    @patch('os.path.exists')
    def test_auto_detection_fallback_to_simple(self, mock_exists, mock_getenv):
        """Test auto-detection fallback when no clear indicators found."""
        manager = PresetManager()
        
        # Mock no clear indicators
        mock_getenv.return_value = None
        mock_exists.return_value = False
        
        recommendation = manager.recommend_preset_with_details(None)
        
        assert recommendation.preset_name == "simple"
        assert recommendation.confidence == 0.50
        assert "no clear environment indicators" in recommendation.reasoning.lower()
        assert "unknown (auto-detected)" in recommendation.environment_detected
    
    def test_recommendation_structure(self):
        """Test that recommendation structure contains all required fields."""
        manager = PresetManager()
        
        recommendation = manager.recommend_preset_with_details("production")
        
        # Verify NamedTuple structure
        assert hasattr(recommendation, 'preset_name')
        assert hasattr(recommendation, 'confidence')
        assert hasattr(recommendation, 'reasoning')
        assert hasattr(recommendation, 'environment_detected')
        
        # Verify types
        assert isinstance(recommendation.preset_name, str)
        assert isinstance(recommendation.confidence, float)
        assert isinstance(recommendation.reasoning, str)
        assert isinstance(recommendation.environment_detected, str)
        
        # Verify constraints
        assert 0.0 <= recommendation.confidence <= 1.0
        assert len(recommendation.reasoning) > 0
        assert recommendation.preset_name in ['simple', 'development', 'production']
    
    def test_legacy_recommend_preset_method(self):
        """Test that legacy recommend_preset method still works."""
        manager = PresetManager()
        
        # Test legacy method returns just the preset name
        result = manager.recommend_preset("development")
        assert result == "development"
        assert isinstance(result, str)
        
        # Test with auto-detection
        result = manager.recommend_preset(None)
        assert result in ['simple', 'development', 'production']
        assert isinstance(result, str)
    
    def test_case_insensitive_environment_matching(self):
        """Test that environment matching is case insensitive."""
        manager = PresetManager()
        
        test_cases = [
            "DEVELOPMENT",
            "Development", 
            "dEvElOpMeNt",
            "DEV",
            "Dev"
        ]
        
        for env_name in test_cases:
            recommendation = manager.recommend_preset_with_details(env_name)
            assert recommendation.preset_name == "development"
    
    def test_whitespace_handling(self):
        """Test that environment names with whitespace are handled correctly."""
        manager = PresetManager()
        
        test_cases = [
            "  development  ",
            "\tproduction\t",
            "\nstaging\n"
        ]
        
        expected = ["development", "production", "production"]
        
        for env_name, expected_preset in zip(test_cases, expected):
            recommendation = manager.recommend_preset_with_details(env_name)
            assert recommendation.preset_name == expected_preset

    @patch.dict(os.environ, {
        'ENVIRONMENT': 'staging',
        'DEBUG': 'false'
    })
    def test_environment_variable_priority(self):
        """Test that explicit environment variables take priority over indicators."""
        manager = PresetManager()
        
        # Even though DEBUG=false (production indicator), 
        # explicit ENVIRONMENT=staging should take priority
        recommendation = manager.recommend_preset_with_details(None)
        
        assert recommendation.preset_name == "production"  # staging maps to production preset
        assert "staging" in recommendation.environment_detected.lower()


class TestEnvironmentRecommendationIntegration:
    """Integration tests for environment recommendation system."""
    
    def test_recommendation_affects_preset_loading(self):
        """Test that recommendations work with actual preset loading."""
        manager = PresetManager()
        
        # Get recommendation
        recommendation = manager.recommend_preset_with_details("production")
        
        # Load the recommended preset
        preset = manager.get_preset(recommendation.preset_name)
        
        # Verify preset characteristics match production expectations
        assert preset.retry_attempts >= 3  # Production should have adequate retries
        assert preset.circuit_breaker_threshold >= 5  # Production should be tolerant
        assert preset.default_strategy.value in ["conservative", "balanced"]
    
    def test_all_recommendations_return_valid_presets(self):
        """Test that all possible recommendations return valid preset names."""
        manager = PresetManager()
        available_presets = set(manager.list_presets())
        
        # Test various environment names
        test_environments = [
            "dev", "development", "test", "testing",
            "staging", "stage", "prod", "production", "live",
            "unknown-env", "custom123", None  # Include auto-detection
        ]
        
        for env in test_environments:
            if env is None:
                with patch('os.getenv', return_value=None), patch('os.path.exists', return_value=False):
                    recommendation = manager.recommend_preset_with_details(env)
            else:
                recommendation = manager.recommend_preset_with_details(env)
            
            assert recommendation.preset_name in available_presets
            
            # Verify we can actually load the recommended preset
            preset = manager.get_preset(recommendation.preset_name)
            assert preset is not None
    
    def test_confidence_scoring_consistency(self):
        """Test that confidence scoring is consistent and logical."""
        manager = PresetManager()
        
        # Exact matches should have highest confidence
        exact_recommendation = manager.recommend_preset_with_details("production")
        pattern_recommendation = manager.recommend_preset_with_details("prod-env-123")
        unknown_recommendation = manager.recommend_preset_with_details("weird-unknown-env")
        
        assert exact_recommendation.confidence > pattern_recommendation.confidence
        assert pattern_recommendation.confidence > unknown_recommendation.confidence
        
        # All confidence scores should be valid
        for rec in [exact_recommendation, pattern_recommendation, unknown_recommendation]:
            assert 0.0 <= rec.confidence <= 1.0