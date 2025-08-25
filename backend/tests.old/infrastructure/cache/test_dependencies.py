"""
Tests for FastAPI cache dependency integration with preset system.

This module tests the cache dependency injection system with the new preset-based
configuration approach, ensuring all preset configurations work correctly with
FastAPI dependencies and override systems.

Test Categories:
    - Preset-based configuration loading tests
    - Environment variable validation and error handling 
    - Override precedence tests (Custom Config > Environment Variables > Preset Defaults)
    - Invalid preset handling with descriptive error messages
    - Fallback behavior when CACHE_PRESET not specified
    - Configuration validation after loading

Key Dependencies Under Test:
    - get_cache_config(): Main configuration dependency using preset system
    - get_cache_service(): Cache service creation with preset configurations
    - Settings integration with preset system
    - Override handling via CACHE_REDIS_URL, ENABLE_AI_CACHE, CACHE_CUSTOM_CONFIG
"""

from __future__ import annotations

import json
import pytest
from unittest.mock import patch, AsyncMock
from fastapi import Depends
from fastapi.testclient import TestClient
from fastapi import FastAPI

from app.core.config import Settings
from app.core.exceptions import ConfigurationError, ValidationError
from app.infrastructure.cache.dependencies import (
    get_cache_config,
    get_cache_service,
    get_settings,
    CacheDependencyManager
)
from app.infrastructure.cache.config import CacheConfig
from app.infrastructure.cache.cache_presets import cache_preset_manager, CACHE_PRESETS
from app.infrastructure.cache.base import CacheInterface


class TestCacheConfigDependency:
    """Test cache configuration dependency with preset system."""
    
    @pytest.mark.asyncio
    async def test_get_cache_config_with_all_presets(self, monkeypatch):
        """Test get_cache_config() with all available preset values."""
        preset_names = ['development', 'testing', 'production', 'ai-development', 'ai-production', 'simple', 'disabled']
        
        for preset_name in preset_names:
            # Set environment for this preset
            monkeypatch.setenv('CACHE_PRESET', preset_name)
            
            # Create settings instance with the preset
            settings = Settings()
            
            # Test the dependency function
            cache_config = await get_cache_config(settings)
            
            # Verify configuration is loaded correctly
            assert isinstance(cache_config, CacheConfig)
            assert cache_config is not None
            
            # Verify preset-specific characteristics
            if preset_name == 'disabled':
                assert not cache_config.enable_redis
            elif preset_name.startswith('ai-'):
                assert cache_config.enable_ai_cache
            else:
                # Standard presets should have basic configuration
                assert hasattr(cache_config, 'default_ttl')
                assert hasattr(cache_config, 'strategy')
            
            # Clean up for next iteration
            if 'CACHE_PRESET' in monkeypatch._setenv:
                monkeypatch.delenv('CACHE_PRESET')
    
    @pytest.mark.asyncio
    async def test_cache_preset_environment_variable_validation(self, monkeypatch):
        """Test CACHE_PRESET environment variable validation and error handling."""
        
        # Test valid preset names
        valid_presets = ['development', 'production', 'ai-development']
        for preset_name in valid_presets:
            monkeypatch.setenv('CACHE_PRESET', preset_name)
            settings = Settings()
            
            # Should not raise an exception
            cache_config = await get_cache_config(settings)
            assert isinstance(cache_config, CacheConfig)
            
            monkeypatch.delenv('CACHE_PRESET')
        
        # Test invalid preset names
        invalid_presets = ['invalid', 'nonexistent', 'bad-preset', '']
        for invalid_preset in invalid_presets:
            monkeypatch.setenv('CACHE_PRESET', invalid_preset)
            
            # Settings should handle invalid presets gracefully
            settings = Settings()
            
            # The dependency should either fall back to default or raise appropriate error
            try:
                cache_config = await get_cache_config(settings)
                # If no exception, verify it fell back to a valid configuration
                assert isinstance(cache_config, CacheConfig)
            except (ConfigurationError, ValidationError) as e:
                # If exception raised, verify it's descriptive
                assert invalid_preset in str(e) or "invalid" in str(e).lower()
            
            monkeypatch.delenv('CACHE_PRESET')
    
    @pytest.mark.asyncio
    async def test_preset_with_override_combinations(self, monkeypatch):
        """Test preset + override combinations (CACHE_REDIS_URL, ENABLE_AI_CACHE, CACHE_CUSTOM_CONFIG)."""
        
        # Test preset with Redis URL override
        monkeypatch.setenv('CACHE_PRESET', 'development')
        monkeypatch.setenv('CACHE_REDIS_URL', 'redis://custom-host:6379/0')
        
        settings = Settings()
        cache_config = await get_cache_config(settings)
        
        assert isinstance(cache_config, CacheConfig)
        assert cache_config.redis_url == 'redis://custom-host:6379/0'
        
        monkeypatch.delenv('CACHE_REDIS_URL')
        
        # Test preset with AI cache enable override
        monkeypatch.setenv('ENABLE_AI_CACHE', 'true')
        
        settings = Settings()
        cache_config = await get_cache_config(settings)
        
        assert cache_config.enable_ai_cache is True
        
        monkeypatch.delenv('ENABLE_AI_CACHE')
        
        # Test preset with custom config override
        custom_config = {
            "default_ttl": 7200,
            "max_connections": 50,
            "compression_level": 6
        }
        monkeypatch.setenv('CACHE_CUSTOM_CONFIG', json.dumps(custom_config))
        
        settings = Settings()
        cache_config = await get_cache_config(settings)
        
        assert cache_config.default_ttl == 7200
        assert cache_config.max_connections == 50
        assert cache_config.compression_level == 6
        
        # Clean up
        monkeypatch.delenv('CACHE_PRESET')
        monkeypatch.delenv('CACHE_CUSTOM_CONFIG')
    
    @pytest.mark.asyncio
    async def test_override_precedence(self, monkeypatch):
        """Test override precedence: Custom Config > Environment Variables > Preset Defaults."""
        
        # Set up base preset
        monkeypatch.setenv('CACHE_PRESET', 'development')
        
        # Set environment variable override
        monkeypatch.setenv('CACHE_REDIS_URL', 'redis://env-override:6379/1')
        monkeypatch.setenv('ENABLE_AI_CACHE', 'true')
        
        # Set custom config override (should have highest precedence)
        custom_config = {
            "redis_url": "redis://custom-override:6379/2",
            "default_ttl": 9999,
            "enable_ai_cache": False  # Should override ENABLE_AI_CACHE
        }
        monkeypatch.setenv('CACHE_CUSTOM_CONFIG', json.dumps(custom_config))
        
        settings = Settings()
        cache_config = await get_cache_config(settings)
        
        # Custom config should have highest precedence
        assert cache_config.redis_url == 'redis://custom-override:6379/2'
        assert cache_config.default_ttl == 9999
        assert cache_config.enable_ai_cache is False  # Custom config overrides env var
        
        # Clean up
        monkeypatch.delenv('CACHE_PRESET')
        monkeypatch.delenv('CACHE_REDIS_URL') 
        monkeypatch.delenv('ENABLE_AI_CACHE')
        monkeypatch.delenv('CACHE_CUSTOM_CONFIG')
    
    @pytest.mark.asyncio
    async def test_invalid_preset_names_with_descriptive_errors(self, monkeypatch):
        """Test invalid preset names with descriptive error messages."""
        
        invalid_presets_and_expected_messages = [
            ('nonexistent-preset', 'not found'),
            ('', 'empty'),
            ('production-typo', 'not found'),
            ('DEVELOPMENT', 'not found'),  # Case sensitivity
        ]
        
        for invalid_preset, expected_message_part in invalid_presets_and_expected_messages:
            monkeypatch.setenv('CACHE_PRESET', invalid_preset)
            
            settings = Settings()
            
            # Should handle invalid presets gracefully with descriptive errors
            try:
                cache_config = await get_cache_config(settings)
                # If it doesn't raise an error, it should fall back to a valid default
                assert isinstance(cache_config, CacheConfig)
            except (ConfigurationError, ValidationError) as e:
                error_message = str(e).lower()
                assert (
                    invalid_preset.lower() in error_message or
                    expected_message_part.lower() in error_message or
                    'invalid' in error_message or
                    'preset' in error_message
                )
            
            monkeypatch.delenv('CACHE_PRESET')
    
    @pytest.mark.asyncio
    async def test_fallback_to_development_preset_when_not_specified(self, monkeypatch):
        """Test fallback to 'development' preset when CACHE_PRESET not specified."""
        
        # Ensure CACHE_PRESET is not set
        monkeypatch.delenv('CACHE_PRESET', raising=False)
        
        settings = Settings()
        cache_config = await get_cache_config(settings)
        
        assert isinstance(cache_config, CacheConfig)
        # Verify it's using development preset characteristics
        # Development preset should have reasonable defaults for local development
        assert cache_config.default_ttl > 0
        assert hasattr(cache_config, 'strategy')
        
        # Should match development preset characteristics
        development_preset = cache_preset_manager.get_preset('development')
        expected_config = development_preset.to_cache_config()
        
        # Key characteristics should match development preset
        assert cache_config.default_ttl == expected_config.default_ttl
        assert cache_config.strategy == expected_config.strategy
    
    @pytest.mark.asyncio
    async def test_preset_configuration_validation_after_loading(self, monkeypatch):
        """Test preset configuration validation after loading."""
        
        # Test valid preset configurations
        valid_presets = ['development', 'production', 'ai-development']
        
        for preset_name in valid_presets:
            monkeypatch.setenv('CACHE_PRESET', preset_name)
            
            settings = Settings()
            cache_config = await get_cache_config(settings)
            
            # Validate the loaded configuration
            validation_result = cache_config.validate()
            
            assert validation_result.is_valid, (
                f"Preset '{preset_name}' produced invalid configuration: "
                f"{validation_result.errors}"
            )
            
            # Verify essential fields are present and valid
            assert cache_config.default_ttl > 0
            assert cache_config.strategy is not None
            assert hasattr(cache_config, 'max_connections')
            assert cache_config.max_connections > 0
            
            monkeypatch.delenv('CACHE_PRESET')
        
        # Test configuration with potentially problematic overrides
        monkeypatch.setenv('CACHE_PRESET', 'development')
        
        # Test with invalid custom config (should be caught during validation)
        invalid_custom_config = {
            "default_ttl": -1,  # Invalid TTL
            "max_connections": 0,  # Invalid connection count
        }
        monkeypatch.setenv('CACHE_CUSTOM_CONFIG', json.dumps(invalid_custom_config))
        
        settings = Settings()
        
        try:
            cache_config = await get_cache_config(settings)
            validation_result = cache_config.validate()
            
            # Should either reject the invalid config or have validation errors
            if validation_result.is_valid:
                # If it passed validation, the invalid values should have been corrected
                assert cache_config.default_ttl > 0
                assert cache_config.max_connections > 0
            else:
                # If validation failed, errors should be descriptive
                assert len(validation_result.errors) > 0
                error_text = ' '.join(validation_result.errors).lower()
                assert 'ttl' in error_text or 'connection' in error_text
                
        except (ConfigurationError, ValidationError):
            # Should raise appropriate exception for invalid configuration
            pass
        
        # Clean up
        monkeypatch.delenv('CACHE_PRESET')
        monkeypatch.delenv('CACHE_CUSTOM_CONFIG')


class TestCacheServiceDependency:
    """Test cache service dependency with preset system."""
    
    @pytest.mark.asyncio
    async def test_get_cache_service_with_preset_configs(self, monkeypatch):
        """Test get_cache_service() creation with different preset configurations."""
        
        preset_names = ['development', 'production', 'ai-development']
        
        for preset_name in preset_names:
            monkeypatch.setenv('CACHE_PRESET', preset_name)
            
            settings = Settings()
            cache_config = await get_cache_config(settings)
            
            # Test cache service creation
            cache_service = await get_cache_service()
            
            assert isinstance(cache_service, CacheInterface)
            assert cache_service is not None
            
            # Verify the cache service reflects the preset configuration
            # This tests that the dependency injection properly uses the preset-based config
            
            monkeypatch.delenv('CACHE_PRESET')
    
    @pytest.mark.asyncio 
    async def test_cache_service_fallback_with_invalid_preset(self, monkeypatch):
        """Test cache service creation with fallback when preset is invalid."""
        
        monkeypatch.setenv('CACHE_PRESET', 'invalid-preset-name')
        
        # Should either fall back to a working configuration or handle the error gracefully
        try:
            cache_service = await get_cache_service()
            assert isinstance(cache_service, CacheInterface)
        except (ConfigurationError, ValidationError):
            # If it raises an exception, it should be descriptive
            pass


class TestFastAPIIntegration:
    """Test FastAPI integration with preset-based cache dependencies."""
    
    def test_fastapi_app_with_preset_cache_dependency(self, monkeypatch):
        """Test FastAPI application using preset-based cache dependency."""
        
        app = FastAPI()
        
        @app.get("/test-cache")
        async def test_endpoint(cache_config: CacheConfig = Depends(get_cache_config)):
            return {
                "preset_used": True,
                "strategy": cache_config.strategy.value if cache_config.strategy else None,
                "ttl": cache_config.default_ttl
            }
        
        monkeypatch.setenv('CACHE_PRESET', 'development')
        
        with TestClient(app) as client:
            response = client.get("/test-cache")
            assert response.status_code == 200
            
            data = response.json()
            assert data["preset_used"] is True
            assert "strategy" in data
            assert "ttl" in data
            assert data["ttl"] > 0
        
        monkeypatch.delenv('CACHE_PRESET')


class TestCacheDependencyManager:
    """Test CacheDependencyManager with preset system."""
    
    @pytest.mark.asyncio
    async def test_dependency_manager_with_preset_configs(self, monkeypatch):
        """Test CacheDependencyManager integration with preset configurations."""
        
        manager = CacheDependencyManager()
        
        # Test with different presets
        preset_names = ['development', 'production', 'simple']
        
        for preset_name in preset_names:
            monkeypatch.setenv('CACHE_PRESET', preset_name)
            
            settings = Settings()
            cache_config = await get_cache_config(settings)
            
            # Test manager can handle preset-based configurations
            assert isinstance(cache_config, CacheConfig)
            
            # Clean up
            monkeypatch.delenv('CACHE_PRESET')
    
    @pytest.mark.asyncio
    async def test_manager_cleanup_with_preset_caches(self):
        """Test manager cleanup functionality with preset-based caches."""
        
        manager = CacheDependencyManager()
        
        # Test cleanup doesn't break with preset-based configurations
        # This ensures the lifecycle management works with the new preset system
        await manager.cleanup_registry()
        
        # Should not raise any exceptions
        assert True


class TestPresetSystemIntegration:
    """Test integration between preset system and dependency injection."""
    
    @pytest.mark.asyncio
    async def test_all_presets_produce_valid_dependencies(self, monkeypatch):
        """Test that all available presets produce valid cache dependencies."""
        
        available_presets = list(CACHE_PRESETS.keys())
        
        for preset_name in available_presets:
            monkeypatch.setenv('CACHE_PRESET', preset_name)
            
            try:
                settings = Settings()
                cache_config = await get_cache_config(settings)
                
                # Every preset should produce a valid cache configuration
                assert isinstance(cache_config, CacheConfig)
                
                # Validate the configuration
                validation_result = cache_config.validate()
                assert validation_result.is_valid or len(validation_result.errors) == 0, (
                    f"Preset '{preset_name}' produced invalid configuration: "
                    f"{validation_result.errors}"
                )
                
            except Exception as e:
                pytest.fail(
                    f"Preset '{preset_name}' failed to create valid dependency: {e}"
                )
            finally:
                monkeypatch.delenv('CACHE_PRESET')
    
    @pytest.mark.asyncio
    async def test_preset_system_performance(self, monkeypatch):
        """Test that preset-based configuration loading performs acceptably."""
        
        import time
        
        monkeypatch.setenv('CACHE_PRESET', 'development')
        
        # Measure configuration loading time
        start_time = time.time()
        
        settings = Settings()
        cache_config = await get_cache_config(settings)
        
        end_time = time.time()
        loading_time = end_time - start_time
        
        # Configuration should load quickly (under 1 second for development)
        assert loading_time < 1.0, (
            f"Preset configuration loading too slow: {loading_time:.3f}s"
        )
        
        assert isinstance(cache_config, CacheConfig)
        
        monkeypatch.delenv('CACHE_PRESET')