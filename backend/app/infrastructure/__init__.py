"""
Security Infrastructure Service

Consolidates and re-exports all business-agnostic security utilities,
including authentication, input sanitization, and response validation.
"""

# Bridge authentication logic.
from ...auth import verify_api_key, optional_verify_api_key, get_auth_status

# Bridge input sanitization logic.
from ...utils.sanitization import sanitize_input, sanitize_options, PromptSanitizer

# Bridge response validation logic.
from ...security.response_validator import validate_ai_response

__all__ = [
    "verify_api_key",
    "optional_verify_api_key",
    "get_auth_status",
    "sanitize_input",
    "sanitize_options",
    "PromptSanitizer",
    "validate_ai_response"
]
