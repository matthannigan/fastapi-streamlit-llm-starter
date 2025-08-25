---
sidebar_label: generator
---

# Cache Benchmark Data Generator

  file_path: `backend/app/infrastructure/cache/benchmarks/generator.py`

This module provides realistic test data generation for cache performance benchmarking.
It generates varied datasets that simulate real-world cache usage patterns including
different sizes, types, and complexity levels.

## Classes

CacheBenchmarkDataGenerator: Main data generator for benchmarks

The generator creates different types of test data:
- Small data sets for basic operations
- Medium and large data sets for performance testing
- JSON structured data for complex objects
- Memory pressure data for load testing
- Concurrent access patterns for multi-threading tests
- Compression test data with varying compressibility
