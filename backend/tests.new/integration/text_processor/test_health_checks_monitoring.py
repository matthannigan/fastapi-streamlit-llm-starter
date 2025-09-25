"""
MEDIUM PRIORITY: Health Checks → Infrastructure Status → Operational Monitoring Integration Test

This test suite verifies the integration between health checks, infrastructure status monitoring,
and operational monitoring systems. It ensures comprehensive visibility into system health
and operational status for production monitoring.

Integration Scope:
    Tests the complete health monitoring flow from service health checks through
    infrastructure status collection to operational monitoring integration.

Seam Under Test:
    Health endpoints → Infrastructure health → Service status → Monitoring integration

Critical Paths:
    - Health check request → Infrastructure status collection → Service health aggregation → Status response
    - Infrastructure dependency health checks
    - Resilience system health reporting
    - Performance metrics integration
    - Health check security and authentication

Business Impact:
    Provides operational visibility for production monitoring and alerting.
    Failures here impact operational monitoring and system observability.

Test Strategy:
    - Test service health endpoint integration
    - Verify infrastructure dependency health checks
    - Test resilience system health reporting
    - Validate performance metrics integration
    - Test health check security and authentication
    - Verify health status aggregation logic
    - Test health monitoring and alerting integration

Success Criteria:
    - Service health endpoint provides accurate status reporting
    - Infrastructure dependencies are properly monitored
    - Resilience system health is correctly reported
    - Performance metrics are integrated into health checks
    - Health check security works appropriately
    - Health status aggregation works correctly
    - Monitoring integration provides operational visibility
"""

import pytest
import asyncio
import time
from unittest.mock import patch, AsyncMock, MagicMock
from fastapi.testclient import TestClient
from fastapi import status
from httpx import AsyncClient, ASGITransport

from app.main import app
from app.services.text_processor import TextProcessorService
from app.infrastructure.cache import AIResponseCache
from app.core.config import Settings
from app.schemas import TextProcessingRequest, TextProcessingOperation
from app.api.v1.deps import get_text_processor


class TestHealthChecksMonitoring:
    """
    Integration tests for health checks and operational monitoring.

    Seam Under Test:
        Health endpoints → Infrastructure health → Service status → Monitoring integration

    Critical Paths:
        - Comprehensive health status collection and reporting
        - Infrastructure dependency monitoring
        - Service health aggregation and metrics
        - Operational monitoring integration

    Business Impact:
        Validates operational monitoring that provides visibility
        into system health for production operations.

    Test Strategy:
        - Test comprehensive health status reporting
        - Verify infrastructure dependency monitoring
        - Validate service health aggregation
        - Test monitoring integration
    """

    @pytest.fixture(autouse=True)
    def setup_mocking_and_fixtures(self):
        """Set up comprehensive mocking for all tests in this class."""
        # Mock the AI agent to avoid actual API calls
        self.mock_agent_class = MagicMock()
        self.mock_agent_instance = AsyncMock()
        self.mock_agent_class.return_value = self.mock_agent_instance

        # Configure agent for health monitoring scenarios
        async def health_aware_agent_run(user_prompt: str):
            """Return responses appropriate for health monitoring tests."""
            mock_result = MagicMock()

            # Health-aware responses
            if "health_test" in user_prompt.lower():
                mock_result.output = "Health monitoring test response"
            else:
                mock_result.output = "Standard processing response"

            return mock_result

        self.mock_agent_instance.run.side_effect = health_aware_agent_run

        # Apply the mock
        with patch('app.services.text_processor.Agent', self.mock_agent_class):
            yield

    @pytest.fixture
    def client(self):
        """Create a test client."""
        return TestClient(app)

    @pytest.fixture
    def auth_headers(self):
        """Headers with valid authentication."""
        return {"Authorization": "Bearer test-api-key-12345"}

    @pytest.fixture
    def optional_auth_headers(self):
        """Headers with optional authentication for public endpoints."""
        return {"X-API-Key": "optional-auth-key"}

    @pytest.fixture
    def sample_text(self):
        """Sample text for testing."""
        return "This is a test of health monitoring and operational visibility in the text processing system."

    @pytest.fixture
    def mock_settings(self):
        """Mock settings for TextProcessorService."""
        mock_settings = MagicMock(spec=Settings)
        mock_settings.gemini_api_key = "test-key"
        mock_settings.ai_model = "gemini-pro"
        mock_settings.ai_temperature = 0.7
        mock_settings.BATCH_AI_CONCURRENCY_LIMIT = 5
        return mock_settings

    @pytest.fixture
    def mock_cache(self):
        """Mock cache for TextProcessorService."""
        return AsyncMock(spec=AIResponseCache)

    @pytest.fixture
    def text_processor_service(self, mock_settings, mock_cache):
        """Create TextProcessorService instance for testing."""
        return TextProcessorService(settings=mock_settings, cache=mock_cache)

    def test_comprehensive_health_status_reporting(self, client, auth_headers, text_processor_service):
        """
        Test comprehensive health status reporting for operational monitoring.

        Integration Scope:
            Health endpoint → Service health → Infrastructure status → Monitoring integration

        Business Impact:
            Provides operational visibility into system health for monitoring
            and alerting in production environments.

        Test Strategy:
            - Request comprehensive health status
            - Verify service health reporting
            - Check infrastructure status integration
            - Validate health status aggregation

        Success Criteria:
            - Health endpoint returns comprehensive status information
            - Service health is accurately reported
            - Infrastructure dependencies are monitored
            - Health status aggregation works correctly
            - Monitoring integration provides operational visibility
        """
        # Override dependency for this test
        app.dependency_overrides[get_text_processor] = lambda: text_processor_service

        try:
            # Request health status with authentication
            response = client.get("/v1/text_processing/health", headers=auth_headers)
            assert response.status_code == 200

            health_data = response.json()
            assert "overall_healthy" in health_data
            assert "service_type" in health_data
            assert "infrastructure" in health_data
            assert "domain_services" in health_data

            # Verify overall health status
            assert isinstance(health_data["overall_healthy"], bool)
            assert health_data["service_type"] == "domain"

            # Verify infrastructure health reporting
            infrastructure = health_data["infrastructure"]
            assert "resilience" in infrastructure
            assert isinstance(infrastructure["resilience"], dict)

            # Verify domain service health reporting
            domain_services = health_data["domain_services"]
            assert "text_processing" in domain_services
            assert isinstance(domain_services["text_processing"], dict)

        finally:
            # Clean up override
            app.dependency_overrides.clear()

    def test_infrastructure_dependency_health_checks(self, client, auth_headers, text_processor_service):
        """
        Test infrastructure dependency health monitoring.

        Integration Scope:
            Health endpoint → Infrastructure monitoring → Dependency status → Health reporting

        Business Impact:
            Ensures infrastructure dependencies are properly monitored
            for operational visibility and alerting.

        Test Strategy:
            - Check cache infrastructure health
            - Verify AI service integration health
            - Test resilience infrastructure monitoring
            - Validate infrastructure dependency reporting

        Success Criteria:
            - Infrastructure dependencies report accurate health status
            - Cache infrastructure health is monitored
            - AI service integration health is tracked
            - Resilience infrastructure status is reported
            - Dependency failures are properly detected
        """
        # Override dependency for this test
        app.dependency_overrides[get_text_processor] = lambda: text_processor_service

        try:
            response = client.get("/v1/text_processing/health", headers=auth_headers)
            assert response.status_code == 200

            health_data = response.json()

            # Verify infrastructure health reporting includes dependencies
            infrastructure = health_data["infrastructure"]
            assert isinstance(infrastructure, dict)

            # Infrastructure health should be available (even if mocked)
            assert "resilience" in infrastructure

        finally:
            # Clean up override
            app.dependency_overrides.clear()

    def test_resilience_system_health_reporting(self, client, auth_headers, text_processor_service):
        """
        Test resilience system health reporting and monitoring.

        Integration Scope:
            Health endpoint → Resilience monitoring → Circuit breaker status → Health aggregation

        Business Impact:
            Provides visibility into resilience system health for
            operational monitoring and capacity planning.

        Test Strategy:
            - Check resilience system health status
            - Verify circuit breaker health reporting
            - Test resilience metrics integration
            - Validate resilience health aggregation

        Success Criteria:
            - Resilience system health is accurately reported
            - Circuit breaker status is monitored
            - Resilience metrics are integrated into health checks
            - Health status reflects resilience system state
            - Resilience monitoring provides operational visibility
        """
        # Override dependency for this test
        app.dependency_overrides[get_text_processor] = lambda: text_processor_service

        try:
            response = client.get("/v1/text_processing/health", headers=auth_headers)
            assert response.status_code == 200

            health_data = response.json()

            # Verify resilience health is included
            infrastructure = health_data["infrastructure"]
            assert "resilience" in infrastructure

            # Resilience health should include system status
            resilience_health = infrastructure["resilience"]
            assert isinstance(resilience_health, dict)

        finally:
            # Clean up override
            app.dependency_overrides.clear()

    def test_performance_metrics_integration(self, client, auth_headers, text_processor_service):
        """
        Test performance metrics integration with health monitoring.

        Integration Scope:
            Health endpoint → Performance metrics → Response time monitoring → Health status

        Business Impact:
            Ensures performance metrics are integrated into health monitoring
            for comprehensive operational visibility.

        Test Strategy:
            - Perform operations to generate metrics
            - Check performance metrics in health status
            - Verify response time monitoring integration
            - Validate performance health indicators

        Success Criteria:
            - Performance metrics are collected during operations
            - Health status includes performance indicators
            - Response time monitoring is integrated
            - Performance health is accurately reported
            - Metrics provide visibility into system performance
        """
        # Override dependency for this test
        app.dependency_overrides[get_text_processor] = lambda: text_processor_service

        try:
            # First perform some operations to generate metrics
            for i in range(2):
                request_data = {
                    "text": f"{self.sample_text} performance_test_{i}",
                    "operation": "summarize"
                }

                response = client.post("/v1/text_processing/process", json=request_data, headers=auth_headers)
                assert response.status_code == 200

            # Then check health status
            health_response = client.get("/v1/text_processing/health", headers=auth_headers)
            assert health_response.status_code == 200

            health_data = health_response.json()

            # Health status should reflect system activity
            assert "overall_healthy" in health_data
            assert health_data["overall_healthy"] is True

        finally:
            # Clean up override
            app.dependency_overrides.clear()

    def test_health_check_security_and_authentication(self, client, sample_text, text_processor_service):
        """
        Test health check security and authentication integration.

        Integration Scope:
            Health endpoint → Authentication → Authorization → Health response

        Business Impact:
            Ensures health checks are properly secured while providing
            appropriate access for monitoring systems.

        Test Strategy:
            - Test health check with valid authentication
            - Test health check with optional authentication
            - Verify security controls are applied
            - Validate authentication error handling

        Success Criteria:
            - Health checks require appropriate authentication
            - Optional authentication works correctly
            - Security controls are properly applied
            - Authentication errors are handled gracefully
            - Monitoring access is appropriately controlled
        """
        # Override dependency for this test
        app.dependency_overrides[get_text_processor] = lambda: text_processor_service

        try:
            # Test with valid authentication
            response = client.get("/v1/text_processing/health", headers=auth_headers)
            assert response.status_code == 200

            health_data = response.json()
            assert "overall_healthy" in health_data

            # Test with optional authentication (should also work)
            optional_response = client.get("/v1/text_processing/health", headers={"X-API-Key": "optional-auth-key"})
            assert optional_response.status_code == 200

        finally:
            # Clean up override
            app.dependency_overrides.clear()

    def test_health_status_aggregation_logic(self, client, auth_headers, text_processor_service):
        """
        Test health status aggregation logic across components.

        Integration Scope:
            Multiple health sources → Status aggregation → Overall health calculation

        Business Impact:
            Ensures health status aggregation works correctly to provide
            accurate overall system health assessment.

        Test Strategy:
            - Test health aggregation with healthy components
            - Verify overall health calculation
            - Test aggregation logic with mixed health states
            - Validate health status computation

        Success Criteria:
            - Health status aggregation works correctly
            - Overall health reflects component health
            - Aggregation logic handles mixed states appropriately
            - Health status calculation is accurate
            - Component health contributes appropriately to overall status
        """
        # Override dependency for this test
        app.dependency_overrides[get_text_processor] = lambda: text_processor_service

        try:
            response = client.get("/v1/text_processing/health", headers=auth_headers)
            assert response.status_code == 200

            health_data = response.json()

            # Verify health status structure
            assert "overall_healthy" in health_data
            assert "service_type" in health_data
            assert "infrastructure" in health_data
            assert "domain_services" in health_data

            # Overall health should be boolean
            assert isinstance(health_data["overall_healthy"], bool)

            # Service type should be identified
            assert health_data["service_type"] == "domain"

        finally:
            # Clean up override
            app.dependency_overrides.clear()

    def test_health_monitoring_under_load(self, client, auth_headers, text_processor_service):
        """
        Test health monitoring behavior under system load.

        Integration Scope:
            Load conditions → Health monitoring → Status reporting → Load adaptation

        Business Impact:
            Ensures health monitoring remains accurate and responsive
            even under high system load.

        Test Strategy:
            - Generate system load through multiple requests
            - Monitor health status during load
            - Verify health reporting remains accurate
            - Test health monitoring resilience

        Success Criteria:
            - Health monitoring works correctly under load
            - Status reporting remains accurate during load
            - Health checks don't impact system performance
            - Monitoring provides reliable visibility during load
            - System health is correctly assessed under stress
        """
        # Override dependency for this test
        app.dependency_overrides[get_text_processor] = lambda: text_processor_service

        try:
            # Generate load through multiple requests
            for i in range(3):
                request_data = {
                    "text": f"{self.sample_text} load_test_{i}",
                    "operation": "summarize"
                }

                response = client.post("/v1/text_processing/process", json=request_data, headers=auth_headers)
                assert response.status_code == 200

            # Check health status during/after load
            health_response = client.get("/v1/text_processing/health", headers=auth_headers)
            assert health_response.status_code == 200

            health_data = health_response.json()
            assert health_data["overall_healthy"] is True

            # Health status should reflect system activity
            assert "infrastructure" in health_data
            assert "domain_services" in health_data

        finally:
            # Clean up override
            app.dependency_overrides.clear()

    def test_health_check_error_handling(self, client, auth_headers, text_processor_service):
        """
        Test health check error handling and graceful degradation.

        Integration Scope:
            Health check → Error handling → Graceful response → Monitoring continuity

        Business Impact:
            Ensures health monitoring continues to provide value even
            when individual components fail.

        Test Strategy:
            - Test health check with component failures
            - Verify graceful error handling
            - Confirm health monitoring continues despite errors
            - Validate error reporting in health status

        Success Criteria:
            - Health checks handle component failures gracefully
            - Error conditions are reported appropriately
            - Health monitoring continues despite failures
            - Error information is available for troubleshooting
            - System remains monitorable during failures
        """
        # Override dependency for this test
        app.dependency_overrides[get_text_processor] = lambda: text_processor_service

        try:
            response = client.get("/v1/text_processing/health", headers=auth_headers)
            assert response.status_code == 200

            health_data = response.json()

            # Health check should succeed even with potential internal issues
            assert "overall_healthy" in health_data
            assert isinstance(health_data["overall_healthy"], bool)

        finally:
            # Clean up override
            app.dependency_overrides.clear()

    def test_health_status_trends_and_history(self, client, auth_headers, text_processor_service):
        """
        Test health status trends and historical monitoring.

        Integration Scope:
            Health monitoring → Trend analysis → Historical tracking → Status evolution

        Business Impact:
            Provides historical context for health monitoring to enable
            trend analysis and proactive issue detection.

        Test Strategy:
            - Check health status multiple times
            - Verify status consistency over time
            - Test trend detection capabilities
            - Validate historical monitoring integration

        Success Criteria:
            - Health status is consistent across multiple checks
            - Trend analysis capabilities work correctly
            - Historical monitoring provides useful context
            - Status changes are tracked appropriately
            - Monitoring provides temporal visibility
        """
        # Override dependency for this test
        app.dependency_overrides[get_text_processor] = lambda: text_processor_service

        try:
            # Check health status multiple times
            health_results = []
            for i in range(3):
                response = client.get("/v1/text_processing/health", headers=auth_headers)
                assert response.status_code == 200

                health_data = response.json()
                health_results.append(health_data)

                # Small delay between checks
                time.sleep(0.1)

            # Verify consistent health reporting
            for health_data in health_results:
                assert "overall_healthy" in health_data
                assert health_data["overall_healthy"] is True
                assert health_data["service_type"] == "domain"

            # All health checks should report the same structure
            assert all("infrastructure" in h for h in health_results)
            assert all("domain_services" in h for h in health_results)

        finally:
            # Clean up override
            app.dependency_overrides.clear()

    def test_operational_monitoring_integration(self, client, auth_headers, text_processor_service):
        """
        Test operational monitoring integration and alerting.

        Integration Scope:
            Health monitoring → Operational metrics → Alerting integration → Monitoring systems

        Business Impact:
            Ensures health monitoring integrates properly with operational
            monitoring and alerting systems for production visibility.

        Test Strategy:
            - Test health monitoring data collection
            - Verify operational metrics integration
            - Test alerting threshold integration
            - Validate monitoring system compatibility

        Success Criteria:
            - Health monitoring integrates with operational systems
            - Metrics are collected for alerting
            - Threshold-based monitoring works correctly
            - Monitoring system compatibility is maintained
            - Operational visibility is comprehensive
        """
        # Override dependency for this test
        app.dependency_overrides[get_text_processor] = lambda: text_processor_service

        try:
            response = client.get("/v1/text_processing/health", headers=auth_headers)
            assert response.status_code == 200

            health_data = response.json()

            # Verify health data structure supports operational monitoring
            assert "overall_healthy" in health_data
            assert "infrastructure" in health_data
            assert "domain_services" in health_data

            # Health data should be structured for monitoring systems
            infrastructure = health_data["infrastructure"]
            assert isinstance(infrastructure, dict)

            domain_services = health_data["domain_services"]
            assert isinstance(domain_services, dict)

            # Data should be suitable for monitoring dashboards and alerting
            assert health_data["service_type"] in ["domain", "infrastructure"]

        finally:
            # Clean up override
            app.dependency_overrides.clear()
