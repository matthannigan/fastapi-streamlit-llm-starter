## **Product Requirements Document: Secure-First Redis Implementation**

### **1. Overview**

We will implement a **security-first Redis architecture** where secure connections and data encryption are mandatory, not optional. This eliminates configuration complexity, prevents accidental insecure deployments, and creates a robust foundation for production systems.

This document outlines our approach to create an opinionated **"pit of success"** where security is foundational, not configurable. All Redis connections must use TLS encryption and authentication, and all cached data must be encrypted at rest using application-layer encryption.

**Core Philosophy: Security is not configurable - it's always enabled.**

### **2. Core Goals & Objectives**

* **Mandatory Security:** All Redis connections must use TLS encryption and authentication. No insecure connections permitted in any environment.
* **Always-On Encryption:** All cached data is encrypted at rest using Fernet encryption. No unencrypted data storage.
* **Fail-Fast Design:** Application fails immediately on startup if security requirements aren't met.
* **Environment-Aware Defaults:** Security configuration automatically adapts to environment (development vs production) while maintaining security.
* **Zero-Configuration Security:** Developers get secure Redis with a single setup command.

---

### **3. Scope**

#### **In Scope**

* Mandatory TLS for all Redis connections in all environments
* Mandatory application-layer encryption for all cached data
* Automatic security configuration based on environment detection
* Fail-fast startup validation with clear error messages
* Simplified, secure-only `GenericRedisCache` implementation
* One-command secure Redis setup for development
* Graceful fallback to in-memory cache when Redis unavailable

#### **Out of Scope**

* Backward compatibility with existing insecure configurations
* Optional security features or graceful degradation
* Support for unencrypted connections in any environment
* Implementation of advanced Redis security features like Access Control Lists (ACLs)
* Support for Redis Sentinel or Redis Cluster configurations

---

### **4. Functional Requirements & User Stories**

#### **Story 1: Mandatory Security for All Environments**

* **As a Template User,** I want all Redis connections to be secure by default, preventing any possibility of insecure deployments.
* **Acceptance Criteria:**
    * All Redis connections must use TLS (`rediss://`) and authentication in all environments.
    * Application fails immediately on startup if security requirements aren't met.
    * Clear error messages guide developers to fix configuration issues.
    * No configuration paths that result in insecure connections.

#### **Story 2: Automatic Environment-Aware Security**

* **As a Developer,** I want security configuration to automatically adapt to my environment while maintaining security.
* **Acceptance Criteria:**
    * Production: TLS 1.3, strong passwords, certificate validation required.
    * Development: TLS 1.2+, moderate passwords, self-signed certificates OK.
    * Security level appropriate for environment but never insecure.
    * Zero manual security configuration required.

#### **Story 3: One-Command Secure Setup**

* **As a Developer,** I want to set up secure Redis for development with a single command.
* **Acceptance Criteria:**
    * `./scripts/setup-secure-redis.sh` provides complete secure Redis environment.
    * Generates TLS certificates, secure passwords, and encryption keys.
    * Starts TLS-enabled Redis container with proper configuration.
    * Application works securely immediately after setup.

#### **Story 4: Always-On Data Encryption**

* **As a Security Engineer,** I want all cached data to be encrypted at rest, regardless of environment.
* **Acceptance Criteria:**
    * All cache data is encrypted using Fernet before storage in Redis.
    * Encryption/decryption happens transparently in cache operations.
    * No configuration option to disable encryption.
    * Performance impact under 15% for typical operations.

#### **Story 5: Simplified Secure Cache Architecture**

* **As a Software Maintainer,** I want a single, always-secure Redis cache implementation.
* **Acceptance Criteria:**
    * `GenericRedisCache` has built-in mandatory security features.
    * All cache implementations automatically inherit security.
    * Simple API with security handled transparently.
    * Graceful fallback to in-memory cache when Redis unavailable.

---

### **5. Technical Architecture**

#### **Startup Security Validation**

```python
# backend/app/core/startup/redis_security.py
from app.core.environment import get_environment_info, Environment, FeatureContext
from app.core.exceptions import ConfigurationError
import logging

class RedisSecurityValidator:
    """Validates Redis security configuration at application startup"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

    def validate_production_security(self, redis_url: str, insecure_override: bool = False) -> None:
        """
        Validate Redis security for production environments.

        Args:
            redis_url: Redis connection string
            insecure_override: Explicit override to allow insecure connections

        Raises:
            ConfigurationError: If production environment lacks TLS
        """
        env_info = get_environment_info(FeatureContext.SECURITY_ENFORCEMENT)

        # Only enforce TLS in production
        if env_info.environment != Environment.PRODUCTION:
            self.logger.info(f"Environment: {env_info.environment.value} - TLS validation skipped")
            return

        # Check for explicit insecure override
        if insecure_override:
            self.logger.warning(
                "🚨 SECURITY WARNING: Running with insecure Redis connection in production! "
                "REDIS_INSECURE_ALLOW_PLAINTEXT=true detected. This should only be used "
                "in highly secure, isolated network environments."
            )
            return

        # Validate TLS usage
        if not self._is_secure_connection(redis_url):
            raise ConfigurationError(
                "🔒 SECURITY ERROR: Production environment requires secure Redis connection.\n"
                "\n"
                "Current connection: insecure (redis://)\n"
                "Required: TLS-enabled (rediss://) or authenticated connection\n"
                "\n"
                "To fix this issue:\n"
                "1. Use TLS: Change REDIS_URL to rediss://... \n"
                "2. Or set REDIS_TLS_ENABLED=true in environment\n"
                "3. For secure networks only: Set REDIS_INSECURE_ALLOW_PLAINTEXT=true\n"
                "\n"
                "📚 See documentation: docs/infrastructure/redis-security.md"
            )

    def _is_secure_connection(self, redis_url: str) -> bool:
        """Check if Redis connection is secure"""
        if redis_url.startswith('rediss://'):
            return True
        if redis_url.startswith('redis://') and '@' in redis_url:  # Has auth
            return True
        return False
```

#### **Secure Docker Configuration**

```yaml
# docker-compose.secure.yml
version: '3.8'

services:
  redis:
    image: redis:7-alpine
    container_name: redis_secure
    restart: unless-stopped
    networks:
      - redis_internal
    volumes:
      - ./certs:/tls
      - redis_data:/data
    command: >
      redis-server
      --tls-port 6380
      --port 0
      --tls-cert-file /tls/redis.crt
      --tls-key-file /tls/redis.key
      --tls-ca-cert-file /tls/ca.crt
      --tls-protocols "TLSv1.2 TLSv1.3"
      --requirepass ${REDIS_PASSWORD}
      --protected-mode yes
    environment:
      - REDIS_PASSWORD=${REDIS_PASSWORD}
    healthcheck:
      test: ["CMD", "redis-cli", "--tls", "--cert", "/tls/redis.crt", "--key", "/tls/redis.key", "--cacert", "/tls/ca.crt", "-p", "6380", "ping"]
      interval: 30s
      timeout: 10s
      retries: 3

  backend:
    build: ./backend
    networks:
      - redis_internal
      - app_external
    environment:
      - REDIS_URL=rediss://redis:6380
      - REDIS_PASSWORD=${REDIS_PASSWORD}
      - REDIS_TLS_ENABLED=true
    depends_on:
      redis:
        condition: service_healthy

networks:
  redis_internal:
    driver: bridge
    internal: true
  app_external:
    driver: bridge

volumes:
  redis_data:
```

#### **TLS Certificate Generation Script**

```bash
#!/bin/bash
# scripts/init-redis-tls.sh
set -euo pipefail

CERT_DIR="./certs"
REDIS_HOST="redis"

echo "🔐 Generating TLS certificates for Redis..."

# Create certificate directory
mkdir -p "$CERT_DIR"
cd "$CERT_DIR"

# Generate CA private key
openssl genrsa -out ca.key 4096

# Generate CA certificate
openssl req -x509 -new -nodes -key ca.key -sha256 -days 365 -out ca.crt -subj "/CN=Redis-CA"

# Generate Redis private key
openssl genrsa -out redis.key 4096

# Generate Redis certificate signing request
openssl req -new -key redis.key -out redis.csr -subj "/CN=$REDIS_HOST"

# Generate Redis certificate
openssl x509 -req -in redis.csr -CA ca.crt -CAkey ca.key -CAcreateserial -out redis.crt -days 365 -sha256

# Set appropriate permissions
chmod 600 *.key
chmod 644 *.crt

# Clean up CSR
rm redis.csr

echo "✅ TLS certificates generated successfully!"
echo "📁 Certificates location: $CERT_DIR"
echo "🚀 Ready to start secure Redis with: docker-compose -f docker-compose.secure.yml up"
```

---

### **6. User Experience**

#### **Developer Workflow**

**Local Development Setup:**
```bash
# One-command secure Redis setup
./scripts/init-redis-tls.sh
docker-compose -f docker-compose.secure.yml up -d

# Application starts with secure connection
export REDIS_URL="rediss://localhost:6380"
export REDIS_PASSWORD="$(openssl rand -base64 32)"
python -m app.main
```

**Production Deployment:**
```bash
# Environment validation and encryption happen automatically
export NODE_ENV=production
export REDIS_URL="rediss://production-redis:6380"
export REDIS_PASSWORD="${SECURE_PASSWORD}"
export REDIS_ENCRYPTION_KEY="${GENERATED_ENCRYPTION_KEY}"

# Application validates security at startup
python -m app.main
# ✅ Production environment detected
# ✅ Secure Redis connection validated (TLS + Encryption)
# 🚀 Application started successfully
```

**Override for Trusted Networks:**
```bash
# Explicit override with prominent warning
export REDIS_INSECURE_ALLOW_PLAINTEXT=true
export REDIS_URL="redis://internal-redis:6379"
python -m app.main
# 🚨 WARNING: Insecure Redis connection in production
```

#### **Encryption at Rest Implementation**

```python
# backend/app/infrastructure/cache/encryption.py
from cryptography.fernet import Fernet
from typing import Optional, Dict, Any
import json
import logging

class EncryptedCacheLayer:
    """Handles encryption/decryption of sensitive cache data"""

    def __init__(self, encryption_key: Optional[str] = None):
        self.logger = logging.getLogger(__name__)
        self.fernet = None

        if encryption_key:
            try:
                self.fernet = Fernet(encryption_key.encode())
                self.logger.info("🔐 Cache encryption enabled")
            except Exception as e:
                self.logger.error(f"Failed to initialize encryption: {e}")
                raise ConfigurationError(f"Invalid encryption key: {e}")
        else:
            self.logger.info("Cache encryption disabled - no key provided")

    def encrypt_cache_data(self, data: Dict[str, Any]) -> bytes:
        """Encrypt cache data if encryption is enabled"""
        if not self.fernet:
            return json.dumps(data).encode('utf-8')

        json_data = json.dumps(data).encode('utf-8')
        return self.fernet.encrypt(json_data)

    def decrypt_cache_data(self, encrypted_data: bytes) -> Dict[str, Any]:
        """Decrypt cache data if encryption is enabled"""
        if not self.fernet:
            return json.loads(encrypted_data.decode('utf-8'))

        try:
            decrypted_data = self.fernet.decrypt(encrypted_data)
            return json.loads(decrypted_data.decode('utf-8'))
        except Exception as e:
            self.logger.warning(f"Failed to decrypt cache data: {e}")
            # Attempt to read as unencrypted for backward compatibility
            return json.loads(encrypted_data.decode('utf-8'))

    @property
    def is_enabled(self) -> bool:
        """Check if encryption is enabled"""
        return self.fernet is not None
```

#### **Mandatory Security Implementation**

```python
# backend/app/infrastructure/cache/security.py (Security-First)
# Mandatory security configuration - no optional fields

@dataclass
class SecurityConfig:
    """Mandatory security configuration - all fields required"""

    # Required authentication (no optional fields)
    redis_auth: str
    encryption_key: str

    # Required TLS (always enabled)
    use_tls: bool = True
    tls_cert_path: str = ""  # Auto-generated if empty

    # Environment-specific settings
    environment: Environment = Environment.DEVELOPMENT

    @classmethod
    def create_for_environment(cls) -> 'SecurityConfig':
        """Create secure configuration appropriate for detected environment"""
        from app.core.environment import get_environment_info, FeatureContext

        env_info = get_environment_info(FeatureContext.SECURITY_ENFORCEMENT)

        if env_info.environment == Environment.PRODUCTION:
            return cls(
                redis_auth=generate_secure_password(32),
                encryption_key=Fernet.generate_key().decode(),
                tls_cert_path="/etc/ssl/redis-client.crt",
                environment=Environment.PRODUCTION
            )
        elif env_info.environment == Environment.STAGING:
            return cls(
                redis_auth=generate_secure_password(24),
                encryption_key=Fernet.generate_key().decode(),
                tls_cert_path="/etc/ssl/redis-staging.crt",
                environment=Environment.STAGING
            )
        else:  # Development
            return cls(
                redis_auth=generate_secure_password(16),
                encryption_key=Fernet.generate_key().decode(),
                tls_cert_path="",  # Will auto-generate self-signed
                environment=Environment.DEVELOPMENT
            )

    def __post_init__(self):
        """Validate that all security requirements are met"""
        if not self.redis_auth:
            raise ConfigurationError("Redis authentication is mandatory")
        if not self.encryption_key:
            raise ConfigurationError("Encryption key is mandatory")
        if not self.use_tls:
            raise ConfigurationError("TLS is mandatory for all environments")

    @property
    def security_level(self) -> str:
        """Security level based on environment"""
        return f"{self.environment.value.upper()}_SECURE"

class RedisCacheSecurityManager:
    """Security manager with mandatory validation - no insecure options"""

    def validate_mandatory_security(self, redis_url: str) -> None:
        """Validate that all security requirements are met (fail-fast)"""

        # Require TLS in ALL environments
        if not redis_url.startswith('rediss://'):
            raise ConfigurationError(
                "🔒 SECURITY ERROR: Only secure Redis connections allowed.\n"
                "\n"
                "Current: insecure connection\n"
                "Required: TLS-enabled connection (rediss://)\n"
                "\n"
                "Fix:\n"
                "1. Change REDIS_URL to rediss://your-redis:6380\n"
                "2. Run: ./scripts/setup-secure-redis.sh\n"
                "\n"
                "ℹ️ This application requires security in ALL environments."
            )

        # Require authentication
        if not self.config.redis_auth:
            raise ConfigurationError("Redis authentication is mandatory")

        # Require encryption
        if not self.config.encryption_key:
            raise ConfigurationError("Data encryption is mandatory")

        logger.info("✅ Security validation passed")

def generate_secure_password(length: int) -> str:
    """Generate cryptographically secure password"""
    import secrets, string
    alphabet = string.ascii_letters + string.digits + "!@#$%^&*-_=+"
    return ''.join(secrets.choice(alphabet) for _ in range(length))

def create_security_config_from_env() -> SecurityConfig:
    """Create mandatory security config from environment"""
    import os

    # Security config is always required - no None return
    return SecurityConfig(
        redis_auth=os.getenv("REDIS_AUTH") or generate_secure_password(16),
        encryption_key=os.getenv("REDIS_ENCRYPTION_KEY") or Fernet.generate_key().decode(),
        use_tls=True,  # Always required
        tls_cert_path=os.getenv("REDIS_TLS_CERT_PATH", ""),
    )
```

#### **Always-Secure GenericRedisCache**

```python
# backend/app/infrastructure/cache/redis_generic.py (Security-First)
from app.infrastructure.cache.encryption import EncryptedCacheLayer
from app.infrastructure.cache.security import RedisCacheSecurityManager, SecurityConfig
from app.core.exceptions import ConfigurationError
import logging
import os

class GenericRedisCache:
    """Redis cache with mandatory security - no insecure options"""

    def __init__(self, redis_url: str):
        """Initialize with mandatory security validation"""

        self.logger = logging.getLogger(__name__)

        # Security is always required - no optional parameter
        self.security_config = SecurityConfig.create_for_environment()
        self.security_manager = RedisCacheSecurityManager(self.security_config)

        # Validate security before connecting (fail-fast)
        self.security_manager.validate_mandatory_security(redis_url)

        # Initialize encryption (always enabled)
        self.encryption = EncryptedCacheLayer(self.security_config.encryption_key)

        # Create secure connection
        self.redis_client = self.security_manager.create_secure_connection(redis_url)

        self.logger.info(f"✅ Secure Redis cache initialized: TLS + Encryption + Auth")

    def _serialize_value(self, value: Any) -> bytes:
        """Always encrypt data before storage"""
        return self.encryption.encrypt_cache_data(value)

    def _deserialize_value(self, data: bytes) -> Any:
        """Always decrypt data after retrieval"""
        return self.encryption.decrypt_cache_data(data)

    @classmethod
    def create_secure(cls) -> 'GenericRedisCache':
        """Factory method for secure cache creation"""
        redis_url = os.getenv('REDIS_URL', 'rediss://localhost:6380')
        return cls(redis_url)

    # Rest of existing GenericRedisCache methods remain unchanged
    # All data is automatically encrypted/decrypted transparently
```

#### **AIResponseCache with Automatic Security**

```python
# backend/app/infrastructure/cache/redis_ai.py (Simplified)
from app.infrastructure.cache.redis_generic import GenericRedisCache
import os

class AIResponseCache(GenericRedisCache):
    """AI response cache with automatic security inheritance"""

    def __init__(self):
        # Security is automatically configured - no parameters needed
        redis_url = os.getenv('REDIS_URL', 'rediss://localhost:6380')
        super().__init__(redis_url)

        # AI-specific configuration (all on top of secure base)
        self.default_ttl = 3600
        self.compression_threshold = 1024

    # All existing AIResponseCache methods remain unchanged
    # Security (TLS + Auth + Encryption) is handled transparently by parent class
```

#### **Cache Manager with Fallback Strategy**

```python
# backend/app/infrastructure/cache/manager.py
from app.infrastructure.cache.redis_generic import GenericRedisCache
from app.infrastructure.cache.memory import MemoryCache
import logging

class CacheManager:
    """Intelligent cache management with secure Redis → Memory fallback"""

    def __init__(self):
        self.logger = logging.getLogger(__name__)

        try:
            # Always try secure Redis first
            self.cache = GenericRedisCache.create_secure()
            self.cache_type = "redis_secure"
            self.logger.info("✅ Using secure Redis cache")
        except (ConnectionError, ConfigurationError) as e:
            # Graceful fallback to memory cache
            self.logger.warning(f"Redis unavailable ({e}), falling back to memory cache")
            self.cache = MemoryCache()  # From memory.pyi contract
            self.cache_type = "memory"

    async def get(self, key: str):
        """Get value with transparent security"""
        return await self.cache.get(key)

    async def set(self, key: str, value, ttl: int = None):
        """Set value with transparent security"""
        return await self.cache.set(key, value, ttl)
```

---

---

### **8. Development Roadmap**

#### **Phase 1: Production Security Enforcement (Week 1)**

**Scope:** Implement startup security validation to enforce TLS in production environments.

**Deliverables:**
- `RedisSecurityValidator` class for startup validation
- Environment-aware TLS enforcement logic
- Clear error messages and configuration guidance
- Integration with existing environment detection service
- Unit tests for validation logic

**Acceptance Criteria:**
- Application fails fast with clear error in production without TLS
- Development environments continue working without TLS
- Explicit insecure override mechanism available
- Comprehensive error messages guide configuration fixes

#### **Phase 2: Automated TLS Setup (Week 1)**

**Scope:** Provide automated tools for TLS-enabled Redis setup.

**Deliverables:**
- `scripts/init-redis-tls.sh` certificate generation script
- `docker-compose.secure.yml` with TLS-enabled Redis configuration
- Internal Docker network isolation
- Health checks for TLS connections
- Documentation for local development setup

**Acceptance Criteria:**
- Single script generates all required TLS certificates
- Docker configuration successfully establishes TLS connections
- Redis isolated within internal Docker networks
- Clear setup instructions for developers

#### **Phase 1: Security-First Foundation (Week 1)**

**Scope:** Implement mandatory security for all Redis cache operations.

**Deliverables:**
- Mandatory `SecurityConfig` with environment-aware generation in `backend/app/infrastructure/cache/security.py`
- Always-secure `GenericRedisCache` implementation in `backend/app/infrastructure/cache/redis_generic.py`
- Fail-fast security validation in `RedisCacheSecurityManager`
- `EncryptedCacheLayer` for mandatory data encryption
- Automated TLS certificate generation scripts

**Acceptance Criteria:**
- Zero configuration paths that result in insecure connections
- Application fails immediately if security requirements not met
- All environments enforce TLS and encryption requirements
- Performance impact under 15% for typical operations

#### **Phase 2: Simplified Cache Architecture (Week 0.5)**

**Scope:** Implement always-secure cache implementations with graceful fallback.

**Deliverables:**
- Simplified `AIResponseCache` with automatic security inheritance in `backend/app/infrastructure/cache/redis_ai.py`
- `CacheManager` with Redis → Memory fallback in `backend/app/infrastructure/cache/manager.py`
- Always-on encryption for all cached data
- Removal of all optional security parameters

**Acceptance Criteria:**
- All cache operations are encrypted by default
- No code paths for unencrypted data storage or retrieval
- Graceful fallback to memory cache when Redis unavailable
- Simplified API surface with security built-in

#### **Phase 3: Developer Tooling & Documentation (Week 0.5)**

**Scope:** Provide one-command setup and clear documentation.

**Deliverables:**
- One-command secure setup script (`scripts/setup-secure-redis.sh`)
- Always-secure Docker configuration (`docker-compose.secure.yml`)
- Clear error messages for security violations
- Updated documentation for security-first approach
- Performance benchmarking for encryption overhead

**Acceptance Criteria:**
- Developers can set up secure Redis in one command
- Clear guidance when security requirements aren't met
- Zero-configuration secure development environment
- Comprehensive security documentation

---

### **9. Implementation Benefits**

#### **Security Benefits**
- **Eliminates security misconfiguration** - no insecure options available
- **Prevents accidental insecure deployments** - application won't start
- **Uniform security posture** across all environments
- **Compliance readiness** - encryption at rest and in transit by default

#### **Developer Experience Benefits**
- **Zero security configuration** - works securely out of the box
- **One setup command** - `./scripts/setup-secure-redis.sh`
- **Clear error messages** - immediate guidance when issues occur
- **Graceful fallback** - memory cache when Redis unavailable

#### **Code Quality Benefits**
- **Dramatically simplified codebase** - single secure code path
- **Easier testing** - one security mode to test
- **Clear architecture** - security is foundational, not optional
- **Reduced maintenance** - no fallback logic to maintain

---

### **10. Success Metrics**

We will measure the success of this initiative through the following metrics:

* **Security Posture:** 100% of deployments use TLS + encryption with zero insecure connections possible.
* **Developer Onboarding:** One-command setup success rate for new developers setting up secure Redis.
* **Code Quality:** Single, always-secure Redis implementation with graceful memory fallback.
* **Performance:** Encryption overhead remains under 15% for typical cache operations.

---

### **11. Migration Strategy**

Since this approach eliminates backward compatibility, we provide:

1. **Clear documentation** of the breaking change in release notes
2. **Migration script** (`scripts/migrate-to-secure-redis.sh`) to generate secure configuration
3. **Step-by-step migration guide** in documentation
4. **One-command setup** for new secure Redis environment

**For Template Users:**
- Template provides secure foundation from day one
- No migration needed - start with security built-in
- Educational value - learn secure patterns from the beginning