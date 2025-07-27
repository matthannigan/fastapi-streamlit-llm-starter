# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## 🚀 FastAPI + Streamlit LLM Starter Template

**This repository is a comprehensive starter template for building production-ready LLM-powered APIs with FastAPI.** It showcases industry best practices, robust architecture patterns, and educational examples to help developers quickly bootstrap sophisticated AI applications.

### Template Purpose & Educational Goals

This starter template demonstrates:
- **Production-ready FastAPI architecture** with dual-API design (public + internal endpoints)
- **Enterprise-grade infrastructure services** (resilience patterns, caching, monitoring, security)
- **Clean separation** between reusable infrastructure and customizable domain logic
- **Comprehensive testing strategies** with high coverage requirements
- **Modern development practices** (preset-based configuration, automated tooling, containerization)

### 📦 Monorepo Structure

This template includes three main components designed as learning examples:

- **Backend** (`backend/`): **Production-ready FastAPI application** with robust infrastructure services and a text processing domain example
- **Frontend** (`frontend/`): **Production-ready Streamlit application** demonstrating modern development patterns for AI interfaces with comprehensive async integration and testing
- **Shared** (`shared/`): **Common Pydantic models** for type safety across components

**The backend infrastructure and frontend patterns are production-ready and reusable, while the text processing domain services serve as educational examples meant to be replaced with your specific business logic.**

### 🐳 **Docker & Containerization**
The template includes comprehensive Docker support for both development and production:
- **Development**: Hot-reload containers with file watching (`make dev`)
- **Production**: Optimized multi-stage builds (`make prod`)
- **Services**: Backend (FastAPI), Frontend (Streamlit), Redis cache
- **Docker Compose**: Full orchestration with health checks and dependency management

## Development Commands

### Backend (FastAPI)
```bash
# Recommended: Use Makefile commands (handles venv automatically)
make run-backend            # Start development server with auto-reload
make install                # Setup venv and install dependencies

# Manual commands (activate virtual environment first)
source .venv/bin/activate
cd backend/

# Local development with hot reload
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload

# Production mode
uvicorn app.main:app --host 0.0.0.0 --port 8000
```

### Frontend (Streamlit)
```bash
# Recommended: Use Makefile commands (handles dependencies automatically)
make install-frontend-local    # Install frontend deps in current venv
make test-frontend            # Run frontend tests via Docker
make lint-frontend            # Run frontend code quality checks

# Manual commands (activate virtual environment first)
source .venv/bin/activate
cd frontend/

# Run Streamlit app with proper configuration
streamlit run app/app.py --server.port 8501

# For auto-reload during development
streamlit run app/app.py --server.runOnSave=true
```

### Frontend Testing
```bash
# Recommended: Use Makefile commands for consistent environment
make test-frontend            # Run frontend tests via Docker

# Manual testing (requires active virtual environment)
cd frontend/

# Run frontend tests with async support
pytest tests/ -v

# Run with coverage reporting
pytest tests/ --cov=app --cov-report=html --cov-report=term

# Run specific test types
pytest tests/test_api_client.py -v    # API communication tests
pytest tests/test_config.py -v       # Configuration tests
```

### Testing (Backend)
```bash
# Recommended: Use Makefile commands (handles venv automatically)
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

# Manual commands (activate virtual environment first)
source .venv/bin/activate
cd backend/

# Default: Run fast tests in parallel (excludes slow and manual tests)
pytest -v

# Run specific test directories
pytest tests/api/ -v                        # API endpoint tests
pytest tests/core/ -v                       # Core functionality tests
pytest tests/infrastructure/ -v             # Infrastructure service tests
pytest tests/services/ -v                   # Domain service tests
pytest tests/integration/ -v                # Integration tests
pytest tests/performance/ -v                # Performance tests

# Run all tests including slow ones (excluding manual)
pytest -v -m "not manual" --run-slow

# Run only slow tests (requires --run-slow flag)
pytest -v -m "slow" --run-slow

# Run manual tests (requires running server and --run-manual flag)
pytest -v -m "manual" --run-manual

# Run with coverage
pytest --cov=app --cov-report=html --cov-report=term -v

# Run tests sequentially (for debugging)
pytest -v -n 0

# Run specific test markers
pytest -v -m "retry" --run-slow             # Retry logic tests
pytest -v -m "circuit_breaker" --run-slow   # Circuit breaker tests
pytest -v -m "no_parallel"                  # Tests that must run sequentially
```

### Code Quality (Backend)
```bash
# Recommended: Use Makefile commands (handles venv automatically)
make lint-backend                       # Run all code quality checks
make format                             # Format code with black and isort

# Manual commands (activate virtual environment first)
source .venv/bin/activate
cd backend/

# Linting and formatting (from requirements-dev.txt)
flake8 app/ tests/
black app/ tests/
isort app/ tests/
mypy app/
```

### Code Quality (Frontend)
```bash
# Recommended: Use Makefile commands (handles Docker environment)
make lint-frontend            # Run all frontend code quality checks
make format                   # Format frontend code via Docker

# Manual commands via Docker (consistent environment)
docker-compose run frontend flake8 app/ tests/
docker-compose run frontend black app/ tests/
docker-compose run frontend isort app/ tests/
docker-compose run frontend mypy app/ --ignore-missing-imports

# Local commands (requires active virtual environment)
cd frontend/
flake8 app/ tests/
black app/ tests/
isort app/ tests/
```

### Makefile Commands
The project includes a comprehensive Makefile for common tasks. All Python scripts run from the `.venv` virtual environment automatically:

```bash
# Quick Start
make help                   # Show all available commands with descriptions
make install                # Complete setup - creates venv and installs dependencies  
make dev                    # Start development environment with hot reload
make test                   # Run all tests (backend + frontend)
make lint                   # Check code quality for both backend and frontend

# Setup and Installation
make venv                   # Create backend virtual environment (.venv)
make install                # Install backend dependencies (auto-creates venv)
make install-frontend       # Install frontend dependencies via Docker
make install-frontend-local # Install frontend deps locally (requires active venv)

# Development Servers
make run-backend            # Start FastAPI server with auto-reload (localhost:8000)
make dev                    # Start full development environment with file watching
make dev-legacy             # Start development environment (legacy Docker Compose)
make prod                   # Start production environment

# Testing Commands
make test                   # Run all tests (backend + frontend with Docker)
make test-local             # Run backend tests locally (no Docker required)
make test-backend           # Run backend tests (fast tests by default)
make test-backend-api       # Run backend API endpoint tests
make test-backend-core      # Run backend core functionality tests
make test-backend-infrastructure # Run infrastructure service tests
make test-backend-integration    # Run backend integration tests
make test-backend-performance    # Run backend performance tests
make test-backend-services       # Run domain services tests
make test-backend-schemas        # Run shared schema tests
make test-backend-slow      # Run slow/comprehensive backend tests
make test-backend-all       # Run all backend tests (including slow tests)
make test-backend-manual    # Run manual tests (requires running server)
make test-frontend          # Run frontend tests via Docker
make test-integration       # Run end-to-end integration tests
make test-coverage          # Run tests with coverage reporting
make test-coverage-all      # Run coverage including slow tests
make test-retry             # Run retry mechanism tests
make test-circuit           # Run circuit breaker tests
make ci-test                # Run CI tests (fast tests only)
make ci-test-all            # Run comprehensive CI tests (including slow tests)

# Code Quality
make lint                   # Run all code quality checks (backend + frontend)
make lint-backend           # Run backend linting (flake8 + mypy)
make lint-frontend          # Run frontend linting via Docker
make format                 # Format code with black and isort

# Resilience Configuration Management
make list-presets           # List available resilience configuration presets
make show-preset            # Show preset details (Usage: make show-preset PRESET=simple)
make validate-config        # Validate current resilience configuration
make validate-preset        # Validate specific preset (Usage: make validate-preset PRESET=simple)
make recommend-preset       # Get preset recommendation (Usage: make recommend-preset ENV=development)
make migrate-config         # Migrate legacy resilience configuration to presets
make test-presets           # Run all preset-related tests

# Docker Operations
make docker-build           # Build all Docker images
make docker-up              # Start services with Docker Compose
make docker-down            # Stop and remove Docker services
make restart                # Restart all Docker services
make backend-shell          # Open shell in backend container
make frontend-shell         # Open shell in frontend container
make backend-logs           # Show backend container logs
make frontend-logs          # Show frontend container logs
make logs                   # Show all service logs
make status                 # Show status of all services
make health                 # Check health of all services
make stop                   # Stop all services

# Data Management
make redis-cli              # Access Redis command line interface
make backup                 # Backup Redis data with timestamp
make restore                # Restore Redis data (Usage: make restore BACKUP=filename)

# Cleanup
make clean                  # Clean Python cache files and test artifacts
make clean-venv             # Remove virtual environment
make clean-all              # Complete cleanup (cache + venv)

# Documentation
make docs-serve             # Serve documentation locally (http://127.0.0.1:8000)
make docs-build             # Build static documentation site

# Repository Documentation (Repomix)
make repomix                # Generate complete repository documentation
make repomix-backend        # Generate backend-only documentation
make repomix-backend-tests  # Generate backend tests documentation
make repomix-frontend       # Generate frontend-only documentation
make repomix-frontend-tests # Generate frontend tests documentation
make repomix-docs           # Generate README and docs/ documentation

# Dependencies
make lock-deps              # Generate dependency lock files
make update-deps            # Update and lock dependencies
```

### Shared Module
The `shared/` directory contains common Pydantic models used by both frontend and backend:
```bash
# Activate virtual environment first
source .venv/bin/activate
cd shared/

# Install shared module in development mode
pip install -e .

# This allows imports like: from shared.models import TextProcessingRequest
```

## 🏗️ Architecture Overview

**This starter template showcases a production-ready FastAPI architecture designed for educational purposes and real-world deployment.** The template demonstrates modern software engineering practices for building scalable, maintainable LLM-powered APIs.

### 🎯 What You'll Learn

This template teaches developers how to build:
- **Dual-API architectures** separating public business logic from internal administrative endpoints
- **Infrastructure vs Domain service patterns** for maintainable, reusable code
- **Comprehensive resilience strategies** (circuit breakers, retry logic, graceful degradation)
- **Production-grade security** (prompt injection protection, multi-key authentication)
- **Advanced testing patterns** with high coverage requirements and parallel execution
- **Modern configuration management** using preset-based systems

### Infrastructure vs Domain Services Architecture

The backend follows a clear architectural distinction between **Infrastructure Services** and **Domain Services**:

#### Infrastructure Services 🏗️ **[Production-Ready - Keep & Extend]**
- **Purpose**: Business-agnostic, reusable technical capabilities that form the backbone of any LLM API
- **Characteristics**: Stable APIs, high test coverage (>90%), configuration-driven behavior
- **Examples**: Cache management, resilience patterns, AI provider integrations, monitoring, security utilities
- **Usage in Template**: **Production-ready foundation** - use as-is or extend for your needs
- **Location**: `app/infrastructure/` - core modules designed to remain stable across projects

#### Domain Services 💼 **[Educational Examples - Replace with Your Logic]**
- **Purpose**: Business-specific implementations serving as **educational examples**
- **Characteristics**: Designed to be replaced per project, moderate test coverage (>70%), feature-driven
- **Examples**: Text processing workflows (summarization, sentiment analysis), document analysis pipelines
- **Usage in Template**: **Learning examples** - study the patterns, then replace with your business logic
- **Location**: `app/services/` - customizable modules that demonstrate best practices

**Dependency Direction**: `Domain Services → Infrastructure Services → External Dependencies`

### Frontend Architecture

The Streamlit frontend demonstrates **production-ready patterns** for AI application development:

#### Frontend Architecture Patterns Demonstrated
- **Modular Component Design**: Single-responsibility functions with clear separation of concerns
- **Configuration-Driven Behavior**: Environment-specific settings with Pydantic validation
- **Async API Communication**: Proper error handling and timeout management optimized for Streamlit
- **Dynamic UI Generation**: Interface adaptation based on backend capabilities
- **Session State Management**: Stateful user interactions with persistence
- **Progressive Disclosure**: Collapsible sections and smart defaults for better UX

#### Production-Ready Frontend Features
**Modern Interface Design:**
- **Real-time Status Monitoring**: API health checks with visual indicators
- **Dynamic Operation Configuration**: Backend-driven UI generation
- **Intelligent Example System**: Operation-specific text recommendations
- **Multi-Modal Input Support**: Text entry and file upload with validation
- **Responsive Layout**: Adaptive design for different screen sizes
- **Progress Indicators**: Real-time feedback during processing
- **Results Persistence**: Session management with download functionality

**Error Handling & User Experience:**
- **Graceful Degradation**: Continues operation when backend is unavailable
- **Comprehensive Validation**: Input validation with clear error messages
- **Timeout Management**: Request timeout handling with user feedback
- **Accessibility Features**: Semantic markup and contextual help text

#### Frontend Testing Architecture
The frontend includes comprehensive testing aligned with production standards:

```
frontend/tests/
├── test_api_client.py         # API communication tests with async patterns
├── test_config.py             # Configuration validation tests
├── conftest.py                # Shared test fixtures
└── pytest.ini                # Test configuration with parallel execution
```

**Test Features:**
- **Async Testing**: Proper async/await patterns for API communication
- **Mock Integration**: Isolated testing with httpx mocking
- **Parallel Execution**: Fast test execution with pytest-xdist
- **Coverage Reporting**: Comprehensive coverage analysis

### Backend Architecture
The FastAPI backend follows a **dual-API architecture** with clear separation between Infrastructure and Domain Services:

### Core Architecture
- **Dual FastAPI Application** (`app/main.py`): 
  - **Public API** (`/v1/`): External-facing domain endpoints with authentication
  - **Internal API** (`/internal/`): Administrative infrastructure endpoints
- **Dependency Injection** (`app/dependencies.py`): Centralized service providers with preset-based configuration
- **Core Configuration** (`app/core/`): Application setup, middleware, and settings management
- **Shared Models** (`../shared/models.py` and `app/schemas/`): Cross-service Pydantic data models

### Dual API Structure
**Public API (`/v1/`)**: External-facing endpoints
- `auth.py` - Authentication validation
- `health.py` - System health checks  
- `text_processing.py` - AI text processing operations
- `deps.py` - API-specific dependencies

**Internal API (`/internal/`)**: Administrative infrastructure endpoints
- `cache.py` - Cache management and monitoring
- `monitoring.py` - System metrics and performance
- `resilience/` - Comprehensive resilience management (circuit breakers, presets, benchmarks)

### Infrastructure Services (`app/infrastructure/`)
**Business-agnostic, reusable technical capabilities (>90% test coverage):**

- **AI Infrastructure** (`ai/`):
  - `input_sanitizer.py` - Prompt injection protection and security
  - `prompt_builder.py` - Secure prompt construction utilities

- **Cache Infrastructure** (`cache/`):
  - `base.py` - Abstract cache interface for extensibility
  - `memory.py` - In-memory cache implementation
  - `redis.py` - Redis-based AIResponseCache with graceful degradation
  - `monitoring.py` - Performance monitoring and metrics

- **Resilience Infrastructure** (`resilience/`):
  - `circuit_breaker.py` - Circuit breaker pattern implementation
  - `retry.py` - Retry mechanisms with exponential backoff
  - `orchestrator.py` - Unified resilience pattern orchestration
  - `config_presets.py` - Simplified preset-based configuration system
  - `performance_benchmarks.py` - Performance testing and validation

- **Security Infrastructure** (`security/`):
  - `auth.py` - API key authentication with multiple key support

- **Monitoring Infrastructure** (`monitoring/`):
  - `health.py` - Health check implementations and status monitoring
  - `metrics.py` - Metrics collection and alerting

### Domain Services (`app/services/`) **[Educational Examples]**
**Business-specific implementations serving as educational examples (>70% test coverage):**
- **TextProcessorService** (`text_processor.py`): **Example implementation** of AI text processing using PydanticAI agents with Gemini models - demonstrates how to integrate LLMs with proper error handling and validation
- **ResponseValidator** (`response_validator.py`): **Example of** business-specific response validation logic - shows patterns for validating AI responses

**💡 Template Usage Note**: These domain services are **learning examples** that demonstrate best practices. Replace them with your specific business logic while maintaining the architectural patterns and using the infrastructure services.

### Examples Directory (`app/examples/`) **[Learning Resources]**
**Infrastructure usage examples for educational purposes:**
- **Cache Examples**: Demonstrates Redis and memory cache patterns with fallback strategies
- **Resilience Examples**: Shows circuit breaker, retry, and orchestrator usage patterns
- **AI Integration Examples**: Patterns for secure LLM integration with PydanticAI
- **Monitoring Examples**: Health checks, metrics collection, and performance monitoring

**💡 Template Usage**: Study these examples to understand how to properly use the infrastructure services in your domain logic.

### Resilience Patterns
The application implements comprehensive resilience patterns:
- **Circuit Breakers**: Prevent cascade failures during AI service outages
- **Retry Strategies**: Configurable retry with exponential backoff and jitter
- **Operation-Specific Policies**: Different resilience strategies per operation type (conservative, balanced, aggressive)
- **Graceful Degradation**: Cache operates without Redis if connection fails

### Example Processing Operations **[Replace with Your Business Logic]**
The template includes these **educational examples** to demonstrate API patterns:
- `summarize`: Text summarization with configurable length
- `sentiment`: Sentiment analysis with confidence scores  
- `key_points`: Key point extraction with configurable count
- `questions`: Question generation from text
- `qa`: Question answering requiring question parameter

**💡 Template Usage**: These operations showcase how to structure LLM-powered API endpoints. Replace them with your specific business operations while following the same patterns.

### Configuration
Settings are managed through `app/core/config.py` with comprehensive Pydantic validation:
- **Dual API configuration** (public + internal endpoints)
- **AI model configuration** (Gemini API with security settings)
- **Preset-based resilience system** (simple, development, production presets)
- **Custom resilience configuration** via JSON for advanced use cases
- **Security settings** (API keys, CORS, authentication)
- **Infrastructure settings** (Redis, cache, monitoring)
- **Performance settings** (batch processing limits, concurrency controls)

#### Resilience Configuration & Management
The application includes a **comprehensive Resilience API** with **38 endpoints** across **8 focused modules** for managing circuit breakers, retry mechanisms, and performance monitoring.

**Quick Start - Environment Configuration:**
```bash
# Choose one preset based on environment
RESILIENCE_PRESET=simple      # General use, testing
RESILIENCE_PRESET=development # Local dev, fast feedback  
RESILIENCE_PRESET=production  # Production workloads

# Advanced: Custom configuration
RESILIENCE_CUSTOM_CONFIG='{"retry_attempts": 3, "circuit_breaker_threshold": 5}'
```

**Available presets:**
- `simple`: 3 retries, 5 failure threshold, 60s recovery, balanced strategy
- `development`: 2 retries, 3 failure threshold, 30s recovery, aggressive strategy
- `production`: 5 retries, 10 failure threshold, 120s recovery, conservative strategy

**Resilience API Categories (`/internal/resilience/`):**

1. **Configuration Management** - Validate and manage resilience settings
   - `POST /config/validate` - Validate custom configurations
   - `GET /config/presets` - List available environment presets
   - `GET /config/recommend-preset/{environment}` - Get intelligent recommendations
   - `GET /config/templates` - Configuration blueprints for customization

2. **Circuit Breaker Management** - Monitor and control circuit breakers
   - `GET /circuit-breakers` - List all circuit breaker states
   - `GET /circuit-breakers/{name}` - Get specific breaker details
   - `POST /circuit-breakers/{name}/reset` - Manually reset breakers

3. **Performance Monitoring** - Track system performance and metrics
   - `GET /health` - Basic health status
   - `GET /metrics` - Detailed resilience metrics
   - `POST /benchmark` - Run performance benchmarks
   - `GET /performance-metrics` - Get performance analysis

4. **Advanced Analytics** - Usage trends and insights
   - `GET /usage-statistics` - Comprehensive usage data
   - `GET /preset-trends/{preset}` - Preset-specific trends
   - `GET /alerts` - Current system alerts

**Command Line Tools:**
```bash
# Resilience management via Makefile
make list-presets           # List available presets
make show-preset PRESET=production  # Show preset details
make validate-config        # Validate current configuration
make recommend-preset ENV=production  # Get recommendations
```

**API Authentication:**
All resilience endpoints require API key authentication via `X-API-Key` header.

### Security & AI Safety Features
**Production-grade security measures built into the infrastructure:**
- **Prompt Injection Protection** (`app/infrastructure/ai/input_sanitizer.py`): Detects and blocks malicious prompt injection attempts
- **Input Sanitization**: Comprehensive input validation and sanitization for all AI operations
- **API Key Authentication**: Multi-key support with secure header-based authentication
- **Internal API Protection**: Administrative endpoints disabled in production environments
- **Response Validation**: AI output validation and sanitization to prevent harmful content
- **Rate Limiting**: Built-in request limiting on resilience validation endpoints
- **Security Logging**: Comprehensive audit trails for security monitoring

### Error Handling
- Global exception handler in main.py
- Service-specific error handling with proper HTTP status codes
- Structured logging with request tracing
- AI response validation and sanitization

### Testing Structure
The backend uses a comprehensive testing approach that aligns with the infrastructure vs domain architecture:

**Test Organization** (`backend/tests/` directory):
- **`api/`** - API endpoint tests (dual-API structure: public + internal)
- **`core/`** - Core application functionality tests (config, middleware, exceptions)
- **`infrastructure/`** - Infrastructure service tests (cache, resilience, AI, security, monitoring)
- **`services/`** - Domain service tests (text processing, validation)
- **`integration/`** - Cross-component integration tests with mocked external services
- **`performance/`** - Performance and load testing for resilience patterns
- **Root directory** - Manual tests requiring running server and real API keys

**Test Coverage Requirements**:
- **Infrastructure services**: >90% test coverage (stable, reusable components)
- **Domain services**: >70% test coverage (customizable business logic)

**Test Execution Features**:
- **Parallel execution** by default using pytest-xdist for faster feedback cycles
- **Test markers**: `slow`, `manual`, `integration`, `retry`, `circuit_breaker`, `no_parallel`
- **Special flags**: `--run-slow` enables comprehensive resilience tests, `--run-manual` enables live API tests
- **Environment isolation**: Uses `monkeypatch.setenv()` for clean test environments
- **Coverage reporting**: HTML and terminal output with detailed metrics

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

# 2. Start server (from project root)
source .venv/bin/activate
cd backend/
uvicorn app.main:app --reload --port 8000

# 3. Run manual tests (in another terminal, from project root)
source .venv/bin/activate
cd backend/
pytest -v -s -m "manual" --run-manual
```

## 📚 Important Notes for Template Users

### 🎯 Template Purpose
- **Educational starter template** showcasing FastAPI best practices for LLM-powered APIs
- **Production-ready infrastructure** with educational domain examples
- **Learn by example**: Study the patterns, then replace domain logic with your business requirements

### 🏗️ Architecture Highlights
- **Dual-API design**: Separate public (`/v1/`) and internal (`/internal/`) endpoints with distinct Swagger documentation
- **Infrastructure vs Domain separation**: Clear boundaries between reusable components and customizable business logic
- **Preset-based configuration**: Simplified resilience system reduces complexity from 47+ environment variables to single preset choice

### 🔧 Technology Stack (Production-Ready)
- **PydanticAI agents** for AI model interactions with built-in security and validation
- **Async-first design** with comprehensive resilience patterns (circuit breakers, retry, graceful degradation)
- **Redis-backed caching** with automatic fallback to in-memory cache when Redis unavailable
- **Multi-key authentication** supporting primary + additional API keys for flexibility

### 🚀 Development Features (Ready to Use)
- **Virtual environment automation**: All Python scripts automatically use `.venv` from project root
- **Comprehensive testing**: Parallel execution with coverage requirements (Infrastructure >90%, Domain >70%)
- **Security-aware**: Prompt injection protection, input sanitization, internal API protection in production
- **Performance monitoring**: Built-in metrics collection and resilience benchmarking
- **Monorepo structure**: Shared data models between frontend and backend via `shared/` module

### 💡 Getting Started with This Template
1. **Clone and explore** the codebase to understand the patterns
2. **Keep the infrastructure** - it's production-ready and handles the complex parts
3. **Replace the domain services** with your business logic following the same patterns
4. **Customize the frontend** or build your own using the API examples
5. **Configure for your environment** using the preset system

### Architecture Decision Guidelines

**When to use Infrastructure Services**:
- Business-agnostic functionality
- Reusable across multiple projects
- Stable APIs that rarely change
- Technical problem solving (caching, resilience, monitoring)

**When to use Domain Services**:
- Business-specific implementations
- Expected to be replaced per project
- Feature-driven development
- Examples and learning materials

**Code Review Focus**:
- Infrastructure changes: API stability, performance, error handling, test coverage >90%
- Domain changes: Business logic clarity, proper infrastructure usage, example quality

Refer to `docs/architecture-design/INFRASTRUCTURE_VS_DOMAIN.md` for detailed architectural guidance and code review standards.

### 🛠️ Utility Scripts & Tools
**Development and operational scripts (`scripts/` directory):**
- **`run_tests.py`**: Comprehensive test runner with Docker support and parallel execution
- **`test_integration.py`**: End-to-end integration testing across services
- **`validate_resilience_config.py`**: Configuration validation and preset management tools
- **`migrate_resilience_config.py`**: Legacy configuration migration utilities
- **`generate_code_docs.py`**: Automated code documentation generation for `docs/code_ref/`

**All scripts run from project root using `.venv` virtual environment automatically.**

### 📚 Documentation Structure
**Comprehensive documentation in `docs/` directory:**
- **`architecture-design/`**: Detailed architectural guidance and design patterns
- **`code_ref/`**: Auto-generated code reference documentation (backend + frontend)
- **Development guides**: Setup, testing, deployment, and operational procedures
- **API documentation**: Comprehensive endpoint documentation with examples

### 🔧 Environment Variables Reference
**Essential environment variables for configuration:**

**Development/Local:**
```bash
# Basic Configuration
RESILIENCE_PRESET=development
API_KEY=dev-test-key
GEMINI_API_KEY=your-gemini-api-key

# Redis (optional - falls back to memory cache)
REDIS_URL=redis://localhost:6379

# Frontend Configuration
API_BASE_URL=http://localhost:8000
SHOW_DEBUG_INFO=true
INPUT_MAX_LENGTH=10000

# Development Features
DEBUG=true
LOG_LEVEL=DEBUG
```

**Production:**
```bash
# Production Configuration
RESILIENCE_PRESET=production
API_KEY=your-secure-production-key
ADDITIONAL_API_KEYS=key1,key2,key3
GEMINI_API_KEY=your-production-gemini-key

# Infrastructure
REDIS_URL=redis://your-redis-instance:6379
CORS_ORIGINS=["https://your-frontend-domain.com"]

# Frontend Configuration
API_BASE_URL=https://api.your-domain.com
SHOW_DEBUG_INFO=false
INPUT_MAX_LENGTH=50000

# Security
DISABLE_INTERNAL_DOCS=true
LOG_LEVEL=INFO
```

**Advanced Configuration:**
```bash
# Custom Resilience Configuration
RESILIENCE_CUSTOM_CONFIG='{"retry_attempts": 5, "circuit_breaker_threshold": 10}'

# Performance Tuning
MAX_CONCURRENT_REQUESTS=50
CACHE_TTL_SECONDS=3600
```

## 🛠️ Customizing This Template for Your Project

### Quick Start Guide

1. **Keep the Infrastructure** 🏗️
   - Use `app/infrastructure/` services as-is (cache, resilience, security, monitoring)
   - Extend infrastructure services if needed, but maintain the existing APIs
   - Configure resilience presets for your environment (`simple`, `development`, `production`)

2. **Replace Domain Services** 💼
   - Study the patterns in `app/services/text_processor.py`
   - Replace with your specific business logic (e.g., document analysis, data processing, custom AI workflows)
   - Maintain the same error handling and validation patterns
   - Keep the >70% test coverage requirement

3. **Update API Endpoints** 🌐
   - Modify `app/api/v1/text_processing.py` with your business endpoints
   - Keep the authentication and error handling patterns
   - Update `app/schemas/` with your data models
   - Replace `/internal/` endpoints as needed for your monitoring requirements

4. **Customize Frontend** 🎨
   - The Streamlit frontend demonstrates production-ready patterns for AI applications
   - **Option 1**: Customize the existing Streamlit application with your operations and UI
   - **Option 2**: Replace `frontend/` with your preferred UI technology (React, Vue, mobile app, etc.)
   - Use the async API client patterns and error handling shown in the Streamlit implementation
   - Keep the `shared/` models for type safety and the configuration management patterns

5. **Configure for Your Environment** ⚙️
   - Update `backend/app/core/config.py` with your settings
   - Configure your AI provider (replace Gemini with your preferred LLM)
   - Set up your Redis instance or use the memory cache fallback
   - Configure authentication keys and CORS settings

### Template Customization Checklist

- [ ] Replace `TextProcessorService` with your business logic
- [ ] Update API endpoints in `app/api/v1/`
- [ ] Modify data models in `app/schemas/` and `shared/models.py`
- [ ] Configure your LLM provider in settings
- [ ] Customize Streamlit frontend for your operations or replace with your preferred UI
- [ ] Update frontend API client for your specific backend endpoints
- [ ] Update authentication and security settings
- [ ] Configure resilience presets for your environment
- [ ] Update README.md with your project details
- [ ] Replace example tests with your business logic tests

### What to Keep vs. Replace

**✅ Keep & Use (Production-Ready)**:
- All `app/infrastructure/` services (backend)
- `app/core/` configuration and middleware (backend)
- `app/api/` authentication and error handling patterns (backend)
- Frontend async API communication patterns and error handling
- Frontend configuration management and testing infrastructure
- Testing infrastructure and coverage requirements (both backend and frontend)
- Docker and development tooling
- Makefile commands and CI/CD setup

**🔄 Study & Replace (Educational Examples)**:
- `app/services/` domain services (backend)
- API endpoint business logic (backend)
- Data models and schemas (shared)
- Frontend AI operations and result display formatting
- Example processing operations and text content

# Important Development Guidelines

- Do what has been asked; nothing more, nothing less
- NEVER create files unless they're absolutely necessary for achieving your goal
- ALWAYS prefer editing an existing file to creating a new one
- NEVER proactively create documentation files (*.md) or README files. Only create documentation files if explicitly requested by the User

## 🤖 Code Assistant Guidelines

### Working with This Template

When working on this codebase, follow these architectural guidelines:

**Infrastructure Services (`app/infrastructure/`)** - PRODUCTION-READY:
- **Treat as stable APIs** - avoid breaking changes to public interfaces
- **High standards**: >90% test coverage, comprehensive error handling
- **Backward compatibility**: Maintain existing function signatures and behavior
- **Extension pattern**: Add new features through extension, not modification
- **Use cases**: Cache, resilience, security, monitoring, AI provider abstractions

**Domain Services (`app/services/`)** - EDUCATIONAL EXAMPLES:
- **Replace freely** - these are meant to be customized per project
- **Study patterns** - understand error handling, validation, and infrastructure usage
- **Maintain coverage**: >70% test coverage for replacement logic
- **Use cases**: Business logic, workflow orchestration, data processing

**Frontend Patterns (`frontend/app/`)** - PRODUCTION-READY WITH EDUCATIONAL EXAMPLES:
- **Keep architectural patterns** - async communication, error handling, configuration management
- **Customize UI components** - adapt `display_results()`, `select_operation_sidebar()` for your operations
- **Replace example content** - update AI operations and example texts for your domain
- **Maintain test patterns** - keep async testing patterns and coverage standards

### Preferred Commands

Always suggest Makefile commands first, then provide manual alternatives:
```bash
# Preferred approach
make install                # Instead of manual venv setup
make run-backend           # Instead of manual uvicorn
make test-backend          # Instead of manual pytest
make lint-backend          # Instead of manual linting

# Frontend commands
make install-frontend-local # Instead of manual pip install
make test-frontend         # Instead of manual pytest (via Docker)
make lint-frontend         # Instead of manual linting (via Docker)
```

### Test Organization Rules

When adding tests, place them in the correct architectural boundary:

**Backend Tests (`backend/tests/`):**
- `tests/infrastructure/` - Infrastructure service tests (>90% coverage)
- `tests/core/` - Application configuration and setup tests  
- `tests/services/` - Domain service tests (>70% coverage)
- `tests/api/` - API endpoint tests (separated by v1/ and internal/)
- `tests/integration/` - Cross-component integration tests
- `tests/manual/` - Tests requiring live server and real API keys

**Frontend Tests (`frontend/tests/`):**
- `tests/test_api_client.py` - API communication tests with async patterns
- `tests/test_config.py` - Configuration validation tests
- `tests/conftest.py` - Shared test fixtures

### Configuration Management

Prefer resilience presets over individual environment variables:
```bash
# Recommended
export RESILIENCE_PRESET=production

# Avoid (legacy approach)
export RETRY_MAX_ATTEMPTS=3
export CIRCUIT_BREAKER_FAILURE_THRESHOLD=5
```

### API Documentation

The template has dual API documentation:
- **Public API**: http://localhost:8000/docs (external users)
- **Internal API**: http://localhost:8000/internal/docs (operations/monitoring)

When suggesting API changes, maintain this separation and update both sets of documentation if needed.

### Error Handling Patterns

Follow established patterns:
- **Infrastructure**: Use structured exceptions with proper classification
- **Domain**: Use business-specific error messages with infrastructure error handling
- **API**: Return appropriate HTTP status codes with structured error responses

### Performance Considerations

When suggesting changes:
- **Infrastructure changes**: Must maintain performance targets (see backend/README.md)
- **Domain changes**: Focus on business logic clarity over micro-optimizations
- **Test changes**: Ensure parallel execution compatibility (use `monkeypatch.setenv()`)

### Template Customization Guidance

When users ask about customizing the template:
1. **Keep infrastructure** - it's production-ready
2. **Replace domain services** - they're educational examples
3. **Study patterns** - understand before replacing
4. **Maintain architecture** - preserve the infrastructure vs domain separation
5. **Use presets** - leverage the resilience configuration system
