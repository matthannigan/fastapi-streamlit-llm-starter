# FastAPI Backend - Production-Ready AI Text Processing API

A comprehensive FastAPI application showcasing production-ready architecture for AI-powered text processing services. This backend serves as both a working application and an educational template demonstrating modern software engineering practices for building scalable, maintainable LLM-powered APIs.

## 🎯 Template Purpose & Architecture Overview

**This backend is a production-ready starter template** that demonstrates industry best practices for building sophisticated AI APIs. It combines reusable infrastructure services with educational domain examples to help developers understand and implement robust AI applications.

### Dual-API Architecture

The application implements a **dual-API architecture** with clear separation of concerns:

- **Public API** (`/v1/`): External-facing domain endpoints with authentication
- **Internal API** (`/internal/`): Administrative infrastructure endpoints for monitoring and management

This separation provides security isolation, allows independent scaling, and enables different documentation strategies for different user types.

### Infrastructure vs Domain Services Architecture

The backend follows a clear architectural distinction between **Infrastructure Services** (production-ready, reusable) and **Domain Services** (educational examples to be replaced):

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

**Dependency Direction**: `Domain Services → Infrastructure Services → External Dependencies`

### Core Module Integration Layer

The **Core Module** (`app/core/`) serves as the critical integration layer that ties together infrastructure and domain services. It provides:

- **Configuration Management** (`config.py`): Centralized settings with validation, resilience presets, and environment variable support
- **Exception Handling** (`exceptions.py`): Unified exception hierarchy with intelligent classification for retry logic
- **Middleware Infrastructure** (`middleware.py`): Production-ready middleware stack with CORS, security, logging, and monitoring

**Key Integration Role**: The core module acts as the central nervous system that enables your domain logic to seamlessly integrate with production-ready infrastructure services without tight coupling.

**For Developers**: See the **[Core Module Integration Guide](../developer/CORE_MODULE_INTEGRATION.md)** for detailed patterns on working with configuration, exceptions, and middleware when customizing the template.

## 🚀 Quick Start

### Using Makefile Commands (Recommended)

```bash
# Complete setup (creates venv and installs dependencies)
make install

# Start development server with auto-reload
make run-backend

# Run comprehensive test suite
make test-backend

# Check code quality
make lint-backend

# Get all available commands
make help
```

### Manual Setup

```bash
# Create virtual environment
python3 -m venv .venv
source .venv/bin/activate

# Install dependencies
cd backend
pip install -r requirements.lock -r requirements-dev.lock

# Set up environment variables
export GEMINI_API_KEY="your-gemini-api-key"
export API_KEY="your-secure-api-key"

# Start server
uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload
```

### Docker Development

```bash
# Start full development environment with hot reload
make dev

# Access services:
# - Backend (FastAPI): http://localhost:8000
# - Frontend (Streamlit): http://localhost:8501
# - Redis: localhost:6379
```

## 📊 API Documentation

### Interactive Documentation

When the server is running, access comprehensive API documentation:

- **Public API (Swagger)**: http://localhost:8000/docs
- **Internal API (Swagger)**: http://localhost:8000/internal/docs  
- **Public API (ReDoc)**: http://localhost:8000/redoc
- **Internal API (ReDoc)**: http://localhost:8000/internal/redoc

### Key API Endpoints

#### Public API (`/v1/`)
- `GET /v1/health` - Comprehensive health check with component status
- `GET /v1/auth/status` - Authentication validation and API key verification
- `GET /v1/text_processing/operations` - List available AI operations
- `POST /v1/text_processing/process` - Single text processing operation
- `POST /v1/text_processing/batch_process` - Batch text processing operations

#### Internal API (`/internal/`)
- `GET /internal/monitoring/health` - System metrics and performance monitoring
- `GET /internal/cache/status` - Cache status and performance metrics
- `POST /internal/cache/invalidate` - Cache management operations
- `GET /internal/resilience/health` - Resilience infrastructure status
- `GET /internal/resilience/circuit-breakers` - Circuit breaker monitoring
- `GET /internal/resilience/config/presets` - Resilience configuration management

### Available AI Operations **[Educational Examples]**

The template includes these **educational examples** to demonstrate API patterns:

1. **Summarize** (`summarize`) - Text summarization with configurable length
2. **Sentiment Analysis** (`sentiment`) - Emotional tone analysis with confidence scores  
3. **Key Points** (`key_points`) - Key point extraction with configurable count
4. **Questions** (`questions`) - Question generation from text
5. **Q&A** (`qa`) - Question answering requiring question parameter

**💡 Template Usage**: These operations showcase how to structure LLM-powered API endpoints. Replace them with your specific business operations while following the same patterns.

## 🧪 Testing

### Test Organization

The backend includes a comprehensive test suite with **23,162 lines** across **59 test files**, organized by architectural boundaries:

```
backend/tests/
├── infrastructure/         # Tests for reusable infrastructure (>90% coverage)
│   ├── ai/                # AI infrastructure tests
│   ├── cache/             # Cache infrastructure tests  
│   ├── resilience/        # Resilience infrastructure tests
│   ├── security/          # Security infrastructure tests
│   └── monitoring/        # Monitoring infrastructure tests
├── core/                  # Application configuration and setup tests
├── services/              # Domain service tests (educational examples)
├── api/                   # API endpoint tests
│   ├── v1/               # Public API tests
│   └── internal/         # Internal API tests
├── integration/           # Cross-component integration tests
├── performance/           # Performance and load tests
└── manual/               # Manual tests (require live server)
```

### Test Execution

```bash
# Run fast tests (default - excludes slow and manual tests)
make test-backend

# Run specific test categories
make test-backend-api              # API endpoint tests
make test-backend-core             # Core functionality tests
make test-backend-infrastructure   # Infrastructure service tests
make test-backend-integration      # Integration tests
make test-backend-services         # Domain service tests

# Run comprehensive tests including slow tests
make test-backend-all

# Run manual tests (requires running server)
make test-backend-manual

# Run with coverage reporting
make test-coverage
```

### Manual Test Requirements

Manual tests require a live server and real API keys:

```bash
# 1. Set environment variables
export GEMINI_API_KEY="your-actual-gemini-api-key"
export API_KEY="test-api-key-12345"

# 2. Start server
make run-backend

# 3. Run manual tests (in another terminal)
make test-backend-manual
```

## ⚙️ Configuration Management

### Resilience Configuration System

The application uses a comprehensive **resilience configuration system** with **38 endpoints** for managing circuit breakers, retry mechanisms, and performance monitoring.

#### Environment-Based Presets (Recommended)

```bash
# Choose one preset based on environment
export RESILIENCE_PRESET=simple      # General use, testing
export RESILIENCE_PRESET=development # Local dev, fast feedback  
export RESILIENCE_PRESET=production  # Production workloads
```

**Available presets:**
- **simple**: 3 retries, 5 failure threshold, 60s recovery, balanced strategy
- **development**: 2 retries, 3 failure threshold, 30s recovery, aggressive strategy
- **production**: 5 retries, 10 failure threshold, 120s recovery, conservative strategy

#### Advanced Custom Configuration

```bash
# Custom JSON configuration for advanced scenarios
export RESILIENCE_CUSTOM_CONFIG='{"retry_attempts": 3, "circuit_breaker_threshold": 5}'
```

#### Resilience Management Commands

```bash
# List available presets
make list-resil-presets

# Show preset details  
make show-resil-preset PRESET=production

# Validate current configuration
make validate-resil-config

# Get environment recommendations
make recommend-resil-preset ENV=production

# Migrate legacy configuration
make migrate-config
```

### Core Environment Variables

#### Essential Configuration
```bash
# AI Model Configuration
GEMINI_API_KEY=your_gemini_api_key        # Required for AI operations
AI_MODEL=gemini-2.0-flash-exp             # AI model selection
AI_TEMPERATURE=0.7                        # Model temperature

# Authentication
API_KEY=your_secure_api_key               # Primary API key
ADDITIONAL_API_KEYS=key1,key2,key3        # Additional valid keys

# Resilience Configuration  
RESILIENCE_PRESET=production              # Resilience preset
```

#### Optional Configuration
```bash
# Server Settings
BACKEND_HOST=0.0.0.0                      # Server host
BACKEND_PORT=8000                         # Server port
DEBUG=false                               # Debug mode
LOG_LEVEL=INFO                            # Logging level

# Cache Configuration
REDIS_URL=redis://localhost:6379          # Redis connection
CACHE_DEFAULT_TTL=3600                    # Cache TTL in seconds
CACHE_COMPRESSION_THRESHOLD=1000          # Compression threshold

# Security Settings
CORS_ORIGINS=["http://localhost:8501"]    # Allowed CORS origins
DISABLE_INTERNAL_DOCS=true                # Disable internal docs in production
```

## 🏗️ Project Structure

```
backend/
├── app/
│   ├── main.py                          # FastAPI app setup, dual-API routing
│   ├── dependencies.py                  # Global dependency injection
│   │
│   ├── api/                             # API Layer: Request/Response handling
│   │   ├── v1/                         # Public API endpoints
│   │   │   ├── text_processing.py      # Main business logic endpoints
│   │   │   ├── health.py               # Health check endpoints
│   │   │   ├── auth.py                 # Authentication endpoints
│   │   │   └── deps.py                 # API-specific dependencies
│   │   └── internal/                   # Internal/admin endpoints
│   │       ├── monitoring.py           # System monitoring endpoints
│   │       ├── cache.py                # Cache management endpoints
│   │       └── resilience/             # Resilience management (38 endpoints)
│   │
│   ├── core/                           # Application-wide setup
│   │   ├── config.py                   # Centralized Pydantic settings
│   │   ├── exceptions.py               # Custom exception classes
│   │   └── middleware.py               # CORS, error handling middleware
│   │
│   ├── infrastructure/                 # Reusable infrastructure services [KEEP]
│   │   ├── ai/                        # AI provider abstractions, security
│   │   │   ├── input_sanitizer.py     # Prompt injection protection
│   │   │   └── prompt_builder.py      # Secure prompt construction
│   │   ├── cache/                     # Multi-tier caching system
│   │   │   ├── base.py                # Cache interface
│   │   │   ├── redis.py               # Redis implementation
│   │   │   ├── memory.py              # Memory cache implementation
│   │   │   └── monitoring.py          # Cache performance monitoring
│   │   ├── resilience/                # Comprehensive resilience patterns
│   │   │   ├── circuit_breaker.py     # Circuit breaker implementation
│   │   │   ├── retry.py               # Retry mechanisms
│   │   │   ├── orchestrator.py        # Resilience orchestration
│   │   │   ├── config_presets.py      # Preset configuration system
│   │   │   └── performance_benchmarks.py # Performance testing
│   │   ├── security/                  # Authentication and authorization
│   │   │   └── auth.py                # API key authentication
│   │   └── monitoring/                # Health checks and metrics
│   │       ├── health.py              # Health check implementations
│   │       └── metrics.py             # Metrics collection
│   │
│   ├── services/                      # Domain services [REPLACE WITH YOUR LOGIC]
│   │   ├── text_processor.py          # Example text processing service
│   │   └── response_validator.py      # Example response validation
│   │
│   └── schemas/                       # Pydantic models (data contracts)
│       ├── text_processing.py         # Request/response models
│       ├── health.py                  # Health check models
│       └── common.py                  # Shared response models
├── examples/                          # Infrastructure usage examples
├── tests/                            # Comprehensive test suite (23k+ lines)
├── scripts/                          # Utility scripts
├── requirements.txt                  # Python dependencies
├── requirements-dev.txt              # Development dependencies
├── Dockerfile                        # Docker configuration
└── README.md                         # This file
```

## 🛡️ Security & AI Safety Features

**Production-grade security measures built into the infrastructure:**

- **Prompt Injection Protection**: Detects and blocks malicious prompt injection attempts
- **Input Sanitization**: Comprehensive input validation for all AI operations
- **API Key Authentication**: Multi-key support with secure header-based authentication
- **Internal API Protection**: Administrative endpoints disabled in production environments
- **Response Validation**: AI output validation and sanitization
- **Security Logging**: Comprehensive audit trails for security monitoring

## 🔧 Infrastructure Features

### Multi-Tier Caching System
- **Redis-backed Storage**: Persistent caching with automatic failover to memory-only
- **Compression Support**: Automatic compression for large responses  
- **Performance Monitoring**: Real-time cache metrics and optimization recommendations
- **Graceful Degradation**: Continues operation without Redis if connection fails

### Comprehensive Resilience Patterns
- **Circuit Breakers**: Prevent cascade failures during AI service outages
- **Intelligent Retry Logic**: Exponential backoff with jitter for transient failures
- **Exception Classification**: Smart categorization of permanent vs transient errors
- **Graceful Degradation**: Fallback mechanisms for failed operations

### Advanced Monitoring
- **Health Checks**: Component-level health monitoring and status reporting
- **Performance Metrics**: Operation timing, success rates, and failure patterns
- **Circuit Breaker Status**: Real-time resilience pattern monitoring
- **Cache Analytics**: Hit rates, memory usage, and performance statistics

## 📈 Performance Characteristics

### Performance Targets

| Component | Target Performance | Actual Performance |
|-----------|-------------------|-------------------|
| **Preset Loading** | <10ms | ~2-5ms typical |
| **Configuration Loading** | <100ms | ~15-50ms typical |
| **Service Initialization** | <200ms | ~50-150ms typical |
| **Circuit Breaker Call** | <1ms overhead | ~0.1-0.5ms typical |

### Memory Usage
- **Base Memory**: ~2-5MB for core resilience infrastructure
- **Per-Operation**: ~100-500KB additional memory per registered operation
- **Metrics Storage**: ~1-10MB depending on retention settings

## 🔧 Development Tools

### Code Quality

```bash
# Run all code quality checks
make lint-backend

# Format code with black and isort
make format

# Run type checking with mypy
cd backend && python -m mypy app/ --ignore-missing-imports
```

### Documentation Generation

```bash
# Generate code documentation
make repomix-backend        # Backend-only documentation
make repomix-backend-tests  # Backend tests documentation
```

### Performance Monitoring

```bash
# Run performance benchmarks
cd backend && python -c "
from app.infrastructure.resilience.performance_benchmarks import ConfigurationPerformanceBenchmark
benchmark = ConfigurationPerformanceBenchmark()
suite = benchmark.run_comprehensive_benchmark()
print(f'Overall pass rate: {suite.pass_rate:.1f}%')
"
```

## 🚀 Deployment

### Docker Production

```bash
# Start production environment
make prod

# Access production services:
# - Backend: http://localhost:8000 (internal docs disabled)
# - Redis: localhost:6379
```

### Environment-Specific Configuration

**Development:**
```bash
export RESILIENCE_PRESET=development
export DEBUG=true
export LOG_LEVEL=DEBUG
```

**Production:**
```bash
export RESILIENCE_PRESET=production
export DISABLE_INTERNAL_DOCS=true
export LOG_LEVEL=INFO
export CORS_ORIGINS='["https://your-frontend-domain.com"]'
```

## 🛠️ Customizing This Template for Your Project

### Quick Start Guide

1. **Keep the Infrastructure** 🏗️
   - Use `app/infrastructure/` services as-is (cache, resilience, security, monitoring)
   - Configure resilience presets for your environment
   - Extend infrastructure services if needed, maintaining existing APIs

2. **Replace Domain Services** 💼
   - Study patterns in `app/services/text_processor.py`
   - Replace with your specific business logic
   - Maintain the same error handling and validation patterns
   - Keep the >70% test coverage requirement

3. **Update API Endpoints** 🌐
   - Modify `app/api/v1/text_processing.py` with your business endpoints
   - Keep the authentication and error handling patterns
   - Update `app/schemas/` with your data models

4. **Configure for Your Environment** ⚙️
   - Update `app/core/config.py` with your settings
   - Configure your AI provider (replace Gemini with your preferred LLM)
   - Set up Redis or use memory cache fallback
   - Configure authentication keys and CORS settings

### What to Keep vs. Replace

**✅ Keep & Use (Production-Ready)**:
- All `app/infrastructure/` services
- `app/core/` configuration and middleware
- `app/api/` authentication and error handling patterns
- Testing infrastructure and coverage requirements
- Docker and development tooling
- Makefile commands and CI/CD setup

**🔄 Study & Replace (Educational Examples)**:
- `app/services/` domain services  
- API endpoint business logic
- Data models and schemas
- Example processing operations

## 🔍 Troubleshooting

### Common Issues

1. **AI Service Unavailable**
   - Check `GEMINI_API_KEY` is set correctly
   - Verify API key has proper permissions
   - Check network connectivity

2. **Redis Connection Errors**
   - Verify Redis is running at `REDIS_URL`
   - Application will automatically fallback to memory cache
   - Check `make health` for service status

3. **Import Errors**
   - Ensure working directory is `backend/`
   - Verify virtual environment is activated
   - Check all dependencies are installed: `make install`

4. **Test Failures**
   - For manual tests: ensure server is running and API keys are set
   - For parallel test issues: use `pytest -n 0` to run sequentially
   - Check test isolation with `monkeypatch.setenv()`

### Debug Mode

Enable comprehensive debugging:
```bash
export DEBUG=true
export LOG_LEVEL=DEBUG
make run-backend
```

This provides:
- Detailed error messages and stack traces
- Request/response logging
- Auto-reload on code changes
- Internal API documentation access

## Related Documentation

### Prerequisites
- **[Complete Setup Guide](../get-started/SETUP_INTEGRATION.md)**: Basic template setup and environment configuration
- **[Infrastructure vs Domain Services](../reference/key-concepts/INFRASTRUCTURE_VS_DOMAIN.md)**: Understanding the architectural distinction fundamental to backend design

### Related Topics
- **[API Documentation](./API.md)**: Detailed reference for public and internal API endpoints
- **[Dual API Architecture](../reference/key-concepts/DUAL_API_ARCHITECTURE.md)**: Understanding the dual-API design philosophy
- **[Testing Guide](./TESTING.md)**: Comprehensive testing strategies for backend components

### Next Steps
- **[Security Guide](./SECURITY.md)**: Comprehensive security implementation guide
- **[Operations Monitoring Guide](./operations/MONITORING.md)**: Production monitoring and operational procedures
- **[Troubleshooting Guide](./operations/TROUBLESHOOTING.md)**: Backend troubleshooting procedures
- **[AI Infrastructure](./infrastructure/AI.md)**: Production-ready AI infrastructure service with security-first design
- **[Cache Infrastructure](./infrastructure/CACHE.md)**: Multi-tiered caching optimized for AI response patterns
- **[Resilience Infrastructure](./infrastructure/RESILIENCE.md)**: Circuit breakers, retry mechanisms, and performance monitoring
- **[Security Infrastructure](./infrastructure/SECURITY.md)**: Defense-in-depth security for AI-powered applications
- **[Monitoring Infrastructure](./infrastructure/MONITORING.md)**: Comprehensive observability and performance analytics
- **[Authentication Guide](./developer/AUTHENTICATION.md)**: Multi-key authentication system configuration

## 📄 License

This project is licensed under the MIT License.