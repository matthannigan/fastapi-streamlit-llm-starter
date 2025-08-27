---
sidebar_label: models
---

# [REFACTORED] Comprehensive cache benchmarking data models with statistical analysis and comparison utilities.

  file_path: `backend/app/infrastructure/cache/benchmarks/models.py`

This module provides complete data model infrastructure for cache performance benchmarking
including individual result containers, before/after comparison analysis, and benchmark
suite aggregation with performance grading and statistical analysis capabilities.

## Classes

BenchmarkResult: Individual benchmark measurement with comprehensive metrics and analysis
ComparisonResult: Before/after performance comparison with regression detection
BenchmarkSuite: Collection of benchmark results with suite-level analysis and grading

## Key Features

- **Comprehensive Metrics**: Complete performance data including timing percentiles,
memory usage, throughput, success rates, and optional cache-specific metrics.

- **Statistical Analysis**: Built-in performance grading, threshold validation,
and comprehensive statistical analysis with percentile calculations.

- **Comparison Analysis**: Detailed before/after comparison with percentage changes,
regression detection, and improvement/degradation area identification.

- **Suite Aggregation**: Collection-level analysis with overall scoring, performance
grading, and operation-specific result retrieval.

- **Serialization Support**: Full JSON serialization support for data persistence,
API integration, and report generation with datetime stamping.

- **Performance Grading**: Automated performance assessment using industry-standard
thresholds with Excellent/Good/Acceptable/Poor/Critical classifications.

## Data Model Structure

BenchmarkResult contains individual benchmark metrics:
- Core timing metrics (avg, min, max, percentiles, std dev)
- Memory usage tracking (usage, peak consumption)
- Throughput and success rate analysis
- Optional cache-specific metrics (hit rates, compression)
- Metadata and timestamp information

ComparisonResult provides before/after analysis:
- Performance change percentages
- Regression detection flags
- Improvement and degradation area identification
- Strategic recommendations

BenchmarkSuite aggregates multiple results:
- Overall performance grading
- Suite-level scoring and pass rates
- Failed benchmark tracking
- Environment context preservation

## Usage Examples

### Individual Result Analysis

```python
result = BenchmarkResult(
    operation_type="get",
    avg_duration_ms=1.5,
    p95_duration_ms=3.2,
    operations_per_second=800.0,
    success_rate=1.0
)
print(result.performance_grade())  # "Excellent"
print(result.meets_threshold(5.0))  # True
data = result.to_dict()  # For serialization
```
Before/After Comparison:
```python
comparison = ComparisonResult(
    original_cache_results=old_result,
    new_cache_results=new_result,
    performance_change_percent=-15.2,  # 15.2% improvement
    regression_detected=False
)
print(comparison.summary())  # "Performance improved by 15.2%..."
recommendations = comparison.generate_recommendations()
```

### Suite Analysis

```python
suite = BenchmarkSuite(
    name="Redis Cache Performance",
    results=[result1, result2, result3],
    pass_rate=1.0,
    performance_grade="Good"
)
score = suite.calculate_overall_score()
get_result = suite.get_operation_result("get")
json_data = suite.to_json()  # Full suite serialization
```

## Thread Safety

All data model classes are immutable after construction and thread-safe for
concurrent access. Serialization methods are stateless and safe for concurrent use.
