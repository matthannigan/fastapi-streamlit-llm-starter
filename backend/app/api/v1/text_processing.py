"""Domain Service: AI Text Processing REST API

📚 **EXAMPLE IMPLEMENTATION** - Replace in your project  
💡 **Demonstrates infrastructure usage patterns**  
🔄 **Expected to be modified/replaced**

This module provides comprehensive REST API endpoints for AI-powered text processing
operations, demonstrating how to build domain services that leverage infrastructure
services for AI processing, caching, resilience, and security. It serves as a complete
example for implementing AI-powered domain APIs with proper error handling,
authentication, and monitoring.

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

from app.schemas import (
    ErrorResponse,
    TextProcessingRequest,
    TextProcessingResponse,
    BatchTextProcessingRequest,
    BatchTextProcessingResponse
)

from app.core.config import settings
from app.core.exceptions import (
    ValidationError,
    BusinessLogicError,
    InfrastructureError
)
from app.api.v1.deps import get_text_processor
from app.services.text_processor import TextProcessorService
from app.infrastructure.security import verify_api_key, optional_verify_api_key

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/text_processing", tags=["Text Processing"])

@router.get("/operations",
            responses={
                401: {"model": ErrorResponse, "description": "Authentication Error"},
            })
async def get_operations(api_key: str = Depends(optional_verify_api_key)):
    """Get available text processing operations and their configurations.
    
    Retrieves a comprehensive list of all supported AI text processing operations,
    including their descriptions, supported options, and special requirements.
    This endpoint supports optional authentication.
    
    Args:
        api_key (str, optional): API key for authentication. Defaults to optional verification.
    
    Returns:
        dict: A dictionary containing:
            - operations (list): List of operation objects, each containing:
                - id (str): Unique operation identifier
                - name (str): Human-readable operation name
                - description (str): Detailed operation description
                - options (list): List of supported configuration options
                - requires_question (bool, optional): Whether operation requires a question parameter
    
    Example:
        Response format:
        ```json
        {
            "operations": [
                {
                    "id": "summarize",
                    "name": "Summarize", 
                    "description": "Generate a concise summary of the text",
                    "options": ["max_length"]
                },
                {
                    "id": "qa",
                    "name": "Question & Answer",
                    "description": "Answer a specific question about the text",
                    "options": [],
                    "requires_question": true
                }
            ]
        }
        ```
    """
    return {
        "operations": [
            {
                "id": "summarize",
                "name": "Summarize",
                "description": "Generate a concise summary of the text",
                "options": ["max_length"]
            },
            {
                "id": "sentiment",
                "name": "Sentiment Analysis",
                "description": "Analyze the emotional tone of the text",
                "options": []
            },
            {
                "id": "key_points",
                "name": "Key Points",
                "description": "Extract the main points from the text",
                "options": ["max_points"]
            },
            {
                "id": "questions",
                "name": "Generate Questions",
                "description": "Create questions about the text content",
                "options": ["num_questions"]
            },
            {
                "id": "qa",
                "name": "Question & Answer",
                "description": "Answer a specific question about the text",
                "options": [],
                "requires_question": True
            }
        ]
    }


@router.post("/process", 
             response_model=TextProcessingResponse,
             responses={
                 400: {"model": ErrorResponse, "description": "Validation Error"},
                 422: {"model": ErrorResponse, "description": "Validation Error"},
                 500: {"model": ErrorResponse, "description": "Internal Server Error"},
                 502: {"model": ErrorResponse, "description": "AI Service Error"},
                 503: {"model": ErrorResponse, "description": "Service Unavailable"}
             })
async def process_text(
    request: TextProcessingRequest,
    api_key: str = Depends(verify_api_key),
    text_processor: TextProcessorService = Depends(get_text_processor)
):
    """Process a single text request using specified AI operations.
    
    Performs AI-powered text processing operations such as summarization, sentiment analysis,
    key point extraction, question generation, or question answering. Each request is assigned
    a unique ID for tracing and logging purposes.
    
    Args:
        request (TextProcessingRequest): The text processing request containing:
            - text (str): The input text to be processed
            - operation (TextTextProcessingOperation): The type of operation to perform
            - options (dict, optional): Additional options for the operation
            - question (str, optional): Required for Q&A operations
        api_key (str): Valid API key for authentication.
        text_processor (TextProcessorService): Injected text processing service.
    
    Returns:
        TextProcessingResponse: Processing result containing:
            - result (str): The processed output text
            - operation (str): The operation that was performed
            - metadata (dict, optional): Additional information about the processing
    
    Raises:
        ValidationError: If:
            - Question is missing for Q&A operations
            - Request validation fails
            - Input data is invalid
        BusinessLogicError: If text processing business rules are violated
        InfrastructureError: If underlying services fail
    
    Example:
        Request:
        ```json
        {
            "text": "The quick brown fox jumps over the lazy dog...",
            "operation": "summarize",
            "options": {"max_length": 50}
        }
        ```
        
        Response:
        ```json
        {
            "result": "A brief summary of the text...",
            "operation": "summarize",
            "metadata": {"processing_time": 1.23}
        }
        ```
    """
    # Generate unique request ID for tracing
    request_id = str(uuid.uuid4())
    
    logger.info(f"REQUEST_START - ID: {request_id}, Operation: {request.operation}, API Key: {api_key[:8]}...")
    
    try:
        logger.info(f"Received request for operation: {request.operation}")
        
        # Validate Q&A request
        if request.operation.value == "qa" and not request.question:
            raise ValidationError(
                "Question is required for Q&A operation",
                context={"operation": request.operation.value, "request_id": request_id}
            )
        
        # Process the text
        result = await text_processor.process_text(request)
        
        logger.info(f"REQUEST_END - ID: {request_id}, Status: SUCCESS, Operation: {request.operation}")
        logger.info("Request processed successfully")
        return result
        
    except (ValidationError, BusinessLogicError, InfrastructureError):
        # Re-raise custom exceptions - they'll be handled by the global exception handler
        logger.info(f"REQUEST_END - ID: {request_id}, Status: ERROR, Operation: {request.operation}")
        raise
    except ValueError as e:
        # Convert ValueError to ValidationError for consistent handling
        logger.warning(f"Validation error: {str(e)}")
        logger.info(f"REQUEST_END - ID: {request_id}, Status: VALIDATION_ERROR, Operation: {request.operation}")
        raise ValidationError(
            str(e),
            context={"operation": request.operation.value, "request_id": request_id}
        )
    except Exception as e:
        # Convert unexpected exceptions to InfrastructureError
        logger.error(f"Processing error: {str(e)}")
        logger.info(f"REQUEST_END - ID: {request_id}, Status: INTERNAL_ERROR, Operation: {request.operation}")
        raise InfrastructureError(
            "Failed to process text",
            context={"operation": request.operation.value, "request_id": request_id, "error": str(e)}
        )


@router.post("/batch_process", 
             response_model=BatchTextProcessingResponse,
             responses={
                 400: {"model": ErrorResponse, "description": "Validation Error"},
                 422: {"model": ErrorResponse, "description": "Validation Error"},
                 500: {"model": ErrorResponse, "description": "Internal Server Error"},
                 502: {"model": ErrorResponse, "description": "AI Service Error"},
                 503: {"model": ErrorResponse, "description": "Service Unavailable"}
             })
async def batch_process_text(
    request: BatchTextProcessingRequest,
    api_key: str = Depends(verify_api_key),
    text_processor: TextProcessorService = Depends(get_text_processor)
):
    """Process multiple text requests in a single batch operation.
    
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
    # Generate unique request ID for tracing
    request_id = str(uuid.uuid4())
    batch_id = request.batch_id or f"batch_{int(time.time())}"
    
    logger.info(f"BATCH_REQUEST_START - ID: {request_id}, Batch ID: {batch_id}, Count: {len(request.requests)}, API Key: {api_key[:8]}...")
    
    try:
        if not request.requests:
            raise ValidationError(
                "Batch request list cannot be empty",
                context={"batch_id": batch_id, "request_id": request_id}
            )
        
        if len(request.requests) > settings.MAX_BATCH_REQUESTS_PER_CALL:
            raise ValidationError(
                f"Batch size exceeds maximum limit of {settings.MAX_BATCH_REQUESTS_PER_CALL} requests",
                context={
                    "batch_id": batch_id, 
                    "request_id": request_id, 
                    "requested_size": len(request.requests),
                    "max_allowed": settings.MAX_BATCH_REQUESTS_PER_CALL
                }
            )
            
        logger.info(f"Batch processing {len(request.requests)} requests for user (API key prefix): {api_key[:8]}..., batch_id: {request.batch_id or 'N/A'}")
        
        result = await text_processor.process_batch(request)
        
        logger.info(f"BATCH_REQUEST_END - ID: {request_id}, Batch ID: {result.batch_id}, Status: SUCCESS, Completed: {result.completed}/{result.total_requests}")
        logger.info(f"Batch (batch_id: {result.batch_id}) completed: {result.completed}/{result.total_requests} successful for user (API key prefix): {api_key[:8]}...")
        return result
        
    except (ValidationError, BusinessLogicError, InfrastructureError):
        # Re-raise custom exceptions - they'll be handled by the global exception handler
        logger.info(f"BATCH_REQUEST_END - ID: {request_id}, Batch ID: {batch_id}, Status: ERROR")
        raise
    except Exception as e:
        # Convert unexpected exceptions to InfrastructureError
        logger.error(f"Batch processing error for user (API key prefix) {api_key[:8]}..., batch_id {request.batch_id or 'N/A'}: {str(e)}", exc_info=True)
        logger.info(f"BATCH_REQUEST_END - ID: {request_id}, Batch ID: {batch_id}, Status: INTERNAL_ERROR")
        raise InfrastructureError(
            "Failed to process batch request due to an internal server error",
            context={
                "batch_id": batch_id,
                "request_id": request_id,
                "request_count": len(request.requests),
                "error": str(e)
            }
        )


@router.get("/batch_status/{batch_id}", 
            response_model=dict,
            responses={
                401: {"model": ErrorResponse, "description": "Authentication Error"},
                422: {"model": ErrorResponse, "description": "Validation Error"},
            })
async def get_batch_status(batch_id: str, api_key: str = Depends(verify_api_key)):
    """Get the status of a batch processing job.
    
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
    logger.info(f"Batch status requested for batch_id: {batch_id} by user (API key prefix): {api_key[:8]}...")
    return {
        "batch_id": batch_id,
        "status": "COMPLETED_SYNC",
        "message": "Batch processing is synchronous. If your request to /text_processing/batch_process completed, the results were returned then."
    }

@router.get("/health",
            responses={
                401: {"model": ErrorResponse, "description": "Authentication Error"},
                500: {"model": ErrorResponse, "description": "Infrastructure Error"},
            })
async def get_service_health(
    api_key: str = Depends(optional_verify_api_key),
    text_processor: TextProcessorService = Depends(get_text_processor)
):
    """Get comprehensive health status for the text processing service.
    
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
    try:
        # Get infrastructure health (without dependency)
        from app.infrastructure.resilience.orchestrator import ai_resilience
        resilience_health = ai_resilience.get_health_status()
        
        # Get domain service health
        service_health = text_processor.get_resilience_health()
        
        overall_healthy = resilience_health["healthy"] and service_health.get("healthy", True)
        
        return {
            "overall_healthy": overall_healthy,
            "service_type": "domain",
            "infrastructure": {
                "resilience": resilience_health
            },
            "domain_services": {
                "text_processing": service_health
            }
        }
    except Exception as e:
        # Convert health check failures to InfrastructureError
        raise InfrastructureError(
            f"Failed to get service health: {str(e)}",
            context={"endpoint": "/v1/health", "error": str(e)}
        )
