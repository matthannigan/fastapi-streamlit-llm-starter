# Get Started Checklist

## 🚀 Installation & Setup

### 1. Initial Setup
- [ ] Clone the repository
- [ ] Install Python 3.8+ and create virtual environment
- [ ] Copy `.env.example` to `.env`
- [ ] Configure authentication and AI API keys in `.env`
- [ ] Ensure Docker and Docker Compose are installed (optional for Docker workflow)

### 2. Development Setup

#### Option A: Makefile Commands (Recommended)
```bash
# Quick start with virtual environment automation
git clone <repository-url>
cd fastapi-streamlit-llm-starter
cp .env.example .env
# Edit .env with your configuration

# Setup and install dependencies
make install

# Run backend (FastAPI)
make run-backend

# Run frontend (Streamlit) - in separate terminal
make install-frontend-local
make run-frontend
```

#### Option B: Docker Workflow
```bash
# Development with Docker
make dev
```

#### Option C: Manual Setup
```bash
# Manual virtual environment setup
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate
pip install -r backend/requirements.txt
cd backend && uvicorn app.main:app --reload --port 8000
```

### 3. Production Deployment

#### Docker Production
```bash
# Production deployment with Docker
cp .env.example .env.prod
# Edit .env.prod with production settings
make prod
```

#### Manual Production
```bash
# Production setup without Docker
export ENVIRONMENT=production
export AUTH_MODE=advanced
export API_KEY=your-secure-production-key
export GEMINI_API_KEY=your-gemini-key

# Backend
cd backend
gunicorn app.main:app --workers 4 --host 0.0.0.0 --port 8000

# Frontend (separate process)
cd frontend
streamlit run app/app.py --server.port 8501
```

### 4. Verify Installation
- [ ] Backend health: http://localhost:8000/health
- [ ] Public API docs: http://localhost:8000/docs
- [ ] Internal API docs: http://localhost:8000/internal/docs
- [ ] Frontend app: http://localhost:8501
- [ ] Test authentication: Use API key in frontend or curl
- [ ] Run backend tests: `make test-backend`
- [ ] Run frontend tests: `make test-frontend`

## 🎯 Next Steps

After setting up the starter template:

### 5. Configure Authentication & Security
- [ ] Set `AUTH_MODE=simple` for basic usage or `AUTH_MODE=advanced` for enhanced features
- [ ] Generate secure API keys: `openssl rand -hex 32`
- [ ] Configure additional API keys for multiple clients if needed
- [ ] Enable user tracking and request logging in advanced mode
- [ ] Test all authentication modes (simple, advanced, development)

### 6. Customize for Your Use Case
- [ ] **Keep Infrastructure Services**: Use cache, resilience, security, monitoring as-is
- [ ] **Replace Domain Services**: Customize `app/services/` with your business logic
- [ ] Replace example text operations with your specific AI functionality
- [ ] Modify the Streamlit UI to match your application's needs
- [ ] Update `shared/models.py` with your data structures
- [ ] Configure resilience presets for your environment

### 7. Production Features Setup
- [ ] **Security**: API keys configured, internal docs disabled in production
- [ ] **Resilience**: Choose appropriate preset (`simple`, `development`, `production`)
- [ ] **Monitoring**: Configure cache and resilience monitoring endpoints
- [ ] **Caching**: Set up Redis or use in-memory cache fallback
- [ ] **Database**: Add user data storage (optional)
- [ ] **CI/CD**: Set up automated testing and deployment pipeline

### 8. Scale Your Application
- [ ] **Load Balancing**: Multiple backend instances behind load balancer
- [ ] **Database**: Clustering for high availability (if using database)
- [ ] **Cache Scaling**: Redis cluster for distributed caching
- [ ] **Auto-scaling**: Container orchestration (Kubernetes, Docker Swarm)
- [ ] **CDN**: Static assets and caching layer

### 9. Monitor and Optimize
- [ ] **Built-in Monitoring**: Use `/internal/monitoring/overview` endpoint
- [ ] **Resilience Metrics**: Monitor circuit breakers and retry patterns
- [ ] **Cache Performance**: Track hit ratios and memory usage
- [ ] **Cost Tracking**: Monitor AI API usage and billing
- [ ] **User Analytics**: Leverage built-in security event logging
- [ ] **Performance**: Use resilience benchmarks and health checks

## 🔧 Troubleshooting

### Common Issues

1. **Authentication errors**
   - Verify `API_KEY` is set in `.env` file  
   - Check API key format (use `Authorization: Bearer <key>` header)
   - Confirm `AUTH_MODE` setting matches your setup
   - Development mode activates automatically when no keys configured

2. **CORS errors in browser**
   - Check `CORS_ORIGINS` in backend configuration
   - Ensure frontend URL is included in CORS settings
   - Verify API endpoints use correct paths (`/v1/` for public, `/internal/` for admin)

3. **AI API issues**
   - Set `GEMINI_API_KEY` in environment variables
   - Monitor resilience patterns - circuit breakers may be activated
   - Check `/internal/resilience/health` for resilience system status
   - Verify resilience preset configuration (`RESILIENCE_PRESET`)

4. **Docker issues**
   - Ensure sufficient disk space and memory
   - Check port availability (8000 for backend, 8501 for frontend)
   - Verify environment variables are properly mounted
   - Check service health with `docker-compose ps`

5. **Performance issues**
   - Monitor cache performance at `/internal/monitoring/overview`
   - Check resilience metrics for retry/circuit breaker activity
   - Use built-in Redis cache or verify in-memory cache fallback
   - Review resilience preset settings for your workload

### Debug Commands

```bash
# Development workflow
make install                    # Setup virtual environment and dependencies
make run-backend               # Start FastAPI development server
make test-backend              # Run backend tests
make lint-backend              # Code quality checks

# Docker workflow
make dev                       # Start development environment
make logs                      # View application logs
docker-compose ps              # Check service status
make backend-shell             # Access backend container
make frontend-shell            # Access frontend container

# Testing and validation
make test-backend-all          # Run all tests including slow ones
make test-coverage             # Run tests with coverage reports
make validate-config           # Validate resilience configuration

# Monitoring and diagnostics
curl http://localhost:8000/health                    # Basic health check
curl http://localhost:8000/internal/monitoring/overview  # System monitoring
curl http://localhost:8000/internal/resilience/health    # Resilience status
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

## Related Documentation

### Prerequisites
*No prerequisites - this checklist can be used independently or alongside other guides.*

### Related Topics
- **[Complete Setup Guide](./SETUP_INTEGRATION.md)**: Comprehensive setup and system integration guide with detailed examples
- **[Virtual Environment Guide](../guides/developer/VIRTUAL_ENVIRONMENT_GUIDE.md)**: Enhanced virtual environment management and setup

### Next Steps
- **[Template Customization](../guides/get-started/TEMPLATE_CUSTOMIZATION.md)**: Understanding architecture for customizing the template for your project
- **[Authentication Guide](../guides/developer/AUTHENTICATION.md)**: Configure multi-key authentication and security modes
- **[Docker Setup](../guides/developer/DOCKER.md)**: Development and production environments with Docker

## 📄 License

This project is licensed under the MIT License - see LICENSE file for details.