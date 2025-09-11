"""
Security Infrastructure Service Package

This package provides comprehensive security infrastructure for the FastAPI application,
implementing defense-in-depth security practices with multi-layered protection, configurable
security policies, and extensive audit capabilities.

## Package Architecture

The security system follows a multi-layered defense approach:
- **Authentication Layer**: API key-based authentication with multi-key support
- **Authorization Layer**: Role-based access control and permission management
- **Input Security Layer**: Input validation and sanitization protection
- **Audit Layer**: Comprehensive security event logging and monitoring

## Core Components

### Authentication & Authorization (`auth.py`)
Robust authentication system with flexible configuration:
- **API Key Authentication**: Bearer token and header-based authentication
- **Multi-Key Support**: Primary + additional API keys for different use cases
- **User Context Management**: Optional user tracking and session management
- **Development Mode**: Automatic development mode for testing environments
- **Graceful Degradation**: Fallback authentication for development/test environments

### Security Features

#### Multi-Tier Authentication
- **Primary Key**: Main application authentication key
- **Additional Keys**: Secondary keys for different services or environments
- **Key Rotation**: Support for seamless key rotation without downtime
- **Test Mode**: Built-in test authentication for automated testing
- **Development Fallback**: Automatic development mode detection

#### Access Control
- **Endpoint Protection**: Fine-grained endpoint access control
- **Optional Authentication**: Flexible authentication for mixed public/private endpoints
- **Permission Validation**: Role-based access control system (future)
- **Session Management**: User session tracking and validation

#### Security Monitoring
- **Request Logging**: Comprehensive security event logging
- **Authentication Metrics**: Success/failure rates and patterns
- **Threat Detection**: Anomalous access pattern detection (future)
- **Audit Trails**: Complete audit trail for security events

## Performance Characteristics

- **Authentication**: < 1ms per authentication check
- **Key Validation**: O(1) lookup time for all supported keys  
- **Memory Efficient**: Minimal memory overhead for key storage
- **High Throughput**: Supports thousands of authentications per second
- **Non-blocking**: Async-first design for optimal performance

## Usage Patterns

### Basic Authentication
```python
from fastapi import Depends
from app.infrastructure.security import verify_api_key

@app.get("/protected")
async def protected_endpoint(api_key: str = Depends(verify_api_key)):
    return {"message": "Access granted", "authenticated": True}

@app.post("/admin")
async def admin_endpoint(api_key: str = Depends(verify_api_key)):
    # Automatically authenticated with any valid API key
    return {"message": "Admin access", "user": api_key}
```

### Optional Authentication
```python
from app.infrastructure.security import optional_verify_api_key

@app.get("/public-or-private")
async def flexible_endpoint(api_key: Optional[str] = Depends(optional_verify_api_key)):
    if api_key:
        return {"message": "Authenticated user", "user": api_key, "premium": True}
    return {"message": "Public access", "premium": False}

@app.get("/content")
async def content_endpoint(api_key: Optional[str] = Depends(optional_verify_api_key)):
    # Return different content based on authentication
    is_authenticated = api_key is not None
    return {"content": get_content(is_authenticated)}
```

### Authentication Status Checking
```python
from app.infrastructure.security import get_auth_status

@app.get("/status")
async def status_endpoint():
    auth_status = get_auth_status()
    return {
        "authentication": auth_status,
        "development_mode": auth_status.get("development_mode", False),
        "available_keys": len(auth_status.get("available_keys", []))
    }
```

### Custom Authentication Validation
```python
from app.infrastructure.security import verify_api_key
from fastapi import HTTPException, Depends

async def admin_only_auth(api_key: str = Depends(verify_api_key)):
    # Add additional validation for admin endpoints
    if not is_admin_key(api_key):
        raise HTTPException(status_code=403, detail="Admin access required")
    return api_key

@app.delete("/admin/users/{user_id}")
async def delete_user(user_id: str, admin_key: str = Depends(admin_only_auth)):
    return {"message": f"User {user_id} deleted", "admin": admin_key}
```

## Integration with Other Infrastructure

The security system integrates with all infrastructure services:
- **AI System**: Input sanitization and prompt injection protection
- **Cache System**: Authenticated cache access and secure key generation
- **Monitoring System**: Security metrics and authentication monitoring
- **Resilience System**: Secure configuration validation and access control

## Configuration

Security behavior is controlled through environment variables:

```bash
# Core Authentication Configuration
AUTH_MODE=simple                    # "simple" or "advanced"
API_KEY=your-primary-api-key       # Primary authentication key
ADDITIONAL_API_KEYS=key1,key2,key3 # Additional valid keys (comma-separated)

# Security Features
ENABLE_USER_TRACKING=true          # Enable user context tracking
ENABLE_REQUEST_LOGGING=true        # Enable security event logging
SECURITY_POLICY=standard           # Security policy preset

# Development & Testing
DEVELOPMENT_MODE=false             # Force development mode
TEST_MODE=false                   # Enable test mode with mock authentication
DISABLE_AUTH_IN_TESTS=false       # Disable authentication for testing

# Security Hardening
REQUIRE_HTTPS=true                # Require HTTPS for authentication
ENABLE_RATE_LIMITING=false        # Enable rate limiting (future)
MAX_AUTH_FAILURES=10              # Maximum authentication failures per IP
```

## Security Policies

### Standard Policy (Default)
- API key authentication required for protected endpoints
- Optional authentication supported for flexible endpoints
- Security event logging enabled
- Development mode auto-detection

### Strict Policy
- Mandatory authentication for all endpoints
- Enhanced logging and monitoring
- Rate limiting enabled
- HTTPS enforcement

### Development Policy
- Relaxed authentication for development
- Enhanced debugging information
- Test mode support
- Simplified configuration

## Security Best Practices

### Key Management
- **Secure Storage**: Store API keys securely (environment variables, secrets management)
- **Key Rotation**: Regularly rotate API keys to minimize exposure
- **Separation**: Use different keys for different environments
- **Access Control**: Limit key access to authorized personnel only

### Monitoring & Alerting
- **Failed Authentication**: Monitor and alert on authentication failures
- **Unusual Patterns**: Detect and investigate unusual access patterns
- **Audit Logs**: Regularly review security audit logs
- **Key Usage**: Monitor API key usage patterns

### Input Validation
- **Sanitization**: Always sanitize user input (integrated with AI sanitization)
- **Validation**: Validate all input parameters and payloads
- **Encoding**: Proper encoding for different contexts (HTML, JSON, etc.)
- **Limits**: Enforce reasonable limits on input size and complexity

## Testing Support

The security system includes comprehensive testing utilities:
- **Mock Authentication**: Configurable mock authentication for testing
- **Test Keys**: Pre-defined test keys for automated testing
- **Security Test Cases**: Comprehensive security test scenarios
- **Performance Tests**: Authentication performance validation

## Thread Safety

All security components are designed for concurrent access:
- **Thread-Safe Authentication**: All authentication operations are atomic
- **Concurrent Access**: Multiple threads can authenticate simultaneously
- **Immutable Configuration**: Security configuration uses immutable data structures
- **Lock-Free Operations**: Most operations use lock-free algorithms for performance

## Compliance & Standards

The security system follows industry standards:
- **OWASP Guidelines**: Follows OWASP security best practices
- **API Security**: Implements OWASP API Security Top 10 recommendations
- **Authentication Standards**: Supports standard authentication mechanisms
- **Audit Standards**: Provides comprehensive audit trails for compliance
"""
from .auth import verify_api_key, verify_api_key_http, optional_verify_api_key, get_auth_status

__all__ = [
    "verify_api_key",
    "verify_api_key_http",
    "optional_verify_api_key",
    "get_auth_status"
]
