# Product Requirements Document: Batch Processing Endpoint

## 1. Introduction

This document outlines the requirements for implementing a new batch processing endpoint within the FastAPI-Streamlit-LLM starter template. This feature aims to provide users with the ability to process multiple text inputs in a single API request, leveraging parallel processing for efficiency.

### 1.1 Purpose of this Document
The purpose of this PRD is to define the scope, goals, user stories, functional and non-functional requirements, and release criteria for the new batch processing functionality. It serves as a guide for development, testing, and stakeholders to ensure a common understanding of the feature.

### 1.2 Feature Overview and Scope
* **Feature:** Batch Processing Endpoint
* **Reasoning:** The `shared/models.py` already defines comprehensive models for batch processing (`BatchTextProcessingRequest`, `BatchTextProcessingResponse`, `BatchProcessingItem`), and `shared/examples.py` demonstrates their potential usage. However, the backend API (`backend/app/main.py`) doesn't currently have an endpoint to handle these batch requests. This feature addresses this gap.
* **Priority:** 🔥 **HIGH**
* **Estimated Effort:** 3-4 hours
* **Expected Impact:** Addresses a major functionality gap by enabling an existing, but unused, data model for batch operations. It will make the template significantly more versatile for users needing to process multiple texts efficiently.

**Scope of this Feature/Enhancement:**
* **In Scope:**
    * Implementation of a new POST endpoint `/batch_process` in `backend/app/main.py`.
    * Modification of `backend/app/services/text_processor.py` to include a `process_batch` method capable of handling multiple text processing requests, potentially in parallel.
    * Integration with existing shared Pydantic models (`BatchTextProcessingRequest`, `BatchTextProcessingResponse`, `BatchProcessingItem`, `ProcessingStatus`).
    * Integration with the existing authentication mechanism (`auth_service.verify_api_key`).
    * Implementation of a placeholder GET endpoint `/batch_status/{batch_id}` for future asynchronous capabilities, initially indicating synchronous processing.
    * Basic validation (e.g., maximum batch size).
    * Configuration options for batch size limit and concurrency.
* **Out of Scope (for this iteration):**
    * Changes to the Streamlit frontend UI to utilize this batch endpoint.
    * Full implementation of asynchronous batch processing and persistent status tracking (beyond the placeholder endpoint).
    * Advanced rate limiting based on the number of items within a batch.
    * Database persistence for batch job details and results.

### 1.3 Target Audience
* **Primary:** Developers using the FastAPI-Streamlit-LLM starter template to build AI-powered applications who need to process multiple text inputs efficiently.
* **Secondary:** Backend developers contributing to or maintaining the starter template.

## 2. Goals and Objectives

### 2.1 Business Goals
* Enhance the utility and completeness of the FastAPI-Streamlit-LLM starter template.
* Increase adoption of the template by providing a commonly required, high-demand feature.
* Improve the template's positioning as a "production-ready" solution.

### 2.2 User Goals
* To efficiently process multiple text inputs (e.g., documents, messages) in a single API call, reducing network latency and client-side complexity.
* To benefit from parallel processing of batch items for faster overall throughput.
* To receive clear, itemized status and results for each text processed within a batch.

## 3. User Stories

* **As a developer using the starter template, I want** to send multiple text processing requests in a single API call **so that** I can reduce network overhead and simplify my client-side logic.
* **As a developer, I want** the batch processing to be performed with concurrent execution of individual requests **so that** I can get the results for the entire batch more quickly.
* **As a developer, I want** to receive a consolidated response that clearly indicates the status (e.g., completed, failed) and result (or error message) for each individual item submitted in the batch **so that** I can effectively handle partial successes and failures.
* **As a developer, I want** the batch processing endpoint to be secured using the existing API key authentication **so that** only authorized users can access it.
* **As an administrator or developer deploying the template, I want** to be able to configure the maximum number of items allowed in a single batch request **so that** I can manage server load and prevent abuse.
* **As an administrator or developer deploying the template, I want** to be able to configure the maximum concurrency for AI calls during batch processing **so that** I can manage resource utilization and costs associated with AI model interactions.
* **As a developer, I want** a way to understand the processing status of a batch (even if initially synchronous) **so that** I can build workflows around batch submissions.

## 4. Functional Requirements

### FR1: New Batch Processing Endpoint
* The system shall expose a new POST endpoint at `/batch_process`.
* This endpoint will be located in `backend/app/main.py`.

### FR2: Request Handling
* The `/batch_process` endpoint shall accept a JSON request body conforming to the `shared.models.BatchTextProcessingRequest` Pydantic model.
* The `BatchTextProcessingRequest` includes a list of `TextProcessingRequest` items.

### FR3: Response Structure
* The `/batch_process` endpoint shall return a JSON response body conforming to the `shared.models.BatchTextProcessingResponse` Pydantic model.
* The response shall include:
    * `batch_id`: A unique identifier for the batch request.
    * `total_requests`: The total number of items submitted in the batch.
    * `completed`: The number of successfully processed items.
    * `failed`: The number of items that failed processing.
    * `results`: A list of `BatchProcessingItem` objects, each containing:
        * `request_index`: The original index of the item in the input request.
        * `status`: `ProcessingStatus.COMPLETED` or `ProcessingStatus.FAILED`.
        * `response`: The result of processing (if completed).
        * `error`: An error message (if failed).
    * `total_processing_time`: The total time taken to process the batch in seconds.

### FR4: Parallel Processing
* The `TextProcessorService.process_batch` method shall process the items in `BatchTextProcessingRequest.requests` concurrently to improve efficiency.
* A semaphore or similar mechanism shall be used to limit the maximum number of concurrent AI calls.

### FR5: Configurable Concurrency Limit
* The maximum number of concurrent AI calls during batch processing shall be configurable (e.g., via `backend/app/config.py` or environment variables).
* Default value: 5 concurrent AI calls (as per example code).

### FR6: Configurable Batch Size Limit
* The `/batch_process` endpoint shall enforce a maximum limit on the number of items (`requests`) in a single `BatchTextProcessingRequest`.
* This limit shall be configurable (e.g., via `backend/app/config.py` or environment variables).
* Default value: 50 requests (as per example code).
* If the batch size exceeds this limit, the endpoint shall return an HTTP 400 Bad Request error.

### FR7: Authentication
* The `/batch_process` endpoint shall be secured and require API key authentication, verified by the existing `auth_service.verify_api_key` dependency.

### FR8: Error Handling
* **Batch Level Errors:**
    * If `len(request.requests)` exceeds the configured maximum batch size, the API shall return an HTTP `400 Bad Request` status code with a descriptive error message.
    * Any other unexpected server-side errors during batch processing setup or orchestration (not individual item errors) shall result in an HTTP `500 Internal Server Error` with a generic error message.
* **Item Level Errors:**
    * If an individual item within the batch fails processing (e.g., an exception during an AI call), its corresponding `BatchProcessingItem` in the response shall have `status` set to `ProcessingStatus.FAILED` and include a descriptive error message in the `error` field.
    * Failures of individual items should not prevent other items in the batch from being processed.

### FR9: Logging
* The system shall log key events during batch processing:
    * Receipt of a batch request, including the number of items and user ID.
    * Completion of a batch request, including the number of successful and failed items, and total processing time.
    * Errors encountered during the processing of individual batch items.

### FR10: Placeholder Batch Status Endpoint
* A GET endpoint `/batch_status/{batch_id}` shall be implemented in `backend/app/main.py`.
* For this initial synchronous implementation, this endpoint will act as a placeholder.
* Upon receiving a `batch_id`, it shall return a JSON response indicating that the processing is synchronous (e.g., `{"batch_id": batch_id, "status": "completed", "message": "Synchronous processing only"}`).
* This endpoint also requires API key authentication.

## 5. Non-Functional Requirements

### NFR1: Performance
* The batch processing should be significantly faster than making individual API calls for each item, due to reduced network overhead and parallel processing of AI tasks.
* The system should efficiently manage concurrent operations to avoid overwhelming downstream AI services or internal resources. The concurrency limit (FR5) contributes to this.
* Response times for the `/batch_process` endpoint will depend on the number of items, the complexity of each item's processing, and the performance of the underlying LLM, but should be optimized by the parallel execution.

### NFR2: Security
* The endpoint must be protected by the existing API key authentication mechanism (`UserContext = Depends(auth_service.verify_api_key)`).
* Input validation must be performed on the batch request, particularly for batch size.

### NFR3: Usability (API)
* The API contract (request/response models, endpoint path) must be clear, intuitive, and well-documented.
* Error messages returned by the API (both for batch-level and item-level errors) should be informative and help the user diagnose issues.

### NFR4: Scalability
* While individual batch processing occurs within a single service call, the overall FastAPI application is designed for horizontal scaling. The batch endpoint should function correctly in a multi-instance deployment.
* The concurrency limit helps manage resource use per instance.

### NFR5: Configurability
* Key parameters such as maximum batch size and internal concurrency limits for AI calls must be configurable by the deployer of the application without code changes (e.g., through environment variables or configuration files).

### NFR6: Reliability
* The system must gracefully handle errors occurring in individual items within a batch without causing the entire batch request to fail catastrophically.
* The service should remain stable under valid load conditions.

## 6. User Interface (UI) and User Experience (UX) Considerations

* **Backend API Focus:** This feature is primarily an enhancement to the backend API. No direct changes to the existing Streamlit frontend UI are included in the scope of this PRD.
* **API UX:**
    * Endpoint naming (`/batch_process`, `/batch_status/{batch_id}`) should be clear and RESTful.
    * Request and response schemas (`BatchTextProcessingRequest`, `BatchTextProcessingResponse`) are based on pre-defined Pydantic models, ensuring consistency.
    * Error messages should be structured (JSON) and informative.
* **Future Frontend Integration (Out of Scope for this PRD):** The Streamlit frontend could be enhanced in the future to:
    * Provide a UI for users to upload or input multiple text items for batch processing.
    * Display the progress and results of batch processing jobs by calling this new backend endpoint.

## 7. Code Examples

The following code snippets illustrate the proposed implementation for the service layer and the API endpoint.

### 7.1 Update Text Processor for Batch Operations
```python
# backend/app/services/text_processor.py (additions)
import asyncio
import time
from fastapi.logger import logger # Assuming logger is configured
from shared.models import BatchTextProcessingRequest, BatchTextProcessingResponse, BatchProcessingItem, ProcessingStatus, TextProcessingRequest # Added TextProcessingRequest

class TextProcessorService:
    # ... existing code ...
    
    async def process_batch(self, batch_request: BatchTextProcessingRequest) -> BatchTextProcessingResponse:
        """Process multiple text requests in parallel."""
        start_time = time.time()
        total_requests = len(batch_request.requests)
        
        logger.info(f"Processing batch of {total_requests} requests for batch_id: {batch_request.batch_id or 'N/A'}")
        
        # Process requests in parallel with concurrency limit
        # This should be configurable, e.g., from app config
        semaphore = asyncio.Semaphore(5)  # Max 5 concurrent AI calls 
        tasks = []
        
        async def process_single_request(index: int, request: TextProcessingRequest) -> BatchProcessingItem:
            async with semaphore:
                try:
                    # Assuming self.process_text is the existing method for single text processing
                    response = await self.process_text(request) 
                    return BatchProcessingItem(
                        request_index=index,
                        status=ProcessingStatus.COMPLETED,
                        response=response
                    )
                except Exception as e:
                    logger.error(f"Batch item {index} (batch_id: {batch_request.batch_id or 'N/A'}) failed: {str(e)}")
                    return BatchProcessingItem(
                        request_index=index,
                        status=ProcessingStatus.FAILED,
                        error=str(e)
                    )
        
        # Create tasks for all requests
        for i, request_item in enumerate(batch_request.requests):
            task = process_single_request(i, request_item)
            tasks.append(task)
        
        # Execute all tasks
        results = await asyncio.gather(*tasks, return_exceptions=False) # Errors are handled within process_single_request
        
        # Calculate statistics
        completed_count = sum(1 for r in results if r.status == ProcessingStatus.COMPLETED)
        failed_count = sum(1 for r in results if r.status == ProcessingStatus.FAILED)
        total_time = time.time() - start_time
        
        logger.info(f"Batch (batch_id: {batch_request.batch_id or 'N/A'}) completed. Successful: {completed_count}/{total_requests}. Time: {total_time:.2f}s")

        return BatchTextProcessingResponse(
            batch_id=batch_request.batch_id or f"batch_{int(time.time())}",
            total_requests=total_requests,
            completed=completed_count,
            failed=failed_count,
            results=results,
            total_processing_time=total_time
        )

    # Placeholder for the single text processing method, adapt as per actual implementation
    async def process_text(self, request: TextProcessingRequest):
        # This is the method that interacts with the LLM for a single item.
        # Its implementation is outside the scope of this specific batching PRD,
        # but it's called by process_single_request.
        # Example:
        # await asyncio.sleep(0.1) # Simulate AI call
        # return {"processed_text": f"Processed: {request.text[:10]}..."}
        raise NotImplementedError("process_text method needs to be implemented or connected")

```

### 7.2 Add Batch Endpoint in FastAPI
```python
# backend/app/main.py (additions)
from fastapi import FastAPI, Depends, HTTPException, status
from fastapi.logger import logger # Assuming logger is configured
from shared.models import BatchTextProcessingRequest, BatchTextProcessingResponse, UserContext # Assuming UserContext from your auth
# Assuming text_processor service and auth_service are initialized, e.g.:
# from .services.text_processor import TextProcessorService
# from .services.auth import AuthService
# text_processor = TextProcessorService()
# auth_service = AuthService()

# app = FastAPI() # Existing app instance

MAX_BATCH_REQUESTS = 50 # This should be configurable

@app.post("/batch_process", response_model=BatchTextProcessingResponse)
async def batch_process_text(
    request: BatchTextProcessingRequest,
    user: UserContext = Depends(auth_service.verify_api_key) # Assuming auth_service and UserContext
):
    """Process multiple text requests in batch."""
    try:
        if len(request.requests) == 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Batch request list cannot be empty."
            )
        if len(request.requests) > MAX_BATCH_REQUESTS:  # Use configurable limit
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Batch size exceeds maximum limit of {MAX_BATCH_REQUESTS} requests."
            )
        
        logger.info(f"Batch processing {len(request.requests)} requests for user: {user.user_id}, batch_id: {request.batch_id or 'N/A'}") # Assuming user_id in UserContext
        
        # Ensure text_processor is available, e.g., via dependency injection or global instance
        result = await text_processor.process_batch(request)
        
        logger.info(f"Batch (batch_id: {result.batch_id}) completed: {result.completed}/{result.total_requests} successful for user: {user.user_id}")
        return result
        
    except HTTPException:
        raise # Re-raise HTTPException to let FastAPI handle it
    except Exception as e:
        logger.error(f"Batch processing error for user {user.user_id}, batch_id {request.batch_id or 'N/A'}: {str(e)}", exc_info=True)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to process batch request due to an internal server error."
        )

@app.get("/batch_status/{batch_id}", response_model=dict) # Define a response model if desired
async def get_batch_status(
    batch_id: str,
    user: UserContext = Depends(auth_service.verify_api_key) # Assuming auth_service and UserContext
):
    """
    Get status of a batch processing job.
    For the current synchronous implementation, this is a placeholder.
    """
    logger.info(f"Batch status requested for batch_id: {batch_id} by user: {user.user_id}")
    # In a synchronous model, if the request to /batch_process has returned, the job is "done".
    # This endpoint doesn't store state, so it can't confirm if a batch_id was ever valid.
    # For future async, this would query a database or cache.
    return {"batch_id": batch_id, "status": "COMPLETED_SYNC", "message": "Batch processing is synchronous. If your request to /batch_process completed, the results were returned then."}
```
*(Note: Assumed logger, `text_processor` service, `auth_service`, and `UserContext` are appropriately initialized and available in `main.py` and `text_processor.py`.)*

## 8. Release Criteria

For this feature to be considered ready for release, the following conditions must be met:

* All functional requirements (FR1-FR10) are implemented as specified.
* The `TextProcessorService.process_batch` method correctly processes items in parallel, respecting the concurrency limit.
* The `/batch_process` endpoint correctly handles requests and responses according to the defined Pydantic models.
* Batch size limits (FR6) and concurrency limits (FR5) are configurable and function as expected.
* Authentication (FR7) is enforced on both `/batch_process` and `/batch_status/{batch_id}` endpoints.
* Comprehensive error handling (FR8) is in place for both batch-level and item-level failures.
* Logging (FR9) is implemented for key batch processing events.
* The placeholder `/batch_status/{batch_id}` endpoint (FR10) is implemented.
* Unit tests are written and pass for the new service logic in `TextProcessorService` (e.g., batching logic, error handling for items, concurrency (mocked)) and for the FastAPI endpoints in `main.py` (e.g., request validation, auth, successful processing, error responses).
* End-to-end testing confirms the batch processing flow with valid and invalid inputs.
* API documentation (e.g., Swagger/OpenAPI docs generated by FastAPI) is updated to include the new endpoints, request/response models, and authentication requirements.
* Code has been peer-reviewed and merged into the target branch.
* Configuration options for batch size and concurrency are documented for users/deployers.

## 9. Open Issues and Future Considerations

### 9.1 Open Issues
* **Configuration Mechanism:**
    * The exact mechanism for configuring the `MAX_BATCH_REQUESTS` limit (currently 50 in example) needs to be finalized and implemented (e.g., environment variable `MAX_BATCH_REQUESTS_PER_CALL`, entry in `backend/app/config.py`).
    * The exact mechanism for configuring the `SEMAPHORE_CONCURRENCY_LIMIT` for AI calls (currently 5 in example) needs to be finalized and implemented (e.g., environment variable `BATCH_AI_CONCURRENCY_LIMIT`, entry in `backend/app/config.py`).
* **`process_text` method:** The provided code for `TextProcessorService` assumes an existing `async def process_text(self, request: TextProcessingRequest)` method. Ensure this method is correctly defined and integrated for single item processing within the batch logic.

### 9.2 Future Considerations
* **True Asynchronous Batch Processing:** Implement a fully asynchronous batch processing system. This would involve:
    * The `/batch_process` endpoint immediately returning a `202 Accepted` response with a `batch_id`.
    * Processing occurring in a background task (e.g., using Celery, ARQ, or FastAPI's `BackgroundTasks`).
    * Persisting batch job status and results to a database or distributed cache.
    * The `/batch_status/{batch_id}` endpoint querying this persistent storage to provide real-time status updates (e.g., PENDING, IN_PROGRESS, COMPLETED, FAILED) and final results.
* **Streamlit UI Integration:** Develop UI components within the Streamlit frontend to allow users to:
    * Submit multiple text inputs for batch processing via the new API endpoint.
    * Track the status of their batch jobs.
    * View and download the results of completed batch jobs.
* **Webhook/Callback Notifications:** For asynchronous batch processing, add support for user-provided webhook URLs to be called upon completion or failure of a batch job.
* **Advanced Rate Limiting:** Implement more granular rate limiting, potentially based on the total number of individual items processed across batches over a time window, rather than just per batch request.
* **Partial Results for Long Batches (Async):** In an async model, consider allowing retrieval of partial results for batches that are still in progress.
* **Retry Mechanisms:** Implement configurable retry mechanisms for individual items within a batch that may fail due to transient errors.
