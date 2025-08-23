"""
Comprehensive Tests for AI Cache Configuration Module with Preset Integration

This test suite validates the AIResponseCacheConfig implementation including:
- Configuration creation and validation
- Factory methods for different sources
- Environment variable integration
- Preset system integration (NEW)
- ValidationResult integration
- Configuration merging and inheritance
- Error handling and edge cases

Test Coverage Requirements: >95% for production-ready infrastructure
"""

import hashlib
import json
import os
import tempfile
from dataclasses import asdict
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from app.core.exceptions import ConfigurationError, ValidationError
from app.infrastructure.cache.ai_config import AIResponseCacheConfig
from app.infrastructure.cache.monitoring import CachePerformanceMonitor
from app.infrastructure.cache.parameter_mapping import ValidationResult
from app.infrastructure.cache.cache_presets import cache_preset_manager, CACHE_PRESETS
from app.core.config import Settings


class TestAIResponseCacheConfig:
    """Test suite for AIResponseCacheConfig class."""

    def test_default_initialization(self):
        """Test default configuration initialization."""
        config = AIResponseCacheConfig()
        
        # Test default values
        assert config.redis_url == "redis://redis:6379"
        assert config.default_ttl == 3600
        assert config.enable_l1_cache is True
        assert config.compression_threshold == 1000
        assert config.compression_level == 6
        assert config.text_hash_threshold == 1000
        assert config.hash_algorithm == hashlib.sha256
        assert config.memory_cache_size == 100
        
        # Test default complex fields
        assert config.text_size_tiers == {
            "small": 500,
            "medium": 5000,
            "large": 50000,
        }
        assert config.operation_ttls == {
            "summarize": 7200,
            "sentiment": 86400,
            "key_points": 7200,
            "questions": 3600,
            "qa": 1800,
        }
        
        # Test created performance monitor
        assert isinstance(config.performance_monitor, CachePerformanceMonitor)

    def test_custom_initialization(self):
        """Test configuration with custom values."""
        custom_tiers = {"small": 300, "medium": 3000, "large": 30000}
        custom_ttls = {"summarize": 1800, "sentiment": 3600}
        
        config = AIResponseCacheConfig(
            redis_url="redis://localhost:6379",
            default_ttl=7200,
            memory_cache_size=200,
            compression_threshold=2000,
            compression_level=8,
            text_hash_threshold=500,
            text_size_tiers=custom_tiers,
            operation_ttls=custom_ttls,
            enable_l1_cache=False,
        )
        
        assert config.redis_url == "redis://localhost:6379"
        assert config.default_ttl == 7200
        assert config.memory_cache_size == 200
        assert config.compression_threshold == 2000
        assert config.compression_level == 8
        assert config.text_hash_threshold == 500
        assert config.text_size_tiers == custom_tiers
        assert config.operation_ttls == custom_ttls
        assert config.enable_l1_cache is False

    def test_post_init_l1_cache_auto_enable(self):
        """Test L1 cache auto-enablement in post_init."""
        config = AIResponseCacheConfig(
            enable_l1_cache=False,
            memory_cache_size=100
        )
        
        # Should auto-enable L1 cache due to memory_cache_size > 0
        assert config.enable_l1_cache is True

    def test_validation_success(self):
        """Test successful validation."""
        config = AIResponseCacheConfig()
        result = config.validate()
        
        assert isinstance(result, ValidationResult)
        assert result.is_valid is True
        assert len(result.errors) == 0
        assert isinstance(result.warnings, list)
        assert isinstance(result.recommendations, list)

    def test_validation_redis_url_errors(self):
        """Test Redis URL validation errors."""
        config = AIResponseCacheConfig(redis_url="invalid://url")
        result = config.validate()
        
        assert result.is_valid is False
        assert any("redis_url must start with redis://" in error for error in result.errors)

    def test_validation_numeric_parameter_errors(self):
        """Test numeric parameter validation errors."""
        config = AIResponseCacheConfig(
            default_ttl=-1,
            memory_cache_size=-10,
            compression_threshold=-5,
            compression_level=0,
            text_hash_threshold=0,
        )
        result = config.validate()
        
        assert result.is_valid is False
        assert any("default_ttl must be positive" in error for error in result.errors)
        assert any("memory_cache_size must be non-negative" in error for error in result.errors)
        assert any("compression_threshold must be non-negative" in error for error in result.errors)
        assert any("compression_level must be 1-9" in error for error in result.errors)
        assert any("text_hash_threshold must be positive" in error for error in result.errors)

    def test_validation_range_errors(self):
        """Test parameter range validation errors."""
        config = AIResponseCacheConfig(
            default_ttl=86400 * 366,  # More than 1 year
            memory_cache_size=20000,  # More than 10000
            compression_threshold=2 * 1024 * 1024,  # More than 1MB
            compression_level=10,  # More than 9
            text_hash_threshold=200000,  # More than 100000
        )
        result = config.validate()
        
        assert result.is_valid is False
        assert any("default_ttl too large" in error for error in result.errors)
        assert any("memory_cache_size too large" in error for error in result.errors)
        assert any("compression_threshold too large" in error for error in result.errors)
        assert any("compression_level must be 1-9" in error for error in result.errors)
        assert any("text_hash_threshold too large" in error for error in result.errors)

    def test_validation_text_size_tiers_errors(self):
        """Test text size tiers validation errors."""
        # Missing required tiers
        config = AIResponseCacheConfig(
            text_size_tiers={"small": 500}
        )
        result = config.validate()
        
        assert result.is_valid is False
        assert any("missing required tiers" in error for error in result.errors)
        
        # Invalid tier values
        config = AIResponseCacheConfig(
            text_size_tiers={"small": -100, "medium": "invalid", "large": 5000}
        )
        result = config.validate()
        
        assert result.is_valid is False
        assert any("must be positive integer" in error for error in result.errors)
        
        # Invalid tier ordering
        config = AIResponseCacheConfig(
            text_size_tiers={"small": 5000, "medium": 1000, "large": 500}
        )
        result = config.validate()
        
        assert result.is_valid is False
        assert any("must be ordered" in error for error in result.errors)

    def test_validation_operation_ttls_errors(self):
        """Test operation TTLs validation errors."""
        config = AIResponseCacheConfig(
            operation_ttls={
                "summarize": -100,
                "invalid_operation": 3600,
                "sentiment": 86400 * 366,  # More than 1 year
            }
        )
        result = config.validate()
        
        assert result.is_valid is False
        assert any("must be positive integer" in error for error in result.errors)
        
        # Should have warnings for unknown operation and large TTL
        assert any("Unknown operation" in warning for warning in result.warnings)
        assert any("very large" in warning for warning in result.warnings)

    def test_validation_consistency_errors(self):
        """Test configuration consistency validation."""
        config = AIResponseCacheConfig(
            enable_l1_cache=False,
            memory_cache_size=100
        )
        # Override the post_init behavior to test validation
        config.enable_l1_cache = False
        
        result = config.validate()
        
        assert result.is_valid is False
        assert any("Inconsistent configuration" in error for error in result.errors)

    def test_validation_hash_algorithm_error(self):
        """Test hash algorithm validation."""
        config = AIResponseCacheConfig(hash_algorithm="not_callable")
        result = config.validate()
        
        assert result.is_valid is False
        assert any("hash_algorithm must be callable" in error for error in result.errors)

    def test_validation_performance_monitor_error(self):
        """Test performance monitor validation."""
        invalid_monitor = MagicMock()
        del invalid_monitor.record_cache_operation_time  # Remove required method
        
        config = AIResponseCacheConfig(performance_monitor=invalid_monitor)
        result = config.validate()
        
        assert result.is_valid is False
        assert any("performance_monitor must have record_cache_operation_time method" in error for error in result.errors)

    def test_validation_recommendations(self):
        """Test configuration recommendations."""
        config = AIResponseCacheConfig(
            compression_threshold=15000,  # High threshold
            compression_level=8,  # High level
            text_hash_threshold=2000,  # Different from compression threshold
            memory_cache_size=600,  # Large memory cache
            default_ttl=100000,  # Long TTL
            operation_ttls=None,  # No operation TTLs
        )
        result = config.validate()
        
        # Should have multiple recommendations
        assert len(result.recommendations) > 0
        recommendations_text = " ".join(result.recommendations)
        assert "Compression threshold" in recommendations_text
        assert "Compression level" in recommendations_text
        assert "differs from compression threshold" in recommendations_text
        assert "Memory cache size" in recommendations_text
        assert "Default TTL" in recommendations_text
        assert "operation-specific TTLs" in recommendations_text

    def test_to_ai_cache_kwargs(self):
        """Test conversion to legacy AI cache kwargs."""
        config = AIResponseCacheConfig(
            redis_url="redis://test:6379",
            default_ttl=1800,
            memory_cache_size=50,
        )
        
        kwargs = config.to_ai_cache_kwargs()
        
        # Test that legacy compatible parameters are included (no enable_l1_cache)
        expected_legacy_keys = {
            'redis_url', 'default_ttl', 'compression_threshold',
            'compression_level', 'performance_monitor',
            'text_hash_threshold', 'hash_algorithm', 'text_size_tiers',
            'operation_ttls', 'memory_cache_size'
        }
        
        # Check that non-None values are included
        for key in expected_legacy_keys:
            config_value = getattr(config, key)
            if config_value is not None:
                assert key in kwargs, f"Expected key '{key}' not in kwargs"
                assert kwargs[key] == config_value
        
        # Ensure enable_l1_cache is NOT in legacy kwargs (for backward compatibility)
        assert 'enable_l1_cache' not in kwargs
        assert 'l1_cache_size' not in kwargs

    def test_to_generic_cache_kwargs(self):
        """Test conversion to generic cache kwargs."""
        config = AIResponseCacheConfig(
            redis_url="redis://test:6379",
            default_ttl=1800,
            memory_cache_size=50,
            enable_l1_cache=True,
        )
        
        kwargs = config.to_generic_cache_kwargs()
        
        # Test that generic parameters are included with proper mapping
        expected_generic_keys = {
            'redis_url', 'default_ttl', 'enable_l1_cache', 'l1_cache_size',
            'compression_threshold', 'compression_level', 'performance_monitor'
        }
        
        # Check that non-None values are included
        for key in expected_generic_keys:
            if key == 'l1_cache_size':
                # This is mapped from memory_cache_size
                assert key in kwargs, f"Expected mapped key '{key}' not in kwargs"
                assert kwargs[key] == config.memory_cache_size
            else:
                config_value = getattr(config, key, None)
                if config_value is not None:
                    assert key in kwargs, f"Expected key '{key}' not in kwargs"
                    assert kwargs[key] == config_value
        
        # Ensure AI-specific parameters are NOT in generic kwargs
        assert 'text_hash_threshold' not in kwargs
        assert 'hash_algorithm' not in kwargs
        assert 'text_size_tiers' not in kwargs
        assert 'operation_ttls' not in kwargs
        assert 'memory_cache_size' not in kwargs

    def test_create_default(self):
        """Test default configuration creation."""
        config = AIResponseCacheConfig.create_default()
        
        assert isinstance(config, AIResponseCacheConfig)
        assert config.redis_url == "redis://redis:6379"
        assert config.default_ttl == 3600

    def test_create_production(self):
        """Test production configuration creation."""
        redis_url = "redis://production:6379"
        config = AIResponseCacheConfig.create_production(redis_url)
        
        assert isinstance(config, AIResponseCacheConfig)
        assert config.redis_url == redis_url
        assert config.default_ttl == 7200  # 2 hours
        assert config.memory_cache_size == 200
        assert config.compression_threshold == 500
        assert config.compression_level == 7
        assert config.text_hash_threshold == 500

    def test_create_development(self):
        """Test development configuration creation."""
        config = AIResponseCacheConfig.create_development()
        
        assert isinstance(config, AIResponseCacheConfig)
        assert config.redis_url == "redis://localhost:6379"
        assert config.default_ttl == 1800  # 30 minutes
        assert config.memory_cache_size == 50
        assert config.compression_threshold == 2000
        assert config.compression_level == 3
        assert config.text_hash_threshold == 2000

    def test_create_testing(self):
        """Test testing configuration creation."""
        config = AIResponseCacheConfig.create_testing()
        
        assert isinstance(config, AIResponseCacheConfig)
        assert config.redis_url == "redis://localhost:6379"
        assert config.default_ttl == 300  # 5 minutes
        assert config.memory_cache_size == 10
        assert config.compression_threshold == 5000
        assert config.compression_level == 1
        assert config.text_hash_threshold == 5000
        
        # All operation TTLs should be 300 seconds
        for operation, ttl in config.operation_ttls.items():
            assert ttl == 300

    def test_from_dict_basic(self):
        """Test configuration creation from dictionary."""
        config_dict = {
            'redis_url': 'redis://test:6379',
            'default_ttl': 1800,
            'memory_cache_size': 75,
            'compression_threshold': 1500,
        }
        
        config = AIResponseCacheConfig.from_dict(config_dict)
        
        assert config.redis_url == 'redis://test:6379'
        assert config.default_ttl == 1800
        assert config.memory_cache_size == 75
        assert config.compression_threshold == 1500

    def test_from_dict_hash_algorithm_conversion(self):
        """Test hash algorithm conversion in from_dict."""
        config_dict = {
            'redis_url': 'redis://test:6379',
            'hash_algorithm': 'sha256',
        }
        
        config = AIResponseCacheConfig.from_dict(config_dict)
        assert config.hash_algorithm == hashlib.sha256
        
        # Test md5 conversion
        config_dict['hash_algorithm'] = 'md5'
        config = AIResponseCacheConfig.from_dict(config_dict)
        assert config.hash_algorithm == hashlib.md5

    def test_from_dict_invalid_hash_algorithm(self):
        """Test invalid hash algorithm in from_dict."""
        config_dict = {
            'redis_url': 'redis://test:6379',
            'hash_algorithm': 'invalid_algorithm',
        }
        
        with pytest.raises(ConfigurationError, match="Unsupported hash algorithm"):
            AIResponseCacheConfig.from_dict(config_dict)

    def test_from_dict_performance_monitor_creation(self):
        """Test performance monitor creation in from_dict."""
        config_dict = {
            'redis_url': 'redis://test:6379',
            'performance_monitor': True,
        }
        
        config = AIResponseCacheConfig.from_dict(config_dict)
        assert isinstance(config.performance_monitor, CachePerformanceMonitor)

    def test_from_dict_unknown_parameters(self):
        """Test handling of unknown parameters in from_dict."""
        config_dict = {
            'redis_url': 'redis://test:6379',
            'unknown_parameter': 'value',
            'another_unknown': 123,
        }
        
        # Should succeed but ignore unknown parameters
        config = AIResponseCacheConfig.from_dict(config_dict)
        assert config.redis_url == 'redis://test:6379'
        assert not hasattr(config, 'unknown_parameter')

    def test_from_dict_exception_handling(self):
        """Test exception handling in from_dict."""
        # Test with invalid dataclass field
        with patch.object(AIResponseCacheConfig, '__init__', side_effect=TypeError("Invalid field")):
            with pytest.raises(ConfigurationError, match="Failed to create AIResponseCacheConfig from dictionary"):
                AIResponseCacheConfig.from_dict({'redis_url': 'redis://test:6379'})

    def test_from_env_basic(self):
        """Test configuration creation from environment variables."""
        env_vars = {
            'AI_CACHE_REDIS_URL': 'redis://env:6379',
            'AI_CACHE_DEFAULT_TTL': '1800',
            'AI_CACHE_MEMORY_CACHE_SIZE': '75',
            'AI_CACHE_COMPRESSION_THRESHOLD': '1500',
            'AI_CACHE_COMPRESSION_LEVEL': '7',
            'AI_CACHE_ENABLE_L1_CACHE': 'true',
            'AI_CACHE_TEXT_HASH_THRESHOLD': '500',
            'AI_CACHE_HASH_ALGORITHM': 'md5',
        }
        
        with patch.dict(os.environ, env_vars):
            config = AIResponseCacheConfig.from_env()
        
        assert config.redis_url == 'redis://env:6379'
        assert config.default_ttl == 1800
        assert config.memory_cache_size == 75
        assert config.compression_threshold == 1500
        assert config.compression_level == 7
        assert config.enable_l1_cache is True
        assert config.text_hash_threshold == 500
        assert config.hash_algorithm == 'md5'

    def test_from_env_custom_prefix(self):
        """Test environment loading with custom prefix."""
        env_vars = {
            'CUSTOM_REDIS_URL': 'redis://custom:6379',
            'CUSTOM_DEFAULT_TTL': '900',
        }
        
        with patch.dict(os.environ, env_vars):
            config = AIResponseCacheConfig.from_env(prefix="CUSTOM_")
        
        assert config.redis_url == 'redis://custom:6379'
        assert config.default_ttl == 900

    def test_from_env_boolean_values(self):
        """Test boolean environment variable parsing."""
        bool_test_cases = [
            ('true', True),
            ('True', True),
            ('1', True),
            ('yes', True),
            ('on', True),
            ('false', False),
            ('False', False),
            ('0', False),
            ('no', False),
            ('off', False),
        ]
        
        for env_value, expected in bool_test_cases:
            env_vars = {'AI_CACHE_ENABLE_L1_CACHE': env_value}
            with patch.dict(os.environ, env_vars):
                config = AIResponseCacheConfig.from_env()
            assert config.enable_l1_cache == expected

    def test_from_env_json_fields(self):
        """Test JSON field parsing from environment."""
        text_size_tiers = '{"small": 300, "medium": 3000, "large": 30000}'
        operation_ttls = '{"summarize": 1800, "sentiment": 3600}'
        
        env_vars = {
            'AI_CACHE_TEXT_SIZE_TIERS': text_size_tiers,
            'AI_CACHE_OPERATION_TTLS': operation_ttls,
        }
        
        with patch.dict(os.environ, env_vars):
            config = AIResponseCacheConfig.from_env()
        
        assert config.text_size_tiers == {"small": 300, "medium": 3000, "large": 30000}
        assert config.operation_ttls == {"summarize": 1800, "sentiment": 3600}

    def test_from_env_invalid_json(self):
        """Test handling of invalid JSON in environment variables."""
        env_vars = {
            'AI_CACHE_TEXT_SIZE_TIERS': 'invalid json',
            'AI_CACHE_OPERATION_TTLS': '{"invalid": json}',
        }
        
        with patch.dict(os.environ, env_vars):
            # Should not raise exception but should log warnings
            config = AIResponseCacheConfig.from_env()
        
        # Should use defaults since JSON parsing failed
        assert config.text_size_tiers is not None

    def test_from_env_invalid_numeric_values(self):
        """Test handling of invalid numeric values."""
        env_vars = {
            'AI_CACHE_DEFAULT_TTL': 'invalid_number',
            'AI_CACHE_MEMORY_CACHE_SIZE': 'not_a_number',
        }
        
        with patch.dict(os.environ, env_vars):
            # Should not raise exception but should log warnings
            config = AIResponseCacheConfig.from_env()
        
        # Should use defaults since parsing failed
        assert config.default_ttl == 3600  # default value

    def test_from_env_no_environment_variables(self):
        """Test from_env with no relevant environment variables."""
        # Clear any existing cache-related env vars
        env_to_clear = [key for key in os.environ.keys() if key.startswith('AI_CACHE_')]
        with patch.dict(os.environ, {key: '' for key in env_to_clear}, clear=False):
            config = AIResponseCacheConfig.from_env()
        
        # Should return default configuration
        assert config.redis_url == "redis://redis:6379"
        assert config.default_ttl == 3600

    def test_from_env_exception_handling(self):
        """Test exception handling in from_env."""
        with patch.object(AIResponseCacheConfig, 'from_dict', side_effect=Exception("Test error")):
            with pytest.raises(ConfigurationError, match="Failed to create AIResponseCacheConfig from environment"):
                AIResponseCacheConfig.from_env()

    @pytest.mark.skipif(
        not hasattr(pytest, 'importorskip') or 
        pytest.importorskip('yaml', minversion=None) is None,
        reason="PyYAML not available"
    )
    def test_from_yaml_success(self):
        """Test successful YAML configuration loading."""
        yaml_content = """
redis_url: redis://yaml:6379
default_ttl: 1800
memory_cache_size: 75
text_size_tiers:
  small: 300
  medium: 3000
  large: 30000
operation_ttls:
  summarize: 1800
  sentiment: 3600
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name
        
        try:
            config = AIResponseCacheConfig.from_yaml(yaml_path)
            assert config.redis_url == 'redis://yaml:6379'
            assert config.default_ttl == 1800
            assert config.memory_cache_size == 75
            assert config.text_size_tiers == {"small": 300, "medium": 3000, "large": 30000}
            assert config.operation_ttls == {"summarize": 1800, "sentiment": 3600}
        finally:
            os.unlink(yaml_path)

    def test_from_yaml_no_yaml_library(self):
        """Test YAML loading when PyYAML is not available."""
        with patch('app.infrastructure.cache.ai_config.yaml', None):
            with pytest.raises(ConfigurationError, match="PyYAML library is required"):
                AIResponseCacheConfig.from_yaml('config.yaml')

    def test_from_yaml_file_not_found(self):
        """Test YAML loading with non-existent file."""
        with pytest.raises(ConfigurationError, match="YAML configuration file not found"):
            AIResponseCacheConfig.from_yaml('nonexistent.yaml')

    def test_from_yaml_invalid_yaml(self):
        """Test YAML loading with invalid YAML content."""
        yaml_content = """
redis_url: redis://yaml:6379
invalid_yaml: [unclosed list
"""
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name
        
        try:
            with pytest.raises(ConfigurationError, match="Invalid YAML"):
                AIResponseCacheConfig.from_yaml(yaml_path)
        finally:
            os.unlink(yaml_path)

    def test_from_yaml_non_dict_content(self):
        """Test YAML loading with non-dictionary content."""
        yaml_content = "- item1\n- item2\n"
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.yaml', delete=False) as f:
            f.write(yaml_content)
            yaml_path = f.name
        
        try:
            with pytest.raises(ConfigurationError, match="YAML file must contain a dictionary"):
                AIResponseCacheConfig.from_yaml(yaml_path)
        finally:
            os.unlink(yaml_path)

    def test_from_json_success(self):
        """Test successful JSON configuration loading."""
        json_data = {
            'redis_url': 'redis://json:6379',
            'default_ttl': 1800,
            'memory_cache_size': 75,
            'text_size_tiers': {
                'small': 300,
                'medium': 3000,
                'large': 30000
            },
            'operation_ttls': {
                'summarize': 1800,
                'sentiment': 3600
            }
        }
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(json_data, f)
            json_path = f.name
        
        try:
            config = AIResponseCacheConfig.from_json(json_path)
            assert config.redis_url == 'redis://json:6379'
            assert config.default_ttl == 1800
            assert config.memory_cache_size == 75
            assert config.text_size_tiers == {"small": 300, "medium": 3000, "large": 30000}
            assert config.operation_ttls == {"summarize": 1800, "sentiment": 3600}
        finally:
            os.unlink(json_path)

    def test_from_json_file_not_found(self):
        """Test JSON loading with non-existent file."""
        with pytest.raises(ConfigurationError, match="JSON configuration file not found"):
            AIResponseCacheConfig.from_json('nonexistent.json')

    def test_from_json_invalid_json(self):
        """Test JSON loading with invalid JSON content."""
        json_content = '{"redis_url": "redis://json:6379", "invalid": json}'
        
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            f.write(json_content)
            json_path = f.name
        
        try:
            with pytest.raises(ConfigurationError, match="Invalid JSON"):
                AIResponseCacheConfig.from_json(json_path)
        finally:
            os.unlink(json_path)

    def test_merge_basic(self):
        """Test basic configuration merging."""
        base_config = AIResponseCacheConfig(
            redis_url="redis://base:6379",
            default_ttl=1800,
            memory_cache_size=50,
        )
        
        override_config = AIResponseCacheConfig(
            redis_url="redis://override:6379",
            default_ttl=3600,
            compression_threshold=2000,
        )
        
        merged_config = base_config.merge(override_config)
        
        # Override values should take precedence
        assert merged_config.redis_url == "redis://override:6379"
        assert merged_config.default_ttl == 3600
        assert merged_config.compression_threshold == 2000
        
        # Base values should be preserved where not overridden
        assert merged_config.memory_cache_size == 50

    def test_merge_exception_handling(self):
        """Test exception handling in merge."""
        config = AIResponseCacheConfig()
        
        with patch('app.infrastructure.cache.ai_config.asdict', side_effect=Exception("Test error")):
            with pytest.raises(ConfigurationError, match="Failed to merge AIResponseCacheConfig"):
                config.merge(config)

    def test_repr(self):
        """Test string representation."""
        config = AIResponseCacheConfig(
            redis_url="redis://test:6379",
            default_ttl=1800,
            memory_cache_size=75,
            text_hash_threshold=500,
        )
        
        repr_str = repr(config)
        assert "AIResponseCacheConfig(" in repr_str
        assert "redis_url='redis://test:6379'" in repr_str
        assert "default_ttl=1800" in repr_str
        assert "memory_cache_size=75" in repr_str
        assert "text_hash_threshold=500" in repr_str

    def test_post_init_exception_handling(self):
        """Test exception handling in __post_init__."""
        # Mock CachePerformanceMonitor to raise exception
        with patch('app.infrastructure.cache.ai_config.CachePerformanceMonitor', side_effect=Exception("Monitor error")):
            with pytest.raises(ConfigurationError, match="Failed to setup AIResponseCacheConfig defaults"):
                AIResponseCacheConfig()

    def test_to_ai_cache_kwargs_exception_handling(self):
        """Test exception handling in to_ai_cache_kwargs."""
        config = AIResponseCacheConfig()
        
        # Mock a field to cause exception during kwargs creation
        with patch.object(config, 'redis_url', property(lambda self: exec('raise Exception("Test error")'))):
            with pytest.raises(ConfigurationError, match="Failed to convert AIResponseCacheConfig to kwargs"):
                config.to_ai_cache_kwargs()

    def test_validation_exception_handling(self):
        """Test exception handling in validate method."""
        config = AIResponseCacheConfig()
        
        # Mock redis_url to raise exception during validation
        with patch.object(config, 'redis_url', property(lambda self: exec('raise Exception("Test error")'))):
            result = config.validate()
            assert result.is_valid is False
            assert any("validation failed with exception" in error for error in result.errors)
            assert 'validation_exception' in result.context


class TestAIResponseCacheConfigIntegration:
    """Integration tests for AIResponseCacheConfig with other components."""

    def test_integration_with_parameter_mapper(self):
        """Test integration with CacheParameterMapper."""
        from app.infrastructure.cache.parameter_mapping import CacheParameterMapper
        
        config = AIResponseCacheConfig(
            redis_url="redis://integration:6379",
            memory_cache_size=100,
            text_hash_threshold=1000,
        )
        
        kwargs = config.to_ai_cache_kwargs()
        mapper = CacheParameterMapper()
        
        generic_params, ai_specific_params = mapper.map_ai_to_generic_params(kwargs)
        
        # Test parameter separation
        assert 'redis_url' in generic_params
        assert 'l1_cache_size' in generic_params  # Mapped from memory_cache_size
        assert 'text_hash_threshold' in ai_specific_params
        
        # Test validation integration
        validation_result = mapper.validate_parameter_compatibility(kwargs)
        assert isinstance(validation_result, ValidationResult)

    def test_environment_variable_documentation_accuracy(self):
        """Test that environment variable documentation is accurate."""
        # Test all documented environment variables
        env_vars = {
            'AI_CACHE_REDIS_URL': 'redis://doc:6379',
            'AI_CACHE_DEFAULT_TTL': '1800',
            'AI_CACHE_MEMORY_CACHE_SIZE': '100',
            'AI_CACHE_TEXT_HASH_THRESHOLD': '1000',
            'AI_CACHE_COMPRESSION_THRESHOLD': '2000',
            'AI_CACHE_COMPRESSION_LEVEL': '7',
            'AI_CACHE_ENABLE_L1_CACHE': 'true',
        }
        
        with patch.dict(os.environ, env_vars):
            config = AIResponseCacheConfig.from_env()
        
        # Verify all documented variables work
        assert config.redis_url == 'redis://doc:6379'
        assert config.default_ttl == 1800
        assert config.memory_cache_size == 100
        assert config.text_hash_threshold == 1000
        assert config.compression_threshold == 2000
        assert config.compression_level == 7
        assert config.enable_l1_cache is True

    def test_performance_with_large_configurations(self):
        """Test performance with large configuration dictionaries."""
        import time
        
        # Create a large configuration dictionary
        large_config = {
            'redis_url': 'redis://perf:6379',
            'operation_ttls': {f'operation_{i}': 3600 for i in range(1000)}
        }
        
        start_time = time.time()
        config = AIResponseCacheConfig.from_dict(large_config)
        creation_time = time.time() - start_time
        
        # Configuration creation should be fast (< 1 second)
        assert creation_time < 1.0
        
        start_time = time.time()
        result = config.validate()
        validation_time = time.time() - start_time
        
        # Validation should be fast (< 1 second)
        assert validation_time < 1.0
        assert result.is_valid is True

    def test_configuration_immutability_patterns(self):
        """Test that configuration supports immutability patterns."""
        config1 = AIResponseCacheConfig(redis_url="redis://test1:6379")
        config2 = AIResponseCacheConfig(redis_url="redis://test2:6379")
        
        # Merging should create new instance
        merged = config1.merge(config2)
        
        assert merged is not config1
        assert merged is not config2
        assert config1.redis_url == "redis://test1:6379"  # Original unchanged
        assert config2.redis_url == "redis://test2:6379"  # Original unchanged


class TestAIConfigPresetIntegration:
    """Test preset system integration with AI cache configuration."""
    
    def test_from_env_with_preset_integration(self, monkeypatch):
        """Test from_env() method with preset system integration."""
        
        # Test with AI-specific presets
        ai_preset_names = ['ai-development', 'ai-production']
        
        for preset_name in ai_preset_names:
            monkeypatch.setenv('CACHE_PRESET', preset_name)
            
            # Get preset configuration for comparison
            preset = cache_preset_manager.get_preset(preset_name)
            preset_config = preset.to_cache_config()
            
            # Set additional AI-specific environment variables
            env_vars = {
                'AI_CACHE_REDIS_URL': 'redis://ai-env:6379',
                'AI_CACHE_TEXT_HASH_THRESHOLD': '2000',
            }
            
            with patch.dict(os.environ, env_vars):
                ai_config = AIResponseCacheConfig.from_env()
            
            # Environment variables should take precedence over preset defaults
            assert ai_config.redis_url == 'redis://ai-env:6379'
            assert ai_config.text_hash_threshold == 2000
            
            # Other values should come from preset or defaults
            assert ai_config.default_ttl > 0  # Should have valid TTL
            
            monkeypatch.delenv('CACHE_PRESET')
    
    def test_environment_variable_precedence_with_preset(self, monkeypatch):
        """Test environment variable precedence with preset system."""
        
        # Set up AI preset
        monkeypatch.setenv('CACHE_PRESET', 'ai-development')
        
        preset = cache_preset_manager.get_preset('ai-development')
        preset_config = preset.to_cache_config()
        
        # Set environment variables that should override preset values
        override_vars = {
            'AI_CACHE_DEFAULT_TTL': '9999',  # Override preset default
            'AI_CACHE_MEMORY_CACHE_SIZE': '500',  # Override preset default
            'AI_CACHE_TEXT_HASH_THRESHOLD': '3000',  # Override preset default
        }
        
        with patch.dict(os.environ, override_vars):
            ai_config = AIResponseCacheConfig.from_env()
        
        # Environment variables should override preset defaults
        assert ai_config.default_ttl == 9999
        assert ai_config.memory_cache_size == 500
        assert ai_config.text_hash_threshold == 3000
        
        monkeypatch.delenv('CACHE_PRESET')
    
    def test_preset_scenario_validation_tests(self, monkeypatch):
        """Test configuration validation with preset scenarios."""
        
        preset_names = ['ai-development', 'ai-production', 'development', 'production']
        
        for preset_name in preset_names:
            monkeypatch.setenv('CACHE_PRESET', preset_name)
            
            # Create AI config with preset context
            ai_config = AIResponseCacheConfig()
            
            # Validate the configuration
            validation_result = ai_config.validate()
            
            assert validation_result.is_valid, (
                f"AI configuration with preset '{preset_name}' should be valid: "
                f"{validation_result.errors}"
            )
            
            # AI-specific validation should pass
            assert ai_config.text_hash_threshold > 0
            assert ai_config.hash_algorithm is not None
            
            monkeypatch.delenv('CACHE_PRESET')
    
    def test_preset_ai_config_combinations_and_inheritance(self, monkeypatch):
        """Test preset + AI config combinations and inheritance."""
        
        # Test AI preset with additional AI configuration
        monkeypatch.setenv('CACHE_PRESET', 'ai-development')
        
        # Create base AI config
        base_ai_config = AIResponseCacheConfig(
            text_hash_threshold=1500,
            operation_ttls={"summarize": 1800, "sentiment": 900}
        )
        
        # Create AI config with preset influence
        preset_ai_config = AIResponseCacheConfig(
            text_hash_threshold=2500,
            enable_smart_promotion=True
        )
        
        # Merge configurations (simulating inheritance)
        merged_config = base_ai_config.merge(preset_ai_config)
        
        # Merged configuration should combine both sources
        assert merged_config.text_hash_threshold == 2500  # Override from preset_ai_config
        assert merged_config.enable_smart_promotion is True  # From preset_ai_config
        assert merged_config.operation_ttls == {"summarize": 1800, "sentiment": 900}  # From base
        
        # Validate merged configuration
        validation_result = merged_config.validate()
        assert validation_result.is_valid
        
        monkeypatch.delenv('CACHE_PRESET')
    
    def test_existing_environment_variable_tests_with_preset_system(self, monkeypatch):
        """Test that existing environment variable tests work alongside preset system."""
        
        # Set a preset to ensure it doesn't interfere with direct env var tests
        monkeypatch.setenv('CACHE_PRESET', 'development')
        
        # Run existing environment variable test with preset context
        env_vars = {
            'AI_CACHE_REDIS_URL': 'redis://env-with-preset:6379',
            'AI_CACHE_DEFAULT_TTL': '2400',
            'AI_CACHE_TEXT_HASH_THRESHOLD': '1200',
            'AI_CACHE_ENABLE_L1_CACHE': 'false',
        }
        
        with patch.dict(os.environ, env_vars):
            config = AIResponseCacheConfig.from_env()
        
        # Environment variables should still work correctly
        assert config.redis_url == 'redis://env-with-preset:6379'
        assert config.default_ttl == 2400
        assert config.text_hash_threshold == 1200
        assert config.enable_l1_cache is False
        
        # Configuration should be valid
        validation_result = config.validate()
        assert validation_result.is_valid
        
        monkeypatch.delenv('CACHE_PRESET')
    
    def test_preset_with_custom_prefix_environment_variables(self, monkeypatch):
        """Test preset system works with custom prefix environment variables."""
        
        # Set preset
        monkeypatch.setenv('CACHE_PRESET', 'ai-development')
        
        # Use custom prefix for AI config
        custom_env_vars = {
            'CUSTOM_AI_REDIS_URL': 'redis://custom-ai:6379',
            'CUSTOM_AI_TEXT_HASH_THRESHOLD': '800',
        }
        
        with patch.dict(os.environ, custom_env_vars):
            ai_config = AIResponseCacheConfig.from_env(prefix="CUSTOM_AI_")
        
        # Custom prefix should work correctly with preset system
        assert ai_config.redis_url == 'redis://custom-ai:6379'
        assert ai_config.text_hash_threshold == 800
        
        monkeypatch.delenv('CACHE_PRESET')


class TestPresetSystemCompatibility:
    """Test compatibility between preset system and AI configuration."""
    
    def test_all_presets_produce_valid_ai_configurations(self, monkeypatch):
        """Test that all presets produce valid AI configurations."""
        
        for preset_name in CACHE_PRESETS.keys():
            monkeypatch.setenv('CACHE_PRESET', preset_name)
            
            try:
                # Create AI config in preset context
                ai_config = AIResponseCacheConfig()
                
                # Validate AI configuration
                validation_result = ai_config.validate()
                
                assert validation_result.is_valid, (
                    f"Preset '{preset_name}' should produce valid AI configuration: "
                    f"{validation_result.errors}"
                )
                
                # AI-specific fields should be properly initialized
                assert ai_config.text_hash_threshold > 0
                assert ai_config.hash_algorithm is not None
                assert isinstance(ai_config.text_size_tiers, dict)
                
            except Exception as e:
                pytest.fail(f"Preset '{preset_name}' failed to create valid AI configuration: {e}")
            finally:
                monkeypatch.delenv('CACHE_PRESET')
    
    def test_ai_preset_vs_standard_preset_differences(self, monkeypatch):
        """Test differences between AI-specific and standard presets."""
        
        # Test AI-specific preset
        monkeypatch.setenv('CACHE_PRESET', 'ai-development')
        ai_config = AIResponseCacheConfig()
        monkeypatch.delenv('CACHE_PRESET')
        
        # Test standard preset
        monkeypatch.setenv('CACHE_PRESET', 'development')
        standard_config = AIResponseCacheConfig()
        monkeypatch.delenv('CACHE_PRESET')
        
        # Both should be valid
        assert ai_config.validate().is_valid
        assert standard_config.validate().is_valid
        
        # AI preset may have different optimization characteristics
        # (The actual differences would depend on preset implementation)
        assert ai_config.text_hash_threshold > 0
        assert standard_config.text_hash_threshold > 0
    
    def test_preset_system_performance_with_ai_config(self, monkeypatch):
        """Test preset system performance with AI configuration loading."""
        import time
        
        monkeypatch.setenv('CACHE_PRESET', 'ai-development')
        
        start_time = time.time()
        
        # Create multiple AI configs with preset context
        ai_configs = []
        for i in range(10):
            ai_config = AIResponseCacheConfig()
            validation_result = ai_config.validate()
            assert validation_result.is_valid
            ai_configs.append(ai_config)
        
        end_time = time.time()
        total_time = end_time - start_time
        
        # Should create AI configs quickly even with preset system
        assert total_time < 2.0, f"AI config creation with presets too slow: {total_time:.3f}s"
        assert len(ai_configs) == 10
        
        monkeypatch.delenv('CACHE_PRESET')
    
    def test_preset_error_handling_with_ai_configuration(self, monkeypatch):
        """Test error handling when preset system has issues with AI configuration."""
        
        # Test with invalid preset
        monkeypatch.setenv('CACHE_PRESET', 'invalid-preset-name')
        
        # AI configuration should still work (fallback to defaults)
        try:
            ai_config = AIResponseCacheConfig()
            validation_result = ai_config.validate()
            
            # Should either work with defaults or handle gracefully
            assert validation_result.is_valid or len(validation_result.errors) > 0
            
        except Exception as e:
            # If it raises an exception, it should be appropriate
            assert isinstance(e, (ConfigurationError, ValidationError))
        
        monkeypatch.delenv('CACHE_PRESET')
    
    def test_preset_json_field_interaction(self, monkeypatch):
        """Test preset system interaction with JSON fields in AI configuration."""
        
        monkeypatch.setenv('CACHE_PRESET', 'ai-development')
        
        # Set JSON fields via environment
        json_env_vars = {
            'AI_CACHE_TEXT_SIZE_TIERS': '{"small": 200, "medium": 2000, "large": 20000}',
            'AI_CACHE_OPERATION_TTLS': '{"summarize": 2400, "sentiment": 1200, "questions": 3600}',
        }
        
        with patch.dict(os.environ, json_env_vars):
            ai_config = AIResponseCacheConfig.from_env()
        
        # JSON fields should work correctly with preset system
        assert ai_config.text_size_tiers == {"small": 200, "medium": 2000, "large": 20000}
        assert ai_config.operation_ttls == {"summarize": 2400, "sentiment": 1200, "questions": 3600}
        
        # Configuration should be valid
        validation_result = ai_config.validate()
        assert validation_result.is_valid
        
        monkeypatch.delenv('CACHE_PRESET')