"""
Comprehensive cache benchmark configuration management with environment-specific presets.

This module provides complete configuration infrastructure for cache performance benchmarking
including performance thresholds, environment-specific presets, and flexible configuration
loading from multiple sources. Designed for maximum flexibility across development, testing,
production, and CI environments with comprehensive validation and error handling.

Classes:
    CachePerformanceThresholds: Performance threshold definitions with validation
    BenchmarkConfig: Complete benchmark configuration with validation
    ConfigPresets: Environment-specific configuration presets (development, testing, production, ci)

Functions:
    load_config_from_env: Load configuration from environment variables with validation
    load_config_from_file: Load configuration from JSON/YAML files with error handling
    get_default_config: Get validated default configuration settings

Key Features:
    - **Environment-Specific Presets**: Pre-configured settings optimized for development,
      testing, production, and CI environments with appropriate thresholds and iterations.

    - **Flexible Configuration Sources**: Support for environment variables, JSON files,
      YAML files, and programmatic configuration with consistent validation.

    - **Comprehensive Validation**: Built-in validation for all configuration parameters
      with clear error messages and consistency checks.

    - **Performance Thresholds**: Configurable performance thresholds for basic operations,
      memory cache, compression, and regression detection with validation.

    - **Threshold Validation**: Automatic validation of threshold relationships ensuring
      logical consistency (avg <= p95 <= p99, warning < critical, etc.).

    - **Error Handling**: Robust error handling with descriptive ConfigurationError
      messages for troubleshooting configuration issues.

Configuration Hierarchy:
    1. **Environment Variables**: Highest priority for deployment flexibility
    2. **Configuration Files**: JSON/YAML files for complex configurations
    3. **Preset Selection**: Environment-specific presets for common scenarios
    4. **Defaults**: Sensible defaults for immediate use

Environment Presets:
    - **development**: Fast feedback with relaxed thresholds (50 iterations, 100ms avg threshold)
    - **testing**: Balanced settings for automated testing (100 iterations, 50ms avg threshold)
    - **production**: High accuracy with strict thresholds (500 iterations, 25ms avg threshold)
    - **ci**: Optimized for CI/CD pipelines (200 iterations, 75ms avg threshold)

Usage Examples:
    Environment-Specific Presets:
        >>> from app.infrastructure.cache.benchmarks.config import ConfigPresets
        >>>
        >>> # Development configuration
        >>> dev_config = ConfigPresets.development_config()
        >>> print(f"Iterations: {dev_config.default_iterations}")  # 50
        >>>
        >>> # Production configuration
        >>> prod_config = ConfigPresets.production_config()
        >>> print(f"Threshold: {prod_config.thresholds.basic_operations_avg_ms}")  # 25.0

    Environment Variable Configuration:
        >>> import os
        >>> os.environ['BENCHMARK_DEFAULT_ITERATIONS'] = '200'
        >>> os.environ['BENCHMARK_THRESHOLD_BASIC_OPS_AVG_MS'] = '30.0'
        >>> config = load_config_from_env()
        >>> print(f"Loaded iterations: {config.default_iterations}")  # 200

    File-Based Configuration:
        >>> # config.json contains: {"default_iterations": 150, "thresholds": {...}}
        >>> config = load_config_from_file('config.json')
        >>> config.validate()  # Ensures all settings are consistent

    Validation and Error Handling:
        >>> try:
        ...     config = BenchmarkConfig(
        ...         default_iterations=-10,  # Invalid
        ...         thresholds=CachePerformanceThresholds(
        ...             basic_operations_avg_ms=100,
        ...             basic_operations_p95_ms=50  # Invalid: p95 < avg
        ...         )
        ...     )
        ...     config.validate()
        ... except ConfigurationError as e:
        ...     print(f"Configuration error: {e}")

Thread Safety:
    All configuration classes are immutable after construction and thread-safe.
    Configuration loading functions are stateless and safe for concurrent use.
"""

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict
from app.core.exceptions import ConfigurationError


@dataclass
class CachePerformanceThresholds:
    """
    Performance threshold definitions for cache operations.
    
    This class defines acceptable performance limits for various cache
    operations and system metrics. Thresholds are used to determine
    pass/fail status and performance grades.
    
    Attributes:
        basic_operations_avg_ms: Average time threshold for basic operations
        basic_operations_p95_ms: 95th percentile threshold for basic operations
        basic_operations_p99_ms: 99th percentile threshold for basic operations
        memory_cache_avg_ms: Average time threshold for memory cache operations
        memory_cache_p95_ms: 95th percentile threshold for memory cache
        memory_cache_p99_ms: 99th percentile threshold for memory cache
        compression_avg_ms: Average time threshold for compression operations
        compression_p95_ms: 95th percentile threshold for compression
        compression_p99_ms: 99th percentile threshold for compression
        memory_usage_warning_mb: Memory usage warning threshold in MB
        memory_usage_critical_mb: Memory usage critical threshold in MB
        regression_warning_percent: Performance regression warning threshold
        regression_critical_percent: Performance regression critical threshold
        success_rate_warning: Success rate warning threshold (0-100)
        success_rate_critical: Success rate critical threshold (0-100)
    
    Example:
        >>> thresholds = CachePerformanceThresholds()
        >>> thresholds.basic_operations_avg_ms = 25.0  # Stricter threshold
        >>> is_fast = avg_time <= thresholds.basic_operations_avg_ms
    """

    def validate(self) -> bool:
        """
        Validate threshold configuration for consistency.
        
        Returns:
            True if all thresholds are valid and consistent
        
        Raises:
            ConfigurationError: If thresholds are invalid or inconsistent
        """
        ...


@dataclass
class BenchmarkConfig:
    """
    Complete configuration for cache performance benchmarking.
    
    This class contains all configuration options for benchmark execution,
    including iteration counts, timeouts, feature flags, and thresholds.
    
    Attributes:
        default_iterations: Default number of iterations for benchmarks
        warmup_iterations: Number of warmup iterations before measurement
        timeout_seconds: Maximum benchmark execution time
        enable_memory_tracking: Whether to track memory usage
        enable_compression_tests: Whether to run compression benchmarks
        thresholds: Performance threshold configuration
        environment: Environment name (development, testing, production, ci)
        custom_settings: Additional custom configuration options
    
    Example:
        >>> config = BenchmarkConfig(
        ...     default_iterations=50,
        ...     timeout_seconds=120,
        ...     thresholds=CachePerformanceThresholds()
        ... )
        >>> config.validate()
    """

    def validate(self) -> bool:
        """
        Validate configuration for consistency and reasonable values.
        
        Returns:
            True if configuration is valid
        
        Raises:
            ConfigurationError: If configuration is invalid
        """
        ...


class ConfigPresets:
    """
    Environment-specific configuration presets.
    
    This class provides pre-configured settings optimized for different
    environments and use cases. Presets balance performance, accuracy,
    and execution time based on the intended environment.
    
    Available presets:
    - development: Fast feedback for local development
    - testing: Balanced settings for automated testing
    - production: High accuracy for production validation
    - ci: Optimized for CI/CD pipelines
    
    Example:
        >>> config = ConfigPresets.development_config()
        >>> config = ConfigPresets.production_config()
        >>> ci_config = ConfigPresets.ci_config()
    """

    @staticmethod
    def development_config() -> BenchmarkConfig:
        """
        Configuration optimized for local development.
        
        Features:
        - Lower iteration counts for faster feedback
        - Relaxed thresholds for development environments
        - Minimal warmup for quick execution
        - All features enabled for comprehensive testing
        
        Returns:
            BenchmarkConfig optimized for development use
        """
        ...

    @staticmethod
    def testing_config() -> BenchmarkConfig:
        """
        Configuration optimized for automated testing.
        
        Features:
        - Standard iteration counts for reliable results
        - Standard thresholds for test validation
        - Standard warmup for measurement accuracy
        - All features enabled for comprehensive coverage
        
        Returns:
            BenchmarkConfig optimized for testing environments
        """
        ...

    @staticmethod
    def production_config() -> BenchmarkConfig:
        """
        Configuration optimized for production validation.
        
        Features:
        - Higher iteration counts for maximum accuracy
        - Strict performance thresholds
        - Extended warmup for stable measurements
        - All features enabled for comprehensive validation
        
        Returns:
            BenchmarkConfig optimized for production use
        """
        ...

    @staticmethod
    def ci_config() -> BenchmarkConfig:
        """
        Configuration optimized for CI/CD pipelines.
        
        Features:
        - Balanced iteration counts for CI time constraints
        - CI-appropriate thresholds
        - Standard warmup for reliable results
        - All features enabled but optimized for CI environment
        
        Returns:
            BenchmarkConfig optimized for CI/CD use
        """
        ...


def load_config_from_env() -> BenchmarkConfig:
    """
    Load benchmark configuration from environment variables.
    
    Supported environment variables:
    - BENCHMARK_DEFAULT_ITERATIONS: Default iteration count
    - BENCHMARK_WARMUP_ITERATIONS: Warmup iteration count
    - BENCHMARK_TIMEOUT_SECONDS: Benchmark timeout
    - BENCHMARK_ENABLE_MEMORY_TRACKING: Enable memory tracking (true/false)
    - BENCHMARK_ENABLE_COMPRESSION_TESTS: Enable compression tests (true/false)
    - BENCHMARK_ENVIRONMENT: Environment name
    - BENCHMARK_THRESHOLD_*: Individual threshold overrides
    
    Returns:
        BenchmarkConfig loaded from environment variables
    
    Example:
        >>> os.environ['BENCHMARK_DEFAULT_ITERATIONS'] = '50'
        >>> config = load_config_from_env()
        >>> print(config.default_iterations)  # 50
    """
    ...


def load_config_from_file(file_path: str) -> BenchmarkConfig:
    """
    Load benchmark configuration from JSON or YAML file.
    
    Args:
        file_path: Path to configuration file (.json or .yaml/.yml)
    
    Returns:
        BenchmarkConfig loaded from file
    
    Raises:
        ConfigurationError: If file cannot be loaded or parsed
    
    Example:
        >>> config = load_config_from_file('config/benchmark.json')
        >>> config = load_config_from_file('config/benchmark.yaml')
    """
    ...


def get_default_config() -> BenchmarkConfig:
    """
    Get default benchmark configuration.
    
    Returns standard testing configuration with default values.
    
    Returns:
        BenchmarkConfig with default settings
    """
    ...
