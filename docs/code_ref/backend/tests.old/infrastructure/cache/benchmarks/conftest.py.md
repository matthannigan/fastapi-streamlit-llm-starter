---
sidebar_label: conftest
---

# Shared fixtures for benchmark tests.

  file_path: `backend/tests.old/infrastructure/cache/benchmarks/conftest.py`

This module provides common test fixtures and utilities for testing
the modular benchmark components.

## sample_benchmark_result()

```python
def sample_benchmark_result() -> BenchmarkResult:
```

Create a sample benchmark result for testing.

## sample_comparison_result()

```python
def sample_comparison_result() -> ComparisonResult:
```

Create a sample comparison result for testing.

## sample_benchmark_suite()

```python
def sample_benchmark_suite(sample_benchmark_result) -> BenchmarkSuite:
```

Create a sample benchmark suite for testing.

## default_config()

```python
def default_config() -> BenchmarkConfig:
```

Create a default benchmark configuration.

## development_config()

```python
def development_config() -> BenchmarkConfig:
```

Create a development benchmark configuration.

## production_config()

```python
def production_config() -> BenchmarkConfig:
```

Create a production benchmark configuration.

## ci_config()

```python
def ci_config() -> BenchmarkConfig:
```

Create a CI benchmark configuration.

## default_thresholds()

```python
def default_thresholds() -> CachePerformanceThresholds:
```

Create default performance thresholds.

## strict_thresholds()

```python
def strict_thresholds() -> CachePerformanceThresholds:
```

Create strict performance thresholds for testing.

## data_generator()

```python
def data_generator() -> CacheBenchmarkDataGenerator:
```

Create a benchmark data generator.

## test_cache()

```python
def test_cache() -> InMemoryCache:
```

Create an in-memory cache for testing.

## performance_test_data()

```python
def performance_test_data() -> List[Dict[str, Any]]:
```

Generate test data for performance benchmarks.

## sample_environment_vars()

```python
def sample_environment_vars(monkeypatch):
```

Set up sample environment variables for testing.

## temp_config_file()

```python
def temp_config_file(tmp_path):
```

Create a temporary configuration file for testing.

## invalid_config_file()

```python
def invalid_config_file(tmp_path):
```

Create an invalid configuration file for testing.

## preset_development_cache()

```python
def preset_development_cache(monkeypatch):
```

Create a cache configured with development preset for testing.

## preset_production_cache()

```python
def preset_production_cache(monkeypatch):
```

Create a cache configured with production preset for testing.

## preset_ai_development_cache()

```python
def preset_ai_development_cache(monkeypatch):
```

Create a cache configured with ai-development preset for testing.

## preset_benchmark_config()

```python
def preset_benchmark_config(monkeypatch):
```

Create a benchmark configuration influenced by cache preset.

## multiple_preset_caches()

```python
def multiple_preset_caches(monkeypatch):
```

Create multiple caches with different preset configurations.

## preset_environment_setup()

```python
def preset_environment_setup(monkeypatch):
```

Set up complete preset environment for comprehensive testing.

## preset_test_data_scenarios()

```python
def preset_test_data_scenarios():
```

Generate test data scenarios for different preset configurations.
