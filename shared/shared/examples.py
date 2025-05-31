"""
Examples demonstrating the use of comprehensive Pydantic models.

This file shows how to use the various models for type safety and API consistency.
"""

from datetime import datetime
from typing import List, Dict, Any
from shared.models import (
    ProcessingOperation,
    ProcessingStatus,
    TextProcessingRequest,
    TextProcessingResponse,
    BatchTextProcessingRequest,
    BatchTextProcessingResponse,
    BatchProcessingItem,
    SentimentResult,
    ErrorResponse,
    HealthResponse,
    ModelConfiguration,
    UsageStatistics,
    APIKeyValidation,
    ConfigurationUpdate,
    ModelInfo
)


def create_text_processing_request_examples() -> List[TextProcessingRequest]:
    """Create examples of text processing requests."""
    
    examples = [
        # Summarization request
        TextProcessingRequest(
            text="Artificial intelligence is revolutionizing the way we work and live. From automated customer service to predictive analytics, AI is transforming industries across the globe. Machine learning algorithms can now process vast amounts of data to identify patterns and make predictions that were previously impossible.",
            operation=ProcessingOperation.SUMMARIZE,
            options={"max_length": 100}
        ),
        
        # Sentiment analysis request
        TextProcessingRequest(
            text="I absolutely love this new product! It has exceeded all my expectations and made my daily routine so much easier. The customer service was also fantastic.",
            operation=ProcessingOperation.SENTIMENT
        ),
        
        # Key points extraction request
        TextProcessingRequest(
            text="The quarterly report shows significant growth in revenue, with a 25% increase compared to last quarter. Customer satisfaction scores have improved by 15%, and we've successfully launched three new product lines. However, operational costs have risen by 8% due to increased staffing and infrastructure investments.",
            operation=ProcessingOperation.KEY_POINTS,
            options={"max_points": 4}
        ),
        
        # Question generation request
        TextProcessingRequest(
            text="Climate change is one of the most pressing issues of our time. Rising global temperatures are causing ice caps to melt, sea levels to rise, and weather patterns to become more extreme. Scientists agree that immediate action is needed to reduce greenhouse gas emissions.",
            operation=ProcessingOperation.QUESTIONS,
            options={"max_questions": 3}
        ),
        
        # Q&A request
        TextProcessingRequest(
            text="Python is a high-level programming language known for its simplicity and readability. It supports multiple programming paradigms including procedural, object-oriented, and functional programming. Python is widely used in web development, data science, artificial intelligence, and automation.",
            operation=ProcessingOperation.QA,
            question="What are the main uses of Python?"
        )
    ]
    
    return examples


def create_text_processing_response_examples() -> List[TextProcessingResponse]:
    """Create examples of text processing responses."""
    
    examples = [
        # Summarization response
        TextProcessingResponse(
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
        
        # Sentiment analysis response
        TextProcessingResponse(
            operation=ProcessingOperation.SENTIMENT,
            success=True,
            sentiment=SentimentResult(
                sentiment="positive",
                confidence=0.95,
                explanation="The text expresses strong positive emotions with words like 'absolutely love', 'exceeded expectations', and 'fantastic'."
            ),
            metadata={
                "word_count": 28,
                "model_used": "gemini-pro"
            },
            processing_time=1.8
        ),
        
        # Key points response
        TextProcessingResponse(
            operation=ProcessingOperation.KEY_POINTS,
            success=True,
            key_points=[
                "Revenue increased by 25% compared to last quarter",
                "Customer satisfaction scores improved by 15%",
                "Successfully launched three new product lines",
                "Operational costs rose by 8% due to staffing and infrastructure"
            ],
            metadata={
                "word_count": 52,
                "model_used": "gemini-pro"
            },
            processing_time=2.5
        ),
        
        # Questions response
        TextProcessingResponse(
            operation=ProcessingOperation.QUESTIONS,
            success=True,
            questions=[
                "What are the main causes of rising global temperatures?",
                "How can individuals contribute to reducing greenhouse gas emissions?",
                "What specific actions do scientists recommend for immediate implementation?"
            ],
            metadata={
                "word_count": 45,
                "model_used": "gemini-pro"
            },
            processing_time=2.0
        )
    ]
    
    return examples


def create_batch_processing_example() -> BatchTextProcessingRequest:
    """Create an example of batch text processing request."""
    
    requests = [
        TextProcessingRequest(
            text="The new smartphone features an advanced camera system with AI-powered photography enhancements.",
            operation=ProcessingOperation.SUMMARIZE
        ),
        TextProcessingRequest(
            text="This movie was absolutely terrible. Poor acting, confusing plot, and terrible special effects.",
            operation=ProcessingOperation.SENTIMENT
        ),
        TextProcessingRequest(
            text="Our company achieved record profits this year through strategic partnerships, innovative products, and excellent customer service.",
            operation=ProcessingOperation.KEY_POINTS
        )
    ]
    
    return BatchTextProcessingRequest(
        requests=requests,
        batch_id="batch_2024_001"
    )


def create_batch_processing_response_example() -> BatchTextProcessingResponse:
    """Create an example of batch text processing response."""
    
    results = [
        BatchProcessingItem(
            request_index=0,
            status=ProcessingStatus.COMPLETED,
            response=TextProcessingResponse(
                operation=ProcessingOperation.SUMMARIZE,
                success=True,
                result="New smartphone with AI-enhanced camera system.",
                processing_time=1.5
            )
        ),
        BatchProcessingItem(
            request_index=1,
            status=ProcessingStatus.COMPLETED,
            response=TextProcessingResponse(
                operation=ProcessingOperation.SENTIMENT,
                success=True,
                sentiment=SentimentResult(
                    sentiment="negative",
                    confidence=0.92,
                    explanation="Strong negative sentiment with words like 'terrible', 'poor', and 'confusing'."
                ),
                processing_time=1.2
            )
        ),
        BatchProcessingItem(
            request_index=2,
            status=ProcessingStatus.FAILED,
            error="Processing timeout after 30 seconds"
        )
    ]
    
    return BatchTextProcessingResponse(
        batch_id="batch_2024_001",
        total_requests=3,
        completed=2,
        failed=1,
        results=results,
        total_processing_time=5.7
    )


def create_error_response_example() -> ErrorResponse:
    """Create an example of error response."""
    
    return ErrorResponse(
        error="Invalid API key provided",
        error_code="AUTH_001",
        details={
            "provided_key_length": 15,
            "expected_key_format": "32+ alphanumeric characters",
            "help_url": "https://docs.example.com/api-keys"
        }
    )


def create_health_response_example() -> HealthResponse:
    """Create an example of health response."""
    
    return HealthResponse(
        status="healthy",
        version="1.0.0",
        ai_model_available=True
    )


def create_model_configuration_example() -> ModelConfiguration:
    """Create an example of model configuration."""
    
    return ModelConfiguration(
        model_name="gemini-pro",
        temperature=0.7,
        max_tokens=1024,
        top_p=0.9
    )


def create_usage_statistics_example() -> UsageStatistics:
    """Create an example of usage statistics."""
    
    return UsageStatistics(
        total_requests=1250,
        successful_requests=1198,
        failed_requests=52,
        average_processing_time=2.3,
        operations_count={
            "summarize": 450,
            "sentiment": 320,
            "key_points": 280,
            "questions": 150,
            "qa": 50
        },
        last_request_time=datetime.now()
    )


def demonstrate_validation_examples():
    """Demonstrate validation features of the models."""
    
    print("=== Validation Examples ===\n")
    
    # Example 1: Text too short
    try:
        TextProcessingRequest(
            text="Short",  # Less than 10 characters
            operation=ProcessingOperation.SUMMARIZE
        )
    except ValueError as e:
        print(f"✓ Caught validation error for short text: {e}")
    
    # Example 2: Missing question for Q&A
    try:
        TextProcessingRequest(
            text="This is a valid text for Q&A processing.",
            operation=ProcessingOperation.QA
            # Missing question field
        )
    except ValueError as e:
        print(f"✓ Caught validation error for missing question: {e}")
    
    # Example 3: Invalid confidence score
    try:
        SentimentResult(
            sentiment="positive",
            confidence=1.5,  # Greater than 1.0
            explanation="Invalid confidence score"
        )
    except ValueError as e:
        print(f"✓ Caught validation error for invalid confidence: {e}")
    
    # Example 4: Invalid API key format
    try:
        APIKeyValidation(api_key="invalid@key!")  # Contains invalid characters
    except ValueError as e:
        print(f"✓ Caught validation error for invalid API key: {e}")


def main():
    """Main function to demonstrate all model examples."""
    
    print("=== Comprehensive Pydantic Models Examples ===\n")
    
    # Text processing examples
    print("1. Text Processing Request Examples:")
    requests = create_text_processing_request_examples()
    for i, req in enumerate(requests, 1):
        print(f"   {i}. {req.operation.value}: {req.text[:50]}...")
    
    print("\n2. Text Processing Response Examples:")
    responses = create_text_processing_response_examples()
    for i, resp in enumerate(responses, 1):
        print(f"   {i}. {resp.operation.value}: Success={resp.success}, Time={resp.processing_time}s")
    
    # Batch processing example
    print("\n3. Batch Processing Example:")
    batch_req = create_batch_processing_example()
    print(f"   Batch ID: {batch_req.batch_id}")
    print(f"   Total requests: {len(batch_req.requests)}")
    
    batch_resp = create_batch_processing_response_example()
    print(f"   Completed: {batch_resp.completed}/{batch_resp.total_requests}")
    print(f"   Failed: {batch_resp.failed}")
    
    # Other examples
    print("\n4. Other Model Examples:")
    health = create_health_response_example()
    print(f"   Health: {health.status}, AI Available: {health.ai_model_available}")
    
    config = create_model_configuration_example()
    print(f"   Model Config: {config.model_name}, Temp: {config.temperature}")
    
    stats = create_usage_statistics_example()
    print(f"   Usage Stats: {stats.total_requests} total, {stats.successful_requests} successful")
    
    error = create_error_response_example()
    print(f"   Error Example: {error.error_code} - {error.error}")
    
    # Validation examples
    print("\n5. Validation Examples:")
    demonstrate_validation_examples()
    
    print("\n=== All examples completed successfully! ===")


if __name__ == "__main__":
    main() 