"""
Test fixtures for CacheInterface unit tests.

This module provides reusable fixtures following behavior-driven testing
principles. Since CacheInterface is an abstract base class with no external
dependencies (only standard library imports), there are no dependency mocks
required for testing the interface itself.

The fixtures here primarily provide test data and utilities for testing
concrete implementations of the CacheInterface contract.

Fixture Categories:
    - Interface compliance test utilities
    - Mock implementations for polymorphism testing

Design Philosophy:
    - CacheInterface has no external dependencies requiring mocking
    - Fixtures support testing interface compliance and polymorphic behavior
    - Test data fixtures are minimal since this is an abstract interface
    - Focus on testing that concrete implementations honor the contract
"""

from typing import Any, Optional
from unittest.mock import AsyncMock, MagicMock

import pytest


@pytest.fixture
def interface_test_keys():
    """
    Set of diverse cache keys for interface compliance testing.

    Provides a variety of cache key patterns to test that concrete
    implementations properly handle different key formats as allowed
    by the CacheInterface contract.
    """
    return [
        "simple_key",
        "key:with:colons",
        "key-with-dashes",
        "key_with_underscores",
        "123_numeric_prefix",
        "UPPERCASE_KEY",
        "mixedCase_Key",
        "key.with.dots",
        "very_long_key_name_that_tests_length_handling_by_implementations",
    ]


@pytest.fixture
def interface_test_values():
    """
    Set of diverse cache values for interface compliance testing.

    Provides a variety of value types and structures to test that
    concrete implementations properly handle different data types
    as specified in the CacheInterface contract.
    """
    return [
        # Simple string
        "simple string value",
        # Integer
        42,
        # Float
        3.14159,
        # Boolean
        True,
        # None value
        None,
        # List
        ["item1", "item2", "item3"],
        # Dictionary
        {"name": "test", "value": 123, "nested": {"key": "value"}},
        # Complex nested structure
        {
            "users": [{"id": 1, "name": "Alice"}, {"id": 2, "name": "Bob"}],
            "metadata": {"created_at": "2023-01-01T12:00:00Z", "version": 1.0},
        },
    ]


@pytest.fixture
def interface_compliance_test_cases():
    """
    Test cases for verifying CacheInterface contract compliance.

    Provides a set of test scenarios that can be used to verify that
    concrete implementations properly follow the CacheInterface contract
    including behavior specifications from the docstrings.
    """
    return [
        {
            "name": "basic_get_set_delete",
            "description": "Test basic cache operations work as documented",
            "key": "test:basic",
            "value": {"data": "basic test"},
            "ttl": None,
        },
        {
            "name": "get_nonexistent_key",
            "description": "Test get returns None for missing keys",
            "key": "nonexistent:key",
            "expected_result": None,
        },
        {
            "name": "set_with_ttl",
            "description": "Test set operation with TTL parameter",
            "key": "test:ttl",
            "value": {"data": "ttl test"},
            "ttl": 3600,
        },
        {
            "name": "delete_nonexistent_key",
            "description": "Test delete is idempotent for missing keys",
            "key": "nonexistent:delete",
            "should_not_raise": True,
        },
        {
            "name": "overwrite_existing_key",
            "description": "Test set overwrites existing values",
            "key": "test:overwrite",
            "initial_value": {"data": "initial"},
            "new_value": {"data": "updated"},
            "ttl": None,
        },
        {
            "name": "type_preservation",
            "description": "Test that data types are preserved",
            "test_cases": [
                ("string", "test_string"),
                ("integer", 42),
                ("float", 3.14),
                ("boolean", True),
                ("list", [1, 2, 3]),
                ("dict", {"key": "value"}),
            ],
        },
    ]


@pytest.fixture
def polymorphism_test_scenarios():
    """
    Test scenarios for verifying polymorphic usage of CacheInterface.

    Provides test scenarios that verify code can work with any
    CacheInterface implementation without knowing the specific
    concrete type, ensuring the interface abstraction works correctly.
    """
    return [
        {
            "name": "service_with_cache_dependency",
            "description": "Test service that accepts any CacheInterface implementation",
            "test_operations": [
                ("store_user", "user:123", {"name": "John", "active": True}),
                ("retrieve_user", "user:123"),
                ("remove_user", "user:123"),
            ],
        },
        {
            "name": "cache_factory_pattern",
            "description": "Test factory that returns different CacheInterface implementations",
            "implementations": ["memory", "redis", "mock"],
            "common_operations": ["get", "set", "delete"],
        },
        {
            "name": "cache_switching",
            "description": "Test code that can switch between cache implementations",
            "scenario": "fallback_on_failure",
        },
    ]


# Note: Since CacheInterface is an abstract base class with no external dependencies,
# the fixtures above focus on providing test data and utilities for testing concrete
# implementations rather than mocking dependencies. The abstract interface itself
# only depends on standard library modules (abc, typing) which don't require mocking.
