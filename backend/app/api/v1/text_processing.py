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

from app.config import settings
from app.api.v1.deps import get_text_processor
from app.services.text_processor import TextProcessorService
from app.infrastructure.security import verify_api_key, optional_verify_api_key

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/text_processing", tags=["text_processing"])

@router.get("/operations")
async def get_operations(api_key: str = Depends(optional_verify_api_key)):
    """Get available processing operations."""
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
    """Process text using AI models."""
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
    """Process multiple text requests in batch."""
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
    """Get status of a batch processing job. Placeholder for synchronous implementation."""
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
    """
    Domain Service: Text Processing Health Check
    
    📚 EXAMPLE IMPLEMENTATION - Includes domain + infrastructure status
    Returns comprehensive health including underlying resilience infrastructure.
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
