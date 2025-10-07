"""
Test fixtures for security module unit tests.

This module provides reusable fixtures specific to cache security testing.

Note: This module exists for consistency with the testing structure,
but currently contains no fixtures as the security module's dependencies
(ConfigurationError, CachePerformanceMonitor) are already available in the
shared cache conftest.py file. The Redis connections are created dynamically
and returned by the methods, so they don't need mocking at the fixture level.
"""


# Note: No additional fixtures needed for security module as its dependencies
# (ConfigurationError, CachePerformanceMonitor) are already available in the shared
# cache conftest.py file. Redis clients are created dynamically within methods
# and can be mocked within individual test functions as needed.
