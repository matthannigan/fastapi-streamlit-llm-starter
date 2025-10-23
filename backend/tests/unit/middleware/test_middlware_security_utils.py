from typing import Callable
from unittest.mock import Mock
from app.core.middleware.security import SecurityMiddleware
from app.core.config import create_settings


class TestIsDocsEndpoint:
    """
    Test suite for SecurityMiddleware documentation endpoint detection functionality.

    Scope:
        Tests the _is_docs_endpoint() method which determines whether HTTP requests
        should receive relaxed Content Security Policy (CSP) headers suitable for
        documentation interfaces like Swagger UI and ReDoc.

    Business Critical:
        Documentation endpoints require relaxed CSP policies to function properly,
        while API endpoints need strict CSP policies for security. Incorrect classification
        can break documentation interfaces or compromise API security.

    Contract Reference:
        Tests validate the behavior documented in:
        backend/contracts/core/middleware/security.pyi - SecurityMiddleware._is_docs_endpoint()

    Test Strategy:
        - Unit tests for pure path pattern matching logic
        - Edge case testing for various documentation endpoint patterns
        - Negative testing to ensure API endpoints are not misclassified
        - Integration-independent testing using mock Request objects

    Security Implications:
        Proper CSP policy selection prevents XSS attacks while ensuring documentation
        interfaces can load necessary JavaScript and CSS resources.

    External Dependencies:
        - FastAPI Request: HTTP request object (mocked with spec)
        - SecurityMiddleware: Real middleware instance with default settings
        - Mock ASGI app: For middleware initialization
    """

    def test_exact_docs_path(self, mock_app: Mock, create_mock_request: Callable[..., Mock]) -> None:
        """
        Test that exact /docs path is correctly identified as documentation endpoint.

        Behavior Verified:
            Direct requests to Swagger UI documentation interface are detected
            and will receive relaxed CSP policies for proper functionality.

        Business Impact:
            Ensures Swagger UI documentation interface is accessible to developers
            and API consumers for API exploration and testing.

        Test Scenario:
            Given: HTTP request with exact path "/docs"
            When: _is_docs_endpoint() is called
            Then: Returns True indicating documentation endpoint

        Security Policy Applied:
            Relaxed CSP allowing inline scripts and styles necessary for Swagger UI

        Related Tests:
            - test_docs_prefix_match(): Tests subpaths under /docs
            - test_api_endpoint_not_docs(): Ensures API endpoints not misclassified
        """
        middleware = SecurityMiddleware(mock_app, create_settings())
        request = create_mock_request(path="/docs")

        assert middleware._is_docs_endpoint(request) is True

    def test_exact_redoc_path(self, mock_app: Mock, create_mock_request: Callable[..., Mock]) -> None:
        """
        Test that exact /redoc path is correctly identified as documentation endpoint.

        Behavior Verified:
            Direct requests to ReDoc documentation interface are detected
            and will receive relaxed CSP policies for proper functionality.

        Business Impact:
            Ensures ReDoc documentation interface is accessible as an alternative
            to Swagger UI for API documentation and exploration.

        Test Scenario:
            Given: HTTP request with exact path "/redoc"
            When: _is_docs_endpoint() is called
            Then: Returns True indicating documentation endpoint

        Documentation Interface:
            ReDoc provides an alternative, more modern API documentation interface
            compared to traditional Swagger UI.

        Related Tests:
            - test_redoc_prefix_match(): Tests subpaths under /redoc
            - test_exact_docs_path(): Tests Swagger UI endpoint detection
        """
        middleware = SecurityMiddleware(mock_app, create_settings())
        request = create_mock_request(path="/redoc")

        assert middleware._is_docs_endpoint(request) is True

    def test_exact_openapi_path(self, mock_app: Mock, create_mock_request: Callable[..., Mock]) -> None:
        """
        Test that exact /openapi.json path is correctly identified as documentation endpoint.

        Behavior Verified:
            Direct requests to OpenAPI schema file are detected and will receive
            relaxed CSP policies to allow documentation tools to fetch the schema.

        Business Impact:
            Enables API clients and documentation tools to retrieve the OpenAPI
            specification for automatic client generation and API documentation.

        Test Scenario:
            Given: HTTP request with exact path "/openapi.json"
            When: _is_docs_endpoint() is called
            Then: Returns True indicating documentation endpoint

        OpenAPI Specification:
            The /openapi.json endpoint provides the machine-readable API specification
            used by documentation generators, client SDKs, and API testing tools.

        Related Tests:
            - test_openapi_in_path(): Tests paths containing 'openapi' in other locations
            - test_api_endpoint_not_docs(): Ensures regular API endpoints not misclassified
        """
        middleware = SecurityMiddleware(mock_app, create_settings())
        request = create_mock_request(path="/openapi.json")

        assert middleware._is_docs_endpoint(request) is True

    def test_docs_prefix_match(self, mock_app: Mock, create_mock_request: Callable[..., Mock]) -> None:
        """
        Test that paths starting with /docs are correctly identified as documentation endpoints.

        Behavior Verified:
            Subpaths under /docs directory are detected as documentation endpoints,
            including OAuth redirect URLs and other Swagger UI resources.

        Business Impact:
            Ensures complete Swagger UI functionality works properly, including
            OAuth authentication flows and static resource loading.

        Test Scenario:
            Given: HTTP request with path "/docs/oauth2-redirect"
            When: _is_docs_endpoint() is called
            Then: Returns True indicating documentation endpoint

        Edge Case Covered:
            OAuth redirect URLs used in Swagger UI authentication flows must
            receive relaxed CSP policies to complete the authentication process.

        Security Consideration:
            All /docs/* paths are trusted as documentation interfaces and receive
            relaxed CSP policies, which is acceptable in controlled environments.

        Related Tests:
            - test_exact_docs_path(): Tests root docs endpoint
            - test_redoc_prefix_match(): Tests ReDoc subpath matching
        """
        middleware = SecurityMiddleware(mock_app, create_settings())
        request = create_mock_request(path="/docs/oauth2-redirect")

        assert middleware._is_docs_endpoint(request) is True

    def test_redoc_prefix_match(self, mock_app: Mock, create_mock_request: Callable[..., Mock]) -> None:
        """
        Test that paths starting with /redoc are correctly identified as documentation endpoints.

        Behavior Verified:
            Subpaths under /redoc directory are detected as documentation endpoints,
            including static JavaScript and CSS resources required by ReDoc interface.

        Business Impact:
            Ensures complete ReDoc functionality works properly, including
            static resource loading and interface rendering.

        Test Scenario:
            Given: HTTP request with path "/redoc/static/redoc.standalone.js"
            When: _is_docs_endpoint() is called
            Then: Returns True indicating documentation endpoint

        Edge Case Covered:
            Static JavaScript resources for ReDoc require relaxed CSP policies
            to load and execute properly in the browser.

        Resource Loading:
            ReDoc interface depends on external JavaScript files for functionality,
            which would be blocked by strict CSP policies.

        Related Tests:
            - test_exact_redoc_path(): Tests root ReDoc endpoint
            - test_docs_prefix_match(): Tests Swagger UI subpath matching
        """
        middleware = SecurityMiddleware(mock_app, create_settings())
        request = create_mock_request(path="/redoc/static/redoc.standalone.js")

        assert middleware._is_docs_endpoint(request) is True

    def test_internal_path_match(self, mock_app: Mock, create_mock_request: Callable[..., Mock]) -> None:
        """
        Test that internal documentation paths are correctly identified as documentation endpoints.

        Behavior Verified:
            Internal API documentation endpoints (like /internal/docs) are detected
            as documentation endpoints and receive relaxed CSP policies.

        Business Impact:
            Ensures internal documentation interfaces for administrators and
            developers remain accessible and functional.

        Test Scenario:
            Given: HTTP request with path "/internal/docs"
            When: _is_docs_endpoint() is called
            Then: Returns True indicating documentation endpoint

        Internal API Context:
            Internal endpoints provide administrative interfaces for system
            monitoring, configuration, and internal tooling.

        Security Boundary:
            Internal documentation endpoints are still considered trusted
            documentation interfaces despite being in the internal API namespace.

        Related Tests:
            - test_exact_docs_path(): Tests public docs endpoint
            - test_api_endpoint_not_docs(): Tests regular internal API endpoints
        """
        middleware = SecurityMiddleware(mock_app, create_settings())
        request = create_mock_request(path="/internal/docs")

        assert middleware._is_docs_endpoint(request) is True

    def test_openapi_in_path(self, mock_app: Mock, create_mock_request: Callable[..., Mock]) -> None:
        """
        Test that paths containing 'openapi' are correctly identified as documentation endpoints.

        Behavior Verified:
            Paths containing 'openapi' anywhere in the path are detected as
            documentation endpoints, even when not at the root level.

        Business Impact:
            Ensures OpenAPI specification files are accessible from various
            URL patterns used by different API documentation tools and clients.

        Test Scenario:
            Given: HTTP request with path "/api/v1/openapi.json"
            When: _is_docs_endpoint() is called
            Then: Returns True indicating documentation endpoint

        Flexibility Consideration:
            Different API frameworks and tools may use different URL patterns
            for serving OpenAPI specifications beyond the standard /openapi.json.

        Edge Case Covered:
            OpenAPI specifications served under versioned API paths or custom
            routes are still properly classified as documentation endpoints.

        Related Tests:
            - test_exact_openapi_path(): Tests standard openapi.json endpoint
            - test_api_endpoint_not_docs(): Tests regular API endpoints without openapi
        """
        middleware = SecurityMiddleware(mock_app, create_settings())
        request = create_mock_request(path="/api/v1/openapi.json")

        assert middleware._is_docs_endpoint(request) is True

    def test_api_endpoint_not_docs(self, mock_app: Mock, create_mock_request: Callable[..., Mock]) -> None:
        """
        Test that regular API endpoints are correctly identified as non-documentation endpoints.

        Behavior Verified:
            Standard API endpoints that don't match documentation patterns are
        correctly rejected and will receive strict CSP policies for security.

        Business Impact:
            Ensures API endpoints maintain strong security posture with strict
            CSP policies, preventing XSS attacks while protecting business data.

        Test Scenario:
            Given: HTTP request with path "/v1/api/users"
            When: _is_docs_endpoint() is called
            Then: Returns False indicating non-documentation endpoint

        Security Protection:
            Regular API endpoints receive strict CSP policies that block inline
            scripts, unsafe evaluations, and untrusted resource loading.

        Risk Mitigation:
            Prevents accidental relaxation of security policies on business
            API endpoints that handle sensitive data and operations.

        Negative Testing:
            This test serves as a critical control to ensure false positives
            don't compromise API security posture.

        Related Tests:
            - All other tests verify positive documentation endpoint detection
            - This test ensures the boundary is properly maintained
        """
        middleware = SecurityMiddleware(mock_app, create_settings())
        request = create_mock_request(path="/v1/api/users")

        assert middleware._is_docs_endpoint(request) is False