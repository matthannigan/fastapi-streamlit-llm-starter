---
sidebar_label: Configuration
---

# Cache Infrastructure Configuration Guide

The Cache Infrastructure Service provides flexible, production-ready configuration through a modern preset-based system that simplifies setup from 28+ environment variables to just 1-4 essential settings. This comprehensive guide covers all configuration aspects from quick setup to advanced customization.

## Quick Start

### Preset-Based Configuration (Recommended)

The modern approach uses presets to configure cache infrastructure with minimal environment variables:

```bash
# Choose your preset (this replaces 28+ individual variables)
CACHE_PRESET=development          # For local development
CACHE_PRESET=production           # For production web applications  
CACHE_PRESET=ai-production        # For AI-powered applications

# Optional overrides (only when needed)
CACHE_REDIS_URL=redis://localhost:6379    # Custom Redis connection
ENABLE_AI_CACHE=true                       # Toggle AI features
CACHE_CUSTOM_CONFIG='{"memory_cache_size": 500}'  # Advanced JSON overrides
```

### Configuration Comparison

**Legacy Approach (28+ variables)**:
```bash
CACHE_DEFAULT_TTL=3600
CACHE_MEMORY_CACHE_SIZE=200
CACHE_COMPRESSION_THRESHOLD=2000
CACHE_COMPRESSION_LEVEL=6
CACHE_TEXT_HASH_THRESHOLD=1000
CACHE_HASH_ALGORITHM=sha256
# ... 22+ more variables
```

**Modern Preset Approach (1-4 variables)**:
```bash
CACHE_PRESET=ai-production
CACHE_REDIS_URL=redis://redis:6379
ENABLE_AI_CACHE=true
```

**Result**: 96% reduction in configuration complexity while maintaining full customization capabilities.

## Available Presets

### Core Presets Overview

| Preset | Use Case | Redis Required | AI Features | Memory Cache | TTL Strategy |
|--------|----------|----------------|-------------|--------------|--------------|
| `disabled` | Testing, debugging | No | No | 10 entries | 5 minutes |
| `minimal` | Resource-constrained | Optional | No | 25 entries | 15 minutes |
| `simple` | Small applications | Optional | No | 100 entries | 1 hour |
| `development` | Local development | Recommended | Yes | 100 entries | 30 minutes |
| `production` | Web applications | Required | No | 500 entries | 2 hours |
| `ai-development` | AI development | Recommended | Yes | 200 entries | 30 minutes |
| `ai-production` | AI applications | Required | Yes | 1000 entries | 4 hours |

### Preset Detailed Specifications

#### `disabled` - Cache Completely Disabled

**Use Case**: Unit testing, minimal overhead scenarios, troubleshooting cache issues

**Configuration Details**:
- **Default TTL**: 300 seconds (5 minutes)
- **Memory Cache**: 10 entries maximum (minimal footprint)
- **Redis Connection**: Not used (memory-only operation)
- **Compression**: Minimal (level 1, threshold 10KB)
- **AI Features**: Disabled
- **Monitoring**: Disabled for maximum performance
- **Log Level**: WARNING (errors and warnings only)
- **Environment Contexts**: testing, minimal, troubleshooting

**When to Use**:
- Running comprehensive unit test suites
- Debugging cache-related application issues
- Extremely resource-constrained deployments (IoT, embedded systems)
- Temporary troubleshooting scenarios where cache might interfere

**Resource Usage**: ~2MB memory, no Redis connections

```bash
# Basic disabled configuration
CACHE_PRESET=disabled

# With custom overrides for testing
CACHE_PRESET=disabled
CACHE_CUSTOM_CONFIG='{"default_ttl": 60, "memory_cache_size": 5}'
```

#### `minimal` - Ultra-Lightweight Caching

**Use Case**: Edge computing, microservices, serverless functions, container environments with strict limits

**Configuration Details**:
- **Default TTL**: 900 seconds (15 minutes)
- **Memory Cache**: 25 entries maximum
- **Max Redis Connections**: 2 (minimal connection pool)
- **Connection Timeout**: 3 seconds (fast timeout to prevent hanging)
- **Compression**: Conservative (level 3, threshold 5KB)
- **AI Features**: Disabled for simplicity
- **Monitoring**: Basic logging only
- **Log Level**: ERROR (only critical errors logged)
- **Environment Contexts**: minimal, embedded, iot, container, serverless, edge

**When to Use**:
- Docker containers with memory constraints (<256MB)
- AWS Lambda or serverless functions
- Edge deployments with limited resources
- Microservices requiring minimal overhead
- Development environments with resource limitations

**Performance Characteristics**:
- Memory usage: ~5MB base, ~15MB peak
- Throughput: ~1,000 requests/second for small payloads
- Redis connections: 2 maximum
- Startup time: <1 second

```bash
# Minimal configuration for edge deployment
CACHE_PRESET=minimal
CACHE_REDIS_URL=redis://edge-redis:6379

# With custom connection settings
CACHE_PRESET=minimal
CACHE_CUSTOM_CONFIG='{"max_connections": 1, "connection_timeout": 2}'
```

#### `simple` - Basic General-Purpose Configuration

**Use Case**: Small web applications, API servers, prototypes, getting started quickly

**Configuration Details**:
- **Default TTL**: 3600 seconds (1 hour)
- **Memory Cache**: 100 entries
- **Max Redis Connections**: 5
- **Connection Timeout**: 5 seconds
- **Compression**: Balanced (level 6, threshold 1KB)
- **AI Features**: Disabled by default
- **Monitoring**: Enabled with basic metrics
- **Log Level**: INFO (standard operational logging)
- **Environment Contexts**: development, testing, staging, production

**When to Use**:
- General web applications without AI features
- RESTful API servers
- Content management systems
- E-commerce platforms (basic tier)
- Quick prototypes and proof-of-concepts
- Default choice for new projects

**Performance Characteristics**:
- Memory usage: ~20MB base, ~50MB peak
- Throughput: ~5,000 requests/second for small payloads, ~1,000 for large
- Cache hit ratio target: >70%
- Compression savings: 40-60% for typical web responses

```bash
# Simple web application configuration
CACHE_PRESET=simple
CACHE_REDIS_URL=redis://app-redis:6379

# With monitoring enhancements
CACHE_PRESET=simple
CACHE_CUSTOM_CONFIG='{"monitoring_enabled": true, "log_level": "DEBUG"}'
```

#### `development` - Development-Optimized Configuration

**Use Case**: Local development, feature testing, debugging cache behavior, development iteration

**Configuration Details**:
- **Default TTL**: 1800 seconds (30 minutes) - shorter for development cycles
- **Memory Cache**: 100 entries (balanced for development testing)
- **Max Redis Connections**: 5 (moderate for local development)
- **Connection Timeout**: 5 seconds
- **Compression**: Moderate (level 6, threshold 1KB)
- **AI Features**: Enabled for full feature development
- **Monitoring**: Full monitoring with DEBUG logging
- **Log Level**: DEBUG (detailed logging for development)
- **Environment Contexts**: development, local

**AI-Specific Development Settings**:
- **Text Hash Threshold**: 500 characters (lower for development)
- **Hash Algorithm**: sha256
- **Text Size Tiers**: small=500, medium=2000, large=10000
- **Operation TTLs**: 
  - summarize: 1800s (30 minutes)
  - sentiment: 900s (15 minutes)
  - key_points: 1200s (20 minutes)
  - questions: 1500s (25 minutes)
  - qa: 900s (15 minutes)
- **Smart Promotion**: Enabled
- **Max Text Length**: 50,000 characters

**When to Use**:
- Local development environment setup
- Testing AI feature integration
- Debugging cache behavior and key generation
- Development workflow with frequent code changes
- Learning and experimenting with cache features

**Development Features**:
- Detailed debug logging for troubleshooting
- Shorter TTLs for testing cache expiration
- AI features enabled for comprehensive development
- Memory-efficient for typical development machines

```bash
# Development environment with AI features
CACHE_PRESET=development
CACHE_REDIS_URL=redis://localhost:6379
ENABLE_AI_CACHE=true

# With custom development settings
CACHE_PRESET=development
CACHE_CUSTOM_CONFIG='{"default_ttl": 600, "log_level": "DEBUG"}'
```

#### `production` - High-Performance Production Configuration

**Use Case**: Production web applications, high-traffic APIs, general production workloads without heavy AI processing

**Configuration Details**:
- **Default TTL**: 7200 seconds (2 hours) - extended for production efficiency
- **Memory Cache**: 500 entries (large cache for high performance)
- **Max Redis Connections**: 20 (high connection pool for concurrency)
- **Connection Timeout**: 10 seconds (longer timeout for reliability)
- **Compression**: Optimized (level 6, threshold 1KB)
- **AI Features**: Disabled by default (use `ai-production` for AI workloads)
- **Monitoring**: Enabled with production metrics
- **Log Level**: INFO (production-appropriate logging)
- **Environment Contexts**: production, staging

**When to Use**:
- Production web applications and websites
- High-traffic REST APIs
- Content delivery and management systems
- E-commerce platforms (production tier)
- Business applications requiring high performance
- Staging environments that mirror production

**Performance Optimizations**:
- Large memory cache reduces Redis roundtrips
- High connection pool supports concurrent requests
- Optimized compression balances CPU vs storage
- Extended TTLs improve cache hit ratios
- Production-tuned monitoring and alerting

**Resource Characteristics**:
- Memory usage: ~100MB base, ~200MB peak
- Throughput: ~15,000 requests/second for small payloads, ~5,000 for large
- Redis connections: 20 maximum
- Target cache hit ratio: >80%

```bash
# Production web application
CACHE_PRESET=production
CACHE_REDIS_URL=redis://prod-cache:6379

# High-traffic production with custom tuning
CACHE_PRESET=production
CACHE_CUSTOM_CONFIG='{"max_connections": 30, "memory_cache_size": 1000, "compression_level": 8}'
```

#### `ai-development` - AI Application Development

**Use Case**: Developing AI-powered applications locally, testing text processing features, AI experimentation

**Configuration Details**:
- **Default TTL**: 1800 seconds (30 minutes) - development-friendly
- **Memory Cache**: 200 entries (optimized for AI data structures)
- **Max Redis Connections**: 5
- **Connection Timeout**: 5 seconds
- **Compression**: Balanced (level 6, threshold 1KB)
- **AI Features**: Fully enabled with development-friendly settings
- **Monitoring**: Full AI-specific monitoring with DEBUG logging
- **Log Level**: DEBUG (detailed AI operation logging)
- **Environment Contexts**: development, ai-development

**AI-Specific Configuration**:
- **Text Hash Threshold**: 500 characters (development-optimized)
- **Hash Algorithm**: sha256 (secure and consistent)
- **Text Size Tiers**: 
  - small: 500 characters (short prompts, quick responses)
  - medium: 2000 characters (typical AI conversations)
  - large: 10000 characters (long-form content)
- **Operation-Specific TTLs** (development-optimized):
  - summarize: 1800s (30 minutes) - frequent content changes
  - sentiment: 900s (15 minutes) - rapid iteration
  - key_points: 1200s (20 minutes) - moderate stability
  - questions: 1500s (25 minutes) - context development
  - qa: 900s (15 minutes) - frequent Q&A testing
- **Smart Promotion**: Enabled (automatic L1 cache optimization)
- **Max Text Length**: 50,000 characters (development limits)

**When to Use**:
- Developing AI-powered applications and features
- Testing text processing and NLP workflows
- Local AI model integration and testing
- Experimenting with different AI operations
- Debugging AI response caching strategies

**AI Development Features**:
- Comprehensive AI operation logging
- Development-appropriate TTLs for rapid iteration
- Full text processing tier analysis
- Smart cache key generation for AI content
- Enhanced debugging information for AI workflows

```bash
# AI application development
CACHE_PRESET=ai-development
CACHE_REDIS_URL=redis://localhost:6379
GEMINI_API_KEY=your-development-api-key

# With custom AI development settings
CACHE_PRESET=ai-development
CACHE_CUSTOM_CONFIG='{"text_hash_threshold": 300, "max_text_length": 25000}'
```

#### `ai-production` - Production AI Workloads

**Use Case**: Production AI applications, high-volume text processing systems, AI-powered APIs, enterprise AI services

**Configuration Details**:
- **Default TTL**: 14400 seconds (4 hours) - optimized for AI efficiency
- **Memory Cache**: 1000 entries (large cache for AI datasets)
- **Max Redis Connections**: 25 (high pool for AI workloads)
- **Connection Timeout**: 15 seconds (extended for AI operations)
- **Compression**: Maximum efficiency (level 9, threshold 300 bytes)
- **AI Features**: Fully enabled with production optimizations
- **Monitoring**: Production AI monitoring with comprehensive metrics
- **Log Level**: INFO (production-appropriate with AI insights)
- **Environment Contexts**: production, ai-production

**Production AI Configuration**:
- **Text Hash Threshold**: 1000 characters (production-optimized)
- **Hash Algorithm**: sha256 (cryptographically secure)
- **Text Size Tiers** (production-optimized):
  - small: 1000 characters (short business content)
  - medium: 5000 characters (typical documents)
  - large: 25000 characters (long-form content, reports)
- **Operation-Specific TTLs** (production-optimized):
  - summarize: 14400s (4 hours) - summaries are stable
  - sentiment: 7200s (2 hours) - sentiment rarely changes
  - key_points: 10800s (3 hours) - key points are stable
  - questions: 9600s (2.67 hours) - question generation stable
  - qa: 7200s (2 hours) - Q&A responses moderately stable
- **Smart Promotion**: Enabled with advanced algorithms
- **Max Text Length**: 200,000 characters (enterprise-scale)

**When to Use**:
- Production AI applications and services
- High-volume text processing systems
- Enterprise AI platforms
- AI-powered APIs with performance requirements
- Large-scale content analysis applications
- Business intelligence and analytics platforms

**Production AI Optimizations**:
- Extended TTLs for expensive AI operations
- Large text processing capabilities for enterprise content
- Advanced smart promotion strategies for optimal performance
- Maximum compression for storage efficiency
- High connection pools for concurrent AI workloads
- Comprehensive monitoring for AI-specific metrics

**Resource Characteristics**:
- Memory usage: ~200MB base, ~500MB peak
- Throughput: ~12,000 requests/second for small payloads, ~4,000 for large
- AI operations: ~500 operations/second
- Redis connections: 25 maximum
- Target cache hit ratio: >85% for AI operations

```bash
# Production AI application
CACHE_PRESET=ai-production
CACHE_REDIS_URL=redis://ai-prod-cache:6379
GEMINI_API_KEY=your-production-api-key

# High-volume AI production with custom optimization
CACHE_PRESET=ai-production
CACHE_CUSTOM_CONFIG='{
  "max_connections": 50,
  "memory_cache_size": 2000,
  "operation_ttls": {
    "summarize": 28800,
    "custom_ai_operation": 3600
  },
  "text_size_tiers": {
    "small": 2000,
    "medium": 10000,
    "large": 100000
  }
}'
```

## Preset Selection Guide

### Decision Tree for Preset Selection

**Step 1: Identify Application Type**
```
Do you need AI features (text processing, LLM integration)?
├─ Yes → Go to Step 2 (AI Applications)
└─ No → Go to Step 3 (General Applications)
```

**Step 2: AI Applications**
```
What is your deployment environment?
├─ Development/Testing → ai-development
├─ Production → ai-production
└─ Resource-Constrained → minimal (with ENABLE_AI_CACHE=true)
```

**Step 3: General Applications**
```
What is your deployment context?
├─ Testing/Debugging → disabled
├─ Resource-Constrained (< 256MB RAM) → minimal
├─ Quick Prototype → simple
├─ Development Environment → development
├─ Production Environment → production
└─ High-Performance Production → production (with custom config)
```

### Use Case Matrix

| Application Type | Primary Preset | Alternative | Development | Production |
|------------------|----------------|-------------|-------------|------------|
| **Simple Web App** | `simple` | `development` | `development` | `production` |
| **REST API** | `simple` | `production` | `development` | `production` |
| **AI Text Processing** | `ai-development` | `ai-production` | `ai-development` | `ai-production` |
| **Content Management** | `production` | `simple` | `development` | `production` |
| **E-commerce** | `production` | `simple` | `development` | `production` |
| **Microservices** | `minimal` | `simple` | `development` | `minimal` or `simple` |
| **IoT/Edge Computing** | `minimal` | `disabled` | `minimal` | `minimal` |
| **Analytics/ML** | `ai-production` | `ai-development` | `ai-development` | `ai-production` |
| **Enterprise AI** | `ai-production` | N/A | `ai-development` | `ai-production` |

### Environment-Specific Recommendations

| Environment | General Apps | AI Apps | Resource-Constrained | Testing |
|-------------|--------------|---------|---------------------|---------|
| **Local Development** | `development` | `ai-development` | `minimal` | `disabled` |
| **CI/CD Pipeline** | `disabled` | `disabled` | `disabled` | `disabled` |
| **Staging** | `production` | `ai-production` | `simple` | `simple` |
| **Production** | `production` | `ai-production` | `minimal` | `production` |
| **Edge/Serverless** | `minimal` | `minimal` | `minimal` | `minimal` |

### Resource Requirements by Preset

| Preset | Memory Usage | CPU Usage | Redis Connections | Startup Time | Throughput (req/s) |
|--------|-------------|-----------|-------------------|--------------|-------------------|
| `disabled` | 2-5MB | Minimal | 0 | Instant | 10,000+ |
| `minimal` | 5-15MB | Low | 2 | <1s | 1,000 |
| `simple` | 20-50MB | Low | 5 | 1-2s | 5,000 |
| `development` | 30-80MB | Medium | 5 | 2-3s | 3,000 |
| `production` | 100-200MB | Medium | 20 | 3-5s | 15,000 |
| `ai-development` | 50-150MB | High | 5 | 3-5s | 2,000 |
| `ai-production` | 200-500MB | High | 25 | 5-10s | 12,000 |

## Configuration Override Patterns

### Essential Environment Variables

The preset system uses a minimal set of environment variables for maximum impact:

| Variable | Type | Purpose | Example | Required |
|----------|------|---------|---------|----------|
| `CACHE_PRESET` | string | Preset selection | `"ai-production"` | Yes |
| `CACHE_REDIS_URL` | string | Redis connection override | `redis://redis:6379` | Optional |
| `ENABLE_AI_CACHE` | boolean | AI features toggle | `true` | Optional |
| `CACHE_CUSTOM_CONFIG` | JSON | Advanced customization | `{"memory_cache_size": 500}` | Optional |

### Override Precedence

The configuration system follows this precedence hierarchy:

1. **`CACHE_CUSTOM_CONFIG`** - JSON overrides (highest priority)
2. **Essential environment variables** - `CACHE_REDIS_URL`, `ENABLE_AI_CACHE`
3. **Preset defaults** - Configuration from chosen preset (lowest priority)

### Common Override Scenarios

#### Scenario 1: Production with Custom Redis

```bash
# Use production preset with dedicated cache Redis
CACHE_PRESET=production
CACHE_REDIS_URL=redis://cache-cluster:6379
```

#### Scenario 2: Development with Enhanced Memory

```bash
# Development preset with larger memory cache
CACHE_PRESET=development
CACHE_CUSTOM_CONFIG='{"memory_cache_size": 300, "default_ttl": 600}'
```

#### Scenario 3: AI Production with Security

```bash
# AI production with TLS and authentication
CACHE_PRESET=ai-production
CACHE_REDIS_URL=rediss://secure-ai-cache:6380
CACHE_CUSTOM_CONFIG='{
  "use_tls": true,
  "redis_password": "secure_password",
  "max_connections": 50
}'
```

#### Scenario 4: Multi-Environment Configuration

```bash
# Environment-aware configuration using shell variables
CACHE_PRESET=${ENVIRONMENT:-development}
CACHE_REDIS_URL=${CACHE_REDIS_URL:-redis://localhost:6379}
ENABLE_AI_CACHE=${ENABLE_AI_CACHE:-true}
```

### Advanced JSON Configuration

The `CACHE_CUSTOM_CONFIG` variable accepts JSON for complex overrides:

#### Performance Tuning
```bash
CACHE_CUSTOM_CONFIG='{
  "memory_cache_size": 1000,
  "max_connections": 50,
  "compression_level": 8,
  "compression_threshold": 500,
  "default_ttl": 5400
}'
```

#### AI-Specific Customization
```bash
CACHE_CUSTOM_CONFIG='{
  "text_hash_threshold": 2000,
  "max_text_length": 150000,
  "operation_ttls": {
    "summarize": 7200,
    "sentiment": 14400,
    "custom_operation": 3600
  },
  "text_size_tiers": {
    "small": 2000,
    "medium": 10000,
    "large": 50000
  }
}'
```

#### Security Configuration
```bash
CACHE_CUSTOM_CONFIG='{
  "use_tls": true,
  "redis_password": "secure_password",
  "tls_cert_path": "/certs/redis-client.crt",
  "tls_key_path": "/certs/redis-client.key",
  "redis_username": "cache_user"
}'
```

#### Development and Debugging
```bash
CACHE_CUSTOM_CONFIG='{
  "log_level": "DEBUG",
  "monitoring_enabled": true,
  "default_ttl": 300,
  "enable_smart_promotion": false
}'
```

## Environment Variables Reference

### Core Configuration Variables

| Variable | Type | Default | Description | Example |
|----------|------|---------|-------------|---------|
| `CACHE_PRESET` | string | `"development"` | Cache preset name | `"production"` |
| `CACHE_REDIS_URL` | string | `None` | Override Redis connection | `redis://redis:6379` |
| `ENABLE_AI_CACHE` | boolean | `None` | Override AI features | `true` |
| `CACHE_CUSTOM_CONFIG` | JSON | `None` | Advanced customization | See examples above |

### Preset-Specific Defaults

Each preset provides sensible defaults for all configuration parameters:

#### Core Settings (All Presets)
| Setting | disabled | minimal | simple | development | production | ai-development | ai-production |
|---------|----------|---------|---------|-------------|------------|----------------|---------------|
| **default_ttl** | 300s | 900s | 3600s | 1800s | 7200s | 1800s | 14400s |
| **memory_cache_size** | 10 | 25 | 100 | 100 | 500 | 200 | 1000 |
| **max_connections** | 0 | 2 | 5 | 5 | 20 | 5 | 25 |
| **compression_level** | 1 | 3 | 6 | 6 | 6 | 6 | 9 |
| **compression_threshold** | 10000 | 5000 | 1000 | 1000 | 1000 | 1000 | 300 |
| **log_level** | WARNING | ERROR | INFO | DEBUG | INFO | DEBUG | INFO |

#### AI-Specific Settings (AI Presets)
| Setting | ai-development | ai-production |
|---------|----------------|---------------|
| **text_hash_threshold** | 500 | 1000 |
| **max_text_length** | 50000 | 200000 |
| **hash_algorithm** | sha256 | sha256 |
| **enable_smart_promotion** | true | true |

#### Text Size Tiers
| Tier | ai-development | ai-production |
|------|----------------|---------------|
| **small** | 500 | 1000 |
| **medium** | 2000 | 5000 |
| **large** | 10000 | 25000 |

#### Operation TTLs (AI Presets)
| Operation | ai-development | ai-production |
|-----------|----------------|---------------|
| **summarize** | 1800s | 14400s |
| **sentiment** | 900s | 7200s |
| **key_points** | 1200s | 10800s |
| **questions** | 1500s | 9600s |
| **qa** | 900s | 7200s |

## Redis Configuration

### Redis Connection Management

The cache infrastructure supports flexible Redis configuration patterns:

#### Basic Redis Configuration
```bash
# Simple Redis connection
CACHE_REDIS_URL=redis://localhost:6379

# Redis with database selection
CACHE_REDIS_URL=redis://localhost:6379/1

# Redis with authentication
CACHE_REDIS_URL=redis://:password@redis:6379
CACHE_REDIS_URL=redis://username:password@redis:6379
```

#### Secure Redis Configuration
```bash
# TLS-enabled Redis
CACHE_REDIS_URL=rediss://secure-redis:6380

# Redis with custom security via JSON config
CACHE_PRESET=production
CACHE_REDIS_URL=rediss://secure-redis:6380
CACHE_CUSTOM_CONFIG='{
  "use_tls": true,
  "redis_password": "secure_password",
  "tls_cert_path": "/certs/client.crt",
  "tls_key_path": "/certs/client.key",
  "tls_ca_cert_path": "/certs/ca.crt"
}'
```

#### Redis Cluster Configuration
```bash
# Redis cluster with multiple endpoints
CACHE_REDIS_URL=redis://node1:6379,node2:6379,node3:6379

# Cluster with custom configuration
CACHE_CUSTOM_CONFIG='{
  "redis_cluster_nodes": [
    "redis://node1:6379",
    "redis://node2:6379", 
    "redis://node3:6379"
  ],
  "cluster_mode": true,
  "max_connections_per_node": 10
}'
```

### Connection Pool Settings

Different presets provide different connection pool configurations:

| Setting | Development | Production | AI Production |
|---------|-------------|------------|---------------|
| **Max Connections** | 5 | 20 | 25 |
| **Connection Timeout** | 5s | 10s | 15s |
| **Socket Timeout** | 5s | 5s | 10s |
| **Retry Strategy** | Basic | Advanced | Advanced |
| **Health Checks** | Basic | Comprehensive | Comprehensive |

### Redis Security Best Practices

#### Authentication Configuration
```bash
# Username/password authentication
CACHE_CUSTOM_CONFIG='{
  "redis_username": "cache_user",
  "redis_password": "secure_password_from_secrets"
}'
```

#### TLS Configuration
```bash
# Full TLS configuration
CACHE_CUSTOM_CONFIG='{
  "use_tls": true,
  "tls_cert_path": "/etc/ssl/certs/redis-client.crt",
  "tls_key_path": "/etc/ssl/private/redis-client.key",
  "tls_ca_cert_path": "/etc/ssl/certs/redis-ca.crt",
  "tls_check_hostname": true
}'
```

#### Network Security
```bash
# Private network configuration
CACHE_REDIS_URL=redis://internal-cache.vpc:6379
CACHE_CUSTOM_CONFIG='{
  "connection_timeout": 30,
  "socket_timeout": 30,
  "socket_keepalive": true,
  "socket_keepalive_options": {}
}'
```

## Configuration Builder Patterns

### Programmatic Configuration

For advanced use cases, you can configure the cache system programmatically:

#### Basic Builder Pattern
```python
from app.infrastructure.cache.config import CacheConfigBuilder

# Build configuration from preset
config = CacheConfigBuilder().from_preset("production").build()

# Build with environment overrides
config = CacheConfigBuilder().from_environment().build()

# Build from file
config = CacheConfigBuilder().from_file("cache_config.json").build()
```

#### Advanced Builder Configuration
```python
from app.infrastructure.cache.config import CacheConfigBuilder

# Combine multiple sources
config = (CacheConfigBuilder()
    .from_preset("ai-production")
    .with_redis_url("redis://custom-redis:6379")
    .with_ai_enabled(True)
    .with_custom_config({
        "memory_cache_size": 1500,
        "compression_level": 8,
        "operation_ttls": {
            "summarize": 7200,
            "sentiment": 3600
        }
    })
    .build())
```

#### Dynamic Configuration
```python
import os
from app.infrastructure.cache.config import CacheConfigBuilder

# Environment-aware configuration
def create_cache_config():
    environment = os.getenv("ENVIRONMENT", "development")
    
    builder = CacheConfigBuilder()
    
    if environment == "production":
        builder.from_preset("ai-production")
        builder.with_redis_url(os.getenv("PROD_REDIS_URL"))
    elif environment == "staging":
        builder.from_preset("production")
        builder.with_redis_url(os.getenv("STAGING_REDIS_URL"))
    else:
        builder.from_preset("development")
        builder.with_redis_url("redis://localhost:6379")
    
    return builder.build()
```

### Configuration Validation

The builder provides comprehensive validation:

```python
from app.infrastructure.cache.config import CacheConfigBuilder
from app.core.exceptions import ConfigurationError

try:
    config = CacheConfigBuilder().from_environment().build()
    print("✅ Configuration is valid")
except ConfigurationError as e:
    print(f"❌ Configuration error: {e}")
    print(f"📝 Context: {e.context}")
```

#### Validation Results
```python
# Get validation without building
builder = CacheConfigBuilder().from_preset("production")
validation_result = builder.validate()

if validation_result.is_valid:
    print("Configuration is valid")
    config = builder.build()
else:
    print("Validation errors:")
    for error in validation_result.errors:
        print(f"  - {error}")
```

## Environment-Specific Configuration

### Development Environment

#### Local Development Setup
```bash
# .env.development
CACHE_PRESET=development
CACHE_REDIS_URL=redis://localhost:6379
ENABLE_AI_CACHE=true
GEMINI_API_KEY=your-development-api-key

# Optional development customizations
CACHE_CUSTOM_CONFIG='{
  "log_level": "DEBUG",
  "default_ttl": 600,
  "memory_cache_size": 50
}'
```

#### Development Docker Compose
```yaml
# docker-compose.dev.yml
services:
  backend:
    environment:
      - CACHE_PRESET=${CACHE_PRESET:-development}
      - CACHE_REDIS_URL=redis://redis:6379
      - ENABLE_AI_CACHE=${ENABLE_AI_CACHE:-true}
    depends_on:
      - redis

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
```

### Testing Environment

#### Test Configuration
```bash
# .env.testing
CACHE_PRESET=disabled
TEST_REDIS_URL=redis://localhost:6379/15

# For integration tests
CACHE_PRESET=minimal
CACHE_REDIS_URL=redis://localhost:6379/14
CACHE_CUSTOM_CONFIG='{"default_ttl": 60, "memory_cache_size": 10}'
```

#### CI/CD Configuration
```yaml
# .github/workflows/test.yml
env:
  CACHE_PRESET: disabled
  TEST_REDIS_URL: redis://localhost:6379/15
  
services:
  redis:
    image: redis:7-alpine
    options: >-
      --health-cmd "redis-cli ping"
      --health-interval 10s
      --health-timeout 5s
      --health-retries 5
```

### Staging Environment

#### Staging Configuration
```bash
# .env.staging
CACHE_PRESET=production
CACHE_REDIS_URL=redis://staging-cache:6379
ENABLE_AI_CACHE=true

# Mirror production with reduced resources
CACHE_CUSTOM_CONFIG='{
  "memory_cache_size": 200,
  "max_connections": 10
}'
```

#### Kubernetes Staging
```yaml
# k8s-staging-configmap.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: cache-config-staging
data:
  CACHE_PRESET: "production"
  CACHE_REDIS_URL: "redis://staging-cache:6379"
  ENABLE_AI_CACHE: "true"
  CACHE_CUSTOM_CONFIG: |
    {
      "memory_cache_size": 200,
      "max_connections": 10,
      "log_level": "INFO"
    }
```

### Production Environment

#### Production Configuration
```bash
# .env.production
CACHE_PRESET=ai-production
CACHE_REDIS_URL=redis://prod-cache-cluster:6379
ENABLE_AI_CACHE=true

# Production-specific optimizations
CACHE_CUSTOM_CONFIG='{
  "max_connections": 50,
  "memory_cache_size": 2000,
  "use_tls": true,
  "redis_password": "secure_password_from_vault"
}'
```

#### Production Docker Compose
```yaml
# docker-compose.prod.yml
services:
  backend:
    environment:
      - CACHE_PRESET=${CACHE_PRESET:-ai-production}
      - CACHE_REDIS_URL=${CACHE_REDIS_URL}
      - ENABLE_AI_CACHE=${ENABLE_AI_CACHE:-true}
      - CACHE_CUSTOM_CONFIG=${CACHE_CUSTOM_CONFIG:-'{}'}
    secrets:
      - cache_redis_password
    volumes:
      - ./certs:/certs:ro

secrets:
  cache_redis_password:
    external: true
```

#### Kubernetes Production
```yaml
# k8s-prod-deployment.yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend-deployment
spec:
  template:
    spec:
      containers:
      - name: backend
        env:
        - name: CACHE_PRESET
          value: "ai-production"
        - name: CACHE_REDIS_URL
          valueFrom:
            secretKeyRef:
              name: redis-secret
              key: url
        - name: ENABLE_AI_CACHE
          value: "true"
        - name: CACHE_CUSTOM_CONFIG
          valueFrom:
            configMapKeyRef:
              name: cache-config
              key: custom-config
```

## Custom Configuration

### Creating Custom Configurations

For specialized use cases, you can create entirely custom configurations:

#### Custom AI Configuration
```python
# custom_ai_config.py
from app.infrastructure.cache.config import CacheConfigBuilder

def create_custom_ai_config():
    return (CacheConfigBuilder()
        .from_preset("ai-production")
        .with_custom_config({
            # Custom text processing tiers for legal documents
            "text_size_tiers": {
                "brief": 2000,      # Legal briefs
                "contract": 10000,  # Contracts
                "document": 50000,  # Full legal documents
                "corpus": 200000    # Large legal corpus
            },
            # Legal-specific operation TTLs
            "operation_ttls": {
                "legal_summarize": 28800,    # 8 hours
                "contract_analysis": 14400,  # 4 hours
                "compliance_check": 7200,    # 2 hours
                "legal_qa": 3600            # 1 hour
            },
            # Enhanced security for legal data
            "text_hash_threshold": 100,  # Hash almost everything
            "max_text_length": 500000,   # Large legal documents
            "compression_level": 9       # Maximum compression
        })
        .build())
```

#### Custom Performance Configuration
```python
# high_performance_config.py
def create_high_performance_config():
    return (CacheConfigBuilder()
        .from_preset("production")
        .with_custom_config({
            # Maximum performance settings
            "memory_cache_size": 5000,
            "max_connections": 100,
            "compression_threshold": 10000,  # Less compression
            "compression_level": 1,          # Fastest compression
            "default_ttl": 28800,           # 8 hour TTL
            
            # Connection optimization
            "connection_timeout": 1,
            "socket_timeout": 1,
            "connection_pool_retry_attempts": 5,
            
            # Monitoring settings
            "monitoring_enabled": True,
            "metrics_collection_interval": 10
        })
        .build())
```

### Environment-Specific Customization

#### Multi-Tenant Configuration
```python
# multi_tenant_config.py
import os

def create_tenant_config(tenant_id: str):
    base_preset = os.getenv("BASE_CACHE_PRESET", "production")
    
    return (CacheConfigBuilder()
        .from_preset(base_preset)
        .with_redis_url(f"redis://tenant-{tenant_id}-cache:6379")
        .with_custom_config({
            "key_prefix": f"tenant:{tenant_id}:",
            "memory_cache_size": 100,  # Per-tenant memory cache
            "default_ttl": 3600,       # Tenant-specific TTL
            
            # Tenant isolation
            "redis_db": hash(tenant_id) % 16,  # Distribute across DBs
            
            # Tenant-specific AI settings
            "operation_ttls": {
                f"tenant_{tenant_id}_summarize": 7200,
                f"tenant_{tenant_id}_analysis": 3600
            }
        })
        .build())
```

#### Geographic Configuration
```python
# geo_config.py
def create_geo_config(region: str):
    region_configs = {
        "us-east": {
            "redis_url": "redis://us-east-cache:6379",
            "max_connections": 50,
            "connection_timeout": 5
        },
        "eu-west": {
            "redis_url": "redis://eu-west-cache:6379", 
            "max_connections": 30,
            "connection_timeout": 10  # Higher latency
        },
        "ap-south": {
            "redis_url": "redis://ap-south-cache:6379",
            "max_connections": 20,
            "connection_timeout": 15  # Highest latency
        }
    }
    
    config = region_configs.get(region, region_configs["us-east"])
    
    return (CacheConfigBuilder()
        .from_preset("ai-production")
        .with_redis_url(config["redis_url"])
        .with_custom_config({
            "max_connections": config["max_connections"],
            "connection_timeout": config["connection_timeout"],
            "region": region,
            "key_prefix": f"region:{region}:"
        })
        .build())
```

## Configuration Validation

### Built-in Validation

The configuration system provides comprehensive validation:

#### Validation Categories
1. **Required Fields**: Ensures essential configuration is present
2. **Type Validation**: Validates data types and ranges
3. **Dependency Validation**: Checks for conflicting or missing dependencies
4. **Resource Validation**: Validates resource constraints and limits
5. **Security Validation**: Ensures secure configuration practices

#### Validation Example
```python
from app.infrastructure.cache.config import CacheConfigBuilder, ValidationError

def validate_configuration():
    try:
        builder = CacheConfigBuilder().from_environment()
        
        # Validate without building
        result = builder.validate()
        
        if result.is_valid:
            print("✅ Configuration is valid")
            if result.warnings:
                print("⚠️  Warnings:")
                for warning in result.warnings:
                    print(f"  - {warning}")
        else:
            print("❌ Configuration is invalid")
            print("🚨 Errors:")
            for error in result.errors:
                print(f"  - {error}")
            return False
            
        # Build configuration (additional validation)
        config = builder.build()
        return True
        
    except ValidationError as e:
        print(f"❌ Validation error: {e}")
        return False
```

### Common Validation Issues

#### Invalid Preset Names
```python
# ❌ Invalid preset
CACHE_PRESET=prodcution  # Typo

# ✅ Valid preset  
CACHE_PRESET=production
```

#### Invalid Redis URLs
```python
# ❌ Invalid URLs
CACHE_REDIS_URL=localhost:6379          # Missing protocol
CACHE_REDIS_URL=redis://invalid:host    # Invalid hostname

# ✅ Valid URLs
CACHE_REDIS_URL=redis://localhost:6379
CACHE_REDIS_URL=rediss://secure-redis:6380
```

#### Invalid JSON Configuration
```python
# ❌ Invalid JSON
CACHE_CUSTOM_CONFIG='{memory_cache_size: 100}'  # Unquoted keys

# ✅ Valid JSON
CACHE_CUSTOM_CONFIG='{"memory_cache_size": 100}'
```

#### Resource Constraint Violations
```python
# ❌ Invalid ranges
CACHE_CUSTOM_CONFIG='{
  "memory_cache_size": -10,      # Negative value
  "max_connections": 1000,       # Excessive connections
  "compression_level": 15        # Invalid compression level
}'

# ✅ Valid ranges
CACHE_CUSTOM_CONFIG='{
  "memory_cache_size": 100,      # Positive value
  "max_connections": 50,         # Reasonable limit
  "compression_level": 6         # Valid range (1-9)
}'
```

### Validation Scripts

#### Configuration Validation Script
```bash
#!/bin/bash
# validate_cache_config.sh

echo "🔍 Validating cache configuration..."

# Check required environment variables
if [ -z "$CACHE_PRESET" ]; then
    echo "❌ CACHE_PRESET is required"
    exit 1
fi

# Validate preset name
valid_presets=("disabled" "minimal" "simple" "development" "production" "ai-development" "ai-production")
if [[ ! " ${valid_presets[@]} " =~ " ${CACHE_PRESET} " ]]; then
    echo "❌ Invalid CACHE_PRESET: $CACHE_PRESET"
    echo "   Valid presets: ${valid_presets[*]}"
    exit 1
fi

# Validate JSON configuration
if [ ! -z "$CACHE_CUSTOM_CONFIG" ]; then
    echo "$CACHE_CUSTOM_CONFIG" | jq . > /dev/null
    if [ $? -ne 0 ]; then
        echo "❌ Invalid JSON in CACHE_CUSTOM_CONFIG"
        exit 1
    fi
fi

echo "✅ Basic validation passed"

# Run Python validation
python -c "
from app.infrastructure.cache.config import CacheConfigBuilder
try:
    config = CacheConfigBuilder().from_environment().build()
    print('✅ Full validation passed')
except Exception as e:
    print(f'❌ Validation failed: {e}')
    exit(1)
"
```

## Management and Monitoring

### Configuration Management Commands

The cache system provides several management commands:

#### Preset Management
```bash
# List all available presets
make list-cache-presets

# Show detailed preset configuration
make show-cache-preset PRESET=production
make show-cache-preset PRESET=ai-production

# Show all presets summary
make show-cache-preset PRESET=all
```

#### Configuration Validation
```bash
# Validate current configuration
make validate-cache-config

# Validate specific preset
make validate-cache-preset PRESET=ai-production

# Get configuration recommendations
make recommend-cache-preset ENV=production
make recommend-cache-preset ENV=staging
```

### Configuration Monitoring

#### Health Check Endpoints
```bash
# Check cache health and configuration
curl http://localhost:8000/internal/cache/health

# Get current configuration
curl http://localhost:8000/internal/cache/config

# Get cache metrics
curl http://localhost:8000/internal/cache/metrics
```

#### Monitoring Configuration
```bash
# Enable detailed monitoring
CACHE_CUSTOM_CONFIG='{"monitoring_enabled": true, "metrics_collection_interval": 30}'

# Monitor specific metrics
CACHE_CUSTOM_CONFIG='{"monitor_hit_ratios": true, "monitor_memory_usage": true, "monitor_compression_ratios": true}'
```

### Configuration Updates

#### Runtime Configuration Updates
```python
from app.infrastructure.cache.config import CacheConfigBuilder
from app.infrastructure.cache.dependencies import get_cache_service

async def update_cache_config():
    # Build new configuration
    new_config = (CacheConfigBuilder()
        .from_preset("ai-production")
        .with_custom_config({
            "memory_cache_size": 1500,
            "default_ttl": 10800
        })
        .build())
    
    # Update cache service (requires restart)
    # This is typically done during deployment
    cache_service = await get_cache_service()
    await cache_service.update_config(new_config)
```

#### Configuration Rollback
```bash
# Save current configuration
make save-cache-config --output cache_config_backup.json

# Apply new configuration
CACHE_PRESET=ai-production make restart-backend

# Rollback if needed
make restore-cache-config --input cache_config_backup.json
```

## Troubleshooting Configuration Issues

### Common Configuration Problems

#### Issue 1: Unknown Preset Error
```
ConfigurationError: Unknown preset 'prodcution'
```

**Solution**:
```bash
# Check available presets
make list-cache-presets

# Fix typo
CACHE_PRESET=production  # Not 'prodcution'
```

#### Issue 2: Invalid JSON Configuration
```
ConfigurationError: Invalid JSON in CACHE_CUSTOM_CONFIG
```

**Solution**:
```bash
# Check JSON syntax
echo $CACHE_CUSTOM_CONFIG | jq .

# Fix JSON (common issues)
# ❌ Unquoted keys
CACHE_CUSTOM_CONFIG='{memory_cache_size: 100}'

# ✅ Quoted keys
CACHE_CUSTOM_CONFIG='{"memory_cache_size": 100}'
```

#### Issue 3: Redis Connection Failures
```
WARNING Cache: Redis connection failed, using memory-only mode
```

**Solution**:
```bash
# Test Redis connectivity
redis-cli -h redis-host -p 6379 ping

# Check Redis URL format
CACHE_REDIS_URL=redis://localhost:6379  # ✅ Correct
CACHE_REDIS_URL=localhost:6379         # ❌ Missing protocol

# Verify authentication
CACHE_REDIS_URL=redis://:password@redis:6379
```

#### Issue 4: High Memory Usage
```
WARNING Cache: Memory usage exceeded threshold: 150MB
```

**Solution**:
```bash
# Reduce memory cache size
CACHE_CUSTOM_CONFIG='{"memory_cache_size": 50}'

# Enable aggressive compression
CACHE_CUSTOM_CONFIG='{"compression_threshold": 500, "compression_level": 9}'

# Reduce TTL values
CACHE_CUSTOM_CONFIG='{"default_ttl": 1800}'
```

#### Issue 5: Poor Cache Hit Rates
```
Cache hit rate: 25% (Expected: >70%)
```

**Solution**:
```bash
# Increase TTL values
CACHE_CUSTOM_CONFIG='{"default_ttl": 7200}'

# Optimize AI operation TTLs
CACHE_CUSTOM_CONFIG='{
  "operation_ttls": {
    "summarize": 14400,
    "sentiment": 86400
  }
}'

# Lower text hash threshold for better consistency
CACHE_CUSTOM_CONFIG='{"text_hash_threshold": 300}'
```

### Debug Configuration

#### Debug Mode Configuration
```bash
# Enable comprehensive debugging
CACHE_PRESET=development
CACHE_CUSTOM_CONFIG='{
  "log_level": "DEBUG",
  "monitoring_enabled": true,
  "debug_key_generation": true,
  "debug_compression": true
}'
```

#### Configuration Inspection Tools
```python
# Inspect current configuration
from app.infrastructure.cache.dependencies import get_cache_config

async def inspect_config():
    config = await get_cache_config()
    
    print(f"Preset: {config.preset}")
    print(f"Redis URL: {config.redis_url}")
    print(f"Memory cache size: {config.memory_cache_size}")
    print(f"AI enabled: {config.ai_config is not None}")
    
    if config.ai_config:
        print(f"Text hash threshold: {config.ai_config.text_hash_threshold}")
        print(f"Operation TTLs: {config.ai_config.operation_ttls}")
```

### Performance Troubleshooting

#### Performance Analysis
```bash
# Analyze cache performance
make analyze-cache-performance

# Check specific metrics
curl http://localhost:8000/internal/cache/metrics | jq '.performance'

# Monitor cache in real-time
watch -n 5 'curl -s http://localhost:8000/internal/cache/metrics | jq ".hit_ratio, .memory_usage"'
```

#### Configuration Optimization
```python
# Performance optimization for specific use cases
def optimize_for_high_traffic():
    return {
        "memory_cache_size": 2000,
        "max_connections": 100,
        "compression_threshold": 10000,  # Less compression for speed
        "compression_level": 1,          # Fastest compression
        "default_ttl": 14400            # Longer TTL for better hit rates
    }

def optimize_for_memory_constrained():
    return {
        "memory_cache_size": 25,
        "compression_threshold": 100,    # Compress everything
        "compression_level": 9,          # Maximum compression
        "default_ttl": 7200             # Longer TTL to reduce churn
    }
```

## Best Practices

### Configuration Best Practices

#### 1. Start Simple, Scale Up
- Begin with appropriate preset (`simple`, `development`, `production`)
- Add custom configuration only when needed
- Monitor performance and adjust incrementally

```bash
# Good progression
CACHE_PRESET=simple                    # Start here
CACHE_PRESET=production                # Scale up
CACHE_PRESET=ai-production             # Add AI when needed
```

#### 2. Environment-Specific Configuration
- Use consistent presets across environments
- Override only environment-specific settings
- Document all custom configurations

```bash
# Development
CACHE_PRESET=development
CACHE_REDIS_URL=redis://localhost:6379

# Staging (mirror production)
CACHE_PRESET=production
CACHE_REDIS_URL=redis://staging-cache:6379
CACHE_CUSTOM_CONFIG='{"memory_cache_size": 200}'  # Reduced resources

# Production
CACHE_PRESET=production
CACHE_REDIS_URL=redis://prod-cache:6379
```

#### 3. Security Considerations
- Use TLS in production environments
- Implement proper authentication
- Avoid logging sensitive data

```bash
# Production security configuration
CACHE_PRESET=production
CACHE_REDIS_URL=rediss://secure-cache:6380
CACHE_CUSTOM_CONFIG='{
  "use_tls": true,
  "redis_password": "secure_password",
  "log_level": "INFO"
}'
```

#### 4. Performance Optimization
- Monitor cache hit ratios (target >70%)
- Adjust TTLs based on content stability
- Balance compression vs CPU usage

```bash
# High-performance configuration
CACHE_PRESET=production
CACHE_CUSTOM_CONFIG='{
  "memory_cache_size": 1000,
  "compression_threshold": 5000,
  "default_ttl": 7200
}'
```

#### 5. Monitoring and Alerting
- Enable monitoring in all environments except testing
- Set up alerts for critical metrics
- Monitor configuration drift

```bash
# Monitoring configuration
CACHE_CUSTOM_CONFIG='{
  "monitoring_enabled": true,
  "alert_on_high_memory": true,
  "alert_threshold_mb": 100,
  "metrics_retention_hours": 24
}'
```

### Development Workflow Best Practices

#### 1. Local Development Setup
```bash
# .env.local
CACHE_PRESET=development
CACHE_REDIS_URL=redis://localhost:6379
ENABLE_AI_CACHE=true
CACHE_CUSTOM_CONFIG='{"log_level": "DEBUG"}'
```

#### 2. Testing Configuration
```bash
# .env.test
CACHE_PRESET=disabled
TEST_REDIS_URL=redis://localhost:6379/15

# For integration tests
CACHE_PRESET=minimal
CACHE_CUSTOM_CONFIG='{"default_ttl": 60, "memory_cache_size": 10}'
```

#### 3. Configuration Validation in CI/CD
```yaml
# .github/workflows/test.yml
- name: Validate Cache Configuration
  run: |
    export CACHE_PRESET=production
    make validate-cache-config
    
    export CACHE_PRESET=ai-production
    make validate-cache-config
```

### Deployment Best Practices

#### 1. Blue-Green Deployments
```bash
# Blue environment
CACHE_PRESET=production
CACHE_REDIS_URL=redis://blue-cache:6379

# Green environment (staging)
CACHE_PRESET=production  
CACHE_REDIS_URL=redis://green-cache:6379
CACHE_CUSTOM_CONFIG='{"memory_cache_size": 200}'  # Test with reduced resources
```

#### 2. Canary Deployments
```bash
# Canary configuration (gradual rollout)
CACHE_PRESET=production
CACHE_CUSTOM_CONFIG='{
  "memory_cache_size": 300,     # Intermediate setting
  "monitoring_enabled": true,    # Enhanced monitoring
  "log_level": "INFO"           # Detailed logging
}'
```

#### 3. Rollback Procedures
```bash
# Save configuration before deployment
make save-cache-config --output pre-deploy-config.json

# Deploy with new configuration
make deploy CACHE_PRESET=ai-production

# Rollback if needed
make rollback-cache-config --input pre-deploy-config.json
```

## Related Documentation

### Prerequisites
- **[Infrastructure vs Domain Services](../../reference/key-concepts/INFRASTRUCTURE_VS_DOMAIN.md)**: Understanding the architectural foundation that guides cache configuration decisions
- **[Cache Infrastructure Service](CACHE.md)**: Overview of the cache system architecture and core components
- **[Environment Management](../developer/ENVIRONMENT_MANAGEMENT.md)**: General environment configuration patterns and best practices

### Cache Documentation Suite
- **[Cache Usage Guide](usage-guide.md)**: Practical implementation examples and integration patterns that utilize these configurations
- **[Cache API Reference](api-reference.md)**: Detailed documentation of configuration objects and validation methods  
- **[Cache Testing Guide](testing.md)**: Testing strategies for different cache configurations and environments

### Configuration Resources
- **[Code Standards](../developer/CODE_STANDARDS.md)**: Standardized patterns for configuration management and environment handling
- **[Docker Guide](../developer/DOCKER.md)**: Container-specific configuration patterns and Docker Compose examples
- **[Deployment Guide](../operations/DEPLOYMENT.md)**: Production deployment considerations and configuration management

### Infrastructure Integration
- **[Resilience Infrastructure](../RESILIENCE.md)**: How cache configuration integrates with circuit breaker and retry patterns
- **[Monitoring Infrastructure](../MONITORING.md)**: Monitoring configuration for cache performance and health metrics
- **[Security Infrastructure](../SECURITY.md)**: Security considerations for cache configuration and data protection

### Management Tools
- **[Cache Developer Experience](../CACHE_DEVELOPER_EXPERIENCE.md)**: Development workflows and debugging techniques for cache configuration

---

**Next Steps**: 
- **Quick Setup**: Use the preset selection guide to choose your configuration
- **Advanced Configuration**: Explore custom configuration patterns for specialized use cases  
- **Implementation**: Continue to the [Usage Guide](usage-guide.md) for practical integration examples
- **Production**: Review [deployment best practices](../operations/DEPLOYMENT.md) for production configuration management