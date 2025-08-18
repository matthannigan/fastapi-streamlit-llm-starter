"""
Cache Performance Benchmarking Package

This package provides a comprehensive, modular performance benchmarking infrastructure
for cache implementations. It has been refactored from a monolithic design to improve
maintainability, testability, and extensibility.

Package Structure:
    models.py: Data models for benchmark results and analysis
    utils.py: Statistical calculations and utility functions
    generator.py: Test data generation for realistic workloads
    config.py: Configuration management and environment-specific presets
    reporting.py: Report generation in multiple formats
    core.py: Main benchmarking orchestration and execution

The package maintains backward compatibility with the original benchmarks.py interface
while providing enhanced modularity and configuration flexibility.

Usage:
    >>> from app.infrastructure.cache.benchmarks import CachePerformanceBenchmark
    >>> 
    >>> benchmark = CachePerformanceBenchmark()
    >>> cache = SomeCache()
    >>> result = await benchmark.benchmark_basic_operations(cache)
    >>> print(f"Performance: {result.avg_duration_ms:.2f}ms")

Key Features:
    - Comprehensive cache operation benchmarking
    - Memory usage tracking and analysis
    - Compression efficiency testing
    - Before/after comparison utilities
    - Configurable performance thresholds
    - Multiple report formats (text, JSON, markdown, CI)
    - Environment-specific configuration presets
"""

# Import all public components for backward compatibility
from .models import (
    BenchmarkResult,
    ComparisonResult,
    BenchmarkSuite,
)

from .utils import (
    StatisticalCalculator,
    MemoryTracker,
)

from .generator import (
    CacheBenchmarkDataGenerator,
)

from .config import (
    CachePerformanceThresholds,
    BenchmarkConfig,
    ConfigPresets,
    load_config_from_env,
    load_config_from_file,
    get_default_config,
)

from .reporting import (
    BenchmarkReporter,
    TextReporter,
    CIReporter,
    JSONReporter,
    MarkdownReporter,
    ReporterFactory,
)

from .core import (
    CachePerformanceBenchmark,
    PerformanceRegressionDetector,
)

# Public API exports for backward compatibility
__all__ = [
    # Data Models
    "BenchmarkResult",
    "ComparisonResult", 
    "BenchmarkSuite",
    
    # Utilities
    "StatisticalCalculator",
    "MemoryTracker",
    
    # Data Generation
    "CacheBenchmarkDataGenerator",
    
    # Configuration
    "CachePerformanceThresholds",
    "BenchmarkConfig",
    "ConfigPresets",
    "load_config_from_env",
    "load_config_from_file",
    "get_default_config",
    
    # Reporting
    "BenchmarkReporter",
    "TextReporter",
    "CIReporter",
    "JSONReporter",
    "MarkdownReporter",
    "ReporterFactory",
    
    # Core Functionality
    "CachePerformanceBenchmark",
    "PerformanceRegressionDetector",
]