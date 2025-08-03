# Setup & Complete Systems Integration Guide

Welcome to the comprehensive setup and system integration guide for the FastAPI-Streamlit-LLM Starter Template! This guide ties together all components and provides complete usage examples to get you up and running quickly.

## 📋 Table of Contents

1. [Quick Start](#-quick-start)
2. [System Architecture](#-system-architecture)
3. [Complete Setup Guide](#-complete-setup-guide)
4. [Usage Examples](#-usage-examples)
5. [API Integration](#-api-integration)
6. [Frontend Integration](#-frontend-integration)
7. [Custom Operations](#-custom-operations)
8. [Testing & Validation](#-testing--validation)
9. [Deployment](#-deployment)
10. [Troubleshooting](#-troubleshooting)

## 🚀 Quick Start

Get the entire system running in under 5 minutes:

### 1. Clone and Setup
```bash
git clone <repository-url>
cd fastapi-streamlit-llm-starter
cp .env.example .env
# Edit .env with your API keys
```

### 2. Configure Authentication
```bash
# Edit .env file with your configuration
API_KEY=your-secure-api-key-here
GEMINI_API_KEY=your-gemini-api-key
AUTH_MODE=simple  # or 'advanced' for enhanced features
RESILIENCE_PRESET=development  # or 'simple', 'production'
```

### 3. Start Backend
```bash
# Using Makefile (recommended)
make install                # Creates virtual environment and installs dependencies
make run-backend           # Starts FastAPI with auto-reload

# Or manually
source .venv/bin/activate   # Activate virtual environment
cd backend
uvicorn app.main:app --reload --port 8000
```

### 4. Start Frontend
```bash
# Using Makefile (recommended)
make install-frontend-local  # Install frontend dependencies in current venv
make run-frontend           # Start Streamlit app

# Or manually
source .venv/bin/activate
cd frontend
streamlit run app/app.py --server.port 8501
```

### 5. Test the System
```bash
# Using Makefile (recommended)
make test-backend          # Run backend tests
make test-frontend         # Run frontend tests via Docker

# Test API directly
curl -H "Authorization: Bearer your-secure-api-key-here" \
     -H "Content-Type: application/json" \
     -d '{"text":"Hello world","operation":"summarize"}' \
     http://localhost:8000/v1/text_processing/process
```

**🎉 You're ready to go!**
- **Backend Public API**: http://localhost:8000/v1/ (external-facing endpoints)
- **Backend Internal API**: http://localhost:8000/internal/ (admin/monitoring)
- **Frontend UI**: http://localhost:8501
- **Public API Docs**: http://localhost:8000/docs (Swagger UI for public API)
- **Internal API Docs**: http://localhost:8000/internal/docs (admin endpoints)
- **Health Check**: http://localhost:8000/health
- **System Monitoring**: http://localhost:8000/internal/monitoring/overview

## 🏗️ System Architecture

```mermaid
graph TB
    subgraph "Frontend Layer"
        ST[Streamlit UI]
        ST --> PUB[Public API /v1/]
    end
    
    subgraph "Dual-API Backend"
        PUB[Public API /v1/] --> DS[Domain Services]
        INT[Internal API /internal/] --> IS[Infrastructure Services]
        
        subgraph "Infrastructure Services"
            IS --> CACHE[Cache Service]
            IS --> RES[Resilience Patterns]
            IS --> SEC[Security Service]
            IS --> MON[Monitoring Service]
        end
        
        subgraph "Domain Services"
            DS --> TP[Text Processor]
            DS --> RV[Response Validator]
        end
        
        CACHE --> REDIS[Redis Cache]
        CACHE --> MEM[Memory Cache]
        TP --> AI[PydanticAI Agent]
    end
    
    subgraph "AI Layer"
        AI --> GM[Gemini Model]
    end
    
    subgraph "Shared Layer"
        SM[Shared Models] --> PUB
        SM --> INT
    end
    
    subgraph "Examples & Testing"
        EX[Examples] --> PUB
        IT[Integration Tests] --> PUB
        IT --> INT
    end
```

### Component Overview

| Component | Purpose | Technology | Coverage |
|-----------|---------|------------|----------|
| **Frontend** | Production-ready UI for AI operations | Streamlit | N/A |
| **Public API** | External-facing business endpoints | FastAPI | 95%+ |
| **Internal API** | Administrative/infrastructure endpoints | FastAPI | 95%+ |
| **Infrastructure Services** | Production-ready technical capabilities | Python | >90% |
| **Domain Services** | Educational examples (replace with your logic) | Python + PydanticAI | >70% |
| **Resilience Patterns** | Circuit breakers, retry, orchestration | Python | >90% |
| **Cache System** | Redis + memory cache with fallback | Redis/Python | >90% |
| **Security Service** | Multi-key auth, input sanitization | Python | >90% |
| **Shared Models** | Cross-service data validation | Pydantic | 100% |

## 🔧 Complete Setup Guide

### Prerequisites
- Python 3.8+
- Gemini API key (get from Google AI Studio)
- Git

### Environment Setup

1. **Backend Configuration:**
   ```bash
   cd backend
   cp env.example .env
   ```
   
   Edit `.env`:
   ```env
   # Authentication Configuration
   AUTH_MODE=simple                # Choose: simple or advanced
   API_KEY=dev-test-key-12345     # Primary API key for authentication
   ADDITIONAL_API_KEYS=key1,key2   # Optional additional keys
   
   # Advanced Auth Features (AUTH_MODE=advanced only)
   ENABLE_USER_TRACKING=false      # Enable user context tracking
   ENABLE_REQUEST_LOGGING=false    # Enable security event logging
   
   # Resilience Configuration
   RESILIENCE_PRESET=development   # Choose: simple, development, production
   
   # AI Configuration
   GEMINI_API_KEY=your_api_key_here
   AI_MODEL=gemini-2.0-flash-exp
   
   # Development Settings
   DEBUG=true
   LOG_LEVEL=DEBUG
   HOST=0.0.0.0
   PORT=8000
   
   # Infrastructure Settings
   REDIS_URL=redis://localhost:6379       # Optional - falls back to memory cache
   CORS_ORIGINS=["http://localhost:8501"]
   DISABLE_INTERNAL_DOCS=false           # Enable internal API docs in development
   ```

2. **Install Dependencies:**
   ```bash
   # Using Makefile (recommended - handles virtual environment automatically)
   make install
   
   # Or manually with project-level virtual environment
   python3 -m venv .venv
   source .venv/bin/activate  # On Windows: .venv\Scripts\activate
   
   # Backend
   cd backend
   pip install -r requirements.txt -r requirements-dev.txt
   
   # Frontend
   cd ../frontend
   pip install -r requirements.txt -r requirements-dev.txt
   
   # Examples (optional)
   pip install httpx asyncio
   ```

3. **Verify Installation:**
   ```bash
   # Using Makefile (recommended)
   make test-local  # Runs tests to verify everything works
   
   # Or manually test components
   cd backend
   ../.venv/bin/python -c "from app.main import app; print('Backend OK')"
   
   # Test frontend
   cd ../frontend
   ../.venv/bin/python -c "import streamlit; print('Frontend OK')"
   ```

## 💡 Usage Examples

### Basic API Usage

```python
#!/usr/bin/env python3
"""Basic API usage example with authentication and dual-API structure."""

# Standard library imports
import asyncio
import logging
from typing import Dict, Any, Optional

# Third-party imports
import httpx

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

API_KEY = "dev-test-key-12345"  # Use your actual API key
BASE_URL = "http://localhost:8000"

async def basic_example():
    """Demonstrate basic API usage with authentication and error handling."""
    headers = {"Authorization": f"Bearer {API_KEY}"}
    
    try:
        async with httpx.AsyncClient(timeout=30.0) as client:
            # Health check (no auth required)
            response = await client.get(f"{BASE_URL}/health")
            response.raise_for_status()
            health = response.json()
            print(f"API Status: {health['status']}")
            
            # Check authentication status
            response = await client.get(f"{BASE_URL}/v1/auth/status", headers=headers)
            response.raise_for_status()
            auth_status = response.json()
            print(f"Auth Status: {auth_status}")
            
            # Process text using public API with authentication
            response = await client.post(
                f"{BASE_URL}/v1/text_processing/process",
                headers=headers,
                json={
                    "text": "Artificial intelligence is revolutionizing industries across the globe...",
                    "operation": "summarize",
                    "options": {"max_length": 50}
                }
            )
            response.raise_for_status()
            result = response.json()
            print(f"Summary: {result['result']}")
            
            # Check system monitoring (internal API)
            response = await client.get(f"{BASE_URL}/internal/monitoring/overview", headers=headers)
            response.raise_for_status()
            monitoring = response.json()
            print(f"System Status: {monitoring.get('status', 'unknown')}")
            
    except httpx.TimeoutException:
        logger.error("Request timeout")
        print("Request timed out. Please try again.")
    except httpx.HTTPStatusError as e:
        logger.error(f"HTTP error: {e.response.status_code}")
        error_detail = e.response.json().get('detail', 'Unknown error')
        print(f"API Error ({e.response.status_code}): {error_detail}")
    except Exception as e:
        logger.error(f"Unexpected error: {str(e)}")
        print(f"Error: {str(e)}")

# Run the example
if __name__ == "__main__":
    asyncio.run(basic_example())
```

### All Operations Example

```python
async def demonstrate_all_operations():
    """Demonstrate all available text processing operations with authentication."""
    
    headers = {"Authorization": f"Bearer {API_KEY}"}
    sample_text = "Climate change represents one of the most significant challenges facing humanity today..."
    
    operations = [
        {
            "operation": "summarize",
            "options": {"max_length": 50},
            "description": "Generate a concise summary"
        },
        {
            "operation": "sentiment",
            "options": {},
            "description": "Analyze emotional tone"
        },
        {
            "operation": "key_points",
            "options": {"max_points": 3},
            "description": "Extract main points"
        },
        {
            "operation": "questions",
            "options": {"num_questions": 2},
            "description": "Generate questions"
        },
        {
            "operation": "qa",
            "question": "What causes climate change?",
            "options": {},
            "description": "Answer specific questions"
        }
    ]
    
    async with httpx.AsyncClient() as client:
        for op in operations:
            print(f"\n🔄 {op['description']}")
            
            payload = {
                "text": sample_text,
                "operation": op["operation"],
                "options": op["options"]
            }
            
            if "question" in op:
                payload["question"] = op["question"]
            
            try:
                response = await client.post(
                    f"{BASE_URL}/v1/text_processing/process",
                    headers=headers,
                    json=payload
                )
                response.raise_for_status()
                result = response.json()
                
                if op["operation"] == "sentiment":
                    sentiment = result["sentiment"]
                    print(f"   Sentiment: {sentiment['sentiment']} ({sentiment['confidence']:.1%})")
                elif op["operation"] == "key_points":
                    print("   Key Points:")
                    for i, point in enumerate(result["key_points"], 1):
                        print(f"     {i}. {point}")
                elif op["operation"] == "questions":
                    print("   Questions:")
                    for i, question in enumerate(result["questions"], 1):
                        print(f"     {i}. {question}")
                else:
                    print(f"   Result: {result['result']}")
                    
            except httpx.HTTPStatusError as e:
                print(f"   Error: {e.response.status_code} - {e.response.text}")

# Run the demonstration
if __name__ == "__main__":
    asyncio.run(demonstrate_all_operations())
```

## 🔌 API Integration

### Dual-API Architecture

The template provides two distinct API interfaces:

#### Public API (`/v1/`) - External Business Logic
For external applications and frontend integration:

**Health Check** (No authentication required)
```http
GET /health
```
**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0"
}
```

**Authentication Status**
```http
GET /v1/auth/status
Authorization: Bearer your-api-key
```
**Response:**
```json
{
  "authenticated": true,
  "mode": "simple",
  "features": ["multi_key_support"]
}
```

**Process Text** (Authentication required)
```http
POST /v1/text_processing/process
Content-Type: application/json
Authorization: Bearer your-api-key

{
  "text": "Your text here",
  "operation": "summarize",
  "options": {"max_length": 100},
  "question": "Optional question for Q&A operations"
}
```

**Available Operations** (Optional authentication)
```http
GET /v1/operations
Authorization: Bearer your-api-key  # Optional
```
**Response:**
```json
{
  "operations": ["summarize", "sentiment", "key_points", "questions", "qa"],
  "authenticated": true
}
```

#### Internal API (`/internal/`) - Infrastructure Management
For administrative and monitoring tasks (requires API key authentication):

**System Monitoring**
```http
GET /internal/monitoring/overview
Authorization: Bearer your-api-key
```
**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "cache_performance": {
    "hit_ratio": 85.3,
    "avg_operation_time": 0.012,
    "memory_usage_mb": 45.2
  },
  "resilience_status": {
    "circuit_breakers": {"text_processing": "closed"},
    "retry_statistics": {"success_rate": 98.7}
  }
}
```

**Resilience Management** (38 endpoints across 8 focused modules)
```http
# Configuration Management (4 endpoints)
GET /internal/resilience/config/presets
POST /internal/resilience/config/validate
GET /internal/resilience/config/recommend-preset/{environment}
GET /internal/resilience/config/templates

# Circuit Breaker Management (3 endpoints)
GET /internal/resilience/circuit-breakers
GET /internal/resilience/circuit-breakers/{name}
POST /internal/resilience/circuit-breakers/{name}/reset

# Performance Monitoring (4 endpoints)
GET /internal/resilience/health
GET /internal/resilience/metrics  
POST /internal/resilience/benchmark
GET /internal/resilience/performance-metrics

# Cache Management (via monitoring)
GET /internal/monitoring/cache-stats
GET /internal/monitoring/cache-health

# System Analytics (4 endpoints)
GET /internal/resilience/usage-statistics
GET /internal/resilience/preset-trends/{preset}
GET /internal/resilience/alerts
GET /internal/resilience/performance-analysis
```

**Authentication required for all internal endpoints:**
```bash
# Set authentication header
curl -H "Authorization: Bearer your-api-key" \
     http://localhost:8000/internal/monitoring/overview
```

### Example API Usage

#### Public API Integration
```python
import httpx

async def use_public_api():
    headers = {"X-API-Key": "your-api-key"}
    
    async with httpx.AsyncClient() as client:
        # Health check
        health = await client.get("http://localhost:8000/v1/health")
        print(f"API Status: {health.json()['status']}")
        
        # Process text
        response = await client.post(
            "http://localhost:8000/v1/text-processing/summarize",
            headers=headers,
            json={
                "text": "Your long text here...",
                "options": {"max_length": 100}
            }
        )
        result = response.json()
        print(f"Summary: {result['result']}")
```

#### Internal API Integration
```python
async def monitor_system():
    headers = {"X-API-Key": "your-api-key"}
    
    async with httpx.AsyncClient() as client:
        # Check system health
        health = await client.get(
            "http://localhost:8000/internal/health",
            headers=headers
        )
        
        # Get resilience metrics
        metrics = await client.get(
            "http://localhost:8000/internal/resilience/metrics",
            headers=headers
        )
        
        # Check cache performance
        cache_stats = await client.get(
            "http://localhost:8000/internal/cache/stats",
            headers=headers
        )
        
        print(f"System Health: {health.json()['status']}")
        print(f"Cache Hit Rate: {cache_stats.json()['hit_rate']:.2%}")
```

### Python Client Library

Create a comprehensive client for both APIs:

```python
class LLMClient:
    """Comprehensive client for the dual-API FastAPI-Streamlit-LLM template."""
    
    def __init__(self, base_url: str = "http://localhost:8000", api_key: str = None):
        self.base_url = base_url
        self.api_key = api_key
        self.session = None
        self.headers = {"X-API-Key": api_key} if api_key else {}
    
    async def __aenter__(self):
        self.session = httpx.AsyncClient(timeout=30.0)
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        if self.session:
            await self.session.aclose()
    
    # Public API Methods
    async def summarize(self, text: str, max_length: int = 100) -> str:
        """Summarize text using public API."""
        response = await self.session.post(
            f"{self.base_url}/v1/text-processing/summarize",
            headers=self.headers,
            json={"text": text, "options": {"max_length": max_length}}
        )
        response.raise_for_status()
        return response.json()["result"]
    
    async def analyze_sentiment(self, text: str) -> dict:
        """Analyze sentiment using public API."""
        response = await self.session.post(
            f"{self.base_url}/v1/text-processing/sentiment",
            headers=self.headers,
            json={"text": text}
        )
        response.raise_for_status()
        return response.json()["sentiment"]
    
    async def get_operations(self) -> dict:
        """Get available operations from public API."""
        response = await self.session.get(
            f"{self.base_url}/v1/operations",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    # Internal API Methods (Infrastructure Management)
    async def get_system_health(self) -> dict:
        """Get comprehensive system health from internal API."""
        response = await self.session.get(
            f"{self.base_url}/internal/health",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    async def get_resilience_metrics(self) -> dict:
        """Get resilience metrics from internal API."""
        response = await self.session.get(
            f"{self.base_url}/internal/resilience/metrics",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    async def get_cache_stats(self) -> dict:
        """Get cache statistics from internal API."""
        response = await self.session.get(
            f"{self.base_url}/internal/cache/stats",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()
    
    async def validate_resilience_config(self, config: dict) -> dict:
        """Validate resilience configuration."""
        response = await self.session.post(
            f"{self.base_url}/internal/resilience/validate",
            headers=self.headers,
            json={"configuration": config}
        )
        response.raise_for_status()
        return response.json()
    
    async def reset_circuit_breaker(self, name: str) -> dict:
        """Reset a specific circuit breaker."""
        response = await self.session.post(
            f"{self.base_url}/internal/resilience/circuit-breakers/{name}/reset",
            headers=self.headers
        )
        response.raise_for_status()
        return response.json()

# Usage Examples
async def use_public_api():
    """Example using public API for business operations."""
    async with LLMClient(api_key="your-api-key") as client:
        # Business operations
        summary = await client.summarize("Your long text here...", max_length=150)
        sentiment = await client.analyze_sentiment("I love this product!")
        operations = await client.get_operations()
        
        print(f"Summary: {summary}")
        print(f"Sentiment: {sentiment}")
        print(f"Available operations: {len(operations['operations'])}")

async def monitor_infrastructure():
    """Example using internal API for infrastructure monitoring."""
    async with LLMClient(api_key="your-api-key") as client:
        # Infrastructure monitoring
        health = await client.get_system_health()
        metrics = await client.get_resilience_metrics()
        cache_stats = await client.get_cache_stats()
        
        print(f"System Status: {health['status']}")
        print(f"Cache Hit Rate: {cache_stats.get('hit_rate', 0):.2%}")
        print(f"Total Requests: {health['metrics']['total_requests']}")
        
        # Validate configuration
        test_config = {"retry_attempts": 3, "circuit_breaker_threshold": 5}
        validation = await client.validate_resilience_config(test_config)
        print(f"Config Valid: {validation['is_valid']}")
```

## 🎨 Frontend Integration

### Streamlit Interface

The frontend provides an intuitive web interface:

1. **Text Input Area** - Enter or paste text to process
2. **Operation Selection** - Choose from available operations
3. **Options Configuration** - Set operation-specific parameters
4. **Results Display** - View processed results with formatting
5. **History Tracking** - Review previous operations

### Custom Frontend Integration

Integrate with your own frontend:

```javascript
// JavaScript example for web integration
class LLMAPIClient {
    constructor(baseURL = 'http://localhost:8000') {
        this.baseURL = baseURL;
    }
    
    async processText(text, operation, options = {}, question = null) {
        const payload = { text, operation, options };
        if (question) payload.question = question;
        
        const response = await fetch(`${this.baseURL}/process`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(payload)
        });
        
        if (!response.ok) {
            throw new Error(`API Error: ${response.status}`);
        }
        
        return await response.json();
    }
    
    async getOperations() {
        const response = await fetch(`${this.baseURL}/operations`);
        return await response.json();
    }
}

// Usage
const client = new LLMAPIClient();

client.processText(
    "Your text here",
    "summarize",
    { max_length: 100 }
).then(result => {
    console.log('Summary:', result.result);
});
```

## 🔧 Custom Operations

### Adding New Operations

Follow these steps to add custom text processing operations:

#### 1. Extend the Models
```python
# shared/models.py
class TextProcessingOperation(str, Enum):
    SUMMARIZE = "summarize"
    SENTIMENT = "sentiment"
    KEY_POINTS = "key_points"
    QUESTIONS = "questions"
    QA = "qa"
    
    # New custom operations
    TRANSLATE = "translate"
    CLASSIFY = "classify"
```

#### 2. Implement Processing Logic
```python
# backend/app/services/text_processor.py
async def _translate_text(self, text: str, options: Dict[str, Any]) -> str:
    """Translate text to target language."""
    target_language = options.get("target_language", "Spanish")
    
    prompt = f"""
    Translate the following text to {target_language}:
    
    Text: {text}
    
    Translation:
    """
    
    result = await self.agent.run(prompt)
    return result.data.strip()

# Add to process_text method
elif request.operation == TextProcessingOperation.TRANSLATE:
    result = await self._translate_text(request.text, request.options)
```

#### 3. Update API Endpoints
```python
# backend/app/main.py
@app.get("/operations")
async def get_operations():
    return {
        "operations": [
            # ... existing operations ...
            {
                "id": "translate",
                "name": "Translate",
                "description": "Translate text to another language",
                "options": ["target_language"]
            }
        ]
    }
```

#### 4. Enhance Frontend
```python
# frontend/app/app.py
if operation == "translate":
    options["target_language"] = st.selectbox(
        "Target Language",
        ["Spanish", "French", "German", "Italian"],
        key="target_language"
    )
```

### Example Custom Operations

See `examples/custom_operation.py` for complete implementation examples of:
- 🌐 Text Translation
- 📊 Text Classification  
- 🏷️ Named Entity Extraction
- 📖 Readability Analysis

## 🧪 Testing & Validation

### Running Tests

The project now includes enhanced testing with automatic virtual environment management:

```bash
# Setup and run all tests (recommended)
make install     # Create virtual environment and install dependencies
make test        # Run all tests (includes Docker integration if available)
make test-local  # Run tests without Docker dependency

# Individual test suites
make test-backend   # Backend tests only
make test-frontend  # Frontend tests only
make test-coverage  # Tests with coverage report

# Code quality
make lint        # Code quality checks
make format      # Format code

# Manual testing
cd examples
.venv/bin/python basic_usage.py  # Using virtual environment

# Run comprehensive integration tests
.venv/bin/python integration_test.py

# Manual unit tests with virtual environment
cd backend
../.venv/bin/python -m pytest

cd ../frontend
../.venv/bin/python -m pytest
```

### Test Coverage

The integration tests cover:
- ✅ API health and availability
- ✅ All text processing operations
- ✅ Error handling scenarios
- ✅ Performance benchmarks
- ✅ Concurrent request handling

### Custom Test Scenarios

```python
# Add your own test scenarios
async def test_custom_scenario():
    async with httpx.AsyncClient() as client:
        # Test with your specific use case
        response = await client.post(
            "http://localhost:8000/process",
            json={
                "text": "Your specific test text",
                "operation": "your_operation"
            }
        )
        
        assert response.status_code == 200
        result = response.json()
        assert result["success"] is True
        # Add your specific assertions
```

## 🚀 Deployment

### Docker Deployment

```bash
# Build and run with Docker Compose
docker-compose up --build

# Production deployment
docker-compose -f docker-compose.prod.yml up -d
```

### Manual Deployment

```bash
# Backend
cd backend
gunicorn app.main:app -w 4 -k uvicorn.workers.UvicornWorker

# Frontend
cd frontend
streamlit run app/app.py --server.port 8501
```

### Environment Variables for Production

```env
# Production settings
DEBUG=false
LOG_LEVEL=WARNING
ALLOWED_ORIGINS=["https://yourdomain.com"]
GEMINI_API_KEY=your_production_key
```

## 🔍 Troubleshooting

### Common Issues

#### 1. API Connection Issues
```
Error: Connection refused to localhost:8000
```
**Solutions:**
- Ensure backend is running: `python -m uvicorn app.main:app --reload`
- Check both API endpoints:
  - Public API: `curl http://localhost:8000/v1/health`
  - Internal API: `curl http://localhost:8000/internal/health -H "X-API-Key: your-key"`
- Check port availability: `lsof -i :8000`
- Verify firewall settings

#### 2. Authentication Issues
```
Error: 401 Unauthorized
```
**Solutions:**
- Set `API_KEY` environment variable
- Include `X-API-Key` header in requests to internal API
- Verify API key format (no extra whitespace)
- Check `ADDITIONAL_API_KEYS` for multi-key setup

#### 3. Resilience Configuration Issues
```
Error: Invalid resilience configuration
```
**Solutions:**
- Set `RESILIENCE_PRESET` environment variable (`simple`, `development`, or `production`)
- Validate custom configuration:
  ```bash
  curl -X POST http://localhost:8000/internal/resilience/validate \
    -H "X-API-Key: your-key" \
    -H "Content-Type: application/json" \
    -d '{"configuration": {"retry_attempts": 3}}'
  ```
- Check configuration health:
  ```bash
  curl http://localhost:8000/internal/resilience/config/health-check \
    -H "X-API-Key: your-key"
  ```

#### 4. Cache Issues
```
Error: Redis connection failed
```
**Solutions:**
- Redis is optional - the application automatically falls back to memory cache
- Check Redis connection: `docker-compose exec redis redis-cli ping`
- Verify `REDIS_URL` environment variable
- Monitor cache performance:
  ```bash
  curl http://localhost:8000/internal/cache/stats \
    -H "X-API-Key: your-key"
  ```

#### 5. AI Model Issues
```
Error: AI model not available
```
**Solutions:**
- Set `GEMINI_API_KEY` environment variable
- Verify API key validity with Google AI Studio
- Check internet connectivity
- Monitor resilience metrics for AI service failures:
  ```bash
  curl http://localhost:8000/internal/resilience/metrics \
    -H "X-API-Key: your-key"
  ```

#### 6. Frontend Issues
```
Error: Streamlit app won't start
```
**Solutions:**
- Install dependencies: `pip install -r requirements.txt`
- Check Python version (3.8+)
- Clear Streamlit cache: `streamlit cache clear`
- Verify backend API connectivity from frontend

#### 7. Performance Issues
```
Error: Request timeout / Circuit breaker open
```
**Solutions:**
- Check resilience patterns are working:
  ```bash
  curl http://localhost:8000/internal/resilience/circuit-breakers \
    -H "X-API-Key: your-key"
  ```
- Reset circuit breakers if needed:
  ```bash
  curl -X POST http://localhost:8000/internal/resilience/circuit-breakers/ai_service/reset \
    -H "X-API-Key: your-key"
  ```
- Monitor system performance:
  ```bash
  curl http://localhost:8000/internal/monitoring/metrics \
    -H "X-API-Key: your-key"
  ```
- Adjust resilience preset for your environment:
  ```bash
  export RESILIENCE_PRESET=production  # For higher reliability
  export RESILIENCE_PRESET=development  # For faster feedback
  ```

### Debug Mode

Enable comprehensive debugging:

```python
import logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
```

### Health Monitoring

Monitor system health with dual-API endpoints:

```bash
# Check Public API health (basic)
curl http://localhost:8000/v1/health

# Check Internal API health (comprehensive)
curl http://localhost:8000/internal/health \
  -H "X-API-Key: your-api-key"

# Monitor resilience system
curl http://localhost:8000/internal/resilience/health \
  -H "X-API-Key: your-api-key"

# Check cache performance
curl http://localhost:8000/internal/cache/stats \
  -H "X-API-Key: your-api-key"

# Get system metrics
curl http://localhost:8000/internal/monitoring/metrics \
  -H "X-API-Key: your-api-key"

# Monitor logs with filtering
tail -f backend/logs/app.log | grep -E "(ERROR|WARNING|resilience|circuit|retry)"

# Check resource usage
htop

# Monitor Docker containers
docker-compose ps
docker stats
```

## 📚 Additional Resources

### Documentation
- **Public API Documentation:** http://localhost:8000/docs
- **Internal API Documentation:** http://localhost:8000/internal/docs (disable in production)
- **Architecture Guide:** `docs/architecture-design/INFRASTRUCTURE_VS_DOMAIN.md`
- **Testing Guide:** `docs/development/TESTING.md`
- **Deployment Guide:** `docs/deployment/DEPLOYMENT.md`
- **Resilience Configuration:** `docs/infrastructure/RESILIENCE_CONFIG.md`
- **Cache Guide:** `docs/infrastructure/CACHE.md`
- **Security Guide:** `docs/infrastructure/SECURITY.md`
- **Examples:** `examples/README.md`
- **Docker Guide:** `docs/deployment/DOCKER.md`

### Community & Support
- **Issues:** GitHub Issues
- **Discussions:** GitHub Discussions
- **Contributing:** `CONTRIBUTING.md`

### Learning Resources
- **FastAPI:** https://fastapi.tiangolo.com/
- **Streamlit:** https://streamlit.io/
- **Gemini API:** https://ai.google.dev/

## 🎯 Next Steps

After completing this integration guide:

1. **Explore Examples:** Run all examples in the `examples/` directory
2. **Customize Operations:** Add your own text processing operations
3. **Deploy to Production:** Use Docker or manual deployment
4. **Monitor Performance:** Set up logging and monitoring
5. **Scale as Needed:** Add load balancing and caching

## 🤝 Contributing

We welcome contributions! Please:

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Update documentation
5. Submit a pull request

## 📄 License

This project is licensed under the MIT License. See `LICENSE` file for details.

## Related Documentation

### Prerequisites
*No prerequisites - this is the starting point for the template.*

### Related Topics
- **[Installation Checklist](./CHECKLIST.md)**: Step-by-step checklist for quick setup verification and troubleshooting
- **[Template Customization](../guides/get-started/TEMPLATE_CUSTOMIZATION.md)**: Understanding the architecture for stability and easy customization

### Next Steps
- **[FastAPI Backend Guide](../guides/application/BACKEND.md)**: Deep dive into backend architecture, API endpoints, and development patterns
- **[Streamlit Frontend Guide](../guides/application/FRONTEND.md)**: Comprehensive frontend development with modern Streamlit patterns
- **[Testing Guide](../guides/developer/TESTING.md)**: Complete testing strategies for backend and frontend components
- **[API Documentation](../guides/application/API.md)**: Detailed API reference for public and internal endpoints
- **[Authentication Guide](../guides/developer/AUTHENTICATION.md)**: Multi-key authentication system configuration and usage

---

**🎉 Congratulations!** You now have a complete understanding of the FastAPI-Streamlit-LLM Starter Template. Start building amazing AI-powered applications! 