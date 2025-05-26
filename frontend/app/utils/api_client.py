"""API client for backend communication."""

import asyncio
import logging
from typing import Optional, Dict, Any
import httpx
import streamlit as st

from shared.models import (
    TextProcessingRequest, 
    TextProcessingResponse, 
    ProcessingOperation,
    ErrorResponse
)
from frontend.app.config import settings

logger = logging.getLogger(__name__)

class APIClient:
    """Client for communicating with the backend API."""
    
    def __init__(self):
        self.base_url = settings.api_base_url
        self.timeout = httpx.Timeout(60.0)  # 60 second timeout
    
    async def health_check(self) -> bool:
        """Check if the API is healthy."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/health")
                return response.status_code == 200
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return False
    
    async def get_operations(self) -> Optional[Dict[str, Any]]:
        """Get available processing operations."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/operations")
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Failed to get operations: {response.status_code}")
                    return None
        except Exception as e:
            logger.error(f"Error getting operations: {e}")
            return None
    
    async def process_text(self, request: TextProcessingRequest) -> Optional[TextProcessingResponse]:
        """Process text using the backend API."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.post(
                    f"{self.base_url}/process",
                    json=request.dict()
                )
                
                if response.status_code == 200:
                    data = response.json()
                    return TextProcessingResponse(**data)
                else:
                    error_data = response.json()
                    error_msg = error_data.get('detail', 'Unknown error')
                    logger.error(f"API error: {error_msg}")
                    st.error(f"API Error: {error_msg}")
                    return None
                    
        except httpx.TimeoutException:
            logger.error("Request timeout")
            st.error("Request timed out. Please try again.")
            return None
        except Exception as e:
            logger.error(f"Error processing text: {e}")
            st.error(f"Error: {str(e)}")
            return None

# Helper function for running async code in Streamlit
def run_async(coro):
    """Run async code in Streamlit."""
    try:
        loop = asyncio.get_event_loop()
    except RuntimeError:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
    
    return loop.run_until_complete(coro)

# Global client instance
api_client = APIClient() 