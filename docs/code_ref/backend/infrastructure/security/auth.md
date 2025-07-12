# Authentication and Authorization Module for FastAPI Applications.

This module provides a comprehensive, extensible authentication system built around
API key authentication with FastAPI. It supports multiple operation modes, from simple
development setups to advanced production configurations with user tracking,
permissions, and request logging.

## Key Features

- **API Key Authentication**: Secure Bearer token authentication using configurable API keys
- **Multiple Operation Modes**: Simple mode for development, advanced mode for production
- **Extensible Architecture**: Built-in extension points for custom authentication logic
- **Development Support**: Automatic development mode when no keys are configured
- **Test Integration**: Built-in test mode support for automated testing
- **User Tracking**: Optional user context and request metadata tracking
- **Flexible Configuration**: Environment-based configuration with runtime reloading

## Architecture

The module is structured around three main components:

1. **AuthConfig**: Manages authentication configuration and feature flags
2. **APIKeyAuth**: Handles API key validation and metadata management
3. **FastAPI Dependencies**: Provides authentication dependencies for route protection

## Operation Modes

- **Simple Mode** (default): Basic API key validation without advanced features
- **Advanced Mode**: Full feature set including user tracking and permissions
- **Development Mode**: Automatic when no API keys configured, allows unauthenticated access
- **Test Mode**: Special handling for automated tests with test keys

## Configuration

The module supports configuration through environment variables:

- `AUTH_MODE`: "simple" (default) or "advanced"
- `ENABLE_USER_TRACKING`: Enable user context tracking ("true"/"false")
- `ENABLE_REQUEST_LOGGING`: Enable request metadata logging ("true"/"false")
- `API_KEY`: Primary API key for authentication
- `ADDITIONAL_API_KEYS`: Comma-separated additional API keys
- `PYTEST_CURRENT_TEST`: Automatically set by pytest for test mode

## Usage Examples

### Basic API key protection

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

### Optional authentication

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

## Extension Points

The module provides several extension points for customization:

- **Key Metadata**: Add custom metadata to API keys via `_key_metadata`
- **Request Context**: Extend `add_request_metadata()` for custom request tracking
- **Authentication Logic**: Override `verify_api_key()` for custom validation
- **Configuration**: Extend `AuthConfig` for additional configuration options

## Security Considerations

- API keys are stored in memory and loaded from environment variables
- Invalid authentication attempts are logged with truncated key information
- Test mode only activates when `PYTEST_CURRENT_TEST` is set
- Development mode warnings are logged when no keys are configured
- Bearer token authentication follows RFC 6750 standard

## Dependencies

- FastAPI: Web framework and security utilities
- Python logging: For authentication event logging
- Environment variables: For configuration management

## Thread Safety

The module is thread-safe for read operations. Key reloading via `reload_keys()`
should be used carefully in multi-threaded environments.

## Performance

- API key verification is O(1) using set-based lookups
- Metadata operations are O(1) dictionary lookups
- Minimal overhead for simple mode operations

## Error Handling

The module raises appropriate HTTP exceptions:
- `401 Unauthorized`: Missing or invalid API key
- Detailed error messages with WWW-Authenticate headers
- Graceful degradation in development mode

Version: 1.0.0
Author: FastAPI LLM Starter Team
License: MIT
