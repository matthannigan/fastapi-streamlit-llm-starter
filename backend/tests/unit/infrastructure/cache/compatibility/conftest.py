"""
Test fixtures for compatibility module unit tests.

This module provides reusable fixtures specific to compatibility layer testing.
The compatibility module has no external dependencies requiring mocking,
as it only uses standard library components.

Note: This module exists for consistency with the testing structure,
but currently contains no fixtures as compatibility has no external dependencies.
"""

import pytest


# Note: No fixtures needed for compatibility module as it has no external dependencies.
# The module only uses standard library components (asyncio, inspect, logging, warnings, typing)
# which don't require mocking in unit tests following the testing philosophy of mocking
# only at system boundaries.