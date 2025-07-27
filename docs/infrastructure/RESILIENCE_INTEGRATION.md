# Resilience Configuration Integration Guide

This guide covers how the resilience configuration preset system is integrated into the development workflow, including Makefile commands, Docker health checks, and CI/CD validation.

## Quick Start

### Using Presets in Development

```bash
# Set resilience preset for your environment
export RESILIENCE_PRESET=development    # For local development
export RESILIENCE_PRESET=simple         # For general use/staging  
export RESILIENCE_PRESET=production     # For production

# Start development environment
make dev

# Validate current configuration
make validate-config
```

## Makefile Commands

The resilience configuration system is fully integrated with the project's Makefile for easy management:

### Preset Management

```bash
# List all available presets with descriptions
make list-presets

# Show detailed information about a specific preset
make show-preset PRESET=simple
make show-preset PRESET=development
make show-preset PRESET=production

# Validate current configuration
make validate-config

# Validate a specific preset
make validate-preset PRESET=production

# Get preset recommendation for an environment
make recommend-preset ENV=development
make recommend-preset ENV=production

# Migrate from legacy configuration
make migrate-config

# Run preset-related tests
make test-presets
```

### Example Usage

```bash
# Development workflow
$ make show-preset PRESET=development
======================================================================
 DEVELOPMENT PRESET CONFIGURATION
======================================================================

📝 Description: Fast-fail configuration optimized for development speed

⚙️  BASIC CONFIGURATION:
   • Retry Attempts: 2
   • Circuit Breaker Threshold: 3 failures
   • Recovery Timeout: 30 seconds
   • Default Strategy: aggressive

🎯 OPERATION-SPECIFIC STRATEGIES:
   • Sentiment: aggressive
   • Qa: balanced

🌍 ENVIRONMENT CONTEXTS:
   • Recommended for: development, testing

💻 USAGE:
   export RESILIENCE_PRESET=development
```

## Docker Integration

### Environment-Specific Defaults

Each Docker Compose configuration automatically sets appropriate defaults:

- **Development** (`docker-compose.dev.yml`): `RESILIENCE_PRESET=development`
- **Base** (`docker-compose.yml`): `RESILIENCE_PRESET=simple`
- **Production** (`docker-compose.prod.yml`): `RESILIENCE_PRESET=production`

### Health Checks

Enhanced Docker health checks now validate resilience configuration:

```yaml
healthcheck:
  test: ["CMD", "sh", "-c", "curl -f http://localhost:8000/health && curl -f http://localhost:8000/resilience/config && python scripts/health_check_resilience.py"]
  interval: 30s
  timeout: 10s
  retries: 3
  start_period: 40s
```

The health check validates:
1. Basic application health (`/health`)
2. Resilience configuration endpoint (`/resilience/config`)
3. Preset system initialization (`health_check_resilience.py`)

### Starting Services

```bash
# Development environment (uses development preset by default)
make dev

# Production environment (uses production preset by default)
make prod

# Check service health including resilience configuration
make health
```

## CI/CD Integration

### Continuous Integration Tests

The CI pipeline now includes resilience configuration validation:

```bash
# Fast CI tests (includes config validation)
make ci-test

# Comprehensive CI tests (includes all preset validation)
make ci-test-all
```

The CI pipeline validates:
- Current resilience configuration is valid
- All presets can be loaded successfully
- Preset-related tests pass
- Configuration can be applied to resilience service

### GitHub Actions Example

```yaml
- name: Validate Resilience Configuration
  run: |
    make validate-config
    make validate-preset PRESET=simple
    make validate-preset PRESET=development 
    make validate-preset PRESET=production
    make test-presets
```

## Validation Scripts

### Comprehensive Validation

The `scripts/validate_resilience_config.py` script provides comprehensive validation:

```bash
# List all presets
python scripts/validate_resilience_config.py --list-presets

# Show preset details
python scripts/validate_resilience_config.py --show-preset simple

# Validate current configuration
python scripts/validate_resilience_config.py --validate-current

# Get environment recommendation
python scripts/validate_resilience_config.py --recommend-preset development
```

### Health Check Script

The `scripts/health_check_resilience.py` script provides lightweight health checks suitable for Docker:

```bash
# Run health check (exits 0 if healthy, 1 if unhealthy)
python scripts/health_check_resilience.py
```

## Environment Configuration

### Basic Setup

Set the resilience preset in your environment:

```bash
# .env file
RESILIENCE_PRESET=simple
GEMINI_API_KEY=your-api-key-here
```

### Docker Compose Override

```yaml
# docker-compose.override.yml
services:
  backend:
    environment:
      - RESILIENCE_PRESET=production
```

### Environment Variables

| Variable | Description | Default | Options |
|----------|-------------|---------|---------|
| `RESILIENCE_PRESET` | Resilience configuration preset | `simple` | `simple`, `development`, `production` |
| `RESILIENCE_CUSTOM_CONFIG` | Custom JSON configuration | None | JSON string with custom settings |

## Monitoring and Alerting

### Configuration Health

Monitor resilience configuration health through:

```bash
# Service health (includes resilience validation)
curl http://localhost:8000/health

# Resilience configuration status
curl http://localhost:8000/resilience/config

# Preset information
curl http://localhost:8000/resilience/presets
```

### Error Handling

The system provides comprehensive error handling:
- Invalid preset names → fallback to `simple` preset
- Missing configuration → uses preset defaults
- JSON parsing errors → validation warnings
- Service initialization failures → health check failures

## Best Practices

### Development Workflow

1. **Start with preset**: Use `RESILIENCE_PRESET=development` for local development
2. **Validate early**: Run `make validate-config` after environment changes
3. **Test presets**: Use `make test-presets` before committing preset changes
4. **Monitor health**: Use `make health` to verify configuration is working

### Deployment Workflow

1. **Environment-specific presets**: Set appropriate preset for each environment
2. **Validate before deploy**: Run `make ci-test-all` in deployment pipeline
3. **Monitor after deploy**: Check health endpoints post-deployment
4. **Rollback plan**: Use `RESILIENCE_PRESET=simple` as safe fallback

### Troubleshooting

```bash
# Debug configuration issues
make validate-config

# Check specific preset
make show-preset PRESET=production

# View current configuration
curl http://localhost:8000/resilience/config

# Run health check
python scripts/health_check_resilience.py

# Check logs
make logs
```

## Migration Guide

### From Legacy Configuration

If you have existing resilience configuration (47+ environment variables):

1. **Keep existing setup** - The system maintains backward compatibility
2. **Get migration suggestions** - Run `make migrate-config`
3. **Validate preset equivalent** - Use `make recommend-preset ENV=production`
4. **Gradual migration** - Test preset in development first
5. **Update deployment** - Replace environment variables with `RESILIENCE_PRESET`

### Example Migration

```bash
# Before (legacy configuration)
export RETRY_MAX_ATTEMPTS=5
export CIRCUIT_BREAKER_FAILURE_THRESHOLD=10
export DEFAULT_RESILIENCE_STRATEGY=conservative
# ... 44+ more variables

# After (preset configuration)  
export RESILIENCE_PRESET=production
```

## API Reference

### Resilience Endpoints

- `GET /resilience/presets` - List available presets
- `GET /resilience/presets/{name}` - Get specific preset details
- `GET /resilience/config` - Current active configuration
- `POST /resilience/validate` - Validate custom configuration

### Configuration Schema

```json
{
  "preset_name": "production",
  "retry_attempts": 5,
  "circuit_breaker_threshold": 10,
  "recovery_timeout": 120,
  "default_strategy": "conservative",
  "operation_overrides": {
    "qa": "critical",
    "sentiment": "aggressive"
  }
}
```

For complete API documentation, see the interactive docs at `/docs` when the service is running. 