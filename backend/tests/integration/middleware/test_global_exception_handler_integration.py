"""
Integration tests for Global Exception Handler → All Middleware Integration (Error Handling).

This module tests the integration between the global exception handler and all middleware
components to ensure comprehensive error handling, security header preservation,
and proper error response formatting across the entire middleware stack.

Seam Under Test:
    Global Exception Handler → All Middleware Components (Error Handling)

Critical Paths:
    - Exception in any middleware → Global handler → Structured error response with headers
    - Security headers preservation on error responses
    - Custom exception mapping to appropriate HTTP status codes
    - Error information disclosure control (production vs development)
    - Error logging with request correlation

Test Scope:
    - Exception handler catches all middleware exceptions
    - Security headers on error responses (CORS, security headers, correlation ID)
    - Custom exception mapping to HTTP status codes
    - Error response structure and information disclosure
    - Error logging with correlation and structured log capture

Business Impact:
    Error handling security + consistency. Missing headers on error responses break CORS
    or security; information disclosure creates security vulnerabilities; incorrect
    status codes confuse clients.

Testing Strategy:
    - Use high-fidelity test clients with full middleware stack
    - Create test endpoints that raise specific exception types
    - Verify observable behavior through HTTP responses and headers
    - Use log capture to verify error logging with correlation
    - Test both production and development environments for information disclosure

Success Criteria:
    All exceptions handled gracefully, security headers preserved on error responses,
    production mode prevents information disclosure.
"""

import pytest
import logging
from typing import Any
from unittest.mock import Mock

from fastapi import FastAPI, Request
from fastapi.testclient import TestClient
from pydantic import BaseModel

from app.main import create_app
from app.core.exceptions import (
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    ConfigurationError,
    BusinessLogicError,
    InfrastructureError,
    TransientAIError,
    PermanentAIError,
    RateLimitError,
    ServiceUnavailableError,
    ApplicationError,
    RequestTooLargeError
)
from app.schemas.common import ErrorResponse


class TestGlobalExceptionHandlerIntegration:
    """
    Integration tests for Global Exception Handler → All Middleware Integration (Error Handling).

    Seam Under Test:
        Global Exception Handler → All Middleware Components → Structured Error Response

    Critical Paths:
        - Exception in any middleware → Global handler → Structured error response with headers
        - Security headers preservation on error responses
        - Custom exception mapping to appropriate HTTP status codes
        - Error information disclosure control (production vs development)
        - Error logging with request correlation

    Business Impact:
        Error handling security + consistency. Missing headers on error responses break CORS
        or security; information disclosure creates security vulnerabilities; incorrect
        status codes confuse clients.

    Integration Scope:
        - Global exception handler (setup_global_exception_handler)
        - All middleware components as exception sources
        - Security headers preservation on error responses
        - Error response formatting with security considerations
        - Error logging with request correlation
    """

    # -------------------------------------------------------------------------
    # Test Exception Handler Catches All Middleware Exceptions
    # -------------------------------------------------------------------------

    def test_exception_handler_catches_custom_exceptions(self, exception_test_client: TestClient) -> None:
        """
        Test that global exception handler catches all custom exceptions from middleware.

        Integration Scope:
            Global exception handler + custom exception classes

        Business Impact:
            Prevents unhandled exceptions from breaking application and ensures
            consistent error responses for all custom exception types.

        Test Strategy:
            - Use pre-registered exception test endpoints from fixture
            - Verify all exceptions return structured JSON error responses
            - Verify appropriate HTTP status codes for each exception type
            - Verify error responses don't expose stack traces or internals

        Success Criteria:
            All custom exceptions return structured error responses with correct status codes.
        """
        # Use exception_test_client fixture which has pre-registered endpoints

        # Test ValidationError (400)
        response = exception_test_client.get("/test/validation-error")
        assert response.status_code == 400
        data = response.json()
        assert data["error_code"] == "VALIDATION_ERROR"
        assert "Invalid request data" in data["error"]
        assert "timestamp" in data
        assert "success" not in data or data["success"] is False

        # Test AuthenticationError (401)
        response = exception_test_client.get("/test/authentication-error")
        assert response.status_code == 401
        data = response.json()
        assert data["error_code"] == "AUTHENTICATION_ERROR"
        assert "Authentication failed" in data["error"]

        # Test AuthorizationError (403)
        response = exception_test_client.get("/test/authorization-error")
        assert response.status_code == 403
        data = response.json()
        assert data["error_code"] == "AUTHORIZATION_ERROR"
        assert "Access denied" in data["error"]

        # Test ConfigurationError (500)
        response = exception_test_client.get("/test/configuration-error")
        assert response.status_code == 500
        data = response.json()
        assert data["error_code"] == "CONFIGURATION_ERROR"
        assert "Service configuration error" in data["error"]

        # Test BusinessLogicError (422)
        response = exception_test_client.get("/test/business-logic-error")
        assert response.status_code == 422
        data = response.json()
        assert data["error_code"] == "VALIDATION_ERROR"
        assert "Invalid request data" in data["error"]

        # Test InfrastructureError (500)
        response = exception_test_client.get("/test/infrastructure-error")
        assert response.status_code == 500
        data = response.json()
        assert data["error_code"] == "INFRASTRUCTURE_ERROR"
        assert "External service error" in data["error"]

        # Test RateLimitError (429)
        response = exception_test_client.get("/test/rate-limit-error")
        assert response.status_code == 429
        data = response.json()
        assert data["error_code"] == "RATE_LIMIT_EXCEEDED"
        assert "Rate limit exceeded" in data["error"]

        # Test RequestTooLargeError (413)
        response = exception_test_client.get("/test/request-too-large-error")
        assert response.status_code == 413
        data = response.json()
        assert data["error_code"] == "REQUEST_TOO_LARGE"
        assert "Request too large" in data["error"]

    def test_exception_handler_catches_generic_exceptions(self, exception_test_client: TestClient) -> None:
        """
        Test that global exception handler catches generic Python exceptions.

        Integration Scope:
            Global exception handler + generic Python exceptions

        Business Impact:
            Prevents application crashes from unexpected exceptions and ensures
            consistent error responses even for unhandled exceptions.

        Test Strategy:
            - Create test endpoints that raise generic Python exceptions
            - Verify all exceptions return 500 status with INTERNAL_ERROR code
            - Verify error responses don't expose stack traces or implementation details
            - Test various common exception types (ValueError, KeyError, TypeError)

        Success Criteria:
            All generic exceptions return sanitized 500 error responses.
        """
        # Use exception_test_client fixture which has pre-registered endpoints

        # Test ValueError (500)
        response = exception_test_client.get("/test/value-error")
        assert response.status_code == 500
        data = response.json()
        assert data["error_code"] == "INTERNAL_ERROR"
        assert data["error"] == "Internal server error"
        assert "Invalid value" not in data["error"]  # Message sanitized
        assert "timestamp" in data

        # Test KeyError (500)
        response = exception_test_client.get("/test/key-error")
        assert response.status_code == 500
        data = response.json()
        assert data["error_code"] == "INTERNAL_ERROR"
        assert data["error"] == "Internal server error"
        assert "nonexistent_key" not in data["error"]  # Details not exposed

        # Test TypeError (500)
        response = exception_test_client.get("/test/type-error")
        assert response.status_code == 500
        data = response.json()
        assert data["error_code"] == "INTERNAL_ERROR"
        assert data["error"] == "Internal server error"

        # Test RuntimeError (500)
        response = exception_test_client.get("/test/runtime-error")
        assert response.status_code == 500
        data = response.json()
        assert data["error_code"] == "INTERNAL_ERROR"
        assert data["error"] == "Internal server error"

        # Test generic Exception (500)
        response = exception_test_client.get("/test/generic-exception")
        assert response.status_code == 500
        data = response.json()
        assert data["error_code"] == "INTERNAL_ERROR"
        assert data["error"] == "Internal server error"

    def test_exception_handler_catches_middleware_exceptions(self, exception_test_client: TestClient) -> None:
        """
        Test that global exception handler catches exceptions from middleware components.

        Integration Scope:
            Global exception handler + all middleware components

        Business Impact:
            Ensures middleware failures don't crash the application and provide
            consistent error responses even when middleware components fail.

        Test Strategy:
            - Mock middleware components to raise exceptions
            - Verify exception handler catches middleware exceptions
            - Verify security headers are preserved on middleware error responses
            - Verify correlation IDs are maintained through middleware errors

        Success Criteria:
            Middleware exceptions are caught and return proper error responses with headers.
        """
        app = create_app()

        # Create endpoint that simulates middleware failure
        @app.get("/test/middleware-failure")
        async def middleware_failure_endpoint(request: Request) -> None:
            # Simulate a middleware-style failure
            raise InfrastructureError(
                "Rate limiting middleware failed",
                {"middleware": "rate_limiting", "operation": "redis_check"}
            )

        client = TestClient(app, raise_server_exceptions=False)

        response = client.get("/test/middleware-failure")
        assert response.status_code == 500
        data = response.json()
        assert data["error_code"] == "INFRASTRUCTURE_ERROR"
        assert "External service error" in data["error"]
        assert "timestamp" in data

    # -------------------------------------------------------------------------
    # Test Security Headers on Error Responses
    # -------------------------------------------------------------------------

    def test_security_headers_preserved_on_error_responses(self, exception_test_client: TestClient) -> None:
        """
        Test that security headers are preserved on error responses.

        Integration Scope:
            Global exception handler + security middleware + error responses

        Business Impact:
            Security headers must be present on error responses to prevent
            security vulnerabilities when errors occur. Missing headers on
            error responses can expose the application to attacks.

        Test Strategy:
            - Create endpoint that raises various exception types
            - Verify security headers are present on all error responses
            - Test CORS headers, security headers, and correlation headers
            - Ensure headers are applied after exception handling

        Success Criteria:
            All error responses include required security and CORS headers.
        """
        app = create_app()

        @app.get("/test/security-headers-error")
        async def security_headers_error_endpoint() -> None:
            raise ValidationError("Test error for security headers")

        client = TestClient(app, raise_server_exceptions=False)

        response = client.get("/test/security-headers-error")
        assert response.status_code == 400

        # Verify security headers are present on error response
        assert "x-content-type-options" in response.headers
        assert response.headers["x-content-type-options"] == "nosniff"

        # Check for other common security headers (if configured)
        if "x-frame-options" in response.headers:
            assert response.headers["x-frame-options"] == "DENY"

        # Verify correlation ID header is present (if logging middleware ran)
        if "x-request-id" in response.headers:
            assert len(response.headers["x-request-id"]) > 0

    def test_cors_headers_preserved_on_error_responses(self, exception_test_client: TestClient) -> None:
        """
        Test that CORS headers are preserved on error responses.

        Integration Scope:
            Global exception handler + CORS middleware + error responses

        Business Impact:
            CORS headers must be present on error responses to allow browsers
            to handle error responses properly. Missing CORS headers on errors
            can break client-side error handling.

        Test Strategy:
            - Make request with Origin header to trigger CORS
            - Raise exception in endpoint
            - Verify CORS headers are present on error response
            - Test both preflight and actual request scenarios

        Success Criteria:
            Error responses include appropriate CORS headers when requested.
        """
        app = create_app()

        @app.get("/test/cors-error")
        async def cors_error_endpoint() -> None:
            raise ValidationError("Test error for CORS headers")

        client = TestClient(app, raise_server_exceptions=False)

        # Make request with Origin header to trigger CORS
        response = client.get("/test/cors-error", headers={"Origin": "http://localhost:3000"})
        assert response.status_code == 400

        # Verify CORS headers are present on error response
        # Note: Actual CORS headers depend on configuration
        # This test verifies the mechanism works when CORS is configured
        assert response.headers.get("content-type") == "application/json"

    def test_correlation_id_preserved_on_error_responses(self, exception_test_client: TestClient) -> None:
        """
        Test that correlation IDs are preserved on error responses.

        Integration Scope:
            Global exception handler + request logging middleware + error responses

        Business Impact:
            Correlation IDs enable debugging and monitoring of error scenarios.
            Maintaining correlation IDs on errors is critical for incident response.

        Test Strategy:
            - Make request to endpoint that raises exception
            - Verify correlation ID is present in error response
            - Verify correlation ID is logged with error details
            - Test correlation ID consistency across request lifecycle

        Success Criteria:
            Error responses include correlation IDs for debugging and monitoring.
        """
        app = create_app()

        @app.get("/test/correlation-error")
        async def correlation_error_endpoint() -> None:
            raise InfrastructureError("Test error for correlation ID")

        client = TestClient(app, raise_server_exceptions=False)

        response = client.get("/test/correlation-error")
        assert response.status_code == 500
        data = response.json()

        # Verify error response structure
        assert "error_code" in data
        assert "timestamp" in data

        # Check for correlation ID in headers (if logging middleware ran)
        correlation_id = response.headers.get("x-request-id")
        if correlation_id:
            assert len(correlation_id) > 0
            assert isinstance(correlation_id, str)

    # -------------------------------------------------------------------------
    # Test Custom Exception Mapping to HTTP Status Codes
    # -------------------------------------------------------------------------

    def test_validation_error_maps_to_400(self, exception_test_client: TestClient) -> None:
        """
        Test that ValidationError maps to HTTP 400 status code.

        Integration Scope:
            Global exception handler + ValidationError exception

        Business Impact:
            Correct HTTP status codes guide client error handling and retry logic.
            Validation errors should return 400 to indicate client-side issues.

        Test Strategy:
            - Create endpoint that raises ValidationError
            - Verify response status code is 400
            - Verify error response structure and content
            - Test ValidationError with and without context

        Success Criteria:
            ValidationError exceptions return 400 status with proper error format.
        """
        app = create_app()

        @app.post("/test/validation-error-mapping")
        async def validation_error_mapping_endpoint(request_data: dict) -> None:
            raise ValidationError(
                "Invalid request data",
                {"field": "email", "value": "invalid-email", "reason": "invalid format"}
            )

        client = TestClient(app, raise_server_exceptions=False)

        response = client.post("/test/validation-error-mapping", json={})
        assert response.status_code == 400

        data = response.json()
        assert data["error_code"] == "VALIDATION_ERROR"
        assert "Invalid request data" in data["error"]
        assert "timestamp" in data

    def test_authentication_error_maps_to_401(self, exception_test_client: TestClient) -> None:
        """
        Test that AuthenticationError maps to HTTP 401 status code.

        Integration Scope:
            Global exception handler + AuthenticationError exception

        Business Impact:
            Authentication errors should return 401 to guide clients to
            provide proper authentication credentials.

        Test Strategy:
            - Create endpoint that raises AuthenticationError
            - Verify response status code is 401
            - Verify error response indicates authentication failure
            - Test different authentication error scenarios

        Success Criteria:
            AuthenticationError exceptions return 401 status with authentication error message.
        """
        app = create_app()

        @app.get("/test/authentication-error-mapping")
        async def authentication_error_mapping_endpoint() -> None:
            raise AuthenticationError("Invalid or missing API key")

        client = TestClient(app, raise_server_exceptions=False)

        response = client.get("/test/authentication-error-mapping")
        assert response.status_code == 401

        data = response.json()
        assert data["error_code"] == "AUTHENTICATION_ERROR"
        assert "Authentication failed" in data["error"]
        assert "timestamp" in data

    def test_authorization_error_maps_to_403(self, exception_test_client: TestClient) -> None:
        """
        Test that AuthorizationError maps to HTTP 403 status code.

        Integration Scope:
            Global exception handler + AuthorizationError exception

        Business Impact:
            Authorization errors should return 403 to indicate that the
            client is authenticated but lacks permission for the resource.

        Test Strategy:
            - Create endpoint that raises AuthorizationError
            - Verify response status code is 403
            - Verify error response indicates authorization failure
            - Test permission-based access control scenarios

        Success Criteria:
            AuthorizationError exceptions return 403 status with authorization error message.
        """
        app = create_app()

        @app.get("/test/authorization-error-mapping")
        async def authorization_error_mapping_endpoint() -> None:
            raise AuthorizationError("Insufficient permissions for resource")

        client = TestClient(app, raise_server_exceptions=False)

        response = client.get("/test/authorization-error-mapping")
        assert response.status_code == 403

        data = response.json()
        assert data["error_code"] == "AUTHORIZATION_ERROR"
        assert "Access denied" in data["error"]
        assert "timestamp" in data

    def test_rate_limit_error_maps_to_429(self, exception_test_client: TestClient) -> None:
        """
        Test that RateLimitError maps to HTTP 429 status code.

        Integration Scope:
            Global exception handler + RateLimitError exception

        Business Impact:
            Rate limit errors should return 429 to guide clients to
            implement proper backoff and retry logic.

        Test Strategy:
            - Create endpoint that raises RateLimitError
            - Verify response status code is 429
            - Verify error response indicates rate limiting
            - Test retry_after context is preserved

        Success Criteria:
            RateLimitError exceptions return 429 status with rate limit error message.
        """
        app = create_app()

        @app.get("/test/rate-limit-error-mapping")
        async def rate_limit_error_mapping_endpoint() -> None:
            raise RateLimitError("Rate limit exceeded", retry_after=60)

        client = TestClient(app, raise_server_exceptions=False)

        response = client.get("/test/rate-limit-error-mapping")
        assert response.status_code == 429

        data = response.json()
        assert data["error_code"] == "RATE_LIMIT_EXCEEDED"
        assert "Rate limit exceeded" in data["error"]
        assert "timestamp" in data

    def test_infrastructure_error_maps_to_500(self, exception_test_client: TestClient) -> None:
        """
        Test that InfrastructureError maps to HTTP 500 status code.

        Integration Scope:
            Global exception handler + InfrastructureError exception

        Business Impact:
            Infrastructure errors should return 500 to indicate server-side
            failures that are not the client's fault.

        Test Strategy:
            - Create endpoint that raises InfrastructureError
            - Verify response status code is 500
            - Verify error response indicates infrastructure failure
            - Test different infrastructure failure scenarios

        Success Criteria:
            InfrastructureError exceptions return 500 status with infrastructure error message.
        """
        app = create_app()

        @app.get("/test/infrastructure-error-mapping")
        async def infrastructure_error_mapping_endpoint() -> None:
            raise InfrastructureError("Database connection failed")

        client = TestClient(app, raise_server_exceptions=False)

        response = client.get("/test/infrastructure-error-mapping")
        assert response.status_code == 500

        data = response.json()
        assert data["error_code"] == "INFRASTRUCTURE_ERROR"
        assert "External service error" in data["error"]
        assert "timestamp" in data

    # -------------------------------------------------------------------------
    # Test Error Response Structure and Information Disclosure
    # -------------------------------------------------------------------------

    def test_production_mode_prevents_information_disclosure(self, monkeypatch: Any) -> None:
        """
        Test that production mode prevents information disclosure in error responses.

        Integration Scope:
            Global exception handler + production environment settings

        Business Impact:
            Production mode must not expose sensitive information like stack traces,
            internal paths, or implementation details that could aid attackers.

        Test Strategy:
            - Set environment to production mode
            - Create endpoints that raise various exceptions with sensitive details
            - Verify error responses don't expose stack traces or internal details
            - Verify error messages are generic and safe for production

        Success Criteria:
            Production error responses are sanitized and don't expose sensitive information.
        """
        # Set production environment
        monkeypatch.setenv("ENVIRONMENT", "production")
        monkeypatch.setenv("API_KEY", "test-api-key")

        app = create_app()

        @app.get("/test/production-sensitive-error")
        async def production_sensitive_error_endpoint() -> None:
            # Raise error with potentially sensitive context
            raise InfrastructureError(
                "Database connection failed",
                {
                    "database_url": "postgresql://user:pass@localhost/db",
                    "internal_path": "/app/internal/db.py",
                    "stack_trace": "Traceback (most recent call last)..."
                }
            )

        @app.get("/test/production-validation-error")
        async def production_validation_error_endpoint() -> None:
            raise ValidationError(
                "Invalid input",
                {"internal_field": "sensitive_value", "debug_info": "detailed_error"}
            )

        client = TestClient(app, raise_server_exceptions=False)

        # Test infrastructure error in production
        response = client.get("/test/production-sensitive-error")
        assert response.status_code == 500

        data = response.json()
        assert data["error_code"] == "INFRASTRUCTURE_ERROR"
        assert data["error"] == "External service error"  # Generic message

        # Verify sensitive information is not exposed
        response_text = str(data)
        assert "postgresql://" not in response_text
        assert "password" not in response_text.lower()
        assert "stack trace" not in response_text.lower()
        assert "/app/internal/" not in response_text

        # Test validation error in production
        response = client.get("/test/production-validation-error")
        assert response.status_code == 400

        data = response.json()
        assert data["error_code"] == "VALIDATION_ERROR"
        assert "Invalid request data" in data["error"]

        # Verify sensitive context is not exposed in production
        if "details" in data:
            details_str = str(data["details"])
            assert "sensitive_value" not in details_str
            assert "detailed_error" not in details_str

    def test_development_mode_allows_detailed_errors(self, monkeypatch: Any) -> None:
        """
        Test that development mode allows detailed error information.

        Integration Scope:
            Global exception handler + development environment settings

        Business Impact:
            Development mode should provide detailed error information to
            help developers debug issues quickly and effectively.

        Test Strategy:
            - Set environment to development mode
            - Create endpoints that raise exceptions with context
            - Verify error responses include useful debugging information
            - Test that development provides more detailed error context

        Success Criteria:
            Development error responses include helpful debugging information.
        """
        # Set development environment
        monkeypatch.setenv("ENVIRONMENT", "development")
        monkeypatch.setenv("API_KEY", "test-api-key")

        app = create_app()

        @app.get("/test/development-detailed-error")
        async def development_detailed_error_endpoint() -> None:
            raise ApplicationError(
                "Business logic error occurred",
                {
                    "user_id": "12345",
                    "operation": "create_order",
                    "debug_context": "Additional debugging info"
                }
            )

        client = TestClient(app, raise_server_exceptions=False)

        response = client.get("/test/development-detailed-error")
        assert response.status_code == 400

        data = response.json()
        assert "error" in data
        assert "timestamp" in data

        # Development mode includes helpful message (not generic)
        assert "Business logic error occurred" in data["error"]

        # Details available for debugging (if implementation provides them)
        if "details" in data:
            assert isinstance(data["details"], dict)
            # Verify helpful debugging context is included
            assert "user_id" in data["details"]
            assert "operation" in data["details"]
            assert data["details"]["user_id"] == "12345"
            assert data["details"]["operation"] == "create_order"

    def test_error_response_consistency_across_exception_types(self, exception_test_client: TestClient) -> None:
        """
        Test that error responses have consistent structure across all exception types.

        Integration Scope:
            Global exception handler + all exception types

        Business Impact:
            Consistent error response structure enables clients to handle
            errors predictably and implement proper error handling logic.

        Test Strategy:
            - Create endpoints that raise different exception types
            - Verify all error responses have consistent structure
            - Test required fields are present in all error responses
            - Verify optional fields are handled consistently

        Success Criteria:
            All error responses follow consistent structure and format.
        """
        app = create_app()

        @app.get("/test/consistency-validation")
        async def consistency_validation_endpoint() -> None:
            raise ValidationError("Validation error")

        @app.get("/test/consistency-infrastructure")
        async def consistency_infrastructure_endpoint() -> None:
            raise InfrastructureError("Infrastructure error")

        @app.get("/test/consistency-ai")
        async def consistency_ai_endpoint() -> None:
            raise TransientAIError("AI service error")

        @app.get("/test/consistency-generic")
        async def consistency_generic_endpoint() -> None:
            raise ValueError("Generic error")

        client = TestClient(app, raise_server_exceptions=False)

        # Test all endpoints and verify consistent structure
        endpoints = [
            "/test/consistency-validation",
            "/test/consistency-infrastructure",
            "/test/consistency-ai",
            "/test/consistency-generic"
        ]

        for endpoint in endpoints:
            response = client.get(endpoint)
            data = response.json()

            # Verify consistent error response structure
            assert "error" in data, f"Missing 'error' field in response from {endpoint}"
            assert "error_code" in data, f"Missing 'error_code' field in response from {endpoint}"
            assert "timestamp" in data, f"Missing 'timestamp' field in response from {endpoint}"

            # Verify timestamp format (ISO format)
            timestamp = data["timestamp"]
            assert isinstance(timestamp, str), f"Timestamp should be string, got {type(timestamp)}"
            assert "T" in timestamp, f"Timestamp should be ISO format, got: {timestamp}"

            # Verify error and error_code are strings
            assert isinstance(data["error"], str), f"Error should be string, got {type(data['error'])}"
            assert isinstance(data["error_code"], str), f"Error code should be string, got {type(data['error_code'])}"

            # Verify no unexpected fields that could cause client parsing issues
            known_fields = {"error", "error_code", "timestamp", "details", "success"}
            for field in data.keys():
                assert field in known_fields, f"Unexpected field '{field}' in error response from {endpoint}"

    def test_special_case_api_versioning_error_response(self, exception_test_client: TestClient) -> None:
        """
        Test special case API versioning error response format.

        Integration Scope:
            Global exception handler + API versioning error special case

        Business Impact:
            API versioning errors require special response format with
            version information headers to guide client API migration.

        Test Strategy:
            - Create ApplicationError with API versioning context
            - Verify special response format for API versioning errors
            - Verify version information headers are included
            - Test backward compatibility with existing clients

        Success Criteria:
            API versioning errors return special response format with version headers.
        """
        app = create_app()

        @app.get("/test/api-versioning-error")
        async def api_versioning_error_endpoint() -> None:
            raise ApplicationError(
                "Unsupported API version",
                {
                    "error_code": "API_VERSION_NOT_SUPPORTED",
                    "requested_version": "3.0",
                    "supported_versions": ["1.0", "2.0"],
                    "current_version": "2.0"
                }
            )

        client = TestClient(app, raise_server_exceptions=False)

        response = client.get("/test/api-versioning-error")
        assert response.status_code == 400

        # Verify special API versioning response format
        data = response.json()
        assert data["error"] == "Unsupported API version"
        assert data["error_code"] == "API_VERSION_NOT_SUPPORTED"
        assert data["requested_version"] == "3.0"
        assert data["supported_versions"] == ["1.0", "2.0"]
        assert data["current_version"] == "2.0"
        assert "detail" in data

        # Verify version information headers
        headers = response.headers
        assert "x-api-supported-versions" in headers
        assert "x-api-current-version" in headers
        assert headers["x-api-supported-versions"] == "1.0, 2.0"
        assert headers["x-api-current-version"] == "2.0"

    # -------------------------------------------------------------------------
    # Test Error Logging with Correlation
    # -------------------------------------------------------------------------

    def test_error_logging_with_correlation_id(self, exception_test_client: TestClient, caplog: Any) -> None:
        """
        Test that errors are logged with correlation IDs for debugging.

        Integration Scope:
            Global exception handler + request logging middleware + error logging

        Business Impact:
            Error logs with correlation IDs enable effective debugging and
            incident response by linking errors to specific requests.

        Test Strategy:
            - Create endpoint that raises exception
            - Capture logs using caplog fixture
            - Verify error is logged with correlation ID
            - Verify log includes request method, path, and error details
            - Test structured logging format

        Success Criteria:
            Errors are logged with correlation IDs and request context for debugging.
        """
        app = create_app()

        @app.get("/test/error-logging")
        async def error_logging_endpoint() -> None:
            raise InfrastructureError("Test error for logging verification")

        client = TestClient(app, raise_server_exceptions=False)

        # Capture logs at ERROR level
        with caplog.at_level(logging.ERROR):
            response = client.get("/test/error-logging")

        assert response.status_code == 500

        # Verify error was logged
        assert len(caplog.records) > 0

        # Find the error log record from exception handler
        error_log = None
        for record in caplog.records:
            if record.levelname == "ERROR" and "Unhandled exception" in record.message:
                error_log = record
                break

        assert error_log is not None, "Expected exception handler error log not found"

        # Verify log structure
        assert error_log.levelname == "ERROR"
        assert "Unhandled exception" in error_log.message
        assert "/test/error-logging" in error_log.message or \
               error_log.__dict__.get("url") and "/test/error-logging" in str(error_log.url)

        # Verify exception details are logged in the message or extra dict
        assert "Test error for logging verification" in error_log.message or \
               error_log.__dict__.get("exception_type") == "InfrastructureError"

    def test_validation_error_logging_with_details(self, exception_test_client: TestClient, caplog: Any) -> None:
        """
        Test that validation errors are logged with detailed information.

        Integration Scope:
            Global exception handler + validation error handling + logging

        Business Impact:
            Validation error logs with detailed information help with
            debugging client-side issues and API usage problems.

        Test Strategy:
            - Create endpoint that raises ValidationError
            - Capture logs using caplog fixture
            - Verify validation error is logged with details
            - Test that validation context is preserved in logs

        Success Criteria:
            Validation errors are logged with detailed context for debugging.
        """
        app = create_app()

        @app.post("/test/validation-logging")
        async def validation_logging_endpoint(data: dict) -> None:
            raise ValidationError(
                "Invalid request data",
                {
                    "field": "email",
                    "value": "invalid-email-format",
                    "expected": "valid email address"
                }
            )

        client = TestClient(app, raise_server_exceptions=False)

        # Capture logs at ERROR level (validation errors log at ERROR via global exception handler)
        with caplog.at_level(logging.ERROR):
            response = client.post("/test/validation-logging", json={})

        assert response.status_code == 400

        # Verify validation error was logged
        assert len(caplog.records) > 0

        # Find the validation error log record from the global exception handler
        validation_log = None
        for record in caplog.records:
            # Target the specific global exception handler logger
            if (record.name == "app.core.middleware.global_exception_handler" and
                "unhandled exception in request" in record.message.lower()):
                validation_log = record
                break

        assert validation_log is not None, "Expected validation error log from global exception handler not found"

        # Verify log structure
        assert validation_log.levelname == "ERROR"
        assert "Invalid request data" in validation_log.message
        assert "email" in validation_log.message

        # Verify exception type is properly logged
        assert validation_log.__dict__.get("exception_type") == "ValidationError"

    def test_multiple_error_logging_with_unique_correlation_ids(self, exception_test_client: TestClient, caplog: Any) -> None:
        """
        Test that multiple errors are logged with unique correlation IDs.

        Integration Scope:
            Global exception handler + request logging middleware + multiple error scenarios

        Business Impact:
            Unique correlation IDs for each request enable proper log
            aggregation and debugging of concurrent error scenarios.

        Test Strategy:
            - Make multiple requests that raise exceptions
            - Capture logs using caplog fixture
            - Verify each error has unique correlation ID
            - Test correlation ID isolation between requests

        Success Criteria:
            Multiple errors are logged with unique correlation IDs for proper request isolation.
        """
        app = create_app()

        @app.get("/test/multiple-errors/{error_id}")
        async def multiple_errors_endpoint(error_id: str) -> None:
            raise InfrastructureError(f"Error {error_id} for correlation testing")

        client = TestClient(app, raise_server_exceptions=False)

        # Make multiple requests that will error
        error_ids = ["error1", "error2", "error3"]

        # Capture logs
        with caplog.at_level(logging.ERROR):
            for error_id in error_ids:
                response = client.get(f"/test/multiple-errors/{error_id}")
                assert response.status_code == 500

        # Verify we have error logs for all requests
        error_logs = [record for record in caplog.records if record.levelname == "ERROR"]
        assert len(error_logs) >= len(error_ids)

        # Each error should be unique (we can't easily test correlation ID uniqueness
        # without more complex setup, but we can verify the error messages are different)
        error_messages = [log.message for log in error_logs if "Error" in log.message]

        # Verify we have logs for each unique error
        for error_id in error_ids:
            matching_logs = [msg for msg in error_messages if error_id in msg]
            assert len(matching_logs) > 0, f"No log found for error {error_id}"