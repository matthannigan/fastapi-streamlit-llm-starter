# Cache Environment Configuration Guide (UPDATED FOR PRESET SYSTEM)

This guide documents the **Phase 4 preset-based cache configuration system** that replaces 28+ individual environment variables with 1-4 simple variables. For comprehensive preset documentation, see **[Cache Preset Guide](CACHE_PRESET_GUIDE.md)**.

⚡ **NEW: Phase 4 simplifies cache configuration from 28+ variables to 1-4 variables**

## Table of Contents

1. [Preset-Based Configuration (RECOMMENDED)](#preset-based-configuration-recommended)
2. [Legacy Variable Migration](#legacy-variable-migration)
3. [Docker Configuration](#docker-configuration)
4. [Kubernetes Configuration](#kubernetes-configuration)
5. [Cloud Provider Configurations](#cloud-provider-configurations)
6. [Validation and Troubleshooting](#validation-and-troubleshooting)

## Preset-Based Configuration (RECOMMENDED)

### Current Environment Variables (Phase 4)

**Primary Configuration:**
| Variable | Type | Default | Description | Example |
|----------|------|---------|-------------|---------|
| `CACHE_PRESET` | string | `"development"` | Cache preset name | `"production"`, `"ai-production"` |

**Optional Overrides:**
| Variable | Type | Default | Description | Example |
|----------|------|---------|-------------|---------|
| `CACHE_REDIS_URL` | string | `None` | Override Redis connection URL | `redis://prod-cache:6379` |
| `ENABLE_AI_CACHE` | boolean | `None` | Override AI features (depends on preset) | `true`, `false` |
| `CACHE_CUSTOM_CONFIG` | JSON | `None` | Advanced customization via JSON | `{"compression_threshold": 500}` |

### Available Presets

| Preset | Use Case | Redis Required | AI Features | TTL | Memory Cache |
|--------|----------|----------------|-------------|-----|--------------|
| `disabled` | Testing, debugging | No | No | 5 min | Memory-only |
| `minimal` | Resource-constrained | Optional | No | 15 min | 10 entries |
| `simple` | Small applications | Optional | No | 1 hour | 100 entries |
| `development` | Local development | Recommended | Yes | 30 min | 100 entries |
| `production` | Web applications | Required | No | 2 hours | 500 entries |
| `ai-development` | AI development | Recommended | Yes | 30 min | 200 entries |
| `ai-production` | AI applications | Required | Yes | 4 hours | 1000 entries |

**Quick Start:**
```bash
# Choose your preset
export CACHE_PRESET=development

# Add Redis if desired
export CACHE_REDIS_URL=redis://localhost:6379

# That's it! Your cache is configured.
```

## Legacy Variable Migration

**DEPRECATED**: Individual CACHE_* environment variables are no longer supported in Phase 4.

### Migration Guide

**Old Way (28+ variables):**
```bash
export CACHE_DEFAULT_TTL=3600
export CACHE_MEMORY_SIZE=200
export CACHE_COMPRESSION_THRESHOLD=2000
export CACHE_COMPRESSION_LEVEL=6
export CACHE_TEXT_HASH_THRESHOLD=1000
# ... 23+ more variables
```

**New Way (1-4 variables):**
```bash
export CACHE_PRESET=development
export CACHE_REDIS_URL=redis://localhost:6379  # Optional override
export ENABLE_AI_CACHE=true                     # Optional toggle
```

**Migration Tools:**
```bash
# Analyze current configuration
python backend/scripts/migrate_cache_config.py --analyze

# Get preset recommendation
python backend/scripts/migrate_cache_config.py --recommend

# Apply migration
python backend/scripts/migrate_cache_config.py --migrate
```

| Variable | Type | Default | Description | Example |
|----------|------|---------|-------------|---------|
| `CACHE_TEXT_SIZE_TIERS` | JSON | See below | Text categorization thresholds | See [examples](#text-size-tier-examples) |

**Default Text Size Tiers**:
```json
{
  "small": 1000,
  "medium": 10000,
  "large": 100000
}
```

### Operation-Specific TTLs

| Variable | Type | Default | Description | Example |
|----------|------|---------|-------------|---------|
| `CACHE_OPERATION_TTLS` | JSON | See below | TTL values for specific AI operations | See [examples](#operation-ttl-examples) |

**Default Operation TTLs**:
```json
{
  "summarize": 7200,
  "sentiment": 3600,
  "key_points": 5400,
  "questions": 4800,
  "qa": 3600
}
```

### Environment and Deployment

| Variable | Type | Default | Description | Example |
|----------|------|---------|-------------|---------|
| `CACHE_ENVIRONMENT` | string | `development` | Environment name (development, testing, production) | `production` |

## Configuration File Examples

### Basic JSON Configuration

**`cache_config.json`**:
```json
{
  "redis_url": "redis://localhost:6379",
  "default_ttl": 3600,
  "memory_cache_size": 100,
  "compression_threshold": 1000,
  "compression_level": 6,
  "environment": "development"
}
```

### AI-Enhanced Configuration

**`ai_cache_config.json`**:
```json
{
  "redis_url": "redis://redis:6379",
  "default_ttl": 7200,
  "memory_cache_size": 200,
  "compression_threshold": 1000,
  "compression_level": 6,
  "environment": "production",
  "ai_config": {
    "text_hash_threshold": 1000,
    "hash_algorithm": "sha256",
    "text_size_tiers": {
      "small": 500,
      "medium": 5000,
      "large": 50000
    },
    "operation_ttls": {
      "summarize": 7200,
      "sentiment": 86400,
      "key_points": 7200,
      "questions": 3600,
      "qa": 1800
    },
    "enable_smart_promotion": true,
    "max_text_length": 100000
  }
}
```

### Production Configuration with Security

**`production_cache_config.json`**:
```json
{
  "redis_url": "rediss://redis-cluster.internal:6380",
  "redis_password": "${REDIS_PASSWORD}",
  "use_tls": true,
  "tls_cert_path": "/certs/redis-client.crt",
  "tls_key_path": "/certs/redis-client.key",
  "default_ttl": 7200,
  "memory_cache_size": 500,
  "compression_threshold": 500,
  "compression_level": 8,
  "environment": "production",
  "ai_config": {
    "text_hash_threshold": 2000,
    "hash_algorithm": "sha256",
    "text_size_tiers": {
      "small": 1000,
      "medium": 10000,
      "large": 100000
    },
    "operation_ttls": {
      "summarize": 14400,
      "sentiment": 86400,
      "key_points": 10800,
      "questions": 7200,
      "qa": 3600
    },
    "enable_smart_promotion": true,
    "max_text_length": 200000
  }
}
```

### Text Size Tier Examples

**Small Data Applications**:
```json
{
  "text_size_tiers": {
    "small": 100,
    "medium": 1000,
    "large": 10000
  }
}
```

**Large Document Processing**:
```json
{
  "text_size_tiers": {
    "small": 2000,
    "medium": 20000,
    "large": 200000
  }
}
```

### Operation TTL Examples

**Fast-Paced Applications (Short TTLs)**:
```json
{
  "operation_ttls": {
    "summarize": 1800,
    "sentiment": 900,
    "key_points": 1200,
    "questions": 600,
    "qa": 300
  }
}
```

**Content Management Systems (Long TTLs)**:
```json
{
  "operation_ttls": {
    "summarize": 86400,
    "sentiment": 172800,
    "key_points": 43200,
    "questions": 21600,
    "qa": 10800
  }
}
```

## Environment Presets

### Development Environment

**`.env.development`**:
```bash
# Basic Configuration
CACHE_ENVIRONMENT=development
REDIS_URL=redis://localhost:6379
CACHE_DEFAULT_TTL=1800
CACHE_MEMORY_SIZE=50
CACHE_COMPRESSION_THRESHOLD=2000
CACHE_COMPRESSION_LEVEL=4

# AI Features
CACHE_ENABLE_AI_FEATURES=true
CACHE_TEXT_HASH_THRESHOLD=500
CACHE_ENABLE_SMART_PROMOTION=true

# Development-specific settings
CACHE_TEXT_SIZE_TIERS='{"small": 500, "medium": 2000, "large": 10000}'
CACHE_OPERATION_TTLS='{"summarize": 600, "sentiment": 300, "qa": 180}'
```

### Testing Environment

**`.env.testing`**:
```bash
# Testing Configuration
CACHE_ENVIRONMENT=testing
REDIS_URL=redis://redis-test:6379
CACHE_DEFAULT_TTL=60
CACHE_MEMORY_SIZE=25
CACHE_COMPRESSION_THRESHOLD=1000
CACHE_COMPRESSION_LEVEL=1

# AI Features for Testing
CACHE_ENABLE_AI_FEATURES=true
CACHE_TEXT_HASH_THRESHOLD=200
CACHE_MAX_TEXT_LENGTH=10000

# Fast expiration for test isolation
CACHE_TEXT_SIZE_TIERS='{"small": 200, "medium": 1000, "large": 5000}'
CACHE_OPERATION_TTLS='{"summarize": 30, "sentiment": 15, "qa": 10}'
```

### Production Environment

**`.env.production`**:
```bash
# Production Configuration
CACHE_ENVIRONMENT=production
REDIS_URL=redis://redis-cluster.internal:6379
CACHE_REDIS_PASSWORD=secure_redis_password_from_secrets
CACHE_USE_TLS=true
CACHE_TLS_CERT_PATH=/etc/ssl/certs/redis-client.crt
CACHE_TLS_KEY_PATH=/etc/ssl/private/redis-client.key

# Performance Settings
CACHE_DEFAULT_TTL=7200
CACHE_MEMORY_SIZE=200
CACHE_COMPRESSION_THRESHOLD=1000
CACHE_COMPRESSION_LEVEL=6

# AI Features
CACHE_ENABLE_AI_FEATURES=true
CACHE_TEXT_HASH_THRESHOLD=1000
CACHE_HASH_ALGORITHM=sha256
CACHE_ENABLE_SMART_PROMOTION=true
CACHE_MAX_TEXT_LENGTH=200000

# Production Text Tiers
CACHE_TEXT_SIZE_TIERS='{"small": 1000, "medium": 10000, "large": 100000}'

# Production Operation TTLs
CACHE_OPERATION_TTLS='{
  "summarize": 14400,
  "sentiment": 86400,
  "key_points": 10800,
  "questions": 7200,
  "qa": 3600
}'
```

## Docker Configuration

### Docker Compose Configuration

**`docker-compose.yml`**:
```yaml
version: '3.8'

services:
  backend:
    build: .
    ports:
      - "8000:8000"
    environment:
      # Cache Configuration
      REDIS_URL: redis://redis:6379
      CACHE_DEFAULT_TTL: 3600
      CACHE_MEMORY_SIZE: 100
      CACHE_COMPRESSION_THRESHOLD: 1000
      CACHE_COMPRESSION_LEVEL: 6
      
      # AI Cache Features
      CACHE_ENABLE_AI_FEATURES: "true"
      CACHE_TEXT_HASH_THRESHOLD: 1000
      CACHE_HASH_ALGORITHM: sha256
      CACHE_ENABLE_SMART_PROMOTION: "true"
      
      # Text Size Tiers (JSON)
      CACHE_TEXT_SIZE_TIERS: '{"small": 500, "medium": 5000, "large": 50000}'
      
      # Operation TTLs (JSON)
      CACHE_OPERATION_TTLS: '{
        "summarize": 7200,
        "sentiment": 3600,
        "key_points": 5400,
        "questions": 4800,
        "qa": 3600
      }'
    depends_on:
      - redis
    volumes:
      - ./cache_config.json:/app/cache_config.json:ro

  redis:
    image: redis:7-alpine
    ports:
      - "6379:6379"
    command: redis-server --appendonly yes
    volumes:
      - redis_data:/data
    healthcheck:
      test: ["CMD", "redis-cli", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

volumes:
  redis_data:
```

### Docker Compose with Redis Security

**`docker-compose.production.yml`**:
```yaml
version: '3.8'

services:
  backend:
    build: .
    environment:
      # Secure Redis Configuration
      REDIS_URL: redis://redis:6379
      CACHE_REDIS_PASSWORD_FILE: /run/secrets/redis_password
      CACHE_USE_TLS: "true"
      CACHE_TLS_CERT_PATH: /certs/redis-client.crt
      CACHE_TLS_KEY_PATH: /certs/redis-client.key
      
      # Production Cache Settings
      CACHE_ENVIRONMENT: production
      CACHE_DEFAULT_TTL: 7200
      CACHE_MEMORY_SIZE: 200
      CACHE_COMPRESSION_THRESHOLD: 1000
      CACHE_COMPRESSION_LEVEL: 7
      
      # AI Features
      CACHE_ENABLE_AI_FEATURES: "true"
      CACHE_TEXT_HASH_THRESHOLD: 1000
      CACHE_MAX_TEXT_LENGTH: 200000
    secrets:
      - redis_password
    volumes:
      - ./certs/redis-client.crt:/certs/redis-client.crt:ro
      - ./certs/redis-client.key:/certs/redis-client.key:ro
      - ./config/production_cache.json:/app/cache_config.json:ro

  redis:
    image: redis:7-alpine
    command: >
      sh -c "redis-server 
        --requirepass $$(cat /run/secrets/redis_password)
        --appendonly yes
        --tls-port 6380
        --tls-cert-file /certs/redis-server.crt
        --tls-key-file /certs/redis-server.key
        --tls-ca-cert-file /certs/ca.crt"
    secrets:
      - redis_password
    volumes:
      - redis_data:/data
      - ./certs/redis-server.crt:/certs/redis-server.crt:ro
      - ./certs/redis-server.key:/certs/redis-server.key:ro
      - ./certs/ca.crt:/certs/ca.crt:ro

secrets:
  redis_password:
    file: ./secrets/redis_password.txt

volumes:
  redis_data:
```

### Multi-Environment Docker Configuration

**`docker-compose.override.yml`** (Development):
```yaml
version: '3.8'

services:
  backend:
    environment:
      CACHE_ENVIRONMENT: development
      CACHE_DEFAULT_TTL: 1800
      CACHE_MEMORY_SIZE: 50
      CACHE_TEXT_HASH_THRESHOLD: 500
      CACHE_OPERATION_TTLS: '{
        "summarize": 600,
        "sentiment": 300,
        "qa": 180
      }'
    volumes:
      - ./config/development_cache.json:/app/cache_config.json:ro

  redis:
    ports:
      - "6379:6379"  # Expose for development
```

## Kubernetes Configuration

### ConfigMap for Cache Configuration

**`cache-config.yaml`**:
```yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: cache-config
  namespace: default
data:
  cache_config.json: |
    {
      "default_ttl": 7200,
      "memory_cache_size": 200,
      "compression_threshold": 1000,
      "compression_level": 6,
      "environment": "production",
      "ai_config": {
        "text_hash_threshold": 1000,
        "hash_algorithm": "sha256",
        "text_size_tiers": {
          "small": 1000,
          "medium": 10000,
          "large": 100000
        },
        "operation_ttls": {
          "summarize": 14400,
          "sentiment": 86400,
          "key_points": 10800,
          "questions": 7200,
          "qa": 3600
        },
        "enable_smart_promotion": true,
        "max_text_length": 200000
      }
    }
  
  # Environment-specific overrides
  CACHE_ENVIRONMENT: "production"
  CACHE_DEFAULT_TTL: "7200"
  CACHE_MEMORY_SIZE: "200"
  CACHE_COMPRESSION_THRESHOLD: "1000"
  CACHE_COMPRESSION_LEVEL: "6"
  CACHE_ENABLE_AI_FEATURES: "true"
  CACHE_TEXT_HASH_THRESHOLD: "1000"
  CACHE_HASH_ALGORITHM: "sha256"
  CACHE_ENABLE_SMART_PROMOTION: "true"
  CACHE_MAX_TEXT_LENGTH: "200000"
```

### Secret for Redis Authentication

**`redis-secret.yaml`**:
```yaml
apiVersion: v1
kind: Secret
metadata:
  name: redis-secret
  namespace: default
type: Opaque
data:
  # Base64 encoded values
  redis-password: c2VjdXJlX3JlZGlzX3Bhc3N3b3JkXzEyMw==
  redis-url: cmVkaXM6Ly86c2VjdXJlX3JlZGlzX3Bhc3N3b3JkXzEyM0ByZWRpcy1jbHVzdGVyOjYzNzk=
```

### Deployment Configuration

**`deployment.yaml`**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend-deployment
  namespace: default
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      containers:
      - name: backend
        image: fastapi-backend:latest
        ports:
        - containerPort: 8000
        env:
        # Redis Configuration from Secret
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: redis-secret
              key: redis-url
        
        # Cache Configuration from ConfigMap
        - name: CACHE_ENVIRONMENT
          valueFrom:
            configMapKeyRef:
              name: cache-config
              key: CACHE_ENVIRONMENT
        - name: CACHE_DEFAULT_TTL
          valueFrom:
            configMapKeyRef:
              name: cache-config
              key: CACHE_DEFAULT_TTL
        - name: CACHE_MEMORY_SIZE
          valueFrom:
            configMapKeyRef:
              name: cache-config
              key: CACHE_MEMORY_SIZE
        - name: CACHE_COMPRESSION_THRESHOLD
          valueFrom:
            configMapKeyRef:
              name: cache-config
              key: CACHE_COMPRESSION_THRESHOLD
        - name: CACHE_COMPRESSION_LEVEL
          valueFrom:
            configMapKeyRef:
              name: cache-config
              key: CACHE_COMPRESSION_LEVEL
        - name: CACHE_ENABLE_AI_FEATURES
          valueFrom:
            configMapKeyRef:
              name: cache-config
              key: CACHE_ENABLE_AI_FEATURES
        - name: CACHE_TEXT_HASH_THRESHOLD
          valueFrom:
            configMapKeyRef:
              name: cache-config
              key: CACHE_TEXT_HASH_THRESHOLD
        - name: CACHE_HASH_ALGORITHM
          valueFrom:
            configMapKeyRef:
              name: cache-config
              key: CACHE_HASH_ALGORITHM
        - name: CACHE_ENABLE_SMART_PROMOTION
          valueFrom:
            configMapKeyRef:
              name: cache-config
              key: CACHE_ENABLE_SMART_PROMOTION
        - name: CACHE_MAX_TEXT_LENGTH
          valueFrom:
            configMapKeyRef:
              name: cache-config
              key: CACHE_MAX_TEXT_LENGTH
        
        # Complex JSON configurations
        - name: CACHE_TEXT_SIZE_TIERS
          value: '{"small": 1000, "medium": 10000, "large": 100000}'
        - name: CACHE_OPERATION_TTLS
          value: '{
            "summarize": 14400,
            "sentiment": 86400,
            "key_points": 10800,
            "questions": 7200,
            "qa": 3600
          }'
        
        volumeMounts:
        - name: cache-config-volume
          mountPath: /app/cache_config.json
          subPath: cache_config.json
          readOnly: true
        
        # TLS Certificates (if using secure Redis)
        - name: tls-certs
          mountPath: /certs
          readOnly: true
        
        # Resource limits
        resources:
          requests:
            memory: "256Mi"
            cpu: "250m"
          limits:
            memory: "512Mi"
            cpu: "500m"
      
      volumes:
      - name: cache-config-volume
        configMap:
          name: cache-config
      - name: tls-certs
        secret:
          secretName: redis-tls-certs
```

### Redis Cluster Configuration

**`redis-cluster.yaml`**:
```yaml
apiVersion: apps/v1
kind: StatefulSet
metadata:
  name: redis-cluster
  namespace: default
spec:
  serviceName: redis-cluster
  replicas: 3
  selector:
    matchLabels:
      app: redis-cluster
  template:
    metadata:
      labels:
        app: redis-cluster
    spec:
      containers:
      - name: redis
        image: redis:7-alpine
        ports:
        - containerPort: 6379
        env:
        - name: REDIS_PASSWORD
          valueFrom:
            secretKeyRef:
              name: redis-secret
              key: redis-password
        command:
        - redis-server
        - /etc/redis/redis.conf
        - --requirepass
        - $(REDIS_PASSWORD)
        - --appendonly
        - "yes"
        volumeMounts:
        - name: redis-config
          mountPath: /etc/redis
        - name: redis-data
          mountPath: /data
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
      volumes:
      - name: redis-config
        configMap:
          name: redis-config
  volumeClaimTemplates:
  - metadata:
      name: redis-data
    spec:
      accessModes: ["ReadWriteOnce"]
      resources:
        requests:
          storage: 10Gi

---
apiVersion: v1
kind: Service
metadata:
  name: redis-cluster
  namespace: default
spec:
  selector:
    app: redis-cluster
  ports:
  - port: 6379
    targetPort: 6379
  clusterIP: None  # Headless service for StatefulSet
```

## Cloud Provider Configurations

### AWS Configuration

#### AWS ElastiCache Integration

**Environment Variables for ElastiCache**:
```bash
# AWS ElastiCache Configuration
REDIS_URL=rediss://my-cluster.abc123.cache.amazonaws.com:6380
CACHE_USE_TLS=true
CACHE_REDIS_PASSWORD=${ELASTICACHE_AUTH_TOKEN}

# Production settings for ElastiCache
CACHE_DEFAULT_TTL=7200
CACHE_MEMORY_SIZE=500
CACHE_COMPRESSION_THRESHOLD=1000
CACHE_COMPRESSION_LEVEL=8

# AI Features optimized for ElastiCache
CACHE_ENABLE_AI_FEATURES=true
CACHE_TEXT_HASH_THRESHOLD=2000
CACHE_MAX_TEXT_LENGTH=500000
```

#### AWS ECS Task Definition

**`ecs-task-definition.json`**:
```json
{
  "family": "fastapi-backend",
  "networkMode": "awsvpc",
  "requiresCompatibilities": ["FARGATE"],
  "cpu": "512",
  "memory": "1024",
  "executionRoleArn": "arn:aws:iam::account:role/ecsTaskExecutionRole",
  "taskRoleArn": "arn:aws:iam::account:role/ecsTaskRole",
  "containerDefinitions": [
    {
      "name": "backend",
      "image": "your-account.dkr.ecr.region.amazonaws.com/fastapi-backend:latest",
      "portMappings": [
        {
          "containerPort": 8000,
          "protocol": "tcp"
        }
      ],
      "environment": [
        {
          "name": "CACHE_ENVIRONMENT",
          "value": "production"
        },
        {
          "name": "CACHE_DEFAULT_TTL",
          "value": "7200"
        },
        {
          "name": "CACHE_MEMORY_SIZE",
          "value": "500"
        },
        {
          "name": "CACHE_COMPRESSION_THRESHOLD",
          "value": "1000"
        },
        {
          "name": "CACHE_COMPRESSION_LEVEL",
          "value": "8"
        },
        {
          "name": "CACHE_ENABLE_AI_FEATURES",
          "value": "true"
        },
        {
          "name": "CACHE_TEXT_HASH_THRESHOLD",
          "value": "2000"
        },
        {
          "name": "CACHE_USE_TLS",
          "value": "true"
        }
      ],
      "secrets": [
        {
          "name": "REDIS_URL",
          "valueFrom": "arn:aws:ssm:region:account:parameter/app/redis-url"
        },
        {
          "name": "CACHE_REDIS_PASSWORD",
          "valueFrom": "arn:aws:ssm:region:account:parameter/app/redis-password"
        }
      ],
      "logConfiguration": {
        "logDriver": "awslogs",
        "options": {
          "awslogs-group": "/ecs/fastapi-backend",
          "awslogs-region": "us-east-1",
          "awslogs-stream-prefix": "ecs"
        }
      }
    }
  ]
}
```

#### AWS CDK Configuration

**`cache_stack.py`**:
```python
from aws_cdk import (
    Stack,
    aws_elasticache as elasticache,
    aws_ec2 as ec2,
    aws_ssm as ssm,
    aws_secretsmanager as secretsmanager,
)
from constructs import Construct

class CacheStack(Stack):
    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)
        
        # Create VPC for ElastiCache
        vpc = ec2.Vpc(self, "CacheVPC", max_azs=2)
        
        # Create subnet group for ElastiCache
        subnet_group = elasticache.CfnSubnetGroup(
            self, "CacheSubnetGroup",
            description="Subnet group for ElastiCache",
            subnet_ids=[subnet.subnet_id for subnet in vpc.private_subnets]
        )
        
        # Create security group for ElastiCache
        security_group = ec2.SecurityGroup(
            self, "CacheSecurityGroup",
            vpc=vpc,
            description="Security group for ElastiCache",
            allow_all_outbound=False
        )
        
        # Allow Redis access from ECS
        security_group.add_ingress_rule(
            peer=ec2.Peer.ipv4(vpc.vpc_cidr_block),
            connection=ec2.Port.tcp(6379),
            description="Redis access from VPC"
        )
        
        # Create Redis auth token
        auth_token = secretsmanager.Secret(
            self, "RedisAuthToken",
            description="Redis authentication token",
            generate_secret_string=secretsmanager.SecretStringGenerator(
                secret_string_template='{"username": "default"}',
                generate_string_key="password",
                exclude_characters=" %+~`#$&*()|[]{}:;<>?!'/\"\\",
                password_length=32
            )
        )
        
        # Create ElastiCache Redis cluster
        cache_cluster = elasticache.CfnCacheCluster(
            self, "RedisCluster",
            cache_node_type="cache.t3.micro",
            engine="redis",
            engine_version="7.0",
            num_cache_nodes=1,
            cache_subnet_group_name=subnet_group.ref,
            vpc_security_group_ids=[security_group.security_group_id],
            transit_encryption_enabled=True,
            auth_token=auth_token.secret_value.unsafe_unwrap()
        )
        
        # Store Redis URL in Parameter Store
        redis_url = f"rediss://:{auth_token.secret_value.unsafe_unwrap()}@{cache_cluster.attr_redis_endpoint_address}:{cache_cluster.attr_redis_endpoint_port}"
        
        ssm.StringParameter(
            self, "RedisUrl",
            parameter_name="/app/redis-url",
            string_value=redis_url,
            description="Redis connection URL for cache"
        )
        
        # Store cache configuration parameters
        cache_params = {
            "cache-default-ttl": "7200",
            "cache-memory-size": "500",
            "cache-compression-threshold": "1000",
            "cache-compression-level": "8",
            "cache-text-hash-threshold": "2000",
            "cache-max-text-length": "500000"
        }
        
        for name, value in cache_params.items():
            ssm.StringParameter(
                self, f"CacheParam{name.replace('-', '').title()}",
                parameter_name=f"/app/{name}",
                string_value=value,
                description=f"Cache configuration: {name}"
            )
```

### Google Cloud Platform (GCP) Configuration

#### GCP Memorystore Integration

**Environment Variables for Memorystore**:
```bash
# GCP Memorystore Configuration
REDIS_URL=redis://10.0.0.3:6379  # Private IP from Memorystore
CACHE_USE_TLS=true
CACHE_REDIS_PASSWORD=${MEMORYSTORE_AUTH_STRING}

# Production settings for Memorystore
CACHE_DEFAULT_TTL=7200
CACHE_MEMORY_SIZE=500
CACHE_COMPRESSION_THRESHOLD=1000
CACHE_COMPRESSION_LEVEL=8

# AI Features optimized for Memorystore
CACHE_ENABLE_AI_FEATURES=true
CACHE_TEXT_HASH_THRESHOLD=2000
```

#### GKE Configuration

**`gke-deployment.yaml`**:
```yaml
apiVersion: apps/v1
kind: Deployment
metadata:
  name: backend-deployment
  namespace: default
spec:
  replicas: 3
  selector:
    matchLabels:
      app: backend
  template:
    metadata:
      labels:
        app: backend
    spec:
      serviceAccountName: backend-sa
      containers:
      - name: backend
        image: gcr.io/your-project/fastapi-backend:latest
        ports:
        - containerPort: 8000
        env:
        # Cache Configuration
        - name: CACHE_ENVIRONMENT
          value: "production"
        - name: CACHE_DEFAULT_TTL
          value: "7200"
        - name: CACHE_MEMORY_SIZE
          value: "500"
        - name: CACHE_COMPRESSION_THRESHOLD
          value: "1000"
        - name: CACHE_COMPRESSION_LEVEL
          value: "8"
        - name: CACHE_ENABLE_AI_FEATURES
          value: "true"
        - name: CACHE_TEXT_HASH_THRESHOLD
          value: "2000"
        - name: CACHE_USE_TLS
          value: "true"
        - name: REDIS_URL
          valueFrom:
            secretKeyRef:
              name: redis-secret
              key: redis-url
        - name: CACHE_REDIS_PASSWORD
          valueFrom:
            secretKeyRef:
              name: redis-secret
              key: auth-string
        resources:
          requests:
            memory: "512Mi"
            cpu: "250m"
          limits:
            memory: "1Gi"
            cpu: "500m"
```

### Microsoft Azure Configuration

#### Azure Cache for Redis Integration

**Environment Variables for Azure Cache**:
```bash
# Azure Cache for Redis Configuration
REDIS_URL=rediss://your-cache.redis.cache.windows.net:6380
CACHE_USE_TLS=true
CACHE_REDIS_PASSWORD=${AZURE_REDIS_PRIMARY_KEY}

# Production settings for Azure Cache
CACHE_DEFAULT_TTL=7200
CACHE_MEMORY_SIZE=500
CACHE_COMPRESSION_THRESHOLD=1000
CACHE_COMPRESSION_LEVEL=8

# AI Features optimized for Azure Cache
CACHE_ENABLE_AI_FEATURES=true
CACHE_TEXT_HASH_THRESHOLD=2000
```

#### Azure Container Instances Configuration

**`azure-container-group.json`**:
```json
{
  "$schema": "https://schema.management.azure.com/schemas/2019-04-01/deploymentTemplate.json#",
  "contentVersion": "1.0.0.0",
  "parameters": {
    "redisConnectionString": {
      "type": "securestring",
      "metadata": {
        "description": "Redis connection string"
      }
    },
    "redisPrimaryKey": {
      "type": "securestring",
      "metadata": {
        "description": "Redis primary access key"
      }
    }
  },
  "resources": [
    {
      "type": "Microsoft.ContainerInstance/containerGroups",
      "apiVersion": "2021-07-01",
      "name": "fastapi-backend",
      "location": "[resourceGroup().location]",
      "properties": {
        "containers": [
          {
            "name": "backend",
            "properties": {
              "image": "your-registry.azurecr.io/fastapi-backend:latest",
              "ports": [
                {
                  "port": 8000,
                  "protocol": "TCP"
                }
              ],
              "environmentVariables": [
                {
                  "name": "CACHE_ENVIRONMENT",
                  "value": "production"
                },
                {
                  "name": "CACHE_DEFAULT_TTL",
                  "value": "7200"
                },
                {
                  "name": "CACHE_MEMORY_SIZE",
                  "value": "500"
                },
                {
                  "name": "CACHE_COMPRESSION_THRESHOLD",
                  "value": "1000"
                },
                {
                  "name": "CACHE_COMPRESSION_LEVEL",
                  "value": "8"
                },
                {
                  "name": "CACHE_ENABLE_AI_FEATURES",
                  "value": "true"
                },
                {
                  "name": "CACHE_TEXT_HASH_THRESHOLD",
                  "value": "2000"
                },
                {
                  "name": "CACHE_USE_TLS",
                  "value": "true"
                },
                {
                  "name": "REDIS_URL",
                  "secureValue": "[parameters('redisConnectionString')]"
                },
                {
                  "name": "CACHE_REDIS_PASSWORD",
                  "secureValue": "[parameters('redisPrimaryKey')]"
                }
              ],
              "resources": {
                "requests": {
                  "cpu": 0.5,
                  "memoryInGB": 1
                }
              }
            }
          }
        ],
        "osType": "Linux",
        "ipAddress": {
          "type": "Public",
          "ports": [
            {
              "port": 8000,
              "protocol": "TCP"
            }
          ]
        }
      }
    }
  ]
}
```

## Validation and Troubleshooting

### Configuration Validation

#### Using the Builder Pattern

```python
from app.infrastructure.cache.config import CacheConfigBuilder

# Validate configuration from environment
try:
    config = CacheConfigBuilder().from_environment().build()
    print("✅ Configuration is valid")
except ValidationError as e:
    print(f"❌ Configuration error: {e}")
    print(f"Context: {e.context}")
```

#### Using Configuration File

```python
from app.infrastructure.cache.config import CacheConfigBuilder

# Validate configuration from file
try:
    config = CacheConfigBuilder().from_file("cache_config.json").build()
    print("✅ Configuration file is valid")
except ConfigurationError as e:
    print(f"❌ Configuration file error: {e}")
```

#### Validation Script

Create `scripts/validate_cache_config.py`:

```python
#!/usr/bin/env python3
"""
Cache Configuration Validation Script

Usage:
    python scripts/validate_cache_config.py --env
    python scripts/validate_cache_config.py --file cache_config.json
    python scripts/validate_cache_config.py --all
"""

import argparse
import os
import sys
from pathlib import Path

# Add the backend directory to Python path
backend_dir = Path(__file__).parent.parent / "backend"
sys.path.insert(0, str(backend_dir))

from app.infrastructure.cache.config import CacheConfigBuilder, ValidationResult
from app.core.exceptions import ConfigurationError, ValidationError


def validate_environment_config() -> bool:
    """Validate cache configuration from environment variables."""
    print("🔍 Validating environment configuration...")
    
    try:
        builder = CacheConfigBuilder().from_environment()
        validation_result = builder.validate()
        
        if validation_result.is_valid:
            print("✅ Environment configuration is valid")
            
            if validation_result.warnings:
                print("\n⚠️  Warnings found:")
                for warning in validation_result.warnings:
                    print(f"   - {warning}")
            
            # Build to trigger final validation
            config = builder.build()
            print(f"📋 Configuration summary:")
            print(f"   Environment: {config.environment}")
            print(f"   Redis URL: {config.redis_url}")
            print(f"   Default TTL: {config.default_ttl}s")
            print(f"   Memory cache size: {config.memory_cache_size}")
            print(f"   AI features: {'enabled' if config.ai_config else 'disabled'}")
            
            return True
        else:
            print("❌ Environment configuration is invalid")
            print("\n🚨 Errors found:")
            for error in validation_result.errors:
                print(f"   - {error}")
            return False
            
    except (ConfigurationError, ValidationError) as e:
        print(f"❌ Environment configuration error: {e}")
        if hasattr(e, 'context') and e.context:
            print(f"📝 Context: {e.context}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error validating environment config: {e}")
        return False


def validate_file_config(file_path: str) -> bool:
    """Validate cache configuration from file."""
    print(f"🔍 Validating file configuration: {file_path}")
    
    if not Path(file_path).exists():
        print(f"❌ Configuration file not found: {file_path}")
        return False
    
    try:
        builder = CacheConfigBuilder().from_file(file_path)
        validation_result = builder.validate()
        
        if validation_result.is_valid:
            print("✅ File configuration is valid")
            
            if validation_result.warnings:
                print("\n⚠️  Warnings found:")
                for warning in validation_result.warnings:
                    print(f"   - {warning}")
            
            # Build to trigger final validation
            config = builder.build()
            print(f"📋 Configuration summary:")
            print(f"   Environment: {config.environment}")
            print(f"   Redis URL: {config.redis_url}")
            print(f"   Default TTL: {config.default_ttl}s")
            print(f"   Memory cache size: {config.memory_cache_size}")
            print(f"   AI features: {'enabled' if config.ai_config else 'disabled'}")
            
            return True
        else:
            print("❌ File configuration is invalid")
            print("\n🚨 Errors found:")
            for error in validation_result.errors:
                print(f"   - {error}")
            return False
            
    except (ConfigurationError, ValidationError) as e:
        print(f"❌ File configuration error: {e}")
        if hasattr(e, 'context') and e.context:
            print(f"📝 Context: {e.context}")
        return False
    except Exception as e:
        print(f"❌ Unexpected error validating file config: {e}")
        return False


def validate_all_configs() -> bool:
    """Validate all available configurations."""
    print("🔍 Validating all available configurations...\n")
    
    all_valid = True
    
    # Check environment configuration
    env_valid = validate_environment_config()
    all_valid = all_valid and env_valid
    
    print()  # Spacing
    
    # Check for common config files
    config_files = [
        "cache_config.json",
        "config/cache_config.json",
        "config/production_cache.json",
        "config/development_cache.json",
        "config/testing_cache.json"
    ]
    
    files_found = 0
    for config_file in config_files:
        if Path(config_file).exists():
            files_found += 1
            file_valid = validate_file_config(config_file)
            all_valid = all_valid and file_valid
            print()  # Spacing
    
    if files_found == 0:
        print("ℹ️  No configuration files found to validate")
    
    return all_valid


def main():
    parser = argparse.ArgumentParser(description="Cache Configuration Validation")
    group = parser.add_mutually_exclusive_group(required=True)
    group.add_argument("--env", action="store_true", help="Validate environment configuration")
    group.add_argument("--file", help="Validate specific configuration file")
    group.add_argument("--all", action="store_true", help="Validate all available configurations")
    
    args = parser.parse_args()
    
    if args.env:
        success = validate_environment_config()
    elif args.file:
        success = validate_file_config(args.file)
    elif args.all:
        success = validate_all_configs()
    
    if success:
        print("\n🎉 All validations passed!")
        sys.exit(0)
    else:
        print("\n💥 Some validations failed!")
        sys.exit(1)


if __name__ == "__main__":
    main()
```

**Make the script executable**:
```bash
chmod +x scripts/validate_cache_config.py
```

### Common Configuration Issues

#### Issue: Redis Connection Fails

**Symptoms**:
```
WARNING Cache: Redis connection failed, using memory-only mode
```

**Diagnosis**:
```bash
# Check Redis connectivity
redis-cli -h redis-host -p 6379 ping

# Validate Redis URL format
python scripts/validate_cache_config.py --env
```

**Solutions**:
```bash
# Fix Redis URL format
REDIS_URL=redis://localhost:6379        # ✅ Correct
REDIS_URL=localhost:6379               # ❌ Missing protocol

# Add authentication if required
REDIS_URL=redis://:password@redis:6379  # With password
REDIS_URL=redis://user:pass@redis:6379  # With username/password
```

#### Issue: High Memory Usage

**Symptoms**:
```
WARNING Cache: Memory usage exceeded threshold: 150MB
```

**Solutions**:
```bash
# Reduce memory cache size
CACHE_MEMORY_SIZE=50

# Enable more aggressive compression
CACHE_COMPRESSION_THRESHOLD=500
CACHE_COMPRESSION_LEVEL=8

# Reduce TTL values
CACHE_DEFAULT_TTL=1800
```

#### Issue: Poor Cache Hit Rates

**Symptoms**:
```
Cache hit rate: 25% (Expected: >70%)
```

**Solutions**:
```bash
# Increase TTL values
CACHE_DEFAULT_TTL=7200

# Optimize operation-specific TTLs
CACHE_OPERATION_TTLS='{
  "summarize": 14400,
  "sentiment": 86400
}'

# Review text preprocessing consistency
CACHE_TEXT_HASH_THRESHOLD=500  # Lower threshold for better key consistency
```

#### Issue: Invalid JSON Configuration

**Symptoms**:
```
ConfigurationError: Invalid JSON in CACHE_OPERATION_TTLS
```

**Solutions**:
```bash
# ❌ Invalid JSON (missing quotes)
CACHE_OPERATION_TTLS='{summarize: 3600}'

# ✅ Valid JSON
CACHE_OPERATION_TTLS='{"summarize": 3600}'

# ✅ Multi-line JSON (use proper escaping)
CACHE_OPERATION_TTLS='{
  "summarize": 3600,
  "sentiment": 1800
}'
```

### Environment-Specific Troubleshooting

#### Development Environment

```bash
# Common development issues and solutions
export CACHE_ENVIRONMENT=development
export CACHE_DEFAULT_TTL=300  # Short TTL for testing
export CACHE_MEMORY_SIZE=25   # Small cache for debugging
export REDIS_URL=redis://localhost:6379  # Local Redis

# Debug configuration
python scripts/validate_cache_config.py --env
```

#### Production Environment

```bash
# Production troubleshooting checklist
export CACHE_ENVIRONMENT=production
export CACHE_USE_TLS=true     # Ensure TLS is enabled
export CACHE_COMPRESSION_LEVEL=6  # Optimize for production

# Validate production config
python scripts/validate_cache_config.py --file config/production_cache.json

# Check Redis cluster health
redis-cli -h prod-redis --tls -a "$REDIS_PASSWORD" cluster info
```

## Migration from Legacy Configuration

### Legacy Environment Variables

The following legacy environment variables are still supported but deprecated:

| Legacy Variable | New Variable | Migration Action |
|----------------|--------------|------------------|
| `REDIS_URL` | `CACHE_REDIS_URL` | Both supported, prefer new |
| `CACHE_TTL_SECONDS` | `CACHE_DEFAULT_TTL` | Rename variable |
| `MEMORY_CACHE_SIZE` | `CACHE_MEMORY_SIZE` | Rename with prefix |
| `COMPRESSION_THRESHOLD` | `CACHE_COMPRESSION_THRESHOLD` | Rename with prefix |

### Migration Script

Create `scripts/migrate_cache_config.py`:

```python
#!/usr/bin/env python3
"""
Cache Configuration Migration Script

Migrates from legacy environment variables to new configuration format.

Usage:
    python scripts/migrate_cache_config.py --check
    python scripts/migrate_cache_config.py --migrate --output .env.new
    python scripts/migrate_cache_config.py --generate-file --output cache_config.json
"""

import argparse
import json
import os
from pathlib import Path
from typing import Dict, Any, List


class ConfigMigrator:
    """Handles migration from legacy configuration to new format."""
    
    # Legacy to new variable mappings
    LEGACY_MAPPINGS = {
        'CACHE_TTL_SECONDS': 'CACHE_DEFAULT_TTL',
        'MEMORY_CACHE_SIZE': 'CACHE_MEMORY_SIZE',
        'COMPRESSION_THRESHOLD': 'CACHE_COMPRESSION_THRESHOLD',
        'TEXT_HASH_THRESHOLD': 'CACHE_TEXT_HASH_THRESHOLD',
        'HASH_ALGORITHM': 'CACHE_HASH_ALGORITHM',
    }
    
    def __init__(self):
        self.env_vars = dict(os.environ)
        self.migration_needed = False
        self.warnings: List[str] = []
        self.new_config: Dict[str, Any] = {}
    
    def check_legacy_variables(self) -> bool:
        """Check if legacy variables are present."""
        legacy_found = []
        
        for legacy_var in self.LEGACY_MAPPINGS.keys():
            if legacy_var in self.env_vars:
                legacy_found.append(legacy_var)
                self.migration_needed = True
        
        if legacy_found:
            print(f"🔍 Found legacy environment variables:")
            for var in legacy_found:
                new_var = self.LEGACY_MAPPINGS[var]
                value = self.env_vars[var]
                print(f"   {var} -> {new_var} (current value: {value})")
        
        return self.migration_needed
    
    def migrate_environment_variables(self) -> Dict[str, str]:
        """Migrate legacy environment variables to new format."""
        migrated_vars = {}
        
        # Copy existing cache variables
        for key, value in self.env_vars.items():
            if key.startswith('CACHE_') and key not in self.LEGACY_MAPPINGS:
                migrated_vars[key] = value
        
        # Migrate legacy variables
        for legacy_var, new_var in self.LEGACY_MAPPINGS.items():
            if legacy_var in self.env_vars:
                migrated_vars[new_var] = self.env_vars[legacy_var]
                print(f"✅ Migrated {legacy_var} -> {new_var}")
        
        # Handle special cases
        if 'REDIS_URL' in self.env_vars and 'CACHE_REDIS_URL' not in migrated_vars:
            migrated_vars['CACHE_REDIS_URL'] = self.env_vars['REDIS_URL']
            print(f"✅ Copied REDIS_URL -> CACHE_REDIS_URL")
        
        return migrated_vars
    
    def generate_config_file(self) -> Dict[str, Any]:
        """Generate configuration file from environment variables."""
        config = {
            "environment": self.env_vars.get('CACHE_ENVIRONMENT', 'development'),
            "redis_url": self.env_vars.get('CACHE_REDIS_URL', self.env_vars.get('REDIS_URL')),
            "default_ttl": int(self.env_vars.get('CACHE_DEFAULT_TTL', 3600)),
            "memory_cache_size": int(self.env_vars.get('CACHE_MEMORY_SIZE', 100)),
            "compression_threshold": int(self.env_vars.get('CACHE_COMPRESSION_THRESHOLD', 1000)),
            "compression_level": int(self.env_vars.get('CACHE_COMPRESSION_LEVEL', 6)),
        }
        
        # Add TLS configuration if present
        if self.env_vars.get('CACHE_USE_TLS', '').lower() == 'true':
            config['use_tls'] = True
            if 'CACHE_TLS_CERT_PATH' in self.env_vars:
                config['tls_cert_path'] = self.env_vars['CACHE_TLS_CERT_PATH']
            if 'CACHE_TLS_KEY_PATH' in self.env_vars:
                config['tls_key_path'] = self.env_vars['CACHE_TLS_KEY_PATH']
        
        # Add AI configuration if enabled
        if self.env_vars.get('CACHE_ENABLE_AI_FEATURES', '').lower() == 'true':
            ai_config = {
                "text_hash_threshold": int(self.env_vars.get('CACHE_TEXT_HASH_THRESHOLD', 1000)),
                "hash_algorithm": self.env_vars.get('CACHE_HASH_ALGORITHM', 'sha256'),
                "enable_smart_promotion": self.env_vars.get('CACHE_ENABLE_SMART_PROMOTION', 'true').lower() == 'true',
                "max_text_length": int(self.env_vars.get('CACHE_MAX_TEXT_LENGTH', 100000)),
            }
            
            # Add text size tiers if present
            if 'CACHE_TEXT_SIZE_TIERS' in self.env_vars:
                try:
                    ai_config['text_size_tiers'] = json.loads(self.env_vars['CACHE_TEXT_SIZE_TIERS'])
                except json.JSONDecodeError:
                    self.warnings.append("Invalid CACHE_TEXT_SIZE_TIERS JSON, using defaults")
            
            # Add operation TTLs if present
            if 'CACHE_OPERATION_TTLS' in self.env_vars:
                try:
                    ai_config['operation_ttls'] = json.loads(self.env_vars['CACHE_OPERATION_TTLS'])
                except json.JSONDecodeError:
                    self.warnings.append("Invalid CACHE_OPERATION_TTLS JSON, using defaults")
            
            config['ai_config'] = ai_config
        
        return config
    
    def write_env_file(self, migrated_vars: Dict[str, str], output_file: str) -> None:
        """Write migrated environment variables to file."""
        with open(output_file, 'w') as f:
            f.write("# Migrated Cache Configuration\n")
            f.write("# Generated by cache configuration migration script\n\n")
            
            # Group variables logically
            basic_vars = [k for k in migrated_vars.keys() if k in [
                'CACHE_ENVIRONMENT', 'CACHE_REDIS_URL', 'CACHE_DEFAULT_TTL',
                'CACHE_MEMORY_SIZE', 'CACHE_COMPRESSION_THRESHOLD', 'CACHE_COMPRESSION_LEVEL'
            ]]
            
            if basic_vars:
                f.write("# Basic Configuration\n")
                for var in basic_vars:
                    f.write(f"{var}={migrated_vars[var]}\n")
                f.write("\n")
            
            # AI configuration
            ai_vars = [k for k in migrated_vars.keys() if k.startswith('CACHE_') and 'AI' in k or 'TEXT' in k or 'HASH' in k]
            if ai_vars:
                f.write("# AI Configuration\n")
                for var in ai_vars:
                    f.write(f"{var}={migrated_vars[var]}\n")
                f.write("\n")
            
            # Security configuration
            security_vars = [k for k in migrated_vars.keys() if 'TLS' in k or 'PASSWORD' in k]
            if security_vars:
                f.write("# Security Configuration\n")
                for var in security_vars:
                    f.write(f"{var}={migrated_vars[var]}\n")
                f.write("\n")
            
            # Remaining variables
            remaining_vars = [k for k in migrated_vars.keys() if k not in basic_vars + ai_vars + security_vars]
            if remaining_vars:
                f.write("# Additional Configuration\n")
                for var in remaining_vars:
                    f.write(f"{var}={migrated_vars[var]}\n")
        
        print(f"✅ Wrote migrated environment variables to {output_file}")
    
    def write_config_file(self, config: Dict[str, Any], output_file: str) -> None:
        """Write configuration to JSON file."""
        with open(output_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        print(f"✅ Wrote configuration file to {output_file}")


def main():
    parser = argparse.ArgumentParser(description="Cache Configuration Migration")
    parser.add_argument("--check", action="store_true", help="Check for legacy variables")
    parser.add_argument("--migrate", action="store_true", help="Migrate environment variables")
    parser.add_argument("--generate-file", action="store_true", help="Generate configuration file")
    parser.add_argument("--output", help="Output file path")
    
    args = parser.parse_args()
    
    migrator = ConfigMigrator()
    
    if args.check:
        print("🔍 Checking for legacy configuration variables...\n")
        
        if migrator.check_legacy_variables():
            print(f"\n⚠️  Migration recommended!")
            print("   Run with --migrate to create new environment file")
            print("   Run with --generate-file to create JSON configuration")
        else:
            print("✅ No legacy variables found, configuration is up to date")
        
        return
    
    if args.migrate:
        if not args.output:
            args.output = ".env.migrated"
        
        print("🚀 Migrating environment variables...\n")
        
        if migrator.check_legacy_variables():
            migrated_vars = migrator.migrate_environment_variables()
            migrator.write_env_file(migrated_vars, args.output)
            
            if migrator.warnings:
                print("\n⚠️  Warnings:")
                for warning in migrator.warnings:
                    print(f"   - {warning}")
            
            print(f"\n✅ Migration complete!")
            print(f"   Review {args.output} and update your environment")
        else:
            print("ℹ️  No legacy variables found, nothing to migrate")
    
    if args.generate_file:
        if not args.output:
            args.output = "cache_config.json"
        
        print("📄 Generating configuration file...\n")
        
        config = migrator.generate_config_file()
        migrator.write_config_file(config, args.output)
        
        if migrator.warnings:
            print("\n⚠️  Warnings:")
            for warning in migrator.warnings:
                print(f"   - {warning}")
        
        print(f"\n✅ Configuration file generated!")
        print(f"   Use with: CacheConfigBuilder().from_file('{args.output}')")


if __name__ == "__main__":
    main()
```

### Migration Process

1. **Check for legacy variables**:
   ```bash
   python scripts/migrate_cache_config.py --check
   ```

2. **Migrate environment variables**:
   ```bash
   python scripts/migrate_cache_config.py --migrate --output .env.new
   ```

3. **Generate configuration file**:
   ```bash
   python scripts/migrate_cache_config.py --generate-file --output cache_config.json
   ```

4. **Validate new configuration**:
   ```bash
   python scripts/validate_cache_config.py --file cache_config.json
   ```

## Best Practices Summary

### Environment Variable Organization

1. **Use consistent prefixes**: All cache variables start with `CACHE_`
2. **Group related settings**: Organize variables by functionality
3. **Use type-appropriate formats**: JSON for complex objects, boolean strings for flags
4. **Document environment-specific values**: Comment configuration files

### Security Best Practices

1. **Never commit secrets**: Use secure parameter stores or secrets management
2. **Enable TLS in production**: Always use encrypted connections
3. **Use strong authentication**: Generate secure Redis passwords
4. **Rotate credentials regularly**: Update passwords and certificates

### Performance Optimization

1. **Match TTL to content stability**: Longer TTL for stable content
2. **Optimize compression settings**: Balance CPU vs storage based on resources
3. **Size memory cache appropriately**: Based on available RAM and usage patterns
4. **Monitor cache performance**: Use built-in metrics and alerting

### Environment-Specific Recommendations

| Environment | TTL | Memory Size | Compression | TLS | Monitoring |
|-------------|-----|-------------|-------------|-----|------------|
| **Development** | Short (300-1800s) | Small (25-50) | Low (level 1-4) | Optional | Basic |
| **Testing** | Very short (30-60s) | Minimal (10-25) | Minimal (level 1) | Optional | Basic |
| **Production** | Long (3600-14400s) | Large (200-500) | High (level 6-8) | Required | Full |

This comprehensive guide provides all the configuration patterns and examples needed to deploy the Cache Infrastructure Service across any environment or cloud provider while maintaining security, performance, and reliability standards.