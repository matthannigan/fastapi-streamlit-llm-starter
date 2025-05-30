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

Edit `.env` file with your API keys:

```env
GEMINI_API_KEY=your_gemini_api_key_here
AI_MODEL=gemini-2.0-flash-exp
AI_TEMPERATURE=0.7
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
- **Redis**: Caching and session storage
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

### Local Development Setup

**Recommended: Use the enhanced Makefile (with automatic virtual environment management):**
```bash
# Create virtual environment and install all dependencies
make install

# Run tests locally (no Docker required)
make test-local

# Run code quality checks
make lint

# Format code
make format

# Clean up when needed
make clean-all
```

**Use the provided scripts:**
```bash
# Automated setup
./scripts/setup.sh

# Run backend
./scripts/run_backend.sh

# Run frontend (new terminal)
./scripts/run_frontend.sh
```

**Or setup manually with project-level virtual environment:**
```bash
# Create project-level virtual environment
python3 -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install backend dependencies
cd backend
pip install -r requirements.txt -r requirements-dev.txt

# Install frontend dependencies
cd ../frontend
pip install -r requirements.txt -r requirements-dev.txt

# Start backend (from project root)
cd ../backend
uvicorn app.main:app --reload

# Start frontend (new terminal, from project root)
cd frontend
streamlit run app/app.py
```

### Project Structure

```
fastapi-streamlit-llm-starter/
├── backend/                 # FastAPI application
│   ├── app/
│   │   ├── main.py         # FastAPI app and routes
│   │   ├── config.py       # Configuration management
│   │   └── services/       # Business logic services
│   └── Dockerfile
├── frontend/                # Streamlit application
│   ├── app/
│   │   ├── app.py          # Main Streamlit app
│   │   ├── config.py       # Frontend configuration
│   │   └── utils/          # Utility functions
│   └── Dockerfile
├── shared/                  # Shared Pydantic models
│   └── models.py
├── nginx/                   # Nginx configuration
├── docker-compose.yml       # Docker orchestration
└── Makefile                # Development shortcuts
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

The project includes comprehensive testing with automatic virtual environment management:

```bash
# Install dependencies and setup virtual environment
make install

# Run all tests (includes Docker integration tests if available)
make test

# Run local tests only (no Docker required)
make test-local

# Run backend tests only
make test-backend

# Run frontend tests only
make test-frontend

# Run with coverage
make test-coverage

# Run code quality checks
make lint

# Format code
make format
```

**Manual testing with Docker:**
```bash
# Run backend tests in Docker
docker-compose exec backend python -m pytest

# Run with coverage in Docker
docker-compose exec backend python -m pytest --cov=app
```

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

### Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
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

## Deployment
- [DEPLOYMENT.md](docs/DEPLOYMENT.md) - Deployment guide
- [DOCKER.md](docs/DOCKER.md) - Docker setup and management
- [API.md](docs/API.md) - API documentation

## Support
- [AUTHENTICATION.md](docs/AUTHENTICATION.md) - Authentication setup
- [TROUBLESHOOTING.md](docs/TROUBLESHOOTING.md) - Common issues and solutions
- [CONTRIBUTING.md](docs/CONTRIBUTING.md) - How to contribute
