---
sidebar_label: core
---

# Cache Performance Benchmarking Core

  file_path: `backend/app/infrastructure/cache/benchmarks/core.py`

This module contains the main benchmarking orchestration classes including
the CachePerformanceBenchmark class and PerformanceRegressionDetector.

## Classes

PerformanceRegressionDetector: Automated regression detection and alerting
CachePerformanceBenchmark: Main benchmarking orchestration class

The core module coordinates all benchmarking activities while using the
extracted utilities, data models, and configuration from other modules.
