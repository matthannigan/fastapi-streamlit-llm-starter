---
sidebar_label: utils
---

# Cache Benchmarking Utility Functions

  file_path: `backend/app/infrastructure/cache/benchmarks/utils.py`

This module provides statistical calculations and memory tracking utilities
for cache performance benchmarking. These utilities are extracted from the
original monolithic benchmarks module for better reusability and testing.

## Classes

StatisticalCalculator: Statistical analysis methods for benchmark data
MemoryTracker: Memory usage tracking and measurement utilities

The utilities support comprehensive statistical analysis including percentiles,
standard deviation, outlier detection, confidence intervals, and memory tracking
with fallback mechanisms for different environments.
