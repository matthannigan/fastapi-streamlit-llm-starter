---
sidebar_label: Testing
---

# Testing Guide

This document provides comprehensive information about the test suite for the FastAPI-Streamlit-LLM starter template.

## Overview

> **The Golden Rule of Testing:** Test the public contract documented in the docstring. **Do NOT test the implementation code inside a function.** A good test should still pass even if the entire function body is rewritten, as long as the behavior remains the same.

The test suite covers both backend and frontend components with the following types of tests:

- **Unit Tests**: Test individual functions and classes in isolation
- **Integration Tests**: Test component interactions and API endpoints
- **End-to-End Tests**: Test complete user workflows
- **Code Quality**: Linting, type checking, and formatting validation

### Testing Philosophy: Maintainable, Behavior-Driven Testing

This project emphasizes **maintainability over exhaustiveness** and **behavior over implementation** to create robust test suites that provide real confidence while remaining maintainable over time.

#### Core Testing Principles

Our testing strategy prioritizes tests that give us confidence that the system works correctly for users, not that every internal function executes in a specific way.

1. **Test Behavior, Not Implementation** - Focus on what the system should accomplish from an external observer's perspective
2. **Maintainability Over Exhaustiveness** - Better to have fewer, high-value tests than comprehensive low-value tests
3. **Mock Only at System Boundaries** - Minimize mocking to reduce test brittleness
4. **Fast Feedback Loops** - Tests should run quickly to enable continuous development

#### Test Maintenance Guidelines

Before writing or keeping a test, ask these critical questions:

1. **Fragility Check**: Will this test break if I refactor the implementation?
2. **Value Check**: Does this test verify behavior that users depend on?
3. **Deletion Test**: Would removing this test reduce our confidence in the system?
4. **Mock Check**: Am I mocking more than necessary to isolate the behavior?

If a test fails these checks, refactor or remove it.

#### Mock Hierarchy Strategy

Mock only at appropriate boundaries to maintain test value while ensuring reliability:

**Always Mock:**
- External APIs (LLM providers, third-party services)
- Network calls to external systems
- File system operations in unit tests

**Sometimes Mock:**
- Databases (mock for unit tests, use real instances for integration tests)
- Redis and other infrastructure (depending on test scope)
- Time-dependent operations (for deterministic testing)

**Rarely Mock:**
- Internal services and business logic
- Utility functions and helpers
- Domain-specific operations

#### Test Pyramid Strategy

```
        /\
       /E2E\      <- Few critical user journeys (5-10 tests)
      /------\
     /Integr. \   <- Component interactions (20-30 tests)
    /----------\
   /   Unit     \ <- Pure functions, utilities (50+ tests)
  /--------------\
```

**Focus Distribution:**
- **Unit Tests (50+)**: Pure functions, utilities, critical business logic
- **Integration Tests (20-30)**: Component interactions with minimal mocking
- **End-to-End Tests (5-10)**: Critical user journeys and workflows

#### Behavior-Focused Testing ✅

**Tests what the code should accomplish from an external observer's perspective:**

```python
# ✅ GOOD: Tests observable behavior
def test_user_service_creates_valid_user():
    """Test that user creation produces a valid user with required fields."""
    user_data = {"name": "John Doe", "email": "john@example.com"}
    
    user = user_service.create_user(user_data)
    
    # Tests external contract/behavior
    assert user.id is not None
    assert user.name == "John Doe"
    assert user.email == "john@example.com"  
    assert user.created_at is not None
    assert user.is_active is True

# ✅ GOOD: Tests error handling behavior
def test_user_service_rejects_invalid_email():
    """Test that invalid email addresses are properly rejected."""
    user_data = {"name": "John", "email": "invalid-email"}
    
    with pytest.raises(ValidationError) as exc_info:
        user_service.create_user(user_data)
        
    assert "email" in str(exc_info.value)
```

**Characteristics:**
- Tests external contracts and interfaces
- Focuses on inputs, outputs, and side effects
- Survives implementation changes
- Provides confidence that features work as intended
- Documents expected behavior for other developers

#### Implementation-Focused Testing ❌

**Tests how the code currently works internally:**

```python
# ❌ BAD: Tests internal implementation details  
def test_user_service_calls_validator_internally():
    """Test that create_user calls EmailValidator internally."""
    user_data = {"name": "John", "email": "john@example.com"}
    
    with patch('user_service.EmailValidator') as mock_validator:
        user_service.create_user(user_data)
        
        # Tests internal implementation, not external behavior
        mock_validator.validate.assert_called_once_with("john@example.com")

# ❌ BAD: Tests internal state that users can't observe
def test_user_service_caches_validation_results():
    """Test that validation results are stored in internal cache."""
    user_data = {"name": "John", "email": "john@example.com"}
    
    user_service.create_user(user_data)
    
    # Tests private implementation detail
    assert len(user_service._validation_cache) == 1
    assert "john@example.com" in user_service._validation_cache
```

**Problems:**
- Breaks when refactoring internal code
- Tests private methods and attributes
- Doesn't verify external functionality
- Creates brittle test suites
- Makes refactoring painful and expensive

#### Applying Behavior Focus to Common Scenarios

##### Testing API Endpoints

```python
# ✅ GOOD: Tests API contract behavior
def test_process_text_endpoint_returns_success(client):
    """Test that text processing endpoint returns expected response structure."""
    response = client.post("/api/v1/process", json={
        "text": "Sample text to process",
        "operation": "summarize"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert "result" in data
    assert "processing_time" in data
    assert len(data["result"]) > 0

# ❌ BAD: Tests internal implementation
def test_process_text_endpoint_calls_text_processor_service(client):
    """Test that endpoint calls TextProcessorService internally."""
    with patch('app.api.v1.text_processing.text_processor_service') as mock:
        client.post("/api/v1/process", json={"text": "test", "operation": "summarize"})
        mock.process.assert_called_once()
```

##### Testing Service Classes

```python
# ✅ GOOD: Tests service behavior and state changes
async def test_cache_service_stores_and_retrieves_data():
    """Test that cache service properly stores and retrieves data."""
    cache = CacheService()
    
    await cache.set("test_key", "test_value")
    result = await cache.get("test_key")
    
    assert result == "test_value"

# ✅ GOOD: Tests error handling behavior  
async def test_cache_service_handles_missing_keys():
    """Test that cache service returns None for missing keys."""
    cache = CacheService()
    
    result = await cache.get("nonexistent_key")
    
    assert result is None

# ❌ BAD: Tests internal Redis client usage
async def test_cache_service_uses_redis_client_correctly():
    """Test that cache service calls Redis client methods."""
    with patch('redis.asyncio.Redis') as mock_redis:
        cache = CacheService()
        await cache.set("key", "value")
        
        mock_redis.return_value.set.assert_called_once_with("key", "value")
```

##### Testing Resilience Patterns

```python  
# ✅ GOOD: Tests resilience behavior outcomes
async def test_circuit_breaker_fails_fast_when_open():
    """Test that circuit breaker fails immediately when open."""
    breaker = CircuitBreaker(failure_threshold=2, recovery_timeout=60)
    
    # Force circuit breaker to open state
    for _ in range(3):
        try:
            await breaker.call(lambda: exec('raise Exception("service down")'))
        except:
            pass
    
    # Should fail immediately without calling function
    start_time = time.time()
    with pytest.raises(CircuitBreakerOpenError):
        await breaker.call(lambda: "should not be called")
    
    # Verify it failed fast (under 100ms)
    assert time.time() - start_time < 0.1

# ❌ BAD: Tests internal state management
def test_circuit_breaker_updates_failure_count_correctly():
    """Test that circuit breaker increments internal failure counter."""
    breaker = CircuitBreaker(failure_threshold=2)
    
    try:
        breaker.call(lambda: exec('raise Exception("fail")'))
    except:
        pass
        
    # Tests private internal state
    assert breaker._failure_count == 1
```

#### Benefits of Behavior-Focused Testing

1. **Refactoring Safety**: Tests continue passing when you improve implementation
2. **Real Confidence**: Tests verify that features actually work for users
3. **Living Documentation**: Tests describe what the system should do
4. **Faster Development**: Less test maintenance during development
5. **Better API Design**: Forces you to think about external contracts

#### Transitioning to Behavior-Focused Tests

1. **Start with docstrings**: Write comprehensive behavior documentation first
2. **Test public interfaces**: Focus on public methods and API endpoints
3. **Think like a user**: What would external users expect this code to do?
4. **Test outcomes, not steps**: Verify results, not the process to get there
5. **Mock external dependencies only**: Don't mock your own internal code

## Test Structure

The testing architecture follows both the infrastructure vs domain service separation and a pragmatic organization focused on test purpose and maintainability:

### Recommended Test Organization

```
├── backend/
│   ├── tests/
│   │   ├── conftest.py              # Global fixtures and test configuration
│   │   ├── functional/              # User-facing functionality tests
│   │   │   ├── test_text_processing_flow.py    # End-to-end text processing workflows
│   │   │   ├── test_api_contracts.py           # API endpoint behavior contracts
│   │   │   └── test_user_workflows.py          # Complete user journey tests
│   │   ├── integration/             # Component interaction tests
│   │   │   ├── test_cache_with_api.py          # Cache integration with API layer
│   │   │   ├── test_resilience_patterns.py     # Resilience pattern interactions
│   │   │   └── test_ai_service_integration.py  # AI service with infrastructure
│   │   ├── unit/                    # Pure function and isolated component tests
│   │   │   ├── test_validators.py              # Input validation logic
│   │   │   ├── test_utilities.py               # Pure utility functions
│   │   │   └── test_config_parsing.py          # Configuration parsing logic
│   │   └── manual/                  # Tests requiring real services
│   │       ├── test_llm_integration.py         # Real LLM API integration
│   │       └── test_performance_benchmarks.py # Performance tests with real services
│   ├── pytest.ini                  # Simplified pytest configuration
│   └── requirements-dev.txt         # Testing dependencies
├── frontend/
│   ├── tests/
│   │   ├── test_api_client.py       # API client behavior and error handling
│   │   └── test_user_workflows.py   # User interaction flows and UI behavior
│   └── pytest.ini
└── Makefile                         # Test automation with category support
```

### Test Categories Explained

#### Functional Tests (User-Facing Behavior)
**Purpose**: Verify that the system works correctly from a user's perspective  
**Scope**: End-to-end workflows, API contracts, user journeys  
**Mocking**: Minimal - only external services (LLM APIs, external databases)  
**Examples**:
```python
def test_complete_text_processing_workflow(client):
    """Test the complete text processing workflow from request to response."""
    # User submits text for processing
    response = client.post("/v1/process", json={
        "text": "Sample article content...",
        "operation": "summarize", 
        "max_length": 100
    })
    
    # Verify user gets expected response structure
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["result"]) <= 100
    assert "processing_time" in data
```

#### Integration Tests (Component Interactions)
**Purpose**: Verify that system components work together correctly  
**Scope**: Service interactions, infrastructure integration, data flow  
**Mocking**: Selective - mock external systems but use real internal components  
**Examples**:
```python
def test_cache_integration_with_resilience(cache_service, circuit_breaker):
    """Test that caching works correctly with resilience patterns."""
    # Should cache successful results
    result1 = cache_service.get_or_compute("key1", lambda: "computed_value")
    assert result1 == "computed_value"
    
    # Should serve from cache on subsequent calls
    result2 = cache_service.get_or_compute("key1", lambda: "different_value")  
    assert result2 == "computed_value"  # Served from cache
```

#### Unit Tests (Pure Functions and Isolated Logic)
**Purpose**: Verify individual functions and classes in isolation  
**Scope**: Pure functions, business logic, validation, utilities  
**Mocking**: Heavy - isolate the unit under test completely  
**Examples**:
```python
def test_text_validator_rejects_empty_input():
    """Test that text validator properly rejects empty input."""
    validator = TextValidator(min_length=1, max_length=1000)
    
    result = validator.validate("")
    
    assert not result.is_valid
    assert "empty" in result.error_message.lower()
```

#### Manual Tests (Real Service Integration)
**Purpose**: Verify integration with real external services  
**Scope**: LLM API calls, performance benchmarks, smoke tests  
**Mocking**: None - uses real external services  
**Examples**:
```python
@pytest.mark.manual
def test_gemini_api_integration_smoke():
    """Smoke test to verify Gemini API integration works end-to-end."""
    # Requires real GEMINI_API_KEY and network access
    response = requests.post("http://localhost:8000/v1/process", 
                           headers={"X-API-Key": "test-key"},
                           json={"text": "Test input", "operation": "summarize"})
    
    assert response.status_code == 200
    assert response.json()["success"] is True
```

### Alternative: Current Detailed Structure

The existing detailed structure organized by architectural boundaries is also valid and provides more granular organization:

```
├── backend/
│   ├── tests/
│   │   ├── conftest.py            # Global test fixtures and configuration
│   │   ├── api/                   # API endpoint tests (dual-API structure)
│   │   │   ├── conftest.py        # API-specific fixtures
│   │   │   ├── v1/                # Public API tests (/v1/)
│   │   │   │   ├── test_main_endpoints.py
│   │   │   │   └── test_text_processing_endpoints.py
│   │   │   └── internal/          # Internal API tests (/internal/)
│   │   │       ├── test_admin_endpoints.py
│   │   │       ├── test_cache_endpoints.py
│   │   │       ├── test_monitoring_endpoints.py
│   │   │       └── test_resilience_*_endpoints.py
│   │   ├── core/                  # Core application functionality
│   │   │   ├── test_config.py
│   │   │   ├── test_dependencies.py
│   │   │   ├── test_exceptions.py
│   │   │   └── test_middleware.py
│   │   ├── infrastructure/        # Infrastructure service tests (>90% coverage)
│   │   │   ├── ai/               # AI infrastructure tests
│   │   │   ├── cache/            # Cache infrastructure tests
│   │   │   ├── monitoring/       # Monitoring infrastructure tests
│   │   │   ├── resilience/       # Resilience pattern tests
│   │   │   └── security/         # Security infrastructure tests
│   │   ├── services/             # Domain service tests (>70% coverage)
│   │   │   ├── test_response_validator.py
│   │   │   └── test_text_processing.py
│   │   ├── integration/          # Cross-component integration tests
│   │   │   ├── test_auth_endpoints.py
│   │   │   ├── test_cache_integration.py
│   │   │   ├── test_end_to_end.py
│   │   │   └── test_resilience_integration*.py
│   │   ├── performance/          # Performance and load testing
│   │   │   └── test_cache_performance.py
│   │   ├── manual/               # Manual tests (require running server)
│   │   │   ├── test_manual_api.py
│   │   │   └── test_manual_auth.py
│   │   └── shared_schemas/       # Shared model tests
│   │       ├── test_common_schemas.py
│   │       └── test_text_processing_schemas.py
│   ├── pytest.ini                # Pytest configuration with markers
│   └── requirements-dev.txt      # Testing dependencies
├── frontend/
│   ├── tests/
│   │   ├── conftest.py           # Test fixtures and configuration
│   │   ├── test_api_client.py    # API client tests
│   │   └── test_config.py        # Configuration tests
│   ├── pytest.ini               # Pytest configuration
│   └── requirements-dev.txt     # Testing dependencies
├── scripts/
│   ├── run_tests.py             # Main test runner script
│   └── test_integration.py      # Comprehensive testing scenarios
├── Makefile                     # Test automation commands
└── .github/workflows/test.yml   # CI/CD pipeline
```

## Running Tests

### Quick Start

The project now includes automatic virtual environment management for testing. You can run tests without manually managing Python environments.

```bash
# Create virtual environment and install dependencies
make install

# Run all tests (includes Docker integration tests if available)
make test

# Run local tests only (no Docker required)
make test-local

# Run backend tests only
make test-backend

# Run frontend tests only
make test-frontend

# Run tests with coverage
make test-coverage
```

### Virtual Environment Management

The Makefile automatically handles Python executable detection and virtual environment management:

- **Automatic Python Detection**: Uses `python3` or `python` based on availability
- **Virtual Environment Creation**: Creates `.venv/` directory automatically
- **Dependency Management**: Installs all required dependencies in the virtual environment
- **Environment Awareness**: Detects if running in Docker, virtual environment, or system Python

```bash
# Create virtual environment (done automatically by make install)
make venv

# Install dependencies in virtual environment
make install

# Run tests without Docker dependency
make test-local

# Clean up virtual environment
make clean-all
```

### Detailed Commands

#### Backend Tests

```bash
# Using Makefile (recommended - handles virtual environment automatically)
make test-backend                       # Run fast tests (default)
make test-backend-all                   # Run all tests including slow ones
make test-backend-manual                # Run manual tests (requires running server)
make test-coverage                      # Run tests with coverage reporting

# Specific test categories
make test-backend-api                   # API endpoint tests
make test-backend-core                  # Core functionality tests  
make test-backend-infrastructure        # Infrastructure service tests
make test-backend-services              # Domain service tests
make test-backend-integration           # Integration tests
make test-backend-performance           # Performance tests

# Manual commands with virtual environment
cd backend

# Default: Run fast tests in parallel (excludes slow and manual tests)
../.venv/bin/python -m pytest tests/ -v

# Run specific test directories
../.venv/bin/python -m pytest tests/api/ -v                        # API endpoint tests
../.venv/bin/python -m pytest tests/core/ -v                       # Core functionality tests
../.venv/bin/python -m pytest tests/infrastructure/ -v             # Infrastructure service tests
../.venv/bin/python -m pytest tests/services/ -v                   # Domain service tests
../.venv/bin/python -m pytest tests/integration/ -v                # Integration tests
../.venv/bin/python -m pytest tests/performance/ -v                # Performance tests

# Run all tests including slow ones (excluding manual)
../.venv/bin/python -m pytest tests/ -v -m "not manual" --run-slow

# Run only slow tests (requires --run-slow flag)
../.venv/bin/python -m pytest tests/ -v -m "slow" --run-slow

# Run manual tests (requires running server and --run-manual flag)
../.venv/bin/python -m pytest tests/ -v -m "manual" --run-manual

# Run with coverage
../.venv/bin/python -m pytest tests/ --cov=app --cov-report=html --cov-report=term

# Run tests sequentially (for debugging)
../.venv/bin/python -m pytest tests/ -v -n 0

# Run specific test markers
../.venv/bin/python -m pytest tests/ -v -m "retry" --run-slow             # Retry logic tests
../.venv/bin/python -m pytest tests/ -v -m "circuit_breaker" --run-slow   # Circuit breaker tests
../.venv/bin/python -m pytest tests/ -v -m "no_parallel"                  # Tests that must run sequentially
```

#### Frontend Tests

```bash
# Using Makefile (recommended - handles virtual environment automatically)
make test-frontend

# Or manually with virtual environment
cd frontend
../.venv/bin/python -m pytest tests/ -v

# Run with coverage
../.venv/bin/python -m pytest tests/ --cov=app --cov-report=html
```

#### Integration Tests

```bash
# Using Makefile (recommended - handles Docker availability detection)
make test

# Using the test runner script with virtual environment
.venv/bin/python run_tests.py

# Manual Docker Compose testing
docker-compose up -d
# Wait for services to start
curl http://localhost:8000/health
curl http://localhost:8501/_stcore/health
docker-compose down

# Local testing without Docker
make test-local
```

## 🧪 Comprehensive Tests

### `scripts/test_integration.py`

Comprehensive testing suite that validates the entire system functionality.

**Test Categories:**
- 🏥 Core functionality tests
- 📝 Text processing operation tests
- 🚨 Error handling tests
- ⚡ Performance tests
- 🔄 Concurrent request tests

**Usage:**
```bash
python integration_test.py
```

**Test Results Example:**
```
📊 Test Results:
   Total Tests: 9
   ✅ Passed: 9
   ❌ Failed: 0
   📈 Success Rate: 100.0%
   ⏱️  Total Duration: 15.23s
   🕐 Average Test Time: 1.69s
```

### ⚡ Performance Considerations

#### Benchmarking Results
Typical performance metrics from `integration_test.py`:

| Operation | Avg Time | Success Rate |
|-----------|----------|--------------|
| Summarize | 2.1s     | 100%         |
| Sentiment | 1.8s     | 100%         |
| Key Points| 2.3s     | 100%         |
| Questions | 2.0s     | 100%         |
| Q&A       | 2.2s     | 100%         |

#### Optimization Tips
- Use appropriate `max_length` for summaries
- Batch similar operations when possible
- Implement caching for frequently requested content
- Monitor API rate limits

## Test Coverage Strategy

### Tiered Coverage Approach

This project follows a **tiered test coverage strategy** that prioritizes testing effort based on component criticality and user impact. Rather than applying uniform coverage requirements across all code, we focus intensive testing on components where failures matter most.

> ⚠️ **Warning: Principles Over Percentages**
> These coverage targets are guidelines, not mandates. A test suite that perfectly follows the 'Test Behavior, Not Implementation' principle at 80% coverage is far more valuable than a 95% coverage suite full of brittle, implementation-focused tests. **Never sacrifice test quality to meet a numeric target.

#### 🔴 Critical Components (90-100% line coverage)
**What:** User-facing APIs, core business logic, data integrity operations  
**Why:** Failures directly impact users and business operations  
**Testing Priority:** MUST test comprehensively  

**Examples:**
- **Public API endpoints** (`/api/v1/*`) - External user contracts
- **Core service methods** (`TextProcessor.process()`) - Business logic that affects outcomes
- **Authentication/authorization** - Security-critical operations
- **Data persistence operations** - Operations affecting data integrity

```python
# MUST test - user-facing API
@app.post("/api/v1/process")
async def process_text(request: ProcessRequest):
    return await text_processor.process(request.text)

# MUST test - core business logic  
class TextProcessor:
    async def process(self, text: str) -> ProcessedResult:
        # Business logic that affects user outcomes
```

#### 🟡 Important Components (70-85% line coverage)
**What:** Infrastructure services, configuration, resilience patterns  
**Why:** Failures cause degraded service but not complete failure  
**Testing Priority:** SHOULD test key behaviors, not all edge cases  

**Examples:**
- **Circuit breakers, retry logic** - Resilience infrastructure
- **Caching services** - Performance infrastructure  
- **Configuration validation** - System setup and validation
- **Health monitoring** - Operational visibility

```python
# SHOULD test key behaviors, not all edge cases
class CircuitBreaker:
    def call(self, func):
        # Test: works when healthy, fails over when broken
        # Don't test: exact state transition timing
```

#### 🟢 Supporting Components (40-60% line coverage)
**What:** Utilities, helpers, internal plumbing  
**Why:** Covered indirectly by higher-level tests  
**Testing Priority:** OPTIONAL testing - covered by integration tests  

**Examples:**
- **Logging utilities** - Cross-cutting concerns
- **Data formatting functions** - Pure transformation functions
- **Internal helper classes** - Supporting infrastructure
- **Environment detection** - System introspection

```python
# OPTIONAL testing - covered by integration tests
def format_response(data: dict) -> dict:
    return {"status": "success", "data": data}

# SKIP testing - pure utility
def get_timestamp() -> str:
    return datetime.now().isoformat()
```

#### ⚪ Skip Testing (0% direct coverage)
**What:** Framework code, external libraries, trivial functions  
**Examples:**
- **Property getters/setters** - No logic to test
- **Simple data classes** - Just containers
- **Third-party library wrappers** - Covered by library tests
- **Configuration constants** - Static values

### Component-Specific Coverage Requirements

#### Backend Infrastructure Services (70-90% coverage)
- **AI Infrastructure** (`app/infrastructure/ai/`) - 85% target
  - Input sanitization and prompt injection protection
  - Prompt builder utilities and AI provider abstractions
  - Focus on security-critical validation logic

- **Cache Infrastructure** (`app/infrastructure/cache/`) - 80% target
  - Redis and memory cache implementations
  - Cache monitoring and performance metrics
  - Graceful degradation patterns and fallback logic

- **Resilience Infrastructure** (`app/infrastructure/resilience/`) - 85% target
  - Circuit breaker pattern implementation
  - Retry mechanisms with exponential backoff
  - Orchestrator and configuration presets
  - Performance benchmarks

- **Security Infrastructure** (`app/infrastructure/security/`) - 90% target
  - Multi-key authentication system
  - Security validation and protection mechanisms

- **Monitoring Infrastructure** (`app/infrastructure/monitoring/`) - 75% target
  - Health check implementations
  - Metrics collection and alerting

#### Domain Services (60-75% coverage) 
*Educational examples - replace with your business logic*

- **Text Processing Service** (`app/services/text_processor.py`) - 70% target
  - AI text processing using PydanticAI agents
  - Business-specific processing logic (educational examples)

- **Response Validator** (`app/services/response_validator.py`) - 65% target
  - Business-specific response validation logic

#### API Endpoints (90-95% coverage)
- **Public API** (`/v1/`) - 95% target
  - Authentication validation and user-facing contracts
  - Health checks and core processing operations
  - Error handling and CORS configuration

- **Internal API** (`/internal/`) - 90% target
  - Cache management endpoints (38 resilience endpoints)
  - Monitoring and metrics collection
  - Resilience management across 8 modules

#### Core Components (90-95% coverage)
- **Configuration Management** (`app/core/config.py`) - 95% target
  - Dual-API configuration and preset-based resilience system
  - Security and infrastructure settings

- **Dependency Injection** (`app/dependencies.py`) - 90% target
  - Service provider patterns and preset-based configuration loading

#### Shared Models (95-100% coverage)
- **Pydantic Models** (`shared/models.py` and `app/schemas/`) - 100% target
  - Cross-service data models and field validation
  - Serialization/deserialization contracts

### Practical Coverage Targets

#### By Test Type
- **Unit Tests:** 60-80% line coverage (focused on critical paths)
- **Integration Tests:** Cover key workflows end-to-end
- **API Tests:** 100% endpoint coverage, 80% scenario coverage

#### Overall Project Target
**Target: 70-80% overall line coverage**
- High enough to catch most bugs
- Low enough to avoid testing trivia
- Focuses effort on valuable tests
- Allows for some untested utility code

### Coverage Quality Metrics

**Quality Metrics (More Important Than Coverage Percentage):**
- **Bug Detection Rate:** Do tests catch real issues before production?
- **Test Maintenance Time:** How often do tests break during refactoring?
- **Confidence Level:** Do you feel safe deploying with these tests?
- **Development Speed:** Do tests help or hinder feature development?

### Coverage Anti-Patterns to Avoid

#### ❌ Don't Do This
```python
# Testing implementation details
def test_internal_cache_structure():
    service = MyService()
    service._process_item("test")
    assert len(service._internal_cache) == 1

# Testing trivial functions
def test_add_numbers():
    assert add(2, 3) == 5

# Testing framework integration
def test_pydantic_model_validation():
    # Pydantic already tests this
    with pytest.raises(ValidationError):
        MyModel(invalid_field="bad")
```

#### ✅ Do This Instead
```python
# Testing behavior contracts
def test_service_processes_valid_input():
    service = MyService()
    result = service.process("valid input")
    assert result.status == "success"
    assert "processed" in result.data

# Testing error handling
def test_service_handles_invalid_input():
    service = MyService()
    result = service.process("invalid input")
    assert result.status == "error"
    assert result.error_message is not None
```

### Implementation Strategy

1. **Start with current coverage baseline**
2. **Identify your critical paths** (user-facing features)
3. **Set coverage floors** for each component type
4. **Delete low-value tests** to focus effort
5. **Measure quality, not just quantity**
6. **Focus on behavior testing over implementation testing**

### Pragmatic Testing Categories & Goals

Different parts of the system require different testing approaches based on their criticality and user impact:

| Category | Coverage Target | Focus | Example | Testing Approach |
|----------|----------------|-------|---------|------------------|
| **Critical User Paths** | 90%+ | End-to-end behavior | Text processing workflow | Integration tests with real data flows |
| **API Endpoints** | 80%+ | Request/response contracts | Status codes, response structure | Contract testing with edge cases |
| **Business Logic** | 70%+ | Core functionality | Text processing operations | Unit tests with behavior focus |
| **Infrastructure** | 50%+ | Basic configuration | Can it start? Does config load? | Smoke tests and health checks |
| **Utilities** | 30%+ | Pure functions only | Validation helpers | Unit tests for complex logic only |

### Handling LLM Non-Determinism

LLM outputs are inherently non-deterministic, requiring specialized testing strategies:

#### 1. Mock LLM Calls in Most Tests
Use predictable responses for testing application logic:

```python
@pytest.fixture
def mock_llm():
    """Mock LLM for predictable testing."""
    with patch('app.services.ai_provider.call') as mock:
        # Return predictable, valid responses
        mock.return_value = "Mocked LLM response for testing"
        yield mock

def test_text_processing_workflow(client, mock_llm):
    """Test processing workflow with predictable LLM response."""
    response = client.post("/v1/process", json={
        "text": "Sample input text", 
        "operation": "summarize"
    })
    
    assert response.status_code == 200
    assert "result" in response.json()
    # Can test exact response structure since LLM is mocked
```

#### 2. Evaluation-Based Testing
For real LLM tests, check properties rather than exact matches:

```python
@pytest.mark.manual
def test_llm_summarization_properties(real_llm_client):
    """Test that real LLM summarization has expected properties."""
    long_text = "Very long article text..." * 100
    
    result = real_llm_client.summarize(long_text, max_length=100)
    
    # Test properties, not exact content
    assert len(result) <= 100
    assert len(result) >= 50  # Not too short
    assert "summary" in result.lower() or any(word in result for word in ["main", "key", "important"])
    assert result != long_text  # Actually summarized
```

#### 3. Snapshot Testing
Save and compare outputs for regression detection:

```python
def test_llm_response_format_stability(snapshot, mock_llm):
    """Test that LLM response format remains stable."""
    mock_llm.return_value = "Consistent test response"
    
    response = process_text("test input", "summarize")
    
    # Will fail if response structure changes
    snapshot.assert_match(response.dict(), "llm_response_format.json")
```

#### 4. Manual Verification Tests
Small set of tests with real LLM calls for smoke testing:

```python
@pytest.mark.manual
def test_gemini_integration_smoke():
    """Smoke test to verify Gemini integration works end-to-end."""
    # Requires GEMINI_API_KEY and running server
    response = requests.post("http://localhost:8000/v1/process", json={
        "text": "This is a simple test of the AI integration.",
        "operation": "summarize"
    })
    
    assert response.status_code == 200
    data = response.json()
    assert data["success"] is True
    assert len(data["result"]) > 10  # Got some meaningful response
```

### Frontend Coverage

The frontend test suite covers:

- **API Client** (85%+ coverage)
  - HTTP request handling
  - Error handling
  - Response parsing
  - Timeout handling

- **Configuration** (100% coverage)
  - Environment variable handling
  - Default values
  - Settings validation

## Test Configuration

### Pytest Configuration

The backend uses pytest with parallel execution and comprehensive markers:

```ini
[pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -n auto                    # Parallel execution with auto-detection
    --dist worksteal          # Work-stealing load balancing
    -v                        # Verbose output
    --strict-markers          # Strict marker validation
    --tb=short               # Short traceback format
    --asyncio-mode=auto      # Automatic async support
    -m "not slow and not manual"  # Exclude slow and manual tests by default
asyncio_default_fixture_loop_scope = function
markers =
    asyncio: marks tests as async
    slow: marks tests as slow (deselect with '-m "not slow"')
    manual: marks tests as manual (deselect with '-m "not manual"')
    integration: marks tests as integration tests
    retry: marks tests that test retry logic specifically
    circuit_breaker: marks tests that test circuit breaker functionality
    no_parallel: marks tests that must run sequentially (not in parallel)
filterwarnings =
    ignore::DeprecationWarning
    ignore::PendingDeprecationWarning
    ignore::pytest.PytestDeprecationWarning
```

The frontend uses a simpler configuration:

```ini
[tool:pytest]
testpaths = tests
python_files = test_*.py
python_classes = Test*
python_functions = test_*
addopts = 
    -v
    --strict-markers
    --tb=short
    --asyncio-mode=auto
markers =
    asyncio: marks tests as async
```

### Test Fixtures

#### Backend Fixtures (`backend/tests/conftest.py`)

**Global Fixtures:**
- `client`: FastAPI test client for main application
- `internal_client`: FastAPI test client for internal API
- `async_client`: Async HTTP client for integration tests
- `sample_text`: Sample text for processing operations
- `sample_request`: Sample processing request data
- `mock_ai_agent`: Mocked AI agent (auto-used to avoid external API calls)
- `redis_client`: Redis client for cache testing
- `memory_cache`: In-memory cache for testing

**Infrastructure-Specific Fixtures** (`backend/tests/infrastructure/conftest.py`):
- `circuit_breaker`: Circuit breaker instance for testing
- `retry_policy`: Retry policy configuration for testing  
- `resilience_config`: Test resilience configuration
- `cache_service`: Cache service with test configuration
- `health_monitor`: Health monitoring service for testing

**API-Specific Fixtures** (`backend/tests/api/conftest.py`):
- `authenticated_client`: Test client with API key authentication
- `internal_api_client`: Test client for internal endpoints
- `mock_dependencies`: Mocked dependency injection for testing

#### Frontend Fixtures (`frontend/tests/conftest.py`)

- `api_client`: API client instance
- `sample_text`: Sample text for testing
- `sample_request`: Sample processing request
- `sample_response`: Sample API response

#### Fixture Documentation Best Practices

Fixtures should include comprehensive docstrings explaining their purpose, scope, and usage patterns:

```python
@pytest.fixture
def authenticated_user():
    """
    Provides a fully authenticated user for testing protected endpoints.
    
    User Profile:
        - Standard user permissions (not admin)
        - Active account status
        - Email verified
        - No special role assignments
        
    Use Cases:
        - Testing endpoints that require authentication
        - Verifying user-specific data access
        - Testing standard user workflows
        
    Cleanup:
        User session is automatically cleaned up after test completion
        
    Related Fixtures:
        - admin_user: For testing admin-only functionality
        - unverified_user: For testing email verification flows
    """
```

> **📖 Fixture Documentation Templates**: See **[DOCSTRINGS_TESTS.md](./DOCSTRINGS_TESTS.md)** section on "Fixture Documentation" for comprehensive fixture docstring patterns and examples.

## Mocking Strategy

**Anti-Patterns: What NOT to Mock in Unit Tests:**
* **Parent Classes**: Do not mock methods from a class's parent (e.g., `GenericRedisCache.set`).
* **Internal Helper Classes**: Do not mock internal collaborators (e.g., `CacheKeyGenerator`).
* **Private Methods**: Never test or mock private methods (e.g., `_decompress_data`).

### AI Service Mocking

The test suite uses comprehensive mocking for AI services to:

- Avoid external API calls during testing
- Ensure consistent test results
- Speed up test execution
- Test error scenarios and resilience patterns

```python
@pytest.fixture(autouse=True)
def mock_ai_agent():
    """Mock the AI agent to avoid actual API calls during testing."""
    with patch('app.services.text_processor.Agent') as mock:
        mock_instance = AsyncMock()
        mock_instance.run = AsyncMock(return_value=AsyncMock(data="Mock AI response"))
        mock.return_value = mock_instance
        yield mock_instance
```

### Infrastructure Service Mocking

Infrastructure tests use targeted mocking to test resilience patterns:

```python
# Circuit breaker testing
@pytest.fixture
def failing_service():
    """Mock service that fails to test circuit breaker behavior."""
    mock_service = AsyncMock()
    mock_service.call = AsyncMock(side_effect=Exception("Service unavailable"))
    return mock_service

# Cache testing with Redis fallback
@pytest.fixture
def redis_unavailable():
    """Mock Redis unavailability to test memory cache fallback."""
    with patch('redis.Redis') as mock_redis:
        mock_redis.side_effect = ConnectionError("Redis unavailable")
        yield mock_redis
```

### Environment Isolation

Tests use `monkeypatch.setenv()` for clean environment isolation:

```python
def test_resilience_preset_loading(monkeypatch):
    """Test preset loading with clean environment."""
    monkeypatch.setenv("RESILIENCE_PRESET", "production")
    # Test preset loading logic
```

### HTTP Client Mocking

Frontend tests mock HTTP clients to test different scenarios:

```python
async def test_health_check_success(self, api_client):
    """Test successful health check."""
    with patch('httpx.AsyncClient') as mock_client:
        mock_response = AsyncMock()
        mock_response.status_code = 200
        mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
        
        result = await api_client.health_check()
        assert result is True
```

## Code Quality Checks

### Linting

```bash
# Backend linting
cd backend
python -m flake8 app/
python -m mypy app/ --ignore-missing-imports

# Frontend linting
cd frontend
python -m flake8 app/
```

### Code Formatting

```bash
# Format all code (uses virtual environment automatically)
make format

# Manual formatting with virtual environment
cd backend
../.venv/bin/python -m black app/ tests/
../.venv/bin/python -m isort app/ tests/

cd ../frontend
../.venv/bin/python -m black app/ tests/
../.venv/bin/python -m isort app/ tests/
```

## Continuous Integration

### GitHub Actions

The project uses GitHub Actions for CI/CD with the following workflow:

1. **Test Matrix**: Tests run on Python 3.9, 3.10, and 3.11
2. **Dependency Installation**: Install both runtime and development dependencies
3. **Unit Tests**: Run all unit tests with coverage
4. **Code Quality**: Run linting and type checking
5. **Integration Tests**: Build and test with Docker Compose
6. **Coverage Upload**: Upload coverage reports to Codecov

### Local CI Simulation

```bash
# Run the same checks as CI (uses virtual environment automatically)
make ci-test

# Or manually with virtual environment:
cd backend
../.venv/bin/python -m pytest tests/ -v --cov=app --cov-report=xml
../.venv/bin/python -m flake8 app/
../.venv/bin/python -m mypy app/ --ignore-missing-imports

cd ../frontend
../.venv/bin/python -m pytest tests/ -v --cov=app --cov-report=xml
../.venv/bin/python -m flake8 app/
```

## Writing New Tests

### Docstring-Driven Test Development

This project promotes **docstring-driven test development**, where comprehensive function and class docstrings serve as specifications for generating focused, behavior-based tests. This approach creates tests that verify what functions *should do* rather than how they *currently work*.

> **📖 Comprehensive Docstring Guidance**: See **[DOCSTRINGS_CODE.md](./DOCSTRINGS_CODE.md)** for production code docstring standards and **[DOCSTRINGS_TESTS.md](./DOCSTRINGS_TESTS.md)** for test documentation templates and philosophy.

#### Core Principles

1. **TEST WHAT'S DOCUMENTED**: Only test behaviors, inputs, outputs, and exceptions mentioned in docstrings
2. **IGNORE IMPLEMENTATION**: Don't test internal methods, private attributes, or undocumented behavior  
3. **FOCUS ON CONTRACTS**: Test that the function fulfills its documented contract
4. **USE DOCSTRING EXAMPLES**: Convert docstring examples into actual test cases
5. **TEST EDGE CASES FROM DOCS**: If docstring mentions limits (1-50,000 characters), test the boundaries
6. **DON'T OVER-TEST**: If it's not in the docstring, it's probably not worth testing

#### Converting Docstrings to Tests

##### Input Contract Testing
**Rich Docstring:**
```python
def validate_config(config: dict) -> ValidationResult:
    """
    Validates AI service configuration.
    
    Args:
        config: Configuration dictionary with required keys:
               - 'model': str, one of ['gpt-4', 'claude', 'gemini']
               - 'timeout': int, 1-300 seconds
               - 'retries': int, 0-10 attempts
               Optional keys:
               - 'fallback_model': str, same options as 'model'
    
    Returns:
        ValidationResult containing:
        - is_valid: bool, True if config passes validation
        - errors: List[str], validation error messages if any
        
    Raises:
        TypeError: If config is not a dictionary
        
    Behavior:
        - Validates all required fields are present
        - Checks field value constraints and types
        - Returns detailed error messages for debugging
        - Accepts None values for optional fields
    """
```

**Generated Tests:**
```python
class TestValidateConfig:
    """Test config validation per docstring specification."""
    
    def test_validate_config_required_fields(self):
        """Test validation requires all mandatory fields per docstring."""
        minimal_config = {
            'model': 'gpt-4',
            'timeout': 30,
            'retries': 3
        }
        result = validate_config(minimal_config)
        assert result.is_valid
        assert len(result.errors) == 0

    def test_validate_config_invalid_model(self):
        """Test validation rejects invalid model names per docstring."""
        config = {'model': 'invalid-model', 'timeout': 30, 'retries': 3}
        result = validate_config(config)
        assert not result.is_valid
        assert any('model' in error for error in result.errors)
        
    def test_validate_config_timeout_boundaries(self):
        """Test timeout boundary conditions per docstring (1-300 seconds)."""
        # Test lower boundary
        config = {'model': 'gpt-4', 'timeout': 1, 'retries': 3}
        result = validate_config(config)
        assert result.is_valid
        
        # Test upper boundary  
        config = {'model': 'gpt-4', 'timeout': 300, 'retries': 3}
        result = validate_config(config)
        assert result.is_valid
        
        # Test invalid boundaries
        config = {'model': 'gpt-4', 'timeout': 0, 'retries': 3}
        result = validate_config(config)
        assert not result.is_valid
        
    def test_validate_config_type_error(self):
        """Test TypeError raised for non-dict input per docstring."""
        with pytest.raises(TypeError):
            validate_config("not a dict")
```

##### Behavior Contract Testing
**Rich Docstring:**
```python
async def with_retry(operation: Callable, strategy: RetryStrategy) -> Any:
    """
    Executes operation with retry logic according to strategy.
    
    Args:
        operation: Async callable to execute
        strategy: RetryStrategy with max_attempts and delay_seconds
        
    Returns:
        Result of successful operation execution
        
    Raises:
        Original exception if all retry attempts fail
        
    Behavior:
        - Attempts operation according to strategy.max_attempts
        - Waits strategy.delay_seconds between attempts  
        - Raises original exception if all attempts fail
        - Returns immediately on first success
        - Logs each retry attempt for monitoring
    """
```

**Generated Tests:**
```python
class TestWithRetry:
    """Test retry behavior per docstring specification."""
    
    @pytest.mark.asyncio
    async def test_with_retry_succeeds_immediately(self):
        """Test retry returns immediately on first success per docstring."""
        success_operation = AsyncMock(return_value="success")
        strategy = RetryStrategy(max_attempts=3, delay_seconds=1)
        
        result = await with_retry(success_operation, strategy)
        
        assert result == "success"
        success_operation.assert_called_once()  # No retries needed
        
    @pytest.mark.asyncio  
    async def test_with_retry_exhausts_attempts(self):
        """Test retry raises original exception after max attempts per docstring."""
        failing_operation = AsyncMock(side_effect=ValueError("test error"))
        strategy = RetryStrategy(max_attempts=2, delay_seconds=0.1)
        
        with pytest.raises(ValueError, match="test error"):
            await with_retry(failing_operation, strategy)
            
        assert failing_operation.call_count == 2  # Max attempts reached
        
    @pytest.mark.asyncio
    async def test_with_retry_respects_delay(self):
        """Test retry waits delay_seconds between attempts per docstring."""
        attempt_times = []
        
        def record_time():
            attempt_times.append(time.time())
            if len(attempt_times) < 2:
                raise ValueError("fail first time")
            return "success"
            
        operation = AsyncMock(side_effect=record_time)
        strategy = RetryStrategy(max_attempts=3, delay_seconds=0.5)
        
        result = await with_retry(operation, strategy)
        
        assert result == "success"
        assert len(attempt_times) == 2
        delay_actual = attempt_times[1] - attempt_times[0]
        assert 0.4 <= delay_actual <= 0.6  # Allow some timing variance
```

##### Return Contract Testing
**Rich Docstring:**
```python
def process_batch(items: List[str]) -> BatchResult:
    """
    Processes a batch of text items.
    
    Returns:
        BatchResult with:
        - success_count: int, number of successfully processed items
        - failed_items: List[str], items that failed processing  
        - results: List[ProcessedItem], successful results in order
        - total_time: float, processing time in seconds
        
        Guarantees:
        - success_count + len(failed_items) == len(input items)
        - results list contains only successful items
        - failed_items preserves original input strings
    """
```

**Generated Tests:**
```python
def test_process_batch_counts_match(self):
    """Test batch result counts match input per docstring guarantee."""
    items = ["valid1", "invalid", "valid2"]  
    result = process_batch(items)
    
    # Test docstring guarantee
    assert result.success_count + len(result.failed_items) == len(items)
    assert len(result.results) == result.success_count
    
def test_process_batch_preserves_failed_items(self):
    """Test failed items preserve original strings per docstring."""
    items = ["valid", "invalid_item", "valid"]
    result = process_batch(items)
    
    # Failed items should contain original strings
    for failed_item in result.failed_items:
        assert failed_item in items
```

### Traditional Test Examples with Rich Documentation

#### Backend Test Example
```python
class TestNewFeature:
    """
    Test suite for new feature functionality.
    
    Scope:
        - API endpoint behavior and response validation
        - Service method integration and error handling
        - Business logic verification for feature workflows
        
    Business Critical:
        Feature failures directly impact user workflows and system reliability
        
    Test Strategy:
        - Unit tests for individual service methods
        - Integration tests for API endpoint contracts
        - Error scenario coverage for resilience validation
    """
    
    def test_new_endpoint(self, client: TestClient):
        """
        Test that new API endpoint returns expected response structure.
        
        API Contract:
            GET /new-endpoint should return 200 with required fields
            
        Business Impact:
            Provides core functionality access to frontend clients
            
        Success Criteria:
            - Status code 200 indicates successful processing
            - Response contains expected_field for client usage
            - Response format matches API specification
        """
        response = client.get("/new-endpoint")
        assert response.status_code == 200
        
        data = response.json()
        assert "expected_field" in data
    
    async def test_new_service_method(self, service):
        """
        Test that service method processes input and returns valid result.
        
        Behavior Under Test:
            Service method transforms test input into structured response
            
        Business Impact:
            Core processing logic that affects user data handling
            
        Success Criteria:
            - Processing completes successfully (success=True)
            - Result contains processed data for downstream usage
            - No exceptions during normal operation
        """
        result = await service.new_method("test_input")
        assert result.success is True
        assert result.data is not None
```

#### Frontend Test Example
```python
class TestNewComponent:
    """
    Test suite for new frontend API client component.
    
    Integration Scope:
        Tests API client communication patterns and error handling
        
    External Dependencies:
        - Mocked HTTP client for deterministic testing
        - Real async patterns for realistic behavior validation
    """
    
    async def test_new_api_method(self, api_client):
        """
        Test that API client method handles successful responses correctly.
        
        Integration Behavior:
            API client makes HTTP request and processes JSON response
            
        Business Impact:
            Ensures frontend can successfully communicate with backend services
            
        Test Isolation:
            Uses mocked HTTP client to avoid external dependencies
            
        Success Criteria:
            - HTTP request is made with correct parameters
            - JSON response is parsed and returned to caller
            - Result format matches expected client interface
        """
        with patch('httpx.AsyncClient') as mock_client:
            mock_response = AsyncMock()
            mock_response.status_code = 200
            mock_response.json.return_value = {"result": "success"}
            mock_client.return_value.__aenter__.return_value.get.return_value = mock_response
            
            result = await api_client.new_method()
            assert result["result"] == "success"
```

> **📖 Test Documentation Templates**: See **[DOCSTRINGS_TESTS.md](./DOCSTRINGS_TESTS.md)** for comprehensive test docstring templates including unit tests, integration tests, API tests, security tests, and performance tests.

### Test Generation Guidelines

#### Systematic Docstring-to-Test Mapping
- **Args section** → Input validation tests and boundary conditions
- **Returns section** → Return value structure and content verification  
- **Raises section** → Exception condition tests
- **Behavior section** → Observable outcome tests for each documented behavior
- **Examples section** → Convert to executable test cases

#### Test Documentation Standards

When writing test docstrings, focus on **WHY** the test exists rather than **HOW** it works:

**Essential Elements for Test Documentation:**
- **Behavior Being Verified**: What specific functionality is being tested
- **Business Impact**: Why this test matters to users/stakeholders  
- **Test Scenario**: Given/When/Then or specific conditions being tested
- **Success Criteria**: What constitutes a passing test
- **Failure Impact**: What breaks if this test starts failing

**Quick Example:**
```python
def test_api_returns_400_for_missing_required_field(self, client):
    """
    Test that API validates required fields and returns proper error codes.
    
    Business Impact:
        Provides clear feedback to API consumers about request format errors
        
    Test Scenario:
        When required 'text' field is missing from request body
        
    Success Criteria:
        - Returns 400 status code for validation errors
        - Error response includes field-specific validation message
    """
```

#### Test Structure Best Practices
- **Use descriptive test names** that reflect documented behavior
- **Group related tests in test classes** organized by function/class under test
- **Include both positive and negative test cases** based on docstring specifications
- **Use appropriate fixtures and mocking** for external dependencies
- **Focus on testing contracts, not implementation details**
- **Document test intent clearly** using the standards from DOCSTRINGS_TESTS.md

#### Property-Based Testing for Edge Cases

Instead of writing dozens of individual edge case tests, use property-based testing to generate comprehensive test scenarios:

```python
from hypothesis import given, strategies as st

@given(
    text=st.text(min_size=1, max_size=10000),
    operation=st.sampled_from(["summarize", "analyze", "extract"])
)
def test_text_processing_handles_any_valid_input(text, operation, client):
    """Test that all valid inputs are handled gracefully."""
    response = client.post("/v1/text_processing/process",
                          json={"text": text, "operation": operation})
    
    # Should never crash, always return structured response
    assert response.status_code in [200, 400, 422]
    assert "error" in response.json() or "result" in response.json()

@given(
    config_dict=st.dictionaries(
        keys=st.sampled_from(['model', 'timeout', 'retries']),
        values=st.one_of(
            st.text(min_size=1, max_size=50),
            st.integers(min_value=1, max_value=1000),
            st.none()
        )
    )
)
def test_config_validation_handles_any_input(config_dict):
    """Test that configuration validation never crashes."""
    result = validate_config(config_dict)
    
    # Should always return ValidationResult, never crash
    assert hasattr(result, 'is_valid')
    assert hasattr(result, 'errors')
    assert isinstance(result.errors, list)
```

#### Refactoring Tests: From Brittle to Maintainable

**Before (Brittle, Implementation-Focused):**
```python
def test_text_processor_with_retry_and_circuit_breaker(
    text_processor, mock_ai_agent, mock_retry_policy, mock_circuit_breaker
):
    """Test that text processor uses retry and circuit breaker correctly."""
    mock_ai_agent.run.side_effect = [Exception(), Exception(), "Success"]
    mock_retry_policy.should_retry.side_effect = [True, True, False]
    mock_circuit_breaker.call.return_value = "Success"
    
    result = text_processor.process("test")
    
    # Tests internal implementation details
    assert mock_retry_policy.should_retry.call_count == 3
    assert mock_circuit_breaker.call.call_count == 1
    assert mock_ai_agent.run.call_count == 3
    assert result == "Success"
```

**Problems with the above:**
- Tests internal method calls, not behavior
- Breaks when refactoring resilience implementation
- Doesn't verify user-observable outcomes
- Complex mocking setup obscures test intent

**After (Maintainable, Behavior-Focused):**
```python
def test_text_processing_recovers_from_transient_failures(client):
    """Test that text processing recovers from transient failures."""
    # Setup: Configure test to simulate transient failure
    with patch('app.services.ai_provider.call') as mock_ai:
        mock_ai.side_effect = [
            Exception("Temporary service failure"), 
            "Successfully processed text"
        ]
        
        response = client.post("/v1/text_processing/process",
                              json={"text": "test input", "operation": "summarize"})
        
        # Assert on user-visible behavior
        assert response.status_code == 200
        assert response.json()["success"] is True
        assert "processed text" in response.json()["result"].lower()
```

**Benefits of the refactored test:**
- Tests user-observable behavior (API response)
- Survives internal implementation changes
- Clear test intent and failure messages
- Minimal mocking at system boundary only

#### What to Test vs. What to Avoid

**✅ Test These (From Docstrings):**
- **Input validation** and boundary conditions mentioned in Args
- **Return value structure** and guarantees specified in Returns
- **Exception conditions** listed in Raises section  
- **Observable behaviors** documented in Behavior section
- **Usage patterns** shown in Examples section

**❌ Avoid Testing These:**
- **Internal implementation details** not mentioned in docstring
- **Private methods** or undocumented attributes
- **Specific algorithms** or data structures used internally
- **Framework integration details** (covered by framework tests)
- **Trivial functions** without documented behavior contracts

### Test Naming Conventions

- Test files: `test_*.py`
- Test classes: `Test*` (typically `TestFunctionName` or `TestClassName`)
- Test methods: `test_*` with descriptive names explaining the documented behavior being tested
- Use names like: `test_function_validates_input_per_docstring()` or `test_service_handles_timeout_behavior()`

#### Test Class Documentation

Test classes should include comprehensive docstrings that provide context about the entire test suite:

```python
class TestUserAuthentication:
    """
    Test suite for user authentication and authorization workflows.
    
    Scope:
        - Login/logout functionality
        - Password validation and security
        - Session management
        - Multi-factor authentication
        - Account lockout policies
        
    Business Critical:
        Authentication failures directly impact user access and security
        
    Test Strategy:
        - Unit tests for individual validation functions
        - Integration tests for complete auth flows
        - Security tests for attack prevention
        - Performance tests for auth under load
        
    External Dependencies:
        - Mocked user database
        - Real password hashing (bcrypt)
        - Mocked email service for 2FA
        
    Known Limitations:
        - Does not test actual email delivery
        - Browser session persistence not covered
        - LDAP integration tested separately
    """
```

This provides essential context for understanding test failures and maintaining the test suite over time.

### Test Organization

- **Group related tests in classes** organized around the component being tested
- **Use fixtures for common setup** but ensure tests remain focused on documented contracts
- **Keep tests focused and independent** - each test should verify one aspect of the documented contract
- **Test both success and failure scenarios** as documented in the function's specification
- **Organize tests to mirror docstring structure** (Args tests, Returns tests, Behavior tests, etc.)

## Debugging Tests

### Running Tests in Debug Mode

```bash
# Run with verbose output (using virtual environment)
.venv/bin/python -m pytest tests/ -v -s

# Run specific test with debugging
.venv/bin/python -m pytest tests/test_main.py::test_specific_function -v -s --pdb

# Run with coverage and keep temporary files
.venv/bin/python -m pytest tests/ --cov=app --cov-report=html --keep-durations=10

# Or use Makefile commands with additional pytest options
make test-backend PYTEST_ARGS="-v -s --pdb"
```

### Test Execution Features

#### Parallel Execution
By default, tests run in parallel using pytest-xdist:
- **Auto-detection**: `-n auto --dist worksteal` automatically determines optimal worker count
- **Environment isolation**: Tests use `monkeypatch.setenv()` for clean environments
- **Work-stealing**: Dynamic load balancing across test workers
- **Sequential tests**: Use `@pytest.mark.no_parallel` for tests that must run sequentially

#### Test Markers
- **`slow`**: Comprehensive resilience tests, timing tests, and performance scenarios
- **`manual`**: Require running FastAPI server and real API keys
- **`integration`**: Test component interactions with mocked external services
- **`retry`**: Test retry logic and exponential backoff patterns
- **`circuit_breaker`**: Test circuit breaker functionality and recovery
- **`no_parallel`**: Must run sequentially (not in parallel with other tests)

#### Special Flags
- **`--run-slow`**: Enable tests marked as `slow` (excluded by default)
- **`--run-manual`**: Enable tests marked as `manual` (excluded by default)

### Manual Test Requirements

Manual tests (`-m "manual"`) require:
- FastAPI server running on `http://localhost:8000`
- `API_KEY=test-api-key-12345` environment variable for authentication tests
- `GEMINI_API_KEY` environment variable for AI features and live API testing
- Use `--run-manual` flag to enable manual tests

**Setup for manual tests:**
```bash
# 1. Set environment variables
export GEMINI_API_KEY="your-actual-gemini-api-key"
export API_KEY="test-api-key-12345"
export RESILIENCE_PRESET="development"  # or appropriate preset

# 2. Start server (from project root)
source .venv/bin/activate
cd backend/
uvicorn app.main:app --reload --port 8000

# 3. Run manual tests (in another terminal, from project root)
source .venv/bin/activate
cd backend/
pytest -v -s -m "manual" --run-manual

# 4. Test both public and internal APIs
curl http://localhost:8000/v1/health        # Public API
curl http://localhost:8000/internal/health  # Internal API
```

### Slow Test Categories

Slow tests (`-m "slow"`) include:
- **Resilience pattern testing**: Circuit breaker recovery, retry with backoff
- **Performance benchmarks**: Cache performance, concurrent request handling
- **Integration scenarios**: End-to-end workflows with multiple service interactions
- **Timeout testing**: Testing various timeout scenarios and recovery patterns

### Common Issues

#### Configuration Issues
1. **Resilience Configuration**: Ensure `RESILIENCE_PRESET` is set (default: `simple`)
2. **API Key Issues**: Set `GEMINI_API_KEY` for AI tests (can be dummy value for unit tests)
3. **Authentication**: Use `API_KEY=test-api-key-12345` for manual authentication tests
4. **Environment Variables**: Use `monkeypatch.setenv()` in fixtures for test isolation

#### Infrastructure Issues
5. **Redis Connection**: Tests automatically fall back to memory cache if Redis unavailable
6. **Port Conflicts**: Ensure ports 8000 (backend) and 8501 (frontend) are available
7. **Docker Issues**: Use `make test-local` to run tests without Docker dependency

#### Test Execution Issues
8. **Parallel Execution**: Use `-n 0` to disable parallel execution for debugging
9. **Slow Tests**: Use `--run-slow` flag to enable comprehensive resilience testing
10. **Manual Tests**: Requires running server - use `--run-manual` flag
11. **Marker Issues**: Use `--strict-markers` to catch undefined test markers

#### Development Issues
12. **Virtual Environment**: Run `make clean-all` and `make install` to reset environment
13. **Python Version**: Makefile automatically detects `python3` or `python`
14. **Dependencies**: Run `make install` to update all dependencies
15. **Coverage Issues**: Infrastructure services require >90%, domain services >70%

## Performance Testing

### Load Testing

For performance testing, consider using:

```bash
# Install load testing tools
pip install locust

# Run load tests (if implemented)
locust -f tests/load_tests.py --host=http://localhost:8000
```

### Benchmarking

```bash
# Run tests with timing (using virtual environment)
.venv/bin/python -m pytest tests/ --durations=10

# Profile specific tests
.venv/bin/python -m pytest tests/test_main.py --profile
```

## Contributing to Tests

### Guidelines

1. **Write tests for new features**: All new code should include tests
2. **Maintain coverage**: Aim for >90% test coverage
3. **Test edge cases**: Include tests for error conditions and edge cases

> **📖 For comprehensive exception testing patterns**, see the **[Exception Handling Guide](./EXCEPTION_HANDLING.md)** which covers:
> - Testing exception hierarchy and classification
> - Unit testing patterns for exception handling
> - API testing with proper status code validation
> - Exception classification testing for resilience patterns
> - Best practices for testing error scenarios
4. **Use appropriate mocks**: Mock external dependencies appropriately
5. **Keep tests fast**: Unit tests should run quickly
6. **Document complex tests**: Add comments for complex test logic

### Pull Request Requirements

Before submitting a pull request:

1. Run the full test suite: `make test`
2. Check code quality: `make lint`
3. Format code: `make format`
4. Ensure coverage doesn't decrease
5. Add tests for new functionality

## Troubleshooting

### Common Test Issues & Solutions

| Problem | Root Cause | Solution | Prevention |
|---------|------------|----------|------------|
| **Tests break during refactoring** | Too much implementation testing | Focus on behavior testing, reduce internal mocking | Use docstring-driven test development |
| **Tests take too long** | Too many integration tests | Increase unit test ratio, optimize test data | Follow test pyramid, mock external dependencies |
| **Flaky/inconsistent tests** | Too much real I/O or timing dependencies | Mock external dependencies, use deterministic test data | Mock at system boundaries only |
| **Hard to understand test failures** | Poor test names, unclear assertions | Use descriptive, behavior-focused test names | Write tests from user perspective |
| **Tests pass but bugs reach production** | Poor coverage of critical paths | Focus testing on user-facing workflows | Prioritize critical user journey coverage |
| **Developers skip running tests** | Tests are slow or unreliable | Optimize for fast feedback, fix flaky tests | Maintain <60s test execution time |

### Quick Debugging Commands

```bash
# Run only fast tests during development
pytest -m "not slow and not manual"

# Debug specific test with detailed output
pytest path/to/test.py::test_name -v -s --pdb

# Run tests without parallel execution for debugging
pytest tests/ -n 0 -v

# Update snapshots after intentional changes
pytest --snapshot-update

# Run with maximum verbosity
pytest tests/ -vv --tb=long
```

### Environment Issues

**Common Setup Problems:**

1. **API Key Issues**: Ensure `GEMINI_API_KEY` is set for AI tests (can be dummy value for unit tests)
2. **Port Conflicts**: Ensure test ports (8000, 8501) are available for manual tests
3. **Docker Issues**: Use `make test-local` to skip Docker tests if Docker unavailable
4. **Dependency Issues**: Run `make install` to update dependencies in virtual environment
5. **Python Version Issues**: Makefile automatically detects correct Python version
6. **Virtual Environment Issues**: Run `make clean-all` followed by `make install` to reset

## Best Practices Summary

### DO ✅

**Testing Approach:**
- **Test user-visible behavior** and external contracts
- **Mock at system boundaries** (external APIs, databases)
- **Write descriptive test names** that explain what behavior is being verified
- **Use property-based testing** (Hypothesis) for comprehensive edge case coverage
- **Keep tests fast and deterministic** (<60s total execution time)
- **Test the happy path thoroughly** before diving into edge cases
- **Delete tests that don't add value** or are primarily testing framework/library code

**Test Organization:**
- **Follow the test pyramid** (many unit, fewer integration, minimal E2E)
- **Focus on critical user paths** with integration tests
- **Use docstring-driven test development** for better test specifications
- **Group tests by behavior** rather than by implementation structure

**Maintenance:**
- **Refactor tests alongside production code** to maintain relevance
- **Measure meaningful metrics** (critical path coverage, test execution time)
- **Review tests regularly** using the 4-question maintenance check

### DON'T ❌

**Avoid These Testing Anti-Patterns:**
- **Don't test implementation details** (internal method calls, private state)
- **Don't mock internal components** (your own services, utilities, business logic)
- **Don't write tests for trivial code** (getters/setters, one-line functions)
- **Don't aim for 100% coverage** as a primary goal
- **Don't keep brittle tests "just in case"** - delete or refactor them
- **Don't test every edge case exhaustively** - use property-based testing instead
- **Don't verify exact function call counts** unless it's user-observable behavior

**Avoid These Development Habits:**
- **Don't skip tests because they're slow** - fix the speed issue
- **Don't disable tests instead of fixing them** - address the root cause
- **Don't write tests after the fact** - test-driven or docstring-driven development works better
- **Don't optimize for vanity metrics** (total test count, line coverage percentage)

### Getting Help

- **Check test output** for specific error messages and stack traces
- **Review test configuration** in `pytest.ini` for marker and execution settings
- **Check CI logs** for additional context and environment differences  
- **Refer to pytest documentation** for advanced usage patterns
- **Use debugging tools** like `--pdb` flag for interactive debugging

## Test Metrics

The test suite tracks the following metrics:

- **Test Coverage**: Percentage of code covered by tests
- **Test Duration**: Time taken to run tests
- **Test Success Rate**: Percentage of tests passing
- **Code Quality Score**: Results from linting and type checking

These metrics are tracked in CI and can be viewed in the coverage reports and GitHub Actions logs.

## Testing Metrics That Matter

Focus on actionable metrics that drive quality improvements rather than vanity metrics that don't correlate with system reliability.

### Meaningful Metrics ✅

| Metric | Target | Why It Matters | How to Measure |
|--------|--------|----------------|----------------|
| **Critical Path Coverage** | 90%+ | User-facing features must work | Coverage on API endpoints, core workflows |
| **Test Execution Time** | <60s | Fast feedback loop essential for development | Total time for fast test suite |
| **Test Maintenance Time** | <10% dev time | Tests shouldn't slow development | Time spent fixing broken tests vs writing features |
| **False Positive Rate** | <5% | Tests should be reliable indicators | % of test failures not indicating real issues |
| **Mean Time to Fix** | <30min | Quick resolution of test failures | Time from test failure to fix deployment |
| **Bug Detection Rate** | 80%+ | Tests should catch issues before production | % of production bugs caught by tests first |

### Vanity Metrics to Ignore ❌

Avoid optimizing for these metrics as they don't correlate with system quality:

- **Total number of tests** - More tests ≠ better coverage
- **Line coverage percentage** - High coverage ≠ meaningful testing
- **Number of assertions** - More assertions ≠ better validation
- **Cyclomatic complexity scores** - Arbitrary thresholds don't improve code
- **Docstring coverage percentage** - Documentation for documentation's sake

### Actionable Quality Indicators

**Green Flags (System is Healthy):**
- Tests run in under 60 seconds for fast feedback
- Less than 5% of test failures are false positives
- New features rarely break existing tests
- Developers feel confident deploying after tests pass
- Most production issues are caught by tests first

**Red Flags (System Needs Attention):**
- Tests take >5 minutes to run (developers avoid running them)
- Frequent test breakage during refactoring (implementation testing)
- Tests pass but production issues occur (poor test coverage of critical paths)
- Developers frequently skip or disable tests (tests are more burden than help)

## Related Documentation

### **Core Testing Documentation**
- **[DOCSTRINGS_CODE.md](./DOCSTRINGS_CODE.md)**: Production code docstring standards that serve as test specifications for behavior-driven testing
- **[DOCSTRINGS_TESTS.md](./DOCSTRINGS_TESTS.md)**: Comprehensive test documentation templates, including unit tests, integration tests, API tests, security tests, and fixture documentation

### **Prerequisites**
- **[Backend Guide](./BACKEND.md)**: Understanding backend architecture and components being tested
- **[Frontend Guide](./FRONTEND.md)**: Understanding frontend architecture and testing patterns

### **Related Topics**
- **[Code Standards](./CODE_STANDARDS.md)**: Code quality standards that complement testing requirements
- **[Exception Handling](./EXCEPTION_HANDLING.md)**: Exception testing patterns that complement docstring-driven testing
- **[Docker Setup](./DOCKER.md)**: Docker environments used for consistent testing across systems
- **[Virtual Environment Guide](./VIRTUAL_ENVIRONMENT_GUIDE.md)**: Environment management for test execution

### **Next Steps**
- **[Deployment Guide](./DEPLOYMENT.md)**: Production deployment with comprehensive testing validation
- **[Infrastructure Testing](./infrastructure/MONITORING.md)**: Advanced monitoring and performance testing patterns
- **[Authentication Testing](./AUTHENTICATION.md)**: Security and authentication testing approaches

### **Documentation Integration Workflow**

For comprehensive test development:
1. **Start with DOCSTRINGS_CODE.md** - Write rich production code docstrings with Args, Returns, Raises, and Behavior sections
2. **Use this TESTING.md guide** - Apply docstring-driven test development principles to generate behavior-focused tests
3. **Apply DOCSTRINGS_TESTS.md templates** - Document test intent, business impact, and success criteria using our test documentation standards
4. **Follow CODE_STANDARDS.md** - Ensure overall code quality and documentation consistency 