---
sidebar_label: test_utils
---

# Tests for benchmark utility functions.

  file_path: `backend/tests.old/infrastructure/cache/benchmarks/test_utils.py`

This module tests the statistical calculator and memory tracker utilities
with various data distributions and edge cases.

## TestStatisticalCalculator

Test cases for StatisticalCalculator utility class.

### test_percentile_calculation_even_data()

```python
def test_percentile_calculation_even_data(self):
```

Test percentile calculation with even number of data points.

### test_percentile_calculation_odd_data()

```python
def test_percentile_calculation_odd_data(self):
```

Test percentile calculation with odd number of data points.

### test_percentile_calculation_performance_data()

```python
def test_percentile_calculation_performance_data(self):
```

Test percentile calculation with realistic performance data.

### test_percentile_single_value()

```python
def test_percentile_single_value(self):
```

Test percentile calculation with single data point.

### test_percentile_empty_data()

```python
def test_percentile_empty_data(self):
```

Test percentile calculation with empty data.

### test_percentile_invalid_percentile()

```python
def test_percentile_invalid_percentile(self):
```

Test percentile calculation with invalid percentile values.

### test_standard_deviation_calculation()

```python
def test_standard_deviation_calculation(self):
```

Test standard deviation calculation.

### test_standard_deviation_uniform_data()

```python
def test_standard_deviation_uniform_data(self):
```

Test standard deviation with uniform data.

### test_standard_deviation_single_value()

```python
def test_standard_deviation_single_value(self):
```

Test standard deviation with single data point.

### test_standard_deviation_empty_data()

```python
def test_standard_deviation_empty_data(self):
```

Test standard deviation with empty data.

### test_outlier_detection_with_outliers()

```python
def test_outlier_detection_with_outliers(self):
```

Test outlier detection with clear outliers.

### test_outlier_detection_no_outliers()

```python
def test_outlier_detection_no_outliers(self):
```

Test outlier detection with no outliers.

### test_outlier_detection_edge_cases()

```python
def test_outlier_detection_edge_cases(self):
```

Test outlier detection edge cases.

### test_confidence_intervals_calculation()

```python
def test_confidence_intervals_calculation(self):
```

Test confidence interval calculation.

### test_confidence_intervals_different_levels()

```python
def test_confidence_intervals_different_levels(self):
```

Test confidence intervals with different confidence levels.

### test_confidence_intervals_edge_cases()

```python
def test_confidence_intervals_edge_cases(self):
```

Test confidence intervals edge cases.

### test_calculate_statistics_comprehensive()

```python
def test_calculate_statistics_comprehensive(self):
```

Test the unified calculate_statistics method.

## TestMemoryTracker

Test cases for MemoryTracker utility class.

### test_memory_tracker_initialization()

```python
def test_memory_tracker_initialization(self):
```

Test MemoryTracker initialization.

### test_get_memory_usage_with_psutil()

```python
def test_get_memory_usage_with_psutil(self, mock_process, mock_virtual_memory):
```

Test memory usage retrieval when psutil is available.

### test_get_memory_usage_fallback()

```python
def test_get_memory_usage_fallback(self, mock_getrusage, mock_virtual_memory):
```

Test memory usage retrieval fallback when psutil is unavailable.

### test_get_memory_usage_full_fallback()

```python
def test_get_memory_usage_full_fallback(self, mock_virtual_memory, mock_get_process_memory):
```

Test memory usage retrieval when both psutil and resource fail.

### test_get_process_memory_mb_basic()

```python
def test_get_process_memory_mb_basic(self):
```

Test basic process memory retrieval.

### test_memory_delta_calculation()

```python
def test_memory_delta_calculation(self):
```

Test memory delta calculation between measurements.

### test_memory_tracking_during_operation()

```python
def test_memory_tracking_during_operation(self):
```

Test memory tracking during a simulated operation.

### test_platform_specific_memory_handling()

```python
def test_platform_specific_memory_handling(self, mock_platform):
```

Test platform-specific memory handling.

### test_memory_tracker_error_handling()

```python
def test_memory_tracker_error_handling(self):
```

Test memory tracker error handling and recovery.

### test_memory_measurement_consistency()

```python
def test_memory_measurement_consistency(self):
```

Test that repeated memory measurements are consistent.

### test_memory_units_conversion()

```python
def test_memory_units_conversion(self):
```

Test memory units conversion accuracy.
