---
sidebar_label: config
---

# [REFACTORED] Comprehensive cache benchmark configuration management with environment-specific presets.

  file_path: `backend/app/infrastructure/cache/benchmarks/config.py`

This module provides complete configuration infrastructure for cache performance benchmarking
including performance thresholds, environment-specific presets, and flexible configuration
loading from multiple sources. Designed for maximum flexibility across development, testing,
production, and CI environments with comprehensive validation and error handling.

## Classes

CachePerformanceThresholds: Performance threshold definitions with validation
BenchmarkConfig: Complete benchmark configuration with validation
ConfigPresets: Environment-specific configuration presets (development, testing, production, ci)

## Functions

load_config_from_env: Load configuration from environment variables with validation
load_config_from_file: Load configuration from JSON/YAML files with error handling
get_default_config: Get validated default configuration settings

## Key Features

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

## Configuration Hierarchy

1. **Environment Variables**: Highest priority for deployment flexibility
2. **Configuration Files**: JSON/YAML files for complex configurations
3. **Preset Selection**: Environment-specific presets for common scenarios
4. **Defaults**: Sensible defaults for immediate use

## Environment Presets

- **development**: Fast feedback with relaxed thresholds (50 iterations, 100ms avg threshold)
- **testing**: Balanced settings for automated testing (100 iterations, 50ms avg threshold)
- **production**: High accuracy with strict thresholds (500 iterations, 25ms avg threshold)
- **ci**: Optimized for CI/CD pipelines (200 iterations, 75ms avg threshold)

## Usage Examples

### Environment-Specific Presets

```python
from app.infrastructure.cache.benchmarks.config import ConfigPresets

# Development configuration
dev_config = ConfigPresets.development_config()
print(f"Iterations: {dev_config.default_iterations}")  # 50

# Production configuration
prod_config = ConfigPresets.production_config()
print(f"Threshold: {prod_config.thresholds.basic_operations_avg_ms}")  # 25.0
```

### Environment Variable Configuration

```python
import os
os.environ['BENCHMARK_DEFAULT_ITERATIONS'] = '200'
os.environ['BENCHMARK_THRESHOLD_BASIC_OPS_AVG_MS'] = '30.0'
config = load_config_from_env()
print(f"Loaded iterations: {config.default_iterations}")  # 200
```

### File-Based Configuration

```python
# config.json contains: {"default_iterations": 150, "thresholds": {...}}
config = load_config_from_file('config.json')
config.validate()  # Ensures all settings are consistent
```

### Validation and Error Handling

```python
try:
    config = BenchmarkConfig(
        default_iterations=-10,  # Invalid
        thresholds=CachePerformanceThresholds(
            basic_operations_avg_ms=100,
            basic_operations_p95_ms=50  # Invalid: p95 < avg
        )
    )
    config.validate()
except ConfigurationError as e:
    print(f"Configuration error: {e}")
```

## Thread Safety

All configuration classes are immutable after construction and thread-safe.
Configuration loading functions are stateless and safe for concurrent use.
