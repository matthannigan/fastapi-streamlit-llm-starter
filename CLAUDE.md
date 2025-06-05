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

# Run all tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=app --cov-report=html

# Run specific test categories
pytest tests/test_main.py tests/test_text_processor.py -v  # Unit tests
pytest tests/test_manual_api.py tests/test_manual_auth.py -v  # Integration tests

# Run a single test file
pytest tests/test_resilience.py -v

# Run tests excluding slow ones
pytest -m "not slow"
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
make install          # Install all dependencies (creates venv automatically)
make test            # Run all tests (with Docker if available)
make test-local      # Run tests without Docker dependency
make test-backend    # Run backend tests only
make test-frontend   # Run frontend tests only
make test-coverage   # Run tests with coverage report
make lint            # Run code quality checks for both backend and frontend
make format          # Format code with black and isort

# Docker commands
make docker-build    # Build Docker images
make docker-up       # Start services with Docker Compose
make docker-down     # Stop Docker services
make dev            # Start development environment
make prod           # Start production environment

# Utilities
make clean          # Clean up generated files
make clean-all      # Clean up including virtual environment
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
- Unit tests with mocked AI services
- Integration tests requiring running server
- Manual test scripts for API validation
- Coverage reporting available

## Important Notes

- The application uses PydanticAI agents for AI model interactions
- All AI operations are async with resilience patterns
- Cache gracefully degrades when Redis is unavailable
- Authentication supports primary + additional API keys
- Batch processing has configurable concurrency limits
- CORS is configured for Streamlit frontend integration
- Monorepo structure allows shared data models between frontend and backend
- Frontend communicates with backend via REST API endpoints