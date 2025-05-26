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
         │                       │                       │
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

# Development environment (with hot reload)
make dev

# Production environment (with scaling and nginx)
make prod

# Check service status
make status

# View logs
make logs

# Health check all services
make health

# Clean up
make clean
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

### Available Operations

1. **Summarize**: Generate concise summaries of long texts
2. **Sentiment Analysis**: Analyze emotional tone and confidence
3. **Key Points**: Extract main points from content
4. **Question Generation**: Create questions about the text
5. **Q&A**: Answer specific questions about the content

### Example API Usage

```python
import httpx

# Process text
response = httpx.post("http://localhost:8000/process", json={
    "text": "Your text here...",
    "operation": "summarize",
    "options": {"max_length": 100}
})

result = response.json()
print(result["result"])
```

### Frontend Features

- **File Upload**: Support for .txt and .md files
- **Real-time Processing**: Live progress indicators
- **Rich Results**: Formatted output with metrics
- **Download Results**: Export results as JSON
- **Example Content**: Built-in examples for testing

## 🛠️ Development

### Local Development Setup

```bash
# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -r backend/requirements.txt
pip install -r frontend/requirements.txt

# Start backend
cd backend
uvicorn app.main:app --reload

# Start frontend (new terminal)
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

```bash
# Run all tests
make test

# Run backend tests only
docker-compose exec backend python -m pytest

# Run with coverage
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
```

### Create `docs/API.md`:

```markdown
# API Documentation

## Overview

The AI Text Processor API provides endpoints for processing text using various AI models.

## Base URL

- **Development**: `http://localhost:8000`
- **Production**: `https://your-domain.com/api`

## Authentication

Currently, no authentication is required. In production, consider adding API key authentication.

## Endpoints

### Health Check

**GET** `/health`

Check if the API is running and AI models are available.

**Response:**
```json
{
  "status": "healthy",
  "timestamp": "2024-01-01T12:00:00Z",
  "version": "1.0.0",
  "ai_model_available": true
}
```

### Get Operations

**GET** `/operations`

Get list of available text processing operations.

**Response:**
```json
{
  "operations": [
    {
      "id": "summarize",
      "name": "Summarize",
      "description": "Generate a concise summary of the text",
      "options": ["max_length"]
    }
  ]
}
```

### Process Text

**POST** `/process`

Process text using specified operation.

**Request Body:**
```json
{
  "text": "Your text content here...",
  "operation": "summarize",
  "question": "Optional question for Q&A",
  "options": {
    "max_length": 100
  }
}
```

**Response:**
```json
{
  "operation": "summarize",
  "success": true,
  "result": "Summary of the text...",
  "metadata": {
    "word_count": 150
  },
  "processing_time": 2.3,
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## Error Responses

All endpoints return error responses in this format:

```json
{
  "success": false,
  "error": "Error message",
  "error_code": "ERROR_CODE",
  "details": {},
  "timestamp": "2024-01-01T12:00:00Z"
}
```

## Rate Limiting

- API requests: 10 requests per second
- Burst: up to 5 additional requests

## Examples

See `examples/` directory for code samples in various languages.
```

### Create `docs/DEPLOYMENT.md`:

```markdown
# Deployment Guide

## Overview

This guide covers deploying the AI Text Processor to various environments.

## Docker Deployment

### Local Development

```bash
# Start with hot reload
make dev

# Or manually
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up
```

### Production

```bash
# Production deployment
make prod

# Or manually  
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d
```

## Cloud Deployment

### AWS ECS

1. **Build and Push Images**:
```bash
# Build images
docker build -t your-repo/ai-processor-backend ./backend
docker build -t your-repo/ai-processor-frontend ./frontend

# Push to ECR
aws ecr get-login-password | docker login --username AWS --password-stdin your-repo
docker push your-repo/ai-processor-backend
docker push your-repo/ai-processor-frontend
```

2. **Create ECS Task Definition**:
```json
{
  "family": "ai-text-processor",
  "networkMode": "awsvpc",
  "cpu": "1024",
  "memory": "2048",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "your-repo/ai-processor-backend",
      "portMappings": [{"containerPort": 8000, "protocol": "tcp"}],
      "environment": [
        {"name": "GEMINI_API_KEY", "value": "your-key"}
      ]
    }
  ]
}
```

### Google Cloud Run

```bash
# Build and deploy backend
gcloud builds submit --tag gcr.io/PROJECT-ID/ai-processor-backend ./backend
gcloud run deploy ai-processor-backend \
  --image gcr.io/PROJECT-ID/ai-processor-backend \
  --platform managed \
  --set-env-vars GEMINI_API_KEY=your-key

# Build and deploy frontend
gcloud builds submit --tag gcr.io/PROJECT-ID/ai-processor-frontend ./frontend  
gcloud run deploy ai-processor-frontend \
  --image gcr.io/PROJECT-ID/ai-processor-frontend \
  --platform managed \
  --set-env-vars API_BASE_URL=https://your-backend-url
```

### Kubernetes

See `k8s/` directory for Kubernetes manifests.

## Environment Variables

| Variable | Required | Description |
|----------|----------|-------------|
| `GEMINI_API_KEY` | Yes | Google Gemini API key |
| `AI_MODEL` | No | Model name (default: gemini-2.0-flash-exp) |
| `DEBUG` | No | Enable debug mode (default: false) |

## SSL/HTTPS

### Let's Encrypt with Nginx

```bash
# Install certbot
sudo apt-get install certbot python3-certbot-nginx

# Get certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

## Monitoring

### Health Checks

Both services include health check endpoints:
- Backend: `http://localhost:8000/health`
- Frontend: `http://localhost:8501/_stcore/health`

### Logging

Logs are available via Docker:
```bash
# View all logs
docker-compose logs -f

# Service-specific logs
docker-compose logs -f backend
docker-compose logs -f frontend
```

## Backup and Recovery

### Database Backup (if using)

```bash
# Backup database
docker-compose exec postgres pg_dump -U postgres dbname > backup.sql

# Restore database
docker-compose exec postgres psql -U postgres dbname < backup.sql
```

### Configuration Backup

```bash
# Backup environment and configuration
tar -czf backup-$(date +%Y%m%d).tar.gz .env docker-compose.yml nginx/
```

## Security Considerations

1. **API Keys**: Store in environment variables, not code
2. **HTTPS**: Always use HTTPS in production
3. **Rate Limiting**: Configure appropriate limits
4. **CORS**: Restrict to necessary origins
5. **Updates**: Keep dependencies updated

## Scaling

### Horizontal Scaling

```bash
# Scale backend instances
docker-compose up -d --scale backend=3

# Scale with load balancer
# Update nginx configuration for upstream servers
```

### Vertical Scaling

Update resource limits in `docker-compose.prod.yml`:

```yaml
deploy:
  resources:
    limits:
      cpus: '2'
      memory: 4G
```

## Troubleshooting

### Common Issues

1. **Out of Memory**: Increase memory limits
2. **High CPU**: Scale horizontally or increase CPU limits
3. **Network Issues**: Check security groups and firewall rules
4. **SSL Issues**: Verify certificate installation and renewal

### Debug Commands

```bash
# Check container status
docker-compose ps

# View resource usage
docker stats

# Access container
docker-compose exec backend bash

# Test API
curl -X POST http://localhost:8000/process \
  -H "Content-Type: application/json" \
  -d '{"text":"test","operation":"summarize"}'
```

## 🚀 Complete Setup Checklist

### 1. Initial Setup
- [ ] Clone the repository
- [ ] Copy `.env.example` to `.env`
- [ ] Add your AI API keys to `.env`
- [ ] Ensure Docker and Docker Compose are installed

### 2. Development Setup
```bash
# Quick start
git clone <your-repo>
cd fastapi-streamlit-llm-starter
cp .env.example .env
# Edit .env with your API keys
make dev
```

### 3. Production Deployment
```bash
# Production deployment
cp .env.example .env.prod
# Edit .env.prod with production settings
make prod
```

### 4. Verify Installation
- [ ] Backend health: http://localhost:8000/health
- [ ] Frontend app: http://localhost:8501  
- [ ] API docs: http://localhost:8000/docs
- [ ] Run example: `python examples/basic_usage.py`

### 5. Customization
- [ ] Add your custom AI operations
- [ ] Customize the UI theme and branding
- [ ] Add authentication if needed
- [ ] Configure monitoring and logging
- [ ] Set up CI/CD pipeline

## 🎯 Next Steps

After setting up the starter template:

1. **Customize for Your Use Case**
   - Replace the example text operations with your specific AI functionality
   - Modify the UI to match your application's needs
   - Add domain-specific prompts and AI configurations

2. **Add Production Features**
   - User authentication and authorization
   - Rate limiting and usage tracking
   - Error monitoring and alerting
   - Database integration for user data
   - Caching for improved performance

3. **Scale Your Application**
   - Load balancing with multiple backend instances
   - Database clustering for high availability
   - CDN for static assets
   - Auto-scaling based on demand

4. **Monitor and Optimize**
   - Application performance monitoring
   - Cost tracking for AI API usage
   - User analytics and feedback collection
   - A/B testing for UI improvements

## 🔧 Troubleshooting

**Common Issues:**

1. **CORS errors in browser**
   - Check `ALLOWED_ORIGINS` in backend configuration
   - Ensure frontend URL is included in CORS settings

2. **AI API rate limiting**
   - Implement request queuing
   - Add retry logic with exponential backoff
   - Monitor API usage and set appropriate limits

3. **Docker issues**
   - Ensure sufficient disk space and memory
   - Check port availability (8000, 8501)
   - Verify environment variables are properly set

4. **Performance issues**
   - Monitor resource usage with `docker stats`
   - Optimize AI prompts for faster responses
   - Implement caching for repeated requests

**Debug Commands:**
```bash
# View logs
make logs

# Check service status
docker-compose ps

# Run tests
make test

# Access container shell
make backend-shell
make frontend-shell
```

## 📚 Additional Resources

- **FastAPI Documentation**: https://fastapi.tiangolo.com/
- **Streamlit Documentation**: https://docs.streamlit.io/
- **PydanticAI Documentation**: https://ai.pydantic.dev/
- **Docker Documentation**: https://docs.docker.com/
- **AI Model APIs**: 
  - Google Gemini: https://ai.google.dev/
  - OpenAI: https://platform.openai.com/docs
  - Anthropic Claude: https://docs.anthropic.com/

## 🤝 Contributing

We welcome contributions! Please see our contributing guidelines:

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see LICENSE file for details.
