"""
"""

from fastapi import APIRouter, Depends
import logging

from app.infrastructure.security import verify_api_key

# Create a router for auth endpoints
auth_router = APIRouter(prefix="/auth", tags=["auth"])

logger = logging.getLogger(__name__)


@auth_router.get("/status")
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
        HTTPException: Authentication failures raise HTTP exceptions:
            - 401 Unauthorized: No API key provided in request headers
            - 401 Unauthorized: Invalid or malformed API key provided
            - 401 Unauthorized: API key format is incorrect or unrecognized
    
    Example:
        >>> # GET /auth/status
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

