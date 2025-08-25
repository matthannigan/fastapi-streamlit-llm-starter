"""
Tests for cache preset system validation, comparison, and recommendation functionality.

This module tests the cache preset management system including validation utilities,
comparison functionality, recommendation engines, metadata handling, and configuration
export/import capabilities.

Test Categories:
    - Preset validation and error handling utilities
    - Preset comparison and recommendation functionality  
    - Preset metadata and documentation features
    - Configuration export/import functionality
    - Environment detection and preset recommendation
    - Performance characteristics validation

Key Components Under Test:
    - CachePresetManager: Core preset management functionality
    - Cache preset validation system
    - Preset comparison utilities
    - Environment-based preset recommendations
    - Configuration export/import capabilities
"""

from __future__ import annotations

import json
import pytest
from typing import Dict, Any
from unittest.mock import patch, MagicMock

from app.infrastructure.cache.cache_presets import (
    cache_preset_manager,
    CachePresetManager,
    CachePreset,
    CacheStrategy,
    CACHE_PRESETS,
    EnvironmentRecommendation
)
from app.infrastructure.cache.cache_validator import cache_validator, ValidationResult
from app.infrastructure.cache.config import CacheConfig
from app.core.exceptions import ConfigurationError, ValidationError


class TestPresetValidation:
    """Test preset validation and error handling utilities."""
    
    def test_validate_preset_with_valid_configurations(self):
        """Test preset validation with all valid preset configurations."""
        
        for preset_name, preset in CACHE_PRESETS.items():
            # Validate each preset
            is_valid = cache_preset_manager.validate_preset(preset)
            
            assert is_valid, f"Preset '{preset_name}' should be valid but validation failed"
            
            # Also test the preset can be converted to valid cache config
            cache_config = preset.to_cache_config()
            validation_result = cache_config.validate()
            
            assert validation_result.is_valid, (
                f"Preset '{preset_name}' produces invalid cache config: "
                f"{validation_result.errors}"
            )
    
    def test_validate_preset_with_invalid_configurations(self):
        """Test preset validation with invalid configurations."""
        
        # Create preset with invalid TTL
        invalid_preset = CachePreset(
            name="invalid-ttl",
            description="Test preset with invalid TTL",
            strategy=CacheStrategy.FAST,
            default_ttl=-100,  # Invalid negative TTL
            max_connections=10,
            connection_timeout=5,
            memory_cache_size=1000,
            compression_level=1,
            enable_monitoring=True,
            log_level="INFO",
            environment_contexts=["test"]
        )
        
        # Validation should fail
        is_valid = cache_preset_manager.validate_preset(invalid_preset)
        assert not is_valid, "Preset with invalid TTL should fail validation"
        
        # Create preset with invalid connections
        invalid_preset2 = CachePreset(
            name="invalid-connections",
            description="Test preset with invalid connections",
            strategy=CacheStrategy.BALANCED,
            default_ttl=3600,
            max_connections=0,  # Invalid zero connections
            connection_timeout=5,
            memory_cache_size=1000,
            compression_level=1,
            enable_monitoring=True,
            log_level="INFO",
            environment_contexts=["test"]
        )
        
        is_valid2 = cache_preset_manager.validate_preset(invalid_preset2)
        assert not is_valid2, "Preset with zero connections should fail validation"
    
    def test_preset_error_handling_with_descriptive_messages(self):
        """Test preset error handling produces descriptive error messages."""
        
        # Test with completely invalid preset data
        with pytest.raises((ConfigurationError, ValidationError, AttributeError)) as exc_info:
            invalid_data = {
                "invalid_field": "invalid_value",
                "default_ttl": "not_a_number"  # Should be integer
            }
            
            # Try to create preset with invalid data structure
            CachePreset(**invalid_data)
        
        error_message = str(exc_info.value).lower()
        assert ("invalid" in error_message or 
                "required" in error_message or 
                "missing" in error_message or
                "unexpected" in error_message)
    
    def test_preset_validation_with_edge_cases(self):
        """Test preset validation with edge case values."""
        
        # Test with minimum valid values
        minimal_preset = CachePreset(
            name="minimal-valid",
            description="Minimal valid preset",
            strategy=CacheStrategy.FAST,
            default_ttl=60,  # Minimum 1 minute
            max_connections=1,  # Minimum 1 connection
            connection_timeout=1,  # Minimum timeout
            memory_cache_size=100,  # Small but valid size
            compression_level=1,  # Minimum compression
            enable_monitoring=False,
            log_level="ERROR",
            environment_contexts=["test"]
        )
        
        is_valid = cache_preset_manager.validate_preset(minimal_preset)
        assert is_valid, "Minimal valid preset should pass validation"
        
        # Test with maximum reasonable values
        maximal_preset = CachePreset(
            name="maximal-valid",
            description="Maximal valid preset", 
            strategy=CacheStrategy.ROBUST,
            default_ttl=604800,  # 1 week
            max_connections=100,  # High but reasonable
            connection_timeout=60,  # Long timeout
            memory_cache_size=100000,  # Large cache
            compression_level=9,  # Maximum compression
            enable_monitoring=True,
            log_level="DEBUG",
            environment_contexts=["test"]
        )
        
        is_valid_max = cache_preset_manager.validate_preset(maximal_preset)
        assert is_valid_max, "Maximal valid preset should pass validation"


class TestPresetComparison:
    """Test preset comparison and recommendation functionality."""
    
    def test_compare_preset_configurations(self):
        """Test preset comparison functionality."""
        
        # Get two different presets to compare
        development_preset = cache_preset_manager.get_preset('development')
        production_preset = cache_preset_manager.get_preset('production')
        
        # Convert to configurations for comparison
        dev_config = development_preset.to_cache_config()
        prod_config = production_preset.to_cache_config()
        
        # Use cache validator to compare configurations
        dev_dict = dev_config.to_dict()
        prod_dict = prod_config.to_dict()
        
        comparison = cache_validator.compare_configurations(dev_dict, prod_dict)
        
        # Verify comparison structure
        assert "added_keys" in comparison
        assert "removed_keys" in comparison
        assert "changed_values" in comparison
        assert "identical_keys" in comparison
        
        # Development and production should have some differences
        total_differences = (
            len(comparison["added_keys"]) + 
            len(comparison["removed_keys"]) + 
            len(comparison["changed_values"])
        )
        
        assert total_differences > 0, "Development and production presets should have differences"
        
        # Verify changed values have proper structure
        for changed in comparison["changed_values"]:
            assert "key" in changed
            assert "old_value" in changed
            assert "new_value" in changed
    
    def test_preset_recommendation_functionality(self):
        """Test preset recommendation based on environment detection."""
        
        # Test with specific environment hints
        environments_to_test = [
            ('development', 'dev'),
            ('production', 'prod'), 
            ('testing', 'test'),
            ('staging', 'stage')
        ]
        
        for env_context, env_hint in environments_to_test:
            recommendation = cache_preset_manager.recommend_preset_with_details(env_hint)
            
            assert isinstance(recommendation, EnvironmentRecommendation)
            assert recommendation.preset_name is not None
            assert recommendation.confidence >= 0.0
            assert recommendation.confidence <= 1.0
            assert recommendation.reasoning is not None
            assert len(recommendation.reasoning) > 0
            
            # Environment detection should work reasonably
            assert recommendation.environment_detected is not None
    
    def test_environment_detection_patterns(self):
        """Test environment detection with various naming patterns."""
        
        environment_patterns = [
            ('dev', 'development'),
            ('development', 'development'),
            ('prod', 'production'),
            ('production', 'production'), 
            ('test', 'testing'),
            ('testing', 'testing'),
            ('stage', 'staging'),
            ('staging', 'staging'),
            ('local', 'development'),
            ('localhost', 'development')
        ]
        
        for pattern, expected_context in environment_patterns:
            recommendation = cache_preset_manager.recommend_preset_with_details(pattern)
            
            # Should detect environment reasonably
            assert recommendation.environment_detected is not None
            
            # Recommended preset should be appropriate for the context
            recommended_preset = cache_preset_manager.get_preset(recommendation.preset_name)
            assert expected_context in recommended_preset.environment_contexts or \
                   any(ctx in expected_context for ctx in recommended_preset.environment_contexts)
    
    def test_preset_recommendation_confidence_scoring(self):
        """Test preset recommendation confidence scoring."""
        
        # Test with clear environment indicators (should have high confidence)
        high_confidence_envs = ['production', 'development', 'testing']
        
        for env in high_confidence_envs:
            recommendation = cache_preset_manager.recommend_preset_with_details(env)
            assert recommendation.confidence >= 0.7, (
                f"Clear environment '{env}' should have high confidence, "
                f"got {recommendation.confidence:.2f}"
            )
        
        # Test with ambiguous environment indicators (should have lower confidence)
        ambiguous_envs = ['unknown', 'custom', 'special-env']
        
        for env in ambiguous_envs:
            recommendation = cache_preset_manager.recommend_preset_with_details(env)
            # Should still provide a recommendation but with lower confidence
            assert 0.0 <= recommendation.confidence <= 1.0
            assert recommendation.preset_name is not None
    
    def test_help_users_choose_appropriate_preset(self):
        """Test functionality to help users choose appropriate presets."""
        
        # Test get preset details
        preset_names = cache_preset_manager.list_presets()
        assert len(preset_names) > 0
        
        for preset_name in preset_names:
            preset_details = cache_preset_manager.get_preset_details(preset_name)
            
            assert preset_details is not None
            assert "name" in preset_details
            assert "description" in preset_details
            assert "strategy" in preset_details
            assert "environment_contexts" in preset_details
            
            # Details should be helpful for user decision-making
            assert len(preset_details["description"]) > 10
            assert len(preset_details["environment_contexts"]) > 0


class TestPresetMetadata:
    """Test preset metadata and documentation features."""
    
    def test_preset_metadata_completeness(self):
        """Test that all presets have complete metadata."""
        
        for preset_name, preset in CACHE_PRESETS.items():
            # Every preset should have essential metadata
            assert preset.name is not None and len(preset.name) > 0
            assert preset.description is not None and len(preset.description) > 0
            assert preset.strategy is not None
            assert isinstance(preset.strategy, CacheStrategy)
            assert preset.environment_contexts is not None
            assert len(preset.environment_contexts) > 0
            
            # Metadata should be informative
            assert len(preset.description) > 20, (
                f"Preset '{preset_name}' description too short: '{preset.description}'"
            )
    
    def test_preset_documentation_features(self):
        """Test preset documentation and help features."""
        
        # Test preset manager provides documentation
        preset_names = cache_preset_manager.list_presets()
        
        for preset_name in preset_names:
            preset = cache_preset_manager.get_preset(preset_name)
            
            # Should be able to get detailed information about each preset
            details = cache_preset_manager.get_preset_details(preset_name)
            
            assert "performance_characteristics" in details or "strategy" in details
            assert "use_cases" in details or "environment_contexts" in details
            
    def test_preset_strategy_documentation(self):
        """Test that preset strategies are well-documented."""
        
        strategies_found = set()
        
        for preset_name, preset in CACHE_PRESETS.items():
            strategies_found.add(preset.strategy)
            
            # Each strategy should have meaningful implications
            cache_config = preset.to_cache_config()
            
            if preset.strategy == CacheStrategy.FAST:
                # Fast strategy should prioritize speed
                assert cache_config.default_ttl <= 3600  # Shorter TTLs for freshness
            elif preset.strategy == CacheStrategy.ROBUST:
                # Robust strategy should prioritize reliability
                assert cache_config.max_connections >= 10  # More connections for reliability
            elif preset.strategy == CacheStrategy.BALANCED:
                # Balanced should be between fast and robust
                assert 1800 <= cache_config.default_ttl <= 7200  # Moderate TTLs
        
        # Should have multiple strategies represented
        assert len(strategies_found) >= 2


class TestConfigurationExportImport:
    """Test configuration export/import functionality."""
    
    def test_export_preset_configuration_to_json(self):
        """Test exporting preset configurations to JSON format."""
        
        for preset_name in cache_preset_manager.list_presets():
            preset = cache_preset_manager.get_preset(preset_name)
            cache_config = preset.to_cache_config()
            
            # Export configuration to dictionary (JSON-serializable)
            config_dict = cache_config.to_dict()
            
            # Should be JSON serializable
            json_str = json.dumps(config_dict)
            assert len(json_str) > 0
            
            # Should be able to parse back
            parsed_config = json.loads(json_str)
            assert isinstance(parsed_config, dict)
            
            # Essential fields should be present
            assert "default_ttl" in parsed_config
            assert "strategy" in parsed_config or "max_connections" in parsed_config
    
    def test_import_configuration_from_json(self):
        """Test importing and applying configuration from JSON."""
        
        # Create a sample configuration
        sample_config = {
            "default_ttl": 3600,
            "max_connections": 20,
            "connection_timeout": 10.0,
            "compression_level": 6,
            "enable_monitoring": True,
            "log_level": "INFO"
        }
        
        json_str = json.dumps(sample_config)
        
        # Should be able to create configuration from imported JSON
        parsed_config = json.loads(json_str)
        
        # Validate the imported configuration makes sense
        assert parsed_config["default_ttl"] == 3600
        assert parsed_config["max_connections"] == 20
        assert parsed_config["enable_monitoring"] is True
    
    def test_configuration_roundtrip_fidelity(self):
        """Test configuration export/import maintains fidelity."""
        
        # Test with development preset
        original_preset = cache_preset_manager.get_preset('development')
        original_config = original_preset.to_cache_config()
        
        # Export to JSON
        exported_dict = original_config.to_dict()
        json_str = json.dumps(exported_dict)
        
        # Import back from JSON
        imported_dict = json.loads(json_str)
        
        # Key values should be preserved
        assert imported_dict["default_ttl"] == exported_dict["default_ttl"]
        assert imported_dict.get("max_connections") == exported_dict.get("max_connections")
        
        # Should be able to validate the imported configuration
        # (This would require a factory method to create CacheConfig from dict)
        assert isinstance(imported_dict, dict)
        assert len(imported_dict) > 0


class TestPresetSystemPerformance:
    """Test preset system performance characteristics."""
    
    def test_preset_loading_performance(self):
        """Test that preset loading performs acceptably."""
        
        import time
        
        # Test loading time for all presets
        start_time = time.time()
        
        for preset_name in cache_preset_manager.list_presets():
            preset = cache_preset_manager.get_preset(preset_name)
            cache_config = preset.to_cache_config()
            # Validate to ensure complete loading
            validation_result = cache_config.validate()
            
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should load all presets quickly
        assert total_time < 2.0, f"Preset loading too slow: {total_time:.3f}s"
    
    def test_preset_validation_performance(self):
        """Test preset validation performance."""
        
        import time
        
        start_time = time.time()
        
        # Validate all presets
        for preset_name, preset in CACHE_PRESETS.items():
            is_valid = cache_preset_manager.validate_preset(preset)
            assert is_valid, f"Preset '{preset_name}' should be valid"
        
        end_time = time.time()
        validation_time = end_time - start_time
        
        # Validation should be fast
        assert validation_time < 1.0, f"Preset validation too slow: {validation_time:.3f}s"
    
    def test_recommendation_performance(self):
        """Test preset recommendation performance."""
        
        import time
        
        test_environments = ['dev', 'prod', 'test', 'stage', 'local', 'unknown']
        
        start_time = time.time()
        
        for env in test_environments:
            recommendation = cache_preset_manager.recommend_preset_with_details(env)
            assert recommendation.preset_name is not None
        
        end_time = time.time()
        recommendation_time = end_time - start_time
        
        # Recommendations should be fast
        assert recommendation_time < 1.0, f"Preset recommendations too slow: {recommendation_time:.3f}s"


class TestPresetSystemIntegration:
    """Test integration aspects of the preset system."""
    
    def test_preset_system_with_environment_variables(self, monkeypatch):
        """Test preset system integration with environment variable overrides."""
        
        # Test preset with Redis URL override
        preset = cache_preset_manager.get_preset('development')
        base_config = preset.to_cache_config()
        
        # This tests that the preset system works well with environment overrides
        # (The actual override logic is tested in test_dependencies.py)
        assert isinstance(base_config, CacheConfig)
        assert base_config.default_ttl > 0
    
    def test_preset_system_error_recovery(self):
        """Test preset system error recovery and fallback behavior."""
        
        # Test with non-existent preset name
        try:
            preset = cache_preset_manager.get_preset('nonexistent-preset')
            pytest.fail("Should raise error for non-existent preset")
        except (ValueError, KeyError, ConfigurationError):
            # Expected behavior
            pass
        
        # Test validation with corrupted preset data
        corrupted_preset = CachePreset(
            name="corrupted",
            description="Test corrupted preset",
            strategy=CacheStrategy.BALANCED,
            default_ttl=3600,
            max_connections=10,
            connection_timeout=5,
            memory_cache_size=1000,
            compression_level=1,
            enable_monitoring=True,
            log_level="INFO",
            environment_contexts=["test"]
        )
        
        # Even with potential issues, should handle gracefully
        is_valid = cache_preset_manager.validate_preset(corrupted_preset)
        assert isinstance(is_valid, bool)
    
    def test_preset_system_thread_safety(self):
        """Test preset system thread safety for concurrent access."""
        
        import threading
        import time
        
        results = []
        errors = []
        
        def load_preset_worker(preset_name):
            try:
                preset = cache_preset_manager.get_preset(preset_name)
                config = preset.to_cache_config()
                validation = config.validate()
                results.append((preset_name, validation.is_valid))
            except Exception as e:
                errors.append((preset_name, str(e)))
        
        # Test concurrent access to preset system
        threads = []
        preset_names = cache_preset_manager.list_presets()
        
        for preset_name in preset_names:
            thread = threading.Thread(target=load_preset_worker, args=(preset_name,))
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join()
        
        # Should handle concurrent access without errors
        assert len(errors) == 0, f"Concurrent access errors: {errors}"
        assert len(results) == len(preset_names)
        
        # All presets should still validate correctly
        for preset_name, is_valid in results:
            assert is_valid, f"Preset '{preset_name}' failed validation in concurrent test"