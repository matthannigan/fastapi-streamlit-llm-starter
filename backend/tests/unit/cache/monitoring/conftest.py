"""
Test fixtures for monitoring module unit tests.

This module provides reusable fixtures specific to cache monitoring testing.

Note: This module exists for consistency with the testing structure,
but currently contains no fixtures as the monitoring module has no external dependencies
requiring mocking. The module only uses standard library components (logging, sys, time,
statistics, dataclasses, datetime, typing) which don't require mocking in unit tests
following the testing philosophy of mocking only at system boundaries.
"""


# Note: No fixtures needed for monitoring module as it has no external dependencies.
# The module only uses standard library components which don't require mocking
# in unit tests following the testing philosophy of mocking only at system boundaries.
