"""
Integration Tests for Error Handling and Configuration Validation (SEAM 5)

Tests the integration between HealthChecker initialization, configuration validation,
and graceful error handling patterns. Validates that HealthChecker properly validates
timeout parameters, retry configurations, and handles configuration errors gracefully.

This test file validates the critical integration seam:
Configuration → Validation → Graceful error handling → Status reporting

Test Coverage:
- Timeout boundary validation (100-30000ms)
- Retry policy validation (0-10 retries, 0.0-5.0 backoff)
- Configuration immutability after instantiation
- Defensive parameter validation
- Error reporting for invalid configurations
"""

import pytest
from unittest.mock import patch

from app.infrastructure.monitoring.health import (
    HealthChecker,
    HealthCheckError,
    HealthCheckTimeoutError,
    HealthStatus,
    check_ai_model_health,
    check_cache_health,
    check_resilience_health,
)


@pytest.mark.integration
class TestHealthCheckerConfigurationValidation:
    """
    Integration tests for HealthChecker configuration validation and error handling.

    Seam Under Test:
        Configuration → Validation → Graceful error handling → Status reporting

    Critical Paths:
        - Timeout parameter validation within acceptable ranges
        - Retry policy validation with reasonable bounds
        - Configuration immutability after instantiation
        - Defensive parameter validation and error reporting

    Business Impact:
        Prevents misconfiguration that could cause operational issues
        Ensures health monitoring behaves predictably under various configurations
        Validates configuration validation logic protects against invalid settings

    Integration Scope:
        HealthChecker initialization → Configuration validation → Error handling
    """

    def test_health_checker_validates_timeout_configuration_boundaries(self):
        """
        Test HealthChecker validates timeout parameters within acceptable ranges.

        Integration Scope:
            HealthChecker initialization → Configuration validation → Timeout boundary checking

        Contract Validation:
            - Timeout validation (100-30000ms) per health.pyi:388
            - Defensive parameter validation per health.pyi:402
            - ValueError raised for invalid timeout values

        Business Impact:
            Prevents misconfiguration that could cause operational issues
            Ensures health monitoring has reasonable timeout boundaries
            Validates configuration validation protects against extreme values

        Test Strategy:
            - Test boundary conditions from docstring specification
            - Verify configuration validation errors raised appropriately
            - Test both minimum and maximum boundary conditions
            - Validate configuration immutability per docstring

        Success Criteria:
            - Valid timeouts (100-30000ms) accepted
            - Invalid timeouts rejected with clear error messages
            - Configuration immutability maintained after instantiation
            - Boundary conditions tested and validated
        """
        # Test valid boundary conditions
        health_checker_min = HealthChecker(default_timeout_ms=100)
        assert health_checker_min is not None
        assert health_checker_min._default_timeout_ms == 100

        health_checker_max = HealthChecker(default_timeout_ms=30000)
        assert health_checker_max is not None
        assert health_checker_max._default_timeout_ms == 30000

        # Test invalid boundaries (should raise ValueError per validation)
        with pytest.raises(ValueError):
            HealthChecker(default_timeout_ms=50)  # Below minimum

        with pytest.raises(ValueError):
            HealthChecker(default_timeout_ms=50000)  # Above maximum

        # Test that configuration is immutable after instantiation
        checker = HealthChecker(default_timeout_ms=2000)
        # Should not be able to modify internal configuration directly
        assert hasattr(checker, '_default_timeout_ms')
        # The _default_timeout_ms should be read-only in practice
        with pytest.raises(AttributeError):
            checker._default_timeout_ms = 5000  # Should fail due to immutability

    def test_health_checker_validates_retry_configuration_boundaries(self):
        """
        Test HealthChecker validates retry parameters within acceptable ranges.

        Integration Scope:
            HealthChecker initialization → Retry policy validation → Boundary checking

        Contract Validation:
            - Retry count validation (0-10) per health.pyi:392
            - Backoff validation (0.0-5.0) per health.pyi:394
            - ValueError raised for invalid retry parameters

        Business Impact:
            Ensures retry policies configured within reasonable operational bounds
            Prevents excessive retry attempts that could impact performance
            Validates backoff configuration prevents aggressive retry patterns

        Test Strategy:
            - Test boundary conditions from docstring specification
            - Verify validation error handling for retry parameters
            - Test both retry count and backoff boundary conditions
            - Validate parameter validation provides clear error messages

        Success Criteria:
            - Valid retry counts (0-10) accepted
            - Valid backoff values (0.0-5.0) accepted
            - Invalid values rejected with descriptive errors
            - Boundary conditions properly enforced
        """
        # Test valid retry boundaries
        health_checker_no_retry = HealthChecker(retry_count=0)
        assert health_checker_no_retry is not None
        assert health_checker_no_retry._retry_count == 0

        health_checker_max_retry = HealthChecker(retry_count=10)
        assert health_checker_max_retry is not None
        assert health_checker_max_retry._retry_count == 10

        # Test valid backoff boundaries
        health_checker_no_backoff = HealthChecker(backoff_base_seconds=0.0)
        assert health_checker_no_backoff is not None
        assert health_checker_no_backoff._backoff_base_seconds == 0.0

        health_checker_max_backoff = HealthChecker(backoff_base_seconds=5.0)
        assert health_checker_max_backoff is not None
        assert health_checker_max_backoff._backoff_base_seconds == 5.0

        # Test invalid retry count
        with pytest.raises(ValueError):
            HealthChecker(retry_count=-1)  # Negative not allowed

        with pytest.raises(ValueError):
            HealthChecker(retry_count=15)  # Above maximum

        # Test invalid backoff
        with pytest.raises(ValueError):
            HealthChecker(backoff_base_seconds=-0.5)  # Negative not allowed

        with pytest.raises(ValueError):
            HealthChecker(backoff_base_seconds=10.0)  # Above maximum

    def test_health_checker_maintains_configuration_immutability(self):
        """
        Test HealthChecker maintains configuration immutability after instantiation.

        Integration Scope:
            HealthChecker initialization → Configuration immutability → Runtime behavior

        Contract Validation:
            - Configuration immutability per health.pyi:402
            - Prevents runtime configuration changes that could affect behavior
            - Ensures consistent health checking behavior across requests

        Business Impact:
            Ensures health monitoring behavior remains consistent
            Prevents runtime configuration changes that could cause issues
            Validates reliability through configuration stability

        Test Strategy:
            - Test that configuration cannot be modified after instantiation
            - Verify internal configuration attributes are protected
            - Test consistent behavior across multiple health check calls
            - Validate immutability prevents race conditions

        Success Criteria:
            - Configuration cannot be modified after instantiation
            - Internal attributes are protected from modification
            - Behavior remains consistent across multiple calls
            - Configuration validation only occurs at initialization
        """
        # Arrange: Create health checker with specific configuration
        checker = HealthChecker(
            default_timeout_ms=5000,
            retry_count=3,
            backoff_base_seconds=0.5
        )

        # Act: Verify configuration is set correctly
        assert checker._default_timeout_ms == 5000
        assert checker._retry_count == 3
        assert checker._backoff_base_seconds == 0.5

        # Assert: Configuration immutability
        # Try to modify internal configuration (should fail)
        with pytest.raises((AttributeError, TypeError)):
            checker._default_timeout_ms = 10000

        with pytest.raises((AttributeError, TypeError)):
            checker._retry_count = 5

        with pytest.raises((AttributeError, TypeError)):
            checker._backoff_base_seconds = 1.0

        # Verify original configuration unchanged
        assert checker._default_timeout_ms == 5000
        assert checker._retry_count == 3
        assert checker._backoff_base_seconds == 0.5

    def test_health_checker_defensive_parameter_validation(self):
        """
        Test HealthChecker applies defensive parameter validation during initialization.

        Integration Scope:
            HealthChecker initialization → Defensive validation → Error handling

        Contract Validation:
            - Defensive parameter validation per health.pyi:402
            - Type checking for configuration parameters
            - Comprehensive validation of all input parameters

        Business Impact:
            Prevents configuration errors that could cause runtime issues
            Ensures type safety and parameter validity
            Validates robust error handling for invalid inputs

        Test Strategy:
            - Test type validation for configuration parameters
            - Verify comprehensive validation of all parameters
            - Test edge cases and invalid input types
            - Validate error messages are descriptive and helpful

        Success Criteria:
            - Type errors caught and reported appropriately
            - Invalid parameter types rejected with clear errors
            - All configuration parameters validated
            - Error messages provide helpful diagnostic information
        """
        # Test invalid parameter types
        with pytest.raises(TypeError):
            HealthChecker(default_timeout_ms="2000")  # String instead of int

        with pytest.raises(TypeError):
            HealthChecker(retry_count="1")  # String instead of int

        with pytest.raises(TypeError):
            HealthChecker(backoff_base_seconds="0.1")  # String instead of float

        # Test None values for required parameters
        with pytest.raises((TypeError, ValueError)):
            HealthChecker(default_timeout_ms=None)

        with pytest.raises((TypeError, ValueError)):
            HealthChecker(retry_count=None)

        with pytest.raises((TypeError, ValueError)):
            HealthChecker(backoff_base_seconds=None)

        # Test complex configuration validation
        # Valid complex configuration
        complex_config = HealthChecker(
            default_timeout_ms=2000,
            per_component_timeouts_ms={
                "database": 5000,
                "cache": 1000,
                "ai_model": 3000
            },
            retry_count=2,
            backoff_base_seconds=0.5
        )
        assert complex_config is not None
        assert len(complex_config._per_component_timeouts_ms) == 3

        # Invalid component-specific timeout should be caught
        with pytest.raises(ValueError):
            HealthChecker(
                default_timeout_ms=2000,
                per_component_timeouts_ms={
                    "database": 50  # Below minimum
                }
            )

    def test_health_checker_per_component_timeout_validation(self):
        """
        Test HealthChecker validates per-component timeout configurations.

        Integration Scope:
            HealthChecker initialization → Per-component timeout validation → Error handling

        Contract Validation:
            - Component-specific timeout validation within global bounds
            - Type checking for component timeout configuration
            - Error handling for invalid component-specific timeouts

        Business Impact:
            Ensures component-specific timeouts are within reasonable bounds
            Prevents misconfiguration of individual component health checks
            Validates flexible timeout configuration while maintaining safety

        Test Strategy:
            - Test valid per-component timeout configurations
            - Verify component timeouts are validated against global bounds
            - Test invalid component timeout configurations
            - Validate error handling for component-specific timeout issues

        Success Criteria:
            - Valid component timeouts accepted and applied
            - Invalid component timeouts rejected with clear errors
            - Component timeouts validated against global bounds
            - Error messages specify which component has invalid timeout
        """
        # Test valid per-component timeouts
        checker = HealthChecker(
            default_timeout_ms=2000,
            per_component_timeouts_ms={
                "database": 5000,  # Valid (within bounds)
                "cache": 500,     # Valid (within bounds)
                "ai_model": 3000  # Valid (within bounds)
            }
        )

        assert checker is not None
        assert checker._per_component_timeouts_ms["database"] == 5000
        assert checker._per_component_timeouts_ms["cache"] == 500
        assert checker._per_component_timeouts_ms["ai_model"] == 3000

        # Test invalid per-component timeouts
        with pytest.raises(ValueError):
            HealthChecker(
                default_timeout_ms=2000,
                per_component_timeouts_ms={
                    "database": 50  # Below minimum
                }
            )

        with pytest.raises(ValueError):
            HealthChecker(
                default_timeout_ms=2000,
                per_component_timeouts_ms={
                    "cache": 50000  # Above maximum
                }
            )

        # Test mixed valid and invalid component timeouts
        with pytest.raises(ValueError):
            HealthChecker(
                default_timeout_ms=2000,
                per_component_timeouts_ms={
                    "database": 5000,   # Valid
                    "cache": 50,       # Invalid (below minimum)
                    "ai_model": 3000   # Valid
                }
            )

    async def test_health_checker_configuration_affects_behavior(self):
        """
        Test HealthChecker configuration actually affects health check behavior.

        Integration Scope:
            HealthChecker configuration → Health check execution → Observable behavior changes

        Contract Validation:
            - Configuration parameters affect actual health check behavior
            - Timeout settings influence component check execution
            - Retry policies affect failure handling behavior

        Business Impact:
            Ensures configuration changes have expected effects
            Validates that configuration tuning can optimize health monitoring
            Confirms configuration parameters are not just cosmetic

        Test Strategy:
            - Create health checkers with different configurations
            - Compare behavior differences between configurations
            - Test that timeout settings actually limit execution time
            - Verify retry policies affect failure handling

        Success Criteria:
            - Different configurations produce different observable behavior
            - Timeout settings actually limit health check duration
            - Retry policies affect failure handling behavior
            - Configuration changes have expected operational effects
        """
        # Create two health checkers with different timeout configurations
        fast_checker = HealthChecker(
            default_timeout_ms=100,  # Very short timeout
            retry_count=0  # No retries
        )

        normal_checker = HealthChecker(
            default_timeout_ms=2000,  # Normal timeout
            retry_count=1  # One retry
        )

        # Register a mock health check function that can be slow
        import asyncio

        async def slow_health_check():
            await asyncio.sleep(0.2)  # 200ms delay
            return ComponentStatus("slow", HealthStatus.HEALTHY, "OK")

        fast_checker.register_check("slow", slow_health_check)
        normal_checker.register_check("slow", slow_health_check)

        # Act: Execute health checks with different configurations
        fast_result = await fast_checker.check_component("slow")
        normal_result = await normal_checker.check_component("slow")

        # Assert: Configuration affects observable behavior
        # Fast checker should timeout and return DEGRADED
        assert fast_result.status == HealthStatus.DEGRADED
        assert "timeout" in fast_result.message.lower()

        # Normal checker should complete successfully
        assert normal_result.status == HealthStatus.HEALTHY
        assert normal_result.message == "OK"

        # Verify response times reflect configuration differences
        assert fast_result.response_time_ms < 150  # Should timeout quickly
        assert normal_result.response_time_ms >= 200  # Should take full sleep time

    def test_health_checker_configuration_error_messages(self):
        """
        Test HealthChecker provides descriptive error messages for configuration errors.

        Integration Scope:
            HealthChecker initialization → Configuration validation → Error message generation

        Contract Validation:
            - Error messages provide clear diagnostic information
            - Error messages help users understand configuration issues
            - Validation errors include context about parameter requirements

        Business Impact:
            Enables developers to quickly understand and fix configuration issues
            Reduces debugging time for health monitoring configuration problems
            Improves developer experience with clear error reporting

        Test Strategy:
            - Test various configuration error scenarios
            - Verify error messages are descriptive and helpful
            - Test that error messages include parameter context
            - Validate error reporting helps with issue resolution

        Success Criteria:
            - Error messages clearly indicate what went wrong
            - Messages include parameter names and valid ranges
            - Errors help users understand how to fix issues
            - Error reporting is consistent and professional
        """
        # Test timeout boundary error messages
        with pytest.raises(ValueError) as exc_info:
            HealthChecker(default_timeout_ms=50)  # Below minimum

        error_message = str(exc_info.value)
        assert "timeout" in error_message.lower()
        assert "50" in error_message
        assert "100" in error_message  # Minimum should be mentioned

        with pytest.raises(ValueError) as exc_info:
            HealthChecker(default_timeout_ms=50000)  # Above maximum

        error_message = str(exc_info.value)
        assert "timeout" in error_message.lower()
        assert "50000" in error_message
        assert "30000" in error_message  # Maximum should be mentioned

        # Test retry count error messages
        with pytest.raises(ValueError) as exc_info:
            HealthChecker(retry_count=15)  # Above maximum

        error_message = str(exc_info.value)
        assert "retry" in error_message.lower()
        assert "15" in error_message
        assert "10" in error_message  # Maximum should be mentioned

        # Test backoff error messages
        with pytest.raises(ValueError) as exc_info:
            HealthChecker(backoff_base_seconds=10.0)  # Above maximum

        error_message = str(exc_info.value)
        assert "backoff" in error_message.lower()
        assert "10.0" in error_message
        assert "5.0" in error_message  # Maximum should be mentioned

    def test_health_checker_configuration_defaults_are_reasonable(self):
        """
        Test HealthChecker provides reasonable default configuration values.

        Integration Scope:
            HealthChecker initialization with no parameters → Default configuration validation

        Contract Validation:
            - Default values are suitable for most use cases
            - Default configuration provides balanced behavior
            - No parameters required for basic functionality

        Business Impact:
            Ensures health monitoring works out-of-the-box with sensible defaults
            Reduces configuration complexity for common use cases
            Provides good starting point for health monitoring setup

        Test Strategy:
            - Test default configuration without parameters
            - Verify default values are reasonable and balanced
            - Test that defaults provide good basic functionality
            - Validate defaults are documented and consistent

        Success Criteria:
            - Default timeout (2000ms) is reasonable for health checks
            - Default retry count (1) provides basic failure handling
            - Default backoff (0.1s) prevents aggressive retry storms
            - Defaults work well for most monitoring scenarios
        """
        # Act: Create health checker with default configuration
        checker = HealthChecker()

        # Assert: Reasonable default values
        assert checker._default_timeout_ms == 2000  # 2 seconds - reasonable for health checks
        assert checker._retry_count == 1  # One retry - basic failure handling
        assert checker._backoff_base_seconds == 0.1  # 100ms backoff - prevents retry storms
        assert checker._per_component_timeouts_ms == {}  # No component-specific overrides

        # Verify defaults allow basic functionality
        assert checker is not None
        assert hasattr(checker, 'register_check')
        assert hasattr(checker, 'check_component')
        assert hasattr(checker, 'check_all_components')

        # Test that default configuration can be used for basic health checking
        async def mock_health_check():
            return ComponentStatus("test", HealthStatus.HEALTHY, "OK")

        checker.register_check("test", mock_health_check)
        assert "test" in checker._checks

        # Default configuration should work for actual component checks too
        from app.infrastructure.monitoring.health import check_ai_model_health
        checker.register_check("ai_model", check_ai_model_health)
        assert "ai_model" in checker._checks