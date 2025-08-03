# Deployment Guide

## Overview

This guide covers deploying the FastAPI-Streamlit LLM Starter Template with its dual-API architecture, resilience patterns, and infrastructure services to various environments.

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
        {"name": "RESILIENCE_PRESET", "value": "production"},
        {"name": "GEMINI_API_KEY", "value": "your-gemini-key"},
        {"name": "API_KEY", "value": "your-secure-api-key"},
        {"name": "REDIS_URL", "value": "redis://your-redis-cluster:6379"},
        {"name": "DISABLE_INTERNAL_DOCS", "value": "true"},
        {"name": "LOG_LEVEL", "value": "INFO"},
        {"name": "CORS_ORIGINS", "value": "[\"https://your-frontend-domain.com\"]"}
      ]
    },
    {
      "name": "frontend",
      "image": "your-repo/ai-processor-frontend",
      "portMappings": [{"containerPort": 8501, "protocol": "tcp"}],
      "environment": [
        {"name": "API_BASE_URL", "value": "https://your-backend-url"},
        {"name": "SHOW_DEBUG_INFO", "value": "false"},
        {"name": "INPUT_MAX_LENGTH", "value": "50000"}
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
  --set-env-vars RESILIENCE_PRESET=production,GEMINI_API_KEY=your-gemini-key,API_KEY=your-secure-api-key,DISABLE_INTERNAL_DOCS=true,LOG_LEVEL=INFO

# Build and deploy frontend
gcloud builds submit --tag gcr.io/PROJECT-ID/ai-processor-frontend ./frontend  
gcloud run deploy ai-processor-frontend \
  --image gcr.io/PROJECT-ID/ai-processor-frontend \
  --platform managed \
  --set-env-vars API_BASE_URL=https://your-backend-url,SHOW_DEBUG_INFO=false,INPUT_MAX_LENGTH=50000

# Optional: Deploy Redis for caching (recommended for production)
gcloud run deploy redis-cache \
  --image redis:alpine \
  --platform managed \
  --no-allow-unauthenticated \
  --memory 512Mi
```

## Environment Configuration

### Resilience Configuration (Simplified)

The template uses a preset-based resilience system that replaces 47+ individual environment variables with a single preset choice:

| Environment | Recommended Preset | Configuration |
|-------------|-------------------|---------------|
| **Development/Local** | `development` | Fast-fail, minimal retries, quick recovery |
| **Staging/Testing** | `simple` | Balanced configuration for general use |
| **Production** | `production` | High reliability, maximum retries |

```bash
# Choose one preset based on your environment
export RESILIENCE_PRESET=development  # For local development
export RESILIENCE_PRESET=simple       # For staging/testing
export RESILIENCE_PRESET=production   # For production workloads
```

### Core Environment Variables

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `RESILIENCE_PRESET` | **Recommended** | Resilience configuration preset (`simple`, `development`, `production`) | `simple` |
| `GEMINI_API_KEY` | Yes | Google Gemini API key for AI processing | - |
| `API_KEY` | Yes | Primary API key for authentication | - |
| `ADDITIONAL_API_KEYS` | No | Comma-separated additional API keys | - |
| `AI_MODEL` | No | AI model name | `gemini-2.0-flash-exp` |
| `DEBUG` | No | Enable debug mode | `false` |

### Infrastructure Variables

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `REDIS_URL` | No | Redis connection URL (falls back to memory cache) | - |
| `CORS_ORIGINS` | No | Allowed CORS origins for API access | `["*"]` |
| `DISABLE_INTERNAL_DOCS` | No | Disable internal API documentation in production | `false` |
| `LOG_LEVEL` | No | Logging level (`DEBUG`, `INFO`, `WARNING`, `ERROR`) | `INFO` |

### Frontend Variables

| Variable | Required | Description | Default |
|----------|----------|-------------|---------|
| `API_BASE_URL` | Yes | Backend API base URL | `http://localhost:8000` |
| `SHOW_DEBUG_INFO` | No | Show debug information in UI | `false` |
| `INPUT_MAX_LENGTH` | No | Maximum input text length | `10000` |

### Advanced Configuration (Optional)

For advanced users requiring fine-tuned control:

```bash
export RESILIENCE_CUSTOM_CONFIG='{
  "retry_attempts": 5,
  "circuit_breaker_threshold": 10,
  "recovery_timeout": 120,
  "default_strategy": "conservative",
  "operation_overrides": {
    "qa": "critical",
    "summarize": "conservative"
  }
}'
```

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

The application provides comprehensive health monitoring with dual-API architecture:

#### Public API Health Checks
```bash
# Basic backend health
curl http://localhost:8000/v1/health

# Frontend health
curl http://localhost:8501/_stcore/health
```

#### Internal API Health Checks (Administrative)
```bash
# Comprehensive system health
curl http://localhost:8000/internal/health \
  -H "X-API-Key: your-api-key"

# Resilience system health
curl http://localhost:8000/internal/resilience/health \
  -H "X-API-Key: your-api-key"

# Cache system health
curl http://localhost:8000/internal/cache/health \
  -H "X-API-Key: your-api-key"

# Infrastructure monitoring
curl http://localhost:8000/internal/monitoring/metrics \
  -H "X-API-Key: your-api-key"
```

#### Health Check Response Examples

**Public Health Check** (`/v1/health`):
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "version": "1.0.0"
}
```

**Internal Health Check** (`/internal/health`):
```json
{
  "status": "healthy",
  "timestamp": "2024-01-15T10:30:00Z",
  "components": {
    "database": "healthy",
    "cache": "healthy",
    "ai_service": "healthy",
    "resilience": "healthy"
  },
  "metrics": {
    "uptime": "7d 2h 30m",
    "total_requests": 15420,
    "error_rate": 0.02
  }
}
```

### Resilience Monitoring

Monitor resilience patterns and performance:

```bash
# Get resilience metrics
curl http://localhost:8000/internal/resilience/metrics \
  -H "X-API-Key: your-api-key"

# Circuit breaker status
curl http://localhost:8000/internal/resilience/circuit-breakers \
  -H "X-API-Key: your-api-key"

# Performance benchmarks
curl -X POST http://localhost:8000/internal/resilience/benchmark \
  -H "X-API-Key: your-api-key"

# Configuration health
curl http://localhost:8000/internal/resilience/config/health-check \
  -H "X-API-Key: your-api-key"
```

### Infrastructure Monitoring

The template includes 38 resilience endpoints across 8 modules for comprehensive monitoring:

1. **Configuration Management** - Validate and manage resilience settings
2. **Circuit Breaker Management** - Monitor and control circuit breakers  
3. **Performance Monitoring** - Track system performance and metrics
4. **Advanced Analytics** - Usage trends and insights
5. **Cache Management** - Cache performance and hit rates
6. **Security Monitoring** - Authentication and access patterns
7. **Health Monitoring** - System component health status
8. **Alert Management** - System alerts and notifications

### Logging

Logs are structured and available via Docker:

```bash
# View all logs
docker-compose logs -f

# Service-specific logs
docker-compose logs -f backend
docker-compose logs -f frontend
docker-compose logs -f redis  # if using Redis

# Filter resilience-related logs
docker-compose logs backend 2>&1 | grep -i "resilience\|circuit\|retry"

# Filter security-related logs
docker-compose logs backend 2>&1 | grep -i "auth\|security\|api_key"

# Performance monitoring logs
docker-compose logs backend 2>&1 | grep -i "performance\|metrics\|cache"
```

### Production Monitoring Setup

For production deployments, disable internal API documentation:

```bash
export DISABLE_INTERNAL_DOCS=true
```

This removes `/internal/docs` while keeping monitoring endpoints functional.

## Infrastructure Requirements

### Redis Cache (Recommended)

For production deployments, Redis is recommended for optimal caching performance:

```bash
# Docker Compose (included in template)
services:
  redis:
    image: redis:alpine
    ports:
      - "6379:6379"
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

# Environment configuration
export REDIS_URL=redis://localhost:6379
```

**Note**: The application automatically falls back to in-memory caching if Redis is unavailable.

### Resource Requirements

#### Minimum Requirements (Development)
- **CPU**: 1 core
- **Memory**: 1GB RAM
- **Storage**: 10GB disk space
- **Network**: Basic internet connectivity

#### Recommended Production Requirements
- **CPU**: 2+ cores
- **Memory**: 4GB+ RAM
- **Storage**: 50GB+ disk space
- **Network**: High-bandwidth connection
- **Redis**: Dedicated Redis instance or cluster

#### Scaling Considerations
- **Backend**: Stateless, horizontally scalable
- **Frontend**: Stateless, can be served from CDN
- **Redis**: Consider Redis Cluster for high-availability
- **Load Balancer**: Required for multi-instance deployments

### Security Requirements

#### Authentication
- Multi-key API authentication system
- Primary API key required for all endpoints
- Additional API keys supported for different services/environments

#### Network Security
- HTTPS/TLS required for production
- CORS properly configured for frontend domains
- Internal API endpoints protected by authentication
- Rate limiting recommended for public endpoints

#### Data Security
- API keys stored securely (environment variables, secrets management)
- No sensitive data logged in application logs
- Prompt injection protection built-in
- Input sanitization for all AI operations

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

# Test Public API endpoints
curl http://localhost:8000/v1/health
curl -X POST http://localhost:8000/v1/text-processing/summarize \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"text":"test content","max_length":100}'

# Test Internal API endpoints (requires API key)
curl http://localhost:8000/internal/health \
  -H "X-API-Key: your-api-key"

curl http://localhost:8000/internal/resilience/health \
  -H "X-API-Key: your-api-key"

curl http://localhost:8000/internal/cache/stats \
  -H "X-API-Key: your-api-key"

# Check resilience metrics
curl http://localhost:8000/internal/resilience/metrics \
  -H "X-API-Key: your-api-key"

# Validate resilience configuration
curl -X POST http://localhost:8000/internal/resilience/validate \
  -H "Content-Type: application/json" \
  -H "X-API-Key: your-api-key" \
  -d '{"configuration": {"retry_attempts": 3}}'
```

### Environment-Specific Debug Commands

#### Development Environment
```bash
export RESILIENCE_PRESET=development
export DEBUG=true
export LOG_LEVEL=DEBUG

# Test with development settings
curl http://localhost:8000/internal/resilience/config \
  -H "X-API-Key: your-api-key"
```

#### Production Environment
```bash
export RESILIENCE_PRESET=production  
export DISABLE_INTERNAL_DOCS=true
export LOG_LEVEL=INFO

# Verify production configuration
curl http://localhost:8000/internal/resilience/config/health-check \
  -H "X-API-Key: your-api-key"
```

### Redis Debug Commands

```bash
# Test Redis connection (if using)
docker-compose exec redis redis-cli ping

# Check cache statistics
curl http://localhost:8000/internal/cache/stats \
  -H "X-API-Key: your-api-key"

# Clear cache if needed
curl -X POST http://localhost:8000/internal/cache/clear \
  -H "X-API-Key: your-api-key"
```

## Related Documentation

### Prerequisites
- **[Backend Guide](./BACKEND.md)**: Understanding the backend architecture being deployed
- **[Frontend Guide](./FRONTEND.md)**: Understanding the frontend architecture being deployed
- **[Testing Guide](./TESTING.md)**: Comprehensive testing before deployment

### Related Topics
- **[Docker Setup](./developer/DOCKER.md)**: Development and production Docker environments
- **[Authentication Guide](./developer/AUTHENTICATION.md)**: Production authentication and security configuration

### Next Steps
- **[Security Guide](./SECURITY.md)**: Comprehensive security implementation and operational procedures
- **[Operations Monitoring Guide](./operations/MONITORING.md)**: Production monitoring setup and operational procedures
- **[Troubleshooting Guide](./operations/TROUBLESHOOTING.md)**: Operational troubleshooting procedures for deployment issues
- **[Performance Optimization Guide](./operations/PERFORMANCE_OPTIMIZATION.md)**: Production performance tuning and optimization procedures
- **[Backup & Recovery Guide](./operations/BACKUP_RECOVERY.md)**: Data protection and disaster recovery procedures
- **[Monitoring Infrastructure](./infrastructure/MONITORING.md)**: Technical monitoring implementation details
- **[Security Infrastructure](./infrastructure/SECURITY.md)**: Technical security implementation details
- **[Cache Infrastructure](./infrastructure/CACHE.md)**: Production caching and performance optimization