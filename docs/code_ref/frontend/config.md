# Frontend configuration settings and environment management.

This module provides centralized configuration management for the Streamlit frontend application.
It uses Pydantic settings for validation and environment variable loading with sensible defaults.

The configuration includes API connectivity settings, UI customization options, and feature flags
for controlling application behavior in different environments.

## Classes

Settings: Pydantic settings class with configuration validation and environment variable loading

## Attributes

settings: Global settings instance for use throughout the application

## Environment Variables

API_BASE_URL: Backend API base URL (default: "http://backend:8000")
SHOW_DEBUG_INFO: Enable debug information display (default: "false")
INPUT_MAX_LENGTH: Maximum input text length in characters (default: "10000")

## Example

```python
from config import settings

# Access configuration values
api_url = settings.api_base_url
max_length = settings.max_text_length
```

## Note

The module automatically loads environment variables from a .env file located
in the project root directory. Configuration values can be overridden through
environment variables following Pydantic settings conventions.
