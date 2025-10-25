"""Environment-Aware Authentication and Authorization Module for FastAPI Applications.

This module provides a comprehensive, production-ready authentication system built around
API key authentication with environment-aware security enforcement. It integrates with
the unified environment detection service to provide automatic production security
validation, development mode support, and extensive operational monitoring.

## 🔐 Key Features

- **🌍 Environment-Aware Security**: Automatic production security enforcement with
  environment detection integration
- **🔑 Multi-Key API Authentication**: Secure Bearer token authentication with support
  for multiple API keys and key rotation
- **⚙️ Flexible Operation Modes**: Simple development mode to advanced production
  configurations with user tracking and permissions
- **🏗️ Extensible Architecture**: Built-in extension points for custom authentication
  logic and metadata management
- **🛠️ Development Support**: Automatic development mode when no keys are configured,
  with clear warnings and guidance
- **📊 Operational Monitoring**: Comprehensive logging, status endpoints, and
  authentication event tracking
- **🔄 HTTP Exception Compatibility**: Wrapper dependencies that convert custom
  exceptions to proper HTTP responses for middleware compatibility

## 📐 Architecture

The module follows a layered architecture with four main components:

1. **`AuthConfig`** - Environment-based configuration and feature flag management
2. **`APIKeyAuth`** - Multi-key validation with production security enforcement
3. **`FastAPI Dependencies`** - Authentication dependencies for route protection
4. **`HTTP Wrapper Dependencies`** - HTTPException conversion for middleware compatibility

## 🎛️ Operation Modes

### Development Mode
- **Trigger**: No API keys configured in environment variables
- **Behavior**: Allows unauthenticated access with warning logs
- **Use Case**: Local development and testing without security overhead

### Production Mode
- **Trigger**: Production environment detected OR API keys configured
- **Behavior**: Mandatory authentication with fail-fast security validation
- **Use Case**: Production deployments with strict security enforcement

### Advanced Mode
- **Trigger**: `AUTH_MODE=advanced` environment variable
- **Behavior**: Full feature set including user tracking and request metadata
- **Use Case**: Enterprise deployments requiring detailed audit trails

## ⚙️ Configuration

Environment variables for authentication configuration:

```bash
# Authentication Mode
AUTH_MODE=simple                    # "simple" (default) or "advanced"

# API Key Configuration
API_KEY=sk-1234567890abcdef         # Primary API key
ADDITIONAL_API_KEYS=sk-key2,sk-key3 # Comma-separated additional keys

# Advanced Features (when AUTH_MODE=advanced)
ENABLE_USER_TRACKING=true           # Enable user context tracking
ENABLE_REQUEST_LOGGING=true         # Enable request metadata logging

# Environment Detection (automatic)
ENVIRONMENT=production               # Detected automatically by environment service
```

## 🚀 Usage Examples

### Basic API Protection (Recommended)

```python
from fastapi import FastAPI, Depends
from app.infrastructure.security.auth import verify_api_key_http

app = FastAPI()

@app.get("/protected")
async def protected_endpoint(api_key: str = Depends(verify_api_key_http)):
    return {"message": "Access granted", "key_prefix": api_key[:8]}
```

### Advanced Metadata Tracking

```python
from app.infrastructure.security.auth import verify_api_key_with_metadata

@app.get("/protected-advanced")
async def protected_with_metadata(
    auth_data: dict = Depends(verify_api_key_with_metadata)
):
    return {
        "message": "Access granted",
        "api_key": auth_data["api_key"],
        "metadata": auth_data.get("metadata", {})
    }
```

### Optional Authentication

```python
from app.infrastructure.security.auth import optional_verify_api_key

@app.get("/optional-auth")
async def optional_auth(api_key: str = Depends(optional_verify_api_key)):
    if api_key and api_key != "development":
        return {"message": "Authenticated access", "key_prefix": api_key[:8]}
    return {"message": "Anonymous access"}
```

### Programmatic Validation

```python
from app.infrastructure.security.auth import verify_api_key_string

def validate_batch_request(api_key: str, data: list) -> bool:
    # Validate API key for batch processing
    if not verify_api_key_string(api_key):
        raise ValueError("Invalid API key for batch processing")
    return True
```

### System Status Monitoring

```python
from app.infrastructure.security.auth import get_auth_status

@app.get("/internal/auth/status")
async def auth_status():
    # Get authentication system status for monitoring
    return get_auth_status()
```

## 🔧 Extension Points

The module provides extensive customization capabilities:

- **Key Metadata Management**: Custom per-key metadata via `_key_metadata`
- **Request Context Tracking**: Extended request metadata via `add_request_metadata()`
- **Authentication Logic**: Custom validation by extending `APIKeyAuth.verify_api_key()`
- **Configuration Extension**: Additional options via `AuthConfig` inheritance
- **Environment Integration**: Custom environment detection via environment service

## 🛡️ Security Features

### Production Security Enforcement
- **Fail-Fast Validation**: Prevents deployment without proper API key configuration
- **Environment Detection**: Automatic security mode based on environment confidence
- **Mandatory Authentication**: Required credentials in production/staging environments
- **Security Event Logging**: Comprehensive audit trail for authentication events

### Operational Security
- **Key Rotation Support**: Runtime key reloading via `reload_keys()`
- **Truncated Logging**: Invalid attempts logged with masked key information
- **Development Warnings**: Clear guidance when security is disabled
- **RFC 6750 Compliance**: Standard Bearer token authentication implementation

## ⚡ Performance Characteristics

- **O(1) Key Validation**: Set-based lookups for API key verification
- **O(1) Metadata Access**: Dictionary-based metadata operations
- **Minimal Overhead**: Efficient operation in simple mode
- **Thread-Safe Operations**: Concurrent request handling support
- **Lazy Environment Detection**: Environment info loaded only when needed

## 🔄 Error Handling Strategies

### Standard Dependencies (`verify_api_key`, `optional_verify_api_key`)
- Raise `AuthenticationError` custom exceptions with rich context
- Handled by global exception handlers with structured error responses
- Include environment detection information and confidence scores
- May cause middleware conflicts in complex dependency injection scenarios

### HTTP Wrapper Dependencies (`verify_api_key_http` - **Recommended**)
- Convert `AuthenticationError` to `HTTPException` automatically
- Return proper `401 Unauthorized` responses with detailed error context
- Include `WWW-Authenticate` headers for proper HTTP authentication flow
- Avoid middleware conflicts and provide clean HTTP responses
- Preserve original error messages and debugging context for troubleshooting

## 🔗 Dependencies

- **FastAPI**: Web framework and security utilities (`fastapi.security.HTTPBearer`)
- **Environment Detection**: Unified environment service (`app.core.environment`)
- **Exception Handling**: Custom exception types (`app.core.exceptions`)
- **Configuration**: Application settings (`app.core.config`)
- **Python Standard Library**: `os`, `sys`, `logging`, `typing`

## 🔒 Thread Safety

- **Read Operations**: Fully thread-safe for concurrent request handling
- **Key Validation**: Thread-safe set-based lookups across multiple workers
- **Configuration Access**: Thread-safe environment variable reading
- **Key Reloading**: Use `reload_keys()` carefully in multi-threaded environments
- **Metadata Operations**: Thread-safe dictionary operations with proper locking

## 📝 Version Information

- **Version**: 2.0.0 (Environment-Aware Security Release)
- **Author**: FastAPI LLM Starter Team
- **License**: MIT
- **API Compatibility**: Backward compatible with 1.x authentication contracts
- **Environment Integration**: Requires unified environment detection service

## 🔗 Related Documentation

- **Environment Detection**: `app.core.environment` - Unified environment detection service
- **Exception Handling**: `app.core.exceptions` - Custom exception types and handling
- **FastAPI Security**: `app.api.v1.auth` - Public authentication endpoints
- **Internal Monitoring**: `app.api.internal.monitoring` - Administrative auth status
"""

import os
import sys
import logging
from typing import Dict, Any, TYPE_CHECKING
from fastapi import Depends, status, HTTPException, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from app.core.config import settings
from app.core.exceptions import AuthenticationError, ConfigurationError
from app.core.environment import get_environment_info, FeatureContext, Environment

if TYPE_CHECKING:
    from app.core.config import Settings

# Import get_settings for dependency injection
from app.dependencies import get_settings

logger = logging.getLogger(__name__)

# HTTP Bearer security scheme
security = HTTPBearer(auto_error=False)


def get_api_key_from_request(
    request: Request,
    bearer_credentials: HTTPAuthorizationCredentials | None = Depends(security)
) -> tuple[str | None, str]:
    """
    Extract API key from either Authorization Bearer or X-API-Key header.

    Supports both authentication methods:
    - Authorization: Bearer <key>
    - X-API-Key: <key>

    Args:
        request: FastAPI Request object containing headers
        bearer_credentials: HTTP Bearer credentials from Authorization header

    Returns:
        tuple: (api_key: Optional[str], auth_method: str)
               - api_key: The extracted API key or None if not found
               - auth_method: "bearer_token", "x_api_key", or "none"
    """
    # Try Bearer token first (existing implementation)
    if bearer_credentials and bearer_credentials.credentials:
        return bearer_credentials.credentials, "bearer_token"

    # Try X-API-Key header
    x_api_key = request.headers.get("X-API-Key")
    if x_api_key:
        return x_api_key, "x_api_key"

    # No authentication provided
    return None, "none"

class AuthConfig:
    """
    Authentication configuration manager providing environment-based settings and feature control.

    Manages authentication behavior modes and feature flags through environment variables,
    supporting both simple API key validation and advanced user management capabilities.

    Attributes:
        simple_mode: bool indicating basic API key validation mode (default: True)
        enable_user_tracking: bool for user context and session tracking (default: False)
        enable_request_logging: bool for request metadata collection (default: False)

    Public Methods:
        supports_user_context(): Returns True if advanced user context features are enabled
        supports_permissions(): Returns True if permission-based access control is supported
        supports_rate_limiting(): Returns True if rate limiting features are supported
        get_auth_info(): Returns comprehensive configuration information dictionary

    State Management:
        - Configuration loaded from environment variables at initialization
        - Immutable state after construction (no runtime configuration changes)
        - Thread-safe for concurrent access across request handlers
        - Extensible through inheritance for custom authentication requirements

    Behavior:
        - Reads AUTH_MODE environment variable ("simple" or "advanced", default: "simple")
        - Reads ENABLE_USER_TRACKING environment variable ("true"/"false", default: "false")
        - Reads ENABLE_REQUEST_LOGGING environment variable ("true"/"false", default: "false")
        - Provides feature capability checks through property methods
        - Returns comprehensive configuration summary via get_auth_info()
        - Supports inheritance for extending authentication capabilities

    Usage:
        # Basic authentication configuration
        config = AuthConfig()
        assert config.simple_mode is True
        assert config.supports_user_context() is False

        # Environment-driven advanced configuration
        # Set: AUTH_MODE=advanced ENABLE_USER_TRACKING=true
        config = AuthConfig()
        if not config.simple_mode:
            user_features_available = config.supports_user_context()

        # Configuration inspection
        auth_info = config.get_auth_info()
        print(f"Mode: {auth_info['mode']}")

        # Custom extension
        class CustomAuthConfig(AuthConfig):
            def supports_custom_feature(self) -> bool:
                return not self.simple_mode
    """

    def __init__(self) -> None:
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
    API key authentication handler providing multi-key validation and environment-aware security.

    Manages API key validation with support for multiple keys, production security validation,
    development mode fallbacks, and extensible metadata management for advanced authentication
    scenarios. Integrates with environment detection for production security enforcement.

    Attributes:
        config: AuthConfig instance controlling authentication behavior and feature flags
        api_keys: Set[str] containing all valid API keys loaded from environment variables
        _key_metadata: Dict[str, Dict[str, Any]] extensible per-key metadata for advanced features

    Public Methods:
        verify_api_key(api_key): Validates a single API key string against configured keys
        get_key_metadata(api_key): Retrieves metadata associated with specific API key
        add_request_metadata(api_key, request_info): Generates request-specific metadata
        reload_keys(): Reloads API keys from environment variables

    State Management:
        - API keys loaded from environment variables at initialization
        - Thread-safe key validation for concurrent request handling
        - Production security validation enforced during initialization
        - Immutable key set after initialization (use reload_keys() for updates)
        - Extensible metadata system for custom authentication requirements

    Behavior:
        - Loads API_KEY and ADDITIONAL_API_KEYS from environment variables with whitespace trimming
        - Validates production environments have API keys configured (fail-fast)
        - Falls back to production security mode if environment detection fails
        - Creates default metadata for keys when user tracking is enabled
        - Supports development mode when no keys are configured
        - Provides O(1) key validation using set-based lookups
        - Logs security events and warnings for operational monitoring
        - Enforces production security requirements via environment detection with fallback

    Usage:
        # Basic authentication setup
        auth = APIKeyAuth()
        is_valid = auth.verify_api_key("sk-1234567890abcdef")

        # Production deployment (with environment detection)
        # Automatically validates that API keys are configured in production
        auth = APIKeyAuth()  # Raises ConfigurationError if no keys in production

        # Advanced usage with custom configuration
        config = AuthConfig()
        auth = APIKeyAuth(config)

        # Add custom metadata for enhanced features
        if config.enable_user_tracking:
            metadata = auth.get_key_metadata("sk-1234567890abcdef")
            print(f"Key type: {metadata.get('type')}")

        # Runtime key management
        auth.reload_keys()  # Refresh from environment variables

        # Request-specific metadata generation
        request_data = auth.add_request_metadata("sk-key", {
            "timestamp": "2024-01-01T00:00:00Z",
            "endpoint": "/api/process",
            "method": "POST"
        })
    """

    def __init__(self, auth_config: AuthConfig | None = None):
        self.config = auth_config or AuthConfig()

        # Extension point: metadata can be added for advanced auth
        self._key_metadata: Dict[str, Dict[str, Any]] = {}

        self.api_keys = self._load_api_keys()

        # Environment-aware authentication with production validation
        self._validate_production_security()

    def _load_api_keys(self) -> set:
        """Load API keys from environment variables."""
        api_keys = set()

        # Primary API key - trim whitespace for consistency
        primary_key = settings.api_key
        if primary_key:
            primary_key = primary_key.strip()
            if primary_key:  # Only add non-empty keys after trimming
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
            is_pytest = ("pytest" in sys.modules) or bool(os.getenv("PYTEST_CURRENT_TEST"))
            if not is_pytest:
                logger.warning("No API keys configured. API endpoints will be unprotected!")
        else:
            logger.info(f"Loaded {len(api_keys)} API key(s) in {self.config.get_auth_info()['mode']} mode")

        return api_keys

    def _validate_production_security(self) -> None:
        """
        Validate production security configuration to prevent misconfiguration.

        Implements fail-fast production validation that checks API key configuration
        in production environments to prevent accidental unprotected deployments.

        Raises:
            ConfigurationError: If production environment lacks proper authentication
        """
        try:
            # Detect environment with security enforcement context
            env_info: Any = get_environment_info(FeatureContext.SECURITY_ENFORCEMENT)
        except Exception as e:
            # Fallback to conservative behavior on environment detection failure
            logger.warning(f"Environment detection failed ({e}), assuming production environment for security")
            # Create fallback environment info assuming production for safety
            from dataclasses import dataclass

            @dataclass
            class FallbackEnvironmentInfo:
                environment = Environment.PRODUCTION
                confidence = 0.5  # Low confidence due to detection failure
                reasoning = f"Environment detection failed, assuming production for security: {e}"

            env_info = FallbackEnvironmentInfo()

        # Skip validation if not in production or staging (confidence check)
        if env_info.environment not in [Environment.PRODUCTION, Environment.STAGING]:
            return

        # Check for production API key configuration
        if not self.api_keys:
            error_message = (
                f"Production security validation failed: No API keys configured in "
                f"{env_info.environment} environment (confidence: {env_info.confidence:.2f}). "
                f"Please configure API_KEY or ADDITIONAL_API_KEYS environment variables "
                f"before deploying to production."
            )

            # Include environment detection reasoning for troubleshooting
            context = {
                "environment": env_info.environment.value,
                "confidence": env_info.confidence,
                "reasoning": env_info.reasoning,
                "required_vars": ["API_KEY", "ADDITIONAL_API_KEYS"],
                "current_keys_count": len(self.api_keys)
            }

            logger.error(f"SECURITY VALIDATION FAILED: {error_message}")
            raise ConfigurationError(error_message, context=context)

        # Log successful production validation
        logger.info(
            f"Production security validation passed: {len(self.api_keys)} API key(s) "
            f"configured for {env_info.environment} environment "
            f"(confidence: {env_info.confidence:.2f})"
        )

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

    def reload_keys(self) -> None:
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
        # Clear existing metadata before reloading to ensure consistency
        self._key_metadata.clear()

        # Reload keys (this will repopulate metadata via _load_api_keys)
        self.api_keys = self._load_api_keys()

        logger.info(f"Reloaded {len(self.api_keys)} API key(s) in {self.config.get_auth_info()['mode']} mode")

# Global instances
auth_config = AuthConfig()
api_key_auth = APIKeyAuth(auth_config)

async def verify_api_key(
    request: Request,
    bearer_credentials: HTTPAuthorizationCredentials | None = Depends(security),
    settings: "Settings" = Depends(get_settings)
) -> str:
    """
    Environment-aware FastAPI dependency for API key authentication with production security.

    Validates API key authentication with environment-aware security enforcement,
    development mode support, and comprehensive error context for operational debugging.

    Args:
        request: FastAPI Request object containing headers for X-API-Key support
        bearer_credentials: HTTP Bearer authorization credentials from request headers.
                           Expected format: "Bearer sk-1234567890abcdef" or None for missing auth.
                           Automatically injected by FastAPI's HTTPBearer security scheme.
        settings: Settings instance injected via dependency for configuration isolation.

    Returns:
        str: The validated API key string when authentication succeeds.
             Returns "development" when no keys configured in development environments.
             Never returns None - always authenticates or raises exception.

    Raises:
        AuthenticationError: When authentication fails with detailed context including:
                           - Missing credentials when API keys are configured
                           - Invalid API key format or unrecognized key value
                           - Environment detection information and confidence scores
                           - Authentication method and credential status for debugging
        ConfigurationError: When production environment lacks API key configuration.

    Behavior:
        - Returns "development" immediately if no API keys are configured (development mode)
        - Validates production environments have API keys configured (fail-fast)
        - Requires valid credentials when API keys are configured in any environment
        - Validates provided API key against all configured valid keys (O(1) lookup)
        - Includes environment detection context in all error messages and logging
        - Logs security events for monitoring: warnings for no keys, invalid attempts
        - Preserves authentication flow for development, staging, and production environments
        - Fails fast with clear error messages guiding proper configuration
        - Thread-safe for concurrent request handling across multiple workers

    Examples:
        >>> # FastAPI endpoint with authentication
        >>> @app.get("/protected")
        >>> async def protected_route(api_key: str = Depends(verify_api_key)):
        ...     return {"message": "authenticated", "key_prefix": api_key[:8]}

        >>> # Development mode (no keys configured)
        >>> # GET /protected without Authorization header
        >>> # Returns: api_key = "development"

        >>> # Production mode with valid Bearer token
        >>> # GET /protected with "Authorization: Bearer sk-1234567890abcdef"
        >>> # Returns: api_key = "sk-1234567890abcdef"

        >>> # Production mode with valid X-API-Key header
        >>> # GET /protected with "X-API-Key: sk-1234567890abcdef"
        >>> # Returns: api_key = "sk-1234567890abcdef"

        >>> # Invalid authentication attempt
        >>> # GET /protected with "Authorization: Bearer invalid-key"
        >>> # Raises: AuthenticationError("Invalid API key", context={...})

        >>> # Missing credentials in production
        >>> # GET /protected without Authorization or X-API-Key headers (keys configured)
        >>> # Raises: AuthenticationError("API key required...", context={...})
    """
    # Extract API key from either Bearer or X-API-Key header
    api_key, _auth_method = get_api_key_from_request(request, bearer_credentials)

    # Get valid API keys from settings (uses dependency-injected settings)
    valid_api_keys = settings.get_valid_api_keys()

    # Validate production security - no keys configured
    if not valid_api_keys:
        try:
            # Detect environment with security enforcement context
            env_info: Any = get_environment_info(FeatureContext.SECURITY_ENFORCEMENT)
        except Exception as e:
            # Fallback to conservative behavior on environment detection failure
            logger.warning(f"Environment detection failed ({e}), assuming production environment for security")
            # Create fallback environment info assuming production for safety
            from dataclasses import dataclass

            @dataclass
            class FallbackEnvironmentInfo:
                environment = Environment.PRODUCTION
                confidence = 0.5  # Low confidence due to detection failure
                reasoning = f"Environment detection failed, assuming production for security: {e}"

            env_info = FallbackEnvironmentInfo()

        # Production/staging requires API keys
        if env_info.environment in [Environment.PRODUCTION, Environment.STAGING]:
            error_message = (
                f"Production security validation failed: No API keys configured in "
                f"{env_info.environment} environment (confidence: {env_info.confidence:.2f}). "
                f"Please configure API_KEY or ADDITIONAL_API_KEYS environment variables "
                f"before deploying to production."
            )
            context = {
                "environment": env_info.environment.value,
                "confidence": env_info.confidence,
                "reasoning": env_info.reasoning,
                "required_vars": ["API_KEY", "ADDITIONAL_API_KEYS"],
                "current_keys_count": 0
            }
            logger.error(f"SECURITY VALIDATION FAILED: {error_message}")
            raise ConfigurationError(error_message, context=context)

        # Development mode - allow unauthenticated access
        logger.warning(
            f"No API keys configured in {env_info.environment} environment "
            f"(confidence: {env_info.confidence:.2f}) - allowing unauthenticated access"
        )
        return "development"

    # Check if credentials are provided
    if not api_key:
        try:
            env_info = get_environment_info(FeatureContext.SECURITY_ENFORCEMENT)
            context = {
                "auth_method": _auth_method,
                "environment": env_info.environment.value,
                "confidence": env_info.confidence,
                "credentials_provided": False
            }
        except Exception:
            context = {"auth_method": _auth_method, "credentials_provided": False}

        from fastapi import HTTPException
        raise HTTPException(
            status_code=401,
            detail="API key required. Please provide a valid API key via 'Authorization: Bearer <key>' or 'X-API-Key: <key>' header.",
            headers={"WWW-Authenticate": "Bearer"}
        )

    # Verify the API key against valid keys from settings
    if api_key not in valid_api_keys:
        logger.warning(f"Invalid API key attempted via {_auth_method}: {api_key[:8]}...")

        try:
            env_info = get_environment_info(FeatureContext.SECURITY_ENFORCEMENT)
            context = {
                "auth_method": _auth_method,
                "environment": env_info.environment.value,
                "confidence": env_info.confidence,
                "key_prefix": api_key[:8],
                "credentials_provided": True
            }
        except Exception:
            context = {
                "auth_method": _auth_method,
                "key_prefix": api_key[:8],
                "credentials_provided": True
            }

        from fastapi import HTTPException
        raise HTTPException(
            status_code=401,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"}
        )

    logger.debug(f"API key authentication successful via {_auth_method}")
    return api_key

async def verify_api_key_with_metadata(
    request: Request,
    bearer_credentials: HTTPAuthorizationCredentials | None = Depends(security),
    settings: "Settings" = Depends(get_settings)
) -> Dict[str, Any]:
    """
    Enhanced dependency that returns API key with metadata (extension point).

    Args:
        request: FastAPI Request object containing headers for X-API-Key support
        bearer_credentials: HTTP Bearer credentials from the request
        settings: Settings instance injected via dependency for configuration isolation.

    Returns:
        Dictionary with api_key and metadata

    Raises:
        AuthenticationError: If authentication fails
        ConfigurationError: If production environment lacks API key configuration
    """
    api_key = await verify_api_key(request, bearer_credentials, settings)

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
    request: Request,
    bearer_credentials: HTTPAuthorizationCredentials | None = Depends(security),
    settings: "Settings" = Depends(get_settings)
) -> str | None:
    """
    Optional dependency to verify API key authentication.
    Returns None if no credentials provided, otherwise verifies the key.

    Args:
        request: FastAPI Request object containing headers for X-API-Key support
        bearer_credentials: HTTP Bearer credentials from the request
        settings: Settings instance injected via dependency for configuration isolation.

    Returns:
        The verified API key or None if no credentials provided

    Raises:
        AuthenticationError: If invalid credentials are provided
        ConfigurationError: If production environment lacks API key configuration
    """
    # Extract API key from either Bearer or X-API-Key header
    api_key, _auth_method = get_api_key_from_request(request, bearer_credentials)

    if not api_key:
        return None

    # If credentials are provided, they must be valid
    return await verify_api_key(request, bearer_credentials, settings)

# Convenience functions
def verify_api_key_string(api_key: str) -> bool:
    """
    Validate an API key string without HTTP request context for programmatic verification.

    Provides direct API key validation for non-HTTP contexts such as batch processing,
    background tasks, or programmatic authentication checks without FastAPI dependencies.

    Args:
        api_key: The API key string to validate.
                Must be complete API key (e.g., "sk-1234567890abcdef").
                Empty strings, None, or malformed keys return False.

    Returns:
        bool: True if the API key is valid and configured in the system.
              False if invalid, empty, None, or not found in configured keys.
              False if no API keys are configured (development mode).

    Behavior:
        - Performs O(1) lookup against configured API key set
        - Returns False immediately for None or empty string inputs
        - Case-sensitive exact string matching (no normalization)
        - Thread-safe for concurrent access from multiple contexts
        - No logging or error raising - silent validation for programmatic use
        - Works independently of HTTP context or FastAPI dependencies

    Examples:
        >>> # Programmatic validation
        >>> is_valid = verify_api_key_string("sk-1234567890abcdef")
        >>> assert is_valid is True

        >>> # Invalid key validation
        >>> is_valid = verify_api_key_string("invalid-key")
        >>> assert is_valid is False

        >>> # Empty or None handling
        >>> assert verify_api_key_string("") is False
        >>> assert verify_api_key_string(None) is False

        >>> # Background task authentication
        >>> def process_batch(api_key: str, data: List[str]):
        ...     if not verify_api_key_string(api_key):
        ...         raise ValueError("Invalid API key for batch processing")
        ...     return process_data(data)
    """
    return api_key_auth.verify_api_key(api_key)

def get_auth_status() -> Dict[str, Any]:
    """
    Retrieve comprehensive authentication system status and configuration information.

    Provides operational visibility into authentication system state, configuration,
    and capabilities for monitoring, debugging, and administrative purposes.

    Returns:
        Dict[str, Any]: Authentication system status containing:
                       - auth_config: dict with mode, user tracking, and request logging status
                       - api_keys_configured: int count of configured API keys
                       - development_mode: bool indicating if running without authentication

    Behavior:
        - Returns current authentication configuration from AuthConfig instance
        - Counts configured API keys without exposing key values
        - Determines development mode based on API key configuration
        - Provides snapshot of current system state (not live monitoring)
        - Thread-safe for concurrent access from monitoring endpoints
        - Safe for logging and status endpoints (no sensitive information exposed)

    Examples:
        >>> # System status check
        >>> status = get_auth_status()
        >>> print(f"Mode: {status['auth_config']['mode']}")
        >>> print(f"Keys configured: {status['api_keys_configured']}")

        >>> # Development environment check
        >>> status = get_auth_status()
        >>> if status['development_mode']:
        ...     print("WARNING: Running in development mode without authentication")

        >>> # Monitoring endpoint usage
        >>> @app.get("/internal/auth/status")
        >>> async def auth_status_endpoint():
        ...     return get_auth_status()

        >>> # Expected status structure:
        >>> {
        ...     "auth_config": {
        ...         "mode": "simple",
        ...         "user_tracking": False,
        ...         "request_logging": False
        ...     },
        ...     "api_keys_configured": 3,
        ...     "development_mode": False
        ... }
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
        "user_context": auth_config.supports_user_context,
        "permissions": auth_config.supports_permissions,
        "rate_limiting": auth_config.supports_rate_limiting,
        "user_tracking": auth_config.enable_user_tracking,
        "request_logging": auth_config.enable_request_logging
    }
    return feature_map.get(feature, False)

# ============================================================================
# HTTPException Wrapper Dependencies for FastAPI Compatibility
# ============================================================================

async def verify_api_key_http(
    request: Request,
    bearer_credentials: HTTPAuthorizationCredentials | None = Depends(security),
    settings: "Settings" = Depends(get_settings)
) -> str:
    """
    FastAPI-compatible authentication dependency with HTTP exception handling.

    Provides the same authentication functionality as verify_api_key but converts
    AuthenticationError and ConfigurationError exceptions to HTTPException for proper
    FastAPI middleware compatibility and standardized HTTP error responses.

    Args:
        request: FastAPI Request object containing headers for X-API-Key support
        bearer_credentials: HTTP Bearer authorization credentials from request headers.
                           Expected format: "Bearer sk-1234567890abcdef" or None for missing auth.
                           Automatically injected by FastAPI's HTTPBearer security scheme.
        settings: Settings instance injected via dependency for configuration isolation.

    Returns:
        str: The validated API key string when authentication succeeds.
             Returns "development" when no keys configured in development environments.
             Never returns None - always authenticates or raises HTTPException.

    Raises:
        HTTPException: 401 Unauthorized when authentication fails, containing:
                      - Structured error detail with message and context information
                      - WWW-Authenticate header for proper HTTP authentication flow
                      - Environment detection context for operational debugging
                      - Original exception context preserved for troubleshooting
        HTTPException: 500 Internal Server Error when configuration validation fails

    Behavior:
        - Delegates authentication logic to verify_api_key for consistency
        - Converts AuthenticationError to HTTPException 401 for middleware compatibility
        - Converts ConfigurationError to HTTPException 500 for configuration issues
        - Preserves all authentication context and environment information
        - Returns proper HTTP 401 status with WWW-Authenticate header
        - Provides structured error response format for API clients
        - Maintains compatibility with FastAPI middleware and error handling
        - Prevents "response already started" conflicts in middleware stack
        - Thread-safe for concurrent request processing

    Examples:
        >>> # Recommended FastAPI endpoint authentication
        >>> @app.get("/api/data")
        >>> async def get_data(api_key: str = Depends(verify_api_key_http)):
        ...     return {"data": "protected", "authenticated_key": api_key[:8]}

        >>> # Supports both Bearer token and X-API-Key header:
        >>> # GET /api/data with "Authorization: Bearer sk-1234567890abcdef"
        >>> # GET /api/data with "X-API-Key: sk-1234567890abcdef"

        >>> # HTTP error response for invalid authentication
        >>> # GET /api/data with "Authorization: Bearer invalid-key" or "X-API-Key: invalid-key"
        >>> # Returns: 401 Unauthorized
        >>> # {
        >>> #   "detail": {
        >>> #     "message": "Invalid API key",
        >>> #     "context": {
        >>> #       "auth_method": "bearer_token",
        >>> #       "environment": "development",
        >>> #       "credentials_provided": true
        >>> #     }
        >>> #   }
        >>> # }

        >>> # Success response with valid authentication
        >>> # GET /api/data with "Authorization: Bearer sk-1234567890abcdef"
        >>> # Returns: 200 OK with authenticated content

        >>> # Missing credentials error response
        >>> # GET /api/data without Authorization or X-API-Key headers (keys configured)
        >>> # Returns: 401 Unauthorized with "API key required" message
    """
    try:
        return await verify_api_key(request, bearer_credentials, settings)
    except AuthenticationError as exc:
        # Convert authentication errors to HTTP 401
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"message": str(exc), "context": exc.context},
            headers={"WWW-Authenticate": "Bearer"}
        )
    except ConfigurationError as exc:
        # Convert configuration errors to HTTP 500
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail={"message": str(exc), "context": exc.context}
        )
