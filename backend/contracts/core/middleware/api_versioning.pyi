"""
API Versioning Middleware

## Overview

Robust API version detection and routing with support for URL prefix, headers,
query parameters, and Accept media types. Adds response headers with current
and supported versions, and can perform compatibility transformations.

Now includes a safe-by-default exemption for internal routes mounted at `/internal/*`
so that administrative endpoints are not rewritten with public API version prefixes.

## Detection Strategies

- **Path**: `/v1/`, `/v2/`, `/v1.5/`
- **Headers**: `X-API-Version`, `API-Version`, or custom via settings
- **Query**: `?version=1.0` or `?api_version=1.0`
- **Accept**: `application/vnd.api+json;version=2.0`

## Behavior

- Writes detected version and method to `request.state`
- Rejects unsupported versions with a stable JSON payload and
  `X-API-Supported-Versions`/`X-API-Current-Version` headers
- Optionally rewrites paths to the expected version prefix
- Skips versioning for health-check paths (e.g., `/health`, `/readiness`)
- Skips versioning for internal API paths (e.g., `/internal/resilience/health`) to
  prevent unintended rewrites like `/v1/internal/resilience/health`

## Configuration

Configured via `app.core.config.Settings` and helper settings in this module:

- `api_versioning_enabled`, `default_api_version`, `current_api_version`
- `min_api_version`, `max_api_version`, `api_supported_versions`
- `api_version_compatibility_enabled`, `api_version_header`
- `api_versioning_skip_internal` (bool, default: True)
  - When True, requests whose path is `/internal` or starts with `/internal/`
    bypass version detection and path rewriting

## Examples

```text
Request:  GET /internal/resilience/health
Before:   (could be rewritten to /v1/internal/resilience/health)
After:    Versioning bypassed; remains /internal/resilience/health
```

## Usage

```python
from app.core.middleware.api_versioning import APIVersioningMiddleware
from app.core.config import settings

app.add_middleware(APIVersioningMiddleware, settings=settings)
```
"""

import logging
import re
from typing import Dict, Tuple, Callable, Any
from packaging import version
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.types import ASGIApp
from fastapi import Request, Response
from fastapi.responses import JSONResponse
from app.core.config import Settings
from app.core.exceptions import ApplicationError


class APIVersioningMiddleware(BaseHTTPMiddleware):
    """
    Production-grade API versioning middleware with multiple detection strategies and comprehensive compatibility handling.
    
    Provides robust API version detection and routing with support for URL prefixes, headers,
    query parameters, and Accept media types. Ensures backward compatibility through intelligent
    version matching and handles deprecation scenarios with appropriate headers and warnings.
    
    Attributes:
        enabled (bool): Whether the middleware is active for processing requests
        skip_internal_paths (bool): Whether to bypass versioning for internal API routes
        default_version (str): Default version used when no version is detected
        current_version (str): The latest/current API version
        min_api_version (str): Minimum supported API version
        max_api_version (str): Maximum supported API version
        version_header (str): Header name used for version responses
        supported_versions_list (List[str]): List of all supported API versions
        supported_versions (Dict[str, Dict]): Detailed version information with status and metadata
    
    Public Methods:
        dispatch(): Main middleware entry point for request processing
        _normalize_version(): Converts version strings to standard format
        _detect_api_version(): Extracts version using multiple strategies
        _is_version_supported(): Validates if a version is supported
    
    State Management:
        - Version detection uses configurable strategy hierarchy (path → header → query → default)
        - Request state is populated with detected version information for downstream use
        - Version compatibility is maintained through intelligent version matching
        - Thread-safe through request-scoped state management
    
    Usage:
        # Basic setup with default settings
        from app.core.middleware.api_versioning import APIVersioningMiddleware
        from app.core.config import settings
    
        app.add_middleware(APIVersioningMiddleware, settings=settings)
    
        # Requests now support multiple versioning strategies:
        # Path: GET /v1/users
        # Header: GET /users with "X-API-Version: 1.0"
        # Query: GET /users?version=1.0
        # Accept: GET /users with "Accept: application/vnd.api+json;version=1.0"
    
        # Access version information in endpoints
        @app.get("/users")
        async def get_users(request: Request):
            api_version = getattr(request.state, 'api_version', '1.0')
            detection_method = getattr(request.state, 'api_version_detection_method', 'default')
            return {"version": api_version, "method": detection_method}
    
    Version Detection Strategy:
        The middleware applies strategies in order of precedence:
        1. Path-based extraction from URL patterns like /v1/, /v2/, /v1.5/
        2. Header-based extraction from X-API-Version, API-Version, or custom headers
        3. Query parameter extraction from ?version=1.0 or ?api_version=1.0
        4. Accept header media type versioning
        5. Default version fallback
    
    Internal API Bypass:
        Internal routes mounted at /internal/* automatically bypass versioning
        to prevent unintended path rewrites like /v1/internal/resilience/health.
        This behavior is configurable via the api_versioning_skip_internal setting.
    
    Note:
        The middleware adds comprehensive version headers to responses including
        X-API-Version, X-API-Supported-Versions, X-API-Current-Version, and
        deprecation headers when applicable. Health check and documentation
        endpoints also bypass versioning for accessibility.
    """

    def __init__(self, app: ASGIApp, settings: Settings):
        ...

    async def dispatch(self, request: Request, call_next: Callable[[Request], Any]) -> Response:
        """
        Process HTTP request with comprehensive API versioning, validation, and compatibility handling.
        
        Main middleware entry point that orchestrates version detection, validation, routing,
        and response header management. Handles malformed version formats and unsupported versions
        with structured error responses while maintaining backward compatibility.
        
        Args:
            request: FastAPI Request object to be processed for version detection and routing
            call_next: ASGI callable to invoke the next middleware/endpoint in the request chain
        
        Returns:
            FastAPI Response object with comprehensive version headers added. May return a
            JSONResponse error for malformed or unsupported version specifications.
        
        Raises:
            None (all errors are returned as structured JSON responses with appropriate headers)
        
        Behavior:
            - Skips processing entirely if middleware is disabled via configuration
            - Bypasses versioning for health check, docs, internal API, and test endpoints
            - Detects API version using configured strategy hierarchy with format validation
            - Returns 400 structured error for malformed version formats with helpful guidance
            - Returns 400 structured error for unsupported versions with compatibility suggestions
            - Attempts intelligent compatibility matching for unsupported but similar versions
            - Populates request.state with version information for downstream middleware/endpoints
            - Rewrites request paths for proper routing to versioned endpoints
            - Adds comprehensive version headers to all successful responses
            - Logs version usage and errors for analytics and debugging
        
        Bypassed Paths (versioning skipped):
            - Health check endpoints: /health, /readiness, /ping, /status, /liveness
            - Documentation endpoints: /, /docs, /openapi.json, /redoc
            - Internal API endpoints: /internal/* (configurable bypass)
            - Test endpoints: /test/* (for integration testing)
        
        Error Responses:
            - 400 Bad Request for malformed version formats (API_VERSION_FORMAT_INVALID)
            - 400 Bad Request for unsupported versions (API_VERSION_NOT_SUPPORTED)
            - Both error types include supported_versions and current_version in response body
            - Both error types include X-API-Supported-Versions and X-API-Current-Version headers
        
        Response Headers Added (successful responses):
            X-API-Version: The API version used for processing
            X-API-Version-Detection: Strategy used for version detection (path, header, query, accept, default)
            X-API-Supported-Versions: Comma-separated list of supported versions
            X-API-Current-Version: The latest/current API version
            Deprecation: Set to 'true' for deprecated versions
            Sunset: Sunset date for deprecated versions
            Link: Link to migration documentation for deprecated versions
        
        Examples:
            >>> # Valid version request with successful processing
            >>> response = await dispatch(request_with_v1, call_next)
            >>> response.headers['X-API-Version']
            '1.0'
            >>> response.headers['X-API-Version-Detection']
            'path'
        
            >>> # Malformed version format request
            >>> response = await dispatch(request_with_malformed_version, call_next)
            >>> response.status_code
            400
            >>> response.json()['error_code']
            'API_VERSION_FORMAT_INVALID'
            >>> 'Version must be numeric' in response.json()['detail']
            True
        
            >>> # Unsupported version request
            >>> response = await dispatch(request_with_v5, call_next)
            >>> response.status_code
            400
            >>> response.json()['error_code']
            'API_VERSION_NOT_SUPPORTED'
            >>> response.json()['supported_versions']
            ['1.0', '2.0']
        
            >>> # Test endpoint bypass
            >>> response = await dispatch(request_to_test_endpoint, call_next)
            >>> response.status_code
            200
            >>> 'X-API-Version' in response.headers
            False
        
        Request State Added (for downstream use):
            request.state.api_version: The detected/validated version string
            request.state.api_version_detection_method: Strategy used for detection
            request.state.api_version_info: Detailed version metadata (status, deprecation info)
        
        Note:
            This method ensures thread safety through request-scoped state management and
            maintains backward compatibility while providing clear error messages and migration
            paths for deprecated or malformed version specifications.
        """
        ...


class VersionCompatibilityMiddleware(BaseHTTPMiddleware):
    """
    Middleware for handling backward compatibility transformations.
    
    This middleware can transform requests and responses to maintain
    compatibility between different API versions.
    """

    def __init__(self, app: ASGIApp, settings: Settings):
        ...

    async def dispatch(self, request: Request, call_next: Callable[[Request], Any]) -> Response:
        """
        Apply version compatibility transformations.
        """
        ...


class APIVersioningSettings:
    """
    API versioning configuration settings.
    """

    ...


class APIVersionNotSupported(ApplicationError):
    """
    Exception raised when an unsupported API version is requested.
    """

    def __init__(self, message: str, requested_version: str, supported_versions: list[str], current_version: str):
        ...


def get_api_version(request: Request) -> str:
    """
    Extract the API version used for processing the current request.
    
    Utility function for endpoints and middleware to access the API version
    that was detected and used by the APIVersioningMiddleware for processing
    the current request.
    
    Args:
        request: FastAPI Request object that has been processed by
                APIVersioningMiddleware
    
    Returns:
        API version string in major.minor format (e.g., "1.0", "2.3").
        Returns "1.0" if no version was set by the middleware.
    
    Behavior:
            - Reads version from request.state.api_version set by middleware
            - Returns default version if middleware didn't set version information
            - Useful for endpoints that need to adapt behavior based on API version
            - Provides consistent access pattern across the application
    
        Examples:
            >>> @app.get("/endpoint")
            ... async def get_endpoint(request: Request):
            ...     version = get_api_version(request)
            ...     if version == "1.0":
            ...         return {"data": "v1 format"}
            ...     else:
            ...         return {"data": "v2 format"}
    
            >>> # Get version from request processed by middleware
            >>> version = get_api_version(processed_request)
            >>> version
            '1.0'
    """
    ...


def is_version_deprecated(request: Request) -> bool:
    """
    Check if the current API version is deprecated.
    """
    ...


def get_version_sunset_date(request: Request) -> str | None:
    """
    Get the sunset date for the current API version.
    """
    ...


def extract_version_from_url(path: str) -> str | None:
    """
    Extract version from URL path (e.g., /v1/users -> 1.0).
    """
    ...


def extract_version_from_header(request: Request, header_name: str) -> str | None:
    """
    Extract version from request header.
    """
    ...


def extract_version_from_accept(request: Request) -> str | None:
    """
    Extract version from Accept header (e.g., application/vnd.api+json;version=2.0).
    """
    ...


def validate_api_version(version_str: str, supported_versions: list) -> bool:
    """
    Validate if a version string is in the list of supported versions.
    
    Utility function for validating API versions against a supported
    versions list, commonly used for testing and validation logic.
    
    Args:
        version_str: Version string to validate (e.g., "1.0", "2.3")
        supported_versions: List of supported version strings (e.g., ["1.0", "2.0"])
    
    Returns:
        True if the version is in the supported_versions list, False otherwise.
        Returns False for empty or None version strings.
    
    Behavior:
            - Performs exact string matching against supported versions list
            - Case-sensitive comparison (versions should be normalized before validation)
            - Returns False for None, empty, or whitespace-only version strings
            - Used by middleware for version support validation
            - Useful for custom validation logic outside of middleware flow
    
        Examples:
            >>> validate_api_version("1.0", ["1.0", "2.0"])
            True
    
            >>> validate_api_version("3.0", ["1.0", "2.0"])
            False
    
            >>> validate_api_version("", ["1.0", "2.0"])
            False
    
            >>> validate_api_version(None, ["1.0", "2.0"])
            False
    """
    ...


def rewrite_path_for_version(path: str, target_version: str) -> str:
    """
    Rewrite path to include version prefix.
    """
    ...


def add_version_headers(response: Response, current_version: str, supported_versions: list, header_name: str = 'X-API-Version') -> None:
    """
    Add version information to response headers.
    """
    ...
