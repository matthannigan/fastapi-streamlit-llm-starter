"""
Authentication and Authorization Module for FastAPI Applications.

This module provides a comprehensive, extensible authentication system built around
API key authentication with FastAPI. It supports multiple operation modes, from simple
development setups to advanced production configurations with user tracking,
permissions, and request logging.

Key Features:
    - **API Key Authentication**: Secure Bearer token authentication using configurable API keys
    - **Multiple Operation Modes**: Simple mode for development, advanced mode for production
    - **Extensible Architecture**: Built-in extension points for custom authentication logic
    - **Development Support**: Automatic development mode when no keys are configured
    - **Test Integration**: Built-in test mode support for automated testing
    - **User Tracking**: Optional user context and request metadata tracking
    - **Flexible Configuration**: Environment-based configuration with runtime reloading
    - **HTTP Exception Compatibility**: Wrapper dependencies that convert custom exceptions to proper HTTP responses

Architecture:
    The module is structured around four main components:
    
    1. **AuthConfig**: Manages authentication configuration and feature flags
    2. **APIKeyAuth**: Handles API key validation and metadata management
    3. **FastAPI Dependencies**: Provides authentication dependencies for route protection
    4. **HTTPException Wrappers**: Converts custom exceptions to FastAPI-compatible HTTP responses

Operation Modes:
    - **Simple Mode** (default): Basic API key validation without advanced features
    - **Advanced Mode**: Full feature set including user tracking and permissions
    - **Development Mode**: Automatic when no API keys configured, allows unauthenticated access
    - **Test Mode**: Special handling for automated tests with test keys

Configuration:
    The module supports configuration through environment variables:
    
    - `AUTH_MODE`: "simple" (default) or "advanced"
    - `ENABLE_USER_TRACKING`: Enable user context tracking ("true"/"false")
    - `ENABLE_REQUEST_LOGGING`: Enable request metadata logging ("true"/"false")
    - `API_KEY`: Primary API key for authentication
    - `ADDITIONAL_API_KEYS`: Comma-separated additional API keys
    - `PYTEST_CURRENT_TEST`: Automatically set by pytest for test mode

Usage Examples:
    Basic API key protection:
        ```python
        from fastapi import FastAPI, Depends
        from app.infrastructure.security.auth import verify_api_key
        
        app = FastAPI()
        
        @app.get("/protected")
        async def protected_endpoint(api_key: str = Depends(verify_api_key)):
            return {"message": "Access granted", "key": api_key}
        ```
    
    With metadata tracking:
        ```python
        from app.infrastructure.security.auth import verify_api_key_with_metadata
        
        @app.get("/protected-with-metadata")
        async def protected_with_metadata(
            auth_data: dict = Depends(verify_api_key_with_metadata)
        ):
            return {
                "message": "Access granted",
                "auth_data": auth_data
            }
        ```
    
    Optional authentication:
        ```python
        from app.infrastructure.security.auth import optional_verify_api_key
        
        @app.get("/optional-auth")
        async def optional_auth(api_key: str = Depends(optional_verify_api_key)):
            if api_key:
                return {"message": "Authenticated access", "key": api_key}
            return {"message": "Anonymous access"}
        ```
    
    Manual key verification:
        ```python
        from app.infrastructure.security.auth import verify_api_key_string
        
        def custom_logic(key: str):
            if verify_api_key_string(key):
                return "Valid key"
            return "Invalid key"
        ```
    
    HTTP Exception compatibility (recommended for FastAPI endpoints):
        ```python
        from app.infrastructure.security.auth import verify_api_key_http
        
        @app.post("/internal/cache/invalidate")
        async def protected_endpoint(api_key: str = Depends(verify_api_key_http)):
            # This dependency automatically converts AuthenticationError to 401 HTTPException
            # Avoids middleware conflicts and provides clean HTTP responses
            return {"message": "Authenticated access", "key": api_key}
        ```

Extension Points:
    The module provides several extension points for customization:
    
    - **Key Metadata**: Add custom metadata to API keys via `_key_metadata`
    - **Request Context**: Extend `add_request_metadata()` for custom request tracking
    - **Authentication Logic**: Override `verify_api_key()` for custom validation
    - **Configuration**: Extend `AuthConfig` for additional configuration options

Security Considerations:
    - API keys are stored in memory and loaded from environment variables
    - Invalid authentication attempts are logged with truncated key information
    - Test mode only activates when `PYTEST_CURRENT_TEST` is set
    - Development mode warnings are logged when no keys are configured
    - Bearer token authentication follows RFC 6750 standard

Dependencies:
    - FastAPI: Web framework and security utilities
    - Python logging: For authentication event logging
    - Environment variables: For configuration management

Thread Safety:
    The module is thread-safe for read operations. Key reloading via `reload_keys()`
    should be used carefully in multi-threaded environments.

Performance:
    - API key verification is O(1) using set-based lookups
    - Metadata operations are O(1) dictionary lookups
    - Minimal overhead for simple mode operations

Error Handling:
    The module provides two approaches for error handling:
    
    **Standard Dependencies** (verify_api_key, optional_verify_api_key):
    - Raise `AuthenticationError` custom exceptions
    - Handled by global exception handlers
    - May cause middleware conflicts in dependency injection
    
    **HTTP Wrapper Dependencies** (verify_api_key_http - recommended):
    - Convert `AuthenticationError` to `HTTPException` automatically
    - Return proper `401 Unauthorized` responses with detailed error messages
    - Include WWW-Authenticate headers and structured error context
    - Avoid middleware conflicts and provide clean HTTP responses
    - Preserve original error messages and debugging context
    
    Both approaches support graceful degradation in development mode

Version: 1.0.0
Author: FastAPI LLM Starter Team
License: MIT
"""

import os
import sys
import logging
from typing import Optional, Dict, Any
from fastapi import Depends, status, HTTPException
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings
from app.core.exceptions import AuthenticationError


class AuthConfig:
    """
    Authentication configuration manager with environment-based settings and extensibility hooks.
    
    Manages authentication behavior, feature flags, and operation modes through environment
    variables, providing a flexible foundation for both simple API key validation and
    advanced user management systems.
    
    Attributes:
        simple_mode: bool indicating basic API key validation mode (default)
        enable_user_tracking: bool for user context and session tracking
        enable_request_logging: bool for request metadata collection
        
    Public Methods:
        supports_user_context: Property indicating user context availability
        
    State Management:
        - Environment-driven configuration with sensible defaults
        - Immutable configuration after initialization
        - Extension points for custom authentication logic
        - Thread-safe operation for concurrent request handling
        
    Usage:
        # Default configuration for simple API key authentication
        config = AuthConfig()
        
        # Environment-based configuration
        # AUTH_MODE=advanced ENABLE_USER_TRACKING=true
        config = AuthConfig()
        if not config.simple_mode:
            print("Advanced authentication features enabled")
            
        # Extension point usage
        class CustomAuthConfig(AuthConfig):
            def supports_permissions(self) -> bool:
                return True
    """

    def __init__(self):
        ...

    @property
    def supports_user_context(self) -> bool:
        """
        Check if advanced user context is supported.
        """
        ...

    @property
    def supports_permissions(self) -> bool:
        """
        Check if permission-based access control is supported.
        """
        ...

    @property
    def supports_rate_limiting(self) -> bool:
        """
        Check if rate limiting is supported.
        """
        ...

    def get_auth_info(self) -> Dict[str, Any]:
        """
        Get current authentication configuration info.
        """
        ...


class APIKeyAuth:
    """
    API key authentication handler with multi-key support and extensible metadata management.
    
    Provides secure API key validation with support for multiple keys, development mode,
    test integration, and extensibility hooks for advanced authentication requirements.
    Handles Bearer token extraction, validation, and optional user context management.
    
    Attributes:
        config: AuthConfig instance controlling authentication behavior
        api_keys: Set[str] containing valid API keys for authentication
        _key_metadata: Dict[str, Dict[str, Any]] extensible metadata per API key
        
    Public Methods:
        authenticate(): Primary authentication method with Bearer token validation
        get_user_context(): Extract user information from authenticated requests
        add_key_metadata(): Associate metadata with specific API keys
        
    State Management:
        - Thread-safe API key validation for concurrent requests
        - Immutable key set after initialization (reload required for changes)
        - Extensible metadata system for custom authentication logic
        - Development and test mode support with automatic fallbacks
        
    Usage:
        # Basic API key authentication
        auth = APIKeyAuth()
        api_key = await auth.authenticate("Bearer sk-abc123")
        
        # Advanced usage with user context
        config = AuthConfig()
        auth = APIKeyAuth(config)
        if config.supports_user_context:
            user_info = auth.get_user_context(api_key)
            
        # Extension with metadata
        auth.add_key_metadata("sk-abc123", {
            "user_id": "user_123",
            "permissions": ["read", "write"]
        })
    """

    def __init__(self, auth_config: Optional[AuthConfig] = None):
        ...

    def verify_api_key(self, api_key: str) -> bool:
        """
        Verify if the provided API key is valid.
        """
        ...

    def get_key_metadata(self, api_key: str) -> Dict[str, Any]:
        """
        Get metadata for an API key (extension point for advanced auth).
        """
        ...

    def add_request_metadata(self, api_key: str, request_info: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add request metadata (extension point for advanced features).
        """
        ...

    def reload_keys(self):
        """
        Reload API keys from environment variables with metadata consistency.
        
        Performs complete key and metadata refresh from current environment state,
        ensuring consistent state between api_keys and _key_metadata.
        
        Behavior:
            - Clears existing metadata to prevent orphaned entries
            - Reloads API keys from current environment variables
            - Regenerates metadata for new keys when user tracking is enabled
            - Maintains consistent state between keys and metadata
            - Logs reload completion for operational monitoring
        
        Use Cases:
            - Runtime key rotation without application restart
            - Adding or removing API keys during operation
            - Updating key metadata after configuration changes
        
        Thread Safety:
            Use carefully in multi-threaded environments as this modifies
            internal state. Consider implementing proper locking if needed.
        """
        ...


async def verify_api_key(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> str:
    """
    Dependency to verify API key authentication.
    
    Args:
        credentials: HTTP Bearer credentials from the request
        
    Returns:
        The verified API key
        
    Raises:
        AuthenticationError: If authentication fails (missing or invalid API key)
    """
    ...


async def verify_api_key_with_metadata(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Dict[str, Any]:
    """
    Enhanced dependency that returns API key with metadata (extension point).
    
    Returns:
        Dictionary with api_key and metadata
    """
    ...


async def optional_verify_api_key(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> Optional[str]:
    """
    Optional dependency to verify API key authentication.
    Returns None if no credentials provided, otherwise verifies the key.
    
    Args:
        credentials: HTTP Bearer credentials from the request
        
    Returns:
        The verified API key or None if no credentials provided
        
    Raises:
        HTTPException: If invalid credentials are provided
    """
    ...


def verify_api_key_string(api_key: str) -> bool:
    """
    Manually verify an API key string.
    
    Args:
        api_key: The API key to verify
        
    Returns:
        True if valid, False otherwise
    """
    ...


def get_auth_status() -> Dict[str, Any]:
    """
    Get current authentication system status and capabilities.
    
    Returns:
        Dictionary with auth system information
    """
    ...


def is_development_mode() -> bool:
    """
    Check if running in development mode (no auth configured).
    """
    ...


def supports_feature(feature: str) -> bool:
    """
    Check if a specific authentication feature is supported.
    
    Args:
        feature: Feature name ('user_context', 'permissions', 'rate_limiting', etc.)
        
    Returns:
        True if feature is supported
    """
    ...


async def verify_api_key_http(credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)) -> str:
    """
    Dependency wrapper that converts AuthenticationError to HTTPException.
    
    This wrapper catches AuthenticationError exceptions from verify_api_key and
    converts them to HTTPException which FastAPI handles more gracefully with
    the middleware stack, avoiding "response already started" conflicts.
    
    Args:
        credentials: HTTP Bearer credentials from the request
        
    Returns:
        The verified API key
        
    Raises:
        HTTPException: 401 Unauthorized if authentication fails
    """
    ...
