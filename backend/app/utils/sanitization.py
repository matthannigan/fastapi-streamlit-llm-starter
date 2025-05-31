import re

def sanitize_input(text: str) -> str:
    """
    Sanitizes input text to prevent prompt injection.
    Removes or escapes potentially malicious characters and patterns.
    """
    if not isinstance(text, str):
        return ""

    # Remove characters that could be used to manipulate prompts or inject commands
    # This is a basic example; a more robust solution might involve more sophisticated pattern matching
    # or a library specifically designed for prompt sanitization.
    text = re.sub(r'[<>{}\[\];|`'"]', '', text)

    # Optional: Escape special characters if they are needed for legitimate input
    # text = text.replace("\", "\\")
    # text = text.replace(""", "\"")
    # text = text.replace("'", "\'")

    # Limit input length to prevent overly long inputs
    max_length = 1024  # Example max length
    if len(text) > max_length:
        text = text[:max_length]

    return text

def sanitize_options(options: dict) -> dict:
    """
    Sanitizes options dictionary.
    """
    if not isinstance(options, dict):
        return {}

    sanitized_options = {}
    for key, value in options.items():
        if isinstance(value, str):
            sanitized_options[key] = sanitize_input(value)
        elif isinstance(value, (int, float, bool)):
            sanitized_options[key] = value
        # Add more type checks if necessary
    return sanitized_options
