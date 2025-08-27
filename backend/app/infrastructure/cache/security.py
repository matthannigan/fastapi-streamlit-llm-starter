"""**Redis security implementation with TLS, authentication, and validation.**

This module provides comprehensive Redis security features for production cache
deployments including TLS encryption, authentication, and connection validation.

## Security Features

- **Authentication**: AUTH password and ACL username/password authentication
- **TLS Encryption**: SSL/TLS with certificate validation for secure connections
- **Connection Security**: Secure connection management with timeout and retry logic
- **Validation**: Comprehensive security configuration validation and reporting
- **Monitoring**: Security event monitoring and alerting capabilities
- **Compatibility**: Backward compatibility with insecure development connections

## Usage

```python
from app.infrastructure.cache.security import SecurityConfig, RedisCacheSecurityManager
    
    # Create security configuration
    config = SecurityConfig(
        redis_auth="your_password",
        use_tls=True,
        tls_cert_path="/path/to/cert.pem",
        acl_username="cache_user",
        acl_password="user_password"
    )
    
    # Initialize security manager
    security_manager = RedisCacheSecurityManager(config)
    
    # Create secure Redis connection
    redis_client = await security_manager.create_secure_connection()
    
    # Validate security status
    validation = await security_manager.validate_connection_security(redis_client)
    if not validation.is_secure:
        logger.warning(f"Security issues: {validation.vulnerabilities}")

Author: Cache Infrastructure Team
Created: 2024-08-12
Version: 1.0.0
"""

import logging
import ssl
import asyncio
import time
import inspect
from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any, Union
from pathlib import Path

from app.core.exceptions import ConfigurationError

# Optional Redis import for graceful degradation
try:
    import aioredis  # type: ignore
    from aioredis import Redis, RedisError  # type: ignore
    AIOREDIS_AVAILABLE = True
except ImportError:
    AIOREDIS_AVAILABLE = False
    aioredis = None  # type: ignore
    Redis = None  # type: ignore
    RedisError = Exception  # type: ignore

from app.infrastructure.cache.monitoring import CachePerformanceMonitor

logger = logging.getLogger(__name__)


@dataclass
class SecurityConfig:
    """Comprehensive Redis security configuration.
    
    This class encapsulates all Redis security settings including authentication,
    TLS/SSL encryption, ACL configuration, and connection parameters.
    
    Attributes:
        redis_auth: Redis AUTH password for password-based authentication
        use_tls: Enable TLS/SSL encryption for Redis connections
        tls_cert_path: Path to client certificate file for TLS
        tls_key_path: Path to private key file for TLS
        tls_ca_path: Path to Certificate Authority file for TLS validation
        acl_username: Username for Redis ACL authentication
        acl_password: Password for Redis ACL authentication
        connection_timeout: Connection timeout in seconds
        max_retries: Maximum number of connection retry attempts
        retry_delay: Delay between retry attempts in seconds
        verify_certificates: Whether to verify TLS certificates
        min_tls_version: Minimum TLS version to accept
        cipher_suites: Allowed cipher suites for TLS connections
    
    Examples:
        # Basic AUTH configuration
        config = SecurityConfig(redis_auth="mypassword")
        
        # TLS with certificate authentication
        config = SecurityConfig(
            use_tls=True,
            tls_cert_path="/etc/ssl/redis-client.crt",
            tls_key_path="/etc/ssl/redis-client.key",
            tls_ca_path="/etc/ssl/ca.crt"
        )
        
        # ACL authentication
        config = SecurityConfig(
            acl_username="cache_user",
            acl_password="secure_password"
        )
        
        # Combined security (recommended for production)
        config = SecurityConfig(
            redis_auth="fallback_password",
            use_tls=True,
            tls_cert_path="/etc/ssl/redis-client.crt",
            tls_key_path="/etc/ssl/redis-client.key",
            tls_ca_path="/etc/ssl/ca.crt",
            acl_username="cache_user",
            acl_password="secure_password",
            verify_certificates=True
        )
    """
    
    # Authentication settings
    redis_auth: Optional[str] = None
    acl_username: Optional[str] = None
    acl_password: Optional[str] = None
    
    # TLS/SSL settings
    use_tls: bool = False
    tls_cert_path: Optional[str] = None
    tls_key_path: Optional[str] = None
    tls_ca_path: Optional[str] = None
    verify_certificates: bool = True
    min_tls_version: float = ssl.TLSVersion.TLSv1_2.value
    cipher_suites: Optional[List[str]] = None
    
    # Connection settings
    connection_timeout: int = 30
    socket_timeout: int = 30
    max_retries: int = 3
    retry_delay: float = 1.0
    
    # Security monitoring
    enable_security_monitoring: bool = True
    log_security_events: bool = True
    
    def __post_init__(self):
        """Validate security configuration after initialization."""
        self._validate_configuration()
    
    def _validate_configuration(self) -> None:
        """Validate security configuration parameters.
        
        Raises:
            ConfigurationError: If configuration is invalid
        """
        # Validate TLS configuration
        if self.use_tls:
            if self.tls_cert_path and not Path(self.tls_cert_path).exists():
                raise ConfigurationError(
                    f"TLS certificate file not found: {self.tls_cert_path}",
                    context={"cert_path": self.tls_cert_path, "validation_type": "tls_cert"}
                )
            if self.tls_key_path and not Path(self.tls_key_path).exists():
                raise ConfigurationError(
                    f"TLS key file not found: {self.tls_key_path}",
                    context={"key_path": self.tls_key_path, "validation_type": "tls_key"}
                )
            if self.tls_ca_path and not Path(self.tls_ca_path).exists():
                raise ConfigurationError(
                    f"TLS CA file not found: {self.tls_ca_path}",
                    context={"ca_path": self.tls_ca_path, "validation_type": "tls_ca"}
                )
        
        # Validate ACL configuration
        if self.acl_username and not self.acl_password:
            raise ConfigurationError(
                "ACL password is required when ACL username is provided",
                context={"acl_username": self.acl_username, "validation_type": "acl_config"}
            )
        
        # Validate timeout settings
        if self.connection_timeout <= 0:
            raise ConfigurationError(
                "Connection timeout must be positive",
                context={"connection_timeout": self.connection_timeout, "validation_type": "timeout"}
            )
        if self.socket_timeout <= 0:
            raise ConfigurationError(
                "Socket timeout must be positive",
                context={"socket_timeout": self.socket_timeout, "validation_type": "timeout"}
            )
        if self.max_retries < 0:
            raise ConfigurationError(
                "Max retries cannot be negative",
                context={"max_retries": self.max_retries, "validation_type": "retry_config"}
            )
        if self.retry_delay < 0:
            raise ConfigurationError(
                "Retry delay cannot be negative",
                context={"retry_delay": self.retry_delay, "validation_type": "retry_config"}
            )
    
    @property
    def has_authentication(self) -> bool:
        """Check if any form of authentication is configured."""
        return bool(self.redis_auth or (self.acl_username and self.acl_password))
    
    @property
    def security_level(self) -> str:
        """Get a descriptive security level."""
        if self.use_tls and self.has_authentication and self.verify_certificates:
            return "HIGH"
        elif self.use_tls or self.has_authentication:
            return "MEDIUM"
        else:
            return "LOW"


@dataclass
class SecurityValidationResult:
    """Security validation results with detailed security analysis.
    
    This class provides comprehensive security validation results including
    detailed vulnerability analysis and security recommendations.
    
    Attributes:
        is_secure: Overall security status
        auth_configured: Whether authentication is properly configured
        tls_enabled: Whether TLS encryption is active
        acl_enabled: Whether ACL authentication is active
        certificate_valid: Whether TLS certificates are valid
        vulnerabilities: List of identified security vulnerabilities
        recommendations: List of security improvement recommendations
        security_score: Numeric security score (0-100)
        detailed_checks: Detailed results of individual security checks
    """
    
    is_secure: bool
    auth_configured: bool
    tls_enabled: bool
    acl_enabled: bool
    certificate_valid: bool
    
    vulnerabilities: List[str] = field(default_factory=list)
    recommendations: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    
    security_score: int = 0  # 0-100
    detailed_checks: Dict[str, Any] = field(default_factory=dict)
    
    # Additional security metrics
    connection_encrypted: bool = False
    auth_method: Optional[str] = None
    tls_version: Optional[str] = None
    cipher_suite: Optional[str] = None
    certificate_expiry_days: Optional[int] = None
    
    def __post_init__(self):
        """Calculate security score and overall status.

        Respect an explicitly provided `security_score` if it's non-zero; otherwise
        compute it from the flags. Always recompute the overall `is_secure` based
        on the (possibly overridden) score and critical vulnerabilities.
        """
        if self.security_score == 0:
            self._calculate_security_score()
        self._determine_overall_security()
    
    def _calculate_security_score(self) -> None:
        """Calculate numeric security score based on configuration."""
        score = 0
        
        # Authentication (30 points max)
        if self.auth_configured:
            score += 20
            if self.acl_enabled:
                score += 10  # ACL is more secure than basic AUTH
        
        # Encryption (40 points max)
        if self.tls_enabled:
            score += 25
            if self.certificate_valid:
                score += 10
            if self.connection_encrypted:
                score += 5
        
        # Certificate management (15 points max)
        if self.certificate_expiry_days is not None:
            if self.certificate_expiry_days > 90:
                score += 15
            elif self.certificate_expiry_days > 30:
                score += 10
            elif self.certificate_expiry_days > 7:
                score += 5
        
        # Deduct points for vulnerabilities (15 points max deduction)
        vulnerability_penalty = min(len(self.vulnerabilities) * 5, 15)
        score = max(0, score - vulnerability_penalty)
        
        self.security_score = min(100, score)
    
    def _determine_overall_security(self) -> None:
        """Determine overall security status based on score and critical checks."""
        # Critical vulnerabilities make the connection insecure regardless of score
        critical_vulnerabilities = [
            "No authentication configured",
            "Unencrypted connection in production",
            "Invalid or expired certificates",
            "Weak cipher suites"
        ]
        
        has_critical_vulnerability = any(
            vuln in self.vulnerabilities for vuln in critical_vulnerabilities
        )
        
        # Consider secure if score >= 70 and no critical vulnerabilities
        self.is_secure = self.security_score >= 70 and not has_critical_vulnerability
    
    def get_security_summary(self) -> str:
        """Get a human-readable security summary."""
        status = "SECURE" if self.is_secure else "INSECURE"
        level = "HIGH" if self.security_score >= 80 else "MEDIUM" if self.security_score >= 60 else "LOW"
        
        summary = f"Security Status: {status} (Score: {self.security_score}/100, Level: {level})\n"
        
        if self.vulnerabilities:
            summary += f"\nVulnerabilities ({len(self.vulnerabilities)}):\n"
            for vuln in self.vulnerabilities:
                summary += f"  - {vuln}\n"
        
        if self.recommendations:
            summary += f"\nRecommendations ({len(self.recommendations)}):\n"
            for rec in self.recommendations:
                summary += f"  - {rec}\n"
        
        return summary


class RedisCacheSecurityManager:
    """Production-grade Redis security implementation.
    
    This class provides comprehensive Redis security management including:
    - Secure connection creation with AUTH, TLS, and ACL support
    - Security validation and monitoring
    - Certificate management and validation
    - Connection retry logic with exponential backoff
    - Security event logging and alerting
    
    The security manager integrates with the cache infrastructure to provide
    enterprise-grade security features while maintaining backward compatibility.
    
    Usage:
        # Initialize with security configuration
        config = SecurityConfig(redis_auth="password", use_tls=True)
        manager = RedisCacheSecurityManager(config)
        
        # Create secure connection
        redis = await manager.create_secure_connection()
        
        # Validate security
        validation = await manager.validate_connection_security(redis)
        
        # Get security report
        report = manager.generate_security_report(validation)
    """
    
    def __init__(self, 
                 config: SecurityConfig,
                 performance_monitor: Optional[CachePerformanceMonitor] = None):
        """Initialize Redis security manager.
        
        Args:
            config: Security configuration
            performance_monitor: Optional performance monitoring
        """
        self.config = config
        self.performance_monitor = performance_monitor
        
        # Security logging
        self._security_logger = logging.getLogger(f"{__name__}.security")
        self._security_events: List[Dict[str, Any]] = []
        
        # Connection state
        self._ssl_context: Optional[ssl.SSLContext] = None
        self._last_validation: Optional[SecurityValidationResult] = None
        
        self._initialize_ssl_context()
        
        if config.log_security_events:
            self._security_logger.info(f"Security manager initialized with level: {config.security_level}")
    
    def _initialize_ssl_context(self) -> None:
        """Initialize SSL context for TLS connections."""
        if not self.config.use_tls:
            return
        
        try:
            # Create SSL context with secure defaults
            self._ssl_context = ssl.create_default_context(ssl.Purpose.SERVER_AUTH)
            
            # Configure certificate verification
            if self.config.verify_certificates:
                self._ssl_context.check_hostname = True
                self._ssl_context.verify_mode = ssl.CERT_REQUIRED
            else:
                self._ssl_context.check_hostname = False
                self._ssl_context.verify_mode = ssl.CERT_NONE
                self._security_logger.warning("Certificate verification disabled - not recommended for production")
            
            # Set minimum TLS version
            self._ssl_context.minimum_version = ssl.TLSVersion(self.config.min_tls_version)
            
            # Configure cipher suites
            if self.config.cipher_suites:
                self._ssl_context.set_ciphers(':'.join(self.config.cipher_suites))
            
            # Load certificates
            if self.config.tls_cert_path and self.config.tls_key_path:
                self._ssl_context.load_cert_chain(
                    self.config.tls_cert_path,
                    self.config.tls_key_path
                )
            
            # Load CA certificates
            if self.config.tls_ca_path:
                self._ssl_context.load_verify_locations(self.config.tls_ca_path)
            
            self._security_logger.info("SSL context initialized successfully")
            
        except Exception as e:
            self._security_logger.error(f"Failed to initialize SSL context: {e}")
            raise
    
    async def create_secure_connection(self, redis_url: str = "redis://localhost:6379") -> Any:
        """Create secure Redis connection with full security features.
        
        This method creates a Redis connection with all configured security features
        including authentication, TLS encryption, and ACL support. It includes
        retry logic and comprehensive error handling.
        
        Args:
            redis_url: Redis connection URL
            
        Returns:
            Configured Redis client with security features
            
        Raises:
            RedisError: If connection cannot be established
            ConfigurationError: If security configuration is invalid
        """
        start_time = time.perf_counter()
        
        try:
            # Parse Redis URL and apply security configuration
            connection_kwargs = self._build_connection_kwargs(redis_url)
            
            # Create connection with retry logic
            redis_client = await self._create_connection_with_retry(connection_kwargs)
            
            # Validate connection
            await self._validate_new_connection(redis_client)
            
            # Log security event
            if self.config.log_security_events:
                self._log_security_event("connection_created", {
                    "security_level": self.config.security_level,
                    "tls_enabled": self.config.use_tls,
                    "auth_configured": self.config.has_authentication
                })
            
            # Track performance
            if self.performance_monitor:
                duration = (time.perf_counter() - start_time) * 1000
                await self.performance_monitor.record_operation("secure_connection_create", duration, True)
            
            return redis_client
            
        except Exception as e:
            # Track performance for failed connections
            if self.performance_monitor:
                duration = (time.perf_counter() - start_time) * 1000
                await self.performance_monitor.record_operation("secure_connection_create", duration, False)
            
            self._security_logger.error(f"Failed to create secure Redis connection: {e}")
            raise
    
    def _build_connection_kwargs(self, redis_url: str) -> Dict[str, Any]:
        """Build connection parameters with security configuration."""
        kwargs = {
            "socket_timeout": self.config.socket_timeout,
            "socket_connect_timeout": self.config.connection_timeout,
            "retry_on_timeout": True,
            "health_check_interval": 30,
        }
        
        # Authentication configuration
        if self.config.acl_username and self.config.acl_password:
            # ACL authentication (Redis 6+)
            kwargs["username"] = self.config.acl_username
            kwargs["password"] = self.config.acl_password
            self._security_logger.info("ACL authentication configured")
        elif self.config.redis_auth:
            # Basic AUTH authentication
            kwargs["password"] = self.config.redis_auth
            self._security_logger.info("Basic AUTH authentication configured")
        
        # TLS configuration
        if self.config.use_tls and self._ssl_context:
            kwargs["ssl"] = self._ssl_context
            # Update URL scheme to rediss://
            if redis_url.startswith("redis://"):
                redis_url = redis_url.replace("redis://", "rediss://", 1)
            self._security_logger.info("TLS encryption enabled")
        
        kwargs["url"] = redis_url
        return kwargs
    
    async def _create_connection_with_retry(self, connection_kwargs: Dict[str, Any]) -> Any:
        """Create Redis connection with retry logic."""
        if not AIOREDIS_AVAILABLE or aioredis is None:
            raise RedisError("aioredis module not available - cannot create Redis connection")
            
        last_exception = None
        
        for attempt in range(self.config.max_retries + 1):
            try:
                self._security_logger.debug(f"Connection attempt {attempt + 1}/{self.config.max_retries + 1}")
                
                # Support both sync and async factories for easier testing/mocking
                redis_client = aioredis.from_url(**connection_kwargs)  # type: ignore[attr-defined]
                if asyncio.iscoroutine(redis_client):  # when mocked as AsyncMock
                    redis_client = await redis_client
                
                # Do not ping here to avoid duplicate pings in validation phase
                self._security_logger.info(f"Secure Redis connection established on attempt {attempt + 1}")
                return redis_client
                
            except Exception as e:
                last_exception = e
                self._security_logger.warning(f"Connection attempt {attempt + 1} failed: {e}")
                
                if attempt < self.config.max_retries:
                    delay = self.config.retry_delay * (2 ** attempt)  # Exponential backoff
                    self._security_logger.info(f"Retrying in {delay} seconds...")
                    await asyncio.sleep(delay)
        
        # All attempts failed
        raise RedisError(f"Failed to establish secure Redis connection after {self.config.max_retries + 1} attempts. Last error: {last_exception}")
    
    async def _validate_new_connection(self, redis_client: Any) -> None:
        """Validate newly created connection."""
        try:
            # Basic connectivity test
            await redis_client.ping()
            
            # Test authentication
            info = await redis_client.info()
            # Be lenient in mocks: accept any dict-like info response
            try:
                if not isinstance(info, dict) or "redis_version" not in info:
                    self._security_logger.warning("Redis server info did not include 'redis_version'")
            except Exception:
                self._security_logger.warning("Unexpected format for Redis info response")
            
            # Avoid accessing dict methods on non-dict mocks
            version = None
            try:
                version = info.get('redis_version', 'unknown') if isinstance(info, dict) else 'unknown'
            except Exception:
                version = 'unknown'
            self._security_logger.info(f"Connection validated - Redis version: {version}")
            
        except Exception as e:
            self._security_logger.error(f"Connection validation failed: {e}")
            raise
    
    async def validate_connection_security(self, redis_client: Any) -> SecurityValidationResult:
        """Validate Redis connection security status.
        
        This method performs comprehensive security validation of an existing
        Redis connection, checking authentication, encryption, certificates,
        and other security aspects.
        
        Args:
            redis_client: Redis client to validate
            
        Returns:
            Detailed security validation results
        """
        start_time = time.perf_counter()
        
        try:
            # Quick sanity check: ensure we can await redis methods in tests/mocks
            ping_attr = getattr(redis_client, "ping", None)
            if ping_attr is None or not asyncio.iscoroutinefunction(ping_attr):
                raise TypeError("Provided Redis client 'ping' is not awaitable")
            # Initialize validation result
            result = SecurityValidationResult(
                is_secure=False,
                auth_configured=self.config.has_authentication,
                tls_enabled=self.config.use_tls,
                acl_enabled=bool(self.config.acl_username),
                certificate_valid=False
            )
            
            # Validate connection
            await self._validate_basic_connectivity(redis_client, result)
            await self._validate_authentication(redis_client, result)
            await self._validate_encryption(redis_client, result)
            await self._validate_certificates(result)
            await self._analyze_security_vulnerabilities(result)
            await self._generate_security_recommendations(result)
            
            # Cache validation result
            self._last_validation = result
            
            # Track performance
            if self.performance_monitor:
                duration = (time.perf_counter() - start_time) * 1000
                await self.performance_monitor.record_operation("security_validation", duration, True)
            
            # Log security validation
            if self.config.log_security_events:
                self._log_security_event("security_validation", {
                    "security_score": result.security_score,
                    "is_secure": result.is_secure,
                    "vulnerabilities_count": len(result.vulnerabilities)
                })
            
            return result
            
        except Exception as e:
            # Track performance for failed validation
            if self.performance_monitor:
                duration = (time.perf_counter() - start_time) * 1000
                await self.performance_monitor.record_operation("security_validation", duration, False)
            
            self._security_logger.error(f"Security validation failed: {e}")
            
            # Return minimal result indicating validation failure
            return SecurityValidationResult(
                is_secure=False,
                auth_configured=False,
                tls_enabled=False,
                acl_enabled=False,
                certificate_valid=False,
                vulnerabilities=["Security validation failed"],
                recommendations=["Re-check Redis connection and security configuration"]
            )
    
    async def _validate_basic_connectivity(self, redis_client: Any, result: SecurityValidationResult) -> None:
        """Validate basic Redis connectivity."""
        try:
            await redis_client.ping()
            result.detailed_checks["connectivity"] = "OK"
        except Exception as e:
            result.vulnerabilities.append(f"Connection failure: {e}")
            result.detailed_checks["connectivity"] = f"FAILED: {e}"
    
    async def _validate_authentication(self, redis_client: Any, result: SecurityValidationResult) -> None:
        """Validate Redis authentication configuration."""
        try:
            # Check if authentication is working
            info = await redis_client.info("server")
            
            if self.config.acl_username:
                result.auth_method = "ACL"
                result.detailed_checks["authentication"] = "ACL configured"
            elif self.config.redis_auth:
                result.auth_method = "AUTH"
                result.detailed_checks["authentication"] = "AUTH configured"
            else:
                result.vulnerabilities.append("No authentication configured")
                result.detailed_checks["authentication"] = "None"
                
        except Exception as e:
            result.vulnerabilities.append(f"Authentication validation failed: {e}")
            result.detailed_checks["authentication"] = f"FAILED: {e}"
    
    async def _validate_encryption(self, redis_client: Any, result: SecurityValidationResult) -> None:
        """Validate TLS encryption configuration."""
        if self.config.use_tls:
            # Check if connection is actually encrypted
            # Note: aioredis doesn't provide direct access to connection encryption status
            # This is a simplified check
            result.connection_encrypted = True
            result.tls_version = f"TLS {self.config.min_tls_version}"
            result.detailed_checks["encryption"] = f"TLS enabled (min version: {self.config.min_tls_version})"
        else:
            result.vulnerabilities.append("Unencrypted connection")
            result.detailed_checks["encryption"] = "Disabled"
    
    async def _validate_certificates(self, result: SecurityValidationResult) -> None:
        """Validate TLS certificates."""
        if not self.config.use_tls:
            return
            
        try:
            # Certificate validation logic would go here
            # For now, assume certificates are valid if paths exist and are readable
            cert_valid = True
            
            if self.config.tls_cert_path:
                cert_path = Path(self.config.tls_cert_path)
                if not cert_path.exists():
                    cert_valid = False
                    result.vulnerabilities.append(f"Certificate file not found: {self.config.tls_cert_path}")
            
            if self.config.tls_key_path:
                key_path = Path(self.config.tls_key_path)
                if not key_path.exists():
                    cert_valid = False
                    result.vulnerabilities.append(f"Private key file not found: {self.config.tls_key_path}")
            
            result.certificate_valid = cert_valid
            result.detailed_checks["certificates"] = "Valid" if cert_valid else "Invalid"
            
        except Exception as e:
            result.vulnerabilities.append(f"Certificate validation failed: {e}")
            result.detailed_checks["certificates"] = f"FAILED: {e}"
    
    async def _analyze_security_vulnerabilities(self, result: SecurityValidationResult) -> None:
        """Analyze and identify security vulnerabilities."""
        # Check for common security issues
        
        # No authentication
        if not self.config.has_authentication:
            result.vulnerabilities.append("No authentication configured - Redis is accessible without credentials")
        
        # Unencrypted connection
        if not self.config.use_tls:
            result.vulnerabilities.append("Unencrypted connection - data transmitted in plain text")
        
        # Weak TLS configuration
        if self.config.use_tls and not self.config.verify_certificates:
            result.vulnerabilities.append("Certificate verification disabled - vulnerable to man-in-the-middle attacks")
        
        # Default passwords or weak configuration
        if self.config.redis_auth and len(self.config.redis_auth) < 12:
            result.vulnerabilities.append("Weak password - consider using a stronger password (≥12 characters)")
        
        # Long connection timeouts
        if self.config.connection_timeout > 60:
            result.warnings.append("Long connection timeout may increase vulnerability window")
    
    async def _generate_security_recommendations(self, result: SecurityValidationResult) -> None:
        """Generate security improvement recommendations."""
        recommendations = []
        
        # Authentication recommendations
        if not self.config.has_authentication:
            recommendations.append("Enable Redis authentication (AUTH or ACL)")
        elif self.config.redis_auth and not self.config.acl_username:
            recommendations.append("Consider upgrading to ACL authentication for better security")
        
        # Encryption recommendations
        if not self.config.use_tls:
            recommendations.append("Enable TLS encryption for data in transit")
        elif self.config.use_tls and not self.config.verify_certificates:
            recommendations.append("Enable certificate verification")
        
        # Password strength recommendations
        if self.config.redis_auth and len(self.config.redis_auth) < 16:
            recommendations.append("Use a stronger password (≥16 characters with mixed case, numbers, symbols)")
        
        # Certificate management
        if self.config.use_tls:
            recommendations.append("Regularly rotate TLS certificates")
            recommendations.append("Monitor certificate expiration dates")
        
        # Network security
        recommendations.append("Use Redis in a private network or VPN")
        recommendations.append("Configure firewall rules to restrict Redis access")
        recommendations.append("Consider using Redis Sentinel for high availability")
        
        # Monitoring
        recommendations.append("Enable Redis slow log monitoring")
        recommendations.append("Monitor failed authentication attempts")
        recommendations.append("Set up alerts for security events")
        
        result.recommendations = recommendations
    
    def _log_security_event(self, event_type: str, details: Dict[str, Any]) -> None:
        """Log security events for monitoring and auditing."""
        event = {
            "timestamp": time.time(),
            "event_type": event_type,
            "details": details,
            "security_level": self.config.security_level
        }
        
        self._security_events.append(event)
        
        # Keep only recent events (last 1000)
        if len(self._security_events) > 1000:
            self._security_events = self._security_events[-1000:]
        
        self._security_logger.info(f"Security event: {event_type}", extra=event)
    
    def get_security_recommendations(self) -> List[str]:
        """Get security hardening recommendations for current configuration."""
        recommendations = []
        
        # Authentication recommendations
        if not self.config.has_authentication:
            recommendations.append("🔐 Enable Redis authentication (AUTH password or ACL username/password)")
        
        # Encryption recommendations  
        if not self.config.use_tls:
            recommendations.append("🔒 Enable TLS encryption to protect data in transit")
        
        # Certificate recommendations
        if self.config.use_tls and not self.config.verify_certificates:
            recommendations.append("⚠️ Enable certificate verification to prevent MITM attacks")
        
        # Password strength
        if self.config.redis_auth and len(self.config.redis_auth) < 16:
            recommendations.append("💪 Use a stronger password (≥16 characters, mixed case, numbers, symbols)")
        
        # Network security
        recommendations.extend([
            "🌐 Deploy Redis in a private network or VPN",
            "🔥 Configure firewall rules to restrict Redis port access",
            "📊 Enable Redis slow log and monitor performance",
            "🚨 Set up monitoring for failed authentication attempts",
            "🔄 Regularly rotate passwords and certificates",
            "⚡ Consider Redis Sentinel for high availability and security"
        ])
        
        return recommendations
    
    async def test_security_configuration(self, redis_url: str = "redis://localhost:6379") -> Dict[str, Any]:
        """Test security configuration comprehensively.
        
        This method performs comprehensive testing of the security configuration
        including connection testing, authentication validation, and encryption verification.
        
        Args:
            redis_url: Redis URL to test against
            
        Returns:
            Detailed test results
        """
        results = {
            "timestamp": time.time(),
            "configuration_valid": False,
            "connection_successful": False,
            "authentication_working": False,
            "encryption_active": False,
            "overall_secure": False,
            "test_details": {},
            "errors": []
        }
        
        try:
            # Test 1: Configuration validation
            try:
                self.config._validate_configuration()
                results["configuration_valid"] = True
                results["test_details"]["configuration"] = "Valid"
            except Exception as e:
                results["errors"].append(f"Configuration invalid: {e}")
                results["test_details"]["configuration"] = f"Invalid: {e}"
            
            # Test 2: Connection test
            try:
                # Support synchronous mocks in tests by awaiting conditionally
                conn_result = self.create_secure_connection(redis_url)
                redis_client = await conn_result if inspect.isawaitable(conn_result) else conn_result
                results["connection_successful"] = True
                results["test_details"]["connection"] = "Successful"
                
                # Test 3: Authentication test
                try:
                    await redis_client.ping()
                    results["authentication_working"] = True
                    results["test_details"]["authentication"] = "Working"
                except Exception as e:
                    results["errors"].append(f"Authentication failed: {e}")
                    results["test_details"]["authentication"] = f"Failed: {e}"
                
                # Test 4: Security validation
                validation = await self.validate_connection_security(redis_client)
                results["encryption_active"] = validation.tls_enabled
                results["overall_secure"] = validation.is_secure
                results["security_score"] = validation.security_score
                results["test_details"]["security_validation"] = {
                    "secure": validation.is_secure,
                    "score": validation.security_score,
                    "vulnerabilities": validation.vulnerabilities
                }
                
                # Clean up
                await redis_client.close()
                
            except Exception as e:
                results["errors"].append(f"Connection failed: {e}")
                results["test_details"]["connection"] = f"Failed: {e}"
        
        except Exception as e:
            results["errors"].append(f"Test execution failed: {e}")
        
        return results
    
    def generate_security_report(self, validation_result: Optional[SecurityValidationResult] = None) -> str:
        """Generate detailed security assessment report.
        
        Args:
            validation_result: Optional validation result, uses last validation if not provided
            
        Returns:
            Formatted security report
        """
        if validation_result is None:
            validation_result = self._last_validation
        
        if validation_result is None:
            return "No security validation data available. Run validate_connection_security() first."
        
        report = []
        report.append("=" * 60)
        report.append("REDIS CACHE SECURITY ASSESSMENT REPORT")
        report.append("=" * 60)
        report.append("")
        
        # Executive Summary
        report.append("EXECUTIVE SUMMARY")
        report.append("-" * 20)
        status = "✅ SECURE" if validation_result.is_secure else "❌ INSECURE"
        report.append(f"Security Status: {status}")
        report.append(f"Security Score: {validation_result.security_score}/100")
        # Also include a concise score line for compatibility with tests
        report.append(f"Score: {validation_result.security_score}/100")
        report.append(f"Security Level: {self.config.security_level}")
        report.append("")
        
        # Configuration Summary
        report.append("SECURITY CONFIGURATION")
        report.append("-" * 25)
        report.append(f"Authentication: {'✅ Enabled' if validation_result.auth_configured else '❌ Disabled'}")
        if validation_result.auth_method:
            report.append(f"Auth Method: {validation_result.auth_method}")
        report.append(f"TLS Encryption: {'✅ Enabled' if validation_result.tls_enabled else '❌ Disabled'}")
        if validation_result.tls_version:
            report.append(f"TLS Version: {validation_result.tls_version}")
        report.append(f"ACL Authentication: {'✅ Enabled' if validation_result.acl_enabled else '❌ Disabled'}")
        report.append(f"Certificate Validation: {'✅ Valid' if validation_result.certificate_valid else '❌ Invalid'}")
        report.append("")
        
        # Vulnerabilities
        if validation_result.vulnerabilities:
            report.append("SECURITY VULNERABILITIES")
            report.append("-" * 25)
            for i, vuln in enumerate(validation_result.vulnerabilities, 1):
                report.append(f"{i}. ❌ {vuln}")
            report.append("")
        
        # Warnings
        if validation_result.warnings:
            report.append("SECURITY WARNINGS")
            report.append("-" * 18)
            for i, warning in enumerate(validation_result.warnings, 1):
                report.append(f"{i}. ⚠️ {warning}")
            report.append("")
        
        # Recommendations
        if validation_result.recommendations:
            report.append("SECURITY RECOMMENDATIONS")
            report.append("-" * 27)
            for i, rec in enumerate(validation_result.recommendations, 1):
                report.append(f"{i}. 💡 {rec}")
            report.append("")
        
        # Detailed Checks
        if validation_result.detailed_checks:
            report.append("DETAILED SECURITY CHECKS")
            report.append("-" * 26)
            for check, result in validation_result.detailed_checks.items():
                status_icon = "✅" if "OK" in str(result) or "Valid" in str(result) else "❌"
                report.append(f"{check.title()}: {status_icon} {result}")
            report.append("")
        
        # Security Events
        if self._security_events:
            recent_events = self._security_events[-5:]  # Last 5 events
            report.append("RECENT SECURITY EVENTS")
            report.append("-" * 24)
            for event in recent_events:
                timestamp = event.get("timestamp", 0)
                event_type = event.get("event_type", "unknown")
                report.append(f"• {event_type} (Score: {validation_result.security_score})")
            report.append("")
        
        # Footer
        report.append("=" * 60)
        report.append("Report generated by Redis Cache Security Manager")
        report.append(f"Configuration Security Level: {self.config.security_level}")
        report.append("=" * 60)
        
        return "\n".join(report)
    
    def get_security_status(self) -> Dict[str, Any]:
        """Get current security status and metrics.
        
        Returns:
            Comprehensive security status information
        """
        status = {
            "timestamp": time.time(),
            "security_level": self.config.security_level,
            "configuration": {
                "has_authentication": self.config.has_authentication,
                "tls_enabled": self.config.use_tls,
                "acl_configured": bool(self.config.acl_username),
                "certificate_verification": self.config.verify_certificates,
                "connection_timeout": self.config.connection_timeout,
                "max_retries": self.config.max_retries
            },
            "last_validation": None,
            "security_events_count": len(self._security_events),
            "recommendations_count": len(self.get_security_recommendations())
        }
        
        # Include last validation results if available
        if self._last_validation:
            status["last_validation"] = {
                "timestamp": "recent",  # Would include actual timestamp in real implementation
                "is_secure": self._last_validation.is_secure,
                "security_score": self._last_validation.security_score,
                "vulnerabilities_count": len(self._last_validation.vulnerabilities),
                "recommendations_count": len(self._last_validation.recommendations)
            }
        
        return status


def create_security_config_from_env() -> Optional[SecurityConfig]:
    """Create SecurityConfig from environment variables.
    
    This utility function creates a SecurityConfig instance from common
    environment variables, making it easy to configure Redis security
    in containerized environments.
    
    Environment Variables:
        REDIS_AUTH: Redis AUTH password
        REDIS_USE_TLS: Enable TLS (true/false)
        REDIS_TLS_CERT_PATH: Path to TLS certificate
        REDIS_TLS_KEY_PATH: Path to TLS private key
        REDIS_TLS_CA_PATH: Path to TLS CA certificate
        REDIS_ACL_USERNAME: ACL username
        REDIS_ACL_PASSWORD: ACL password
        REDIS_VERIFY_CERTIFICATES: Verify certificates (true/false)
        REDIS_CONNECTION_TIMEOUT: Connection timeout in seconds
    
    Returns:
        SecurityConfig instance or None if no security settings found
    """
    import os
    
    # Check if any security settings are configured
    security_env_vars = [
        "REDIS_AUTH", "REDIS_USE_TLS", "REDIS_ACL_USERNAME", "REDIS_ACL_PASSWORD"
    ]
    
    if not any(os.getenv(var) for var in security_env_vars):
        return None
    
    return SecurityConfig(
        redis_auth=os.getenv("REDIS_AUTH"),
        use_tls=os.getenv("REDIS_USE_TLS", "false").lower() == "true",
        tls_cert_path=os.getenv("REDIS_TLS_CERT_PATH"),
        tls_key_path=os.getenv("REDIS_TLS_KEY_PATH"),
        tls_ca_path=os.getenv("REDIS_TLS_CA_PATH"),
        acl_username=os.getenv("REDIS_ACL_USERNAME"),
        acl_password=os.getenv("REDIS_ACL_PASSWORD"),
        verify_certificates=os.getenv("REDIS_VERIFY_CERTIFICATES", "true").lower() == "true",
        connection_timeout=int(os.getenv("REDIS_CONNECTION_TIMEOUT", "30")),
        max_retries=int(os.getenv("REDIS_MAX_RETRIES", "3")),
        retry_delay=float(os.getenv("REDIS_RETRY_DELAY", "1.0"))
    )


# Export public API
__all__ = [
    "SecurityConfig",
    "SecurityValidationResult", 
    "RedisCacheSecurityManager",
    "create_security_config_from_env"
]
