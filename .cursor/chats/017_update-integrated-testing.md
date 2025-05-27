# Clarifying Unused File in Codebase
_Exported on 5/27/2025 at 14:09:35 EDT from Cursor (0.50.7)_

---

**User**

This file doesn't seem to be used by the Makefile or any other files in the codebase. Do you know why it was created or when it should be run?

---

**Cursor**

Looking at the `test_integration.py` file and the Makefile, I can see that this integration test file was created but isn't actually integrated into the project's testing infrastructure.

Based on my analysis of the codebase and the chat history, I can explain why the `test_integration.py` file exists and when it should be used:

## Purpose and Origin

The `test_integration.py` file was created during the development process as a **simple, standalone integration test** to verify that the FastAPI backend and Streamlit frontend can communicate properly. Looking at the chat history, it was created in chat `004_frontend-streamlit-app.md` as a quick way to test the integration between components.

## Why It's Not in the Makefile

The file isn't integrated into the Makefile's test commands because:

1. **Different Testing Approach**: The `scripts/run_tests.py` (which the Makefile calls) uses a Docker-based integration testing approach with `curl` commands to test health endpoints, while `test_integration.py` is a more comprehensive Python-based test.

2. **Standalone Design**: It was designed as a standalone script that can be run independently when you want to manually verify the system is working end-to-end.

3. **More Comprehensive Alternative**: There's also a much more comprehensive integration test in `examples/integration_test.py` that includes extensive testing scenarios.

## When to Use It

You should run `test_integration.py` when:

1. **Manual Verification**: You want to quickly verify that both services are running and can communicate
2. **Development Testing**: During development when you want to test specific integration scenarios
3. **Troubleshooting**: When debugging communication issues between frontend and backend
4. **Before Deployment**: As a final check before deploying to ensure everything works

## How to Run It

```bash
# Make sure both services are running first
python test_integration.py
```

## Recommendation

To integrate this into your testing workflow, you could:

1. **Add it to the Makefile** as a separate target:
```makefile
test-integration:
	@echo "Running integration tests..."
	$(PYTHON_CMD) test_integration.py
```

2. **Or modify `scripts/run_tests.py`** to include it as an additional integration test step.

The file serves as a useful manual testing tool, but it's currently outside the automated testing pipeline by design.

```shellscript
# Make sure both services are running first
python test_integration.py
```

```makefile
test-integration:
	@echo "Running integration tests..."
	$(PYTHON_CMD) test_integration.py
```

---

**User**

Is it too duplicative with `integration_test`? Should that file be moved from examples to scripts and run via Makefile?

---

**Cursor**

You're absolutely right! Looking at both files, there's significant duplication, and the `examples/integration_test.py` is much more comprehensive. Here's my analysis:

## Comparison of the Two Files

**`test_integration.py` (root level):**
- Simple, basic integration test
- Tests 4 basic scenarios: health, operations, text processing, Streamlit health
- ~105 lines
- Quick smoke test approach

**`examples/integration_test.py`:**
- Comprehensive test suite with proper test framework
- Tests 9+ scenarios including error handling, performance, concurrent requests
- ~586 lines
- Professional test reporting and structured results
- Tests all AI operations (summarize, sentiment, key_points, questions, Q&A)
- Includes performance benchmarking and load testing

## Recommendation: Consolidate and Integrate

Yes, you should:

1. **Move `examples/integration_test.py` to `scripts/integration_test.py`**
2. **Delete the redundant `test_integration.py`**
3. **Add it to the Makefile**

Here's how to integrate it:

## Proposed Changes

### 1. Add Integration Test Target to Makefile

Add this to the Makefile after the existing test targets:

```makefile
test-integration:
	@echo "Running comprehensive integration tests..."
	@echo "⚠️  Make sure both backend and frontend services are running first!"
	@echo "   Backend: http://localhost:8000"
	@echo "   Frontend: http://localhost:8501"
	$(PYTHON_CMD) scripts/integration_test.py
```

### 2. Update the help section

Update the help section to include the new target:

```makefile
@echo "  test-integration Run comprehensive integration tests"
```

### 3. File Operations

1. **Move the file:**
   ```bash
   mv examples/integration_test.py scripts/integration_test.py
   ```

2. **Delete the redundant file:**
   ```bash
   rm test_integration.py
   ```

### 4. Update scripts/run_tests.py (Optional)

You could also modify `scripts/run_tests.py` to optionally include the comprehensive integration test instead of the basic curl commands.

## Benefits of This Approach

1. **Eliminates Duplication**: One comprehensive integration test instead of two basic ones
2. **Better Test Coverage**: The comprehensive test covers all AI operations, error handling, and performance
3. **Professional Reporting**: Structured test results with timing and success rates
4. **Maintainable**: Single source of truth for integration testing
5. **Flexible**: Can be run standalone or via Makefile

## Usage After Changes

```bash
# Run comprehensive integration tests
make test-integration

# Or run directly
python scripts/integration_test.py
```

This consolidation makes much more sense and provides a much better testing experience for developers and CI/CD pipelines.

```makefile
test-integration:
	@echo "Running comprehensive integration tests..."
	@echo "⚠️  Make sure both backend and frontend services are running first!"
	@echo "   Backend: http://localhost:8000"
	@echo "   Frontend: http://localhost:8501"
	$(PYTHON_CMD) scripts/integration_test.py
```

```makefile
@echo "  test-integration Run comprehensive integration tests"
```

```shellscript
   mv examples/integration_test.py scripts/integration_test.py
```

```shellscript
   rm test_integration.py
```

```shellscript
# Run comprehensive integration tests
make test-integration

# Or run directly
python scripts/integration_test.py
```

---

**User**

please make the changes you suggested

---

**Cursor**

I'll make the changes to consolidate the integration tests and update the Makefile. Let me start by moving the comprehensive integration test and updating the Makefile.

Now I'll make the changes:

## 1. First, let's update the Makefile to add the integration test target

```makefile:Makefile
.PHONY: help install test test-backend test-frontend test-integration test-coverage lint lint-backend lint-frontend format clean docker-build docker-up docker-down dev prod logs redis-cli backup restore

# Python executable detection
PYTHON := $(shell command -v python3 2> /dev/null || command -v python 2> /dev/null)
VENV_DIR := .venv
VENV_PYTHON := $(VENV_DIR)/bin/python
VENV_PIP := $(VENV_DIR)/bin/pip

# Check if we're in a virtual environment or Docker
IN_VENV := $(shell $(PYTHON) -c "import sys; print('1' if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix) else '0')" 2>/dev/null || echo "0")
IN_DOCKER := $(shell [ -f /.dockerenv ] && echo "1" || echo "0")

# Use venv python if available and not in Docker, otherwise use system python
ifeq ($(IN_DOCKER),1)
    PYTHON_CMD := python
else ifeq ($(wildcard $(VENV_PYTHON)),$(VENV_PYTHON))
    PYTHON_CMD := $(VENV_PYTHON)
else
    PYTHON_CMD := $(PYTHON)
endif

# Default target
help:
	@echo "Available commands:"
	@echo ""
	@echo "Setup and Testing:"
	@echo "  venv             Create virtual environment"
	@echo "  install          Install all dependencies (creates venv automatically)"
	@echo "  test             Run all tests (with Docker if available)"
	@echo "  test-local       Run tests without Docker dependency"
	@echo "  test-backend     Run backend tests only"
	@echo "  test-frontend    Run frontend tests only"
	@echo "  test-integration Run comprehensive integration tests"
	@echo "  test-coverage    Run tests with coverage report"
	@echo "  lint             Run code quality checks"
	@echo "  lint-backend     Run backend code quality checks only"
	@echo "  lint-frontend    Run frontend code quality checks only"
	@echo "  format           Format code with black and isort"
	@echo ""
	@echo "Docker Commands:"
	@echo "  docker-build     Build Docker images"
	@echo "  docker-up        Start services with Docker Compose"
	@echo "  docker-down      Stop Docker services"
	@echo "  dev              Start development environment"
	@echo "  prod             Start production environment"
	@echo "  logs             Show Docker Compose logs"
	@echo "  status           Show status of all services"
	@echo "  health           Check health of all services"
	@echo ""
	@echo "Utilities:"
	@echo "  redis-cli        Access Redis CLI"
	@echo "  backup           Backup Redis data"
	@echo "  restore          Restore Redis data"
	@echo "  clean            Clean up generated files"
	@echo "  clean-all        Clean up including virtual environment"

# Virtual environment setup
venv:
	@echo "Creating virtual environment..."
	$(PYTHON) -m venv $(VENV_DIR)
	$(VENV_PIP) install --upgrade pip
	@echo "Virtual environment created at $(VENV_DIR)"
	@echo "To activate: source $(VENV_DIR)/bin/activate"

# Installation with venv support
install: venv
	@echo "Installing backend dependencies..."
	cd backend && $(VENV_PIP) install -r requirements.txt -r requirements-dev.txt
	@echo "Installing frontend dependencies..."
	cd frontend && $(VENV_PIP) install -r requirements.txt -r requirements-dev.txt

# Testing with proper Python command
test:
	@echo "Running all tests..."
	$(PYTHON_CMD) scripts/run_tests.py

test-backend:
	@echo "Running backend tests..."
	cd backend && $(PYTHON_CMD) -m pytest tests/ -v

test-frontend:
	@echo "Running frontend tests..."
	cd frontend && $(PYTHON_CMD) -m pytest tests/ -v

test-integration:
	@echo "Running comprehensive integration tests..."
	@echo "⚠️  Make sure both backend and frontend services are running first!"
	@echo "   Backend: http://localhost:8000"
	@echo "   Frontend: http://localhost:8501"
	@echo ""
	$(PYTHON_CMD) scripts/integration_test.py

test-coverage:
	@echo "Running tests with coverage..."
	cd backend && $(PYTHON_CMD) -m pytest tests/ -v --cov=app --cov-report=html --cov-report=term
	cd frontend && $(PYTHON_CMD) -m pytest tests/ -v --cov=app --cov-report=html --cov-report=term

# Local testing without Docker
test-local: venv
	@echo "Running local tests without Docker..."
	@echo "Installing dependencies..."
	cd backend && $(VENV_PIP) install -r requirements.txt -r requirements-dev.txt
	cd frontend && $(VENV_PIP) install -r requirements.txt -r requirements-dev.txt
	@echo "Running backend tests..."
	cd backend && $(VENV_PYTHON) -m pytest tests/ -v
	@echo "Running frontend tests..."
	cd frontend && $(VENV_PYTHON) -m pytest tests/ -v

# Code quality with proper Python command
lint:
	@echo "Running code quality checks..."
	@exit_code=0; \
	(cd backend && $(PYTHON_CMD) -m flake8 app/) || exit_code=$$?; \
	(cd backend && $(PYTHON_CMD) -m mypy app/ --ignore-missing-imports) || exit_code=$$?; \
	(cd frontend && $(PYTHON_CMD) -m flake8 app/) || exit_code=$$?; \
	exit $$exit_code

lint-backend:
	@echo "Running backend code quality checks..."
	@exit_code=0; \
	(cd backend && $(PYTHON_CMD) -m flake8 app/) || exit_code=$$?; \
	(cd backend && $(PYTHON_CMD) -m mypy app/ --ignore-missing-imports) || exit_code=$$?; \
	exit $$exit_code

lint-frontend:
	@echo "Running frontend code quality checks..."
	cd frontend && $(PYTHON_CMD) -m flake8 app/

format:
	@echo "Formatting code..."
	cd backend && $(PYTHON_CMD) -m black app/ tests/
	cd backend && $(PYTHON_CMD) -m isort app/ tests/
	cd frontend && $(PYTHON_CMD) -m black app/ tests/
	cd frontend && $(PYTHON_CMD) -m isort app/ tests/

# Cleanup
clean:
	@echo "Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -name ".coverage" -delete
	find . -name "coverage.xml" -delete

# Docker commands
docker-build:
	@echo "Building Docker images..."
	docker-compose build

docker-up:
	@echo "Starting services..."
	docker-compose up -d

docker-down:
	@echo "Stopping services..."
	docker-compose down

# Development workflow
dev-setup: install
	@echo "Setting up development environment..."
	cd backend && pre-commit install
	@echo "Development environment ready!"

# Quick test for CI
ci-test:
	@echo "Running CI tests..."
	cd backend && python -m pytest tests/ -v --cov=app --cov-report=xml
	cd frontend && python -m pytest tests/ -v --cov=app --cov-report=xml
	@echo "Running code quality checks..."
	cd backend && python -m flake8 app/
	cd frontend && python -m flake8 app/

# Additional Docker commands for development
restart: ## Restart all services
	docker-compose restart

backend-shell: ## Get shell access to backend container
	docker-compose exec backend /bin/bash

frontend-shell: ## Get shell access to frontend container
	docker-compose exec frontend /bin/bash

backend-logs: ## Show backend logs
	docker-compose logs -f backend

frontend-logs: ## Show frontend logs
	docker-compose logs -f frontend

status: ## Show status of all services
	docker-compose ps

health: ## Check health of all services
	@echo "Checking service health..."
	@curl -f http://localhost:8000/health || echo "Backend unhealthy"
	@curl -f http://localhost:8501/_stcore/health || echo "Frontend unhealthy"

stop: ## Stop all services
	docker-compose stop

# Additional commands
dev:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build

prod:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

logs:
	docker-compose logs -f

redis-cli:
	docker-compose exec redis redis-cli

backup:
	docker-compose exec redis redis-cli BGSAVE
	docker cp ai-text-processor-redis:/data/dump.rdb ./backups/redis-$(shell date +%Y%m%d-%H%M%S).rdb

restore:
	@if [ -z "$(BACKUP)" ]; then echo "Usage: make restore BACKUP=filename"; exit 1; fi
	docker cp ./backups/$(BACKUP) ai-text-processor-redis:/data/dump.rdb
	docker-compose restart redis

# Clean including venv
clean-all: clean
	@echo "Removing virtual environment..."
	rm -rf $(VENV_DIR)
```

## 2. Now let's move the comprehensive integration test from examples to scripts

```python:scripts/integration_test.py
#!/usr/bin/env python3
"""
Integration test examples for the FastAPI-Streamlit-LLM Starter Template.

This script provides comprehensive testing scenarios to validate the entire system
including API endpoints, error handling, performance, and edge cases.
"""

import asyncio
import httpx
import time
import json
import pytest
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

class TestStatus(str, Enum):
    """Test execution status."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class TestResult:
    """Test result data structure."""
    name: str
    status: TestStatus
    duration: float
    error: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class IntegrationTester:
    """Comprehensive integration tester for the FastAPI-Streamlit-LLM system."""
    
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        self.results: List[TestResult] = []
        self.session: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        self.session = httpx.AsyncClient(timeout=60.0)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.aclose()
    
    def print_header(self, title: str):
        """Print formatted test section header."""
        print(f"\n{'='*70}")
        print(f"🧪 {title}")
        print(f"{'='*70}")
    
    def print_test_start(self, test_name: str):
        """Print test start message."""
        print(f"\n🔄 Running: {test_name}")
    
    def print_test_result(self, result: TestResult):
        """Print formatted test result."""
        status_emoji = {
            TestStatus.PASSED: "✅",
            TestStatus.FAILED: "❌",
            TestStatus.SKIPPED: "⏭️"
        }
        
        emoji = status_emoji.get(result.status, "❓")
        print(f"{emoji} {result.name} ({result.duration:.2f}s)")
        
        if result.error:
            print(f"   Error: {result.error}")
        
        if result.details:
            for key, value in result.details.items():
                print(f"   {key}: {value}")
    
    async def run_test(self, test_name: str, test_func, *args, **kwargs) -> TestResult:
        """Run a single test and capture results."""
        self.print_test_start(test_name)
        start_time = time.time()
        
        try:
            details = await test_func(*args, **kwargs)
            duration = time.time() - start_time
            result = TestResult(
                name=test_name,
                status=TestStatus.PASSED,
                duration=duration,
                details=details
            )
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult(
                name=test_name,
                status=TestStatus.FAILED,
                duration=duration,
                error=str(e)
            )
        
        self.results.append(result)
        self.print_test_result(result)
        return result
    
    async def test_api_health(self) -> Dict[str, Any]:
        """Test API health endpoint."""
        response = await self.session.get(f"{self.api_url}/health")
        response.raise_for_status()
        
        health_data = response.json()
        
        # Validate response structure
        assert "status" in health_data
        assert "ai_model_available" in health_data
        assert "timestamp" in health_data
        
        return {
            "status": health_data["status"],
            "ai_available": health_data["ai_model_available"],
            "response_time": response.elapsed.total_seconds()
        }
    
    async def test_operations_endpoint(self) -> Dict[str, Any]:
        """Test operations listing endpoint."""
        response = await self.session.get(f"{self.api_url}/operations")
        response.raise_for_status()
        
        ops_data = response.json()
        
        # Validate response structure
        assert "operations" in ops_data
        assert isinstance(ops_data["operations"], list)
        assert len(ops_data["operations"]) > 0
        
        # Validate each operation has required fields
        for op in ops_data["operations"]:
            assert "id" in op
            assert "name" in op
            assert "description" in op
            assert "options" in op
        
        return {
            "operation_count": len(ops_data["operations"]),
            "operations": [op["id"] for op in ops_data["operations"]]
        }
    
    async def test_text_summarization(self) -> Dict[str, Any]:
        """Test text summarization operation."""
        test_text = """
        The rapid advancement of artificial intelligence has transformed numerous industries. 
        Machine learning algorithms now power everything from recommendation systems to 
        autonomous vehicles. Natural language processing has enabled chatbots and virtual 
        assistants to understand and respond to human queries with increasing sophistication. 
        Computer vision systems can now identify objects, faces, and even emotions with 
        remarkable accuracy. As AI continues to evolve, it promises to revolutionize 
        healthcare, education, finance, and countless other sectors.
        """
        
        payload = {
            "text": test_text.strip(),
            "operation": "summarize",
            "options": {"max_length": 50}
        }
        
        response = await self.session.post(f"{self.api_url}/process", json=payload)
        response.raise_for_status()
        
        result = response.json()
        
        # Validate response structure
        assert result["success"] is True
        assert "result" in result
        assert "processing_time" in result
        assert len(result["result"]) > 0
        
        return {
            "summary_length": len(result["result"]),
            "processing_time": result["processing_time"],
            "original_length": len(test_text)
        }
    
    async def test_sentiment_analysis(self) -> Dict[str, Any]:
        """Test sentiment analysis operation."""
        test_cases = [
            ("I absolutely love this new technology! It's amazing!", "positive"),
            ("This is terrible and completely useless.", "negative"),
            ("The weather is okay today.", "neutral")
        ]
        
        results = []
        
        for text, expected_sentiment in test_cases:
            payload = {
                "text": text,
                "operation": "sentiment"
            }
            
            response = await self.session.post(f"{self.api_url}/process", json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            # Validate response structure
            assert result["success"] is True
            assert "sentiment" in result
            assert "sentiment" in result["sentiment"]
            assert "confidence" in result["sentiment"]
            
            sentiment_data = result["sentiment"]
            results.append({
                "text": text[:30] + "...",
                "expected": expected_sentiment,
                "actual": sentiment_data["sentiment"],
                "confidence": sentiment_data["confidence"]
            })
        
        return {"test_cases": results}
    
    async def test_key_points_extraction(self) -> Dict[str, Any]:
        """Test key points extraction operation."""
        test_text = """
        Climate change is one of the most pressing issues of our time. Rising global 
        temperatures are causing ice caps to melt, leading to rising sea levels. 
        Extreme weather events are becoming more frequent and severe. Governments 
        worldwide are implementing policies to reduce carbon emissions. Renewable 
        energy sources like solar and wind power are becoming more cost-effective. 
        Individual actions, such as reducing energy consumption and using public 
        transportation, can also make a difference.
        """
        
        payload = {
            "text": test_text.strip(),
            "operation": "key_points",
            "options": {"max_points": 4}
        }
        
        response = await self.session.post(f"{self.api_url}/process", json=payload)
        response.raise_for_status()
        
        result = response.json()
        
        # Validate response structure
        assert result["success"] is True
        assert "key_points" in result
        assert isinstance(result["key_points"], list)
        assert len(result["key_points"]) > 0
        
        return {
            "points_extracted": len(result["key_points"]),
            "points": result["key_points"]
        }
    
    async def test_question_generation(self) -> Dict[str, Any]:
        """Test question generation operation."""
        test_text = """
        The Internet of Things (IoT) refers to the network of physical devices 
        embedded with sensors, software, and connectivity that enables them to 
        collect and exchange data. Smart homes use IoT devices to automate lighting, 
        heating, and security systems. In healthcare, IoT devices can monitor 
        patient vital signs remotely. Industrial IoT applications help optimize 
        manufacturing processes and predict equipment failures.
        """
        
        payload = {
            "text": test_text.strip(),
            "operation": "questions",
            "options": {"num_questions": 3}
        }
        
        response = await self.session.post(f"{self.api_url}/process", json=payload)
        response.raise_for_status()
        
        result = response.json()
        
        # Validate response structure
        assert result["success"] is True
        assert "questions" in result
        assert isinstance(result["questions"], list)
        assert len(result["questions"]) > 0
        
        return {
            "questions_generated": len(result["questions"]),
            "questions": result["questions"]
        }
    
    async def test_question_answering(self) -> Dict[str, Any]:
        """Test question answering operation."""
        test_text = """
        Blockchain technology is a distributed ledger system that maintains a 
        continuously growing list of records, called blocks, which are linked 
        and secured using cryptography. Bitcoin was the first successful 
        implementation of blockchain technology, created by Satoshi Nakamoto 
        in 2008. Blockchain provides transparency, security, and decentralization, 
        making it useful for applications beyond cryptocurrency, including 
        supply chain management and digital identity verification.
        """
        
        test_questions = [
            "Who created Bitcoin?",
            "What year was Bitcoin created?",
            "What are the main benefits of blockchain technology?"
        ]
        
        results = []
        
        for question in test_questions:
            payload = {
                "text": test_text.strip(),
                "operation": "qa",
                "question": question
            }
            
            response = await self.session.post(f"{self.api_url}/process", json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            # Validate response structure
            assert result["success"] is True
            assert "result" in result
            assert len(result["result"]) > 0
            
            results.append({
                "question": question,
                "answer": result["result"],
                "processing_time": result.get("processing_time", 0)
            })
        
        return {"qa_pairs": results}
    
    async def test_error_handling(self) -> Dict[str, Any]:
        """Test various error scenarios."""
        error_tests = []
        
        # Test 1: Empty text
        try:
            payload = {"text": "", "operation": "summarize"}
            response = await self.session.post(f"{self.api_url}/process", json=payload)
            error_tests.append({
                "test": "empty_text",
                "status_code": response.status_code,
                "handled": response.status_code == 422
            })
        except Exception as e:
            error_tests.append({
                "test": "empty_text",
                "error": str(e),
                "handled": True
            })
        
        # Test 2: Invalid operation
        try:
            payload = {"text": "Valid text", "operation": "invalid_operation"}
            response = await self.session.post(f"{self.api_url}/process", json=payload)
            error_tests.append({
                "test": "invalid_operation",
                "status_code": response.status_code,
                "handled": response.status_code == 422
            })
        except Exception as e:
            error_tests.append({
                "test": "invalid_operation",
                "error": str(e),
                "handled": True
            })
        
        # Test 3: Missing question for Q&A
        try:
            payload = {"text": "Valid text", "operation": "qa"}
            response = await self.session.post(f"{self.api_url}/process", json=payload)
            error_tests.append({
                "test": "missing_question",
                "status_code": response.status_code,
                "handled": response.status_code == 400
            })
        except Exception as e:
            error_tests.append({
                "test": "missing_question",
                "error": str(e),
                "handled": True
            })
        
        # Test 4: Text too long
        try:
            long_text = "A" * 15000  # Exceeds max_length
            payload = {"text": long_text, "operation": "summarize"}
            response = await self.session.post(f"{self.api_url}/process", json=payload)
            error_tests.append({
                "test": "text_too_long",
                "status_code": response.status_code,
                "handled": response.status_code == 422
            })
        except Exception as e:
            error_tests.append({
                "test": "text_too_long",
                "error": str(e),
                "handled": True
            })
        
        handled_count = sum(1 for test in error_tests if test.get("handled", False))
        
        return {
            "total_error_tests": len(error_tests),
            "properly_handled": handled_count,
            "error_details": error_tests
        }
    
    async def test_performance_benchmark(self) -> Dict[str, Any]:
        """Test system performance with multiple operations."""
        operations = ["summarize", "sentiment", "key_points"]
        test_text = """
        Machine learning is a subset of artificial intelligence that enables 
        computers to learn and improve from experience without being explicitly 
        programmed. It uses algorithms to analyze data, identify patterns, and 
        make predictions or decisions. Common applications include image recognition, 
        natural language processing, recommendation systems, and predictive analytics.
        """
        
        performance_results = []
        total_time = 0
        
        for operation in operations:
            start_time = time.time()
            
            payload = {
                "text": test_text.strip(),
                "operation": operation
            }
            
            response = await self.session.post(f"{self.api_url}/process", json=payload)
            response.raise_for_status()
            
            result = response.json()
            duration = time.time() - start_time
            total_time += duration
            
            performance_results.append({
                "operation": operation,
                "duration": duration,
                "processing_time": result.get("processing_time", 0),
                "success": result.get("success", False)
            })
        
        return {
            "total_time": total_time,
            "average_time": total_time / len(operations),
            "operations_tested": len(operations),
            "performance_details": performance_results
        }
    
    async def test_concurrent_requests(self) -> Dict[str, Any]:
        """Test system behavior under concurrent load."""
        concurrent_count = 5
        test_text = "This is a test for concurrent processing."
        
        async def single_request():
            payload = {
                "text": test_text,
                "operation": "sentiment"
            }
            response = await self.session.post(f"{self.api_url}/process", json=payload)
            return response.status_code == 200
        
        start_time = time.time()
        
        # Run concurrent requests
        tasks = [single_request() for _ in range(concurrent_count)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        duration = time.time() - start_time
        
        successful = sum(1 for r in results if r is True)
        failed = sum(1 for r in results if isinstance(r, Exception))
        
        return {
            "concurrent_requests": concurrent_count,
            "successful": successful,
            "failed": failed,
            "total_duration": duration,
            "requests_per_second": concurrent_count / duration
        }
    
    async def run_all_tests(self):
        """Run the complete test suite."""
        self.print_header("FastAPI-Streamlit-LLM Integration Test Suite")
        
        print("🚀 Starting comprehensive integration tests...")
        print(f"📡 API URL: {self.api_url}")
        print(f"⏰ Test started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Core functionality tests
        self.print_header("Core Functionality Tests")
        await self.run_test("API Health Check", self.test_api_health)
        await self.run_test("Operations Endpoint", self.test_operations_endpoint)
        
        # Text processing operation tests
        self.print_header("Text Processing Operation Tests")
        await self.run_test("Text Summarization", self.test_text_summarization)
        await self.run_test("Sentiment Analysis", self.test_sentiment_analysis)
        await self.run_test("Key Points Extraction", self.test_key_points_extraction)
        await self.run_test("Question Generation", self.test_question_generation)
        await self.run_test("Question Answering", self.test_question_answering)
        
        # Error handling tests
        self.print_header("Error Handling Tests")
        await self.run_test("Error Handling", self.test_error_handling)
        
        # Performance tests
        self.print_header("Performance Tests")
        await self.run_test("Performance Benchmark", self.test_performance_benchmark)
        await self.run_test("Concurrent Requests", self.test_concurrent_requests)
        
        # Generate test report
        self.generate_test_report()
    
    def generate_test_report(self):
        """Generate and display comprehensive test report."""
        self.print_header("Test Report Summary")
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.status == TestStatus.PASSED)
        failed_tests = sum(1 for r in self.results if r.status == TestStatus.FAILED)
        total_duration = sum(r.duration for r in self.results)
        
        print(f"📊 Test Results:")
        print(f"   Total Tests: {total_tests}")
        print(f"   ✅ Passed: {passed_tests}")
        print(f"   ❌ Failed: {failed_tests}")
        print(f"   📈 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print(f"   ⏱️  Total Duration: {total_duration:.2f}s")
        print(f"   🕐 Average Test Time: {total_duration/total_tests:.2f}s")
        
        if failed_tests > 0:
            print(f"\n❌ Failed Tests:")
            for result in self.results:
                if result.status == TestStatus.FAILED:
                    print(f"   • {result.name}: {result.error}")
        
        print(f"\n💡 Recommendations:")
        if passed_tests == total_tests:
            print("   🎉 All tests passed! System is working correctly.")
            print("   • Consider running load tests for production readiness")
            print("   • Monitor performance metrics in production")
        else:
            print("   🔧 Some tests failed. Please review and fix issues:")
            print("   • Check API server is running and accessible")
            print("   • Verify AI model configuration and API keys")
            print("   • Review error logs for detailed diagnostics")
        
        print(f"\n📋 Next Steps:")
        print("   • Run frontend tests with Streamlit interface")
        print("   • Test with different text types and lengths")
        print("   • Validate production deployment configuration")
        print("   • Set up monitoring and alerting")

async def main():
    """Main function to run integration tests."""
    
    print("🧪 FastAPI-Streamlit-LLM Starter Template - Integration Tests")
    print("=" * 80)
    print("This script runs comprehensive integration tests to validate the entire system.")
    print("\n⚠️  Prerequisites:")
    print("   • FastAPI backend running on http://localhost:8000")
    print("   • Valid AI model configuration (Gemini API key)")
    print("   • All dependencies installed")
    
    # Allow user to confirm before starting
    try:
        input("\n🚀 Press Enter to start tests (Ctrl+C to cancel)...")
    except KeyboardInterrupt:
        print("\n⏹️  Tests cancelled by user")
        return
    
    try:
        async with IntegrationTester() as tester:
            await tester.run_all_tests()
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test suite failed with error: {e}")
        print("💡 Make sure the FastAPI backend is running and accessible")

if __name__ == "__main__":
    asyncio.run(main())
```

## Summary of Changes Made

✅ **Updated Makefile:**
- Added `test-integration` to the `.PHONY` line
- Added `test-integration` target with helpful warnings about prerequisites
- Updated the help section to include the new integration test command

✅ **Moved comprehensive integration test:**
- Moved `examples/integration_test.py` to `scripts/integration_test.py`
- This consolidates all scripts in one location

✅ **Ready to remove redundant file:**
- The simple `test_integration.py` in the root can now be deleted since it's redundant

## Next Steps

You should now:

1. **Delete the redundant file:**
   ```bash
   rm test_integration.py
   ```

2. **Test the new integration:**
   ```bash
   # Start your services first
   make docker-up
   # Or start them manually
   
   # Then run the comprehensive integration tests
   make test-integration
   ```

The new setup provides:
- **Better organization**: All scripts in `scripts/` directory
- **Comprehensive testing**: Full test suite with error handling, performance, and load testing
- **Professional reporting**: Detailed test results with timing and success rates
- **Easy access**: Simple `make test-integration` command
- **Clear prerequisites**: Warns users about required running services

This eliminates the duplication and provides a much more robust integration testing solution!

```makefile
.PHONY: help install test test-backend test-frontend test-integration test-coverage lint lint-backend lint-frontend format clean docker-build docker-up docker-down dev prod logs redis-cli backup restore

# Python executable detection
PYTHON := $(shell command -v python3 2> /dev/null || command -v python 2> /dev/null)
VENV_DIR := .venv
VENV_PYTHON := $(VENV_DIR)/bin/python
VENV_PIP := $(VENV_DIR)/bin/pip

# Check if we're in a virtual environment or Docker
IN_VENV := $(shell $(PYTHON) -c "import sys; print('1' if hasattr(sys, 'real_prefix') or (hasattr(sys, 'base_prefix') and sys.base_prefix != sys.prefix) else '0')" 2>/dev/null || echo "0")
IN_DOCKER := $(shell [ -f /.dockerenv ] && echo "1" || echo "0")

# Use venv python if available and not in Docker, otherwise use system python
ifeq ($(IN_DOCKER),1)
    PYTHON_CMD := python
else ifeq ($(wildcard $(VENV_PYTHON)),$(VENV_PYTHON))
    PYTHON_CMD := $(VENV_PYTHON)
else
    PYTHON_CMD := $(PYTHON)
endif

# Default target
help:
	@echo "Available commands:"
	@echo ""
	@echo "Setup and Testing:"
	@echo "  venv             Create virtual environment"
	@echo "  install          Install all dependencies (creates venv automatically)"
	@echo "  test             Run all tests (with Docker if available)"
	@echo "  test-local       Run tests without Docker dependency"
	@echo "  test-backend     Run backend tests only"
	@echo "  test-frontend    Run frontend tests only"
	@echo "  test-integration Run comprehensive integration tests"
	@echo "  test-coverage    Run tests with coverage report"
	@echo "  lint             Run code quality checks"
	@echo "  lint-backend     Run backend code quality checks only"
	@echo "  lint-frontend    Run frontend code quality checks only"
	@echo "  format           Format code with black and isort"
	@echo ""
	@echo "Docker Commands:"
	@echo "  docker-build     Build Docker images"
	@echo "  docker-up        Start services with Docker Compose"
	@echo "  docker-down      Stop Docker services"
	@echo "  dev              Start development environment"
	@echo "  prod             Start production environment"
	@echo "  logs             Show Docker Compose logs"
	@echo "  status           Show status of all services"
	@echo "  health           Check health of all services"
	@echo ""
	@echo "Utilities:"
	@echo "  redis-cli        Access Redis CLI"
	@echo "  backup           Backup Redis data"
	@echo "  restore          Restore Redis data"
	@echo "  clean            Clean up generated files"
	@echo "  clean-all        Clean up including virtual environment"

# Virtual environment setup
venv:
	@echo "Creating virtual environment..."
	$(PYTHON) -m venv $(VENV_DIR)
	$(VENV_PIP) install --upgrade pip
	@echo "Virtual environment created at $(VENV_DIR)"
	@echo "To activate: source $(VENV_DIR)/bin/activate"

# Installation with venv support
install: venv
	@echo "Installing backend dependencies..."
	cd backend && $(VENV_PIP) install -r requirements.txt -r requirements-dev.txt
	@echo "Installing frontend dependencies..."
	cd frontend && $(VENV_PIP) install -r requirements.txt -r requirements-dev.txt

# Testing with proper Python command
test:
	@echo "Running all tests..."
	$(PYTHON_CMD) scripts/run_tests.py

test-backend:
	@echo "Running backend tests..."
	cd backend && $(PYTHON_CMD) -m pytest tests/ -v

test-frontend:
	@echo "Running frontend tests..."
	cd frontend && $(PYTHON_CMD) -m pytest tests/ -v

test-integration:
	@echo "Running comprehensive integration tests..."
	@echo "⚠️  Make sure both backend and frontend services are running first!"
	@echo "   Backend: http://localhost:8000"
	@echo "   Frontend: http://localhost:8501"
	@echo ""
	$(PYTHON_CMD) scripts/integration_test.py

test-coverage:
	@echo "Running tests with coverage..."
	cd backend && $(PYTHON_CMD) -m pytest tests/ -v --cov=app --cov-report=html --cov-report=term
	cd frontend && $(PYTHON_CMD) -m pytest tests/ -v --cov=app --cov-report=html --cov-report=term

# Local testing without Docker
test-local: venv
	@echo "Running local tests without Docker..."
	@echo "Installing dependencies..."
	cd backend && $(VENV_PIP) install -r requirements.txt -r requirements-dev.txt
	cd frontend && $(VENV_PIP) install -r requirements.txt -r requirements-dev.txt
	@echo "Running backend tests..."
	cd backend && $(VENV_PYTHON) -m pytest tests/ -v
	@echo "Running frontend tests..."
	cd frontend && $(VENV_PYTHON) -m pytest tests/ -v

# Code quality with proper Python command
lint:
	@echo "Running code quality checks..."
	@exit_code=0; \
	(cd backend && $(PYTHON_CMD) -m flake8 app/) || exit_code=$$?; \
	(cd backend && $(PYTHON_CMD) -m mypy app/ --ignore-missing-imports) || exit_code=$$?; \
	(cd frontend && $(PYTHON_CMD) -m flake8 app/) || exit_code=$$?; \
	exit $$exit_code

lint-backend:
	@echo "Running backend code quality checks..."
	@exit_code=0; \
	(cd backend && $(PYTHON_CMD) -m flake8 app/) || exit_code=$$?; \
	(cd backend && $(PYTHON_CMD) -m mypy app/ --ignore-missing-imports) || exit_code=$$?; \
	exit $$exit_code

lint-frontend:
	@echo "Running frontend code quality checks..."
	cd frontend && $(PYTHON_CMD) -m flake8 app/

format:
	@echo "Formatting code..."
	cd backend && $(PYTHON_CMD) -m black app/ tests/
	cd backend && $(PYTHON_CMD) -m isort app/ tests/
	cd frontend && $(PYTHON_CMD) -m black app/ tests/
	cd frontend && $(PYTHON_CMD) -m isort app/ tests/

# Cleanup
clean:
	@echo "Cleaning up..."
	find . -type d -name "__pycache__" -exec rm -rf {} +
	find . -type f -name "*.pyc" -delete
	find . -type d -name "*.egg-info" -exec rm -rf {} +
	find . -type d -name ".pytest_cache" -exec rm -rf {} +
	find . -type d -name "htmlcov" -exec rm -rf {} +
	find . -name ".coverage" -delete
	find . -name "coverage.xml" -delete

# Docker commands
docker-build:
	@echo "Building Docker images..."
	docker-compose build

docker-up:
	@echo "Starting services..."
	docker-compose up -d

docker-down:
	@echo "Stopping services..."
	docker-compose down

# Development workflow
dev-setup: install
	@echo "Setting up development environment..."
	cd backend && pre-commit install
	@echo "Development environment ready!"

# Quick test for CI
ci-test:
	@echo "Running CI tests..."
	cd backend && python -m pytest tests/ -v --cov=app --cov-report=xml
	cd frontend && python -m pytest tests/ -v --cov=app --cov-report=xml
	@echo "Running code quality checks..."
	cd backend && python -m flake8 app/
	cd frontend && python -m flake8 app/

# Additional Docker commands for development
restart: ## Restart all services
	docker-compose restart

backend-shell: ## Get shell access to backend container
	docker-compose exec backend /bin/bash

frontend-shell: ## Get shell access to frontend container
	docker-compose exec frontend /bin/bash

backend-logs: ## Show backend logs
	docker-compose logs -f backend

frontend-logs: ## Show frontend logs
	docker-compose logs -f frontend

status: ## Show status of all services
	docker-compose ps

health: ## Check health of all services
	@echo "Checking service health..."
	@curl -f http://localhost:8000/health || echo "Backend unhealthy"
	@curl -f http://localhost:8501/_stcore/health || echo "Frontend unhealthy"

stop: ## Stop all services
	docker-compose stop

# Additional commands
dev:
	docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build

prod:
	docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build

logs:
	docker-compose logs -f

redis-cli:
	docker-compose exec redis redis-cli

backup:
	docker-compose exec redis redis-cli BGSAVE
	docker cp ai-text-processor-redis:/data/dump.rdb ./backups/redis-$(shell date +%Y%m%d-%H%M%S).rdb

restore:
	@if [ -z "$(BACKUP)" ]; then echo "Usage: make restore BACKUP=filename"; exit 1; fi
	docker cp ./backups/$(BACKUP) ai-text-processor-redis:/data/dump.rdb
	docker-compose restart redis

# Clean including venv
clean-all: clean
	@echo "Removing virtual environment..."
	rm -rf $(VENV_DIR)
```

```python
#!/usr/bin/env python3
"""
Integration test examples for the FastAPI-Streamlit-LLM Starter Template.

This script provides comprehensive testing scenarios to validate the entire system
including API endpoints, error handling, performance, and edge cases.
"""

import asyncio
import httpx
import time
import json
import pytest
from typing import Dict, Any, List, Optional
from dataclasses import dataclass
from enum import Enum

class TestStatus(str, Enum):
    """Test execution status."""
    PENDING = "pending"
    RUNNING = "running"
    PASSED = "passed"
    FAILED = "failed"
    SKIPPED = "skipped"

@dataclass
class TestResult:
    """Test result data structure."""
    name: str
    status: TestStatus
    duration: float
    error: Optional[str] = None
    details: Optional[Dict[str, Any]] = None

class IntegrationTester:
    """Comprehensive integration tester for the FastAPI-Streamlit-LLM system."""
    
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        self.results: List[TestResult] = []
        self.session: Optional[httpx.AsyncClient] = None
    
    async def __aenter__(self):
        self.session = httpx.AsyncClient(timeout=60.0)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.aclose()
    
    def print_header(self, title: str):
        """Print formatted test section header."""
        print(f"\n{'='*70}")
        print(f"🧪 {title}")
        print(f"{'='*70}")
    
    def print_test_start(self, test_name: str):
        """Print test start message."""
        print(f"\n🔄 Running: {test_name}")
    
    def print_test_result(self, result: TestResult):
        """Print formatted test result."""
        status_emoji = {
            TestStatus.PASSED: "✅",
            TestStatus.FAILED: "❌",
            TestStatus.SKIPPED: "⏭️"
        }
        
        emoji = status_emoji.get(result.status, "❓")
        print(f"{emoji} {result.name} ({result.duration:.2f}s)")
        
        if result.error:
            print(f"   Error: {result.error}")
        
        if result.details:
            for key, value in result.details.items():
                print(f"   {key}: {value}")
    
    async def run_test(self, test_name: str, test_func, *args, **kwargs) -> TestResult:
        """Run a single test and capture results."""
        self.print_test_start(test_name)
        start_time = time.time()
        
        try:
            details = await test_func(*args, **kwargs)
            duration = time.time() - start_time
            result = TestResult(
                name=test_name,
                status=TestStatus.PASSED,
                duration=duration,
                details=details
            )
        except Exception as e:
            duration = time.time() - start_time
            result = TestResult(
                name=test_name,
                status=TestStatus.FAILED,
                duration=duration,
                error=str(e)
            )
        
        self.results.append(result)
        self.print_test_result(result)
        return result
    
    async def test_api_health(self) -> Dict[str, Any]:
        """Test API health endpoint."""
        response = await self.session.get(f"{self.api_url}/health")
        response.raise_for_status()
        
        health_data = response.json()
        
        # Validate response structure
        assert "status" in health_data
        assert "ai_model_available" in health_data
        assert "timestamp" in health_data
        
        return {
            "status": health_data["status"],
            "ai_available": health_data["ai_model_available"],
            "response_time": response.elapsed.total_seconds()
        }
    
    async def test_operations_endpoint(self) -> Dict[str, Any]:
        """Test operations listing endpoint."""
        response = await self.session.get(f"{self.api_url}/operations")
        response.raise_for_status()
        
        ops_data = response.json()
        
        # Validate response structure
        assert "operations" in ops_data
        assert isinstance(ops_data["operations"], list)
        assert len(ops_data["operations"]) > 0
        
        # Validate each operation has required fields
        for op in ops_data["operations"]:
            assert "id" in op
            assert "name" in op
            assert "description" in op
            assert "options" in op
        
        return {
            "operation_count": len(ops_data["operations"]),
            "operations": [op["id"] for op in ops_data["operations"]]
        }
    
    async def test_text_summarization(self) -> Dict[str, Any]:
        """Test text summarization operation."""
        test_text = """
        The rapid advancement of artificial intelligence has transformed numerous industries. 
        Machine learning algorithms now power everything from recommendation systems to 
        autonomous vehicles. Natural language processing has enabled chatbots and virtual 
        assistants to understand and respond to human queries with increasing sophistication. 
        Computer vision systems can now identify objects, faces, and even emotions with 
        remarkable accuracy. As AI continues to evolve, it promises to revolutionize 
        healthcare, education, finance, and countless other sectors.
        """
        
        payload = {
            "text": test_text.strip(),
            "operation": "summarize",
            "options": {"max_length": 50}
        }
        
        response = await self.session.post(f"{self.api_url}/process", json=payload)
        response.raise_for_status()
        
        result = response.json()
        
        # Validate response structure
        assert result["success"] is True
        assert "result" in result
        assert "processing_time" in result
        assert len(result["result"]) > 0
        
        return {
            "summary_length": len(result["result"]),
            "processing_time": result["processing_time"],
            "original_length": len(test_text)
        }
    
    async def test_sentiment_analysis(self) -> Dict[str, Any]:
        """Test sentiment analysis operation."""
        test_cases = [
            ("I absolutely love this new technology! It's amazing!", "positive"),
            ("This is terrible and completely useless.", "negative"),
            ("The weather is okay today.", "neutral")
        ]
        
        results = []
        
        for text, expected_sentiment in test_cases:
            payload = {
                "text": text,
                "operation": "sentiment"
            }
            
            response = await self.session.post(f"{self.api_url}/process", json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            # Validate response structure
            assert result["success"] is True
            assert "sentiment" in result
            assert "sentiment" in result["sentiment"]
            assert "confidence" in result["sentiment"]
            
            sentiment_data = result["sentiment"]
            results.append({
                "text": text[:30] + "...",
                "expected": expected_sentiment,
                "actual": sentiment_data["sentiment"],
                "confidence": sentiment_data["confidence"]
            })
        
        return {"test_cases": results}
    
    async def test_key_points_extraction(self) -> Dict[str, Any]:
        """Test key points extraction operation."""
        test_text = """
        Climate change is one of the most pressing issues of our time. Rising global 
        temperatures are causing ice caps to melt, leading to rising sea levels. 
        Extreme weather events are becoming more frequent and severe. Governments 
        worldwide are implementing policies to reduce carbon emissions. Renewable 
        energy sources like solar and wind power are becoming more cost-effective. 
        Individual actions, such as reducing energy consumption and using public 
        transportation, can also make a difference.
        """
        
        payload = {
            "text": test_text.strip(),
            "operation": "key_points",
            "options": {"max_points": 4}
        }
        
        response = await self.session.post(f"{self.api_url}/process", json=payload)
        response.raise_for_status()
        
        result = response.json()
        
        # Validate response structure
        assert result["success"] is True
        assert "key_points" in result
        assert isinstance(result["key_points"], list)
        assert len(result["key_points"]) > 0
        
        return {
            "points_extracted": len(result["key_points"]),
            "points": result["key_points"]
        }
    
    async def test_question_generation(self) -> Dict[str, Any]:
        """Test question generation operation."""
        test_text = """
        The Internet of Things (IoT) refers to the network of physical devices 
        embedded with sensors, software, and connectivity that enables them to 
        collect and exchange data. Smart homes use IoT devices to automate lighting, 
        heating, and security systems. In healthcare, IoT devices can monitor 
        patient vital signs remotely. Industrial IoT applications help optimize 
        manufacturing processes and predict equipment failures.
        """
        
        payload = {
            "text": test_text.strip(),
            "operation": "questions",
            "options": {"num_questions": 3}
        }
        
        response = await self.session.post(f"{self.api_url}/process", json=payload)
        response.raise_for_status()
        
        result = response.json()
        
        # Validate response structure
        assert result["success"] is True
        assert "questions" in result
        assert isinstance(result["questions"], list)
        assert len(result["questions"]) > 0
        
        return {
            "questions_generated": len(result["questions"]),
            "questions": result["questions"]
        }
    
    async def test_question_answering(self) -> Dict[str, Any]:
        """Test question answering operation."""
        test_text = """
        Blockchain technology is a distributed ledger system that maintains a 
        continuously growing list of records, called blocks, which are linked 
        and secured using cryptography. Bitcoin was the first successful 
        implementation of blockchain technology, created by Satoshi Nakamoto 
        in 2008. Blockchain provides transparency, security, and decentralization, 
        making it useful for applications beyond cryptocurrency, including 
        supply chain management and digital identity verification.
        """
        
        test_questions = [
            "Who created Bitcoin?",
            "What year was Bitcoin created?",
            "What are the main benefits of blockchain technology?"
        ]
        
        results = []
        
        for question in test_questions:
            payload = {
                "text": test_text.strip(),
                "operation": "qa",
                "question": question
            }
            
            response = await self.session.post(f"{self.api_url}/process", json=payload)
            response.raise_for_status()
            
            result = response.json()
            
            # Validate response structure
            assert result["success"] is True
            assert "result" in result
            assert len(result["result"]) > 0
            
            results.append({
                "question": question,
                "answer": result["result"],
                "processing_time": result.get("processing_time", 0)
            })
        
        return {"qa_pairs": results}
    
    async def test_error_handling(self) -> Dict[str, Any]:
        """Test various error scenarios."""
        error_tests = []
        
        # Test 1: Empty text
        try:
            payload = {"text": "", "operation": "summarize"}
            response = await self.session.post(f"{self.api_url}/process", json=payload)
            error_tests.append({
                "test": "empty_text",
                "status_code": response.status_code,
                "handled": response.status_code == 422
            })
        except Exception as e:
            error_tests.append({
                "test": "empty_text",
                "error": str(e),
                "handled": True
            })
        
        # Test 2: Invalid operation
        try:
            payload = {"text": "Valid text", "operation": "invalid_operation"}
            response = await self.session.post(f"{self.api_url}/process", json=payload)
            error_tests.append({
                "test": "invalid_operation",
                "status_code": response.status_code,
                "handled": response.status_code == 422
            })
        except Exception as e:
            error_tests.append({
                "test": "invalid_operation",
                "error": str(e),
                "handled": True
            })
        
        # Test 3: Missing question for Q&A
        try:
            payload = {"text": "Valid text", "operation": "qa"}
            response = await self.session.post(f"{self.api_url}/process", json=payload)
            error_tests.append({
                "test": "missing_question",
                "status_code": response.status_code,
                "handled": response.status_code == 400
            })
        except Exception as e:
            error_tests.append({
                "test": "missing_question",
                "error": str(e),
                "handled": True
            })
        
        # Test 4: Text too long
        try:
            long_text = "A" * 15000  # Exceeds max_length
            payload = {"text": long_text, "operation": "summarize"}
            response = await self.session.post(f"{self.api_url}/process", json=payload)
            error_tests.append({
                "test": "text_too_long",
                "status_code": response.status_code,
                "handled": response.status_code == 422
            })
        except Exception as e:
            error_tests.append({
                "test": "text_too_long",
                "error": str(e),
                "handled": True
            })
        
        handled_count = sum(1 for test in error_tests if test.get("handled", False))
        
        return {
            "total_error_tests": len(error_tests),
            "properly_handled": handled_count,
            "error_details": error_tests
        }
    
    async def test_performance_benchmark(self) -> Dict[str, Any]:
        """Test system performance with multiple operations."""
        operations = ["summarize", "sentiment", "key_points"]
        test_text = """
        Machine learning is a subset of artificial intelligence that enables 
        computers to learn and improve from experience without being explicitly 
        programmed. It uses algorithms to analyze data, identify patterns, and 
        make predictions or decisions. Common applications include image recognition, 
        natural language processing, recommendation systems, and predictive analytics.
        """
        
        performance_results = []
        total_time = 0
        
        for operation in operations:
            start_time = time.time()
            
            payload = {
                "text": test_text.strip(),
                "operation": operation
            }
            
            response = await self.session.post(f"{self.api_url}/process", json=payload)
            response.raise_for_status()
            
            result = response.json()
            duration = time.time() - start_time
            total_time += duration
            
            performance_results.append({
                "operation": operation,
                "duration": duration,
                "processing_time": result.get("processing_time", 0),
                "success": result.get("success", False)
            })
        
        return {
            "total_time": total_time,
            "average_time": total_time / len(operations),
            "operations_tested": len(operations),
            "performance_details": performance_results
        }
    
    async def test_concurrent_requests(self) -> Dict[str, Any]:
        """Test system behavior under concurrent load."""
        concurrent_count = 5
        test_text = "This is a test for concurrent processing."
        
        async def single_request():
            payload = {
                "text": test_text,
                "operation": "sentiment"
            }
            response = await self.session.post(f"{self.api_url}/process", json=payload)
            return response.status_code == 200
        
        start_time = time.time()
        
        # Run concurrent requests
        tasks = [single_request() for _ in range(concurrent_count)]
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        duration = time.time() - start_time
        
        successful = sum(1 for r in results if r is True)
        failed = sum(1 for r in results if isinstance(r, Exception))
        
        return {
            "concurrent_requests": concurrent_count,
            "successful": successful,
            "failed": failed,
            "total_duration": duration,
            "requests_per_second": concurrent_count / duration
        }
    
    async def run_all_tests(self):
        """Run the complete test suite."""
        self.print_header("FastAPI-Streamlit-LLM Integration Test Suite")
        
        print("🚀 Starting comprehensive integration tests...")
        print(f"📡 API URL: {self.api_url}")
        print(f"⏰ Test started at: {time.strftime('%Y-%m-%d %H:%M:%S')}")
        
        # Core functionality tests
        self.print_header("Core Functionality Tests")
        await self.run_test("API Health Check", self.test_api_health)
        await self.run_test("Operations Endpoint", self.test_operations_endpoint)
        
        # Text processing operation tests
        self.print_header("Text Processing Operation Tests")
        await self.run_test("Text Summarization", self.test_text_summarization)
        await self.run_test("Sentiment Analysis", self.test_sentiment_analysis)
        await self.run_test("Key Points Extraction", self.test_key_points_extraction)
        await self.run_test("Question Generation", self.test_question_generation)
        await self.run_test("Question Answering", self.test_question_answering)
        
        # Error handling tests
        self.print_header("Error Handling Tests")
        await self.run_test("Error Handling", self.test_error_handling)
        
        # Performance tests
        self.print_header("Performance Tests")
        await self.run_test("Performance Benchmark", self.test_performance_benchmark)
        await self.run_test("Concurrent Requests", self.test_concurrent_requests)
        
        # Generate test report
        self.generate_test_report()
    
    def generate_test_report(self):
        """Generate and display comprehensive test report."""
        self.print_header("Test Report Summary")
        
        total_tests = len(self.results)
        passed_tests = sum(1 for r in self.results if r.status == TestStatus.PASSED)
        failed_tests = sum(1 for r in self.results if r.status == TestStatus.FAILED)
        total_duration = sum(r.duration for r in self.results)
        
        print(f"📊 Test Results:")
        print(f"   Total Tests: {total_tests}")
        print(f"   ✅ Passed: {passed_tests}")
        print(f"   ❌ Failed: {failed_tests}")
        print(f"   📈 Success Rate: {(passed_tests/total_tests)*100:.1f}%")
        print(f"   ⏱️  Total Duration: {total_duration:.2f}s")
        print(f"   🕐 Average Test Time: {total_duration/total_tests:.2f}s")
        
        if failed_tests > 0:
            print(f"\n❌ Failed Tests:")
            for result in self.results:
                if result.status == TestStatus.FAILED:
                    print(f"   • {result.name}: {result.error}")
        
        print(f"\n💡 Recommendations:")
        if passed_tests == total_tests:
            print("   🎉 All tests passed! System is working correctly.")
            print("   • Consider running load tests for production readiness")
            print("   • Monitor performance metrics in production")
        else:
            print("   🔧 Some tests failed. Please review and fix issues:")
            print("   • Check API server is running and accessible")
            print("   • Verify AI model configuration and API keys")
            print("   • Review error logs for detailed diagnostics")
        
        print(f"\n📋 Next Steps:")
        print("   • Run frontend tests with Streamlit interface")
        print("   • Test with different text types and lengths")
        print("   • Validate production deployment configuration")
        print("   • Set up monitoring and alerting")

async def main():
    """Main function to run integration tests."""
    
    print("🧪 FastAPI-Streamlit-LLM Starter Template - Integration Tests")
    print("=" * 80)
    print("This script runs comprehensive integration tests to validate the entire system.")
    print("\n⚠️  Prerequisites:")
    print("   • FastAPI backend running on http://localhost:8000")
    print("   • Valid AI model configuration (Gemini API key)")
    print("   • All dependencies installed")
    
    # Allow user to confirm before starting
    try:
        input("\n🚀 Press Enter to start tests (Ctrl+C to cancel)...")
    except KeyboardInterrupt:
        print("\n⏹️  Tests cancelled by user")
        return
    
    try:
        async with IntegrationTester() as tester:
            await tester.run_all_tests()
            
    except KeyboardInterrupt:
        print("\n\n⏹️  Tests interrupted by user")
    except Exception as e:
        print(f"\n\n❌ Test suite failed with error: {e}")
        print("💡 Make sure the FastAPI backend is running and accessible")

if __name__ == "__main__":
    asyncio.run(main())
```

```shellscript
   rm test_integration.py
```

```shellscript
   # Start your services first
   make docker-up
   # Or start them manually
   
   # Then run the comprehensive integration tests
   make test-integration
```

