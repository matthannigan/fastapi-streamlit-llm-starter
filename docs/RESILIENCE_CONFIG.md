# Resilience Configuration Guide

This guide explains the simplified resilience configuration system that reduces 47+ environment variables to a single preset selection, while maintaining full customization capabilities for advanced users.

## Table of Contents

- [Quick Start](#quick-start)
- [Configuration Presets](#configuration-presets)
- [Custom Configuration](#custom-configuration)
- [Environment Detection](#environment-detection)
- [Migration Guide](#migration-guide)
- [API Reference](#api-reference)
- [Troubleshooting](#troubleshooting)

## Quick Start

### Simple Setup (Recommended)

Set a single environment variable based on your deployment context:

```bash
# For development and testing
export RESILIENCE_PRESET=development

# For general use and staging
export RESILIENCE_PRESET=simple

# For production workloads
export RESILIENCE_PRESET=production
```

That's it! No need to configure 47+ individual environment variables.

### Docker Environment

Add to your `.env` file or Docker configuration:

```env
RESILIENCE_PRESET=simple
```

Or in docker-compose.yml:

```yaml
services:
  backend:
    environment:
      - RESILIENCE_PRESET=production
```

## Configuration Presets

### Available Presets

| Preset | Best For | Retry Attempts | Circuit Breaker Threshold | Recovery Timeout | Default Strategy |
|--------|----------|----------------|---------------------------|------------------|------------------|
| **simple** | General use, testing, staging | 3 | 5 failures | 60 seconds | Balanced |
| **development** | Local development, fast feedback | 2 | 3 failures | 30 seconds | Aggressive |
| **production** | Production workloads, high reliability | 5 | 10 failures | 120 seconds | Conservative |

### Preset Details

#### Simple Preset
- **Use Case**: Balanced configuration suitable for most scenarios
- **Characteristics**: Moderate retry attempts, reasonable failure tolerance
- **Operation Overrides**: None (uses balanced strategy for all operations)
- **Ideal For**: New projects, testing, staging environments

#### Development Preset
- **Use Case**: Fast-fail configuration optimized for development speed
- **Characteristics**: Quick failures, minimal retries, fast recovery
- **Operation Overrides**: 
  - `sentiment`: Aggressive (fast feedback for UI development)
  - `qa`: Balanced (reasonable reliability for testing)
- **Ideal For**: Local development, unit testing, CI/CD pipelines

#### Production Preset
- **Use Case**: High-reliability configuration for production workloads
- **Characteristics**: Multiple retries, high failure tolerance, longer recovery
- **Operation Overrides**:
  - `qa`: Critical (maximum reliability for user-facing Q&A)
  - `sentiment`: Aggressive (can afford faster feedback)
  - `summarize`: Conservative (important for content processing)
  - `key_points`: Balanced (balanced approach)
  - `questions`: Balanced (balanced approach)
- **Ideal For**: Production systems, customer-facing applications

### Strategy Types

Each preset uses different resilience strategies:

- **Aggressive**: Fast failures, minimal delays, quick recovery
- **Balanced**: Moderate approach balancing speed and reliability
- **Conservative**: Higher reliability with longer delays and more retries
- **Critical**: Maximum reliability for mission-critical operations

## Custom Configuration

### Basic Custom Configuration

For advanced users who need fine-tuned control:

```bash
export RESILIENCE_CUSTOM_CONFIG='{
  "retry_attempts": 4,
  "circuit_breaker_threshold": 8,
  "recovery_timeout": 90,
  "default_strategy": "balanced"
}'
```

### Advanced Custom Configuration

Full configuration with operation-specific overrides:

```bash
export RESILIENCE_CUSTOM_CONFIG='{
  "retry_attempts": 4,
  "circuit_breaker_threshold": 8,
  "recovery_timeout": 90,
  "default_strategy": "conservative",
  "operation_overrides": {
    "qa": "critical",
    "sentiment": "aggressive",
    "summarize": "balanced",
    "key_points": "balanced",
    "questions": "conservative"
  },
  "exponential_multiplier": 1.5,
  "exponential_min": 2.0,
  "exponential_max": 30.0,
  "jitter_enabled": true,
  "jitter_max": 3.0
}'
```

### Configuration Schema

Valid configuration parameters:

| Parameter | Type | Range | Description |
|-----------|------|-------|-------------|
| `retry_attempts` | integer | 1-10 | Number of retry attempts |
| `circuit_breaker_threshold` | integer | 1-20 | Failures before circuit opens |
| `recovery_timeout` | integer | 10-300 | Circuit recovery time (seconds) |
| `default_strategy` | string | aggressive, balanced, conservative, critical | Default resilience strategy |
| `operation_overrides` | object | - | Strategy overrides per operation |
| `exponential_multiplier` | number | 0.1-5.0 | Exponential backoff multiplier |
| `exponential_min` | number | 0.5-10.0 | Minimum backoff delay |
| `exponential_max` | number | 5.0-120.0 | Maximum backoff delay |
| `jitter_enabled` | boolean | - | Enable jitter in delays |
| `jitter_max` | number | 0.1-10.0 | Maximum jitter value |
| `max_delay_seconds` | integer | 5-600 | Total delay limit for all retries |

### Validation

Validate your custom configuration:

```bash
curl -X POST http://localhost:8000/resilience/validate \
  -H "Content-Type: application/json" \
  -d '{
    "configuration": {
      "retry_attempts": 4,
      "circuit_breaker_threshold": 8,
      "default_strategy": "balanced"
    }
  }'
```

## Environment Detection

### Automatic Detection

The system automatically detects your environment and suggests appropriate presets:

```bash
# Get environment-aware recommendation
curl http://localhost:8000/resilience/recommend-auto
```

### Detection Logic

**Development Environment Indicators:**
- `DEBUG=true` or `DEBUG=1`
- `NODE_ENV=development`
- `HOST` contains `localhost` or `127.0.0.1`
- Presence of `.env` file
- Presence of `docker-compose.dev.yml`
- Presence of `.git` directory

**Production Environment Indicators:**
- `PROD=true` or `PRODUCTION=true`
- `DEBUG=false` or `DEBUG=0`
- `DATABASE_URL` contains `production`
- `HOST` contains `prod`

**Staging Environment Detection:**
- Environment names matching: `staging`, `stage`, `pre-prod`, `uat`, `integration`

### Manual Environment Recommendation

Get recommendations for specific environments:

```bash
# Development environment
curl http://localhost:8000/resilience/recommend/development

# Production environment  
curl http://localhost:8000/resilience/recommend/production

# Custom environment
curl http://localhost:8000/resilience/recommend/my-custom-env
```

## Migration Guide

### Detecting Legacy Configuration

Check if you're using legacy configuration:

```bash
curl http://localhost:8000/resilience/config
```

Response will indicate if legacy configuration is detected:

```json
{
  "preset_name": "simple",
  "is_legacy_config": true,
  "configuration": {...},
  "operation_strategies": {...}
}
```

### Migration Steps

1. **Check Current Configuration**:
```bash
# View current settings
curl http://localhost:8000/resilience/config

# Get preset recommendation based on current config
curl http://localhost:8000/resilience/recommend-auto
```

2. **Choose Migration Strategy**:

**Option A: Simple Migration (Recommended)**
```bash
# Remove legacy environment variables
unset CIRCUIT_BREAKER_FAILURE_THRESHOLD
unset RETRY_MAX_ATTEMPTS
unset DEFAULT_RESILIENCE_STRATEGY
# ... remove other legacy variables

# Set preset
export RESILIENCE_PRESET=production  # or development/simple
```

**Option B: Custom Configuration Migration**
```bash
# Convert existing settings to custom JSON
export RESILIENCE_CUSTOM_CONFIG='{
  "retry_attempts": 5,  # from RETRY_MAX_ATTEMPTS
  "circuit_breaker_threshold": 10,  # from CIRCUIT_BREAKER_FAILURE_THRESHOLD
  "default_strategy": "conservative"  # from DEFAULT_RESILIENCE_STRATEGY
}'
```

3. **Validate New Configuration**:
```bash
# Test the new configuration
curl http://localhost:8000/resilience/config

# Validate custom config if used
curl -X POST http://localhost:8000/resilience/validate \
  -H "Content-Type: application/json" \
  -d '{"configuration": {...}}'
```

4. **Test and Deploy**:
```bash
# Restart application with new configuration
# Monitor for any issues
# Check resilience metrics
curl http://localhost:8000/resilience/metrics
```

### Legacy Variable Mapping

Common legacy variables and their preset equivalents:

| Legacy Variable | Preset Parameter | Notes |
|-----------------|------------------|-------|
| `RETRY_MAX_ATTEMPTS` | `retry_attempts` | Direct mapping |
| `CIRCUIT_BREAKER_FAILURE_THRESHOLD` | `circuit_breaker_threshold` | Direct mapping |
| `CIRCUIT_BREAKER_RECOVERY_TIMEOUT` | `recovery_timeout` | Direct mapping |
| `DEFAULT_RESILIENCE_STRATEGY` | `default_strategy` | Direct mapping |
| `SUMMARIZE_RESILIENCE_STRATEGY` | `operation_overrides.summarize` | Operation-specific |
| `SENTIMENT_RESILIENCE_STRATEGY` | `operation_overrides.sentiment` | Operation-specific |
| `QA_RESILIENCE_STRATEGY` | `operation_overrides.qa` | Operation-specific |

## API Reference

### Configuration Management Endpoints

#### List Available Presets
```bash
GET /resilience/presets
```

Response:
```json
[
  {
    "name": "Simple",
    "description": "Balanced configuration suitable for most use cases",
    "retry_attempts": 3,
    "circuit_breaker_threshold": 5,
    "recovery_timeout": 60,
    "default_strategy": "balanced",
    "environment_contexts": ["development", "testing", "staging", "production"]
  }
]
```

#### Get Preset Details
```bash
GET /resilience/presets/{preset_name}
```

#### Get Current Configuration
```bash
GET /resilience/config
```

#### Validate Configuration
```bash
POST /resilience/validate
Content-Type: application/json

{
  "configuration": {
    "retry_attempts": 3,
    "circuit_breaker_threshold": 5,
    "default_strategy": "balanced"
  }
}
```

#### Get Environment Recommendation
```bash
GET /resilience/recommend/{environment}
GET /resilience/recommend-auto
```

#### Get Configuration Templates
```bash
GET /resilience/templates
```

#### Validate Template-Based Configuration
```bash
POST /resilience/validate-template
Content-Type: application/json

{
  "template_name": "robust_production",
  "overrides": {
    "retry_attempts": 6
  }
}
```

### Health and Monitoring

#### Check Resilience Health
```bash
GET /resilience/health
```

#### Get Resilience Metrics
```bash
GET /resilience/metrics
```

#### Reset Metrics
```bash
POST /resilience/metrics/reset
POST /resilience/metrics/reset?operation_name=summarize
```

## Troubleshooting

### Common Issues

#### Invalid Preset Name
**Error**: `Invalid preset 'prod'. Available: ['simple', 'development', 'production']`

**Solution**: Use correct preset name:
```bash
export RESILIENCE_PRESET=production  # not 'prod'
```

#### JSON Parsing Error
**Error**: `Invalid JSON in resilience_custom_config`

**Solution**: Validate JSON format:
```bash
# Test JSON validity
echo '{"retry_attempts": 3}' | python -m json.tool

# Use proper escaping in shell
export RESILIENCE_CUSTOM_CONFIG='{"retry_attempts": 3, "default_strategy": "balanced"}'
```

#### Configuration Validation Failures
**Error**: `retry_attempts must be between 1 and 10`

**Solution**: Check parameter ranges in the configuration schema above.

#### Legacy Configuration Conflicts
**Error**: `Conflicting configuration detected`

**Solution**: Remove legacy environment variables or disable preset system temporarily:
```bash
# Option 1: Remove legacy variables
unset RETRY_MAX_ATTEMPTS CIRCUIT_BREAKER_FAILURE_THRESHOLD

# Option 2: Temporarily disable preset (not recommended)
unset RESILIENCE_PRESET
```

### Debug Configuration Loading

Enable debug logging to troubleshoot configuration issues:

```bash
export LOG_LEVEL=DEBUG
export SHOW_CONFIG_LOADING=true
```

Check configuration loading in application logs:
```bash
# Docker
docker-compose logs backend | grep -i resilience

# Local
tail -f logs/app.log | grep -i resilience
```

### Performance Issues

If configuration loading is slow:

1. **Check Configuration Size**:
```bash
# Custom config should be < 4KB
echo $RESILIENCE_CUSTOM_CONFIG | wc -c
```

2. **Monitor Loading Time**:
```bash
curl -w "@curl-format.txt" http://localhost:8000/resilience/config
```

3. **Use Simpler Configuration**:
```bash
# Switch to preset if custom config is complex
export RESILIENCE_PRESET=production
unset RESILIENCE_CUSTOM_CONFIG
```

### Getting Help

1. **Check Configuration Status**:
```bash
curl http://localhost:8000/resilience/config
```

2. **Validate Current Settings**:
```bash
curl -X POST http://localhost:8000/resilience/validate \
  -H "Content-Type: application/json" \
  -d '{"configuration": {}}'
```

3. **Review Application Logs**:
```bash
# Look for resilience-related errors
docker-compose logs backend 2>&1 | grep -i "resilience\|preset\|circuit\|retry"
```

4. **Test Resilience Behavior**:
```bash
# Trigger operations to test resilience
curl -X POST http://localhost:8000/process \
  -H "Content-Type: application/json" \
  -d '{"text": "test", "operation": "summarize"}'
```

## Configuration Templates

Pre-defined templates for common use cases:

### Fast Development
```json
{
  "name": "Fast Development",
  "description": "Optimized for development speed with minimal retries",
  "config": {
    "retry_attempts": 1,
    "circuit_breaker_threshold": 2,
    "recovery_timeout": 15,
    "default_strategy": "aggressive"
  }
}
```

### Robust Production
```json
{
  "name": "Robust Production", 
  "description": "High reliability configuration for production workloads",
  "config": {
    "retry_attempts": 6,
    "circuit_breaker_threshold": 12,
    "recovery_timeout": 180,
    "default_strategy": "conservative",
    "operation_overrides": {
      "qa": "critical",
      "summarize": "conservative"
    }
  }
}
```

### Low Latency
```json
{
  "name": "Low Latency",
  "description": "Minimal latency configuration with fast failures",
  "config": {
    "retry_attempts": 1,
    "circuit_breaker_threshold": 2,
    "recovery_timeout": 10,
    "default_strategy": "aggressive",
    "max_delay_seconds": 5
  }
}
```

### High Throughput
```json
{
  "name": "High Throughput",
  "description": "Optimized for high throughput with moderate reliability",
  "config": {
    "retry_attempts": 3,
    "circuit_breaker_threshold": 8,
    "recovery_timeout": 45,
    "default_strategy": "balanced"
  }
}
```

### Maximum Reliability
```json
{
  "name": "Maximum Reliability",
  "description": "Maximum reliability configuration for critical operations",
  "config": {
    "retry_attempts": 8,
    "circuit_breaker_threshold": 15,
    "recovery_timeout": 300,
    "default_strategy": "critical",
    "operation_overrides": {
      "qa": "critical",
      "summarize": "critical",
      "sentiment": "conservative"
    }
  }
}
```

Use templates via API:
```bash
# List available templates
curl http://localhost:8000/resilience/templates

# Get specific template
curl http://localhost:8000/resilience/templates/robust_production

# Validate template-based config
curl -X POST http://localhost:8000/resilience/validate-template \
  -H "Content-Type: application/json" \
  -d '{"template_name": "robust_production", "overrides": {"retry_attempts": 7}}'
```
