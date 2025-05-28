"""Backend configuration settings."""

import os
from typing import List
from pydantic_settings import BaseSettings
from dotenv import load_dotenv
from pathlib import Path

# Load .env from project root
project_root = Path(__file__).parent.parent.parent
load_dotenv(project_root / ".env")

class Settings(BaseSettings):
    """Application settings with environment variable support."""
    
    # AI Configuration
    gemini_api_key: str = os.getenv("GEMINI_API_KEY", "")
    ai_model: str = os.getenv("AI_MODEL", "gemini-2.0-flash-exp")
    ai_temperature: float = float(os.getenv("AI_TEMPERATURE", "0.7"))
    # Maximum number of requests allowed in a single batch call.
    # Can be set via the MAX_BATCH_REQUESTS_PER_CALL environment variable.
    MAX_BATCH_REQUESTS_PER_CALL: int = int(os.getenv("MAX_BATCH_REQUESTS_PER_CALL", "50"))
    # Maximum concurrent AI calls during batch processing.
    # Can be set via the BATCH_AI_CONCURRENCY_LIMIT environment variable.
    BATCH_AI_CONCURRENCY_LIMIT: int = int(os.getenv("BATCH_AI_CONCURRENCY_LIMIT", "5"))
    
    # API Configuration
    host: str = os.getenv("BACKEND_HOST", "0.0.0.0")
    port: int = int(os.getenv("BACKEND_PORT", "8000"))
    
    # Authentication Configuration
    api_key: str = os.getenv("API_KEY", "")
    additional_api_keys: str = os.getenv("ADDITIONAL_API_KEYS", "")
    
    # CORS Configuration
    allowed_origins: List[str] = ["http://localhost:8501", "http://frontend:8501"]
    
    # Application Settings
    debug: bool = os.getenv("DEBUG", "false").lower() == "true"
    log_level: str = os.getenv("LOG_LEVEL", "INFO")

    # Redis Configuration
    redis_url: str = os.getenv("REDIS_URL", "redis://redis:6379")
    
    model_config = {"env_file": ".env"}


settings = Settings()
