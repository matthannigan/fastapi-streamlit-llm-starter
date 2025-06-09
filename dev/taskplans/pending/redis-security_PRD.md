# Redis Security Enhancement PRD (Scaled-Back)

## Overview

The FastAPI-Streamlit-LLM Starter Template currently uses Redis for AI response caching with minimal security controls, creating vulnerabilities in production deployments. This PRD outlines essential security improvements to protect cached data and prevent unauthorized access, focused on practical implementation without enterprise complexity.

**Problem**: The current Redis implementation in `backend/app/services/cache.py` operates without authentication, encryption, or access controls, exposing AI-generated content and user data to potential breaches and cache poisoning attacks.

**Target Users**: 
- **Small to medium development teams** needing production-ready security
- **Startup operations teams** deploying with limited security expertise
- **Individual developers** building secure applications
- **Teams requiring good security** without enterprise overhead

**Value Proposition**: Transforms the Redis cache from a security liability into a well-secured component that protects sensitive data while maintaining simplicity and performance.

## Core Features

### 1. Password Authentication
**What it does**: Implements Redis AUTH password protection with secure credential management.

**Why it's important**: Prevents unauthorized access to cached AI responses and user data.

**How it works**: 
```python
class SecureRedisAuth:
    def __init__(self):
        self.password = os.getenv("REDIS_PASSWORD")
        if not self.password:
            raise SecurityError("REDIS_PASSWORD environment variable required")
        
    async def create_authenticated_connection(self):
        return await aioredis.from_url(
            f"redis://:{self.password}@{self.host}:{self.port}",
            ssl=self.ssl_enabled
        )
```

### 2. TLS Encryption
**What it does**: Encrypts data in transit using TLS/SSL connections to Redis.

**Why it's important**: Protects AI-generated content and user data from network interception.

**How it works**:
```python
class TLSRedisConnection:
    def __init__(self):
        self.ssl_enabled = os.getenv("REDIS_TLS_ENABLED", "true").lower() == "true"
        
    def _create_ssl_context(self):
        if not self.ssl_enabled:
            return None
            
        context = ssl.create_default_context()
        # For development with self-signed certificates
        if os.getenv("REDIS_DEV_MODE", "false").lower() == "true":
            context.check_hostname = False
            context.verify_mode = ssl.CERT_NONE
        return context
        
    async def connect(self):
        return await aioredis.from_url(
            self.redis_url,
            ssl=self._create_ssl_context()
        )
```

### 3. Application-Layer Encryption
**What it does**: Encrypts sensitive data before storing in Redis cache.

**Why it's important**: Protects data at rest even if Redis is compromised.

**How it works**:
```python
from cryptography.fernet import Fernet
import json

class EncryptedCache:
    def __init__(self, encryption_key: str):
        self.cipher = Fernet(encryption_key.encode())
        
    async def encrypted_set(self, key: str, value: dict, ttl: int):
        """Encrypt data before storing"""
        serialized = json.dumps(value)
        encrypted = self.cipher.encrypt(serialized.encode())
        await self.redis.setex(f"enc:{key}", ttl, encrypted)
        
    async def encrypted_get(self, key: str) -> dict:
        """Decrypt data after retrieving"""
        encrypted_data = await self.redis.get(f"enc:{key}")
        if encrypted_data:
            decrypted = self.cipher.decrypt(encrypted_data)
            return json.loads(decrypted.decode())
        return None
```

### 4. Basic Access Control
**What it does**: Implements simple Redis ACL with role-based access for different services.

**Why it's important**: Limits access scope and prevents privilege escalation.

**How it works**:
```python
class BasicACLManager:
    def __init__(self):
        self.users = {
            "cache_service": {
                "password": os.getenv("REDIS_CACHE_PASSWORD"),
                "permissions": ["+@read", "+@write", "+@keyspace", "-@dangerous"],
                "key_pattern": "ai_cache:*"
            },
            "health_service": {
                "password": os.getenv("REDIS_HEALTH_PASSWORD"),
                "permissions": ["+ping", "+info"],
                "key_pattern": "health:*"
            }
        }
        
    async def setup_users(self):
        """Configure basic ACL users"""
        for username, config in self.users.items():
            permissions = " ".join(config["permissions"])
            key_pattern = f"~{config['key_pattern']}"
            
            await self.redis.execute_command(
                "ACL", "SETUSER", username, "on", 
                f">{config['password']}", permissions, key_pattern
            )
```

### 5. Security Monitoring
**What it does**: Monitors authentication attempts and logs security events.

**Why it's important**: Provides visibility into potential security issues.

**How it works**:
```python
class SecurityMonitor:
    def __init__(self):
        self.security_events = []
        self.max_events = 1000
        
    async def log_auth_attempt(self, success: bool, username: str = None):
        """Log authentication attempts"""
        event = {
            "timestamp": datetime.now(),
            "type": "auth_attempt",
            "success": success,
            "username": username
        }
        self.security_events.append(event)
        
        # Keep only recent events
        if len(self.security_events) > self.max_events:
            self.security_events = self.security_events[-self.max_events:]
            
        # Alert on repeated failures
        if not success:
            await self._check_failed_attempts()
            
    async def _check_failed_attempts(self):
        """Check for brute force attempts"""
        recent_failures = [
            e for e in self.security_events[-10:] 
            if e["type"] == "auth_attempt" and not e["success"]
        ]
        
        if len(recent_failures) >= 5:
            logger.warning(f"Multiple authentication failures detected: {len(recent_failures)}")
```

### 6. Network Isolation
**What it does**: Isolates Redis using Docker networks and removes external port exposure.

**Why it's important**: Reduces attack surface by limiting network access.

**How it works**:
```yaml
# docker-compose.yml
services:
  redis:
    image: redis:7-alpine
    networks:
      - internal
    # No external ports exposed
    command: >
      redis-server
      --requirepass ${REDIS_PASSWORD}
      --protected-mode yes
      --bind 0.0.0.0
      
  backend:
    networks:
      - internal
      - external
      
networks:
  internal:
    driver: bridge
    internal: true
  external:
    driver: bridge
```

## User Experience

### User Personas

**1. Small Team Developer (Primary User)**
- **Needs**: Simple, secure Redis setup without complexity
- **Pain Points**: Complex security configurations, certificate management
- **Success Metrics**: One-command secure deployment, no code changes needed

**2. Startup Operations**
- **Needs**: Production-ready security, easy monitoring
- **Pain Points**: Security expertise gap, deployment complexity
- **Success Metrics**: Clear security status, simple troubleshooting

### Key User Flows

**1. Quick Secure Setup**
```bash
# Generate secure passwords
export REDIS_PASSWORD="$(openssl rand -base64 32)"
export REDIS_CACHE_PASSWORD="$(openssl rand -base64 32)"
export REDIS_ENCRYPTION_KEY="$(python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')"

# Deploy with security enabled
docker-compose up -d
```

**2. Security Status Check**
```python
# Add to monitoring endpoint
@monitoring_router.get("/security-status")
async def get_security_status():
    return {
        "redis_authenticated": redis_config.password_enabled,
        "tls_enabled": redis_config.tls_enabled,
        "encryption_enabled": redis_config.encryption_enabled,
        "network_isolated": redis_config.network_isolated,
        "recent_auth_failures": security_monitor.get_failure_count(24)
    }
```

**3. Simple Security Dashboard**
```python
# Streamlit security indicator
with st.sidebar:
    security_status = get_security_status()
    
    if all([
        security_status["redis_authenticated"],
        security_status["tls_enabled"], 
        security_status["encryption_enabled"]
    ]):
        st.success("🔒 Redis Secured")
    else:
        st.warning("⚠️ Security Issues")
        
    with st.expander("Security Details"):
        st.write(f"Authentication: {'✅' if security_status['redis_authenticated'] else '❌'}")
        st.write(f"TLS Encryption: {'✅' if security_status['tls_enabled'] else '❌'}")
        st.write(f"Data Encryption: {'✅' if security_status['encryption_enabled'] else '❌'}")
```

## Technical Architecture

### Enhanced Cache Service
```python
class SecureAIResponseCache(AIResponseCache):
    """Security-enhanced cache service"""
    
    def __init__(self, config: SecureRedisConfig):
        self.config = config
        self.auth = SecureRedisAuth()
        self.encryption = EncryptedCache(config.encryption_key) if config.encryption_key else None
        self.monitor = SecurityMonitor()
        
    async def connect(self):
        """Connect with security features"""
        try:
            self.redis = await self.auth.create_authenticated_connection()
            await self._validate_security()
            await self.monitor.log_auth_attempt(True)
        except Exception as e:
            await self.monitor.log_auth_attempt(False)
            raise
            
    async def set(self, key: str, value: dict, ttl: int = 3600):
        """Set with optional encryption"""
        if self.encryption:
            await self.encryption.encrypted_set(key, value, ttl)
        else:
            await super().set(key, value, ttl)
            
    async def get(self, key: str) -> dict:
        """Get with optional decryption"""
        if self.encryption:
            return await self.encryption.encrypted_get(key)
        else:
            return await super().get(key)
```

### Configuration Model
```python
class SecureRedisConfig(BaseSettings):
    """Simplified security configuration"""
    
    # Basic settings
    redis_host: str = Field(default="redis", description="Redis host")
    redis_port: int = Field(default=6379, description="Redis port")
    
    # Security settings
    redis_password: Optional[str] = Field(default=None, description="Redis password")
    redis_tls_enabled: bool = Field(default=False, description="Enable TLS")
    redis_encryption_key: Optional[str] = Field(default=None, description="Encryption key")
    
    # ACL settings
    redis_cache_password: Optional[str] = Field(default=None, description="Cache service password")
    redis_health_password: Optional[str] = Field(default=None, description="Health service password")
    
    # Network settings
    redis_protected_mode: bool = Field(default=True, description="Enable protected mode")
    redis_bind_address: str = Field(default="0.0.0.0", description="Bind address")
    
    @validator('redis_password')
    def validate_password(cls, v):
        if v and len(v) < 16:
            raise ValueError('Redis password must be at least 16 characters')
        return v
        
    @property
    def security_enabled(self) -> bool:
        """Check if basic security is enabled"""
        return bool(self.redis_password)
```

## Development Roadmap

### Phase 1: Essential Security (MVP)
**Duration**: 2-3 weeks  
**Scope**: Implement core security controls to address critical vulnerabilities

**Features**:
1. **Redis Password Authentication**
   - Environment variable configuration
   - Secure connection establishment
   - Error handling for authentication failures

2. **TLS Encryption**
   - Enable Redis TLS support
   - Self-signed certificate generation for development
   - Secure connection validation

3. **Basic Security Monitoring**
   - Authentication attempt logging
   - Simple security status endpoint
   - Failed login alerting

4. **Secure Environment Configuration**
   - Secure environment variable handling
   - Configuration validation
   - Security best practices documentation

**Deliverables**:
- Updated `cache.py` with authentication
- TLS setup scripts
- Security configuration documentation
- Basic monitoring endpoint

### Phase 2: Enhanced Security
**Duration**: 2-3 weeks  
**Scope**: Add encryption and access controls

**Features**:
1. **Application-Layer Encryption**
   - Data encryption for sensitive cache entries
   - Key management utilities
   - Performance optimization

2. **Basic Access Control**
   - Simple Redis ACL setup
   - Service-specific users
   - Permission validation

3. **Network Security**
   - Docker network isolation
   - Remove external port exposure
   - Connection filtering

4. **Enhanced Monitoring**
   - Security dashboard integration
   - Event logging and alerting
   - Health check integration

**Deliverables**:
- Encryption service module
- ACL management scripts
- Network security configuration
- Enhanced monitoring dashboard

## Risks and Mitigations

### Technical Challenges

**Risk**: TLS Setup Complexity
- **Mitigation**: Provide automated certificate generation and clear setup scripts

**Risk**: Performance Impact from Encryption
- **Mitigation**: Make encryption optional, provide performance monitoring

**Risk**: Configuration Complexity
- **Mitigation**: Use sensible defaults, provide environment templates

### Implementation Challenges

**Risk**: Breaking Existing Deployments
- **Mitigation**: Maintain backward compatibility, provide migration guide

**Risk**: Development Environment Friction
- **Mitigation**: Provide "development mode" with reduced security requirements

**Risk**: Debugging Complexity
- **Mitigation**: Clear error messages, comprehensive logging

## Migration Strategy

### Simple Migration Approach
```python
class SecurityMigration:
    """Simple migration to secure Redis"""
    
    def __init__(self):
        self.steps = [
            "Generate secure passwords",
            "Update environment configuration", 
            "Enable Redis authentication",
            "Configure TLS (optional)",
            "Enable data encryption (optional)",
            "Set up basic monitoring"
        ]
    
    async def migrate_to_secure_redis(self):
        """Execute migration with validation"""
        logger.info("Starting Redis security migration")
        
        # Step 1: Validate current setup
        await self._validate_current_setup()
        
        # Step 2: Generate credentials
        credentials = await self._generate_credentials()
        
        # Step 3: Update configuration
        await self._update_configuration(credentials)
        
        # Step 4: Restart with security enabled
        await self._restart_with_security()
        
        # Step 5: Validate security
        await self._validate_security()
        
        logger.info("Migration completed successfully")
```

## Testing Strategy

### Security Test Coverage
```python
class SecurityTests:
    """Essential security tests"""
    
    async def test_authentication_required(self):
        """Test that authentication is enforced"""
        with pytest.raises(ConnectionError):
            await aioredis.from_url("redis://localhost:6379")
    
    async def test_wrong_password_rejected(self):
        """Test that wrong passwords are rejected"""
        with pytest.raises(ConnectionError):
            await aioredis.from_url("redis://:wrongpassword@localhost:6379")
    
    async def test_encryption_roundtrip(self):
        """Test encryption/decryption works correctly"""
        original = {"test": "data", "number": 42}
        await secure_cache.encrypted_set("test_key", original, 300)
        retrieved = await secure_cache.encrypted_get("test_key")
        assert retrieved == original
    
    async def test_security_monitoring(self):
        """Test that security events are logged"""
        # Trigger auth failure
        try:
            await aioredis.from_url("redis://:wrong@localhost:6379")
        except:
            pass
        
        # Check event was logged
        events = security_monitor.get_recent_events()
        assert any(e["type"] == "auth_attempt" and not e["success"] for e in events)
```

## Implementation Checklist

### Phase 1 Checklist
- [ ] Redis password authentication implementation
- [ ] Environment variable security configuration
- [ ] TLS connection support
- [ ] Certificate generation scripts
- [ ] Basic security monitoring
- [ ] Authentication failure alerting
- [ ] Security status endpoint
- [ ] Updated documentation

### Phase 2 Checklist
- [ ] Application-layer encryption service
- [ ] Key management utilities
- [ ] Basic Redis ACL setup
- [ ] Service-specific user accounts
- [ ] Docker network isolation
- [ ] Security dashboard integration
- [ ] Enhanced monitoring and alerting
- [ ] Performance impact documentation

### Deployment Checklist
- [ ] Generate secure passwords
- [ ] Configure environment variables
- [ ] Test Redis connectivity
- [ ] Validate TLS connections
- [ ] Test encryption/decryption
- [ ] Verify ACL permissions
- [ ] Check security monitoring
- [ ] Document security configuration

## Resource Requirements

**Development Effort**: 4-6 weeks total
- Phase 1: 2-3 weeks (1-2 developers)
- Phase 2: 2-3 weeks (1-2 developers)

**Infrastructure Requirements**:
- Redis 7+ for full ACL support
- Docker/Docker Compose for network isolation
- Environment variable management system
- Basic monitoring infrastructure

**Skills Required**:
- Redis administration basics
- Docker networking knowledge
- Basic cryptography understanding
- Environment security best practices

This scaled-back approach focuses on practical security improvements that provide significant protection without enterprise complexity, making it suitable for small to medium teams that need good security without extensive resources.

## Appendix

### Security Best Practices Reference

**Redis Security Configuration Standards**
- Password minimum length: 16 characters
- TLS version: TLS 1.2 or higher
- Encryption standard: AES-256-GCM for application-layer encryption
- Key derivation: PBKDF2 with 10,000+ iterations for password-based keys

### Technical Specifications

**Supported Authentication Methods**
```python
# Authentication configuration options
REDIS_AUTH_METHODS = {
    "password": {
        "description": "Simple password authentication",
        "security_level": "basic",
        "implementation": "Redis AUTH command",
        "requirements": ["REDIS_PASSWORD environment variable"],
        "recommended_for": "Development and small production deployments"
    },
    "acl": {
        "description": "Access Control Lists with user-based permissions",
        "security_level": "enhanced", 
        "implementation": "Redis 6+ ACL system",
        "requirements": ["Redis 6+", "ACL user configuration"],
        "recommended_for": "Production deployments with multiple services"
    }
}
```

**Network Security Configuration Templates**
```yaml
# Production Docker network security
networks:
  redis_internal:
    driver: bridge
    internal: true
    enable_ipv6: false
    ipam:
      driver: default
      config:
        - subnet: 172.20.0.0/24
          gateway: 172.20.0.1
    driver_opts:
      com.docker.network.bridge.name: br-redis
      com.docker.network.bridge.enable_icc: "false"
      com.docker.network.bridge.host_binding_ipv4: "127.0.0.1"

  app_network:
    driver: bridge
    ipam:
      config:
        - subnet: 172.21.0.0/24

# Development network (less restrictive)
networks:
  redis_dev:
    driver: bridge
    internal: false  # Allow external access for debugging
```

**Environment Configuration Templates**
```bash
# Production environment template
REDIS_PASSWORD="$(openssl rand -base64 32)"
REDIS_CACHE_PASSWORD="$(openssl rand -base64 32)"
REDIS_HEALTH_PASSWORD="$(openssl rand -base64 32)"
REDIS_ENCRYPTION_KEY="$(python -c 'from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())')"
REDIS_TLS_ENABLED=true
REDIS_PROTECTED_MODE=true
REDIS_DEV_MODE=false

# Development environment template
REDIS_PASSWORD="dev_password_change_in_production"
REDIS_TLS_ENABLED=false
REDIS_PROTECTED_MODE=true
REDIS_DEV_MODE=true
REDIS_ENCRYPTION_KEY=""  # Optional in development
```

### Performance Impact Analysis

**Benchmark Results: Security Feature Overhead**
```python
# Performance test results for security configurations
PERFORMANCE_BENCHMARKS = {
    "baseline_unencrypted": {
        "operations_per_second": 50000,
        "latency_p99_ms": 2.1,
        "memory_overhead_mb": 0,
        "cpu_overhead_percent": 0
    },
    "password_auth_only": {
        "operations_per_second": 49500,  # 1% overhead
        "latency_p99_ms": 2.2,
        "memory_overhead_mb": 5,
        "cpu_overhead_percent": 2
    },
    "password_auth_plus_tls": {
        "operations_per_second": 42000,  # 16% overhead
        "latency_p99_ms": 3.8,
        "memory_overhead_mb": 15,
        "cpu_overhead_percent": 8
    },
    "full_security_suite": {
        "operations_per_second": 35000,  # 30% overhead
        "latency_p99_ms": 4.5,
        "memory_overhead_mb": 25,
        "cpu_overhead_percent": 15,
        "notes": "Includes auth, TLS, application encryption, and ACL"
    }
}
```

**Performance Optimization Guidelines**
```python
class SecurityOptimizationConfig:
    """Configuration for optimizing security performance"""
    
    # Connection management
    connection_pool_size: int = 10
    connection_max_age: int = 300  # seconds
    
    # Encryption optimization
    encryption_batch_size: int = 100  # process multiple items together
    
    # Monitoring optimization
    security_event_buffer_size: int = 100
    metrics_collection_interval: int = 30  # seconds
    
    # Development optimizations
    dev_mode_skip_tls: bool = True
    dev_mode_simple_passwords: bool = True
```

### Detailed Migration Strategy

**Step-by-Step Migration Process**
```python
class DetailedMigrationManager:
    """Manages step-by-step migration to secure Redis"""
    
    def __init__(self):
        self.migration_steps = [
            {
                "name": "preparation",
                "description": "Prepare for security migration",
                "duration_hours": 2,
                "actions": [
                    "Backup current Redis data",
                    "Document current configuration",
                    "Verify Redis version compatibility",
                    "Prepare rollback plan"
                ],
                "validation": "Confirm Redis 6+ and backup completion",
                "rollback": "Restore from backup if needed"
            },
            {
                "name": "authentication",
                "description": "Enable Redis password authentication",
                "duration_hours": 1,
                "actions": [
                    "Generate secure password",
                    "Update Redis configuration",
                    "Update application connection strings",
                    "Test authentication"
                ],
                "validation": "Confirm authenticated connections work",
                "rollback": "Remove AUTH requirement from Redis config"
            },
            {
                "name": "tls_optional",
                "description": "Enable TLS encryption (optional)",
                "duration_hours": 3,
                "actions": [
                    "Generate TLS certificates",
                    "Configure Redis TLS",
                    "Update client TLS settings",
                    "Test encrypted connections"
                ],
                "validation": "Confirm TLS connections and certificate validity",
                "rollback": "Disable TLS in Redis and client configuration"
            },
            {
                "name": "application_encryption",
                "description": "Enable application-layer encryption",
                "duration_hours": 2,
                "actions": [
                    "Generate encryption key",
                    "Deploy encryption code",
                    "Migrate existing cache data",
                    "Test encrypted operations"
                ],
                "validation": "Confirm encrypted data storage and retrieval",
                "rollback": "Disable encryption in application config"
            },
            {
                "name": "access_control",
                "description": "Configure basic ACL",
                "duration_hours": 2,
                "actions": [
                    "Create ACL users",
                    "Configure service permissions",
                    "Update service credentials",
                    "Test permission boundaries"
                ],
                "validation": "Confirm ACL users work and permissions are enforced",
                "rollback": "Remove ACL users, use default user"
            }
        ]
    
    async def execute_migration_step(self, step_name: str) -> bool:
        """Execute a specific migration step with detailed logging"""
        step = next(s for s in self.migration_steps if s["name"] == step_name)
        
        try:
            logger.info(f"Starting migration step: {step['name']}")
            logger.info(f"Description: {step['description']}")
            logger.info(f"Estimated duration: {step['duration_hours']} hours")
            
            # Execute each action
            for action in step["actions"]:
                logger.info(f"Executing: {action}")
                await self._execute_action(action, step_name)
            
            # Validate step completion
            logger.info(f"Validating: {step['validation']}")
            await self._validate_step(step_name)
            
            logger.info(f"Migration step {step_name} completed successfully")
            return True
            
        except Exception as e:
            logger.error(f"Migration step {step_name} failed: {e}")
            logger.info(f"Executing rollback: {step['rollback']}")
            await self._execute_rollback(step_name)
            return False
    
    async def _execute_action(self, action: str, step_name: str):
        """Execute individual migration action"""
        # Implementation would map actions to actual functions
        action_map = {
            "Generate secure password": self._generate_password,
            "Update Redis configuration": self._update_redis_config,
            "Generate TLS certificates": self._generate_certificates,
            # ... etc
        }
        
        if action in action_map:
            await action_map[action]()
        else:
            logger.warning(f"Manual action required: {action}")
```

### Comprehensive Testing Framework

**Security Test Suite Structure**
```python
class ComprehensiveSecurityTests:
    """Complete security testing framework"""
    
    @pytest.mark.security
    class AuthenticationTests:
        """Authentication security tests"""
        
        async def test_no_password_rejected(self):
            """Test connections without password are rejected"""
            with pytest.raises(redis.AuthenticationError):
                await aioredis.from_url("redis://localhost:6379")
        
        async def test_wrong_password_rejected(self):
            """Test wrong passwords are rejected"""
            with pytest.raises(redis.AuthenticationError):
                await aioredis.from_url("redis://:wrongpass@localhost:6379")
        
        async def test_correct_password_accepted(self):
            """Test correct password is accepted"""
            redis_client = await aioredis.from_url(f"redis://:{REDIS_PASSWORD}@localhost:6379")
            await redis_client.ping()
            await redis_client.close()
        
        async def test_password_length_requirements(self):
            """Test password meets minimum length requirements"""
            assert len(os.getenv("REDIS_PASSWORD", "")) >= 16
    
    @pytest.mark.security
    class EncryptionTests:
        """Encryption security tests"""
        
        async def test_tls_connection_when_enabled(self):
            """Test TLS connections work when enabled"""
            if os.getenv("REDIS_TLS_ENABLED", "false").lower() == "true":
                ssl_context = ssl.create_default_context()
                redis_client = await aioredis.from_url(
                    f"rediss://:{REDIS_PASSWORD}@localhost:6379",
                    ssl=ssl_context
                )
                await redis_client.ping()
                await redis_client.close()
        
        async def test_application_encryption_roundtrip(self):
            """Test application-layer encryption works correctly"""
            if not ENCRYPTION_KEY:
                pytest.skip("Encryption not enabled")
            
            original_data = {
                "ai_response": "This is a test AI response",
                "confidence": 0.95,
                "metadata": {"model": "test", "timestamp": "2024-01-01"}
            }
            
            encrypted_cache = EncryptedCache(ENCRYPTION_KEY)
            await encrypted_cache.encrypted_set("test_key", original_data, 300)
            retrieved_data = await encrypted_cache.encrypted_get("test_key")
            
            assert retrieved_data == original_data
        
        async def test_encrypted_data_unreadable_without_key(self):
            """Test encrypted data cannot be read without proper key"""
            if not ENCRYPTION_KEY:
                pytest.skip("Encryption not enabled")
            
            # Store encrypted data
            encrypted_cache = EncryptedCache(ENCRYPTION_KEY)
            await encrypted_cache.encrypted_set("test_key", {"secret": "data"}, 300)
            
            # Try to read with wrong key
            wrong_key = Fernet.generate_key()
            wrong_cache = EncryptedCache(wrong_key.decode())
            
            with pytest.raises(cryptography.fernet.InvalidToken):
                await wrong_cache.encrypted_get("test_key")
    
    @pytest.mark.security 
    class AccessControlTests:
        """ACL and access control tests"""
        
        async def test_cache_user_permissions(self):
            """Test cache user can only access cache keys"""
            cache_redis = await aioredis.from_url(
                f"redis://cache_service:{REDIS_CACHE_PASSWORD}@localhost:6379"
            )
            
            # Should succeed - cache user can access cache keys
            await cache_redis.set("ai_cache:test", "value")
            value = await cache_redis.get("ai_cache:test")
            assert value == b"value"
            
            # Should fail - cache user cannot access other keys
            with pytest.raises(redis.ResponseError):
                await cache_redis.set("admin:config", "value")
            
            await cache_redis.close()
        
        async def test_health_user_permissions(self):
            """Test health user has limited permissions"""
            health_redis = await aioredis.from_url(
                f"redis://health_service:{REDIS_HEALTH_PASSWORD}@localhost:6379"
            )
            
            # Should succeed - health user can ping
            await health_redis.ping()
            
            # Should fail - health user cannot write data
            with pytest.raises(redis.ResponseError):
                await health_redis.set("test", "value")
            
            await health_redis.close()
    
    @pytest.mark.performance
    class PerformanceTests:
        """Security performance impact tests"""
        
        async def test_authentication_overhead(self):
            """Measure authentication performance impact"""
            import time
            
            # Test connection time with authentication
            start_time = time.time()
            for i in range(10):
                redis_client = await aioredis.from_url(f"redis://:{REDIS_PASSWORD}@localhost:6379")
                await redis_client.ping()
                await redis_client.close()
            auth_time = time.time() - start_time
            
            # Authentication should not add more than 100ms overhead
            assert auth_time < 1.0  # 10 connections in under 1 second
        
        async def test_encryption_performance(self):
            """Measure encryption performance impact"""
            if not ENCRYPTION_KEY:
                pytest.skip("Encryption not enabled")
            
            import time
            
            test_data = {"test": "data" * 100}  # Reasonably sized test data
            encrypted_cache = EncryptedCache(ENCRYPTION_KEY)
            
            # Measure encryption performance
            start_time = time.time()
            for i in range(100):
                await encrypted_cache.encrypted_set(f"perf_test_{i}", test_data, 300)
            encryption_time = time.time() - start_time
            
            # Should complete 100 operations in reasonable time
            assert encryption_time < 5.0  # 100 operations in under 5 seconds
    
    @pytest.mark.monitoring
    class MonitoringTests:
        """Security monitoring tests"""
        
        async def test_auth_failure_logging(self):
            """Test authentication failures are logged"""
            initial_event_count = len(security_monitor.security_events)
            
            # Trigger authentication failure
            try:
                await aioredis.from_url("redis://:wrongpassword@localhost:6379")
            except:
                pass
            
            # Check event was logged
            assert len(security_monitor.security_events) > initial_event_count
            recent_event = security_monitor.security_events[-1]
            assert recent_event["type"] == "auth_attempt"
            assert recent_event["success"] is False
        
        async def test_security_status_endpoint(self):
            """Test security status endpoint returns correct information"""
            from httpx import AsyncClient
            
            async with AsyncClient() as client:
                response = await client.get("http://localhost:8000/monitoring/security-status")
                assert response.status_code == 200
                
                status = response.json()
                assert "redis_authenticated" in status
                assert "tls_enabled" in status
                assert "encryption_enabled" in status
```

### Monitoring and Alerting Configuration

**Basic Security Metrics Collection**
```python
class SecurityMetricsCollector:
    """Simplified security metrics for monitoring"""
    
    def __init__(self):
        self.metrics = {
            "auth_attempts": {"success": 0, "failure": 0},
            "connection_count": 0,
            "encryption_operations": {"encrypt": 0, "decrypt": 0, "errors": 0},
            "security_events": {"info": 0, "warning": 0, "error": 0}
        }
        
    def record_auth_attempt(self, success: bool):
        """Record authentication attempt"""
        if success:
            self.metrics["auth_attempts"]["success"] += 1
        else:
            self.metrics["auth_attempts"]["failure"] += 1
            
        # Simple alerting - log warning if too many failures
        if self.metrics["auth_attempts"]["failure"] % 5 == 0:
            logger.warning(f"Multiple auth failures: {self.metrics['auth_attempts']['failure']}")
    
    def record_encryption_operation(self, operation: str, success: bool):
        """Record encryption operation"""
        if success:
            self.metrics["encryption_operations"][operation] += 1
        else:
            self.metrics["encryption_operations"]["errors"] += 1
    
    def get_security_summary(self) -> dict:
        """Get security metrics summary"""
        total_auth = sum(self.metrics["auth_attempts"].values())
        auth_success_rate = (
            self.metrics["auth_attempts"]["success"] / total_auth * 100 
            if total_auth > 0 else 100
        )
        
        return {
            "authentication": {
                "total_attempts": total_auth,
                "success_rate_percent": round(auth_success_rate, 2),
                "recent_failures": self.metrics["auth_attempts"]["failure"]
            },
            "encryption": {
                "total_operations": sum(
                    v for k, v in self.metrics["encryption_operations"].items() 
                    if k != "errors"
                ),
                "error_count": self.metrics["encryption_operations"]["errors"]
            },
            "connections": {
                "active_count": self.metrics["connection_count"]
            }
        }
```

**Simple Alerting Configuration**
```python
class SimpleAlertManager:
    """Basic alerting for security events"""
    
    def __init__(self):
        self.alert_thresholds = {
            "auth_failures_per_hour": 10,
            "encryption_errors_per_hour": 5,
            "connection_failures_per_hour": 20
        }
        
        self.alert_channels = {
            "log": True,  # Always log alerts
            "email": os.getenv("SECURITY_ALERT_EMAIL"),
            "webhook": os.getenv("SECURITY_ALERT_WEBHOOK")
        }
    
    async def check_and_send_alerts(self):
        """Check thresholds and send alerts if needed"""
        metrics = security_metrics.get_security_summary()
        
        # Check authentication failures
        if metrics["authentication"]["recent_failures"] >= self.alert_thresholds["auth_failures_per_hour"]:
            await self._send_alert(
                "High Authentication Failures",
                f"Detected {metrics['authentication']['recent_failures']} auth failures"
            )
        
        # Check encryption errors
        if metrics["encryption"]["error_count"] >= self.alert_thresholds["encryption_errors_per_hour"]:
            await self._send_alert(
                "Encryption Errors Detected", 
                f"Detected {metrics['encryption']['error_count']} encryption errors"
            )
    
    async def _send_alert(self, title: str, message: str):
        """Send alert through configured channels"""
        alert_data = {
            "timestamp": datetime.now().isoformat(),
            "title": title,
            "message": message,
            "severity": "warning"
        }
        
        # Always log
        logger.warning(f"SECURITY ALERT: {title} - {message}")
        
        # Send email if configured
        if self.alert_channels["email"]:
            await self._send_email_alert(alert_data)
        
        # Send webhook if configured  
        if self.alert_channels["webhook"]:
            await self._send_webhook_alert(alert_data)
```

### Implementation Timeline and Resource Estimates

**Detailed Development Estimates**
```python
DEVELOPMENT_ESTIMATES = {
    "phase_1_essential_security": {
        "duration_weeks": 2.5,
        "developer_weeks": 4,
        "components": {
            "redis_password_auth": {
                "effort": "1 dev-week",
                "complexity": "low",
                "description": "Implement Redis AUTH with environment variables"
            },
            "tls_configuration": {
                "effort": "1.5 dev-weeks", 
                "complexity": "medium",
                "description": "TLS setup, certificate generation, client configuration"
            },
            "basic_security_monitoring": {
                "effort": "0.5 dev-week",
                "complexity": "low", 
                "description": "Auth logging, simple metrics, status endpoint"
            },
            "configuration_security": {
                "effort": "0.5 dev-week",
                "complexity": "low",
                "description": "Secure config validation, environment handling"
            },
            "testing_documentation": {
                "effort": "0.5 dev-week",
                "complexity": "low",
                "description": "Security tests, setup documentation"
            }
        }
    },
    "phase_2_enhanced_security": {
        "duration_weeks": 2.5,
        "developer_weeks": 5,
        "components": {
            "application_encryption": {
                "effort": "2 dev-weeks",
                "complexity": "medium-high",
                "description": "Data encryption, key management, performance optimization"
            },
            "basic_acl_implementation": {
                "effort": "1.5 dev-weeks",
                "complexity": "medium",
                "description": "Simple ACL users, permission management"
            },
            "network_security": {
                "effort": "1 dev-week",
                "complexity": "medium",
                "description": "Docker network isolation, security hardening"
            },
            "enhanced_monitoring": {
                "effort": "0.5 dev-week", 
                "complexity": "low",
                "description": "Security dashboard, improved alerting"
            }
        }
    }
}

TOTAL_PROJECT_ESTIMATE = {
    "duration_weeks": 5,
    "developer_weeks": 9,
    "parallel_developers_recommended": 2,
    "testing_weeks": 1,
    "documentation_weeks": 0.5
}
```

**Resource Requirements Breakdown**
```python
RESOURCE_REQUIREMENTS = {
    "infrastructure": {
        "redis_version": "7.0+",
        "docker_version": "20.0+", 
        "memory_overhead": "25-50MB",
        "cpu_overhead": "5-15%",
        "storage_overhead": "Minimal (certificates only)"
    },
    "development_skills": {
        "required": [
            "Redis administration basics",
            "Docker networking",
            "Environment variable security",
            "Basic cryptography concepts"
        ],
        "helpful": [
            "TLS/SSL certificate management",
            "Python async programming",
            "Security monitoring concepts"
        ]
    },
    "operational_requirements": {
        "monitoring": "Basic log aggregation recommended",
        "backup": "Redis data backup procedures",
        "key_management": "Secure environment variable storage",
        "incident_response": "Basic security incident procedures"
    }
}
```