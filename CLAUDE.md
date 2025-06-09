# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Monorepo Structure

This is a monorepo containing a full-stack AI text processing application:
- **Backend** (`backend/`): FastAPI REST API with AI text processing capabilities
- **Frontend** (`frontend/`): Streamlit web application for user interaction
- **Shared** (`shared/`): Common Pydantic models used by both frontend and backend

The backend provides AI-powered text processing services, while the frontend offers an intuitive web interface. Both components share data models for consistency.

## Development Commands

### Backend (FastAPI)
```bash
cd backend/

# Local development with hot reload
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend (Streamlit)
```bash
cd frontend/

# Run Streamlit app
streamlit run app.py --server.port 8501
```

### Frontend Testing
```bash
cd frontend/

# Run frontend tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html
```

### Testing (Backend)
```bash
cd backend/

# Default: Run fast tests in parallel (excludes slow and manual tests)
pytest -v

# Run all unit tests only (no external dependencies)
pytest unit/ -v

# Run all integration tests only (mocked external dependencies)
pytest integration/ -v

# Run all tests including slow ones (excluding manual)
pytest -v -m "not manual" --run-slow

# Run only slow tests (requires --run-slow flag)
pytest -v -m "slow" --run-slow

# Run manual tests (requires running server and --run-manual flag)
pytest -v -m "manual" --run-manual

# Run with coverage
pytest --cov=app --cov-report=html --cov-report=term -v

# Run specific test categories
pytest unit/services/ -v                    # Service layer unit tests
pytest unit/security/ -v                    # Security unit tests
pytest integration/test_main_endpoints.py -v # Main endpoint integration tests

# Run tests sequentially (for debugging)
pytest -v -n 0

# Run specific test markers
pytest -v -m "retry" --run-slow             # Retry logic tests
pytest -v -m "circuit_breaker" --run-slow   # Circuit breaker tests
pytest -v -m "no_parallel"                  # Tests that must run sequentially
```

### Code Quality (Backend)
```bash
cd backend/

# Linting and formatting (from requirements-dev.txt)
flake8 app/ tests/
black app/ tests/
isort app/ tests/
mypy app/
```

### Code Quality (Frontend)
```bash
cd frontend/

# Linting and formatting
flake8 app/ tests/
black app/ tests/
isort app/ tests/
```

### Makefile Commands
The project includes a comprehensive Makefile for common tasks:
```bash
# Setup and testing
make install              # Install all dependencies (creates venv automatically)
make test                # Run all tests (with Docker if available)
make test-local          # Run tests without Docker dependency
make test-backend        # Run backend tests only (fast tests by default)
make test-backend-slow   # Run slow backend tests only
make test-backend-all    # Run all backend tests (including slow ones)
make test-backend-manual # Run backend manual tests (requires running server)
make test-frontend       # Run frontend tests only
make test-integration    # Run comprehensive integration tests
make test-coverage       # Run tests with coverage report
make test-coverage-all   # Run tests with coverage (including slow tests)
make test-retry          # Run retry-specific tests only
make test-circuit        # Run circuit breaker tests only
make ci-test            # Run CI tests (fast tests only)
make ci-test-all        # Run comprehensive CI tests (including slow tests)
make lint               # Run code quality checks for both backend and frontend
make lint-backend       # Run backend code quality checks only
make lint-frontend      # Run frontend code quality checks only
make format             # Format code with black and isort

# Docker commands
make docker-build    # Build Docker images
make docker-up       # Start services with Docker Compose
make docker-down     # Stop Docker services
make dev            # Start development environment
make prod           # Start production environment
make logs           # Show Docker Compose logs
make status         # Show status of all services
make health         # Check health of all services

# Utilities
make redis-cli      # Access Redis CLI
make backup         # Backup Redis data
make restore        # Restore Redis data (Usage: make restore BACKUP=filename)
make clean          # Clean up generated files
make clean-all      # Clean up including virtual environment
make repomix        # Generate full repository documentation
make repomix-backend # Generate backend-only documentation
make repomix-frontend # Generate frontend-only documentation
make repomix-docs   # Generate documentation for README and docs/
```

### Shared Module
The `shared/` directory contains common Pydantic models used by both frontend and backend:
```bash
cd shared/

# Install shared module in development mode
pip install -e .

# This allows imports like: from shared.models import ProcessingRequest
```

## Architecture Overview

This monorepo implements a full-stack AI text processing application with clear separation between frontend and backend. The FastAPI backend provides AI-powered text processing services, while the Streamlit frontend offers an intuitive web interface.

### Backend Architecture
The FastAPI backend includes the following key architectural components:

### Core Architecture
- **FastAPI Application** (`app/main.py`): Main HTTP server with CORS, authentication, and global exception handling
- **Dependency Injection** (`app/dependencies.py`): Service providers for settings, cache, and text processor
- **Service Layer**: Business logic separated into focused services
- **Shared Models** (`../shared/models.py`): Cross-service Pydantic data models

### Key Services
- **TextProcessorService** (`app/services/text_processor.py`): AI text processing using PydanticAI agents with Gemini models
- **AIResponseCache** (`app/services/cache.py`): Redis-backed caching with graceful degradation
- **Resilience Service** (`app/services/resilience.py`): Circuit breaker, retry logic, and error handling patterns
- **Authentication** (`app/auth.py`): API key-based authentication with multiple key support

### Resilience Patterns
The application implements comprehensive resilience patterns:
- **Circuit Breakers**: Prevent cascade failures during AI service outages
- **Retry Strategies**: Configurable retry with exponential backoff and jitter
- **Operation-Specific Policies**: Different resilience strategies per operation type (conservative, balanced, aggressive)
- **Graceful Degradation**: Cache operates without Redis if connection fails

### Processing Operations
- `summarize`: Text summarization with configurable length
- `sentiment`: Sentiment analysis with confidence scores
- `key_points`: Key point extraction with configurable count
- `questions`: Question generation from text
- `qa`: Question answering requiring question parameter

### Configuration
Settings are managed through `app/config.py` with Pydantic validation:
- AI model configuration (Gemini API)
- Resilience strategy settings
- Batch processing limits
- Redis connection settings
- CORS and authentication settings

### Error Handling
- Global exception handler in main.py
- Service-specific error handling with proper HTTP status codes
- Structured logging with request tracing
- AI response validation and sanitization

### Testing Structure
- **Unit tests** (`unit/` directory): No external dependencies, mocked AI services (fast, run by default)
- **Integration tests** (`integration/` directory): Test components working together with mocked external services
- **Manual tests** (root directory): Require running server and real API keys (marked as `manual`)
- **Slow tests** for comprehensive resilience testing (marked as `slow`, require `--run-slow` flag)
- **Parallel execution** by default using pytest-xdist for faster feedback
- **Test markers**: `slow`, `manual`, `integration`, `retry`, `circuit_breaker`, `no_parallel`
- **Special flags**: `--run-slow` enables slow tests, `--run-manual` enables manual tests
- Coverage reporting available with HTML and terminal output

### Test Configuration
Backend tests use parallel execution by default (`-n auto --dist worksteal`):
- Tests run in parallel for faster feedback cycles
- Use `monkeypatch.setenv()` for environment isolation in fixtures
- **Unit tests**: Test individual components in isolation with no external dependencies
- **Integration tests**: Test component interactions with mocked external services
- **Manual tests**: Require running FastAPI server at `http://localhost:8000` and real API keys
- **Slow tests**: Include comprehensive resilience testing, timing tests, and performance scenarios
- **Special flags**: Tests marked `slow` or `manual` are excluded by default and require explicit flags

### Manual Test Requirements
Manual tests (`-m "manual"`) require:
- FastAPI server running on `http://localhost:8000`
- `API_KEY=test-api-key-12345` environment variable for authentication tests
- `GEMINI_API_KEY` environment variable for AI features and live API testing
- Use `--run-manual` flag to enable manual tests: `pytest -v -m "manual" --run-manual`

**Setup for manual tests:**
```bash
# 1. Set environment variables
export GEMINI_API_KEY="your-actual-gemini-api-key"
export API_KEY="test-api-key-12345"

# 2. Start server
uvicorn app.main:app --reload --port 8000

# 3. Run manual tests (in another terminal)
pytest test_manual_api.py test_manual_auth.py -v -s -m "manual" --run-manual
```

## Important Notes

- The application uses PydanticAI agents for AI model interactions
- All AI operations are async with resilience patterns
- Cache gracefully degrades when Redis is unavailable
- Authentication supports primary + additional API keys
- Batch processing has configurable concurrency limits
- CORS is configured for Streamlit frontend integration
- Monorepo structure allows shared data models between frontend and backend
- Frontend communicates with backend via REST API endpoints

# Important Development Guidelines

- Do what has been asked; nothing more, nothing less
- NEVER create files unless they're absolutely necessary for achieving your goal
- ALWAYS prefer editing an existing file to creating a new one
- NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User
