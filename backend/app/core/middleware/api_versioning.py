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

# Configure module logger
logger = logging.getLogger(__name__)


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
        super().__init__(app)
        self.settings = settings

        # Enable/disable middleware
        self.enabled = getattr(settings, "api_versioning_enabled", True)
        # Exempt internal routes from versioning by default
        self.skip_internal_paths = getattr(settings, "api_versioning_skip_internal", True)

        # Version configuration
        self.default_version = getattr(settings, "api_default_version", "1.0")
        self.current_version = getattr(settings, "api_current_version", "1.0")
        self.min_api_version = getattr(settings, "api_min_version", "1.0")
        self.max_api_version = getattr(settings, "api_max_version", "2.0")
        self.version_header = getattr(settings, "api_version_header", "X-API-Version")

        # Parse supported versions from settings
        supported_versions_list = getattr(settings, "api_supported_versions", ["1.0", "2.0"])
        self.supported_versions_list = supported_versions_list

        # Build supported_versions dictionary from list
        self.supported_versions = {}
        for ver in self.supported_versions_list:
            major_version = ver.split(".")[0]
            self.supported_versions[ver] = {
                "status": "current" if ver == self.current_version else "supported",
                "deprecated": False,
                "sunset_date": None,
                "path_prefix": f"/v{major_version}"
            }

        # Version detection strategies in order of preference
        self.version_strategies = [
            self._get_version_from_path,
            self._get_version_from_header,
            self._get_version_from_query,
            self._get_default_version
        ]

        # Path patterns for version extraction
        self.version_path_pattern = re.compile(r"^/v(\d+(?:\.\d+)?)")

        # Header names to check for version
        self.version_headers = ["api-version", "x-api-version", "version"]

        # Accept header pattern for media type versioning
        self.accept_version_pattern = re.compile(
            r"application/vnd\.[\w\-\.]+\+json;?\s*version=(\d+(?:\.\d+)?)"
        )

    def _normalize_version(self, version_str: str) -> str | None:
        """
        Normalize version string to standard major.minor format.

        Converts various version string formats (v1, 1, 1.0, v1.5) to consistent
        major.minor format (1.0, 1.5) for reliable comparison and routing.

        Args:
            version_str: Version string to normalize. Can include 'v' prefix,
                        be in major-only format, or already in major.minor format.
                        Examples: "v1", "1", "v1.5", "1.0", "2.3.4"

        Returns:
            Normalized version string in major.minor format (e.g., "1.0", "2.3")
            or None if the input cannot be parsed as a valid version.

        Behavior:
            - Removes 'v' prefix if present (case-insensitive)
            - Parses version using packaging.version for robust handling
            - Converts major-only versions to major.minor format (e.g., "1" → "1.0")
            - Preserves major.minor format for already normalized versions
            - Returns None for malformed or unparsable version strings

        Examples:
            >>> _normalize_version("v1")
            '1.0'
            >>> _normalize_version("1.5")
            '1.5'
            >>> _normalize_version("v2.3.4")
            '2.3'
            >>> _normalize_version("invalid")
            None
        """
        if not version_str:
            return None

        try:
            # Remove 'v' prefix if present
            if version_str.lower().startswith("v"):
                version_str = version_str[1:]

            # Parse and normalize using packaging.version
            parsed = version.parse(version_str)

            # Convert back to string in major.minor format
            if hasattr(parsed, "major") and hasattr(parsed, "minor"):
                return f"{parsed.major}.{parsed.minor}"
            if hasattr(parsed, "major"):
                return f"{parsed.major}.0"
            return version_str

        except Exception:
            return None

    def _validate_version_format(self, version_str: str) -> Tuple[bool, str | None]:
        """
        Validate that a version string follows proper semantic versioning format.

        Validates version strings against strict numeric patterns to distinguish between
        missing versions and malformed version specifications. This enables proper error
        handling for invalid version formats while allowing graceful fallback for missing versions.

        Args:
            version_str: Raw version string to validate. Can include 'v' prefix, be in
                        major-only format (e.g., "1", "v1"), or major.minor format
                        (e.g., "1.0", "v1.5"). Empty or None values are handled.

        Returns:
            Tuple of (is_valid, normalized_version) where:
            - is_valid: True if version format is valid and parseable, False otherwise
            - normalized_version: Normalized version string in "major.minor" format if valid,
                                None if invalid or not parseable

        Behavior:
            - Validates against numeric pattern: digits optionally followed by dot and more digits
            - Accepts 'v' prefix (case-insensitive) and removes it during validation
            - Normalizes major-only versions to major.minor format (e.g., "1" → "1.0")
            - Rejects completely invalid formats (non-numeric, special characters, malformed)
            - Returns False for None, empty strings, or strings with invalid characters
            - Used by version detection strategies to distinguish "no version" from "malformed version"
            - Enables 400 error responses for invalid formats instead of silent fallback

        Examples:
            >>> # Valid formats with normalization
            >>> _validate_version_format("1.0")
            (True, '1.0')
            >>> _validate_version_format("v1.5")
            (True, '1.5')
            >>> _validate_version_format("2")
            (True, '2.0')

            >>> # Invalid formats
            >>> _validate_version_format("1.2.3")
            (True, '1.2')  # Truncated to major.minor
            >>> _validate_version_format("v1.2beta")
            (False, None)
            >>> _validate_version_format("invalid")
            (False, None)
            >>> _validate_version_format("")
            (False, None)
            >>> _validate_version_format(None)
            (False, None)

            >>> # Edge cases
            >>> _validate_version_format("v")
            (False, None)
            >>> _validate_version_format("1..2")
            (False, None)
        """
        if not version_str:
            return False, None

        # Check for valid version pattern: digits optionally followed by .digits
        import re
        if not re.match(r'^\d+(\.\d+)*$', version_str):
            # Try removing 'v' prefix and re-check
            if version_str.lower().startswith('v'):
                clean_version = version_str[1:]
                if not re.match(r'^\d+(\.\d+)*$', clean_version):
                    return False, None
            else:
                return False, None

        # Try to normalize and parse the version
        normalized = self._normalize_version(version_str)
        return normalized is not None, normalized

    def _get_version_with_validation(self, version_str: str, strategy_name: str) -> Tuple[str | None, str | None]:
        """
        Extract and validate version from detection strategy with proper error handling.

        Centralizes version validation logic for all detection strategies, ensuring consistent
        error reporting and validation behavior across path, header, query, and Accept header
        strategies. Enables clear distinction between missing versions and malformed formats.

        Args:
            version_str: Raw version string extracted by the detection strategy. Can be
                        empty string, None, or any format that the strategy encountered.
                        Examples: "1.0", "v2", "invalid", "", None
            strategy_name: Human-readable name of the detection strategy for error reporting.
                          Used to provide specific error messages indicating where the invalid
                          format was found. Examples: "path", "header 'X-API-Version'",
                          "query parameter", "Accept header"

        Returns:
            Tuple of (version, error) where:
            - version: Normalized version string in "major.minor" format if valid, None if
                      not found, malformed, or empty
            - error: Descriptive error message if format is invalid, None if valid or not found.
                    Includes strategy name and specific format requirements.

        Behavior:
            - Returns (None, None) for empty or None version_str (no version present)
            - Validates format using _validate_version_format() for consistency
            - Generates descriptive error messages including strategy location
            - Provides specific guidance on valid format examples in error messages
            - Enables 400 error responses for malformed versions instead of silent fallback
            - Centralizes validation logic to avoid code duplication across strategies
            - Maintains backward compatibility for missing versions while rejecting malformed ones

        Examples:
            >>> # Valid version extraction
            >>> _get_version_with_validation("1.0", "path")
            ('1.0', None)
            >>> _get_version_with_validation("v2.5", "header")
            ('2.5', None)

            >>> # No version present (not an error)
            >>> _get_version_with_validation("", "query parameter")
            (None, None)
            >>> _get_version_with_validation(None, "Accept header")
            (None, None)

            >>> # Invalid format with error reporting
            >>> _get_version_with_validation("invalid", "path")
            (None, "Invalid version format in path: 'invalid'. Version must be numeric (e.g., '1.0', '2.1')")
            >>> _get_version_with_validation("1.2beta", "header 'X-API-Version'")
            (None, "Invalid version format in header 'X-API-Version': '1.2beta'. Version must be numeric (e.g., '1.0', '2.1')")

            >>> # Strategy-specific error context
            >>> _get_version_with_validation("bad-version", "query parameter")
            (None, "Invalid version format in query parameter: 'bad-version'. Version must be numeric (e.g., '1.0', '2.1')")
        """
        if not version_str:
            return None, None

        is_valid, normalized = self._validate_version_format(version_str)
        if not is_valid:
            error_msg = f"Invalid version format in {strategy_name}: '{version_str}'. Version must be numeric (e.g., '1.0', '2.1')"
            return None, error_msg

        return normalized, None

    def _get_version_from_path(self, request: Request) -> str | None:
        """Extract version from URL path."""
        match = self.version_path_pattern.match(request.url.path)
        if match:
            return self._normalize_version(match.group(1))
        return None

    def _get_version_from_header(self, request: Request) -> str | None:
        """Extract version from HTTP headers."""
        # Check dedicated version headers (case insensitive)
        for header_name in self.version_headers:
            version_str = request.headers.get(header_name)
            if version_str:
                return self._normalize_version(version_str)

        # Also check the configured version header
        version_str = request.headers.get(self.version_header)
        if version_str:
            return self._normalize_version(version_str)

        # Check Accept header for media type versioning
        accept_header = request.headers.get("accept", "")
        match = self.accept_version_pattern.search(accept_header)
        if match:
            return self._normalize_version(match.group(1))

        return None

    def _get_version_from_query(self, request: Request) -> str | None:
        """Extract version from query parameters."""
        version_str = request.query_params.get("version") or request.query_params.get("api_version")
        if version_str:
            return self._normalize_version(version_str)
        return None

    def _get_default_version(self, request: Request) -> str:
        """Return the default version."""
        return self.default_version

    def _detect_api_version(self, request: Request) -> Tuple[str, str]:
        """
        Detect API version from request using multiple strategies with comprehensive validation.

        Applies the configured version detection strategies sequentially until a valid version
        is found or defaults to the configured default version. Validates all detected versions
        for proper format and raises descriptive errors for malformed version specifications
        instead of silently falling back to defaults.

        Args:
            request: The FastAPI Request object containing URL, headers, and query
                    parameters to be analyzed for version information. The request should
                    be a fully formed FastAPI request with all standard attributes.

        Returns:
            Tuple of (detected_version, detection_method) where:
            - detected_version: The API version string in normalized major.minor format
            - detection_method: Name of the strategy that detected the version
                              ('path', 'header', 'query', 'accept', 'default')

        Raises:
            ValueError: If malformed version formats are detected in any strategy.
                        Error message includes specific details about where the invalid
                        format was found and what constitutes a valid format.

        Behavior:
            - Applies version strategies in configured precedence order: path → header → query → accept → default
            - Validates all detected version strings using _get_version_with_validation()
            - Returns first successfully detected and validated version, even if unsupported
            - Collects all validation errors and raises ValueError if any malformed versions found
            - Falls back to default version only if no version information is present (not for invalid formats)
            - Normalizes all valid versions to major.minor format for consistency
            - Strategy names are derived from method names for debugging and analytics
            - Enables precise error reporting for debugging client version specification issues

        Examples:
            >>> # Valid path-based detection: /v1/users
            >>> _detect_api_version(request_with_v1_path)
            ('1.0', 'path')

            >>> # Valid header-based detection: X-API-Version: 2.0
            >>> _detect_api_version(request_with_version_header)
            ('2.0', 'header')

            >>> # Valid query parameter detection: ?version=1.5
            >>> _detect_api_version(request_with_version_query)
            ('1.5', 'query')

            >>> # Valid Accept header detection: Accept: application/vnd.api+json;version=2.1
            >>> _detect_api_version(request_with_accept_version)
            ('2.1', 'accept')

            >>> # Default fallback when no version present
            >>> _detect_api_version(request_without_version)
            ('1.0', 'default')

            >>> # Error case: malformed version in path
            >>> _detect_api_version(request_with_malformed_path)
            ValueError: Invalid API version format: Invalid version format in path: '1.2beta'. Version must be numeric (e.g., '1.0', '2.1')

            >>> # Error case: malformed version in header
            >>> _detect_api_version(request_with_malformed_header)
            ValueError: Invalid API version format: Invalid version format in header 'X-API-Version': 'invalid-version'. Version must be numeric (e.g., '1.0', '2.1')

        Detection Strategy Order:
            1. Path: Extracts version from URL patterns like /v1/, /v2/, /v1.5/
            2. Header: Checks X-API-Version, API-Version, and configured version headers
            3. Query: Looks for version or api_version query parameters
            4. Accept: Parses media type versioning from Accept header
            5. Default: Returns configured default version

        Error Handling:
            - All malformed version formats across all strategies are collected
            - Single ValueError raised with combined error messages for all invalid formats
            - Errors include strategy location and format guidance
            - Enables clients to identify and fix version specification issues
        """
        # Check for malformed versions first, before processing strategies
        validation_errors = []

        # Strategy 1: Path-based detection
        match = self.version_path_pattern.match(request.url.path)
        if match:
            version_str = match.group(1)
            version, error = self._get_version_with_validation(version_str, "path")
            if error:
                validation_errors.append(error)
            elif version:
                return version, "path"

        # Strategy 2: Header-based detection
        for header_name in self.version_headers:
            version_str = request.headers.get(header_name)
            if version_str:
                version, error = self._get_version_with_validation(version_str, f"header '{header_name}'")
                if error:
                    validation_errors.append(error)
                elif version:
                    return version, "header"

        # Check configured version header
        version_str = request.headers.get(self.version_header)
        if version_str:
            version, error = self._get_version_with_validation(version_str, f"header '{self.version_header}'")
            if error:
                validation_errors.append(error)
            elif version:
                return version, "header"

        # Strategy 3: Query parameter detection
        version_str = request.query_params.get("version") or request.query_params.get("api_version")
        if version_str:
            version, error = self._get_version_with_validation(version_str, "query parameter")
            if error:
                validation_errors.append(error)
            elif version:
                return version, "query"

        # Strategy 4: Accept header detection
        accept_header = request.headers.get("accept", "")
        match = self.accept_version_pattern.search(accept_header)
        if match:
            version_str = match.group(1)
            version, error = self._get_version_with_validation(version_str, "Accept header")
            if error:
                validation_errors.append(error)
            elif version:
                return version, "accept"

        # If we found malformed versions, raise an exception
        if validation_errors:
            # This will be caught by the middleware and converted to a 400 response
            raise ValueError(f"Invalid API version format: {'; '.join(validation_errors)}")

        # Strategy 5: Default fallback
        return self.default_version, "default"

    def _is_version_supported(self, requested_version: str) -> bool:
        """Check if the requested version is supported."""
        return requested_version in self.supported_versions_list

    def _get_version_info(self, version_str: str) -> Dict[str, Any]:
        """Get detailed information about a version."""
        return self.supported_versions.get(version_str, {})

    def _create_version_headers(self, request_version: str, detection_method: str) -> Dict[str, str]:
        """Create version-related response headers."""
        version_info = self._get_version_info(request_version)

        headers = {
            self.version_header: request_version,  # Use configured header name
            "X-API-Version-Detection": detection_method,
            "X-API-Supported-Versions": ", ".join(self.supported_versions_list),
            "X-API-Current-Version": self.current_version,
        }

        # Add deprecation headers if version is deprecated
        if version_info.get("deprecated"):
            headers["Deprecation"] = "true"
            if version_info.get("sunset_date"):
                headers["Sunset"] = version_info["sunset_date"]
            headers["Link"] = '</docs/migration>; rel="deprecation"'

        return headers

    def _should_redirect_version(self, request: Request, detected_version: str) -> str | None:
        """Determine if request should be redirected to a different version."""
        # If version is not supported, try to find a compatible version
        if not self._is_version_supported(detected_version):
            # Try to find the closest supported version
            try:
                requested = version.parse(detected_version)
                compatible_versions = []

                for supported_ver in self.supported_versions.keys():
                    supported = version.parse(supported_ver)
                    # Same major version is considered compatible
                    if supported.major == requested.major:
                        compatible_versions.append((supported_ver, supported))

                if compatible_versions:
                    # Return the highest compatible version
                    compatible_versions.sort(key=lambda x: x[1], reverse=True)
                    return compatible_versions[0][0]

            except Exception:
                pass

        return None

    def _rewrite_request_path(self, request: Request, target_version: str) -> str:
        """Rewrite request path for version routing."""
        current_path = request.url.path
        version_info = self._get_version_info(target_version)
        target_prefix = version_info.get("path_prefix", f'/v{target_version.split(".")[0]}')

        # Remove existing version prefix if present
        path_without_version = re.sub(r"^/v\d+(?:\.\d+)?", "", current_path)

        # Add target version prefix
        return f"{target_prefix}{path_without_version}"

    def _is_health_check_path(self, path: str) -> bool:
        """Check if the path is a health check endpoint that should bypass versioning."""
        health_check_paths = {"/health", "/healthz", "/ping", "/status", "/readiness", "/liveness"}
        return path in health_check_paths or path.startswith("/health/")

    def _is_root_or_docs_path(self, path: str) -> bool:
        """Check if the path is the root or documentation/schema endpoints.

        These endpoints should not be rewritten by API versioning, since they
        are intentionally unversioned and live at stable paths.
        """
        # Stable, unversioned paths that must be accessible without a prefix
        unversioned_paths = {
            "/",
            "/docs",
            "/openapi.json",
            "/redoc",
        }
        return path in unversioned_paths

    def _is_internal_path(self, path: str) -> bool:
        """Check if the path targets the internal API and should bypass public versioning.

        Internal API is mounted at /internal and should not be rewritten with
        public version prefixes like /v1. This prevents paths such as
        /internal/resilience/health from becoming /v1/internal/resilience/health.
        """
        if not self.skip_internal_paths:
            return False
        return path == "/internal" or path.startswith("/internal/")

    def _is_test_path(self, path: str) -> bool:
        """
        Determine if a request path targets test endpoints that should bypass versioning.

        Identifies test endpoint paths used in integration testing scenarios. These paths
        are exempt from version detection and path rewriting to ensure consistent routing
        behavior during automated testing without requiring version prefixes.

        Args:
            path: The request URL path to evaluate. Should be the raw path from the request
                  URL, without query parameters. Examples: "/test/health", "/test/auth",
                  "/api/v1/users", "/internal/health"

        Returns:
            True if the path starts with "/test/", indicating it's a test endpoint that
            should bypass all versioning logic. False for all other paths.

        Behavior:
            - Bypasses versioning for all paths beginning with "/test/" prefix
            - Prevents version prefix rewriting for test endpoints (e.g., avoids "/v1/test/health")
            - Enables direct access to test endpoints without version specification
            - Supports integration testing scenarios where consistent endpoint access is required
            - Works alongside other bypass methods (health checks, internal API, docs)
            - Simple prefix-based check for performance and predictability

        Examples:
            >>> # Test endpoints (bypass versioning)
            >>> _is_test_path("/test/health")
            True
            >>> _is_test_path("/test/auth/validate")
            True
            >>> _is_test_path("/test/v1/users")  # Still a test path despite "v1" in name
            True

            >>> # Non-test endpoints (subject to versioning)
            >>> _is_test_path("/api/v1/users")
            False
            >>> _is_test_path("/v1/health")
            False
            >>> _is_test_path("/internal/resilience/health")
            False
            >>> _is_test_path("/docs")
            False
            >>> _is_test_path("/")
            False

        Integration Testing Usage:
            Test endpoints can be accessed directly without version specification:
            - GET /test/health - Health check for test suite setup
            - POST /test/auth - Authentication testing endpoint
            - GET /test/cache - Cache behavior verification endpoint

        Note:
            This method is called early in the dispatch() method before any version
            detection logic, ensuring test endpoints bypass all versioning processing.
        """
        return path.startswith("/test/")

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

        # Skip processing if middleware is disabled
        if not self.enabled:
            return await call_next(request)

        # Skip versioning for health check endpoints
        if self._is_health_check_path(request.url.path):
            return await call_next(request)

        # Skip versioning for root and docs/schema endpoints
        if self._is_root_or_docs_path(request.url.path):
            return await call_next(request)

        # Skip versioning for internal API endpoints
        if self._is_internal_path(request.url.path):
            return await call_next(request)

        # Skip versioning for test endpoints (used in integration tests)
        if self._is_test_path(request.url.path):
            return await call_next(request)

        # 1. Detect requested API version
        try:
            detected_version, detection_method = self._detect_api_version(request)
        except ValueError as e:
            # Handle malformed version format errors
            return JSONResponse(
                status_code=400,
                content={
                    "error": "Invalid API version format",
                    "error_code": "API_VERSION_FORMAT_INVALID",
                    "detail": str(e),
                    "supported_versions": self.supported_versions_list,
                    "current_version": self.current_version,
                },
                headers={
                    "X-API-Supported-Versions": ", ".join(self.supported_versions_list),
                    "X-API-Current-Version": self.current_version,
                },
            )

        # 2. Check if version is supported
        if not self._is_version_supported(detected_version):
            # Try to find a compatible version
            compatible_version = self._should_redirect_version(request, detected_version)

            if compatible_version:
                # Log version compatibility redirect
                logger.info(
                    f"API version compatibility: {detected_version} -> {compatible_version} "
                    f"for {request.method} {request.url.path}"
                )
                detected_version = compatible_version
            else:
                # Version not supported and no compatible version found
                # Return a JSON error directly for compatibility in apps/tests
                # that do not configure the global exception handler.
                return JSONResponse(
                    status_code=400,
                    content={
                        "error": "Unsupported API version",
                        "error_code": "API_VERSION_NOT_SUPPORTED",
                        "requested_version": detected_version,
                        "supported_versions": self.supported_versions_list,
                        "current_version": self.current_version,
                        "detail": f"API version '{detected_version}' is not supported",
                    },
                    headers={
                        "X-API-Supported-Versions": ", ".join(self.supported_versions_list),
                        "X-API-Current-Version": self.current_version,
                    },
                )

        # 3. Add version info to request state
        request.state.api_version = detected_version
        request.state.api_version_detection_method = detection_method
        request.state.api_version_info = self._get_version_info(detected_version)

        # 4. Rewrite request path if necessary for routing
        original_path = request.url.path
        version_info = self._get_version_info(detected_version)
        expected_prefix = version_info.get("path_prefix", f'/v{detected_version.split(".")[0]}')

        if not original_path.startswith(expected_prefix):
            new_path = self._rewrite_request_path(request, detected_version)
            # Update the request scope path for routing
            request.scope["path"] = new_path
            request.scope["raw_path"] = new_path.encode()

        # 5. Process the request
        response = await call_next(request)

        # 6. Add version headers to response
        version_headers = self._create_version_headers(detected_version, detection_method)
        for header, value in version_headers.items():
            response.headers[header] = value

        # 7. Log version usage for analytics
        logger.debug(
            f"API version used: {detected_version} ({detection_method}) "
            f"for {request.method} {original_path}"
        )

        return response


class VersionCompatibilityMiddleware(BaseHTTPMiddleware):
    """
    Middleware for handling backward compatibility transformations.

    This middleware can transform requests and responses to maintain
    compatibility between different API versions.
    """

    def __init__(self, app: ASGIApp, settings: Settings):
        super().__init__(app)
        self.settings = settings

        # Version compatibility rules
        self.compatibility_rules = {
            # Transform v1.0 requests to v2.0 format
            ("1.0", "2.0"): {
                "request_transformers": [
                    self._transform_v1_to_v2_request
                ],
                "response_transformers": [
                    self._transform_v2_to_v1_response
                ]
            }
        }

    def _transform_v1_to_v2_request(self, request_data: dict) -> dict:
        """Transform v1.0 request format to v2.0 format."""
        # Example transformation: rename fields, restructure data
        if "text" in request_data:
            request_data["input_text"] = request_data.pop("text")

        if "options" in request_data:
            request_data["processing_options"] = request_data.pop("options")

        return request_data

    def _transform_v2_to_v1_response(self, response_data: dict) -> dict:
        """Transform v2.0 response format to v1.0 format."""
        # Example transformation: rename fields, restructure data
        if "processed_text" in response_data:
            response_data["result"] = response_data.pop("processed_text")

        if "metadata" in response_data:
            response_data["info"] = response_data.pop("metadata")

        return response_data

    async def dispatch(self, request: Request, call_next: Callable[[Request], Any]) -> Response:
        """Apply version compatibility transformations."""
        api_version = getattr(request.state, "api_version", None)

        if not api_version:
            return await call_next(request)

        # Check if compatibility transformation is needed
        target_version = self.settings.current_api_version
        compatibility_key = (api_version, target_version)

        if compatibility_key not in self.compatibility_rules:
            return await call_next(request)

        rules = self.compatibility_rules[compatibility_key]

        # Transform request if necessary
        if rules.get("request_transformers") and request.method in ["POST", "PUT", "PATCH"]:
            try:
                body = await request.body()
                if body:
                    import json
                    request_data = json.loads(body)

                    for transformer in rules["request_transformers"]:
                        request_data = transformer(request_data)

                    # Create new request with transformed data
                    transformed_body = json.dumps(request_data).encode()

                    async def new_receive():
                        return {
                            "type": "http.request",
                            "body": transformed_body,
                            "more_body": False
                        }

                    request._receive = new_receive

            except Exception as e:
                logger.warning(f"Failed to transform request for compatibility: {e}")

        # Process request
        response = await call_next(request)

        # Transform response if necessary
        if rules.get("response_transformers") and hasattr(response, "body"):
            try:
                import json
                response_data = json.loads(response.body)

                for transformer in rules["response_transformers"]:
                    response_data = transformer(response_data)

                response.body = json.dumps(response_data).encode()
                response.headers["content-length"] = str(len(response.body))

            except Exception as e:
                logger.warning(f"Failed to transform response for compatibility: {e}")

        return response


# Utility functions for version management
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
    return getattr(request.state, "api_version", "1.0")


def is_version_deprecated(request: Request) -> bool:
    """Check if the current API version is deprecated."""
    version_info = getattr(request.state, "api_version_info", {})
    return version_info.get("deprecated", False)


def get_version_sunset_date(request: Request) -> str | None:
    """Get the sunset date for the current API version."""
    version_info = getattr(request.state, "api_version_info", {})
    return version_info.get("sunset_date")


# Settings additions for API versioning
class APIVersioningSettings:
    """API versioning configuration settings."""

    # Default API version to use when none specified
    default_api_version: str = "1.0"

    # Current/latest API version
    current_api_version: str = "1.0"

    # Minimum supported API version
    min_api_version: str = "1.0"

    # Maximum supported API version
    max_api_version: str = "2.0"

    # Enable version compatibility transformations
    api_version_compatibility_enabled: bool = True

    # Enable version analytics and logging
    version_analytics_enabled: bool = True

    # Skip applying versioning to internal API routes mounted at /internal
    api_versioning_skip_internal: bool = True


# Additional utility functions for testing and external use
def extract_version_from_url(path: str) -> str | None:
    """Extract version from URL path (e.g., /v1/users -> 1.0)."""
    if not path:
        return None

    # Match patterns like /v1/, /v2/, /v1.5/, etc.
    version_match = re.match(r"^/v(\d+(?:\.\d+)?)", path)
    if version_match:
        version_str = version_match.group(1)
        # Convert to standard format (e.g., "1" -> "1.0")
        if "." not in version_str:
            version_str += ".0"
        return version_str

    return None


def extract_version_from_header(request: Request, header_name: str) -> str | None:
    """Extract version from request header."""
    # Try exact match first (for real FastAPI headers which are case-insensitive)
    result = request.headers.get(header_name)
    if result:
        return result

    # For tests with mock headers, also try lowercase versions
    if hasattr(request.headers, "get"):
        # Try lowercase version of requested header
        result = request.headers.get(header_name.lower())
        if result:
            return result

        # Try searching through all headers case-insensitively
        for key, value in request.headers.items():
            if key.lower() == header_name.lower():
                return value

    return None


def extract_version_from_accept(request: Request) -> str | None:
    """Extract version from Accept header (e.g., application/vnd.api+json;version=2.0)."""
    accept_header = request.headers.get("accept", "")
    if not accept_header:
        return None

    # Look for version parameter in Accept header
    version_match = re.search(r"version=([0-9]+(?:\.[0-9]+)?)", accept_header)
    if version_match:
        return version_match.group(1)

    return None


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
    return version_str in supported_versions if version_str else False


def rewrite_path_for_version(path: str, target_version: str) -> str:
    """Rewrite path to include version prefix."""
    if not path or not target_version:
        return path

    # Convert version to URL format (e.g., "1.0" -> "v1", "1.5" -> "v1.5")
    if target_version.endswith(".0"):
        url_version = f"v{target_version[:-2]}"
    else:
        url_version = f"v{target_version}"

    # If path already has version, replace it
    if re.match(r"^/v\d+(?:\.\d+)?", path):
        return re.sub(r"^/v\d+(?:\.\d+)?", f"/{url_version}", path)

    # If path is root, just add version
    if path == "/":
        return f"/{url_version}"

    # Otherwise, prepend version
    return f"/{url_version}{path}"


def add_version_headers(response: Response, current_version: str, supported_versions: list, header_name: str = "X-API-Version") -> None:
    """Add version information to response headers."""
    response.headers[header_name] = current_version
    response.headers["X-API-Supported-Versions"] = ", ".join(sorted(supported_versions))


class APIVersionNotSupported(ApplicationError):
    """Exception raised when an unsupported API version is requested."""
    def __init__(self, message: str, requested_version: str, supported_versions: list[str], current_version: str):
        context = {
            "requested_version": requested_version,
            "supported_versions": supported_versions,
            "current_version": current_version,
            "error_code": "API_VERSION_NOT_SUPPORTED",
        }
        super().__init__(message, context)
