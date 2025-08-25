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
        ...

    async def dispatch(self, request: Request, call_next: Callable[[Request], Any]) -> Response:
        """
        Process HTTP request with security validations and header injection.
        
        Args:
            request (Request): The incoming HTTP request
            call_next (Callable): The next middleware/handler in the chain
            
        Returns:
            Response: The HTTP response with security headers
        """
        ...
