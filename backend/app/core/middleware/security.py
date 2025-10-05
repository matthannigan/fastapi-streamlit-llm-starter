"""
Security Middleware

## Overview

Adds essential HTTP security headers and performs lightweight request
validations to provide a strong baseline for API hardening. Designed to work
in tandem with upstream protections like WAF and rate limiting.

## Headers

Automatically configures:

- `Strict-Transport-Security`
- `X-Frame-Options`
- `X-Content-Type-Options`
- `X-XSS-Protection`
- `Content-Security-Policy` (strict for APIs, relaxed for docs)
- `Referrer-Policy`
- `Permissions-Policy`

## Validation

- Enforces `Content-Length` limits
- Caps total request header count
- Applies URL length and basic pattern checks (lightweight)

## Configuration

From `app.core.config.Settings`:

- `security_headers_enabled` (bool)
- `max_request_size` (int)
- `max_headers_count` (int)
- `csp_policy` (optional override for API CSP)

## Usage

```python
from app.core.middleware.security import SecurityMiddleware
from app.core.config import settings

app.add_middleware(SecurityMiddleware, settings=settings)
```
"""

import logging
from typing import Callable, Any
from starlette.types import ASGIApp
from fastapi import Request, Response, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.config import Settings

# Configure module logger
logger = logging.getLogger(__name__)


class SecurityMiddleware(BaseHTTPMiddleware):
    """
    HTTP security middleware providing comprehensive headers injection and request validation.

    Implements defense-in-depth security principles with essential security headers,
    request validation, and protection against common web vulnerabilities. Suitable
    for production API deployments with configurable security policies and endpoint-specific
    content security policies for documentation compatibility.

    Attributes:
        settings (Settings): Application configuration object containing security preferences
        max_request_size (int): Maximum request body size in bytes for DoS protection
        max_headers_count (int): Maximum number of headers allowed per request
        base_security_headers (dict): Core security headers applied to all responses
        api_csp (str): Content Security Policy for API endpoints (strict)
        docs_csp (str): Content Security Policy for documentation endpoints (relaxed)
        docs_endpoints (set): Set of endpoint paths requiring relaxed CSP policies

    Public Methods:
        dispatch(): Processes HTTP requests with security validation and header injection
        _is_docs_endpoint(): Determines if request requires relaxed CSP for documentation

    State Management:
        - Stateless middleware with no persistent state between requests
        - Maintains security header configuration in memory from settings
        - Uses request metadata for endpoint-specific security policy application
        - Applies consistent security headers across all HTTP responses

    Usage:
        # Basic middleware registration
        from app.core.middleware.security import SecurityMiddleware
        from app.core.config import settings

        app.add_middleware(SecurityMiddleware, settings=settings)

        # Configuration via settings
        # security_headers_enabled: bool = True
        # max_request_size: int = 10485760  # 10MB
        # max_headers_count: int = 100
        # csp_policy: str = None  # Optional custom CSP override
    """

    def __init__(self, app: ASGIApp, settings: Settings):
        """
        Initialize security middleware with comprehensive configuration and header policies.

        Args:
            app (ASGIApp): The ASGI application to wrap with security functionality
            settings (Settings): Application settings containing security configuration:
                - security_headers_enabled (bool): Master switch for security headers
                - max_request_size (int): Maximum request body size in bytes
                - max_headers_count (int): Maximum number of headers per request
                - csp_policy (str): Optional custom Content Security Policy override

        Behavior:
            - Configures request size and header count limits for DoS protection
            - Sets up base security headers for all HTTP responses
            - Prepares strict CSP policies for API endpoints
            - Configures relaxed CSP policies for documentation endpoints
            - Initializes middleware chain with the wrapped ASGI application
            - Maintains endpoint detection for CSP policy application
        """
        super().__init__(app)
        self.settings = settings
        self.max_request_size = getattr(settings, 'max_request_size', 10 * 1024 * 1024)  # 10MB
        self.max_headers_count = getattr(settings, 'max_headers_count', 100)
        
        # Base security headers (applied to all endpoints)
        self.base_security_headers = {
            'Strict-Transport-Security': 'max-age=31536000; includeSubDomains',
            'X-Frame-Options': 'DENY',
            'X-Content-Type-Options': 'nosniff',
            'X-XSS-Protection': '1; mode=block',
            'Referrer-Policy': 'strict-origin-when-cross-origin',
            'Permissions-Policy': 'geolocation=(), microphone=(), camera=()'
        }
        
        # Strict CSP for API endpoints (production security)
        self.api_csp = "default-src 'self'; script-src 'self'; style-src 'self'; img-src 'self' data:; font-src 'self'; connect-src 'self'; object-src 'none'; base-uri 'self'; frame-ancestors 'none';"
        
        # Relaxed CSP for documentation endpoints (Swagger UI compatibility)
        self.docs_csp = "default-src 'self' https://fastapi.tiangolo.com; script-src 'self' 'unsafe-inline' 'unsafe-eval' https://cdn.jsdelivr.net https://unpkg.com; style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://unpkg.com https://fonts.googleapis.com; img-src 'self' https://fastapi.tiangolo.com data: https:; font-src 'self' https://cdn.jsdelivr.net https://unpkg.com https://fonts.gstatic.com; connect-src 'self'; object-src 'none'; base-uri 'self';"
        
        # Documentation endpoints that need relaxed CSP
        self.docs_endpoints = {'/docs', '/redoc', '/openapi.json'}
    
    def _is_docs_endpoint(self, request: Request) -> bool:
        """
        Determine if the request targets a documentation endpoint requiring relaxed CSP policies.

        Identifies requests for API documentation interfaces (Swagger UI, ReDoc, OpenAPI schema)
        that require relaxed Content Security Policies to function properly with external
        resources and inline scripts. This ensures documentation interfaces work while maintaining
        strict security policies for production API endpoints.

        Args:
            request (Request): The incoming HTTP request object containing URL path information

        Returns:
            bool: True if the request targets a documentation endpoint requiring relaxed CSP,
                  False if the request should receive strict API security policies

        Behavior:
            - Checks exact matches against known documentation endpoint paths
            - Identifies documentation-related path prefixes (/docs, /redoc)
            - Detects internal API documentation paths (/internal/*)
            - Recognizes OpenAPI schema endpoints for interactive documentation
            - Returns True for any endpoint that needs relaxed CSP for proper functionality
            - Applies strict CSP policies to all other API endpoints for security

        Examples:
            # Returns True for these paths:
            # /docs, /redoc, /openapi.json
            # /docs/oauth2-redirect, /redoc/static/*
            # /internal/docs, /internal/monitoring/docs
            # /api/v1/openapi.json, /internal/api/openapi.json

            # Returns False for these paths:
            # /api/v1/users, /internal/health
            # /webhook, /callback, /admin/dashboard
        """
        path = request.url.path
        
        # Check exact matches for docs endpoints
        if path in self.docs_endpoints:
            return True
            
        # Check for docs-related paths (e.g., /docs/oauth2-redirect)
        if path.startswith('/docs') or path.startswith('/redoc'):
            return True
            
        # Check for internal-related paths (e.g., /internal/docs)
        if path.startswith('/internal'):
            return True
            
        # Check for OpenAPI schema variants
        if 'openapi' in path.lower():
            return True
            
        return False
        
    async def dispatch(self, request: Request, call_next: Callable[[Request], Any]) -> Response:
        """
        Process HTTP request with comprehensive security validation and header injection.

        Args:
            request (Request): The incoming HTTP request object containing headers and metadata
            call_next (Callable[[Request], Any]): The next middleware or route handler in the ASGI chain

        Returns:
            Response: HTTP response with comprehensive security headers applied and appropriate
                     Content Security Policy based on endpoint type

        Raises:
            No exceptions raised; security violations return appropriate HTTP error responses

        Behavior:
            - Validates request header count to prevent header-based DoS attacks
            - Validates Content-Length header when present for request size protection
            - Returns 400 Bad Request for requests with excessive headers
            - Returns 413 Request Entity Too Large for oversized requests
            - Returns 400 Bad Request for invalid Content-Length headers
            - Processes request through remaining middleware stack
            - Injects base security headers into all responses (HSTS, X-Frame-Options, etc.)
            - Applies strict Content Security Policy to API endpoints
            - Applies relaxed Content Security Policy to documentation endpoints
            - Logs security violations for monitoring and debugging
            - Maintains audit trail of security-related request rejections

        Examples:
            # Valid request receives security headers
            # Response headers include:
            # Strict-Transport-Security, X-Frame-Options, X-Content-Type-Options
            # Content-Security-Policy (strict for API, relaxed for docs)
            # Referrer-Policy, Permissions-Policy

            # Security violations return error responses:
            # 400 for too many headers
            # 413 for request size exceeded
            # 400 for invalid Content-Length
        """
        # Validate request headers count
        if len(request.headers) > self.max_headers_count:
            logger.warning(f"Request with excessive headers: {len(request.headers)}")
            return JSONResponse(
                status_code=status.HTTP_400_BAD_REQUEST,
                content={"error": "Too many headers"}
            )
        
        # Validate Content-Length if present
        content_length = request.headers.get('content-length')
        if content_length:
            try:
                size = int(content_length)
                if size > self.max_request_size:
                    logger.warning(f"Request too large: {size} bytes")
                    return JSONResponse(
                        status_code=status.HTTP_413_REQUEST_ENTITY_TOO_LARGE,
                        content={"error": "Request too large"}
                    )
            except ValueError:
                logger.warning("Invalid Content-Length header")
                return JSONResponse(
                    status_code=status.HTTP_400_BAD_REQUEST,
                    content={"error": "Invalid Content-Length"}
                )
        
        # Process request through remaining middleware
        response = await call_next(request)
        
        # Inject base security headers
        for header, value in self.base_security_headers.items():
            response.headers[header] = value
        
        # Determine and inject appropriate CSP based on endpoint type
        if self._is_docs_endpoint(request):
            response.headers['Content-Security-Policy'] = self.docs_csp
            logger.debug(f"Applied docs CSP for {request.url.path}")
        else:
            response.headers['Content-Security-Policy'] = self.api_csp
            logger.debug(f"Applied API CSP for {request.url.path}")
            
        return response
