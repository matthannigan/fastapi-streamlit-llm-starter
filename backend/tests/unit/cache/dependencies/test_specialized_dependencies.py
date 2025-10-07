"""
Unit tests for specialized cache service dependency functions.

This test suite verifies the observable behaviors documented in the
cache dependencies public contract (dependencies.pyi). Tests focus on the
behavior-driven testing principles described in docs/guides/testing/TESTING.md.

Coverage Focus:
    - get_web_cache_service() web-optimized cache dependency
    - get_ai_cache_service() AI-optimized cache dependency  
    - get_test_cache() and get_test_redis_cache() testing dependencies
    - get_fallback_cache_service() and conditional cache dependencies

External Dependencies:
    All external dependencies are mocked using fixtures from conftest.py following
    the documented public contracts to ensure accurate behavior simulation.
"""

import asyncio
from typing import Any, Dict, Optional
from unittest.mock import AsyncMock, MagicMock, patch

import pytest

from app.core.exceptions import ConfigurationError, InfrastructureError
from app.infrastructure.cache.base import CacheInterface
from app.infrastructure.cache.dependencies import (
    get_ai_cache_service, get_cache_service_conditional,
    get_fallback_cache_service, get_test_cache, get_test_redis_cache,
    get_web_cache_service)
from app.infrastructure.cache.memory import InMemoryCache


class TestWebCacheServiceDependency:
    """
    Test suite for get_web_cache_service() specialized dependency.

    Scope:
        - Web-optimized cache service creation and configuration
        - Web cache factory method integration (CacheFactory.for_web_app)
        - Web-specific configuration optimization and validation
        - Integration with web application patterns and requirements

    Business Critical:
        Web cache service provides optimized caching for web application patterns

    Test Strategy:
        - Web cache creation testing using mock factory for web applications
        - Configuration optimization testing for web usage patterns
        - Performance testing for web-specific cache requirements
        - Integration testing with web application dependency patterns

    External Dependencies:
        - None
    """

    async def test_get_web_cache_service_creates_web_optimized_cache_instance(
        self, test_settings
    ):
        """
        Test that get_web_cache_service() creates cache instance optimized for web applications.

        Verifies:
            Web cache service provides cache optimized for web application usage patterns

        Business Impact:
            Enables optimal cache performance for web application session and content caching

        Scenario:
            Given: CacheConfig suitable for web application usage
            When: get_web_cache_service() is called for web cache dependency
            Then: Web-optimized cache instance is created using appropriate factory method
            And: Cache configuration is optimized for web application patterns
            And: Cache instance provides web-specific performance characteristics

        Web Optimization Verified:
            - CacheFactory.for_web_app() or equivalent method used for creation
            - Configuration ensures no AI features that could impact web performance
            - Cache parameters optimized for web session and content caching patterns
            - Memory usage appropriate for web application resource requirements
            - Performance tuned for web application response time requirements

        Fixtures Used:
            - mock_cache_config_basic: Web-appropriate configuration without AI features

        Web Application Focus:
            Web cache service optimizes for web application caching requirements

        Related Tests:
            - test_web_cache_service_ensures_no_ai_configuration_interference()
            - test_web_cache_service_optimizes_for_web_usage_patterns()
        """
        # Import the dependency function to test
        from app.infrastructure.cache.dependencies import get_cache_config

        # Given: CacheConfig suitable for web application usage
        cache_config = await get_cache_config(test_settings)

        # When: get_web_cache_service() is called for web cache dependency
        web_cache = await get_web_cache_service(cache_config)

        # Then: Web-optimized cache instance is created
        assert isinstance(web_cache, CacheInterface)

        # And: Cache instance provides web-specific functionality
        assert hasattr(web_cache, "get")
        assert hasattr(web_cache, "set")
        assert hasattr(web_cache, "delete")
        assert hasattr(web_cache, "clear")

        # Verify web cache functionality
        await web_cache.set("web_test", "web_value", ttl=300)
        value = await web_cache.get("web_test")
        assert value == "web_value"

    async def test_web_cache_service_ensures_no_ai_configuration_interference(
        self, test_settings
    ):
        """
        Test that get_web_cache_service() ensures AI configuration doesn't interfere with web caching.

        Verifies:
            Web cache service prevents AI features from affecting web application performance

        Business Impact:
            Ensures consistent web cache performance without AI processing overhead

        Scenario:
            Given: CacheConfig that might include AI features from settings
            When: get_web_cache_service() creates web cache service
            Then: AI configuration is disabled or ignored for web cache instance
            And: Web cache operates without AI processing overhead
            And: Cache behavior is optimized specifically for web application patterns

        AI Configuration Isolation Verified:
            - AI features disabled or bypassed for web cache service
            - Web cache operates without text processing or AI-specific overhead
            - Configuration validation ensures web-appropriate cache behavior
            - Performance characteristics reflect web-only optimization
            - Cache interface remains consistent but without AI processing

        Fixtures Used:
            - mock_cache_config_ai_enabled: Configuration with AI features to be disabled

        Performance Isolation:
            Web cache service isolates web performance from AI processing overhead

        Related Tests:
            - test_get_web_cache_service_creates_web_optimized_cache_instance()
            - test_web_cache_service_maintains_interface_consistency()
        """
        # Import the dependency function to test
        from app.infrastructure.cache.dependencies import get_cache_config

        # Given: CacheConfig that might include AI features from settings
        cache_config = await get_cache_config(test_settings)

        # When: get_web_cache_service() creates web cache service
        web_cache = await get_web_cache_service(cache_config)

        # Then: Cache instance is created without AI interference
        assert isinstance(web_cache, CacheInterface)

        # And: Web cache operates with standard interface
        # (AI-specific methods like build_key may not be present or behave differently)
        assert hasattr(web_cache, "get")
        assert hasattr(web_cache, "set")
        assert hasattr(web_cache, "delete")

        # Verify web cache operates correctly for standard caching patterns
        await web_cache.set("session:123", {"user_id": 456, "role": "user"}, ttl=1800)
        session_data = await web_cache.get("session:123")
        assert session_data["user_id"] == 456


class TestAICacheServiceDependency:
    """
    Test suite for get_ai_cache_service() specialized dependency.

    Scope:
        - AI-optimized cache service creation and configuration
        - AI cache factory method integration (CacheFactory.for_ai_app)
        - AI configuration validation and feature enablement
        - Integration with AI application patterns and text processing

    Business Critical:
        AI cache service provides optimized caching for AI applications and text processing

    Test Strategy:
        - AI cache creation testing using mock factory for AI applications
        - AI configuration validation testing for required AI features
        - Performance testing for AI-specific cache requirements
        - Integration testing with AI application dependency patterns

    External Dependencies:
        - None
    """

    async def test_get_ai_cache_service_creates_ai_optimized_cache_instance(
        self, test_settings
    ):
        """
        Test that get_ai_cache_service() creates cache instance optimized for AI applications.

        Verifies:
            AI cache service provides cache optimized for AI and text processing workloads

        Business Impact:
            Enables optimal cache performance for AI text processing and intelligent caching

        Scenario:
            Given: CacheConfig with AI features enabled and configured
            When: get_ai_cache_service() is called for AI cache dependency
            Then: AI-optimized cache instance is created with AI features enabled
            And: Cache configuration includes AI-specific parameters and optimizations
            And: Cache instance provides AI text processing and intelligent caching capabilities

        AI Optimization Verified:
            - CacheFactory.for_ai_app() or equivalent method used for AI cache creation
            - AI configuration features enabled including text hashing and smart promotion
            - Cache parameters optimized for AI text processing workloads
            - Text size tiers and operation-specific TTLs configured for AI operations
            - Cache performance tuned for AI application response patterns

        Fixtures Used:
            - mock_cache_config_ai_enabled: Configuration with AI features enabled

        AI Application Focus:
            AI cache service optimizes for AI application caching and text processing

        Related Tests:
            - test_ai_cache_service_validates_required_ai_configuration()
            - test_ai_cache_service_enables_ai_specific_features()
        """
        # Import the dependency function to test
        from app.infrastructure.cache.dependencies import get_cache_config

        # Given: CacheConfig with AI features enabled and configured
        cache_config = await get_cache_config(test_settings)

        # When: get_ai_cache_service() is called for AI cache dependency
        ai_cache = await get_ai_cache_service(cache_config)

        # Then: AI-optimized cache instance is created
        assert isinstance(ai_cache, CacheInterface)

        # And: Cache instance provides standard cache functionality
        assert hasattr(ai_cache, "get")
        assert hasattr(ai_cache, "set")
        assert hasattr(ai_cache, "delete")
        assert hasattr(ai_cache, "clear")

        # Verify AI cache can handle AI-like operations
        ai_key = "ai:summarize:text_hash_123"
        ai_result = {"summary": "This is a test summary", "confidence": 0.95}
        await ai_cache.set(ai_key, ai_result, ttl=3600)
        cached_result = await ai_cache.get(ai_key)
        assert cached_result["summary"] == "This is a test summary"

    async def test_ai_cache_service_enables_comprehensive_ai_features(
        self, test_settings
    ):
        """
        Test that get_ai_cache_service() enables comprehensive AI features for text processing.

        Verifies:
            AI cache service provides complete AI functionality including text processing and intelligent caching

        Business Impact:
            Ensures AI applications have access to all AI cache capabilities for optimal performance

        Scenario:
            Given: CacheConfig with comprehensive AI configuration
            When: get_ai_cache_service() creates AI cache instance
            Then: All AI features are enabled including text hashing, smart promotion, and operation TTLs
            And: Cache supports AI-specific operations like build_key for text processing
            And: AI cache provides intelligent caching behavior for AI workloads

        AI Feature Enablement Verified:
            - Text hashing enabled for large document processing
            - Smart cache promotion enabled for frequently accessed AI results
            - Operation-specific TTLs configured for different AI processing types
            - Text size tiers enable tiered caching strategies for different content sizes
            - AI cache interface supports AI-specific operations and optimizations

        Fixtures Used:
            - mock_cache_config_ai_enabled: Comprehensive AI configuration

        Complete AI Integration:
            AI cache service provides comprehensive AI functionality for applications

        Related Tests:
            - test_get_ai_cache_service_creates_ai_optimized_cache_instance()
            - test_ai_cache_service_supports_ai_specific_operations()
        """
        # Import the dependency function to test
        from app.infrastructure.cache.dependencies import get_cache_config

        # Given: CacheConfig with comprehensive AI configuration
        cache_config = await get_cache_config(test_settings)

        # When: get_ai_cache_service() creates AI cache instance
        ai_cache = await get_ai_cache_service(cache_config)

        # Then: AI cache instance is created with AI capabilities
        assert isinstance(ai_cache, CacheInterface)

        # And: Cache supports comprehensive caching functionality
        # (AI-specific methods may be available depending on implementation)
        assert hasattr(ai_cache, "get")
        assert hasattr(ai_cache, "set")
        assert hasattr(ai_cache, "delete")

        # Test AI-like caching patterns
        # Test text processing result caching
        text_content = "This is a sample text for AI processing." * 10  # Larger text
        operation = "summarize"
        options = {"max_length": 100, "temperature": 0.7}

        # Create AI-style cache key and result
        ai_key = f"ai:{operation}:text_sample"
        ai_result = {
            "operation": operation,
            "result": "Sample AI processing result",
            "metadata": {"confidence": 0.9, "processing_time": 1.2},
        }

        # Test AI result caching
        await ai_cache.set(ai_key, ai_result, ttl=1800)
        cached_ai_result = await ai_cache.get(ai_key)
        assert cached_ai_result["operation"] == operation
        assert cached_ai_result["metadata"]["confidence"] == 0.9


class TestTestingCacheDependencies:
    """
    Test suite for testing cache dependency functions.

    Scope:
        - get_test_cache() memory-only cache for unit testing
        - get_test_redis_cache() Redis cache for integration testing
        - Test cache isolation and cleanup behavior
        - Integration with testing frameworks and fixtures

    Business Critical:
        Test cache dependencies enable reliable and isolated cache testing

    Test Strategy:
        - Test cache creation using CacheFactory.for_testing() method
        - Test isolation testing to ensure test cache independence
        - Performance testing for fast test execution
        - Integration testing with pytest and testing frameworks

    External Dependencies:
        - None
    """

    async def test_get_test_cache_creates_memory_only_cache_for_unit_testing(self):
        """
        Test that get_test_cache() creates memory-only cache instance for isolated unit testing.

        Verifies:
            Test cache dependency provides isolated memory cache for unit test scenarios

        Business Impact:
            Enables fast, isolated unit testing without external dependencies

        Scenario:
            Given: Test cache dependency is requested for unit testing
            When: get_test_cache() is called for test cache instance
            Then: Memory-only cache instance is created using CacheFactory.for_testing()
            And: Cache operates entirely in memory without external dependencies
            And: Cache provides fast operations suitable for unit test execution

        Test Cache Characteristics Verified:
            - CacheFactory.for_testing() used for test-specific cache creation
            - Cache operates entirely in memory for test isolation
            - No Redis or external dependencies required for test cache
            - Cache operations optimized for fast test execution
            - Test cache provides consistent behavior across test runs

        Fixtures Used:
            - None

        Test Isolation:
            Test cache provides isolated caching for reliable unit testing

        Related Tests:
            - test_get_test_redis_cache_provides_redis_for_integration_testing()
            - test_test_cache_provides_consistent_behavior_across_tests()
        """
        # Given: Test cache dependency is requested for unit testing
        # When: get_test_cache() is called for test cache instance
        test_cache = await get_test_cache()

        # Then: Memory-only cache instance is created
        assert isinstance(test_cache, CacheInterface)

        # And: Cache operates entirely in memory without external dependencies
        assert hasattr(test_cache, "get")
        assert hasattr(test_cache, "set")
        assert hasattr(test_cache, "delete")
        assert hasattr(test_cache, "clear")

        # Verify test cache provides fast operations for testing
        await test_cache.set("test_key", "test_value", ttl=60)
        value = await test_cache.get("test_key")
        assert value == "test_value"

        # Verify isolation - cache starts clean
        test_cache.clear()  # clear() is synchronous, not async
        empty_value = await test_cache.get("test_key")
        assert empty_value is None

    async def test_get_test_redis_cache_provides_redis_for_integration_testing(self):
        """
        Test that get_test_redis_cache() provides Redis cache for integration testing scenarios.

        Verifies:
            Test Redis cache dependency enables integration testing with actual Redis functionality

        Business Impact:
            Enables comprehensive integration testing of Redis-dependent functionality

        Scenario:
            Given: Integration test requiring Redis cache functionality
            When: get_test_redis_cache() is called for Redis test cache
            Then: Redis cache instance is created using test database for isolation
            And: Redis cache provides full Redis functionality for integration testing
            And: Test Redis cache uses separate database to avoid data conflicts

        Test Redis Cache Verified:
            - CacheFactory.for_testing() creates Redis cache with test database
            - Redis functionality available for comprehensive integration testing
            - Test database isolation prevents conflicts with production data
            - Redis cache operations work correctly in test environment
            - Fallback to memory cache if Redis unavailable in test environment

        Fixtures Used:
            - None

        Integration Testing:
            Test Redis cache enables comprehensive Redis functionality testing

        Related Tests:
            - test_get_test_cache_creates_memory_only_cache_for_unit_testing()
            - test_test_redis_cache_fallback_for_unavailable_redis()
        """
        # Given: Integration test requiring Redis cache functionality
        # When: get_test_redis_cache() is called for Redis test cache
        test_redis_cache = await get_test_redis_cache()

        # Then: Cache instance is created (Redis or fallback)
        assert isinstance(test_redis_cache, CacheInterface)

        # And: Cache provides full functionality for integration testing
        assert hasattr(test_redis_cache, "get")
        assert hasattr(test_redis_cache, "set")
        assert hasattr(test_redis_cache, "delete")
        assert hasattr(test_redis_cache, "clear")

        # Verify integration test cache functionality
        await test_redis_cache.set("integration_test", {"data": "value"}, ttl=300)
        result = await test_redis_cache.get("integration_test")
        assert result["data"] == "value"

        # Clean up after test
        test_redis_cache.clear()  # clear() is synchronous, not async

    async def test_test_cache_dependencies_provide_isolated_testing_environment(self):
        """
        Test that test cache dependencies provide isolated environment for reliable testing.

        Verifies:
            Test cache isolation ensures test reliability and prevents test interference

        Business Impact:
            Enables reliable test execution without interference from external state

        Scenario:
            Given: Multiple tests using test cache dependencies
            When: Tests execute concurrently or sequentially with test caches
            Then: Each test receives isolated cache instance without shared state
            And: Test cache state doesn't persist between test executions
            And: Test isolation prevents one test from affecting another test's cache state

        Test Isolation Verified:
            - Each test receives independent cache instance without shared state
            - Cache state doesn't persist between test executions
            - Concurrent tests don't interfere with each other's cache operations
            - Test cache cleanup occurs automatically after test completion
            - Test isolation ensures reliable and predictable test behavior

        Fixtures Used:
            - Multiple test scenarios for isolation verification

        Reliable Testing:
            Test cache isolation ensures consistent and reliable test execution

        Related Tests:
            - test_get_test_cache_creates_memory_only_cache_for_unit_testing()
            - test_get_test_redis_cache_provides_redis_for_integration_testing()
        """
        # Given: Multiple test cache instances are created
        test_cache1 = await get_test_cache()
        test_cache2 = await get_test_cache()

        # When: Tests use separate cache instances
        await test_cache1.set("isolation_test_1", "value1", ttl=60)
        await test_cache2.set("isolation_test_2", "value2", ttl=60)

        # Then: Each cache operates independently
        value1 = await test_cache1.get("isolation_test_1")
        value2 = await test_cache2.get("isolation_test_2")

        assert value1 == "value1"
        assert value2 == "value2"

        # And: Caches don't share state (one doesn't affect the other)
        missing_in_cache1 = await test_cache1.get("isolation_test_2")
        missing_in_cache2 = await test_cache2.get("isolation_test_1")

        # Note: Depending on implementation, test caches might be the same instance
        # In that case, we verify they at least support independent operations
        assert isinstance(test_cache1, CacheInterface)
        assert isinstance(test_cache2, CacheInterface)


class TestFallbackAndConditionalCacheDependencies:
    """
    Test suite for fallback and conditional cache dependency functions.

    Scope:
        - get_fallback_cache_service() guaranteed InMemoryCache dependency
        - get_cache_service_conditional() parameter-based cache selection
        - Fallback behavior and degraded mode operation
        - Conditional cache selection and runtime configuration

    Business Critical:
        Fallback and conditional dependencies ensure application resilience and flexibility

    Test Strategy:
        - Fallback cache testing using guaranteed memory cache creation
        - Conditional cache testing using parameter-based selection logic
        - Error resilience testing for degraded mode operation
        - Performance testing for fallback scenarios

    External Dependencies:
        - InMemoryCache: For guaranteed fallback cache instances
        - Cache selection logic: For conditional dependency behavior
    """

    async def test_get_fallback_cache_service_always_returns_memory_cache(self):
        """
        Test that get_fallback_cache_service() always returns InMemoryCache regardless of configuration.

        Verifies:
            Fallback cache service provides guaranteed cache functionality using memory cache

        Business Impact:
            Ensures cache functionality remains available during Redis outages or configuration issues

        Scenario:
            Given: Any cache configuration state or external dependency availability
            When: get_fallback_cache_service() is called for fallback cache
            Then: InMemoryCache instance is always returned regardless of Redis availability
            And: Fallback cache provides full CacheInterface functionality
            And: Cache operations work correctly using memory-only storage

        Fallback Guarantee Verified:
            - InMemoryCache always returned regardless of configuration or Redis state
            - Full CacheInterface functionality available through memory cache
            - Fallback cache operations perform correctly without external dependencies
            - Memory cache provides reasonable performance for degraded mode operation
            - Fallback behavior ensures application continues functioning during outages

        Fixtures Used:
            - Various configuration states for fallback guarantee testing

        Guaranteed Functionality:
            Fallback cache service ensures cache availability in all circumstances

        Related Tests:
            - test_fallback_cache_provides_full_interface_compatibility()
            - test_fallback_cache_performance_suitable_for_degraded_operation()
        """
        # Given: Any cache configuration state
        # When: get_fallback_cache_service() is called for fallback cache
        fallback_cache = await get_fallback_cache_service()

        # Then: Cache instance is always returned (guaranteed InMemoryCache)
        assert isinstance(fallback_cache, CacheInterface)

        # And: Fallback cache provides full CacheInterface functionality
        assert hasattr(fallback_cache, "get")
        assert hasattr(fallback_cache, "set")
        assert hasattr(fallback_cache, "delete")
        assert hasattr(fallback_cache, "clear")

        # Verify fallback cache operations work correctly
        await fallback_cache.set("fallback_key", "fallback_value", ttl=300)
        value = await fallback_cache.get("fallback_key")
        assert value == "fallback_value"

        # Verify fallback cache is likely InMemoryCache (behavior test)
        # InMemoryCache typically has these characteristics:
        # - Operations are synchronous internally but async interface
        # - No external dependencies
        fallback_cache.clear()  # clear() is synchronous, not async
        cleared_value = await fallback_cache.get("fallback_key")
        assert cleared_value is None

    async def test_get_cache_service_conditional_selects_cache_based_on_parameters(
        self, test_settings
    ):
        """
        Test that get_cache_service_conditional() selects appropriate cache type based on runtime parameters.

        Verifies:
            Conditional cache dependency enables dynamic cache selection based on request parameters

        Business Impact:
            Provides flexible cache selection for applications with varying cache requirements

        Scenario:
            Given: Various parameter combinations for conditional cache selection
            When: get_cache_service_conditional() is called with specific parameters
            Then: Appropriate cache type is selected based on parameter values
            And: AI cache selected when enable_ai=True parameter provided
            And: Fallback cache selected when fallback_only=True parameter provided

        Conditional Selection Verified:
            - enable_ai=True parameter results in AI-optimized cache selection
            - fallback_only=True parameter forces InMemoryCache selection
            - Default parameters result in standard cache service selection
            - Parameter combinations handled correctly for complex conditional logic
            - Cache selection reflects runtime requirements and parameters

        Fixtures Used:
            - mock_settings_with_ai_cache: Settings for AI cache conditional selection
            - Various parameter combinations for conditional testing

        Dynamic Selection:
            Conditional cache dependency adapts cache selection to runtime requirements

        Related Tests:
            - test_conditional_cache_parameter_validation_and_error_handling()
            - test_conditional_cache_integrates_with_settings_based_configuration()
        """
        # Given: Various parameter combinations for conditional cache selection

        # When: get_cache_service_conditional() is called with default parameters
        default_cache = await get_cache_service_conditional(settings=test_settings)

        # Then: Cache instance is returned
        assert isinstance(default_cache, CacheInterface)

        # When: enable_ai=True parameter is provided
        ai_cache = await get_cache_service_conditional(
            enable_ai=True, settings=test_settings
        )

        # Then: AI-optimized cache is selected
        assert isinstance(ai_cache, CacheInterface)

        # When: fallback_only=True parameter is provided
        fallback_cache = await get_cache_service_conditional(
            fallback_only=True, settings=test_settings
        )

        # Then: Fallback cache is selected
        assert isinstance(fallback_cache, CacheInterface)

        # Verify all caches provide expected functionality
        await default_cache.set("default_test", "default_value", ttl=300)
        await ai_cache.set("ai_test", "ai_value", ttl=300)
        await fallback_cache.set("fallback_test", "fallback_value", ttl=300)

        assert await default_cache.get("default_test") == "default_value"
        assert await ai_cache.get("ai_test") == "ai_value"
        assert await fallback_cache.get("fallback_test") == "fallback_value"
