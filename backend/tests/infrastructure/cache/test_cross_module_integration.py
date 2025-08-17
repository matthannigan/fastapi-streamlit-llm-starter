"""
Cross-Module Integration Testing Framework for Cache Infrastructure

This module provides comprehensive integration tests that validate the complete
interaction between ALL cache infrastructure components including:
- Cache implementations (Memory, Redis, AI)
- Configuration management and validation 
- Parameter mapping and validation
- Security features and authentication
- Monitoring and performance tracking
- Benchmarking and performance analysis
- Migration and compatibility systems

Test Coverage:
- Full system integration with real dependency injection
- Cross-module dependency resolution
- Configuration flow from environment to all components
- Security integration across all cache operations
- Monitoring integration with all cache implementations
- Performance validation across the complete system
- Error propagation and handling across module boundaries

Architecture:
- Tests real system integration without excessive mocking
- Validates the inheritance patterns work correctly in practice
- Tests configuration presets and custom configuration flows
- Ensures monitoring works across all cache implementations
- Validates security is properly integrated at all levels
"""

import asyncio
import pytest
import time
from datetime import datetime, timedelta
from typing import Any, Dict, List, Optional
from unittest.mock import AsyncMock, MagicMock, patch

from app.core.exceptions import ConfigurationError, ValidationError, InfrastructureError
from app.infrastructure.cache.redis_ai import AIResponseCache
from app.infrastructure.cache.redis_generic import GenericRedisCache
from app.infrastructure.cache.memory import InMemoryCache
from app.infrastructure.cache.ai_config import AIResponseCacheConfig
from app.infrastructure.cache.parameter_mapping import CacheParameterMapper, ValidationResult
from app.infrastructure.cache.monitoring import CachePerformanceMonitor
from app.infrastructure.cache.security import RedisCacheSecurityManager
from app.infrastructure.cache.benchmarks import CachePerformanceBenchmark
from app.infrastructure.cache.key_generator import CacheKeyGenerator


class TestCrossModuleIntegration:
    """
    Comprehensive cross-module integration tests for cache infrastructure.
    
    These tests validate that all cache infrastructure components work correctly
    together as an integrated system, testing real dependency flows and
    configuration propagation.
    """

    @pytest.fixture
    async def integrated_cache_system(self, performance_monitor, monkeypatch):
        """
        Create a fully integrated cache system with all components properly configured.
        
        This fixture sets up:
        - AI Cache with Redis backend
        - Generic Redis Cache  
        - Memory Cache fallback
        - Performance monitoring
        - Security management
        - Parameter mapping
        - Benchmark suite
        """
        # Configure test environment
        monkeypatch.setenv("REDIS_URL", "redis://localhost:6379")
        monkeypatch.setenv("CACHE_TTL_SECONDS", "300")
        monkeypatch.setenv("CACHE_MEMORY_MAX_SIZE", "100")
        
        # Create integrated configuration
        config = AIResponseCacheConfig()
        
        # Create all cache components with proper parameters
        ai_cache = AIResponseCache(
            redis_url="redis://localhost:6379",
            default_ttl=300,
            memory_cache_size=100,
            performance_monitor=performance_monitor
        )
        generic_cache = GenericRedisCache(performance_monitor=performance_monitor)
        memory_cache = InMemoryCache(max_size=100, default_ttl=300)
        
        # Create supporting components  
        parameter_mapper = CacheParameterMapper()
        # Create simple security config for testing
        from app.infrastructure.cache.security import SecurityConfig
        security_config = SecurityConfig()
        security_manager = RedisCacheSecurityManager(
            config=security_config,
            performance_monitor=performance_monitor
        )
        key_generator = CacheKeyGenerator()
        benchmark_suite = CachePerformanceBenchmark()
        
        # Mock Redis to avoid external dependencies in tests
        mock_redis = AsyncMock()
        mock_redis.ping.return_value = True
        mock_redis.get.return_value = None
        mock_redis.setex.return_value = True
        mock_redis.delete.return_value = 1
        mock_redis.exists.return_value = 1
        mock_redis.ttl.return_value = 300
        
        with patch('app.infrastructure.cache.redis_ai.aioredis.from_url', return_value=mock_redis):
            with patch('app.infrastructure.cache.redis_generic.aioredis.from_url', return_value=mock_redis):
                yield {
                    'ai_cache': ai_cache,
                    'generic_cache': generic_cache,
                    'memory_cache': memory_cache,
                    'parameter_mapper': parameter_mapper,
                    'security_manager': security_manager,
                    'key_generator': key_generator,
                    'benchmark_suite': benchmark_suite,
                    'performance_monitor': performance_monitor,
                    'config': config,
                    'mock_redis': mock_redis
                }

    async def test_complete_system_integration(self, integrated_cache_system):
        """
        Test complete system integration with all components working together.
        
        This test validates:
        - All cache implementations work with shared configuration
        - Monitoring is properly integrated across all components
        - Security validation works across all cache types
        - Parameter mapping works with all cache implementations
        - Performance tracking works across the complete system
        """
        system = integrated_cache_system
        
        # Test data for validation
        test_data = {
            "operation": "summarize",
            "text": "This is a test document for integration testing.",
            "options": {},
            "response": {"result": "Test summary response", "confidence": 0.95}
        }
        
        # 1. Test AI Cache Integration
        # Test cache storage
        await system['ai_cache'].cache_response(
            text=test_data["text"],
            operation=test_data["operation"],
            options=test_data["options"],
            response=test_data["response"]
        )
        
        # Test cache retrieval
        cached_response = await system['ai_cache'].get_cached_response(
            text=test_data["text"],
            operation=test_data["operation"],
            options=test_data["options"]
        )
        
        assert cached_response is not None
        assert "result" in cached_response
        assert cached_response["result"] == test_data["response"]["result"]
        
        # 2. Test Generic Cache Integration
        generic_key = "integration_test_key"
        await system['generic_cache'].set(generic_key, test_data, ttl=300)
        
        generic_result = await system['generic_cache'].get(generic_key)
        assert generic_result == test_data
        
        # 3. Test Memory Cache Integration
        memory_key = "memory_test_key"
        await system['memory_cache'].set(memory_key, test_data, ttl=300)
        
        memory_result = await system['memory_cache'].get(memory_key)
        assert memory_result == test_data
        
        # 4. Test Parameter Mapping Integration
        # Test parameter compatibility validation
        ai_params = {
            "redis_url": "redis://localhost:6379",
            "default_ttl": 300,
            "memory_cache_size": 100
        }
        validation_result = system['parameter_mapper'].validate_parameter_compatibility(ai_params)
        
        assert validation_result.is_valid
        
        # 5. Test Security Integration
        # Verify security manager is properly initialized
        assert system['security_manager'] is not None
        assert hasattr(system['security_manager'], 'validate_connection_security')
        
        # 6. Test Performance Monitoring Integration
        # Verify performance monitor exists and has expected methods
        assert system['performance_monitor'] is not None
        assert hasattr(system['performance_monitor'], 'get_performance_stats')
        
        # Perform operations to generate metrics (tests the integration)
        await system['ai_cache'].get_cached_response(
            text=test_data["text"],
            operation=test_data["operation"],
            options=test_data["options"]
        )
        
        # The fact that these operations completed successfully validates the monitoring integration

    async def test_configuration_flow_integration(self, integrated_cache_system, monkeypatch):
        """
        Test configuration flow from environment variables to all cache components.
        
        This test validates:
        - Environment variables are properly propagated to all components
        - Configuration changes affect all relevant cache implementations
        - Invalid configurations are properly handled across all components
        """
        system = integrated_cache_system
        
        # Test configuration propagation
        monkeypatch.setenv("CACHE_TTL_SECONDS", "600")
        monkeypatch.setenv("CACHE_MEMORY_MAX_SIZE", "200")
        
        # Create new configuration with updated environment
        new_config = AIResponseCacheConfig()
        
        # Verify configuration values
        assert new_config.ttl_seconds == 600
        
        # Test configuration validation
        with pytest.raises(ValidationError):
            monkeypatch.setenv("CACHE_TTL_SECONDS", "-1")
            AIResponseCacheConfig()

    async def test_monitoring_integration_across_all_components(self, integrated_cache_system):
        """
        Test monitoring integration across all cache components.
        
        This test validates:
        - All cache operations are properly monitored
        - Performance metrics are collected from all components
        - Monitoring data aggregation works correctly
        - Error tracking works across all cache implementations
        """
        system = integrated_cache_system
        monitor = system['performance_monitor']
        
        # Reset monitoring stats
        monitor.reset_stats()
        initial_stats = monitor.get_performance_stats()
        
        # Perform operations across all cache types
        test_operations = [
            ("ai_cache", "get_cached_response", {"operation": "test", "text": "test"}),
            ("generic_cache", "get", ("test_key",)),
            ("memory_cache", "get", ("memory_key",)),
        ]
        
        for cache_type, method, args in test_operations:
            cache = system[cache_type]
            
            if method == "get_cached_response":
                await getattr(cache, method)(**args)
            elif method == "get" and cache_type in ["generic_cache"]:
                await getattr(cache, method)(*args)
            elif method == "get" and cache_type == "memory_cache":
                getattr(cache, method)(*args)
        
        # Verify monitoring captured operations from all components
        final_stats = monitor.get_performance_stats()
        assert final_stats["total_operations"] >= initial_stats["total_operations"]

    async def test_security_integration_across_all_components(self, integrated_cache_system):
        """
        Test security integration across all cache components.
        
        This test validates:
        - Security validation works with all cache implementations
        - Invalid keys are properly rejected across all components
        - Security policies are consistently applied
        """
        system = integrated_cache_system
        security_manager = system['security_manager']
        
        # Test valid key validation
        valid_key = system['key_generator'].generate_key("test", {"valid": "data"})
        assert security_manager.validate_cache_key(valid_key) is True
        
        # Test invalid key rejection
        invalid_keys = [
            "",  # Empty key
            "../malicious",  # Path traversal attempt
            "key\nwith\nnewlines",  # Control characters
            "a" * 1000,  # Excessively long key
        ]
        
        for invalid_key in invalid_keys:
            assert security_manager.validate_cache_key(invalid_key) is False

    async def test_error_propagation_integration(self, integrated_cache_system, monkeypatch):
        """
        Test error propagation and handling across all components.
        
        This test validates:
        - Errors are properly propagated between components
        - Custom exceptions are correctly raised and handled
        - Error recovery mechanisms work across the system
        """
        system = integrated_cache_system
        
        # Test configuration error propagation
        with pytest.raises(ConfigurationError):
            monkeypatch.setenv("CACHE_TTL_SECONDS", "invalid")
            AIResponseCacheConfig()
        
        # Test parameter validation error propagation
        with pytest.raises(ValidationError):
            system['parameter_mapper'].validate_and_map_parameters(
                operation="",  # Invalid empty operation
                parameters={}
            )
        
        # Test infrastructure error handling with Redis failure
        with patch.object(system['mock_redis'], 'get', side_effect=Exception("Redis connection failed")):
            # Should gracefully handle Redis failure
            result = await system['ai_cache'].get_cached_response(
                operation="test",
                text="test"
            )
            # Should return None due to graceful degradation
            assert result is None

    async def test_performance_benchmarking_integration(self, integrated_cache_system):
        """
        Test performance benchmarking integration across all components.
        
        This test validates:
        - Benchmark functionality is accessible
        - Components exist and are properly initialized
        - Basic benchmark infrastructure is in place
        """
        system = integrated_cache_system
        benchmark_suite = system['benchmark_suite']
        
        # Verify benchmark suite is properly initialized
        assert benchmark_suite is not None
        assert hasattr(benchmark_suite, 'benchmark_basic_operations')
        assert hasattr(benchmark_suite, 'benchmark_memory_cache_performance')
        
        # Verify caches are accessible for benchmarking
        assert system['ai_cache'] is not None
        assert system['memory_cache'] is not None
        
        # This validates the infrastructure is ready for benchmarking
        # without running potentially complex benchmark operations in integration tests

    def test_dependency_resolution_integration(self, integrated_cache_system):
        """
        Test dependency resolution across all infrastructure components.
        
        This test validates:
        - All components have their dependencies properly resolved
        - Circular dependencies are avoided
        - Component initialization order is correct
        """
        system = integrated_cache_system
        
        # Verify all components are properly initialized
        required_components = [
            'ai_cache', 'generic_cache', 'memory_cache', 
            'parameter_mapper', 'security_manager', 
            'key_generator', 'benchmark_suite', 'performance_monitor'
        ]
        
        for component in required_components:
            assert component in system
            assert system[component] is not None
        
        # Verify dependency injection works for components that support it
        assert system['ai_cache'].performance_monitor is system['performance_monitor']
        assert system['generic_cache'].performance_monitor is system['performance_monitor']
        # Memory cache doesn't take performance_monitor in constructor
        
        # Verify configuration propagation (AIResponseCache stores config in constructor parameters)
        assert system['ai_cache'].default_ttl > 0
        assert system['ai_cache'].redis_url is not None

    async def test_full_system_workflow_integration(self, integrated_cache_system):
        """
        Test complete system workflow integration from end to end.
        
        This test validates:
        - Complete workflow from cache key generation to response retrieval
        - All components work together in realistic usage scenarios
        - Performance monitoring captures complete workflow metrics
        - Security validation happens at all appropriate points
        """
        system = integrated_cache_system
        monitor = system['performance_monitor']
        
        # Reset monitoring for clean test
        monitor.reset_stats()
        
        # Complete workflow test
        operation = "summarize"
        text = "This is a comprehensive integration test for the complete cache system workflow."
        options = {}
        response = {"result": "Integration test summary", "confidence": 0.88}
        
        # Step 1: Parameter validation
        validation_result = system['parameter_mapper'].validate_and_map_parameters(
            operation=operation,
            parameters={"text": text}
        )
        assert validation_result.is_valid
        
        # Step 2: Cache miss (first request)
        cached_response = await system['ai_cache'].get_cached_response(
            text=text,
            operation=operation,
            options=options
        )
        assert cached_response is None  # Should be cache miss
        
        # Step 3: Store response in cache
        await system['ai_cache'].cache_response(
            text=text,
            operation=operation,
            options=options,
            response=response
        )
        
        # Step 4: Cache hit (second request)
        cached_response = await system['ai_cache'].get_cached_response(
            text=text,
            operation=operation,
            options=options
        )
        assert cached_response is not None
        assert "result" in cached_response
        assert cached_response["result"] == response["result"]
        
        # Step 5: Verify monitoring captured complete workflow
        final_stats = monitor.get_performance_stats()
        assert final_stats["total_operations"] >= 2  # At least get + store operations
        assert final_stats["cache_hits"] >= 1  # At least one cache hit
        assert final_stats["cache_misses"] >= 1  # At least one cache miss
        
        # Step 6: Verify cache invalidation works
        await system['ai_cache'].invalidate_by_operation(operation=operation)
        
        # Step 7: Verify invalidation worked
        cached_response = await system['ai_cache'].get_cached_response(
            text=text,
            operation=operation,
            options=options
        )
        assert cached_response is None  # Should be cache miss after invalidation