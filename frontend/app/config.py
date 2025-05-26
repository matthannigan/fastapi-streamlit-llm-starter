"""Frontend configuration settings."""

import os
from typing import Optional


class Settings:
    """Frontend application settings."""
    
    # API Configuration
    backend_host: str = os.getenv("BACKEND_HOST", "localhost")
    backend_port: int = int(os.getenv("BACKEND_PORT", "8000"))
    frontend_port: int = int(os.getenv("FRONTEND_PORT", "8501"))
    
    # Development Settings
    debug: bool = os.getenv("DEBUG", "true").lower() == "true"
    
    @property
    def backend_url(self) -> str:
        """Get the backend API URL."""
        return f"http://{self.backend_host}:{self.backend_port}"
    
    @property
    def api_base_url(self) -> str:
        """Get the API base URL."""
        return f"{self.backend_url}/api/v1"


settings = Settings() 