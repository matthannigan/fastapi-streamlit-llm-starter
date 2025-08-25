"""
Comprehensive unit tests for cache factory system with explicit cache instantiation.

This module tests all cache factory components following docstring-driven
test development methodology. Tests verify documented contracts in Args, Returns,
Raises, and Behavior sections, focusing on WHAT should happen rather than HOW
it's implemented.

The cache factory provides deterministic cache creation for different use cases,
replacing auto-detection patterns with explicit configuration. Tests validate
proper factory pattern implementation, cache construction workflows, input
validation, error handling, and graceful fallback behaviors.

Test Classes:
    - TestCacheFactoryInitialization: Factory initialization and monitoring setup
    - TestFactoryInputValidation: Comprehensive input validation for all factory methods
    - TestWebAppCacheFactory: Web application cache creation with balanced performance
    - TestAIAppCacheFactory: AI application cache creation with enhanced storage
    - TestTestingCacheFactory: Testing-optimized cache creation with short TTLs
    - TestConfigBasedCacheFactory: Configuration-driven cache creation
    - TestFactoryErrorHandling: Error handling and graceful degradation patterns
    - TestFactoryIntegration: Integration testing across factory methods and cache types

Coverage Requirements:
    >90% coverage for infrastructure modules per project standards
    
Testing Philosophy:
    - Test WHAT should happen per docstring contracts
    - Focus on factory behavior verification, not cache implementation details
    - Mock external dependencies (Redis, CachePerformanceMonitor, cache classes) appropriately
    - Test input validation, configuration mapping, and error handling patterns
    - Validate factory method selection logic and parameter passing
    - Test graceful fallback to InMemoryCache when Redis unavailable

Business Impact:
    These tests ensure reliable cache factory operation for deterministic cache
    instantiation across different application types. Factory failures could impact
    cache availability, leading to performance degradation and potential service
    outages. Proper factory testing prevents cache misconfiguration issues.
"""

import json
import logging
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
from typing import Dict, Any, Optional

from app.infrastructure.cache.factory import CacheFactory, MONITORING_AVAILABLE
from app.infrastructure.cache.base import CacheInterface
from app.infrastructure.cache.memory import InMemoryCache
from app.core.exceptions import ConfigurationError, ValidationError, InfrastructureError


class TestCacheFactoryInitialization:
    """
    Test CacheFactory initialization and monitoring setup.
    
    Business Impact:
        CacheFactory initialization ensures proper performance monitoring setup
        when available and establishes logging for factory operations. Failures
        could prevent cache factory operation and monitoring capabilities.
    """
    
    def test_factory_initialization_default(self):
        """
        Test CacheFactory initialization with default configuration per docstring.
        
        Business Impact:
            Ensures factory can be created with default configuration for immediate use
            
        Test Scenario:
            Create CacheFactory instance with default settings
            
        Success Criteria:
            - Factory initializes successfully
            - Performance monitor is set up when monitoring available
            - Logging is properly configured
        """
        with patch('app.infrastructure.cache.factory.logger') as mock_logger:
            factory = CacheFactory()
            
            # Verify initialization
            assert factory is not None
            
            # Verify logging
            mock_logger.info.assert_called_with("CacheFactory initialized")
    
    @patch('app.infrastructure.cache.factory.MONITORING_AVAILABLE', True)
    @patch('app.infrastructure.cache.factory.CachePerformanceMonitor')
    def test_factory_initialization_with_monitoring(self, mock_monitor_class):
        """
        Test CacheFactory initialization with performance monitoring enabled.
        
        Business Impact:
            Ensures factory properly sets up performance monitoring for production environments
            
        Test Scenario:
            Create factory when monitoring is available
            
        Success Criteria:
            - Performance monitor is created
            - Factory stores monitor reference
        """
        mock_monitor_instance = MagicMock()
        mock_monitor_class.return_value = mock_monitor_instance
        
        factory = CacheFactory()
        
        # Verify monitor setup
        mock_monitor_class.assert_called_once()
        assert factory._performance_monitor is mock_monitor_instance
    
    @patch('app.infrastructure.cache.factory.MONITORING_AVAILABLE', False)
    def test_factory_initialization_without_monitoring(self):
        """
        Test CacheFactory initialization when monitoring is unavailable.
        
        Business Impact:
            Ensures factory works in environments without performance monitoring
            
        Test Scenario:
            Create factory when monitoring is not available
            
        Success Criteria:
            - Factory initializes successfully
            - Performance monitor is None
        """
        factory = CacheFactory()
        
        assert factory._performance_monitor is None


class TestFactoryInputValidation:
    """
    Test _validate_factory_inputs method for comprehensive parameter validation.
    
    Business Impact:
        Input validation prevents cache factory creation with invalid parameters
        that could cause runtime errors, security issues, or performance problems.
        Proper validation ensures reliable cache configuration.
    """
    
    def setup_method(self):
        """Set up factory instance for testing."""
        self.factory = CacheFactory()
    
    def test_validate_factory_inputs_valid_parameters(self):
        """
        Test input validation with all valid parameters per docstring.
        
        Business Impact:
            Ensures validation accepts properly formatted parameters for cache creation
            
        Test Scenario:
            Call validation with all valid parameter combinations
            
        Success Criteria:
            - No exceptions raised for valid inputs
            - Validation passes silently
        """
        # Test valid parameters - should not raise
        self.factory._validate_factory_inputs(
            redis_url="redis://localhost:6379",
            default_ttl=3600,
            fail_on_connection_error=False,
            enable_l1_cache=True,
            l1_cache_size=100,
            compression_threshold=1000,
            compression_level=6
        )
    
    def test_validate_redis_url_format(self):
        """
        Test redis_url validation per docstring format requirements.
        
        Business Impact:
            Prevents invalid Redis URLs that would cause connection failures
            
        Test Scenario:
            Test various redis_url format validations
            
        Success Criteria:
            - Valid URLs pass validation
            - Invalid URLs raise ValidationError with specific messages
        """
        # Valid URLs should pass
        valid_urls = [
            "redis://localhost:6379",
            "rediss://secure.redis.com:6380",
            "redis://user:pass@redis.example.com:6379/1",
            "rediss://redis-cluster:6379"
        ]
        
        for url in valid_urls:
            self.factory._validate_factory_inputs(redis_url=url)
        
        # Invalid URLs should fail
        invalid_urls = [
            "http://localhost:6379",  # Wrong protocol
            "redis://",               # Missing host
            "redis:///",              # Missing host with slash
            "",                       # Empty string
            "   ",                    # Whitespace only
            123                       # Not a string
        ]
        
        for url in invalid_urls:
            with pytest.raises(ValidationError) as exc_info:
                self.factory._validate_factory_inputs(redis_url=url)
            
            assert "redis_url" in str(exc_info.value).lower()
    
    def test_validate_default_ttl_boundaries(self):
        """
        Test default_ttl validation per docstring boundary requirements.
        
        Business Impact:
            Prevents invalid TTL values that could cause cache performance issues
            
        Test Scenario:
            Test TTL boundary conditions and type validation
            
        Success Criteria:
            - Valid TTL values pass validation
            - Invalid TTL values raise ValidationError
        """
        # Valid TTL values
        valid_ttls = [0, 1, 3600, 86400, 86400 * 365]  # 0 to 1 year
        
        for ttl in valid_ttls:
            self.factory._validate_factory_inputs(default_ttl=ttl)
        
        # Invalid TTL values
        invalid_ttls = [
            -1,              # Negative
            86400 * 366,     # Over 1 year
            "3600",          # String
            3.14             # Float
        ]
        
        for ttl in invalid_ttls:
            with pytest.raises(ValidationError) as exc_info:
                self.factory._validate_factory_inputs(default_ttl=ttl)
            
            assert "default_ttl" in str(exc_info.value).lower()
    
    def test_validate_fail_on_connection_error_type(self):
        """
        Test fail_on_connection_error validation per docstring type requirements.
        
        Business Impact:
            Ensures connection error handling behavior is properly specified
            
        Test Scenario:
            Test boolean type validation for fail_on_connection_error
            
        Success Criteria:
            - Boolean values pass validation
            - Non-boolean values raise ValidationError
        """
        # Valid boolean values
        for value in [True, False]:
            self.factory._validate_factory_inputs(fail_on_connection_error=value)
        
        # Invalid non-boolean values
        invalid_values = ["true", 1, 0, None]
        
        for value in invalid_values:
            with pytest.raises(ValidationError) as exc_info:
                self.factory._validate_factory_inputs(fail_on_connection_error=value)
            
            assert "fail_on_connection_error" in str(exc_info.value).lower()
    
    def test_validate_additional_parameters(self):
        """
        Test validation of additional parameters per docstring kwargs support.
        
        Business Impact:
            Ensures extended parameters are properly validated for cache configuration
            
        Test Scenario:
            Test validation of optional cache configuration parameters
            
        Success Criteria:
            - Valid additional parameters pass validation
            - Invalid additional parameters raise ValidationError
        """
        # Valid additional parameters
        valid_params = {
            "enable_l1_cache": True,
            "l1_cache_size": 100,
            "compression_threshold": 1000,
            "compression_level": 6
        }
        
        self.factory._validate_factory_inputs(**valid_params)
        
        # Invalid additional parameters
        invalid_params = [
            {"enable_l1_cache": "true"},        # Not boolean
            {"l1_cache_size": 0},               # Not positive
            {"compression_threshold": -1},       # Negative
            {"compression_level": 10}           # Out of range
        ]
        
        for params in invalid_params:
            with pytest.raises(ValidationError):
                self.factory._validate_factory_inputs(**params)
    
    def test_validation_error_context(self):
        """
        Test that validation errors include proper context per docstring.
        
        Business Impact:
            Ensures validation errors provide detailed debugging information
            
        Test Scenario:
            Trigger validation error and verify context information
            
        Success Criteria:
            - ValidationError includes context data
            - Context contains parameter values and error details
        """
        with pytest.raises(ValidationError) as exc_info:
            self.factory._validate_factory_inputs(
                redis_url="invalid-url",
                default_ttl=-100
            )
        
        error = exc_info.value
        assert hasattr(error, 'context')
        context = error.context
        
        assert "validation_errors" in context
        assert "redis_url" in context
        assert "default_ttl" in context
        assert len(context["validation_errors"]) >= 2


class TestWebAppCacheFactory:
    """
    Test for_web_app factory method for web application cache creation.
    
    Business Impact:
        Web application cache factory provides balanced performance caching for
        typical web workloads. Failures could impact session management, API
        response caching, and overall web application performance.
    """
    
    def setup_method(self):
        """Set up factory instance and mocks for testing."""
        self.factory = CacheFactory()
    
    @pytest.mark.asyncio
    @patch('app.infrastructure.cache.factory.GenericRedisCache')
    async def test_for_web_app_successful_creation(self, mock_redis_cache_class):
        """
        Test successful web app cache creation per docstring behavior.
        
        Business Impact:
            Ensures web applications get properly configured cache instances
            
        Test Scenario:
            Create web app cache with valid parameters and successful Redis connection
            
        Success Criteria:
            - GenericRedisCache is created with web-optimized defaults
            - Redis connection is tested
            - Configured cache instance is returned
        """
        # Mock cache instance
        mock_cache = AsyncMock(spec=CacheInterface)
        mock_cache.connect.return_value = True
        mock_redis_cache_class.return_value = mock_cache
        
        # Create web app cache
        result = await self.factory.for_web_app(
            redis_url="redis://test:6379",
            default_ttl=1800
        )
        
        # Verify cache creation
        mock_redis_cache_class.assert_called_once_with(
            redis_url="redis://test:6379",
            default_ttl=1800,
            enable_l1_cache=True,
            l1_cache_size=200,
            compression_threshold=2000,
            compression_level=6,
            performance_monitor=self.factory._performance_monitor
        )
        
        # Verify connection test
        mock_cache.connect.assert_called_once()
        
        # Verify result
        assert result is mock_cache
    
    @pytest.mark.asyncio
    @patch('app.infrastructure.cache.factory.GenericRedisCache')
    @patch('app.infrastructure.cache.factory.InMemoryCache')
    async def test_for_web_app_redis_failure_fallback(self, mock_memory_cache_class, mock_redis_cache_class):
        """
        Test web app cache fallback to InMemoryCache when Redis fails.
        
        Business Impact:
            Ensures web applications continue functioning with fallback cache
            when Redis is unavailable, preventing service outages
            
        Test Scenario:
            Redis connection fails, should fallback to InMemoryCache
            
        Success Criteria:
            - GenericRedisCache creation is attempted
            - Connection failure detected
            - InMemoryCache is created as fallback
            - Warning is logged
        """
        # Mock failed Redis cache
        mock_redis_cache = AsyncMock(spec=CacheInterface)
        mock_redis_cache.connect.return_value = False
        mock_redis_cache_class.return_value = mock_redis_cache
        
        # Mock memory cache
        mock_memory_cache = MagicMock(spec=InMemoryCache)
        mock_memory_cache_class.return_value = mock_memory_cache
        
        with patch('app.infrastructure.cache.factory.logger') as mock_logger:
            result = await self.factory.for_web_app()
            
            # Verify fallback creation
            mock_memory_cache_class.assert_called_once_with(
                default_ttl=1800,
                max_size=200
            )
            
            # Verify warning logged
            mock_logger.warning.assert_called()
            assert "Redis connection failed, falling back" in mock_logger.warning.call_args[0][0]
            
            # Verify result
            assert result is mock_memory_cache
    
    @pytest.mark.asyncio
    async def test_for_web_app_validation_error(self):
        """
        Test web app cache creation with invalid parameters per docstring.
        
        Business Impact:
            Prevents cache creation with invalid configurations that could
            cause runtime errors or performance issues
            
        Test Scenario:
            Call for_web_app with invalid parameters
            
        Success Criteria:
            - ValidationError is raised with parameter details
        """
        with pytest.raises(ValidationError):
            await self.factory.for_web_app(
                redis_url="invalid-url",
                default_ttl=-100
            )
    
    @pytest.mark.asyncio
    @patch('app.infrastructure.cache.factory.GenericRedisCache')
    async def test_for_web_app_fail_on_connection_error_true(self, mock_redis_cache_class):
        """
        Test web app cache with fail_on_connection_error=True per docstring.
        
        Business Impact:
            Allows strict environments to require Redis availability instead
            of falling back to memory cache
            
        Test Scenario:
            Redis connection fails with fail_on_connection_error=True
            
        Success Criteria:
            - InfrastructureError is raised instead of fallback
            - Error includes context information
        """
        # Mock failed Redis cache
        mock_redis_cache = AsyncMock(spec=CacheInterface)
        mock_redis_cache.connect.return_value = False
        mock_redis_cache_class.return_value = mock_redis_cache
        
        with pytest.raises(InfrastructureError) as exc_info:
            await self.factory.for_web_app(fail_on_connection_error=True)
        
        error = exc_info.value
        assert "Redis connection failed" in str(error)
        assert hasattr(error, 'context')
        assert error.context["cache_type"] == "web_app"
        assert error.context["fail_on_connection_error"] is True
    
    @pytest.mark.asyncio
    @patch('app.infrastructure.cache.factory.GenericRedisCache')
    async def test_for_web_app_custom_parameters(self, mock_redis_cache_class):
        """
        Test web app cache creation with custom parameters per docstring examples.
        
        Business Impact:
            Allows fine-tuning web application cache configuration for specific
            performance requirements
            
        Test Scenario:
            Create web app cache with custom performance parameters
            
        Success Criteria:
            - Custom parameters are passed to GenericRedisCache
            - All parameters are validated and applied
        """
        mock_cache = AsyncMock(spec=CacheInterface)
        mock_cache.connect.return_value = True
        mock_redis_cache_class.return_value = mock_cache
        
        result = await self.factory.for_web_app(
            redis_url="redis://production:6379",
            default_ttl=3600,
            l1_cache_size=500,
            compression_threshold=5000,
            compression_level=9,
            custom_param="test_value"
        )
        
        # Verify custom parameters passed
        mock_redis_cache_class.assert_called_once_with(
            redis_url="redis://production:6379",
            default_ttl=3600,
            enable_l1_cache=True,
            l1_cache_size=500,
            compression_threshold=5000,
            compression_level=9,
            performance_monitor=self.factory._performance_monitor,
            custom_param="test_value"
        )


class TestAIAppCacheFactory:
    """
    Test for_ai_app factory method for AI application cache creation.
    
    Business Impact:
        AI application cache factory provides optimized caching for AI workloads
        with enhanced compression and operation-specific TTLs. Failures could
        impact AI response caching and system performance for AI operations.
    """
    
    def setup_method(self):
        """Set up factory instance for testing."""
        self.factory = CacheFactory()
    
    @pytest.mark.asyncio
    @patch('app.infrastructure.cache.factory.AIResponseCache')
    async def test_for_ai_app_successful_creation(self, mock_ai_cache_class):
        """
        Test successful AI app cache creation per docstring behavior.
        
        Business Impact:
            Ensures AI applications get properly configured cache instances
            with AI-specific optimizations
            
        Test Scenario:
            Create AI app cache with valid parameters and successful Redis connection
            
        Success Criteria:
            - AIResponseCache is created with AI-optimized defaults
            - Redis connection is tested
            - Configured cache instance is returned
        """
        # Mock cache instance
        mock_cache = AsyncMock(spec=CacheInterface)
        mock_cache.connect.return_value = True
        mock_ai_cache_class.return_value = mock_cache
        
        # Create AI app cache
        result = await self.factory.for_ai_app(
            redis_url="redis://ai:6379",
            default_ttl=3600
        )
        
        # Verify cache creation with AI defaults
        mock_ai_cache_class.assert_called_once_with(
            redis_url="redis://ai:6379",
            default_ttl=3600,
            memory_cache_size=100,
            compression_threshold=1000,
            compression_level=6,
            text_hash_threshold=500,
            operation_ttls={},
            performance_monitor=self.factory._performance_monitor
        )
        
        # Verify connection test
        mock_cache.connect.assert_called_once()
        
        # Verify result
        assert result is mock_cache
    
    @pytest.mark.asyncio
    async def test_for_ai_app_ai_specific_validation(self):
        """
        Test AI-specific parameter validation per docstring requirements.
        
        Business Impact:
            Ensures AI cache parameters are properly validated to prevent
            configuration errors specific to AI workloads
            
        Test Scenario:
            Test validation of AI-specific parameters
            
        Success Criteria:
            - Valid AI parameters pass validation
            - Invalid AI parameters raise ValidationError
        """
        # Test invalid text_hash_threshold
        with pytest.raises(ValidationError) as exc_info:
            await self.factory.for_ai_app(text_hash_threshold="invalid")
        
        assert "text_hash_threshold" in str(exc_info.value).lower()
        
        # Test invalid memory_cache_size
        with pytest.raises(ValidationError):
            await self.factory.for_ai_app(memory_cache_size=-1)
        
        # Test invalid operation_ttls
        with pytest.raises(ValidationError):
            await self.factory.for_ai_app(operation_ttls="invalid")
        
        # Test invalid operation_ttls values
        with pytest.raises(ValidationError):
            await self.factory.for_ai_app(operation_ttls={"op1": -1})
    
    @pytest.mark.asyncio
    @patch('app.infrastructure.cache.factory.AIResponseCache')
    async def test_for_ai_app_with_operation_ttls(self, mock_ai_cache_class):
        """
        Test AI app cache creation with operation-specific TTLs per docstring.
        
        Business Impact:
            Enables fine-grained caching control for different AI operations
            to optimize cache performance and resource usage
            
        Test Scenario:
            Create AI cache with custom operation TTLs
            
        Success Criteria:
            - Operation TTLs are passed to AIResponseCache
            - Parameters are validated correctly
        """
        mock_cache = AsyncMock(spec=CacheInterface)
        mock_cache.connect.return_value = True
        mock_ai_cache_class.return_value = mock_cache
        
        operation_ttls = {
            "summarize": 1800,
            "sentiment": 3600,
            "translate": 7200
        }
        
        result = await self.factory.for_ai_app(
            operation_ttls=operation_ttls
        )
        
        # Verify operation TTLs passed
        call_args = mock_ai_cache_class.call_args
        assert call_args.kwargs["operation_ttls"] == operation_ttls
    
    @pytest.mark.asyncio
    @patch('app.infrastructure.cache.factory.AIResponseCache')
    async def test_for_ai_app_memory_cache_size_override(self, mock_ai_cache_class):
        """
        Test AI app cache with memory_cache_size override per docstring.
        
        Business Impact:
            Allows overriding L1 cache size for AI-specific memory requirements
            
        Test Scenario:
            Create AI cache with memory_cache_size overriding l1_cache_size
            
        Success Criteria:
            - memory_cache_size is used instead of l1_cache_size
        """
        mock_cache = AsyncMock(spec=CacheInterface)
        mock_cache.connect.return_value = True
        mock_ai_cache_class.return_value = mock_cache
        
        result = await self.factory.for_ai_app(
            l1_cache_size=100,
            memory_cache_size=200  # Should override l1_cache_size
        )
        
        # Verify memory_cache_size is used
        call_args = mock_ai_cache_class.call_args
        assert call_args.kwargs["memory_cache_size"] == 200
    
    @pytest.mark.asyncio
    @patch('app.infrastructure.cache.factory.AIResponseCache')
    @patch('app.infrastructure.cache.factory.InMemoryCache')
    async def test_for_ai_app_fallback_with_memory_cache_size(self, mock_memory_cache_class, mock_ai_cache_class):
        """
        Test AI app cache fallback uses correct memory_cache_size per docstring.
        
        Business Impact:
            Ensures fallback cache maintains consistent memory usage configuration
            
        Test Scenario:
            Redis connection fails with custom memory_cache_size
            
        Success Criteria:
            - InMemoryCache uses memory_cache_size when provided
            - Fallback maintains AI cache sizing
        """
        # Mock failed AI cache
        mock_ai_cache = AsyncMock(spec=CacheInterface)
        mock_ai_cache.connect.return_value = False
        mock_ai_cache_class.return_value = mock_ai_cache
        
        # Mock memory cache
        mock_memory_cache = MagicMock(spec=InMemoryCache)
        mock_memory_cache_class.return_value = mock_memory_cache
        
        await self.factory.for_ai_app(
            memory_cache_size=150,
            fail_on_connection_error=False
        )
        
        # Verify fallback uses memory_cache_size
        mock_memory_cache_class.assert_called_once_with(
            default_ttl=3600,
            max_size=150  # Uses memory_cache_size, not l1_cache_size
        )


class TestTestingCacheFactory:
    """
    Test for_testing factory method for testing environment cache creation.
    
    Business Impact:
        Testing cache factory provides optimized caching for test environments
        with short TTLs and minimal resource usage. Failures could impact
        test reliability and development workflow efficiency.
    """
    
    def setup_method(self):
        """Set up factory instance for testing."""
        self.factory = CacheFactory()
    
    @pytest.mark.asyncio
    @patch('app.infrastructure.cache.factory.InMemoryCache')
    async def test_for_testing_memory_cache_forced(self, mock_memory_cache_class):
        """
        Test testing cache with use_memory_cache=True per docstring.
        
        Business Impact:
            Enables isolated testing with guaranteed in-memory cache behavior
            
        Test Scenario:
            Force InMemoryCache usage for test isolation
            
        Success Criteria:
            - InMemoryCache is created directly
            - Redis connection is not attempted
        """
        mock_memory_cache = MagicMock(spec=InMemoryCache)
        mock_memory_cache_class.return_value = mock_memory_cache
        
        result = await self.factory.for_testing(
            use_memory_cache=True,
            default_ttl=30,
            l1_cache_size=25
        )
        
        # Verify memory cache creation
        mock_memory_cache_class.assert_called_once_with(
            default_ttl=30,
            max_size=25
        )
        
        assert result is mock_memory_cache
    
    @pytest.mark.asyncio
    async def test_for_testing_use_memory_cache_validation(self):
        """
        Test validation of use_memory_cache parameter per docstring type requirements.
        
        Business Impact:
            Ensures testing cache behavior is properly specified
            
        Test Scenario:
            Test boolean type validation for use_memory_cache
            
        Success Criteria:
            - Boolean values pass validation
            - Non-boolean values raise ValidationError
        """
        # Valid boolean values should work
        await self.factory.for_testing(use_memory_cache=True)
        await self.factory.for_testing(use_memory_cache=False)
        
        # Invalid values should raise ValidationError
        with pytest.raises(ValidationError) as exc_info:
            await self.factory.for_testing(use_memory_cache="true")
        
        assert "use_memory_cache must be a boolean" in str(exc_info.value)
    
    @pytest.mark.asyncio
    @patch('app.infrastructure.cache.factory.GenericRedisCache')
    async def test_for_testing_redis_cache_creation(self, mock_redis_cache_class):
        """
        Test testing cache with Redis configuration per docstring defaults.
        
        Business Impact:
            Allows testing with Redis when test isolation isn't required
            
        Test Scenario:
            Create testing cache with Redis using test database defaults
            
        Success Criteria:
            - GenericRedisCache created with testing optimizations
            - Test database URL is used by default
            - Fast compression and short TTLs configured
        """
        mock_cache = AsyncMock(spec=CacheInterface)
        mock_cache.connect.return_value = True
        mock_redis_cache_class.return_value = mock_cache
        
        result = await self.factory.for_testing()
        
        # Verify testing-optimized configuration
        mock_redis_cache_class.assert_called_once_with(
            redis_url="redis://redis:6379/15",  # Test database 15
            default_ttl=60,                      # 1 minute
            enable_l1_cache=False,              # Simplified for testing
            l1_cache_size=50,
            compression_threshold=1000,
            compression_level=1,                 # Fast compression
            performance_monitor=self.factory._performance_monitor
        )
    
    @pytest.mark.asyncio
    @patch('app.infrastructure.cache.factory.GenericRedisCache')
    async def test_for_testing_custom_test_database(self, mock_redis_cache_class):
        """
        Test testing cache with custom test database per docstring examples.
        
        Business Impact:
            Allows test isolation using different Redis test databases
            
        Test Scenario:
            Create testing cache with custom test database URL
            
        Success Criteria:
            - Custom Redis URL is used
            - Other testing optimizations maintained
        """
        mock_cache = AsyncMock(spec=CacheInterface)
        mock_cache.connect.return_value = True
        mock_redis_cache_class.return_value = mock_cache
        
        custom_url = "redis://test-server:6379/10"
        result = await self.factory.for_testing(
            redis_url=custom_url,
            default_ttl=30
        )
        
        # Verify custom configuration
        call_args = mock_redis_cache_class.call_args
        assert call_args.kwargs["redis_url"] == custom_url
        assert call_args.kwargs["default_ttl"] == 30


class TestConfigBasedCacheFactory:
    """
    Test create_cache_from_config method for configuration-driven cache creation.
    
    Business Impact:
        Configuration-based cache factory enables flexible cache setup from
        external configuration sources. Failures could prevent dynamic cache
        configuration and limit deployment flexibility.
    """
    
    def setup_method(self):
        """Set up factory instance for testing."""
        self.factory = CacheFactory()
    
    @pytest.mark.asyncio
    async def test_create_cache_from_config_validation_errors(self):
        """
        Test configuration validation per docstring requirements.
        
        Business Impact:
            Prevents cache creation with invalid configurations that could
            cause runtime errors
            
        Test Scenario:
            Test various configuration validation scenarios
            
        Success Criteria:
            - Non-dict config raises ValidationError
            - Empty config raises ValidationError
            - Missing redis_url raises ValidationError
        """
        # Test non-dict config
        with pytest.raises(ValidationError) as exc_info:
            await self.factory.create_cache_from_config("not-a-dict")
        
        assert "config must be a dictionary" in str(exc_info.value)
        
        # Test empty config
        with pytest.raises(ValidationError):
            await self.factory.create_cache_from_config({})
        
        # Test missing redis_url
        with pytest.raises(ValidationError) as exc_info:
            await self.factory.create_cache_from_config({"default_ttl": 3600})
        
        assert "redis_url is required" in str(exc_info.value)
    
    @pytest.mark.asyncio
    @patch('app.infrastructure.cache.factory.CacheFactory.for_web_app')
    async def test_create_cache_from_config_generic_cache(self, mock_for_web_app):
        """
        Test configuration-based creation of GenericRedisCache per docstring detection.
        
        Business Impact:
            Enables automatic detection and creation of appropriate cache type
            based on configuration parameters
            
        Test Scenario:
            Configuration without AI-specific parameters creates GenericRedisCache
            
        Success Criteria:
            - for_web_app method is called with correct parameters
            - No AI-specific parameters are passed
        """
        mock_cache = AsyncMock(spec=CacheInterface)
        mock_for_web_app.return_value = mock_cache
        
        config = {
            "redis_url": "redis://localhost:6379",
            "default_ttl": 3600,
            "enable_l1_cache": True,
            "compression_threshold": 2000,
            "custom_param": "test_value"
        }
        
        result = await self.factory.create_cache_from_config(config)
        
        # Verify for_web_app called with correct parameters
        mock_for_web_app.assert_called_once_with(
            redis_url="redis://localhost:6379",
            default_ttl=3600,
            enable_l1_cache=True,
            l1_cache_size=100,  # Default value
            compression_threshold=2000,
            compression_level=6,  # Default value
            fail_on_connection_error=False,
            custom_param="test_value"
        )
        
        assert result is mock_cache
    
    @pytest.mark.asyncio
    @patch('app.infrastructure.cache.factory.CacheFactory.for_ai_app')
    async def test_create_cache_from_config_ai_cache(self, mock_for_ai_app):
        """
        Test configuration-based creation of AIResponseCache per docstring detection.
        
        Business Impact:
            Enables automatic detection and creation of AI-optimized cache when
            AI-specific parameters are present
            
        Test Scenario:
            Configuration with AI-specific parameters creates AIResponseCache
            
        Success Criteria:
            - for_ai_app method is called with AI-specific parameters
            - AI parameters are properly mapped
        """
        mock_cache = AsyncMock(spec=CacheInterface)
        mock_for_ai_app.return_value = mock_cache
        
        config = {
            "redis_url": "redis://ai-cache:6379",
            "default_ttl": 7200,
            "text_hash_threshold": 500,  # AI-specific parameter
            "operation_ttls": {"summarize": 1800},  # AI-specific parameter
            "memory_cache_size": 150,  # AI-specific parameter
            "compression_threshold": 1000
        }
        
        result = await self.factory.create_cache_from_config(config)
        
        # Verify for_ai_app called with AI parameters
        mock_for_ai_app.assert_called_once_with(
            redis_url="redis://ai-cache:6379",
            default_ttl=7200,
            enable_l1_cache=True,  # Default value
            l1_cache_size=100,     # Default value
            compression_threshold=1000,
            compression_level=6,   # Default value
            text_hash_threshold=500,
            memory_cache_size=150,
            operation_ttls={"summarize": 1800},
            fail_on_connection_error=False
        )
        
        assert result is mock_cache
    
    @pytest.mark.asyncio
    @patch('app.infrastructure.cache.factory.CacheFactory.for_web_app')
    async def test_create_cache_from_config_fail_on_connection_error(self, mock_for_web_app):
        """
        Test configuration-based creation with fail_on_connection_error per docstring.
        
        Business Impact:
            Allows strict configuration requiring Redis availability
            
        Test Scenario:
            Create cache with fail_on_connection_error=True
            
        Success Criteria:
            - fail_on_connection_error parameter is passed correctly
        """
        mock_cache = AsyncMock(spec=CacheInterface)
        mock_for_web_app.return_value = mock_cache
        
        config = {"redis_url": "redis://localhost:6379"}
        
        result = await self.factory.create_cache_from_config(
            config, 
            fail_on_connection_error=True
        )
        
        # Verify fail_on_connection_error parameter passed
        call_args = mock_for_web_app.call_args
        assert call_args.kwargs["fail_on_connection_error"] is True
    
    @pytest.mark.asyncio
    @patch('app.infrastructure.cache.factory.CacheFactory.for_web_app')
    async def test_create_cache_from_config_error_handling(self, mock_for_web_app):
        """
        Test configuration-based cache creation error handling per docstring.
        
        Business Impact:
            Ensures proper error handling and context information for
            configuration-based cache creation failures
            
        Test Scenario:
            Underlying factory method raises exception
            
        Success Criteria:
            - ConfigurationError is raised with context
            - Original error is preserved in context
        """
        # Mock underlying method to raise exception
        original_error = ValueError("Test error")
        mock_for_web_app.side_effect = original_error
        
        config = {"redis_url": "redis://localhost:6379"}
        
        with pytest.raises(ConfigurationError) as exc_info:
            await self.factory.create_cache_from_config(config)
        
        error = exc_info.value
        assert "Failed to create cache from configuration" in str(error)
        assert hasattr(error, 'context')
        
        context = error.context
        assert context["config"] == config
        assert context["has_ai_params"] is False
        assert context["fail_on_connection_error"] is False
        assert context["original_error"] == str(original_error)


class TestFactoryErrorHandling:
    """
    Test error handling and exception propagation across factory methods.
    
    Business Impact:
        Proper error handling ensures cache factory failures are properly
        diagnosed and handled, preventing silent failures that could impact
        application performance and reliability.
    """
    
    def setup_method(self):
        """Set up factory instance for testing."""
        self.factory = CacheFactory()
    
    @pytest.mark.asyncio
    @patch('app.infrastructure.cache.factory.GenericRedisCache')
    async def test_factory_method_exception_handling(self, mock_redis_cache_class):
        """
        Test factory method exception handling per docstring error handling.
        
        Business Impact:
            Ensures factory methods handle unexpected errors gracefully
            with proper context information
            
        Test Scenario:
            Cache creation raises unexpected exception
            
        Success Criteria:
            - Known exceptions are re-raised as-is
            - Unknown exceptions are wrapped with context
            - Fallback behavior is triggered when appropriate
        """
        # Test that ValidationError is re-raised as-is
        mock_redis_cache_class.side_effect = ValidationError("Test validation error")
        
        with pytest.raises(ValidationError):
            await self.factory.for_web_app()
        
        # Test that ConfigurationError is re-raised as-is
        mock_redis_cache_class.side_effect = ConfigurationError("Test config error")
        
        with pytest.raises(ConfigurationError):
            await self.factory.for_web_app()
        
        # Test that InfrastructureError is re-raised as-is
        mock_redis_cache_class.side_effect = InfrastructureError("Test infra error")
        
        with pytest.raises(InfrastructureError):
            await self.factory.for_web_app()
    
    @pytest.mark.asyncio
    @patch('app.infrastructure.cache.factory.GenericRedisCache')
    @patch('app.infrastructure.cache.factory.InMemoryCache')
    async def test_unexpected_exception_fallback(self, mock_memory_cache_class, mock_redis_cache_class):
        """
        Test fallback behavior on unexpected exceptions per docstring.
        
        Business Impact:
            Ensures application continues functioning even when cache factory
            encounters unexpected errors
            
        Test Scenario:
            Unexpected exception during cache creation triggers fallback
            
        Success Criteria:
            - Unexpected exception triggers fallback to InMemoryCache
            - Error is logged appropriately
            - Application continues functioning
        """
        # Mock unexpected exception
        mock_redis_cache_class.side_effect = RuntimeError("Unexpected error")
        
        # Mock memory cache fallback
        mock_memory_cache = MagicMock(spec=InMemoryCache)
        mock_memory_cache_class.return_value = mock_memory_cache
        
        with patch('app.infrastructure.cache.factory.logger') as mock_logger:
            result = await self.factory.for_web_app(fail_on_connection_error=False)
            
            # Verify fallback occurred
            assert result is mock_memory_cache
            
            # Verify error was logged
            mock_logger.error.assert_called()
            mock_logger.info.assert_called_with(
                "Falling back to InMemoryCache due to cache creation error"
            )
    
    @pytest.mark.asyncio
    @patch('app.infrastructure.cache.factory.GenericRedisCache')
    async def test_unexpected_exception_with_fail_on_error(self, mock_redis_cache_class):
        """
        Test unexpected exception handling with fail_on_connection_error=True.
        
        Business Impact:
            Allows strict environments to prevent fallback and require
            proper cache configuration
            
        Test Scenario:
            Unexpected exception with strict error handling
            
        Success Criteria:
            - InfrastructureError is raised with context
            - No fallback occurs
        """
        # Mock unexpected exception
        original_error = RuntimeError("Unexpected error")
        mock_redis_cache_class.side_effect = original_error
        
        with pytest.raises(InfrastructureError) as exc_info:
            await self.factory.for_web_app(fail_on_connection_error=True)
        
        error = exc_info.value
        assert "Failed to create web application cache" in str(error)
        assert hasattr(error, 'context')
        assert error.context["original_error"] == str(original_error)


class TestFactoryIntegration:
    """
    Test integration scenarios across factory methods and cache types.
    
    Business Impact:
        Integration testing ensures factory methods work correctly together
        and produce consistent cache instances across different use cases.
        Failures could lead to inconsistent cache behavior in applications.
    """
    
    def setup_method(self):
        """Set up factory instance for testing."""
        self.factory = CacheFactory()
    
    @pytest.mark.asyncio
    @patch('app.infrastructure.cache.factory.CacheFactory.for_web_app')
    @patch('app.infrastructure.cache.factory.CacheFactory.for_ai_app')
    async def test_config_based_factory_method_selection(self, mock_for_ai_app, mock_for_web_app):
        """
        Test automatic factory method selection based on configuration.
        
        Business Impact:
            Ensures configuration-driven cache creation selects appropriate
            cache type based on parameter presence
            
        Test Scenario:
            Test both web and AI cache selection logic
            
        Success Criteria:
            - Configurations without AI params use for_web_app
            - Configurations with AI params use for_ai_app
        """
        mock_web_cache = AsyncMock(spec=CacheInterface)
        mock_ai_cache = AsyncMock(spec=CacheInterface)
        mock_for_web_app.return_value = mock_web_cache
        mock_for_ai_app.return_value = mock_ai_cache
        
        # Test web cache selection
        web_config = {
            "redis_url": "redis://localhost:6379",
            "default_ttl": 3600,
            "enable_l1_cache": True
        }
        
        result = await self.factory.create_cache_from_config(web_config)
        
        mock_for_web_app.assert_called_once()
        mock_for_ai_app.assert_not_called()
        assert result is mock_web_cache
        
        # Reset mocks
        mock_for_web_app.reset_mock()
        mock_for_ai_app.reset_mock()
        
        # Test AI cache selection
        ai_config = {
            "redis_url": "redis://ai:6379",
            "default_ttl": 7200,
            "text_hash_threshold": 500  # AI-specific parameter
        }
        
        result = await self.factory.create_cache_from_config(ai_config)
        
        mock_for_ai_app.assert_called_once()
        mock_for_web_app.assert_not_called()
        assert result is mock_ai_cache
    
    @pytest.mark.asyncio
    async def test_factory_parameter_consistency(self):
        """
        Test parameter consistency across factory methods.
        
        Business Impact:
            Ensures all factory methods handle common parameters consistently
            
        Test Scenario:
            Test common parameter validation across methods
            
        Success Criteria:
            - Common parameters are validated consistently
            - Validation errors have consistent format
        """
        common_invalid_params = {
            "redis_url": "invalid-url",
            "default_ttl": -100
        }
        
        # Test all factory methods with same invalid parameters
        factory_methods = [
            self.factory.for_web_app,
            self.factory.for_ai_app,
            self.factory.for_testing
        ]
        
        for method in factory_methods:
            with pytest.raises(ValidationError) as exc_info:
                await method(**common_invalid_params)
            
            # Verify consistent error handling
            error_msg = str(exc_info.value).lower()
            assert "redis_url" in error_msg
            assert "default_ttl" in error_msg
    
    def test_factory_logging_consistency(self):
        """
        Test logging consistency across factory methods.
        
        Business Impact:
            Ensures consistent logging for monitoring and debugging
            
        Test Scenario:
            Verify factory initialization logging
            
        Success Criteria:
            - Factory initialization is logged consistently
        """
        with patch('app.infrastructure.cache.factory.logger') as mock_logger:
            factory = CacheFactory()
            
            # Verify consistent initialization logging
            mock_logger.info.assert_called_with("CacheFactory initialized")