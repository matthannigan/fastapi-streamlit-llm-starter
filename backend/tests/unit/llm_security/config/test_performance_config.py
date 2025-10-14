"""
Test suite for PerformanceConfig Pydantic model.

Tests verify PerformanceConfig initialization, validation, and configuration
according to the public contract defined in config.pyi.
"""

import pytest
from pydantic import ValidationError
from app.infrastructure.security.llm.config import PerformanceConfig


class TestPerformanceConfigInitialization:
    """Test PerformanceConfig model instantiation and defaults."""

    def test_performance_config_initialization_with_defaults(self):
        """
        Test that PerformanceConfig initializes with sensible default values.

        Verifies:
            PerformanceConfig provides default values for all performance settings
            per contract's Attributes section defaults.

        Business Impact:
            Enables quick performance configuration without specifying all parameters
            for standard deployment scenarios.

        Scenario:
            Given: No parameters provided to PerformanceConfig.
            When: PerformanceConfig instance is created.
            Then: All fields have sensible defaults for performance optimization.

        Fixtures Used:
            None - tests default initialization.
        """
        # Given: No parameters provided
        # When: PerformanceConfig instance is created
        config = PerformanceConfig()

        # Then: All fields have sensible defaults
        assert config.enable_model_caching is True  # Model caching enabled by default
        assert config.enable_result_caching is True  # Result caching enabled by default
        assert config.cache_ttl_seconds == 300  # 5 minutes default TTL
        assert config.cache_redis_url is None  # No Redis URL by default (memory-only)
        assert config.max_concurrent_scans == 10  # Moderate concurrent scans
        assert config.max_memory_mb == 2048  # 2GB default memory limit
        assert config.enable_batch_processing is False  # Batch processing disabled by default
        assert config.batch_size == 5  # Small batch size for when enabled
        assert config.enable_async_processing is True  # Async processing enabled by default
        assert config.queue_size == 100  # Moderate queue size
        assert config.metrics_collection_interval == 60  # 1 minute metrics interval
        assert config.health_check_interval == 30  # 30 second health check interval

    def test_performance_config_with_caching_enabled(self):
        """
        Test that PerformanceConfig accepts caching configuration.

        Verifies:
            PerformanceConfig stores enable_model_caching and enable_result_caching
            settings per contract's Attributes section.

        Business Impact:
            Enables caching optimization for faster security scanning through
            model and result reuse.

        Scenario:
            Given: enable_model_caching=True and enable_result_caching=True.
            When: PerformanceConfig is created with caching enabled.
            Then: Caching settings are stored for scanner optimization.

        Fixtures Used:
            None - tests caching configuration.
        """
        # Given: Caching configuration with both model and result caching enabled
        # When: PerformanceConfig is created with caching settings
        config = PerformanceConfig(
            enable_model_caching=True,
            enable_result_caching=True
        )

        # Then: Caching settings are stored correctly
        assert config.enable_model_caching is True
        assert config.enable_result_caching is True

    def test_performance_config_with_redis_cache_url(self):
        """
        Test that PerformanceConfig accepts Redis URL for distributed caching.

        Verifies:
            PerformanceConfig stores cache_redis_url for distributed result caching
            per contract's Attributes section.

        Business Impact:
            Enables distributed caching across multiple application instances for
            optimal cache hit rates.

        Scenario:
            Given: cache_redis_url="redis://cache.example.com:6379".
            When: PerformanceConfig is created with Redis URL.
            Then: Redis URL is stored for distributed cache configuration.

        Fixtures Used:
            None - tests Redis URL configuration.
        """
        # Given: Redis URL for distributed caching
        redis_url = "redis://cache.example.com:6379"

        # When: PerformanceConfig is created with Redis URL
        config = PerformanceConfig(cache_redis_url=redis_url)

        # Then: Redis URL is stored correctly
        assert config.cache_redis_url == redis_url

    def test_performance_config_with_concurrency_limits(self):
        """
        Test that PerformanceConfig accepts concurrency limit configuration.

        Verifies:
            PerformanceConfig stores max_concurrent_scans for resource management
            per contract's Attributes section.

        Business Impact:
            Enables system protection from resource exhaustion through concurrent
            scan limiting.

        Scenario:
            Given: max_concurrent_scans=20.
            When: PerformanceConfig is created with concurrency limit.
            Then: Concurrency limit is stored for scan throttling.

        Fixtures Used:
            None - tests concurrency configuration.
        """
        # Given: Concurrency limit configuration
        max_concurrent = 20

        # When: PerformanceConfig is created with concurrency limit
        config = PerformanceConfig(max_concurrent_scans=max_concurrent)

        # Then: Concurrency limit is stored correctly
        assert config.max_concurrent_scans == max_concurrent

    def test_performance_config_with_memory_limits(self):
        """
        Test that PerformanceConfig accepts memory usage limit configuration.

        Verifies:
            PerformanceConfig stores max_memory_mb for memory management per
            contract's Attributes section.

        Business Impact:
            Enables memory usage control to prevent system resource exhaustion
            during security scanning.

        Scenario:
            Given: max_memory_mb=4096 (4GB).
            When: PerformanceConfig is created with memory limit.
            Then: Memory limit is stored for resource management.

        Fixtures Used:
            None - tests memory configuration.
        """
        # Given: Memory limit configuration
        max_memory = 4096  # 4GB

        # When: PerformanceConfig is created with memory limit
        config = PerformanceConfig(max_memory_mb=max_memory)

        # Then: Memory limit is stored correctly
        assert config.max_memory_mb == max_memory

    def test_performance_config_with_batch_processing_settings(self):
        """
        Test that PerformanceConfig accepts batch processing configuration.

        Verifies:
            PerformanceConfig stores enable_batch_processing and batch_size per
            contract's Attributes section.

        Business Impact:
            Enables batch processing optimization for higher throughput when
            processing multiple security scans.

        Scenario:
            Given: enable_batch_processing=True and batch_size=10.
            When: PerformanceConfig is created with batch settings.
            Then: Batch processing configuration is stored for optimization.

        Fixtures Used:
            None - tests batch processing configuration.
        """
        # Given: Batch processing configuration
        enable_batch = True
        batch_size = 10

        # When: PerformanceConfig is created with batch settings
        config = PerformanceConfig(
            enable_batch_processing=enable_batch,
            batch_size=batch_size
        )

        # Then: Batch processing configuration is stored correctly
        assert config.enable_batch_processing == enable_batch
        assert config.batch_size == batch_size

    def test_performance_config_with_async_processing_settings(self):
        """
        Test that PerformanceConfig accepts async processing configuration.

        Verifies:
            PerformanceConfig stores enable_async_processing and queue_size per
            contract's Attributes section.

        Business Impact:
            Enables asynchronous processing for better throughput and system
            responsiveness under load.

        Scenario:
            Given: enable_async_processing=True and queue_size=100.
            When: PerformanceConfig is created with async settings.
            Then: Async processing configuration is stored for optimization.

        Fixtures Used:
            None - tests async processing configuration.
        """
        # Given: Async processing configuration
        enable_async = True
        queue_size = 100

        # When: PerformanceConfig is created with async settings
        config = PerformanceConfig(
            enable_async_processing=enable_async,
            queue_size=queue_size
        )

        # Then: Async processing configuration is stored correctly
        assert config.enable_async_processing == enable_async
        assert config.queue_size == queue_size

    def test_performance_config_with_monitoring_intervals(self):
        """
        Test that PerformanceConfig accepts monitoring interval configuration.

        Verifies:
            PerformanceConfig stores metrics_collection_interval and health_check_interval
            per contract's Attributes section.

        Business Impact:
            Enables monitoring configuration for performance tracking and health
            checking at appropriate intervals.

        Scenario:
            Given: metrics_collection_interval=60 and health_check_interval=30.
            When: PerformanceConfig is created with monitoring intervals.
            Then: Monitoring configuration is stored for system observability.

        Fixtures Used:
            None - tests monitoring configuration.
        """
        # Given: Monitoring interval configuration
        metrics_interval = 60
        health_check_interval = 30

        # When: PerformanceConfig is created with monitoring intervals
        config = PerformanceConfig(
            metrics_collection_interval=metrics_interval,
            health_check_interval=health_check_interval
        )

        # Then: Monitoring configuration is stored correctly
        assert config.metrics_collection_interval == metrics_interval
        assert config.health_check_interval == health_check_interval


class TestPerformanceConfigValidation:
    """Test PerformanceConfig Pydantic validation rules."""

    def test_performance_config_validates_cache_ttl_minimum(self):
        """
        Test that PerformanceConfig validates cache TTL minimum boundary (1 minute).

        Verifies:
            validate_cache_ttl() raises ValidationError when cache_ttl_seconds < 60 per
            contract's Raises section.

        Business Impact:
            Prevents excessively short cache TTLs that would cause cache churn and
            performance degradation.

        Scenario:
            Given: cache_ttl_seconds=30 (below 60 second minimum).
            When: PerformanceConfig instantiation is attempted.
            Then: ValidationError is raised indicating TTL below operational minimum.

        Fixtures Used:
            None - tests validation with invalid input.
        """
        # Given: Cache TTL below minimum boundary
        invalid_ttl = 30  # Below 60 second minimum

        # When: PerformanceConfig instantiation is attempted
        # Then: ValidationError is raised with appropriate message
        with pytest.raises(ValidationError) as exc_info:
            PerformanceConfig(cache_ttl_seconds=invalid_ttl)

        # Check that the error indicates the value is too low
        assert "cache_ttl_seconds" in str(exc_info.value)
        assert "greater than or equal to 60" in str(exc_info.value)

    def test_performance_config_validates_cache_ttl_maximum(self):
        """
        Test that PerformanceConfig validates cache TTL maximum boundary (1 hour).

        Verifies:
            validate_cache_ttl() raises ValidationError when cache_ttl_seconds > 3600 per
            contract's Raises section.

        Business Impact:
            Prevents excessively long cache TTLs that could serve stale security
            scan results beyond freshness requirements.

        Scenario:
            Given: cache_ttl_seconds=7200 (above 3600 second maximum).
            When: PerformanceConfig instantiation is attempted.
            Then: ValidationError is raised indicating TTL exceeds operational limit.

        Fixtures Used:
            None - tests validation with invalid input.
        """
        # Given: Cache TTL above maximum boundary
        invalid_ttl = 7200  # Above 3600 second maximum

        # When: PerformanceConfig instantiation is attempted
        # Then: ValidationError is raised with appropriate message
        with pytest.raises(ValidationError) as exc_info:
            PerformanceConfig(cache_ttl_seconds=invalid_ttl)

        # Check that the error indicates the value is too high
        assert "cache_ttl_seconds" in str(exc_info.value)
        assert "less than or equal to 3600" in str(exc_info.value)

    def test_performance_config_validates_concurrent_scans_minimum(self):
        """
        Test that PerformanceConfig validates concurrent scans minimum boundary (1).

        Verifies:
            validate_concurrent_scans() raises ValidationError when max_concurrent_scans < 1
            per contract's Raises section.

        Business Impact:
            Ensures minimum capacity for security scanning operations with at least
            one concurrent scan allowed.

        Scenario:
            Given: max_concurrent_scans=0 (below minimum).
            When: PerformanceConfig instantiation is attempted.
            Then: ValidationError is raised indicating insufficient concurrent capacity.

        Fixtures Used:
            None - tests validation with invalid input.
        """
        # Given: Concurrent scans below minimum boundary
        invalid_concurrent = 0  # Below minimum of 1

        # When: PerformanceConfig instantiation is attempted
        # Then: ValidationError is raised with appropriate message
        with pytest.raises(ValidationError) as exc_info:
            PerformanceConfig(max_concurrent_scans=invalid_concurrent)

        # Check that the error indicates the value is too low
        assert "max_concurrent_scans" in str(exc_info.value)
        assert "greater than or equal to 1" in str(exc_info.value)

    def test_performance_config_validates_concurrent_scans_maximum(self):
        """
        Test that PerformanceConfig validates concurrent scans maximum boundary (100).

        Verifies:
            validate_concurrent_scans() raises ValidationError when max_concurrent_scans > 100
            per contract's Raises section.

        Business Impact:
            Prevents resource exhaustion from excessive parallelism beyond system
            capabilities.

        Scenario:
            Given: max_concurrent_scans=150 (above maximum).
            When: PerformanceConfig instantiation is attempted.
            Then: ValidationError is raised indicating excessive concurrent capacity.

        Fixtures Used:
            None - tests validation with invalid input.
        """
        # Given: Concurrent scans above maximum boundary
        invalid_concurrent = 150  # Above maximum of 100

        # When: PerformanceConfig instantiation is attempted
        # Then: ValidationError is raised with appropriate message
        with pytest.raises(ValidationError) as exc_info:
            PerformanceConfig(max_concurrent_scans=invalid_concurrent)

        # Check that the error indicates the value is too high
        assert "max_concurrent_scans" in str(exc_info.value)
        assert "less than or equal to 100" in str(exc_info.value)


class TestPerformanceConfigUsagePatterns:
    """Test PerformanceConfig usage in typical scenarios."""

    def test_performance_config_for_high_performance_production(self):
        """
        Test PerformanceConfig configuration for high-performance production deployment.

        Verifies:
            PerformanceConfig supports high-performance settings per contract's
            Usage example for production.

        Business Impact:
            Enables optimal performance configuration for production deployments
            with distributed caching and high concurrency.

        Scenario:
            Given: Production-optimized performance settings.
            When: PerformanceConfig is created with high-performance values.
            Then: Configuration supports production performance requirements.

        Fixtures Used:
            None - tests production configuration pattern.
        """
        # Given: High-performance production settings
        production_config = PerformanceConfig(
            enable_model_caching=True,           # Cache models for faster loading
            enable_result_caching=True,           # Cache results to avoid reprocessing
            cache_ttl_seconds=1800,              # 30 minutes TTL for optimal performance
            cache_redis_url="redis://cache.example.com:6379",  # Distributed caching
            max_concurrent_scans=20,             # High concurrency for production
            max_memory_mb=4096,                  # 4GB memory for production workloads
            enable_batch_processing=True,         # Batch processing for throughput
            batch_size=10,                       # Moderate batch size
            enable_async_processing=True,         # Async for better throughput
            queue_size=100                       # Reasonable queue size
        )

        # When: PerformanceConfig is created with production settings
        # (Configuration created in given section)

        # Then: Configuration supports production performance requirements
        assert production_config.enable_model_caching is True
        assert production_config.enable_result_caching is True
        assert production_config.cache_ttl_seconds == 1800  # 30 minutes
        assert production_config.cache_redis_url == "redis://cache.example.com:6379"
        assert production_config.max_concurrent_scans == 20
        assert production_config.max_memory_mb == 4096  # 4GB
        assert production_config.enable_batch_processing is True
        assert production_config.batch_size == 10
        assert production_config.enable_async_processing is True
        assert production_config.queue_size == 100

    def test_performance_config_for_minimal_development(self):
        """
        Test PerformanceConfig configuration for minimal development deployment.

        Verifies:
            PerformanceConfig supports minimal settings per contract's Usage
            example for development.

        Business Impact:
            Enables lightweight configuration for development with caching disabled
            and minimal resource usage.

        Scenario:
            Given: Development-optimized minimal settings.
            When: PerformanceConfig is created with minimal values.
            Then: Configuration supports development requirements.

        Fixtures Used:
            None - tests development configuration pattern.
        """
        # Given: Minimal development settings
        dev_config = PerformanceConfig(
            enable_result_caching=False,        # Fresh scans each time for development
            max_concurrent_scans=2,             # Low concurrency for development
            max_memory_mb=1024,                 # 1GB memory limit for development
            enable_batch_processing=False,      # No batch processing for simplicity
            enable_async_processing=False,      # Sync processing for easier debugging
            queue_size=10                       # Small queue for development
        )

        # When: PerformanceConfig is created with minimal development settings
        # (Configuration created in given section)

        # Then: Configuration supports development requirements
        assert dev_config.enable_result_caching is False  # Fresh scans
        assert dev_config.max_concurrent_scans == 2
        assert dev_config.max_memory_mb == 1024  # 1GB
        assert dev_config.enable_batch_processing is False
        assert dev_config.enable_async_processing is False
        assert dev_config.queue_size == 10
        # Default values for other settings
        assert dev_config.enable_model_caching is True  # Still enabled by default
        assert dev_config.cache_ttl_seconds == 300     # Default TTL
        assert dev_config.cache_redis_url is None      # Memory-only cache

    def test_performance_config_for_memory_constrained_deployment(self):
        """
        Test PerformanceConfig configuration for memory-constrained deployment.

        Verifies:
            PerformanceConfig supports memory-limited settings per contract's
            Usage example for limited resources.

        Business Impact:
            Enables deployment on resource-constrained systems with appropriate
            memory limits and reduced caching.

        Scenario:
            Given: Memory-constrained configuration settings.
            When: PerformanceConfig is created with low memory limits.
            Then: Configuration supports constrained resource requirements.

        Fixtures Used:
            None - tests constrained configuration pattern.
        """
        # Given: Memory-constrained settings
        constrained_config = PerformanceConfig(
            max_memory_mb=512,                     # Very low memory limit
            enable_model_caching=False,            # Disable model caching to save memory
            enable_result_caching=True,            # Keep result caching for performance
            cache_ttl_seconds=60,                 # Short TTL to limit memory usage
            max_concurrent_scans=3,                # Low concurrency to reduce memory pressure
            enable_batch_processing=True,          # Enable batching for efficiency
            batch_size=5,                          # Small batch size
            enable_async_processing=False,         # Disable async to reduce memory overhead
            queue_size=20                          # Small queue size
        )

        # When: PerformanceConfig is created with memory-constrained settings
        # (Configuration created in given section)

        # Then: Configuration supports constrained resource requirements
        assert constrained_config.max_memory_mb == 512  # Low memory limit
        assert constrained_config.enable_model_caching is False  # Disabled to save memory
        assert constrained_config.enable_result_caching is True   # Keep result caching
        assert constrained_config.cache_ttl_seconds == 60         # Short TTL
        assert constrained_config.max_concurrent_scans == 3       # Low concurrency
        assert constrained_config.enable_batch_processing is True
        assert constrained_config.batch_size == 5
        assert constrained_config.enable_async_processing is False  # Reduce memory overhead
        assert constrained_config.queue_size == 20
        # Default values for other settings
        assert constrained_config.cache_redis_url is None           # Memory-only cache