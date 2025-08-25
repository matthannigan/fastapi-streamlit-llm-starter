---
sidebar_label: config
---

# Cache Benchmark Configuration Management

  file_path: `backend/app/infrastructure/cache/benchmarks/config.py`

This module provides configuration management for cache performance benchmarking,
including performance thresholds, environment-specific presets, and configuration
loading from various sources.

## Classes

CachePerformanceThresholds: Performance threshold definitions
BenchmarkConfig: Complete benchmark configuration
ConfigPresets: Environment-specific configuration presets

## Functions

load_config_from_env: Load configuration from environment variables
load_config_from_file: Load configuration from JSON/YAML files
get_default_config: Get default configuration settings

The configuration system supports environment variables, JSON/YAML files,
and programmatic configuration for maximum flexibility.
