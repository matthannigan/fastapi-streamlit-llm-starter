"""
Tests for resilience integration.
Need to combine old test_resilience_endpoints.py and test_preset_resilience_integration.py

This file currently only contains tests that were in test_resilience_endpoints.py

Comprehensive tests for resilience endpoints.
Tests all endpoints in app/resilience_endpoints.py
"""

import pytest
import json
from unittest.mock import Mock, patch, AsyncMock
from fastapi.testclient import TestClient
from fastapi import status

from app.main import app

@pytest.fixture(autouse=True)
def mock_resilience_service():
    """Mock the resilience service for all tests in this module."""
    with patch('app.infrastructure.resilience.ai_resilience') as mock_resilience:
        # Default healthy state
        mock_resilience.get_health_status.return_value = {
            "healthy": True,
            "open_circuit_breakers": [],
            "half_open_circuit_breakers": [],
            "total_circuit_breakers": 3
        }
        
        # Default metrics
        mock_resilience.get_all_metrics.return_value = {
            "operations": {
                "summarize_text": {
                    "total_calls": 100,
                    "successful_calls": 95,
                    "failed_calls": 5,
                    "retry_attempts": 10
                }
            },
            "circuit_breakers": {
                "test_breaker": {
                    "state": "closed",
                    "failure_count": 0,
                    "failure_threshold": 5
                }
            },
            "summary": {"overall_success_rate": 95.0}
        }
        
        # Default circuit breakers
        mock_resilience.circuit_breakers = {}
        
        # Default configs
        mock_resilience.configs = {}
        
        yield mock_resilience


@pytest.fixture
def mock_text_processor():
    """Mock the text processor service."""
    with patch('app.api.v1.deps.get_text_processor') as mock_get_processor:
        mock_processor = AsyncMock()
        mock_processor.get_resilience_health.return_value = {
            "strategies": {"summarize": "balanced"},
            "status": "healthy"
        }
        mock_processor.resilience_strategies = {"summarize": "balanced"}
        mock_get_processor.return_value = mock_processor
        yield mock_processor


class TestResilienceHealthEndpoint:
    """Test GET /resilience/health endpoint."""
    
    def test_resilience_health_success(self, client, mock_resilience_service, mock_text_processor):
        """Test successful health check."""
        response = client.get("/resilience/health")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "resilience_health" in data
        assert "service_health" in data
        assert "overall_healthy" in data
        assert data["overall_healthy"] is True

    def test_resilience_health_with_auth(self, client, auth_headers, mock_resilience_service, mock_text_processor):
        """Test health check with optional authentication."""
        response = client.get("/resilience/health", headers=auth_headers)
        assert response.status_code == status.HTTP_200_OK

    def test_resilience_health_error(self, client, mock_resilience_service, mock_text_processor):
        """Test health check when service throws error."""
        mock_resilience_service.get_health_status.side_effect = Exception("Service error")
        
        response = client.get("/resilience/health")
        
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        data = response.json()
        assert "Failed to get resilience health" in data["detail"]


class TestResilienceMetricsEndpoints:
    """Test metrics-related endpoints."""
    
    def test_get_all_metrics_success(self, client, auth_headers, mock_resilience_service):
        """Test GET /resilience/metrics with authentication."""
        response = client.get("/resilience/metrics", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "operations" in data
        assert "summarize_text" in data["operations"]

    def test_get_all_metrics_unauthorized(self, client, mock_resilience_service):
        """Test GET /resilience/metrics without authentication."""
        response = client.get("/resilience/metrics")
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_get_operation_metrics_success(self, client, auth_headers, mock_resilience_service):
        """Test GET /resilience/metrics/{operation_name}."""
        mock_metrics = Mock()
        mock_metrics.to_dict.return_value = {
            "total_calls": 50,
            "successful_calls": 48,
            "failed_calls": 2
        }
        mock_resilience_service.get_metrics.return_value = mock_metrics
        
        response = client.get("/resilience/metrics/summarize_text", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["operation"] == "summarize_text"
        assert "metrics" in data

    def test_get_operation_metrics_error(self, client, auth_headers, mock_resilience_service):
        """Test GET /resilience/metrics/{operation_name} with error."""
        mock_resilience_service.get_metrics.side_effect = Exception("Metrics error")
        
        response = client.get("/resilience/metrics/nonexistent", headers=auth_headers)
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_reset_metrics_all_operations(self, client, auth_headers, mock_resilience_service):
        """Test POST /resilience/metrics/reset without operation name."""
        response = client.post("/resilience/metrics/reset", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "all operations" in data["message"]
        assert data["operation"] is None
        mock_resilience_service.reset_metrics.assert_called_once_with(None)

    def test_reset_metrics_specific_operation(self, client, auth_headers, mock_resilience_service):
        """Test POST /resilience/metrics/reset with operation name."""
        response = client.post(
            "/resilience/metrics/reset?operation_name=summarize_text",
            headers=auth_headers
        )
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "summarize_text" in data["message"]
        assert data["operation"] == "summarize_text"
        mock_resilience_service.reset_metrics.assert_called_once_with("summarize_text")


class TestCircuitBreakerEndpoints:
    """Test circuit breaker-related endpoints."""
    
    def test_get_circuit_breaker_status(self, client, auth_headers, mock_resilience_service):
        """Test GET /resilience/circuit-breakers."""
        response = client.get("/resilience/circuit-breakers", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "test_breaker" in data

    def test_get_circuit_breaker_details_success(self, client, auth_headers, mock_resilience_service):
        """Test GET /resilience/circuit-breakers/{breaker_name}."""
        mock_breaker = Mock()
        mock_breaker.state = "closed"
        mock_breaker.failure_count = 2
        mock_breaker.failure_threshold = 5
        mock_breaker.recovery_timeout = 60
        mock_breaker.last_failure_time = None
        # Avoid recursive serialization
        del mock_breaker.metrics  # Remove if exists
        
        mock_resilience_service.circuit_breakers = {"test_breaker": mock_breaker}
        
        response = client.get("/resilience/circuit-breakers/test_breaker", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["name"] == "test_breaker"
        assert data["state"] == "closed"
        assert data["failure_count"] == 2

    def test_get_circuit_breaker_details_not_found(self, client, auth_headers, mock_resilience_service):
        """Test GET /resilience/circuit-breakers/{breaker_name} when breaker doesn't exist."""
        mock_resilience_service.circuit_breakers = {}
        
        response = client.get("/resilience/circuit-breakers/nonexistent", headers=auth_headers)
        
        assert response.status_code == status.HTTP_404_NOT_FOUND
        data = response.json()
        assert "not found" in data["detail"]

    def test_reset_circuit_breaker_success(self, client, auth_headers, mock_resilience_service):
        """Test POST /resilience/circuit-breakers/{breaker_name}/reset."""
        mock_breaker = Mock()
        mock_breaker.state = "closed"
        
        mock_resilience_service.circuit_breakers = {"test_breaker": mock_breaker}
        
        response = client.post("/resilience/circuit-breakers/test_breaker/reset", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "has been reset" in data["message"]
        assert data["name"] == "test_breaker"

    def test_reset_circuit_breaker_not_found(self, client, auth_headers, mock_resilience_service):
        """Test POST /resilience/circuit-breakers/{breaker_name}/reset when breaker doesn't exist."""
        mock_resilience_service.circuit_breakers = {}
        
        response = client.post("/resilience/circuit-breakers/nonexistent/reset", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND


class TestResilienceConfigEndpoint:
    """Test GET /resilience/config endpoint."""
    
    def test_get_resilience_config_success(self, client, auth_headers, mock_resilience_service, mock_text_processor):
        """Test successful config retrieval."""
        # Mock the config structure
        from app.infrastructure.resilience import ResilienceStrategy
        
        mock_config = Mock()
        mock_config.strategy.value = "balanced"
        mock_config.retry_config = Mock()
        mock_config.retry_config.max_attempts = 3
        mock_config.retry_config.max_delay_seconds = 30
        mock_config.retry_config.exponential_multiplier = 1.0
        mock_config.retry_config.exponential_min = 2.0
        mock_config.retry_config.exponential_max = 10.0
        mock_config.retry_config.jitter = True
        mock_config.retry_config.jitter_max = 2.0
        mock_config.circuit_breaker_config = Mock()
        mock_config.circuit_breaker_config.failure_threshold = 5
        mock_config.circuit_breaker_config.recovery_timeout = 60
        mock_config.circuit_breaker_config.half_open_max_calls = 5
        mock_config.enable_circuit_breaker = True
        mock_config.enable_retry = True
        
        mock_resilience_service.configs = {ResilienceStrategy.BALANCED: mock_config}
        
        response = client.get("/resilience/config", headers=auth_headers)
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert "strategies" in data
        assert "operation_strategies" in data


class TestResilienceDashboardEndpoint:
    """Test GET /resilience/dashboard endpoint."""
    
    def test_dashboard_success(self, client, mock_resilience_service):
        """Test successful dashboard retrieval."""
        response = client.get("/resilience/dashboard")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        assert "timestamp" in data
        assert "health" in data
        assert "performance" in data
        assert "operations" in data
        assert "alerts" in data
        assert "summary" in data
        
        # Check calculated values based on mock data
        assert data["performance"]["total_calls"] == 100
        assert data["performance"]["successful_calls"] == 95
        assert data["performance"]["failed_calls"] == 5

    def test_dashboard_with_alerts(self, client, mock_resilience_service):
        """Test dashboard with alert conditions."""
        mock_resilience_service.get_health_status.return_value = {
            "healthy": False,
            "open_circuit_breakers": ["failed_breaker"],
            "half_open_circuit_breakers": [],
            "total_circuit_breakers": 3
        }
        
        mock_resilience_service.get_all_metrics.return_value = {
            "operations": {
                "summarize_text": {
                    "total_calls": 100,
                    "successful_calls": 70,  # Low success rate
                    "failed_calls": 30,
                    "retry_attempts": 50
                }
            },
            "summary": {}
        }
        
        response = client.get("/resilience/dashboard")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        
        # Check that alerts are generated
        alerts = [alert for alert in data["alerts"] if alert is not None]
        assert len(alerts) >= 1
        assert any("Circuit breaker open: failed_breaker" in alert for alert in alerts)

    def test_dashboard_error_handling(self, client, mock_resilience_service):
        """Test dashboard error handling."""
        mock_resilience_service.get_health_status.side_effect = Exception("Health error")
        
        response = client.get("/resilience/dashboard")
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR


class TestAuthenticationProtection:
    """Test authentication requirements for protected endpoints."""
    
    @pytest.mark.parametrize("endpoint", [
        "/resilience/metrics",
        "/resilience/metrics/test_operation",
        "/resilience/circuit-breakers",
        "/resilience/circuit-breakers/test_breaker",
        "/resilience/config"
    ])
    def test_protected_endpoints_require_auth(self, client, endpoint, mock_resilience_service):
        """Test that protected endpoints require authentication."""
        response = client.get(endpoint)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    @pytest.mark.parametrize("endpoint", [
        "/resilience/metrics/reset",
        "/resilience/circuit-breakers/test_breaker/reset"
    ])
    def test_protected_post_endpoints_require_auth(self, client, endpoint, mock_resilience_service):
        """Test that protected POST endpoints require authentication."""
        response = client.post(endpoint)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_optional_auth_endpoints_work_without_auth(self, client, mock_resilience_service, mock_text_processor):
        """Test that optional auth endpoints work without authentication."""
        # These endpoints should work without auth
        response = client.get("/resilience/health")
        assert response.status_code == status.HTTP_200_OK
        
        response = client.get("/resilience/dashboard")
        assert response.status_code == status.HTTP_200_OK


class TestErrorHandling:
    """Test error handling and edge cases."""
    
    def test_invalid_operation_name_in_metrics(self, client, auth_headers, mock_resilience_service):
        """Test handling of invalid operation names."""
        mock_resilience_service.get_metrics.side_effect = KeyError("Operation not found")
        
        response = client.get("/resilience/metrics/invalid_operation", headers=auth_headers)
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_service_unavailable_scenarios(self, client, auth_headers, mock_resilience_service):
        """Test scenarios where resilience service is unavailable."""
        mock_resilience_service.get_all_metrics.side_effect = Exception("Service unavailable")
        
        response = client.get("/resilience/metrics", headers=auth_headers)
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR
        
        response = client.get("/resilience/circuit-breakers", headers=auth_headers)
        assert response.status_code == status.HTTP_500_INTERNAL_SERVER_ERROR

    def test_circuit_breaker_reset_error(self, client, auth_headers, mock_resilience_service):
        """Test error handling in circuit breaker reset."""
        mock_resilience_service.circuit_breakers = {}  # Empty to trigger not found
        
        response = client.post("/resilience/circuit-breakers/test_breaker/reset", headers=auth_headers)
        assert response.status_code == status.HTTP_404_NOT_FOUND

    def test_malformed_auth_header(self, client, mock_resilience_service):
        """Test handling of malformed authorization headers."""
        headers = {"Authorization": "InvalidFormat"}
        response = client.get("/resilience/metrics", headers=headers)
        assert response.status_code == status.HTTP_401_UNAUTHORIZED

    def test_empty_metrics_response(self, client, mock_resilience_service):
        """Test dashboard with empty metrics."""
        mock_resilience_service.get_all_metrics.return_value = {
            "operations": {},
            "summary": {}
        }
        
        response = client.get("/resilience/dashboard")
        
        assert response.status_code == status.HTTP_200_OK
        data = response.json()
        assert data["performance"]["total_calls"] == 0
        assert data["performance"]["success_rate"] == 0