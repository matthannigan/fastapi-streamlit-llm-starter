# Cache Infrastructure Refactoring PRD

# Overview  
The current cache infrastructure in the FastAPI-Streamlit LLM starter template suffers from architectural issues that limit its reusability and maintainability. The `AIResponseCache` class is designed specifically for AI/LLM operations but is forced to serve as a generic Redis cache, resulting in unnecessary complexity for non-AI use cases and code duplication with the `InMemoryCache` implementation.

This refactoring aims to create a clean, extensible cache architecture that separates generic caching concerns from AI-specific optimizations, making the starter template suitable for both AI projects and general-purpose FastAPI applications.

**Problem Statement:**
- `AIResponseCache` contains AI-specific logic (operation TTLs, text tiers, specialized key generation) that adds complexity for generic caching
- Code duplication between `AIResponseCache`'s internal memory cache and the standalone `InMemoryCache` class
- No clean generic Redis cache option for non-AI projects
- Inconsistent interfaces between memory and Redis cache implementations
- Template users are forced to use AI-specific cache features even for simple web applications

**Target Users:**
- Developers building generic FastAPI applications from the starter template
- AI/LLM application developers who need specialized caching features
- Template maintainers seeking cleaner, more maintainable code architecture

**Value Proposition:**
- Clean separation between generic and AI-specific caching concerns
- Consistent interfaces across all cache implementations
- Reduced complexity for generic use cases
- Better extensibility for future cache types
- Improved testability and maintainability

# Core Features  

## 1. GenericRedisCache - Universal Redis Caching
**What it does:** Provides a clean, generic Redis cache implementation that mirrors `InMemoryCache` functionality without AI-specific features.

**Why it's important:** Enables the starter template to serve general-purpose FastAPI projects without forcing AI-specific overhead.

**Implementation:**
```python
class GenericRedisCache(CacheInterface):
    """Generic Redis cache with compression and monitoring"""
    
    def __init__(self, redis_url: str = "redis://redis:6379", 
                 default_ttl: int = 3600,
                 compression_threshold: int = 1000,
                 compression_level: int = 6,
                 performance_monitor: Optional[CachePerformanceMonitor] = None):
        self.redis = None
        self.redis_url = redis_url
        self.default_ttl = default_ttl
        self.compression_threshold = compression_threshold
        self.compression_level = compression_level
        self.performance_monitor = performance_monitor or CachePerformanceMonitor()
    
    async def get(self, key: str) -> Any
    async def set(self, key: str, value: Any, ttl: int = None) -> None
    async def delete(self, key: str) -> None
    async def exists(self, key: str) -> bool
    async def get_ttl(self, key: str) -> Optional[int]
    async def clear(self) -> None
    def get_stats(self) -> Dict[str, Any]
```

## 2. Refactored AIResponseCache - Specialized AI Caching
**What it does:** Extends `GenericRedisCache` with AI-specific optimizations including intelligent key generation, operation-specific TTLs, and text-based caching strategies.

**Why it's important:** Maintains all current AI-specific functionality while building on a solid generic foundation.

**Implementation:**
```python
class AIResponseCache(GenericRedisCache):
    """AI-optimized cache extending GenericRedisCache"""
    
    def __init__(self, text_hash_threshold: int = 1000,
                 text_size_tiers: dict = None,
                 operation_ttls: dict = None,
                 **kwargs):
        super().__init__(**kwargs)
        
        # AI-specific configuration
        self.operation_ttls = operation_ttls or {
            "summarize": 7200,    # 2 hours
            "sentiment": 86400,   # 24 hours  
            "key_points": 7200,   # 2 hours
            "questions": 3600,    # 1 hour
            "qa": 1800           # 30 minutes
        }
        
        self.text_size_tiers = text_size_tiers or {
            'small': 500,
            'medium': 5000, 
            'large': 50000
        }
        
        self.key_generator = CacheKeyGenerator(
            text_hash_threshold=text_hash_threshold,
            hash_algorithm=hashlib.sha256,
            performance_monitor=self.performance_monitor
        )
    
    # AI-specific methods
    async def cache_response(self, text: str, operation: str, 
                           options: Dict[str, Any], response: Dict[str, Any], 
                           question: str = None) -> None
    
    async def get_cached_response(self, text: str, operation: str, 
                                options: Dict[str, Any], question: str = None) -> Optional[Dict[str, Any]]
    
    async def invalidate_by_operation(self, operation: str, operation_context: str = "") -> None
    
    def get_ai_performance_summary(self) -> Dict[str, Any]
```

## 3. Enhanced CacheKeyGenerator - Modular Key Generation
**What it does:** Extracts intelligent key generation logic into a reusable component that can work with any cache implementation.

**Why it's important:** Enables text-aware caching optimizations to be applied independently of the cache backend.

**Implementation:**
```python
class CacheKeyGenerator:
    def __init__(self, text_hash_threshold: int = 1000, 
                 hash_algorithm=hashlib.sha256,
                 performance_monitor: Optional[CachePerformanceMonitor] = None):
        self.text_hash_threshold = text_hash_threshold
        self.hash_algorithm = hash_algorithm
        self.performance_monitor = performance_monitor
    
    def generate_cache_key(self, text: str, operation: str, 
                          options: Dict[str, Any], question: Optional[str] = None) -> str:
        # Efficient key generation with text hashing for large content
        
    def _hash_text_efficiently(self, text: str) -> str:
        # Streaming hash approach for memory efficiency
```

## 4. Unified Performance Monitoring
**What it does:** Provides consistent performance monitoring across all cache implementations with both generic and AI-specific metrics.

**Why it's important:** Ensures all cache types provide comprehensive observability for production deployments.

## 5. Consistent Interface Design
**What it does:** Ensures all cache implementations follow the same patterns for initialization, configuration, and operation.

**Why it's important:** Simplifies developer experience and enables easy switching between cache types.

# User Experience  

## Developer Personas

### 1. Generic FastAPI Developer
**Needs:** Simple, reliable caching for web application data (user sessions, API responses, configuration)
**Pain Points:** Doesn't want AI-specific complexity, needs Redis persistence
**Solution:** Uses `GenericRedisCache` with clean, familiar interface

**Usage Example:**
```python
from app.infrastructure.cache import GenericRedisCache

# Simple initialization
cache = GenericRedisCache(
    redis_url="redis://localhost:6379",
    default_ttl=3600
)

# Standard caching operations
await cache.set("user:123", user_data, ttl=1800)
user = await cache.get("user:123")
await cache.delete("session:abc")

# Pattern operations
await cache.invalidate_pattern("user:*")
keys = await cache.get_keys("session:*")
```

### 2. AI/LLM Application Developer  
**Needs:** Specialized caching for AI operations with intelligent key generation and operation-specific TTLs
**Pain Points:** Requires text-aware caching, compression for large responses, AI operation optimization
**Solution:** Uses `AIResponseCache` with full AI-specific feature set

**Usage Example:**
```python
from app.infrastructure.cache import AIResponseCache

# AI-optimized initialization
cache = AIResponseCache(
    redis_url="redis://prod:6379",
    text_hash_threshold=500,
    compression_threshold=2000
)

# AI-specific operations
await cache.cache_response(
    text="Long document to analyze...",
    operation="summarize",
    options={"max_length": 100, "model": "gpt-4"},
    response={"summary": "Brief summary", "confidence": 0.95}
)

# Intelligent retrieval
cached = await cache.get_cached_response(
    text="Long document to analyze...",
    operation="summarize",
    options={"max_length": 100, "model": "gpt-4"}
)

# Operation-specific invalidation
await cache.invalidate_by_operation("summarize", 
                                   operation_context="model_update")
```

### 3. Template Maintainer
**Needs:** Clean, maintainable code architecture with clear separation of concerns
**Pain Points:** Code duplication, complex inheritance hierarchies, hard-to-test components
**Solution:** Modular design with composition over inheritance

## Key User Flows

### Flow 1: Generic Web Application Setup
```python
# 1. Developer chooses appropriate cache for their needs
from app.infrastructure.cache import GenericRedisCache, InMemoryCache

# 2. Environment-based configuration
def create_cache() -> CacheInterface:
    if settings.USE_REDIS:
        return GenericRedisCache(redis_url=settings.REDIS_URL)
    else:
        return InMemoryCache(default_ttl=settings.CACHE_TTL)

# 3. Dependency injection into services
class UserService:
    def __init__(self, cache: CacheInterface):
        self.cache = cache
```

### Flow 2: AI Application with Fallback
```python
# 1. Primary AI cache with memory fallback
from app.infrastructure.cache import AIResponseCache, InMemoryCache

class CacheFactory:
    @staticmethod
    async def create_ai_cache() -> CacheInterface:
        try:
            ai_cache = AIResponseCache(redis_url=settings.REDIS_URL)
            if await ai_cache.connect():
                return ai_cache
        except Exception:
            logger.warning("Redis unavailable, falling back to memory cache")
            
        return InMemoryCache(default_ttl=300)  # 5-minute fallback TTL

# 2. Seamless usage regardless of backend
cache = await CacheFactory.create_ai_cache()
await cache.cache_response(...)  # Works with either implementation
```

### Flow 3: Testing and Development
```python
# 1. Easy test setup with memory cache
@pytest.fixture
def test_cache():
    return InMemoryCache(default_ttl=60, max_size=100)

# 2. Integration tests with Redis
@pytest.fixture
def redis_cache():
    return GenericRedisCache(redis_url="redis://test-redis:6379")

# 3. AI-specific tests
@pytest.fixture  
def ai_cache():
    return AIResponseCache(redis_url="redis://test-redis:6379")
```

# Technical Architecture  

## Current State Analysis

### Current Implementation (Post-Refactoring)
The cache infrastructure has been recently refactored and now consists of:

```
backend/app/infrastructure/cache/
├── __init__.py              # Module exports with comprehensive cache components
├── base.py                  # CacheInterface (ABC with get/set/delete contract)
├── memory.py                # InMemoryCache (TTL + LRU with comprehensive features)
├── redis.py                 # AIResponseCache (Redis with AI-specific features)
├── monitoring.py            # CachePerformanceMonitor (comprehensive analytics)
├── README.md                # Detailed documentation and feature comparison
├── redis.py.md              # Additional Redis implementation documentation
└── redis.py.txt             # Implementation notes
```

**What's Working Well:**
- ✅ Solid CacheInterface abstraction enabling dependency injection
- ✅ Feature-rich InMemoryCache with TTL, LRU eviction, and monitoring
- ✅ Sophisticated AIResponseCache with compression, tiered caching, and monitoring
- ✅ Comprehensive CachePerformanceMonitor with detailed analytics
- ✅ Strong documentation and clear module separation

**Gap Analysis - What Still Needs Refactoring:**
- ❌ **No GenericRedisCache**: AIResponseCache still contains both generic Redis functionality AND AI-specific features mixed together
- ❌ **Code Duplication**: Redis operations code is embedded within AI-specific logic
- ❌ **Complexity for Generic Use Cases**: Template users must use AI-specific cache even for simple web apps
- ❌ **Security Integration Gap**: No Redis security features as outlined in Redis Security PRD

## System Components

### 1. Current Cache Hierarchy (As-Is)
```plaintext
CacheInterface (ABC)
├── InMemoryCache (Complete - TTL, LRU, monitoring)
└── AIResponseCache (Mixed - Redis + AI features combined)
    ├── Redis connection management (generic functionality)
    ├── Compression/decompression (generic functionality) 
    ├── CacheKeyGenerator (AI-specific functionality)
    ├── Operation-specific TTLs (AI-specific functionality)
    └── Performance monitoring integration (shared functionality)
```

### 2. Target Cache Hierarchy (To-Be)
```plaintext
CacheInterface (ABC)
├── InMemoryCache (Keep as-is - no changes needed)
├── GenericRedisCache (NEW - extract from AIResponseCache)
│   ├── Redis connection management
│   ├── Compression/decompression  
│   ├── Basic performance monitoring
│   ├── Pattern-based operations (get_keys, invalidate_pattern)
│   └── Security integration (from Redis Security PRD)
└── AIResponseCache (REFACTOR - inherit from GenericRedisCache)
    ├── Extends GenericRedisCache
    ├── CacheKeyGenerator integration
    ├── AI-specific TTL management
    ├── Text-tier optimization
    └── AI-specific monitoring metrics
```

### 3. Supporting Components
```plaintext
CacheKeyGenerator (AI-specific - extract from AIResponseCache)
├── Text hashing strategies
├── Key optimization algorithms
└── Performance measurement

CachePerformanceMonitor (Enhanced - support both generic and AI metrics)
├── Generic cache metrics (hits, misses, operations/sec)
├── AI-specific analytics (operation distribution, text tiers)
└── Security monitoring integration

SecurityManager (NEW - from Redis Security PRD)
├── Redis authentication
├── TLS connection management
├── Application-layer encryption
└── Access control integration
```

### 4. Updated Module Structure (Target)
```plaintext
app/infrastructure/cache/
├── __init__.py              # Updated exports with new components
├── base.py                  # CacheInterface (unchanged)
├── memory.py                # InMemoryCache (unchanged)
├── redis.py                 # GenericRedisCache (extracted from AIResponseCache)
├── ai_cache.py              # AIResponseCache (refactored to inherit from GenericRedisCache)
├── key_generator.py         # CacheKeyGenerator (extracted from AIResponseCache)
├── monitoring.py            # Enhanced monitoring (generic + AI + security metrics)
├── security.py              # SecurityManager (NEW - from Redis Security PRD)
└── README.md                # Updated documentation
```

## Data Models

### Cache Configuration Model
```python
@dataclass
class CacheConfig:
    """Unified cache configuration"""
    redis_url: str = "redis://redis:6379"
    default_ttl: int = 3600
    compression_threshold: int = 1000
    compression_level: int = 6
    
    # AI-specific options (optional)
    text_hash_threshold: Optional[int] = None
    text_size_tiers: Optional[Dict[str, int]] = None
    operation_ttls: Optional[Dict[str, int]] = None

@dataclass
class CacheStats:
    """Standardized cache statistics"""
    total_entries: int
    hit_ratio: float
    memory_usage_bytes: int
    operations_per_second: float
    backend_type: str  # "memory", "redis", "ai_redis"
```

### Performance Metrics Model
```python
@dataclass
class GenericCacheMetrics:
    """Standard cache performance metrics"""
    cache_hits: int
    cache_misses: int
    average_operation_time: float
    compression_ratio: Optional[float]
    
@dataclass 
class AICacheMetrics(GenericCacheMetrics):
    """Extended metrics for AI cache operations"""
    text_processing_time: float
    key_generation_time: float
    operation_distribution: Dict[str, int]
    text_tier_distribution: Dict[str, int]
```

## APIs and Integrations

### 1. Cache Factory API
```python
class CacheFactory:
    """Factory for creating appropriate cache instances"""
    
    @staticmethod
    def create_cache(config: CacheConfig, cache_type: str = "auto") -> CacheInterface:
        """Create cache instance based on configuration and type"""
        
    @staticmethod
    async def create_with_fallback(primary_config: CacheConfig, 
                                 fallback_type: str = "memory") -> CacheInterface:
        """Create cache with automatic fallback on connection failure"""
```

### 2. Dependency Injection Integration
```python
# FastAPI dependency setup
def get_cache() -> CacheInterface:
    """Dependency provider for cache instances"""
    return CacheFactory.create_cache(
        config=CacheConfig(redis_url=settings.REDIS_URL),
        cache_type=settings.CACHE_TYPE
    )

# Usage in endpoints
@app.get("/users/{user_id}")
async def get_user(user_id: str, cache: CacheInterface = Depends(get_cache)):
    # Works with any cache implementation
    cached_user = await cache.get(f"user:{user_id}")
```

### 3. Monitoring Integration
```python
# Prometheus metrics export
@app.get("/metrics/cache")
async def cache_metrics(cache: CacheInterface = Depends(get_cache)):
    stats = cache.get_stats()
    return {
        "cache_hit_ratio": stats.hit_ratio,
        "cache_operations_total": stats.operations_per_second,
        "cache_memory_usage_bytes": stats.memory_usage_bytes
    }
```

## Infrastructure Requirements

### Development Environment
- Redis server (optional, with graceful fallback)
- Python 3.8+ with asyncio support
- Testing framework with async support

### Production Environment  
- Redis cluster or standalone instance
- Performance monitoring integration
- Centralized logging for cache operations

### Dependencies
```python
# Required
redis[asyncio]>=4.5.0
aioredis>=2.0.0

# Optional (graceful degradation)
psutil  # For memory monitoring
prometheus-client  # For metrics export
```

# Development Roadmap (Updated for Current State + Security Integration)

## Phase 1: Generic Redis Cache Extraction + Basic Security (MVP)
**Scope:** Extract generic Redis functionality from AIResponseCache into a new GenericRedisCache class.

**Deliverables:**
- `GenericRedisCache` class with core Redis operations
- Basic compression and serialization
- Connection management with graceful degradation
- Essential performance monitoring
- Unit tests for generic functionality

**Code Example:**
```python
# Minimal GenericRedisCache implementation
class GenericRedisCache(CacheInterface):
    async def get(self, key: str) -> Any:
        # Extract from current AIResponseCache.get()
        
    async def set(self, key: str, value: Any, ttl: int = None) -> None:
        # Extract from current AIResponseCache.set()
        
    async def delete(self, key: str) -> None:
        # Extract from current AIResponseCache.delete()
```

**Success Criteria:**
- All existing generic cache operations work identically
- Performance matches or improves upon current implementation
- Memory usage is optimized compared to AIResponseCache for generic use

## Phase 2: AI Cache Refactoring
**Scope:** Refactor AIResponseCache to extend GenericRedisCache while maintaining all AI-specific features.

**Deliverables:**
- Refactored `AIResponseCache` extending `GenericRedisCache`
- Extracted `CacheKeyGenerator` as standalone component
- AI-specific TTL and text tier management
- Enhanced monitoring for AI operations
- Integration tests ensuring feature parity

**Code Example:**
```python
class AIResponseCache(GenericRedisCache):
    def __init__(self, **kwargs):
        # Separate AI-specific and generic parameters
        ai_params = self._extract_ai_params(kwargs)
        super().__init__(**kwargs)
        self._setup_ai_features(**ai_params)
        
    async def cache_response(self, text: str, operation: str, 
                           options: Dict[str, Any], response: Dict[str, Any], 
                           question: str = None) -> None:
        # Use inherited Redis operations with AI-specific key generation
        cache_key = self.key_generator.generate_cache_key(text, operation, options, question)
        ttl = self.operation_ttls.get(operation, self.default_ttl)
        await self.set(cache_key, response, ttl)
```

**Success Criteria:**
- All existing AI cache functionality preserved
- Code complexity reduced through inheritance
- Clear separation between generic and AI-specific concerns

## Phase 3: Enhanced Developer Experience
**Scope:** Improve developer experience with factory patterns, better configuration, and comprehensive documentation.

**Deliverables:**
- `CacheFactory` for simplified cache creation
- Environment-based cache configuration
- Comprehensive documentation and examples
- Migration guide for existing code
- Performance benchmarking suite

**Code Example:**
```python
# Simplified cache setup for different environments
class CacheFactory:
    @staticmethod
    def for_web_app(redis_url: str = None) -> CacheInterface:
        """Create optimized cache for web applications"""
        if redis_url:
            return GenericRedisCache(redis_url=redis_url, default_ttl=1800)
        return InMemoryCache(default_ttl=1800, max_size=1000)
    
    @staticmethod  
    def for_ai_app(redis_url: str = None, **ai_options) -> CacheInterface:
        """Create optimized cache for AI applications"""
        if redis_url:
            return AIResponseCache(redis_url=redis_url, **ai_options)
        return InMemoryCache(default_ttl=300, max_size=100)
```

**Success Criteria:**
- Template users can easily choose appropriate cache type
- Clear documentation with practical examples
- Performance benchmarks demonstrate improvements

## Phase 4: Advanced Features and Optimizations
**Scope:** Add advanced features like cache warming, distributed invalidation, and enhanced monitoring.

**Deliverables:**
- Cache warming strategies
- Distributed cache invalidation
- Advanced performance analytics
- Load testing and optimization
- Production deployment guide

**Success Criteria:**
- Production-ready performance characteristics
- Advanced monitoring and alerting capabilities
- Comprehensive operational documentation

# Logical Dependency Chain

## 1. Foundation First (Phase 1)
**Priority:** Critical path - must be completed before any other work
**Components:**
- Extract Redis connection management
- Implement basic get/set/delete operations
- Add compression/decompression logic
- Create performance monitoring integration

**Rationale:** All subsequent work depends on having a solid, generic Redis foundation.

## 2. AI Feature Migration (Phase 2)  
**Priority:** High - maintains existing functionality
**Dependencies:** Requires completed Phase 1
**Components:**
- Extract `CacheKeyGenerator` as standalone component
- Refactor `AIResponseCache` to inherit from `GenericRedisCache`
- Migrate AI-specific methods (cache_response, get_cached_response)
- Update AI-specific invalidation logic

**Rationale:** Ensures no functionality is lost during refactoring while building on the new foundation.

## 3. Developer Experience (Phase 3)
**Priority:** Medium - improves usability
**Dependencies:** Requires completed Phases 1 & 2
**Components:**
- Create `CacheFactory` with smart defaults
- Add environment-based configuration
- Write comprehensive documentation
- Create migration examples

**Rationale:** Makes the refactored system accessible to template users.

## 4. Production Optimization (Phase 4)
**Priority:** Low - performance and operational improvements  
**Dependencies:** Requires completed Phases 1-3
**Components:**
- Advanced monitoring and metrics
- Performance optimization
- Production deployment patterns
- Load testing and benchmarking

**Rationale:** Ensures the system is production-ready with optimal performance.

## Incremental Development Strategy

### Atomic Deliverables
Each phase produces working, testable components:
- **Phase 1:** Functional generic Redis cache
- **Phase 2:** Feature-complete AI cache with inheritance
- **Phase 3:** Developer-friendly cache factories
- **Phase 4:** Production-optimized system

### Build-Upon Pattern
Each phase extends the previous without breaking changes:
- Phase 2 builds on Phase 1's foundation
- Phase 3 adds convenience without changing core functionality  
- Phase 4 optimizes without changing interfaces

### Validation Points
- Unit tests pass after each phase
- Integration tests verify compatibility
- Performance benchmarks show no regression
- Documentation examples work as written

# Risks and Mitigations  

## Technical Challenges

### Risk: Performance Regression During Refactoring
**Impact:** High - could slow down production applications
**Probability:** Medium
**Mitigation:**
- Comprehensive benchmarking before and after refactoring
- Performance tests in CI/CD pipeline
- Gradual rollout with monitoring
- Rollback plan if metrics show degradation

**Code Example - Performance Testing:**
```python
@pytest.mark.benchmark
async def test_cache_performance_comparison():
    # Test current AIResponseCache
    old_cache = AIResponseCache()
    old_time = await benchmark_cache_operations(old_cache)
    
    # Test new GenericRedisCache  
    new_cache = GenericRedisCache()
    new_time = await benchmark_cache_operations(new_cache)
    
    # Ensure no significant regression
    assert new_time <= old_time * 1.1  # Allow 10% tolerance
```

### Risk: Data Serialization Incompatibilities
**Impact:** High - could cause data loss or corruption
**Probability:** Low  
**Mitigation:**
- Maintain same serialization format in new implementation
- Comprehensive data compatibility tests
- Data migration utilities if format changes needed

**Code Example - Compatibility Testing:**
```python
async def test_data_format_compatibility():
    # Save data with old implementation
    old_cache = AIResponseCache()
    test_data = {"key": "value", "number": 42}
    await old_cache.set("test_key", test_data)
    
    # Read with new implementation
    new_cache = GenericRedisCache()
    retrieved_data = await new_cache.get("test_key")
    
    assert retrieved_data == test_data
```

### Risk: Complex Inheritance Hierarchies
**Impact:** Medium - could create maintenance burden
**Probability:** Medium
**Mitigation:**
- Favor composition over inheritance where possible
- Keep inheritance hierarchy shallow (max 2 levels)
- Clear separation of concerns between generic and AI-specific code
- Comprehensive documentation of inheritance relationships

## MVP and Scope Management

### Risk: Scope Creep into Advanced Features
**Impact:** Medium - could delay core refactoring
**Probability:** High
**Mitigation:**
- Strict phase-based development approach
- Clear acceptance criteria for each phase
- Regular scope reviews with stakeholders
- Advanced features deferred to Phase 4

### Risk: Breaking Existing Functionality
**Impact:** High - could disrupt current development
**Probability:** Medium
**Mitigation:**
- Comprehensive test suite covering all existing functionality
- Feature parity validation between old and new implementations
- Staged rollout starting with new projects
- Rollback plan for any breaking changes

**Code Example - Feature Parity Testing:**
```python
@pytest.mark.parametrize("cache_impl", [
    AIResponseCache,  # Original implementation
    lambda: AIResponseCache(),  # New implementation
])
async def test_ai_cache_feature_parity(cache_impl):
    cache = cache_impl()
    
    # Test all AI-specific operations
    await cache.cache_response(
        text="Test document",
        operation="summarize", 
        options={"max_length": 100},
        response={"summary": "Test summary"}
    )
    
    result = await cache.get_cached_response(
        text="Test document",
        operation="summarize",
        options={"max_length": 100}
    )
    
    assert result["summary"] == "Test summary"
```

## Resource Constraints

### Risk: Limited Development Time
**Impact:** Medium - could result in incomplete implementation
**Probability:** Medium  
**Mitigation:**
- Prioritize Phase 1 and 2 as critical path
- Defer non-essential features to later phases
- Automated testing to reduce manual validation time
- Clear documentation to enable parallel development

### Risk: Insufficient Redis Infrastructure for Testing
**Impact:** Low - could slow development and testing
**Probability:** Low
**Mitigation:**
- Docker-based Redis for local development
- In-memory Redis mock for unit tests
- Graceful fallback to InMemoryCache during development

**Code Example - Test Infrastructure:**
```python
@pytest.fixture(scope="session")
def redis_server():
    """Start Redis server for integration tests"""
    if os.getenv("CI"):
        # Use Redis service in CI
        return "redis://redis:6379"
    else:
        # Start local Redis container
        container = docker_client.containers.run(
            "redis:alpine", 
            ports={'6379/tcp': None},
            detach=True
        )
        yield f"redis://localhost:{container.ports['6379/tcp'][0]['HostPort']}"
        container.remove(force=True)
```

# Appendix  

## Research Findings

### Current Code Analysis
- **Total lines in AIResponseCache:** ~1,326 lines
- **Generic Redis functionality:** ~60% (~800 lines)
- **AI-specific functionality:** ~40% (~526 lines) 
- **Code duplication with InMemoryCache:** ~40 lines of memory management logic

### Performance Benchmarks (Current State)
- **Memory cache operations:** ~0.1ms average
- **Redis operations:** ~1-5ms average (network dependent)
- **Key generation for large text:** ~2-10ms (size dependent)
- **Compression for large responses:** ~5-50ms (size dependent)

### Cache Usage Patterns Analysis
```python
# Common generic usage patterns
await cache.set("user:123", user_data)           # 45% of operations
await cache.get("config:feature_flags")          # 30% of operations  
await cache.delete("session:expired")            # 15% of operations
await cache.invalidate_pattern("user:*")         # 10% of operations

# AI-specific usage patterns  
await cache.cache_response(text, op, opts, resp)  # 60% of AI operations
await cache.get_cached_response(text, op, opts)   # 35% of AI operations
await cache.invalidate_by_operation("summarize")  # 5% of AI operations
```

## Technical Specifications

### Cache Key Format Specifications
```python
# Generic cache keys (user-provided)
"user:123"
"session:abc-def-ghi"
"config:feature_flags"

# AI cache keys (generated)
"ai_cache:op:summarize|txt:sample_text|opts:a1b2c3d4"
"ai_cache:op:sentiment|txt:hash:1234567890abcdef|opts:e5f6g7h8"
```

### Compression Algorithm Specifications
```python
# Compression decision matrix
if response_size < 1000 bytes:
    storage_format = "raw:json"
elif response_size < 10000 bytes:
    storage_format = "compressed:zlib_level_6"  
else:
    storage_format = "compressed:zlib_level_9"
```

### Performance Monitoring Specifications
```python
# Standard metrics for all cache types
class StandardMetrics:
    hit_ratio: float              # 0.0 - 1.0
    operations_per_second: float  # Recent average
    memory_usage_bytes: int       # Current usage
    compression_ratio: float      # Average compression achieved

# Extended metrics for AI cache
class AIMetrics(StandardMetrics):
    key_generation_time_ms: float      # Average key generation time
    text_processing_time_ms: float     # Average text analysis time
    operation_distribution: Dict[str, int]  # Count by operation type
```

### Configuration Schema
```python
# Environment variables
REDIS_URL=redis://localhost:6379
CACHE_DEFAULT_TTL=3600
CACHE_COMPRESSION_THRESHOLD=1000
CACHE_COMPRESSION_LEVEL=6

# AI-specific configuration
CACHE_TEXT_HASH_THRESHOLD=1000
CACHE_AI_OPERATION_TTLS={"summarize": 7200, "sentiment": 86400}
```

### Migration Compatibility Matrix
```python
# Compatibility between implementations
compatibility_matrix = {
    "InMemoryCache -> GenericRedisCache": "Full compatibility",
    "AIResponseCache -> AIResponseCache(new)": "Full compatibility", 
    "AIResponseCache.get/set -> GenericRedisCache": "Full compatibility",
    "Data format": "No changes required",
    "Configuration": "Backward compatible with new options"
}
```

### Testing Requirements
```python
# Test coverage requirements
minimum_coverage = {
    "GenericRedisCache": 95,
    "AIResponseCache": 95, 
    "CacheKeyGenerator": 100,
    "Integration tests": 90,
    "Performance tests": "All critical paths"
}

# Test categories
test_categories = [
    "Unit tests - individual methods",
    "Integration tests - Redis connectivity", 
    "Performance tests - operation timing",
    "Compatibility tests - data format",
    "Stress tests - high load scenarios",
    "Failure tests - Redis disconnection"
]
```

## Summary of Key Updates

This PRD has been updated based on the current cache infrastructure state and integration requirements with the Redis Security PRD. Key changes include:

### Current State Recognition
- **Solid Foundation**: The existing cache infrastructure already provides excellent InMemoryCache and sophisticated AIResponseCache with monitoring
- **Gap Identification**: AIResponseCache mixes generic Redis functionality with AI-specific features, creating complexity for non-AI use cases
- **Security Gap**: No Redis security features currently implemented

### Updated Refactoring Approach
1. **Extract GenericRedisCache**: Pull generic Redis operations from current AIResponseCache
2. **Refactor AIResponseCache**: Make it inherit from GenericRedisCache while preserving all AI-specific features
3. **Security Integration**: Add Redis authentication, TLS, encryption, and ACL from Redis Security PRD
4. **Testing Modernization**: Apply resilient testing patterns from `dev/prompts/tests-after-refactoring.md`

### Implementation Priority
- **Phase 1**: Generic Redis extraction + basic security (3-4 weeks)
- **Phase 2**: AI cache refactoring + enhanced security (3-4 weeks)  
- **Phase 3**: Developer experience + production security (2-3 weeks)
- **Phase 4**: Advanced features and comprehensive testing (2-3 weeks)

### Success Metrics
- Template users can choose between generic Redis and AI-optimized caching
- All current functionality preserved during refactoring
- Production-ready security features integrated cleanly
- Tests are resilient to implementation changes while maintaining coverage

The refactoring maintains the excellent work already done while providing the flexibility and security needed for both AI and general-purpose FastAPI applications.
