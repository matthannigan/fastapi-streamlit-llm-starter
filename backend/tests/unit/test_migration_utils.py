"""
Unit tests for resilience configuration migration utilities.

Tests the migration analysis, preset recommendation, and script generation
functionality for legacy-to-preset configuration migration.
"""

import pytest
import json
import os
from unittest.mock import patch, MagicMock

from app.migration_utils import (
    LegacyConfigAnalyzer,
    ConfigurationMigrator,
    MigrationRecommendation,
    MigrationConfidence,
    migrator
)


class TestLegacyConfigAnalyzer:
    """Test legacy configuration detection and analysis."""
    
    def test_detect_empty_legacy_configuration(self):
        """Test detection when no legacy variables are present."""
        analyzer = LegacyConfigAnalyzer()
        env_vars = {"SOME_OTHER_VAR": "value"}
        
        result = analyzer.detect_legacy_configuration(env_vars)
        assert result == {}
    
    def test_detect_basic_legacy_configuration(self):
        """Test detection of basic legacy configuration."""
        analyzer = LegacyConfigAnalyzer()
        env_vars = {
            "RETRY_MAX_ATTEMPTS": "5",
            "CIRCUIT_BREAKER_FAILURE_THRESHOLD": "10",
            "CIRCUIT_BREAKER_RECOVERY_TIMEOUT": "120",
            "DEFAULT_RESILIENCE_STRATEGY": "conservative"
        }
        
        result = analyzer.detect_legacy_configuration(env_vars)
        
        expected = {
            "retry_attempts": 5,
            "circuit_breaker_threshold": 10,
            "recovery_timeout": 120,
            "default_strategy": "conservative"
        }
        assert result == expected
    
    def test_detect_operation_specific_strategies(self):
        """Test detection of operation-specific strategy overrides."""
        analyzer = LegacyConfigAnalyzer()
        env_vars = {
            "SUMMARIZE_RESILIENCE_STRATEGY": "conservative",
            "SENTIMENT_RESILIENCE_STRATEGY": "aggressive",
            "QA_RESILIENCE_STRATEGY": "critical"
        }
        
        result = analyzer.detect_legacy_configuration(env_vars)
        
        expected = {
            "operation_overrides": {
                "summarize": "conservative",
                "sentiment": "aggressive",
                "qa": "critical"
            }
        }
        assert result == expected
    
    def test_detect_advanced_retry_configuration(self):
        """Test detection of advanced retry configuration parameters."""
        analyzer = LegacyConfigAnalyzer()
        env_vars = {
            "RETRY_EXPONENTIAL_MULTIPLIER": "1.5",
            "RETRY_EXPONENTIAL_MIN": "2.0",
            "RETRY_EXPONENTIAL_MAX": "30.0",
            "RETRY_JITTER_ENABLED": "true",
            "RETRY_JITTER_MAX": "3.0",
            "RETRY_MAX_DELAY": "180"
        }
        
        result = analyzer.detect_legacy_configuration(env_vars)
        
        expected = {
            "exponential_multiplier": 1.5,
            "exponential_min": 2.0,
            "exponential_max": 30.0,
            "jitter_enabled": True,
            "jitter_max": 3.0,
            "max_delay_seconds": 180
        }
        assert result == expected
    
    def test_detect_with_invalid_values(self):
        """Test detection handles invalid values gracefully."""
        analyzer = LegacyConfigAnalyzer()
        env_vars = {
            "RETRY_MAX_ATTEMPTS": "invalid",  # Invalid integer
            "RETRY_EXPONENTIAL_MULTIPLIER": "not_a_float",  # Invalid float
            "CIRCUIT_BREAKER_FAILURE_THRESHOLD": "5"  # Valid value
        }
        
        result = analyzer.detect_legacy_configuration(env_vars)
        
        # Should only include valid values
        expected = {
            "circuit_breaker_threshold": 5
        }
        assert result == expected
    
    def test_recommend_preset_no_legacy_config(self):
        """Test preset recommendation when no legacy config exists."""
        analyzer = LegacyConfigAnalyzer()
        
        recommendation = analyzer.recommend_preset({})
        
        assert recommendation.recommended_preset == "simple"
        assert recommendation.confidence == MigrationConfidence.HIGH
        assert "No legacy configuration detected" in recommendation.reasoning
        assert recommendation.custom_overrides is None
    
    def test_recommend_preset_development_pattern(self):
        """Test recommendation for development-like configuration."""
        analyzer = LegacyConfigAnalyzer()
        legacy_config = {
            "retry_attempts": 2,
            "circuit_breaker_threshold": 3,
            "recovery_timeout": 30,
            "default_strategy": "aggressive"
        }
        
        recommendation = analyzer.recommend_preset(legacy_config)
        
        assert recommendation.recommended_preset == "development"
        assert recommendation.confidence in [MigrationConfidence.HIGH, MigrationConfidence.MEDIUM]
        assert "development" in recommendation.reasoning.lower()
    
    def test_recommend_preset_production_pattern(self):
        """Test recommendation for production-like configuration."""
        analyzer = LegacyConfigAnalyzer()
        legacy_config = {
            "retry_attempts": 5,
            "circuit_breaker_threshold": 10,
            "recovery_timeout": 120,
            "default_strategy": "conservative",
            "operation_overrides": {
                "qa": "critical",
                "summarize": "conservative"
            }
        }
        
        recommendation = analyzer.recommend_preset(legacy_config)
        
        assert recommendation.recommended_preset == "production"
        assert recommendation.confidence in [MigrationConfidence.HIGH, MigrationConfidence.MEDIUM]
        assert "production" in recommendation.reasoning.lower()
    
    def test_recommend_preset_with_custom_overrides(self):
        """Test recommendation generates custom overrides for non-standard values."""
        analyzer = LegacyConfigAnalyzer()
        legacy_config = {
            "retry_attempts": 7,  # Different from all presets
            "circuit_breaker_threshold": 8,  # Different from all presets
            "max_delay_seconds": 300  # Custom parameter
        }
        
        recommendation = analyzer.recommend_preset(legacy_config)
        
        assert recommendation.custom_overrides is not None
        assert "retry_attempts" in recommendation.custom_overrides
        assert "circuit_breaker_threshold" in recommendation.custom_overrides
        assert "max_delay_seconds" in recommendation.custom_overrides
        assert recommendation.custom_overrides["retry_attempts"] == 7
        assert recommendation.custom_overrides["circuit_breaker_threshold"] == 8
        assert recommendation.custom_overrides["max_delay_seconds"] == 300
    
    def test_generate_migration_warnings(self):
        """Test generation of migration warnings for problematic configurations."""
        analyzer = LegacyConfigAnalyzer()
        legacy_config = {
            "retry_attempts": 10,  # Very high
            "circuit_breaker_threshold": 2,  # Very low
            "default_strategy": "aggressive"
        }
        
        recommendation = analyzer.recommend_preset(legacy_config)
        
        assert len(recommendation.warnings) > 0
        warning_text = " ".join(recommendation.warnings)
        assert "high retry attempts" in warning_text.lower() or "significant latency" in warning_text.lower()
        assert "low circuit breaker threshold" in warning_text.lower() or "frequent" in warning_text.lower()
    
    def test_generate_migration_steps(self):
        """Test generation of detailed migration steps."""
        analyzer = LegacyConfigAnalyzer()
        legacy_config = {
            "retry_attempts": 4,
            "default_strategy": "balanced"
        }
        
        recommendation = analyzer.recommend_preset(legacy_config)
        
        assert len(recommendation.migration_steps) > 0
        steps_text = " ".join(recommendation.migration_steps)
        assert "RESILIENCE_PRESET" in steps_text
        assert "remove legacy" in steps_text.lower()
        assert "test" in steps_text.lower()
    
    def test_preset_scoring_calculation(self):
        """Test preset scoring calculation logic."""
        analyzer = LegacyConfigAnalyzer()
        
        # Configuration that exactly matches simple preset
        simple_config = {
            "retry_attempts": 3,
            "circuit_breaker_threshold": 5,
            "recovery_timeout": 60,
            "default_strategy": "balanced"
        }
        
        scores = analyzer._calculate_preset_scores(simple_config)
        
        # Simple preset should have highest score
        assert scores["simple"] >= scores["development"]
        assert scores["simple"] >= scores["production"]
        assert scores["simple"] > 0.8  # Should be high confidence match


class TestConfigurationMigrator:
    """Test configuration migration orchestration."""
    
    def test_analyze_current_environment(self):
        """Test analysis of current environment variables."""
        migrator_instance = ConfigurationMigrator()
        
        with patch.dict(os.environ, {
            "RETRY_MAX_ATTEMPTS": "3",
            "CIRCUIT_BREAKER_FAILURE_THRESHOLD": "5"
        }):
            recommendation = migrator_instance.analyze_current_environment()
            
            assert isinstance(recommendation, MigrationRecommendation)
            assert recommendation.recommended_preset in ["simple", "development", "production"]
            assert isinstance(recommendation.confidence, MigrationConfidence)
    
    def test_generate_bash_migration_script(self):
        """Test generation of bash migration script."""
        migrator_instance = ConfigurationMigrator()
        
        recommendation = MigrationRecommendation(
            recommended_preset="simple",
            confidence=MigrationConfidence.HIGH,
            reasoning="Test reasoning",
            custom_overrides={"retry_attempts": 4},
            warnings=["Test warning"],
            migration_steps=["Step 1", "Step 2"]
        )
        
        script = migrator_instance.generate_migration_script(recommendation, "bash")
        
        assert "#!/bin/bash" in script
        assert "RESILIENCE_PRESET=simple" in script
        assert "unset RETRY_MAX_ATTEMPTS" in script
        assert "RESILIENCE_CUSTOM_CONFIG" in script
        assert '"retry_attempts": 4' in script
        assert "Test warning" in script
    
    def test_generate_env_file_migration(self):
        """Test generation of .env file migration."""
        migrator_instance = ConfigurationMigrator()
        
        recommendation = MigrationRecommendation(
            recommended_preset="production",
            confidence=MigrationConfidence.MEDIUM,
            reasoning="Test reasoning"
        )
        
        env_content = migrator_instance.generate_migration_script(recommendation, "env")
        
        assert "RESILIENCE_PRESET=production" in env_content
        assert "# Legacy variables" in env_content
        assert "# RETRY_MAX_ATTEMPTS=" in env_content
    
    def test_generate_docker_migration(self):
        """Test generation of Docker environment migration."""
        migrator_instance = ConfigurationMigrator()
        
        recommendation = MigrationRecommendation(
            recommended_preset="development",
            confidence=MigrationConfidence.HIGH,
            reasoning="Test reasoning",
            custom_overrides={"circuit_breaker_threshold": 3}
        )
        
        docker_content = migrator_instance.generate_migration_script(recommendation, "docker")
        
        assert "environment:" in docker_content
        assert "- RESILIENCE_PRESET=development" in docker_content
        assert "RESILIENCE_CUSTOM_CONFIG" in docker_content
    
    def test_generate_invalid_format_raises_error(self):
        """Test that invalid format raises appropriate error."""
        migrator_instance = ConfigurationMigrator()
        
        recommendation = MigrationRecommendation(
            recommended_preset="simple",
            confidence=MigrationConfidence.HIGH,
            reasoning="Test"
        )
        
        with pytest.raises(ValueError, match="Unsupported output format"):
            migrator_instance.generate_migration_script(recommendation, "invalid")


class TestMigrationIntegration:
    """Test integration scenarios for migration utilities."""
    
    def test_full_migration_workflow_development(self):
        """Test complete migration workflow for development scenario."""
        env_vars = {
            "RETRY_MAX_ATTEMPTS": "2",
            "CIRCUIT_BREAKER_FAILURE_THRESHOLD": "3",
            "CIRCUIT_BREAKER_RECOVERY_TIMEOUT": "30",
            "DEFAULT_RESILIENCE_STRATEGY": "aggressive",
            "SENTIMENT_RESILIENCE_STRATEGY": "aggressive"
        }
        
        # Analyze configuration
        analyzer = LegacyConfigAnalyzer()
        legacy_config = analyzer.detect_legacy_configuration(env_vars)
        
        # Get recommendation
        recommendation = analyzer.recommend_preset(legacy_config)
        
        # Generate migration script
        migrator_instance = ConfigurationMigrator()
        script = migrator_instance.generate_migration_script(recommendation, "bash")
        
        # Verify workflow results
        assert recommendation.recommended_preset == "development"
        assert "RESILIENCE_PRESET=development" in script
        assert "unset RETRY_MAX_ATTEMPTS" in script
    
    def test_full_migration_workflow_production(self):
        """Test complete migration workflow for production scenario."""
        env_vars = {
            "RETRY_MAX_ATTEMPTS": "5",
            "CIRCUIT_BREAKER_FAILURE_THRESHOLD": "10",
            "CIRCUIT_BREAKER_RECOVERY_TIMEOUT": "120",
            "DEFAULT_RESILIENCE_STRATEGY": "conservative",
            "QA_RESILIENCE_STRATEGY": "critical",
            "SUMMARIZE_RESILIENCE_STRATEGY": "conservative"
        }
        
        # Analyze configuration
        analyzer = LegacyConfigAnalyzer()
        legacy_config = analyzer.detect_legacy_configuration(env_vars)
        
        # Get recommendation
        recommendation = analyzer.recommend_preset(legacy_config)
        
        # Generate migration script
        migrator_instance = ConfigurationMigrator()
        env_file = migrator_instance.generate_migration_script(recommendation, "env")
        
        # Verify workflow results
        assert recommendation.recommended_preset == "production"
        assert "RESILIENCE_PRESET=production" in env_file
        assert recommendation.confidence in [MigrationConfidence.HIGH, MigrationConfidence.MEDIUM]
    
    def test_migration_with_complex_custom_overrides(self):
        """Test migration with complex custom configuration requirements."""
        env_vars = {
            "RETRY_MAX_ATTEMPTS": "7",  # Custom value
            "CIRCUIT_BREAKER_FAILURE_THRESHOLD": "8",  # Custom value
            "RETRY_EXPONENTIAL_MULTIPLIER": "2.0",  # Custom parameter
            "RETRY_JITTER_ENABLED": "false",  # Custom parameter
            "SUMMARIZE_RESILIENCE_STRATEGY": "critical",  # Custom override
            "SENTIMENT_RESILIENCE_STRATEGY": "aggressive"  # Custom override
        }
        
        # Run migration analysis
        analyzer = LegacyConfigAnalyzer()
        legacy_config = analyzer.detect_legacy_configuration(env_vars)
        recommendation = analyzer.recommend_preset(legacy_config)
        
        # Verify custom overrides are properly captured
        assert recommendation.custom_overrides is not None
        assert "retry_attempts" in recommendation.custom_overrides
        assert "circuit_breaker_threshold" in recommendation.custom_overrides
        assert "exponential_multiplier" in recommendation.custom_overrides
        assert "jitter_enabled" in recommendation.custom_overrides
        
        # Check for operation overrides - only if they differ from preset defaults
        if "operation_overrides" in recommendation.custom_overrides:
            custom_ops = recommendation.custom_overrides["operation_overrides"]
            # At least one operation should have overrides
            assert len(custom_ops) > 0
    
    @patch('app.migration_utils.os.environ')
    def test_global_migrator_instance(self, mock_environ):
        """Test the global migrator instance functionality."""
        mock_environ.copy.return_value = {
            "RETRY_MAX_ATTEMPTS": "3",
            "DEFAULT_RESILIENCE_STRATEGY": "balanced"
        }
        
        # Test global migrator
        recommendation = migrator.analyze_current_environment()
        
        assert isinstance(recommendation, MigrationRecommendation)
        assert recommendation.recommended_preset in ["simple", "development", "production"]
    
    def test_edge_case_empty_environment(self):
        """Test migration analysis with completely empty environment."""
        analyzer = LegacyConfigAnalyzer()
        recommendation = analyzer.recommend_preset({})
        
        assert recommendation.recommended_preset == "simple"
        assert recommendation.confidence == MigrationConfidence.HIGH
        assert recommendation.custom_overrides is None
        assert len(recommendation.warnings) == 0
    
    def test_edge_case_partial_configuration(self):
        """Test migration with only partial legacy configuration."""
        legacy_config = {
            "retry_attempts": 4
            # Missing other typical configuration
        }
        
        analyzer = LegacyConfigAnalyzer()
        recommendation = analyzer.recommend_preset(legacy_config)
        
        assert recommendation.recommended_preset in ["simple", "development", "production"]
        assert isinstance(recommendation.confidence, MigrationConfidence)
        assert recommendation.custom_overrides is not None
        assert "retry_attempts" in recommendation.custom_overrides


class TestMigrationRecommendation:
    """Test MigrationRecommendation data class."""
    
    def test_migration_recommendation_creation(self):
        """Test creation of migration recommendation."""
        recommendation = MigrationRecommendation(
            recommended_preset="simple",
            confidence=MigrationConfidence.HIGH,
            reasoning="Test reasoning"
        )
        
        assert recommendation.recommended_preset == "simple"
        assert recommendation.confidence == MigrationConfidence.HIGH
        assert recommendation.reasoning == "Test reasoning"
        assert recommendation.warnings == []
        assert recommendation.migration_steps == []
        assert recommendation.custom_overrides is None
    
    def test_migration_recommendation_with_all_fields(self):
        """Test creation with all fields populated."""
        custom_overrides = {"retry_attempts": 5}
        warnings = ["Warning 1", "Warning 2"]
        steps = ["Step 1", "Step 2", "Step 3"]
        
        recommendation = MigrationRecommendation(
            recommended_preset="production",
            confidence=MigrationConfidence.MEDIUM,
            reasoning="Complex migration",
            custom_overrides=custom_overrides,
            warnings=warnings,
            migration_steps=steps
        )
        
        assert recommendation.custom_overrides == custom_overrides
        assert recommendation.warnings == warnings
        assert recommendation.migration_steps == steps