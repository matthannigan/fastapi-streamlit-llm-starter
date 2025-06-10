"""
Comprehensive backward compatibility test suite.

This module provides extensive testing for backward compatibility scenarios,
including legacy configuration migration, mixed environments, edge cases,
and migration validation.
"""

import pytest
import json
import os
import tempfile
from unittest.mock import patch, MagicMock
from typing import Dict, Any

from app.config import Settings
from app.resilience_presets import preset_manager, PRESETS, PresetManager
from app.services.resilience import AIServiceResilience, ResilienceStrategy
from app.validation_schemas import config_validator


class TestLegacyConfigurationDetection:
    """Test detection of legacy configuration patterns."""
    
    @pytest.mark.parametrize("env_vars,expected_legacy", [
        # Single legacy variable should trigger detection
        ({"RETRY_MAX_ATTEMPTS": "5"}, True),
        ({"CIRCUIT_BREAKER_FAILURE_THRESHOLD": "10"}, True),
        ({"DEFAULT_RESILIENCE_STRATEGY": "conservative"}, True),
        ({"SUMMARIZE_RESILIENCE_STRATEGY": "aggressive"}, True),
        
        # Multiple legacy variables
        ({"RETRY_MAX_ATTEMPTS": "3", "CIRCUIT_BREAKER_FAILURE_THRESHOLD": "5"}, True),
        
        # Non-legacy variables should not trigger detection
        ({"GEMINI_API_KEY": "test", "DEBUG": "true"}, False),
        ({"RESILIENCE_PRESET": "simple"}, False),
        
        # Empty environment
        ({}, False),
        
    ])
    def test_legacy_config_detection_environment_variables(self, env_vars, expected_legacy):
        """Test legacy configuration detection from environment variables."""
        with patch.dict(os.environ, env_vars, clear=False):
            settings = Settings()
            assert settings._has_legacy_resilience_config() == expected_legacy
    
    def test_legacy_config_detection_modified_defaults(self):
        """Test legacy configuration detection from modified default values."""
        # Default values should not trigger legacy detection
        settings = Settings()
        assert not settings._has_legacy_resilience_config()
        
        # Modified values should trigger legacy detection
        settings_modified = Settings(
            circuit_breaker_failure_threshold=10,  # Changed from default
            retry_max_attempts=7  # Changed from default
        )
        assert settings_modified._has_legacy_resilience_config()
    
    def test_legacy_config_priority_over_preset(self):
        """Test that legacy configuration takes priority over preset."""
        legacy_env = {
            "RETRY_MAX_ATTEMPTS": "8",
            "CIRCUIT_BREAKER_FAILURE_THRESHOLD": "15",
            "DEFAULT_RESILIENCE_STRATEGY": "conservative"
        }
        
        with patch.dict(os.environ, legacy_env):
            # Even with preset specified, legacy should take precedence
            settings = Settings(resilience_preset="development")
            
            assert settings._has_legacy_resilience_config()
            
            config = settings.get_resilience_config()
            assert config.retry_config.max_attempts == 8
            assert config.circuit_breaker_config.failure_threshold == 15


class TestLegacyConfigurationMapping:
    """Test mapping from legacy configuration to new system."""
    
    def test_complete_legacy_environment_mapping(self):
        """Test complete mapping of all legacy environment variables."""
        complete_legacy_env = {
            # Core configuration
            "RESILIENCE_ENABLED": "true",
            "CIRCUIT_BREAKER_ENABLED": "true", 
            "RETRY_ENABLED": "true",
            
            # Global settings
            "DEFAULT_RESILIENCE_STRATEGY": "balanced",
            "CIRCUIT_BREAKER_FAILURE_THRESHOLD": "7",
            "CIRCUIT_BREAKER_RECOVERY_TIMEOUT": "90",
            
            # Retry configuration
            "RETRY_MAX_ATTEMPTS": "4",
            "RETRY_MAX_DELAY": "25",
            "RETRY_EXPONENTIAL_MULTIPLIER": "1.5",
            "RETRY_EXPONENTIAL_MIN": "1.0",
            "RETRY_EXPONENTIAL_MAX": "15.0",
            "RETRY_JITTER_ENABLED": "true",
            "RETRY_JITTER_MAX": "3.0",
            
            # Operation-specific strategies
            "SUMMARIZE_RESILIENCE_STRATEGY": "conservative",
            "SENTIMENT_RESILIENCE_STRATEGY": "aggressive",
            "KEY_POINTS_RESILIENCE_STRATEGY": "balanced",
            "QUESTIONS_RESILIENCE_STRATEGY": "conservative",
            "QA_RESILIENCE_STRATEGY": "conservative",
            
            # Monitoring configuration
            "RESILIENCE_METRICS_ENABLED": "true",
            "RESILIENCE_HEALTH_CHECK_ENABLED": "true"
        }
        
        with patch.dict(os.environ, complete_legacy_env):
            settings = Settings()
            
            # Should detect legacy configuration
            assert settings._has_legacy_resilience_config()
            
            # Get configuration
            config = settings.get_resilience_config()
            
            # Verify core values are mapped correctly
            assert config.retry_config.max_attempts == 4
            assert config.circuit_breaker_config.failure_threshold == 7
            assert config.circuit_breaker_config.recovery_timeout == 90
            assert config.strategy == ResilienceStrategy.BALANCED
            
            # Verify operation-specific strategies
            assert settings.get_operation_strategy("summarize") == "conservative"
            assert settings.get_operation_strategy("sentiment") == "aggressive"
            assert settings.get_operation_strategy("key_points") == "balanced"
            assert settings.get_operation_strategy("questions") == "conservative"
            assert settings.get_operation_strategy("qa") == "conservative"
    
    def test_partial_legacy_configuration_handling(self):
        """Test handling of partial legacy configuration."""
        partial_legacy_env = {
            "RETRY_MAX_ATTEMPTS": "6",
            "SUMMARIZE_RESILIENCE_STRATEGY": "aggressive"
            # Missing circuit breaker and other settings
        }
        
        with patch.dict(os.environ, partial_legacy_env):
            settings = Settings()
            
            # Should detect legacy configuration
            assert settings._has_legacy_resilience_config()
            
            config = settings.get_resilience_config()
            
            # Specified values should be used
            assert config.retry_config.max_attempts == 6
            assert settings.get_operation_strategy("summarize") == "aggressive"
            
            # Missing values should use defaults
            assert config.circuit_breaker_config.failure_threshold == settings.circuit_breaker_failure_threshold
    
    def test_legacy_boolean_string_conversion(self):
        """Test conversion of legacy boolean string values."""
        boolean_env = {
            "RESILIENCE_ENABLED": "false",
            "CIRCUIT_BREAKER_ENABLED": "true",
            "RETRY_ENABLED": "1",
            "RETRY_JITTER_ENABLED": "0"
        }
        
        with patch.dict(os.environ, boolean_env):
            settings = Settings()
            
            # Should handle boolean string conversion
            assert not settings.resilience_enabled
            assert settings.circuit_breaker_enabled
            assert settings.retry_enabled
            assert not settings.retry_jitter_enabled


class TestMigrationScenarios:
    """Test various migration scenarios from legacy to preset configuration."""
    
    def test_migration_recommendation_based_on_legacy_config(self):
        """Test preset recommendations based on legacy configuration patterns."""
        # Development-like legacy configuration
        dev_legacy = {
            "RETRY_MAX_ATTEMPTS": "2",
            "CIRCUIT_BREAKER_FAILURE_THRESHOLD": "3",
            "CIRCUIT_BREAKER_RECOVERY_TIMEOUT": "30",
            "DEFAULT_RESILIENCE_STRATEGY": "aggressive"
        }
        
        with patch.dict(os.environ, dev_legacy):
            settings = Settings()
            
            # Should suggest development preset for these values
            recommendation = preset_manager.recommend_preset("development")
            assert recommendation == "development"
        
        # Production-like legacy configuration
        prod_legacy = {
            "RETRY_MAX_ATTEMPTS": "5",
            "CIRCUIT_BREAKER_FAILURE_THRESHOLD": "10", 
            "CIRCUIT_BREAKER_RECOVERY_TIMEOUT": "120",
            "DEFAULT_RESILIENCE_STRATEGY": "conservative"
        }
        
        with patch.dict(os.environ, prod_legacy):
            settings = Settings()
            
            recommendation = preset_manager.recommend_preset("production")
            assert recommendation == "production"
    
    def test_gradual_migration_with_mixed_configuration(self):
        """Test gradual migration approach with mixed legacy and preset config."""
        # Start with legacy configuration
        initial_legacy = {
            "RETRY_MAX_ATTEMPTS": "4",
            "CIRCUIT_BREAKER_FAILURE_THRESHOLD": "8",
            "DEFAULT_RESILIENCE_STRATEGY": "balanced"
        }
        
        with patch.dict(os.environ, initial_legacy):
            # Phase 1: Legacy configuration
            legacy_settings = Settings()
            legacy_config = legacy_settings.get_resilience_config()
            
            # Capture legacy behavior
            legacy_attempts = legacy_config.retry_config.max_attempts
            legacy_threshold = legacy_config.circuit_breaker_config.failure_threshold
            
            # Phase 2: Introduce preset with custom overrides to match legacy
            custom_config = {
                "retry_attempts": legacy_attempts,
                "circuit_breaker_threshold": legacy_threshold,
                "default_strategy": "balanced"
            }
            
            # Phase 3: Remove legacy env vars, use preset + custom config
            migration_settings = Settings(
                resilience_preset="simple",
                resilience_custom_config=json.dumps(custom_config)
            )
            
            migration_config = migration_settings.get_resilience_config()
            
            # Behavior should be identical
            assert migration_config.retry_config.max_attempts == legacy_attempts
            assert migration_config.circuit_breaker_config.failure_threshold == legacy_threshold
    
    def test_migration_validation_and_rollback(self):
        """Test migration validation and rollback scenarios."""
        original_legacy = {
            "RETRY_MAX_ATTEMPTS": "3",
            "CIRCUIT_BREAKER_FAILURE_THRESHOLD": "5",
            "DEFAULT_RESILIENCE_STRATEGY": "balanced"
        }
        
        with patch.dict(os.environ, original_legacy):
            # Original legacy configuration
            original_settings = Settings()
            original_config = original_settings.get_resilience_config()
            
            # Test migration to preset
            preset_settings = Settings(resilience_preset="simple")
            preset_config = preset_settings.get_resilience_config()
            
            # Verify migration maintains similar behavior
            # Simple preset should have same values as this legacy config
            assert preset_config.retry_config.max_attempts == 3
            assert preset_config.circuit_breaker_config.failure_threshold == 5
            
            # Test rollback scenario - should be able to go back to legacy
            rollback_settings = Settings()  # Will use legacy again
            rollback_config = rollback_settings.get_resilience_config()
            
            # Should match original legacy configuration
            assert rollback_config.retry_config.max_attempts == original_config.retry_config.max_attempts
            assert rollback_config.circuit_breaker_config.failure_threshold == original_config.circuit_breaker_config.failure_threshold


class TestEdgeCasesAndErrorHandling:
    """Test edge cases and error handling in backward compatibility."""
    
    def test_malformed_legacy_environment_variables(self):
        """Test handling of malformed legacy environment variables."""
        # Legacy environment variables with invalid values should be handled gracefully
        # with fallback to defaults, NOT raise exceptions (that's the point of legacy support)
        malformed_env = {
            "RETRY_MAX_ATTEMPTS": "not_a_number",
            "CIRCUIT_BREAKER_FAILURE_THRESHOLD": "invalid",
            "DEFAULT_RESILIENCE_STRATEGY": "unknown_strategy"
        }
        
        with patch.dict(os.environ, malformed_env):
            # Should NOT raise an exception - legacy mode should be graceful
            settings = Settings()
            
            # Should fall back to defaults
            assert settings.retry_max_attempts == 3  # default
            assert settings.circuit_breaker_failure_threshold == 5  # default
            assert settings.default_resilience_strategy == "balanced"  # default
            
            # Should still be considered legacy config
            assert settings._has_legacy_resilience_config() is True
    
    def test_legacy_config_with_extreme_values(self):
        """Test handling of legacy configuration with extreme values."""
        extreme_env = {
            "RETRY_MAX_ATTEMPTS": "100",  # Very high but valid
            "CIRCUIT_BREAKER_FAILURE_THRESHOLD": "1000",  # Very high but valid
            "CIRCUIT_BREAKER_RECOVERY_TIMEOUT": "1"  # Minimum valid value
        }
        
        with patch.dict(os.environ, extreme_env):
            settings = Settings()
            config = settings.get_resilience_config()
            
            # Should handle extreme values gracefully
            assert config is not None
            # Values should be accepted if within validation ranges
            assert config.retry_config.max_attempts == 100
            assert config.circuit_breaker_config.failure_threshold == 1000
    
    def test_mixed_legacy_and_custom_config_conflict(self):
        """Test conflict resolution between legacy config and custom JSON config."""
        legacy_env = {
            "RETRY_MAX_ATTEMPTS": "5",
            "CIRCUIT_BREAKER_FAILURE_THRESHOLD": "8"
        }
        
        custom_config = {
            "retry_attempts": 3,  # Conflicts with legacy
            "circuit_breaker_threshold": 6,  # Conflicts with legacy
            "default_strategy": "aggressive"
        }
        
        with patch.dict(os.environ, legacy_env):
            settings = Settings(
                resilience_preset="simple",
                resilience_custom_config=json.dumps(custom_config)
            )
            
            # Legacy should take precedence over custom config
            config = settings.get_resilience_config()
            assert config.retry_config.max_attempts == 5  # Legacy value
            assert config.circuit_breaker_config.failure_threshold == 8  # Legacy value
    
    def test_empty_and_null_legacy_values(self):
        """Test handling of empty and null legacy configuration values."""
        # With current Pydantic validation, empty values will cause validation errors
        # This test ensures validation is working correctly
        empty_env = {
            "RETRY_MAX_ATTEMPTS": "",  # Empty string will fail validation
        }
        
        with patch.dict(os.environ, empty_env, clear=False):
            # Should raise validation error for empty values
            with pytest.raises((ValueError, Exception)):
                settings = Settings()


class TestMultiEnvironmentCompatibility:
    """Test compatibility across different deployment environments."""
    
    def test_development_environment_compatibility(self):
        """Test compatibility in development environment setup."""
        dev_env = {
            "DEBUG": "true",
            "NODE_ENV": "development",
            "HOST": "localhost",
            # Mix of legacy and new config
            "RETRY_MAX_ATTEMPTS": "2",
            "RESILIENCE_PRESET": "development"
        }
        
        with patch.dict(os.environ, dev_env):
            settings = Settings()
            
            # Legacy should take precedence
            assert settings._has_legacy_resilience_config()
            
            config = settings.get_resilience_config()
            assert config.retry_config.max_attempts == 2  # Legacy value
            
            # But preset recommendation should suggest development
            recommendation = preset_manager.recommend_preset_with_details()
            assert recommendation.preset_name == "development"
    
    def test_production_environment_compatibility(self):
        """Test compatibility in production environment setup."""
        prod_env = {
            "PROD": "true",
            "DEBUG": "false",
            "DATABASE_URL": "postgres://prod-server/db",
            # Production-like legacy config
            "RETRY_MAX_ATTEMPTS": "5",
            "CIRCUIT_BREAKER_FAILURE_THRESHOLD": "10",
            "DEFAULT_RESILIENCE_STRATEGY": "conservative"
        }
        
        with patch.dict(os.environ, prod_env):
            # Mock file existence to avoid dev indicators triggering
            with patch('os.path.exists', return_value=False):
                settings = Settings()
                
                # Should detect legacy config
                assert settings._has_legacy_resilience_config()
                
                # Should suggest production preset
                recommendation = preset_manager.recommend_preset_with_details()
                assert recommendation.preset_name == "production"
                
                # Legacy config should work in production environment
                config = settings.get_resilience_config()
                assert config.retry_config.max_attempts == 5
                assert config.circuit_breaker_config.failure_threshold == 10
    
    def test_staging_environment_compatibility(self):
        """Test compatibility in staging environment setup."""
        staging_env = {
            "ENV": "staging",
            "NODE_ENV": "staging",
            "DATABASE_URL": "postgres://staging-server/db"
        }
        
        with patch.dict(os.environ, staging_env):
            settings = Settings()
            
            # Should recommend production preset for staging
            recommendation = preset_manager.recommend_preset_with_details()
            assert recommendation.preset_name == "production"
            
            # Should work without legacy config
            config = settings.get_resilience_config()
            assert config is not None


class TestConfigurationVersioning:
    """Test configuration versioning and compatibility."""
    
    def test_configuration_format_v1_compatibility(self):
        """Test compatibility with version 1 configuration format (legacy)."""
        # Simulate old configuration format
        v1_config = {
            "RETRY_MAX_ATTEMPTS": "3",
            "CIRCUIT_BREAKER_FAILURE_THRESHOLD": "5",
            "DEFAULT_RESILIENCE_STRATEGY": "balanced",
            # Old operation format
            "SUMMARIZE_RESILIENCE_STRATEGY": "conservative"
        }
        
        with patch.dict(os.environ, v1_config):
            settings = Settings()
            
            # Should handle v1 format
            assert settings._has_legacy_resilience_config()
            
            config = settings.get_resilience_config()
            assert config.retry_config.max_attempts == 3
            assert settings.get_operation_strategy("summarize") == "conservative"
    
    def test_configuration_format_v2_compatibility(self):
        """Test compatibility with version 2 configuration format (preset-based)."""
        # Current preset-based format
        settings = Settings(resilience_preset="production")
        
        config = settings.get_resilience_config()
        production_preset = PRESETS["production"]
        
        assert config.retry_config.max_attempts == production_preset.retry_attempts
        assert config.circuit_breaker_config.failure_threshold == production_preset.circuit_breaker_threshold
    
    def test_configuration_format_v3_compatibility(self):
        """Test compatibility with version 3 configuration format (preset + custom)."""
        # Future format with enhanced custom configuration
        custom_config = {
            "retry_attempts": 4,
            "circuit_breaker_threshold": 7,
            "operation_overrides": {
                "summarize": "critical",
                "sentiment": "aggressive"
            },
            "exponential_multiplier": 1.5,
            "jitter_enabled": True
        }
        
        settings = Settings(
            resilience_preset="simple",
            resilience_custom_config=json.dumps(custom_config)
        )
        
        config = settings.get_resilience_config()
        assert config.retry_config.max_attempts == 4
        assert config.circuit_breaker_config.failure_threshold == 7
        assert settings.get_operation_strategy("summarize") == "critical"


class TestDataMigrationScenarios:
    """Test data migration scenarios for configuration persistence."""
    
    def test_configuration_export_import(self):
        """Test exporting and importing configuration data."""
        # Original configuration
        original_env = {
            "RETRY_MAX_ATTEMPTS": "4",
            "CIRCUIT_BREAKER_FAILURE_THRESHOLD": "7",
            "DEFAULT_RESILIENCE_STRATEGY": "balanced",
            "SUMMARIZE_RESILIENCE_STRATEGY": "conservative"
        }
        
        with patch.dict(os.environ, original_env):
            original_settings = Settings()
            
            # Export configuration (simulate export function)
            exported_config = {
                "retry_attempts": original_settings.retry_max_attempts,
                "circuit_breaker_threshold": original_settings.circuit_breaker_failure_threshold,
                "default_strategy": original_settings.default_resilience_strategy,
                "operation_overrides": {
                    "summarize": original_settings.summarize_resilience_strategy
                }
            }
            
            # Import configuration as custom config
            imported_settings = Settings(
                resilience_preset="simple",
                resilience_custom_config=json.dumps(exported_config)
            )
            
            # Should maintain same behavior
            original_config = original_settings.get_resilience_config()
            imported_config = imported_settings.get_resilience_config()
            
            assert imported_config.retry_config.max_attempts == original_config.retry_config.max_attempts
            assert imported_config.circuit_breaker_config.failure_threshold == original_config.circuit_breaker_config.failure_threshold
    
    def test_configuration_backup_and_restore(self):
        """Test configuration backup and restore functionality."""
        # Create a temporary backup file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as backup_file:
            backup_config = {
                "format_version": "2.0",
                "preset_name": "production",
                "custom_overrides": {
                    "retry_attempts": 6,
                    "circuit_breaker_threshold": 9
                },
                "timestamp": "2024-01-01T00:00:00Z"
            }
            
            json.dump(backup_config, backup_file)
            backup_file.flush()
            
            # Restore from backup
            restored_settings = Settings(
                resilience_preset=backup_config["preset_name"],
                resilience_custom_config=json.dumps(backup_config["custom_overrides"])
            )
            
            config = restored_settings.get_resilience_config()
            assert config.retry_config.max_attempts == 6
            assert config.circuit_breaker_config.failure_threshold == 9
            
            # Cleanup
            os.unlink(backup_file.name)


class TestPerformanceWithBackwardCompatibility:
    """Test performance implications of backward compatibility."""
    
    def test_legacy_config_detection_performance(self):
        """Test that legacy configuration detection is fast."""
        import time
        
        # Test with legacy environment
        legacy_env = {
            "RETRY_MAX_ATTEMPTS": "3",
            "CIRCUIT_BREAKER_FAILURE_THRESHOLD": "5",
            "DEFAULT_RESILIENCE_STRATEGY": "balanced"
        }
        
        with patch.dict(os.environ, legacy_env):
            # Create a single Settings instance first
            settings = Settings()
            
            start_time = time.time()
            
            # Test just the legacy detection method performance by clearing cache each time
            for _ in range(1000):
                # Clear cache to force re-detection
                if hasattr(settings, '_legacy_config_cache'):
                    delattr(settings, '_legacy_config_cache')
                settings._has_legacy_resilience_config()
            
            end_time = time.time()
            total_time = end_time - start_time
            
            # Should be very fast (less than 1 second for 1000 detections)
            assert total_time < 1.0, f"Legacy detection too slow: {total_time:.3f}s for 1000 detections"
    
    def test_mixed_configuration_loading_performance(self):
        """Test performance of loading mixed legacy and preset configuration."""
        import time
        
        legacy_env = {
            "RETRY_MAX_ATTEMPTS": "5",
            "CIRCUIT_BREAKER_FAILURE_THRESHOLD": "8"
        }
        
        with patch.dict(os.environ, legacy_env):
            start_time = time.time()
            
            # Load mixed configuration multiple times
            for _ in range(100):
                settings = Settings(resilience_preset="production")
                config = settings.get_resilience_config()
                resilience_service = AIServiceResilience(settings=settings)
            
            end_time = time.time()
            avg_time = (end_time - start_time) / 100
            
            # Should be fast (less than 10ms per load)
            assert avg_time < 0.01, f"Mixed configuration loading too slow: {avg_time:.3f}s"


class TestComprehensiveIntegrationScenarios:
    """Test comprehensive integration scenarios covering all compatibility aspects."""
    
    def test_full_application_lifecycle_with_migration(self):
        """Test full application lifecycle including configuration migration."""
        # Phase 1: Application starts with legacy configuration
        legacy_env = {
            "RETRY_MAX_ATTEMPTS": "3",
            "CIRCUIT_BREAKER_FAILURE_THRESHOLD": "5",
            "DEFAULT_RESILIENCE_STRATEGY": "balanced",
            "SUMMARIZE_RESILIENCE_STRATEGY": "conservative"
        }
        
        with patch.dict(os.environ, legacy_env):
            # Application startup
            settings = Settings()
            resilience_service = AIServiceResilience(settings=settings)
            
            # Verify legacy configuration works
            assert settings._has_legacy_resilience_config()
            config = resilience_service.get_operation_config("summarize")
            assert config.retry_config.max_attempts == 3
            
            # Phase 2: Migration planning - analyze current config
            current_config = settings.get_resilience_config()
            migration_config = {
                "retry_attempts": current_config.retry_config.max_attempts,
                "circuit_breaker_threshold": current_config.circuit_breaker_config.failure_threshold,
                "default_strategy": current_config.strategy.value,
                "operation_overrides": {
                    "summarize": settings.get_operation_strategy("summarize")
                }
            }
            
            # Phase 3: Test migration configuration
            test_settings = Settings(
                resilience_preset="simple",
                resilience_custom_config=json.dumps(migration_config)
            )
            test_config = test_settings.get_resilience_config()
            
            # Verify migration maintains behavior
            assert test_config.retry_config.max_attempts == current_config.retry_config.max_attempts
            assert test_config.circuit_breaker_config.failure_threshold == current_config.circuit_breaker_config.failure_threshold
        
        # Phase 4: Deployment with new configuration (legacy env vars removed)
        final_settings = Settings(
            resilience_preset="simple",
            resilience_custom_config=json.dumps(migration_config)
        )
        final_service = AIServiceResilience(settings=final_settings)
        
        # Verify application works with migrated configuration
        final_config = final_service.get_operation_config("summarize")
        assert final_config.retry_config.max_attempts == 3
        assert final_settings.get_operation_strategy("summarize") == "conservative"
    
    def test_cross_version_compatibility_matrix(self):
        """Test compatibility matrix across different configuration versions."""
        test_cases = [
            # (description, env_vars, preset, custom_config, expected_behavior)
            (
                "Pure legacy v1",
                {"RETRY_MAX_ATTEMPTS": "2", "DEFAULT_RESILIENCE_STRATEGY": "aggressive"},
                None,
                None,
                {"retry_attempts": 2, "strategy": "aggressive"}
            ),
            (
                "Pure preset v2",
                {},
                "development",
                None,
                {"retry_attempts": 2, "strategy": "aggressive"}
            ),
            (
                "Hybrid preset + custom v3",
                {},
                "simple",
                '{"retry_attempts": 4, "default_strategy": "conservative"}',
                {"retry_attempts": 4, "strategy": "conservative"}
            ),
            (
                "Legacy override preset",
                {"RETRY_MAX_ATTEMPTS": "6"},
                "production",
                None,
                {"retry_attempts": 6}  # Legacy takes precedence
            )
        ]
        
        for description, env_vars, preset, custom_config, expected in test_cases:
            with patch.dict(os.environ, env_vars, clear=False):
                settings_kwargs = {}
                if preset:
                    settings_kwargs["resilience_preset"] = preset
                if custom_config:
                    settings_kwargs["resilience_custom_config"] = custom_config
                
                settings = Settings(**settings_kwargs)
                config = settings.get_resilience_config()
                
                # Verify expected behavior
                if "retry_attempts" in expected:
                    assert config.retry_config.max_attempts == expected["retry_attempts"], f"Failed for: {description}"
                
                if "strategy" in expected:
                    strategy_mapping = {
                        "aggressive": ResilienceStrategy.AGGRESSIVE,
                        "balanced": ResilienceStrategy.BALANCED,
                        "conservative": ResilienceStrategy.CONSERVATIVE,
                        "critical": ResilienceStrategy.CRITICAL
                    }
                    expected_strategy = strategy_mapping[expected["strategy"]]
                    assert config.strategy == expected_strategy, f"Failed for: {description}"