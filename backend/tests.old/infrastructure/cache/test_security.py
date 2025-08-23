"""
Test suite for Redis Cache Security Implementation

This module provides comprehensive tests for the security features including:
- SecurityConfig validation and initialization
- RedisCacheSecurityManager functionality 
- Security validation and reporting
- Integration with GenericRedisCache
- Environment configuration
- Error handling and edge cases

Author: Cache Infrastructure Team
Created: 2024-08-12
"""

import asyncio
import ssl
import pytest
import os
import tempfile
from unittest.mock import AsyncMock, MagicMock, patch, mock_open
from typing import Dict, Any, Optional

# Import security components
from app.infrastructure.cache.security import (
    SecurityConfig,
    SecurityValidationResult,
    RedisCacheSecurityManager,
    create_security_config_from_env
)
from app.core.exceptions import ConfigurationError
from app.infrastructure.cache.monitoring import CachePerformanceMonitor
from app.infrastructure.cache.redis_generic import GenericRedisCache


class TestSecurityConfig:
    """Test SecurityConfig dataclass and validation."""
    
    def test_default_security_config(self):
        """Test default SecurityConfig initialization."""
        config = SecurityConfig()
        
        assert config.redis_auth is None
        assert config.acl_username is None
        assert config.acl_password is None
        assert config.use_tls is False
        assert config.verify_certificates is True
        assert config.connection_timeout == 30
        assert config.socket_timeout == 30
        assert config.max_retries == 3
        assert config.retry_delay == 1.0
        assert config.enable_security_monitoring is True
        assert config.log_security_events is True
        
        # Test computed properties
        assert config.has_authentication is False
        assert config.security_level == "LOW"
    
    def test_auth_password_config(self):
        """Test SecurityConfig with AUTH password."""
        config = SecurityConfig(redis_auth="test_password")
        
        assert config.redis_auth == "test_password"
        assert config.has_authentication is True
        assert config.security_level == "MEDIUM"
    
    def test_acl_config(self):
        """Test SecurityConfig with ACL authentication."""
        config = SecurityConfig(
            acl_username="cache_user",
            acl_password="secure_password"
        )
        
        assert config.acl_username == "cache_user"
        assert config.acl_password == "secure_password" 
        assert config.has_authentication is True
        assert config.security_level == "MEDIUM"
    
    def test_tls_config(self):
        """Test SecurityConfig with TLS encryption."""
        config = SecurityConfig(use_tls=True)
        
        assert config.use_tls is True
        assert config.security_level == "MEDIUM"
    
    def test_high_security_config(self):
        """Test SecurityConfig with all security features enabled."""
        config = SecurityConfig(
            redis_auth="fallback_password",
            use_tls=True,
            acl_username="cache_user",
            acl_password="secure_password",
            verify_certificates=True
        )
        
        assert config.has_authentication is True
        assert config.use_tls is True
        assert config.verify_certificates is True
        assert config.security_level == "HIGH"
    
    def test_config_validation_success(self):
        """Test successful configuration validation."""
        # Should not raise any exceptions
        config = SecurityConfig(
            redis_auth="password",
            use_tls=True,
            connection_timeout=30,
            socket_timeout=30,
            max_retries=3,
            retry_delay=1.0
        )
        config._validate_configuration()  # Should not raise
    
    def test_config_validation_acl_missing_password(self):
        """Test configuration validation with ACL username but no password."""
        with pytest.raises(ConfigurationError, match="ACL password is required"):
            SecurityConfig(acl_username="user")
    
    def test_config_validation_invalid_timeouts(self):
        """Test configuration validation with invalid timeout values."""
        with pytest.raises(ConfigurationError, match="Connection timeout must be positive"):
            SecurityConfig(connection_timeout=-1)
        
        with pytest.raises(ConfigurationError, match="Socket timeout must be positive"):
            SecurityConfig(socket_timeout=0)
    
    def test_config_validation_invalid_retries(self):
        """Test configuration validation with invalid retry values."""
        with pytest.raises(ConfigurationError, match="Max retries cannot be negative"):
            SecurityConfig(max_retries=-1)
        
        with pytest.raises(ConfigurationError, match="Retry delay cannot be negative"):
            SecurityConfig(retry_delay=-0.5)
    
    @patch('pathlib.Path.exists')
    def test_config_validation_missing_tls_files(self, mock_exists):
        """Test configuration validation with missing TLS certificate files."""
        mock_exists.return_value = False
        
        with pytest.raises(ConfigurationError, match="TLS certificate file not found"):
            SecurityConfig(use_tls=True, tls_cert_path="/nonexistent/cert.pem")
        
        with pytest.raises(ConfigurationError, match="TLS key file not found"):
            SecurityConfig(use_tls=True, tls_key_path="/nonexistent/key.pem")
        
        with pytest.raises(ConfigurationError, match="TLS CA file not found"):
            SecurityConfig(use_tls=True, tls_ca_path="/nonexistent/ca.pem")


class TestSecurityValidationResult:
    """Test SecurityValidationResult dataclass and scoring."""
    
    def test_default_validation_result(self):
        """Test default SecurityValidationResult initialization."""
        result = SecurityValidationResult(
            is_secure=False,
            auth_configured=False,
            tls_enabled=False,
            acl_enabled=False,
            certificate_valid=False
        )
        
        assert result.is_secure is False
        assert result.security_score >= 0
        assert result.security_score <= 100
        assert isinstance(result.vulnerabilities, list)
        assert isinstance(result.recommendations, list)
        assert isinstance(result.warnings, list)
        assert isinstance(result.detailed_checks, dict)
    
    def test_high_security_validation_result(self):
        """Test SecurityValidationResult with high security configuration."""
        result = SecurityValidationResult(
            is_secure=True,
            auth_configured=True,
            tls_enabled=True,
            acl_enabled=True,
            certificate_valid=True,
            connection_encrypted=True,
            certificate_expiry_days=180
        )
        
        assert result.is_secure is True
        assert result.security_score >= 80  # Should be high score
        assert result.auth_method is None  # Not set in initialization
    
    def test_security_score_calculation(self):
        """Test security score calculation logic."""
        # Test with authentication only
        result_auth = SecurityValidationResult(
            is_secure=False,
            auth_configured=True,
            tls_enabled=False,
            acl_enabled=False,
            certificate_valid=False
        )
        score_auth = result_auth.security_score
        
        # Test with TLS only
        result_tls = SecurityValidationResult(
            is_secure=False,
            auth_configured=False,
            tls_enabled=True,
            acl_enabled=False,
            certificate_valid=True,
            connection_encrypted=True
        )
        score_tls = result_tls.security_score
        
        # Test with both auth and TLS
        result_both = SecurityValidationResult(
            is_secure=True,
            auth_configured=True,
            tls_enabled=True,
            acl_enabled=True,
            certificate_valid=True,
            connection_encrypted=True
        )
        score_both = result_both.security_score
        
        # Combined should have higher score than individual components
        assert score_both > score_auth
        assert score_both > score_tls
    
    def test_security_summary_generation(self):
        """Test security summary string generation."""
        result = SecurityValidationResult(
            is_secure=False,
            auth_configured=True,
            tls_enabled=False,
            acl_enabled=False,
            certificate_valid=False,
            vulnerabilities=["Unencrypted connection", "Weak password"],
            recommendations=["Enable TLS", "Use stronger password"]
        )
        
        summary = result.get_security_summary()
        assert "INSECURE" in summary
        assert "Unencrypted connection" in summary
        assert "Enable TLS" in summary
        assert "Vulnerabilities (2)" in summary
        assert "Recommendations (2)" in summary


class TestRedisCacheSecurityManager:
    """Test RedisCacheSecurityManager functionality."""
    
    def setup_method(self):
        """Setup method run before each test."""
        self.performance_monitor = CachePerformanceMonitor()
        self.basic_config = SecurityConfig(redis_auth="test_password")
        self.tls_config = SecurityConfig(
            redis_auth="test_password",
            use_tls=True,
            verify_certificates=False  # For testing
        )
    
    def test_security_manager_initialization(self):
        """Test SecurityManager initialization."""
        manager = RedisCacheSecurityManager(
            config=self.basic_config,
            performance_monitor=self.performance_monitor
        )
        
        assert manager.config == self.basic_config
        assert manager.performance_monitor == self.performance_monitor
        assert manager._ssl_context is None  # No TLS configured
        assert isinstance(manager._security_events, list)
    
    def test_security_manager_ssl_initialization(self):
        """Test SecurityManager SSL context initialization."""
        manager = RedisCacheSecurityManager(
            config=self.tls_config,
            performance_monitor=self.performance_monitor
        )
        
        assert manager._ssl_context is not None
        assert isinstance(manager._ssl_context, ssl.SSLContext)
    
    def test_build_connection_kwargs_basic_auth(self):
        """Test connection kwargs building with basic AUTH."""
        manager = RedisCacheSecurityManager(self.basic_config)
        kwargs = manager._build_connection_kwargs("redis://localhost:6379")
        
        assert kwargs["password"] == "test_password"
        assert kwargs["socket_timeout"] == 30
        assert kwargs["socket_connect_timeout"] == 30
        assert kwargs["url"] == "redis://localhost:6379"
        assert "username" not in kwargs
        assert "ssl" not in kwargs
    
    def test_build_connection_kwargs_acl_auth(self):
        """Test connection kwargs building with ACL authentication."""
        acl_config = SecurityConfig(
            acl_username="cache_user",
            acl_password="user_password"
        )
        manager = RedisCacheSecurityManager(acl_config)
        kwargs = manager._build_connection_kwargs("redis://localhost:6379")
        
        assert kwargs["username"] == "cache_user"
        assert kwargs["password"] == "user_password"
        assert "ssl" not in kwargs
    
    def test_build_connection_kwargs_tls(self):
        """Test connection kwargs building with TLS."""
        manager = RedisCacheSecurityManager(self.tls_config)
        kwargs = manager._build_connection_kwargs("redis://localhost:6379")
        
        assert "ssl" in kwargs
        assert kwargs["ssl"] == manager._ssl_context
        assert kwargs["url"] == "rediss://localhost:6379"  # Should be updated to rediss://
    
    @pytest.mark.asyncio
    async def test_create_secure_connection_mock_success(self):
        """Test successful secure connection creation with mocked Redis."""
        manager = RedisCacheSecurityManager(self.basic_config)
        
        # Mock aioredis.from_url to return a mock Redis client
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock()
        mock_redis.info = AsyncMock(return_value={"redis_version": "6.2.0"})
        
        # Patch AIOREDIS_AVAILABLE to True and mock aioredis
        with patch('app.infrastructure.cache.security.AIOREDIS_AVAILABLE', True):
            with patch('app.infrastructure.cache.security.aioredis') as mock_aioredis:
                mock_aioredis.from_url = AsyncMock(return_value=mock_redis)
                
                redis_client = await manager.create_secure_connection()
                
                assert redis_client == mock_redis
                mock_redis.ping.assert_called_once()
                mock_redis.info.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_create_secure_connection_retry_logic(self):
        """Test connection retry logic with failures."""
        config = SecurityConfig(redis_auth="password", max_retries=2, retry_delay=0.1)
        manager = RedisCacheSecurityManager(config)
        
        # Mock aioredis.from_url to fail first two times, succeed third time
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock()
        mock_redis.info = AsyncMock(return_value={"redis_version": "6.2.0"})
        
        call_count = 0
        def side_effect(*args, **kwargs):
            nonlocal call_count
            call_count += 1
            if call_count <= 2:
                raise Exception("Connection failed")
            return mock_redis
        
        with patch('app.infrastructure.cache.security.AIOREDIS_AVAILABLE', True):
            with patch('app.infrastructure.cache.security.aioredis') as mock_aioredis:
                mock_aioredis.from_url = AsyncMock(side_effect=side_effect)
                
                redis_client = await manager.create_secure_connection()
                
                assert redis_client == mock_redis
                assert call_count == 3  # Failed twice, succeeded on third try
    
    @pytest.mark.asyncio
    async def test_create_secure_connection_max_retries_exceeded(self):
        """Test connection failure after max retries exceeded."""
        config = SecurityConfig(redis_auth="password", max_retries=1, retry_delay=0.1)
        manager = RedisCacheSecurityManager(config)
        
        # Mock aioredis to always fail
        with patch('app.infrastructure.cache.security.AIOREDIS_AVAILABLE', True):
            with patch('app.infrastructure.cache.security.aioredis') as mock_aioredis:
                mock_aioredis.from_url = AsyncMock(side_effect=Exception("Connection failed"))
                
                with pytest.raises(Exception, match="Failed to establish secure Redis connection"):
                    await manager.create_secure_connection()
    
    @pytest.mark.asyncio
    async def test_validate_connection_security_basic(self):
        """Test basic security validation."""
        manager = RedisCacheSecurityManager(self.basic_config)
        
        # Mock Redis client
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock()
        mock_redis.info = AsyncMock(return_value={"redis_version": "6.2.0"})
        
        validation = await manager.validate_connection_security(mock_redis)
        
        assert isinstance(validation, SecurityValidationResult)
        assert validation.auth_configured is True
        assert validation.tls_enabled is False
        assert validation.acl_enabled is False
        assert "connectivity" in validation.detailed_checks
        assert "authentication" in validation.detailed_checks
    
    @pytest.mark.asyncio
    async def test_validate_connection_security_with_tls(self):
        """Test security validation with TLS configuration."""
        manager = RedisCacheSecurityManager(self.tls_config)
        
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock()
        mock_redis.info = AsyncMock(return_value={"redis_version": "6.2.0"})
        
        validation = await manager.validate_connection_security(mock_redis)
        
        assert validation.auth_configured is True
        assert validation.tls_enabled is True
        assert validation.connection_encrypted is True
        assert "encryption" in validation.detailed_checks
    
    @pytest.mark.asyncio
    async def test_validate_connection_security_connection_failure(self):
        """Test security validation with connection failure."""
        manager = RedisCacheSecurityManager(self.basic_config)
        
        # Mock Redis client that fails ping
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock(side_effect=Exception("Connection failed"))
        
        validation = await manager.validate_connection_security(mock_redis)
        
        assert validation.is_secure is False
        assert "Connection failure" in str(validation.vulnerabilities)
        assert "connectivity" in validation.detailed_checks
        assert "FAILED" in validation.detailed_checks["connectivity"]
    
    def test_get_security_recommendations_no_auth(self):
        """Test security recommendations for insecure configuration."""
        config = SecurityConfig()  # No security features
        manager = RedisCacheSecurityManager(config)
        
        recommendations = manager.get_security_recommendations()
        
        assert any("Enable Redis authentication" in rec for rec in recommendations)
        assert any("Enable TLS encryption" in rec for rec in recommendations)
        assert len(recommendations) >= 3
    
    def test_get_security_recommendations_partial_security(self):
        """Test security recommendations for partially secure configuration."""
        config = SecurityConfig(redis_auth="short")  # Weak password
        manager = RedisCacheSecurityManager(config)
        
        recommendations = manager.get_security_recommendations()
        
        assert any("stronger password" in rec for rec in recommendations)
        assert any("TLS encryption" in rec for rec in recommendations)
    
    @pytest.mark.asyncio
    async def test_test_security_configuration(self):
        """Test comprehensive security configuration testing."""
        manager = RedisCacheSecurityManager(self.basic_config)
        
        # Mock successful connection
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock()
        mock_redis.close = AsyncMock()
        
        with patch.object(manager, 'create_secure_connection', return_value=mock_redis):
            with patch.object(manager, 'validate_connection_security') as mock_validate:
                mock_validation = SecurityValidationResult(
                    is_secure=True,
                    auth_configured=True,
                    tls_enabled=False,
                    acl_enabled=False,
                    certificate_valid=False,
                    security_score=75
                )
                mock_validate.return_value = mock_validation
                
                results = await manager.test_security_configuration()
                
                assert results["configuration_valid"] is True
                assert results["connection_successful"] is True
                assert results["authentication_working"] is True
                assert results["overall_secure"] is True
                assert results["security_score"] == 75
    
    def test_generate_security_report_basic(self):
        """Test security report generation."""
        manager = RedisCacheSecurityManager(self.basic_config)
        
        # Create mock validation result
        validation = SecurityValidationResult(
            is_secure=False,
            auth_configured=True,
            tls_enabled=False,
            acl_enabled=False,
            certificate_valid=False,
            vulnerabilities=["Unencrypted connection"],
            recommendations=["Enable TLS encryption"],
            security_score=45
        )
        manager._last_validation = validation
        
        report = manager.generate_security_report()
        
        assert "REDIS CACHE SECURITY ASSESSMENT REPORT" in report
        assert "INSECURE" in report
        assert "Score: 45/100" in report
        assert "Unencrypted connection" in report
        assert "Enable TLS encryption" in report
    
    def test_get_security_status(self):
        """Test security status retrieval."""
        manager = RedisCacheSecurityManager(self.basic_config)
        
        status = manager.get_security_status()
        
        assert "timestamp" in status
        assert status["security_level"] == "MEDIUM"
        assert status["configuration"]["has_authentication"] is True
        assert status["configuration"]["tls_enabled"] is False
        assert "security_events_count" in status
        assert "recommendations_count" in status


class TestEnvironmentConfiguration:
    """Test environment-based configuration creation."""
    
    def test_create_security_config_from_env_no_vars(self):
        """Test environment config creation with no environment variables set."""
        with patch.dict(os.environ, {}, clear=True):
            config = create_security_config_from_env()
            assert config is None
    
    def test_create_security_config_from_env_basic_auth(self):
        """Test environment config creation with basic AUTH."""
        env_vars = {
            'REDIS_AUTH': 'env_password',
            'REDIS_CONNECTION_TIMEOUT': '45'
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = create_security_config_from_env()
            
            assert config is not None
            assert config.redis_auth == 'env_password'
            assert config.connection_timeout == 45
            assert config.use_tls is False
    
    @patch('pathlib.Path.exists')
    def test_create_security_config_from_env_full_config(self, mock_exists):
        """Test environment config creation with full configuration."""
        # Mock file existence to avoid file validation errors
        mock_exists.return_value = True
        
        env_vars = {
            'REDIS_AUTH': 'env_password',
            'REDIS_USE_TLS': 'true',
            'REDIS_TLS_CERT_PATH': '/path/to/cert.pem',
            'REDIS_TLS_KEY_PATH': '/path/to/key.pem',
            'REDIS_TLS_CA_PATH': '/path/to/ca.pem',
            'REDIS_ACL_USERNAME': 'env_user',
            'REDIS_ACL_PASSWORD': 'env_user_pass',
            'REDIS_VERIFY_CERTIFICATES': 'false',
            'REDIS_CONNECTION_TIMEOUT': '60',
            'REDIS_MAX_RETRIES': '5',
            'REDIS_RETRY_DELAY': '2.0'
        }
        
        with patch.dict(os.environ, env_vars, clear=True):
            config = create_security_config_from_env()
            
            assert config is not None
            assert config.redis_auth == 'env_password'
            assert config.use_tls is True
            assert config.tls_cert_path == '/path/to/cert.pem'
            assert config.tls_key_path == '/path/to/key.pem'
            assert config.tls_ca_path == '/path/to/ca.pem'
            assert config.acl_username == 'env_user'
            assert config.acl_password == 'env_user_pass'
            assert config.verify_certificates is False
            assert config.connection_timeout == 60
            assert config.max_retries == 5
            assert config.retry_delay == 2.0
    
    def test_create_security_config_from_env_boolean_parsing(self):
        """Test boolean environment variable parsing."""
        # Test various boolean representations
        test_cases = [
            ('true', True),
            ('True', True),
            ('TRUE', True),
            ('false', False),
            ('False', False),
            ('FALSE', False),
            ('yes', False),  # Only 'true' should be True
            ('1', False),    # Only 'true' should be True
            ('', False)      # Empty should be False
        ]
        
        for env_value, expected in test_cases:
            env_vars = {'REDIS_USE_TLS': env_value}
            with patch.dict(os.environ, env_vars, clear=True):
                config = create_security_config_from_env()
                if config:  # Only test if config was created
                    assert config.use_tls == expected, f"Failed for {env_value} -> {expected}"


class TestGenericRedisCacheSecurityIntegration:
    """Test security integration with GenericRedisCache."""
    
    def setup_method(self):
        """Setup method run before each test."""
        self.security_config = SecurityConfig(redis_auth="test_password")
        self.performance_monitor = CachePerformanceMonitor()
    
    def test_generic_cache_with_security_config(self):
        """Test GenericRedisCache initialization with security configuration."""
        cache = GenericRedisCache(
            redis_url="redis://localhost:6379",
            security_config=self.security_config
        )
        
        assert cache.security_config == self.security_config
        assert cache.security_manager is not None
        assert isinstance(cache.security_manager, RedisCacheSecurityManager)
    
    def test_generic_cache_without_security_config(self):
        """Test GenericRedisCache initialization without security configuration."""
        cache = GenericRedisCache(redis_url="redis://localhost:6379")
        
        assert cache.security_config is None
        assert cache.security_manager is None
    
    def test_generic_cache_security_config_unavailable(self):
        """Test GenericRedisCache with security config but security module unavailable."""
        with patch('app.infrastructure.cache.redis_generic.SECURITY_AVAILABLE', False):
            with patch('app.infrastructure.cache.redis_generic.logger') as mock_logger:
                cache = GenericRedisCache(
                    redis_url="redis://localhost:6379",
                    security_config=self.security_config
                )
                
                assert cache.security_config == self.security_config
                assert cache.security_manager is None
                mock_logger.warning.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_generic_cache_secure_connection(self):
        """Test GenericRedisCache secure connection process."""
        cache = GenericRedisCache(
            redis_url="redis://localhost:6379",
            security_config=self.security_config
        )
        
        # Mock the security manager's create_secure_connection method
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock()
        cache.security_manager.create_secure_connection = AsyncMock(return_value=mock_redis)
        
        connected = await cache.connect()
        
        assert connected is True
        assert cache.redis == mock_redis
        cache.security_manager.create_secure_connection.assert_called_once_with(cache.redis_url)
    
    @pytest.mark.asyncio
    async def test_generic_cache_fallback_connection(self):
        """Test GenericRedisCache fallback to basic connection without security."""
        cache = GenericRedisCache(redis_url="redis://localhost:6379")  # No security config
        
        # Mock aioredis for basic connection
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock()
        
        with patch('app.infrastructure.cache.redis_generic.REDIS_AVAILABLE', True):
            with patch('app.infrastructure.cache.redis_generic.aioredis') as mock_aioredis:
                mock_aioredis.from_url = AsyncMock(return_value=mock_redis)
                
                connected = await cache.connect()
                
                assert connected is True
                assert cache.redis == mock_redis
    
    @pytest.mark.asyncio
    async def test_generic_cache_validate_security(self):
        """Test security validation through GenericRedisCache."""
        cache = GenericRedisCache(
            redis_url="redis://localhost:6379",
            security_config=self.security_config
        )
        
        # Mock Redis connection and security manager
        mock_redis = AsyncMock()
        cache.redis = mock_redis
        
        mock_validation = SecurityValidationResult(
            is_secure=True,
            auth_configured=True,
            tls_enabled=False,
            acl_enabled=False,
            certificate_valid=False
        )
        cache.security_manager.validate_connection_security = AsyncMock(return_value=mock_validation)
        
        validation = await cache.validate_security()
        
        assert validation == mock_validation
        cache.security_manager.validate_connection_security.assert_called_once_with(mock_redis)
    
    @pytest.mark.asyncio
    async def test_generic_cache_validate_security_no_manager(self):
        """Test security validation without security manager."""
        cache = GenericRedisCache(redis_url="redis://localhost:6379")  # No security config
        
        validation = await cache.validate_security()
        
        assert validation is None
    
    def test_generic_cache_get_security_status_with_manager(self):
        """Test getting security status with security manager."""
        cache = GenericRedisCache(
            redis_url="redis://localhost:6379",
            security_config=self.security_config
        )
        
        mock_status = {
            "security_level": "MEDIUM",
            "configuration": {"has_authentication": True}
        }
        cache.security_manager.get_security_status = MagicMock(return_value=mock_status)
        
        status = cache.get_security_status()
        
        assert status == mock_status
    
    def test_generic_cache_get_security_status_no_manager(self):
        """Test getting security status without security manager."""
        cache = GenericRedisCache(redis_url="redis://localhost:6379")  # No security config
        
        status = cache.get_security_status()
        
        assert status["security_enabled"] is False
        assert status["security_level"] == "NONE"
        assert "No security configuration provided" in status["message"]
    
    def test_generic_cache_get_security_recommendations_with_manager(self):
        """Test getting security recommendations with security manager."""
        cache = GenericRedisCache(
            redis_url="redis://localhost:6379",
            security_config=self.security_config
        )
        
        mock_recommendations = ["Enable TLS", "Use stronger password"]
        cache.security_manager.get_security_recommendations = MagicMock(return_value=mock_recommendations)
        
        recommendations = cache.get_security_recommendations()
        
        assert recommendations == mock_recommendations
    
    def test_generic_cache_get_security_recommendations_no_manager(self):
        """Test getting security recommendations without security manager."""
        cache = GenericRedisCache(redis_url="redis://localhost:6379")  # No security config
        
        recommendations = cache.get_security_recommendations()
        
        assert len(recommendations) >= 3
        assert any("Configure Redis security" in rec for rec in recommendations)
        assert any("Enable TLS encryption" in rec for rec in recommendations)
    
    @pytest.mark.asyncio
    async def test_generic_cache_generate_security_report_with_manager(self):
        """Test generating security report with security manager."""
        cache = GenericRedisCache(
            redis_url="redis://localhost:6379",
            security_config=self.security_config
        )
        
        # Mock Redis connection
        cache.redis = AsyncMock()
        
        mock_report = "SECURITY REPORT\nStatus: SECURE\nScore: 85/100"
        cache.security_manager.validate_connection_security = AsyncMock()
        cache.security_manager.generate_security_report = MagicMock(return_value=mock_report)
        
        report = await cache.generate_security_report()
        
        assert report == mock_report
        cache.security_manager.validate_connection_security.assert_called_once_with(cache.redis)
    
    @pytest.mark.asyncio
    async def test_generic_cache_generate_security_report_no_manager(self):
        """Test generating security report without security manager."""
        cache = GenericRedisCache(redis_url="redis://localhost:6379")  # No security config
        
        report = await cache.generate_security_report()
        
        assert "NOT CONFIGURED" in report
        assert "SecurityConfig" in report
        assert "RECOMMENDATIONS" in report
    
    @pytest.mark.asyncio
    async def test_generic_cache_test_security_configuration_with_manager(self):
        """Test comprehensive security configuration testing with security manager."""
        cache = GenericRedisCache(
            redis_url="redis://localhost:6379",
            security_config=self.security_config
        )
        
        mock_results = {
            "configuration_valid": True,
            "connection_successful": True,
            "overall_secure": True,
            "security_score": 80
        }
        cache.security_manager.test_security_configuration = AsyncMock(return_value=mock_results)
        
        results = await cache.test_security_configuration()
        
        assert results == mock_results
        cache.security_manager.test_security_configuration.assert_called_once_with(cache.redis_url)
    
    @pytest.mark.asyncio
    async def test_generic_cache_test_security_configuration_no_manager(self):
        """Test comprehensive security configuration testing without security manager."""
        cache = GenericRedisCache(redis_url="redis://localhost:6379")  # No security config
        
        results = await cache.test_security_configuration()
        
        assert results["security_configured"] is False
        assert results["overall_secure"] is False
        assert "No security configuration provided" in results["message"]
        assert "recommendations" in results


class TestSecurityEdgeCases:
    """Test edge cases and error scenarios."""
    
    @pytest.mark.asyncio
    async def test_security_manager_ssl_context_failure(self):
        """Test SSL context initialization failure."""
        # Patch Path.exists to return True, but ssl operations to fail
        with patch('pathlib.Path.exists', return_value=True):
            config = SecurityConfig(
                use_tls=True,
                tls_cert_path="/nonexistent/cert.pem"
            )
            with patch('ssl.create_default_context', side_effect=Exception("SSL Error")):
                with pytest.raises(Exception, match="SSL Error"):
                    RedisCacheSecurityManager(config)
    
    @pytest.mark.asyncio
    async def test_validate_connection_security_exception_handling(self):
        """Test security validation with unexpected exceptions."""
        config = SecurityConfig(redis_auth="password")
        manager = RedisCacheSecurityManager(config)
        
        # Create a Redis mock that raises unexpected exceptions
        mock_redis = MagicMock()
        
        # This should not raise an exception, but return a validation result indicating failure
        validation = await manager.validate_connection_security(mock_redis)
        
        assert isinstance(validation, SecurityValidationResult)
        assert validation.is_secure is False
        assert "Security validation failed" in validation.vulnerabilities
    
    def test_security_validation_result_with_vulnerabilities(self):
        """Test SecurityValidationResult with many vulnerabilities affecting score."""
        result = SecurityValidationResult(
            is_secure=False,
            auth_configured=True,
            tls_enabled=True,
            acl_enabled=False,
            certificate_valid=True,
            vulnerabilities=[
                "Vulnerability 1",
                "Vulnerability 2", 
                "Vulnerability 3",
                "Vulnerability 4",
                "Vulnerability 5"  # Should cause max deduction
            ]
        )
        
        # With many vulnerabilities, score should be reduced
        assert result.security_score < 70  # Should be reduced due to vulnerabilities
    
    def test_security_config_with_cipher_suites(self):
        """Test SecurityConfig with custom cipher suites."""
        cipher_suites = ["ECDHE-RSA-AES256-GCM-SHA384", "ECDHE-RSA-AES128-GCM-SHA256"]
        config = SecurityConfig(
            use_tls=True,
            cipher_suites=cipher_suites,
            min_tls_version=ssl.TLSVersion.TLSv1_3.value
        )
        
        assert config.cipher_suites == cipher_suites
        assert config.min_tls_version == ssl.TLSVersion.TLSv1_3.value
    
    @pytest.mark.asyncio
    async def test_performance_monitoring_integration(self):
        """Test performance monitoring integration with security operations."""
        config = SecurityConfig(redis_auth="password")
        performance_monitor = CachePerformanceMonitor()
        manager = RedisCacheSecurityManager(config, performance_monitor)
        
        # Mock Redis operations
        mock_redis = AsyncMock()
        mock_redis.ping = AsyncMock()
        
        with patch.object(manager, '_create_connection_with_retry', return_value=mock_redis):
            await manager.create_secure_connection()
            
            # Should have recorded performance metrics
            assert performance_monitor.total_operations > 0
    
    def test_security_manager_log_security_event(self):
        """Test security event logging."""
        config = SecurityConfig(redis_auth="password", log_security_events=True)
        manager = RedisCacheSecurityManager(config)
        
        initial_events = len(manager._security_events)
        manager._log_security_event("test_event", {"test": "data"})
        
        assert len(manager._security_events) == initial_events + 1
        latest_event = manager._security_events[-1]
        assert latest_event["event_type"] == "test_event"
        assert latest_event["details"]["test"] == "data"
    
    def test_security_manager_event_limit(self):
        """Test security event storage limit."""
        config = SecurityConfig(redis_auth="password", log_security_events=True)
        manager = RedisCacheSecurityManager(config)
        
        # Add more than 1000 events (the limit)
        for i in range(1100):
            manager._log_security_event(f"event_{i}", {})
        
        # Should only keep the last 1000 events
        assert len(manager._security_events) == 1000
        # First event should be event_100 (events 0-99 should be removed)
        assert manager._security_events[0]["event_type"] == "event_100"
        assert manager._security_events[-1]["event_type"] == "event_1099"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
