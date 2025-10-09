# Data Models & Schemas Philosophy

This guide outlines the project's philosophy for organizing data models and schemas. Adhering to these patterns ensures clarity, maintainability, and a strong separation of concerns between the public API contract and internal data structures.

-----

## The Two Core Patterns

Our codebase utilizes two primary patterns for defining data structures, each with a specific location and purpose.

### 1\. API Contracts: `backend/app/schemas/`

This directory is exclusively for Pydantic `BaseModel`s that define the **public-facing contract** of your API.

  * **Purpose**: To define the shape of JSON request and response bodies for API endpoints, primarily those in `backend/app/api/v1/`.
  * **Technology**: **Pydantic `BaseModel`**. Pydantic's robust validation and JSON schema generation are ideal for defining API contracts that FastAPI uses to validate requests, serialize responses, and generate OpenAPI documentation.
  * **Example**: A `TextProcessingRequest` model that defines the expected input for the `/v1/text_processing/process` endpoint.

<!-- end list -->

```python
# In backend/app/schemas/text_processing.py

from pydantic import BaseModel
from app.services.text_processor.models import ProcessingOperation

class TextProcessingRequest(BaseModel):
    """Request model for processing text."""
    text: str
    operation: ProcessingOperation
    question: str | None = None
    options: dict | None = None
```

-----

### 2\. Internal Data Models: Co-located with Logic

These models are used for handling data *within* the application. They are not directly exposed to the outside world via an API endpoint.

  * **Purpose**: To structure internal data, such as configuration objects, data passed between services, or the results of an internal computation.
  * **Technology**: Standard Python **`@dataclass`** is often preferred for its simplicity and lightweight nature. Internal-only Pydantic models can also be used if validation is needed.
  * **Location**: These models should be "co-located"—defined in the same file or a dedicated `models.py` file directly alongside the service or logic that uses them (e.g., in `backend/app/core/`, `backend/app/infrastructure/`, or `backend/app/services/`).
  * **Example**: The `EnvironmentInfo` dataclass in `backend/app/core/environment/models.py`, which structures environment variable data for internal use.

<!-- end list -->

```python
# In backend/app/core/environment/models.py

from dataclasses import dataclass, field

@dataclass
class EnvironmentInfo:
    """A dataclass to hold environment information."""
    is_production: bool
    is_development: bool
    is_testing: bool
    log_level: str
    # ... other internal fields
```

-----

## How to Choose Where to Place a Model

When creating a new data model, ask yourself this simple question:

> **Is this model part of a public API request or response body?**

  * **If YES**: It's an **API Contract**. Create it as a Pydantic `BaseModel` inside the `backend/app/schemas/` directory.
  * **If NO**: It's an **Internal Data Model**. Create it as a `@dataclass` (or Pydantic model if needed) and place it next to the code that uses it.

-----

## Auditing for Conformity with an LLM

You can use a capable LLM coding assistant to periodically audit the codebase and ensure these architectural patterns are being followed. Here are some effective prompts you can use.

### Prompt 1: General Pattern Analysis

This prompt asks the agent to discover and explain the patterns, which is useful for verification.

```
What is the value to the template of `backend/schemas`? It seems like our more recent `@dataclass` implementations such as `SecurityResult` in `backend/app/infrastructure/security/llm/protocol.py` and `EnvironmentInfo` in `backend/app/core/environment/models.py` `@dataclass` are being declared directly with other production code.

What appears to be the more common pattern based on our current codebase? Should I be trying to migrate these `@dataclass` implementations to the `schemas` directory? Or should I keep them where they are and consider migrating the models out of `backend/schemas` to a more appropriate, functionally-related directory?
```

### Prompt 2: Targeted API Audit

This prompt directs the agent to perform a specific check on the API endpoints to verify they are correctly using the `schemas` directory.

```
To identify which (if any) dataclasses belong in `backend/app/schemas` should I be looking at the code in `backend/app/api` to see which schemas are being used and check their location? Please perform this check and report your findings.
```