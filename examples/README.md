# API Integration Examples

This directory contains comprehensive examples demonstrating **API integration patterns** for the FastAPI-Streamlit-LLM Starter Template. These examples show how to interact with the backend API using HTTP clients and are designed for frontend developers, API consumers, and integration testing.

> **🏗️ Looking for backend infrastructure examples?** See [Infrastructure Examples](../backend/examples/README.md) for advanced backend service configurations, caching patterns, and resilience systems.

## 📁 Directory Contents

### API Integration Examples

- **`basic_usage.py`** - Complete demonstration of all API operations via HTTP client
- **`custom_operation.py`** - Guide for adding custom text processing operations  
- **`integration_test.py`** - Comprehensive integration testing suite

### Quick Start

```bash
# Make sure the backend is running
cd backend
python -m uvicorn app.main:app --reload

# In another terminal, run examples
cd examples
python basic_usage.py
```

## 🚀 API Integration Examples

### `basic_usage.py`

This script demonstrates how to interact with all API endpoints using HTTP clients. Perfect for understanding API integration patterns and building your own client applications.

**API Integration Features Demonstrated:**
- ✅ HTTP client setup and connection management
- 📋 REST API endpoint interaction patterns
- 📝 Text processing via API calls (summarization, sentiment, etc.)
- 🚨 Comprehensive error handling and retry logic
- ⚡ Performance benchmarking of API operations
- 🔗 Async HTTP client usage with context managers

**Usage:**
```bash
python basic_usage.py
```

**Sample Output:**
```
🤖 FastAPI-Streamlit-LLM Starter Template - Basic Usage Examples
============================================================

1️⃣ Health Check
--------------
✅ API Status: healthy
🤖 AI Model Available: True
📅 Timestamp: 2024-01-15T10:30:00

2️⃣ Available Operations
----------------------
📋 Available operations:
   • Summarize: Generate a concise summary of the text (Options: max_length)
   • Sentiment Analysis: Analyze the emotional tone of the text
   • Key Points: Extract the main points from the text (Options: max_points)
   ...
```

## 🔧 API Extension Guide

### `custom_operation.py`

This script provides a step-by-step guide for extending the API with custom text processing operations, including how to modify both backend and frontend components.

**Custom Operations Demonstrated:**
- 🌐 Text translation
- 📊 Text classification
- 🏷️ Named entity extraction
- 📖 Readability analysis

**Usage:**
```bash
python custom_operation.py
```

**What You'll Learn:**
1. How to extend the `TextProcessingOperation` enum
2. Adding new processing methods to the backend
3. Updating API endpoints
4. Enhancing the frontend UI
5. Testing and deployment strategies

**Example Custom Operation:**
```python
async def _translate_text(self, text: str, options: Dict[str, Any]) -> str:
    """Translate text to target language."""
    target_language = options.get("target_language", "Spanish")
    
    prompt = f"""
    Translate the following text to {target_language}:
    
    Text: {text}
    
    Translation:
    """
    
    result = await self.agent.run(prompt)
    return result.output.strip()
```

## 📋 Prerequisites

Before running the examples, ensure you have:

1. **Backend Running:**
   ```bash
   cd backend
   python -m uvicorn app.main:app --reload
   ```

2. **Environment Variables:**
   ```bash
   export GEMINI_API_KEY="your-api-key-here"
   ```

3. **Dependencies Installed:**
   ```bash
   pip install httpx asyncio
   ```

## 🎯 API Integration Scenarios

### Scenario 1: Building API Clients
Use `basic_usage.py` to understand how to build robust API clients:

```python
from examples.basic_usage import APIClient

async def my_app():
    async with APIClient() as client:
        result = await client.process_text(
            text="Your text here",
            operation="summarize",
            options={"max_length": 100}
        )
        print(result)
```

### Scenario 2: Extending API Functionality
Follow `custom_operation.py` to add new API endpoints and text processing capabilities:

1. Define new operation in `shared/models.py`
2. Implement processing logic in `backend/app/services/text_processor.py`
3. Update API endpoints in `backend/app/main.py`
4. Enhance frontend UI in `frontend/app/app.py`

### Scenario 3: API Testing & Validation
Use `integration_test.py` for comprehensive API testing and system validation:

```bash
# Run all tests
python integration_test.py

# Or integrate with pytest
pytest integration_test.py -v
```

## 🔍 API Reference

### Health Check
```http
GET /health
```

**Response:**
```json
{
  "status": "healthy",
  "ai_model_available": true,
  "timestamp": "2024-01-15T10:30:00"
}
```

### Process Text
```http
POST /process
```

**Request:**
```json
{
  "text": "Your text to process",
  "operation": "summarize",
  "options": {"max_length": 100}
}
```

**Response:**
```json
{
  "operation": "summarize",
  "success": true,
  "result": "Summary of the text...",
  "processing_time": 2.3,
  "metadata": {"word_count": 150}
}
```

### Available Operations
```http
GET /operations
```

**Response:**
```json
{
  "operations": [
    {
      "id": "summarize",
      "name": "Summarize",
      "description": "Generate a concise summary",
      "options": ["max_length"]
    }
  ]
}
```

## 🚨 Error Handling

The examples demonstrate proper error handling for common scenarios:

### Empty Text
```python
# This will raise a validation error
await client.process_text(text="", operation="summarize")
```

### Invalid Operation
```python
# This will raise a 422 error
await client.process_text(text="Valid text", operation="invalid_op")
```

### Missing Required Parameters
```python
# Q&A requires a question
await client.process_text(text="Valid text", operation="qa")  # Missing question
```

## 🔧 Troubleshooting

### Common Issues

1. **Connection Refused**
   ```
   Error: Connection refused to localhost:8000
   ```
   **Solution:** Make sure the FastAPI backend is running

2. **API Key Error**
   ```
   Error: AI model not available
   ```
   **Solution:** Set the `GEMINI_API_KEY` environment variable

3. **Timeout Errors**
   ```
   Error: Request timeout
   ```
   **Solution:** Increase timeout in the client or check network connectivity

### Debug Mode
Enable debug logging in the examples:

```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## 📚 Additional Resources

### Related Examples
- 🏗️ [Infrastructure Examples](../backend/examples/README.md) - Backend service configurations, caching patterns, and resilience systems
- 📚 [Main Project README](../README.md) - Project overview and setup instructions

### Development Resources
- **API Documentation:** `http://localhost:8000/docs` - Interactive Swagger/OpenAPI docs
- **Frontend Interface:** `http://localhost:8501` - Streamlit web interface
- **Backend Tests:** `../backend/tests/` - Backend unit and integration tests
- **Frontend Tests:** `../frontend/tests/` - Frontend UI tests

## 🤝 Contributing

To add new examples:

1. Create a new Python file in this directory
2. Follow the existing code style and documentation format
3. Add comprehensive error handling
4. Include usage instructions in this README
5. Test thoroughly before submitting

## 📄 License

These API integration examples are part of the FastAPI-Streamlit-LLM Starter Template and are subject to the same license terms as the main project. 