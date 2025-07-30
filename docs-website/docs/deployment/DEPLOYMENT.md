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