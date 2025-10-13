"""
Test fixtures for config_monitoring module unit tests.

This module provides reusable fixtures specific to configuration monitoring
testing, following the behavior-driven testing philosophy.

Note: This module exists for consistency with the testing structure,
but currently contains no fixtures as the config_monitoring module has
no external dependencies outside the app.infrastructure.resilience
boundary that require mocking or faking.

Dependencies:
- All imports are from Python standard library (time, json, logging, datetime,
  typing, dataclasses, enum, collections, threading, contextlib)
- No external dependencies requiring test doubles
- Component can be tested in isolation following our boundary rules

Testing Philosophy:
The config_monitoring module tests focus on documented contract behavior
including:
- Metric collection and recording per docstring specifications
- Alert generation based on threshold violations
- Thread-safe operations and state management
- Performance analysis and trend calculations
- Export functionality for monitoring systems
"""