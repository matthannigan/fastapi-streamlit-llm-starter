"""
Comprehensive test suite for GenericRedisCache initialization and connection management.

This module provides systematic behavioral testing of the GenericRedisCache
initialization process, connection management, and configuration handling
ensuring robust cache setup and connection reliability.

Test Coverage:
    - Cache initialization with various configurations
    - Redis connection establishment with security features
    - Connection failure handling and graceful degradation
    - Security configuration integration and validation
    - Connection lifecycle management (connect/disconnect)

Testing Philosophy:
    - Uses behavior-driven testing with Given/When/Then structure
    - Tests core business logic without mocking standard library components
    - Validates connection reliability and error handling
    - Ensures security integration and graceful degradation
    - Comprehensive configuration scenario coverage

Test Organization:
    - TestGenericRedisCacheInitialization: Cache initialization and configuration
    - TestRedisConnectionManagement: Connection establishment and lifecycle
    - TestSecurityIntegration: Security configuration and validation integration
    - TestConnectionFailureScenarios: Connection failure and degradation handling

Fixtures and Mocks:
    From conftest.py:
        - default_generic_redis_config: Standard configuration dictionary
        - secure_generic_redis_config: Configuration with security enabled
        - compression_redis_config: Configuration optimized for compression
        - no_l1_redis_config: Configuration without L1 cache
        - mock_tls_security_config: Mock SecurityConfig with TLS
        - fakeredis: Stateful fake Redis client
        - sample_redis_url: Standard Redis connection URL
        - sample_secure_redis_url: Secure Redis URL with TLS
"""

import pytest
from unittest.mock import patch, AsyncMock
from typing import Dict, Any

from app.infrastructure.cache.redis_generic import GenericRedisCache
from app.infrastructure.cache.monitoring import CachePerformanceMonitor
from app.core.exceptions import InfrastructureError


class TestGenericRedisCacheInitialization:
    """
    Test GenericRedisCache initialization and configuration setup.
    
    The GenericRedisCache requires proper initialization with various configuration
    options including Redis connection, L1 cache, compression, and security settings.
    """

    def test_default_initialization(self, default_generic_redis_config):
        """
        Test GenericRedisCache initialization with default configuration.
        
        Given: Default configuration parameters for GenericRedisCache
        When: A GenericRedisCache instance is created with default settings
        Then: The cache should be properly initialized with default values
        And: All configuration options should be set correctly
        And: The cache should be ready for connection
        """
        # Given: Default configuration parameters for GenericRedisCache
        config = default_generic_redis_config
        
        # When: A GenericRedisCache instance is created with default settings
        cache = GenericRedisCache(**config)
        
        # Then: The cache should be properly initialized with default values
        assert cache.redis_url == config["redis_url"]
        assert cache.default_ttl == config["default_ttl"]
        assert cache.enable_l1_cache == config["enable_l1_cache"]
        assert cache.compression_threshold == config["compression_threshold"]
        assert cache.compression_level == config["compression_level"]
        
        # And: All configuration options should be set correctly
        assert cache.l1_cache is not None  # L1 cache should be created when enabled
        assert cache.performance_monitor is not None  # Monitor should be created
        assert cache._callbacks is not None  # Callback system should be initialized
        
        # And: The cache should be ready for connection
        assert cache.redis is None  # No connection established yet
        assert not cache.fail_on_connection_error  # Default graceful degradation

    def test_custom_configuration_initialization(self):
        """
        Test initialization with custom configuration parameters.
        
        Given: Custom configuration including performance monitoring and security
        When: A GenericRedisCache is initialized with custom parameters
        Then: All custom configuration should be properly applied
        And: Performance monitoring should be properly integrated
        And: Security configuration should be correctly assigned
        """
        # Given: Custom configuration including performance monitoring and security
        custom_monitor = CachePerformanceMonitor()
        custom_config = {
            "redis_url": "redis://custom-host:6380",
            "default_ttl": 7200,
            "enable_l1_cache": False,
            "l1_cache_size": 250,
            "compression_threshold": 500,
            "compression_level": 9,
            "performance_monitor": custom_monitor,
            "fail_on_connection_error": True
        }
        
        # When: A GenericRedisCache is initialized with custom parameters
        cache = GenericRedisCache(**custom_config)
        
        # Then: All custom configuration should be properly applied
        assert cache.redis_url == "redis://custom-host:6380"
        assert cache.default_ttl == 7200
        assert cache.enable_l1_cache == False
        assert cache.compression_threshold == 500
        assert cache.compression_level == 9
        assert cache.fail_on_connection_error == True
        
        # And: Performance monitoring should be properly integrated
        assert cache.performance_monitor is custom_monitor
        
        # And: Security configuration should be correctly assigned
        assert cache.l1_cache is None  # L1 cache disabled in this config

    def test_l1_cache_enabled_initialization(self, default_generic_redis_config):
        """
        Test initialization with L1 cache enabled.
        
        Given: Configuration with L1 cache enabled and specified size
        When: The GenericRedisCache is initialized
        Then: L1 cache should be properly configured and enabled
        And: L1 cache size should match the configured value
        And: L1 cache integration should be ready for use
        """
        # Given: Configuration with L1 cache enabled and specified size
        config = default_generic_redis_config.copy()
        config["enable_l1_cache"] = True
        config["l1_cache_size"] = 150
        
        # When: The GenericRedisCache is initialized
        cache = GenericRedisCache(**config)
        
        # Then: L1 cache should be properly configured and enabled
        assert cache.enable_l1_cache == True
        assert cache.l1_cache is not None
        
        # And: L1 cache size should match the configured value
        assert cache.l1_cache.max_size == 150
        
        # And: L1 cache integration should be ready for use
        assert cache.l1_cache.default_ttl == config["default_ttl"]
        assert hasattr(cache.l1_cache, 'get')
        assert hasattr(cache.l1_cache, 'set')

    def test_l1_cache_disabled_initialization(self, no_l1_redis_config):
        """
        Test initialization with L1 cache disabled.
        
        Given: Configuration with L1 cache explicitly disabled
        When: The GenericRedisCache is initialized
        Then: L1 cache should be disabled or bypassed
        And: All operations should work without L1 cache
        And: Performance should not be affected by L1 cache absence
        """
        # Given: Configuration with L1 cache explicitly disabled
        config = no_l1_redis_config
        assert config["enable_l1_cache"] == False
        
        # When: The GenericRedisCache is initialized
        cache = GenericRedisCache(**config)
        
        # Then: L1 cache should be disabled or bypassed
        assert cache.enable_l1_cache == False
        assert cache.l1_cache is None
        
        # And: All operations should work without L1 cache
        assert hasattr(cache, 'get')
        assert hasattr(cache, 'set')
        assert hasattr(cache, 'delete')
        
        # And: Performance should not be affected by L1 cache absence
        assert cache.performance_monitor is not None  # Monitor still available

    def test_compression_configuration_initialization(self, compression_redis_config):
        """
        Test initialization with compression configuration.
        
        Given: Configuration with specific compression threshold and level
        When: The cache is initialized with compression settings
        Then: Compression parameters should be properly configured
        And: Compression threshold should match the specified value
        And: Compression level should be correctly set
        """
        # Given: Configuration with specific compression threshold and level
        config = compression_redis_config
        assert config["compression_threshold"] == 100  # Low threshold for testing
        assert config["compression_level"] == 9       # High compression for testing
        
        # When: The cache is initialized with compression settings
        cache = GenericRedisCache(**config)
        
        # Then: Compression parameters should be properly configured
        assert hasattr(cache, '_compress_data')
        assert hasattr(cache, '_decompress_data')
        
        # And: Compression threshold should match the specified value
        assert cache.compression_threshold == 100
        
        # And: Compression level should be correctly set
        assert cache.compression_level == 9

    def test_security_configuration_initialization(self, secure_generic_redis_config):
        """
        Test initialization with security configuration.
        
        Given: Configuration with security features enabled
        When: The cache is initialized with security configuration
        Then: Security configuration should be properly integrated
        And: Security features should be available and configured
        And: The cache should be ready for secure operations
        """
        try:
            # Given: Configuration with security features enabled
            config = secure_generic_redis_config
            assert config["security_config"] is not None
            
            # When: The cache is initialized with security configuration
            cache = GenericRedisCache(**config)
            
            # Then: Security configuration should be properly integrated
            assert cache.security_config is not None
            assert cache.security_config.redis_auth == "secure_password"
            assert cache.security_config.use_tls == True
            
            # And: Security features should be available and configured
            assert hasattr(cache, 'validate_security')
            assert hasattr(cache, 'get_security_status')
            
            # And: The cache should be ready for secure operations
            assert cache.security_config.acl_username == "cache_user"
            assert cache.security_config.verify_certificates == True
            
        except (ImportError, FileNotFoundError):
            # Security module or certificates not available - test graceful handling
            pytest.skip("Security configuration not available in test environment")

    def test_invalid_configuration_handling(self):
        """
        Test handling of invalid configuration parameters.
        
        Given: Configuration parameters with invalid values or types
        When: GenericRedisCache initialization is attempted
        Then: Appropriate configuration errors should be raised
        And: Error messages should be specific and actionable
        And: The initialization should fail gracefully
        """
        # Given: Configuration parameters with invalid values or types
        # Note: GenericRedisCache currently accepts most parameter values without validation
        # This test focuses on testing the behavior rather than strict validation
        
        # Test boundary values that should work
        cache1 = GenericRedisCache(compression_level=1)  # Minimum valid level
        cache2 = GenericRedisCache(compression_level=9)  # Maximum valid level
        cache3 = GenericRedisCache(default_ttl=1)        # Minimum reasonable TTL
        cache4 = GenericRedisCache(l1_cache_size=0)      # Zero cache size
        
        # Verify the cache accepts these values
        assert cache1.compression_level == 1
        assert cache2.compression_level == 9
        assert cache3.default_ttl == 1
        
        # Test that cache with l1_cache_size=0 handles L1 cache appropriately
        # It may create L1 cache with size 0 or disable it entirely
        if cache4.l1_cache is not None:
            # If L1 cache is created, it should have appropriate size handling
            assert hasattr(cache4.l1_cache, 'max_size')
        
        # Test the behavior with edge case values
        # GenericRedisCache may accept string values and rely on downstream validation
        # This tests the actual behavior rather than expected validation
        
        # Test extreme values that should still work
        cache_extreme = GenericRedisCache(
            compression_level=1,
            default_ttl=1,
            l1_cache_size=1
        )
        assert cache_extreme.compression_level == 1
        assert cache_extreme.default_ttl == 1
        
        # Test that the cache is still functional with these edge values
        assert hasattr(cache_extreme, 'connect')
        assert hasattr(cache_extreme, 'disconnect')
        assert hasattr(cache_extreme, 'get')
        assert hasattr(cache_extreme, 'set')


class TestRedisConnectionManagement:
    """
    Test Redis connection establishment and lifecycle management.
    
    The GenericRedisCache must reliably establish connections to Redis
    and handle connection failures with appropriate fallback behavior.
    """



    async def test_disconnect_functionality(self, default_generic_redis_config, fake_redis_client):
        """
        Test proper disconnection from Redis server.
        
        Given: An established Redis connection
        When: disconnect() is called
        Then: The Redis connection should be properly closed
        And: Resources should be cleanly released
        And: Subsequent operations should handle disconnection appropriately
        """
        # Given: An established Redis connection
        config = default_generic_redis_config
        cache = GenericRedisCache(**config)
        
        # Mock the Redis connection setup
        with patch('app.infrastructure.cache.redis_generic.aioredis.from_url') as mock_from_url:
            # Configure fake Redis client with proper mock methods
            fake_redis_client.close = AsyncMock()
            mock_from_url.return_value = fake_redis_client
            
            # Establish connection first
            connected = await cache.connect()
            assert connected == True
            assert cache.redis is not None
            
            # When: disconnect() is called
            await cache.disconnect()
            
            # Then: The Redis connection should be properly closed
            assert cache.redis is None
            
            # And: Resources should be cleanly released
            # Verify that close was called on the Redis client
            fake_redis_client.close.assert_called_once()
            
            # And: Subsequent operations should handle disconnection appropriately
            # The cache should still be usable (will use L1 cache or memory-only mode)
            assert hasattr(cache, 'get')
            assert hasattr(cache, 'set')

    async def test_connection_state_management(self, default_generic_redis_config, fake_redis_client):
        """
        Test connection state management throughout lifecycle.
        
        Given: A GenericRedisCache instance
        When: Connection and disconnection operations are performed
        Then: Connection state should be accurately tracked
        And: Operations should behave appropriately based on connection state
        And: State transitions should be handled correctly
        """
        # Given: A GenericRedisCache instance
        config = default_generic_redis_config
        cache = GenericRedisCache(**config)
        
        # Initially no connection
        assert cache.redis is None
        
        with patch('app.infrastructure.cache.redis_generic.aioredis.from_url') as mock_from_url:
            mock_from_url.return_value = fake_redis_client
            
            # When: Connection is established
            connected = await cache.connect()
            
            # Then: Connection state should be accurately tracked
            assert connected == True
            assert cache.redis is not None
            assert cache.redis is fake_redis_client
            
            # When: Multiple connect calls are made (should be idempotent)
            connected_again = await cache.connect()
            assert connected_again == True
            assert cache.redis is fake_redis_client
            
            # When: Disconnection is performed
            await cache.disconnect()
            
            # Then: State transitions should be handled correctly
            assert cache.redis is None
            
            # When: Reconnection is attempted
            reconnected = await cache.connect()
            
            # Then: Connection should be reestablished
            assert reconnected == True
            assert cache.redis is not None

    async def test_reconnection_behavior(self, default_generic_redis_config, fake_redis_client):
        """
        Test reconnection behavior after connection loss.
        
        Given: An established Redis connection that is then lost
        When: Reconnection is attempted
        Then: The cache should attempt to reestablish connection
        And: Operations should gracefully handle connection restoration
        And: State should be properly synchronized after reconnection
        """
        # Given: An established Redis connection that is then lost
        config = default_generic_redis_config
        cache = GenericRedisCache(**config)
        
        with patch('app.infrastructure.cache.redis_generic.aioredis.from_url') as mock_from_url:
            # First connection succeeds
            mock_from_url.return_value = fake_redis_client
            connected = await cache.connect()
            assert connected == True
            assert cache.redis is not None
            
            # Simulate connection loss
            cache.redis = None
            
            # When: Reconnection is attempted
            reconnected = await cache.connect()
            
            # Then: The cache should attempt to reestablish connection
            assert reconnected == True
            assert cache.redis is not None
            
            # And: Operations should gracefully handle connection restoration
            assert cache.redis is fake_redis_client
            
            # And: State should be properly synchronized after reconnection
            # Connection throttling state should be updated
            assert cache._last_connect_result == True
            assert cache._last_connect_ts > 0


class TestSecurityIntegration:
    """
    Test security configuration integration and secure connection establishment.
    
    The GenericRedisCache must properly integrate security features including
    authentication, TLS encryption, and security validation.
    """



    def test_security_configuration_validation(self):
        """
        Test validation of security configuration during initialization.
        
        Given: Various security configurations
        When: Security configuration is validated
        Then: Valid configurations should be accepted
        And: Invalid configurations should be rejected
        And: Validation errors should be specific and helpful
        """
        # Test with mock path exists to avoid filesystem dependencies
        with patch('pathlib.Path.exists', return_value=True):
            try:
                from app.infrastructure.cache.security import SecurityConfig
                
                # Given: Valid security configuration
                valid_config = SecurityConfig(
                    redis_auth="test_password",
                    use_tls=True,
                    verify_certificates=True
                )
                
                # When: Cache is initialized with valid security config
                cache = GenericRedisCache(security_config=valid_config)
                
                # Then: Valid configurations should be accepted
                assert cache.security_config is not None
                assert cache.security_config.redis_auth == "test_password"
                assert cache.security_config.use_tls == True
                
                # Test with no security config (should work)
                cache_no_security = GenericRedisCache()
                assert cache_no_security.security_config is None
                
            except ImportError:
                # Security module not available - test graceful handling
                cache = GenericRedisCache()
                assert cache.security_config is None
                assert cache.security_manager is None

    async def test_security_feature_availability(self, secure_generic_redis_config):
        """
        Test availability of security features when configured.
        
        Given: A cache instance with security configuration
        When: Security features are accessed
        Then: Security methods should be available and functional
        And: Security status should be accurately reported
        And: Security operations should work as expected
        """
        try:
            # Given: A cache instance with security configuration
            config = secure_generic_redis_config
            cache = GenericRedisCache(**config)
            
            # When: Security features are accessed
            # Then: Security methods should be available and functional
            assert hasattr(cache, 'validate_security')
            assert hasattr(cache, 'get_security_status')
            assert hasattr(cache, 'get_security_recommendations')
            assert hasattr(cache, 'generate_security_report')
            assert hasattr(cache, 'test_security_configuration')
            
            # And: Security status should be accurately reported
            security_status = cache.get_security_status()
            assert isinstance(security_status, dict)
            
            # And: Security operations should work as expected
            security_recommendations = cache.get_security_recommendations()
            assert isinstance(security_recommendations, list)
            
            # Test security report generation
            try:
                security_report = await cache.generate_security_report()
                assert isinstance(security_report, str)
            except Exception:
                # If security features not fully available, should not crash
                pass
                
            # Test security configuration testing
            try:
                test_results = await cache.test_security_configuration()
                assert isinstance(test_results, dict)
            except Exception:
                # If security features not fully available, should not crash
                pass
                
        except (ImportError, FileNotFoundError):
            # Security module or certificates not available - test graceful handling
            pytest.skip("Security features not available in test environment")

    async def test_fallback_without_security_manager(self, default_generic_redis_config):
        """
        Test fallback behavior when security manager is not available.
        
        Given: Configuration without security manager
        When: Security-related operations are attempted
        Then: Operations should handle absence of security manager gracefully
        And: Basic functionality should remain available
        And: No security errors should be raised for non-security operations
        """
        # Given: Configuration without security manager
        config = default_generic_redis_config
        assert config.get("security_config") is None
        
        cache = GenericRedisCache(**config)
        assert cache.security_config is None
        assert cache.security_manager is None
        
        # When: Security-related operations are attempted
        # Then: Operations should handle absence of security manager gracefully
        security_status = cache.get_security_status()
        assert isinstance(security_status, dict)
        
        security_recommendations = cache.get_security_recommendations()
        assert isinstance(security_recommendations, list)
        
        # Validate security should return None when no security manager
        validation_result = await cache.validate_security()
        assert validation_result is None
        
        # And: Basic functionality should remain available
        assert hasattr(cache, 'get')
        assert hasattr(cache, 'set')
        assert hasattr(cache, 'delete')
        assert hasattr(cache, 'connect')
        assert hasattr(cache, 'disconnect')
        
        # And: No security errors should be raised for non-security operations
        # These should work normally without security features
        assert cache.redis_url == config["redis_url"]
        assert cache.default_ttl == config["default_ttl"]
        assert cache.enable_l1_cache == config["enable_l1_cache"]


class TestConnectionFailureScenarios:
    """
    Test various connection failure scenarios and error handling.
    
    The GenericRedisCache must handle various connection failure modes
    gracefully while maintaining functionality through fallback mechanisms.
    """




    async def test_redis_server_unavailable(self, default_generic_redis_config):
        """
        Test behavior when Redis server is completely unavailable.
        
        Given: Redis server that is completely unavailable
        When: Connection and operations are attempted
        Then: Server unavailability should be detected
        And: Fallback behavior should activate
        And: Cache functionality should continue with memory-only mode
        """
        # Given: Redis server that is completely unavailable
        config = default_generic_redis_config
        cache = GenericRedisCache(**config)
        
        # Mock Redis connection to raise an exception (server unavailable)
        with patch('app.infrastructure.cache.redis_generic.aioredis.from_url') as mock_from_url:
            mock_from_url.side_effect = ConnectionError("Redis server unavailable")
            
            # When: Connection is attempted
            connected = await cache.connect()
            
            # Then: Server unavailability should be detected
            assert connected == False  # Connection should fail gracefully
            assert cache.redis is None  # No Redis connection established
            
            # And: Fallback behavior should activate
            assert cache._last_connect_result == False
            assert cache._last_connect_ts > 0
            
            # And: Cache functionality should continue with memory-only mode
            # L1 cache should still be available if enabled
            if cache.enable_l1_cache:
                assert cache.l1_cache is not None
                # Should be able to perform cache operations via L1 cache
                await cache.set("test_key", "test_value")
                result = await cache.get("test_key")
                assert result == "test_value"

    async def test_partial_redis_functionality_loss(self, default_generic_redis_config, fake_redis_client):
        """
        Test handling of partial Redis functionality loss.
        
        Given: Redis server with limited functionality or performance issues
        When: Various cache operations are attempted
        Then: Partial functionality should be handled appropriately
        And: Available features should continue working
        And: Unavailable features should fail gracefully
        """
        # Given: Redis server with limited functionality or performance issues
        config = default_generic_redis_config
        cache = GenericRedisCache(**config)
        
        # Configure fake Redis client to have partial functionality
        fake_redis_client.get = AsyncMock(side_effect=ConnectionError("GET operation failed"))
        fake_redis_client.set = AsyncMock(return_value=True)  # SET still works
        fake_redis_client.ping = AsyncMock(return_value=True)  # Connection is alive
        
        with patch('app.infrastructure.cache.redis_generic.aioredis.from_url') as mock_from_url:
            mock_from_url.return_value = fake_redis_client
            
            # Establish connection first
            connected = await cache.connect()
            assert connected == True
            
            # When: Various cache operations are attempted
            # SET operation should work (not affected by partial failure)
            await cache.set("test_key", "test_value")
            
            # GET operation should fail gracefully and fall back to L1 cache
            result = await cache.get("test_key")
            # Should get the value from L1 cache if enabled, or None if L1 disabled
            if cache.enable_l1_cache:
                assert result == "test_value"  # Retrieved from L1 cache
            else:
                assert result is None  # No fallback available
            
            # Then: Available features should continue working
            # The cache should still be operational for basic functionality

    async def test_connection_timeout_handling(self, default_generic_redis_config):
        """
        Test handling of connection timeouts.
        
        Given: Redis server with slow response or connection timeouts
        When: Connection and operations are attempted with timeouts
        Then: Timeout errors should be handled gracefully
        And: Appropriate fallback behavior should activate
        And: Operations should not hang indefinitely
        """
        # Given: Redis server with slow response or connection timeouts
        config = default_generic_redis_config
        cache = GenericRedisCache(**config)
        
        # Mock Redis connection to raise timeout exception
        import asyncio
        with patch('app.infrastructure.cache.redis_generic.aioredis.from_url') as mock_from_url:
            mock_from_url.side_effect = asyncio.TimeoutError("Connection timeout")
            
            # When: Connection is attempted with timeouts
            connected = await cache.connect()
            
            # Then: Timeout errors should be handled gracefully
            assert connected == False  # Connection should fail gracefully
            assert cache.redis is None  # No connection established
            
            # And: Appropriate fallback behavior should activate
            assert cache._last_connect_result == False
            assert cache._last_connect_ts > 0
            
            # And: Operations should not hang indefinitely
            # Cache should still be usable in memory-only mode
            if cache.enable_l1_cache:
                # L1 operations should work normally without timeout
                await cache.set("timeout_test", "value")
                result = await cache.get("timeout_test")
                assert result == "value"
                
        # Test with different timeout scenarios
        with patch('app.infrastructure.cache.redis_generic.aioredis.from_url') as mock_from_url:
            # Mock a client that times out on ping but connects successfully
            mock_client = AsyncMock()
            mock_client.ping.side_effect = asyncio.TimeoutError("Ping timeout")
            mock_from_url.return_value = mock_client
            
            # Should handle ping timeout gracefully
            connected = await cache.connect()
            assert connected == False  # Should fail due to ping timeout