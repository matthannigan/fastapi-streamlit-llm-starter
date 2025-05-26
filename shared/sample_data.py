#!/usr/bin/env python3
"""
Standardized sample data for consistent examples across the codebase.

This module provides centralized sample texts and data structures that should
be used in all examples, tests, and documentation to ensure consistency.
"""

from typing import Dict, List, Any
from shared.models import (
    ProcessingOperation,
    TextProcessingRequest,
    TextProcessingResponse,
    SentimentResult
)

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
    """.strip(),
    
    "climate_change": """
    Climate change represents one of the most significant challenges facing 
    humanity today. Rising global temperatures, caused primarily by increased 
    greenhouse gas emissions, are leading to more frequent extreme weather events, 
    rising sea levels, and disruptions to ecosystems worldwide. Scientists agree 
    that immediate action is required to mitigate these effects and transition 
    to sustainable energy sources. The Paris Agreement, signed by nearly 200 
    countries, aims to limit global warming to well below 2 degrees Celsius 
    above pre-industrial levels.
    """.strip(),
    
    "business_report": """
    The quarterly earnings report shows strong performance across all business 
    units. Revenue increased by 15% compared to the same period last year, driven 
    primarily by growth in our digital services division. Customer satisfaction 
    scores have improved significantly, and we've successfully launched three new 
    products. Looking ahead, we remain optimistic about market conditions and 
    expect continued growth in the coming quarters.
    """.strip(),
    
    "positive_review": """
    I absolutely love this new product! It has exceeded all my expectations and 
    made my daily routine so much easier. The design is elegant, the functionality 
    is intuitive, and the customer service was fantastic. I would definitely 
    recommend this to anyone looking for a high-quality solution.
    """.strip(),
    
    "negative_review": """
    This product was a complete disappointment. The build quality is poor, the 
    interface is confusing, and it doesn't work as advertised. Customer support 
    was unhelpful and took days to respond. I would not recommend this product 
    and am considering returning it for a refund.
    """.strip(),
    
    "technical_documentation": """
    The new API endpoint supports RESTful operations with JSON payloads. 
    Authentication is handled via Bearer tokens, and rate limiting is enforced 
    at 1000 requests per hour per API key. The response format includes standard 
    HTTP status codes and detailed error messages. Pagination is supported for 
    large datasets using cursor-based navigation.
    """.strip(),
    
    "educational_content": """
    Photosynthesis is the process by which plants convert sunlight, carbon dioxide, 
    and water into glucose and oxygen. This fundamental biological process occurs 
    in the chloroplasts of plant cells and is essential for life on Earth. The 
    process can be divided into two main stages: the light-dependent reactions 
    and the Calvin cycle, each playing a crucial role in energy conversion.
    """.strip()
}

# Standard request examples for different operations
STANDARD_REQUEST_EXAMPLES = {
    "summarize": TextProcessingRequest(
        text=STANDARD_SAMPLE_TEXTS["ai_technology"],
        operation=ProcessingOperation.SUMMARIZE,
        options={"max_length": 100}
    ),
    
    "sentiment_positive": TextProcessingRequest(
        text=STANDARD_SAMPLE_TEXTS["positive_review"],
        operation=ProcessingOperation.SENTIMENT
    ),
    
    "sentiment_negative": TextProcessingRequest(
        text=STANDARD_SAMPLE_TEXTS["negative_review"],
        operation=ProcessingOperation.SENTIMENT
    ),
    
    "key_points": TextProcessingRequest(
        text=STANDARD_SAMPLE_TEXTS["business_report"],
        operation=ProcessingOperation.KEY_POINTS,
        options={"max_points": 4}
    ),
    
    "questions": TextProcessingRequest(
        text=STANDARD_SAMPLE_TEXTS["climate_change"],
        operation=ProcessingOperation.QUESTIONS,
        options={"num_questions": 3}
    ),
    
    "qa": TextProcessingRequest(
        text=STANDARD_SAMPLE_TEXTS["technical_documentation"],
        operation=ProcessingOperation.QA,
        question="What authentication method does the API use?"
    )
}

# Standard response examples for documentation
STANDARD_RESPONSE_EXAMPLES = {
    "summarize": TextProcessingResponse(
        operation=ProcessingOperation.SUMMARIZE,
        success=True,
        result="AI is transforming industries through automation and predictive analytics, processing vast data to identify patterns and make previously impossible predictions.",
        metadata={
            "word_count": 65,
            "model_used": "gemini-pro",
            "original_length": 312
        },
        processing_time=2.1
    ),
    
    "sentiment_positive": TextProcessingResponse(
        operation=ProcessingOperation.SENTIMENT,
        success=True,
        sentiment=SentimentResult(
            sentiment="positive",
            confidence=0.95,
            explanation="The text expresses strong positive emotions with words like 'absolutely love', 'exceeded expectations', and 'fantastic'."
        ),
        metadata={
            "word_count": 45,
            "model_used": "gemini-pro"
        },
        processing_time=1.8
    ),
    
    "sentiment_negative": TextProcessingResponse(
        operation=ProcessingOperation.SENTIMENT,
        success=True,
        sentiment=SentimentResult(
            sentiment="negative",
            confidence=0.92,
            explanation="The text contains strong negative sentiment with words like 'disappointment', 'poor', 'confusing', and 'unhelpful'."
        ),
        metadata={
            "word_count": 42,
            "model_used": "gemini-pro"
        },
        processing_time=1.6
    ),
    
    "key_points": TextProcessingResponse(
        operation=ProcessingOperation.KEY_POINTS,
        success=True,
        key_points=[
            "Revenue increased by 15% compared to last year",
            "Customer satisfaction scores improved significantly",
            "Successfully launched three new products",
            "Optimistic outlook for continued growth"
        ],
        metadata={
            "word_count": 52,
            "model_used": "gemini-pro"
        },
        processing_time=2.5
    ),
    
    "questions": TextProcessingResponse(
        operation=ProcessingOperation.QUESTIONS,
        success=True,
        questions=[
            "What are the main causes of rising global temperatures?",
            "How can individuals contribute to reducing greenhouse gas emissions?",
            "What specific actions do scientists recommend for immediate implementation?"
        ],
        metadata={
            "word_count": 78,
            "model_used": "gemini-pro"
        },
        processing_time=2.0
    ),
    
    "qa": TextProcessingResponse(
        operation=ProcessingOperation.QA,
        success=True,
        result="The API uses Bearer token authentication for securing access to endpoints.",
        metadata={
            "word_count": 67,
            "model_used": "gemini-pro",
            "question_answered": "What authentication method does the API use?"
        },
        processing_time=1.9
    )
}

# Standard API call examples for documentation
STANDARD_API_EXAMPLES = {
    "basic_request": {
        "url": "http://localhost:8000/process",
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "body": {
            "text": STANDARD_SAMPLE_TEXTS["ai_technology"],
            "operation": "summarize",
            "options": {"max_length": 100}
        }
    },
    
    "sentiment_request": {
        "url": "http://localhost:8000/process",
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "body": {
            "text": STANDARD_SAMPLE_TEXTS["positive_review"],
            "operation": "sentiment"
        }
    },
    
    "qa_request": {
        "url": "http://localhost:8000/process",
        "method": "POST",
        "headers": {"Content-Type": "application/json"},
        "body": {
            "text": STANDARD_SAMPLE_TEXTS["technical_documentation"],
            "operation": "qa",
            "question": "What authentication method does the API use?"
        }
    }
}

# Standard error examples for documentation
STANDARD_ERROR_EXAMPLES = {
    "validation_error": {
        "status_code": 422,
        "response": {
            "detail": [
                {
                    "type": "string_too_short",
                    "loc": ["body", "text"],
                    "msg": "String should have at least 10 characters",
                    "input": "short"
                }
            ]
        }
    },
    
    "missing_question": {
        "status_code": 400,
        "response": {
            "detail": "Question is required for Q&A operation"
        }
    },
    
    "server_error": {
        "status_code": 500,
        "response": {
            "detail": "Failed to process text"
        }
    }
}

def get_sample_text(text_type: str) -> str:
    """
    Get a standard sample text by type.
    
    Args:
        text_type: Type of sample text to retrieve
        
    Returns:
        The requested sample text
        
    Raises:
        KeyError: If the text type is not found
    """
    if text_type not in STANDARD_SAMPLE_TEXTS:
        available_types = list(STANDARD_SAMPLE_TEXTS.keys())
        raise KeyError(f"Text type '{text_type}' not found. Available types: {available_types}")
    
    return STANDARD_SAMPLE_TEXTS[text_type]

def get_sample_request(operation: str) -> TextProcessingRequest:
    """
    Get a standard request example for an operation.
    
    Args:
        operation: The operation type to get an example for
        
    Returns:
        A standard TextProcessingRequest example
        
    Raises:
        KeyError: If the operation is not found
    """
    if operation not in STANDARD_REQUEST_EXAMPLES:
        available_ops = list(STANDARD_REQUEST_EXAMPLES.keys())
        raise KeyError(f"Operation '{operation}' not found. Available operations: {available_ops}")
    
    return STANDARD_REQUEST_EXAMPLES[operation]

def get_sample_response(operation: str) -> TextProcessingResponse:
    """
    Get a standard response example for an operation.
    
    Args:
        operation: The operation type to get an example for
        
    Returns:
        A standard TextProcessingResponse example
        
    Raises:
        KeyError: If the operation is not found
    """
    if operation not in STANDARD_RESPONSE_EXAMPLES:
        available_ops = list(STANDARD_RESPONSE_EXAMPLES.keys())
        raise KeyError(f"Operation '{operation}' not found. Available operations: {available_ops}")
    
    return STANDARD_RESPONSE_EXAMPLES[operation]

def get_all_sample_texts() -> Dict[str, str]:
    """Get all available sample texts."""
    return STANDARD_SAMPLE_TEXTS.copy()

def get_all_request_examples() -> Dict[str, TextProcessingRequest]:
    """Get all available request examples."""
    return STANDARD_REQUEST_EXAMPLES.copy()

def get_all_response_examples() -> Dict[str, TextProcessingResponse]:
    """Get all available response examples."""
    return STANDARD_RESPONSE_EXAMPLES.copy()

def get_api_example(example_type: str) -> Dict[str, Any]:
    """
    Get a standard API call example.
    
    Args:
        example_type: Type of API example to retrieve
        
    Returns:
        Dictionary containing the API call example
        
    Raises:
        KeyError: If the example type is not found
    """
    if example_type not in STANDARD_API_EXAMPLES:
        available_types = list(STANDARD_API_EXAMPLES.keys())
        raise KeyError(f"Example type '{example_type}' not found. Available types: {available_types}")
    
    return STANDARD_API_EXAMPLES[example_type].copy()

def get_error_example(error_type: str) -> Dict[str, Any]:
    """
    Get a standard error response example.
    
    Args:
        error_type: Type of error example to retrieve
        
    Returns:
        Dictionary containing the error example
        
    Raises:
        KeyError: If the error type is not found
    """
    if error_type not in STANDARD_ERROR_EXAMPLES:
        available_types = list(STANDARD_ERROR_EXAMPLES.keys())
        raise KeyError(f"Error type '{error_type}' not found. Available types: {available_types}")
    
    return STANDARD_ERROR_EXAMPLES[error_type].copy()

# Convenience functions for common use cases
def get_short_text() -> str:
    """Get a short sample text suitable for quick examples."""
    return STANDARD_SAMPLE_TEXTS["positive_review"]

def get_medium_text() -> str:
    """Get a medium-length sample text suitable for most examples."""
    return STANDARD_SAMPLE_TEXTS["ai_technology"]

def get_long_text() -> str:
    """Get a longer sample text suitable for comprehensive examples."""
    return STANDARD_SAMPLE_TEXTS["climate_change"]

def get_technical_text() -> str:
    """Get a technical sample text suitable for documentation examples."""
    return STANDARD_SAMPLE_TEXTS["technical_documentation"]

def get_business_text() -> str:
    """Get a business-oriented sample text."""
    return STANDARD_SAMPLE_TEXTS["business_report"] 