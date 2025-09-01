---
sidebar_label: Coverage
---

# Test Coverage Strategy

## Tiered Coverage Approach

This project follows a **tiered test coverage strategy** that prioritizes testing effort based on component criticality and user impact. Rather than applying uniform coverage requirements across all code, we focus intensive testing on components where failures matter most.

> ⚠️ **Warning: Principles Over Percentages**
> These coverage targets are guidelines, not mandates. A test suite that perfectly follows the 'Test Behavior, Not Implementation' principle at 80% coverage is far more valuable than a 95% coverage suite full of brittle, implementation-focused tests. **Never sacrifice test quality to meet a numeric target.

## Pragmatic Testing Categories & Goals

Different parts of the system require different testing approaches based on their criticality and user impact:

| Category | Coverage Target | Focus | Example | Testing Approach |
|----------|----------------|-------|---------|------------------|
| **Critical User Paths** | 90%+ | End-to-end behavior | Text processing workflow | Integration tests with real data flows |
| **API Endpoints** | 80%+ | Request/response contracts | Status codes, response structure | Contract testing with edge cases |
| **Business Logic** | 70%+ | Core functionality | Text processing operations | Unit tests with behavior focus |
| **Infrastructure** | 50%+ | Basic configuration | Can it start? Does config load? | Smoke tests and health checks |
| **Utilities** | 30%+ | Pure functions only | Validation helpers | Unit tests for complex logic only |

### 🔴 Critical Components (90-100% line coverage)
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

### 🟡 Important Components (70-85% line coverage)
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

### 🟢 Supporting Components (40-60% line coverage)
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

### ⚪ Skip Testing (0% direct coverage)
**What:** Framework code, external libraries, trivial functions  
**Examples:**
- **Property getters/setters** - No logic to test
- **Simple data classes** - Just containers
- **Third-party library wrappers** - Covered by library tests
- **Configuration constants** - Static values

## Component-Specific Coverage Requirements

### Backend Infrastructure Services (70-90% coverage)
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

### Domain Services (60-75% coverage) 
*Educational examples - replace with your business logic*

- **Text Processing Service** (`app/services/text_processor.py`) - 70% target
  - AI text processing using PydanticAI agents
  - Business-specific processing logic (educational examples)

- **Response Validator** (`app/services/response_validator.py`) - 65% target
  - Business-specific response validation logic

### API Endpoints (90-95% coverage)
- **Public API** (`/v1/`) - 95% target
  - Authentication validation and user-facing contracts
  - Health checks and core processing operations
  - Error handling and CORS configuration

- **Internal API** (`/internal/`) - 90% target
  - Cache management endpoints (38 resilience endpoints)
  - Monitoring and metrics collection
  - Resilience management across 8 modules

### Core Components (90-95% coverage)
- **Configuration Management** (`app/core/config.py`) - 95% target
  - Dual-API configuration and preset-based resilience system
  - Security and infrastructure settings

- **Dependency Injection** (`app/dependencies.py`) - 90% target
  - Service provider patterns and preset-based configuration loading

### Shared Models (95-100% coverage)
- **Pydantic Models** (`shared/models.py` and `app/schemas/`) - 100% target
  - Cross-service data models and field validation
  - Serialization/deserialization contracts

## Practical Coverage Targets

### By Test Type
- **Unit Tests:** 60-80% line coverage (focused on critical paths)
- **Integration Tests:** Cover key workflows end-to-end
- **API Tests:** 100% endpoint coverage, 80% scenario coverage

### Overall Project Target
**Target: 70-80% overall line coverage**
- High enough to catch most bugs
- Low enough to avoid testing trivia
- Focuses effort on valuable tests
- Allows for some untested utility code

## Coverage Quality Metrics

**Quality Metrics (More Important Than Coverage Percentage):**
- **Bug Detection Rate:** Do tests catch real issues before production?
- **Test Maintenance Time:** How often do tests break during refactoring?
- **Confidence Level:** Do you feel safe deploying with these tests?
- **Development Speed:** Do tests help or hinder feature development?

## Coverage Anti-Patterns to Avoid

### ❌ Don't Do This
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

### ✅ Do This Instead
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

## Implementation Strategy

1. **Start with current coverage baseline**
2. **Identify your critical paths** (user-facing features)
3. **Set coverage floors** for each component type
4. **Delete low-value tests** to focus effort
5. **Measure quality, not just quantity**
6. **Focus on behavior testing over implementation testing**

## Frontend Coverage

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

