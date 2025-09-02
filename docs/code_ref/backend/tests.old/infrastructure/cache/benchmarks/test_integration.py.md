---
sidebar_label: test_integration
---

# Integration tests for benchmark system.

  file_path: `backend/tests.old/infrastructure/cache/benchmarks/test_integration.py`

This module tests end-to-end benchmark execution, report generation pipeline,
and configuration loading with real cache implementations.

## TestEndToEndBenchmarkExecution

Test end-to-end benchmark execution with real cache implementations.

### test_full_benchmark_with_memory_cache()

```python
async def test_full_benchmark_with_memory_cache(self):
```

Test complete benchmark execution with InMemoryCache.

### test_full_benchmark_with_mock_redis()

```python
async def test_full_benchmark_with_mock_redis(self, mock_redis_class):
```

Test complete benchmark execution with mocked Redis cache.

### test_benchmark_with_different_configurations()

```python
async def test_benchmark_with_different_configurations(self):
```

Test benchmark execution with different configuration presets.

### test_benchmark_error_recovery()

```python
async def test_benchmark_error_recovery(self):
```

Test benchmark behavior when cache operations fail.

### test_memory_tracking_integration()

```python
async def test_memory_tracking_integration(self, mock_memory_tracker):
```

Test memory tracking integration across benchmark execution.

### test_compression_tests_integration()

```python
async def test_compression_tests_integration(self):
```

Test compression benchmark integration.

## TestReportGenerationPipeline

Test the complete benchmark → results → reports pipeline.

### test_benchmark_to_all_report_formats()

```python
async def test_benchmark_to_all_report_formats(self):
```

Test complete pipeline from benchmark to all report formats.

### test_report_generation_with_failed_benchmarks()

```python
async def test_report_generation_with_failed_benchmarks(self):
```

Test report generation when some benchmarks fail.

### test_report_generation_with_custom_thresholds()

```python
async def test_report_generation_with_custom_thresholds(self):
```

Test report generation with custom performance thresholds.

### test_multiple_format_generation_consistency()

```python
async def test_multiple_format_generation_consistency(self):
```

Test that different report formats contain consistent information.

## TestConfigurationLoadingAndApplication

Test configuration loading and application in benchmarks.

### test_environment_to_config_to_benchmark()

```python
async def test_environment_to_config_to_benchmark(self, monkeypatch):
```

Test Environment → Config → Benchmark pipeline.

### test_file_to_config_to_benchmark()

```python
async def test_file_to_config_to_benchmark(self):
```

Test File → Config → Benchmark pipeline.

### test_config_preset_application()

```python
async def test_config_preset_application(self):
```

Test applying different configuration presets.

### test_configuration_validation_in_pipeline()

```python
def test_configuration_validation_in_pipeline(self):
```

Test that configuration validation works in the full pipeline.

### test_config_to_reporter_pipeline()

```python
async def test_config_to_reporter_pipeline(self):
```

Test configuration affecting reporter selection and behavior.

## TestPerformanceRegressionIntegration

Test performance regression detection in full pipeline.

### test_benchmark_comparison_workflow()

```python
async def test_benchmark_comparison_workflow(self):
```

Test comparing two benchmark runs for regression detection.

### test_full_regression_detection_pipeline()

```python
async def test_full_regression_detection_pipeline(self):
```

Test complete regression detection and reporting pipeline.

## TestCachePresetBenchmarkIntegration

Test cache preset integration with benchmark system.

### test_preset_based_config_loading()

```python
async def test_preset_based_config_loading(self, monkeypatch):
```

Test loading benchmark configuration with cache preset integration.

### test_multiple_preset_benchmark_scenarios()

```python
async def test_multiple_preset_benchmark_scenarios(self, monkeypatch):
```

Test benchmarking across different cache preset scenarios.

### test_preset_performance_comparison()

```python
async def test_preset_performance_comparison(self, monkeypatch):
```

Test performance comparison between different preset configurations.
