# Phase 3 Implementation Plan: Enhanced Developer Experience

## Overview
**Scope:** Improve developer experience with factory patterns, better configuration, comprehensive documentation, and migration guides.

**Dependencies:** Requires completed Phases 1 & 2 (GenericRedisCache with security, refactored AIResponseCache with inheritance, migration tools, and performance benchmarking)

**Duration:** 3-4 weeks

## Current State After Phase 2
After Phase 2 completion, we will have:
- ✅ `GenericRedisCache` with Redis operations, L1 memory cache, compression, security
- ✅ `AIResponseCache` inheriting from `GenericRedisCache` with AI-specific features validated
- ✅ `CacheKeyGenerator` as standalone component with performance monitoring
- ✅ `RedisCacheSecurityManager` and migration tools from Phase 1
- ✅ `CacheParameterMapper` for clean parameter separation
- ✅ Comprehensive testing and performance validation completed
- ✅ Clean architectural separation achieved and verified

## Phase 3 Deliverables

### 1. CacheFactory with Application Type Detection
**New file**: `backend/app/infrastructure/cache/factory.py`

**Enhanced Test Requirement**: Add comprehensive testing for application type detection under various conditions to prevent brittleness.

**Factory Implementation with Smart Detection:
```python
import os
import importlib.util
from typing import Optional, Dict, Any, Union
from functools import lru_cache

class CacheFactory:
    """Factory for creating appropriate cache instances with smart defaults and validation."""
    
    @staticmethod
    @lru_cache(maxsize=1)
    def _detect_app_type() -> str:
        """Detect application type based on dependencies and environment."""
        detection_signals = {
            'ai': [
                # Check for AI-related imports
                lambda: CacheFactory._check_module_exists('pydantic_ai'),
                lambda: CacheFactory._check_module_exists('openai'),
                lambda: CacheFactory._check_module_exists('anthropic'),
                lambda: CacheFactory._check_module_exists('transformers'),
                # Check for AI-related environment variables
                lambda: any(var in os.environ for var in ['GEMINI_API_KEY', 'OPENAI_API_KEY', 'ANTHROPIC_API_KEY']),
                # Check for AI-related service files
                lambda: CacheFactory._check_file_exists('app/services/text_processor.py'),
                lambda: CacheFactory._check_file_exists('app/services/ai_service.py'),
            ],
            'web': [
                # Default signals for web applications
                lambda: CacheFactory._check_module_exists('fastapi'),
                lambda: CacheFactory._check_module_exists('django'),
                lambda: CacheFactory._check_module_exists('flask'),
                # Check for typical web service patterns
                lambda: CacheFactory._check_file_exists('app/services/user_service.py'),
                lambda: CacheFactory._check_file_exists('app/services/auth_service.py'),
            ]
        }
        
        scores = {'ai': 0, 'web': 0}
        
        for app_type, signals in detection_signals.items():
            for signal in signals:
                try:
                    if signal():
                        scores[app_type] += 1
                except Exception:
                    continue  # Ignore detection errors
        
        # Determine app type based on scores
        if scores['ai'] >= 2:  # Require at least 2 AI signals
            return 'ai'
        elif scores['web'] >= 1:  # Web is more permissive
            return 'web'
        else:
            return 'web'  # Default to web for unknown scenarios
    
    @staticmethod
    def _check_module_exists(module_name: str) -> bool:
        """Check if a module exists in the current environment."""
        return importlib.util.find_spec(module_name) is not None
    
    @staticmethod
    def _check_file_exists(file_path: str) -> bool:
        """Check if a file exists relative to the current working directory."""
        return os.path.exists(file_path)
    
    @staticmethod
    def _validate_factory_inputs(redis_url: Optional[str] = None, **kwargs) -> None:
        """Validate factory method inputs."""
        if redis_url and not isinstance(redis_url, str):
            raise ValueError("redis_url must be a string")
        
        if redis_url and not redis_url.startswith(('redis://', 'rediss://')):
            raise ValueError("redis_url must start with 'redis://' or 'rediss://'")
        
        # Validate common parameters
        if 'memory_cache_size' in kwargs:
            size = kwargs['memory_cache_size']
            if not isinstance(size, int) or size <= 0:
                raise ValueError("memory_cache_size must be a positive integer")
        
        if 'default_ttl' in kwargs:
            ttl = kwargs['default_ttl']
            if not isinstance(ttl, int) or ttl <= 0:
                raise ValueError("default_ttl must be a positive integer")
    
    @staticmethod
    def for_web_app(redis_url: Optional[str] = None, **kwargs) -> CacheInterface:
        """Create optimized cache for web applications with validation."""
        CacheFactory._validate_factory_inputs(redis_url, **kwargs)
        
        # Web app optimized defaults
        web_defaults = {
            'default_ttl': kwargs.get('default_ttl', 1800),  # 30 minutes
            'memory_cache_size': kwargs.get('memory_cache_size', 200),  # Larger memory cache for web
            'compression_threshold': kwargs.get('compression_threshold', 2000),  # Less aggressive compression
            'compression_level': kwargs.get('compression_level', 4),  # Faster compression
        }
        
        if redis_url:
            try:
                cache = GenericRedisCache(
                    redis_url=redis_url,
                    **{**web_defaults, **kwargs}
                )
                return cache
            except Exception as e:
                # Log error but continue with fallback
                import logging
                logging.warning(f"Redis connection failed for web app, using memory cache: {e}")
        
        # Fallback to memory cache with web-optimized settings
        return InMemoryCache(
            default_ttl=web_defaults['default_ttl'],
            max_size=web_defaults['memory_cache_size']
        )
    
    @staticmethod  
    def for_ai_app(redis_url: Optional[str] = None, **ai_options) -> CacheInterface:
        """Create optimized cache for AI applications with validation."""
        CacheFactory._validate_factory_inputs(redis_url, **ai_options)
        
        # AI app optimized defaults
        ai_defaults = {
            'default_ttl': ai_options.get('default_ttl', 3600),  # 1 hour
            'memory_cache_size': ai_options.get('memory_cache_size', 100),  # Moderate memory cache
            'compression_threshold': ai_options.get('compression_threshold', 1000),  # Aggressive compression
            'compression_level': ai_options.get('compression_level', 6),  # Balanced compression
            'text_hash_threshold': ai_options.get('text_hash_threshold', 1000),
            'operation_ttls': ai_options.get('operation_ttls', {
                "summarize": 7200, "sentiment": 86400, "key_points": 7200,
                "questions": 3600, "qa": 1800
            })
        }
        
        if redis_url:
            try:
                cache = AIResponseCache(
                    redis_url=redis_url,
                    **{**ai_defaults, **ai_options}
                )
                return cache
            except Exception as e:
                # Log error but continue with fallback
                import logging
                logging.warning(f"Redis connection failed for AI app, using memory cache: {e}")
        
        # Fallback to memory cache with AI-optimized settings (smaller, faster TTL)
        return InMemoryCache(
            default_ttl=300,  # 5 minutes for AI fallback
            max_size=50       # Smaller cache for AI fallback
        )
    
    @staticmethod
    async def create_with_fallback(primary_config: 'CacheConfig', 
                                 fallback_type: str = "memory") -> CacheInterface:
        """Create cache with automatic fallback on connection failure and lifecycle management."""
        from .config import CacheConfig  # Avoid circular import
        
        if not isinstance(primary_config, CacheConfig):
            raise ValueError("primary_config must be a CacheConfig instance")
        
        # Validate and create primary cache
        try:
            validation_result = primary_config.validate()
            if not validation_result.is_valid:
                raise ValueError(f"Invalid primary config: {validation_result.errors}")
            
            # Determine cache type based on configuration
            if primary_config.ai_config:
                primary_cache = CacheFactory.for_ai_app(
                    redis_url=primary_config.redis_url,
                    **primary_config.to_dict()
                )
            else:
                primary_cache = CacheFactory.for_web_app(
                    redis_url=primary_config.redis_url,
                    **primary_config.to_dict()
                )
            
            # Test connection for Redis-based caches
            if hasattr(primary_cache, 'connect'):
                connection_success = await primary_cache.connect()
                if connection_success:
                    return primary_cache
                else:
                    raise ConnectionError("Primary cache connection failed")
            
            return primary_cache
            
        except Exception as e:
            import logging
            logging.warning(f"Primary cache creation failed, using {fallback_type} fallback: {e}")
            
            # Create fallback cache
            if fallback_type == "memory":
                return InMemoryCache(
                    default_ttl=primary_config.default_ttl // 4,  # Shorter TTL for fallback
                    max_size=50
                )
            else:
                raise ValueError(f"Unsupported fallback type: {fallback_type}")
    
    @staticmethod
    def from_environment(app_type: str = "auto") -> CacheInterface:
        """Create cache based on environment variables with smart detection."""
        if app_type == "auto":
            app_type = CacheFactory._detect_app_type()
        
        if app_type not in ["ai", "web"]:
            raise ValueError(f"Unsupported app_type: {app_type}. Must be 'auto', 'ai', or 'web'")
        
        # Check for testing environment
        if os.getenv("TESTING") or os.getenv("CI") or os.getenv("PYTEST_CURRENT_TEST"):
            return CacheFactory.for_testing()
        
        redis_url = os.getenv("REDIS_URL")
        
        # Environment-specific configuration
        env_config = {
            'default_ttl': int(os.getenv('CACHE_DEFAULT_TTL', '3600')),
            'memory_cache_size': int(os.getenv('CACHE_MEMORY_SIZE', '100')),
            'compression_threshold': int(os.getenv('CACHE_COMPRESSION_THRESHOLD', '1000')),
            'compression_level': int(os.getenv('CACHE_COMPRESSION_LEVEL', '6')),
            'redis_auth': os.getenv('REDIS_AUTH'),
            'use_tls': os.getenv('REDIS_USE_TLS', '').lower() in ('true', '1', 'yes')
        }
        
        if app_type == "ai":
            # Add AI-specific environment variables
            ai_config = {
                **env_config,
                'text_hash_threshold': int(os.getenv('CACHE_TEXT_HASH_THRESHOLD', '1000')),
            }
            
            # Parse operation TTLs from environment if provided
            operation_ttls_env = os.getenv('CACHE_OPERATION_TTLS')
            if operation_ttls_env:
                import json
                try:
                    ai_config['operation_ttls'] = json.loads(operation_ttls_env)
                except json.JSONDecodeError:
                    pass  # Use defaults
            
            return CacheFactory.for_ai_app(redis_url=redis_url, **ai_config)
        else:
            return CacheFactory.for_web_app(redis_url=redis_url, **env_config)
    
    @staticmethod
    def for_testing(cache_type: str = "memory") -> CacheInterface:
        """Create cache optimized for testing scenarios with fast cleanup."""
        if cache_type == "memory":
            return InMemoryCache(
                default_ttl=60,   # 1 minute for fast test cycles
                max_size=25       # Small cache for testing
            )
        elif cache_type == "redis":
            # Use test Redis with fast settings
            return GenericRedisCache(
                redis_url=os.getenv('TEST_REDIS_URL', 'redis://localhost:6379/15'),  # Use DB 15 for testing
                default_ttl=60,
                memory_cache_size=10,
                compression_threshold=5000  # Minimal compression for testing
            )
        else:
            raise ValueError(f"Unsupported testing cache_type: {cache_type}")
    
    @staticmethod
    def create_cache_from_config(config: 'CacheConfig') -> CacheInterface:
        """Create cache instance from configuration object."""
        from .config import CacheConfig  # Avoid circular import
        
        if not isinstance(config, CacheConfig):
            raise ValueError("config must be a CacheConfig instance")
        
        validation_result = config.validate()
        if not validation_result.is_valid:
            raise ValueError(f"Invalid configuration: {validation_result.errors}")
        
        if config.ai_config:
            return CacheFactory.for_ai_app(**config.to_dict())
        else:
            return CacheFactory.for_web_app(**config.to_dict())
```

### 2. Enhanced Configuration Management with Builder Pattern
**New file**: `backend/app/infrastructure/cache/config.py`

**Unified Configuration System:**
```python
from dataclasses import dataclass, field, asdict
from typing import Dict, Any, Optional, List
from pathlib import Path
import json
import os

@dataclass
class ValidationResult:
    """Result of configuration validation."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)

@dataclass
class CacheConfig:
    """Unified cache configuration for all cache types with environment integration."""
    # Generic Redis configuration
    redis_url: str = "redis://redis:6379"
    default_ttl: int = 3600
    compression_threshold: int = 1000
    compression_level: int = 6
    memory_cache_size: int = 100
    
    # Security configuration
    redis_auth: Optional[str] = None
    use_tls: bool = False
    tls_cert_path: Optional[str] = None
    tls_key_path: Optional[str] = None
    
    # Environment-specific settings
    environment: str = "development"  # development, testing, production
    
    # AI-specific options (optional)
    ai_config: Optional['AICacheConfig'] = None
    
    def __post_init__(self):
        """Post-initialization validation and environment variable loading."""
        # Load from environment variables if not explicitly set
        if hasattr(self, '_from_env') and self._from_env:
            self._load_from_environment()
    
    def _load_from_environment(self):
        """Load configuration from environment variables."""
        env_mappings = {
            'redis_url': 'REDIS_URL',
            'default_ttl': ('CACHE_DEFAULT_TTL', int),
            'compression_threshold': ('CACHE_COMPRESSION_THRESHOLD', int),
            'compression_level': ('CACHE_COMPRESSION_LEVEL', int),
            'memory_cache_size': ('CACHE_MEMORY_SIZE', int),
            'redis_auth': 'REDIS_AUTH',
            'use_tls': ('REDIS_USE_TLS', lambda x: x.lower() in ('true', '1', 'yes')),
            'tls_cert_path': 'REDIS_TLS_CERT_PATH',
            'tls_key_path': 'REDIS_TLS_KEY_PATH',
            'environment': 'CACHE_ENVIRONMENT'
        }
        
        for field_name, env_config in env_mappings.items():
            if isinstance(env_config, tuple):
                env_var, converter = env_config
                env_value = os.getenv(env_var)
                if env_value:
                    try:
                        setattr(self, field_name, converter(env_value))
                    except (ValueError, TypeError):
                        pass  # Keep default value if conversion fails
            else:
                env_value = os.getenv(env_config)
                if env_value:
                    setattr(self, field_name, env_value)

@dataclass 
class AICacheConfig:
    """AI-specific cache configuration with intelligent defaults."""
    text_hash_threshold: int = 1000
    hash_algorithm: str = "sha256"  # Store as string for serialization
    
    text_size_tiers: Dict[str, int] = field(default_factory=lambda: {
        'small': 500,
        'medium': 5000,
        'large': 50000
    })
    
    operation_ttls: Dict[str, int] = field(default_factory=lambda: {
        "summarize": 7200,    # 2 hours
        "sentiment": 86400,   # 24 hours  
        "key_points": 7200,   # 2 hours
        "questions": 3600,    # 1 hour
        "qa": 1800           # 30 minutes
    })
    
    # Advanced AI-specific settings
    enable_smart_promotion: bool = True  # Enable smart memory cache promotion
    max_text_length: int = 100000       # Maximum text length to process
    
    def validate(self) -> ValidationResult:
        """Validate AI-specific configuration."""
        errors = []
        warnings = []
        
        if self.text_hash_threshold <= 0:
            errors.append("text_hash_threshold must be positive")
            
        if not all(isinstance(v, int) and v > 0 for v in self.text_size_tiers.values()):
            errors.append("text_size_tiers values must be positive integers")
            
        if not all(isinstance(v, int) and v > 0 for v in self.operation_ttls.values()):
            errors.append("operation_ttls values must be positive integers")
        
        # Check for reasonable text size tier progression
        tiers = list(self.text_size_tiers.values())
        if not all(tiers[i] < tiers[i+1] for i in range(len(tiers)-1)):
            warnings.append("text_size_tiers should be in ascending order for optimal performance")
        
        # Check for reasonable operation TTLs
        if any(ttl > 86400 * 7 for ttl in self.operation_ttls.values()):  # 1 week
            warnings.append("Some operation TTLs are very long (>1 week) - consider if this is intentional")
        
        return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)

class CacheConfigBuilder:
    """Builder pattern for cache configuration with fluent interface."""
    
    def __init__(self):
        self.config = CacheConfig()
    
    def for_environment(self, env: str) -> 'CacheConfigBuilder':
        """Configure for specific environment with optimized defaults."""
        self.config.environment = env
        
        if env == "development":
            self.config.default_ttl = 1800      # 30 minutes
            self.config.memory_cache_size = 50   # Smaller for development
            self.config.compression_level = 4    # Faster compression
        elif env == "testing":
            self.config.default_ttl = 60        # 1 minute
            self.config.memory_cache_size = 10   # Very small for tests
            self.config.compression_threshold = 5000  # Minimal compression
        elif env == "production":
            self.config.default_ttl = 7200      # 2 hours
            self.config.memory_cache_size = 200  # Larger for production
            self.config.compression_level = 8    # Higher compression
        else:
            raise ValueError(f"Unknown environment: {env}")
        
        return self
    
    def with_redis(self, redis_url: str, auth: Optional[str] = None, 
                   use_tls: bool = False) -> 'CacheConfigBuilder':
        """Configure Redis connection with security options."""
        self.config.redis_url = redis_url
        self.config.redis_auth = auth
        self.config.use_tls = use_tls
        return self
    
    def with_security(self, tls_cert_path: Optional[str] = None,
                     tls_key_path: Optional[str] = None) -> 'CacheConfigBuilder':
        """Configure TLS security settings."""
        self.config.tls_cert_path = tls_cert_path
        self.config.tls_key_path = tls_key_path
        if tls_cert_path or tls_key_path:
            self.config.use_tls = True
        return self
    
    def with_compression(self, threshold: int = 1000, 
                        level: int = 6) -> 'CacheConfigBuilder':
        """Configure compression settings."""
        self.config.compression_threshold = threshold
        self.config.compression_level = level
        return self
    
    def with_memory_cache(self, size: int = 100) -> 'CacheConfigBuilder':
        """Configure memory cache settings."""
        self.config.memory_cache_size = size
        return self
    
    def with_ai_features(self, **ai_options) -> 'CacheConfigBuilder':
        """Enable and configure AI-specific features."""
        if self.config.ai_config is None:
            self.config.ai_config = AICacheConfig()
        
        # Update AI config with provided options
        for key, value in ai_options.items():
            if hasattr(self.config.ai_config, key):
                setattr(self.config.ai_config, key, value)
            else:
                raise ValueError(f"Unknown AI config option: {key}")
        
        return self
    
    def from_file(self, config_path: str) -> 'CacheConfigBuilder':
        """Load configuration from JSON file."""
        config_file = Path(config_path)
        if not config_file.exists():
            raise FileNotFoundError(f"Configuration file not found: {config_path}")
        
        with open(config_file, 'r') as f:
            config_data = json.load(f)
        
        # Apply configuration data
        for key, value in config_data.items():
            if key == "ai_config" and value:
                self.config.ai_config = AICacheConfig(**value)
            elif hasattr(self.config, key):
                setattr(self.config, key, value)
        
        return self
    
    def from_environment(self) -> 'CacheConfigBuilder':
        """Load configuration from environment variables."""
        self.config._from_env = True
        self.config._load_from_environment()
        
        # Load AI configuration from environment if indicated
        if os.getenv('ENABLE_AI_CACHE', '').lower() in ('true', '1', 'yes'):
            ai_config = AICacheConfig()
            
            # Load AI-specific environment variables
            if os.getenv('CACHE_TEXT_HASH_THRESHOLD'):
                ai_config.text_hash_threshold = int(os.getenv('CACHE_TEXT_HASH_THRESHOLD'))
            
            if os.getenv('CACHE_OPERATION_TTLS'):
                try:
                    ai_config.operation_ttls = json.loads(os.getenv('CACHE_OPERATION_TTLS'))
                except json.JSONDecodeError:
                    pass  # Use defaults
            
            self.config.ai_config = ai_config
        
        return self
    
    def build(self) -> CacheConfig:
        """Build and validate the final configuration."""
        validation_result = self.validate()
        if not validation_result.is_valid:
            raise ValueError(f"Invalid configuration: {validation_result.errors}")
        
        return self.config
    
    def validate(self) -> ValidationResult:
        """Validate the current configuration."""
        errors = []
        warnings = []
        
        # Validate Redis URL
        if not self.config.redis_url.startswith(('redis://', 'rediss://')):
            errors.append("redis_url must start with 'redis://' or 'rediss://'")
        
        # Validate TTL values
        if self.config.default_ttl <= 0:
            errors.append("default_ttl must be positive")
        
        # Validate memory cache size
        if self.config.memory_cache_size <= 0:
            errors.append("memory_cache_size must be positive")
        
        # Validate compression settings
        if not 1 <= self.config.compression_level <= 9:
            errors.append("compression_level must be between 1 and 9")
        
        if self.config.compression_threshold < 0:
            errors.append("compression_threshold must be non-negative")
        
        # Validate TLS configuration
        if self.config.use_tls:
            if self.config.tls_cert_path and not Path(self.config.tls_cert_path).exists():
                warnings.append(f"TLS certificate file not found: {self.config.tls_cert_path}")
            
            if self.config.tls_key_path and not Path(self.config.tls_key_path).exists():
                warnings.append(f"TLS key file not found: {self.config.tls_key_path}")
        
        # Validate AI configuration if present
        if self.config.ai_config:
            ai_validation = self.config.ai_config.validate()
            errors.extend(ai_validation.errors)
            warnings.extend(ai_validation.warnings)
        
        return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary for serialization."""
        config_dict = asdict(self.config)
        
        # Handle AI config serialization
        if config_dict.get('ai_config'):
            # Convert to dictionary format
            ai_config_dict = config_dict['ai_config']
            config_dict.update(ai_config_dict)
        
        return config_dict
    
    def save_to_file(self, config_path: str) -> None:
        """Save configuration to JSON file."""
        config_dict = self.to_dict()
        
        config_file = Path(config_path)
        config_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(config_file, 'w') as f:
            json.dump(config_dict, f, indent=2)

# Pre-configured environment presets
class EnvironmentPresets:
    """Pre-configured settings for different environments with validation."""
    
    @staticmethod
    def development() -> CacheConfig:
        """Development environment configuration."""
        return (CacheConfigBuilder()
               .for_environment("development")
               .with_compression(threshold=2000, level=4)
               .build())
    
    @staticmethod
    def testing() -> CacheConfig:
        """Testing environment configuration."""
        return (CacheConfigBuilder()
               .for_environment("testing")
               .with_redis("redis://localhost:6379/15")  # Use test database
               .build())
    
    @staticmethod
    def production() -> CacheConfig:
        """Production environment configuration."""
        return (CacheConfigBuilder()
               .for_environment("production")
               .with_compression(threshold=1000, level=8)
               .with_memory_cache(200)
               .build())
    
    @staticmethod
    def ai_development() -> CacheConfig:
        """AI development environment configuration."""
        return (CacheConfigBuilder()
               .for_environment("development")
               .with_ai_features(
                   text_hash_threshold=500,
                   operation_ttls={
                       "summarize": 3600, "sentiment": 7200,
                       "questions": 1800, "qa": 900
                   }
               )
               .build())
    
    @staticmethod
    def ai_production() -> CacheConfig:
        """AI production environment configuration."""
        return (CacheConfigBuilder()
               .for_environment("production")
               .with_ai_features(
                   text_hash_threshold=1000,
                   max_text_length=200000,
                   enable_smart_promotion=True
               )
               .build())
```

### 3. FastAPI Dependency Integration with Lifecycle Management
**New file**: `backend/app/infrastructure/cache/dependencies.py`

**Enhanced Dependency Providers:**
```python
from fastapi import Depends, HTTPException
from functools import lru_cache
import asyncio
import logging
from typing import Optional, Dict, Any
import weakref

from app.core.config import Settings
from .factory import CacheFactory
from .config import CacheConfig, CacheConfigBuilder, EnvironmentPresets
from .base import CacheInterface
from .redis_generic import GenericRedisCache
from .redis_ai import AIResponseCache
from .memory import InMemoryCache

logger = logging.getLogger(__name__)

# Cache instance registry for lifecycle management
_cache_registry: Dict[str, weakref.ReferenceType] = {}
_cache_lock = asyncio.Lock()

class CacheDependencyManager:
    """Manages cache dependencies with proper lifecycle and error handling."""
    
    @staticmethod
    async def _ensure_cache_connected(cache: CacheInterface, cache_name: str) -> CacheInterface:
        """Ensure cache is connected with proper error handling."""
        if hasattr(cache, 'connect'):
            try:
                connection_result = await cache.connect()
                if connection_result:
                    logger.info(f"Successfully connected {cache_name}")
                    return cache
                else:
                    logger.warning(f"Failed to connect {cache_name}, connection returned False")
            except Exception as e:
                logger.error(f"Exception connecting {cache_name}: {e}")
                # Don't raise exception - let cache operate in degraded mode
        
        return cache
    
    @staticmethod
    async def _get_or_create_cache(cache_key: str, cache_factory_func) -> CacheInterface:
        """Get existing cache or create new one with registry management."""
        async with _cache_lock:
            # Check if we have an existing cache
            if cache_key in _cache_registry:
                existing_cache = _cache_registry[cache_key]()
                if existing_cache is not None:
                    return existing_cache
            
            # Create new cache
            cache = await cache_factory_func()
            
            # Register with weak reference for cleanup
            _cache_registry[cache_key] = weakref.ref(cache)
            
            return cache

# Settings-based dependency (cached)
@lru_cache()
def get_settings() -> Settings:
    """Get cached settings instance."""
    from app.core.config import Settings
    return Settings()

# Configuration-based dependencies
async def get_cache_config(settings: Settings = Depends(get_settings)) -> CacheConfig:
    """Get cache configuration based on settings and environment."""
    try:
        # Try to build configuration from settings
        builder = CacheConfigBuilder()
        
        if hasattr(settings, 'cache_environment'):
            builder.for_environment(settings.cache_environment)
        else:
            # Detect environment from other settings
            if getattr(settings, 'debug', False):
                builder.for_environment('development')
            elif getattr(settings, 'testing', False):
                builder.for_environment('testing')
            else:
                builder.for_environment('production')
        
        # Configure Redis if available
        if hasattr(settings, 'redis_url') and settings.redis_url:
            builder.with_redis(
                settings.redis_url,
                auth=getattr(settings, 'redis_auth', None),
                use_tls=getattr(settings, 'redis_use_tls', False)
            )
        
        # Configure AI features if enabled
        if getattr(settings, 'enable_ai_cache', False):
            ai_options = {}
            if hasattr(settings, 'cache_text_hash_threshold'):
                ai_options['text_hash_threshold'] = settings.cache_text_hash_threshold
            
            builder.with_ai_features(**ai_options)
        
        return builder.build()
        
    except Exception as e:
        logger.warning(f"Failed to build config from settings, using environment preset: {e}")
        # Fallback to environment-based configuration
        return EnvironmentPresets.development()

# Main cache dependency (auto-detection)
async def get_cache_service(config: CacheConfig = Depends(get_cache_config)) -> CacheInterface:
    """Main cache dependency with auto-detection and lifecycle management."""
    
    async def create_cache():
        try:
            cache = CacheFactory.create_cache_from_config(config)
            return await CacheDependencyManager._ensure_cache_connected(cache, "auto-detected cache")
        except Exception as e:
            logger.error(f"Failed to create cache from config, using fallback: {e}")
            # Create safe fallback
            fallback_cache = InMemoryCache(default_ttl=1800, max_size=100)
            logger.info("Using InMemoryCache as fallback")
            return fallback_cache
    
    return await CacheDependencyManager._get_or_create_cache("main_cache", create_cache)

# Environment-based cache dependency
async def get_cache_service_from_environment(app_type: str = "auto") -> CacheInterface:
    """Cache dependency using environment variable detection."""
    
    async def create_cache():
        try:
            cache = CacheFactory.from_environment(app_type)
            return await CacheDependencyManager._ensure_cache_connected(cache, f"{app_type} cache from environment")
        except Exception as e:
            logger.error(f"Failed to create cache from environment, using fallback: {e}")
            return InMemoryCache(default_ttl=1800, max_size=50)
    
    cache_key = f"env_cache_{app_type}"
    return await CacheDependencyManager._get_or_create_cache(cache_key, create_cache)

# Type-specific cache dependencies
async def get_web_cache_service(settings: Settings = Depends(get_settings)) -> GenericRedisCache:
    """Web application cache dependency."""
    
    async def create_cache():
        redis_url = getattr(settings, 'redis_url', None)
        web_options = {
            'default_ttl': getattr(settings, 'cache_default_ttl', 1800),
            'memory_cache_size': getattr(settings, 'cache_memory_size', 200),
            'compression_threshold': getattr(settings, 'cache_compression_threshold', 2000),
            'redis_auth': getattr(settings, 'redis_auth', None),
            'use_tls': getattr(settings, 'redis_use_tls', False)
        }
        
        cache = CacheFactory.for_web_app(redis_url=redis_url, **web_options)
        return await CacheDependencyManager._ensure_cache_connected(cache, "web cache")
    
    return await CacheDependencyManager._get_or_create_cache("web_cache", create_cache)

async def get_ai_cache_service(settings: Settings = Depends(get_settings)) -> AIResponseCache:
    """AI application cache dependency."""
    
    async def create_cache():
        redis_url = getattr(settings, 'redis_url', None)
        ai_options = {
            'default_ttl': getattr(settings, 'cache_default_ttl', 3600),
            'memory_cache_size': getattr(settings, 'cache_memory_size', 100),
            'compression_threshold': getattr(settings, 'cache_compression_threshold', 1000),
            'text_hash_threshold': getattr(settings, 'cache_text_hash_threshold', 1000),
            'redis_auth': getattr(settings, 'redis_auth', None),
            'use_tls': getattr(settings, 'redis_use_tls', False)
        }
        
        # Add operation TTLs if configured
        if hasattr(settings, 'cache_operation_ttls'):
            ai_options['operation_ttls'] = settings.cache_operation_ttls
        
        cache = CacheFactory.for_ai_app(redis_url=redis_url, **ai_options)
        return await CacheDependencyManager._ensure_cache_connected(cache, "AI cache")
    
    return await CacheDependencyManager._get_or_create_cache("ai_cache", create_cache)

# Testing dependencies
def get_test_cache() -> CacheInterface:
    """Cache dependency for testing with no persistence."""
    return CacheFactory.for_testing("memory")

def get_test_redis_cache() -> GenericRedisCache:
    """Redis cache dependency for integration testing."""
    return CacheFactory.for_testing("redis")

# Fallback cache dependency
async def get_fallback_cache_service() -> InMemoryCache:
    """Fallback cache that always works (memory-only)."""
    return InMemoryCache(default_ttl=1800, max_size=100)

# Configuration validation dependency
async def validate_cache_configuration(config: CacheConfig = Depends(get_cache_config)) -> CacheConfig:
    """Dependency that validates cache configuration and raises HTTP errors for invalid config."""
    validation_result = config.validate() if hasattr(config, 'validate') else None
    
    if validation_result and not validation_result.is_valid:
        logger.error(f"Invalid cache configuration: {validation_result.errors}")
        raise HTTPException(
            status_code=500,
            detail=f"Cache configuration error: {', '.join(validation_result.errors)}"
        )
    
    if validation_result and validation_result.warnings:
        for warning in validation_result.warnings:
            logger.warning(f"Cache configuration warning: {warning}")
    
    return config

# Conditional cache dependencies based on features
async def get_cache_service_conditional(
    enable_ai: bool = False,
    fallback_only: bool = False,
    settings: Settings = Depends(get_settings)
) -> CacheInterface:
    """Conditional cache service based on feature flags."""
    
    if fallback_only:
        return await get_fallback_cache_service()
    
    if enable_ai:
        return await get_ai_cache_service(settings)
    else:
        return await get_web_cache_service(settings)

# Cleanup function for application shutdown
async def cleanup_cache_registry():
    """Cleanup function to be called during application shutdown."""
    async with _cache_lock:
        active_caches = []
        
        for cache_key, cache_ref in list(_cache_registry.items()):
            cache = cache_ref()
            if cache is not None:
                active_caches.append((cache_key, cache))
            else:
                # Remove dead references
                del _cache_registry[cache_key]
        
        # Disconnect active caches
        for cache_key, cache in active_caches:
            try:
                if hasattr(cache, 'disconnect'):
                    await cache.disconnect()
                logger.info(f"Disconnected cache: {cache_key}")
            except Exception as e:
                logger.warning(f"Error disconnecting cache {cache_key}: {e}")
        
        _cache_registry.clear()
        logger.info("Cache registry cleaned up")

# Health check dependency
async def get_cache_health_status(cache: CacheInterface = Depends(get_cache_service)) -> Dict[str, Any]:
    """Get cache health status for monitoring."""
    health_status = {
        "cache_type": type(cache).__name__,
        "status": "unknown"
    }
    
    try:
        # Test basic cache operation
        test_key = "health_check_test"
        test_value = {"timestamp": "health_check"}
        
        await cache.set(test_key, test_value, ttl=60)
        retrieved = await cache.get(test_key)
        
        if retrieved and retrieved.get("timestamp") == "health_check":
            health_status["status"] = "healthy"
            
            # Clean up test data
            await cache.delete(test_key)
        else:
            health_status["status"] = "degraded"
            health_status["error"] = "Test data retrieval failed"
            
    except Exception as e:
        health_status["status"] = "unhealthy"
        health_status["error"] = str(e)
    
    # Add cache statistics if available
    if hasattr(cache, 'get_stats'):
        try:
            health_status["stats"] = cache.get_stats()
        except Exception:
            pass  # Stats not critical for health check
    
    return health_status
```

### 4. Performance Benchmarking Suite with Comparison Tools
**Update**: `backend/app/infrastructure/cache/benchmarks.py`

**Enhanced Benchmarking with Factory Integration:**
```python
import asyncio
import time
import statistics
import json
from typing import Dict, Any, List, Optional, Tuple
from dataclasses import dataclass, asdict
from datetime import datetime
import logging

from .base import CacheInterface
from .factory import CacheFactory
from .config import CacheConfig, EnvironmentPresets
from .redis_generic import GenericRedisCache
from .redis_ai import AIResponseCache
from .memory import InMemoryCache

logger = logging.getLogger(__name__)

@dataclass
class BenchmarkResult:
    """Comprehensive benchmark result with statistical analysis."""
    operation_type: str
    cache_type: str
    total_operations: int
    duration_seconds: float
    operations_per_second: float
    avg_duration_ms: float
    median_duration_ms: float
    p95_duration_ms: float
    p99_duration_ms: float
    min_duration_ms: float
    max_duration_ms: float
    memory_usage_mb: float
    success_rate: float
    error_count: int
    timestamp: str
    test_data_size: str
    additional_metrics: Dict[str, Any]

@dataclass
class ComparisonResult:
    """Result of comparing different cache implementations."""
    baseline_cache: str
    comparison_cache: str
    operation_comparisons: Dict[str, Dict[str, float]]  # operation -> metric -> percentage_change
    overall_performance_change: float
    recommendation: str
    significant_differences: List[str]

class CachePerformanceBenchmark:
    """Comprehensive performance benchmarking for cache implementations with factory integration."""
    
    def __init__(self, warmup_operations: int = 10, test_operations: int = 100):
        self.warmup_operations = warmup_operations
        self.test_operations = test_operations
        self.test_data_sets = self._generate_test_data_sets()
    
    def _generate_test_data_sets(self) -> Dict[str, List[Tuple[str, Any]]]:
        """Generate various test data sets for comprehensive testing."""
        return {
            "small": [
                (f"small_key_{i}", {"value": f"small_value_{i}", "size": "small"})
                for i in range(self.test_operations)
            ],
            "medium": [
                (f"medium_key_{i}", {"value": "medium_value_" * 100 + str(i), "size": "medium"})
                for i in range(self.test_operations)
            ],
            "large": [
                (f"large_key_{i}", {"value": "large_value_" * 1000 + str(i), "size": "large", "data": list(range(100))})
                for i in range(self.test_operations)
            ],
            "json": [
                (f"json_key_{i}", {
                    "id": i, "name": f"item_{i}", "description": f"Description for item {i}",
                    "tags": [f"tag_{j}" for j in range(5)], "metadata": {"created": "2024-01-01", "version": 1}
                })
                for i in range(self.test_operations)
            ]
        }
    
    async def benchmark_basic_operations(self, cache: CacheInterface, data_size: str = "small") -> BenchmarkResult:
        """Benchmark basic get/set/delete operations with statistical analysis."""
        if data_size not in self.test_data_sets:
            raise ValueError(f"Unknown data size: {data_size}")
        
        test_data = self.test_data_sets[data_size]
        
        # Warmup
        await self._warmup_cache(cache, test_data[:self.warmup_operations])
        
        # Benchmark SET operations
        set_times = []
        set_errors = 0
        
        start_memory = await self._get_memory_usage(cache)
        start_time = time.time()
        
        for key, value in test_data:
            try:
                operation_start = time.time()
                await cache.set(key, value, ttl=300)
                set_times.append((time.time() - operation_start) * 1000)  # Convert to ms
            except Exception as e:
                set_errors += 1
                logger.warning(f"SET operation failed for {key}: {e}")
        
        # Benchmark GET operations
        get_times = []
        get_errors = 0
        
        for key, expected_value in test_data:
            try:
                operation_start = time.time()
                result = await cache.get(key)
                get_times.append((time.time() - operation_start) * 1000)
                
                # Verify data integrity
                if result is None:
                    logger.warning(f"GET operation returned None for {key}")
                
            except Exception as e:
                get_errors += 1
                logger.warning(f"GET operation failed for {key}: {e}")
        
        # Benchmark DELETE operations  
        delete_times = []
        delete_errors = 0
        
        for key, _ in test_data:
            try:
                operation_start = time.time()
                await cache.delete(key)
                delete_times.append((time.time() - operation_start) * 1000)
            except Exception as e:
                delete_errors += 1
                logger.warning(f"DELETE operation failed for {key}: {e}")
        
        total_time = time.time() - start_time
        end_memory = await self._get_memory_usage(cache)
        
        # Calculate comprehensive statistics
        all_times = set_times + get_times + delete_times
        total_operations = len(all_times)
        total_errors = set_errors + get_errors + delete_errors
        
        if not all_times:
            # Handle edge case of all operations failing
            return BenchmarkResult(
                operation_type="basic_operations",
                cache_type=type(cache).__name__,
                total_operations=0,
                duration_seconds=total_time,
                operations_per_second=0,
                avg_duration_ms=0,
                median_duration_ms=0,
                p95_duration_ms=0,
                p99_duration_ms=0,
                min_duration_ms=0,
                max_duration_ms=0,
                memory_usage_mb=end_memory - start_memory,
                success_rate=0,
                error_count=total_errors,
                timestamp=datetime.now().isoformat(),
                test_data_size=data_size,
                additional_metrics={"set_errors": set_errors, "get_errors": get_errors, "delete_errors": delete_errors}
            )
        
        return BenchmarkResult(
            operation_type="basic_operations",
            cache_type=type(cache).__name__,
            total_operations=total_operations,
            duration_seconds=total_time,
            operations_per_second=total_operations / total_time if total_time > 0 else 0,
            avg_duration_ms=statistics.mean(all_times),
            median_duration_ms=statistics.median(all_times),
            p95_duration_ms=self._percentile(all_times, 95),
            p99_duration_ms=self._percentile(all_times, 99),
            min_duration_ms=min(all_times),
            max_duration_ms=max(all_times),
            memory_usage_mb=end_memory - start_memory,
            success_rate=(total_operations - total_errors) / total_operations if total_operations > 0 else 0,
            error_count=total_errors,
            timestamp=datetime.now().isoformat(),
            test_data_size=data_size,
            additional_metrics={
                "set_avg_ms": statistics.mean(set_times) if set_times else 0,
                "get_avg_ms": statistics.mean(get_times) if get_times else 0,
                "delete_avg_ms": statistics.mean(delete_times) if delete_times else 0,
                "set_errors": set_errors,
                "get_errors": get_errors,
                "delete_errors": delete_errors
            }
        )
    
    async def benchmark_memory_cache_performance(self, cache: GenericRedisCache) -> BenchmarkResult:
        """Benchmark L1 memory cache performance specifically."""
        if not hasattr(cache, '_check_memory_cache'):
            raise ValueError("Cache does not support memory cache benchmarking")
        
        # Use small data for memory cache testing
        test_data = self.test_data_sets["small"][:50]  # Smaller dataset for memory cache
        
        # Pre-populate memory cache
        for key, value in test_data:
            await cache.set(key, value, ttl=300)
            # Ensure it's promoted to memory cache
            await cache.get(key)
        
        # Benchmark memory cache hits
        memory_hit_times = []
        memory_hits = 0
        
        start_time = time.time()
        
        for key, _ in test_data:
            operation_start = time.time()
            # Direct memory cache check
            result = cache._check_memory_cache(key)
            memory_hit_times.append((time.time() - operation_start) * 1000)
            
            if result is not None:
                memory_hits += 1
        
        total_time = time.time() - start_time
        
        return BenchmarkResult(
            operation_type="memory_cache",
            cache_type=f"{type(cache).__name__}_memory",
            total_operations=len(test_data),
            duration_seconds=total_time,
            operations_per_second=len(test_data) / total_time if total_time > 0 else 0,
            avg_duration_ms=statistics.mean(memory_hit_times) if memory_hit_times else 0,
            median_duration_ms=statistics.median(memory_hit_times) if memory_hit_times else 0,
            p95_duration_ms=self._percentile(memory_hit_times, 95) if memory_hit_times else 0,
            p99_duration_ms=self._percentile(memory_hit_times, 99) if memory_hit_times else 0,
            min_duration_ms=min(memory_hit_times) if memory_hit_times else 0,
            max_duration_ms=max(memory_hit_times) if memory_hit_times else 0,
            memory_usage_mb=0,  # Memory usage not applicable for this test
            success_rate=memory_hits / len(test_data) if test_data else 0,
            error_count=0,
            timestamp=datetime.now().isoformat(),
            test_data_size="memory_optimized",
            additional_metrics={
                "memory_hit_rate": memory_hits / len(test_data) if test_data else 0,
                "memory_hits": memory_hits
            }
        )
    
    async def benchmark_compression_efficiency(self, cache: GenericRedisCache) -> BenchmarkResult:
        """Benchmark compression performance and ratios."""
        if not hasattr(cache, '_compress_data'):
            raise ValueError("Cache does not support compression benchmarking")
        
        # Use large data for compression testing
        test_data = self.test_data_sets["large"][:20]  # Smaller set for compression testing
        
        compression_times = []
        decompression_times = []
        compression_ratios = []
        total_original_size = 0
        total_compressed_size = 0
        
        for key, value in test_data:
            # Test compression
            original_data = json.dumps(value).encode()
            total_original_size += len(original_data)
            
            start_time = time.time()
            compressed_data = cache._compress_data(value)
            compression_times.append((time.time() - start_time) * 1000)
            
            total_compressed_size += len(compressed_data) if isinstance(compressed_data, bytes) else len(str(compressed_data))
            
            # Test decompression
            start_time = time.time()
            decompressed_data = cache._decompress_data(compressed_data)
            decompression_times.append((time.time() - start_time) * 1000)
            
            # Calculate compression ratio for this item
            if isinstance(compressed_data, bytes):
                ratio = len(compressed_data) / len(original_data)
                compression_ratios.append(ratio)
        
        overall_compression_ratio = total_compressed_size / total_original_size if total_original_size > 0 else 1
        all_times = compression_times + decompression_times
        
        return BenchmarkResult(
            operation_type="compression",
            cache_type=type(cache).__name__,
            total_operations=len(all_times),
            duration_seconds=sum(all_times) / 1000,  # Convert back to seconds
            operations_per_second=len(all_times) / (sum(all_times) / 1000) if all_times else 0,
            avg_duration_ms=statistics.mean(all_times) if all_times else 0,
            median_duration_ms=statistics.median(all_times) if all_times else 0,
            p95_duration_ms=self._percentile(all_times, 95) if all_times else 0,
            p99_duration_ms=self._percentile(all_times, 99) if all_times else 0,
            min_duration_ms=min(all_times) if all_times else 0,
            max_duration_ms=max(all_times) if all_times else 0,
            memory_usage_mb=0,
            success_rate=1.0,  # Assume success if no exceptions
            error_count=0,
            timestamp=datetime.now().isoformat(),
            test_data_size="compression_test",
            additional_metrics={
                "compression_ratio": overall_compression_ratio,
                "space_savings_percent": (1 - overall_compression_ratio) * 100,
                "avg_compression_time_ms": statistics.mean(compression_times) if compression_times else 0,
                "avg_decompression_time_ms": statistics.mean(decompression_times) if decompression_times else 0,
                "original_size_bytes": total_original_size,
                "compressed_size_bytes": total_compressed_size
            }
        )
    
    async def benchmark_ai_operations(self, ai_cache: AIResponseCache) -> Dict[str, BenchmarkResult]:
        """Benchmark AI-specific operations."""
        if not isinstance(ai_cache, AIResponseCache):
            raise ValueError("Cache must be AIResponseCache instance")
        
        # AI-specific test data
        ai_test_scenarios = {
            "summarize": [
                ("Short text for summarization", "summarize", {"max_length": 100}, {"summary": "Brief summary"}),
                ("Medium length text " * 50, "summarize", {"max_length": 200}, {"summary": "Medium summary"}),
            ],
            "sentiment": [
                ("Happy text example", "sentiment", {}, {"sentiment": "positive", "confidence": 0.9}),
                ("Sad text example", "sentiment", {}, {"sentiment": "negative", "confidence": 0.8}),
            ],
            "qa": [
                ("What is the meaning of life?", "qa", {"question": "meaning"}, {"answer": "42"}),
                ("How does this work?", "qa", {"question": "how"}, {"answer": "It works well"}),
            ]
        }
        
        results = {}
        
        for operation, scenarios in ai_test_scenarios.items():
            operation_times = []
            errors = 0
            
            start_time = time.time()
            
            # Test caching
            for text, op, options, response in scenarios:
                try:
                    cache_start = time.time()
                    await ai_cache.cache_response(text, op, options, response)
                    operation_times.append((time.time() - cache_start) * 1000)
                except Exception as e:
                    errors += 1
                    logger.warning(f"AI cache operation failed for {op}: {e}")
            
            # Test retrieval
            for text, op, options, response in scenarios:
                try:
                    retrieve_start = time.time()
                    cached_result = await ai_cache.get_cached_response(text, op, options)
                    operation_times.append((time.time() - retrieve_start) * 1000)
                    
                    if cached_result is None:
                        logger.warning(f"AI cache retrieval failed for {op}")
                        
                except Exception as e:
                    errors += 1
                    logger.warning(f"AI cache retrieval failed for {op}: {e}")
            
            total_time = time.time() - start_time
            
            if operation_times:
                results[operation] = BenchmarkResult(
                    operation_type=f"ai_{operation}",
                    cache_type=type(ai_cache).__name__,
                    total_operations=len(operation_times),
                    duration_seconds=total_time,
                    operations_per_second=len(operation_times) / total_time if total_time > 0 else 0,
                    avg_duration_ms=statistics.mean(operation_times),
                    median_duration_ms=statistics.median(operation_times),
                    p95_duration_ms=self._percentile(operation_times, 95),
                    p99_duration_ms=self._percentile(operation_times, 99),
                    min_duration_ms=min(operation_times),
                    max_duration_ms=max(operation_times),
                    memory_usage_mb=0,
                    success_rate=(len(operation_times) - errors) / len(operation_times) if operation_times else 0,
                    error_count=errors,
                    timestamp=datetime.now().isoformat(),
                    test_data_size="ai_scenarios",
                    additional_metrics={
                        "cache_scenarios": len(scenarios),
                        "total_ai_operations": len(scenarios) * 2  # Cache + retrieve
                    }
                )
        
        return results
    
    async def compare_implementations(self, 
                                    baseline_cache: CacheInterface,
                                    comparison_cache: CacheInterface) -> ComparisonResult:
        """Compare performance between different cache implementations."""
        
        # Benchmark both caches
        baseline_results = {}
        comparison_results = {}
        
        test_sizes = ["small", "medium"]  # Use smaller set for comparison
        
        for size in test_sizes:
            baseline_results[size] = await self.benchmark_basic_operations(baseline_cache, size)
            comparison_results[size] = await self.benchmark_basic_operations(comparison_cache, size)
        
        # Calculate performance comparisons
        operation_comparisons = {}
        significant_differences = []
        overall_changes = []
        
        for size in test_sizes:
            baseline = baseline_results[size]
            comparison = comparison_results[size]
            
            # Compare key metrics
            metrics_to_compare = [
                "operations_per_second", "avg_duration_ms", "p95_duration_ms",
                "memory_usage_mb", "success_rate"
            ]
            
            size_comparisons = {}
            for metric in metrics_to_compare:
                baseline_value = getattr(baseline, metric, 0)
                comparison_value = getattr(comparison, metric, 0)
                
                if baseline_value > 0:
                    percentage_change = ((comparison_value - baseline_value) / baseline_value) * 100
                    size_comparisons[metric] = percentage_change
                    
                    # Track significant differences (>10% change)
                    if abs(percentage_change) > 10:
                        significant_differences.append(
                            f"{metric} changed by {percentage_change:.1f}% for {size} data"
                        )
                    
                    # Track for overall calculation
                    if metric in ["operations_per_second"]:  # Higher is better
                        overall_changes.append(percentage_change)
                    elif metric in ["avg_duration_ms", "p95_duration_ms"]:  # Lower is better
                        overall_changes.append(-percentage_change)
                else:
                    size_comparisons[metric] = 0
            
            operation_comparisons[size] = size_comparisons
        
        # Calculate overall performance change
        overall_performance_change = statistics.mean(overall_changes) if overall_changes else 0
        
        # Generate recommendation
        if overall_performance_change > 10:
            recommendation = f"Significant improvement: {comparison_cache.__class__.__name__} is {overall_performance_change:.1f}% better"
        elif overall_performance_change < -10:
            recommendation = f"Performance regression: {comparison_cache.__class__.__name__} is {abs(overall_performance_change):.1f}% worse"
        else:
            recommendation = "Performance is similar between implementations"
        
        return ComparisonResult(
            baseline_cache=baseline_cache.__class__.__name__,
            comparison_cache=comparison_cache.__class__.__name__,
            operation_comparisons=operation_comparisons,
            overall_performance_change=overall_performance_change,
            recommendation=recommendation,
            significant_differences=significant_differences
        )
    
    async def benchmark_factory_patterns(self) -> Dict[str, BenchmarkResult]:
        """Benchmark different factory creation patterns."""
        factory_results = {}
        
        # Test different factory methods
        factory_methods = [
            ("memory_web", lambda: CacheFactory.for_web_app()),
            ("memory_ai", lambda: CacheFactory.for_ai_app()),
            ("environment_auto", lambda: CacheFactory.from_environment("auto")),
            ("testing", lambda: CacheFactory.for_testing()),
        ]
        
        for method_name, factory_func in factory_methods:
            creation_times = []
            errors = 0
            
            # Test multiple cache creations
            for i in range(10):
                try:
                    start_time = time.time()
                    cache = factory_func()
                    creation_time = (time.time() - start_time) * 1000
                    creation_times.append(creation_time)
                    
                    # Test basic functionality
                    await cache.set(f"test_{i}", {"test": True}, ttl=60)
                    result = await cache.get(f"test_{i}")
                    if result is None:
                        errors += 1
                        
                except Exception as e:
                    errors += 1
                    logger.warning(f"Factory method {method_name} failed: {e}")
            
            if creation_times:
                factory_results[method_name] = BenchmarkResult(
                    operation_type=f"factory_{method_name}",
                    cache_type="factory_created",
                    total_operations=len(creation_times),
                    duration_seconds=sum(creation_times) / 1000,
                    operations_per_second=len(creation_times) / (sum(creation_times) / 1000) if creation_times else 0,
                    avg_duration_ms=statistics.mean(creation_times),
                    median_duration_ms=statistics.median(creation_times),
                    p95_duration_ms=self._percentile(creation_times, 95),
                    p99_duration_ms=self._percentile(creation_times, 99),
                    min_duration_ms=min(creation_times),
                    max_duration_ms=max(creation_times),
                    memory_usage_mb=0,
                    success_rate=(len(creation_times) - errors) / len(creation_times) if creation_times else 0,
                    error_count=errors,
                    timestamp=datetime.now().isoformat(),
                    test_data_size="factory_test",
                    additional_metrics={
                        "creation_method": method_name,
                        "functional_test_errors": errors
                    }
                )
        
        return factory_results
    
    def generate_performance_report(self, results: Dict[str, BenchmarkResult], 
                                   comparison: Optional[ComparisonResult] = None) -> str:
        """Generate comprehensive performance report with recommendations."""
        report_lines = []
        report_lines.append("=" * 80)
        report_lines.append("CACHE PERFORMANCE BENCHMARK REPORT")
        report_lines.append("=" * 80)
        report_lines.append(f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report_lines.append("")
        
        # Summary section
        report_lines.append("SUMMARY")
        report_lines.append("-" * 40)
        
        if results:
            fastest_cache = min(results.items(), key=lambda x: x[1].avg_duration_ms)
            highest_throughput = max(results.items(), key=lambda x: x[1].operations_per_second)
            
            report_lines.append(f"Fastest Average Response: {fastest_cache[0]} ({fastest_cache[1].avg_duration_ms:.2f}ms)")
            report_lines.append(f"Highest Throughput: {highest_throughput[0]} ({highest_throughput[1].operations_per_second:.1f} ops/sec)")
        
        report_lines.append("")
        
        # Detailed results
        report_lines.append("DETAILED RESULTS")
        report_lines.append("-" * 40)
        
        for result_name, result in results.items():
            report_lines.append(f"\n{result_name.upper()} ({result.cache_type})")
            report_lines.append(f"  Total Operations: {result.total_operations}")
            report_lines.append(f"  Duration: {result.duration_seconds:.2f}s")
            report_lines.append(f"  Throughput: {result.operations_per_second:.1f} ops/sec")
            report_lines.append(f"  Average Latency: {result.avg_duration_ms:.2f}ms")
            report_lines.append(f"  95th Percentile: {result.p95_duration_ms:.2f}ms")
            report_lines.append(f"  99th Percentile: {result.p99_duration_ms:.2f}ms")
            report_lines.append(f"  Success Rate: {result.success_rate * 100:.1f}%")
            
            if result.additional_metrics:
                report_lines.append("  Additional Metrics:")
                for key, value in result.additional_metrics.items():
                    if isinstance(value, (int, float)):
                        report_lines.append(f"    {key}: {value:.2f}")
                    else:
                        report_lines.append(f"    {key}: {value}")
        
        # Comparison section
        if comparison:
            report_lines.append("\nCOMPARISON ANALYSIS")
            report_lines.append("-" * 40)
            report_lines.append(f"Baseline: {comparison.baseline_cache}")
            report_lines.append(f"Comparison: {comparison.comparison_cache}")
            report_lines.append(f"Overall Performance Change: {comparison.overall_performance_change:.1f}%")
            report_lines.append(f"Recommendation: {comparison.recommendation}")
            
            if comparison.significant_differences:
                report_lines.append("\nSignificant Differences:")
                for diff in comparison.significant_differences:
                    report_lines.append(f"  • {diff}")
        
        # Recommendations section
        report_lines.append("\nRECOMMENDations")
        report_lines.append("-" * 40)
        
        # Generate context-aware recommendations
        if results:
            recommendations = self._generate_recommendations(results, comparison)
            for rec in recommendations:
                report_lines.append(f"  • {rec}")
        
        report_lines.append("")
        report_lines.append("=" * 80)
        
        return "\n".join(report_lines)
    
    def _generate_recommendations(self, results: Dict[str, BenchmarkResult], 
                                comparison: Optional[ComparisonResult]) -> List[str]:
        """Generate intelligent recommendations based on benchmark results."""
        recommendations = []
        
        # Performance-based recommendations
        for result_name, result in results.items():
            if result.success_rate < 0.95:
                recommendations.append(
                    f"{result_name}: Low success rate ({result.success_rate*100:.1f}%) - investigate error handling"
                )
            
            if result.p95_duration_ms > result.avg_duration_ms * 3:
                recommendations.append(
                    f"{result_name}: High latency variance - consider connection pooling or load balancing"
                )
            
            if "memory_usage_mb" in result.additional_metrics:
                memory_usage = result.additional_metrics["memory_usage_mb"]
                if memory_usage > 100:  # 100MB threshold
                    recommendations.append(
                        f"{result_name}: High memory usage ({memory_usage:.1f}MB) - consider memory optimization"
                    )
        
        # Comparison-based recommendations
        if comparison and comparison.significant_differences:
            recommendations.append(
                f"Significant performance differences detected - review {comparison.recommendation.lower()}"
            )
        
        # Cache-type specific recommendations
        ai_results = [r for name, r in results.items() if "ai" in name.lower()]
        if ai_results:
            avg_ai_latency = sum(r.avg_duration_ms for r in ai_results) / len(ai_results)
            if avg_ai_latency > 100:  # 100ms threshold
                recommendations.append(
                    "AI cache latency is high - consider increasing memory cache size or optimizing text processing"
                )
        
        if not recommendations:
            recommendations.append("Performance looks good - no specific recommendations")
        
        return recommendations
    
    async def _warmup_cache(self, cache: CacheInterface, warmup_data: List[Tuple[str, Any]]):
        """Warm up cache before benchmarking."""
        for key, value in warmup_data:
            try:
                await cache.set(key, value, ttl=300)
            except Exception:
                pass  # Ignore warmup failures
    
    async def _get_memory_usage(self, cache: CacheInterface) -> float:
        """Get cache memory usage in MB."""
        try:
            if hasattr(cache, 'get_memory_usage'):
                stats = cache.get_memory_usage()
                if 'memory_usage_mb' in stats:
                    return stats['memory_usage_mb']
        except Exception:
            pass
        
        return 0.0
    
    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile of data."""
        if not data:
            return 0.0
        
        k = (len(data) - 1) * percentile / 100
        f = int(k)
        c = k - f
        
        if f == len(data) - 1:
            return data[f]
        
        return data[f] * (1 - c) + data[f + 1] * c
    
    def save_results_to_file(self, results: Dict[str, BenchmarkResult], 
                            filename: str, comparison: Optional[ComparisonResult] = None):
        """Save benchmark results to JSON file."""
        output_data = {
            "timestamp": datetime.now().isoformat(),
            "results": {name: asdict(result) for name, result in results.items()},
            "comparison": asdict(comparison) if comparison else None
        }
        
        with open(filename, 'w') as f:
            json.dump(output_data, f, indent=2, default=str)
        
        logger.info(f"Benchmark results saved to {filename}")
```

### 5. Comprehensive Documentation, Migration Guides, and Examples

**New files**: 
- `backend/examples/cache/comprehensive_usage_examples.py`
- `docs/guides/infrastructure/CACHE_MIGRATION.md`
- `docs/guides/infrastructure/CACHE_USAGE.md`

**Dual Documentation Approach**: Maintain both usage documentation for new developers and migration patterns for future template versions or existing implementations.

**Migration Guide (`docs/guides/infrastructure/CACHE_MIGRATION.md`):**
- Migration from inheritance-based hooks to callback composition
- Upgrading from older template versions with different cache architectures
- Step-by-step migration checklist with code transformations
- Backward compatibility patterns and transition strategies
- Performance validation during migration

**Usage Guide (`docs/guides/infrastructure/CACHE_USAGE.md`):**
- Choosing the right cache type for your application
- Configuration with CacheConfigBuilder for different environments
- Using CacheFactory for one-line cache setup
- Callback composition patterns for custom behavior
- Code examples for web apps, AI applications, and testing scenarios

```python
"""Comprehensive cache usage examples demonstrating Phase 3 developer experience improvements."""

import asyncio
import os
from typing import Dict, Any

# Phase 3 imports - simplified developer experience
from app.infrastructure.cache import (
    CacheFactory,
    CacheConfig, 
    CacheConfigBuilder,
    EnvironmentPresets,
    CachePerformanceBenchmark
)

async def example_1_simple_web_app_setup():
    """Example 1: Simple web application cache setup - one line of code."""
    print("=== Example 1: Simple Web App Setup ===")
    
    # One-line cache setup for web applications using callback composition
    cache = CacheFactory.for_web_app(
        redis_url="redis://localhost:6379",
        # Optional: Add custom callbacks for specific behaviors
        custom_callbacks={
            'get_success': lambda key, value, source: print(f"Cache hit: {key}"),
            'get_miss': lambda key: print(f"Cache miss: {key}")
        }
    )
    
    # Basic usage
    await cache.set("user:123", {"name": "John", "email": "john@example.com"}, ttl=1800)
    user_data = await cache.get("user:123")
    print(f"Retrieved user: {user_data}")
    
    # Pattern operations
    keys = await cache.get_keys("user:*")
    print(f"Found {len(keys)} user keys")
    
    print("✅ Web app cache setup complete!\n")

async def example_2_ai_app_setup():
    """Example 2: AI application cache setup with intelligent defaults."""
    print("=== Example 2: AI App Setup ===")
    
    # One-line cache setup for AI applications with optimized settings
    ai_cache = CacheFactory.for_ai_app(
        redis_url="redis://localhost:6379",
        text_hash_threshold=500,  # Hash texts over 500 characters
        operation_ttls={
            "summarize": 7200,  # 2 hours
            "sentiment": 86400,  # 24 hours
            "qa": 1800  # 30 minutes
        }
    )
    
    # AI-specific usage
    await ai_cache.cache_response(
        text="This is a sample document for summarization testing.",
        operation="summarize",
        options={"max_length": 100},
        response={"summary": "Sample document for testing", "confidence": 0.9}
    )
    
    # Retrieve AI response
    cached_result = await ai_cache.get_cached_response(
        text="This is a sample document for summarization testing.",
        operation="summarize", 
        options={"max_length": 100}
    )
    print(f"AI cache result: {cached_result['summary']}")
    
    # AI-specific analytics
    ai_stats = ai_cache.get_ai_performance_summary()
    print(f"AI cache hit rate: {ai_stats.get('overall_hit_rate', 0):.1f}%")
    
    print("✅ AI app cache setup complete!\n")

async def example_3_environment_based_setup():
    """Example 3: Environment-based automatic cache setup."""
    print("=== Example 3: Environment-Based Setup ===")
    
    # Set up environment variables (normally done via deployment/config)
    os.environ.update({
        "REDIS_URL": "redis://localhost:6379",
        "CACHE_DEFAULT_TTL": "3600",
        "CACHE_MEMORY_SIZE": "150",
        "ENABLE_AI_CACHE": "true"
    })
    
    # Automatic detection based on environment and application type
    cache = CacheFactory.from_environment(app_type="auto")
    
    print(f"Auto-detected cache type: {type(cache).__name__}")
    
    # Test functionality
    await cache.set("env_test", {"auto_detected": True}, ttl=60)
    result = await cache.get("env_test")
    print(f"Environment cache test: {result}")
    
    print("✅ Environment-based setup complete!\n")

async def example_4_configuration_builder_pattern():
    """Example 4: Using configuration builder for complex setups."""
    print("=== Example 4: Configuration Builder Pattern ===")
    
    # Build configuration using fluent interface
    config = (CacheConfigBuilder()
              .for_environment("production")
              .with_redis("redis://prod-redis:6379", auth="secret-password")
              .with_security(tls_cert_path="/path/to/cert.pem")
              .with_compression(threshold=500, level=8)
              .with_memory_cache(size=300)
              .with_ai_features(
                  text_hash_threshold=1000,
                  operation_ttls={
                      "summarize": 14400,  # 4 hours for production
                      "sentiment": 172800,  # 48 hours
                  }
              )
              .build())
    
    # Create cache from configuration
    cache = CacheFactory.create_cache_from_config(config)
    
    print(f"Configuration-based cache: {type(cache).__name__}")
    print(f"Redis URL: {config.redis_url}")
    print(f"Environment: {config.environment}")
    print(f"AI features enabled: {config.ai_config is not None}")
    
    print("✅ Configuration builder pattern complete!\n")

async def example_5_fallback_and_resilience():
    """Example 5: Automatic fallback and resilience patterns."""
    print("=== Example 5: Fallback and Resilience ===")
    
    # Configuration for primary cache with fallback
    primary_config = (CacheConfigBuilder()
                      .for_environment("production")
                      .with_redis("redis://might-be-down:6379")
                      .with_ai_features()
                      .build())
    
    # Create cache with automatic fallback
    cache = await CacheFactory.create_with_fallback(
        primary_config=primary_config,
        fallback_type="memory"
    )
    
    print(f"Cache with fallback: {type(cache).__name__}")
    
    # Test functionality regardless of Redis availability
    await cache.set("resilience_test", {"fallback": "working"}, ttl=300)
    result = await cache.get("resilience_test")
    print(f"Resilience test result: {result}")
    
    print("✅ Fallback and resilience complete!\n")

async def example_6_testing_patterns():
    """Example 6: Testing-optimized cache patterns."""
    print("=== Example 6: Testing Patterns ===")
    
    # Quick test cache setup
    test_cache = CacheFactory.for_testing("memory")
    
    # Fast testing with short TTLs
    await test_cache.set("test_key", {"test": True}, ttl=5)
    
    # Test with Redis for integration testing
    integration_cache = CacheFactory.for_testing("redis") 
    
    print(f"Test cache: {type(test_cache).__name__}")
    print(f"Integration cache: {type(integration_cache).__name__}")
    
    # Verify test isolation
    test_result = await test_cache.get("test_key")
    print(f"Test isolation verified: {test_result is not None}")
    
    print("✅ Testing patterns complete!\n")

async def example_7_performance_benchmarking():
    """Example 7: Built-in performance benchmarking."""
    print("=== Example 7: Performance Benchmarking ===")
    
    # Create different cache types for comparison
    memory_cache = CacheFactory.for_web_app()  # Falls back to memory
    
    # Set up Redis cache if available
    try:
        redis_cache = CacheFactory.for_web_app(redis_url="redis://localhost:6379")
    except:
        redis_cache = memory_cache  # Use same cache if Redis unavailable
    
    # Initialize benchmarking suite
    benchmark = CachePerformanceBenchmark(warmup_operations=5, test_operations=20)
    
    # Benchmark both caches
    print("Running performance benchmarks...")
    
    memory_results = await benchmark.benchmark_basic_operations(memory_cache, "small")
    redis_results = await benchmark.benchmark_basic_operations(redis_cache, "small")
    
    # Compare results
    comparison = await benchmark.compare_implementations(memory_cache, redis_cache)
    
    # Generate comprehensive report
    results = {
        "memory_cache": memory_results,
        "redis_cache": redis_results
    }
    
    report = benchmark.generate_performance_report(results, comparison)
    print("\n" + report)
    
    print("✅ Performance benchmarking complete!\n")

async def example_8_monitoring_and_analytics():
    """Example 8: Built-in monitoring and analytics."""
    print("=== Example 8: Monitoring and Analytics ===")
    
    # Create AI cache with analytics
    ai_cache = CacheFactory.for_ai_app()
    
    # Generate some activity for analytics
    test_operations = [
        ("Document about AI", "summarize", {"max_length": 100}, {"summary": "AI document"}),
        ("Happy customer review", "sentiment", {}, {"sentiment": "positive", "confidence": 0.9}),
        ("Technical question", "qa", {"question": "How?"}, {"answer": "Like this"}),
    ]
    
    for text, operation, options, response in test_operations:
        await ai_cache.cache_response(text, operation, options, response)
        # Retrieve to generate hit metrics
        await ai_cache.get_cached_response(text, operation, options)
    
    # Get comprehensive analytics
    if hasattr(ai_cache, 'get_ai_performance_summary'):
        analytics = ai_cache.get_ai_performance_summary()
        print("AI Cache Analytics:")
        print(f"  Total operations: {analytics.get('total_ai_operations', 0)}")
        print(f"  Overall hit rate: {analytics.get('overall_hit_rate', 0):.1f}%")
        
        hit_rates = analytics.get('hit_rate_by_operation', {})
        for operation, rate in hit_rates.items():
            print(f"  {operation} hit rate: {rate:.1f}%")
        
        recommendations = analytics.get('optimization_recommendations', [])
        if recommendations:
            print("  Optimization recommendations:")
            for rec in recommendations:
                print(f"    • {rec}")
    
    print("✅ Monitoring and analytics complete!\n")

async def example_9_migration_from_existing_cache():
    """Example 9: Migration from existing cache implementations."""
    print("=== Example 9: Migration Example ===")
    
    # Simulate existing cache data
    old_data = {
        "user:1": {"name": "Alice", "role": "admin"},
        "user:2": {"name": "Bob", "role": "user"},
        "config:app": {"theme": "dark", "version": "2.1"}
    }
    
    # Create old and new cache implementations
    old_cache = CacheFactory.for_testing("memory")
    new_cache = CacheFactory.for_web_app()
    
    # Populate old cache
    for key, value in old_data.items():
        await old_cache.set(key, value, ttl=3600)
    
    # Migration process
    print("Migrating cache data...")
    migrated_count = 0
    
    for key, expected_value in old_data.items():
        # Read from old cache
        value = await old_cache.get(key)
        if value:
            # Write to new cache
            await new_cache.set(key, value, ttl=3600)
            
            # Verify migration
            migrated_value = await new_cache.get(key)
            if migrated_value == expected_value:
                migrated_count += 1
                print(f"  ✓ Migrated {key}")
            else:
                print(f"  ✗ Migration failed for {key}")
    
    print(f"Migration complete: {migrated_count}/{len(old_data)} items migrated")
    print("✅ Migration example complete!\n")

async def example_10_advanced_configuration_patterns():
    """Example 10: Advanced configuration patterns and presets."""
    print("=== Example 10: Advanced Configuration Patterns ===")
    
    # Using environment presets
    dev_config = EnvironmentPresets.development()
    prod_config = EnvironmentPresets.production()
    ai_dev_config = EnvironmentPresets.ai_development()
    
    print("Environment Presets:")
    print(f"  Development TTL: {dev_config.default_ttl}s")
    print(f"  Production TTL: {prod_config.default_ttl}s")
    print(f"  AI Development has AI config: {ai_dev_config.ai_config is not None}")
    
    # Configuration from file (example)
    config_from_builder = (CacheConfigBuilder()
                          .from_environment()  # Load from environment variables
                          .with_compression(threshold=2000, level=6)
                          .build())
    
    print(f"Config from environment: {config_from_builder.environment}")
    
    # Validation example
    validation_result = config_from_builder.validate() if hasattr(config_from_builder, 'validate') else None
    if validation_result:
        print(f"Configuration valid: {validation_result.is_valid}")
        if validation_result.warnings:
            print("  Warnings:")
            for warning in validation_result.warnings:
                print(f"    • {warning}")
    
    print("✅ Advanced configuration patterns complete!\n")

async def main():
    """Run all examples to demonstrate Phase 3 developer experience improvements."""
    print("🚀 CACHE INFRASTRUCTURE PHASE 3 - DEVELOPER EXPERIENCE EXAMPLES")
    print("=" * 80)
    print()
    
    examples = [
        example_1_simple_web_app_setup,
        example_2_ai_app_setup,
        example_3_environment_based_setup,
        example_4_configuration_builder_pattern,
        example_5_fallback_and_resilience,
        example_6_testing_patterns,
        example_7_performance_benchmarking,
        example_8_monitoring_and_analytics,
        example_9_migration_from_existing_cache,
        example_10_advanced_configuration_patterns,
    ]
    
    for example in examples:
        try:
            await example()
        except Exception as e:
            print(f"❌ Example failed: {e}")
            print()
    
    print("🎉 All examples completed!")
    print("=" * 80)
    print("\nDeveloper Experience Summary:")
    print("• One-line cache setup for web and AI applications")
    print("• Automatic environment detection and configuration")
    print("• Fluent configuration builder with validation")
    print("• Built-in fallback and resilience patterns")
    print("• Comprehensive testing utilities")
    print("• Performance benchmarking and analytics")
    print("• Intelligent monitoring and optimization recommendations")
    print("• Seamless migration support")

if __name__ == "__main__":
    asyncio.run(main())
```

### 6. Updated Module Exports and Integration

**Update**: `backend/app/infrastructure/cache/__init__.py`

```python
# Base interface
from .base import CacheInterface

# Implementations
from .memory import InMemoryCache
from .redis_generic import GenericRedisCache  # From Phase 1
from .redis_ai import AIResponseCache         # From Phase 2

# Phase 3: Developer Experience Components
from .factory import CacheFactory
from .config import (
    CacheConfig, AICacheConfig, CacheConfigBuilder, 
    EnvironmentPresets, ValidationResult
)
from .dependencies import (
    get_cache_service, get_cache_config, get_web_cache_service,
    get_ai_cache_service, get_test_cache, cleanup_cache_registry,
    get_cache_health_status
)

# Core components (from previous phases)
from .key_generator import CacheKeyGenerator                    # Phase 1
from .parameter_mapping import CacheParameterMapper            # Phase 2

# Infrastructure components (from Phase 1)
from .migration import CacheMigrationManager
from .compatibility import CacheCompatibilityWrapper
from .security import RedisCacheSecurityManager, SecurityConfig

# Monitoring and performance (enhanced in Phase 3)
from .monitoring import (
    CachePerformanceMonitor, PerformanceMetric, 
    CompressionMetric, MemoryUsageMetric, InvalidationMetric
)
from .benchmarks import (
    CachePerformanceBenchmark, BenchmarkResult, ComparisonResult
)

# Comprehensive exports list for Phase 3
__all__ = [
    # Core interfaces and implementations
    "CacheInterface", "InMemoryCache", "GenericRedisCache", "AIResponseCache",
    
    # Phase 3: Developer Experience
    "CacheFactory",
    "CacheConfig", "AICacheConfig", "CacheConfigBuilder", "EnvironmentPresets", "ValidationResult",
    
    # FastAPI Dependencies
    "get_cache_service", "get_cache_config", "get_web_cache_service", 
    "get_ai_cache_service", "get_test_cache", "cleanup_cache_registry", "get_cache_health_status",
    
    # Core components
    "CacheKeyGenerator", "CacheParameterMapper",
    
    # Migration and compatibility (Phase 1)
    "CacheMigrationManager", "CacheCompatibilityWrapper",
    
    # Security (Phase 1)
    "RedisCacheSecurityManager", "SecurityConfig",
    
    # Monitoring and performance
    "CachePerformanceMonitor", "PerformanceMetric", "CompressionMetric", 
    "MemoryUsageMetric", "InvalidationMetric",
    "CachePerformanceBenchmark", "BenchmarkResult", "ComparisonResult",
    
    # Redis availability
    "REDIS_AVAILABLE", "aioredis"
]

# Version and metadata
__version__ = "3.0.0"  # Phase 3 version
__description__ = "Enhanced developer experience cache infrastructure with factories, configuration management, and comprehensive tooling"
```

## Enhanced Implementation Timeline

### Week 1: Factory and Application Detection
- [ ] Implement CacheFactory with smart application type detection
- [ ] Create comprehensive testing for application type detection (test_factory.py)
- [ ] Add comprehensive input validation and error handling
- [ ] Create application type detection logic with multiple signal sources
- [ ] Implement factory methods for different use cases (web, AI, testing)
- [ ] Add lifecycle management for async cache instances

### Week 2: Configuration Management and Builder Pattern
- [ ] Implement CacheConfig and CacheConfigBuilder with fluent interface
- [ ] Add environment variable integration and validation
- [ ] Create EnvironmentPresets with optimized defaults
- [ ] Implement configuration file loading and saving
- [ ] Add comprehensive validation with helpful error messages

### Week 3: FastAPI Integration and Benchmarking
- [ ] Create comprehensive FastAPI dependency providers with lifecycle management
- [ ] Implement cache registry for proper resource cleanup
- [ ] Enhance benchmarking suite with factory pattern testing
- [ ] Add performance comparison tools and intelligent recommendations
- [ ] Create health check dependencies and monitoring integration

### Week 4: Documentation, Examples, and Validation
- [ ] Create comprehensive usage examples for all patterns
- [ ] Update all documentation with Phase 3 features
- [ ] Create comprehensive developer usage documentation AND migration guides
- [ ] Implement migration tools for potential future template versions
- [ ] Comprehensive integration testing across all components
- [ ] Final performance validation and optimization

## Enhanced Success Criteria

✅ **One-Line Cache Setup**: Developers can create appropriate caches with single factory calls  
✅ **Smart Environment Detection**: Automatic application type detection works reliably across scenarios  
✅ **Comprehensive Configuration**: Builder pattern supports all cache configuration needs with validation  
✅ **Seamless FastAPI Integration**: Dependency injection works flawlessly with lifecycle management  
✅ **Performance Insights**: Built-in benchmarking provides actionable optimization recommendations  
✅ **Developer Documentation**: Comprehensive usage guide for new template users
✅ **Migration Support**: Clear migration patterns for future template versions and existing implementations  
✅ **Testing Integration**: Testing utilities integrate seamlessly with existing test suites  
✅ **Documentation Quality**: Comprehensive documentation with practical examples  
✅ **Developer Productivity**: 5-minute setup for any cache use case  
✅ **Error Handling**: Comprehensive error handling with helpful error messages  

## Enhanced Risk Mitigation

### Usability Risks
- **Complex Factory API**: Simple methods with sensible defaults and comprehensive validation
- **Configuration Confusion**: Builder pattern with validation and environment presets
- **Migration Complexity**: Step-by-step migration guides with automated tools
- **Integration Issues**: Comprehensive dependency injection with lifecycle management

### Technical Risks
- **Performance Overhead**: Benchmarking validates factory overhead is minimal
- **Circular Dependencies**: Careful dependency management and lazy loading
- **Memory Leaks**: Proper cache registry and cleanup mechanisms
- **Configuration Validation**: Extensive validation with clear error messages

### Deployment Risks
- **Environment Detection**: Robust detection logic with fallbacks
- **Security Configuration**: Secure defaults with validation
- **Monitoring Integration**: Built-in health checks and performance monitoring

## Dependencies for Future Phases

Phase 4 (Advanced Features) will build on:
- ✅ One-line cache setup working reliably
- ✅ Configuration management with validation
- ✅ Performance benchmarking infrastructure
- ✅ Comprehensive testing and monitoring
- ✅ Developer documentation and examples
- ✅ Migration tooling and compatibility

### 7. Callback Composition and Migration Examples

**New file**: `backend/examples/cache/callback_composition_examples.py`

**Examples demonstrating:**
- Custom callback composition for web applications with audit, performance, and alerting callbacks
- Migration from inheritance hooks to callback composition patterns
- Advanced callback chaining and composition techniques
- Integration of callbacks with FastAPI dependency injection
- Testing strategies for callback-based cache implementations

**Migration Documentation Sections:**
```markdown
# Migration from Inheritance Hooks to Callback Composition

## Old Approach (Inheritance-based)
- Required method overrides in subclasses
- Tight coupling between parent and child classes
- Difficult to test and modify behavior dynamically

## New Approach (Callback Composition) 
- Pass callback functions during initialization
- Loose coupling via function composition
- Easy to test with mock callbacks
- Runtime behavior modification possible
- Follows composition over inheritance principles

## Migration Steps
1. Identify overridden methods in subclasses
2. Extract logic into callback functions
3. Pass callbacks to parent during initialization
4. Remove method overrides from subclasses
5. Update tests to use callback mocking
```

This enhanced Phase 3 plan transforms the cache infrastructure into a developer-friendly, production-ready system with callback composition architecture that can be set up and optimized in minutes while maintaining all the advanced capabilities built in the previous phases, plus comprehensive migration support for future template versions.