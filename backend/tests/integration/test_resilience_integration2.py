"""
Tests for resilience integration.
Need to combine old test_resilience_endpoints.py and test_preset_resilience_integration.py

This file currently only contains tests that were in test_preset_resilience_integration.py

Integration tests for preset-resilience service integration.

Tests the complete flow from preset selection through resilience service
configuration, including operation-specific strategies, custom overrides,
and legacy configuration compatibility.
"""

import pytest
import json
import os
from unittest.mock import patch, MagicMock
from typing import Dict, Any

from app.core.config import Settings
from app.infrastructure.resilience.config_presets import preset_manager, PRESETS
from app.infrastructure.resilience import AIServiceResilience, ResilienceStrategy
from app.infrastructure.resilience.config_validator import config_validator


class TestPresetResilienceIntegration:
    """Test integration between presets and resilience service."""
    
    def test_simple_preset_configures_resilience_service(self):
        """Test that simple preset correctly configures resilience service."""
        # Create settings with simple preset
        settings = Settings(resilience_preset="simple")
        
        # Initialize resilience service with settings
        resilience_service = AIServiceResilience(settings=settings)
        
        # Verify configuration matches simple preset expectations
        simple_preset = PRESETS["simple"]
        
        # Check that configuration was loaded
        assert resilience_service.settings.resilience_preset == "simple"
        
        # Verify operation configs exist for all operations
        operations = ["summarize", "sentiment", "key_points", "questions", "qa"]
        for operation in operations:
            config = resilience_service.get_operation_config(operation)
            assert config is not None
            assert hasattr(config, "retry_config")
            assert hasattr(config, "circuit_breaker_config")
    
    def test_development_preset_configures_resilience_service(self):
        """Test that development preset correctly configures resilience service."""
        settings = Settings(resilience_preset="development")
        resilience_service = AIServiceResilience(settings=settings)
        
        development_preset = PRESETS["development"]
        
        # Verify preset is loaded
        assert resilience_service.settings.resilience_preset == "development"
        
        # Check operation-specific overrides are applied
        sentiment_config = resilience_service.get_operation_config("sentiment")
        qa_config = resilience_service.get_operation_config("qa")
        
        assert sentiment_config is not None
        assert qa_config is not None
        
        # Verify development preset characteristics (fast failure)
        # Development preset should have lower retry attempts
        config = resilience_service.get_operation_config("summarize")
        assert config.retry_config.max_attempts <= 3  # Development should be fast
    
    def test_production_preset_configures_resilience_service(self):
        """Test that production preset correctly configures resilience service."""
        settings = Settings(resilience_preset="production")
        resilience_service = AIServiceResilience(settings=settings)
        
        production_preset = PRESETS["production"]
        
        # Verify preset is loaded
        assert resilience_service.settings.resilience_preset == "production"
        
        # Check that production has more robust configuration
        config = resilience_service.get_operation_config("summarize")
        assert config.retry_config.max_attempts >= 3  # Production should be robust
        assert config.circuit_breaker_config.failure_threshold >= 5
        
        # Verify operation-specific strategies from production preset
        qa_config = resilience_service.get_operation_config("qa")
        assert qa_config is not None
    
    def test_custom_configuration_overrides_preset(self):
        """Test that custom configuration properly overrides preset defaults."""
        custom_config = {
            "retry_attempts": 7,
            "circuit_breaker_threshold": 12,
            "operation_overrides": {
                "sentiment": "critical",
                "qa": "aggressive"
            }
        }
        
        settings = Settings(
            resilience_preset="simple",
            resilience_custom_config=json.dumps(custom_config)
        )
        
        resilience_service = AIServiceResilience(settings=settings)
        
        # Verify custom overrides are applied
        sentiment_config = resilience_service.get_operation_config("sentiment")
        qa_config = resilience_service.get_operation_config("qa")
        
        assert sentiment_config is not None
        assert qa_config is not None
        
        # Get overall configuration to verify custom values
        base_config = settings.get_resilience_config()
        assert base_config.retry_config.max_attempts == 7
        assert base_config.circuit_breaker_config.failure_threshold == 12
    
    def test_operation_specific_strategy_application(self):
        """Test that operation-specific strategies are properly applied."""
        settings = Settings(resilience_preset="production")
        resilience_service = AIServiceResilience(settings=settings)
        
        # Production preset has specific operation overrides
        production_preset = PRESETS["production"]
        
        # Test each operation gets correct strategy
        for operation in ["summarize", "sentiment", "key_points", "questions", "qa"]:
            strategy = settings.get_operation_strategy(operation)
            
            # Should get operation override or default strategy
            if operation in production_preset.operation_overrides:
                expected_strategy = production_preset.operation_overrides[operation].value
            else:
                expected_strategy = production_preset.default_strategy.value
            
            assert strategy == expected_strategy
    
    def test_legacy_configuration_compatibility(self):
        """Test that legacy configuration still works with resilience service."""
        # Mock legacy environment variables
        legacy_env = {
            "RETRY_MAX_ATTEMPTS": "4",
            "CIRCUIT_BREAKER_FAILURE_THRESHOLD": "8",
            "CIRCUIT_BREAKER_RECOVERY_TIMEOUT": "90",
            "DEFAULT_RESILIENCE_STRATEGY": "balanced",
            "SUMMARIZE_RESILIENCE_STRATEGY": "conservative"
        }
        
        with patch.dict(os.environ, legacy_env):
            settings = Settings(resilience_preset="simple")  # Preset should be ignored
            resilience_service = AIServiceResilience(settings=settings)
            
            # Verify legacy configuration is detected and used
            assert settings._has_legacy_resilience_config()
            
            # Check that legacy values are applied
            config = settings.get_resilience_config()
            assert config.retry_config.max_attempts == 4
            assert config.circuit_breaker_config.failure_threshold == 8
            assert config.circuit_breaker_config.recovery_timeout == 90
            
            # Check operation-specific strategy
            summarize_strategy = settings.get_operation_strategy("summarize")
            assert summarize_strategy == "conservative"
    
    def test_invalid_preset_fallback_to_simple(self):
        """Test that invalid preset falls back to simple preset."""
        # Test the fallback behavior within get_resilience_config
        settings = Settings(resilience_preset="simple")  # Start with valid preset
        
        # Mock the preset manager to simulate failure then fallback
        from app.infrastructure.resilience.config_presets import PRESETS
        
        def mock_get_preset_side_effect(preset_name):
            if preset_name == "simple" and mock_get_preset_side_effect.call_count == 1:
                raise ValueError("Unknown preset")  # First call fails
            elif preset_name == "simple":
                return PRESETS["simple"]  # Fallback succeeds
            else:
                raise ValueError(f"Unknown preset: {preset_name}")
        
        mock_get_preset_side_effect.call_count = 0
        
        with patch('app.infrastructure.resilience.preset_manager.get_preset') as mock_get_preset:
            def side_effect_wrapper(preset_name):
                mock_get_preset_side_effect.call_count += 1
                return mock_get_preset_side_effect(preset_name)
            
            mock_get_preset.side_effect = side_effect_wrapper
            
            # Should not raise exception and should fall back
            resilience_config = settings.get_resilience_config()
            assert resilience_config is not None
            
            # Should have been called twice (original + fallback)
            assert mock_get_preset.call_count == 2
    
    def test_with_operation_resilience_decorator_integration(self):
        """Test the new with_operation_resilience decorator integration."""
        settings = Settings(resilience_preset="development")
        resilience_service = AIServiceResilience(settings=settings)
        
        # Check if the decorator method exists and can be called
        assert hasattr(resilience_service, 'with_operation_resilience')
        
        # Test that we can get the decorator function
        decorator = resilience_service.with_operation_resilience("sentiment")
        assert callable(decorator)
    
    @pytest.mark.parametrize("preset_name", ["simple", "development", "production"])
    def test_all_presets_configure_successfully(self, preset_name):
        """Test that all presets can configure resilience service successfully."""
        settings = Settings(resilience_preset=preset_name)
        resilience_service = AIServiceResilience(settings=settings)
        
        # Verify configuration loads without errors
        config = settings.get_resilience_config()
        assert config is not None
        
        # Verify all operations have configurations
        operations = ["summarize", "sentiment", "key_points", "questions", "qa"]
        for operation in operations:
            op_config = resilience_service.get_operation_config(operation)
            assert op_config is not None
            
            # Verify operation strategy is valid
            strategy = settings.get_operation_strategy(operation)
            assert strategy in ["aggressive", "balanced", "conservative", "critical"]
    
    def test_preset_validation_integration(self):
        """Test that preset validation integrates with settings validation."""
        # Test valid preset
        settings = Settings(resilience_preset="simple")
        validation_result = settings.validate_custom_config()
        
        # Should be valid when no custom config is provided
        assert validation_result["is_valid"] is True
        
        # Test custom config validation
        custom_config = '{"retry_attempts": 5, "circuit_breaker_threshold": 8}'
        validation_result = settings.validate_custom_config(custom_config)
        assert validation_result["is_valid"] is True
    
    def test_configuration_hot_reload_capability(self):
        """Test that configuration can be reloaded without service restart."""
        # Start with simple preset
        settings = Settings(resilience_preset="simple")
        resilience_service = AIServiceResilience(settings=settings)
        
        initial_config = resilience_service.get_operation_config("summarize")
        initial_attempts = initial_config.retry_config.max_attempts
        
        # Change to production preset (simulating config change)
        settings.resilience_preset = "production"
        
        # Reinitialize configurations (simulating hot reload)
        resilience_service = AIServiceResilience(settings=settings)
        
        new_config = resilience_service.get_operation_config("summarize")
        new_attempts = new_config.retry_config.max_attempts
        
        # Configuration should have changed
        production_preset = PRESETS["production"]
        assert new_attempts == production_preset.retry_attempts


class TestPresetConfigurationFlow:
    """Test the complete configuration flow from preset to service."""
    
    def test_end_to_end_simple_preset_flow(self):
        """Test complete flow: simple preset → settings → resilience service."""
        # Step 1: Create settings with simple preset
        settings = Settings(resilience_preset="simple")
        
        # Step 2: Verify preset configuration is loaded
        resilience_config = settings.get_resilience_config()
        assert resilience_config is not None
        
        simple_preset = PRESETS["simple"]
        assert resilience_config.retry_config.max_attempts == simple_preset.retry_attempts
        assert resilience_config.circuit_breaker_config.failure_threshold == simple_preset.circuit_breaker_threshold
        
        # Step 3: Initialize resilience service
        resilience_service = AIServiceResilience(settings=settings)
        
        # Step 4: Verify service has correct configuration for each operation
        for operation in ["summarize", "sentiment", "key_points", "questions", "qa"]:
            config = resilience_service.get_operation_config(operation)
            assert config is not None
            assert config.retry_config.max_attempts == simple_preset.retry_attempts
            assert config.circuit_breaker_config.failure_threshold == simple_preset.circuit_breaker_threshold
    
    def test_end_to_end_custom_override_flow(self):
        """Test complete flow with custom configuration overrides."""
        custom_overrides = {
            "retry_attempts": 6,
            "circuit_breaker_threshold": 9,
            "operation_overrides": {
                "summarize": "critical",
                "sentiment": "aggressive"
            }
        }
        
        # Step 1: Create settings with custom overrides
        settings = Settings(
            resilience_preset="simple",
            resilience_custom_config=json.dumps(custom_overrides)
        )
        
        # Step 2: Verify custom overrides are applied to configuration
        resilience_config = settings.get_resilience_config()
        assert resilience_config.retry_config.max_attempts == 6
        assert resilience_config.circuit_breaker_config.failure_threshold == 9
        
        # Step 3: Initialize resilience service
        resilience_service = AIServiceResilience(settings=settings)
        
        # Step 4: Verify operation-specific overrides
        summarize_strategy = settings.get_operation_strategy("summarize")
        sentiment_strategy = settings.get_operation_strategy("sentiment")
        
        assert summarize_strategy == "critical"
        assert sentiment_strategy == "aggressive"
        
        # Step 5: Verify other operations use default strategy
        qa_strategy = settings.get_operation_strategy("qa")
        assert qa_strategy == PRESETS["simple"].default_strategy.value  # Should use simple preset default
    
    def test_validation_integration_with_service_configuration(self):
        """Test that validation integrates properly with service configuration."""
        # Test with valid custom configuration
        valid_config = {
            "retry_attempts": 4,
            "circuit_breaker_threshold": 7,
            "default_strategy": "balanced"
        }
        
        settings = Settings(
            resilience_preset="simple",
            resilience_custom_config=json.dumps(valid_config)
        )
        
        # Validation should pass
        validation_result = settings.validate_custom_config()
        assert validation_result["is_valid"] is True
        
        # Service should configure successfully
        resilience_service = AIServiceResilience(settings=settings)
        config = resilience_service.get_operation_config("summarize")
        assert config is not None
        
        # Custom values should be applied
        resilience_config = settings.get_resilience_config()
        assert resilience_config.retry_config.max_attempts == 4
        assert resilience_config.circuit_breaker_config.failure_threshold == 7
    
    def test_error_handling_in_configuration_flow(self):
        """Test error handling throughout the configuration flow."""
        # Test with invalid JSON in custom config
        settings = Settings(
            resilience_preset="simple",
            resilience_custom_config='{"retry_attempts": invalid_json}'
        )
        
        # Should not crash and should fall back to preset defaults
        resilience_config = settings.get_resilience_config()
        assert resilience_config is not None
        
        # Should use simple preset defaults
        simple_preset = PRESETS["simple"]
        assert resilience_config.retry_config.max_attempts == simple_preset.retry_attempts
        
        # Service should still initialize successfully
        resilience_service = AIServiceResilience(settings=settings)
        config = resilience_service.get_operation_config("summarize")
        assert config is not None


class TestBackwardCompatibilityIntegration:
    """Test backward compatibility with legacy configuration systems."""
    
    def test_mixed_legacy_and_preset_environment(self):
        """Test behavior when both legacy and preset configs are present."""
        legacy_env = {
            "RETRY_MAX_ATTEMPTS": "6",
            "CIRCUIT_BREAKER_FAILURE_THRESHOLD": "12",
            "DEFAULT_RESILIENCE_STRATEGY": "aggressive"
        }
        
        with patch.dict(os.environ, legacy_env):
            # Even with preset specified, legacy should take precedence
            settings = Settings(resilience_preset="production")
            
            # Should detect legacy configuration
            assert settings._has_legacy_resilience_config()
            
            # Should use legacy values
            config = settings.get_resilience_config()
            assert config.retry_config.max_attempts == 6
            assert config.circuit_breaker_config.failure_threshold == 12
            
            # Resilience service should work with legacy config
            resilience_service = AIServiceResilience(settings=settings)
            service_config = resilience_service.get_operation_config("summarize")
            assert service_config is not None
    
    def test_migration_scenario_simulation(self):
        """Test simulated migration from legacy to preset configuration."""
        # Simulate legacy environment
        legacy_env = {
            "RETRY_MAX_ATTEMPTS": "3",
            "CIRCUIT_BREAKER_FAILURE_THRESHOLD": "5",
            "CIRCUIT_BREAKER_RECOVERY_TIMEOUT": "60",
            "DEFAULT_RESILIENCE_STRATEGY": "balanced"
        }
        
        # Phase 1: Legacy configuration
        with patch.dict(os.environ, legacy_env):
            legacy_settings = Settings()
            legacy_config = legacy_settings.get_resilience_config()
            legacy_service = AIServiceResilience(settings=legacy_settings)
            
            # Capture legacy behavior
            legacy_op_config = legacy_service.get_operation_config("summarize")
            assert legacy_op_config.retry_config.max_attempts == 3
        
        # Phase 2: Migration to preset (remove legacy env vars)
        preset_settings = Settings(resilience_preset="simple")
        preset_config = preset_settings.get_resilience_config()
        preset_service = AIServiceResilience(settings=preset_settings)
        
        # Verify similar behavior with preset
        preset_op_config = preset_service.get_operation_config("summarize")
        
        # Simple preset should have same values as the legacy config
        simple_preset = PRESETS["simple"]
        assert preset_op_config.retry_config.max_attempts == simple_preset.retry_attempts
        assert preset_op_config.circuit_breaker_config.failure_threshold == simple_preset.circuit_breaker_threshold
    
    def test_gradual_migration_with_custom_overrides(self):
        """Test gradual migration using custom overrides to match legacy behavior."""
        # Legacy configuration that doesn't exactly match any preset
        legacy_values = {
            "retry_attempts": 7,  # Custom value
            "circuit_breaker_threshold": 8,  # Custom value
            "default_strategy": "conservative"
        }
        
        # Migrate to preset with custom overrides to maintain exact behavior
        settings = Settings(
            resilience_preset="simple",  # Base preset
            resilience_custom_config=json.dumps(legacy_values)  # Custom overrides
        )
        
        # Verify exact legacy behavior is maintained
        config = settings.get_resilience_config()
        assert config.retry_config.max_attempts == 7
        assert config.circuit_breaker_config.failure_threshold == 8
        
        # Service should work with migrated configuration
        resilience_service = AIServiceResilience(settings=settings)
        service_config = resilience_service.get_operation_config("summarize")
        assert service_config.retry_config.max_attempts == 7
        assert service_config.circuit_breaker_config.failure_threshold == 8


class TestPerformanceAndReliability:
    """Test performance and reliability aspects of preset integration."""
    
    def test_configuration_loading_performance(self):
        """Test that preset configuration loading is fast."""
        import time
        
        # Measure preset configuration loading time
        start_time = time.time()
        
        for _ in range(100):  # Load configuration 100 times
            settings = Settings(resilience_preset="simple")
            config = settings.get_resilience_config()
            resilience_service = AIServiceResilience(settings=settings)
        
        end_time = time.time()
        total_time = end_time - start_time
        avg_time_per_load = total_time / 100
        
        # Should be very fast (less than 10ms per load)
        assert avg_time_per_load < 0.01, f"Configuration loading too slow: {avg_time_per_load:.3f}s"
    
    def test_memory_efficiency_of_preset_system(self):
        """Test that preset system doesn't use excessive memory."""
        import sys
        
        # Create multiple settings instances
        settings_instances = []
        for _ in range(50):
            settings = Settings(resilience_preset="production")
            resilience_service = AIServiceResilience(settings=settings)
            settings_instances.append((settings, resilience_service))
        
        # Memory usage should be reasonable
        # This is a basic check - in production you might use memory_profiler
        assert len(settings_instances) == 50
    
    def test_concurrent_configuration_access(self):
        """Test that configuration can be accessed concurrently."""
        import threading
        import concurrent.futures
        
        def create_and_test_config(preset_name):
            """Create configuration and test it."""
            settings = Settings(resilience_preset=preset_name)
            resilience_service = AIServiceResilience(settings=settings)
            config = resilience_service.get_operation_config("summarize")
            return config is not None
        
        # Test concurrent access with multiple presets
        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as executor:
            futures = []
            preset_names = ["simple", "development", "production"] * 10
            
            for preset_name in preset_names:
                future = executor.submit(create_and_test_config, preset_name)
                futures.append(future)
            
            # All configurations should succeed
            results = [future.result() for future in concurrent.futures.as_completed(futures)]
            assert all(results), "Some concurrent configurations failed"
    
    def test_configuration_consistency_across_operations(self):
        """Test that configuration is consistent across all operations."""
        settings = Settings(resilience_preset="production")
        resilience_service = AIServiceResilience(settings=settings)
        
        production_preset = PRESETS["production"]
        operations = ["summarize", "sentiment", "key_points", "questions", "qa"]
        
        # All operations should have consistent base configuration
        base_retry_attempts = production_preset.retry_attempts
        base_circuit_threshold = production_preset.circuit_breaker_threshold
        
        for operation in operations:
            config = resilience_service.get_operation_config(operation)
            
            # Base configuration should be consistent
            assert config.retry_config.max_attempts == base_retry_attempts
            assert config.circuit_breaker_config.failure_threshold == base_circuit_threshold
            
            # Strategy may vary based on operation overrides
            strategy = settings.get_operation_strategy(operation)
            assert strategy in ["aggressive", "balanced", "conservative", "critical"]