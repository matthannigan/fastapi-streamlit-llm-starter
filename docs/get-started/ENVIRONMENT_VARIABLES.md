# Environment Variables

**Essential environment variables for configuration:**

## Quick Start: Secure Redis Setup

For the fastest and most secure setup, use the one-command setup script:

```bash
# One-command secure Redis setup (recommended)
./scripts/setup-secure-redis.sh

# This will:
# - Check dependencies
# - Generate TLS certificates
# - Create secure passwords and encryption keys
# - Configure environment variables
# - Start secure Redis container
# - Validate the setup
```

**Alternative: Manual environment generation:**
```bash
# Generate secure environment configuration
python scripts/generate-secure-env.py --environment development

# For production
python scripts/generate-secure-env.py --environment production

# Validate existing configuration
python scripts/generate-secure-env.py --validate-only
```

---

## Development/Local Recommendations

### Secure Development Configuration (Recommended)

```bash
# === SECURE REDIS CONFIGURATION (REQUIRED) ===
# Run ./scripts/setup-secure-redis.sh to auto-generate these values

# Redis connection with TLS encryption
REDIS_URL=rediss://localhost:6380
REDIS_PASSWORD=your-secure-password-32-chars-min
REDIS_TLS_ENABLED=true
REDIS_TLS_CERT_PATH=./certs/redis.crt
REDIS_TLS_KEY_PATH=./certs/redis.key
REDIS_TLS_CA_PATH=./certs/ca.crt
REDIS_VERIFY_CERTIFICATES=false  # Self-signed certs OK in development

# Data encryption (always enabled)
REDIS_ENCRYPTION_KEY=your-fernet-encryption-key-here

# === BASIC CONFIGURATION ===
RESILIENCE_PRESET=development
API_KEY=dev-test-key
GEMINI_API_KEY=your-gemini-api-key

# Authentication Configuration
AUTH_MODE=simple                  # "simple" or "advanced" mode
ENABLE_USER_TRACKING=false        # Enable user context tracking (advanced mode only)
ENABLE_REQUEST_LOGGING=true       # Enable security event logging

# Cache Configuration (uses secure REDIS_URL automatically)
CACHE_PRESET=ai-development       # Choose: disabled, simple, development, production, ai-development, ai-production
ENABLE_AI_CACHE=true              # Toggle AI cache features

# Frontend Configuration
API_BASE_URL=http://localhost:8000
SHOW_DEBUG_INFO=true
INPUT_MAX_LENGTH=10000

# Health Check Configuration
HEALTH_CHECK_TIMEOUT_MS=2000
HEALTH_CHECK_AI_MODEL_TIMEOUT_MS=1000
HEALTH_CHECK_CACHE_TIMEOUT_MS=3000
HEALTH_CHECK_RESILIENCE_TIMEOUT_MS=1500
HEALTH_CHECK_RETRY_COUNT=1

# Development Features
DEBUG=true
LOG_LEVEL=DEBUG
```

### Development with Insecure Redis (NOT Recommended)

**⚠️ WARNING: Only use in isolated development environments with throwaway data**

```bash
# Allow plaintext Redis (development only)
REDIS_INSECURE_ALLOW_PLAINTEXT=true
REDIS_URL=redis://localhost:6379

# Still recommended to use encryption
REDIS_ENCRYPTION_KEY=your-fernet-encryption-key-here

# Other configuration same as secure development above...
```

---

## Production Recommendations

### Secure Production Configuration (Mandatory)

```bash
# === SECURE REDIS CONFIGURATION (MANDATORY) ===
# Generate with: python scripts/generate-secure-env.py --environment production

# Redis connection with TLS encryption (REQUIRED)
REDIS_URL=rediss://your-redis-instance.example.com:6380
REDIS_PASSWORD=your-production-password-48-chars-min
REDIS_TLS_ENABLED=true
REDIS_TLS_CERT_PATH=/etc/ssl/certs/redis.crt
REDIS_TLS_KEY_PATH=/etc/ssl/private/redis.key
REDIS_TLS_CA_PATH=/etc/ssl/certs/ca.crt
REDIS_VERIFY_CERTIFICATES=true  # MUST be true in production

# Data encryption (REQUIRED)
REDIS_ENCRYPTION_KEY=your-production-fernet-key-here

# === BASIC CONFIGURATION ===
RESILIENCE_PRESET=production
API_KEY=your-secure-production-key-32-chars-min
ADDITIONAL_API_KEYS=key1,key2,key3
GEMINI_API_KEY=your-production-gemini-key

# Authentication Configuration
AUTH_MODE=advanced                # "simple" or "advanced" - use advanced for production
ENABLE_USER_TRACKING=true         # Enable user context tracking and metadata
ENABLE_REQUEST_LOGGING=true       # Enable comprehensive security event logging

# Cache Configuration (uses secure REDIS_URL automatically)
CACHE_PRESET=ai-production        # Production-optimized cache settings

# Infrastructure
CORS_ORIGINS=["https://your-frontend-domain.com"]

# Frontend Configuration
API_BASE_URL=https://api.your-domain.com
SHOW_DEBUG_INFO=false
INPUT_MAX_LENGTH=50000

# Health Check Configuration  
HEALTH_CHECK_TIMEOUT_MS=2000
HEALTH_CHECK_AI_MODEL_TIMEOUT_MS=1000
HEALTH_CHECK_CACHE_TIMEOUT_MS=3000
HEALTH_CHECK_RESILIENCE_TIMEOUT_MS=1500
HEALTH_CHECK_RETRY_COUNT=2

# Security
DISABLE_INTERNAL_DOCS=true
LOG_LEVEL=INFO
```

---

## Advanced Configuration

### Custom Resilience Configuration

```bash
# Custom Resilience Configuration (JSON overrides)
RESILIENCE_PRESET=production
RESILIENCE_CUSTOM_CONFIG='{"retry_attempts": 5, "circuit_breaker_threshold": 10}'
```

### Custom Cache Configuration

```bash
# Custom Cache Configuration (JSON overrides)
CACHE_PRESET=ai-production
CACHE_CUSTOM_CONFIG='{
  "compression_threshold": 500,
  "memory_cache_size": 2000,
  "operation_ttls": {
    "summarize": 7200,
    "sentiment": 3600
  }
}'
```

### Performance Tuning

```bash
# Performance and concurrency limits
MAX_CONCURRENT_REQUESTS=50
REQUEST_TIMEOUT_SECONDS=30
```

---

## Security-Specific Variables

### Redis Security Variables

All Redis security variables are **REQUIRED** for production deployments:

| Variable | Required | Description | Example |
|----------|----------|-------------|---------|
| `REDIS_URL` | Yes | Redis connection URL with TLS | `rediss://localhost:6380` |
| `REDIS_PASSWORD` | Yes | Strong authentication password | 32+ chars in production |
| `REDIS_TLS_ENABLED` | Yes | Enable TLS encryption | `true` |
| `REDIS_TLS_CERT_PATH` | Yes | TLS certificate path | `./certs/redis.crt` |
| `REDIS_TLS_KEY_PATH` | Yes | TLS private key path | `./certs/redis.key` |
| `REDIS_TLS_CA_PATH` | Yes | CA certificate path | `./certs/ca.crt` |
| `REDIS_VERIFY_CERTIFICATES` | Yes | Verify certificate validity | `true` (production), `false` (dev) |
| `REDIS_ENCRYPTION_KEY` | Yes | Fernet encryption key | Base64-encoded Fernet key |
| `REDIS_INSECURE_ALLOW_PLAINTEXT` | No | Allow insecure plaintext Redis (dev only) | `false` (default) |

**Security Levels by Environment:**

| Environment | Password Length | Min Entropy | TLS Version | Cert Validation |
|-------------|----------------|-------------|-------------|-----------------|
| Development | 24 chars | 128 bits | TLS 1.2 | Optional |
| Staging | 32 chars | 192 bits | TLS 1.2 | Required |
| Production | 48 chars | 256 bits | TLS 1.3 | Required |

### Generating Secure Credentials

```bash
# Generate complete secure environment (recommended)
python scripts/generate-secure-env.py --environment production

# Generate Redis password manually
openssl rand -base64 48 | tr -d "=+/" | cut -c1-48

# Generate Fernet encryption key manually
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# Generate TLS certificates
./scripts/init-redis-tls.sh
```

### Security Best Practices

1. **Never commit credentials** to version control
2. **Use strong passwords**: Minimum 32 characters, cryptographically random
3. **Rotate credentials regularly**: At least every 90 days
4. **Keep certificates secure**: File permissions 600 for keys, 644 for certs
5. **Validate certificates** in production: Always set `REDIS_VERIFY_CERTIFICATES=true`
6. **Monitor security logs**: Check for authentication failures and connection issues
7. **Use environment-specific keys**: Never share credentials between environments
8. **Backup encryption keys securely**: Store in encrypted key management system

---

## Environment-Specific Notes

### Development Environment

- **Security**: Balanced security for fast iteration
- **Certificates**: Self-signed certificates acceptable
- **Passwords**: 24+ character minimum
- **Validation**: Certificate validation can be disabled for convenience
- **Setup**: Use `./scripts/setup-secure-redis.sh` for one-command setup

### Staging Environment

- **Security**: Production-like security for realistic testing
- **Certificates**: Use production-grade certificates
- **Passwords**: 32+ character minimum
- **Validation**: Full certificate validation required
- **Setup**: Use `python scripts/generate-secure-env.py --environment staging`

### Production Environment

- **Security**: Maximum security enforcement
- **Certificates**: Valid certificates from trusted CA
- **Passwords**: 48+ character minimum
- **Validation**: Strict certificate validation mandatory
- **Setup**: Use `python scripts/generate-secure-env.py --environment production`
- **Monitoring**: Enable security monitoring and alerting

---

## Validation and Troubleshooting

### Validate Configuration

```bash
# Validate environment configuration
python scripts/generate-secure-env.py --validate-only --output .env

# Test Redis connection
redis-cli --tls \
  --cert certs/redis.crt \
  --key certs/redis.key \
  --cacert certs/ca.crt \
  -p 6380 ping

# Check certificate validity
openssl x509 -in certs/redis.crt -text -noout

# Verify certificate expiration
openssl x509 -in certs/redis.crt -checkend 0
```

### Common Issues

**Connection Refused:**
- Check Redis is running: `docker ps | grep redis`
- Verify port is correct: 6380 for TLS, 6379 for plaintext
- Check firewall rules

**TLS Handshake Failure:**
- Verify certificate paths are correct
- Check certificate validity: `openssl x509 -in certs/redis.crt -text -noout`
- Ensure `REDIS_TLS_ENABLED=true`

**Authentication Failed:**
- Verify `REDIS_PASSWORD` is correct
- Check Redis requirepass configuration
- Ensure password has no special characters that need escaping

**Encryption Key Invalid:**
- Regenerate key: `python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"`
- Verify key is properly base64-encoded
- Check for whitespace or newlines in key value

---

## See Also

- **Setup Guide**: `docs/get-started/SETUP_INTEGRATION.md` - Complete setup instructions
- **Cache Documentation**: `docs/guides/infrastructure/cache/` - Cache architecture and configuration
- **Security Guide**: `docs/guides/infrastructure/cache/security.md` - Comprehensive security documentation
- **Example Configurations**: `.env.example` and `.env.examples-cache` - Complete example configurations
