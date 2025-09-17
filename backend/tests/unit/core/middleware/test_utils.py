"""
Tests for core middleware utility functions.
"""
import pytest
from unittest.mock import Mock, patch
from fastapi import Request

from app.core.middleware import (
    get_request_id,
    get_request_duration,
    add_response_headers,
    is_health_check_request,
)


class TestMiddlewareUtilities:
    """Test middleware utility functions."""

    def test_get_request_id_from_state(self):
        """Test getting request ID from request state."""
        request = Mock(spec=Request)
        request.state.request_id = "test-request-123"

        request_id = get_request_id(request)
        assert request_id == "test-request-123"

    def test_get_request_id_from_context(self):
        """Test getting request ID from context when not in state."""
        request = Mock(spec=Request)
        request.state = Mock(spec=[])  # Empty spec, no attributes

        with patch('app.core.middleware.request_id_context') as mock_context:
            mock_context.get.return_value = "context-request-456"

            request_id = get_request_id(request)
            assert request_id == "context-request-456"

    def test_get_request_duration_valid(self):
        """Test getting request duration with valid timing."""
        request = Mock(spec=Request)

        with patch('app.core.middleware.request_start_time_context') as mock_context, \
             patch('time.time') as mock_time:

            mock_context.get.return_value = 1000.0  # Start time
            mock_time.return_value = 1002.5  # Current time (2.5s later)

            duration = get_request_duration(request)
            assert duration == 2500.0  # 2.5 seconds in milliseconds

    def test_get_request_duration_no_timing(self):
        """Test getting request duration without timing information."""
        request = Mock(spec=Request)

        with patch('app.core.middleware.request_start_time_context') as mock_context:
            mock_context.get.return_value = 0.0  # No valid start time

            duration = get_request_duration(request)
            assert duration is None

    def test_add_response_headers(self):
        """Test adding custom headers to response."""
        from fastapi import Response

        response = Response()
        headers_to_add = {
            "X-Custom-Header": "custom-value",
            "X-API-Version": "1.0",
            "X-Request-ID": "req-123"
        }

        add_response_headers(response, headers_to_add)

        assert response.headers["X-Custom-Header"] == "custom-value"
        assert response.headers["X-API-Version"] == "1.0"
        assert response.headers["X-Request-ID"] == "req-123"

    def test_add_response_headers_skip_restricted(self):
        """Test that restricted headers are not added."""
        from fastapi import Response

        response = Response()
        response.headers["content-type"] = "application/json"
        response.headers["content-length"] = "100"

        headers_to_add = {
            "content-type": "text/plain",  # Should be skipped
            "content-length": "200",       # Should be skipped
            "X-Custom": "allowed"          # Should be added
        }

        add_response_headers(response, headers_to_add)

        # Original headers should be preserved
        assert response.headers["content-type"] == "application/json"
        assert response.headers["content-length"] == "100"
        # Custom header should be added
        assert response.headers["X-Custom"] == "allowed"

    def test_is_health_check_request_health_paths(self):
        """Test health check detection for standard health paths."""
        health_paths = ["/health", "/healthz", "/ping", "/status", "/readiness", "/liveness"]

        for path in health_paths:
            request = Mock(spec=Request)
            request.url = Mock()
            request.url.path = path
            request.headers = {}

            assert is_health_check_request(request) == True, f"Should detect {path} as health check"

    def test_is_health_check_request_health_prefix(self):
        """Test health check detection for paths starting with /health."""
        health_prefix_paths = ["/health/live", "/health/ready", "/health/status"]

        for path in health_prefix_paths:
            request = Mock(spec=Request)
            request.url = Mock()
            request.url.path = path
            request.headers = {}

            assert is_health_check_request(request) == True, f"Should detect {path} as health check"

    def test_is_health_check_request_user_agent(self):
        """Test health check detection based on User-Agent header."""
        health_user_agents = ["kube-probe/1.0", "health-checker", "Kube-Probe/2.1"]

        for user_agent in health_user_agents:
            request = Mock(spec=Request)
            request.url = Mock()
            request.url.path = "/api/endpoint"
            request.headers = {"user-agent": user_agent}

            assert is_health_check_request(request) == True, f"Should detect {user_agent} as health check"

    def test_is_health_check_request_regular_request(self):
        """Test that regular requests are not detected as health checks."""
        request = Mock(spec=Request)
        request.url = Mock()
        request.url.path = "/api/users"
        request.headers = {"user-agent": "Mozilla/5.0"}

        assert is_health_check_request(request) == False
