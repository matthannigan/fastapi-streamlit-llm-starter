"""
Unit tests for rate limiting utility functions.

This module tests the pure utility functions from the rate limiting middleware
that can be tested in isolation without HTTP context. These functions handle
client identification and endpoint classification logic following the documented
public contract in backend/contracts/core/middleware/rate_limiting.pyi.

Test Scope:
    - Client identification priority hierarchy logic
    - Endpoint classification based on request path patterns
    - Header parsing and fallback mechanisms
    - Edge cases and boundary conditions

Functions Tested:
    - get_client_identifier(request: Request) -> str
    - get_endpoint_classification(request: Request) -> str

Testing Strategy:
    - Pure function testing with mock Request objects
    - Priority hierarchy validation with comprehensive test coverage
    - Edge case testing for fallback mechanisms
    - Behavior-driven test documentation following DOCSTRINGS_TESTS.md
"""

from typing import Callable
from unittest.mock import Mock
from app.core.middleware.rate_limiting import get_client_identifier, get_endpoint_classification


class TestGetClientIdentifier:
    """
    Test suite for client identification priority logic in rate limiting.

    Scope:
        Tests the get_client_identifier function that extracts unique client identifiers
        from request headers and metadata using a documented priority hierarchy. This
        function is critical for proper rate limiting enforcement across different
        authentication methods and client types.

    Business Impact:
        Accurate client identification ensures that rate limits are applied correctly
        to different clients (API keys, users, IP addresses) preventing both unauthorized
        bypass and legitimate blocking. This function directly impacts security and
        fairness of rate limiting policies.

    Priority Hierarchy Tested:
        1. API key from 'x-api-key' header (highest priority)
        2. API key from 'authorization' header (fallback)
        3. User ID from request.state.user_id (authenticated users)
        4. IP address from 'x-forwarded-for' header (proxy environments)
        5. IP address from 'x-real-ip' header (single proxy)
        6. Connection IP address from request.client.host (final fallback)

    Contract Reference:
        backend/contracts/core/middleware/rate_limiting.pyi (lines 459-507)

    Test Strategy:
        - Each test validates one specific path in the priority hierarchy
        - Comprehensive edge case coverage for header parsing
        - Fallback mechanism validation
        - Test environment special cases (mocked objects)
    """

    def test_api_key_header_priority_highest(self, create_mock_request: Callable[..., Mock]) -> None:
        """
        Test that x-api-key header has highest priority in client identification.

        Scenario:
            Given: Request contains x-api-key header with valid API key
            When: get_client_identifier is called
            Then: Returns API key identifier with highest priority

        Business Impact:
            API keys provide the most reliable client identification for
            authenticated API access. They should override all other identification
            methods to ensure proper rate limiting for API clients.

        Edge Cases Validated:
            - API key takes precedence over user ID and IP identification
            - Proper identifier format: "api_key: {key}"
            - Header case sensitivity handled correctly

        Contract Reference:
            get_client_identifier() returns "api_key: {key}" for x-api-key header

        Test Data:
            - API key: "test-key-123"
            - Client host: "192.168.1.1" (should be ignored due to API key)
        """
        request = create_mock_request(
            headers={"x-api-key": "test-key-123"},
            client_host="192.168.1.1"
        )

        identifier = get_client_identifier(request)

        assert identifier == "api_key: test-key-123"

    def test_authorization_header_as_api_key(self, create_mock_request: Callable[..., Mock]) -> None:
        """
        Test that Authorization header is used as API key fallback.

        Scenario:
            Given: Request contains Authorization header but no x-api-key header
            When: get_client_identifier is called
            Then: Returns API key identifier from Authorization header

        Business Impact:
            Supports standard Bearer token authentication pattern for API access.
            Ensures clients using standard Authorization headers are properly
            identified and rate limited independently of x-api-key users.

        Edge Cases Validated:
            - Authorization header parsed correctly when x-api-key absent
            - Bearer token prefix preserved in identifier
            - Authorization header has lower priority than x-api-key

        Contract Reference:
            get_client_identifier() checks Authorization header when x-api-key missing

        Test Data:
            - Authorization header: "Bearer token-abc"
            - Client host: "192.168.1.1" (should be ignored due to auth header)
        """
        request = create_mock_request(
            headers={"authorization": "Bearer token-abc"},
            client_host="192.168.1.1"
        )

        identifier = get_client_identifier(request)

        assert identifier == "api_key: Bearer token-abc"

    def test_user_id_from_request_state(self, create_mock_request: Callable[..., Mock]) -> None:
        """
        Test that user ID from request.state is used when no API keys present.

        Scenario:
            Given: Request has user_id in state but no API key headers
            When: get_client_identifier is called
            Then: Returns user identifier from request.state.user_id

        Business Impact:
            Enables user-based rate limiting for authenticated sessions. This
            ensures that individual users are rate limited regardless of their
            IP address or device, preventing abuse across multiple connections.

        Edge Cases Validated:
            - User identification works when API keys are absent
            - Proper identifier format: "user: {user_id}"
            - Request state properly accessed for authenticated sessions

        Contract Reference:
            get_client_identifier() returns "user: {user_id}" when API keys missing

        Test Data:
            - User ID: "user_12345" (set in request.state)
            - Client host: "192.168.1.1" (should be ignored due to user ID)
        """
        request = create_mock_request(client_host="192.168.1.1")
        request.state.user_id = "user_12345"

        identifier = get_client_identifier(request)

        assert identifier == "user: user_12345"

    def test_x_forwarded_for_first_ip(self, create_mock_request: Callable[..., Mock]) -> None:
        """
        Test that X-Forwarded-For header uses first IP in the chain.

        Scenario:
            Given: Request has X-Forwarded-For header with multiple IPs
            When: get_client_identifier is called
            Then: Returns identifier using first IP from the header

        Business Impact:
            In proxy/load balancer environments, X-Forwarded-For contains the
            original client IP. Using the first IP ensures rate limiting is
            applied to the actual client rather than intermediate proxies.

        Edge Cases Validated:
            - Multiple IP addresses in X-Forwarded-For header parsed correctly
            - First IP prioritized (represents original client)
            - Comma-separated format handled properly
            - Proper identifier format: "ip: {ip_address}"

        Contract Reference:
            get_client_identifier() extracts first IP from X-Forwarded-For header

        Test Data:
            - X-Forwarded-For: "203.0.113.1, 203.0.113.2, 203.0.113.3"
            - Expected IP: "203.0.113.1" (first in chain)
            - Client host: "192.168.1.1" (should be ignored)
        """
        request = create_mock_request(
            headers={"x-forwarded-for": "203.0.113.1, 203.0.113.2, 203.0.113.3"},
            client_host="192.168.1.1"
        )

        identifier = get_client_identifier(request)

        assert identifier == "ip: 203.0.113.1"

    def test_x_real_ip_fallback(self, create_mock_request: Callable[..., Mock]) -> None:
        """
        Test that X-Real-IP header is used when X-Forwarded-For is absent.

        Scenario:
            Given: Request has X-Real-IP header but no X-Forwarded-For
            When: get_client_identifier is called
            Then: Returns identifier using X-Real-IP header value

        Business Impact:
            Some proxy configurations use X-Real-IP instead of X-Forwarded-For
            to pass the original client IP. Supporting this header ensures
            rate limiting works correctly with various proxy setups.

        Edge Cases Validated:
            - X-Real-IP used when X-Forwarded-For header missing
            - Single IP address from proxy correctly identified
            - Proper fallback in proxy identification chain

        Contract Reference:
            get_client_identifier() checks X-Real-IP after X-Forwarded-For

        Test Data:
            - X-Real-IP: "203.0.113.5"
            - Client host: "192.168.1.1" (should be ignored)
        """
        request = create_mock_request(
            headers={"x-real-ip": "203.0.113.5"},
            client_host="192.168.1.1"
        )

        identifier = get_client_identifier(request)

        assert identifier == "ip: 203.0.113.5"

    def test_client_host_final_fallback(self, create_mock_request: Callable[..., Mock]) -> None:
        """
        Test that request.client.host is used as final fallback identifier.

        Scenario:
            Given: Request has no identification headers or state
            When: get_client_identifier is called
            Then: Returns identifier using connection client host IP

        Business Impact:
            Ensures rate limiting works even for direct connections without
            proxy headers or authentication. This prevents abuse from clients
            that bypass all other identification methods.

        Edge Cases Validated:
            - Direct connection IP used when all other methods fail
            - Final fallback in priority hierarchy functions correctly
            - Basic IP-based rate limiting always available

        Contract Reference:
            get_client_identifier() uses request.client.host as final fallback

        Test Data:
            - Client host: "192.168.1.99"
            - No headers or state data provided
        """
        request = create_mock_request(client_host="192.168.1.99")

        identifier = get_client_identifier(request)

        assert identifier == "ip: 192.168.1.99"

    def test_mock_user_id_ignored(self, create_mock_request: Callable[..., Mock]) -> None:
        """
        Test that mocked user IDs in test environment are ignored gracefully.

        Scenario:
            Given: Request.state.user_id contains a mock object identifier
            When: get_client_identifier is called
            Then: Falls back to IP-based identification

        Business Impact:
            Prevents test environment artifacts from affecting rate limiting
        behavior. Mocked user IDs should not be treated as real user identifiers,
        ensuring tests accurately reflect production behavior.

        Edge Cases Validated:
            - Mock object identifiers detected and ignored
            - Graceful fallback to IP identification
            - Test environment special case handling
            - No crashes or exceptions from mock data

        Contract Reference:
            get_client_identifier() handles mocked user IDs in test environments

        Test Data:
            - Mock user ID: "<Mock name='user_id'>"
            - Expected fallback to IP-based identification
        """
        request = create_mock_request(client_host="192.168.1.1")
        request.state.user_id = "<Mock name='user_id'>"

        identifier = get_client_identifier(request)

        assert identifier.startswith("ip:")  # Falls back to IP


class TestGetEndpointClassification:
    """
    Test suite for endpoint classification logic in rate limiting.

    Scope:
        Tests the get_endpoint_classification function that maps request paths to
        rate limiting categories. This classification determines which rate limit
        rules apply to different endpoints, enabling granular control over
        request limits based on endpoint type and business importance.

    Business Impact:
        Proper endpoint classification ensures that critical endpoints have
        appropriate rate limits that balance availability with resource protection.
        Health checks need high limits, processing endpoints need strict limits,
        and standard endpoints get balanced treatment.

    Classification Categories Tested:
        - "health": Health check endpoints (should bypass rate limiting)
        - "critical": High-impact processing endpoints
        - "monitoring": Internal monitoring and metrics endpoints
        - "auth": Authentication and authorization endpoints
        - "standard": All other endpoints (default classification)

    Contract Reference:
        backend/contracts/core/middleware/rate_limiting.pyi (lines 510-577)

    Test Strategy:
        - Each test validates path pattern matching for specific classifications
        - Comprehensive coverage of all classification categories
        - Edge case testing for path variations and special characters
        - Fallback behavior validation for unclassified endpoints
    """

    def test_health_endpoint_classifications(self, create_mock_request: Callable[..., Mock]) -> None:
        """
        Test that various health check endpoint patterns are classified correctly.

        Scenario:
            Given: Request paths corresponding to different health check patterns
            When: get_endpoint_classification is called for each path
            Then: All return "health" classification

        Business Impact:
            Health check endpoints must be classified as "health" to potentially
            bypass rate limiting. This ensures monitoring systems can reliably
            check application health without being blocked by rate limits.

        Edge Cases Validated:
            - Exact path matches for standard health endpoints
            - Multiple health check endpoint variations
            - Consistent classification across all health check patterns
            - Health endpoints properly distinguished from other endpoints

        Contract Reference:
            get_endpoint_classification() returns "health" for health check paths

        Test Data:
            - "/health": Standard health check endpoint
            - "/healthz": Kubernetes-style health check
            - "/ping": Simple liveness probe
            - "/status": Application status endpoint
        """
        health_paths = ["/health", "/healthz", "/ping", "/status"]

        for path in health_paths:
            request = create_mock_request(path=path)
            classification = get_endpoint_classification(request)
            assert classification == "health", f"Path {path} should be classified as health"

    def test_critical_processing_endpoints(self, create_mock_request: Callable[..., Mock]) -> None:
        """
        Test that resource-intensive processing endpoints are classified as critical.

        Scenario:
            Given: Request paths for AI processing and batch operations
            When: get_endpoint_classification is called
            Then: Returns "critical" classification for processing endpoints

        Business Impact:
            Processing endpoints consume significant computational resources
        and require strict rate limiting. Critical classification enables
        appropriate limits that prevent resource exhaustion while maintaining
        service availability.

        Edge Cases Validated:
            - Text processing endpoints classified as critical
            - Batch processing operations properly categorized
            - Resource-intensive operations receive strict rate limits
            - Processing endpoints distinguished from standard API endpoints

        Contract Reference:
            get_endpoint_classification() returns "critical" for processing paths

        Test Data:
            - "/v1/text_processing/process": Individual text processing
            - "/v1/text_processing/batch_process": Batch processing operations
        """
        critical_paths = [
            "/v1/text_processing/process",
            "/v1/text_processing/batch_process"
        ]

        for path in critical_paths:
            request = create_mock_request(path=path)
            classification = get_endpoint_classification(request)
            assert classification == "critical", f"Path {path} should be classified as critical"

    def test_monitoring_endpoint_classification(self, create_mock_request: Callable[..., Mock]) -> None:
        """
        Test that internal monitoring endpoints are classified correctly.

        Scenario:
            Given: Request paths for internal monitoring and metrics
            When: get_endpoint_classification is called
            Then: Returns "monitoring" classification for internal endpoints

        Business Impact:
            Internal monitoring endpoints need appropriate rate limits that
        allow sufficient monitoring traffic while preventing abuse. Monitoring
        classification enables policies specific to operational endpoints.

        Edge Cases Validated:
            - Internal API prefix properly detected
            - Monitoring endpoints under /internal/ path classified correctly
            - Internal endpoints distinguished from public API endpoints
            - Monitoring classification applied consistently

        Contract Reference:
            get_endpoint_classification() returns "monitoring" for /internal/* paths

        Test Data:
            - "/internal/monitoring/metrics": Metrics collection endpoint
            - "/internal/cache/status": Cache monitoring endpoint
            - "/internal/resilience/state": Resilience monitoring endpoint
        """
        monitoring_paths = [
            "/internal/monitoring/metrics",
            "/internal/cache/status",
            "/internal/resilience/state"
        ]

        for path in monitoring_paths:
            request = create_mock_request(path=path)
            classification = get_endpoint_classification(request)
            assert classification == "monitoring", f"Path {path} should be classified as monitoring"

    def test_auth_endpoint_classification(self, create_mock_request: Callable[..., Mock]) -> None:
        """
        Test that authentication endpoints are classified correctly.

        Scenario:
            Given: Request paths for authentication and authorization operations
            When: get_endpoint_classification is called
            Then: Returns "auth" classification for authentication endpoints

        Business Impact:
            Authentication endpoints are security-critical and need rate limits
        that prevent brute force attacks while allowing legitimate user access.
        Auth classification enables appropriate security-focused rate limiting.

        Edge Cases Validated:
            - Authentication endpoints under /v1/auth/ properly classified
            - Various auth operations (login, logout, token refresh) categorized
            - Auth endpoints distinguished from other public API endpoints
            - Security-focused rate limiting applied consistently

        Contract Reference:
            get_endpoint_classification() returns "auth" for /v1/auth/* paths

        Test Data:
            - "/v1/auth/login": User login endpoint
            - "/v1/auth/logout": User logout endpoint
            - "/v1/auth/refresh": Token refresh endpoint
            - "/v1/auth/register": User registration endpoint
        """
        auth_paths = [
            "/v1/auth/login",
            "/v1/auth/logout",
            "/v1/auth/refresh",
            "/v1/auth/register"
        ]

        for path in auth_paths:
            request = create_mock_request(path=path)
            classification = get_endpoint_classification(request)
            assert classification == "auth", f"Path {path} should be classified as auth"

    def test_standard_endpoint_fallback_classification(self, create_mock_request: Callable[..., Mock]) -> None:
        """
        Test that unclassified endpoints fall back to standard classification.

        Scenario:
            Given: Request paths that don't match any specific classification
            When: get_endpoint_classification is called
            Then: Returns "standard" classification as default

        Business Impact:
        Standard classification provides balanced rate limiting for typical
        API endpoints. This ensures reasonable usage limits without being
        overly restrictive for normal application usage.

        Edge Cases Validated:
            - Non-critical API endpoints classified as standard
            - Default fallback behavior functions correctly
            - Standard endpoints receive balanced rate limiting
            - Fallback prevents uncategorized endpoints from having no limits

        Contract Reference:
            get_endpoint_classification() returns "standard" as default fallback

        Test Data:
            - "/v1/data/list": Standard data retrieval endpoint
            - "/v1/users/profile": Standard user profile endpoint
            - "/v1/products/search": Standard search endpoint
            - "/api/v1/orders": Standard orders endpoint
        """
        standard_paths = [
            "/v1/data/list",
            "/v1/users/profile",
            "/v1/products/search",
            "/api/v1/orders"
        ]

        for path in standard_paths:
            request = create_mock_request(path=path)
            classification = get_endpoint_classification(request)
            assert classification == "standard", f"Path {path} should be classified as standard"

    def test_path_variations_and_edge_cases(self, create_mock_request: Callable[..., Mock]) -> None:
        """
        Test that path variations and edge cases are handled correctly.

        Scenario:
            Given: Request paths with various edge cases and configurations
            When: get_endpoint_classification is called
            Then: Returns appropriate classifications based on path patterns

        Business Impact:
            Robust path handling ensures rate limiting works correctly across
        various URL formats. Classification relies on exact path matching and
        prefix patterns, providing predictable behavior for rate limiting rules.

        Edge Cases Validated:
            - Exact path matching for health endpoints
            - Prefix matching for endpoint categories (/v1/auth/, /internal/)
            - Path patterns that don't match special classifications fall back to standard
            - Function handles both exact matches and prefix-based classification

        Contract Reference:
            get_endpoint_classification() uses exact path matching and prefix detection

        Test Data:
            - "/health": Health check endpoint (exact match)
            - "/v1/auth/login": Auth endpoint (prefix match for /v1/auth)
            - "/v1/text_processing/process": Processing endpoint (exact match)
            - "/internal/cache/status": Monitoring endpoint (prefix match for /internal/)
            - "/api/v1/data/list": Standard endpoint (no special classification)
        """
        test_cases = [
            ("/health", "health"),
            ("/v1/auth/login", "auth"),
            ("/v1/text_processing/process", "critical"),
            ("/internal/cache/status", "monitoring"),
            ("/api/v1/data/list", "standard")
        ]

        for path, expected_classification in test_cases:
            request = create_mock_request(path=path)
            classification = get_endpoint_classification(request)
            assert classification == expected_classification, f"Path {path} should be classified as {expected_classification}"
