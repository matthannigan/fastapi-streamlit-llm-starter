# Resilience Configuration Guide

This guide explains the simplified resilience configuration system that reduces 47+ environment variables to a single preset selection, while maintaining full customization capabilities for advanced users. The system now includes intelligent environment detection, preset comparison tools, and enhanced user experience features.

## Table of Contents

- [Quick Start](#quick-start)
- [Configuration Presets](#configuration-presets)
- [Environment Detection & Recommendations](#environment-detection--recommendations)
- [Preset Comparison & Selection](#preset-comparison--selection)
- [Custom Configuration](#custom-configuration)
- [Configuration Health & Validation](#configuration-health--validation)
- [Migration Guide](#migration-guide)
- [API Reference](#api-reference)
- [User Experience Features](#user-experience-features)
- [Troubleshooting](#troubleshooting)

## Quick Start

### 🚀 Automatic Setup (Recommended)

Let the system detect your environment and suggest the optimal preset:

```bash
# Get automatic environment detection and preset recommendation
curl http://localhost:8000/resilience/environment/detect
```

**Example Response**:
```json
{
  "environment_detection": {
    "detected_environment": "development (auto-detected)",
    "suggested_preset": "development",
    "confidence": 0.75,
    "reasoning": "Development indicators detected (DEBUG=true, .env file, localhost, etc.)",
    "current_preset": "simple",
    "preset_matches_environment": false,
    "recommendation": "💡 We suggest switching from 'simple' to 'development' preset for better performance in your environment."
  }
}
```

Apply the suggested preset:
```bash
export RESILIENCE_PRESET=development
```

### Simple Setup (Manual)

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

### Enhanced Preset Information

Get comprehensive preset details:

```bash
# List all presets with detailed information
curl http://localhost:8000/resilience/presets
```

**Example Response**:
```json
[
  {
    "name": "simple",
    "display_name": "Simple",
    "description": "Balanced configuration suitable for most use cases",
    "best_for": ["General use", "Testing", "Staging environments"],
    "trade_offs": {
      "pros": ["Easy to configure", "Balanced performance", "Good for most scenarios"],
      "cons": ["May not be optimal for specific environments"]
    },
    "retry_attempts": 3,
    "circuit_breaker_threshold": 5,
    "recovery_timeout": 60,
    "default_strategy": "balanced",
    "environment_contexts": ["development", "testing", "staging", "production"]
  }
]
```

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

## Environment Detection & Recommendations

### 🔍 Automatic Environment Detection

The system automatically detects your current environment and suggests the most appropriate resilience preset based on various indicators.

```bash
# Get environment-aware recommendation
curl http://localhost:8000/resilience/environment/detect
```

### Detection Logic

**Development Environment Indicators:**
- Environment variables: `DEBUG=true`, `NODE_ENV=development`, `RAILS_ENV=development`, `APP_ENV=development`
- Development indicators: `.env` files, `DEBUG=true`, localhost usage
- File system context: `.git` directory, `docker-compose.dev.yml`
- Host indicators: `HOST` contains `localhost` or `127.0.0.1`

**Production Environment Indicators:**
- Environment variables: `PROD=true`, `PRODUCTION=true`, `NODE_ENV=production`
- Production indicators: production database URLs, `DEBUG=false`
- Host indicators: `HOST` contains `prod`

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

## Preset Comparison & Selection

### 🔄 Preset Comparison Tool

Compare your current preset with any other preset to understand the differences and trade-offs:

```bash
# Compare current preset with production preset
curl "http://localhost:8000/resilience/presets/compare?current=simple&compare_with=production"
```

**Example Response**:
```json
{
  "comparison": {
    "current_preset": {
      "name": "simple",
      "retry_attempts": 3,
      "circuit_breaker_threshold": 5,
      "recovery_timeout": 60
    },
    "compare_preset": {
      "name": "production", 
      "retry_attempts": 5,
      "circuit_breaker_threshold": 10,
      "recovery_timeout": 120
    },
    "differences": [
      {
        "parameter": "retry_attempts",
        "current_value": 3,
        "compare_value": 5,
        "impact": "Production preset provides +2 additional retry attempts for better reliability",
        "trade_off": "Slightly higher latency in failure scenarios"
      }
    ],
    "recommendations": [
      "Consider switching to production preset for better fault tolerance",
      "Production preset is better suited for customer-facing applications"
    ]
  }
}
```

### Quick Preset Selection Guide

Use the environment detection to get personalized recommendations:

```bash
# Get tailored recommendation based on your environment
curl http://localhost:8000/resilience/environment/detect

# Compare with suggested preset
curl "http://localhost:8000/resilience/presets/compare?compare_with=development"
```

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

## Configuration Health & Validation

### 🏥 Configuration Health Check

Get a comprehensive health assessment of your current configuration:

```bash
curl http://localhost:8000/resilience/config/health-check
```

**Example Response**:
```json
{
  "overall_health": {
    "score": 85,
    "status": "healthy",
    "summary": "🟢 Good! Your configuration is working well with minor optimization opportunities."
  },
  "validation_results": {
    "is_valid": true,
    "errors": [],
    "warnings": [
      "Consider enabling jitter for better load distribution"
    ]
  },
  "environment_alignment": {
    "matches_environment": true,
    "detected_environment": "development",
    "current_preset": "development",
    "alignment_score": 0.9
  },
  "performance_analysis": {
    "estimated_latency": "low",
    "reliability_score": 0.8,
    "throughput_impact": "minimal"
  },
  "recommendations": {
    "suggested_actions": [
      {
        "action": "enable_jitter",
        "description": "Enable jitter to improve load distribution",
        "command": "Add jitter_enabled: true to custom config",
        "impact": "Better performance under high load"
      }
    ],
    "optimization_opportunities": [
      "Consider custom operation overrides for better performance"
    ]
  }
}
```

### 🔧 Enhanced Validation with Friendly Errors

Validate your configuration with user-friendly error messages:

```bash
curl -X POST http://localhost:8000/resilience/validate/friendly \
  -H "Content-Type: application/json" \
  -d '{"configuration": {"retry_attempts": 15, "circuit_breaker_threshold": 8}}'
```

**Enhanced Error Response**:
```json
{
  "is_valid": false,
  "errors": [
    {
      "field": "retry_attempts",
      "value": 15,
      "message": "Value 15 is greater than maximum 10",
      "friendly_message": "🔧 Retry attempts value is out of range",
      "suggestion": "Set retry_attempts to a number between 1 (fast failure) and 10 (maximum persistence)",
      "valid_range": "1-10",
      "examples": ["3 (balanced)", "5 (reliable)", "10 (maximum)"],
      "quick_fix": "retry_attempts: 3"
    }
  ],
  "warnings": [],
  "suggestions": [
    "💡 For high reliability, consider retry_attempts: 5 with circuit_breaker_threshold: 10",
    "🚀 For fast feedback, try retry_attempts: 2 with circuit_breaker_threshold: 3"
  ]
}
```

### Standard Validation

Basic validation for custom configurations:

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

1. **Check Current Configuration and Get Recommendations**:
```bash
# View current settings
curl http://localhost:8000/resilience/config

# Get environment-based recommendation
curl http://localhost:8000/resilience/environment/detect

# Compare current with recommended preset
curl "http://localhost:8000/resilience/presets/compare?compare_with=development"
```

2. **Choose Migration Strategy**:

**Option A: Simple Migration (Recommended)**
```bash
# Remove legacy environment variables
unset CIRCUIT_BREAKER_FAILURE_THRESHOLD
unset RETRY_MAX_ATTEMPTS
unset DEFAULT_RESILIENCE_STRATEGY
# ... remove other legacy variables

# Set preset based on recommendation
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

# Run health check
curl http://localhost:8000/resilience/config/health-check

# Validate custom config if used
curl -X POST http://localhost:8000/resilience/validate/friendly \
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

Enhanced response with detailed information:
```json
[
  {
    "name": "simple",
    "display_name": "Simple",
    "description": "Balanced configuration suitable for most use cases",
    "best_for": ["General use", "Testing", "Staging environments"],
    "trade_offs": {
      "pros": ["Easy to configure", "Balanced performance", "Good for most scenarios"],
      "cons": ["May not be optimal for specific environments"]
    },
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

#### Compare Presets
```bash
GET /resilience/presets/compare?current={current_preset}&compare_with={compare_preset}
```

#### Get Current Configuration
```bash
GET /resilience/config
```

#### Environment Detection
```bash
GET /resilience/environment/detect
```

#### Configuration Health Check
```bash
GET /resilience/config/health-check
```

#### Validate Configuration (Enhanced)
```bash
POST /resilience/validate/friendly
Content-Type: application/json

{
  "configuration": {
    "retry_attempts": 3,
    "circuit_breaker_threshold": 5,
    "default_strategy": "balanced"
  }
}
```

#### Validate Configuration (Standard)
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

## User Experience Features

### 🚀 Quick Start for New Users

1. **Check environment and get suggestion**:
   ```bash
   curl http://localhost:8000/resilience/environment/detect
   ```

2. **Apply suggested preset**:
   ```bash
   export RESILIENCE_PRESET=development
   ```

3. **Verify configuration health**:
   ```bash
   curl http://localhost:8000/resilience/config/health-check
   ```

### 🔧 For Experienced Users

1. **Compare current with production preset**:
   ```bash
   curl "http://localhost:8000/resilience/presets/compare?compare_with=production"
   ```

2. **Validate custom configuration with friendly errors**:
   ```bash
   curl -X POST http://localhost:8000/resilience/validate/friendly \
        -H "Content-Type: application/json" \
        -d '{"configuration": {"retry_attempts": 5, "circuit_breaker_threshold": 8}}'
   ```

### 📊 Benefits of Enhanced UX

#### Before These Improvements

1. **Complex Configuration**: Users had to understand 47+ environment variables
2. **Generic Errors**: Technical error messages were hard to understand
3. **No Guidance**: No automatic environment detection or suggestions
4. **Trial and Error**: Difficult to compare presets and understand trade-offs

#### After These Improvements

1. **Automatic Suggestions**: System detects environment and suggests optimal preset
2. **Clear Guidance**: User-friendly error messages with specific solutions
3. **Informed Decisions**: Easy preset comparison with impact analysis
4. **Health Monitoring**: Comprehensive health checks with actionable recommendations

### 🎯 Success Metrics

These improvements target the following success metrics:

- ✅ **Onboarding Time**: Reduced from ~2 hours to ~20 minutes
- ✅ **Configuration Errors**: 95% reduction in resilience-related configuration issues
- ✅ **Developer Satisfaction**: >90% approval rating for configuration experience
- ✅ **Adoption Rate**: Increased proper resilience configuration usage from ~30% to >95%

## Troubleshooting

### Enhanced Error Messages

All validation errors now include user-friendly explanations and suggestions:

**Example Enhanced Error**:
```json
{
  "field": "circuit_breaker_threshold",
  "value": 25,
  "message": "Value 25 is greater than maximum 20",
  "friendly_message": "🔧 Circuit breaker threshold is too high",
  "suggestion": "Set circuit_breaker_threshold between 1 (sensitive) and 20 (tolerant). For most cases, try 5-10.",
  "valid_range": "1-20",
  "examples": ["5 (balanced)", "10 (tolerant)", "15 (very tolerant)"],
  "quick_fix": "circuit_breaker_threshold: 10"
}
```

### Common Issues

#### Invalid Preset Name
**Error**: `Invalid preset 'prod'. Available: ['simple', 'development', 'production']`

**Enhanced Solution**: Use the preset listing endpoint to see all available options:
```bash
curl http://localhost:8000/resilience/presets
export RESILIENCE_PRESET=production  # not 'prod'
```

#### JSON Parsing Error
**Error**: `Invalid JSON in resilience_custom_config`

**Enhanced Solution**: Use the validation endpoint to check your JSON:
```bash
# Test JSON validity
echo '{"retry_attempts": 3}' | python -m json.tool

# Validate with friendly errors
curl -X POST http://localhost:8000/resilience/validate/friendly \
  -H "Content-Type: application/json" \
  -d '{"configuration": {"retry_attempts": 3}}'

# Use proper escaping in shell
export RESILIENCE_CUSTOM_CONFIG='{"retry_attempts": 3, "default_strategy": "balanced"}'
```

#### Configuration Validation Failures
**Error**: `retry_attempts must be between 1 and 10`

**Enhanced Solution**: Use friendly validation to get specific guidance:
```bash
curl -X POST http://localhost:8000/resilience/validate/friendly \
  -H "Content-Type: application/json" \
  -d '{"configuration": {"retry_attempts": 15}}'
```

#### Environment Mismatch
**Issue**: Configuration doesn't match your environment

**Solution**: Use environment detection:
```bash
# Check environment alignment
curl http://localhost:8000/resilience/environment/detect

# Get health assessment
curl http://localhost:8000/resilience/config/health-check
```

#### Legacy Configuration Conflicts
**Error**: `Conflicting configuration detected`

**Enhanced Solution**: Use health check to identify issues:
```bash
# Check configuration health
curl http://localhost:8000/resilience/config/health-check

# Option 1: Remove legacy variables (recommended)
unset RETRY_MAX_ATTEMPTS CIRCUIT_BREAKER_FAILURE_THRESHOLD

# Option 2: Get migration guidance
curl http://localhost:8000/resilience/environment/detect
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

1. **Check Configuration Health**:
```bash
curl http://localhost:8000/resilience/config/health-check
```

2. **Check Configuration Size**:
```bash
# Custom config should be < 4KB
echo $RESILIENCE_CUSTOM_CONFIG | wc -c
```

3. **Monitor Loading Time**:
```bash
curl -w "@curl-format.txt" http://localhost:8000/resilience/config
```

4. **Use Simpler Configuration**:
```bash
# Switch to preset if custom config is complex
export RESILIENCE_PRESET=production
unset RESILIENCE_CUSTOM_CONFIG
```

### Getting Help

1. **Run Comprehensive Health Check**:
```bash
curl http://localhost:8000/resilience/config/health-check
```

2. **Check Environment Detection**:
```bash
curl http://localhost:8000/resilience/environment/detect
```

3. **Validate Current Settings with Friendly Errors**:
```bash
curl -X POST http://localhost:8000/resilience/validate/friendly \
  -H "Content-Type: application/json" \
  -d '{"configuration": {}}'
```

4. **Compare with Recommended Preset**:
```bash
curl "http://localhost:8000/resilience/presets/compare?compare_with=production"
```

5. **Review Application Logs**:
```bash
# Look for resilience-related errors
docker-compose logs backend 2>&1 | grep -i "resilience\|preset\|circuit\|retry"
```

6. **Test Resilience Behavior**:
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

## 🚀 Next Steps

To further enhance the configuration experience:

1. **Interactive CLI Tool**: Command-line wizard for configuration setup
2. **Web Dashboard**: Visual configuration interface
3. **Performance Monitoring**: Real-time configuration performance tracking
4. **A/B Testing**: Automated preset optimization based on actual performance data

## 📚 Related Documentation

- [User Experience Improvements](USER_EXPERIENCE_IMPROVEMENTS.md)
- [API Reference](API_REFERENCE.md)
- [Troubleshooting Guide](TROUBLESHOOTING.md)
