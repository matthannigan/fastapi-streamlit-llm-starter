"""
Integration tests for FastAPI dependency injection with health monitoring.

These tests verify the integration between FastAPI's dependency injection system
and the health monitoring infrastructure, ensuring proper service lifecycle
management and singleton behavior.

HIGH PRIORITY - Service lifecycle and dependency management
"""

import pytest
from unittest.mock import patch
from fastapi.testclient import TestClient

from app.main import app
from app.infrastructure.monitoring.health import HealthChecker, HealthStatus
from app.dependencies import get_health_checker


class TestFastAPIDependencyInjectionIntegration:
    """
    Integration tests for FastAPI dependency injection with health monitoring.

    Seam Under Test:
        get_health_checker() → HealthChecker → Component registration → Service availability

    Critical Path:
        Dependency injection resolution → Health checker initialization →
        Component registration → Health validation

    Business Impact:
        Ensures health monitoring service is properly integrated into
        FastAPI application lifecycle and provides consistent monitoring
        capabilities across all health check requests.

    Test Strategy:
        - Test health checker singleton behavior through dependency injection
        - Verify component registration works correctly
        - Confirm proper service lifecycle management
        - Test dependency injection with different configurations
        - Validate health checker availability throughout application

    Success Criteria:
        - Health checker provides singleton instance through dependency injection
        - Component registration works correctly during initialization
        - Service lifecycle is properly managed by FastAPI
        - Health checks are available throughout application lifecycle
        - Response times are reasonable for dependency resolution
    """

    def test_health_checker_singleton_behavior_through_dependency_injection(self):
        """
        Test that health checker provides singleton instance through FastAPI DI.

        Integration Scope:
            FastAPI DI → get_health_checker() → HealthChecker singleton

        Business Impact:
            Ensures health monitoring service maintains consistent state
            and configuration across all requests, providing reliable
            monitoring capabilities.

        Test Strategy:
            - Resolve health checker multiple times through DI
            - Verify same instance is returned each time
            - Confirm singleton pattern works correctly
            - Validate instance maintains state across resolutions

        Success Criteria:
            - Same HealthChecker instance returned on multiple resolutions
            - Singleton pattern maintains instance identity
            - Instance state is preserved across dependency resolutions
            - No memory leaks or instance duplication occurs
        """
        # Resolve health checker multiple times
        checker1 = get_health_checker()
        checker2 = get_health_checker()
        checker3 = get_health_checker()

        # Verify singleton behavior
        assert checker1 is checker2
        assert checker2 is checker3
        assert checker1 is checker3

        # Verify it's actually a HealthChecker instance
        assert isinstance(checker1, HealthChecker)
        assert isinstance(checker2, HealthChecker)
        assert isinstance(checker3, HealthChecker)

    def test_health_checker_component_registration_through_dependency_injection(
        self
    ):
        """
        Test that health checker registers components correctly through DI.

        Integration Scope:
            FastAPI DI → get_health_checker() → Component registration

        Business Impact:
            Ensures health monitoring service has all required components
            registered and available for monitoring, providing comprehensive
            system observability.

        Test Strategy:
            - Resolve health checker through dependency injection
            - Verify standard components are registered
            - Confirm health checks are available
            - Validate registration process completes successfully

        Success Criteria:
            - Standard health check components are registered
            - Health check functions are available
            - Registration process completes without errors
            - All expected monitoring components are present
        """
        checker = get_health_checker()

        # Verify standard components are registered
        registered_checks = list(checker._checks.keys())
        expected_checks = ["ai_model", "cache", "resilience"]

        for expected_check in expected_checks:
            assert expected_check in registered_checks, f"Missing expected health check: {expected_check}"

        # Verify health check functions are callable
        for check_name in expected_checks:
            assert check_name in checker._checks
            assert callable(checker._checks[check_name])

    def test_health_checker_functionality_through_dependency_injection(self):
        """
        Test that health checker works correctly when resolved through DI.

        Integration Scope:
            FastAPI DI → get_health_checker() → Health validation

        Business Impact:
            Ensures health monitoring service functions correctly when
            used through FastAPI's dependency injection system, maintaining
            reliable monitoring capabilities.

        Test Strategy:
            - Resolve health checker through dependency injection
            - Execute individual component health checks
            - Verify health check results are valid
            - Confirm all components can be checked

        Success Criteria:
            - Individual component health checks execute successfully
            - Health check results contain expected information
            - All registered components respond to health checks
            - Response times are reasonable for monitoring
        """
        checker = get_health_checker()

        # Test individual component health checks
        for component_name in ["ai_model", "cache", "resilience"]:
            assert component_name in checker._checks

            # Execute health check for this component
            result = await checker.check_component(component_name)

            # Verify health check result structure
            assert result.name == component_name
            assert isinstance(result.status, HealthStatus)
            assert isinstance(result.message, str)
            assert isinstance(result.response_time_ms, (int, float))
            assert result.response_time_ms > 0

    def test_health_checker_system_health_check_through_dependency_injection(self):
        """
        Test system-wide health check through dependency injection.

        Integration Scope:
            FastAPI DI → get_health_checker() → System health validation

        Business Impact:
            Ensures comprehensive system health monitoring works correctly
            through FastAPI's dependency injection, providing complete
            system observability.

        Test Strategy:
            - Resolve health checker through dependency injection
            - Execute comprehensive system health check
            - Verify system health status is valid
            - Confirm all components contribute to system health

        Success Criteria:
            - System health check executes successfully
            - All components are included in system health
            - Overall health status reflects component states
            - System health provides comprehensive monitoring data
        """
        checker = get_health_checker()

        # Execute comprehensive system health check
        system_health = await checker.check_all_components()

        # Verify system health result structure
        assert isinstance(system_health.overall_status, HealthStatus)
        assert isinstance(system_health.components, list)
        assert isinstance(system_health.timestamp, float)
        assert len(system_health.components) > 0

        # Verify all registered components are checked
        checked_components = [comp.name for comp in system_health.components]
        registered_components = list(checker._checks.keys())

        for registered_component in registered_components:
            assert registered_component in checked_components, f"Component {registered_component} not checked"

        # Verify overall status logic
        component_statuses = [comp.status for comp in system_health.components]
        if any(status == HealthStatus.UNHEALTHY for status in component_statuses):
            assert system_health.overall_status == HealthStatus.UNHEALTHY
        elif any(status == HealthStatus.DEGRADED for status in component_statuses):
            assert system_health.overall_status == HealthStatus.DEGRADED
        else:
            assert system_health.overall_status == HealthStatus.HEALTHY

    def test_health_checker_dependency_injection_performance_characteristics(self):
        """
        Test health checker dependency injection performance characteristics.

        Integration Scope:
            FastAPI DI → get_health_checker() → Performance monitoring

        Business Impact:
            Ensures health checker dependency injection doesn't become
            a performance bottleneck when used frequently, maintaining
            fast API response times.

        Test Strategy:
            - Resolve health checker multiple times through DI
            - Measure dependency resolution time
            - Verify consistent performance across resolutions
            - Confirm singleton caching works efficiently

        Success Criteria:
            - Dependency resolution is fast and consistent
            - Singleton caching provides performance benefits
            - No performance degradation with repeated resolutions
            - Response times remain suitable for web application use
        """
        import time

        # Test multiple dependency resolutions
        resolution_times = []
        instances = []

        for i in range(10):
            start_time = time.time()
            checker = get_health_checker()
            end_time = time.time()

            resolution_time = (end_time - start_time) * 1000  # Convert to milliseconds
            resolution_times.append(resolution_time)
            instances.append(checker)

        # Verify performance characteristics
        avg_resolution_time = sum(resolution_times) / len(resolution_times)
        max_resolution_time = max(resolution_times)
        min_resolution_time = min(resolution_times)

        # First resolution should be slower (actual creation)
        # Subsequent resolutions should be very fast (cache lookup)
        assert max_resolution_time < 100  # All resolutions under 100ms
        assert avg_resolution_time < 50   # Average under 50ms

        # Verify singleton behavior
        assert all(instance is instances[0] for instance in instances)

    def test_health_checker_dependency_injection_with_custom_configuration(
        self
    ):
        """
        Test health checker with custom configuration through DI.

        Integration Scope:
            FastAPI DI → get_health_checker() → Custom HealthChecker configuration

        Business Impact:
            Ensures health checker can be configured with custom parameters
            while maintaining dependency injection compatibility and
            providing flexible monitoring capabilities.

        Test Strategy:
            - Create custom health checker configuration
            - Override dependency injection with custom checker
            - Verify custom configuration is used correctly
            - Confirm dependency injection still works with overrides

        Success Criteria:
            - Custom health checker configuration is respected
            - Dependency injection works with custom instances
            - Custom timeouts and retry settings are applied
            - Override mechanism doesn't break existing functionality
        """
        # Create custom configured health checker
        custom_checker = HealthChecker(
            default_timeout_ms=5000,  # Custom timeout
            per_component_timeouts_ms={"slow_component": 10000},
            retry_count=3,  # Custom retry count
            backoff_base_seconds=0.5,  # Custom backoff
        )

        # Override the dependency injection
        original_get_health_checker = get_health_checker
        with patch('app.dependencies.get_health_checker', lambda: custom_checker):
            # Test that our custom checker is returned
            resolved_checker = get_health_checker()
            assert resolved_checker is custom_checker

            # Verify custom configuration is applied
            assert resolved_checker._default_timeout_ms == 5000
            assert resolved_checker._retry_count == 3
            assert resolved_checker._backoff_base_seconds == 0.5
            assert resolved_checker._per_component_timeouts_ms["slow_component"] == 10000

    def test_health_checker_dependency_injection_lifecycle_integration(self):
        """
        Test health checker integration with FastAPI application lifecycle.

        Integration Scope:
            FastAPI app → Dependency injection → Health checker lifecycle

        Business Impact:
            Ensures health monitoring service integrates properly with
            FastAPI application lifecycle, providing reliable monitoring
            from application startup to shutdown.

        Test Strategy:
            - Create FastAPI app with health monitoring dependency
            - Test dependency resolution during application lifecycle
            - Verify health checker availability during requests
            - Confirm proper cleanup and lifecycle management

        Success Criteria:
            - Health checker is available during application lifecycle
            - Dependency injection works throughout request lifecycle
            - Singleton instance persists across requests
            - No lifecycle conflicts or dependency issues
        """
        from fastapi import FastAPI, Depends
        from fastapi.testclient import TestClient

        # Create test app with health checker dependency
        test_app = FastAPI()

        @test_app.get("/health-check")
        async def test_endpoint(checker: HealthChecker = Depends(get_health_checker)):
            """Test endpoint that uses health checker dependency."""
            return {
                "checker_id": id(checker),
                "registered_checks": list(checker._checks.keys()),
                "status": "ok"
            }

        client = TestClient(test_app)

        # Test multiple requests to verify lifecycle consistency
        responses = []
        for i in range(5):
            response = client.get("/health-check")
            assert response.status_code == 200
            responses.append(response.json())

        # Verify consistent behavior across requests
        assert len(responses) == 5
        first_checker_id = responses[0]["checker_id"]

        for response in responses[1:]:
            assert response["checker_id"] == first_checker_id  # Same instance
            assert response["registered_checks"] == responses[0]["registered_checks"]
            assert response["status"] == "ok"

    def test_health_checker_dependency_injection_error_handling(self):
        """
        Test error handling in health checker dependency injection.

        Integration Scope:
            FastAPI DI → get_health_checker() → Error handling

        Business Impact:
            Ensures dependency injection handles errors gracefully and
            provides meaningful error information when health checker
            initialization fails.

        Test Strategy:
            - Simulate health checker initialization failure
            - Attempt dependency resolution with failure condition
            - Verify proper error handling and reporting
            - Confirm system degrades gracefully with failures

        Success Criteria:
            - Errors during health checker initialization are handled
            - Dependency injection provides meaningful error information
            - System continues operating despite initialization failures
            - Error conditions are properly reported and logged
        """
        # Mock health checker initialization to fail
        with patch('app.infrastructure.monitoring.health.HealthChecker') as mock_checker_class:
            mock_checker_class.side_effect = Exception("Health checker initialization failed")

            # Attempt to resolve dependency
            with pytest.raises(Exception) as exc_info:
                get_health_checker()

            # Verify error is properly raised
            assert "Health checker initialization failed" in str(exc_info.value)

    def test_health_checker_dependency_injection_concurrent_access(self):
        """
        Test health checker dependency injection under concurrent access.

        Integration Scope:
            FastAPI DI → get_health_checker() → Concurrent access

        Business Impact:
            Ensures health checker dependency injection works correctly
            under concurrent access patterns, maintaining thread safety
            and consistent behavior in multi-threaded environments.

        Test Strategy:
            - Simulate concurrent dependency resolutions
            - Verify singleton behavior under concurrent access
            - Confirm no race conditions or instance duplication
            - Validate consistent behavior across concurrent requests

        Success Criteria:
            - Singleton behavior maintained under concurrent access
            - No race conditions in dependency resolution
            - Consistent instance returned across concurrent calls
            - Performance remains acceptable under concurrent load
        """
        import threading
        import time

        # Test concurrent access to dependency injection
        results = []
        exceptions = []

        def resolve_health_checker():
            try:
                checker = get_health_checker()
                results.append(id(checker))
            except Exception as e:
                exceptions.append(e)

        # Create multiple threads to resolve dependency concurrently
        threads = []
        for i in range(10):
            thread = threading.Thread(target=resolve_health_checker)
            threads.append(thread)
            thread.start()

        # Wait for all threads to complete
        for thread in threads:
            thread.join()

        # Verify results
        assert len(exceptions) == 0, f"Exceptions occurred: {exceptions}"
        assert len(results) == 10

        # All resolutions should return the same instance
        first_instance_id = results[0]
        assert all(result == first_instance_id for result in results), "Different instances returned under concurrent access"
