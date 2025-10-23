"""
Unit tests for middleware utility functions.

Tests pure utility functions that don't require HTTP context execution.
Follows behavior-driven testing principles with comprehensive docstrings.
"""

from typing import Callable
from unittest.mock import Mock
from app.core.middleware import is_health_check_request


class TestIsHealthCheckRequest:
    """
    Test suite for health check request detection functionality.

    Scope:
        - Path pattern matching for health check endpoints
        - User agent based detection for monitoring probes
        - Kubernetes health check identification
        - Health endpoint prefix matching

    Business Critical:
        Health check detection enables optimized logging and monitoring behavior
        for automated probes while maintaining full observability for user traffic.

    Test Strategy:
        - Unit tests for pure pattern matching logic (no HTTP execution)
        - Coverage of all documented health check patterns
        - Verification of non-health check rejection
        - User agent based detection for container orchestration

    Contract Reference:
        Tests verify behavior documented in `backend/contracts/core/middleware/__init__.pyi`
        for `is_health_check_request(request: Request) -> bool`

    External Dependencies:
        - Mock Request objects (system boundary for HTTP context)

    Known Limitations:
        - Tests only verify detection logic, not middleware logging behavior
        - Header normalization (case sensitivity) not tested here
    """

    def test_exact_health_path_match(self, create_mock_request: Callable[..., Mock]) -> None:
        """
        Test that exact /health path is correctly identified as health check.

        Verifies:
            Direct /health endpoint requests return True per contract

        Business Impact:
            Ensures standard health check endpoints receive optimized processing
            for monitoring systems and load balancers

        Scenario:
            Given: Request with exact path "/health"
            When: Health check detection is performed
            Then: Request is identified as health check (True)

        Edge Cases Covered:
            - Exact path matching (no prefix/suffix variations)
            - Root health endpoint pattern

        Related Tests:
            - test_health_prefix_match: Tests /health/* variations
            - test_exact_healthz_path_match: Tests alternative health endpoint
        """
        # Given: Request with exact health path
        request = create_mock_request(path="/health")

        # When: Health check detection is performed
        result = is_health_check_request(request)

        # Then: Request is identified as health check
        assert result is True, "Exact /health path should be identified as health check"

    def test_exact_healthz_path_match(self, create_mock_request: Callable[..., Mock]) -> None:
        """
        Test that exact /healthz path is correctly identified as health check.

        Verifies:
            Kubernetes-style /healthz endpoint requests return True per contract

        Business Impact:
            Ensures compatibility with Kubernetes health check conventions
            for container orchestration and service discovery

        Scenario:
            Given: Request with exact path "/healthz"
            When: Health check detection is performed
            Then: Request is identified as health check (True)

        Edge Cases Covered:
            - Kubernetes health check convention
            - Alternative health endpoint naming
            - Container orchestration compatibility

        Related Tests:
            - test_exact_health_path_match: Tests standard health endpoint
            - test_kube_probe_user_agent: Tests Kubernetes user agent detection
        """
        # Given: Request with Kubernetes-style health path
        request = create_mock_request(path="/healthz")

        # When: Health check detection is performed
        result = is_health_check_request(request)

        # Then: Request is identified as health check
        assert result is True, "Exact /healthz path should be identified as health check"

    def test_health_prefix_match(self, create_mock_request: Callable[..., Mock]) -> None:
        """
        Test that /health/* prefix paths are correctly identified as health checks.

        Verifies:
            Health endpoint sub-paths return True per prefix matching contract

        Business Impact:
            Supports detailed health endpoints (e.g., /health/detailed) while
            maintaining consistent health check detection behavior

        Scenario:
            Given: Request with path starting with "/health/"
            When: Health check detection is performed
            Then: Request is identified as health check (True)

        Edge Cases Covered:
            - Prefix matching behavior
            - Sub-path health endpoints
            - Health endpoint hierarchies

        Related Tests:
            - test_exact_health_path_match: Tests root health endpoint
            - test_ping_status_paths: Tests other health endpoint variations
        """
        # Given: Request with health prefix path
        request = create_mock_request(path="/health/detailed")

        # When: Health check detection is performed
        result = is_health_check_request(request)

        # Then: Request is identified as health check
        assert result is True, "Paths starting with /health/ should be identified as health checks"

    def test_kube_probe_user_agent(self, create_mock_request: Callable[..., Mock]) -> None:
        """
        Test that kube-probe user agent triggers health check detection.

        Verifies:
            Requests with "kube-probe" user agent are identified as health checks

        Business Impact:
            Ensures Kubernetes liveness and readiness probes are properly
            identified for optimized processing regardless of request path

        Scenario:
            Given: Request with "kube-probe" user agent header
            When: Health check detection is performed
            Then: Request is identified as health check (True)

        Edge Cases Covered:
            - User agent based detection
            - Kubernetes probe identification
            - Container orchestration monitoring

        Related Tests:
            - test_exact_health_path_match: Tests path-based detection
            - test_non_health_check_path: Tests rejection of regular requests
        """
        # Given: Request with Kubernetes probe user agent
        request = create_mock_request(path="/", headers={"user-agent": "kube-probe/1.0"})

        # When: Health check detection is performed
        result = is_health_check_request(request)

        # Then: Request is identified as health check
        assert result is True, "Requests with kube-probe user agent should be identified as health checks"

    def test_non_health_check_path(self, create_mock_request: Callable[..., Mock]) -> None:
        """
        Test that non-health check paths are correctly rejected.

        Verifies:
            Regular API endpoints return False per negative matching contract

        Business Impact:
            Prevents accidental health check classification of user traffic,
            ensuring full logging and monitoring for legitimate requests

        Scenario:
            Given: Request with non-health API path
            When: Health check detection is performed
            Then: Request is NOT identified as health check (False)

        Edge Cases Covered:
            - Negative matching behavior
            - API endpoint classification
            - False positive prevention

        Related Tests:
            - test_exact_health_path_match: Tests positive matching
            - test_health_prefix_match: Tests prefix matching
        """
        # Given: Request with non-health API path
        request = create_mock_request(path="/v1/api/data")

        # When: Health check detection is performed
        result = is_health_check_request(request)

        # Then: Request is NOT identified as health check
        assert result is False, "Non-health API paths should not be identified as health checks"

    def test_ping_status_paths(self, create_mock_request: Callable[..., Mock]) -> None:
        """
        Test that common health check path variations are correctly identified.

        Verifies:
            Alternative health endpoints (/ping, /status, /readiness, /liveness)
            are correctly identified as health checks per contract

        Business Impact:
            Ensures compatibility with various monitoring systems and health
            check conventions across different platforms and frameworks

        Scenario:
            Given: Request with common health check path variations
            When: Health check detection is performed for each path
            Then: All requests are identified as health checks (True)

        Edge Cases Covered:
            - Multiple health endpoint conventions
            - Readiness/liveness probe patterns
            - Cross-platform compatibility

        Contract Reference:
            Verifies all documented health check path patterns are supported

        Related Tests:
            - test_exact_health_path_match: Tests primary health endpoint
            - test_kube_probe_user_agent: Tests Kubernetes-specific detection
        """
        # Given: Common health check path variations
        health_paths = ["/ping", "/status", "/readiness", "/liveness"]

        # When/Then: Each path should be identified as health check
        for path in health_paths:
            request = create_mock_request(path=path)
            result = is_health_check_request(request)
            assert result is True, f"Path {path} should be identified as health check"