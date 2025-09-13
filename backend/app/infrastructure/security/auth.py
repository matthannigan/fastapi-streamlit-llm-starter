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

logger = logging.getLogger(__name__)

# HTTP Bearer security scheme
security = HTTPBearer(auto_error=False)

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
        # Can be overridden via environment variable
        self.simple_mode: bool = os.getenv("AUTH_MODE", "simple").lower() == "simple"
        self.enable_user_tracking: bool = os.getenv("ENABLE_USER_TRACKING", "false").lower() == "true"
        self.enable_request_logging: bool = os.getenv("ENABLE_REQUEST_LOGGING", "false").lower() == "true"
    
    @property
    def supports_user_context(self) -> bool:
        """Check if advanced user context is supported."""
        return not self.simple_mode
    
    @property
    def supports_permissions(self) -> bool:
        """Check if permission-based access control is supported."""
        return not self.simple_mode
    
    @property
    def supports_rate_limiting(self) -> bool:
        """Check if rate limiting is supported."""
        return not self.simple_mode
    
    def get_auth_info(self) -> Dict[str, Any]:
        """Get current authentication configuration info."""
        return {
            "mode": "simple" if self.simple_mode else "advanced",
            "features": {
                "user_context": self.supports_user_context,
                "permissions": self.supports_permissions,
                "rate_limiting": self.supports_rate_limiting,
                "user_tracking": self.enable_user_tracking,
                "request_logging": self.enable_request_logging
            }
        }

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
        self.config = auth_config or AuthConfig()
        
        # Extension point: metadata can be added for advanced auth
        self._key_metadata: Dict[str, Dict[str, Any]] = {}
        
        self.api_keys = self._load_api_keys()
    
    def _load_api_keys(self) -> set:
        """Load API keys from environment variables."""
        api_keys = set()
        
        # Primary API key
        primary_key = settings.api_key
        if primary_key:
            api_keys.add(primary_key)
            # Extension point: add metadata for this key
            if self.config.enable_user_tracking:
                self._key_metadata[primary_key] = {
                    "type": "primary",
                    "created_at": "system",
                    "permissions": ["read", "write"]  # Default permissions
                }
        
        # Additional API keys (comma-separated)
        additional_keys = settings.additional_api_keys
        if additional_keys:
            keys = [key.strip() for key in additional_keys.split(",") if key.strip()]
            api_keys.update(keys)
            
            # Extension point: add metadata for additional keys
            if self.config.enable_user_tracking:
                for key in keys:
                    self._key_metadata[key] = {
                        "type": "additional",
                        "created_at": "system",
                        "permissions": ["read", "write"]
                    }
        
        if not api_keys:
            _IS_PYTEST = ("pytest" in sys.modules) or bool(os.getenv("PYTEST_CURRENT_TEST"))
            if not _IS_PYTEST:
                logger.warning("No API keys configured. API endpoints will be unprotected!")
        else:
            logger.info(f"Loaded {len(api_keys)} API key(s) in {self.config.get_auth_info()['mode']} mode")
        
        return api_keys
    
    def verify_api_key(self, api_key: str) -> bool:
        """Verify if the provided API key is valid."""
        return api_key in self.api_keys
    
    def get_key_metadata(self, api_key: str) -> Dict[str, Any]:
        """Get metadata for an API key (extension point for advanced auth)."""
        if not self.config.enable_user_tracking:
            return {}
        return self._key_metadata.get(api_key, {})
    
    def add_request_metadata(self, api_key: str, request_info: Dict[str, Any]) -> Dict[str, Any]:
        """Add request metadata (extension point for advanced features)."""
        metadata = {"api_key_type": "simple"}
        
        if self.config.enable_user_tracking:
            key_meta = self.get_key_metadata(api_key)
            metadata.update({
                "key_type": key_meta.get("type", "unknown"),
                "permissions": key_meta.get("permissions", [])
            })
        
        if self.config.enable_request_logging:
            metadata.update({
                "timestamp": request_info.get("timestamp", "unknown"),
                "endpoint": request_info.get("endpoint", "unknown"),
                "method": request_info.get("method", "unknown")
            })
        
        return metadata
    
    def reload_keys(self):
        """Reload API keys from environment (useful for runtime updates)."""
        self.api_keys = self._load_api_keys()

# Global instances
auth_config = AuthConfig()
api_key_auth = APIKeyAuth(auth_config)

async def verify_api_key(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> str:
    """
    Dependency to verify API key authentication.
    
    Args:
        credentials: HTTP Bearer credentials from the request
        
    Returns:
        The verified API key
        
    Raises:
        AuthenticationError: If authentication fails (missing or invalid API key)
    """
    # Check if we're in test mode
    if os.getenv("PYTEST_CURRENT_TEST"):  # pytest sets this automatically
        # In test mode, accept a specific test key or allow development mode
        test_key = "test-api-key-12345"
        if credentials and credentials.credentials == test_key:
            return test_key
        elif not api_key_auth.api_keys:  # Development mode
            return "development"
    
    # If no API keys are configured, allow access (development mode)
    if not api_key_auth.api_keys:
        logger.warning("No API keys configured - allowing unauthenticated access")
        return "development"
    
    # Check if credentials are provided
    if not credentials:
        raise AuthenticationError(
            "API key required. Please provide a valid API key in the Authorization header.",
            context={"auth_method": "bearer_token", "credentials_provided": False}
        )
    
    # Verify the API key
    if not api_key_auth.verify_api_key(credentials.credentials):
        logger.warning(f"Invalid API key attempted: {credentials.credentials[:8]}...")
        raise AuthenticationError(
            "Invalid API key",
            context={
                "auth_method": "bearer_token", 
                "key_prefix": credentials.credentials[:8],
                "credentials_provided": True
            }
        )
    
    logger.debug("API key authentication successful")
    return credentials.credentials

async def verify_api_key_with_metadata(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Dict[str, Any]:
    """
    Enhanced dependency that returns API key with metadata (extension point).
    
    Returns:
        Dictionary with api_key and metadata
    """
    api_key = await verify_api_key(credentials)
    
    # Extension point: return metadata along with key
    result = {"api_key": api_key}
    
    if auth_config.enable_user_tracking or auth_config.enable_request_logging:
        metadata = api_key_auth.add_request_metadata(api_key, {
            "timestamp": "now",  # In real implementation, use actual timestamp
            "endpoint": "unknown",  # In real implementation, extract from request
            "method": "unknown"
        })
        result.update(metadata)
    
    return result

async def optional_verify_api_key(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> Optional[str]:
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
    if not credentials:
        return None
    
    # If credentials are provided, they must be valid
    return await verify_api_key(credentials)

# Convenience functions
def verify_api_key_string(api_key: str) -> bool:
    """
    Manually verify an API key string.
    
    Args:
        api_key: The API key to verify
        
    Returns:
        True if valid, False otherwise
    """
    return api_key_auth.verify_api_key(api_key)

def get_auth_status() -> Dict[str, Any]:
    """
    Get current authentication system status and capabilities.
    
    Returns:
        Dictionary with auth system information
    """
    return {
        "auth_config": auth_config.get_auth_info(),
        "api_keys_configured": len(api_key_auth.api_keys),
        "development_mode": len(api_key_auth.api_keys) == 0
    }

def is_development_mode() -> bool:
    """Check if running in development mode (no auth configured)."""
    return len(api_key_auth.api_keys) == 0

def supports_feature(feature: str) -> bool:
    """
    Check if a specific authentication feature is supported.
    
    Args:
        feature: Feature name ('user_context', 'permissions', 'rate_limiting', etc.)
        
    Returns:
        True if feature is supported
    """
    feature_map = {
        'user_context': auth_config.supports_user_context,
        'permissions': auth_config.supports_permissions,
        'rate_limiting': auth_config.supports_rate_limiting,
        'user_tracking': auth_config.enable_user_tracking,
        'request_logging': auth_config.enable_request_logging
    }
    return feature_map.get(feature, False)

# ============================================================================
# HTTPException Wrapper Dependencies for FastAPI Compatibility
# ============================================================================

async def verify_api_key_http(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> str:
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
    try:
        return await verify_api_key(credentials)
    except AuthenticationError as exc:
        # 1. Use the status module for clarity and standardization.
        # 2. Preserve the original, more specific error message from the exception.
        # 3. Include the exception's context for better debugging, just like your global handler.
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": str(exc), "context": exc.context},
            headers={"WWW-Authenticate": "Bearer"}
        )
