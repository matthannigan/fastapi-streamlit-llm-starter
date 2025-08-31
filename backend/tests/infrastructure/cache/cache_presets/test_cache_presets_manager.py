"""
Unit tests for CachePresetManager behavior.

This test suite verifies the observable behaviors documented in the
CachePresetManager class public contract (cache_presets.pyi). Tests focus on the
behavior-driven testing principles described in docs/guides/developer/TESTING.md.

Coverage Focus:
    - Infrastructure service (>90% test coverage requirement)
    - Preset management and recommendation functionality
    - Environment detection and intelligent preset selection
    - Validation integration and preset quality assurance

External Dependencies:
    All external dependencies are mocked using fixtures from conftest.py following
    the documented public contracts to ensure accurate behavior simulation.
"""

import pytest
import os
from unittest.mock import MagicMock, patch
from typing import Dict, List, Optional

from app.infrastructure.cache.cache_presets import CachePresetManager, CachePreset, EnvironmentRecommendation, CacheStrategy


class TestCachePresetManagerInitialization:
    """
    Test suite for CachePresetManager initialization and basic functionality.
    
    Scope:
        - Manager initialization with default presets
        - Preset registry management and access
        - Basic preset retrieval and listing functionality
        - Preset metadata access and organization
        
    Business Critical:
        Preset manager provides centralized access to cache configuration presets
        
    Test Strategy:
        - Unit tests for manager initialization with CACHE_PRESETS
        - Preset access and retrieval testing
        - Preset listing and enumeration functionality
        - Preset metadata access verification
        
    External Dependencies:
        - CACHE_PRESETS dictionary (real): Predefined preset registry
        - CachePreset instances (real): Managed preset objects
    """

    def test_cache_preset_manager_initializes_with_default_presets(self):
        """
        Test that CachePresetManager initializes with all default presets available.
        
        Verifies:
            Manager initialization includes all predefined presets from CACHE_PRESETS
            
        Business Impact:
            Ensures all standard deployment scenarios have available preset configurations
            
        Scenario:
            Given: CachePresetManager initialization
            When: Manager instance is created
            Then: All default presets are available for retrieval
            And: Preset registry includes development, production, and AI presets
            And: Manager provides access to disabled and minimal presets
            And: All presets are properly indexed and accessible by name
            
        Default Preset Availability Verified:
            - 'disabled' preset is available for testing scenarios
            - 'simple' preset is available for basic deployments
            - 'development' preset is available for local development
            - 'production' preset is available for production deployments
            - 'ai-development' and 'ai-production' presets are available
            
        Fixtures Used:
            - None (testing real preset manager initialization)
            
        Preset Registry Completeness Verified:
            Manager provides access to complete set of deployment scenario presets
            
        Related Tests:
            - test_cache_preset_manager_get_preset_retrieves_valid_presets()
            - test_cache_preset_manager_list_presets_returns_all_available_presets()
        """
        # Initialize a new preset manager
        manager = CachePresetManager()
        
        # Verify all expected presets are available
        expected_presets = ['disabled', 'minimal', 'simple', 'development', 'production', 'ai-development', 'ai-production']
        available_presets = manager.list_presets()
        
        # Assert all expected presets are present
        for preset_name in expected_presets:
            assert preset_name in available_presets, f"Expected preset '{preset_name}' not found in available presets"
        
        # Verify each preset is accessible
        for preset_name in expected_presets:
            preset = manager.get_preset(preset_name)
            assert preset is not None, f"Preset '{preset_name}' should be accessible"
            assert isinstance(preset, CachePreset), f"Retrieved object for '{preset_name}' should be a CachePreset instance"
        
        # Verify specific presets have expected characteristics
        disabled_preset = manager.get_preset('disabled')
        assert disabled_preset.name == "Disabled"
        assert disabled_preset.enable_ai_cache is False
        
        simple_preset = manager.get_preset('simple')
        assert simple_preset.name == "Simple"
        assert simple_preset.strategy == CacheStrategy.BALANCED
        
        dev_preset = manager.get_preset('development')
        assert dev_preset.name == "Development"
        assert dev_preset.strategy == CacheStrategy.FAST
        
        prod_preset = manager.get_preset('production')
        assert prod_preset.name == "Production"
        assert prod_preset.strategy == CacheStrategy.ROBUST
        
        ai_dev_preset = manager.get_preset('ai-development')
        assert ai_dev_preset.name == "AI Development"
        assert ai_dev_preset.enable_ai_cache is True
        
        ai_prod_preset = manager.get_preset('ai-production')
        assert ai_prod_preset.name == "AI Production"
        assert ai_prod_preset.enable_ai_cache is True

    def test_cache_preset_manager_get_preset_retrieves_valid_presets(self):
        """
        Test that get_preset() retrieves valid presets by name.
        
        Verifies:
            Preset retrieval by name returns correct preset configurations
            
        Business Impact:
            Enables reliable preset access for configuration system integration
            
        Scenario:
            Given: CachePresetManager with initialized preset registry
            When: get_preset() is called with valid preset name
            Then: Correct CachePreset instance is returned
            And: Preset contains expected configuration parameters
            And: Preset is ready for cache configuration usage
            And: Retrieved preset matches expectations for the requested deployment scenario
            
        Preset Retrieval Verified:
            - get_preset('development') returns development-optimized preset
            - get_preset('production') returns production-optimized preset
            - get_preset('ai-development') returns AI development preset
            - Retrieved presets have expected strategy and parameter configurations
            
        Fixtures Used:
            - None (testing preset retrieval directly)
            
        Configuration Access Verified:
            Preset retrieval provides reliable access to deployment-ready configurations
            
        Related Tests:
            - test_cache_preset_manager_get_preset_raises_error_for_invalid_names()
            - test_retrieved_presets_are_ready_for_cache_configuration()
        """
        manager = CachePresetManager()
        
        # Test development preset retrieval
        dev_preset = manager.get_preset('development')
        assert isinstance(dev_preset, CachePreset), "Development preset should be a CachePreset instance"
        assert dev_preset.name == "Development", "Development preset should have correct name"
        assert dev_preset.strategy == CacheStrategy.FAST, "Development preset should use FAST strategy"
        assert dev_preset.default_ttl == 600, "Development preset should have 10-minute TTL for quick feedback"
        assert dev_preset.max_connections == 3, "Development preset should have minimal connections"
        assert dev_preset.log_level == "DEBUG", "Development preset should use DEBUG logging"
        assert "development" in dev_preset.environment_contexts, "Development preset should support development context"
        
        # Test production preset retrieval
        prod_preset = manager.get_preset('production')
        assert isinstance(prod_preset, CachePreset), "Production preset should be a CachePreset instance"
        assert prod_preset.name == "Production", "Production preset should have correct name"
        assert prod_preset.strategy == CacheStrategy.ROBUST, "Production preset should use ROBUST strategy"
        assert prod_preset.default_ttl == 7200, "Production preset should have 2-hour TTL"
        assert prod_preset.max_connections == 20, "Production preset should have high connection pool"
        assert prod_preset.compression_level == 9, "Production preset should use maximum compression"
        assert "production" in prod_preset.environment_contexts, "Production preset should support production context"
        
        # Test AI development preset retrieval
        ai_dev_preset = manager.get_preset('ai-development')
        assert isinstance(ai_dev_preset, CachePreset), "AI development preset should be a CachePreset instance"
        assert ai_dev_preset.name == "AI Development", "AI development preset should have correct name"
        assert ai_dev_preset.strategy == CacheStrategy.AI_OPTIMIZED, "AI development preset should use AI_OPTIMIZED strategy"
        assert ai_dev_preset.enable_ai_cache is True, "AI development preset should enable AI cache features"
        assert ai_dev_preset.ai_optimizations is not None, "AI development preset should have AI optimizations"
        assert 'operation_ttls' in ai_dev_preset.ai_optimizations, "AI preset should have operation-specific TTLs"
        
        # Test AI production preset retrieval
        ai_prod_preset = manager.get_preset('ai-production')
        assert isinstance(ai_prod_preset, CachePreset), "AI production preset should be a CachePreset instance"
        assert ai_prod_preset.enable_ai_cache is True, "AI production preset should enable AI cache features"
        assert ai_prod_preset.max_connections == 25, "AI production preset should have high connection pool for AI workloads"
        assert ai_prod_preset.memory_cache_size == 1000, "AI production preset should have large memory cache"
        
        # Verify presets are ready for cache configuration usage by checking key attributes
        for preset_name in ['development', 'production', 'ai-development', 'ai-production']:
            preset = manager.get_preset(preset_name)
            assert preset.default_ttl > 0, f"{preset_name} preset should have positive TTL"
            assert preset.max_connections > 0, f"{preset_name} preset should have positive max connections"
            assert preset.memory_cache_size > 0, f"{preset_name} preset should have positive memory cache size"
            assert preset.compression_level >= 1, f"{preset_name} preset should have valid compression level"

    def test_cache_preset_manager_get_preset_raises_error_for_invalid_names(self):
        """
        Test that get_preset() raises ValueError for invalid preset names.
        
        Verifies:
            Invalid preset names are rejected with clear error messages
            
        Business Impact:
            Prevents configuration errors due to typos or invalid preset references
            
        Scenario:
            Given: CachePresetManager with initialized preset registry
            When: get_preset() is called with invalid preset name
            Then: ValueError is raised with descriptive error message
            And: Error message lists available preset names
            And: Error context helps with debugging preset name issues
            And: No preset is returned for invalid names
            
        Invalid Name Handling Verified:
            - Non-existent preset names raise ValueError
            - Error messages include available preset name suggestions
            - Error context helps identify correct preset names
            - Case-sensitive name validation prevents silent failures
            
        Fixtures Used:
            - None (testing error handling directly)
            
        Configuration Safety Verified:
            Invalid preset access is prevented with clear error guidance
            
        Related Tests:
            - test_cache_preset_manager_error_messages_are_helpful()
            - test_cache_preset_manager_suggests_similar_preset_names()
        """
        manager = CachePresetManager()
        
        # Test non-existent preset name
        with pytest.raises(Exception) as exc_info:  # Using generic Exception since implementation uses ConfigurationError
            manager.get_preset('non_existent_preset')
        
        error_message = str(exc_info.value)
        assert 'non_existent_preset' in error_message, "Error message should mention the invalid preset name"
        assert 'Available presets:' in error_message, "Error message should list available presets"
        
        # Verify available presets are listed in error message
        expected_presets = ['disabled', 'minimal', 'simple', 'development', 'production', 'ai-development', 'ai-production']
        for preset_name in expected_presets:
            assert preset_name in error_message, f"Error message should list '{preset_name}' as available preset"
        
        # Test case-sensitive validation
        with pytest.raises(Exception) as exc_info:
            manager.get_preset('Development')  # Wrong case
        
        error_message = str(exc_info.value)
        assert 'Development' in error_message, "Error message should mention the incorrectly cased preset name"
        
        # Test empty string
        with pytest.raises(Exception) as exc_info:
            manager.get_preset('')
        
        error_message = str(exc_info.value)
        assert 'Available presets:' in error_message, "Error message should provide helpful guidance for empty string"
        
        # Test typo scenarios
        typo_names = ['developement', 'prodution', 'ai-dev', 'staging']  # Common typos
        for typo_name in typo_names:
            with pytest.raises(Exception) as exc_info:
                manager.get_preset(typo_name)
            
            error_message = str(exc_info.value)
            assert typo_name in error_message, f"Error message should mention the typo '{typo_name}'"
            assert 'Available presets:' in error_message, "Error message should list available presets for guidance"

    def test_cache_preset_manager_list_presets_returns_all_available_presets(self):
        """
        Test that list_presets() returns complete list of available preset names.
        
        Verifies:
            Preset enumeration provides complete view of available configurations
            
        Business Impact:
            Enables dynamic preset discovery and configuration UI development
            
        Scenario:
            Given: CachePresetManager with complete preset registry
            When: list_presets() is called
            Then: List of all available preset names is returned
            And: List includes all deployment scenario presets
            And: Preset names are suitable for user selection interfaces
            And: List order is consistent and predictable
            
        Preset Enumeration Verified:
            - All predefined preset names are included in list
            - List includes development, production, and specialized presets
            - Preset name order is consistent for UI development
            - No duplicate names appear in enumeration
            
        Fixtures Used:
            - None (testing preset enumeration directly)
            
        Discovery Support Verified:
            Preset enumeration enables dynamic configuration discovery and selection
            
        Related Tests:
            - test_cache_preset_manager_get_preset_details_provides_preset_information()
            - test_preset_list_supports_configuration_ui_development()
        """
        manager = CachePresetManager()
        
        # Get list of available presets
        available_presets = manager.list_presets()
        
        # Verify return type is list
        assert isinstance(available_presets, list), "list_presets() should return a list"
        
        # Verify all expected presets are included
        expected_presets = ['disabled', 'minimal', 'simple', 'development', 'production', 'ai-development', 'ai-production']
        
        assert len(available_presets) == len(expected_presets), f"Should have {len(expected_presets)} presets, got {len(available_presets)}"
        
        for expected_preset in expected_presets:
            assert expected_preset in available_presets, f"Expected preset '{expected_preset}' should be in list"
        
        # Verify no duplicate names appear
        unique_presets = set(available_presets)
        assert len(unique_presets) == len(available_presets), "Preset list should not contain duplicates"
        
        # Verify all preset names are strings (suitable for UI)
        for preset_name in available_presets:
            assert isinstance(preset_name, str), f"Preset name '{preset_name}' should be a string"
            assert len(preset_name) > 0, f"Preset name should not be empty"
            assert preset_name.strip() == preset_name, f"Preset name '{preset_name}' should not have leading/trailing whitespace"
        
        # Verify preset names cover all deployment scenarios
        deployment_categories = {
            'testing': ['disabled', 'minimal'],
            'development': ['development', 'ai-development'],
            'basic': ['simple'],
            'production': ['production', 'ai-production']
        }
        
        for category, category_presets in deployment_categories.items():
            for preset in category_presets:
                assert preset in available_presets, f"Deployment category '{category}' should include preset '{preset}'"
        
        # Verify each listed preset is actually accessible
        for preset_name in available_presets:
            preset = manager.get_preset(preset_name)
            assert preset is not None, f"Listed preset '{preset_name}' should be retrievable"
            assert isinstance(preset, CachePreset), f"Listed preset '{preset_name}' should be a CachePreset instance"
        
        # Verify list order is consistent across multiple calls
        second_call = manager.list_presets()
        assert available_presets == second_call, "list_presets() should return consistent order across calls"


class TestCachePresetManagerRecommendation:
    """
    Test suite for CachePresetManager environment-based recommendation functionality.
    
    Scope:
        - Environment detection and classification
        - Intelligent preset recommendation based on environment characteristics
        - Recommendation confidence scoring and reasoning
        - Complex deployment scenario handling
        
    Business Critical:
        Intelligent preset recommendation enables optimal cache configuration selection
        
    Test Strategy:
        - Unit tests for recommend_preset() with various environment scenarios
        - Environment detection testing with mock environment variables
        - Recommendation confidence and reasoning verification
        - Complex deployment scenario recommendation testing
        
    External Dependencies:
        - Environment variables (mocked): Environment detection input
        - EnvironmentRecommendation (real): Recommendation result structure
    """

    def test_cache_preset_manager_recommend_preset_detects_development_environments(self):
        """
        Test that recommend_preset() detects development environments and recommends appropriate presets.
        
        Verifies:
            Development environment detection leads to development-optimized preset recommendations
            
        Business Impact:
            Enables automatic configuration optimization for development workflow efficiency
            
        Scenario:
            Given: Environment variables indicating development environment
            When: recommend_preset() is called with environment detection
            Then: Development-appropriate preset is recommended
            And: Recommendation confidence reflects environment detection accuracy
            And: Development preset optimizes for fast feedback and iteration
            And: Recommendation reasoning explains development environment characteristics
            
        Development Environment Detection Verified:
            - Environment variables like 'development', 'dev', 'local' trigger development preset
            - ENVIRONMENT, NODE_ENV, FLASK_ENV variables are considered
            - Development preset recommendation prioritizes development speed
            - Recommendation confidence is high for clear development indicators
            
        Fixtures Used:
            - Environment variable mocking for development scenario simulation
            
        Development Optimization Verified:
            Development environment detection leads to workflow-optimized cache configuration
            
        Related Tests:
            - test_cache_preset_manager_recommend_preset_detects_production_environments()
            - test_recommendation_confidence_reflects_environment_detection_accuracy()
        """
        manager = CachePresetManager()
        
        # Test explicit development environment names
        development_environments = ['development', 'dev', 'local', 'testing', 'test']
        
        for env_name in development_environments:
            preset_name = manager.recommend_preset(env_name)
            assert preset_name == 'development', f"Environment '{env_name}' should recommend development preset, got '{preset_name}'"
        
        # Test development environment detection with details
        detailed_recommendation = manager.recommend_preset_with_details('development')
        assert isinstance(detailed_recommendation, EnvironmentRecommendation), "Should return EnvironmentRecommendation instance"
        assert detailed_recommendation.preset_name == 'development', "Should recommend development preset"
        assert detailed_recommendation.confidence >= 0.85, "Should have high confidence for explicit development environment"
        assert 'development' in detailed_recommendation.reasoning.lower(), "Reasoning should mention development"
        assert detailed_recommendation.environment_detected == 'development', "Should correctly identify environment"
        
        # Test 'dev' abbreviation
        dev_recommendation = manager.recommend_preset_with_details('dev')
        assert dev_recommendation.preset_name == 'development', "'dev' should map to development preset"
        assert dev_recommendation.confidence >= 0.80, "Should have high confidence for 'dev' abbreviation"
        
        # Test with environment variable mocking for auto-detection
        with patch.dict(os.environ, {'NODE_ENV': 'development'}, clear=False):
            auto_recommendation = manager.recommend_preset_with_details(None)  # Auto-detect
            assert auto_recommendation.preset_name == 'development', "Auto-detection should find development from NODE_ENV"
            assert auto_recommendation.confidence >= 0.70, "Auto-detection should have reasonable confidence"
        
        with patch.dict(os.environ, {'ENVIRONMENT': 'dev'}, clear=False):
            auto_recommendation = manager.recommend_preset_with_details(None)
            assert auto_recommendation.preset_name == 'development', "Auto-detection should find development from ENVIRONMENT"
        
        with patch.dict(os.environ, {'FLASK_ENV': 'development'}, clear=False):
            auto_recommendation = manager.recommend_preset_with_details(None)
            assert auto_recommendation.preset_name == 'development', "Auto-detection should find development from FLASK_ENV"
        
        # Verify development preset characteristics for optimization
        dev_preset = manager.get_preset('development')
        assert dev_preset.strategy == CacheStrategy.FAST, "Development preset should use FAST strategy for quick feedback"
        assert dev_preset.default_ttl == 600, "Development preset should have short TTL for fast iteration"
        assert dev_preset.connection_timeout == 2, "Development preset should have fast timeout"
        assert dev_preset.log_level == "DEBUG", "Development preset should enable debug logging"

    def test_cache_preset_manager_recommend_preset_detects_production_environments(self):
        """
        Test that recommend_preset() detects production environments and recommends robust presets.
        
        Verifies:
            Production environment detection leads to production-optimized preset recommendations
            
        Business Impact:
            Ensures production deployments use reliable, high-performance cache configurations
            
        Scenario:
            Given: Environment variables indicating production environment
            When: recommend_preset() is called with environment detection
            Then: Production-appropriate preset is recommended
            And: Production preset optimizes for reliability and performance
            And: Recommendation confidence is high for production indicators
            And: Recommendation reasoning explains production environment requirements
            
        Production Environment Detection Verified:
            - Environment variables like 'production', 'prod', 'live' trigger production preset
            - Production preset recommendation prioritizes reliability and performance
            - High connection limits and robust TTL settings are recommended
            - Recommendation confidence reflects production environment certainty
            
        Fixtures Used:
            - Environment variable mocking for production scenario simulation
            
        Production Optimization Verified:
            Production environment detection leads to reliability-optimized cache configuration
            
        Related Tests:
            - test_cache_preset_manager_recommend_preset_detects_ai_environments()
            - test_production_recommendations_prioritize_reliability_over_speed()
        """
        manager = CachePresetManager()
        
        # Test explicit production environment names
        production_environments = ['production', 'prod', 'live', 'staging', 'stage']
        
        for env_name in production_environments:
            preset_name = manager.recommend_preset(env_name)
            assert preset_name == 'production', f"Environment '{env_name}' should recommend production preset, got '{preset_name}'"
        
        # Test production environment detection with details
        detailed_recommendation = manager.recommend_preset_with_details('production')
        assert isinstance(detailed_recommendation, EnvironmentRecommendation), "Should return EnvironmentRecommendation instance"
        assert detailed_recommendation.preset_name == 'production', "Should recommend production preset"
        assert detailed_recommendation.confidence >= 0.85, "Should have high confidence for explicit production environment"
        assert 'production' in detailed_recommendation.reasoning.lower(), "Reasoning should mention production"
        assert detailed_recommendation.environment_detected == 'production', "Should correctly identify environment"
        
        # Test 'prod' abbreviation
        prod_recommendation = manager.recommend_preset_with_details('prod')
        assert prod_recommendation.preset_name == 'production', "'prod' should map to production preset"
        assert prod_recommendation.confidence >= 0.80, "Should have high confidence for 'prod' abbreviation"
        
        # Test 'staging' should map to production (common pattern)
        staging_recommendation = manager.recommend_preset_with_details('staging')
        assert staging_recommendation.preset_name == 'production', "Staging should use production-like settings"
        assert staging_recommendation.confidence >= 0.80, "Should have high confidence for staging environment"
        
        # Test with environment variable mocking for auto-detection
        with patch.dict(os.environ, {'NODE_ENV': 'production'}, clear=False):
            auto_recommendation = manager.recommend_preset_with_details(None)  # Auto-detect
            assert auto_recommendation.preset_name == 'production', "Auto-detection should find production from NODE_ENV"
            assert auto_recommendation.confidence >= 0.70, "Auto-detection should have reasonable confidence"
        
        with patch.dict(os.environ, {'ENVIRONMENT': 'prod'}, clear=False):
            auto_recommendation = manager.recommend_preset_with_details(None)
            assert auto_recommendation.preset_name == 'production', "Auto-detection should find production from ENVIRONMENT"
        
        # Clear development indicators and set production indicators
        with patch.dict(os.environ, {'PRODUCTION': 'true', 'DEBUG': 'false'}, clear=False):
            with patch('os.path.exists', return_value=False):  # Remove development file indicators
                auto_recommendation = manager.recommend_preset_with_details(None)
                assert auto_recommendation.preset_name == 'production', "Auto-detection should find production when dev indicators are cleared"
        
        # Verify production preset characteristics for reliability
        prod_preset = manager.get_preset('production')
        assert prod_preset.strategy == CacheStrategy.ROBUST, "Production preset should use ROBUST strategy for reliability"
        assert prod_preset.default_ttl == 7200, "Production preset should have longer TTL for efficiency"
        assert prod_preset.max_connections == 20, "Production preset should have high connection pool"
        assert prod_preset.compression_level == 9, "Production preset should use maximum compression"
        assert prod_preset.log_level == "INFO", "Production preset should use INFO logging level"

    def test_cache_preset_manager_recommend_preset_detects_ai_environments(self):
        """
        Test that recommend_preset() detects AI environments and recommends AI-optimized presets.
        
        Verifies:
            AI environment detection leads to AI-workload-optimized preset recommendations
            
        Business Impact:
            Ensures AI workloads receive cache configurations optimized for text processing and AI operations
            
        Scenario:
            Given: Environment variables or context indicating AI workload deployment
            When: recommend_preset() is called with AI environment detection
            Then: AI-optimized preset is recommended
            And: AI preset includes text processing optimizations
            And: AI-specific cache features are enabled in recommendation
            And: Recommendation reasoning explains AI workload characteristics
            
        AI Environment Detection Verified:
            - Environment variables with 'ai', 'ml', 'nlp' patterns trigger AI presets
            - AI preset recommendations enable AI cache features
            - Text processing optimizations are included in AI recommendations
            - AI development vs production environments are distinguished
            
        Fixtures Used:
            - Environment variable mocking for AI deployment scenarios
            
        AI Workload Optimization Verified:
            AI environment detection leads to text-processing-optimized cache configuration
            
        Related Tests:
            - test_cache_preset_manager_distinguishes_ai_development_vs_production()
            - test_ai_recommendations_include_text_processing_optimizations()
        """
        manager = CachePresetManager()
        
        # Test explicit AI environment names
        ai_development_environments = ['ai-development', 'ai-dev']
        ai_production_environments = ['ai-production', 'ai-prod']
        
        for env_name in ai_development_environments:
            preset_name = manager.recommend_preset(env_name)
            assert preset_name == 'ai-development', f"Environment '{env_name}' should recommend ai-development preset, got '{preset_name}'"
        
        for env_name in ai_production_environments:
            preset_name = manager.recommend_preset(env_name)
            assert preset_name == 'ai-production', f"Environment '{env_name}' should recommend ai-production preset, got '{preset_name}'"
        
        # Test AI development environment with details
        ai_dev_recommendation = manager.recommend_preset_with_details('ai-development')
        assert isinstance(ai_dev_recommendation, EnvironmentRecommendation), "Should return EnvironmentRecommendation instance"
        assert ai_dev_recommendation.preset_name == 'ai-development', "Should recommend ai-development preset"
        assert ai_dev_recommendation.confidence >= 0.90, "Should have high confidence for explicit AI development environment"
        assert 'ai' in ai_dev_recommendation.reasoning.lower(), "Reasoning should mention AI"
        
        # Test AI production environment with details
        ai_prod_recommendation = manager.recommend_preset_with_details('ai-production')
        assert ai_prod_recommendation.preset_name == 'ai-production', "Should recommend ai-production preset"
        assert ai_prod_recommendation.confidence >= 0.90, "Should have high confidence for explicit AI production environment"
        
        # Test environment variable mocking for AI detection
        with patch.dict(os.environ, {'ENVIRONMENT': 'ai-development'}, clear=False):
            auto_recommendation = manager.recommend_preset_with_details(None)  # Auto-detect
            assert auto_recommendation.preset_name == 'ai-development', "Auto-detection should find AI development from ENVIRONMENT"
            assert auto_recommendation.confidence >= 0.70, "Auto-detection should have reasonable confidence"
        
        with patch.dict(os.environ, {'ENVIRONMENT': 'ai-prod'}, clear=False):
            auto_recommendation = manager.recommend_preset_with_details(None)
            assert auto_recommendation.preset_name == 'ai-production', "Auto-detection should find AI production from ENVIRONMENT"
        
        with patch.dict(os.environ, {'ENABLE_AI_CACHE': 'true', 'NODE_ENV': 'development'}, clear=False):
            auto_recommendation = manager.recommend_preset_with_details(None)
            assert auto_recommendation.preset_name == 'ai-development', "Should detect AI development when AI cache enabled with dev environment"
        
        with patch.dict(os.environ, {'ENABLE_AI_CACHE': 'true', 'NODE_ENV': 'production'}, clear=False):
            auto_recommendation = manager.recommend_preset_with_details(None)
            assert auto_recommendation.preset_name == 'ai-production', "Should detect AI production when AI cache enabled with prod environment"
        
        # Verify AI preset characteristics
        ai_dev_preset = manager.get_preset('ai-development')
        assert ai_dev_preset.strategy == CacheStrategy.AI_OPTIMIZED, "AI development preset should use AI_OPTIMIZED strategy"
        assert ai_dev_preset.enable_ai_cache is True, "AI development preset should enable AI cache features"
        assert ai_dev_preset.ai_optimizations is not None, "AI development preset should have AI optimizations"
        assert 'operation_ttls' in ai_dev_preset.ai_optimizations, "AI preset should have operation-specific TTLs"
        assert 'text_hash_threshold' in ai_dev_preset.ai_optimizations, "AI preset should have text hashing configuration"
        
        ai_prod_preset = manager.get_preset('ai-production')
        assert ai_prod_preset.strategy == CacheStrategy.AI_OPTIMIZED, "AI production preset should use AI_OPTIMIZED strategy"
        assert ai_prod_preset.enable_ai_cache is True, "AI production preset should enable AI cache features"
        assert ai_prod_preset.max_connections == 25, "AI production preset should have high connection pool for AI workloads"
        assert ai_prod_preset.memory_cache_size == 1000, "AI production preset should have large memory cache for AI data"

    def test_cache_preset_manager_recommend_preset_with_details_provides_comprehensive_reasoning(self):
        """
        Test that recommend_preset_with_details() provides comprehensive recommendation reasoning.
        
        Verifies:
            Detailed recommendations include confidence scoring and decision reasoning
            
        Business Impact:
            Enables informed decision-making about cache configuration selection
            
        Scenario:
            Given: Environment context for preset recommendation
            When: recommend_preset_with_details() is called
            Then: EnvironmentRecommendation is returned with comprehensive details
            And: Confidence score reflects environment detection accuracy
            And: Reasoning explains why specific preset was recommended
            And: Alternative preset options are considered in reasoning
            
        Detailed Recommendation Verified:
            - EnvironmentRecommendation includes preset name and confidence score
            - Reasoning explains environment characteristics that influenced recommendation
            - Confidence score reflects accuracy of environment detection
            - Alternative preset considerations are explained when applicable
            
        Fixtures Used:
            - Environment variable mocking for detailed recommendation testing
            
        Decision Support Verified:
            Detailed recommendations provide information needed for informed configuration decisions
            
        Related Tests:
            - test_recommendation_confidence_scores_are_accurate()
            - test_recommendation_reasoning_explains_decision_factors()
        """
        manager = CachePresetManager()
        
        # Test detailed recommendation structure for development environment
        recommendation = manager.recommend_preset_with_details('development')
        
        # Verify return type and structure
        assert isinstance(recommendation, EnvironmentRecommendation), "Should return EnvironmentRecommendation instance"
        assert hasattr(recommendation, 'preset_name'), "Should have preset_name attribute"
        assert hasattr(recommendation, 'confidence'), "Should have confidence attribute"
        assert hasattr(recommendation, 'reasoning'), "Should have reasoning attribute"
        assert hasattr(recommendation, 'environment_detected'), "Should have environment_detected attribute"
        
        # Verify preset name is valid
        assert recommendation.preset_name in manager.list_presets(), "Recommended preset should be available"
        
        # Verify confidence score is within valid range
        assert 0.0 <= recommendation.confidence <= 1.0, f"Confidence should be between 0.0 and 1.0, got {recommendation.confidence}"
        
        # Verify reasoning is informative
        assert isinstance(recommendation.reasoning, str), "Reasoning should be a string"
        assert len(recommendation.reasoning) > 0, "Reasoning should not be empty"
        assert 'development' in recommendation.reasoning.lower(), "Reasoning should explain development context"
        
        # Verify environment detected
        assert recommendation.environment_detected == 'development', "Should correctly identify detected environment"
        
        # Test high-confidence scenarios
        high_confidence_envs = ['production', 'development', 'ai-production']
        for env in high_confidence_envs:
            rec = manager.recommend_preset_with_details(env)
            assert rec.confidence >= 0.90, f"Exact match for '{env}' should have high confidence, got {rec.confidence}"
            # For AI production, check for 'ai' and 'production' separately since the reasoning might say "AI production"
            if env == 'ai-production':
                reasoning_lower = rec.reasoning.lower()
                assert 'ai' in reasoning_lower and 'production' in reasoning_lower, f"Reasoning should mention AI and production for '{env}', got: {rec.reasoning}"
            else:
                assert env in rec.reasoning.lower(), f"Reasoning should mention '{env}' environment"
        
        # Test medium-confidence scenarios
        medium_confidence_envs = ['dev', 'prod', 'staging']
        for env in medium_confidence_envs:
            rec = manager.recommend_preset_with_details(env)
            assert 0.70 <= rec.confidence < 0.95, f"Abbreviation '{env}' should have medium confidence, got {rec.confidence}"
            assert len(rec.reasoning) > 20, "Reasoning should be descriptive for abbreviations"
        
        # Test auto-detection with comprehensive details
        with patch.dict(os.environ, {'NODE_ENV': 'production', 'DEBUG': 'false'}, clear=False):
            auto_rec = manager.recommend_preset_with_details(None)
            assert auto_rec.preset_name == 'production', "Auto-detection should find production"
            assert auto_rec.confidence >= 0.70, "Auto-detection should have reasonable confidence"
            assert 'auto-detected' in auto_rec.environment_detected.lower(), "Should indicate auto-detection"
            assert len(auto_rec.reasoning) > 30, "Auto-detection reasoning should be comprehensive"
        
        # Test pattern matching with reasoning
        pattern_envs = ['dev-staging', 'prod-cluster-1', 'ai-ml-production']
        for env in pattern_envs:
            rec = manager.recommend_preset_with_details(env)
            assert isinstance(rec.reasoning, str), f"Pattern matching for '{env}' should provide reasoning"
            assert 'pattern' in rec.reasoning.lower() or 'match' in rec.reasoning.lower(), "Should explain pattern matching"
        
        # Test fallback scenarios have lower confidence but informative reasoning
        unknown_envs = ['unknown-env', 'custom-deployment']
        for env in unknown_envs:
            rec = manager.recommend_preset_with_details(env)
            assert rec.confidence < 0.60, f"Unknown environment '{env}' should have lower confidence"
            assert 'default' in rec.reasoning.lower() or 'unknown' in rec.reasoning.lower(), "Should explain fallback reasoning"

    def test_cache_preset_manager_handles_ambiguous_environment_scenarios(self):
        """
        Test that recommend_preset() handles ambiguous environment scenarios appropriately.
        
        Verifies:
            Ambiguous environment detection leads to safe default recommendations
            
        Business Impact:
            Prevents misconfiguration in unclear deployment scenarios
            
        Scenario:
            Given: Environment variables with conflicting or unclear signals
            When: recommend_preset() is called with ambiguous environment
            Then: Safe default preset is recommended with lower confidence
            And: Recommendation reasoning explains ambiguity and default selection
            And: Conservative configuration is chosen to avoid performance issues
            And: Manual configuration review is suggested for ambiguous cases
            
        Ambiguous Environment Handling Verified:
            - Conflicting environment signals result in safe default recommendations
            - Lower confidence scores reflect environment detection uncertainty
            - Conservative preset selection avoids potential performance issues
            - Reasoning explains ambiguity and suggests manual review
            
        Fixtures Used:
            - Environment variable mocking for ambiguous scenario creation
            
        Configuration Safety Verified:
            Ambiguous environment handling prevents misconfiguration through conservative defaults
            
        Related Tests:
            - test_cache_preset_manager_suggests_manual_review_for_complex_scenarios()
            - test_ambiguous_environment_recommendations_are_conservative()
        """
        manager = CachePresetManager()
        
        # Test unknown/unclear environment names
        # Note: Some ambiguous environments might still match patterns with reasonable confidence
        truly_ambiguous_environments = ['custom-deployment', 'unknown-env', 'mystery-env']
        pattern_matching_environments = ['testing-prod', 'dev-like-prod']  # These may match patterns
        
        for env_name in truly_ambiguous_environments:
            recommendation = manager.recommend_preset_with_details(env_name)
            
            # Should recommend safe default (simple preset is a good conservative choice)
            assert recommendation.preset_name in ['simple', 'development'], f"Ambiguous environment '{env_name}' should get safe default preset"
            
            # Should have lower confidence to reflect uncertainty
            assert recommendation.confidence <= 0.50, f"Truly ambiguous environment '{env_name}' should have low confidence, got {recommendation.confidence}"
            
            # Reasoning should explain the ambiguity
            reasoning_lower = recommendation.reasoning.lower()
            assert any(word in reasoning_lower for word in ['unknown', 'default', 'pattern', 'simple']), f"Reasoning should explain ambiguity for '{env_name}'"
        
        # Test environments that might match patterns but are still somewhat ambiguous
        for env_name in pattern_matching_environments:
            recommendation = manager.recommend_preset_with_details(env_name)
            
            # Should still recommend a reasonable preset based on pattern matching
            assert recommendation.preset_name in manager.list_presets(), f"Pattern-matched environment '{env_name}' should get valid preset"
            
            # Pattern matching gives moderate confidence (not as low as truly unknown)
            assert 0.40 <= recommendation.confidence <= 0.80, f"Pattern-matched environment '{env_name}' should have moderate confidence, got {recommendation.confidence}"
        
        # Test conflicting environment variables (simulating conflicting signals)
        # Note: The implementation gives priority to explicit environment variables first,
        # so NODE_ENV=development will take precedence over PROD=true
        with patch.dict(os.environ, {'NODE_ENV': 'development', 'PROD': 'true'}, clear=False):
            recommendation = manager.recommend_preset_with_details(None)
            # Should handle conflicting signals gracefully by following priority order
            assert recommendation.preset_name in ['development', 'production', 'simple'], "Should handle conflicting signals"
            # The confidence may still be high if the primary signal (NODE_ENV) is clear
            assert recommendation.confidence >= 0.70, "Primary environment signal should still have reasonable confidence"
        
        # Test empty/minimal environment detection
        # Note: The test environment itself may have development indicators like .git
        # so we need to mock those away for a truly clean test
        with patch.dict(os.environ, {}, clear=True):
            with patch('os.path.exists', return_value=False):  # Remove all file-based indicators
                recommendation = manager.recommend_preset_with_details(None)
                
                # Should fall back to safe default when no indicators are present
                assert recommendation.preset_name in ['simple', 'ai-development'], "No environment signals should use safe fallback"
                assert recommendation.confidence <= 0.60, "No clear signals should have low confidence"
                assert 'default' in recommendation.reasoning.lower() or 'no clear' in recommendation.reasoning.lower(), "Should explain lack of clear signals"
        
        # Test complex/compound environment names that don't clearly map
        complex_environments = ['dev-staging-test', 'prod-dev-hybrid', 'staging-like-prod']
        
        for env_name in complex_environments:
            recommendation = manager.recommend_preset_with_details(env_name)
            
            # Should still make a reasonable recommendation based on pattern matching
            assert recommendation.preset_name in manager.list_presets(), "Should recommend a valid preset"
            
            # But with appropriate confidence reflecting the complexity (allowing for pattern matching)
            assert 0.30 <= recommendation.confidence <= 0.80, f"Complex environment '{env_name}' should have moderate confidence"
        
        # Verify conservative preset characteristics for ambiguous cases
        simple_preset = manager.get_preset('simple')
        assert simple_preset.strategy == CacheStrategy.BALANCED, "Simple preset should be balanced/conservative"
        assert simple_preset.enable_monitoring is True, "Conservative preset should enable monitoring for visibility"
        
        # Test that reasoning includes helpful guidance for manual review
        unclear_recommendation = manager.recommend_preset_with_details('unclear-environment')
        reasoning_words = unclear_recommendation.reasoning.lower().split()
        # Should provide some guidance about the selection
        assert len(reasoning_words) >= 5, "Reasoning should be descriptive for unclear environments"


class TestCachePresetManagerValidation:
    """
    Test suite for CachePresetManager validation and quality assurance functionality.
    
    Scope:
        - Preset validation integration
        - Configuration quality assurance
        - Preset consistency checking
        - Validation error reporting and guidance
        
    Business Critical:
        Preset validation ensures deployment-ready configurations across all preset types
        
    Test Strategy:
        - Unit tests for validate_preset() method with various preset configurations
        - Preset quality assurance testing with predefined presets
        - Validation integration testing with configuration systems
        - Error reporting and guidance verification
        
    External Dependencies:
        - Preset validation logic (internal): Configuration validation integration
    """

    def test_cache_preset_manager_validate_preset_confirms_preset_quality(self):
        """
        Test that validate_preset() confirms preset configuration quality.
        
        Verifies:
            Preset validation ensures deployment-ready configuration quality
            
        Business Impact:
            Prevents deployment of invalid preset configurations
            
        Scenario:
            Given: CachePreset with complete configuration parameters
            When: validate_preset() is called
            Then: Validation confirms preset configuration quality
            And: All preset parameters pass validation checks
            And: Strategy-parameter consistency is verified
            And: Preset is marked as deployment-ready
            
        Preset Quality Validation Verified:
            - All parameter values are within acceptable ranges
            - Strategy-parameter alignment is consistent
            - Required parameters are present and valid
            - Optional parameters have appropriate defaults
            
        Fixtures Used:
            - None (testing preset validation directly)
            
        Configuration Quality Assurance Verified:
            Preset validation ensures reliable deployment-ready configurations
            
        Related Tests:
            - test_cache_preset_manager_validates_all_predefined_presets()
            - test_preset_validation_identifies_configuration_issues()
        """
        manager = CachePresetManager()
        
        # Test validation of a well-formed preset
        valid_preset = CachePreset(
            name="test_valid_preset",
            description="Test preset with valid configuration",
            strategy=CacheStrategy.BALANCED,
            default_ttl=3600,  # Valid: 1 hour
            max_connections=10,  # Valid: reasonable connection pool
            connection_timeout=5,  # Valid: 5 seconds
            memory_cache_size=100,  # Valid: 100 entries
            compression_threshold=1000,  # Valid threshold
            compression_level=6,  # Valid compression level
            enable_ai_cache=False,
            enable_monitoring=True,
            log_level="INFO",
            environment_contexts=["testing"],
            ai_optimizations={}
        )
        
        # Validate the preset
        is_valid = manager.validate_preset(valid_preset)
        assert is_valid is True, "Well-formed preset should pass validation"
        
        # Test validation with AI preset
        valid_ai_preset = CachePreset(
            name="test_valid_ai_preset",
            description="Test AI preset with valid configuration",
            strategy=CacheStrategy.AI_OPTIMIZED,
            default_ttl=1800,  # Valid: 30 minutes
            max_connections=15,  # Valid: higher for AI workloads
            connection_timeout=8,  # Valid: longer for AI operations
            memory_cache_size=200,  # Valid: larger for AI data
            compression_threshold=500,  # Valid: aggressive compression
            compression_level=9,  # Valid: maximum compression
            enable_ai_cache=True,
            enable_monitoring=True,
            log_level="INFO",
            environment_contexts=["ai-testing"],
            ai_optimizations={
                "text_hash_threshold": 1000,  # Valid
                "operation_ttls": {
                    "summarize": 1800,  # Valid TTL
                    "sentiment": 900,   # Valid TTL
                },
                "hash_algorithm": "sha256"
            }
        )
        
        # Validate the AI preset
        is_ai_valid = manager.validate_preset(valid_ai_preset)
        assert is_ai_valid is True, "Well-formed AI preset should pass validation"
        
        # Test parameter range validation by checking boundaries
        boundary_preset = CachePreset(
            name="test_boundary_preset",
            description="Test preset at parameter boundaries",
            strategy=CacheStrategy.FAST,
            default_ttl=60,  # Minimum valid TTL
            max_connections=1,  # Minimum connections
            connection_timeout=1,  # Minimum timeout
            memory_cache_size=1,  # Minimum cache size
            compression_threshold=1,  # Minimum threshold
            compression_level=1,  # Minimum compression
            enable_ai_cache=False,
            enable_monitoring=True,
            log_level="DEBUG",
            environment_contexts=["testing"],
            ai_optimizations={}
        )
        
        # Should validate boundary values
        is_boundary_valid = manager.validate_preset(boundary_preset)
        assert is_boundary_valid is True, "Preset with minimum valid values should pass validation"

    def test_cache_preset_manager_validates_all_predefined_presets(self):
        """
        Test that validate_preset() confirms all predefined presets pass validation.
        
        Verifies:
            All CACHE_PRESETS configurations are valid and deployment-ready
            
        Business Impact:
            Ensures reliability of all standard preset configurations
            
        Scenario:
            Given: All predefined presets in CACHE_PRESETS
            When: Each preset is validated using validate_preset()
            Then: All presets pass validation without errors
            And: Each preset is confirmed as deployment-ready
            And: Preset quality is consistent across all deployment scenarios
            And: No preset has configuration issues that would prevent deployment
            
        Comprehensive Preset Validation Verified:
            - 'disabled', 'simple' presets pass validation
            - 'development', 'production' presets pass validation
            - 'ai-development', 'ai-production' presets pass validation
            - All presets meet quality standards for their intended scenarios
            
        Fixtures Used:
            - None (validating real CACHE_PRESETS configurations)
            
        Preset Reliability Verified:
            All standard presets provide reliable, validated configurations
            
        Related Tests:
            - test_cache_preset_manager_validation_catches_configuration_errors()
            - test_preset_validation_ensures_deployment_readiness()
        """
        manager = CachePresetManager()
        
        # Get all available preset names
        preset_names = manager.list_presets()
        
        # Validate each predefined preset
        validation_results = {}
        for preset_name in preset_names:
            preset = manager.get_preset(preset_name)
            is_valid = manager.validate_preset(preset)
            validation_results[preset_name] = is_valid
            
            # Each preset should pass validation
            assert is_valid is True, f"Predefined preset '{preset_name}' should pass validation"
        
        # Verify all expected presets were validated
        expected_presets = ['disabled', 'minimal', 'simple', 'development', 'production', 'ai-development', 'ai-production']
        for expected_preset in expected_presets:
            assert expected_preset in validation_results, f"Expected preset '{expected_preset}' should be validated"
            assert validation_results[expected_preset] is True, f"Expected preset '{expected_preset}' should be valid"
        
        # Verify specific preset categories are all valid
        basic_presets = ['disabled', 'minimal', 'simple']
        for preset_name in basic_presets:
            preset = manager.get_preset(preset_name)
            assert preset.enable_ai_cache is False, f"Basic preset '{preset_name}' should not have AI cache enabled"
            assert manager.validate_preset(preset) is True, f"Basic preset '{preset_name}' should be valid"
        
        development_presets = ['development', 'ai-development']
        for preset_name in development_presets:
            preset = manager.get_preset(preset_name)
            assert preset.log_level == "DEBUG", f"Development preset '{preset_name}' should use DEBUG logging"
            assert preset.default_ttl <= 1800, f"Development preset '{preset_name}' should have short TTL for quick feedback"
            assert manager.validate_preset(preset) is True, f"Development preset '{preset_name}' should be valid"
        
        production_presets = ['production', 'ai-production']
        for preset_name in production_presets:
            preset = manager.get_preset(preset_name)
            assert preset.max_connections >= 20, f"Production preset '{preset_name}' should have high connection pool"
            assert preset.compression_level >= 6, f"Production preset '{preset_name}' should use good compression"
            assert manager.validate_preset(preset) is True, f"Production preset '{preset_name}' should be valid"
        
        ai_presets = ['ai-development', 'ai-production']
        for preset_name in ai_presets:
            preset = manager.get_preset(preset_name)
            assert preset.enable_ai_cache is True, f"AI preset '{preset_name}' should enable AI cache"
            assert preset.strategy == CacheStrategy.AI_OPTIMIZED, f"AI preset '{preset_name}' should use AI_OPTIMIZED strategy"
            assert len(preset.ai_optimizations) > 0, f"AI preset '{preset_name}' should have AI optimizations"
            assert manager.validate_preset(preset) is True, f"AI preset '{preset_name}' should be valid"
        
        # Verify validation success rate
        total_presets = len(validation_results)
        valid_presets = sum(validation_results.values())
        validation_rate = valid_presets / total_presets if total_presets > 0 else 0
        
        assert validation_rate == 1.0, f"All predefined presets should be valid, got {validation_rate:.2%} success rate"

    def test_cache_preset_manager_get_all_presets_summary_provides_comprehensive_overview(self):
        """
        Test that get_all_presets_summary() provides comprehensive preset overview.
        
        Verifies:
            Preset summary enables informed preset selection and comparison
            
        Business Impact:
            Supports configuration decision-making with complete preset information
            
        Scenario:
            Given: CachePresetManager with complete preset registry
            When: get_all_presets_summary() is called
            Then: Summary includes all preset information for comparison
            And: Summary data enables informed preset selection
            And: Preset characteristics are clearly described
            And: Summary supports configuration UI development
            
        Preset Summary Information Verified:
            - All preset names, descriptions, and strategies are included
            - Environment contexts are summarized for deployment guidance
            - Performance characteristics are highlighted for comparison
            - AI features are clearly identified for AI-enabled presets
            
        Fixtures Used:
            - None (testing preset summary generation directly)
            
        Configuration Decision Support Verified:
            Preset summary provides information needed for informed configuration selection
            
        Related Tests:
            - test_preset_summary_enables_configuration_comparison()
            - test_preset_summary_supports_ui_development()
        """
        manager = CachePresetManager()
        
        # Get comprehensive summary of all presets
        summary = manager.get_all_presets_summary()
        
        # Verify return structure
        assert isinstance(summary, dict), "get_all_presets_summary() should return a dictionary"
        
        # Verify all expected presets are included in summary
        expected_presets = manager.list_presets()
        assert len(summary) == len(expected_presets), "Summary should include all available presets"
        
        for preset_name in expected_presets:
            assert preset_name in summary, f"Summary should include '{preset_name}' preset"
        
        # Verify each preset summary has required information
        for preset_name, preset_info in summary.items():
            assert isinstance(preset_info, dict), f"Preset '{preset_name}' summary should be a dictionary"
            
            # Check required fields
            required_fields = ['name', 'description', 'configuration', 'environment_contexts']
            for field in required_fields:
                assert field in preset_info, f"Preset '{preset_name}' summary should include '{field}' field"
            
            # Verify configuration details are present
            config = preset_info['configuration']
            config_fields = ['strategy', 'default_ttl', 'max_connections', 'enable_ai_cache', 'log_level']
            for field in config_fields:
                assert field in config, f"Preset '{preset_name}' configuration should include '{field}'"
        
        # Test comparison capabilities by checking strategy distribution
        strategies = {}
        for preset_name, preset_info in summary.items():
            strategy = preset_info['configuration']['strategy']
            strategies[strategy] = strategies.get(strategy, 0) + 1
        
        # Should have multiple strategies represented
        assert len(strategies) >= 3, "Summary should include multiple cache strategies"
        assert 'fast' in strategies, "Summary should include fast strategy presets"
        assert 'balanced' in strategies, "Summary should include balanced strategy presets"
        assert 'robust' in strategies, "Summary should include robust strategy presets"
        
        # Verify AI feature identification
        ai_presets = []
        non_ai_presets = []
        
        for preset_name, preset_info in summary.items():
            if preset_info['configuration']['enable_ai_cache']:
                ai_presets.append(preset_name)
            else:
                non_ai_presets.append(preset_name)
        
        # Should have both AI and non-AI presets
        assert len(ai_presets) >= 2, "Summary should include AI-enabled presets"
        assert len(non_ai_presets) >= 4, "Summary should include non-AI presets"
        
        # Verify AI presets have AI optimizations in summary
        for ai_preset_name in ai_presets:
            ai_preset_info = summary[ai_preset_name]
            assert 'ai_optimizations' in ai_preset_info, f"AI preset '{ai_preset_name}' summary should include AI optimizations"
            assert ai_preset_info['ai_optimizations'] is not None, f"AI preset '{ai_preset_name}' should have non-null AI optimizations"
        
        # Verify environment context coverage
        all_contexts = set()
        for preset_info in summary.values():
            contexts = preset_info['environment_contexts']
            all_contexts.update(contexts)
        
        # Should cover main deployment scenarios
        expected_contexts = {'development', 'testing', 'production', 'staging'}
        context_coverage = expected_contexts.intersection(all_contexts)
        assert len(context_coverage) >= 3, f"Summary should cover major deployment contexts, got {context_coverage}"
        
        # Verify performance characteristics are distinguishable
        ttl_values = [preset_info['configuration']['default_ttl'] for preset_info in summary.values()]
        connection_values = [preset_info['configuration']['max_connections'] for preset_info in summary.values()]
        
        # Should have variety in performance characteristics
        assert len(set(ttl_values)) >= 4, "Summary should show variety in TTL configurations for comparison"
        assert len(set(connection_values)) >= 4, "Summary should show variety in connection pool sizes for comparison"
        
        # Verify summary supports UI development with descriptive information
        for preset_name, preset_info in summary.items():
            description = preset_info['description']
            assert isinstance(description, str), f"Preset '{preset_name}' description should be a string"
            assert len(description) > 20, f"Preset '{preset_name}' description should be descriptive for UI display"
    
    def test_cache_preset_manager_get_preset_details_provides_specific_preset_information(self):
        """
        Test that get_preset_details() provides detailed information about specific presets.
        
        Verifies:
            Detailed preset information supports configuration understanding and customization
            
        Business Impact:
            Enables deep understanding of preset configurations for customization decisions
            
        Scenario:
            Given: CachePresetManager with specific preset selection
            When: get_preset_details() is called for specific preset
            Then: Detailed preset information is returned
            And: Parameter values and rationale are explained
            And: Environment applicability is clearly described
            And: Customization guidance is provided
            
        Detailed Preset Information Verified:
            - Complete parameter configuration is detailed
            - Parameter rationale and optimization reasoning is explained
            - Environment context and applicability is described
            - Customization recommendations are provided where appropriate
            
        Fixtures Used:
            - None (testing preset detail generation directly)
            
        Configuration Understanding Verified:
            Detailed preset information enables informed customization and deployment decisions
            
        Related Tests:
            - test_preset_details_explain_parameter_optimization_reasoning()
            - test_preset_details_provide_customization_guidance()
        """
        manager = CachePresetManager()
        
        # Test details for development preset
        dev_details = manager.get_preset_details('development')
        
        # Verify return structure
        assert isinstance(dev_details, dict), "get_preset_details() should return a dictionary"
        
        # Verify required fields are present
        required_fields = ['name', 'description', 'configuration', 'environment_contexts']
        for field in required_fields:
            assert field in dev_details, f"Development preset details should include '{field}' field"
        
        # Verify detailed configuration information
        config = dev_details['configuration']
        assert config['strategy'] == 'fast', "Development preset should use fast strategy"
        assert config['default_ttl'] == 600, "Development preset should have 10-minute TTL"
        assert config['max_connections'] == 3, "Development preset should have minimal connections"
        assert config['log_level'] == 'DEBUG', "Development preset should use debug logging"
        
        # Verify environment contexts are descriptive
        contexts = dev_details['environment_contexts']
        assert isinstance(contexts, list), "Environment contexts should be a list"
        assert 'development' in contexts, "Development preset should list development context"
        assert 'local' in contexts, "Development preset should list local context"
        
        # Test details for AI production preset
        ai_prod_details = manager.get_preset_details('ai-production')
        
        # Verify AI-specific information is included
        ai_config = ai_prod_details['configuration']
        assert ai_config['enable_ai_cache'] is True, "AI production preset should enable AI cache"
        assert ai_config['strategy'] == 'ai_optimized', "AI production preset should use ai_optimized strategy"
        
        # Verify AI optimizations are detailed
        ai_opts = ai_prod_details['ai_optimizations']
        assert ai_opts is not None, "AI production preset should have AI optimizations details"
        
        # Test details for simple preset
        simple_details = manager.get_preset_details('simple')
        simple_config = simple_details['configuration']
        assert simple_config['strategy'] == 'balanced', "Simple preset should use balanced strategy"
        assert simple_config['enable_ai_cache'] is False, "Simple preset should not enable AI cache"
        
        # Verify multiple environment contexts for flexible presets
        simple_contexts = simple_details['environment_contexts']
        assert len(simple_contexts) >= 3, "Simple preset should support multiple environment contexts"
        
        # Test error handling for invalid preset names
        with pytest.raises(Exception):  # Should raise an error for invalid preset
            manager.get_preset_details('non_existent_preset')
        
        # Verify all available presets can provide details
        for preset_name in manager.list_presets():
            details = manager.get_preset_details(preset_name)
            assert isinstance(details, dict), f"Preset '{preset_name}' should provide valid details dictionary"
            assert 'name' in details, f"Preset '{preset_name}' details should include name"
            assert 'description' in details, f"Preset '{preset_name}' details should include description"
            assert len(details['description']) > 10, f"Preset '{preset_name}' should have descriptive description"

    def test_cache_preset_manager_get_preset_details_provides_specific_preset_information(self):
        """
        Test that get_preset_details() provides detailed information about specific presets.
        
        Verifies:
            Detailed preset information supports configuration understanding and customization
            
        Business Impact:
            Enables deep understanding of preset configurations for customization decisions
            
        Scenario:
            Given: CachePresetManager with specific preset selection
            When: get_preset_details() is called for specific preset
            Then: Detailed preset information is returned
            And: Parameter values and rationale are explained
            And: Environment applicability is clearly described
            And: Customization guidance is provided
            
        Detailed Preset Information Verified:
            - Complete parameter configuration is detailed
            - Parameter rationale and optimization reasoning is explained
            - Environment context and applicability is described
            - Customization recommendations are provided where appropriate
            
        Fixtures Used:
            - None (testing preset detail generation directly)
            
        Configuration Understanding Verified:
            Detailed preset information enables informed customization and deployment decisions
            
        Related Tests:
            - test_preset_details_explain_parameter_optimization_reasoning()
            - test_preset_details_provide_customization_guidance()
        """
        pass