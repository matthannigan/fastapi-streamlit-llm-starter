# Docker Setup & Usage

This project includes a comprehensive Docker setup for both development and production environments.

## Architecture

The Docker setup includes the following services:

- **Backend**: FastAPI application with AI text processing capabilities
- **Frontend**: Streamlit web interface
- **Redis**: Caching and session storage
- **Nginx**: Reverse proxy and load balancer (production only)

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

Create a `.env` file in the root directory with the following variables:

```env
# Authentication Configuration
AUTH_MODE=simple                      # "simple" or "advanced"
API_KEY=your-secure-api-key-here      # Primary API key
ADDITIONAL_API_KEYS=key1,key2,key3    # Optional additional keys
ENABLE_USER_TRACKING=false            # Enable user context tracking (advanced mode)
ENABLE_REQUEST_LOGGING=false          # Enable security event logging (advanced mode)

# Resilience Configuration
RESILIENCE_PRESET=development         # "simple", "development", or "production"

# AI Configuration
GEMINI_API_KEY=your_gemini_api_key_here
AI_MODEL=gemini-2.0-flash-exp
AI_TEMPERATURE=0.7

# Application Configuration
DEBUG=true
LOG_LEVEL=INFO
SHOW_DEBUG_INFO=false
MAX_TEXT_LENGTH=10000

# Infrastructure Configuration
REDIS_URL=redis://redis:6379
CORS_ORIGINS=["http://localhost:8501", "http://frontend:8501"]

# Security Configuration (Production)
DISABLE_INTERNAL_DOCS=false          # Set to true in production
```

## Available Commands

Use the Makefile for easy Docker management:

```bash
make help              # Show all available commands
make build             # Build all Docker images
make up                # Start all services
make down              # Stop all services
make dev               # Start development environment
make prod              # Start production environment
make logs              # Show logs for all services
make status            # Show status of all services
make health            # Check health of all services
make clean             # Clean up Docker resources
make test              # Run tests
make restart           # Restart all services
```

### Service-specific commands:

```bash
make backend-shell     # Get shell access to backend container
make frontend-shell    # Get shell access to frontend container
make backend-logs      # Show backend logs
make frontend-logs     # Show frontend logs
make redis-logs        # Show Redis logs
make nginx-logs        # Show Nginx logs
make redis-cli         # Open Redis CLI
```

### Backup and restore:

```bash
make backup            # Backup Redis data
make restore BACKUP=filename  # Restore Redis data
```

## Service Details

### Backend (FastAPI)

- **Port**: 8000
- **Health Check**: `http://localhost:8000/health`
- **API Documentation**:
  - Public API: `http://localhost:8000/docs`
  - Internal API: `http://localhost:8000/internal/docs` (dev only)
- **Features**:
  - **Dual-API Architecture**: Public (`/v1/`) and Internal (`/internal/`) endpoints
  - **Multi-mode Authentication**: Simple and advanced modes with security features
  - **Resilience Patterns**: Circuit breakers, retry logic, graceful degradation
  - **Comprehensive Monitoring**: 38 resilience endpoints across 8 modules
  - **Multi-stage Docker build** (development/production)
  - **Hot reloading** in development
  - **Non-root user** in production

### Frontend (Streamlit)

- **Port**: 8501
- **Health Check**: `http://localhost:8501/_stcore/health`
- **Features**:
  - **Production-ready UI**: Modern interface patterns for AI applications
  - **Authentication Integration**: Support for both simple and advanced auth modes
  - **Real-time Monitoring**: API health checks with visual indicators
  - **Async API Communication**: Proper timeout and error handling for backend calls
  - **Multi-stage Docker build**
  - **Auto-reload** on file changes in development
  - **WebSocket support** for real-time updates

### Redis

- **Port**: 6379
- **Features**:
  - **AI Response Caching**: Optimized cache with compression and graceful degradation
  - **Fallback Support**: System automatically falls back to in-memory cache if Redis unavailable  
  - **Performance Monitoring**: Built-in cache metrics and performance tracking
  - **Persistent data storage**
  - **Health monitoring**
  - **Backup/restore capabilities**

### Nginx (Production Only)

- **Ports**: 80, 443
- **Features**:
  - Reverse proxy for backend and frontend
  - Rate limiting
  - Security headers
  - WebSocket support for Streamlit
  - SSL/TLS termination ready

## Development vs Production

### Development Features:
- Hot reloading for both backend and frontend
- Debug mode enabled
- Volume mounts for live code editing
- Development dependencies included
- Detailed logging

### Production Features:
- Optimized builds without development dependencies
- Non-root users for security
- Resource limits and scaling
- No volume mounts for security
- Nginx reverse proxy
- Health checks and monitoring

## Networking

All services communicate through a custom Docker network (`ai-processor-network`) for:
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

### Check service status:
```bash
make status
make health
```

### View logs:
```bash
make logs                # All services
make backend-logs        # Backend only
make frontend-logs       # Frontend only
```

### Access containers:
```bash
make backend-shell       # Backend container
make frontend-shell      # Frontend container
make redis-cli          # Redis CLI
```

### Test API endpoints:
```bash
# Test health endpoints
curl http://localhost:8000/health
curl http://localhost:8000/internal/monitoring/overview

# Test authentication (replace with your API key)
curl -H "Authorization: Bearer your-api-key" \
     -H "Content-Type: application/json" \
     -d '{"text":"Test","operation":"summarize"}' \
     http://localhost:8000/v1/text_processing/process
```

### Clean up issues:
```bash
make clean              # Remove containers and volumes
docker system prune -a  # Clean all Docker resources
```

## SSL/TLS Setup (Production)

To enable HTTPS in production:

1. Place SSL certificates in `nginx/ssl/`
2. Update `nginx/nginx.conf` to include SSL configuration
3. Restart the nginx service

## Monitoring and Logging

### Built-in Monitoring Endpoints
- **System Health**: `http://localhost:8000/health`
- **Comprehensive Monitoring**: `http://localhost:8000/internal/monitoring/overview`
- **Resilience Status**: `http://localhost:8000/internal/resilience/health`
- **Cache Performance**: `http://localhost:8000/internal/monitoring/cache-stats`

### Features
- **Structured logging** across all services
- **Health checks** provide real-time service status
- **Performance metrics** for cache and resilience patterns
- **Redis data persistence** across container restarts
- **Backup/restore functionality** for Redis data
- **Circuit breaker monitoring** with automatic recovery

## Performance Optimization

- Multi-stage builds reduce image size
- Resource limits prevent resource exhaustion
- Redis caching improves response times
- Nginx load balancing distributes traffic

## Related Documentation

### Prerequisites
- **[Complete Setup Guide](../../get-started/SETUP_INTEGRATION.md)**: Basic understanding of the template structure and components

### Related Topics
- **[Virtual Environment Guide](./VIRTUAL_ENVIRONMENT_GUIDE.md)**: Alternative local development setup without Docker
- **[Testing Guide](../TESTING.md)**: Docker-based testing environments and strategies

### Next Steps
- **[Deployment Guide](../DEPLOYMENT.md)**: Production deployment using Docker and container orchestration
- **[Backend Guide](../BACKEND.md)**: Understanding the backend services being containerized
- **[Frontend Guide](../FRONTEND.md)**: Understanding the frontend services being containerized 