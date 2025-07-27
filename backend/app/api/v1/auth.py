"""Domain Service: Authentication Status API

📚 **EXAMPLE IMPLEMENTATION** - Replace in your project  
💡 **Demonstrates infrastructure usage patterns**  
🔄 **Expected to be modified/replaced**

This module provides REST API endpoints for authentication validation and status
checking. It demonstrates how to build secure API endpoints using the infrastructure
authentication services and serves as an example for implementing authentication
workflows in domain services.

## Core Components

### API Endpoints
- `GET /v1/auth/status`: Verify authentication status and return API key validation information

### Security Model
- **Required Authentication**: All endpoints require valid API key authentication
- **API Key Validation**: Demonstrates proper use of infrastructure security services
- **Response Security**: Safely truncates sensitive information in responses

## Dependencies & Integration

### Infrastructure Dependencies
- `app.infrastructure.security.verify_api_key`: Infrastructure authentication service
- `app.schemas.ErrorResponse`: Structured error response model

### FastAPI Dependencies
- `verify_api_key()`: Required authentication dependency injection

## Usage Examples

### Authentication Status Check
```bash
# With Authorization header
curl -H "Authorization: Bearer your-api-key" /v1/auth/status

# With X-API-Key header  
curl -H "X-API-Key: your-api-key" /v1/auth/status
```

### Response Format
```json
{
    "authenticated": true,
    "api_key_prefix": "abcd1234...",
    "message": "Authentication successful"
}
```

## Implementation Notes

This service demonstrates domain-level authentication endpoints that:
- Validate API keys using infrastructure services
- Provide secure confirmation without exposing sensitive data
- Follow proper error handling patterns with structured responses
- Support multiple authentication methods (Bearer token, X-API-Key header)

**Replace in your project** - This is an example showing authentication patterns.
Customize the authentication logic and responses based on your application needs.
"""

from fastapi import APIRouter, Depends
import logging

from app.infrastructure.security import verify_api_key
from app.schemas import ErrorResponse

# Create a router for auth endpoints
auth_router = APIRouter(prefix="/auth", tags=["Authentication"])

logger = logging.getLogger(__name__)


@auth_router.get("/status",
                 responses={
                     401: {"model": ErrorResponse, "description": "Authentication Error"},
                 })
async def auth_status(api_key: str = Depends(verify_api_key)):
    """Verify authentication status and return API key validation information.
    
    This endpoint validates the provided API key and returns authentication status
    information. It serves as a secure health check for authentication systems and
    provides a safe method to validate API keys without exposing sensitive data.
    
    The endpoint requires a valid API key provided through the standard authentication
    mechanism (Authorization header with "Bearer <token>" format or X-API-Key header).
    Upon successful authentication, it returns confirmation details with a safely
    truncated version of the API key for verification purposes.
    
    Args:
        api_key (str): The validated API key obtained through the verify_api_key
            dependency. This parameter is automatically injected by FastAPI's
            dependency injection system after successful authentication validation.
    
    Returns:
        dict: Authentication status information containing:
            - authenticated (bool): Always True when the request reaches this endpoint,
              confirming successful authentication
            - api_key_prefix (str): Safely truncated API key showing only the first
              8 characters followed by "..." for security verification purposes.
              Keys with 8 characters or fewer display the complete key
            - message (str): Human-readable confirmation message indicating successful
              authentication
    
    Raises:
        AuthenticationError: Authentication failures raise authentication errors:
            - Missing API key: No API key provided in request headers
            - Invalid API key: API key is malformed or unrecognized
            - Authentication failure: API key format is incorrect
    
    Example:
        >>> # GET /v1/auth/status
        >>> # Headers: Authorization: Bearer your-api-key-here
        >>> {
        ...   "authenticated": true,
        ...   "api_key_prefix": "abcd1234...",
        ...   "message": "Authentication successful"
        ... }
    
    Note:
        This endpoint is designed for:
        - API key validation in client applications and SDKs
        - Authentication system health monitoring and diagnostics
        - Debugging authentication configuration issues
        - Integration testing of authentication workflows
        - Verifying API key rotation and management processes
    """
    return {
        "authenticated": True,
        "api_key_prefix": api_key[:8] + "..." if len(api_key) > 8 else api_key,
        "message": "Authentication successful"
    }

