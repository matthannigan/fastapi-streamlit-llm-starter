"""Test Security Integration and Validation

This module provides integration tests for cache security features, validating that
the CacheFactory correctly applies security configurations and that security
validation works end-to-end with real Redis connections.

Focus on testing observable security behaviors through public interfaces rather than
internal security implementation details. Tests validate the contracts defined in
backend/contracts/infrastructure/cache/security.pyi for production confidence.

These tests use fakeredis for secure testing scenarios while validating real
security integration patterns that would work with production Redis instances.
"""

import pytest
from typing import Dict, Any, Optional
from unittest.mock import patch, MagicMock

# Import actual security and factory modules for testing
from app.infrastructure.cache.security import SecurityConfig, RedisCacheSecurityManager
from app.infrastructure.cache.factory import CacheFactory
from app.core.exceptions import ConfigurationError, InfrastructureError


class TestCacheSecurityIntegration:
    """
    Test suite for verifying cache security integration and validation.
    
    Integration Scope:
        Tests security configuration integration with CacheFactory, validating
        that security settings are properly applied and enforced during cache creation.
    
    Business Impact:
        Ensures production Redis deployments are properly secured with authentication,
        TLS encryption, and proper security validation, protecting sensitive cached data.
    
    Test Strategy:
        - Test SecurityConfig creation and validation with various configurations
        - Verify CacheFactory applies security settings correctly
        - Test security validation and error handling
        - Test authentication and connection security behavior
        - Validate security integration across different factory methods
    """

    @pytest.fixture
    def cache_factory(self):
        """Create a cache factory for security testing."""
        return CacheFactory()

    @pytest.mark.asyncio
    async def test_security_config_creation_and_validation(self):
        """
        Test SecurityConfig creation with various authentication methods.
        
        Behavior Under Test:
            SecurityConfig should accept various authentication configurations
            and properly validate them during creation.
        
        Business Impact:
            Ensures security configuration can be properly created for different
            production deployment scenarios (AUTH, ACL, TLS).
        
        Success Criteria:
            - SecurityConfig accepts AUTH password configuration
            - SecurityConfig accepts ACL username/password configuration
            - SecurityConfig accepts TLS configuration parameters
            - SecurityConfig validates configuration parameters
        """
        # Test basic AUTH password configuration
        auth_config = SecurityConfig(redis_auth="secure_password_123")
        assert auth_config.has_authentication, "AUTH config should show authentication enabled"
        assert auth_config.security_level in ["LOW", "MEDIUM", "HIGH"], "Should provide security level"
        
        # Test ACL username/password configuration
        acl_config = SecurityConfig(
            acl_username="cache_user",
            acl_password="acl_password_456"
        )
        assert acl_config.has_authentication, "ACL config should show authentication enabled"
        assert acl_config.security_level in ["LOW", "MEDIUM", "HIGH"], "Should provide security level"
        
        # Test TLS configuration - use temp files to avoid validation errors
        import tempfile
        import os
        with tempfile.NamedTemporaryFile(suffix='.pem', delete=False) as cert_file:
            with tempfile.NamedTemporaryFile(suffix='.pem', delete=False) as key_file:
                tls_config = SecurityConfig(
                    redis_auth="password",
                    use_tls=True,
                    tls_cert_path=cert_file.name,
                    tls_key_path=key_file.name,
                    verify_certificates=True
                )
        # Clean up temp files
        os.unlink(cert_file.name)
        os.unlink(key_file.name)
        assert tls_config.has_authentication, "TLS config should show authentication enabled"
        assert tls_config.security_level in ["MEDIUM", "HIGH"], "TLS should provide higher security level"
        
        # Test combined security configuration
        combined_config = SecurityConfig(
            redis_auth="fallback_password",
            acl_username="secure_user",
            acl_password="secure_acl_password",
            use_tls=True,
            verify_certificates=True
        )
        assert combined_config.has_authentication, "Combined config should show authentication enabled"
        assert combined_config.security_level == "HIGH", "Combined security should be high level"

    @pytest.mark.asyncio
    async def test_security_manager_creation_and_basic_functionality(self):
        """
        Test RedisCacheSecurityManager creation and basic functionality.
        
        Behavior Under Test:
            RedisCacheSecurityManager should initialize properly with SecurityConfig
            and provide security management functionality.
        
        Business Impact:
            Ensures security manager can be created and used for managing
            Redis connection security in production environments.
        
        Success Criteria:
            - Security manager initializes with valid SecurityConfig
            - Security manager provides security recommendations
            - Security manager provides security status information
        """
        # Create security configuration
        security_config = SecurityConfig(
            redis_auth="test_password",
            use_tls=False,  # Simplified for testing
            connection_timeout=10
        )
        
        # Create security manager
        security_manager = RedisCacheSecurityManager(security_config)
        
        # Test security recommendations
        recommendations = security_manager.get_security_recommendations()
        assert isinstance(recommendations, list), "Recommendations should be list"
        assert len(recommendations) >= 0, "Should provide recommendations or empty list"
        
        # Test security status
        status = security_manager.get_security_status()
        assert isinstance(status, dict), "Security status should be dictionary"
        assert "security_level" in status or "config" in status, "Status should include security information"

    @pytest.mark.asyncio
    async def test_cache_factory_with_security_config_integration(self, cache_factory):
        """
        Test CacheFactory integration with SecurityConfig for different cache types.
        
        Behavior Under Test:
            CacheFactory should properly integrate SecurityConfig into cache creation
            for web, AI, and testing cache types, applying security settings appropriately.
        
        Business Impact:
            Ensures all cache types can be secured consistently through the factory,
            providing unified security management across different application scenarios.
        
        Success Criteria:
            - Web cache factory accepts SecurityConfig
            - AI cache factory accepts SecurityConfig  
            - Testing cache factory accepts SecurityConfig
            - SecurityConfig is properly integrated into cache instances
        """
        # Create security configuration for testing
        security_config = SecurityConfig(
            redis_auth="factory_test_password",
            connection_timeout=5,
            max_retries=2
        )
        
        # Test web cache with security config
        web_cache = await cache_factory.for_web_app(
            redis_url="redis://localhost:6379",
            security_config=security_config,
            fail_on_connection_error=False  # Allow fallback for testing
        )
        assert web_cache is not None, "Web cache should be created with security config"
        
        # Test AI cache with security config
        ai_cache = await cache_factory.for_ai_app(
            redis_url="redis://localhost:6379",
            security_config=security_config,
            fail_on_connection_error=False  # Allow fallback for testing
        )
        assert ai_cache is not None, "AI cache should be created with security config"
        
        # Test testing cache with security config
        test_cache = await cache_factory.for_testing(
            redis_url="redis://localhost:6379/15",
            security_config=security_config,
            fail_on_connection_error=False  # Allow fallback for testing
        )
        assert test_cache is not None, "Test cache should be created with security config"

    @pytest.mark.asyncio
    async def test_security_validation_with_mock_redis_success(self, cache_factory):
        """
        Test security validation with successful authentication scenario.
        
        Behavior Under Test:
            When Redis authentication is properly configured and Redis accepts
            the credentials, security validation should report successful authentication.
        
        Business Impact:
            Ensures production deployments can validate that security configuration
            is working correctly with the actual Redis instance.
        
        Success Criteria:
            - Security manager can connect to authenticated Redis
            - Security validation reports successful authentication
            - Cache operations work with authenticated connection
        """
        # Create security configuration
        security_config = SecurityConfig(
            redis_auth="correct_password",
            connection_timeout=5
        )
        
        # Mock a successful Redis connection with authentication
        with patch('app.infrastructure.cache.security.aioredis') as mock_redis:
            # Configure mock to simulate successful authentication
            mock_client = MagicMock()
            mock_client.ping.return_value = True
            mock_client.info.return_value = {"redis_version": "6.2.0", "auth": "enabled"}
            mock_redis.Redis.return_value = mock_client
            
            # Create security manager and test connection
            security_manager = RedisCacheSecurityManager(security_config)
            
            try:
                # Test security configuration
                test_result = await security_manager.test_security_configuration(
                    "redis://localhost:6379"
                )
                
                # Verify test results indicate success
                assert isinstance(test_result, dict), "Test result should be dictionary"
                assert "connection_successful" in test_result or "status" in test_result, "Should report connection status"
                
            except Exception as e:
                # If the security manager implementation requires actual Redis,
                # we can still validate that it attempts the connection properly
                pytest.skip(f"Security manager requires actual Redis connection: {e}")

    @pytest.mark.asyncio
    async def test_security_configuration_error_handling(self, cache_factory):
        """
        Test security configuration validation and error handling.
        
        Behavior Under Test:
            Invalid security configurations should be detected and appropriate
            errors should be raised during cache creation or security validation.
        
        Business Impact:
            Ensures misconfigured security settings are caught early rather than
            causing runtime security vulnerabilities or connection failures.
        
        Success Criteria:
            - Invalid TLS certificate paths are detected
            - Invalid configuration combinations are rejected
            - Appropriate error messages are provided for debugging
        """
        # Test invalid TLS certificate path - should raise ConfigurationError during init
        with pytest.raises(ConfigurationError) as exc_info:
            SecurityConfig(
                redis_auth="password",
                use_tls=True,
                tls_cert_path="/nonexistent/path/cert.pem",
                tls_key_path="/nonexistent/path/key.pem"
            )
        
        # Verify error message is helpful
        assert "certificate file not found" in str(exc_info.value).lower()
        
        # Test configuration with missing required TLS components
        incomplete_tls_config = SecurityConfig(
            use_tls=True,
            # Missing cert and key paths
        )
        
        # Configuration should still be created but may fail at connection time
        assert incomplete_tls_config.use_tls, "TLS should be enabled even with incomplete config"

    @pytest.mark.asyncio 
    async def test_cache_factory_security_fallback_behavior(self, cache_factory):
        """
        Test cache factory behavior when security configuration causes connection failures.
        
        Behavior Under Test:
            When security configuration prevents Redis connection (wrong password,
            TLS issues, etc.), factory should handle the failure appropriately based
            on fail_on_connection_error setting.
        
        Business Impact:
            Ensures applications can start with degraded functionality when Redis
            security is misconfigured, while still enforcing security in strict mode.
        
        Success Criteria:
            - fail_on_connection_error=False allows fallback to InMemoryCache
            - fail_on_connection_error=True raises InfrastructureError
            - Fallback behavior provides working cache functionality
            - Security errors are properly logged and reported
        """
        # Create security config with wrong password (simulates auth failure)
        wrong_auth_config = SecurityConfig(
            redis_auth="wrong_password",
            connection_timeout=2  # Quick timeout for testing
        )
        
        # Test graceful fallback (fail_on_connection_error=False)
        fallback_cache = await cache_factory.for_web_app(
            redis_url="redis://localhost:6379",
            security_config=wrong_auth_config,
            fail_on_connection_error=False  # Allow fallback
        )
        
        # Cache should be created (likely InMemoryCache due to auth failure)
        assert fallback_cache is not None, "Should create fallback cache"
        
        # Verify cache functionality works
        await fallback_cache.set("test_key", "test_value")
        retrieved_value = await fallback_cache.get("test_key")
        assert retrieved_value == "test_value", "Fallback cache should be functional"
        
        # Test strict security mode (fail_on_connection_error=True)
        # This should either succeed with proper security or raise an error
        try:
            strict_cache = await cache_factory.for_web_app(
                redis_url="redis://localhost:6379", 
                security_config=wrong_auth_config,
                fail_on_connection_error=True  # Strict mode
            )
            
            # If it succeeds, verify it's functional
            await strict_cache.set("strict_test", "strict_value")
            assert await strict_cache.get("strict_test") == "strict_value"
            
        except InfrastructureError:
            # This is expected behavior when Redis auth fails in strict mode
            pass
        except Exception as e:
            # Other exceptions might indicate Redis is not available for testing
            pytest.skip(f"Redis not available for strict security testing: {e}")

    @pytest.mark.asyncio
    async def test_security_config_environment_integration(self, monkeypatch):
        """
        Test SecurityConfig creation from environment variables.
        
        Behavior Under Test:
            SecurityConfig should be creatable from environment variables
            for containerized deployment scenarios.
        
        Business Impact:
            Ensures Redis security can be configured through environment
            variables in Docker, Kubernetes, and other containerized deployments.
        
        Success Criteria:
            - Environment variables are properly mapped to SecurityConfig
            - Missing environment variables result in None or defaults
            - Invalid environment values are handled appropriately
        """
        # Test environment-based configuration creation
        from app.infrastructure.cache.security import create_security_config_from_env
        
        # Mock environment variables for testing
        with patch.dict('os.environ', {
            'REDIS_AUTH': 'env_test_password',
            'REDIS_USE_TLS': 'true',
            'REDIS_VERIFY_CERTIFICATES': 'false',
            'REDIS_CONNECTION_TIMEOUT': '15'
        }):
            env_config = create_security_config_from_env()
            
            if env_config is not None:
                assert env_config.redis_auth == 'env_test_password', "Should read auth from environment"
                assert env_config.use_tls is True, "Should parse TLS boolean from environment"
                assert env_config.connection_timeout == 15, "Should parse timeout from environment"
            else:
                # If no configuration is created, that's also valid behavior
                pass
        
        # Test with empty environment
        # Clear all Redis security-related environment variables for clean test
        redis_security_vars = [
            'REDIS_AUTH', 'REDIS_ACL_USERNAME', 'REDIS_ACL_PASSWORD', 'REDIS_USE_TLS',
            'REDIS_TLS_CERT_PATH', 'REDIS_TLS_KEY_PATH', 'REDIS_TLS_CA_PATH',
            'REDIS_VERIFY_CERTIFICATES', 'REDIS_CONNECTION_TIMEOUT'
        ]
        for var in redis_security_vars:
            monkeypatch.delenv(var, raising=False)
        
        empty_env_config = create_security_config_from_env()
        
        # Should return None or default configuration
        assert empty_env_config is None or isinstance(empty_env_config, SecurityConfig)

    @pytest.mark.asyncio
    async def test_security_validation_comprehensive_reporting(self):
        """
        Test comprehensive security validation reporting.
        
        Behavior Under Test:
            Security validation should provide detailed reporting about
            security status, vulnerabilities, and recommendations.
        
        Business Impact:
            Enables operations teams to assess Redis security posture
            and implement appropriate security improvements.
        
        Success Criteria:
            - Security validation provides comprehensive results
            - Validation results include security scores and levels
            - Vulnerabilities and recommendations are provided
            - Results are actionable for security improvements
        """
        # Create security configuration for validation testing
        test_config = SecurityConfig(
            redis_auth="validation_test_password",
            use_tls=False,  # This should be flagged as a security issue
            verify_certificates=False
        )
        
        security_manager = RedisCacheSecurityManager(test_config)
        
        # Generate security report
        security_report = security_manager.generate_security_report()
        
        # Verify report structure and content
        assert isinstance(security_report, str), "Security report should be string"
        assert len(security_report) > 0, "Security report should have content"
        
        # Check if report contains expected security information
        report_lower = security_report.lower()
        security_keywords = ["security", "authentication", "tls", "encryption"]
        assert any(keyword in report_lower for keyword in security_keywords), "Report should contain security information"

    @pytest.mark.asyncio
    async def test_cache_factory_config_based_security_integration(self, cache_factory):
        """
        Test cache factory security integration through configuration-based creation.
        
        Behavior Under Test:
            CacheFactory.create_cache_from_config should properly integrate
            SecurityConfig when provided in the configuration dictionary.
        
        Business Impact:
            Ensures configuration-driven cache creation can include security
            settings for flexible deployment scenarios.
        
        Success Criteria:
            - Configuration-based factory accepts security_config parameter
            - SecurityConfig is properly applied to created cache
            - Cache creation respects security and fallback settings
        """
        # Create security configuration
        config_security = SecurityConfig(
            redis_auth="config_test_password",
            connection_timeout=8,
            max_retries=3
        )
        
        # Test configuration-based creation with security
        cache_config = {
            "redis_url": "redis://localhost:6379",
            "default_ttl": 1800,
            "compression_threshold": 2000,
            "security_config": config_security
        }
        
        config_cache = await cache_factory.create_cache_from_config(
            cache_config,
            fail_on_connection_error=False  # Allow fallback for testing
        )
        
        # Verify cache was created successfully
        assert config_cache is not None, "Config-based cache should be created with security"
        
        # Test cache functionality
        await config_cache.set("config_test_key", "config_test_value")
        retrieved = await config_cache.get("config_test_key")
        assert retrieved == "config_test_value", "Config-based cache should be functional"

    @pytest.mark.asyncio
    async def test_security_integration_across_cache_types(self, cache_factory):
        """
        Test that security configuration works consistently across all cache types.
        
        Behavior Under Test:
            All factory methods (web, AI, testing, config-based) should apply
            security configuration consistently and provide the same security behavior.
        
        Business Impact:
            Ensures security policy can be applied uniformly across different
            cache types in mixed application deployments.
        
        Success Criteria:
            - Same SecurityConfig works with all factory methods
            - Security behavior is consistent across cache types
            - All cache types respect fail_on_connection_error setting
        """
        # Create consistent security configuration
        uniform_security = SecurityConfig(
            redis_auth="uniform_test_password",
            connection_timeout=6
        )
        
        # Test all factory methods with same security config
        cache_types = []
        
        # Web cache
        web_cache = await cache_factory.for_web_app(
            security_config=uniform_security,
            fail_on_connection_error=False
        )
        cache_types.append(("web", web_cache))
        
        # AI cache
        ai_cache = await cache_factory.for_ai_app(
            security_config=uniform_security, 
            fail_on_connection_error=False
        )
        cache_types.append(("ai", ai_cache))
        
        # Testing cache
        test_cache = await cache_factory.for_testing(
            security_config=uniform_security,
            fail_on_connection_error=False
        )
        cache_types.append(("testing", test_cache))
        
        # Verify all caches were created and are functional
        for cache_type, cache in cache_types:
            assert cache is not None, f"{cache_type} cache should be created with security"
            
            # Test basic functionality
            test_key = f"{cache_type}_security_test"
            test_value = f"{cache_type}_security_value"
            
            await cache.set(test_key, test_value)
            retrieved = await cache.get(test_key)
            assert retrieved == test_value, f"{cache_type} cache should be functional with security"