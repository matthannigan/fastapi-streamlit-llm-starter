# API client for backend communication and async request handling.

  file_path: `frontend/app/utils/api_client.py`

This module provides a robust HTTP client for communicating with the FastAPI backend service.
It includes comprehensive error handling, timeout management, and proper async/await patterns
optimized for Streamlit applications.

The client handles all text processing operations, health checks, and configuration retrieval
with graceful error handling and user-friendly error messages displayed through Streamlit.

## Classes

APIClient: Async HTTP client for backend API communication

## Functions

run_async: Helper function to execute async code in Streamlit's synchronous context

## Attributes

api_client: Global APIClient instance for use throughout the application

## Features

- Async HTTP requests with configurable timeouts
- Automatic JSON serialization/deserialization using Pydantic models
- Comprehensive error handling with user feedback
- Health check monitoring for backend connectivity
- Request timeout handling with graceful degradation

## Example

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

## Dependencies

httpx: Modern async HTTP client for Python
streamlit: For displaying user feedback and error messages
shared.models: Pydantic models for request/response validation

## Note

All API methods are async and should be called using the `run_async` helper function
when used in Streamlit's synchronous context. The client automatically handles
timeout errors and displays appropriate user feedback.
