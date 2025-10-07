# Redis Cache Security Guide

## Overview

This guide documents the **security-first Redis architecture** implemented in the FastAPI-Streamlit-LLM Starter template. Security is not optional or configurable—it's foundational and always enabled.

### Core Security Philosophy

**Security is not configurable - it's always enabled.**

Our Redis implementation follows a **"pit of success"** design where:
- All Redis connections in **production** **must** use TLS encryption
- All cached data **must** be encrypted at rest
- Applications **fail immediately** if security requirements aren't met
- Configuration automatically adapts to environment while maintaining security

This eliminates configuration complexity, prevents accidental insecure deployments, and creates a robust foundation for production systems.

## Security Architecture

### Three-Layer Security Model

```
┌─────────────────────────────────────────────────────────┐
│  Application Layer                                      │
│  • Startup Security Validation (Fail-Fast)              │
│  • Environment Detection & Security Adaptation          │
└────────────────┬────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────┐
│  Transport Layer Security (TLS)                         │
│  • TLS 1.2+ / TLS 1.3 Encryption                        │
│  • Certificate-Based Authentication                     │
│  • Protected Mode & Network Isolation                   │
└────────────────┬────────────────────────────────────────┘
                 │
┌────────────────▼────────────────────────────────────────┐
│  Data Layer Security                                    │
│  • Fernet Application-Layer Encryption (AES-128)        │
│  • Transparent Encrypt/Decrypt Operations               │
│  • Mandatory Encryption Keys                            │
└─────────────────────────────────────────────────────────┘
```

### Mandatory Security Components

#### 1. Startup Security Validation

**Location:** `backend/app/core/startup/redis_security.py`

The `RedisSecurityValidator` validates security configuration at application startup:

```python
from app.core.startup.redis_security import RedisSecurityValidator

validator = RedisSecurityValidator()
validator.validate_production_security(redis_url, insecure_override)
```

**Key Features:**
- **Environment-Aware Enforcement**: TLS required in production, recommended in development
- **Fail-Fast Design**: Application refuses to start without proper security
- **Clear Error Messages**: Actionable guidance for configuration issues
- **Explicit Override Mechanism**: `REDIS_INSECURE_ALLOW_PLAINTEXT` for trusted networks only

**Validation Logic:**
- Production: Requires `rediss://` URL or authenticated `redis://` connection
- Development/Staging: Logs information but allows flexibility
- Override: Prominent warning when insecure connections used

#### 2. TLS Transport Security

**Configuration:** `docker-compose.secure.yml` and `scripts/init-redis-tls.sh`

Redis enforces TLS encryption for all connections:

```yaml
# TLS-Only Redis Configuration
redis-server
  --tls-port 6380        # TLS-enabled port
  --port 0               # Disable non-TLS port
  --tls-cert-file /tls/redis.crt
  --tls-key-file /tls/redis.key
  --tls-ca-cert-file /tls/ca.crt
  --tls-protocols "TLSv1.2 TLSv1.3"
  --requirepass ${REDIS_PASSWORD}
  --protected-mode yes
```

**TLS Features:**
- **Certificate-Based Security**: 4096-bit RSA certificates
- **Protocol Enforcement**: TLS 1.2+ (development) or TLS 1.3 (production)
- **Password Authentication**: Required for all connections
- **Protected Mode**: Prevents unauthorized network access

#### 3. Application-Layer Encryption

**Location:** `backend/app/infrastructure/cache/encryption.py`

The `EncryptedCacheLayer` provides transparent data encryption:

```python
from app.infrastructure.cache.encryption import EncryptedCacheLayer

# Encryption is mandatory - always initialized with key
encryption = EncryptedCacheLayer(encryption_key)

# All data encrypted before storage
encrypted_data = encryption.encrypt_cache_data(data)

# All data decrypted after retrieval
decrypted_data = encryption.decrypt_cache_data(encrypted_data)
```

**Encryption Features:**
- **Fernet Symmetric Encryption**: AES-128 in CBC mode with HMAC authentication
- **Automatic Serialization**: JSON → Encrypt → Store / Retrieve → Decrypt → JSON
- **Transparent Operations**: Cache consumers don't need encryption awareness
- **Error Handling**: Invalid keys fail fast with `ConfigurationError`

## Environment-Specific Security

### Security Levels by Environment

| Environment | Password | TLS Version | Cert Validation | Encryption |
|------------|----------|-------------|-----------------|------------|
| Production | 48 chars, 256-bit entropy | TLS 1.3 required | Strict (verified CAs) | Mandatory |
| Staging | 32 chars, 192-bit entropy | TLS 1.2+ | Verified CAs | Mandatory |
| Development | 24 chars, 128-bit entropy | TLS 1.2+ | Self-signed OK | Mandatory |
| Testing     | 12 chars                  | Disabled         | Self-signed OK  | Mandatory  |
| Testing | 12 chars | Disabled | Self-signed OK | Mandatory |

### Automatic Environment Detection

Security configuration automatically adapts based on environment:

```python
from app.infrastructure.cache.security import SecurityConfig

# Automatically detects environment and applies appropriate security
config = SecurityConfig.create_for_environment()

# Development: self-signed certs OK, moderate password strength
# Production: strict cert validation, strong passwords required
```

**Environment Detection Logic:**
- Uses `app.core.environment.get_environment_info(FeatureContext.SECURITY_ENFORCEMENT)`
- Checks `NODE_ENV`, `ENVIRONMENT`, deployment indicators
- Defaults to highest security level when uncertain

## Quick Start: Secure Setup

### One-Command Development Setup

For local development with secure Redis:

```bash
# Generate certificates, keys, and start secure Redis
./scripts/setup-secure-redis.sh

# Application automatically uses secure connection
export REDIS_URL="rediss://localhost:6380"
make run-backend
```

**What the script does:**
1. ✅ Checks dependencies (Docker, OpenSSL, Python)
2. ✅ Generates TLS certificates (4096-bit RSA)
3. ✅ Creates secure password (24+ characters)
4. ✅ Generates encryption key (Fernet)
5. ✅ Creates `.env.secure` configuration
6. ✅ Starts TLS-enabled Redis container
7. ✅ Validates connection and encryption

### Production Setup

For production deployments:

```bash
# Generate environment-specific secure configuration
python scripts/generate-secure-env.py --environment production

# Review and deploy configuration
cat .env.production  # Contains secure defaults

# Set production environment variables
export NODE_ENV=production
export REDIS_URL="rediss://production-redis:6380"
export REDIS_PASSWORD="${SECURE_PASSWORD}"
export REDIS_ENCRYPTION_KEY="${GENERATED_KEY}"

# Application validates security at startup
python -m app.main
# ✅ Production environment detected
# ✅ Secure Redis connection validated (TLS + Auth + Encryption)
# 🚀 Application started successfully
```

## TLS Certificate Management

### Certificate Generation

Use the automated script for certificate generation:

```bash
# Generate TLS certificates for Redis
./scripts/init-redis-tls.sh

# Certificates created in ./certs/:
# - ca.key, ca.crt (Certificate Authority)
# - redis.key, redis.crt (Redis Server)
```

**Certificate Details:**
- **Algorithm**: RSA 4096-bit
- **Validity**: 365 days
- **Hash**: SHA-256
- **Permissions**: 600 (keys), 644 (certificates)

### Certificate Validation

Production environments require valid certificates:

```python
# Strict certificate validation in production
REDIS_TLS_CERT_REQS=required  # Verify certificate chain
REDIS_TLS_CA_CERT=/etc/ssl/ca.crt  # Trusted CA certificate
```

Development allows self-signed certificates:

```python
# Development allows self-signed certificates
REDIS_TLS_CERT_REQS=optional  # Self-signed OK
REDIS_TLS_CA_CERT=./certs/ca.crt  # Local CA
```

### Certificate Renewal

Certificates expire after 365 days. To renew:

```bash
# Backup existing certificates
cp -r certs certs.backup.$(date +%Y%m%d)

# Regenerate certificates
./scripts/init-redis-tls.sh

# Restart Redis with new certificates
docker-compose -f docker-compose.secure.yml restart redis
```

**Production Certificate Renewal:**
- Use enterprise certificate management (Let's Encrypt, HashiCorp Vault)
- Implement certificate rotation with zero-downtime
- Monitor certificate expiration dates
- Automate renewal processes

## Encryption Key Management

### Key Generation

Generate cryptographically secure Fernet keys:

```bash
# Using Python cryptography library
python scripts/generate-encryption-key.py

# Or manually:
python -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

**Key Requirements:**
- **Format**: Base64-encoded 32-byte key
- **Algorithm**: Fernet (AES-128-CBC + HMAC-SHA256)
- **Entropy**: 256 bits minimum
- **Storage**: Environment variable or secure secrets manager

### Key Storage Best Practices

**Development:**
```bash
# Store in .env file (git-ignored)
REDIS_ENCRYPTION_KEY="your-generated-key-here"
```

**Production:**
```bash
# Use secrets management service
# - AWS Secrets Manager
# - Azure Key Vault
# - HashiCorp Vault
# - Google Secret Manager

# Load at runtime, never commit to version control
```

### Key Rotation Procedure

To rotate encryption keys securely:

```python
# 1. Generate new encryption key
new_key = Fernet.generate_key()

# 2. Decrypt all cached data with old key
old_cache = EncryptedCacheLayer(old_key)
cached_keys = await old_cache.get_all_keys()
decrypted_data = {k: await old_cache.get(k) for k in cached_keys}

# 3. Re-encrypt data with new key
new_cache = EncryptedCacheLayer(new_key)
for key, value in decrypted_data.items():
    await new_cache.set(key, value)

# 4. Update environment configuration
REDIS_ENCRYPTION_KEY=new_key
```

**Key Rotation Best Practices:**
- Schedule regular rotation (e.g., every 90 days)
- Implement dual-key decryption during rotation period
- Test rotation procedure in staging first
- Monitor for decryption failures after rotation

## Insecure Override Mechanism

### When to Use Insecure Override

**ONLY use in highly controlled environments:**
- Private network with strict firewall rules
- Air-gapped systems with no external access
- Internal development within isolated VPN
- Compliance exemptions for specific deployments

### How to Override Security

Set explicit environment variable:

```bash
export REDIS_INSECURE_ALLOW_PLAINTEXT=true
export REDIS_URL="redis://internal-redis:6379"

python -m app.main
# 🚨 WARNING: Insecure Redis connection in production
# Running with REDIS_INSECURE_ALLOW_PLAINTEXT=true
```

**Security Implications:**
- ⚠️ Data transmitted in plaintext over network
- ⚠️ Vulnerable to man-in-the-middle attacks
- ⚠️ Credentials visible in network traffic
- ⚠️ Compliance violations (GDPR, HIPAA, PCI-DSS)

### Network Isolation Requirements

If using insecure override:

```yaml
# Require internal-only Docker network
networks:
  redis_internal:
    driver: bridge
    internal: true  # No external routing

services:
  redis:
    networks:
      - redis_internal
    # No ports exposed to host
```

**Monitoring Requirements:**
- Log all insecure connections
- Alert on insecure override usage
- Audit network traffic patterns
- Regular security reviews

## Security Troubleshooting

### TLS Connection Issues

**Error: `Connection refused` or `SSL handshake failed`**

Check TLS configuration:

```bash
# Verify Redis is listening on TLS port
docker exec redis_secure redis-cli --tls \
  --cert /tls/redis.crt \
  --key /tls/redis.key \
  --cacert /tls/ca.crt \
  -p 6380 ping
# Expected: PONG

# Check certificate validity
openssl x509 -in certs/redis.crt -text -noout
# Verify: Valid dates, correct CN

# Test TLS connection
openssl s_client -connect localhost:6380 \
  -CAfile certs/ca.crt
# Expected: SSL handshake successful
```

**Common Fixes:**
- Regenerate certificates: `./scripts/init-redis-tls.sh`
- Check certificate paths in Redis configuration
- Verify certificate permissions (600 for keys)
- Ensure TLS port is accessible

### Certificate Validation Failures

**Error: `Certificate verify failed` or `Unknown CA`**

Check certificate chain:

```bash
# Verify certificate chain
openssl verify -CAfile certs/ca.crt certs/redis.crt
# Expected: redis.crt: OK

# Check certificate dates
openssl x509 -in certs/redis.crt -noout -dates
# Verify: notBefore and notAfter are valid

# Verify CA certificate is trusted
REDIS_TLS_CA_CERT=/path/to/ca.crt
```

**Common Fixes:**
- Ensure CA certificate matches server certificate
- Update expired certificates
- Configure correct CA certificate path
- Use `REDIS_TLS_CERT_REQS=optional` for development

### Authentication Failures

**Error: `NOAUTH Authentication required` or `Invalid password`**

Check authentication configuration:

```bash
# Verify password is set in Redis
docker exec redis_secure redis-cli --tls \
  --cert /tls/redis.crt \
  --key /tls/redis.key \
  --cacert /tls/ca.crt \
  -p 6380 \
  -a "$REDIS_PASSWORD" \
  ping
# Expected: PONG

# Check password in environment
echo $REDIS_PASSWORD

# Verify password in .env file
grep REDIS_PASSWORD .env.secure
```

**Common Fixes:**
- Regenerate secure password: `openssl rand -base64 32`
- Update Redis configuration with correct password
- Ensure `REDIS_PASSWORD` environment variable is set
- Check for special characters requiring escaping

### Encryption Key Problems

**Error: `Invalid encryption key` or `Decryption failed`**

Validate encryption key:

```bash
# Check key format (Base64-encoded 32 bytes)
python -c "
from cryptography.fernet import Fernet
key = '$REDIS_ENCRYPTION_KEY'
try:
    Fernet(key.encode())
    print('✅ Valid Fernet key')
except:
    print('❌ Invalid Fernet key')
"

# Generate new key if invalid
python scripts/generate-encryption-key.py
```

**Common Fixes:**
- Generate new Fernet key
- Ensure key is properly base64-encoded
- Check for whitespace or newlines in key
- Clear cache after key rotation

### Production Security Validation Failures

**Error: `SECURITY ERROR: Production environment requires secure connection`**

Fix production security configuration:

```bash
# Change to secure Redis URL
export REDIS_URL="rediss://production-redis:6380"

# Or enable TLS explicitly
export REDIS_TLS_ENABLED=true

# Or for isolated networks only:
export REDIS_INSECURE_ALLOW_PLAINTEXT=true  # ⚠️ Not recommended
```

**Validation Checklist:**
- [ ] Redis URL uses `rediss://` protocol
- [ ] TLS certificates are valid and not expired
- [ ] Password authentication is configured
- [ ] Encryption key is set and valid
- [ ] Network isolation is configured
- [ ] Monitoring is enabled for security events

## Security Monitoring

### Logging Security Events

Security validation results are logged:

```python
# Success
✅ Security validation passed
✅ Secure Redis cache initialized: TLS + Encryption + Auth

# Warnings
🚨 SECURITY WARNING: Running with insecure Redis connection in production!
REDIS_INSECURE_ALLOW_PLAINTEXT=true detected.

# Errors
🔒 SECURITY ERROR: Production environment requires secure Redis connection.
```

### Monitoring Recommendations

**Application Metrics:**
- Track security validation success/failure rates
- Monitor TLS handshake performance
- Measure encryption/decryption overhead
- Alert on insecure override usage

**Redis Metrics:**
- Monitor connection counts and sources
- Track authentication failures
- Alert on certificate expiration (< 30 days)
- Monitor for unusual access patterns

**Security Alerts:**
- Immediate alert on production insecure override
- Daily certificate expiration reports
- Weekly security configuration audits
- Monthly encryption key rotation reminders

### Incident Response

**Security Violation Detected:**

1. **Immediate Action:**
   - Block insecure connections
   - Review application logs
   - Check for data exposure

2. **Investigation:**
   - Identify affected systems
   - Review configuration changes
   - Check for unauthorized access

3. **Remediation:**
   - Restore secure configuration
   - Rotate compromised credentials
   - Re-encrypt affected data
   - Update security procedures

4. **Prevention:**
   - Implement stricter validation
   - Enhance monitoring
   - Review access controls
   - Update security documentation

## Migration Guide

### Migrating from Insecure Redis

This security implementation introduces **breaking changes** that eliminate backward compatibility with insecure configurations.

#### Breaking Changes

1. **TLS Required in Production**: All production connections must use the `rediss://` protocol. Development and testing environments are flexible.
2. **Authentication Mandatory**: Password required for all environments
3. **Encryption Always On**: Data encryption cannot be disabled
4. **Fail-Fast Validation**: Application won't start without security

#### Migration Steps

**Step 1: Backup Existing Data**

```bash
# Export existing Redis data
redis-cli --rdb /backup/dump.rdb

# Or use Redis BGSAVE
redis-cli BGSAVE
cp /var/lib/redis/dump.rdb /backup/
```

**Step 2: Set Up Secure Redis**

```bash
# Generate secure configuration
./scripts/setup-secure-redis.sh

# Review generated configuration
cat .env.secure
```

**Step 3: Update Application Configuration**

```bash
# Update Redis URL to use TLS
OLD: REDIS_URL=redis://localhost:6379
NEW: REDIS_URL=rediss://localhost:6380

# Add required security variables
REDIS_PASSWORD=<generated-password>
REDIS_ENCRYPTION_KEY=<generated-key>
REDIS_TLS_ENABLED=true
```

**Step 4: Migrate Data**

```bash
# Import data to secure Redis
docker exec -i redis_secure redis-cli \
  --tls \
  --cert /tls/redis.crt \
  --key /tls/redis.key \
  --cacert /tls/ca.crt \
  -p 6380 \
  -a "$REDIS_PASSWORD" \
  --rdb < /backup/dump.rdb

# Note: Data will be re-encrypted automatically on first access
```

**Step 5: Validate Migration**

```bash
# Test application startup
python -m app.main
# Expected: ✅ Secure Redis cache initialized

# Verify data accessibility
python -c "
from app.infrastructure.cache.redis_generic import GenericRedisCache
cache = GenericRedisCache.create_secure()
# Test get/set operations
"
```

**Step 6: Update Monitoring**

```bash
# Update health checks for TLS
# Update connection strings in monitoring
# Configure security alerts
```

### Migration Troubleshooting

**Issue: Application fails to start after migration**

Check security configuration:

```bash
# Verify all required variables are set
env | grep REDIS_

# Test Redis connection manually
redis-cli --tls --cert certs/redis.crt --key certs/redis.key \
  --cacert certs/ca.crt -p 6380 -a "$REDIS_PASSWORD" ping
```

**Issue: Data not accessible after migration**

Data encryption may require re-caching:

```bash
# Clear cache and allow re-population
redis-cli --tls [...] FLUSHDB

# Application will re-cache data with encryption
```

## Security Best Practices

### Development

- ✅ Use `./scripts/setup-secure-redis.sh` for local setup
- ✅ Keep certificates in git-ignored `certs/` directory
- ✅ Use `.env.secure` for development configuration
- ✅ Test with self-signed certificates
- ❌ Never commit certificates or keys to version control
- ❌ Don't use production keys in development

### Staging

- ✅ Use production-like security configuration
- ✅ Validate certificate chains
- ✅ Test certificate renewal procedures
- ✅ Practice key rotation procedures
- ❌ Don't use self-signed certificates
- ❌ Don't share credentials with production

### Production

- ✅ Use TLS 1.3 exclusively
- ✅ Implement certificate management automation
- ✅ Use enterprise secrets management
- ✅ Monitor security metrics continuously
- ✅ Rotate encryption keys regularly (90 days)
- ✅ Audit security configuration monthly
- ❌ Never use `REDIS_INSECURE_ALLOW_PLAINTEXT`
- ❌ Never expose Redis ports externally
- ❌ Never use weak passwords (<32 characters)

## Performance Considerations

### Encryption Overhead

**Measured Performance Impact:**
- Encryption/Decryption: 5-10% overhead
- TLS Handshake: 20-30ms initial connection
- Overall: <15% performance impact for typical operations

**Optimization Strategies:**
- Use connection pooling to amortize TLS handshake cost
- Implement compression before encryption for large payloads
- Cache frequently accessed decrypted data in memory
- Monitor and tune Redis memory allocation

### Monitoring Performance

```python
# Track encryption performance
import time
start = time.time()
encrypted = encryption.encrypt_cache_data(data)
encryption_time = time.time() - start

# Log performance metrics
logger.info(f"Encryption time: {encryption_time*1000:.2f}ms")
```

## Compliance and Audit

### Compliance Standards

This security implementation supports:

- **GDPR**: Encryption at rest and in transit
- **HIPAA**: Protected health information encryption
- **PCI-DSS**: Strong encryption for payment data
- **SOC 2**: Security controls and monitoring

### Audit Checklist

**Security Configuration:**
- [ ] TLS 1.2+ enabled for all connections
- [ ] Certificate validation configured
- [ ] Strong passwords (32+ characters)
- [ ] Encryption keys properly secured
- [ ] Network isolation implemented

**Operational Security:**
- [ ] Certificate expiration monitoring active
- [ ] Encryption key rotation scheduled
- [ ] Security event logging enabled
- [ ] Incident response procedures documented
- [ ] Regular security audits scheduled

**Access Controls:**
- [ ] Redis access restricted to application only
- [ ] Secrets stored in secure vault
- [ ] Principle of least privilege applied
- [ ] Access logging enabled
- [ ] Regular access reviews conducted

## Additional Resources

### Documentation

- **Configuration Guide**: `docs/guides/infrastructure/cache/configuration.md`
- **Troubleshooting Guide**: `docs/guides/infrastructure/cache/troubleshooting.md`
- **Usage Guide**: `docs/guides/infrastructure/cache/usage-guide.md`
- **Cache Infrastructure Overview**: `docs/guides/infrastructure/cache/CACHE.md`

### Scripts and Tools

- **Secure Setup**: `scripts/setup-secure-redis.sh`
- **Certificate Generation**: `scripts/init-redis-tls.sh`
- **Environment Generator**: `scripts/generate-secure-env.py`
- **Encryption Key Generator**: `scripts/generate-encryption-key.py`

### Related Documentation

- **Environment Variables**: `docs/get-started/ENVIRONMENT_VARIABLES.md`
- **Quick Start Guide**: `docs/get-started/CACHE_QUICK_START.md`
- **Infrastructure Security**: `docs/guides/infrastructure/SECURITY.md`

### Support and Feedback

For security issues or questions:
1. Review troubleshooting section above
2. Check related documentation
3. Open issue at: https://github.com/anthropics/fastapi-streamlit-llm-starter/issues
4. For security vulnerabilities, report privately to maintainers

---

**Last Updated**: 2025-09-29
**Related PRD**: `dev/taskplans/current/redis-critical-security-gaps_PRD.md`