"""Backend configuration settings with resilience support."""

import os
from typing import List
from pydantic import Field, field_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from dotenv import load_dotenv
from pathlib import Path

# Load .env from project root
project_root = Path(__file__).parent.parent.parent
load_dotenv(project_root / ".env")

class Settings(BaseSettings):
    """Application settings with environment variable support and validation."""
    
    # AI Configuration
    gemini_api_key: str = Field(default="", description="Google Gemini API key")
    ai_model: str = Field(default="gemini-2.0-flash-exp", description="Default AI model to use")
    ai_temperature: float = Field(default=0.7, ge=0.0, le=2.0, description="AI model temperature")
    
    # Batch Processing Configuration
    MAX_BATCH_REQUESTS_PER_CALL: int = Field(default=50, gt=0, description="Maximum batch requests per call")
    BATCH_AI_CONCURRENCY_LIMIT: int = Field(default=5, gt=0, description="Batch AI concurrency limit")
    
    # API Configuration
    host: str = Field(default="0.0.0.0", description="Backend host address")
    port: int = Field(default=8000, gt=0, le=65535, description="Backend port number")
    
    # Authentication Configuration
    api_key: str = Field(default="", description="Primary API key")
    additional_api_keys: str = Field(default="", description="Additional API keys (comma-separated)")
    
    # CORS Configuration
    allowed_origins: List[str] = Field(
        default=["http://localhost:8501", "http://frontend:8501"],
        description="Allowed CORS origins"
    )
    
    # Application Settings
    debug: bool = Field(default=False, description="Enable debug mode")
    log_level: str = Field(default="INFO", description="Logging level")

    # Redis Configuration
    redis_url: str = Field(default="redis://redis:6379", description="Redis connection URL")
    
    # Resilience Configuration
    # Enable/disable resilience features
    resilience_enabled: bool = Field(default=True, description="Enable resilience features")
    circuit_breaker_enabled: bool = Field(default=True, description="Enable circuit breaker")
    retry_enabled: bool = Field(default=True, description="Enable retry mechanism")
    
    # Default resilience strategy for AI operations
    default_resilience_strategy: str = Field(
        default="balanced", 
        description="Default resilience strategy",
        pattern="^(conservative|balanced|aggressive)$"
    )
    
    # Circuit Breaker Settings
    circuit_breaker_failure_threshold: int = Field(
        default=5, gt=0, description="Circuit breaker failure threshold"
    )
    circuit_breaker_recovery_timeout: int = Field(
        default=60, gt=0, description="Circuit breaker recovery timeout in seconds"
    )
    
    # Retry Settings
    retry_max_attempts: int = Field(default=3, gt=0, description="Maximum retry attempts")
    retry_max_delay: int = Field(default=30, gt=0, description="Maximum retry delay in seconds")
    retry_exponential_multiplier: float = Field(
        default=1.0, gt=0.0, description="Exponential backoff multiplier"
    )
    retry_exponential_min: float = Field(
        default=2.0, gt=0.0, description="Minimum exponential backoff delay"
    )
    retry_exponential_max: float = Field(
        default=10.0, gt=0.0, description="Maximum exponential backoff delay"
    )
    retry_jitter_enabled: bool = Field(default=True, description="Enable retry jitter")
    retry_jitter_max: float = Field(default=2.0, gt=0.0, description="Maximum jitter value")
    
    # Operation-specific resilience strategies
    summarize_resilience_strategy: str = Field(
        default="balanced",
        pattern="^(conservative|balanced|aggressive)$",
        description="Resilience strategy for summarize operations"
    )
    sentiment_resilience_strategy: str = Field(
        default="aggressive",
        pattern="^(conservative|balanced|aggressive)$",
        description="Resilience strategy for sentiment analysis"
    )
    key_points_resilience_strategy: str = Field(
        default="balanced",
        pattern="^(conservative|balanced|aggressive)$",
        description="Resilience strategy for key points extraction"
    )
    questions_resilience_strategy: str = Field(
        default="balanced",
        pattern="^(conservative|balanced|aggressive)$",
        description="Resilience strategy for question generation"
    )
    qa_resilience_strategy: str = Field(
        default="conservative",
        pattern="^(conservative|balanced|aggressive)$",
        description="Resilience strategy for Q&A operations"
    )
    
    # Monitoring and health check settings
    resilience_metrics_enabled: bool = Field(default=True, description="Enable resilience metrics")
    resilience_health_check_enabled: bool = Field(default=True, description="Enable resilience health checks")
    
    # Pydantic V2 configuration
    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        case_sensitive=False,
        extra="ignore",
        validate_assignment=True
    )

    @field_validator('log_level')
    @classmethod
    def validate_log_level(cls, v: str) -> str:
        """Validate log level is one of the allowed values."""
        allowed_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if v.upper() not in allowed_levels:
            raise ValueError(f"log_level must be one of: {', '.join(allowed_levels)}")
        return v.upper()

    @field_validator('allowed_origins')
    @classmethod
    def validate_origins(cls, v: List[str]) -> List[str]:
        """Validate CORS origins format."""
        if not v:
            raise ValueError("At least one allowed origin must be specified")
        return v


# Global settings instance for dependency injection
settings = Settings()