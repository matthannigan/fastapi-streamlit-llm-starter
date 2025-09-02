---
sidebar_label: test_core
---

# Tests for core benchmark functionality.

  file_path: `backend/tests.old/infrastructure/cache/benchmarks/test_core.py`

This module tests the main benchmark orchestration classes including
CachePerformanceBenchmark and PerformanceRegressionDetector.

## TestCachePerformanceBenchmark

Test cases for CachePerformanceBenchmark class.

### test_initialization_default()

```python
def test_initialization_default(self):
```

Test benchmark initialization with default configuration.

### test_initialization_with_config()

```python
def test_initialization_with_config(self, development_config):
```

Test benchmark initialization with custom configuration.

### test_benchmark_with_production_config()

```python
def test_benchmark_with_production_config(self, production_config):
```

Test creating benchmark with production configuration.

### test_configuration_validation()

```python
def test_configuration_validation(self):
```

Test that invalid configuration raises error during validation.

### test_get_reporter_default()

```python
def test_get_reporter_default(self, test_cache):
```

Test getting default reporter.

### test_get_reporter_custom_format()

```python
def test_get_reporter_custom_format(self, test_cache):
```

Test getting reporter with custom format.

### test_benchmark_basic_operations()

```python
async def test_benchmark_basic_operations(self, mock_memory_tracker, test_cache):
```

Test running basic operations benchmark.

### test_comprehensive_benchmark_suite_cache_efficiency()

```python
async def test_comprehensive_benchmark_suite_cache_efficiency(self, mock_memory_tracker, test_cache):
```

Test cache efficiency through comprehensive benchmark suite.

### test_memory_usage_tracking()

```python
async def test_memory_usage_tracking(self, mock_memory_tracker, test_cache):
```

Test memory usage tracking in basic operations benchmark.

### test_run_comprehensive_benchmark_suite()

```python
async def test_run_comprehensive_benchmark_suite(self, mock_memory_tracker, test_cache):
```

Test running comprehensive benchmark suite.

### test_benchmark_timeout_handling()

```python
async def test_benchmark_timeout_handling(self, test_cache):
```

Test benchmark timeout handling.

### test_warmup_iterations()

```python
async def test_warmup_iterations(self, test_cache):
```

Test that warmup iterations are performed.

### test_error_handling_in_operations()

```python
async def test_error_handling_in_operations(self, test_cache):
```

Test error handling during benchmark operations.

### test_data_generation_integration()

```python
async def test_data_generation_integration(self, test_cache):
```

Test integration with data generator.

### test_statistical_analysis_integration()

```python
async def test_statistical_analysis_integration(self, test_cache):
```

Test integration with statistical calculator.

### test_memory_tracking_disabled()

```python
async def test_memory_tracking_disabled(self, test_cache):
```

Test benchmark with memory tracking disabled.

### test_compression_tests_disabled()

```python
async def test_compression_tests_disabled(self, test_cache):
```

Test benchmark with compression tests disabled.

### test_environment_info_collection()

```python
async def test_environment_info_collection(self, test_cache):
```

Test collection of environment information.

## TestPerformanceRegressionDetector

Test cases for PerformanceRegressionDetector class.

### test_initialization()

```python
def test_initialization(self):
```

Test regression detector initialization.

### test_compare_results_improvement()

```python
def test_compare_results_improvement(self):
```

Test comparison showing improvement.

### test_detect_timing_regression()

```python
def test_detect_timing_regression(self):
```

Test detecting timing regression.

### test_detect_memory_regression()

```python
def test_detect_memory_regression(self):
```

Test detecting memory regression.

### test_regression_detector_thresholds()

```python
def test_regression_detector_thresholds(self):
```

Test detector with custom thresholds.

### test_regression_detector_basic_functionality()

```python
def test_regression_detector_basic_functionality(self):
```

Test basic regression detector functionality.

### test_regression_threshold_configuration()

```python
def test_regression_threshold_configuration(self):
```

Test regression detection with custom thresholds.

### test_memory_regression_detection()

```python
def test_memory_regression_detection(self):
```

Test detection of memory usage regressions.

### test_success_rate_regression_detection()

```python
def test_success_rate_regression_detection(self):
```

Test detection of success rate regressions.

### test_edge_cases_handling()

```python
def test_edge_cases_handling(self):
```

Test handling of edge cases in regression detection.

## TestCachePresetBenchmarkCore

Test cache preset integration with core benchmark functionality.

### test_environment_detection_with_presets()

```python
async def test_environment_detection_with_presets(self, monkeypatch):
```

Test environment detection integrating cache preset information.

### test_benchmark_core_with_preset_environments()

```python
async def test_benchmark_core_with_preset_environments(self, monkeypatch):
```

Test core benchmark functionality across different preset environments.

### test_preset_configuration_integration_with_core()

```python
def test_preset_configuration_integration_with_core(self, monkeypatch):
```

Test preset configuration integration with benchmark core initialization.

### test_regression_detection_with_preset_scenarios()

```python
def test_regression_detection_with_preset_scenarios(self):
```

Test regression detection between different preset-based scenarios.
