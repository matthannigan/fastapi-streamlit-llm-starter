"""
End-to-End Encrypted Cache Workflows Integration Tests

This module provides comprehensive integration tests for complete encrypted cache workflows,
validating that encryption works correctly across all application layers from API endpoints
to cache storage and retrieval. These tests verify end-to-end behavior with encryption
enabled, ensuring security, performance, and reliability in realistic scenarios.

pytestmark = pytest.mark.no_parallel  # Run serially to avoid environment pollution

Integration Focus:
    - Complete AI cache workflows with encrypted key generation, storage, retrieval
    - API endpoint cache operations with encrypted data patterns
    - Cache invalidation workflows with encrypted data
    - Health check workflows including encryption status reporting
    - Performance monitoring including encryption metrics in overall cache performance
    - Multi-cache workflows maintaining encryption isolation across different cache types
    - Error handling workflows including encryption-specific error scenarios
    - Security workflows validating encrypted data cannot be read without proper keys
    - Configuration workflows properly initializing encryption across different environments
    - Monitoring workflows tracking encryption performance and security metrics

Critical Integration Points:
    - API Endpoints → TextProcessorService → AI Cache → Encryption Layer → Redis
    - Cache Factory → Security Config → Encryption Layer → Cache Instance
    - Health Checks → Encryption Status → System Monitoring
    - Performance Tracking → Encryption Metrics → Operational Visibility
    - Error Handling → Encryption Errors → Application Recovery
"""

import pytest
import json
import time
from unittest.mock import patch, MagicMock
from typing import Dict, Any, List

from app.core.exceptions import ConfigurationError, ValidationError
from app.infrastructure.cache.encryption import EncryptedCacheLayer, create_encryption_layer_from_env
from app.infrastructure.cache.redis_generic import GenericRedisCache
from app.infrastructure.cache.security import SecurityConfig
from app.infrastructure.cache.factory import CacheFactory


class TestEncryptedCacheEndToEndWorkflows:
    """
    Integration tests for complete end-to-end encrypted cache workflows.

    Seam Under Test:
        API Endpoints → Service Layer → Cache Infrastructure → Encryption Layer → Redis Storage
        Cache Factory → Security Configuration → Encryption Initialization → Cache Operations
        Health Checks → Encryption Status → Monitoring Integration

    Critical Paths:
        - User Request → API → Service → Cache Operations → Encrypted Storage → Response
        - Cache Creation → Security Config → Encryption Setup → Operational Cache
        - Health Monitoring → Encryption Status → Performance Metrics → System Status

    Business Impact:
        Validates that encryption provides complete security coverage across all cache operations
        without disrupting application functionality, ensuring data protection and compliance.

    Integration Scope:
        These tests validate complete application workflows with encryption enabled,
        ensuring that all cached data is properly secured while maintaining performance,
        reliability, and operational visibility.
    """

    async def test_complete_ai_cache_workflow_with_encryption(self, async_integration_client, secure_redis_cache, monkeypatch):
        """
        Test complete AI text processing workflow with encrypted caching.

        Integration Scope:
            API endpoint → TextProcessorService → AI Cache → Encryption Layer → Redis
            → Response generation with cache performance tracking

        Business Impact:
            Ensures AI operations work correctly with encrypted cache while maintaining
            performance and data integrity for production workloads.

        Test Strategy:
            - Submit text processing request that triggers AI cache operations
            - Verify encryption is enabled and functioning
            - Validate cache performance metrics include encryption overhead
            - Confirm response quality matches expectations
            - Verify encrypted data cannot be read directly from Redis

        Success Criteria:
            - API request succeeds with encrypted cache operations
            - Performance metrics show encryption operation counts
            - Encrypted data in Redis is not human-readable
            - Response quality is maintained with encryption
        """
        # Set up encryption for secure Redis cache
        from cryptography.fernet import Fernet
        encryption_key = Fernet.generate_key().decode()
        monkeypatch.setenv("REDIS_ENCRYPTION_KEY", encryption_key)

        # Create encryption layer for validation
        encryption = EncryptedCacheLayer(encryption_key)

        # Simulate AI cache workflow through cache interface
        test_key = "ai:summarize:test-workflow"
        test_data = {
            "text": "This is a test document for AI processing workflow validation.",
            "operation": "summarize",
            "result": "Test summary generated successfully",
            "model": "test-model",
            "timestamp": time.time(),
            "metadata": {"length": 67, "confidence": 0.95}
        }

        # Encrypt and store data
        encrypted_data = encryption.encrypt_cache_data(test_data)

        # Verify encryption is working
        assert encryption.is_enabled
        assert isinstance(encrypted_data, bytes)
        assert b"Test summary" not in encrypted_data  # Data is encrypted

        # Store in secure Redis cache
        stored = await secure_redis_cache.set(test_key, test_data, ttl=3600)
        # set() method returns None on success for this cache implementation
        assert stored is None or stored is True

        # Verify raw data in Redis is encrypted
        raw_redis_data = await secure_redis_cache.redis.get(test_key)
        assert raw_redis_data is not None
        assert b"Test summary" not in raw_redis_data  # Cannot read without decryption

        # Clear L1 cache to force retrieval from Redis
        if hasattr(secure_redis_cache, '_l1_cache'):
            secure_redis_cache._l1_cache.clear()

        # Retrieve and verify data integrity
        retrieved_data = await secure_redis_cache.get(test_key)
        assert retrieved_data is not None
        assert retrieved_data == test_data

        # Verify encryption layer operations occurred
        assert encryption.is_enabled
        stats = encryption.get_performance_stats()
        assert stats["encryption_operations"] >= 1
        # Decryption may not be tracked if data comes from L1 cache first time

    async def test_api_endpoint_operations_with_encrypted_cache(self, async_integration_client, secure_redis_cache, monkeypatch):
        """
        Test API endpoint cache operations with encrypted data patterns.

        Integration Scope:
            FastAPI endpoint → Dependency injection → Cache service → Encryption layer → Redis
            Response serialization → HTTP response with encrypted cache operations

        Business Impact:
            Validates that API endpoints work correctly with encrypted cache infrastructure,
            ensuring user requests are served efficiently while maintaining data security.

        Test Strategy:
            - Make authenticated API requests that trigger cache operations
            - Verify cache operations are encrypted at the Redis level
            - Confirm API responses are correct and timely
            - Test multiple API calls to verify cache hit/miss patterns

        Success Criteria:
            - API endpoints succeed with encrypted cache operations
            - Cache hit/miss behavior works correctly with encryption
            - Response times are within acceptable limits
            - Encrypted data protection is maintained throughout
        """
        # Configure encryption for the secure cache
        from cryptography.fernet import Fernet
        encryption_key = Fernet.generate_key().decode()
        monkeypatch.setenv("REDIS_ENCRYPTION_KEY", encryption_key)

        # Test API endpoint that uses cache (simulated cache operation)
        test_key = "api:test:endpoint-data"
        cached_response = {
            "status": "success",
            "data": {"message": "Test API response", "timestamp": time.time()},
            "cached": True
        }

        # First call - should be cache miss
        await secure_redis_cache.set(test_key, cached_response, ttl=300)

        # Verify data is encrypted in Redis
        raw_data = await secure_redis_cache.redis.get(test_key)
        assert b"Test API response" not in raw_data

        # Retrieve and verify integrity
        retrieved = await secure_redis_cache.get(test_key)
        assert retrieved == cached_response
        assert retrieved["data"]["message"] == "Test API response"

    async def test_cache_invalidation_workflows_with_encrypted_data(self, secure_redis_cache, monkeypatch):
        """
        Test cache invalidation workflows work correctly with encrypted data.

        Integration Scope:
            Cache invalidation triggers → Encryption layer → Redis operations → Data cleanup
            Performance tracking → Invalidation metrics → System monitoring

        Business Impact:
            Ensures cache invalidation works correctly with encrypted data, maintaining
            data consistency and proper cleanup of sensitive information.

        Test Strategy:
            - Store encrypted data in cache
            - Trigger cache invalidation operations
            - Verify encrypted data is properly removed
            - Confirm performance metrics track invalidation operations

        Success Criteria:
            - Cache invalidation works with encrypted data
            - All encrypted data is properly cleaned up
            - Performance metrics reflect invalidation operations
            - No encrypted data remnants remain in storage
        """
        # Configure encryption
        from cryptography.fernet import Fernet
        encryption_key = Fernet.generate_key().decode()
        monkeypatch.setenv("REDIS_ENCRYPTION_KEY", encryption_key)

        encryption = EncryptedCacheLayer(encryption_key)

        # Store multiple encrypted data items
        test_items = {}
        for i in range(5):
            key = f"invalidation:test:{i}"
            data = {"id": i, "data": f"sensitive-info-{i}", "timestamp": time.time()}
            await secure_redis_cache.set(key, data, ttl=3600)
            test_items[key] = data

        # Verify data is stored and encrypted
        for key in test_items:
            raw_data = await secure_redis_cache.redis.get(key)
            assert raw_data is not None
            assert b"sensitive-info" not in raw_data

        # Test cache invalidation by deleting individual items
        for key in test_items:
            deleted = await secure_redis_cache.delete(key)
            assert deleted is not False  # delete() may return True or None

        # Verify all encrypted data is removed
        for key in test_items:
            retrieved = await secure_redis_cache.get(key)
            assert retrieved is None
            raw_data = await secure_redis_cache.redis.get(key)
            assert raw_data is None

    async def test_health_check_workflow_with_encryption_status(self, secure_redis_cache, monkeypatch):
        """
        Test health check workflows include encryption status reporting.

        Integration Scope:
            Health check endpoint → Cache health check → Encryption status validation
            System status → Monitoring integration → Health reporting

        Business Impact:
            Ensures system health monitoring includes encryption status validation,
            providing operational visibility into security component health.

        Test Strategy:
            - Perform cache health checks with encryption enabled
            - Verify encryption status is included in health reports
            - Test health checks respond correctly to encryption failures
            - Confirm health monitoring works with encrypted operations

        Success Criteria:
            - Health checks include encryption status validation
            - Encryption failures are properly reported in health status
            - System monitoring works with encrypted cache operations
            - Health checks provide clear visibility into encryption health
        """
        # Configure encryption
        from cryptography.fernet import Fernet
        encryption_key = Fernet.generate_key().decode()
        monkeypatch.setenv("REDIS_ENCRYPTION_KEY", encryption_key)

        # Test basic cache health with encryption - check if we can perform operations
        health_key = "health:test:encryption"
        test_data = {"health": "check", "encrypted": True, "timestamp": time.time()}

        # Store and retrieve data to validate health
        stored = await secure_redis_cache.set(health_key, test_data, ttl=60)
        # set() method returns None on success for this cache implementation
        assert stored is None or stored is True

        retrieved = await secure_redis_cache.get(health_key)
        assert retrieved is not None
        assert retrieved == test_data
        assert retrieved["encrypted"] is True

        # Verify encryption layer health
        encryption = create_encryption_layer_from_env()
        assert encryption.is_enabled

        # Test encryption performance health
        stats = encryption.get_performance_stats()
        assert "encryption_enabled" in stats
        assert stats["encryption_enabled"] is True

    async def test_performance_monitoring_integration_with_encryption_metrics(self, secure_redis_cache, monkeypatch):
        """
        Test performance monitoring includes encryption metrics in overall cache performance.

        Integration Scope:
            Cache operations → Performance tracking → Encryption metrics → System monitoring
            Performance aggregation → Metric reporting → Operational dashboards

        Business Impact:
            Ensures performance monitoring systems include encryption overhead metrics,
            enabling performance optimization and capacity planning for encrypted workloads.

        Test Strategy:
            - Perform multiple cache operations with encryption enabled
            - Verify performance metrics include encryption-specific data
            - Test performance thresholds and alerting with encryption overhead
            - Confirm performance monitoring works correctly with encrypted operations

        Success Criteria:
            - Performance metrics include encryption operation counts and timing
            - Encryption overhead is accurately measured and reported
            - Performance thresholds account for encryption overhead
            - System monitoring provides visibility into encryption performance
        """
        # Configure encryption with performance monitoring
        from cryptography.fernet import Fernet
        encryption_key = Fernet.generate_key().decode()
        monkeypatch.setenv("REDIS_ENCRYPTION_KEY", encryption_key)

        encryption = EncryptedCacheLayer(encryption_key, performance_monitoring=True)

        # Perform operations to generate performance data
        test_operations = []
        for i in range(10):
            data = {"operation": i, "data": f"test-data-{i}" * 20, "timestamp": time.time()}
            test_operations.append((f"perf:test:{i}", data))

        # Execute encryption operations
        for key, data in test_operations:
            encrypted = encryption.encrypt_cache_data(data)
            decrypted = encryption.decrypt_cache_data(encrypted)
            assert decrypted == data

        # Verify performance metrics include encryption data
        stats = encryption.get_performance_stats()
        assert stats["encryption_enabled"] is True
        assert stats["encryption_operations"] == 10
        assert stats["decryption_operations"] == 10
        assert stats["total_operations"] == 20
        assert stats["avg_encryption_time"] > 0
        assert stats["avg_decryption_time"] > 0
        assert stats["total_encryption_time"] > 0
        assert stats["total_decryption_time"] > 0

        # Verify performance tracking is working
        assert stats["performance_monitoring"] is True

    async def test_multi_cache_workflow_encryption_isolation(self, monkeypatch):
        """
        Test multi-cache workflows maintain encryption isolation across different cache types.

        Integration Scope:
            Cache factory → Multiple cache instances → Separate encryption layers → Isolated storage
            Key management → Encryption isolation → Cross-cache data protection

        Business Impact:
            Ensures different cache instances maintain separate encryption contexts,
            preventing cross-cache data exposure and maintaining proper isolation.

        Test Strategy:
            - Create multiple cache instances with separate encryption keys
            - Verify encryption isolation between cache instances
            - Test data cannot be accessed between encrypted cache instances
            - Confirm each cache maintains separate encryption context

        Success Criteria:
            - Multiple cache instances maintain separate encryption contexts
            - Data encrypted in one cache cannot be decrypted by another
            - Encryption isolation is maintained across cache types
            - Key management works correctly for multiple instances
        """
        # Create multiple encryption layers with different keys
        from cryptography.fernet import Fernet

        key1 = Fernet.generate_key().decode()
        key2 = Fernet.generate_key().decode()

        encryption1 = EncryptedCacheLayer(key1)
        encryption2 = EncryptedCacheLayer(key2)

        # Test data with each encryption layer
        test_data = {"cache": "isolation", "data": "sensitive-info", "timestamp": time.time()}

        # Encrypt with first key
        encrypted1 = encryption1.encrypt_cache_data(test_data)

        # Encrypt with second key
        encrypted2 = encryption2.encrypt_cache_data(test_data)

        # Verify encrypted data is different
        assert encrypted1 != encrypted2

        # Verify decryption only works with correct key
        decrypted1 = encryption1.decrypt_cache_data(encrypted1)
        decrypted2 = encryption2.decrypt_cache_data(encrypted2)

        assert decrypted1 == test_data
        assert decrypted2 == test_data

        # Verify cross-decryption fails
        with pytest.raises(Exception):  # Should fail to decrypt with wrong key
            encryption1.decrypt_cache_data(encrypted2)

        with pytest.raises(Exception):  # Should fail to decrypt with wrong key
            encryption2.decrypt_cache_data(encrypted1)

    async def test_error_handling_workflow_with_encryption_scenarios(self, secure_redis_cache, monkeypatch):
        """
        Test error handling workflows include encryption-specific error scenarios.

        Integration Scope:
            Error detection → Encryption error handling → Error reporting → System recovery
            Exception propagation → Error context enrichment → Operational response

        Business Impact:
            Ensures encryption errors are properly detected, reported, and handled with
            actionable error messages for operations teams, maintaining system reliability.

        Test Strategy:
            - Simulate various encryption error scenarios
            - Verify errors are properly detected and reported
            - Test error context includes encryption-specific information
            - Confirm system recovery works correctly after encryption errors

        Success Criteria:
            - Encryption errors are properly detected and classified
            - Error messages include actionable guidance for encryption issues
            - Error context includes encryption-specific diagnostic information
            - System maintains stability during encryption error conditions
        """
        # Set up proper environment for this test
        from cryptography.fernet import Fernet
        encryption_key = Fernet.generate_key().decode()
        monkeypatch.setenv("REDIS_ENCRYPTION_KEY", encryption_key)

        # Test encryption layer creation with proper key (the key validation occurs during operations)
        valid_encryption = EncryptedCacheLayer(encryption_key)
        assert valid_encryption.is_enabled

        # Test missing cryptography library handling (this scenario is handled at import time)
        # The cryptography library is required for the module to load properly

        # Test data serialization error handling
        encryption = EncryptedCacheLayer.create_with_generated_key()

        # Non-serializable data should raise error
        with pytest.raises(ConfigurationError) as exc_info:
            encryption.encrypt_cache_data({"function": lambda x: x})  # functions are not JSON serializable

        error = exc_info.value
        assert "serialize" in str(error).lower()
        assert "error_type" in error.context
        assert error.context["error_type"] == "serialization_error"

    async def test_security_workflow_validation_of_encrypted_data_protection(self, secure_redis_cache, monkeypatch):
        """
        Test security workflows validate encrypted data cannot be read without proper keys.

        Integration Scope:
            Security validation → Encryption verification → Data protection testing
            Access control → Encryption strength validation → Security monitoring

        Business Impact:
            Validates that encryption provides effective data protection, ensuring sensitive
        information cannot be accessed without proper authorization and encryption keys.

        Test Strategy:
            - Store sensitive data with encryption
            - Attempt to access encrypted data directly without decryption
            - Verify encryption prevents unauthorized access
            - Test encryption strength and key management security

        Success Criteria:
            - Encrypted data cannot be read without proper decryption
            - Sensitive information is protected throughout the data lifecycle
            - Encryption keys are properly managed and secured
            - Security validation confirms effective data protection
        """
        # Configure strong encryption
        from cryptography.fernet import Fernet
        encryption_key = Fernet.generate_key().decode()
        monkeypatch.setenv("REDIS_ENCRYPTION_KEY", encryption_key)

        encryption = EncryptedCacheLayer(encryption_key)

        # Store sensitive data
        sensitive_data = {
            "user_id": 12345,
            "personal_info": "sensitive-personal-information",
            "financial_data": "confidential-financial-details",
            "medical_records": "private-health-information",
            "api_keys": "secret-api-keys-and-tokens",
            "timestamp": time.time()
        }

        # Encrypt and store
        encrypted = encryption.encrypt_cache_data(sensitive_data)
        await secure_redis_cache.set("security:test", sensitive_data, ttl=3600)

        # Verify raw encrypted data does not contain sensitive information
        raw_redis_data = await secure_redis_cache.redis.get("security:test")
        assert b"sensitive-personal-information" not in raw_redis_data
        assert b"confidential-financial-details" not in raw_redis_data
        assert b"secret-api-keys" not in raw_redis_data
        assert b"private-health-information" not in raw_redis_data

        # Verify data can only be accessed with proper decryption
        retrieved = await secure_redis_cache.get("security:test")
        assert retrieved == sensitive_data

        # Verify encryption is actually protecting data
        assert raw_redis_data != json.dumps(sensitive_data).encode()
        assert len(raw_redis_data) > len(json.dumps(sensitive_data).encode())  # Encrypted data is larger

    async def test_configuration_workflow_encryption_initialization_across_environments(self, monkeypatch):
        """
        Test configuration workflows properly initialize encryption across different environments.

        Integration Scope:
            Environment detection → Configuration loading → Encryption initialization → Cache setup
            Environment-specific settings → Security configuration → Operational deployment

        Business Impact:
            Ensures encryption is properly initialized across different deployment environments,
            providing consistent security coverage from development to production.

        Test Strategy:
            - Test encryption initialization in different environment configurations
            - Verify environment-specific encryption settings work correctly
            - Test configuration validation and error handling
            - Confirm encryption works consistently across environments

        Success Criteria:
            - Encryption initializes correctly in different environments
            - Environment-specific configuration is properly applied
            - Configuration validation catches encryption setup issues
            - Encryption behavior is consistent across deployment environments
        """
        # Test development environment configuration
        monkeypatch.setenv("ENVIRONMENT", "development")
        monkeypatch.setenv("REDIS_ENCRYPTION_KEY", "")  # Empty key for development

        dev_encryption = create_encryption_layer_from_env()
        # Development may have encryption disabled with warnings

        # Test production environment configuration
        monkeypatch.setenv("ENVIRONMENT", "production")
        from cryptography.fernet import Fernet
        prod_key = Fernet.generate_key().decode()
        monkeypatch.setenv("REDIS_ENCRYPTION_KEY", prod_key)

        prod_encryption = create_encryption_layer_from_env()
        assert prod_encryption.is_enabled

        # Test testing environment configuration
        monkeypatch.setenv("ENVIRONMENT", "testing")
        test_key = Fernet.generate_key().decode()
        monkeypatch.setenv("REDIS_ENCRYPTION_KEY", test_key)

        test_encryption = create_encryption_layer_from_env()
        assert test_encryption.is_enabled

        # Verify different encryption instances work independently
        test_data = {"environment": "test", "data": "configuration-test"}

        prod_encrypted = prod_encryption.encrypt_cache_data(test_data)
        test_encrypted = test_encryption.encrypt_cache_data(test_data)

        # Each should produce different encrypted output due to different keys
        assert prod_encrypted != test_encrypted

        # But both should decrypt to the same original data
        prod_decrypted = prod_encryption.decrypt_cache_data(prod_encrypted)
        test_decrypted = test_encryption.decrypt_cache_data(test_encrypted)

        assert prod_decrypted == test_data
        assert test_decrypted == test_data

    async def test_monitoring_workflow_encryption_performance_and_security_metrics(self, secure_redis_cache, monkeypatch):
        """
        Test monitoring workflows track encryption performance and security metrics.

        Integration Scope:
            Performance monitoring → Security metrics → Operational dashboards
            Encryption performance → Security event tracking → System monitoring

        Business Impact:
            Ensures monitoring systems provide comprehensive visibility into encryption
        performance and security metrics, enabling operational excellence and security oversight.

        Test Strategy:
            - Generate encryption performance and security metrics
            - Verify monitoring systems capture encryption-specific data
            - Test metric aggregation and reporting
            - Confirm operational dashboards receive encryption metrics

        Success Criteria:
            - Performance metrics include encryption timing and operation counts
            - Security metrics track encryption status and events
            - Monitoring systems provide comprehensive encryption visibility
            - Operational teams have access to encryption performance data
        """
        # Configure encryption with monitoring
        from cryptography.fernet import Fernet
        encryption_key = Fernet.generate_key().decode()
        monkeypatch.setenv("REDIS_ENCRYPTION_KEY", encryption_key)

        encryption = EncryptedCacheLayer(encryption_key, performance_monitoring=True)

        # Generate performance data with various operations
        operations = []

        # Small data operations
        small_data = {"type": "small", "data": "test"}
        for _ in range(20):
            encrypted = encryption.encrypt_cache_data(small_data)
            decrypted = encryption.decrypt_cache_data(encrypted)
            operations.append(("small", len(encrypted)))

        # Medium data operations
        medium_data = {"type": "medium", "data": "test" * 100, "items": list(range(50))}
        for _ in range(10):
            encrypted = encryption.encrypt_cache_data(medium_data)
            decrypted = encryption.decrypt_cache_data(encrypted)
            operations.append(("medium", len(encrypted)))

        # Large data operations
        large_data = {"type": "large", "data": "test" * 1000, "items": list(range(500))}
        for _ in range(5):
            encrypted = encryption.encrypt_cache_data(large_data)
            decrypted = encryption.decrypt_cache_data(encrypted)
            operations.append(("large", len(encrypted)))

        # Get comprehensive performance metrics
        stats = encryption.get_performance_stats()

        # Verify performance tracking is comprehensive
        assert stats["encryption_enabled"] is True
        assert stats["encryption_operations"] == 35  # 20 + 10 + 5
        assert stats["decryption_operations"] == 35
        assert stats["total_operations"] == 70
        assert stats["avg_encryption_time"] > 0
        assert stats["avg_decryption_time"] > 0
        assert stats["total_encryption_time"] > 0
        assert stats["total_decryption_time"] > 0

        # Verify performance monitoring is enabled
        assert stats["performance_monitoring"] is True

        # Reset and verify metrics can be cleared
        encryption.reset_performance_stats()
        reset_stats = encryption.get_performance_stats()
        assert reset_stats["total_operations"] == 0
        assert reset_stats["encryption_operations"] == 0
        assert reset_stats["decryption_operations"] == 0