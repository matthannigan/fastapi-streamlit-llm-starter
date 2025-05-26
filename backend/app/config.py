"""Backend configuration settings."""

import os
from typing import List
from pydantic import BaseSettings


class Settings(BaseSettings):
    """Application settings."""
    
    # AI Model Configuration
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    ai_model: str = os.getenv("AI_MODEL", "gemini-2.0-flash-exp")
    ai_temperature: float = float(os.getenv("AI_TEMPERATURE", "0.7"))
    
    # API Configuration
    backend_host: str = os.getenv("BACKEND_HOST", "0.0.0.0")
    backend_port: int = int(os.getenv("BACKEND_PORT", "8000"))
    
    # Development Settings
    debug: bool = os.getenv("DEBUG", "true").lower() == "true"
    log_level: str = os.getenv("LOG_LEVEL", "INFO")
    
    # CORS Settings
    allowed_origins: List[str] = ["http://localhost:8501"]
    
    class Config:
        env_file = ".env"


settings = Settings() 