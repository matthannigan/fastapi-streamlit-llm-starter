# Code Standards and Examples Guide

This document defines the standardized patterns for code examples, imports, error handling, and sample data across the FastAPI-Streamlit-LLM Starter Template.

## 📋 Table of Contents

1. [Import Patterns](#import-patterns)
2. [Error Handling](#error-handling)
3. [Sample Data](#sample-data)
4. [Code Structure](#code-structure)
5. [Documentation Examples](#documentation-examples)
6. [Testing Patterns](#testing-patterns)

## 🔧 Import Patterns

### Standard Import Order

All Python files should follow this import order:

```python
#!/usr/bin/env python3
"""Module docstring describing the purpose of the file."""

# 1. Standard library imports (alphabetical)
import asyncio
import json
import logging
import time
from datetime import datetime
from typing import Dict, Any, List, Optional, Union

# 2. Third-party imports (alphabetical)
import httpx
import streamlit as st
from fastapi import FastAPI, HTTPException, status
from pydantic import BaseModel, Field

# 3. Local application imports (alphabetical)
from app.config import settings
from app.services.text_processor import text_processor
from shared.models import (
    ProcessingOperation,
    TextProcessingRequest,
    TextProcessingResponse,
    ErrorResponse
)

# 4. Configure logging (if needed)
logger = logging.getLogger(__name__)
```

### Import Guidelines

- **Group imports** by category with blank lines between groups
- **Sort alphabetically** within each group
- **Use explicit imports** rather than `import *`
- **Import only what you need** to keep dependencies clear
- **Use consistent aliases** (e.g., `import streamlit as st`)

## 🚨 Error Handling

### Standard Error Handling Pattern

All functions should follow this error handling pattern:

```python
async def process_request(request: TextProcessingRequest) -> Optional[TextProcessingResponse]:
    """Process a text request with standardized error handling."""
    try:
        logger.info(f"Processing request for operation: {request.operation}")
        
        # Validate input
        if not request.text.strip():
            raise ValueError("Text cannot be empty")
        
        # Process the request
        result = await perform_processing(request)
        
        logger.info("Request processed successfully")
        return result
        
    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except httpx.TimeoutException:
        logger.error("Request timeout")
        raise HTTPException(
            status_code=status.HTTP_408_REQUEST_TIMEOUT,
            detail="Request timed out. Please try again."
        )
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Internal server error"
        )
```

### Error Handling Guidelines

- **Always log errors** with appropriate log levels
- **Use specific exception types** when possible
- **Provide meaningful error messages** to users
- **Include context** in error logs for debugging
- **Handle timeouts explicitly** for external API calls
- **Return appropriate HTTP status codes**

### Client-Side Error Handling

```python
async def api_call_with_error_handling(client: httpx.AsyncClient, url: str, data: Dict[str, Any]) -> Optional[Dict[str, Any]]:
    """Make API call with standardized error handling."""
    try:
        response = await client.post(url, json=data, timeout=30.0)
        response.raise_for_status()
        return response.json()
        
    except httpx.TimeoutException:
        logger.error("API request timeout")
        st.error("Request timed out. Please try again.")
        return None
    except httpx.HTTPStatusError as e:
        logger.error(f"API error: {e.response.status_code}")
        error_detail = e.response.json().get('detail', 'Unknown error')
        st.error(f"API Error: {error_detail}")
        return None
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        st.error(f"Error: {str(e)}")
        return None
```

## 📝 Sample Data

### Standard Sample Texts

Use these standardized sample texts across all examples and documentation:

```python
# Standard sample texts for consistent examples
STANDARD_SAMPLE_TEXTS = {
    "ai_technology": """
    Artificial intelligence is revolutionizing industries across the globe. 
    From healthcare diagnostics to autonomous vehicles, AI systems are becoming 
    increasingly sophisticated and capable. Machine learning algorithms can now 
    process vast amounts of data to identify patterns and make predictions with 
    remarkable accuracy. However, this rapid advancement also raises important 
    questions about ethics, privacy, and the future of human employment in an 
    AI-driven world.
    """,
    
    "climate_change": """
    Climate change represents one of the most significant challenges facing 
    humanity today. Rising global temperatures, caused primarily by increased 
    greenhouse gas emissions, are leading to more frequent extreme weather events, 
    rising sea levels, and disruptions to ecosystems worldwide. Scientists agree 
    that immediate action is required to mitigate these effects and transition 
    to sustainable energy sources. The Paris Agreement, signed by nearly 200 
    countries, aims to limit global warming to well below 2 degrees Celsius 
    above pre-industrial levels.
    """,
    
    "business_report": """
    The quarterly earnings report shows strong performance across all business 
    units. Revenue increased by 15% compared to the same period last year, driven 
    primarily by growth in our digital services division. Customer satisfaction 
    scores have improved significantly, and we've successfully launched three new 
    products. Looking ahead, we remain optimistic about market conditions and 
    expect continued growth in the coming quarters.
    """,
    
    "positive_review": """
    I absolutely love this new product! It has exceeded all my expectations and 
    made my daily routine so much easier. The design is elegant, the functionality 
    is intuitive, and the customer service was fantastic. I would definitely 
    recommend this to anyone looking for a high-quality solution.
    """,
    
    "negative_review": """
    This product was a complete disappointment. The build quality is poor, the 
    interface is confusing, and it doesn't work as advertised. Customer support 
    was unhelpful and took days to respond. I would not recommend this product 
    and am considering returning it for a refund.
    """
}
```

### Sample Data Guidelines

- **Use consistent sample texts** across all examples
- **Choose representative content** for each operation type
- **Keep text length appropriate** (100-500 words typically)
- **Include diverse content types** (technical, business, reviews, etc.)
- **Ensure content is appropriate** and professional

## 🏗️ Code Structure

### Function Structure

```python
async def standard_function_template(
    required_param: str,
    optional_param: Optional[str] = None,
    options: Dict[str, Any] = None
) -> Dict[str, Any]:
    """
    Brief description of what the function does.
    
    Args:
        required_param: Description of required parameter
        optional_param: Description of optional parameter
        options: Dictionary of additional options
        
    Returns:
        Dictionary containing the result and metadata
        
    Raises:
        ValueError: When input validation fails
        HTTPException: When API call fails
    """
    # Initialize variables
    options = options or {}
    start_time = time.time()
    
    try:
        # Input validation
        if not required_param.strip():
            raise ValueError("Required parameter cannot be empty")
        
        # Main processing logic
        result = await perform_main_operation(required_param, options)
        
        # Calculate metrics
        processing_time = time.time() - start_time
        
        # Return standardized response
        return {
            "success": True,
            "result": result,
            "metadata": {
                "processing_time": processing_time,
                "timestamp": datetime.now().isoformat()
            }
        }
        
    except Exception as e:
        logger.error(f"Error in {__name__}: {str(e)}")
        raise
```

### Class Structure

```python
class StandardServiceTemplate:
    """
    Brief description of the service class.
    
    This class provides standardized methods for [specific functionality].
    All methods follow consistent error handling and logging patterns.
    """
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        Initialize the service with configuration.
        
        Args:
            config: Optional configuration dictionary
        """
        self.config = config or {}
        self.logger = logging.getLogger(self.__class__.__name__)
        
        # Initialize any required resources
        self._initialize_resources()
    
    def _initialize_resources(self) -> None:
        """Initialize internal resources (private method)."""
        # Implementation details
        pass
    
    async def public_method(self, param: str) -> Dict[str, Any]:
        """
        Public method with standardized structure.
        
        Args:
            param: Description of parameter
            
        Returns:
            Standardized response dictionary
        """
        try:
            self.logger.info(f"Processing {param}")
            
            # Method implementation
            result = await self._process_internal(param)
            
            return {
                "success": True,
                "result": result
            }
            
        except Exception as e:
            self.logger.error(f"Error in {self.__class__.__name__}.public_method: {str(e)}")
            raise
    
    async def _process_internal(self, param: str) -> Any:
        """Internal processing method (private)."""
        # Implementation details
        pass
```

## 📚 Documentation Examples

### API Endpoint Documentation

```python
@app.post("/process", response_model=TextProcessingResponse)
async def process_text(request: TextProcessingRequest):
    """
    Process text using AI models.
    
    This endpoint accepts text and performs various AI-powered operations
    such as summarization, sentiment analysis, and key point extraction.
    
    **Example Request:**
    ```json
    {
        "text": "Artificial intelligence is revolutionizing industries...",
        "operation": "summarize",
        "options": {"max_length": 100}
    }
    ```
    
    **Example Response:**
    ```json
    {
        "operation": "summarize",
        "success": true,
        "result": "AI is transforming industries..."
    }
    ```
    
    **Error Responses:**
    - 400: Invalid input (text too short/long, invalid operation)
    - 500: Internal server error (AI service unavailable)
    """
    # Implementation follows standard error handling pattern
    pass
```

### Usage Examples in Documentation

```python
# Example 1: Basic Text Summarization
async def example_summarization():
    """Demonstrate text summarization with error handling."""
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                "http://localhost:8000/process",
                json={
                    "text": STANDARD_SAMPLE_TEXTS["ai_technology"],
                    "operation": "summarize",
                    "options": {"max_length": 100}
                },
                timeout=30.0
            )
            response.raise_for_status()
            result = response.json()
            print(f"Summary: {result['result']}")
            
        except httpx.HTTPStatusError as e:
            print(f"API Error: {e.response.status_code}")
        except httpx.TimeoutException:
            print("Request timed out")
        except Exception as e:
            print(f"Error: {str(e)}")

# Example 2: Batch Processing
async def example_batch_processing():
    """Demonstrate batch processing with error handling."""
    operations = [
        ("summarize", {"max_length": 50}),
        ("sentiment", {}),
        ("key_points", {"max_points": 3})
    ]
    
    async with httpx.AsyncClient() as client:
        results = []
        
        for operation, options in operations:
            try:
                response = await client.post(
                    "http://localhost:8000/process",
                    json={
                        "text": STANDARD_SAMPLE_TEXTS["business_report"],
                        "operation": operation,
                        "options": options
                    },
                    timeout=30.0
                )
                response.raise_for_status()
                results.append(response.json())
                
            except Exception as e:
                print(f"Error processing {operation}: {str(e)}")
                results.append({"error": str(e)})
        
        return results
```

## 🧪 Testing Patterns

### Test Structure

```python
import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient

class TestStandardPattern:
    """Test class following standard patterns."""
    
    @pytest.fixture
    def sample_data(self):
        """Provide standard sample data for tests."""
        return {
            "text": STANDARD_SAMPLE_TEXTS["ai_technology"],
            "operation": "summarize",
            "options": {"max_length": 100}
        }
    
    async def test_successful_operation(self, sample_data):
        """Test successful operation with standard sample data."""
        # Arrange
        expected_result = "AI is transforming industries..."
        
        # Act
        result = await process_text_function(sample_data)
        
        # Assert
        assert result["success"] is True
        assert "result" in result
        assert result["metadata"]["processing_time"] > 0
    
    async def test_error_handling(self, sample_data):
        """Test error handling with invalid input."""
        # Arrange
        sample_data["text"] = ""  # Invalid empty text
        
        # Act & Assert
        with pytest.raises(ValueError, match="Text cannot be empty"):
            await process_text_function(sample_data)
    
    @patch('httpx.AsyncClient')
    async def test_api_timeout(self, mock_client, sample_data):
        """Test API timeout handling."""
        # Arrange
        mock_client.return_value.__aenter__.return_value.post.side_effect = httpx.TimeoutException("Timeout")
        
        # Act
        result = await api_call_function(sample_data)
        
        # Assert
        assert result is None
```

### Test Guidelines

- **Use standard sample data** from `STANDARD_SAMPLE_TEXTS`
- **Test both success and error cases**
- **Mock external dependencies** consistently
- **Use descriptive test names** that explain what is being tested
- **Follow Arrange-Act-Assert pattern**
- **Include performance assertions** where appropriate

## 🔄 Migration Checklist

When updating existing code to follow these standards:

### 1. Import Standardization
- [ ] Reorder imports according to standard pattern
- [ ] Remove unused imports
- [ ] Use consistent import aliases
- [ ] Group imports with proper spacing

### 2. Error Handling Updates
- [ ] Add try-catch blocks with specific exception types
- [ ] Include appropriate logging statements
- [ ] Use standard error response formats
- [ ] Handle timeouts explicitly

### 3. Sample Data Consistency
- [ ] Replace custom sample texts with `STANDARD_SAMPLE_TEXTS`
- [ ] Update documentation examples
- [ ] Ensure test data consistency
- [ ] Verify example completeness

### 4. Code Structure Alignment
- [ ] Add comprehensive docstrings
- [ ] Follow standard function/class structure
- [ ] Include type hints consistently
- [ ] Add appropriate metadata to responses

### 5. Documentation Updates
- [ ] Update API documentation examples
- [ ] Ensure code examples are runnable
- [ ] Include error handling in examples
- [ ] Verify example consistency across docs

## 📋 Validation

To ensure compliance with these standards:

1. **Run linting tools** (flake8, black, isort)
2. **Execute all tests** to ensure functionality
3. **Verify examples work** by running them
4. **Check documentation** for consistency
5. **Review error handling** coverage

This standardization ensures consistency, maintainability, and reliability across the entire codebase. 