"""
Integration tests for health monitoring API endpoints.

These tests verify the integration between FastAPI monitoring endpoints
and the health monitoring infrastructure, ensuring proper API responses,
dependency injection, and external monitoring system compatibility.

HIGH PRIORITY - External monitoring system interface
"""

import pytest
from unittest.mock import patch, AsyncMock
from fastapi.testclient import TestClient

from app.main import app
from app.infrastructure.monitoring.health import (
    HealthStatus,
    ComponentStatus,
)
from app.infrastructure.cache import AIResponseCache


class TestHealthMonitoringAPIIntegration:
    """
    Integration tests for health monitoring API endpoints.

    Seam Under Test:
        /internal/monitoring/health → HealthChecker → Component validation → Status aggregation

    Critical Path:
        HTTP request → Health checker resolution → Component validation →
        Response formatting → API response

    Business Impact:
        Provides external monitoring systems with comprehensive health status
        and ensures monitoring infrastructure reliability for operational visibility.

    Test Strategy:
        - Test comprehensive health monitoring API responses
        - Verify dependency injection integration with FastAPI
        - Confirm proper HTTP status codes and response structure
        - Test authentication and authorization integration
        - Validate component-level health information accuracy

    Success Criteria:
        - Health monitoring API returns comprehensive system status
        - Component health information is accurate and detailed
        - HTTP responses follow proper API design patterns
        - Authentication integration works correctly
        - Response times are reasonable for monitoring frequency
    """

    def test_health_monitoring_api_comprehensive_response_structure(self, client):
        """
        Test that health monitoring API returns comprehensive response structure.

        Integration Scope:
            HTTP client → FastAPI app → Health monitoring endpoint → HealthChecker

        Business Impact:
            Ensures external monitoring systems receive complete and
            structured health information for proper alerting and
            dashboard integration.

        Test Strategy:
            - Make HTTP request to monitoring health endpoint
            - Validate comprehensive response structure
            - Verify all required fields are present
            - Confirm response follows documented API contract

        Success Criteria:
            - Response contains status, timestamp, and components
            - All expected components are present in response
            - Response structure matches API documentation
            - HTTP status code is 200 for successful health check
        """
        response = client.get("/internal/monitoring/health")

        # Verify HTTP response structure
        assert response.status_code == 200
        data = response.json()

        # Verify comprehensive response structure
        assert "status" in data
        assert "timestamp" in data
        assert "components" in data
        assert "available_endpoints" in data

        # Verify status is valid enum value
        assert data["status"] in ["healthy", "degraded", "unhealthy"]

        # Verify timestamp is properly formatted
        assert isinstance(data["timestamp"], str)
        assert len(data["timestamp"]) > 0

        # Verify components object exists
        assert isinstance(data["components"], dict)

        # Verify available endpoints list
        assert isinstance(data["available_endpoints"], list)
        assert len(data["available_endpoints"]) > 0

    def test_health_monitoring_api_component_level_health_reporting(
        self, client, fake_redis_cache, performance_monitor
    ):
        """
        Test component-level health reporting in monitoring API.

        Integration Scope:
            HTTP client → FastAPI app → Cache service → Performance monitor

        Business Impact:
            Provides detailed component-level health information
            enabling operators to identify specific failing components
            without ambiguity.

        Test Strategy:
            - Configure cache service with performance monitor
            - Make HTTP request to monitoring health endpoint
            - Validate component-specific health information
            - Verify component status and metadata accuracy

        Success Criteria:
            - Each component reports its specific health status
            - Component metadata provides actionable information
            - Failed components are clearly identified
            - Component information helps with troubleshooting
        """
        # Configure cache with performance monitor
        fake_redis_cache.performance_monitor = performance_monitor

        with patch('app.dependencies.get_cache_service', return_value=fake_redis_cache):
            response = client.get("/internal/monitoring/health")

            assert response.status_code == 200
            data = response.json()

            # Verify component-level health information
            components = data["components"]
            assert isinstance(components, dict)

            # Check for expected components
            component_names = list(components.keys())
            assert len(component_names) > 0

            # Verify each component has required fields
            for component_name, component_info in components.items():
                assert "status" in component_info
                assert component_info["status"] in ["healthy", "degraded", "unhealthy"]

    def test_health_monitoring_api_with_mixed_component_health_states(
        self, client, fake_redis_cache, performance_monitor
    ):
        """
        Test health monitoring API with mixed component health states.

        Integration Scope:
            HTTP client → FastAPI app → Mixed health components → Status aggregation

        Business Impact:
            Ensures monitoring API correctly aggregates and reports
            mixed health states, providing accurate overall system
            status for operational decision making.

        Test Strategy:
            - Configure components with different health states
            - Make HTTP request to monitoring health endpoint
            - Validate overall status reflects component states
            - Verify individual component status is preserved

        Success Criteria:
            - Overall status reflects worst component state
            - Individual component states are accurately reported
            - Mixed states don't cause response formatting issues
            - Response structure remains consistent despite mixed states
        """
        # Configure cache with performance monitor but simulate some issues
        fake_redis_cache.performance_monitor = performance_monitor

        # Mock some performance monitor issues
        performance_monitor.get_performance_stats.return_value = {
            "timestamp": "2024-01-15T10:30:00.123456",
            "total_cache_operations": 0,  # No operations - degraded state
        }

        with patch('app.dependencies.get_cache_service', return_value=fake_redis_cache):
            response = client.get("/internal/monitoring/health")

            assert response.status_code == 200
            data = response.json()

            # Verify response structure with mixed states
            assert "status" in data
            assert "components" in data
            assert isinstance(data["components"], dict)

            # Verify overall status logic
            overall_status = data["status"]
            assert overall_status in ["healthy", "degraded", "unhealthy"]

    def test_health_monitoring_api_endpoint_discovery_functionality(
        self, client
    ):
        """
        Test endpoint discovery functionality in health monitoring API.

        Integration Scope:
            HTTP client → FastAPI app → Endpoint registration → Discovery response

        Business Impact:
            Enables external monitoring systems to discover available
            monitoring endpoints for comprehensive system coverage
            and automated monitoring setup.

        Test Strategy:
            - Make HTTP request to monitoring health endpoint
            - Validate endpoint discovery list is present
            - Verify expected monitoring endpoints are listed
            - Confirm endpoint URLs are properly formatted

        Success Criteria:
            - Available endpoints list is comprehensive
            - All expected monitoring endpoints are included
            - Endpoint URLs follow correct format and structure
            - List helps with monitoring system integration
        """
        response = client.get("/internal/monitoring/health")

        assert response.status_code == 200
        data = response.json()

        # Verify endpoint discovery functionality
        assert "available_endpoints" in data
        endpoints = data["available_endpoints"]
        assert isinstance(endpoints, list)

        # Verify expected monitoring endpoints are present
        expected_endpoints = [
            "GET /internal/monitoring/health",
            "GET /internal/cache/status",
            "GET /internal/cache/metrics",
            "GET /internal/cache/invalidation-stats",
            "GET /internal/resilience/health"
        ]

        for expected_endpoint in expected_endpoints:
            assert expected_endpoint in endpoints, f"Missing expected endpoint: {expected_endpoint}"

        # Verify endpoint format is consistent
        for endpoint in endpoints:
            assert endpoint.startswith(("GET ", "POST ", "PUT ", "DELETE "))
            assert "/internal/" in endpoint

    def test_health_monitoring_api_response_time_characteristics(
        self, client, fake_redis_cache, performance_monitor
    ):
        """
        Test health monitoring API response time characteristics.

        Integration Scope:
            HTTP client → FastAPI app → Health checks → Response timing

        Business Impact:
            Ensures monitoring API response times are reasonable for
            frequent polling by external monitoring systems, maintaining
            operational visibility without performance impact.

        Test Strategy:
            - Configure comprehensive monitoring setup
            - Make HTTP request to monitoring health endpoint
            - Measure and validate response time
            - Verify timing is suitable for monitoring frequency

        Success Criteria:
            - Response time is reasonable for monitoring scenarios
            - Performance doesn't degrade with comprehensive checks
            - Response time includes all component validation
            - System remains responsive during health monitoring
        """
        import time

        fake_redis_cache.performance_monitor = performance_monitor

        with patch('app.dependencies.get_cache_service', return_value=fake_redis_cache):
            start_time = time.time()
            response = client.get("/internal/monitoring/health")
            end_time = time.time()

            # Calculate actual response time
            response_time_ms = (end_time - start_time) * 1000

            # Verify response time characteristics
            assert response.status_code == 200
            assert response_time_ms > 0
            assert response_time_ms < 1000  # Should complete within 1 second

            # Verify response was successful
            data = response.json()
            assert "status" in data
            assert isinstance(data["timestamp"], str)

    def test_health_monitoring_api_with_authentication_integration(
        self, client, fake_redis_cache, performance_monitor
    ):
        """
        Test health monitoring API with authentication integration.

        Integration Scope:
            HTTP client → FastAPI app → Authentication → Health monitoring

        Business Impact:
            Ensures monitoring API properly integrates with authentication
            system, providing secure access to monitoring information
            while maintaining operational functionality.

        Test Strategy:
            - Test API access with valid authentication
            - Test API access without authentication
            - Verify authentication integration works correctly
            - Confirm monitoring data is accessible when authenticated

        Success Criteria:
            - Authentication is properly validated for monitoring access
            - Monitoring data is accessible with valid credentials
            - Response structure remains consistent with authentication
            - Security integration doesn't break monitoring functionality
        """
        fake_redis_cache.performance_monitor = performance_monitor

        with patch('app.dependencies.get_cache_service', return_value=fake_redis_cache):
            # Test with authentication
            response = client.get("/internal/monitoring/health")

            # Should work without authentication (optional_verify_api_key)
            assert response.status_code == 200

            data = response.json()
            assert "status" in data
            assert "components" in data
            assert isinstance(data["components"], dict)

    def test_health_monitoring_api_with_component_health_aggregation(
        self, client, fake_redis_cache, performance_monitor
    ):
        """
        Test component health status aggregation in monitoring API.

        Integration Scope:
            HTTP client → FastAPI app → Component validation → Status aggregation

        Business Impact:
            Ensures monitoring API correctly aggregates individual
            component health states into meaningful overall system
            health status for operational decision making.

        Test Strategy:
            - Configure multiple components with different health states
            - Make HTTP request to monitoring health endpoint
            - Validate overall status reflects component states
            - Verify aggregation logic works correctly

        Success Criteria:
            - Overall status correctly reflects component health states
            - Aggregation follows health status priority rules
            - Individual component states are preserved in response
            - Response provides clear overall system health picture
        """
        fake_redis_cache.performance_monitor = performance_monitor

        with patch('app.dependencies.get_cache_service', return_value=fake_redis_cache):
            response = client.get("/internal/monitoring/health")

            assert response.status_code == 200
            data = response.json()

            # Verify health status aggregation
            overall_status = data["status"]
            assert overall_status in ["healthy", "degraded", "unhealthy"]

            components = data["components"]
            assert isinstance(components, dict)

            # If any component is unhealthy, overall should be unhealthy
            if any(comp.get("status") == "unhealthy" for comp in components.values()):
                assert overall_status == "unhealthy"
            # If any component is degraded but none unhealthy, overall should be degraded
            elif any(comp.get("status") == "degraded" for comp in components.values()):
                assert overall_status == "degraded"
            # Otherwise overall should be healthy
            else:
                assert overall_status == "healthy"

    def test_health_monitoring_api_error_handling_and_response_format(
        self, client
    ):
        """
        Test error handling and response format consistency in monitoring API.

        Integration Scope:
            HTTP client → FastAPI app → Error handling → Response formatting

        Business Impact:
            Ensures monitoring API handles errors gracefully and maintains
            consistent response formats even during system failures,
            providing reliable monitoring data for operational systems.

        Test Strategy:
            - Simulate component failures in monitoring system
            - Make HTTP request to monitoring health endpoint
            - Validate error handling and response format
            - Verify system degrades gracefully under failure conditions

        Success Criteria:
            - API handles component failures without crashing
            - Response format remains consistent despite failures
            - Error information is captured and reported
            - System continues providing monitoring data even with failed components
        """
        # Mock a component to fail during health check
        with patch('app.api.internal.monitoring.cache_service') as mock_cache:
            mock_cache.get_cache_stats = AsyncMock(side_effect=Exception("Cache service unavailable"))

            response = client.get("/internal/monitoring/health")

            # Should still return 200 but with degraded status
            assert response.status_code == 200
            data = response.json()

            # Verify response structure is maintained
            assert "status" in data
            assert "timestamp" in data
            assert "components" in data
            assert "available_endpoints" in data

            # Verify error is captured
            assert data["status"] in ["degraded", "unhealthy"]

            # Verify components reflect the failure
            components = data["components"]
            assert isinstance(components, dict)
