import re
import html
import os
from typing import Any, Dict, List, Pattern

# Read max length from environment variable with appropriate fallbacks
_DEFAULT_MAX_LENGTH = int(os.getenv('INPUT_MAX_LENGTH', '2048'))
_LEGACY_MAX_LENGTH = 1024  # Legacy functions maintain backward compatibility with original 1024 default

class PromptSanitizer:
    """
    Advanced prompt sanitizer class for detecting and preventing prompt injection attacks.
    
    This class implements a comprehensive set of regex patterns to identify potentially
    malicious prompts that attempt to manipulate AI systems through instruction injection,
    system prompt revelation, or other attack vectors.
    """
    
    def __init__(self) -> None:
        """
        Initialize the PromptSanitizer with pre-compiled regex patterns.
        
        Sets up forbidden_patterns as raw regex strings and compiled_patterns
        as pre-compiled regex objects with case-insensitive matching for
        efficient pattern detection.
        """
        # Define raw regex patterns for prompt injection detection
        self.forbidden_patterns: List[str] = [
            r"ignore\s+(all\s+)?previous\s+instructions",
            r"new\s+instruction",
            r"system\s+prompt",
            r"reveal\s+.*?(password|key|secret|api_key|token)",
            r"forget\s+(all\s+)?previous\s+(instructions|context)",
            r"forget\s+(everything|all)",
            r"override\s+(previous\s+)?(instructions|settings)",
            r"act\s+as\s+(if\s+)?(you\s+are\s+)?a\s+(different|new)",
            r"you\s+are\s+now\s+a?\s*\w*",  # More flexible pattern for "you are now a/an [anything]"
            r"pretend\s+(to\s+be|you\s+are|you\s+can)",
            r"roleplay\s+as",
            r"simulate\s+(being\s+)?a",
            r"execute\s+(this\s+)?(command|code|script)",
            r"run\s+(this\s+)?(command|code|script)",
            r"run\s+any\s+command",
            r"sudo\s+",
            r"admin\s+mode",
            r"developer\s+mode",
            r"debug\s+mode",
            r"maintenance\s+mode",
            r"bypass\s+(security|filter|restriction)",
            r"bypass\s+all\s+security",
            r"disable\s+(security|filter|safety)",
            r"jailbreak",
            r"escape\s+(sequence|mode)",
            r"break\s+out\s+of",
            r"exit\s+(sandbox|containment)",
            r"act\s+outside\s+your\s+normal",
            r"reveal\s+confidential",
            r"\\n\\n\\*",
            r"\\r\\n",
            r"\\x[0-9a-fA-F]{2}",
            r"\\u[0-9a-fA-F]{4}",
            r"base64:",
            r"eval\s*\(",
            r"exec\s*\(",
            r"import\s+(os|sys|subprocess)",
            r"from\s+(os|sys|subprocess)",
            r"__import__",
            r"\$\{.*\}",
            r"javascript:",
            r"data:text/html",
            r"<script",
            r"</script>",
            r"<iframe",
            r"onload\s*=",
            r"onerror\s*=",
            r"alert\s*\(",
            r"console\.log\s*\(",
            r"fetch\s*\(",
            r"XMLHttpRequest",
            r"document\.cookie",
            r"window\.location",
        ]
        
        # Pre-compile patterns for efficiency with case-insensitive matching
        self.compiled_patterns: List[Pattern[str]] = [
            re.compile(pattern, re.IGNORECASE) for pattern in self.forbidden_patterns
        ]
    
    def sanitize_input(self, user_input: str, max_length: int | None = None) -> str:
        """
        Sanitize user input by detecting and removing prompt injection patterns.
        
        This method performs comprehensive sanitization including:
        1. Removal of forbidden patterns (prompt injection attempts)
        2. Basic character removal for potentially dangerous characters
        3. HTML/XML character escaping
        4. Whitespace normalization
        5. Input length truncation
        
        Args:
            user_input: The raw user input string to sanitize
            max_length: Maximum allowed length for the input (default: from INPUT_MAX_LENGTH env var or 2048)
            
        Returns:
            Sanitized string with malicious patterns removed and characters escaped
        """
        if not isinstance(user_input, str):
            return ""
        
        # Use environment variable default if max_length not provided
        if max_length is None:
            max_length = _DEFAULT_MAX_LENGTH
        
        # Initialize cleaned text
        cleaned_text = user_input
        
        # Step 1: Remove forbidden patterns using compiled regex patterns
        for pattern in self.compiled_patterns:
            cleaned_text = pattern.sub("", cleaned_text)
        
        # Step 2: Apply basic character removal for potentially dangerous characters
        # Remove specific characters that could be used for injection attacks
        cleaned_text = re.sub(r'[<>{}\[\];|`\'"]', '', cleaned_text)
        
        # Step 3: Escape HTML/XML special characters
        cleaned_text = html.escape(cleaned_text)
        
        # Step 4: Normalize whitespace (multiple spaces -> single space, trim)
        cleaned_text = ' '.join(cleaned_text.split())
        
        # Step 5: Truncate to maximum length if necessary
        if len(cleaned_text) > max_length:
            cleaned_text = cleaned_text[:max_length]
        
        return cleaned_text

# Global sanitizer instance for backward compatibility
_global_sanitizer = PromptSanitizer()

def sanitize_input(text: str, max_length: int | None = None) -> str:
    """
    Legacy-compatible sanitize function that provides basic character filtering.
    
    This function maintains backward compatibility with the original implementation
    while providing minimal security benefits. It performs basic character removal
    without aggressive pattern detection to preserve existing behavior.
    
    For new code, consider using PromptSanitizer directly for enhanced security.
    
    Args:
        text: The input text to sanitize
        max_length: Maximum allowed length for the input (default: 1024 for legacy compatibility)
        
    Returns:
        Sanitized string with basic character filtering applied
    """
    if not isinstance(text, str):
        return ""
    
    # Use legacy default if max_length not provided to maintain backward compatibility
    if max_length is None:
        max_length = _LEGACY_MAX_LENGTH
    
    # Apply basic character removal only - matching original behavior
    # Remove only: < > { } [ ] ; | ` ' "
    cleaned_text = re.sub(r'[<>{}\[\];|`\'"]', '', text)
    
    # Truncate to maximum length if necessary (original default was 1024)
    if len(cleaned_text) > max_length:
        cleaned_text = cleaned_text[:max_length]
    
    return cleaned_text

def sanitize_input_advanced(text: str, max_length: int | None = None) -> str:
    """
    Advanced sanitize function using the full PromptSanitizer capabilities.
    
    This function provides comprehensive protection against prompt injection attacks
    and should be used for new implementations requiring enhanced security.
    
    Args:
        text: The input text to sanitize
        max_length: Maximum allowed length for the input (default: from INPUT_MAX_LENGTH env var or 2048)
        
    Returns:
        Sanitized string with comprehensive security filtering applied
    """
    if max_length is None:
        max_length = _DEFAULT_MAX_LENGTH
    return _global_sanitizer.sanitize_input(text, max_length)

def sanitize_options(options: Dict[str, Any]) -> Dict[str, Any]:
    """
    Sanitizes options dictionary using basic character filtering for backward compatibility.
    
    Args:
        options: Dictionary of options to sanitize
        
    Returns:
        Dictionary with string values sanitized using basic filtering
    """
    if not isinstance(options, dict):
        return {}

    sanitized_options: Dict[str, Any] = {}
    for key, value in options.items():
        if isinstance(value, str):
            # Use basic sanitization for backward compatibility
            sanitized_options[key] = sanitize_input(value)
        elif isinstance(value, (int, float, bool)):
            sanitized_options[key] = value
        # Add more type checks if necessary
    return sanitized_options
