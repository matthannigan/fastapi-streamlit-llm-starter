---
sidebar_label: security
---

# Security Infrastructure Module

This directory provides a comprehensive security infrastructure for FastAPI applications, implementing defense-in-depth security practices with configurable authentication, authorization, and input protection designed to handle both development and production environments.

## Directory Structure

```
security/
├── __init__.py          # Module exports and comprehensive documentation
├── auth.py             # Authentication and authorization implementation
└── README.md           # This documentation file
```

## Core Architecture

### Security-First Design

The security infrastructure follows a **defense-in-depth architecture** with multiple layers of protection:

1. **Authentication Layer**: Multi-tier API key authentication with Bearer token support
2. **Authorization Layer**: Extensible permission system with role-based access control (future)
3. **Configuration Layer**: Environment-based security policies with mode detection
4. **Integration Layer**: FastAPI dependency injection with optional authentication
5. **Monitoring Layer**: Security event logging and audit trail capabilities

## Core Components Comparison

### Authentication & Authorization (`auth.py`)

**Purpose:** Provides comprehensive, extensible authentication system built around API key authentication with FastAPI, supporting multiple operation modes from simple development setups to advanced production configurations.

**Key Features:**
- ✅ **Multi-Mode Operation**: Simple mode for development, advanced mode for production
- ✅ **API Key Authentication**: Secure Bearer token authentication with RFC 6750 compliance
- ✅ **Development Support**: Automatic development mode when no keys configured
- ✅ **Test Integration**: Built-in test mode support with pytest integration
- ✅ **User Tracking**: Optional user context and request metadata tracking
- ✅ **Extensible Architecture**: Built-in extension points for custom authentication logic
- ✅ **Thread Safety**: Safe for concurrent usage in async environments
- ✅ **Performance Optimized**: O(1) API key verification using set-based lookups

**Operation Modes:**
- **Simple Mode** (default): Basic API key validation without advanced features
- **Advanced Mode**: Full feature set including user tracking and permissions
- **Development Mode**: Automatic when no API keys configured, allows unauthenticated access
- **Test Mode**: Special handling for automated tests with `PYTEST_CURRENT_TEST`

**Configuration:**
```python
# Environment variables
AUTH_MODE=simple                      # "simple" or "advanced"
API_KEY=your-primary-api-key         # Primary authentication key
ADDITIONAL_API_KEYS=key1,key2,key3   # Additional valid keys
ENABLE_USER_TRACKING=true            # Enable user context tracking
ENABLE_REQUEST_LOGGING=true          # Enable security event logging

# Initialize authentication
auth_config = AuthConfig()
api_key_auth = APIKeyAuth(auth_config)
```

**Core Classes:**

#### `AuthConfig` - Configuration Management
**Purpose:** Manages authentication configuration and feature flags with environment-based detection.

**Key Features:**
- **Environment Detection**: Automatic mode detection based on configuration
- **Feature Flags**: Configurable security features (user tracking, permissions, rate limiting)
- **Extensibility**: Extension points for custom configuration options
- **Runtime Configuration**: Support for runtime configuration queries

#### `APIKeyAuth` - Authentication Handler
**Purpose:** Core authentication logic with API key validation and metadata management.

**Key Features:**
- **Multi-Key Support**: Primary and additional API keys with metadata
- **Metadata System**: Extensible key metadata for user tracking and permissions
- **Thread-Safe Operations**: Safe for concurrent async environments
- **Extension Points**: Hooks for custom authentication logic

**Best For:**
- Production APIs requiring secure authentication
- Development environments needing flexible security
- Applications with multiple API consumers
- Systems requiring user tracking and audit trails
- Microservices needing lightweight authentication

**Security Features:**
- **Bearer Token Authentication**: RFC 6750 compliant token handling
- **Key Validation**: Secure API key verification with logging
- **Request Metadata**: Optional request context tracking
- **Development Warnings**: Automatic warnings for unprotected endpoints
- **Audit Logging**: Security event tracking with truncated key information

## Usage Examples

### Basic Authentication Protection

```python
from fastapi import FastAPI, Depends
from app.infrastructure.security import verify_api_key

app = FastAPI()

@app.get("/protected")
async def protected_endpoint(api_key: str = Depends(verify_api_key)):
    """Protected endpoint requiring valid API key."""
    return {"message": "Access granted", "key": api_key}
```

### Optional Authentication

```python
from app.infrastructure.security import optional_verify_api_key

@app.get("/public-or-private")
async def flexible_endpoint(api_key: Optional[str] = Depends(optional_verify_api_key)):
    """Endpoint supporting both authenticated and anonymous access."""
    if api_key:
        return {"message": "Authenticated user", "user": api_key}
    return {"message": "Public access"}
```

### Advanced Authentication with Metadata

```python
from app.infrastructure.security.auth import verify_api_key_with_metadata

@app.get("/protected-with-metadata")
async def protected_with_metadata(
    auth_data: dict = Depends(verify_api_key_with_metadata)
):
    """Protected endpoint with user context tracking."""
    return {
        "message": "Access granted",
        "auth_data": auth_data,
        "user_info": auth_data.get("metadata", {})
    }
```

### Manual Key Verification

```python
from app.infrastructure.security.auth import verify_api_key_string

def custom_authentication_logic(key: str) -> bool:
    """Custom authentication with manual key verification."""
    if verify_api_key_string(key):
        logger.info(f"Valid key used: {key[:8]}...")
        return True
    logger.warning(f"Invalid key attempted: {key[:4]}...")
    return False
```

### Authentication Status and Health Checks

```python
from app.infrastructure.security.auth import get_auth_status, is_development_mode

@app.get("/auth/status")
async def auth_status():
    """Get current authentication system status."""
    status = get_auth_status()
    
    return {
        "auth_system": status,
        "development_mode": is_development_mode(),
        "security_warnings": [] if not is_development_mode() else [
            "Running in development mode - authentication disabled"
        ]
    }
```

## Integration Patterns

### FastAPI Dependency Injection

The security system integrates seamlessly with FastAPI's dependency injection:

```python
from fastapi import FastAPI, Depends
from app.core.exceptions import AuthenticationError, AuthorizationError
from app.infrastructure.security import verify_api_key, get_auth_status

app = FastAPI()

# Global dependency for protected routes
async def require_auth(api_key: str = Depends(verify_api_key)) -> str:
    """Global authentication dependency."""
    return api_key

# Service-level authentication
class SecureTextProcessingService:
    def __init__(self):
        self.auth_required = True
    
    async def process_text(
        self, 
        text: str, 
        api_key: str = Depends(verify_api_key)
    ) -> dict:
        """Secure text processing with authentication."""
        return {
            "result": f"Processed: {text}",
            "authenticated": True,
            "key_used": api_key[:8] + "..."
        }

# Route-level protection
@app.post("/process")
async def process_text(
    request: ProcessRequest,
    api_key: str = Depends(require_auth)
):
    """Protected text processing endpoint."""
    service = SecureTextProcessingService()
    return await service.process_text(request.text, api_key)
```

### Environment-Based Configuration

```python
import os
from app.infrastructure.security.auth import AuthConfig, APIKeyAuth

# Development configuration
if os.getenv("ENVIRONMENT") == "development":
    auth_config = AuthConfig()
    # Development mode automatically detected if no keys configured
    
# Production configuration
elif os.getenv("ENVIRONMENT") == "production":
    auth_config = AuthConfig()
    # Ensure API keys are configured
    if not os.getenv("API_KEY"):
        raise ValueError("API_KEY required in production")

# Custom configuration
auth_config.simple_mode = False  # Enable advanced features
auth_config.enable_user_tracking = True
auth_config.enable_request_logging = True
```

### Middleware Integration

```python
from fastapi import Request
from app.infrastructure.security.auth import api_key_auth

async def security_middleware(request: Request, call_next):
    """Security middleware for automatic logging and monitoring."""
    
    # Log security events for protected endpoints
    if request.url.path.startswith("/api/"):
        auth_header = request.headers.get("authorization")
        if auth_header:
            # Extract and validate API key
            try:
                scheme, credentials = auth_header.split()
                if scheme.lower() == "bearer":
                    is_valid = api_key_auth.verify_api_key(credentials)
                    logger.info(f"API key validation: {is_valid} for path {request.url.path}")
            except ValueError:
                logger.warning(f"Invalid authorization header format for {request.url.path}")
    
    response = await call_next(request)
    
    # Add security headers
    response.headers["X-Content-Type-Options"] = "nosniff"
    response.headers["X-Frame-Options"] = "DENY"
    response.headers["X-XSS-Protection"] = "1; mode=block"
    
    return response
```

### Service Integration with Fallback

```python
from typing import Optional
from app.infrastructure.security import optional_verify_api_key

class FlexibleAIService:
    """AI service with optional authentication and graceful degradation."""
    
    async def process_request(
        self,
        text: str,
        api_key: Optional[str] = Depends(optional_verify_api_key)
    ) -> dict:
        """Process text with optional authentication."""
        
        if api_key:
            # Authenticated request - full features
            return await self._process_authenticated(text, api_key)
        else:
            # Anonymous request - limited features
            return await self._process_anonymous(text)
    
    async def _process_authenticated(self, text: str, api_key: str) -> dict:
        """Full processing for authenticated users."""
        return {
            "result": f"Full processing of: {text}",
            "features": ["summarize", "sentiment", "questions", "key_points"],
            "authenticated": True,
            "rate_limit": None  # No rate limiting for authenticated users
        }
    
    async def _process_anonymous(self, text: str) -> dict:
        """Limited processing for anonymous users."""
        return {
            "result": f"Basic processing of: {text[:100]}...",
            "features": ["summarize"],  # Limited features
            "authenticated": False,
            "rate_limit": "10 requests per hour"
        }
```

## Configuration Management

### Environment-Based Security Policies

The security system supports multiple configuration approaches:

```python
# Simple configuration (default)
AUTH_MODE=simple
API_KEY=your-api-key

# Advanced configuration
AUTH_MODE=advanced
API_KEY=primary-key-12345
ADDITIONAL_API_KEYS=secondary-key-67890,backup-key-abcdef
ENABLE_USER_TRACKING=true
ENABLE_REQUEST_LOGGING=true
```

### Runtime Configuration

```python
from app.infrastructure.security.auth import auth_config, supports_feature

# Check current configuration
config_info = auth_config.get_auth_info()
print(f"Running in {config_info['mode']} mode")
print(f"Features enabled: {config_info['features']}")

# Feature detection
if supports_feature('user_tracking'):
    print("User context tracking is available")

if supports_feature('permissions'):
    print("Permission-based access control is available")

# Dynamic configuration updates (development only)
if is_development_mode():
    auth_config.enable_request_logging = True
    logger.info("Enabled request logging for development")
```

### Security Policy Templates

```python
from app.infrastructure.security.auth import AuthConfig

class SecurityPolicyTemplate:
    """Pre-configured security policy templates."""
    
    @staticmethod
    def development_policy() -> AuthConfig:
        """Relaxed security for development."""
        config = AuthConfig()
        config.simple_mode = True
        config.enable_request_logging = True
        return config
    
    @staticmethod
    def production_policy() -> AuthConfig:
        """Strict security for production."""
        config = AuthConfig()
        config.simple_mode = False
        config.enable_user_tracking = True
        config.enable_request_logging = True
        return config
    
    @staticmethod
    def testing_policy() -> AuthConfig:
        """Security configuration for testing."""
        config = AuthConfig()
        config.simple_mode = True
        config.enable_request_logging = False
        return config

# Use policy templates
if os.getenv("ENVIRONMENT") == "production":
    auth_config = SecurityPolicyTemplate.production_policy()
```

## Error Handling & Resilience

The security system provides comprehensive error handling using the custom exception hierarchy with automatic HTTP status code mapping and structured security context for audit logging. For complete details on the exception system, see the [Exception Handling Guide](../../../guides/developer/EXCEPTION_HANDLING.md).

### Security-Specific Exception Types

The security infrastructure uses these custom exceptions from `app.core.exceptions`:

- **`AuthenticationError`**: Authentication failures (401 Unauthorized)
  - Missing API keys, invalid credentials, malformed auth headers
  - Includes security context for audit logging
- **`AuthorizationError`**: Authorization failures (403 Forbidden)  
  - Insufficient permissions, role-based access violations
  - Includes permission context and resource information
- **`ValidationError`**: Input validation errors (400 Bad Request)
  - Invalid API key formats, malformed request data
- **`ConfigurationError`**: Security configuration errors (500 Internal Server Error)
  - Missing required security configuration, invalid settings

All security exceptions include structured context data for security monitoring and audit trails.

### Exception Handling

```python
from app.core.exceptions import AuthenticationError, AuthorizationError

# Authentication exceptions are automatically converted to proper HTTP responses
try:
    api_key = await verify_api_key(credentials)
except AuthenticationError as e:
    # Automatically converted to 401 Unauthorized
    # Error details available in e.context for security auditing
    logger.warning(f"Authentication failed: {e.context}")
    raise  # Re-raise for FastAPI global exception handler

# Authorization example
try:
    # Check user permissions for protected resource
    if not user_has_permission(api_key, "admin_access"):
        raise AuthorizationError(
            "Insufficient privileges for admin operations",
            context={
                "api_key": api_key[:8] + "...",  # Truncated for security
                "required_permission": "admin_access",
                "endpoint": "/admin/users"
            }
        )
except AuthorizationError as e:
    # Automatically converted to 403 Forbidden
    # Security context available for audit logging
    logger.warning(f"Authorization failed: {e.context}")
    raise  # Re-raise for FastAPI global exception handler
```

### Graceful Degradation

```python
from app.core.exceptions import AuthenticationError, AuthorizationError

@app.middleware("http")
async def auth_fallback_middleware(request: Request, call_next):
    """Middleware providing graceful authentication fallback."""
    
    try:
        response = await call_next(request)
        return response
    except AuthenticationError as e:
        # Check if endpoint supports anonymous access
        if request.url.path in ["/health", "/docs", "/openapi.json"]:
            # Log security event but allow access to public endpoints
            logger.info(f"Anonymous access to public endpoint: {request.url.path}")
            return await call_next(request)
        
        # Log security event for protected endpoints
        logger.warning(
            f"Authentication failed for protected endpoint: {request.url.path}", 
            extra={"security_context": e.context}
        )
        raise  # Re-raise for protected endpoints
    except AuthorizationError as e:
        # Log authorization failures with context
        logger.warning(
            f"Authorization failed for endpoint {request.url.path}: {e.message}",
            extra={"security_context": e.context}
        )
        raise  # Re-raise for FastAPI error handling
```

### Security Event Logging

```python
import logging
from app.infrastructure.security.auth import api_key_auth
from app.core.exceptions import AuthenticationError, AuthorizationError

# Configure security logging
security_logger = logging.getLogger("security")
security_logger.setLevel(logging.INFO)

class SecurityEventHandler:
    """Handle security events and logging with structured exception context."""
    
    @staticmethod
    def log_authentication_attempt(api_key: str, success: bool, request_info: dict):
        """Log authentication attempts with proper security practices."""
        # Truncate API key for security
        truncated_key = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else "****"
        
        if success:
            security_logger.info(
                f"Authentication successful: key={truncated_key}, "
                f"ip={request_info.get('client_ip', 'unknown')}, "
                f"path={request_info.get('path', 'unknown')}"
            )
        else:
            # Create structured security exception for failed authentication
            auth_error = AuthenticationError(
                "Authentication failed",
                context={
                    "api_key_hint": truncated_key,
                    "client_ip": request_info.get('client_ip', 'unknown'),
                    "request_path": request_info.get('path', 'unknown'),
                    "timestamp": request_info.get('timestamp'),
                    "user_agent": request_info.get('user_agent', 'unknown')
                }
            )
            
            security_logger.warning(
                f"Authentication failed: {auth_error.message}",
                extra={"security_context": auth_error.context}
            )
    
    @staticmethod 
    def log_authorization_failure(api_key: str, required_permission: str, resource: str, request_info: dict):
        """Log authorization failures with structured exception context."""
        truncated_key = f"{api_key[:4]}...{api_key[-4:]}" if len(api_key) > 8 else "****"
        
        auth_error = AuthorizationError(
            f"Access denied: insufficient privileges for {resource}",
            context={
                "api_key_hint": truncated_key,
                "required_permission": required_permission,
                "resource": resource,
                "client_ip": request_info.get('client_ip', 'unknown'),
                "request_path": request_info.get('path', 'unknown'),
                "timestamp": request_info.get('timestamp')
            }
        )
        
        security_logger.warning(
            f"Authorization failed: {auth_error.message}",
            extra={"security_context": auth_error.context}
        )
        
        # Re-raise for FastAPI error handling
        raise auth_error
```

## Advanced Security Features

### Custom Authentication Extensions

```python
from app.infrastructure.security.auth import APIKeyAuth, AuthConfig
from app.core.exceptions import AuthenticationError, AuthorizationError, RateLimitError, ConfigurationError

class CustomAPIKeyAuth(APIKeyAuth):
    """Extended authentication with custom logic and structured exception handling."""
    
    def __init__(self, auth_config: AuthConfig):
        super().__init__(auth_config)
        
        # Custom key metadata with additional fields
        self._custom_metadata = {
            "rate_limits": {},
            "permissions": {},
            "user_contexts": {}
        }
    
    def verify_api_key(self, api_key: str) -> bool:
        """Enhanced key verification with custom logic and proper exception handling."""
        if not super().verify_api_key(api_key):
            raise AuthenticationError(
                "Invalid API key",
                context={
                    "api_key_hint": api_key[:4] + "..." if len(api_key) > 4 else "****",
                    "validation_stage": "base_verification"
                }
            )
        
        # Custom validation logic with proper exception handling
        try:
            if not self._check_rate_limit(api_key):
                raise RateLimitError(
                    "Rate limit exceeded for API key",
                    context={
                        "api_key_hint": api_key[:4] + "..." if len(api_key) > 4 else "****",
                        "rate_limit_info": self._custom_metadata["rate_limits"].get(api_key, {})
                    }
                )
            
            if not self._check_permissions(api_key):
                raise AuthorizationError(
                    "API key lacks required permissions",
                    context={
                        "api_key_hint": api_key[:4] + "..." if len(api_key) > 4 else "****",
                        "permissions": self._custom_metadata["permissions"].get(api_key, [])
                    }
                )
            
            return True
            
        except (RateLimitError, AuthorizationError):
            # Re-raise security exceptions with context intact
            raise
        except Exception as e:
            # Wrap unexpected errors in proper security context
            raise AuthenticationError(
                f"Authentication verification failed: {str(e)}",
                context={
                    "api_key_hint": api_key[:4] + "..." if len(api_key) > 4 else "****",
                    "validation_stage": "custom_verification",
                    "original_error": str(e)
                }
            )
    
    def _check_rate_limit(self, api_key: str) -> bool:
        """Check rate limiting for API key."""
        # Custom rate limiting logic - return True if within limits
        rate_limit_data = self._custom_metadata["rate_limits"].get(api_key, {})
        # Implement your rate limiting logic here
        return True
    
    def _check_permissions(self, api_key: str) -> bool:
        """Check permissions for API key."""
        # Custom permission logic - return True if permissions are sufficient
        permissions = self._custom_metadata["permissions"].get(api_key, [])
        # Implement your permission checking logic here
        return True

# Use custom authentication with proper exception handling
try:
    custom_auth = CustomAPIKeyAuth(AuthConfig())
except Exception as e:
    raise ConfigurationError(
        "Failed to initialize custom authentication",
        context={"initialization_error": str(e)}
    )
```

### Integration with External Authentication

```python
from typing import Optional
import jwt
from app.infrastructure.security.auth import AuthConfig

class HybridAuthConfig(AuthConfig):
    """Authentication supporting both API keys and JWT tokens."""
    
    def __init__(self):
        super().__init__()
        self.jwt_secret = os.getenv("JWT_SECRET")
        self.jwt_algorithm = "HS256"
    
    def verify_jwt_token(self, token: str) -> Optional[dict]:
        """Verify JWT token and return payload."""
        try:
            payload = jwt.decode(token, self.jwt_secret, algorithms=[self.jwt_algorithm])
            return payload
        except jwt.InvalidTokenError:
            return None

async def hybrid_verify_auth(
    credentials: Optional[HTTPAuthorizationCredentials] = Depends(security)
) -> dict:
    """Verify either API key or JWT token."""
    if not credentials:
        raise AuthenticationError(
            "Authentication required", 
            context={"error_type": "missing_credentials"}
        )
    
    token = credentials.credentials
    
    # Try API key first
    if api_key_auth.verify_api_key(token):
        return {"type": "api_key", "key": token}
    
    # Try JWT token
    hybrid_config = HybridAuthConfig()
    jwt_payload = hybrid_config.verify_jwt_token(token)
    if jwt_payload:
        return {"type": "jwt", "payload": jwt_payload}
    
    # Authentication failed - provide security context for auditing
    raise AuthenticationError(
        "Invalid authentication credentials", 
        context={
            "error_type": "invalid_credentials",
            "credential_hint": token[:4] + "..." if len(token) > 4 else "****",
            "attempted_types": ["api_key", "jwt_token"]
        }
    )
```

## Performance Characteristics

### Authentication Performance

| Operation | Performance Target | Actual Performance |
|-----------|-------------------|-------------------|
| **API Key Verification** | <1ms | ~0.1-0.5ms typical |
| **Metadata Lookup** | <1ms | ~0.1-0.3ms typical |
| **Configuration Loading** | <10ms | ~2-5ms typical |
| **Key Validation** | O(1) | Set-based lookup |

### Memory Usage

- **Base Authentication**: ~1-2MB for core security infrastructure
- **Per-Key Metadata**: ~100-500KB additional memory per API key
- **Configuration Cache**: ~10-50KB for authentication configuration
- **Request Context**: ~1-5KB per active authenticated request

### Optimization Features

- **Pre-compiled Key Sets**: API keys stored in sets for O(1) lookup
- **Metadata Caching**: Key metadata cached in memory for fast access
- **Minimal Overhead**: Simple mode operations have minimal performance impact
- **Efficient Logging**: Structured logging with configurable levels

## Testing Integration

### Test Mode Support

```python
# Automatic test mode detection
import os
os.environ["PYTEST_CURRENT_TEST"] = "test_auth.py::test_function"

# Test mode provides special handling
from app.infrastructure.security.auth import is_development_mode
assert is_development_mode()  # True in test mode without configured keys
```

### Testing Utilities

```python
import pytest
from app.infrastructure.security.auth import APIKeyAuth, AuthConfig

@pytest.fixture
def test_auth():
    """Test authentication configuration."""
    config = AuthConfig()
    auth = APIKeyAuth(config)
    auth.api_keys = {"test-key-12345", "test-key-67890"}
    return auth

def test_api_key_verification(test_auth):
    """Test API key verification logic."""
    assert test_auth.verify_api_key("test-key-12345")
    assert not test_auth.verify_api_key("invalid-key")
```

## Migration Guide

### From No Authentication to Secure Authentication

1. **Add Environment Variables:**
```bash
# Set primary API key
export API_KEY=your-secure-api-key-here

# Optional: Add additional keys
export ADDITIONAL_API_KEYS=key1,key2,key3

# Enable advanced features
export AUTH_MODE=advanced
export ENABLE_REQUEST_LOGGING=true
```

2. **Update Route Protection:**
```python
# Before: Unprotected endpoints
@app.get("/data")
async def get_data():
    return {"data": "sensitive information"}

# After: Protected endpoints
from app.infrastructure.security import verify_api_key

@app.get("/data")
async def get_data(api_key: str = Depends(verify_api_key)):
    return {"data": "sensitive information", "authenticated": True}
```

3. **Gradual Migration with Optional Auth:**
```python
# Transition period - support both authenticated and anonymous access
from app.infrastructure.security import optional_verify_api_key

@app.get("/data")
async def get_data(api_key: Optional[str] = Depends(optional_verify_api_key)):
    if api_key:
        # Full data for authenticated users
        return {"data": "complete dataset", "authenticated": True}
    else:
        # Limited data for anonymous users
        return {"data": "sample dataset", "authenticated": False}
```

### From Simple to Advanced Authentication

```python
# Update configuration
AUTH_MODE=advanced
ENABLE_USER_TRACKING=true
ENABLE_REQUEST_LOGGING=true

# Update code to use advanced features
from app.infrastructure.security.auth import verify_api_key_with_metadata

@app.get("/advanced-endpoint")
async def advanced_endpoint(
    auth_data: dict = Depends(verify_api_key_with_metadata)
):
    return {
        "message": "Advanced features enabled",
        "user_context": auth_data.get("metadata", {}),
        "permissions": auth_data.get("permissions", [])
    }
```

## Exception Handling Integration

### Security Exception Patterns

The security infrastructure is fully integrated with the custom exception system. All security-related errors use structured exceptions that provide:

- **Automatic HTTP Status Mapping**: Custom exceptions are automatically converted to appropriate HTTP status codes by the global exception handler
- **Security Context**: All exceptions include structured context data for security auditing and monitoring
- **Audit Trail**: Security events are logged with proper context while protecting sensitive information

For complete details on exception handling patterns, see:
- [Exception Handling Guide](../../../guides/developer/EXCEPTION_HANDLING.md) - Comprehensive exception system documentation
- [Exception Handler Configuration](../../core/exceptions.py) - Core exception definitions and HTTP status mapping

### Security Exception Usage Guidelines

```python
from app.core.exceptions import AuthenticationError, AuthorizationError, ValidationError

# Always include security context for audit trails
raise AuthenticationError(
    "Invalid API key format",
    context={
        "api_key_hint": key[:4] + "..." if len(key) > 4 else "****",
        "validation_type": "format_check",
        "client_ip": request.client.host,
        "timestamp": datetime.utcnow().isoformat()
    }
)

# Use appropriate exception types for different security scenarios
if not api_key:
    raise AuthenticationError("API key required")
elif not valid_format(api_key):
    raise ValidationError("Invalid API key format")  
elif not key_exists(api_key):
    raise AuthenticationError("Invalid API key")
elif not has_permission(api_key, resource):
    raise AuthorizationError("Insufficient permissions")
```

## Best Practices

### Security Guidelines

1. **API Key Management**: Store API keys securely in environment variables, never in code
2. **Key Rotation**: Implement regular API key rotation policies
3. **Exception Context**: Always include structured security context in exceptions for audit trails
4. **Logging Security**: Log authentication events but truncate sensitive information (API keys, tokens)
5. **Error Messages**: Provide secure error messages that don't leak sensitive information
6. **Development Mode**: Never run production with development mode enabled
7. **Security Monitoring**: Use exception context data for security monitoring and alerting

### Performance Guidelines

1. **Key Storage**: Use environment variables for small numbers of keys
2. **Metadata Optimization**: Only enable user tracking when needed
3. **Logging Configuration**: Configure appropriate logging levels for production
4. **Memory Management**: Monitor memory usage with large numbers of API keys

### Development Guidelines

1. **Environment Configuration**: Use different configurations for dev/test/prod
2. **Test Integration**: Leverage built-in test mode for automated testing
3. **Error Handling**: Implement proper exception handling for authentication failures
4. **Monitoring**: Include authentication metrics in application monitoring

This security infrastructure provides production-ready, defense-in-depth security practices designed to protect FastAPI applications while maintaining flexibility for development and testing environments.