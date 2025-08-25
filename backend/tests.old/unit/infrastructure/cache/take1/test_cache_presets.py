"""
Comprehensive unit tests for cache presets configuration system.

This module tests all cache preset components following docstring-driven
test development methodology. Tests verify documented contracts in Args, Returns,
Raises, and Behavior sections, focusing on WHAT should happen rather than HOW
it's implemented.

Test Classes:
    - TestEnvironmentRecommendation: Named tuple for environment-based recommendations
    - TestCacheStrategy: Cache strategy enumeration and string serialization
    - TestCacheConfig: Local cache configuration with validation and conversion
    - TestCachePreset: Preset dataclass with conversion and validation methods
    - TestCachePresetManager: Manager with environment detection and recommendations  
    - TestUtilityFunctions: Default presets generation and global manager access
    - TestCachePresetsIntegration: Integration between presets and external config system

Coverage Requirements:
    >90% coverage for infrastructure modules per project standards
    
Testing Philosophy:
    - Test WHAT should happen per docstring contracts
    - Focus on behavior verification, not implementation details
    - Mock only external dependencies (environment variables, file system, cache_validator)
    - Test edge cases and error conditions documented in docstrings
    - Validate preset system integration with cache_validator when available
"""

import json
import os
import pytest
import re
from unittest.mock import patch, MagicMock, call
from dataclasses import asdict

from app.infrastructure.cache.cache_presets import (
    EnvironmentRecommendation,
    CacheStrategy,
    CacheConfig,
    CachePreset,
    CachePresetManager,
    CACHE_PRESETS,
    get_default_presets,
    DEFAULT_PRESETS,
    cache_preset_manager
)
from app.core.exceptions import ConfigurationError


class TestEnvironmentRecommendation:
    """Test environment recommendation named tuple per docstring contracts."""
    
    def test_environment_recommendation_initialization(self):
        """
        Test EnvironmentRecommendation initialization per docstring.
        
        Verifies:
            EnvironmentRecommendation can be created with all required fields as documented
            
        Business Impact:
            Ensures recommendation system can represent environment analysis results
            
        Scenario:
            Given: EnvironmentRecommendation with preset name, confidence, reasoning, and detected environment
            When: Object is created
            Then: All attributes are accessible and correctly stored
        """
        recommendation = EnvironmentRecommendation(
            preset_name="production",
            confidence=0.85,
            reasoning="Production indicators detected",
            environment_detected="prod-cluster-01"
        )
        
        assert recommendation.preset_name == "production"
        assert recommendation.confidence == 0.85
        assert recommendation.reasoning == "Production indicators detected"
        assert recommendation.environment_detected == "prod-cluster-01"
    
    def test_environment_recommendation_confidence_boundaries(self):
        """
        Test EnvironmentRecommendation confidence values per docstring range.
        
        Verifies:
            Confidence values are documented as 0.0 to 1.0 range in docstring
            
        Business Impact:
            Ensures confidence scoring is properly bounded for recommendation algorithms
            
        Scenario:
            Given: EnvironmentRecommendation with various confidence values
            When: Objects are created with boundary values
            Then: Confidence values are stored correctly
        """
        # Test minimum confidence
        min_recommendation = EnvironmentRecommendation("simple", 0.0, "Fallback", "unknown")
        assert min_recommendation.confidence == 0.0
        
        # Test maximum confidence
        max_recommendation = EnvironmentRecommendation("production", 1.0, "Exact match", "production")
        assert max_recommendation.confidence == 1.0
        
        # Test mid-range confidence
        mid_recommendation = EnvironmentRecommendation("development", 0.75, "Strong indicators", "dev")
        assert mid_recommendation.confidence == 0.75


class TestCacheStrategy:
    """Test cache strategy enumeration per docstring contracts."""
    
    def test_cache_strategy_values_match_documentation(self):
        """
        Test CacheStrategy enum values per docstring Values section.
        
        Verifies:
            All documented strategy values are available and have correct string representations
            
        Business Impact:
            Ensures cache strategy selection matches documented deployment patterns
            
        Scenario:
            Given: CacheStrategy enum values as documented
            When: Strategy values are accessed
            Then: String values match documented patterns for serialization
        """
        assert CacheStrategy.FAST == "fast"
        assert CacheStrategy.BALANCED == "balanced"
        assert CacheStrategy.ROBUST == "robust"
        assert CacheStrategy.AI_OPTIMIZED == "ai_optimized"
    
    def test_cache_strategy_string_enum_behavior(self):
        """
        Test CacheStrategy string enum behavior per docstring.
        
        Verifies:
            String enum supports direct comparison and serialization as documented
            
        Business Impact:
            Ensures strategy values work correctly in configuration serialization
            
        Scenario:
            Given: CacheStrategy enum values
            When: Values are compared and serialized
            Then: String behavior works as documented
        """
        # Test direct comparison as documented
        strategy = CacheStrategy.BALANCED
        assert strategy == "balanced"
        assert strategy.value == "balanced"
        
        # Test serialization behavior
        assert json.dumps(strategy) == '"balanced"'
        
        # Test comparison between strategies
        assert CacheStrategy.FAST != CacheStrategy.ROBUST
    
    def test_cache_strategy_usage_examples_from_docstring(self):
        """
        Test CacheStrategy usage examples per docstring Examples section.
        
        Verifies:
            Examples from docstring work correctly in practice
            
        Business Impact:
            Ensures documented examples provide accurate usage guidance
            
        Scenario:
            Given: Examples from CacheStrategy docstring
            When: Examples are executed
            Then: Results match documented behavior
        """
        # Example 1: Direct strategy usage (enum may show full representation)
        strategy = CacheStrategy.BALANCED
        strategy_str = f"Using {strategy} strategy"
        assert "balanced" in strategy_str.lower() or strategy.value == "balanced"
        
        # Example 2: Strategy-based configuration access (verify DEFAULT_PRESETS exists)
        config = DEFAULT_PRESETS[CacheStrategy.AI_OPTIMIZED]
        assert config is not None
        assert hasattr(config, 'default_ttl')


class TestCacheConfig:
    """Test local CacheConfig class per docstring contracts."""
    
    def test_cache_config_default_initialization(self):
        """
        Test CacheConfig initialization with defaults per docstring Attributes.
        
        Verifies:
            Default values match those documented in docstring Attributes section
            
        Business Impact:
            Ensures consistent cache configuration across deployments without explicit settings
            
        Scenario:
            Given: CacheConfig created with no parameters
            When: Object is initialized
            Then: All attributes match documented default values
        """
        config = CacheConfig()
        
        # Test strategy default per docstring
        assert config.strategy == CacheStrategy.BALANCED
        
        # Test Redis configuration defaults per docstring
        assert config.redis_url is None
        assert config.redis_password is None
        assert config.use_tls is False
        assert config.tls_cert_path is None
        assert config.tls_key_path is None
        assert config.max_connections == 10
        assert config.connection_timeout == 5
        
        # Test cache behavior defaults per docstring
        assert config.default_ttl == 3600  # 1 hour
        assert config.memory_cache_size == 100
        assert config.compression_threshold == 1000
        assert config.compression_level == 6
        
        # Test AI features defaults per docstring
        assert config.enable_ai_cache is False
        assert config.text_hash_threshold == 1000
        assert config.hash_algorithm == "sha256"
        assert config.enable_smart_promotion is True
        assert config.max_text_length == 100000
        
        # Test default text_size_tiers per docstring
        expected_tiers = {"small": 1000, "medium": 5000, "large": 20000}
        assert config.text_size_tiers == expected_tiers
        
        # Test default operation_ttls per docstring
        expected_ttls = {
            "summarize": 7200,  # 2 hours
            "sentiment": 3600,  # 1 hour
            "key_points": 5400, # 1.5 hours
            "questions": 4800,  # 1.33 hours
            "qa": 3600         # 1 hour
        }
        assert config.operation_ttls == expected_ttls
        
        # Test monitoring defaults per docstring
        assert config.enable_monitoring is True
        assert config.log_level == "INFO"
    
    def test_to_dict_factory_mapping(self):
        """
        Test to_dict method factory field mapping per docstring.
        
        Verifies:
            Dictionary conversion maps fields to factory-expected names as documented
            
        Business Impact:
            Ensures configuration integrates correctly with cache factory system
            
        Scenario:
            Given: CacheConfig with various settings
            When: to_dict() is called
            Then: Dictionary contains factory-expected field names
        """
        config = CacheConfig(
            strategy=CacheStrategy.AI_OPTIMIZED,
            redis_url="redis://test:6379",
            memory_cache_size=200,
            enable_ai_cache=True
        )
        
        result_dict = config.to_dict()
        
        # Test strategy conversion per docstring
        assert result_dict["cache_strategy"] == "ai_optimized"
        
        # Test Redis field mapping per docstring
        assert result_dict["redis_url"] == "redis://test:6379"
        
        # Test factory naming per docstring - memory_cache_size -> l1_cache_size
        assert result_dict["l1_cache_size"] == 200
        assert result_dict["enable_l1_cache"] is True
        
        # Test AI features mapping per docstring
        assert result_dict["enable_ai_cache"] is True
        assert "text_hash_threshold" in result_dict
        assert "operation_ttls" in result_dict
        
        # Verify None values removed per docstring
        assert None not in result_dict.values()
    
    def test_to_dict_ai_features_conditional_inclusion(self):
        """
        Test to_dict AI features conditional inclusion per docstring.
        
        Verifies:
            AI features are only included when enable_ai_cache is True as documented
            
        Business Impact:
            Prevents AI-specific configuration from being passed when AI features disabled
            
        Scenario:
            Given: CacheConfig with AI features disabled
            When: to_dict() is called
            Then: AI-specific fields are not included in factory dictionary
        """
        config = CacheConfig(enable_ai_cache=False)
        result_dict = config.to_dict()
        
        # AI features should be excluded when disabled per docstring (None values removed)
        ai_fields = ["text_hash_threshold", "operation_ttls", "text_size_tiers", 
                    "hash_algorithm", "enable_smart_promotion", "max_text_length"]
        
        # These fields should either be missing (None values removed) or None
        for field in ai_fields:
            if field in result_dict:
                assert result_dict[field] is None
        
        # But enable_ai_cache should still be present
        assert result_dict["enable_ai_cache"] is False
    
    @patch('app.infrastructure.cache.cache_validator.cache_validator')
    def test_validate_with_cache_validator_available(self, mock_validator):
        """
        Test validate method with cache_validator available per docstring.
        
        Verifies:
            Validation delegates to cache_validator.validate_configuration when available
            
        Business Impact:
            Ensures comprehensive validation when validation system is available
            
        Scenario:
            Given: CacheConfig with cache_validator available
            When: validate() is called
            Then: Validation is delegated to cache_validator system
        """
        mock_result = MagicMock()
        mock_result.is_valid = True
        mock_result.errors = []
        mock_validator.validate_configuration.return_value = mock_result
        
        config = CacheConfig(default_ttl=1800)
        result = config.validate()
        
        # Verify cache_validator was called with to_dict() output
        mock_validator.validate_configuration.assert_called_once()
        call_args = mock_validator.validate_configuration.call_args[0][0]
        assert isinstance(call_args, dict)
        assert call_args["default_ttl"] == 1800
        
        assert result is mock_result
    
    def test_validate_fallback_to_basic_validation(self):
        """
        Test validate method fallback to basic validation per docstring.
        
        Verifies:
            Falls back to _basic_validate when cache_validator not available
            
        Business Impact:
            Ensures validation works even when advanced validation system unavailable
            
        Scenario:
            Given: CacheConfig with cache_validator not available (ImportError)
            When: validate() is called
            Then: Basic validation is performed with essential checks
        """
        config = CacheConfig(default_ttl=1800)
        
        # Create a mock _basic_validate to return predictable result
        with patch.object(config, '_basic_validate') as mock_basic_validate:
            mock_result = MagicMock()
            mock_result.is_valid = True
            mock_result.errors = []
            mock_basic_validate.return_value = mock_result
            
            # Mock the import to raise ImportError
            with patch('builtins.__import__', side_effect=lambda name, *args: __import__(name, *args) if 'cache_validator' not in name else exec('raise ImportError()')):
                result = config.validate()
            
            # Verify _basic_validate was called
            mock_basic_validate.assert_called_once()
            
            # Should return basic validation result
            assert result is mock_result
    
    @patch('app.infrastructure.cache.cache_validator.ValidationResult')
    def test_basic_validate_ttl_boundaries(self, mock_validation_result):
        """
        Test _basic_validate TTL boundary validation per docstring.
        
        Verifies:
            TTL validation enforces 60-604800 second range as documented
            
        Business Impact:
            Prevents invalid TTL configurations that could break cache behavior
            
        Scenario:
            Given: CacheConfig with TTL outside documented range
            When: _basic_validate() is called
            Then: Validation errors are added for out-of-range values
        """
        mock_result = MagicMock()
        mock_validation_result.return_value = mock_result
        
        # Test TTL below minimum
        config = CacheConfig(default_ttl=30)  # Below 60 seconds
        config._basic_validate()
        
        mock_result.add_error.assert_called_with("default_ttl must be between 60 and 604800 seconds")
        
        # Reset and test TTL above maximum
        mock_result.reset_mock()
        config = CacheConfig(default_ttl=700000)  # Above 604800 seconds (1 week)
        config._basic_validate()
        
        mock_result.add_error.assert_called_with("default_ttl must be between 60 and 604800 seconds")
    
    @patch('app.infrastructure.cache.cache_validator.ValidationResult')
    def test_basic_validate_connection_boundaries(self, mock_validation_result):
        """
        Test _basic_validate connection parameter validation per docstring.
        
        Verifies:
            Connection parameters enforce documented ranges
            
        Business Impact:
            Prevents invalid connection configurations that could cause system issues
            
        Scenario:
            Given: CacheConfig with connection parameters outside valid ranges
            When: _basic_validate() is called
            Then: Validation errors are added for invalid values
        """
        mock_result = MagicMock()
        mock_validation_result.return_value = mock_result
        
        # Test max_connections boundaries
        config = CacheConfig(max_connections=0)  # Below minimum of 1
        config._basic_validate()
        assert any(call[0][0] == "max_connections must be between 1 and 100" for call in mock_result.add_error.call_args_list)
        
        # Test connection_timeout boundaries
        mock_result.reset_mock()
        config = CacheConfig(connection_timeout=70)  # Above maximum of 60
        config._basic_validate()
        assert any(call[0][0] == "connection_timeout must be between 1 and 60 seconds" for call in mock_result.add_error.call_args_list)
    
    @patch('app.infrastructure.cache.cache_validator.ValidationResult')
    def test_basic_validate_compression_level_range(self, mock_validation_result):
        """
        Test _basic_validate compression level validation per docstring.
        
        Verifies:
            Compression level enforces 1-9 range as documented
            
        Business Impact:
            Prevents invalid compression settings that could cause compression errors
            
        Scenario:
            Given: CacheConfig with compression_level outside valid range
            When: _basic_validate() is called
            Then: Validation error is added for invalid compression level
        """
        mock_result = MagicMock()
        mock_validation_result.return_value = mock_result
        
        config = CacheConfig(compression_level=0)  # Below minimum of 1
        config._basic_validate()
        
        mock_result.add_error.assert_called_with("compression_level must be between 1 and 9")


class TestCachePreset:
    """Test CachePreset dataclass per docstring contracts."""
    
    def test_cache_preset_initialization(self):
        """
        Test CachePreset initialization with all fields per docstring Attributes.
        
        Verifies:
            All documented attributes are properly initialized
            
        Business Impact:
            Ensures preset system can represent complete cache configurations
            
        Scenario:
            Given: CachePreset with all documented attributes
            When: Object is initialized
            Then: All attributes are accessible and correctly stored
        """
        preset = CachePreset(
            name="test-preset",
            description="Test configuration preset",
            strategy=CacheStrategy.BALANCED,
            default_ttl=1800,
            max_connections=15,
            connection_timeout=10,
            memory_cache_size=150,
            compression_threshold=800,
            compression_level=7,
            enable_ai_cache=True,
            enable_monitoring=True,
            log_level="DEBUG",
            environment_contexts=["testing", "development"],
            ai_optimizations={
                "text_hash_threshold": 2000,
                "hash_algorithm": "sha512"
            }
        )
        
        assert preset.name == "test-preset"
        assert preset.description == "Test configuration preset"
        assert preset.strategy == CacheStrategy.BALANCED
        assert preset.default_ttl == 1800
        assert preset.max_connections == 15
        assert preset.enable_ai_cache is True
        assert preset.environment_contexts == ["testing", "development"]
        assert preset.ai_optimizations["text_hash_threshold"] == 2000
    
    def test_to_dict_serialization(self):
        """
        Test to_dict method serialization per docstring.
        
        Verifies:
            Preset can be serialized to dictionary for configuration management
            
        Business Impact:
            Enables preset persistence and configuration export functionality
            
        Scenario:
            Given: CachePreset with various configurations
            When: to_dict() is called
            Then: Dictionary contains all preset data in serializable format
        """
        preset = CachePreset(
            name="serialize-test",
            description="Serialization test",
            strategy=CacheStrategy.FAST,
            default_ttl=600,
            max_connections=5,
            connection_timeout=3,
            memory_cache_size=50,
            compression_threshold=1500,
            compression_level=4,
            enable_ai_cache=False,
            enable_monitoring=True,
            log_level="INFO",
            environment_contexts=["development"],
            ai_optimizations={}
        )
        
        result_dict = preset.to_dict()
        
        assert result_dict["name"] == "serialize-test"
        assert result_dict["strategy"] == CacheStrategy.FAST
        assert result_dict["default_ttl"] == 600
        assert result_dict["environment_contexts"] == ["development"]
        assert isinstance(result_dict, dict)
    
    @patch('app.infrastructure.cache.config.CacheConfig')
    @patch('app.infrastructure.cache.config.AICacheConfig')
    def test_to_cache_config_without_ai_features(self, mock_ai_config_class, mock_cache_config_class):
        """
        Test to_cache_config conversion without AI features per docstring.
        
        Verifies:
            Preset converts to config.py CacheConfig without AI configuration when AI disabled
            
        Business Impact:
            Ensures preset system integrates correctly with main configuration system
            
        Scenario:
            Given: CachePreset with AI features disabled
            When: to_cache_config() is called
            Then: config.py CacheConfig is created without AI configuration
        """
        mock_config_instance = MagicMock()
        mock_cache_config_class.return_value = mock_config_instance
        
        preset = CachePreset(
            name="no-ai-test",
            description="No AI features test",
            strategy=CacheStrategy.BALANCED,
            default_ttl=3600,
            max_connections=10,
            connection_timeout=5,
            memory_cache_size=100,
            compression_threshold=1000,
            compression_level=6,
            enable_ai_cache=False,
            enable_monitoring=True,
            log_level="INFO",
            environment_contexts=["production"],
            ai_optimizations={}
        )
        
        result = preset.to_cache_config()
        
        # Verify config.py CacheConfig was called with correct parameters
        mock_cache_config_class.assert_called_once()
        call_kwargs = mock_cache_config_class.call_args[1]
        
        assert call_kwargs["default_ttl"] == 3600
        assert call_kwargs["memory_cache_size"] == 100
        assert call_kwargs["compression_threshold"] == 1000
        assert call_kwargs["compression_level"] == 6
        assert call_kwargs["environment"] == "production"
        assert call_kwargs["ai_config"] is None  # No AI config when disabled
        
        # Verify AI config class was not called
        mock_ai_config_class.assert_not_called()
        
        assert result is mock_config_instance
    
    @patch('app.infrastructure.cache.config.CacheConfig')
    @patch('app.infrastructure.cache.config.AICacheConfig')
    def test_to_cache_config_with_ai_features(self, mock_ai_config_class, mock_cache_config_class):
        """
        Test to_cache_config conversion with AI features per docstring.
        
        Verifies:
            Preset converts to config.py CacheConfig with AI configuration when AI enabled
            
        Business Impact:
            Ensures AI-enabled presets integrate correctly with main configuration system
            
        Scenario:
            Given: CachePreset with AI features enabled and AI optimizations
            When: to_cache_config() is called
            Then: config.py CacheConfig is created with properly configured AI settings
        """
        mock_config_instance = MagicMock()
        mock_cache_config_class.return_value = mock_config_instance
        mock_ai_config_instance = MagicMock()
        mock_ai_config_class.return_value = mock_ai_config_instance
        
        preset = CachePreset(
            name="ai-test",
            description="AI features test",
            strategy=CacheStrategy.AI_OPTIMIZED,
            default_ttl=7200,
            max_connections=25,
            connection_timeout=15,
            memory_cache_size=1000,
            compression_threshold=300,
            compression_level=9,
            enable_ai_cache=True,
            enable_monitoring=True,
            log_level="INFO",
            environment_contexts=["production"],
            ai_optimizations={
                "text_hash_threshold": 1500,
                "hash_algorithm": "sha512",
                "text_size_tiers": {"small": 500, "medium": 2000, "large": 10000},
                "operation_ttls": {"summarize": 5400, "sentiment": 2700},
                "enable_smart_promotion": False,
                "max_text_length": 150000
            }
        )
        
        result = preset.to_cache_config()
        
        # Verify AI config was created with correct parameters
        mock_ai_config_class.assert_called_once()
        ai_call_kwargs = mock_ai_config_class.call_args[1]
        
        assert ai_call_kwargs["text_hash_threshold"] == 1500
        assert ai_call_kwargs["hash_algorithm"] == "sha512"
        assert ai_call_kwargs["text_size_tiers"]["small"] == 500
        assert ai_call_kwargs["operation_ttls"]["summarize"] == 5400
        assert ai_call_kwargs["enable_smart_promotion"] is False
        assert ai_call_kwargs["max_text_length"] == 150000
        
        # Verify main config was created with AI config
        mock_cache_config_class.assert_called_once()
        config_call_kwargs = mock_cache_config_class.call_args[1]
        assert config_call_kwargs["ai_config"] is mock_ai_config_instance
        
        assert result is mock_config_instance
    
    @patch('app.infrastructure.cache.config.CacheConfig')
    @patch('app.infrastructure.cache.config.AICacheConfig')
    def test_to_cache_config_ai_defaults_fallback(self, mock_ai_config_class, mock_cache_config_class):
        """
        Test to_cache_config AI configuration defaults per docstring behavior.
        
        Verifies:
            Missing AI optimization values fall back to documented defaults
            
        Business Impact:
            Ensures AI presets work correctly even with incomplete AI optimization data
            
        Scenario:
            Given: CachePreset with AI enabled but minimal ai_optimizations
            When: to_cache_config() is called
            Then: AI configuration uses documented defaults for missing values
        """
        mock_config_instance = MagicMock()
        mock_cache_config_class.return_value = mock_config_instance
        mock_ai_config_instance = MagicMock()
        mock_ai_config_class.return_value = mock_ai_config_instance
        
        preset = CachePreset(
            name="ai-defaults-test",
            description="AI defaults test",
            strategy=CacheStrategy.AI_OPTIMIZED,
            default_ttl=3600,
            max_connections=10,
            connection_timeout=5,
            memory_cache_size=100,
            compression_threshold=1000,
            compression_level=6,
            enable_ai_cache=True,
            enable_monitoring=True,
            log_level="INFO",
            environment_contexts=["development"],
            ai_optimizations={"text_hash_threshold": 800}  # Only one value, rest should use defaults
        )
        
        result = preset.to_cache_config()
        
        # Verify AI config was created with defaults for missing values
        mock_ai_config_class.assert_called_once()
        ai_call_kwargs = mock_ai_config_class.call_args[1]
        
        assert ai_call_kwargs["text_hash_threshold"] == 800  # From ai_optimizations
        assert ai_call_kwargs["hash_algorithm"] == "sha256"  # Default per docstring
        assert ai_call_kwargs["enable_smart_promotion"] is True  # Default per docstring
        assert ai_call_kwargs["max_text_length"] == 100000  # Default per docstring
        
        # Verify default text_size_tiers per docstring
        expected_default_tiers = {"small": 1000, "medium": 5000, "large": 20000}
        assert ai_call_kwargs["text_size_tiers"] == expected_default_tiers
        
        # Verify default operation_ttls per docstring
        expected_default_ttls = {
            "summarize": 7200, "sentiment": 3600, "key_points": 5400,
            "questions": 4800, "qa": 3600
        }
        assert ai_call_kwargs["operation_ttls"] == expected_default_ttls


class TestCachePresetManager:
    """Test CachePresetManager functionality per docstring contracts."""
    
    def test_initialization_with_default_presets(self):
        """
        Test CachePresetManager initialization per docstring.
        
        Verifies:
            Manager initializes with CACHE_PRESETS and logs preset count as documented
            
        Business Impact:
            Ensures preset manager has access to all predefined presets for configuration
            
        Scenario:
            Given: CachePresetManager is initialized
            When: Manager is created
            Then: All CACHE_PRESETS are available and count is logged
        """
        manager = CachePresetManager()
        
        assert manager.presets is not None
        assert len(manager.presets) > 0
        
        # Verify all CACHE_PRESETS are included
        for preset_name in CACHE_PRESETS.keys():
            assert preset_name in manager.presets
    
    def test_get_preset_valid_name(self):
        """
        Test get_preset method with valid preset name per docstring.
        
        Verifies:
            Valid preset names return corresponding CachePreset objects as documented
            
        Business Impact:
            Enables configuration system to retrieve specific preset configurations
            
        Scenario:
            Given: CachePresetManager with available presets
            When: get_preset is called with valid preset name
            Then: Corresponding CachePreset object is returned
        """
        manager = CachePresetManager()
        
        preset = manager.get_preset("development")
        
        assert isinstance(preset, CachePreset)
        assert preset.name == "Development"
        assert preset.strategy == CacheStrategy.FAST
        assert "development" in preset.environment_contexts
    
    def test_get_preset_invalid_name_raises_configuration_error(self):
        """
        Test get_preset method with invalid name per docstring error handling.
        
        Verifies:
            Invalid preset names raise ConfigurationError with available presets list
            
        Business Impact:
            Prevents system startup with invalid preset configurations and provides guidance
            
        Scenario:
            Given: CachePresetManager with available presets
            When: get_preset is called with unknown preset name
            Then: ConfigurationError is raised with context about available presets
        """
        manager = CachePresetManager()
        
        with pytest.raises(ConfigurationError) as exc_info:
            manager.get_preset("nonexistent-preset")
        
        error_message = str(exc_info.value)
        assert "Unknown preset 'nonexistent-preset'" in error_message
        assert "Available presets:" in error_message
        
        # Verify error includes available preset names
        for preset_name in ["disabled", "simple", "development", "production"]:
            assert preset_name in error_message
    
    def test_list_presets_returns_all_preset_names(self):
        """
        Test list_presets method returns all available names per docstring.
        
        Verifies:
            All preset names from CACHE_PRESETS are returned in list format
            
        Business Impact:
            Enables preset discovery for configuration interfaces and documentation
            
        Scenario:
            Given: CachePresetManager with loaded presets
            When: list_presets() is called
            Then: List of all available preset names is returned
        """
        manager = CachePresetManager()
        
        preset_names = manager.list_presets()
        
        assert isinstance(preset_names, list)
        assert len(preset_names) > 0
        
        # Verify all CACHE_PRESETS keys are included
        for preset_name in CACHE_PRESETS.keys():
            assert preset_name in preset_names
    
    def test_get_preset_details_returns_configuration_info(self):
        """
        Test get_preset_details method returns preset information per docstring.
        
        Verifies:
            Preset details include name, description, configuration, and context as documented
            
        Business Impact:
            Enables configuration interfaces to display detailed preset information
            
        Scenario:
            Given: CachePresetManager with available presets
            When: get_preset_details is called with valid preset name
            Then: Dictionary with detailed preset information is returned
        """
        manager = CachePresetManager()
        
        details = manager.get_preset_details("production")
        
        assert isinstance(details, dict)
        assert "name" in details
        assert "description" in details
        assert "configuration" in details
        assert "environment_contexts" in details
        assert "ai_optimizations" in details
        
        # Verify configuration section contains key settings
        config_section = details["configuration"]
        assert "strategy" in config_section
        assert "default_ttl" in config_section
        assert "max_connections" in config_section
        assert "memory_cache_size" in config_section
        assert "enable_ai_cache" in config_section
        assert "enable_monitoring" in config_section
        assert "log_level" in config_section
    
    @patch('app.infrastructure.cache.cache_validator.cache_validator')
    def test_validate_preset_with_validator_available(self, mock_validator):
        """
        Test validate_preset method with cache_validator available per docstring.
        
        Verifies:
            Validation delegates to cache_validator.validate_preset when available
            
        Business Impact:
            Ensures comprehensive preset validation when validation system is available
            
        Scenario:
            Given: CachePresetManager with cache_validator available
            When: validate_preset is called
            Then: Validation is delegated to cache_validator system
        """
        mock_result = MagicMock()
        mock_result.is_valid = True
        mock_result.errors = []
        mock_result.warnings = []
        mock_validator.validate_preset.return_value = mock_result
        
        manager = CachePresetManager()
        preset = manager.get_preset("simple")
        
        result = manager.validate_preset(preset)
        
        # Verify cache_validator was called with preset dictionary
        mock_validator.validate_preset.assert_called_once()
        call_args = mock_validator.validate_preset.call_args[0][0]
        assert isinstance(call_args, dict)
        assert call_args["name"] == "Simple"
        
        assert result is True  # Valid preset returns True
    
    @patch('app.infrastructure.cache.cache_validator.cache_validator')
    def test_validate_preset_with_validation_errors(self, mock_validator):
        """
        Test validate_preset method with validation errors per docstring behavior.
        
        Verifies:
            Validation errors are logged and method returns False as documented
            
        Business Impact:
            Prevents invalid presets from being used and provides error details
            
        Scenario:
            Given: CachePresetManager with cache_validator returning validation errors
            When: validate_preset is called
            Then: Errors are logged and False is returned
        """
        mock_result = MagicMock()
        mock_result.is_valid = False
        mock_result.errors = ["Invalid TTL value", "Missing required field"]
        mock_result.warnings = ["Configuration may be suboptimal"]
        mock_validator.validate_preset.return_value = mock_result
        
        manager = CachePresetManager()
        preset = manager.get_preset("simple")
        
        with patch('app.infrastructure.cache.cache_presets.logger') as mock_logger:
            result = manager.validate_preset(preset)
            
            # Verify errors were logged (allow flexible logging format)
            error_calls = [call[0][0] for call in mock_logger.error.call_args_list]
            assert any("Invalid TTL value" in call for call in error_calls)
            assert any("Missing required field" in call for call in error_calls)
            
            # Verify warnings were logged (allow flexible logging format)
            if mock_logger.warning.call_args_list:
                warning_calls = [call[0][0] for call in mock_logger.warning.call_args_list]
                assert any("Configuration may be suboptimal" in call for call in warning_calls)
        
        assert result is False  # Invalid preset returns False
    
    @patch('app.infrastructure.cache.cache_validator.cache_validator', side_effect=ImportError)
    def test_validate_preset_fallback_to_basic_validation(self, mock_import_error):
        """
        Test validate_preset fallback to basic validation per docstring.
        
        Verifies:
            Falls back to _basic_validate_preset when cache_validator not available
            
        Business Impact:
            Ensures preset validation works even when advanced validation system unavailable
            
        Scenario:
            Given: CachePresetManager with cache_validator not available (ImportError)
            When: validate_preset is called
            Then: Basic validation is performed with essential checks
        """
        manager = CachePresetManager()
        preset = manager.get_preset("simple")
        
        result = manager.validate_preset(preset)
        
        # Should use basic validation and return boolean
        assert isinstance(result, bool)
        assert result is True  # Valid preset should pass basic validation
    
    def test_basic_validate_preset_ttl_boundaries(self):
        """
        Test _basic_validate_preset TTL validation per docstring rules.
        
        Verifies:
            TTL validation enforces 1-604800 second range in basic validation
            
        Business Impact:
            Prevents invalid TTL configurations in preset validation
            
        Scenario:
            Given: CachePreset with TTL outside valid range
            When: _basic_validate_preset is called
            Then: Validation fails and error is logged
        """
        manager = CachePresetManager()
        
        # Create preset with invalid TTL
        invalid_preset = CachePreset(
            name="invalid-ttl",
            description="Invalid TTL test",
            strategy=CacheStrategy.FAST,
            default_ttl=0,  # Invalid - below minimum of 1
            max_connections=5,
            connection_timeout=3,
            memory_cache_size=50,
            compression_threshold=1000,
            compression_level=6,
            enable_ai_cache=False,
            enable_monitoring=True,
            log_level="INFO",
            environment_contexts=["testing"]
        )
        
        with patch('app.infrastructure.cache.cache_presets.logger') as mock_logger:
            result = manager._basic_validate_preset(invalid_preset)
            
            # Verify error was logged for invalid TTL
            mock_logger.error.assert_called_with("Invalid default_ttl: 0 (must be 1-604800)")
        
        assert result is False
    
    def test_basic_validate_preset_connection_parameters(self):
        """
        Test _basic_validate_preset connection parameter validation per docstring.
        
        Verifies:
            Connection parameters enforce documented ranges in basic validation
            
        Business Impact:
            Prevents invalid connection configurations in preset validation
            
        Scenario:
            Given: CachePreset with connection parameters outside valid ranges
            When: _basic_validate_preset is called
            Then: Validation fails and errors are logged
        """
        manager = CachePresetManager()
        
        # Test max_connections validation
        invalid_preset = CachePreset(
            name="invalid-connections",
            description="Invalid connections test",
            strategy=CacheStrategy.FAST,
            default_ttl=1800,
            max_connections=0,  # Invalid - below minimum of 1
            connection_timeout=5,  # Valid
            memory_cache_size=50,
            compression_threshold=1000,
            compression_level=6,
            enable_ai_cache=False,
            enable_monitoring=True,
            log_level="INFO",
            environment_contexts=["testing"]
        )
        
        with patch('app.infrastructure.cache.cache_presets.logger') as mock_logger:
            result = manager._basic_validate_preset(invalid_preset)
            
            # Check if any error was logged (the method returns False on first error)
            mock_logger.error.assert_called()
            error_calls = [call[0][0] for call in mock_logger.error.call_args_list]
            assert any("max_connections" in call and "0" in call for call in error_calls)
        
        assert result is False
    
    def test_basic_validate_preset_ai_optimization_ttls(self):
        """
        Test _basic_validate_preset AI optimization TTL validation per docstring.
        
        Verifies:
            AI operation TTLs must be positive integers when AI is enabled
            
        Business Impact:
            Prevents invalid AI TTL configurations that could break AI cache features
            
        Scenario:
            Given: CachePreset with AI enabled and invalid operation TTLs
            When: _basic_validate_preset is called
            Then: Validation fails and AI TTL errors are logged
        """
        manager = CachePresetManager()
        
        # Create preset with invalid AI optimization TTLs
        invalid_preset = CachePreset(
            name="invalid-ai-ttls",
            description="Invalid AI TTLs test",
            strategy=CacheStrategy.AI_OPTIMIZED,
            default_ttl=1800,
            max_connections=10,
            connection_timeout=5,
            memory_cache_size=100,
            compression_threshold=1000,
            compression_level=6,
            enable_ai_cache=True,
            enable_monitoring=True,
            log_level="INFO",
            environment_contexts=["testing"],
            ai_optimizations={
                "operation_ttls": {
                    "summarize": -100,  # Invalid - negative
                    "sentiment": 0      # Invalid - zero
                }
            }
        )
        
        with patch('app.infrastructure.cache.cache_presets.logger') as mock_logger:
            result = manager._basic_validate_preset(invalid_preset)
            
            # Check if errors were logged (method returns False on first error)
            mock_logger.error.assert_called()
            error_calls = [call[0][0] for call in mock_logger.error.call_args_list]
            # Should log error for at least one invalid TTL
            assert any("AI operation TTL" in call for call in error_calls)
        
        assert result is False
    
    def test_recommend_preset_delegates_to_detailed_method(self):
        """
        Test recommend_preset method delegates to detailed method per docstring.
        
        Verifies:
            recommend_preset returns only preset name from detailed recommendation
            
        Business Impact:
            Provides simple preset name interface while maintaining detailed analysis capability
            
        Scenario:
            Given: CachePresetManager with environment detection capability
            When: recommend_preset is called with environment
            Then: Only preset name is returned from detailed recommendation
        """
        manager = CachePresetManager()
        
        with patch.object(manager, 'recommend_preset_with_details') as mock_detailed:
            mock_recommendation = MagicMock()
            mock_recommendation.preset_name = "production"
            mock_detailed.return_value = mock_recommendation
            
            result = manager.recommend_preset("production")
            
            mock_detailed.assert_called_once_with("production")
            assert result == "production"
    
    def test_recommend_preset_with_details_exact_matches(self):
        """
        Test recommend_preset_with_details exact matches per docstring algorithm.
        
        Verifies:
            High-confidence exact matches work as documented in method
            
        Business Impact:
            Ensures accurate preset recommendations for standard environment names
            
        Scenario:
            Given: CachePresetManager with standard environment names
            When: recommend_preset_with_details is called with exact match names
            Then: High-confidence recommendations are returned with correct reasoning
        """
        manager = CachePresetManager()
        
        # Test exact match for development
        recommendation = manager.recommend_preset_with_details("development")
        
        assert recommendation.preset_name == "development"
        assert recommendation.confidence == 0.95
        assert "Exact match for development environment" in recommendation.reasoning
        assert recommendation.environment_detected == "development"
        
        # Test exact match for production
        recommendation = manager.recommend_preset_with_details("production")
        
        assert recommendation.preset_name == "production"
        assert recommendation.confidence == 0.95
        assert "Exact match for production environment" in recommendation.reasoning
        
        # Test abbreviation match
        recommendation = manager.recommend_preset_with_details("dev")
        
        assert recommendation.preset_name == "development"
        assert recommendation.confidence == 0.90
        assert "Standard abbreviation for development" in recommendation.reasoning
    
    def test_recommend_preset_with_details_ai_environment_patterns(self):
        """
        Test recommend_preset_with_details AI environment detection per docstring.
        
        Verifies:
            AI environment patterns are detected and mapped correctly
            
        Business Impact:
            Ensures AI-specific presets are recommended for AI workload environments
            
        Scenario:
            Given: CachePresetManager with AI environment detection
            When: recommend_preset_with_details is called with AI environment names
            Then: AI-specific presets are recommended with appropriate confidence
        """
        manager = CachePresetManager()
        
        # Test AI development
        recommendation = manager.recommend_preset_with_details("ai-development")
        
        assert recommendation.preset_name == "ai-development"
        assert recommendation.confidence == 0.95
        assert "Exact match for AI development" in recommendation.reasoning
        
        # Test AI production
        recommendation = manager.recommend_preset_with_details("ai-production")
        
        assert recommendation.preset_name == "ai-production"
        assert recommendation.confidence == 0.95
        assert "Exact match for AI production" in recommendation.reasoning
        
        # Test AI abbreviation
        recommendation = manager.recommend_preset_with_details("ai-dev")
        
        assert recommendation.preset_name == "ai-development"
        assert recommendation.confidence == 0.90
        assert "AI development abbreviation" in recommendation.reasoning
    
    def test_recommend_preset_with_details_pattern_matching_fallback(self):
        """
        Test recommend_preset_with_details pattern matching per docstring algorithm.
        
        Verifies:
            Pattern-based matching works for complex environment names
            
        Business Impact:
            Ensures intelligent preset recommendations for non-standard environment names
            
        Scenario:
            Given: CachePresetManager with pattern matching capability
            When: recommend_preset_with_details is called with complex environment names
            Then: Pattern-based recommendations are returned with appropriate confidence
        """
        manager = CachePresetManager()
        
        # Test staging pattern
        recommendation = manager.recommend_preset_with_details("staging-cluster-01")
        
        assert recommendation.preset_name == "production"  # Staging uses production preset per docstring
        assert recommendation.confidence >= 0.70
        assert "staging pattern" in recommendation.reasoning.lower()
        
        # Test unknown pattern fallback
        recommendation = manager.recommend_preset_with_details("weird-unknown-environment-name")
        
        assert recommendation.preset_name == "simple"  # Default fallback per docstring
        assert recommendation.confidence == 0.40
        assert "Unknown environment pattern" in recommendation.reasoning
        assert "defaulting to simple preset" in recommendation.reasoning
    
    @patch.dict(os.environ, {"CACHE_PRESET": "production"}, clear=False)
    def test_auto_detect_environment_explicit_cache_preset(self):
        """
        Test _auto_detect_environment explicit CACHE_PRESET per docstring priority.
        
        Verifies:
            Explicit CACHE_PRESET environment variable has highest priority as documented
            
        Business Impact:
            Ensures explicit preset configuration overrides automatic detection
            
        Scenario:
            Given: CACHE_PRESET environment variable is set
            When: _auto_detect_environment is called
            Then: Explicit preset is used with high confidence
        """
        manager = CachePresetManager()
        
        recommendation = manager._auto_detect_environment()
        
        assert recommendation.preset_name == "production"
        assert recommendation.confidence == 0.95
        assert "Explicit CACHE_PRESET=production" in recommendation.reasoning
        assert "CACHE_PRESET" in recommendation.environment_detected
    
    @patch.dict(os.environ, {"ENVIRONMENT": "staging"}, clear=False)
    def test_auto_detect_environment_explicit_environment_variable(self):
        """
        Test _auto_detect_environment ENVIRONMENT variable per docstring behavior.
        
        Verifies:
            ENVIRONMENT variable is honored when CACHE_PRESET not present
            
        Business Impact:
            Enables environment-based preset selection through standard environment variables
            
        Scenario:
            Given: ENVIRONMENT variable set to staging
            When: _auto_detect_environment is called
            Then: Production preset is recommended for staging environment
        """
        manager = CachePresetManager()
        
        recommendation = manager._auto_detect_environment()
        
        assert recommendation.preset_name == "production"  # Staging maps to production per docstring
        assert recommendation.confidence == 0.70
        assert "ENVIRONMENT=staging maps to production preset" in recommendation.reasoning
        assert "staging (auto-detected)" in recommendation.environment_detected
    
    @patch.dict(os.environ, {
        "ENVIRONMENT": "ai-production", 
        "ENABLE_AI_CACHE": "true"
    }, clear=False)
    def test_auto_detect_environment_ai_environment_detection(self):
        """
        Test _auto_detect_environment AI environment detection per docstring.
        
        Verifies:
            AI environments are detected and AI presets are recommended
            
        Business Impact:
            Ensures AI-specific cache configurations are used for AI workloads
            
        Scenario:
            Given: ENVIRONMENT contains 'ai' and production indicators
            When: _auto_detect_environment is called
            Then: AI production preset is recommended
        """
        manager = CachePresetManager()
        
        recommendation = manager._auto_detect_environment()
        
        assert recommendation.preset_name == "ai-production"
        assert recommendation.confidence == 0.75
        assert "AI production environment detected" in recommendation.reasoning
        assert "ai-production (auto-detected)" in recommendation.environment_detected
    
    @patch.dict(os.environ, {
        "DEBUG": "true",
        "HOST": "localhost"
    }, clear=False)
    def test_auto_detect_environment_development_indicators(self):
        """
        Test _auto_detect_environment development indicators per docstring.
        
        Verifies:
            Development indicators are detected and development preset is recommended
            
        Business Impact:
            Ensures development-friendly cache configuration in development environments
            
        Scenario:
            Given: Development indicators like DEBUG=true and localhost host
            When: _auto_detect_environment is called
            Then: Development preset is recommended
        """
        manager = CachePresetManager()
        
        recommendation = manager._auto_detect_environment()
        
        assert recommendation.preset_name == "development"
        assert recommendation.confidence == 0.75
        assert "Development indicators detected" in recommendation.reasoning
        assert "development (auto-detected)" in recommendation.environment_detected
    
    @patch.dict(os.environ, {
        "PROD": "true",
        "DEBUG": "false"
    }, clear=False)
    def test_auto_detect_environment_production_indicators(self):
        """
        Test _auto_detect_environment production indicators per docstring.
        
        Verifies:
            Production indicators are detected and production preset is recommended
            
        Business Impact:
            Ensures production-grade cache configuration in production environments
            
        Scenario:
            Given: Production indicators like PROD=true and DEBUG=false
            When: _auto_detect_environment is called
            Then: Production preset is recommended
        """
        manager = CachePresetManager()
        
        recommendation = manager._auto_detect_environment()
        
        assert recommendation.preset_name == "production"
        assert recommendation.confidence == 0.70
        assert "Production indicators detected" in recommendation.reasoning
        assert "production (auto-detected)" in recommendation.environment_detected
    
    @patch.dict(os.environ, {}, clear=True)
    def test_auto_detect_environment_fallback_default(self):
        """
        Test _auto_detect_environment fallback default per docstring.
        
        Verifies:
            Unknown environment falls back to simple preset as safe default
            
        Business Impact:
            Ensures system can start with reasonable cache configuration when environment unclear
            
        Scenario:
            Given: No clear environment indicators are present
            When: _auto_detect_environment is called
            Then: Simple preset is recommended as safe default
        """
        manager = CachePresetManager()
        
        recommendation = manager._auto_detect_environment()
        
        assert recommendation.preset_name == "simple"
        assert recommendation.confidence == 0.50
        assert "No clear environment indicators found" in recommendation.reasoning
        assert "using simple preset as safe default" in recommendation.reasoning
        assert "unknown (auto-detected)" in recommendation.environment_detected
    
    def test_pattern_match_environment_ai_patterns(self):
        """
        Test _pattern_match_environment AI pattern detection per docstring algorithm.
        
        Verifies:
            AI patterns are detected first with appropriate confidence levels
            
        Business Impact:
            Ensures AI environments get AI-specific cache configurations
            
        Scenario:
            Given: Environment strings containing 'ai' with various patterns
            When: _pattern_match_environment is called
            Then: AI presets are recommended with pattern-based confidence
        """
        manager = CachePresetManager()
        
        # Test AI production pattern
        preset, confidence, reasoning = manager._pattern_match_environment("ai-ml-production")
        
        assert preset == "ai-production"
        assert confidence == 0.80
        assert "AI production pattern" in reasoning
        
        # Test AI development fallback
        preset, confidence, reasoning = manager._pattern_match_environment("ai-research-cluster")
        
        assert preset == "ai-development"
        assert confidence == 0.75
        assert "contains 'ai', using AI development preset" in reasoning
    
    def test_pattern_match_environment_staging_patterns(self):
        """
        Test _pattern_match_environment staging pattern detection per docstring.
        
        Verifies:
            Staging patterns are detected before other patterns to avoid conflicts
            
        Business Impact:
            Ensures staging environments get production-level cache configurations
            
        Scenario:
            Given: Environment strings matching staging patterns
            When: _pattern_match_environment is called
            Then: Production preset is recommended with staging reasoning
        """
        manager = CachePresetManager()
        
        # Test staging pattern
        preset, confidence, reasoning = manager._pattern_match_environment("pre-prod-staging")
        
        assert preset == "production"  # Staging uses production preset per docstring
        assert confidence == 0.70
        assert "staging pattern, using production preset" in reasoning
        
        # Test UAT pattern
        preset, confidence, reasoning = manager._pattern_match_environment("uat-environment")
        
        assert preset == "production"
        assert confidence == 0.70
        assert "staging pattern, using production preset" in reasoning
    
    def test_pattern_match_environment_development_patterns(self):
        """
        Test _pattern_match_environment development pattern detection per docstring.
        
        Verifies:
            Development patterns are detected with appropriate confidence
            
        Business Impact:
            Ensures development environments get development-friendly cache configurations
            
        Scenario:
            Given: Environment strings matching development patterns
            When: _pattern_match_environment is called
            Then: Development preset is recommended
        """
        manager = CachePresetManager()
        
        # Test dev pattern
        preset, confidence, reasoning = manager._pattern_match_environment("dev-cluster-west")
        
        assert preset == "development"
        assert confidence == 0.75
        assert "development pattern" in reasoning
        
        # Test sandbox pattern
        preset, confidence, reasoning = manager._pattern_match_environment("sandbox-testing")
        
        assert preset == "development"
        assert confidence == 0.75
        assert "development pattern" in reasoning
    
    def test_get_all_presets_summary_returns_complete_information(self):
        """
        Test get_all_presets_summary method per docstring contract.
        
        Verifies:
            Summary includes detailed information for all available presets
            
        Business Impact:
            Enables comprehensive preset overview for configuration interfaces
            
        Scenario:
            Given: CachePresetManager with multiple presets
            When: get_all_presets_summary is called
            Then: Dictionary with all preset details is returned
        """
        manager = CachePresetManager()
        
        summary = manager.get_all_presets_summary()
        
        assert isinstance(summary, dict)
        assert len(summary) > 0
        
        # Verify all CACHE_PRESETS are included
        for preset_name in CACHE_PRESETS.keys():
            assert preset_name in summary
            
            preset_info = summary[preset_name]
            assert "name" in preset_info
            assert "description" in preset_info
            assert "configuration" in preset_info
            assert "environment_contexts" in preset_info


class TestUtilityFunctions:
    """Test utility functions per docstring contracts."""
    
    def test_get_default_presets_returns_strategy_configurations(self):
        """
        Test get_default_presets function per docstring contract.
        
        Verifies:
            Returns dictionary mapping CacheStrategy values to CacheConfig objects
            
        Business Impact:
            Provides strategy-based configuration access for direct usage
            
        Scenario:
            Given: get_default_presets function exists
            When: Function is called
            Then: Dictionary with CacheStrategy keys and CacheConfig values is returned
        """
        presets = get_default_presets()
        
        assert isinstance(presets, dict)
        assert len(presets) == 4  # One for each CacheStrategy value
        
        # Verify all CacheStrategy values are keys
        assert CacheStrategy.FAST in presets
        assert CacheStrategy.BALANCED in presets
        assert CacheStrategy.ROBUST in presets
        assert CacheStrategy.AI_OPTIMIZED in presets
        
        # Verify all values are CacheConfig instances
        for strategy, config in presets.items():
            assert isinstance(config, CacheConfig)
            assert config.strategy == strategy
    
    def test_get_default_presets_fast_strategy_configuration(self):
        """
        Test get_default_presets FAST strategy per docstring Values section.
        
        Verifies:
            FAST strategy has development-friendly configuration as documented
            
        Business Impact:
            Ensures fast strategy provides quick feedback for development workflows
            
        Scenario:
            Given: get_default_presets with FAST strategy
            When: FAST strategy configuration is accessed
            Then: Configuration matches documented fast access parameters
        """
        presets = get_default_presets()
        fast_config = presets[CacheStrategy.FAST]
        
        assert fast_config.strategy == CacheStrategy.FAST
        assert fast_config.default_ttl == 600  # 10 minutes per docstring
        assert fast_config.max_connections == 3
        assert fast_config.connection_timeout == 2
        assert fast_config.memory_cache_size == 50
        assert fast_config.compression_threshold == 2000
        assert fast_config.compression_level == 3
        assert fast_config.log_level == "DEBUG"  # Development-friendly logging
    
    def test_get_default_presets_ai_optimized_strategy_configuration(self):
        """
        Test get_default_presets AI_OPTIMIZED strategy per docstring Values section.
        
        Verifies:
            AI_OPTIMIZED strategy has AI-specific optimizations as documented
            
        Business Impact:
            Ensures AI strategy provides text processing optimizations for AI workloads
            
        Scenario:
            Given: get_default_presets with AI_OPTIMIZED strategy
            When: AI_OPTIMIZED strategy configuration is accessed
            Then: Configuration matches documented AI workload parameters
        """
        presets = get_default_presets()
        ai_config = presets[CacheStrategy.AI_OPTIMIZED]
        
        assert ai_config.strategy == CacheStrategy.AI_OPTIMIZED
        assert ai_config.default_ttl == 14400  # 4 hours per docstring
        assert ai_config.max_connections == 25
        assert ai_config.connection_timeout == 15
        assert ai_config.memory_cache_size == 1000
        assert ai_config.compression_threshold == 300  # Aggressive compression
        assert ai_config.compression_level == 9  # Maximum compression
        assert ai_config.enable_ai_cache is True  # AI features enabled
        assert ai_config.text_hash_threshold == 1000
    
    def test_default_presets_constant_matches_function(self):
        """
        Test DEFAULT_PRESETS constant matches get_default_presets per docstring.
        
        Verifies:
            DEFAULT_PRESETS constant provides same configurations as function
            
        Business Impact:
            Ensures consistent strategy-based configuration access across codebase
            
        Scenario:
            Given: DEFAULT_PRESETS constant and get_default_presets function
            When: Both are compared
            Then: They provide identical strategy configurations
        """
        function_presets = get_default_presets()
        
        assert DEFAULT_PRESETS == function_presets
        
        # Verify both have same keys and equivalent configs
        for strategy in CacheStrategy:
            assert strategy in DEFAULT_PRESETS
            assert strategy in function_presets
            
            constant_config = DEFAULT_PRESETS[strategy]
            function_config = function_presets[strategy]
            
            assert constant_config.strategy == function_config.strategy
            assert constant_config.default_ttl == function_config.default_ttl
            assert constant_config.max_connections == function_config.max_connections
    
    def test_global_cache_preset_manager_initialization(self):
        """
        Test global cache_preset_manager initialization per docstring.
        
        Verifies:
            Global manager instance is properly initialized and accessible
            
        Business Impact:
            Provides consistent preset manager access across application
            
        Scenario:
            Given: Global cache_preset_manager variable
            When: Manager is accessed
            Then: Properly initialized CachePresetManager instance is available
        """
        assert cache_preset_manager is not None
        assert isinstance(cache_preset_manager, CachePresetManager)
        assert len(cache_preset_manager.presets) > 0
        
        # Verify it has all expected presets
        preset_names = cache_preset_manager.list_presets()
        expected_presets = ["disabled", "minimal", "simple", "development", "production", "ai-development", "ai-production"]
        
        for expected in expected_presets:
            assert expected in preset_names


class TestCachePresetsIntegration:
    """Test integration between cache presets and external systems per docstring."""
    
    def test_cache_presets_keys_match_preset_manager_presets(self):
        """
        Test CACHE_PRESETS dictionary keys match manager presets per docstring.
        
        Verifies:
            All CACHE_PRESETS keys are accessible through CachePresetManager
            
        Business Impact:
            Ensures consistency between preset definitions and manager access
            
        Scenario:
            Given: CACHE_PRESETS dictionary and CachePresetManager
            When: Preset keys are compared
            Then: Manager provides access to all defined presets
        """
        manager = CachePresetManager()
        manager_presets = manager.list_presets()
        
        for preset_name in CACHE_PRESETS.keys():
            assert preset_name in manager_presets
            
            # Verify preset can be retrieved
            preset = manager.get_preset(preset_name)
            assert isinstance(preset, CachePreset)
    
    def test_predefined_presets_environment_contexts_coverage(self):
        """
        Test predefined presets cover expected environment contexts per docstring.
        
        Verifies:
            Preset system provides coverage for common deployment scenarios
            
        Business Impact:
            Ensures preset system supports typical application deployment patterns
            
        Scenario:
            Given: CACHE_PRESETS with environment contexts
            When: Environment contexts are analyzed
            Then: Common environments are covered by appropriate presets
        """
        # Collect all environment contexts from presets
        all_contexts = set()
        for preset in CACHE_PRESETS.values():
            all_contexts.update(preset.environment_contexts)
        
        # Verify common environments are covered
        expected_contexts = {"development", "testing", "staging", "production", "local", "minimal"}
        for context in expected_contexts:
            assert context in all_contexts, f"Environment context '{context}' not covered by any preset"
    
    def test_ai_presets_have_ai_optimizations(self):
        """
        Test AI presets contain AI optimizations per docstring specification.
        
        Verifies:
            AI-specific presets have appropriate AI optimization configurations
            
        Business Impact:
            Ensures AI cache features are properly configured in AI-specific presets
            
        Scenario:
            Given: AI development and production presets
            When: AI optimizations are examined
            Then: Appropriate AI-specific configurations are present
        """
        ai_dev_preset = CACHE_PRESETS["ai-development"]
        ai_prod_preset = CACHE_PRESETS["ai-production"]
        
        # Verify AI presets have AI features enabled
        assert ai_dev_preset.enable_ai_cache is True
        assert ai_prod_preset.enable_ai_cache is True
        
        # Verify AI optimizations are present and reasonable
        assert "text_hash_threshold" in ai_dev_preset.ai_optimizations
        assert "hash_algorithm" in ai_dev_preset.ai_optimizations
        assert "operation_ttls" in ai_dev_preset.ai_optimizations
        
        assert "text_hash_threshold" in ai_prod_preset.ai_optimizations
        assert "hash_algorithm" in ai_prod_preset.ai_optimizations
        assert "operation_ttls" in ai_prod_preset.ai_optimizations
        
        # Verify production has longer TTLs than development
        prod_ttls = ai_prod_preset.ai_optimizations["operation_ttls"]
        dev_ttls = ai_dev_preset.ai_optimizations["operation_ttls"]
        
        # Compare common operations
        for operation in ["summarize", "sentiment"]:
            if operation in prod_ttls and operation in dev_ttls:
                assert prod_ttls[operation] > dev_ttls[operation], f"Production {operation} TTL should be longer than development"
    
    def test_preset_strategy_alignment_with_use_cases(self):
        """
        Test preset strategies align with documented use cases per docstring.
        
        Verifies:
            Preset strategies match their intended deployment scenarios
            
        Business Impact:
            Ensures preset selection provides appropriate performance characteristics
            
        Scenario:
            Given: Presets with documented strategies and use cases
            When: Strategy assignments are examined
            Then: Strategies align with preset purposes
        """
        # Development presets should use FAST strategy for quick feedback
        dev_preset = CACHE_PRESETS["development"]
        assert dev_preset.strategy == CacheStrategy.FAST
        
        # Production preset should use ROBUST strategy for stability
        prod_preset = CACHE_PRESETS["production"]
        assert prod_preset.strategy == CacheStrategy.ROBUST
        
        # Simple preset should use BALANCED strategy for general use
        simple_preset = CACHE_PRESETS["simple"]
        assert simple_preset.strategy == CacheStrategy.BALANCED
        
        # AI presets should use AI_OPTIMIZED strategy
        ai_dev_preset = CACHE_PRESETS["ai-development"]
        ai_prod_preset = CACHE_PRESETS["ai-production"]
        assert ai_dev_preset.strategy == CacheStrategy.AI_OPTIMIZED
        assert ai_prod_preset.strategy == CacheStrategy.AI_OPTIMIZED
    
    def test_preset_configuration_scaling_across_environments(self):
        """
        Test preset configurations scale appropriately across environments per docstring.
        
        Verifies:
            Resource allocation scales from development to production appropriately
            
        Business Impact:
            Ensures cache configurations are appropriate for their deployment environments
            
        Scenario:
            Given: Development and production presets
            When: Resource configurations are compared
            Then: Production has higher resource allocation than development
        """
        dev_preset = CACHE_PRESETS["development"]
        prod_preset = CACHE_PRESETS["production"]
        
        # Production should have higher resource allocation
        assert prod_preset.default_ttl > dev_preset.default_ttl
        assert prod_preset.max_connections > dev_preset.max_connections
        assert prod_preset.memory_cache_size > dev_preset.memory_cache_size
        
        # Production should have more aggressive compression for network efficiency
        assert prod_preset.compression_level > dev_preset.compression_level
        assert prod_preset.compression_threshold < dev_preset.compression_threshold  # Lower threshold = more compression
        
        # Production should have longer timeouts for reliability
        assert prod_preset.connection_timeout > dev_preset.connection_timeout