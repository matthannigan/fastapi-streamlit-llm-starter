from functools import lru_cache
from fastapi import Depends
from .config import Settings, settings


@lru_cache()
def get_settings() -> Settings:
    """
    Dependency provider for application settings.
    
    Uses lru_cache to ensure the same Settings instance is returned
    across all dependency injections, improving performance and
    ensuring consistent configuration throughout the application.
    
    Returns:
        Settings: The application settings instance
    """
    return settings


# Alternative dependency provider that creates a fresh instance each time
# (useful for testing scenarios where you might want to override settings)
def get_fresh_settings() -> Settings:
    """
    Dependency provider that creates a fresh Settings instance.
    
    This is useful for testing scenarios where you might want to
    override environment variables or provide different configurations.
    
    Returns:
        Settings: A fresh Settings instance
    """
    return Settings() 