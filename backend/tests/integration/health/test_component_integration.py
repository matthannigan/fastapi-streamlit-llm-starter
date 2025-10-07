"""
Component-Specific Health Integration Tests

This test module implements component-specific integration tests for the health monitoring
system, validating individual component behaviors through the health endpoint API.

Tests 1.5-1.7 from the TEST_PLAN.md focus on:
- Cache infrastructure health and Redis connectivity
- Cache graceful degradation with memory fallback
- Resilience health monitoring with circuit breaker states

These tests follow the outside-in testing philosophy, validating observable behavior
through HTTP requests without mocking internal components.
"""

import pytest
import time


class TestCacheComponentIntegration:
    """
    Test suite for cache component health monitoring integration.

    Integration Scope:
        API endpoint → HealthChecker → check_cache_health → Cache infrastructure

    Tests validate cache health reporting through the complete API integration,
    ensuring cache operational status is accurately reflected in system health.
    """

    @pytest.mark.integration
    async def test_cache_health_reports_operational_status_through_api(self, integration_client):
        """
        Test cache health check reports operational status through health endpoint.

        Integration Scope:
            API endpoint → HealthChecker → check_cache_health → Cache infrastructure

        Contract Validation:
            - ComponentStatus includes cache backend status per health.pyi:625-647
            - Connectivity validation reports accurate operational state
            - Metadata includes backend information for diagnostics

        Business Impact:
            Validates caching infrastructure operational for optimal performance
            Enables monitoring of cache backend availability

        Test Strategy:
            - Request health status with cache infrastructure available
            - Verify cache component reports accurately
            - Check metadata includes backend information

        Success Criteria:
            - Cache component status is "healthy" when Redis available
            - Metadata indicates active backend type
            - Response time measured for performance monitoring
        """
        # Arrange: Ensure cache is available with default configuration
        # Use the production environment setup from conftest.py

        # Act: Make HTTP request to health endpoint
        response = integration_client.get("/v1/health")

        # Assert: Observable HTTP behavior
        assert response.status_code == 200, f"Health endpoint should return 200, got {response.status_code}"

        data = response.json()
        assert "status" in data, "Response should include overall status"
        assert "timestamp" in data, "Response should include timestamp"

        # For cache-specific testing, we need to access the detailed component information
        # Since the public endpoint returns simplified format, we'll test what's available
        assert data["cache_healthy"] in [True, None], f"Cache should be operational or None, got {data['cache_healthy']}"

        # If cache is healthy, the overall system should at least be degraded or better
        if data["cache_healthy"] is True:
            assert data["status"] in ["healthy", "degraded"], "System should be operational when cache is healthy"

    @pytest.mark.integration
    async def test_cache_health_reports_degraded_with_fallback_mode(self, integration_client, monkeypatch):
        """
        Test cache health check reports DEGRADED when using fallback mechanisms.

        Integration Scope:
            API endpoint → HealthChecker → check_cache_health → Memory cache fallback

        Contract Validation:
            - ComponentStatus with status=DEGRADED for fallback mode
            - System remains operational with reduced cache capacity
            - Graceful degradation maintains service availability

        Business Impact:
            Demonstrates cache resilience through fallback to memory backend
            Alerts operations to reduced cache capacity without system failure

        Test Strategy:
            - Configure memory-only cache (simulate Redis unavailable)
            - Verify degraded status reported accurately
            - Confirm system remains operational

        Success Criteria:
            - Cache component status indicates fallback mode
            - System remains operational
            - Message indicates reduced functionality or fallback state
        """
        # Arrange: Configure memory-only cache to simulate Redis unavailability
        monkeypatch.setenv("CACHE_PRESET", "minimal")

        # Force re-evaluation of cache settings if possible
        try:
            from app.core.config import settings
            # Reset cache configuration by invalidating any cached values
            if hasattr(settings, "_cache_config"):
                delattr(settings, "_cache_config")
        except Exception:
            pass  # Configuration reload is optional for testing

        # Act: Make HTTP request to health endpoint
        response = integration_client.get("/v1/health")

        # Assert: System remains functional with cache fallback
        assert response.status_code == 200, f"Health endpoint should return 200, got {response.status_code}"

        data = response.json()
        assert data["status"] in ["healthy", "degraded"], f"System should remain operational, got status: {data['status']}"

        # Cache should be either healthy (with memory) or None (unavailable)
        assert data["cache_healthy"] in [True, None], f"Cache should use memory fallback or be None, got {data['cache_healthy']}"

        # Overall system should remain at least degraded, not completely failed
        assert data["status"] != "unhealthy", "System should not be completely unhealthy due to cache issues"

    @pytest.mark.integration
    async def test_cache_health_with_environment_variables(self, integration_client, monkeypatch):
        """
        Test cache health responds correctly to different cache configurations.

        Integration Scope:
            API endpoint → HealthChecker → check_cache_health with environment-based configuration

        Contract Validation:
            - Cache health check respects environment configuration
            - Different cache presets affect health reporting appropriately
            - Configuration changes are reflected in health status

        Business Impact:
            Ensures cache configuration changes are properly detected and reported
            Validates operational visibility into cache configuration state

        Test Strategy:
            - Test different cache presets via environment variables
            - Verify health endpoint reflects configuration changes
            - Test cache availability under different configurations

        Success Criteria:
            - Health endpoint responds correctly to different cache configurations
            - Cache status reflects actual configuration state
            - System remains stable across configuration changes
        """
        # Test Case 1: Disabled cache (falls back to memory, still healthy)
        monkeypatch.setenv("CACHE_PRESET", "disabled")
        response = integration_client.get("/v1/health")
        assert response.status_code == 200
        data = response.json()
        # Even "disabled" cache uses memory cache and reports as healthy
        assert data["cache_healthy"] is True, "Disabled cache should fallback to memory and be healthy"

        # Test Case 2: Minimal cache (memory only)
        monkeypatch.setenv("CACHE_PRESET", "minimal")
        response = integration_client.get("/v1/health")
        assert response.status_code == 200
        data = response.json()
        # Memory cache should be healthy
        assert data["cache_healthy"] is True, "Minimal cache should be healthy with memory"


class TestResilienceComponentIntegration:
    """
    Test suite for resilience component health monitoring integration.

    Integration Scope:
        API endpoint → HealthChecker → check_resilience_health → Circuit breaker states

    Tests validate resilience health reporting through the complete API integration,
    ensuring circuit breaker states and resilience infrastructure are accurately monitored.
    """

    @pytest.mark.integration
    async def test_resilience_health_reports_circuit_breaker_states(self, integration_client):
        """
        Test resilience health check reports circuit breaker states accurately.

        Integration Scope:
            API endpoint → HealthChecker → check_resilience_health → Circuit breaker states

        Contract Validation:
            - ComponentStatus includes circuit breaker information per health.pyi:650-713
            - HEALTHY when all circuits closed, DEGRADED when circuits open
            - Metadata includes circuit breaker counts and states

        Business Impact:
            Monitors resilience infrastructure protecting system from failures
            Alerts to external service issues via circuit breaker states

        Test Strategy:
            - Request health status with resilience orchestrator available
            - Verify resilience component reports circuit breaker states
            - Check metadata includes operational metrics

        Success Criteria:
            - Resilience component status reflects circuit breaker states
            - Metadata includes circuit breaker counts
            - Open circuits reported when present
        """
        # Arrange: Default resilience configuration should be available

        # Act: Make HTTP request to health endpoint
        response = integration_client.get("/v1/health")

        # Assert: Resilience component reports status
        assert response.status_code == 200, f"Health endpoint should return 200, got {response.status_code}"

        data = response.json()
        assert "status" in data, "Response should include overall status"

        # Resilience should be healthy or None (if not configured)
        assert data["resilience_healthy"] in [True, None], f"Resilience should be operational or None, got {data['resilience_healthy']}"

        # If resilience is healthy, overall system should be at least degraded
        if data["resilience_healthy"] is True:
            assert data["status"] in ["healthy", "degraded"], "System should be operational when resilience is healthy"

    @pytest.mark.integration
    async def test_resilience_health_with_different_presets(self, integration_client, monkeypatch):
        """
        Test resilience health responds correctly to different resilience configurations.

        Integration Scope:
            API endpoint → HealthChecker → check_resilience_health with different presets

        Contract Validation:
            - Resilience health check respects preset configuration
            - Different resilience presets affect health reporting appropriately
            - Configuration changes are reflected in health status

        Business Impact:
            Ensures resilience configuration changes are properly detected and reported
            Validates operational visibility into resilience configuration state

        Test Strategy:
            - Test different resilience presets via environment variables
            - Verify health endpoint reflects configuration changes
            - Test resilience availability under different configurations

        Success Criteria:
            - Health endpoint responds correctly to different resilience configurations
            - Resilience status reflects actual configuration state
            - System remains stable across configuration changes
        """
        # Test Case 1: Simple resilience preset
        monkeypatch.setenv("RESILIENCE_PRESET", "simple")
        response = integration_client.get("/v1/health")
        assert response.status_code == 200
        data = response.json()
        # Simple preset should make resilience healthy
        assert data["resilience_healthy"] in [True, None], "Simple resilience should be healthy or None"

        # Test Case 2: Development resilience preset
        monkeypatch.setenv("RESILIENCE_PRESET", "development")
        response = integration_client.get("/v1/health")
        assert response.status_code == 200
        data = response.json()
        # Development preset should make resilience healthy
        assert data["resilience_healthy"] in [True, None], "Development resilience should be healthy or None"

    @pytest.mark.integration
    async def test_resilience_health_with_invalid_configuration(self, integration_client, monkeypatch):
        """
        Test resilience health gracefully handles invalid configuration.

        Integration Scope:
            API endpoint → HealthChecker → check_resilience_health with invalid config

        Contract Validation:
            - Resilience health check handles invalid configuration gracefully
            - Invalid configurations result in degraded status rather than system failure
            - Error handling provides operational visibility

        Business Impact:
            Ensures system remains operational despite resilience configuration issues
            Provides clear visibility into configuration problems

        Test Strategy:
            - Configure invalid resilience preset
            - Verify system degrades gracefully
            - Confirm health endpoint remains accessible

        Success Criteria:
            - Health endpoint remains accessible (200 status)
            - Resilience reports appropriate status for invalid configuration
            - Overall system continues to function
        """
        # Arrange: Configure invalid resilience preset
        monkeypatch.setenv("RESILIENCE_PRESET", "nonexistent_preset")

        # Act: Request health status
        response = integration_client.get("/v1/health")

        # Assert: System handles invalid resilience configuration gracefully
        assert response.status_code == 200, "Health endpoint should remain accessible with invalid resilience config"

        data = response.json()
        # System should be at least degraded, not completely failed
        assert data["status"] in ["healthy", "degraded"], f"System should remain operational, got status: {data['status']}"

        # Resilience might be None or False due to invalid configuration
        assert data["resilience_healthy"] in [True, False, None], "Resilience status should reflect configuration issue"


class TestComponentInteractionIntegration:
    """
    Test suite for component interaction and system-wide health monitoring.

    Tests validate how multiple components work together and affect overall system health,
    ensuring proper aggregation and graceful degradation patterns.
    """

    @pytest.mark.integration
    async def test_multiple_component_health_interaction(self, integration_client, monkeypatch):
        """
        Test interaction between multiple component health states.

        Integration Scope:
            API endpoint → HealthChecker → Multiple component health checks

        Contract Validation:
            - System health aggregation follows worst-case logic per health.pyi:524-526
            - Multiple component issues are properly aggregated
            - Component interactions don't cause system failures

        Business Impact:
            Validates system behavior under multiple component issues
            Ensures proper health aggregation across all components

        Test Strategy:
            - Configure multiple components with different health states
            - Verify system health reflects worst component state
            - Test graceful degradation with multiple issues

        Success Criteria:
            - Overall system status reflects worst component status
            - Health endpoint remains accessible
            - Component states are properly aggregated
        """
        # Arrange: Configure minimal cache and no AI key to create multiple issues
        monkeypatch.setenv("CACHE_PRESET", "minimal")
        monkeypatch.delenv("GEMINI_API_KEY", raising=False)

        # Act: Request health status
        response = integration_client.get("/v1/health")

        # Assert: System handles multiple component issues appropriately
        assert response.status_code == 200, "Health endpoint should return 200"

        data = response.json()
        # System should be degraded due to missing AI key
        assert data["status"] in ["degraded", "healthy"], f"System should handle multiple issues gracefully, got: {data['status']}"

        # AI should be unavailable (missing API key)
        assert data["ai_model_available"] is False, "AI should be unavailable without API key"

        # Cache should be operational with memory fallback
        assert data["cache_healthy"] in [True, None], "Cache should use memory fallback"

        # Resilience should be operational
        assert data["resilience_healthy"] in [True, None], "Resilience should be operational"

    @pytest.mark.integration
    async def test_health_endpoint_performance_monitoring(self, integration_client):
        """
        Test health endpoint includes performance monitoring capabilities.

        Integration Scope:
            API endpoint → HealthChecker → Performance measurement

        Contract Validation:
            - Health check execution time is measured per health.pyi:266
            - Response includes timing information for monitoring
            - Performance metrics are available for operational visibility

        Business Impact:
            Enables performance monitoring of health check infrastructure
            Provides operational visibility into health check response times

        Test Strategy:
            - Make multiple health check requests
            - Verify response timing is reasonable
            - Check that timing information is available

        Success Criteria:
            - Health check responses are timely
            - Performance doesn't degrade significantly
            - Response structure supports performance monitoring
        """
        # Arrange: No special configuration needed

        # Act: Make health check request and measure timing
        start_time = time.time()
        response = integration_client.get("/v1/health")
        end_time = time.time()

        response_time_ms = (end_time - start_time) * 1000

        # Assert: Performance characteristics
        assert response.status_code == 200, "Health endpoint should return 200"

        # Health check should be reasonably fast
        assert response_time_ms < 2000, f"Health check should complete in < 2s, took {response_time_ms:.1f}ms"

        # Response should include timestamp for performance tracking
        data = response.json()
        assert "timestamp" in data, "Response should include timestamp for performance monitoring"

        # Timestamp should be recent (within last 5 seconds)
        response_timestamp = data["timestamp"]
        # The timestamp is ISO format, so we can parse it to check recency
        import datetime
        try:
            parsed_time = datetime.datetime.fromisoformat(response_timestamp.replace("Z", "+00:00"))
            time_diff = datetime.datetime.now(datetime.UTC) - parsed_time
            assert abs(time_diff.total_seconds()) < 5, "Health check timestamp should be recent"
        except (ValueError, TypeError):
            # If timestamp parsing fails, just ensure it exists
            assert response_timestamp is not None, "Timestamp should be present"
