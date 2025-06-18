"""
REFACTOR: This module was moved into backend/app/infrastructure/ai/prompt_builder.py

Utility functions for prompt processing and user input handling.

This module provides functions for safely handling user input before embedding
it into prompt templates to prevent injection attacks and formatting issues.
"""

import html
from typing import Optional


def escape_user_input(user_input: str) -> str:
    """
    Escape user input to make it safe for embedding in prompt templates.
    
    This function uses HTML escaping as the primary mechanism to prevent
    special characters from breaking template structure or being misinterpreted
    by the LLM.
    
    Args:
        user_input (str): The raw user input string to escape.
        
    Returns:
        str: The escaped string safe for use in prompt templates.
        
    Examples:
        >>> escape_user_input("Hello <script>alert('xss')</script>")
        "Hello &lt;script&gt;alert(&#x27;xss&#x27;)&lt;/script&gt;"
        
        >>> escape_user_input("Tom & Jerry's adventure")
        "Tom &amp; Jerry&#x27;s adventure"
        
        >>> escape_user_input("")
        ""
    """
    if not isinstance(user_input, str):
        raise TypeError(f"user_input must be a string, got {type(user_input)}")
    
    return html.escape(user_input) 