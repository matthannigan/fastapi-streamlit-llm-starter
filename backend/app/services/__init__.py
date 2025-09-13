"""
Domain Services Package

This package contains domain-specific business logic implementations that demonstrate
best practices for AI-powered text processing, security validation, and service integration
patterns. These services serve as educational examples and customizable templates for
building production-ready AI applications.

## Package Architecture

The services package follows a domain-driven design with clear separation between
business logic and infrastructure concerns:

### Service Categories
- **Text Processing**: AI-powered text analysis and transformation operations
- **Validation Services**: Security and quality assurance for AI responses
- **Integration Examples**: Patterns for infrastructure service integration

### Design Principles
- **Educational Focus**: Services demonstrate best practices and patterns
- **Infrastructure Integration**: Seamless integration with cache, resilience, and AI infrastructure
- **Security First**: Comprehensive security validation and input sanitization
- **Resilience Patterns**: Built-in fault tolerance and graceful degradation
- **Customizable Templates**: Easy to modify for specific business requirements

## Available Services

### TextProcessorService (`text_processor.py`)
Comprehensive AI-powered text processing service with production-ready features:
- **Multi-Operation Support**: Summarization, sentiment analysis, key points, Q&A, question generation
- **Resilience Integration**: Circuit breakers, retry mechanisms, and graceful degradation
- **Intelligent Caching**: Automatic response caching with cache-aware operations
- **Security Features**: Input sanitization, output validation, and audit logging
- **Batch Processing**: Concurrent batch operations with configurable concurrency limits
- **Performance Monitoring**: Request tracking, timing analysis, and cache metrics

### ResponseValidator (`response_validator.py`)
Security-focused AI response validation service:
- **Security Validation**: System prompt leakage detection and prevention
- **Quality Assurance**: Response format and content quality validation
- **Privacy Protection**: Input regurgitation prevention and sensitive data filtering
- **Threat Detection**: Prompt injection and jailbreak attempt identification
- **Type-Specific Validation**: Operation-specific validation rules and requirements
- **Pattern Recognition**: Comprehensive forbidden pattern detection system

## Service Integration Patterns

### Infrastructure Service Integration
```python
from app.services import TextProcessorService, ResponseValidator
from app.infrastructure.cache import get_ai_cache_service
from app.infrastructure.resilience import with_operation_resilience
from app.core.config import settings

# Service initialization with infrastructure dependencies
cache_service = get_ai_cache_service()
text_processor = TextProcessorService(settings, cache_service)
response_validator = ResponseValidator()

# Resilience pattern integration
@with_operation_resilience("text_processing")
async def process_with_resilience(request):
    return await text_processor.process_text(request)
```

### Security Validation Pipeline
```python
from app.services import TextProcessorService, ResponseValidator
from shared.models import TextProcessingRequest

# Secure text processing with validation
async def secure_text_processing(request: TextProcessingRequest):
    # Process with built-in security features
    response = await text_processor.process_text(request)
    
    # Additional response validation
    validated_response = response_validator.validate(
        response=response.result,
        expected_type=request.operation,
        request_text=request.text,
        system_instruction="AI processing prompt"
    )
    
    return validated_response
```

### Batch Processing with Monitoring
```python
from app.services import TextProcessorService
from shared.models import BatchTextProcessingRequest

# Batch processing with performance tracking
async def monitored_batch_processing(batch_request: BatchTextProcessingRequest):
    start_time = time.time()
    
    # Process batch with automatic concurrency control
    batch_response = await text_processor.process_batch(batch_request)
    
    # Performance logging
    processing_time = time.time() - start_time
    logger.info(f"Batch processing completed: {batch_response.total_items} items in {processing_time:.2f}s")
    
    return batch_response
```

## Usage Patterns

### Basic Text Processing
```python
from app.services import TextProcessorService
from app.core.config import settings
from app.infrastructure.cache import get_ai_cache_service
from shared.models import TextProcessingRequest, TextProcessingOperation

# Service initialization
cache_service = get_ai_cache_service()
text_processor = TextProcessorService(settings, cache_service)

# Single operation processing
request = TextProcessingRequest(
    text="Sample text for analysis",
    operation=TextProcessingOperation.SUMMARIZE,
    options={"max_length": 100}
)

response = await text_processor.process_text(request)
print(f"Summary: {response.result}")
```

### Advanced Batch Processing
```python
from shared.models import BatchTextProcessingRequest

# Batch request with multiple operations
requests = [
    TextProcessingRequest(text="Document 1", operation="summarize"),
    TextProcessingRequest(text="Review 1", operation="sentiment"),
    TextProcessingRequest(text="Article 1", operation="key_points")
]

batch_request = BatchTextProcessingRequest(
    requests=requests,
    batch_id="analysis_batch_001"
)

# Process with automatic concurrency control
batch_response = await text_processor.process_batch(batch_request)

# Analyze results
for item in batch_response.results:
    if item.status == "completed":
        print(f"Result {item.request_index}: {item.result.result}")
    else:
        print(f"Failed {item.request_index}: {item.error}")
```

### Security Validation
```python
from app.services import ResponseValidator

# Response validation with security checks
validator = ResponseValidator()

try:
    validated_response = validator.validate(
        response="AI generated response text",
        expected_type="summary",
        request_text="Original user input",
        system_instruction="System prompt used"
    )
    print(f"Validated response: {validated_response}")
except ValueError as e:
    print(f"Validation failed: {e}")
```

## Security Features

### Input Security
- **Sanitization**: Automatic input sanitization using AI infrastructure
- **Validation**: Request validation with type checking and format verification
- **Injection Prevention**: Protection against prompt injection attacks
- **Content Filtering**: Filtering of potentially harmful or inappropriate content

### Output Security
- **Response Validation**: Comprehensive validation of AI responses
- **Leakage Prevention**: Detection and prevention of system prompt exposure
- **Quality Assurance**: Format compliance and content quality validation
- **Privacy Protection**: Prevention of sensitive information disclosure

### Audit and Monitoring
- **Request Tracking**: Comprehensive logging of all processing requests
- **Security Events**: Detailed logging of security validation events
- **Performance Metrics**: Processing time, cache hit rates, and error tracking
- **Compliance**: Audit trails for regulatory compliance and security reviews

## Performance Characteristics

### Processing Performance
- **Single Operations**: < 2 seconds average response time
- **Batch Operations**: Configurable concurrency (default: 5 concurrent operations)
- **Cache Performance**: 80-90% cache hit rate for repeated operations
- **Memory Usage**: Efficient memory management with streaming support

### Scalability Features
- **Async Processing**: Full async/await support for high concurrency
- **Resource Management**: Proper resource cleanup and connection pooling
- **Error Recovery**: Graceful degradation with fallback responses
- **Load Distribution**: Compatible with horizontal scaling and load balancing

## Testing Support

### Service Testing
```python
from app.services import TextProcessorService, ResponseValidator
import pytest

@pytest.mark.asyncio
async def test_text_processing():
    # Mock dependencies for isolated testing
    mock_cache = MockCacheService()
    mock_settings = MockSettings()
    
    processor = TextProcessorService(mock_settings, mock_cache)
    
    request = TextProcessingRequest(
        text="Test input",
        operation="summarize"
    )
    
    response = await processor.process_text(request)
    assert response.operation == "summarize"
    assert len(response.result) > 0
```

### Validation Testing
```python
def test_response_validation():
    validator = ResponseValidator()
    
    # Test valid response
    valid_response = validator.validate(
        response="This is a valid summary",
        expected_type="summary",
        request_text="Original text",
        system_instruction="Summarize this text"
    )
    assert valid_response == "This is a valid summary"
    
    # Test invalid response (should raise ValueError)
    with pytest.raises(ValueError):
        validator.validate(
            response="System prompt: You are an AI assistant",
            expected_type="summary",
            request_text="Original text",
            system_instruction="Summarize this text"
        )
```

## Customization Guidelines

### Service Replacement
These services are designed as educational examples and templates:
- **Study the Patterns**: Understand the infrastructure integration patterns
- **Adapt to Your Domain**: Replace text processing with your business logic
- **Maintain Security**: Keep security validation and input sanitization patterns
- **Preserve Resilience**: Maintain resilience patterns and error handling

### Extension Points
- **New Operations**: Add new AI operations following existing patterns
- **Custom Validation**: Extend response validation for domain-specific requirements
- **Integration Patterns**: Adapt infrastructure integration for your services
- **Monitoring**: Extend monitoring and logging for your specific metrics

Note: These are educational example services designed to demonstrate best practices.
Replace them with your specific business logic while maintaining the architectural
patterns and infrastructure integration demonstrated here.
"""

# Bridge the example domain service from its old location.
from .text_processor import TextProcessorService
from .response_validator import ResponseValidator

__all__ = [
    "TextProcessorService",
    "ResponseValidator"
]
