"""Frontend configuration settings and environment management.

This module provides centralized configuration management for the Streamlit frontend application.
It uses Pydantic settings for validation and environment variable loading with sensible defaults.

The configuration includes API connectivity settings, UI customization options, and feature flags
for controlling application behavior in different environments.

Classes:
    Settings: Pydantic settings class with configuration validation and environment variable loading

Attributes:
    settings: Global settings instance for use throughout the application

Environment Variables:
    API_BASE_URL: Backend API base URL (default: "http://backend:8000")
    SHOW_DEBUG_INFO: Enable debug information display (default: "false")
    INPUT_MAX_LENGTH: Maximum input text length in characters (default: "10000")

Example:
    ```python
    from config import settings
    
    # Access configuration values
    api_url = settings.api_base_url
    max_length = settings.max_text_length
    ```

Note:
    The module automatically loads environment variables from a .env file located
    in the project root directory. Configuration values can be overridden through
    environment variables following Pydantic settings conventions.
"""

import os
from dotenv import load_dotenv
from pathlib import Path

# Load .env from project root
project_root = Path(__file__).parent.parent.parent
load_dotenv(project_root / ".env")

from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    """Frontend application settings."""
    
    # API Configuration
    api_base_url: str = os.getenv("API_BASE_URL", "http://backend:8000")
    
    # UI Configuration
    page_title: str = "AI Text Processor"
    page_icon: str = "🤖"
    layout: str = "wide"
    
    # Features
    show_debug_info: bool = os.getenv("SHOW_DEBUG_INFO", "false").lower() == "true"
    max_text_length: int = int(os.getenv("INPUT_MAX_LENGTH", "10000"))
    
    class Config:
        env_file = ".env"

settings = Settings()
