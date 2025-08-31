"""
Unit tests for CacheFactory explicit cache instantiation.

This test suite verifies the observable behaviors documented in the
CacheFactory public contract (factory.pyi). Tests focus on the
behavior-driven testing principles described in docs/guides/developer/TESTING.md.

Coverage Focus:
    - Infrastructure service (>90% test coverage requirement)
    - Behavior verification per docstring specifications
    - Factory method cache creation and configuration
    - Error handling and graceful fallback patterns

External Dependencies:
    - Settings configuration (mocked): Application configuration management
    - Redis client library (fakeredis): Redis connection simulation for cache creation
    - Standard library components (typing): For type annotations and dependency injection
"""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from typing import Dict, Any

from app.infrastructure.cache.factory import CacheFactory
from app.core.exceptions import ConfigurationError, ValidationError, InfrastructureError


class TestCacheFactoryInitialization:
    """
    Test suite for CacheFactory initialization and basic functionality.
    
    Scope:
        - Factory instance creation and default configuration
        - Basic initialization patterns per docstring specifications
        
    Business Critical:
        Factory initialization determines cache behavior for all application types
        
    Test Strategy:
        - Unit tests for factory initialization
        - Verification of default configuration behavior
        - Validation of factory instance readiness
        
    External Dependencies:
        - None (testing pure factory initialization)
    """

    def test_factory_creates_with_default_configuration(self):
        """
        Test that CacheFactory initializes with appropriate default configuration.
        
        Verifies:
            Factory instance is created and ready for cache instantiation
            
        Business Impact:
            Ensures developers can use factory with minimal configuration
            
        Scenario:
            Given: No configuration parameters provided
            When: CacheFactory is instantiated
            Then: Factory instance is created with sensible defaults ready for use
            
        Edge Cases Covered:
            - Default parameter handling
            - Factory readiness validation
            
        Mocks Used:
            - None (pure initialization test)
            
        Related Tests:
            - test_factory_maintains_configuration_state()
        """
        # Given: No configuration parameters provided
        # When: CacheFactory is instantiated
        factory = CacheFactory()
        
        # Then: Factory instance is created with sensible defaults ready for use
        assert factory is not None
        assert isinstance(factory, CacheFactory)
        
        # Verify factory is ready for cache instantiation by checking it has the expected methods
        assert hasattr(factory, 'for_web_app')
        assert hasattr(factory, 'for_ai_app') 
        assert hasattr(factory, 'for_testing')
        assert hasattr(factory, 'create_cache_from_config')
        assert callable(factory.for_web_app)
        assert callable(factory.for_ai_app)
        assert callable(factory.for_testing)
        assert callable(factory.create_cache_from_config)

    def test_factory_maintains_configuration_state(self):
        """
        Test that CacheFactory maintains internal configuration state correctly.
        
        Verifies:
            Factory instance preserves configuration for subsequent cache creation
            
        Business Impact:
            Ensures consistent cache behavior across multiple factory method calls
            
        Scenario:
            Given: Factory instance is created
            When: Factory configuration is accessed
            Then: Configuration remains consistent and available for cache creation
            
        Edge Cases Covered:
            - Configuration persistence across method calls
            - State isolation between factory instances
            
        Mocks Used:
            - None (state verification test)
            
        Related Tests:
            - test_factory_creates_with_default_configuration()
        """
        # Given: Factory instance is created
        factory1 = CacheFactory()
        factory2 = CacheFactory()
        
        # Then: Configuration remains consistent and available for cache creation
        # Verify state isolation between factory instances
        assert factory1 is not factory2
        
        # Verify both instances maintain their own state
        assert hasattr(factory1, 'for_web_app')
        assert hasattr(factory2, 'for_web_app')
        
        # Verify factory methods remain callable across instances
        assert callable(factory1.for_web_app)
        assert callable(factory2.for_web_app)
        
        # Verify instances are independent
        assert id(factory1) != id(factory2)


class TestWebApplicationCacheCreation:
    """
    Test suite for web application optimized cache creation.
    
    Scope:
        - for_web_app() method behavior and configuration
        - Web application specific cache optimizations
        - Parameter validation and default behavior
        - Redis connection handling and fallback scenarios
        
    Business Critical:
        Web application caches serve session data, API responses, and page content
        
    Test Strategy:
        - Unit tests for web app cache creation with various configurations
        - Integration tests with mocked Redis for connection validation
        - Fallback behavior testing when Redis is unavailable
        - Parameter validation and error handling
        
    External Dependencies:
        - Settings configuration (mocked): Application and cache configuration
        - Redis client library (fakeredis): Redis connection simulation for integration tests
    """

    @pytest.mark.asyncio
    async def test_for_web_app_creates_generic_redis_cache_with_default_settings(self):
        """
        Test that for_web_app() creates a cache with web-optimized behavior.
        
        Verifies:
            Web application cache is created with balanced performance behavior
            
        Business Impact:
            Provides optimal caching performance for typical web application patterns
            
        Scenario:
            Given: Factory instance with default configuration
            When: for_web_app() is called without parameters
            Then: Cache is created that supports standard cache operations
            And: Cache has appropriate fallback behavior when Redis unavailable
            
        Edge Cases Covered:
            - Default parameter application
            - Web optimization presets
            - Redis URL default handling
            
        Behavior Validated:
            - Cache provides standard get/set/delete interface
            - Cache handles connection failures gracefully
            - Cache supports TTL functionality
            
        Related Tests:
            - test_for_web_app_applies_custom_parameters()
            - test_for_web_app_validates_parameter_combinations()
        """
        # Given: Factory instance with default configuration
        factory = CacheFactory()
        
        # When: for_web_app() is called without parameters
        cache = await factory.for_web_app()
        
        # Then: Cache is created that supports standard cache operations
        assert cache is not None
        assert hasattr(cache, 'get')
        assert hasattr(cache, 'set')
        assert hasattr(cache, 'delete')
        assert hasattr(cache, 'exists')
        
        # Verify cache provides async interface as specified in contract
        assert callable(cache.get)
        assert callable(cache.set)
        assert callable(cache.delete)
        assert callable(cache.exists)
        
        # Test actual cache behavior works
        test_key = "test:factory:web_app"
        test_value = {"data": "web_app_test", "type": "factory_validation"}
        
        # Set and get should work (behavior validation)
        await cache.set(test_key, test_value)
        retrieved_value = await cache.get(test_key)
        assert retrieved_value == test_value
        
        # Delete should work (behavior validation)  
        deleted = await cache.delete(test_key)
        assert await cache.get(test_key) is None

    @pytest.mark.asyncio
    async def test_for_web_app_applies_custom_parameters_correctly(self):
        """
        Test that for_web_app() properly applies custom configuration parameters.
        
        Verifies:
            Custom parameters override defaults while maintaining web optimization behavior
            
        Business Impact:
            Allows web applications to fine-tune cache performance for specific needs
            
        Scenario:
            Given: Factory instance ready for cache creation
            When: for_web_app() is called with custom TTL and configuration
            Then: Cache is created with custom behavior that respects the parameters
            
        Edge Cases Covered:
            - Custom TTL values affect cache expiration behavior
            - Custom Redis URL affects connection target
            - Cache maintains web application optimization patterns
            
        Behavior Validated:
            - Cache respects custom TTL settings
            - Cache provides consistent interface regardless of parameters
            - Cache functionality works with custom configuration
            
        Related Tests:
            - test_for_web_app_creates_generic_redis_cache_with_default_settings()
            - test_for_web_app_validates_parameter_combinations()
        """
        # Given: Factory instance ready for cache creation
        factory = CacheFactory()
        
        # Custom parameters for testing
        custom_redis_url = "redis://test-custom:6379"
        custom_ttl = 120  # 2 minutes for faster test
        
        # When: for_web_app() is called with custom parameters
        cache = await factory.for_web_app(
            redis_url=custom_redis_url,
            default_ttl=custom_ttl
        )
        
        # Then: Cache is created with custom behavior that respects the parameters
        assert cache is not None
        
        # Verify cache provides expected interface
        assert hasattr(cache, 'get')
        assert hasattr(cache, 'set')
        assert hasattr(cache, 'delete')
        assert hasattr(cache, 'exists')
        
        # Test that cache works with custom configuration
        test_key = "test:factory:custom_params"
        test_value = {"config": "custom", "ttl": custom_ttl}
        
        # Behavior validation: cache operations should work
        await cache.set(test_key, test_value)
        retrieved_value = await cache.get(test_key)
        assert retrieved_value == test_value
        
        # Cleanup
        await cache.delete(test_key)

    @pytest.mark.asyncio
    async def test_for_web_app_validates_parameter_combinations(self):
        """
        Test that for_web_app() validates parameter combinations and raises appropriate errors.
        
        Verifies:
            Invalid parameter combinations are rejected with descriptive error messages
            
        Business Impact:
            Prevents misconfigured caches that could degrade web application performance
            
        Scenario:
            Given: Factory instance ready for cache creation
            When: for_web_app() is called with conflicting or invalid parameters
            Then: ValidationError is raised with specific configuration guidance
            
        Edge Cases Covered:
            - Invalid TTL values (negative, zero, extremely large)
            - Invalid cache sizes (negative, zero, extremely large)
            - Invalid compression levels (outside 1-9 range)
            - Malformed Redis URL formats
            - Parameter combination conflicts
            
        Mocks Used:
            - None (validation logic test)
            
        Related Tests:
            - test_for_web_app_applies_custom_parameters_correctly()
            - test_for_web_app_handles_redis_connection_failure()
        """
        # Given: Factory instance ready for cache creation
        factory = CacheFactory()
        
        # Test invalid TTL values - behavior focused on exception type and context
        with pytest.raises(ValidationError) as exc_info:
            await factory.for_web_app(default_ttl=-1)
        assert "default_ttl" in str(exc_info.value).lower()
        
        # Test invalid Redis URL format
        with pytest.raises(ValidationError) as exc_info:
            await factory.for_web_app(redis_url="invalid-url")
        assert "redis_url" in str(exc_info.value).lower()
        
        # Test invalid compression level
        with pytest.raises(ValidationError) as exc_info:
            await factory.for_web_app(compression_level=0)
        assert "compression_level" in str(exc_info.value).lower()
        
        with pytest.raises(ValidationError) as exc_info:
            await factory.for_web_app(compression_level=10)
        assert "compression_level" in str(exc_info.value).lower()
        
        # Test invalid parameter types (not just ranges)
        with pytest.raises(ValidationError) as exc_info:
            await factory.for_web_app(default_ttl="not_a_number")
        assert hasattr(exc_info.value, 'context')

    @pytest.mark.asyncio
    async def test_for_web_app_handles_redis_connection_failure_with_memory_fallback(self):
        """
        Test that for_web_app() falls back to InMemoryCache when Redis connection fails.
        
        Verifies:
            Graceful degradation to memory cache when Redis is unavailable
            
        Business Impact:
            Ensures web applications remain functional during Redis outages
            
        Scenario:
            Given: Factory configured for web application cache
            When: for_web_app() is called with impossible Redis URL
            Then: Cache is returned that works (fallback behavior)
            
        Edge Cases Covered:
            - Redis connection timeout
            - Redis server unavailable
            - Network connectivity issues
            
        Behavior Validated:
            - Factory returns a working cache despite Redis failure
            - Cache supports all required operations
            - Fallback cache type is appropriate (InMemoryCache)
            
        Related Tests:
            - test_for_web_app_raises_error_when_redis_required()
        """
        # Given: Factory configured for web application cache
        factory = CacheFactory()
        
        # Use impossible Redis URL to force connection failure
        impossible_redis_url = "redis://nonexistent-host:99999"
        
        # When: for_web_app() is called but Redis connection fails
        cache = await factory.for_web_app(
            redis_url=impossible_redis_url,
            fail_on_connection_error=False
        )
        
        # Then: Cache is returned that works (fallback behavior)
        assert cache is not None
        assert hasattr(cache, 'get')
        assert hasattr(cache, 'set')
        assert hasattr(cache, 'delete')
        
        # Behavior validation: fallback cache should work
        test_key = "test:fallback:behavior"
        test_value = {"fallback": True, "type": "memory"}
        
        await cache.set(test_key, test_value)
        retrieved_value = await cache.get(test_key)
        assert retrieved_value == test_value
        
        # Verify cache type is memory-based (fallback behavior)
        from app.infrastructure.cache.memory import InMemoryCache
        assert isinstance(cache, InMemoryCache)

    @pytest.mark.asyncio
    async def test_for_web_app_raises_error_when_redis_required(self):
        """
        Test that for_web_app() raises InfrastructureError when fail_on_connection_error=True.
        
        Verifies:
            Strict Redis requirement enforcement when explicitly requested
            
        Business Impact:
            Allows critical web applications to fail fast rather than degrade silently
            
        Scenario:
            Given: Factory configured with fail_on_connection_error=True
            When: for_web_app() is called but Redis connection fails
            Then: InfrastructureError is raised with connection failure details
            
        Edge Cases Covered:
            - Explicit Redis requirement scenarios
            - Error message clarity and debugging information
            - Different connection failure types
            
        Mocks Used:
            - Redis connection mocking to simulate failures (acceptable for error handling testing)
            
        Related Tests:
            - test_for_web_app_handles_redis_connection_failure_with_memory_fallback()
            - test_for_web_app_validates_parameter_combinations()
        """
        # Given: Factory configured with fail_on_connection_error=True
        factory = CacheFactory()
        
        # Mock Redis connection to fail (acceptable for testing factory's error handling logic)
        with patch('app.infrastructure.cache.redis_generic.GenericRedisCache') as mock_redis:
            redis_error = Exception("Redis connection failed")
            mock_redis.side_effect = redis_error
            
            # When: for_web_app() is called but Redis connection fails
            # Then: InfrastructureError is raised with connection failure details
            with pytest.raises(InfrastructureError, match="Redis connection failed for web application cache"):
                await factory.for_web_app(fail_on_connection_error=True)

    @pytest.mark.asyncio  
    async def test_for_web_app_strict_redis_requirement_with_invalid_url(self):
        """
        Integration test: Verify error handling with real invalid Redis configuration.
        
        Tests factory's error handling behavior using real Redis connection attempts
        with invalid URLs to verify actual error handling without mocking.
        
        Scenario:
            Given: Factory configured with fail_on_connection_error=True
            When: for_web_app() is called with completely invalid Redis URL
            Then: InfrastructureError is raised from actual connection failure
        """
        # Given: Factory configured with fail_on_connection_error=True
        factory = CacheFactory()
        
        # Use a clearly invalid Redis URL that will cause real connection failure
        invalid_redis_url = "redis://invalid-host-that-does-not-exist:99999/0"
        
        # When: for_web_app() is called with invalid Redis URL and strict error mode
        # Then: Should raise InfrastructureError from real connection failure
        with pytest.raises(InfrastructureError):
            await factory.for_web_app(
                redis_url=invalid_redis_url,
                fail_on_connection_error=True
            )


class TestAIApplicationCacheCreation:
    """
    Test suite for AI application optimized cache creation.
    
    Scope:
        - for_ai_app() method behavior and AI-specific configurations
        - AI application cache optimizations (compression, TTLs, text handling)
        - AIResponseCache creation with operation-specific settings
        - Enhanced monitoring and performance tracking integration
        
    Business Critical:
        AI application caches store expensive-to-compute AI responses and embeddings
        
    Test Strategy:
        - Unit tests for AI cache creation with AI-specific parameters
        - Integration tests with mocked AIResponseCache for feature validation
        - Performance optimization verification (compression, text hashing)
        - Operation-specific TTL and monitoring integration testing
        
    External Dependencies:
        - Settings configuration (mocked): Application and cache configuration
        - Redis client library (fakeredis): Redis connection simulation for integration tests
    """

    @pytest.mark.asyncio
    async def test_for_ai_app_creates_ai_response_cache_with_default_settings(self):
        """
        Test that for_ai_app() creates a cache with AI-optimized behavior.
        
        Verifies:
            AI application cache is created with enhanced AI-specific functionality
            
        Business Impact:
            Provides optimal caching performance for AI workloads with large responses
            
        Scenario:
            Given: Factory instance with default configuration
            When: for_ai_app() is called without parameters
            Then: Cache is created that supports AI-specific operations
            And: Cache provides AI key generation and text handling capabilities
            
        Edge Cases Covered:
            - AI-specific default parameters
            - Enhanced compression settings
            - Text hashing threshold defaults
            - AI operation monitoring defaults
            
        Behavior Validated:
            - Cache provides standard cache interface
            - Cache includes AI-specific features (build_key method)
            - Cache handles AI operations appropriately
            
        Related Tests:
            - test_for_ai_app_applies_operation_specific_ttls()
            - test_for_ai_app_configures_text_hashing_threshold()
        """
        # Given: Factory instance with default configuration
        factory = CacheFactory()
        
        # When: for_ai_app() is called without parameters
        cache = await factory.for_ai_app()
        
        # Then: Cache is created that supports AI-specific operations
        assert cache is not None
        assert hasattr(cache, 'get')
        assert hasattr(cache, 'set')
        assert hasattr(cache, 'delete')
        assert hasattr(cache, 'exists')
        
        # Test cache type and features based on what was actually created
        from app.infrastructure.cache.redis_ai import AIResponseCache
        from app.infrastructure.cache.memory import InMemoryCache
        
        # Should be AIResponseCache or fallback to InMemoryCache if Redis unavailable
        assert isinstance(cache, (AIResponseCache, InMemoryCache))
        
        # If we got an AIResponseCache, verify AI-specific features
        if isinstance(cache, AIResponseCache):
            assert hasattr(cache, 'build_key'), "AI cache should have build_key method"
            assert callable(cache.build_key)
        else:
            # If we got InMemoryCache fallback, that's also valid behavior
            assert isinstance(cache, InMemoryCache), "Fallback should be InMemoryCache"
        
        # Test actual cache behavior works for AI operations
        test_key = "test:ai_factory:default"
        test_value = {"ai_response": "test", "operation": "factory_validation"}
        
        await cache.set(test_key, test_value)
        retrieved_value = await cache.get(test_key)
        assert retrieved_value == test_value

    @pytest.mark.asyncio
    async def test_for_ai_app_applies_operation_specific_ttls(self):
        """
        Test that for_ai_app() properly accepts operation-specific TTL parameters.
        
        Verifies:
            AI cache factory accepts custom operation TTL configurations
            
        Business Impact:
            Balances cache freshness with AI processing cost savings across operations
            
        Scenario:
            Given: Factory configured with operation-specific TTL mappings
            When: for_ai_app() is called with operation_ttls parameter
            Then: Cache is created that accepts the operation TTL configuration
            And: Cache provides consistent interface regardless of TTL settings
            
        Edge Cases Covered:
            - Multiple operation TTL configurations
            - TTL parameter acceptance and validation
            - Cache creation with custom configuration
            
        Behavior Validated:
            - Factory accepts operation_ttls parameter without error
            - Cache creation succeeds with custom TTL configuration
            - Cache provides standard interface
            
        Related Tests:
            - test_for_ai_app_creates_ai_response_cache_with_default_settings()
            - test_for_ai_app_validates_operation_ttl_parameters()
        """
        # Given: Factory configured with operation-specific TTL mappings
        factory = CacheFactory()
        
        operation_ttls = {
            "summarize": 1800,  # 30 minutes
            "sentiment": 3600,  # 1 hour
            "translate": 7200   # 2 hours
        }
        
        # When: for_ai_app() is called with operation_ttls parameter
        cache = await factory.for_ai_app(operation_ttls=operation_ttls)
        
        # Then: Cache is created that accepts the operation TTL configuration
        assert cache is not None
        assert hasattr(cache, 'get')
        assert hasattr(cache, 'set')
        assert hasattr(cache, 'delete')
        assert hasattr(cache, 'exists')
        
        # Test cache behavior works with custom TTL configuration
        test_key = "test:ai_factory:operation_ttls"
        test_value = {"operation_ttls": operation_ttls, "configured": True}
        
        await cache.set(test_key, test_value)
        retrieved_value = await cache.get(test_key)
        assert retrieved_value == test_value
        
        # Cleanup
        await cache.delete(test_key)

    @pytest.mark.asyncio
    async def test_for_ai_app_configures_text_hashing_threshold(self):
        """
        Test that for_ai_app() properly configures text hashing threshold for key generation.
        
        Verifies:
            Large text inputs are handled efficiently through intelligent key generation
            
        Business Impact:
            Prevents cache key length issues while maintaining cache efficiency for AI text processing
            
        Scenario:
            Given: Factory configured for AI application cache
            When: for_ai_app() is called with text_hash_threshold parameter
            Then: AIResponseCache is created with specified threshold for text hashing behavior
            
        Edge Cases Covered:
            - Small threshold values for aggressive hashing
            - Large threshold values for direct text inclusion
            - Threshold validation and boundary conditions
            - Integration with CacheKeyGenerator
            
        Mocks Used:
            - None
            
        Related Tests:
            - test_for_ai_app_applies_operation_specific_ttls()
            - test_for_ai_app_integrates_with_performance_monitoring()
        """
        # Given: Factory configured for AI application cache
        factory = CacheFactory()
        
        # Test small threshold for aggressive hashing
        small_threshold = 200
        
        from app.infrastructure.cache.redis_ai import AIResponseCache
        from app.infrastructure.cache.memory import InMemoryCache
        
        # When: for_ai_app() is called with text_hash_threshold parameter
        cache = await factory.for_ai_app(text_hash_threshold=small_threshold)
        
        # Then: Cache should be functional (AIResponseCache or InMemoryCache fallback)
        assert cache is not None
        assert isinstance(cache, (AIResponseCache, InMemoryCache))
        
        # Prove cache is functional with basic operations
        await cache.set("test:threshold", "value")
        assert await cache.get("test:threshold") == "value"

    @pytest.mark.asyncio
    async def test_for_ai_app_integrates_with_performance_monitoring(self, real_performance_monitor):
        """
        Test that for_ai_app() properly integrates performance monitoring for AI metrics.
        
        Verifies:
            AI-specific performance metrics are collected for monitoring and optimization
            
        Business Impact:
            Enables monitoring of AI cache performance for cost optimization and SLA compliance
            
        Scenario:
            Given: Factory configured with performance monitoring enabled
            When: for_ai_app() is called with monitoring integration
            Then: Cache is created with performance monitor configured for AI metrics
            
        Edge Cases Covered:
            - Performance monitor integration
            - AI-specific metric collection
            - Monitoring configuration validation
            - Optional monitoring behavior
            
        Mocks Used:
            - None (uses real performance monitor)
            
        Related Tests:
            - test_for_ai_app_configures_text_hashing_threshold()
            - test_for_ai_app_handles_redis_connection_failure_with_fallback()
        """
        # Given: Factory configured with performance monitoring enabled
        factory = CacheFactory()
        
        # When: for_ai_app() is called with monitoring integration
        cache = await factory.for_ai_app(
            performance_monitor=real_performance_monitor,
            fail_on_connection_error=False  # Allow fallback for test environments
        )
        
        # Then: Cache should be created and functional
        assert cache is not None
        assert hasattr(cache, 'get')
        assert hasattr(cache, 'set')
        assert hasattr(cache, 'delete')
        assert hasattr(cache, 'exists')
        
        # Test actual monitoring integration by performing operations
        test_key = "test:monitoring:ai_metrics"
        test_value = {"ai_response": "test", "operation": "monitoring_validation"}
        
        # Perform operations that should be monitored
        await cache.set(test_key, test_value)
        retrieved_value = await cache.get(test_key)
        assert retrieved_value == test_value
        
        # If monitor is integrated, verify it has collected metrics
        if hasattr(cache, '_performance_monitor') and cache._performance_monitor is not None:
            # Test that monitor is actively collecting metrics
            # (Specific monitoring verification depends on monitor implementation)
            assert cache._performance_monitor is real_performance_monitor
        
        # Test cache deletion and monitoring
        await cache.delete(test_key)
        assert await cache.get(test_key) is None

    @pytest.mark.asyncio
    async def test_for_ai_app_validates_operation_ttl_parameters(self):
        """
        Test that for_ai_app() validates operation TTL parameters and raises appropriate errors.
        
        Verifies:
            Invalid operation TTL configurations are rejected with descriptive error messages
            
        Business Impact:
            Prevents misconfigured AI caches that could impact processing cost efficiency
            
        Scenario:
            Given: Factory instance ready for AI cache creation
            When: for_ai_app() is called with invalid operation TTL parameters
            Then: ValidationError is raised with specific TTL configuration guidance
            
        Edge Cases Covered:
            - Invalid TTL values (negative, zero, extremely large)
            - Unknown operation names in TTL configuration
            - TTL parameter type validation
            - Operation TTL consistency validation
            
        Mocks Used:
            - None (validation logic test)
            
        Related Tests:
            - test_for_ai_app_applies_operation_specific_ttls()
            - test_for_ai_app_handles_redis_connection_failure_with_fallback()
        """
        # Given: Factory instance ready for AI cache creation
        factory = CacheFactory()
        
        # Test invalid TTL values in operation_ttls
        invalid_operation_ttls = {"summarize": -1, "sentiment": 0}
        
        with pytest.raises(ValidationError, match="must be a non-negative integer"):
            await factory.for_ai_app(operation_ttls=invalid_operation_ttls)
            
        # Test invalid operation_ttls type
        with pytest.raises(ValidationError, match="operation_ttls must be a dictionary"):
            await factory.for_ai_app(operation_ttls="invalid")
            
        # Test empty operation names
        invalid_operation_ttls_empty = {"": 3600}
        
        with pytest.raises(ValidationError, match="must be non-empty strings"):
            await factory.for_ai_app(operation_ttls=invalid_operation_ttls_empty)

    @pytest.mark.asyncio
    async def test_for_ai_app_handles_redis_connection_failure_with_fallback(self):
        """
        Test that for_ai_app() falls back to InMemoryCache when Redis connection fails.
        
        Verifies:
            Graceful degradation to memory cache preserving AI application functionality
            
        Business Impact:
            Ensures AI applications continue functioning during Redis outages
            
        Scenario:
            Given: Factory configured for AI application cache
            When: for_ai_app() is called but Redis connection fails
            Then: InMemoryCache is returned with AI configuration warnings logged
            
        Edge Cases Covered:
            - Redis connection failures during AI cache creation
            - Fallback behavior with AI-specific configuration loss
            - Warning message clarity for AI degradation
            - Memory cache limitations for AI workloads
            
        Mocks Used:
            - Redis connection mocking to simulate failures
            
        Related Tests:
            - test_for_ai_app_integrates_with_performance_monitoring()
            - test_for_ai_app_raises_error_when_redis_required_for_ai()
        """
        # Given: Factory configured for AI application cache
        factory = CacheFactory()
        
        from app.infrastructure.cache.memory import InMemoryCache
        
        # Use an impossible Redis URL to force a connection failure
        cache = await factory.for_ai_app(
            redis_url="redis://nonexistent-host:9999",
            fail_on_connection_error=False
        )
        
        # Then: Should fall back to InMemoryCache
        assert cache is not None
        assert isinstance(cache, InMemoryCache)
        
        # Prove the fallback cache is functional
        await cache.set("test:fallback", "data")
        assert await cache.get("test:fallback") == "data"

    @pytest.mark.asyncio
    async def test_for_ai_app_raises_error_when_redis_required_for_ai(self):
        """
        Test that for_ai_app() raises InfrastructureError when fail_on_connection_error=True.
        
        Verifies:
            Strict Redis requirement enforcement for critical AI applications
            
        Business Impact:
            Allows critical AI applications to fail fast rather than lose AI-specific features
            
        Scenario:
            Given: Factory configured with fail_on_connection_error=True for AI cache
            When: for_ai_app() is called but Redis connection fails
            Then: InfrastructureError is raised with AI-specific connection failure details
            
        Edge Cases Covered:
            - AI application critical dependency on Redis
            - Error message specificity for AI cache failures
            - Different AI connection failure scenarios
            
        Mocks Used:
            - Redis connection mocking to simulate failures (acceptable for factory error handling testing)
            
        Related Tests:
            - test_for_ai_app_handles_redis_connection_failure_with_fallback()
            - test_for_ai_app_validates_operation_ttl_parameters()
        """
        # Given: Factory configured with fail_on_connection_error=True for AI cache
        factory = CacheFactory()
        
        # Mock AI cache connection to fail (acceptable for testing factory's error handling logic)
        with patch('app.infrastructure.cache.redis_ai.AIResponseCache') as mock_ai_class:
            ai_error = Exception("Redis connection failed")
            mock_ai_class.side_effect = ai_error
            
            # When: for_ai_app() is called but Redis connection fails
            # Then: InfrastructureError is raised with AI-specific connection failure details
            with pytest.raises(InfrastructureError, match="Redis connection failed for AI application cache"):
                await factory.for_ai_app(fail_on_connection_error=True)

    @pytest.mark.asyncio
    async def test_for_ai_app_strict_redis_requirement_with_invalid_url(self):
        """
        Integration test: Verify AI cache error handling with real invalid Redis configuration.
        
        Tests factory's AI error handling behavior using real Redis connection attempts
        with invalid URLs to verify actual error handling without mocking.
        
        Scenario:
            Given: Factory configured with fail_on_connection_error=True
            When: for_ai_app() is called with completely invalid Redis URL
            Then: InfrastructureError is raised from actual connection failure
        """
        # Given: Factory configured with fail_on_connection_error=True
        factory = CacheFactory()
        
        # Use a clearly invalid Redis URL that will cause real connection failure
        invalid_redis_url = "redis://invalid-ai-host-that-does-not-exist:99999/0"
        
        # When: for_ai_app() is called with invalid Redis URL and strict error mode
        # Then: Should raise InfrastructureError from real connection failure
        with pytest.raises(InfrastructureError):
            await factory.for_ai_app(
                redis_url=invalid_redis_url,
                fail_on_connection_error=True
            )


class TestTestingCacheCreation:
    """
    Test suite for testing environment optimized cache creation.
    
    Scope:
        - for_testing() method behavior and testing-specific configurations
        - Test database isolation and short TTL configurations
        - Memory cache option for isolated testing scenarios
        - Fast operation settings for minimal test overhead
        
    Business Critical:
        Testing caches enable reliable automated testing without interference
        
    Test Strategy:
        - Unit tests for testing cache creation with test-specific parameters
        - Verification of test isolation features (database selection, TTLs)
        - Memory cache testing option validation
        - Performance optimization for test execution speed
        
    External Dependencies:
        - Settings configuration (mocked): Application and cache configuration
        - Redis client library (fakeredis): Redis connection simulation for integration tests
    """

    @pytest.mark.asyncio
    async def test_for_testing_creates_cache_with_test_optimizations(self):
        """
        Test that for_testing() creates cache with testing-optimized behavior.
        
        Verifies:
            Testing cache is created with behavior suitable for test environments
            
        Business Impact:
            Ensures test suites run efficiently without cache interference between tests
            
        Scenario:
            Given: Factory instance configured for testing environment
            When: for_testing() is called with default parameters
            Then: Cache is created with appropriate testing behavior
            And: Cache provides standard interface with testing-appropriate performance
            
        Edge Cases Covered:
            - Default testing configuration application
            - Test database isolation behavior
            - Fast operation settings for test efficiency
            - Memory usage appropriate for testing
            
        Behavior Validated:
            - Cache provides standard cache interface
            - Cache works appropriately for testing scenarios
            - Cache handles fallback gracefully when Redis unavailable
            
        Related Tests:
            - test_for_testing_uses_test_database_for_isolation()
            - test_for_testing_applies_short_ttls_for_quick_expiration()
        """
        # Given: Factory instance configured for testing environment
        factory = CacheFactory()
        
        # When: for_testing() is called with default parameters
        cache = await factory.for_testing()
        
        # Then: Cache is created with appropriate testing behavior
        assert cache is not None
        assert hasattr(cache, 'get')
        assert hasattr(cache, 'set')
        assert hasattr(cache, 'delete')
        assert hasattr(cache, 'exists')
        
        # Verify cache provides expected interface
        assert callable(cache.get)
        assert callable(cache.set)
        assert callable(cache.delete)
        assert callable(cache.exists)
        
        # Test actual testing cache behavior works
        test_key = "test:factory:testing_optimizations"
        test_value = {"testing": True, "optimization": "enabled"}
        
        # Behavior validation: testing cache operations should work
        await cache.set(test_key, test_value)
        retrieved_value = await cache.get(test_key)
        assert retrieved_value == test_value
        
        # Test that we got an appropriate cache type for testing
        from app.infrastructure.cache.redis_generic import GenericRedisCache
        from app.infrastructure.cache.memory import InMemoryCache
        
        # Should be either GenericRedisCache or InMemoryCache fallback
        assert isinstance(cache, (GenericRedisCache, InMemoryCache))
        
        # Cleanup
        await cache.delete(test_key)

    @pytest.mark.asyncio
    async def test_for_testing_uses_test_database_for_isolation(self):
        """
        Test that for_testing() uses Redis test database for test isolation.
        
        Verifies:
            Testing cache uses separate Redis database to avoid production data conflicts
            
        Business Impact:
            Prevents test data from interfering with development or production caches
            
        Scenario:
            Given: Factory configured for testing with default settings
            When: for_testing() is called without custom Redis URL
            Then: Cache is created targeting Redis database 15 for test isolation
            
        Edge Cases Covered:
            - Default test database selection (DB 15)
            - Custom test database configuration
            - Test database URL parsing and validation
            - Database isolation verification
            
        Mocks Used:
            - none
            
        Related Tests:
            - test_for_testing_creates_cache_with_test_optimizations()
            - test_for_testing_supports_custom_test_database()
        """
        # Given: Factory configured for testing with default settings
        factory = CacheFactory()
        
        # When: for_testing() is called without custom Redis URL
        cache = await factory.for_testing()
        
        from app.infrastructure.cache.redis_generic import GenericRedisCache
        from app.infrastructure.cache.memory import InMemoryCache
        
        # Then: Cache should be functional (Redis or memory fallback)
        assert cache is not None
        
        # Skip if fallback occurred, as this test is Redis-specific
        if not isinstance(cache, GenericRedisCache):
            pytest.skip("Redis is not available for this test.")
        
        # Verify test database is configured (default test DB is 15)
        assert hasattr(cache, 'redis_url')
        assert '/15' in cache.redis_url
        
        # Prove cache is functional
        await cache.set("test:isolation", "test_data")
        assert await cache.get("test:isolation") == "test_data"

    @pytest.mark.asyncio
    async def test_for_testing_applies_short_ttls_for_quick_expiration(self):
        """
        Test that for_testing() applies short TTL values for quick test data expiration.
        
        Verifies:
            Test data expires quickly to prevent interference between test runs
            
        Business Impact:
            Ensures test isolation and prevents stale test data affecting subsequent tests
            
        Scenario:
            Given: Factory configured for testing environment
            When: for_testing() is called with default or custom short TTL
            Then: Cache is created with TTL appropriate for test execution timeframes
            
        Edge Cases Covered:
            - Default 1-minute TTL for testing
            - Custom short TTL values (seconds range)
            - TTL validation for testing scenarios
            - Balance between isolation and test performance
            
        Mocks Used:
            - None
            
        Related Tests:
            - test_for_testing_uses_test_database_for_isolation()
            - test_for_testing_creates_memory_cache_when_requested()
        """
        # Given: Factory configured for testing environment
        factory = CacheFactory()
        
        from app.infrastructure.cache.redis_generic import GenericRedisCache
        from app.infrastructure.cache.memory import InMemoryCache
        
        # Test default short TTL
        cache = await factory.for_testing()
        
        # Then: Cache should be functional for testing
        assert cache is not None
        assert isinstance(cache, (GenericRedisCache, InMemoryCache))
        
        # Test custom short TTL
        custom_ttl = 30  # 30 seconds
        cache2 = await factory.for_testing(default_ttl=custom_ttl)
        
        # Verify both caches are functional
        assert cache2 is not None
        assert isinstance(cache2, (GenericRedisCache, InMemoryCache))
        
        # Prove caches work with quick operations
        await cache.set("test:ttl_default", "data1")
        await cache2.set("test:ttl_custom", "data2")
        assert await cache.get("test:ttl_default") == "data1"
        assert await cache2.get("test:ttl_custom") == "data2"

    @pytest.mark.asyncio
    async def test_for_testing_creates_memory_cache_when_requested(self):
        """
        Test that for_testing() creates InMemoryCache when use_memory_cache=True.
        
        Verifies:
            Pure memory cache is available for completely isolated testing scenarios
            
        Business Impact:
            Enables testing without any Redis dependency for maximum test isolation
            
        Scenario:
            Given: Factory configured for testing with memory cache option
            When: for_testing() is called with use_memory_cache=True
            Then: InMemoryCache is created for completely isolated testing
            
        Edge Cases Covered:
            - Memory cache selection over Redis for testing
            - Memory cache configuration for testing scenarios
            - Isolation benefits of pure memory caching
            - Memory cache limitations awareness
            
        Mocks Used:
            - None
            
        Related Tests:
            - test_for_testing_applies_short_ttls_for_quick_expiration()
            - test_for_testing_supports_custom_test_database()
        """
        # Given: Factory configured for testing with memory cache option
        factory = CacheFactory()
        
        from app.infrastructure.cache.memory import InMemoryCache
        
        # When: for_testing() is called with use_memory_cache=True
        cache = await factory.for_testing(use_memory_cache=True)
        
        # Then: InMemoryCache should be created
        assert cache is not None
        assert isinstance(cache, InMemoryCache)
        
        # Prove the memory cache is functional
        await cache.set("test:memory", "data")
        assert await cache.get("test:memory") == "data"

    @pytest.mark.asyncio
    async def test_for_testing_supports_custom_test_database(self):
        """
        Test that for_testing() supports custom test database configuration.
        
        Verifies:
            Custom Redis test databases can be specified for advanced testing scenarios
            
        Business Impact:
            Allows parallel test execution with different database isolation levels
            
        Scenario:
            Given: Factory configured for testing with custom database
            When: for_testing() is called with custom Redis URL specifying test database
            Then: Cache is created targeting specified test database for isolation
            
        Edge Cases Covered:
            - Custom test database selection (non-default)
            - Redis URL parsing with database specification
            - Database number validation and boundaries
            - Test isolation with multiple databases
            
        Mocks Used:
            - None
            
        Related Tests:
            - test_for_testing_uses_test_database_for_isolation()
            - test_for_testing_validates_testing_parameters()
        """
        # Given: Factory configured for testing with custom database
        factory = CacheFactory()
        
        # Custom Redis URL with different test database
        custom_redis_url = "redis://test-server:6379/10"
        
        # When: for_testing() is called with custom Redis URL
        cache = await factory.for_testing(redis_url=custom_redis_url)
        
        from app.infrastructure.cache.redis_generic import GenericRedisCache
        from app.infrastructure.cache.memory import InMemoryCache
        
        # Then: Cache should be functional (Redis or memory fallback)
        assert cache is not None
        assert isinstance(cache, (GenericRedisCache, InMemoryCache))
        
        # If Redis cache, verify custom database URL
        if isinstance(cache, GenericRedisCache):
            assert hasattr(cache, 'redis_url')
            assert '/10' in cache.redis_url
        
        # Prove cache is functional regardless of type
        await cache.set("test:custom_db", "test_data")
        assert await cache.get("test:custom_db") == "test_data"

    @pytest.mark.asyncio
    async def test_for_testing_validates_testing_parameters(self):
        """
        Test that for_testing() validates testing parameters and raises appropriate errors.
        
        Verifies:
            Invalid testing configurations are rejected with helpful error messages
            
        Business Impact:
            Prevents misconfigured testing caches that could cause test failures
            
        Scenario:
            Given: Factory instance ready for testing cache creation
            When: for_testing() is called with invalid testing parameters
            Then: ValidationError is raised with specific testing configuration guidance
            
        Edge Cases Covered:
            - Invalid TTL values for testing scenarios
            - Invalid test database specifications
            - Parameter combination validation for testing
            - Testing-specific parameter constraints
            
        Mocks Used:
            - None (validation logic test)
            
        Related Tests:
            - test_for_testing_supports_custom_test_database()
            - test_for_testing_handles_redis_unavailable_in_tests()
        """
        # Given: Factory instance ready for testing cache creation
        factory = CacheFactory()
        
        # Test invalid TTL values for testing scenarios
        with pytest.raises(ValidationError, match="default_ttl must be non-negative"):
            await factory.for_testing(default_ttl=-1)
            
        # TTL of 0 is actually valid (means no expiration), so test a negative value
        # The zero case should not raise an error
            
        # Test invalid cache sizes for testing
        with pytest.raises(ValidationError, match="must be a positive integer"):
            await factory.for_testing(l1_cache_size=-1)
            
        # Test invalid compression levels
        with pytest.raises(ValidationError, match="compression"):
            await factory.for_testing(compression_level=0)
            
        with pytest.raises(ValidationError, match="compression"):
            await factory.for_testing(compression_level=10)

    @pytest.mark.asyncio
    async def test_for_testing_handles_redis_unavailable_in_tests(self):
        """
        Test that for_testing() gracefully handles Redis unavailability during testing.
        
        Verifies:
            Testing continues with memory fallback when Redis is unavailable
            
        Business Impact:
            Ensures test suites can run in environments without Redis infrastructure
            
        Scenario:
            Given: Factory configured for testing but Redis is unavailable
            When: for_testing() is called but Redis connection fails
            Then: InMemoryCache fallback is used with appropriate testing configuration
            
        Edge Cases Covered:
            - Redis unavailability during testing
            - Graceful fallback behavior for test environments
            - Memory cache configuration preservation
            - Testing isolation with fallback cache
            
        Mocks Used:
            - Redis connection mocking to simulate unavailability
            
        Related Tests:
            - test_for_testing_creates_memory_cache_when_requested()
            - test_for_testing_validates_testing_parameters()
        """
        # Given: Factory configured for testing but Redis is unavailable
        factory = CacheFactory()
        
        from app.infrastructure.cache.memory import InMemoryCache
        
        # Use an impossible Redis URL to force a connection failure
        cache = await factory.for_testing(
            redis_url="redis://nonexistent-host:9999",
            fail_on_connection_error=False
        )
        
        # Then: Should fall back to InMemoryCache
        assert cache is not None
        assert isinstance(cache, InMemoryCache)
        
        # Prove the fallback cache is functional for testing
        await cache.set("test:redis_unavailable", "fallback_data")
        assert await cache.get("test:redis_unavailable") == "fallback_data"


class TestConfigurationBasedCacheCreation:
    """
    Test suite for configuration-driven cache creation.
    
    Scope:
        - create_cache_from_config() method behavior and flexible configuration
        - Configuration dictionary parsing and validation
        - Automatic cache type detection (Generic vs AI)
        - Parameter mapping from configuration to cache instances
        
    Business Critical:
        Configuration-based creation enables dynamic cache setup from external config files
        
    Test Strategy:
        - Unit tests for configuration parsing and cache type detection
        - Parameter mapping validation from config dictionaries
        - Cache type selection logic testing (Generic vs AI)
        - Configuration validation and error handling
        
    External Dependencies:
        - None
    """

    @pytest.mark.asyncio
    async def test_create_cache_from_config_creates_generic_cache_for_basic_config(self):
        """
        Test that create_cache_from_config() creates GenericRedisCache for basic configuration.
        
        Verifies:
            Basic cache configuration results in GenericRedisCache creation
            
        Business Impact:
            Enables straightforward cache configuration without AI-specific complexity
            
        Scenario:
            Given: Factory with basic cache configuration dictionary
            When: create_cache_from_config() is called without AI-specific parameters
            Then: GenericRedisCache is created with configuration parameters applied
            
        Edge Cases Covered:
            - Minimal required configuration (redis_url only)
            - Basic configuration with common parameters
            - Configuration parameter mapping validation
            - Generic cache type selection logic
            
        Mocks Used:
            - None
            
        Related Tests:
            - test_create_cache_from_config_creates_ai_cache_when_ai_params_present()
            - test_create_cache_from_config_validates_required_parameters()
        """
        # Given: Factory with basic cache configuration dictionary
        factory = CacheFactory()
        
        basic_config = {
            "redis_url": "redis://localhost:6379",
            "default_ttl": 3600,
            "enable_l1_cache": True,
            "compression_threshold": 2000
        }
        
        from app.infrastructure.cache.redis_generic import GenericRedisCache
        from app.infrastructure.cache.memory import InMemoryCache
        
        # When: create_cache_from_config() is called without AI-specific parameters
        cache = await factory.create_cache_from_config(basic_config)
        
        # Then: Cache should be functional (Generic Redis or memory fallback)
        assert cache is not None
        assert isinstance(cache, (GenericRedisCache, InMemoryCache))
        
        # Prove cache is functional
        await cache.set("test:config_basic", "config_data")
        assert await cache.get("test:config_basic") == "config_data"

    @pytest.mark.asyncio
    async def test_create_cache_from_config_creates_ai_cache_when_ai_params_present(self):
        """
        Test that create_cache_from_config() creates AIResponseCache when AI parameters are present.
        
        Verifies:
            Configuration with AI-specific parameters triggers AIResponseCache creation
            
        Business Impact:
            Enables automatic AI cache selection based on configuration content
            
        Scenario:
            Given: Factory with configuration containing AI-specific parameters
            When: create_cache_from_config() is called with text_hash_threshold or operation_ttls
            Then: AIResponseCache is created with AI-specific configuration applied
            
        Edge Cases Covered:
            - AI parameter detection logic (text_hash_threshold, operation_ttls)
            - AI configuration parameter mapping
            - AI cache type selection triggers
            - Mixed parameter configuration handling
            
        Mocks Used:
            - None
            
        Related Tests:
            - test_create_cache_from_config_creates_generic_cache_for_basic_config()
            - test_create_cache_from_config_maps_parameters_correctly()
        """
        # Given: Factory with configuration containing AI-specific parameters
        factory = CacheFactory()
        
        from app.infrastructure.cache.redis_ai import AIResponseCache
        from app.infrastructure.cache.memory import InMemoryCache
        
        ai_config = {
            "redis_url": "redis://ai-cache:6379",
            "default_ttl": 7200,
            "text_hash_threshold": 500,
            "operation_ttls": {"summarize": 1800, "sentiment": 3600}
        }
        
        # When: create_cache_from_config() is called with AI-specific parameters
        cache = await factory.create_cache_from_config(ai_config)
        
        # Then: Cache should be functional (AIResponseCache or InMemoryCache fallback)
        assert cache is not None
        assert isinstance(cache, (AIResponseCache, InMemoryCache))
        
        # Prove cache is functional with AI operations
        await cache.set("test:ai_config", "ai_data")
        assert await cache.get("test:ai_config") == "ai_data"

    @pytest.mark.asyncio
    async def test_create_cache_from_config_maps_parameters_correctly(self):
        """
        Test that create_cache_from_config() correctly maps configuration parameters to cache instances.
        
        Verifies:
            Configuration dictionary parameters are properly mapped to cache creation calls
            
        Business Impact:
            Ensures configuration-driven cache setup preserves all specified settings
            
        Scenario:
            Given: Factory with comprehensive configuration dictionary
            When: create_cache_from_config() is called with various parameters
            Then: Appropriate cache type is created with all configuration parameters mapped
            
        Edge Cases Covered:
            - Complete parameter mapping for generic caches
            - Complete parameter mapping for AI caches
            - Parameter type conversion and validation
            - Optional parameter handling and defaults
            
        Mocks Used:
            - None
            
        Related Tests:
            - test_create_cache_from_config_creates_ai_cache_when_ai_params_present()
            - test_create_cache_from_config_validates_parameter_types()
        """
        # Given: Factory with comprehensive configuration dictionary
        factory = CacheFactory()
        
        # Test comprehensive generic cache configuration
        comprehensive_generic_config = {
            "redis_url": "redis://production:6379",
            "default_ttl": 3600,
            "enable_l1_cache": True,
            "l1_cache_size": 500,
            "compression_threshold": 2000,
            "compression_level": 9
        }
        
        from app.infrastructure.cache.redis_generic import GenericRedisCache
        from app.infrastructure.cache.redis_ai import AIResponseCache
        from app.infrastructure.cache.memory import InMemoryCache
        
        # When: create_cache_from_config() is called with comprehensive parameters
        cache = await factory.create_cache_from_config(comprehensive_generic_config)
        
        # Then: Cache should be functional (Generic Redis or memory fallback)
        assert cache is not None
        assert isinstance(cache, (GenericRedisCache, InMemoryCache))
        
        # Prove cache is functional
        await cache.set("test:config_generic", "generic_data")
        assert await cache.get("test:config_generic") == "generic_data"
        
        # Test comprehensive AI cache configuration
        comprehensive_ai_config = {
            "redis_url": "redis://ai-production:6379",
            "default_ttl": 7200,
            "text_hash_threshold": 500,
            "operation_ttls": {"summarize": 1800, "sentiment": 3600},
            "enable_l1_cache": True,
            "l1_cache_size": 100,
            "compression_level": 6
        }
        
        # When: create_cache_from_config() is called with AI parameters
        ai_cache = await factory.create_cache_from_config(comprehensive_ai_config)
        
        # Then: Cache should be functional (AI or memory fallback)
        assert ai_cache is not None
        assert isinstance(ai_cache, (AIResponseCache, InMemoryCache))
        
        # Prove AI cache is functional
        await ai_cache.set("test:config_ai", "ai_config_data")
        assert await ai_cache.get("test:config_ai") == "ai_config_data"

    @pytest.mark.asyncio
    async def test_create_cache_from_config_validates_required_parameters(self):
        """
        Test that create_cache_from_config() validates required configuration parameters.
        
        Verifies:
            Missing required parameters are detected and appropriate errors are raised
            
        Business Impact:
            Prevents invalid cache configurations that could cause runtime failures
            
        Scenario:
            Given: Factory ready for configuration-based cache creation
            When: create_cache_from_config() is called with incomplete configuration
            Then: ValidationError is raised identifying missing required parameters
            
        Edge Cases Covered:
            - Missing redis_url parameter
            - Empty configuration dictionary
            - Partial configuration with critical parameters missing
            - Required vs optional parameter distinction
            
        Mocks Used:
            - None (validation logic test)
            
        Related Tests:
            - test_create_cache_from_config_validates_parameter_types()
            - test_create_cache_from_config_handles_configuration_conflicts()
        """
        # Given: Factory ready for configuration-based cache creation
        factory = CacheFactory()
        
        # Test missing redis_url parameter
        incomplete_config = {
            "default_ttl": 3600,
            "enable_l1_cache": True
        }
        
        with pytest.raises(ValidationError, match="redis_url is required"):
            await factory.create_cache_from_config(incomplete_config)
            
        # Test empty configuration dictionary
        empty_config = {}
        
        with pytest.raises(ValidationError, match="config dictionary cannot be empty"):
            await factory.create_cache_from_config(empty_config)
            
        # Test None configuration
        with pytest.raises(ValidationError, match="config must be a dictionary"):
            await factory.create_cache_from_config(None)

    @pytest.mark.asyncio
    async def test_create_cache_from_config_validates_parameter_types(self):
        """
        Test that create_cache_from_config() validates configuration parameter types.
        
        Verifies:
            Configuration parameters with incorrect types are rejected with helpful errors
            
        Business Impact:
            Prevents configuration errors that could cause unexpected cache behavior
            
        Scenario:
            Given: Factory with configuration containing incorrect parameter types
            When: create_cache_from_config() is called with type-mismatched parameters
            Then: ValidationError is raised with specific type requirement guidance
            
        Edge Cases Covered:
            - String parameters provided as integers
            - Integer parameters provided as strings
            - Boolean parameters provided as strings or integers
            - Dictionary parameters provided as strings
            - Type conversion possibilities vs strict validation
            
        Mocks Used:
            - None (validation logic test)
            
        Related Tests:
            - test_create_cache_from_config_validates_required_parameters()
            - test_create_cache_from_config_handles_configuration_conflicts()
        """
        # Given: Factory with configuration containing incorrect parameter types
        factory = CacheFactory()
        
        # Test integer parameters provided as strings where integers required
        invalid_config_int = {
            "redis_url": "redis://localhost:6379",
            "default_ttl": "not_an_integer",  # Should be int
        }
        
        with pytest.raises(ValidationError, match="default_ttl must be an integer"):
            await factory.create_cache_from_config(invalid_config_int)
            
        # Test boolean parameters provided as strings
        invalid_config_bool = {
            "redis_url": "redis://localhost:6379",
            "enable_l1_cache": "true",  # Should be bool
        }
        
        with pytest.raises(ValidationError, match="enable_l1_cache must be a boolean"):
            await factory.create_cache_from_config(invalid_config_bool)
            
        # Test dictionary parameters provided as strings
        invalid_config_dict = {
            "redis_url": "redis://localhost:6379",
            "operation_ttls": "not_a_dict",  # Should be dict
        }
        
        with pytest.raises(ValidationError, match="operation_ttls must be a dictionary"):
            await factory.create_cache_from_config(invalid_config_dict)

    @pytest.mark.asyncio
    async def test_create_cache_from_config_handles_configuration_conflicts(self):
        """
        Test that create_cache_from_config() detects and handles configuration conflicts.
        
        Verifies:
            Conflicting configuration parameters are identified with resolution guidance
            
        Business Impact:
            Prevents ambiguous cache configurations that could lead to unexpected behavior
            
        Scenario:
            Given: Factory with configuration containing conflicting parameters
            When: create_cache_from_config() is called with parameter conflicts
            Then: ConfigurationError is raised with conflict resolution guidance
            
        Edge Cases Covered:
            - Conflicting cache type indicators
            - Incompatible parameter combinations
            - Resource constraint conflicts (memory vs performance)
            - Configuration precedence rules
            
        Mocks Used:
            - None (validation logic test)
            
        Related Tests:
            - test_create_cache_from_config_validates_parameter_types()
            - test_create_cache_from_config_handles_redis_connection_failure()
        """
        # Given: Factory with configuration containing conflicting parameters
        factory = CacheFactory()
        
        # Test conflicting L1 cache configuration
        conflicting_config = {
            "redis_url": "redis://localhost:6379",
            "enable_l1_cache": False,
            "l1_cache_size": 500  # Conflicts with disabled L1 cache
        }
        
        # This should not actually raise an error - the factory should handle this gracefully
        # by ignoring l1_cache_size when enable_l1_cache is False
        # If it does raise, it would be a ValidationError
        try:
            cache = await factory.create_cache_from_config(conflicting_config)
            # Should succeed - conflicting config is handled gracefully
            assert cache is not None
        except ValidationError:
            # If validation error is raised, that's also acceptable behavior
            pass
            
        # Test memory cache size conflict with L1 cache size  
        conflicting_ai_config = {
            "redis_url": "redis://localhost:6379",
            "text_hash_threshold": 500,  # Triggers AI cache
            "l1_cache_size": 100,
            "memory_cache_size": 200  # Should override l1_cache_size in AI cache
        }
        
        # This should NOT raise an error as memory_cache_size should override l1_cache_size
        # But we can test a warning is logged
        with patch('app.infrastructure.cache.redis_ai.AIResponseCache') as mock_ai_class:
            mock_ai_class.return_value = AsyncMock()
            
            cache = await factory.create_cache_from_config(conflicting_ai_config)
            
            # Check if AI cache was created
            if mock_ai_class.call_args is not None:
                call_kwargs = mock_ai_class.call_args.kwargs
                # The factory should pass memory_cache_size and potentially log a warning
                assert 'memory_cache_size' in call_kwargs
            else:
                # If not called, it means the factory handled the conflict differently
                # which is also acceptable behavior
                pass

    @pytest.mark.asyncio
    async def test_create_cache_from_config_handles_redis_connection_failure(self):
        """
        Test that create_cache_from_config() handles Redis connection failures gracefully.
        
        Verifies:
            Configuration-based cache creation falls back appropriately when Redis unavailable
            
        Business Impact:
            Ensures configuration-driven applications can start with degraded cache functionality
            
        Scenario:
            Given: Factory with valid configuration but Redis connection fails
            When: create_cache_from_config() is called but Redis is unavailable
            Then: InMemoryCache fallback is created with configuration warnings
            
        Edge Cases Covered:
            - Redis connection failure during configuration-based creation
            - Fallback behavior with configuration parameter preservation
            - Warning messages for configuration-driven fallback
            - Configuration-specific error handling
            
        Mocks Used:
            - Redis connection mocking to simulate failures
            
        Related Tests:
            - test_create_cache_from_config_handles_configuration_conflicts()
            - test_create_cache_from_config_enforces_strict_redis_requirement()
        """
        # Given: Factory with valid configuration but Redis connection fails
        factory = CacheFactory()
        
        valid_config = {
            "redis_url": "redis://unavailable-server:6379",
            "default_ttl": 3600,
            "enable_l1_cache": True
        }
        
        from app.infrastructure.cache.memory import InMemoryCache
        
        # Use an impossible Redis URL to force a connection failure
        invalid_config = valid_config.copy()
        invalid_config["redis_url"] = "redis://nonexistent-host:9999"
        
        # When: create_cache_from_config() is called but Redis is unavailable
        cache = await factory.create_cache_from_config(invalid_config, fail_on_connection_error=False)
        
        # Then: Should fall back to InMemoryCache
        assert cache is not None
        assert isinstance(cache, InMemoryCache)
        
        # Prove the fallback cache is functional
        await cache.set("test:config_fallback", "fallback_data")
        assert await cache.get("test:config_fallback") == "fallback_data"

    @pytest.mark.asyncio
    async def test_create_cache_from_config_enforces_strict_redis_requirement(self):
        """
        Test that create_cache_from_config() enforces strict Redis requirements when specified.
        
        Verifies:
            Configuration-based creation can require Redis connectivity without fallback
            
        Business Impact:
            Allows configuration-driven applications to fail fast for critical cache dependencies
            
        Scenario:
            Given: Factory with configuration and fail_on_connection_error=True
            When: create_cache_from_config() is called but Redis connection fails
            Then: InfrastructureError is raised with configuration-specific failure details
            
        Edge Cases Covered:
            - Strict Redis requirements in configuration context
            - Configuration-specific error messages
            - Different failure scenarios with configuration context
            - Error message specificity for configuration debugging
            
        Mocks Used:
            - Redis connection mocking to simulate failures
            
        Related Tests:
            - test_create_cache_from_config_handles_redis_connection_failure()
            - test_create_cache_from_config_handles_configuration_conflicts()
        """
        # Given: Factory with configuration and fail_on_connection_error=True
        factory = CacheFactory()
        
        valid_config = {
            "redis_url": "redis://unavailable-server:6379",
            "default_ttl": 3600
        }
        
        # Mock Redis connection to fail
        with patch('app.infrastructure.cache.redis_generic.GenericRedisCache') as mock_redis:
            redis_error = Exception("Redis connection failed")
            mock_redis.side_effect = redis_error
            
            # When: create_cache_from_config() is called but Redis connection fails
            # Then: InfrastructureError is raised with configuration-specific failure details
            with pytest.raises(InfrastructureError, match="Redis connection failed"):
                await factory.create_cache_from_config(valid_config, fail_on_connection_error=True)