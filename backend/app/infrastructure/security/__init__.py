"""
Security Infrastructure Service

Consolidates and re-exports all business-agnostic security utilities,
including authentication, input sanitization, and response validation.
"""
from .auth import verify_api_key, optional_verify_api_key, get_auth_status

__all__ = [
    "verify_api_key",
    "optional_verify_api_key",
    "get_auth_status"
]
