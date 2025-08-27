"""
Comprehensive test suite for GenericRedisCache core cache operations.

This module provides systematic behavioral testing of the fundamental cache
operations including get, set, delete, exists, and their interaction with
L1 cache, Redis backend, compression, and performance monitoring.

Test Coverage:
    - Basic cache operations: get, set, delete, exists
    - L1 cache and Redis backend coordination
    - TTL (Time To Live) management and expiration
    - Data compression and decompression functionality
    - Performance monitoring integration
    - Error handling and edge cases

Testing Philosophy:
    - Uses behavior-driven testing with Given/When/Then structure
    - Tests core business logic without mocking standard library components
    - Validates cache behavior consistency across different configurations
    - Ensures data integrity and proper error handling
    - Comprehensive edge case coverage for production reliability

Test Organization:
    - TestBasicCacheOperations: Core get, set, delete, exists functionality
    - TestL1CacheIntegration: L1 memory cache coordination with Redis
    - TestTTLAndExpiration: Time-to-live management and expiration behavior
    - TestDataCompressionIntegration: Compression functionality and thresholds

Fixtures and Mocks:
    From conftest.py:
        - default_generic_redis_config: Standard configuration dictionary
        - compression_redis_config: Configuration optimized for compression
        - no_l1_redis_config: Configuration without L1 cache
        - mock_redis_client: Stateful mock Redis client
        - sample_large_value: Large data for compression testing
        - bulk_test_data: Multiple key-value pairs for batch testing
        - compression_test_data: Data designed for compression testing
    From parent conftest.py:
        - sample_cache_key: Standard cache key for testing
        - sample_cache_value: Standard cache value for testing
        - sample_ttl: Standard TTL value for testing
        - short_ttl: Short TTL for expiration testing
        - mock_performance_monitor: Mock CachePerformanceMonitor instance
"""

import pytest
from typing import Dict, Any