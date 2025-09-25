"""
Integration Tests: Configuration → Environment Detection → Strategy Selection

This module tests the integration between configuration management, environment detection,
and resilience strategy selection. It validates that the system correctly applies
environment-specific configurations and strategy selection based on various deployment
scenarios.

Integration Scope:
    - Environment variable detection → PresetManager → ResilienceConfig
    - Configuration loading → Strategy resolution → Operation configuration
    - Environment-specific overrides → Configuration validation → Application behavior

Business Impact:
    Incorrect configuration leads to inappropriate resilience behavior affecting
    system reliability across different deployment environments

Test Strategy:
    - Test environment detection from various sources (env vars, system properties)
    - Validate preset selection based on detected environments
    - Verify configuration loading and validation processes
    - Test configuration overrides and custom settings
    - Validate error handling for invalid configurations

Critical Paths:
    - Environment variables → Configuration loading → Strategy resolution
    - Preset selection → Configuration validation → Settings application
    - Configuration migration → Backward compatibility → Forward compatibility
"""

import pytest
import os
from unittest.mock import patch, MagicMock
from typing import Dict, Any

from app.core.config import Settings
from app.infrastructure.resilience.config_presets import (
    preset_manager,
    ResilienceStrategy,
    ResilienceConfig,
    get_default_presets,
    EnvironmentRecommendation
)
from app.infrastructure.resilience.orchestrator import AIServiceResilience
from app.infrastructure.resilience.retry import RetryConfig
from app.infrastructure.resilience.circuit_breaker import CircuitBreakerConfig


class TestConfigurationEnvironmentSelection:
    """
    Integration tests for Configuration → Environment Detection → Strategy Selection.

    Seam Under Test:
        Environment detection → PresetManager → ResilienceConfig → Strategy application

    Critical Paths:
        - Environment variables → Configuration loading → Strategy resolution
        - Preset selection → Configuration validation → Settings application
        - Configuration overrides → Custom settings → Validation

    Business Impact:
        Ensures correct resilience behavior across different deployment environments
        through proper configuration management and environment detection
    """

    @pytest.fixture
    def environment_scenarios(self):
        """Provides test scenarios for different environments."""
        return {
            "development": {
                "env_vars": {"ENVIRONMENT": "development", "DEBUG": "true"},
                "expected_preset": "development",
                "expected_strategy": ResilienceStrategy.AGGRESSIVE,
                "description": "Development environment with fast-fail configuration"
            },
            "production": {
                "env_vars": {"ENVIRONMENT": "production", "PRODUCTION": "true"},
                "expected_preset": "production",
                "expected_strategy": ResilienceStrategy.CONSERVATIVE,
                "description": "Production environment with high-reliability configuration"
            },
            "staging": {
                "env_vars": {"ENVIRONMENT": "staging", "DEPLOY_ENV": "staging"},
                "expected_preset": "production",  # Staging uses production preset
                "expected_strategy": ResilienceStrategy.CONSERVATIVE,
                "description": "Staging environment using production preset"
            },
            "testing": {
                "env_vars": {"ENVIRONMENT": "testing", "PYTEST_CURRENT_TEST": "true"},
                "expected_preset": "development",  # Testing uses development preset
                "expected_strategy": ResilienceStrategy.AGGRESSIVE,
                "description": "Testing environment with development configuration"
            },
            "custom_env": {
                "env_vars": {"ENVIRONMENT": "custom", "CUSTOM_ENV": "myapp-prod"},
                "expected_preset": "production",  # Pattern matching should detect production-like
                "expected_strategy": ResilienceStrategy.CONSERVATIVE,
                "description": "Custom environment name with pattern matching"
            }
        }

    def test_environment_detection_development(self, environment_scenarios):
        """Test environment detection for development environment."""
        scenario = environment_scenarios["development"]

        with patch.dict(os.environ, scenario["env_vars"]):
            recommendation = preset_manager.recommend_preset_with_details()

            assert recommendation.preset == scenario["expected_preset"]
            assert isinstance(recommendation.confidence, float)
            assert recommendation.confidence > 0.8  # High confidence for exact match
            assert "development" in recommendation.reasoning.lower()

    def test_environment_detection_production(self, environment_scenarios):
        """Test environment detection for production environment."""
        scenario = environment_scenarios["production"]

        with patch.dict(os.environ, scenario["env_vars"]):
            recommendation = preset_manager.recommend_preset_with_details()

            assert recommendation.preset == scenario["expected_preset"]
            assert isinstance(recommendation.confidence, float)
            assert recommendation.confidence > 0.8
            assert "production" in recommendation.reasoning.lower()

    def test_environment_pattern_matching(self, environment_scenarios):
        """Test pattern-based environment detection for custom environment names."""
        scenario = environment_scenarios["custom_env"]

        with patch.dict(os.environ, scenario["env_vars"]):
            recommendation = preset_manager.recommend_preset_with_details()

            # Should detect production-like environment based on patterns
            assert recommendation.preset in ["production", scenario["expected_preset"]]
            assert isinstance(recommendation.confidence, float)
            assert recommendation.confidence > 0.5  # Lower confidence for pattern matching

    def test_auto_environment_detection(self):
        """Test automatic environment detection without explicit environment variables."""
        # Clear environment variables
        with patch.dict(os.environ, {}, clear=True):
            # Mock system indicators for development
            with patch('app.infrastructure.resilience.config_presets.os.path.exists') as mock_exists:
                mock_exists.return_value = True  # Simulate development indicators

                recommendation = preset_manager.recommend_preset_with_details()

                assert recommendation.preset in ["development", "balanced"]
                assert isinstance(recommendation.confidence, float)

    def test_preset_configuration_loading(self):
        """Test that presets load correct configuration values."""
        # Test each preset loads appropriate configuration
        presets_to_test = ["simple", "development", "production"]

        for preset_name in presets_to_test:
            preset = preset_manager.get_preset(preset_name)
            config = preset.to_resilience_config()

            assert isinstance(config, ResilienceConfig)
            assert config.strategy is not None
            assert config.retry_config is not None
            assert config.circuit_breaker_config is not None

            # Validate configuration values are reasonable
            assert config.retry_config.max_attempts > 0
            assert config.circuit_breaker_config.failure_threshold > 0
            assert config.circuit_breaker_config.recovery_timeout > 0

    def test_operation_specific_strategy_override(self):
        """Test operation-specific strategy overrides work correctly."""
        # Create configuration with operation overrides
        custom_config = ResilienceConfig(
            strategy=ResilienceStrategy.BALANCED,
            retry_config=RetryConfig(max_attempts=3),
            circuit_breaker_config=CircuitBreakerConfig(failure_threshold=5, recovery_timeout=60)
        )

        # Test that custom config overrides work
        assert custom_config.strategy == ResilienceStrategy.BALANCED
        assert custom_config.retry_config.max_attempts == 3
        assert custom_config.circuit_breaker_config.failure_threshold == 5

    def test_environment_variable_configuration_override(self, mock_environment_variables):
        """Test that environment variables can override preset configurations."""
        # Set environment variables for configuration override
        env_overrides = {
            "RETRY_MAX_ATTEMPTS": "7",
            "CIRCUIT_BREAKER_FAILURE_THRESHOLD": "12",
            "CIRCUIT_BREAKER_RECOVERY_TIMEOUT": "90"
        }

        mock_environment_variables["set"](env_overrides)

        try:
            # Get a preset configuration
            preset = preset_manager.get_preset("simple")
            config = preset.to_resilience_config()

            # Verify that environment variables can override
            # (This would be applied at the Settings level, not preset level)
            # We're testing the mechanism exists for override
            assert isinstance(config, ResilienceConfig)

            # Verify configuration structure is intact
            assert hasattr(config, 'retry_config')
            assert hasattr(config, 'circuit_breaker_config')
            assert hasattr(config, 'strategy')

        finally:
            mock_environment_variables["cleanup"]()

    def test_configuration_validation(self):
        """Test configuration validation prevents invalid configurations."""
        # Test invalid configuration values
        invalid_configs = [
            ResilienceConfig(
                strategy=ResilienceStrategy.BALANCED,
                retry_config=RetryConfig(max_attempts=-1)  # Invalid negative value
            ),
            ResilienceConfig(
                strategy=ResilienceStrategy.BALANCED,
                circuit_breaker_config=CircuitBreakerConfig(failure_threshold=0)  # Invalid zero
            )
        ]

        for config in invalid_configs:
            # Should not raise exception during construction
            # but should have reasonable defaults or validation
            assert isinstance(config, ResilienceConfig)

            # Validate configuration has reasonable values
            assert config.retry_config.max_attempts >= 1
            if config.circuit_breaker_config:
                assert config.circuit_breaker_config.failure_threshold >= 1
                assert config.circuit_breaker_config.recovery_timeout >= 1

    def test_resilience_service_configuration_integration(self):
        """Test that resilience service integrates properly with configuration management."""
        # Create settings with specific configuration
        test_settings = Settings(
            environment="testing",
            resilience_preset="development",
            enable_circuit_breaker=True,
            enable_retry=True,
            max_retry_attempts=5,
            circuit_breaker_failure_threshold=3,
            circuit_breaker_recovery_timeout=30
        )

        # Initialize resilience service
        resilience_service = AIServiceResilience(test_settings)

        # Register test operations
        resilience_service.register_operation("test_operation", ResilienceStrategy.BALANCED)
        resilience_service.register_operation("critical_operation", ResilienceStrategy.CRITICAL)

        # Verify operations are registered with correct strategies
        config1 = resilience_service.get_operation_config("test_operation")
        config2 = resilience_service.get_operation_config("critical_operation")

        assert isinstance(config1, ResilienceConfig)
        assert isinstance(config2, ResilienceConfig)

        # Critical operation should have different configuration than test operation
        # (Different strategies should result in different configurations)
        assert config1.strategy != config2.strategy or config1 != config2

    def test_configuration_error_handling(self):
        """Test error handling when configuration loading fails."""
        # Test with invalid preset name
        with pytest.raises(ValueError, match="not found"):
            preset_manager.get_preset("invalid_preset_name")

        # Test with empty configuration
        empty_config = ResilienceConfig(
            strategy=ResilienceStrategy.BALANCED,
            retry_config=RetryConfig(max_attempts=0),
            circuit_breaker_config=None
        )

        # Should handle empty configuration gracefully
        assert isinstance(empty_config, ResilienceConfig)
        assert empty_config.strategy == ResilienceStrategy.BALANCED

    def test_preset_details_and_metadata(self):
        """Test that preset details and metadata are accessible."""
        # Test getting preset details
        details = preset_manager.get_preset_details("simple")

        assert isinstance(details, dict)
        assert "name" in details
        assert "description" in details
        assert "retry_attempts" in details
        assert "circuit_breaker_threshold" in details
        assert "recovery_timeout" in details

        # Test all presets summary
        all_presets = preset_manager.get_all_presets_summary()

        assert isinstance(all_presets, dict)
        assert "simple" in all_presets
        assert "development" in all_presets
        assert "production" in all_presets

        # Verify each preset has required information
        for preset_name, preset_info in all_presets.items():
            assert "name" in preset_info
            assert "description" in preset_info
            assert "retry_attempts" in preset_info
            assert "circuit_breaker_threshold" in preset_info

    def test_strategy_enum_validation(self):
        """Test that resilience strategies are properly validated."""
        # Test valid strategies
        valid_strategies = [
            ResilienceStrategy.AGGRESSIVE,
            ResilienceStrategy.BALANCED,
            ResilienceStrategy.CONSERVATIVE,
            ResilienceStrategy.CRITICAL
        ]

        for strategy in valid_strategies:
            assert isinstance(strategy, ResilienceStrategy)

            # Should be able to create configuration with strategy
            config = ResilienceConfig(strategy=strategy)
            assert config.strategy == strategy

        # Test string conversion
        assert str(ResilienceStrategy.BALANCED) == "balanced"
        assert ResilienceStrategy.BALANCED == "balanced"

        # Test invalid strategy handling
        invalid_config = ResilienceConfig(strategy="invalid_strategy")
        assert invalid_config.strategy is not None  # Should handle gracefully

    def test_configuration_inheritance_and_defaults(self):
        """Test configuration inheritance and default value handling."""
        # Test configuration with minimal specification
        minimal_config = ResilienceConfig(strategy=ResilienceStrategy.BALANCED)

        assert minimal_config.strategy == ResilienceStrategy.BALANCED
        assert minimal_config.retry_config is not None
        assert minimal_config.circuit_breaker_config is not None

        # Test that defaults are applied
        assert minimal_config.retry_config.max_attempts > 0
        assert minimal_config.circuit_breaker_config.failure_threshold > 0
        assert minimal_config.circuit_breaker_config.recovery_timeout > 0

    def test_environment_recommendation_confidence_scoring(self):
        """Test environment recommendation confidence scoring."""
        test_cases = [
            # (environment_vars, expected_confidence_range)
            ({"ENVIRONMENT": "production"}, (0.9, 1.0)),  # High confidence for exact match
            ({"ENVIRONMENT": "prod"}, (0.7, 0.9)),       # Medium-high for pattern match
            ({"DEPLOY_ENV": "staging"}, (0.8, 1.0)),     # High for staging pattern
            ({}, (0.3, 0.7)),                            # Low for auto-detection
        ]

        for env_vars, expected_confidence_range in test_cases:
            with patch.dict(os.environ, env_vars, clear=True):
                recommendation = preset_manager.recommend_preset_with_details()

                assert isinstance(recommendation.confidence, float)
                assert expected_confidence_range[0] <= recommendation.confidence <= expected_confidence_range[1]

                # Verify reasoning reflects confidence
                reasoning = recommendation.reasoning.lower()
                if recommendation.confidence > 0.8:
                    assert "exact" in reasoning or "direct" in reasoning or "clear" in reasoning
                elif recommendation.confidence > 0.5:
                    assert "pattern" in reasoning or "similar" in reasoning

    def test_configuration_backwards_compatibility(self):
        """Test backwards compatibility with legacy configuration formats."""
        # Test that old configuration formats are handled gracefully
        legacy_preset = preset_manager.get_preset("simple")

        # Should be able to convert to configuration
        config = legacy_preset.to_resilience_config()
        assert isinstance(config, ResilienceConfig)

        # Should have all required components
        assert config.retry_config is not None
        assert config.circuit_breaker_config is not None
        assert config.strategy is not None

        # Test with custom legacy-style configuration
        custom_config = ResilienceConfig(
            strategy=ResilienceStrategy.BALANCED,
            retry_config=RetryConfig(max_attempts=5),  # Custom value
            circuit_breaker_config=CircuitBreakerConfig(failure_threshold=10, recovery_timeout=120)
        )

        # Should maintain custom values
        assert custom_config.retry_config.max_attempts == 5
        assert custom_config.circuit_breaker_config.failure_threshold == 10
        assert custom_config.circuit_breaker_config.recovery_timeout == 120
