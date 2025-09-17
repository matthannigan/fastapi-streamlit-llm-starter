# Integration Tests

## Quick Navigation

### Related Guides
- **[Testing Overview](./TESTING.md)** - High-level testing philosophy and principles
- **[Writing Tests](./1_WRITING_TESTS.md)** - Docstring-driven test development
- **[Mocking Strategy](./2_MOCKING_GUIDE.md)** - When and how to use mocks vs fakes
- **[Test Structure](./4_TEST_STRUCTURE.md)** - Test organization and fixtures
- **[Test Execution](./5_TEST_EXECUTION_GUIDE.md)** - Running and debugging tests

### Quick Start Commands
```bash
# Run integration tests only
pytest tests/integration -v

# Run integration tests with coverage
pytest tests/integration --cov=app --cov-report=term-missing

# Run specific integration test file
pytest tests/integration/test_cache_integration.py -v
```

## Our Guiding Philosophy (TL;DR)

Our testing strategy prioritizes confidence and maintainability over raw code coverage. We write behavior-focused tests that verify the public contracts of our components, making our test suite resilient to refactoring.

Integration tests are the primary tool for verifying that our internal components collaborate correctly, and they are always written from the outside-in against a high-fidelity environment.

## Core Definition

In the context of our FastAPI application, a **behavior-focused integration test** is a test that verifies the collaborative behavior of two or more internal application components as they work together to fulfill a specific use case, exercised through a defined public interface.

This definition is built on three key pillars:

  * **Focus on Collaboration:** The primary purpose is not to test a single component's logic (that's a unit test), but to ensure that the "seams" or "connections" between our own components are correct. It answers the question: "When component A calls component B, does the system behave as expected?"
  * **Driven by Behavior:** Tests are written from the perspective of an external caller and validate observable outcomes, not internal implementation details. We test the *what* (the result), not the *how* (the internal function calls). For a service, the "caller" might be another service; for an API, the "caller" is an HTTP client.
  * **High-Fidelity Environment:** These tests run against real or high-fidelity fake infrastructure (e.g., a real database in a container, a real message queue, `fakeredis`). This ensures that our application's interaction with its infrastructure dependencies—like data serialization, query languages, and connection handling—is correct.

## The Guiding Principles

Our philosophy for integration testing follows from the core definition and is guided by our modern, multi-layered verification strategy.

### Principle 1: Test Critical Paths, Not Every Path

We invert the traditional testing pyramid. Instead of building a massive base of integration tests, we create a small, dense suite that provides maximum confidence for minimum maintenance.

  * **What to Test:** Focus on "critical paths" and high-value user journeys. A critical path is a sequence of operations that is essential to the application's function and business value. For example:
      * The complete flow from receiving an API request to persisting the result in the database.
      * The data pipeline of consuming a message from a queue, processing it, and storing it in the cache.
  * **What to Avoid:** Avoid writing integration tests for simple CRUD operations or edge cases that are already well-covered by unit/contract tests. The goal is confidence in the system's architecture, not 100% code coverage at the integration level.

### Principle 2: Trust Contracts, Verify Integrations

This is the cornerstone of our strategy. We leverage abstractions and interfaces to enable powerful, reusable tests.

> **📖 Contract-Driven Development**: Our project uses `.pyi` stub files to formally define component contracts. These are located in `backend/contracts/` and are automatically generated via `make generate-contracts`. See [Writing Tests Guide](./1_WRITING_TESTS.md#docstring-driven-test-development) for how we use these contracts to drive test development.

  * **The Workflow:**

    1.  **Define a Contract:** An interface is defined (e.g., using an `ABC` or a `.pyi` file) that specifies the public behavior of a component, like a `CacheInterface` or `StorageInterface`.
    2.  **Unit Test the Contract:** Write a suite of unit tests that validate *any* implementation of that contract. These tests confirm the component's internal logic and adherence to its own rules.
    3.  **Integration Test the Implementations:** The *same* contract test suite is then run against concrete implementations that use real infrastructure. This is our integration test.

  * **The Benefit:** This approach is incredibly resilient to refactoring. A single test suite can validate an in-memory fake cache (for fast local runs), a Redis cache, and a Memcached cache, guaranteeing that all implementations behave identically from the perspective of a calling service.

```python
# In conftest.py - Fixtures provide different cache implementations
import pytest
from fakeredis import FakeStrictRedis
from my_app.cache import RedisCache, CacheInterface

@pytest.fixture
def fake_redis_cache() -> CacheInterface:
    client = FakeStrictRedis()
    return RedisCache(client)

@pytest.fixture
def real_redis_cache() -> CacheInterface:
    # Assumes Testcontainers or a running Redis instance
    client = ... # Connect to real Redis
    return RedisCache(client)

# In test_cache_contract.py
@pytest.mark.parametrize("cache_instance", ["fake_redis_cache", "real_redis_cache"])
def test_cache_set_and_get_behaves_identically(cache_instance, request):
    """
    This single test serves as both a unit and integration test.
    It verifies the contract against multiple backends.
    """
    cache = request.getfixturevalue(cache_instance)
    key, value = "integration:test", {"data": "value"}
    
    cache.set(key, value, timeout_seconds=60)
    retrieved = cache.get(key)
    
    assert retrieved == value
```

### Principle 3: Test from the Outside-In

To ensure we are always testing behavior, integration tests should, whenever possible, be initiated from the application's boundary (e.g., an API endpoint or a message queue consumer).

  * **API-Level Integration Tests:** For a FastAPI service, the most valuable integration test makes an HTTP request to an endpoint and asserts on the HTTP response and any resulting side-effects (e.g., a database record was created). This simultaneously tests routing, dependency injection, serialization, business logic, and infrastructure interaction.

  * **Snapshot/Approval Testing:** For complex JSON responses, manual assertions are brittle. We will use snapshot testing (e.g., with `syrupy` for pytest) to verify the entire response payload. The test simply compares the current output to a stored "snapshot." This makes tests easier to write and forces a conscious review of any changes to the API's data structure.

```python
def test_processing_endpoint_with_cache(client, snapshot):
    """
    This is a behavior-focused integration test. It drives the system
    via the API and verifies the final, observable output.
    """
    # 1. First call populates the cache
    client.post("/v1/process", json={"text": "A long article to summarize.", "operation": "summarize"})
    
    # 2. Second call should be faster and hit the cache
    response = client.post("/v1/process", json={"text": "A long article to summarize.", "operation": "summarize"})
    
    # 3. Assert on the behavior and the exact output
    assert response.status_code == 200
    assert response.json() == snapshot
```

*In this example, the test doesn't know or care *how* the caching is implemented. It only verifies the integrated behavior: the correct data is returned. The snapshot assertion provides a powerful, low-maintenance way to lock in the API contract.*

### Principle 4: Identify and Test Critical Seams

Think of "seams" as the meaningful boundaries between different parts of our system. Here are four repeatable ways to find them.

#### **Start at the Application Boundary (The "Outside-In" Method) 🚪**

This is the most valuable strategy. Look at every way the outside world interacts with our application. Each entry point is a primary seam for a high-value integration test.

  * **API Endpoints:** Every `POST`, `PUT`, or `GET` endpoint that triggers a multi-step business process is a seam. The test should make an HTTP request and verify the outcome (the response, a database change, a message published, etc.).
  * **Message Queue Consumers:** If a service listens to a RabbitMQ or Kafka queue, the seam is the act of processing a message. The test should place a message on the queue and assert that the correct actions were taken.
  * **Scheduled Jobs:** A function triggered by a cron scheduler is another entry point. The test should invoke the job and check for its side effects.

#### **Identify Infrastructure Abstractions (The "Contract" Method) 📝**

This strategy focuses on where our application logic talks to infrastructure like databases, caches, or file storage. As per our philosophy, these interactions should happen through an interface (an Abstract Base Class).

  * **The Seam is the Interface:** The seam isn't the specific Redis or PostgreSQL client library; it's the `CacheInterface` or `RepositoryInterface` we've defined.
  * **How to Test:** We write a "contract test" for the interface, and then run it against a real implementation (e.g., a `RedisCache` class that uses a real Redis container). This verifies that our component's use of the infrastructure is correct.

#### **Follow a Critical Piece of Data (The "Data Flow" Method) 🗺️**

Pick a core piece of data in our system (e.g., a "user," an "order," a "processing job") and trace its journey. Every time it's handed off from one major component to another, we've found a seam.

**Example Journey:**
  1.  An API endpoint receives a request and creates a `Job` object.
  2.  The API controller passes the `Job` to a `ProcessingService`. **(Seam 1)**
  3.  The `ProcessingService` uses a `CacheService` to check for existing results. **(Seam 2)**
  4.  The `ProcessingService` saves the final result using a `JobRepository`. **(Seam 3)**

An integration test could cover the entire flow from step 1 to 4, verifying that all the components collaborate correctly to move the `Job` through its lifecycle.

#### **Use `import` Statements as Indicators**

`import` statements are a great **indicator** of a seam, but they aren't the seam itself.

Think of it this way: If our component `api.py` has the line `from my_app.services.processing import ProcessingService`, it's declaring a **dependency**. This is a signal that the API controller's behavior depends on the `ProcessingService`.

  * **Focus on `from` imports within a component.** These tell us what other internal components it relies on.
  * We don't need to worry about "to" imports. The integration test should focus on making the component under test collaborate with its dependencies.
  * The goal is **not** to test the `import` itself, but to test the **interaction** that the import enables. The test for the `api` would call the endpoint and, by doing so, implicitly test its collaboration with the real `ProcessingService`.

## Distinctions Between Test Categories

### Table: Testing Categories At-a-Glance

This table clarifies the distinct role of integration tests within our established categories.

| Test Category           | Purpose                                                                 | Scope & Scope Boundary                                                                | Mocking/Faking Strategy                                                                         |
| ----------------------- | ----------------------------------------------------------------------- | ------------------------------------------------------------------------------------- | ----------------------------------------------------------------------------------------------- |
| **Unit Tests** | Verify a single component fulfills its **contract** in isolation.         | A single class or module. The boundary is the component's public methods.             | Mock external systems (APIs). **Strictly no mocking of internal collaborators.** Use in-memory fakes. |
| **Integration Tests** | Verify the **collaborative behavior** of internal components.           | Two or more internal components, often spanning the full stack from API to database.  | Use high-fidelity fakes (`fakeredis`) or real infrastructure (Testcontainers). Minimal mocking.  |
| **Functional/E2E Tests** | Verify a **user journey** or business workflow meets requirements.        | The entire deployed system, from a user's perspective (e.g., HTTP client).         | Mock only true third-party external services (e.g., LLM APIs, payment gateways).                |
| **Manual Tests** | Verify integration with **real, live external services**.               | The live, deployed application communicating over the network to production services. | None. Uses real API keys and network access.                                                    |

### A Spectrum of Collaboration: Integration, E2E, and Manual Tests

We can view **Integration, E2E, and Manual tests as existing on a spectrum**. Their shared DNA is that they all test the **collaboration of multiple components**. The primary variable that distinguishes them is, as we said, the **boundary condition**—essentially, how much of the "real world" we let into the test.

We can visualize it as a series of expanding concentric circles:

1.  **🎯 Integration Tests (The Innermost Circle):**
    * **Boundary:** Our application's internal components.
    * **Goal:** Verify that *our code* works with *our other code* and its immediate infrastructure (like our database).
    * **Excludes:** All true external, third-party network dependencies.

2.  **🌐 E2E/Functional Tests (The Middle Circle):**
    * **Boundary:** Our application + its automated connections to external services.
    * **Goal:** Verify that a complete, automated user journey works across services.
    * **Excludes:** The unpredictability of human interaction and live production environments.

3.  **🌍 Manual Tests (The Outermost Circle):**
    * **Boundary:** Our application + its live connections in a real environment.
    * **Goal:** Verify that the system works in the messy, unpredictable real world, often involving human validation.
    * **Excludes:** Nothing. This is the final check against reality.

All three are fundamentally about ensuring that pieces connect and communicate correctly, just with an ever-increasing scope of what "pieces" are included.

### Behavioral Unit Tests: A Different Category

**Behavioral unit tests are a whole different thing**. Their defining characteristic is **isolation**.

While the other three types are about connection and collaboration, a unit test is about **proving the contract of a single component in a vacuum**. It answers a fundamentally different question: "Does this one specific component do its job correctly, assuming all its dependencies work?"

| | **Integration/E2E/Manual Tests** | **Behavioral Unit Tests** |
| :--- | :--- | :--- |
| **Core Principle** | **Collaboration** | **Isolation** |
| **Question Asked** | "Do these pieces work **together**?" | "Does this one piece work **by itself**?" |
| **Scope** | Two or more components | A single, isolated component |
| **Dependencies** | Uses real or high-fidelity fakes | Uses low-fidelity fakes or mocks |

We have one category of tests dedicated to verifying isolated components (Unit Tests) and another category—a spectrum, really—dedicated to verifying collaborative behavior under increasingly realistic conditions (Integration → E2E → Manual).

### Distinguishing Integration and E2E Tests: The System Boundary

There is one defining characteristic that separates integration tests from E2E/functional tests: the **system boundary** and how we treat **external dependencies**. Imagine a line drawn around the code we've written and control. The key difference between these test types is where they operate relative to that line.

The simplest way to think about it is that **integration tests** verify that *our* application's components work together correctly, while **E2E tests** verify that our application works correctly within its complete, real-world environment, including external services.

#### Integration Tests: Verifying our Internal World 🏠

An integration test draws the boundary tightly around **our application only**. It tests the full stack of *our* code—from the API layer, through our services, to our database—to ensure all our internal parts are wired together correctly.

* **Key Characteristic:** Any true third-party service (like an LLM API, a payment gateway, or an external identity provider) that our application depends on is **mocked, faked, or stubbed out**.
* **Purpose:** To confirm that if all the external services behave as we expect, our application does the right thing. It answers the question: "Is *my house* in order?"
* **Example:** We test our `/v1/process` endpoint. The test makes a real HTTP call to our running app, which then interacts with a real test database. However, when our `LLMService` tries to call the Gemini API over the network, the test intercepts that call and returns a pre-defined, canned response. We are testing our API, caching, and database logic *integrated together*, but we are *not* testing the actual Gemini service.

#### E2E/Functional Tests: Verifying the Real-World Workflow 🌍

An E2E test expands the boundary to include **both our application and its real external dependencies**. It aims to simulate a complete user journey from start to finish, exactly as it would happen in production.

* **Key Characteristic:** It makes **real network calls** to live, third-party services (using test accounts and API keys, of course). There is minimal to no mocking.
* **Purpose:** To confirm that the entire system, including the integration points with external services, works as a whole. It answers the question: "Does the entire user journey succeed in the real world?"
* **Example:** We test the same `/v1/process` endpoint. This time, the test provides a real (but sandboxed) Gemini API key. When our `LLMService` makes the call, it travels over the internet, hits Google's servers, gets processed by the real LLM, and returns a real result. We are testing our app's logic *plus* our authentication, network configuration, and contract with the live Gemini API.

#### Table: Integration Tests vs. E2E/Functional Tests At-a-Glance Comparison

| Feature                     | **Integration Test** | **End-to-End (E2E) / Functional Test** |
| --------------------------- | --------------------------------------------------------------------------------------------------------------------------- | --------------------------------------------------------------------------------------------------------------------------------------------- |
| **Primary Goal** | Verify that **our internal components** collaborate correctly.                                                             | Verify that a **complete user workflow** succeeds across the entire system.                                                                   |
| **Scope** | our application stack (e.g., API -> Service -> Database).                                                                  | our application stack **plus** real external services.                                                                                       |
| **Dependencies** | **Mocks/Fakes** are used for external services (LLM APIs, payment gateways). Real connections for internal infra (DB, cache). | **Real services** are used. The test makes actual network calls to third-party APIs using test credentials.                                   |
| **Key Question Answered** | "Does my code work together as designed?"                                                                                   | "Does the user's goal get accomplished in a production-like environment?"                                                                     |
| **Example for our App** | Call `/v1/process`. The test confirms a job is saved to the database, but the Gemini API call is mocked.                     | Call `/v1/process`. The test makes a real network call to the Gemini API and verifies the response is processed and saved to the database. |

### Distinguishing E2E and Manual Tests: The Role of Automation

The defining difference between End-to-End/Functional tests and Manual tests is **automation**. E2E/Functional tests are automated scripts, while Manual tests require a human to execute them.

This boundary is the clearest one in the entire testing suite. It's not about what is being tested (both can test the full application), but about *how* it's tested.

#### E2E / Functional Tests: Automated Verification

These are **code that tests our code**. They are written using a testing framework like `pytest` and are designed to be run automatically, typically by a CI/CD pipeline. Their purpose is to provide a consistent, repeatable, and fast check that critical user workflows have not broken. Because they are automated, they form a reliable regression safety net.

#### Manual Tests: Human-Driven Validation

These are **actions performed by a person**. They might follow a script or be exploratory. This category is reserved for scenarios that are either too costly, too complex, or too impractical to automate. This often includes verifying integrations with live, third-party services where we don't have a stable test environment or where real-world conditions (like network latency or variable API responses) are a key part of what we need to check.

#### Table: E2E/Functional vs. Manual Tests: At-a-Glance Comparison

| Feature | **E2E / Functional Test** | **Manual Test** |
| :--- | :--- | :--- |
| **Execution Method** | **Automated script** runs without human intervention (`pytest .`). | **Human operator** runs the test by making API calls or using the UI. |
| **Primary Goal** | **Continuous regression testing** of critical user journeys in a stable environment. | **Periodic validation** of live service integrations or exploratory testing. |
| **Dependencies** | Typically mocks true third-party services to ensure a consistent, repeatable test run. | **Uses real, live external services** with production or sandbox API keys. |
| **Frequency** | **High.** Run on every code change (e.g., in a CI/CD pipeline). | **Low.** Run before a release, after a major deployment, or to diagnose an issue. |
| **Key Question Answered** | "Did my recent code change break any existing user workflows?" | "Is our application still working correctly with the live version of the Gemini API right now?" |

## Practical Application: Strategies by Code Location

### Organizing Integration Tests

**The best practice is to have a top-level `tests/integration/` directory.**

Our test structure would look like this:

```
my_fastapi_app/
├── src/
│   ├── api/
│   │   └── v1/
│   │       └── endpoints.py
│   └── services/
│       └── processing.py
└── tests/
    ├── unit/              # Tests for single components in isolation
    │   ├── api/
    │   │   └── test_endpoints_unit.py
    │   └── services/
    │       └── test_processing_unit.py
    │
    ├── integration/       # <-- YOUR INTEGRATION TESTS LIVE HERE
    │   └── test_processing_flow.py
    │   └── test_cache_contract.py
    │
    └── conftest.py        # Shared fixtures (e.g., db connections)
```

**Why this structure is better:**

1.  **Mental Model:** It reinforces that integration tests are about **flows and collaborations**, not individual components. A test named `test_complete_summarization_flow.py` makes more sense here than in a `tests/services/` folder.
2.  **Clear Separation:** We can easily run different types of tests. `pytest tests/unit` runs our fast, isolated tests. `pytest tests/integration` runs the slower tests that may spin up database containers.
3.  **Reduces Confusion:** It prevents the question of "Does this integration test belong with the API tests or the service tests?" The answer is neither; it belongs with other tests that verify the integration *between* them.

### Strategy for API Layer Code (`/api`)

For `backend/app/api` code, we should overwhelmingly favor **collaborative** Integration and E2E tests. There is a very limited, almost negligible, role for isolated behavioral unit tests.

#### Why We Favor Collaborative Tests

Our API layer, by its very nature, is an **orchestration and integration layer**. Its primary job is not to perform complex business logic, but to connect the outside world (HTTP) to our internal services.

Looking at our `api/v1/text_processing.pyi` contract, the `process_text` endpoint's core responsibilities are:

1.  Receive an HTTP request.
2.  Deserialize and validate the `TextProcessingRequest` schema (handled by FastAPI).
3.  Invoke the `TextProcessorService` dependency (`Depends(get_text_processor)`).
4.  Serialize the `TextProcessingResponse` (handled by FastAPI).

The most valuable thing we can test here is the **entire collaboration**. An isolated unit test where we mock the `text_processor` dependency would only confirm that our endpoint calls the mock. This is a brittle implementation test that provides very little confidence.

An **integration test** that sends a real HTTP request to the endpoint and uses a real (or high-fidelity fake) `TextProcessorService` instance verifies the entire chain: routing, dependency injection, the service call, and the response serialization. This is where we get the highest return on our testing investment.

#### The Limited Role for Isolated Unit Tests (1% of cases)

There are very rare situations where an API endpoint might contain a piece of pure, stateless logic that is complex enough to warrant an isolated unit test. This logic must be self-contained within the API module and have no external dependencies (like services or databases).

**When we might consider a unit test for API code:**

1.  **Complex Request Transformation:** If we were to transform a raw request into a more complex domain model *before* passing it to the service, and that transformation logic is intricate.
2.  **Intricate, Self-Contained Logic:** If an endpoint had complex conditional logic based solely on query parameters or headers that didn't involve calling other services.

**Example of a (Rare) Justifiable API Unit Test:**

Imagine an endpoint that constructs a complex search query object from multiple optional query parameters before passing it to a search service.

```python
# In an API file like api/v1/search.py
def _build_search_filter(q: str | None, a_min: int = 0, a_max: int = 100) -> dict:
    # ... some complex logic to build a filter dictionary ...
    # This function is pure and has no dependencies.
    ...

@router.get("/search")
async def search_items(
    q: str | None = None,
    # ... other params
    search_service: SearchService = Depends(...)
):
    search_filter = _build_search_filter(q, ...)
    results = await search_service.find(search_filter)
    return results

# In tests/unit/api/v1/test_search.py
def test_build_search_filter_handles_complex_query():
    # This is a valid unit test because it tests pure, isolated logic.
    result = _build_search_filter(q="test", a_min=10)
    assert result == {"query": "test", "range": {"a": {"min": 10, "max": 100}}}
```

For our current API contracts, this scenario does not appear to exist. Our endpoints correctly delegate all real work to dependencies. **Therefore, for our current structure, we should focus exclusively on integration and E2E tests for the API layer.**

### Strategy for Infrastructure Layer Code (`/infrastructure`)

#### Example: `api/v1/auth` and `infrastructure/security/auth`

This is a perfect example of where a **collaborative integration test** is the correct and most effective approach.

We've correctly identified the relationship:

  * **Consumer:** `backend/app/api/v1/auth.py` contains the `auth_status` endpoint.
  * **Provider:** `backend/app/infrastructure/security/auth.py` provides the `verify_api_key_http` dependency.
  * **The "Seam":** The `Depends(verify_api_key_http)` in the endpoint's signature.

The goal is to verify that this seam is wired correctly and that the provider (`verify_api_key_http`) effectively protects the consumer (`auth_status`).

We do this by writing an integration test that **tests from the outside-in**, through the HTTP boundary. We do **not** mock the dependency.

Here is how we would structure these tests, following the philosophy we've established.

```python
# tests/integration/api/v1/test_auth_integration.py

import pytest
from fastapi.testclient import TestClient
from app.main import app  # Import our main FastAPI app

client = TestClient(app)

# Assume our settings are configured with a valid API key for testing, e.g., 'test-key'
VALID_API_KEY = "test-key"
INVALID_API_KEY = "invalid-key"

def test_auth_status_success_with_valid_key():
    """
    Given: A valid API key provided in the Authorization header
    When:  The /v1/auth/status endpoint is called
    Then:  The response should be 200 OK with authenticated status.
    """
    response = client.get(
        "/v1/auth/status",
        headers={"Authorization": f"Bearer {VALID_API_KEY}"}
    )

    assert response.status_code == 200
    data = response.json()
    assert data["authenticated"] is True
    assert data["api_key_prefix"].startswith("test-key") # Or the first 8 chars
    assert "Authentication successful" in data["message"]

def test_auth_status_fails_with_invalid_key():
    """
    Given: An invalid API key provided in the Authorization header
    When:  The /v1/auth/status endpoint is called
    Then:  The response should be 401 Unauthorized.
    """
    response = client.get(
        "/v1/auth/status",
        headers={"Authorization": f"Bearer {INVALID_API_KEY}"}
    )

    assert response.status_code == 401
    # We can also assert on the error response body if we have a standard error schema
    assert "Authentication Error" in response.text

def test_auth_status_fails_with_no_key():
    """
    Given: No API key is provided
    When:  The /v1/auth/status endpoint is called
    Then:  The response should be 401 Unauthorized.
    """
    response = client.get("/v1/auth/status")
    
    assert response.status_code == 401
    assert "Not authenticated" in response.text # Or similar default FastAPI error

def test_auth_status_success_with_x_api_key_header():
    """
    Given: A valid API key provided in the X-API-Key header
    When:  The /v1/auth/status endpoint is called
    Then:  The response should be 200 OK with authenticated status.
    (This tests the flexibility of our auth dependency)
    """
    response = client.get(
        "/v1/auth/status",
        headers={"X-API-Key": VALID_API_KEY}
    )
    
    assert response.status_code == 200
    data = response.json()
    assert data["authenticated"] is True

```

**Why This Approach Works:**

  * **High Confidence:** This single test file verifies everything: routing, the `Depends` mechanism, the logic inside `verify_api_key_http`, and the logic inside the `auth_status` endpoint itself. If these tests pass, the endpoint is secure.
  * **Resilience to Refactoring:** We could completely refactor the implementation of `verify_api_key_http` (e.g., switch from a simple set lookup to a database call). As long as it still correctly validates the key from the header, these integration tests will **continue to pass** without any changes.
  * **No Brittle Mocks:** We are not asserting that a mock was called. We are asserting the **observable behavior** of the system: a request with a valid key gets a 200, and one without gets a 401. This is the contract we care about.

#### Example: `infrastructure/security/auth` and `core/environment`

The relationship between `backend/app/infrastructure/security/auth.py` and `backend/app/core/environment.py` is a classic and vital seam.

  * **Consumer:** `auth.py` consumes environment information to make critical security decisions.
  * **Provider:** `environment.py` provides a standardized way to determine the current operating environment.
  * **The Seam:** The function call to `get_environment_info()` within the `APIKeyAuth` class is the point of connection. The behavior of the `auth` component fundamentally changes based on the data that crosses this seam.

#### The Role of the Unit Test (Mocking the Seam)

In the unit tests for `auth` we mocked the production environment response:

```python
@pytest.fixture
def mock_production_environment(mock_environment_detection):
    """
    Pre-configured mock for production environment detection.

    Configures the environment detection mock to return production environment
    with high confidence, useful for testing production security enforcement.

    Returns:
        Mock configured to return:
        - environment: Environment.PRODUCTION
        - confidence: 0.95
        - reasoning: "Production deployment detected"

    Use Cases:
        - Testing production security validation
        - Testing API key requirement enforcement
        - Testing production-specific error messages
    """
    class MockEnvironmentInfo:
        def __init__(self):
            self.environment = Environment.PRODUCTION
            self.confidence = 0.95
            self.reasoning = "Production deployment detected"

    mock_environment_detection.return_value = MockEnvironmentInfo()
    return mock_environment_detection
```

The goal of that unit test is to answer the question: "**Given that the `APIKeyAuth` class *knows* it is in production, does it correctly enforce that API keys must be configured?**"

By mocking the response from `get_environment_info`, we achieve perfect isolation. We are not testing the environment detection logic itself; we are testing the `APIKeyAuth` class's reaction to the *outcome* of that logic. This allows we to test its behavior deterministically under various conditions (production, development, etc.) without manipulating global state like environment variables.

#### The Role of the Integration Test (Exercising the Seam)

This is where our second point comes in, and it is spot on. The goal of the **integration test** is to answer the question: "**Does our environment detection logic correctly trigger the production security enforcement in our authentication component?**"

Here, we absolutely want to use the live, un-mocked code for both components. The test involves manipulating the *inputs* to the `environment` module (the actual environment variables) and asserting on the *observable behavior* of the `auth` module.

Here is what that integration test would look like in practice:

```python
# tests/integration/security/test_auth_environment_integration.py

import pytest
from app.infrastructure.security.auth import APIKeyAuth
from app.core.exceptions import ConfigurationError

def test_auth_in_production_enforces_api_keys(monkeypatch):
    """
    Given: The environment is set to 'production'
    And:   No API keys are configured
    When:  The APIKeyAuth class is initialized
    Then:  A ConfigurationError should be raised, enforcing the security policy.
    """
    # Manipulate the input to the 'environment' module
    monkeypatch.setenv("ENVIRONMENT", "production")
    
    # Clear any potentially configured API keys for this test
    monkeypatch.delenv("API_KEY", raising=False)
    monkeypatch.delenv("ADDITIONAL_API_KEYS", raising=False)

    # Exercise the seam and assert on the collaborative behavior
    with pytest.raises(ConfigurationError) as exc_info:
        # This call will trigger get_environment_info() inside the APIKeyAuth constructor
        APIKeyAuth()
        
    assert "API keys must be configured in a production environment" in str(exc_info.value)

def test_auth_in_development_allows_no_keys(monkeypatch):
    """
    Given: The environment is set to 'development'
    And:   No API keys are configured
    When:  The APIKeyAuth class is initialized
    Then:  It should initialize successfully and enter development mode.
    """
    # Manipulate the input to the 'environment' module
    monkeypatch.setenv("ENVIRONMENT", "development")

    # Clear any potentially configured API keys
    monkeypatch.delenv("API_KEY", raising=False)
    monkeypatch.delenv("ADDITIONAL_API_KEYS", raising=False)

    # Exercise the seam and assert on the outcome
    # This should NOT raise an error
    auth_handler = APIKeyAuth()
    
    # We can verify the 'development mode' behavior
    assert auth_handler.verify_api_key("development") is True
    assert not auth_handler.api_keys # The set of configured keys should be empty
```

## Common Integration Testing Patterns

### Pattern 1: Testing with High-Fidelity Fakes

We prefer high-fidelity fakes (like `fakeredis`) over mocks for infrastructure components:

```python
# tests/integration/conftest.py
import pytest
from fakeredis import FakeStrictRedis
from app.infrastructure.cache import RedisCache

@pytest.fixture
def fake_redis_cache():
    """
    Provides a high-fidelity fake Redis for integration testing.
    
    This allows us to test real Redis operations without
    requiring a running Redis server.
    """
    client = FakeStrictRedis(decode_responses=True)
    return RedisCache(client)
```

### Pattern 2: Testing API to Database Flow

For testing complete data flows from API to database:

```python
def test_complete_processing_flow(client, test_database):
    """
    Test complete flow from API request to database persistence.
    
    Integration Scope:
        API endpoint -> Service layer -> Repository -> Database
    """
    # Submit processing request
    response = client.post("/v1/process", 
                          json={"text": "Test content", "operation": "summarize"})
    
    # Verify API response
    assert response.status_code == 200
    job_id = response.json()["job_id"]
    
    # Verify database persistence
    job = test_database.query(Job).filter_by(id=job_id).first()
    assert job is not None
    assert job.status == "completed"
    assert job.result is not None
```

### Pattern 3: Testing Resilience Patterns

Integration tests for circuit breakers, retries, and timeouts:

```python
def test_circuit_breaker_integration(cache_service, unreliable_backend):
    """
    Test that circuit breaker protects system from cascading failures.
    
    Seam Under Test:
        Integration between cache service and circuit breaker
    """
    # Cause backend failures to trip circuit breaker
    for _ in range(5):
        unreliable_backend.fail_next_request()
        try:
            cache_service.get("key")
        except ServiceUnavailableError:
            pass
    
    # Circuit should now be open
    with pytest.raises(CircuitBreakerOpenError):
        cache_service.get("another_key")
    
    # Wait for circuit to half-open
    time.sleep(circuit_breaker.reset_timeout)
    
    # Next successful call should close circuit
    unreliable_backend.succeed_next_request()
    result = cache_service.get("key")
    assert result is not None
```

### Pattern 4: Testing with Testcontainers

For tests requiring real infrastructure:

```python
from testcontainers.redis import RedisContainer

@pytest.fixture(scope="session")
def real_redis():
    """
    Provides a real Redis instance using Testcontainers.
    
    Use this for integration tests that need to verify
    actual Redis-specific behaviors.
    """
    with RedisContainer() as redis:
        yield redis.get_client()

def test_redis_specific_features(real_redis):
    """
    Test Redis-specific features that fakes might not support.
    """
    # Test Redis transactions
    pipe = real_redis.pipeline()
    pipe.set("key1", "value1")
    pipe.set("key2", "value2")
    pipe.execute()
    
    assert real_redis.get("key1") == "value1"
    assert real_redis.get("key2") == "value2"
```

## Integration Test Documentation Standards

> **📖 Comprehensive Documentation**: All integration tests follow the unified documentation standards outlined in [DOCSTRINGS_TESTS.md](../developer/DOCSTRINGS_TESTS.md). This ensures consistency across our test suite.

#### Essential Elements for Integration Test Docstrings:

```python
def test_cache_integration_with_resilience_patterns(self):
    """
    Test that caching integrates correctly with resilience patterns.
    
    Integration Scope:
        Tests collaboration between CacheService and CircuitBreaker components
        
    Seam Under Test:
        The boundary where cache operations are wrapped by resilience patterns
        
    Business Impact:
        Ensures system stability during cache failures and prevents cascading failures
        
    Test Strategy:
        - Verify cache operations are protected by circuit breaker
        - Confirm graceful degradation when cache is unavailable
        - Test recovery behavior when cache returns to healthy state
        
    Success Criteria:
        - Cache failures trigger circuit breaker after threshold
        - System continues operating without cache
        - Circuit breaker recovers when cache is healthy
    """
```

## Troubleshooting Integration Tests

### Common Issues and Solutions

#### Issue: Tests Pass Individually but Fail When Run Together

**Cause**: Test isolation problems, shared state between tests

**Solution**:
```python
# Use function-scoped fixtures to ensure fresh state
@pytest.fixture
def cache_service():
    """Create a fresh cache service for each test."""
    return CacheService()

# Clean up after tests
@pytest.fixture(autouse=True)
def cleanup_database(test_database):
    """Ensure database is clean before each test."""
    yield
    test_database.rollback()
    test_database.query(Job).delete()
    test_database.commit()
```

#### Issue: Integration Tests Are Too Slow

**Cause**: Using real infrastructure when fakes would suffice

**Solution**:
```python
# Use test markers to separate fast and slow tests
@pytest.mark.fast
def test_with_fake_redis(fake_redis_cache):
    """Fast test using fake Redis."""
    pass

@pytest.mark.slow
def test_with_real_redis(real_redis):
    """Slower test requiring real Redis."""
    pass

# Run only fast tests during development
# pytest -m fast tests/integration
```

#### Issue: Flaky Tests Due to Timing Issues

**Cause**: Race conditions, insufficient wait times

**Solution**:
```python
import asyncio
from tenacity import retry, stop_after_delay, wait_fixed

@retry(stop=stop_after_delay(5), wait=wait_fixed(0.5))
async def wait_for_condition(condition_func):
    """Retry until condition is met or timeout."""
    assert await condition_func()

# In test
async def test_eventual_consistency():
    # Trigger async operation
    await service.process_async(data)
    
    # Wait for eventual consistency
    await wait_for_condition(
        lambda: database.query(Result).filter_by(id=job_id).first() is not None
    )
```

#### Issue: Mock/Fake Behavior Doesn't Match Production

**Cause**: Oversimplified mocks or outdated fakes

**Solution**:
- Use high-fidelity fakes (e.g., `fakeredis` instead of custom mocks)
- Write contract tests that run against both fakes and real implementations
- Regularly update fake implementations to match production behavior
- Consider using Testcontainers for critical integration points

### Best Practices for Debugging Integration Test Failures

1. **Use Verbose Logging**:
```python
pytest tests/integration -v -s --log-cli-level=DEBUG
```

2. **Isolate the Failing Test**:
```python
pytest tests/integration/test_file.py::test_specific_test -v
```

3. **Check Test Order Dependencies**:
```python
# Run tests in random order to detect dependencies
pytest tests/integration --random-order
```

4. **Inspect Database State**:
```python
# Add debugging fixture
@pytest.fixture
def debug_db(test_database):
    """Helper to inspect database state during tests."""
    def dump_table(table_name):
        results = test_database.execute(f"SELECT * FROM {table_name}")
        for row in results:
            print(row)
    return dump_table
```

## Coding Assistant Integration

### Prompt 1: Identifying Integration Test Opportunities and Creating Test Plans

Use this prompt with your coding assistant to identify integration test opportunities and create comprehensive test plans:

````markdown
Analyze [CODEBASE/DIRECTORY/FILES] to identify integration test opportunities and create a comprehensive test plan following our integration testing philosophy.

**ANALYSIS OBJECTIVES:**
1. Identify critical seams between components that require integration testing
2. Map data flows that cross component boundaries
3. Find API endpoints that orchestrate multiple services
4. Locate infrastructure abstractions that need contract verification
5. Identify resilience patterns that require integration validation

**SEAM IDENTIFICATION METHODS:**
- Start at Application Boundaries: Find all API endpoints, message queue consumers, scheduled jobs
- Infrastructure Abstractions: Identify interfaces for cache, database, external services
- Data Flow Tracking: Follow critical domain objects through the system
- Import Analysis: Map dependencies between major components

**TEST PLAN OUTPUT FORMAT:**
For each identified integration point, provide:
1. SEAM NAME: Clear description of the integration boundary
2. COMPONENTS: List of components involved in the integration
3. CRITICAL PATH: The data/control flow being tested
4. TEST SCENARIOS: Specific scenarios to validate
5. INFRASTRUCTURE NEEDS: Required test fixtures (fakeredis, test DB, etc.)
6. PRIORITY: High/Medium/Low based on business criticality

**PRIORITIZATION CRITERIA:**
- HIGH: User-facing features, payment flows, authentication, data persistence
- MEDIUM: Caching layers, monitoring, non-critical workflows
- LOW: Admin features, reporting, nice-to-have optimizations

**EXAMPLE OUTPUT:**
```
INTEGRATION TEST PLAN

1. SEAM: API → TextProcessingService → Cache → Database
   COMPONENTS: /v1/process endpoint, TextProcessingService, RedisCache, JobRepository
   CRITICAL PATH: User request → Processing → Caching → Persistence
   TEST SCENARIOS:
   - Successful processing with cache hit
   - Successful processing with cache miss
   - Cache failure fallback to direct processing
   - Database persistence after processing
   INFRASTRUCTURE: fakeredis, test database
   PRIORITY: HIGH (core user feature)

2. SEAM: AuthMiddleware → SecurityService → EnvironmentDetector
   COMPONENTS: verify_api_key_http, APIKeyAuth, get_environment_info
   CRITICAL PATH: Request → Authentication → Environment-based rules
   TEST SCENARIOS:
   - Valid API key in production environment
   - Missing API key in production (should fail)
   - Development environment bypass
   INFRASTRUCTURE: None (in-memory)
   PRIORITY: HIGH (security critical)
```

**FOCUS ON:**
- Multi-component workflows that users depend on
- Infrastructure integration points
- Error handling and resilience patterns
- Security and authentication flows
- Performance-critical paths with caching/optimization

Generate a prioritized test plan that covers the most critical integration points first.
````

### Prompt 2: Implementing Integration Tests from Test Plan

Use this prompt to implement integration tests based on the identified test plan:

````markdown
Implement integration tests for [SPECIFIC SEAM/COMPONENT] following our integration testing philosophy and the test plan.

**IMPLEMENTATION PRINCIPLES:**
1. TEST FROM THE OUTSIDE-IN: Start from API endpoints or entry points
2. USE HIGH-FIDELITY FAKES: Prefer fakeredis, test containers over mocks
3. TEST BEHAVIOR, NOT IMPLEMENTATION: Verify observable outcomes
4. MAINTAIN TEST ISOLATION: Each test should be independent
5. DOCUMENT INTEGRATION SCOPE: Clear docstrings about what's being tested

**TEST STRUCTURE TEMPLATE:**
```python
class Test[IntegrationName]:
    """
    Integration tests for [describe the integration].
    
    Seam Under Test:
        [Component A] → [Component B] → [Component C]
        
    Critical Paths:
        - [Path 1]: [Description]
        - [Path 2]: [Description]
    """
    
    def test_[scenario]_[expected_outcome](self, [fixtures]):
        """
        Test [specific behavior] across [components].
        
        Integration Scope:
            [List components being integrated]
            
        Business Impact:
            [Why this integration matters]
            
        Test Strategy:
            - [Step 1]
            - [Step 2]
            - [Verification]
            
        Success Criteria:
            - [Observable outcome 1]
            - [Observable outcome 2]
        """
        # Arrange
        [setup test data and state]
        
        # Act
        [trigger the integration through entry point]
        
        # Assert
        [verify observable outcomes]
```

**FIXTURE REQUIREMENTS:**
- Use shared fixtures from conftest.py where available
- Create integration-specific fixtures for complex setups
- Prefer function-scoped fixtures for test isolation
- Use session-scoped fixtures only for expensive resources (test containers)

**COMMON PATTERNS TO USE:**

1. **API to Database Flow:**
```python
def test_api_persists_to_database(client, test_db):
    response = client.post("/endpoint", json=data)
    assert response.status_code == 200
    
    # Verify database state
    record = test_db.query(Model).filter_by(id=response.json()["id"]).first()
    assert record is not None
```

2. **Service Integration with Cache:**
```python
def test_service_uses_cache(service, fake_redis_cache):
    # First call - cache miss
    result1 = service.process("key")
    
    # Second call - cache hit
    result2 = service.process("key")
    
    # Verify same result (from cache)
    assert result1 == result2
    assert fake_redis_cache.get("key") is not None
```

3. **Resilience Pattern Integration:**
```python
def test_circuit_breaker_protects_service(service, unreliable_backend):
    # Trigger failures to open circuit
    for _ in range(threshold):
        unreliable_backend.fail_next_request()
        with pytest.raises(ServiceError):
            service.call_backend()
    
    # Circuit should be open
    with pytest.raises(CircuitOpenError):
        service.call_backend()
```

**AVOID:**
- Mocking internal component methods
- Testing implementation details
- Asserting on internal state
- Creating overly complex test setups
- Writing tests that depend on test execution order

Generate comprehensive integration tests that validate the critical paths identified in the test plan.
````

### Prompt 3: Converting Unit Tests to Integration Tests

Use this prompt when you need to elevate existing unit tests to integration tests:

````markdown
Convert unit tests in [FILE/DIRECTORY] to integration tests that validate real component interactions.

**CONVERSION STRATEGY:**
1. REMOVE MOCKS: Replace mocked dependencies with real or high-fidelity fake implementations
2. EXPAND SCOPE: Test from API/entry point rather than individual methods
3. VERIFY END-TO-END: Check final outcomes rather than intermediate calls
4. USE REAL INFRASTRUCTURE: Replace in-memory fakes with fakeredis/test DB where appropriate

**CONVERSION MAPPING:**
- Mock objects → Real service instances or high-fidelity fakes
- Method calls → API endpoint calls
- Return value checks → Database state verification
- Mock assertions → Observable outcome assertions
- In-memory state → Persistent state in test infrastructure

**EXAMPLE CONVERSION:**

FROM (Unit Test):
```python
def test_service_calls_cache(mock_cache):
    service = Service(cache=mock_cache)
    mock_cache.get.return_value = None
    
    service.process("key")
    
    mock_cache.get.assert_called_with("key")
    mock_cache.set.assert_called_once()
```

TO (Integration Test):
```python
def test_service_integrates_with_cache(client, fake_redis_cache):
    # First request - cache miss
    response1 = client.get("/api/resource/key")
    assert response1.status_code == 200
    
    # Verify cache was populated
    cached_value = fake_redis_cache.get("resource:key")
    assert cached_value == response1.json()
    
    # Second request - cache hit
    response2 = client.get("/api/resource/key")
    assert response2.json() == response1.json()
```

**MAINTAIN TEST VALUE:**
- Keep the core test intention
- Expand coverage to include integration points
- Add verification of side effects and state changes
- Ensure tests still run reasonably fast

Convert the tests while preserving their business value and expanding their scope to cover real integrations.
````

### Benefits of AI-Assisted Integration Testing

#### **For Test Identification:**
- Systematic analysis of codebase for integration points
- Consistent prioritization based on business value
- Complete coverage of critical paths
- Reduced chance of missing important seams

#### **For Test Implementation:**
- Consistent test structure and documentation
- Proper use of fixtures and test patterns
- Focus on behavior over implementation
- Faster test development with templates

#### **For Test Maintenance:**
- Clear documentation of integration scope
- Easy identification of what's being tested
- Consistent patterns make updates easier
- Better test resilience to refactoring

## Checklist for New Integration Tests

Before merging a new integration test, ensure it meets the following criteria:
- [ ] **Identifies a Critical Seam:** The test verifies a meaningful collaboration between two or more internal components.
- [ ] **Focuses on a Critical Path:** The user journey or data flow being tested provides significant business value.
- [ ] **Located Correctly:** The test file is located within the `tests/integration/` directory.
- [ ] **Tests from the Outside-In:** The test is initiated through a public boundary (e.g., an HTTP request to an endpoint).
- [ ] **Uses High-Fidelity Fakes/Infra:** The test avoids mocking internal collaborators, preferring high-fidelity fakes (`fakeredis`) or containerized services.
- [ ] **Asserts on Behavior:** The test asserts on observable outcomes (e.g., the HTTP response, a database state change), not on implementation details.
- [ ] **Follows Documentation Standards:** The test includes a comprehensive docstring that clearly defines its scope, the seam under test, and its business impact.