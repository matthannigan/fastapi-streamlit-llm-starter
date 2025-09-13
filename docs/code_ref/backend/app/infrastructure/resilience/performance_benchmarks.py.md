---
sidebar_label: performance_benchmarks
---

# Performance benchmarking for resilience configuration loading.

  file_path: `backend/app/infrastructure/resilience/performance_benchmarks.py`

This module provides comprehensive performance testing and monitoring
for the resilience configuration system with a target of <100ms loading time.

## BenchmarkResult

Result of a performance benchmark.

## PerformanceThreshold

Performance thresholds for different operations.

## BenchmarkSuite

Collection of benchmark results with analysis.

### to_dict()

```python
def to_dict(self) -> Dict[str, Any]:
```

Convert benchmark suite to dictionary.

### to_json()

```python
def to_json(self) -> str:
```

Convert benchmark suite to JSON string.

## ConfigurationPerformanceBenchmark

Performance benchmark suite for resilience configuration loading.

Provides comprehensive testing of configuration loading performance
with detailed metrics and regression detection.

### __init__()

```python
def __init__(self):
```

Initialize performance benchmark.

### measure_performance()

```python
def measure_performance(self, operation_name: str, operation_func: Callable, iterations: int = 1):
```

Measure operation performance.

Args:
    operation_name: Name of the operation being measured
    operation_func: Function to measure
    iterations: Number of iterations to average over
    
Returns:
    BenchmarkResult with performance metrics

### benchmark_preset_loading()

```python
def benchmark_preset_loading(self, iterations: int = 100) -> BenchmarkResult:
```

Benchmark preset loading performance.

Args:
    iterations: Number of iterations to run
    
Returns:
    BenchmarkResult for preset loading

### benchmark_settings_initialization()

```python
def benchmark_settings_initialization(self, iterations: int = 50) -> BenchmarkResult:
```

Benchmark Settings class initialization performance.

Args:
    iterations: Number of iterations to run
    
Returns:
    BenchmarkResult for settings initialization

### benchmark_resilience_config_loading()

```python
def benchmark_resilience_config_loading(self, iterations: int = 50) -> BenchmarkResult:
```

Benchmark resilience configuration loading performance.

Args:
    iterations: Number of iterations to run
    
Returns:
    BenchmarkResult for config loading

### benchmark_service_initialization()

```python
def benchmark_service_initialization(self, iterations: int = 25) -> BenchmarkResult:
```

Benchmark AIServiceResilience initialization performance.

Args:
    iterations: Number of iterations to run
    
Returns:
    BenchmarkResult for service initialization

### benchmark_custom_config_loading()

```python
def benchmark_custom_config_loading(self, iterations: int = 25) -> BenchmarkResult:
```

Benchmark custom configuration loading performance.

Args:
    iterations: Number of iterations to run
    
Returns:
    BenchmarkResult for custom config loading

### benchmark_legacy_config_loading()

```python
def benchmark_legacy_config_loading(self, iterations: int = 25) -> BenchmarkResult:
```

Benchmark legacy configuration loading performance.

Args:
    iterations: Number of iterations to run
    
Returns:
    BenchmarkResult for legacy config loading

### benchmark_validation_performance()

```python
def benchmark_validation_performance(self, iterations: int = 50) -> BenchmarkResult:
```

Benchmark configuration validation performance.

Args:
    iterations: Number of iterations to run
    
Returns:
    BenchmarkResult for validation performance

### run_comprehensive_benchmark()

```python
def run_comprehensive_benchmark(self) -> BenchmarkSuite:
```

Run comprehensive performance benchmark suite.

Returns:
    BenchmarkSuite with all results

### analyze_performance_trends()

```python
def analyze_performance_trends(self, historical_results: List[BenchmarkSuite]) -> Dict[str, Any]:
```

Analyze performance trends across multiple benchmark runs.

Args:
    historical_results: List of previous benchmark suite results
    
Returns:
    Performance trend analysis

### generate_performance_report()

```python
def generate_performance_report(self, suite: BenchmarkSuite) -> str:
```

Generate human-readable performance report.

Args:
    suite: BenchmarkSuite to generate report for
    
Returns:
    Formatted performance report
