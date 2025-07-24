"""
Core Application Imports

This file re-exports the application's central configuration object and
custom exception base classes, making them easily accessible from a single,
stable import path.

Example:
    from .core import settings
    from .core import ApplicationError (once moved)
"""

# This allows other modules to import settings directly from the core package
from .config import settings, Settings

# Re-export custom exceptions for easy access
from .exceptions import (
    # Base exceptions
    ApplicationError,
    ValidationError,
    AuthenticationError,
    AuthorizationError,
    ConfigurationError,
    BusinessLogicError,
    InfrastructureError,
    
    # AI service exceptions
    AIServiceException,
    TransientAIError,
    PermanentAIError,
    RateLimitError,
    ServiceUnavailableError,
    
    # Utility functions
    classify_ai_exception,
    get_http_status_for_exception,
)
