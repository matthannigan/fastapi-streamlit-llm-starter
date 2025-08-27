"""
Test fixtures for cache benchmarks module unit tests.

This module provides reusable fixtures specific to cache benchmark testing.
All fixtures provide 'happy path' behavior based on public contracts from 
backend/contracts/infrastructure/cache/benchmarks/ directory.

Note: The benchmarks modules have very few external dependencies that aren't already
covered by the shared cache conftest.py file. Most dependencies are either internal
to the benchmarks package or are standard library modules.

Dependencies covered by shared cache conftest.py:
    - ConfigurationError (from app.core.exceptions)
    - CacheInterface (from app.infrastructure.cache.base)
    - CachePerformanceMonitor (from app.infrastructure.cache.monitoring)

Internal benchmarks dependencies (no mocking needed):
    - BenchmarkResult, BenchmarkSuite, ComparisonResult (from .models)
    - StatisticalCalculator, MemoryTracker (from .utils)
    - CacheBenchmarkDataGenerator (from .generator)
    - BenchmarkConfig, ConfigPresets, CachePerformanceThresholds (from .config)
    - ReporterFactory and reporter classes (from .reporting)

Standard library dependencies (no mocking needed):
    - json, random, string, datetime, typing, math, statistics, logging
    - dataclasses, abc, asyncio, time

Design Philosophy:
    - Fixtures represent 'happy path' successful behavior only
    - Error scenarios are configured within individual test functions
    - All fixtures use public contracts from backend/contracts/ directory
    - Mock dependencies are spec'd against real classes for accuracy
    - Mock only at system boundaries (external dependencies)
"""

import pytest


# Note: No additional fixtures needed for benchmarks modules as:
# 1. External dependencies (ConfigurationError, CacheInterface, CachePerformanceMonitor) 
#    are already available in the shared cache conftest.py file
# 2. Internal dependencies are all defined within the benchmarks package itself
# 3. Remaining dependencies are standard library modules which don't require mocking
#    in unit tests following the testing philosophy of mocking only at system boundaries
