"""
Test fixtures shared across middleware unit tests.

This module provides reusable fixtures following behavior-driven testing
principles. Fixtures focus on providing test data and mock dependencies
that are commonly used across multiple middleware test suites.

Fixture Categories:
    - Mock ASGI application fixtures
    - Mock FastAPI Request fixtures with factory pattern
    - HTTP context fixtures (headers, client info)
    - Middleware-specific test data fixtures

Design Philosophy:
    - Fixtures represent 'happy path' successful behavior only
    - Error scenarios are configured within individual test functions
    - All fixtures use public contracts and maintain realistic behavior
    - Stateful mocks maintain internal state for consistent testing

External Dependencies Handled:
    - fastapi.Request: HTTP request object (mocked with spec)
    - starlette.middleware: Base middleware classes (real implementations used)
    - ASGI application: Mock callable for middleware chain termination
"""

import pytest
from fastapi import Request
from unittest.mock import Mock, MagicMock
from typing import Dict, Optional, Any, Callable, Awaitable
from starlette.types import ASGIApp, Scope


# =============================================================================
# Mock ASGI Application Fixtures
# =============================================================================


@pytest.fixture
def mock_asgi_app() -> Mock:
    """
    Mock ASGI application for middleware testing.

    Purpose:
        Provides a mock ASGI application that simulates the next middleware
        or endpoint in the chain. This enables testing middleware behavior
        in isolation from the actual application.

    Default Behavior:
        - Returns a 200 status response when called
        - Tracks call count and arguments for assertions
        - Simulates successful request processing
        - Compatible with ASGI callable signature

    Use Cases:
        - Testing request/response middleware processing
        - Verifying middleware calls next app correctly
        - Testing middleware exception handling
        - Validating request modification behavior

    Example:
        def test_middleware_calls_next_app(mock_asgi_app):
            middleware = MyMiddleware(mock_asgi_app)
            # Test that middleware properly calls the next application

    Assertion Methods:
        - mock_asgi_app.call_count: Number of times middleware called next app
        - mock_asgi_app.call_args: Arguments passed to next application
        - mock_asgi_app.assert_called_once(): Verify single call pattern
    """
    mock_app = Mock(spec=ASGIApp)

    async def mock_asgi_callable(scope: Scope, receive: Callable, send: Callable) -> None:
        """Mock ASGI application that returns a successful response."""
        # Simulate successful response by calling send with response data
        await send({
            'type': 'http.response.start',
            'status': 200,
            'headers': [(b'content-type', b'application/json')],
        })
        await send({
            'type': 'http.response.body',
            'body': b'{"message": "success"}',
        })

    mock_app.side_effect = mock_asgi_callable
    return mock_app


@pytest.fixture
def mock_asgi_app_with_error() -> Mock:
    """
    Mock ASGI application that raises an exception for error testing.

    Purpose:
        Provides a mock ASGI application that simulates an error in the
        downstream application. This enables testing middleware error
        handling and exception recovery behavior.

    Default Behavior:
        - Raises RuntimeError when called
        - Tracks call count for assertions
        - Simulates application failure scenarios
        - Tests middleware exception propagation

    Use Cases:
        - Testing middleware error handling
        - Verifying exception logging behavior
        - Testing error response generation
        - Validating failure recovery mechanisms

    Example Exception Scenarios:
        - RuntimeError: General application errors
        - ValueError: Invalid request data
        - ConnectionError: External service failures

    Related Fixtures:
        - mock_asgi_app: For successful execution testing
    """
    mock_app = Mock(spec=ASGIApp)

    async def mock_asgi_callable_with_error(scope: Scope, receive: Callable, send: Callable) -> None:
        """Mock ASGI application that raises an exception."""
        raise RuntimeError("Simulated application error")

    mock_app.side_effect = mock_asgi_callable_with_error
    return mock_app


# =============================================================================
# Mock Request Factory Fixtures
# =============================================================================


@pytest.fixture
def create_mock_request() -> Callable[..., Mock]:
    """
    Factory fixture for creating mock Request objects with customizable parameters.

    Purpose:
        Provides a flexible factory function that creates mock FastAPI Request
        objects configured with specific paths, headers, and client information.
        This enables testing middleware behavior across various request scenarios.

    Factory Signature:
        _create(path: str = "/", headers: dict = None, client_host: str = "127.0.0.1") -> Request

    Parameters:
        path: Request path (default: "/")
        headers: Dictionary of request headers (default: None)
        client_host: Client IP address (default: "127.0.0.1")

    Default Behavior:
        - Creates Request mock with proper spec for type safety
        - Configures URL mock with provided path
        - Sets up client mock with host information
        - Initializes empty state object for middleware use
        - Returns fully configured Request object

    Use Cases:
        - Testing middleware path-based routing
        - Verifying header processing logic
        - Testing client identification behavior
        - Creating requests with custom attributes for testing

    Example Usage:
        def test_middleware_processes_headers(create_mock_request):
            request = create_mock_request(
                path="/api/test",
                headers={"authorization": "Bearer token"},
                client_host="192.168.1.100"
            )
            # Test middleware behavior with custom request

    Customization Patterns:
        - Header testing: Pass custom headers dict
        - Path testing: Use different URL paths
        - Client testing: Vary client_host for IP-based logic
        - Authentication testing: Add auth headers

    Design Notes:
        - Uses Mock(spec=Request) for proper type checking
        - All Request attributes are properly mocked
        - Maintains compatibility with FastAPI Request interface
        - Supports middleware testing patterns from documentation

    Related Fixtures:
        - mock_request: Pre-configured request fixture
        - create_mock_request_with_query: Factory with query parameter support
    """
    def _create(path: str = "/", headers: Optional[Dict[str, str]] = None, client_host: str = "127.0.0.1") -> Mock:
        """Create a mock Request object with specified parameters."""
        request = Mock(spec=Request)

        # Configure URL mock
        request.url = Mock()
        request.url.path = path
        request.url.query_string = ""
        request.url.scheme = "http"
        request.url.hostname = "localhost"
        request.url.port = 8000

        # Configure headers
        request.headers = headers or {}

        # Configure client information
        request.client = Mock()
        request.client.host = client_host
        request.client.port = 12345

        # Configure method and state
        request.method = "GET"
        request.state = Mock()
        request.query_params = {}
        request.path_params = {}

        # Configure body
        request.body = b""
        request.json = Mock(return_value={})

        return request

    return _create


@pytest.fixture
def create_mock_request_with_query() -> Callable[..., Mock]:
    """
    Factory fixture for creating mock Request objects with query parameters.

    Purpose:
        Extends the basic request factory to support query parameter
        configuration for testing middleware that processes URL parameters.

    Factory Signature:
        _create(path: str = "/", query_params: dict = None, **kwargs) -> Request

    Parameters:
        path: Request path (default: "/")
        query_params: Dictionary of query parameters (default: None)
        **kwargs: Additional arguments passed to base request factory

    Use Cases:
        - Testing middleware query parameter validation
        - Verifying parameter-based routing behavior
        - Testing middleware with URL filtering logic
        - Validating parameter extraction functionality

    Example:
        def test_middleware_validates_query_params(create_mock_request_with_query):
            request = create_mock_request_with_query(
                path="/api/search",
                query_params={"q": "test", "limit": "10"}
            )
    """
    def _create(path: str = "/", query_params: Optional[Dict[str, str]] = None, **kwargs: Any) -> Mock:
        """Create a mock Request with query parameters."""
        # Get base request factory
        factory = create_mock_request()
        request = factory(path=path, **kwargs)

        # Configure query parameters
        query_params = query_params or {}
        request.query_params = query_params

        # Configure URL query string
        if query_params:
            query_string = "&".join([f"{k}={v}" for k, v in query_params.items()])
            request.url.query_string = query_string
        else:
            request.url.query_string = ""

        return request  # type: ignore

    return _create


# =============================================================================
# Pre-configured Request Fixtures
# =============================================================================


@pytest.fixture
def mock_request() -> Mock:
    """
    Standard mock Request object for basic middleware testing.

    Purpose:
        Provides a pre-configured mock Request object representing a typical
        HTTP request for middleware testing. This fixture represents the
        'happy path' scenario with standard request attributes.

    Request Configuration:
        - Path: "/"
        - Method: "GET"
        - Client: "127.0.0.1"
        - Headers: Empty dict
        - Query parameters: Empty dict
        - Body: Empty bytes
        - JSON: Empty dict

    Use Cases:
        - Testing basic middleware functionality
        - Verifying request processing pipeline
        - Testing middleware with minimal request setup
        - Standard middleware behavior validation

    Customization:
        For specific test scenarios, use the create_mock_request factory
        to create requests with custom paths, headers, or client information.

    Related Fixtures:
        - create_mock_request: Factory for custom requests
        - mock_request_with_headers: Request with standard headers
        - mock_request_with_auth: Request with authentication headers
    """
    factory = create_mock_request()
    return factory()  # type: ignore  # type: ignore


@pytest.fixture
def mock_request_with_headers() -> Mock:
    """
    Mock Request object with common HTTP headers for testing.

    Purpose:
        Provides a mock Request object pre-configured with typical HTTP
        headers found in production requests. This enables testing middleware
        that processes or validates request headers.

    Headers Included:
        - content-type: "application/json"
        - user-agent: "TestClient/1.0"
        - accept: "application/json"
        - accept-language: "en-US,en;q=0.9"

    Use Cases:
        - Testing header validation middleware
        - Verifying content-type processing
        - Testing user-agent based routing
        - Validating language negotiation logic

    Additional Customization:
        Use create_mock_request factory to add custom headers or modify
        the standard header set for specific test scenarios.

    Related Fixtures:
        - mock_request: Basic request without headers
        - create_mock_request: Factory for custom header configuration
    """
    factory = create_mock_request()
    headers = {
        "content-type": "application/json",
        "user-agent": "TestClient/1.0",
        "accept": "application/json",
        "accept-language": "en-US,en;q=0.9",
    }
    return factory(headers=headers)  # type: ignore


@pytest.fixture
def mock_request_with_auth() -> Mock:
    """
    Mock Request object with authentication headers for testing.

    Purpose:
        Provides a mock Request object configured with standard authentication
        headers for testing authentication and authorization middleware.

    Authentication Headers:
        - authorization: "Bearer test-token-12345"
        - x-api-key: "test-api-key-67890"

    Use Cases:
        - Testing authentication middleware
        - Verifying authorization logic
        - Testing token validation behavior
        - Validating API key processing

    Security Testing:
        This fixture helps test middleware that handles security-sensitive
        operations like token validation, user authentication, and access control.

    Related Fixtures:
        - mock_request: Basic request without auth
        - mock_request_unauthorized: Request without valid auth headers
    """
    factory = create_mock_request()
    headers = {
        "authorization": "Bearer test-token-12345",
        "x-api-key": "test-api-key-67890",
    }
    return factory(headers=headers)  # type: ignore


@pytest.fixture
def mock_request_unauthorized() -> Mock:
    """
    Mock Request object without authentication for testing unauthorized access.

    Purpose:
        Provides a mock Request object representing an unauthenticated
        request for testing middleware that handles authentication failures
        and unauthorized access attempts.

    Configuration:
        - No authentication headers
        - Standard client host
        - Basic request path

    Use Cases:
        - Testing authentication failure scenarios
        - Verifying unauthorized response behavior
        - Testing middleware access control
        - Validating error response formatting

    Security Testing:
        Complements mock_request_with_auth to test both authenticated and
        unauthenticated scenarios for comprehensive security testing.

    Related Fixtures:
        - mock_request_with_auth: Authenticated request counterpart
    """
    factory = create_mock_request()
    return factory()  # type: ignore


# =============================================================================
# Specialized Request Fixtures
# =============================================================================


@pytest.fixture
def mock_api_request() -> Mock:
    """
    Mock Request object configured for API endpoint testing.

    Purpose:
        Provides a mock Request object configured specifically for testing
        API middleware with typical API request patterns and headers.

    API Configuration:
        - Path: "/api/v1/test"
        - Method: "POST"
        - Headers: API-specific headers including content-type and accept
        - Body: Sample JSON payload
        - JSON: Sample dictionary data

    Use Cases:
        - Testing API request validation
        - Verifying JSON parsing middleware
        - Testing API rate limiting behavior
        - Validating request/response transformation

    API Testing Patterns:
        This fixture supports common API testing scenarios including
        request body validation, header processing, and response formatting.

    Related Fixtures:
        - mock_request: Basic HTTP request fixture
        - create_mock_request: Factory for custom API requests
    """
    factory = create_mock_request()
    headers = {
        "content-type": "application/json",
        "accept": "application/json",
        "x-request-id": "test-request-123",
    }

    request = factory(path="/api/v1/test", headers=headers)
    request.method = "POST"
    request.body = b'{"test": "data"}'
    request.json.return_value = {"test": "data"}

    return request  # type: ignore


@pytest.fixture
def mock_websocket_request() -> Mock:
    """
    Mock Request object for WebSocket connection testing.

    Purpose:
        Provides a mock Request object configured for WebSocket connection
        scenarios for testing WebSocket-specific middleware.

    WebSocket Configuration:
        - Path: "/ws/test"
        - Headers: WebSocket upgrade headers
        - Connection type: WebSocket

    Use Cases:
        - Testing WebSocket connection middleware
        - Verifying upgrade header processing
        - Testing connection validation logic
        - Validating WebSocket-specific behavior

    WebSocket Testing:
        Supports testing middleware that handles WebSocket protocol upgrades,
        connection authentication, and WebSocket-specific request processing.

    Related Fixtures:
        - mock_request: HTTP request counterpart
    """
    factory = create_mock_request()
    headers = {
        "upgrade": "websocket",
        "connection": "Upgrade",
        "sec-websocket-key": "test-websocket-key",
        "sec-websocket-version": "13",
    }

    request = factory(path="/ws/test", headers=headers)
    request.method = "GET"

    return request  # type: ignore


# =============================================================================
# Test Data and Context Fixtures
# =============================================================================


@pytest.fixture
def sample_middleware_config() -> Dict[str, Any]:
    """
    Sample middleware configuration for testing.

    Purpose:
        Provides a sample configuration dictionary that represents typical
        middleware settings for testing configuration-based middleware behavior.

    Configuration Includes:
        - enabled_paths: Paths where middleware is active
        - excluded_paths: Paths where middleware is bypassed
        - rate_limiting: Rate limiting configuration
        - headers: Header processing settings

    Use Cases:
        - Testing configuration-based middleware activation
        - Verifying path exclusion logic
        - Testing rate limiting configuration
        - Validating header processing settings

    Configuration Testing:
        This fixture enables testing middleware that uses configuration
        files or environment variables for behavior customization.

    Customization:
        Modify the configuration in tests or create custom fixtures
        for specific middleware configuration scenarios.
    """
    return {
        "enabled_paths": ["/api/", "/internal/"],
        "excluded_paths": ["/health", "/metrics"],
        "rate_limiting": {
            "requests_per_minute": 100,
            "burst_size": 20,
        },
        "headers": {
            "required": ["x-request-id"],
            "optional": ["x-client-version"],
            "remove": ["x-internal-info"],
        },
        "logging": {
            "log_requests": True,
            "log_responses": False,
            "log_level": "INFO",
        },
    }


@pytest.fixture
def mock_receive() -> Mock:
    """
    Mock ASGI receive callable for testing.

    Purpose:
        Provides a mock ASGI receive function that simulates receiving
        request data from the ASGI server. This enables testing middleware
        that processes request bodies or handles streaming data.

    Default Behavior:
        - Returns empty message for basic requests
        - Can be configured to return specific body content
        - Simulates ASGI receive callable interface
        - Tracks receive calls for assertions

    Use Cases:
        - Testing request body processing middleware
        - Verifying streaming data handling
        - Testing request parsing behavior
        - Validating data transformation logic

    ASGI Interface:
        Follows the ASGI specification for receive callables with
        proper message format and async behavior.

    Related Fixtures:
        - mock_send: Mock ASGI send callable
    """
    mock_receive = Mock()

    async def mock_receive_callable() -> Dict[str, Any]:
        """Mock ASGI receive that returns empty message."""
        return {
            "type": "http.request",
            "body": b"",
            "more_body": False,
        }

    mock_receive.side_effect = mock_receive_callable
    return mock_receive


@pytest.fixture
def mock_send() -> Mock:
    """
    Mock ASGI send callable for testing response handling.

    Purpose:
        Provides a mock ASGI send function that captures response data
        sent by middleware. This enables testing middleware response
        processing and modification behavior.

    Default Behavior:
        - Captures response start and body messages
        - Tracks send calls for assertions
        - Simulates ASGI send callable interface
        - Stores response data for verification

    Use Cases:
        - Testing response header modification
        - Verifying response body transformation
        - Testing response status code changes
        - Validating response compression logic

    Response Capture:
        Stores sent messages in mock_send.sent_messages for test assertions.
        Enables verification of response modifications made by middleware.

    Related Fixtures:
        - mock_receive: Mock ASGI receive callable
    """
    mock_send = Mock()
    mock_send.sent_messages = []

    async def mock_send_callable(message: Dict[str, Any]) -> None:
        """Mock ASGI send that captures messages."""
        mock_send.sent_messages.append(message)

    mock_send.side_effect = mock_send_callable
    return mock_send


# =============================================================================
# Legacy Fixtures (Backward Compatibility)
# =============================================================================


@pytest.fixture
def mock_app() -> Mock:
    """
    Legacy mock ASGI application for backward compatibility.

    DEPRECATED: Use mock_asgi_app instead for new tests.

    Purpose:
        Provides a simple mock ASGI application for basic middleware testing.
        Maintained for backward compatibility with existing tests.

    Migration:
        Replace mock_app with mock_asgi_app in new tests for
        better ASGI compliance and clearer intent.
    """
    return Mock()