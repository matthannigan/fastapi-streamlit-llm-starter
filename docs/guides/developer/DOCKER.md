# Docker Setup & Usage

This project includes a comprehensive Docker setup for both development and production environments with simplified dependency management using pip for containerized builds.

## Architecture

The Docker setup includes the following services:

- **Backend**: FastAPI application with dual-API architecture and AI text processing capabilities
- **Frontend**: Streamlit web interface with async API communication
- **Redis**: AI response caching with graceful degradation and performance monitoring
- **Nginx**: Reverse proxy and load balancer (production only)

## Dependency Management Strategy

**Docker builds use pip instead of Poetry for simplified dependency management:**

- **Local Development**: Poetry for dependency management and virtual environments
- **Docker Containers**: pip with `requirements.docker.txt` files for simplified builds
- **Shared Library**: Automatically installed as editable package (`-e file:./shared`)

This approach eliminates Poetry workspace dependency complexity in Docker builds while maintaining Poetry benefits for local development.

## Poetry vs pip Strategy

### Why pip for Docker?

**Poetry Challenges in Docker**:
- Complex workspace dependencies with shared libraries
- Lock file synchronization issues between host and container
- Mixed Poetry/setuptools dependency resolution conflicts
- Increased build complexity and longer build times

**pip Benefits for Docker**:
- Simple, reliable dependency installation
- Direct editable installs for shared libraries (`-e file:./shared`)
- Consistent behavior across different environments
- Faster, more predictable builds

### Development Workflow

```bash
# Local development - use Poetry for dependency management
poetry install
poetry add new-package

# Docker development - dependencies automatically handled
make dev

# Update Docker requirements when adding dependencies
# (requirements.docker.txt files are maintained manually)
```

### File Structure
```
├── backend/
│   ├── Dockerfile              # Uses pip + requirements.docker.txt
│   ├── pyproject.toml          # Poetry for local development
│   ├── poetry.lock            # Poetry lock file
│   └── requirements.docker.txt # Docker-specific requirements
├── frontend/
│   ├── Dockerfile              # Uses pip + requirements.docker.txt
│   ├── pyproject.toml          # Poetry for local development
│   └── requirements.docker.txt # Docker-specific requirements
└── shared/
    ├── pyproject.toml          # setuptools (not Poetry)
    └── README.md               # Required for setuptools build
```

## Quick Start

### Development Environment

```bash
# Start development environment with hot reloading
make dev

# Or manually:
docker-compose -f docker-compose.yml -f docker-compose.dev.yml up --build
```

### Production Environment

```bash
# Start production environment
make prod

# Or manually:
docker-compose -f docker-compose.yml -f docker-compose.prod.yml up -d --build
```

## Environment Variables

Create a `.env` file in the root directory. For complete configuration details, see [`docs/get-started/ENVIRONMENT_VARIABLES.md`](../../get-started/ENVIRONMENT_VARIABLES.md).

### Essential Docker Configuration:

```env
# Authentication Configuration
AUTH_MODE=simple                      # "simple" or "advanced"
API_KEY=your-secure-api-key-here      # Primary API key
ADDITIONAL_API_KEYS=key1,key2,key3    # Optional additional keys

# Resilience Configuration (simplified preset-based)
RESILIENCE_PRESET=development         # Choose: "simple", "development", "production"

# Cache Configuration (simplified preset-based)
CACHE_PRESET=development              # Choose: "disabled", "minimal", "simple", "development", "production", "ai-development", "ai-production"

# AI Configuration
GEMINI_API_KEY=your_gemini_api_key_here
AI_MODEL=gemini-2.5-flash-lite
AI_TEMPERATURE=0.7

# Application Configuration
DEBUG=true
LOG_LEVEL=INFO
SHOW_DEBUG_INFO=false
MAX_TEXT_LENGTH=10000

# Infrastructure Configuration (Docker-specific paths)
REDIS_URL=redis://redis:6379
CACHE_REDIS_URL=redis://redis:6379
CORS_ORIGINS=["http://localhost:8501", "http://frontend:8501"]

# Security Configuration (Production)
DISABLE_INTERNAL_DOCS=false          # Set to true in production
```

### Cache Preset Options:
- **`disabled`**: No caching
- **`minimal`**: Memory-only cache with basic settings
- **`simple`**: Memory cache with moderate TTLs
- **`development`**: Memory + Redis fallback, short TTLs for testing
- **`production`**: Redis-first with memory fallback, optimized TTLs
- **`ai-development`**: AI-optimized settings for development
- **`ai-production`**: AI-optimized settings for production

## Available Commands

Use the Makefile for easy Docker management:

### Development & Production:
```bash
make help              # Show all available commands
make dev               # Start development environment with hot reload
make prod              # Start production environment
make restart           # Restart all Docker services
make stop              # Stop all services
```

### Docker Operations:
```bash
make docker-build      # Build all Docker images
make docker-up         # Start services with Docker Compose
make docker-down       # Stop and remove Docker services
```

### Service Management:
```bash
make status            # Show status of all services
make health            # Check health of all services
make logs              # Show logs for all services
make backend-logs      # Show backend container logs
make frontend-logs     # Show frontend container logs
```

### Container Access:
```bash
make backend-shell     # Get shell access to backend container
make frontend-shell    # Get shell access to frontend container
make redis-cli         # Open Redis command line interface
```

### Data Management:
```bash
make backup            # Backup Redis data with timestamp
make restore BACKUP=filename  # Restore Redis data from backup
```

### Configuration Management:
```bash
make list-resil-presets        # List available resilience presets
make show-resil-preset PRESET=simple  # Show preset details
make validate-resil-config     # Validate current resilience configuration
make list-cache-presets        # List available cache presets
make show-cache-preset PRESET=development  # Show cache preset details
make validate-cache-config     # Validate current cache configuration
```

## Service Details

### Backend (FastAPI)

- **Port**: 8000
- **Health Check**: `http://localhost:8000/v1/health`
- **API Documentation**:
  - Public API: `http://localhost:8000/docs` (dual-API architecture)
  - Internal API: `http://localhost:8000/internal/docs` (dev only)
- **Key Features**:
  - **Dual-API Architecture**: Public (`/v1/`) and Internal (`/internal/`) endpoints
  - **Preset-based Configuration**: Simplified resilience and cache management
  - **Multi-mode Authentication**: Simple and advanced modes with security features
  - **AI Infrastructure**: PydanticAI integration with Gemini models
  - **Resilience Patterns**: Circuit breakers, retry logic, graceful degradation
  - **Cache Infrastructure**: Redis with memory fallback and performance monitoring
- **Docker Build**:
  - **Dependency Management**: pip with `requirements.docker.txt`
  - **Shared Library**: Automatically installed as editable package
  - **Multi-stage Build**: Separate development/production stages
  - **Hot Reloading**: Development mode with uvicorn auto-reload

### Frontend (Streamlit)

- **Port**: 8501
- **Health Check**: `http://localhost:8501/_stcore/health`
- **Key Features**:
  - **Production-ready UI**: Modern interface patterns for AI applications
  - **Async API Communication**: Proper timeout and error handling for backend calls
  - **Real-time Monitoring**: API health checks with visual indicators
  - **Dynamic Configuration**: Backend-driven UI generation
  - **Session State Management**: Stateful user interactions with persistence
- **Docker Build**:
  - **Dependency Management**: pip with `requirements.docker.txt`
  - **Shared Library**: Automatically installed as editable package
  - **Hot Reloading**: File watching for development
  - **WebSocket Support**: Real-time updates and notifications

### Redis

- **Port**: 6379
- **Key Features**:
  - **AI Response Caching**: Optimized cache with compression and graceful degradation
  - **Preset-based Configuration**: Simplified cache management via `CACHE_PRESET`
  - **Fallback Support**: Automatic fallback to in-memory cache if Redis unavailable
  - **Performance Monitoring**: Built-in cache metrics and performance tracking
  - **Data Persistence**: Redis data survives container restarts
  - **Backup/Restore**: Automated backup with timestamp and restore capabilities

### Nginx (Production Only)

- **Ports**: 80, 443
- **Features**:
  - Reverse proxy for backend and frontend
  - Rate limiting
  - Security headers
  - WebSocket support for Streamlit
  - SSL/TLS termination ready

## Development vs Production

### Development Features (`make dev`):
- **Hot Reloading**: uvicorn auto-reload for backend, Streamlit file watching for frontend
- **Debug Mode**: Detailed logging and error messages
- **Volume Mounts**: Live code editing with immediate reflection
- **Full Dependencies**: All development and testing dependencies included
- **Internal API Access**: `/internal/docs` available for debugging
- **Configuration**: `CACHE_PRESET=development`, `RESILIENCE_PRESET=development`

### Production Features (`make prod`):
- **Optimized Builds**: Minimal dependencies, multi-stage builds for smaller images
- **Security Hardening**: Non-root users, no debug information exposure
- **Performance Tuning**: Resource limits, optimized configurations
- **Infrastructure**: Nginx reverse proxy, SSL/TLS termination ready
- **Monitoring**: Health checks, performance metrics, structured logging
- **Configuration**: `CACHE_PRESET=production`, `RESILIENCE_PRESET=production`

## Networking

All services communicate through a custom Docker network (`llm-starter-network`) for:
- Service discovery
- Network isolation
- Improved security

## Health Monitoring

Each service includes comprehensive health checks:
- **Backend**: HTTP health endpoint
- **Frontend**: Streamlit health endpoint
- **Redis**: Redis ping command
- **Nginx**: Depends on backend/frontend health

## Scaling

The production setup supports horizontal scaling:
- Backend: 3 replicas with resource limits
- Frontend: 2 replicas with resource limits
- Redis: Single instance with persistent storage

## Security Features

- Non-root users in production containers
- Security headers via Nginx
- Rate limiting
- Network isolation
- No volume mounts in production

## Troubleshooting

### Common Issues

#### 1. Shared Library Dependency Issues
**Problem**: Build fails with shared library path errors
**Solution**: The project now uses pip instead of Poetry for Docker builds
- Docker builds use `requirements.docker.txt` with `-e file:./shared`
- Local development continues to use Poetry
- This eliminates workspace dependency complexity

#### 2. Port Conflicts
**Problem**: Ports 8000, 8501, or 6379 already in use
**Solution**:
```bash
# Check what's using the ports
lsof -i :8000 -i :8501 -i :6379

# Stop conflicting services or use different ports in .env
BACKEND_PORT=8001
FRONTEND_PORT=8502
REDIS_PORT=6380
```

#### 3. Cache Configuration Issues
**Problem**: Redis connection errors or cache misses
**Solution**:
```bash
# Validate cache configuration
make validate-cache-config

# Check available cache presets
make list-cache-presets

# Use development preset for local work
CACHE_PRESET=development
```

### Diagnostic Commands

#### Check service status:
```bash
make status             # Container status
make health             # Health check results
make logs               # All service logs
```

#### Access services:
```bash
make backend-shell      # Backend container shell
make frontend-shell     # Frontend container shell
make redis-cli          # Redis command line
```

#### Test endpoints:
```bash
# Test health endpoints
curl http://localhost:8000/v1/health
curl http://localhost:8501/_stcore/health

# Test monitoring endpoints
curl http://localhost:8000/internal/monitoring/overview
curl http://localhost:8000/internal/cache/stats

# Test API with authentication
curl -H "Authorization: Bearer your-api-key" \
     -H "Content-Type: application/json" \
     -d '{"text":"Test","operation":"summarize"}' \
     http://localhost:8000/v1/text_processing/process
```

### Clean Up Commands

```bash
make docker-down        # Stop and remove containers
make clean              # Clean Python cache files
docker system prune -a  # Clean all Docker resources (use carefully)
docker volume prune     # Remove unused volumes
```

## SSL/TLS Setup (Production)

To enable HTTPS in production:

1. Place SSL certificates in `nginx/ssl/`
2. Update `nginx/nginx.conf` to include SSL configuration
3. Restart the nginx service

## Monitoring and Logging

### Built-in Monitoring Endpoints
- **System Health**: `http://localhost:8000/v1/health`
- **Internal Monitoring**: `http://localhost:8000/internal/monitoring/overview`
- **Resilience Status**: `http://localhost:8000/internal/resilience/health`
- **Cache Statistics**: `http://localhost:8000/internal/cache/stats`
- **Frontend Health**: `http://localhost:8501/_stcore/health`

### Configuration Validation
```bash
# Validate resilience configuration
make validate-resil-config
make list-resil-presets

# Validate cache configuration
make validate-cache-config
make list-cache-presets
```

### Logging Features
- **Structured Logging**: JSON-formatted logs across all services
- **Service Discovery**: Automatic health check integration
- **Performance Metrics**: Cache hit rates, response times, circuit breaker status
- **Data Persistence**: Redis data and logs survive container restarts
- **Real-time Monitoring**: Live health status updates

## Performance Optimization

### Docker Build Optimization
- **Multi-stage Builds**: Separate development/production stages reduce image size
- **pip vs Poetry**: Simplified dependency resolution eliminates Poetry workspace complexity
- **Layer Caching**: Optimized Dockerfile layer ordering for faster rebuilds
- **Shared Library**: Editable install (`-e file:./shared`) enables efficient development

### Runtime Performance
- **Preset-based Configuration**: Simplified cache and resilience management
- **Redis Caching**: AI response caching with automatic fallback to memory
- **Connection Pooling**: Optimized Redis and HTTP connection management
- **Circuit Breakers**: Automatic protection against cascading failures
- **Resource Limits**: Prevents resource exhaustion in production

## Related Documentation

### Prerequisites
- **[Complete Setup Guide](../../get-started/SETUP_INTEGRATION.md)**: Basic understanding of the template structure and components
- **[Environment Variables](../../get-started/ENVIRONMENT_VARIABLES.md)**: Complete configuration reference

### Configuration & Infrastructure
- **[Cache Infrastructure](../infrastructure/CACHE.md)**: Redis caching and preset configuration
- **[Resilience Infrastructure](../infrastructure/RESILIENCE.md)**: Circuit breakers and retry patterns
- **[Monitoring Infrastructure](../infrastructure/MONITORING.md)**: Health checks and performance metrics

### Development & Testing
- **[Virtual Environment Guide](./VIRTUAL_ENVIRONMENT_GUIDE.md)**: Alternative local development without Docker
- **[Testing Guide](../testing/TESTING.md)**: Docker-based testing environments and strategies
- **[Backend Guide](../BACKEND.md)**: FastAPI service architecture and implementation
- **[Frontend Guide](../FRONTEND.md)**: Streamlit application and async patterns

### Production & Deployment
- **[Deployment Guide](../DEPLOYMENT.md)**: Production deployment using Docker and container orchestration
- **[Code Standards](./CODE_STANDARDS.md)**: Development standards and architectural guidelines 