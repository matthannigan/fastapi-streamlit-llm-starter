"""
Root conftest.py for all backend tests.

Provides pytest hooks and fixtures that apply to all test types
(unit, integration, etc.).
"""

import pytest


def pytest_collection_modifyitems(items):
    """
    Pytest hook to enforce serial execution for tests marked with @pytest.mark.no_parallel.

    Tests marked with no_parallel will run sequentially in the same pytest-xdist
    worker, preventing race conditions and environment pollution.

    Usage in test files:
        @pytest.mark.no_parallel
        class TestSomething:
            # All tests in this class run serially
            pass

        @pytest.mark.no_parallel
        def test_something():
            # This individual test runs serially
            pass

    Why This Is Needed:
        Some tests manipulate shared state (environment variables, global instances,
        Docker containers) that causes race conditions when run in parallel across
        pytest-xdist workers.

    Related:
        - pytest.ini markers section defines no_parallel marker
        - pytest-xdist documentation: https://pytest-xdist.readthedocs.io/en/latest/
    """
    for item in items:
        # Check if test has no_parallel marker
        if item.get_closest_marker("no_parallel"):
            # Force tests with no_parallel marker to run in same worker (sequentially)
            item.add_marker(pytest.mark.xdist_group(name="serial_only"))
