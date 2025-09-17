---
sidebar_label: Overview
sidebar_position: 1
---

# Testing Guide

This document provides a high-level overview of the testing philosophy for this project. For detailed, practical guidance, please refer to the in-depth guides linked at the end of this document.

## Quick Navigation

### Comprehensive Testing Guides
- **[Unit Tests](./UNIT_TESTS.md)** - Complete guide to behavior-driven unit testing with AI workflows
- **[Integration Tests](./INTEGRATION_TESTS.md)** - Component collaboration and seam testing strategies
- **[Writing Tests](./1_WRITING_TESTS.md)** - Docstring-driven test development principles
- **[Mocking Strategy](./2_MOCKING_GUIDE.md)** - Fakes over mocks, boundary mocking patterns
- **[Coverage Strategy](./3_COVERAGE_STRATEGY.md)** - Tiered coverage approach and meaningful metrics
- **[Test Structure](./4_TEST_STRUCTURE.md)** - Organization, fixtures, and test categories
- **[Test Execution](./5_TEST_EXECUTION_GUIDE.md)** - Running tests, debugging, and troubleshooting
- **[Contributing Tests](./6_CONTRIBUTING_TESTS.md)** - Guidelines for adding new tests

- ### Quick Start Commands
```bash
# Setup and run all tests
make install && make test

# Backend tests only
make test-backend

# Frontend tests only  
make test-frontend

# Tests with coverage
make test-coverage
```

### Find What You Need
- **New to the project?** → Start with [Test Execution Guide](./5_TEST_EXECUTION_GUIDE.md)
- **Writing unit tests?** → See [Unit Tests Guide](./UNIT_TESTS.md) for comprehensive guidance
- **Testing component interactions?** → Check [Integration Tests Guide](./INTEGRATION_TESTS.md)
- **Writing new features?** → See [Writing Tests](./1_WRITING_TESTS.md) for docstring-driven development
- **Struggling with mocks?** → Check [Mocking Strategy](./2_MOCKING_GUIDE.md)
- **Coverage questions?** → Review [Coverage Strategy](./3_COVERAGE_STRATEGY.md)
- **Test failing?** → See [Troubleshooting](./5_TEST_EXECUTION_GUIDE.md#troubleshooting)

## Overview

> **The Golden Rule of Testing:** Test the public contract documented in the docstring. **Do NOT test the implementation code inside a function.** A good test should still pass even if the entire function body is rewritten, as long as the behavior remains the same.

The test suite covers both backend and frontend components with the following types of tests:

- **Unit Tests**: Test individual components in complete isolation, verifying their documented contracts through observable behavior. See [Unit Tests Guide](./UNIT_TESTS.md) for comprehensive guidance on behavior-driven unit testing.
- **Integration Tests**: Test collaboration between multiple internal components and critical integration points. See [Integration Tests Guide](./INTEGRATION_TESTS.md) for detailed strategies.
- **End-to-End Tests**: Test complete user workflows through the entire application stack.
- **Code Quality**: Linting, type checking, and formatting validation.

### Testing Philosophy: Maintainable, Behavior-Driven Testing

This project emphasizes **maintainability over exhaustiveness** and **behavior over implementation** to create robust test suites that provide real confidence while remaining maintainable over time.

#### Core Testing Principles

Our testing strategy prioritizes tests that give us confidence that the system works correctly for users, not that every internal function executes in a specific way.

1. **Test Behavior, Not Implementation** - Focus on what the system should accomplish from an external observer's perspective.
2. **Maintainability Over Exhaustiveness** - Better to have fewer, high-value tests than comprehensive low-value tests.
3. **Mock Only at System Boundaries** - Minimize mocking to reduce test brittleness.
4. **Fast Feedback Loops** - Tests should run quickly to enable continuous development.

#### Defining the Public Contract

To rigorously enforce our behavior-driven approach, we formally define a component's "public contract" using stub files (`.pyi`).

- **Source of Truth**: These stub files are automatically generated from the production code via `make generate-contracts` and are located in `backend/contracts`.
- **Implementation-Agnostic**: Each `.pyi` file contains the public interface—class definitions, method signatures, type hints, and docstrings—but all internal implementation logic is removed.
- **Test Development**: All tests should be written and debugged by referencing only these contract files. This provides a clean, focused, and implementation-agnostic context that ensures we test *what* a component does, not *how* it does it.

### The Modern Testing Pyramid

Our approach reshapes the classic testing pyramid into a modern, multi-layered verification strategy that prioritizes resilience to refactoring.

```
      / \
     /I&E\      <- Small number of Integration & End-to-End tests
    /-----\
   /  B&C  \    <- Focused suite of Behavioral & Contract tests
  /---------\
 /   Static  \  <- Largest base: Static Analysis (MyPy, Linters)
/-------------\
```

- **Base: Static Analysis**: We place a heavy reliance on static analysis tools like `MyPy` and linters as our foundational layer of defense.
- **Middle: Behavioral and Contract Tests**: This layer consists of a "small and focused" suite of tests that exercise the public contract of a component from the outside in.
- **Peak: Integration and End-to-End Tests**: The peak is a small number of tests that verify critical user flows and true wire-level interactions between components.

### Behavior-Focused Testing Approach

Our testing strategy emphasizes **behavior over implementation**, ensuring tests remain maintainable and provide genuine confidence in component functionality.

**Core Principles:**
- **Test Public Contracts**: Focus on documented interfaces (Args, Returns, Raises, Behavior)
- **Observable Outcomes**: Test what external callers can see and depend on
- **Implementation Independence**: Tests should survive internal refactoring
- **Clear Intent**: Test names and structure should document expected behavior

**Comprehensive Examples and Guidance:**
- **Unit Testing**: See [Unit Tests Guide](./UNIT_TESTS.md) for detailed behavior-focused patterns, mocking strategies, and component testing examples
- **Integration Testing**: See [Integration Tests Guide](./INTEGRATION_TESTS.md) for collaboration testing and seam verification patterns
- **Anti-Patterns**: Both comprehensive guides include detailed examples of what to avoid and troubleshooting guidance

### Test Maintenance Guidelines

Before writing or keeping a test, ask these critical questions:

1. **Fragility Check**: Will this test break if I refactor the implementation?
2. **Value Check**: Does this test verify behavior that users depend on?
3. **Deletion Test**: Would removing this test reduce our confidence in the system?
4. **Mock Check**: Am I mocking more than necessary to isolate the behavior?

If a test fails these checks, refactor or remove it.

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

## Handling LLM Non-Determinism

LLM outputs are inherently non-deterministic, requiring specialized testing strategies:

### 1. Mock LLM Calls in Most Tests
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

### 2. Evaluation-Based Testing
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

### 3. Snapshot Testing
Save and compare outputs for regression detection:

```python
def test_llm_response_format_stability(snapshot, mock_llm):
    """Test that LLM response format remains stable."""
    mock_llm.return_value = "Consistent test response"
    
    response = process_text("test input", "summarize")
    
    # Will fail if response structure changes
    snapshot.assert_match(response.dict(), "llm_response_format.json")
```

### 4. Manual Verification Tests
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
## Related Documentation

### Comprehensive Testing Guides
- **[Unit Tests](./UNIT_TESTS.md)**: Complete guide to behavior-driven unit testing including 5-step process, AI workflows, patterns, and quality framework
- **[Integration Tests](./INTEGRATION_TESTS.md)**: Component collaboration testing with seam verification, high-fidelity fakes, and AI-assisted workflows
- **[Writing Tests](./1_WRITING_TESTS.md)**: Docstring-driven test development principles and general testing guidance
- **[Mocking Strategy](./2_MOCKING_GUIDE.md)**: When and how to use mocks vs fakes with system boundary patterns
- **[Test Structure](./4_TEST_STRUCTURE.md)**: Test organization, fixtures, and directory structure

### Core Testing Documentation
- **[DOCSTRINGS_CODE.md](../developer/DOCSTRINGS_CODE.md)**: Production code docstring standards that serve as test specifications for behavior-driven testing
- **[DOCSTRINGS_TESTS.md](../developer/DOCSTRINGS_TESTS.md)**: Comprehensive test documentation templates, including unit tests, integration tests, API tests, security tests, and fixture documentation

### Component-Specific Testing Guidance
- **[Backend Testing](../../backend/AGENTS.md)**: FastAPI-specific testing patterns, infrastructure services, domain services
- **[Frontend Testing](../../frontend/AGENTS.md)**: Streamlit testing patterns, API client testing, UI component testing

### Related Topics
- **[Code Standards](../developer/CODE_STANDARDS.md)**: Code quality standards that complement testing requirements
- **[Exception Handling](../developer/EXCEPTION_HANDLING.md)**: Exception testing patterns that complement docstring-driven testing
- **[Docker Setup](../developer/DOCKER.md)**: Docker environments used for consistent testing across systems

### Next Steps
- **[Deployment Guide](../deployment/DEPLOYMENT.md)**: Production deployment with comprehensive testing validation
- **[Infrastructure Testing](../infrastructure/MONITORING.md)**: Advanced monitoring and performance testing patterns
- **[Authentication Testing](../developer/AUTHENTICATION.md)**: Security and authentication testing approaches

### Documentation Integration Workflow

For comprehensive test development:
1. **Start with [DOCSTRINGS_CODE.md](../developer/DOCSTRINGS_CODE.md)** - Write rich production code docstrings with Args, Returns, Raises, and Behavior sections
2. **Use this TESTING.md guide** - Apply docstring-driven test development principles to generate behavior-focused tests
3. **Apply [DOCSTRINGS_TESTS.md](../developer/DOCSTRINGS_TESTS.md) templates** - Document test intent, business impact, and success criteria using our test documentation standards
4. **Follow [CODE_STANDARDS.md](../developer/CODE_STANDARDS.md)** - Ensure overall code quality and documentation consistency 