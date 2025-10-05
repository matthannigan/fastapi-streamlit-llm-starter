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
        ...

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
        ...
