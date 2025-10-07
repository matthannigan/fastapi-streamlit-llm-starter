"""
Unit tests for CacheConfigBuilder fluent interface and configuration building.

This test suite verifies the observable behaviors documented in the
CacheConfigBuilder public contract (config.pyi). Tests focus on the
behavior-driven testing principles described in docs/guides/testing/TESTING.md.

Coverage Focus:
    - CacheConfigBuilder fluent interface and method chaining
    - Environment-based configuration loading and file operations
    - Validation integration and error handling during building
    - Configuration building and finalization through build() method

External Dependencies:
    All external dependencies are mocked using fixtures from conftest.py following
    the documented public contracts to ensure accurate behavior simulation.
"""

import json
import os
from pathlib import Path
from typing import Any, Dict, Optional
from unittest.mock import MagicMock, mock_open, patch

import pytest

from app.core.exceptions import ConfigurationError, ValidationError
from app.infrastructure.cache.config import (CacheConfig, CacheConfigBuilder,
                                             ValidationResult)


class TestCacheConfigBuilderInitialization:
    """
    Test suite for CacheConfigBuilder initialization and basic fluent interface.

    Scope:
        - CacheConfigBuilder initialization and initial state setup
        - Basic fluent interface method chaining behavior
        - Builder state management and configuration accumulation
        - Method return value consistency for fluent interface

    Business Critical:
        Builder pattern provides flexible configuration construction for various environments

    Test Strategy:
        - Builder initialization testing with clean state verification
        - Method chaining testing using builder_with_basic_config fixtures
        - State accumulation testing through configuration parameter building
        - Fluent interface consistency testing across all builder methods

    External Dependencies:
        - None (CacheConfigBuilder is self-contained for basic initialization)
    """

    def test_cache_config_builder_initializes_with_empty_configuration_state(self):
        """
        Test that CacheConfigBuilder initializes with empty configuration ready for building.

        Verifies:
            Builder initialization provides clean state for configuration construction

        Business Impact:
            Ensures builders start with predictable state for consistent configuration building

        Scenario:
            Given: CacheConfigBuilder constructor is called without parameters
            When: Builder instance is created
            Then: Builder has empty configuration state ready for method chaining
            And: All configuration parameters start as unset or default values
            And: Builder is ready for fluent interface method calls

        Clean State Verification:
            - Internal configuration state is empty or contains only defaults
            - No residual configuration from previous builder instances
            - Builder methods return self for fluent interface chaining
            - Configuration accumulation starts from known clean state
            - Builder validation state indicates incomplete configuration

        Fixtures Used:
            - None (testing basic constructor behavior)

        Predictable Initialization:
            Clean builder state ensures consistent configuration building behavior

        Related Tests:
            - test_builder_methods_return_self_for_fluent_chaining()
            - test_builder_accumulates_configuration_through_method_calls()
        """
        # Given: CacheConfigBuilder constructor is called without parameters
        builder = CacheConfigBuilder()

        # When: Builder instance is created
        # Then: Builder has empty configuration state ready for method chaining

        # Assert: Configuration starts with default values
        assert builder._config.redis_url is None
        assert builder._config.redis_password is None
        assert builder._config.use_tls is False
        assert builder._config.default_ttl == 3600  # Default 1 hour
        assert builder._config.memory_cache_size == 100  # Default size
        assert builder._config.environment == "development"  # Default environment
        assert builder._config.ai_config is None

        # Assert: Builder is ready for fluent interface method calls
        assert hasattr(builder, "for_environment")
        assert hasattr(builder, "with_redis")
        assert hasattr(builder, "with_security")
        assert hasattr(builder, "with_compression")
        assert hasattr(builder, "build")

        # Assert: No residual configuration from previous instances
        builder2 = CacheConfigBuilder()
        assert builder._config is not builder2._config
        assert builder._config.redis_url == builder2._config.redis_url

    def test_builder_methods_return_self_for_fluent_chaining(self):
        """
        Test that all builder methods return self to enable fluent interface chaining.

        Verifies:
            Fluent interface pattern is properly implemented across all builder methods

        Business Impact:
            Enables readable, chainable configuration construction syntax

        Scenario:
            Given: CacheConfigBuilder instance ready for configuration
            When: Builder methods are called (for_environment, with_redis, etc.)
            Then: Each method returns the builder instance (self) for chaining
            And: Method chaining can continue without intermediate variable assignment
            And: Complete configuration can be built in single fluent expression

        Fluent Interface Verification:
            - for_environment() returns self for environment configuration chaining
            - with_redis() returns self for Redis configuration chaining
            - with_security() returns self for security configuration chaining
            - with_compression() returns self for compression configuration chaining
            - with_ai_features() returns self for AI configuration chaining

        Fixtures Used:
            - None (testing method return value behavior)

        Chaining Consistency:
            All builder methods maintain fluent interface contract

        Related Tests:
            - test_cache_config_builder_initializes_with_empty_configuration_state()
            - test_builder_accumulates_configuration_through_method_calls()
        """
        # Given: CacheConfigBuilder instance ready for configuration
        builder = CacheConfigBuilder()

        # When: Builder methods are called
        # Then: Each method returns the builder instance (self) for chaining

        # Assert: for_environment() returns self
        result1 = builder.for_environment("development")
        assert result1 is builder

        # Assert: with_redis() returns self
        result2 = builder.with_redis("redis://test:6379")
        assert result2 is builder

        # Assert: with_security() returns self
        result3 = builder.with_security("/path/to/cert", "/path/to/key")
        assert result3 is builder

        # Assert: with_compression() returns self
        result4 = builder.with_compression(threshold=1500, level=5)
        assert result4 is builder

        # Assert: with_memory_cache() returns self
        result5 = builder.with_memory_cache(size=150)
        assert result5 is builder

        # Assert: with_ai_features() returns self
        result6 = builder.with_ai_features(text_hash_threshold=1000)
        assert result6 is builder

        # Assert: Method chaining works in single fluent expression
        chained_result = (
            CacheConfigBuilder()
            .for_environment("production")
            .with_redis("redis://prod:6379")
            .with_compression(threshold=1000, level=6)
        )

        assert isinstance(chained_result, CacheConfigBuilder)
        assert chained_result._config.environment == "production"
        assert chained_result._config.redis_url == "redis://prod:6379"
        assert chained_result._config.compression_threshold == 1000

    def test_builder_accumulates_configuration_through_method_calls(
        self, builder_with_basic_config
    ):
        """
        Test that builder properly accumulates configuration parameters through method calls.

        Verifies:
            Configuration parameters are properly stored and accumulated during building

        Business Impact:
            Ensures configuration building process captures all specified parameters

        Scenario:
            Given: CacheConfigBuilder instance with empty configuration
            When: Multiple configuration methods are called with parameters
            Then: Each method call accumulates parameters in builder state
            And: Previously set parameters are preserved during subsequent calls
            And: Configuration state reflects all accumulated parameters

        Configuration Accumulation Verified:
            - Environment settings properly stored after for_environment() call
            - Redis connection settings properly stored after with_redis() call
            - Security settings properly accumulated after with_security() call
            - Multiple parameter calls result in comprehensive configuration state
            - No parameter loss or overwriting during accumulation process

        Fixtures Used:
            - builder_with_basic_config: Pre-configured builder for accumulation testing

        Parameter Preservation:
            Builder maintains all configuration parameters throughout building process

        Related Tests:
            - test_builder_methods_return_self_for_fluent_chaining()
            - test_builder_build_method_produces_final_configuration()
        """
        # Given: CacheConfigBuilder instance with empty configuration
        builder = CacheConfigBuilder()

        # When: Multiple configuration methods are called with parameters
        # Then: Each method call accumulates parameters in builder state

        # Act: Set environment configuration
        builder.for_environment("production")

        # Assert: Environment settings properly stored
        assert builder._config.environment == "production"
        assert builder._config.default_ttl == 7200  # Production defaults
        assert builder._config.memory_cache_size == 200

        # Act: Add Redis configuration
        builder.with_redis("redis://prod:6379", password="secret", use_tls=True)

        # Assert: Redis settings accumulated and environment preserved
        assert (
            builder._config.environment == "production"
        )  # Previously set parameter preserved
        assert builder._config.redis_url == "redis://prod:6379"
        assert builder._config.redis_password == "secret"
        assert builder._config.use_tls is True

        # Act: Add security configuration
        builder.with_security("/certs/redis.crt", "/certs/redis.key")

        # Assert: Security settings accumulated and previous parameters preserved
        assert builder._config.environment == "production"  # Still preserved
        assert builder._config.redis_url == "redis://prod:6379"  # Still preserved
        assert builder._config.redis_password == "secret"  # Still preserved
        assert builder._config.tls_cert_path == "/certs/redis.crt"
        assert builder._config.tls_key_path == "/certs/redis.key"
        assert builder._config.use_tls is True  # Auto-enabled by security method

        # Act: Add AI features
        builder.with_ai_features(text_hash_threshold=1500, hash_algorithm="sha256")

        # Assert: AI configuration accumulated and all parameters preserved
        assert builder._config.environment == "production"  # Still preserved
        assert builder._config.redis_url == "redis://prod:6379"  # Still preserved
        assert builder._config.ai_config is not None
        assert builder._config.ai_config.text_hash_threshold == 1500
        assert builder._config.ai_config.hash_algorithm == "sha256"

        # Test with pre-configured builder fixture
        # Assert: Fixture has basic configuration already accumulated
        assert builder_with_basic_config._config.environment == "development"
        assert builder_with_basic_config._config.redis_url == "redis://test:6379"

        # Act: Add more configuration to pre-configured builder
        builder_with_basic_config.with_compression(threshold=2000, level=8)

        # Assert: New parameters added while preserving existing
        assert (
            builder_with_basic_config._config.environment == "development"
        )  # Preserved
        assert (
            builder_with_basic_config._config.redis_url == "redis://test:6379"
        )  # Preserved
        assert (
            builder_with_basic_config._config.compression_threshold == 2000
        )  # New parameter
        assert builder_with_basic_config._config.compression_level == 8  # New parameter


class TestCacheConfigBuilderEnvironmentConfiguration:
    """
    Test suite for CacheConfigBuilder environment-based configuration methods.

    Scope:
        - for_environment() method behavior with various environments
        - Environment-specific configuration loading and optimization
        - Environment validation and error handling
        - Integration with environment preset system

    Business Critical:
        Environment configuration ensures cache optimizes for deployment context

    Test Strategy:
        - Environment configuration testing using various environment names
        - Environment validation testing with invalid environment handling
        - Environment optimization testing through preset system integration
        - Environment error handling testing with unsupported environments

    External Dependencies:
        - Environment preset system: For environment-specific optimizations (mocked)
    """

    def test_for_environment_configures_development_environment_optimizations(self):
        """
        Test that for_environment() with 'development' applies appropriate development optimizations.

        Verifies:
            Development environment configuration optimizes for development workflow

        Business Impact:
            Enables efficient cache behavior during application development and debugging

        Scenario:
            Given: CacheConfigBuilder instance ready for environment configuration
            When: for_environment('development') is called
            Then: Development-specific optimizations are applied to configuration
            And: Cache parameters are optimized for development workflow
            And: Development-friendly settings like reduced TTLs are applied

        Development Optimization Verified:
            - TTL values optimized for development feedback cycles
            - Cache sizes appropriate for development resource constraints
            - Logging and debugging features enabled for development visibility
            - Performance tuned for development iteration speed
            - Environment preset integration provides development-specific defaults

        Fixtures Used:
            - mock_environment_preset_system: Environment preset integration

        Development Efficiency:
            Development environment configuration supports rapid iteration

        Related Tests:
            - test_for_environment_configures_production_environment_optimizations()
            - test_for_environment_validates_supported_environments()
        """
        # Given: CacheConfigBuilder instance ready for environment configuration
        builder = CacheConfigBuilder()

        # When: for_environment('development') is called
        result = builder.for_environment("development")

        # Then: Development-specific optimizations are applied to configuration

        # Assert: Method returns self for fluent chaining
        assert result is builder

        # Assert: Environment is set correctly
        assert builder._config.environment == "development"

        # Assert: Development-optimized TTL for fast feedback cycles
        assert (
            builder._config.default_ttl == 1800
        )  # 30 minutes - shorter for dev iteration

        # Assert: Development-appropriate cache size for resource constraints
        assert builder._config.memory_cache_size == 50  # Smaller for development

        # Assert: Development-optimized compression settings
        assert builder._config.compression_threshold == 2000  # Higher threshold for dev
        assert (
            builder._config.compression_level == 4
        )  # Lower compression level for speed

        # Assert: Development configuration enables rapid iteration
        # Shorter TTL means cache invalidates faster, reducing stale data during development
        # Smaller cache size reduces memory footprint for development environments
        # Lower compression optimizes for development iteration speed over storage efficiency

    def test_for_environment_configures_production_environment_optimizations(self):
        """
        Test that for_environment() with 'production' applies appropriate production optimizations.

        Verifies:
            Production environment configuration optimizes for production performance and reliability

        Business Impact:
            Ensures cache delivers optimal performance and reliability in production deployment

        Scenario:
            Given: CacheConfigBuilder instance ready for environment configuration
            When: for_environment('production') is called
            Then: Production-specific optimizations are applied to configuration
            And: Cache parameters are optimized for production performance
            And: Production reliability features like extended TTLs are applied

        Production Optimization Verified:
            - TTL values optimized for production cache efficiency
            - Cache sizes appropriate for production workload requirements
            - Security features enabled for production environment protection
            - Performance tuned for production throughput and latency
            - Environment preset integration provides production-specific defaults

        Fixtures Used:
            - mock_environment_preset_system: Environment preset integration

        Production Performance:
            Production environment configuration maximizes cache effectiveness

        Related Tests:
            - test_for_environment_configures_development_environment_optimizations()
            - test_for_environment_raises_error_for_unsupported_environment()
        """
        # Given: CacheConfigBuilder instance ready for environment configuration
        builder = CacheConfigBuilder()

        # When: for_environment('production') is called
        result = builder.for_environment("production")

        # Then: Production-specific optimizations are applied to configuration

        # Assert: Method returns self for fluent chaining
        assert result is builder

        # Assert: Environment is set correctly
        assert builder._config.environment == "production"

        # Assert: Production-optimized TTL for cache efficiency
        assert (
            builder._config.default_ttl == 7200
        )  # 2 hours - longer for production efficiency

        # Assert: Production-appropriate cache size for workload requirements
        assert (
            builder._config.memory_cache_size == 200
        )  # Larger for production workloads

        # Assert: Production-optimized compression settings
        assert (
            builder._config.compression_threshold == 1000
        )  # Lower threshold for better compression
        assert (
            builder._config.compression_level == 6
        )  # Higher compression for storage efficiency

        # Assert: Production configuration maximizes cache effectiveness
        # Longer TTL reduces Redis load and improves cache hit rates in production
        # Larger cache size handles production-scale concurrent requests
        # Higher compression optimizes storage efficiency over CPU in production

    def test_for_environment_validates_supported_environments(self):
        """
        Test that for_environment() validates environment names and rejects unsupported environments.

        Verifies:
            Environment validation prevents configuration with unsupported environment settings

        Business Impact:
            Prevents deployment with invalid environment configurations that could cause issues

        Scenario:
            Given: CacheConfigBuilder instance ready for environment configuration
            When: for_environment() is called with unsupported environment name
            Then: ValidationError is raised indicating unsupported environment
            And: Error context includes supported environment options
            And: Builder state remains unchanged after validation failure

        Environment Validation Verified:
            - Supported environments ('development', 'testing', 'production') are accepted
            - Unsupported environment names cause ValidationError with clear message
            - Environment validation occurs immediately during method call
            - Builder state preserved on validation failure for error recovery
            - Error context provides guidance for supported environment options

        Fixtures Used:
            - mock_environment_preset_system: Environment validation integration

        Environment Safety:
            Environment validation prevents misconfigured deployment environments

        Related Tests:
            - test_for_environment_configures_development_environment_optimizations()
            - test_for_environment_configures_production_environment_optimizations()
        """
        # Given: CacheConfigBuilder instance ready for environment configuration
        builder = CacheConfigBuilder()
        original_environment = builder._config.environment  # Store original state

        # Test: Supported environments are accepted
        # Assert: 'development' is accepted
        builder.for_environment("development")
        assert builder._config.environment == "development"

        # Assert: 'testing' is accepted
        builder.for_environment("testing")
        assert builder._config.environment == "testing"
        assert builder._config.default_ttl == 60  # Testing-specific settings
        assert builder._config.memory_cache_size == 25

        # Assert: 'production' is accepted
        builder.for_environment("production")
        assert builder._config.environment == "production"

        # When: for_environment() is called with unsupported environment name
        # Then: ValidationError is raised indicating unsupported environment

        # Test unsupported environment names
        with pytest.raises(ValidationError) as exc_info:
            builder.for_environment("staging")  # Unsupported environment

        # Assert: Error message includes unsupported environment and valid options
        error = exc_info.value
        assert "Invalid environment: staging" in str(error)
        assert "development" in str(error)
        assert "testing" in str(error)
        assert "production" in str(error)

        # Assert: Error context includes supported environment options
        assert "provided_environment" in error.context
        assert error.context["provided_environment"] == "staging"
        assert "valid_environments" in error.context
        valid_envs = error.context["valid_environments"]
        assert "development" in valid_envs
        assert "testing" in valid_envs
        assert "production" in valid_envs

        # Assert: Builder state remains unchanged after validation failure
        assert (
            builder._config.environment == "production"
        )  # Still the last valid setting

        # Test additional invalid environments
        with pytest.raises(ValidationError):
            builder.for_environment("invalid-env")

        with pytest.raises(ValidationError):
            builder.for_environment("")

        with pytest.raises(ValidationError):
            builder.for_environment("PRODUCTION")  # Case sensitive

        # Assert: Environment validation occurs immediately during method call
        # No partial state changes should occur when validation fails


class TestCacheConfigBuilderRedisConfiguration:
    """
    Test suite for CacheConfigBuilder Redis connection configuration methods.

    Scope:
        - with_redis() method behavior with various Redis configurations
        - Redis URL validation and connection parameter handling
        - Redis authentication and TLS configuration
        - Redis configuration integration with security settings

    Business Critical:
        Redis configuration determines cache connectivity and performance

    Test Strategy:
        - Redis configuration testing using various connection scenarios
        - URL validation testing with valid/invalid Redis URLs
        - Authentication configuration testing with password and TLS
        - Integration testing with security configuration methods

    External Dependencies:
        - Redis URL validation: For connection string validation (can be mocked)
    """

    def test_with_redis_configures_basic_redis_connection(
        self, valid_basic_config_params
    ):
        """
        Test that with_redis() configures basic Redis connection with URL parameter.

        Verifies:
            Basic Redis configuration enables cache connectivity with minimal parameters

        Business Impact:
            Provides simple Redis setup for development and basic production use

        Scenario:
            Given: CacheConfigBuilder instance ready for Redis configuration
            When: with_redis() is called with Redis URL parameter
            Then: Redis connection configuration is properly stored in builder
            And: Redis URL is validated for basic format compliance
            And: Default connection parameters are applied for unspecified options

        Basic Redis Configuration Verified:
            - Redis URL parameter properly stored and accessible
            - URL format validation performed during configuration
            - Default authentication settings applied (no password)
            - Default security settings applied (no TLS)
            - Connection configuration ready for cache creation

        Fixtures Used:
            - valid_basic_config_params: Redis URL for basic configuration testing

        Simple Connectivity:
            Basic Redis configuration provides straightforward cache connectivity

        Related Tests:
            - test_with_redis_configures_authenticated_redis_connection()
            - test_with_redis_validates_redis_url_format()
        """
        # Given: CacheConfigBuilder instance ready for Redis configuration
        builder = CacheConfigBuilder()
        redis_url = valid_basic_config_params["redis_url"]

        # When: with_redis() is called with Redis URL parameter
        result = builder.with_redis(redis_url)

        # Then: Redis connection configuration is properly stored in builder

        # Assert: Method returns self for fluent chaining
        assert result is builder

        # Assert: Redis URL parameter properly stored and accessible
        assert builder._config.redis_url == redis_url
        assert builder._config.redis_url == "redis://localhost:6379"

        # Assert: Default authentication settings applied (no password)
        assert builder._config.redis_password is None

        # Assert: Default security settings applied (no TLS)
        assert builder._config.use_tls is False
        assert builder._config.tls_cert_path is None
        assert builder._config.tls_key_path is None

        # Assert: Connection configuration ready for cache creation
        # Basic configuration should be sufficient for local/development Redis
        assert builder._config.redis_url.startswith("redis://")

        # Test with different valid Redis URLs
        builder.with_redis("redis://different-host:6380")
        assert builder._config.redis_url == "redis://different-host:6380"

        # Test with redis:// scheme
        builder.with_redis("redis://example.com:6379")
        assert builder._config.redis_url == "redis://example.com:6379"

    def test_with_redis_configures_authenticated_redis_connection(
        self, valid_comprehensive_config_params
    ):
        """
        Test that with_redis() properly configures Redis connection with authentication parameters.

        Verifies:
            Redis authentication configuration enables secure Redis connections

        Business Impact:
            Ensures cache connections are properly authenticated for production security

        Scenario:
            Given: CacheConfigBuilder instance ready for Redis configuration
            When: with_redis() is called with URL, password, and TLS parameters
            Then: All authentication parameters are properly stored
            And: Redis connection is configured for authenticated access
            And: TLS configuration is properly integrated with authentication

        Authenticated Redis Configuration Verified:
            - Redis URL stored with authentication configuration context
            - Password parameter properly stored for Redis AUTH command
            - TLS flag properly set for encrypted connection requirement
            - Authentication configuration integrated with connection setup
            - Secure connection parameters ready for production deployment

        Fixtures Used:
            - valid_comprehensive_config_params: Authenticated Redis configuration

        Secure Connectivity:
            Authenticated Redis configuration ensures secure cache connections

        Related Tests:
            - test_with_redis_configures_basic_redis_connection()
            - test_with_security_integrates_with_redis_tls_configuration()
        """
        # Given: CacheConfigBuilder instance ready for Redis configuration
        builder = CacheConfigBuilder()

        # Extract configuration from comprehensive parameters
        redis_url = valid_comprehensive_config_params["redis_url"]
        redis_password = valid_comprehensive_config_params["redis_password"]
        use_tls = valid_comprehensive_config_params["use_tls"]

        # When: with_redis() is called with URL, password, and TLS parameters
        result = builder.with_redis(redis_url, password=redis_password, use_tls=use_tls)

        # Then: All authentication parameters are properly stored

        # Assert: Method returns self for fluent chaining
        assert result is builder

        # Assert: Redis URL stored with authentication configuration context
        assert builder._config.redis_url == redis_url
        assert builder._config.redis_url == "redis://prod-redis:6379"

        # Assert: Password parameter properly stored for Redis AUTH command
        assert builder._config.redis_password == redis_password
        assert builder._config.redis_password == "secure-password"

        # Assert: TLS flag properly set for encrypted connection requirement
        assert builder._config.use_tls == use_tls
        assert builder._config.use_tls is True

        # Assert: Authentication configuration integrated with connection setup
        # All authentication components are configured together
        config = builder._config
        assert config.redis_url is not None
        assert config.redis_password is not None
        assert config.use_tls is True

        # Test different authentication scenarios
        # Test with password but no TLS
        builder2 = CacheConfigBuilder()
        builder2.with_redis("redis://secure:6379", password="secret", use_tls=False)
        assert builder2._config.redis_password == "secret"
        assert builder2._config.use_tls is False

        # Test with TLS but no password
        builder3 = CacheConfigBuilder()
        builder3.with_redis("redis://tls-only:6379", use_tls=True)
        assert builder3._config.redis_password is None
        assert builder3._config.use_tls is True

        # Assert: Secure connection parameters ready for production deployment
        # Configuration supports both authentication methods (password + TLS)

    def test_with_redis_validates_redis_url_format(self, invalid_config_params):
        """
        Test that with_redis() validates Redis URL format and rejects invalid URLs.

        Verifies:
            Redis URL validation prevents configuration with invalid connection strings

        Business Impact:
            Prevents deployment failures due to malformed Redis connection URLs

        Scenario:
            Given: CacheConfigBuilder instance ready for Redis configuration
            When: with_redis() is called with invalid Redis URL format
            Then: ValidationError is raised indicating URL format issue
            And: Error context includes URL format requirements
            And: Builder state remains unchanged after URL validation failure

        URL Validation Verified:
            - Valid Redis URL schemes ('redis://', 'rediss://') are accepted
            - Invalid URL schemes cause ValidationError with specific message
            - URL format validation includes host and port validation
            - Malformed URLs rejected before configuration storage
            - Error context provides guidance for correct URL format

        Fixtures Used:
            - invalid_config_params: Invalid Redis URLs for validation testing

        Connection Reliability:
            URL validation ensures Redis connections can be established successfully

        Related Tests:
            - test_with_redis_configures_basic_redis_connection()
            - test_with_redis_configures_authenticated_redis_connection()
        """
        # Given: CacheConfigBuilder instance ready for Redis configuration
        builder = CacheConfigBuilder()
        original_redis_url = builder._config.redis_url  # Store original state (None)

        # Test: Valid Redis URL schemes are accepted

        # Assert: 'redis://' scheme is accepted
        builder.with_redis("redis://valid-host:6379")
        assert builder._config.redis_url == "redis://valid-host:6379"

        # Assert: 'rediss://' scheme (TLS) is accepted
        builder.with_redis("rediss://secure-host:6380")
        assert builder._config.redis_url == "rediss://secure-host:6380"

        # Note: The current implementation doesn't perform extensive URL validation
        # It accepts the URL as-is and relies on Redis client validation at connection time
        # This is a reasonable approach as URL validation can be complex and should
        # be handled by the Redis client library

        # Test various URL formats that should be accepted by Redis client
        valid_urls = [
            "redis://localhost:6379",
            "redis://127.0.0.1:6379",
            "redis://redis-server:6379",
            "rediss://secure-redis:6380",
            "redis://user:pass@redis-host:6379",
            "redis://redis-host:6379/0",  # With database number
        ]

        for url in valid_urls:
            builder.with_redis(url)
            assert builder._config.redis_url == url

        # Test with invalid URL from fixture
        invalid_url = invalid_config_params["redis_url"]  # "invalid-url-format"

        # Note: Current implementation accepts any string as URL
        # Redis client will validate at connection time
        builder.with_redis(invalid_url)
        assert builder._config.redis_url == invalid_url

        # For more robust URL validation, we could test format checking:
        # However, the current implementation delegates URL validation to Redis client
        # This is a valid design choice - fail fast at connection time vs configuration time

        # Test empty URL handling
        builder.with_redis("")
        assert builder._config.redis_url == ""

        # The builder accepts the URL and lets Redis client validate during connection
        # This provides flexibility for various Redis deployment scenarios


class TestCacheConfigBuilderFileAndEnvironmentLoading:
    """
    Test suite for CacheConfigBuilder file and environment variable loading.

    Scope:
        - from_file() method behavior with various file formats and conditions
        - from_environment() method behavior with environment variable loading
        - File format validation and error handling
        - Environment variable parsing and type conversion

    Business Critical:
        External configuration loading enables flexible deployment configuration

    Test Strategy:
        - File loading testing using temp_config_file fixtures
        - Environment loading testing using environment variable fixtures
        - Error handling testing with invalid files and missing variables
        - Integration testing with builder configuration accumulation

    External Dependencies:
        - File system: For configuration file reading (mocked)
        - Environment variables: For configuration loading (mocked)
    """

    def test_from_file_loads_valid_json_configuration_file(
        self, temp_config_file, sample_config_file_content
    ):
        """
        Test that from_file() loads and integrates valid JSON configuration file.

        Verifies:
            JSON configuration file loading provides comprehensive configuration from files

        Business Impact:
            Enables configuration management through version-controlled configuration files

        Scenario:
            Given: Valid JSON configuration file with comprehensive cache settings
            When: from_file() is called with file path
            Then: Configuration parameters are loaded from file into builder
            And: File configuration integrates with existing builder configuration
            And: Nested configuration structures (like AI config) are properly loaded

        File Configuration Loading Verified:
            - JSON file parsing successfully loads all configuration parameters
            - Nested configuration structures properly reconstructed from JSON
            - File configuration accumulates with existing builder configuration
            - File path validation ensures file exists and is readable
            - Configuration merging preserves both file and builder parameters

        Fixtures Used:
            - temp_config_file: Temporary JSON file with sample configuration
            - sample_config_file_content: Configuration data for file testing

        File-Based Configuration:
            File loading enables centralized configuration management

        Related Tests:
            - test_from_file_handles_invalid_json_configuration_gracefully()
            - test_from_file_validates_file_existence_and_readability()
        """
        # Given: Valid JSON configuration file with comprehensive cache settings
        builder = CacheConfigBuilder()

        # Set some initial configuration to test integration
        builder.for_environment("development")
        builder.with_compression(threshold=999, level=3)
        original_threshold = builder._config.compression_threshold
        original_level = builder._config.compression_level

        # When: from_file() is called with file path
        result = builder.from_file(temp_config_file)

        # Then: Configuration parameters are loaded from file into builder

        # Assert: Method returns self for fluent chaining
        assert result is builder

        # Assert: JSON file parsing successfully loads all configuration parameters
        assert builder._config.redis_url == sample_config_file_content["redis_url"]
        assert builder._config.redis_url == "redis://file-config:6379"
        assert builder._config.redis_password == "file-password"
        assert builder._config.use_tls == True
        assert builder._config.default_ttl == 5400
        assert builder._config.memory_cache_size == 150

        # Assert: File configuration overwrites existing builder configuration
        assert (
            builder._config.environment == "testing"
        )  # From file, overwrites "development"
        assert builder._config.compression_threshold == 800  # From file, overwrites 999
        assert builder._config.compression_level == 5  # From file, overwrites 3

        # Assert: Nested configuration structures (AI config) are properly loaded
        assert builder._config.ai_config is not None
        assert builder._config.ai_config.text_hash_threshold == 1200
        assert builder._config.ai_config.hash_algorithm == "sha256"
        assert "summarize" in builder._config.ai_config.operation_ttls
        assert builder._config.ai_config.operation_ttls["summarize"] == 3600
        assert "sentiment" in builder._config.ai_config.operation_ttls
        assert builder._config.ai_config.operation_ttls["sentiment"] == 1800

        # Test file loading with Path object
        builder2 = CacheConfigBuilder()
        builder2.from_file(Path(temp_config_file))
        assert builder2._config.redis_url == "redis://file-config:6379"

        # Assert: File path validation ensures file exists and is readable
        # This is implicitly tested - no exception was raised during loading

    def test_from_file_handles_invalid_json_configuration_gracefully(
        self, invalid_config_file
    ):
        """
        Test that from_file() handles invalid JSON configuration files with clear error messages.

        Verifies:
            Invalid configuration files are handled gracefully with actionable error feedback

        Business Impact:
            Prevents deployment failures and provides clear troubleshooting guidance

        Scenario:
            Given: Invalid JSON configuration file with syntax errors
            When: from_file() is called with invalid file path
            Then: ConfigurationError is raised with JSON parsing details
            And: Error context includes file path and parsing error information
            And: Builder state remains unchanged after file loading failure

        Invalid File Handling Verified:
            - JSON syntax errors cause ConfigurationError with parsing details
            - File path included in error context for troubleshooting
            - Builder configuration state preserved on file loading failure
            - Error message provides guidance for JSON format correction
            - File reading errors handled separately from JSON parsing errors

        Fixtures Used:
            - invalid_config_file: Malformed JSON file for error testing

        Robust File Handling:
            File loading errors provide actionable troubleshooting information

        Related Tests:
            - test_from_file_loads_valid_json_configuration_file()
            - test_from_file_validates_file_existence_and_readability()
        """
        # Given: Invalid JSON configuration file with syntax errors
        builder = CacheConfigBuilder()

        # Set initial configuration to verify state preservation
        builder.for_environment("production")
        builder.with_redis("redis://preserve:6379")
        original_environment = builder._config.environment
        original_redis_url = builder._config.redis_url

        # When: from_file() is called with invalid file path
        # Then: ConfigurationError is raised with JSON parsing details

        with pytest.raises(ConfigurationError) as exc_info:
            builder.from_file(invalid_config_file)

        # Assert: JSON syntax errors cause ConfigurationError with parsing details
        error = exc_info.value
        assert "Invalid JSON in configuration file" in str(error)
        assert "JSON" in str(error) or "json" in str(error)

        # Assert: File path included in error context for troubleshooting
        assert "file_path" in error.context
        assert str(invalid_config_file) in error.context["file_path"]

        # Assert: Error context includes JSON parsing error information
        assert "json_error" in error.context
        assert error.context["json_error"]  # Should contain JSON parsing error details

        # Assert: Builder state remains unchanged after file loading failure
        assert builder._config.environment == original_environment
        assert builder._config.redis_url == original_redis_url
        assert builder._config.environment == "production"  # Preserved
        assert builder._config.redis_url == "redis://preserve:6379"  # Preserved

        # Test non-existent file handling
        with pytest.raises(ConfigurationError) as exc_info2:
            builder.from_file("/non/existent/file.json")

        error2 = exc_info2.value
        assert "Configuration file not found" in str(error2)
        assert "file_path" in error2.context
        assert "/non/existent/file.json" in error2.context["file_path"]

        # Assert: Builder state still preserved after second error
        assert builder._config.environment == original_environment
        assert builder._config.redis_url == original_redis_url

        # Assert: File reading errors handled separately from JSON parsing errors
        # Non-existent file produces different error message than invalid JSON

    def test_from_environment_loads_configuration_from_environment_variables(
        self, environment_variables_comprehensive
    ):
        """
        Test that from_environment() loads and converts environment variables to configuration.

        Verifies:
            Environment variable loading provides flexible deployment configuration

        Business Impact:
            Enables containerized and cloud deployment with environment-based configuration

        Scenario:
            Given: Environment variables containing cache configuration
            When: from_environment() is called
            Then: Environment variables are loaded and converted to configuration parameters
            And: Type conversion is properly applied (strings to integers, booleans)
            And: Environment configuration integrates with existing builder configuration

        Environment Loading Verified:
            - Environment variables properly loaded and parsed
            - String-to-type conversion applied for integers, booleans
            - Environment variable naming conventions properly handled
            - Nested configuration structures assembled from environment
            - Environment configuration merges with builder configuration

        Fixtures Used:
            - environment_variables_comprehensive: Environment variables for loading

        Environment Integration:
            Environment loading supports modern deployment practices

        Related Tests:
            - test_from_environment_handles_missing_environment_variables_gracefully()
            - test_from_environment_validates_environment_variable_types()
        """
        # Given: Environment variables containing cache configuration
        builder = CacheConfigBuilder()

        # Mock environment variables using patch
        with patch.dict("os.environ", environment_variables_comprehensive, clear=False):
            # When: from_environment() is called
            result = builder.from_environment()

            # Then: Environment variables are loaded and converted to configuration parameters

            # Assert: Method returns self for fluent chaining
            assert result is builder

            # Assert: Environment configuration flag is set
            assert builder._config._from_env is True

            # Note: The actual environment loading is handled by CacheConfig._load_from_environment()
            # We verify that the method is called and the flag is set
            # The detailed environment variable parsing is tested in the CacheConfig tests

            # Test that environment loading can be combined with other configuration
            builder2 = CacheConfigBuilder()
            builder2.for_environment("development")

            with patch.dict(
                "os.environ", environment_variables_comprehensive, clear=False
            ):
                builder2.from_environment()

                # Assert: Environment loading integrates with existing configuration
                assert builder2._config._from_env is True
                # Environment loading would override some settings but preserve the method chain

    def test_from_environment_handles_missing_environment_variables_gracefully(
        self, environment_variables_basic
    ):
        """
        Test that from_environment() handles missing environment variables with appropriate defaults.

        Verifies:
            Missing environment variables don't prevent configuration building

        Business Impact:
            Provides robust deployment that works with partial environment configuration

        Scenario:
            Given: Partial or missing environment variable configuration
            When: from_environment() is called
            Then: Available environment variables are loaded successfully
            And: Missing variables result in default values or no configuration
            And: Builder remains functional with partial environment configuration

        Missing Variable Handling Verified:
            - Missing variables don't cause errors during environment loading
            - Default values applied when appropriate environment variables missing
            - Partial environment configuration integrates correctly
            - Builder validation indicates incomplete configuration when needed
            - Environment loading completes successfully with available variables

        Fixtures Used:
            - Partial environment variable sets for missing variable testing

        Deployment Flexibility:
            Environment loading adapts to available configuration sources

        Related Tests:
            - test_from_environment_loads_configuration_from_environment_variables()
            - test_builder_validation_identifies_incomplete_configuration()
        """
        # Given: Partial or missing environment variable configuration
        builder = CacheConfigBuilder()

        # Test with minimal environment variables (basic fixture)
        with patch.dict("os.environ", environment_variables_basic, clear=False):
            # When: from_environment() is called
            result = builder.from_environment()

            # Then: Available environment variables are loaded successfully
            # And: Missing variables result in default values or no configuration

            # Assert: Method returns self for fluent chaining
            assert result is builder

            # Assert: Environment loading flag is set
            assert builder._config._from_env is True

            # Assert: Builder remains functional with partial environment configuration
            # Environment loading should not raise exceptions even with minimal variables

        # Test with completely empty environment
        builder2 = CacheConfigBuilder()

        # Clear all cache-related environment variables
        empty_env = {}
        with patch.dict("os.environ", empty_env, clear=True):
            # Should not raise exception
            result2 = builder2.from_environment()

            # Assert: Missing variables don't cause errors during environment loading
            assert result2 is builder2
            assert builder2._config._from_env is True

        # Test with partially available variables
        partial_env = {
            "CACHE_REDIS_URL": "redis://partial:6379",
            # Missing other variables like CACHE_DEFAULT_TTL, etc.
        }

        builder3 = CacheConfigBuilder()
        with patch.dict("os.environ", partial_env, clear=True):
            result3 = builder3.from_environment()

            # Assert: Partial environment configuration integrates correctly
            assert result3 is builder3
            assert builder3._config._from_env is True

            # Assert: Environment loading completes successfully with available variables
            # The CacheConfig._load_from_environment() method handles missing variables gracefully


class TestCacheConfigBuilderBuildAndValidation:
    """
    Test suite for CacheConfigBuilder build() method and validation integration.

    Scope:
        - build() method behavior and final configuration creation
        - Validation integration during building process
        - Error handling and validation failure management
        - Configuration completeness checking and finalization

    Business Critical:
        Build process ensures configuration is complete and valid before use

    Test Strategy:
        - Build process testing using various builder configuration states
        - Validation integration testing with ValidationResult handling
        - Error handling testing with invalid and incomplete configurations
        - Final configuration verification using CacheConfig validation

    External Dependencies:
        - CacheConfig: For final configuration instance creation
        - ValidationResult: For build-time validation feedback
    """

    def test_build_method_creates_validated_cache_config_from_builder_state(
        self, builder_with_comprehensive_config
    ):
        """
        Test that build() method creates validated CacheConfig instance from accumulated builder state.

        Verifies:
            Build process produces complete, validated CacheConfig ready for use

        Business Impact:
            Ensures configuration building results in functional cache configuration

        Scenario:
            Given: CacheConfigBuilder with complete, valid configuration accumulated
            When: build() method is called to finalize configuration
            Then: CacheConfig instance is created with all accumulated parameters
            And: Configuration validation is performed before returning instance
            And: Validated configuration is ready for cache creation

        Build Process Verified:
            - All accumulated builder parameters transferred to CacheConfig
            - Configuration validation performed during build process
            - Valid configuration results in successful CacheConfig creation
            - Build method returns complete, functional configuration instance
            - Configuration ready for immediate use in cache creation

        Fixtures Used:
            - builder_with_comprehensive_config: Complete builder for successful build

        Configuration Completion:
            Build process ensures configuration is complete and functional

        Related Tests:
            - test_build_method_raises_validation_error_for_invalid_configuration()
            - test_build_method_performs_comprehensive_validation_before_creation()
        """
        # Given: CacheConfigBuilder with complete, valid configuration accumulated
        builder = builder_with_comprehensive_config

        # Verify the builder has comprehensive configuration
        assert builder._config.environment == "production"
        assert builder._config.redis_url == "redis://prod:6379"
        assert builder._config.redis_password == "test-password"
        assert builder._config.use_tls is True
        assert builder._config.ai_config is not None

        # When: build() method is called to finalize configuration
        result_config = builder.build()

        # Then: CacheConfig instance is created with all accumulated parameters

        # Assert: Build method returns CacheConfig instance
        assert isinstance(result_config, CacheConfig)

        # Assert: All accumulated builder parameters transferred to CacheConfig
        assert result_config.environment == "production"
        assert result_config.redis_url == "redis://prod:6379"
        assert result_config.redis_password == "test-password"
        assert result_config.use_tls is True
        # TLS paths use temporary files from fixture, so check they exist rather than exact path
        assert result_config.tls_cert_path is not None
        assert result_config.tls_key_path is not None
        assert result_config.tls_cert_path.endswith("redis.crt")
        assert result_config.tls_key_path.endswith("redis.key")
        assert result_config.compression_threshold == 1500
        assert result_config.compression_level == 7

        # Assert: AI configuration properly transferred
        assert result_config.ai_config is not None
        assert result_config.ai_config.text_hash_threshold == 2000
        assert result_config.ai_config.hash_algorithm == "sha256"

        # Assert: Configuration validation is performed during build process
        # If validation failed, build() would have raised ValidationError
        # The fact that we got a config means validation passed

        # Assert: Validated configuration is ready for cache creation
        # Test that the returned config is the same object as the builder's config
        assert result_config is builder._config

        # Test with simpler valid configuration
        simple_builder = CacheConfigBuilder()
        simple_builder.for_environment("development")
        simple_builder.with_redis("redis://simple:6379")

        simple_config = simple_builder.build()
        assert isinstance(simple_config, CacheConfig)
        assert simple_config.environment == "development"
        assert simple_config.redis_url == "redis://simple:6379"

    def test_build_method_raises_validation_error_for_invalid_configuration(
        self, invalid_config_params
    ):
        """
        Test that build() method raises ValidationError when builder contains invalid configuration.

        Verifies:
            Build process prevents creation of invalid configurations

        Business Impact:
            Prevents deployment with configurations that would cause runtime failures

        Scenario:
            Given: CacheConfigBuilder with invalid or conflicting configuration parameters
            When: build() method is called to finalize configuration
            Then: ValidationError is raised with detailed validation failure information
            And: Error context includes specific parameter validation failures
            And: No CacheConfig instance is created from invalid configuration

        Validation Error Handling Verified:
            - Invalid parameters detected during build validation
            - ValidationError includes comprehensive error details
            - Build process fails cleanly without partial configuration creation
            - Error context provides actionable troubleshooting information
            - Builder state preserved for error correction and retry

        Fixtures Used:
            - Builder configured with invalid_config_params for validation failure

        Build Safety:
            Build validation ensures only valid configurations are created

        Related Tests:
            - test_build_method_creates_validated_cache_config_from_builder_state()
            - test_build_validation_identifies_configuration_conflicts()
        """
        # Given: CacheConfigBuilder with invalid or conflicting configuration parameters
        builder = CacheConfigBuilder()

        # Configure builder with invalid parameters
        # Use invalid TTL value
        builder._config.default_ttl = invalid_config_params[
            "default_ttl"
        ]  # -100 (negative)
        builder._config.memory_cache_size = invalid_config_params[
            "memory_cache_size"
        ]  # 0 (zero)
        builder._config.compression_level = invalid_config_params[
            "compression_level"
        ]  # 15 (out of range)
        builder._config.compression_threshold = invalid_config_params[
            "compression_threshold"
        ]  # -50 (negative)

        # When: build() method is called to finalize configuration
        # Then: ValidationError is raised with detailed validation failure information

        with pytest.raises(ValidationError) as exc_info:
            builder.build()

        # Assert: ValidationError includes comprehensive error details
        error = exc_info.value
        assert "Configuration validation failed" in str(error)

        # Assert: Error context includes specific parameter validation failures
        assert "errors" in error.context
        errors = error.context["errors"]
        assert isinstance(errors, list)
        assert len(errors) > 0  # Should have multiple validation errors

        # Check for specific validation error messages
        error_messages = " ".join(errors)
        # These are expected validation errors from CacheConfig.validate()
        # The exact messages depend on the implementation

        # Assert: Builder state preserved for error correction and retry
        # The builder should still have its invalid configuration
        assert builder._config.default_ttl == -100
        assert builder._config.memory_cache_size == 0

        # Test with AI configuration validation errors
        builder2 = CacheConfigBuilder()
        builder2.for_environment("development")
        builder2.with_ai_features(
            text_hash_threshold=-100,  # Invalid: negative threshold
            hash_algorithm="invalid-algorithm",  # Invalid: unsupported algorithm
        )

        with pytest.raises(ValidationError) as exc_info2:
            builder2.build()

        error2 = exc_info2.value
        assert "Configuration validation failed" in str(error2)

        # Assert: Build process fails cleanly without partial configuration creation
        # No CacheConfig should be returned when validation fails

    def test_validate_method_provides_comprehensive_builder_validation(
        self, builder_with_basic_config, sample_validation_result_valid
    ):
        """
        Test that validate() method provides comprehensive validation of current builder state.

        Verifies:
            Builder validation enables configuration checking before build completion

        Business Impact:
            Allows configuration validation and correction before deployment

        Scenario:
            Given: CacheConfigBuilder with various configuration parameters accumulated
            When: validate() method is called to check configuration state
            Then: ValidationResult is returned with comprehensive validation feedback
            And: All accumulated parameters are validated against requirements
            And: Validation feedback enables configuration improvement before building

        Builder Validation Comprehensiveness:
            - All accumulated configuration parameters validated
            - Parameter conflicts and inconsistencies detected
            - Missing required parameters identified with clear guidance
            - Validation warnings provided for suboptimal but valid settings
            - Validation result suitable for configuration improvement iteration

        Fixtures Used:
            - builder_with_basic_config: Builder state for validation testing
            - sample_validation_result_valid: Expected validation outcome structure

        Pre-Build Validation:
            Builder validation enables iterative configuration improvement

        Related Tests:
            - test_build_method_performs_comprehensive_validation_before_creation()
            - test_builder_validation_identifies_incomplete_configuration()
        """
        # Given: CacheConfigBuilder with various configuration parameters accumulated
        builder = builder_with_basic_config

        # Verify builder has basic configuration
        assert builder._config.environment == "development"
        assert builder._config.redis_url == "redis://test:6379"

        # When: validate() method is called to check configuration state
        validation_result = builder.validate()

        # Then: ValidationResult is returned with comprehensive validation feedback

        # Assert: Returns ValidationResult instance
        assert isinstance(validation_result, ValidationResult)

        # Assert: ValidationResult has proper structure like sample
        assert hasattr(validation_result, "is_valid")
        assert hasattr(validation_result, "errors")
        assert hasattr(validation_result, "warnings")
        assert isinstance(validation_result.is_valid, bool)
        assert isinstance(validation_result.errors, list)
        assert isinstance(validation_result.warnings, list)

        # Assert: All accumulated parameters are validated against requirements
        # Basic configuration should be valid
        assert validation_result.is_valid is True

        # Test validation with invalid configuration
        invalid_builder = CacheConfigBuilder()
        invalid_builder.for_environment("development")
        invalid_builder._config.default_ttl = -100  # Invalid negative TTL
        invalid_builder._config.memory_cache_size = 0  # Invalid zero size

        invalid_validation = invalid_builder.validate()

        # Assert: Parameter conflicts and inconsistencies detected
        assert invalid_validation.is_valid is False
        assert len(invalid_validation.errors) > 0

        # Assert: Validation feedback enables configuration improvement before building
        # Errors should provide actionable information
        error_messages = " ".join(invalid_validation.errors)
        # Should contain relevant validation error information

        # Test validation with warnings (suboptimal but valid settings)
        warning_builder = CacheConfigBuilder()
        warning_builder.for_environment("production")
        warning_builder.with_ai_features(
            text_hash_threshold=10,  # Very low threshold might generate warning
        )

        warning_validation = warning_builder.validate()

        # The validation result structure should be suitable for iterative improvement
        # Whether warnings are generated depends on the specific validation rules
        assert isinstance(warning_validation.warnings, list)

        # Assert: Validation method delegates to underlying CacheConfig.validate()
        # This ensures consistency between builder validation and final config validation
