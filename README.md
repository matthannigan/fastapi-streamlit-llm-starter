# FastAPI-Streamlit-LLM Starter Template

A production-ready starter template for building AI-powered applications using FastAPI, Streamlit, and PydanticAI.

## 🌟 Features

- **🚀 Modern Stack**: FastAPI + Streamlit + PydanticAI
- **🤖 AI Integration**: Easy integration with multiple AI models
- **📊 Rich UI**: Interactive Streamlit interface with real-time updates
- **🐳 Docker Ready**: Complete containerization for easy deployment
- **🔒 Production Ready**: Security headers, rate limiting, health checks
- **📈 Scalable**: Designed for horizontal scaling
- **🧪 Extensible**: Easy to add new features and AI operations

## 🏗️ Architecture

```
┌─────────────────┐    ┌──────────────────┐    ┌─────────────────┐
│   Streamlit     │───▶│     FastAPI      │───▶│   PydanticAI    │
│   Frontend      │    │     Backend      │    │   + LLM APIs    │
└─────────────────┘    └──────────────────┘    └─────────────────┘
         │                       │                      │
         │              ┌─────────────────┐             │
         └─────────────▶│  Shared Models  │◀────────────┘
                        │   (Pydantic)    │
                        └─────────────────┘
```

## 🚀 Quick Start

### Prerequisites

- Docker and Docker Compose
- AI API Key (Gemini, OpenAI, or Anthropic)

### 1. Clone and Setup

```bash
git clone <repository-url>
cd fastapi-streamlit-llm-starter
cp .env.example .env
```

### 2. Configure Environment

Edit `.env` file with your API keys and resilience settings:

```env
# AI Configuration
GEMINI_API_KEY=your_gemini_api_key_here
AI_MODEL=gemini-2.0-flash-exp
AI_TEMPERATURE=0.7

# Resilience Configuration (Choose one approach)
# Option 1: Use preset (recommended)
RESILIENCE_PRESET=simple  # Options: simple, development, production

# Option 2: Custom configuration (advanced users)
# RESILIENCE_CUSTOM_CONFIG='{"retry_attempts": 3, "circuit_breaker_threshold": 5}'
```

### 3. Start the Application

```bash
# Development mode (with hot reload)
make dev

# Or production mode
make prod

# Or using docker-compose directly
docker-compose up --build
```

### 4. Access the Application

- **Frontend**: http://localhost:8501
- **Backend API**: http://localhost:8000
- **API Docs**: http://localhost:8000/docs

## 🐳 Docker Setup

This project includes a comprehensive Docker setup for both development and production environments.

### Services

- **Backend**: FastAPI application with AI text processing
- **Frontend**: Streamlit web interface
- **Redis**: Caching and session storage (see [`docs/CACHE.md`](docs/CACHE.md) for details)
- **Nginx**: Reverse proxy and load balancer (production only)

### Quick Commands

```bash
# Show all available commands
make help

# Setup and testing
make install          # Create venv and install dependencies
make test            # Run all tests (with Docker if available)
make test-local      # Run tests without Docker
make lint            # Code quality checks
make format          # Format code

# Development environment (with hot reload)
make dev

# Production environment (with scaling and nginx)
make prod

# Docker management
make status          # Check service status
make logs            # View logs
make health          # Health check all services

# Cleanup
make clean           # Clean generated files
make clean-all       # Clean including virtual environment
```

### Development vs Production

**Development Features:**
- Hot reloading for both backend and frontend
- Debug mode enabled
- Volume mounts for live code editing
- Development dependencies included

**Production Features:**
- Optimized builds without development dependencies
- Non-root users for security
- Resource limits and horizontal scaling
- Nginx reverse proxy with rate limiting
- No volume mounts for security

### Service Management

```bash
# Individual service logs
make backend-logs
make frontend-logs
make redis-logs

# Access containers
make backend-shell
make frontend-shell
make redis-cli

# Backup/restore Redis data
make backup
make restore BACKUP=redis-20240101-120000.rdb
```

For detailed Docker setup information, see [DOCKER_README.md](DOCKER_README.md).

## 📖 Usage

> **📋 Code Standards:** All examples follow standardized patterns for imports, error handling, and sample data. See [`docs/CODE_STANDARDS.md`](docs/CODE_STANDARDS.md) for detailed guidelines.

### Available Operations

1. **Summarize**: Generate concise summaries of long texts
2. **Sentiment Analysis**: Analyze emotional tone and confidence
3. **Key Points**: Extract main points from content
4. **Question Generation**: Create questions about the text
5. **Q&A**: Answer specific questions about the content

### Example API Usage

```python
#!/usr/bin/env python3
"""Example API usage with standardized patterns."""

# Standard library imports
import asyncio
import logging
from typing import Optional, Dict, Any

# Third-party imports
import httpx

# Local application imports
from shared.sample_data import get_sample_text

# Configure logging
logger = logging.getLogger(__name__)

async def example_api_usage():
    """Demonstrate API usage with proper error handling."""
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Process text using standardized sample data
            response = await client.post(
                "http://localhost:8000/process", 
                json={
                    "text": get_sample_text("ai_technology"),
                    "operation": "summarize",
                    "options": {"max_length": 100}
                }
            )
            response.raise_for_status()
            result = response.json()
            print(f"Summary: {result['result']}")
            
    except httpx.TimeoutException:
        logger.error("Request timeout")
        print("Request timed out. Please try again.")
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error: {e.response.status_code}")
        print(f"API Error: {e.response.status_code}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        print(f"Error: {str(e)}")

# Run the example
if __name__ == "__main__":
    asyncio.run(example_api_usage())
```

### Frontend Features

- **File Upload**: Support for .txt and .md files
- **Real-time Processing**: Live progress indicators
- **Rich Results**: Formatted output with metrics
- **Download Results**: Export results as JSON
- **Example Content**: Built-in examples for testing

## 🛠️ Development

This project uses a **hybrid approach** to resolve dependency conflicts:

- **Backend**: Uses a local virtual environment for fast development
- **Frontend**: Runs exclusively in Docker to avoid packaging version conflicts

### Quick Start

#### Using Makefile (Recommended)

1. **Complete setup:**
   ```bash
   make install
   ```
   This creates a `.venv` virtual environment and installs all backend dependencies with lock files.

2. **Run backend locally:**
   ```bash
   # Activate the virtual environment
   source .venv/bin/activate
   
   # Start the FastAPI server
   cd backend && uvicorn app.main:app --reload
   ```

3. **Run frontend via Docker:**
   ```bash
   # Start frontend and dependencies
   docker-compose up frontend
   ```

#### Using Scripts (Alternative)

The scripts provide the same functionality with enhanced user experience:

```bash
# One-time automated setup (includes Docker validation)
./scripts/setup.sh

# Run backend (handles venv creation/activation automatically)
./scripts/run_backend.sh

# Run frontend (Docker-only, includes dependency management)
./scripts/run_frontend.sh
```

**Script Benefits:**
- ✅ Automatic virtual environment detection and creation
- ✅ Lock file support with fallback to requirements.txt
- ✅ Comprehensive environment validation
- ✅ Rich feedback and helpful troubleshooting tips
- ✅ Consistent with Makefile patterns

### Development Workflow

- **Backend development:** Use your local virtual environment with your favorite IDE
- **Frontend development:** Edit files locally, run via Docker for testing
- **Full stack testing:** Use Docker Compose for integration testing

**Enhanced Script Features:**
- **Smart Setup**: Scripts automatically detect existing environments and dependencies
- **Lock File Support**: Prioritizes `requirements.lock` files for reproducible installs
- **Environment Validation**: Comprehensive checks for Python, Docker, and required files
- **Rich Feedback**: Clear status messages, tips, and troubleshooting guidance
- **Graceful Handling**: Proper cleanup and error handling throughout

This approach provides:
- ✅ Fast backend development with local virtual environment
- ✅ No dependency conflicts (frontend isolated in Docker)  
- ✅ Consistent frontend environment across all machines
- ✅ Easy deployment (both services already containerized)
- ✅ Production-quality development tooling

### Project Structure (Abbreviated)

```
fastapi-streamlit-llm-starter/
├── backend/                    # FastAPI application
│   ├── app/
│   │   ├── main.py                     # FastAPI app and main routes
│   │   ├── config.py                   # Configuration management
│   │   ├── auth.py                     # Authentication and authorization
│   │   ├── dependencies.py             # Dependency injection
│   │   ├── routers/                    # Specialized API route modules
│   │   ├── services/                   # Business logic services
│   │   ├── security/                   # Security components
│   │   └── utils/                      # Utility functions
│   ├── tests/                      # Comprehensive unit tests
│   ├── Dockerfile                  # Container configuration
│   └── README.md                   # Backend documentation
├── docs/                       # Comprehensive project documentation
├── examples                    # Practical application guides
├── frontend/                   # Streamlit application
│   ├── app/
│   │   ├── app.py                      # Main Streamlit app
│   │   ├── config.py                   # Frontend configuration
│   │   └── utils/                      # Utility functions
│   ├── tests/                      # Unit tests for frontend
│   ├── Dockerfile                  # Container configuration
│   └── README.md                   # Frontend documentation
├── shared/                     # Shared module
│   ├── shared/
│   │   ├── examples.py
│   │   ├── models.py               # Pydantic models
│   │   └── sample_data.py
│   └── models.py
├── nginx/                   # Nginx configuration
├── docker-compose.yml       # Docker orchestration
├── Makefile                 # Development shortcuts
└── README.md                # Primary project README
```

### Adding New Operations

1. **Update Shared Models** (`shared/models.py`):
```python
class ProcessingOperation(str, Enum):
    SUMMARIZE = "summarize"
    # Add your new operation
    TRANSLATE = "translate"
```

2. **Add Backend Logic** (`backend/app/services/text_processor.py`):
```python
async def _translate_text(self, text: str, options: Dict[str, Any]) -> str:
    target_language = options.get("target_language", "Spanish")
    # Implementation here
    return translated_text
```

3. **Update Frontend UI** (`frontend/app/app.py`):
```python
# Add UI controls for new operation
if "target_language" in op_info.get("options", []):
    options["target_language"] = st.selectbox(
        "Target Language",
        ["Spanish", "French", "German", "Italian"]
    )
```

### Testing

The project includes comprehensive testing with **parallel execution by default** for fast feedback:

```bash
# Install dependencies and setup virtual environment
make install

# Run all tests (includes Docker integration tests if available)
make test

# Run local tests only (no Docker required)
make test-local

# Run backend tests only (uses local virtual environment)
make test-backend

# Run frontend tests only (uses Docker)
make test-frontend

# Run with coverage
make test-coverage

# Run code quality checks
make lint

# Format code
make format
```

**Advanced Testing with Parallel Execution:**
```bash
# Backend parallel testing (default behavior)
cd backend
scripts/test.sh                                    # All tests in parallel
scripts/test.sh -c                                # With coverage report
scripts/test.sh -w 4                              # Use 4 workers specifically
scripts/test.sh tests/test_specific.py            # Specific test file
scripts/test.sh -m debug tests/test_failing.py    # Debug mode (sequential)

# Test execution modes
scripts/test.sh -m parallel                       # Fast parallel execution (default)
scripts/test.sh -m sequential                     # Sequential for debugging
scripts/test.sh -m debug                          # Detailed debugging output

# Coverage and reporting
scripts/test.sh -c -v                             # Coverage with verbose output
scripts/test.sh -w 8 -c                          # Maximum parallelization with coverage
```

**Manual testing with Docker:**
```bash
# Run backend tests in Docker (parallel by default)
docker-compose exec backend python -m pytest

# Run with coverage in Docker
docker-compose exec backend python -m pytest --cov=app

# Debug mode in Docker
docker-compose exec backend python -m pytest -s -vv -n 0
```

**Testing Best Practices:**
- ✅ All tests run in parallel by default for faster feedback
- ✅ Environment isolation ensures reliable parallel execution
- ✅ Use debug mode (`-m debug`) for troubleshooting failing tests
- ✅ Coverage reports available in `htmlcov/index.html`

## 🚀 Deployment

### Production Deployment

1. **Configure Environment**:
```bash
# Set production environment variables
export DEBUG=false
export LOG_LEVEL=INFO
export GEMINI_API_KEY=your_production_key
```

2. **Deploy with Docker**:
```bash
# Production mode
make prod

# Or with docker-compose
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

3. **Setup SSL** (optional):
```bash
# Add SSL certificates to nginx/ssl/
# Update nginx configuration for HTTPS
```

### Scaling

Scale individual services:
```bash
# Scale backend instances
docker-compose up -d --scale backend=3

# Scale frontend instances  
docker-compose up -d --scale frontend=2
```

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

For complete configuration details, see [Resilience Configuration](docs/RESILIENCE_CONFIG.md).

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `RESILIENCE_PRESET` | Resilience configuration preset | `simple` |
| `RESILIENCE_CUSTOM_CONFIG` | Custom JSON configuration (optional) | None |
| `GEMINI_API_KEY` | Google Gemini API key | Required |
| `AI_MODEL` | AI model to use | `gemini-2.0-flash-exp` |
| `AI_TEMPERATURE` | Model temperature | `0.7` |
| `DEBUG` | Enable debug mode | `false` |
| `LOG_LEVEL` | Logging level | `INFO` |
| `MAX_TEXT_LENGTH` | Max input text length | `10000` |

### Model Configuration

Easily switch between AI providers:

```python
# In backend/app/config.py
class Settings(BaseSettings):
    # Use OpenAI instead of Gemini
    openai_api_key: str = os.getenv("OPENAI_API_KEY", "")
    ai_model: str = "gpt-4"
    
    # Or use Anthropic Claude
    anthropic_api_key: str = os.getenv("ANTHROPIC_API_KEY", "")
    ai_model: str = "claude-3-sonnet"
```

## 🔧 Troubleshooting

### Common Issues

**1. CORS Errors**
```bash
# Check CORS configuration in backend/app/main.py
# Ensure frontend URL is in allowed_origins
```

**2. API Connection Failed**
```bash
# Check if backend is running
curl http://localhost:8000/health

# Check Docker network
docker-compose logs backend
```

**3. AI API Errors**
```bash
# Verify API keys are set correctly
echo $GEMINI_API_KEY

# Check API quota and billing
```

**4. Port Conflicts**
```bash
# Change ports in docker-compose.yml
ports:
  - "8001:8000"  # Backend
  - "8502:8501"  # Frontend
```

### Debug Mode

Enable debug mode for development:
```bash
export DEBUG=true
export SHOW_DEBUG_INFO=true
make dev
```

## 📚 Examples

### Basic Text Processing

```python
from shared.models import TextProcessingRequest, ProcessingOperation

# Create request
request = TextProcessingRequest(
    text="Artificial intelligence is transforming industries...",
    operation=ProcessingOperation.SUMMARIZE,
    options={"max_length": 100}
)

# Process with API
response = await api_client.process_text(request)
print(response.result)
```

### Custom AI Operations

See `docs/examples/` for detailed examples:
- Adding new text operations
- Integrating different AI models
- Custom UI components
- Authentication integration

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Add tests
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## 🆘 Support

- 📖 [Documentation](docs/)
- 🐛 [Issue Tracker](issues/)
- 💬 [Discussions](discussions/)

---

**Happy coding! 🚀**

# Documentation Index

## Getting Started
- [README.md](../README.md) - Project overview and quick start
- [CHECKLIST.md](docs/CHECKLIST.md) - Complete setup checklist
- [VIRTUAL_ENVIRONMENT_GUIDE.md](docs/VIRTUAL_ENVIRONMENT_GUIDE.md) - Virtual environment management

## Development
- [INTEGRATION_GUIDE.md](docs/INTEGRATION_GUIDE.md) - Complete integration guide
- [TESTING.md](docs/TESTING.md) - Testing guide with virtual environment support
- [CODE_STANDARDS.md](docs/CODE_STANDARDS.md) - Code standards and patterns
- [RESILIENCE_CONFIG.md](docs/RESILIENCE_CONFIG.md) - Resilience configuration guide and migration

## Deployment
- [DEPLOYMENT.md](docs/DEPLOYMENT.md) - Deployment guide
- [DOCKER.md](docs/DOCKER.md) - Docker setup and management
- [API.md](docs/API.md) - API documentation

## Support
- [AUTHENTICATION.md](docs/AUTHENTICATION.md) - Authentication setup
- [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) - Common issues and solutions
- [CONTRIBUTING.md](docs/CONTRIBUTING.md) - How to contribute
