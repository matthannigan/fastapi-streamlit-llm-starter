"""
REST API endpoints for text processing operations.

This module provides a comprehensive set of endpoints for AI-powered text processing
operations including summarization, sentiment analysis, key point extraction,
question generation, and Q&A functionality.

Endpoints:
    GET /text_processing/operations: 
        Retrieve available text processing operations and their configurations.
        
    POST /text_processing/process:
        Process a single text request using specified AI operations.
        
    POST /text_processing/batch_process:
        Process multiple text requests in a single batch operation.
        
    GET /text_processing/batch_status/{batch_id}:
        Check the status of a batch processing job (synchronous implementation).
        
    GET /text_processing/health:
        Get comprehensive health status for the text processing service,
        including domain service and underlying resilience infrastructure.

Authentication:
    Most endpoints require API key authentication via the Authorization header
    or api_key parameter. The /operations and /health endpoints support
    optional authentication.

Features:
    - Multiple AI processing operations (summarize, sentiment, key_points, etc.)
    - Batch processing with configurable limits
    - Comprehensive error handling and logging
    - Request tracing with unique IDs
    - Resilience infrastructure integration
    - Input validation and sanitization

Examples:
    Single text processing:
        POST /text_processing/process
        {
            "text": "Your text here",
            "operation": "summarize",
            "options": {"max_length": 150}
        }
        
    Batch processing:
        POST /text_processing/batch_process
        {
            "requests": [
                {"text": "Text 1", "operation": "sentiment"},
                {"text": "Text 2", "operation": "summarize"}
            ],
            "batch_id": "optional-batch-id"
        }
"""

import logging
import uuid
import time
from typing import Dict, Any, Optional

from fastapi import APIRouter, Depends, Query, HTTPException, status
from pydantic import BaseModel, Field

from shared.models import (
    TextProcessingRequest,
    TextProcessingResponse,
    BatchTextProcessingRequest,
    BatchTextProcessingResponse
)

from app.core.config import settings
from app.api.v1.deps import get_text_processor
from app.services.text_processor import TextProcessorService
from app.infrastructure.security import verify_api_key, optional_verify_api_key

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/text_processing", tags=["Text Processing"])

@router.get("/operations")
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


@router.post("/process", response_model=TextProcessingResponse)
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
            - operation (TextProcessingOperation): The type of operation to perform
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
        HTTPException: 400 Bad Request if:
            - Question is missing for Q&A operations
            - Request validation fails
        HTTPException: 401 Unauthorized if API key is invalid
        HTTPException: 500 Internal Server Error if processing fails
    
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
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Question is required for Q&A operation"
            )
        
        # Process the text
        result = await text_processor.process_text(request)
        
        logger.info(f"REQUEST_END - ID: {request_id}, Status: SUCCESS, Operation: {request.operation}")
        logger.info("Request processed successfully")
        return result
        
    except HTTPException:
        logger.info(f"REQUEST_END - ID: {request_id}, Status: HTTP_ERROR, Operation: {request.operation}")
        raise
    except ValueError as e:
        logger.warning(f"Validation error: {str(e)}")
        logger.info(f"REQUEST_END - ID: {request_id}, Status: VALIDATION_ERROR, Operation: {request.operation}")
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )
    except Exception as e:
        logger.error(f"Processing error: {str(e)}")
        logger.info(f"REQUEST_END - ID: {request_id}, Status: INTERNAL_ERROR, Operation: {request.operation}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process text"
        )


@router.post("/batch_process", response_model=BatchTextProcessingResponse)
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
        HTTPException: 400 Bad Request if:
            - Batch request list is empty
            - Batch size exceeds maximum limit (configured in settings)
            - Individual request validation fails
        HTTPException: 401 Unauthorized if API key is invalid
        HTTPException: 500 Internal Server Error if batch processing fails
    
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
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Batch request list cannot be empty."
            )
        
        if len(request.requests) > settings.MAX_BATCH_REQUESTS_PER_CALL:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Batch size exceeds maximum limit of {settings.MAX_BATCH_REQUESTS_PER_CALL} requests."
            )
            
        logger.info(f"Batch processing {len(request.requests)} requests for user (API key prefix): {api_key[:8]}..., batch_id: {request.batch_id or 'N/A'}")
        
        result = await text_processor.process_batch(request)
        
        logger.info(f"BATCH_REQUEST_END - ID: {request_id}, Batch ID: {result.batch_id}, Status: SUCCESS, Completed: {result.completed}/{result.total_requests}")
        logger.info(f"Batch (batch_id: {result.batch_id}) completed: {result.completed}/{result.total_requests} successful for user (API key prefix): {api_key[:8]}...")
        return result
        
    except HTTPException:
        logger.info(f"BATCH_REQUEST_END - ID: {request_id}, Batch ID: {batch_id}, Status: HTTP_ERROR")
        raise
    except Exception as e:
        logger.error(f"Batch processing error for user (API key prefix) {api_key[:8]}..., batch_id {request.batch_id or 'N/A'}: {str(e)}", exc_info=True)
        logger.info(f"BATCH_REQUEST_END - ID: {request_id}, Batch ID: {batch_id}, Status: INTERNAL_ERROR")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process batch request due to an internal server error."
        )


@router.get("/batch_status/{batch_id}", response_model=dict)
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
    
    Raises:
        HTTPException: 401 Unauthorized if API key is invalid
    
    Note:
        This is a placeholder endpoint for the current synchronous implementation.
        In future versions with asynchronous batch processing, this will provide
        real-time status updates including progress percentages and partial results.
    
    Example:
        Request:
        ```
        GET /text_processing/batch_status/my-batch-2024
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

@router.get("/health")
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
        HTTPException: 500 Internal Server Error if health check fails
    
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
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to get service health: {str(e)}"
        )
