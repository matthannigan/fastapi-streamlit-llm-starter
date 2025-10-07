"""API client for backend communication and async request handling.

This module provides a robust HTTP client for communicating with the FastAPI backend service.
It includes comprehensive error handling, timeout management, and proper async/await patterns
optimized for Streamlit applications.

The client handles all text processing operations, health checks, and configuration retrieval
with graceful error handling and user-friendly error messages displayed through Streamlit.

Classes:
    APIClient: Async HTTP client for backend API communication

Functions:
    run_async: Helper function to execute async code in Streamlit's synchronous context

Attributes:
    api_client: Global APIClient instance for use throughout the application

Features:
    - Async HTTP requests with configurable timeouts
    - Automatic JSON serialization/deserialization using Pydantic models
    - Comprehensive error handling with user feedback
    - Health check monitoring for backend connectivity
    - Request timeout handling with graceful degradation

Example:
    ```python
    from utils.api_client import api_client, run_async
    from shared.models import TextProcessingRequest, TextProcessingOperation
    
    # Check API health
    is_healthy = run_async(api_client.health_check())
    
    # Process text
    request = TextProcessingRequest(
        text="Sample text",
        operation=TextProcessingOperation.SUMMARIZE
    )
    response = run_async(api_client.process_text(request))
    ```

Dependencies:
    httpx: Modern async HTTP client for Python
    streamlit: For displaying user feedback and error messages
    shared.models: Pydantic models for request/response validation

Note:
    All API methods are async and should be called using the `run_async` helper function
    when used in Streamlit's synchronous context. The client automatically handles
    timeout errors and displays appropriate user feedback.
"""

import asyncio
import logging
from typing import Optional, Dict, Any
import httpx
import streamlit as st

from shared.models import (
    TextProcessingRequest,
    TextProcessingResponse
)
from config import settings

logger = logging.getLogger(__name__)

class APIClient:
    """Client for communicating with the backend API."""
    
    def __init__(self):
        self.base_url = settings.api_base_url
        self.timeout = httpx.Timeout(60.0)  # 60 second timeout
    
    async def health_check(self) -> Optional[Dict[str, Any]]:
        """Check API health and return full health status.

        Returns:
            Optional[Dict[str, Any]]: Health status dictionary containing:
                - status: Overall health status ("healthy", "degraded", "unhealthy")
                - ai_model_available: Boolean indicating AI model availability
                - cache_healthy: Optional boolean indicating cache system health
                - resilience_healthy: Optional boolean indicating resilience health
                Returns None if health check fails
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/v1/health")
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Health check returned status {response.status_code}")
                    return None
        except Exception as e:
            logger.error(f"Health check failed: {e}")
            return None

    async def get_cache_status(self) -> Optional[Dict[str, Any]]:
        """Get detailed cache infrastructure status from internal API.

        Returns:
            Optional[Dict[str, Any]]: Cache status dictionary containing:
                - redis: Redis backend status with connection state and metrics
                - memory: In-memory cache status with entry counts
                - performance: Cache performance metrics including hit rates
                - security: Security configuration including TLS and auth status
                Returns None if request fails
        """
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/internal/cache/status")
                if response.status_code == 200:
                    return response.json()
                else:
                    logger.error(f"Cache status check returned status {response.status_code}")
                    return None
        except Exception as e:
            logger.error(f"Cache status check failed: {e}")
            return None
    
    async def get_operations(self) -> Optional[Dict[str, Any]]:
        """Get available processing operations."""
        try:
            async with httpx.AsyncClient(timeout=self.timeout) as client:
                response = await client.get(f"{self.base_url}/v1/text_processing/operations")
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
                    f"{self.base_url}/v1/text_processing/process",
                    json=request.model_dump()
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
