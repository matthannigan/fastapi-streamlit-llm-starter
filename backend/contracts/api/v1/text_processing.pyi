"""
Domain Service: Comprehensive AI Text Processing REST API with Enterprise-Grade Infrastructure Integration

📚 **EXAMPLE IMPLEMENTATION** - Replace in your project  
💡 **Demonstrates infrastructure usage patterns**  
🔄 **Expected to be modified/replaced**

This module provides a comprehensive REST API implementation for AI-powered text processing operations,
serving as a complete reference implementation that demonstrates enterprise-grade patterns for building
domain services with robust infrastructure integration. It showcases how to leverage infrastructure
services for AI processing, caching, resilience patterns, security, and operational monitoring while
maintaining clean separation of concerns between domain logic and infrastructure capabilities.

The module implements production-ready patterns including authentication, validation, caching, resilience,
monitoring, and error handling, providing a complete template for AI-powered API development that can be
customized and extended for specific business requirements while maintaining operational excellence.

## Architecture Overview

### Domain Service Implementation Pattern
This module demonstrates the **Domain Service** architectural pattern where business logic is implemented
as services that orchestrate infrastructure capabilities. The text processing operations represent domain
functionality that leverages infrastructure services for:

- **AI Model Integration**: PydanticAI agents with Gemini models for text processing operations
- **Caching Layer**: Redis-backed response caching with memory fallback for performance optimization
- **Resilience Patterns**: Circuit breakers, retry mechanisms, and graceful degradation
- **Security Integration**: API key authentication and input validation for secure operation
- **Monitoring Capabilities**: Request tracing, performance metrics, and operational visibility

### API Design Principles
- **RESTful Design**: Standard HTTP methods and status codes with clear resource organization
- **Comprehensive Validation**: Pydantic models for request/response validation and API documentation
- **Error Handling**: Structured exception handling with appropriate HTTP status codes
- **Authentication**: API key-based security with flexible access control patterns
- **Documentation**: OpenAPI/Swagger integration with comprehensive endpoint documentation

## Core Components

### API Endpoints
- `GET /v1/text_processing/operations`: Available operations and configurations (optional auth)
- `POST /v1/text_processing/process`: Single text processing with AI operations (requires auth)
- `POST /v1/text_processing/batch_process`: Batch text processing with limits (requires auth)
- `GET /v1/text_processing/batch_status/{batch_id}`: Batch status checking (requires auth)
- `GET /v1/text_processing/health`: Service health with infrastructure status (optional auth)

### Processing Operations
- **summarize**: Text summarization with configurable length
- **sentiment**: Sentiment analysis with confidence scores  
- **key_points**: Key point extraction with configurable count
- **questions**: Question generation from text content
- **qa**: Question answering (requires question parameter)

### Features
- **Batch Processing**: Configurable limits with comprehensive error handling
- **Request Tracing**: Unique IDs for logging and debugging
- **Resilience Integration**: Circuit breakers, retries, and graceful degradation
- **Input Validation**: Pydantic models with sanitization
- **Error Handling**: Structured exceptions with proper HTTP status codes

## Dependencies & Integration

### Infrastructure Dependencies
- `app.infrastructure.security`: API key authentication services
- `app.services.text_processor.TextProcessorService`: AI text processing with resilience
- `app.core.exceptions`: Structured exception handling
- `app.schemas`: Pydantic request/response models

### Domain Logic
- Operation validation and business rule enforcement
- Batch size limits and concurrent processing management
- Request tracing and logging for operational visibility
- Health monitoring that combines domain and infrastructure status

## Usage Examples

### Single Text Processing
```bash
POST /v1/text_processing/process
Content-Type: application/json
Authorization: Bearer your-api-key

{
    "text": "Your text to process here",
    "operation": "summarize", 
    "options": {"max_length": 150}
}
```

### Batch Processing
```bash
POST /v1/text_processing/batch_process
Content-Type: application/json
Authorization: Bearer your-api-key

{
    "requests": [
        {"text": "First document", "operation": "sentiment"},
        {"text": "Second document", "operation": "key_points", "options": {"max_points": 5}}
    ],
    "batch_id": "my-batch-2024"
}
```

### Operations Discovery
```bash
GET /v1/text_processing/operations
# No auth required - returns available operations and their options
```

## Response Examples

### Successful Processing
```json
{
    "result": "Generated summary of the input text...",
    "operation": "summarize",
    "metadata": {"processing_time": 1.23}
}
```

### Batch Response
```json
{
    "batch_id": "my-batch-2024",
    "total_requests": 2,
    "completed": 2,
    "failed": 0,
    "results": [
        {"result": "Positive sentiment", "operation": "sentiment"},
        {"result": "Key points: 1. Point one...", "operation": "key_points"}
    ]
}
```

## Error Handling

### Exception Types
- `ValidationError`: Invalid requests, missing required fields
- `BusinessLogicError`: Domain rule violations, operation constraints
- `InfrastructureError`: AI service failures, cache issues, network problems

### HTTP Status Codes
- `200 OK`: Successful processing
- `400 Bad Request`: Validation errors
- `401 Unauthorized`: Authentication failures
- `422 Unprocessable Entity`: Request validation errors
- `500 Internal Server Error`: Infrastructure failures
- `502 Bad Gateway`: AI service errors
- `503 Service Unavailable`: Service temporarily unavailable

## Implementation Notes

This service demonstrates domain-level text processing APIs that:
- Compose multiple infrastructure services for comprehensive functionality
- Implement proper authentication and authorization patterns
- Provide structured error handling with appropriate HTTP status codes
- Support both single and batch processing with configurable limits
- Include comprehensive logging and request tracing for operations

**Replace in your project** - This is a complete example of an AI-powered domain service.
Customize the operations, validation logic, and business rules based on your specific
text processing requirements and use cases.
"""

import logging
import uuid
import time
from typing import Dict, Any, Optional
from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel, Field
from app.schemas import ErrorResponse, TextProcessingRequest, TextProcessingResponse, BatchTextProcessingRequest, BatchTextProcessingResponse
from app.core.config import settings
from app.core.exceptions import ValidationError, BusinessLogicError, InfrastructureError
from app.api.v1.deps import get_text_processor
from app.services.text_processor import TextProcessorService
from app.infrastructure.security import verify_api_key, optional_verify_api_key

router = APIRouter(prefix='/text_processing', tags=['Text Processing'])


@router.get('/operations', responses={401: {'model': ErrorResponse, 'description': 'Authentication Error'}})
async def get_operations(api_key: str = Depends(optional_verify_api_key)):
    """
    AI operations discovery endpoint with comprehensive configuration metadata and optional authentication.
    
    This endpoint provides complete discoverability for all supported AI text processing operations,
    including detailed configuration options, parameter requirements, and operational metadata. It
    serves as the primary API discovery mechanism for client applications and development tools,
    enabling dynamic UI generation and automated API integration with optional authentication for
    enhanced functionality access.
    
    Args:
        api_key: Optional API key for enhanced authentication and access logging. When provided,
                enables additional operational metadata and usage tracking. Authentication is optional
                to support public API discovery and development integration scenarios.
    
    Returns:
        dict: Comprehensive operations catalog containing:
             - operations: List of operation definition objects, each providing complete metadata:
               * id: Unique operation identifier for API requests and caching
               * name: Human-readable operation name for UI display and documentation
               * description: Detailed operational description explaining functionality and use cases
               * options: List of supported configuration parameter names for operation customization
               * requires_question: Boolean flag indicating operations requiring question parameter input
    
    Behavior:
        **API Discovery and Documentation:**
        - Provides complete catalog of all supported AI text processing operations
        - Includes comprehensive metadata for dynamic client integration and UI generation
        - Enables automatic API documentation generation and client SDK development
        - Supports versioning and backward compatibility for evolving operation sets
        
        **Authentication Integration:**
        - Supports optional authentication for enhanced access and usage tracking
        - Maintains public accessibility for API discovery and development scenarios
        - Enables authentication-based operation filtering and access control future enhancement
        - Provides consistent authentication patterns across all API endpoints
        
        **Client Integration Support:**
        - Enables dynamic UI generation based on available operations and options
        - Supports automated validation of operation requests in client applications
        - Facilitates API testing tools and development environment integration
        - Provides machine-readable operation metadata for automated processing
        
        **Operation Metadata Management:**
        - Maintains centralized definition of all available AI processing operations
        - Provides consistent operation information across all API endpoints
        - Enables operation-specific configuration validation and request processing
        - Supports future extension with additional operation metadata and capabilities
    
    Examples:
        >>> # Public API discovery (no authentication required)
        >>> response = await client.get("/v1/text_processing/operations")
        >>> operations = response.json()["operations"]
        >>> summarize_op = next(op for op in operations if op["id"] == "summarize")
        >>> assert summarize_op["options"] == ["max_length"]
        >>> assert "requires_question" not in summarize_op
        
        >>> # Authenticated access for enhanced metadata
        >>> headers = {"Authorization": "Bearer api-key-12345"}
        >>> response = await client.get("/v1/text_processing/operations", headers=headers)
        >>> assert response.status_code == 200
        >>> operations_data = response.json()
        
        >>> # Dynamic UI generation based on operations
        >>> def generate_operation_forms(operations):
        ...     forms = []
        ...     for op in operations:
        ...         form = {"id": op["id"], "name": op["name"], "fields": []}
        ...         if op.get("requires_question"):
        ...             form["fields"].append({"name": "question", "required": True})
        ...         for option in op["options"]:
        ...             form["fields"].append({"name": option, "required": False})
        ...         forms.append(form)
        ...     return forms
        
        >>> # Client SDK operation validation
        >>> available_operations = {op["id"]: op for op in operations["operations"]}
        >>> def validate_request(operation_id, options):
        ...     if operation_id not in available_operations:
        ...         raise ValueError(f"Unknown operation: {operation_id}")
        ...     op_def = available_operations[operation_id]
        ...     if op_def.get("requires_question") and "question" not in options:
        ...         raise ValueError(f"Operation {operation_id} requires question parameter")
        ...     return True
        
        >>> # API testing and development integration
        >>> def test_all_operations():
        ...     ops_response = await client.get("/v1/text_processing/operations")
        ...     operations = ops_response.json()["operations"]
        ...     
        ...     for operation in operations:
        ...         test_request = {
        ...             "text": "Sample text for testing",
        ...             "operation": operation["id"]
        ...         }
        ...         if operation.get("requires_question"):
        ...             test_request["question"] = "What is this about?"
        ...         
        ...         response = await client.post("/v1/text_processing/process", json=test_request)
        ...         print(f"Operation {operation['id']}: {response.status_code}")
        
        >>> # Complete operations discovery response structure
        >>> expected_operations = ["summarize", "sentiment", "key_points", "questions", "qa"]
        >>> actual_operations = [op["id"] for op in operations["operations"]]
        >>> assert all(op_id in actual_operations for op_id in expected_operations)
    
    Note:
        This endpoint serves as the primary API discovery interface and should remain stable
        across API versions to maintain client compatibility. Operation metadata changes should
        be carefully versioned to prevent breaking existing client integrations. The endpoint
        supports both public and authenticated access to enable flexible development workflows
        while maintaining security for production usage scenarios.
    """
    ...


@router.post('/process', response_model=TextProcessingResponse, responses={400: {'model': ErrorResponse, 'description': 'Validation Error'}, 422: {'model': ErrorResponse, 'description': 'Validation Error'}, 500: {'model': ErrorResponse, 'description': 'Internal Server Error'}, 502: {'model': ErrorResponse, 'description': 'AI Service Error'}, 503: {'model': ErrorResponse, 'description': 'Service Unavailable'}})
async def process_text(request: TextProcessingRequest, api_key: str = Depends(verify_api_key), text_processor: TextProcessorService = Depends(get_text_processor)):
    """
    Primary AI text processing endpoint with comprehensive operation support and resilience integration.
    
    This endpoint provides the core AI text processing functionality for the application, supporting
    multiple AI operations with comprehensive validation, caching, resilience patterns, and monitoring.
    Each request is uniquely tracked for operational visibility and debugging, with integrated error
    handling and graceful degradation patterns ensuring reliable service operation under various
    system conditions.
    
    Args:
        request: Comprehensive text processing request containing input text, operation specification,
                optional configuration parameters, and operation-specific requirements such as questions
                for Q&A operations
        api_key: Validated API key for authentication and authorization, enabling secure access to AI
                processing capabilities and usage tracking for operational monitoring
        text_processor: Injected text processing service providing AI model integration, caching
                       capabilities, resilience patterns, and comprehensive error handling for all
                       supported text processing operations
    
    Returns:
        TextProcessingResponse: Comprehensive processing result containing:
                               - result: Processed output text from the specified AI operation
                               - operation: Echo of the operation performed for request verification
                               - metadata: Additional processing information including timing, caching status,
                                         and operational metrics for monitoring and optimization
    
    Raises:
        ValidationError: Request validation failures including missing required parameters (question for Q&A),
                        invalid operation specifications, malformed input data, or business rule violations
        InfrastructureError: AI service failures, cache system issues, or other infrastructure-related
                           problems that prevent successful request processing
        HTTPException: HTTP-specific errors with appropriate status codes:
                      - 400: Bad Request for validation failures
                      - 422: Unprocessable Entity for data validation errors  
                      - 500: Internal Server Error for unexpected system failures
                      - 502: Bad Gateway for AI service communication issues
                      - 503: Service Unavailable for temporary system unavailability
    
    Behavior:
        **Request Processing and Validation:**
        - Generates unique request ID for comprehensive request tracing and logging
        - Validates operation-specific requirements (question parameter for Q&A operations)
        - Applies comprehensive input validation and sanitization for security and reliability
        - Logs request initiation with operation type and authentication details for monitoring
        
        **AI Service Integration:**
        - Integrates with TextProcessorService for AI model access and processing capabilities
        - Applies caching strategies for performance optimization and cost reduction
        - Implements resilience patterns including circuit breakers and retry mechanisms
        - Provides graceful degradation when AI services experience temporary issues
        
        **Response Processing and Metadata:**
        - Generates comprehensive processing results with operation confirmation
        - Includes processing metadata for performance monitoring and optimization
        - Applies response validation and sanitization for security and quality assurance
        - Provides detailed logging for operational visibility and troubleshooting
        
        **Error Handling and Recovery:**
        - Implements comprehensive exception handling with structured error responses
        - Provides meaningful error messages for client application integration
        - Maintains detailed error logging for operational monitoring and debugging
        - Ensures graceful error handling without exposing sensitive system information
        
        **Security and Authentication:**
        - Requires valid API key authentication for all processing requests
        - Implements secure request processing with input sanitization and validation
        - Maintains audit trails for security monitoring and compliance requirements
        - Protects against common security vulnerabilities and attack patterns
    
    Examples:
        >>> # Basic text summarization request
        >>> request_data = {
        ...     "text": "Long article text that needs to be summarized...",
        ...     "operation": "summarize",
        ...     "options": {"max_length": 150}
        ... }
        >>> headers = {"Authorization": "Bearer api-key-12345"}
        >>> response = await client.post("/v1/text_processing/process", 
        ...                             json=request_data, headers=headers)
        >>> assert response.status_code == 200
        >>> result = response.json()
        >>> assert result["operation"] == "summarize"
        >>> assert "result" in result and len(result["result"]) > 0
        
        >>> # Sentiment analysis with metadata
        >>> request_data = {
        ...     "text": "I absolutely love this new feature! It's amazing.",
        ...     "operation": "sentiment"
        ... }
        >>> response = await client.post("/v1/text_processing/process", 
        ...                             json=request_data, headers=headers)
        >>> sentiment_result = response.json()
        >>> assert sentiment_result["operation"] == "sentiment"
        >>> assert "metadata" in sentiment_result
        
        >>> # Question-answering operation with required question parameter
        >>> qa_request = {
        ...     "text": "Python is a programming language created by Guido van Rossum.",
        ...     "operation": "qa",
        ...     "question": "Who created Python?"
        ... }
        >>> response = await client.post("/v1/text_processing/process",
        ...                             json=qa_request, headers=headers)
        >>> qa_result = response.json()
        >>> assert "Guido" in qa_result["result"]
        
        >>> # Error handling for missing required parameters
        >>> invalid_request = {
        ...     "text": "Some text here",
        ...     "operation": "qa"  # Missing required question parameter
        ... }
        >>> response = await client.post("/v1/text_processing/process",
        ...                             json=invalid_request, headers=headers)
        >>> assert response.status_code == 400
        >>> error = response.json()
        >>> assert "Question is required" in error["detail"]
        
        >>> # Key points extraction with custom options
        >>> key_points_request = {
        ...     "text": "Complex document with multiple important points...",
        ...     "operation": "key_points",
        ...     "options": {"max_points": 5}
        ... }
        >>> response = await client.post("/v1/text_processing/process",
        ...                             json=key_points_request, headers=headers)
        >>> key_points = response.json()
        >>> assert key_points["operation"] == "key_points"
        
        >>> # Comprehensive error handling and retry patterns
        >>> async def robust_text_processing(text, operation, max_retries=3):
        ...     for attempt in range(max_retries):
        ...         try:
        ...             response = await client.post("/v1/text_processing/process", 
        ...                                        json={"text": text, "operation": operation}, 
        ...                                        headers=headers)
        ...             if response.status_code == 200:
        ...                 return response.json()
        ...             elif response.status_code in [502, 503]:  # Temporary errors
        ...                 await asyncio.sleep(2 ** attempt)  # Exponential backoff
        ...                 continue
        ...             else:
        ...                 break  # Permanent error
        ...         except Exception as e:
        ...             if attempt == max_retries - 1:
        ...                 raise
        ...             await asyncio.sleep(2 ** attempt)
        ...     return None
    
    Note:
        This endpoint represents the core business functionality of the AI text processing service
        and implements comprehensive production-ready patterns including authentication, validation,
        caching, resilience, monitoring, and error handling. All requests are uniquely tracked for
        operational visibility and the endpoint maintains backward compatibility while supporting
        extensible operation definitions and configuration options.
    """
    ...


@router.post('/batch_process', response_model=BatchTextProcessingResponse, responses={400: {'model': ErrorResponse, 'description': 'Validation Error'}, 422: {'model': ErrorResponse, 'description': 'Validation Error'}, 500: {'model': ErrorResponse, 'description': 'Internal Server Error'}, 502: {'model': ErrorResponse, 'description': 'AI Service Error'}, 503: {'model': ErrorResponse, 'description': 'Service Unavailable'}})
async def batch_process_text(request: BatchTextProcessingRequest, api_key: str = Depends(verify_api_key), text_processor: TextProcessorService = Depends(get_text_processor)):
    """
    Process multiple text requests in a single batch operation.
    
    Efficiently processes multiple text requests simultaneously, with configurable
    batch limits and comprehensive error handling. Each batch is assigned a unique
    ID for tracking and logging. The operation is synchronous and returns results
    for all processed requests.
    
    Args:
        request (BatchTextProcessingRequest): The batch processing request containing:
            - requests (list[TextProcessingRequest]): List of individual text processing requests
            - batch_id (str, optional): Custom batch identifier, auto-generated if not provided
        api_key (str): Valid API key for authentication.
        text_processor (TextProcessorService): Injected text processing service.
    
    Returns:
        BatchTextProcessingResponse: Batch processing results containing:
            - batch_id (str): Unique identifier for this batch
            - total_requests (int): Total number of requests in the batch
            - completed (int): Number of successfully processed requests
            - failed (int): Number of failed requests
            - results (list[TextProcessingResponse]): Individual processing results
            - errors (list[dict], optional): Details of any processing errors
    
    Raises:
        ValidationError: If:
            - Batch request list is empty
            - Batch size exceeds maximum limit
            - Individual request validation fails
        BusinessLogicError: If batch processing business rules are violated
        InfrastructureError: If batch processing infrastructure fails
    
    Example:
        Request:
        ```json
        {
            "requests": [
                {
                    "text": "First document to analyze...",
                    "operation": "sentiment"
                },
                {
                    "text": "Second document to summarize...",
                    "operation": "summarize",
                    "options": {"max_length": 100}
                }
            ],
            "batch_id": "my-batch-2024"
        }
        ```
        
        Response:
        ```json
        {
            "batch_id": "my-batch-2024",
            "total_requests": 2,
            "completed": 2,
            "failed": 0,
            "results": [
                {
                    "result": "Positive sentiment detected",
                    "operation": "sentiment"
                },
                {
                    "result": "Brief summary of the document...",
                    "operation": "summarize"
                }
            ]
        }
        ```
    """
    ...


@router.get('/batch_status/{batch_id}', response_model=dict, responses={401: {'model': ErrorResponse, 'description': 'Authentication Error'}, 422: {'model': ErrorResponse, 'description': 'Validation Error'}})
async def get_batch_status(batch_id: str, api_key: str = Depends(verify_api_key)):
    """
    Get the status of a batch processing job.
    
    Returns the current status of a batch processing operation. Note that the current
    implementation processes batches synchronously, so this endpoint primarily serves
    as a status confirmation for completed batches.
    
    Args:
        batch_id (str): The unique identifier of the batch to check status for.
        api_key (str): Valid API key for authentication.
    
    Returns:
        dict: Batch status information containing:
            - batch_id (str): The requested batch identifier
            - status (str): Current status of the batch (typically "COMPLETED_SYNC")
            - message (str): Descriptive message about the batch status
    
    Note:
        This is a placeholder endpoint for the current synchronous implementation.
        In future versions with asynchronous batch processing, this will provide
        real-time status updates including progress percentages and partial results.
    
    Example:
        Request:
        ```
        GET /v1/text_processing/batch_status/my-batch-2024
        ```
        
        Response:
        ```json
        {
            "batch_id": "my-batch-2024",
            "status": "COMPLETED_SYNC",
            "message": "Batch processing is synchronous. If your request to /text_processing/batch_process completed, the results were returned then."
        }
        ```
    """
    ...


@router.get('/health', responses={401: {'model': ErrorResponse, 'description': 'Authentication Error'}, 500: {'model': ErrorResponse, 'description': 'Infrastructure Error'}})
async def get_service_health(api_key: str = Depends(optional_verify_api_key), text_processor: TextProcessorService = Depends(get_text_processor)):
    """
    Get comprehensive health status for the text processing service.
    
    Returns detailed health information for both the domain service layer and
    underlying resilience infrastructure components. This endpoint provides
    visibility into service availability, performance, and operational status.
    
    Args:
        api_key (str, optional): API key for authentication. Defaults to optional verification.
        text_processor (TextProcessorService): Injected text processing service.
    
    Returns:
        dict: Comprehensive health status containing:
            - overall_healthy (bool): Aggregated health status across all components
            - service_type (str): Type of service ("domain")
            - infrastructure (dict): Infrastructure-level health information:
                - resilience (dict): Resilience system health status
            - domain_services (dict): Domain service health information:
                - text_processing (dict): Text processing service specific health
    
    Raises:
        InfrastructureError: If health check fails
    
    Note:
        This is an example implementation demonstrating how to combine domain
        service health with infrastructure health monitoring. The endpoint
        supports optional authentication and provides detailed diagnostics.
    
    Example:
        Response:
        ```json
        {
            "overall_healthy": true,
            "service_type": "domain", 
            "infrastructure": {
                "resilience": {
                    "healthy": true,
                    "circuit_breakers": {"status": "closed"},
                    "rate_limiters": {"active": false}
                }
            },
            "domain_services": {
                "text_processing": {
                    "healthy": true,
                    "response_time_ms": 150,
                    "requests_processed": 1024
                }
            }
        }
        ```
    """
    ...
