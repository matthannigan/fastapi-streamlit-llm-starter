"""
Cache Benchmark Configuration Management

This module provides configuration management for cache performance benchmarking,
including performance thresholds, environment-specific presets, and configuration
loading from various sources.

Classes:
    CachePerformanceThresholds: Performance threshold definitions
    BenchmarkConfig: Complete benchmark configuration
    ConfigPresets: Environment-specific configuration presets

Functions:
    load_config_from_env: Load configuration from environment variables
    load_config_from_file: Load configuration from JSON/YAML files
    get_default_config: Get default configuration settings

The configuration system supports environment variables, JSON/YAML files,
and programmatic configuration for maximum flexibility.
"""

import json
import os
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

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
    
    # Basic operation thresholds (milliseconds)
    basic_operations_avg_ms: float = 50.0
    basic_operations_p95_ms: float = 100.0
    basic_operations_p99_ms: float = 200.0
    
    # Memory cache thresholds (milliseconds)
    memory_cache_avg_ms: float = 5.0
    memory_cache_p95_ms: float = 10.0
    memory_cache_p99_ms: float = 20.0
    
    # Compression thresholds (milliseconds)
    compression_avg_ms: float = 100.0
    compression_p95_ms: float = 200.0
    compression_p99_ms: float = 500.0
    
    # Memory usage thresholds (megabytes)
    memory_usage_warning_mb: float = 50.0
    memory_usage_critical_mb: float = 100.0
    
    # Performance regression thresholds (percentage)
    regression_warning_percent: float = 10.0
    regression_critical_percent: float = 25.0
    
    # Success rate thresholds (percentage)
    success_rate_warning: float = 95.0
    success_rate_critical: float = 90.0
    
    def validate(self) -> bool:
        """
        Validate threshold configuration for consistency.
        
        Returns:
            True if all thresholds are valid and consistent
            
        Raises:
            ConfigurationError: If thresholds are invalid or inconsistent
        """
        errors = []
        
        # Check that percentile thresholds increase
        if not (self.basic_operations_avg_ms <= self.basic_operations_p95_ms <= self.basic_operations_p99_ms):
            errors.append("Basic operations thresholds must increase: avg <= p95 <= p99")
        
        if not (self.memory_cache_avg_ms <= self.memory_cache_p95_ms <= self.memory_cache_p99_ms):
            errors.append("Memory cache thresholds must increase: avg <= p95 <= p99")
        
        if not (self.compression_avg_ms <= self.compression_p95_ms <= self.compression_p99_ms):
            errors.append("Compression thresholds must increase: avg <= p95 <= p99")
        
        # Check memory thresholds
        if self.memory_usage_warning_mb >= self.memory_usage_critical_mb:
            errors.append("Memory warning threshold must be less than critical threshold")
        
        # Check regression thresholds
        if self.regression_warning_percent >= self.regression_critical_percent:
            errors.append("Regression warning threshold must be less than critical threshold")
        
        # Check success rate thresholds
        if not (0 <= self.success_rate_critical <= self.success_rate_warning <= 100):
            errors.append("Success rate thresholds must be: 0 <= critical <= warning <= 100")
        
        if errors:
            raise ConfigurationError(f"Invalid threshold configuration: {'; '.join(errors)}")
        
        return True


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
    
    default_iterations: int = 100
    warmup_iterations: int = 10
    timeout_seconds: int = 300
    enable_memory_tracking: bool = True
    enable_compression_tests: bool = True
    thresholds: CachePerformanceThresholds = field(default_factory=CachePerformanceThresholds)
    environment: str = "testing"
    custom_settings: Dict[str, Any] = field(default_factory=dict)
    
    def validate(self) -> bool:
        """
        Validate configuration for consistency and reasonable values.
        
        Returns:
            True if configuration is valid
            
        Raises:
            ConfigurationError: If configuration is invalid
        """
        errors = []
        
        # Check iteration counts
        if self.default_iterations <= 0:
            errors.append("default_iterations must be positive")
        
        if self.warmup_iterations < 0:
            errors.append("warmup_iterations must be non-negative")
        
        if self.timeout_seconds <= 0:
            errors.append("timeout_seconds must be positive")
        
        # Check environment
        valid_environments = ["development", "testing", "production", "ci"]
        if self.environment not in valid_environments:
            errors.append(f"environment must be one of: {valid_environments}")
        
        if errors:
            raise ConfigurationError(f"Invalid benchmark configuration: {'; '.join(errors)}")
        
        # Validate thresholds
        self.thresholds.validate()
        
        return True


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
        thresholds = CachePerformanceThresholds(
            basic_operations_avg_ms=100.0,  # Relaxed for development
            basic_operations_p95_ms=200.0,
            basic_operations_p99_ms=400.0,
            memory_cache_avg_ms=10.0,
            memory_cache_p95_ms=20.0,
            memory_cache_p99_ms=40.0,
            compression_avg_ms=200.0,
            compression_p95_ms=400.0,
            compression_p99_ms=800.0,
            memory_usage_warning_mb=100.0,
            memory_usage_critical_mb=200.0,
            regression_warning_percent=15.0,
            regression_critical_percent=30.0
        )
        
        return BenchmarkConfig(
            default_iterations=50,
            warmup_iterations=5,
            timeout_seconds=120,
            enable_memory_tracking=True,
            enable_compression_tests=True,
            thresholds=thresholds,
            environment="development"
        )
    
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
        thresholds = CachePerformanceThresholds()  # Use default thresholds
        
        return BenchmarkConfig(
            default_iterations=100,
            warmup_iterations=10,
            timeout_seconds=300,
            enable_memory_tracking=True,
            enable_compression_tests=True,
            thresholds=thresholds,
            environment="testing"
        )
    
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
        thresholds = CachePerformanceThresholds(
            basic_operations_avg_ms=25.0,  # Stricter for production
            basic_operations_p95_ms=50.0,
            basic_operations_p99_ms=100.0,
            memory_cache_avg_ms=2.0,
            memory_cache_p95_ms=5.0,
            memory_cache_p99_ms=10.0,
            compression_avg_ms=50.0,
            compression_p95_ms=100.0,
            compression_p99_ms=200.0,
            memory_usage_warning_mb=25.0,
            memory_usage_critical_mb=50.0,
            regression_warning_percent=5.0,
            regression_critical_percent=10.0
        )
        
        return BenchmarkConfig(
            default_iterations=500,
            warmup_iterations=20,
            timeout_seconds=600,
            enable_memory_tracking=True,
            enable_compression_tests=True,
            thresholds=thresholds,
            environment="production"
        )
    
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
        thresholds = CachePerformanceThresholds(
            basic_operations_avg_ms=75.0,  # Relaxed for CI environment
            basic_operations_p95_ms=150.0,
            basic_operations_p99_ms=300.0,
            memory_cache_avg_ms=7.0,
            memory_cache_p95_ms=15.0,
            memory_cache_p99_ms=30.0,
            compression_avg_ms=150.0,
            compression_p95_ms=300.0,
            compression_p99_ms=600.0,
            memory_usage_warning_mb=75.0,
            memory_usage_critical_mb=150.0,
            regression_warning_percent=12.0,
            regression_critical_percent=20.0
        )
        
        return BenchmarkConfig(
            default_iterations=200,
            warmup_iterations=10,
            timeout_seconds=400,
            enable_memory_tracking=True,
            enable_compression_tests=True,
            thresholds=thresholds,
            environment="ci"
        )


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
    # Start with default config
    config = BenchmarkConfig()
    
    # Load basic settings
    if iterations := os.getenv('BENCHMARK_DEFAULT_ITERATIONS'):
        try:
            config.default_iterations = int(iterations)
        except ValueError:
            raise ConfigurationError(f"Invalid BENCHMARK_DEFAULT_ITERATIONS: {iterations}")
    
    if warmup := os.getenv('BENCHMARK_WARMUP_ITERATIONS'):
        try:
            config.warmup_iterations = int(warmup)
        except ValueError:
            raise ConfigurationError(f"Invalid BENCHMARK_WARMUP_ITERATIONS: {warmup}")
    
    if timeout := os.getenv('BENCHMARK_TIMEOUT_SECONDS'):
        try:
            config.timeout_seconds = int(timeout)
        except ValueError:
            raise ConfigurationError(f"Invalid BENCHMARK_TIMEOUT_SECONDS: {timeout}")
    
    if memory_tracking := os.getenv('BENCHMARK_ENABLE_MEMORY_TRACKING'):
        config.enable_memory_tracking = memory_tracking.lower() in ('true', '1', 'yes', 'on')
    
    if compression_tests := os.getenv('BENCHMARK_ENABLE_COMPRESSION_TESTS'):
        config.enable_compression_tests = compression_tests.lower() in ('true', '1', 'yes', 'on')
    
    if environment := os.getenv('BENCHMARK_ENVIRONMENT'):
        config.environment = environment
    
    # Load threshold overrides
    threshold_mapping = {
        'BENCHMARK_THRESHOLD_BASIC_OPS_AVG_MS': 'basic_operations_avg_ms',
        'BENCHMARK_THRESHOLD_BASIC_OPS_P95_MS': 'basic_operations_p95_ms',
        'BENCHMARK_THRESHOLD_BASIC_OPS_P99_MS': 'basic_operations_p99_ms',
        'BENCHMARK_THRESHOLD_MEMORY_CACHE_AVG_MS': 'memory_cache_avg_ms',
        'BENCHMARK_THRESHOLD_MEMORY_CACHE_P95_MS': 'memory_cache_p95_ms',
        'BENCHMARK_THRESHOLD_MEMORY_CACHE_P99_MS': 'memory_cache_p99_ms',
        'BENCHMARK_THRESHOLD_COMPRESSION_AVG_MS': 'compression_avg_ms',
        'BENCHMARK_THRESHOLD_COMPRESSION_P95_MS': 'compression_p95_ms',
        'BENCHMARK_THRESHOLD_COMPRESSION_P99_MS': 'compression_p99_ms',
        'BENCHMARK_THRESHOLD_MEMORY_WARNING_MB': 'memory_usage_warning_mb',
        'BENCHMARK_THRESHOLD_MEMORY_CRITICAL_MB': 'memory_usage_critical_mb',
        'BENCHMARK_THRESHOLD_REGRESSION_WARNING_PCT': 'regression_warning_percent',
        'BENCHMARK_THRESHOLD_REGRESSION_CRITICAL_PCT': 'regression_critical_percent',
        'BENCHMARK_THRESHOLD_SUCCESS_WARNING': 'success_rate_warning',
        'BENCHMARK_THRESHOLD_SUCCESS_CRITICAL': 'success_rate_critical'
    }
    
    for env_var, attr_name in threshold_mapping.items():
        if value := os.getenv(env_var):
            try:
                setattr(config.thresholds, attr_name, float(value))
            except ValueError:
                raise ConfigurationError(f"Invalid {env_var}: {value}")
    
    # Validate final configuration
    config.validate()
    
    return config


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
    if not os.path.exists(file_path):
        raise ConfigurationError(f"Configuration file not found: {file_path}")
    
    try:
        with open(file_path, 'r') as f:
            if file_path.endswith('.json'):
                data = json.load(f)
            elif file_path.endswith(('.yaml', '.yml')):
                try:
                    import yaml
                    data = yaml.safe_load(f)
                except ImportError:
                    raise ConfigurationError("PyYAML not installed, cannot load YAML configuration")
            else:
                raise ConfigurationError(f"Unsupported file format: {file_path}")
    except Exception as e:
        raise ConfigurationError(f"Failed to load configuration file {file_path}: {e}")
    
    # Build configuration from data
    config = BenchmarkConfig()
    
    # Basic settings
    if 'default_iterations' in data:
        config.default_iterations = int(data['default_iterations'])
    if 'warmup_iterations' in data:
        config.warmup_iterations = int(data['warmup_iterations'])
    if 'timeout_seconds' in data:
        config.timeout_seconds = int(data['timeout_seconds'])
    if 'enable_memory_tracking' in data:
        config.enable_memory_tracking = bool(data['enable_memory_tracking'])
    if 'enable_compression_tests' in data:
        config.enable_compression_tests = bool(data['enable_compression_tests'])
    if 'environment' in data:
        config.environment = str(data['environment'])
    
    # Thresholds
    if 'thresholds' in data:
        threshold_data = data['thresholds']
        for key, value in threshold_data.items():
            if hasattr(config.thresholds, key):
                setattr(config.thresholds, key, float(value))
    
    # Custom settings
    if 'custom_settings' in data:
        config.custom_settings = dict(data['custom_settings'])
    
    # Validate configuration
    config.validate()
    
    return config


def get_default_config() -> BenchmarkConfig:
    """
    Get default benchmark configuration.
    
    Returns standard testing configuration with default values.
    
    Returns:
        BenchmarkConfig with default settings
    """
    return BenchmarkConfig()