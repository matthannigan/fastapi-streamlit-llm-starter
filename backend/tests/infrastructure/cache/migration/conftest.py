"""
Test fixtures for migration module unit tests.

This module provides reusable fixtures specific to cache migration testing.

Note: This module exists for consistency with the testing structure,
but currently contains no fixtures as the migration module's dependencies
(ValidationError, CacheInterface) are already available in the shared
cache conftest.py file.
"""

import pytest


# Note: No additional fixtures needed for migration module as its dependencies
# (ValidationError, CacheInterface) are already available in the shared
# cache conftest.py file. The AIResponseCache and GenericRedisCache are only
# used in type hints for method signatures.