# 🚀 FastAPI + Streamlit LLM Starter Template

**A comprehensive starter template for building production-ready LLM-powered APIs with FastAPI.** This template showcases industry best practices, robust architecture patterns, and educational examples to help developers quickly bootstrap sophisticated AI applications.

## 🎯 Template Purpose & Educational Goals

This starter template demonstrates:
- **Production-ready FastAPI architecture** with dual-API design (public + internal endpoints)
- **Enterprise-grade infrastructure services** (resilience patterns, caching, monitoring, security)
- **Clean separation** between reusable infrastructure and customizable domain logic
- **Comprehensive testing strategies** with high coverage requirements
- **Modern development practices** (preset-based configuration, automated tooling, containerization)

## 🌟 Key Features

### 🏗️ Production-Ready Architecture
- **Dual-API Design**: Separate public (`/v1/`) and internal (`/internal/`) endpoints with distinct documentation
- **Infrastructure vs Domain Separation**: Clear boundaries between reusable components and customizable business logic
- **Comprehensive Resilience Patterns**: Circuit breakers, retry logic, graceful degradation
- **Multi-tier Caching System**: Redis-backed with automatic fallback to in-memory cache

### 🤖 AI Integration Excellence
- **PydanticAI Agents**: Built-in security and validation for AI model interactions
- **Prompt Injection Protection**: Comprehensive security measures against malicious inputs
- **Multi-Provider Support**: Easy integration with Gemini, OpenAI, Anthropic, and other providers
- **Response Validation**: AI output sanitization and structured validation

### 🔧 Developer Experience
- **Virtual Environment Automation**: All Python scripts automatically use `.venv` from project root
- **Preset-Based Configuration**: Simplified resilience system reduces 47+ environment variables to single preset choice
- **Parallel Testing**: Fast feedback cycles with comprehensive coverage requirements
- **Hot Reload Development**: Docker Compose with file watching for both frontend and backend

### 🛡️ Production Security & Error Handling
- **Custom Exception Hierarchy**: Structured error handling with specific exception types and consistent JSON responses
- **Multi-Key Authentication**: Primary + additional API keys for flexibility
- **Internal API Protection**: Administrative endpoints disabled in production environments
- **Security Logging**: Comprehensive audit trails with structured error context
- **Rate Limiting**: Built-in request limiting with configurable thresholds

## 📦 Monorepo Structure

This template includes three main components designed as learning examples:

- **Backend** (`backend/`): **Production-ready FastAPI application** with robust infrastructure services and text processing domain examples
- **Frontend** (`frontend/`): **Production-ready Streamlit application** demonstrating modern development patterns for AI interfaces
- **Shared** (`shared/`): **Common Pydantic models** for type safety across components

**The backend infrastructure and frontend patterns are production-ready and reusable, while the text processing domain services serve as educational examples meant to be replaced with your specific business logic.**

## 🏗️ Architecture Overview

### Infrastructure vs Domain Services Architecture

The backend follows a clear architectural distinction between **Infrastructure Services** and **Domain Services**:

#### Infrastructure Services 🏗️ **[Production-Ready - Keep & Extend]**
- **Purpose**: Business-agnostic, reusable technical capabilities that form the backbone of any LLM API
- **Characteristics**: Stable APIs, high test coverage (>90%), configuration-driven behavior
- **Examples**: Cache management, resilience patterns, AI provider integrations, monitoring, security utilities
- **Location**: `app/infrastructure/` - core modules designed to remain stable across projects

#### Domain Services 💼 **[Educational Examples - Replace with Your Logic]**
- **Purpose**: Business-specific implementations serving as **educational examples**
- **Characteristics**: Designed to be replaced per project, moderate test coverage (>70%), feature-driven
- **Examples**: Text processing workflows (summarization, sentiment analysis), document analysis pipelines
- **Location**: `app/services/` - customizable modules that demonstrate best practices

### Dual-API Architecture

```
┌─────────────────────────────────────────────────────────────────┐
│                     FastAPI Application                        │
├─────────────────────────────────────────────────────────────────┤
│  Public API (/v1/)           │  Internal API (/internal/)       │
│  ├─ Text Processing          │  ├─ Cache Management              │
│  ├─ Health Checks            │  ├─ System Monitoring             │
│  ├─ Authentication           │  ├─ Circuit Breaker Control       │
│  └─ Business Operations      │  └─ Resilience Configuration      │
├─────────────────────────────────────────────────────────────────┤
│                   Infrastructure Services                       │
│  ├─ AI (Security & Providers)  ├─ Resilience (Circuit Breakers) │
│  ├─ Cache (Redis + Memory)     ├─ Security (Auth & Validation)  │
│  └─ Monitoring (Health & Metrics)                              │
└─────────────────────────────────────────────────────────────────┘
           │                            │
    ┌─────────────┐              ┌─────────────┐
    │  Streamlit  │              │   Shared    │
    │  Frontend   │              │   Models    │
    │  (8501)     │              │ (Pydantic) │
    └─────────────┘              └─────────────┘
```

### Custom Exception Handling System

The backend implements a comprehensive **custom exception hierarchy** that provides structured error handling across all services:

**Exception Types & HTTP Status Codes:**
- **`ValidationError`** (400): Input validation failures, configuration format issues
- **`AuthenticationError`** (401): Authentication failures, API key issues  
- **`AuthorizationError`** (403): Permission and authorization failures
- **`BusinessLogicError`** (422): Business rule violations, resource not found
- **`InfrastructureError`** (500): Service failures, Redis issues, AI service problems

**Structured Error Responses:**
All exceptions are converted to consistent JSON responses with:
```json
{
  "success": false,
  "error": "Human-readable error message",
  "error_code": "VALIDATION_ERROR", 
  "details": {
    "field": "Additional context for debugging",
    "operation": "Operation that failed"
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

**Global Exception Handler:**
- Converts custom exceptions to appropriate HTTP responses
- Maintains consistent error structure across all endpoints
- Includes structured context data for debugging and monitoring
- Provides detailed logging with request tracing

## 🚀 Quick Start

### Prerequisites

- **Python 3.8+** for backend development
- **Docker and Docker Compose** for containerized development
- **AI API Key** (Gemini, OpenAI, or Anthropic)

### 1. Clone and Setup Environment

```bash
git clone <repository-url>
cd fastapi-streamlit-llm-starter

# Complete setup - creates venv and installs all dependencies
make install
```

### 2. Configure Environment Variables

Create and configure your environment file:

```bash
cp .env.example .env
```

**Essential Configuration:**
```env
# AI Model Configuration
GEMINI_API_KEY=your_gemini_api_key_here
AI_MODEL=gemini-2.0-flash-exp
AI_TEMPERATURE=0.7

# Resilience Configuration (Choose one preset)
RESILIENCE_PRESET=simple      # General use, testing
# RESILIENCE_PRESET=development # Local dev, fast feedback  
# RESILIENCE_PRESET=production  # Production workloads

# Optional: Redis for caching (falls back to memory cache)
REDIS_URL=redis://localhost:6379
```

**Available Resilience Presets:**
- **simple**: 3 retries, 5 failure threshold, 60s recovery, balanced strategy
- **development**: 2 retries, 3 failure threshold, 30s recovery, aggressive strategy
- **production**: 5 retries, 10 failure threshold, 120s recovery, conservative strategy

### 3. Start the Application

**Option A: Full Development Environment (Recommended)**
```bash
# Start all services with hot reload and file watching
make dev
```

**Option B: Backend Only (Local Development)**
```bash
# Start FastAPI server locally with auto-reload
make run-backend
```

**Option C: Production Mode**
```bash
# Start optimized production environment
make prod
```

### 4. Access the Application

- **🌐 Frontend (Streamlit)**: http://localhost:8501
- **🔌 Backend API**: http://localhost:8000
- **📚 API Documentation (Swagger)**: http://localhost:8000/docs
- **📖 Internal API Documentation**: http://localhost:8000/internal/docs
- **❤️ Health Check**: http://localhost:8000/health

### 5. Verify Installation

```bash
# Check service health
make health

# Run comprehensive tests
make test

# Check code quality
make lint
```

## 🐳 Docker & Containerization

The template includes comprehensive Docker support for both development and production:

### Available Services
- **Backend (FastAPI)**: AI text processing API with resilience infrastructure
- **Frontend (Streamlit)**: Interactive web interface with real-time updates
- **Redis**: High-performance caching with graceful fallback to memory cache

### Essential Commands

```bash
# Show all available commands with descriptions
make help

# 🏗️ Setup and Installation
make install                # Complete setup - creates venv and installs dependencies
make install-frontend-local # Install frontend deps in current venv (local dev)

# 🖥️ Development Servers
make run-backend           # Start FastAPI server locally (localhost:8000)
make dev                   # Start full development environment with hot reload
make prod                  # Start production environment

# 🧪 Testing Commands
make test                  # Run all tests (backend + frontend)
make test-backend          # Run backend tests (fast tests by default)
make test-backend-all      # Run all backend tests (including slow tests)
make test-frontend         # Run frontend tests via Docker
make test-coverage         # Run tests with coverage reporting

# 🔍 Code Quality
make lint                  # Run all code quality checks (backend + frontend)
make lint-backend          # Run backend linting (flake8 + mypy)
make format                # Format code with black and isort

# ⚙️ Resilience Configuration Management
make list-presets          # List available resilience configuration presets
make show-preset PRESET=production  # Show preset details
make validate-config       # Validate current resilience configuration
make recommend-preset ENV=production # Get preset recommendation

# 🐳 Docker Operations
make docker-build          # Build all Docker images
make status                # Show status of all services
make logs                  # Show all service logs
make health                # Check health of all services
make stop                  # Stop all services

# 🗄️ Data Management
make redis-cli             # Access Redis command line interface
make backup                # Backup Redis data with timestamp
make restore BACKUP=filename # Restore Redis data

# 🧹 Cleanup
make clean                 # Clean Python cache files and test artifacts
make clean-all             # Complete cleanup (cache + venv)
```

### Development vs Production Modes

**Development Features (`make dev`):**
- **Hot Reload**: Automatic reloads on code changes with file watching
- **Debug Mode**: Comprehensive logging and error details
- **Volume Mounts**: Live code editing without rebuilds
- **Internal Docs**: Access to administrative API documentation

**Production Features (`make prod`):**
- **Optimized Builds**: Multi-stage Docker builds without dev dependencies
- **Security Hardening**: Non-root users, disabled internal docs
- **Resource Limits**: Memory and CPU constraints for stability
- **Graceful Degradation**: Fallback mechanisms for service failures

## 🎯 Example AI Operations

The template includes these **educational examples** to demonstrate API patterns:

1. **Summarize** (`summarize`) - Text summarization with configurable length (50-500 words)
2. **Sentiment Analysis** (`sentiment`) - Emotional tone analysis with confidence scores and explanations
3. **Key Points** (`key_points`) - Key point extraction with customizable count (3-10 points)
4. **Question Generation** (`questions`) - Educational question creation (3-10 questions)
5. **Q&A** (`qa`) - Interactive question answering requiring question parameter

**💡 Template Usage**: These operations showcase how to structure LLM-powered API endpoints. Replace them with your specific business operations while following the same patterns.

## 🔧 Technology Stack

### Backend (Production-Ready)
- **FastAPI**: Modern, fast web framework with automatic API documentation
- **PydanticAI**: Type-safe AI agent framework with built-in security
- **Redis**: High-performance caching with automatic fallback to in-memory
- **Pydantic**: Data validation and settings management with type hints
- **uvicorn**: ASGI server with hot reload capabilities

### Frontend (Production-Ready Patterns)
- **Streamlit**: Modern web application framework for AI interfaces
- **httpx**: Async HTTP client for robust API communication
- **asyncio**: Proper async/await patterns optimized for Streamlit

### Infrastructure (Production-Ready)
- **Docker**: Multi-stage containerization for development and production
- **Docker Compose**: Service orchestration with health checks and dependency management
- **Circuit Breakers**: Automatic failure detection and service protection
- **Retry Mechanisms**: Intelligent retry with exponential backoff and jitter
- **Comprehensive Monitoring**: Health checks, metrics collection, and performance analysis

## 📚 Usage Examples

### API Integration

```python
#!/usr/bin/env python3
"""Example API usage with comprehensive error handling."""

import asyncio
import httpx
from shared.sample_data import get_sample_text

async def process_text_example():
    """Demonstrate text processing with the API."""
    async with httpx.AsyncClient(timeout=30.0) as client:
        try:
            # Single text processing
            response = await client.post(
                "http://localhost:8000/v1/text_processing/process",
                headers={"X-API-Key": "your-api-key"},
                json={
                    "text": get_sample_text("ai_technology"),
                    "operation": "summarize",
                    "options": {"max_length": 150}
                }
            )
            response.raise_for_status()
            result = response.json()
            
            # Check if the response indicates success
            if result.get("success", False):
                print(f"Summary: {result['result']}")
            else:
                print(f"Error: {result.get('error', 'Unknown error')}")
                print(f"Error Code: {result.get('error_code', 'N/A')}")
                
        except httpx.HTTPStatusError as e:
            error_detail = e.response.json()
            print(f"HTTP {e.response.status_code} Error: {error_detail.get('error', 'Unknown error')}")
            print(f"Error Code: {error_detail.get('error_code', 'N/A')}")
            print(f"Details: {error_detail.get('details', {})}")
        
        try:
            # Batch processing
            batch_response = await client.post(
                "http://localhost:8000/v1/text_processing/batch_process",
                headers={"X-API-Key": "your-api-key"},
                json={
                    "requests": [
                        {"text": get_sample_text("business_report"), "operation": "sentiment"},
                        {"text": get_sample_text("climate_change"), "operation": "key_points"}
                    ],
                    "batch_id": "example_batch"
                }
            )
            batch_response.raise_for_status()
            batch_result = batch_response.json()
            
            if batch_result.get("success", False):
                print(f"Batch completed: {batch_result['completed']}/{batch_result['total_requests']}")
            else:
                print(f"Batch Error: {batch_result.get('error', 'Unknown error')}")
                
        except httpx.HTTPStatusError as e:
            error_detail = e.response.json()
            print(f"Batch processing failed with HTTP {e.response.status_code}: {error_detail.get('error')}")

# Run the example
if __name__ == "__main__":
    asyncio.run(process_text_example())
```

### Shared Models Usage

```python
from shared.models import TextProcessingRequest, TextProcessingOperation
from shared.sample_data import get_sample_text, get_example_options

# Create type-safe requests
request = TextProcessingRequest(
    text=get_sample_text("ai_technology"),
    operation=TextProcessingOperation.SUMMARIZE,
    options={"max_length": 100}
)

# Q&A operation (requires question)
qa_request = TextProcessingRequest(
    text=get_sample_text("technical_documentation"),
    operation=TextProcessingOperation.QA,
    question="What authentication method does the API use?"
)

# Get UI-friendly example options
example_options = get_example_options()
# Returns: {"ai_technology": "🤖 AI Technology - About AI trends", ...}
```

## 🎨 Frontend Features

### Production-Ready UI Components
- **Real-time Status Monitoring**: API health checks with visual indicators
- **Dynamic Operation Configuration**: Backend-driven UI generation
- **Intelligent Example System**: Operation-specific text recommendations
- **Multi-Modal Input Support**: Text entry and file upload with validation (.txt, .md)
- **Progress Indicators**: Real-time feedback during processing
- **Results Persistence**: Session management with download functionality

### User Experience Features
- **Graceful Degradation**: Continues operation when backend is unavailable
- **Comprehensive Validation**: Input validation with structured error responses and detailed context
- **Timeout Management**: Request timeout handling with user feedback
- **Progressive Disclosure**: Collapsible sections and smart defaults for better UX

## 🛠️ Development Workflow

### Architecture-Driven Development

The template uses a **hybrid development approach** optimized for modern AI application development:

- **Backend**: Local virtual environment for fast iteration and IDE integration
- **Frontend**: Docker-only to ensure consistent Streamlit environment across machines
- **Infrastructure**: Docker Compose for Redis and service integration testing

### Development Commands

```bash
# 🚀 Quick Start Development
make install && make dev    # Complete setup and start development environment

# 🔧 Backend Development (Local Virtual Environment)
make run-backend           # Start FastAPI server with auto-reload (localhost:8000)
source .venv/bin/activate  # Activate virtual environment for IDE integration

# 🎨 Frontend Development (Docker Only)
make dev                   # Start Streamlit via Docker with hot reload (localhost:8501)

# 🧪 Testing Workflow
make test-backend          # Fast backend tests (parallel execution)
make test-frontend         # Frontend tests via Docker
make test-coverage         # Comprehensive coverage reporting

# 📊 Quality Assurance
make lint                  # All code quality checks (backend + frontend)
make format                # Automatic code formatting with black/isort
```

### Project Structure

```
fastapi-streamlit-llm-starter/
├── backend/                          # 🏗️ FastAPI Application
│   ├── app/
│   │   ├── main.py                   # Dual FastAPI app (public + internal APIs)
│   │   ├── dependencies.py           # Global dependency injection
│   │   ├── api/                      # API Layer
│   │   │   ├── v1/                   # Public API endpoints (/v1/)
│   │   │   └── internal/             # Internal API endpoints (/internal/)
│   │   ├── infrastructure/           # 🏗️ Production-Ready Infrastructure
│   │   │   ├── ai/                   # AI security & provider abstractions
│   │   │   ├── cache/                # Multi-tier caching (Redis + Memory)
│   │   │   ├── resilience/           # Circuit breakers, retry, orchestration
│   │   │   ├── security/             # Authentication & authorization
│   │   │   └── monitoring/           # Health checks & metrics
│   │   ├── services/                 # 💼 Domain Services [Educational Examples]
│   │   │   ├── text_processor.py     # Example AI text processing service
│   │   │   └── response_validator.py # Example response validation
│   │   ├── schemas/                  # Request/response models
│   │   └── core/                     # Application configuration
│   ├── tests/                        # Comprehensive test suite (23k+ lines)
│   └── examples/                     # Infrastructure usage examples
|
├── frontend/                         # 🎨 Streamlit Application
│   ├── app/
│   │   ├── app.py                    # Main Streamlit application (854 lines)
│   │   ├── config.py                 # Configuration management
│   │   └── utils/api_client.py       # Async API client with error handling
│   └── tests/                        # Frontend tests with async patterns
|
├── shared/                           # 📊 Shared Pydantic Models
│   ├── models.py                     # Core data models & validation
│   └── sample_data.py                # Standardized example content
|
├── examples/                         # 📚 API Integration Examples
├── docs/                             # 📖 Comprehensive Documentation
├── docker-compose.yml                # 🐳 Development orchestration
├── docker-compose.prod.yml           # 🚀 Production configuration
└── Makefile                          # 🛠️ Development commands (762 lines)
```

### Adding New Operations

**1. Update Shared Models** (`shared/models.py`):
```python
class TextProcessingOperation(str, Enum):
    SUMMARIZE = "summarize"
    SENTIMENT = "sentiment"
    # Add your new operation
    TRANSLATE = "translate"
```

**2. Add Backend Logic** (`backend/app/services/text_processor.py`):
```python
async def _translate_text(self, text: str, options: Dict[str, Any]) -> str:
    """Translate text to target language."""
    target_language = options.get("target_language", "Spanish")
    
    prompt = f"""
    Translate the following text to {target_language}:
    
    Text: {text}
    
    Translation:
    """
    
    result = await self.agent.run(prompt)
    return result.output.strip()
```

**3. Update Frontend UI** (`frontend/app/app.py`):
```python
# Add UI controls for new operation
if "target_language" in op_info.get("options", []):
    options["target_language"] = st.selectbox(
        "Target Language",
        ["Spanish", "French", "German", "Italian"]
    )
```

## 🧪 Comprehensive Testing

The project includes a robust testing framework with **parallel execution by default** for fast feedback cycles:

### Test Organization & Coverage

**Backend Testing** (`backend/tests/` - 23,162 lines across 59 test files):
- **Infrastructure Tests** (>90% coverage): Cache, resilience, AI, security, monitoring
- **Domain Service Tests** (>70% coverage): Text processing, validation
- **API Tests**: Public (`/v1/`) and internal (`/internal/`) endpoints
- **Integration Tests**: Cross-component testing with mocked external services
- **Performance Tests**: Load testing and resilience pattern validation

**Frontend Testing** (`frontend/tests/`):
- **API Client Tests**: Async communication patterns with custom exception handling and structured error responses
- **Configuration Tests**: Environment variable validation and settings
- **Mock Integration**: Isolated testing with httpx mocking
- **Parallel Execution**: Fast test execution with pytest-xdist

### Testing Commands

```bash
# 🏗️ Setup and Basic Testing
make install               # Setup environment and dependencies
make test                 # Run all tests (backend + frontend)
make test-coverage        # Comprehensive coverage reporting

# 🔬 Backend Testing (Granular)
make test-backend                    # Fast tests (parallel, excludes slow/manual)
make test-backend-api               # API endpoint tests
make test-backend-infrastructure    # Infrastructure service tests  
make test-backend-integration       # Integration tests
make test-backend-all               # All tests including slow tests
make test-backend-manual            # Manual tests (requires live server)

# 🎨 Frontend Testing
make test-frontend         # Frontend tests via Docker

# 📊 Specialized Testing
make test-retry           # Retry mechanism tests
make test-circuit         # Circuit breaker tests
make test-presets         # Resilience preset tests
```

### Test Execution Features

**Parallel Execution (Default):**
- Tests run with `pytest-xdist` for faster feedback cycles
- Environment isolation with `monkeypatch.setenv()`
- Sequential mode available for debugging: `pytest -n 0`

**Test Categories:**
- **Fast Tests** (default): Unit tests, quick integration tests
- **Slow Tests** (`--run-slow` flag): Comprehensive resilience testing, timing tests
- **Manual Tests** (`--run-manual` flag): Require live server and real API keys

**Manual Test Setup:**
```bash
# 1. Set environment variables
export GEMINI_API_KEY="your-actual-gemini-api-key"
export API_KEY="test-api-key-12345"

# 2. Start server
make run-backend

# 3. Run manual tests (in another terminal)
make test-backend-manual
```

## 🚀 Production Deployment

### Environment-Specific Configuration

**Development:**
```bash
export RESILIENCE_PRESET=development
export DEBUG=true
export LOG_LEVEL=DEBUG
export SHOW_DEBUG_INFO=true
```

**Production:**
```bash
export RESILIENCE_PRESET=production
export DEBUG=false
export LOG_LEVEL=INFO
export DISABLE_INTERNAL_DOCS=true
export CORS_ORIGINS='["https://your-frontend-domain.com"]'
```

### Deployment Options

**Option 1: Production Mode**
```bash
# Start optimized production environment
make prod

# Access services:
# - Backend: http://localhost:8000 (internal docs disabled)
# - Frontend: http://localhost:8501
# - Redis: localhost:6379
```

**Option 2: Manual Docker Compose**
```bash
# Production configuration with optimizations
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d

# Check deployment status
make status
make health
```

### Scaling & Performance

**Horizontal Scaling:**
```bash
# Scale backend instances for load distribution
docker-compose up -d --scale backend=3

# Scale frontend instances for user load
docker-compose up -d --scale frontend=2

# Monitor performance
make logs
make health
```

**Performance Optimization:**
- **Redis Caching**: Automatic caching with compression for improved response times
- **Circuit Breakers**: Prevent cascade failures during high load
- **Connection Pooling**: Efficient resource utilization
- **Multi-stage Docker Builds**: Optimized container sizes

## ⚙️ Configuration

### Resilience Configuration Presets

The application includes a **simplified resilience configuration system** that reduces 47+ environment variables to a single preset selection:

#### Quick Setup (Recommended)
```env
# Choose one preset based on your environment
RESILIENCE_PRESET=simple      # Balanced for most use cases
RESILIENCE_PRESET=development # Fast-fail for development
RESILIENCE_PRESET=production  # High reliability for production
```

#### Available Presets

| Preset | Use Case | Retry Attempts | Circuit Breaker | Recovery Time | Strategy |
|--------|----------|---------------|-----------------|---------------|-----------|
| **simple** | General use, testing | 3 | 5 failures | 60s | Balanced |
| **development** | Local dev, fast feedback | 2 | 3 failures | 30s | Aggressive |
| **production** | Production workloads | 5 | 10 failures | 120s | Conservative |

#### Advanced Custom Configuration
For fine-tuned control, use JSON configuration:
```env
RESILIENCE_CUSTOM_CONFIG='{
  "retry_attempts": 4,
  "circuit_breaker_threshold": 8,
  "recovery_timeout": 90,
  "default_strategy": "balanced",
  "operation_overrides": {
    "qa": "critical",
    "sentiment": "aggressive"
  }
}'
```

#### Environment-Aware Recommendations
The system automatically detects your environment and suggests appropriate presets:
- Development indicators (DEBUG=true, localhost) → `development` preset
- Production indicators (PROD=true, production URLs) → `production` preset
- Unknown environments → `simple` preset (safe default)

#### Migration from Legacy Configuration
If you have existing resilience configuration (47+ environment variables), the system will:
1. **Automatically detect** legacy configuration
2. **Continue using** existing settings for backward compatibility
3. **Suggest migration** to presets via API: `GET /resilience/config`

**Migration example:**
```bash
# Check current configuration and get migration suggestions
curl http://localhost:8000/resilience/config

# Validate a custom configuration
curl -X POST http://localhost:8000/resilience/validate \
  -H "Content-Type: application/json" \
  -d '{"configuration": {"retry_attempts": 3, "circuit_breaker_threshold": 5}}'
```

### Complete Environment Variables Reference

| Variable | Description | Default | Environment |
|----------|-------------|---------|-------------|
| `RESILIENCE_PRESET` | Resilience configuration preset | `simple` | All |
| `GEMINI_API_KEY` | Google Gemini API key | Required | All |
| `AI_MODEL` | AI model to use | `gemini-2.0-flash-exp` | All |
| `AI_TEMPERATURE` | Model temperature | `0.7` | All |
| `API_KEY` | Primary API key | Required | All |
| `ADDITIONAL_API_KEYS` | Additional valid API keys (comma-separated) | None | Production |
| `REDIS_URL` | Redis connection URL | `redis://localhost:6379` | Optional |
| `DEBUG` | Enable debug mode | `false` | Development |
| `LOG_LEVEL` | Logging level | `INFO` | All |
| `DISABLE_INTERNAL_DOCS` | Disable internal API docs | `false` | Production |
| `CORS_ORIGINS` | Allowed CORS origins (JSON array) | `["http://localhost:8501"]` | Production |
| `MAX_TEXT_LENGTH` | Max input text length | `10000` | All |
| `SHOW_DEBUG_INFO` | Frontend debug information | `false` | Development |

## 🛠️ Customizing This Template for Your Project

### Template Customization Checklist

- [ ] Replace `TextProcessorService` with your business logic
- [ ] Update API endpoints in `app/api/v1/` 
- [ ] Modify data models in `app/schemas/` and `shared/models.py`
- [ ] Configure your LLM provider in settings
- [ ] Customize Streamlit frontend for your operations or replace with your preferred UI
- [ ] Update authentication and security settings
- [ ] Configure resilience presets for your environment
- [ ] Update README.md with your project details
- [ ] Replace example tests with your business logic tests

## 🔧 Troubleshooting

### Common Issues

**1. API Connection Failed**
```bash
# Check if backend is running
curl http://localhost:8000/health

# Verify services status
make status
make health

# Check logs for errors
make logs
make backend-logs
```

**API Error Response Format:**
All API errors return structured JSON responses:
```json
{
  "success": false,
  "error": "Human-readable error message",
  "error_code": "VALIDATION_ERROR",
  "details": {
    "field": "Additional context",
    "operation": "summarize"
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

**Common Error Codes:**
- `VALIDATION_ERROR` (400): Invalid input data or configuration
- `AUTHENTICATION_ERROR` (401): Missing or invalid API key
- `AUTHORIZATION_ERROR` (403): Insufficient permissions
- `BUSINESS_LOGIC_ERROR` (422): Business rule violation or resource not found
- `INFRASTRUCTURE_ERROR` (500): Internal service failures

**2. AI API Errors**
```bash
# Verify API keys are set correctly
echo $GEMINI_API_KEY

# Check AI service availability
curl http://localhost:8000/v1/health

# Check API quota and billing in your AI provider console
```

**AI Service Error Responses:**
```json
{
  "success": false,
  "error": "AI service temporarily unavailable",
  "error_code": "INFRASTRUCTURE_ERROR",
  "details": {
    "service": "gemini",
    "operation": "summarize",
    "retry_after": "30s"
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

**3. Redis Connection Errors**
```bash
# Check Redis connectivity
make redis-cli

# Application automatically falls back to memory cache
# Verify cache status
curl http://localhost:8000/internal/cache/status
```

**Cache Service Error Handling:**
```json
{
  "success": false,
  "error": "Redis connection failed, using memory cache fallback",
  "error_code": "INFRASTRUCTURE_ERROR",
  "details": {
    "service": "redis",
    "fallback_active": true,
    "performance_impact": "minimal"
  },
  "timestamp": "2024-01-01T12:00:00Z"
}
```

**4. Port Conflicts**
```bash
# Change ports in docker-compose.yml if needed
ports:
  - "8001:8000"  # Backend
  - "8502:8501"  # Frontend
  - "6380:6379"  # Redis
```

**5. Import Errors**
```bash
# Ensure virtual environment is activated and dependencies installed
make install

# For manual setup
source .venv/bin/activate
cd backend && pip install -r requirements.lock
```

**6. Test Failures**
```bash
# For manual tests, ensure server is running
make run-backend

# Set required environment variables
export API_KEY="test-api-key-12345"
export GEMINI_API_KEY="your-gemini-api-key"

# Run manual tests
make test-backend-manual
```

### Debug Mode

Enable comprehensive debugging:
```bash
# Backend debug mode
export DEBUG=true
export LOG_LEVEL=DEBUG

# Frontend debug mode  
export SHOW_DEBUG_INFO=true

# Start with debugging enabled
make dev
```

This provides:
- **Enhanced Error Context**: Detailed error messages with structured context data
- **Custom Exception Stack Traces**: Full debugging information for specific error types
- **Request/Response Logging**: Complete audit trail with error classification
- **Auto-reload on Code Changes**: Hot reload for rapid development iteration
- **Internal API Documentation Access**: Administrative endpoints for monitoring
- **Error Code Mapping**: Clear mapping between custom exceptions and HTTP status codes

## 📚 Learning Resources

### Examples and Documentation

**API Integration Examples** (`examples/`):
- **`basic_usage.py`**: Complete HTTP client integration examples
- **`custom_operation.py`**: Step-by-step guide for adding new operations
- **`integration_test.py`**: Comprehensive integration testing patterns

**Infrastructure Examples** (`backend/examples/`):
- **`advanced_infrastructure_demo.py`**: Complete infrastructure component integration
- **`cache_configuration_examples.py`**: Different caching patterns for various environments

**Comprehensive Documentation** (`docs/`):
- **`architecture-design/`**: Detailed architectural guidance and design patterns
- **`code_ref/`**: Auto-generated code reference documentation
- **Component READMEs**: Detailed documentation for each major component

### Additional Resources

**Interactive Documentation** (when server is running):
- **Public API (Swagger)**: http://localhost:8000/docs
- **Internal API (Swagger)**: http://localhost:8000/internal/docs
- **Public API (ReDoc)**: http://localhost:8000/redoc
- **Internal API (ReDoc)**: http://localhost:8000/internal/redoc

**Component Documentation**:
- **Backend**: `backend/README.md` - FastAPI application architecture and setup
- **Frontend**: `frontend/README.md` - Streamlit application patterns and features
- **Shared**: `shared/README.md` - Common data models and sample data
- **API**: `backend/app/api/README.md` - Comprehensive API endpoint documentation

## 💡 Template Benefits

This starter template provides:

- **Rapid Prototyping**: Quick setup for AI application development with comprehensive infrastructure
- **Production-Ready Architecture**: Scalable patterns suitable for enterprise deployment
- **Educational Value**: Best practices demonstration for FastAPI, Streamlit, and AI integration
- **Extensible Design**: Clear separation between infrastructure and domain logic for easy customization
- **Comprehensive Testing**: Reliable test patterns with high coverage requirements
- **Modern Development Experience**: Automated tooling, hot reload, and intelligent configuration management

### Learning Outcomes

Developers using this template will learn:

- **Modern FastAPI Architecture**: Dual-API design, dependency injection, and comprehensive configuration management
- **Production AI Integration**: Secure LLM integration with custom exception hierarchy, resilience patterns, and comprehensive monitoring
- **Infrastructure vs Domain Patterns**: Clear architectural boundaries for maintainable, scalable applications
- **Advanced Streamlit Development**: Production-ready frontend patterns with async integration and comprehensive testing
- **DevOps Best Practices**: Docker containerization, automated testing, and deployment strategies

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch (`git checkout -b feature/amazing-feature`)
3. Make your changes following the established patterns
4. Add tests maintaining coverage requirements (Infrastructure >90%, Domain >70%)
5. Run the test suite: `make test`
6. Run code quality checks: `make lint`
7. Submit a pull request with a clear description

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- **📖 Documentation**: Comprehensive guides in `docs/` directory
- **🔧 Makefile Help**: Run `make help` for all available commands
- **🏗️ Architecture Guide**: See `docs/architecture-design/` for detailed patterns
- **📊 API Documentation**: Interactive docs at http://localhost:8000/docs when running

---

**🚀 Start building production-ready AI applications today!**
