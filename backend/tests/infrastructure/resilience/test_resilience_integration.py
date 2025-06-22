"""
Unit tests for resilience service integration with preset system.

Tests that the resilience service properly integrates with the preset configuration
system and respects operation-specific strategy overrides.
"""

import pytest
from unittest.mock import patch, MagicMock

from app.config import Settings
from app.infrastructure.resilience.orchestrator import AIServiceResilience
from app.infrastructure.resilience.presets import ResilienceStrategy
from app.infrastructure.resilience import ResilienceConfig


class TestResilienceIntegration:
    """Test integration between resilience service and preset system."""
    
    def test_resilience_service_with_preset_config(self):
        """Test resilience service initialization with preset configuration."""
        settings = Settings(resilience_preset="production")
        resilience_service = AIServiceResilience(settings=settings)
        
        # Verify service is initialized properly
        assert resilience_service.settings == settings
        assert len(resilience_service.configurations) >= 1
        
        # Verify base configuration matches production preset
        base_config = settings.get_resilience_config()
        assert base_config.strategy == ResilienceStrategy.CONSERVATIVE
        assert base_config.retry_config.max_attempts == 5
        assert base_config.circuit_breaker_config.failure_threshold == 10
    
    def test_operation_specific_configuration(self):
        """Test that operations get their specific configurations."""
        settings = Settings(resilience_preset="production")
        resilience_service = AIServiceResilience(settings=settings)
        
        # Test QA operation should get CRITICAL strategy in production preset
        qa_config = resilience_service.get_operation_config("qa")
        qa_strategy = settings.get_operation_strategy("qa")
        assert qa_strategy == "critical"
        
        # Test sentiment operation should get AGGRESSIVE strategy in production preset
        sentiment_config = resilience_service.get_operation_config("sentiment")
        sentiment_strategy = settings.get_operation_strategy("sentiment")
        assert sentiment_strategy == "aggressive"
        
        # Test summarize operation should get CONSERVATIVE strategy in production preset
        summarize_config = resilience_service.get_operation_config("summarize")
        summarize_strategy = settings.get_operation_strategy("summarize")
        assert summarize_strategy == "conservative"
    
    def test_operation_resilience_decorator(self):
        """Test the operation-specific resilience decorator."""
        settings = Settings(resilience_preset="development")
        resilience_service = AIServiceResilience(settings=settings)
        
        # Mock function to decorate
        mock_func = MagicMock()
        mock_func.__name__ = "test_func"
        
        # Apply operation-specific resilience decorator
        decorated = resilience_service.with_resilience("sentiment", strategy=None)(mock_func)
        
        # Verify decorator was applied
        assert decorated is not None
        assert callable(decorated)
    
    def test_fallback_to_balanced_strategy(self):
        """Test fallback behavior when invalid strategy is encountered."""
        settings = Settings(resilience_preset="simple")
        resilience_service = AIServiceResilience(settings=settings)
        
        # Mock get_operation_strategy by patching the method directly
        with patch('app.config.Settings.get_operation_strategy', return_value='invalid_strategy'):
            config = resilience_service.get_operation_config("test_operation")
            
            # Should fall back to balanced strategy
            assert config.strategy == ResilienceStrategy.BALANCED
    
    def test_legacy_configuration_integration(self):
        """Test that legacy configuration still works with resilience service."""
        # Create settings with legacy configuration
        settings = Settings(
            circuit_breaker_failure_threshold=8,
            retry_max_attempts=4,
            default_resilience_strategy="conservative"
        )
        
        resilience_service = AIServiceResilience(settings=settings)
        
        # Verify legacy configuration is used
        base_config = settings.get_resilience_config()
        assert base_config.retry_config.max_attempts == 4
        assert base_config.circuit_breaker_config.failure_threshold == 8
        assert base_config.strategy == ResilienceStrategy.CONSERVATIVE
    
    def test_resilience_service_health_check(self):
        """Test resilience service health check functionality."""
        settings = Settings(resilience_preset="simple")
        resilience_service = AIServiceResilience(settings=settings)
        
        # Service should be healthy initially
        assert resilience_service.is_healthy() is True
        
        health_status = resilience_service.get_health_status()
        assert health_status["healthy"] is True
        assert health_status["open_circuit_breakers"] == []
        assert health_status["half_open_circuit_breakers"] == []
        assert health_status["total_circuit_breakers"] == 0
    
    def test_operation_config_caching(self):
        """Test that operation configurations are properly cached."""
        settings = Settings(resilience_preset="production")
        resilience_service = AIServiceResilience(settings=settings)
        
        # Get configuration for same operation multiple times
        config1 = resilience_service.get_operation_config("qa")
        config2 = resilience_service.get_operation_config("qa")
        
        # Should return the same configuration object
        assert config1 is config2
    
    @pytest.mark.parametrize("preset,operation,expected_strategy", [
        ("simple", "summarize", "balanced"),
        ("development", "sentiment", "aggressive"),
        ("development", "qa", "balanced"),
        ("production", "qa", "critical"),
        ("production", "sentiment", "aggressive"),
        ("production", "summarize", "conservative")
    ])
    def test_preset_operation_strategy_mapping(self, preset, operation, expected_strategy):
        """Test that preset-operation strategy mappings work correctly."""
        settings = Settings(resilience_preset=preset)
        resilience_service = AIServiceResilience(settings=settings)
        
        strategy = settings.get_operation_strategy(operation)
        assert strategy == expected_strategy
        
        config = resilience_service.get_operation_config(operation)
        assert config.strategy.value == expected_strategy
    
    def test_custom_config_override_integration(self):
        """Test that custom JSON configuration overrides work with resilience service."""
        import json
        
        custom_config = json.dumps({
            "retry_attempts": 7,
            "circuit_breaker_threshold": 12
        })
        
        settings = Settings(
            resilience_preset="simple",
            resilience_custom_config=custom_config
        )
        
        resilience_service = AIServiceResilience(settings=settings)
        
        # Verify custom overrides are applied
        base_config = settings.get_resilience_config()
        assert base_config.retry_config.max_attempts == 7
        assert base_config.circuit_breaker_config.failure_threshold == 12
    
    def test_resilience_metrics_integration(self):
        """Test that resilience metrics work with preset system."""
        settings = Settings(resilience_preset="development")
        resilience_service = AIServiceResilience(settings=settings)
        
        # Get metrics for an operation
        metrics = resilience_service.get_metrics("test_operation")
        
        # Verify initial state
        assert metrics.total_calls == 0
        assert metrics.successful_calls == 0
        assert metrics.failed_calls == 0
        assert metrics.success_rate == 0.0
        
        # Verify metrics can be retrieved in summary
        all_metrics = resilience_service.get_all_metrics()
        assert "operations" in all_metrics
        assert "circuit_breakers" in all_metrics
        assert "summary" in all_metrics


class TestResilienceConvenienceDecorators:
    """Test the convenience decorator functions."""
    
    def test_with_operation_resilience_decorator(self):
        """Test the with_operation_resilience decorator."""
        from app.infrastructure.resilience import with_operation_resilience
        
        @with_operation_resilience("test_operation")
        async def test_function():
            return "success"
        
        # Verify decorator was applied
        assert callable(test_function)
    
    def test_strategy_specific_decorators(self):
        """Test strategy-specific decorators."""
        from app.infrastructure.resilience import (
            with_aggressive_resilience,
            with_balanced_resilience, 
            with_conservative_resilience,
            with_critical_resilience
        )
        
        @with_aggressive_resilience("test_aggressive")
        async def aggressive_func():
            return "aggressive"
        
        @with_balanced_resilience("test_balanced")
        async def balanced_func():
            return "balanced"
        
        @with_conservative_resilience("test_conservative")
        async def conservative_func():
            return "conservative"
        
        @with_critical_resilience("test_critical")
        async def critical_func():
            return "critical"
        
        # Verify all decorators were applied
        assert callable(aggressive_func)
        assert callable(balanced_func)
        assert callable(conservative_func)
        assert callable(critical_func)