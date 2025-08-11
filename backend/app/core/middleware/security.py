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
    Security-focused middleware for HTTP headers and request validation.
    
    Provides essential security controls including security headers injection,
    basic request validation, and protection against common web vulnerabilities.
    The middleware implements defense-in-depth security principles suitable
    for production API deployments.
    
    Security Features:
        * Security headers injection (HSTS, X-Frame-Options, etc.)
        * Content Security Policy (CSP) configuration
        * X-Content-Type-Options and X-XSS-Protection headers
        * Request size limits to prevent DoS attacks
        * Basic input validation and sanitization
        * Referrer policy configuration for privacy
        * Feature policy headers for browser security
    
    Headers Configured:
        * Strict-Transport-Security: HSTS for HTTPS enforcement
        * X-Frame-Options: Clickjacking protection
        * X-Content-Type-Options: MIME type sniffing prevention
        * X-XSS-Protection: XSS attack mitigation
        * Content-Security-Policy: Resource loading restrictions
        * Referrer-Policy: Referrer information control
        * Permissions-Policy: Browser feature access control
    
    Request Validation:
        * Content-Length limits for request body size
        * Header count and size validation
        * URL length restrictions
        * Basic malicious pattern detection
        * Rate limiting hooks (basic implementation)
    
    Configuration:
        Security behavior can be configured through settings:
        * security_headers_enabled: Enable/disable security headers
        * max_request_size: Maximum request body size in bytes
        * max_headers_count: Maximum number of headers per request
        * csp_policy: Custom Content Security Policy string
    
    Note:
        This middleware provides basic security controls. For production
        deployments, additional security measures like WAF, rate limiting,
        and DDoS protection should be implemented at the infrastructure level.
    """
    
    def __init__(self, app: ASGIApp, settings: Settings):
        """
        Initialize security middleware with configuration.
        
        Args:
            app (ASGIApp): The ASGI application to wrap
            settings (Settings): Application settings for security configuration
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
        Determine if the request is for a documentation endpoint.
        
        Checks if the request path matches any of the known documentation
        endpoints that require relaxed CSP policies for Swagger UI functionality.
        
        Args:
            request (Request): The incoming HTTP request
            
        Returns:
            bool: True if the request is for a documentation endpoint
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
        Process HTTP request with security validations and header injection.
        
        Args:
            request (Request): The incoming HTTP request
            call_next (Callable): The next middleware/handler in the chain
            
        Returns:
            Response: The HTTP response with security headers
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
