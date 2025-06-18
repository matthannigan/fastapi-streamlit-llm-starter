"""
Domain Services Layer

Re-exports the primary domain services of the application.
During refactoring, this points to the original location.
"""

# Bridge the example domain service from its old location.
from .text_processor import TextProcessorService
from .response_validator import validate_ai_response

__all__ = [
    "TextProcessorService",
    "validate_ai_response"
]
