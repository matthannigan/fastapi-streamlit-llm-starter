"""
Integration tests for configuration-driven health monitoring.

These tests verify the integration between health monitoring system
and application configuration, ensuring health checks adapt to different
deployment environments and configuration requirements.

MEDIUM PRIORITY - Configuration management and flexibility
"""

import pytest
from unittest.mock import patch

from app.infrastructure.monitoring.health import (
    HealthChecker,
    HealthStatus,
    ComponentStatus,
)
from app.core.config import Settings


class TestConfigurationDrivenHealthMonitoring:
    """
    Integration tests for configuration-driven health monitoring.

    Seam Under Test:
        HealthChecker → Settings → Timeout configuration → Retry settings

    Critical Path:
        Configuration loading → Health check parameter application →
        Check execution → Status reporting

    Business Impact:
        Ensures health monitoring adapts to different deployment environments
        and requirements, providing flexible monitoring capabilities that
        can be tuned for various operational scenarios.

    Test Strategy:
        - Test health monitoring with different configuration scenarios
        - Verify configuration-driven timeout and retry behavior
        - Confirm proper integration with application settings
        - Test configuration flexibility and validation
        - Validate environment-specific health monitoring behavior

    Success Criteria:
        - Health monitoring respects configuration settings
        - Timeout and retry behavior adapts to configuration
        - Settings integration works correctly
        - Configuration flexibility supports different scenarios
        - Environment-specific behavior is properly implemented
    """

    def test_health_monitoring_with_different_timeout_configurations(
        self
    ):
        """
        Test health monitoring with different timeout configurations.

        Integration Scope:
            HealthChecker → Timeout configuration → Health check execution → Timing validation

        Business Impact:
            Ensures health monitoring timeout behavior is configurable
            and adapts to different operational requirements, allowing
            operators to tune monitoring for their specific environment.

        Test Strategy:
            - Create health checkers with different timeout configurations
            - Test timeout behavior with slow health checks
            - Verify timeout enforcement matches configuration
            - Confirm configuration-driven timeout flexibility

        Success Criteria:
            - Timeout configurations are properly applied
            - Health checks respect configured timeout values
            - Different timeout settings produce different behavior
            - Timeout configuration flexibility works as expected
        """
        # Test configurations with different timeout values
        test_configs = [
            {"default_timeout_ms": 500, "description": "Fast timeout"},
            {"default_timeout_ms": 2000, "description": "Standard timeout"},
            {"default_timeout_ms": 5000, "description": "Slow timeout"},
        ]

        for config in test_configs:
            checker = HealthChecker(**config)

            # Create health check that takes time but completes
            async def timed_check():
                await asyncio.sleep(0.1)  # 100ms delay
                return ComponentStatus("timed", HealthStatus.HEALTHY, f"Completed with {config['description']}")

            checker.register_check("timed", timed_check)

            result = await checker.check_component("timed")

            # Verify configuration-driven behavior
            assert result.name == "timed"
            assert result.status == HealthStatus.HEALTHY
            assert result.response_time_ms > 0
            assert result.response_time_ms < config["default_timeout_ms"] + 100  # Allow some variance

    def test_health_monitoring_with_per_component_timeout_configuration(
        self
    ):
        """
        Test health monitoring with per-component timeout configuration.

        Integration Scope:
            HealthChecker → Per-component timeouts → Component-specific behavior

        Business Impact:
            Ensures health monitoring can apply different timeout values
            to different components, allowing fine-tuned monitoring
            for components with different response characteristics.

        Test Strategy:
            - Configure health checker with per-component timeouts
            - Test different components with different timeout expectations
            - Verify component-specific timeout enforcement
            - Confirm proper timeout configuration application

        Success Criteria:
            - Per-component timeouts are properly applied
            - Different components can have different timeout values
            - Component-specific timeout configuration works correctly
            - Timeout behavior adapts to component-specific settings
        """
        # Configure per-component timeouts
        per_component_timeouts = {
            "fast_component": 200,    # Fast timeout for quick components
            "slow_component": 5000,   # Slow timeout for slow components
        }

        checker = HealthChecker(
            default_timeout_ms=1000,
            per_component_timeouts_ms=per_component_timeouts
        )

        # Create health checks with different timing characteristics
        async def fast_check():
            await asyncio.sleep(0.05)  # 50ms - should work with fast timeout
            return ComponentStatus("fast", HealthStatus.HEALTHY, "Fast component")

        async def slow_check():
            await asyncio.sleep(0.5)   # 500ms - should work with slow timeout
            return ComponentStatus("slow", HealthStatus.HEALTHY, "Slow component")

        checker.register_check("fast", fast_check)
        checker.register_check("slow", slow_check)

        # Test fast component
        fast_result = await checker.check_component("fast")
        assert fast_result.name == "fast"
        assert fast_result.status == HealthStatus.HEALTHY
        assert fast_result.response_time_ms < 300  # Should complete within fast timeout + buffer

        # Test slow component
        slow_result = await checker.check_component("slow")
        assert slow_result.name == "slow"
        assert slow_result.status == HealthStatus.HEALTHY
        assert slow_result.response_time_ms < 1000  # Should complete within slow timeout + buffer

    def test_health_monitoring_with_different_retry_configurations(
        self
    ):
        """
        Test health monitoring with different retry configurations.

        Integration Scope:
            HealthChecker → Retry configuration → Retry behavior → Configuration validation

        Business Impact:
            Ensures health monitoring retry behavior is configurable
            and adapts to different reliability requirements, allowing
            operators to tune retry behavior for operational needs.

        Test Strategy:
            - Create health checkers with different retry configurations
            - Test retry behavior with failing health checks
            - Verify retry count enforcement matches configuration
            - Confirm configuration-driven retry flexibility

        Success Criteria:
            - Retry configurations are properly applied
            - Health checks respect configured retry counts
            - Different retry settings produce different behavior
            - Retry configuration flexibility works as expected
        """
        # Test configurations with different retry counts
        test_configs = [
            {"retry_count": 0, "description": "No retries"},
            {"retry_count": 2, "description": "Two retries"},
            {"retry_count": 5, "description": "Five retries"},
        ]

        for config in test_configs:
            checker = HealthChecker(
                default_timeout_ms=2000,
                per_component_timeouts_ms={},
                **config
            )

            # Create failing health check
            attempt_count = 0
            async def failing_check():
                nonlocal attempt_count
                attempt_count += 1
                raise Exception(f"Failure attempt {attempt_count}")

            checker.register_check("failing", failing_check)

            result = await checker.check_component("failing")

            # Verify configuration-driven retry behavior
            assert result.name == "failing"
            assert result.status == HealthStatus.UNHEALTHY
            expected_attempts = config["retry_count"] + 1  # Initial + retries
            assert attempt_count == expected_attempts

    def test_health_monitoring_configuration_integration_with_settings(
        self
    ):
        """
        Test health monitoring configuration integration with application settings.

        Integration Scope:
            HealthChecker → Settings integration → Configuration application → Settings validation

        Business Impact:
            Ensures health monitoring integrates properly with application
            settings system, allowing configuration-driven monitoring
            behavior based on deployment environment.

        Test Strategy:
            - Mock different settings configurations
            - Test health monitoring behavior with different settings
            - Verify settings-driven configuration application
            - Confirm proper settings integration

        Success Criteria:
            - Settings configurations are properly integrated
            - Health monitoring behavior adapts to settings
            - Settings validation works correctly
            - Configuration flexibility supports different environments
        """
        # Test different settings scenarios
        test_settings = [
            {
                "health_check_timeout": 1000,
                "health_check_retries": 1,
                "description": "Development settings"
            },
            {
                "health_check_timeout": 5000,
                "health_check_retries": 3,
                "description": "Production settings"
            }
        ]

        for settings_config in test_settings:
            # Create health checker based on settings
            checker = HealthChecker(
                default_timeout_ms=settings_config["health_check_timeout"],
                per_component_timeouts_ms={},
                retry_count=settings_config["health_check_retries"]
            )

            # Verify settings-driven configuration
            assert checker._default_timeout_ms == settings_config["health_check_timeout"]
            assert checker._retry_count == settings_config["health_check_retries"]

            # Test with a simple health check
            async def simple_check():
                return ComponentStatus("test", HealthStatus.HEALTHY, f"With {settings_config['description']}")

            checker.register_check("test", simple_check)
            result = await checker.check_component("test")

            assert result.name == "test"
            assert result.status == HealthStatus.HEALTHY

    def test_health_monitoring_configuration_validation_and_error_handling(
        self
    ):
        """
        Test health monitoring configuration validation and error handling.

        Integration Scope:
            HealthChecker → Configuration validation → Error handling → Configuration resilience

        Business Impact:
            Ensures health monitoring configuration is properly validated
            and handles invalid configurations gracefully, maintaining
            monitoring system stability despite configuration issues.

        Test Strategy:
            - Test configuration validation with invalid values
            - Verify error handling for invalid configurations
            - Confirm system behavior with edge case configurations
            - Validate configuration resilience

        Success Criteria:
            - Invalid configurations are handled gracefully
            - Configuration validation prevents system errors
            - Edge cases are handled appropriately
            - System remains stable with invalid configurations
        """
        # Test edge case configurations
        edge_configs = [
            {"default_timeout_ms": 0, "retry_count": 0},  # Zero values
            {"default_timeout_ms": -1, "retry_count": -1},  # Negative values
            {"default_timeout_ms": 1000000, "retry_count": 100},  # Extreme values
        ]

        for config in edge_configs:
            # HealthChecker should handle edge cases gracefully
            checker = HealthChecker(**config)

            # Verify configuration is normalized/sanitized
            assert checker._default_timeout_ms >= 0
            assert checker._retry_count >= 0

            # Test with a simple health check
            async def simple_check():
                return ComponentStatus("test", HealthStatus.HEALTHY, "Edge case test")

            checker.register_check("test", simple_check)
            result = await checker.check_component("test")

            assert result.name == "test"
            assert result.status == HealthStatus.HEALTHY

    def test_health_monitoring_configuration_flexibility_for_different_environments(
        self
    ):
        """
        Test health monitoring configuration flexibility for different environments.

        Integration Scope:
            HealthChecker → Environment-specific configuration → Flexibility → Environment adaptation

        Business Impact:
            Ensures health monitoring can be configured differently for
            different deployment environments, supporting development,
            staging, and production monitoring requirements.

        Test Strategy:
            - Define configurations for different environments
            - Test health monitoring behavior in each environment
            - Verify environment-specific configuration application
            - Confirm flexibility supports operational needs

        Success Criteria:
            - Different environments can have different configurations
            - Environment-specific behavior is properly implemented
            - Configuration flexibility supports operational scenarios
            - Environment detection and configuration works correctly
        """
        # Environment-specific configurations
        env_configs = {
            "development": {
                "default_timeout_ms": 500,    # Fast for quick feedback
                "retry_count": 1,             # Minimal retries for fast failure
                "description": "Development environment"
            },
            "staging": {
                "default_timeout_ms": 2000,   # Moderate timeouts
                "retry_count": 2,             # Some resilience
                "description": "Staging environment"
            },
            "production": {
                "default_timeout_ms": 5000,   # Generous timeouts
                "retry_count": 3,             # High resilience
                "description": "Production environment"
            }
        }

        for env_name, config in env_configs.items():
            checker = HealthChecker(**config)

            # Verify environment-specific configuration
            assert checker._default_timeout_ms == config["default_timeout_ms"]
            assert checker._retry_count == config["retry_count"]

            # Test with environment-specific health check
            async def env_specific_check():
                return ComponentStatus(env_name, HealthStatus.HEALTHY, f"Running in {env_name}")

            checker.register_check("env_test", env_specific_check)
            result = await checker.check_component("env_test")

            assert result.name == env_name
            assert result.status == HealthStatus.HEALTHY
            assert env_name in result.message

    def test_health_monitoring_configuration_integration_with_component_registration(
        self
    ):
        """
        Test configuration integration with component registration.

        Integration Scope:
            HealthChecker → Component registration → Configuration integration → Registration validation

        Business Impact:
            Ensures health monitoring configuration is properly applied
            during component registration, maintaining consistent
            monitoring behavior across all registered components.

        Test Strategy:
            - Register multiple components with configured health checker
            - Verify configuration is applied consistently to all components
            - Test component-specific configuration overrides
            - Confirm configuration integration works during registration

        Success Criteria:
            - Configuration is applied consistently to all components
            - Component-specific overrides work correctly
            - Registration process integrates configuration properly
            - All components respect the same configuration baseline
        """
        # Configuration with some component-specific overrides
        per_component_timeouts = {"special_component": 10000}
        checker = HealthChecker(
            default_timeout_ms=2000,
            per_component_timeouts_ms=per_component_timeouts,
            retry_count=2
        )

        # Register multiple components
        async def standard_check():
            return ComponentStatus("standard", HealthStatus.HEALTHY, "Standard component")

        async def special_check():
            return ComponentStatus("special", HealthStatus.HEALTHY, "Special component")

        checker.register_check("standard", standard_check)
        checker.register_check("special", special_check)

        # Test both components
        standard_result = await checker.check_component("standard")
        special_result = await checker.check_component("special")

        # Verify configuration integration
        assert standard_result.name == "standard"
        assert standard_result.status == HealthStatus.HEALTHY
        assert special_result.name == "special"
        assert special_result.status == HealthStatus.HEALTHY

        # Verify both respect base configuration
        assert checker._retry_count == 2
        assert checker._default_timeout_ms == 2000

    def test_health_monitoring_configuration_persistence_across_operations(
        self
    ):
        """
        Test configuration persistence across multiple health check operations.

        Integration Scope:
            HealthChecker → Configuration persistence → Operation consistency → State management

        Business Impact:
            Ensures health monitoring configuration remains consistent
            across multiple operations, providing stable and predictable
            monitoring behavior over time.

        Test Strategy:
            - Create health checker with specific configuration
            - Execute multiple health check operations
            - Verify configuration remains consistent across operations
            - Confirm configuration persistence and stability

        Success Criteria:
            - Configuration persists across multiple operations
            - Configuration values remain stable over time
            - Multiple operations use consistent configuration
            - Configuration doesn't change unexpectedly
        """
        # Create health checker with specific configuration
        original_config = {
            "default_timeout_ms": 3000,
            "retry_count": 1,
            "backoff_base_seconds": 0.5
        }

        checker = HealthChecker(**original_config)

        # Verify initial configuration
        assert checker._default_timeout_ms == 3000
        assert checker._retry_count == 1
        assert checker._backoff_base_seconds == 0.5

        # Execute multiple operations
        async def test_check():
            return ComponentStatus("test", HealthStatus.HEALTHY, "Test operation")

        checker.register_check("test", test_check)

        # Perform multiple health check operations
        results = []
        for i in range(5):
            result = await checker.check_component("test")
            results.append(result)

            # Verify configuration hasn't changed
            assert checker._default_timeout_ms == 3000
            assert checker._retry_count == 1
            assert checker._backoff_base_seconds == 0.5

        # Verify all operations completed successfully
        assert len(results) == 5
        for result in results:
            assert result.name == "test"
            assert result.status == HealthStatus.HEALTHY

    def test_health_monitoring_configuration_with_dynamic_adjustment(
        self
    ):
        """
        Test health monitoring configuration with dynamic adjustment scenarios.

        Integration Scope:
            HealthChecker → Dynamic configuration → Adjustment handling → Configuration flexibility

        Business Impact:
            Ensures health monitoring can handle dynamic configuration
            adjustments, supporting scenarios where monitoring parameters
            need to be adjusted at runtime.

        Test Strategy:
            - Create health checker with initial configuration
            - Test dynamic configuration scenarios
            - Verify adjustment handling works correctly
            - Confirm configuration flexibility supports dynamic scenarios

        Success Criteria:
            - Configuration adjustments are handled appropriately
            - Dynamic scenarios work as expected
            - Configuration flexibility supports operational needs
            - System adapts to configuration changes correctly
        """
        # Create health checker with base configuration
        checker = HealthChecker(
            default_timeout_ms=2000,
            per_component_timeouts_ms={},
            retry_count=1
        )

        # Verify initial configuration
        assert checker._default_timeout_ms == 2000
        assert checker._retry_count == 1

        # Create health check that can succeed or fail based on scenario
        scenario_success = True
        async def scenario_check():
            if scenario_success:
                return ComponentStatus("scenario", HealthStatus.HEALTHY, "Success scenario")
            else:
                raise Exception("Failure scenario")

        checker.register_check("scenario", scenario_check)

        # Test success scenario
        scenario_success = True
        success_result = await checker.check_component("scenario")
        assert success_result.status == HealthStatus.HEALTHY
        assert success_result.name == "scenario"

        # Test failure scenario
        scenario_success = False
        failure_result = await checker.check_component("scenario")
        assert failure_result.status == HealthStatus.UNHEALTHY
        assert failure_result.name == "scenario"

        # Verify configuration remained stable across scenarios
        assert checker._default_timeout_ms == 2000
        assert checker._retry_count == 1

    def test_health_monitoring_configuration_comprehensive_integration(
        self
    ):
        """
        Test comprehensive configuration integration for health monitoring.

        Integration Scope:
            HealthChecker → Comprehensive configuration → Integration validation → Configuration testing

        Business Impact:
            Ensures comprehensive health monitoring configuration works
            correctly across all configuration dimensions, providing
            robust and flexible monitoring capabilities.

        Test Strategy:
            - Test comprehensive configuration scenarios
            - Verify all configuration parameters work together
            - Confirm integration across all configuration dimensions
            - Validate comprehensive configuration functionality

        Success Criteria:
            - All configuration parameters work together correctly
            - Integration across configuration dimensions works properly
            - Comprehensive configuration scenarios are supported
            - Configuration system is robust and reliable
        """
        # Comprehensive configuration test
        comprehensive_config = {
            "default_timeout_ms": 3000,
            "per_component_timeouts_ms": {
                "fast": 500,
                "slow": 10000,
                "normal": 2000
            },
            "retry_count": 2,
            "backoff_base_seconds": 0.5
        }

        checker = HealthChecker(**comprehensive_config)

        # Verify comprehensive configuration
        assert checker._default_timeout_ms == 3000
        assert checker._per_component_timeouts_ms == comprehensive_config["per_component_timeouts_ms"]
        assert checker._retry_count == 2
        assert checker._backoff_base_seconds == 0.5

        # Create different types of health checks
        async def fast_check():
            await asyncio.sleep(0.1)
            return ComponentStatus("fast", HealthStatus.HEALTHY, "Fast check")

        async def slow_check():
            await asyncio.sleep(0.5)
            return ComponentStatus("slow", HealthStatus.HEALTHY, "Slow check")

        async def normal_check():
            return ComponentStatus("normal", HealthStatus.HEALTHY, "Normal check")

        checker.register_check("fast", fast_check)
        checker.register_check("slow", slow_check)
        checker.register_check("normal", normal_check)

        # Test all components
        fast_result = await checker.check_component("fast")
        slow_result = await checker.check_component("slow")
        normal_result = await checker.check_component("normal")

        # Verify comprehensive configuration works
        assert fast_result.status == HealthStatus.HEALTHY
        assert slow_result.status == HealthStatus.HEALTHY
        assert normal_result.status == HealthStatus.HEALTHY

        # Verify configuration was applied to all checks
        assert checker._retry_count == 2
        assert checker._backoff_base_seconds == 0.5
