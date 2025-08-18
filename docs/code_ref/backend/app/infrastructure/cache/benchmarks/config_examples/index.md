# Benchmark Configuration Examples

This directory contains example configuration files for different environments and use cases.

## Configuration Files

### development.json
- **Purpose**: Local development and debugging
- **Characteristics**: 
  - Fast execution (50 iterations)
  - Relaxed thresholds
  - Minimal warmup
- **Use Cases**: 
  - Local development
  - Quick validation
  - Debugging performance issues

### production.json
- **Purpose**: Production validation and release testing
- **Characteristics**: 
  - High accuracy (500 iterations)
  - Strict performance thresholds
  - Extended warmup
- **Use Cases**: 
  - Production deployment validation
  - Release testing
  - Performance certification

### ci.json
- **Purpose**: CI/CD pipelines and automated testing
- **Characteristics**: 
  - Balanced execution time (200 iterations)
  - CI-appropriate thresholds
  - Standard warmup
- **Use Cases**: 
  - Continuous integration
  - Pull request validation
  - Automated testing

## Configuration Options

### Basic Settings
- `default_iterations`: Number of benchmark iterations
- `warmup_iterations`: Number of warmup iterations
- `timeout_seconds`: Maximum benchmark execution time
- `enable_memory_tracking`: Enable memory usage tracking
- `enable_compression_tests`: Enable compression benchmarks
- `environment`: Environment identifier

### Performance Thresholds
All threshold values are in milliseconds unless otherwise specified:

- `basic_operations_avg_ms`: Average time threshold for basic operations
- `basic_operations_p95_ms`: 95th percentile threshold for basic operations
- `basic_operations_p99_ms`: 99th percentile threshold for basic operations
- `memory_cache_avg_ms`: Average time threshold for memory cache operations
- `memory_cache_p95_ms`: 95th percentile threshold for memory cache
- `memory_cache_p99_ms`: 99th percentile threshold for memory cache
- `compression_avg_ms`: Average time threshold for compression operations
- `compression_p95_ms`: 95th percentile threshold for compression
- `compression_p99_ms`: 99th percentile threshold for compression
- `memory_usage_warning_mb`: Memory usage warning threshold (MB)
- `memory_usage_critical_mb`: Memory usage critical threshold (MB)
- `regression_warning_percent`: Performance regression warning threshold (%)
- `regression_critical_percent`: Performance regression critical threshold (%)
- `success_rate_warning`: Success rate warning threshold (0-100%)
- `success_rate_critical`: Success rate critical threshold (0-100%)

## Usage Examples

### Loading Configuration Files

```python
from app.infrastructure.cache.benchmarks.config import load_config_from_file

# Load development configuration
config = load_config_from_file('config_examples/development.json')

# Load production configuration
config = load_config_from_file('config_examples/production.json')

# Load CI configuration
config = load_config_from_file('config_examples/ci.json')
```

### Using Configuration Presets

```python
from app.infrastructure.cache.benchmarks.config import ConfigPresets

# Use built-in presets (same as loading from files)
dev_config = ConfigPresets.development_config()
prod_config = ConfigPresets.production_config()
ci_config = ConfigPresets.ci_config()
```

### Environment Variables

You can override any configuration value using environment variables:

```bash
# Basic settings
export BENCHMARK_DEFAULT_ITERATIONS=100
export BENCHMARK_WARMUP_ITERATIONS=10
export BENCHMARK_TIMEOUT_SECONDS=300
export BENCHMARK_ENABLE_MEMORY_TRACKING=true
export BENCHMARK_ENABLE_COMPRESSION_TESTS=true
export BENCHMARK_ENVIRONMENT=testing

# Threshold overrides
export BENCHMARK_THRESHOLD_BASIC_OPS_AVG_MS=50.0
export BENCHMARK_THRESHOLD_BASIC_OPS_P95_MS=100.0
export BENCHMARK_THRESHOLD_MEMORY_CACHE_AVG_MS=5.0
export BENCHMARK_THRESHOLD_REGRESSION_WARNING_PCT=10.0
```

## Custom Configuration

You can create custom configuration files by copying and modifying the examples:

1. Copy an existing example file
2. Modify the values to suit your needs
3. Add custom settings in the `custom_settings` section
4. Load using `load_config_from_file()`

### Custom Settings
The `custom_settings` section allows you to add metadata and custom configuration:

```json
{
  "custom_settings": {
    "description": "My custom configuration",
    "optimized_for": "specific_use_case",
    "suitable_for": ["use_case_1", "use_case_2"],
    "notes": "Additional information about this configuration",
    "custom_key": "custom_value"
  }
}
```

## Validation

All configuration files are automatically validated when loaded. Invalid configurations will raise a `ConfigurationError` with details about the issue.

Common validation rules:
- Iteration counts must be positive
- Timeout must be positive
- Percentile thresholds must increase (avg ≤ p95 ≤ p99)
- Memory thresholds must be ordered (warning < critical)
- Success rates must be between 0 and 100