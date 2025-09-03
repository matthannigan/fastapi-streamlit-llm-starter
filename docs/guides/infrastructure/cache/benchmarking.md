---
sidebar_label: Benchmarking
---

# Cache Performance Benchmarking Guide

This comprehensive guide covers the cache performance benchmarking system, providing detailed performance analysis, regression detection, and optimization strategies for cache infrastructure. The benchmarking system implements a modular architecture for comprehensive performance testing with multiple report formats and configurable thresholds.

## Table of Contents

1. [Benchmarking System Overview](#benchmarking-system-overview)
2. [Getting Started](#getting-started)
3. [Core Components](#core-components)
4. [Configuration Management](#configuration-management)
5. [Reporting and Analysis](#reporting-and-analysis)
6. [Performance Testing Patterns](#performance-testing-patterns)
7. [Regression Detection](#regression-detection)
8. [CI/CD Integration](#cicd-integration)
9. [Advanced Features](#advanced-features)
10. [Troubleshooting](#troubleshooting)

## Benchmarking System Overview

The cache benchmarking system provides production-ready performance testing capabilities with comprehensive analysis and reporting. It follows the infrastructure vs domain service architecture, providing focused testing tools for cache performance optimization.

### Architecture Components

The benchmarking system implements a modular architecture that breaks down performance testing into focused, maintainable components:

```
benchmarks/
├── __init__.py          # Public API exports and backward compatibility
├── models.py            # Data models and result containers
├── utils.py             # Statistical analysis and memory tracking utilities
├── generator.py         # Test data generation for realistic workloads
├── config.py            # Configuration management and validation
├── reporting.py         # Multi-format report generation
├── core.py              # Main benchmark orchestration
├── config_examples/     # Example configurations for different environments
│   ├── development.json
│   ├── production.json
│   ├── ci.json
│   └── README.md
└── README.md           # Component documentation
```

### Key Features

**Comprehensive Performance Analysis**:
- Statistical analysis with percentiles, standard deviation, and outlier detection
- Memory usage tracking and optimization recommendations
- Cache hit rate analysis and performance correlation
- Operation timing with warmup iterations and accurate measurements

**Multi-Format Reporting**:
- Human-readable text reports for development and analysis
- CI/CD optimized reports with performance badges
- JSON output for programmatic analysis and integration
- GitHub-flavored markdown for documentation and sharing

**Configurable Testing**:
- Environment-specific presets for different testing contexts
- Customizable thresholds for performance regression detection
- Flexible iteration counts and timeout configurations
- Support for different data types and workload patterns

**Production-Ready Integration**:
- CI/CD pipeline integration with automated regression detection
- Environment variable configuration for deployment flexibility
- Comprehensive error handling and graceful degradation
- Performance monitoring integration with metrics collection

## Getting Started

### 5-Minute Quick Start

**Basic Performance Testing**:

```python
from app.infrastructure.cache.benchmarks import CachePerformanceBenchmark
from app.infrastructure.cache.factory import CacheFactory

# Create cache instance using factory
factory = CacheFactory()
cache = await factory.for_testing(use_memory_cache=True)

# Run benchmark with default configuration
benchmark = CachePerformanceBenchmark(cache)
suite = await benchmark.run_comprehensive_benchmark_suite()

# Generate human-readable report
reporter = benchmark.get_reporter("text")
report = reporter.generate_report(suite)
print(report)
```

**Performance Analysis Output**:
```
🚀 Cache Performance Benchmark Results
======================================

Basic Operations:
  GET Operations: 1,247 ops/sec (avg: 0.80ms, p95: 1.2ms)
  SET Operations: 1,156 ops/sec (avg: 0.87ms, p95: 1.4ms)
  DELETE Operations: 1,389 ops/sec (avg: 0.72ms, p95: 1.1ms)

Memory Usage:
  Peak Memory: 42.3 MB
  Cache Hit Rate: 85.6%
  Compression Savings: 67%

Recommendations:
  ✅ Performance within expected thresholds
  💡 Consider increasing cache size for higher hit rates
```

### Configuration-Based Usage

```python
from app.infrastructure.cache.benchmarks.config import ConfigPresets
from app.infrastructure.cache.benchmarks import CachePerformanceBenchmark

# Use preset configurations
config = ConfigPresets.production_config()  # or development_config(), ci_config()
benchmark = CachePerformanceBenchmark(cache, config=config)

# Or load from file
from app.infrastructure.cache.benchmarks.config import load_config_from_file
config = load_config_from_file("config_examples/production.json")
benchmark = CachePerformanceBenchmark.from_config(cache, config)
```

### Multi-Format Reporting

```python
from app.infrastructure.cache.benchmarks.reporting import ReporterFactory

# Generate all report formats
reports = ReporterFactory.generate_all_reports(suite)

# Available formats: text, ci, json, markdown
print(reports["text"])      # Human-readable console output
print(reports["ci"])        # CI/CD pipeline with badges
print(reports["json"])      # Machine-readable JSON
print(reports["markdown"])  # GitHub-flavored markdown
```

## Core Components

### Data Models (`models.py`)

The package provides three main data models:

- **`BenchmarkResult`**: Individual benchmark measurement data with comprehensive metrics
- **`ComparisonResult`**: Before/after performance comparison with regression detection
- **`BenchmarkSuite`**: Collection of benchmark results with aggregated analysis

```python
from app.infrastructure.cache.benchmarks.models import BenchmarkResult, BenchmarkSuite

# Individual result with comprehensive metrics
result = BenchmarkResult(
    operation_type="get_operations",
    duration_ms=1250.0,
    memory_peak_mb=45.2,
    iterations=1000,
    avg_duration_ms=1.25,
    min_duration_ms=0.8,
    max_duration_ms=15.2,
    p95_duration_ms=3.4,
    p99_duration_ms=8.1,
    std_dev_ms=1.8,
    operations_per_second=800.0,
    success_rate=0.998,
    memory_usage_mb=42.1,
    cache_hit_rate=0.85
)

# Check performance against thresholds
assert result.meets_threshold(5.0)  # Average under 5ms
print(result.performance_grade())   # "Good", "Excellent", etc.
```

### Configuration System (`config.py`)

Comprehensive configuration management with validation and presets:

```python
from app.infrastructure.cache.benchmarks.config import (
    BenchmarkConfig, ConfigPresets, load_config_from_env
)

# Preset configurations for different environments
dev_config = ConfigPresets.development_config()    # Fast, relaxed thresholds
prod_config = ConfigPresets.production_config()    # Thorough, strict thresholds
ci_config = ConfigPresets.ci_config()              # Balanced for CI/CD

# Load from environment variables
config = load_config_from_env()

# Custom configuration
custom_config = BenchmarkConfig(
    default_iterations=200,
    warmup_iterations=20,
    timeout_seconds=300,
    enable_memory_tracking=True,
    enable_compression_tests=True,
    environment="custom"
)
```

### Statistical Analysis (`utils.py`)

Advanced statistical analysis and memory tracking:

```python
from app.infrastructure.cache.benchmarks.utils import StatisticalCalculator, MemoryTracker

# Statistical analysis
data = [10.2, 12.5, 11.8, 9.7, 13.1, 10.9, 12.2]
stats = StatisticalCalculator.calculate_statistics(data)
print(f"Mean: {stats['mean']:.2f}ms")
print(f"P95: {stats['p95']:.2f}ms")
print(f"Outliers: {stats['outliers']}")

# Memory tracking
tracker = MemoryTracker()
baseline = tracker.get_process_memory_mb()
# ... perform operations ...
current = tracker.get_process_memory_mb()
memory_delta = current - baseline
```

### Data Generation (`generator.py`)

Realistic test data generation for comprehensive benchmarks:

```python
from app.infrastructure.cache.benchmarks.generator import CacheBenchmarkDataGenerator

generator = CacheBenchmarkDataGenerator()

# Generate different types of test data
text_data = generator.generate_text_data(size_kb=2.0)
json_data = generator.generate_json_data(complexity="complex")
binary_data = generator.generate_binary_data(size_kb=5.0)

# Generate realistic workloads
workload = generator.generate_workload_data(
    num_items=100,
    data_types=["text", "json", "binary"],
    size_distribution={
        "small": (0.1, 0.5),    # 0.1-0.5 KB
        "medium": (0.5, 2.0),   # 0.5-2.0 KB  
        "large": (2.0, 10.0)    # 2.0-10.0 KB
    }
)
```

### Multi-Format Reporting (`reporting.py`)

Comprehensive reporting system with multiple output formats:

```python
from app.infrastructure.cache.benchmarks.reporting import (
    TextReporter, CIReporter, JSONReporter, MarkdownReporter, ReporterFactory
)

# Text reporting with verbosity control
text_reporter = TextReporter(
    verbosity="detailed",  # "summary", "standard", "detailed"
    include_sections=["header", "results", "analysis", "recommendations"]
)

# CI/CD optimized reporting
ci_reporter = CIReporter()
badges = ci_reporter.create_performance_badges(suite)

# Structured JSON for programmatic use
json_reporter = JSONReporter(include_metadata=True, schema_version="1.0")

# GitHub-flavored markdown
markdown_reporter = MarkdownReporter()

# Factory pattern for easy format selection
reporter = ReporterFactory.get_reporter("markdown")
```

## Configuration

### Environment Variables

Configure benchmarks through environment variables:

```bash
# Basic settings
export BENCHMARK_DEFAULT_ITERATIONS=100
export BENCHMARK_WARMUP_ITERATIONS=10
export BENCHMARK_TIMEOUT_SECONDS=300
export BENCHMARK_ENABLE_MEMORY_TRACKING=true
export BENCHMARK_ENABLE_COMPRESSION_TESTS=true
export BENCHMARK_ENVIRONMENT=production

# Performance thresholds
export BENCHMARK_THRESHOLD_BASIC_OPS_AVG_MS=50.0
export BENCHMARK_THRESHOLD_BASIC_OPS_P95_MS=100.0
export BENCHMARK_THRESHOLD_MEMORY_USAGE_WARNING_MB=50.0
export BENCHMARK_THRESHOLD_SUCCESS_RATE_WARNING=95.0
```

### Configuration Files

Load configuration from JSON files:

```python
from app.infrastructure.cache.benchmarks.config import load_config_from_file

# Load environment-specific configuration
config = load_config_from_file("config_examples/production.json")
benchmark = CachePerformanceBenchmark(cache, config=config)
```

Example configuration file structure:

```json
{
  "default_iterations": 500,
  "warmup_iterations": 20,
  "timeout_seconds": 600,
  "enable_memory_tracking": true,
  "enable_compression_tests": true,
  "environment": "production",
  "thresholds": {
    "basic_operations_avg_ms": 25.0,
    "basic_operations_p95_ms": 50.0,
    "memory_usage_warning_mb": 25.0,
    "success_rate_warning": 99.0
  }
}
```

### Configuration Presets

Use predefined presets for common environments:

| Preset | Iterations | Warmup | Timeout | Thresholds | Use Case |
|--------|------------|---------|---------|------------|----------|
| `development` | 50 | 5 | 180s | Relaxed | Local development, debugging |
| `testing` | 100 | 10 | 300s | Standard | Automated testing, validation |
| `ci` | 200 | 10 | 400s | Balanced | CI/CD pipelines |
| `production` | 500 | 20 | 600s | Strict | Production validation, releases |

## Advanced Features

### Performance Regression Detection

```python
from app.infrastructure.cache.benchmarks.core import PerformanceRegressionDetector

detector = PerformanceRegressionDetector()

# Compare two benchmark runs
comparison = detector.compare_results(baseline_result, current_result)
if comparison.is_regression:
    print(f"Performance regression: {comparison.performance_change_percent:.1f}%")
    print(f"Recommendations: {comparison.generate_recommendations()}")

# Analyze performance trends
trends = detector.analyze_performance_trends(historical_results)
print(f"Trend direction: {trends['trend_direction']}")
```

### Custom Reporters

Create custom reporters by extending the base class:

```python
from app.infrastructure.cache.benchmarks.reporting import BenchmarkReporter

class CustomReporter(BenchmarkReporter):
    def generate_report(self, suite: BenchmarkSuite) -> str:
        # Custom report generation logic
        return f"Custom report for {suite.name}"

# Register with factory
ReporterFactory.register_reporter("custom", CustomReporter)
```

### Memory Profiling

Detailed memory usage analysis:

```python
from app.infrastructure.cache.benchmarks.utils import MemoryTracker

tracker = MemoryTracker()

# Track memory during operations
baseline = tracker.get_memory_usage()
# ... cache operations ...
peak = tracker.get_memory_usage()

memory_delta = peak["process_mb"] - baseline["process_mb"]
print(f"Memory usage increased by {memory_delta:.2f} MB")
```

## Testing

The package includes comprehensive tests organized by component:

```bash
# Run all benchmark tests
make test-backend-infra-cache-benchmarks

# Run specific test categories
pytest tests/infrastructure/cache/benchmarks/test_models.py     # Data models
pytest tests/infrastructure/cache/benchmarks/test_utils.py      # Utilities
pytest tests/infrastructure/cache/benchmarks/test_config.py     # Configuration
pytest tests/infrastructure/cache/benchmarks/test_reporting.py  # Reporting
pytest tests/infrastructure/cache/benchmarks/test_core.py       # Core logic
pytest tests/infrastructure/cache/benchmarks/test_integration.py # End-to-end

# Run with coverage
pytest --cov=app.infrastructure.cache.benchmarks --cov-report=html
```

## Migration Guide

### From Legacy `benchmarks.py`

The refactored package maintains 100% backward compatibility:

```python
# Legacy import (still works)
from app.infrastructure.cache.benchmarks import CachePerformanceBenchmark

# New modular imports (recommended)
from app.infrastructure.cache.benchmarks.core import CachePerformanceBenchmark
from app.infrastructure.cache.benchmarks.config import ConfigPresets
from app.infrastructure.cache.benchmarks.reporting import ReporterFactory
```

### Key Changes

1. **Modular Structure**: Single file split into focused modules
2. **Enhanced Configuration**: File-based and preset configurations
3. **Multi-Format Reporting**: Text, CI, JSON, and Markdown outputs
4. **Improved Statistics**: Comprehensive statistical analysis utilities
5. **Better Testing**: Modular test suite with >95% coverage

### Breaking Changes

None. All existing APIs are preserved through the `__init__.py` module exports.

## Performance Considerations

### Benchmark Execution

- **Development**: ~30 seconds (50 iterations, relaxed thresholds)
- **CI**: ~2 minutes (200 iterations, balanced thresholds)  
- **Production**: ~5 minutes (500 iterations, strict thresholds)

### Memory Usage

- **Base overhead**: ~10-15 MB
- **Per benchmark**: ~2-5 MB depending on data size
- **Peak usage**: Automatically tracked and reported

### Optimization Tips

1. **Use appropriate presets** for your environment
2. **Adjust iterations** based on accuracy requirements
3. **Enable compression tests** only when needed
4. **Use memory tracking** selectively for detailed analysis

## Troubleshooting

### Common Issues

1. **Import Errors**: Ensure all required dependencies are installed
2. **Configuration Validation**: Check threshold ordering and value ranges
3. **Memory Tracking**: Requires `psutil` for detailed tracking
4. **Redis Tests**: Ensure Redis is available for Redis cache benchmarks

### Debug Mode

Enable debug logging for detailed execution information:

```python
import logging
logging.basicConfig(level=logging.DEBUG)

# Detailed execution logs will be displayed
benchmark = CachePerformanceBenchmark(cache, config=config)
```

### Performance Tuning

Adjust configuration for specific needs:

```python
# Fast development testing
config = BenchmarkConfig(
    default_iterations=10,
    warmup_iterations=2,
    timeout_seconds=60,
    enable_memory_tracking=False
)

# Detailed production validation
config = BenchmarkConfig(
    default_iterations=1000,
    warmup_iterations=50,
    timeout_seconds=1800,
    enable_memory_tracking=True,
    enable_compression_tests=True
)
```

## API Reference

### Core Classes

- `CachePerformanceBenchmark`: Main benchmark orchestrator
- `PerformanceRegressionDetector`: Regression analysis and comparison
- `BenchmarkResult`: Individual benchmark result container
- `BenchmarkSuite`: Collection of results with aggregated analysis
- `ComparisonResult`: Performance comparison between two results

### Configuration Classes

- `BenchmarkConfig`: Main configuration container
- `CachePerformanceThresholds`: Performance threshold definitions
- `ConfigPresets`: Predefined environment configurations

### Utility Classes

- `StatisticalCalculator`: Statistical analysis utilities
- `MemoryTracker`: Memory usage tracking and analysis
- `CacheBenchmarkDataGenerator`: Test data generation

### Reporter Classes

- `BenchmarkReporter`: Base reporter class
- `TextReporter`: Human-readable text reports
- `CIReporter`: CI/CD optimized reports with badges
- `JSONReporter`: Structured JSON output
- `MarkdownReporter`: GitHub-flavored markdown
- `ReporterFactory`: Reporter creation and management

## Related Documentation

### Cache Infrastructure
- **[Cache Infrastructure Overview](./CACHE.md)** - Complete cache system architecture, components, and integration patterns
- **[Cache Usage Guide](./usage-guide.md)** - Practical implementation patterns and optimization strategies  
- **[Cache API Reference](./api-reference.md)** - Comprehensive API documentation with examples and best practices
- **[Cache Testing Guide](./testing.md)** - Testing strategies, fixtures, and validation approaches
- **[Cache Configuration Guide](./configuration.md)** - Environment-specific configuration and preset management

### Performance and Monitoring
- **[Monitoring Infrastructure](../MONITORING.md)** - Performance monitoring, metrics collection, and observability
- **[Performance Optimization Guide](../../operations/PERFORMANCE_OPTIMIZATION.md)** - System-wide performance optimization strategies
- **[Resilience Patterns](../RESILIENCE.md)** - Error handling, circuit breakers, and reliability patterns

### Development Guidelines
- **[Code Standards](../../developer/CODE_STANDARDS.md)** - Development patterns and quality standards
- **[Testing Strategy](../../testing/TESTING.md)** - Comprehensive testing approaches across the application
- **[CI/CD Integration](../../operations/CICD.md)** - Automated testing and deployment patterns

### Infrastructure Integration
- **[AI Infrastructure](../AI.md)** - AI service integration patterns that leverage cache infrastructure
- **[Security Guidelines](../SECURITY.md)** - Security considerations for performance testing and cache infrastructure
- **[Docker Development](../../developer/DOCKER.md)** - Containerized development and testing environments

### Cross-References
This benchmarking guide complements the cache infrastructure documentation by providing:
- **Performance validation** for the patterns described in the [Cache Infrastructure Overview](./CACHE.md)
- **Testing strategies** for the optimization techniques documented in the [Usage Guide](./usage-guide.md)  
- **Regression detection** for the APIs detailed in the [API Reference](./api-reference.md)
- **Quality assurance** for the testing approaches covered in the [Testing Guide](./testing.md)

---

**Next Steps**: Ready to implement performance benchmarking? Start with the basic performance testing patterns, then integrate regression detection into your CI/CD pipeline for continuous performance monitoring.