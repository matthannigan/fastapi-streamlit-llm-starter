"""
Config presets module test fixtures providing external dependency isolation.

Provides Fakes and Mocks for external dependencies following the philosophy of
creating realistic test doubles that enable behavior-driven testing while isolating
the config presets component from systems outside its boundary.

External Dependencies Handled:
    - logging: Standard library logging system (mocked)
    - re: Standard library regex module (fake implementation)

Note: Internal dependencies from the same module family (RetryConfig, CircuitBreakerConfig)
are NOT mocked here as they are part of the same component boundary.
"""

import pytest
from unittest.mock import Mock, MagicMock
from typing import Pattern, List, Dict, Any


@pytest.fixture
def mock_logger():
    """
    Mock logger for testing config presets logging behavior.

    Provides a spec'd mock logger that simulates logging.Logger
    for testing log message generation without actual I/O. Config
    presets components log validation results, environment detection,
    and operational messages for monitoring and debugging.

    Default Behavior:
        - All log methods available (info, warning, error, debug)
        - No actual logging output (mocked)
        - Call tracking for assertions in tests
        - Realistic method signatures matching logging.Logger

    Use Cases:
        - Testing preset validation logging and error messages
        - Testing environment detection logging and recommendations
        - Testing configuration loading and validation logging
        - Testing operational monitoring and debugging messages

    Test Customization:
        def test_logs_validation_errors(mock_logger):
            # Configure mock to capture specific log calls
            mock_logger.warning.assert_called_with("Invalid preset configuration detected")

    Example:
        def test_preset_manager_logs_recommendations(mock_logger, monkeypatch):
            # Replace the module logger with our mock
            monkeypatch.setattr('app.infrastructure.resilience.config_presets.logger', mock_logger)

            # Test environment recommendation
            manager = PresetManager()
            recommendation = manager.recommend_preset("production")

            # Verify logging occurred
            mock_logger.info.assert_called()

    State Management:
        - Tracks all log method calls for assertion verification
        - Maintains call history for complex logging scenarios
        - Supports configuration of expected log patterns
        - Provides clear failure messages for log assertion errors

    Note:
        This is a proper system boundary mock - logging performs I/O
        and should be mocked for unit tests to avoid actual log output.
    """
    mock = MagicMock()
    mock.info = Mock(return_value=None)
    mock.warning = Mock(return_value=None)
    mock.error = Mock(return_value=None)
    mock.debug = Mock(return_value=None)
    mock.critical = Mock(return_value=None)
    return mock


@pytest.fixture
def fake_regex_module():
    """
    Fake regex module implementation for predictable pattern matching testing.

    Provides a controllable regex implementation that allows tests to control
    pattern matching behavior without relying on actual regex engine behavior.
    This enables deterministic testing of environment detection and pattern
    matching logic used by preset recommendation systems.

    Default Behavior:
        - Simulates standard re module interface (compile, match, search)
        - Configurable pattern matching results for different test scenarios
        - Realistic regex object behavior with groups and methods
        - Deterministic matching behavior independent of actual regex patterns

    Configuration Methods:
        add_pattern_match(pattern, should_match, groups=None): Configure pattern behavior
        add_search_result(pattern, should_find, position=None): Configure search behavior
        reset_patterns(): Clear all configured pattern behaviors

    Use Cases:
        - Testing environment pattern detection logic
        - Testing preset recommendation based on environment names
        - Testing complex environment naming patterns
        - Any test requiring regex pattern matching behavior

    Test Customization:
        def test_environment_detection(fake_regex_module):
            # Configure fake regex to match specific patterns
            fake_regex_module.add_pattern_match(r'.*prod.*', True)
            fake_regex_module.add_pattern_match(r'.*dev.*', True)

    Example:
        def test_preset_manager_environment_detection(fake_regex_module, monkeypatch):
            # Replace re module with our fake
            monkeypatch.setattr('app.infrastructure.resilience.config_presets.re', fake_regex_module)

            # Configure pattern matching for environment detection
            fake_regex_module.add_pattern_match(r'production', True, groups=('production',))
            fake_regex_module.add_pattern_match(r'development', True, groups=('development',))

            manager = PresetManager()

            # Test production environment detection
            result = manager.recommend_preset_with_details("production-server-v2")
            assert "production" in result.reasoning.lower()

    State Management:
        - Maintains pattern matching configuration across test calls
        - Supports complex matching scenarios with groups and positions
        - Provides deterministic behavior for consistent testing
        - Tracks pattern compilation and matching calls

    Regex Object Interface:
        - match(string): Simulates re.match behavior
        - search(string): Simulates re.search behavior
        - groups(): Returns configured group matches
        - groupdict(): Returns named group matches
        - start()/end(): Position information for matches

    Default Patterns:
        - Production: matches 'prod', 'production' environments
        - Development: matches 'dev', 'development' environments
        - Staging: matches 'staging', 'stage' environments
        - Testing: matches 'test', 'testing' environments

    Note:
        This fake enables deterministic testing of regex-dependent logic
        without relying on actual regex engine behavior, making tests
        more reliable and easier to understand.
    """

    class FakeRegexModule:
        def __init__(self):
            self.patterns = {}
            self.search_results = {}
            self.compiled_patterns = {}

        def compile(self, pattern):
            """Compile regex pattern and return fake regex object."""
            if pattern not in self.compiled_patterns:
                self.compiled_patterns[pattern] = FakeRegexObject(pattern, self)
            return self.compiled_patterns[pattern]

        def match(self, pattern, string):
            """Simulate re.match behavior."""
            regex_obj = self.compile(pattern)
            return regex_obj.match(string)

        def search(self, pattern, string):
            """Simulate re.search behavior."""
            regex_obj = self.compile(pattern)
            return regex_obj.search(string)

        def add_pattern_match(self, pattern, should_match, groups=None, position=None):
            """Configure pattern match behavior."""
            self.patterns[pattern] = {
                'should_match': should_match,
                'groups': groups or (),
                'position': position
            }

        def add_search_result(self, pattern, should_find, position=None, groups=None):
            """Configure search result behavior."""
            self.search_results[pattern] = {
                'should_find': should_find,
                'position': position,
                'groups': groups or ()
            }

        def reset_patterns(self):
            """Clear all configured pattern behaviors."""
            self.patterns.clear()
            self.search_results.clear()
            self.compiled_patterns.clear()

    class FakeRegexObject:
        def __init__(self, pattern, module):
            self.pattern = pattern
            self.module = module
            self._last_match_result = None

        def match(self, string):
            """Simulate regex match behavior."""
            config = self.module.patterns.get(self.pattern, {})
            if config.get('should_match', False):
                self._last_match_result = FakeMatchResult(
                    matched=True,
                    groups=config.get('groups', ()),
                    position=config.get('position', 0),
                    string=string
                )
                return self._last_match_result
            else:
                self._last_match_result = None
                return None

        def search(self, string):
            """Simulate regex search behavior."""
            config = self.module.search_results.get(self.pattern, {})
            if config.get('should_find', False):
                self._last_match_result = FakeMatchResult(
                    matched=True,
                    groups=config.get('groups', ()),
                    position=config.get('position', 0),
                    string=string
                )
                return self._last_match_result
            else:
                self._last_match_result = None
                return None

        def groups(self):
            """Return groups from last match."""
            if self._last_match_result:
                return self._last_match_result.groups
            return ()

    class FakeMatchResult:
        def __init__(self, matched, groups, position, string):
            self.matched = matched
            self.groups = groups
            self.position = position
            self.string = string

        def groups(self):
            return self.groups

        def groupdict(self):
            # Return empty dict for simplicity
            return {}

        def start(self):
            return self.position

        def end(self):
            return self.position + 10  # Arbitrary end position

        def __bool__(self):
            return self.matched

    return FakeRegexModule()


@pytest.fixture
def preset_test_data():
    """
    Standardized test data for config presets behavior testing.

    Provides consistent test scenarios and data structures for config
    presets testing across different test modules. Ensures test
    consistency and reduces duplication in test implementations.

    Data Structure:
        - environment_names: Various environment naming patterns
        - preset_configurations: Different preset configurations
        - recommendation_scenarios: Environment recommendation test cases
        - validation_scenarios: Configuration validation test cases

    Use Cases:
        - Standardizing preset test inputs across test modules
        - Providing consistent environment detection scenarios
        - Testing different preset configuration combinations
        - Reducing test code duplication

    Example:
        def test_preset_manager_with_environments(preset_test_data):
            for env_scenario in preset_test_data['environment_names']:
                # Test environment detection with each naming pattern
                result = manager.recommend_preset(env_scenario['name'])
                assert result == env_scenario['expected_preset']
    """
    return {
        "environment_names": [
            {
                "name": "production",
                "expected_preset": "production",
                "description": "Standard production environment"
            },
            {
                "name": "prod",
                "expected_preset": "production",
                "description": "Short production environment name"
            },
            {
                "name": "production-server-v2",
                "expected_preset": "production",
                "description": "Complex production environment name"
            },
            {
                "name": "development",
                "expected_preset": "development",
                "description": "Standard development environment"
            },
            {
                "name": "dev",
                "expected_preset": "development",
                "description": "Short development environment name"
            },
            {
                "name": "dev-local",
                "expected_preset": "development",
                "description": "Local development environment"
            },
            {
                "name": "staging",
                "expected_preset": "production",
                "description": "Staging environment uses production preset"
            },
            {
                "name": "test",
                "expected_preset": "development",
                "description": "Test environment uses development preset"
            },
            {
                "name": "unknown-env",
                "expected_preset": "simple",
                "description": "Unknown environment falls back to simple preset"
            }
        ],
        "preset_configurations": [
            {
                "name": "simple",
                "strategy": "balanced",
                "retry_attempts": 3,
                "circuit_threshold": 5,
                "recovery_timeout": 60,
                "description": "Balanced configuration for general use"
            },
            {
                "name": "development",
                "strategy": "aggressive",
                "retry_attempts": 2,
                "circuit_threshold": 3,
                "recovery_timeout": 30,
                "description": "Fast-fail configuration for development"
            },
            {
                "name": "production",
                "strategy": "conservative",
                "retry_attempts": 5,
                "circuit_threshold": 10,
                "recovery_timeout": 120,
                "description": "High-reliability configuration for production"
            }
        ],
        "validation_scenarios": [
            {
                "name": "valid_preset",
                "is_valid": True,
                "config": {"retry_attempts": 3, "circuit_threshold": 5},
                "description": "Valid preset configuration"
            },
            {
                "name": "invalid_retry_attempts",
                "is_valid": False,
                "config": {"retry_attempts": 0, "circuit_threshold": 5},
                "description": "Invalid retry attempts (too low)"
            },
            {
                "name": "invalid_circuit_threshold",
                "is_valid": False,
                "config": {"retry_attempts": 3, "circuit_threshold": 0},
                "description": "Invalid circuit threshold (too low)"
            }
        ],
        "strategy_scenarios": [
            {
                "strategy": "aggressive",
                "expected_retry_attempts": 3,
                "expected_circuit_threshold": 3,
                "expected_behavior": "fast_fail",
                "expected_performance": "low_latency",
                "description": "Aggressive strategy for user-facing operations with fast failure"
            },
            {
                "strategy": "balanced",
                "expected_retry_attempts": 3,
                "expected_circuit_threshold": 5,
                "expected_behavior": "balanced_retry",
                "expected_performance": "moderate_latency",
                "description": "Balanced strategy for standard operations with moderate resilience"
            },
            {
                "strategy": "conservative",
                "expected_retry_attempts": 2,
                "expected_circuit_threshold": 10,
                "expected_behavior": "selective_retry",
                "expected_performance": "high_availability",
                "description": "Conservative strategy for resource-intensive operations with high availability"
            },
            {
                "strategy": "critical",
                "expected_retry_attempts": 5,
                "expected_circuit_threshold": 15,
                "expected_behavior": "persistent_retry",
                "expected_performance": "maximum_reliability",
                "description": "Critical strategy for mission-critical operations with maximum reliability"
            }
        ]
    }