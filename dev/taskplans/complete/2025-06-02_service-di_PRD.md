## Service Dependency Injection in Backend

### Current State Analysis

**Global Service Pattern Found:**
```python
# backend/app/services/text_processor.py
text_processor = TextProcessorService()

# backend/app/services/cache.py
ai_cache = AIResponseCache()

# backend/app/main.py
from app.services.text_processor import text_processor
```

### Functional Gaps Identified

#### 1. **Tight Coupling and Testing Difficulties**
- **Gap**: Services are instantiated at module level
- **Impact**: Cannot mock services easily, tests interfere with each other
- **Evidence**: Tests in `test_main.py` require complex mocking patterns

#### 2. **Service Lifecycle Management**
- **Gap**: No control over when services are created/destroyed
- **Impact**: Memory leaks, resource conflicts, unclear initialization order
- **Evidence**: Services initialize even when not needed (like in tests)

#### 3. **Configuration Dependency Issues**
- **Gap**: Services depend on global settings at import time
- **Impact**: Cannot test with different configurations, hard to override settings
- **Evidence**: `TextProcessorService.__init__()` reads from global `settings`

#### 4. **Circular Dependency Risk**
- **Gap**: Services import each other directly
- **Impact**: Risk of circular imports as system grows
- **Evidence**: Cache service and text processor both import from each other

### Current Testing Pain Points

```python
# Current testing approach (problematic)
@patch('app.services.text_processor.text_processor.agent')
def test_something(mock_agent):
# Complex mocking required

# Service initialization happens at import
# Cannot easily test different configurations
```

### Opportunities for Improvement

#### Immediate Solutions (2-3 days effort)

**1. Create Dependency Injection Container**
```python
# backend/app/dependencies.py
from functools import lru_cache
from fastapi import Depends
from app.services.text_processor import TextProcessorService
from app.services.cache import AIResponseCache
from app.config import Settings

@lru_cache()
def get_settings() -> Settings:
return Settings()

async def get_cache_service(
settings: Settings = Depends(get_settings)
) -> AIResponseCache:
cache = AIResponseCache()
await cache.connect()
return cache

async def get_text_processor(
settings: Settings = Depends(get_settings),
cache: AIResponseCache = Depends(get_cache_service)
) -> TextProcessorService:
return TextProcessorService(settings=settings, cache=cache)
```

**2. Update Endpoints to Use DI**
```python
# backend/app/main.py
@app.post("/process", response_model=TextProcessingResponse)
async def process_text(
request: TextProcessingRequest,
processor: TextProcessorService = Depends(get_text_processor),
api_key: str = Depends(verify_api_key)
):
return await processor.process_text(request)
```

**3. Refactor Service Classes**
```python
# backend/app/services/text_processor.py
class TextProcessorService:
def __init__(self, settings: Settings, cache: AIResponseCache):
    self.settings = settings
    self.cache = cache
    self.agent = Agent(model=settings.ai_model)

# Remove global instance
# text_processor = TextProcessorService()  # DELETE THIS
```

#### Testing Improvements
```python
# Much easier testing with DI
@pytest.fixture
def mock_processor():
return Mock(spec=TextProcessorService)

def test_endpoint(mock_processor):
app.dependency_overrides[get_text_processor] = lambda: mock_processor
# Test with clean mocks
```

#### Long-term Benefits
- **Easy Unit Testing**: Clean dependency injection for tests
- **Better Resource Management**: Services created only when needed
- **Configuration Flexibility**: Different configs for different environments
- **Clear Dependency Graph**: Explicit service dependencies
- **Async Support**: Proper async service initialization

### Task List

Fulfill the requirements of the PRD by executing this task list:

#### Task 1
**Create the new file `dependencies.py` within the `backend/app` directory. This file will house all dependency provider functions.**

Create an empty Python file named `dependencies.py` in the `backend/app/` path. Add necessary initial imports like `from functools import lru_cache` and `from fastapi import Depends`.

#### Task 2
**Define or refine the `Settings` class in `app.config` to ensure it can be instantiated and used by dependency providers. This class holds application configurations.**

Ensure `app.config.Settings` class is well-defined, potentially using Pydantic for validation. It should load settings from environment variables or a configuration file. Example: `class Settings(BaseSettings): ai_model: str = 'default_model' ...`.

#### Task 3
**Implement the `get_settings` dependency provider function in `dependencies.py` using `lru_cache` for efficiency.**

In `backend/app/dependencies.py`, implement `get_settings` as shown in PRD: 

```python
from app.config import Settings
from functools import lru_cache

@lru_cache()
def get_settings() -> Settings:
    return Settings()
```

#### Task 4
**Modify `AIResponseCache` class in `app.services.cache` to remove any direct dependency on global settings at import time or instantiation. Configuration should be injectable.**

Review `AIResponseCache.__init__` and its methods (e.g., `connect`). Remove any direct reads from global `settings`. Ensure that any configuration needed by the cache (e.g., connection strings) can be managed by its provider function `get_cache_service`.

#### Task 5
**Implement the `get_cache_service` asynchronous dependency provider in `dependencies.py`.**

In `backend/app/dependencies.py`, implement `get_cache_service`:

```python
from app.services.cache import AIResponseCache

async def get_cache_service(settings: Settings = Depends(get_settings)) -> AIResponseCache:
    cache = AIResponseCache()
    await cache.connect() # Assuming connect might use settings implicitly or be refactored to take settings.
    return cache
```

#### Task 6
**Remove the global instance `ai_cache = AIResponseCache()` from `backend/app/services/cache.py`.**

Delete the line `ai_cache = AIResponseCache()` from `backend/app/services/cache.py`. All usages will now rely on DI via `get_cache_service`.

#### Task 7
**Modify `TextProcessorService.__init__` in `app.services.text_processor` to accept `settings: Settings` and `cache: AIResponseCache` as arguments.**

Change `TextProcessorService.__init__` signature to `def __init__(self, settings: Settings, cache: AIResponseCache):`. Store `settings` and `cache` as instance attributes (e.g., `self.settings = settings`, `self.cache = cache`).

#### Task 8
**Update `TextProcessorService` internal logic to use injected `settings` and `cache`.**

Modify methods within `TextProcessorService` to use `self.settings` and `self.cache` instead of global settings or cache instances. Specifically, update agent initialization: `self.agent = Agent(model=self.settings.ai_model)`.

#### Task 9
**Implement the `get_text_processor` asynchronous dependency provider in `dependencies.py`.**

In `backend/app/dependencies.py`, implement `get_text_processor`: 

```python
from app.services.text_processor import TextProcessorService

async def get_text_processor(settings: Settings = Depends(get_settings), cache: AIResponseCache = Depends(get_cache_service)) -> TextProcessorService:
    return TextProcessorService(settings=settings, cache=cache)
```

#### Task 10
**Remove the global instance `text_processor = TextProcessorService()` from `backend/app/services/text_processor.py`.**

Delete the line `text_processor = TextProcessorService()` from `backend/app/services/text_processor.py`. All usages will now rely on DI via `get_text_processor`.

#### Task 11
**Review and refactor service modules (`text_processor.py`, `cache.py`) to remove direct module-level imports of each other, preventing circular dependencies.**

Inspect `text_processor.py` and `cache.py` for any `from app.services.other_service import ...` statements at the module level. Remove these. Dependencies are now injected via `__init__` and resolved by FastAPI's DI.

#### Task 12
**Update the `/process` endpoint in `backend/app/main.py` to use `Depends(get_text_processor)` for `TextProcessorService`.**

Modify the `/process` endpoint signature: `async def process_text(request: TextProcessingRequest, processor: TextProcessorService = Depends(get_text_processor), ...):`. Remove any manual instantiation or retrieval of `text_processor` from globals.

#### Task 13
**Ensure the `verify_api_key` dependency used in the `/process` endpoint is correctly defined and integrated.**

Check or implement the `verify_api_key` dependency function. It should be a FastAPI dependency (e.g., `async def verify_api_key(api_key: str = Header(...)) -> str:`). Ensure it's correctly used in the `/process` endpoint signature.

#### Task 14
**Identify all other FastAPI endpoints that currently use global instances of `TextProcessorService` or `AIResponseCache`.**

Scan `main.py` and any other router files for usages of `app.services.text_processor.text_processor` or `app.services.cache.ai_cache`. Create a list of these endpoints.

#### Task 15
**Refactor one additional representative endpoint (identified in Task 14, if any) to use DI for `TextProcessorService`.**

Pick an endpoint from the list generated in Task 14 that uses `TextProcessorService`. Update its signature to use `processor: TextProcessorService = Depends(get_text_processor)`.

#### Task 16
**Refactor one additional representative endpoint (identified in Task 14, if any) to use DI for `AIResponseCache` if it's used directly.**

Pick an endpoint from the list generated in Task 14 that uses `AIResponseCache` directly. Update its signature to use `cache: AIResponseCache = Depends(get_cache_service)`.

#### Task 17
**Create a `pytest.fixture` for mocking `TextProcessorService` in test files, as shown in PRD.**

In the relevant test file (e.g., `test_main.py`), add:

```python
import pytest
from unittest.mock import Mock
from app.services.text_processor import TextProcessorService

@pytest.fixture
def mock_processor():
    return Mock(spec=TextProcessorService)
```

#### Task 18
**Update tests for the `/process` endpoint in `test_main.py` to use `app.dependency_overrides` with `mock_processor`.**

Refactor tests for `/process` endpoint. Use `app.dependency_overrides[get_text_processor] = lambda: mock_processor_fixture_instance`. Ensure tests pass with the mocked service.

#### Task 19
**Create a `pytest.fixture` for mocking `AIResponseCache` for tests.**

Similar to `mock_processor`, create a fixture for `AIResponseCache`: 

```python
from app.services.cache import AIResponseCache

@pytest.fixture
def mock_cache_service():
    mock_cache = Mock(spec=AIResponseCache)
    # if connect is async and called by provider, mock it as async
    mock_cache.connect = AsyncMock() 
    return mock_cache
```
(Requires `from unittest.mock import AsyncMock` if Python 3.8+).

#### Task 20
**Update tests that previously mocked `AIResponseCache` globally or relied on its global instance to use `app.dependency_overrides` with `mock_cache_service`.**

Identify tests that interacted with `AIResponseCache`. Refactor them to use `app.dependency_overrides[get_cache_service] = lambda: mock_cache_fixture_instance`. Ensure tests pass with the mocked service.
