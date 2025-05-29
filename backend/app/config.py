"""Backend configuration settings with resilience support."""

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
    
    # Batch Processing Configuration
    MAX_BATCH_REQUESTS_PER_CALL: int = int(os.getenv("MAX_BATCH_REQUESTS_PER_CALL", "50"))
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
    
    # Resilience Configuration
    # Enable/disable resilience features
    resilience_enabled: bool = os.getenv("RESILIENCE_ENABLED", "true").lower() == "true"
    circuit_breaker_enabled: bool = os.getenv("CIRCUIT_BREAKER_ENABLED", "true").lower() == "true"
    retry_enabled: bool = os.getenv("RETRY_ENABLED", "true").lower() == "true"
    
    # Default resilience strategy for AI operations
    default_resilience_strategy: str = os.getenv("DEFAULT_RESILIENCE_STRATEGY", "balanced")
    
    # Circuit Breaker Settings
    circuit_breaker_failure_threshold: int = int(os.getenv("CIRCUIT_BREAKER_FAILURE_THRESHOLD", "5"))
    circuit_breaker_recovery_timeout: int = int(os.getenv("CIRCUIT_BREAKER_RECOVERY_TIMEOUT", "60"))
    
    # Retry Settings
    retry_max_attempts: int = int(os.getenv("RETRY_MAX_ATTEMPTS", "3"))
    retry_max_delay: int = int(os.getenv("RETRY_MAX_DELAY", "30"))
    retry_exponential_multiplier: float = float(os.getenv("RETRY_EXPONENTIAL_MULTIPLIER", "1.0"))
    retry_exponential_min: float = float(os.getenv("RETRY_EXPONENTIAL_MIN", "2.0"))
    retry_exponential_max: float = float(os.getenv("RETRY_EXPONENTIAL_MAX", "10.0"))
    retry_jitter_enabled: bool = os.getenv("RETRY_JITTER_ENABLED", "true").lower() == "true"
    retry_jitter_max: float = float(os.getenv("RETRY_JITTER_MAX", "2.0"))
    
    # Operation-specific resilience strategies
    summarize_resilience_strategy: str = os.getenv("SUMMARIZE_RESILIENCE_STRATEGY", "balanced")
    sentiment_resilience_strategy: str = os.getenv("SENTIMENT_RESILIENCE_STRATEGY", "aggressive")
    key_points_resilience_strategy: str = os.getenv("KEY_POINTS_RESILIENCE_STRATEGY", "balanced")
    questions_resilience_strategy: str = os.getenv("QUESTIONS_RESILIENCE_STRATEGY", "balanced")
    qa_resilience_strategy: str = os.getenv("QA_RESILIENCE_STRATEGY", "conservative")
    
    # Monitoring and health check settings
    resilience_metrics_enabled: bool = os.getenv("RESILIENCE_METRICS_ENABLED", "true").lower() == "true"
    resilience_health_check_enabled: bool = os.getenv("RESILIENCE_HEALTH_CHECK_ENABLED", "true").lower() == "true"
    
    model_config = {"env_file": ".env"}


settings = Settings()