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
# API Configuration
GEMINI_API_KEY=your_gemini_api_key_here
AI_MODEL=gemini-2.0-flash-exp
AI_TEMPERATURE=0.7

# Application Configuration
DEBUG=true
LOG_LEVEL=INFO
SHOW_DEBUG_INFO=false
MAX_TEXT_LENGTH=10000

# Redis Configuration
REDIS_URL=redis://redis:6379

# Network Configuration
ALLOWED_ORIGINS=["http://localhost:8501", "http://frontend:8501"]
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
- **Features**:
  - Multi-stage Docker build (development/production)
  - Hot reloading in development
  - Non-root user in production
  - Comprehensive health checks

### Frontend (Streamlit)

- **Port**: 8501
- **Health Check**: `http://localhost:8501/_stcore/health`
- **Features**:
  - Multi-stage Docker build
  - Auto-reload on file changes in development
  - WebSocket support for real-time updates

### Redis

- **Port**: 6379
- **Features**:
  - Persistent data storage
  - Health monitoring
  - Backup/restore capabilities

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

- All services include structured logging
- Health checks provide service status
- Redis data is persisted across restarts
- Backup/restore functionality for Redis data

## Performance Optimization

- Multi-stage builds reduce image size
- Resource limits prevent resource exhaustion
- Redis caching improves response times
- Nginx load balancing distributes traffic 