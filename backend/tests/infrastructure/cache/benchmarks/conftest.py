"""
Shared fixtures for benchmark tests.

This module provides common test fixtures and utilities for testing
the modular benchmark components.
"""

import pytest
from datetime import datetime
from typing import Dict, Any, List

from app.infrastructure.cache.benchmarks.models import (
    BenchmarkResult, ComparisonResult, BenchmarkSuite
)
from app.infrastructure.cache.benchmarks.config import (
    BenchmarkConfig, CachePerformanceThresholds, ConfigPresets
)
from app.infrastructure.cache.benchmarks.generator import CacheBenchmarkDataGenerator
from app.infrastructure.cache.memory import InMemoryCache


@pytest.fixture
def sample_benchmark_result() -> BenchmarkResult:
    """Create a sample benchmark result for testing."""
    return BenchmarkResult(
        operation_type="test_operation",
        duration_ms=2550.0,  # Total duration
        memory_peak_mb=15.2,  # Peak memory
        iterations=100,
        avg_duration_ms=25.5,
        min_duration_ms=20.1,
        max_duration_ms=35.8,
        p95_duration_ms=32.0,
        p99_duration_ms=34.5,
        std_dev_ms=3.2,
        operations_per_second=39.2,
        success_rate=1.0,
        memory_usage_mb=12.5,
        error_count=0,
        cache_hit_rate=0.85,
        compression_ratio=0.65,
        compression_savings_mb=5.2,
        metadata={"test_key": "test_value"}
    )


@pytest.fixture
def sample_comparison_result() -> ComparisonResult:
    """Create a sample comparison result for testing."""
    baseline = BenchmarkResult(
        operation_type="baseline",
        duration_ms=3000.0,
        memory_peak_mb=18.0,
        iterations=100,
        avg_duration_ms=30.0,
        min_duration_ms=25.0,
        max_duration_ms=40.0,
        p95_duration_ms=38.0,
        p99_duration_ms=39.0,
        std_dev_ms=4.0,
        operations_per_second=33.3,
        success_rate=1.0,
        memory_usage_mb=15.0,
        error_count=0
    )
    
    current = BenchmarkResult(
        operation_type="current",
        duration_ms=2500.0,
        memory_peak_mb=14.0,
        iterations=100,
        avg_duration_ms=25.0,
        min_duration_ms=20.0,
        max_duration_ms=35.0,
        p95_duration_ms=32.0,
        p99_duration_ms=34.0,
        std_dev_ms=3.0,
        operations_per_second=40.0,
        success_rate=1.0,
        memory_usage_mb=12.0,
        error_count=0
    )
    
    return ComparisonResult(
        operation_type="test_comparison",
        baseline_result=baseline,
        current_result=current,
        performance_change_percent=-16.67,  # 16.67% improvement
        is_regression=False,
        comparison_timestamp=datetime.now()
    )


@pytest.fixture
def sample_benchmark_suite(sample_benchmark_result) -> BenchmarkSuite:
    """Create a sample benchmark suite for testing."""
    return BenchmarkSuite(
        name="Test Suite",
        results=[sample_benchmark_result],
        timestamp=datetime.now(),
        total_duration_ms=1000.0,
        environment_info={"python_version": "3.9", "platform": "test"},
        failed_benchmarks=[],
        config_used={"iterations": 100}
    )


@pytest.fixture
def default_config() -> BenchmarkConfig:
    """Create a default benchmark configuration."""
    return BenchmarkConfig()


@pytest.fixture
def development_config() -> BenchmarkConfig:
    """Create a development benchmark configuration."""
    return ConfigPresets.development_config()


@pytest.fixture
def production_config() -> BenchmarkConfig:
    """Create a production benchmark configuration."""
    return ConfigPresets.production_config()


@pytest.fixture
def ci_config() -> BenchmarkConfig:
    """Create a CI benchmark configuration."""
    return ConfigPresets.ci_config()


@pytest.fixture
def default_thresholds() -> CachePerformanceThresholds:
    """Create default performance thresholds."""
    return CachePerformanceThresholds()


@pytest.fixture
def strict_thresholds() -> CachePerformanceThresholds:
    """Create strict performance thresholds for testing."""
    return CachePerformanceThresholds(
        basic_operations_avg_ms=10.0,
        basic_operations_p95_ms=20.0,
        basic_operations_p99_ms=30.0,
        memory_cache_avg_ms=1.0,
        memory_cache_p95_ms=2.0,
        memory_cache_p99_ms=5.0,
        memory_usage_warning_mb=10.0,
        memory_usage_critical_mb=20.0,
        success_rate_warning=99.0,
        success_rate_critical=95.0
    )


@pytest.fixture
def data_generator() -> CacheBenchmarkDataGenerator:
    """Create a benchmark data generator."""
    return CacheBenchmarkDataGenerator()


@pytest.fixture
def test_cache() -> InMemoryCache:
    """Create an in-memory cache for testing."""
    return InMemoryCache(max_size=100, ttl_seconds=3600)


@pytest.fixture
def performance_test_data() -> List[Dict[str, Any]]:
    """Generate test data for performance benchmarks."""
    return [
        {"key": f"test_key_{i}", "value": f"test_value_{i}" * 10, "size_kb": 0.1}
        for i in range(50)
    ]


@pytest.fixture
def sample_environment_vars(monkeypatch):
    """Set up sample environment variables for testing."""
    test_env_vars = {
        "BENCHMARK_DEFAULT_ITERATIONS": "50",
        "BENCHMARK_WARMUP_ITERATIONS": "5",
        "BENCHMARK_TIMEOUT_SECONDS": "120",
        "BENCHMARK_ENABLE_MEMORY_TRACKING": "true",
        "BENCHMARK_THRESHOLD_BASIC_OPS_AVG_MS": "30.0",
        "BENCHMARK_THRESHOLD_MEMORY_USAGE_WARNING_MB": "20.0"
    }
    
    for key, value in test_env_vars.items():
        monkeypatch.setenv(key, value)
    
    return test_env_vars


@pytest.fixture
def temp_config_file(tmp_path):
    """Create a temporary configuration file for testing."""
    config_content = """
{
    "default_iterations": 75,
    "warmup_iterations": 8,
    "timeout_seconds": 180,
    "enable_memory_tracking": true,
    "enable_compression_tests": false,
    "environment": "test",
    "thresholds": {
        "basic_operations_avg_ms": 40.0,
        "basic_operations_p95_ms": 80.0,
        "basic_operations_p99_ms": 160.0,
        "memory_usage_warning_mb": 30.0,
        "memory_usage_critical_mb": 60.0,
        "success_rate_warning": 98.0,
        "success_rate_critical": 90.0
    },
    "custom_settings": {
        "description": "Test configuration",
        "test_mode": true
    }
}
"""
    config_file = tmp_path / "test_config.json"
    config_file.write_text(config_content)
    return str(config_file)


@pytest.fixture
def invalid_config_file(tmp_path):
    """Create an invalid configuration file for testing."""
    invalid_content = """
{
    "default_iterations": -10,
    "warmup_iterations": "invalid",
    "thresholds": {
        "basic_operations_avg_ms": "not_a_number"
    }
}
"""
    config_file = tmp_path / "invalid_config.json"
    config_file.write_text(invalid_content)
    return str(config_file)