"""
Domain Services Layer

Re-exports the primary domain services of the application.
"""

# Bridge the example domain service from its old location.
from .text_processor import TextProcessorService
from .response_validator import ResponseValidator

__all__ = [
    "TextProcessorService",
    "ResponseValidator"
]
