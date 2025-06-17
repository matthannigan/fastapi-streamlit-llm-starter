"""
AI Infrastructure Service

Re-exports the primary utilities for interacting with AI models,
such as the safe prompt builder.
"""

# Bridge from the old 'services' directory to the new infrastructure path.
from ...services.prompt_builder import create_safe_prompt, get_available_templates

__all__ = ["create_safe_prompt", "get_available_templates"]
