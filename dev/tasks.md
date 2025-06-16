# Tasks

## Task 1: Create Core Directory Structure

**Priority:** high     **Status:** done     **Dependencies:** none

**Description:** Create the foundational directory structure for the refactored backend application as specified in the PRD, including all top-level and nested directories. Add __init__.py files to make them Python packages.

**Details:** Execute the following commands to create the directory tree and initialize Python packages:
```bash
mkdir -p backend/app/api/v1/routers
mkdir -p backend/app/api/internal
mkdir -p backend/app/core
mkdir -p backend/app/infrastructure/ai
mkdir -p backend/app/infrastructure/cache
mkdir -p backend/app/infrastructure/resilience
mkdir -p backend/app/infrastructure/security
mkdir -p backend/app/infrastructure/monitoring
mkdir -p backend/app/services
mkdir -p backend/app/schemas
mkdir -p backend/app/examples

# Create __init__.py files in all subdirectories of backend/app
find backend/app -type d -exec touch {}/__init__.py \;
# Ensure backend/app/__init__.py itself is also created as per PRD structure.
```

**Test Strategy:** Verify all specified directories (`api/`, `core/`, `infrastructure/`, `services/`, `schemas/`, `examples/` and their subdirectories) and `__init__.py` files exist under `backend/app/`. Attempt to import modules from these new packages (e.g., `from backend.app import core`) to ensure they are recognized by Python.


## Task 2: Initialize FastAPI Application and Global Dependencies

**Priority:** high     **Status:** in-progress     **Dependencies:** 1

**Description:** Create the main FastAPI application entry point (`main_refactored.py`) and a placeholder for global dependency injection providers (`dependencies_refactored.py`) in `backend/app/` for the refactored application. During the migration, `main_refactored.py` and `dependencies_refactored.py` will be used for running and testing the refactored app. The original `main.py` and `dependencies.py` files must not be modified until Tasks 20 and 29, where integration will occur. After integration, these `_refactored.py` files will be deleted as they are no longer needed. This approach allows the refactored app to run using the new code while preserving the original files for later integration.

**Details:** Create `backend/app/main_refactored.py` with a basic FastAPI application instance. Example:
```python
# backend/app/main_refactored.py
from fastapi import FastAPI

app = FastAPI(title="Refactored App")

@app.get("/")
async def root():
    return {"message": "Hello World - Refactored"}
```
Create `backend/app/dependencies_refactored.py` as a placeholder for future dependency injection setup for the refactored application. Example:
```python
# backend/app/dependencies_refactored.py
# Global dependency injection providers for the refactored app will be defined here.
pass
```
These new files will exist alongside the original `main.py` and `dependencies.py`.

**Important Migration Note:**
During the migration phase, use `main_refactored.py` and `dependencies_refactored.py` exclusively for running and testing the refactored application. **Do not modify the original `main.py` and `dependencies.py` files.** These original files will be updated during Tasks 20 (for `main.py`) and 29 (for `dependencies.py`) to integrate the refactored code. After successful integration, the `_refactored.py` files will be obsolete and can be deleted.

**Test Strategy:** Verify `backend/app/main_refactored.py` and `backend/app/dependencies_refactored.py` are created in the `backend/app/` directory. Run the refactored FastAPI application using Uvicorn (e.g., `uvicorn backend.app.main_refactored:app --reload`) and ensure it starts without errors and responds to requests at the root endpoint. Crucially, confirm that the original `main.py` and `dependencies.py` files remain untouched during this task, as they will be handled in later integration tasks (Tasks 20 and 29).


## Task 3: Setup Examples Directory README

**Priority:** medium     **Status:** pending     **Dependencies:** 1

**Description:** Create the `README.md` file within the `examples/` directory with the specified content to inform developers about the purpose of this directory.

**Details:** Create a file named `README.md` in `backend/app/examples/`.
The content of this file should be exactly: "These are examples for learning!"

**Test Strategy:** Verify the file `backend/app/examples/README.md` exists and contains the exact specified text.


## Task 4: Define Import Strategy and Path Aliases

**Priority:** medium     **Status:** pending     **Dependencies:** 1

**Description:** Document the import strategy for the gradual migration process. Configure path aliases in `pyproject.toml` or `setup.cfg` if beneficial for cleaner imports during and after refactoring.

**Details:** 1. Document conventions for imports (e.g., prefer absolute imports from the `backend.app` root).
2. Evaluate and implement path aliases if needed. For example, using `PYTHONPATH` adjustments or `sys.path` modifications in a common entry point for development, or more robustly via `pyproject.toml` for tools like MyPy and IDEs.
Example for `pyproject.toml` (if using Poetry/PEP 621 tools):
```toml
# [tool.mypy]
# mypy_path = "backend"
# [tool.pytest.ini_options]
# pythonpath = [".", "backend"]
```
This task is primarily about establishing patterns to be used by `import_update_script.py` and developers.

**Test Strategy:** Review the documented import strategy for clarity. If path aliases are implemented, verify that imports using these aliases resolve correctly in a test script or by running static analysis tools.


## Task 5: Create Cache Service Interface and Implementations

**Priority:** high     **Status:** pending     **Dependencies:** 1

**Description:** Create the cache service interface (`CacheInterface`) and its Redis (`AIResponseCache`) and in-memory (`InMemoryCache`) implementations within the `infrastructure/cache/` directory. Preserve the `AIResponseCache` class name.

**Details:** 1. Create `backend/app/infrastructure/cache/base.py`:
```python
from abc import ABC, abstractmethod

class CacheInterface(ABC):
    @abstractmethod
    async def get(self, key: str):
        pass
    @abstractmethod
    async def set(self, key: str, value: any, ttl: int = None):
        pass
    @abstractmethod
    async def delete(self, key: str):
        pass
```
2. Move existing `AIResponseCache` logic from `app/services/cache.py` to `backend/app/infrastructure/cache/redis.py`. Ensure it implements `CacheInterface` and preserves the `AIResponseCache` class name.
3. Create `backend/app/infrastructure/cache/memory.py` with an `InMemoryCache` class implementing `CacheInterface`.

**Test Strategy:** Unit test `AIResponseCache` and `InMemoryCache`. Verify they implement all methods of `CacheInterface`. Confirm `AIResponseCache` maintains its original functionality after relocation. Test get, set, delete, and TTL logic for both implementations.


## Task 6: Extract Circuit Breaker Logic

**Priority:** high     **Status:** pending     **Dependencies:** 1

**Description:** Move existing circuit breaker logic to `infrastructure/resilience/circuit_breaker.py`. Ensure all class names and method signatures are preserved for compatibility.

**Details:** Identify circuit breaker classes and related functions in the current codebase (likely in `app/services/resilience.py`). Move this logic to `backend/app/infrastructure/resilience/circuit_breaker.py`. Ensure all original class names, method signatures, and functionality are preserved. The logic should be business-agnostic.

**Test Strategy:** Review the moved code for completeness and preservation of names/signatures. Existing unit tests for circuit breaker functionality should pass when pointed to the new location (though test refactoring is out of scope, tests might need import updates later).


## Task 7: Extract Retry Logic

**Priority:** high     **Status:** pending     **Dependencies:** 1

**Description:** Move existing retry logic and strategies to `infrastructure/resilience/retry.py`. Preserve all class names and method signatures.

**Details:** Identify retry mechanism classes, functions, and strategies (e.g., exponential backoff) in the current codebase (likely in `app/services/resilience.py`). Move this logic to `backend/app/infrastructure/resilience/retry.py`. Preserve all original class names, method signatures, and functionality. The logic should be business-agnostic.

**Test Strategy:** Review the moved code for completeness and preservation of names/signatures. Existing unit tests for retry logic should pass when imports are updated.


## Task 8: Extract Resilience Presets

**Priority:** medium     **Status:** pending     **Dependencies:** 1, 6, 7

**Description:** Extract resilience configuration presets into `infrastructure/resilience/presets.py`. These presets would typically configure the circuit breaker and retry mechanisms.

**Details:** Identify any predefined configurations or presets for resilience patterns (circuit breaker, retries) from `app/services/resilience.py` or configuration files. Move these to `backend/app/infrastructure/resilience/presets.py`. This file should provide ready-to-use configurations for common scenarios.

**Test Strategy:** Verify that `presets.py` contains meaningful configurations that can be applied to the circuit breaker and retry components. Ensure presets are easily importable and usable.


## Task 9: Extract Security Utilities (Auth & Sanitization)

**Priority:** high     **Status:** pending     **Dependencies:** 1

**Description:** Move API key validation logic to `infrastructure/security/auth.py` and input sanitization utilities to `infrastructure/security/sanitization.py`. Preserve all function names.

**Details:** 1. Move API key validation logic from its current location (e.g., `app/auth.py`) to `backend/app/infrastructure/security/auth.py`.
2. Move input sanitization utilities to `backend/app/infrastructure/security/sanitization.py`.
Preserve all original function names and signatures for both.

**Test Strategy:** Review moved code for completeness and preservation of function names/signatures. Existing tests for auth and sanitization should pass after import updates.


## Task 10: Extract Response Security Validator

**Priority:** medium     **Status:** pending     **Dependencies:** 1

**Description:** Move response security validation logic to `infrastructure/security/response_validator.py`.

**Details:** Identify and move any logic responsible for validating or securing outbound responses to `backend/app/infrastructure/security/response_validator.py`. Preserve function/class names and signatures.

**Test Strategy:** Review moved code. Existing tests for response validation should pass after import updates.


## Task 11: Extract Monitoring Utilities (Metrics & Health)

**Priority:** high     **Status:** pending     **Dependencies:** 1

**Description:** Move performance metrics collection logic to `infrastructure/monitoring/metrics.py` and health check utilities to `infrastructure/monitoring/health.py`.

**Details:** 1. Move logic for collecting and exposing performance metrics to `backend/app/infrastructure/monitoring/metrics.py`.
2. Move utilities for application health checks (e.g., checking database connections, external services) to `backend/app/infrastructure/monitoring/health.py`.
Preserve function/class names and signatures.

**Test Strategy:** Review moved code. Existing tests for metrics and health checks should pass after import updates.


## Task 12: Create Cache Monitor

**Priority:** medium     **Status:** pending     **Dependencies:** 1, 5, 11

**Description:** Implement `infrastructure/monitoring/cache_monitor.py` for monitoring the performance and health of cache services.

**Details:** Create `backend/app/infrastructure/monitoring/cache_monitor.py`. This module should contain utilities to monitor cache performance, such as hit/miss ratios, latency, and cache size, possibly integrating with the metrics system from `infrastructure/monitoring/metrics.py` and utilizing the `CacheInterface`.

**Test Strategy:** Unit test the cache monitoring utilities. If integrated with a metrics system, verify that cache metrics are correctly reported.


## Task 13: Consolidate Application Configuration

**Priority:** high     **Status:** pending     **Dependencies:** 1

**Description:** Consolidate all application settings from the old `config.py` (and potentially other places) into `core/config.py`. Preserve the `Settings` class name and its internal structure, organizing settings by sections using comments or nested Pydantic models.

**Details:** Migrate all configurations from `app/config.py` (and other disparate sources if any) to `backend/app/core/config.py`. The main configuration class must retain the name `Settings`. Structure settings logically, e.g., using nested `BaseSettings` models or clear comments for sections. Ensure environment variable loading and validation at startup are maintained.
Example structure:
```python
# backend/app/core/config.py
from pydantic_settings import BaseSettings

class Settings(BaseSettings):
    APP_NAME: str = "My FastAPI App"
    # ... other settings ...
    # Example of a section:
    # REDIS_SETTINGS
    REDIS_HOST: str = "localhost"

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"

settings = Settings()
```

**Test Strategy:** Verify that `core.config.settings` can be imported and all expected configuration values are present and correctly loaded from environment variables or defaults. Existing tests relying on configuration should pass after import updates.


## Task 14: Centralize Custom Exceptions

**Priority:** medium     **Status:** pending     **Dependencies:** 1

**Description:** Extract the custom exception hierarchy into a dedicated `core/exceptions.py` file.

**Details:** Identify all custom exception classes defined throughout the application. Move them into `backend/app/core/exceptions.py`. Ensure a clear hierarchy if one exists or should be established.

**Test Strategy:** Verify that all custom exceptions are present in `core/exceptions.py` and can be imported. Existing code that raises or catches these exceptions should function correctly after import updates.


## Task 15: Setup Core Middleware

**Priority:** high     **Status:** pending     **Dependencies:** 1, 13, 14

**Description:** Create `core/middleware.py` and consolidate or define application-wide middleware such as CORS, error handling, and request/response logging.

**Details:** Create `backend/app/core/middleware.py`. Move existing middleware (e.g., CORS, global error handlers, logging middleware) to this file. If new standard middleware is needed, define it here. Middleware may depend on `core.config` for settings and `core.exceptions` for error handling.

**Test Strategy:** Unit test individual middleware if possible. Verify that middleware is correctly applied to the FastAPI application and functions as expected (e.g., CORS headers are present, errors are handled gracefully).


## Task 16: Structure Versioned Public API (v1)

**Priority:** high     **Status:** pending     **Dependencies:** 1

**Description:** Create the directory structure for versioned public APIs under `api/v1/`, including `routers/` for route handlers and `deps.py` for API-specific dependencies.

**Details:** Ensure the following directory structure exists: `backend/app/api/v1/` and `backend/app/api/v1/routers/`. Create an empty `backend/app/api/v1/deps.py` file for API-specific dependencies like authentication or rate limiting.

**Test Strategy:** Verify the directory structure and `deps.py` file are created. Ensure `__init__.py` files are present to make them packages.


## Task 17: Relocate v1 Text Processing and Health Endpoints

**Priority:** high     **Status:** pending     **Dependencies:** 16

**Description:** Relocate existing text processing endpoints to `api/v1/routers/text_processing.py` and health check endpoints to `api/v1/routers/health.py`.

**Details:** 1. Move FastAPI router and endpoint functions related to text processing to `backend/app/api/v1/routers/text_processing.py`.
2. Move FastAPI router and endpoint functions related to health checks (e.g., `/v1/health`, `/v1/auth/status`) to `backend/app/api/v1/routers/health.py`.
Preserve endpoint paths, request/response models, and functionality.

**Test Strategy:** After relocation and router registration (Task 20), test these specific endpoints to ensure they function as before. Check paths and expected responses.


## Task 18: Structure Unversioned Internal API

**Priority:** high     **Status:** pending     **Dependencies:** 1

**Description:** Create the directory structure for unversioned internal APIs under `api/internal/`.

**Details:** Ensure the directory `backend/app/api/internal/` exists. Ensure `__init__.py` is present.

**Test Strategy:** Verify the directory structure is created and `api.internal` is a Python package.


## Task 19: Relocate Internal Monitoring and Admin Endpoints

**Priority:** high     **Status:** pending     **Dependencies:** 18

**Description:** Relocate the existing monitoring router to `api/internal/monitoring.py` and admin/resilience-related endpoints to `api/internal/admin.py`.

**Details:** 1. Move the FastAPI router and endpoint functions for monitoring (e.g., from `app/routers/monitoring.py`) to `backend/app/api/internal/monitoring.py`.
2. Move admin and resilience-related endpoints (e.g., cache management, circuit breaker status from `resilience_endpoints.py`) to `backend/app/api/internal/admin.py`.
These are unversioned internal APIs.

**Test Strategy:** After relocation and router registration (Task 20), test these specific internal endpoints to ensure they function as before. Check paths and expected responses.


## Task 20: Update Main Router Registration

**Priority:** high     **Status:** pending     **Dependencies:** 2, 17, 19

**Description:** Update `main.py` to register API routers from their new locations in `api/v1/routers/` and `api/internal/`. After successful registration, `main_refactored.py` should be deleted if it exists.

**Details:** 1. Modify `backend/app/main.py` to import and include routers from their new locations (`api/v1/routers/` and `api/internal/`). Example:
```python
# backend/app/main.py
from fastapi import FastAPI
from .api.v1.routers import text_processing as v1_text_processing, health as v1_health
from .api.internal import monitoring as internal_monitoring, admin as internal_admin
# ... other imports ...

app = FastAPI(title="Refactored App")

# V1 Routers
app.include_router(v1_text_processing.router, prefix="/v1", tags=["V1 Text Processing"])
app.include_router(v1_health.router, prefix="/v1", tags=["V1 Health"])

# Internal Routers
app.include_router(internal_monitoring.router, prefix="/monitoring", tags=["Internal Monitoring"])
app.include_router(internal_admin.router, prefix="/admin", tags=["Internal Admin"])
```
Ensure all existing routes are preserved with correct prefixes and tags.
2. After updating `main.py` and confirming the application runs correctly, delete the `main_refactored.py` file from `backend/app/` if it exists, as it is no longer needed.

**Test Strategy:** 1. Start the application and access the OpenAPI docs (e.g., `/docs`). Verify all relocated routes are registered correctly under their new prefixes and tags.
2. Ensure existing API tests target these routes correctly and pass.
3. After deleting `main_refactored.py` (if it existed), confirm the application still starts and functions as expected, and that the OpenAPI docs remain correct.

**Subtasks (2):**

### Subtask 1: Update main.py router registrations

**Description:** No description available

**Details:** Modify `backend/app/main.py` to import and include routers from `api/v1/routers/` and `api/internal/` as per the main task details. Ensure all existing routes are preserved with correct prefixes and tags.

### Subtask 2: Delete main_refactored.py

**Description:** No description available

**Details:** After `main.py` is updated and verified, delete `backend/app/main_refactored.py` if it exists.


## Task 21: Refactor Text Processing Service

**Priority:** high     **Status:** pending     **Dependencies:** 1, 5, 6, 7, 9, 11

**Description:** Consolidate domain-specific text processing logic into `services/text_processing.py`. Preserve the `TextProcessorService` class name and demonstrate usage of infrastructure services.

**Details:** Move/consolidate text processing business logic from `app/services/text_processor.py` (and potentially other places) into `backend/app/services/text_processing.py`. The primary class should retain the name `TextProcessorService`. This service should be updated to use abstracted infrastructure services (e.g., CacheInterface, AI client, resilience patterns) via dependency injection.

**Test Strategy:** Unit test `TextProcessorService`. Verify it correctly utilizes injected infrastructure services. Existing tests for text processing functionality should pass after import and DI updates.


## Task 22: Relocate Advanced Examples

**Priority:** medium     **Status:** pending     **Dependencies:** 1, 3, 21

**Description:** Move complex usage examples, such as `advanced_text_processing.py`, from the main codebase to the `examples/` directory.

**Details:** Identify any advanced or complex example implementations currently within the main application logic (e.g., `app/services/` or `app/routers/`). Move these to `backend/app/examples/`, for instance, as `backend/app/examples/advanced_text_processing.py`. These examples should demonstrate best practices for using infrastructure and domain services.

**Test Strategy:** Verify that the example files are moved to `examples/`. Ensure the examples are runnable (if applicable) and demonstrate correct usage patterns. The main codebase should be cleaner as a result.


## Task 23: Document Domain Service Replaceability

**Priority:** medium     **Status:** pending     **Dependencies:** 21

**Description:** Add clear comments and documentation within `services/text_processing.py` (and other domain services) indicating that this is example code meant to be replaced or customized by users of the template.

**Details:** In `backend/app/services/text_processing.py` (and any other example domain services), add prominent comments at the top of the file and/or in the class docstring. Example:
```python
# backend/app/services/text_processing.py
"""
This is an EXAMPLE domain service for text processing.
It demonstrates how to use infrastructure services.
REPLACE THIS with your actual business logic.
"""
# ... rest of the code ...
```

**Test Strategy:** Review the `services/text_processing.py` file to ensure the documentation clearly communicates that the service is an example and should be replaced.


## Task 24: Organize Text Processing Schemas

**Priority:** high     **Status:** pending     **Dependencies:** 1, 21

**Description:** Create `schemas/text_processing.py` and move all Pydantic models related to text processing requests and responses into this file. Preserve all model class names.

**Details:** Identify Pydantic models used for text processing API requests and responses (likely from an old `validation_schemas.py` or defined alongside routers/services). Move them to `backend/app/schemas/text_processing.py`. All original Pydantic model class names must be preserved for compatibility.

**Test Strategy:** Verify all relevant text processing Pydantic models are in the new file. Ensure class names are unchanged. Code using these schemas should function correctly after import updates.


## Task 25: Organize Monitoring Schemas

**Priority:** medium     **Status:** pending     **Dependencies:** 1, 11, 19

**Description:** Create `schemas/monitoring.py` and move Pydantic models related to monitoring endpoints and data structures into this file. Preserve all model class names.

**Details:** Identify Pydantic models used for monitoring API endpoints (e.g., health status, metrics data) from `validation_schemas.py` or other locations. Move them to `backend/app/schemas/monitoring.py`. All original Pydantic model class names must be preserved.

**Test Strategy:** Verify all relevant monitoring Pydantic models are in the new file with unchanged class names. Code using these schemas should function correctly after import updates.


## Task 26: Organize Resilience Schemas

**Priority:** medium     **Status:** pending     **Dependencies:** 1, 6, 7, 8

**Description:** Create `schemas/resilience.py` and move Pydantic models related to resilience configurations (e.g., circuit breaker settings, retry policies) into this file. Preserve all model class names.

**Details:** Identify Pydantic models used for configuring resilience features (e.g., from `validation_schemas.py` or resilience modules). Move them to `backend/app/schemas/resilience.py`. All original Pydantic model class names must be preserved.

**Test Strategy:** Verify all relevant resilience Pydantic models are in the new file with unchanged class names. Code using these schemas should function correctly after import updates.


## Task 27: Create Common Schemas File

**Priority:** medium     **Status:** pending     **Dependencies:** 1

**Description:** Create `schemas/common.py` for shared Pydantic models, enums, or base models used across different features. Preserve all model class names.

**Details:** Identify any Pydantic models, enums, or base classes that are shared across multiple domains or features. Move them to `backend/app/schemas/common.py`. All original Pydantic model class names must be preserved.

**Test Strategy:** Verify that shared Pydantic models are correctly placed in `common.py` with unchanged class names. Ensure these common models are usable by other schema files or services.


## Task 28: Automated Import Updates

**Priority:** high     **Status:** pending     **Dependencies:** 1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12, 13, 14, 15, 16, 17, 18, 19, 20, 21, 22, 23, 24, 25, 26, 27

**Description:** Run the `import_update_script.py` tool to automatically update all import statements throughout the codebase to reflect the new file structure.

**Details:** Use the provided `import_update_script.py` to refactor import statements. Execute from the `backend` directory.
1. Dry run: `python scripts/import_update_script.py --dry-run --verbose`
2. Review changes.
3. Apply changes: `python scripts/import_update_script.py`
The script should use a pre-defined mapping of old paths to new paths based on the refactoring tasks.

**Test Strategy:** After running the script, the application should be importable and runnable without `ImportError` exceptions. Static analysis tools (linters, MyPy) should pass regarding imports. Key application functionality should be smoke-tested.


## Task 29: Update Global Dependency Injection Providers

**Priority:** high     **Status:** pending     **Dependencies:** 2, 28

**Description:** Update `dependencies.py` to use new dependency locations and remove the obsolete `dependencies_refactored.py` file.

**Details:** The primary goal is to update `backend/app/dependencies.py` with the correct paths for all services, configurations, and other providers. After this update is complete and verified, the `dependencies_refactored.py` file, if present in `backend/app/` or its relevant location, should be deleted as it is no longer needed. Ensure FastAPI's dependency injection system functions correctly post-update.

**Test Strategy:** Start the application. Test endpoints that rely on dependency injection. Ensure no DI-related errors occur at startup or runtime. Existing tests that use DI should pass. Verify that `dependencies_refactored.py` has been deleted and its absence does not cause issues.

**Subtasks (2):**

### Subtask 29.1: Update dependency paths in dependencies.py

**Description:** Modify `backend/app/dependencies.py` to correctly instantiate and provide dependencies from their new locations (e.g., infrastructure services, configuration objects). Ensure FastAPI's dependency injection system can resolve all dependencies after these changes.

### Subtask 29.2: Delete obsolete dependencies_refactored.py

**Description:** After `dependencies.py` has been successfully updated and all dependency injection mechanisms are verified, delete the `dependencies_refactored.py` file from `backend/app/` (or its relevant location) if it exists, as it is no longer needed.


## Task 30: Validate Structure and Run Tests

**Priority:** high     **Status:** pending     **Dependencies:** 29

**Description:** Run the `structure_validation.py` script to validate architectural integrity (circular dependencies, layer hierarchy, file sizes, import depth). Subsequently, run the full existing test suite to ensure all tests pass without any modification to the test code itself.

**Details:** 1. Execute `structure_validation.py` from the `backend` directory: `python scripts/structure_validation.py --verbose`.
2. Analyze the report and address any critical issues related to architectural violations (e.g., domain importing from other domain, services importing API layer, file size > 500 lines).
3. Run the entire existing test suite (unit, integration, E2E tests). All tests must pass. No modifications should be made to the test files themselves as per PRD constraints.

**Test Strategy:** Successful execution of `structure_validation.py` without critical errors. 100% pass rate for the existing test suite. Confirm that no test code was changed to make tests pass.


## Task 31: Manual Endpoint Verification and Cleanup

**Priority:** medium     **Status:** pending     **Dependencies:** 30

**Description:** Perform manual verification of key API endpoints to ensure end-to-end functionality. Remove any old directories that are now empty as a result of file migrations.

**Details:** 1. Manually test a selection of critical API endpoints using a tool like Postman, curl, or the Swagger UI to ensure they behave as expected after refactoring.
2. Identify and remove any directories from the old structure that are now empty (e.g., old `app/services/`, `app/routers/` if all contents were moved).

**Test Strategy:** Successful manual tests of key API endpoints covering different aspects of the application. Verify that the project directory is clean and no obsolete empty directories remain.


## Task 32: Final Documentation Review

**Priority:** low     **Status:** pending     **Dependencies:** 31

**Description:** Review and update all relevant project documentation (READMEs, code comments, architectural diagrams if any) to accurately reflect the new directory structure and design principles.

**Details:** Update the main project README.md, any architectural documents, and significant code comments to align with the refactored structure. Ensure documentation clearly explains the separation of `infrastructure/`, `services/`, `core/`, and `api/` layers, and guides developers on where to add new logic or customize the template.

**Test Strategy:** Peer review of updated documentation for clarity, accuracy, and completeness. Ensure the developer journey described in the PRD is well-supported by the documentation.

