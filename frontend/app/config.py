"""Frontend configuration settings."""

import os
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
    max_text_length: int = int(os.getenv("MAX_TEXT_LENGTH", "10000"))
    
    class Config:
        env_file = ".env"

settings = Settings() 