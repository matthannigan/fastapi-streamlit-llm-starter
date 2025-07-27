# Domain Service: Application Health Check API

📚 **EXAMPLE IMPLEMENTATION** - Replace in your project
💡 **Demonstrates infrastructure usage patterns**
🔄 **Expected to be modified/replaced**

This module provides a comprehensive health check endpoint for the application,
demonstrating how to build monitoring endpoints that check multiple infrastructure
components. It serves as an example for implementing domain-level health monitoring
that aggregates infrastructure service status.

## Core Components

### API Endpoints
- `GET /v1/health`: Enhanced health check with comprehensive system monitoring

### Health Check Components
The health check evaluates three main components:
- **AI Model**: Verifies Google Gemini API key configuration
- **Resilience Infrastructure**: Checks circuit breakers and failure detection
- **Cache System**: Validates Redis connectivity and cache operations

### Health Status Algorithm
- **"healthy"**: AI model available and no critical component failures
- **"degraded"**: AI model unavailable or critical components explicitly failed
- **Optional Components**: Resilience and cache can be None without affecting overall health

## Dependencies & Integration

### Infrastructure Dependencies
- `app.infrastructure.resilience.ai_resilience`: Resilience service health checking
- `app.infrastructure.cache.AIResponseCache`: Cache service connectivity testing
- `app.core.config.settings`: Configuration access for component validation

### Domain Logic
- Component health aggregation and status determination
- Graceful degradation when optional services are unavailable
- Manual cache service instantiation for health validation

## Response Structure

### Successful Health Check
```json
{
"status": "healthy",
"timestamp": "2025-06-28T00:06:39.130848",
"version": "1.0.0",
"ai_model_available": true,
"resilience_healthy": true,
"cache_healthy": true
}
```

### Degraded Status Example
```json
{
"status": "degraded",
"ai_model_available": false,
"resilience_healthy": null,
"cache_healthy": true
}
```

## Usage Examples

### Health Check Request
```bash
# No authentication required
curl http://localhost:8000/v1/health
```

### Load Balancer Configuration
```yaml
health_check:
path: /v1/health
expected_status: 200
expected_body_contains: '"status":"healthy"'
```

## Implementation Notes

This service demonstrates domain-level health checking that:
- Aggregates multiple infrastructure component health status
- Uses manual service instantiation for isolated health testing
- Implements graceful degradation for optional components
- Provides structured responses for monitoring systems

**Replace in your project** - Customize the health checks and status logic
based on your specific infrastructure components and monitoring requirements.
