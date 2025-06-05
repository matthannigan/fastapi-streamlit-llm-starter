# Continue work on task 6
_Exported on 6/2/2025 at 14:24:20 EDT from Cursor (0.50.7)_

---

**User**

Continue work on Task 6: Remove Global `ai_cache` Instance

---

**Cursor**

I'll help you continue work on Task 6. Let me first get the details of this task to understand what needs to be done.

Now let me check the current state of the cache.py file to see what needs to be done:

I can see that the cache.py file currently does not have a global `ai_cache` instance. It seems this task may have already been completed or the global instance was removed. Let me search for any remaining references to `ai_cache` in the codebase to make sure:

Now let me check the actual Python source files to see if there are any current imports or usages of a global `ai_cache`:

Let me also check for any direct `ai_cache =` assignments in Python files:

Let me check for any usage of `ai_cache` in Python files:

Now I can see the issue! There are still references to `app.services.text_processor.ai_cache` in the test files. Let me check the text_processor.py file to see the current state:

I can see that the `text_processor.py` file has been updated properly and no longer imports or uses a global `ai_cache`. It now uses dependency injection with the `cache_service` parameter in the constructor. However, there are test files that still reference the old global `ai_cache`. Let me check the test files:

I can see the issue. The test files still have mocks that reference `app.services.text_processor.ai_cache`, but since the text processor no longer has a global `ai_cache`, these mocks are invalid. However, looking at the current task, it only asks to remove the global `ai_cache` instance from `cache.py`, and I can see that the global instance is already removed from that file.

Let me also check if there's any remaining assignment at the end of the cache.py file that might not have been visible:

Perfect! I can confirm that:

1. **The global `ai_cache = AIResponseCache()` instance has already been removed** from `backend/app/services/cache.py` - the file only contains the `AIResponseCache` class definition without any global instance.

2. **The text processor service has been updated** to use dependency injection and no longer imports or uses a global `ai_cache`.

3. **The task's main requirement is already complete** - there is no global `ai_cache` instance in the cache.py file.

However, as per the task's test strategy, I should run a final verification to ensure the application still runs and there are no direct usages of the global `ai_cache`. Let me run the verification:

Great! No global `ai_cache` assignments or imports were found in the backend Python files. Now let me test if the application still runs properly:

Ah! I found an issue. It looks like there's still a global instantiation of `text_processor` at the end of the `text_processor.py` file that's trying to create the service without providing the required `cache_service` argument. Let me check the end of that file:

Perfect! I found the issue. There's still a global instantiation of the text processor service at the end of the file (line 486) that's trying to create `TextProcessorService()` without providing the required `cache_service` argument. This is exactly the kind of issue that Task 6 is meant to address.

Let me remove this global instantiation:

```python
# Global service instance
text_processor = TextProcessorService()
```

Let me try removing those specific lines:

```python
# ... existing code ...

    def get_resilience_metrics(self) -> Dict[str, Any]:
        """Get resilience metrics for this service."""
        return ai_resilience.get_all_metrics()


# Global service instance
text_processor = TextProcessorService()
```

Let me try a different approach by reading the specific lines and then removing them:

```python
    def get_resilience_metrics(self) -> Dict[str, Any]:
        """Get resilience metrics for this service."""
        return ai_resilience.get_all_metrics()

```

Excellent! Now let me test if the text processor can be imported and instantiated properly:

Perfect! Now let me do a final verification to ensure there are no remaining global `ai_cache` references:

Let me also run a quick application startup test to make sure everything works:

Ah! Now I see there's another issue. The `main.py` file is trying to import the global `text_processor` instance that we just removed. This is actually part of the larger dependency injection work. Let me check what Task 5 was supposed to accomplish and see if this import should have been updated:

Let me check the dependencies.py file to see if `get_cache_service` was implemented and then check main.py to see what needs to be updated:

Great! I can see that Task 5 was completed and both `get_cache_service` and `get_text_processor_service` are implemented. Now let me check what the main.py file looks like and see if it needs updating:

I can see the issue! The main.py file is still importing `text_processor` as a global instance on line 19. This should be updated to use dependency injection. Let me fix this:

```python
from app.config import settings
from app.services.text_processor import text_processor
from app.auth import verify_api_key, optional_verify_api_key
from app.dependencies import get_cache_service
from app.services.cache import AIResponseCache
```

Let me fix the import and function signature:

```python
from app.config import settings
from app.services.text_processor import text_processor
from app.auth import verify_api_key, optional_verify_api_key
from app.dependencies import get_cache_service
from app.services.cache import AIResponseCache
from app.resilience_endpoints import resilience_router
```

Let me fix this more precisely:

```python
from app.config import settings
from app.services.text_processor import text_processor
from app.auth import verify_api_key, optional_verify_api_key
from app.dependencies import get_cache_service
```

Let me try a different approach by editing the specific line:

```python
from app.services.text_processor import text_processor
```

Let me try to replace the import line:

```python
from app.config import settings
from app.services.text_processor import TextProcessorService
from app.auth import verify_api_key, optional_verify_api_key
from app.dependencies import get_cache_service, get_text_processor_service
from app.services.cache import AIResponseCache
from app.resilience_endpoints import resilience_router
```

Great! Now I need to update the endpoints that use the global `text_processor` to use dependency injection instead. Let me find and update those:

I can see that there are two places where `text_processor` is used: in the `/process` endpoint (line 139) and in the `/batch_process` endpoint (line 210). Let me update both to use dependency injection:

```python
@app.post("/process", response_model=TextProcessingResponse)
async def process_text(
    request: TextProcessingRequest,
    api_key: str = Depends(verify_api_key)
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
```

Let me try a more targeted approach:

```python
@app.post("/process", response_model=TextProcessingResponse)
async def process_text(
    request: TextProcessingRequest,
    api_key: str = Depends(verify_api_key),
    text_processor: TextProcessorService = Depends(get_text_processor_service)
):
```

Great! Now let me update the batch_process endpoint as well:

```python
@app.post("/batch_process", response_model=BatchTextProcessingResponse)
async def batch_process_text(
    request: BatchTextProcessingRequest,
    api_key: str = Depends(verify_api_key)
):
```

Let me try a more specific approach:

```python
async def batch_process_text(
    request: BatchTextProcessingRequest,
    api_key: str = Depends(verify_api_key)
):
```

Let me find the exact line and update it:

Now I can see the batch_process_text function. Let me update it:

```python
@app.post("/batch_process", response_model=BatchTextProcessingResponse)
async def batch_process_text(
    request: BatchTextProcessingRequest,
    api_key: str = Depends(verify_api_key)
):
```

Let me try a different approach by targeting the specific function parameters:

```python
async def batch_process_text(
    request: BatchTextProcessingRequest,
    api_key: str = Depends(verify_api_key)
):
```

Let me try to update the function signature more specifically:

```python
async def batch_process_text(
    request: BatchTextProcessingRequest,
    api_key: str = Depends(verify_api_key),
    text_processor: TextProcessorService = Depends(get_text_processor_service)
):
```

Perfect! Now let me test if the application can be imported successfully:

There's another file that imports the global `text_processor`! Let me check the resilience_endpoints.py file:

I can see that the resilience_endpoints.py file also imports the global `text_processor` on line 10. Let me update this file to use dependency injection as well:

```python
from app.auth import verify_api_key, optional_verify_api_key
from app.services.resilience import ai_resilience
from app.services.text_processor import text_processor
```

Let me try a more specific approach:

```python
from app.services.text_processor import text_processor
```

Let me try updating the imports section:

```python
from app.auth import verify_api_key, optional_verify_api_key
from app.services.resilience import ai_resilience
from app.services.text_processor import text_processor

# Create a router for resilience endpoints
resilience_router = APIRouter(prefix="/resilience", tags=["resilience"])
```

Let me try a different approach by updating the imports and the function that uses text_processor:

```python
from app.auth import verify_api_key, optional_verify_api_key
from app.services.resilience import ai_resilience
from app.services.text_processor import TextProcessorService
from app.dependencies import get_text_processor_service
```

Let me try to replace the specific import line:

```python
from app.services.resilience import ai_resilience
from app.services.text_processor import text_processor

# Create a router for resilience endpoints
```

Let me try a more targeted approach by editing the specific lines:

```python
from app.services.resilience import ai_resilience
from app.services.text_processor import TextProcessorService
from app.dependencies import get_text_processor_service
```

I see that the edit model automatically updated the usages of `text_processor` as well. However, there's an issue - `get_text_processor_service()` is a dependency provider that should be used with FastAPI's dependency injection system, not called directly. Let me fix this by updating the endpoints to use proper dependency injection:

I need to update the functions that use the text processor to use dependency injection. Let me fix the `get_resilience_health` function:

```python
@resilience_router.get("/health")
async def get_resilience_health(
    api_key: str = Depends(optional_verify_api_key),
    text_processor: TextProcessorService = Depends(get_text_processor_service)
):
    """
    Get the health status of the resilience service.
    
    Returns information about circuit breaker states and overall health.
    """
    try:
        health_status = ai_resilience.get_health_status()
        return {
            "resilience_health": health_status,
            "service_health": get_text_processor_service().get_resilience_health(),
            "overall_healthy": health_status["healthy"]
        }
```

Now I need to update the function body to use the injected text_processor instead of calling the dependency provider directly:

```python
        return {
            "resilience_health": health_status,
            "service_health": get_text_processor_service().get_resilience_health(),
            "overall_healthy": health_status["healthy"]
        }
```

Let me try a more specific approach:

```python
            "service_health": get_text_processor_service().get_resilience_health(),
```

Let me try updating the entire return statement:

```python
        health_status = ai_resilience.get_health_status()
        return {
            "resilience_health": health_status,
            "service_health": get_text_processor_service().get_resilience_health(),
            "overall_healthy": health_status["healthy"]
        }
```

Let me try a different approach by reading the specific lines and updating them:

```python
    try:
        health_status = ai_resilience.get_health_status()
        return {
            "resilience_health": health_status,
            "service_health": text_processor.get_resilience_health(),
            "overall_healthy": health_status["healthy"]
        }
```

