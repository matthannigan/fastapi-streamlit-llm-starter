"""API client for backend communication."""

import httpx
import streamlit as st
from typing import Dict, Any, Optional
from app.config import settings


class APIClient:
    """Client for communicating with the backend API."""
    
    def __init__(self):
        self.base_url = settings.api_base_url
        self.timeout = 30.0
    
    async def process_text(self, text: str, prompt: str = "Please analyze and improve this text:") -> Optional[Dict[str, Any]]:
        """Send text to backend for processing."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/process-text",
                    json={"text": text, "prompt": prompt}
                )
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            st.error(f"API Error: {e}")
            return None
        except Exception as e:
            st.error(f"Unexpected error: {e}")
            return None
    
    async def get_models_info(self) -> Optional[Dict[str, Any]]:
        """Get information about available models."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/models")
                response.raise_for_status()
                return response.json()
        except httpx.HTTPError as e:
            st.error(f"API Error: {e}")
            return None
        except Exception as e:
            st.error(f"Unexpected error: {e}")
            return None
    
    async def health_check(self) -> bool:
        """Check if the backend is healthy."""
        try:
            async with httpx.AsyncClient(timeout=5.0) as client:
                response = await client.get(f"{settings.backend_url}/health")
                response.raise_for_status()
                return True
        except:
            return False


# Global API client instance
api_client = APIClient() 